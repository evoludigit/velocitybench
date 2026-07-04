"""MC1 wiring for the schema-to-API engines.

MC1 is the mutation-to-consistent-state *workflow* benchmark, deliberately
asymmetric: FraiseQL's mutation response carries the cascade (1 request per
cycle), while classical engines need a mutation followed by a serial Q1
re-fetch (2 requests per cycle). Hasura and PostGraphile must run the
classical form so the report's central comparison includes them.
"""

import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential  # noqa: E402

FRAMEWORKS = bench_sequential.FRAMEWORKS


def test_hasura_has_mc1_sentinel():
    assert FRAMEWORKS["hasura"]["queries"].get("MC1") == "MC1"


def test_postgraphile_has_m1_and_mc1_sentinels():
    queries = FRAMEWORKS["postgraphile"]["queries"]
    assert queries.get("M1") == "M1"
    assert queries.get("MC1") == "MC1"


def test_postgraphile_m1_template_is_v5_shape():
    tmpl = FRAMEWORKS["postgraphile"].get("m1_template", "")
    assert "updateTbUserByRowId" in tmpl, (
        "postgraphile M1 must use the v5 update-by-rowId mutation"
    )


def test_schema_engines_use_classical_mc1():
    """m1_template != 'fraiseql' routes MC1 to the 2-request classical cycle."""
    for fw in ("hasura", "postgraphile"):
        assert FRAMEWORKS[fw].get("m1_template") not in (None, "fraiseql"), (
            f"{fw} must define a classical mutation template"
        )


def test_fraiseql_keeps_cascade_mc1():
    for fw in ("fraiseql-tv", "fraiseql-tv-cache", "fraiseql-v-nocache", "fraiseql-v-cache"):
        assert FRAMEWORKS[fw]["m1_template"] == "fraiseql"
        assert FRAMEWORKS[fw]["queries"].get("MC1") == "MC1"


def test_mc1_asymmetry_documented_in_report_output():
    """The workflow-benchmark labeling must be generated into every report."""
    desc = bench_sequential._QUERY_LABELS["MC1"]
    assert "1 request" in desc and "2 serial requests" in desc
