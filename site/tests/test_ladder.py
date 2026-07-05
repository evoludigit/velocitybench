"""Phase 03 Step 1 [TDD] — ladder data extraction for the S1 nesting cliff."""
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


def test_rungs_follow_ladder_pos(meta):
    rungs = build.ladder_rungs(meta, "nesting")
    assert [sc for sc, _ in rungs] == ["Q1", "Q2", "Q2b", "Q3", "T1"]
    assert [pos for _, pos in rungs] == [0, 1, 2, 3, 4]


def test_series_omits_frameworks_with_no_ladder_result(grid):
    frameworks = {s.framework for s in build.ladder_series(grid)}
    # fraiseql-tv-audit measures M1 only — never a ladder line
    assert "fraiseql-tv-audit" not in frameworks
    assert len(frameworks) == 11


def test_full_line_framework_has_five_result_points(grid):
    s = next(s for s in build.ladder_series(grid)
             if s.framework == "fraiseql-tv")
    assert [p.scenario for p in s.points] == ["Q1", "Q2", "Q2b", "Q3", "T1"]
    assert all(p.status == "result" for p in s.points)
    assert round(s.points[0].rps, 1) == 8182.3
    assert len(s.segments()) == 1               # one unbroken line
    assert len(s.segments()[0]) == 5


def test_missing_rung_breaks_the_line(grid):
    """actix-web-rest has no Q3 (not measured); the line must break, not
    interpolate Q2b -> T1."""
    s = next(s for s in build.ladder_series(grid)
             if s.framework == "actix-web-rest")
    q3 = next(p for p in s.points if p.scenario == "Q3")
    assert q3.status == "not_measured" and q3.rps is None
    segs = s.segments()
    assert len(segs) == 2                        # Q1-Q2-Q2b | T1
    assert [p.scenario for p in segs[0]] == ["Q1", "Q2", "Q2b"]
    assert [p.scenario for p in segs[1]] == ["T1"]


def test_ladder_generic_over_name(grid):
    assert build.ladder_series(grid, "does-not-exist") == []
