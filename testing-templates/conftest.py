"""Shared pytest fixtures for VelocityBench Python frameworks.

All tests connect to a single shared PostgreSQL database.
Transaction isolation ensures each test has clean data automatically.
"""

import os
import pytest
import psycopg2
from psycopg2.extras import DictCursor

# Database connection parameters (from environment or defaults)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'velocitybench')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'velocitybench_test')


@pytest.fixture
def db():
    """Connect to shared PostgreSQL test database with transaction isolation.

    Each test runs in its own transaction which is automatically rolled back
    after the test, ensuring clean data for the next test.

    Usage:
        def test_something(db):
            cursor = db.cursor(cursor_factory=DictCursor)
            cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("Alice", "alice@example.com"))
            # ...data automatically rolls back after test
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    conn.autocommit = False
    conn.begin()  # Start transaction for test isolation

    yield conn

    # Cleanup: rollback automatically clears all test data
    try:
        conn.rollback()
    except Exception:
        pass  # Already rolled back
    finally:
        conn.close()


@pytest.fixture
def factory(db):
    """Factory for creating test data.

    Provides convenience methods for creating test objects.
    All created data is automatically rolled back after the test.

    Usage:
        def test_something(factory):
            user = factory.create_user("Alice", "alice@example.com")
            assert user["name"] == "Alice"
    """
    class TestFactory:
        """Factory for test data creation."""

        @staticmethod
        def create_user(name: str, email: str) -> dict:
            """Create a test user.

            Args:
                name: User name
                email: User email

            Returns:
                dict with id, name, email
            """
            cursor = db.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s) "
                "RETURNING id, name, email",
                (name, email),
            )
            return dict(cursor.fetchone())

        @staticmethod
        def create_company(name: str) -> dict:
            """Create a test company.

            Args:
                name: Company name

            Returns:
                dict with id, name
            """
            cursor = db.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "INSERT INTO companies (name) VALUES (%s) RETURNING id, name",
                (name,),
            )
            return dict(cursor.fetchone())

        @staticmethod
        def create_product(name: str, price: float, company_id: int) -> dict:
            """Create a test product.

            Args:
                name: Product name
                price: Product price
                company_id: Company ID (foreign key)

            Returns:
                dict with id, name, price, company_id
            """
            cursor = db.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "INSERT INTO products (name, price, company_id) VALUES (%s, %s, %s) "
                "RETURNING id, name, price, company_id",
                (name, price, company_id),
            )
            return dict(cursor.fetchone())

    return TestFactory()


# Pytest markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: slow tests")
