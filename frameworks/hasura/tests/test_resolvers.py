"""Tests for Hasura GraphQL resolvers (integration test pattern)."""

import pytest
from uuid import UUID
from test_factory import TestFactory, ValidationHelper, DataGenerator


@pytest.fixture
def factory():
    """Provide a fresh TestFactory for each test."""
    f = TestFactory()
    yield f
    f.reset()


class TestUserQueries:
    """Test user query resolvers."""

    def test_query_user_by_uuid(self, factory):
        """Should return user by UUID."""
        user = factory.create_user("alice", "alice@example.com", "Alice Smith", "Hello!")

        result = factory.get_user(user.id)

        assert result is not None
        assert result.id == user.id
        assert result.username == "alice"
        assert result.full_name == "Alice Smith"
        assert result.bio == "Hello!"

    def test_query_users_returns_list(self, factory):
        """Should return list of users."""
        factory.create_user("alice", "alice@example.com", "Alice")
        factory.create_user("bob", "bob@example.com", "Bob")
        factory.create_user("charlie", "charlie@example.com", "Charlie")

        users = factory.get_all_users()

        assert len(users) == 3

    def test_query_user_not_found(self, factory):
        """Should return None for non-existent user."""
        result = factory.get_user("non-existent-id")

        assert result is None


class TestPostQueries:
    """Test post query resolvers."""

    def test_query_post_by_id(self, factory):
        """Should return post by ID."""
        user = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(user.id, "Test Post", "Test content")

        result = factory.get_post(post.id)

        assert result is not None
        assert result.title == "Test Post"
        assert result.content == "Test content"

    def test_query_posts_by_author(self, factory):
        """Should return posts by author."""
        author = factory.create_user("author", "author@example.com", "Author")
        factory.create_post(author.id, "Post 1", "Content 1")
        factory.create_post(author.id, "Post 2", "Content 2")

        posts = factory.get_posts_by_author(author.pk_user)

        assert len(posts) == 2


class TestCommentQueries:
    """Test comment query resolvers."""

    def test_query_comment_by_id(self, factory):
        """Should return comment by ID."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author.id, "Test Post", "Content")
        commenter = factory.create_user("commenter", "commenter@example.com", "Commenter")
        comment = factory.create_comment(commenter.id, post.id, "Great post!")

        result = factory.get_comment(comment.id)

        assert result is not None
        assert result.content == "Great post!"

    def test_query_comments_by_post(self, factory):
        """Should return comments by post."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author.id, "Test Post", "Content")
        commenter = factory.create_user("commenter", "commenter@example.com", "Commenter")
        factory.create_comment(commenter.id, post.id, "Comment 1")
        factory.create_comment(commenter.id, post.id, "Comment 2")

        comments = factory.get_comments_by_post(post.pk_post)

        assert len(comments) == 2


class TestRelationships:
    """Test relationship resolvers."""

    def test_user_posts_relationship(self, factory):
        """Should resolve user posts."""
        user = factory.create_user("author", "author@example.com", "Author")
        post1 = factory.create_post(user.id, "Post 1", "Content 1")
        post2 = factory.create_post(user.id, "Post 2", "Content 2")

        posts = factory.get_posts_by_author(user.pk_user)

        assert len(posts) == 2
        post_ids = [p.id for p in posts]
        assert post1.id in post_ids
        assert post2.id in post_ids

    def test_post_author_relationship(self, factory):
        """Should resolve post author."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author.id, "Test Post", "Content")

        assert post.author is not None
        assert post.author.pk_user == author.pk_user

    def test_comment_author_relationship(self, factory):
        """Should resolve comment author."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author.id, "Test Post", "Content")
        commenter = factory.create_user("commenter", "commenter@example.com", "Commenter")
        comment = factory.create_comment(commenter.id, post.id, "Great!")

        assert comment.author is not None
        assert comment.author.pk_user == commenter.pk_user


class TestEdgeCases:
    """Test edge cases."""

    def test_null_bio(self, factory):
        """Should handle null bio."""
        user = factory.create_user("user", "user@example.com", "User")

        assert user.bio is None

    def test_empty_posts_list(self, factory):
        """Should handle empty posts list."""
        user = factory.create_user("newuser", "new@example.com", "New User")

        posts = factory.get_posts_by_author(user.pk_user)

        assert len(posts) == 0

    def test_special_characters_in_content(self, factory):
        """Should handle special characters."""
        user = factory.create_user("author", "author@example.com", "Author")
        special_content = "Test with 'quotes' and \"double quotes\" and <html>"
        post = factory.create_post(user.id, "Special", special_content)

        assert post.content == special_content

    def test_unicode_content(self, factory):
        """Should handle unicode content."""
        user = factory.create_user("author", "author@example.com", "Author")
        unicode_content = "Test with émojis 🎉 and ñ and 中文"
        post = factory.create_post(user.id, "Unicode", unicode_content)

        assert post.content == unicode_content


class TestValidation:
    """Test validation."""

    def test_valid_uuid(self, factory):
        """Should generate valid UUIDs."""
        user = factory.create_user("user", "user@example.com", "User")

        assert ValidationHelper.is_valid_uuid(user.id)

    def test_create_post_with_invalid_author(self, factory):
        """Should raise for invalid author."""
        with pytest.raises(ValueError):
            factory.create_post("invalid-author", "Test", "Content")

    def test_create_comment_with_invalid_post(self, factory):
        """Should raise for invalid post."""
        user = factory.create_user("user", "user@example.com", "User")

        with pytest.raises(ValueError):
            factory.create_comment(user.id, "invalid-post", "Content")


class TestPerformance:
    """Test performance scenarios."""

    def test_create_many_posts(self, factory):
        """Should handle many posts."""
        user = factory.create_user("author", "author@example.com", "Author")

        for i in range(50):
            factory.create_post(user.id, f"Post {i}", "Content")

        posts = factory.get_posts_by_author(user.pk_user)
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
        long_content = DataGenerator.generate_long_string(100000)
        post = factory.create_post(user.id, "Long", long_content)

        assert len(post.content) == 100000
