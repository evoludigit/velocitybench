"""S0 request-anatomy markup pins.

Written after the markup settled. They guard the honesty-critical invariants of
the movement layer when the grid or styling changes: the section is anchored and
placed as S1's "why" companion, every drawn hop still resolves to real code (no
invented hops), the classical engines are credited as batched (no strawman),
Hasura + PostGraphile are shown as compilers too, the cache path elides a hop,
and the motion never runs before a user gesture / never encodes an unmeasured
pace / derives its durations from measured p50.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SITE_DIR.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402

ANATOMY_SCENARIOS = ("Q1", "Q2b", "Q3")


@pytest.fixture()
def page(sweep3_run, meta):
    return build.render(sweep3_run, meta)["index.html"].decode("utf-8")


def section(page):
    m = re.search(r'<section id="s0-request-anatomy".*?</section>', page,
                  re.DOTALL)
    assert m, "S0 section missing"
    return m.group(0)


def lane_html(page, strategy):
    m = re.search(
        rf'<div class="s0-lane [^"]*" data-strategy="{re.escape(strategy)}">'
        r'.*?(?=<div class="s0-lane |</section>)', section(page), re.DOTALL)
    assert m, f"no lane for {strategy}"
    return m.group(0)


class LiCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hops = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "li" and "s0-hop" in d.get("class", ""):
            self.hops.append(d)


def hops_in(html_str):
    c = LiCollector()
    c.feed(html_str)
    return c.hops


# --------------------------------------------------------------------------
# Step 2 pins — placement, lanes, provenance, no strawman
# --------------------------------------------------------------------------

def test_section_anchored_and_is_s1_why_companion(page):
    """Deep-linkable, and rendered directly between the S1 hero and S5."""
    assert 'id="s0-request-anatomy"' in page
    i_s1 = page.index('id="s1-nesting-cliff"')
    i_s0 = page.index('id="s0-request-anatomy"')
    i_s5 = page.index('id="s5-write-trade"')
    assert i_s1 < i_s0 < i_s5


def test_exactly_three_animated_lanes(page, meta):
    strategies = re.findall(r'data-strategy="([^"]+)"', section(page))
    assert strategies == meta["anatomy"]["lanes"]        # order + count
    assert len(strategies) == 3


def test_every_hop_carries_hop_number_roundtrips_and_source(page):
    hops = hops_in(section(page))
    assert hops, "no hops rendered"
    for h in hops:
        assert "data-hop" in h
        assert "data-sql-roundtrips" in h
        src = h.get("data-source", "")
        assert src.startswith("frameworks/"), f"hop source off-tree: {src!r}"
        assert (REPO_DIR / src).exists(), f"invented hop — missing source {src}"


def test_visible_default_variant_roundtrips_match_model(page, meta):
    """Each lane's shown (non-hidden) variant is the default scenario, and its
    hop <li>s sum to the declared SQL round-trip count."""
    default_sc = meta["anatomy"]["default_scenario"]
    for key in meta["anatomy"]["lanes"]:
        lane = lane_html(page, key)
        # the one variant without hidden is the default scenario
        vis = re.search(
            r'<div class="s0-variant" data-scenario="([^"]+)"(?!\s+hidden)>'
            r'.*?</figure></div>', lane, re.DOTALL)
        assert vis, f"{key} has no visible default variant"
        assert vis.group(1) == default_sc
        rts = [int(h["data-sql-roundtrips"]) for h in hops_in(vis.group(0))]
        declared = meta["query_strategies"][key]["sql_roundtrips"][default_sc]
        assert sum(rts) == declared, f"{key}: {sum(rts)} != {declared}"


def test_dataloader_credit_rendered_verbatim(page, meta):
    assert meta["anatomy"]["dataloader_credit"] in page
    assert "no N+1" in page and "ANY($1)" in page


def test_compile_lane_shows_hasura_and_postgraphile_not_only_fraiseql(page, meta):
    """The section's honesty test: it never pretends FraiseQL is the only
    compiler. Hasura and PostGraphile appear in the compile-to-SQL lane, and
    FraiseQL·v is shown there too — as one compiler among several."""
    lane = lane_html(page, "compile-to-sql")
    assert meta["frameworks"]["hasura"]["label"] in lane
    assert meta["frameworks"]["postgraphile"]["label"] in lane
    assert meta["frameworks"]["fraiseql-v-nocache"]["label"] in lane


def test_resolver_lane_names_all_four_batched_engines(page, meta):
    lane = lane_html(page, "resolver-dataloader")
    for fw in ("async-graphql", "mercurius", "apollo-server", "strawberry"):
        assert meta["frameworks"][fw]["label"] in lane


def test_cache_variant_elides_the_db_hop(page):
    """Precompute lane shows the cache hit as hop-elision: a 0-round-trip hop
    whose path stops at the server (database not touched)."""
    lane = lane_html(page, "precompute")
    assert "database not touched" in lane
    cache_hops = [h for h in hops_in(lane) if h.get("data-hop") == "cache-hit"]
    assert cache_hops and all(
        h["data-sql-roundtrips"] == "0" for h in cache_hops)
    assert "s0-cache-wire" in lane      # the visibly-shorter drawn path


def test_provenance_paths_visible_per_lane(page):
    sec = section(page)
    assert "hops provenanced to" in sec
    assert "frameworks/async-graphql/src/dataloaders.rs" in sec
    assert "frameworks/fraiseql/schema_tv.py" in sec


def test_llms_txt_gains_query_strategy_table(sweep3_run, meta):
    txt = build.render(sweep3_run, meta)["llms.txt"].decode()
    assert "QUERY STRATEGIES" in txt
    for key in meta["query_strategies"]:
        assert f"[{key}]" in txt
    assert "SQL round-trips: Q1=1 Q2b=2 Q3=3" in txt      # resolver scales
    assert "SQL round-trips: Q1=1 Q2b=1 Q3=1" in txt      # compiler flat
    assert "ANY($1)" in txt


# --------------------------------------------------------------------------
# Step 3 pins — motion is user-initiated, honest, and reduced-motion safe
# --------------------------------------------------------------------------

def test_no_motion_before_a_user_gesture(page):
    """Initial DOM: the stage is not .playing and there is no SMIL animation —
    nothing moves until the play button toggles it."""
    assert re.search(r'class="s0-stage"[^>]*data-scenario=', page)
    assert 'class="s0-stage playing"' not in page
    assert "<animate" not in page and "<animateMotion" not in page


def test_durations_derive_from_measured_p50(page, grid, meta):
    """Every rendered --s0-dur equals the representative's measured p50 × scale
    (recomputed here from the grid, never trusted from the page)."""
    scale = meta["anatomy"]["p50_scale_s_per_ms"]
    expected = set()
    for key in meta["anatomy"]["lanes"]:
        rep = meta["query_strategies"][key]["representative"]
        for sc in ANATOMY_SCENARIOS:
            p50 = grid.cell(rep, sc).p50_ms
            expected.add(build.anatomy_duration(p50, scale))
    durs = {float(x) for x in re.findall(r'--s0-dur:([\d.]+)s', page)}
    assert durs, "no paced dots rendered"
    assert durs <= expected, f"unmeasured durations on the page: {durs - expected}"


def test_scale_annotation_present(page, meta):
    scale = meta["anatomy"]["p50_scale_s_per_ms"]
    assert "measured p50" in page
    assert f"p50 × {build.svg.n(scale)} s/ms" in page
    assert "slow-motion" in page


def test_reduced_motion_disables_the_dot(page):
    assert "@media (prefers-reduced-motion: reduce)" in page
    assert re.search(r'\.s0-dot\s*\{\s*animation:\s*none', page)


def test_motion_only_runs_under_playing_stage(page):
    """The keyframe animation is gated behind .s0-stage.playing, so a paused or
    un-started stage never animates."""
    assert ".s0-stage.playing" in page
    assert "@keyframes s0-run" in page
