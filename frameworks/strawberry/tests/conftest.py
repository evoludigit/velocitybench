"""Pytest configuration and fixtures for Strawberry GraphQL framework tests.

Modern 2025 patterns using:
- pytest-asyncio 1.0+ (async/await native)
- psycopg3 with force_rollback for test isolation
- Direct schema execution for GraphQL tests
- Pydantic v2 for input validation
"""

import os
import pytest
import pytest_asyncio
import psycopg
from psycopg import sql

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
    """Synchronous database connection for non-async tests.

    Uses transaction isolation with automatic rollback.
    For async tests, use db_async fixture instead.
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

    # ✅ MODERN 2025 PATTERN: No explicit commit() in tests!
    # Transaction context auto-rollback on exit
    try:
        with conn.transaction():
            yield conn
    finally:
        # Ensure connection is closed properly
        if not conn.closed:
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
        def create_user(username: str, email_or_identifier: str = None, email: str = None, full_name: str = None, bio: str = None) -> dict:
            """Create a test user in the command side (tb_user).

            Supports flexible calling: create_user(username, email) or create_user(username, identifier, email)

            Args:
                username: Username
                email_or_identifier: Email or identifier (auto-detects based on context)
                email: Email address (optional, only if called with 3+ args)
                full_name: Full name (optional, defaults to empty string)
                bio: Biography (optional)

            Returns:
                dict with pk_user, id (UUID), username, identifier, email, full_name, bio
            """
            # Auto-detect: if email_or_identifier looks like email and email is None, treat it as email
            if email is None and email_or_identifier and '@' in email_or_identifier:
                email = email_or_identifier
                identifier = username  # Use username as identifier
            else:
                identifier = email_or_identifier if email_or_identifier else username

            # full_name is NOT NULL in schema, so use empty string as default
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
        def create_post(fk_author: int, title: str, identifier: str = None, content: str = None) -> dict:
            """Create a test post in the command side (tb_post).

            Args:
                fk_author: Foreign key to tb_user.pk_user
                title: Post title
                identifier: Human-readable identifier/slug (auto-generated if not provided)
                content: Post content (auto-generated if not provided)

            Returns:
                dict with pk_post, id (UUID), title, identifier, content, fk_author
            """
            # Auto-generate identifier from title if not provided
            if identifier is None:
                identifier = title.lower().replace(' ', '-')

            # Auto-generate content if not provided (required by schema)
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


# Pytest markers
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "security: security tests")
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


# ============================================================================
# Enhanced Factory Methods for Bulk Operations
# ============================================================================

@pytest.fixture
def bulk_factory(db):
    """Factory with bulk operation methods for test data creation."""
    class BulkFactory:
        @staticmethod
        def create_bulk_users(count: int, prefix: str = "user") -> list[dict]:
            """Create multiple users efficiently.

            Args:
                count: Number of users to create
                prefix: Username prefix for generated users

            Returns:
                List of user dictionaries
            """
            users = []
            with db.cursor() as cursor:
                for i in range(count):
                    cursor.execute(
                        "INSERT INTO benchmark.tb_user (username, identifier, email, full_name, bio) "
                        "VALUES (%s, %s, %s, %s, %s) "
                        "RETURNING pk_user, id, username, identifier, email, full_name, bio",
                        (
                            f"{prefix}{i}",
                            f"{prefix}-{i}",
                            f"{prefix}{i}@example.com",
                            f"{prefix.title()} {i}",
                            f"Bio for {prefix}{i}"
                        ),
                    )
                    row = cursor.fetchone()
                    if row:
                        users.append({
                            'pk_user': row[0],
                            'id': row[1],
                            'username': row[2],
                            'identifier': row[3],
                            'email': row[4],
                            'full_name': row[5],
                            'bio': row[6]
                        })
            db.commit()
            return users

        @staticmethod
        def create_user_with_posts(username: str, identifier: str, email: str, post_count: int = 5) -> dict:
            """Create a user with multiple posts.

            Args:
                username: User's username
                identifier: User's identifier/slug
                email: User's email
                post_count: Number of posts to create for user

            Returns:
                dict with user and list of posts
            """
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO benchmark.tb_user (username, identifier, email, full_name, bio) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING pk_user, id, username, identifier, email, full_name, bio",
                    (username, identifier, email, f"{username.title()}", f"Bio for {username}"),
                )
                user_row = cursor.fetchone()
                user = {
                    'pk_user': user_row[0],
                    'id': user_row[1],
                    'username': user_row[2],
                    'identifier': user_row[3],
                    'email': user_row[4],
                    'full_name': user_row[5],
                    'bio': user_row[6]
                }

                posts = []
                for i in range(post_count):
                    cursor.execute(
                        "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
                        "VALUES (%s, %s, %s, %s) "
                        "RETURNING pk_post, id, title, identifier, content, fk_author",
                        (
                            user['pk_user'],
                            f"Post {i} by {username}",
                            f"post-{username}-{i}",
                            f"Content for post {i}"
                        ),
                    )
                    post_row = cursor.fetchone()
                    if post_row:
                        posts.append({
                            'pk_post': post_row[0],
                            'id': post_row[1],
                            'title': post_row[2],
                            'identifier': post_row[3],
                            'content': post_row[4],
                            'fk_author': post_row[5]
                        })

            db.commit()
            return {
                'user': user,
                'posts': posts
            }

        @staticmethod
        def create_post_with_comments(author_pk: int, title: str, identifier: str, comment_count: int = 3) -> dict:
            """Create a post with multiple comments.

            Args:
                author_pk: Primary key of post author
                title: Post title
                identifier: Post identifier/slug
                comment_count: Number of comments to create

            Returns:
                dict with post and list of comments
            """
            with db.cursor() as cursor:
                # Create post
                cursor.execute(
                    "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING pk_post, id, title, identifier, content, fk_author",
                    (author_pk, title, identifier, f"Content for {title}"),
                )
                post_row = cursor.fetchone()
                post = {
                    'pk_post': post_row[0],
                    'id': post_row[1],
                    'title': post_row[2],
                    'identifier': post_row[3],
                    'content': post_row[4],
                    'fk_author': post_row[5]
                }

                # Create commenter
                cursor.execute(
                    "INSERT INTO benchmark.tb_user (username, identifier, email, full_name, bio) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING pk_user, id",
                    (f"commenter-{identifier}", f"commenter-{identifier}",
                     f"commenter-{identifier}@example.com", "Commenter", "I comment"),
                )
                commenter_row = cursor.fetchone()
                commenter_pk = commenter_row[0]

                # Create comments
                comments = []
                for i in range(comment_count):
                    cursor.execute(
                        "INSERT INTO benchmark.tb_comment (fk_post, fk_author, identifier, content) "
                        "VALUES (%s, %s, %s, %s) "
                        "RETURNING pk_comment, id, identifier, content, fk_post, fk_author",
                        (
                            post['pk_post'],
                            commenter_pk,
                            f"comment-{i}",
                            f"Comment {i} on {title}"
                        ),
                    )
                    cmt_row = cursor.fetchone()
                    if cmt_row:
                        comments.append({
                            'pk_comment': cmt_row[0],
                            'id': cmt_row[1],
                            'identifier': cmt_row[2],
                            'content': cmt_row[3],
                            'fk_post': cmt_row[4],
                            'fk_author': cmt_row[5]
                        })

            db.commit()
            return {
                'post': post,
                'comments': comments,
                'commenter_pk': commenter_pk
            }

        @staticmethod
        def cleanup_all_data() -> None:
            """Clean all benchmark tables in cascade order.

            Cleans in order: comments -> posts -> users to respect FK constraints.
            """
            with db.cursor() as cursor:
                cursor.execute("TRUNCATE benchmark.tb_comment CASCADE")
                cursor.execute("TRUNCATE benchmark.tb_post CASCADE")
                cursor.execute("TRUNCATE benchmark.tb_user CASCADE")
            db.commit()

        @staticmethod
        def get_user_count() -> int:
            """Get total number of users in database."""
            with db.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
                return cursor.fetchone()[0]

        @staticmethod
        def get_post_count(author_pk: int = None) -> int:
            """Get total number of posts, optionally filtered by author."""
            with db.cursor() as cursor:
                if author_pk:
                    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s", (author_pk,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
                return cursor.fetchone()[0]

        @staticmethod
        def get_comment_count(post_pk: int = None) -> int:
            """Get total number of comments, optionally filtered by post."""
            with db.cursor() as cursor:
                if post_pk:
                    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s", (post_pk,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_comment")
                return cursor.fetchone()[0]

    return BulkFactory()
