"""Shared test data factory for VelocityBench test suites.

Provides TestFactory for creating test data with psycopg3.

Uses Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""

import pytest


@pytest.fixture
def factory(db):
    """Factory for creating test data using psycopg3."""

    class TestFactory:
        @staticmethod
        def create_user(
            username: str,
            email_or_identifier: str = None,
            email: str = None,
            full_name: str = None,
            bio: str = None,
        ) -> dict:
            """Create a test user in the command side (tb_user).

            Supports flexible calling:
            - create_user(username, email)
            - create_user(username, identifier, email)

            Args:
                username: Username
                email_or_identifier: Email or identifier (auto-detects based on context)
                email: Email address (optional, only if called with 3+ args)
                full_name: Full name (defaults to capitalized username)
                bio: Biography (optional)

            Returns:
                dict with pk_user, id (UUID), username, identifier, email, full_name, bio
            """
            # Auto-detect: if email_or_identifier looks like email and email is None, treat it as email
            if email is None and email_or_identifier and "@" in email_or_identifier:
                email = email_or_identifier
                identifier = username  # Use username as identifier
            else:
                identifier = email_or_identifier if email_or_identifier else username

            # full_name is required by schema, default to capitalized username if not provided
            if full_name is None:
                full_name = username.capitalize()

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
                        "pk_user": row[0],
                        "id": row[1],
                        "username": row[2],
                        "identifier": row[3],
                        "email": row[4],
                        "full_name": row[5],
                        "bio": row[6],
                    }
                return {}

        @staticmethod
        def create_post(
            fk_author: int,
            title: str,
            identifier: str = None,
            content: str = None,
        ) -> dict:
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
                identifier = title.lower().replace(" ", "-")

            # Auto-generate content if not provided
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
                        "pk_post": row[0],
                        "id": row[1],
                        "title": row[2],
                        "identifier": row[3],
                        "content": row[4],
                        "fk_author": row[5],
                    }
                return {}

        @staticmethod
        def create_comment(
            fk_post: int,
            fk_author: int,
            identifier: str,
            content: str,
        ) -> dict:
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
                        "pk_comment": row[0],
                        "id": row[1],
                        "identifier": row[2],
                        "content": row[3],
                        "fk_post": row[4],
                        "fk_author": row[5],
                    }
                return {}

    return TestFactory()
