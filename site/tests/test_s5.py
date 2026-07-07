"""S5 write-trade pins + workload-selector mapping.

These pins guard the load-bearing honesty invariants of the whole site:
M1 and M1d shown adjacent and labelled by mechanism, MC1 flagged as a workflow
benchmark, M1d exclusions rendered in place, the audit row marked appendix, and
every workload-shape link resolving to a real anchor.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))
import build  # noqa: E402


@pytest.fixture()
def page(sweep3_run, meta):
    return build.render(sweep3_run, meta)["index.html"].decode("utf-8")


def group_html(page, framework):
    m = re.search(
        rf'<div class="wt-group(?: appendix)?" data-framework="{re.escape(framework)}">'
        r'.*?</div></div>', page, re.DOTALL)
    assert m, f"no wt-group for {framework}"
    return m.group(0)


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.add(d["id"])


def all_ids(page):
    c = IdCollector()
    c.feed(page)
    return c.ids


# --------------------------------------------------------------------------
# S5 pins
# --------------------------------------------------------------------------

def test_m1_and_m1d_are_adjacent_in_dom(page):
    g = group_html(page, "fraiseql-tv")
    i_m1 = g.index('data-scenario="M1"')
    i_m1d = g.index('data-scenario="M1d"')
    assert 0 <= i_m1 < i_m1d, "M1 must render immediately before M1d"
    # nothing else between them in the write-trade group
    between = g[i_m1:i_m1d]
    assert 'data-scenario="MC1"' not in between


def test_each_write_bar_labelled_by_mechanism(page):
    tv = group_html(page, "fraiseql-tv")
    assert "full-cascade" in tv and "jsonb-delta" in tv
    hasura = group_html(page, "hasura")
    assert "vanilla-update" in hasura


def test_mc1_labelled_workflow_benchmark(page):
    assert "workflow benchmark" in page
    assert "1 request/cycle" in page and "2 requests/cycle" in page


def test_write_axis_starts_at_zero(page):
    axis = re.search(r'<div class="wt-axis"[^>]*>.*?</div>', page, re.DOTALL)
    assert axis and ">0<" in axis.group(0)


def test_m1d_exclusions_render_in_place(page):
    v = group_html(page, "fraiseql-v-cache")
    assert 'data-scenario="M1d"' in v and 'data-excluded="true"' in v
    assert 'data-reason-id="1"' in v
    hasura = group_html(page, "hasura")
    assert 'data-reason-id="3"' in hasura


def test_audit_row_labelled_appendix(page):
    audit = group_html(page, "fraiseql-tv-audit")
    assert "audit overhead appendix" in audit
    # audit shows M1 only (no M1d/MC1 bars in its group)
    assert audit.count('data-scenario="') == 1
    assert 'data-scenario="M1"' in audit


def test_full_cascade_m1_shown_at_full_prominence(sweep3_run, meta):
    """FraiseQL M1 must not be truncated or log-scaled away — a real, small
    linear bar on the same axis as the wins."""
    page = build.render(sweep3_run, meta)["index.html"].decode()
    tv = group_html(page, "fraiseql-tv")
    m1_bar = re.search(r'wt-bar wt-M1" style="width:([\d.]+)%', tv)
    m1d_bar = re.search(r'wt-bar wt-M1d" style="width:([\d.]+)%', tv)
    assert m1_bar and m1d_bar
    # the delta bar is vastly longer than the cascade bar — the honest trade
    assert float(m1d_bar.group(1)) > 20 * float(m1_bar.group(1))


# --------------------------------------------------------------------------
# Workload selector [TDD] mapping + pins
# --------------------------------------------------------------------------

def test_workload_shapes_reference_only_real_scenarios(meta):
    known = set(meta["scenario_order"])
    for key, shape in meta["workload_shapes"].items():
        for sc in shape["scenarios"]:
            assert sc in known, f"{key} references unknown scenario {sc}"


def test_four_shapes_present(page):
    for shape in ("read-heavy", "nested", "write-heavy", "hot-key"):
        assert f'data-shape="{shape}"' in page


def test_every_shape_link_resolves_to_a_real_anchor(page):
    ids = all_ids(page)
    sel = re.search(r'<section id="workload-selector".*?</section>', page,
                    re.DOTALL).group(0)
    hrefs = re.findall(r'href="#([^"]+)"', sel)
    assert hrefs
    for target in hrefs:
        assert target in ids, f"selector links to missing anchor #{target}"


def test_llms_txt_has_workload_paragraph(sweep3_run, meta):
    txt = build.render(sweep3_run, meta)["llms.txt"].decode()
    assert "WORKLOAD SHAPES" in txt
    for shape in meta["workload_shapes"].values():
        assert shape["label"] in txt
