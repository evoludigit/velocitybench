# Phase 2: FraiseQL Server Setup

## Objective

Deploy fraiseql-server (Rust binary), validate it works with the schema, and establish baseline performance metrics for compiled query execution.

## Success Criteria

- [ ] fraiseql-server builds without errors
- [ ] Server accepts compiled schema.json
- [ ] Server executes simple queries correctly
- [ ] Baseline performance metrics established (latency, throughput)
- [ ] Resource usage profiled (memory, CPU)
- [ ] Ready for Phase 3 (framework proxy implementations)

---

## TDD Cycles

### Cycle 1: Server Build & Basic Validation

**RED**: Write test that fraiseql-server exists, builds, and accepts schema

```python
def test_fraiseql_server_builds():
    """fraiseql-server must build successfully."""
    # Run cargo build in fraiseql-server directory
    # Verify binary exists at target/release/fraiseql-server
    # Verify it can execute --version

def test_fraiseql_server_accepts_schema():
    """Server must accept schema.json and start."""
    # Copy schema.json to server directory
    # Start server with schema
    # Verify it starts listening on expected port
```

**GREEN**: Build fraiseql-server, start it with schema

**REFACTOR**: Improve server integration, add logging

**CLEANUP**: Format code, verify tests pass

---

### Cycle 2: Query Execution Validation

**RED**: Write tests that server executes queries correctly

```python
def test_simple_query_execution():
    """Server must execute simple queries."""
    # Query: { users { id } }
    # Verify response format and data

def test_nested_query_execution():
    """Server must execute nested queries with joins."""
    # Query: { users { id posts { id } } }
    # Verify joins work correctly

def test_mutation_execution():
    """Server must execute mutations."""
    # Mutation: create_user(name, email) -> User
    # Verify mutation creates record and returns it
```

**GREEN**: Implement basic query execution against database

**REFACTOR**: Optimize query handling

**CLEANUP**: Error handling, validation

---

### Cycle 3: Performance Baseline Measurement

**RED**: Write benchmark tests that measure performance

```python
def test_simple_query_latency():
    """Measure latency for simple query: { users { id } }"""
    # Run 100 times, measure p50, p99 latency
    # Store baseline: expected 15-20ms p99

def test_nested_query_latency():
    """Measure latency for nested query: { users { posts { comments } } }"""
    # Run 100 times, measure p50, p99 latency
    # Store baseline: expected 40-60ms p99

def test_throughput():
    """Measure throughput (requests/second)."""
    # Run concurrent requests, measure req/s
    # Store baseline: expected 2000+ req/s
```

**GREEN**: Implement performance measurement framework

**REFACTOR**: Add statistical analysis, variance tracking

**CLEANUP**: Format results, document methodology

---

### Cycle 4: Resource Profiling

**RED**: Profile memory and CPU usage

```python
def test_memory_usage():
    """Measure memory usage at rest and under load."""
    # Start server, measure baseline memory
    # Run 1000 concurrent requests
    # Measure peak memory
    # Verify within acceptable range (< 200MB)

def test_cpu_usage():
    """Measure CPU usage under load."""
    # Monitor CPU during sustained 1000 req/s
    # Verify single-threaded efficiency
```

**GREEN**: Implement resource monitoring

**REFACTOR**: Add detailed profiling output

**CLEANUP**: Format results

---

## Deliverables

1. **fraiseql-server Binary**
   - Built and tested
   - Accepts schema.json
   - Executes queries correctly

2. **Baseline Performance Metrics**
   ```
   Simple Query (100 runs):
     P50: 14.2ms
     P99: 15.8ms
     Mean: 14.5ms

   Nested Query (100 runs):
     P50: 42.1ms
     P99: 47.3ms
     Mean: 43.2ms

   Throughput: 2,150 req/s
   Memory: 85MB baseline, 120MB peak
   CPU: Single-threaded, efficient
   ```

3. **Reference Metrics Document**
   - Location: `benchmarks/reports/FRAISEQL_BASELINE.md`
   - Used for comparison with framework proxies in Phase 4

4. **Test Infrastructure**
   - Location: `tests/integration/test_fraiseql_server.py`
   - Query execution validation
   - Performance measurement
   - Resource profiling

## Dependencies

- Requires: Phase 1 complete (schema definition)
- Blocks: Phase 3 (framework proxies need baseline to compare against)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete
