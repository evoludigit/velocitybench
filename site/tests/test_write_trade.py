"""Write-trade data model (M1 / MC1)."""
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


def group(grid, framework):
    return next(g for g in build.write_trade(grid) if g.framework == framework)


def test_write_trade_rows_are_m1_and_mc1_only(grid):
    g = group(grid, "fraiseql-tv")
    assert set(g.rows) == {"M1", "MC1"}


def test_fraiseql_tv_m1_is_full_cascade(grid):
    g = group(grid, "fraiseql-tv")
    assert g.rows["M1"].status == "result"
    assert g.rows["M1"].mechanism == "full-cascade"
    # the integrated cascade is the honest, slow write
    assert g.rows["M1"].rps is not None and g.rows["M1"].rps > 0


def test_hasura_m1_is_vanilla_update(grid):
    g = group(grid, "hasura")
    assert g.rows["M1"].status == "result"
    assert g.rows["M1"].mechanism == "vanilla-update"


def test_fraiseql_full_cascade_far_slower_than_classical_m1(grid):
    """The honest trade: FraiseQL's integrated cascade write is far slower than
    a classical vanilla UPDATE on the same axis."""
    ft = group(grid, "fraiseql-tv").rows["M1"].rps
    classical = [group(grid, fw).rows["M1"].rps
                 for fw in ("hasura", "postgraphile", "async-graphql", "mercurius")]
    assert ft is not None and all(c is not None for c in classical)
    assert max(classical) > 20 * ft


def test_audit_row_is_flagged_appendix_m1_only(grid):
    g = group(grid, "fraiseql-tv-audit")
    assert g.appendix is True
    assert g.rows["M1"].status == "result"
    assert g.rows["MC1"].status == "excluded" and g.rows["MC1"].reason_id == 2


def test_mc1_has_no_mutation_mechanism(grid):
    # MC1 is a workflow metric, not a mutation mechanism
    g = group(grid, "fraiseql-tv")
    assert g.rows["MC1"].mechanism is None
