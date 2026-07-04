"""Phase-04 report regeneration: full markdown from the run JSON alone.

`bench_sequential.py --from-json <run.json>` must emit the complete report
with zero hand-editing: honesty note, methodology block (hardware/versions/
dataset/load-gen from the JSON `environment`), MC1 workflow-benchmark label,
logged/UNLOGGED tview stamp. Regeneration is byte-stable (same JSON in →
same MD out) so Phase 07 visual work never touches the sweep code.
"""

import json
import sys
from pathlib import Path

import pytest

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential as bench  # noqa: E402


@pytest.fixture()
def run_json(tmp_path):
    doc = {
        "environment": {
            "timestamp": "2026-07-04T12:00:00+02:00",
            "cpu_model": "13th Gen Intel(R) Core(TM) i7-13700K",
            "kernel": "7.0.9-arch1-1",
            "postgres_version": "PostgreSQL 16.6",
            "load_generator": "k6-1.0.0",
            "target_host": "localhost",
            "concurrency": 40,
            "duration_secs": 20,
            "warmup_secs": 5,
            "cooldown_secs": 5,
            "passes": 1,
            "tview_mode": "logged",
        },
        "framework_versions": {"fraiseql-tv": "2.10.0", "hasura": "v2.49.3-ce"},
        "results": [
            {
                "framework": "fraiseql-tv",
                "query": "Q1",
                "pass": 1,
                "rps": 10000.0,
                "p50_ms": 3.1,
                "p95_ms": 6.2,
                "p99_ms": 9.3,
                "requests": 200000,
                "errors": 0,
                "error_breakdown": {},
                "rss_steady_mb": 11.0,
                "rss_max_mb": 12.5,
                "cold_start_ms": 873.0,
                "skipped": False,
                "skip_reason": None,
            },
            {
                "framework": "fraiseql-tv",
                "query": "MC1",
                "pass": 1,
                "rps": 8000.0,
                "p50_ms": 4.0,
                "p95_ms": 8.0,
                "p99_ms": 12.0,
                "requests": 160000,
                "errors": 0,
                "error_breakdown": {},
                "rss_steady_mb": 11.0,
                "rss_max_mb": 12.5,
                "cold_start_ms": 873.0,
                "skipped": False,
                "skip_reason": None,
            },
        ],
        "resource_metrics": [
            {
                "framework": "fraiseql-tv",
                "loc": 500,
                "complexity_per_100_loc": 2.0,
                "image_mb": 40.0,
                "peak_ram_mb": 30.0,
                "avg_cpu_pct": 55.0,
            }
        ],
        "db_footprint": [
            {
                "table": "tb_user",
                "total_bytes": 10_000_000,
                "heap_bytes": 8_000_000,
                "indexes_bytes": 2_000_000,
            },
            {
                "table": "tv_user",
                "total_bytes": 20_000_000,
                "heap_bytes": 16_000_000,
                "indexes_bytes": 4_000_000,
            },
        ],
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(doc, indent=2))
    return path


def test_from_json_flag_exists():
    src = (BENCH_DIR / "bench_sequential.py").read_text()
    assert "--from-json" in src, "regeneration entry point missing"


def test_regenerated_report_contains_methodology_block(run_json):
    md = bench.regenerate_report_from_json(run_json)
    assert "## Methodology" in md
    assert "i7-13700K" in md, "CPU model from JSON environment"
    assert "7.0.9-arch1-1" in md, "kernel from JSON environment"
    assert "PostgreSQL 16.6" in md
    assert "k6-1.0.0" in md, "load generator identity"
    assert "10 000 users" in md, "dataset description"


def test_regenerated_report_contains_framework_versions(run_json):
    md = bench.regenerate_report_from_json(run_json)
    assert "2.10.0" in md
    assert "v2.49.3-ce" in md


def test_regenerated_report_contains_tview_stamp(run_json):
    md = bench.regenerate_report_from_json(run_json)
    assert "logged" in md
    # and the stamp flips for unlogged runs
    doc = json.loads(run_json.read_text())
    doc["environment"]["tview_mode"] = "unlogged"
    run_json.write_text(json.dumps(doc))
    md_unlogged = bench.regenerate_report_from_json(run_json)
    assert "UNLOGGED" in md_unlogged


def test_regenerated_report_contains_honesty_note(run_json):
    md = bench.regenerate_report_from_json(run_json)
    assert "## Reading These Numbers" in md
    assert "one sequential sweep" in md, "same-run rule"
    assert "mid-pack" in md, "Q1 honesty note"


def test_regenerated_report_contains_mc1_workflow_label(run_json):
    md = bench.regenerate_report_from_json(run_json)
    assert "cycles/second" in md or "cycles/s" in md
    assert "mutation-to-consistent-state" in md


def test_regeneration_is_byte_stable(run_json):
    assert bench.regenerate_report_from_json(run_json) == \
        bench.regenerate_report_from_json(run_json)


def test_rps_reconstruction_matches_json(run_json):
    """Q1 summary table must show the JSON's throughput, not zeros."""
    md = bench.regenerate_report_from_json(run_json)
    assert "10,000" in md or "10000" in md


def test_legacy_json_without_environment_keeps_rps(tmp_path):
    """Pre-July run JSONs lack the environment block; rps must still be
    reconstructed from the recorded per-row rps, not collapse to zero."""
    doc = {
        "results": [{
            "framework": "fraiseql-tv", "query": "Q1", "pass": 1,
            "rps": 9547.1, "p50_ms": 3.64, "p95_ms": 8.86, "p99_ms": 12.22,
            "requests": 286413, "errors": 0, "error_breakdown": {},
            "skipped": False, "skip_reason": "",
        }],
    }
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(doc))
    md = bench.regenerate_report_from_json(path)
    assert "9,547" in md or "9547" in md
