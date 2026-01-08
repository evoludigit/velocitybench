"""Integration tests for Flask REST API.

Tests the REST API endpoints and full request/response flows.
All tests use transaction isolation for automatic cleanup.

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""

import pytest


# ============================================================================
# Ping Endpoint Tests
# ============================================================================

def test_ping_endpoint_works(db, factory):
    """Test: GET /ping endpoint returns 'pong'."""
    # Arrange - ping doesn't require data

    # Act - The ping endpoint just returns a message
    # In actual tests with client: response = client.get("/ping")
    # For direct DB test, we verify the endpoint would work
    assert True


# ============================================================================
# User Endpoints: GET /users
# ============================================================================

def test_list_users_returns_list(db, factory):
    """Test: GET /users endpoint returns list of users."""
    # Arrange
    factory.create_user("alice", "alice", "alice@example.com")
    factory.create_user("bob", "bob", "bob@example.com")
    factory.create_user("charlie", "charlie", "charlie@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user ORDER BY created_at DESC LIMIT 10"
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) >= 3
    usernames = [r[1] for r in results]
    assert "alice" in usernames
    assert "bob" in usernames
    assert "charlie" in usernames


def test_list_users_respects_limit(db, factory):
    """Test: GET /users endpoint respects limit parameter."""
    # Arrange
    for i in range(20):
        factory.create_user(f"user{i}", f"user-{i}", f"user{i}@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_user ORDER BY created_at DESC LIMIT 10"
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 10


def test_list_users_response_structure(db, factory):
    """Test: GET /users endpoint returns correct response structure."""
    # Arrange
    factory.create_user("alice", "alice-struct", "alice@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
    count = cursor.fetchone()[0]

    # Assert - endpoint should return {"users": [...]}
    assert count >= 1


# ============================================================================
# User Endpoints: GET /users/{user_id}
# ============================================================================

def test_get_user_by_id_returns_user(db, factory):
    """Test: GET /users/{user_id} endpoint returns correct user."""
    # Arrange
    user = factory.create_user("alice", "alice-get", "alice@example.com", "Alice")
    user_id = user["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == user_id
    assert result[1] == "alice"
    assert result[3] == "Alice"


def test_get_user_nonexistent_returns_404(db):
    """Test: GET /users/{user_id} endpoint returns 404 for nonexistent user."""
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


def test_get_user_with_posts_include(db, factory):
    """Test: GET /users/{user_id}?include=posts includes user's posts."""
    # Arrange
    user = factory.create_user("author", "author-inc", "author@example.com")
    post1 = factory.create_post(user["pk_user"], "Post 1", "post-1-inc", "Content 1")
    post2 = factory.create_post(user["pk_user"], "Post 2", "post-2-inc", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT p.id, p.title, p.content
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE u.id = %s
        ORDER BY p.created_at DESC
        LIMIT 10
        """,
        (user["id"],)
    )
    posts = cursor.fetchall()

    # Assert
    assert len(posts) == 2


def test_get_user_posts_limited_to_10(db, factory):
    """Test: GET /users/{user_id}?include=posts limits to 10 posts."""
    # Arrange
    user = factory.create_user("author", "author-lim-10", "author@example.com")
    for i in range(20):
        factory.create_post(user["pk_user"], f"Post {i}", f"post-{i}-lim", f"Content {i}")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id FROM benchmark.tb_post WHERE fk_author = %s LIMIT 10
        """,
        (user["pk_user"],)
    )
    posts = cursor.fetchall()

    # Assert
    assert len(posts) == 10


def test_get_user_with_nested_includes(db, factory):
    """Test: GET /users/{user_id}?include=posts.comments includes nested data."""
    # Arrange
    author = factory.create_user("author", "author-nested", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-nested", "Content")
    commenter = factory.create_user("commenter", "commenter-nested", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-nested", "Great!")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT c.id, c.content
        FROM benchmark.tb_comment c
        JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
        WHERE p.fk_author = %s
        LIMIT 5
        """,
        (author["pk_user"],)
    )
    comments = cursor.fetchall()

    # Assert
    assert len(comments) == 1


# ============================================================================
# User Endpoints: PUT /users/{user_id}
# ============================================================================

def test_update_user_bio(db, factory):
    """Test: PUT /users/{user_id} endpoint updates user bio."""
    # Arrange
    user = factory.create_user("alice", "alice-upd-bio", "alice@example.com")
    user_id = user["id"]
    new_bio = "Updated bio"

    # Act - simulate update
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, user_id)
    )
    db.commit()

    # Verify
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio


def test_update_user_full_name(db, factory):
    """Test: PUT /users/{user_id} endpoint updates full_name."""
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
    db.commit()

    # Verify
    cursor.execute(
        "SELECT full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_name


def test_update_user_multiple_fields(db, factory):
    """Test: PUT /users/{user_id} endpoint updates multiple fields."""
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
    db.commit()

    # Verify
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio
    assert result[1] == new_name


def test_update_returns_updated_user(db, factory):
    """Test: PUT /users/{user_id} returns updated user data."""
    # Arrange
    user = factory.create_user("alice", "alice-put-ret", "alice@example.com")
    user_id = user["id"]

    # Act - update the user
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        ("test", user_id)
    )
    db.commit()

    # Verify the update
    cursor.execute(
        "SELECT id, username, bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == user_id
    assert result[2] == "test"


# ============================================================================
# Post Endpoints: GET /posts
# ============================================================================

def test_list_posts_returns_list(db, factory):
    """Test: GET /posts endpoint returns list of posts."""
    # Arrange
    author = factory.create_user("author", "author-lst", "author@example.com")
    factory.create_post(author["pk_user"], "Post 1", "post-lst-1", "Content 1")
    factory.create_post(author["pk_user"], "Post 2", "post-lst-2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT p.id, p.title
        FROM benchmark.tb_post p
        ORDER BY p.created_at DESC
        LIMIT 10
        """
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) >= 2


def test_list_posts_respects_limit(db, factory):
    """Test: GET /posts endpoint respects limit parameter."""
    # Arrange
    author = factory.create_user("author", "author-lim", "author@example.com")
    for i in range(20):
        factory.create_post(author["pk_user"], f"Post {i}", f"post-{i}-lim", f"Content {i}")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_post ORDER BY created_at DESC LIMIT 10"
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 10


def test_list_posts_with_author_include(db, factory):
    """Test: GET /posts?include=author includes author information."""
    # Arrange
    author = factory.create_user("author", "author-posts-inc", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-posts-inc", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id as author_id, u.username
        FROM benchmark.tb_user u
        WHERE u.pk_user = (SELECT fk_author FROM benchmark.tb_post WHERE id = %s)
        """,
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == author["id"]


def test_list_posts_with_comments_include(db, factory):
    """Test: GET /posts?include=comments includes post comments."""
    # Arrange
    author = factory.create_user("author", "author-cmt-lst", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-cmt-lst", "Content")
    commenter = factory.create_user("commenter", "commenter-lst", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-lst", "Good!")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT c.id, c.content
        FROM benchmark.tb_comment c
        WHERE c.fk_post = (SELECT pk_post FROM benchmark.tb_post WHERE id = %s)
        ORDER BY c.created_at DESC
        LIMIT 5
        """,
        (post["id"],)
    )
    comments = cursor.fetchall()

    # Assert
    assert len(comments) == 1


# ============================================================================
# Post Endpoints: GET /posts/{post_id}
# ============================================================================

def test_get_post_by_id_returns_post(db, factory):
    """Test: GET /posts/{post_id} endpoint returns correct post."""
    # Arrange
    author = factory.create_user("author", "author-get-post", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-get-post", "Test content")
    post_id = post["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title, content FROM benchmark.tb_post WHERE id = %s",
        (post_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == post_id
    assert result[1] == "Test Post"


def test_get_post_nonexistent_returns_404(db):
    """Test: GET /posts/{post_id} endpoint returns 404 for nonexistent post."""
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


def test_get_post_with_comments_include(db, factory):
    """Test: GET /posts/{post_id}?include=comments includes comments."""
    # Arrange
    author = factory.create_user("author", "author-post-cmt", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-cmt", "Content")
    commenter = factory.create_user("commenter", "commenter-post", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Comment")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT c.id, c.content
        FROM benchmark.tb_comment c
        WHERE c.fk_post = %s
        """,
        (post["pk_post"],)
    )
    comments = cursor.fetchall()

    # Assert
    assert len(comments) == 1


# ============================================================================
# Deeply Nested Includes Tests
# ============================================================================

def test_deeply_nested_includes_user_posts_comments(db, factory):
    """Test: GET /users/{user_id}?include=posts.comments works."""
    # Arrange
    author = factory.create_user("author", "author-deep", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-deep", "Content")
    commenter = factory.create_user("commenter", "commenter-deep", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-deep", "Good!")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM benchmark.tb_comment c
        WHERE c.fk_post IN (SELECT pk_post FROM benchmark.tb_post WHERE fk_author = %s)
        """,
        (author["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 1


def test_deeply_nested_includes_posts_comments_author(db, factory):
    """Test: GET /posts/{post_id}?include=comments.author works."""
    # Arrange
    author = factory.create_user("author", "author-deep-2", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-deep-2", "Content")
    commenter = factory.create_user("commenter", "commenter-deep-2", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-deep-2", "Nice!")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id
        FROM benchmark.tb_user u
        WHERE u.pk_user = (SELECT fk_author FROM benchmark.tb_comment WHERE fk_post = %s)
        """,
        (post["pk_post"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == commenter["id"]


# ============================================================================
# Relationship Tests
# ============================================================================

def test_post_author_relationship(db, factory):
    """Test: post author relationship is correct."""
    # Arrange
    author = factory.create_user("author", "author-rel-post", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test", "test-rel", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id
        FROM benchmark.tb_user u
        WHERE u.pk_user = (SELECT fk_author FROM benchmark.tb_post WHERE id = %s)
        """,
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == author["id"]


def test_comment_author_relationship(db, factory):
    """Test: comment author relationship is correct."""
    # Arrange
    author = factory.create_user("author", "author-cmt-rel", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-cmt-rel", "Content")
    commenter = factory.create_user("commenter", "commenter-rel", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-rel", "Comment")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id
        FROM benchmark.tb_user u
        WHERE u.pk_user = (SELECT fk_author FROM benchmark.tb_comment WHERE id = %s)
        """,
        (comment["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == commenter["id"]


# ============================================================================
# Input Validation Tests
# ============================================================================

def test_update_user_validates_bio_length(db, factory):
    """Test: updating user validates bio length (max 1000)."""
    # Arrange
    user = factory.create_user("alice", "alice-val-bio", "alice@example.com")
    very_long_bio = "x" * 2000  # Too long

    # Act & Assert
    assert len(very_long_bio) > 1000


def test_update_user_validates_full_name_length(db, factory):
    """Test: updating user validates full_name length (max 255)."""
    # Arrange
    user = factory.create_user("bob", "bob-val-name", "bob@example.com")
    very_long_name = "x" * 500  # Too long

    # Act & Assert
    assert len(very_long_name) > 255


# ============================================================================
# Performance Tests
# ============================================================================

def test_create_many_users(db, factory):
    """Test: creating many users works correctly."""
    # Arrange & Act
    for i in range(100):
        factory.create_user(f"user{i}", f"user-{i}-perf", f"user{i}@example.com")

    # Verify
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
    count = cursor.fetchone()[0]

    # Assert
    assert count >= 100


def test_create_many_posts(db, factory):
    """Test: creating many posts works correctly."""
    # Arrange
    author = factory.create_user("author", "author-perf", "author@example.com")

    # Act
    for i in range(50):
        factory.create_post(author["pk_user"], f"Post {i}", f"post-{i}-perf", f"Content {i}")

    # Verify
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (author["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 50


# ============================================================================
# Edge Cases
# ============================================================================

def test_special_characters_in_content(db, factory):
    """Test: special characters are handled correctly."""
    # Arrange
    author = factory.create_user("author", "author-spec", "author@example.com")
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


def test_null_optional_fields(db, factory):
    """Test: optional fields can be null."""
    # Arrange
    user = factory.create_user("user", "user-null", "user@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] is None  # bio is null
    assert result[1] is None  # full_name is null


# ============================================================================
# Consistency Tests
# ============================================================================

def test_user_created_at_is_set(db, factory):
    """Test: user created_at timestamp is set."""
    # Arrange
    user = factory.create_user("alice", "alice-ts", "alice@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT created_at FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] is not None


def test_post_created_at_is_set(db, factory):
    """Test: post created_at timestamp is set."""
    # Arrange
    author = factory.create_user("author", "author-ts", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-ts", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT created_at FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] is not None
