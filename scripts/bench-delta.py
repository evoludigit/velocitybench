#!/usr/bin/env python3
"""Per-cell delta comparison between two bench_sequential run JSONs.

Usage:
    bench-delta.py run-A.json run-B.json [--cell-threshold 5.0]
                   [--max-flagged-fraction 0.25] [--output delta.md]

Every (framework, query) cell present in both runs is compared across the
metrics rps / p50_ms / p99_ms as a percentage delta (B relative to A). Cells
whose absolute delta exceeds --cell-threshold are flagged; cells present in
only one run count as flagged for every metric. The exit code is non-zero
when the flagged fraction of all compared cells exceeds
--max-flagged-fraction — which makes this tool usable as an acceptance gate:

    bench-delta.py sweep1.json sweep2.json || echo "variance gate FAILED"

Skipped rows are excluded. Multi-pass runs collapse to the per-cell median
before comparison.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

METRICS = ("rps", "p50_ms", "p99_ms")


@dataclass
class CellDelta:
    framework: str
    query: str
    metric: str
    value_a: float
    value_b: float
    delta_pct: float
    flagged: bool


@dataclass
class DeltaReport:
    cells: list[CellDelta]
    missing: list[tuple[str, str]]  # (framework, query) present in only one run
    cell_threshold_pct: float
    metrics: tuple[str, ...] = METRICS

    @property
    def flagged_count(self) -> int:
        return sum(c.flagged for c in self.cells) + len(self.missing) * len(self.metrics)

    @property
    def total_count(self) -> int:
        return len(self.cells) + len(self.missing) * len(self.metrics)

    @property
    def flagged_fraction(self) -> float:
        return self.flagged_count / self.total_count if self.total_count else 0.0


def extract_cells(run_doc: dict) -> dict[tuple[str, str], dict[str, float]]:
    """Index run-JSON rows by (framework, query) → {metric: median across passes}."""
    samples: dict[tuple[str, str], dict[str, list[float]]] = {}
    for row in run_doc.get("results", []):
        if row.get("skipped"):
            continue
        key = (row["framework"], row["query"])
        per_metric = samples.setdefault(key, {m: [] for m in METRICS})
        for metric in METRICS:
            per_metric[metric].append(float(row[metric]))
    return {
        key: {m: statistics.median(vals) for m, vals in per_metric.items()}
        for key, per_metric in samples.items()
    }


def compute_deltas(
    cells_a: dict[tuple[str, str], dict[str, float]],
    cells_b: dict[tuple[str, str], dict[str, float]],
    cell_threshold_pct: float = 5.0,
) -> DeltaReport:
    deltas: list[CellDelta] = []
    common = sorted(cells_a.keys() & cells_b.keys())
    missing = sorted(cells_a.keys() ^ cells_b.keys())
    for fw, query in common:
        for metric in METRICS:
            a, b = cells_a[(fw, query)][metric], cells_b[(fw, query)][metric]
            delta_pct = ((b - a) / a * 100.0) if a else (0.0 if b == a else float("inf"))
            deltas.append(CellDelta(
                framework=fw,
                query=query,
                metric=metric,
                value_a=a,
                value_b=b,
                delta_pct=delta_pct,
                flagged=abs(delta_pct) > cell_threshold_pct,
            ))
    return DeltaReport(cells=deltas, missing=missing, cell_threshold_pct=cell_threshold_pct)


def format_report(report: DeltaReport, label_a: str, label_b: str,
                  max_flagged_fraction: float) -> str:
    lines = [
        "# Run-to-Run Delta Report",
        "",
        f"**Run A**: {label_a}  ",
        f"**Run B**: {label_b}  ",
        f"**Cell threshold**: ±{report.cell_threshold_pct:g}%  ",
        "",
        "| Framework | Query | Metric | A | B | Δ% | |",
        "|-----------|-------|--------|--:|--:|---:|--|",
    ]
    for c in report.cells:
        mark = "⚠" if c.flagged else ""
        lines.append(
            f"| {c.framework} | {c.query} | {c.metric} "
            f"| {c.value_a:.1f} | {c.value_b:.1f} | {c.delta_pct:+.1f} | {mark} |"
        )
    if report.missing:
        lines += ["", "## Missing cells (present in only one run — count as flagged)", ""]
        lines += [f"- {fw} / {query}" for fw, query in report.missing]
    verdict = "PASS" if report.flagged_fraction <= max_flagged_fraction else "FAIL"
    lines += [
        "",
        f"**Summary**: {report.flagged_count}/{report.total_count} cells flagged "
        f"({report.flagged_fraction:.1%}) — gate limit {max_flagged_fraction:.0%} "
        f"→ **{verdict}**",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("run_a", type=Path, help="Baseline run JSON")
    parser.add_argument("run_b", type=Path, help="Comparison run JSON")
    parser.add_argument(
        "--cell-threshold", type=float, default=5.0, metavar="PCT",
        help="Flag any cell whose |delta| exceeds this percentage (default: 5)",
    )
    parser.add_argument(
        "--max-flagged-fraction", type=float, default=0.25, metavar="FRAC",
        help="Exit non-zero when flagged/total exceeds this fraction (default: 0.25)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Also write the markdown report to this path",
    )
    args = parser.parse_args(argv)

    try:
        doc_a = json.loads(args.run_a.read_text())
        doc_b = json.loads(args.run_b.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = compute_deltas(
        extract_cells(doc_a), extract_cells(doc_b),
        cell_threshold_pct=args.cell_threshold,
    )
    if not report.total_count:
        print("error: no comparable cells in either run", file=sys.stderr)
        return 2

    text = format_report(report, str(args.run_a), str(args.run_b),
                         args.max_flagged_fraction)
    print(text)
    if args.output:
        args.output.write_text(text)
    return 0 if report.flagged_fraction <= args.max_flagged_fraction else 1


if __name__ == "__main__":
    sys.exit(main())
