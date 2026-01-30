# Database Schema Reference

VelocityBench uses the Trinity Pattern (ADR-001) to structure its database schema. This document provides a comprehensive reference of all tables, views, indexes, and relationships.

## Table of Contents

- [Overview](#overview)
- [Layer 1: Write Tables (tb_*)](#layer-1-write-tables-tb_)
- [Layer 2: Projection Views (v_*)](#layer-2-projection-views-v_)
- [Layer 3: Composition Views (tv_*)](#layer-3-composition-views-tv_)
- [Indexes](#indexes)
- [Triggers](#triggers)
- [Relationships](#relationships)
- [Data Types](#data-types)

## Overview

VelocityBench's database schema follows the Trinity Pattern with three layers:

```
Application (REST/GraphQL)
          ↓
Composition Views (tv_*)    ← Rich aggregations, GraphQL object types
          ↓
Projection Views (v_*)      ← Denormalized for query patterns
          ↓
Write Tables (tb_*)         ← Normalized, write-optimized
```

**Key Principles**:
- **Write tables**: Optimized for INSERT/UPDATE/DELETE
- **Projection views**: Denormalized for common queries
- **Composition views**: Aggregated data with statistics

**PostgreSQL Version**: 15.5+

## Layer 1: Write Tables (tb_*)

Write tables are the single source of truth for all data. They are normalized to 3NF and optimized for write operations.

### tb_users

User accounts for the blog platform.

```sql
CREATE TABLE tb_users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    bio             TEXT,
    avatar_url      VARCHAR(500),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Constraints**:
- `PRIMARY KEY`: `id`
- `UNIQUE`: `email`
- `NOT NULL`: `id`, `name`, `email`, `created_at`, `updated_at`

**Indexes**:
- `pk_tb_users` (PRIMARY KEY on `id`)
- `idx_tb_users_email` (UNIQUE on `email`)

**Triggers**:
- `update_tb_users_updated_at` - Auto-update `updated_at` on modification

**Sample Data**:
```
id | name           | email                  | created_at
---|----------------|------------------------|-------------------
1  | Alice Johnson  | alice@example.com      | 2024-01-15 10:30:00
2  | Bob Smith      | bob@example.com        | 2024-01-16 11:45:00
```

---

### tb_posts

Blog posts written by users.

```sql
CREATE TABLE tb_posts (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES tb_users(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    content         TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Constraints**:
- `PRIMARY KEY`: `id`
- `FOREIGN KEY`: `user_id` → `tb_users(id)` (CASCADE on delete)
- `NOT NULL`: `id`, `user_id`, `title`, `content`, `status`, `created_at`, `updated_at`

**Indexes**:
- `pk_tb_posts` (PRIMARY KEY on `id`)
- `idx_tb_posts_user_id` (on `user_id` for JOIN performance)
- `idx_tb_posts_created_at` (on `created_at DESC` for sorting)

**Triggers**:
- `update_tb_posts_updated_at` - Auto-update `updated_at`
- `update_tb_post_stats_on_insert` - Update aggregation table on insert

**Status Values**:
- `draft` - Not yet published
- `published` - Publicly visible
- `archived` - No longer visible

**Sample Data**:
```
id | user_id | title                      | status    | created_at
---|---------|----------------------------|-----------|-------------------
1  | 1       | Introduction to GraphQL    | published | 2024-01-17 09:00:00
2  | 1       | Advanced TypeScript        | draft     | 2024-01-18 14:30:00
```

---

### tb_comments

Comments on blog posts.

```sql
CREATE TABLE tb_comments (
    id              SERIAL PRIMARY KEY,
    post_id         INTEGER NOT NULL REFERENCES tb_posts(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES tb_users(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Constraints**:
- `PRIMARY KEY`: `id`
- `FOREIGN KEY`: `post_id` → `tb_posts(id)` (CASCADE)
- `FOREIGN KEY`: `user_id` → `tb_users(id)` (CASCADE)
- `NOT NULL`: All fields

**Indexes**:
- `pk_tb_comments` (PRIMARY KEY on `id`)
- `idx_tb_comments_post_id` (on `post_id`)
- `idx_tb_comments_user_id` (on `user_id`)
- `idx_tb_comments_created_at` (on `created_at DESC`)

**Triggers**:
- `update_tb_comments_updated_at`
- `update_tb_post_stats_on_comment_insert`
- `update_tb_post_stats_on_comment_delete`

**Sample Data**:
```
id | post_id | user_id | content                        | created_at
---|---------|---------|--------------------------------|-------------------
1  | 1       | 2       | Great introduction!            | 2024-01-17 10:15:00
2  | 1       | 1       | Thanks for the feedback!       | 2024-01-17 11:30:00
```

---

### tb_post_stats

Aggregation table for post statistics (updated by triggers).

```sql
CREATE TABLE tb_post_stats (
    post_id             INTEGER PRIMARY KEY REFERENCES tb_posts(id) ON DELETE CASCADE,
    comment_count       INTEGER NOT NULL DEFAULT 0,
    like_count          INTEGER NOT NULL DEFAULT 0,
    last_comment_at     TIMESTAMP,
    last_activity_at    TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Purpose**: Pre-compute expensive aggregations to avoid GROUP BY on large tables.

**Constraints**:
- `PRIMARY KEY`: `post_id`
- `FOREIGN KEY`: `post_id` → `tb_posts(id)` (CASCADE)

**Indexes**:
- `pk_tb_post_stats` (PRIMARY KEY on `post_id`)
- `idx_tb_post_stats_comment_count` (on `comment_count DESC`)

**Updated By Triggers**:
- Insert/delete on `tb_comments` → Update `comment_count`, `last_comment_at`
- Insert/delete on `tb_likes` → Update `like_count`

**Sample Data**:
```
post_id | comment_count | like_count | last_comment_at      | updated_at
--------|---------------|------------|----------------------|-------------------
1       | 2             | 15         | 2024-01-17 11:30:00  | 2024-01-17 11:30:05
2       | 0             | 3          | NULL                 | 2024-01-18 14:30:00
```

---

## Layer 2: Projection Views (v_*)

Projection views denormalize data for common query patterns. They include JOINs to related tables and computed columns.

### v_users

User projection with computed fields.

```sql
CREATE VIEW v_users AS
SELECT
    u.id,
    u.name,
    u.email,
    u.bio,
    u.avatar_url,
    u.created_at,
    u.updated_at,
    -- Computed fields
    COUNT(DISTINCT p.id) AS post_count,
    COUNT(DISTINCT c.id) AS comment_count,
    CASE
        WHEN u.avatar_url IS NOT NULL THEN true
        ELSE false
    END AS has_avatar
FROM tb_users u
LEFT JOIN tb_posts p ON u.id = p.user_id
LEFT JOIN tb_comments c ON u.id = c.user_id
GROUP BY u.id;
```

**Fields**:
- `id` (INTEGER) - User ID
- `name` (VARCHAR) - User name
- `email` (VARCHAR) - Email address
- `bio` (TEXT) - User bio
- `avatar_url` (VARCHAR) - Avatar URL
- `created_at` (TIMESTAMP) - Account creation time
- `updated_at` (TIMESTAMP) - Last update time
- `post_count` (INTEGER) - Number of posts written
- `comment_count` (INTEGER) - Number of comments made
- `has_avatar` (BOOLEAN) - Whether user has avatar

**Used By**:
- REST: `GET /users`, `GET /users/:id`
- GraphQL: `Query.users`, `Query.user(id)`

---

### v_posts

Post projection with author details.

```sql
CREATE VIEW v_posts AS
SELECT
    p.id,
    p.title,
    p.content,
    p.status,
    p.created_at,
    p.updated_at,
    -- Author details (denormalized)
    p.user_id AS author_id,
    u.name AS author_name,
    u.email AS author_email,
    u.avatar_url AS author_avatar,
    -- Computed fields
    CHAR_LENGTH(p.content) AS content_length,
    DATE(p.created_at) AS published_date,
    EXTRACT(EPOCH FROM (NOW() - p.created_at)) AS age_seconds
FROM tb_posts p
JOIN tb_users u ON p.user_id = u.id;
```

**Fields**:
- `id` (INTEGER) - Post ID
- `title` (VARCHAR) - Post title
- `content` (TEXT) - Post content (full text)
- `status` (VARCHAR) - Post status (draft/published/archived)
- `created_at` (TIMESTAMP) - Post creation time
- `updated_at` (TIMESTAMP) - Last update time
- `author_id` (INTEGER) - Author user ID
- `author_name` (VARCHAR) - Author name
- `author_email` (VARCHAR) - Author email
- `author_avatar` (VARCHAR) - Author avatar URL
- `content_length` (INTEGER) - Character count
- `published_date` (DATE) - Publication date (without time)
- `age_seconds` (NUMERIC) - Post age in seconds

**Used By**:
- REST: `GET /posts`, `GET /posts/:id`
- GraphQL: `Query.posts`, `Query.post(id)`, `User.posts`

---

### v_comments

Comment projection with post and author details.

```sql
CREATE VIEW v_comments AS
SELECT
    c.id,
    c.content,
    c.created_at,
    c.updated_at,
    -- Post details
    c.post_id,
    p.title AS post_title,
    -- Author details
    c.user_id AS author_id,
    u.name AS author_name,
    u.email AS author_email,
    u.avatar_url AS author_avatar
FROM tb_comments c
JOIN tb_posts p ON c.post_id = p.id
JOIN tb_users u ON c.user_id = u.id;
```

**Fields**:
- `id` (INTEGER) - Comment ID
- `content` (TEXT) - Comment content
- `created_at` (TIMESTAMP) - Comment creation time
- `updated_at` (TIMESTAMP) - Last update time
- `post_id` (INTEGER) - Post ID
- `post_title` (VARCHAR) - Post title
- `author_id` (INTEGER) - Author user ID
- `author_name` (VARCHAR) - Author name
- `author_email` (VARCHAR) - Author email
- `author_avatar` (VARCHAR) - Author avatar URL

**Used By**:
- REST: `GET /comments`, `GET /posts/:id/comments`
- GraphQL: `Query.comments`, `Post.comments`

---

## Layer 3: Composition Views (tv_*)

Composition views combine multiple projections and add rich aggregations. These are used for complex GraphQL queries and summary endpoints.

### tv_posts_with_stats

Posts with comment statistics and engagement metrics.

```sql
CREATE VIEW tv_posts_with_stats AS
SELECT
    p.*,
    -- From aggregation table (fast!)
    COALESCE(s.comment_count, 0) AS comment_count,
    COALESCE(s.like_count, 0) AS like_count,
    s.last_comment_at,
    -- Computed engagement score
    (COALESCE(s.comment_count, 0) * 2 + COALESCE(s.like_count, 0)) AS engagement_score
FROM v_posts p
LEFT JOIN tb_post_stats s ON p.id = s.post_id;
```

**Fields**: All fields from `v_posts`, plus:
- `comment_count` (INTEGER) - Number of comments
- `like_count` (INTEGER) - Number of likes
- `last_comment_at` (TIMESTAMP) - Last comment timestamp
- `engagement_score` (INTEGER) - Computed engagement (comments*2 + likes)

**Used By**:
- REST: `GET /posts?include=stats`
- GraphQL: `Post` type with `commentCount`, `likeCount` fields

---

### tv_users_with_activity

Users with activity statistics.

```sql
CREATE VIEW tv_users_with_activity AS
SELECT
    u.*,
    -- Post statistics
    COUNT(DISTINCT p.id) AS post_count,
    MAX(p.created_at) AS last_post_at,
    -- Comment statistics
    COUNT(DISTINCT c.id) AS comment_count,
    MAX(c.created_at) AS last_comment_at,
    -- Overall activity
    GREATEST(MAX(p.created_at), MAX(c.created_at)) AS last_activity_at
FROM v_users u
LEFT JOIN tb_posts p ON u.id = p.user_id
LEFT JOIN tb_comments c ON u.id = c.user_id
GROUP BY u.id;
```

**Fields**: All fields from `v_users`, plus:
- `post_count` (INTEGER) - Number of posts
- `last_post_at` (TIMESTAMP) - Last post timestamp
- `comment_count` (INTEGER) - Number of comments
- `last_comment_at` (TIMESTAMP) - Last comment timestamp
- `last_activity_at` (TIMESTAMP) - Last post or comment (whichever is newer)

**Used By**:
- GraphQL: `User` type with activity fields

---

### tv_posts_with_comments_json

Posts with comments pre-aggregated as JSONB array (for N+1 prevention).

```sql
CREATE VIEW tv_posts_with_comments_json AS
SELECT
    p.*,
    COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'id', c.id,
                'content', c.content,
                'authorName', c.author_name,
                'authorAvatar', c.author_avatar,
                'createdAt', c.created_at
            ) ORDER BY c.created_at DESC
        ) FILTER (WHERE c.id IS NOT NULL),
        '[]'::jsonb
    ) AS comments
FROM tv_posts_with_stats p
LEFT JOIN v_comments c ON p.id = c.post_id
GROUP BY p.id;
```

**Purpose**: Eliminate N+1 queries in GraphQL by fetching post + comments in single query.

**Fields**: All fields from `tv_posts_with_stats`, plus:
- `comments` (JSONB) - Array of comment objects

**Used By**:
- GraphQL: `Post.comments` resolver (single query, no N+1)

---

## Indexes

### Primary Keys

- `pk_tb_users` on `tb_users(id)`
- `pk_tb_posts` on `tb_posts(id)`
- `pk_tb_comments` on `tb_comments(id)`
- `pk_tb_post_stats` on `tb_post_stats(post_id)`

### Foreign Key Indexes

- `idx_tb_posts_user_id` on `tb_posts(user_id)`
- `idx_tb_comments_post_id` on `tb_comments(post_id)`
- `idx_tb_comments_user_id` on `tb_comments(user_id)`

### Query Optimization Indexes

- `idx_tb_users_email` (UNIQUE) on `tb_users(email)` - Fast email lookup
- `idx_tb_posts_created_at` on `tb_posts(created_at DESC)` - Sorted post queries
- `idx_tb_posts_status` on `tb_posts(status)` - Filter by status
- `idx_tb_comments_created_at` on `tb_comments(created_at DESC)` - Sorted comments
- `idx_tb_post_stats_comment_count` on `tb_post_stats(comment_count DESC)` - Popular posts

### Partial Indexes

```sql
-- Published posts only (faster queries for common case)
CREATE INDEX idx_tb_posts_published
ON tb_posts(created_at DESC)
WHERE status = 'published';
```

---

## Triggers

### Auto-update Timestamps

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Applied to all write tables
CREATE TRIGGER update_tb_users_updated_at
    BEFORE UPDATE ON tb_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tb_posts_updated_at
    BEFORE UPDATE ON tb_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tb_comments_updated_at
    BEFORE UPDATE ON tb_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Aggregation Table Updates

```sql
-- Update comment count when comment is added
CREATE TRIGGER update_post_stats_on_comment_insert
    AFTER INSERT ON tb_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_post_comment_count();

-- Update comment count when comment is deleted
CREATE TRIGGER update_post_stats_on_comment_delete
    AFTER DELETE ON tb_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_post_comment_count();
```

---

## Relationships

### Entity Relationship Diagram

```
┌─────────────┐
│  tb_users   │
│ (id, name,  │
│  email)     │
└──────┬──────┘
       │
       │ 1:N (user writes posts)
       ↓
┌─────────────┐         ┌──────────────┐
│  tb_posts   │ 1:1     │tb_post_stats │
│ (id, title, │ ←──────→│(post_id,     │
│  user_id)   │         │ comment_cnt) │
└──────┬──────┘         └──────────────┘
       │
       │ 1:N (post has comments)
       ↓
┌─────────────┐
│tb_comments  │
│ (id,        │
│  post_id,   │───┐
│  user_id)   │   │
└─────────────┘   │
       ↑          │
       │          │
       └──────────┘
    N:1 (user writes comments)
```

### Cascade Rules

- **User deletion**: Cascades to `tb_posts` and `tb_comments` (all user content deleted)
- **Post deletion**: Cascades to `tb_comments` and `tb_post_stats` (all related data deleted)
- **Comment deletion**: Updates `tb_post_stats` (trigger decrements count)

---

## Data Types

### Standard Types

- `SERIAL` - Auto-incrementing integer (PostgreSQL specific)
- `INTEGER` - 32-bit integer
- `VARCHAR(N)` - Variable-length string (max N characters)
- `TEXT` - Unlimited length string
- `TIMESTAMP` - Date and time (no timezone)
- `BOOLEAN` - True/false
- `JSONB` - Binary JSON (efficient storage and indexing)

### Timestamp Handling

All timestamps use `TIMESTAMP WITHOUT TIME ZONE` and store UTC time.

**Application Responsibility**:
- Convert to UTC before INSERT/UPDATE
- Convert to user's timezone for display

**Example**:
```sql
-- Store UTC time
INSERT INTO tb_posts (title, created_at)
VALUES ('My Post', NOW() AT TIME ZONE 'UTC');

-- Query returns UTC timestamp
SELECT created_at FROM v_posts WHERE id = 1;
-- Result: 2024-01-17 09:00:00
```

---

## Sample Queries

### Get all published posts with stats

```sql
SELECT id, title, author_name, comment_count, like_count
FROM tv_posts_with_stats
WHERE status = 'published'
ORDER BY created_at DESC
LIMIT 20;
```

### Get user with activity summary

```sql
SELECT id, name, email, post_count, comment_count, last_activity_at
FROM tv_users_with_activity
WHERE id = 1;
```

### Get post with all comments (N+1 prevention)

```sql
SELECT id, title, content, comments
FROM tv_posts_with_comments_json
WHERE id = 1;
```

---

## References

- [ADR-001: Trinity Pattern](../adr/001-trinity-pattern.md) - Pattern overview
- [ADR-011: Trinity Pattern Implementation](../adr/011-trinity-pattern-implementation.md) - Implementation details
- [PostgreSQL Views Documentation](https://www.postgresql.org/docs/current/sql-createview.html)
- [PostgreSQL Triggers](https://www.postgresql.org/docs/current/triggers.html)
- [REST API Documentation](REST.md)
- [GraphQL API Documentation](GRAPHQL.md)
