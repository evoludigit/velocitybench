"""Phase 01 — data pipeline & contract.

100% data layer, strict TDD. Mirrors tests/benchmark/test_report_from_json.py.
The stakes are asymmetric (README methodology): a silently dropped or
mislabeled cell discredits the campaign, so these invariants exist as tests
before the code.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent
BUILD_PY = SITE_DIR / "build.py"
SCENARIOS = SITE_DIR / "scenarios.json"

sys.path.insert(0, str(SITE_DIR))


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(BUILD_PY), *map(str, args)],
        capture_output=True, text=True, cwd=cwd,
    )


# --------------------------------------------------------------------------
# Cycle 1 — CLI contract & same-run rule
# --------------------------------------------------------------------------

def test_build_py_exists():
    assert BUILD_PY.exists(), "site/build.py must exist"


def test_single_json_exit_zero(sweep3_path, tmp_path):
    out = tmp_path / "dist"
    res = run_cli(sweep3_path, "--out", out)
    assert res.returncode == 0, res.stderr
    assert (out / "index.html").exists()


def test_two_jsons_exit_nonzero_names_same_run(sweep3_path, tmp_path):
    out = tmp_path / "dist"
    res = run_cli(sweep3_path, sweep3_path, "--out", out)
    assert res.returncode != 0
    assert "same-run" in (res.stderr + res.stdout).lower()


def test_directory_exit_nonzero_names_same_run(tmp_path):
    out = tmp_path / "dist"
    res = run_cli(tmp_path, "--out", out)
    assert res.returncode != 0
    assert "same-run" in (res.stderr + res.stdout).lower()


def test_missing_file_clear_error(tmp_path):
    out = tmp_path / "dist"
    res = run_cli(tmp_path / "nope.json", "--out", out)
    assert res.returncode != 0
    assert "nope.json" in (res.stderr + res.stdout)


def test_load_run_validates_required_keys(tmp_path):
    import build
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"environment": {}, "results": []}))
    with pytest.raises(Exception) as exc:
        build.load_run(bad)
    assert "framework_versions" in str(exc.value)


# --------------------------------------------------------------------------
# Cycle 2 — the cell grid (no silent gaps)
# --------------------------------------------------------------------------

def test_grid_covers_full_cross_product(grid, meta):
    n_fw = len(meta["framework_order"])
    n_sc = len(meta["scenario_order"])
    assert len(grid.cells) == n_fw * n_sc == 12 * 16
    for fw in meta["framework_order"]:
        for sc in meta["scenario_order"]:
            assert (fw, sc) in grid.cells, f"missing cell {fw}/{sc}"


def test_grid_partition_no_silent_gaps(grid):
    statuses = [c.status for c in grid.cells.values()]
    assert set(statuses) <= {"result", "excluded", "not_measured"}
    assert statuses.count("result") == 118
    assert statuses.count("excluded") == 36
    assert statuses.count("not_measured") == 38


def test_result_cell_carries_metrics(grid):
    cell = grid.cells[("fraiseql-tv", "Q1")]
    assert cell.status == "result"
    assert round(cell.rps, 1) == 8182.3
    assert cell.errors == 0
    assert cell.p99_ms == 7.63


def test_excluded_cell_carries_reason(grid):
    cell = grid.cells[("hasura", "M1d")]
    assert cell.status == "excluded"
    assert cell.reason_id == 3
    assert "no equivalent operation" in cell.reason
    # a structurally different reason id resolves to different text
    apq = grid.cells[("hasura", "Q1_APQ")]
    assert apq.status == "excluded" and apq.reason_id == 4


def test_not_measured_cell_is_explicit(grid):
    cell = grid.cells[("actix-web-rest", "Q3")]
    assert cell.status == "not_measured"
    # tv-cache M1d is wired-but-unrun in this sweep, NOT excluded by design
    assert grid.cells[("fraiseql-tv-cache", "M1d")].status == "not_measured"


def test_cross_check_exclusions_have_no_result_row(grid, meta):
    """Every declared exclusion must be absent from results (drift catch)."""
    for exc in meta["exclusions"]:
        cell = grid.cells[(exc["framework"], exc["scenario"])]
        assert cell.status == "excluded", (
            f"{exc['framework']}/{exc['scenario']} declared excluded but has "
            f"status {cell.status}")


def test_cross_check_results_are_not_excluded(sweep3_run, meta):
    excluded = {(e["framework"], e["scenario"]) for e in meta["exclusions"]}
    for r in sweep3_run.results:
        assert (r["framework"], r["query"]) not in excluded


def test_contradiction_present_and_excluded_raises(sweep3_run, meta):
    """A result row for a by-design-excluded cell must fail the build loudly."""
    import build
    import copy
    run = copy.deepcopy(sweep3_run)
    run.results.append({
        "framework": "hasura", "query": "M1d", "pass": 1, "rps": 1.0,
        "p50_ms": 1.0, "p95_ms": 1.0, "p99_ms": 1.0, "requests": 1,
        "errors": 0, "error_breakdown": {}, "skipped": False,
        "skip_reason": "",
    })
    with pytest.raises(Exception) as exc:
        build.build_grid(run, meta)
    assert "hasura" in str(exc.value) and "M1d" in str(exc.value)


def test_unknown_exclusion_reference_raises(sweep3_run, meta):
    import build
    import copy
    bad_meta = copy.deepcopy(meta)
    bad_meta["exclusions"].append(
        {"framework": "hasura", "scenario": "NOPE", "reason_id": 3})
    with pytest.raises(Exception):
        build.build_grid(sweep3_run, bad_meta)


# --------------------------------------------------------------------------
# Cycle 3 — byte-stability & banner logic
# --------------------------------------------------------------------------

def test_render_is_byte_stable(sweep3_run, meta):
    import build
    a = build.render(sweep3_run, meta)
    b = build.render(sweep3_run, meta)
    assert a == b
    assert all(isinstance(v, bytes) for v in a.values())


def test_build_twice_produces_identical_tree(sweep3_path, tmp_path):
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    assert run_cli(sweep3_path, "--out", out_a).returncode == 0
    assert run_cli(sweep3_path, "--out", out_b).returncode == 0
    files_a = sorted(p.relative_to(out_a) for p in out_a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(out_b) for p in out_b.rglob("*") if p.is_file())
    assert files_a == files_b and files_a, "output file sets differ or empty"
    for rel in files_a:
        assert (out_a / rel).read_bytes() == (out_b / rel).read_bytes(), rel


def test_banner_present_for_localhost(localhost_path, meta):
    import build
    run = build.load_run(localhost_path)
    html = build.render(run, meta)["index.html"]
    assert "LOCAL DATA — NOT PUBLISHABLE".encode() in html


def test_banner_absent_for_sweep3(sweep3_run, meta):
    import build
    html = build.render(sweep3_run, meta)["index.html"]
    assert "LOCAL DATA — NOT PUBLISHABLE".encode() not in html


def test_no_wallclock_in_build_source():
    """Byte-stability guard: the build must never read the wall clock."""
    src = BUILD_PY.read_text()
    assert "datetime.now" not in src
    assert "time.time" not in src
