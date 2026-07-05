"""Phase 07b Step 1 [TDD] — S7 amortization model.

Test-first, recomputed from the sweep-3 grid. This view is a misleading-chart
minefield (see project_m1_scenario_invalid: conflating mechanisms is exactly
what invalidated the historical M1 numbers), so the invariants exist as tests
before the code:

  * the cost layer is sustainable throughput from measured rps — at r→0 the
    write rps, at r→∞ the read rps, both traceable to grid cells;
  * the structural-count layer is round-trips from the S0 hop model, kept
    SEPARATE — never merged into the cost number;
  * a cascade write whose fan-out this run did not measure yields a None count,
    never a silent zero;
  * break-evens are the real crossovers of the cost curves, computed from data;
  * a series missing its read or write cell degrades with a status.
"""
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


def series(amort, fw):
    return next(s for s in amort.series if s.framework == fw)


def test_amort_series_are_the_four_architecture_reps(grid, meta):
    a = build.amortize(grid, meta)          # defaults: read Q2b, write full
    assert a.read == "Q2b" and a.write == "full"
    assert {s.framework for s in a.series} == {
        "fraiseql-tv", "postgraphile", "async-graphql", "actix-web-rest"}
    assert series(a, "fraiseql-tv").architecture == "precompute"


def test_amort_cost_endpoints_are_measured_rps(grid, meta):
    """r→0 collapses to the measured write rps, r→∞ to the measured read rps —
    the curve interpolates between two grid cells."""
    ft = series(build.amortize(grid, meta), "fraiseql-tv")
    assert round(ft.read_rps, 1) == 7905.6   # Q2b
    assert round(ft.write_rps, 1) == 98.8    # M1 full cascade
    assert round(ft.sustainable_rps(0.0), 1) == round(ft.write_rps, 1)
    # r = 1e6 ~ read-only asymptote
    assert abs(ft.sustainable_rps(1_000_000) - ft.read_rps) < 5


def test_amort_full_cascade_makes_fraiseql_lose_write_heavy(grid, meta):
    """At 1 read : 1 write the logged cascade dominates — FraiseQL sustains far
    less than the resolver engine. The honest write-heavy loss, shown as-is."""
    a = build.amortize(grid, meta, "Q2b", "full")
    ft = series(a, "fraiseql-tv").sustainable_rps(1)
    ag = series(a, "async-graphql").sustainable_rps(1)
    assert round(ft, 1) == 195.2
    assert ag > ft * 30                      # async ~6685 vs fraiseql ~195


def test_amort_read_heavy_flips_to_fraiseql(grid, meta):
    a = build.amortize(grid, meta, "Q2b", "full")
    ft = series(a, "fraiseql-tv").sustainable_rps(1000)
    ag = series(a, "async-graphql").sustainable_rps(1000)
    assert round(ft, 1) == 7327.2
    assert ft > ag                           # 7327 > 5588: precompute wins reads


def test_amort_breakevens_recomputed_from_grid(grid, meta):
    a = build.amortize(grid, meta, "Q2b", "full")
    be = {b.other: b for b in a.breakevens}
    assert round(be["async-graphql"].ratio, 2) == 190.49
    assert round(be["postgraphile"].ratio, 2) == 37.94
    assert round(be["actix-web-rest"].ratio, 2) == 127.20
    assert all(b.anchor_wins_above for b in a.breakevens)  # reads faster than all


def test_amort_breakeven_equals_curve_crossing(grid, meta):
    """The reported r* is exactly where the two sustainable-rps curves meet."""
    a = build.amortize(grid, meta, "Q2b", "full")
    be = next(b for b in a.breakevens if b.other == "async-graphql")
    ft, ag = series(a, "fraiseql-tv"), series(a, "async-graphql")
    at = ft.sustainable_rps(be.ratio)
    bt = ag.sustainable_rps(be.ratio)
    assert abs(at - bt) < 1e-6               # curves actually cross there


def test_amort_count_layer_is_roundtrips_not_cost(grid, meta):
    """Structural count = r·read_trips + write_trips from the S0 hop model,
    separate from the cost curve. A resolver read costs more trips than a
    compiler/precompute read."""
    a = build.amortize(grid, meta, "Q2b", "full")
    assert series(a, "async-graphql").read_trips == 2      # 2 trips at Q2b
    assert series(a, "postgraphile").read_trips == 1
    assert series(a, "actix-web-rest").count(10) == 11     # 10·1 + 1
    assert series(a, "async-graphql").count(10) == 21      # 10·2 + 1


def test_amort_unmeasured_cascade_count_is_none_not_zero(grid, meta):
    """Full-cascade fan-out is not measured in this run — the count layer says
    so (None), never a silent zero. The cost layer still works from M1 rps."""
    a = build.amortize(grid, meta, "Q2b", "full")
    ft = series(a, "fraiseql-tv")
    assert ft.write_trips is None
    assert ft.count(100) is None                           # can't fake the write count
    assert ft.sustainable_rps(100) is not None             # cost layer unaffected


def test_amort_delta_mode_uses_m1d_and_counts_one(grid, meta):
    """The delta write mode swaps FraiseQL to its measured jsonb-delta path;
    then the write is one patch and FraiseQL is fast at every ratio."""
    a = build.amortize(grid, meta, "Q2b", "delta")
    ft = series(a, "fraiseql-tv")
    assert ft.write_scenario == "M1d"
    assert round(ft.write_rps, 1) == 8641.9
    assert ft.write_trips == 1
    assert ft.count(100) == 101                            # 100·1 + 1
    # fast reads + fast writes: FraiseQL leads the field at a 1:1 mix now
    assert ft.sustainable_rps(1) > series(a, "async-graphql").sustainable_rps(1)


def test_amort_missing_read_cell_degrades(grid, meta):
    """Actix has no Q3 in sweep-3 — its series is present but marked no_read,
    never plotted with a zero."""
    a = build.amortize(grid, meta, "Q3", "full")
    actix = series(a, "actix-web-rest")
    assert actix.status == "no_read"
    assert actix.read_rps is None
    assert actix.sustainable_rps(100) is None
    # and it sorts after the ok series
    assert [s.status for s in a.series] == sorted(
        [s.status for s in a.series], key=lambda st: st != "ok")


# --------------------------------------------------------------------------
# Phase 07b Step 2 [design→pin] — S7 markup pins (written after the chart
# design settled; they guard the honesty-critical invariants).
# --------------------------------------------------------------------------

import re  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture()
def page(sweep3_run, meta):
    return build.render(sweep3_run, meta)["index.html"].decode("utf-8")


def s7(page):
    m = re.search(r'<section id="s7-amortization".*?</section>', page, re.DOTALL)
    assert m, "S7 section missing"
    return m.group(0)


def panel(page, read, write):
    m = re.search(
        rf'<div class="s7-panel"[^>]*data-read="{read}"[^>]*data-write="{write}".*?'
        r'(?=<div class="s7-panel"|</div><p class="s7-layer-note)',
        s7(page), re.DOTALL)
    assert m, f"no s7 panel {read}/{write}"
    return m.group(0)


def test_s7_anchored_after_s6_before_selector(page):
    assert (page.index('id="s6-footprint"') < page.index('id="s7-amortization"')
            < page.index('id="workload-selector"'))


def test_s7_cost_is_the_default_layer(page):
    """The default panel leads with the cost SVG visible and the count SVG
    hidden — cost decides the winner, count is opt-in secondary."""
    p = panel(page, "Q2b", "full")
    assert re.search(r'<svg class="s7-svg s7-cost" viewBox', p)     # not hidden
    assert '<svg class="s7-svg s7-count" hidden' in p


def test_s7_illustrative_caveat_present(page, meta):
    sec = s7(page)
    assert 's7-caveat' in sec and 'Illustrative model' in sec
    assert meta["amortization"]["caveat"] in sec


def test_s7_crossovers_recomputed_and_marked(page):
    """The three break-even markers on the default cost chart equal the model's
    computed crossovers — never typed in."""
    cost = re.search(r'<svg class="s7-svg s7-cost" viewBox.*?</svg>',
                     panel(page, "Q2b", "full"), re.DOTALL).group(0)
    for r in ("≈38", "≈127", "≈190"):
        assert r in cost


def test_s7_breakeven_sentence_matches_model(sweep3_run, meta, page):
    grid = build.build_grid(sweep3_run, meta)
    a = build.amortize(grid, meta, "Q2b", "full")
    be = {b.other: round(b.ratio) for b in a.breakevens}
    sent = re.search(r's7-breakeven">(.*?)</p>', panel(page, "Q2b", "full"),
                     re.DOTALL).group(1)
    assert f'≈{be["async-graphql"]}' in sent      # 190, from the model
    assert "overtakes" in sent


def test_s7_count_layer_labelled_structural_not_cost(page):
    count = re.search(r'<svg class="s7-svg s7-count".*?</svg>',
                      panel(page, "Q2b", "full"), re.DOTALL).group(0)
    assert "structural" in count and "not cost" in count.lower()


def test_s7_count_omits_unmeasured_cascade_with_note(page):
    """In full-cascade mode FraiseQL's write count is unmeasured, so its line is
    absent from the count layer and an in-chart note says why — never a zero."""
    count = re.search(r'<svg class="s7-svg s7-count".*?</svg>',
                      panel(page, "Q2b", "full"), re.DOTALL).group(0)
    assert 'data-framework="fraiseql-tv"' not in count
    assert "cascade fan-out not measured" in count


def test_s7_delta_mode_leads_everywhere(page):
    sent = re.search(r's7-breakeven">(.*?)</p>', panel(page, "Q2b", "delta"),
                     re.DOTALL).group(1)
    assert "leads every architecture" in sent


def test_s7_provenance_data_attrs_on_lines(page):
    """Every plotted line carries its framework so a reader can trace it to the
    grid cell above (no chart-only, unsourced numbers)."""
    cost = re.search(r'<svg class="s7-svg s7-cost" viewBox.*?</svg>',
                     panel(page, "Q2b", "full"), re.DOTALL).group(0)
    for fw in ("fraiseql-tv", "postgraphile", "async-graphql", "actix-web-rest"):
        assert f'data-framework="{fw}"' in cost


def test_s7_no_js_preset_table(page):
    """A table of preset ratios → per-engine sustainable rps works without JS."""
    sec = s7(page)
    assert 's7-tbl' in sec
    assert '1:1' in sec and '1000:1' in sec           # preset ratio rows


def test_s7_six_panels_default_visible(page):
    sec = s7(page)
    assert sec.count('class="s7-panel"') == 6         # 3 reads × 2 writes
    # exactly one panel (the default) renders without the hidden attribute
    assert len(re.findall(r'<div class="s7-panel" hidden', sec)) == 5
