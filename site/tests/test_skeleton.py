"""Skeleton, honesty devices & AI layer (pins + AI-layer tests).

These are the design->pin regression tests: written AFTER the markup settled,
they guard the honesty-critical invariants (every cell anchored, exclusion vs
not-measured vs slow never conflated, notes sourced from scenarios.json, the
machine layer round-trips, the page is offline) when the grid grows or styling
changes.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


class TagCollector(HTMLParser):
    """Collect (tag, attrs-dict) for every start tag."""

    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


@pytest.fixture()
def built(sweep3_run, meta):
    return build.render(sweep3_run, meta)


@pytest.fixture()
def index_html(built):
    return built["index.html"].decode("utf-8")


@pytest.fixture()
def tags(index_html):
    c = TagCollector()
    c.feed(index_html)
    return c.tags


def cells_by_id(tags):
    return {a["id"]: (t, a) for t, a in tags
            if a.get("id", "").startswith("cell-")}


# --------------------------------------------------------------------------
# Step 1 pins — grid, anchors, exclusion vs not-measured
# --------------------------------------------------------------------------

def test_every_grid_cell_has_its_anchor(tags, meta):
    ids = {a["id"] for _, a in tags if "id" in a}
    for fw in meta["framework_order"]:
        for sc in meta["scenario_order"]:
            anchor = build.cell_anchor(fw, sc)   # shared helper, not hardcoded
            assert anchor in ids, f"missing DOM anchor {anchor}"


def test_no_framework_scenario_pair_missing(tags, meta):
    n = len(meta["framework_order"]) * len(meta["scenario_order"])
    assert len(cells_by_id(tags)) == n == 192


def test_result_cells_carry_microdata(tags):
    _, cell = cells_by_id(tags)["cell-fraiseql-tv-Q1"]
    assert cell.get("data-framework") == "fraiseql-tv"
    assert cell.get("data-scenario") == "Q1"
    assert cell.get("data-rps") == "8182.3"
    assert "data-p99-ms" in cell and "data-errors" in cell


def test_excluded_cells_flagged_and_reasoned(tags, meta, index_html):
    _, cell = cells_by_id(tags)["cell-hasura-M1d"]
    assert cell.get("data-excluded") == "true"
    assert cell.get("data-reason-id") == "3"
    # the verbatim reason text is present in the page (exclusion key)
    reason = meta["exclusion_reasons"]["3"]
    assert reason in index_html


def test_not_measured_cells_are_distinct_from_excluded(tags):
    _, nm = cells_by_id(tags)["cell-actix-web-rest-Q3"]
    assert nm.get("data-not-measured") == "true"
    assert "data-excluded" not in nm
    _, ex = cells_by_id(tags)["cell-hasura-M1d"]
    assert "data-not-measured" not in ex


# --------------------------------------------------------------------------
# Step 2 pins — honesty devices
# --------------------------------------------------------------------------

def test_tview_trigger_scope_visible(index_html, sweep3_run):
    assert sweep3_run.environment["tview_trigger_scope"] in index_html
    assert "fraiseql-only" in index_html


def test_q1_toast_note_present_verbatim(index_html, meta):
    assert meta["notes"]["q1_toast"] in index_html


def test_all_reading_notes_sourced_from_scenarios_json(index_html, meta):
    for key in ("same_run", "tview_scope", "mc1_workflow", "not_measured"):
        assert meta["notes"][key] in index_html, f"note {key} not rendered"


def test_zero_error_badge_count_matches_zero_error_cells(index_html, grid):
    zero_err_cells = sum(1 for c in grid.cells.values() if c.ok)
    # count the class attribute exactly (not the CSS rule token)
    rendered_badges = index_html.count('class="cell zero-err"')
    assert rendered_badges == zero_err_cells == 118


def test_methodology_block_renders_environment(index_html, sweep3_run):
    env = sweep3_run.environment
    for key in ("cpu_model", "kernel", "postgres_version", "load_generator"):
        assert str(env[key]) in index_html


def test_error_cell_is_greyed_with_breakdown(tmp_path, meta):
    """A cell with errors>0 must grey out and expose its breakdown — verified
    with a synthetic run since sweep-3 has zero errors everywhere."""
    doc = {
        "environment": {"target_host": "10.7.0.2", "timestamp": "t",
                        "tview_mode": "logged",
                        "tview_trigger_scope": "fraiseql-only"},
        "framework_versions": {"fraiseql-tv": "2.10.0"},
        "results": [{
            "framework": "fraiseql-tv", "query": "Q1", "pass": 1,
            "rps": 12.0, "p50_ms": 1.0, "p95_ms": 2.0, "p99_ms": 3.0,
            "requests": 100, "errors": 7,
            "error_breakdown": {"http_500": 7}, "skipped": False,
            "skip_reason": "",
        }],
        "resource_metrics": [], "db_footprint": [],
    }
    p = tmp_path / "err.json"
    p.write_text(json.dumps(doc))
    html = build.render(build.load_run(p), meta)["index.html"].decode()
    assert "has-err" in html
    assert "http_500" in html and "7 errors" in html


# --------------------------------------------------------------------------
# Step 3 [TDD] — data.json + llms.txt + offline audit
# --------------------------------------------------------------------------

def test_data_json_round_trips(built, sweep3_run, meta):
    data = json.loads(built["data.json"].decode("utf-8"))
    assert data == {"run": sweep3_run.raw, "scenarios": meta,
                    "costs": build.load_prices(build.COSTS_PATH)}


def test_llms_txt_describes_structure(built):
    txt = built["llms.txt"].decode("utf-8")
    assert "one" in txt.lower() and "run" in txt.lower()
    assert "excluded by design" in txt.lower()
    assert "not measured in this run" in txt.lower()
    assert "#cell-" in txt                      # anchor scheme
    assert 'named "query"' in txt or "not \"scenario\"" in txt.lower()
    assert "M1d" in txt and "jsonb-delta" in txt  # mechanism distinction


def test_dist_is_offline(built):
    pattern = re.compile(rb"https?://")
    for name, data in built.items():
        assert not pattern.search(data), f"external URL reference in {name}"
