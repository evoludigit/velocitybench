"""Shared fixtures for the site build tests.

Mirrors tests/benchmark/test_report_from_json.py discipline: the real sweep-3
Hetzner JSON is the primary fixture; a synthetic localhost run exercises the
banner path.
"""
import json
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent
REPO_DIR = SITE_DIR.parent
SWEEP3 = REPO_DIR / "reports/hetzner-2026-07/bench-hetzner-2026-07-05-sweep3.json"
SCENARIOS = SITE_DIR / "scenarios.json"

# Make `import build` resolve to site/build.py.
sys.path.insert(0, str(SITE_DIR))


@pytest.fixture()
def sweep3_path():
    if not SWEEP3.exists():
        pytest.skip(f"sweep-3 fixture missing: {SWEEP3}")
    return SWEEP3


@pytest.fixture()
def meta():
    import build
    return build.load_meta(SCENARIOS)


@pytest.fixture()
def sweep3_run(sweep3_path):
    import build
    return build.load_run(sweep3_path)


@pytest.fixture()
def grid(sweep3_run, meta):
    import build
    return build.build_grid(sweep3_run, meta)


@pytest.fixture()
def localhost_path(tmp_path):
    """A minimal but structurally valid run whose target_host is localhost."""
    doc = {
        "environment": {
            "timestamp": "2026-07-05T04:27:19+00:00",
            "cpu_model": "AMD EPYC-Genoa Processor",
            "kernel": "6.8.0-117-generic",
            "postgres_version": "17.10",
            "load_generator": "k6-v2.0.0",
            "target_host": "localhost",
            "concurrency": 40,
            "duration_secs": 30,
            "warmup_secs": 10,
            "cooldown_secs": 5,
            "passes": 1,
            "tview_mode": "logged",
            "tview_trigger_scope": "fraiseql-only",
        },
        "framework_versions": {"fraiseql-tv": "2.10.0"},
        "results": [
            {
                "framework": "fraiseql-tv", "query": "Q1", "pass": 1,
                "rps": 9000.0, "p50_ms": 3.0, "p95_ms": 6.0, "p99_ms": 9.0,
                "requests": 200000, "errors": 0, "error_breakdown": {},
                "rss_steady_mb": 10.2, "rss_max_mb": 10.4,
                "cold_start_ms": 1000.0, "skipped": False, "skip_reason": "",
            },
        ],
        "resource_metrics": [],
        "db_footprint": [],
    }
    path = tmp_path / "localhost-run.json"
    path.write_text(json.dumps(doc, indent=2))
    return path
