"""Scenario coverage gate — the publishable subset has no implicit gaps.

Every (framework, scenario) cell in the 2026-07 subset is either wired in
FRAMEWORKS or listed as a by-design exclusion in docs/scenarios.md. This test
pins the wired side of that matrix, plus the load-generator lockstep for the
two scenario modes added for REST workflows (C3/HC3 lookups, REST MC1).
"""

import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential as bench  # noqa: E402

# The publishable subset — keep in sync with scripts/hetzner/bench-run.sh.
SUBSET = [
    "fraiseql-tv",
    "fraiseql-tv-cache",
    "fraiseql-v-nocache",
    "fraiseql-v-cache",
    "fraiseql-tv-audit",
    "hasura",
    "postgraphile",
    "actix-web-rest",
    "async-graphql",
    "mercurius",
    "apollo-server",
    "strawberry",
]

CORE = {"Q1", "Q2", "Q2b", "Q3", "C3", "HC3", "F1", "F2", "F3", "M1", "T1", "MC1"}
APQ = {"Q1_APQ", "Q2b_APQ", "M1_APQ"}

# Wired scenario keys per subset framework. Anything absent here must appear
# in the docs/scenarios.md exclusion list (see test below).
EXPECTED: dict[str, set[str]] = {
    "fraiseql-tv": CORE | APQ | {"M1d"},
    "fraiseql-tv-cache": CORE | APQ | {"M1d"},
    "fraiseql-v-nocache": CORE | APQ,  # M1d excluded: tvd_* is tv-pipeline-only
    "fraiseql-v-cache": CORE | APQ,
    "fraiseql-tv-audit": {"M1"},  # audit-overhead appendix row — by design
    "hasura": CORE,  # no native APQ in CE v2; no M1d
    "postgraphile": CORE,  # persisted ops are an allowlist, not APQ; no M1d
    "actix-web-rest": CORE,  # APQ is a GraphQL protocol — N/A for REST
    "async-graphql": CORE | APQ,  # first-party ApolloPersistedQueries extension
    "mercurius": CORE | APQ,  # first-party persistedQueryDefaults.automatic()
    "apollo-server": CORE | APQ,  # APQ native, on by default
    "strawberry": CORE,  # no first-party APQ extension exists
}


def test_subset_scenarios_match_coverage_matrix():
    for fw_name, expected in EXPECTED.items():
        wired = set(bench.FRAMEWORKS[fw_name]["queries"])
        assert wired == expected, (
            f"{fw_name}: wired {sorted(wired)} != documented {sorted(expected)} "
            "— update docs/scenarios.md coverage matrix and this test together"
        )


def test_excluded_cells_are_documented():
    doc = (BENCH_DIR.parent.parent / "docs" / "scenarios.md").read_text()
    assert "Scenario coverage & exclusions" in doc
    for marker in (
        "M1d on v-variants",
        "fraiseql-tv-audit",
        "M1d on non-FraiseQL engines",
        "APQ on Hasura",
        "APQ on PostGraphile",
        "APQ on actix-web-rest",
        "APQ on Strawberry",
    ):
        assert marker in doc, f"exclusion '{marker}' missing from docs/scenarios.md"


def test_single_lookup_templates_exist_for_schema_engines():
    assert bench.FRAMEWORKS["hasura"]["c3_template"] == bench._HASURA_C3_TMPL
    assert bench.FRAMEWORKS["postgraphile"]["c3_template"] == bench._PG_C3_TMPL
    assert "where" in bench._HASURA_C3_TMPL  # uuid not addressable via *_by_pk
    assert "tbUserByRowId" in bench._PG_C3_TMPL


# ── k6 lockstep for the new REST scenario modes ─────────────────────────────

def test_k6_rest_get_rotating_mode():
    entry = {
        "mode": "rest_get_rotating",
        "urls": ["http://x/users/1", "http://x/users/2"],
    }
    steps = bench._entry_to_k6_steps(entry, "rest", "C3")
    assert len(steps) == 1
    assert steps[0]["method"] == "GET"
    assert steps[0]["urls"] == entry["urls"]
    assert steps[0]["validate"] == "rest"


def test_k6_mc1_rest_is_two_step_cycle():
    entry = {
        "mode": "mc1_rest",
        "put_urls": ["http://x/users/1", "http://x/users/2"],
        "put_bodies": ['{"bio":"bio-0"}', '{"bio":"bio-1"}'],
        "q1_url": "http://x/users?limit=20",
    }
    steps = bench._entry_to_k6_steps(entry, "rest", "MC1")
    assert len(steps) == 2
    assert steps[0]["method"] == "PUT"
    assert steps[0]["urls"] == entry["put_urls"]
    assert steps[0]["bodies"] == entry["put_bodies"]
    assert steps[1] == {
        "method": "GET",
        "url": entry["q1_url"],
        "validate": "rest",
    }


def test_python_workers_exist_for_new_modes():
    assert callable(bench._worker_rest_get_rotating)
    assert callable(bench._worker_mc1_rest)
