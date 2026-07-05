"""Scenario parity audit — schema-to-API engines vs the FraiseQL reference.

Parity means equivalent *work*, not byte-identical JSON: for every read
scenario, each audited engine must return the same entity count and an
equivalent field set (same rows/joins/fields) as FraiseQL's document. The
audit runs one request per (framework, scenario) and fails loudly on any
mismatch, so a config regression can never silently produce incomparable
numbers.

Naming differences are normalized through per-engine alias maps (e.g.
PostGraphile's `tbUserByFkAuthor` → `author`); anything left over after
normalization is a genuine parity break.

Used two ways:
- pytest: tests/benchmark/test_scenario_parity.py (skips when services are down)
- pre-sweep gate: bench_sequential.py runs it before measuring an audited engine
"""

import json
import urllib.error
import urllib.request

import bench_sequential as bench

REFERENCE = "fraiseql-tv"
AUDITED = ("hasura", "postgraphile")

# Read scenarios under audit. Mutations (M1/MC1) are deliberately excluded:
# their cross-engine definition is workflow-based (see _QUERY_LABELS["MC1"])
# and their response shape is engine-native by design.
SCENARIOS = ("Q1", "Q2", "Q2b", "Q3", "F1", "F2", "F3", "T1")

EXPECTED_COUNTS = {
    "Q1": 20,
    "Q2": 10,
    "Q2b": 10,
    "Q3": 20,
    "F1": 10,
    "F2": 10,
    "F3": 20,
}

# Relation/collection fields renamed to the cross-framework shape before
# comparison. Hasura needs no map (renames live in its metadata).
_ALIASES = {
    "postgraphile": {
        "tbUserByFkAuthor": "author",
        "tbPostByFkPost": "post",
        "tbCommentsByFkPost": "comments",
        "tbPostByRowId": "post",
        "allTbUsers": "users",
        "allTbPosts": "posts",
        "allTbComments": "comments",
    },
}


class ParityError(AssertionError):
    pass


def _post(url: str, query: str, variables: dict | None = None) -> dict:
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read())
    if body.get("errors"):
        raise ParityError(f"GraphQL errors from {url}: {str(body['errors'])[:300]}")
    return body["data"]


def _normalize(value, aliases: dict):
    """Recursively apply field aliases and unwrap Relay connections."""
    if isinstance(value, dict):
        if set(value) <= {"nodes", "edges", "pageInfo", "totalCount"} and "nodes" in value:
            return _normalize(value["nodes"], aliases)
        return {aliases.get(k, k): _normalize(v, aliases) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v, aliases) for v in value]
    return value


def _shape(value):
    """Recursive field-set shape: dicts → sorted key/shape map, lists → union."""
    if isinstance(value, dict):
        return {k: _shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        merged = {}
        for item in value:
            s = _shape(item)
            if isinstance(s, dict):
                merged.update(s)
        return [merged]
    return "scalar"


def _rows(data, aliases: dict):
    """Unwrap the single-root entity list from a normalized response."""
    norm = _normalize(data, aliases)
    values = list(norm.values())
    if len(values) != 1:
        raise ParityError(f"expected one root field, got {sorted(norm)}")
    rows = values[0]
    if not isinstance(rows, list):
        raise ParityError(f"root field is not a list: {type(rows).__name__}")
    return rows


def _t1_composite(data, aliases: dict):
    """Normalize T1 into {post fields..., comments: [...]} regardless of shape.

    FraiseQL answers with two roots (post + comments); Hasura with a
    one-element posts list nesting comments; PostGraphile with a single
    post object nesting a comment connection.
    """
    norm = _normalize(data, aliases)
    if set(norm) == {"post", "comments"}:  # FraiseQL multi-root
        return {**norm["post"], "comments": norm["comments"]}
    values = list(norm.values())
    if len(values) != 1:
        raise ParityError(f"unexpected T1 roots: {sorted(norm)}")
    post = values[0]
    if isinstance(post, list):  # Hasura: posts(where: id) → [post]
        if len(post) != 1:
            raise ParityError(f"T1 matched {len(post)} posts, expected 1")
        post = post[0]
    if not isinstance(post, dict):
        raise ParityError("T1 root is not an object")
    return post


def _resolve_t1_query(fw_name: str, fw_config: dict, post_id: str):
    """Build the (query, variables) pair each engine benchmarks for T1."""
    tmpl_key = fw_config.get("t1_template")
    if tmpl_key == "fraiseql_multi_root":
        return bench._FRAISEQL_T1_MULTI_ROOT, {"id": post_id}
    if tmpl_key == "postgraphile":
        return bench._PG_T1_TMPL.format(post_id=post_id), None
    if tmpl_key == "hasura":
        return bench._HASURA_T1_TMPL.format(post_id=post_id), None
    return bench._GQL_T1_TMPL.format(post_id=post_id), None


def _graphql_url(fw_config: dict) -> str:
    for key in ("Q1", "Q2", "Q2b"):
        entry = fw_config["queries"].get(key)
        if isinstance(entry, tuple):
            return entry[0]
    return fw_config.get("graphql_url", "")


def _scenario_document(fw_config: dict, scenario: str):
    entry = fw_config["queries"].get(scenario)
    if not isinstance(entry, tuple):
        raise ParityError(f"scenario {scenario} not wired as a static document")
    return entry[0], entry[1]


def run_audit(
    audited: tuple[str, ...] = AUDITED,
    scenarios: tuple[str, ...] = SCENARIOS,
    bench_module=None,
) -> list[str]:
    """Run the full parity audit. Returns a list of failure descriptions.

    bench_module: pass the live module when calling from bench_sequential
    itself (running as __main__, a fresh `import bench_sequential` would be a
    second instance without the --target-host rebasing applied).
    """
    global bench
    if bench_module is not None:
        bench = bench_module
    failures: list[str] = []
    ref_config = bench.FRAMEWORKS[REFERENCE]

    post_info = bench._discover_post_uuid(ref_config)
    if not post_info:
        return [f"could not discover a post UUID from {REFERENCE}"]
    post_id = post_info[0]

    # Reference responses
    ref: dict[str, object] = {}
    for scenario in scenarios:
        try:
            if scenario == "T1":
                query, variables = _resolve_t1_query(REFERENCE, ref_config, post_id)
                data = _post(_graphql_url(ref_config), query, variables)
                ref[scenario] = _t1_composite(data, {})
            else:
                url, query = _scenario_document(ref_config, scenario)
                ref[scenario] = _rows(_post(url, query), {})
        except (ParityError, urllib.error.URLError, OSError) as exc:
            return [f"{REFERENCE}/{scenario}: reference unavailable — {exc}"]

    for fw_name in audited:
        fw_config = bench.FRAMEWORKS[fw_name]
        aliases = _ALIASES.get(fw_name, {})
        for scenario in scenarios:
            try:
                if scenario == "T1":
                    query, variables = _resolve_t1_query(fw_name, fw_config, post_id)
                    got = _t1_composite(
                        _post(_graphql_url(fw_config), query, variables), aliases
                    )
                    ref_t1 = ref["T1"]
                    # Same fixed post id everywhere → comment counts must match
                    # the reference exactly (equivalent work on identical rows).
                    if len(got.get("comments", [])) != len(ref_t1.get("comments", [])):
                        failures.append(
                            f"{fw_name}/T1: {len(got.get('comments', []))} comments, "
                            f"reference returned {len(ref_t1.get('comments', []))}"
                        )
                    if _shape(got) != _shape(ref_t1):
                        failures.append(
                            f"{fw_name}/T1: field shape {_shape(got)} != "
                            f"reference {_shape(ref_t1)}"
                        )
                    # T1 is a fixed-id lookup — values are deterministic.
                    for field in ("id", "title", "content"):
                        if got.get(field) != ref_t1.get(field):
                            failures.append(
                                f"{fw_name}/T1: {field}={str(got.get(field))[:40]!r} != "
                                f"reference {str(ref_t1.get(field))[:40]!r}"
                            )
                else:
                    url, query = _scenario_document(fw_config, scenario)
                    got_rows = _rows(_post(url, query), aliases)
                    ref_rows = ref[scenario]
                    if len(got_rows) != EXPECTED_COUNTS[scenario]:
                        failures.append(
                            f"{fw_name}/{scenario}: {len(got_rows)} rows, "
                            f"expected {EXPECTED_COUNTS[scenario]}"
                        )
                    if _shape(got_rows) != _shape(ref_rows):
                        failures.append(
                            f"{fw_name}/{scenario}: field shape {_shape(got_rows)} != "
                            f"reference {_shape(ref_rows)}"
                        )
            except (ParityError, urllib.error.URLError, OSError) as exc:
                failures.append(f"{fw_name}/{scenario}: {exc}")

    return failures


if __name__ == "__main__":
    import sys

    problems = run_audit()
    if problems:
        print("PARITY AUDIT FAILED:")
        for p in problems:
            print(f"  ✗ {p}")
        sys.exit(1)
    print(f"parity audit passed: {len(AUDITED)} engines × {len(SCENARIOS)} scenarios vs {REFERENCE}")
