"""Phase 07 Step 2 [TDD] — S6 footprint & cost data model.

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
