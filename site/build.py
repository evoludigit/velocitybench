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

BUILD_DIR = Path(__file__).resolve().parent
SCENARIOS_PATH = BUILD_DIR / "scenarios.json"

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
# Rendering (pure: run + meta -> {relpath: bytes})
# --------------------------------------------------------------------------

def _render_index(run: Run, meta: dict, grid: Grid) -> str:
    """Phase 01 placeholder skeleton. Phases 02+ replace this body with the
    real semantic page; kept intentionally minimal and deterministic."""
    env = run.environment
    banner = ""
    if run.is_local:
        banner = f'  <div class="banner" role="alert">{BANNER_TEXT}</div>\n'
    title = "VelocityBench — benchmark explorer"
    counts = {STATUS_RESULT: 0, STATUS_EXCLUDED: 0, STATUS_NOT_MEASURED: 0}
    for c in grid.cells.values():
        counts[c.status] += 1
    run_id = " · ".join([
        html.escape(str(env.get("timestamp", ""))),
        html.escape(str(env.get("target_host", ""))),
        "FraiseQL " + html.escape(str(
            run.framework_versions.get("fraiseql-tv", "?"))),
    ])
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n"
        "</head>\n<body>\n"
        f"{banner}"
        f"<h1>{html.escape(title)}</h1>\n"
        f'<p class="run-identity">{run_id}</p>\n'
        f"<p>Grid: {counts[STATUS_RESULT]} measured, "
        f"{counts[STATUS_EXCLUDED]} excluded by design, "
        f"{counts[STATUS_NOT_MEASURED]} not measured in this run.</p>\n"
        "<!-- Phase 02 replaces this placeholder with the full grid, "
        "honesty devices and AI layer. -->\n"
        "</body>\n</html>\n"
    )


def render(run: Run, meta: dict) -> dict[str, bytes]:
    """Pure renderer: returns every output file as bytes. Tests never touch
    the filesystem twice."""
    grid = build_grid(run, meta)
    index = _render_index(run, meta, grid)
    return {"index.html": index.encode("utf-8")}


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
