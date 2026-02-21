"""
FraiseQL v_* vs tv_* Drop Analysis Tests

Validates the core CQRS architectural claim:
  tv_* pre-computation eliminates nesting overhead → Q1→Q3 drop < 10%
  v_*  computes JSONB at query time         → Q1→Q3 drop >= tv_* drop

Both services must be running:
    docker compose --profile fraiseql up -d

These tests are slower (each runs a 15-second benchmark sub-window).
Mark them with -m slow to exclude from fast test runs.
"""

import json
import threading
import time
import urllib.error
import urllib.request

import pytest

V_STAR_URL = "http://localhost:8815/graphql"
TV_STAR_URL = "http://localhost:8816/graphql"

# Q1: flat — no embedded objects
Q1 = "{ users(limit: 20) { id username fullName } }"
# Q3: deep — 2 embedded objects (author + post)
Q3 = "{ comments(limit: 20) { id content author { username } post { title } } }"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _services_running() -> bool:
    for url in (V_STAR_URL, TV_STAR_URL):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps({"query": "{ users(limit: 1) { id } }"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3):
                pass
        except (urllib.error.URLError, OSError):
            return False
    return True


requires_services = pytest.mark.skipif(
    not _services_running(),
    reason="fraiseql services not running — start with: "
           "docker compose --profile fraiseql up -d",
)


def get_rps(url: str, query: str, duration: int = 15, concurrency: int = 20) -> float:
    """
    Measure requests-per-second for a GraphQL endpoint over `duration` seconds
    using `concurrency` parallel worker threads.
    """
    counts: list[int] = [0] * concurrency
    end_time = time.monotonic() + duration
    payload = json.dumps({"query": query}).encode()

    def worker(idx: int) -> None:
        req_template = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        while time.monotonic() < end_time:
            try:
                with urllib.request.urlopen(req_template, timeout=10) as resp:
                    body = json.loads(resp.read())
                    if resp.status == 200 and "data" in body:
                        counts[idx] += 1
            except (urllib.error.URLError, OSError, json.JSONDecodeError):
                pass

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return sum(counts) / duration


# ---------------------------------------------------------------------------
# Warm-up fixture — run once per session to prime both services
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def warmup_services():
    """Fire a quick warmup burst before any comparison test."""
    if not _services_running():
        return
    for url in (V_STAR_URL, TV_STAR_URL):
        get_rps(url, Q1, duration=5, concurrency=10)
        get_rps(url, Q3, duration=5, concurrency=10)


# ---------------------------------------------------------------------------
# Assertion tests
# ---------------------------------------------------------------------------


@requires_services
@pytest.mark.slow
def test_tv_star_q1_q3_drop_within_threshold():
    """
    tv_* variant: Q1→Q3 throughput drop must be < 15%.

    Hypothesis: pre-computed JSONB makes nesting depth irrelevant.
    A > 15% drop suggests the tv_* sync is incomplete or the server
    is falling back to join-based resolution for nested fields.
    """
    rps_q1 = get_rps(TV_STAR_URL, Q1)
    rps_q3 = get_rps(TV_STAR_URL, Q3)

    assert rps_q1 > 0, "tv_* Q1 returned 0 RPS — service may be down"
    assert rps_q3 > 0, "tv_* Q3 returned 0 RPS — service may be down"

    drop_pct = (rps_q1 - rps_q3) / rps_q1 * 100
    assert drop_pct < 15, (
        f"tv_* Q1→Q3 drop too large: {drop_pct:.1f}% (threshold: 15%)\n"
        f"  Q1 (flat):  {rps_q1:.1f} RPS\n"
        f"  Q3 (2-embed): {rps_q3:.1f} RPS\n"
        "Check that fn_sync_tv_comment populates author and post embeddings."
    )


@requires_services
@pytest.mark.slow
def test_tv_star_q3_not_slower_than_v_star():
    """
    tv_* Q3 must not be slower than v_* Q3.

    tv_* reads pre-baked JSONB; v_* assembles JSONB at query time with joins.
    If tv_* is slower, the sync functions are not producing the right data
    or the GIN indexes are hurting read performance.
    """
    rps_v  = get_rps(V_STAR_URL,  Q3)
    rps_tv = get_rps(TV_STAR_URL, Q3)

    assert rps_tv >= rps_v * 0.9, (
        f"tv_* Q3 ({rps_tv:.1f} RPS) is more than 10% slower than "
        f"v_* Q3 ({rps_v:.1f} RPS) — pre-computation not helping"
    )


@requires_services
@pytest.mark.slow
def test_v_star_q1_q3_drop_exceeds_tv_star():
    """
    v_* Q1→Q3 drop must be >= tv_* Q1→Q3 drop.

    v_* computes JSONB at query time (runtime JOIN overhead).
    tv_* pre-bakes JSONB (no JOIN overhead).
    v_* drop should therefore be larger.
    """
    rps_v_q1  = get_rps(V_STAR_URL,  Q1)
    rps_v_q3  = get_rps(V_STAR_URL,  Q3)
    rps_tv_q1 = get_rps(TV_STAR_URL, Q1)
    rps_tv_q3 = get_rps(TV_STAR_URL, Q3)

    drop_v  = (rps_v_q1  - rps_v_q3)  / rps_v_q1  * 100 if rps_v_q1  > 0 else 0
    drop_tv = (rps_tv_q1 - rps_tv_q3) / rps_tv_q1 * 100 if rps_tv_q1 > 0 else 0

    assert drop_v >= drop_tv, (
        f"Expected v_* drop ({drop_v:.1f}%) >= tv_* drop ({drop_tv:.1f}%).\n"
        f"CQRS nesting-overhead hypothesis not confirmed.\n"
        f"  v_*  Q1: {rps_v_q1:.1f} RPS  Q3: {rps_v_q3:.1f} RPS  drop: {drop_v:.1f}%\n"
        f"  tv_* Q1: {rps_tv_q1:.1f} RPS  Q3: {rps_tv_q3:.1f} RPS  drop: {drop_tv:.1f}%"
    )
