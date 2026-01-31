"""Performance benchmarks for list queries with pagination.

Tests query performance for retrieving multiple records with different
data sizes and pagination patterns.

Expected latency:
- Small (10-50 records): <50ms
- Medium (100-500 records): <200ms
- Large (1000+ records): Scale linearly

Uses pytest-benchmark for timing measurements and TestFactory for data creation.
"""

import pytest


@pytest.mark.perf
@pytest.mark.perf_queries
class TestListQueries:
    """List query benchmarks with pagination."""

    def test_list_users_limit_10(self, benchmark, db, factory):
        """Benchmark: List 10 users from 50 total.

        Expected: <50ms
        """
        # Create 50 users
        for i in range(50):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def query_users():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email FROM benchmark.tb_user "
                    "ORDER BY created_at DESC LIMIT 10"
                )
                return cursor.fetchall()

        result = benchmark(query_users)
        assert len(result) == 10

    def test_list_users_limit_100(self, benchmark, db, factory):
        """Benchmark: List 100 users from 200 total.

        Expected: <100ms
        """
        # Create 200 users
        for i in range(200):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def query_users():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email FROM benchmark.tb_user "
                    "ORDER BY created_at DESC LIMIT 100"
                )
                return cursor.fetchall()

        result = benchmark(query_users)
        assert len(result) == 100

    def test_list_posts_with_pagination(self, benchmark, db, factory):
        """Benchmark: List posts with LIMIT/OFFSET pagination.

        Expected: <50ms (small page)
        """
        # Create user and 50 posts
        user = factory.create_user('author', 'author@example.com')
        for i in range(50):
            factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')

        def query_posts_page():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title, fk_author FROM benchmark.tb_post "
                    "ORDER BY created_at DESC LIMIT 10 OFFSET 10"
                )
                return cursor.fetchall()

        result = benchmark(query_posts_page)
        assert len(result) == 10

    def test_list_comments_with_pagination(self, benchmark, db, factory):
        """Benchmark: List comments with pagination.

        Expected: <50ms
        """
        # Create user, post, and 30 comments
        user = factory.create_user('commenter', 'commenter@example.com')
        post = factory.create_post(user['pk_user'], 'Popular Post', 'popular-post')
        for i in range(30):
            factory.create_comment(post['pk_post'], user['pk_user'], f'comment-{i}', f'Comment {i}')

        def query_comments():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, content, fk_post FROM benchmark.tb_comment "
                    "ORDER BY created_at DESC LIMIT 10"
                )
                return cursor.fetchall()

        result = benchmark(query_comments)
        assert len(result) == 10

    def test_list_users_smoke(self, benchmark, db, factory):
        """Benchmark: List users (smoke test with minimal data).

        Expected: <10ms
        """
        # Create 5 users
        for i in range(5):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def query_users():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user ORDER BY username LIMIT 10"
                )
                return cursor.fetchall()

        result = benchmark(query_users)
        assert len(result) == 5

    def test_list_users_medium_dataset(self, benchmark, db, factory):
        """Benchmark: List users from medium dataset (500 records).

        Expected: <200ms
        """
        # Create 500 users
        for i in range(500):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def query_users():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email FROM benchmark.tb_user "
                    "ORDER BY created_at DESC LIMIT 50"
                )
                return cursor.fetchall()

        result = benchmark(query_users)
        assert len(result) == 50

    def test_offset_pagination_deep(self, benchmark, db, factory):
        """Benchmark: Deep offset pagination (OFFSET 200).

        Expected: <150ms (offset can be expensive)
        """
        # Create 300 users
        for i in range(300):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def query_deep_page():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user "
                    "ORDER BY created_at DESC LIMIT 20 OFFSET 200"
                )
                return cursor.fetchall()

        result = benchmark(query_deep_page)
        assert len(result) == 20

    def test_list_all_users_no_limit(self, benchmark, db, factory):
        """Benchmark: List all users without LIMIT (100 records).

        Expected: <100ms
        """
        # Create 100 users
        for i in range(100):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def query_all_users():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email FROM benchmark.tb_user ORDER BY username"
                )
                return cursor.fetchall()

        result = benchmark(query_all_users)
        assert len(result) == 100

    def test_list_posts_by_author_paginated(self, benchmark, db, factory):
        """Benchmark: List posts filtered by author with pagination.

        Expected: <50ms
        """
        # Create 2 users with posts
        user1 = factory.create_user('author1', 'author1@example.com')
        user2 = factory.create_user('author2', 'author2@example.com')

        for i in range(30):
            factory.create_post(user1['pk_user'], f'Author1 Post {i}', f'a1-post-{i}')
        for i in range(20):
            factory.create_post(user2['pk_user'], f'Author2 Post {i}', f'a2-post-{i}')

        def query_author1_posts():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title FROM benchmark.tb_post "
                    "WHERE fk_author = %s ORDER BY created_at DESC LIMIT 10",
                    (user1['pk_user'],)
                )
                return cursor.fetchall()

        result = benchmark(query_author1_posts)
        assert len(result) == 10

    def test_list_recent_posts(self, benchmark, db, factory):
        """Benchmark: List most recent posts (ORDER BY created_at).

        Expected: <50ms
        """
        # Create user and 40 posts
        user = factory.create_user('prolific', 'prolific@example.com')
        for i in range(40):
            factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')

        def query_recent_posts():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title, created_at FROM benchmark.tb_post "
                    "ORDER BY created_at DESC LIMIT 20"
                )
                return cursor.fetchall()

        result = benchmark(query_recent_posts)
        assert len(result) == 20
