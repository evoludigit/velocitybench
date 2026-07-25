"""The site ships the publishable median-of-3 (2026-07-07) Hetzner run.

Structural honesty invariants are parametrized over BOTH the shipping median
and sweep-3 (permanent regression net) via the `any_run`/`any_grid` fixtures.
Median-specific assertions (versions, full-grid collapse, the Q1 reframe) pin
the publishable run itself.
"""
import json

import build

STATUS = (build.STATUS_RESULT, build.STATUS_EXCLUDED, build.STATUS_NOT_MEASURED)


# ── Invariants that must hold for ANY valid run (median + sweep-3) ──────────

def test_build_emits_all_three_files(any_run, meta):
    out = build.render(any_run, meta)
    assert set(out) == {"index.html", "data.json", "llms.txt"}
    assert all(v and isinstance(v, bytes) for v in out.values())


def test_byte_stable(any_run, meta):
    a = build.render(any_run, meta)
    b = build.render(any_run, meta)
    assert a == b, "same run in must produce identical bytes out"


def test_grid_accounts_for_every_cell(any_grid, meta):
    n_fw = len(meta["framework_order"])
    n_sc = len(meta["scenario_order"])
    cells = list(any_grid.cells.values())
    assert len(cells) == n_fw * n_sc
    assert all(c.status in STATUS for c in cells)
    # No cell is both a result and an exclusion (build_grid would raise, but pin it).
    for c in cells:
        assert not (c.status == build.STATUS_RESULT and c.reason_id is not None)


def test_no_local_data_banner_on_hetzner(any_run, meta):
    html = build.render(any_run, meta)["index.html"].decode()
    assert "10.7.0" in any_run.environment["target_host"]
    assert "LOCAL DATA" not in html


def test_no_numeric_none_or_nan_leak(any_run, meta):
    html = build.render(any_run, meta)["index.html"].decode()
    for bad in ('>None<', 'None RPS', '="None"', 'NaN', 'undefined', '=nan'):
        assert bad not in html, f"rendered a bare {bad!r}"


def test_exclusion_reasons_render_verbatim(any_grid, meta):
    # Reasons come from scenarios.json; every excluded cell carries the exact
    # canonical reason text for its id.
    reasons = meta["exclusion_reasons"]
    excluded = [c for c in any_grid.cells.values()
                if c.status == build.STATUS_EXCLUDED]
    assert excluded, "grid should have structural exclusions"
    for c in excluded:
        assert c.reason == reasons[str(c.reason_id)]


def test_m1_and_m1d_adjacent_in_mutation_view(any_run, meta):
    html = build.render(any_run, meta)["index.html"].decode()
    i_m1 = html.find("data-scenario=\"M1\"")
    i_m1d = html.find("data-scenario=\"M1d\"")
    # Both present and M1 precedes M1d somewhere in the write-trade section.
    if i_m1 != -1 and i_m1d != -1:
        assert i_m1 < i_m1d


# ── Median-specific: the publishable run's own facts ───────────────────────

def test_provenance_link_is_self_contained(any_run, meta):
    """The 'source run JSON' link must resolve wherever the site is served
    (repo, file://, standalone Pages) — a same-dir link, never an ../.. escape
    above the deploy root."""
    html = build.render(any_run, meta)["index.html"].decode()
    name = build.Path(any_run.source_path).name
    assert f'href="./{name}"' in html
    assert f'href="../../{name}"' not in html


def test_scenario_glossary_defines_every_code(any_run, meta):
    """Every Q1/M1/C3-style code that leads on the page is defined, in plain
    English, in one visible glossary — a newcomer never meets an undefined code."""
    import re
    html = build.render(any_run, meta)["index.html"].decode()
    m = re.search(r'<section id="glossary".*?</section>', html, re.S)
    assert m, "no visible scenario glossary section"
    gloss = m.group(0)
    for sc in meta["scenario_order"]:
        assert f'<code>{sc}</code>' in gloss, f"{sc} missing from the scenario key"


def test_median_versions_are_2_14(median_run):
    fq = {k: v for k, v in median_run.framework_versions.items()
          if k.startswith("fraiseql")}
    assert fq and all(v == "2.14.0" for v in fq.values()), fq


def test_median_full_grid_no_not_measured(median_grid):
    from collections import Counter
    st = Counter(c.status for c in median_grid.cells.values())
    assert st[build.STATUS_NOT_MEASURED] == 0, \
        "the full publishable run should measure every non-excluded cell"
    assert st[build.STATUS_RESULT] == 156
    assert st[build.STATUS_EXCLUDED] == 36


def test_median_no_empty_apq_coverage_block(median_run, meta):
    html = build.render(median_run, meta)["index.html"].decode()
    # async/mercurius/apollo APQ are measured now → the not-measured coverage
    # sub-block must be suppressed, not rendered empty.
    assert "APQ-capable · not measured" not in html


def test_median_fraiseql_tops_q1(median_grid):
    q1 = {fw: c.rps for (fw, sc), c in median_grid.cells.items()
          if sc == "Q1" and c.status == build.STATUS_RESULT}
    top = max(q1, key=q1.get)
    assert top.startswith("fraiseql"), f"expected FraiseQL to top Q1, got {top}"
    best_classical = max((r for fw, r in q1.items()
                          if not fw.startswith("fraiseql")), default=0)
    assert q1[top] > 2 * best_classical, "Q1 lead should clear ~2x"


def test_median_data_json_carries_spread(median_run, meta):
    blob = build.render(median_run, meta)["data.json"].decode()
    assert '"spread"' in blob and '"samples"' in blob, \
        "median spread fields must reach the AI layer, not be dropped"


def test_hostile_reader_objections_answered_on_page(any_run, meta):
    """Every April-evaluation objection is answered in the text, not just fixed:
    UNLOGGED durability, load-gen headroom, co-located loadgen, cross-run."""
    html = build.render(any_run, meta)["index.html"].decode()
    for needed in ("UNLOGGED", "never co-located", "30,000 RPS",
                   "same-run", "median of three warm sweeps"):
        assert needed in html, f"hostile-reader objection unanswered: {needed!r}"


def test_median_no_stale_prototype_caveats(median_run, meta):
    out = build.render(median_run, meta)
    for name in ("index.html", "llms.txt"):
        text = out[name].decode()
        for stale in ("Prototype single-pass", "Phase 06 median-of-three",
                      "single-pass sweep", "crossovers become claims"):
            assert stale not in text, f"stale caveat {stale!r} in {name}"
