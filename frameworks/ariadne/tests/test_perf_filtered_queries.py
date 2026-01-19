"""Performance benchmarks for filtered and searched queries.

Tests query performance with WHERE clauses, pattern matching, and
multiple filter combinations.

Expected latency:
- Single filter: <50ms
- Multiple filters: <100ms
- Pattern matching (LIKE/ILIKE): <100ms

Uses pytest-benchmark for timing measurements and TestFactory for data creation.
"""

import pytest


@pytest.mark.perf
@pytest.mark.perf_queries
class TestFilteredQueries:
    """Filtered and searched query benchmarks."""

    def test_filter_users_by_username_exact(self, benchmark, db, factory):
        """Benchmark: Filter users by exact username match.

        Expected: <10ms (indexed)
        """
        # Create 50 users
        for i in range(50):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        # Also create target user
        target = factory.create_user('alice', 'alice@example.com')

        def query_filtered():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user WHERE username = %s",
                    ('alice',)
                )
                return cursor.fetchall()

        result = benchmark(query_filtered)
        assert len(result) == 1
        assert result[0][1] == 'alice'

    def test_filter_users_by_email_pattern(self, benchmark, db, factory):
        """Benchmark: Filter users by email domain pattern.

        Expected: <100ms
        """
        # Create users with different email domains
        for i in range(30):
            factory.create_user(f'user{i}', f'user{i}@example.com')
        for i in range(20):
            factory.create_user(f'test{i}', f'test{i}@test.com')

        def query_filtered():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email FROM benchmark.tb_user WHERE email LIKE %s",
                    ('%@test.com',)
                )
                return cursor.fetchall()

        result = benchmark(query_filtered)
        assert len(result) == 20

    def test_filter_posts_by_title_ilike(self, benchmark, db, factory):
        """Benchmark: Filter posts by case-insensitive title search.

        Expected: <100ms
        """
        user = factory.create_user('author', 'author@example.com')

        # Create posts with different titles
        for i in range(40):
            if i % 3 == 0:
                factory.create_post(user['pk_user'], f'Python Tutorial {i}', f'python-{i}')
            else:
                factory.create_post(user['pk_user'], f'Random Post {i}', f'random-{i}')

        def query_filtered():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title FROM benchmark.tb_post WHERE title ILIKE %s",
                    ('%python%',)
                )
                return cursor.fetchall()

        result = benchmark(query_filtered)
        assert len(result) >= 13  # Approximately 1/3 of 40

    def test_filter_comments_by_content(self, benchmark, db, factory):
        """Benchmark: Filter comments by content contains.

        Expected: <100ms
        """
        user = factory.create_user('commenter', 'commenter@example.com')
        post = factory.create_post(user['pk_user'], 'Discussion', 'discussion')

        # Create 50 comments
        for i in range(50):
            if i % 4 == 0:
                content = f'Great point about the topic {i}'
            else:
                content = f'Random comment {i}'
            factory.create_comment(post['pk_post'], user['pk_user'], f'comment-{i}', content)

        def query_filtered():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, content FROM benchmark.tb_comment WHERE content ILIKE %s",
                    ('%great point%',)
                )
                return cursor.fetchall()

        result = benchmark(query_filtered)
        assert len(result) >= 12  # Approximately 1/4 of 50

    def test_filter_users_multiple_conditions(self, benchmark, db, factory):
        """Benchmark: Filter users with multiple AND conditions.

        Expected: <50ms
        """
        # Create users with various attributes
        for i in range(60):
            if i < 20:
                factory.create_user(f'alice{i}', f'alice{i}@example.com', 'Alice User', 'Active user')
            elif i < 40:
                factory.create_user(f'bob{i}', f'bob{i}@example.com', 'Bob User', 'Active user')
            else:
                factory.create_user(f'charlie{i}', f'charlie{i}@example.com', 'Charlie User', 'Inactive')

        def query_filtered():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user "
                    "WHERE username LIKE %s AND bio = %s",
                    ('alice%', 'Active user')
                )
                return cursor.fetchall()

        result = benchmark(query_filtered)
        assert len(result) == 20

    def test_filter_posts_by_author_and_title(self, benchmark, db, factory):
        """Benchmark: Filter posts by author AND title pattern.

        Expected: <50ms
        """
        # Create 2 authors
        alice = factory.create_user('alice', 'alice@example.com')
        bob = factory.create_user('bob', 'bob@example.com')

        # Create posts for both
        for i in range(25):
            factory.create_post(alice['pk_user'], f'Tutorial {i}', f'alice-{i}')
        for i in range(25):
            factory.create_post(bob['pk_user'], f'Tutorial {i}', f'bob-{i}')

        def query_filtered():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title FROM benchmark.tb_post "
                    "WHERE fk_author = %s AND title LIKE %s",
                    (alice['pk_user'], 'Tutorial%')
                )
                return cursor.fetchall()

        result = benchmark(query_filtered)
        assert len(result) == 25

    def test_filter_with_pagination(self, benchmark, db, factory):
        """Benchmark: Filtered query with pagination.

        Expected: <100ms
        """
        # Create 100 users
        for i in range(100):
            if i % 2 == 0:
                factory.create_user(f'active{i}', f'active{i}@example.com', 'User', 'Active')
            else:
                factory.create_user(f'inactive{i}', f'inactive{i}@example.com', 'User', 'Inactive')

        def query_filtered_paginated():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user "
                    "WHERE bio = %s ORDER BY created_at DESC LIMIT 10 OFFSET 5",
                    ('Active',)
                )
                return cursor.fetchall()

        result = benchmark(query_filtered_paginated)
        assert len(result) == 10

    def test_filter_with_sorting(self, benchmark, db, factory):
        """Benchmark: Filtered query with ORDER BY.

        Expected: <100ms
        """
        user = factory.create_user('author', 'author@example.com')

        # Create 60 posts
        for i in range(60):
            title = f'Post {i:03d}'  # Zero-padded for sorting
            factory.create_post(user['pk_user'], title, f'post-{i}')

        def query_filtered_sorted():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title FROM benchmark.tb_post "
                    "WHERE fk_author = %s ORDER BY title ASC LIMIT 20",
                    (user['pk_user'],)
                )
                return cursor.fetchall()

        result = benchmark(query_filtered_sorted)
        assert len(result) == 20

    def test_filter_date_range(self, benchmark, db, factory):
        """Benchmark: Filter by date range (created_at).

        Expected: <100ms
        """
        # Create users
        for i in range(50):
            factory.create_user(f'user{i}', f'user{i}@example.com')

        def query_filtered_dates():
            with db.cursor() as cursor:
                # Get users created in the last hour (all test data)
                cursor.execute(
                    "SELECT id, username, created_at FROM benchmark.tb_user "
                    "WHERE created_at >= NOW() - INTERVAL '1 hour' "
                    "ORDER BY created_at DESC"
                )
                return cursor.fetchall()

        result = benchmark(query_filtered_dates)
        assert len(result) == 50

    def test_filter_or_conditions(self, benchmark, db, factory):
        """Benchmark: Filter with OR conditions.

        Expected: <100ms
        """
        # Create users with different usernames
        for i in range(30):
            factory.create_user(f'alice{i}', f'alice{i}@example.com')
        for i in range(30):
            factory.create_user(f'bob{i}', f'bob{i}@example.com')
        for i in range(30):
            factory.create_user(f'charlie{i}', f'charlie{i}@example.com')

        def query_filtered_or():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user "
                    "WHERE username LIKE %s OR username LIKE %s",
                    ('alice%', 'bob%')
                )
                return cursor.fetchall()

        result = benchmark(query_filtered_or)
        assert len(result) == 60

    def test_filter_in_list(self, benchmark, db, factory):
        """Benchmark: Filter using IN clause.

        Expected: <50ms
        """
        # Create users
        users = []
        for i in range(50):
            user = factory.create_user(f'user{i}', f'user{i}@example.com')
            users.append(user)

        # Select 10 specific user PKs
        target_pks = [users[i]['pk_user'] for i in range(0, 50, 5)]

        def query_filtered_in():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user WHERE pk_user = ANY(%s)",
                    (target_pks,)
                )
                return cursor.fetchall()

        result = benchmark(query_filtered_in)
        assert len(result) == 10
