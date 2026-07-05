"""Phase 07 Step 1 [TDD] — S4 caching-under-fire data model.

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
