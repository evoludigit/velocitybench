"""FraiseQL version gate.

The publishable benchmark must run against current FraiseQL (v2.10.x).
These binaries are COPY'd verbatim into the container image, so the binary
version is the container version.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAISEQL_DIR = REPO_ROOT / "frameworks" / "fraiseql"

REQUIRED_MAJOR_MINOR = (2, 10)


def binary_version(binary: Path) -> tuple[int, int, int]:
    out = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, check=True
    ).stdout
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    assert match, f"no semver in {binary.name} --version output: {out!r}"
    return (int(match[1]), int(match[2]), int(match[3]))


@pytest.mark.parametrize("name", ["fraiseql-server", "fraiseql-cli"])
def test_fraiseql_binary_is_current(name):
    version = binary_version(FRAISEQL_DIR / name)
    assert version[:2] == REQUIRED_MAJOR_MINOR, (
        f"{name} is v{'.'.join(map(str, version))}, "
        f"campaign requires v{REQUIRED_MAJOR_MINOR[0]}.{REQUIRED_MAJOR_MINOR[1]}.x"
    )


def test_dockerfile_matches_required_version():
    dockerfile = (FRAISEQL_DIR / "Dockerfile").read_text()
    stale = re.findall(r"v2\.[0-9]\.[0-9]+", dockerfile)
    assert not stale, f"Dockerfile still references stale versions: {stale}"
