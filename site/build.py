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

import svg

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
# Ladder extraction (S1 nesting cliff; reused by S2/S4/S5 ladders)
# --------------------------------------------------------------------------

@dataclass
class LadderPoint:
    scenario: str
    pos: int
    status: str                 # "result" | "excluded" | "not_measured"
    rps: float | None = None
    p50_ms: float | None = None
    p99_ms: float | None = None


@dataclass
class LadderSeries:
    framework: str
    points: list                # one LadderPoint per rung, in ladder order

    def segments(self) -> list:
        """Runs of consecutive result points with no gap between them. A
        missing rung breaks the run, so the chart never interpolates across an
        excluded or not-measured cell."""
        segs, cur = [], []
        for p in self.points:
            if p.status == "result":
                cur.append(p)
            elif cur:
                segs.append(cur)
                cur = []
        if cur:
            segs.append(cur)
        return segs


def ladder_rungs(meta: dict, ladder: str) -> list:
    """The (scenario, pos) rungs of a named ladder, ordered by ladder_pos."""
    rungs = [(sc, m["ladder_pos"]) for sc, m in meta["scenarios"].items()
             if m.get("ladder") == ladder]
    return sorted(rungs, key=lambda x: x[1])


def ladder_series(grid: Grid, ladder: str = "nesting") -> list:
    """Per-framework ordered ladder points. Frameworks with no result on any
    rung (e.g. the M1-only audit row) are omitted; excluded/not-measured rungs
    are kept as explicit gap points so the renderer can break lines, never
    interpolate."""
    meta = grid.meta
    rungs = ladder_rungs(meta, ladder)
    out = []
    for fw in meta["framework_order"]:
        points = []
        for sc, pos in rungs:
            cell = grid.cell(fw, sc)
            if cell.status == STATUS_RESULT:
                points.append(LadderPoint(
                    sc, pos, "result", cell.rps, cell.p50_ms, cell.p99_ms))
            else:
                points.append(LadderPoint(sc, pos, cell.status))
        if any(p.status == STATUS_RESULT for p in points):
            out.append(LadderSeries(fw, points))
    return out


# --------------------------------------------------------------------------
# Write-trade extraction (S5)
# --------------------------------------------------------------------------

WRITE_SCENARIOS = ("M1", "M1d", "MC1")


@dataclass
class WriteRow:
    scenario: str
    status: str
    rps: float | None = None
    mechanism: str | None = None
    reason_id: int | None = None
    reason: str | None = None


@dataclass
class WriteTradeGroup:
    framework: str
    rows: dict            # scenario -> WriteRow
    appendix: bool = False


def write_mechanism(framework: str, scenario: str, meta: dict) -> str | None:
    fam = ("fraiseql" if meta["frameworks"][framework].get("family") == "fraiseql"
           else "classical")
    return meta.get("mutation_mechanisms", {}).get(scenario, {}).get(fam)


def write_trade(grid: Grid) -> list:
    """Per-framework M1/M1d/MC1 cells (or their exclusion/not-measured records),
    with mutation mechanisms resolved from scenarios.json. The load-bearing
    honesty section: FraiseQL's full-cascade M1 and its delta M1d side by side
    with classical vanilla writes."""
    meta = grid.meta
    out = []
    for fw in meta["framework_order"]:
        rows = {}
        for sc in WRITE_SCENARIOS:
            c = grid.cell(fw, sc)
            rows[sc] = WriteRow(
                scenario=sc, status=c.status, rps=c.rps,
                mechanism=(write_mechanism(fw, sc, meta)
                           if c.status == STATUS_RESULT else None),
                reason_id=c.reason_id, reason=c.reason)
        out.append(WriteTradeGroup(
            framework=fw, rows=rows,
            appendix=bool(meta["frameworks"][fw].get("appendix"))))
    return out


# --------------------------------------------------------------------------
# S0 request anatomy — the hop model (movement layer)
# --------------------------------------------------------------------------

@dataclass
class Hop:
    n: int
    kind: str            # "http" | "parse" | "sql" | "serialize"
    label: str
    sql_roundtrips: int
    source: str


def strategy_of(framework: str, meta: dict) -> str:
    return meta["framework_strategy"][framework]


def hop_diagram(strategy: str, scenario: str, meta: dict) -> list:
    """Ordered browser→server→DB hop list for one (strategy, scenario). Every
    hop is provenanced to the strategy's implementation source; the SQL hops are
    structural truth — resolver + DataLoader adds one batched trip per nesting
    level, compile-to-SQL and precompute stay at one at any depth. No hop is
    drawn without a source (the section's honesty rule)."""
    s = meta["query_strategies"][strategy]
    src = s["source"]
    hops: list = []

    def add(kind: str, label: str, rt: int = 0) -> None:
        hops.append(Hop(len(hops) + 1, kind, label, rt, src))

    add("http", "HTTP request — GraphQL document uploaded")
    if strategy == "resolver-dataloader":
        shape = meta["read_shape"][scenario]
        add("parse", "Parse · validate · plan the query")
        add("sql", f"Root SQL — select the {shape['root']}", 1)
        for lvl in shape["levels"]:
            add("sql",
                f"DataLoader batch — {lvl} in one WHERE key = ANY($1) query", 1)
        add("serialize", "Resolve fields in-process · serialise JSON")
    elif strategy == "compile-to-sql":
        add("parse",
            "Compile the whole tree to ONE SQL — LATERAL joins · jsonb_agg")
        add("sql", "One composed SQL round-trip — full nested JSON returned", 1)
    elif strategy == "precompute":
        add("parse",
            "Look up the pre-computed tv_* row (JSONB built at write time)")
        add("sql", "One SQL round-trip — SELECT jsonb, no joins", 1)
    elif strategy == "rest":
        levels = meta["read_shape"][scenario]["levels"]
        add("sql",
            f"Hand-written SQL — {'a JOIN' if levels else 'single-table select'}",
            1)
    add("http", "Serialise + HTTP response")
    return hops


def anatomy_duration(p50_ms: float, scale: float) -> float:
    """Playback seconds for one request-dot = measured p50 × the stated scale.
    Rounded to 2 dp so the generated SVG is byte-stable."""
    return round(p50_ms * scale, 2)


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


# --------------------------------------------------------------------------
# S1 — the nesting cliff (inline SVG, generated at build time)
# --------------------------------------------------------------------------

S1_W, S1_H = 980, 520
S1_MARGIN = {"l": 62, "r": 182, "t": 30, "b": 58}
DASH_STYLES = ["solid", "dashed", "dotted", "dashdot"]
RUNG_SUBLABEL = {"Q1": "flat", "Q2": "flat", "Q2b": "1-level nest",
                 "Q3": "2-level nest", "T1": "multi-root"}


def _arch_of(fw: str, meta: dict) -> str:
    f = meta["frameworks"][fw]
    if f.get("family") == "fraiseql":
        return "fraiseql"
    return {"compile": "compiler", "resolver": "resolver",
            "rest": "rest"}.get(f.get("mechanism"), "resolver")


def chart_styles(meta: dict) -> dict:
    """Per-framework chart identity: architecture band (the hue) + a dash style
    (the within-band separator). Colour encodes architecture, not identity, so
    the palette stays CVD-safe; the dash + the direct end-label carry identity."""
    out, seen = {}, {}
    for fw in meta["framework_order"]:
        arch = _arch_of(fw, meta)
        i = seen.get(arch, 0)
        seen[arch] = i + 1
        out[fw] = {"arch": arch, "style": DASH_STYLES[i % 4],
                   "hero": fw == "fraiseql-tv"}
    return out


def _tick_int(v) -> str:
    return f"{v:,.0f}"


def _tick_compact(v) -> str:
    return f"{v:g}"


def _metric_val(point, metric):
    return point.rps if metric == "rps" else point.p99_ms


def _metric_fmt(v, metric):
    return fmt_rps(v) if metric == "rps" else fmt_ms(v)


def s1_annotations(grid: Grid, meta: dict) -> dict:
    """Data-driven callouts — recomputed from the grid, never typed in.
    Deliberately extremes (argmax/argmin/steepest), so they cannot be read as
    cherry-picking. See test_chart.py for the exact-string pins."""
    series = ladder_series(grid, "nesting")
    rungs = ladder_rungs(meta, "nesting")
    labels = {fw: meta["frameworks"][fw]["label"] for fw in meta["frameworks"]}

    # Spread at the deepest rung that has any result.
    deepest = None
    for sc, _ in reversed(rungs):
        vals = [(s.framework, next(p.rps for p in s.points if p.scenario == sc))
                for s in series
                if any(p.scenario == sc and p.status == "result"
                       for p in s.points)]
        if vals:
            deepest = (sc, vals)
            break
    spread = None
    if deepest:
        sc, vals = deepest
        top_fw, top_v = max(vals, key=lambda kv: kv[1])
        bot_fw, bot_v = min(vals, key=lambda kv: kv[1])
        ratio = top_v / bot_v if bot_v else float("inf")
        spread = (
            f"{ratio:.0f}× spread at {sc}: {labels[top_fw]} "
            f"{fmt_rps(top_v)} RPS vs {labels[bot_fw]} {fmt_rps(bot_v)} RPS")

    # Steepest single-step fall within a drawn segment (adjacent rungs only).
    worst = None  # (pct, framework, from_sc, to_sc)
    for s in series:
        for seg in s.segments():
            for a, b in zip(seg, seg[1:]):
                if a.rps:
                    pct = (b.rps - a.rps) / a.rps
                    if worst is None or pct < worst[0]:
                        worst = (pct, s.framework, a.scenario, b.scenario)
    steepest = None
    if worst:
        pct, fw, a, b = worst
        steepest = (f"Steepest single-step fall: {labels[fw]} "
                    f"{pct * 100:.0f}% {a}→{b}")

    return {"spread": spread, "steepest": steepest}


def _s1_chart(grid: Grid, meta: dict, metric: str) -> str:
    series = ladder_series(grid, "nesting")
    rungs = ladder_rungs(meta, "nesting")
    styles = chart_styles(meta)
    m = S1_MARGIN
    plot_l, plot_r = m["l"], S1_W - m["r"]
    plot_t, plot_b = m["t"], S1_H - m["b"]

    result_vals = [_metric_val(p, metric) for s in series for p in s.points
                   if p.status == STATUS_RESULT]
    vmax = max(result_vals, default=1.0)
    if metric == "rps":
        top, _step, ticks = svg.nice_axis(vmax, 6)
        yscale = svg.Scale(0, top, plot_b, plot_t)
        ylabel = _tick_int
        ytitle = "Requests / second (y from 0)"
    else:  # p99 spans orders of magnitude -> loudly-labelled log axis
        vmin = min(result_vals, default=1.0)
        lo, hi, ticks = svg.nice_log_axis(vmin, vmax)
        yscale = svg.LogScale(lo, hi, plot_b, plot_t)
        ylabel = _tick_compact
        ytitle = "p99 latency, ms — LOG scale · lower is better"
    xs = {sc: plot_l + (i * (plot_r - plot_l) / (len(rungs) - 1))
          for i, (sc, _) in enumerate(rungs)}

    parts = []
    # gridlines + y tick labels
    for tk in ticks:
        y = yscale(tk)
        parts.append(
            f'<line class="s1-grid" x1="{svg.n(plot_l)}" y1="{svg.n(y)}" '
            f'x2="{svg.n(plot_r)}" y2="{svg.n(y)}"/>')
        parts.append(
            f'<text class="s1-ylabel" x="{svg.n(plot_l - 8)}" '
            f'y="{svg.n(y + 3.5)}">{ylabel(tk)}</text>')
    # x rung labels
    for sc, _ in rungs:
        x = xs[sc]
        parts.append(
            f'<text class="s1-xlabel" x="{svg.n(x)}" y="{svg.n(plot_b + 20)}">'
            f'{esc(sc)}</text>')
        parts.append(
            f'<text class="s1-xsub" x="{svg.n(x)}" y="{svg.n(plot_b + 35)}">'
            f'{esc(RUNG_SUBLABEL.get(sc, ""))}</text>')
    # axis titles
    parts.append(
        f'<text class="s1-axis-title" x="{svg.n(plot_l - 44)}" '
        f'y="{svg.n(plot_t - 14)}">{esc(ytitle)}</text>')
    parts.append(
        f'<text class="s1-axis-title xt" x="{svg.n((plot_l + plot_r) / 2)}" '
        f'y="{svg.n(S1_H - 8)}">read ladder → deeper nesting →</text>')

    # one group per framework; lines break across gaps
    end_labels = []
    for s in series:
        st = styles[s.framework]
        hero = " hero" if st["hero"] else ""
        seg_svg, dots, last = [], [], None
        for seg in s.segments():
            pts = [(xs[p.scenario], yscale(_metric_val(p, metric)))
                   for p in seg]
            seg_svg.append(
                f'<path class="s1-line style-{st["style"]}" '
                f'd="{svg.path_d(pts)}"/>')
            for p, (x, y) in zip(seg, pts):
                tip = (f'{p.scenario} · {_metric_fmt(_metric_val(p, metric), metric)}'
                       f' {"RPS" if metric == "rps" else "ms"}'
                       f' · p99 {fmt_ms(p.p99_ms)} ms')
                dots.append(
                    f'<circle class="s1-dot" cx="{svg.n(x)}" cy="{svg.n(y)}" '
                    f'r="3"><title>{esc(s.framework)} — {esc(tip)}</title>'
                    f'</circle>')
            last = (seg[-1], pts[-1])
        parts.append(
            f'<g class="s1-series arch-{st["arch"]}{hero}" '
            f'data-framework="{esc(s.framework)}">'
            + "".join(seg_svg) + "".join(dots) + "</g>")
        if last:
            p, (x, y) = last
            end_labels.append({
                "y0": y, "fw": s.framework, "arch": st["arch"],
                "text": f'{meta["frameworks"][s.framework]["label"]}  '
                        f'{_metric_fmt(_metric_val(p, metric), metric)}'})

    # de-collide end labels: greedy min-gap from the top
    gap = 14.5
    for lab in sorted(end_labels, key=lambda d: d["y0"]):
        lab["y"] = lab["y0"]
    ordered = sorted(end_labels, key=lambda d: d["y0"])
    prev = plot_t - gap
    for lab in ordered:
        lab["y"] = max(lab["y0"], prev + gap)
        prev = lab["y"]
    # if pushed past the bottom, compress upward
    overflow = ordered[-1]["y"] - plot_b if ordered else 0
    if overflow > 0:
        for lab in ordered:
            lab["y"] -= overflow
    for lab in ordered:
        parts.append(
            f'<text class="s1-endlabel arch-{lab["arch"]}" '
            f'x="{svg.n(plot_r + 10)}" y="{svg.n(lab["y"] + 3)}" '
            f'data-framework="{esc(lab["fw"])}">{esc(lab["text"])}</text>')

    hidden = "" if metric == "rps" else ' hidden'
    return (
        f'<svg class="s1 metric-{metric}"{hidden} viewBox="0 0 {S1_W} {S1_H}" '
        f'preserveAspectRatio="xMinYMid meet" role="img" '
        f'aria-label="Throughput across the read ladder, one line per '
        f'framework, y-axis from zero">'
        + "".join(parts) + "</svg>")


def _s1_section(grid: Grid, meta: dict) -> str:
    ann = s1_annotations(grid, meta)
    callouts = "".join(
        f'<li>{esc(v)}</li>' for v in (ann["spread"], ann["steepest"]) if v)
    return (
        '<section id="s1-nesting-cliff" aria-labelledby="s1-h">'
        '<h2 id="s1-h">S1 — The nesting cliff</h2>'
        '<p class="lede">Throughput across the read ladder Q1 → Q2 → Q2b → Q3 '
        '→ T1, one line per framework. Colour marks the <em>architecture</em> '
        '(FraiseQL · compile-to-SQL · resolver · REST); line style and the '
        'end-label name the specific engine. The y-axis starts at zero; a '
        'missing rung breaks its line rather than interpolating.</p>'
        '<div class="s1-controls">'
        '<button id="s1-metric-toggle" class="theme-toggle" type="button" '
        'aria-pressed="false" data-metric="rps">Showing: throughput (RPS)'
        '</button>'
        '<span class="s1-hint">tap a point for its exact numbers</span></div>'
        '<div class="s1-figure">'
        + _s1_chart(grid, meta, "rps")
        + _s1_chart(grid, meta, "p99")
        + '</div>'
        f'<ul class="s1-callouts">{callouts}</ul>'
        '<p class="footnote" style="margin-top:10px">Prototype sweep — single '
        'pass; tail rungs (Q3, T1) are noisy and the Phase 06 median-of-three '
        'run replaces them. Every value here is also in the grid table above '
        '(no chart-only numbers).</p>'
        '</section>')


# --------------------------------------------------------------------------
# S0 — anatomy of a request (movement layer; the "why" behind S1)
# --------------------------------------------------------------------------

S0_W, S0_H = 560, 96
S0_BX, S0_SX, S0_DX = 56, 288, 508      # browser / server / database columns
S0_Y0, S0_ROWGAP, S0_LABELY = 40, 15, 14
S0_ARCH = {"resolver-dataloader": "resolver", "compile-to-sql": "compiler",
           "precompute": "fraiseql"}
S0_SUBLABEL = {"Q1": "flat", "Q2b": "1-level nest", "Q3": "2-level nest"}


def _s0_points(n_trips: int) -> list:
    """Dot path: browser → server, then one server↔DB rung per SQL round-trip
    (descending so N trips read as an N-rung ladder), then server → browser.
    n_trips == 0 (a cache hit) never reaches the DB column."""
    pts = [(S0_BX, S0_Y0), (S0_SX, S0_Y0)]
    for i in range(n_trips):
        yi = S0_Y0 + i * S0_ROWGAP
        pts.append((S0_DX, yi))
        ynext = S0_Y0 + (i + 1) * S0_ROWGAP if i < n_trips - 1 else yi
        pts.append((S0_SX, ynext))
    pts.append((S0_BX, S0_Y0))
    return pts


def _s0_svg(scenario: str, n_trips: int, dur: float | None, rep_label: str,
            p50: float | None, is_cache: bool) -> str:
    path = svg.path_d(_s0_points(n_trips))
    plural = "s" if n_trips != 1 else ""
    parts = []
    for x, name, anchor in ((S0_BX, "Browser", "start"),
                            (S0_SX, "Server", "middle"),
                            (S0_DX, "Database", "end")):
        parts.append(
            f'<text class="s0-station" x="{svg.n(x)}" y="{S0_LABELY}" '
            f'text-anchor="{anchor}">{name}</text>')
    parts.append(f'<path class="s0-wire" d="{path}"/>')
    parts.append(
        f'<circle class="s0-node" cx="{svg.n(S0_BX)}" cy="{svg.n(S0_Y0)}" r="3"/>'
        f'<circle class="s0-node" cx="{svg.n(S0_SX)}" cy="{svg.n(S0_Y0)}" r="3"/>')
    for i in range(n_trips):
        yi = S0_Y0 + i * S0_ROWGAP
        parts.append(
            f'<circle class="s0-db" cx="{svg.n(S0_DX)}" cy="{svg.n(yi)}" r="4">'
            f'<title>SQL round-trip {i + 1}</title></circle>')
    if is_cache:
        gy = S0_Y0 - 12
        ghost = svg.path_d([(S0_BX, gy), (S0_SX, gy), (S0_BX, gy)])
        parts.append(f'<path class="s0-wire s0-cache-wire" d="{ghost}"/>')
        parts.append(
            f'<text class="s0-cache-label" x="{svg.n(S0_SX + 8)}" '
            f'y="{svg.n(gy - 3)}" text-anchor="middle">tv+cache hit — no DB</text>')
    # The paced dot is only drawn when this run measured the representative's
    # p50 for the scenario — the hop STRUCTURE above is measurement-independent,
    # but the motion must never encode an unmeasured pace.
    if dur is not None:
        tip = (f'{rep_label} · {scenario} · {n_trips} SQL round-trip{plural} · '
               f'median {fmt_ms(p50)} ms')
        # cx/cy stay at 0,0: offset-path translates the element origin along the
        # path, so a circle centred at the origin rides the path exactly (a
        # non-zero cx/cy would double the offset).
        parts.append(
            f'<circle class="s0-dot" cx="0" cy="0" r="6" '
            f"style=\"offset-path:path('{path}');--s0-dur:{svg.n(dur)}s\">"
            f'<title>{esc(tip)}</title></circle>')
    return (
        f'<svg class="s0-anim" viewBox="0 0 {S0_W} {S0_H}" '
        f'preserveAspectRatio="xMidYMid meet" role="img" '
        f'aria-label="{esc(rep_label)} {esc(scenario)}: request travels browser '
        f'to server to database and back, {n_trips} database round-trip{plural}">'
        + "".join(parts) + "</svg>")


def _s0_hop_list(hops: list, is_cache: bool, cache_src: str) -> str:
    lis = []
    for h in hops:
        rt = (' <span class="s0-rt">DB round-trip</span>'
              if h.sql_roundtrips else "")
        lis.append(
            f'<li class="s0-hop kind-{esc(h.kind)}" data-hop="{h.n}" '
            f'data-sql-roundtrips="{h.sql_roundtrips}" '
            f'data-source="{esc(h.source)}">{esc_text(h.label)}{rt}</li>')
    if is_cache:
        lis.append(
            '<li class="s0-hop kind-cache" data-hop="cache-hit" '
            f'data-sql-roundtrips="0" data-source="{esc(cache_src)}">'
            'tv+cache hit — served from the result cache, database not touched'
            ' <span class="s0-rt s0-rt-0">0 DB round-trips</span></li>')
    return f'<ol class="s0-hops">{"".join(lis)}</ol>'


def _s0_variant(strategy: str, scenario: str, meta: dict, grid: Grid,
                default_sc: str) -> str:
    s = meta["query_strategies"][strategy]
    hops = hop_diagram(strategy, scenario, meta)
    n_trips = sum(h.sql_roundtrips for h in hops)
    rep = s["representative"]
    rep_label = meta["frameworks"][rep]["label"]
    scale = meta["anatomy"]["p50_scale_s_per_ms"]
    cell = grid.cell(rep, scenario)
    measured = cell.status == STATUS_RESULT and cell.p50_ms is not None
    p50 = cell.p50_ms if measured else None
    dur = anatomy_duration(p50, scale) if measured else None
    is_cache = strategy == "precompute"
    hidden = "" if scenario == default_sc else " hidden"
    plural = "s" if n_trips != 1 else ""
    if measured:
        pace = (f'median {fmt_ms(p50)} ms · {esc(rep_label)} → '
                f'{svg.n(dur)} s playback')
    else:
        pace = f'{esc(rep_label)} — not measured in this run (pace not shown)'
    cap = (
        '<figcaption class="s0-cap">'
        f'<span class="s0-trips">{n_trips} SQL round-trip{plural}</span>'
        f'<span class="s0-p50">{pace}</span></figcaption>')
    ol = _s0_hop_list(hops, is_cache, s["source"])
    return (
        f'<div class="s0-variant" data-scenario="{esc(scenario)}"{hidden}>'
        f'<figure class="s0-fig">'
        + _s0_svg(scenario, n_trips, dur, rep_label, p50, is_cache)
        + cap + ol + '</figure></div>')


def _s0_lane(strategy: str, meta: dict, grid: Grid, default_sc: str) -> str:
    s = meta["query_strategies"][strategy]
    arch = S0_ARCH[strategy]
    members = " · ".join(meta["frameworks"][m]["label"] for m in s["members"])
    srcs = ", ".join(dict.fromkeys([s["source"], *s.get("sources", [])]))
    variants = "".join(
        _s0_variant(strategy, sc, meta, grid, default_sc)
        for sc in meta["anatomy"]["scenarios"])
    return (
        f'<div class="s0-lane arch-{arch}" data-strategy="{esc(strategy)}">'
        '<div class="s0-lane-head">'
        f'<span class="s0-lane-title">{esc(s["label"])}</span>'
        f'<span class="s0-lane-members">{esc(members)}</span></div>'
        + variants
        + f'<p class="s0-prov">hops provenanced to <code>{esc(srcs)}</code></p>'
        '</div>')


def _s0_section(grid: Grid, meta: dict) -> str:
    a = meta["anatomy"]
    default_sc = a["default_scenario"]
    scale = a["p50_scale_s_per_ms"]
    slow = round(scale * 1000)
    lanes = "".join(_s0_lane(k, meta, grid, default_sc) for k in a["lanes"])
    paces = []
    for k in a["lanes"]:
        rep = meta["query_strategies"][k]["representative"]
        cell = grid.cell(rep, default_sc)
        if cell.status != STATUS_RESULT or cell.p50_ms is None:
            continue
        paces.append(
            f'{meta["frameworks"][rep]["label"]} {fmt_ms(cell.p50_ms)} ms→'
            f'{svg.n(anatomy_duration(cell.p50_ms, scale))} s')
    pace_txt = (" · ".join(esc(p) for p in paces) if paces
                else "representatives not measured in this run")
    scenario_btns = "".join(
        f'<button class="s0-scn" type="button" data-scenario="{esc(sc)}" '
        f'aria-pressed="{"true" if sc == default_sc else "false"}">{esc(sc)}'
        f'<span class="s0-scn-sub">{esc(S0_SUBLABEL.get(sc, ""))}</span></button>'
        for sc in a["scenarios"])
    controls = (
        '<div class="s0-controls" hidden>'
        '<button id="s0-play" class="s0-btn" type="button" aria-pressed="false">'
        '► Play the three requests</button>'
        '<div class="s0-scenario" role="group" aria-label="Read scenario">'
        f'{scenario_btns}</div></div>')
    scale_line = (
        '<p class="s0-scale">Dots are paced by each engine’s <strong>measured '
        f'p50</strong> for the selected read: playback = p50 × {svg.n(scale)} '
        f's/ms (≈{slow}× slow-motion). At {esc(default_sc)}: {pace_txt}. '
        'The pace is the only thing the motion encodes — nothing is '
        'decorative.</p>')
    return (
        '<section id="s0-request-anatomy" aria-labelledby="s0-h">'
        '<h2 id="s0-h">S0 — Anatomy of a request</h2>'
        '<p class="lede">Why the nesting cliff happens. The same nested read, '
        'three architectures, one lane each — watch where the round-trips come '
        'from as depth grows: the resolver lane gains a batched SQL trip per '
        'nesting level, while compile-to-SQL and precompute stay at one at any '
        'depth.</p>'
        f'<p class="lede s0-credit">{esc_text(a["dataloader_credit"])}</p>'
        f'<p class="s0-lens">{esc_text(a["lens_note"])}</p>'
        + controls + scale_line
        + f'<div class="s0-stage" data-scenario="{esc(default_sc)}">{lanes}</div>'
        '<p class="footnote s0-foot"><span class="s0-nojs">Interactive: press '
        'Play to send the dots, and pick a read to switch depth. Without '
        'JavaScript the numbered steps under each lane are the full, ordered '
        f'story.</span> {esc_text(a["apq_note"])}</p>'
        '</section>')


# --------------------------------------------------------------------------
# S5 — the write trade (mandatory honesty section) + workload selector
# --------------------------------------------------------------------------

def _bar_pct(v, axis_max) -> float:
    if not v or axis_max <= 0:
        return 0.0
    return max(0.4, min(100.0, v / axis_max * 100.0))


def _wt_row(row: WriteRow, axis_max: float, unit: str) -> str:
    tag = row.scenario
    if row.status == STATUS_RESULT:
        mech = row.mechanism or "workflow"
        pct = _bar_pct(row.rps, axis_max)
        return (
            f'<div class="wt-row" data-framework="" data-scenario="{esc(tag)}" '
            f'data-rps="{esc(row.rps)}">'
            f'<span class="wt-tag">{esc(tag)}</span>'
            f'<span class="wt-mech">{esc(mech)}</span>'
            f'<span class="wt-track"><span class="wt-bar wt-{esc(tag)}" '
            f'style="width:{svg.n(pct)}%"></span></span>'
            f'<span class="wt-val">{fmt_rps(row.rps)} {esc(unit)}</span></div>')
    if row.status == STATUS_EXCLUDED:
        short = (row.reason or "").split("—", 1)[0].strip() or "excluded"
        return (
            f'<div class="wt-row excluded" data-scenario="{esc(tag)}" '
            f'data-excluded="true" data-reason-id="{esc(row.reason_id)}" '
            f'title="{esc(row.reason)}">'
            f'<span class="wt-tag">{esc(tag)}</span>'
            f'<span class="wt-mech">excluded · #{esc(row.reason_id)}</span>'
            f'<span class="wt-track"></span>'
            f'<span class="wt-val excl">{esc(short)}</span></div>')
    return (
        f'<div class="wt-row not-measured" data-scenario="{esc(tag)}" '
        f'data-not-measured="true">'
        f'<span class="wt-tag">{esc(tag)}</span>'
        f'<span class="wt-mech">—</span>'
        f'<span class="wt-track"></span>'
        f'<span class="wt-val">not measured in this run</span></div>')


def _wt_group(group: WriteTradeGroup, meta: dict, scenarios: list,
              axis_max: float, unit: str) -> str:
    fw_label = meta["frameworks"][group.framework]["label"]
    appendix = " appendix" if group.appendix else ""
    tail = ('<span class="wt-appendix-tag">audit overhead appendix</span>'
            if group.appendix else "")
    rows = "".join(
        _wt_row(group.rows[sc], axis_max, unit) for sc in scenarios)
    return (
        f'<div class="wt-group{appendix}" data-framework="{esc(group.framework)}">'
        f'<div class="wt-fw">{esc(fw_label)}{tail}</div>'
        f'<div class="wt-rows">{rows}</div></div>')


def _wt_axis(axis_max: float, unit: str) -> str:
    return (
        '<div class="wt-axis" aria-hidden="true">'
        '<span>0</span>'
        f'<span>{fmt_rps(axis_max / 2)}</span>'
        f'<span>{fmt_rps(axis_max)} {esc(unit)}</span></div>')


def _s5_section(grid: Grid, meta: dict) -> str:
    groups = write_trade(grid)
    notes = meta.get("notes", {})
    main = [g for g in groups if not g.appendix]
    audit = [g for g in groups if g.appendix]

    # M1 / M1d share one linear req/s axis (same unit, adjacency preserved)
    mm_vals = [g.rows[sc].rps for g in groups for sc in ("M1", "M1d")
               if g.rows[sc].status == STATUS_RESULT and g.rows[sc].rps]
    mm_max = svg.nice_axis(max(mm_vals, default=1.0), 5)[0]
    mc_vals = [g.rows["MC1"].rps for g in groups
               if g.rows["MC1"].status == STATUS_RESULT and g.rows["MC1"].rps]
    mc_max = svg.nice_axis(max(mc_vals, default=1.0), 5)[0]

    explainer = "".join(
        f'<div class="wt-exp wt-exp-{cls}"><strong>{esc(tag)}</strong> '
        f'{esc_text(notes.get(key, ""))}</div>'
        for tag, cls, key in [
            ("M1 — FraiseQL", "M1", "m1_full_cascade"),
            ("M1d — delta", "M1d", "m1_delta"),
            ("M1 — classical", "M1", "m1_vanilla")])

    mm_groups = "".join(
        _wt_group(g, meta, ["M1", "M1d"], mm_max, "req/s") for g in main)
    audit_html = "".join(
        _wt_group(g, meta, ["M1"], mm_max, "req/s") for g in audit)
    mc_groups = "".join(
        _wt_group(g, meta, ["MC1"], mc_max, "cyc/s") for g in main
        if g.rows["MC1"].status != STATUS_NOT_MEASURED or True)

    legend = (
        '<div class="state-legend">'
        '<span><span class="swatch" style="background:var(--wt-c-M1)"></span>'
        'M1 — full write</span>'
        '<span><span class="swatch" style="background:var(--wt-c-M1d)"></span>'
        'M1d — delta patch</span>'
        '<span><span class="swatch" style="background:var(--wt-c-MC1)"></span>'
        'MC1 — workflow</span></div>')

    return (
        '<section id="s5-write-trade" aria-labelledby="s5-h">'
        '<h2 id="s5-h">S5 — The write trade</h2>'
        '<p class="lede">The mandatory honesty section. FraiseQL’s precomputed '
        'reads are paid for on writes: its full-cascade <strong>M1</strong> is '
        'the slowest write here, shown at full linear prominence next to its '
        'own delta path <strong>M1d</strong> and classical vanilla updates. '
        'M1 and M1d sit adjacent, each labelled by mechanism.</p>'
        f'<div class="wt-explainer">{explainer}</div>'
        + legend +
        '<h3>Raw write throughput — M1 vs M1d '
        '<span class="wt-unit">requests / second, linear from 0</span></h3>'
        + _wt_axis(mm_max, "req/s")
        + f'<div class="wt-chart">{mm_groups}</div>'
        + (f'<div class="wt-chart wt-audit">{audit_html}</div>' if audit_html
           else "")
        + '<h3>Mutation → consistent state — MC1 '
        '<span class="wt-unit">a workflow benchmark, cycles / second</span>'
        '</h3>'
        f'<p class="lede">{esc_text(notes.get("mc1_workflow", ""))}</p>'
        + _wt_axis(mc_max, "cyc/s")
        + f'<div class="wt-chart">{mc_groups}</div>'
        + '</section>')


def _workload_selector(grid: Grid, meta: dict) -> str:
    shapes = meta.get("workload_shapes", {})
    cards = []
    for key, shape in shapes.items():
        # resolve a guaranteed-existing anchor: the section, else a real cell
        section = shape.get("section")
        if section:
            primary = f'#{section}'
        else:
            sc = shape["scenarios"][0]
            primary = f'#{cell_anchor(meta["framework_order"][0], sc)}'
            # framework_order[0] is fraiseql-tv which has C3/HC3 results
        chips = "".join(
            f'<a class="wl-chip" href="#{cell_anchor("fraiseql-tv", sc)}">'
            f'{esc(sc)}</a>' for sc in shape["scenarios"])
        cards.append(
            f'<article class="wl-card" data-shape="{esc(key)}">'
            f'<h3><a href="{esc(primary)}">{esc(shape.get("label", key))}</a>'
            f'</h3>'
            f'<p>{esc_text(shape.get("blurb", ""))}</p>'
            f'<div class="wl-chips">answers: {chips}</div></article>')
    return (
        '<section id="workload-selector" aria-labelledby="wl-h">'
        '<h2 id="wl-h">Which workload shape is yours?</h2>'
        '<p class="lede">Pick the shape that matches your workload; each names '
        'the scenarios that answer it — a winner <em>and</em> the trade — and '
        'links to the section and the exact grid cells. Stub for now: plain '
        'anchor navigation, no scoring. The scored selector is future work.</p>'
        f'<div class="wl-grid">{"".join(cards)}</div></section>')


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
(function () {
  var btn = document.getElementById('s1-metric-toggle');
  var fig = document.querySelector('.s1-figure');
  if (!btn || !fig) return;
  var rps = fig.querySelector('.metric-rps');
  var p99 = fig.querySelector('.metric-p99');
  btn.addEventListener('click', function () {
    var showP99 = btn.getAttribute('data-metric') === 'rps';
    btn.setAttribute('data-metric', showP99 ? 'p99' : 'rps');
    btn.setAttribute('aria-pressed', showP99 ? 'true' : 'false');
    btn.textContent = showP99 ? 'Showing: p99 latency (ms)'
                              : 'Showing: throughput (RPS)';
    if (rps) rps.hidden = showP99;
    if (p99) p99.hidden = !showP99;
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
        _s1_section(grid, meta),
        _s0_section(grid, meta),
        _s5_section(grid, meta),
        _workload_selector(grid, meta),
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
    st_lines = []
    for key, s in meta.get("query_strategies", {}).items():
        rt = s.get("sql_roundtrips", {})
        trips = " ".join(f"{sc}={rt.get(sc, '—')}" for sc in ("Q1", "Q2b", "Q3"))
        st_lines.append(f"  {s['label']} [{key}]")
        st_lines.append(f"      members: {', '.join(s['members'])}")
        st_lines.append(f"      SQL round-trips: {trips}")
        st_lines.append(f"      source: {s['source']}")
        st_lines.append(f"      {s['summary']}")
    anatomy = meta.get("anatomy", {})
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
        workload_lines="\n".join(wl_lines),
        strategy_lines="\n".join(st_lines),
        dataloader_credit=anatomy.get("dataloader_credit", ""),
        apq_note=anatomy.get("apq_note", ""))


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
