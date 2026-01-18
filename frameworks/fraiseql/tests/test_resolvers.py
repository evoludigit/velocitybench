"""Tests for FraiseQL GraphQL resolvers.

Uses Trinity Identifier Pattern:
- pk_* = Integer primary key (internal, for FK relationships)
- id = UUID (external API identifier)
- fk_* = Integer foreign key (references pk_*)
"""

import pytest
from uuid import UUID


class TestUserQueries:
    """Test user query resolvers."""

    def test_query_user_by_uuid(self, factory):
        """Should return user by UUID."""
        user = factory.create_user("alice", "alice@example.com", "Alice Smith", "Hello!")

        result = factory.get_user(user["id"])

        assert result is not None
        assert result["id"] == user["id"]
        assert result["username"] == "alice"
        assert result["full_name"] == "Alice Smith"
        assert result["bio"] == "Hello!"

    def test_query_users_returns_list(self, factory):
        """Should return list of users."""
        factory.create_user("alice", "alice@example.com", "Alice")
        factory.create_user("bob", "bob@example.com", "Bob")
        factory.create_user("charlie", "charlie@example.com", "Charlie")

        users = factory.get_all_users()

        assert len(users) == 3

    def test_query_user_not_found(self, factory):
        """Should return None for non-existent user."""
        result = factory.get_user("00000000-0000-0000-0000-000000000000")

        assert result is None


class TestPostQueries:
    """Test post query resolvers."""

    def test_query_post_by_id(self, factory):
        """Should return post by ID."""
        user = factory.create_user("author", "author@example.com", "Author")
        # Use pk_user for FK relationship (Trinity Pattern)
        post = factory.create_post(user["pk_user"], "Test Post", "Test content")

        result = factory.get_post(post["id"])

        assert result is not None
        assert result["title"] == "Test Post"
        assert result["content"] == "Test content"

    def test_query_posts_by_author(self, factory):
        """Should return posts by author."""
        author = factory.create_user("author", "author@example.com", "Author")
        # Use pk_user for FK relationship
        factory.create_post(author["pk_user"], "Post 1", "Content 1")
        factory.create_post(author["pk_user"], "Post 2", "Content 2")

        posts = factory.get_posts_by_author(author["pk_user"])

        assert len(posts) == 2


class TestCommentQueries:
    """Test comment query resolvers."""

    def test_query_comment_by_id(self, factory):
        """Should return comment by ID."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author["pk_user"], "Test Post", "Content")
        commenter = factory.create_user("commenter", "commenter@example.com", "Commenter")
        # Use pk_user and pk_post for FK relationships
        comment = factory.create_comment(commenter["pk_user"], post["pk_post"], "Great post!")

        result = factory.get_comment(comment["id"])

        assert result is not None
        assert result["content"] == "Great post!"

    def test_query_comments_by_post(self, factory):
        """Should return comments by post."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author["pk_user"], "Test Post", "Content")
        commenter = factory.create_user("commenter", "commenter@example.com", "Commenter")
        factory.create_comment(commenter["pk_user"], post["pk_post"], "Comment 1")
        factory.create_comment(commenter["pk_user"], post["pk_post"], "Comment 2")

        comments = factory.get_comments_by_post(post["pk_post"])

        assert len(comments) == 2


class TestRelationships:
    """Test relationship resolvers."""

    def test_user_posts_relationship(self, factory):
        """Should resolve user posts."""
        user = factory.create_user("author", "author@example.com", "Author")
        post1 = factory.create_post(user["pk_user"], "Post 1", "Content 1")
        post2 = factory.create_post(user["pk_user"], "Post 2", "Content 2")

        posts = factory.get_posts_by_author(user["pk_user"])

        assert len(posts) == 2
        post_ids = [p["id"] for p in posts]
        assert post1["id"] in post_ids
        assert post2["id"] in post_ids

    def test_post_author_relationship(self, factory):
        """Should resolve post author."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author["pk_user"], "Test Post", "Content")

        assert post["author"] is not None
        assert post["author"]["pk_user"] == author["pk_user"]

    def test_comment_author_relationship(self, factory):
        """Should resolve comment author."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author["pk_user"], "Test Post", "Content")
        commenter = factory.create_user("commenter", "commenter@example.com", "Commenter")
        comment = factory.create_comment(commenter["pk_user"], post["pk_post"], "Great!")

        assert comment["author"] is not None
        assert comment["author"]["pk_user"] == commenter["pk_user"]


class TestEdgeCases:
    """Test edge cases."""

    def test_null_bio(self, factory):
        """Should handle null bio."""
        user = factory.create_user("user", "user@example.com", "User")

        assert user["bio"] is None

    def test_empty_posts_list(self, factory):
        """Should handle empty posts list."""
        user = factory.create_user("newuser", "new@example.com", "New User")

        posts = factory.get_posts_by_author(user["pk_user"])

        assert len(posts) == 0

    def test_special_characters_in_content(self, factory):
        """Should handle special characters."""
        user = factory.create_user("author", "author@example.com", "Author")
        special_content = "Test with 'quotes' and \"double quotes\" and <html>"
        post = factory.create_post(user["pk_user"], "Special", special_content)

        assert post["content"] == special_content

    def test_unicode_content(self, factory):
        """Should handle unicode content."""
        user = factory.create_user("author", "author@example.com", "Author")
        unicode_content = "Test with emojis and n and Chinese"
        post = factory.create_post(user["pk_user"], "Unicode", unicode_content)

        assert post["content"] == unicode_content


class TestValidation:
    """Test validation."""

    def test_valid_uuid(self, factory):
        """Should generate valid UUIDs."""
        user = factory.create_user("user", "user@example.com", "User")

        # Should not raise - id is already a string UUID
        UUID(user["id"])

    def test_create_post_with_invalid_author(self, factory):
        """Should raise for invalid author."""
        with pytest.raises(Exception):
            factory.create_post(99999999, "Test", "Content")  # Non-existent pk_user

    def test_create_comment_with_invalid_post(self, factory):
        """Should raise for invalid post."""
        user = factory.create_user("user", "user@example.com", "User")

        with pytest.raises(Exception):
            factory.create_comment(user["pk_user"], 99999999, "Content")  # Non-existent pk_post


class TestPerformance:
    """Test performance scenarios."""

    def test_create_many_posts(self, factory):
        """Should handle many posts."""
        user = factory.create_user("author", "author@example.com", "Author")

        for i in range(50):
            factory.create_post(user["pk_user"], f"Post {i}", "Content")

        posts = factory.get_posts_by_author(user["pk_user"])
        assert len(posts) == 50

    def test_reset(self, factory):
        """Should reset factory state."""
        factory.create_user("user1", "user1@example.com", "User 1")
        factory.create_user("user2", "user2@example.com", "User 2")

        factory.reset()

        assert len(factory.get_all_users()) == 0

    def test_long_content(self, factory):
        """Should handle long content."""
        user = factory.create_user("author", "author@example.com", "Author")
        long_content = "x" * 100000
        post = factory.create_post(user["pk_user"], "Long", long_content)

        assert len(post["content"]) == 100000
