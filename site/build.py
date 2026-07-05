#!/usr/bin/env python3
"""VelocityBench site build — one run JSON in, a static self-contained site out.

Stdlib only (json, pathlib, html, string.Template, argparse). No third-party
deps, no build framework, no wall-clock reads: the same run JSON in produces
byte-identical output, so the only date on the page is the run's own.

Contract enforced here (README "Hard rules"):
  * same-run rule — exactly one run JSON, never two;
  * no silent gaps — every (framework, scenario) cell is classified as a
    measured result, an excluded-by-design cell, or a not-measured-in-this-run
    cell; a result that collides with a by-design exclusion fails loudly;
  * LOCAL-DATA banner when the run targeted localhost.

Phase 01 renders a placeholder index.html; Phases 02+ layer the real skeleton,
honesty devices and charts on top of the same grid model.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from string import Template

BUILD_DIR = Path(__file__).resolve().parent
SCENARIOS_PATH = BUILD_DIR / "scenarios.json"
TEMPLATES_DIR = BUILD_DIR / "templates"

REQUIRED_RUN_KEYS = ("environment", "framework_versions", "results")
BANNER_TEXT = "LOCAL DATA — NOT PUBLISHABLE"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}

STATUS_RESULT = "result"
STATUS_EXCLUDED = "excluded"
STATUS_NOT_MEASURED = "not_measured"


# --------------------------------------------------------------------------
# Loading & validation
# --------------------------------------------------------------------------

@dataclass
class Run:
    """A single benchmark sweep, validated and normalised."""
    environment: dict
    framework_versions: dict
    results: list
    resource_metrics: list
    db_footprint: list
    source_path: str
    raw: dict

    @property
    def target_host(self) -> str:
        return str(self.environment.get("target_host", ""))

    @property
    def is_local(self) -> bool:
        return self.target_host in LOCAL_HOSTS


def load_meta(path: Path | str = SCENARIOS_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_run(path: Path | str) -> Run:
    path = Path(path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    for key in REQUIRED_RUN_KEYS:
        if key not in doc:
            raise ValueError(
                f"run JSON {path} missing required key: {key!r}")
    return Run(
        environment=doc["environment"],
        framework_versions=doc["framework_versions"],
        results=list(doc["results"]),
        resource_metrics=list(doc.get("resource_metrics", [])),
        db_footprint=list(doc.get("db_footprint", [])),
        source_path=str(path),
        raw=doc,
    )


# --------------------------------------------------------------------------
# The cell grid — no silent gaps
# --------------------------------------------------------------------------

@dataclass
class Cell:
    framework: str
    scenario: str
    status: str
    # result fields (status == "result")
    rps: float | None = None
    p50_ms: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None
    requests: int | None = None
    errors: int | None = None
    error_breakdown: dict = field(default_factory=dict)
    rss_steady_mb: float | None = None
    rss_max_mb: float | None = None
    cold_start_ms: float | None = None
    # exclusion fields (status == "excluded")
    reason_id: int | None = None
    reason: str | None = None

    @property
    def ok(self) -> bool:
        """A measured cell with zero errors."""
        return self.status == STATUS_RESULT and (self.errors or 0) == 0


@dataclass
class Grid:
    cells: dict[tuple[str, str], Cell]
    run: Run
    meta: dict

    def cell(self, framework: str, scenario: str) -> Cell:
        return self.cells[(framework, scenario)]


def _result_cell(framework: str, scenario: str, row: dict) -> Cell:
    return Cell(
        framework=framework, scenario=scenario, status=STATUS_RESULT,
        rps=row.get("rps"), p50_ms=row.get("p50_ms"),
        p95_ms=row.get("p95_ms"), p99_ms=row.get("p99_ms"),
        requests=row.get("requests"), errors=row.get("errors"),
        error_breakdown=dict(row.get("error_breakdown") or {}),
        rss_steady_mb=row.get("rss_steady_mb"),
        rss_max_mb=row.get("rss_max_mb"),
        cold_start_ms=row.get("cold_start_ms"),
    )


def build_grid(run: Run, meta: dict) -> Grid:
    fw_order = meta["framework_order"]
    sc_order = meta["scenario_order"]
    fw_set, sc_set = set(fw_order), set(sc_order)
    reasons = meta["exclusion_reasons"]

    # Index results; refuse a result row for an off-grid framework/scenario.
    result_index: dict[tuple[str, str], dict] = {}
    for row in run.results:
        key = (row["framework"], row["query"])
        if key[0] not in fw_set or key[1] not in sc_set:
            raise ValueError(
                f"result row {key} references a framework/scenario absent "
                f"from scenarios.json canonical order (grid drift)")
        result_index[key] = row

    # Index exclusions; validate every reference.
    excl_index: dict[tuple[str, str], dict] = {}
    for exc in meta["exclusions"]:
        fw, sc, rid = exc["framework"], exc["scenario"], exc["reason_id"]
        if fw not in fw_set:
            raise ValueError(f"exclusion names unknown framework: {fw!r}")
        if sc not in sc_set:
            raise ValueError(f"exclusion names unknown scenario: {sc!r}")
        if str(rid) not in reasons:
            raise ValueError(f"exclusion uses unknown reason_id: {rid!r}")
        excl_index[(fw, sc)] = exc

    cells: dict[tuple[str, str], Cell] = {}
    for fw in fw_order:
        for sc in sc_order:
            key = (fw, sc)
            has_result = key in result_index
            is_excluded = key in excl_index
            if has_result and is_excluded:
                raise ValueError(
                    f"contradiction: {fw}/{sc} has a measured result AND is "
                    f"declared excluded by design — the matrix has drifted")
            if has_result:
                cells[key] = _result_cell(fw, sc, result_index[key])
            elif is_excluded:
                rid = excl_index[key]["reason_id"]
                cells[key] = Cell(
                    framework=fw, scenario=sc, status=STATUS_EXCLUDED,
                    reason_id=rid, reason=reasons[str(rid)])
            else:
                cells[key] = Cell(
                    framework=fw, scenario=sc, status=STATUS_NOT_MEASURED)
    return Grid(cells=cells, run=run, meta=meta)


# --------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------

TITLE = "VelocityBench — how fast, and why"
DESCRIPTION = ("One benchmark sweep, explorable and honest: which framework "
               "wins which workload shape, and by what mechanism.")

# Environment keys shown first, in this order; any remaining keys are appended
# so the methodology block is verbatim-complete, never a curated subset.
ENV_ORDER = [
    ("target_host", "Target host"),
    ("cpu_model", "CPU"),
    ("kernel", "Kernel"),
    ("postgres_version", "PostgreSQL"),
    ("load_generator", "Load generator"),
    ("concurrency", "Concurrency"),
    ("duration_secs", "Duration (s)"),
    ("warmup_secs", "Warm-up (s)"),
    ("cooldown_secs", "Cool-down (s)"),
    ("passes", "Passes"),
    ("tview_mode", "tview mode"),
    ("tview_trigger_scope", "tview trigger scope"),
    ("timestamp", "Run timestamp"),
]

# Structural nav labels for the "Reading These Numbers" panel. The CLAIMS are
# verbatim from scenarios.json.notes; only these short labels live in code.
NOTE_ORDER = [
    ("same_run", "The same-run rule"),
    ("q1_toast", "Why Q1 sits mid-pack (TOAST)"),
    ("tview_scope", "tview trigger scoping"),
    ("mc1_workflow", "MC1 is a workflow benchmark"),
    ("m1_full_cascade", "M1 under tviews — full cascade"),
    ("m1_delta", "M1d — surgical delta patch"),
    ("m1_vanilla", "Classical M1 — vanilla update"),
    ("tv_audit", "The audit-overhead appendix row"),
    ("not_measured", "“Not measured” ≠ excluded ≠ slow"),
]


def esc(v) -> str:
    """Escape for an attribute value (quotes escaped)."""
    return html.escape("" if v is None else str(v))


def esc_text(v) -> str:
    """Escape for element text content. Quotes and apostrophes are safe here,
    so honesty prose (notes, exclusion reasons) stays verbatim in the source."""
    return html.escape("" if v is None else str(v), quote=False)


def cell_anchor(framework: str, scenario: str) -> str:
    """Single source of truth for per-cell anchors (renderer + tests)."""
    return f"cell-{framework}-{scenario}"


def fmt_rps(v) -> str:
    if v is None:
        return "—"
    return f"{v:,.0f}" if v >= 100 else f"{v:,.1f}"


def fmt_ms(v) -> str:
    if v is None:
        return "—"
    return f"{v:.1f}" if v >= 10 else f"{v:.2f}"


def repo_relative(source_path: str) -> str:
    """Normalise the source path to a repo-relative string, so provenance is
    stable regardless of whether the CLI got an absolute or relative path."""
    marker = "velocitybench/"
    idx = source_path.rfind(marker)
    if idx != -1:
        return source_path[idx + len(marker):]
    return Path(source_path).name


def _load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# HTML fragments
# --------------------------------------------------------------------------

def _run_identity(run: Run) -> str:
    env = run.environment
    fql = run.framework_versions.get("fraiseql-tv", "?")
    chips = [
        ("run", env.get("timestamp", "")),
        ("host", env.get("target_host", "")),
        ("FraiseQL", fql),
        ("load-gen", env.get("load_generator", "")),
        ("tview", env.get("tview_mode", "")),
        ("trigger scope", env.get("tview_trigger_scope", "")),
    ]
    spans = "".join(
        f'<span><span class="k">{esc(k)}</span> '
        f'<span class="chip">{esc(v)}</span></span>'
        for k, v in chips if str(v))
    return f'<p class="run-identity">{spans}</p>'


def _methodology(run: Run) -> str:
    env = dict(run.environment)
    rows = []
    seen = set()
    for key, label in ENV_ORDER:
        if key in env:
            rows.append((label, env[key]))
            seen.add(key)
    for key, val in env.items():          # verbatim-complete: nothing hidden
        if key not in seen:
            rows.append((key, val))
    body = "".join(
        f'<div><span class="k">{esc(label)}</span>'
        f'<span class="v">{esc(val)}</span></div>'
        for label, val in rows)
    versions = " · ".join(
        f"{esc(fw)} {esc(ver)}"
        for fw, ver in run.framework_versions.items())
    return (
        '<section id="methodology" aria-labelledby="methodology-h">'
        '<div class="panel">'
        '<h3 id="methodology-h">Methodology — this exact run</h3>'
        f'<div class="meta-grid">{body}</div>'
        f'<p class="run-identity" style="margin-top:12px"><span class="k">'
        f'versions</span> <span>{versions}</span></p>'
        '</div></section>')


def _reading_panel(meta: dict) -> str:
    notes = meta.get("notes", {})
    items = []
    for key, label in NOTE_ORDER:
        if key in notes:
            items.append(
                f"<dt>{esc_text(label)}</dt><dd>{esc_text(notes[key])}</dd>")
    return (
        '<section id="reading" aria-labelledby="reading-h">'
        '<div class="panel reading">'
        '<h3 id="reading-h">Reading these numbers</h3>'
        f'<dl>{"".join(items)}</dl>'
        '</div></section>')


def _state_legend() -> str:
    return (
        '<div class="state-legend" aria-hidden="false">'
        '<span><span class="swatch ok"></span>0 errors (measured)</span>'
        '<span><span class="swatch err"></span>errors &gt; 0 (greyed)</span>'
        '<span><span class="swatch excl"></span>excluded by design</span>'
        '<span><span class="swatch nm"></span>not measured in this run</span>'
        '</div>')


def _grid_head(meta: dict) -> str:
    ths = ['<th scope="col" class="corner">Framework \\ Scenario</th>']
    for sc in meta["scenario_order"]:
        s = meta["scenarios"][sc]
        units = s.get("units", "RPS")
        ths.append(
            f'<th scope="col" id="col-{esc(sc)}" title="{esc(s["label"])}">'
            f'{esc(sc)}<span class="sc-cat">{esc(units)}</span></th>')
    return "<thead><tr>" + "".join(ths) + "</tr></thead>"


def _result_td(cell: Cell) -> str:
    err_free = (cell.errors or 0) == 0
    cls = "cell zero-err" if err_free else "cell has-err"
    anchor = cell_anchor(cell.framework, cell.scenario)
    data = (
        f' data-framework="{esc(cell.framework)}"'
        f' data-scenario="{esc(cell.scenario)}"'
        f' data-rps="{esc(cell.rps)}" data-p99-ms="{esc(cell.p99_ms)}"'
        f' data-errors="{esc(cell.errors)}"')
    inner = (
        f'<span class="rps">{fmt_rps(cell.rps)}</span>'
        f'<span class="p99">p99 {fmt_ms(cell.p99_ms)} ms</span>')
    if not err_free:
        brk = cell.error_breakdown or {}
        detail = ", ".join(f"{esc(k)}: {esc(v)}" for k, v in brk.items())
        inner += (
            f'<details><summary>{esc(cell.errors)} errors</summary>'
            f'<span class="reason">{detail or "no breakdown"}</span></details>')
    return f'<td class="{cls}" id="{anchor}"{data}>{inner}</td>'


def _excluded_td(cell: Cell) -> str:
    anchor = cell_anchor(cell.framework, cell.scenario)
    return (
        f'<td class="excluded" id="{anchor}" data-excluded="true" '
        f'data-reason-id="{esc(cell.reason_id)}" '
        f'title="{esc(cell.reason)}">'
        f'<span class="tag">excluded · {esc(cell.reason_id)}</span>'
        f'<details><summary>why</summary>'
        f'<span class="reason">{esc_text(cell.reason)}</span></details></td>')


def _not_measured_td(cell: Cell, note: str) -> str:
    anchor = cell_anchor(cell.framework, cell.scenario)
    return (
        f'<td class="not-measured" id="{anchor}" data-not-measured="true" '
        f'title="{esc(note)}">'
        f'<span class="tag">not measured</span></td>')


def _grid_body(run: Run, meta: dict, grid: Grid) -> str:
    nm_note = meta.get("notes", {}).get("not_measured", "")
    rows = []
    for fw in meta["framework_order"]:
        fmeta = meta["frameworks"][fw]
        appendix = " appendix-row" if fmeta.get("appendix") else ""
        cells_html = []
        for sc in meta["scenario_order"]:
            cell = grid.cell(fw, sc)
            if cell.status == STATUS_RESULT:
                cells_html.append(_result_td(cell))
            elif cell.status == STATUS_EXCLUDED:
                cells_html.append(_excluded_td(cell))
            else:
                cells_html.append(_not_measured_td(cell, nm_note))
        label = fmeta["label"]
        note = fmeta.get("note", "")
        rows.append(
            f'<tr class="fw-row{appendix}"><th scope="row" '
            f'title="{esc(note)}">{esc(label)}</th>'
            + "".join(cells_html) + "</tr>")
    return "<tbody>" + "".join(rows) + "</tbody>"


def _grid_section(run: Run, meta: dict, grid: Grid) -> str:
    counts = {STATUS_RESULT: 0, STATUS_EXCLUDED: 0, STATUS_NOT_MEASURED: 0}
    zero_err = 0
    for c in grid.cells.values():
        counts[c.status] += 1
        if c.ok:
            zero_err += 1
    caption = (
        f"{counts[STATUS_RESULT]} measured cells "
        f"({zero_err} with 0 errors) · "
        f"{counts[STATUS_EXCLUDED]} excluded by design · "
        f"{counts[STATUS_NOT_MEASURED]} not measured in this run · "
        f"{len(grid.cells)} cells total, none silently dropped")
    table = (
        '<div class="grid-scroll"><table class="grid">'
        f'<caption>{esc(caption)}</caption>'
        + _grid_head(meta) + _grid_body(run, meta, grid)
        + "</table></div>")
    return (
        '<section id="grid" aria-labelledby="grid-h">'
        '<h2 id="grid-h">The full grid</h2>'
        '<p class="lede">Every framework against every scenario. This table is '
        'the no-JS layer — the charts below layer on top of it, never showing a '
        'number it lacks.</p>'
        + _state_legend() + table
        + _exclusion_key(meta) + "</section>")


def _exclusion_key(meta: dict) -> str:
    reasons = meta["exclusion_reasons"]
    items = "".join(
        f"<dt>#{esc_text(rid)}</dt><dd>{esc_text(text)}</dd>"
        for rid, text in sorted(reasons.items(), key=lambda kv: int(kv[0])))
    nm = meta.get("notes", {}).get("not_measured", "")
    return (
        '<div class="panel reading" id="exclusion-key">'
        '<h3>Why cells are excluded by design</h3>'
        f'<dl>{items}</dl>'
        f'<p class="lede" style="margin-top:12px"><strong>Not measured in this '
        f'run</strong> — {esc_text(nm)}</p></div>')


def _placeholder_section(sid: str, title: str, blurb: str) -> str:
    return (
        f'<section id="{sid}" aria-label="{esc(title)}">'
        f'<h2>{esc(title)}</h2>'
        f'<div class="section-todo">{esc(blurb)}</div></section>')


def _footnote(run: Run) -> str:
    rel = repo_relative(run.source_path)
    return (
        '<footer class="footnote">'
        '<p>One sweep, rendered verbatim — no hand-editing, no cross-run '
        'mixing. Rebuilding from the same JSON yields byte-identical output.</p>'
        f'<p>Source run JSON (committed, for provenance): '
        f'<a href="../../{esc(rel)}"><code>{esc(rel)}</code></a> · '
        f'machine copy on this page: <a href="./data.json"><code>data.json</code>'
        f'</a> · agent guide: <a href="./llms.txt"><code>llms.txt</code></a></p>'
        '</footer>')


THEME_SCRIPT = """<script>
(function () {
  var root = document.documentElement;
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  function label(t) {
    return t === 'dark' ? '\\u25D1 dark' : t === 'light' ? '\\u25D0 light'
      : '\\u25D1 auto';
  }
  function apply(t) {
    if (t) root.setAttribute('data-theme', t); else root.removeAttribute('data-theme');
    btn.textContent = label(t);
  }
  var saved = null;
  try { saved = localStorage.getItem('vb-theme'); } catch (e) {}
  // A saved preference wins; otherwise leave any pre-stamped data-theme in
  // place (so a server-rendered theme, or the screenshot loop's stamp, holds).
  if (saved) apply(saved);
  else btn.textContent = label(root.getAttribute('data-theme'));
  btn.addEventListener('click', function () {
    var cur = root.getAttribute('data-theme');
    var next = cur === 'dark' ? 'light' : cur === 'light' ? null : 'dark';
    apply(next);
    try { next ? localStorage.setItem('vb-theme', next)
               : localStorage.removeItem('vb-theme'); } catch (e) {}
  });
})();
</script>"""


def _render_index(run: Run, meta: dict, grid: Grid) -> str:
    banner = ""
    if run.is_local:
        banner = (f'<div class="banner" role="alert">{esc(BANNER_TEXT)}</div>\n')
    header = (
        '<header class="site-head">'
        '<button id="theme-toggle" class="theme-toggle" type="button" '
        'aria-label="Toggle colour theme">◑ auto</button>'
        f'<h1>{esc(TITLE)}</h1>'
        '<p class="lede">One benchmark sweep, explorable and honest — which '
        'framework wins which workload shape, and by which mechanism. FraiseQL '
        'is measured winning on nested reads and losing on full-cascade writes, '
        'both in plain sight.</p>'
        + _run_identity(run) + "</header>")
    body = "\n".join([
        header,
        _methodology(run),
        _reading_panel(meta),
        _grid_section(run, meta, grid),
        _placeholder_section(
            "s1-nesting-cliff", "S1 — The nesting cliff",
            "The read-ladder slope chart (Q1 → Q2 → Q2b → Q3 → T1) lands in "
            "Phase 03; until then the numbers live in the grid above."),
        _placeholder_section(
            "s5-write-trade", "S5 — The write trade",
            "The M1 / M1d / MC1 write-trade view lands in Phase 04; until then "
            "the numbers live in the grid above."),
        _footnote(run),
    ])
    shell = Template(_load_template("base.html"))
    return shell.safe_substitute(
        title=esc(TITLE), description=esc(DESCRIPTION),
        css=_load_template("site.css"), banner=banner, body=body,
        script=THEME_SCRIPT)


# --------------------------------------------------------------------------
# AI layer — data.json + llms.txt
# --------------------------------------------------------------------------

def _render_data_json(run: Run, meta: dict) -> str:
    return json.dumps({"run": run.raw, "scenarios": meta},
                      indent=2, ensure_ascii=False) + "\n"


def _render_llms_txt(run: Run, meta: dict) -> str:
    env = run.environment
    fr_lines = []
    for fw in meta["framework_order"]:
        m = meta["frameworks"][fw]
        tag = " [appendix: M1 only]" if m.get("appendix") else ""
        fr_lines.append(
            f"  {fw:<20} {m['label']} — {m.get('note', '')}"
            f" (family: {m.get('family', '?')}){tag}")
    sc_lines = []
    for sc in meta["scenario_order"]:
        s = meta["scenarios"][sc]
        sc_lines.append(
            f"  {sc:<10} {s['label']} [{s.get('category', '?')},"
            f" {s.get('units', 'RPS')}]")
    wl_lines = []
    for key, shape in meta.get("workload_shapes", {}).items():
        scen = ", ".join(shape["scenarios"])
        wl_lines.append(f"  {shape.get('label', key)} → {scen}")
        wl_lines.append(f"      {shape.get('blurb', '')}")
    local_warning = ""
    if run.is_local:
        local_warning = (
            "\n*** " + BANNER_TEXT + " — target_host is localhost; these "
            "numbers are a local prototype, not a publishable result. ***\n")
    tmpl = Template(_load_template("llms.txt.tmpl"))
    return tmpl.safe_substitute(
        local_warning=local_warning,
        timestamp=env.get("timestamp", ""),
        target_host=env.get("target_host", ""),
        cpu_model=env.get("cpu_model", ""),
        postgres_version=env.get("postgres_version", ""),
        load_generator=env.get("load_generator", ""),
        concurrency=env.get("concurrency", ""),
        duration_secs=env.get("duration_secs", ""),
        tview_mode=env.get("tview_mode", ""),
        tview_trigger_scope=env.get("tview_trigger_scope", ""),
        fraiseql_version=run.framework_versions.get("fraiseql-tv", "?"),
        source_path=repo_relative(run.source_path),
        mc1_workflow=meta.get("notes", {}).get("mc1_workflow", ""),
        n_frameworks=len(meta["framework_order"]),
        n_scenarios=len(meta["scenario_order"]),
        framework_lines="\n".join(fr_lines),
        scenario_lines="\n".join(sc_lines),
        workload_lines="\n".join(wl_lines))


def render(run: Run, meta: dict) -> dict[str, bytes]:
    """Pure renderer: returns every output file as bytes. Tests never touch
    the filesystem twice."""
    grid = build_grid(run, meta)
    return {
        "index.html": _render_index(run, meta, grid).encode("utf-8"),
        "data.json": _render_data_json(run, meta).encode("utf-8"),
        "llms.txt": _render_llms_txt(run, meta).encode("utf-8"),
    }


def write_site(files: dict[str, bytes], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, data in files.items():
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


# --------------------------------------------------------------------------
# CLI — same-run rule
# --------------------------------------------------------------------------

def _fail(msg: str) -> "int":
    print(f"build.py: {msg}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="Render the VelocityBench site from exactly one run JSON.")
    parser.add_argument(
        "run_json", nargs="+",
        help="path to a single bench_sequential run JSON (exactly one)")
    parser.add_argument(
        "--out", required=True, type=Path,
        help="output directory for the generated site")
    parser.add_argument(
        "--scenarios", type=Path, default=SCENARIOS_PATH,
        help="path to scenarios.json metadata contract")
    args = parser.parse_args(argv)

    if len(args.run_json) > 1:
        return _fail(
            "the same-run rule allows exactly one run JSON; refusing to "
            f"build from {len(args.run_json)} paths "
            "(no cross-run or cross-hardware mixing, ever)")

    path = Path(args.run_json[0])
    if path.is_dir():
        return _fail(
            f"'{path}' is a directory; the same-run rule requires exactly "
            "one run JSON file, not a folder of them")
    if not path.exists():
        return _fail(f"'{path}': no such file")

    run = load_run(path)
    meta = load_meta(args.scenarios)
    files = render(run, meta)
    write_site(files, args.out)
    print(f"build.py: wrote {len(files)} file(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
