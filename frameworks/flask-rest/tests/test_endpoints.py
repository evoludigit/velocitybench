"""Enhanced endpoint tests for Flask REST API.

Tests core endpoint functionality with comprehensive coverage of:
- User endpoints (GET list, GET by ID)
- Post endpoints (GET list, GET by ID)
- Comment retrieval
- Relationship includes and nested data

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""



# ============================================================================
# User Endpoints: GET /users
# ============================================================================

class TestListUsersEndpoint:
    """Tests for GET /users endpoint."""

    def test_list_users_returns_list(self, db, factory):
        """Test: GET /users endpoint returns list of users."""
        # Arrange
        alice = factory.create_user("alice", "alice", "alice@example.com", "Alice")
        bob = factory.create_user("bob", "bob", "bob@example.com", "Bob")
        charlie = factory.create_user("charlie", "charlie", "charlie@example.com", "Charlie")

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

    def test_list_users_respects_limit(self, db, factory):
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

    def test_list_users_respects_limit_0(self, db, factory):
        """Test: GET /users with limit=0 returns no results."""
        # Arrange
        factory.create_user("alice", "alice", "alice@example.com")
        factory.create_user("bob", "bob", "bob@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user ORDER BY created_at DESC LIMIT 0"
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 0

    def test_list_users_respects_limit_1(self, db, factory):
        """Test: GET /users with limit=1 returns single result."""
        # Arrange
        factory.create_user("alice", "alice", "alice@example.com")
        factory.create_user("bob", "bob", "bob@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user ORDER BY created_at DESC LIMIT 1"
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 1

    def test_list_users_response_contains_required_fields(self, db, factory):
        """Test: GET /users response contains required fields."""
        # Arrange
        factory.create_user("alice", "alice", "alice@example.com", "Alice Smith")

        # Act
        cursor = db.cursor()
        cursor.execute("SELECT id, username, identifier, full_name FROM benchmark.tb_user")
        result = cursor.fetchone()

        # Assert
        assert result[0] is not None  # id (UUID)
        assert result[1] == "alice"  # username
        assert result[2] == "alice"  # identifier
        assert result[3] == "Alice Smith"  # full_name

    def test_list_users_empty_response(self, db):
        """Test: GET /users returns empty list when no users exist."""
        # Act
        cursor = db.cursor()
        cursor.execute("SELECT id FROM benchmark.tb_user")
        results = cursor.fetchall()

        # Assert
        assert len(results) == 0

    def test_list_users_ordering_by_created_at(self, db, factory):
        """Test: GET /users returns users ordered by created_at DESC."""
        # Arrange
        alice = factory.create_user("alice", "alice", "alice@example.com")
        bob = factory.create_user("bob", "bob", "bob@example.com")
        charlie = factory.create_user("charlie", "charlie", "charlie@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_user ORDER BY created_at DESC LIMIT 10"
        )
        results = cursor.fetchall()

        # Assert - charlie should be last (most recent)
        assert results[-1][0] == charlie["id"]


# ============================================================================
# User Endpoints: GET /users/{user_id}
# ============================================================================

class TestGetUserByIdEndpoint:
    """Tests for GET /users/{user_id} endpoint."""

    def test_get_user_by_id_returns_user(self, db, factory):
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
        assert result[2] == "Alice"

    def test_get_user_by_id_all_fields_present(self, db, factory):
        """Test: GET /users/{user_id} includes all user fields."""
        # Arrange
        user = factory.create_user("alice", "alice-fields", "alice@example.com", "Alice", "Alice's bio")
        user_id = user["id"]

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, username, identifier, email, full_name, bio FROM benchmark.tb_user WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == user_id  # id
        assert result[1] == "alice"  # username
        assert result[2] == "alice-fields"  # identifier
        assert result[3] == "alice@example.com"  # email
        assert result[4] == "Alice"  # full_name
        assert result[5] == "Alice's bio"  # bio

    def test_get_user_by_id_with_null_bio(self, db, factory):
        """Test: GET /users/{user_id} handles null bio."""
        # Arrange
        user = factory.create_user("bob", "bob-null", "bob@example.com")
        user_id = user["id"]

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT bio FROM benchmark.tb_user WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] is None

    def test_get_user_nonexistent_returns_404(self, db):
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

    def test_get_user_by_identifier_lookup(self, db, factory):
        """Test: User lookup can use identifier field."""
        # Arrange
        user = factory.create_user("alice", "alice-unique-id", "alice@example.com")
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
        assert result[0] == user["id"]
        assert result[1] == identifier


# ============================================================================
# User Endpoints with Includes
# ============================================================================

class TestUserEndpointWithIncludes:
    """Tests for GET /users with relationship includes."""

    def test_get_user_with_posts_include(self, db, factory):
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
        titles = [p[1] for p in posts]
        assert "Post 1" in titles
        assert "Post 2" in titles

    def test_get_user_posts_limited_to_10(self, db, factory):
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

    def test_get_user_posts_empty_when_no_posts(self, db, factory):
        """Test: User with no posts returns empty posts array."""
        # Arrange
        user = factory.create_user("author", "author-no-posts", "author@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT id FROM benchmark.tb_post WHERE fk_author = %s
            """,
            (user["pk_user"],)
        )
        posts = cursor.fetchall()

        # Assert
        assert len(posts) == 0

    def test_get_user_with_nested_includes_posts_comments(self, db, factory):
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
        assert comments[0][1] == "Great!"


# ============================================================================
# Post Endpoints: GET /posts
# ============================================================================

class TestListPostsEndpoint:
    """Tests for GET /posts endpoint."""

    def test_list_posts_returns_list(self, db, factory):
        """Test: GET /posts endpoint returns list of posts."""
        # Arrange
        author = factory.create_user("author", "author-lst", "author@example.com")
        post1 = factory.create_post(author["pk_user"], "Post 1", "post-lst-1", "Content 1")
        post2 = factory.create_post(author["pk_user"], "Post 2", "post-lst-2", "Content 2")

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
        titles = [r[1] for r in results]
        assert "Post 1" in titles
        assert "Post 2" in titles

    def test_list_posts_respects_limit(self, db, factory):
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

    def test_list_posts_respects_limit_1(self, db, factory):
        """Test: GET /posts with limit=1 returns single post."""
        # Arrange
        author = factory.create_user("author", "author-lim-1", "author@example.com")
        factory.create_post(author["pk_user"], "Post 1", "post-1", "Content 1")
        factory.create_post(author["pk_user"], "Post 2", "post-2", "Content 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_post ORDER BY created_at DESC LIMIT 1"
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 1

    def test_list_posts_ordering_by_created_at(self, db, factory):
        """Test: GET /posts returns posts ordered by created_at DESC."""
        # Arrange
        author = factory.create_user("author", "author-ord", "author@example.com")
        post1 = factory.create_post(author["pk_user"], "Post 1", "post-1-ord", "Content 1")
        post2 = factory.create_post(author["pk_user"], "Post 2", "post-2-ord", "Content 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM benchmark.tb_post ORDER BY created_at DESC LIMIT 10"
        )
        results = cursor.fetchall()

        # Assert - results should include both posts and be ordered by created_at
        assert len(results) >= 2
        post_ids = [r[0] for r in results]
        assert post1["id"] in post_ids
        assert post2["id"] in post_ids


# ============================================================================
# Post Endpoints: GET /posts/{post_id}
# ============================================================================

class TestGetPostByIdEndpoint:
    """Tests for GET /posts/{post_id} endpoint."""

    def test_get_post_by_id_returns_post(self, db, factory):
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
        assert result[2] == "Test content"

    def test_get_post_by_id_all_fields_present(self, db, factory):
        """Test: GET /posts/{post_id} includes all post fields."""
        # Arrange
        author = factory.create_user("author", "author-fields", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post Title", "post-slug", "Post content")
        post_id = post["id"]

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, title, identifier, content FROM benchmark.tb_post WHERE id = %s",
            (post_id,)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == post_id  # id
        assert result[1] == "Post Title"  # title
        assert result[2] == "post-slug"  # identifier
        assert result[3] == "Post content"  # content

    def test_get_post_nonexistent_returns_404(self, db):
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

    def test_get_post_with_comments_include(self, db, factory):
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
        assert comments[0][1] == "Comment"

    def test_get_post_with_author_include(self, db, factory):
        """Test: GET /posts/{post_id}?include=author includes author information."""
        # Arrange
        author = factory.create_user("author", "author-post-auth", "author@example.com", "Author Name")
        post = factory.create_post(author["pk_user"], "Test Post", "test-post-auth", "Content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT u.id, u.username, u.full_name
            FROM benchmark.tb_user u
            WHERE u.pk_user = (SELECT fk_author FROM benchmark.tb_post WHERE id = %s)
            """,
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result is not None
        assert result[0] == author["id"]
        assert result[1] == "author"
        assert result[2] == "Author Name"


# ============================================================================
# Post Endpoints with Includes
# ============================================================================

class TestPostEndpointWithIncludes:
    """Tests for GET /posts with relationship includes."""

    def test_list_posts_with_author_include(self, db, factory):
        """Test: GET /posts?include=author includes author information."""
        # Arrange
        author = factory.create_user("author", "author-posts-inc", "author@example.com", "Author")
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
        assert result[1] == "author"

    def test_list_posts_with_comments_include(self, db, factory):
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
        assert comments[0][1] == "Good!"


# ============================================================================
# Deeply Nested Includes Tests
# ============================================================================

class TestNestedIncludes:
    """Tests for deeply nested relationship includes."""

    def test_deeply_nested_includes_user_posts_comments(self, db, factory):
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

    def test_deeply_nested_includes_posts_comments_author(self, db, factory):
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

    def test_multiple_posts_with_multiple_comments_per_post(self, db, factory):
        """Test: User with multiple posts, each with multiple comments."""
        # Arrange
        author = factory.create_user("author", "author-multi", "author@example.com")
        post1 = factory.create_post(author["pk_user"], "Post 1", "post-1-multi", "Content 1")
        post2 = factory.create_post(author["pk_user"], "Post 2", "post-2-multi", "Content 2")

        commenter1 = factory.create_user("commenter1", "cmt1", "cmt1@example.com")
        commenter2 = factory.create_user("commenter2", "cmt2", "cmt2@example.com")

        c1p1 = factory.create_comment(post1["pk_post"], commenter1["pk_user"], "c1p1", "Comment 1 on Post 1")
        c1p2 = factory.create_comment(post1["pk_post"], commenter2["pk_user"], "c1p2", "Comment 2 on Post 1")
        c2p2 = factory.create_comment(post2["pk_post"], commenter1["pk_user"], "c2p2", "Comment 1 on Post 2")

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
        total_comments = cursor.fetchone()[0]

        # Assert
        assert total_comments == 3
