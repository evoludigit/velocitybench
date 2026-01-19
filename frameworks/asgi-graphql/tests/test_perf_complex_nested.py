"""Performance benchmarks for complex nested queries.

Tests query performance with deep relationship nesting, field selection
impact, and memory usage patterns.

Expected latency:
- 2-level nesting: <200ms
- 3-level nesting: <500ms
- Deep nesting should scale linearly, not exponentially

Uses pytest-benchmark for timing measurements and TestFactory for data creation.
"""

import pytest


@pytest.mark.perf
@pytest.mark.perf_queries
class TestComplexNestedQueries:
    """Complex nested query benchmarks."""

    def test_two_level_nesting_full_fields(self, benchmark, db, factory):
        """Benchmark: User → Posts (2 levels) with all fields.

        Expected: <200ms
        """
        # Create user with 10 posts
        user = factory.create_user('alice', 'alice@example.com', 'Alice Author', 'Prolific writer')
        for i in range(10):
            factory.create_post(user['pk_user'], f'Article {i}', f'article-{i}', f'Content for article {i}')

        def query_nested():
            with db.cursor() as cursor:
                # Get user with all fields
                cursor.execute(
                    "SELECT pk_user, id, username, identifier, email, full_name, bio, created_at "
                    "FROM benchmark.tb_user WHERE id = %s",
                    (user['id'],)
                )
                user_row = cursor.fetchone()

                # Get posts with all fields
                cursor.execute(
                    "SELECT pk_post, id, title, identifier, content, fk_author, created_at "
                    "FROM benchmark.tb_post WHERE fk_author = %s ORDER BY created_at",
                    (user_row[0],)
                )
                posts = cursor.fetchall()

                return {'user': user_row, 'posts': posts}

        result = benchmark(query_nested)
        assert result['user'] is not None
        assert len(result['posts']) == 10

    def test_two_level_nesting_sparse_fields(self, benchmark, db, factory):
        """Benchmark: User → Posts (2 levels) with minimal fields.

        Tests if field selection reduces query time.
        Expected: <150ms (faster than full fields)
        """
        # Create user with 10 posts
        user = factory.create_user('bob', 'bob@example.com')
        for i in range(10):
            factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')

        def query_sparse():
            with db.cursor() as cursor:
                # Get user with minimal fields
                cursor.execute(
                    "SELECT pk_user, id, username FROM benchmark.tb_user WHERE id = %s",
                    (user['id'],)
                )
                user_row = cursor.fetchone()

                # Get posts with minimal fields
                cursor.execute(
                    "SELECT id, title FROM benchmark.tb_post WHERE fk_author = %s",
                    (user_row[0],)
                )
                posts = cursor.fetchall()

                return {'user': user_row, 'posts': posts}

        result = benchmark(query_sparse)
        assert result['user'] is not None
        assert len(result['posts']) == 10

    def test_three_level_nesting(self, benchmark, db, factory):
        """Benchmark: User → Posts → Comments (3 levels).

        Expected: <500ms
        """
        # Create user with 5 posts, each with 4 comments
        user = factory.create_user('alice', 'alice@example.com')
        commenter = factory.create_user('commenter', 'commenter@example.com')

        for i in range(5):
            post = factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')
            for j in range(4):
                factory.create_comment(post['pk_post'], commenter['pk_user'], f'c-{i}-{j}', f'Comment {j}')

        def query_three_levels():
            with db.cursor() as cursor:
                # Level 1: User
                cursor.execute(
                    "SELECT pk_user, id, username FROM benchmark.tb_user WHERE id = %s",
                    (user['id'],)
                )
                user_row = cursor.fetchone()

                # Level 2: Posts
                cursor.execute(
                    "SELECT pk_post, id, title FROM benchmark.tb_post WHERE fk_author = %s",
                    (user_row[0],)
                )
                posts = cursor.fetchall()

                # Level 3: Comments for all posts (batch load)
                post_pks = [p[0] for p in posts]
                cursor.execute(
                    "SELECT pk_comment, id, content, fk_post FROM benchmark.tb_comment "
                    "WHERE fk_post = ANY(%s) ORDER BY fk_post, pk_comment",
                    (post_pks,)
                )
                all_comments = cursor.fetchall()

                # Group comments by post
                comments_by_post = {}
                for comment in all_comments:
                    post_pk = comment[3]
                    if post_pk not in comments_by_post:
                        comments_by_post[post_pk] = []
                    comments_by_post[post_pk].append(comment)

                # Build result
                posts_with_comments = []
                for post in posts:
                    post_pk = post[0]
                    comments = comments_by_post.get(post_pk, [])
                    posts_with_comments.append({'post': post, 'comments': comments})

                return {'user': user_row, 'posts': posts_with_comments}

        result = benchmark(query_three_levels)
        assert result['user'] is not None
        assert len(result['posts']) == 5
        assert all(len(p['comments']) == 4 for p in result['posts'])

    def test_three_level_with_author_resolution(self, benchmark, db, factory):
        """Benchmark: User → Posts → Comments → Comment Authors (3 levels).

        Expected: <500ms
        """
        # Create user with 3 posts
        author = factory.create_user('author', 'author@example.com')

        # Create 3 commenters
        commenters = []
        for i in range(3):
            commenter = factory.create_user(f'commenter{i}', f'c{i}@example.com')
            commenters.append(commenter)

        # Create posts with comments from different users
        for i in range(3):
            post = factory.create_post(author['pk_user'], f'Post {i}', f'post-{i}')
            for j in range(3):
                commenter = commenters[j]
                factory.create_comment(post['pk_post'], commenter['pk_user'], f'c-{i}-{j}', f'Comment {j}')

        def query_with_authors():
            with db.cursor() as cursor:
                # Level 1: User
                cursor.execute(
                    "SELECT pk_user, id, username FROM benchmark.tb_user WHERE id = %s",
                    (author['id'],)
                )
                user_row = cursor.fetchone()

                # Level 2: Posts
                cursor.execute(
                    "SELECT pk_post, id, title FROM benchmark.tb_post WHERE fk_author = %s",
                    (user_row[0],)
                )
                posts = cursor.fetchall()

                # Level 3: Comments (batch load)
                post_pks = [p[0] for p in posts]
                cursor.execute(
                    "SELECT pk_comment, id, content, fk_post, fk_author FROM benchmark.tb_comment "
                    "WHERE fk_post = ANY(%s)",
                    (post_pks,)
                )
                all_comments = cursor.fetchall()

                # Level 4: Comment authors (batch load)
                author_pks = list(set(c[4] for c in all_comments))
                cursor.execute(
                    "SELECT pk_user, id, username FROM benchmark.tb_user WHERE pk_user = ANY(%s)",
                    (author_pks,)
                )
                comment_authors = cursor.fetchall()

                # Map authors
                authors_map = {a[0]: a for a in comment_authors}

                # Group comments by post with authors
                comments_by_post = {}
                for comment in all_comments:
                    post_pk = comment[3]
                    author_pk = comment[4]
                    if post_pk not in comments_by_post:
                        comments_by_post[post_pk] = []
                    comments_by_post[post_pk].append({
                        'comment': comment,
                        'author': authors_map.get(author_pk)
                    })

                # Build result
                posts_with_comments = []
                for post in posts:
                    post_pk = post[0]
                    comments = comments_by_post.get(post_pk, [])
                    posts_with_comments.append({'post': post, 'comments': comments})

                return {'user': user_row, 'posts': posts_with_comments}

        result = benchmark(query_with_authors)
        assert result['user'] is not None
        assert len(result['posts']) == 3

    def test_deep_nesting_stress(self, benchmark, db, factory):
        """Benchmark: Stress test with deep nesting and many records.

        Expected: Should scale linearly, not exponentially
        """
        # Create 3 users
        users = []
        for i in range(3):
            user = factory.create_user(f'user{i}', f'user{i}@example.com')
            users.append(user)

            # Each user has 5 posts
            for j in range(5):
                post = factory.create_post(user['pk_user'], f'U{i} Post {j}', f'u{i}-p{j}')

                # Each post has 3 comments from different users
                for k in range(3):
                    commenter = users[k]
                    factory.create_comment(post['pk_post'], commenter['pk_user'], f'c-{i}-{j}-{k}', f'Comment {k}')

        def query_stress():
            with db.cursor() as cursor:
                results = []
                for user in users:
                    # Get user
                    cursor.execute(
                        "SELECT pk_user, id, username FROM benchmark.tb_user WHERE id = %s",
                        (user['id'],)
                    )
                    user_row = cursor.fetchone()

                    # Get posts
                    cursor.execute(
                        "SELECT pk_post, id, title FROM benchmark.tb_post WHERE fk_author = %s",
                        (user_row[0],)
                    )
                    posts = cursor.fetchall()

                    # Get comments for all posts
                    post_pks = [p[0] for p in posts]
                    if post_pks:
                        cursor.execute(
                            "SELECT pk_comment, content, fk_post FROM benchmark.tb_comment "
                            "WHERE fk_post = ANY(%s)",
                            (post_pks,)
                        )
                        all_comments = cursor.fetchall()

                        # Group comments
                        comments_by_post = {}
                        for comment in all_comments:
                            post_pk = comment[2]
                            if post_pk not in comments_by_post:
                                comments_by_post[post_pk] = []
                            comments_by_post[post_pk].append(comment)

                        posts_with_comments = [
                            {'post': p, 'comments': comments_by_post.get(p[0], [])}
                            for p in posts
                        ]
                    else:
                        posts_with_comments = []

                    results.append({'user': user_row, 'posts': posts_with_comments})

                return results

        result = benchmark(query_stress)
        assert len(result) == 3

    def test_field_selection_impact(self, benchmark, db, factory):
        """Benchmark: Compare full vs sparse field selection.

        Expected: Sparse should be noticeably faster
        """
        # Create user with 20 posts
        user = factory.create_user('tester', 'tester@example.com', 'Tester User', 'Testing performance')
        for i in range(20):
            factory.create_post(
                user['pk_user'],
                f'Long Title For Post Number {i} With Extra Words',
                f'post-{i}',
                f'Very long content for post {i}' * 20  # Long content
            )

        def query_full_fields():
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT pk_user, id, username, identifier, email, full_name, bio, created_at, updated_at "
                    "FROM benchmark.tb_user WHERE id = %s",
                    (user['id'],)
                )
                user_row = cursor.fetchone()

                cursor.execute(
                    "SELECT pk_post, id, title, identifier, content, fk_author, created_at, updated_at "
                    "FROM benchmark.tb_post WHERE fk_author = %s",
                    (user_row[0],)
                )
                posts = cursor.fetchall()

                return {'user': user_row, 'posts': posts}

        result = benchmark(query_full_fields)
        assert result['user'] is not None
        assert len(result['posts']) == 20

    def test_multiple_relationships_parallel(self, benchmark, db, factory):
        """Benchmark: Query multiple independent relationships.

        Expected: <300ms
        """
        # Create user who is both author and commenter
        user = factory.create_user('active', 'active@example.com')

        # User authored 10 posts
        for i in range(10):
            factory.create_post(user['pk_user'], f'My Post {i}', f'my-post-{i}')

        # Create another user's post that our user commented on 15 times
        other_user = factory.create_user('other', 'other@example.com')
        other_post = factory.create_post(other_user['pk_user'], 'Other Post', 'other-post')
        for i in range(15):
            factory.create_comment(other_post['pk_post'], user['pk_user'], f'comment-{i}', f'Comment {i}')

        def query_parallel_relationships():
            with db.cursor() as cursor:
                # Get user
                cursor.execute(
                    "SELECT pk_user, id, username FROM benchmark.tb_user WHERE id = %s",
                    (user['id'],)
                )
                user_row = cursor.fetchone()

                # Get user's authored posts
                cursor.execute(
                    "SELECT id, title FROM benchmark.tb_post WHERE fk_author = %s",
                    (user_row[0],)
                )
                authored_posts = cursor.fetchall()

                # Get user's comments
                cursor.execute(
                    "SELECT id, content FROM benchmark.tb_comment WHERE fk_author = %s",
                    (user_row[0],)
                )
                comments = cursor.fetchall()

                return {
                    'user': user_row,
                    'authored_posts': authored_posts,
                    'comments': comments
                }

        result = benchmark(query_parallel_relationships)
        assert result['user'] is not None
        assert len(result['authored_posts']) == 10
        assert len(result['comments']) == 15

    def test_join_vs_separate_queries(self, benchmark, db, factory):
        """Benchmark: JOIN approach vs separate queries.

        Expected: JOIN should be competitive or faster
        """
        # Create 5 users with 4 posts each
        for i in range(5):
            user = factory.create_user(f'user{i}', f'user{i}@example.com')
            for j in range(4):
                factory.create_post(user['pk_user'], f'Post {j}', f'u{i}-p{j}')

        def query_with_join():
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        u.pk_user, u.id as user_id, u.username,
                        p.pk_post, p.id as post_id, p.title
                    FROM benchmark.tb_user u
                    LEFT JOIN benchmark.tb_post p ON p.fk_author = u.pk_user
                    ORDER BY u.pk_user, p.pk_post
                    LIMIT 100
                """)
                rows = cursor.fetchall()

                # Group by user
                users = {}
                for row in rows:
                    user_pk = row[0]
                    if user_pk not in users:
                        users[user_pk] = {
                            'user': (row[0], row[1], row[2]),
                            'posts': []
                        }
                    if row[3] is not None:
                        users[user_pk]['posts'].append((row[3], row[4], row[5]))

                return list(users.values())

        result = benchmark(query_with_join)
        assert len(result) == 5
        assert all(len(r['posts']) == 4 for r in result)
