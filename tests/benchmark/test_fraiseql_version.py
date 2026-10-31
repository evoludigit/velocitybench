"""FraiseQL version gate.

The FraiseQL image runs one published release: frameworks/fraiseql/Dockerfile
downloads it (FRAISEQL_VERSION) and checks the asset's digest (FRAISEQL_SHA256),
unless binaries were injected into the Docker context, which must then report
the same version.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAISEQL_DIR = REPO_ROOT / "frameworks" / "fraiseql"
DOCKERFILE = (FRAISEQL_DIR / "Dockerfile").read_text()


def dockerfile_arg(name: str) -> str:
    match = re.search(rf"^ARG {name}=(\S+)$", DOCKERFILE, re.MULTILINE)
    assert match, f"Dockerfile declares no default for {name}"
    return match[1]


def test_the_dockerfile_pins_a_release_and_its_digest():
    assert re.fullmatch(r"\d+\.\d+\.\d+", dockerfile_arg("FRAISEQL_VERSION"))
    assert re.fullmatch(r"[0-9a-f]{64}", dockerfile_arg("FRAISEQL_SHA256"))
    assert 'sha256sum -c -' in DOCKERFILE


def test_compose_builds_the_version_the_dockerfile_pins():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    defaults = set(re.findall(r"FRAISEQL_VERSION: \$\{FRAISEQL_VERSION:-([^}]+)\}", compose))
    assert defaults == {dockerfile_arg("FRAISEQL_VERSION")}, defaults


def test_no_fraiseql_binary_is_tracked():
    tracked = subprocess.run(
        ["git", "ls-files", "frameworks/fraiseql/fraiseql-cli", "frameworks/fraiseql/fraiseql-server"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert tracked == [], tracked


@pytest.mark.parametrize("name", ["fraiseql-server", "fraiseql-cli"])
def test_an_injected_binary_reports_the_pinned_version(name):
    binary = FRAISEQL_DIR / name
    if not binary.exists():
        pytest.skip(f"no {name} injected: the image downloads the release")
    out = subprocess.run([str(binary), "--version"], capture_output=True, text=True, check=True).stdout
    assert dockerfile_arg("FRAISEQL_VERSION") in out, out
