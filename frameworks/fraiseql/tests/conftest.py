"""Pytest configuration and fixtures for FraiseQL benchmarking tests."""

import os
import json
import subprocess
import time
from pathlib import Path
from typing import Generator

import pytest
import requests
import psycopg


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def db_connection_string() -> str:
    """Get PostgreSQL connection string from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://velocitybench:password@localhost:5432/fraiseql_test",
    )


@pytest.fixture
def db_connection(db_connection_string):
    """Get a database connection for testing."""
    try:
        conn = psycopg.connect(db_connection_string)
        yield conn
        conn.close()
    except psycopg.OperationalError as e:
        pytest.skip(f"Database not available: {e}")


# ============================================================================
# FraiseQL Server Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def fraiseql_root() -> Path:
    """Get path to FraiseQL repository."""
    return Path("/home/lionel/code/fraiseql")


@pytest.fixture(scope="session")
def fraiseql_cli(fraiseql_root: Path) -> Path:
    """Get path to fraiseql-cli binary."""
    cli_path = fraiseql_root / "target" / "release" / "fraiseql-cli"
    if not cli_path.exists():
        pytest.skip("fraiseql-cli binary not found")
    return cli_path


@pytest.fixture(scope="session")
def fraiseql_server_bin(fraiseql_root: Path) -> Path:
    """Get path to fraiseql-server binary."""
    server_path = fraiseql_root / "target" / "release" / "fraiseql-server"
    if not server_path.exists():
        pytest.skip("fraiseql-server binary not found")
    return server_path


@pytest.fixture(scope="session")
def schema_file() -> Path:
    """Get path to schema.json."""
    schema_path = Path(__file__).parent.parent / "schema.json"
    if not schema_path.exists():
        pytest.skip("schema.json not found")
    return schema_path


@pytest.fixture(scope="session")
def compiled_schema(fraiseql_cli: Path, schema_file: Path) -> Path:
    """Compile schema.json to schema.compiled.json."""
    compiled_path = schema_file.parent / "schema.compiled.json"

    # Compile schema if needed
    if not compiled_path.exists() or schema_file.stat().st_mtime > compiled_path.stat().st_mtime:
        result = subprocess.run(
            [str(fraiseql_cli), "compile", str(schema_file), "-o", str(compiled_path)],
            capture_output=True,
            timeout=30,
        )

        if result.returncode != 0:
            pytest.skip(f"Failed to compile schema: {result.stderr.decode()}")

    return compiled_path


@pytest.fixture
def fraiseql_server(
    fraiseql_server_bin: Path,
    compiled_schema: Path,
    db_connection_string: str,
    tmp_path,
) -> Generator[str, None, None]:
    """Start FraiseQL server for testing.

    Yields:
        Base URL of the FraiseQL server (e.g., 'http://localhost:3000')
    """
    port = 3000
    url = f"http://localhost:{port}"

    # Start server
    process = subprocess.Popen(
        [
            str(fraiseql_server_bin),
            "--schema",
            str(compiled_schema),
            "--database",
            db_connection_string,
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                break
        except (requests.RequestException, ConnectionError):
            pass

        retry_count += 1
        time.sleep(0.5)

    if retry_count >= max_retries:
        process.terminate()
        pytest.skip("FraiseQL server failed to start")

    yield url

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


# ============================================================================
# Query Fixtures
# ============================================================================


@pytest.fixture
def graphql_query():
    """Helper function to send GraphQL queries."""
    def _query(url: str, query: str, variables: dict = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            f"{url}/graphql",
            json=payload,
            timeout=5,
        )
        return response.json()

    return _query
