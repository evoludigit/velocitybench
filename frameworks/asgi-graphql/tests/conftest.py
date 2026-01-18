"""Pytest configuration and fixtures for Ariadne GraphQL framework tests.

Modern 2025 patterns using:
- pytest-asyncio 1.0+ (async/await native)
- psycopg3 with force_rollback for test isolation
- Direct schema execution for GraphQL tests
"""

import os
import pytest
import psycopg

# Database configuration - matches docker-compose postgres service
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5434'))  # Docker maps 5434:5432
DB_USER = os.getenv('DB_USER', 'benchmark')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'benchmark123')
DB_NAME = os.getenv('DB_NAME', 'velocitybench_benchmark')


@pytest.fixture
def db():
    """Synchronous database connection with transaction isolation."""
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

    try:
        with conn.transaction():
            yield conn
    finally:
        if not conn.closed:
            conn.close()


@pytest.fixture
def factory(db):
    """Factory for creating test data using Trinity Identifier Pattern."""
    class TestFactory:
        @staticmethod
        def create_user(username: str, email: str = None, full_name: str = None, bio: str = None) -> dict:
            """Create a test user in tb_user."""
            if email is None:
                email = f"{username}@example.com"
            identifier = username
            if full_name is None:
                full_name = ""

            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_user (username, identifier, email, full_name, bio) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING pk_user, id, username, identifier, email, full_name, bio",
                    (username, identifier, email, full_name, bio),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'pk_user': row[0],
                        'id': row[1],
                        'username': row[2],
                        'identifier': row[3],
                        'email': row[4],
                        'full_name': row[5],
                        'bio': row[6]
                    }
                return {}

        @staticmethod
        def create_post(fk_author: int, title: str, content: str = None) -> dict:
            """Create a test post in tb_post."""
            identifier = title.lower().replace(' ', '-')
            if content is None:
                content = f"Content for {title}"

            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING pk_post, id, title, identifier, content, fk_author",
                    (fk_author, title, identifier, content),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'pk_post': row[0],
                        'id': row[1],
                        'title': row[2],
                        'identifier': row[3],
                        'content': row[4],
                        'fk_author': row[5]
                    }
                return {}

        @staticmethod
        def create_comment(fk_post: int, fk_author: int, content: str) -> dict:
            """Create a test comment in tb_comment."""
            import uuid
            identifier = f"comment-{uuid.uuid4().hex[:8]}"

            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_comment (fk_post, fk_author, identifier, content) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING pk_comment, id, identifier, content, fk_post, fk_author",
                    (fk_post, fk_author, identifier, content),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'pk_comment': row[0],
                        'id': row[1],
                        'identifier': row[2],
                        'content': row[3],
                        'fk_post': row[4],
                        'fk_author': row[5]
                    }
                return {}

    return TestFactory()


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "mutation: mutation tests")
    config.addinivalue_line("markers", "query: query resolver tests")
    config.addinivalue_line("markers", "relationship: relationship tests")
    config.addinivalue_line("markers", "schema: schema validation tests")
    config.addinivalue_line("markers", "error: error handling tests")
