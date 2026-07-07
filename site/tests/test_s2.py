"""S2 mechanism-ladder markup pins.

Written after the ladder design settled. They guard the honesty-critical
invariants when the grid or styling changes: the section is anchored and placed
between S0 and S5, the default scenario is pre-rendered (no-JS story), every rung
is labelled by its mechanism from scenarios.json (not hardcoded), the deltas on
the page equal the recomputed values, bars are absolute (axis starts at 0), and
the +APQ rung is a real bar only where an _APQ twin was measured.
"""
import re
import sys
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


@pytest.fixture()
def page(sweep3_run, meta):
    return build.render(sweep3_run, meta)["index.html"].decode("utf-8")


def section(page):
    m = re.search(r'<section id="s2-mechanism-ladder".*?</section>', page,
                  re.DOTALL)
    assert m, "S2 section missing"
    return m.group(0)


def variant(page, scenario):
    m = re.search(
        rf'<div class="s2-variant" data-scenario="{scenario}"[^>]*>'
        r'.*?(?=<div class="s2-variant"|</div><p class="footnote)',
        section(page), re.DOTALL)
    assert m, f"no s2 variant for {scenario}"
    return m.group(0)


def test_section_anchored_between_s0_and_s5(page):
    assert 'id="s2-mechanism-ladder"' in page
    i_s0 = page.index('id="s0-request-anatomy"')
    i_s2 = page.index('id="s2-mechanism-ladder"')
    i_s5 = page.index('id="s5-write-trade"')
    assert i_s0 < i_s2 < i_s5


def test_default_variant_prerendered_visible_others_hidden(page, meta):
    default_sc = meta["mechanism_ladder"]["default_scenario"]
    sec = section(page)
    # the default variant is present WITHOUT the hidden attribute (no-JS story)
    assert re.search(
        rf'<div class="s2-variant" data-scenario="{default_sc}">', sec)
    for sc in meta["mechanism_ladder"]["scenarios"]:
        if sc != default_sc:
            assert re.search(
                rf'<div class="s2-variant" data-scenario="{sc}" hidden>', sec)


def test_all_ladder_scenarios_rendered(page, meta):
    scns = re.findall(r'<div class="s2-variant" data-scenario="([^"]+)"',
                      section(page))
    assert scns == meta["mechanism_ladder"]["scenarios"]


def test_variant_order_and_mechanism_labels_from_meta(page, meta):
    """Rung order + mechanism labels are scenarios.json's, not hardcoded."""
    v = variant(page, meta["mechanism_ladder"]["default_scenario"])
    # non-APQ rungs only (the +APQ rung reuses the base variant's framework)
    fws = re.findall(r'<div class="s2-rung" data-framework="([^"]+)"', v)
    assert fws == [x["framework"]
                   for x in meta["mechanism_ladder"]["variants"]]
    mechs = re.findall(r'data-mechanism="([^"]+)"', v)
    expect = [x["mechanism"] for x in meta["mechanism_ladder"]["variants"]]
    expect.append(meta["mechanism_ladder"]["apq_rung"]["mechanism"])
    assert mechs == expect


def test_precompute_is_the_visible_win_delta_matches_recompute(page, grid):
    """The tv-precompute rung carries the big up-delta, recomputed here, not
    trusted from the page."""
    rungs = build.mechanism_ladder(grid, "Q2b")
    tv = next(r for r in rungs if r.framework == "fraiseql-tv" and not r.is_apq)
    chip = build.fmt_delta(tv.delta, "RPS")
    assert chip in variant(page, "Q2b")
    assert "+56.0%" in chip and "▲" in chip


def test_flat_rung_marked_flat_not_up(page, grid):
    """The + result cache rung earns ~nothing → dir-flat, never dressed as a
    gain."""
    v = variant(page, "Q2b")
    assert 's2-delta dir-flat' in v            # v+cache is flat
    # and the honest sign is preserved in the text
    rungs = {r.framework: r for r in build.mechanism_ladder(grid, "Q2b")}
    assert build.fmt_delta(rungs["fraiseql-v-cache"].delta, "RPS") in v


def test_apq_rung_real_for_q2b_na_for_q3(page, grid):
    q2b = variant(page, "Q2b")
    apq = next(r for r in build.mechanism_ladder(grid, "Q2b") if r.is_apq)
    assert build.fmt_delta(apq.delta, "RPS") in q2b        # real negative delta
    assert "▼" in build.fmt_delta(apq.delta, "RPS")
    q3 = variant(page, "Q3")
    assert "no persisted-query twin" in q3                 # na, not a fake bar


def test_axis_starts_at_zero(page):
    sec = section(page)
    assert re.search(r'<div class="s2-axis"[^>]*><span>0</span>', sec)


def test_controls_hidden_until_js(page):
    """Progressive enhancement: the scenario switcher is hidden without JS, the
    pre-rendered default carries the no-JS story."""
    sec = section(page)
    assert '<div class="s2-controls" hidden>' in sec
    scn_btns = re.findall(r'<button class="s2-scn"[^>]*data-scenario="([^"]+)"',
                          sec)
    assert scn_btns == build.load_meta()["mechanism_ladder"]["scenarios"]


def test_every_s2_result_value_is_also_in_the_grid(page, grid, meta):
    """No chart-only numbers: each rung's framework/scenario is a measured grid
    cell (the grid table above holds the same value)."""
    for sc in meta["mechanism_ladder"]["scenarios"]:
        for r in build.mechanism_ladder(grid, sc):
            if r.status == "result":
                cell = grid.cell(r.framework,
                                 build.apq_twin(sc, meta) if r.is_apq else sc)
                assert cell.status == "result" and cell.rps == r.rps


def test_llms_txt_carries_mechanism_ladder(sweep3_run, meta):
    """llms.txt gives an agent the S2 ladder and its load-bearing finding: the
    precompute step is the read win and it grows with nesting depth."""
    txt = build.render(sweep3_run, meta)["llms.txt"].decode("utf-8")
    assert "MECHANISM LADDER (S2)" in txt and "#s2-mechanism-ladder" in txt
    assert "precompute step" in txt and "by depth:" in txt
    for v in meta["mechanism_ladder"]["variants"]:
        assert v["framework"] in txt
