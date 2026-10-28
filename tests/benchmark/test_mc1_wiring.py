"""MC1: a comment on a post, ending with the post's latest comments (#220, #224).

MC1 is a workflow benchmark, deliberately asymmetric. FraiseQL's MC1 is one
request: createCommentCascade returns the comment and, in its cascade, the post
with its latest 10 comments. FraiseQL's MC1c (cascade off) and Hasura's and
PostGraphile's MC1 are two: the insert, then a re-fetch of the same list.

The write changes a list's membership on purpose: after a bio write the written
entity is the whole change, so there is nothing for a cascade to carry (#224).
Every run is checked before it is measured, and deletes exactly the comments it
inserted.
"""

import json
import re
import sys
import uuid
from pathlib import Path

import pytest

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential as bench  # noqa: E402

FRAMEWORKS = bench.FRAMEWORKS
FRAISEQL = ("fraiseql-tv", "fraiseql-tv-cache", "fraiseql-v-nocache", "fraiseql-v-cache")
POOL = [
    ("11111111-0000-4000-8000-000000000001", 101, "22222222-0000-4000-8000-000000000001", 7),
    ("11111111-0000-4000-8000-000000000002", 102, "22222222-0000-4000-8000-000000000002", 8),
]


@pytest.fixture
def fixed_base(monkeypatch):
    monkeypatch.setattr(bench, "_mc1_new_base", lambda: "abcdef012345")


def _config(name):
    return {**FRAMEWORKS[name], "queries": dict(FRAMEWORKS[name]["queries"])}


# ---------------------------------------------------------------------------
# Which engines run it
# ---------------------------------------------------------------------------


def test_mc1_runs_on_engines_with_a_comment_insert():
    wired = {name for name, cfg in FRAMEWORKS.items() if "MC1" in cfg["queries"]}
    assert wired == {*FRAISEQL, "hasura", "postgraphile"}


def test_mc1c_is_fraiseql_with_the_cascade_off():
    wired = {name for name, cfg in FRAMEWORKS.items() if "MC1c" in cfg["queries"]}
    assert wired == set(FRAISEQL)


def test_every_mc1_engine_names_its_template():
    for name, cfg in FRAMEWORKS.items():
        if "MC1" in cfg["queries"]:
            assert cfg["mc1_template"] in ("fraiseql", *bench._MC1_TEMPLATES), name


# ---------------------------------------------------------------------------
# The cycle each engine runs
# ---------------------------------------------------------------------------


def test_fraiseql_mc1_is_one_request_selecting_the_cascade(fixed_base):
    entry = bench._resolve_mc1(_config("fraiseql-tv"), "MC1", POOL)
    assert entry["mode"] == "mc1_cycle"
    assert len(entry["steps"]) == 1
    doc = json.loads(entry["steps"][0][1])
    assert "createCommentCascade" in doc["query"]
    assert "cascade { updated" in doc["query"] and "... on PostFull" in doc["query"]
    assert doc["variables"] == {
        "id": bench._MC1_ID_SLOT, "postId": POOL[1][0], "authorId": POOL[1][2],
        "content": bench._MC1_CONTENT,
    }


def test_fraiseql_mc1c_inserts_then_refetches_the_same_post(fixed_base):
    entry = bench._resolve_mc1(_config("fraiseql-v-nocache"), "MC1c", POOL)
    assert len(entry["steps"]) == 2
    write = json.loads(entry["steps"][0][1])
    read = json.loads(entry["steps"][1][1])
    assert "createComment(" in write["query"] and "cascade" not in write["query"]
    assert "postFull" in read["query"] and read["variables"] == {"id": POOL[1][0]}


@pytest.mark.parametrize("name", ["hasura", "postgraphile"])
def test_classical_mc1_inserts_by_integer_keys_then_refetches(fixed_base, name):
    entry = bench._resolve_mc1(_config(name), "MC1", POOL)
    assert len(entry["steps"]) == 2
    write = json.loads(entry["steps"][0][0])["query"]
    read = json.loads(entry["steps"][1][0])["query"]
    assert bench._MC1_ID_SLOT in write
    assert "101" in write and "7" in write
    assert POOL[0][0] in read and "10" in read


def test_classical_documents_balance_their_braces():
    for create, refetch in bench._MC1_TEMPLATES.values():
        for doc in (create, refetch):
            text = doc.format(comment_id="c", content="x", post_pk=1, author_pk=2, post_id="p")
            assert text.count("{") == text.count("}")


def test_engine_without_a_template_has_no_mc1(fixed_base):
    assert bench._resolve_mc1(_config("async-graphql"), "MC1", POOL) is None


def test_empty_pool_has_no_mc1(fixed_base):
    assert bench._resolve_mc1(_config("fraiseql-tv"), "MC1", []) is None


def test_k6_runs_every_step_of_the_cycle(fixed_base):
    entry = bench._resolve_mc1(_config("hasura"), "MC1", POOL)
    steps = bench._entry_to_k6_steps(entry, "graphql", "MC1")
    assert [len(s["bodies"]) for s in steps] == [2, 2]
    assert all(s["method"] == "POST" and s["validate"] == "graphql" for s in steps)


# ---------------------------------------------------------------------------
# Comment ids: unique, and all under the scenario's prefix
# ---------------------------------------------------------------------------


def test_comment_ids_are_uuids_inside_the_scenario_range():
    lo, hi = bench._mc1_id_range("abcdef012345")
    for run, worker, n in [(0, 0, 0), (2, 39, 123456), (0xFFFF, 0xFFFF, 0xFFFFFFFFFFFF)]:
        cid = bench._mc1_id("abcdef012345", run, worker, n)
        assert str(uuid.UUID(cid)) == cid
        assert lo <= cid <= hi


def test_comment_ids_differ_across_runs_and_workers():
    ids = {
        bench._mc1_id("abcdef012345", run, worker, n)
        for run in (0, 1, 2) for worker in range(3) for n in range(3)
    }
    assert len(ids) == 27


def test_k6_builds_the_same_id_layout():
    src = (BENCH_DIR / "k6" / "scenario.js").read_text()
    assert "hex(cfg.mc1.run, 4)" in src
    assert "hex(exec.vu.idInTest, 4)" in src
    assert "hex(exec.vu.iterationInInstance, 12)" in src
    assert "split(cfg.mc1.slot).join(id)" in src


def test_cleanup_deletes_only_under_the_prefix_then_vacuums(monkeypatch):
    sent = []
    monkeypatch.setattr(bench, "_psql", lambda sql: sent.append(sql) or [["42"]])
    assert bench._mc1_delete_inserted("abcdef012345") == 42
    lo, hi = bench._mc1_id_range("abcdef012345")
    assert f"BETWEEN '{lo}' AND '{hi}'" in sent[0] and "DELETE FROM benchmark.tb_comment" in sent[0]
    assert sent[1] == "VACUUM ANALYZE benchmark.tb_comment, benchmark.tv_comment"


def test_a_used_prefix_is_never_chosen(monkeypatch):
    counts = iter([["3"], ["0"]])
    monkeypatch.setattr(bench, "_psql", lambda sql: [next(counts)])
    base = bench._mc1_new_base()
    assert re.fullmatch(r"[0-9a-f]{12}", base)


# ---------------------------------------------------------------------------
# The check before every run
# ---------------------------------------------------------------------------

CID = "abcdef01-2345-0000-0000-000000000000"


def _listed(ids):
    return [{"id": i, "content": "x"} for i in ids]


def _cascade(listed, created=CID):
    return {"data": {"createCommentCascade": {
        "entity": {"id": CID},
        "cascade": {"updated": [
            {"operation": "CREATED", "entity": {"__typename": "Comment", "id": created}},
            {"operation": "UPDATED", "entity": {"__typename": "PostFull", "id": "p",
                                                "comments": _listed(listed)}},
        ]},
    }}}


def test_a_correct_cascade_passes():
    assert bench._mc1_check_cycle([_cascade([CID, "a", "b"])], CID, 3, cascade=True) is None


def test_a_cascade_without_the_created_comment_fails():
    problem = bench._mc1_check_cycle([_cascade([CID, "a"], created="other")], CID, 2, True)
    assert "CREATED" in problem


def test_a_list_without_the_new_comment_first_fails():
    problem = bench._mc1_check_cycle([_cascade(["a", CID])], CID, 2, cascade=True)
    assert "not first" in problem


def test_a_list_that_appends_without_truncating_fails():
    problem = bench._mc1_check_cycle([_cascade([CID, *"abcdefghij"])], CID, 10, cascade=True)
    assert "11 comments listed, expected 10" in problem


def test_a_response_with_errors_fails():
    problem = bench._mc1_check_cycle([{"errors": [{"message": "no"}]}], CID, 1, cascade=True)
    assert "errors" in problem


def test_classical_write_must_name_the_new_comment():
    write = {"data": {"createComment": {"id": "someone-else"}}}
    read = {"data": {"posts": [{"id": "p", "comments": _listed([CID])}]}}
    problem = bench._mc1_check_cycle([write, read], CID, 1, cascade=False)
    assert "does not name" in problem


@pytest.mark.parametrize("read", [
    {"data": {"posts": [{"id": "p", "comments": _listed([CID, "a"])}]}},
    {"data": {"tbPostByRowId": {"id": "p", "comments": {"nodes": _listed([CID, "a"])}}}},
    {"data": {"postFull": {"id": "p", "comments": _listed([CID, "a"])}}},
])
def test_classical_refetch_shapes_are_read(read):
    write = {"data": {"createComment": {"id": CID}}}
    assert bench._mc1_check_cycle([write, read], CID, 2, cascade=False) is None


def test_failed_check_records_a_failed_cell_and_measures_nothing(monkeypatch, fixed_base):
    cfg = _config("fraiseql-tv")
    cfg["queries"]["MC1"] = bench._resolve_mc1(cfg, "MC1", POOL)
    monkeypatch.setattr(bench, "_mc1_probe", lambda entry: "cycle 1: nope")
    deleted = []
    monkeypatch.setattr(bench, "_mc1_delete_inserted", lambda base: deleted.append(base) or 0)
    monkeypatch.setattr(bench, "_run_scenario", lambda *a: pytest.fail("measured"))
    r = bench.run_scenario("fraiseql-tv", cfg, "MC1", 40, 5, 1)
    assert r.skipped and r.skip_reason == "MC1 check failed: cycle 1: nope"
    assert r.errors == 1
    assert deleted == ["abcdef012345"]


def test_a_measured_run_deletes_its_comments_even_when_it_raises(monkeypatch, fixed_base):
    cfg = _config("hasura")
    cfg["queries"]["MC1"] = bench._resolve_mc1(cfg, "MC1", POOL)
    monkeypatch.setattr(bench, "_mc1_probe", lambda entry: None)
    deleted = []
    monkeypatch.setattr(bench, "_mc1_delete_inserted", lambda base: deleted.append(base) or 0)

    def boom(*_a):
        raise RuntimeError("k6 failed")

    monkeypatch.setattr(bench, "_run_scenario", boom)
    with pytest.raises(RuntimeError):
        bench.run_scenario("hasura", cfg, "MC1", 40, 5, 1)
    assert deleted == ["abcdef012345", "abcdef012345"]


# ---------------------------------------------------------------------------
# pg_tviews scoping covers the table MC1 writes
# ---------------------------------------------------------------------------


def test_tview_scoping_covers_tb_comment(monkeypatch):
    sent = []

    def fake(sql):
        sent.append(sql)
        if sql.startswith("SELECT"):
            return [["tb_user", "trg_tview_flush_user"], ["tb_comment", "trg_tview_flush_comment"]]
        return []

    monkeypatch.setattr(bench, "_psql", fake)
    bench.set_tview_triggers(False)
    assert "'tb_comment'" in sent[0]
    assert "ALTER TABLE benchmark.tb_comment DISABLE TRIGGER trg_tview_flush_comment" in sent[1]
    assert "ALTER TABLE benchmark.tb_user DISABLE TRIGGER trg_tview_flush_user" in sent[1]


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------


def _row(framework, query, rps, p50, server=None, db=None):
    r = bench.BenchResult(framework=framework, query_name=query, duration_secs=10, concurrency=40,
                          ext_requests=int(rps * 10), ext_p50_ms=p50, ext_p95_ms=p50,
                          ext_p99_ms=p50, cpu_server_cores=server, cpu_db_cores=db)
    return r


def test_report_sets_round_trips_latency_and_cpu_side_by_side():
    text = "\n".join(bench.format_mc1_section([
        _row("fraiseql-tv", "MC1", 1000, 4.0, 1.5, 1.5),
        _row("fraiseql-tv", "MC1c", 800, 6.0, 2.0, 2.0),
        _row("hasura", "MC1", 900, 5.0),
    ]))
    assert "| fraiseql-tv | MC1 | 1 | 1000 | 4.0 | 3.00 |" in text
    assert "| fraiseql-tv | MC1c | 2 | 800 | 6.0 | 5.00 |" in text
    assert "| hasura | MC1 | 2 | 900 | 5.0 | — |" in text
    assert "1 round trip instead of 2: p50 4.0 ms against 6.0 ms, 3.00 CPU ms per cycle against 5.00" in text


def test_report_never_claims_the_old_cascade_line_or_a_ratio():
    text = "\n".join(bench.format_mc1_section([
        _row("fraiseql-tv", "MC1", 1000, 4.0), _row("hasura", "MC1", 900, 5.0),
    ]))
    assert "contains all affected entities" not in text
    assert "×" not in text
    assert "outside the timed window" in text


def test_report_lists_a_failed_check():
    r = _row("hasura", "MC1", 0, 0)
    r.skipped = True
    r.skip_reason = "MC1 check failed: cycle 1: nope"
    text = "\n".join(bench.format_mc1_section([r]))
    assert "| hasura | MC1 | — | ❌ MC1 check failed: cycle 1: nope |" in text


def test_report_omits_mc1_without_mc1_rows():
    assert bench.format_mc1_section([_row("hasura", "Q1", 900, 5.0)]) == []


def test_labels_state_the_asymmetry():
    assert "1 request" in bench._QUERY_LABELS["MC1"]
    assert "2 serial requests" in bench._QUERY_LABELS["MC1"]
    assert "cascade off" in bench._QUERY_LABELS["MC1c"]
