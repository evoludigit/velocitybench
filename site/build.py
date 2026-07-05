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
COSTS_PATH = BUILD_DIR.parent / "costs" / "instance-prices-2026-07.yaml"

# Hetzner bills 730 h/month; the cost composite mirrors bench_sequential exactly.
SECONDS_PER_MONTH = 730 * 3600

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


def _price_scalar(v: str):
    """Coerce a YAML scalar: quoted string, else int, else float, else raw str
    (so 4 → int, 85.99 → float, 2026-07-04 → str)."""
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        return v[1:-1]
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def load_prices(path: Path | str = COSTS_PATH) -> dict:
    """Parse the small, fixed-shape instance-price YAML with the stdlib only.

    The site build takes no third-party deps (README hard rule), and this file
    is a flat scalar header plus one two-level ``instances:`` mapping, so a
    purpose-built reader is enough — and anything outside that shape raises, so
    a malformed or truncated price file fails the build loudly rather than
    letting a silent zero cost through. The YAML stays the single source; its
    prices are embedded into data.json at build time."""
    path = Path(path)
    root: dict = {}
    instances: dict = {}
    cur: dict | None = None
    for lineno, raw in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].rstrip()   # no value in this file holds '#'
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, sep, val = line.strip().partition(":")
        if not sep:
            raise ValueError(f"{path}:{lineno}: expected 'key: value', got {raw!r}")
        key, val = key.strip(), val.strip()
        if indent == 0:
            if key == "instances":
                root["instances"] = instances
                cur = None
            elif val == "":
                raise ValueError(f"{path}:{lineno}: unexpected block key {key!r}")
            else:
                root[key] = _price_scalar(val)
        elif indent == 2:
            cur = {}
            instances[key] = cur
        elif indent == 4:
            if cur is None:
                raise ValueError(
                    f"{path}:{lineno}: instance field before any instance name")
            cur[key] = _price_scalar(val)
        else:
            raise ValueError(f"{path}:{lineno}: unexpected indent {indent}")
    if "instances" not in root:
        raise ValueError(f"{path}: no 'instances:' mapping found")
    return root


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
# Delta helper — shared by the S2 mechanism ladder and the S3 APQ pairs
# --------------------------------------------------------------------------

@dataclass
class Delta:
    prev: float
    cur: float
    abs: float            # cur - prev (raw, sign preserved)
    pct: float            # (cur - prev) / prev * 100 (raw)
    direction: str        # "up" | "down" | "flat"


def delta_of(prev: float, cur: float, flat_pct: float = 1.5) -> Delta:
    """The signed change from prev to cur. A change under +/-flat_pct reads as
    'flat' so a rung/pair that earns ~nothing is not visually inflated — but the
    raw magnitude and sign are always kept, so a negative delta stays negative
    and honest. Byte-stability is the caller's job (format at render time)."""
    d = cur - prev
    pct = (d / prev * 100.0) if prev else 0.0
    if abs(pct) < flat_pct:
        direction = "flat"
    elif d > 0:
        direction = "up"
    else:
        direction = "down"
    return Delta(prev=prev, cur=cur, abs=d, pct=pct, direction=direction)


DELTA_GLYPH = {"up": "▲", "down": "▼", "flat": "▬"}


def pct_signed(pct: float) -> str:
    """Signed percent to 1 dp; a value that rounds to zero reads ±0.0% so a tiny
    negative never renders as the odd '−0.0%'."""
    r = round(pct, 1)
    sign = "±" if r == 0 else ("+" if r > 0 else "−")
    return f"{sign}{abs(r):.1f}%"


def fmt_delta(delta: Delta, unit: str = "") -> str:
    """'▲ +2,836 RPS (+56.0%)' — explicit sign, real percent (a flat rung shows
    its true near-zero number, a negative one its minus). Deterministic."""
    asign = "+" if delta.abs >= 0 else "−"
    aval = abs(delta.abs)
    afmt = f"{aval:,.0f}" if aval >= 100 else f"{aval:,.1f}"
    unit_s = f" {unit}" if unit else ""
    return (f"{DELTA_GLYPH[delta.direction]} {asign}{afmt}{unit_s} "
            f"({pct_signed(delta.pct)})")


# --------------------------------------------------------------------------
# S2 mechanism ladder — where the read speed comes from, one mechanism at a time
# --------------------------------------------------------------------------

@dataclass
class MechRung:
    framework: str
    mechanism: str
    explain: str
    status: str                  # "result" | "not_measured" | "excluded" | "na"
    rps: float | None = None
    delta: Delta | None = None   # vs the previous *result* rung
    is_apq: bool = False
    reason_id: int | None = None
    reason: str | None = None
    note: str | None = None      # for the "na" +APQ rung (no twin measured)


def apq_twin(scenario: str, meta: dict) -> str | None:
    """The _APQ scenario whose apq_base is `scenario`, if one is defined."""
    for sc, m in meta["scenarios"].items():
        if m.get("apq_base") == scenario:
            return sc
    return None


def mechanism_ladder(grid: Grid, scenario: str) -> list:
    """Ordered FraiseQL-variant rungs for one read scenario (v-nocache → v-cache
    → tv → tv-cache), each labelled by the mechanism it adds and carrying its
    delta over the previous result rung. A final +APQ rung is appended: a real
    delta where the scenario's _APQ twin was measured for the base variant, else
    'na' with a reason. Absolute throughput per rung — a rung that earns ~nothing
    reads flat; the delta chip still states the real, possibly negative, change.
    Variant order, labels and explanations come from scenarios.json."""
    cfg = grid.meta["mechanism_ladder"]
    flat = cfg.get("flat_threshold_pct", 1.5)
    rungs: list = []
    last_rps = None
    for v in cfg["variants"]:
        cell = grid.cell(v["framework"], scenario)
        rung = MechRung(framework=v["framework"], mechanism=v["mechanism"],
                        explain=v["explain"], status=cell.status)
        if cell.status == STATUS_RESULT:
            rung.rps = cell.rps
            if last_rps is not None:
                rung.delta = delta_of(last_rps, cell.rps, flat)
            last_rps = cell.rps
        elif cell.status == STATUS_EXCLUDED:
            rung.reason_id, rung.reason = cell.reason_id, cell.reason
        rungs.append(rung)

    ar = cfg["apq_rung"]
    base_fw = ar["base_variant"]
    apq = MechRung(framework=base_fw, mechanism=ar["mechanism"],
                   explain=ar["explain"], status="na", is_apq=True)
    twin = apq_twin(scenario, grid.meta)
    if twin is None:
        apq.note = ar["no_twin_note"]
    else:
        cell = grid.cell(base_fw, twin)
        apq.status = cell.status
        if cell.status == STATUS_RESULT:
            apq.rps = cell.rps
            if last_rps is not None:
                apq.delta = delta_of(last_rps, cell.rps, flat)
        elif cell.status == STATUS_EXCLUDED:
            apq.reason_id, apq.reason = cell.reason_id, cell.reason
    rungs.append(apq)
    return rungs


# --------------------------------------------------------------------------
# S3 APQ isolated — before/after per framework, honest about not-measured
# --------------------------------------------------------------------------

_APQ_RANK = {STATUS_RESULT: 0, STATUS_NOT_MEASURED: 1, STATUS_EXCLUDED: 2}


@dataclass
class ApqPairCell:
    framework: str
    status: str                  # "result" | "not_measured" | "excluded"
    base_rps: float | None = None
    apq_rps: float | None = None
    delta: Delta | None = None
    reason_id: int | None = None
    reason: str | None = None


@dataclass
class ApqPairGroup:
    base: str
    apq: str
    cells: list                  # ApqPairCell, results first / excluded last


def apq_pairs(grid: Grid) -> list:
    """Per APQ pair (Q1→Q1_APQ, Q2b→Q2b_APQ, M1→M1_APQ), the before/after of
    every non-appendix framework. Status is derived from the grid, never a
    hand-kept capability list: a measured _APQ twin → a real (possibly negative
    or ~zero) delta; a by-design exclusion → its verbatim reason; anything else →
    APQ-capable-but-not-measured. Rows lead with results and trail with
    exclusions (present with reason, never dropped)."""
    meta = grid.meta
    flat = meta["apq"].get("flat_threshold_pct", 1.5)
    order = {fw: i for i, fw in enumerate(meta["framework_order"])}
    groups = []
    for pair in meta["apq"]["pairs"]:
        base, apq = pair["base"], pair["apq"]
        cells = []
        for fw in meta["framework_order"]:
            if meta["frameworks"][fw].get("appendix"):
                continue
            bcell, acell = grid.cell(fw, base), grid.cell(fw, apq)
            c = ApqPairCell(framework=fw, status=acell.status)
            if acell.status == STATUS_EXCLUDED:
                c.reason_id, c.reason = acell.reason_id, acell.reason
            elif acell.status == STATUS_RESULT and bcell.status == STATUS_RESULT:
                c.status = STATUS_RESULT
                c.base_rps, c.apq_rps = bcell.rps, acell.rps
                c.delta = delta_of(bcell.rps, acell.rps, flat)
            else:
                c.status = STATUS_NOT_MEASURED
                c.base_rps = bcell.rps if bcell.status == STATUS_RESULT else None
            cells.append(c)
        cells.sort(key=lambda c: (_APQ_RANK[c.status], order[c.framework]))
        groups.append(ApqPairGroup(base=base, apq=apq, cells=cells))
    return groups


# --------------------------------------------------------------------------
# S4 caching under fire — C3 (miss regime) vs HC3 (hit regime)
# --------------------------------------------------------------------------

@dataclass
class CacheRow:
    framework: str
    cache_on: bool | None
    status: str                  # "result" | "not_measured" | "excluded"
    miss_rps: float | None = None    # C3 — 20 rotating keys, cache can't hit
    hit_rps: float | None = None     # HC3 — 5-key hot pool, cache should hit
    delta: Delta | None = None       # HC3 (hit) over C3 (miss)
    reason_id: int | None = None
    reason: str | None = None


@dataclass
class CacheUnderFire:
    miss: str                    # scenario id for the miss regime (C3)
    hit: str                     # scenario id for the hit regime (HC3)
    variants: list               # CacheRow, the configured FraiseQL variants
    coverage: list               # CacheRow, every other framework (with reason)


def cache_pairs(grid: Grid) -> CacheUnderFire:
    """C3 (20 rotating keys, a cache can never hit) vs HC3 (5-key hot pool, a
    cache should hit almost every time) per configured FraiseQL variant. The
    delta is HC3 over C3: a cache that earned its keep would push it up on the
    cache-on rows while the cache-off rows stayed flat — so the flatness of the
    no-cache rows is itself information, and a ~zero or negative delta renders
    as-is. Every other non-appendix framework trails as a coverage row (not
    measured in this run, or excluded by design with its verbatim reason);
    variant order and cache state come from scenarios.json, never hardcoded."""
    meta = grid.meta
    cfg = meta["cache_under_fire"]
    miss, hit = cfg["miss"], cfg["hit"]
    flat = cfg.get("flat_threshold_pct", 1.5)

    def row(fw: str, cache_on: bool | None) -> CacheRow:
        mcell, hcell = grid.cell(fw, miss), grid.cell(fw, hit)
        r = CacheRow(framework=fw, cache_on=cache_on, status=hcell.status)
        if hcell.status == STATUS_EXCLUDED:
            r.reason_id, r.reason = hcell.reason_id, hcell.reason
        elif hcell.status == STATUS_RESULT and mcell.status == STATUS_RESULT:
            r.status = STATUS_RESULT
            r.miss_rps, r.hit_rps = mcell.rps, hcell.rps
            r.delta = delta_of(mcell.rps, hcell.rps, flat)
        else:
            r.status = STATUS_NOT_MEASURED
            r.miss_rps = mcell.rps if mcell.status == STATUS_RESULT else None
        return r

    variant_fw = {v["framework"] for v in cfg["variants"]}
    variants = [row(v["framework"], v["cache"]) for v in cfg["variants"]]
    order = {fw: i for i, fw in enumerate(meta["framework_order"])}
    coverage = [
        row(fw, None) for fw in meta["framework_order"]
        if fw not in variant_fw and not meta["frameworks"][fw].get("appendix")]
    coverage.sort(key=lambda c: (_APQ_RANK[c.status], order[c.framework]))
    return CacheUnderFire(miss=miss, hit=hit, variants=variants,
                          coverage=coverage)


# --------------------------------------------------------------------------
# S6 footprint & cost — RSS / cold start, the cost composite, the storage trade
# --------------------------------------------------------------------------

@dataclass
class CostRow:
    framework: str
    rps: float                       # measured throughput for the cost scenario
    per_million: dict                # instance -> € / 1M requests (derived)
    rps_per_euro_month: dict         # instance -> RPS served per €/month


def cost_composite(grid: Grid, prices: dict, scenario: str = "Q1") -> list:
    """€ / 1M requests per framework, priced on each dated instance class from
    measured throughput — the report's exact model:

        € / 1M req = price_month / (RPS × 2,628,000 s) × 10⁶

    A derived figure (the formula is shown in the UI), never a measurement.
    Frameworks are ranked by throughput like the report; one with no measured
    result for the cost scenario is skipped, and the appendix audit row (no Q1)
    never appears. A priced instance missing its price_month raises — no silent
    zero costs."""
    instances = prices["instances"]
    for name, spec in instances.items():
        if "price_month" not in spec:
            raise ValueError(
                f"cost file instance {name!r} has no price_month")
    rows = []
    for fw in grid.meta["framework_order"]:
        if grid.meta["frameworks"][fw].get("appendix"):
            continue
        cell = grid.cell(fw, scenario)
        if cell.status != STATUS_RESULT or not cell.rps:
            continue
        rps = cell.rps
        per_million, per_euro = {}, {}
        for name, spec in instances.items():
            pm = spec["price_month"]
            per_million[name] = pm / (rps * SECONDS_PER_MONTH) * 1_000_000
            per_euro[name] = rps / pm
        rows.append(CostRow(fw, rps, per_million, per_euro))
    rows.sort(key=lambda r: -r.rps)
    return rows


@dataclass
class FootprintRow:
    framework: str
    peak_ram_mb: float | None
    cold_start_ms: float | None
    image_mb: float | None
    loc: int | None


def footprint_rows(run: Run, meta: dict) -> list:
    """Per non-appendix framework: steady-state process memory (peak_ram_mb from
    resource_metrics), cold-start time (from a measured result — a startup
    property, constant across scenarios), and container-image size. Ordered
    lightest-RAM first for the runs-on-a-toaster reading; every framework is
    shown, no cherry-picking (hand-written REST can be lighter than FraiseQL,
    and it is shown so)."""
    rm = {m["framework"]: m for m in run.resource_metrics}
    cold: dict = {}
    for r in run.results:
        cold.setdefault(r["framework"], r.get("cold_start_ms"))
    rows = []
    for fw in meta["framework_order"]:
        if meta["frameworks"][fw].get("appendix"):
            continue
        m = rm.get(fw, {})
        rows.append(FootprintRow(
            framework=fw, peak_ram_mb=m.get("peak_ram_mb"),
            cold_start_ms=cold.get(fw), image_mb=m.get("image_mb"),
            loc=m.get("loc")))
    rows.sort(key=lambda r: (r.peak_ram_mb is None, r.peak_ram_mb or 0.0))
    return rows


@dataclass
class DbPair:
    precompute: str
    base: str
    precompute_bytes: int
    base_bytes: int
    ratio: float                     # precompute / base


def db_footprint_pairs(run: Run, meta: dict) -> list:
    """The storage trade: each precomputed tv_* table beside the base tb_* table
    it derives from, with the size ratio. Precompute buys read speed and cheap
    RAM; it costs disk, and this shows how much. Pairs come from scenarios.json;
    a named table absent from the run's db_footprint raises (no invented rows).
    A run that captured no db_footprint at all yields no pairs — the storage
    trade is simply omitted, not faked."""
    if not run.db_footprint:
        return []
    sizes = {f["table"]: f["total_bytes"] for f in run.db_footprint}
    pairs = []
    for p in meta["footprint"]["db_pairs"]:
        pc, base = p["precompute"], p["base"]
        if pc not in sizes or base not in sizes:
            raise ValueError(
                f"db_footprint pair {pc}/{base} not found in run db_footprint")
        pb, bb = sizes[pc], sizes[base]
        pairs.append(DbPair(pc, base, pb, bb, (pb / bb) if bb else 0.0))
    return pairs


# --------------------------------------------------------------------------
# S7 amortization — total load vs read:write ratio (the break-even model)
# --------------------------------------------------------------------------

@dataclass
class AmortSeries:
    framework: str
    architecture: str
    read_rps: float | None
    write_rps: float | None
    write_scenario: str            # the write cell used (M1 / M1d)
    read_trips: int | None         # SQL round-trips per read (S0 hop model)
    write_trips: int | None        # per write; None = cascade fan-out unmeasured
    status: str                    # "ok" | "no_read" | "no_write"

    def sustainable_rps(self, r: float) -> float | None:
        """Sustainable total (reads+writes) requests/second for a workload of
        1 write + r reads: (r+1) / (r/read_rps + 1/write_rps). At r→0 it is the
        measured write throughput, at r→∞ the measured read throughput."""
        if self.read_rps is None or self.write_rps is None:
            return None
        work = r / self.read_rps + 1.0 / self.write_rps
        return (r + 1.0) / work if work else None

    def count(self, r: float) -> float | None:
        """Structural SQL round-trips per workload-unit: r·read_trips +
        write_trips. None when either is unknown (e.g. an unmeasured cascade
        fan-out) — never silently zero."""
        if self.read_trips is None or self.write_trips is None:
            return None
        return r * self.read_trips + self.write_trips


@dataclass
class Breakeven:
    anchor: str                    # the precompute anchor framework
    other: str
    ratio: float | None            # crossover reads-per-write (None if none > 0)
    anchor_wins_above: bool        # anchor sustains more as reads dominate


@dataclass
class Amortization:
    read: str
    write: str                     # write-mode key ("full" / "delta")
    series: list                   # AmortSeries, ok first
    breakevens: list               # Breakeven, anchor vs each other ok series


def _amort_family(fw: str, meta: dict) -> str:
    return ("fraiseql" if meta["frameworks"][fw].get("family") == "fraiseql"
            else "classical")


def _breakevens(series: list, anchor_fw: str) -> list:
    """Crossover reads-per-write between the anchor (precompute) and each other
    plottable series, from the cost curves: r* where the two sustainable-rps
    curves meet. Equivalent to r·(1/read_a)+1/write_a = r·(1/read_b)+1/write_b,
    solved for r. A non-positive r* (one engine dominates at every ratio) is
    reported as None with the win-direction still set."""
    anchor = next((s for s in series
                   if s.framework == anchor_fw and s.status == "ok"), None)
    if anchor is None:
        return []
    rca, wca = 1.0 / anchor.read_rps, 1.0 / anchor.write_rps
    out = []
    for s in series:
        if s.framework == anchor_fw or s.status != "ok":
            continue
        rcb, wcb = 1.0 / s.read_rps, 1.0 / s.write_rps
        denom = rca - rcb
        r = (wcb - wca) / denom if denom else None
        ratio = r if (r is not None and r > 0) else None
        out.append(Breakeven(anchor_fw, s.framework, ratio,
                             anchor.read_rps > s.read_rps))
    return out


def amortize(grid: Grid, meta: dict, read: str | None = None,
             write: str | None = None) -> Amortization:
    """The amortization model for one read rung and write mode. Each configured
    architecture-representative series carries its measured read and write
    throughput (cost layer) and its structural round-trip counts (secondary
    layer); a series missing either cell degrades with a status, never a silent
    zero. Break-evens are computed against the precompute anchor. A derived
    model: every number here traces to a grid cell or the S0 hop counts."""
    cfg = meta["amortization"]
    read = read or cfg["default_read"]
    write = write or cfg["default_write"]
    wmode = cfg["writes"][write]
    strat, qs = meta["framework_strategy"], meta["query_strategies"]
    order = {s["framework"]: i for i, s in enumerate(cfg["series"])}
    series = []
    for s in cfg["series"]:
        fw = s["framework"]
        fam = _amort_family(fw, meta)
        wscenario = wmode["scenario"][fam]
        rcell, wcell = grid.cell(fw, read), grid.cell(fw, wscenario)
        read_rps = rcell.rps if rcell.status == STATUS_RESULT else None
        write_rps = wcell.rps if wcell.status == STATUS_RESULT else None
        read_trips = qs.get(strat[fw], {}).get("sql_roundtrips", {}).get(read)
        status = ("ok" if read_rps and write_rps
                  else "no_read" if not read_rps else "no_write")
        series.append(AmortSeries(
            framework=fw, architecture=s["architecture"], read_rps=read_rps,
            write_rps=write_rps, write_scenario=wscenario,
            read_trips=read_trips, write_trips=wmode["trips"][fam],
            status=status))
    series.sort(key=lambda a: (a.status != "ok", order[a.framework]))
    return Amortization(read=read, write=write, series=series,
                        breakevens=_breakevens(series, cfg["anchor_series"]))


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
# S2 — the mechanism ladder (where the read speed comes from)
# --------------------------------------------------------------------------

S2_BAR = {"fraiseql-v-nocache": "v", "fraiseql-v-cache": "vc",
          "fraiseql-tv": "tv", "fraiseql-tv-cache": "tvc"}


def _s2_axis(axis_max: float, unit: str = "RPS") -> str:
    return (
        '<div class="s2-axis" aria-hidden="true">'
        '<span>0</span>'
        f'<span>{fmt_rps(axis_max / 2)}</span>'
        f'<span>{fmt_rps(axis_max)} {esc(unit)}</span></div>')


def _s2_delta(rung: MechRung) -> str:
    if rung.delta is None:
        return '<span class="s2-delta dir-base">baseline</span>'
    return (f'<span class="s2-delta dir-{rung.delta.direction}">'
            f'{esc(fmt_delta(rung.delta, "RPS"))}</span>')


def _s2_rung(rung: MechRung, axis_max: float, meta: dict) -> str:
    fw_label = meta["frameworks"][rung.framework]["label"]
    vname = f"persisted query on {fw_label}" if rung.is_apq else fw_label
    apq = " s2-apq" if rung.is_apq else ""
    delta = _s2_delta(rung) if rung.status == STATUS_RESULT else ""
    head = (
        '<div class="s2-rung-head">'
        f'<span class="s2-mech">{esc(rung.mechanism)}</span>'
        f'<span class="s2-vname">{esc(vname)}</span>{delta}</div>')
    if rung.status == STATUS_RESULT:
        pct = _bar_pct(rung.rps, axis_max)
        barcls = "apq" if rung.is_apq else S2_BAR.get(rung.framework, "tv")
        return (
            f'<div class="s2-rung{apq}" data-framework="{esc(rung.framework)}" '
            f'data-mechanism="{esc(rung.mechanism)}" data-rps="{esc(rung.rps)}">'
            f'{head}'
            '<div class="s2-barline">'
            f'<div class="s2-track"><span class="s2-bar s2-bar-{barcls}" '
            f'style="width:{svg.n(pct)}%"></span></div>'
            f'<span class="s2-val">{fmt_rps(rung.rps)} RPS</span></div>'
            f'<p class="s2-explain">{esc_text(rung.explain)}</p></div>')
    # na (no _APQ twin) / not_measured / excluded — an honest empty rung
    if rung.status == STATUS_EXCLUDED:
        msg = rung.reason
    elif rung.status == "na":
        msg = rung.note
    else:
        msg = "not measured in this run"
    return (
        f'<div class="s2-rung s2-rung-empty{apq}" '
        f'data-mechanism="{esc(rung.mechanism)}">'
        f'{head}<p class="s2-empty-msg">{esc_text(msg)}</p>'
        f'<p class="s2-explain">{esc_text(rung.explain)}</p></div>')


def _s2_variant(grid: Grid, meta: dict, scenario: str, axis_max: float,
                default_sc: str) -> str:
    rungs = mechanism_ladder(grid, scenario)
    hidden = "" if scenario == default_sc else " hidden"
    body = "".join(_s2_rung(r, axis_max, meta) for r in rungs)
    return (
        f'<div class="s2-variant" data-scenario="{esc(scenario)}"{hidden}>'
        f'{body}</div>')


def _s2_section(grid: Grid, meta: dict) -> str:
    cfg = meta["mechanism_ladder"]
    default_sc = cfg["default_scenario"]
    all_rps = [r.rps for sc in cfg["scenarios"]
               for r in mechanism_ladder(grid, sc)
               if r.status == STATUS_RESULT and r.rps]
    axis_max = svg.nice_axis(max(all_rps, default=1.0), 5)[0]
    btns = "".join(
        f'<button class="s2-scn" type="button" data-scenario="{esc(sc)}" '
        f'aria-pressed="{"true" if sc == default_sc else "false"}">{esc(sc)}'
        f'<span class="s2-scn-sub">{esc(RUNG_SUBLABEL.get(sc, ""))}</span>'
        '</button>'
        for sc in cfg["scenarios"])
    controls = (
        '<div class="s2-controls" hidden>'
        '<span class="s2-controls-label">Read scenario</span>'
        '<div class="s2-scenario" role="group" aria-label="Read scenario">'
        f'{btns}</div></div>')
    variants = "".join(
        _s2_variant(grid, meta, sc, axis_max, default_sc)
        for sc in cfg["scenarios"])
    return (
        '<section id="s2-mechanism-ladder" aria-labelledby="s2-h">'
        '<h2 id="s2-h">S2 — Where the speed comes from</h2>'
        f'<p class="lede">{esc_text(cfg["summary"])}</p>'
        + controls + _s2_axis(axis_max)
        + f'<div class="s2-stage" data-scenario="{esc(default_sc)}">'
        f'{variants}</div>'
        '<p class="footnote">Bars are absolute throughput from zero, so a rung '
        'that earns ~nothing reads flat — no visual inflation of small gains. '
        'Every value here is also in the grid table above (no chart-only '
        'numbers). Prototype single-pass sweep; the Phase 06 median-of-three '
        'run refines the tail.</p>'
        '</section>')


# --------------------------------------------------------------------------
# S3 — APQ isolated (diverging delta bars + a coverage panel)
# --------------------------------------------------------------------------

def _num(v) -> str:
    return f"{v:g}"


def _s3_axis(axis_pct: float) -> str:
    return (
        '<div class="s3-axis" aria-hidden="true">'
        f'<span>−{_num(axis_pct)}%</span>'
        '<span class="s3-axis-mid">◄ APQ slower · 0, no change · APQ faster ►'
        '</span>'
        f'<span>+{_num(axis_pct)}%</span></div>')


def _s3_delta_bar(cell: ApqPairCell, axis_pct: float) -> str:
    """A diverging bar growing from the centre 0%-line: left/red when APQ was
    slower, right/green when faster, a thin muted stub when ~flat. |pct| is
    scaled against the shared symmetric axis; a real negative stays left."""
    d = cell.delta
    frac = min(1.0, abs(d.pct) / axis_pct) if axis_pct else 0.0
    w = frac * 50.0
    if d.pct >= 0:
        pos = f"left:50%;width:{svg.n(w)}%"
    else:
        pos = f"left:{svg.n(50.0 - w)}%;width:{svg.n(w)}%"
    return (
        '<span class="s3-track"><span class="s3-zero"></span>'
        f'<span class="s3-bar dir-{d.direction}" style="{pos}"></span></span>')


def _s3_result_row(cell: ApqPairCell, meta: dict, axis_pct: float) -> str:
    label = meta["frameworks"][cell.framework]["label"]
    d = cell.delta
    return (
        f'<div class="s3-row" data-framework="{esc(cell.framework)}" '
        f'data-base-rps="{esc(cell.base_rps)}" data-apq-rps="{esc(cell.apq_rps)}">'
        f'<span class="s3-fw">{esc(label)}</span>'
        f'<span class="s3-ba">{fmt_rps(cell.base_rps)} → '
        f'{fmt_rps(cell.apq_rps)} RPS</span>'
        + _s3_delta_bar(cell, axis_pct)
        + f'<span class="s3-delta dir-{d.direction}">{DELTA_GLYPH[d.direction]} '
        f'{pct_signed(d.pct)}</span></div>')


def _s3_pair(group: ApqPairGroup, meta: dict, axis_pct: float) -> str:
    base_label = meta["scenarios"][group.base]["label"]
    results = [c for c in group.cells if c.status == STATUS_RESULT]
    rows = "".join(_s3_result_row(c, meta, axis_pct) for c in results)
    return (
        f'<div class="s3-pair" data-pair="{esc(group.base)}">'
        f'<h3>{esc(group.base)} → {esc(group.apq)} '
        f'<span class="s3-pair-sub">{esc(base_label)}</span></h3>'
        f'<div class="s3-rows">{rows}</div></div>')


def _s3_coverage(groups: list, meta: dict) -> str:
    """The not-measured and excluded frameworks — presence with reason, never
    omission. APQ capability is a property of the framework, not the scenario,
    so it is constant across pairs; read it off the first pair."""
    ref = groups[0].cells
    nm = [c for c in ref if c.status == STATUS_NOT_MEASURED]
    excl = [c for c in ref if c.status == STATUS_EXCLUDED]
    fw_label = meta["frameworks"]
    nm_html = "".join(
        f'<li data-framework="{esc(c.framework)}">'
        f'{esc(fw_label[c.framework]["label"])}</li>' for c in nm)
    excl_html = "".join(
        f'<li data-framework="{esc(c.framework)}" '
        f'data-reason-id="{esc(c.reason_id)}">'
        f'<span class="s3-cov-fw">{esc(fw_label[c.framework]["label"])} '
        f'<span class="tag">excluded · {esc(c.reason_id)}</span></span>'
        f'<span class="s3-cov-reason">{esc_text(c.reason)}</span></li>'
        for c in excl)
    return (
        '<div class="s3-coverage">'
        '<div class="s3-cov-block">'
        '<h4>APQ-capable · not measured in this run</h4>'
        f'<p class="s3-cov-note">{esc_text(meta["apq"]["not_measured_note"])}</p>'
        f'<ul class="s3-cov-list nm">{nm_html}</ul></div>'
        '<div class="s3-cov-block">'
        '<h4>No first-party APQ handshake · excluded by design</h4>'
        f'<ul class="s3-cov-list excl">{excl_html}</ul></div>'
        '</div>')


def _s3_section(grid: Grid, meta: dict) -> str:
    groups = apq_pairs(grid)
    all_pct = [abs(c.delta.pct) for g in groups for c in g.cells
               if c.status == STATUS_RESULT and c.delta]
    axis_pct = svg.nice_axis(max(all_pct, default=1.0), 5)[0]
    pairs = "".join(_s3_pair(g, meta, axis_pct) for g in groups)
    return (
        '<section id="s3-apq" aria-labelledby="s3-h">'
        '<h2 id="s3-h">S3 — APQ, isolated</h2>'
        f'<p class="lede">{esc_text(meta["apq"]["summary"])}</p>'
        + _s3_axis(axis_pct)
        + f'<div class="s3-pairs">{pairs}</div>'
        + _s3_coverage(groups, meta)
        + '<p class="footnote">Bars are the measured APQ delta against a 0% '
        'no-change line — a bar to the left means APQ was <em>slower</em> in '
        'this run. Every before/after value is also in the grid table above '
        '(no chart-only numbers). Prototype single-pass sweep.</p>'
        '</section>')


# --------------------------------------------------------------------------
# S4 — caching under fire (C3 miss regime vs HC3 hit regime, paired bars)
# --------------------------------------------------------------------------

S4_BAR = {"fraiseql-v-nocache": "v", "fraiseql-v-cache": "vc",
          "fraiseql-tv": "tv", "fraiseql-tv-cache": "tvc"}


def _s4_axis(axis_max: float) -> str:
    return (
        '<div class="s4-axis" aria-hidden="true">'
        '<span>0</span>'
        f'<span>{fmt_rps(axis_max / 2)}</span>'
        f'<span>{fmt_rps(axis_max)} RPS</span></div>')


def _s4_regimes(cfg: dict) -> str:
    reg = cfg["regimes"]
    return (
        '<div class="s4-regimes">'
        '<div class="s4-regime s4-regime-miss"><h3>Miss regime</h3>'
        f'<p>{esc_text(reg["miss"])}</p></div>'
        '<div class="s4-regime s4-regime-hit"><h3>Hit regime</h3>'
        f'<p>{esc_text(reg["hit"])}</p></div></div>')


def _s4_bar(regime: str, label: str, rps: float, axis_max: float,
            barcls: str) -> str:
    pct = _bar_pct(rps, axis_max)
    return (
        f'<div class="s4-barline s4-{regime}">'
        f'<span class="s4-reg">{esc(label)}</span>'
        f'<span class="s4-track"><span class="s4-bar s4-bar-{barcls}" '
        f'style="width:{svg.n(pct)}%"></span></span>'
        f'<span class="s4-val">{fmt_rps(rps)} RPS</span></div>')


def _s4_delta(row: CacheRow) -> str:
    if row.delta is None:
        return ""
    return (f'<span class="s4-delta dir-{row.delta.direction}">'
            f'{esc(fmt_delta(row.delta, "RPS"))}</span>')


def _s4_variant(row: CacheRow, axis_max: float, meta: dict) -> str:
    fw_label = meta["frameworks"][row.framework]["label"]
    state = "on" if row.cache_on else "off"
    barcls = S4_BAR.get(row.framework, "tv")
    head = (
        '<div class="s4-head">'
        f'<span class="s4-fw">{esc(fw_label)}</span>'
        f'<span class="s4-badge s4-badge-{state}">cache {state}</span>'
        f'{_s4_delta(row)}</div>')
    return (
        f'<div class="s4-variant" data-framework="{esc(row.framework)}" '
        f'data-cache="{state}" data-miss-rps="{esc(row.miss_rps)}" '
        f'data-hit-rps="{esc(row.hit_rps)}">{head}'
        + _s4_bar("miss", "miss · C3", row.miss_rps, axis_max, barcls)
        + _s4_bar("hit", "hit · HC3", row.hit_rps, axis_max, barcls)
        + '</div>')


def _s4_coverage(view: CacheUnderFire, meta: dict) -> str:
    nm = [r for r in view.coverage if r.status == STATUS_NOT_MEASURED]
    excl = [r for r in view.coverage if r.status == STATUS_EXCLUDED]
    fw_label = meta["frameworks"]
    blocks = ""
    if nm:
        chips = "".join(
            f'<li data-framework="{esc(r.framework)}">'
            f'{esc(fw_label[r.framework]["label"])}</li>' for r in nm)
        blocks += (
            '<div class="s4-cov-block">'
            '<h4>Not measured on the hot-key scenarios in this run</h4>'
            f'<p class="s4-cov-note">'
            f'{esc_text(meta["cache_under_fire"]["not_measured_note"])}</p>'
            f'<ul class="s4-cov-list nm">{chips}</ul></div>')
    if excl:
        items = "".join(
            f'<li data-framework="{esc(r.framework)}" '
            f'data-reason-id="{esc(r.reason_id)}">'
            f'<span class="s4-cov-fw">{esc(fw_label[r.framework]["label"])} '
            f'<span class="tag">excluded · {esc(r.reason_id)}</span></span>'
            f'<span class="s4-cov-reason">{esc_text(r.reason)}</span></li>'
            for r in excl)
        blocks += (
            '<div class="s4-cov-block">'
            '<h4>Excluded by design</h4>'
            f'<ul class="s4-cov-list excl">{items}</ul></div>')
    return f'<div class="s4-coverage">{blocks}</div>' if blocks else ""


def _s4_section(grid: Grid, meta: dict) -> str:
    cfg = meta["cache_under_fire"]
    view = cache_pairs(grid)
    vals = [v for r in view.variants for v in (r.miss_rps, r.hit_rps) if v]
    axis_max = svg.nice_axis(max(vals, default=1.0), 5)[0]
    variants = "".join(_s4_variant(r, axis_max, meta) for r in view.variants)
    return (
        '<section id="s4-cache-under-fire" aria-labelledby="s4-h">'
        '<h2 id="s4-h">S4 — Caching under fire</h2>'
        f'<p class="lede">{esc_text(cfg["summary"])}</p>'
        + _s4_regimes(cfg)
        + _s4_axis(axis_max)
        + f'<div class="s4-chart">{variants}</div>'
        + _s4_coverage(view, meta)
        + '<p class="footnote">Two bars per variant — the same single-row read '
        'against 20 rotating keys (miss) and a 5-key hot pool (hit), on one '
        'linear axis from zero. Equal-length pairs mean the cache changed '
        'nothing; the chip is the real, signed hit-over-miss delta. Every '
        'value is also in the grid table above (no chart-only numbers). '
        'Prototype single-pass sweep.</p>'
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


# --------------------------------------------------------------------------
# S6 — footprint & cost (RSS / cold start, cost composite, storage trade)
# --------------------------------------------------------------------------

def _fam(fw: str, meta: dict) -> str:
    """'fql' for a FraiseQL variant, 'other' otherwise — the figure/ground
    colour key: FraiseQL is the focus hue, every other engine a recessive
    neutral. Identity is never colour-alone; each bar carries its label."""
    return "fql" if meta["frameworks"][fw].get("family") == "fraiseql" else "other"


def _fmt_mb(v) -> str:
    return "—" if v is None else (f"{v:,.1f} MB" if v < 100 else f"{v:,.0f} MB")


def _fmt_cold(ms) -> str:
    return "—" if ms is None else f"{ms / 1000:.1f} s cold"


def _fmt_bytes(nbytes) -> str:
    """Adaptive size label: GB at/above a gigabyte, MB below — so the small
    tv_user/tb_user pair reads its true 14 MB vs 8 MB, not '0.01 GB' twice."""
    gb = nbytes / 1e9
    return f"{gb:.2f} GB" if gb >= 1 else f"{nbytes / 1e6:.0f} MB"


def _s6_legend() -> str:
    return (
        '<div class="s6-legend">'
        '<span><span class="s6-swatch s6-fill-fql"></span>FraiseQL</span>'
        '<span><span class="s6-swatch s6-fill-other"></span>other engines'
        '</span></div>')


def _s6_ram_row(row: FootprintRow, axis_max: float, meta: dict) -> str:
    fam = _fam(row.framework, meta)
    label = meta["frameworks"][row.framework]["label"]
    pct = _bar_pct(row.peak_ram_mb, axis_max)
    meta_bits = _fmt_cold(row.cold_start_ms)
    if row.image_mb:
        meta_bits += f" · {row.image_mb:,.0f} MB img"
    return (
        f'<div class="s6-row" data-framework="{esc(row.framework)}" '
        f'data-ram-mb="{esc(row.peak_ram_mb)}" '
        f'data-cold-ms="{esc(row.cold_start_ms)}">'
        f'<span class="s6-fw">{esc(label)}</span>'
        f'<span class="s6-track"><span class="s6-bar s6-fill-{fam}" '
        f'style="width:{svg.n(pct)}%"></span></span>'
        f'<span class="s6-val">{esc(_fmt_mb(row.peak_ram_mb))}'
        f'<span class="s6-sub">{esc(meta_bits)}</span></span></div>')


def _s6_ram_chart(rows: list, meta: dict) -> str:
    axis_max = svg.nice_axis(
        max((r.peak_ram_mb or 0 for r in rows), default=1.0), 5)[0]
    body = "".join(_s6_ram_row(r, axis_max, meta) for r in rows)
    axis = (
        '<div class="s6-axis" aria-hidden="true"><span>0</span>'
        f'<span>{fmt_rps(axis_max / 2)}</span>'
        f'<span>{fmt_rps(axis_max)} MB</span></div>')
    return (
        '<h3>Steady-state memory <span class="s6-unit">resident MB, '
        'lighter is better</span></h3>'
        + _s6_legend() + axis + f'<div class="s6-chart">{body}</div>')


def _s6_cost_row(row: CostRow, inst: str, axis_max: float, meta: dict) -> str:
    fam = _fam(row.framework, meta)
    label = meta["frameworks"][row.framework]["label"]
    per_m = row.per_million[inst]
    pct = _bar_pct(per_m, axis_max)
    sub = f"{row.rps_per_euro_month[inst]:,.0f} RPS/€mo · {fmt_rps(row.rps)} Q1"
    return (
        f'<div class="s6-row" data-framework="{esc(row.framework)}" '
        f'data-eur-per-million="{esc(round(per_m, 6))}">'
        f'<span class="s6-fw">{esc(label)}</span>'
        f'<span class="s6-track"><span class="s6-bar s6-fill-{fam}" '
        f'style="width:{svg.n(pct)}%"></span></span>'
        f'<span class="s6-val">€{per_m:.4f}'
        f'<span class="s6-sub">{esc(sub)}</span></span></div>')


def _s6_cost_chart(rows: list, cfg: dict, meta: dict) -> str:
    inst = cfg["headline_instance"]
    axis_max = svg.nice_axis(
        max((r.per_million[inst] for r in rows), default=1.0), 5)[0]
    body = "".join(_s6_cost_row(r, inst, axis_max, meta) for r in rows)
    axis = (
        '<div class="s6-axis" aria-hidden="true"><span>€0</span>'
        f'<span>€{axis_max / 2:.3f}</span>'
        f'<span>€{axis_max:.3f} / 1M</span></div>')
    return (
        f'<h3>Cost per million requests <span class="s6-unit">on {esc(inst)}, '
        'lower is better · derived</span></h3>'
        f'<p class="lede">{esc_text(cfg["summary"])}</p>'
        + _s6_legend() + axis + f'<div class="s6-chart">{body}</div>'
        f'<p class="footnote s6-formula">{esc_text(cfg["formula"])}<br>'
        f'{esc_text(cfg["price_note"])}</p>')


def _s6_storage(pairs: list, meta: dict) -> str:
    axis_max = svg.nice_axis(
        max((p.precompute_bytes for p in pairs), default=1.0), 5)[0]
    rows = ""
    for p in pairs:
        pc_pct = _bar_pct(p.precompute_bytes, axis_max)
        b_pct = _bar_pct(p.base_bytes, axis_max)
        rows += (
            f'<div class="s6-store" data-pair="{esc(p.precompute)}" '
            f'data-ratio="{esc(round(p.ratio, 3))}">'
            f'<div class="s6-store-head"><span class="s6-store-name">'
            f'{esc(p.precompute)} <span class="s6-store-vs">vs '
            f'{esc(p.base)}</span></span>'
            f'<span class="s6-ratio">{p.ratio:.1f}× the base table</span></div>'
            f'<div class="s6-store-bar"><span class="s6-store-lbl">precompute'
            f'</span><span class="s6-track"><span class="s6-bar s6-fill-fql" '
            f'style="width:{svg.n(pc_pct)}%"></span></span>'
            f'<span class="s6-val">{esc(_fmt_bytes(p.precompute_bytes))}</span>'
            f'</div>'
            f'<div class="s6-store-bar"><span class="s6-store-lbl">base</span>'
            f'<span class="s6-track"><span class="s6-bar s6-fill-other" '
            f'style="width:{svg.n(b_pct)}%"></span></span>'
            f'<span class="s6-val">{esc(_fmt_bytes(p.base_bytes))}</span></div>'
            '</div>')
    axis = (
        '<div class="s6-axis s6-axis-store" aria-hidden="true"><span>0</span>'
        f'<span>{_fmt_bytes(axis_max / 2)}</span>'
        f'<span>{_fmt_bytes(axis_max)}</span></div>')
    return (
        '<h3>The storage trade <span class="s6-unit">precomputed tv_* vs base '
        'tb_*, total on-disk size</span></h3>'
        f'<p class="lede">{esc_text(meta["footprint"]["db_summary"])}</p>'
        + axis + f'<div class="s6-store-chart">{rows}</div>')


def _s6_section(grid: Grid, run: Run, meta: dict, prices: dict) -> str:
    cfg = meta["footprint"]
    fp = footprint_rows(run, meta)
    costs = cost_composite(grid, prices, cfg["cost"]["scenario"])
    pairs = db_footprint_pairs(run, meta)
    # Each sub-chart is omitted (not faked) when its measurement wasn't captured
    # in this run, so a minimal sweep still renders a valid, honest section.
    body = f'<p class="lede">{esc_text(cfg["rss"]["summary"])}</p>'
    if any(r.peak_ram_mb is not None for r in fp):
        body += _s6_ram_chart(fp, meta)
    if costs:
        body += _s6_cost_chart(costs, cfg["cost"], meta)
    if pairs:
        body += _s6_storage(pairs, meta)
    return (
        '<section id="s6-footprint" aria-labelledby="s6-h">'
        '<h2 id="s6-h">S6 — Footprint &amp; cost</h2>'
        + body
        + '<p class="footnote">Memory, image size and cold start are measured; '
        'the cost figures are <em>derived</em> from measured throughput and the '
        'dated price file (formula above), not a separate measurement. Every '
        'raw number is also in the run JSON linked below. Prototype single-pass '
        'sweep; the Phase 06 median-of-three run refines the tail.</p>'
        '</section>')


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
// Shared scenario switcher (S0 anatomy + S2 mechanism ladder). Progressive
// enhancement only: it toggles [hidden] + aria-pressed on already-rendered
// per-scenario panels, so without JS the pre-rendered default is the story.
function vbSwitcher(o) {
  var btns = o.btnScope.querySelectorAll(o.btnSel);
  var panels = o.panelScope.querySelectorAll(o.panelSel);
  function set(sc) {
    if (o.stateEl) o.stateEl.setAttribute('data-scenario', sc);
    btns.forEach(function (b) {
      b.setAttribute('aria-pressed',
        b.getAttribute('data-scenario') === sc ? 'true' : 'false');
    });
    panels.forEach(function (p) {
      p.hidden = p.getAttribute('data-scenario') !== sc;
    });
  }
  btns.forEach(function (b) {
    b.addEventListener('click', function () {
      set(b.getAttribute('data-scenario'));
    });
  });
  return set;
}
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
(function () {
  // S0 request anatomy — progressive enhancement. Without this script the
  // static ladders + numbered hop lists are the full story; the controls stay
  // hidden and nothing animates. Motion is CSS (offset-path) gated behind
  // .s0-stage.playing, so this only toggles classes — it never drives frames.
  var stage = document.querySelector('.s0-stage');
  var controls = document.querySelector('.s0-controls');
  if (!stage || !controls) return;
  controls.hidden = false;
  vbSwitcher({ btnScope: controls, btnSel: '.s0-scn',
               panelScope: stage, panelSel: '.s0-variant', stateEl: stage });
  var play = document.getElementById('s0-play');
  if (play) {
    play.addEventListener('click', function () {
      if (!stage.classList.contains('playing')) {
        stage.classList.add('playing');
        stage.classList.remove('paused');
      } else {
        stage.classList.toggle('paused');
      }
      var started = stage.classList.contains('playing');
      var paused = stage.classList.contains('paused');
      play.setAttribute('aria-pressed', started && !paused ? 'true' : 'false');
      play.textContent = !started ? '\\u25BA Play the three requests'
        : paused ? '\\u25BA Resume' : '\\u2016 Pause';
    });
  }
})();
(function () {
  // S2 mechanism ladder — the shared scenario switcher, enhancing the
  // pre-rendered default. No motion, so no play button.
  var s2 = document.getElementById('s2-mechanism-ladder');
  if (!s2) return;
  var stage = s2.querySelector('.s2-stage');
  var controls = s2.querySelector('.s2-controls');
  if (!stage || !controls) return;
  controls.hidden = false;
  vbSwitcher({ btnScope: s2, btnSel: '.s2-scn',
               panelScope: stage, panelSel: '.s2-variant', stateEl: stage });
})();
</script>"""


def _render_index(run: Run, meta: dict, grid: Grid, prices: dict) -> str:
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
        _s2_section(grid, meta),
        _s3_section(grid, meta),
        _s4_section(grid, meta),
        _s5_section(grid, meta),
        _s6_section(grid, run, meta, prices),
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

def _render_data_json(run: Run, meta: dict, prices: dict) -> str:
    return json.dumps({"run": run.raw, "scenarios": meta, "costs": prices},
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


def render(run: Run, meta: dict, prices: dict | None = None) -> dict[str, bytes]:
    """Renderer: returns every output file as bytes. Deterministic for a given
    (run, meta, prices); ``prices`` defaults to the committed cost file so the
    common call stays two-argument, but a caller (or test) may pass an explicit
    dict to keep the render filesystem-free."""
    if prices is None:
        prices = load_prices()
    grid = build_grid(run, meta)
    return {
        "index.html": _render_index(run, meta, grid, prices).encode("utf-8"),
        "data.json": _render_data_json(run, meta, prices).encode("utf-8"),
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
    parser.add_argument(
        "--costs", type=Path, default=COSTS_PATH,
        help="path to the dated instance-price YAML (cost composite input)")
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
    prices = load_prices(args.costs)
    files = render(run, meta, prices)
    write_site(files, args.out)
    print(f"build.py: wrote {len(files)} file(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
