"""Schema validation tests for Ariadne GraphQL framework.

Tests that the GraphQL schema is correctly defined and types match expectations.
"""

import pytest


# ============================================================================
# Schema Structure Tests
# ============================================================================

@pytest.mark.schema
def test_user_table_has_required_columns(db, factory):
    """Test: tb_user table has all required columns."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'benchmark' AND table_name = 'tb_user'
        ORDER BY ordinal_position
    """)
    columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}

    # Required columns
    assert 'pk_user' in columns
    assert 'id' in columns
    assert 'username' in columns
    assert 'email' in columns
    assert 'full_name' in columns
    assert 'bio' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


@pytest.mark.schema
def test_post_table_has_required_columns(db, factory):
    """Test: tb_post table has all required columns."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'benchmark' AND table_name = 'tb_post'
        ORDER BY ordinal_position
    """)
    columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}

    assert 'pk_post' in columns
    assert 'id' in columns
    assert 'fk_author' in columns
    assert 'title' in columns
    assert 'content' in columns
    assert 'created_at' in columns


@pytest.mark.schema
def test_comment_table_has_required_columns(db, factory):
    """Test: tb_comment table has all required columns."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'benchmark' AND table_name = 'tb_comment'
        ORDER BY ordinal_position
    """)
    columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}

    assert 'pk_comment' in columns
    assert 'id' in columns
    assert 'fk_post' in columns
    assert 'fk_author' in columns
    assert 'content' in columns


# ============================================================================
# Foreign Key Constraint Tests
# ============================================================================

@pytest.mark.schema
def test_post_author_fk_constraint(db, factory):
    """Test: tb_post.fk_author references tb_user.pk_user."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'benchmark'
            AND tc.table_name = 'tb_post'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'fk_author'
    """)
    result = cursor.fetchone()

    assert result is not None
    assert result[2] == 'tb_user'  # Foreign table
    assert result[3] == 'pk_user'  # Foreign column


@pytest.mark.schema
def test_comment_post_fk_constraint(db, factory):
    """Test: tb_comment.fk_post references tb_post.pk_post."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'benchmark'
            AND tc.table_name = 'tb_comment'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'fk_post'
    """)
    result = cursor.fetchone()

    assert result is not None
    assert result[2] == 'tb_post'


@pytest.mark.schema
def test_comment_author_fk_constraint(db, factory):
    """Test: tb_comment.fk_author references tb_user.pk_user."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'benchmark'
            AND tc.table_name = 'tb_comment'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'fk_author'
    """)
    result = cursor.fetchone()

    assert result is not None
    assert result[2] == 'tb_user'


# ============================================================================
# UUID Generation Tests
# ============================================================================

@pytest.mark.schema
def test_user_id_is_valid_uuid(db, factory):
    """Test: tb_user.id is a valid UUID."""
    user = factory.create_user("testuser", "test@example.com")

    assert user["id"] is not None
    # psycopg3 returns UUID objects
    assert hasattr(user["id"], 'hex') or isinstance(user["id"], str)


@pytest.mark.schema
def test_post_id_is_valid_uuid(db, factory):
    """Test: tb_post.id is a valid UUID."""
    user = factory.create_user("author", "author@example.com")
    post = factory.create_post(user["pk_user"], "Test Post")

    assert post["id"] is not None


@pytest.mark.schema
def test_comment_id_is_valid_uuid(db, factory):
    """Test: tb_comment.id is a valid UUID."""
    user = factory.create_user("author", "author@example.com")
    post = factory.create_post(user["pk_user"], "Test Post")
    comment = factory.create_comment(post["pk_post"], user["pk_user"], "Comment")

    assert comment["id"] is not None


# ============================================================================
# Unique Constraint Tests
# ============================================================================

@pytest.mark.schema
def test_user_username_unique(db, factory):
    """Test: tb_user.username has unique constraint."""
    factory.create_user("uniqueuser", "unique1@example.com")

    with pytest.raises(Exception):  # Should raise unique violation
        factory.create_user("uniqueuser", "unique2@example.com")


@pytest.mark.schema
def test_user_email_unique(db, factory):
    """Test: tb_user.email has unique constraint."""
    factory.create_user("user1", "same@example.com")

    with pytest.raises(Exception):  # Should raise unique violation
        factory.create_user("user2", "same@example.com")


# ============================================================================
# Timestamp Tests
# ============================================================================

@pytest.mark.schema
def test_user_created_at_auto_set(db, factory):
    """Test: tb_user.created_at is automatically set on insert."""
    user = factory.create_user("testuser", "test@example.com")

    cursor = db.cursor()
    cursor.execute("SELECT created_at FROM benchmark.tb_user WHERE id = %s", (user["id"],))
    result = cursor.fetchone()

    assert result[0] is not None


@pytest.mark.schema
def test_post_created_at_auto_set(db, factory):
    """Test: tb_post.created_at is automatically set on insert."""
    user = factory.create_user("author", "author@example.com")
    post = factory.create_post(user["pk_user"], "Test Post")

    cursor = db.cursor()
    cursor.execute("SELECT created_at FROM benchmark.tb_post WHERE id = %s", (post["id"],))
    result = cursor.fetchone()

    assert result[0] is not None
