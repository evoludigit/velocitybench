"""Phase 06 Step 1 [TDD] — S2 mechanism-ladder + S3 APQ-pair data model.

Test-first, recomputed from the sweep-3 grid (never trusted from the page). The
honesty stakes are the same as everywhere on this site: a fabricated APQ delta,
or a not-measured cell dressed up as a result, would discredit the campaign — so
the invariants that guard against that exist as tests before the code:

  * the mechanism ladder's deltas are the real, signed, per-rung changes;
  * the +APQ rung appears only where an _APQ twin was actually measured;
  * APQ deltas that are negative or ~zero in this run stay negative/zero;
  * APQ-capable-but-not-measured (apollo/mercurius/async-graphql here) is
    distinct from excluded-by-design (hasura/postgraphile/actix/strawberry).
"""
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


# --------------------------------------------------------------------------
# delta_of — the shared signed-delta helper (S2 + S3)
# --------------------------------------------------------------------------

def test_delta_of_directions_and_flat_band():
    up = build.delta_of(100.0, 156.0, 1.5)
    assert up.direction == "up" and round(up.pct, 1) == 56.0 and up.abs == 56.0
    down = build.delta_of(100.0, 94.3, 1.5)
    assert down.direction == "down" and down.abs < 0 and round(down.pct, 1) == -5.7
    flat = build.delta_of(5061.2, 5069.2, 1.5)          # +0.2% -> flat, not up
    assert flat.direction == "flat" and flat.abs > 0    # real sign preserved
    zero = build.delta_of(7905.6, 7902.8, 1.5)          # -0.04% -> flat, tiny neg
    assert zero.direction == "flat" and zero.abs < 0


def test_delta_of_zero_prev_is_safe():
    d = build.delta_of(0.0, 10.0, 1.5)
    assert d.pct == 0.0                                 # no ZeroDivisionError


# --------------------------------------------------------------------------
# S2 — mechanism_ladder
# --------------------------------------------------------------------------

def test_ladder_variant_order_and_labels_from_meta(grid, meta):
    rungs = build.mechanism_ladder(grid, "Q2b")
    variants = [r for r in rungs if not r.is_apq]
    cfg = meta["mechanism_ladder"]["variants"]
    assert [r.framework for r in variants] == [v["framework"] for v in cfg]
    # labels are the metadata's, not hardcoded in code
    assert [r.mechanism for r in variants] == [v["mechanism"] for v in cfg]
    assert [r.explain for r in variants] == [v["explain"] for v in cfg]


def test_ladder_q2b_precompute_is_the_win_cache_is_flat(grid):
    rungs = {r.framework: r for r in build.mechanism_ladder(grid, "Q2b")
             if not r.is_apq}
    # first rung is the baseline — no delta
    assert rungs["fraiseql-v-nocache"].delta is None
    # + result cache earns ~nothing -> flat
    assert rungs["fraiseql-v-cache"].delta.direction == "flat"
    # tv precompute is the whole story -> a large up delta
    tv = rungs["fraiseql-tv"].delta
    assert tv.direction == "up" and round(tv.pct, 1) == 56.0
    assert round(tv.abs, 1) == 2836.4
    # + result cache on top of precompute -> small
    assert rungs["fraiseql-tv-cache"].delta.direction in ("flat", "up")
    assert round(rungs["fraiseql-tv-cache"].delta.pct, 1) == 1.9


def test_ladder_apq_rung_present_and_negative_for_q2b(grid):
    apq = next(r for r in build.mechanism_ladder(grid, "Q2b") if r.is_apq)
    assert apq.status == "result"
    assert apq.framework == "fraiseql-tv-cache"          # base_variant
    # APQ hurts a touch here — the honesty rule: render it as-is
    assert apq.delta.direction == "down"
    assert round(apq.delta.pct, 1) == -5.7


def test_ladder_apq_rung_na_when_no_twin(grid, meta):
    """Q3/T1 have no _APQ twin measured — the +APQ rung is 'na' with a reason,
    never a fabricated bar."""
    for sc in ("Q2", "Q3", "T1"):
        apq = next(r for r in build.mechanism_ladder(grid, sc) if r.is_apq)
        assert apq.status == "na"
        assert apq.rps is None and apq.delta is None
        assert apq.note == meta["mechanism_ladder"]["apq_rung"]["no_twin_note"]


def test_ladder_deltas_recomputed_from_grid(grid):
    """Every rung's delta equals the recomputed change over the previous result
    rung — no chart-only arithmetic."""
    for sc in meta_scenarios(grid):
        rungs = build.mechanism_ladder(grid, sc)
        last = None
        for r in rungs:
            if r.status == "result":
                if last is not None:
                    assert round(r.delta.abs, 4) == round(r.rps - last, 4)
                last = r.rps


def meta_scenarios(grid):
    return grid.meta["mechanism_ladder"]["scenarios"]


# --------------------------------------------------------------------------
# S3 — apq_pairs
# --------------------------------------------------------------------------

def test_apq_three_pairs_in_order(grid):
    groups = build.apq_pairs(grid)
    assert [(g.base, g.apq) for g in groups] == [
        ("Q1", "Q1_APQ"), ("Q2b", "Q2b_APQ"), ("M1", "M1_APQ")]


def cell(groups, base, fw):
    g = next(g for g in groups if g.base == base)
    return next(c for c in g.cells if c.framework == fw)


def test_apq_fraiseql_pairs_are_real_and_negative_in_this_run(grid):
    groups = build.apq_pairs(grid)
    q1_tv = cell(groups, "Q1", "fraiseql-tv")
    assert q1_tv.status == "result"
    assert round(q1_tv.base_rps, 1) == 8182.3
    assert round(q1_tv.apq_rps, 1) == 7947.4
    assert q1_tv.delta.direction == "down"              # APQ does not help
    assert round(q1_tv.delta.pct, 1) == -2.9
    # Q2b on fraiseql-tv is ~zero -> flat, and slightly negative
    q2b_tv = cell(groups, "Q2b", "fraiseql-tv")
    assert q2b_tv.delta.direction == "flat" and q2b_tv.delta.abs < 0


def test_apq_resolver_engines_are_not_measured_not_excluded(grid):
    """apollo/mercurius/async-graphql CAN do APQ but their twin was not run in
    sweep-3 — they must read not-measured (base shown, no delta), never a
    fabricated arrow and never a by-design exclusion."""
    groups = build.apq_pairs(grid)
    for fw in ("apollo-server", "mercurius", "async-graphql"):
        c = cell(groups, "Q1", fw)
        assert c.status == "not_measured"
        assert c.delta is None
        assert c.reason_id is None
        assert c.base_rps is not None                   # the before is measured


def test_apq_non_apq_engines_excluded_with_verbatim_reason(grid, meta):
    groups = build.apq_pairs(grid)
    reasons = meta["exclusion_reasons"]
    for fw, rid in (("hasura", 4), ("postgraphile", 5),
                    ("actix-web-rest", 6), ("strawberry", 7)):
        c = cell(groups, "Q1", fw)
        assert c.status == "excluded"
        assert c.reason_id == rid
        assert c.reason == reasons[str(rid)]            # verbatim, not paraphrased
        assert c.delta is None


def test_apq_rows_order_results_then_excluded(grid):
    """Meaningful arrows lead; greyed excluded reasons trail (present, not
    dropped)."""
    groups = build.apq_pairs(grid)
    for g in groups:
        ranks = [{"result": 0, "not_measured": 1, "excluded": 2}[c.status]
                 for c in g.cells]
        assert ranks == sorted(ranks)


def test_apq_appendix_row_never_appears(grid):
    groups = build.apq_pairs(grid)
    for g in groups:
        assert all(c.framework != "fraiseql-tv-audit" for c in g.cells)
