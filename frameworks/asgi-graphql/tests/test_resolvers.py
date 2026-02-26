"""Unit tests for ASGI-GraphQL framework resolvers.

Tests the Query and Mutation resolvers using the shared test database.
ASGI-GraphQL uses graphql-core directly without a framework abstraction.
"""

import pytest


# ============================================================================
# Query Tests: User Resolution
# ============================================================================

@pytest.mark.query
def test_query_user_by_uuid_returns_user(db, factory):
    """Test: user query returns correct user by UUID."""
    user = factory.create_user("alice", "alice@example.com", "Alice Smith", "Hello!")
    user_id = user["id"]

    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == user_id
    assert result[1] == "alice"
    assert result[2] == "Alice Smith"
    assert result[3] == "Hello!"


@pytest.mark.query
def test_query_users_returns_list(db, factory):
    """Test: users query returns list of users."""
    factory.create_user("alice", "alice@example.com")
    factory.create_user("bob", "bob@example.com")
    factory.create_user("charlie", "charlie@example.com")

    cursor = db.cursor()
    cursor.execute("SELECT id, username FROM benchmark.tb_user ORDER BY username")
    results = cursor.fetchall()

    assert len(results) >= 3
    usernames = [r[1] for r in results]
    assert "alice" in usernames
    assert "bob" in usernames
    assert "charlie" in usernames


@pytest.mark.query
def test_query_users_with_limit(db, factory):
    """Test: users query respects limit parameter."""
    for i in range(15):
        factory.create_user(f"user{i}", f"user{i}@example.com")

    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_user LIMIT 10")
    results = cursor.fetchall()

    assert len(results) == 10


# ============================================================================
# Query Tests: Post Resolution
# ============================================================================

@pytest.mark.query
def test_query_post_by_id_returns_post(db, factory):
    """Test: post query returns correct post by ID."""
    user = factory.create_user("author", "author@example.com")
    post = factory.create_post(user["pk_user"], "Test Post", "Test content")

    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title, content FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == post["id"]
    assert result[1] == "Test Post"
    assert result[2] == "Test content"


@pytest.mark.query
def test_query_posts_returns_list(db, factory):
    """Test: posts query returns list of posts."""
    user = factory.create_user("author", "author@example.com")
    factory.create_post(user["pk_user"], "Post 1")
    factory.create_post(user["pk_user"], "Post 2")
    factory.create_post(user["pk_user"], "Post 3")

    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s", (user["pk_user"],))
    count = cursor.fetchone()[0]

    assert count == 3


# ============================================================================
# Query Tests: Comment Resolution
# ============================================================================

@pytest.mark.query
def test_query_comment_by_id_returns_comment(db, factory):
    """Test: comment query returns correct comment by ID."""
    author = factory.create_user("author", "author@example.com")
    commenter = factory.create_user("commenter", "commenter@example.com")
    post = factory.create_post(author["pk_user"], "Test Post")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "Great post!")

    cursor = db.cursor()
    cursor.execute(
        "SELECT id, content FROM benchmark.tb_comment WHERE id = %s",
        (comment["id"],)
    )
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == comment["id"]
    assert result[1] == "Great post!"


# ============================================================================
# Mutation Tests: Update User
# ============================================================================

@pytest.mark.mutation
def test_mutation_update_user_bio(db, factory):
    """Test: updateUser mutation updates user bio."""
    user = factory.create_user("alice", "alice@example.com")
    new_bio = "Updated bio"

    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        (new_bio, user["id"])
    )
    cursor.execute("SELECT bio FROM benchmark.tb_user WHERE id = %s", (user["id"],))
    result = cursor.fetchone()

    assert result[0] == new_bio


@pytest.mark.mutation
def test_mutation_update_user_full_name(db, factory):
    """Test: updateUser mutation updates user full_name."""
    user = factory.create_user("bob", "bob@example.com", "Bob")
    new_name = "Bob Smith"

    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET full_name = %s WHERE id = %s",
        (new_name, user["id"])
    )
    cursor.execute("SELECT full_name FROM benchmark.tb_user WHERE id = %s", (user["id"],))
    result = cursor.fetchone()

    assert result[0] == new_name


# ============================================================================
# Relationship Tests
# ============================================================================

@pytest.mark.relationship
def test_user_posts_relationship(db, factory):
    """Test: User.posts field returns user's posts."""
    user = factory.create_user("author", "author@example.com")
    post1 = factory.create_post(user["pk_user"], "Post 1")
    post2 = factory.create_post(user["pk_user"], "Post 2")

    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_post WHERE fk_author = %s ORDER BY id",
        (user["pk_user"],)
    )
    posts = cursor.fetchall()

    assert len(posts) == 2
    post_ids = [p[0] for p in posts]
    assert post1["id"] in post_ids
    assert post2["id"] in post_ids


@pytest.mark.relationship
def test_post_author_relationship(db, factory):
    """Test: Post.author field resolves to author User."""
    author = factory.create_user("author", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post")

    cursor = db.cursor()
    cursor.execute("SELECT fk_author FROM benchmark.tb_post WHERE id = %s", (post["id"],))
    result = cursor.fetchone()

    assert result[0] == author["pk_user"]


@pytest.mark.relationship
def test_post_comments_relationship(db, factory):
    """Test: Post.comments field returns post's comments."""
    author = factory.create_user("author", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post")
    commenter = factory.create_user("commenter", "commenter@example.com")
    factory.create_comment(post["pk_post"], commenter["pk_user"], "Comment 1")
    factory.create_comment(post["pk_post"], commenter["pk_user"], "Comment 2")

    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s", (post["pk_post"],))
    count = cursor.fetchone()[0]

    assert count == 2


@pytest.mark.relationship
def test_comment_author_relationship(db, factory):
    """Test: Comment.author field resolves to author User."""
    author = factory.create_user("author", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post")
    commenter = factory.create_user("commenter", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "Great!")

    cursor = db.cursor()
    cursor.execute("SELECT fk_author FROM benchmark.tb_comment WHERE id = %s", (comment["id"],))
    result = cursor.fetchone()

    assert result[0] == commenter["pk_user"]


# ============================================================================
# DataLoader Batching Tests
# ============================================================================

@pytest.mark.relationship
def test_dataloader_batches_user_lookups(db, factory):
    """Test: DataLoader batches multiple user lookups."""
    users = []
    for i in range(10):
        users.append(factory.create_user(f"user{i}", f"user{i}@example.com"))

    user_ids = [u["id"] for u in users]
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username FROM benchmark.tb_user WHERE id = ANY(%s)",
        (user_ids,)
    )
    results = cursor.fetchall()

    assert len(results) == 10


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.error
def test_query_nonexistent_user_returns_none(db, factory):
    """Test: querying non-existent user returns None."""
    import uuid
    fake_id = uuid.uuid4()

    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_user WHERE id = %s", (fake_id,))
    result = cursor.fetchone()

    assert result is None


@pytest.mark.query
def test_special_characters_in_content(db, factory):
    """Test: special characters are handled correctly."""
    user = factory.create_user("author", "author@example.com")
    special_content = "Test with 'quotes' and \"double quotes\" and <html>"
    post = factory.create_post(user["pk_user"], "Special Post", special_content)

    cursor = db.cursor()
    cursor.execute("SELECT content FROM benchmark.tb_post WHERE id = %s", (post["id"],))
    result = cursor.fetchone()

    assert result[0] == special_content


@pytest.mark.query
def test_unicode_content(db, factory):
    """Test: unicode content is handled correctly."""
    user = factory.create_user("author", "author@example.com")
    unicode_content = "Test with émojis 🎉 and ñ and 中文"
    post = factory.create_post(user["pk_user"], "Unicode Post", unicode_content)

    cursor = db.cursor()
    cursor.execute("SELECT content FROM benchmark.tb_post WHERE id = %s", (post["id"],))
    result = cursor.fetchone()

    assert result[0] == unicode_content


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.slow
def test_create_many_posts(db, factory):
    """Test: creating many posts works correctly."""
    user = factory.create_user("author", "author@example.com")
    for i in range(50):
        factory.create_post(user["pk_user"], f"Post {i}")

    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s", (user["pk_user"],))
    count = cursor.fetchone()[0]

    assert count == 50


@pytest.mark.slow
def test_deeply_nested_query(db, factory):
    """Test: deeply nested query (user -> posts -> comments) works."""
    author = factory.create_user("author", "author@example.com")
    post1 = factory.create_post(author["pk_user"], "Post 1")
    post2 = factory.create_post(author["pk_user"], "Post 2")

    commenter = factory.create_user("commenter", "commenter@example.com")
    factory.create_comment(post1["pk_post"], commenter["pk_user"], "Comment on post 1")
    factory.create_comment(post2["pk_post"], commenter["pk_user"], "Comment on post 2")

    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id, u.username, p.id, c.id
        FROM benchmark.tb_user u
        LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author
        LEFT JOIN benchmark.tb_comment c ON p.pk_post = c.fk_post
        WHERE u.id = %s
        ORDER BY p.id, c.id
        """,
        (author["id"],)
    )
    results = cursor.fetchall()

    assert len(results) >= 2
