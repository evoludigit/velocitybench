"""Phase 03 — S1 nesting-cliff chart pins + annotation TDD.

Pins are written AFTER the SVG design settled: they guard the honesty-critical
invariants (y from 0 on RPS, log loudly labelled on p99, one path per
framework, lines break at gaps, direct labels) when the grid grows or styling
changes. The annotation strings are computed data, so they are test-first.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402
import svg    # noqa: E402


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def svg_of(html_str, metric):
    m = re.search(rf'<svg class="s1 metric-{metric}".*?</svg>', html_str,
                  re.DOTALL)
    assert m, f"metric-{metric} chart not found"
    return m.group(0)


@pytest.fixture()
def page(sweep3_run, meta):
    return build.render(sweep3_run, meta)["index.html"].decode("utf-8")


@pytest.fixture()
def rps_svg(page):
    return svg_of(page, "rps")


# --------------------------------------------------------------------------
# Step 2 pins — the SVG chart
# --------------------------------------------------------------------------

def test_one_series_group_per_ladder_framework(rps_svg, grid):
    c = TagCollector()
    c.feed(rps_svg)
    groups = [a["data-framework"] for t, a in c.tags
              if t == "g" and "s1-series" in a.get("class", "")]
    expected = {s.framework for s in build.ladder_series(grid)}
    assert set(groups) == expected
    assert len(groups) == 11


def test_rps_y_axis_starts_at_zero(rps_svg):
    assert svg.nice_axis(11585, 6)[2][0] == 0            # ticks start at 0
    assert 'class="s1-ylabel"' in rps_svg
    assert re.search(r'class="s1-ylabel"[^>]*>0<', rps_svg), "no 0 tick label"
    assert "y from 0" in rps_svg


def test_missing_rung_breaks_line_not_interpolates(rps_svg):
    """actix (no Q3) must render two separate <path>s, never one crossing Q3."""
    g = re.search(r'<g class="s1-series[^"]*" data-framework="actix-web-rest">'
                  r'.*?</g>', rps_svg, re.DOTALL).group(0)
    assert g.count("<path") == 2


def test_direct_end_labels_for_every_line(rps_svg, grid):
    labels = re.findall(r'class="s1-endlabel[^"]*"[^>]*data-framework="([^"]+)"',
                        rps_svg)
    assert set(labels) == {s.framework for s in build.ladder_series(grid)}


def test_p99_uses_log_scale_loudly_labelled(page):
    p99 = svg_of(page, "p99")
    assert "LOG" in p99 and "lower is better" in p99
    # log ticks are decades
    assert svg.nice_log_axis(5.23, 989.89)[2] == [1, 10, 100, 1000]


def test_both_metric_charts_present_p99_hidden(page):
    assert 'class="s1 metric-rps"' in page
    assert re.search(r'class="s1 metric-p99" hidden', page)


def test_chart_is_byte_stable(sweep3_run, meta):
    a = build._s1_chart(build.build_grid(sweep3_run, meta), meta, "rps")
    b = build._s1_chart(build.build_grid(sweep3_run, meta), meta, "rps")
    assert a == b


# --------------------------------------------------------------------------
# Step 3 [TDD] — computed annotation strings (recomputed from the JSON here)
# --------------------------------------------------------------------------

def test_spread_annotation_recomputed(grid, meta):
    ann = build.s1_annotations(grid, meta)
    # independently recompute the T1 spread from the grid
    t1 = {fw: grid.cell(fw, "T1").rps for fw in meta["framework_order"]
          if grid.cell(fw, "T1").status == "result"}
    top_fw = max(t1, key=t1.get)
    bot_fw = min(t1, key=t1.get)
    ratio = round(t1[top_fw] / t1[bot_fw])
    assert ann["spread"] == (
        f"{ratio}× spread at T1: {meta['frameworks'][top_fw]['label']} "
        f"{build.fmt_rps(t1[top_fw])} RPS vs "
        f"{meta['frameworks'][bot_fw]['label']} {build.fmt_rps(t1[bot_fw])} RPS")
    assert "103×" in ann["spread"]


def test_steepest_fall_recomputed(grid, meta):
    ann = build.s1_annotations(grid, meta)
    # brute-force the steepest adjacent in-segment drop
    worst = None
    for s in build.ladder_series(grid):
        for seg in s.segments():
            for a, b in zip(seg, seg[1:]):
                pct = (b.rps - a.rps) / a.rps
                if worst is None or pct < worst[0]:
                    worst = (pct, s.framework, a.scenario, b.scenario)
    pct, fw, a, b = worst
    assert ann["steepest"] == (
        f"Steepest single-step fall: {meta['frameworks'][fw]['label']} "
        f"{round(pct * 100)}% {a}→{b}")


def test_annotations_present_in_page(page, grid, meta):
    ann = build.s1_annotations(grid, meta)
    assert ann["spread"] in page
    assert ann["steepest"] in page
