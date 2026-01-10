# FraiseQL Architecture: Three-Layer View System

**Version**: 1.8.1
**Date**: 2026-01-10
**Status**: ✅ Implemented and integrated with Trinity Pattern

## Overview

FraiseQL is a modern GraphQL server that leverages **pre-composed JSONB views** for efficient nested query resolution. Unlike traditional GraphQL resolvers that suffer from N+1 query problems, FraiseQL's architecture composes all nested objects at the database layer, enabling:

- **Zero N+1 queries** - All data fetched in single query
- **Database-level denormalization** - Complex objects pre-composed as JSONB
- **Efficient nested queries** - Nested objects included by default
- **Strong type safety** - Python dataclasses mapped to JSONB structure

## Architecture Layers

### Layer 1: Write Layer (tb_* Tables)

**Purpose**: Internal database optimization using Trinity Pattern

**Tables**:
- `tb_user` - Core user data
- `tb_post` - Post content with author relationship
- `tb_comment` - Nested comments with post, author, and parent relationships

**Key Pattern**:
```sql
CREATE TABLE tb_post (
    pk_post SERIAL PRIMARY KEY,           -- Internal PK (fast joins)
    id UUID UNIQUE NOT NULL,              -- Public identifier (API exposure)
    fk_author INTEGER NOT NULL,           -- Internal FK (hidden from API)
    title VARCHAR(500) NOT NULL,
    content TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Design Principles**:
- `pk_*` (SERIAL INT) - Internal primary keys, 5-10x faster than UUIDs for joins
- `id` (UUID) - Public identifiers exposed in API/GraphQL
- `fk_*` (INTEGER) - Internal foreign keys referencing `pk_*` columns
- Server manages `created_at`, `updated_at` timestamps

### Layer 2: Projection Layer (v_* Views)

**Purpose**: Extract scalar fields from tb_* tables, prepare for composition

**Views**:
- `v_user` - User scalar fields
- `v_post` - Post scalar fields with `fk_author` for joining
- `v_comment` - Comment scalar fields with `fk_post`, `fk_author`, `fk_parent`

**Key Pattern**:
```sql
CREATE OR REPLACE VIEW v_user AS
SELECT
    u.pk_user,          -- Keep for internal joining in composition layer
    u.id,               -- Public UUID identifier
    u.username,
    u.email,
    u.first_name,       -- snake_case in database
    u.last_name,
    u.bio,
    u.avatar_url,
    u.is_active,
    u.created_at,
    u.updated_at
FROM benchmark.tb_user u;

CREATE OR REPLACE VIEW v_post AS
SELECT
    p.pk_post,
    p.id,
    p.fk_author,        -- Keep for joining to author in composition
    p.title,
    p.content,
    p.excerpt,
    p.status,
    p.published_at,
    p.created_at,
    p.updated_at
FROM benchmark.tb_post p;
```

**Purpose of v_* Layer**:
- Hides `pk_*` columns from application code
- Maintains `fk_*` columns for composition joins
- Provides single source of truth for scalar field mapping
- Enables reuse in multiple composition views

### Layer 3: Composition Layer (tv_* Views)

**Purpose**: Build complete JSONB objects with recursive nesting

**Views**:
- `tv_user` - User JSONB with all fields in camelCase
- `tv_post` - Post JSONB with nested author object
- `tv_comment` - Comment JSONB with nested author, post, and parentComment objects

**Key Pattern: tv_user**
```sql
CREATE OR REPLACE VIEW tv_user AS
SELECT
    u.id,
    jsonb_build_object(
        'id', u.id,
        'username', u.username,
        'email', u.email,
        'firstName', u.first_name,      -- snake_case → camelCase in JSONB
        'lastName', u.last_name,
        'bio', u.bio,
        'avatarUrl', u.avatar_url,
        'isActive', u.is_active,
        'createdAt', u.created_at,
        'updatedAt', u.updated_at
    ) as data
FROM v_user u;
```

**Key Pattern: tv_post with Nested Author**
```sql
CREATE OR REPLACE VIEW tv_post AS
SELECT
    p.id,
    p.fk_author,
    jsonb_build_object(
        'id', p.id,
        'title', p.title,
        'content', p.content,
        'excerpt', p.excerpt,
        'status', p.status,
        'publishedAt', p.published_at,
        'createdAt', p.created_at,
        'updatedAt', p.updated_at,
        'author', COALESCE(
            -- Recursively compose author from tv_user
            (SELECT u.data FROM tv_user u WHERE u.id = (
                SELECT id FROM v_user WHERE pk_user = p.fk_author
            )),
            jsonb_null()
        )
    ) as data
FROM v_post p;
```

**Key Pattern: tv_comment with Multiple Nested Objects**
```sql
CREATE OR REPLACE VIEW tv_comment AS
SELECT
    c.id,
    c.fk_post,
    c.fk_author,
    c.fk_parent,
    jsonb_build_object(
        'id', c.id,
        'content', c.content,
        'isApproved', c.is_approved,
        'createdAt', c.created_at,
        'updatedAt', c.updated_at,
        'author', COALESCE(
            (SELECT u.data FROM tv_user u WHERE u.id = (
                SELECT id FROM v_user WHERE pk_user = c.fk_author
            )),
            jsonb_null()
        ),
        'post', COALESCE(
            (SELECT p.data FROM tv_post p WHERE p.id = (
                SELECT id FROM v_post WHERE pk_post = c.fk_post
            )),
            jsonb_null()
        ),
        'parentComment', CASE
            WHEN c.fk_parent IS NOT NULL THEN COALESCE(
                (SELECT tc.data FROM tv_comment tc WHERE tc.id = (
                    SELECT id FROM v_comment WHERE pk_comment = c.fk_parent
                )),
                jsonb_null()
            )
            ELSE null::jsonb
        END
    ) as data
FROM v_comment c;
```

**Design Principles**:
- Each `tv_*` view provides single `data` JSONB field
- JSONB field contains all composite object data with nested children
- Field names use camelCase for GraphQL compatibility
- Recursive composition allows deeply nested queries without N+1
- NULL handling with `COALESCE(..., jsonb_null())` for missing relations

## Data Flow: From Database to GraphQL

### Example Query: Get Post with Author

**User's GraphQL Query**:
```graphql
query {
  post(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    title
    author {
      id
      username
    }
  }
}
```

**FraiseQL Processing**:

1. **Parse GraphQL** - FraiseQL validates requested fields
2. **Query tv_post** - Single database query:
   ```sql
   SELECT id, data FROM benchmark.tv_post
   WHERE id = '550e8400-e29b-41d4-a716-446655440000'
   ```
3. **Result** - Single row with complete JSONB:
   ```json
   {
     "id": "550e8400-e29b-41d4-a716-446655440000",
     "data": {
       "id": "550e8400-e29b-41d4-a716-446655440000",
       "title": "First Post",
       "content": "...",
       "author": {
         "id": "550e8400-e29b-41d4-a716-446655440001",
         "username": "alice",
         "email": "alice@example.com",
         "firstName": "Alice",
         "lastName": "Smith",
         ...
       }
     }
   }
   ```
4. **Deserialize** - FraiseQL extracts requested fields from JSONB
5. **Return** - GraphQL response:
   ```json
   {
     "data": {
       "post": {
         "id": "550e8400-e29b-41d4-a716-446655440000",
         "title": "First Post",
         "author": {
           "id": "550e8400-e29b-41d4-a716-446655440001",
           "username": "alice"
         }
       }
     }
   }
   ```

**Key Insight**: Complete author object was fetched in single database query via JSONB composition, not separate queries.

## FraiseQL Type Mapping

### Type Definitions (main.py)

```python
@fraiseql.type(sql_source="benchmark.tv_user")
class User:
    """Maps to tv_user view's JSONB 'data' field."""
    id: UUID
    username: str
    email: str
    first_name: str | None = None      # snake_case maps to DB field names
    last_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    created_at: str
    updated_at: str


@fraiseql.type(sql_source="benchmark.tv_post")
class Post:
    """Maps to tv_post view's JSONB 'data' field with nested author."""
    id: UUID
    title: str
    content: str | None = None
    excerpt: str | None = None
    status: str = "published"
    published_at: str | None = None
    created_at: str
    updated_at: str
    author: User  # Pre-composed in tv_post.data.author


@fraiseql.type(sql_source="benchmark.tv_comment")
class Comment:
    """Maps to tv_comment view's JSONB 'data' field with nested objects."""
    id: UUID
    content: str
    is_approved: bool = True
    created_at: str
    updated_at: str
    author: User
    post: Post
    parent_comment: "Comment | None" = None
```

**Mapping Rules**:
- Python field names use snake_case (matches database)
- FraiseQL with `auto_camel_case=True` converts to camelCase in GraphQL schema
- Nested objects (author, post) are deserialized from JSONB automatically
- Optional fields use `| None` with defaults
- All required fields must have values in JSONB

### Configuration

```python
def create_fraiseql_config() -> FraiseQLConfig:
    return FraiseQLConfig(
        database_url="postgresql://...",
        default_query_schema="benchmark",      # Query schema where views live
        default_mutation_schema="benchmark",   # Mutation schema where tb_* tables live
        auto_camel_case=True,                  # Convert snake_case to camelCase
        database_pool_size=20,
        database_max_overflow=10,
        max_query_depth=10,
    )
```

## Queries and Mutations

### Queries (Read Operations)

**All queries use tv_* composition views**:

```python
@fraiseql.query
async def user(info: GraphQLResolveInfo, id: str) -> User | None:
    """Get user by UUID id - queries tv_user view."""
    db = info.context["db"]
    return await db.find_one("benchmark.tv_user", id=id)

@fraiseql.query
async def posts(info: GraphQLResolveInfo, limit: int = 10) -> list[Post]:
    """Get posts list - each includes pre-composed author object."""
    db = info.context["db"]
    return await db.find("benchmark.tv_post", limit=limit,
                         order_by=[{"created_at": "DESC"}])

@fraiseql.query
async def comments(info: GraphQLResolveInfo, limit: int = 10) -> list[Comment]:
    """Get comments list - each includes author, post, and parent comment objects."""
    db = info.context["db"]
    return await db.find("benchmark.tv_comment", limit=limit,
                         order_by=[{"created_at": "DESC"}])
```

### Mutations (Write Operations)

**Mutations write to tb_* tables, return via tv_* views**:

```python
@fraiseql.mutation
async def update_user(
    info: GraphQLResolveInfo,
    id: str,
    first_name: str | None = None,
    bio: str | None = None,
) -> User | None:
    """Update user - modifies tb_user, returns via tv_user composition."""
    db = info.context["db"]

    # Update write layer
    await db.update("benchmark.tb_user", where={"id": {"eq": id}},
                    data={"first_name": first_name, "bio": bio})

    # Return via composition layer
    return await db.find_one("benchmark.tv_user", id=id)

@fraiseql.mutation
async def create_post(
    info: GraphQLResolveInfo,
    author_id: str,
    title: str,
    content: str | None = None,
) -> Post | None:
    """Create post - inserts into tb_post, returns via tv_post composition."""
    db = info.context["db"]

    # Insert into write layer
    result = await db.insert("benchmark.tb_post",
                            data={"author_id": author_id, "title": title, "content": content})

    # Return via composition layer
    if result:
        return await db.find_one("benchmark.tv_post", id=result["id"])
    return None
```

**Key Points**:
- Mutations use UUID `id` fields (never expose `pk_*` or `fk_*`)
- Write operations target `tb_*` tables directly
- Return values queried via `tv_*` views to include all composed data
- All mutations are atomic - single INSERT/UPDATE operation

## Performance Characteristics

### Benefits of Three-Layer Architecture

| Characteristic | Benefit |
|---|---|
| **N+1 Query Elimination** | No separate resolver calls for nested objects - all composed in view |
| **Denormalization Efficiency** | JSONB composition happens once per cache TTL, not per request |
| **Integer FK Performance** | Internal `fk_*` → `pk_*` joins are 5-10x faster than UUID joins |
| **Network Efficiency** | JSONB returned as single blob, no separate network roundtrips |
| **Caching Friendly** | Entire objects can be cached at query layer |

### Indexes for Performance

```sql
-- Index on v_* views for FK joins in composition
CREATE INDEX idx_v_post_fk_author ON v_post(fk_author);
CREATE INDEX idx_v_comment_fk_post ON v_comment(fk_post);
CREATE INDEX idx_v_comment_fk_author ON v_comment(fk_author);
CREATE INDEX idx_v_comment_fk_parent ON v_comment(fk_parent);

-- Index on tv_* views for GraphQL lookups
CREATE INDEX idx_tv_user_id ON tv_user(id);
CREATE INDEX idx_tv_post_id ON tv_post(id);
CREATE INDEX idx_tv_post_fk_author ON tv_post(fk_author);
CREATE INDEX idx_tv_comment_id ON tv_comment(id);
CREATE INDEX idx_tv_comment_fk_post ON tv_comment(fk_post);
CREATE INDEX idx_tv_comment_fk_author ON tv_comment(fk_author);
CREATE INDEX idx_tv_comment_fk_parent ON tv_comment(fk_parent);

-- JSONB indexes for complex filtering
CREATE INDEX idx_tv_user_data ON tv_user USING GIN (data);
CREATE INDEX idx_tv_post_data ON tv_post USING GIN (data);
CREATE INDEX idx_tv_comment_data ON tv_comment USING GIN (data);
```

## Integration with Trinity Pattern

The three-layer view system works seamlessly with the Trinity Pattern:

```
┌─────────────────────────────────────────────────┐
│ LAYER 1: TRINITY PATTERN (tb_* tables)         │
│ - pk_user, pk_post, pk_comment (SERIAL INT)    │
│ - id (UUID) - public identifiers                │
│ - fk_author, fk_post, fk_parent (INT FK)       │
├─────────────────────────────────────────────────┤
│ LAYER 2: PROJECTION (v_* views)                 │
│ - Extract scalars from tb_*                     │
│ - Expose pk_*/id but keep fk_* hidden          │
│ - Serve as source for composition              │
├─────────────────────────────────────────────────┤
│ LAYER 3: COMPOSITION (tv_* views)               │
│ - Build JSONB with camelCase fields            │
│ - Recursively compose nested objects           │
│ - Exposed to FraiseQL GraphQL                   │
├─────────────────────────────────────────────────┤
│ FRAISEQL APPLICATION LAYER                     │
│ - Maps @fraiseql.type to tv_* views            │
│ - Deserializes JSONB to Python dataclasses    │
│ - Executes GraphQL queries efficiently        │
└─────────────────────────────────────────────────┘
```

## Summary

FraiseQL's three-layer view architecture provides:

✅ **Zero N+1 queries** through database-level composition
✅ **High performance** using integer PK/FK joins and JSONB pre-composition
✅ **Clean API boundaries** with UUID identifiers and hidden internal keys
✅ **Type safety** through Python dataclasses mapped to views
✅ **GraphQL-native** structure with camelCase field naming
✅ **Scalability** with efficient indexes on all view layers

This makes FraiseQL ideal for benchmarking GraphQL performance against other frameworks in the VelocityBench suite.
