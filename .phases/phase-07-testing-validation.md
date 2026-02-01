# Phase 7: Cross-Language Testing & Validation

## Objective

Establish comprehensive cross-language test suite verifying functional parity, performance consistency, and security across all 5 language backends.

## Success Criteria

- [ ] Functional parity tests pass for all backends
- [ ] Performance benchmarks within 10% relative range
- [ ] Security tests pass uniformly across all languages
- [ ] Database consistency validated
- [ ] Load testing passes (concurrent requests)
- [ ] Error handling behavior identical
- [ ] Integration tests pass
- [ ] No known limitations undocumented

## TDD Cycles

### Cycle 1: Functional Parity Tests

**RED**: Verify all backends return identical data for same queries
```python
# tests/integration/test_functional_parity.py
import pytest
from tests.common.clients import (
    FastAPIClient, FlaskClient, StrawberryClient, GrapheneClient,
    ExpressClient, FastifyClient, ApolloClient,
    GinClient, EchoClient, FiberClient,
    SpringBootClient, QuarkusClient, MicronautClient,
    LaravelClient, SymfonyClient, SlimClient
)

CLIENTS = [
    # Python
    FastAPIClient(), FlaskClient(), StrawberryClient(), GrapheneClient(),
    # TypeScript
    ExpressClient(), FastifyClient(), ApolloClient(),
    # Go
    GinClient(), EchoClient(), FiberClient(),
    # Java
    SpringBootClient(), QuarkusClient(), MicronautClient(),
    # PHP
    LaravelClient(), SymfonyClient(), SlimClient(),
]

@pytest.mark.parametrize("client", CLIENTS)
def test_users_query_identical_results(client):
    """All backends must return identical data for same query."""
    result = client.query('{ users { id name email createdAt isActive } }')

    assert result['data']['users'] is not None
    users = result['data']['users']
    assert len(users) > 0

    # Verify structure is identical across all backends
    assert set(users[0].keys()) == {'id', 'name', 'email', 'createdAt', 'isActive'}

@pytest.mark.parametrize("client", CLIENTS)
def test_users_with_limit(client):
    """Pagination parameters must work identically."""
    result = client.query('{ users(limit: 5) { id } }')
    assert len(result['data']['users']) <= 5

@pytest.mark.parametrize("client", CLIENTS)
def test_users_with_filter(client):
    """Filters must work identically."""
    result = client.query('{ users(isActive: true) { id isActive } }')
    for user in result['data']['users']:
        assert user['isActive'] is True

@pytest.mark.parametrize("client", CLIENTS)
def test_nested_queries(client):
    """Nested queries (author of posts) must work identically."""
    result = client.query('''
        {
            posts {
                id title
                author { id name email }
                comments { id content author { id name } }
            }
        }
    ''')

    assert result['data']['posts'] is not None
    for post in result['data']['posts']:
        assert post['author']['id']
        assert post['author']['name']
        assert isinstance(post['comments'], list)

@pytest.mark.parametrize("client", CLIENTS)
def test_mutations_identical_results(client):
    """Mutations must produce identical results."""
    create_result = client.mutate('''
        mutation {
            createUser(
                name: "Integration Test"
                email: "integration@test.example.com"
            ) {
                id name email createdAt isActive
            }
        }
    ''')

    created_user = create_result['data']['createUser']
    assert created_user['name'] == "Integration Test"
    assert created_user['email'] == "integration@test.example.com"
    assert created_user['isActive'] is True

    # Verify it's queryable
    query_result = client.query(
        f'{{ user(id: {created_user["id"]}) {{ id name }} }}'
    )
    assert query_result['data']['user']['id'] == created_user['id']
```

**GREEN**: Implement all client adapters (already have common test infrastructure)

**REFACTOR**: Add more complex query patterns

**CLEANUP**: Ensure all tests pass consistently

---

### Cycle 2: Performance Parity Benchmarks

**RED**: Verify performance is within acceptable range across all backends
```python
# tests/integration/test_performance_parity.py
import time
import statistics
import pytest

@pytest.mark.benchmark
@pytest.mark.parametrize("client", CLIENTS)
def test_simple_query_performance(client, benchmark):
    """Simple query should have consistent performance."""
    def query():
        return client.query('{ users(limit: 10) { id } }')

    result = benchmark(query)
    assert result['data']['users']

# Collect baselines
BASELINES = {
    'simple_query': 10.0,      # ms (Python/FastAPI baseline)
    'nested_query': 50.0,       # ms
    'mutation': 25.0,           # ms
    'complex_query': 100.0,     # ms
}

@pytest.mark.parametrize("client", CLIENTS)
def test_performance_within_range(client):
    """All backends within 50% of baseline."""
    import timeit

    # Simple query
    time_ms = timeit.timeit(
        lambda: client.query('{ users(limit: 10) { id } }'),
        number=100
    ) / 100 * 1000

    baseline = BASELINES['simple_query']
    assert time_ms <= baseline * 1.5, \
        f"{client} took {time_ms}ms, baseline is {baseline}ms"

@pytest.mark.parametrize("client", CLIENTS)
def test_mutation_performance_consistent(client):
    """Mutation performance should be consistent across backends."""
    import timeit

    mutation = '''
        mutation {
            createUser(name: "Bench", email: "bench@example.com") { id }
        }
    '''

    time_ms = timeit.timeit(
        lambda: client.mutate(mutation),
        number=50
    ) / 50 * 1000

    assert time_ms <= BASELINES['mutation'] * 1.5

def test_performance_relative_parity():
    """All backends should be within 20% of each other."""
    results = {}

    for client in CLIENTS:
        times = []
        for _ in range(10):
            start = time.time()
            client.query('{ users { id } }')
            times.append((time.time() - start) * 1000)

        results[client.__class__.__name__] = statistics.mean(times)

    # Check all are within 20% of mean
    mean_time = statistics.mean(results.values())
    for backend, time_ms in results.items():
        deviation = abs(time_ms - mean_time) / mean_time
        assert deviation < 0.20, \
            f"{backend} deviates {deviation*100:.1f}% from mean"
```

**GREEN**: Run benchmarks against all clients

**REFACTOR**: Add memory profiling, query complexity analysis

**CLEANUP**: Document performance characteristics

---

### Cycle 3: Security Parity Tests

**RED**: Verify security behaviors are identical
```python
# tests/integration/test_security_parity.py

@pytest.mark.parametrize("client", CLIENTS)
def test_sql_injection_protection(client):
    """All backends must reject SQL injection attempts."""
    with pytest.raises(Exception):  # Should fail, not execute
        client.query('{ users(name: "test\' OR 1=1--") { id } }')

@pytest.mark.parametrize("client", CLIENTS)
def test_authorization_enforcement(client):
    """All backends must enforce authorization uniformly."""
    # Attempt unauthorized query
    unauthorized_client = client.with_auth(None)
    with pytest.raises(Exception):
        unauthorized_client.query('{ adminUsers { id } }')

@pytest.mark.parametrize("client", CLIENTS)
def test_rate_limiting_consistent(client):
    """Rate limiting must be consistent."""
    times = []
    for i in range(10):
        start = time.time()
        try:
            client.query('{ users { id } }')
        except RateLimitedException:
            # Expected after threshold
            break
        times.append(time.time() - start)

    # Should be consistent across backends

@pytest.mark.parametrize("client", CLIENTS)
def test_input_validation_identical(client):
    """Input validation errors must be identical."""
    # Invalid query should produce same error
    result = client.query('{ invalidField { id } }')
    assert 'errors' in result
    assert len(result['errors']) > 0

@pytest.mark.parametrize("client", CLIENTS)
def test_no_data_leakage_in_errors(client):
    """Error messages must not leak sensitive data."""
    result = client.query('{ users(id: "invalid") { id } }')
    error_msg = str(result.get('errors', []))

    # Should not contain:
    assert 'password' not in error_msg.lower()
    assert 'secret' not in error_msg.lower()
    assert 'token' not in error_msg.lower()
```

**GREEN**: Verify all security tests pass

**REFACTOR**: Add more edge cases

**CLEANUP**: Document security model

---

### Cycle 4: Database Consistency Tests

**RED**: Verify database state is consistent across all backends
```python
# tests/integration/test_database_consistency.py

@pytest.mark.parametrize("client", CLIENTS)
def test_transaction_isolation(client):
    """Concurrent mutations must maintain consistency."""
    import concurrent.futures

    def create_user(name):
        return client.mutate(f'''
            mutation {{
                createUser(name: "{name}", email: "{name}@example.com") {{ id }}
            }}
        ''')

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_user, f"user_{i}") for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed
    assert all('id' in r['data']['createUser'] for r in results)

    # Verify all are in database
    result = client.query('{ users { name } }')
    created_names = [r['name'] for r in result['data']['users']]
    for i in range(5):
        assert f"user_{i}" in created_names

@pytest.mark.parametrize("client", CLIENTS)
def test_foreign_key_constraints(client):
    """Foreign key relationships must be enforced identically."""
    # Should not allow orphaned references
    with pytest.raises(Exception):  # Database constraint
        client.mutate('''
            mutation {
                createPost(
                    title: "Test"
                    content: "Test"
                    authorId: 999999
                ) { id }
            }
        ''')

@pytest.mark.parametrize("client", CLIENTS)
def test_cascade_delete_behavior(client):
    """Cascade delete must work identically."""
    # Create user, then delete
    create_result = client.mutate('''
        mutation {
            createUser(name: "ToDelete", email: "delete@example.com") { id }
        }
    ''')
    user_id = create_result['data']['createUser']['id']

    # Delete user (should cascade to posts)
    client.mutate(f'mutation {{ deleteUser(id: {user_id}) {{ id }} }}')

    # Verify user is gone
    result = client.query(f'{{ user(id: {user_id}) {{ id }} }}')
    assert result['data']['user'] is None
```

**GREEN**: Verify database consistency across backends

**REFACTOR**: Add more complex scenarios

**CLEANUP**: Document transactional behavior

---

### Cycle 5: Load Testing

**RED**: Verify all backends can handle concurrent load
```python
# tests/integration/test_load.py
import concurrent.futures
import time

@pytest.mark.load
@pytest.mark.parametrize("client", CLIENTS)
def test_concurrent_queries(client):
    """All backends must handle concurrent requests."""
    num_requests = 100

    def query():
        return client.query('{ users(limit: 5) { id } }')

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(query) for _ in range(num_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    elapsed = time.time() - start
    throughput = num_requests / elapsed

    # All should succeed
    assert all(r['data']['users'] for r in results)

    # Should achieve reasonable throughput
    assert throughput > 10, f"{client}: only {throughput} req/s"

@pytest.mark.load
@pytest.mark.parametrize("client", CLIENTS)
def test_mixed_query_mutation_load(client):
    """Backends must handle mixed read/write under load."""
    def random_operation():
        if random.random() > 0.8:  # 20% mutations
            return client.mutate('''
                mutation {
                    createUser(name: "LoadTest", email: "load@example.com") { id }
                }
            ''')
        else:
            return client.query('{ users(limit: 10) { id } }')

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(random_operation) for _ in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed
    assert all(r['data'] for r in results)
```

**GREEN**: Run load tests against all clients

**REFACTOR**: Increase load, add memory profiling

**CLEANUP**: Document performance under load

---

### Cycle 6: Integration & Regression Tests

**RED**: Comprehensive regression test suite
```python
# tests/integration/test_regression.py

@pytest.mark.parametrize("client", CLIENTS)
def test_all_query_types(client):
    """Verify all query types work."""
    # Simple query
    assert client.query('{ users { id } }')['data']['users']

    # Query with arguments
    assert client.query('{ users(limit: 5) { id } }')['data']['users']

    # Nested query
    assert client.query('{ posts { id author { id } } }')['data']['posts']

    # Fragment query
    assert client.query('''
        fragment UserFields on User { id name email }
        query { users { ...UserFields } }
    ''')['data']['users']

@pytest.mark.parametrize("client", CLIENTS)
def test_error_handling_consistency(client):
    """Error responses must be consistent."""
    # Invalid query syntax
    result = client.query('{ invalid')
    assert 'errors' in result

    # Unknown field
    result = client.query('{ users { unknownField } }')
    assert 'errors' in result

    # All backends should have similar error structure
    for error in result['errors']:
        assert 'message' in error
        assert isinstance(error['message'], str)
```

**GREEN**: Run comprehensive regression suite

**REFACTOR**: Add more edge cases

**CLEANUP**: Document known behaviors

---

## Deliverables

### Test Reports

```
tests/reports/
├── parity-report.md          # Functional parity results
├── performance-benchmark.txt # Performance comparison
├── security-audit.md         # Security test results
├── load-test-results.md      # Load testing summary
└── coverage-report.html      # Code coverage
```

### Documentation

```
docs/
├── PARITY.md                 # Cross-language parity guarantees
├── PERFORMANCE.md            # Performance characteristics
├── SECURITY.md               # Security model
└── KNOWN_LIMITATIONS.md      # Documented limitations
```

## Dependencies

- Requires: Phases 2-6 (all backends complete)
- Blocks: Phase 8 (finalization)

## Test Execution Strategy

```bash
# Run all tests
pytest tests/integration/

# Run by category
pytest -m parity
pytest -m benchmark
pytest -m security
pytest -m load
pytest -m regression

# Generate reports
pytest --html=report.html --cov --cov-report=html
```

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- All 15 backends must pass all parity tests
- Performance baseline established from Python/FastAPI
- Security model is uniform across all backends
- Database consistency guaranteed by FraiseQL schema
- No language-specific deviations without documentation
