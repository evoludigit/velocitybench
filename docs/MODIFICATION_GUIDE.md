# Code Modification Guide

## Overview

Step-by-step patterns for agents to follow when modifying VelocityBench code. Each pattern includes checklist and examples.

---

## Adding a New API Endpoint

### Pattern Overview

Adding an endpoint to all frameworks involves 5 steps:

1. **Define operation** - What data? What transformation?
2. **Update database** - Add schema/fields if needed
3. **Implement in Python frameworks** - FastAPI, Flask, GraphQL
4. **Implement in other frameworks** - Node, Go, etc. (as applicable)
5. **Add tests** - Cross-framework coverage

### Step-by-Step Example: Add "List Posts by Category"

#### Step 1: Define the Operation

```
Operation: List all posts in a category
Method: GET /categories/{category_slug}/posts
Parameters: category_slug (string), skip (int), limit (int)
Response: Array of Post objects (with author, no comments)
Sorting: By published_at DESC (newest first)
Filtering: Only published posts, only approved categories
```

#### Step 2: Update Database (If Needed)

**Check existing schema** (already have post_categories table):
```bash
grep -r "post_categories" database/schema-template.sql
# Found: post_categories junction table exists
```

**No schema changes needed!** ✅

#### Step 3: Implement in FastAPI

**Location**: `frameworks/fastapi-rest/main.py`

**Add model**:
```python
class CategoryPostsResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    posts: list[PostResponse]
```

**Add endpoint**:
```python
@app.get("/categories/{category_slug}/posts")
async def list_posts_by_category(
    category_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List published posts in category."""
    try:
        rows = await db.fetch_all(
            """
            SELECT DISTINCT p.id, p.title, p.content, p.status, p.published_at,
                   u.id as author_id, u.username as author_username
            FROM tb_post p
            JOIN tb_user u ON p.fk_author = u.pk_user
            JOIN post_categories pc ON p.id = pc.post_id
            JOIN categories c ON pc.category_id = c.id
            WHERE c.slug = $1 AND p.status = 'published'
            ORDER BY p.published_at DESC
            LIMIT $2 OFFSET $3
            """,
            category_slug,
            limit,
            skip
        )
        return [PostResponse(**row) for row in rows]
    except Exception as e:
        logger.error(f"Error listing posts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Testing**:
```bash
cd frameworks/fastapi-rest
pytest tests/test_categories.py::test_list_posts_by_category -v
```

#### Step 4: Implement in Strawberry GraphQL

**Location**: `frameworks/strawberry/main.py`

**Add query**:
```python
@strawberry.type
class Query:
    @strawberry.field
    async def category_posts(
        self,
        slug: str,
        skip: int = 0,
        limit: int = 20
    ) -> list[Post]:
        """List published posts in category."""
        rows = await db.fetch_all(
            """
            SELECT DISTINCT p.*, u.id as author_id, u.username
            FROM tb_post p
            JOIN tb_user u ON p.fk_author = u.pk_user
            JOIN post_categories pc ON p.id = pc.post_id
            JOIN categories c ON pc.category_id = c.id
            WHERE c.slug = $1 AND p.status = 'published'
            ORDER BY p.published_at DESC
            LIMIT $2 OFFSET $3
            """,
            slug,
            limit,
            skip
        )
        return [Post(**row) for row in rows]
```

**GraphQL Endpoint** (auto-exposed):
```graphql
query {
  categoryPosts(slug: "python-tutorials", skip: 0, limit: 20) {
    id
    title
    publishedAt
    author {
      username
    }
  }
}
```

#### Step 5: Add Cross-Framework Tests

**Location**: `tests/qa/test_categories.py`

```python
import pytest
from tests.common.fixtures import db, factory

def test_list_posts_by_category_shows_published_only(db, factory):
    """List posts by category shows only published posts."""
    # Create test data
    author = factory.create_user("alice", "alice@example.com")

    # Create category
    category = db.fetch_one(
        "INSERT INTO categories (name, slug) VALUES ($1, $2) RETURNING *",
        "Python Tutorials", "python-tutorials"
    )

    # Create posts
    published = factory.create_post(
        fk_author=author['pk_user'],
        title="Published Post",
        status='published'
    )
    draft = factory.create_post(
        fk_author=author['pk_user'],
        title="Draft Post",
        status='draft'
    )

    # Assign published post to category
    db.execute(
        "INSERT INTO post_categories (post_id, category_id) VALUES ($1, $2)",
        published['id'],
        category['id']
    )
    db.execute(
        "INSERT INTO post_categories (post_id, category_id) VALUES ($1, $2)",
        draft['id'],
        category['id']
    )

    # Test REST endpoint
    from frameworks.fastapi_rest.tests import client
    response = client.get(f"/categories/{category['slug']}/posts")
    assert response.status_code == 200
    post_ids = [p['id'] for p in response.json()]
    assert str(published['id']) in post_ids
    assert str(draft['id']) not in post_ids

    # Test GraphQL endpoint
    from frameworks.strawberry.tests import client as gql_client
    query = f"""
    query {{
      categoryPosts(slug: "{category['slug']}") {{
        id
        title
      }}
    }}
    """
    response = gql_client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    posts = response.json()['data']['categoryPosts']
    post_ids = [p['id'] for p in posts]
    assert str(published['id']) in post_ids
    assert str(draft['id']) not in post_ids
```

**Run tests**:
```bash
cd tests/qa
pytest test_categories.py -v
```

### Checklist for Adding Endpoint

- [ ] **Define** - Document operation clearly
- [ ] **Database** - Check/update schema if needed
- [ ] **FastAPI** - Add endpoint with type hints
- [ ] **Flask** - Add endpoint if applicable
- [ ] **Strawberry** - Add GraphQL query/mutation
- [ ] **Graphene** - Add GraphQL if applicable
- [ ] **Tests** - Add cross-framework test
- [ ] **Docs** - Update `docs/API_SCHEMAS.md`
- [ ] **Run tests** - `cd tests/qa && pytest -v`
- [ ] **Manual verification** - Test with cURL/GraphQL client

---

## Adding a Database Field

### Pattern Overview

1. **Add to schema** - Update schema-template.sql
2. **Update models** - Update ORM models in each framework
3. **Migration** - Create migration (optional)
4. **Update validation** - Add field constraints
5. **Update tests** - Add field to test fixtures

### Example: Add "archived_by" Field to Posts

#### Step 1: Update Schema

**Location**: `database/schema-template.sql`

```sql
-- BEFORE
CREATE TABLE tb_post (
    pk_post SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    excerpt VARCHAR(500),
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AFTER
CREATE TABLE tb_post (
    pk_post SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    excerpt VARCHAR(500),
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    published_at TIMESTAMP WITH TIME ZONE,
    archived_by INTEGER REFERENCES tb_user(pk_user) ON DELETE SET NULL,  -- NEW
    archived_at TIMESTAMP WITH TIME ZONE,  -- NEW
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Step 2: Update ORM Models

**FastAPI/Flask** (`frameworks/*/main.py`):
```python
class PostResponse(BaseModel):
    id: UUID
    title: str
    content: str | None
    excerpt: str | None
    status: str
    published_at: datetime | None
    archived_by: dict | None = None  # NEW
    archived_at: datetime | None = None  # NEW
    author: dict | None = None
    created_at: datetime
    updated_at: datetime
```

**Strawberry** (`frameworks/strawberry/main.py`):
```python
@strawberry.type
class Post:
    id: ID
    title: str
    content: str | None
    excerpt: str | None
    status: str
    published_at: datetime | None
    archived_by: User | None = None  # NEW
    archived_at: datetime | None = None  # NEW
    author: User
    created_at: datetime
    updated_at: datetime
```

#### Step 3: Create Migration (Optional)

**Location**: `database/migrations/001-add-archive-tracking.sql`

```sql
-- Migration: Add archive tracking to posts
-- Date: 2025-01-31
-- Description: Track who archived posts and when

ALTER TABLE tb_post ADD COLUMN archived_by INTEGER REFERENCES tb_user(pk_user) ON DELETE SET NULL;
ALTER TABLE tb_post ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE;

-- Index for finding archived posts
CREATE INDEX idx_post_archived_at ON tb_post(archived_at DESC) WHERE archived_at IS NOT NULL;
```

#### Step 4: Update Field Constraints

**Add to field validation** (in Pydantic models or GraphQL):
```python
class PostUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    archived_by_id: UUID | None = Field(None, description="UUID of user archiving post")
    # archived_at is auto-set to NOW()
```

#### Step 5: Update Tests

**Location**: `tests/common/bulk_factory.py`

```python
# Update factory to include new fields
def create_post(self, ..., archived_by_pk: int = None, archived_at: datetime = None):
    """Create post with optional archive info."""
    return self.db.fetch_one(
        """
        INSERT INTO tb_post (fk_author, title, ..., archived_by, archived_at)
        VALUES ($1, $2, ..., $3, $4)
        RETURNING *
        """,
        author_pk, title, ..., archived_by_pk, archived_at
    )
```

**Test the field**:
```python
def test_archive_post_tracks_who_archived(db, factory):
    """Archiving a post records who archived it."""
    author = factory.create_user("alice", "alice@example.com")
    admin = factory.create_user("admin", "admin@example.com")
    post = factory.create_post(fk_author=author['pk_user'], title="Post")

    # Archive post
    db.execute(
        "UPDATE tb_post SET status='archived', archived_by=%s, archived_at=NOW() WHERE id=%s",
        admin['pk_user'],
        post['id']
    )

    # Verify archival
    result = db.fetch_one("SELECT * FROM tb_post WHERE id=%s", post['id'])
    assert result['status'] == 'archived'
    assert result['archived_by'] == admin['pk_user']
    assert result['archived_at'] is not None
```

### Checklist for Adding Field

- [ ] **Schema** - Add column to schema-template.sql with proper type
- [ ] **Constraints** - Add CHECK/UNIQUE/FK constraints
- [ ] **Indexes** - Add index if field will be queried
- [ ] **Migration** - Create migration file if needed
- [ ] **Models** - Update all ORM/Pydantic models
- [ ] **Validation** - Add field validators
- [ ] **Tests** - Add test coverage for field
- [ ] **Documentation** - Update DATABASE_SCHEMA.md
- [ ] **Verify** - Run tests on all frameworks

---

## Fixing a Bug Across Frameworks

### Pattern

1. **Identify bug** - Which framework? Symptom?
2. **Isolate bug** - Minimal reproduction
3. **Fix in one framework** - Implement fix
4. **Check if shared code** - Is it in frameworks/common/?
5. **Apply to other frameworks** - Propagate fix
6. **Verify with tests** - Run full test suite

### Example: Fix N+1 Query in "Get Post with Comments"

#### Step 1: Identify Bug

**Symptom**: Endpoint slow when post has many comments

**Root cause** (after investigation):
```python
# ❌ WRONG: N+1 query
post = await get_post(db, post_id)
comments = []
for comment_id in comment_ids:
    comment = await get_comment(db, comment_id)  # Extra query per comment!
    comments.append(comment)
```

#### Step 2: Fix in FastAPI

**Location**: `frameworks/fastapi-rest/main.py`

```python
# ✅ FIXED: Single query with join
@app.get("/posts/{post_id}")
async def get_post(post_id: str, include_comments: bool = False):
    """Get post, optionally with comments."""
    query = """
        SELECT p.*, u.id as author_id, u.username as author_username
        FROM tb_post p
        JOIN tb_user u ON p.fk_author = u.pk_user
        WHERE p.id = $1
    """
    post = await db.fetch_one(query, UUID(post_id))

    if include_comments:
        # Single query for all comments
        comments = await db.fetch_all("""
            SELECT c.*, cu.id as author_id, cu.username as author_username
            FROM tb_comment c
            JOIN tb_user cu ON c.fk_author = cu.pk_user
            WHERE c.fk_post = %s
            ORDER BY c.created_at DESC
        """, post['pk_post'])
        post['comments'] = comments

    return post
```

#### Step 3: Check if Shared Code

```bash
grep -r "def get_post" frameworks/common/
# Not in shared code - check each framework
```

#### Step 4: Apply to Strawberry

**Location**: `frameworks/strawberry/main.py`

```python
@strawberry.type
class Query:
    @strawberry.field
    async def post(
        self,
        id: str,
        include_comments: bool = False
    ) -> Post | None:
        """Get post with optional comments."""
        # Same optimization as FastAPI
        post = await db.fetch_one("""
            SELECT p.*, u.id as author_id, u.username
            FROM tb_post p
            JOIN tb_user u ON p.fk_author = u.pk_user
            WHERE p.id = %s
        """, UUID(id))

        if include_comments and post:
            comments = await db.fetch_all("""
                SELECT c.*, cu.id as author_id, cu.username
                FROM tb_comment c
                JOIN tb_user cu ON c.fk_author = cu.pk_user
                WHERE c.fk_post = %s
                ORDER BY c.created_at DESC
            """, post['pk_post'])
            post['comments'] = comments

        return Post(**post) if post else None
```

#### Step 5: Test the Fix

```bash
# Test FastAPI
cd frameworks/fastapi-rest
pytest tests/test_posts.py::test_get_post_with_comments -v

# Test Strawberry
cd frameworks/strawberry
pytest tests/test_posts.py::test_get_post_with_comments -v

# Cross-framework test
cd tests/qa
pytest test_posts.py::test_get_post_with_comments_performance -v
```

---

## Modifying Configuration

### Pattern

1. **Add to .env.example** - Document new variable
2. **Add to config module** - Parse environment variable
3. **Update startup code** - Use new configuration
4. **Update documentation** - Explain in DEVELOPMENT.md
5. **Test with different values** - Verify behavior changes

### Example: Make Connection Pool Size Configurable

Already done in previous improvements! See:
- `.env.example` - DB_POOL_MIN_SIZE, DB_POOL_MAX_SIZE
- `frameworks/*/main.py` - Uses environment variables
- `frameworks/common/config.py` - Configuration parsing

---

## Writing Tests for New Features

### Pattern

1. **Test in isolation** - Single feature test
2. **Test with valid input** - Happy path
3. **Test with invalid input** - Error handling
4. **Test edge cases** - Empty results, max values, etc.
5. **Test across frameworks** - REST and GraphQL

### Example: Test New Category Listing

```python
import pytest
from tests.common.fixtures import db, factory

class TestCategories:
    """Test category operations."""

    def test_list_empty_categories_returns_empty_list(self, db):
        """Empty database returns empty categories list."""
        # REST
        response = client.get("/categories")
        assert response.status_code == 200
        assert response.json() == []

        # GraphQL
        response = gql_client.post("/graphql", json={
            "query": "query { categories { id name } }"
        })
        assert response.json()['data']['categories'] == []

    def test_list_categories_returns_all_categories(self, db):
        """Listing returns all categories."""
        # Create test data
        db.execute(
            "INSERT INTO categories (name, slug) VALUES (%s, %s)",
            "Python", "python"
        )
        db.execute(
            "INSERT INTO categories (name, slug) VALUES (%s, %s)",
            "JavaScript", "javascript"
        )

        # REST
        response = client.get("/categories")
        assert len(response.json()) == 2
        names = [c['name'] for c in response.json()]
        assert "Python" in names
        assert "JavaScript" in names

        # GraphQL
        response = gql_client.post("/graphql", json={
            "query": "query { categories { name } }"
        })
        categories = response.json()['data']['categories']
        assert len(categories) == 2

    @pytest.mark.parametrize("query", [
        "",      # Empty string
        None,    # Null
        "/"      # Special char
    ])
    def test_list_categories_with_invalid_query_returns_400(self, db, query):
        """Invalid query parameters return 400."""
        response = client.get(f"/categories?search={query}")
        assert response.status_code == 400
```

---

## Related Documentation

- **Query Patterns**: `docs/QUERY_PATTERNS.md` - SQL patterns for data operations
- **Error Catalog**: `docs/ERROR_CATALOG.md` - Common errors and solutions
- **Database Schema**: `docs/DATABASE_SCHEMA.md` - Field definitions
- **Codebase Navigation**: `docs/CODEBASE_NAVIGATION.md` - Where to find code
- **Testing**: `docs/TESTING_README.md` - Test infrastructure

