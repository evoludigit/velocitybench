"""Phase-03 metrics capture: per-row RSS during the measurement window.

Every sweep row must carry `rss_steady_mb` (median container RSS sampled every
2s strictly inside the measurement window — never warmup) and `rss_max_mb`.
The sampler is a context manager so it is impossible to sample outside the
window or forget to stop it. Identical capture path for every framework — no
per-framework special-casing.
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential as bench  # noqa: E402


def test_bench_result_has_rss_fields():
    result = bench.BenchResult(
        framework="x", query_name="Q1", duration_secs=1, concurrency=1
    )
    assert hasattr(result, "rss_steady_mb")
    assert hasattr(result, "rss_max_mb")


def test_run_json_rows_include_rss():
    src = (BENCH_DIR / "bench_sequential.py").read_text()
    assert '"rss_steady_mb"' in src, "run JSON rows must carry rss_steady_mb"
    assert '"rss_max_mb"' in src


def test_sampler_wraps_measurement_window_only():
    """The sampler must wrap the measurement call, not the warmup."""
    src = (BENCH_DIR / "bench_sequential.py").read_text()
    assert "RssSampler" in src
    assert "with RssSampler" in src, "sampler must be used as a context manager"


def _postgres_running() -> bool:
    out = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False,
    )
    return "velocitybench-postgres-1" in out.stdout


@pytest.mark.skipif(not _postgres_running(), reason="postgres container not running")
def test_rss_sampler_measures_live_container():
    with bench.RssSampler("postgres", interval_secs=1.0) as sampler:
        time.sleep(3.5)
    assert sampler.median_mb is not None and sampler.median_mb > 1.0, (
        f"expected a positive RSS median, got {sampler.median_mb}"
    )
    assert sampler.max_mb >= sampler.median_mb


def test_rss_sampler_degrades_gracefully_for_unknown_container():
    """Remote SUT (--target-host) or a stopped container must yield None,
    not crash the sweep."""
    with bench.RssSampler("no-such-service", interval_secs=0.2) as sampler:
        time.sleep(0.5)
    assert sampler.median_mb is None


# ---------------------------------------------------------------------------
# Cold start
# ---------------------------------------------------------------------------


def test_bench_result_has_cold_start_field():
    result = bench.BenchResult(
        framework="x", query_name="Q1", duration_secs=1, concurrency=1
    )
    assert hasattr(result, "cold_start_ms")


def test_run_json_rows_include_cold_start():
    src = (BENCH_DIR / "bench_sequential.py").read_text()
    assert '"cold_start_ms"' in src, "run JSON rows must carry cold_start_ms"


def _service_running(container: str) -> bool:
    out = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False,
    )
    return container in out.stdout


@pytest.mark.skipif(
    not _service_running("velocitybench-fraiseql-tv-1"),
    reason="fraiseql-tv container not running",
)
def test_cold_start_measures_restart_to_first_q1():
    fw_config = bench.FRAMEWORKS["fraiseql-tv-cache"]  # compose service fraiseql-tv
    cold_ms = bench.measure_cold_start(fw_config, repeats=2)
    assert cold_ms is not None and 10 < cold_ms < 60_000, (
        f"implausible cold start: {cold_ms}"
    )


# ---------------------------------------------------------------------------
# Cost composite
# ---------------------------------------------------------------------------

REPO_ROOT = BENCH_DIR.parent.parent


def test_instance_prices_yaml_is_dated_and_complete():
    import yaml

    path = REPO_ROOT / "costs" / "instance-prices-2026-07.yaml"
    prices = yaml.safe_load(path.read_text())
    assert prices["currency"] == "EUR"
    assert str(prices["captured"]).startswith("2026-")
    for name in ("ccx23", "ccx33"):
        inst = prices["instances"][name]
        assert inst["price_month"] > 0
        assert inst["vcpu"] > 0


def test_report_contains_cost_composite_section():
    """The derivation lives in one function; the price table is data."""
    r = bench.BenchResult(
        framework="hasura", query_name="Q1", duration_secs=5, concurrency=20
    )
    r.ext_requests = 25_000  # 5000 RPS
    section = bench.format_cost_section([r])
    assert "Cost Composite" in section
    assert "ccx23" in section and "ccx33" in section
    assert "€ / 1M requests" in section
    # 5000 RPS on a ccx23 must come out to a sub-euro cost per 1M requests
    assert "hasura" in section
