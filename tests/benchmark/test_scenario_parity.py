"""Pytest wrapper for the scenario parity audit.

Requires the audited engines and the FraiseQL reference to be running:

    docker compose up -d postgres fraiseql-tv-nocache hasura postgraphile

Skips (rather than fails) when the services are down, so the module can sit
in the default suite; the mandatory enforcement happens in bench_sequential's
pre-sweep gate.
"""

import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_sequential as bench  # noqa: E402
import scenario_parity  # noqa: E402


def _up(fw_name: str) -> bool:
    url = bench.FRAMEWORKS[fw_name]["health_url"]
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


_required = (scenario_parity.REFERENCE, *scenario_parity.AUDITED)
_down = [fw for fw in _required if not _up(fw)]


@pytest.mark.skipif(
    bool(_down), reason=f"services not running: {_down} — start them via docker compose"
)
def test_scenario_parity_audit():
    failures = scenario_parity.run_audit()
    assert not failures, "parity audit failed:\n" + "\n".join(f"  ✗ {f}" for f in failures)


def test_parity_gate_wired_into_sweep():
    """The audit must be a mandatory pre-sweep gate, not an optional check."""
    src = (Path(__file__).resolve().parent / "bench_sequential.py").read_text()
    assert "run_parity_gate(" in src
    assert "--skip-parity-gate" in src, "explicit opt-out flag must exist (debug only)"


def test_audited_engines_cover_schema_to_api_category():
    assert set(scenario_parity.AUDITED) == {"hasura", "postgraphile"}
    assert scenario_parity.REFERENCE.startswith("fraiseql")
