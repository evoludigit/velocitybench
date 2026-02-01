# FraiseQL Framework - VelocityBench

FraiseQL v2 is a compiled GraphQL execution engine written in pure Rust. Unlike traditional GraphQL servers that resolve relationships at query time, FraiseQL uses the JSONB pattern where relationships are pre-shaped at the database level.

## Architecture

```
Database Tables (tb_user, tb_post, tb_comment)
        ↓
JSONB Views (v_user, v_post, v_comment)
        ↓
schema.json (Type definitions)
        ↓
fraiseql-cli compile → schema.compiled.json
        ↓
fraiseql-server (Pure Rust binary)
        ↓
HTTP GraphQL Endpoint
```

## Key Characteristics

- **Compiled Execution**: Schema compiled to optimized format before runtime
- **JSONB Pattern**: Relationships pre-computed in database views (no N+1 queries)
- **Write-Time Optimization**: Relationship computation happens at write time in views
- **Pure Rust Runtime**: No Python involved in query execution
- **Performance**: Baseline (xs dataset):
  - Simple query: 0.37ms p50, 0.94ms p99
  - Nested query: 0.42ms p50, 0.47ms p99
  - Throughput: 2400-2500 req/s

## Database Schema

### JSONB Views

The FraiseQL framework uses three main views that implement the JSONB pattern:

#### v_user
Maps `tb_user` table to GraphQL User type with all fields in JSONB:
```sql
SELECT
    id,
    jsonb_build_object(
        'id', id::text,
        'email', email,
        'username', username,
        'firstName', first_name,
        'lastName', last_name,
        ...
    ) AS data
FROM tb_user;
```

#### v_post
Maps `tb_post` table with nested author data pre-computed:
```sql
SELECT
    id,
    jsonb_build_object(
        'id', id::text,
        'title', title,
        'author', (
            SELECT jsonb_build_object(...)
            FROM tb_user WHERE pk_user = fk_author
        ),
        ...
    ) AS data
FROM tb_post;
```

#### v_comment
Maps `tb_comment` table with nested author and post data pre-computed.

### View Columns

Each view has three columns:
1. **id** (UUID): The object identifier for API queries
2. **data** (JSONB): All object fields plus nested relationships
3. **Denormalized filters** (integer or UUID): For efficient WHERE clauses (e.g., `author_pk`, `post_pk`)

### Indexes

Each view has GIN indexes on the `data` JSONB column for efficient filtering:
```sql
CREATE INDEX idx_v_post_data_gin ON v_post USING GIN(data);
```

## FraiseQL Schema Definition

The schema is defined in `schema.py` using Python decorators:

```python
@fraiseql.type
class User:
    id: str
    email: str
    username: str
    # ... other fields

@fraiseql.query(sql_source="v_user")
def users(limit: int = 10) -> list[User]:
    """Get all users"""
    pass
```

## Running FraiseQL

### 1. Setup Database

The database setup creates the JSONB views:
```bash
python database/setup.py fraiseql
```

This:
- Creates `fraiseql_test` database
- Applies Trinity Pattern schema (`schema-template.sql`)
- Creates JSONB views (`frameworks/fraiseql/database/extensions.sql`)
- Loads seed data

### 2. Export Schema (Optional)

If modifying the schema definition:
```bash
python schema.py
# Creates schema.json
```

### 3. Compile Schema

```bash
fraiseql-cli compile schema.json
# Creates schema.compiled.json
```

### 4. Start FraiseQL Server

```bash
fraiseql-server \
    --schema schema.compiled.json \
    --database postgresql://velocitybench:password@localhost:5432/fraiseql_test \
    --port 3000
```

### 5. Query GraphQL

```bash
curl -X POST http://localhost:3000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users(limit: 10) { id username email } }"}'
```

## Benchmarking

The FraiseQL implementation is suitable for benchmarking because:

1. **Pure Rust runtime**: No Python overhead
2. **Compiled schema**: No schema parsing at runtime
3. **JSONB efficiency**: No N+1 queries, all data pre-shaped
4. **Baseline comparison**: Used as reference for other frameworks in Phase 3

Baseline metrics are stored in `benchmarks/reports/fraiseql_baseline.json`.

## Performance Characteristics

FraiseQL achieves high performance through:

- **Compile-time optimization**: Schema analyzed and optimized before execution
- **Database-level relationship pre-computation**: JSONB views include nested data
- **Efficient traversal**: GraphQL execution is pure data extraction from pre-shaped JSON
- **Minimal overhead**: Rust runtime handles only query parsing and JSON serialization

Example query execution flow:
```
GraphQL Query: { posts(limit: 10) { id title author { name } } }
  ↓
fraiseql-server parses query
  ↓
Maps to SQL: SELECT data FROM v_post LIMIT 10
  ↓
PostgreSQL returns pre-shaped JSONB with author data embedded
  ↓
Server extracts requested fields and returns JSON
  ↓
~0.5ms total latency
```

## Files

- `schema.py`: FraiseQL schema definition (Python decorators)
- `database/extensions.sql`: JSONB views
- `database/schema.sql`: Detailed view definitions (included by extensions.sql)
- `requirements.txt`: Python dependencies
- `README.md`: This file

## Testing

Integration tests verify:
- JSONB views return correct data structure
- Nested relationships are properly embedded
- Performance benchmarks are within expected ranges
- Resource usage is efficient

Tests can be run with:
```bash
pytest tests/integration/test_fraiseql.py -v
```

## Further Reading

- [FraiseQL Documentation](https://github.com/lionel/fraiseql)
- [JSONB Pattern Overview](../README.md)
- [VelocityBench Phase 2 Documentation](../../.phases/phase-02-server-setup.md)
