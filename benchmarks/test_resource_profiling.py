"""
FraiseQL Resource Profiling

Measures memory and CPU usage under load.
"""

import time
import json
from pathlib import Path

import pytest
import requests
import psutil


class TestFraiseQLResources:
    """Profile FraiseQL server resource usage."""

    @pytest.mark.benchmark
    def test_memory_usage_idle(self, fraiseql_server):
        """Measure memory usage at idle."""
        # Parse port from URL
        port = fraiseql_server.split(":")[-1]

        # Find server process
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if cmdline and "fraiseql-server" in " ".join(cmdline):
                    if f"--port {port}" in " ".join(cmdline):
                        # Found the right process
                        memory_info = proc.memory_info()
                        memory_mb = memory_info.rss / 1024 / 1024

                        print("\nMemory Usage (Idle):")
                        print(f"  RSS: {memory_mb:.1f}MB")
                        print(f"  VMS: {memory_info.vms / 1024 / 1024:.1f}MB")

                        assert memory_mb < 500, f"Memory usage too high: {memory_mb}MB"
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # If we get here, couldn't find process
        pytest.skip("Could not find fraiseql-server process")

    @pytest.mark.benchmark
    def test_memory_usage_under_load(self, fraiseql_server):
        """Measure memory usage under load."""
        query = "{ users { id } }"
        port = fraiseql_server.split(":")[-1]

        # Find server process
        proc_obj = None
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if cmdline and "fraiseql-server" in " ".join(cmdline):
                    if f"--port {port}" in " ".join(cmdline):
                        proc_obj = proc
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if not proc_obj:
            pytest.skip("Could not find fraiseql-server process")

        # Get baseline memory
        baseline_memory = proc_obj.memory_info().rss / 1024 / 1024

        # Send requests
        for _ in range(500):
            requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query},
                timeout=5,
            )

        # Get peak memory
        peak_memory = proc_obj.memory_info().rss / 1024 / 1024

        print("\nMemory Usage (Under Load - 500 requests):")
        print(f"  Baseline: {baseline_memory:.1f}MB")
        print(f"  Peak:     {peak_memory:.1f}MB")
        print(f"  Delta:    {peak_memory - baseline_memory:.1f}MB")

        # Memory shouldn't grow more than 100MB
        assert peak_memory - baseline_memory < 100, (
            f"Memory growth too high: {peak_memory - baseline_memory}MB"
        )

    @pytest.mark.benchmark
    def test_cpu_usage_during_load(self, fraiseql_server):
        """Measure CPU usage during load."""
        query = "{ users { id } }"
        port = fraiseql_server.split(":")[-1]

        # Find server process
        proc_obj = None
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if cmdline and "fraiseql-server" in " ".join(cmdline):
                    if f"--port {port}" in " ".join(cmdline):
                        proc_obj = proc
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if not proc_obj:
            pytest.skip("Could not find fraiseql-server process")

        # Warm up
        for _ in range(50):
            requests.post(
                f"{fraiseql_server}/graphql",
                json={"query": query},
                timeout=5,
            )

        # Measure CPU during sustained load
        start = time.time()
        cpu_samples = []

        for _ in range(100):
            try:
                cpu_pct = proc_obj.cpu_percent(interval=0.01)
                cpu_samples.append(cpu_pct)
                requests.post(
                    f"{fraiseql_server}/graphql",
                    json={"query": query},
                    timeout=5,
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

        elapsed = time.time() - start

        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)

            print(f"\nCPU Usage (100 requests over {elapsed:.1f}s):")
            print(f"  Average: {avg_cpu:.1f}%")
            print(f"  Peak:    {max_cpu:.1f}%")

    @pytest.mark.benchmark
    def test_store_resource_metrics(self, fraiseql_server):
        """Store resource metrics for comparison."""
        port = fraiseql_server.split(":")[-1]

        # Find server process
        proc_obj = None
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if cmdline and "fraiseql-server" in " ".join(cmdline):
                    if f"--port {port}" in " ".join(cmdline):
                        proc_obj = proc
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if not proc_obj:
            pytest.skip("Could not find fraiseql-server process")

        # Get current metrics
        memory_info = proc_obj.memory_info()
        num_threads = proc_obj.num_threads()

        metrics = {
            "fraiseql_compiled": {
                "resources": {
                    "memory_mb": round(memory_info.rss / 1024 / 1024, 1),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 1),
                    "num_threads": num_threads,
                }
            }
        }

        # Save metrics
        metrics_file = Path(__file__).parent / "reports" / "fraiseql_resources.json"
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(json.dumps(metrics, indent=2))

        print(f"\nResource metrics saved to: {metrics_file}")
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    import sys

    pytest.main([__file__, "-v", "-m", "benchmark"] + sys.argv[1:])
