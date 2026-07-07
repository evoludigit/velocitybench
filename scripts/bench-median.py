#!/usr/bin/env python3
"""Merge N sweep JSONs into one publishable median run JSON.

Usage:
    bench-median.py sweep-A.json sweep-B.json sweep-C.json --output median.json

Every published number is the per-cell median across the input sweeps, with a
`spread` block per metric so the site/report can surface run-to-run variance
(min, max, stddev, rel_pct = (max-min)/|median|*100, n = sample count). The
output preserves the run-JSON contract the site consumes (environment,
framework_versions, results[], resource_metrics[], db_footprint[]) so
site/build.py reads it with zero changes; the median row keeps the same fields
plus `spread` and `samples`.

Same-run discipline: the merge REFUSES inputs whose environment (target_host,
tview_mode, load_generator) or framework_versions disagree — a median across
different hosts/versions is not a defensible number. Deterministic output
(sorted cells, no fresh timestamps) keeps it byte-stable: same inputs → same
bytes.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

# Per-cell result metrics that get median + spread. None samples are dropped.
RESULT_METRICS = (
    "rps", "p50_ms", "p95_ms", "p99_ms", "requests", "errors",
    "rss_steady_mb", "rss_max_mb", "cold_start_ms",
)
# Per-framework resource metrics and per-table footprint metrics: median only.
RESOURCE_METRICS = (
    "loc", "complexity_per_100_loc", "image_mb", "peak_ram_mb", "avg_cpu_pct",
)
FOOTPRINT_METRICS = ("total_bytes", "heap_bytes", "indexes_bytes")

# Environment keys that MUST agree across inputs for the median to be valid.
IDENTITY_KEYS = ("target_host", "tview_mode", "load_generator")


def _median_spread(values: list[float]) -> tuple[float | None, dict | None]:
    """Median plus a spread block; ints stay ints. None if no samples."""
    if not values:
        return None, None
    med = statistics.median(values)
    lo, hi = min(values), max(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    rel = round((hi - lo) / abs(med) * 100, 1) if med else 0.0
    if all(isinstance(v, int) for v in values):
        med = int(med) if med == int(med) else med
    else:
        med = round(med, 3)
    spread = {
        "n": len(values),
        "min": round(lo, 3) if isinstance(lo, float) else lo,
        "max": round(hi, 3) if isinstance(hi, float) else hi,
        "stddev": round(stdev, 3),
        "rel_pct": rel,
    }
    return med, spread


def _samples(rows: list[dict], metric: str) -> list[float]:
    out = []
    for r in rows:
        v = r.get(metric)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out.append(v)
    return out


def _check_same_run(runs: list[dict], paths: list[Path]) -> None:
    base_env = runs[0]["environment"]
    base_fv = runs[0]["framework_versions"]
    for run, path in zip(runs[1:], paths[1:]):
        for k in IDENTITY_KEYS:
            if run["environment"].get(k) != base_env.get(k):
                raise SystemExit(
                    f"REFUSED: {path.name} environment.{k}="
                    f"{run['environment'].get(k)!r} != {base_env.get(k)!r} "
                    f"({paths[0].name}). A median across different runs is not "
                    f"a defensible number.")
        if run["framework_versions"] != base_fv:
            diff = {k: (base_fv.get(k), run["framework_versions"].get(k))
                    for k in set(base_fv) | set(run["framework_versions"])
                    if base_fv.get(k) != run["framework_versions"].get(k)}
            raise SystemExit(
                f"REFUSED: {path.name} framework_versions differ: {diff}")


def merge(runs: list[dict], paths: list[Path]) -> dict:
    _check_same_run(runs, paths)

    # ── results: one median row per (framework, query) cell ────────────────
    cells: dict[tuple[str, str], list[dict]] = {}
    for run in runs:
        for row in run["results"]:
            cells.setdefault((row["framework"], row["query"]), []).append(row)

    merged_results = []
    for (fw, q), rows in sorted(cells.items()):
        # Prefer non-skipped samples; fall back to all if every sweep skipped.
        live = [r for r in rows if not r.get("skipped")] or rows
        row = {"framework": fw, "query": q, "pass": 1, "samples": len(live)}
        spreads = {}
        for m in RESULT_METRICS:
            med, sp = _median_spread(_samples(live, m))
            row[m] = med
            if sp is not None:
                spreads[m] = sp
        # error_breakdown: union summed across sweeps
        eb: dict[str, int] = {}
        for r in live:
            for k, v in (r.get("error_breakdown") or {}).items():
                eb[k] = eb.get(k, 0) + v
        row["error_breakdown"] = eb
        row["skipped"] = all(r.get("skipped") for r in rows)
        reasons = {r.get("skip_reason") for r in rows if r.get("skip_reason")}
        row["skip_reason"] = next(iter(reasons)) if len(reasons) == 1 else (
            "; ".join(sorted(reasons)) if reasons else None)
        row["spread"] = spreads
        merged_results.append(row)

    # ── resource_metrics: median per framework ─────────────────────────────
    res_by_fw: dict[str, list[dict]] = {}
    for run in runs:
        for r in run.get("resource_metrics", []):
            res_by_fw.setdefault(r["framework"], []).append(r)
    merged_resources = []
    for fw, rows in sorted(res_by_fw.items()):
        entry = {"framework": fw}
        for m in RESOURCE_METRICS:
            med, _ = _median_spread(_samples(rows, m))
            if med is not None:
                entry[m] = med
        merged_resources.append(entry)

    # ── db_footprint: median per table ─────────────────────────────────────
    fp_by_table: dict[str, list[dict]] = {}
    for run in runs:
        for r in run.get("db_footprint", []):
            fp_by_table.setdefault(r["table"], []).append(r)
    merged_footprint = []
    for table, rows in sorted(fp_by_table.items()):
        entry = {"table": table}
        for m in FOOTPRINT_METRICS:
            med, _ = _median_spread(_samples(rows, m))
            if med is not None:
                entry[m] = med
        merged_footprint.append(entry)

    # ── environment: carry base + record the merge provenance ──────────────
    env = dict(runs[0]["environment"])
    env["passes"] = len(runs)
    env["merge"] = {
        "method": "per-cell median",
        "n_sweeps": len(runs),
        "sources": [p.name for p in paths],
    }

    return {
        "environment": env,
        "framework_versions": runs[0]["framework_versions"],
        "results": merged_results,
        "resource_metrics": merged_resources,
        "db_footprint": merged_footprint,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", type=Path, nargs="+", help="Sweep JSONs to merge (>=2)")
    ap.add_argument("--output", "-o", type=Path, required=True, help="Median JSON path")
    args = ap.parse_args(argv)
    if len(args.runs) < 2:
        ap.error("need at least 2 sweeps to take a median")

    runs = [json.loads(p.read_text()) for p in args.runs]
    merged = merge(runs, args.runs)
    args.output.write_text(json.dumps(merged, indent=2) + "\n")

    # Variance summary: the worst-spread cells the report should footnote.
    worst = sorted(
        ((c["spread"].get("rps", {}).get("rel_pct", 0.0), c["framework"], c["query"])
         for c in merged["results"] if c.get("spread")),
        reverse=True)[:8]
    print(f"merged {len(args.runs)} sweeps → {args.output}  "
          f"({len(merged['results'])} cells, {len(merged['resource_metrics'])} "
          f"resource rows, {len(merged['db_footprint'])} footprint rows)")
    print("worst RPS spread (rel_pct  framework/scenario):")
    for pct, fw, q in worst:
        print(f"  {pct:5.1f}%  {fw}/{q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
