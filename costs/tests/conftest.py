"""Pytest fixtures for cost simulation tests."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
COSTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(COSTS_DIR))


@pytest.fixture
def cost_config():
    """Provide a CostConfiguration instance with default pricing."""
    from cost_config import CostConfiguration

    return CostConfiguration()


@pytest.fixture
def load_profiler():
    """Provide a LoadProfiler instance."""
    from load_profiler import LoadProfiler

    return LoadProfiler()


@pytest.fixture
def resource_calculator():
    """Provide a ResourceCalculator instance."""
    from resource_calculator import ResourceCalculator

    return ResourceCalculator()


@pytest.fixture
def sample_jmeter_rps():
    """Sample RPS value from JMeter benchmark."""
    return 125.3  # Typical web framework at SMALL load


@pytest.fixture
def sample_load_projection():
    """Sample LoadProjection from load profiler."""
    from load_profiler import LoadProfiler

    profiler = LoadProfiler()
    return profiler.project_from_jmeter(125.3)
