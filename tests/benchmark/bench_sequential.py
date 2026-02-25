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
    python tests/benchmark/bench_sequential.py --diagnose --frameworks strawberry
    python tests/benchmark/bench_sequential.py --verbose --detailed-errors

Query suite:
    Q1   — users(limit:20) { id username fullName }          flat list
    Q2   — posts(limit:10) { id title }                      no nesting
    Q2b  — posts(limit:10) { id title author { ... } }       1-level nest
    Q3   — comments(limit:20) { id content author post }     2-level nest (GraphQL only)
    M1   — mutation updateUser(...)                           mutation (optional)
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

_GQL_Q1 = "{ users(limit: 20) { id username fullName } }"
_GQL_Q2 = "{ posts(limit: 10) { id title } }"
_GQL_Q2b = "{ posts(limit: 10) { id title author { username fullName } } }"
_GQL_Q3 = "{ comments(limit: 20) { id content author { username } post { title } } }"
_GQL_M1_TMPL = (
    'mutation {{ updateUser(id: "{user_id}", input: {{ bio: "bench" }}) {{ id bio }} }}'
)

FRAMEWORKS: dict[str, dict] = {
    # ------------------------------------------------------------------
    # Rust frameworks
    # ------------------------------------------------------------------
    "actix-web-rest": {
        "compose_service": "actix-web-rest",
        "type": "rest",
        "queries": {
            "Q1": "http://localhost:8015/users?limit=20",
            "Q2": "http://localhost:8015/posts?limit=10",
            "Q2b": "http://localhost:8015/posts?limit=10",  # always includes author JOIN
            "M1": "M1",  # resolved at runtime with discovered user UUID
        },
        "health_url": "http://localhost:8015/health",
    },
    "async-graphql": {
        "compose_service": "async-graphql",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:8016/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8016/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8016/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8016/graphql", _GQL_Q3),
            "M1": "M1",  # resolved at runtime with discovered user UUID
        },
        "health_url": "http://localhost:8016/health",
    },
    "juniper": {
        "compose_service": "juniper",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:4000/graphql", _GQL_Q3),
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
            "Q1": ("http://localhost:4010/query", _GQL_Q1),
            "Q2": ("http://localhost:4010/query", _GQL_Q2),
            "Q2b": ("http://localhost:4010/query", _GQL_Q2b),
            "Q3": ("http://localhost:4010/query", _GQL_Q3),
        },
        "health_url": "http://localhost:4010/health",
    },
    "gin-rest": {
        "compose_service": "gin-rest",
        "type": "rest",
        "queries": {
            "Q1": "http://localhost:8006/users?limit=20",
            "Q2": "http://localhost:8006/posts?limit=10",
            "Q2b": "http://localhost:8006/posts?limit=10&include=author",
            "M1": "M1",  # resolved at runtime with discovered user UUID
        },
        "health_url": "http://localhost:8006/health",
    },
    "go-graphql-go": {
        "compose_service": "go-graphql-go",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:8008/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8008/graphql", _GQL_Q2),
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
            "Q1": ("http://localhost:4002/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4002/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4002/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4002/health",
    },
    "apollo-orm": {
        "compose_service": "apollo-orm",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4004/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4004/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4004/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4005/health",  # health on separate port
    },
    "express-rest": {
        "compose_service": "express-rest",
        "type": "rest",
        "queries": {
            "Q1": "http://localhost:8005/users?limit=20",
            "Q2": "http://localhost:8005/posts?limit=10",
            "Q2b": "http://localhost:8005/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8005/health",
    },
    "express-orm": {
        "compose_service": "express-orm",
        "type": "rest",
        "queries": {
            "Q1": "http://localhost:8007/users?limit=20",
            "Q2": "http://localhost:8007/posts?limit=10",
            "Q2b": "http://localhost:8007/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8007/health",
    },
    "express-graphql": {
        "compose_service": "express-graphql",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "graphql-yoga": {
        "compose_service": "graphql-yoga",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "mercurius": {
        "compose_service": "mercurius",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
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
            "Q1": ("http://localhost:8011/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8011/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8011/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8011/health",
    },
    "graphene": {
        "compose_service": "graphene",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:8002/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8002/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8002/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:8002/health",
    },
    "fastapi-rest": {
        "compose_service": "fastapi-rest",
        "type": "rest",
        "queries": {
            "Q1": "http://localhost:8003/users?limit=20",
            "Q2": "http://localhost:8003/posts?limit=10",
            "Q2b": "http://localhost:8003/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8003/health",
    },
    "flask-rest": {
        "compose_service": "flask-rest",
        "type": "rest",
        "queries": {
            "Q1": "http://localhost:8004/users?limit=20",
            "Q2": "http://localhost:8004/posts?limit=10",
            "Q2b": "http://localhost:8004/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8004/health",
    },
    "ariadne": {
        "compose_service": "ariadne",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "asgi-graphql": {
        "compose_service": "asgi-graphql",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
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
            "Q1": "http://localhost:8010/api/users?page=0&size=20",
            "Q2": "http://localhost:8010/api/posts?page=0&size=10",
            "Q2b": None,  # PostDTO has authorId only — no nested author object
        },
        "health_url": "http://localhost:8010/actuator/health",
    },
    "spring-boot-orm": {
        "compose_service": "spring-boot-orm",
        "type": "rest",
        "queries": {
            "Q1": "http://localhost:8013/api/users?page=0&size=20",
            "Q2": "http://localhost:8013/api/posts?size=10",
            "Q2b": "http://localhost:8013/api/posts?size=10&include=author",
        },
        "health_url": "http://localhost:8013/actuator/health",
    },
    "micronaut-graphql": {
        "compose_service": "micronaut-graphql",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
        },
        "health_url": "http://localhost:4000/health",
    },
    "quarkus-graphql": {
        "compose_service": "quarkus-graphql",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:4000/graphql", _GQL_Q3),
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
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
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
            "Q1": "http://localhost:8012/api/users?limit=20",
            "Q2": "http://localhost:8012/api/posts?limit=10",
            "Q2b": None,  # no nested author embedding
        },
        "health_url": "http://localhost:8012/api/health",
    },
    "hanami": {
        "compose_service": "hanami",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
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
            "Q1": "http://localhost:8009/api/users?limit=20",
            "Q2": "http://localhost:8009/api/posts?limit=10",
            "Q2b": "http://localhost:8009/api/posts?limit=10&include=author",
        },
        "health_url": "http://localhost:8009/api/health",
    },
    "webonyx-graphql-php": {
        "compose_service": "webonyx-graphql-php",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
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
            "Q1": ("http://localhost:8025/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8025/graphql", _GQL_Q2),
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
            "Q1": ("http://localhost:8816/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8816/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8816/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8816/graphql", _GQL_Q3),
        },
        "health_url": "http://localhost:8816/health",
        # LRU cache needs 30s warmup to fill before measuring cache-hit throughput.
        "warmup_secs": 30,
    },
    "fraiseql-tv-nocache": {
        "compose_service": "fraiseql-tv-nocache",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:8817/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8817/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8817/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8817/graphql", _GQL_Q3),
        },
        "health_url": "http://localhost:8817/health",
    },
    "fraiseql-v": {
        "compose_service": "fraiseql",
        "type": "graphql",
        "queries": {
            "Q1": ("http://localhost:8815/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8815/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8815/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8815/graphql", _GQL_Q3),
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


_MAX_ERROR_SAMPLES = 3


@dataclass
class BenchResult:
    framework: str
    query_name: str
    duration_secs: int
    concurrency: int
    latencies_ms: list[float] = field(default_factory=list)
    errors: int = 0
    error_breakdown: dict[str, int] = field(default_factory=dict)
    error_samples: list[tuple[str, str]] = field(
        default_factory=list
    )  # (category, detail)
    skipped: bool = False
    skip_reason: str = ""

    @property
    def requests_sent(self) -> int:
        return len(self.latencies_ms)

    @property
    def rps(self) -> float:
        return (
            self.requests_sent / self.duration_secs if self.duration_secs > 0 else 0.0
        )

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


def _post_graphql(
    url: str, query: str, timeout: int = 10
) -> tuple[bool, float, str, str]:
    """Execute one GraphQL POST. Returns (success, latency_ms, error_category, error_detail)."""
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
            raw = resp.read()
            elapsed = (time.monotonic() - t0) * 1000
            if resp.status != 200:
                return False, elapsed, "http_error", f"HTTP {resp.status}"
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                return False, elapsed, "json_error", raw[:200].decode(errors="replace")
            if body.get("errors"):
                msg = body["errors"][0].get("message", "unknown")[:200]
                return False, elapsed, "graphql_error", msg
            if "data" not in body:
                return False, elapsed, "missing_data", str(body)[:200]
            return True, elapsed, "", ""
    except urllib.error.URLError as exc:
        elapsed = (time.monotonic() - t0) * 1000
        if isinstance(exc.reason, ConnectionRefusedError):
            return False, elapsed, "connection_refused", str(exc.reason)
        if "timed out" in str(exc.reason):
            return False, elapsed, "timeout", str(exc.reason)
        return False, elapsed, "connection_error", str(exc.reason)[:200]
    except OSError as exc:
        return False, (time.monotonic() - t0) * 1000, "connection_error", str(exc)[:200]


def _get_rest(url: str, timeout: int = 10) -> tuple[bool, float, str, str]:
    """Execute one REST GET. Returns (success, latency_ms, error_category, error_detail)."""
    req = urllib.request.Request(url, method="GET")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            elapsed = (time.monotonic() - t0) * 1000
            if resp.status != 200:
                return False, elapsed, "http_error", f"HTTP {resp.status}"
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                return False, elapsed, "json_error", raw[:200].decode(errors="replace")
            if not isinstance(body, (dict, list)):
                return (
                    False,
                    elapsed,
                    "missing_data",
                    f"unexpected type: {type(body).__name__}",
                )
            return True, elapsed, "", ""
    except urllib.error.URLError as exc:
        elapsed = (time.monotonic() - t0) * 1000
        if isinstance(exc.reason, ConnectionRefusedError):
            return False, elapsed, "connection_refused", str(exc.reason)
        if "timed out" in str(exc.reason):
            return False, elapsed, "timeout", str(exc.reason)
        return False, elapsed, "connection_error", str(exc.reason)[:200]
    except OSError as exc:
        return False, (time.monotonic() - t0) * 1000, "connection_error", str(exc)[:200]


_WorkerResult = tuple[list[float], int, dict[str, int], list[tuple[str, str]]]


def _worker_graphql(url: str, query: str, end_time: float) -> _WorkerResult:
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    while time.monotonic() < end_time:
        ok, lat, cat, detail = _post_graphql(url, query)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, detail))
    return latencies, errors, breakdown, samples


def _worker_rest(url: str, end_time: float) -> _WorkerResult:
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    while time.monotonic() < end_time:
        ok, lat, cat, detail = _get_rest(url)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, detail))
    return latencies, errors, breakdown, samples


# ---------------------------------------------------------------------------
# M1 mutation: discover a user UUID at runtime
# ---------------------------------------------------------------------------


def _discover_user_uuid(fw_config: dict) -> str | None:
    """Fetch Q1 and extract the first user's id for mutation testing."""
    q1_entry = fw_config["queries"].get("Q1")
    if q1_entry is None:
        return None
    fw_type = fw_config["type"]
    try:
        if fw_type == "graphql":
            url, query = q1_entry
            payload = json.dumps({"query": query}).encode()
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read())
                users = body.get("data", {}).get("users", [])
                if users:
                    return str(users[0]["id"])
        else:
            url = q1_entry
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read())
                users = (
                    body
                    if isinstance(body, list)
                    else body.get("content", body.get("data", []))
                )
                if users and isinstance(users, list):
                    return str(users[0].get("id", users[0].get("pk_user", "")))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, IndexError):
        pass
    return None


def _worker_mutation_graphql(url: str, query: str, end_time: float) -> _WorkerResult:
    """Worker for GraphQL mutations — identical to _worker_graphql."""
    return _worker_graphql(url, query, end_time)


def _worker_mutation_rest(url: str, payload: bytes, end_time: float) -> _WorkerResult:
    """Worker for REST PUT mutations."""
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    while time.monotonic() < end_time:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
                elapsed = (time.monotonic() - t0) * 1000
                if resp.status in (200, 204):
                    latencies.append(elapsed)
                else:
                    errors += 1
                    cat = "http_error"
                    breakdown[cat] = breakdown.get(cat, 0) + 1
                    if len(samples) < _MAX_ERROR_SAMPLES:
                        samples.append((cat, f"HTTP {resp.status}"))
        except urllib.error.URLError as exc:
            elapsed = (time.monotonic() - t0) * 1000
            cat = "connection_error"
            if isinstance(getattr(exc, "reason", None), ConnectionRefusedError):
                cat = "connection_refused"
            errors += 1
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, str(exc.reason)[:200]))
        except OSError as exc:
            errors += 1
            cat = "connection_error"
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, str(exc)[:200]))
    return latencies, errors, breakdown, samples


# ---------------------------------------------------------------------------
# Diagnostic mode
# ---------------------------------------------------------------------------


def run_diagnose(fw_name: str, fw_config: dict) -> None:
    """Send 5 requests per query at concurrency=1, printing full error details."""
    print("  DIAGNOSE: sending 5 probe requests per query...", flush=True)
    for query_name, entry in fw_config["queries"].items():
        if entry is None:
            print(f"    {query_name}: skipped (None)", flush=True)
            continue
        fw_type = fw_config["type"]
        print(f"    {query_name}:", flush=True)
        for i in range(5):
            if fw_type == "graphql":
                url, query = entry
                ok, lat, cat, detail = _post_graphql(url, query, timeout=15)
            else:
                url = entry
                ok, lat, cat, detail = _get_rest(url, timeout=15)
            status = "OK" if ok else f"FAIL [{cat}]"
            print(f"      #{i + 1}: {status}  {lat:.1f}ms", flush=True)
            if not ok and detail:
                print(f"             {detail}", file=sys.stderr, flush=True)


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

    def _run_workers(
        secs: int,
    ) -> tuple[list[float], int, dict[str, int], list[tuple[str, str]]]:
        end_time = time.monotonic() + secs
        all_lats: list[float] = []
        all_errs = 0
        all_breakdown: dict[str, int] = {}
        all_samples: list[tuple[str, str]] = []
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            if fw_type == "graphql":
                url, query = entry
                futures = [
                    pool.submit(_worker_graphql, url, query, end_time)
                    for _ in range(concurrency)
                ]
            elif query_name == "M1":
                url = entry
                payload = json.dumps({"bio": "bench"}).encode()
                futures = [
                    pool.submit(_worker_mutation_rest, url, payload, end_time)
                    for _ in range(concurrency)
                ]
            else:
                url = entry
                futures = [
                    pool.submit(_worker_rest, url, end_time) for _ in range(concurrency)
                ]
            for fut in as_completed(futures):
                lats, errs, breakdown, samples = fut.result()
                all_lats.extend(lats)
                all_errs += errs
                for cat, count in breakdown.items():
                    all_breakdown[cat] = all_breakdown.get(cat, 0) + count
                if len(all_samples) < _MAX_ERROR_SAMPLES:
                    all_samples.extend(samples[: _MAX_ERROR_SAMPLES - len(all_samples)])
        return all_lats, all_errs, all_breakdown, all_samples

    # Warmup (discard results)
    print(f"    warmup {warmup_secs}s...", end=" ", flush=True)
    _run_workers(warmup_secs)
    print("done", flush=True)

    # Measurement
    print(f"    measuring {duration_secs}s...", end=" ", flush=True)
    lats, errs, breakdown, samples = _run_workers(duration_secs)
    result.latencies_ms = lats
    result.errors = errs
    result.error_breakdown = breakdown
    result.error_samples = samples

    err_summary = ""
    if breakdown:
        parts = [
            f"{cat}: {cnt}"
            for cat, cnt in sorted(breakdown.items(), key=lambda x: -x[1])
        ]
        err_summary = f"  [{', '.join(parts)}]"
    print(
        f"{result.rps:.0f} RPS  "
        f"p50={result.p50_ms:.1f}ms  "
        f"p95={result.p95_ms:.1f}ms  "
        f"p99={result.p99_ms:.1f}ms  "
        f"errors={result.errors}{err_summary}",
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


def start_service_or_skip(
    service: str, health_url: str, timeout_secs: int = 60
) -> bool:
    """Like start_service but returns False instead of raising on timeout."""
    try:
        start_service(service, health_url, timeout_secs)
        return True
    except RuntimeError as exc:
        print(f"  WARN: {exc} — skipping", flush=True)
        _compose("stop", service, check=False)
        return False


def stop_service(service: str) -> None:
    print(f"  stopping {service}...", end=" ", flush=True)
    _compose("stop", service)
    print("stopped", flush=True)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def _row(r: BenchResult, detailed_errors: bool = False) -> str:
    if r.skipped:
        return f"| {r.framework} | {r.query_name} | — | — | — | — | — | _{r.skip_reason}_ |"
    err_col = f"{r.error_rate_pct:.1f}%"
    if detailed_errors and r.error_breakdown:
        parts = []
        total_errs = sum(r.error_breakdown.values()) or 1
        for cat, cnt in sorted(r.error_breakdown.items(), key=lambda x: -x[1]):
            pct = cnt / total_errs * 100
            parts.append(f"{cat}: {pct:.0f}%")
        err_col += f" ({', '.join(parts)})"
    return (
        f"| {r.framework} | {r.query_name} "
        f"| {r.rps:.0f} "
        f"| {r.p50_ms:.1f} "
        f"| {r.p95_ms:.1f} "
        f"| {r.p99_ms:.1f} "
        f"| {r.requests_sent:,} "
        f"| {err_col} |"
    )


_QUERY_LABELS = {
    "Q1": "`users(limit: 20) { id username fullName }`",
    "Q2": "`posts(limit: 10) { id title }`",
    "Q2b": "`posts(limit: 10) { id title author { username fullName } }`",
    "Q3": "`comments(limit: 20) { id content author { username } post { title } }`",
    "M1": "`mutation { updateUser(...) { id bio } }`",
}


def format_report(
    results: list[BenchResult],
    args: argparse.Namespace,
    date_str: str,
) -> str:
    detailed = getattr(args, "detailed_errors", False)

    lines: list[str] = [
        "# VelocityBench — Sequential Isolation Benchmark Results",
        "",
        f"**Date**: {date_str}  ",
        "**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  ",
        "**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  ",
        f"**Concurrency**: {args.concurrency} workers  ",
        f"**Measurement**: {args.duration}s per scenario  ",
        f"**Warmup**: {args.warmup}s per scenario  ",
        f"**Cooldown**: {args.cooldown}s between frameworks  ",
        "",
        "---",
    ]

    # Emit a section for each query type that has results
    seen_queries = []
    for r in results:
        if r.query_name not in seen_queries:
            seen_queries.append(r.query_name)

    for qname in seen_queries:
        label = _QUERY_LABELS.get(qname, qname)
        lines += [
            "",
            f"## {qname} — {label}",
            "",
            "| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |",
            "|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|",
        ]
        for r in results:
            if r.query_name == qname:
                lines.append(_row(r, detailed_errors=detailed))

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
        "--duration",
        type=int,
        default=20,
        help="Measurement seconds per scenario (default: 20)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=40,
        help="Concurrent workers (default: 40)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Warmup seconds per scenario (default: 5)",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=5,
        help="Cooldown seconds between frameworks (default: 5)",
    )
    parser.add_argument(
        "--no-isolation",
        action="store_true",
        help="Skip docker start/stop — assume all services already running",
    )
    parser.add_argument(
        "--skip-unhealthy",
        action="store_true",
        help="Skip frameworks that fail to become healthy instead of aborting",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Report output path (default: reports/bench-sequential-YYYY-MM-DD.md)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log error samples to stderr for failing frameworks",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Run 5 slow requests per query at concurrency=1 before benchmarking, printing full error details",
    )
    parser.add_argument(
        "--detailed-errors",
        action="store_true",
        help="Show error category breakdown in the Markdown report",
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
    print(
        f"Isolation   : {'disabled (--no-isolation)' if args.no_isolation else 'enabled'}"
    )
    print()

    all_results: list[BenchResult] = []

    for i, fw_name in enumerate(args.frameworks):
        fw_config = FRAMEWORKS[fw_name]
        print(f"[{i + 1}/{len(args.frameworks)}] {fw_name}")

        query_names = list(fw_config["queries"])

        if not args.no_isolation:
            healthy = (
                start_service_or_skip(
                    fw_config["compose_service"], fw_config["health_url"]
                )
                if args.skip_unhealthy
                else (
                    start_service(fw_config["compose_service"], fw_config["health_url"])
                    or True
                )
            )
            if not healthy:
                for query_name in query_names:
                    r = BenchResult(
                        framework=fw_name,
                        query_name=query_name,
                        duration_secs=args.duration,
                        concurrency=args.concurrency,
                        skipped=True,
                        skip_reason="service did not become healthy",
                    )
                    all_results.append(r)
                continue
        else:
            healthy = True

        if args.diagnose:
            run_diagnose(fw_name, fw_config)

        # Resolve M1 mutation queries at runtime (need a real user UUID)
        if "M1" in fw_config["queries"] and fw_config["queries"]["M1"] == "M1":
            user_id = _discover_user_uuid(fw_config)
            if user_id:
                if fw_config["type"] == "graphql":
                    q1_url = fw_config["queries"]["Q1"][0]  # reuse GraphQL endpoint
                    mutation = _GQL_M1_TMPL.format(user_id=user_id)
                    fw_config["queries"]["M1"] = (q1_url, mutation)
                else:
                    # REST: derive mutation URL from Q1 URL base
                    q1_url = fw_config["queries"]["Q1"]
                    base = q1_url.rsplit("/users", 1)[0]
                    fw_config["queries"]["M1"] = f"{base}/users/{user_id}"
                print(f"  M1: resolved user UUID {user_id[:8]}...", flush=True)
            else:
                fw_config["queries"]["M1"] = None  # skip if UUID discovery fails
                print("  M1: could not discover user UUID — skipping", flush=True)

        for query_name in query_names:
            print(f"  {query_name}:")
            r = run_scenario(
                fw_name,
                fw_config,
                query_name,
                args.concurrency,
                args.duration,
                args.warmup,
            )
            all_results.append(r)
            if args.verbose and r.error_samples:
                print("    error samples:", file=sys.stderr, flush=True)
                for cat, detail in r.error_samples:
                    print(f"      [{cat}] {detail}", file=sys.stderr, flush=True)

        if not args.no_isolation:
            stop_service(fw_config["compose_service"])

        if i < len(args.frameworks) - 1:
            print(f"  cooldown {args.cooldown}s...", flush=True)
            time.sleep(args.cooldown)
        print()

    report = format_report(all_results, args, date_str)

    output_path = (
        Path(args.output)
        if args.output
        else REPORTS_DIR / f"bench-sequential-{date_str}.md"
    )
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
            "error_breakdown": r.error_breakdown,
            "skipped": r.skipped,
            "skip_reason": r.skip_reason,
        }
        for r in all_results
    ]
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"JSON data written to: {json_path}")


if __name__ == "__main__":
    main()
