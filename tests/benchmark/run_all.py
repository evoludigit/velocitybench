#!/usr/bin/env python3
"""
VelocityBench — Full Suite Benchmark Orchestrator

Runs k6 against all 8 benchmark frameworks sequentially and aggregates
results into a unified comparison Markdown table.

Prerequisites:
    docker compose --profile benchmark up -d
    # k6 must be installed: https://k6.io/docs/getting-started/installation/

Usage:
    python benchmarks/run_all.py
    python benchmarks/run_all.py --duration 30s --cooldown 10
    python benchmarks/run_all.py --frameworks strawberry graphene go-gqlgen
    python benchmarks/run_all.py --dry-run  # print commands, don't execute
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ALL_FRAMEWORKS: list[str] = [
    "fastapi-rest",
    "strawberry",
    "graphene",
    "go-gqlgen",
    "actix-web-rest",
    "async-graphql",
    "fraiseql-v",
    "fraiseql-tv",
]

REPORTS_DIR = Path(__file__).parent.parent / "reports"
K6_SCRIPT   = Path(__file__).parent / "k6" / "full_suite.js"

# Cooldown between framework runs to prevent resource interference
DEFAULT_COOLDOWN_SECS = 30

# ---------------------------------------------------------------------------
# k6 runner
# ---------------------------------------------------------------------------


def run_k6(
    framework: str,
    date_str: str,
    extra_env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict | None:
    output_file = REPORTS_DIR / f"k6-{framework}-{date_str}.json"
    cmd = [
        "k6", "run",
        "--env", f"FRAMEWORK={framework}",
        "--out", f"json={output_file}",
        str(K6_SCRIPT),
    ]

    print(f"\n{'=' * 60}")
    print(f"  Framework: {framework}")
    print(f"  Output:    {output_file.relative_to(Path.cwd())}")
    print(f"  Command:   {' '.join(cmd)}")
    print(f"{'=' * 60}", flush=True)

    if dry_run:
        print("  [dry-run] skipping execution")
        return None

    env = dict(__import__("os").environ)
    if extra_env:
        env.update(extra_env)

    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(
            f"WARNING: k6 exited {result.returncode} for {framework}",
            file=sys.stderr,
        )

    # k6 handleSummary writes a JSON file named reports/k6-<fw>-<date>.json
    summary_file = REPORTS_DIR / f"k6-{framework}-{date_str}.json"
    if summary_file.exists():
        try:
            return json.loads(summary_file.read_text())
        except json.JSONDecodeError:
            print(f"WARNING: could not parse {summary_file}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------


def generate_comparison_report(
    results: dict[str, dict | None],
    date_str: str,
) -> str:
    lines: list[str] = [
        "# VelocityBench — Full Suite Benchmark Report",
        "",
        f"**Date**: {date_str}",
        "**Tool**: k6",
        "**Scenario**: 30s warmup → 2m ramp-up → 5m sustained → 30s cooldown, 100 VUs peak",
        "**Dataset**: medium (10K users, 50K posts, 200K comments)",
        "",
        "## Results",
        "",
        "| Framework | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Q3 p99 (ms) | Error % | Requests |",
        "|-----------|-----|----------|----------|----------|-------------|---------|----------|",
    ]

    for framework, r in results.items():
        if r:
            q3_p99 = f"{r['q3_p99_ms']:.0f}" if r.get("q3_p99_ms") else "—"
            lines.append(
                f"| {framework} "
                f"| {r['rps']:.0f} "
                f"| {r['p50_ms']:.1f} "
                f"| {r['p95_ms']:.1f} "
                f"| {r['p99_ms']:.1f} "
                f"| {q3_p99} "
                f"| {r['error_rate'] * 100:.2f}% "
                f"| {r['total_requests']:,} |"
            )
        else:
            lines.append(f"| {framework} | — | — | — | — | — | — | — |")

    lines.extend([
        "",
        "## Request Mix Breakdown",
        "",
        "| Framework | Q1 (flat) | Q2 (1 embed) | Q3 (2 embeds) | Mutations |",
        "|-----------|----------:|-------------:|--------------:|----------:|",
    ])
    for framework, r in results.items():
        if r:
            total = r.get("total_requests", 1) or 1
            lines.append(
                f"| {framework} "
                f"| {r.get('q1_count', 0):,} ({r.get('q1_count', 0)/total*100:.0f}%) "
                f"| {r.get('q2_count', 0):,} ({r.get('q2_count', 0)/total*100:.0f}%) "
                f"| {r.get('q3_count', 0):,} ({r.get('q3_count', 0)/total*100:.0f}%) "
                f"| {r.get('m1_count', 0):,} ({r.get('m1_count', 0)/total*100:.0f}%) |"
            )
        else:
            lines.append(f"| {framework} | — | — | — | — |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run k6 benchmark against all VelocityBench frameworks"
    )
    parser.add_argument(
        "--frameworks",
        nargs="+",
        default=ALL_FRAMEWORKS,
        metavar="FRAMEWORK",
        help=f"Frameworks to benchmark (default: all {len(ALL_FRAMEWORKS)})",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=DEFAULT_COOLDOWN_SECS,
        metavar="SECS",
        help="Seconds to wait between framework runs (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print k6 commands without executing them",
    )
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    print("VelocityBench — Full Suite Benchmark Orchestrator")
    print(f"Frameworks : {', '.join(args.frameworks)}")
    print(f"Cooldown   : {args.cooldown}s between runs")
    print(f"Reports    : {REPORTS_DIR}/")
    if args.dry_run:
        print("Mode       : DRY RUN (no execution)")

    all_results: dict[str, dict | None] = {}
    for i, framework in enumerate(args.frameworks):
        all_results[framework] = run_k6(framework, date_str, dry_run=args.dry_run)

        if i < len(args.frameworks) - 1 and not args.dry_run:
            print(f"\nCooling down {args.cooldown}s before next framework...", flush=True)
            time.sleep(args.cooldown)

    if not args.dry_run:
        report = generate_comparison_report(all_results, date_str)
        report_path = REPORTS_DIR / f"framework-matrix-{date_str}.md"
        report_path.write_text(report)
        print(f"\n{'=' * 60}")
        print(f"Comparison report written to: {report_path}")
        print(f"{'=' * 60}")
        print()
        print(report)


if __name__ == "__main__":
    main()
