"""Pytest configuration and fixtures for FraiseQL GraphQL framework tests.

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


def _check_db_available():
    """Check if database is available."""
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
    """Synchronous database connection with transaction isolation."""
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

    try:
        with conn.transaction():
            yield conn
    finally:
        if not conn.closed:
            conn.close()


@pytest.fixture
def factory(db):
    """Factory for creating and querying test data using Trinity Identifier Pattern.

    Trinity Pattern:
    - pk_* = Integer primary key (internal, for FK relationships)
    - id = UUID (external API identifier)
    - fk_* = Integer foreign key (references pk_*)
    """
    class TestFactory:
        def __init__(self):
            self._db = db

        # ============ CREATE METHODS ============

        def create_user(self, username: str, email: str = None, full_name: str = None, bio: str = None) -> dict:
            """Create a test user in tb_user."""
            if email is None:
                email = f"{username}@example.com"
            identifier = username
            if full_name is None:
                full_name = ""

            with self._db.cursor() as cursor:
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
                        'id': str(row[1]),  # Convert UUID to string
                        'username': row[2],
                        'identifier': row[3],
                        'email': row[4],
                        'full_name': row[5],
                        'bio': row[6]
                    }
                return {}

        def create_post(self, fk_author: int, title: str, content: str = None) -> dict:
            """Create a test post in tb_post.

            Args:
                fk_author: Integer pk_user of the author (use user['pk_user'])
                title: Post title
                content: Post content (optional)
            """
            identifier = title.lower().replace(' ', '-')
            if content is None:
                content = f"Content for {title}"

            with self._db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING pk_post, id, title, identifier, content, fk_author",
                    (fk_author, title, identifier, content),
                )
                row = cursor.fetchone()
                if row:
                    # Also fetch author for relationship tests
                    cursor.execute(
                        "SELECT pk_user, id, username FROM benchmark.tb_user WHERE pk_user = %s",
                        (row[5],)
                    )
                    author_row = cursor.fetchone()
                    author = {'pk_user': author_row[0], 'id': str(author_row[1]), 'username': author_row[2]} if author_row else None

                    return {
                        'pk_post': row[0],
                        'id': str(row[1]),  # Convert UUID to string
                        'title': row[2],
                        'identifier': row[3],
                        'content': row[4],
                        'fk_author': row[5],
                        'author': author
                    }
                return {}

        def create_comment(self, fk_author: int, fk_post: int, content: str) -> dict:
            """Create a test comment in tb_comment.

            Args:
                fk_author: Integer pk_user of the commenter (use user['pk_user'])
                fk_post: Integer pk_post of the post (use post['pk_post'])
                content: Comment content
            """
            import uuid
            identifier = f"comment-{uuid.uuid4().hex[:8]}"

            with self._db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_comment (fk_post, fk_author, identifier, content) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING pk_comment, id, identifier, content, fk_post, fk_author",
                    (fk_post, fk_author, identifier, content),
                )
                row = cursor.fetchone()
                if row:
                    # Also fetch author for relationship tests
                    cursor.execute(
                        "SELECT pk_user, id, username FROM benchmark.tb_user WHERE pk_user = %s",
                        (row[5],)
                    )
                    author_row = cursor.fetchone()
                    author = {'pk_user': author_row[0], 'id': str(author_row[1]), 'username': author_row[2]} if author_row else None

                    return {
                        'pk_comment': row[0],
                        'id': str(row[1]),  # Convert UUID to string
                        'identifier': row[2],
                        'content': row[3],
                        'fk_post': row[4],
                        'fk_author': row[5],
                        'author': author
                    }
                return {}

        # ============ QUERY METHODS ============

        def get_user(self, user_id: str) -> dict | None:
            """Get user by UUID."""
            with self._db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_user, id, username, identifier, email, full_name, bio "
                    "FROM benchmark.tb_user WHERE id = %s",
                    (user_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'pk_user': row[0],
                        'id': str(row[1]),
                        'username': row[2],
                        'identifier': row[3],
                        'email': row[4],
                        'full_name': row[5],
                        'bio': row[6]
                    }
                return None

        def get_all_users(self) -> list[dict]:
            """Get all users."""
            with self._db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_user, id, username, identifier, email, full_name, bio "
                    "FROM benchmark.tb_user ORDER BY pk_user"
                )
                rows = cursor.fetchall()
                return [
                    {
                        'pk_user': row[0],
                        'id': str(row[1]),
                        'username': row[2],
                        'identifier': row[3],
                        'email': row[4],
                        'full_name': row[5],
                        'bio': row[6]
                    }
                    for row in rows
                ]

        def get_post(self, post_id: str) -> dict | None:
            """Get post by UUID."""
            with self._db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_post, id, title, identifier, content, fk_author "
                    "FROM benchmark.tb_post WHERE id = %s",
                    (post_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'pk_post': row[0],
                        'id': str(row[1]),
                        'title': row[2],
                        'identifier': row[3],
                        'content': row[4],
                        'fk_author': row[5]
                    }
                return None

        def get_posts_by_author(self, fk_author: int) -> list[dict]:
            """Get posts by author pk_user."""
            with self._db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_post, id, title, identifier, content, fk_author "
                    "FROM benchmark.tb_post WHERE fk_author = %s ORDER BY pk_post",
                    (fk_author,)
                )
                rows = cursor.fetchall()
                return [
                    {
                        'pk_post': row[0],
                        'id': str(row[1]),
                        'title': row[2],
                        'identifier': row[3],
                        'content': row[4],
                        'fk_author': row[5]
                    }
                    for row in rows
                ]

        def get_comment(self, comment_id: str) -> dict | None:
            """Get comment by UUID."""
            with self._db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_comment, id, identifier, content, fk_post, fk_author "
                    "FROM benchmark.tb_comment WHERE id = %s",
                    (comment_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'pk_comment': row[0],
                        'id': str(row[1]),
                        'identifier': row[2],
                        'content': row[3],
                        'fk_post': row[4],
                        'fk_author': row[5]
                    }
                return None

        def get_comments_by_post(self, fk_post: int) -> list[dict]:
            """Get comments by post pk_post."""
            with self._db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_comment, id, identifier, content, fk_post, fk_author "
                    "FROM benchmark.tb_comment WHERE fk_post = %s ORDER BY pk_comment",
                    (fk_post,)
                )
                rows = cursor.fetchall()
                return [
                    {
                        'pk_comment': row[0],
                        'id': str(row[1]),
                        'identifier': row[2],
                        'content': row[3],
                        'fk_post': row[4],
                        'fk_author': row[5]
                    }
                    for row in rows
                ]

        def reset(self):
            """Reset all test data."""
            with self._db.cursor() as cursor:
                cursor.execute("TRUNCATE benchmark.tb_comment CASCADE")
                cursor.execute("TRUNCATE benchmark.tb_post CASCADE")
                cursor.execute("TRUNCATE benchmark.tb_user CASCADE")

    return TestFactory()


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "security: security tests")
    config.addinivalue_line("markers", "security_injection: SQL injection prevention tests")
    config.addinivalue_line("markers", "security_validation: input validation tests")
    config.addinivalue_line("markers", "security_integrity: data integrity tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "mutation: mutation tests")
    config.addinivalue_line("markers", "query: query resolver tests")
    config.addinivalue_line("markers", "relationship: relationship tests")
    config.addinivalue_line("markers", "schema: schema validation tests")
    config.addinivalue_line("markers", "error: error handling tests")
    config.addinivalue_line("markers", "perf: performance benchmark tests")
    config.addinivalue_line("markers", "perf_queries: query performance benchmark tests")
