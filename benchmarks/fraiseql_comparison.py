#!/usr/bin/env python3
"""
FraiseQL v_* vs tv_* Comparison Benchmark
==========================================

Directly compares two FraiseQL architectural variants:
  - fraiseql   (v_*,  port 8815): JSONB assembled at query time via jsonb_build_object()
  - fraiseql-tv (tv_*, port 8816): JSONB pre-computed at INSERT time, read directly

Both services must be running before executing this script:
    docker compose --profile fraiseql up -d

Usage:
    python benchmarks/fraiseql_comparison.py
    python benchmarks/fraiseql_comparison.py --duration 60 --concurrency 100
    python benchmarks/fraiseql_comparison.py --duration 30 --concurrency 50 --warmup 10

The benchmark uses four queries at increasing nesting depth:
  Q1  flat    — users (no nesting, pure JSONB read)
  Q2  shallow — posts with embedded author (1 level)
  Q3  deep    — comments with embedded author + post (2 embedded objects)
  Q4  filter  — posts filtered by published=true with embedded author
"""

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Benchmark queries
# ---------------------------------------------------------------------------

QUERIES: dict[str, str] = {
    "Q1_flat": "{ users(limit: 20) { id username fullName } }",
    "Q2_shallow": "{ posts(limit: 20) { id title author { username fullName } } }",
    "Q3_deep": (
        "{ comments(limit: 20) { id content "
        "author { username } post { title } } }"
    ),
    "Q4_filtered": (
        "{ posts(limit: 20, published: true) { id title author { username } } }"
    ),
}

VARIANTS: dict[str, str] = {
    "v_star":  "http://localhost:8815/graphql",
    "tv_star": "http://localhost:8816/graphql",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BenchResult:
    query_name: str
    variant: str
    duration_secs: int
    concurrency: int
    latencies_ms: list[float] = field(default_factory=list)
    errors: int = 0

    @property
    def requests_sent(self) -> int:
        return len(self.latencies_ms)

    @property
    def rps(self) -> float:
        return self.requests_sent / self.duration_secs if self.duration_secs > 0 else 0

    @property
    def p50_ms(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0

    @property
    def p95_ms(self) -> float:
        if not self.latencies_ms:
            return 0
        s = sorted(self.latencies_ms)
        return s[int(len(s) * 0.95)]

    @property
    def p99_ms(self) -> float:
        if not self.latencies_ms:
            return 0
        s = sorted(self.latencies_ms)
        return s[int(len(s) * 0.99)]

    @property
    def error_rate_pct(self) -> float:
        total = self.requests_sent + self.errors
        return (self.errors / total * 100) if total > 0 else 0


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _post_graphql(url: str, query: str, timeout: int = 10) -> tuple[bool, float]:
    """Execute one GraphQL request. Returns (success, latency_ms)."""
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            elapsed = (time.monotonic() - t0) * 1000
            ok = resp.status == 200 and "data" in body and not body.get("errors")
            return ok, elapsed
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        elapsed = (time.monotonic() - t0) * 1000
        return False, elapsed


def _worker(url: str, query: str, end_time: float) -> tuple[list[float], int]:
    """Single worker thread: fire requests until end_time."""
    latencies: list[float] = []
    errors = 0
    while time.monotonic() < end_time:
        ok, lat = _post_graphql(url, query)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
    return latencies, errors


# ---------------------------------------------------------------------------
# Core benchmark runner
# ---------------------------------------------------------------------------


def run_benchmark(
    variant: str,
    url: str,
    query_name: str,
    query: str,
    concurrency: int,
    duration_secs: int,
) -> BenchResult:
    result = BenchResult(
        query_name=query_name,
        variant=variant,
        duration_secs=duration_secs,
        concurrency=concurrency,
    )
    end_time = time.monotonic() + duration_secs
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(_worker, url, query, end_time)
            for _ in range(concurrency)
        ]
        for fut in as_completed(futures):
            lats, errs = fut.result()
            result.latencies_ms.extend(lats)
            result.errors += errs
    return result


def warmup(variant: str, url: str, query_name: str, query: str,
           concurrency: int, warmup_secs: int) -> None:
    print(f"  warming up {variant}/{query_name} ({warmup_secs}s)...", flush=True)
    run_benchmark(variant, url, query_name, query, concurrency, warmup_secs)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def _drop_pct(rps_q1: float, rps_qn: float) -> str:
    if rps_q1 <= 0:
        return "n/a"
    drop = (rps_q1 - rps_qn) / rps_q1 * 100
    return f"{drop:+.1f}%"


def format_report(
    results: dict[tuple[str, str], BenchResult],
    args: argparse.Namespace,
) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    lines: list[str] = []

    lines.append("# FraiseQL v_* vs tv_* Comparison Report")
    lines.append(f"")
    lines.append(f"**Date**: {now}  ")
    lines.append(f"**Duration per query**: {args.duration}s  ")
    lines.append(f"**Concurrency**: {args.concurrency}  ")
    lines.append(f"**Warmup**: {args.warmup}s  ")
    lines.append("")

    # Main results table
    lines.append("## Throughput (RPS) and Latency")
    lines.append("")
    lines.append("| Query | Variant | RPS | p50 ms | p95 ms | p99 ms | Errors |")
    lines.append("|-------|---------|----:|-------:|-------:|-------:|-------:|")
    for qname in QUERIES:
        for variant in VARIANTS:
            r = results.get((qname, variant))
            if r:
                lines.append(
                    f"| {qname} | {variant} | {r.rps:.0f} | "
                    f"{r.p50_ms:.1f} | {r.p95_ms:.1f} | {r.p99_ms:.1f} | "
                    f"{r.errors} ({r.error_rate_pct:.1f}%) |"
                )

    lines.append("")

    # Delta table: tv_* vs v_* RPS delta per query
    lines.append("## tv_* vs v_* RPS Delta (positive = tv_* faster)")
    lines.append("")
    lines.append("| Query | v_* RPS | tv_* RPS | Delta | tv_* advantage |")
    lines.append("|-------|--------:|---------:|------:|----------------|")
    for qname in QUERIES:
        r_v  = results.get((qname, "v_star"))
        r_tv = results.get((qname, "tv_star"))
        if r_v and r_tv:
            delta = r_tv.rps - r_v.rps
            adv = f"{delta / r_v.rps * 100:+.1f}%" if r_v.rps > 0 else "n/a"
            lines.append(
                f"| {qname} | {r_v.rps:.0f} | {r_tv.rps:.0f} | "
                f"{delta:+.0f} | {adv} |"
            )

    lines.append("")

    # Q1→Q3 drop analysis
    lines.append("## Q1→Q3 Throughput Drop (core CQRS claim)")
    lines.append("")
    lines.append(
        "The CQRS hypothesis: tv_* pre-computation eliminates nesting overhead,  \n"
        "making Q1 (flat) ≈ Q3 (2 embeds). v_* computes JSONB at query time (JOIN),  \n"
        "so Q3 should be measurably slower than Q1."
    )
    lines.append("")
    lines.append("| Variant | Q1 RPS | Q3 RPS | Q1→Q3 drop |")
    lines.append("|---------|-------:|-------:|-----------|")
    for variant in VARIANTS:
        r_q1 = results.get(("Q1_flat",  variant))
        r_q3 = results.get(("Q3_deep",  variant))
        if r_q1 and r_q3:
            drop = _drop_pct(r_q1.rps, r_q3.rps)
            lines.append(
                f"| {variant} | {r_q1.rps:.0f} | {r_q3.rps:.0f} | {drop} |"
            )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    r_tv_q1 = results.get(("Q1_flat",  "tv_star"))
    r_tv_q3 = results.get(("Q3_deep",  "tv_star"))
    r_v_q1  = results.get(("Q1_flat",  "v_star"))
    r_v_q3  = results.get(("Q3_deep",  "v_star"))
    if r_tv_q1 and r_tv_q3 and r_v_q1 and r_v_q3:
        tv_drop = (r_tv_q1.rps - r_tv_q3.rps) / r_tv_q1.rps * 100 if r_tv_q1.rps else 0
        v_drop  = (r_v_q1.rps  - r_v_q3.rps)  / r_v_q1.rps  * 100 if r_v_q1.rps  else 0
        lines.append(
            f"- **tv_* Q1→Q3 drop**: {tv_drop:.1f}% "
            f"({'✅ within 10% threshold' if tv_drop < 10 else '⚠️ exceeds 10% threshold'})"
        )
        lines.append(
            f"- **v_*  Q1→Q3 drop**: {v_drop:.1f}% "
            f"(expected higher due to runtime JSONB assembly)"
        )
        advantage = tv_drop < v_drop
        lines.append(
            f"- **CQRS hypothesis**: "
            f"{'✅ confirmed — tv_* shows lower nesting overhead' if advantage else '❌ not confirmed — v_* competitive with tv_*'}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_services() -> None:
    for label, url in VARIANTS.items():
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps({"query": "{ users(limit: 1) { id } }"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5):
                pass
            print(f"  ✓ {label} ({url}) reachable")
        except (urllib.error.URLError, OSError) as e:
            print(f"  ✗ {label} ({url}) unreachable: {e}")
            print("    Start services: docker compose --profile fraiseql up -d")
            raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FraiseQL v_* vs tv_* comparison benchmark"
    )
    parser.add_argument("--duration",    type=int, default=30,
                        help="Seconds per query per variant (default: 30)")
    parser.add_argument("--concurrency", type=int, default=50,
                        help="Concurrent workers per test (default: 50)")
    parser.add_argument("--warmup",      type=int, default=10,
                        help="Warmup seconds per query (default: 10)")
    parser.add_argument("--output",      type=str, default=None,
                        help="Report output path (default: reports/fraiseql-comparison-YYYY-MM-DD.md)")
    args = parser.parse_args()

    print("FraiseQL v_* vs tv_* Comparison Benchmark")
    print("=" * 50)
    print(f"Duration: {args.duration}s/query  Concurrency: {args.concurrency}  Warmup: {args.warmup}s")
    print()

    print("Checking services...")
    check_services()
    print()

    results: dict[tuple[str, str], BenchResult] = {}

    for qname, query in QUERIES.items():
        print(f"--- {qname} ---")
        for variant, url in VARIANTS.items():
            warmup(variant, url, qname, query, args.concurrency, args.warmup)
            print(f"  benchmarking {variant}/{qname} ({args.duration}s)...", flush=True)
            r = run_benchmark(variant, url, qname, query, args.concurrency, args.duration)
            results[(qname, variant)] = r
            print(
                f"    {r.rps:.0f} RPS  p50={r.p50_ms:.1f}ms  "
                f"p99={r.p99_ms:.1f}ms  errors={r.errors}"
            )
        print()

    report = format_report(results, args)
    print()
    print(report)

    # Write report to disk
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = args.output or f"reports/fraiseql-comparison-{date_str}.md"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(report)
    print(f"\nReport written to: {output_path}")


if __name__ == "__main__":
    main()
