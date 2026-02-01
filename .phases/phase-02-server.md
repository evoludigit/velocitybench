# Phase 2: FraiseQL Server & Baseline Benchmarking

## Objective

Deploy fraiseql-server, establish pure FraiseQL performance baseline, and create infrastructure for framework overhead measurement.

## Success Criteria

- [ ] fraiseql-server deployed and running
- [ ] Baseline performance benchmarks established
- [ ] Pure FraiseQL metrics documented (latency, throughput, p99)
- [ ] Benchmark infrastructure ready for framework comparison
- [ ] Health checks and monitoring configured
- [ ] Database connection pooling validated

## TDD Cycles

### Cycle 1: Server Deployment & Configuration

**RED**: Test fraiseql-server starts and responds to health checks
```python
# tests/server/test_server_health.py
import os
import time
import requests
from subprocess import Popen
import pytest

@pytest.fixture(scope="session")
def fraiseql_server():
    """Start fraiseql-server for tests."""
    # Start server
    server = Popen(
        ["fraiseql-server"],
        env={
            **os.environ,
            "DATABASE_URL": os.getenv("TEST_DATABASE_URL"),
            "FRAISEQL_SCHEMA_PATH": "schema.compiled.json",
        }
    )

    # Wait for startup
    time.sleep(2)

    yield server

    # Cleanup
    server.terminate()
    server.wait()

def test_server_health_check(fraiseql_server):
    """Server must respond to health checks."""
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_server_introspection(fraiseql_server):
    """Server must support GraphQL introspection."""
    query = "{ __schema { types { name } } }"
    response = requests.post(
        "http://localhost:8000/graphql",
        json={"query": query}
    )
    assert response.status_code == 200
    assert "data" in response.json()
```

**GREEN**: Minimal server setup
```bash
#!/bin/bash
# scripts/start_server.sh
set -e

export DATABASE_URL="${DATABASE_URL:-postgresql://localhost/fraiseql_benchmark}"
export FRAISEQL_SCHEMA_PATH="schema.compiled.json"
export FRAISEQL_BIND_ADDR="0.0.0.0:8000"
export RUST_LOG=info

fraiseql-server
```

**REFACTOR**: Add configuration management, graceful shutdown

**CLEANUP**: Document startup procedure

---

### Cycle 2: Baseline Performance Benchmarking

**RED**: Establish FraiseQL baseline metrics
```python
# tests/benchmarks/test_fraiseql_baseline.py
import time
import statistics
import requests
from typing import List
import pytest

BASE_URL = "http://localhost:8000"

def measure_query_latency(query: str, iterations: int = 100) -> dict:
    """Measure latency for a GraphQL query."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        response = requests.post(
            f"{BASE_URL}/graphql",
            json={"query": query},
            timeout=10
        )
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        times.append(elapsed)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "p99": sorted(times)[int(len(times) * 0.99)],
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
    }

@pytest.mark.benchmark
class TestFraiseQLBaseline:
    def test_simple_query_latency(self):
        """Simple query baseline."""
        metrics = measure_query_latency("{ users { id } }", iterations=100)

        # Baseline expectations (adjust based on hardware)
        assert metrics["p99"] < 50, f"p99 too high: {metrics['p99']}ms"
        assert metrics["mean"] < 20, f"Mean too high: {metrics['mean']}ms"

        print(f"Simple Query: {metrics}")

    def test_nested_query_latency(self):
        """Nested query latency."""
        query = "{ posts { id author { id name } comments { id content } } }"
        metrics = measure_query_latency(query, iterations=50)

        assert metrics["p99"] < 100
        print(f"Nested Query: {metrics}")

    def test_filtered_query_latency(self):
        """Query with filters."""
        query = '{ posts(published: true) { id title } }'
        metrics = measure_query_latency(query, iterations=100)

        assert metrics["p99"] < 50
        print(f"Filtered Query: {metrics}")

    def test_mutation_latency(self):
        """Mutation latency."""
        mutation = 'mutation { createUser(name: "Bench", email: "bench@test.com") { id } }'
        metrics = measure_query_latency(mutation, iterations=50)

        assert metrics["p99"] < 100
        print(f"Mutation: {metrics}")

def test_throughput_baseline():
    """Measure requests per second."""
    import concurrent.futures
    import threading

    query = "{ users { id } }"
    duration_seconds = 5
    results = []
    errors = []

    def make_request():
        try:
            start = time.perf_counter()
            response = requests.post(
                f"{BASE_URL}/graphql",
                json={"query": query},
                timeout=5
            )
            elapsed = time.perf_counter() - start
            if response.status_code == 200:
                results.append(elapsed)
        except Exception as e:
            errors.append(e)

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        while time.time() - start_time < duration_seconds:
            executor.submit(make_request)

    throughput = len(results) / duration_seconds
    assert throughput > 100, f"Throughput too low: {throughput} req/s"
    print(f"Throughput: {throughput:.0f} req/s, Errors: {len(errors)}")
```

**GREEN**: Run benchmarks, capture baseline

**REFACTOR**: Add more query patterns, statistical analysis

**CLEANUP**: Generate baseline report

---

### Cycle 3: Concurrent Load Testing

**RED**: Verify server handles concurrent connections
```python
# tests/benchmarks/test_concurrent_load.py
import concurrent.futures
import time
import requests
import pytest

@pytest.mark.load
def test_concurrent_users(max_concurrent: int = 50):
    """Test with concurrent users."""
    query = "{ users { id name } }"
    errors = []
    latencies = []

    def request():
        try:
            start = time.perf_counter()
            response = requests.post(
                "http://localhost:8000/graphql",
                json={"query": query},
                timeout=10
            )
            elapsed = (time.perf_counter() - start) * 1000

            if response.status_code != 200:
                errors.append(response.status_code)
            else:
                latencies.append(elapsed)
        except Exception as e:
            errors.append(str(e))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = [executor.submit(request) for _ in range(max_concurrent * 10)]
        concurrent.futures.wait(futures)

    assert len(errors) == 0, f"Errors during concurrent load: {errors}"
    assert len(latencies) > max_concurrent * 8, "Too many failed requests"

    print(f"Concurrent load ({max_concurrent} users):")
    print(f"  Total requests: {len(latencies) + len(errors)}")
    print(f"  Successful: {len(latencies)}")
    print(f"  Failed: {len(errors)}")
    print(f"  Mean latency: {statistics.mean(latencies):.2f}ms")
```

**GREEN**: Run concurrent load tests

**REFACTOR**: Test at different concurrency levels (10, 50, 100, 200)

**CLEANUP**: Document results

---

### Cycle 4: Memory & Resource Profiling

**RED**: Baseline memory usage and resource efficiency
```python
# tests/benchmarks/test_resources.py
import requests
import psutil
import os

def test_server_memory_usage():
    """Measure server memory usage under load."""
    pid = os.getpid()  # In real test, would get fraiseql-server PID
    process = psutil.Process(pid)

    # Get baseline memory
    baseline_rss = process.memory_info().rss / 1024 / 1024  # MB

    # Make 1000 requests
    for _ in range(1000):
        requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ users { id } }"}
        )

    # Check memory didn't leak significantly
    after_rss = process.memory_info().rss / 1024 / 1024

    increase = after_rss - baseline_rss
    assert increase < 100, f"Memory increased by {increase}MB"

    print(f"Memory: {baseline_rss}MB → {after_rss}MB (Δ {increase}MB)")
```

**GREEN**: Profile memory usage

**REFACTOR**: Add CPU profiling, database connection analysis

**CLEANUP**: Document resource requirements

---

## Baseline Report Template

```markdown
# FraiseQL v2 Baseline Performance Report

## Environment
- OS: [Linux/macOS/Windows]
- Hardware: [CPU, RAM]
- Database: PostgreSQL [version]
- FraiseQL: v2.0.0-a1

## Query Patterns

### Simple Query: `{ users { id } }`
- Mean: X ms
- Median: X ms
- p99: X ms
- Throughput: X req/s

### Nested Query: `{ posts { author { id } } }`
- Mean: X ms
- p99: X ms

### Filtered Query: `{ posts(published: true) { id } }`
- Mean: X ms
- p99: X ms

### Mutation
- Mean: X ms
- p99: X ms

## Throughput
- Sustained: X req/s
- Burst (10 concurrent): X req/s
- Sustained (50 concurrent): X req/s

## Resource Usage
- Memory: X MB at idle, X MB under load
- CPU: X% under sustained load

## Key Findings
- [Observations]
- [Bottlenecks]
- [Recommendations]
```

## Deliverables

```
benchmarks/
├── fraiseql-direct/
│   ├── test_baseline.py
│   ├── test_concurrent_load.py
│   ├── test_resources.py
│   └── baseline_report.md
├── infrastructure/
│   ├── docker-compose.yml
│   ├── startup.sh
│   └── config.toml
└── reports/
    └── fraiseql_baseline_[date].md
```

## Dependencies

- Requires: Phase 1 (schema compiled)
- Blocks: Phase 3 (framework benchmarking)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- Baseline provides reference point for framework overhead calculation
- All subsequent framework measurements will be compared to this baseline
- Server configuration should be consistent across all measurements
- Load tests validate server reliability before framework integration
