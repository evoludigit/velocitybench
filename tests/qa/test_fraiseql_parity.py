"""
FraiseQL v_* vs tv_* Parity Tests

Verifies that both FraiseQL variants return identical data for the same query.
Both services must be running:
  docker compose --profile fraiseql up -d

Skip these tests when services are not running (CI without containers).
"""

import json
import urllib.error
import urllib.request

import pytest

V_STAR_URL = "http://localhost:8815/graphql"
TV_STAR_URL = "http://localhost:8816/graphql"

# Queries used throughout — must be valid for both schema variants
Q1 = "{ users(limit: 5) { id identifier username fullName } }"
Q2 = "{ posts(limit: 5) { id identifier title author { username fullName } } }"
Q3 = "{ comments(limit: 5) { id content author { username } post { title } } }"
Q4 = "{ posts(limit: 5, published: true) { id title author { username } } }"


def _graphql(url: str, query: str, timeout: int = 10) -> dict:
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _services_running() -> bool:
    for url in (V_STAR_URL, TV_STAR_URL):
        try:
            _graphql(url, "{ users(limit: 1) { id } }", timeout=3)
        except (urllib.error.URLError, OSError):
            return False
    return True


requires_services = pytest.mark.skipif(
    not _services_running(),
    reason="fraiseql and fraiseql-tv services not running — start with: "
           "docker compose --profile fraiseql up -d",
)


# ---------------------------------------------------------------------------
# Schema alignment: both variants must use camelCase field names
# ---------------------------------------------------------------------------


@requires_services
def test_q1_returns_camelcase_full_name():
    """Both variants must expose fullName (camelCase), not full_name."""
    for label, url in (("v_*", V_STAR_URL), ("tv_*", TV_STAR_URL)):
        result = _graphql(url, Q1)
        assert "errors" not in result or not result["errors"], (
            f"{label} Q1 returned errors: {result.get('errors')}"
        )
        users = result["data"]["users"]
        assert len(users) > 0, f"{label} returned no users"
        assert "fullName" in users[0], (
            f"{label} user missing 'fullName' — got keys: {list(users[0].keys())}"
        )
        assert "full_name" not in users[0], (
            f"{label} user has 'full_name' (snake_case) instead of 'fullName'"
        )


# ---------------------------------------------------------------------------
# Parity: both variants must return the same data for fixture queries
# ---------------------------------------------------------------------------


@requires_services
def test_q1_parity_fixture_users():
    """v_* and tv_* must return identical user data for Q1."""
    r_v = _graphql(V_STAR_URL, Q1)
    r_tv = _graphql(TV_STAR_URL, Q1)

    assert not r_v.get("errors"), f"v_* Q1 error: {r_v.get('errors')}"
    assert not r_tv.get("errors"), f"tv_* Q1 error: {r_tv.get('errors')}"

    users_v = {u["id"]: u for u in r_v["data"]["users"]}
    users_tv = {u["id"]: u for u in r_tv["data"]["users"]}

    assert set(users_v.keys()) == set(users_tv.keys()), (
        f"v_* and tv_* returned different user IDs:\n"
        f"  v_*:  {sorted(users_v.keys())}\n"
        f"  tv_*: {sorted(users_tv.keys())}"
    )
    for uid in users_v:
        assert users_v[uid]["username"] == users_tv[uid]["username"], (
            f"username mismatch for {uid}: "
            f"v_*={users_v[uid]['username']} tv_*={users_tv[uid]['username']}"
        )
        assert users_v[uid]["fullName"] == users_tv[uid]["fullName"], (
            f"fullName mismatch for {uid}: "
            f"v_*={users_v[uid]['fullName']} tv_*={users_tv[uid]['fullName']}"
        )


@requires_services
def test_q2_parity_posts_with_author():
    """v_* and tv_* must return identical post+author data for Q2."""
    r_v = _graphql(V_STAR_URL, Q2)
    r_tv = _graphql(TV_STAR_URL, Q2)

    assert not r_v.get("errors"), f"v_* Q2 error: {r_v.get('errors')}"
    assert not r_tv.get("errors"), f"tv_* Q2 error: {r_tv.get('errors')}"

    posts_v = {p["id"]: p for p in r_v["data"]["posts"]}
    posts_tv = {p["id"]: p for p in r_tv["data"]["posts"]}

    assert set(posts_v.keys()) == set(posts_tv.keys()), (
        "v_* and tv_* returned different post IDs"
    )
    for pid in posts_v:
        assert posts_v[pid]["title"] == posts_tv[pid]["title"], (
            f"post title mismatch for {pid}"
        )
        assert posts_v[pid]["author"]["username"] == posts_tv[pid]["author"]["username"], (
            f"author username mismatch for post {pid}"
        )


@requires_services
def test_q3_parity_comments_with_embeds():
    """v_* and tv_* must return identical comment+author+post data for Q3."""
    r_v = _graphql(V_STAR_URL, Q3)
    r_tv = _graphql(TV_STAR_URL, Q3)

    assert not r_v.get("errors"), f"v_* Q3 error: {r_v.get('errors')}"
    assert not r_tv.get("errors"), f"tv_* Q3 error: {r_tv.get('errors')}"

    comments_v = {c["id"]: c for c in r_v["data"]["comments"]}
    comments_tv = {c["id"]: c for c in r_tv["data"]["comments"]}

    assert set(comments_v.keys()) == set(comments_tv.keys()), (
        "v_* and tv_* returned different comment IDs"
    )
    for cid in comments_v:
        assert comments_v[cid]["author"]["username"] == comments_tv[cid]["author"]["username"], (
            f"author username mismatch for comment {cid}"
        )
        assert comments_v[cid]["post"]["title"] == comments_tv[cid]["post"]["title"], (
            f"post title mismatch for comment {cid}"
        )


@requires_services
def test_q4_parity_filtered_posts():
    """Filtered query (published: true) must return same posts from both variants."""
    r_v = _graphql(V_STAR_URL, Q4)
    r_tv = _graphql(TV_STAR_URL, Q4)

    assert not r_v.get("errors"), f"v_* Q4 error: {r_v.get('errors')}"
    assert not r_tv.get("errors"), f"tv_* Q4 error: {r_tv.get('errors')}"

    ids_v = {p["id"] for p in r_v["data"]["posts"]}
    ids_tv = {p["id"] for p in r_tv["data"]["posts"]}
    assert ids_v == ids_tv, (
        f"Filtered query returned different post IDs:\n  v_*: {ids_v}\n  tv_*: {ids_tv}"
    )


@requires_services
def test_alice_appears_in_users():
    """The fixture user 'alice' must appear in both variants' user list."""
    for label, url in (("v_*", V_STAR_URL), ("tv_*", TV_STAR_URL)):
        result = _graphql(url, "{ users(limit: 20) { username } }")
        usernames = [u["username"] for u in result["data"]["users"]]
        assert "alice" in usernames, (
            f"{label} users query missing fixture user 'alice'. Got: {usernames}"
        )
