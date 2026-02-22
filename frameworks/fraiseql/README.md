# FraiseQL v2 Framework - VelocityBench

FraiseQL v2 (2.0.0-rc.2) is a compiled GraphQL execution engine written in pure Rust. Unlike traditional GraphQL servers that resolve relationships at query time, FraiseQL uses the JSONB pattern where relationships are pre-shaped at the database level.

## Architecture

```
Database Tables (tb_user, tb_post, tb_comment)
        ↓
JSONB Views (v_user, v_post, v_comment)
        ↓
schema.py (Python SDK for schema definition)
        ↓
schema.json (Exported schema)
        ↓
fraiseql-cli compile → schema.compiled.json
        ↓
fraiseql-server (Pure Rust binary)
        ↓
HTTP GraphQL Endpoint (port 8815)
```

## Key Characteristics

- **Compiled Execution**: Schema compiled to optimized format before runtime
- **JSONB Pattern**: Relationships pre-computed in database views (no N+1 queries)
- **Write-Time Optimization**: Relationship computation happens in views
- **Pure Rust Runtime**: No Python involved in query execution
- **v2 Features**: Introspection, rate limiting, audit logging, configurable security

## Quick Start

### 1. Install FraiseQL v2 Binaries

From crates.io:
```bash
cargo install fraiseql-cli --version 2.0.0-rc.2
cargo install fraiseql-server --version 2.0.0-rc.2
```

Or build locally:
```bash
cd /home/lionel/code/fraiseql
cargo build --release
```

### 2. Install Python SDK

```bash
cd /home/lionel/code/velocitybench/frameworks/fraiseql
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate Schema

```bash
python schema.py
# Creates schema.json
```

### 4. Compile Schema

```bash
fraiseql-cli compile schema.json -o schema.compiled.json
```

### 5. Start Server

```bash
python main.py
# Or directly:
fraiseql-server --schema schema.compiled.json --config fraiseql.toml --port 8815
```

### 6. Query GraphQL

```bash
# Health check
curl http://localhost:8815/health

# GraphQL query
curl -X POST http://localhost:8815/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users(limit: 5) { id username email } }"}'
```

## Configuration (fraiseql.toml)

```toml
[server]
bind_addr = "0.0.0.0:8815"
shutdown_timeout_secs = 30

[database]
url = "postgresql://velocitybench:password@localhost:5432/fraiseql_test"
pool_min_size = 5
pool_max_size = 20

[graphql]
graphql_path = "/graphql"
health_path = "/health"
introspection_enabled = true
max_query_depth = 10

[security]
rate_limiting_enabled = false
requests_per_second = 100

[audit]
query_logging_enabled = false
slow_query_threshold_ms = 100
```

## Database Schema

### JSONB Views

FraiseQL v2 uses JSONB views that pre-shape data for GraphQL queries:

#### v_user
```sql
SELECT
    id,
    jsonb_build_object(
        'id', id::text,
        'email', email,
        'username', username,
        'firstName', first_name,
        ...
    ) AS data
FROM tb_user;
```

#### v_post (with nested author)
```sql
SELECT
    p.id,
    jsonb_build_object(
        'id', p.id::text,
        'title', p.title,
        'author', jsonb_build_object(
            'id', u.id::text,
            'username', u.username,
            ...
        ),
        ...
    ) AS data
FROM tb_post p
LEFT JOIN tb_user u ON u.pk_user = p.fk_author;
```

## Schema Definition (Python SDK)

FraiseQL v2 uses a Python SDK for schema definition:

```python
from fraiseql import object_type, query, field, argument, ID, String

@object_type(description="User type")
class User:
    id: ID = field(description="User UUID")
    username: String = field(description="Username")

@query(view_source="v_user")
def users(
    limit: Int = argument(default=10),
) -> list[User]:
    pass

schema = FraiseQLSchema(types=[User], queries=[users])
schema.export("schema.json")
```

## Docker

Build and run with Docker:

```bash
# Build image
docker build -t fraiseql-v2 .

# Run container
docker run -p 8815:8815 \
  -e DATABASE_URL=postgresql://... \
  fraiseql-v2
```

Or with docker-compose:

```bash
docker-compose up fraiseql
```

## Testing

Run integration tests:

```bash
cd /home/lionel/code/velocitybench/frameworks/fraiseql
source venv/bin/activate
pytest tests/ -v
```

Run performance benchmarks:

```bash
pytest tests/ -v -m benchmark
```

## Performance

FraiseQL v2 achieves high performance through:

- **Compile-time optimization**: Schema analyzed before runtime
- **Pre-computed relationships**: JSONB views include nested data
- **Efficient traversal**: GraphQL is data extraction from pre-shaped JSON
- **Minimal overhead**: Rust handles only query parsing and JSON serialization

Baseline metrics (xs dataset):
- Simple query: ~0.4ms p50
- Nested query: ~0.5ms p50
- Throughput: 2400+ req/s

## Troubleshooting

### Binary not found

```bash
# Check if installed via cargo
which fraiseql-cli fraiseql-server

# Or set FRAISEQL_ROOT environment variable
export FRAISEQL_ROOT=/path/to/fraiseql
```

### Schema compilation fails

```bash
# Verify schema.json is valid
python schema.py

# Check CLI version
fraiseql-cli --version  # Should be 2.0.0-rc.2
```

### Server won't start

```bash
# Check database connection
psql "postgresql://velocitybench:password@localhost:5432/fraiseql_test"

# Verify config
cat fraiseql.toml

# Run with debug logging
RUST_LOG=debug fraiseql-server --schema schema.compiled.json
```

### Port already in use

```bash
# FraiseQL v2 uses port 8815 by default
lsof -i :8815

# Use different port
python main.py --port 8816
```

## Files

| File | Description |
|------|-------------|
| `schema.py` | FraiseQL v2 schema definition (Python SDK) |
| `schema.json` | Exported schema (generated) |
| `schema.compiled.json` | Compiled schema (generated) |
| `fraiseql.toml` | Server configuration |
| `main.py` | Server management script |
| `Dockerfile` | Multi-stage Docker build |
| `database/extensions.sql` | JSONB view definitions |
| `tests/` | Integration and benchmark tests |

## Version History

- **v2.0.0-rc.2**: Current version
  - New Python SDK for schema authoring
  - Introspection support
  - Rate limiting and audit logging
  - Configuration via TOML
  - Default port changed to 8815
