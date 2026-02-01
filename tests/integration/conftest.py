"""Pytest fixtures for integration tests."""

import subprocess
import time
import socket
from pathlib import Path

import pytest
import requests


def get_free_port() -> int:
    """Get a free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture
def fraiseql_server():
    """Start fraiseql-server for testing."""
    binary_path = (
        Path(__file__).parent.parent.parent
        / "fraiseql-server"
        / "target"
        / "release"
        / "fraiseql-server"
    )

    if not binary_path.exists():
        pytest.skip("fraiseql-server binary not found")

    schema_path = (
        Path(__file__).parent.parent.parent / "fraiseql-schema" / "schema.json"
    )

    # Create schema if it doesn't exist
    if not schema_path.exists():
        import sys

        sys.path.insert(0, str(schema_path.parent))
        from schema_fraiseql import export_schema

        export_schema(str(schema_path))

    port = get_free_port()

    # Start server
    process = subprocess.Popen(
        [str(binary_path), "--schema", str(schema_path), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    for _ in range(30):  # Try for 30 seconds
        try:
            response = requests.get(f"http://127.0.0.1:{port}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.1)

    yield f"http://127.0.0.1:{port}"

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
