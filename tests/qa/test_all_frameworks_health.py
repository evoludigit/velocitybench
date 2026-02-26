"""
Health check smoke tests

Verifies all 8 benchmark frameworks are reachable and healthy.

Prerequisites:
    docker compose --profile benchmark up -d
    # wait ~60s for all containers to start

Run:
    make smoke-test
    # or directly:
    DATA_VOLUME=xs docker compose --profile benchmark up -d
    sleep 60
    pytest tests/qa/test_all_frameworks_health.py -v
"""

import pytest
import urllib.request
import urllib.error
import json

# ---------------------------------------------------------------------------
# Framework registry — all 8 benchmark targets
# ---------------------------------------------------------------------------

FRAMEWORKS = [
    ("fastapi-rest",   "http://localhost:8003/health",   "rest"),
    ("strawberry",     "http://localhost:8011/health",   "graphql"),
    ("graphene",       "http://localhost:8002/health",   "graphql"),
    ("go-gqlgen",      "http://localhost:4010/health",   "graphql"),
    ("actix-web-rest", "http://localhost:8015/health",   "rest"),
    ("async-graphql",  "http://localhost:8016/health",   "graphql"),
    ("fraiseql-v",     "http://localhost:8815/health",   "graphql"),
    ("fraiseql-tv",    "http://localhost:8816/health",   "graphql"),
]

GRAPHQL_ENDPOINTS = {
    "strawberry":     "http://localhost:8011/graphql",
    "graphene":       "http://localhost:8002/graphql",
    "go-gqlgen":      "http://localhost:4010/query",
    "async-graphql":  "http://localhost:8016/",
    "fraiseql-v":     "http://localhost:8815/graphql",
    "fraiseql-tv":    "http://localhost:8816/graphql",
}

REST_ENDPOINTS = {
    "fastapi-rest":   "http://localhost:8003",
    "actix-web-rest": "http://localhost:8015",
}


def _get(url: str, timeout: int = 5) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, OSError) as e:
        pytest.fail(f"Connection failed to {url}: {e}")


def _post_graphql(url: str, query: str, timeout: int = 10) -> dict:
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError) as e:
        pytest.fail(f"GraphQL request failed to {url}: {e}")


# ---------------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,url,kind", FRAMEWORKS, ids=[f[0] for f in FRAMEWORKS])
def test_health_returns_200(name, url, kind):
    """Every benchmark framework must return HTTP 200 from /health."""
    status, _ = _get(url)
    assert status == 200, f"{name} health check returned {status}"


@pytest.mark.parametrize("name,url,kind", FRAMEWORKS, ids=[f[0] for f in FRAMEWORKS])
def test_health_response_is_not_empty(name, url, kind):
    """Health response body must not be empty."""
    _, body = _get(url)
    assert len(body) > 0, f"{name} returned empty health response body"


# ---------------------------------------------------------------------------
# GraphQL basic query test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,endpoint",
    GRAPHQL_ENDPOINTS.items(),
    ids=list(GRAPHQL_ENDPOINTS.keys()),
)
def test_graphql_users_query(name, endpoint):
    """GraphQL frameworks must respond to a users(limit:5) query."""
    result = _post_graphql(endpoint, "{ users(limit: 5) { id username } }")
    assert "errors" not in result or result["errors"] is None, (
        f"{name} returned GraphQL errors: {result.get('errors')}"
    )
    assert "data" in result, f"{name} response missing 'data' key"
    assert result["data"] is not None, f"{name} returned null data"
    users = result["data"].get("users", [])
    assert len(users) > 0, f"{name} returned 0 users"


# ---------------------------------------------------------------------------
# REST basic query test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,base",
    REST_ENDPOINTS.items(),
    ids=list(REST_ENDPOINTS.keys()),
)
def test_rest_users_endpoint(name, base):
    """REST frameworks must return users from /users?limit=5."""
    status, body = _get(f"{base}/users?limit=5")
    assert status == 200, f"{name} /users returned {status}"
    data = json.loads(body)
    assert isinstance(data, list) or isinstance(data, dict), (
        f"{name} /users returned unexpected type"
    )
