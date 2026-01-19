"""Performance benchmarks for relationship traversal queries.

Tests query performance when traversing foreign key relationships
with different nesting levels.

Expected latency:
- Shallow nesting (1 level): <100ms
- Medium nesting (2 levels): <200ms
- Deep nesting (3 levels): <500ms (should scale linearly)

Uses pytest-benchmark for timing measurements and TestFactory for data creation.
"""

import pytest


@pytest.mark.perf
@pytest.mark.perf_queries
class TestRelationshipQueries:
    """Relationship traversal query benchmarks."""

    def test_user_with_posts_shallow(self, benchmark, db, factory):
        """Benchmark: User with posts (1-level nesting).

        Expected: <100ms
        """
        # Create user with 5 posts
        user = factory.create_user('alice', 'alice@example.com')
        for i in range(5):
            factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')

        def query_user_with_posts():
            with db.cursor() as cursor:
                # Get user
                cursor.execute(
                    "SELECT pk_user, id, username FROM benchmark.tb_user WHERE id = %s",
                    (user['id'],)
                )
                user_row = cursor.fetchone()

                # Get user's posts
                cursor.execute(
                    "SELECT id, title FROM benchmark.tb_post WHERE fk_author = %s",
                    (user_row[0],)
                )
                posts = cursor.fetchall()

                return {'user': user_row, 'posts': posts}

        result = benchmark(query_user_with_posts)
        assert result['user'] is not None
        assert len(result['posts']) == 5

    def test_post_with_author(self, benchmark, db, factory):
        """Benchmark: Post with author (1-level relationship).

        Expected: <50ms
        """
        user = factory.create_user('author', 'author@example.com')
        post = factory.create_post(user['pk_user'], 'My Post', 'my-post')

        def query_post_with_author():
            with db.cursor() as cursor:
                # Get post
                cursor.execute(
                    "SELECT pk_post, id, title, fk_author FROM benchmark.tb_post WHERE id = %s",
                    (post['id'],)
                )
                post_row = cursor.fetchone()

                # Get author
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user WHERE pk_user = %s",
                    (post_row[3],)
                )
                author_row = cursor.fetchone()

                return {'post': post_row, 'author': author_row}

        result = benchmark(query_post_with_author)
        assert result['post'] is not None
        assert result['author'] is not None

    def test_post_with_comments(self, benchmark, db, factory):
        """Benchmark: Post with comments (1-level nesting).

        Expected: <100ms
        """
        user = factory.create_user('poster', 'poster@example.com')
        post = factory.create_post(user['pk_user'], 'Popular Post', 'popular')

        # Create 10 comments
        for i in range(10):
            factory.create_comment(post['pk_post'], user['pk_user'], f'comment-{i}', f'Comment {i}')

        def query_post_with_comments():
            with db.cursor() as cursor:
                # Get post
                cursor.execute(
                    "SELECT pk_post, id, title FROM benchmark.tb_post WHERE id = %s",
                    (post['id'],)
                )
                post_row = cursor.fetchone()

                # Get comments
                cursor.execute(
                    "SELECT id, content FROM benchmark.tb_comment WHERE fk_post = %s",
                    (post_row[0],)
                )
                comments = cursor.fetchall()

                return {'post': post_row, 'comments': comments}

        result = benchmark(query_post_with_comments)
        assert result['post'] is not None
        assert len(result['comments']) == 10

    def test_comment_with_author(self, benchmark, db, factory):
        """Benchmark: Comment with author (1-level relationship).

        Expected: <50ms
        """
        user = factory.create_user('commenter', 'commenter@example.com')
        post = factory.create_post(user['pk_user'], 'Post', 'post-1')
        comment = factory.create_comment(post['pk_post'], user['pk_user'], 'comment-1', 'Test')

        def query_comment_with_author():
            with db.cursor() as cursor:
                # Get comment
                cursor.execute(
                    "SELECT pk_comment, id, content, fk_author FROM benchmark.tb_comment WHERE id = %s",
                    (comment['id'],)
                )
                comment_row = cursor.fetchone()

                # Get author
                cursor.execute(
                    "SELECT id, username FROM benchmark.tb_user WHERE pk_user = %s",
                    (comment_row[3],)
                )
                author_row = cursor.fetchone()

                return {'comment': comment_row, 'author': author_row}

        result = benchmark(query_comment_with_author)
        assert result['comment'] is not None
        assert result['author'] is not None

    def test_user_posts_comments_two_level(self, benchmark, db, factory):
        """Benchmark: User → Posts → Comments (2-level nesting).

        Expected: <200ms
        """
        user = factory.create_user('alice', 'alice@example.com')

        # Create 3 posts, each with 3 comments
        for i in range(3):
            post = factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')
            for j in range(3):
                factory.create_comment(post['pk_post'], user['pk_user'], f'c-{i}-{j}', f'Comment {j}')

        def query_user_posts_comments():
            with db.cursor() as cursor:
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

                # Get comments for each post
                result_posts = []
                for post_row in posts:
                    cursor.execute(
                        "SELECT id, content FROM benchmark.tb_comment WHERE fk_post = %s",
                        (post_row[0],)
                    )
                    comments = cursor.fetchall()
                    result_posts.append({'post': post_row, 'comments': comments})

                return {'user': user_row, 'posts': result_posts}

        result = benchmark(query_user_posts_comments)
        assert result['user'] is not None
        assert len(result['posts']) == 3
        assert all(len(p['comments']) == 3 for p in result['posts'])

    def test_post_comments_authors_two_level(self, benchmark, db, factory):
        """Benchmark: Post → Comments → Authors (2-level nesting).

        Expected: <200ms
        """
        author = factory.create_user('author', 'author@example.com')
        post = factory.create_post(author['pk_user'], 'Article', 'article')

        # Create 5 different commenters
        commenters = []
        for i in range(5):
            commenter = factory.create_user(f'commenter{i}', f'commenter{i}@example.com')
            commenters.append(commenter)
            factory.create_comment(post['pk_post'], commenter['pk_user'], f'comment-{i}', f'Comment {i}')

        def query_post_comments_authors():
            with db.cursor() as cursor:
                # Get post
                cursor.execute(
                    "SELECT pk_post, id, title FROM benchmark.tb_post WHERE id = %s",
                    (post['id'],)
                )
                post_row = cursor.fetchone()

                # Get comments
                cursor.execute(
                    "SELECT pk_comment, id, content, fk_author FROM benchmark.tb_comment WHERE fk_post = %s",
                    (post_row[0],)
                )
                comments = cursor.fetchall()

                # Get author for each comment
                result_comments = []
                for comment_row in comments:
                    cursor.execute(
                        "SELECT id, username FROM benchmark.tb_user WHERE pk_user = %s",
                        (comment_row[3],)
                    )
                    author_row = cursor.fetchone()
                    result_comments.append({'comment': comment_row, 'author': author_row})

                return {'post': post_row, 'comments': result_comments}

        result = benchmark(query_post_comments_authors)
        assert result['post'] is not None
        assert len(result['comments']) == 5

    def test_deep_nesting_three_levels(self, benchmark, db, factory):
        """Benchmark: User → Posts → Comments → Comment Authors (3-level nesting).

        Expected: <500ms
        """
        user = factory.create_user('alice', 'alice@example.com')

        # Create 2 posts, each with 2 comments from different users
        for i in range(2):
            post = factory.create_post(user['pk_user'], f'Post {i}', f'post-{i}')
            for j in range(2):
                commenter = factory.create_user(f'commenter-{i}-{j}', f'c{i}{j}@example.com')
                factory.create_comment(post['pk_post'], commenter['pk_user'], f'c-{i}-{j}', f'Comment {j}')

        def query_deep_structure():
            with db.cursor() as cursor:
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

                # Get comments for each post
                result_posts = []
                for post_row in posts:
                    cursor.execute(
                        "SELECT pk_comment, id, content, fk_author FROM benchmark.tb_comment WHERE fk_post = %s",
                        (post_row[0],)
                    )
                    comments = cursor.fetchall()

                    # Get author for each comment
                    result_comments = []
                    for comment_row in comments:
                        cursor.execute(
                            "SELECT id, username FROM benchmark.tb_user WHERE pk_user = %s",
                            (comment_row[3],)
                        )
                        author_row = cursor.fetchone()
                        result_comments.append({'comment': comment_row, 'author': author_row})

                    result_posts.append({'post': post_row, 'comments': result_comments})

                return {'user': user_row, 'posts': result_posts}

        result = benchmark(query_deep_structure)
        assert result['user'] is not None
        assert len(result['posts']) == 2
        assert all(len(p['comments']) == 2 for p in result['posts'])

    def test_multiple_users_with_posts(self, benchmark, db, factory):
        """Benchmark: Multiple users with their posts (N users × M posts).

        Expected: <150ms for 5 users × 3 posts each
        """
        # Create 5 users, each with 3 posts
        users = []
        for i in range(5):
            user = factory.create_user(f'user{i}', f'user{i}@example.com')
            users.append(user)
            for j in range(3):
                factory.create_post(user['pk_user'], f'User{i} Post{j}', f'u{i}-p{j}')

        def query_users_with_posts():
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
                        "SELECT id, title FROM benchmark.tb_post WHERE fk_author = %s",
                        (user_row[0],)
                    )
                    posts = cursor.fetchall()

                    results.append({'user': user_row, 'posts': posts})

                return results

        result = benchmark(query_users_with_posts)
        assert len(result) == 5
        assert all(len(r['posts']) == 3 for r in result)
