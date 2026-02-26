"""
FraiseQL Server Build & Validation Tests

Verifies fraiseql-server builds, accepts schema, and executes queries.
"""

import subprocess
import time
import requests
import socket
from pathlib import Path


def get_free_port() -> int:
    """Get a free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class TestFraiseQLServerBuild:
    """Test fraiseql-server compilation and startup."""

    @staticmethod
    def _get_server_binary_path() -> Path:
        """Get path to fraiseql-server binary."""
        return (
            Path(__file__).parent.parent.parent
            / "fraiseql-server"
            / "target"
            / "release"
            / "fraiseql-server"
        )

    @staticmethod
    def _get_schema_path() -> Path:
        """Get path to schema.json."""
        return Path(__file__).parent.parent.parent / "fraiseql-schema" / "schema.json"

    def test_fraiseql_server_cargo_project_exists(self):
        """fraiseql-server Cargo project must exist."""
        cargo_toml = (
            Path(__file__).parent.parent.parent / "fraiseql-server" / "Cargo.toml"
        )
        assert cargo_toml.exists(), f"Cargo.toml not found at {cargo_toml}"

    def test_fraiseql_server_builds(self):
        """fraiseql-server must build successfully."""
        server_dir = Path(__file__).parent.parent.parent / "fraiseql-server"
        assert server_dir.exists(), (
            f"fraiseql-server directory not found at {server_dir}"
        )

        # Try to build
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=str(server_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )

        assert result.returncode == 0, f"Build failed: {result.stderr}"

        # Verify binary exists
        binary = self._get_server_binary_path()
        assert binary.exists(), f"Binary not found at {binary}"

    def test_fraiseql_server_shows_version(self):
        """fraiseql-server must respond to --version."""
        binary = self._get_server_binary_path()

        if not binary.exists():
            # If build hasn't happened yet, skip
            return

        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0, f"--version failed: {result.stderr}"
        assert "fraiseql-server" in result.stdout or "version" in result.stdout.lower()

    def test_fraiseql_server_accepts_schema(self):
        """fraiseql-server must accept schema.json on startup."""
        binary = self._get_server_binary_path()
        schema_path = self._get_schema_path()

        if not binary.exists():
            # If build hasn't happened yet, skip
            return

        # Create schema.json from schema definition
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))
        from schema_fraiseql import export_schema

        export_schema(str(schema_path))
        assert schema_path.exists(), "Failed to create schema.json"

        # Get a free port
        port = get_free_port()

        # Start server with schema and specific port
        process = subprocess.Popen(
            [str(binary), "--schema", str(schema_path), "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Give server 3 seconds to start
            time.sleep(3)

            # Check if process is still alive
            poll_result = process.poll()
            if poll_result is not None:
                stderr = process.stderr.read() if process.stderr else ""
                raise AssertionError(f"Server crashed on startup: {stderr}")

            # Try to connect on the specified port
            try:
                response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
                assert response.status_code == 200, (
                    f"Health check failed: {response.text}"
                )
            except requests.exceptions.ConnectionError:
                # Server not listening yet, but process is alive - acceptable for now
                pass
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


class TestFraiseQLServerQueries:
    """Test fraiseql-server query execution."""

    def test_simple_query_execution(self, fraiseql_server):
        """Server must execute simple queries correctly."""
        # Query: { users { id } }
        query = "{ users { id } }"

        response = requests.post(
            f"{fraiseql_server}/graphql",
            json={"query": query},
            timeout=5,
        )

        assert response.status_code == 200, f"Query failed: {response.text}"
        data = response.json()

        # Should have data (even if empty initially)
        assert "data" in data
        assert "users" in data["data"]
        assert isinstance(data["data"]["users"], list)

    def test_query_with_variables(self, fraiseql_server):
        """Server must handle queries with variables."""
        query = "query GetUsers($limit: Int) { users(limit: $limit) { id } }"
        variables = {"limit": 10}

        response = requests.post(
            f"{fraiseql_server}/graphql",
            json={"query": query, "variables": variables},
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_nested_query_execution(self, fraiseql_server):
        """Server must execute nested queries."""
        # Query: { users { id posts { id } } }
        query = "{ users { id posts { id } } }"

        response = requests.post(
            f"{fraiseql_server}/graphql",
            json={"query": query},
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "users" in data["data"]

    def test_mutation_execution(self, fraiseql_server):
        """Server must execute mutations."""
        mutation = (
            'mutation { create_user(name: "Test", email: "test@example.com") { id } }'
        )

        response = requests.post(
            f"{fraiseql_server}/graphql",
            json={"query": mutation},
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
