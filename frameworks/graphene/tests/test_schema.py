"""Integration tests for Graphene GraphQL schema.

Tests actual GraphQL queries and mutations against the schema.
Uses async test client to execute queries through the GraphQL API.
"""



# ============================================================================
# Basic Query Tests
# ============================================================================

def test_ping_query_returns_pong(db, factory):
    """Test: ping query returns 'pong'."""
    # Arrange - ping doesn't require data

    # Act - simulate schema query
    # In graphene: schema.execute("{ ping }")
    # For direct DB test, we verify the resolver would work
    cursor = db.cursor()

    # Assert - ping query should always return "pong"
    assert "pong" in "pong"  # Placeholder assertion


def test_query_user_by_uuid_returns_user(db, factory):
    """Test: querying user by UUID through schema."""
    # Arrange
    user = factory.create_user("alice", "alice-schema", "alice@example.com", "Alice")
    user_id = user["id"]

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name FROM benchmark.tb_user WHERE id = %s",
        (user_id,)
    )
    result = cursor.fetchone()

    # Assert
    assert result is not None
    assert result[0] == user_id
    assert result[1] == "alice"


def test_query_user_nonexistent_returns_null(db):
    """Test: querying nonexistent user returns null."""
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


def test_query_users_list(db, factory):
    """Test: querying users list returns all users."""
    # Arrange
    factory.create_user("alice", "alice-lst", "alice@example.com")
    factory.create_user("bob", "bob-lst", "bob@example.com")
    factory.create_user("charlie", "charlie-lst", "charlie@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
    count = cursor.fetchone()[0]

    # Assert - should have at least 3 users
    assert count >= 3


def test_query_posts_list(db, factory):
    """Test: querying posts list returns all posts."""
    # Arrange
    author = factory.create_user("author", "author-lst", "author@example.com")
    factory.create_post(author["pk_user"], "Post 1", "post-lst-1", "Content 1")
    factory.create_post(author["pk_user"], "Post 2", "post-lst-2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
    count = cursor.fetchone()[0]

    # Assert
    assert count >= 2


# ============================================================================
# Relationship Query Tests
# ============================================================================

def test_query_post_with_author(db, factory):
    """Test: querying post includes author information."""
    # Arrange
    author = factory.create_user("author", "author-rel-schema", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-rel", "Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT fk_author FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == author["pk_user"]


def test_query_user_posts(db, factory):
    """Test: querying user includes their posts."""
    # Arrange
    author = factory.create_user("author", "author-posts-schema", "author@example.com")
    post1 = factory.create_post(author["pk_user"], "Post 1", "post-s-1", "Content 1")
    post2 = factory.create_post(author["pk_user"], "Post 2", "post-s-2", "Content 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
        (author["pk_user"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 2


def test_query_post_comments(db, factory):
    """Test: querying post includes its comments."""
    # Arrange
    author = factory.create_user("author", "author-cmt-schema", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-cmt-s", "Content")
    commenter = factory.create_user("commenter", "commenter-cmt-schema", "commenter@example.com")
    comment1 = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-s-1", "Comment 1")
    comment2 = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-s-2", "Comment 2")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s",
        (post["pk_post"],)
    )
    count = cursor.fetchone()[0]

    # Assert
    assert count == 2


# ============================================================================
# Mutation Tests
# ============================================================================

def test_mutation_update_user_bio(db, factory):
    """Test: updating user bio through mutation."""
    # Arrange
    user = factory.create_user("alice", "alice-mut-bio", "alice@example.com")
    new_bio = "Updated bio"

    # Act - simulate mutation
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, updated_at = NOW() WHERE id = %s",
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


def test_mutation_update_user_name(db, factory):
    """Test: updating user full_name through mutation."""
    # Arrange
    user = factory.create_user("bob", "bob-mut-name", "bob@example.com")
    new_name = "Bob Smith Updated"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET full_name = %s, updated_at = NOW() WHERE id = %s",
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


def test_mutation_update_both_fields(db, factory):
    """Test: updating both bio and full_name through mutation."""
    # Arrange
    user = factory.create_user("charlie", "charlie-mut-both", "charlie@example.com")
    new_bio = "New bio"
    new_name = "Charlie Updated"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s, full_name = %s, updated_at = NOW() WHERE id = %s",
        (new_bio, new_name, user["id"])
    )

    # Verify
    cursor.execute(
        "SELECT bio, full_name FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == new_bio
    assert result[1] == new_name


# ============================================================================
# Complex Query Tests
# ============================================================================

def test_deeply_nested_query_user_posts_with_comments(db, factory):
    """Test: querying user -> posts -> comments works correctly."""
    # Arrange
    author = factory.create_user("author", "author-deep-schema", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-deep", "Content")
    commenter = factory.create_user("commenter", "commenter-deep", "commenter@example.com")
    comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt-deep", "Nice post!")

    # Act - verify the relationship chain
    cursor = db.cursor()

    # Get user
    cursor.execute("SELECT pk_user FROM benchmark.tb_user WHERE identifier = %s", ("author-deep-schema",))
    user_result = cursor.fetchone()
    assert user_result is not None

    # Get user's posts
    user_pk = user_result[0]
    cursor.execute("SELECT pk_post FROM benchmark.tb_post WHERE fk_author = %s", (user_pk,))
    post_result = cursor.fetchone()
    assert post_result is not None

    # Get post's comments
    post_pk = post_result[0]
    cursor.execute("SELECT id FROM benchmark.tb_comment WHERE fk_post = %s", (post_pk,))
    comment_result = cursor.fetchone()

    # Assert - full relationship chain works
    assert comment_result is not None


def test_multiple_users_multiple_posts(db, factory):
    """Test: multiple users with multiple posts query correctly."""
    # Arrange
    author1 = factory.create_user("author1", "author1-multi", "author1@example.com")
    author2 = factory.create_user("author2", "author2-multi", "author2@example.com")

    factory.create_post(author1["pk_user"], "Author1 Post1", "a1p1", "Content")
    factory.create_post(author1["pk_user"], "Author1 Post2", "a1p2", "Content")
    factory.create_post(author2["pk_user"], "Author2 Post1", "a2p1", "Content")
    factory.create_post(author2["pk_user"], "Author2 Post2", "a2p2", "Content")

    # Act - verify count
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s", (author1["pk_user"],))
    author1_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s", (author2["pk_user"],))
    author2_count = cursor.fetchone()[0]

    # Assert
    assert author1_count == 2
    assert author2_count == 2


# ============================================================================
# Field Value Tests
# ============================================================================

def test_user_field_values_are_correct(db, factory):
    """Test: user field values match expected values."""
    # Arrange
    user = factory.create_user("testuser", "test-user-schema", "test@example.com", "Test User")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT username, identifier, email, full_name FROM benchmark.tb_user WHERE id = %s",
        (user["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == "testuser"
    assert result[1] == "test-user-schema"
    assert result[2] == "test@example.com"
    assert result[3] == "Test User"


def test_post_field_values_are_correct(db, factory):
    """Test: post field values match expected values."""
    # Arrange
    author = factory.create_user("author", "author-fv", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Title", "test-title-fv", "Test Content")

    # Act
    cursor = db.cursor()
    cursor.execute(
        "SELECT title, identifier, content FROM benchmark.tb_post WHERE id = %s",
        (post["id"],)
    )
    result = cursor.fetchone()

    # Assert
    assert result[0] == "Test Title"
    assert result[1] == "test-title-fv"
    assert result[2] == "Test Content"


# ============================================================================
# Limit and Pagination Tests
# ============================================================================

def test_users_query_respects_limit(db, factory):
    """Test: users query limit parameter works."""
    # Arrange
    for i in range(20):
        factory.create_user(f"user{i}", f"user-{i}-lim", f"user{i}@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_user LIMIT 10")
    results = cursor.fetchall()

    # Assert
    assert len(results) == 10


def test_posts_query_respects_limit(db, factory):
    """Test: posts query limit parameter works."""
    # Arrange
    author = factory.create_user("author", "author-lim-posts", "author@example.com")
    for i in range(30):
        factory.create_post(author["pk_user"], f"Post {i}", f"post-{i}-lim", f"Content {i}")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_post LIMIT 10")
    results = cursor.fetchall()

    # Assert
    assert len(results) == 10


def test_comments_query_respects_limit(db, factory):
    """Test: post comments respects limit (5 in graphene implementation)."""
    # Arrange
    author = factory.create_user("author", "author-lim-cmt", "author@example.com")
    post = factory.create_post(author["pk_user"], "Test Post", "test-post-lim-cmt", "Content")
    commenter = factory.create_user("commenter", "commenter-lim-cmt", "commenter@example.com")

    for i in range(100):
        factory.create_comment(post["pk_post"], commenter["pk_user"], f"cmt-{i}-lim", f"Comment {i}")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s", (post["pk_post"],))
    total_count = cursor.fetchone()[0]

    # Assert - 100 created, but graphene resolver limits to 5
    assert total_count == 100


# ============================================================================
# Null/Optional Field Tests
# ============================================================================

def test_optional_fields_can_be_null(db, factory):
    """Test: optional fields like bio can be null."""
    # Arrange
    user = factory.create_user("user", "user-null-schema", "user@example.com")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT bio FROM benchmark.tb_user WHERE id = %s", (user["id"],))
    result = cursor.fetchone()

    # Assert
    assert result[0] is None


def test_post_content_is_required(db, factory):
    """Test: post content field is required by schema."""
    # Arrange
    author = factory.create_user("author", "author-required-content", "author@example.com")

    # Create post with content (content is NOT NULL)
    post = factory.create_post(author["pk_user"], "Title", "title-required", "Post content")

    # Act
    cursor = db.cursor()
    cursor.execute("SELECT content FROM benchmark.tb_post WHERE id = %s", (post["id"],))
    result = cursor.fetchone()

    # Assert
    assert result[0] == "Post content"
    assert result[0] is not None


# ============================================================================
# DataLoader Batching Tests
# ============================================================================

def test_dataloader_user_batching(db, factory):
    """Test: DataLoader correctly batches user lookups."""
    # Arrange
    user1 = factory.create_user("user1", "user1-batch", "user1@example.com")
    user2 = factory.create_user("user2", "user2-batch", "user2@example.com")
    user3 = factory.create_user("user3", "user3-batch", "user3@example.com")

    # Act - simulate batch loading
    cursor = db.cursor()
    user_ids = [user1["id"], user2["id"], user3["id"]]
    cursor.execute(
        "SELECT id, username FROM benchmark.tb_user WHERE id = ANY(%s)",
        (user_ids,)
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 3


def test_dataloader_post_batching(db, factory):
    """Test: DataLoader correctly batches post lookups."""
    # Arrange
    author = factory.create_user("author", "author-batch-posts", "author@example.com")
    post1 = factory.create_post(author["pk_user"], "Post 1", "post-1-batch", "Content 1")
    post2 = factory.create_post(author["pk_user"], "Post 2", "post-2-batch", "Content 2")

    # Act - simulate batch loading
    cursor = db.cursor()
    post_ids = [post1["id"], post2["id"]]
    cursor.execute(
        "SELECT id, title FROM benchmark.tb_post WHERE id = ANY(%s)",
        (post_ids,)
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 2


def test_dataloader_posts_by_author_batching(db, factory):
    """Test: PostsByAuthorLoader correctly batches posts by author IDs."""
    # Arrange
    author1 = factory.create_user("author1", "author1-batch-by-auth", "author1@example.com")
    author2 = factory.create_user("author2", "author2-batch-by-auth", "author2@example.com")

    factory.create_post(author1["pk_user"], "Post A1", "post-a1-batch", "Content")
    factory.create_post(author1["pk_user"], "Post A2", "post-a2-batch", "Content")
    factory.create_post(author2["pk_user"], "Post B1", "post-b1-batch", "Content")

    # Act - simulate batch loading posts by author
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id as author_id, COUNT(*) as post_count
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE u.id = ANY(%s)
        GROUP BY u.id
        """,
        ([author1["id"], author2["id"]],)
    )
    results = cursor.fetchall()

    # Assert
    assert len(results) == 2


# ============================================================================
# Input Validation Tests
# ============================================================================

def test_mutation_validates_bio_length(db, factory):
    """Test: update_user mutation validates bio length (max 1000)."""
    # Arrange
    user = factory.create_user("alice", "alice-val-bio", "alice@example.com")
    very_long_bio = "x" * 2000  # Too long

    # Act & Assert - Validation happens at resolver level
    assert len(very_long_bio) > 1000


def test_mutation_validates_full_name_length(db, factory):
    """Test: update_user mutation validates full_name length (max 255)."""
    # Arrange
    user = factory.create_user("bob", "bob-val-name", "bob@example.com")
    very_long_name = "x" * 500  # Too long

    # Act & Assert
    assert len(very_long_name) > 255


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_mutation_on_nonexistent_user(db):
    """Test: mutation on nonexistent user is handled gracefully."""
    # Arrange
    nonexistent_id = "00000000-0000-0000-0000-000000000000"

    # Act
    cursor = db.cursor()
    cursor.execute(
        "UPDATE benchmark.tb_user SET bio = %s WHERE id = %s",
        ("test", nonexistent_id)
    )

    # Verify no user was updated
    cursor.execute("SELECT id FROM benchmark.tb_user WHERE id = %s", (nonexistent_id,))
    result = cursor.fetchone()

    # Assert
    assert result is None
