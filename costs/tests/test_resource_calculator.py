"""Tests for resource_calculator module."""

import sys
from pathlib import Path

import pytest

COSTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(COSTS_DIR))

from resource_calculator import ResourceCalculator, ResourceRequirements


class TestResourceCalculator:
    """Test ResourceCalculator class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        calc = ResourceCalculator()

        assert calc.rps_per_core == 100
        assert calc.app_memory_mb == 256
        assert calc.conn_pool_size == 50
        assert calc.memory_per_conn_mb == 5
        assert calc.app_storage_gb == 1

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        calc = ResourceCalculator(
            rps_per_core=50,
            app_memory_mb=512,
            conn_pool_size=100,
            memory_per_conn_mb=10,
            app_storage_gb=2,
        )

        assert calc.rps_per_core == 50
        assert calc.app_memory_mb == 512

    def test_calculate_cpu_cores_basic(self, sample_load_projection):
        """Test basic CPU core calculation."""
        calc = ResourceCalculator()

        cores = calc.calculate_cpu_cores(sample_load_projection)

        # Should be at least 1
        assert cores >= 1
        assert isinstance(cores, int)

    def test_calculate_cpu_cores_with_headroom(self, sample_load_projection):
        """Test CPU core calculation applies headroom."""
        calc = ResourceCalculator(rps_per_core=100)

        cores_no_headroom = sample_load_projection.rps_peak / 100
        cores_with_headroom = calc.calculate_cpu_cores(
            sample_load_projection, headroom_percent=30.0
        )

        # Should be more than without headroom
        assert cores_with_headroom > cores_no_headroom

    def test_calculate_cpu_cores_minimum_one(self):
        """Test CPU core calculation returns minimum 1."""
        from load_profiler import LoadProfiler

        profiler = LoadProfiler()
        # Very small load
        projection = profiler.project_from_jmeter(0.1)

        calc = ResourceCalculator(rps_per_core=1000)
        cores = calc.calculate_cpu_cores(projection, headroom_percent=0.0)

        assert cores >= 1

    def test_calculate_memory_gb(self):
        """Test memory calculation."""
        calc = ResourceCalculator()

        memory = calc.calculate_memory_gb()

        assert memory > 0
        assert isinstance(memory, float)

    def test_calculate_memory_includes_pool(self):
        """Test memory calculation includes connection pool."""
        app_mem = 256
        pool_size = 50
        mem_per_conn = 5

        calc = ResourceCalculator(
            app_memory_mb=app_mem,
            conn_pool_size=pool_size,
            memory_per_conn_mb=mem_per_conn,
        )

        memory = calc.calculate_memory_gb()

        # Total should be: (256 + 50*5) * 1.2 / 1024
        expected_mb = (app_mem + pool_size * mem_per_conn) * 1.2
        expected_gb = expected_mb / 1024

        assert memory == pytest.approx(expected_gb)

    def test_calculate_storage_gb(self, sample_load_projection):
        """Test storage calculation."""
        calc = ResourceCalculator()

        storage = calc.calculate_storage_gb(sample_load_projection)

        assert storage > 0
        assert isinstance(storage, float)

    def test_calculate_network_bandwidth(self, sample_load_projection):
        """Test network bandwidth calculation."""
        calc = ResourceCalculator()

        bandwidth = calc.calculate_network_bandwidth(sample_load_projection)

        assert bandwidth > 0
        assert isinstance(bandwidth, float)

    def test_calculate_requirements_complete(self, sample_load_projection):
        """Test complete resource requirements calculation."""
        calc = ResourceCalculator()

        requirements = calc.calculate_requirements(sample_load_projection)

        assert isinstance(requirements, ResourceRequirements)
        assert requirements.cpu_cores >= 1
        assert requirements.memory_gb > 0
        assert requirements.storage_gb > 0
        assert requirements.network_bandwidth_mbps > 0

    def test_calculate_requirements_custom_headroom(self, sample_load_projection):
        """Test requirements with custom headroom."""
        calc = ResourceCalculator()

        req_low = calc.calculate_requirements(
            sample_load_projection, cpu_headroom_percent=10.0
        )
        req_high = calc.calculate_requirements(
            sample_load_projection, cpu_headroom_percent=50.0
        )

        # Higher headroom should mean more cores
        assert req_high.cpu_cores >= req_low.cpu_cores

    def test_get_resource_profile_description(self, sample_load_projection):
        """Test resource profile description."""
        calc = ResourceCalculator()
        requirements = calc.calculate_requirements(sample_load_projection)

        desc = calc.get_resource_profile_description(requirements)

        assert "cpu" in desc
        assert "memory" in desc
        assert "storage" in desc
        assert "network" in desc

        # Check CPU description
        assert "cores" in desc["cpu"]
        assert "description" in desc["cpu"]
        assert "suitable_for" in desc["cpu"]

    def test_resource_profile_suitable_for_light(self):
        """Test resource profile description for light load."""
        calc = ResourceCalculator()

        requirements = ResourceRequirements(
            cpu_cores=1,
            memory_gb=2.0,
            storage_gb=10,
            network_bandwidth_mbps=10,
        )

        desc = calc.get_resource_profile_description(requirements)

        assert desc["cpu"]["suitable_for"] == "light"
        assert desc["memory"]["suitable_for"] == "lightweight"

    def test_resource_profile_suitable_for_heavy(self):
        """Test resource profile description for heavy load."""
        calc = ResourceCalculator()

        requirements = ResourceRequirements(
            cpu_cores=16,
            memory_gb=64.0,
            storage_gb=1000,
            network_bandwidth_mbps=1000,
        )

        desc = calc.get_resource_profile_description(requirements)

        assert desc["cpu"]["suitable_for"] == "very heavy"
        assert desc["memory"]["suitable_for"] == "large"

    def test_calculate_storage_with_replication(self, sample_load_projection):
        """Test storage calculation with replication factor."""
        calc = ResourceCalculator()

        storage_1x = calc.calculate_storage_gb(
            sample_load_projection, replication_factor=1.0
        )
        storage_2x = calc.calculate_storage_gb(
            sample_load_projection, replication_factor=2.0
        )

        # 2x replication should be roughly 2x storage
        assert storage_2x > storage_1x

    def test_calculate_storage_months_projection(self, sample_load_projection):
        """Test storage calculation with different month projections."""
        calc = ResourceCalculator()

        storage_6m = calc.calculate_storage_gb(sample_load_projection, months=6)
        storage_12m = calc.calculate_storage_gb(sample_load_projection, months=12)
        storage_24m = calc.calculate_storage_gb(sample_load_projection, months=24)

        # More months = more storage for data growth
        assert storage_12m > storage_6m
        assert storage_24m > storage_12m
