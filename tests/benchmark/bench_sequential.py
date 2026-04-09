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
    python tests/benchmark/bench_sequential.py --frameworks fraiseql-tv fraiseql-v-nocache fraiseql-v-cache
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
    F1   — posts(published:true, limit:10) { id title }      published filter, no nesting
    F2   — posts(published:true, limit:10) { id title author { ... } }  published filter + nest
"""

import argparse
import hashlib
import http.client
import json
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Framework registry
# ---------------------------------------------------------------------------

# Each entry: compose_service (docker-compose service name), type (graphql|rest),
# and per-query (url, payload) pairs. None means the query is skipped for this
# framework (known bug or N/A).

_GQL_Q1 = "{ users(limit: 20) { id username fullName } }"
_GQL_Q2 = "{ posts(limit: 10) { id title } }"
_GQL_Q2b = "{ posts(limit: 10) { id title author { username fullName } } }"

# PostGraphile uses Relay-style schema with different field names
_PG_Q1 = "{ allTbUsers(first: 20) { nodes { id username fullName } } }"
_PG_Q2 = "{ allTbPosts(first: 10) { nodes { id title } } }"
_PG_Q2b = "{ allTbPosts(first: 10) { nodes { id title tbUserByFkAuthor { username fullName } } } }"
_GQL_Q3 = "{ comments(limit: 20) { id content author { username } post { title } } }"
_GQL_M1_TMPL = (
    'mutation {{ updateUser(id: "{user_id}", input: {{ bio: "bench" }}) {{ id bio }} }}'
)

# Flat-args mutation template — no input wrapper. Most GraphQL frameworks (gqlgen, graphene,
# strawberry, apollo, yoga, mercurius, go-graphql-go, graphql-go) use flat args directly.
_GQL_M1_FLAT_TMPL = (
    'mutation {{ updateUser(id: "{user_id}", bio: "bench") {{ id bio }} }}'
)

# FraiseQL-specific templates — flat args (no input wrapper), schema compiled differently.
# FraiseQL reads mutation arguments exclusively from the GraphQL `variables` map, not from
# inline literals. M1 is therefore stored as a 3-tuple (url, query, variables) and sent
# as {"query": ..., "variables": {...}} — see _worker_graphql_with_vars below.
_FRAISEQL_M1_QUERY = (
    "mutation UpdateUser($id: ID!, $bio: String) { updateUser(id: $id, bio: $bio)"
    " { id identifier email username fullName bio createdAt updatedAt } }"
)
_FRAISEQL_M1D_QUERY = (
    "mutation UpdateUserDelta($id: ID!, $bio: String) { updateUserDelta(id: $id, bio: $bio)"
    " { id identifier email username fullName bio createdAt updatedAt } }"
)

# ---------------------------------------------------------------------------
# APQ (Automatic Persisted Queries) — pre-computed SHA-256 hashes.
# Registered with the server once during sentinel resolution; measurement
# phase sends hash-only payloads (no query string), eliminating parse overhead.
# ---------------------------------------------------------------------------

def _apq_hash(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()


def _apq_payload_static(sha256: str) -> bytes:
    """Hash-only APQ payload for queries without variables."""
    return json.dumps(
        {"extensions": {"persistedQuery": {"version": 1, "sha256Hash": sha256}}}
    ).encode()


def _apq_payload_with_vars(sha256: str, variables: dict) -> bytes:
    """Hash + variables APQ payload (no query string)."""
    return json.dumps(
        {"variables": variables, "extensions": {"persistedQuery": {"version": 1, "sha256Hash": sha256}}}
    ).encode()


def _apq_register(url: str, query: str, sha256: str) -> bool:
    """Register a query with the server via APQ protocol.

    Sends query + hash once. Returns True if the server accepted it
    (HTTP 200 with data, no PersistedQueryNotFound error). Returns False
    if the server doesn't support APQ or the registration failed.
    """
    payload = json.dumps(
        {"query": query, "extensions": {"persistedQuery": {"version": 1, "sha256Hash": sha256}}}
    ).encode()
    try:
        conn = _PersistentConn(url)
        ok, _, cat, detail = conn.post_graphql(payload)
        if not ok and "PersistedQueryNotFound" in detail:
            # Server requires re-send with query (shouldn't happen on first registration)
            ok, _, _, _ = conn.post_graphql(payload)
        return ok
    except Exception:
        return False
_FRAISEQL_C3_TMPL = '{{ user(id: "{user_id}") {{ id username fullName }} }}'
_FRAISEQL_C3_QUERY = "query GetUser($id: ID!) { user(id: $id) { id username fullName } }"

# Phase 3: Filtered query constants (FraiseQL WHERE / ORDER BY pushdown)
_FRAISEQL_F1 = "{ posts(published: true, limit: 10) { id title } }"
_FRAISEQL_F2 = "{ posts(published: true, limit: 10) { id title author { username fullName } } }"
_FRAISEQL_F3 = "{ users(limit: 20) { id username fullName } }"  # baseline; extend with orderBy once syntax confirmed

# Cross-framework filtered query constants (published=true filter, comparable to FraiseQL F1/F2)
_GQL_F1 = _FRAISEQL_F1  # same query works for all standard GraphQL frameworks
_GQL_F2 = _FRAISEQL_F2  # same query works for all standard GraphQL frameworks

# T1 "Total Scenario" — full blog page load (post + author + 10 comments with authors)
# GraphQL: single nested query.  REST: 3 sequential HTTP calls.
_GQL_T1_TMPL = (
    '{{ post(id: "{post_id}") {{ id title content '
    "author {{ username fullName bio }} "
    "comments(limit: 10) {{ id content author {{ username }} }} "
    "}} }}"
)
# PostGraphile Relay-style T1
_PG_T1_TMPL = (
    '{{ tbPostById(id: "{post_id}") {{ id title content '
    "tbUserByFkAuthor {{ username fullName }} "
    "tbCommentsByFkPost(first: 10) {{ nodes {{ id content tbUserByFkAuthor {{ username }} }} }} "
    "}} }}"
)
# FraiseQL T1: 2 sequential GraphQL calls (legacy — post doesn't nest comments in tview)
_FRAISEQL_T1_POST_TMPL = (
    '{{ post(id: "{post_id}") {{ id title content author {{ username fullName bio }} }} }}'
)
_FRAISEQL_T1_COMMENTS = (
    "{ comments(limit: 10) { id content author { username } post { title } } }"
)
# FraiseQL T1 single-query — uses postFull(id) which resolves via v_post_full composed view
# Single SQL: jsonb_set injects jsonb_agg(tv_comment) into tv_post.data in one query
_FRAISEQL_T1_SINGLE_QUERY = (
    "query GetPostFull($id: ID!) { postFull(id: $id) { id title content "
    "author { id username fullName } "
    "comments { id content author { id username fullName } } } }"
)
# FraiseQL T1 multi-root — parallel SQL execution via fraiseql v2 pipeline
# Fires post(id) + comments(post_id, limit:10) as two concurrent SQL queries
# against tv_post and tv_comment (both indexed). No jsonb_agg, no v_post_full
# composed view overhead. ~26% faster than postFull in benchmarks.
_FRAISEQL_T1_MULTI_ROOT = (
    "query GetPostAndComments($id: ID!) { "
    "post(id: $id) { id title content author { id username fullName } } "
    "comments(post_id: $id, limit: 10) { id content author { id username fullName } } "
    "}"
)

FRAMEWORKS: dict[str, dict] = {
    # ------------------------------------------------------------------
    # Rust frameworks
    # ------------------------------------------------------------------
    "actix-web-rest": {
        "compose_service": "actix-web-rest",
        "type": "rest",
        "language": "Rust",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8015/users?limit=20",
            "Q2": "http://localhost:8015/posts?limit=10",
            "Q2b": "http://localhost:8015/posts?limit=10&include=author",  # includes author JOIN
            "M1": "M1",
            "F1": "http://localhost:8015/posts?published=true&limit=10",
            "F2": "http://localhost:8015/posts?published=true&limit=10&include=author",
            "T1": "T1",  # no /posts/{id}/comments endpoint — skipped at runtime if missing
        },
        "health_url": "http://localhost:8015/health",
    },
    "async-graphql": {
        "compose_service": "async-graphql",
        "type": "graphql",
        "language": "Rust",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:8016/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8016/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8016/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8016/graphql", _GQL_Q3),
            "M1": "M1",
            "F1": ("http://localhost:8016/graphql", _GQL_F1),
            "F2": ("http://localhost:8016/graphql", _GQL_F2),
            "T1": "T1",
            "MC1": "MC1",
            "Q1_APQ": "Q1_APQ",
            "Q2b_APQ": "Q2b_APQ",
        },
        "health_url": "http://localhost:8016/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "juniper": {
        "compose_service": "juniper",
        "type": "graphql",
        "language": "Rust",
        "category": "graphql",
        "start_timeout": 600,
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:4000/graphql", _GQL_Q3),
            "M1": "M1",
            "F1": ("http://localhost:4000/graphql", _GQL_F1),
            "F2": ("http://localhost:4000/graphql", _GQL_F2),
            "T1": "T1",
        },
        # Juniper wraps mutation args in input object: updateUser(id, input: {bio})
        "m1_template": 'mutation {{ updateUser(id: "{user_id}", input: {{ bio: "bench" }}) {{ id username fullName bio }} }}',
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Go frameworks
    # ------------------------------------------------------------------
    "go-gqlgen": {
        "compose_service": "go-gqlgen",
        "type": "graphql",
        "language": "Go",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4010/query", _GQL_Q1),
            "Q2": ("http://localhost:4010/query", _GQL_Q2),
            "Q2b": ("http://localhost:4010/query", _GQL_Q2b),
            "Q3": None,  # Q3: comments query not implemented
            "M1": "M1",
            "F1": ("http://localhost:4010/query", _GQL_F1),
            "F2": ("http://localhost:4010/query", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:4010/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "gin-rest": {
        "compose_service": "gin-rest",
        "type": "rest",
        "language": "Go",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8006/users?limit=20",
            "Q2": "http://localhost:8006/posts?limit=10",
            "Q2b": "http://localhost:8006/posts?limit=10&include=author",
            "M1": "M1",
            "F1": "http://localhost:8006/posts?published=true&limit=10",
            "F2": "http://localhost:8006/posts?published=true&limit=10&include=author",
            "T1": "T1",
        },
        "health_url": "http://localhost:8006/health",
    },
    "go-graphql-go": {
        "compose_service": "go-graphql-go",
        "type": "graphql",
        "language": "Go",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:8008/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8008/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8008/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:8008/graphql", _GQL_F1),
            "F2": ("http://localhost:8008/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:8008/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "graphql-go": {
        "compose_service": "graphql-go",
        "type": "graphql",
        "language": "Go",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4011/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4011/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4011/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:4011/graphql", _GQL_F1),
            "F2": ("http://localhost:4011/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:4011/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    # ------------------------------------------------------------------
    # Node.js frameworks
    # ------------------------------------------------------------------
    "apollo-server": {
        "compose_service": "apollo",
        "type": "graphql",
        "language": "Node.js",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4002/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4002/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4002/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:4002/graphql", _GQL_F1),
            "F2": ("http://localhost:4002/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:4002/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "apollo-orm": {
        "compose_service": "apollo-orm",
        "type": "graphql",
        "language": "Node.js",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4004/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4004/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4004/graphql", _GQL_Q2b),
            "F1": ("http://localhost:4004/graphql", _GQL_F1),
            "F2": ("http://localhost:4004/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:4004/health",
    },
    "express-rest": {
        "compose_service": "express-rest",
        "type": "rest",
        "language": "Node.js",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8005/users?limit=20",
            "Q2": "http://localhost:8005/posts?limit=10",
            "Q2b": "http://localhost:8005/posts?limit=10&include=author",
            "F1": "http://localhost:8005/posts?published=true&limit=10",
            "F2": "http://localhost:8005/posts?published=true&limit=10&include=author",
            "T1": "T1",
        },
        "health_url": "http://localhost:8005/health",
    },
    "express-orm": {
        "compose_service": "express-orm",
        "type": "rest",
        "language": "Node.js",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8007/users?limit=20",
            "Q2": "http://localhost:8007/posts?limit=10",
            "Q2b": "http://localhost:8007/posts?limit=10&include=author",
            "F1": "http://localhost:8007/posts?published=true&limit=10",
            "F2": "http://localhost:8007/posts?published=true&limit=10&include=author",
            "T1": "T1",
        },
        "health_url": "http://localhost:8007/health",
    },
    "express-graphql": {
        "compose_service": "express-graphql",
        "type": "graphql",
        "language": "Node.js",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4011/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4011/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4011/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:4011/graphql", _GQL_F1),
            "F2": ("http://localhost:4011/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:4011/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "graphql-yoga": {
        "compose_service": "graphql-yoga",
        "type": "graphql",
        "language": "Node.js",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4012/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4012/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4012/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:4012/graphql", _GQL_F1),
            "F2": ("http://localhost:4012/graphql", _GQL_F2),
            "T1": "T1",
            "MC1": "MC1",
            "Q1_APQ": "Q1_APQ",
            "Q2b_APQ": "Q2b_APQ",
        },
        "health_url": "http://localhost:4012/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "mercurius": {
        "compose_service": "mercurius",
        "type": "graphql",
        "language": "Node.js",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4008/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4008/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4008/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:4008/graphql", _GQL_F1),
            "F2": ("http://localhost:4008/graphql", _GQL_F2),
            "T1": "T1",
            "MC1": "MC1",
            "Q1_APQ": "Q1_APQ",
            "Q2b_APQ": "Q2b_APQ",
        },
        "health_url": "http://localhost:4008/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    # ------------------------------------------------------------------
    # Python frameworks
    # ------------------------------------------------------------------
    "strawberry": {
        "compose_service": "strawberry",
        "type": "graphql",
        "language": "Python",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:8011/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8011/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8011/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:8011/graphql", _GQL_F1),
            "F2": ("http://localhost:8011/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:8011/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "graphene": {
        "compose_service": "graphene",
        "type": "graphql",
        "language": "Python",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:8002/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8002/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8002/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:8002/graphql", _GQL_F1),
            "F2": ("http://localhost:8002/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:8002/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    "fastapi-rest": {
        "compose_service": "fastapi-rest",
        "type": "rest",
        "language": "Python",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8003/users?limit=20",
            "Q2": "http://localhost:8003/posts?limit=10",
            "Q2b": "http://localhost:8003/posts?limit=10&include=author",
            "M1": "M1",
            "F1": "http://localhost:8003/posts?published=true&limit=10",
            "F2": "http://localhost:8003/posts?published=true&limit=10&include=author",
            "T1": "T1",
        },
        "health_url": "http://localhost:8003/health",
    },
    "flask-rest": {
        "compose_service": "flask-rest",
        "type": "rest",
        "language": "Python",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8004/users?limit=20",
            "Q2": "http://localhost:8004/posts?limit=10",
            "Q2b": "http://localhost:8004/posts?limit=10&include=author",
            "F1": "http://localhost:8004/posts?limit=10&published=true",
            "F2": "http://localhost:8004/posts?limit=10&published=true&include=author",
            "T1": "T1",
        },
        "health_url": "http://localhost:8004/health",
    },
    "ariadne": {
        "compose_service": "ariadne",
        "type": "graphql",
        "language": "Python",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "F1": ("http://localhost:4000/graphql", _GQL_F1),
            "F2": ("http://localhost:4000/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:4000/health",
    },
    "asgi-graphql": {
        "compose_service": "asgi-graphql",
        "type": "graphql",
        "language": "Python",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "F1": ("http://localhost:4000/graphql", _GQL_F1),
            "F2": ("http://localhost:4000/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Java / JVM frameworks
    # ------------------------------------------------------------------
    "spring-boot": {
        "compose_service": "spring-boot",
        "type": "rest",
        "language": "Java",
        "category": "rest",
        "start_timeout": 120,
        "queries": {
            # Spring Boot uses page/size pagination, not limit
            "Q1": "http://localhost:8010/api/users?page=0&size=20",
            "Q2": "http://localhost:8010/api/posts?page=0&size=10",
            "Q2b": "http://localhost:8010/api/posts/with-author?page=0&size=10",
            # Q2/Q2b already hardcode published=true (JPA derived method), so F1 == Q2, F2 == Q2b
            "F1": "http://localhost:8010/api/posts?page=0&size=10",
            "F2": "http://localhost:8010/api/posts/with-author?page=0&size=10",
            "M1": "M1",
            "T1": "T1",  # no /posts/{id}/comments — multi-call will skip if endpoint missing
        },
        "health_url": "http://localhost:8010/actuator/health",
    },
    "spring-boot-orm": {
        "compose_service": "spring-boot-orm",
        "type": "rest",
        "language": "Java",
        "category": "rest",
        "start_timeout": 120,
        "queries": {
            "Q1": "http://localhost:8013/api/users?page=0&size=20",
            "Q2": "http://localhost:8013/api/posts?size=10",
            "Q2b": None,  # Q2b: nested author queries - multiple calls approach causes connection issues
            "M1": "M1",
            # Q2 already hardcodes published=true (JPQL WHERE p.published = true), so F1 == Q2
            "F1": "http://localhost:8013/api/posts?size=10",
            "F2": None,
            "T1": "T1",
        },
        "health_url": "http://localhost:8013/actuator/health",
    },
    "spring-boot-orm-naive": {
        "compose_service": "spring-boot-orm-naive",
        "type": "rest",
        "language": "Java",
        "category": "rest",
        "start_timeout": 120,
        "queries": {
            "Q1": "http://localhost:8014/api/users?page=0&size=20",
            "Q2": "http://localhost:8014/api/posts?size=10",
            "T1": "T1",
        },
        "health_url": "http://localhost:8014/health",
    },
    "micronaut-graphql": {
        "compose_service": "micronaut-graphql",
        "type": "graphql",
        "language": "Java",
        "category": "graphql",
        "start_timeout": 120,
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "M1": "M1",
            "T1": "T1",
        },
        "health_url": "http://localhost:4000/health",
        # Micronaut wraps mutation args in input object: updateUser(id, input: {bio})
        "m1_template": 'mutation {{ updateUser(id: "{user_id}", input: {{ bio: "bench" }}) {{ id username fullName bio createdAt }} }}',
    },
    "quarkus-graphql": {
        "compose_service": "quarkus-graphql",
        "type": "graphql",
        "language": "Java",
        "category": "graphql",
        "start_timeout": 120,
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:4000/graphql", _GQL_Q3),
            "M1": "M1",
            "T1": "T1",
        },
        "health_url": "http://localhost:4000/health",
        # Quarkus wraps mutation args in input object: updateUser(id, input: {bio})
        "m1_template": 'mutation {{ updateUser(id: "{user_id}", input: {{ bio: "bench" }}) {{ id username fullName bio createdAt updatedAt }} }}',
    },
    # ------------------------------------------------------------------
    # Scala frameworks
    # ------------------------------------------------------------------
    "play-graphql": {
        "compose_service": "play-graphql",
        "type": "graphql",
        "language": "Scala",
        "category": "graphql",
        "start_timeout": 120,
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "M1": "M1",
            "T1": "T1",
        },
        "health_url": "http://localhost:4000/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    # ------------------------------------------------------------------
    # Ruby frameworks
    # ------------------------------------------------------------------
    "ruby-rails": {
        "compose_service": "ruby-rails",
        "type": "rest",
        "language": "Ruby",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8012/api/users?limit=20",
            "Q2": "http://localhost:8012/api/posts?limit=10",
            "Q2b": "http://localhost:8012/api/posts?with_author=true",
            "F1": "http://localhost:8012/api/posts?published=true&limit=10",
            "F2": "http://localhost:8012/api/posts?published=true&with_author=true",
            "M1": "M1",
            "T1": "T1",
        },
        "health_url": "http://localhost:8012/api/health",
    },
    "hanami": {
        "compose_service": "hanami",
        "type": "graphql",
        "language": "Ruby",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "T1": "T1",
        },
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # PHP frameworks
    # ------------------------------------------------------------------
    "php-laravel": {
        "compose_service": "php-laravel",
        "type": "rest",
        "language": "PHP",
        "category": "rest",
        "queries": {
            "Q1": "http://localhost:8009/api/users?limit=20",
            "Q2": "http://localhost:8009/api/posts?limit=10",
            "Q2b": "http://localhost:8009/api/posts?limit=10&include=author",
            "F1": "http://localhost:8009/api/posts?published=true&limit=10",
            "F2": "http://localhost:8009/api/posts?published=true&limit=10&include=author",
            "T1": "T1",
        },
        "health_url": "http://localhost:8009/api/health",
    },
    "webonyx-graphql-php": {
        "compose_service": "webonyx-graphql-php",
        "type": "graphql",
        "language": "PHP",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:4000/graphql", _GQL_Q1),
            "Q2": ("http://localhost:4000/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:4000/graphql", _GQL_Q2b),
            "F1": ("http://localhost:4000/graphql", _GQL_F1),
            "F2": ("http://localhost:4000/graphql", _GQL_F2),
            "M1": "M1",
            "T1": "T1",
        },
        # webonyx uses input object wrapper: updateUser(id, input: {bio})
        "m1_template": 'mutation {{ updateUser(id: "{user_id}", input: {{ bio: "bench" }}) {{ id username fullName bio createdAt }} }}',
        "health_url": "http://localhost:4000/health",
    },
    # ------------------------------------------------------------------
    # Node.js schema-first frameworks
    # ------------------------------------------------------------------
    "postgraphile": {
        "compose_service": "postgraphile",
        "type": "graphql",
        "language": "Node.js",
        "category": "graphql-schema-first",
        "queries": {
            "Q1": ("http://localhost:4014/graphql", _PG_Q1),
            "Q2": ("http://localhost:4014/graphql", _PG_Q2),
            "Q2b": ("http://localhost:4014/graphql", _PG_Q2b),
            "T1": "T1",
        },
        "health_url": "http://localhost:4014/health",
        "t1_template": "postgraphile",
    },
    # ------------------------------------------------------------------
    # C# / .NET frameworks
    # ------------------------------------------------------------------
    "csharp-dotnet": {
        "compose_service": "csharp-dotnet",
        "type": "graphql",
        "language": "C#",
        "category": "graphql",
        "queries": {
            "Q1": ("http://localhost:8025/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8025/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8025/graphql", _GQL_Q2b),
            "M1": "M1",
            "F1": ("http://localhost:8025/graphql", _GQL_F1),
            "F2": ("http://localhost:8025/graphql", _GQL_F2),
            "T1": "T1",
        },
        "health_url": "http://localhost:8025/health",
        "m1_template": _GQL_M1_FLAT_TMPL,
    },
    # ------------------------------------------------------------------
    # FraiseQL variants (last — pending upstream fixes)
    # ------------------------------------------------------------------
    # fraiseql-tv: TV tables, no cache — best TV read throughput (pre-computed JSONB baseline)
    "fraiseql-tv": {
        "compose_service": "fraiseql-tv-nocache",
        "type": "graphql",
        "language": "Rust",
        "category": "graphql-precomputed",
        "no_build": True,  # fraiseql copies local binaries; rebuild only when explicitly updating
        # Application-level code: Python schema (type + query definitions) + PL/pgSQL mutation
        # functions. Equivalent to resolvers in other frameworks. Infrastructure SQL excluded.
        "loc_extra_files": [
            "frameworks/fraiseql/schema_tv.py",
            "database/fraiseql_mutations.sql",
        ],
        "queries": {
            # Standard query suite
            "Q1": ("http://localhost:8817/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8817/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8817/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8817/graphql", _GQL_Q3),
            # C3: single-entity lookup — rotating UUIDs, cache miss every time (no cache)
            "C3": "C3",
            # HC3: hot-key lookup — 5 fixed UUIDs, measures sustained throughput without cache
            "HC3": "HC3",
            # Mutation benchmark
            "M1": "M1",
            # Delta mutation benchmark (jsonb_delta surgical patch on tvd_*)
            "M1d": "M1d",
            # Filtered query benchmarks
            "F1": ("http://localhost:8817/graphql", _FRAISEQL_F1),
            "F2": ("http://localhost:8817/graphql", _FRAISEQL_F2),
            "F3": ("http://localhost:8817/graphql", _FRAISEQL_F3),
            "T1": "T1",
            # MC1: mutation-to-consistent-state cycle (cascade: 1 request replaces M1+Q1+C3)
            "MC1": "MC1",
            "Q1_APQ": "Q1_APQ",
            "Q2b_APQ": "Q2b_APQ",
            "M1_APQ": "M1_APQ",
        },
        "health_url": "http://localhost:8817/health",
        "warmup_secs": 30,
        "m1_template": "fraiseql",
        "t1_template": "fraiseql_multi_root",
        "c3_template": _FRAISEQL_C3_TMPL,
    },
    # fraiseql-tv-cache: TV tables, cache enabled — post-cascade fragmentation M1 condition
    "fraiseql-tv-cache": {
        "compose_service": "fraiseql-tv",
        "type": "graphql",
        "language": "Rust",
        "category": "graphql-precomputed",
        "no_build": True,
        "loc_extra_files": [
            "frameworks/fraiseql/schema_tv.py",
            "database/fraiseql_mutations.sql",
        ],
        "queries": {
            "Q1": ("http://localhost:8816/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8816/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8816/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8816/graphql", _GQL_Q3),
            "C3": "C3",
            "HC3": "HC3",
            "M1": "M1",
            "F1": ("http://localhost:8816/graphql", _FRAISEQL_F1),
            "F2": ("http://localhost:8816/graphql", _FRAISEQL_F2),
            "F3": ("http://localhost:8816/graphql", _FRAISEQL_F3),
            "T1": "T1",
            "MC1": "MC1",
            "Q1_APQ": "Q1_APQ",
            "Q2b_APQ": "Q2b_APQ",
            "M1_APQ": "M1_APQ",
        },
        "health_url": "http://localhost:8816/health",
        "warmup_secs": 30,
        "m1_template": "fraiseql",
        "t1_template": "fraiseql_multi_root",
        "c3_template": _FRAISEQL_C3_TMPL,
    },
    # fraiseql-v-nocache: v_* on-the-fly JSONB views, cache disabled — raw JOIN cost baseline
    "fraiseql-v-nocache": {
        "compose_service": "fraiseql-v-nocache",
        "type": "graphql",
        "language": "Rust",
        "category": "graphql-precomputed",
        "no_build": True,
        # V variant: schema + SQL view definitions (the views ARE the resolvers) + mutations
        "loc_extra_files": [
            "frameworks/fraiseql/schema.py",
            "frameworks/fraiseql/database/extensions.sql",
            "database/fraiseql_mutations.sql",
        ],
        "queries": {
            "Q1": ("http://localhost:8819/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8819/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8819/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8819/graphql", _GQL_Q3),
            "C3": "C3",
            "HC3": "HC3",
            "M1": "M1",
            "F1": ("http://localhost:8819/graphql", _FRAISEQL_F1),
            "F2": ("http://localhost:8819/graphql", _FRAISEQL_F2),
            "F3": ("http://localhost:8819/graphql", _FRAISEQL_F3),
            "T1": "T1",
            "MC1": "MC1",
            "Q1_APQ": "Q1_APQ",
            "Q2b_APQ": "Q2b_APQ",
            "M1_APQ": "M1_APQ",
        },
        "health_url": "http://localhost:8819/health",
        "warmup_secs": 5,
        "m1_template": "fraiseql",
        "t1_template": "fraiseql_multi_root",
        "c3_template": _FRAISEQL_C3_TMPL,
    },
    # fraiseql-v-cache: v_* on-the-fly JSONB views, cache enabled — where cache earns its keep
    "fraiseql-v-cache": {
        "compose_service": "fraiseql",
        "type": "graphql",
        "language": "Rust",
        "category": "graphql-precomputed",
        "no_build": True,
        "loc_extra_files": [
            "frameworks/fraiseql/schema.py",
            "frameworks/fraiseql/database/extensions.sql",
            "database/fraiseql_mutations.sql",
        ],
        "queries": {
            "Q1": ("http://localhost:8815/graphql", _GQL_Q1),
            "Q2": ("http://localhost:8815/graphql", _GQL_Q2),
            "Q2b": ("http://localhost:8815/graphql", _GQL_Q2b),
            "Q3": ("http://localhost:8815/graphql", _GQL_Q3),
            "C3": "C3",
            "HC3": "HC3",
            "M1": "M1",
            "F1": ("http://localhost:8815/graphql", _FRAISEQL_F1),
            "F2": ("http://localhost:8815/graphql", _FRAISEQL_F2),
            "F3": ("http://localhost:8815/graphql", _FRAISEQL_F3),
            "T1": "T1",
            "MC1": "MC1",
            "Q1_APQ": "Q1_APQ",
            "Q2b_APQ": "Q2b_APQ",
            "M1_APQ": "M1_APQ",
        },
        "health_url": "http://localhost:8815/health",
        # Cache needs 30s warmup to fill before measuring sustained cache-hit throughput.
        "warmup_secs": 30,
        "m1_template": "fraiseql",
        "t1_template": "fraiseql_multi_root",
        "c3_template": _FRAISEQL_C3_TMPL,
    },
    # Phase 5: Observer overhead — fraiseql-tv with audit logging enabled
    "fraiseql-tv-audit": {
        "compose_service": "fraiseql-tv-audit",
        "type": "graphql",
        "language": "Rust",
        "category": "graphql-precomputed",
        "no_build": True,  # fraiseql copies local binaries; rebuild only when explicitly updating
        "queries": {
            "M1": "M1",
        },
        "health_url": "http://localhost:8818/health",
        # graphql_url: used for UUID discovery and M1 endpoint when Q1 is absent
        "graphql_url": "http://localhost:8818/graphql",
        "warmup_secs": 10,
        "m1_template": "fraiseql",
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
    "graphql-go",
    # Node.js
    "apollo-server",
    "apollo-orm",
    "express-rest",
    "express-orm",
    "express-graphql",
    "graphql-yoga",
    "mercurius",
    "postgraphile",
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
    "spring-boot-orm-naive",
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
    # FraiseQL variants — run order matters for M1 (HOT update pages; see methodology note).
    # TV (no cache) runs first: fresh-table M1 baseline.
    # V-nocache and V-cache run after: shows cache benefit for JOIN-based views.
    "fraiseql-tv",           # TV tables, no cache  — pre-computed JSONB baseline
    "fraiseql-v-nocache",    # v_* views, no cache  — raw JOIN cost
    "fraiseql-v-cache",      # v_* views, cache on  — where cache earns its keep
    "fraiseql-tv-cache",     # TV tables, cache on  — post-cascade fragmentation (optional)
    "fraiseql-tv-audit",     # TV tables, audit logging
]

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"

# Frameworks with known failures — targeted by --broken-only for fast iteration.
BROKEN_FRAMEWORKS = []

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
# Persistent HTTP connection (avoids TIME_WAIT exhaustion from per-request sockets)
# ---------------------------------------------------------------------------


class _PersistentConn:
    """Per-worker persistent HTTP/1.1 connection. Reconnects on failure."""

    def __init__(self, url: str, timeout: int = 10) -> None:
        parsed = urlparse(url)
        self._host = parsed.hostname or "localhost"
        self._port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._path = parsed.path + ("?" + parsed.query if parsed.query else "")
        self._timeout = timeout
        self._conn: http.client.HTTPConnection | None = None

    def _connect(self) -> None:
        if self._conn is None:
            self._conn = http.client.HTTPConnection(
                self._host, self._port, timeout=self._timeout
            )

    def _reset(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def get(self) -> tuple[bool, float, str, str]:
        for attempt in range(2):
            t0 = time.monotonic()
            try:
                self._connect()
                assert self._conn is not None
                self._conn.request("GET", self._path)
                resp = self._conn.getresponse()
                raw = resp.read()
                elapsed = (time.monotonic() - t0) * 1000
                if resp.status != 200:
                    return False, elapsed, "http_error", f"HTTP {resp.status}"
                try:
                    body = json.loads(raw)
                except json.JSONDecodeError:
                    return False, elapsed, "json_error", raw[:200].decode(errors="replace")
                if not isinstance(body, (dict, list)):
                    return False, elapsed, "missing_data", f"unexpected type: {type(body).__name__}"
                return True, elapsed, "", ""
            except (
                http.client.CannotSendRequest,
                http.client.BadStatusLine,
                ConnectionResetError,
                BrokenPipeError,
                OSError,
            ):
                self._reset()
                if attempt == 1:
                    elapsed = (time.monotonic() - t0) * 1000
                    return False, elapsed, "connection_error", "reconnect failed"
        return False, 0.0, "connection_error", "unreachable"

    def post_graphql(self, payload: bytes) -> tuple[bool, float, str, str]:
        for attempt in range(2):
            t0 = time.monotonic()
            try:
                self._connect()
                assert self._conn is not None
                self._conn.request(
                    "POST",
                    self._path,
                    body=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp = self._conn.getresponse()
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
            except (
                http.client.CannotSendRequest,
                http.client.BadStatusLine,
                ConnectionResetError,
                BrokenPipeError,
                OSError,
            ):
                self._reset()
                if attempt == 1:
                    elapsed = (time.monotonic() - t0) * 1000
                    return False, elapsed, "connection_error", "reconnect failed"
        return False, 0.0, "connection_error", "unreachable"

    def put(self, payload: bytes) -> tuple[bool, float, str, str]:
        for attempt in range(2):
            t0 = time.monotonic()
            try:
                self._connect()
                assert self._conn is not None
                self._conn.request(
                    "PUT",
                    self._path,
                    body=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp = self._conn.getresponse()
                resp.read()
                elapsed = (time.monotonic() - t0) * 1000
                if resp.status in (200, 204):
                    return True, elapsed, "", ""
                return False, elapsed, "http_error", f"HTTP {resp.status}"
            except (
                http.client.CannotSendRequest,
                http.client.BadStatusLine,
                ConnectionResetError,
                BrokenPipeError,
                OSError,
            ):
                self._reset()
                if attempt == 1:
                    elapsed = (time.monotonic() - t0) * 1000
                    return False, elapsed, "connection_error", "reconnect failed"
        return False, 0.0, "connection_error", "unreachable"


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
    conn = _PersistentConn(url)
    payload = json.dumps({"query": query}).encode()
    while time.monotonic() < end_time:
        ok, lat, cat, detail = conn.post_graphql(payload)
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
    conn = _PersistentConn(url)
    while time.monotonic() < end_time:
        ok, lat, cat, detail = conn.get()
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
    """Fetch Q1 (or graphql_url fallback) and extract the first user's id."""
    q1_entry = fw_config["queries"].get("Q1")
    fw_type = fw_config["type"]
    try:
        if fw_type == "graphql":
            # Use explicit graphql_url + Q1 query when Q1 entry is absent (e.g. fraiseql-tv-audit)
            if q1_entry is None:
                gql_url = fw_config.get("graphql_url")
                if not gql_url:
                    return None
                url, query = gql_url, _GQL_Q1
            else:
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
                    else body.get("content", body.get("data", body.get("users", [])))
                )
                if users and isinstance(users, list):
                    return str(users[0].get("id", users[0].get("pk_user", "")))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, IndexError):
        pass
    return None


def _discover_user_uuids(fw_config: dict) -> list[str]:
    """Fetch Q1 and return all user ids found (up to the Q1 limit).

    Used by mutation workers to rotate across multiple rows and avoid 40 workers
    hammering the same row, which causes artificial row-lock contention in PostgreSQL.
    """
    q1_entry = fw_config["queries"].get("Q1")
    fw_type = fw_config["type"]
    try:
        if fw_type == "graphql":
            if q1_entry is None:
                gql_url = fw_config.get("graphql_url")
                if not gql_url:
                    return []
                url, query = gql_url, _GQL_Q1
            else:
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
                return [str(u["id"]) for u in users if u.get("id")]
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, IndexError):
        pass
    return []


def _discover_post_uuid(fw_config: dict) -> tuple[str, str] | None:
    """Discover a published post UUID and its author UUID for T1 scenario.

    Returns (post_id, author_id) or None if discovery fails.
    """
    fw_type = fw_config["type"]
    try:
        if fw_type == "graphql":
            # Use Q2b entry or Q1 entry to find the GraphQL URL
            for key in ("Q2b", "Q2", "Q1"):
                entry = fw_config["queries"].get(key)
                if entry is not None and isinstance(entry, tuple):
                    gql_url = entry[0]
                    break
            else:
                gql_url = fw_config.get("graphql_url")
            if not gql_url:
                return None
            # Query a single post with author to get both IDs
            query = '{ posts(limit: 1) { id author { id } } }'
            payload = json.dumps({"query": query}).encode()
            req = urllib.request.Request(
                gql_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read())
                posts = body.get("data", {}).get("posts", [])
                if posts and posts[0].get("author"):
                    return str(posts[0]["id"]), str(posts[0]["author"]["id"])
                # Fallback: post exists but author wasn't nested — get author separately
                if posts:
                    return str(posts[0]["id"]), ""
        else:
            # REST: use Q2b URL pattern (posts with author included)
            q2b_url = fw_config["queries"].get("Q2b")
            if q2b_url and isinstance(q2b_url, str):
                # Replace limit to just get 1 post
                url = q2b_url.replace("limit=10", "limit=1").replace("size=10", "size=1")
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = json.loads(resp.read())
                    # Unwrap: raw list, or {"posts": [...]}, {"content": [...]}, {"data": [...]}
                    if isinstance(body, list):
                        posts = body
                    elif isinstance(body, dict):
                        posts = (
                            body.get("posts")
                            or body.get("content")
                            or body.get("data")
                            or []
                        )
                    else:
                        posts = []
                    if posts and isinstance(posts, list) and posts[0]:
                        post = posts[0]
                        post_id = str(post.get("id", ""))
                        # Author ID can be nested or flat
                        author = post.get("author", {})
                        author_id = str(author.get("id", "")) if isinstance(author, dict) else ""
                        if not author_id:
                            author_id = str(post.get("author_id", ""))
                        if post_id:
                            return post_id, author_id
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, IndexError):
        pass
    return None


def _build_rest_t1_urls(fw_name: str, base: str, post_id: str, author_id: str) -> list[str] | None:
    """Build the REST URL chain for T1 total scenario.

    Returns a list of URLs to call sequentially, or None if the framework
    doesn't have the required endpoints.
    """
    # Framework-specific URL patterns for individual resource endpoints
    _REST_T1_PATTERNS: dict[str, dict] = {
        # Python
        "fastapi-rest": {
            "post": "/posts/{post_id}",
            "author": "/users/{author_id}",
            "comments": "/posts/{post_id}/comments?limit=10",
        },
        "flask-rest": {
            "post": "/posts/{post_id}",
            "author": "/users/{author_id}",
            "comments": "/posts/{post_id}/comments?limit=10",
        },
        # Go
        "gin-rest": {
            "post": "/posts/{post_id}",
            "author": "/users/{author_id}",
            "comments": "/posts/{post_id}/comments?limit=10",
        },
        # Node.js
        "express-rest": {
            "post": "/posts/{post_id}",
            "author": "/users/{author_id}",
            "comments": "/posts/{post_id}/comments?limit=10",
        },
        "express-orm": {
            "post": "/posts/{post_id}",
            "author": "/users/{author_id}",
            "comments": None,  # no comments endpoint
        },
        # Rust
        "actix-web-rest": {
            "post": "/posts/{post_id}",
            "author": "/users/{author_id}",
            "comments": None,  # no comments endpoint
        },
        # Java / Spring Boot
        "spring-boot": {
            "post": "/api/posts/{post_id}",
            "author": "/api/users/{author_id}",
            "comments": None,  # no comments endpoint
        },
        "spring-boot-orm": {
            "post": "/api/posts/{post_id}",
            "author": "/api/users/{author_id}",
            "comments": None,
        },
        "spring-boot-orm-naive": {
            "post": "/api/posts/{post_id}",
            "author": "/api/users/{author_id}",
            "comments": None,
        },
        # Ruby
        "ruby-rails": {
            "post": "/api/posts/{post_id}",
            "author": "/api/users/{author_id}",
            "comments": None,  # no comments endpoint
        },
        # PHP
        "php-laravel": {
            "post": "/api/posts/{post_id}",
            "author": "/api/users/{author_id}",
            "comments": None,  # no comments endpoint
        },
    }

    patterns = _REST_T1_PATTERNS.get(fw_name)
    if not patterns:
        return None

    urls = []
    for key in ("post", "author", "comments"):
        pattern = patterns.get(key)
        if pattern is None:
            continue  # skip missing endpoints (still run post + author as 2-call chain)
        url = base + pattern.format(post_id=post_id, author_id=author_id)
        urls.append(url)

    return urls if urls else None


def _worker_graphql_with_vars(
    url: str, query: str, variables: dict | list[dict], end_time: float
) -> _WorkerResult:
    """Worker for GraphQL requests that require a variables map (e.g. FraiseQL mutations).

    When `variables` is a list, a random entry is chosen per request to distribute
    mutations across multiple rows and avoid row-lock contention under high concurrency.
    """
    import random

    rotating = isinstance(variables, list)
    payload = None if rotating else json.dumps({"query": query, "variables": variables}).encode()
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    conn = _PersistentConn(url)
    while time.monotonic() < end_time:
        if rotating:
            payload = json.dumps({"query": query, "variables": random.choice(variables)}).encode()  # noqa: S311
        ok, lat, cat, detail = conn.post_graphql(payload)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, detail))
    return latencies, errors, breakdown, samples


def _worker_graphql_apq(url: str, payload: bytes, end_time: float) -> _WorkerResult:
    """Worker for APQ hash-only requests (query pre-registered during setup).

    Sends a static pre-computed payload on every request — no query string,
    no per-request JSON encoding. Pure hash-lookup path on the server.
    """
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    conn = _PersistentConn(url)
    while time.monotonic() < end_time:
        ok, lat, cat, detail = conn.post_graphql(payload)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, detail))
    return latencies, errors, breakdown, samples


def _worker_graphql_apq_vars(
    url: str, payloads: list[bytes], end_time: float
) -> _WorkerResult:
    """Worker for APQ requests that carry variables (e.g. mutations).

    `payloads` is a pre-computed list of hash+variables JSON blobs (no query
    string). A random entry is chosen per request to distribute writes across
    multiple rows without per-request JSON encoding overhead.
    """
    import random

    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    conn = _PersistentConn(url)
    while time.monotonic() < end_time:
        ok, lat, cat, detail = conn.post_graphql(random.choice(payloads))  # noqa: S311
        if ok:
            latencies.append(lat)
        else:
            errors += 1
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, detail))
    return latencies, errors, breakdown, samples


def _worker_mutation_graphql(url: str, query: str, end_time: float) -> _WorkerResult:
    """Worker for GraphQL mutations — identical to _worker_graphql."""
    return _worker_graphql(url, query, end_time)


def _worker_mutation_rest(url: str, payload: bytes, end_time: float) -> _WorkerResult:
    """Worker for REST PUT mutations."""
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    conn = _PersistentConn(url)
    while time.monotonic() < end_time:
        ok, lat, cat, detail = conn.put(payload)
        if ok:
            latencies.append(lat)
        else:
            errors += 1
            breakdown[cat] = breakdown.get(cat, 0) + 1
            if len(samples) < _MAX_ERROR_SAMPLES:
                samples.append((cat, detail))
    return latencies, errors, breakdown, samples


def _worker_graphql_composite(url: str, payloads: list[bytes], end_time: float) -> _WorkerResult:
    """Worker for T1 total scenario with multiple sequential GraphQL POSTs.

    Used by FraiseQL where comments can't be nested on post — fires
    post(id) then comments(limit:10) sequentially. Latency = total wall-clock.
    """
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    conn = _PersistentConn(url)
    while time.monotonic() < end_time:
        t0 = time.monotonic()
        failed = False
        for payload in payloads:
            ok, _lat, cat, detail = conn.post_graphql(payload)
            if not ok:
                failed = True
                errors += 1
                breakdown[cat] = breakdown.get(cat, 0) + 1
                if len(samples) < _MAX_ERROR_SAMPLES:
                    samples.append((cat, detail))
                break
        if not failed:
            elapsed = (time.monotonic() - t0) * 1000
            latencies.append(elapsed)
    return latencies, errors, breakdown, samples


def _worker_rest_composite(urls: list[str], end_time: float) -> _WorkerResult:
    """Worker for T1 total scenario: chains multiple sequential REST GETs per iteration.

    Each iteration fires all URLs in order (simulating a client that must fetch
    post → author → comments). Latency = total wall-clock for the full sequence.
    """
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    conns = [_PersistentConn(url) for url in urls]
    while time.monotonic() < end_time:
        t0 = time.monotonic()
        failed = False
        for conn in conns:
            ok, _lat, cat, detail = conn.get()
            if not ok:
                failed = True
                errors += 1
                breakdown[cat] = breakdown.get(cat, 0) + 1
                if len(samples) < _MAX_ERROR_SAMPLES:
                    samples.append((cat, detail))
                break
        if not failed:
            elapsed = (time.monotonic() - t0) * 1000
            latencies.append(elapsed)
    return latencies, errors, breakdown, samples


def _worker_mc1_classical(
    url: str, m1_payload: bytes, q1_payload: bytes, end_time: float
) -> _WorkerResult:
    """Worker for MC1 classical cycle: M1 mutation + Q1 re-fetch (2 serial requests).

    Each cycle represents the minimum client work to reach consistent state after a
    mutation on a classical GraphQL framework. Latency = total wall-clock for the pair.
    RPS = mutation-to-consistent-state cycles per second.
    """
    latencies: list[float] = []
    errors = 0
    breakdown: dict[str, int] = {}
    samples: list[tuple[str, str]] = []
    conn = _PersistentConn(url)
    while time.monotonic() < end_time:
        t0 = time.monotonic()
        failed = False
        for payload in (m1_payload, q1_payload):
            ok, _lat, cat, detail = conn.post_graphql(payload)
            if not ok:
                failed = True
                errors += 1
                breakdown[cat] = breakdown.get(cat, 0) + 1
                if len(samples) < _MAX_ERROR_SAMPLES:
                    samples.append((cat, detail))
                break
        if not failed:
            latencies.append((time.monotonic() - t0) * 1000)
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
        # Skip unresolved sentinels and composite entries in diagnose mode
        if isinstance(entry, str) and entry in ("M1", "MC1", "C3", "HC3", "T1", "M1d", "Q1_APQ", "Q2b_APQ", "M1_APQ"):
            print(f"    {query_name}: skipped (unresolved sentinel)", flush=True)
            continue
        if isinstance(entry, dict):
            mode = entry.get("mode", "composite")
            print(f"    {query_name}: skipped (composite mode={mode})", flush=True)
            continue
        fw_type = fw_config["type"]
        print(f"    {query_name}:", flush=True)
        for i in range(5):
            if fw_type == "graphql":
                if len(entry) == 3:
                    url, query, variables = entry
                    payload = json.dumps({"query": query, "variables": variables}).encode()
                    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                    t0 = time.monotonic()
                    try:
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            raw = resp.read()
                            elapsed = (time.monotonic() - t0) * 1000
                            body = json.loads(raw)
                            ok = "errors" not in body
                            lat, cat, detail = elapsed, ("graphql_error" if not ok else ""), (str(body.get("errors", ""))[:200] if not ok else "")
                    except Exception as exc:
                        ok, lat, cat, detail = False, (time.monotonic() - t0) * 1000, "connection_error", str(exc)[:200]
                else:
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
            if isinstance(entry, dict) and entry.get("mode") == "apq":
                # APQ hash-only: no query string, pure hash lookup on the server
                url = entry["url"]
                payload = entry["payload"]
                futures = [
                    pool.submit(_worker_graphql_apq, url, payload, end_time)
                    for _ in range(concurrency)
                ]
            elif isinstance(entry, dict) and entry.get("mode") == "apq_vars":
                # APQ with variables: hash + rotating variables payloads (no query string)
                url = entry["url"]
                payloads = entry["payloads"]
                futures = [
                    pool.submit(_worker_graphql_apq_vars, url, payloads, end_time)
                    for _ in range(concurrency)
                ]
            elif isinstance(entry, dict) and entry.get("mode") == "graphql_composite":
                # FraiseQL T1: chain multiple GraphQL POSTs per iteration
                url = entry["url"]
                payloads = entry["payloads"]
                futures = [
                    pool.submit(_worker_graphql_composite, url, payloads, end_time)
                    for _ in range(concurrency)
                ]
            elif isinstance(entry, dict) and entry.get("mode") == "composite":
                # T1 total scenario: chain multiple REST calls per iteration
                urls = entry["urls"]
                futures = [
                    pool.submit(_worker_rest_composite, urls, end_time)
                    for _ in range(concurrency)
                ]
            elif isinstance(entry, dict) and entry.get("mode") == "mc1_cascade":
                # FraiseQL MC1: single mutation returns cascade — 1 request per cycle
                url = entry["url"]
                query = entry["query"]
                variables = entry["variables"]
                futures = [
                    pool.submit(_worker_graphql_with_vars, url, query, variables, end_time)
                    for _ in range(concurrency)
                ]
            elif isinstance(entry, dict) and entry.get("mode") == "mc1_classical":
                # Classical MC1: M1 mutation + Q1 re-fetch — 2 requests per cycle
                url = entry["url"]
                m1_p = entry["m1_payload"]
                q1_p = entry["q1_payload"]
                futures = [
                    pool.submit(_worker_mc1_classical, url, m1_p, q1_p, end_time)
                    for _ in range(concurrency)
                ]
            elif fw_type == "graphql":
                if len(entry) == 3:
                    url, query, variables = entry
                    futures = [
                        pool.submit(_worker_graphql_with_vars, url, query, variables, end_time)
                        for _ in range(concurrency)
                    ]
                else:
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


def start_service(service: str, health_url: str, timeout_secs: int = 60, *, no_build: bool = False) -> None:
    print(f"  starting {service}...", end=" ", flush=True)
    if no_build:
        _compose("up", "-d", service)
    else:
        _compose("up", "-d", "--build", service)
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
    service: str, health_url: str, timeout_secs: int = 60, *, no_build: bool = False
) -> bool:
    """Like start_service but returns False instead of raising on timeout."""
    try:
        start_service(service, health_url, timeout_secs, no_build=no_build)
        return True
    except RuntimeError as exc:
        print(f"  WARN: {exc} — skipping", flush=True)
        _compose("stop", service, check=False)
        _compose("rm", "-f", service, check=False)
        return False
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        print(f"  WARN: docker compose up failed (exit {exc.returncode}) — skipping", flush=True)
        if stderr:
            print(f"  stderr: {stderr[:300]}", flush=True)
        _compose("stop", service, check=False)
        _compose("rm", "-f", service, check=False)
        return False


def stop_service(service: str) -> None:
    print(f"  stopping {service}...", end=" ", flush=True)
    _compose("stop", service)
    _compose("rm", "-f", service, check=False)
    print("stopped", flush=True)


def prune_service_image(service: str) -> None:
    """Remove the locally-built docker image for a compose service.

    Docker Compose names images as <project>-<service>:latest where the project
    name is derived from the working directory (velocitybench). Pre-pulled images
    (postgres, etc.) don't follow this convention and are left untouched.
    """
    image_name = f"velocitybench-{service}:latest"
    result = subprocess.run(
        ["docker", "rmi", image_name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        print(f"  image {image_name} pruned", flush=True)


def _check_disk_space(min_gb: float = 5.0) -> None:
    """Abort early if there is insufficient free disk space.

    TV M1 generates ~255 000 mutations × ~2 KB WAL per row × 2 tables ≈ 1 GB WAL,
    plus dead-tuple bloat and Docker overlay writes.  5 GB headroom is the minimum
    safe threshold for a full medium-dataset sequential run.
    """
    free_gb = shutil.disk_usage("/").free / (1024**3)
    if free_gb < min_gb:
        raise RuntimeError(
            f"Insufficient disk space: {free_gb:.1f} GB free, {min_gb:.0f} GB required. "
            "Free space before benchmarking (try: docker system prune -f)."
        )
    print(f"  disk space OK: {free_gb:.1f} GB free (≥{min_gb:.0f} GB required)", flush=True)


def _reset_postgres_state() -> None:
    """CHECKPOINT + VACUUM + pg_prewarm between framework runs.

    Reclaims dead-tuple bloat from mutation workloads, flushes WAL so the next
    framework starts with a clean write path, and pre-warms the shared-buffer
    pool for the benchmark tables.  Prevents PostgreSQL state contamination from
    one framework's M1 run from degrading the next framework's measurements.

    Best-effort: failures are printed but do not abort the benchmark.
    """
    print("  resetting PostgreSQL state (CHECKPOINT + VACUUM + pg_prewarm)...", end=" ", flush=True)
    # UPDATE tb_user triggers a 3-table pg_tviews cascade: tv_user, tv_post, tv_comment.
    # All five tables must be pre-warmed to avoid cold-page I/O at the start of M1.
    result = _compose(
        "exec", "-T", "postgres",
        "psql", "-U", "benchmark", "-d", "velocitybench_benchmark",
        "-c", "CHECKPOINT",
        "-c", "VACUUM ANALYZE benchmark.tb_user, benchmark.tv_user, benchmark.tv_post, benchmark.tv_comment",
        check=False,
    )
    # Prewarm: prefer pg_prewarm (reads all blocks into shared_buffers via OS read-ahead).
    # If the extension is absent, fall back to a full column read — reading the JSONB 'data'
    # column forces a heap scan that loads all pages, unlike COUNT(*) which may use the
    # visibility map.  Added to 01-extensions.sql; takes effect after image rebuild.
    _compose(
        "exec", "-T", "postgres",
        "psql", "-U", "benchmark", "-d", "velocitybench_benchmark",
        "-c", "SELECT pg_prewarm('benchmark.tb_user'), pg_prewarm('benchmark.tv_user'), "
              "pg_prewarm('benchmark.tv_post'), pg_prewarm('benchmark.tv_comment')",
        check=False,
    )
    # Unconditional fallback: if pg_prewarm is absent the above call returns non-zero and
    # is silently skipped (check=False), but we still want warm buffers.  Reading octet_length
    # of every data column value is guaranteed to load all heap pages into shared_buffers.
    _compose(
        "exec", "-T", "postgres",
        "psql", "-U", "benchmark", "-d", "velocitybench_benchmark",
        "-c", "SELECT sum(octet_length(data::text)) FROM benchmark.tv_user",
        "-c", "SELECT sum(octet_length(data::text)) FROM benchmark.tv_post",
        "-c", "SELECT sum(octet_length(data::text)) FROM benchmark.tv_comment",
        check=False,
    )
    if result.returncode == 0:
        print("done ✓", flush=True)
    else:
        stderr = result.stderr.strip() if result.stderr else "(no stderr)"
        print(f"warn (exit {result.returncode}): {stderr[:200]}", flush=True)


# ---------------------------------------------------------------------------
# Resource metrics (opt-in via --resource-metrics)
# ---------------------------------------------------------------------------

# Map framework name → frameworks/ subdirectory name when they differ.
_FW_DIR_OVERRIDE: dict[str, str] = {
    "spring-boot": "java-spring-boot",
    "fraiseql-tv": "fraiseql",
    "fraiseql-tv-cache": "fraiseql",
    "fraiseql-tv-nocache": "fraiseql",
    "fraiseql-v": "fraiseql",
    "fraiseql-v-nocache": "fraiseql",
    "fraiseql-v-cache": "fraiseql",
    "fraiseql-tv-audit": "fraiseql",
}

_LANG_EXTENSIONS: dict[str, list[str]] = {
    "Rust": [".rs"],
    "Go": [".go"],
    "Node.js": [".js", ".ts"],
    "Python": [".py"],
    "Java": [".java"],
    "Scala": [".scala"],
    "Ruby": [".rb"],
    "PHP": [".php"],
    "C#": [".cs"],
}

# Directories to exclude from LOC/complexity counting.
_SKIP_DIRS = {
    "test", "tests", "spec", "__tests__", "__pycache__",
    "vendor", "node_modules", ".venv", "venv", "env",
    "target", "build", "dist", ".gradle", "generated",
    "migrations", "fixtures",
}

# Language-agnostic decision-point keywords for complexity proxy.
_DECISION_RE = re.compile(
    r"\b(if|else|elif|for|while|switch|case|match|catch|except|rescue|unless|loop)\b"
    r"|&&|\|\|"
)


def _count_file_loc(path: Path, total_loc: int, total_decisions: int) -> tuple[int, int]:
    """Count non-blank, non-comment LOC and decision keywords in a single file."""
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return total_loc, total_decisions
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Skip pure comment lines (covers //, #, --, /*, *)
        if stripped.startswith(("//", "#", "--", "*", "/*")):
            continue
        total_loc += 1
        total_decisions += len(_DECISION_RE.findall(stripped))
    return total_loc, total_decisions


def compute_loc_complexity(fw_name: str) -> tuple[int, float]:
    """Return (loc, complexity_per_100_loc) for the framework's source code.

    LOC = non-blank, non-pure-comment lines in primary source files.
    Complexity proxy = decision-keyword occurrences per 100 LOC (McCabe proxy).
    Excludes test directories, vendor/generated code.

    Supports two counting modes (both active when configured):
    - Framework source directory scan: all files with language-matched extensions
      under frameworks/<dir>/, excluding test/vendor dirs.
    - Extra files (loc_extra_files config key): explicit list of repo-relative paths
      to include regardless of language. Used for FraiseQL's Python schema files,
      SQL view definitions, and PL/pgSQL mutation functions — these are the
      application-level code a developer writes, equivalent to resolvers in other
      frameworks.
    """
    fw_config = FRAMEWORKS.get(fw_name, {})
    lang = fw_config.get("language", "")
    extensions = _LANG_EXTENSIONS.get(lang, [])

    repo_root = Path(__file__).parent.parent.parent
    total_loc = 0
    total_decisions = 0

    # Language-matched source files in the framework directory
    if extensions:
        dir_name = _FW_DIR_OVERRIDE.get(fw_name, fw_name)
        fw_dir = repo_root / "frameworks" / dir_name
        if fw_dir.is_dir():
            for ext in extensions:
                for path in fw_dir.rglob(f"*{ext}"):
                    if any(skip in path.parts for skip in _SKIP_DIRS):
                        continue
                    total_loc, total_decisions = _count_file_loc(path, total_loc, total_decisions)

    # Extra files: Python schemas, SQL views, PL/pgSQL functions.
    # Listed explicitly per framework so only application-level code is counted,
    # not shared infrastructure SQL.
    for rel_path in fw_config.get("loc_extra_files", []):
        path = repo_root / rel_path
        if path.is_file():
            total_loc, total_decisions = _count_file_loc(path, total_loc, total_decisions)

    if total_loc == 0:
        return 0, 0.0
    complexity = total_decisions / total_loc * 100
    return total_loc, round(complexity, 1)


def get_image_size_mb(service: str) -> float:
    """Return the docker image size in MB, or 0.0 if unavailable."""
    image_name = f"velocitybench-{service}:latest"
    result = subprocess.run(
        ["docker", "image", "inspect", image_name, "--format", "{{.Size}}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return 0.0
    try:
        return int(result.stdout.strip()) / (1024 * 1024)
    except ValueError:
        return 0.0


def _parse_mem_mb(mem_str: str) -> float:
    """Parse docker stats memory like '256MiB / 16GiB' → float MB (current usage)."""
    used = mem_str.split("/")[0].strip()
    m = re.match(r"([\d.]+)\s*([A-Za-z]+)", used)
    if not m:
        return 0.0
    value, unit = float(m.group(1)), m.group(2).lower()
    multipliers = {"b": 1 / (1024 * 1024), "kib": 1 / 1024, "kb": 1 / 1024,
                   "mib": 1.0, "mb": 1.0, "gib": 1024.0, "gb": 1024.0}
    return value * multipliers.get(unit, 0.0)


def _parse_cpu_pct(cpu_str: str) -> float:
    """Parse docker stats CPU like '12.50%' → 12.5, or -1 on failure."""
    m = re.match(r"([\d.]+)%", cpu_str.strip())
    return float(m.group(1)) if m else -1.0


@dataclass
class FrameworkResourceMetrics:
    fw_name: str
    loc: int = 0
    complexity_per_100_loc: float = 0.0
    image_mb: float = 0.0
    peak_ram_mb: float = 0.0
    avg_cpu_pct: float = 0.0


@dataclass
class DbTableSize:
    tablename: str
    total_bytes: int
    heap_bytes: int
    indexes_bytes: int

    def _fmt(self, n: int) -> str:
        mb = n / (1024 * 1024)
        return f"{mb / 1024:.2f} GB" if mb >= 1024 else f"{mb:.1f} MB"

    @property
    def total_fmt(self) -> str:
        return self._fmt(self.total_bytes)

    @property
    def heap_fmt(self) -> str:
        return self._fmt(self.heap_bytes)

    @property
    def indexes_fmt(self) -> str:
        return self._fmt(self.indexes_bytes)


def collect_db_footprint() -> list[DbTableSize]:
    """Query PostgreSQL for benchmark schema table sizes.

    Returns a list sorted by total_bytes descending, or [] on failure.
    Uses the same docker compose exec pattern as _reset_postgres_state().
    """
    query = (
        "SELECT tablename,"
        " pg_total_relation_size('benchmark.' || tablename),"
        " pg_relation_size('benchmark.' || tablename),"
        " pg_indexes_size('benchmark.' || tablename)"
        " FROM pg_tables"
        " WHERE schemaname = 'benchmark'"
        " ORDER BY pg_total_relation_size('benchmark.' || tablename) DESC;"
    )
    result = _compose(
        "exec", "-T", "postgres",
        "psql", "-U", "benchmark", "-d", "velocitybench_benchmark",
        "--csv", "--tuples-only",
        "-c", query,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    tables: list[DbTableSize] = []
    for line in result.stdout.strip().splitlines():
        parts = line.strip().split(",")
        if len(parts) != 4:
            continue
        try:
            tables.append(DbTableSize(
                tablename=parts[0].strip(),
                total_bytes=int(parts[1]),
                heap_bytes=int(parts[2]),
                indexes_bytes=int(parts[3]),
            ))
        except (ValueError, IndexError):
            continue
    return tables


class ResourceMonitor:
    """Background thread that polls `docker stats` while a framework is benchmarked.

    Collects peak RAM (MiB) and average CPU% for the container.
    Container name follows Compose convention: velocitybench-<service>-1.
    """

    def __init__(self, service: str, interval_secs: float = 2.0) -> None:
        self._container = f"velocitybench-{service}-1"
        self._interval = interval_secs
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._peak_ram_mb: float = 0.0
        self._cpu_samples: list[float] = []

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> tuple[float, float]:
        """Stop monitoring and return (peak_ram_mb, avg_cpu_pct)."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        avg_cpu = statistics.mean(self._cpu_samples) if self._cpu_samples else 0.0
        return self._peak_ram_mb, round(avg_cpu, 1)

    def _run(self) -> None:
        while not self._stop.is_set():
            self._poll()
            self._stop.wait(self._interval)

    def _poll(self) -> None:
        result = subprocess.run(
            [
                "docker", "stats", "--no-stream",
                "--format", "{{.MemUsage}}\t{{.CPUPerc}}",
                self._container,
            ],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return
        line = result.stdout.strip().split("\n")[0]
        parts = line.split("\t")
        if len(parts) < 2:
            return
        ram_mb = _parse_mem_mb(parts[0])
        cpu_pct = _parse_cpu_pct(parts[1])
        if ram_mb > self._peak_ram_mb:
            self._peak_ram_mb = ram_mb
        if cpu_pct >= 0:
            self._cpu_samples.append(cpu_pct)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def _row(
    r: BenchResult, detailed_errors: bool = False, show_language: bool = False
) -> str:
    lang = FRAMEWORKS.get(r.framework, {}).get("language", "")
    lang_col = f" | {lang}" if show_language else ""
    if r.skipped:
        return f"| {r.framework}{lang_col} | {r.query_name} | — | — | — | — | — | _{r.skip_reason}_ |"
    err_col = f"{r.error_rate_pct:.1f}%"
    if detailed_errors and r.error_breakdown:
        parts = []
        total_errs = sum(r.error_breakdown.values()) or 1
        for cat, cnt in sorted(r.error_breakdown.items(), key=lambda x: -x[1]):
            pct = cnt / total_errs * 100
            parts.append(f"{cat}: {pct:.0f}%")
        err_col += f" ({', '.join(parts)})"
    return (
        f"| {r.framework}{lang_col} | {r.query_name} "
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
    "M1d": "`mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)",
    # Feature benchmark labels (published filter cross-framework, FraiseQL-specific extras)
    "C3": "`user(id: UUID) { id username fullName }` — single entity, rotating UUIDs",
    "HC3": "`user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)",
    "F1": "`posts(published: true, limit: 10) { id title }` — published filter, no nesting",
    "F2": "`posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting",
    "F3": "`users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison",
    "T1": "Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`",
    "MC1": "Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.",
    "Q1_APQ": "APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.",
    "Q2b_APQ": "APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.",
    "M1_APQ": "APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.",
}


def format_report(
    results: list[BenchResult],
    args: argparse.Namespace,
    date_str: str,
    resource_metrics: dict[str, FrameworkResourceMetrics] | None = None,
    db_footprint: list[DbTableSize] | None = None,
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

    # Database footprint — TV vs TB storage cost (collected once before any framework runs)
    if db_footprint:
        tv_tables = [t for t in db_footprint if t.tablename.startswith("tv_")]
        tb_tables = [t for t in db_footprint if t.tablename.startswith("tb_")]
        tv_bytes = sum(t.total_bytes for t in tv_tables)
        tb_bytes = sum(t.total_bytes for t in tb_tables)
        amplification = (tv_bytes + tb_bytes) / tb_bytes if tb_bytes else 0.0
        sample = db_footprint[0]  # borrow _fmt helper
        lines += [
            "## Database Footprint",
            "",
            "TV tables (pre-computed JSONB) inflate storage by embedding denormalized data at write time.",
            "Views (v_*) add no storage — they are computed at query time.",
            "",
            "| Table | Heap | Indexes | Total |",
            "|-------|------|---------|-------|",
        ]
        for t in db_footprint:
            lines.append(f"| `{t.tablename}` | {t.heap_fmt} | {t.indexes_fmt} | {t.total_fmt} |")
        lines += [
            "",
            f"**TV tables**: {sample._fmt(tv_bytes)}  ",
            f"**TB tables (normalized baseline)**: {sample._fmt(tb_bytes)}  ",
            f"**Storage amplification**: {amplification:.2f}× "
            f"(TV adds {sample._fmt(tv_bytes)} on top of the normalized {sample._fmt(tb_bytes)})  ",
            "",
            "> Each `tv_comment` row embeds the full comment author + the full post + the post's author.",
            "> With 200 000 comments this JSONB duplication dominates the TV storage cost.",
            "",
            "---",
            "",
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
            "| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |",
            "|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|",
        ]
        for r in results:
            if r.query_name == qname:
                lines.append(_row(r, detailed_errors=detailed, show_language=True))

    # Category leaderboards for Q1
    _CATEGORY_LABELS = {
        "rest": "REST Frameworks",
        "graphql": "GraphQL Frameworks",
        "graphql-precomputed": "Pre-computed GraphQL (FraiseQL)",
        "graphql-schema-first": "Schema-first GraphQL",
    }
    q1_results = [r for r in results if r.query_name == "Q1" and not r.skipped]

    for cat, cat_label in _CATEGORY_LABELS.items():
        cat_results = sorted(
            [
                r
                for r in q1_results
                if FRAMEWORKS.get(r.framework, {}).get("category") == cat
            ],
            key=lambda r: r.rps,
            reverse=True,
        )
        if not cat_results:
            continue
        lines += [
            "",
            "---",
            "",
            f"## {cat_label} — Q1 (sorted by RPS)",
            "",
            "| Framework | Language | RPS | p50 ms | p99 ms | Errors |",
            "|-----------|----------|----:|-------:|-------:|--------|",
        ]
        for r in cat_results:
            lang = FRAMEWORKS.get(r.framework, {}).get("language", "")
            lines.append(
                f"| {r.framework} | {lang} "
                f"| {r.rps:.0f} | {r.p50_ms:.1f} | {r.p99_ms:.1f} "
                f"| {r.error_rate_pct:.1f}% |"
            )

    # Summary: Q1 cross-framework comparison (all categories)
    lines += [
        "",
        "---",
        "",
        "## Summary — Q1 Cross-Framework (sorted by RPS)",
        "",
        "| Framework | Language | Category | RPS | p50 ms | p99 ms |",
        "|-----------|----------|----------|----:|-------:|-------:|",
    ]
    all_q1_sorted = sorted(q1_results, key=lambda r: r.rps, reverse=True)
    for r in all_q1_sorted:
        fw_cfg = FRAMEWORKS.get(r.framework, {})
        lang = fw_cfg.get("language", "")
        cat = fw_cfg.get("category", "")
        lines.append(
            f"| {r.framework} | {lang} | {cat} "
            f"| {r.rps:.0f} | {r.p50_ms:.1f} | {r.p99_ms:.1f} |"
        )

    # Resource metrics section (only if collected via --resource-metrics)
    if resource_metrics:
        lines += [
            "",
            "---",
            "",
            "## Resource Metrics",
            "",
            "> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  ",
            "> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  ",
            "> **Image**: compressed docker image size.  ",
            "> **Peak RAM**: maximum RSS observed during the full benchmark run.  ",
            "> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.",
            "",
            "| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |",
            "|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|",
        ]
        # Sort by Q1 RPS descending (same order as summary table) for easy cross-reference.
        q1_rps: dict[str, float] = {r.framework: r.rps for r in all_q1_sorted}
        sorted_fws = sorted(
            resource_metrics.values(),
            key=lambda m: q1_rps.get(m.fw_name, 0),
            reverse=True,
        )
        for m in sorted_fws:
            lang = FRAMEWORKS.get(m.fw_name, {}).get("language", "")
            image_str = f"{m.image_mb:.0f}" if m.image_mb else "—"
            ram_str = f"{m.peak_ram_mb:.0f}" if m.peak_ram_mb else "—"
            cpu_str = f"{m.avg_cpu_pct:.1f}" if m.avg_cpu_pct else "—"
            complexity_str = f"{m.complexity_per_100_loc:.1f}" if m.loc else "—"
            loc_str = f"{m.loc:,}" if m.loc else "—"
            lines.append(
                f"| {m.fw_name} | {lang} "
                f"| {loc_str} | {complexity_str} "
                f"| {image_str} | {ram_str} | {cpu_str} |"
            )

    # MC1 cascade advantage note — only when MC1 results are present
    mc1_results = [r for r in results if r.query_name == "MC1" and not r.skipped]
    if mc1_results:
        fraiseql_mc1 = [
            r for r in mc1_results
            if FRAMEWORKS.get(r.framework, {}).get("m1_template") == "fraiseql"
        ]
        classical_mc1 = [r for r in mc1_results if r not in fraiseql_mc1]
        lines += [
            "",
            "---",
            "",
            "## MC1 — Cascade Advantage",
            "",
            "**Requests per cycle** (what a client must issue to reach fully consistent state after a mutation):",
            "",
            "| Framework type | Requests/cycle | What is sent |",
            "|----------------|---------------|--------------|",
            "| FraiseQL | **1** | M1 mutation — `cascade` field in response contains all affected entities |",
            "| Classical GraphQL | **2** | M1 mutation (1) + Q1 list re-fetch (2) |",
            "",
            "RPS above = **cycles/second** (mutation-to-consistent-state cycles, not raw requests).  ",
            "At equal cycles/second, FraiseQL issues 2× fewer HTTP round trips and returns ~0 stale entities.  ",
            "Classical frameworks must fire follow-up queries to invalidate stale cache entries.",
        ]
        if fraiseql_mc1 and classical_mc1:
            best_fraiseql = max(fraiseql_mc1, key=lambda r: r.rps)
            best_classical = max(classical_mc1, key=lambda r: r.rps)
            ratio = best_fraiseql.rps / best_classical.rps if best_classical.rps > 0 else 0
            lines += [
                "",
                f"> **Peak**: {best_fraiseql.framework} {best_fraiseql.rps:.0f} cycles/s (1 req) vs "
                f"{best_classical.framework} {best_classical.rps:.0f} cycles/s (2 req) — "
                f"{ratio:.1f}× more cycles/s with half the round trips.",
            ]

    # M1 cascade characteristics note — only when M1 results are present
    m1_results = [r for r in results if r.query_name == "M1" and not r.skipped]
    if m1_results:
        # tb_user update cascades to tv_user (1) + tv_post (~10) + tv_comment (~50) = ~61 rows
        cascade_fan_out = 61
        peak_m1_rps = max(r.rps for r in m1_results)
        peak_row_writes = int(peak_m1_rps * cascade_fan_out)
        lines += [
            "",
            "---",
            "",
            "## M1 — Cascade Characteristics",
            "",
            "Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:",
            "1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` "
            "(author + post embedded) = **~61 rows per top-level mutation**.",
            "",
            f"At peak throughput of {peak_m1_rps:,.0f} M/s: "
            f"**~{peak_row_writes:,} row writes/second** across four tables.",
            "",
            "> **Run-order methodology**: M1 results reflect two distinct operational conditions, "
            "both valid production scenarios:",
            "> ",
            "> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates "
            "rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window "
            "table state.",
            "> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst "
            f"(~{peak_m1_rps * cascade_fan_out / 1_000_000:.1f}M cascade writes) scattered row "
            "versions across pages. VACUUM reclaims dead tuples between runs but cannot repack "
            "pages without VACUUM FULL. Equivalent to sustained production load where autovacuum "
            "lags behind write throughput.",
            "> ",
            f"> The cascade multiplier ({cascade_fan_out}×) is the operative variable: "
            "fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table "
            "vs fragmented-table range characterises the operational envelope, not benchmark noise.",
        ]

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
    parser.add_argument(
        "--broken-only",
        action="store_true",
        help=f"Run only frameworks with known failures: {', '.join(BROKEN_FRAMEWORKS)}",
    )
    parser.add_argument(
        "--prune-images",
        action="store_true",
        help="Remove each framework's docker image after its benchmark run to reclaim disk space. "
             "postgres and other pre-pulled images are never touched.",
    )
    parser.add_argument(
        "--resource-metrics",
        action="store_true",
        help="Collect LOC, complexity, image size, RAM, and CPU metrics per framework "
             "(adds docker stats polling overhead; use for analysis runs, not timing runs).",
    )
    args = parser.parse_args()

    if args.broken_only:
        args.frameworks = [fw for fw in BROKEN_FRAMEWORKS if fw in FRAMEWORKS]

    unknown = [fw for fw in args.frameworks if fw not in FRAMEWORKS]
    if unknown:
        print(f"Unknown frameworks: {unknown}", file=sys.stderr)
        print(f"Available: {list(FRAMEWORKS)}", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    print("VelocityBench — Sequential Isolation Benchmark")
    print("Pre-flight checks")
    _check_disk_space()
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
    all_resource_metrics: dict[str, FrameworkResourceMetrics] = {}

    # Collect database footprint once — before any framework runs so mutation workloads
    # don't inflate sizes.  Best-effort: returns [] if postgres is not yet up.
    print("Collecting database footprint...", end=" ", flush=True)
    db_footprint = collect_db_footprint()
    if db_footprint:
        tv_bytes = sum(t.total_bytes for t in db_footprint if t.tablename.startswith("tv_"))
        tb_bytes = sum(t.total_bytes for t in db_footprint if t.tablename.startswith("tb_"))
        sample = db_footprint[0]
        print(
            f"done ✓  TV={sample._fmt(tv_bytes)}  TB={sample._fmt(tb_bytes)}"
            f"  amplification={((tv_bytes + tb_bytes) / tb_bytes if tb_bytes else 0):.2f}×",
            flush=True,
        )
    else:
        print("skipped (postgres not available)", flush=True)
    print()

    for i, fw_name in enumerate(args.frameworks):
        fw_config = FRAMEWORKS[fw_name]
        print(f"[{i + 1}/{len(args.frameworks)}] {fw_name}")

        query_names = list(fw_config["queries"])

        # Reset PostgreSQL state before every framework run — including the first —
        # so each variant starts from a consistent baseline (no dead tuples from
        # prior M1 runs, WAL flushed, buffer cache warmed).
        _reset_postgres_state()

        if not args.no_isolation:
            timeout = fw_config.get("start_timeout", 60)
            healthy = start_service_or_skip(
                fw_config["compose_service"], fw_config["health_url"], timeout,
                no_build=fw_config.get("no_build", False),
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
                if args.prune_images:
                    prune_service_image(fw_config["compose_service"])
                continue
        else:
            healthy = True

        if args.diagnose:
            run_diagnose(fw_name, fw_config)

        # Resource metrics: collect static metrics and start runtime monitor
        _monitor: ResourceMonitor | None = None
        if args.resource_metrics:
            loc, complexity = compute_loc_complexity(fw_name)
            image_mb = get_image_size_mb(fw_config["compose_service"])
            all_resource_metrics[fw_name] = FrameworkResourceMetrics(
                fw_name=fw_name,
                loc=loc,
                complexity_per_100_loc=complexity,
                image_mb=image_mb,
            )
            if not args.no_isolation:
                _monitor = ResourceMonitor(fw_config["compose_service"])
                _monitor.start()

        # Resolve M1, C3, and MC1 sentinel queries at runtime (need a real user UUID)
        needs_user_id = (
            fw_config["queries"].get("M1") == "M1"
            or fw_config["queries"].get("MC1") == "MC1"
            or fw_config["queries"].get("C3") == "C3"
            or fw_config["queries"].get("HC3") == "HC3"
        )
        if needs_user_id:
            user_id = _discover_user_uuid(fw_config)

            if fw_config["queries"].get("M1") == "M1":
                if user_id:
                    if fw_config["type"] == "graphql":
                        q1_entry = fw_config["queries"].get("Q1")
                        gql_url = (
                            q1_entry[0]
                            if q1_entry is not None
                            else fw_config.get("graphql_url", "")
                        )
                        m1_tmpl = fw_config.get("m1_template")
                        if m1_tmpl is None:
                            # standard GraphQL: inline literal
                            mutation = _GQL_M1_TMPL.format(user_id=user_id)
                            fw_config["queries"]["M1"] = (gql_url, mutation)
                        elif m1_tmpl == "fraiseql":
                            # FraiseQL: must use variables (executor ignores inline args).
                            # Use all discovered UUIDs as a rotating list so 40 workers
                            # don't all hammer the same row (row-lock contention).
                            user_ids = _discover_user_uuids(fw_config)
                            if not user_ids:
                                user_ids = [user_id]
                            variables_list = [{"id": uid, "bio": "bench"} for uid in user_ids]
                            fw_config["queries"]["M1"] = (
                                gql_url,
                                _FRAISEQL_M1_QUERY,
                                variables_list,
                            )
                        else:
                            mutation = m1_tmpl.format(user_id=user_id)
                            fw_config["queries"]["M1"] = (gql_url, mutation)
                    else:
                        q1_url = fw_config["queries"]["Q1"]
                        base = q1_url.rsplit("/users", 1)[0]
                        fw_config["queries"]["M1"] = f"{base}/users/{user_id}"
                    print(f"  M1: resolved user UUID {user_id[:8]}...", flush=True)
                else:
                    fw_config["queries"]["M1"] = None
                    print("  M1: could not discover user UUID — skipping", flush=True)

            # M1d: delta mutation — updateUserDelta with rotating bio values.
            # Rotating bios (bio-0..bio-9 × users) forces actual writes every call,
            # matching real mutation workload (no pg_tviews delta-skip optimization).
            if fw_config["queries"].get("M1d") == "M1d":
                if user_id:
                    q1_entry = fw_config["queries"].get("Q1")
                    gql_url = (
                        q1_entry[0]
                        if q1_entry is not None
                        else fw_config.get("graphql_url", "")
                    )
                    user_ids = _discover_user_uuids(fw_config)
                    if not user_ids:
                        user_ids = [user_id]
                    # Rotate bios so every call writes different data (no no-change skip)
                    bios = [f"bio-{i}" for i in range(10)]
                    variables_list = [
                        {"id": uid, "bio": bios[i % len(bios)]}
                        for i, uid in enumerate(user_ids * len(bios))
                    ]
                    fw_config["queries"]["M1d"] = (
                        gql_url,
                        _FRAISEQL_M1D_QUERY,
                        variables_list,
                    )
                    print(
                        f"  M1d: resolved {len(user_ids)} user UUIDs × {len(bios)} bio values "
                        f"(rotating, jsonb_delta variant)",
                        flush=True,
                    )
                else:
                    fw_config["queries"]["M1d"] = None
                    print("  M1d: could not discover user UUID — skipping", flush=True)

            if fw_config["queries"].get("C3") == "C3":
                if user_id:
                    q1_entry = fw_config["queries"].get("Q1")
                    gql_url = (
                        q1_entry[0]
                        if q1_entry is not None
                        else fw_config.get("graphql_url", "")
                    )
                    if fw_config.get("m1_template") == "fraiseql":
                        # FraiseQL: use variables with rotating UUIDs so workers spread
                        # across all discovered users — realistic single-entity lookup traffic.
                        user_ids = _discover_user_uuids(fw_config)
                        if not user_ids:
                            user_ids = [user_id]
                        variables_list = [{"id": uid} for uid in user_ids]
                        fw_config["queries"]["C3"] = (
                            gql_url,
                            _FRAISEQL_C3_QUERY,
                            variables_list,
                        )
                        print(
                            f"  C3: resolved {len(user_ids)} user UUIDs "
                            f"(rotating, fraiseql variables)",
                            flush=True,
                        )
                    else:
                        c3_tmpl = fw_config.get("c3_template", _FRAISEQL_C3_TMPL)
                        c3_query = c3_tmpl.format(user_id=user_id)
                        fw_config["queries"]["C3"] = (gql_url, c3_query)
                        print(f"  C3: resolved user UUID {user_id[:8]}...", flush=True)
                else:
                    fw_config["queries"]["C3"] = None
                    print("  C3: could not discover user UUID — skipping", flush=True)

            if fw_config["queries"].get("HC3") == "HC3":
                if user_id:
                    q1_entry = fw_config["queries"].get("Q1")
                    gql_url = (
                        q1_entry[0]
                        if q1_entry is not None
                        else fw_config.get("graphql_url", "")
                    )
                    if fw_config.get("m1_template") == "fraiseql":
                        # HC3: hot-key variant of C3 — only 5 fixed UUIDs so cache fills after
                        # 5 misses and all subsequent requests are hits. Measures sustained
                        # cache-hit throughput vs raw DB round-trip (nocache).
                        user_ids = _discover_user_uuids(fw_config)
                        hot_ids = user_ids[:5] if user_ids else [user_id]
                        variables_list = [{"id": uid} for uid in hot_ids]
                        fw_config["queries"]["HC3"] = (
                            gql_url,
                            _FRAISEQL_C3_QUERY,
                            variables_list,
                        )
                        print(
                            f"  HC3: resolved {len(hot_ids)} hot user UUIDs "
                            f"(fixed pool, cache saturation test)",
                            flush=True,
                        )
                    else:
                        c3_tmpl = fw_config.get("c3_template", _FRAISEQL_C3_TMPL)
                        c3_query = c3_tmpl.format(user_id=user_id)
                        fw_config["queries"]["HC3"] = (gql_url, c3_query)
                        print(f"  HC3: resolved user UUID {user_id[:8]}...", flush=True)
                else:
                    fw_config["queries"]["HC3"] = None
                    print("  HC3: could not discover user UUID — skipping", flush=True)

            if fw_config["queries"].get("MC1") == "MC1":
                q1_entry = fw_config["queries"].get("Q1")
                gql_url = (
                    q1_entry[0]
                    if q1_entry is not None and isinstance(q1_entry, tuple)
                    else fw_config.get("graphql_url", "")
                )
                q1_query = q1_entry[1] if q1_entry is not None and isinstance(q1_entry, tuple) else _GQL_Q1
                m1_tmpl = fw_config.get("m1_template")
                if m1_tmpl == "fraiseql":
                    # FraiseQL cascade: mutation response includes all affected entities.
                    # 1 request per cycle replaces M1 + Q1 + C3 on classical frameworks.
                    user_ids_mc1 = _discover_user_uuids(fw_config)
                    if not user_ids_mc1 and user_id:
                        user_ids_mc1 = [user_id]
                    if user_ids_mc1:
                        variables_list = [{"id": uid, "bio": "bench"} for uid in user_ids_mc1]
                        fw_config["queries"]["MC1"] = {
                            "mode": "mc1_cascade",
                            "url": gql_url,
                            "query": _FRAISEQL_M1_QUERY,
                            "variables": variables_list,
                        }
                        print(
                            f"  MC1: cascade (1 req/cycle), {len(user_ids_mc1)} user UUIDs",
                            flush=True,
                        )
                    else:
                        fw_config["queries"]["MC1"] = None
                        print("  MC1: could not discover user UUIDs — skipping", flush=True)
                else:
                    # Classical: M1 mutation + Q1 re-fetch (2 serial requests per cycle).
                    if user_id and gql_url:
                        mutation_query = (
                            m1_tmpl.format(user_id=user_id)
                            if isinstance(m1_tmpl, str)
                            else _GQL_M1_TMPL.format(user_id=user_id)
                        )
                        m1_payload = json.dumps({"query": mutation_query}).encode()
                        q1_payload = json.dumps({"query": q1_query}).encode()
                        fw_config["queries"]["MC1"] = {
                            "mode": "mc1_classical",
                            "url": gql_url,
                            "m1_payload": m1_payload,
                            "q1_payload": q1_payload,
                        }
                        print(
                            f"  MC1: classical (2 req/cycle), user {user_id[:8]}...",
                            flush=True,
                        )
                    else:
                        fw_config["queries"]["MC1"] = None
                        print("  MC1: could not discover user UUID — skipping", flush=True)

        # Resolve T1 "total scenario" sentinel — needs a real post UUID + author UUID
        if fw_config["queries"].get("T1") == "T1":
            post_info = _discover_post_uuid(fw_config)
            if post_info:
                post_id, author_id = post_info
                fw_type = fw_config["type"]
                if fw_type == "graphql":
                    # Find the GraphQL URL from any existing query entry
                    gql_url = None
                    for key in ("Q1", "Q2", "Q2b"):
                        entry = fw_config["queries"].get(key)
                        if entry is not None and isinstance(entry, tuple):
                            gql_url = entry[0]
                            break
                    if not gql_url:
                        gql_url = fw_config.get("graphql_url", "")
                    if gql_url:
                        t1_tmpl_key = fw_config.get("t1_template")
                        if t1_tmpl_key == "fraiseql_single":
                            # FraiseQL single-query T1: postFull(id) via v_post_full composed view.
                            # Fetch up to 20 published post UUIDs and rotate to avoid hot-key effect.
                            multi_post_ids = [post_id]
                            try:
                                disc_payload = json.dumps({"query": "{ posts(limit: 20, published: true) { id } }"}).encode()
                                disc_req = urllib.request.Request(
                                    gql_url,
                                    data=disc_payload,
                                    headers={"Content-Type": "application/json"},
                                    method="POST",
                                )
                                with urllib.request.urlopen(disc_req, timeout=10) as disc_resp:
                                    disc_body = json.loads(disc_resp.read())
                                    extra = [p["id"] for p in disc_body.get("data", {}).get("posts", []) if p.get("id")]
                                    if extra:
                                        multi_post_ids = extra
                            except Exception:
                                pass
                            t1_vars = [{"id": pid} for pid in multi_post_ids]
                            fw_config["queries"]["T1"] = (
                                gql_url,
                                _FRAISEQL_T1_SINGLE_QUERY,
                                t1_vars,
                            )
                            print(f"  T1: resolved {len(t1_vars)} post UUIDs (fraiseql single-query postFull)", flush=True)
                        elif t1_tmpl_key == "fraiseql_multi_root":
                            # FraiseQL multi-root T1: parallel SQL execution (fraiseql v2 pipeline)
                            # post(id) + comments(post_id, limit:10) fire as two concurrent queries
                            # against tv_post and tv_comment. No jsonb_agg / v_post_full overhead.
                            multi_post_ids = [post_id]
                            try:
                                disc_payload = json.dumps({"query": "{ posts(limit: 20, published: true) { id } }"}).encode()
                                disc_req = urllib.request.Request(
                                    gql_url,
                                    data=disc_payload,
                                    headers={"Content-Type": "application/json"},
                                    method="POST",
                                )
                                with urllib.request.urlopen(disc_req, timeout=10) as disc_resp:
                                    disc_body = json.loads(disc_resp.read())
                                    extra = [p["id"] for p in disc_body.get("data", {}).get("posts", []) if p.get("id")]
                                    if extra:
                                        multi_post_ids = extra
                            except Exception:
                                pass
                            t1_vars = [{"id": pid} for pid in multi_post_ids]
                            fw_config["queries"]["T1"] = (
                                gql_url,
                                _FRAISEQL_T1_MULTI_ROOT,
                                t1_vars,
                            )
                            print(f"  T1: resolved {len(t1_vars)} post UUIDs (fraiseql multi-root parallel)", flush=True)
                        elif t1_tmpl_key == "fraiseql":
                            # FraiseQL legacy: 2 sequential GraphQL calls (post doesn't nest comments in tview)
                            post_query = _FRAISEQL_T1_POST_TMPL.format(post_id=post_id)
                            payloads = [
                                json.dumps({"query": post_query}).encode(),
                                json.dumps({"query": _FRAISEQL_T1_COMMENTS}).encode(),
                            ]
                            fw_config["queries"]["T1"] = {
                                "mode": "graphql_composite",
                                "url": gql_url,
                                "payloads": payloads,
                            }
                            print(f"  T1: resolved post UUID {post_id[:8]}... (fraiseql composite)", flush=True)
                        elif t1_tmpl_key == "postgraphile":
                            t1_query = _PG_T1_TMPL.format(post_id=post_id)
                            fw_config["queries"]["T1"] = (gql_url, t1_query)
                            print(f"  T1: resolved post UUID {post_id[:8]}... (GraphQL single query)", flush=True)
                        else:
                            t1_query = _GQL_T1_TMPL.format(post_id=post_id)
                            fw_config["queries"]["T1"] = (gql_url, t1_query)
                            print(f"  T1: resolved post UUID {post_id[:8]}... (GraphQL single query)", flush=True)
                    else:
                        fw_config["queries"]["T1"] = None
                        print("  T1: no GraphQL URL found — skipping", flush=True)
                else:
                    # REST: build multi-URL composite call chain
                    # Derive base URL (scheme + host + port) from Q1 endpoint
                    q1_url = fw_config["queries"].get("Q1", "")
                    if isinstance(q1_url, str) and q1_url:
                        parsed = urlparse(q1_url)
                        base = f"{parsed.scheme}://{parsed.netloc}"
                        # Build the sequential REST URLs
                        t1_urls = _build_rest_t1_urls(fw_name, base, post_id, author_id)
                        if t1_urls:
                            fw_config["queries"]["T1"] = {"mode": "composite", "urls": t1_urls}
                            print(f"  T1: resolved post UUID {post_id[:8]}... ({len(t1_urls)} REST calls)", flush=True)
                        else:
                            fw_config["queries"]["T1"] = None
                            print("  T1: could not build REST URL chain — skipping", flush=True)
                    else:
                        fw_config["queries"]["T1"] = None
                        print("  T1: no REST base URL found — skipping", flush=True)
            else:
                fw_config["queries"]["T1"] = None
                print("  T1: could not discover post UUID — skipping", flush=True)

        # Resolve APQ sentinels — register each query with the server once, then
        # store hash-only payloads for the measurement phase.
        _APQ_BASE_QUERIES: dict[str, str] = {
            "Q1_APQ": _GQL_Q1,
            "Q2b_APQ": _GQL_Q2b,
        }
        q1_entry = fw_config["queries"].get("Q1")
        apq_url = (
            q1_entry[0]
            if q1_entry is not None and isinstance(q1_entry, tuple)
            else fw_config.get("graphql_url", "")
        )
        for apq_key, base_query in _APQ_BASE_QUERIES.items():
            if fw_config["queries"].get(apq_key) == apq_key:
                if apq_url:
                    sha256 = _apq_hash(base_query)
                    ok = _apq_register(apq_url, base_query, sha256)
                    if ok:
                        fw_config["queries"][apq_key] = {
                            "mode": "apq",
                            "url": apq_url,
                            "payload": _apq_payload_static(sha256),
                        }
                        print(f"  {apq_key}: registered hash {sha256[:12]}...", flush=True)
                    else:
                        fw_config["queries"][apq_key] = None
                        print(f"  {apq_key}: server does not support APQ — skipping", flush=True)
                else:
                    fw_config["queries"][apq_key] = None
                    print(f"  {apq_key}: no GraphQL URL — skipping", flush=True)

        # M1_APQ: hash + rotating variables (fraiseql) or hash-only (classical inline mutation)
        if fw_config["queries"].get("M1_APQ") == "M1_APQ":
            if apq_url:
                m1_tmpl = fw_config.get("m1_template")
                if m1_tmpl == "fraiseql":
                    # FraiseQL mutation uses variables — pre-compute payloads for each UUID
                    user_ids_apq = _discover_user_uuids(fw_config)
                    if not user_ids_apq:
                        # Fall back to the single UUID discovered for M1
                        single = fw_config["queries"].get("M1")
                        if isinstance(single, tuple) and len(single) == 3:
                            user_ids_apq = [v["id"] for v in single[2]] if single[2] else []
                    if user_ids_apq:
                        sha256 = _apq_hash(_FRAISEQL_M1_QUERY)
                        ok = _apq_register(apq_url, _FRAISEQL_M1_QUERY, sha256)
                        if ok:
                            apq_payloads = [
                                _apq_payload_with_vars(sha256, {"id": uid, "bio": "bench"})
                                for uid in user_ids_apq
                            ]
                            fw_config["queries"]["M1_APQ"] = {
                                "mode": "apq_vars",
                                "url": apq_url,
                                "payloads": apq_payloads,
                            }
                            print(
                                f"  M1_APQ: registered hash {sha256[:12]}... "
                                f"({len(user_ids_apq)} UUID payloads)",
                                flush=True,
                            )
                        else:
                            fw_config["queries"]["M1_APQ"] = None
                            print("  M1_APQ: server does not support APQ — skipping", flush=True)
                    else:
                        fw_config["queries"]["M1_APQ"] = None
                        print("  M1_APQ: could not discover user UUIDs — skipping", flush=True)
                else:
                    # Classical inline mutation: bake UUID into query string, register once
                    m1_entry = fw_config["queries"].get("M1")
                    inline_query = m1_entry[1] if isinstance(m1_entry, tuple) else None
                    if inline_query:
                        sha256 = _apq_hash(inline_query)
                        ok = _apq_register(apq_url, inline_query, sha256)
                        if ok:
                            fw_config["queries"]["M1_APQ"] = {
                                "mode": "apq",
                                "url": apq_url,
                                "payload": _apq_payload_static(sha256),
                            }
                            print(f"  M1_APQ: registered hash {sha256[:12]}...", flush=True)
                        else:
                            fw_config["queries"]["M1_APQ"] = None
                            print("  M1_APQ: server does not support APQ — skipping", flush=True)
                    else:
                        fw_config["queries"]["M1_APQ"] = None
                        print("  M1_APQ: M1 not resolved yet — skipping", flush=True)
            else:
                fw_config["queries"]["M1_APQ"] = None
                print("  M1_APQ: no GraphQL URL — skipping", flush=True)

        for query_name in query_names:
            # VACUUM immediately before M1/MC1/M1_APQ so mutation scenarios start from a
            # defined page state: dead tuples reclaimed, fillfactor reserve restored.
            # Read scenarios ran earlier; their I/O activity is harmless (reads don't
            # create dead tuples). This decouples M1's starting condition from the
            # prior framework's write burst without hiding M1's run-order dependency
            # (the second framework's M1 still runs on pages fragmented by the first).
            if query_name in ("M1", "MC1", "M1_APQ"):
                _reset_postgres_state()
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

        if _monitor is not None and fw_name in all_resource_metrics:
            peak_ram, avg_cpu = _monitor.stop()
            all_resource_metrics[fw_name].peak_ram_mb = peak_ram
            all_resource_metrics[fw_name].avg_cpu_pct = avg_cpu

        if not args.no_isolation:
            stop_service(fw_config["compose_service"])
            if args.prune_images:
                prune_service_image(fw_config["compose_service"])

        if i < len(args.frameworks) - 1:
            print(f"  cooldown {args.cooldown}s...", flush=True)
            time.sleep(args.cooldown)
        print()

    report = format_report(
        all_results, args, date_str,
        resource_metrics=all_resource_metrics if all_resource_metrics else None,
        db_footprint=db_footprint if db_footprint else None,
    )

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
    json_data_out: dict = {"results": json_data}
    if all_resource_metrics:
        json_data_out["resource_metrics"] = [
            {
                "framework": m.fw_name,
                "loc": m.loc,
                "complexity_per_100_loc": m.complexity_per_100_loc,
                "image_mb": round(m.image_mb, 1),
                "peak_ram_mb": round(m.peak_ram_mb, 1),
                "avg_cpu_pct": m.avg_cpu_pct,
            }
            for m in all_resource_metrics.values()
        ]
    if db_footprint:
        json_data_out["db_footprint"] = [
            {
                "table": t.tablename,
                "total_bytes": t.total_bytes,
                "heap_bytes": t.heap_bytes,
                "indexes_bytes": t.indexes_bytes,
            }
            for t in db_footprint
        ]
    json_path.write_text(json.dumps(json_data_out, indent=2))
    print(f"JSON data written to: {json_path}")


if __name__ == "__main__":
    main()
