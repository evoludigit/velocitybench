# ADR-009: Six-Dimensional QA Testing Strategy

**Status**: Accepted
**Date**: 2025-01-30
**Author**: VelocityBench Team

## Context

VelocityBench benchmarks 39 frameworks across 8 languages, each implementing the same API specification (REST and GraphQL). Ensuring consistency and correctness across all implementations is critical for:

1. **Benchmark Validity**: Performance comparisons are meaningless if implementations are incorrect
2. **API Contract**: All frameworks must return identical data for identical queries
3. **Database Integrity**: All frameworks must query the same underlying data correctly
4. **Query Correctness**: GraphQL N+1 problems must be detected and prevented
5. **Configuration Validation**: Framework configs must match specification
6. **Performance Regression**: Slowdowns must be caught before merging

Traditional testing (unit tests per framework) is insufficient because:
- Doesn't catch cross-framework inconsistencies
- Doesn't validate database query patterns
- Doesn't detect N+1 query problems
- Doesn't ensure configuration compliance

## Decision

**Implement a Six-Dimensional QA Testing Strategy that validates all 39 frameworks against the same comprehensive test suite.**

### The Six Dimensions

#### Dimension 1: Schema Validation

**Goal**: Ensure all frameworks expose the correct API schema (REST endpoints or GraphQL SDL)

**Location**: `tests/qa/validators/schema_validator.py`

**What It Tests**:
- REST: Correct endpoints exist (`/users`, `/posts/:id`, `/comments`)
- REST: Correct HTTP methods (GET, POST, PUT, DELETE)
- GraphQL: SDL matches expected schema (types, fields, arguments)
- GraphQL: Introspection query returns valid schema
- Both: Correct field types (String, Int, DateTime, etc.)

**Example**:
```python
# Schema validator checks GraphQL SDL
expected_schema = """
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
}
"""

actual_schema = await fetch_schema(framework_url)
assert_schema_equivalent(expected_schema, actual_schema)
```

#### Dimension 2: Query Validation

**Goal**: Ensure all frameworks return correct data for standard queries

**Location**: `tests/qa/validators/query_validator.py`

**What It Tests**:
- REST: `GET /users` returns all users
- REST: `GET /users/:id` returns correct user
- GraphQL: Simple queries return correct data
- GraphQL: Nested queries work (user -> posts -> comments)
- GraphQL: Arguments work (filtering, pagination)
- Both: Correct data types in responses
- Both: Null handling (optional vs required fields)

**Example**:
```python
# Query validator checks data correctness
response = await query_framework(
    framework_url,
    "{ user(id: 1) { id, name, email } }"
)

expected = {
    "id": "1",
    "name": "Alice Johnson",
    "email": "alice@example.com"
}

assert response["data"]["user"] == expected
```

#### Dimension 3: N+1 Query Detection

**Goal**: Detect and prevent N+1 query problems in GraphQL resolvers

**Location**: `tests/qa/validators/n1_detector.py`

**What It Tests**:
- Query count monitoring (using PostgreSQL logs)
- DataLoader usage validation
- Batch loading detection
- JOIN vs N+1 pattern detection

**Example**:
```python
# N+1 detector monitors database queries
with QueryCounter(db_connection) as counter:
    response = await query_framework(
        framework_url,
        "{ users { id, posts { id, title } } }"
    )

    # Should be O(1) queries, not O(N)
    assert counter.total_queries <= 3, \
        f"N+1 detected: {counter.total_queries} queries for {len(users)} users"
```

#### Dimension 4: Data Consistency Validation

**Goal**: Ensure all frameworks return identical data for identical queries

**Location**: `tests/qa/validators/consistency_validator.py`

**What It Tests**:
- Cross-framework response comparison
- Field-by-field equality
- Timestamp format consistency (ISO 8601)
- Null vs empty array consistency
- Sorting consistency (ORDER BY)

**Example**:
```python
# Consistency validator compares all frameworks
responses = await query_all_frameworks(
    "{ users { id, name, createdAt } }"
)

# All frameworks should return identical data
baseline = responses["fastapi-rest"]
for framework_name, response in responses.items():
    assert_deep_equal(
        baseline,
        response,
        f"{framework_name} differs from baseline"
    )
```

#### Dimension 5: Configuration Validation

**Goal**: Ensure all frameworks use correct configuration (database, ports, env vars)

**Location**: `tests/qa/validators/config_validator.py`

**What It Tests**:
- Correct database connection (right DB, not shared)
- Correct port binding (framework-specific port)
- Environment variable loading (.env files)
- Trinity Pattern usage (querying views, not tables)
- Connection pooling configuration

**Example**:
```python
# Config validator checks database usage
with DatabaseInspector(framework_db) as inspector:
    await query_framework(framework_url, "{ users { id } }")

    # Should query v_users (projection view), not tb_users (write table)
    assert "v_users" in inspector.queried_tables
    assert "tb_users" not in inspector.queried_tables
```

#### Dimension 6: Performance Baseline Validation

**Goal**: Catch performance regressions before they merge to main

**Location**: `tests/qa/validators/performance_validator.py`

**What It Tests**:
- Response time within expected range (p50, p95, p99)
- Throughput meets minimum threshold (RPS)
- Memory usage within limits
- Connection pool utilization
- Regression detection vs. baseline metrics

**Example**:
```python
# Performance validator checks against baseline
metrics = await benchmark_framework(framework_url, duration=10)

baseline = load_baseline(framework_name)

assert metrics.p95_latency < baseline.p95_latency * 1.5, \
    f"50% regression detected: {metrics.p95_latency}ms vs {baseline.p95_latency}ms"
```

### Testing Architecture

```
tests/qa/
├── validators/
│   ├── schema_validator.py          # Dimension 1
│   ├── query_validator.py           # Dimension 2
│   ├── n1_detector.py               # Dimension 3
│   ├── consistency_validator.py     # Dimension 4
│   ├── config_validator.py          # Dimension 5
│   └── performance_validator.py     # Dimension 6
├── test_rest_frameworks.py          # Tests for all REST frameworks
├── test_graphql_frameworks.py       # Tests for all GraphQL frameworks
├── test_cross_framework.py          # Cross-framework consistency
└── fixtures/
    ├── expected_schemas/            # Expected GraphQL SDL per framework
    ├── expected_responses/          # Expected JSON responses
    └── baselines/                   # Performance baselines
```

### Test Execution

```bash
# Run all QA tests
pytest tests/qa/

# Run specific dimension
pytest tests/qa/ -m schema
pytest tests/qa/ -m n1_detection

# Run for specific framework
pytest tests/qa/ --framework fastapi-rest

# Run cross-framework consistency tests
pytest tests/qa/test_cross_framework.py
```

## Consequences

### Positive

✅ **Comprehensive Validation**: All 6 dimensions ensure correctness
✅ **Early Bug Detection**: Catch issues before performance benchmarking
✅ **Cross-Framework Consistency**: Ensure all implementations are equivalent
✅ **N+1 Prevention**: Automatically detect query efficiency problems
✅ **Regression Prevention**: Performance baselines catch slowdowns
✅ **CI Integration**: All validations run on every PR
✅ **Confidence**: Benchmark results are trustworthy because implementations are correct

### Negative

❌ **Test Complexity**: 6 validators × 39 frameworks = high test maintenance
❌ **Test Runtime**: Running all validations takes ~10-15 minutes
❌ **Infrastructure**: Requires all 39 frameworks running simultaneously
❌ **Flakiness Risk**: Network and database state can cause false failures
❌ **Baseline Maintenance**: Performance baselines must be updated when infrastructure changes

## Alternatives Considered

### Alternative 1: Per-Framework Unit Tests Only

- **Approach**: Each framework has its own unit tests
- **Pros**: Simple, fast, framework-specific
- **Cons**:
  - No cross-framework consistency checking
  - Doesn't validate N+1 problems
  - Doesn't ensure API contract compliance
- **Rejected**: Insufficient for multi-framework benchmarking

### Alternative 2: Schema-Only Validation

- **Approach**: Only validate GraphQL schema, trust data is correct
- **Pros**: Fast, low complexity
- **Cons**:
  - Doesn't catch data bugs
  - Doesn't detect N+1 problems
  - Doesn't validate configuration
- **Rejected**: Too narrow, misses critical bugs

### Alternative 3: Contract Testing (Pact)

- **Approach**: Use Pact or similar contract testing framework
- **Pros**: Industry standard, good tooling
- **Cons**:
  - Designed for consumer/provider, not multi-implementation validation
  - Doesn't handle N+1 detection
  - Adds dependency on external tooling
- **Rejected**: Not designed for our use case

### Alternative 4: Manual Testing

- **Approach**: Human QA engineer manually tests each framework
- **Pros**: Flexible, can catch UX issues
- **Cons**:
  - Slow, error-prone, not scalable to 39 frameworks
  - No automation, no CI integration
- **Rejected**: Not sustainable for 39 frameworks

## Related Decisions

- **ADR-001**: Trinity Pattern - Config validator ensures views are used correctly
- **ADR-002**: Framework Isolation - Each framework's database is tested independently
- **ADR-010**: Benchmarking Methodology - QA validation precedes performance benchmarking

## Implementation Status

✅ **Complete** - All 6 validators implemented and integrated into CI

## CI Integration

The six-dimensional QA strategy runs on every PR:

```yaml
# .github/workflows/qa-validation.yml
qa-tests:
  strategy:
    matrix:
      dimension: [schema, query, n1, consistency, config, performance]
  steps:
    - name: Start all frameworks
      run: docker-compose up -d

    - name: Run ${{ matrix.dimension }} validation
      run: pytest tests/qa/ -m ${{ matrix.dimension }}

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: qa-${{ matrix.dimension }}-results
```

## References

- [tests/qa/README.md](../../tests/qa/README.md) - QA testing guide
- [GraphQL N+1 Problem](https://www.apollographql.com/blog/backend/performance/batching-and-caching/) - Background on N+1 detection
- [Contract Testing](https://pact.io/) - Alternative approach
- [ADR-001](001-trinity-pattern.md) - Trinity Pattern validation in Dimension 5
