"""Performance benchmarks for simple single-entity queries.

Tests basic query performance without relationships or complex operations.
Expected latency: <10ms per query.

Uses pytest-benchmark for timing measurements and the TestFactory pattern
for test data creation with automatic cleanup via transaction isolation.
"""

import pytest


@pytest.mark.perf
@pytest.mark.perf_queries
class TestSimpleQueries:
    """Simple single-entity query benchmarks."""

    def test_get_user_by_id(self, benchmark, db, factory):
        """Benchmark: Get user by UUID.

        Expected: <10ms
        """
        user = factory.create_user('alice', 'alice@example.com')
        user_id = user['id']

        def query_user():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_user, id, username, email, full_name, bio "
                    "FROM benchmark.tb_user WHERE id = %s",
                    (user_id,)
                )
                return cursor.fetchone()

        result = benchmark(query_user)
        assert result is not None
        assert result[1] == user_id

    def test_get_user_by_username(self, benchmark, db, factory):
        """Benchmark: Get user by username.

        Expected: <10ms (indexed)
        """
        user = factory.create_user('bob', 'bob@example.com')

        def query_user():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_user, id, username, email FROM benchmark.tb_user WHERE username = %s",
                    ('bob',)
                )
                return cursor.fetchone()

        result = benchmark(query_user)
        assert result is not None
        assert result[2] == 'bob'

    def test_get_post_by_id(self, benchmark, db, factory):
        """Benchmark: Get post by UUID.

        Expected: <10ms
        """
        user = factory.create_user('author', 'author@example.com')
        post = factory.create_post(user['pk_user'], 'Test Post', 'test-post')
        post_id = post['id']

        def query_post():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_post, id, title, content, fk_author FROM benchmark.tb_post WHERE id = %s",
                    (post_id,)
                )
                return cursor.fetchone()

        result = benchmark(query_post)
        assert result is not None
        assert result[1] == post_id

    def test_get_comment_by_id(self, benchmark, db, factory):
        """Benchmark: Get comment by UUID.

        Expected: <10ms
        """
        user = factory.create_user('commenter', 'commenter@example.com')
        post = factory.create_post(user['pk_user'], 'Post', 'post-1')
        comment = factory.create_comment(post['pk_post'], user['pk_user'], 'comment-1', 'Test comment')
        comment_id = comment['id']

        def query_comment():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_comment, id, content, fk_post, fk_author FROM benchmark.tb_comment WHERE id = %s",
                    (comment_id,)
                )
                return cursor.fetchone()

        result = benchmark(query_comment)
        assert result is not None
        assert result[1] == comment_id

    def test_get_nonexistent_user(self, benchmark, db):
        """Benchmark: Query for non-existent user (null case).

        Expected: <5ms (fast index lookup)
        """
        from uuid import uuid4
        fake_id = uuid4()

        def query_user():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM benchmark.tb_user WHERE id = %s",
                    (fake_id,)
                )
                return cursor.fetchone()

        result = benchmark(query_user)
        assert result is None

    def test_list_users_empty(self, benchmark, db):
        """Benchmark: List users when table is empty.

        Expected: <5ms
        """
        def query_users():
            with db.cursor() as cursor:
                cursor.execute("SELECT id, username FROM benchmark.tb_user LIMIT 10")
                return cursor.fetchall()

        result = benchmark(query_users)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_posts_empty(self, benchmark, db):
        """Benchmark: List posts when table is empty.

        Expected: <5ms
        """
        def query_posts():
            with db.cursor() as cursor:
                cursor.execute("SELECT id, title FROM benchmark.tb_post LIMIT 10")
                return cursor.fetchall()

        result = benchmark(query_posts)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_user_multiple_fields(self, benchmark, db, factory):
        """Benchmark: Get user with all fields selected.

        Expected: <10ms
        """
        user = factory.create_user('fulluser', 'full@example.com', 'Full User', 'A complete bio')
        user_id = user['id']

        def query_user_full():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_user, id, username, identifier, email, full_name, bio, "
                    "created_at, updated_at FROM benchmark.tb_user WHERE id = %s",
                    (user_id,)
                )
                return cursor.fetchone()

        result = benchmark(query_user_full)
        assert result is not None
        assert result[1] == user_id
        assert result[2] == 'fulluser'

    def test_count_users(self, benchmark, db, factory):
        """Benchmark: Count users (aggregate query).

        Expected: <10ms
        """
        # Create 5 users
        for i in range(5):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def count_users():
            with db.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
                return cursor.fetchone()[0]

        result = benchmark(count_users)
        assert result == 5

    def test_get_user_by_email(self, benchmark, db, factory):
        """Benchmark: Get user by email address.

        Expected: <10ms (email should be indexed)
        """
        user = factory.create_user('emailuser', 'unique@example.com')

        def query_by_email():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_user, id, username, email FROM benchmark.tb_user WHERE email = %s",
                    ('unique@example.com',)
                )
                return cursor.fetchone()

        result = benchmark(query_by_email)
        assert result is not None
        assert result[3] == 'unique@example.com'
