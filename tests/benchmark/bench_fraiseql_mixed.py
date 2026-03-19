#!/usr/bin/env python3
"""
VelocityBench — FraiseQL Mixed Workload Benchmark (Phase 4)
============================================================

Benchmarks FraiseQL under realistic mixed read/write traffic (80/20 pattern).
Requires fraiseql-tv to be running with mutations enabled.

PostgreSQL must already be running:
    docker compose up -d postgres fraiseql-tv

Scenarios:
    X1 — 32 read workers + 8 write workers simultaneously (30s after 10s warmup)
    X2 — Cache invalidation storm: 10s reads → 5s burst writes → 10s reads

Usage:
    python tests/benchmark/bench_fraiseql_mixed.py
    python tests/benchmark/bench_fraiseql_mixed.py --url http://localhost:8816/graphql
    python tests/benchmark/bench_fraiseql_mixed.py --scenario X1
    python tests/benchmark/bench_fraiseql_mixed.py --scenario X2
"""

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"

_GQL_USERS = "{ users(limit: 20) { id username fullName } }"
_GQL_POSTS = "{ posts(limit: 10) { id title author { username } } }"
_M1_TMPL = 'mutation {{ updateUser(id: "{user_id}", bio: "bench-{ts}") {{ id bio }} }}'

_MAX_ERROR_SAMPLES = 3


@dataclass
class WorkloadResult:
    scenario: str
    phase: str  # "warmup", "read", "write", "mixed"
    read_latencies_ms: list[float] = field(default_factory=list)
    write_latencies_ms: list[float] = field(default_factory=list)
    read_errors: int = 0
    write_errors: int = 0
    duration_secs: float = 0.0

    @property
    def read_rps(self) -> float:
        return len(self.read_latencies_ms) / self.duration_secs if self.duration_secs else 0.0

    @property
    def write_rps(self) -> float:
        return len(self.write_latencies_ms) / self.duration_secs if self.duration_secs else 0.0

    @property
    def read_p50_ms(self) -> float:
        return statistics.median(self.read_latencies_ms) if self.read_latencies_ms else 0.0

    @property
    def read_p99_ms(self) -> float:
        if not self.read_latencies_ms:
            return 0.0
        s = sorted(self.read_latencies_ms)
        return s[int(len(s) * 0.99)]

    @property
    def write_p50_ms(self) -> float:
        return statistics.median(self.write_latencies_ms) if self.write_latencies_ms else 0.0

    @property
    def write_p99_ms(self) -> float:
        if not self.write_latencies_ms:
            return 0.0
        s = sorted(self.write_latencies_ms)
        return s[int(len(s) * 0.99)]

    @property
    def read_error_pct(self) -> float:
        total = len(self.read_latencies_ms) + self.read_errors
        return (self.read_errors / total * 100) if total else 0.0

    @property
    def write_error_pct(self) -> float:
        total = len(self.write_latencies_ms) + self.write_errors
        return (self.write_errors / total * 100) if total else 0.0


def _post_graphql(url: str, query: str, timeout: int = 10) -> tuple[bool, float]:
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            elapsed = (time.monotonic() - t0) * 1000
            if resp.status != 200:
                return False, elapsed
            body = json.loads(raw)
            if body.get("errors") or "data" not in body:
                return False, elapsed
            return True, elapsed
    except (urllib.error.URLError, OSError):
        return False, (time.monotonic() - t0) * 1000


def _discover_user_uuid(url: str) -> str | None:
    payload = json.dumps({"query": _GQL_USERS}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            users = body.get("data", {}).get("users", [])
            if users:
                return str(users[0]["id"])
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, IndexError):
        pass
    return None


def _read_worker(url: str, end_time: float) -> tuple[list[float], int]:
    latencies: list[float] = []
    errors = 0
    queries = [_GQL_USERS, _GQL_POSTS]
    i = 0
    while time.monotonic() < end_time:
        ok, lat = _post_graphql(url, queries[i % len(queries)])
        if ok:
            latencies.append(lat)
        else:
            errors += 1
        i += 1
    return latencies, errors


def _write_worker(url: str, mutation: str, end_time: float) -> tuple[list[float], int]:
    latencies: list[float] = []
    errors = 0
    while time.monotonic() < end_time:
        # Vary bio content to avoid 100% cache hits on the mutation result
        ts = int(time.monotonic() * 1000) % 100000
        query = mutation.format(ts=ts)
        ok, lat = _post_graphql(url, query)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
    return latencies, errors


def run_x1(url: str, user_id: str, warmup_secs: int = 10, duration_secs: int = 30) -> WorkloadResult:
    """X1: 32 read workers + 8 write workers simultaneously."""
    mutation = _M1_TMPL.format(user_id=user_id, ts="{ts}")
    result = WorkloadResult(scenario="X1", phase="mixed", duration_secs=duration_secs)

    print(f"  X1: warmup {warmup_secs}s (reads only)...", end=" ", flush=True)
    warmup_end = time.monotonic() + warmup_secs
    with ThreadPoolExecutor(max_workers=32) as pool:
        futs = [pool.submit(_read_worker, url, warmup_end) for _ in range(32)]
        for f in as_completed(futs):
            f.result()  # discard warmup results
    print("done", flush=True)

    print(f"  X1: measuring {duration_secs}s (32 readers + 8 writers)...", end=" ", flush=True)
    measure_end = time.monotonic() + duration_secs
    t_start = time.monotonic()

    all_read_lats: list[float] = []
    all_write_lats: list[float] = []
    read_errors = 0
    write_errors = 0

    with ThreadPoolExecutor(max_workers=40) as pool:
        read_futs = [pool.submit(_read_worker, url, measure_end) for _ in range(32)]
        write_futs = [pool.submit(_write_worker, url, mutation, measure_end) for _ in range(8)]
        for f in as_completed(read_futs):
            lats, errs = f.result()
            all_read_lats.extend(lats)
            read_errors += errs
        for f in as_completed(write_futs):
            lats, errs = f.result()
            all_write_lats.extend(lats)
            write_errors += errs

    result.duration_secs = time.monotonic() - t_start
    result.read_latencies_ms = all_read_lats
    result.write_latencies_ms = all_write_lats
    result.read_errors = read_errors
    result.write_errors = write_errors

    print(
        f"reads: {result.read_rps:.0f} RPS p50={result.read_p50_ms:.1f}ms p99={result.read_p99_ms:.1f}ms  "
        f"writes: {result.write_rps:.0f} RPS p99={result.write_p99_ms:.1f}ms",
        flush=True,
    )
    return result


def run_x2(url: str, user_id: str) -> list[WorkloadResult]:
    """X2: Cache invalidation storm — 10s reads → 5s burst writes → 10s reads."""
    mutation = _M1_TMPL.format(user_id=user_id, ts="{ts}")
    results: list[WorkloadResult] = []

    phases = [
        ("phase1_reads", 10, 32, 0, "10s warm reads (pre-invalidation)"),
        ("phase2_writes", 5, 0, 16, "5s burst writes (cache invalidation)"),
        ("phase3_reads", 10, 32, 0, "10s reads (post-invalidation re-warm)"),
    ]

    for phase_name, secs, n_readers, n_writers, label in phases:
        print(f"  X2 {label}...", end=" ", flush=True)
        end_time = time.monotonic() + secs
        t_start = time.monotonic()
        r = WorkloadResult(scenario="X2", phase=phase_name, duration_secs=secs)

        with ThreadPoolExecutor(max_workers=max(n_readers + n_writers, 1)) as pool:
            futs_r = [pool.submit(_read_worker, url, end_time) for _ in range(n_readers)]
            futs_w = [pool.submit(_write_worker, url, mutation, end_time) for _ in range(n_writers)]
            for f in as_completed(futs_r):
                lats, errs = f.result()
                r.read_latencies_ms.extend(lats)
                r.read_errors += errs
            for f in as_completed(futs_w):
                lats, errs = f.result()
                r.write_latencies_ms.extend(lats)
                r.write_errors += errs

        r.duration_secs = time.monotonic() - t_start
        if n_readers:
            print(
                f"reads: {r.read_rps:.0f} RPS p99={r.read_p99_ms:.1f}ms",
                flush=True,
            )
        else:
            print(
                f"writes: {r.write_rps:.0f} RPS p99={r.write_p99_ms:.1f}ms",
                flush=True,
            )
        results.append(r)

    return results


def format_report(results: list[WorkloadResult], date_str: str, url: str) -> str:
    lines = [
        "# VelocityBench — FraiseQL Mixed Workload Benchmark (Phase 4)",
        "",
        f"**Date**: {date_str}  ",
        f"**Target**: {url}  ",
        "**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  ",
        "",
        "---",
        "",
        "## X1 — Sustained Mixed Workload (32 readers + 8 writers)",
        "",
        "| Phase | Read RPS | Read p50 ms | Read p99 ms | Write RPS | Write p99 ms | Read Errors | Write Errors |",
        "|-------|----------|-------------|-------------|-----------|--------------|-------------|--------------|",
    ]
    for r in results:
        if r.scenario == "X1":
            lines.append(
                f"| mixed | {r.read_rps:.0f} | {r.read_p50_ms:.1f} | {r.read_p99_ms:.1f} "
                f"| {r.write_rps:.0f} | {r.write_p99_ms:.1f} "
                f"| {r.read_error_pct:.1f}% | {r.write_error_pct:.1f}% |"
            )

    x2 = [r for r in results if r.scenario == "X2"]
    if x2:
        lines += [
            "",
            "## X2 — Cache Invalidation Storm",
            "",
            "| Phase | Description | RPS | p50 ms | p99 ms | Errors |",
            "|-------|-------------|----:|-------:|-------:|--------|",
        ]
        phase_labels = {
            "phase1_reads": "Pre-invalidation reads (cache warm)",
            "phase2_writes": "Burst writes (cache invalidation)",
            "phase3_reads": "Post-invalidation reads (re-warm)",
        }
        for r in x2:
            label = phase_labels.get(r.phase, r.phase)
            if r.read_latencies_ms:
                lines.append(
                    f"| {r.phase} | {label} | {r.read_rps:.0f} | {r.read_p50_ms:.1f} "
                    f"| {r.read_p99_ms:.1f} | {r.read_error_pct:.1f}% |"
                )
            else:
                lines.append(
                    f"| {r.phase} | {label} | {r.write_rps:.0f} | {r.write_p50_ms:.1f} "
                    f"| {r.write_p99_ms:.1f} | {r.write_error_pct:.1f}% |"
                )

    lines += [
        "",
        "---",
        "",
        "## Interpretation",
        "",
        "- **X1**: Shows read throughput under sustained write pressure.",
        "  Compare read p99 to Q2b from bench_sequential.py (reads-only baseline).",
        "- **X2**: Shows cache re-warm speed after invalidation.",
        "  Phase 1 p99 (warm cache) vs Phase 3 p99 (re-warming) quantifies re-warm overhead.",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FraiseQL mixed workload benchmark (Phase 4)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8816/graphql",
        help="FraiseQL GraphQL endpoint (default: fraiseql-tv port 8816)",
    )
    parser.add_argument(
        "--scenario",
        choices=["X1", "X2", "all"],
        default="all",
        help="Scenario to run (default: all)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="X1 warmup seconds (default: 10)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="X1 measurement seconds (default: 30)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Report output path",
    )
    args = parser.parse_args()

    date_str = datetime.now().strftime("%Y-%m-%d")

    print("VelocityBench — FraiseQL Mixed Workload (Phase 4)")
    print("=" * 55)
    print(f"Endpoint  : {args.url}")
    print(f"Scenario  : {args.scenario}")
    print()

    print("Discovering user UUID...", end=" ", flush=True)
    user_id = _discover_user_uuid(args.url)
    if not user_id:
        print("FAILED — is fraiseql-tv running?", file=sys.stderr)
        sys.exit(1)
    print(f"{user_id[:8]}...", flush=True)
    print()

    all_results: list[WorkloadResult] = []

    if args.scenario in ("X1", "all"):
        print("[X1] Sustained mixed workload (32 readers + 8 writers)")
        r = run_x1(args.url, user_id, warmup_secs=args.warmup, duration_secs=args.duration)
        all_results.append(r)
        print()

    if args.scenario in ("X2", "all"):
        print("[X2] Cache invalidation storm")
        x2_results = run_x2(args.url, user_id)
        all_results.extend(x2_results)
        print()

    report = format_report(all_results, date_str, args.url)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = (
        Path(args.output)
        if args.output
        else REPORTS_DIR / f"bench-fraiseql-mixed-{date_str}.md"
    )
    output_path.write_text(report)
    print(report)
    print(f"\nReport written to: {output_path}")


if __name__ == "__main__":
    main()
