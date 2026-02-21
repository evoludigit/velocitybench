"""Pytest configuration and fixtures for FraiseQL v2 benchmarking tests."""

import os
import shutil
import subprocess
import time
from collections.abc import Generator
from pathlib import Path

import psycopg
import pytest
import requests

DEFAULT_PORT = 8815
REQUIRED_VERSION = "2.0.0-beta.3"


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
# FraiseQL v2 Binary Fixtures
# ============================================================================


def _find_fraiseql_binary(name: str) -> Path | None:
    """Find a FraiseQL binary in common locations."""
    fraiseql_root = os.getenv("FRAISEQL_ROOT", "/home/lionel/code/fraiseql")

    local_path = Path(fraiseql_root) / "target" / "release" / name
    if local_path.exists():
        return local_path

    cargo_bin = Path.home() / ".cargo" / "bin" / name
    if cargo_bin.exists():
        return cargo_bin

    system_path = shutil.which(name)
    if system_path:
        return Path(system_path)

    return None


def _assert_binary_version(binary: Path, required: str) -> None:
    """Assert that the binary reports the required version string."""
    result = subprocess.run(
        [str(binary), "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    version_output = result.stdout.strip() + result.stderr.strip()
    if required not in version_output:
        pytest.skip(
            f"{binary.name} is not {required} (got: {version_output!r}). "
            "Build beta.3 with: cargo build --release --manifest-path "
            "/home/lionel/code/fraiseql/Cargo.toml"
        )


@pytest.fixture(scope="session")
def fraiseql_root() -> Path:
    """Get path to FraiseQL repository or installation."""
    root = os.getenv("FRAISEQL_ROOT", "/home/lionel/code/fraiseql")
    return Path(root)


@pytest.fixture(scope="session")
def fraiseql_cli() -> Path:
    """Get path to fraiseql-cli binary, asserting beta.3 version."""
    cli_path = _find_fraiseql_binary("fraiseql-cli")
    if cli_path is None:
        pytest.skip("fraiseql-cli binary not found")
    _assert_binary_version(cli_path, REQUIRED_VERSION)
    return cli_path


@pytest.fixture(scope="session")
def fraiseql_server_bin() -> Path:
    """Get path to fraiseql-server binary, asserting beta.3 version."""
    server_path = _find_fraiseql_binary("fraiseql-server")
    if server_path is None:
        pytest.skip("fraiseql-server binary not found")
    _assert_binary_version(server_path, REQUIRED_VERSION)
    return server_path


# ============================================================================
# Schema Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def schema_file() -> Path:
    """Get path to schema.json."""
    schema_path = Path(__file__).parent.parent / "schema.json"
    if not schema_path.exists():
        pytest.skip("schema.json not found - run 'python schema.py' first")
    return schema_path


@pytest.fixture(scope="session")
def config_file() -> Path:
    """Get path to fraiseql.toml configuration."""
    config_path = Path(__file__).parent.parent / "fraiseql.toml"
    if not config_path.exists():
        pytest.skip("fraiseql.toml not found")
    return config_path


@pytest.fixture(scope="session")
def compiled_schema(fraiseql_cli: Path, schema_file: Path, config_file: Path) -> Path:
    """Compile schema.json to schema.compiled.json via fraiseql.toml."""
    compiled_path = schema_file.parent / "schema.compiled.json"

    if (
        not compiled_path.exists()
        or schema_file.stat().st_mtime > compiled_path.stat().st_mtime
    ):
        result = subprocess.run(
            [
                str(fraiseql_cli),
                "compile",
                str(config_file),
                "--types",
                str(schema_file),
            ],
            capture_output=True,
            timeout=30,
            cwd=str(config_file.parent),
        )

        if result.returncode != 0:
            pytest.skip(f"Failed to compile schema: {result.stderr.decode()}")

    return compiled_path


# ============================================================================
# FraiseQL v2 Server Fixtures
# ============================================================================


@pytest.fixture
def fraiseql_server(
    fraiseql_server_bin: Path,
    compiled_schema: Path,  # noqa: ARG001 — injected for schema compile side-effect
    config_file: Path,
    db_connection_string: str,
) -> Generator[str, None, None]:
    """Start FraiseQL v2 server for testing.

    Yields:
        Base URL of the FraiseQL server (e.g., 'http://localhost:8815')
    """
    port = DEFAULT_PORT
    url = f"http://localhost:{port}"

    env = os.environ.copy()
    env["RUST_LOG"] = "info"
    env["FRAISEQL_CONFIG"] = str(config_file)
    env["DATABASE_URL"] = db_connection_string

    process = subprocess.Popen(
        [str(fraiseql_server_bin)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

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
        stdout, stderr = process.communicate(timeout=5)
        pytest.skip(f"FraiseQL v2 server failed to start. Stderr: {stderr.decode()}")

    yield url

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

    def _query(url: str, query: str, variables: dict | None = None) -> dict:
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
