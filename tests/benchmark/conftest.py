"""Pytest configuration for benchmarks."""

import sys
from pathlib import Path

# Add tests directory to path to import fixtures
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

# Import fixtures from tests/integration/conftest
from integration.conftest import fraiseql_server  # noqa: F401
