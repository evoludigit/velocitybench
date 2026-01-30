# ADR-001: Trinity Pattern for Data Layer

**Status**: Accepted
**Date**: 2024-01-15
**Author**: VelocityBench Team

## Context

VelocityBench needs to support benchmarking both REST APIs and GraphQL endpoints across 38 frameworks with varying design patterns. The challenge is:

1. **Write Optimization**: Native tables must be fast for INSERT/UPDATE operations
2. **Query Flexibility**: APIs need flexible queries for different access patterns
3. **Schema Stability**: API contracts should remain stable even if internal schema changes
4. **Performance**: Must support both simple and complex queries without performance degradation

## Decision

Implement the **Trinity Pattern** with three layers:

### Layer 1: Write Tables (tb_*)
- Native PostgreSQL tables optimized for writes
- Single source of truth for all data
- Minimal denormalization
- Example: `tb_users`, `tb_posts`, `tb_comments`

### Layer 2: Projection Views (v_*)
- Denormalized views for specific query patterns
- Pre-compute common access paths
- Enable fast filtering and sorting
- Example: `v_users` (with computed fields), `v_posts` (with author details)

### Layer 3: Composition Views (tv_*)
- Complex views combining data from projections
- Support rich GraphQL types and REST endpoints
- Add computed fields (counts, aggregations)
- Example: `tv_posts_with_stats` (post + comment count + author info)

### Visual Structure

```
┌─────────────────────────────────────────┐
│   Application Layer (REST/GraphQL)      │
└─────────────────────────────────────────┘
           ↓            ↓            ↓
     ┌─────────────────────────────────────┐
     │  Composition Views (tv_*)            │  Layer 3
     │  - Rich types with aggregations      │
     │  - GraphQL object types              │
     └─────────────────────────────────────┘
           ↓            ↓            ↓
     ┌─────────────────────────────────────┐
     │  Projection Views (v_*)              │  Layer 2
     │  - Denormalized for access patterns  │
     │  - Computed columns                  │
     └─────────────────────────────────────┘
           ↓            ↓            ↓
     ┌─────────────────────────────────────┐
     │  Write Tables (tb_*)                 │  Layer 1
     │  - Normalized, optimized for writes  │
     │  - Single source of truth            │
     └─────────────────────────────────────┘
```

### SQL Example

```sql
-- Layer 1: Write Table (normalized)
CREATE TABLE tb_posts (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES tb_users(id),
    title VARCHAR(255),
    content TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Layer 2: Projection View (with author)
CREATE VIEW v_posts AS
SELECT
    p.id,
    p.title,
    p.content,
    p.created_at,
    p.updated_at,
    u.id as author_id,
    u.name as author_name,
    u.email as author_email
FROM tb_posts p
JOIN tb_users u ON p.user_id = u.id;

-- Layer 3: Composition View (with stats)
CREATE VIEW tv_posts_with_stats AS
SELECT
    p.*,
    COUNT(c.id) as comment_count,
    MAX(c.created_at) as last_comment_at
FROM v_posts p
LEFT JOIN tb_comments c ON p.id = c.post_id
GROUP BY p.id;
```

## Consequences

### Positive

✅ **Flexibility**: Each framework can query views it needs without schema changes
✅ **Performance**: Projections pre-compute common queries, views are materialized when needed
✅ **Isolation**: Write operations only touch `tb_*` layer, API layer uses views
✅ **Testability**: Can test different query patterns independently
✅ **Scalability**: Views can be materialized or indexed for performance
✅ **Stability**: API contracts independent of internal write table schema

### Negative

❌ **Complexity**: Three layers to understand and maintain
❌ **Migration Cost**: Adding new fields requires updating all three layers
❌ **View Performance**: Nested joins in composition views can be slow (mitigated by materialization)
❌ **Development Overhead**: Framework developers must understand the pattern

## Alternatives Considered

### Alternative 1: Single Flat Schema
- Pros: Simple, no view overhead
- Cons: Schema changes break APIs, poor separation of concerns
- **Rejected**: Doesn't meet stability requirement

### Alternative 2: ORM-Only (No Views)
- Pros: Complete flexibility in ORM code
- Cons: Each framework implements differently, unfair comparison, slow complex queries
- **Rejected**: Violates benchmarking fairness

### Alternative 3: Event Sourcing
- Pros: Complete audit trail, temporal queries
- Cons: Complexity, eventual consistency issues, slower writes
- **Rejected**: Overkill for benchmarking tool

## Related Decisions

- ADR-002: Framework Isolation (each framework gets dedicated database)
- ADR-003: Multi-Language Support (Trinity Pattern supports any language)

## Implementation Status

✅ Complete - All frameworks use Trinity Pattern for consistency

## References

- [PostgreSQL Views Documentation](https://www.postgresql.org/docs/current/sql-createview.html)
- [Database Normalization Best Practices](https://en.wikipedia.org/wiki/Database_normalization)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html) - Related pattern for separation of concerns
