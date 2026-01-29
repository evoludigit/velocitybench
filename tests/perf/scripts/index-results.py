#!/usr/bin/env python3
"""
Index performance test results for efficient searching and analysis.

Creates a searchable index of all JTL result files in the results directory,
enabling fast queries for historical performance trends.

Usage:
    python index-results.py                          # Index all results
    python index-results.py --query framework=strawberry
    python index-results.py --query "latency < 50"
    python index-results.py --recent 10              # Show 10 most recent tests
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ResultsIndexer:
    """Index performance test results for searching."""

    def __init__(self, results_dir: Path) -> None:
        """Initialize indexer with results directory."""
        self.results_dir = results_dir
        self.index_file = results_dir / "results_index.json"
        self.index: dict[str, Any] = {"version": "1.0", "indexed_at": "", "results": []}

    def _parse_result_path(self, path: Path) -> dict[str, str] | None:
        """Parse result directory path to extract metadata."""
        parts = path.parts
        if len(parts) < 4:
            return None

        # Pattern: framework/workload/dataset/timestamp/
        return {
            "framework": parts[0],
            "workload": parts[1],
            "dataset": parts[2],
            "timestamp": parts[3],
            "path": str(path),
        }

    def _parse_jtl_file(self, jtl_path: Path) -> dict[str, Any] | None:
        """Parse JTL file and extract statistics."""
        try:
            if not jtl_path.exists():
                return None

            times: list[int] = []
            count = 0

            with open(jtl_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    count += 1
                    try:
                        elapsed = int(row.get("elapsed", 0))
                        times.append(elapsed)
                    except (ValueError, TypeError):
                        continue

            if not times:
                return None

            times.sort()
            return {
                "samples": count,
                "min": min(times),
                "max": max(times),
                "mean": sum(times) / len(times),
                "p50": times[len(times) // 2],
                "p95": times[int(len(times) * 0.95)],
                "p99": times[int(len(times) * 0.99)],
            }
        except Exception as e:
            print(f"Error parsing {jtl_path}: {e}")
            return None

    def index_results(self) -> dict[str, int]:
        """Index all result directories."""
        stats = {"indexed": 0, "errors": 0}

        if not self.results_dir.exists():
            print(f"Results directory not found: {self.results_dir}")
            return stats

        # Find all JTL files
        for jtl_file in self.results_dir.glob("*/*/*/results.jtl"):
            result_dir = jtl_file.parent
            metadata = self._parse_result_path(result_dir.relative_to(self.results_dir))

            if not metadata:
                stats["errors"] += 1
                continue

            metrics = self._parse_jtl_file(jtl_file)
            if not metrics:
                stats["errors"] += 1
                continue

            self.index["results"].append({**metadata, **metrics})
            stats["indexed"] += 1

        # Save index
        self.index["indexed_at"] = datetime.now().isoformat()
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

        print(f"✓ Indexed {stats['indexed']} results")
        print(f"✗ Failed to index {stats['errors']} results")
        print(f"✓ Index saved to {self.index_file}")

        return stats

    def query_results(
        self, framework: str | None = None, recent: int | None = None
    ) -> list[dict[str, Any]]:
        """Query indexed results."""
        if not self.index_file.exists():
            print("Index not found. Run indexing first with: python index-results.py")
            return []

        with open(self.index_file) as f:
            index = json.load(f)

        results = index.get("results", [])

        # Filter by framework
        if framework:
            results = [r for r in results if r.get("framework") == framework]

        # Sort by timestamp (newest first)
        results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

        # Limit to recent
        if recent:
            results = results[:recent]

        return results

    def print_summary(self) -> None:
        """Print summary of indexed results."""
        if not self.index_file.exists():
            print("No index found")
            return

        with open(self.index_file) as f:
            index = json.load(f)

        results = index.get("results", [])

        # Group by framework
        by_framework: dict[str, list] = {}
        for result in results:
            fw = result.get("framework", "unknown")
            if fw not in by_framework:
                by_framework[fw] = []
            by_framework[fw].append(result)

        print(f"\nResults Index ({index.get('indexed_at')})")
        print(f"Total results: {len(results)}\n")

        for framework in sorted(by_framework.keys()):
            tests = by_framework[framework]
            print(f"  {framework}: {len(tests)} test runs")
            if tests:
                latest = max(tests, key=lambda r: r.get("timestamp", ""))
                print(f"    Latest: {latest.get('timestamp')} ({latest.get('workload')}/{latest.get('dataset')})")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Index and query performance test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index all results
  python index-results.py

  # Show indexed results summary
  python index-results.py --summary

  # Query specific framework
  python index-results.py --query framework=strawberry

  # Show 10 most recent results
  python index-results.py --recent 10
        """,
    )
    parser.add_argument("--results-dir", default=".", help="Results directory (default: current)")
    parser.add_argument("--query", help="Query framework (e.g., 'framework=strawberry')")
    parser.add_argument("--recent", type=int, help="Show N most recent results")
    parser.add_argument("--summary", action="store_true", help="Show summary of indexed results")

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    indexer = ResultsIndexer(results_dir / "results" if (results_dir / "results").exists() else results_dir)

    if args.summary:
        indexer.print_summary()
    elif args.query:
        # Simple query parsing: "framework=strawberry"
        key, value = args.query.split("=")
        results = indexer.query_results(framework=value if key == "framework" else None)
        for r in results:
            print(f"{r['timestamp']} | {r['framework']:<15} | {r['workload']:<15} | p95={r['p95']}ms")
    elif args.recent is not None:
        results = indexer.query_results(recent=args.recent)
        print(f"\nMost recent {args.recent} results:\n")
        for r in results:
            print(f"{r['timestamp']} | {r['framework']:<15} | {r['workload']:<15} | p95={r['p95']}ms")
    else:
        # Index all results
        indexer.index_results()
        indexer.print_summary()


if __name__ == "__main__":
    main()
