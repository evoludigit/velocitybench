"""Phase-04 delta tool: per-cell run-to-run comparison of two sweep JSONs.

`scripts/bench-delta.py run-A.json run-B.json` compares every
(framework, query) cell across the metrics rps / p50_ms / p99_ms, flags any
cell whose absolute percentage delta exceeds a threshold (default 5%), and
exits non-zero when the flagged fraction exceeds a limit. It is the Phase 05
variance-baseline instrument and the Phase 06 acceptance gate.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DELTA_PATH = REPO_ROOT / "scripts" / "bench-delta.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("bench_delta", DELTA_PATH)
    mod = importlib.util.module_from_spec(spec)
    # dataclass field resolution looks the module up in sys.modules
    sys.modules["bench_delta"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def delta():
    return _load_module()


def _run_json(rows: list[dict]) -> dict:
    """Minimal run-JSON document in the bench_sequential output schema."""
    return {
        "environment": {"timestamp": "2026-07-04T12:00:00+02:00"},
        "framework_versions": {},
        "results": rows,
    }


def _row(fw="fraiseql-tv", query="Q1", rps=10000.0, p50=3.0, p99=9.0,
         pass_num=1, skipped=False, **extra):
    row = {
        "framework": fw,
        "query": query,
        "pass": pass_num,
        "rps": rps,
        "p50_ms": p50,
        "p95_ms": p50 * 2,
        "p99_ms": p99,
        "requests": 1000,
        "errors": 0,
        "skipped": skipped,
        "skip_reason": "service did not become healthy" if skipped else None,
    }
    row.update(extra)
    return row


def test_tool_exists():
    assert DELTA_PATH.exists(), "scripts/bench-delta.py missing"


def test_extract_cells_indexes_by_framework_query(delta):
    doc = _run_json([_row(rps=100.0), _row(query="M1", rps=50.0)])
    cells = delta.extract_cells(doc)
    assert cells[("fraiseql-tv", "Q1")]["rps"] == 100.0
    assert cells[("fraiseql-tv", "M1")]["rps"] == 50.0


def test_extract_cells_excludes_skipped_rows(delta):
    doc = _run_json([_row(skipped=True, rps=0.0)])
    assert delta.extract_cells(doc) == {}


def test_extract_cells_takes_median_across_passes(delta):
    doc = _run_json([
        _row(rps=100.0, pass_num=1),
        _row(rps=200.0, pass_num=2),
        _row(rps=400.0, pass_num=3),
    ])
    assert delta.extract_cells(doc)[("fraiseql-tv", "Q1")]["rps"] == 200.0


def test_delta_math_exact_percentages(delta):
    a = delta.extract_cells(_run_json([_row(rps=10000.0, p50=4.0, p99=10.0)]))
    b = delta.extract_cells(_run_json([_row(rps=9000.0, p50=5.0, p99=10.0)]))
    cells = {c.metric: c for c in delta.compute_deltas(a, b).cells}
    assert cells["rps"].delta_pct == pytest.approx(-10.0)
    assert cells["p50_ms"].delta_pct == pytest.approx(25.0)
    assert cells["p99_ms"].delta_pct == pytest.approx(0.0)


def test_flagging_respects_threshold(delta):
    a = delta.extract_cells(_run_json([_row(rps=10000.0, p50=100.0, p99=100.0)]))
    b = delta.extract_cells(_run_json([_row(rps=10490.0, p50=105.1, p99=100.0)]))
    report = delta.compute_deltas(a, b, cell_threshold_pct=5.0)
    flagged = {(c.metric): c.flagged for c in report.cells}
    assert flagged["rps"] is False       # +4.9% — under threshold
    assert flagged["p50_ms"] is True     # +5.1% — over threshold
    assert flagged["p99_ms"] is False


def test_missing_cell_is_reported_and_counts_as_flagged(delta):
    a = delta.extract_cells(_run_json([_row(), _row(fw="hasura")]))
    b = delta.extract_cells(_run_json([_row()]))
    report = delta.compute_deltas(a, b)
    assert ("hasura", "Q1") in report.missing
    # Missing cells count against the gate: one per metric compared.
    assert report.flagged_count >= len(report.metrics)


def test_exit_zero_when_within_threshold(delta, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_run_json([_row(rps=10000.0)])))
    b.write_text(json.dumps(_run_json([_row(rps=10100.0)])))
    assert delta.main([str(a), str(b)]) == 0


def test_exit_nonzero_when_flagged_fraction_exceeded(delta, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_run_json([_row(rps=10000.0, p50=4.0, p99=10.0)])))
    b.write_text(json.dumps(_run_json([_row(rps=5000.0, p50=8.0, p99=20.0)])))
    assert delta.main([str(a), str(b)]) != 0


def test_report_output_contains_table_and_summary(delta, tmp_path, capsys):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_run_json([_row(rps=10000.0)])))
    b.write_text(json.dumps(_run_json([_row(rps=9000.0)])))
    delta.main([str(a), str(b)])
    out = capsys.readouterr().out
    assert "| fraiseql-tv" in out
    assert "-10.0" in out
    assert "flagged" in out.lower()
