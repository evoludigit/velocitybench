"""Shared error scenario and edge case tests.

Tests error handling and edge cases including:
- Invalid input handling
- Non-existent resource queries (404 errors)
- Relationship edge cases
- Field validation and constraints
- Data consistency
- UTF-8 and special character handling
- Boundary conditions

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access

These tests are shared across all frameworks. Framework-specific test wrappers
(if needed for async/class-based patterns) should import these tests.
"""

import pytest


# ============================================================================
# Invalid Input Tests
# ============================================================================

def test_query_with_empty_string_returns_nothing(db, factory):
    """Test: Query with empty string parameter returns no results."""
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


def test_update_bio_to_null_succeeds(db, factory):
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


def test_create_user_without_optional_bio_field(db, factory):
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
# Non-Existent Resource Tests (404 Errors)
# ============================================================================

def test_query_nonexistent_user_returns_none(db):
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


def test_query_nonexistent_post_returns_none(db):
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


def test_query_nonexistent_comment_returns_none(db):
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


def test_update_nonexistent_user_succeeds_silently(db):
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


def test_list_comments_for_nonexistent_post_returns_empty(db):
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


def test_query_by_nonexistent_identifier(db):
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
# Relationship Edge Cases
# ============================================================================

def test_user_with_zero_posts_returns_empty_list(db, factory):
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


def test_post_with_zero_comments_returns_empty_list(db, factory):
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


def test_different_users_have_separate_posts(db, factory):
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


def test_multiple_posts_maintain_correct_author_relationship(db, factory):
    """Test: Multiple posts maintain correct author FK."""
    # Arrange
    author = factory.create_user("author", "author-multi", "author@example.com")
    post1 = factory.create_post(author["pk_user"], "Post 1", "post-rel-1", "Content 1")
    post2 = factory.create_post(author["pk_user"], "Post 2", "post-rel-2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT fk_author FROM benchmark.tb_post WHERE id IN (%s, %s)",
        (post1["id"], post2["id"])
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 2
    assert results[0][0] == author["pk_user"]
    assert results[1][0] == author["pk_user"]


def test_comments_correctly_associated_with_posts(db, factory):
    """Test: Comments maintain correct association with posts."""
    # Arrange
    author = factory.create_user("author", "author-assoc", "author@example.com")
    post1 = factory.create_post(author["pk_user"], "Post 1", "post-assoc-1", "Content")
    post2 = factory.create_post(author["pk_user"], "Post 2", "post-assoc-2", "Content")

    commenter = factory.create_user("commenter", "commenter-assoc", "commenter@example.com")
    comment1 = factory.create_comment(post1["pk_post"], commenter["pk_user"], "cmt-1", "Comment 1")
    comment2 = factory.create_comment(post2["pk_post"], commenter["pk_user"], "cmt-2", "Comment 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT fk_post FROM benchmark.tb_comment WHERE id = %s",
        (comment1["id"],)
    )
    result1 = cursor.fetchone()

    cursor.execute(
        "SELECT fk_post FROM benchmark.tb_comment WHERE id = %s",
        (comment2["id"],)
    )
    result2 = cursor.fetchone()

    # Assert
    assert result1[0] == post1["pk_post"]
    assert result2[0] == post2["pk_post"]


# ============================================================================
# Data Consistency Tests
# ============================================================================

def test_user_id_is_uuid(db, factory):
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


def test_post_id_is_uuid(db, factory):
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


def test_comment_id_is_uuid(db, factory):
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


def test_timestamps_are_set(db, factory):
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


def test_post_timestamps_are_set(db, factory):
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


def test_multiple_users_have_unique_ids(db, factory):
    """Test: multiple users get unique IDs."""
    # Arrange
    user1 = factory.create_user("alice", "alice", "alice@example.com")
    user2 = factory.create_user("bob", "bob", "bob@example.com")
    user3 = factory.create_user("charlie", "charlie", "charlie@example.com")

    # Act
    ids = [user1["id"], user2["id"], user3["id"]]

    # Assert
    assert len(ids) == len(set(ids))  # All unique


def test_multiple_users_do_not_interfere(db, factory):
    """Test: Operations on one user don't affect others."""
    # Arrange
    user1 = factory.create_user("user1", "user-1", "user1@example.com")
    user2 = factory.create_user("user2", "user-2", "user2@example.com")
    original_user2_bio = user2["bio"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        ("User 1 new bio", user1["id"])
    )

    # Assert
    cursor.execute("SELECT bio FROM benchmark.tb_user WHERE id = %s", (user2["id"],))
    result = cursor.fetchone()
    assert result[0] == original_user2_bio


def test_multi_field_update_does_not_leak_to_other_users(db, factory):
    """Test: Multi-field update on one user doesn't leak to others."""
    # Arrange
    user1 = factory.create_user("alice", "alice-1", "alice@example.com", "Alice", "Bio1")
    user2 = factory.create_user("bob", "bob-2", "bob@example.com", "Bob", "Bio2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, full_name = %s WHERE id = %s",
        ("Alice new bio", "Alice Updated", user1["id"])
    )

    # Assert
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user2["id"],)
    )
    result = cursor.fetchone()
    assert result[0] == "Bio2"
    assert result[1] == "Bob"


def test_relationship_integrity_after_bulk_updates(db, factory):
    """Test: Bulk updates don't break relationships."""
    # Arrange
    author = factory.create_user("author", "author-bulk", "author@example.com")
    posts = [
        factory.create_post(author["pk_user"], f"Post {i}", f"post-bulk-{i}", f"Content {i}")
        for i in range(5)
    ]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_post SET updated_at = NOW() WHERE fk_author = %s",
        (author["pk_user"],)
    )

    # Assert
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (author["pk_user"],)
    )
    count = cursor.fetchone()[0]
    assert count == 5


# ============================================================================
# Special Character Handling Tests
# ============================================================================

def test_special_characters_in_bio(db, factory):
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


def test_special_characters_in_content(db, factory):
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


def test_emoji_handling_in_bio(db, factory):
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


def test_emoji_handling_in_content(db, factory):
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


def test_unicode_characters_in_full_name(db, factory):
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


def test_unicode_characters_in_post_title(db, factory):
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

def test_limit_0_returns_no_results(db, factory):
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


def test_limit_1_returns_single_result(db, factory):
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


def test_limit_greater_than_total_returns_all(db, factory):
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


def test_offset_returns_remaining_results(db, factory):
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


def test_very_long_bio_field(db, factory):
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


def test_very_long_post_content(db, factory):
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
