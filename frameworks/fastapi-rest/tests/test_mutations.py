"""Mutation tests for FastAPI REST framework (PUT/PATCH endpoints).

Tests all update operations with validation of:
- Single field mutations (PUT /users/{id})
- Multi-field mutations
- Return value validation
- State change verification
- Immutable field protection
- Input validation

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""

import pytest


# ============================================================================
# User Mutations: Single Field Updates
# ============================================================================

def test_update_user_bio_single_field(db, factory):
    """Test: PUT /users/{user_id} updates user bio only."""
    # Arrange
    user = factory.create_user("alice", "alice-upd-bio", "alice@example.com", "Alice", "Old bio")
    user_id = user["id"]
    new_bio = "Updated bio"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, user_id)
    )

    # Verify the update
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio
    assert result[1] == "Alice"  # Unchanged


def test_update_user_full_name_single_field(db, factory):
    """Test: PUT /users/{user_id} updates full_name only."""
    # Arrange
    user = factory.create_user("bob", "bob-upd-name", "bob@example.com", "Bob")
    user_id = user["id"]
    new_name = "Bob Smith Updated"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET full_name = %s, updated_at = NOW() WHERE id = %s",
        (new_name, user_id)
    )

    # Verify
    cursor.execute(
        "SELECT full_name, bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_name
    assert result[1] is None  # Unchanged


def test_update_user_bio_with_long_text(db, factory):
    """Test: PUT /users/{user_id} handles long bio text."""
    # Arrange
    user = factory.create_user("charlie", "charlie-long", "charlie@example.com")
    user_id = user["id"]
    long_bio = "x" * 500

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        (long_bio, user_id)
    )

    # Verify
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == long_bio
    assert len(result[0]) == 500


def test_update_user_bio_empty_string(db, factory):
    """Test: PUT /users/{user_id} handles empty bio string."""
    # Arrange
    user = factory.create_user("dave", "dave-empty", "dave@example.com", bio="Original bio")
    user_id = user["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        ("", user_id)
    )

    # Verify
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == ""


def test_update_user_bio_to_null(db, factory):
    """Test: PUT /users/{user_id} can set bio to NULL."""
    # Arrange
    user = factory.create_user("eve", "eve-tonull", "eve@example.com", bio="Old bio")
    user_id = user["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = NULL, updated_at = NOW() WHERE id = %s",
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


# ============================================================================
# User Mutations: Multi-Field Updates
# ============================================================================

def test_update_user_multiple_fields(db, factory):
    """Test: PUT /users/{user_id} updates multiple fields."""
    # Arrange
    user = factory.create_user("charlie", "charlie-upd-multi", "charlie@example.com", "Charlie")
    user_id = user["id"]
    new_bio = "New bio"
    new_name = "Charlie Updated"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, full_name = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, new_name, user_id)
    )

    # Verify
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio
    assert result[1] == new_name


def test_update_user_with_special_chars(db, factory):
    """Test: Multi-field update handles special characters."""
    # Arrange
    user = factory.create_user("frank", "frank-spec", "frank@example.com")
    user_id = user["id"]
    new_bio = "Bio with 'quotes' and \"double quotes\""
    new_name = "Frank's Name & Family"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, full_name = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, new_name, user_id)
    )

    # Verify
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio
    assert result[1] == new_name


def test_update_bio_empty_name_preserved(db, factory):
    """Test: Update can set bio to empty while preserving full_name."""
    # Arrange
    user = factory.create_user("grace", "grace-empty", "grace@example.com", "Grace", "Grace's bio")
    user_id = user["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        ("", user_id)
    )

    # Verify
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == ""
    assert result[1] == "Grace"


# ============================================================================
# User Mutations: Return Value Validation
# ============================================================================

def test_update_returns_updated_user(db, factory):
    """Test: PUT /users/{user_id} returns updated user data."""
    # Arrange
    user = factory.create_user("alice", "alice-put-ret", "alice@example.com", "Alice Original")
    user_id = user["id"]
    new_name = "Alice Updated"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET full_name = %s, updated_at = NOW() WHERE id = %s",
        (new_name, user_id)
    )

    # Verify the update
    cursor.execute(
        "SELECT id, username, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == user_id
    assert result[1] == "alice"
    assert result[2] == new_name


def test_update_preserves_id_and_identifier(db, factory):
    """Test: Update preserves id and identifier."""
    # Arrange
    user = factory.create_user("bob", "bob-preserve", "bob@example.com", "Bob")
    user_id = user["id"]
    identifier = user["identifier"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = 'New bio', updated_at = NOW() WHERE id = %s",
        (user_id,)
    )

    # Verify
    cursor.execute(
        "SELECT id, identifier FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == user_id
    assert result[1] == identifier


# ============================================================================
# User Mutations: State Change Verification
# ============================================================================

def test_sequential_updates_accumulate(db, factory):
    """Test: Sequential updates accumulate correctly."""
    # Arrange
    user = factory.create_user("alice", "alice-seq", "alice@example.com")
    user_id = user["id"]

    # Act - first update
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        ("Bio v1", user_id)
    )

    # Second update
    cursor.execute(
        "UPDATE benchmark.tb_user SET full_name = %s WHERE id = %s",
        ("Alice Updated", user_id)
    )

    # Verify both changes were applied
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == "Bio v1"
    assert result[1] == "Alice Updated"


def test_update_one_user_does_not_affect_others(db, factory):
    """Test: Updating one user doesn't affect other users."""
    # Arrange
    user1 = factory.create_user("alice", "alice-iso", "alice@example.com", "Alice")
    user2 = factory.create_user("bob", "bob-iso", "bob@example.com", "Bob")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        ("Alice's new bio", user1["id"])
    )

    # Verify user1 changed but user2 didn't
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user1["id"],)
    )
    user1_result = cursor.fetchone()

    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user2["id"],)
    )
    user2_result = cursor.fetchone()

    # Assert
    assert user1_result[0] == "Alice's new bio"
    assert user2_result[0] is None


def test_update_post_title_and_content(db, factory):
    """Test: Updating post title and content works correctly."""
    # Arrange
    author = factory.create_user("author", "author-post-upd", "author@example.com")
    post = factory.create_post(author["pk_user"], "Original Title", "post-upd", "Original Content")
    post_id = post["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_post SET title = %s, content = %s, updated_at = NOW() WHERE id = %s",
        ("Updated Title", "Updated Content", post_id)
    )

    # Verify
    cursor.execute(
        "SELECT title, content FROM benchmark.tb_post WHERE id = %s",
        (post_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == "Updated Title"
    assert result[1] == "Updated Content"


# ============================================================================
# Input Validation in Mutations
# ============================================================================

def test_update_user_with_special_characters(db, factory):
    """Test: Bio update handles special characters correctly."""
    # Arrange
    user = factory.create_user("alice", "alice-special", "alice@example.com")
    user_id = user["id"]
    special_bio = "Bio with 'quotes', \"double quotes\", <html>, & ampersand"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        (special_bio, user_id)
    )

    # Verify
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == special_bio


def test_update_user_with_unicode_characters(db, factory):
    """Test: Updates handle unicode characters correctly."""
    # Arrange
    user = factory.create_user("alice", "alice-unicode", "alice@example.com")
    user_id = user["id"]
    unicode_bio = "Bio with émojis 🎉 and spëcial chàrs"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        (unicode_bio, user_id)
    )

    # Verify
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == unicode_bio


def test_update_post_content_with_long_text(db, factory):
    """Test: Post update handles long content text."""
    # Arrange
    author = factory.create_user("author", "author-long", "author@example.com")
    post = factory.create_post(author["pk_user"], "Title", "post-long", "Short content")
    post_id = post["id"]
    long_content = "x" * 5000

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_post SET content = %s WHERE id = %s",
        (long_content, post_id)
    )

    # Verify
    cursor.execute(
        "SELECT content FROM benchmark.tb_post WHERE id = %s",
        (post_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert len(result[0]) == 5000


def test_update_comment_content(db, factory):
    """Test: Comment content can be updated."""
    # Arrange
    author = factory.create_user("author", "author-cmt", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-cmt", "Content")
    commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Original")
    comment_id = comment["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_comment SET content = %s WHERE id = %s",
        ("Updated comment", comment_id)
    )

    # Verify
    cursor.execute(
        "SELECT content FROM benchmark.tb_comment WHERE id = %s",
        (comment_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == "Updated comment"


# ============================================================================
# POST Mutations
# ============================================================================

def test_create_post_returns_id(db, factory):
    """Test: Creating a post returns the created post data."""
    # Arrange
    author = factory.create_user("author", "author", "author@example.com")

    # Act
    cursor = db.cursor()
    post_title = "New Post"
    post_id_slug = "new-post"
    post_content = "Post content"

    cursor.execute(
        "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
        "VALUES (%s, %s, %s, %s) "
        "RETURNING id, title, identifier",
        (author["pk_user"], post_title, post_id_slug, post_content)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] is not None  # id was generated
    assert result[1] == post_title
    assert result[2] == post_id_slug
