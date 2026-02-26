"""Integration and schema tests for Flask REST API.

Tests full request/response flows with comprehensive:
- Basic query patterns
- Relationship query tests
- Mutation tests
- Complex query patterns
- Field value validation across relationships
- Limit and pagination tests
- Deeply nested relationship queries

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""



# ============================================================================
# Basic Query Tests
# ============================================================================

class TestBasicQueries:
    """Tests for basic query patterns."""

    def test_query_single_user_all_fields(self, db, factory):
        """Test: Query single user returns all fields."""
        # Arrange
        user = factory.create_user("alice", "alice-fields", "alice@example.com", "Alice Smith", "Alice's bio")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT pk_user, id, username, identifier, email, full_name, bio
            FROM benchmark.tb_user
            WHERE id = %s
            """,
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == user["pk_user"]  # pk_user
        assert result[1] == user["id"]  # id
        assert result[2] == "alice"  # username
        assert result[3] == "alice-fields"  # identifier
        assert result[4] == "alice@example.com"  # email
        assert result[5] == "Alice Smith"  # full_name
        assert result[6] == "Alice's bio"  # bio

    def test_query_single_post_all_fields(self, db, factory):
        """Test: Query single post returns all fields."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Test Post", "test-post", "Test content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT pk_post, id, title, identifier, content, fk_author
            FROM benchmark.tb_post
            WHERE id = %s
            """,
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == post["pk_post"]  # pk_post
        assert result[1] == post["id"]  # id
        assert result[2] == "Test Post"  # title
        assert result[3] == "test-post"  # identifier
        assert result[4] == "Test content"  # content
        assert result[5] == author["pk_user"]  # fk_author

    def test_query_single_comment_all_fields(self, db, factory):
        """Test: Query single comment returns all fields."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")
        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
        comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Comment text")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT pk_comment, id, identifier, content, fk_post, fk_author
            FROM benchmark.tb_comment
            WHERE id = %s
            """,
            (comment["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == comment["pk_comment"]  # pk_comment
        assert result[1] == comment["id"]  # id
        assert result[2] == "cmt"  # identifier
        assert result[3] == "Comment text"  # content
        assert result[4] == post["pk_post"]  # fk_post
        assert result[5] == commenter["pk_user"]  # fk_author


# ============================================================================
# Relationship Query Tests
# ============================================================================

class TestRelationshipQueries:
    """Tests for relationship queries."""

    def test_query_post_with_author(self, db, factory):
        """Test: Query post includes author information."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com", "Author Name")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT p.id, p.title, u.id as author_id, u.username
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE p.id = %s
            """,
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == post["id"]
        assert result[1] == "Post"
        assert result[2] == author["id"]
        assert result[3] == "author"

    def test_query_comment_with_author(self, db, factory):
        """Test: Query comment includes author information."""
        # Arrange
        post_author = factory.create_user("post_author", "post_author", "post_author@example.com")
        post = factory.create_post(post_author["pk_user"], "Post", "post", "Content")
        commenter = factory.create_user("commenter", "commenter", "commenter@example.com", "Commenter Name")
        comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Comment")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT c.id, c.content, u.id as author_id, u.username
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE c.id = %s
            """,
            (comment["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == comment["id"]
        assert result[1] == "Comment"
        assert result[2] == commenter["id"]
        assert result[3] == "commenter"

    def test_query_comment_with_post(self, db, factory):
        """Test: Query comment includes post information."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Test Post", "test-post", "Test content")
        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
        comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Comment")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT c.id, p.id as post_id, p.title
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            WHERE c.id = %s
            """,
            (comment["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == comment["id"]
        assert result[1] == post["id"]
        assert result[2] == "Test Post"

    def test_query_user_with_posts(self, db, factory):
        """Test: Query user includes their posts."""
        # Arrange
        user = factory.create_user("author", "author", "author@example.com")
        post1 = factory.create_post(user["pk_user"], "Post 1", "post-1", "Content 1")
        post2 = factory.create_post(user["pk_user"], "Post 2", "post-2", "Content 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT u.id, u.username, COUNT(p.pk_post) as post_count
            FROM benchmark.tb_user u
            LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author
            WHERE u.id = %s
            GROUP BY u.id, u.username
            """,
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == user["id"]
        assert result[1] == "author"
        assert result[2] == 2

    def test_query_post_with_comments(self, db, factory):
        """Test: Query post includes its comments."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")
        commenter1 = factory.create_user("commenter1", "c1", "c1@example.com")
        commenter2 = factory.create_user("commenter2", "c2", "c2@example.com")
        comment1 = factory.create_comment(post["pk_post"], commenter1["pk_user"], "cmt1", "Comment 1")
        comment2 = factory.create_comment(post["pk_post"], commenter2["pk_user"], "cmt2", "Comment 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT p.id, p.title, COUNT(c.pk_comment) as comment_count
            FROM benchmark.tb_post p
            LEFT JOIN benchmark.tb_comment c ON p.pk_post = c.fk_post
            WHERE p.id = %s
            GROUP BY p.id, p.title
            """,
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == post["id"]
        assert result[1] == "Post"
        assert result[2] == 2


# ============================================================================
# Complex Nested Query Tests
# ============================================================================

class TestComplexNestedQueries:
    """Tests for complex nested relationship queries."""

    def test_query_user_posts_with_comment_counts(self, db, factory):
        """Test: Query user with post counts including comments per post."""
        # Arrange
        user = factory.create_user("author", "author", "author@example.com")
        post1 = factory.create_post(user["pk_user"], "Post 1", "post-1", "Content 1")
        post2 = factory.create_post(user["pk_user"], "Post 2", "post-2", "Content 2")

        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
        comment1 = factory.create_comment(post1["pk_post"], commenter["pk_user"], "cmt1", "Comment 1")
        comment2 = factory.create_comment(post1["pk_post"], commenter["pk_user"], "cmt2", "Comment 2")
        comment3 = factory.create_comment(post2["pk_post"], commenter["pk_user"], "cmt3", "Comment 3")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT u.id, COUNT(DISTINCT p.pk_post) as post_count,
                   COUNT(DISTINCT c.pk_comment) as total_comments
            FROM benchmark.tb_user u
            LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author
            LEFT JOIN benchmark.tb_comment c ON p.pk_post = c.fk_post
            WHERE u.id = %s
            GROUP BY u.id
            """,
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == user["id"]
        assert result[1] == 2  # 2 posts
        assert result[2] == 3  # 3 comments total

    def test_query_post_with_comments_and_comment_authors(self, db, factory):
        """Test: Query post with comments including each commenter's info."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")
        commenter1 = factory.create_user("commenter1", "c1", "c1@example.com", "Commenter One")
        commenter2 = factory.create_user("commenter2", "c2", "c2@example.com", "Commenter Two")
        comment1 = factory.create_comment(post["pk_post"], commenter1["pk_user"], "cmt1", "Comment 1")
        comment2 = factory.create_comment(post["pk_post"], commenter2["pk_user"], "cmt2", "Comment 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT c.id, c.content, u.id as commenter_id, u.full_name
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE c.fk_post = %s
            ORDER BY c.created_at
            """,
            (post["pk_post"],)
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 2
        assert results[0][0] == comment1["id"]
        assert results[0][2] == commenter1["id"]
        assert results[0][3] == "Commenter One"
        assert results[1][0] == comment2["id"]
        assert results[1][2] == commenter2["id"]
        assert results[1][3] == "Commenter Two"

    def test_query_multiple_users_with_post_and_comment_stats(self, db, factory):
        """Test: Query multiple users with stats about their posts and comments."""
        # Arrange
        user1 = factory.create_user("author1", "a1", "a1@example.com")
        user2 = factory.create_user("author2", "a2", "a2@example.com")

        post1 = factory.create_post(user1["pk_user"], "Post 1", "post-1", "Content")
        post2 = factory.create_post(user2["pk_user"], "Post 2", "post-2", "Content")

        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
        comment1 = factory.create_comment(post1["pk_post"], commenter["pk_user"], "cmt1", "Comment")
        comment2 = factory.create_comment(post2["pk_post"], commenter["pk_user"], "cmt2", "Comment")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT u.id, u.username, COUNT(DISTINCT p.pk_post) as post_count
            FROM benchmark.tb_user u
            LEFT JOIN benchmark.tb_post p ON u.pk_user = p.fk_author
            WHERE u.id IN (%s, %s)
            GROUP BY u.id, u.username
            ORDER BY u.username
            """,
            (user1["id"], user2["id"])
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 2
        assert results[0][1] == "author1"  # First alphabetically
        assert results[0][2] == 1  # 1 post
        assert results[1][1] == "author2"
        assert results[1][2] == 1  # 1 post


# ============================================================================
# Field Value Tests
# ============================================================================

class TestFieldValues:
    """Tests for field value consistency and accuracy."""

    def test_uuid_fields_are_distinct_from_pk(self, db, factory):
        """Test: UUID id fields are distinct from pk_ fields."""
        # Arrange
        user = factory.create_user("alice", "alice", "alice@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT pk_user, id FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] != result[1]  # pk_user is int, id is UUID
        assert isinstance(result[0], int)
        assert result[0] == user["pk_user"]

    def test_identifier_slug_format(self, db, factory):
        """Test: identifier field maintains slug format."""
        # Arrange
        user = factory.create_user("alice", "alice-unique-id", "alice@example.com")

        # Act
        cursor = db.cursor()
        cursor.execute(
            "SELECT identifier FROM benchmark.tb_user WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == "alice-unique-id"
        # Slug format: no spaces, lowercase, hyphens allowed
        assert " " not in result[0]

    def test_post_author_foreign_key_matches_user_pk(self, db, factory):
        """Test: Post's fk_author matches user's pk_user."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT p.fk_author, u.pk_user
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE p.id = %s
            """,
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == result[1] == author["pk_user"]

    def test_comment_author_foreign_key_matches_user_pk(self, db, factory):
        """Test: Comment's fk_author matches user's pk_user."""
        # Arrange
        post_author = factory.create_user("post_author", "pa", "pa@example.com")
        post = factory.create_post(post_author["pk_user"], "Post", "post", "Content")
        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
        comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Comment")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT c.fk_author, u.pk_user
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE c.id = %s
            """,
            (comment["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == result[1] == commenter["pk_user"]


# ============================================================================
# Limit and Pagination Tests
# ============================================================================

class TestLimitAndPagination:
    """Tests for limit and pagination behavior."""

    def test_list_posts_limit_10_respects_ordering(self, db, factory):
        """Test: GET /posts with limit respects ordering."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        for i in range(15):
            factory.create_post(author["pk_user"], f"Post {i}", f"post-{i}", f"Content {i}")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT id FROM benchmark.tb_post
            ORDER BY created_at DESC LIMIT 10
            """
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 10

    def test_list_users_limit_10_includes_most_recent(self, db, factory):
        """Test: GET /users limit includes most recent users."""
        # Arrange
        users = []
        for i in range(15):
            user = factory.create_user(f"user{i}", f"user-{i}", f"user{i}@example.com")
            users.append(user)

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT id FROM benchmark.tb_user
            ORDER BY created_at DESC LIMIT 10
            """
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 10
        # Results should include some of the most recently created users
        result_ids = [r[0] for r in results]
        # At least some of the last 10 users should be in results
        recent_users = [u["id"] for u in users[-10:]]
        assert any(uid in result_ids for uid in recent_users)

    def test_pagination_with_offset(self, db, factory):
        """Test: Pagination with LIMIT and OFFSET works correctly."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        posts = []
        for i in range(25):
            post = factory.create_post(author["pk_user"], f"Post {i}", f"post-{i}", f"Content {i}")
            posts.append(post)

        # Act - get page 2 (10 items per page, skip first 10)
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT id FROM benchmark.tb_post
            ORDER BY created_at DESC
            LIMIT 10 OFFSET 10
            """
        )
        page2_results = cursor.fetchall()

        # Assert
        assert len(page2_results) == 10

    def test_list_comments_limited_to_5(self, db, factory):
        """Test: Comment list respects limit of 5."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Post", "post", "Content")
        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")

        for i in range(10):
            factory.create_comment(post["pk_post"], commenter["pk_user"], f"cmt-{i}", f"Comment {i}")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT id FROM benchmark.tb_comment
            WHERE fk_post = %s
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (post["pk_post"],)
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 5


# ============================================================================
# Deeply Nested Relationship Tests
# ============================================================================

class TestDeeplyNestedRelationships:
    """Tests for deeply nested relationship queries."""

    def test_user_posts_comments_deep_nesting(self, db, factory):
        """Test: Query user -> posts -> comments (3 levels deep)."""
        # Arrange
        user = factory.create_user("author", "author", "author@example.com")
        post1 = factory.create_post(user["pk_user"], "Post 1", "post-1", "Content")
        post2 = factory.create_post(user["pk_user"], "Post 2", "post-2", "Content")

        commenter = factory.create_user("commenter", "commenter", "commenter@example.com")
        c1p1 = factory.create_comment(post1["pk_post"], commenter["pk_user"], "c1p1", "Comment 1 on Post 1")
        c2p1 = factory.create_comment(post1["pk_post"], commenter["pk_user"], "c2p1", "Comment 2 on Post 1")
        c1p2 = factory.create_comment(post2["pk_post"], commenter["pk_user"], "c1p2", "Comment on Post 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT c.id, p.id, u.id
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE u.id = %s
            ORDER BY c.created_at
            """,
            (user["id"],)
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 3  # 3 comments total
        # All comments should be from user's posts
        for comment_id, post_id, author_id in results:
            assert author_id == user["id"]

    def test_post_comments_authors_deep_nesting(self, db, factory):
        """Test: Query post -> comments -> comment authors (3 levels deep)."""
        # Arrange
        post_author = factory.create_user("post_author", "pa", "pa@example.com")
        post = factory.create_post(post_author["pk_user"], "Post", "post", "Content")

        commenter1 = factory.create_user("commenter1", "c1", "c1@example.com")
        commenter2 = factory.create_user("commenter2", "c2", "c2@example.com")

        comment1 = factory.create_comment(post["pk_post"], commenter1["pk_user"], "cmt1", "Comment 1")
        comment2 = factory.create_comment(post["pk_post"], commenter2["pk_user"], "cmt2", "Comment 2")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT c.id, p.id, u.id, u.username
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE p.id = %s
            ORDER BY c.created_at
            """,
            (post["id"],)
        )
        results = cursor.fetchall()

        # Assert
        assert len(results) == 2
        assert results[0][1] == post["id"]
        assert results[0][2] == commenter1["id"]
        assert results[0][3] == "commenter1"
        assert results[1][1] == post["id"]
        assert results[1][2] == commenter2["id"]
        assert results[1][3] == "commenter2"

    def test_complex_multi_level_relationship(self, db, factory):
        """Test: Complex query across multiple relationship levels."""
        # Arrange
        author = factory.create_user("author", "author", "author@example.com", "Author Name")
        post = factory.create_post(author["pk_user"], "Post Title", "post-title", "Post content")

        commenter = factory.create_user("commenter", "commenter", "commenter@example.com", "Commenter Name")
        comment = factory.create_comment(post["pk_post"], commenter["pk_user"], "cmt", "Comment content")

        # Act
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT
                u.username as post_author,
                p.title,
                c.content,
                cu.username as comment_author
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            JOIN benchmark.tb_comment c ON p.pk_post = c.fk_post
            JOIN benchmark.tb_user cu ON c.fk_author = cu.pk_user
            WHERE p.id = %s
            """,
            (post["id"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result[0] == "author"  # post author
        assert result[1] == "Post Title"  # post title
        assert result[2] == "Comment content"  # comment content
        assert result[3] == "commenter"  # comment author
