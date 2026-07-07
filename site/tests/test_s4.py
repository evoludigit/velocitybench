"""S4 caching-under-fire data model.

Test-first, recomputed from the sweep-3 grid. The honesty stake here is the
whole point of the section: a cache that earns nothing must be shown earning
nothing. So the invariants exist as tests before the code:

  * C3 (miss regime) and HC3 (hit regime) are paired per FraiseQL variant, with
    the delta computed HC3-over-C3 from the grid — never chart-only arithmetic;
  * a delta that is ~zero or negative in this run stays ~zero/negative (the
    cache-on tv+cache variant is actually a touch slower on the hot pool);
  * cache-off variants (v, tv) are present beside cache-on (v+cache, tv+cache)
    so the flatness of the no-cache rows is itself visible information;
  * the resolver/REST engines that were not run on C3/HC3 read
    not-measured-in-this-run — distinct from excluded, never a fabricated bar;
  * the M1-only audit appendix row never appears.
"""
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


def test_cache_pairs_miss_hit_scenarios_from_meta(grid, meta):
    view = build.cache_pairs(grid)
    cfg = meta["cache_under_fire"]
    assert view.miss == cfg["miss"] == "C3"
    assert view.hit == cfg["hit"] == "HC3"


def test_cache_variant_order_and_cache_state_from_meta(grid, meta):
    view = build.cache_pairs(grid)
    cfg = meta["cache_under_fire"]["variants"]
    assert [r.framework for r in view.variants] == [v["framework"] for v in cfg]
    assert [r.cache_on for r in view.variants] == [v["cache"] for v in cfg]
    # cache-off and cache-on are both present, so the flat no-cache rows show
    assert [r.cache_on for r in view.variants] == [False, True, False, True]


def variant(view, fw):
    return next(r for r in view.variants if r.framework == fw)


def test_cache_all_four_variants_are_results(grid):
    view = build.cache_pairs(grid)
    assert all(r.status == "result" for r in view.variants)
    assert len(view.variants) == 4


def test_cache_delta_is_flat_where_cache_cannot_help(grid):
    """v-nocache / v-cache / tv all land flat between miss and hit — a single-row
    read is already too cheap for the cache (or the hot pool) to matter."""
    view = build.cache_pairs(grid)
    vn = variant(view, "fraiseql-v-nocache")
    assert vn.delta.direction == "flat"
    assert round(vn.miss_rps, 1) == 9587.5 and round(vn.hit_rps, 1) == 9634.5
    assert round(vn.delta.abs, 1) == 47.0 and round(vn.delta.pct, 1) == 0.5

    vc = variant(view, "fraiseql-v-cache")
    assert vc.delta.direction == "flat"          # +1.463% — just under the band
    assert round(vc.delta.abs, 1) == 139.5

    tv = variant(view, "fraiseql-tv")
    assert tv.delta.direction == "flat"
    assert round(tv.delta.pct, 1) == 0.3


def test_cache_on_tv_cache_is_slightly_slower_on_hot_pool(grid):
    """The honesty punchline: the cache-on tv+cache variant is *slower* in the
    hit regime this run — rendered as-is, never hidden."""
    view = build.cache_pairs(grid)
    tvc = variant(view, "fraiseql-tv-cache")
    assert round(tvc.miss_rps, 1) == 10078.2 and round(tvc.hit_rps, 1) == 9909.1
    assert tvc.delta.direction == "down"
    assert tvc.delta.abs < 0
    assert round(tvc.delta.abs, 1) == -169.1 and round(tvc.delta.pct, 1) == -1.7


def test_cache_deltas_recomputed_from_grid(grid):
    view = build.cache_pairs(grid)
    for r in view.variants:
        recomputed = r.hit_rps - r.miss_rps
        assert round(r.delta.abs, 4) == round(recomputed, 4)


def test_cache_coverage_resolver_engines_not_measured(grid):
    """actix/apollo/async/hasura/mercurius/postgraphile/strawberry were not run
    on C3/HC3 in sweep-3 — present as not-measured, not excluded, no delta."""
    view = build.cache_pairs(grid)
    cov = {r.framework: r for r in view.coverage}
    for fw in ("actix-web-rest", "apollo-server", "async-graphql", "hasura",
               "mercurius", "postgraphile", "strawberry"):
        assert cov[fw].status == "not_measured"
        assert cov[fw].delta is None
        assert cov[fw].reason_id is None


def test_cache_coverage_ordered_results_then_rest(grid):
    view = build.cache_pairs(grid)
    ranks = [{"result": 0, "not_measured": 1, "excluded": 2}[r.status]
             for r in view.coverage]
    assert ranks == sorted(ranks)


def test_cache_appendix_audit_row_never_appears(grid):
    view = build.cache_pairs(grid)
    everyone = [r.framework for r in view.variants + view.coverage]
    assert "fraiseql-tv-audit" not in everyone


# --------------------------------------------------------------------------
# S4 markup pins (written after the design
# settled; they guard the honesty-critical invariants when the grid or styling
# changes).
# --------------------------------------------------------------------------

import re  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture()
def page(sweep3_run, meta):
    return build.render(sweep3_run, meta)["index.html"].decode("utf-8")


def s4(page):
    m = re.search(r'<section id="s4-cache-under-fire".*?</section>', page,
                  re.DOTALL)
    assert m, "S4 section missing"
    return m.group(0)


def test_s4_anchored_between_s3_and_s5(page):
    assert 'id="s4-cache-under-fire"' in page
    assert page.index('id="s3-apq"') < page.index('id="s4-cache-under-fire"')
    assert page.index('id="s4-cache-under-fire"') < page.index('id="s6-footprint"')


def test_s4_both_regimes_explained_before_the_bars(page, meta):
    sec = s4(page)
    reg = meta["cache_under_fire"]["regimes"]
    assert reg["miss"] in sec and reg["hit"] in sec
    # the regimes come before the first bar so the reader understands them first
    assert sec.index("Miss regime") < sec.index('class="s4-chart"')
    assert sec.index("Hit regime") < sec.index('class="s4-chart"')


def test_s4_four_variants_with_cache_state_badges(page):
    sec = s4(page)
    # cache off / on / off / on in the config order (no-cache rows present)
    assert re.findall(r'data-cache="(\w+)"', sec) == ["off", "on", "off", "on"]
    assert sec.count("s4-badge-on") == 2 and sec.count("s4-badge-off") == 2


def test_s4_bars_from_zero(page):
    sec = s4(page)
    assert 's4-axis' in sec and '<span>0</span>' in sec


def test_s4_tv_cache_negative_delta_shown_as_is(page):
    """The cache-on tv+cache variant is slower on the hot pool — its chip is the
    down/negative delta, verbatim, never softened."""
    sec = s4(page)
    m = re.search(r'data-framework="fraiseql-tv-cache".*?</div>\s*<div class="s4-barline',
                  sec, re.DOTALL)
    assert m and 's4-delta dir-down' in m.group(0)
    assert '−169 RPS (−1.7%)' in m.group(0)


def test_s4_coverage_lists_not_measured_engines(page):
    sec = s4(page)
    cov = re.search(r's4-cov-list nm">(.*?)</ul>', sec, re.DOTALL).group(1)
    assert cov.count("<li") == 7
    assert 'fraiseql-tv-audit' not in sec       # appendix never rendered


def test_s4_hotkey_workload_card_resolves_to_this_section(page):
    """The earlier stub pointed the hot-key card at section: null; it now
    resolves to the real S4 anchor."""
    assert 'href="#s4-cache-under-fire"' in page


def test_llms_txt_carries_cache_under_fire(sweep3_run, meta):
    """S4 in llms.txt keeps the finding (hit-over-miss delta, which can go
    negative) and the coverage honesty: the classical engines are not measured
    here — not excluded, and not slow."""
    txt = build.render(sweep3_run, meta)["llms.txt"].decode("utf-8")
    assert "CACHE UNDER FIRE (S4)" in txt and "delta = hit over miss" in txt
    assert "not measured this run (classical" in txt
