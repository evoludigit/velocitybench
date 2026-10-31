"""Invalid results: a measured cell later shown to have measured the wrong thing.

M1d (#247): tvd_* were seeded before the bulk sync filled tv_*, so every M1d
run before the fix patched a 5-row copy of the dataset. Such a cell is neither
a result, an exclusion by design, nor a gap: it renders as invalid, with its
reason, and its number never reaches a chart or a model.
"""
import copy
import sys
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


def test_pre_fix_m1d_result_is_invalid_with_its_reason(median_grid):
    for fw in ("fraiseql-tv", "fraiseql-tv-cache"):
        cell = median_grid.cell(fw, "M1d")
        assert cell.status == "invalid", fw
        assert cell.rps is None, "an invalid cell must not carry its number"
        assert "#247" in cell.reason


def test_other_cells_of_the_same_run_stay_results(median_grid):
    assert median_grid.cell("fraiseql-tv", "M1").status == "result"
    assert median_grid.cell("hasura", "M1d").status == "excluded"


def test_a_run_after_the_fix_keeps_its_m1d_result(median_run, meta):
    raw = copy.deepcopy(median_run.raw)
    raw["environment"]["timestamp"] = "2027-01-01T00:00:00+00:00"
    # a post-redesign run carries no MC1 for the engines MC1 now excludes
    excluded = {(e["framework"], e["scenario"]) for e in meta["exclusions"]}
    raw["results"] = [r for r in raw["results"]
                      if (r["framework"], r["query"]) not in excluded]
    run = build.Run(
        environment=raw["environment"],
        framework_versions=raw["framework_versions"],
        results=raw["results"],
        resource_metrics=median_run.resource_metrics,
        db_footprint=median_run.db_footprint,
        source_path=median_run.source_path,
        raw=raw,
    )
    cell = build.build_grid(run, meta).cell("fraiseql-tv", "M1d")
    assert cell.status == "result" and cell.rps


def test_invalid_entry_naming_an_unknown_scenario_fails(median_run, meta):
    bad = copy.deepcopy(meta)
    bad["invalid_results"].append(
        {"scenario": "M9", "measured_before": "2026-11-01",
         "issue": 1, "reason": "x"})
    with pytest.raises(ValueError, match="M9"):
        build.build_grid(median_run, bad)


def test_page_renders_the_reason_not_the_number(median_run, meta):
    page = build.render(median_run, meta)["index.html"].decode("utf-8")
    start = page.index('id="cell-fraiseql-tv-M1d"')
    cell_html = page[page.rindex("<td", 0, start):page.index("</td>", start)]
    assert 'data-invalid="true"' in cell_html
    assert "#247" in cell_html
    assert "6,783" not in cell_html and "6783" not in cell_html
    assert 'wt-bar wt-M1d"' not in page, "an invalid M1d must draw no bar"
    assert "6,783" not in page and "6 783" not in page


def test_delta_mode_says_the_anchor_has_no_valid_write(median_run, meta):
    """With M1d invalid, FraiseQL has no write input in delta mode: the
    break-even sentence must say so, not that it trails every rival."""
    grid = build.build_grid(median_run, meta)
    amort = build.amortize(grid, meta, "Q2b", "delta")
    sent = build._s7_breakeven_sentence(amort, meta)
    assert "trails" not in sent and "leads" not in sent
    assert "no valid M1d measurement" in sent


def test_pre_redesign_mc1_is_invalid_or_excluded_never_a_result(median_grid):
    """MC1 before #224 sent the bio mutation with no cascade: a different
    scenario. Engines MC1 now excludes by design show the exclusion; the rest
    show the invalid reason. Neither keeps the old number."""
    assert median_grid.cell("async-graphql", "MC1").status == "excluded"
    for fw in ("fraiseql-tv", "hasura", "postgraphile"):
        cell = median_grid.cell(fw, "MC1")
        assert cell.status == "invalid", fw
        assert cell.issue == 224 and cell.rps is None
