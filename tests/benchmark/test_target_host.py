"""Remote-target support for bench_sequential.py.

The two-instance benchmark topology (load generator on one host, frameworks on
another) requires every scenario URL to honour --target-host. The dry-run plan
must show the resolved URLs without touching Docker or the network.
"""

import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).parent / "bench_sequential.py"


def dry_run(*extra_args: str) -> str:
    # No --frameworks filter: the plan covers the full default framework list,
    # so a single hardcoded localhost URL anywhere in the table fails the test.
    result = subprocess.run(
        [sys.executable, str(BENCH), "--dry-run", *extra_args],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"dry-run failed: {result.stderr}"
    return result.stdout


def test_dry_run_default_targets_localhost():
    plan = dry_run()
    assert "http://localhost:" in plan


def test_target_host_replaces_localhost_everywhere():
    plan = dry_run("--target-host", "10.0.0.2")
    assert "http://10.0.0.2:" in plan
    assert "localhost" not in plan, "scenario URLs still hardcode localhost"
