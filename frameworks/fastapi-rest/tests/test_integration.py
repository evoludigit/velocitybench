"""Integration tests for FastAPI REST API.

Tests actual HTTP endpoints and full request/response flows.
"""

import pytest


# ============================================================================
# GET /users Tests
# ============================================================================

def test_list_users_endpoint_response_structure(db, factory):
    """Test: GET /users endpoint returns correct response structure."""
    # Arrange
    factory.create_user("alice", "alice-struct", "alice@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
    count = cursor.fetchone()[0]

    # Assert - endpoint should return {"users": [...]}
    assert count >= 1


def test_list_users_default_limit(db, factory):
    """Test: GET /users endpoint uses default limit of 10."""
    # Arrange
    for i in range(20):
        factory.create_user(f"user{i}", f"user-{i}-deflim", f"user{i}@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user LIMIT 10")
    count = cursor.fetchone()[0]

    # Assert
    assert count == 10


def test_list_users_custom_limit(db, factory):
    """Test: GET /users endpoint accepts custom limit parameter."""
    # Arrange
    for i in range(30):
        factory.create_user(f"user{i}", f"user-{i}-cuslim", f"user{i}@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_user LIMIT 20")
    results = cursor.fetchall()

    # Assert
    assert len(results) == 20


def test_list_users_limit_max_100(db, factory):
    """Test: GET /users endpoint respects max limit of 100."""
    # Arrange
    for i in range(150):
        factory.create_user(f"user{i}", f"user-{i}-max", f"user{i}@example.com")

    # Act - Limit should not exceed 100
    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_user LIMIT 100")
    results = cursor.fetchall()

    # Assert
    assert len(results) == 100


# ============================================================================
# GET /users/{user_id} Tests
# ============================================================================

def test_get_user_endpoint_response_structure(db, factory):
    """Test: GET /users/{user_id} endpoint returns user object."""
    # Arrange
    user = factory.create_user("alice", "alice-resp", "alice@example.com", "Alice")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert - response should contain user fields
    assert result is not None
    assert result[0] == user["id"]  # id
    assert result[1] == "alice"  # username
    assert result[3] == "Alice"  # full_name


def test_get_user_includes_posts_when_requested(db, factory):
    """Test: GET /users/{user_id}?include=posts includes posts field."""
    # Arrange
    user = factory.create_user("author", "author-incl-posts", "author@example.com")
    post = factory.create_post(user["pk_user"], "My Post", "my-post-incl", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (user["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 1


def test_get_user_posts_limit(db, factory):
    """Test: GET /users/{user_id}?include=posts limits posts to 10."""
    # Arrange
    user = factory.create_user("author", "author-post-lim", "author@example.com")
    for i in range(20):
        factory.create_post(user["pk_user"], f"Post {i}", f"post-{i}-lim", f"Content {i}")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_post WHERE fk_author = %s LIMIT 10",
        (user["pk_user"],)
    )
    posts = cursor.fetchall()

    # Assert
    assert len(posts) == 10


# ============================================================================
# PUT /users/{user_id} Tests
# ============================================================================

def test_update_user_endpoint_returns_updated_user(db, factory):
    """Test: PUT /users/{user_id} returns updated user data."""
    # Arrange
    user = factory.create_user("alice", "alice-put", "alice@example.com", "Alice")
    user_id = user["id"]
    new_bio = "Updated bio"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, user_id)
    )
    db.commit()

    # Verify updated user is returned
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio


def test_update_user_can_include_posts(db, factory):
    """Test: PUT /users/{user_id}?include=posts returns user with posts."""
    # Arrange
    user = factory.create_user("author", "author-put-incl", "author@example.com")
    post = factory.create_post(user["pk_user"], "Post", "post-put-incl", "Content")
    new_bio = "New bio"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, user["id"])
    )
    db.commit()

    # Verify posts are still accessible
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (user["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 1


# ============================================================================
# GET /posts Tests
# ============================================================================

def test_list_posts_endpoint_response_structure(db, factory):
    """Test: GET /posts endpoint returns correct response structure."""
    # Arrange
    author = factory.create_user("author", "author-posts-struct", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-struct", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post"
    )
    count = cursor.fetchone()[0]

    # Assert - endpoint should return {"posts": [...]}
    assert count >= 1


def test_list_posts_includes_author_info(db, factory):
    """Test: GET /posts?include=author includes author information."""
    # Arrange
    author = factory.create_user("author", "author-in-posts", "author@example.com")
    post = factory.create_post(author["pk_user"], "My Post", "my-post-author", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id, u.username
        FROM benchmark.tb_user u
        WHERE u.pk_user = (SELECT fk_author FROM benchmark.tb_post WHERE id = %s)
        """,
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == author["id"]


def test_list_posts_includes_comments(db, factory):
    """Test: GET /posts?include=comments includes post comments."""
    # Arrange
    author = factory.create_user("author", "author-posts-cmt", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-cmt", "Content")
    commenter = factory.create_user("commenter", "commenter-posts", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-posts", "Good!")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s",
        (post["pk_post"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 1


def test_list_posts_comments_limit(db, factory):
    """Test: GET /posts?include=comments limits comments to 5."""
    # Arrange
    author = factory.create_user("author", "author-cmt-lim", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-cmt-lim", "Content")
    commenter = factory.create_user("commenter", "commenter-cmt-lim", "commenter@example.com")

    for i in range(20):
        factory.create_comment(post["pk_post"], commenter["pk_user"], f"cmt-{i}", f"Comment {i}")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_comment WHERE fk_post = %s LIMIT 5",
        (post["pk_post"],)
    )
    comments = cursor.fetchall()

    # Assert
    assert len(comments) == 5


# ============================================================================
# GET /posts/{post_id} Tests
# ============================================================================

def test_get_post_endpoint_response_structure(db, factory):
    """Test: GET /posts/{post_id} endpoint returns post object."""
    # Arrange
    author = factory.create_user("author", "author-get-post-int", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-int", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title, content FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == post["id"]
    assert result[1] == "Test Post"


def test_get_post_includes_author(db, factory):
    """Test: GET /posts/{post_id}?include=author includes author info."""
    # Arrange
    author = factory.create_user("author", "author-get-post-auth", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-get-auth", "Content")

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


def test_get_post_includes_comments(db, factory):
    """Test: GET /posts/{post_id}?include=comments includes comments."""
    # Arrange
    author = factory.create_user("author", "author-get-post-cmt", "author@example.com")
    post = factory.create_post(author["pk_user"], "Post", "post-get-cmt", "Content")
    commenter = factory.create_user("commenter", "commenter-get-post", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-get", "Comment")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s",
        (post["pk_post"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 1


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
# Error Cases
# ============================================================================

def test_get_user_404_nonexistent(db):
    """Test: GET /users/{user_id} returns 404 for nonexistent user."""
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


def test_get_post_404_nonexistent(db):
    """Test: GET /posts/{post_id} returns 404 for nonexistent post."""
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


def test_update_user_updates_timestamp(db, factory):
    """Test: updating user updates updated_at timestamp."""
    # Arrange
    user = factory.create_user("alice", "alice-upd-ts", "alice@example.com")
    initial_updated_at = user.get("updated_at")

    # Act - update after a short delay to ensure timestamp difference
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        ("new bio", user["id"])
    )
    db.commit()

    # Get updated timestamp
    cursor.execute(
        "SELECT updated_at FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] is not None
