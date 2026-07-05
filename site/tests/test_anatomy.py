"""Phase 05 Step 1 [TDD] — S0 request-anatomy hop model.

The load-bearing honesty rule of S0 is *no invented hops*: every hop the
animation draws must be provenanced to real implementation code, and the
round-trip counts must be structural truth (resolver + DataLoader adds one
batched SQL trip per nesting level; compile-to-SQL and precompute stay at one
trip at any depth). These invariants exist as tests before the renderer.
"""
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SITE_DIR.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402

ANATOMY_SCENARIOS = ("Q1", "Q2b", "Q3")


# --------------------------------------------------------------------------
# Every grid framework is classified; classification is not invented
# --------------------------------------------------------------------------

def test_every_grid_framework_has_a_strategy(meta):
    strat = meta["framework_strategy"]
    known = set(meta["query_strategies"])
    for fw in meta["framework_order"]:
        assert fw in strat, f"{fw} has no query_strategy"
        assert strat[fw] in known, f"{fw} maps to unknown strategy {strat[fw]!r}"


def test_strategy_of_matches_meta(meta):
    for fw in meta["framework_order"]:
        assert build.strategy_of(fw, meta) == meta["framework_strategy"][fw]


def test_each_strategy_names_real_member_frameworks(meta):
    fw_set = set(meta["framework_order"])
    for key, s in meta["query_strategies"].items():
        assert s["members"], f"{key} lists no members"
        for m in s["members"]:
            assert m in fw_set, f"{key} names non-framework member {m!r}"
        assert s["representative"] in s["members"]


def test_members_partition_the_grid_frameworks(meta):
    """Every non-appendix framework is a member of exactly the strategy it is
    classified under. The audit appendix row is classified (it is a tv engine)
    but is never a displayed lane member — it measures M1 only."""
    for fw in meta["framework_order"]:
        owning = [k for k, s in meta["query_strategies"].items()
                  if fw in s["members"]]
        if meta["frameworks"][fw].get("appendix"):
            assert owning == [], f"{fw} is appendix but listed as a lane member"
            continue
        assert owning == [meta["framework_strategy"][fw]], (
            f"{fw} membership is not exactly its declared strategy: {owning}")


# --------------------------------------------------------------------------
# No invented hops — every source resolves to a real file on disk
# --------------------------------------------------------------------------

def test_strategy_sources_exist_on_disk(meta):
    for key, s in meta["query_strategies"].items():
        assert s["source"], f"{key} has no primary source"
        srcs = [s["source"], *s.get("sources", [])]
        for rel in srcs:
            assert rel.startswith("frameworks/"), f"{key} source {rel!r} off-tree"
            assert (REPO_DIR / rel).exists(), f"{key} source missing: {rel}"


def test_every_drawn_hop_carries_a_real_source(meta):
    for key in meta["anatomy"]["lanes"]:
        for sc in ANATOMY_SCENARIOS:
            for hop in build.hop_diagram(key, sc, meta):
                assert hop.source, f"{key}/{sc} hop {hop.n} has no source"
                assert (REPO_DIR / hop.source).exists(), (
                    f"{key}/{sc} hop {hop.n} source missing: {hop.source}")


# --------------------------------------------------------------------------
# Round-trip counts are structural truth
# --------------------------------------------------------------------------

def test_resolver_roundtrips_are_one_per_nesting_level(meta):
    rt = meta["query_strategies"]["resolver-dataloader"]["sql_roundtrips"]
    assert rt == {"Q1": 1, "Q2b": 2, "Q3": 3}
    # and that equals 1 (root) + one batched trip per declared nest level
    for sc in ANATOMY_SCENARIOS:
        levels = meta["read_shape"][sc]["levels"]
        assert rt[sc] == 1 + len(levels), sc


def test_compiler_and_precompute_never_scale_with_depth(meta):
    for key in ("compile-to-sql", "precompute"):
        rt = meta["query_strategies"][key]["sql_roundtrips"]
        assert all(rt[sc] == 1 for sc in ANATOMY_SCENARIOS), key


def test_hop_diagram_sql_matches_declared_roundtrips(meta):
    """The diagram model and the declared count are two independent statements
    of the same truth; they must agree (drift catch)."""
    for key in meta["anatomy"]["lanes"]:
        declared = meta["query_strategies"][key]["sql_roundtrips"]
        for sc in ANATOMY_SCENARIOS:
            hops = build.hop_diagram(key, sc, meta)
            got = sum(h.sql_roundtrips for h in hops)
            assert got == declared[sc], f"{key}/{sc}: {got} != {declared[sc]}"


def test_only_resolver_lane_gains_hops_with_depth(meta):
    def sql_hops(key, sc):
        return sum(1 for h in build.hop_diagram(key, sc, meta)
                   if h.sql_roundtrips)
    # resolver: strictly more SQL hops as nesting deepens
    assert sql_hops("resolver-dataloader", "Q1") == 1
    assert sql_hops("resolver-dataloader", "Q2b") == 2
    assert sql_hops("resolver-dataloader", "Q3") == 3
    # compile / precompute: identical count at every depth
    for key in ("compile-to-sql", "precompute"):
        counts = {sql_hops(key, sc) for sc in ANATOMY_SCENARIOS}
        assert counts == {1}, key


# --------------------------------------------------------------------------
# Diagram model shape — a well-formed, ordered hop list
# --------------------------------------------------------------------------

def test_hop_diagram_is_ordered_and_bookended_by_http(meta):
    hops = build.hop_diagram("resolver-dataloader", "Q3", meta)
    assert [h.n for h in hops] == list(range(1, len(hops) + 1))  # 1..n, ordered
    assert hops[0].kind == "http"       # request in
    assert hops[-1].kind == "http"      # response out
    # a DataLoader batch hop is credited as batched, not N+1
    batched = [h for h in hops if h.kind == "sql" and "batch" in h.label.lower()]
    assert batched, "Q3 resolver diagram must show batched DataLoader hops"
    assert any("ANY($1)" in h.label for h in hops), "batching must be explicit"


def test_resolver_lane_names_the_root_from_read_shape(meta):
    for sc in ANATOMY_SCENARIOS:
        root = meta["read_shape"][sc]["root"]
        hops = build.hop_diagram("resolver-dataloader", sc, meta)
        assert any(root in h.label for h in hops if h.kind == "sql"), sc


# --------------------------------------------------------------------------
# p50 pacing derives from measured JSON, not typed in
# --------------------------------------------------------------------------

def test_lane_representatives_have_measured_p50_for_every_rung(grid, meta):
    for key in meta["anatomy"]["lanes"]:
        rep = meta["query_strategies"][key]["representative"]
        for sc in ANATOMY_SCENARIOS:
            cell = grid.cell(rep, sc)
            assert cell.status == "result" and cell.p50_ms is not None, (
                f"{key} representative {rep} has no p50 for {sc}")


def test_anatomy_duration_is_p50_times_scale(meta):
    scale = meta["anatomy"]["p50_scale_s_per_ms"]
    assert scale == 0.1
    assert build.anatomy_duration(6.57, scale) == round(6.57 * 0.1, 2)
    assert build.anatomy_duration(24.66, scale) == 2.47
