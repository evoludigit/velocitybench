"""PostGraphile version gate for the publishable campaign.

Competitors run their latest stable release — benchmarking a stale
PostGraphile is the fastest way to get the report dismissed. Latest stable
at campaign time (2026-07) is the v5 line (Grafast executor), a different
architecture from the 2026-04-vintage v4 container this repo used to run.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PG_DIR = REPO_ROOT / "frameworks" / "postgraphile"

REQUIRED_MAJOR = 5


def test_package_requires_current_major():
    pkg = json.loads((PG_DIR / "package.json").read_text())
    spec = pkg["dependencies"]["postgraphile"]
    match = re.search(r"(\d+)", spec)
    assert match and int(match[1]) == REQUIRED_MAJOR, (
        f"postgraphile dependency is {spec!r}, campaign requires v{REQUIRED_MAJOR}.x"
    )


def test_lockfile_resolves_current_major():
    lock = json.loads((PG_DIR / "package-lock.json").read_text())
    entry = lock["packages"]["node_modules/postgraphile"]
    assert entry["version"].startswith(f"{REQUIRED_MAJOR}."), (
        f"lockfile pins postgraphile {entry['version']}, "
        f"campaign requires v{REQUIRED_MAJOR}.x"
    )


def test_docker_base_image_is_maintained_node():
    """Node 20 went EOL 2026-04 — the container must run a maintained LTS."""
    dockerfile = (PG_DIR / "Dockerfile").read_text()
    match = re.search(r"FROM node:(\d+)", dockerfile)
    assert match, "Dockerfile must pin a node major"
    assert int(match[1]) >= 22, f"node:{match[1]} is EOL; use node:22 LTS or newer"


def test_no_boot_time_ddl_against_shared_database():
    """Framework config belongs in the checked-in preset, not in COMMENT
    statements written into the shared benchmark database at startup."""
    sources = list((PG_DIR / "src").glob("*.ts"))
    offenders = [p.name for p in sources if "COMMENT ON" in p.read_text()]
    assert not offenders, f"boot-time smart-tag DDL still present in: {offenders}"
