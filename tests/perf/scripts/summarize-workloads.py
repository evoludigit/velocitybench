#!/usr/bin/env python3
"""
Summarize workload test results from JMeter output.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def parse_jtl_results(jtl_file):
    """
    Parse JMeter JTL CSV results file and extract key metrics.
    JTL format: timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,sentBytes
    """
    metrics = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "elapsed_times": [],
        "response_codes": {},
    }

    try:
        with open(jtl_file, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                if not line.strip():
                    continue
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    metrics["total"] += 1
                    elapsed = int(parts[1]) if parts[1].isdigit() else 0
                    metrics["elapsed_times"].append(elapsed)
                    success = parts[7] == "true"
                    if success:
                        metrics["successful"] += 1
                    else:
                        metrics["failed"] += 1
                    code = parts[3] if len(parts) > 3 else "unknown"
                    metrics["response_codes"][code] = metrics["response_codes"].get(code, 0) + 1
    except Exception as e:
        print(f"Warning: Could not parse {jtl_file}: {e}")
        return None

    return metrics


def calculate_stats(elapsed_times):
    """Calculate statistics from elapsed times."""
    if not elapsed_times:
        return {}

    elapsed_times.sort()
    n = len(elapsed_times)

    return {
        "min": elapsed_times[0],
        "max": elapsed_times[-1],
        "avg": sum(elapsed_times) / n,
        "p50": elapsed_times[n // 2],
        "p95": elapsed_times[int(n * 0.95)],
        "p99": elapsed_times[int(n * 0.99)],
    }


def generate_summary(results_dir, framework):
    """Generate summary report from workload results."""
    results_path = Path(results_dir)
    workloads = [
        "simple",
        "parameterized",
        "aggregation",
        "pagination",
        "fulltext",
        "deep-traversal",
        "mutations",
        "mixed"
    ]

    summary = {
        "timestamp": datetime.now().isoformat(),
        "framework": framework,
        "results_dir": str(results_path),
        "workloads": {}
    }

    for workload in workloads:
        jtl_file = results_path / f"{workload}.jtl"
        if jtl_file.exists():
            metrics = parse_jtl_results(jtl_file)
            if metrics:
                stats = calculate_stats(metrics["elapsed_times"])
                summary["workloads"][workload] = {
                    "total_samples": metrics["total"],
                    "successful": metrics["successful"],
                    "failed": metrics["failed"],
                    "error_rate": (metrics["failed"] / metrics["total"] * 100) if metrics["total"] > 0 else 0,
                    "response_codes": metrics["response_codes"],
                    "latency_ms": stats,
                }

    # Write summary to JSON file
    summary_file = results_path / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary to console
    print("\n=== Workload Summary ===")
    print(f"Framework: {framework}")
    print(f"Results directory: {results_path}")
    print(f"Generated: {summary['timestamp']}\n")

    print(f"{'Workload':<20} {'Total':<8} {'Success':<8} {'Failed':<8} {'P50 (ms)':<10} {'P95 (ms)':<10} {'P99 (ms)':<10}")
    print("-" * 84)

    for workload, data in summary["workloads"].items():
        stats = data.get("latency_ms", {})
        p50 = stats.get("p50", 0)
        p95 = stats.get("p95", 0)
        p99 = stats.get("p99", 0)
        print(f"{workload:<20} {data['total_samples']:<8} {data['successful']:<8} {data['failed']:<8} {p50:<10.1f} {p95:<10.1f} {p99:<10.1f}")

    print(f"\nDetailed summary saved to: {summary_file}")
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: summarize-workloads.py <results_dir> [framework]")
        sys.exit(1)

    results_dir = sys.argv[1]
    framework = sys.argv[2] if len(sys.argv) > 2 else "unknown"

    if not Path(results_dir).exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    generate_summary(results_dir, framework)
