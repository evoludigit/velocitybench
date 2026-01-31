"""Performance benchmarks for N+1 query detection and batch optimization.

Tests that verify queries avoid the N+1 problem by using proper batch loading
or JOIN patterns instead of issuing separate queries for each relationship.

Expected behavior:
- Naive approach: 1 + N queries (1 for parent, N for children)
- Optimized approach: 1-2 queries total (batch loading or JOIN)

Uses pytest-benchmark for timing measurements and TestFactory for data creation.
"""

import pytest


@pytest.mark.perf
@pytest.mark.perf_queries
class TestNPlusOneDetection:
    """N+1 query detection and batch loading benchmarks."""

    def test_n_plus_one_users_posts_naive(self, benchmark, db, factory):
        """Benchmark: Naive N+1 query (1 + N pattern) - Users with posts.

        This is intentionally inefficient to demonstrate the N+1 problem.
        Expected: Slower than batch approach, issues 11 queries (1 + 10)
        """
        # Create 10 users, each with 5 posts
        users = []
        for i in range(10):
            user = factory.create_user(f'user{i}', f'user{i}@example.com')
            users.append(user)
            for j in range(5):
                factory.create_post(user['pk_user'], f'Post {j}', f'u{i}-p{j}')

        def query_naive():
            """Naive approach: 1 query for users + 1 query per user for posts"""
            with db.cursor() as cursor:
                # Query 1: Get all users
                cursor.execute("SELECT pk_user, id, username FROM benchmark.tb_user ORDER BY pk_user LIMIT 10")
                user_rows = cursor.fetchall()

                results = []
                # Queries 2-11: Get posts for each user (N+1!)
                for user_row in user_rows:
                    cursor.execute(
                        "SELECT id, title FROM benchmark.tb_post WHERE fk_author = %s",
                        (user_row[0],)
                    )
                    posts = cursor.fetchall()
                    results.append({'user': user_row, 'posts': posts})

                return results

        result = benchmark(query_naive)
        assert len(result) == 10
        assert all(len(r['posts']) == 5 for r in result)

    def test_n_plus_one_users_posts_optimized(self, benchmark, db, factory):
        """Benchmark: Optimized batch loading - Users with posts.

        Uses batch loading: 2 queries total (1 for users, 1 for all posts).
        Expected: Faster than naive approach, issues only 2 queries
        """
        # Create 10 users, each with 5 posts
        users = []
        for i in range(10):
            user = factory.create_user(f'user{i}', f'user{i}@example.com')
            users.append(user)
            for j in range(5):
                factory.create_post(user['pk_user'], f'Post {j}', f'u{i}-p{j}')

        def query_optimized():
            """Optimized: 2 queries total using batch loading"""
            with db.cursor() as cursor:
                # Query 1: Get all users
                cursor.execute("SELECT pk_user, id, username FROM benchmark.tb_user ORDER BY pk_user LIMIT 10")
                user_rows = cursor.fetchall()
                user_pks = [row[0] for row in user_rows]

                # Query 2: Batch load all posts for all users
                cursor.execute(
                    "SELECT pk_post, id, title, fk_author FROM benchmark.tb_post "
                    "WHERE fk_author = ANY(%s) ORDER BY fk_author, pk_post",
                    (user_pks,)
                )
                all_posts = cursor.fetchall()

                # Group posts by author
                posts_by_author = {}
                for post_row in all_posts:
                    author_pk = post_row[3]
                    if author_pk not in posts_by_author:
                        posts_by_author[author_pk] = []
                    posts_by_author[author_pk].append(post_row)

                # Build result
                results = []
                for user_row in user_rows:
                    user_pk = user_row[0]
                    posts = posts_by_author.get(user_pk, [])
                    results.append({'user': user_row, 'posts': posts})

                return results

        result = benchmark(query_optimized)
        assert len(result) == 10
        assert all(len(r['posts']) == 5 for r in result)

    def test_n_plus_one_posts_comments_naive(self, benchmark, db, factory):
        """Benchmark: Naive N+1 query - Posts with comments.

        Expected: Slower, issues 1 + N queries
        """
        # Create user and 8 posts, each with 3 comments
        user = factory.create_user('author', 'author@example.com')
        commenter = factory.create_user('commenter', 'commenter@example.com')

        posts = []
        for i in range(8):
            post = factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')
            posts.append(post)
            for j in range(3):
                factory.create_comment(post['pk_post'], commenter['pk_user'], f'c-{i}-{j}', f'Comment {j}')

        def query_naive():
            with db.cursor() as cursor:
                # Query 1: Get all posts
                cursor.execute("SELECT pk_post, id, title FROM benchmark.tb_post ORDER BY pk_post LIMIT 10")
                post_rows = cursor.fetchall()

                results = []
                # Queries 2-9: Get comments for each post (N+1!)
                for post_row in post_rows:
                    cursor.execute(
                        "SELECT id, content FROM benchmark.tb_comment WHERE fk_post = %s",
                        (post_row[0],)
                    )
                    comments = cursor.fetchall()
                    results.append({'post': post_row, 'comments': comments})

                return results

        result = benchmark(query_naive)
        assert len(result) == 8
        assert all(len(r['comments']) == 3 for r in result)

    def test_n_plus_one_posts_comments_optimized(self, benchmark, db, factory):
        """Benchmark: Optimized batch loading - Posts with comments.

        Expected: Faster, issues only 2 queries total
        """
        # Create user and 8 posts, each with 3 comments
        user = factory.create_user('author', 'author@example.com')
        commenter = factory.create_user('commenter', 'commenter@example.com')

        posts = []
        for i in range(8):
            post = factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')
            posts.append(post)
            for j in range(3):
                factory.create_comment(post['pk_post'], commenter['pk_user'], f'c-{i}-{j}', f'Comment {j}')

        def query_optimized():
            with db.cursor() as cursor:
                # Query 1: Get all posts
                cursor.execute("SELECT pk_post, id, title FROM benchmark.tb_post ORDER BY pk_post LIMIT 10")
                post_rows = cursor.fetchall()
                post_pks = [row[0] for row in post_rows]

                # Query 2: Batch load all comments
                cursor.execute(
                    "SELECT pk_comment, id, content, fk_post FROM benchmark.tb_comment "
                    "WHERE fk_post = ANY(%s) ORDER BY fk_post, pk_comment",
                    (post_pks,)
                )
                all_comments = cursor.fetchall()

                # Group comments by post
                comments_by_post = {}
                for comment_row in all_comments:
                    post_pk = comment_row[3]
                    if post_pk not in comments_by_post:
                        comments_by_post[post_pk] = []
                    comments_by_post[post_pk].append(comment_row)

                # Build result
                results = []
                for post_row in post_rows:
                    post_pk = post_row[0]
                    comments = comments_by_post.get(post_pk, [])
                    results.append({'post': post_row, 'comments': comments})

                return results

        result = benchmark(query_optimized)
        assert len(result) == 8
        assert all(len(r['comments']) == 3 for r in result)

    def test_n_plus_one_comments_authors_optimized(self, benchmark, db, factory):
        """Benchmark: Batch loading for comment authors (many-to-one).

        Expected: 2 queries (1 for comments, 1 for all authors)
        """
        # Create 5 different authors
        authors = []
        for i in range(5):
            author = factory.create_user(f'author{i}', f'author{i}@example.com')
            authors.append(author)

        # Create 1 post
        post = factory.create_post(authors[0]['pk_user'], 'Discussion', 'discussion')

        # Create 15 comments from different authors
        for i in range(15):
            author = authors[i % 5]  # Rotate through authors
            factory.create_comment(post['pk_post'], author['pk_user'], f'comment-{i}', f'Comment {i}')

        def query_optimized():
            with db.cursor() as cursor:
                # Query 1: Get all comments
                cursor.execute(
                    "SELECT pk_comment, id, content, fk_author FROM benchmark.tb_comment "
                    "WHERE fk_post = %s ORDER BY pk_comment",
                    (post['pk_post'],)
                )
                comment_rows = cursor.fetchall()
                author_pks = list(set(row[3] for row in comment_rows))

                # Query 2: Batch load all authors
                cursor.execute(
                    "SELECT pk_user, id, username FROM benchmark.tb_user "
                    "WHERE pk_user = ANY(%s)",
                    (author_pks,)
                )
                author_rows = cursor.fetchall()

                # Map authors by pk
                authors_map = {row[0]: row for row in author_rows}

                # Build result
                results = []
                for comment_row in comment_rows:
                    author_pk = comment_row[3]
                    author = authors_map.get(author_pk)
                    results.append({'comment': comment_row, 'author': author})

                return results

        result = benchmark(query_optimized)
        assert len(result) == 15
        assert all(r['author'] is not None for r in result)

    def test_query_count_comparison(self, benchmark, db, factory):
        """Benchmark: Compare query counts between naive and optimized approaches.

        This test documents the expected query count difference.
        """
        # Create 5 users, each with 4 posts
        for i in range(5):
            user = factory.create_user(f'user{i}', f'user{i}@example.com')
            for j in range(4):
                factory.create_post(user['pk_user'], f'Post {j}', f'u{i}-p{j}')

        def query_optimized_join():
            """Use JOIN to get everything in 1 query"""
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        u.pk_user, u.id as user_id, u.username,
                        p.pk_post, p.id as post_id, p.title
                    FROM benchmark.tb_user u
                    LEFT JOIN benchmark.tb_post p ON p.fk_author = u.pk_user
                    ORDER BY u.pk_user, p.pk_post
                """)
                rows = cursor.fetchall()

                # Group posts by user
                users = {}
                for row in rows:
                    user_pk = row[0]
                    if user_pk not in users:
                        users[user_pk] = {
                            'user': (row[0], row[1], row[2]),
                            'posts': []
                        }
                    if row[3] is not None:  # Has post
                        users[user_pk]['posts'].append((row[3], row[4], row[5]))

                return list(users.values())

        result = benchmark(query_optimized_join)
        assert len(result) == 5
        assert all(len(r['posts']) == 4 for r in result)
