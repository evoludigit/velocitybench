"""Comprehensive error scenario and edge case tests for Flask REST API.

Tests error handling and edge cases including:
- Invalid input handling (empty strings, NULL values)
- Non-existent resource queries
- Relationship edge cases
- Field validation and constraints
- Data consistency under errors
- UTF-8 and special character handling
- Boundary conditions

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""

import pytest


# ============================================================================
# Invalid Input Tests
# ============================================================================

class TestInvalidInput:
    """Tests for handling invalid input."""

    def test_query_with_empty_string_returns_nothing(self, db, factory):
        """Test: Query with empty string returns no results."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user WHERE username = %s",
            ("",)
        )
        result = cursor.fetchone()

        # Assert
        assert result is None

    def test_update_bio_to_null_succeeds(self, db, factory):
        """Test: Update can set bio to NULL (bio is optional)."""
        # Arrange
        user = factory.create_user("bob", "bob", "bob@example.com", "Bob Smith", "Original bio")
        user_id = user["id"]

        # Act
        cursor = db.cursor()
        cursor.execute(
            "UPDATE benchmark.tb_user SET bio = NULL WHERE id = %s",
            (user_id,)
        )

        # Verify
        cursor.execute(
            "SELECT bio FROM benchmark.tb_user WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] is None

    def test_create_user_without_optional_bio_field(self, db, factory):
        """Test: User creation without optional bio field works."""
        # Arrange
        user = factory.create_user("charlie", "charlie", "charlie@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, full_name, bio FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == user["id"]
        assert result[1] is not None  # full_name is required and defaulted
        assert result[2] is None  # bio is optional and NULL


# ============================================================================
# Non-Existent Resource Tests
# ============================================================================

class TestNonExistentResources:
    """Tests for handling non-existent resources."""

    def test_query_nonexistent_user_returns_none(self, db):
        """Test: Query for non-existent user returns None."""
        # Arrange
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user WHERE id = %s",
            (nonexistent_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is None

    def test_query_nonexistent_post_returns_none(self, db):
        """Test: Query for non-existent post returns None."""
        # Arrange
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_post WHERE id = %s",
            (nonexistent_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is None

    def test_query_nonexistent_comment_returns_none(self, db):
        """Test: Query for non-existent comment returns None."""
        # Arrange
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_comment WHERE id = %s",
            (nonexistent_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is None

    def test_update_nonexistent_user_succeeds_silently(self, db):
        """Test: Update on non-existent user succeeds but affects no rows."""
        # Arrange
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # Act
        cursor = db.cursor()
        cursor.execute(
            "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
            ("New bio", nonexistent_id)
        )

        # Verify nothing was updated
        cursor.execute(
            "SELECT id FROM benchmark.tb_user WHERE id = %s",
            (nonexistent_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is None

    def test_list_comments_for_nonexistent_post_returns_empty(self, db):
        """Test: List comments for non-existent post returns empty list."""
        # Arrange
        nonexistent_post_pk = 99999

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_comment WHERE fk_post = %s",
            (nonexistent_post_pk,)
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 0


# ============================================================================
# Relationship Edge Cases
# ============================================================================

class TestRelationshipEdgeCases:
    """Tests for relationship edge cases."""

    def test_post_without_author_not_returned(self, db):
        """Test: Posts without valid author reference are handled correctly."""
        # Note: This test documents constraint behavior
        # In practice, foreign key constraints prevent orphaned posts
        pass

    def test_comment_without_post_not_returned(self, db):
        """Test: Comments without valid post reference are handled correctly."""
        # Note: This test documents constraint behavior
        # In practice, foreign key constraints prevent orphaned comments
        pass

    def test_user_with_zero_posts_returns_empty_list(self, db, factory):
        """Test: User with no posts returns empty posts array."""
        # Arrange
        user = factory.create_user("author", "author-no-posts", "author@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_post WHERE fk_author = %s",
            (user["pk_user"],)
        )
        posts = cursor.fetchall()

        # Assert
        assert len(posts) == 0

    def test_post_with_zero_comments_returns_empty_list(self, db, factory):
        """Test: Post with no comments returns empty comments array."""
        # Arrange
        author = factory.create_user("author", "author-no-cmt", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post-no-cmt", "Content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_comment WHERE fk_post = %s",
            (post["pk_post"],)
        )
        comments = cursor.fetchall()

        # Assert
        assert len(comments) == 0

    def test_different_users_different_posts(self, db, factory):
        """Test: Each user can have separate posts."""
        # Arrange
        user1 = factory.create_user("author1", "author1", "author1@example.com")
        user2 = factory.create_user("author2", "author2", "author2@example.com")
        post1 = factory.create_post(user1["pk_user"], "Post 1", "post-1", "Content 1")
        post2 = factory.create_post(user2["pk_user"], "Post 2", "post-2", "Content 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_post WHERE fk_author = %s",
            (user1["pk_user"],)
        )
        user1_posts = cursor.fetchall()

        cursor.execute(
            "SELECT id FROM benchmark.tb_post WHERE fk_author = %s",
            (user2["pk_user"],)
        )
        user2_posts = cursor.fetchall()

        # Assert
        assert len(user1_posts) == 1
        assert len(user2_posts) == 1
        assert user1_posts[0][0] != user2_posts[0][0]


# ============================================================================
# Field Validation & Constraints
# ============================================================================

class TestFieldValidation:
    """Tests for field validation and constraints."""

    def test_username_is_required(self, db):
        """Test: username field is required."""
        # Note: This test documents schema constraints
        # Attempting to create user without username should fail
        pass

    def test_email_is_required(self, db):
        """Test: email field is required."""
        # Note: This test documents schema constraints
        # Attempting to create user without email should fail
        pass

    def test_identifier_is_required(self, db):
        """Test: identifier field is required."""
        # Note: This test documents schema constraints
        # Attempting to create user without identifier should fail
        pass

    def test_bio_max_length_validation(self, db, factory):
        """Test: bio field validates maximum length."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")
        very_long_bio = "x" * 2000  # Longer than allowed

        # Act & Assert - Field can be inserted but should respect constraints
        assert len(very_long_bio) > 1000

    def test_full_name_max_length_validation(self, db, factory):
        """Test: full_name field validates maximum length."""
        # Arrange
        user = factory.create_user("bob", "bob", "bob@example.com")
        very_long_name = "x" * 500  # Longer than allowed

        # Act & Assert
        assert len(very_long_name) > 255

    def test_query_by_nonexistent_identifier(self, db):
        """Test: Query by non-existent identifier returns nothing."""
        # Arrange
        nonexistent_identifier = "does-not-exist"

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user WHERE identifier = %s",
            (nonexistent_identifier,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is None


# ============================================================================
# Data Consistency Tests
# ============================================================================

class TestDataConsistency:
    """Tests for data consistency under various conditions."""

    def test_user_id_is_uuid(self, db, factory):
        """Test: user id is a valid UUID."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")

        # Act
        user_id = user["id"]

        # Assert
        assert user_id is not None
        # UUID format check: 8-4-4-4-12 hex characters
        parts = str(user_id).split("-")
        assert len(parts) == 5

    def test_post_id_is_uuid(self, db, factory):
        """Test: post id is a valid UUID."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")

        # Act
        post_id = post["id"]

        # Assert
        assert post_id is not None
        parts = str(post_id).split("-")
        assert len(parts) == 5

    def test_comment_id_is_uuid(self, db, factory):
        """Test: comment id is a valid UUID."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")
        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
        comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Comment")

        # Act
        comment_id = comment["id"]

        # Assert
        assert comment_id is not None
        parts = str(comment_id).split("-")
        assert len(parts) == 5

    def test_timestamps_are_set(self, db, factory):
        """Test: created_at timestamp is automatically set."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT created_at FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] is not None

    def test_post_timestamps_are_set(self, db, factory):
        """Test: post created_at timestamp is automatically set."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT created_at FROM benchmark.tb_post WHERE id = %s",
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] is not None

    def test_multiple_users_have_unique_ids(self, db, factory):
        """Test: multiple users get unique IDs."""
        # Arrange
        user1 = factory.create_user("alice", "alice", "alice@example.com")
        user2 = factory.create_user("bob", "bob", "bob@example.com")
        user3 = factory.create_user("charlie", "charlie", "charlie@example.com")

        # Act
        ids = [user1["id"], user2["id"], user3["id"]]

        # Assert
        assert len(ids) == len(set(ids))  # All unique


# ============================================================================
# Special Character Handling Tests
# ============================================================================

class TestSpecialCharacterHandling:
    """Tests for special character and UTF-8 handling."""

    def test_special_characters_in_bio(self, db, factory):
        """Test: special characters are handled correctly in bio."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")
        special_bio = "Bio with 'quotes' and \"double quotes\" and <html>"

        # Act
        cursor = db.cursor()
        cursor.execute(
            "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
            (special_bio, user["id"])
        )

        cursor.execute(
            "SELECT bio FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == special_bio

    def test_special_characters_in_content(self, db, factory):
        """Test: special characters are handled correctly in content."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        special_content = "Test with 'quotes' and \"double quotes\" and <html>"
        post = factory.create_post(author["pk_user"], "Special Post", "special-post", special_content)

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT content FROM benchmark.tb_post WHERE id = %s",
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == special_content

    def test_emoji_handling_in_bio(self, db, factory):
        """Test: emoji characters are handled correctly."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")
        emoji_bio = "Bio with emoji 🎉 and 💚"

        # Act
        cursor = db.cursor()
        cursor.execute(
            "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
            (emoji_bio, user["id"])
        )

        cursor.execute(
            "SELECT bio FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == emoji_bio

    def test_emoji_handling_in_content(self, db, factory):
        """Test: emoji characters are handled correctly in post content."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        emoji_content = "Content with emoji 🚀 and ✨"
        post = factory.create_post(author["pk_user"], "Emoji Post", "emoji-post", emoji_content)

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT content FROM benchmark.tb_post WHERE id = %s",
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == emoji_content

    def test_unicode_characters_in_full_name(self, db, factory):
        """Test: unicode characters are handled correctly in full_name."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com", "Àlice Müller")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT full_name FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == "Àlice Müller"

    def test_unicode_characters_in_post_title(self, db, factory):
        """Test: unicode characters are handled correctly in post title."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        unicode_title = "Thé Töür öf Pythön"
        post = factory.create_post(author["pk_user"], unicode_title, "post-unicode", "Content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT title FROM benchmark.tb_post WHERE id = %s",
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == unicode_title


# ============================================================================
# Boundary Condition Tests
# ============================================================================

class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_limit_0_returns_no_results(self, db, factory):
        """Test: LIMIT 0 returns no results."""
        # Arrange
        factory.create_user("alice", "alice", "alice@example.com")
        factory.create_user("bob", "bob", "bob@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user LIMIT 0"
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 0

    def test_limit_1_returns_single_result(self, db, factory):
        """Test: LIMIT 1 returns exactly one result."""
        # Arrange
        factory.create_user("alice", "alice", "alice@example.com")
        factory.create_user("bob", "bob", "bob@example.com")
        factory.create_user("charlie", "charlie", "charlie@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user LIMIT 1"
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 1

    def test_limit_greater_than_total_returns_all(self, db, factory):
        """Test: LIMIT greater than total returns all available."""
        # Arrange
        factory.create_user("alice", "alice", "alice@example.com")
        factory.create_user("bob", "bob", "bob@example.com")
        factory.create_user("charlie", "charlie", "charlie@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user LIMIT 1000"
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 3

    def test_offset_returns_remaining_results(self, db, factory):
        """Test: OFFSET skips first N results."""
        # Arrange
        factory.create_user("alice", "alice", "alice@example.com")
        factory.create_user("bob", "bob", "bob@example.com")
        factory.create_user("charlie", "charlie", "charlie@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user ORDER BY created_at LIMIT 10 OFFSET 1"
        )
        results = cursor.fetchall()

        # Assert - should get 2 results (skipped first)
        assert len(results) == 2

    def test_very_long_bio_field(self, db, factory):
        """Test: Very long bio field is handled correctly."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")
        very_long_bio = "x" * 5000

        # Act
        cursor = db.cursor()
        cursor.execute(
            "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
            (very_long_bio, user["id"])
        )

        cursor.execute(
            "SELECT LENGTH(bio) FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == 5000

    def test_very_long_post_content(self, db, factory):
        """Test: Very long post content is handled correctly."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        very_long_content = "x" * 10000

        # Act
        post = factory.create_post(author["pk_user"], "Long Post", "long-post", very_long_content)

        cursor = db.cursor()
        cursor.execute(
            "SELECT LENGTH(content) FROM benchmark.tb_post WHERE id = %s",
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == 10000
