"""
Cross-Framework Parity Tests

Verifies that all 8 benchmark frameworks return identical data for the same queries.
Without parity, a faster benchmark result may reflect fewer fields returned, different
pagination, or silently omitted nested data — not faster execution.

Parity is anchored on fixture users (alice through eve, UUIDs starting with 11...1
through 55...5) inserted deterministically by the schema init scripts.

Prerequisites:
    docker compose --profile benchmark up -d
    # wait ~60s for containers

Run:
    pytest tests/qa/test_parity.py -v
"""

import json
import urllib.error
import urllib.request

import pytest

# ---------------------------------------------------------------------------
# Endpoint registry
# ---------------------------------------------------------------------------

GRAPHQL_ENDPOINTS: dict[str, str] = {
    "strawberry":    "http://localhost:8011/graphql",
    "graphene":      "http://localhost:8002/graphql",
    "go-gqlgen":     "http://localhost:4010/query",
    "async-graphql": "http://localhost:8016/",
    "fraiseql-v":    "http://localhost:8815/graphql",
    "fraiseql-tv":   "http://localhost:8816/graphql",
}

REST_ENDPOINTS: dict[str, str] = {
    "fastapi-rest":   "http://localhost:8003",
    "actix-web-rest": "http://localhost:8015",
}

# ---------------------------------------------------------------------------
# Fixture constants (deterministic from fraiseql_cqrs_schema.sql)
# ---------------------------------------------------------------------------

ALICE_UUID     = "11111111-1111-1111-1111-111111111111"
ALICE_USERNAME = "alice"
ALICE_FULLNAME = "Alice Johnson"

FIXTURE_USERNAMES = {"alice", "bob", "carol", "dave", "eve"}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _post_graphql(url: str, query: str, timeout: int = 10) -> dict:
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _get(url: str, timeout: int = 10) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


# ---------------------------------------------------------------------------
# Service availability checks (evaluated once at collection time)
# ---------------------------------------------------------------------------


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


def _rest_services_running() -> bool:
    """Return True only if REST services are up AND connected to the benchmark database."""
    for base in REST_ENDPOINTS.values():
        try:
            # Check health first
            with urllib.request.urlopen(f"{base}/health", timeout=3):
                pass
            # Then verify benchmark fixtures are present (alice must exist)
            with urllib.request.urlopen(
                f"{base}/users/{ALICE_UUID}", timeout=3
            ) as resp:
                body = json.loads(resp.read())
                if body.get("username") != "alice":
                    return False
        except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
            return False
    return True


requires_graphql = pytest.mark.skipif(
    not _graphql_services_running(),
    reason="GraphQL frameworks not running — start with: "
           "docker compose --profile benchmark up -d",
)

requires_rest = pytest.mark.skipif(
    not _rest_services_running(),
    reason="REST frameworks not running — start with: "
           "docker compose --profile benchmark up -d",
)

# ---------------------------------------------------------------------------
# Helpers to extract data from GraphQL responses
# ---------------------------------------------------------------------------


def _gql_data(framework: str, url: str, query: str) -> dict:
    result = _post_graphql(url, query)
    assert "errors" not in result or not result["errors"], (
        f"{framework} returned GraphQL errors: {result.get('errors')}"
    )
    assert "data" in result, f"{framework} response missing 'data' key"
    return result["data"]


# ---------------------------------------------------------------------------
# Cycle 2 — GraphQL field contract
#
# Every GraphQL framework must expose camelCase field names.
# Strawberry and graphene convert Python snake_case to camelCase automatically.
# ---------------------------------------------------------------------------


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_users_return_camelcase_full_name(framework: str, url: str) -> None:
    """Every GraphQL framework must expose `fullName` (camelCase), not `full_name`."""
    data = _gql_data(framework, url, "{ users(limit: 5) { id username fullName } }")
    users = data["users"]
    assert len(users) > 0, f"{framework} returned no users"
    assert "fullName" in users[0], (
        f"{framework} user missing 'fullName' — got keys: {list(users[0].keys())}"
    )
    assert "full_name" not in users[0], (
        f"{framework} returned 'full_name' (snake_case) instead of 'fullName'"
    )


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_users_limit_returns_correct_count(framework: str, url: str) -> None:
    """users(limit: 5) must return exactly 5 users."""
    data = _gql_data(framework, url, "{ users(limit: 5) { id username fullName } }")
    assert len(data["users"]) == 5, (
        f"{framework}: expected 5 users, got {len(data['users'])}"
    )


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_fixture_alice_present(framework: str, url: str) -> None:
    """Fixture user 'alice' must appear in users(limit: 20) for every framework."""
    data = _gql_data(framework, url, "{ users(limit: 20) { id username fullName } }")
    usernames = {u["username"] for u in data["users"]}
    assert "alice" in usernames, (
        f"{framework}: fixture user 'alice' not found. Got: {sorted(usernames)}"
    )


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_alice_full_name_correct(framework: str, url: str) -> None:
    """Alice's fullName must be 'Alice Johnson' — deterministic from fixtures."""
    data = _gql_data(framework, url, "{ users(limit: 20) { id username fullName } }")
    alice = next((u for u in data["users"] if u["username"] == "alice"), None)
    assert alice is not None, f"{framework}: alice not found in users(limit: 20)"
    assert alice["fullName"] == ALICE_FULLNAME, (
        f"{framework}: alice fullName='{alice['fullName']}' expected '{ALICE_FULLNAME}'"
    )


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_alice_uuid_correct(framework: str, url: str) -> None:
    """Alice's UUID must match the fixture value (11111111-...-111111111111)."""
    data = _gql_data(framework, url, "{ users(limit: 20) { id username } }")
    alice = next((u for u in data["users"] if u["username"] == "alice"), None)
    assert alice is not None, f"{framework}: alice not found"
    assert alice["id"] == ALICE_UUID, (
        f"{framework}: alice id='{alice['id']}' expected '{ALICE_UUID}'"
    )


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_post_has_nested_author(framework: str, url: str) -> None:
    """posts(limit: 1) must include a nested author with username and fullName."""
    data = _gql_data(
        framework, url,
        "{ posts(limit: 1) { id title author { username fullName } } }",
    )
    posts = data["posts"]
    assert len(posts) >= 1, f"{framework}: no posts returned"
    post = posts[0]
    assert "author" in post, f"{framework}: post missing 'author' field"
    assert post["author"].get("username"), (
        f"{framework}: author username is empty or missing"
    )
    assert post["author"].get("fullName") is not None, (
        f"{framework}: author fullName is null or missing"
    )


# ---------------------------------------------------------------------------
# Cycle 2 — Cross-framework ID consistency
# ---------------------------------------------------------------------------


@requires_graphql
def test_graphql_same_user_ids_across_frameworks() -> None:
    """
    users(limit: 5) must return the same set of user IDs across all GraphQL frameworks.

    A mismatch indicates that a framework is using different seed data, a different
    database, or has pagination/ordering that surfaces different rows.
    """
    id_sets: dict[str, set[str]] = {}
    for name, url in GRAPHQL_ENDPOINTS.items():
        data = _gql_data(name, url, "{ users(limit: 5) { id username } }")
        id_sets[name] = {u["id"] for u in data["users"]}

    reference_name = next(iter(id_sets))
    reference_ids = id_sets[reference_name]

    for name, ids in id_sets.items():
        assert ids == reference_ids, (
            f"{name} returned different user IDs than {reference_name}.\n"
            f"  Missing: {reference_ids - ids}\n"
            f"  Extra: {ids - reference_ids}"
        )


@requires_graphql
def test_graphql_all_fixture_users_present() -> None:
    """
    All 5 fixture users (alice, bob, carol, dave, eve) must appear in every framework.

    Checks that seed data is identical across frameworks (same database, same fixtures).
    """
    query = "{ users(limit: 20) { username } }"
    for name, url in GRAPHQL_ENDPOINTS.items():
        data = _gql_data(name, url, query)
        usernames = {u["username"] for u in data["users"]}
        missing = FIXTURE_USERNAMES - usernames
        assert not missing, (
            f"{name}: fixture users missing from users(limit: 20): {missing}"
        )


@requires_graphql
def test_graphql_alice_data_consistent_across_frameworks() -> None:
    """
    Alice's id, username, and fullName must be identical across all GraphQL frameworks.
    """
    query = "{ users(limit: 20) { id username fullName } }"
    alice_records: dict[str, dict] = {}
    for name, url in GRAPHQL_ENDPOINTS.items():
        data = _gql_data(name, url, query)
        alice = next((u for u in data["users"] if u["username"] == "alice"), None)
        assert alice is not None, f"{name}: alice not found"
        alice_records[name] = alice

    reference_name = next(iter(alice_records))
    ref = alice_records[reference_name]

    for name, record in alice_records.items():
        assert record["id"] == ref["id"], (
            f"{name} alice.id='{record['id']}' != {reference_name} alice.id='{ref['id']}'"
        )
        assert record["fullName"] == ref["fullName"], (
            f"{name} alice.fullName='{record['fullName']}' "
            f"!= {reference_name} alice.fullName='{ref['fullName']}'"
        )


# ---------------------------------------------------------------------------
# Cycle 3 — REST framework parity
# ---------------------------------------------------------------------------


@requires_rest
@pytest.mark.parametrize("framework,base", list(REST_ENDPOINTS.items()))
def test_rest_users_list_returns_five(framework: str, base: str) -> None:
    """GET /users?limit=5 must return 5 users."""
    status, body = _get(f"{base}/users?limit=5")
    assert status == 200, f"{framework}: GET /users?limit=5 returned HTTP {status}"
    data = json.loads(body)
    users = data.get("users", data) if isinstance(data, dict) else data
    assert len(users) == 5, f"{framework}: expected 5 users, got {len(users)}"


@requires_rest
@pytest.mark.parametrize("framework,base", list(REST_ENDPOINTS.items()))
def test_rest_alice_by_uuid(framework: str, base: str) -> None:
    """GET /users/{alice_uuid} must return alice with correct data."""
    status, body = _get(f"{base}/users/{ALICE_UUID}")
    assert status == 200, (
        f"{framework}: GET /users/{ALICE_UUID} returned HTTP {status}"
    )
    user = json.loads(body)
    assert user.get("username") == ALICE_USERNAME, (
        f"{framework}: expected username='alice', got: {user.get('username')}"
    )
    # REST frameworks may use snake_case (full_name) or camelCase (fullName)
    full_name = user.get("fullName") or user.get("full_name")
    assert full_name == ALICE_FULLNAME, (
        f"{framework}: expected fullName/full_name='{ALICE_FULLNAME}', got: {full_name}"
    )


@requires_rest
def test_rest_alice_same_uuid_across_frameworks() -> None:
    """Alice's UUID must be identical across REST frameworks."""
    uuids: dict[str, str] = {}
    for name, base in REST_ENDPOINTS.items():
        status, body = _get(f"{base}/users?limit=20")
        assert status == 200, f"{name}: GET /users returned HTTP {status}"
        data = json.loads(body)
        users = data.get("users", data) if isinstance(data, dict) else data
        alice = next((u for u in users if u.get("username") == "alice"), None)
        assert alice is not None, f"{name}: alice not found in /users?limit=20"
        uuids[name] = alice["id"]

    reference_name = next(iter(uuids))
    ref_uuid = uuids[reference_name]
    for name, uuid in uuids.items():
        assert uuid == ref_uuid, (
            f"{name} alice.id='{uuid}' != {reference_name} alice.id='{ref_uuid}'"
        )


# ---------------------------------------------------------------------------
# Cycle 4 — Schema consistency sanity checks
# ---------------------------------------------------------------------------


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_users_have_required_fields(framework: str, url: str) -> None:
    """Every user object must contain id, username, and fullName."""
    data = _gql_data(framework, url, "{ users(limit: 5) { id username fullName } }")
    for user in data["users"]:
        assert "id" in user and user["id"], (
            f"{framework}: user missing 'id': {user}"
        )
        assert "username" in user and user["username"], (
            f"{framework}: user missing 'username': {user}"
        )
        assert "fullName" in user, (
            f"{framework}: user missing 'fullName': {user}"
        )


@requires_graphql
@pytest.mark.parametrize("framework,url", list(GRAPHQL_ENDPOINTS.items()))
def test_graphql_post_ids_are_uuids(framework: str, url: str) -> None:
    """Post IDs must be UUID strings (lowercase hex with hyphens)."""
    import re
    uuid_re = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    data = _gql_data(framework, url, "{ posts(limit: 5) { id title } }")
    for post in data["posts"]:
        assert uuid_re.match(post["id"]), (
            f"{framework}: post id '{post['id']}' is not a lowercase UUID"
        )
