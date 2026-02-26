"""Shared database fixtures for VelocityBench test suites.

Provides:
- db: Database connection with transaction isolation
- Database configuration from environment variables
- Pytest marker registration
"""

import os
import pytest
import psycopg

# Database configuration - matches docker-compose postgres service
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5434"))  # Docker maps 5434:5432
DB_USER = os.getenv("DB_USER", "benchmark")
DB_PASSWORD = os.getenv("DB_PASSWORD", "benchmark123")
DB_NAME = os.getenv("DB_NAME", "velocitybench_benchmark")


def _check_db_available() -> bool:
    """Check if database is available before running tests."""
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            connect_timeout=3,
        )
        conn.close()
        return True
    except Exception:
        return False


# Skip all tests if database is not available
db_available = _check_db_available()


@pytest.fixture
def db():
    """Provide a database connection for testing with automatic cleanup.

    Each test runs in its own transaction which is automatically rolled back
    after the test, ensuring clean data for the next test.

    Uses psycopg3 for modern PostgreSQL connectivity.
    """
    if not db_available:
        pytest.skip("Database not available")

    conn = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )
    conn.autocommit = False

    # Clean up test data before test
    with conn.cursor() as cursor:
        cursor.execute("TRUNCATE benchmark.tb_comment CASCADE")
        cursor.execute("TRUNCATE benchmark.tb_post CASCADE")
        cursor.execute("TRUNCATE benchmark.tb_user CASCADE")
    conn.commit()

    # Start transaction - automatically rolls back on context exit
    try:
        with conn.transaction():
            yield conn
    finally:
        # Ensure connection is closed properly
        if not conn.closed:
            conn.close()


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "security: security-related tests")
    config.addinivalue_line("markers", "security_injection: SQL injection prevention tests")
    config.addinivalue_line("markers", "security_validation: input validation tests")
    config.addinivalue_line("markers", "security_integrity: data integrity tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "mutation: mutation tests")
    config.addinivalue_line("markers", "error: error handling tests")
    config.addinivalue_line("markers", "query: query resolver tests")
    config.addinivalue_line("markers", "relationship: relationship tests")
    config.addinivalue_line("markers", "schema: schema integration tests")
    config.addinivalue_line("markers", "boundary: boundary condition tests")
    config.addinivalue_line("markers", "perf: performance benchmark tests")
    config.addinivalue_line("markers", "perf_queries: query performance benchmark tests")
