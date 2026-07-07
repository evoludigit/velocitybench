"""S3 APQ-isolated markup pins.

Written after the design settled. They guard the honesty-critical invariants:
the section is anchored between S2 and S5; each measured pair renders its real
before/after and delta (recomputed here, negatives and ~zeros as-is); APQ-capable
engines whose twin was not measured (apollo/mercurius/async-graphql) appear in
the coverage panel, distinct from the non-APQ engines which carry their verbatim
exclusion reason (4–7); and no framework without a measured delta is drawn as a
bar.
"""
import re
import sys
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


@pytest.fixture()
def page(sweep3_run, meta):
    return build.render(sweep3_run, meta)["index.html"].decode("utf-8")


def section(page):
    m = re.search(r'<section id="s3-apq".*?</section>', page, re.DOTALL)
    assert m, "S3 section missing"
    return m.group(0)


def pair_html(page, base):
    m = re.search(
        rf'<div class="s3-pair" data-pair="{base}">'
        r'.*?(?=<div class="s3-pair"|<div class="s3-coverage")',
        section(page), re.DOTALL)
    assert m, f"no s3 pair for {base}"
    return m.group(0)


def test_section_anchored_between_s2_and_s5(page):
    assert 'id="s3-apq"' in page
    i_s2 = page.index('id="s2-mechanism-ladder"')
    i_s3 = page.index('id="s3-apq"')
    i_s5 = page.index('id="s5-write-trade"')
    assert i_s5 < i_s2 < i_s3   # write-trade earlier; s3 follows s2


def test_three_pairs_in_declared_order(page, meta):
    pairs = re.findall(r'<div class="s3-pair" data-pair="([^"]+)"', section(page))
    assert pairs == [p["base"] for p in meta["apq"]["pairs"]]


def test_only_measured_frameworks_are_drawn_as_rows(page, grid):
    """Every s3-row is a result cell — never a not-measured or excluded one
    dressed as a bar."""
    groups = build.apq_pairs(grid)
    for g in groups:
        drawn = re.findall(r'<div class="s3-row" data-framework="([^"]+)"',
                           pair_html(page, g.base))
        expected = [c.framework for c in g.cells if c.status == "result"]
        assert drawn == expected


def test_before_after_and_delta_recomputed(page, grid):
    """Q1 fraiseql-tv: before→after text + delta match the recomputed values;
    the APQ delta is negative in this run and rendered as-is."""
    tv = next(c for c in build.apq_pairs(grid)[0].cells
              if c.framework == "fraiseql-tv")
    html = pair_html(page, "Q1")
    assert f'{build.fmt_rps(tv.base_rps)} → {build.fmt_rps(tv.apq_rps)} RPS' \
        in html
    assert build.pct_signed(tv.delta.pct) in html         # "−2.9%"
    assert tv.delta.direction == "down"
    assert 's3-delta dir-down' in html


def test_near_zero_delta_reads_plus_minus_zero(page, grid):
    """Q2b fraiseql-tv is ~-0.04% -> ±0.0%, flat glyph — no odd '−0.0%'."""
    q2b_tv = next(c for c in build.apq_pairs(grid)[1].cells
                  if c.framework == "fraiseql-tv")
    assert round(q2b_tv.delta.pct, 1) == 0.0
    html = pair_html(page, "Q2b")
    assert "±0.0%" in html
    assert "−0.0%" not in html


def test_coverage_not_measured_engines_present_without_a_bar(page):
    sec = section(page)
    cov = sec[sec.index('<div class="s3-coverage">'):]
    for fw in ("async-graphql", "mercurius", "apollo-server"):
        assert f'<li data-framework="{fw}">' in cov
        # they are NOT drawn as delta rows anywhere in the section
        assert f'<div class="s3-row" data-framework="{fw}"' not in sec


def test_coverage_excluded_engines_carry_verbatim_reason(page, meta):
    sec = section(page)
    reasons = meta["exclusion_reasons"]
    for fw, rid in (("hasura", 4), ("postgraphile", 5),
                    ("actix-web-rest", 6), ("strawberry", 7)):
        assert f'data-reason-id="{rid}"' in sec
        assert reasons[str(rid)] in sec                    # verbatim
        assert f'<div class="s3-row" data-framework="{fw}"' not in sec


def test_zero_reference_line_and_direction_labels(page):
    sec = section(page)
    assert "0, no change" in sec
    assert "APQ slower" in sec and "APQ faster" in sec
    assert 'class="s3-zero"' in sec                        # the drawn 0% line


def test_no_chart_only_numbers(page, grid, meta):
    """Every before/after value in S3 is a measured grid cell."""
    for g in build.apq_pairs(grid):
        for c in g.cells:
            if c.status == "result":
                assert grid.cell(c.framework, g.base).rps == c.base_rps
                assert grid.cell(c.framework, g.apq).rps == c.apq_rps


def test_llms_txt_apq_coverage_separates_not_measured_from_excluded(sweep3_run, meta):
    """The S3 honesty crux survives into llms.txt: only measured _APQ twins get a
    delta; APQ-capable-but-not-measured is stated distinctly from
    excluded-by-design (an agent must not read 'not measured' as 'slow')."""
    txt = build.render(sweep3_run, meta)["llms.txt"].decode("utf-8")
    assert "APQ ISOLATED (S3)" in txt and "measured twins:" in txt
    assert "NOT measured this run" in txt
    assert "excluded by design" in txt
