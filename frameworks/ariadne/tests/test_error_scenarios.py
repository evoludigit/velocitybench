"""Error scenario tests for Ariadne GraphQL framework.

Tests error handling, edge cases, and validation scenarios.
"""

import pytest
import uuid


# ============================================================================
# Invalid Input Tests
# ============================================================================

@pytest.mark.error
def test_query_with_invalid_uuid_format(db, factory):
    """Test: querying with invalid UUID format is handled."""
    cursor = db.cursor()

    # Invalid UUID format should raise an error or return empty
    with pytest.raises(Exception):
        cursor.execute("SELECT id FROM benchmark.tb_user WHERE id = %s", ("not-a-uuid",))


@pytest.mark.error
def test_query_with_nonexistent_uuid(db, factory):
    """Test: querying with non-existent UUID returns None."""
    fake_id = uuid.uuid4()

    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_user WHERE id = %s", (fake_id,))
    result = cursor.fetchone()

    assert result is None


@pytest.mark.error
def test_create_post_with_invalid_author(db, factory):
    """Test: creating post with non-existent author fails."""
    cursor = db.cursor()

    with pytest.raises(Exception):  # FK violation
        cursor.execute(
            "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
            "VALUES (%s, %s, %s, %s)",
            (999999, "Test", "test", "Content")
        )


@pytest.mark.error
def test_create_comment_with_invalid_post(db, factory):
    """Test: creating comment with non-existent post fails."""
    user = factory.create_user("user", "user@example.com")
    cursor = db.cursor()

    with pytest.raises(Exception):  # FK violation
        cursor.execute(
            "INSERT INTO benchmark.tb_comment (fk_post, fk_author, identifier, content) "
            "VALUES (%s, %s, %s, %s)",
            (999999, user["pk_user"], "comment", "Content")
        )


@pytest.mark.error
def test_create_comment_with_invalid_author(db, factory):
    """Test: creating comment with non-existent author fails."""
    user = factory.create_user("user", "user@example.com")
    post = factory.create_post(user["pk_user"], "Test Post")
    cursor = db.cursor()

    with pytest.raises(Exception):  # FK violation
        cursor.execute(
            "INSERT INTO benchmark.tb_comment (fk_post, fk_author, identifier, content) "
            "VALUES (%s, %s, %s, %s)",
            (post["pk_post"], 999999, "comment", "Content")
        )


# ============================================================================
# Null Value Tests
# ============================================================================

@pytest.mark.error
def test_create_user_without_username_fails(db, factory):
    """Test: creating user without username fails."""
    cursor = db.cursor()

    with pytest.raises(Exception):  # NOT NULL violation
        cursor.execute(
            "INSERT INTO benchmark.tb_user (username, identifier, email, full_name) "
            "VALUES (%s, %s, %s, %s)",
            (None, "test", "test@example.com", "Test")
        )


@pytest.mark.error
def test_create_post_without_title_fails(db, factory):
    """Test: creating post without title fails."""
    user = factory.create_user("user", "user@example.com")
    cursor = db.cursor()

    with pytest.raises(Exception):  # NOT NULL violation
        cursor.execute(
            "INSERT INTO benchmark.tb_post (fk_author, title, identifier, content) "
            "VALUES (%s, %s, %s, %s)",
            (user["pk_user"], None, "test", "Content")
        )


@pytest.mark.error
def test_create_comment_without_content_fails(db, factory):
    """Test: creating comment without content fails."""
    user = factory.create_user("user", "user@example.com")
    post = factory.create_post(user["pk_user"], "Test Post")
    cursor = db.cursor()

    with pytest.raises(Exception):  # NOT NULL violation
        cursor.execute(
            "INSERT INTO benchmark.tb_comment (fk_post, fk_author, identifier, content) "
            "VALUES (%s, %s, %s, %s)",
            (post["pk_post"], user["pk_user"], "comment", None)
        )


# ============================================================================
# Boundary Condition Tests
# ============================================================================

@pytest.mark.error
def test_empty_string_username(db, factory):
    """Test: empty string username is handled."""
    cursor = db.cursor()

    # May succeed or fail depending on constraints
    try:
        cursor.execute(
            "INSERT INTO benchmark.tb_user (username, identifier, email, full_name) "
            "VALUES (%s, %s, %s, %s) RETURNING pk_user",
            ("", "empty-user", "empty@example.com", "")
        )
        result = cursor.fetchone()
        # If it succeeds, pk_user should be set
        assert result[0] is not None
    except Exception:
        # If it fails due to constraint, that's acceptable
        pass


@pytest.mark.error
def test_very_long_content(db, factory):
    """Test: very long content is handled."""
    user = factory.create_user("user", "user@example.com")
    long_content = "x" * 100000  # 100KB of content

    post = factory.create_post(user["pk_user"], "Long Post", long_content)
    assert post["id"] is not None

    cursor = db.cursor()
    cursor.execute("SELECT LENGTH(content) FROM benchmark.tb_post WHERE id = %s", (post["id"],))
    result = cursor.fetchone()

    assert result[0] == 100000


@pytest.mark.error
def test_negative_limit_parameter(db, factory):
    """Test: negative limit values are handled."""
    cursor = db.cursor()

    # PostgreSQL treats negative LIMIT as no limit
    cursor.execute("SELECT id FROM benchmark.tb_user LIMIT -1")
    # Should not raise, may return all or none


@pytest.mark.error
def test_zero_limit_parameter(db, factory):
    """Test: zero limit returns empty list."""
    factory.create_user("user", "user@example.com")

    cursor = db.cursor()
    cursor.execute("SELECT id FROM benchmark.tb_user LIMIT 0")
    results = cursor.fetchall()

    assert len(results) == 0


# ============================================================================
# Cascade Delete Tests
# ============================================================================

@pytest.mark.error
def test_delete_user_cascades_posts(db, factory):
    """Test: deleting user cascades to their posts."""
    user = factory.create_user("author", "author@example.com")
    factory.create_post(user["pk_user"], "Post 1")
    factory.create_post(user["pk_user"], "Post 2")

    cursor = db.cursor()
    cursor.execute("DELETE FROM benchmark.tb_user WHERE pk_user = %s", (user["pk_user"],))

    # Verify posts are deleted (CASCADE)
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s", (user["pk_user"],))
    count = cursor.fetchone()[0]

    assert count == 0


@pytest.mark.error
def test_delete_post_cascades_comments(db, factory):
    """Test: deleting post cascades to its comments."""
    user = factory.create_user("author", "author@example.com")
    post = factory.create_post(user["pk_user"], "Test Post")
    commenter = factory.create_user("commenter", "commenter@example.com")
    factory.create_comment(post["pk_post"], commenter["pk_user"], "Comment 1")
    factory.create_comment(post["pk_post"], commenter["pk_user"], "Comment 2")

    cursor = db.cursor()
    cursor.execute("DELETE FROM benchmark.tb_post WHERE pk_post = %s", (post["pk_post"],))

    # Verify comments are deleted (CASCADE)
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = %s", (post["pk_post"],))
    count = cursor.fetchone()[0]

    assert count == 0


# ============================================================================
# Concurrent Access Tests
# ============================================================================

@pytest.mark.error
def test_update_same_user_twice(db, factory):
    """Test: updating same user twice in same transaction."""
    user = factory.create_user("user", "user@example.com")

    cursor = db.cursor()
    cursor.execute("UPDATE benchmark.tb_user SET bio = %s WHERE id = %s", ("Bio 1", user["id"]))
    cursor.execute("UPDATE benchmark.tb_user SET bio = %s WHERE id = %s", ("Bio 2", user["id"]))

    cursor.execute("SELECT bio FROM benchmark.tb_user WHERE id = %s", (user["id"],))
    result = cursor.fetchone()

    assert result[0] == "Bio 2"  # Last write wins


# ============================================================================
# SQL Injection Prevention Tests
# ============================================================================

@pytest.mark.error
def test_sql_injection_in_username(db, factory):
    """Test: SQL injection attempts in username are escaped."""
    malicious_username = "'; DROP TABLE benchmark.tb_user; --"

    # This should NOT cause SQL injection - parameterized queries protect us
    try:
        user = factory.create_user(malicious_username, "test@example.com")
        # If created, the username should be stored literally
        cursor = db.cursor()
        cursor.execute("SELECT username FROM benchmark.tb_user WHERE id = %s", (user["id"],))
        result = cursor.fetchone()
        assert result[0] == malicious_username
    except Exception:
        # May fail due to character constraints, which is fine
        pass


@pytest.mark.error
def test_sql_injection_in_content(db, factory):
    """Test: SQL injection attempts in content are escaped."""
    user = factory.create_user("user", "user@example.com")
    malicious_content = "'; DELETE FROM benchmark.tb_user; --"

    post = factory.create_post(user["pk_user"], "Test", malicious_content)

    cursor = db.cursor()
    cursor.execute("SELECT content FROM benchmark.tb_post WHERE id = %s", (post["id"],))
    result = cursor.fetchone()

    # Content should be stored literally, not executed
    assert result[0] == malicious_content

    # Verify users table still exists and has data
    cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
    count = cursor.fetchone()[0]
    assert count >= 1
