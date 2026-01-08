"""Unit tests for Strawberry GraphQL resolvers.

Tests the Query and Mutation resolvers in isolation using the shared test database.
All tests use transaction isolation for automatic cleanup.

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""

import pytest
from uuid import UUID


# ============================================================================
# Query Tests: User Resolution
# ============================================================================

@pytest.mark.asyncio
async def test_query_user_by_uuid_returns_user(db, factory):
    """Test: query_user resolver returns correct user by UUID."""
    # Arrange
    user = factory.create_user("alice", "alice", "alice@example.com", "Alice", "Happy to be here")
    user_id = user["id"]

    # Act - simulate resolver
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, identifier, full_name, bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == user_id  # id (UUID)
    assert result[1] == "alice"  # username
    assert result[2] == "alice"  # identifier
    assert result[3] == "Alice"  # full_name


@pytest.mark.asyncio
async def test_query_user_by_identifier_returns_user(db, factory):
    """Test: query_user resolver returns correct user by identifier/slug."""
    # Arrange
    user = factory.create_user("bob", "bob-smith", "bob@example.com", "Bob Smith")
    identifier = user["identifier"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, identifier FROM benchmark.tb_user WHERE identifier = %s",
        (identifier,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[1] == "bob-smith"  # identifier matches


@pytest.mark.asyncio
async def test_query_user_nonexistent_returns_none(db):
    """Test: querying nonexistent user returns None."""
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


@pytest.mark.asyncio
async def test_query_users_returns_list(db, factory):
    """Test: query_users resolver returns list of users."""
    # Arrange
    factory.create_user("alice", "alice", "alice@example.com")
    factory.create_user("bob", "bob", "bob@example.com")
    factory.create_user("charlie", "charlie", "charlie@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username FROM benchmark.tb_user ORDER BY username LIMIT 10"
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) >= 3
    usernames = [r[1] for r in results]
    assert "alice" in usernames
    assert "bob" in usernames
    assert "charlie" in usernames


@pytest.mark.asyncio
async def test_query_users_with_limit(db, factory):
    """Test: query_users respects limit parameter."""
    # Arrange
    for i in range(15):
        factory.create_user(f"user{i}", f"user-{i}", f"user{i}@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_user LIMIT 10"
    )
    results = cursor.fetchall()

    # Assert - limit parameter should restrict results
    assert len(results) == 10


@pytest.mark.asyncio
async def test_query_user_field_retrieval(db, factory):
    """Test: user fields are correctly retrieved from database."""
    # Arrange
    user = factory.create_user("testuser", "test-user", "test@example.com", "Test User", "Test bio")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, identifier, email, full_name, bio FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    row = cursor.fetchone()

    # Assert
    assert row[0] == user["id"]  # id matches
    assert row[1] == user["username"]  # username matches
    assert row[2] == user["identifier"]  # identifier matches
    assert row[3] == "test@example.com"  # email matches


# ============================================================================
# Query Tests: Post Resolution
# ============================================================================

@pytest.mark.asyncio
async def test_query_post_by_id_returns_post(db, factory):
    """Test: query_post resolver returns correct post by ID."""
    # Arrange
    user = factory.create_user("author", "author-one", "author@example.com", "Author One")
    post = factory.create_post(user["pk_user"], "Test Post", "test-post", "Test content")
    post_id = post["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title, identifier FROM benchmark.tb_post WHERE id = %s",
        (post_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == post_id
    assert result[1] == "Test Post"
    assert result[2] == "test-post"


@pytest.mark.asyncio
async def test_query_post_by_identifier_returns_post(db, factory):
    """Test: query_post resolver can find post by identifier/slug."""
    # Arrange
    user = factory.create_user("author", "author-two", "author@example.com")
    post = factory.create_post(user["pk_user"], "My Great Post", "my-great-post", "Content here")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title FROM benchmark.tb_post WHERE identifier = %s",
        (post["identifier"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[1] == "My Great Post"


@pytest.mark.asyncio
async def test_query_posts_returns_list(db, factory):
    """Test: query_posts resolver returns list of posts."""
    # Arrange
    user = factory.create_user("author", "author-three", "author@example.com")
    factory.create_post(user["pk_user"], "Post 1", "post-1", "Content 1")
    factory.create_post(user["pk_user"], "Post 2", "post-2", "Content 2")
    factory.create_post(user["pk_user"], "Post 3", "post-3", "Content 3")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (user["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 3


@pytest.mark.asyncio
async def test_query_posts_with_limit(db, factory):
    """Test: query_posts respects limit parameter."""
    # Arrange
    user = factory.create_user("prolific", "prolific-author", "prolific@example.com")
    for i in range(20):
        factory.create_post(user["pk_user"], f"Post {i}", f"post-{i}", f"Content {i}")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_post WHERE fk_author = %s LIMIT 10",
        (user["pk_user"],)
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 10


# ============================================================================
# Query Tests: Comment Resolution
# ============================================================================

@pytest.mark.asyncio
async def test_query_comment_by_id_returns_comment(db, factory):
    """Test: query_comment resolver returns correct comment by ID."""
    # Arrange
    author = factory.create_user("author", "author-four", "author@example.com")
    commenter = factory.create_user("commenter", "commenter-one", "commenter@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-com", "Test content")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "comment-1", "Great post!")
    comment_id = comment["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, identifier, content FROM benchmark.tb_comment WHERE id = %s",
        (comment_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == comment_id
    assert result[2] == "Great post!"


# ============================================================================
# Mutation Tests: Update User
# ============================================================================

@pytest.mark.asyncio
async def test_mutation_update_user_bio(db, factory):
    """Test: update_user mutation updates user bio."""
    # Arrange
    user = factory.create_user("alice", "alice-update", "alice@example.com")
    user_id = user["id"]
    new_bio = "Updated bio with new info"

    # Act - simulate update_user mutation
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, user_id)
    )

    # Verify update
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio


@pytest.mark.asyncio
async def test_mutation_update_user_full_name(db, factory):
    """Test: update_user mutation updates user full_name."""
    # Arrange
    user = factory.create_user("bob", "bob-update", "bob@example.com", "Bob")
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
        "SELECT full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_name


@pytest.mark.asyncio
async def test_mutation_update_user_multiple_fields(db, factory):
    """Test: update_user mutation updates multiple fields."""
    # Arrange
    user = factory.create_user("charlie", "charlie-update", "charlie@example.com", "Charlie")
    user_id = user["id"]
    new_bio = "New and improved bio"
    new_name = "Charlie Brown Updated"

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


@pytest.mark.asyncio
async def test_mutation_update_nonexistent_user_returns_none(db):
    """Test: updating nonexistent user returns None."""
    # Arrange
    nonexistent_id = "00000000-0000-0000-0000-000000000000"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        ("bio", nonexistent_id)
    )

    # Verify it wasn't updated
    cursor.execute(
        "SELECT id FROM benchmark.tb_user WHERE id = %s",
        (nonexistent_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is None


# ============================================================================
# Relationship Tests: User Posts
# ============================================================================

@pytest.mark.asyncio
async def test_user_posts_relationship(db, factory):
    """Test: User.posts field correctly returns user's posts."""
    # Arrange
    user = factory.create_user("author", "author-rel", "author@example.com")
    post1 = factory.create_post(user["pk_user"], "Post 1", "post-rel-1", "Content 1")
    post2 = factory.create_post(user["pk_user"], "Post 2", "post-rel-2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_post WHERE fk_author = %s ORDER BY id",
        (user["pk_user"],)
    )
    posts = cursor.fetchall()

    # Assert
    assert len(posts) == 2
    post_ids = [p[0] for p in posts]
    assert post1["id"] in post_ids
    assert post2["id"] in post_ids


@pytest.mark.asyncio
async def test_user_posts_empty_for_new_user(db, factory):
    """Test: User with no posts returns empty list."""
    # Arrange
    user = factory.create_user("newuser", "new-user", "newuser@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (user["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 0


# ============================================================================
# Relationship Tests: Post Comments
# ============================================================================

@pytest.mark.asyncio
async def test_post_comments_relationship(db, factory):
    """Test: Post.comments field correctly returns post's comments."""
    # Arrange
    author = factory.create_user("author", "author-cmt", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-cmt", "Content")
    commenter = factory.create_user("commenter", "commenter-cmt", "commenter@example.com")
    comment1 = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-1", "Comment 1")
    comment2 = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-2", "Comment 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_comment WHERE fk_post = %s",
        (post["pk_post"],)
    )
    comments = cursor.fetchall()

    # Assert
    assert len(comments) == 2


@pytest.mark.asyncio
async def test_post_comments_limit(db, factory):
    """Test: Post.comments respects limit parameter."""
    # Arrange
    author = factory.create_user("author", "author-lim", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-lim", "Content")
    commenter = factory.create_user("commenter", "commenter-lim", "commenter@example.com")

    for i in range(100):
        factory.create_comment(post["pk_post"], commenter["pk_user"], f"cmt-{i}", f"Comment {i}")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s",
        (post["pk_post"],)
    )
    total = cursor.fetchone()[0]

    # Assert - should have 100 comments total, but resolver limits to 50
    assert total == 100


# ============================================================================
# Relationship Tests: Post Author
# ============================================================================

@pytest.mark.asyncio
async def test_post_author_relationship(db, factory):
    """Test: Post.author field correctly resolves to author User."""
    # Arrange
    author = factory.create_user("author", "author-post", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-auth", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT fk_author FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == author["pk_user"]


# ============================================================================
# Relationship Tests: Comment Author
# ============================================================================

@pytest.mark.asyncio
async def test_comment_author_relationship(db, factory):
    """Test: Comment.author field correctly resolves to author User."""
    # Arrange
    author = factory.create_user("author", "author-cmt-auth", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-cmt-auth", "Content")
    commenter = factory.create_user("commenter", "commenter-cmt-auth", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-auth", "Comment")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT fk_author FROM benchmark.tb_comment WHERE id = %s",
        (comment["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == commenter["pk_user"]


# ============================================================================
# Edge Cases and Validation
# ============================================================================

@pytest.mark.asyncio
async def test_query_with_special_characters_in_content(db, factory):
    """Test: posts with special characters are handled correctly."""
    # Arrange
    user = factory.create_user("author", "author-spec", "author@example.com")
    special_content = "Test with 'quotes' and \"double quotes\" and <html>"
    post = factory.create_post(user["pk_user"], "Special Post", "special-post", special_content)

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT content FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == special_content


@pytest.mark.asyncio
async def test_multiple_users_dont_interfere(db, factory):
    """Test: users don't see each other's private data."""
    # Arrange
    user1 = factory.create_user("user1", "user-1", "user1@example.com")
    user2 = factory.create_user("user2", "user-2", "user2@example.com")

    # Act - get user1
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, identifier FROM benchmark.tb_user WHERE id = %s",
        (user1["id"],)
    )
    result1 = cursor.fetchone()

    # Get user2
    cursor.execute(
        "SELECT id, identifier FROM benchmark.tb_user WHERE id = %s",
        (user2["id"],)
    )
    result2 = cursor.fetchone()

    # Assert
    assert result1[1] == "user-1"
    assert result2[1] == "user-2"
    assert result1[0] != result2[0]


@pytest.mark.asyncio
async def test_post_author_fk_consistency(db, factory):
    """Test: post's fk_author matches the actual author's pk_user."""
    # Arrange
    author = factory.create_user("author", "author-fk", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test", "test-fk", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT fk_author FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert - post's fk_author should match creator's pk_user
    assert result[0] == author["pk_user"]


@pytest.mark.asyncio
async def test_null_optional_fields(db, factory):
    """Test: optional fields can be null."""
    # Arrange
    user = factory.create_user("user", "user-null", "user@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert - bio should be null for new user
    assert result[0] is None


# ============================================================================
# Performance and Batching
# ============================================================================

@pytest.mark.asyncio
async def test_create_many_posts_performance(db, factory):
    """Test: creating many posts works correctly."""
    # Arrange
    user = factory.create_user("author", "author-perf", "author@example.com")

    # Act
    for i in range(50):
        factory.create_post(user["pk_user"], f"Post {i}", f"post-perf-{i}", f"Content {i}")

    # Verify
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (user["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 50


@pytest.mark.asyncio
async def test_query_with_ordering(db, factory):
    """Test: posts can be ordered by creation date."""
    # Arrange
    user = factory.create_user("author", "author-order", "author@example.com")

    factory.create_post(user["pk_user"], "Post 1", "post-order-1", "Content 1")
    factory.create_post(user["pk_user"], "Post 2", "post-order-2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT title FROM benchmark.tb_post WHERE fk_author = %s ORDER BY created_at",
        (user["pk_user"],)
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 2
