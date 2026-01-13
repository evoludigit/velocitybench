"""Tests for load_profiler module."""

import sys
from pathlib import Path

import pytest

COSTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(COSTS_DIR))

from load_profiler import LoadProfiler, LoadProfile, LoadProjection


class TestLoadProfiler:
    """Test LoadProfiler class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        profiler = LoadProfiler()

        assert profiler.peak_multiplier == 2.5

    def test_init_custom_multiplier(self):
        """Test initialization with custom peak multiplier."""
        profiler = LoadProfiler(peak_multiplier=3.0)

        assert profiler.peak_multiplier == 3.0

    def test_project_from_jmeter(self, sample_jmeter_rps):
        """Test projecting from JMeter RPS."""
        profiler = LoadProfiler()

        projection = profiler.project_from_jmeter(sample_jmeter_rps)

        assert isinstance(projection, LoadProjection)
        assert projection.rps_average == sample_jmeter_rps
        assert projection.rps_peak == sample_jmeter_rps * 2.5
        assert projection.peak_variance == 2.5

    def test_projection_calculations(self, sample_jmeter_rps):
        """Test projection calculations are correct."""
        profiler = LoadProfiler()
        rps = sample_jmeter_rps

        projection = profiler.project_from_jmeter(rps)

        # Verify calculations
        assert projection.requests_per_minute == pytest.approx(rps * 60)
        assert projection.requests_per_hour == pytest.approx(rps * 3600)
        assert projection.requests_per_day == pytest.approx(rps * 86400)
        assert projection.requests_per_month == pytest.approx(rps * 86400 * 30)
        assert projection.requests_per_year == pytest.approx(
            rps * 86400 * 30 * 12
        )

    def test_projection_data_growth(self, sample_jmeter_rps):
        """Test data growth estimation."""
        profiler = LoadProfiler()

        projection = profiler.project_from_jmeter(sample_jmeter_rps)

        # Data growth should be positive
        assert projection.data_growth_gb_per_month > 0
        assert projection.logs_gb_per_month > 0

    def test_custom_peak_multiplier(self):
        """Test custom peak multiplier."""
        profiler = LoadProfiler(peak_multiplier=3.5)

        projection = profiler.project_from_jmeter(100.0)

        assert projection.rps_peak == 350.0

    def test_profile_from_load_profile_smoke(self):
        """Test SMOKE profile projection."""
        profiler = LoadProfiler()

        projection = profiler.profile_from_load_profile(LoadProfile.SMOKE)

        assert projection.rps_average == 10.0
        assert projection.rps_peak == 25.0

    def test_profile_from_load_profile_small(self):
        """Test SMALL profile projection."""
        profiler = LoadProfiler()

        projection = profiler.profile_from_load_profile(LoadProfile.SMALL)

        assert projection.rps_average == 50.0
        assert projection.rps_peak == 125.0

    def test_profile_from_load_profile_medium(self):
        """Test MEDIUM profile projection."""
        profiler = LoadProfiler()

        projection = profiler.profile_from_load_profile(LoadProfile.MEDIUM)

        assert projection.rps_average == 500.0
        assert projection.rps_peak == 1250.0

    def test_profile_from_load_profile_large(self):
        """Test LARGE profile projection."""
        profiler = LoadProfiler()

        projection = profiler.profile_from_load_profile(LoadProfile.LARGE)

        assert projection.rps_average == 5000.0

    def test_profile_from_load_profile_production(self):
        """Test PRODUCTION profile projection."""
        profiler = LoadProfiler()

        projection = profiler.profile_from_load_profile(LoadProfile.PRODUCTION)

        assert projection.rps_average == 10000.0

    def test_estimate_data_storage_one_year(self, sample_load_projection):
        """Test 1-year data storage estimation."""
        profiler = LoadProfiler()

        storage = profiler.estimate_data_storage(sample_load_projection, months=12)

        assert "data_gb" in storage
        assert "logs_gb" in storage
        assert "backups_gb" in storage
        assert "total_primary_gb" in storage
        assert "total_replicated_gb" in storage

        # Replicated should be more than primary
        assert storage["total_replicated_gb"] > storage["total_primary_gb"]

    def test_estimate_data_storage_with_compression(self, sample_load_projection):
        """Test data storage with custom compression ratio."""
        profiler = LoadProfiler()

        storage = profiler.estimate_data_storage(
            sample_load_projection, months=12, compression_ratio=0.8
        )

        # Lower compression ratio should give less total storage
        storage_uncompressed = profiler.estimate_data_storage(
            sample_load_projection, months=12, compression_ratio=1.0
        )

        assert storage["total_primary_gb"] < storage_uncompressed[
            "total_primary_gb"
        ]

    def test_estimate_monthly_storage(self, sample_load_projection):
        """Test monthly storage estimation."""
        profiler = LoadProfiler()

        storage = profiler.estimate_monthly_storage(sample_load_projection)

        assert "data_gb" in storage
        assert "logs_gb" in storage
        assert "total_gb" in storage

        # Total should be sum of data and logs
        assert storage["total_gb"] == pytest.approx(
            storage["data_gb"] + storage["logs_gb"]
        )

    def test_get_profile_description_smoke(self):
        """Test profile description for SMOKE."""
        profiler = LoadProfiler()

        desc = profiler.get_profile_description(LoadProfile.SMOKE)

        assert desc["name"] == "Smoke Test"
        assert desc["rps"] == 10

    def test_get_profile_description_all_profiles(self):
        """Test profile descriptions for all profiles."""
        profiler = LoadProfiler()

        for profile in LoadProfile:
            desc = profiler.get_profile_description(profile)

            assert "name" in desc
            assert "rps" in desc
            assert "use_case" in desc
            assert "typical_deployment" in desc

    def test_load_profile_enum_values(self):
        """Test LoadProfile enum has expected values."""
        assert LoadProfile.SMOKE.value == "smoke"
        assert LoadProfile.SMALL.value == "small"
        assert LoadProfile.MEDIUM.value == "medium"
        assert LoadProfile.LARGE.value == "large"
        assert LoadProfile.PRODUCTION.value == "production"
