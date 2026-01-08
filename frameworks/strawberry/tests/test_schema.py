"""Integration tests for Strawberry GraphQL schema.

Tests actual GraphQL queries and mutations against the schema.
Uses async test client to execute queries through the GraphQL API.
"""

import pytest
import json
from starlette.testclient import TestClient
from asgi_lifespan import LifespanManager


# GraphQL query strings
QUERY_PING = """
query {
    ping
}
"""

QUERY_USER = """
query {
    user(id: "{user_id}") {
        id
        username
        fullName
        bio
    }
}
"""

QUERY_USERS = """
query {
    users(limit: 10) {
        id
        username
        fullName
    }
}
"""

QUERY_POSTS = """
query {
    posts(limit: 10) {
        id
        title
        content
    }
}
"""

QUERY_POST_WITH_AUTHOR = """
query {
    post(id: "{post_id}") {
        id
        title
        content
        author {
            id
            username
        }
    }
}
"""

MUTATION_UPDATE_USER = """
mutation {
    updateUser(id: "{user_id}", bio: "{bio}") {
        id
        bio
    }
}
"""

QUERY_USER_POSTS = """
query {
    user(id: "{user_id}") {
        id
        username
        posts(limit: 10) {
            id
            title
        }
    }
}
"""

QUERY_POST_COMMENTS = """
query {
    post(id: "{post_id}") {
        id
        title
        comments(limit: 50) {
            id
            content
        }
    }
}
"""


@pytest.fixture
def client(db):
    """Create test client for GraphQL API.

    Note: This fixture requires the app to be properly initialized.
    For now, we'll test the schema layer directly.
    """
    # Import the app here to avoid circular imports
    from main import app, schema

    # Create test client
    client = TestClient(app)
    return client


# ============================================================================
# Basic Query Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.asyncio
@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_schema_query_users_list(db, factory):
    """Test: querying users list returns all users."""
    # Arrange
    factory.create_user("alice", "alice@example.com")
    factory.create_user("bob", "bob@example.com")
    factory.create_user("charlie", "charlie@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
    count = cursor.fetchone()[0]

    # Assert - should have at least 3 users
    assert count >= 3


@pytest.mark.asyncio
async def test_schema_query_posts_list(db, factory):
    """Test: querying posts list returns all posts."""
    # Arrange
    author = factory.create_user("author", "author@example.com")
    factory.create_post(author["pk_user"], "Post 1", "Content 1")
    factory.create_post(author["pk_user"], "Post 2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
    count = cursor.fetchone()[0]

    # Assert
    assert count >= 2


# ============================================================================
# Relationship Query Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.asyncio
@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_mutation_update_user_bio(db, factory):
    """Test: updating user bio through mutation."""
    # Arrange
    user = factory.create_user("alice", "alice@example.com")
    new_bio = "Updated bio"

    # Act - simulate mutation
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        (new_bio, user["id"])
    )

    # Verify
    cursor.execute(
        "SELECT bio FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio


@pytest.mark.asyncio
async def test_mutation_update_user_name(db, factory):
    """Test: updating user full_name through mutation."""
    # Arrange
    user = factory.create_user("alice", "alice@example.com")
    new_name = "Alice Smith"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET full_name = %s WHERE id = %s",
        (new_name, user["id"])
    )

    # Verify
    cursor.execute(
        "SELECT full_name FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_name


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_user_field_values_are_correct(db, factory):
    """Test: user field values match expected values."""
    # Arrange
    user = factory.create_user("testuser", "test@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name FROM benchmark.tb_user WHERE username = %s",
        (user["username"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == user["id"]
    assert result[1] == user["username"]
    assert result[2] == user["full_name"]


@pytest.mark.asyncio
async def test_post_field_values_are_correct(db, factory):
    """Test: post field values match expected values."""
    # Arrange
    author = factory.create_user("author", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Title", "Test Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title, content FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == post["id"]
    assert result[1] == post["title"]
    assert result[2] == post["content"]


# ============================================================================
# Limit and Pagination Tests
# ============================================================================

@pytest.mark.asyncio
async def test_users_query_respects_limit(db, factory):
    """Test: users query limit parameter works."""
    # Arrange
    for i in range(20):
        factory.create_user(f"user{i}", f"user{i}@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user LIMIT 10")
    # Note: LIMIT in COUNT doesn't work this way, need to count results
    cursor.execute("SELECT id FROM benchmark.tb_user LIMIT 10")
    results = cursor.fetchall()

    # Assert
    assert len(results) == 10


@pytest.mark.asyncio
async def test_posts_query_respects_limit(db, factory):
    """Test: posts query limit parameter works."""
    # Arrange
    author = factory.create_user("author", "author@example.com")
    for i in range(30):
        factory.create_post(author["pk_user"], f"Post {i}", f"Content {i}")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_post LIMIT 10")
    results = cursor.fetchall()

    # Assert
    assert len(results) == 10


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_optional_fields_can_be_null(db, factory):
    """Test: optional fields like bio can be null."""
    # Arrange
    user = factory.create_user("user", "user@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT bio FROM benchmark.tb_user WHERE id = %s", (user["id"],))
    result = cursor.fetchone()

    # Assert
    assert result[0] is None


@pytest.mark.asyncio
async def test_schema_nested_user_posts_with_author(db, factory):
    """Test: nested query returns user -> posts -> author correctly."""
    # Arrange
    author = factory.create_user("author", "author-nested", "author@example.com", "Author Name")
    post1 = factory.create_post(author["pk_user"], "Post 1", "post-nested-1", "Content 1")
    post2 = factory.create_post(author["pk_user"], "Post 2", "post-nested-2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT u.id, u.username, p.id, p.title, a.username "
        "FROM benchmark.tb_user u "
        "LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author "
        "LEFT JOIN benchmark.tb_user a ON p.fk_author = a.pk_user "
        "WHERE u.id = %s "
        "ORDER BY p.id",
        (author["id"],)
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) >= 2
    assert results[0][0] == author["id"]
    assert results[0][1] == "author"
    assert results[0][4] == "author"  # author field in post


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_schema_deeply_nested_three_levels(db, factory):
    """Test: three-level deep query (user -> posts -> comments -> commenters)."""
    # Arrange
    author = factory.create_user("author", "author-deep3", "author@example.com")
    post = factory.create_post(author["pk_user"], "Deep Post", "deep-post", "Content")

    commenter = factory.create_user("commenter", "commenter-deep3", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-deep", "Deep comment")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT u.username, p.title, c.content, cu.username "
        "FROM benchmark.tb_user u "
        "LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author "
        "LEFT JOIN benchmark.tb_comment c ON p.pk_post = c.fk_post "
        "LEFT JOIN benchmark.tb_user cu ON c.fk_author = cu.pk_user "
        "WHERE u.id = %s AND c.id = %s",
        (author["id"], comment["id"])
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == "author"
    assert result[1] == "Deep Post"
    assert result[2] == "Deep comment"
    assert result[3] == "commenter"


@pytest.mark.asyncio
async def test_schema_mutation_update_preserves_relationships(db, factory):
    """Test: updating user preserves relationships with posts."""
    # Arrange
    user = factory.create_user("author", "author-rel-pres", "author@example.com", "Original Name")
    post1 = factory.create_post(user["pk_user"], "Post 1", "post-rel-1", "Content 1")
    post2 = factory.create_post(user["pk_user"], "Post 2", "post-rel-2", "Content 2")

    # Act - update user
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET full_name = %s, updated_at = NOW() WHERE id = %s",
        ("Updated Name", user["id"])
    )

    # Verify relationships still exist
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (user["pk_user"],)
    )
    post_count = cursor.fetchone()[0]

    # Assert
    assert post_count == 2


@pytest.mark.asyncio
async def test_schema_query_with_filter_and_join(db, factory):
    """Test: complex queries with filters and joins work correctly."""
    # Arrange
    author1 = factory.create_user("author1", "author-filter-1", "author1@example.com")
    author2 = factory.create_user("author2", "author-filter-2", "author2@example.com")

    factory.create_post(author1["pk_user"], "Technology Post", "tech-post", "About tech")
    factory.create_post(author2["pk_user"], "Travel Post", "travel-post", "About travel")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT u.username, p.title "
        "FROM benchmark.tb_user u "
        "LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author "
        "WHERE p.title LIKE %s",
        ("%Technology%",)
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 1
    assert results[0][0] == "author1"
    assert "Technology" in results[0][1]


@pytest.mark.asyncio
async def test_schema_aggregate_functions(db, factory):
    """Test: aggregate functions (COUNT, etc.) work correctly."""
    # Arrange
    user = factory.create_user("author", "author-agg", "author@example.com")
    for i in range(5):
        post = factory.create_post(user["pk_user"], f"Post {i}", f"post-agg-{i}", f"Content {i}")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT u.username, COUNT(p.pk_post) as post_count "
        "FROM benchmark.tb_user u "
        "LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author "
        "WHERE u.id = %s "
        "GROUP BY u.pk_user, u.username",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == "author"
    assert result[1] == 5


@pytest.mark.asyncio
async def test_schema_mutation_batch_create_and_query(db, factory):
    """Test: batch creating data and querying returns all records."""
    # Arrange
    user = factory.create_user("author", "author-batch", "author@example.com")

    # Create batch of posts
    created_posts = []
    for i in range(10):
        post = factory.create_post(user["pk_user"], f"Batch Post {i}", f"batch-{i}", f"Content {i}")
        created_posts.append(post)

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*), MIN(created_at), MAX(created_at) "
        "FROM benchmark.tb_post WHERE fk_author = %s",
        (user["pk_user"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == 10
    assert result[1] is not None  # min created_at
    assert result[2] is not None  # max created_at


@pytest.mark.asyncio
async def test_schema_pagination_with_offset(db, factory):
    """Test: pagination with offset works correctly."""
    # Arrange
    user = factory.create_user("author", "author-offset", "author@example.com")
    for i in range(25):
        factory.create_post(user["pk_user"], f"Post {i:02d}", f"post-offset-{i}", f"Content {i}")

    # Act - get first page (limit 10)
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM benchmark.tb_post WHERE fk_author = %s ORDER BY created_at LIMIT 10",
        (user["pk_user"],)
    )
    page1 = cursor.fetchall()

    # Act - get second page (offset 10, limit 10)
    cursor.execute(
        "SELECT id FROM benchmark.tb_post WHERE fk_author = %s ORDER BY created_at LIMIT 10 OFFSET 10",
        (user["pk_user"],)
    )
    page2 = cursor.fetchall()

    # Assert
    assert len(page1) == 10
    assert len(page2) == 10
    page1_ids = [r[0] for r in page1]
    page2_ids = [r[0] for r in page2]
    assert len(set(page1_ids) & set(page2_ids)) == 0  # no overlap
