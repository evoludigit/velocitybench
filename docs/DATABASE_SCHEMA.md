# Database Schema Reference

## Overview

VelocityBench uses a unified **Trinity Pattern** schema across all 35+ frameworks. This design separates internal identifiers from public API identifiers, optimizing for both write efficiency and API usability.

---

## Trinity Pattern Explained

The Trinity Pattern uses three types of identifiers per entity:

| Identifier | Type | Purpose | Example |
|-----------|------|---------|---------|
| **pk_*** | SERIAL PRIMARY KEY | Internal, write-optimized | `pk_user = 1` |
| **id** | UUID UNIQUE | Public API identifier | `id = "550e8400-e29b-41d4-a716-446655440000"` |
| **fk_*** | INTEGER FK | Efficient relationships | `fk_author = 1` |

### Why This Pattern?

- **pk_*** (SERIAL): Fast, small, sequential integers for internal operations
- **id** (UUID): Public-safe, globally unique identifiers for API exposure
- **fk_*** (INTEGER): Efficient foreign key relationships using internal IDs

**Benefit**: Frameworks can optimize queries with small integers while APIs expose UUIDs, preventing ID guessing attacks and improving performance simultaneously.

---

## Core Tables

### `tb_user` - User Accounts

**Purpose**: Store user accounts and authentication data

**Schema**:
```sql
CREATE TABLE tb_user (
    pk_user SERIAL PRIMARY KEY,                    -- Internal ID (agent use this for FKs)
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),  -- Public API ID
    username VARCHAR(100) UNIQUE NOT NULL,         -- Login username
    email VARCHAR(255) UNIQUE NOT NULL,            -- Contact email (also unique)
    first_name VARCHAR(100),                       -- Optional: user first name
    last_name VARCHAR(100),                        -- Optional: user last name
    bio TEXT,                                      -- Optional: user biography
    avatar_url VARCHAR(500),                       -- Optional: profile picture URL
    is_active BOOLEAN DEFAULT true,                -- Account status
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Creation time (UTC)
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()   -- Last modification (UTC)
);
```

**Indexes**:
- `UNIQUE (id)` - Fast public API lookups
- `UNIQUE (username)` - Login validation
- `UNIQUE (email)` - Email uniqueness enforcement

**Constraints**:
- `username` must be 1-100 characters
- `email` must be valid email format (framework-specific validation)
- `is_active` controls account access (soft delete alternative)

**Usage Patterns**:
```sql
-- Agent: Find user by public ID (for API responses)
SELECT * FROM tb_user WHERE id = $1;

-- Agent: Find user by username (for login)
SELECT * FROM tb_user WHERE username = $1;

-- Agent: Create user with known pk_user
INSERT INTO tb_user (username, email, first_name, last_name)
VALUES ($1, $2, $3, $4)
RETURNING pk_user, id, username, email;
```

---

### `tb_post` - Blog Posts/Content

**Purpose**: Store user-created content (posts, articles, etc.)

**Schema**:
```sql
CREATE TABLE tb_post (
    pk_post SERIAL PRIMARY KEY,                    -- Internal ID
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),  -- Public API ID
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,  -- Author (use pk_user!)
    title VARCHAR(500) NOT NULL,                   -- Post title (required)
    content TEXT,                                  -- Post body (optional)
    excerpt VARCHAR(500),                          -- Summary/preview text
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),  -- Publication status
    published_at TIMESTAMP WITH TIME ZONE,        -- Null until published
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Creation time (UTC)
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()   -- Last modification (UTC)
);
```

**Indexes**:
- `UNIQUE (id)` - Fast public API lookups
- `INDEX (fk_author, created_at)` - Author's posts, newest first
- `INDEX (status, published_at)` - Published posts sorted by date

**Foreign Keys**:
- `fk_author → tb_user(pk_user)` with `ON DELETE CASCADE`
  - When user is deleted, all their posts are deleted
  - Always use `pk_user` for inserts, never `id`

**Constraints**:
- `title` must be 1-500 characters
- `status` must be one of: 'draft', 'published', 'archived'
- `published_at` is NULL for drafts, set when status becomes 'published'
- `excerpt` is optional but limited to 500 characters

**Usage Patterns**:
```sql
-- Agent: Get post with author info
SELECT p.*, u.username, u.id as author_id
FROM tb_post p
JOIN tb_user u ON p.fk_author = u.pk_user
WHERE p.id = $1;

-- Agent: Get all published posts by user (newest first)
SELECT p.* FROM tb_post p
WHERE p.fk_author = (SELECT pk_user FROM tb_user WHERE id = $1)
  AND p.status = 'published'
ORDER BY p.published_at DESC;

-- Agent: Create post (note: use pk_user for fk_author)
INSERT INTO tb_post (fk_author, title, content, status)
VALUES ($1, $2, $3, 'draft')
RETURNING pk_post, id, title;
```

---

### `tb_comment` - Comments on Posts

**Purpose**: Store user comments and replies on posts

**Schema**:
```sql
CREATE TABLE tb_comment (
    pk_comment SERIAL PRIMARY KEY,                 -- Internal ID
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),  -- Public API ID
    fk_post INTEGER NOT NULL REFERENCES tb_post(pk_post) ON DELETE CASCADE,   -- Parent post
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,  -- Comment author
    fk_parent INTEGER REFERENCES tb_comment(pk_comment) ON DELETE CASCADE,     -- Reply-to comment (optional)
    content TEXT NOT NULL,                         -- Comment text (required)
    is_approved BOOLEAN DEFAULT true,              -- Moderation flag
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Creation time (UTC)
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()   -- Last modification (UTC)
);
```

**Indexes**:
- `UNIQUE (id)` - Fast public API lookups
- `INDEX (fk_post, created_at)` - All comments on post, newest first
- `INDEX (fk_parent, created_at)` - Nested comments, newest first

**Foreign Keys**:
- `fk_post → tb_post(pk_post)` with `ON DELETE CASCADE` - Parent post
- `fk_author → tb_user(pk_user)` with `ON DELETE CASCADE` - Comment author
- `fk_parent → tb_comment(pk_comment)` with `ON DELETE CASCADE` - For nested comments (optional, NULL for top-level)

**Constraints**:
- `content` must be non-empty (1+ characters)
- `is_approved` controls visibility (soft delete for moderation)
- `fk_parent` is NULL for top-level comments, set for replies

**Nested Comment Behavior**:
- Top-level comment: `fk_parent = NULL`
- Reply to top-level: `fk_parent = pk_comment` of top-level comment
- Multi-level nesting supported (reply to a reply, etc.)

**Usage Patterns**:
```sql
-- Agent: Get all comments on a post (newest first)
SELECT c.*, u.username, u.id as author_id
FROM tb_comment c
JOIN tb_user u ON c.fk_author = u.pk_user
WHERE c.fk_post = (SELECT pk_post FROM tb_post WHERE id = $1)
  AND c.is_approved = true
ORDER BY c.created_at DESC;

-- Agent: Get replies to a specific comment
SELECT c.* FROM tb_comment c
WHERE c.fk_parent = (SELECT pk_comment FROM tb_comment WHERE id = $1)
ORDER BY c.created_at ASC;

-- Agent: Create top-level comment
INSERT INTO tb_comment (fk_post, fk_author, content)
VALUES ($1, $2, $3)
RETURNING id, content, created_at;

-- Agent: Create reply to comment (note fk_parent)
INSERT INTO tb_comment (fk_post, fk_author, fk_parent, content)
VALUES ($1, $2, $3, $4)
RETURNING id, content, created_at;
```

---

## Supporting Tables

### `categories` - Content Categories/Tags

**Purpose**: Organizational categories for posts

**Schema**:
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- No pk_*, UUID is primary
    name VARCHAR(100) UNIQUE NOT NULL,              -- Category name
    slug VARCHAR(100) UNIQUE NOT NULL,              -- URL-friendly slug
    description TEXT,                               -- Category description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Notes**:
- Unlike core tables, categories use UUID as primary key (no SERIAL)
- `slug` is for URL paths (e.g., "python-frameworks")
- `name` and `slug` must be unique

---

### `post_categories` - Many-to-Many Posts ↔ Categories

**Purpose**: Junction table for posts with multiple categories

**Schema**:
```sql
CREATE TABLE post_categories (
    post_id UUID NOT NULL REFERENCES tb_post(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, category_id)
);
```

**Notes**:
- Composite primary key on both IDs
- Cascade delete when post or category deleted
- Uses UUIDs (not pk_post/pk_comment) for consistency

**Usage Patterns**:
```sql
-- Agent: Get all categories for a post
SELECT c.* FROM categories c
JOIN post_categories pc ON c.id = pc.category_id
WHERE pc.post_id = $1;

-- Agent: Get all posts in a category
SELECT p.* FROM tb_post p
JOIN post_categories pc ON p.id = pc.post_id
WHERE pc.category_id = $1
ORDER BY p.published_at DESC;
```

---

### `user_follows` - Social Graph

**Purpose**: Track follower/following relationships between users

**Schema**:
```sql
CREATE TABLE user_follows (
    follower_id UUID NOT NULL REFERENCES tb_user(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES tb_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id != following_id)  -- User cannot follow themselves
);
```

**Constraints**:
- Composite primary key prevents duplicate follows
- `CHECK` constraint prevents self-follows
- Asymmetric: A follows B ≠ B follows A

**Usage Patterns**:
```sql
-- Agent: Get followers of a user
SELECT u.* FROM tb_user u
JOIN user_follows uf ON u.id = uf.follower_id
WHERE uf.following_id = $1;

-- Agent: Get users that a user is following
SELECT u.* FROM tb_user u
JOIN user_follows uf ON u.id = uf.following_id
WHERE uf.follower_id = $1;

-- Agent: Check if user A follows user B
SELECT 1 FROM user_follows
WHERE follower_id = $1 AND following_id = $2;
```

---

### `post_likes` - Reactions/Likes on Posts

**Purpose**: Track user reactions to posts

**Schema**:
```sql
CREATE TABLE post_likes (
    user_id UUID NOT NULL REFERENCES tb_user(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES tb_post(id) ON DELETE CASCADE,
    reaction_type VARCHAR(20) DEFAULT 'like' CHECK (reaction_type IN ('like', 'love', 'laugh', 'angry')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)
);
```

**Constraints**:
- One reaction per user per post (primary key enforces)
- `reaction_type` must be one of: 'like', 'love', 'laugh', 'angry'

**Usage Patterns**:
```sql
-- Agent: Get like count for a post
SELECT reaction_type, COUNT(*) as count
FROM post_likes
WHERE post_id = $1
GROUP BY reaction_type;

-- Agent: Get total likes (all reaction types)
SELECT COUNT(*) FROM post_likes WHERE post_id = $1;

-- Agent: Check if user liked a post
SELECT reaction_type FROM post_likes
WHERE user_id = $1 AND post_id = $2;
```

---

## Complete Entity Relationship Diagram

```
┌─────────────────────┐
│     tb_user         │
├─────────────────────┤
│ pk_user (PK)        │
│ id (UUID)           │  ──┐ (1)
│ username            │    │
│ email               │    │
│ first_name          │    │
│ last_name           │    │
│ bio                 │    │
│ avatar_url          │    │
│ is_active           │    │
│ created_at          │    │
│ updated_at          │    │
└─────────────────────┘    │
       ▲           ▲       │
       │           │       │
       │ (fk_author,fk_author) (many)
       │           │       │
       │    ┌──────┴───────┘
       │    │
       │    ▼
   ┌───────────────────────┐      ┌──────────────────────┐
   │     tb_post           │      │    categories        │
   ├───────────────────────┤      ├──────────────────────┤
   │ pk_post (PK)          │      │ id (UUID, PK)        │
   │ id (UUID)             │      │ name                 │
   │ fk_author (FK)        │      │ slug                 │
   │ title                 │      │ description          │
   │ content               │      │ created_at           │
   │ excerpt               │      │                      │
   │ status                │      └──────────────────────┘
   │ published_at          │               ▲
   │ created_at            │               │
   │ updated_at            │     (junction via post_categories)
   └───────────────────────┘               │
           │                               │
           │(fk_post)  ┌────────────────────┘
           │           │
           │     ┌─────────────────────────┐
           │     │  post_categories (M:M)  │
           │     │  post_id (UUID) ────────┼──┐
           │     │  category_id (UUID) ────┴──┤
           │     └─────────────────────────┘   │
           │                                   │
           ▼                                   │
   ┌─────────────────────┐                    │
   │   tb_comment        │                    │
   ├─────────────────────┤                    │
   │ pk_comment (PK)     │                    │
   │ id (UUID)           │                    │
   │ fk_post (FK) ───────┼────────────────────┤
   │ fk_author (FK) ─────┼─────────┐          │
   │ fk_parent (FK) ─────┼─────┐   │          │
   │ content             │     │   │          │
   │ is_approved         │     │   │          │
   │ created_at          │     │   │          │
   │ updated_at          │     │   │          │
   └─────────────────────┘     │   │          │
           ▲                    └───┤──────────┤
           │                        │          │
      (self-ref)               (user)  (category)
      (fk_parent)

Social Graph:
┌──────────────────────────────┐
│    user_follows              │
│    follower_id  ─────────┐   │
│    following_id ──────┐  │   │
└──────────────────────────────┘
                     │  │
              ┌──────┘  └──────┐
              │                 │
              ▼                 ▼
         tb_user (follower)  tb_user (following)

Post Reactions:
┌──────────────────────────────┐
│     post_likes               │
│     user_id  ───────┐        │
│     post_id  ─────┐ │        │
│     reaction_type │ │        │
└──────────────────────────────┘
             │     │
          ┌──┘     └──┐
          │            │
          ▼            ▼
       tb_user      tb_post
```

---

## Data Consistency Rules

### Cascading Deletes

When a record is deleted, related records cascade:

| When deleted | Cascades to | Behavior |
|-------------|----------|----------|
| `tb_user` | `tb_post` (fk_author) | All posts by user deleted |
| `tb_user` | `tb_comment` (fk_author) | All comments by user deleted |
| `tb_post` | `tb_comment` (fk_post) | All comments on post deleted |
| `tb_comment` | `tb_comment` (fk_parent) | All nested replies deleted |
| `tb_post` | `post_categories` | All category assignments removed |
| `categories` | `post_categories` | All posts in category unassigned |

**Agent Implication**: Deleting a user deletes all their content and comments. Plan deletions carefully.

---

## Timestamp Handling

All timestamps are in **UTC with timezone** (`TIMESTAMP WITH TIME ZONE`):

```sql
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  -- UTC current time
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  -- UTC current time
```

**For Agents**:
- Always store timestamps in UTC
- Don't assume local timezone
- Update `updated_at` on any record modification
- Use `NOW()` in SQL, not application time

**API Response Format**:
- Return as ISO 8601 string: `"2025-01-31T14:30:00+00:00"`
- Frameworks handle conversion automatically (Pydantic, Strawberry, etc.)

---

## Query Patterns for Agents

### User Lookup
```sql
-- By UUID (public API)
SELECT pk_user, id, username, email FROM tb_user WHERE id = $1;

-- By username (login)
SELECT pk_user, id, username, email FROM tb_user WHERE username = $1;

-- By email
SELECT pk_user, id, username, email FROM tb_user WHERE email = $1;
```

### Post with Author
```sql
SELECT p.*, u.id as author_id, u.username
FROM tb_post p
JOIN tb_user u ON p.fk_author = u.pk_user
WHERE p.id = $1;
```

### Post with All Related Data
```sql
SELECT p.id, p.title, p.content,
       u.id as author_id, u.username,
       c.id as comment_id, c.content as comment_content,
       cu.id as commenter_id, cu.username as commenter
FROM tb_post p
LEFT JOIN tb_user u ON p.fk_author = u.pk_user
LEFT JOIN tb_comment c ON p.pk_post = c.fk_post
LEFT JOIN tb_user cu ON c.fk_author = cu.pk_user
WHERE p.id = $1
ORDER BY c.created_at;
```

### Posts by User (Paginated)
```sql
SELECT id, title, created_at, status
FROM tb_post
WHERE fk_author = (SELECT pk_user FROM tb_user WHERE id = $1)
  AND status = 'published'
ORDER BY published_at DESC
LIMIT 20 OFFSET $2;
```

---

## Key Rules for Agents

1. **Always use `pk_*` for foreign keys** in INSERT/UPDATE operations
2. **Use `id` (UUID) for API queries** (WHERE clauses matching public IDs)
3. **Timestamps are UTC** - Don't assume local time
4. **Cascade deletes happen automatically** - Deleting a user deletes all their content
5. **Status field controls visibility** - Draft posts are not published
6. **Nested comments are supported** - Use `fk_parent` for replies
7. **User cannot follow themselves** - CHECK constraint prevents this
8. **One reaction per user per post** - Primary key enforces this

---

## Validation Rules

| Column | Rule | Example |
|--------|------|---------|
| `username` | 1-100 chars, alphanumeric + underscore | `john_doe` ✅, `a` ✅, `this_is_way_too_long_username...` ❌ |
| `email` | Valid email format | `user@example.com` ✅, `invalid` ❌ |
| `title` | 1-500 chars | `My Post` ✅, `` (empty) ❌ |
| `status` | One of: draft, published, archived | `'published'` ✅, `'pending'` ❌ |
| `reaction_type` | One of: like, love, laugh, angry | `'like'` ✅, `'thumbsup'` ❌ |

---

## Related Documentation

- **Schema Changes**: See `database/migrations/` for version history
- **Test Data**: See `database/seed-data/` for fixture generation
- **ORM Mappings**: See individual framework `models/` directories
- **Testing**: See `docs/TESTING_README.md` for test database setup

