"""Bulk factory for creating large amounts of test data efficiently.

Provides methods for:
- Creating multiple users
- Creating users with multiple posts
- Creating posts with multiple comments
- Cleanup and counting utilities
"""

import pytest


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
                            f"Bio for {prefix}{i}",
                        ),
                    )
                    row = cursor.fetchone()
                    if row:
                        users.append(
                            {
                                "pk_user": row[0],
                                "id": row[1],
                                "username": row[2],
                                "identifier": row[3],
                                "email": row[4],
                                "full_name": row[5],
                                "bio": row[6],
                            }
                        )
            return users

        @staticmethod
        def create_user_with_posts(
            username: str,
            identifier: str,
            email: str,
            post_count: int = 5,
        ) -> dict:
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
                    (
                        username,
                        identifier,
                        email,
                        f"{username.title()}",
                        f"Bio for {username}",
                    ),
                )
                user_row = cursor.fetchone()
                user = {
                    "pk_user": user_row[0],
                    "id": user_row[1],
                    "username": user_row[2],
                    "identifier": user_row[3],
                    "email": user_row[4],
                    "full_name": user_row[5],
                    "bio": user_row[6],
                }

                posts = []
                for i in range(post_count):
                    cursor.execute(
                        "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
                        "VALUES (%s, %s, %s, %s) "
                        "RETURNING pk_post, id, title, identifier, content, fk_author",
                        (
                            user["pk_user"],
                            f"Post {i} by {username}",
                            f"post-{username}-{i}",
                            f"Content for post {i}",
                        ),
                    )
                    post_row = cursor.fetchone()
                    if post_row:
                        posts.append(
                            {
                                "pk_post": post_row[0],
                                "id": post_row[1],
                                "title": post_row[2],
                                "identifier": post_row[3],
                                "content": post_row[4],
                                "fk_author": post_row[5],
                            }
                        )

            return {"user": user, "posts": posts}

        @staticmethod
        def create_post_with_comments(
            author_pk: int,
            title: str,
            identifier: str,
            comment_count: int = 3,
        ) -> dict:
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
                    "pk_post": post_row[0],
                    "id": post_row[1],
                    "title": post_row[2],
                    "identifier": post_row[3],
                    "content": post_row[4],
                    "fk_author": post_row[5],
                }

                # Create commenter
                cursor.execute(
                    "INSERT INTO benchmark.tb_user (username, identifier, email, full_name, bio) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING pk_user, id",
                    (
                        f"commenter-{identifier}",
                        f"commenter-{identifier}",
                        f"commenter-{identifier}@example.com",
                        "Commenter",
                        "I comment",
                    ),
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
                            post["pk_post"],
                            commenter_pk,
                            f"comment-{i}",
                            f"Comment {i} on {title}",
                        ),
                    )
                    cmt_row = cursor.fetchone()
                    if cmt_row:
                        comments.append(
                            {
                                "pk_comment": cmt_row[0],
                                "id": cmt_row[1],
                                "identifier": cmt_row[2],
                                "content": cmt_row[3],
                                "fk_post": cmt_row[4],
                                "fk_author": cmt_row[5],
                            }
                        )

            return {
                "post": post,
                "comments": comments,
                "commenter_pk": commenter_pk,
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
                    cursor.execute(
                        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
                        (author_pk,),
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
                return cursor.fetchone()[0]

        @staticmethod
        def get_comment_count(post_pk: int = None) -> int:
            """Get total number of comments, optionally filtered by post."""
            with db.cursor() as cursor:
                if post_pk:
                    cursor.execute(
                        "SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s",
                        (post_pk,),
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_comment")
                return cursor.fetchone()[0]

    return BulkFactory()
