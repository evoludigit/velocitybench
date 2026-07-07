"""S6 footprint & cost data model.

Test-first, recomputed from the sweep-3 grid + the dated price YAML. The
honesty stakes: a cost figure is *derived*, and a wrong derivation (or a silent
zero from a missing price) would be the most quotable number on the page. So:

  * the cost arithmetic equals the report's exact model, to the digit;
  * a missing instance price raises — never a silent zero;
  * the stdlib YAML reader parses the real committed price file, so a price
    edit flows through (the file stays the single source);
  * footprint shows every framework, no cherry-picking (Actix beats FraiseQL on
    RAM and the row is present), and the M1-only audit appendix never appears;
  * the storage trade (tv_* vs tb_*) is read from the run, never invented.
"""
import sys
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402

SECONDS_PER_MONTH = 730 * 3600


# --------------------------------------------------------------------------
# load_prices — the stdlib YAML subset reader
# --------------------------------------------------------------------------

def test_load_prices_parses_header_and_instances(prices):
    assert prices["currency"] == "EUR"
    assert prices["captured"] == "2026-07-04"      # a date stays a string
    ccx33 = prices["instances"]["ccx33"]
    assert ccx33["vcpu"] == 8 and isinstance(ccx33["vcpu"], int)
    assert ccx33["ram_gb"] == 32
    assert ccx33["price_month"] == 138.49
    assert ccx33["price_hour"] == 0.2219
    # comments and the fallback-instance block are read, not choked on
    assert set(prices["instances"]) == {"ccx23", "ccx33", "cpx42"}


def test_load_prices_rejects_malformed_file(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("currency EUR\ninstances:\n  ccx1:\n    price_month: 1\n")
    with pytest.raises(ValueError):
        build.load_prices(bad)


def test_load_prices_requires_instances(tmp_path):
    p = tmp_path / "noinst.yaml"
    p.write_text("currency: EUR\ncaptured: 2026-01-01\n")
    with pytest.raises(ValueError):
        build.load_prices(p)


# --------------------------------------------------------------------------
# cost_composite — € / 1M requests, the report's exact model
# --------------------------------------------------------------------------

def test_cost_ranked_by_throughput_appendix_absent(grid, prices):
    rows = build.cost_composite(grid, prices)
    assert [r.framework for r in rows][:2] == [
        "fraiseql-tv-cache", "fraiseql-tv"]       # fastest Q1 first
    rpss = [r.rps for r in rows]
    assert rpss == sorted(rpss, reverse=True)
    assert "fraiseql-tv-audit" not in [r.framework for r in rows]  # no Q1
    assert len(rows) == 11


def test_cost_per_million_matches_report_formula(grid, prices):
    rows = {r.framework: r for r in build.cost_composite(grid, prices)}
    tvc = rows["fraiseql-tv-cache"]
    expect = 138.49 / (tvc.rps * SECONDS_PER_MONTH) * 1_000_000
    assert tvc.per_million["ccx33"] == expect
    assert round(tvc.per_million["ccx33"], 4) == 0.0063
    assert round(tvc.rps_per_euro_month["ccx33"], 1) == 60.8
    # the honesty counterweight: the slowest engine costs ~8x FraiseQL per req
    assert round(rows["strawberry"].per_million["ccx33"], 4) == 0.0532


def test_cost_missing_price_raises_no_silent_zero(grid, prices):
    broken = {"instances": {"ccx33": {"vcpu": 8}}}   # no price_month
    with pytest.raises(ValueError):
        build.cost_composite(grid, broken)


# --------------------------------------------------------------------------
# footprint_rows — RSS / cold start, lightest first, everyone shown
# --------------------------------------------------------------------------

def test_footprint_ordered_lightest_ram_first(sweep3_run, meta):
    rows = build.footprint_rows(sweep3_run, meta)
    assert len(rows) == 11                          # audit appendix excluded
    assert rows[0].framework == "actix-web-rest"    # 5.1 MB — lighter than fql
    assert round(rows[0].peak_ram_mb, 1) == 5.1
    assert rows[-1].framework == "strawberry"       # 173.7 MB, shown as-is
    assert round(rows[-1].peak_ram_mb, 1) == 173.7
    rams = [r.peak_ram_mb for r in rows]
    assert rams == sorted(rams)


def test_footprint_carries_cold_start_from_results(sweep3_run, meta):
    rows = {r.framework: r for r in build.footprint_rows(sweep3_run, meta)}
    assert round(rows["fraiseql-tv"].cold_start_ms, 1) == 1099.3
    assert round(rows["hasura"].cold_start_ms, 1) == 3174.8   # slowest to boot
    assert "fraiseql-tv-audit" not in rows


# --------------------------------------------------------------------------
# db_footprint_pairs — the storage trade, read from the run
# --------------------------------------------------------------------------

def test_db_pairs_precompute_costs_disk(sweep3_run, meta):
    pairs = {p.precompute: p for p in build.db_footprint_pairs(sweep3_run, meta)}
    assert set(pairs) == {"tv_comment", "tv_post", "tv_user"}
    c = pairs["tv_comment"]
    assert c.base == "tb_comment"
    assert c.precompute_bytes == 1739972608 and c.base_bytes == 395329536
    assert round(c.ratio, 2) == 4.40                # precompute is 4.4x the base


def test_db_pairs_missing_table_raises(sweep3_run, meta):
    m = dict(meta)
    m["footprint"] = dict(meta["footprint"])
    m["footprint"]["db_pairs"] = [{"precompute": "tv_ghost", "base": "tb_user"}]
    with pytest.raises(ValueError):
        build.db_footprint_pairs(sweep3_run, m)


# --------------------------------------------------------------------------
# data.json embeds the prices (the AI layer carries the cost inputs)
# --------------------------------------------------------------------------

def test_data_json_embeds_costs(sweep3_run, meta, prices):
    import json
    data = build.render(sweep3_run, meta, prices)["data.json"].decode("utf-8")
    doc = json.loads(data)
    assert doc["costs"]["instances"]["ccx33"]["price_month"] == 138.49


# --------------------------------------------------------------------------
# S6 markup pins (written after the design
# settled; they guard the honesty-critical invariants: bars proportional, the
# derived cost carries its formula, the storage trade is present).
# --------------------------------------------------------------------------

import re  # noqa: E402


@pytest.fixture()
def page(sweep3_run, meta, prices):
    return build.render(sweep3_run, meta, prices)["index.html"].decode("utf-8")


def s6(page):
    m = re.search(r'<section id="s6-footprint".*?</section>', page, re.DOTALL)
    assert m, "S6 section missing"
    return m.group(0)


def test_s6_anchored_after_s5_before_selector(page):
    assert (page.index('id="s5-write-trade"') < page.index('id="s6-footprint"')
            < page.index('id="workload-selector"'))


def test_s6_ram_bar_widths_proportional_to_value(page):
    """A bar's length must be proportional to the number it encodes (linear
    from zero). Two known rows: Strawberry (173.7 MB) vs Actix (5.1 MB)."""
    sec = s6(page)

    def width(fw):
        m = re.search(rf'data-framework="{fw}"[^>]*data-ram-mb[^>]*>.*?'
                      r'width:([\d.]+)%', sec, re.DOTALL)
        return float(m.group(1))
    ratio_w = width("strawberry") / width("actix-web-rest")
    assert round(ratio_w, 2) == round(173.7 / 5.1, 2)   # proportional, no lie


def test_s6_shows_every_framework_no_appendix(page):
    sec = s6(page)
    assert sec.count('class="s6-row"') == 22            # 11 RAM + 11 cost
    assert "fraiseql-tv-audit" not in sec               # appendix never shown


def test_s6_derived_cost_carries_its_formula(page, meta):
    """Cost is derived, and the derivation is shown next to it — never a bare
    number the reader can't reconstruct."""
    sec = s6(page)
    assert meta["footprint"]["cost"]["formula"] in sec
    assert meta["footprint"]["cost"]["price_note"] in sec
    assert "€0.0063" in sec                             # tv+cache headline cost
    assert "derived" in sec.lower()


def test_s6_storage_trade_present_with_ratio(page):
    """The storage counterweight: precomputed tv_* beside base tb_*, ratio
    shown — precompute buys speed and costs disk, in plain sight."""
    sec = s6(page)
    assert 'data-pair="tv_comment"' in sec
    assert "4.4× the base table" in sec
    assert sec.count('class="s6-store-bar"') == 6       # 3 pairs × (tv + tb)

    def store_width(kind_re):
        return float(re.search(kind_re, sec, re.DOTALL).group(1))
    # the precompute (tv_comment) bar is wider than its base (tb_comment)
    tv = store_width(r'data-pair="tv_comment".*?s6-fill-fql[^>]*width:([\d.]+)%')
    tb = store_width(r'data-pair="tv_comment".*?s6-fill-other[^>]*width:([\d.]+)%')
    assert tv > tb


def test_s6_legend_gives_identity_beyond_colour(page):
    """≥2 colour roles ⇒ a legend is present, and every bar also carries its
    framework label — identity is never colour-alone."""
    sec = s6(page)
    assert sec.count("s6-legend") == 2                  # RAM + cost charts
    assert "FraiseQL" in sec and "other engines" in sec
    assert 'class="s6-fw">Strawberry' in sec            # direct label on the bar


def test_s6_omits_uncaptured_charts_never_fakes_them(localhost_path, meta, prices):
    """A minimal run with no resource_metrics/db_footprint still renders a valid
    section — the RAM and storage charts are omitted (not faked with zeros)."""
    run = build.load_run(localhost_path)
    page = build.render(run, meta, prices)["index.html"].decode("utf-8")
    sec = re.search(r'<section id="s6-footprint".*?</section>', page,
                    re.DOTALL).group(0)
    assert "Steady-state memory" not in sec             # no RAM chart
    assert "The storage trade" not in sec               # no storage trade
    assert "Cost per million requests" in sec           # cost still derivable


def test_llms_txt_carries_footprint_and_cost(sweep3_run, meta):
    """S6 in llms.txt marks the € figures DERIVED (not measured), ranks RAM
    lightest-first (no cherry-picking), and shows the storage trade."""
    txt = build.render(sweep3_run, meta)["llms.txt"].decode("utf-8")
    assert "FOOTPRINT & COST (S6)" in txt and "DERIVED" in txt
    assert "steady-state RAM (lightest first)" in txt
    assert "storage trade (precompute costs disk)" in txt
