"""Hasura wiring gate for the publishable campaign.

The report's central comparison is FraiseQL vs the schema-to-API engines
(Hasura, PostGraphile). Hasura must therefore:

- run its latest stable v2 CE release (v3/DDN is not benchmarkable
  self-hosted without the hosted control plane — documented methodology
  choice), pinned in exactly one place (the compose image tag),
- apply its metadata non-interactively at container start (cli-migrations
  image variant — a fresh clone reproduces the exact Hasura config),
- sit in the `benchmark` compose profile like every other framework,
- expose the full scenario row set through bench_sequential.py.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH = REPO_ROOT / "tests" / "benchmark" / "bench_sequential.py"

sys.path.insert(0, str(BENCH.parent))
import bench_sequential  # noqa: E402

# Latest stable Hasura v2 line at campaign time (2026-07). Bump deliberately;
# the compose tag must follow.
REQUIRED_MAJOR_MINOR = (2, 49)

REQUIRED_SCENARIOS = {"Q1", "Q2", "Q2b", "Q3", "F1", "F2", "M1", "T1"}


def _compose_hasura_image() -> str:
    text = (REPO_ROOT / "docker-compose.yml").read_text()
    match = re.search(r"image:\s*(hasura/graphql-engine:\S+)", text)
    assert match, "no hasura/graphql-engine image in docker-compose.yml"
    return match[1]


def test_hasura_registered_in_runner():
    assert "hasura" in bench_sequential.FRAMEWORKS, (
        "hasura missing from bench_sequential.FRAMEWORKS"
    )


def test_hasura_scenario_row_set():
    queries = bench_sequential.FRAMEWORKS["hasura"]["queries"]
    missing = REQUIRED_SCENARIOS - set(queries)
    assert not missing, f"hasura lacks scenarios: {sorted(missing)}"


def test_hasura_in_default_sweep_order():
    assert "hasura" in bench_sequential.DEFAULT_FRAMEWORK_ORDER


def test_hasura_dry_run_plan():
    result = subprocess.run(
        [sys.executable, str(BENCH), "--dry-run", "--frameworks", "hasura"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"dry-run failed: {result.stderr}"
    assert "/v1/graphql" in result.stdout, "hasura scenarios must hit /v1/graphql"


def test_hasura_version_recorded_from_version_endpoint():
    """/healthz returns plain text; the version probe needs /v1/version."""
    fw = bench_sequential.FRAMEWORKS["hasura"]
    assert fw.get("version_url", "").endswith("/v1/version")


def test_compose_image_is_current_stable_ce():
    image = _compose_hasura_image()
    tag = image.split(":", 1)[1]
    match = re.match(r"v(\d+)\.(\d+)\.\d+", tag)
    assert match, f"unpinned hasura tag: {tag}"
    assert (int(match[1]), int(match[2])) == REQUIRED_MAJOR_MINOR, (
        f"hasura is {tag}, campaign requires "
        f"v{REQUIRED_MAJOR_MINOR[0]}.{REQUIRED_MAJOR_MINOR[1]}.x (latest stable)"
    )
    assert "-ce" in tag, "pin the community-edition build (-ce tag)"


def test_compose_image_applies_metadata_at_start():
    """cli-migrations variant applies /hasura-metadata before serving —
    the non-interactive, reproducible metadata path."""
    assert ".cli-migrations-v3" in _compose_hasura_image()


def test_hasura_in_benchmark_profile():
    import yaml

    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    profiles = compose["services"]["hasura"].get("profiles", [])
    assert "benchmark" in profiles


def test_bench_one_uses_sequential_runner():
    """`make bench-one FRAMEWORK=x` must go through the canonical k6 path
    (bench_sequential.py), not the legacy full_suite.js mix."""
    mk = (REPO_ROOT / "make" / "framework.mk").read_text()
    recipe = mk.split("bench-one:", 1)[1].split("\n\n", 1)[0]
    assert "bench_sequential.py" in recipe, (
        "bench-one still uses the legacy k6 full_suite.js path"
    )
