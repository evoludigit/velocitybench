"""Shared pytest fixtures for VelocityBench Python frameworks."""

import os
import asyncio
import pytest
from typing import AsyncGenerator
import psycopg2
from psycopg2.extras import DictCursor


# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'velocitybench')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'velocitybench_test')


class TestDatabase:
    """Test database helper with transaction isolation."""

    def __init__(self):
        self.connection = None
        self.transaction = None

    def connect(self):
        """Create database connection."""
        self.connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        self.connection.autocommit = False

    def begin_transaction(self):
        """Start a transaction for test isolation."""
        if self.connection:
            self.connection.begin()

    def rollback(self):
        """Rollback transaction (cleanup)."""
        if self.connection:
            self.connection.rollback()

    def commit(self):
        """Commit transaction."""
        if self.connection:
            self.connection.commit()

    def execute(self, query: str, params=None):
        """Execute SQL query."""
        cursor = self.connection.cursor(cursor_factory=DictCursor)
        cursor.execute(query, params)
        return cursor

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


@pytest.fixture(scope='session')
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def test_db():
    """Session-scoped database connection."""
    db = TestDatabase()
    db.connect()
    yield db
    db.close()


@pytest.fixture
def db(test_db):
    """Per-test database with transaction isolation."""
    test_db.begin_transaction()
    yield test_db
    test_db.rollback()


@pytest.fixture
def clean_db_tables(db):
    """Clean all tables for a fresh test."""
    # Delete from all tables (in reverse dependency order)
    db.execute("DELETE FROM orders")
    db.execute("DELETE FROM products")
    db.execute("DELETE FROM users")
    db.execute("DELETE FROM companies")
    db.connection.commit()
    yield db
    db.rollback()


class TestFactory:
    """Factory for creating test data."""

    def __init__(self, db):
        self.db = db

    def create_user(self, name: str, email: str):
        """Create a test user."""
        cursor = self.db.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email",
            (name, email),
        )
        row = cursor.fetchone()
        self.db.connection.commit()
        return dict(row) if row else None

    def create_company(self, name: str):
        """Create a test company."""
        cursor = self.db.execute(
            "INSERT INTO companies (name) VALUES (%s) RETURNING id, name",
            (name,),
        )
        row = cursor.fetchone()
        self.db.connection.commit()
        return dict(row) if row else None

    def create_product(self, name: str, price: float, company_id: int):
        """Create a test product."""
        cursor = self.db.execute(
            "INSERT INTO products (name, price, company_id) VALUES (%s, %s, %s) "
            "RETURNING id, name, price, company_id",
            (name, price, company_id),
        )
        row = cursor.fetchone()
        self.db.connection.commit()
        return dict(row) if row else None


@pytest.fixture
def factory(db):
    """Factory for creating test data."""
    return TestFactory(db)


# Markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests (no database)")
    config.addinivalue_line("markers", "integration: integration tests (with database)")
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "async: async tests")
