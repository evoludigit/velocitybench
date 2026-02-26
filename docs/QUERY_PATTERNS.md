# Query Patterns & Best Practices

## Overview

Common database query patterns used across VelocityBench frameworks. Agents can copy these patterns and adapt for specific needs.

---

## User Queries

### Get User by ID (Public API)
```sql
-- Use UUID id for public API queries
SELECT pk_user, id, username, email, first_name, last_name, bio, avatar_url, is_active, created_at, updated_at
FROM tb_user
WHERE id = $1;
```

**Python Example**:
```python
from uuid import UUID

async def get_user(db, user_id: str) -> dict:
    """Get user by UUID."""
    row = await db.fetch_one(
        """
        SELECT pk_user, id, username, email, first_name, last_name, bio, avatar_url, is_active, created_at, updated_at
        FROM tb_user
        WHERE id = $1
        """,
        UUID(user_id)
    )
    return row

# Usage:
user = await get_user(db, "550e8400-e29b-41d4-a716-446655440000")
```

---

### Get User by Username
```sql
-- Use username for login/authentication
SELECT pk_user, id, username, email, first_name, last_name, bio, avatar_url, is_active, created_at, updated_at
FROM tb_user
WHERE username = $1 AND is_active = true;
```

**Python Example**:
```python
async def get_user_by_username(db, username: str) -> dict:
    """Get user by username for login."""
    row = await db.fetch_one(
        """
        SELECT pk_user, id, username, email, first_name, last_name, bio, avatar_url, is_active, created_at, updated_at
        FROM tb_user
        WHERE username = $1 AND is_active = true
        """,
        username
    )
    return row
```

---

### List Users (Paginated)
```sql
-- Fetch paginated list of active users
SELECT pk_user, id, username, email, first_name, last_name, is_active, created_at
FROM tb_user
WHERE is_active = true
ORDER BY created_at DESC
LIMIT $1 OFFSET $2;
```

**Python Example**:
```python
async def list_users(db, skip: int = 0, limit: int = 20) -> list[dict]:
    """List users with pagination."""
    rows = await db.fetch_all(
        """
        SELECT pk_user, id, username, email, first_name, last_name, is_active, created_at
        FROM tb_user
        WHERE is_active = true
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit,
        skip
    )
    return rows

# Usage:
users = await list_users(db, skip=0, limit=20)
```

---

### Create User
```sql
-- Create new user, return complete record with generated UUID
INSERT INTO tb_user (username, email, first_name, last_name)
VALUES ($1, $2, $3, $4)
RETURNING pk_user, id, username, email, first_name, last_name, bio, avatar_url, is_active, created_at, updated_at;
```

**Python Example**:
```python
async def create_user(db, username: str, email: str, first_name: str = None, last_name: str = None) -> dict:
    """Create new user."""
    row = await db.fetch_one(
        """
        INSERT INTO tb_user (username, email, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        RETURNING pk_user, id, username, email, first_name, last_name, bio, avatar_url, is_active, created_at, updated_at
        """,
        username,
        email,
        first_name,
        last_name
    )
    return row
```

---

## Post Queries

### Get Post with Author
```sql
-- Include author information in post query
SELECT p.pk_post, p.id, p.title, p.content, p.excerpt, p.status, p.published_at, p.created_at, p.updated_at,
       u.pk_user as author_pk, u.id as author_id, u.username as author_username, u.email as author_email
FROM tb_post p
JOIN tb_user u ON p.fk_author = u.pk_user
WHERE p.id = $1;
```

**Python Example**:
```python
async def get_post_with_author(db, post_id: str) -> dict:
    """Get post with author information."""
    row = await db.fetch_one(
        """
        SELECT p.pk_post, p.id, p.title, p.content, p.excerpt, p.status, p.published_at, p.created_at, p.updated_at,
               u.pk_user as author_pk, u.id as author_id, u.username as author_username, u.email as author_email
        FROM tb_post p
        JOIN tb_user u ON p.fk_author = u.pk_user
        WHERE p.id = $1
        """,
        UUID(post_id)
    )
    return row
```

---

### List Posts by Author
```sql
-- Get all published posts by a user, newest first
SELECT pk_post, id, title, excerpt, status, published_at, created_at, updated_at
FROM tb_post
WHERE fk_author = (SELECT pk_user FROM tb_user WHERE id = $1)
  AND status = 'published'
ORDER BY published_at DESC
LIMIT $2 OFFSET $3;
```

**Python Example**:
```python
async def list_user_posts(db, user_id: str, skip: int = 0, limit: int = 20) -> list[dict]:
    """Get all published posts by user."""
    rows = await db.fetch_all(
        """
        SELECT pk_post, id, title, excerpt, status, published_at, created_at, updated_at
        FROM tb_post
        WHERE fk_author = (SELECT pk_user FROM tb_user WHERE id = $1)
          AND status = 'published'
        ORDER BY published_at DESC
        LIMIT $2 OFFSET $3
        """,
        UUID(user_id),
        limit,
        skip
    )
    return rows
```

---

### List All Published Posts
```sql
-- Get all published posts, newest first
SELECT p.pk_post, p.id, p.title, p.excerpt, p.published_at,
       u.id as author_id, u.username as author_username
FROM tb_post p
JOIN tb_user u ON p.fk_author = u.pk_user
WHERE p.status = 'published'
ORDER BY p.published_at DESC
LIMIT $1 OFFSET $2;
```

---

### Create Post
```sql
-- Create draft post, return with complete data
INSERT INTO tb_post (fk_author, title, content, excerpt, status)
VALUES ($1, $2, $3, $4, 'draft')
RETURNING pk_post, id, title, content, excerpt, status, published_at, created_at, updated_at;
```

**Python Example**:
```python
async def create_post(db, author_pk: int, title: str, content: str = None, excerpt: str = None) -> dict:
    """Create new draft post."""
    row = await db.fetch_one(
        """
        INSERT INTO tb_post (fk_author, title, content, excerpt, status)
        VALUES ($1, $2, $3, $4, 'draft')
        RETURNING pk_post, id, title, content, excerpt, status, published_at, created_at, updated_at
        """,
        author_pk,
        title,
        content,
        excerpt
    )
    return row
```

**Important**: Use `author_pk` (the SERIAL pk_user), NOT the UUID id!

---

### Publish Post
```sql
-- Change post status to published and set published_at timestamp
UPDATE tb_post
SET status = 'published', published_at = NOW(), updated_at = NOW()
WHERE id = $1
RETURNING pk_post, id, title, status, published_at, updated_at;
```

---

## Comment Queries

### Get Comments on Post
```sql
-- Get all approved comments on a post, newest first
SELECT c.pk_comment, c.id, c.content, c.is_approved, c.created_at,
       u.id as author_id, u.username as author_username
FROM tb_comment c
JOIN tb_user u ON c.fk_author = u.pk_user
WHERE c.fk_post = (SELECT pk_post FROM tb_post WHERE id = $1)
  AND c.is_approved = true
ORDER BY c.created_at DESC;
```

---

### Get Comment Replies (Nested)
```sql
-- Get replies to a specific comment
SELECT c.pk_comment, c.id, c.content, c.created_at,
       u.id as author_id, u.username as author_username
FROM tb_comment c
JOIN tb_user u ON c.fk_author = u.pk_user
WHERE c.fk_parent = (SELECT pk_comment FROM tb_comment WHERE id = $1)
ORDER BY c.created_at ASC;
```

---

### Create Comment
```sql
-- Create top-level comment (fk_parent is NULL)
INSERT INTO tb_comment (fk_post, fk_author, content, is_approved)
VALUES ($1, $2, $3, true)
RETURNING pk_comment, id, content, is_approved, created_at;
```

**Python Example**:
```python
async def create_comment(db, post_pk: int, author_pk: int, content: str) -> dict:
    """Create comment on post."""
    row = await db.fetch_one(
        """
        INSERT INTO tb_comment (fk_post, fk_author, content, is_approved)
        VALUES ($1, $2, $3, true)
        RETURNING pk_comment, id, content, is_approved, created_at
        """,
        post_pk,
        author_pk,
        content
    )
    return row
```

---

### Create Reply
```sql
-- Create reply to existing comment
INSERT INTO tb_comment (fk_post, fk_author, fk_parent, content, is_approved)
VALUES ($1, $2, $3, $4, true)
RETURNING pk_comment, id, content, is_approved, created_at;
```

**Python Example**:
```python
async def create_reply(db, post_pk: int, author_pk: int, parent_pk: int, content: str) -> dict:
    """Create reply to comment."""
    row = await db.fetch_one(
        """
        INSERT INTO tb_comment (fk_post, fk_author, fk_parent, content, is_approved)
        VALUES ($1, $2, $3, $4, true)
        RETURNING pk_comment, id, content, is_approved, created_at
        """,
        post_pk,
        author_pk,
        parent_pk,
        content
    )
    return row
```

---

## Complex Queries

### User with Posts and Comments
```sql
-- Full user data hierarchy
SELECT
    u.pk_user, u.id, u.username, u.email,
    p.pk_post, p.id as post_id, p.title, p.status,
    c.pk_comment, c.id as comment_id, c.content,
    cu.id as commenter_id, cu.username as commenter_name
FROM tb_user u
LEFT JOIN tb_post p ON u.pk_user = p.fk_author
LEFT JOIN tb_comment c ON p.pk_post = c.fk_post
LEFT JOIN tb_user cu ON c.fk_author = cu.pk_user
WHERE u.id = $1
ORDER BY p.created_at DESC, c.created_at ASC;
```

**Processing (Denormalize Results)**:
```python
def denormalize_user_hierarchy(rows):
    """Convert flat result set into nested structure."""
    user_data = {}
    posts_map = {}

    for row in rows:
        # Add user if new
        if row['pk_user'] not in user_data:
            user_data[row['pk_user']] = {
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'posts': []
            }

        user = user_data[row['pk_user']]

        # Add post if new
        if row['pk_post'] and row['pk_post'] not in posts_map:
            post = {
                'id': row['post_id'],
                'title': row['title'],
                'status': row['status'],
                'comments': []
            }
            user['posts'].append(post)
            posts_map[row['pk_post']] = post

        # Add comment if present
        if row['pk_comment'] and row['pk_post']:
            post = posts_map[row['pk_post']]
            post['comments'].append({
                'id': row['comment_id'],
                'content': row['content'],
                'author': row['commenter_name']
            })

    return list(user_data.values())[0]  # Return single user
```

---

## Performance Optimization Patterns

### Batch Inserts (Much Faster)
```python
# ❌ SLOW: 100 separate queries
for i in range(100):
    await create_user(db, f"user{i}", f"user{i}@example.com")

# ✅ FAST: Single batch insert
async def bulk_create_users(db, users: list[tuple]) -> int:
    """Create multiple users in single query."""
    query = "INSERT INTO tb_user (username, email) VALUES " + \
            ", ".join([f"(${i*2+1}, ${i*2+2})" for i in range(len(users))])

    flat_args = [item for user in users for item in user]
    result = await db.execute(query, *flat_args)
    return result

# Usage:
users = [("alice", "alice@example.com"), ("bob", "bob@example.com")]
await bulk_create_users(db, users)
```

---

### Selective Field Selection
```python
# ❌ SLOW: Fetch all fields
SELECT * FROM tb_post LIMIT 1000

# ✅ FAST: Only needed fields
SELECT pk_post, id, title, created_at FROM tb_post LIMIT 1000
```

---

### Indexed Filtering
```python
# Ensure queries use indexed columns
-- Status + date combo (should have index)
SELECT * FROM tb_post
WHERE status = 'published'
ORDER BY published_at DESC
LIMIT 20;

-- Username (unique, automatically indexed)
SELECT * FROM tb_user
WHERE username = 'alice';
```

---

## Anti-Patterns (Don't Do These)

### ❌ SELECT * with Many Joins
```sql
-- INEFFICIENT: Fetches all columns from all tables
SELECT *
FROM tb_post p
JOIN tb_user u ON p.fk_author = u.pk_user
JOIN tb_comment c ON p.pk_post = c.fk_post
LIMIT 100;
```

### ✅ Explicit Field Selection
```sql
-- EFFICIENT: Only needed fields
SELECT p.id, p.title, u.username, COUNT(c.pk_comment) as comment_count
FROM tb_post p
JOIN tb_user u ON p.fk_author = u.pk_user
LEFT JOIN tb_comment c ON p.pk_post = c.fk_post
GROUP BY p.id, p.title, u.username;
```

---

### ❌ N+1 Queries (Loop with Subquery)
```python
# SLOW: 100 queries
posts = await db.fetch_all("SELECT * FROM tb_post LIMIT 100")
for post in posts:
    author = await db.fetch_one("SELECT * FROM tb_user WHERE pk_user = %s",
                               post['fk_author'])
    post['author'] = author  # 100+ queries!
```

### ✅ Single Query with Join
```python
# FAST: 1 query
posts = await db.fetch_all("""
    SELECT p.*, u.username as author_username
    FROM tb_post p
    JOIN tb_user u ON p.fk_author = u.pk_user
    LIMIT 100
""")
```

---

### ❌ Missing WHERE Clause
```sql
-- DANGEROUS: Deletes all records!
DELETE FROM tb_post;

-- DANGEROUS: Updates all records!
UPDATE tb_user SET bio = 'new bio';
```

### ✅ Specific WHERE Clause
```sql
-- SAFE: Only specific record
DELETE FROM tb_post WHERE id = $1;

-- SAFE: Only specific record
UPDATE tb_user SET bio = $1 WHERE id = $2;
```

---

## Testing Query Patterns

### Verify Query Returns Expected Data
```python
def test_get_user_by_id(db, factory):
    """Verify get_user returns correct user."""
    user = factory.create_user("alice", "alice@example.com")

    result = db.fetch_one(
        "SELECT * FROM tb_user WHERE id = $1",
        user['id']
    )

    assert result['username'] == "alice"
    assert result['email'] == "alice@example.com"
```

---

### Verify Query Respects Filters
```python
def test_list_published_posts_only(db, factory):
    """Verify published posts query excludes drafts."""
    author = factory.create_user("alice", "alice@example.com")

    # Create mix of drafts and published
    draft = factory.create_post(fk_author=author['pk_user'], title="Draft", status='draft')
    published = factory.create_post(fk_author=author['pk_user'], title="Published", status='published')

    # Query only published
    results = db.fetch_all(
        "SELECT * FROM tb_post WHERE status = 'published' ORDER BY created_at DESC"
    )

    post_ids = [r['id'] for r in results]
    assert published['id'] in post_ids
    assert draft['id'] not in post_ids
```

---

### Verify JOIN Completeness
```python
def test_post_with_author_join_includes_author(db, factory):
    """Verify post+author join includes all author fields."""
    author = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(fk_author=author['pk_user'], title="Post")

    result = db.fetch_one("""
        SELECT p.*, u.username as author_username, u.email as author_email
        FROM tb_post p
        JOIN tb_user u ON p.fk_author = u.pk_user
        WHERE p.id = %s
    """, post['id'])

    assert result['author_username'] == "alice"
    assert result['author_email'] == "alice@example.com"
```

---

## Related Documentation

- **Database Schema**: `docs/DATABASE_SCHEMA.md` - Field definitions and constraints
- **Codebase Navigation**: `docs/CODEBASE_NAVIGATION.md` - Code patterns section
- **Testing**: `docs/TESTING_README.md` - Running tests with queries
- **Performance Baselines**: `docs/PERFORMANCE_BASELINE_MANAGEMENT.md` - Measuring query performance

