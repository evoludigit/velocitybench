# Performance Baseline Management

## Overview

VelocityBench tracks performance metrics across framework implementations to detect regressions and compare approaches. This guide explains how baselines are captured, stored, and used to prevent performance degradation.

---

## What is a Baseline?

A **baseline** is a snapshot of performance metrics captured at a known point in time:

```yaml
baseline_version: "1.0"
timestamp: "2025-01-31T10:00:00Z"
framework: "strawberry"
framework_version: "0.250.0"

metrics:
  query_latency_ms:
    p50: 12.3
    p95: 45.2
    p99: 102.1
  queries_per_second: 850
  memory_usage_mb: 256
  connection_pool_size: 50
```

### Why Baselines Matter

- ✅ **Detect Regressions** - Know when performance degrades
- ✅ **Track Improvements** - Measure optimization impact
- ✅ **Compare Frameworks** - Benchmark different approaches
- ✅ **Capacity Planning** - Understand limits and scaling
- ✅ **CI/CD Integration** - Fail tests if performance drops

---

## Baseline Storage

### Directory Structure

```
tests/perf/baselines/
├── README.md
├── v1.0/
│   ├── strawberry.json
│   ├── fastapi-rest.json
│   ├── graphene.json
│   ├── flask-rest.json
│   ├── ariadne.json
│   └── asgi-graphql.json
├── v1.1/
│   ├── strawberry.json
│   ├── fastapi-rest.json
│   └── ...
└── current/
    ├── strawberry.json          ← Latest baseline
    ├── fastapi-rest.json
    └── ...
```

### Baseline File Format

Each framework has a JSON baseline file:

```json
{
  "baseline_version": "1.0",
  "timestamp": "2025-01-31T10:00:00Z",
  "framework": "strawberry",
  "framework_version": "0.250.0",
  "python_version": "3.13.7",
  "database": {
    "version": "14.2",
    "host": "localhost",
    "pool_size": 50
  },
  "test_data": {
    "users_count": 1000,
    "posts_per_user": 10,
    "comments_per_post": 5,
    "total_records": 50000
  },
  "test_conditions": {
    "concurrent_clients": 50,
    "test_duration_seconds": 60,
    "warmup_seconds": 10
  },
  "metrics": {
    "user_query": {
      "latency_ms": {
        "p50": 12.3,
        "p95": 45.2,
        "p99": 102.1,
        "mean": 28.5
      },
      "throughput_ops_per_sec": 850,
      "errors": 0
    },
    "user_with_posts_query": {
      "latency_ms": {
        "p50": 45.1,
        "p95": 120.3,
        "p99": 350.5,
        "mean": 78.2
      },
      "throughput_ops_per_sec": 250,
      "errors": 0
    },
    "create_user_mutation": {
      "latency_ms": {
        "p50": 8.2,
        "p95": 25.1,
        "p99": 65.3,
        "mean": 15.4
      },
      "throughput_ops_per_sec": 1200,
      "errors": 0
    },
    "memory_usage_mb": 256,
    "connection_pool_utilization_percent": 65
  },
  "notes": "Baseline after optimization PR #123"
}
```

---

## Capturing Baselines

### Using Performance Test Scripts

Baselines are captured by running performance test suite:

```bash
# Run performance tests and capture baseline
make quality  # Run linting, type-checking first
pytest tests/perf/ -v --benchmark-only

# Or with Make target (if configured)
make perf-capture-baseline
```

### Manual Baseline Capture

```bash
#!/bin/bash
# capture_baseline.sh

FRAMEWORK=$1
VERSION=$2
BASELINE_DIR="tests/perf/baselines/current"

echo "Capturing baseline for $FRAMEWORK v$VERSION..."

# Run performance test suite
pytest tests/perf/test_${FRAMEWORK}_performance.py -v \
    --json-report \
    --json-report-file="${BASELINE_DIR}/${FRAMEWORK}_report.json"

# Convert to baseline format
python tests/perf/scripts/generate_baseline.py \
    --input "${BASELINE_DIR}/${FRAMEWORK}_report.json" \
    --output "${BASELINE_DIR}/${FRAMEWORK}.json" \
    --framework "$FRAMEWORK" \
    --version "$VERSION"

echo "✓ Baseline captured: ${BASELINE_DIR}/${FRAMEWORK}.json"
```

### Baseline Generator Script

```python
# tests/perf/scripts/generate_baseline.py

import json
import argparse
from datetime import datetime
from pathlib import Path

def generate_baseline(input_file, output_file, framework, version):
    """Convert performance test results to baseline format."""
    with open(input_file) as f:
        results = json.load(f)

    baseline = {
        "baseline_version": "1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "framework": framework,
        "framework_version": version,
        "python_version": "3.13.7",
        # ... rest of template
        "metrics": extract_metrics(results),
    }

    with open(output_file, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"✓ Baseline: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--framework", required=True)
    parser.add_argument("--version", required=True)

    args = parser.parse_args()
    generate_baseline(args.input, args.output, args.framework, args.version)
```

---

## Comparing Against Baselines

### Performance Test with Baseline Comparison

```python
# tests/perf/test_performance_regression.py

import json
import pytest
from pathlib import Path

@pytest.fixture
def baseline():
    """Load baseline for comparison."""
    baseline_file = Path("tests/perf/baselines/current/strawberry.json")
    with open(baseline_file) as f:
        return json.load(f)

def test_user_query_latency_against_baseline(benchmark, baseline):
    """Test user query latency hasn't regressed."""
    result = benchmark(run_user_query)

    baseline_p95 = baseline["metrics"]["user_query"]["latency_ms"]["p95"]
    current_p95 = result["latency_p95_ms"]

    # Allow 10% variance (baselines have natural variance)
    tolerance = baseline_p95 * 0.10
    assert current_p95 <= baseline_p95 + tolerance, \
        f"Query latency regressed: {current_p95}ms vs baseline {baseline_p95}ms"

def test_throughput_against_baseline(benchmark, baseline):
    """Test throughput hasn't regressed."""
    result = benchmark(run_load_test, duration=60)

    baseline_throughput = baseline["metrics"]["user_query"]["throughput_ops_per_sec"]
    current_throughput = result["ops_per_sec"]

    # Allow 10% variance
    tolerance = baseline_throughput * 0.10
    assert current_throughput >= baseline_throughput - tolerance, \
        f"Throughput regressed: {current_throughput} ops/s vs baseline {baseline_throughput} ops/s"
```

### Running Regression Tests

```bash
# Run performance regression tests
pytest tests/perf/test_performance_regression.py -v

# Run with detailed reporting
pytest tests/perf/test_performance_regression.py -v --tb=short

# Run specific framework
pytest tests/perf/test_performance_regression.py::test_strawberry_regression -v
```

---

## Baseline Comparison Script

### Compare Two Baselines

```python
# tests/perf/scripts/compare_baselines.py

import json
from pathlib import Path

def compare_baselines(baseline1_path, baseline2_path):
    """Compare two baseline files and show differences."""
    with open(baseline1_path) as f:
        baseline1 = json.load(f)
    with open(baseline2_path) as f:
        baseline2 = json.load(f)

    print(f"\nComparison: {baseline1['framework']}")
    print(f"  Version 1: {baseline1['timestamp']}")
    print(f"  Version 2: {baseline2['timestamp']}")
    print()

    for query_name in baseline1["metrics"]:
        if query_name not in baseline2["metrics"]:
            continue

        m1 = baseline1["metrics"][query_name]
        m2 = baseline2["metrics"][query_name]

        if "latency_ms" in m1 and "latency_ms" in m2:
            lat1_p95 = m1["latency_ms"]["p95"]
            lat2_p95 = m2["latency_ms"]["p95"]
            change_pct = ((lat2_p95 - lat1_p95) / lat1_p95) * 100

            print(f"{query_name} latency (p95):")
            print(f"  Before: {lat1_p95:.1f}ms")
            print(f"  After:  {lat2_p95:.1f}ms")
            print(f"  Change: {change_pct:+.1f}%")
            print()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    args = parser.parse_args()

    compare_baselines(args.before, args.after)
```

### Usage

```bash
# Compare two baseline files
python tests/perf/scripts/compare_baselines.py \
    --before tests/perf/baselines/v1.0/strawberry.json \
    --after tests/perf/baselines/current/strawberry.json

# Example output:
# Comparison: strawberry
#   Version 1: 2025-01-01T10:00:00Z
#   Version 2: 2025-01-31T10:00:00Z
#
# user_query latency (p95):
#   Before: 45.2ms
#   After:  48.3ms
#   Change: +6.9%
#
# user_with_posts_query latency (p95):
#   Before: 120.3ms
#   After:  118.5ms
#   Change: -1.5%
```

---

## Baseline Management Workflow

### 1. **Capture Initial Baseline**

When adding new performance tests:

```bash
# Ensure tests pass
pytest tests/perf/test_strawberry_performance.py -v

# Capture baseline
python tests/perf/scripts/generate_baseline.py \
    --input tests/perf/results/strawberry_report.json \
    --output tests/perf/baselines/current/strawberry.json \
    --framework strawberry \
    --version 0.250.0

# Commit baseline
git add tests/perf/baselines/
git commit -m "perf: Add strawberry performance baseline"
```

### 2. **During Development**

Run regression tests to ensure no degradation:

```bash
# Before committing
pytest tests/perf/test_performance_regression.py -v

# If regression detected:
# - Review changes
# - Optimize code
# - Re-run tests
```

### 3. **After Optimization**

Update baseline when intentional improvement is made:

```bash
# Verify improvement
pytest tests/perf/test_performance_regression.py -v

# Compare old vs new
python tests/perf/scripts/compare_baselines.py \
    --before tests/perf/baselines/v1.0/strawberry.json \
    --after tests/perf/results/new_baseline.json

# Update current baseline
cp tests/perf/results/new_baseline.json tests/perf/baselines/current/strawberry.json

# Archive old baseline
cp tests/perf/baselines/current/strawberry.json \
   tests/perf/baselines/v1.1/strawberry.json

# Commit
git add tests/perf/baselines/
git commit -m "perf: Update strawberry baseline after query optimization"
```

### 4. **Cross-Framework Comparison**

Compare performance across frameworks:

```python
# tests/perf/test_framework_comparison.py

import json
from pathlib import Path

def test_framework_performance_comparison():
    """Compare performance across all frameworks."""
    baselines_dir = Path("tests/perf/baselines/current")

    results = {}
    for baseline_file in baselines_dir.glob("*.json"):
        with open(baseline_file) as f:
            baseline = json.load(f)
            results[baseline["framework"]] = baseline["metrics"]

    # Print comparison table
    print("\nFramework Performance Comparison (p95 latency ms):")
    print("-" * 60)
    for framework, metrics in sorted(results.items()):
        latency = metrics.get("user_query", {}).get("latency_ms", {}).get("p95", "N/A")
        print(f"{framework:20} {latency}")

    # Assert no framework is significantly slower
    for framework, metrics in results.items():
        latency = metrics.get("user_query", {}).get("latency_ms", {}).get("p95", float("inf"))
        assert latency < 500, f"{framework} latency too high: {latency}ms"
```

---

## Baseline Update Policy

### When to Update Baselines

✅ **DO Update:**
- After intentional performance optimization
- When upgrading framework versions
- When database schema changes
- When load test conditions change

❌ **DON'T Update:**
- When performance regresses (fix code instead)
- Without documenting the reason
- In every commit (baselines should be stable)
- Without running multiple test iterations

### Documentation Template

When updating baseline:

```markdown
## Baseline Update: strawberry v0.250.0

**Date:** 2025-01-31
**PR:** #456
**Reason:** Query optimization - added indexes on post.fk_author

**Changes:**
- user_query latency: 45.2ms → 42.1ms (-7%)
- user_with_posts_query latency: 120.3ms → 98.5ms (-18%)
- throughput: no change

**Test Conditions:**
- Database: PostgreSQL 14.2
- Test data: 1000 users, 10 posts/user, 5 comments/post
- Load: 50 concurrent clients for 60s
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Performance Regression Tests

on:
  pull_request:
    paths:
      - 'frameworks/**'
      - 'tests/perf/**'

jobs:
  performance-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: velocitybench_benchmark
          POSTGRES_USER: benchmark
          POSTGRES_PASSWORD: benchmark123
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-benchmark

      - name: Run performance regression tests
        run: pytest tests/perf/test_performance_regression.py -v

      - name: Compare baselines (if regression)
        if: failure()
        run: |
          python tests/perf/scripts/compare_baselines.py \
            --before tests/perf/baselines/current/strawberry.json \
            --after tests/perf/results/current_run.json
```

---

## Best Practices

### ✅ DO:

- **Capture baselines regularly** - After each major change
- **Document why baselines change** - Link to PRs and commits
- **Run tests multiple times** - Account for variance
- **Version baselines** - Keep history for comparison
- **Test on consistent hardware** - Same machine/cloud for comparison

### ❌ DON'T:

- **Commit baselines without testing** - Ensure tests pass first
- **Update baselines without justification** - Document the reason
- **Ignore small regressions** - They compound over time
- **Test different frameworks on different systems** - Use consistent environment
- **Delete old baselines** - Keep them for historical comparison

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Baseline comparison fails | Baseline file not found | Check path and ensure file exists |
| High variance in results | System load, database interference | Run tests in isolation |
| Regression false positive | Natural variance in latency | Increase tolerance (e.g., 15%) |
| Can't reproduce improvement | Different test conditions | Match exact conditions from baseline |

---

## Related Documentation

- [Performance Tuning Guide](PERFORMANCE_TUNING_GUIDE.md) - How to optimize queries
- [Test Isolation Strategy](TEST_ISOLATION_STRATEGY.md) - How tests are isolated
- [Fixture Factory Guide](FIXTURE_FACTORY_GUIDE.md) - Creating test data
