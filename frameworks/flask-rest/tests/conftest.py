"""Pytest configuration and fixtures for Flask REST framework tests.

All tests connect to a shared PostgreSQL database with transaction isolation
for automatic cleanup. Uses psycopg3 (modern async-friendly PostgreSQL driver).
"""

import os
import pytest
import psycopg
from psycopg import sql

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'velocitybench')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'velocitybench_test')


@pytest.fixture
def db():
    """Connect to shared test database with transaction isolation.

    Each test runs in its own transaction which is automatically rolled back
    after the test, ensuring clean data for the next test.

    Uses psycopg3 for modern PostgreSQL connectivity.
    """
    conn = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )
    conn.autocommit = False

    with conn.transaction():
        yield conn
        conn.rollback()

    conn.close()


@pytest.fixture
def factory(db):
    """Factory for creating test data using psycopg3.

    Uses Trinity Identifier Pattern:
    - pk_{entity}: Internal int identifier (primary key)
    - id: UUID for public API
    - identifier: Text slug for human-readable access
    """
    class TestFactory:
        @staticmethod
        def create_user(username: str, identifier: str, email: str, full_name: str = None, bio: str = None) -> dict:
            """Create a test user in the command side (tb_user).

            Args:
                username: Username
                identifier: Human-readable identifier/slug
                email: Email address
                full_name: Full name (optional)
                bio: Biography (optional)

            Returns:
                dict with pk_user, id (UUID), username, identifier, email, full_name, bio
            """
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_user (username, identifier, email, full_name, bio) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING pk_user, id, username, identifier, email, full_name, bio",
                    (username, identifier, email, full_name, bio),
                )
                row = cursor.fetchone()
                return dict(row) if row else {}

        @staticmethod
        def create_post(fk_author: int, title: str, identifier: str, content: str = None) -> dict:
            """Create a test post in the command side (tb_post).

            Args:
                fk_author: Foreign key to tb_user.pk_user
                title: Post title
                identifier: Human-readable identifier/slug
                content: Post content (optional)

            Returns:
                dict with pk_post, id (UUID), title, identifier, content, fk_author
            """
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING pk_post, id, title, identifier, content, fk_author",
                    (fk_author, title, identifier, content),
                )
                row = cursor.fetchone()
                return dict(row) if row else {}

        @staticmethod
        def create_comment(fk_post: int, fk_author: int, identifier: str, content: str) -> dict:
            """Create a test comment in the command side (tb_comment).

            Args:
                fk_post: Foreign key to tb_post.pk_post
                fk_author: Foreign key to tb_user.pk_user
                identifier: Human-readable identifier/slug
                content: Comment content

            Returns:
                dict with pk_comment, id (UUID), identifier, content, fk_post, fk_author
            """
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_comment (fk_post, fk_author, identifier, content) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING pk_comment, id, identifier, content, fk_post, fk_author",
                    (fk_post, fk_author, identifier, content),
                )
                row = cursor.fetchone()
                return dict(row) if row else {}

    return TestFactory()


# Pytest markers
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: slow tests")
