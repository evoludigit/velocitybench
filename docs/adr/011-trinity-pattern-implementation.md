# ADR-011: Trinity Pattern Implementation Deep Dive

**Status**: Accepted
**Date**: 2025-01-30
**Author**: VelocityBench Team

## Context

ADR-001 established the Trinity Pattern (Write Tables, Projection Views, Composition Views) as VelocityBench's data layer architecture. This ADR extends ADR-001 with implementation details discovered during development:

1. **Materialized Views**: When should views be materialized vs. standard?
2. **Index Strategy**: How to index views for optimal query performance?
3. **Query Optimization**: Techniques to avoid slow nested joins in composition views
4. **Migration Strategy**: How to evolve schema without breaking API contracts?
5. **Performance Trade-offs**: When does the Trinity Pattern hurt performance?

## Decision

**Implement Trinity Pattern with selective materialization, strategic indexing, and query optimization techniques.**

### Layer 1: Write Tables (tb_*) - Detailed Schema

**Naming Convention**: `tb_{entity}` (tb_users, tb_posts, tb_comments)

**Design Principles**:
- Normalized to 3NF (Third Normal Form)
- Minimal constraints (FK constraints exist, no complex check constraints)
- Optimized for INSERT/UPDATE/DELETE speed
- SERIAL primary keys (auto-increment)
- Timestamps: `created_at`, `updated_at` (for audit trail)

**Example - Users Table**:
```sql
CREATE TABLE tb_users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Minimal indexes on write tables (only uniqueness + FK lookup)
CREATE UNIQUE INDEX idx_tb_users_email ON tb_users(email);

-- Update trigger for updated_at
CREATE TRIGGER update_tb_users_updated_at
    BEFORE UPDATE ON tb_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Why Minimal Indexes**:
- Write tables are write-optimized
- Indexes slow down INSERTs/UPDATEs
- Query indexes go on views (Layer 2/3), not write tables

### Layer 2: Projection Views (v_*) - Denormalization Strategy

**Naming Convention**: `v_{entity}` (v_users, v_posts, v_comments)

**Design Principles**:
- Denormalize for common access patterns
- Include foreign key data (JOINs pre-computed)
- Add computed columns (e.g., `full_name`, `post_count`)
- Still entity-focused (not aggregated)

**Example - Posts Projection**:
```sql
CREATE VIEW v_posts AS
SELECT
    p.id,
    p.title,
    p.content,
    p.created_at,
    p.updated_at,
    -- Denormalize author information
    p.user_id AS author_id,
    u.name AS author_name,
    u.email AS author_email,
    u.avatar_url AS author_avatar,
    -- Computed fields
    CHAR_LENGTH(p.content) AS content_length,
    DATE(p.created_at) AS published_date
FROM tb_posts p
JOIN tb_users u ON p.user_id = u.id;
```

**Indexing Projection Views** (when materialized):
```sql
-- Materialize for complex views
CREATE MATERIALIZED VIEW v_posts AS ...;

-- Index common lookup patterns
CREATE INDEX idx_v_posts_author_id ON v_posts(author_id);
CREATE INDEX idx_v_posts_published_date ON v_posts(published_date);
CREATE INDEX idx_v_posts_created_at ON v_posts(created_at DESC);

-- Refresh strategy (manual for now, could be automated)
REFRESH MATERIALIZED VIEW CONCURRENTLY v_posts;
```

**When to Materialize**:
- ✅ View has complex JOINs (3+ tables)
- ✅ View is queried frequently (hot path)
- ✅ Underlying data changes infrequently (< 1000 writes/min)
- ❌ View is simple (1-2 table JOIN) - Keep as standard view
- ❌ Data changes rapidly - Materialization causes stale reads

### Layer 3: Composition Views (tv_*) - Rich Aggregations

**Naming Convention**: `tv_{entity}_with_{aggregation}` (tv_posts_with_stats, tv_users_with_counts)

**Design Principles**:
- Combine data from multiple projections
- Add aggregations (COUNT, SUM, AVG)
- Support GraphQL object types with nested resolvers
- May be materialized for expensive aggregations

**Example - Posts with Statistics**:
```sql
CREATE VIEW tv_posts_with_stats AS
SELECT
    p.*,
    -- Aggregations
    COUNT(DISTINCT c.id) AS comment_count,
    COUNT(DISTINCT l.id) AS like_count,
    MAX(c.created_at) AS last_comment_at,
    -- Computed engagement score
    (COUNT(DISTINCT c.id) * 2 + COUNT(DISTINCT l.id)) AS engagement_score
FROM v_posts p
LEFT JOIN tb_comments c ON p.id = c.post_id
LEFT JOIN tb_likes l ON p.id = l.post_id
GROUP BY p.id;
```

**Performance Optimization Technique: Partial Aggregation**

Instead of GROUP BY on entire v_posts (slow), create separate aggregation tables:

```sql
-- Aggregation table (updated by triggers)
CREATE TABLE tb_post_stats (
    post_id INT PRIMARY KEY REFERENCES tb_posts(id),
    comment_count INT NOT NULL DEFAULT 0,
    like_count INT NOT NULL DEFAULT 0,
    last_comment_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Trigger on tb_comments to update stats
CREATE TRIGGER update_post_stats_on_comment
AFTER INSERT OR DELETE ON tb_comments
FOR EACH ROW
EXECUTE FUNCTION update_post_comment_count();

-- Composition view becomes simple JOIN (fast!)
CREATE VIEW tv_posts_with_stats AS
SELECT
    p.*,
    COALESCE(s.comment_count, 0) AS comment_count,
    COALESCE(s.like_count, 0) AS like_count,
    s.last_comment_at,
    (COALESCE(s.comment_count, 0) * 2 + COALESCE(s.like_count, 0)) AS engagement_score
FROM v_posts p
LEFT JOIN tb_post_stats s ON p.id = s.post_id;
```

**Result**: Composition view queries are O(1) instead of O(N) aggregations.

### Query Optimization Techniques

#### Technique 1: Index on Computed Columns (Materialized Views)

```sql
CREATE MATERIALIZED VIEW v_posts_sorted AS
SELECT * FROM v_posts
ORDER BY created_at DESC;

CREATE INDEX idx_v_posts_sorted ON v_posts_sorted(created_at DESC);
```

#### Technique 2: Partial Indexes for Filters

```sql
-- Common query: published posts only
CREATE INDEX idx_v_posts_published ON v_posts(created_at DESC)
WHERE status = 'published';

-- GraphQL: posts(status: PUBLISHED, limit: 20)
-- Uses partial index, 10x faster than full table scan
```

#### Technique 3: JSONB Aggregation for GraphQL

```sql
-- Pre-aggregate comments as JSONB array
CREATE VIEW tv_posts_with_comments AS
SELECT
    p.*,
    COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'id', c.id,
                'content', c.content,
                'author_name', c.author_name
            ) ORDER BY c.created_at DESC
        ) FILTER (WHERE c.id IS NOT NULL),
        '[]'::jsonb
    ) AS comments
FROM v_posts p
LEFT JOIN v_comments c ON p.id = c.post_id
GROUP BY p.id;
```

**Result**: Single query returns post + comments (no N+1), GraphQL resolver is trivial.

### Migration Strategy

**Problem**: Adding a new field breaks API contracts if not handled carefully.

**Solution**: Use view abstraction to hide schema changes.

**Example - Adding `verified` field to users**:

```sql
-- Step 1: Add column to write table (no API break yet)
ALTER TABLE tb_users ADD COLUMN verified BOOLEAN NOT NULL DEFAULT false;

-- Step 2: Update projection view (API now exposes new field)
CREATE OR REPLACE VIEW v_users AS
SELECT
    id,
    name,
    email,
    bio,
    avatar_url,
    verified,  -- New field added
    created_at,
    updated_at
FROM tb_users;

-- Step 3: Composition views automatically inherit new field
-- No changes needed to tv_users_with_stats (uses v_users.*)
```

**Result**: Framework code unchanged, GraphQL schema updated, API contracts extended (not broken).

### Performance Trade-offs

#### When Trinity Pattern Hurts Performance

1. **Deep Nesting**: 4+ levels of views (view -> view -> view -> table)
   - **Solution**: Materialize intermediate views OR flatten into fewer layers

2. **Frequent Writes + Materialized Views**: Writes invalidate materialized views
   - **Solution**: Use standard views for write-heavy tables, materialize read-heavy only

3. **Complex Aggregations**: GROUP BY on millions of rows
   - **Solution**: Use aggregation tables (tb_post_stats) with trigger updates

4. **Over-Indexing**: Too many indexes on materialized views slows refreshes
   - **Solution**: Index only hot query paths (measured via EXPLAIN ANALYZE)

## Consequences

### Positive

✅ **Query Performance**: Indexing and materialization make reads fast (< 10ms p95)
✅ **Schema Evolution**: Views decouple API from storage (migrations don't break contracts)
✅ **N+1 Prevention**: JSONB aggregation and pre-joins eliminate N+1 queries
✅ **Maintainability**: Aggregation tables centralize stats logic (no per-framework recomputation)
✅ **Flexibility**: Can optimize hot paths without changing framework code

### Negative

❌ **Complexity**: 3 layers + materialization + triggers = steep learning curve
❌ **Migration Overhead**: Schema changes require updating 3 layers
❌ **Stale Data Risk**: Materialized views can serve stale data (need refresh strategy)
❌ **Trigger Debugging**: Trigger-based stats updates are hard to debug when they fail
❌ **Storage Overhead**: Materialized views + aggregation tables duplicate data (~2x storage)

## Alternatives Considered

### Alternative 1: ORM-Only (No Views)

- **Approach**: Each framework queries tb_* tables directly via ORM
- **Pros**: Simple, no view management
- **Cons**:
  - N+1 queries everywhere (Graphene, Strawberry would be slow)
  - Schema changes break all frameworks
  - No aggregation caching (every request recomputes stats)
- **Rejected**: Violates fair benchmarking (frameworks with better ORMs win unfairly)

### Alternative 2: API-Layer Caching (Redis)

- **Approach**: Cache aggregations in Redis, not database views
- **Pros**: Faster than database views, TTL-based expiration
- **Cons**:
  - Cache invalidation complexity (when to invalidate?)
  - Not all frameworks have Redis clients
  - Doesn't solve N+1 problem (still need views for JOINs)
- **Rejected**: Adds external dependency, doesn't fully solve problem

### Alternative 3: Event Sourcing + CQRS

- **Approach**: Write events to stream, materialize views from events
- **Pros**: Ultimate flexibility, temporal queries, audit trail
- **Cons**:
  - Massive complexity (Kafka/EventStore/etc.)
  - Eventual consistency (reads lag writes)
  - Overkill for benchmarking
- **Rejected**: Too complex for VelocityBench's needs

## Related Decisions

- **ADR-001**: Trinity Pattern - This ADR extends with implementation details
- **ADR-009**: Six-Dimensional QA Testing - Config validator ensures views are queried correctly
- **ADR-010**: Benchmarking Methodology - Performance targets inform materialization decisions

## Implementation Status

✅ **Complete** - All optimizations implemented in production schema

## Schema Documentation

Full schema with all views, indexes, and triggers: [docs/api/SCHEMA.md](../api/SCHEMA.md)

## References

- [PostgreSQL Materialized Views](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
- [PostgreSQL Indexing Strategies](https://www.postgresql.org/docs/current/indexes.html)
- [N+1 Query Problem](https://stackoverflow.com/questions/97197/what-is-the-n1-selects-problem)
- [Database Denormalization](https://en.wikipedia.org/wiki/Denormalization)
- [ADR-001](001-trinity-pattern.md) - Original Trinity Pattern decision
