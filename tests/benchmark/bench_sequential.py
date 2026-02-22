#!/usr/bin/env python3
"""
VelocityBench — Sequential Isolation Benchmark
===============================================

Benchmarks each framework in isolation: starts one service, runs the full
query suite against it, stops it, then moves to the next. This prevents
resource contention between frameworks and gives each one the full machine.

PostgreSQL must already be running:
    docker compose up -d postgres

Usage:
    python tests/benchmark/bench_sequential.py
    python tests/benchmark/bench_sequential.py --frameworks fraiseql-tv fraiseql-v
    python tests/benchmark/bench_sequential.py --duration 30 --concurrency 40
    python tests/benchmark/bench_sequential.py --no-isolation  # all services pre-started

Query suite (matches results_20260221.md baseline):
    Q1   — users(limit:20) { id username fullName }          flat list
    Q2   — posts(limit:10) { id title }                      no nesting
    Q2b  — posts(limit:10) { id title author { ... } }       1-level nest
"""

import argparse
import json
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Framework registry
# ---------------------------------------------------------------------------

# Each entry: compose_service (docker-compose service name), type (graphql|rest),
# and per-query (url, payload) pairs. None means the query is skipped for this
# framework (known bug or N/A).

_GQL_Q1  = "{ users(limit: 20) { id username fullName } }"
_GQL_Q2  = "{ posts(limit: 10) { id title } }"
_GQL_Q2b = "{ posts(limit: 10) { id title author { username fullName } } }"

FRAMEWORKS: dict[str, dict] = {
    # ------------------------------------------------------------------
    # Rust frameworks
    # ------------------------------------------------------------------
    "actix-web-rest": {
        "compose_service": "actix-web-rest",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8015/users?limit=20",
            "Q2":  "http://localhost:8015/posts?limit=10",
            "Q2b": "http://localhost:8015/posts?limit=10",  # always includes author JOIN
        },
        "health_url": "http://localhost:8015/health",
    },
    "async-graphql": {
        "compose_service": "async-graphql",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8016/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8016/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8016/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8016/health",
    },
    "juniper": {
        "compose_service": "juniper",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Go frameworks
    # ------------------------------------------------------------------
    "go-gqlgen": {
        "compose_service": "go-gqlgen",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4010/query", _GQL_Q1),
            "Q2":  ("http://localhost:4010/query", _GQL_Q2),
            "Q2b": None,  # SKIP: author resolver architectural bug (fk_author→UUID mismatch)
        },
        "health_url": "http://localhost:4010/health",
    },
    "gin-rest": {
        "compose_service": "gin-rest",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8006/users?limit=20",
            "Q2":  "http://localhost:8006/posts?limit=10",
            "Q2b": "http://localhost:8006/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8006/health",
    },
    "go-graphql-go": {
        "compose_service": "go-graphql-go",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8008/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8008/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8008/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8008/health",
    },
    # ------------------------------------------------------------------
    # Node.js frameworks
    # ------------------------------------------------------------------
    "apollo-server": {
        "compose_service": "apollo",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4002/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4002/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4002/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4002/health",
    },
    "apollo-orm": {
        "compose_service": "apollo-orm",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4004/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4004/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4004/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4005/health",  # health on separate port
    },
    "express-rest": {
        "compose_service": "express-rest",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8005/users?limit=20",
            "Q2":  "http://localhost:8005/posts?limit=10",
            "Q2b": "http://localhost:8005/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8005/health",
    },
    "express-orm": {
        "compose_service": "express-orm",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8007/users?limit=20",
            "Q2":  "http://localhost:8007/posts?limit=10",
            "Q2b": "http://localhost:8007/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8007/health",
    },
    "express-graphql": {
        "compose_service": "express-graphql",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "graphql-yoga": {
        "compose_service": "graphql-yoga",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "mercurius": {
        "compose_service": "mercurius",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Python frameworks
    # ------------------------------------------------------------------
    "strawberry": {
        "compose_service": "strawberry",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8011/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8011/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8011/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8011/health",
    },
    "graphene": {
        "compose_service": "graphene",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8002/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8002/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8002/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8002/health",
    },
    "fastapi-rest": {
        "compose_service": "fastapi-rest",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8003/users?limit=20",
            "Q2":  "http://localhost:8003/posts?limit=10",
            "Q2b": "http://localhost:8003/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8003/health",
    },
    "flask-rest": {
        "compose_service": "flask-rest",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8004/users?limit=20",
            "Q2":  "http://localhost:8004/posts?limit=10",
            "Q2b": "http://localhost:8004/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8004/health",
    },
    "ariadne": {
        "compose_service": "ariadne",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "asgi-graphql": {
        "compose_service": "asgi-graphql",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Java / JVM frameworks
    # ------------------------------------------------------------------
    "spring-boot": {
        "compose_service": "spring-boot",
        "type": "rest",
        "queries": {
            # Spring Boot uses page/size pagination, not limit
            "Q1":  "http://localhost:8010/api/users?page=0&size=20",
            "Q2":  "http://localhost:8010/api/posts?page=0&size=10",
            "Q2b": None,  # PostDTO has authorId only — no nested author object
        },
        "health_url": "http://localhost:8010/actuator/health",
    },
    "spring-boot-orm": {
        "compose_service": "spring-boot-orm",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8013/api/users?page=0&size=20",
            "Q2":  "http://localhost:8013/api/posts?size=10",
            "Q2b": None,  # PostDTO has authorId only — no nested author object
        },
        "health_url": "http://localhost:8013/actuator/health",
    },
    "micronaut-graphql": {
        "compose_service": "micronaut-graphql",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "quarkus-graphql": {
        "compose_service": "quarkus-graphql",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Scala frameworks
    # ------------------------------------------------------------------
    "play-graphql": {
        "compose_service": "play-graphql",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Ruby frameworks
    # ------------------------------------------------------------------
    "ruby-rails": {
        "compose_service": "ruby-rails",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8012/api/users?limit=20",
            "Q2":  "http://localhost:8012/api/posts?limit=10",
            "Q2b": None,  # no nested author embedding
        },
        "health_url": "http://localhost:8012/api/health",
    },
    "hanami": {
        "compose_service": "hanami",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # PHP frameworks
    # ------------------------------------------------------------------
    "php-laravel": {
        "compose_service": "php-laravel",
        "type": "rest",
        "queries": {
            "Q1":  "http://localhost:8009/api/users?limit=20",
            "Q2":  "http://localhost:8009/api/posts?limit=10",
            "Q2b": None,  # no nested author embedding
        },
        "health_url": "http://localhost:8009/api/health",
    },
    "webonyx-graphql-php": {
        "compose_service": "webonyx-graphql-php",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # C# / .NET frameworks
    # ------------------------------------------------------------------
    "csharp-dotnet": {
        "compose_service": "csharp-dotnet",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8025/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8025/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8025/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8025/health",
    },
    # ------------------------------------------------------------------
    # FraiseQL variants (last — pending upstream fixes)
    # ------------------------------------------------------------------
    "fraiseql-tv": {
        "compose_service": "fraiseql-tv",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8816/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8816/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8816/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8816/health",
        # LRU cache needs 30s warmup to fill before measuring cache-hit throughput.
        "warmup_secs": 30,
    },
    "fraiseql-tv-nocache": {
        "compose_service": "fraiseql-tv-nocache",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8817/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8817/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8817/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8817/health",
    },
    "fraiseql-v": {
        "compose_service": "fraiseql",
        "type": "graphql",
        "queries": {
            "Q1":  ("http://localhost:8815/graphql", _GQL_Q1),
            "Q2":  ("http://localhost:8815/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8815/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8815/health",
        "warmup_secs": 30,
    },
}

# Ordered for a single full-suite run: fastest first (Rust/Go), then compiled
# (JVM/.NET), then interpreted (Node/Python/Ruby/PHP), then FraiseQL last.
DEFAULT_FRAMEWORK_ORDER = [
    # Rust
    "actix-web-rest",
    "async-graphql",
    "juniper",
    # Go
    "go-gqlgen",
    "gin-rest",
    "go-graphql-go",
    # Node.js
    "apollo-server",
    "apollo-orm",
    "express-rest",
    "express-orm",
    "express-graphql",
    "graphql-yoga",
    "mercurius",
    # Python
    "strawberry",
    "graphene",
    "fastapi-rest",
    "flask-rest",
    "ariadne",
    "asgi-graphql",
    # Java / JVM
    "spring-boot",
    "spring-boot-orm",
    "micronaut-graphql",
    "quarkus-graphql",
    # Scala
    "play-graphql",
    # Ruby
    "ruby-rails",
    "hanami",
    # PHP
    "php-laravel",
    "webonyx-graphql-php",
    # C# / .NET
    "csharp-dotnet",
    # FraiseQL (last — regression pending upstream fix)
    "fraiseql-tv",
    "fraiseql-tv-nocache",
    "fraiseql-v",
]

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BenchResult:
    framework: str
    query_name: str
    duration_secs: int
    concurrency: int
    latencies_ms: list[float] = field(default_factory=list)
    errors: int = 0
    skipped: bool = False
    skip_reason: str = ""

    @property
    def requests_sent(self) -> int:
        return len(self.latencies_ms)

    @property
    def rps(self) -> float:
        return self.requests_sent / self.duration_secs if self.duration_secs > 0 else 0.0

    @property
    def p50_ms(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        s = sorted(self.latencies_ms)
        return s[int(len(s) * 0.95)]

    @property
    def p99_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        s = sorted(self.latencies_ms)
        return s[int(len(s) * 0.99)]

    @property
    def error_rate_pct(self) -> float:
        total = self.requests_sent + self.errors
        return (self.errors / total * 100) if total > 0 else 0.0


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _post_graphql(url: str, query: str, timeout: int = 10) -> tuple[bool, float]:
    """Execute one GraphQL POST. Returns (success, latency_ms)."""
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
        return False, (time.monotonic() - t0) * 1000


def _get_rest(url: str, timeout: int = 10) -> tuple[bool, float]:
    """Execute one REST GET. Returns (success, latency_ms)."""
    req = urllib.request.Request(url, method="GET")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            elapsed = (time.monotonic() - t0) * 1000
            return resp.status == 200, elapsed
    except (urllib.error.URLError, OSError):
        return False, (time.monotonic() - t0) * 1000


def _worker_graphql(url: str, query: str, end_time: float) -> tuple[list[float], int]:
    latencies: list[float] = []
    errors = 0
    while time.monotonic() < end_time:
        ok, lat = _post_graphql(url, query)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
    return latencies, errors


def _worker_rest(url: str, end_time: float) -> tuple[list[float], int]:
    latencies: list[float] = []
    errors = 0
    while time.monotonic() < end_time:
        ok, lat = _get_rest(url)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
    return latencies, errors


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------


def run_scenario(
    fw_name: str,
    fw_config: dict,
    query_name: str,
    concurrency: int,
    duration_secs: int,
    warmup_secs: int,
) -> BenchResult:
    # Per-framework warmup override (e.g. cache-enabled fraiseql needs 30s to fill LRU).
    warmup_secs = fw_config.get("warmup_secs", warmup_secs)
    """Run warmup then measurement for one (framework, query) pair."""
    entry = fw_config["queries"][query_name]
    result = BenchResult(
        framework=fw_name,
        query_name=query_name,
        duration_secs=duration_secs,
        concurrency=concurrency,
    )

    if entry is None:
        result.skipped = True
        result.skip_reason = "known bug — skipped"
        return result

    fw_type = fw_config["type"]

    def _run_workers(secs: int) -> tuple[list[float], int]:
        end_time = time.monotonic() + secs
        all_lats: list[float] = []
        all_errs = 0
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            if fw_type == "graphql":
                url, query = entry
                futures = [pool.submit(_worker_graphql, url, query, end_time)
                           for _ in range(concurrency)]
            else:
                url = entry
                futures = [pool.submit(_worker_rest, url, end_time)
                           for _ in range(concurrency)]
            for fut in as_completed(futures):
                lats, errs = fut.result()
                all_lats.extend(lats)
                all_errs += errs
        return all_lats, all_errs

    # Warmup (discard results)
    print(f"    warmup {warmup_secs}s...", end=" ", flush=True)
    _run_workers(warmup_secs)
    print("done", flush=True)

    # Measurement
    print(f"    measuring {duration_secs}s...", end=" ", flush=True)
    lats, errs = _run_workers(duration_secs)
    result.latencies_ms = lats
    result.errors = errs
    print(
        f"{result.rps:.0f} RPS  "
        f"p50={result.p50_ms:.1f}ms  "
        f"p95={result.p95_ms:.1f}ms  "
        f"p99={result.p99_ms:.1f}ms  "
        f"errors={result.errors}",
        flush=True,
    )
    return result


# ---------------------------------------------------------------------------
# Docker lifecycle helpers
# ---------------------------------------------------------------------------


def _compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=str(Path(__file__).parent.parent.parent),
        capture_output=True,
        text=True,
        check=check,
    )


def start_service(service: str, health_url: str, timeout_secs: int = 60) -> None:
    print(f"  starting {service}...", end=" ", flush=True)
    _compose("up", "-d", service)
    deadline = time.monotonic() + timeout_secs
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as resp:
                if resp.status == 200:
                    print("healthy ✓", flush=True)
                    return
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(1)
    print("timed out ✗", flush=True)
    raise RuntimeError(f"{service} did not become healthy within {timeout_secs}s")


def stop_service(service: str) -> None:
    print(f"  stopping {service}...", end=" ", flush=True)
    _compose("stop", service)
    print("stopped", flush=True)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def _row(r: BenchResult) -> str:
    if r.skipped:
        return f"| {r.framework} | {r.query_name} | — | — | — | — | — | _{r.skip_reason}_ |"
    return (
        f"| {r.framework} | {r.query_name} "
        f"| {r.rps:.0f} "
        f"| {r.p50_ms:.1f} "
        f"| {r.p95_ms:.1f} "
        f"| {r.p99_ms:.1f} "
        f"| {r.requests_sent:,} "
        f"| {r.error_rate_pct:.1f}% |"
    )


def format_report(
    results: list[BenchResult],
    args: argparse.Namespace,
    date_str: str,
) -> str:
    lines: list[str] = [
        "# VelocityBench — Sequential Isolation Benchmark Results",
        "",
        f"**Date**: {date_str}  ",
        f"**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  ",
        f"**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  ",
        f"**Concurrency**: {args.concurrency} workers  ",
        f"**Measurement**: {args.duration}s per scenario  ",
        f"**Warmup**: {args.warmup}s per scenario  ",
        f"**Cooldown**: {args.cooldown}s between frameworks  ",
        "",
        "---",
        "",
        "## Q1 — `users(limit: 20) { id username fullName }`",
        "",
        "| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |",
        "|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|",
    ]
    for r in results:
        if r.query_name == "Q1":
            lines.append(_row(r))

    lines += [
        "",
        "## Q2 — `posts(limit: 10) { id title }`",
        "",
        "| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |",
        "|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|",
    ]
    for r in results:
        if r.query_name == "Q2":
            lines.append(_row(r))

    lines += [
        "",
        "## Q2b — `posts(limit: 10) { id title author { username fullName } }`",
        "",
        "| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |",
        "|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|",
    ]
    for r in results:
        if r.query_name == "Q2b":
            lines.append(_row(r))

    # Summary: Q1 cross-framework comparison
    lines += [
        "",
        "---",
        "",
        "## Summary — Q1 Cross-Framework (sorted by RPS)",
        "",
        "| Framework | Cache | RPS | p50 ms | p99 ms |",
        "|-----------|-------|----:|-------:|-------:|",
    ]
    q1_results = sorted(
        [r for r in results if r.query_name == "Q1" and not r.skipped],
        key=lambda r: r.rps,
        reverse=True,
    )
    for r in q1_results:
        cache_label = "off" if "nocache" in r.framework else "on"
        lines.append(
            f"| {r.framework} | {cache_label} "
            f"| {r.rps:.0f} | {r.p50_ms:.1f} | {r.p99_ms:.1f} |"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sequential isolation benchmark for VelocityBench frameworks"
    )
    parser.add_argument(
        "--frameworks",
        nargs="+",
        default=DEFAULT_FRAMEWORK_ORDER,
        metavar="FW",
        help=f"Frameworks to run (default: {' '.join(DEFAULT_FRAMEWORK_ORDER)})",
    )
    parser.add_argument(
        "--duration", type=int, default=20,
        help="Measurement seconds per scenario (default: 20)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=40,
        help="Concurrent workers (default: 40)",
    )
    parser.add_argument(
        "--warmup", type=int, default=5,
        help="Warmup seconds per scenario (default: 5)",
    )
    parser.add_argument(
        "--cooldown", type=int, default=5,
        help="Cooldown seconds between frameworks (default: 5)",
    )
    parser.add_argument(
        "--no-isolation", action="store_true",
        help="Skip docker start/stop — assume all services already running",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Report output path (default: reports/bench-sequential-YYYY-MM-DD.md)",
    )
    args = parser.parse_args()

    unknown = [fw for fw in args.frameworks if fw not in FRAMEWORKS]
    if unknown:
        print(f"Unknown frameworks: {unknown}", file=sys.stderr)
        print(f"Available: {list(FRAMEWORKS)}", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    print("VelocityBench — Sequential Isolation Benchmark")
    print("=" * 55)
    print(f"Frameworks  : {', '.join(args.frameworks)}")
    print(f"Concurrency : {args.concurrency} workers")
    print(f"Measurement : {args.duration}s / scenario")
    print(f"Warmup      : {args.warmup}s / scenario")
    print(f"Cooldown    : {args.cooldown}s between frameworks")
    print(f"Isolation   : {'disabled (--no-isolation)' if args.no_isolation else 'enabled'}")
    print()

    all_results: list[BenchResult] = []

    for i, fw_name in enumerate(args.frameworks):
        fw_config = FRAMEWORKS[fw_name]
        print(f"[{i + 1}/{len(args.frameworks)}] {fw_name}")

        if not args.no_isolation:
            start_service(fw_config["compose_service"], fw_config["health_url"])

        for query_name in ("Q1", "Q2", "Q2b"):
            print(f"  {query_name}:")
            r = run_scenario(fw_name, fw_config, query_name, args.concurrency,
                             args.duration, args.warmup)
            all_results.append(r)

        if not args.no_isolation:
            stop_service(fw_config["compose_service"])

        if i < len(args.frameworks) - 1:
            print(f"  cooldown {args.cooldown}s...", flush=True)
            time.sleep(args.cooldown)
        print()

    report = format_report(all_results, args, date_str)

    output_path = Path(args.output) if args.output else REPORTS_DIR / f"bench-sequential-{date_str}.md"
    output_path.write_text(report)

    print(report)
    print(f"\nReport written to: {output_path}")

    # Also write JSON for programmatic use
    json_path = output_path.with_suffix(".json")
    json_data = [
        {
            "framework": r.framework,
            "query": r.query_name,
            "rps": round(r.rps, 1),
            "p50_ms": round(r.p50_ms, 2),
            "p95_ms": round(r.p95_ms, 2),
            "p99_ms": round(r.p99_ms, 2),
            "requests": r.requests_sent,
            "errors": r.errors,
            "skipped": r.skipped,
            "skip_reason": r.skip_reason,
        }
        for r in all_results
    ]
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"JSON data written to: {json_path}")


if __name__ == "__main__":
    main()
