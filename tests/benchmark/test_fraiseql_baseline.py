"""
FraiseQL Performance Baseline Measurement

Measures baseline performance metrics for compiled query execution.
"""

import time
import statistics
import json
from pathlib import Path

import pytest
import requests


class TestFraiseQLPerformance:
    """Measure FraiseQL server performance baseline."""

    @pytest.mark.benchmark
    def test_simple_query_latency(self, fraiseql_server):
        """Measure latency for simple query: { users { id } }."""
        query = "{ users { id } }"
        latencies = []

        # Run 100 iterations
        for _ in range(100):
            start = time.perf_counter()
            response = requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query},
                timeout=5,
            )
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

            assert response.status_code == 200
            latencies.append(elapsed)

        # Calculate statistics
        p50 = statistics.quantiles(latencies, n=2)[0]
        p99 = sorted(latencies)[-1]
        mean = statistics.mean(latencies)
        median = statistics.median(latencies)
        stdev = statistics.stdev(latencies)

        # Print results
        print("\nSimple Query Latency (100 runs):")
        print(f"  P50:    {p50:.2f}ms")
        print(f"  P99:    {p99:.2f}ms")
        print(f"  Mean:   {mean:.2f}ms")
        print(f"  Median: {median:.2f}ms")
        print(f"  StDev:  {stdev:.2f}ms")

        # Assert reasonable performance (< 100ms p99 for now)
        assert p99 < 100, f"P99 latency too high: {p99}ms"

    @pytest.mark.benchmark
    def test_nested_query_latency(self, fraiseql_server):
        """Measure latency for nested query: { users { id posts { id } } }."""
        query = "{ users { id posts { id } } }"
        latencies = []

        # Run 50 iterations (nested queries take longer)
        for _ in range(50):
            start = time.perf_counter()
            response = requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query},
                timeout=5,
            )
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

            assert response.status_code == 200
            latencies.append(elapsed)

        # Calculate statistics
        p50 = statistics.quantiles(latencies, n=2)[0]
        p99 = sorted(latencies)[-1]
        mean = statistics.mean(latencies)
        median = statistics.median(latencies)
        stdev = statistics.stdev(latencies)

        # Print results
        print("\nNested Query Latency (50 runs):")
        print(f"  P50:    {p50:.2f}ms")
        print(f"  P99:    {p99:.2f}ms")
        print(f"  Mean:   {mean:.2f}ms")
        print(f"  Median: {median:.2f}ms")
        print(f"  StDev:  {stdev:.2f}ms")

        # Assert reasonable performance (< 200ms p99 for now)
        assert p99 < 200, f"P99 latency too high: {p99}ms"

    @pytest.mark.benchmark
    def test_throughput_simple_query(self, fraiseql_server):
        """Measure throughput for simple queries."""
        query = "{ users { id } }"
        num_requests = 200
        start = time.perf_counter()

        for _ in range(num_requests):
            response = requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query},
                timeout=5,
            )
            assert response.status_code == 200

        elapsed = time.perf_counter() - start
        throughput = num_requests / elapsed

        print("\nThroughput (Simple Query):")
        print(f"  Requests:   {num_requests}")
        print(f"  Duration:   {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.1f} req/s")

        # Assert minimum throughput (at least 10 req/s for now)
        assert throughput > 10, f"Throughput too low: {throughput:.1f} req/s"

    @pytest.mark.benchmark
    def test_throughput_nested_query(self, fraiseql_server):
        """Measure throughput for nested queries."""
        query = "{ users { id posts { id } } }"
        num_requests = 100  # Fewer for nested queries
        start = time.perf_counter()

        for _ in range(num_requests):
            response = requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query},
                timeout=5,
            )
            assert response.status_code == 200

        elapsed = time.perf_counter() - start
        throughput = num_requests / elapsed

        print("\nThroughput (Nested Query):")
        print(f"  Requests:   {num_requests}")
        print(f"  Duration:   {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.1f} req/s")

        # Assert minimum throughput
        assert throughput > 1, f"Throughput too low: {throughput:.1f} req/s"

    @pytest.mark.benchmark
    def test_store_baseline_metrics(self, fraiseql_server):
        """Store baseline metrics for comparison."""
        query_simple = "{ users { id } }"
        query_nested = "{ users { id posts { id } } }"

        # Measure simple query
        simple_latencies = []
        for _ in range(100):
            start = time.perf_counter()
            requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query_simple},
                timeout=5,
            )
            elapsed = (time.perf_counter() - start) * 1000
            simple_latencies.append(elapsed)

        # Measure nested query
        nested_latencies = []
        for _ in range(50):
            start = time.perf_counter()
            requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query_nested},
                timeout=5,
            )
            elapsed = (time.perf_counter() - start) * 1000
            nested_latencies.append(elapsed)

        # Create baseline report
        baseline = {
            "fraiseql_compiled": {
                "simple_query": {
                    "runs": 100,
                    "p50_ms": statistics.quantiles(simple_latencies, n=2)[0],
                    "p99_ms": sorted(simple_latencies)[-1],
                    "mean_ms": statistics.mean(simple_latencies),
                    "median_ms": statistics.median(simple_latencies),
                    "stdev_ms": statistics.stdev(simple_latencies),
                },
                "nested_query": {
                    "runs": 50,
                    "p50_ms": statistics.quantiles(nested_latencies, n=2)[0],
                    "p99_ms": sorted(nested_latencies)[-1],
                    "mean_ms": statistics.mean(nested_latencies),
                    "median_ms": statistics.median(nested_latencies),
                    "stdev_ms": statistics.stdev(nested_latencies),
                },
            }
        }

        # Save baseline
        baseline_file = Path(__file__).parent / "reports" / "fraiseql_baseline.json"
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        baseline_file.write_text(json.dumps(baseline, indent=2))

        print(f"\nBaseline metrics saved to: {baseline_file}")
        print(json.dumps(baseline, indent=2))


if __name__ == "__main__":
    import sys

    pytest.main([__file__, "-v", "-m", "benchmark"] + sys.argv[1:])
