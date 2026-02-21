"""
N+1 Query Guard

Detects N+1 query regressions by counting SQL statements executed against the
benchmark schema during a single GraphQL request.

Strategy (Option A — pg_stat_statements delta):
  1. Reset pg_stat_statements for the benchmark schema.
  2. Execute exactly one GraphQL request.
  3. Count the sum(calls) for queries touching the benchmark schema.
  4. Assert the count is ≤ the DataLoader threshold (typically 2–3 queries).

A DataLoader-based framework executing posts(limit:20) { author { username } }
should emit exactly 2 queries:
  SELECT … FROM benchmark.tv_post  (or tb_post / v_post) LIMIT 20
  SELECT … FROM benchmark.tb_user  WHERE pk_user = ANY($1)   -- batched

An N+1 framework would emit 21 queries (1 posts + 1 per author).

Limitations:
- pg_stat_statements counts globally across all connections. These tests must
  run serially (no concurrent benchmark traffic) to be reliable.
- Connection pool setup/teardown queries add ~1–2 extra calls. Thresholds are
  set conservatively (≤ 5 for DataLoader patterns).
- FraiseQL tv_* pre-computes JSONB: only 1 query regardless of nesting depth.

Prerequisites:
    docker compose --profile benchmark up -d
    # wait ~60s for containers

Run:
    pytest tests/qa/test_n1_detection.py -v -p no:randomly
"""

import json
import time
import urllib.error
import urllib.request

import pytest

try:
    import psycopg2
    _psycopg2_available = True
except ImportError:
    _psycopg2_available = False

# ---------------------------------------------------------------------------
# Endpoint registry (same as test_parity.py)
# ---------------------------------------------------------------------------

GRAPHQL_ENDPOINTS: dict[str, str] = {
    "strawberry":    "http://localhost:8011/graphql",
    "graphene":      "http://localhost:8002/graphql",
    "go-gqlgen":     "http://localhost:4010/query",
    "async-graphql": "http://localhost:8016/",
    "fraiseql-v":    "http://localhost:8815/graphql",
    "fraiseql-tv":   "http://localhost:8816/graphql",
}

DB_CONFIG = dict(
    host="localhost",
    port=5434,
    dbname="velocitybench_benchmark",
    user="benchmark",
    password="benchmark123",
)

# ---------------------------------------------------------------------------
# N+1 thresholds: maximum acceptable SQL calls per GraphQL request.
# These are intentionally generous (+2) to absorb connection-pool overhead.
# DataLoader frameworks should emit exactly 1–2 benchmark queries per request.
# N+1 for 20 items would be 21, which will always exceed these limits.
# ---------------------------------------------------------------------------

N1_THRESHOLDS: dict[str, int] = {
    # posts(limit:20) { author { username } }
    # DataLoader: 1 posts query + 1 batched-author query = 2
    "posts_with_author":     5,
    # users(limit:10) { posts(limit:5) { id title } }
    # DataLoader: 1 users query + 1 batched-posts query = 2
    "users_with_posts":      5,
    # comments(limit:20) { author { username } post { title } }
    # DataLoader: 1 comments + 1 batched authors + 1 batched posts = 3
    # FraiseQL tv_*: 1 (all in JSONB)
    "comments_deep":         6,
}

# FraiseQL tv_* should emit ≤ 1 benchmark query (JSONB pre-computed)
FRAISEQL_TV_THRESHOLD = 2  # allow 1 overhead

# ---------------------------------------------------------------------------
# GraphQL queries
# ---------------------------------------------------------------------------

QUERIES: dict[str, str] = {
    "posts_with_author": (
        "{ posts(limit: 20) { id title author { username fullName } } }"
    ),
    "users_with_posts": (
        "{ users(limit: 10) { id username posts(limit: 5) { id title } } }"
    ),
    "comments_deep": (
        "{ comments(limit: 20) { id content author { username } post { title } } }"
    ),
}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _post_graphql(url: str, query: str, timeout: int = 15) -> dict:
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Service / database availability checks
# ---------------------------------------------------------------------------


def _pg_stat_statements_available() -> bool:
    if not _psycopg2_available:
        return False
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements'"
            )
            available = cur.fetchone()[0] > 0
        conn.close()
        return available
    except Exception:
        return False


def _graphql_services_running() -> bool:
    probe = json.dumps({"query": "{ users(limit: 1) { id } }"}).encode()
    for url in GRAPHQL_ENDPOINTS.values():
        try:
            req = urllib.request.Request(
                url,
                data=probe,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3):
                pass
        except (urllib.error.URLError, OSError):
            return False
    return True


requires_services = pytest.mark.skipif(
    not (_graphql_services_running() and _pg_stat_statements_available()),
    reason="GraphQL services or pg_stat_statements not available — "
           "start with: docker compose --profile benchmark up -d",
)

# ---------------------------------------------------------------------------
# Database fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pg_conn():
    if not _psycopg2_available:
        pytest.skip("psycopg2 not installed — run: pip install psycopg2-binary")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# pg_stat_statements helpers
# ---------------------------------------------------------------------------


def _reset_stats(pg_conn) -> None:
    """Reset pg_stat_statements counters (requires pg_stat_statements.track=all)."""
    with pg_conn.cursor() as cur:
        cur.execute("SELECT pg_stat_statements_reset()")


def _count_benchmark_queries(pg_conn) -> int:
    """
    Count total SQL call executions against the benchmark schema since last reset.

    Filters to queries that reference 'benchmark.' to exclude internal PostgreSQL
    catalog queries (autovacuum, pg_stat, etc.).
    """
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(SUM(calls), 0)
            FROM pg_stat_statements
            WHERE query ILIKE '%benchmark.%'
              AND query NOT ILIKE '%pg_stat%'
        """)
        row = cur.fetchone()
        return int(row[0]) if row else 0


def _measure_query_count(
    pg_conn,
    url: str,
    query: str,
    warmup_first: bool = True,
) -> tuple[int, dict]:
    """
    Measure how many benchmark SQL queries are executed for one GraphQL request.

    If warmup_first is True, fires one request before measuring to avoid
    counting connection pool initialisation queries.

    Returns (query_count, graphql_response).
    """
    if warmup_first:
        try:
            _post_graphql(url, query)
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.05)  # let pool settle

    _reset_stats(pg_conn)
    time.sleep(0.02)  # brief pause so reset propagates

    response = _post_graphql(url, query)

    # Small sleep to let async handlers flush their query completion
    time.sleep(0.05)

    count = _count_benchmark_queries(pg_conn)
    return count, response


# ---------------------------------------------------------------------------
# Cycle 1 — Basic pg_stat_statements sanity
# ---------------------------------------------------------------------------


@requires_services
def test_pg_stat_statements_is_enabled(pg_conn) -> None:
    """pg_stat_statements extension must be active in the benchmark database."""
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements'"
        )
        count = cur.fetchone()[0]
    assert count == 1, (
        "pg_stat_statements extension not found — "
        "check docker-compose postgres shared_preload_libraries setting"
    )


@requires_services
def test_flat_query_emits_exactly_one_benchmark_query(pg_conn) -> None:
    """
    users(limit: 5) { id username } — flat, no nesting.
    Any framework should emit exactly 1 benchmark query.
    """
    url = GRAPHQL_ENDPOINTS["fraiseql-tv"]  # most predictable: pure JSONB read
    count, response = _measure_query_count(
        pg_conn,
        url,
        "{ users(limit: 5) { id username } }",
    )
    assert "errors" not in response or not response["errors"], (
        f"fraiseql-tv returned GraphQL errors: {response.get('errors')}"
    )
    # 1 benchmark query + possible overhead from stats tracking (allow ≤ 3)
    assert count <= 3, (
        f"Flat users query emitted {count} benchmark SQL calls (expected ≤ 3). "
        "This may indicate connection pool overhead or pg_stat_statements noise."
    )


# ---------------------------------------------------------------------------
# Cycle 2 — N+1 guard for DataLoader frameworks
# ---------------------------------------------------------------------------


@requires_services
@pytest.mark.parametrize("framework,url", [
    ("strawberry",    GRAPHQL_ENDPOINTS["strawberry"]),
    ("graphene",      GRAPHQL_ENDPOINTS["graphene"]),
    ("go-gqlgen",     GRAPHQL_ENDPOINTS["go-gqlgen"]),
    ("async-graphql", GRAPHQL_ENDPOINTS["async-graphql"]),
])
def test_posts_with_author_uses_dataloader(framework: str, url: str, pg_conn) -> None:
    """
    posts(limit:20) { author { username } } must use ≤ 5 benchmark SQL calls.

    A DataLoader implementation issues 2 queries (posts + batched authors).
    An N+1 implementation issues 21 queries (posts + 1 per author).
    The threshold of 5 comfortably separates these two cases.
    """
    threshold = N1_THRESHOLDS["posts_with_author"]
    count, response = _measure_query_count(pg_conn, url, QUERIES["posts_with_author"])

    assert "errors" not in response or not response["errors"], (
        f"{framework}: GraphQL errors on posts+author query: {response.get('errors')}"
    )
    assert "data" in response and response["data"]["posts"], (
        f"{framework}: No posts returned — cannot validate N+1 behaviour"
    )

    n_items = len(response["data"]["posts"])
    assert count <= threshold, (
        f"{framework}: posts+author query executed {count} benchmark SQL calls "
        f"(threshold: {threshold}, items fetched: {n_items}). "
        f"This exceeds the DataLoader threshold — check your author resolver "
        f"for missing DataLoader / batching. "
        f"N+1 pattern would emit {n_items + 1} calls."
    )


@requires_services
@pytest.mark.parametrize("framework,url", [
    ("strawberry",    GRAPHQL_ENDPOINTS["strawberry"]),
    ("graphene",      GRAPHQL_ENDPOINTS["graphene"]),
    ("go-gqlgen",     GRAPHQL_ENDPOINTS["go-gqlgen"]),
    ("async-graphql", GRAPHQL_ENDPOINTS["async-graphql"]),
])
def test_users_with_posts_uses_dataloader(framework: str, url: str, pg_conn) -> None:
    """
    users(limit:10) { posts(limit:5) { id title } } must use ≤ 5 SQL calls.

    DataLoader: 1 users query + 1 batched posts query = 2 total.
    N+1: 1 users query + 10 individual posts queries = 11 total.
    """
    threshold = N1_THRESHOLDS["users_with_posts"]
    count, response = _measure_query_count(pg_conn, url, QUERIES["users_with_posts"])

    assert "errors" not in response or not response["errors"], (
        f"{framework}: GraphQL errors on users+posts query: {response.get('errors')}"
    )
    assert "data" in response, f"{framework}: Response missing 'data' key"

    n_items = len(response["data"].get("users", []))
    assert count <= threshold, (
        f"{framework}: users+posts query executed {count} benchmark SQL calls "
        f"(threshold: {threshold}, items fetched: {n_items}). "
        f"Check posts resolver for DataLoader usage."
    )


# ---------------------------------------------------------------------------
# Cycle 2 — FraiseQL tv_* specific: must emit exactly 1 query
# ---------------------------------------------------------------------------


@requires_services
def test_fraiseql_tv_posts_with_author_single_query(pg_conn) -> None:
    """
    FraiseQL tv_* pre-computes JSONB at INSERT time.
    posts(limit:20) { author { username } } must use ≤ 2 benchmark SQL calls
    (1 SELECT from tv_post, plus possible overhead).
    """
    url = GRAPHQL_ENDPOINTS["fraiseql-tv"]
    count, response = _measure_query_count(pg_conn, url, QUERIES["posts_with_author"])

    assert "errors" not in response or not response["errors"], (
        f"fraiseql-tv: GraphQL errors: {response.get('errors')}"
    )
    assert count <= FRAISEQL_TV_THRESHOLD, (
        f"fraiseql-tv: posts+author issued {count} SQL calls "
        f"(threshold: {FRAISEQL_TV_THRESHOLD}). "
        f"Pre-computed JSONB should require only 1 SELECT from tv_post."
    )


@requires_services
def test_fraiseql_tv_deep_query_single_query(pg_conn) -> None:
    """
    FraiseQL tv_* must use ≤ 2 SQL calls even for the deepest nesting
    (comments + author + post — all embedded in tv_comment JSONB).
    """
    url = GRAPHQL_ENDPOINTS["fraiseql-tv"]
    count, response = _measure_query_count(pg_conn, url, QUERIES["comments_deep"])

    assert "errors" not in response or not response["errors"], (
        f"fraiseql-tv: GraphQL errors on deep query: {response.get('errors')}"
    )
    assert count <= FRAISEQL_TV_THRESHOLD, (
        f"fraiseql-tv: deep query (comments+author+post) issued {count} SQL calls "
        f"(threshold: {FRAISEQL_TV_THRESHOLD}). "
        f"All fields should be embedded in tv_comment JSONB."
    )


# ---------------------------------------------------------------------------
# Cycle 3 — Regression tests for 3 core N+1 patterns
# ---------------------------------------------------------------------------


@requires_services
@pytest.mark.parametrize("framework,url", [
    ("strawberry",    GRAPHQL_ENDPOINTS["strawberry"]),
    ("graphene",      GRAPHQL_ENDPOINTS["graphene"]),
    ("go-gqlgen",     GRAPHQL_ENDPOINTS["go-gqlgen"]),
    ("async-graphql", GRAPHQL_ENDPOINTS["async-graphql"]),
    ("fraiseql-v",    GRAPHQL_ENDPOINTS["fraiseql-v"]),
])
def test_comments_deep_nesting_no_n1(framework: str, url: str, pg_conn) -> None:
    """
    comments(limit:20) { author { username } post { title } } must not trigger N+1.

    DataLoader: 1 comments + 1 batched authors + 1 batched posts = 3 queries.
    N+1: 1 + 20 + 20 = 41 queries.
    Threshold: 6 (generous allowance for overhead, far below 41).
    """
    threshold = N1_THRESHOLDS["comments_deep"]
    count, response = _measure_query_count(pg_conn, url, QUERIES["comments_deep"])

    assert "errors" not in response or not response["errors"], (
        f"{framework}: GraphQL errors on deep comments query: {response.get('errors')}"
    )
    assert "data" in response, f"{framework}: Response missing 'data' key"

    n_items = len(response["data"].get("comments", []))
    assert count <= threshold, (
        f"{framework}: comments+author+post query executed {count} SQL calls "
        f"(threshold: {threshold}, items: {n_items}). "
        f"N+1 pattern for 20 comments would issue ~{20*2+1} queries."
    )
