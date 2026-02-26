# Framework QA Validation System

Comprehensive multi-dimensional validation system for all 23 framework implementations in the FraiseQL performance assessment project.

## Overview

This QA system validates frameworks across **6 dimensions**:

1. **Schema Validation** - Verifies correct database table references
2. **Query Validation** - Tests all GraphQL/REST queries work correctly
3. **N+1 Detection** - Identifies N+1 query anti-patterns
4. **Data Consistency** - Ensures all frameworks return identical data
5. **Config Validation** - Verifies connection pools, health checks, metrics
6. **Performance Sanity** - Detects broken/timing-out implementations

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full validation
python -m tests.qa.framework_validator

# View results
cat reports/qa-verification-YYYY-MM-DD.md
```

## Architecture

```
tests/qa/
├── framework_validator.py          # Main orchestrator
├── schema_validator.py             # Database schema validation
├── query_validator.py              # Query correctness validation
├── n1_detector.py                  # N+1 query detection
├── data_consistency_validator.py   # Cross-framework data comparison
├── config_validator.py             # Configuration validation
├── performance_validator.py        # Performance sanity checks
├── framework_registry.yaml         # Framework metadata
├── validation_config.yaml          # Validation rules/thresholds
└── fixtures/
    ├── test_queries.json           # Standard test queries
    ├── expected_responses.json     # Expected response shapes
    └── test_mutations.json         # Mutation tests
```

## Individual Validators

### Schema Validator

Verifies database schema consistency:

```bash
python -m tests.qa.schema_validator
```

**Checks**:
- All referenced tables exist in database
- Tables have expected columns
- Foreign keys are defined
- Indexes exist on foreign keys

**Detects**:
- ❌ FastAPI REST references `benchmark.users` instead of `benchmark.tv_user`
- ❌ Framework references non-existent tables
- ⚠️ Missing indexes on foreign key columns

### Query Validator

Tests all GraphQL/REST queries:

```bash
python -m tests.qa.query_validator
```

**Checks**:
- `ping` query returns "pong"
- `user(id)` query returns user data
- `users(limit)` query returns list
- Nested queries work (`user.posts`, `post.author`)
- Deep nested queries work (`post.comments.author`)
- Mutations work and return updated data

**Detects**:
- ❌ async-graphql returns null for all queries (broken)
- ❌ Framework doesn't support required queries
- ⚠️ Framework returns different field names

### N+1 Detector

Detects N+1 query anti-patterns:

```bash
python -m tests.qa.n1_detector
```

**Test Cases**:
1. **users_with_posts**: Fetch 10 users with their posts
   - Expected: 2 queries (1 users + 1 batched posts)
   - N+1 pattern: 11 queries (1 users + 10 individual post queries)

2. **posts_with_authors**: Fetch 10 posts with authors
   - Expected: 2 queries (1 posts + 1 batched authors)
   - N+1 pattern: 11 queries

3. **posts_with_comments_and_authors**: Fetch 10 posts with comments and authors
   - Expected: 3 queries (1 posts + 1 batched comments + 1 batched authors)
   - N+1 pattern: 20+ queries

**Uses**: PostgreSQL `pg_stat_statements` to monitor actual queries executed

### Data Consistency Validator

Compares data across frameworks:

```bash
python -m tests.qa.data_consistency_validator
```

**Checks**:
- Same query against all frameworks returns identical data
- Field naming is consistent (camelCase for GraphQL)
- Null handling is consistent
- List ordering is deterministic

**Detects**:
- ❌ Framework returns different data than baseline
- ⚠️ Framework uses different field names
- ⚠️ Framework returns data in different order

### Config Validator

Validates framework configurations:

```bash
python -m tests.qa.config_validator
```

**Checks**:
- Health endpoint returns 200 with `{"status": "healthy"}`
- Metrics endpoint (Prometheus) accessible
- Database connection working
- Connection pool configured correctly

**Detects**:
- ❌ Framework not running (health check fails)
- ❌ Cannot connect to database
- ⚠️ Metrics endpoint missing
- ⚠️ Pool configuration differs from registry

### Performance Validator

Basic performance sanity checks:

```bash
python -m tests.qa.performance_validator
```

**NOT comprehensive benchmarking** - just sanity checks to detect broken implementations.

**Checks**:
- Ping query < 100ms
- Simple queries < 500ms
- Complex queries < 2s
- Timeout rate < 1%

**Detects**:
- ❌ Framework times out on all requests (broken)
- ❌ Framework >10x slower than median (likely broken)
- ⚠️ Framework 3-10x slower than median (investigate)

## Framework Registry

All frameworks are registered in `framework_registry.yaml`:

```yaml
frameworks:
  - name: fraiseql
    language: python
    type: graphql
    port: 4000
    endpoint: /graphql
    health_check: /health
    metrics_endpoint: /metrics
    expected_tables:
      - benchmark.tv_user
      - benchmark.tv_post
      - benchmark.tv_comment
    pool_config:
      min: 20
      max: 30
    features:
      dataloader: native
      statement_caching: true
```

To add a new framework, add entry to registry and re-run validation.

## Validation Config

Configuration and thresholds in `validation_config.yaml`:

```yaml
thresholds:
  performance:
    ping_query_max_ms: 100
    simple_query_max_ms: 500
    complex_query_max_ms: 2000
    max_timeout_rate: 0.01

  n1_queries:
    max_query_multiplier: 1.5

baseline_framework: fraiseql  # Used for data consistency comparison
```

## Output Reports

### Markdown Report

Human-readable report: `reports/qa-verification-YYYY-MM-DD.md`

```markdown
# Framework Validation Report

**Generated**: 2024-01-15T10:30:00Z
**Total Frameworks**: 23

## Summary
- ✅ Pass: 18
- ⚠️ Warning: 3
- ❌ Fail: 1
- 🚨 Broken: 1

### 🚨 Broken Frameworks
- async-graphql (Rust GraphQL) - No queries implemented

### ❌ Failing Frameworks
- fastapi-rest (Python REST) - Wrong table names

## Individual Framework Results

### ✅ fraiseql (python - graphql)
**Overall Status**: PASS

**Schema Validation**: pass
**Query Support**: 10/10 queries passing
**N+1 Queries**: ✅ None detected
**Performance**: Ping 5.2ms avg, 0.0% timeout rate
```

### JSON Report

Machine-readable report: `reports/qa-verification-YYYY-MM-DD.json`

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "total_frameworks": 23,
  "summary": {
    "status_breakdown": {
      "pass": 18,
      "warning": 3,
      "fail": 1,
      "broken": 1
    }
  },
  "frameworks": {
    "fraiseql": {
      "overall_status": "pass",
      "checks": { ... }
    }
  }
}
```

## Status Levels

Frameworks are classified into 4 status levels:

1. **✅ PASS**: All checks pass, ready for benchmarking
2. **⚠️ WARNING**: Minor issues, functional but needs review
3. **❌ FAIL**: Critical issues, needs fixes before benchmarking
4. **🚨 BROKEN**: Not running or completely non-functional

## Exit Codes

- `0`: All frameworks pass (warnings OK)
- `1`: Some frameworks fail validation
- `2`: Some frameworks are broken (not running)

## CI/CD Integration

```yaml
# .github/workflows/framework-qa.yml
name: Framework QA
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start all frameworks
        run: docker-compose up -d
      - name: Run QA validation
        run: python -m tests.qa.framework_validator
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: validation-results
          path: reports/qa-verification-*.json
```

## Development Workflow

### Adding a New Framework

1. Implement framework in `frameworks/{name}/`
2. Add entry to `framework_registry.yaml`
3. Run validation: `python -m tests.qa.framework_validator`
4. Fix any failing checks
5. Re-run until status is PASS

### Adding a New Validation Check

1. Create validator module in `tests/qa/`
2. Implement validation logic
3. Add to `FrameworkValidator._validate_framework()`
4. Update `validation_config.yaml` with thresholds
5. Update documentation

## Troubleshooting

### Framework shows as BROKEN

Check:
```bash
# Is framework running?
curl http://localhost:{port}/health

# Check logs
docker-compose logs {framework-name}

# Try starting manually
cd frameworks/{framework-name}
./start.sh
```

### N+1 detector not working

Requires PostgreSQL extension:
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

### Data consistency fails

Compare responses manually:
```bash
# Query FraiseQL (baseline)
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { user(id: \"...\") { id username } }"}'

# Query other framework
curl -X POST http://localhost:8001/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { user(id: \"...\") { id username } }"}'

# Compare outputs
```

## Dependencies

```txt
# requirements.txt
asyncpg>=0.29.0
httpx>=0.25.0
pyyaml>=6.0
deepdiff>=6.7.0
psutil>=5.9.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

## Future Enhancements

- [ ] Add load testing capabilities
- [ ] Add memory leak detection
- [ ] Add database connection leak detection
- [ ] Add GraphQL schema validation (SDL comparison)
- [ ] Add OpenAPI spec validation for REST APIs
- [ ] Add security scanning (SQL injection, XSS)
- [ ] Add accessibility testing for GraphQL playground
- [ ] Add container health monitoring
- [ ] Add database query plan analysis
- [ ] Add cache hit rate monitoring

## Contributing

To add new validators:

1. Create validator class with consistent interface
2. Implement async validation methods
3. Return standardized result format: `{'status': 'pass'|'fail', 'issues': []}`
4. Add to main orchestrator
5. Update documentation
6. Add tests for validator itself

## License

MIT License - See project root LICENSE file
