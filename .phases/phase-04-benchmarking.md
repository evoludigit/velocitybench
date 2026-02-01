# Phase 4: Benchmark Suite & Framework Overhead Analysis

## Objective

Measure framework overhead by comparing pure FraiseQL performance (Phase 2 baseline) with framework-proxied performance, establishing language-specific costs.

## Success Criteria

- [ ] Framework overhead measured for all 5 languages
- [ ] Overhead < 10ms for simple queries (target)
- [ ] Overhead consistent across query patterns
- [ ] Memory usage profiled per framework
- [ ] CPU usage profiled per framework
- [ ] Comparison report generated
- [ ] Bottlenecks identified

## Benchmark Methodology

### Setup
1. FraiseQL server running at localhost:8000
2. All 5 frameworks running simultaneously
3. Same test query set
4. Same database state
5. Minimum 100 iterations per test

### Formula
```
Framework Overhead = (Framework Latency) - (FraiseQL Baseline Latency)
```

### Test Queries

**Query 1: Simple (baseline)**
```graphql
{ users { id } }
```

**Query 2: Nested**
```graphql
{ posts { id author { id name } } }
```

**Query 3: Filtered**
```graphql
{ posts(published: true) { id title } }
```

**Query 4: Mutation**
```graphql
mutation { createUser(name: "Benchmark", email: "bench@example.com") { id } }
```

## TDD Cycles

### Cycle 1: Unified Benchmark Framework

**RED**: Test harness compares all frameworks fairly
```python
# benchmarks/test_framework_comparison.py
from typing import List, Dict
import time
import statistics
import requests

class FrameworkBenchmark:
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.results = {}

    def run_query(self, query: str, iterations: int = 100) -> Dict:
        """Run query and return latency statistics."""
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": query},
                timeout=10
            )
            elapsed = (time.perf_counter() - start) * 1000

            assert response.status_code == 200
            times.append(elapsed)

        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "p99": sorted(times)[int(len(times) * 0.99)],
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        }

def test_framework_parity():
    """All frameworks execute same queries correctly."""
    frameworks = [
        FrameworkBenchmark("FastAPI", "http://localhost:8001"),
        FrameworkBenchmark("Express", "http://localhost:8002"),
        FrameworkBenchmark("Gin", "http://localhost:8003"),
        FrameworkBenchmark("Spring Boot", "http://localhost:8004"),
        FrameworkBenchmark("Laravel", "http://localhost:8005"),
    ]

    query = "{ users { id } }"

    for fw in frameworks:
        result = fw.run_query(query, iterations=100)
        assert result["mean"] < 100, f"{fw.name} latency too high"
        print(f"{fw.name}: {result['mean']:.2f}ms (p99: {result['p99']:.2f}ms)")
```

**GREEN**: Run benchmarks for all frameworks

**REFACTOR**: Add statistical comparison, overhead calculation

**CLEANUP**: Format results

---

### Cycle 2: Overhead Calculation & Analysis

**RED**: Calculate and report framework overhead
```python
def test_framework_overhead():
    """Calculate overhead vs FraiseQL baseline."""
    fraiseql_baseline = {
        "simple": 15.2,      # ms (from Phase 2)
        "nested": 45.1,
        "filtered": 18.3,
        "mutation": 52.0,
    }

    frameworks = {
        "FastAPI": "http://localhost:8001",
        "Express": "http://localhost:8002",
        "Gin": "http://localhost:8003",
        "Spring Boot": "http://localhost:8004",
        "Laravel": "http://localhost:8005",
    }

    overhead_report = {}

    for name, url in frameworks.items():
        fw = FrameworkBenchmark(name, url)

        overhead_report[name] = {
            "simple": fw.run_query("{ users { id } }")["mean"] - fraiseql_baseline["simple"],
            "nested": fw.run_query("{ posts { author { id } } }")["mean"] - fraiseql_baseline["nested"],
            "filtered": fw.run_query("{ posts(published: true) { id } }")["mean"] - fraiseql_baseline["filtered"],
            "mutation": fw.run_query(
                'mutation { createUser(name: "B", email: "b@test.com") { id } }'
            )["mean"] - fraiseql_baseline["mutation"],
        }

    # Verify overhead is reasonable (< 10ms target)
    for name, queries in overhead_report.items():
        for query_type, overhead_ms in queries.items():
            assert overhead_ms < 15, f"{name} {query_type} overhead too high: {overhead_ms}ms"
            print(f"{name:15} {query_type:10} overhead: {overhead_ms:6.2f}ms")

    return overhead_report
```

**GREEN**: Analyze and report overhead per framework

**REFACTOR**: Add graphical comparisons

**CLEANUP**: Document findings

---

### Cycle 3: Memory & CPU Profiling

**RED**: Profile resource usage per framework
```python
import psutil
import subprocess
from typing import Tuple

def profile_framework(
    framework_name: str,
    startup_cmd: str,
    port: int,
    duration_seconds: int = 60
) -> Dict:
    """Profile framework resource usage."""
    # Start framework
    process = subprocess.Popen(
        startup_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(2)  # Let it start

    try:
        ps_process = psutil.Process(process.pid)

        # Get baseline
        baseline_memory_mb = ps_process.memory_info().rss / 1024 / 1024
        baseline_cpu = ps_process.cpu_num()

        # Run load
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            requests.post(
                f"http://localhost:{port}/graphql",
                json={"query": "{ users { id } }"},
                timeout=5
            )

        # Get peak
        peak_memory_mb = ps_process.memory_info().rss / 1024 / 1024
        cpu_percent = ps_process.cpu_percent(interval=1)

        return {
            "baseline_memory_mb": baseline_memory_mb,
            "peak_memory_mb": peak_memory_mb,
            "memory_increase_mb": peak_memory_mb - baseline_memory_mb,
            "cpu_percent": cpu_percent,
        }

    finally:
        process.terminate()

def test_resource_usage():
    """Profile all frameworks."""
    frameworks = {
        "FastAPI": ("uvicorn app:app --port 8001", 8001),
        "Express": ("npm start -- --port 8002", 8002),
        # ... etc
    }

    for name, (cmd, port) in frameworks.items():
        metrics = profile_framework(name, cmd, port)
        print(f"{name}:")
        print(f"  Memory: {metrics['baseline_memory_mb']:.0f}MB → {metrics['peak_memory_mb']:.0f}MB")
        print(f"  CPU: {metrics['cpu_percent']:.1f}%")
```

**GREEN**: Profile memory and CPU usage

**REFACTOR**: Add sustained load profiling

**CLEANUP**: Document resource requirements

---

### Cycle 4: Concurrent Load Comparison

**RED**: Compare behavior under concurrent load
```python
def test_concurrent_load_comparison():
    """All frameworks should handle concurrent load."""
    import concurrent.futures

    frameworks = {
        "FastAPI": "http://localhost:8001",
        "Express": "http://localhost:8002",
        # ... etc
    }

    for name, url in frameworks.items():
        errors = []
        latencies = []

        def request():
            try:
                start = time.perf_counter()
                response = requests.post(
                    f"{url}/graphql",
                    json={"query": "{ users { id } }"},
                    timeout=10
                )
                if response.status_code == 200:
                    latencies.append((time.perf_counter() - start) * 1000)
                else:
                    errors.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(request) for _ in range(500)]
            concurrent.futures.wait(futures)

        success_rate = len(latencies) / (len(latencies) + len(errors))
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0

        print(f"{name}: {success_rate*100:.1f}% success, p99 {p99_latency:.1f}ms")
        assert success_rate > 0.99, f"{name} too many failures: {len(errors)}"
```

**GREEN**: Run concurrent load tests

**REFACTOR**: Test at multiple concurrency levels

**CLEANUP**: Document scalability characteristics

---

## Deliverables

```
benchmarks/
├── test_framework_comparison.py    # Main benchmark harness
├── test_overhead_analysis.py       # Overhead calculation
├── test_resource_profiling.py      # Memory/CPU analysis
├── test_concurrent_load.py         # Concurrent testing
├── conftest.py                     # Pytest fixtures
└── reports/
    ├── overhead_summary.md
    ├── resource_usage.md
    ├── concurrent_load_results.md
    └── graphs/
        ├── latency_comparison.png
        ├── overhead_comparison.png
        └── throughput_comparison.png
```

## Benchmark Report Template

```markdown
# Framework Overhead Analysis Report

## Executive Summary
Framework overhead compared to pure FraiseQL:
- [Language]: X ms average overhead
- Conclusion: [Which languages are most efficient]

## Query Pattern Analysis

### Simple Query: `{ users { id } }`
| Framework | Baseline | Overhead | % Overhead |
|-----------|----------|----------|-----------|
| FraiseQL  | 15.2ms   | 0ms      | 0%        |
| FastAPI   | 23.1ms   | 7.9ms    | 52%       |
| Express   | 21.5ms   | 6.3ms    | 41%       |
| Gin       | 19.4ms   | 4.2ms    | 28%       |
| Spring    | 28.1ms   | 12.9ms   | 85%       |
| Laravel   | 32.5ms   | 17.3ms   | 114%      |

## Resource Usage

| Framework | Memory (idle) | Memory (loaded) | CPU (sustained) |
|-----------|--------------|-----------------|-----------------|
| FastAPI   | 45MB         | 68MB            | 12%             |
| Express   | 32MB         | 51MB            | 8%              |
| Gin       | 15MB         | 22MB            | 5%              |
| Spring    | 320MB        | 380MB           | 15%             |
| Laravel   | 52MB         | 75MB            | 10%             |

## Key Findings
- [Performance characteristics]
- [Resource efficiency]
- [Scalability notes]

## Recommendations
- [Best-performing language for specific scenarios]
- [Resource-constrained deployments]
- [Concurrent request handling]
```

## Dependencies

- Requires: Phase 3 (all frameworks implemented and running)
- Blocks: Phase 5 (feature enhancements based on results)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- Baseline is established with no application load
- All tests run on same hardware for fair comparison
- Network latency (HTTP overhead) is included in measurements
- Results guide optimization priorities for Phase 5
