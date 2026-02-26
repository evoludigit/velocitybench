"""Tests for cost_config module."""

import sys
from pathlib import Path


COSTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(COSTS_DIR))

from cost_config import (
    CostConfiguration,
    InstancePricing,
    DatabasePricing,
)


class TestCostConfiguration:
    """Test CostConfiguration class."""

    def test_init_with_defaults(self):
        """Test initialization with default pricing."""
        config = CostConfiguration()

        assert len(config.instances) > 0
        assert len(config.databases) > 0
        assert len(config.storage) > 0
        assert len(config.transfer) > 0

    def test_load_default_pricing(self):
        """Test default pricing is loaded."""
        config = CostConfiguration()

        # Check specific instances exist
        assert "aws_t3_micro" in config.instances
        assert "aws_m5_xlarge" in config.instances

        # Check pricing data is reasonable
        micro = config.get_instance("aws_t3_micro")
        assert micro is not None
        assert micro.cpu_cores == 1
        assert micro.memory_gb == 1.0
        assert 0 < micro.aws_hourly < 0.02

    def test_get_instance(self):
        """Test getting instance pricing."""
        config = CostConfiguration()

        micro = config.get_instance("aws_t3_micro")
        assert micro is not None
        assert isinstance(micro, InstancePricing)
        assert micro.instance_id == "t3.micro"

    def test_get_nonexistent_instance(self):
        """Test getting nonexistent instance returns None."""
        config = CostConfiguration()

        result = config.get_instance("nonexistent")
        assert result is None

    def test_get_database(self):
        """Test getting database pricing."""
        config = CostConfiguration()

        db = config.get_database("aws_t3_micro")
        assert db is not None
        assert isinstance(db, DatabasePricing)

    def test_get_compute_instances_for_cores(self):
        """Test filtering instances by core count."""
        config = CostConfiguration()

        instances = config.get_compute_instances_for_cores(min_cores=4)

        assert len(instances) > 0
        # All instances should have at least 4 cores
        for inst in instances:
            assert inst.cpu_cores >= 4

        # Should be sorted by AWS hourly cost
        for i in range(len(instances) - 1):
            assert instances[i].aws_hourly <= instances[i + 1].aws_hourly

    def test_get_database_instances_for_cores(self):
        """Test filtering database instances by core count."""
        config = CostConfiguration()

        dbs = config.get_database_instances_for_cores(min_cores=2)

        assert len(dbs) > 0
        for db in dbs:
            assert db.cpu_cores >= 2

    def test_instance_pricing_structure(self):
        """Test instance pricing has all cloud providers."""
        config = CostConfiguration()

        instance = config.get_instance("aws_t3_small")
        assert instance is not None

        # Check all cloud providers have pricing
        assert instance.aws_hourly > 0
        assert instance.gcp_hourly > 0
        assert instance.azure_hourly > 0

        # Check reserved pricing exists
        assert instance.aws_1yr_reserved > 0
        assert instance.aws_3yr_reserved > 0

    def test_pricing_consistency(self):
        """Test pricing is consistent across instances."""
        config = CostConfiguration()

        # Reserved should be cheaper than on-demand
        for instance in config.instances.values():
            assert instance.aws_1yr_reserved < instance.aws_hourly
            assert instance.aws_3yr_reserved < instance.aws_1yr_reserved

    def test_estimate_annual_cost_with_reserved(self):
        """Test annual cost estimation with reserved instances."""
        config = CostConfiguration()

        monthly = 100.0

        # On-demand only
        result = config.estimate_annual_cost_with_reserved(monthly)
        assert result["on_demand"] == 1200.0

        # With 1-year reserved
        result = config.estimate_annual_cost_with_reserved(
            monthly, reserved_term_years=1
        )
        assert "1yr_reserved" in result
        assert result["1yr_reserved"] == 1200.0 * 0.60  # 40% discount

        # With 3-year reserved
        result = config.estimate_annual_cost_with_reserved(
            monthly, reserved_term_years=3
        )
        assert "3yr_reserved" in result
        assert result["3yr_reserved"] == 1200.0 * 0.45  # 55% discount

    def test_storage_pricing(self):
        """Test storage pricing is configured."""
        config = CostConfiguration()

        # Check storage options exist
        assert len(config.storage) > 0

        # Get a storage option
        storage = list(config.storage.values())[0]
        assert storage.provider in ["aws", "gcp", "azure"]
        assert storage.gb_per_month > 0

    def test_transfer_pricing(self):
        """Test data transfer pricing is configured."""
        config = CostConfiguration()

        # Check all cloud providers have transfer pricing
        assert "aws" in config.transfer
        assert "gcp" in config.transfer
        assert "azure" in config.transfer

        for provider, pricing in config.transfer.items():
            assert pricing.gb_egress > 0
