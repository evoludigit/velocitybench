"""Phase 04 Step 1 [TDD] — write-trade data model (M1 / M1d / MC1)."""
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


def group(grid, framework):
    return next(g for g in build.write_trade(grid) if g.framework == framework)


def test_fraiseql_tv_has_both_m1_and_m1d(grid):
    g = group(grid, "fraiseql-tv")
    assert g.rows["M1"].status == "result"
    assert g.rows["M1d"].status == "result"
    assert g.rows["M1"].mechanism == "full-cascade"
    assert g.rows["M1d"].mechanism == "jsonb-delta"
    # full cascade is far slower than the delta patch — the honest trade
    assert g.rows["M1"].rps < g.rows["M1d"].rps


def test_hasura_m1_present_m1d_excluded_reason_3(grid):
    g = group(grid, "hasura")
    assert g.rows["M1"].status == "result"
    assert g.rows["M1"].mechanism == "vanilla-update"
    assert g.rows["M1d"].status == "excluded"
    assert g.rows["M1d"].reason_id == 3


def test_v_cache_m1d_excluded_reason_1(grid):
    g = group(grid, "fraiseql-v-cache")
    assert g.rows["M1d"].status == "excluded"
    assert g.rows["M1d"].reason_id == 1


def test_tv_cache_m1d_is_not_measured_not_excluded(grid):
    g = group(grid, "fraiseql-tv-cache")
    assert g.rows["M1d"].status == "not_measured"
    assert g.rows["M1d"].reason_id is None


def test_audit_row_is_flagged_appendix_m1_only(grid):
    g = group(grid, "fraiseql-tv-audit")
    assert g.appendix is True
    assert g.rows["M1"].status == "result"
    assert g.rows["M1d"].status == "excluded" and g.rows["M1d"].reason_id == 2
    assert g.rows["MC1"].status == "excluded" and g.rows["MC1"].reason_id == 2


def test_mc1_has_no_mutation_mechanism(grid):
    # MC1 is a workflow metric, not a mutation mechanism
    g = group(grid, "fraiseql-tv")
    assert g.rows["MC1"].mechanism is None
