"""Phase-05 Hetzner IaC: single SUT+loadgen pair, one-command lifecycle.

`scripts/hetzner/bench-run.sh` provisions CCX33 (SUT) + CCX23 (loadgen),
runs two sequential sweeps of the publishable subset, fetches results,
prints a cost note, and destroys everything scoped to the campaign label.
`--plan` prints every action without calling the hcloud API — these tests
exercise exactly that mode (no credentials, no API).
"""

import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "hetzner" / "bench-run.sh"
PRICES_YAML = REPO_ROOT / "costs" / "instance-prices-2026-07.yaml"


def _plan(*extra_args):
    """Run --plan with hcloud guaranteed absent from PATH."""
    env = dict(os.environ)
    env["PATH"] = "/usr/bin:/bin"  # no user-local hcloud
    env.pop("HCLOUD_TOKEN", None)
    return subprocess.run(
        ["bash", str(SCRIPT), "--plan", *extra_args],
        capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False,
    )


def test_script_exists_and_is_executable():
    assert SCRIPT.exists(), "scripts/hetzner/bench-run.sh missing"
    assert SCRIPT.stat().st_mode & stat.S_IXUSR


def test_script_syntax_is_valid():
    proc = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_plan_succeeds_without_hcloud_or_token():
    proc = _plan()
    assert proc.returncode == 0, proc.stderr


def test_plan_names_instance_types_and_label():
    out = _plan().stdout
    assert "ccx33" in out, "SUT type"
    assert "cpx42" in out, "loadgen type (dedicated-core quota fallback)"
    assert "velocitybench=2026-07" in out, "campaign label"


def test_plan_covers_full_lifecycle():
    out = _plan().stdout.lower()
    for step in ("network", "headroom", "sweep 1", "sweep 2",
                 "bench-delta", "rsync", "destroy"):
        assert step in out, f"lifecycle step missing from plan: {step}"


def test_plan_reads_prices_from_yaml_not_hardcoded():
    src = SCRIPT.read_text()
    assert "0.2219" not in src, "price hardcoded — must come from the YAML"
    assert "0.1114" not in src, "price hardcoded — must come from the YAML"
    out = _plan().stdout
    assert "0.2219" in out and "0.1114" in out, "plan must show YAML prices"


def test_plan_destroy_is_label_scoped():
    out = _plan().stdout
    destroy_lines = [ln for ln in out.splitlines() if "delete" in ln.lower()
                     or "destroy" in ln.lower()]
    assert destroy_lines, "no destroy step in plan"
    assert any("velocitybench=2026-07" in ln for ln in destroy_lines), \
        "destruction must be scoped to the campaign label"


def test_keep_flag_skips_destruction():
    out = _plan("--keep").stdout.lower()
    assert "skip" in out and ("destroy" in out or "destruction" in out)


def test_prices_yaml_still_has_expected_shape():
    text = PRICES_YAML.read_text()
    assert "ccx33" in text and "ccx23" in text and "price_hour" in text
