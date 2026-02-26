"""Cloud provider pricing configuration and models.

Manages pricing data for AWS, GCP, and Azure cloud providers including:
- Compute instances (on-demand and reserved)
- Database instances and storage
- Storage costs
- Data transfer and egress
"""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class InstancePricing:
    """Pricing for a specific instance type across cloud providers."""

    instance_id: str
    cpu_cores: int
    memory_gb: float
    aws_hourly: float
    gcp_hourly: float
    azure_hourly: float
    aws_1yr_reserved: float  # 40% discount
    aws_3yr_reserved: float  # 55% discount
    gcp_1yr_reserved: float
    gcp_3yr_reserved: float
    azure_1yr_reserved: float
    azure_3yr_reserved: float


@dataclass
class DatabasePricing:
    """Pricing for managed database instances."""

    instance_id: str
    cpu_cores: int
    memory_gb: float
    aws_hourly: float
    gcp_hourly: float
    azure_hourly: float


@dataclass
class StoragePricing:
    """Pricing for cloud storage services."""

    provider: str  # "aws", "gcp", "azure"
    service: str  # "ebs", "s3", "gcs", "blob"
    gb_per_month: float  # Storage cost per GB/month
    api_requests_per_million: float  # Cost per 1M API requests


@dataclass
class DataTransferPricing:
    """Pricing for data transfer and egress."""

    provider: str  # "aws", "gcp", "azure"
    gb_egress: float  # Cost per GB of data egress


class CostConfiguration:
    """Manages cloud provider pricing data and configurations.

    Loads pricing models from configuration files and provides
    lookups for compute, database, and storage costs across
    AWS, GCP, and Azure.
    """

    def __init__(self, config_file: str | None = None):
        """Initialize cost configuration.

        Args:
            config_file: Path to cost-config.json. If None, uses default fixtures.
        """
        self.instances: dict[str, InstancePricing] = {}
        self.databases: dict[str, DatabasePricing] = {}
        self.storage: dict[str, StoragePricing] = {}
        self.transfer: dict[str, DataTransferPricing] = {}

        if config_file:
            self.load_from_file(config_file)
        else:
            self._load_default_pricing()

    def _load_default_pricing(self) -> None:
        """Load default pricing models (AWS primary, GCP/Azure secondary).

        Uses conservative US region pricing for 2026.
        """
        # AWS EC2 instances - t3/m5 family (common for web workloads)
        self.instances["aws_t3_micro"] = InstancePricing(
            instance_id="t3.micro",
            cpu_cores=1,
            memory_gb=1.0,
            aws_hourly=0.0104,
            gcp_hourly=0.0149,
            azure_hourly=0.012,
            aws_1yr_reserved=0.0062,  # 40% off
            aws_3yr_reserved=0.0047,  # 55% off
            gcp_1yr_reserved=0.0089,
            gcp_3yr_reserved=0.0067,
            azure_1yr_reserved=0.0072,
            azure_3yr_reserved=0.0054,
        )

        self.instances["aws_t3_small"] = InstancePricing(
            instance_id="t3.small",
            cpu_cores=2,
            memory_gb=2.0,
            aws_hourly=0.0208,
            gcp_hourly=0.0298,
            azure_hourly=0.024,
            aws_1yr_reserved=0.0125,
            aws_3yr_reserved=0.0094,
            gcp_1yr_reserved=0.0179,
            gcp_3yr_reserved=0.0134,
            azure_1yr_reserved=0.0144,
            azure_3yr_reserved=0.0108,
        )

        self.instances["aws_t3_medium"] = InstancePricing(
            instance_id="t3.medium",
            cpu_cores=2,
            memory_gb=4.0,
            aws_hourly=0.0416,
            gcp_hourly=0.0596,
            azure_hourly=0.048,
            aws_1yr_reserved=0.0250,
            aws_3yr_reserved=0.0187,
            gcp_1yr_reserved=0.0357,
            gcp_3yr_reserved=0.0268,
            azure_1yr_reserved=0.0288,
            azure_3yr_reserved=0.0216,
        )

        self.instances["aws_m5_large"] = InstancePricing(
            instance_id="m5.large",
            cpu_cores=2,
            memory_gb=8.0,
            aws_hourly=0.096,
            gcp_hourly=0.1370,
            azure_hourly=0.1090,
            aws_1yr_reserved=0.0576,
            aws_3yr_reserved=0.0432,
            gcp_1yr_reserved=0.0822,
            gcp_3yr_reserved=0.0616,
            azure_1yr_reserved=0.0654,
            azure_3yr_reserved=0.0490,
        )

        self.instances["aws_m5_xlarge"] = InstancePricing(
            instance_id="m5.xlarge",
            cpu_cores=4,
            memory_gb=16.0,
            aws_hourly=0.192,
            gcp_hourly=0.2740,
            azure_hourly=0.2180,
            aws_1yr_reserved=0.1152,
            aws_3yr_reserved=0.0864,
            gcp_1yr_reserved=0.1644,
            gcp_3yr_reserved=0.1232,
            azure_1yr_reserved=0.1308,
            azure_3yr_reserved=0.0980,
        )

        self.instances["aws_m5_2xlarge"] = InstancePricing(
            instance_id="m5.2xlarge",
            cpu_cores=8,
            memory_gb=32.0,
            aws_hourly=0.384,
            gcp_hourly=0.5480,
            azure_hourly=0.4360,
            aws_1yr_reserved=0.2304,
            aws_3yr_reserved=0.1728,
            gcp_1yr_reserved=0.3288,
            gcp_3yr_reserved=0.2464,
            azure_1yr_reserved=0.2616,
            azure_3yr_reserved=0.1960,
        )

        # RDS/Database instances
        self.databases["aws_t3_micro"] = DatabasePricing(
            instance_id="db.t3.micro",
            cpu_cores=1,
            memory_gb=1.0,
            aws_hourly=0.0190,
            gcp_hourly=0.0290,
            azure_hourly=0.0220,
        )

        self.databases["aws_t3_small"] = DatabasePricing(
            instance_id="db.t3.small",
            cpu_cores=1,
            memory_gb=2.0,
            aws_hourly=0.0380,
            gcp_hourly=0.0580,
            azure_hourly=0.0440,
        )

        self.databases["aws_t3_medium"] = DatabasePricing(
            instance_id="db.t3.medium",
            cpu_cores=2,
            memory_gb=4.0,
            aws_hourly=0.0760,
            gcp_hourly=0.1160,
            azure_hourly=0.0880,
        )

        # Storage pricing (per GB per month)
        self.storage["aws_ebs_gp3"] = StoragePricing(
            provider="aws",
            service="ebs",
            gb_per_month=0.10,
            api_requests_per_million=0.00,
        )

        self.storage["aws_s3_standard"] = StoragePricing(
            provider="aws",
            service="s3",
            gb_per_month=0.023,
            api_requests_per_million=0.0004,
        )

        self.storage["gcp_pd_ssd"] = StoragePricing(
            provider="gcp",
            service="gcs",
            gb_per_month=0.17,
            api_requests_per_million=0.0004,
        )

        self.storage["gcp_gcs_standard"] = StoragePricing(
            provider="gcp",
            service="gcs",
            gb_per_month=0.020,
            api_requests_per_million=0.0004,
        )

        self.storage["azure_blob_hot"] = StoragePricing(
            provider="azure",
            service="blob",
            gb_per_month=0.0184,
            api_requests_per_million=0.0004,
        )

        # Data transfer pricing (per GB egress)
        self.transfer["aws"] = DataTransferPricing(
            provider="aws",
            gb_egress=0.09,
        )

        self.transfer["gcp"] = DataTransferPricing(
            provider="gcp",
            gb_egress=0.12,
        )

        self.transfer["azure"] = DataTransferPricing(
            provider="azure",
            gb_egress=0.087,
        )

    def load_from_file(self, config_file: str) -> None:
        """Load pricing configuration from JSON file.

        Args:
            config_file: Path to cost-config.json file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If file is not valid JSON.
        """
        path = Path(config_file)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(path) as f:
            config = json.load(f)

        # Load instances
        for inst_data in config.get("instances", []):
            inst = InstancePricing(**inst_data)
            self.instances[inst.instance_id] = inst

        # Load databases
        for db_data in config.get("databases", []):
            db = DatabasePricing(**db_data)
            self.databases[db.instance_id] = db

        # Load storage
        for stor_data in config.get("storage", []):
            stor = StoragePricing(**stor_data)
            self.storage[f"{stor.provider}_{stor.service}"] = stor

        # Load transfer
        for trans_data in config.get("transfer", []):
            trans = DataTransferPricing(**trans_data)
            self.transfer[trans.provider] = trans

    def get_instance(self, instance_id: str) -> InstancePricing | None:
        """Get pricing for a specific instance type.

        Args:
            instance_id: Instance identifier (e.g., 'aws_t3_micro').

        Returns:
            InstancePricing object or None if not found.
        """
        return self.instances.get(instance_id)

    def get_database(self, instance_id: str) -> DatabasePricing | None:
        """Get pricing for a specific database instance type.

        Args:
            instance_id: Database instance identifier (e.g., 'aws_t3_small').

        Returns:
            DatabasePricing object or None if not found.
        """
        return self.databases.get(instance_id)

    def get_compute_instances_for_cores(
        self, min_cores: int
    ) -> list[InstancePricing]:
        """Get all compute instances with at least min_cores.

        Args:
            min_cores: Minimum number of CPU cores required.

        Returns:
            List of InstancePricing objects sorted by cost (AWS on-demand).
        """
        matching = [
            inst
            for inst in self.instances.values()
            if inst.cpu_cores >= min_cores
        ]
        return sorted(matching, key=lambda x: x.aws_hourly)

    def get_database_instances_for_cores(
        self, min_cores: int
    ) -> list[DatabasePricing]:
        """Get all database instances with at least min_cores.

        Args:
            min_cores: Minimum number of CPU cores required.

        Returns:
            List of DatabasePricing objects sorted by cost (AWS on-demand).
        """
        matching = [
            db for db in self.databases.values() if db.cpu_cores >= min_cores
        ]
        return sorted(matching, key=lambda x: x.aws_hourly)

    def estimate_annual_cost_with_reserved(
        self,
        monthly_cost: float,
        reserved_term_years: int | None = None,
    ) -> dict[str, float]:
        """Estimate annual cost with optional reserved instance discounts.

        Args:
            monthly_cost: Monthly cost in on-demand pricing.
            reserved_term_years: 1 for 1-year reserved, 3 for 3-year reserved.
                                 None for on-demand only.

        Returns:
            Dict with annual costs: {"on_demand": X, "1yr_reserved": Y, "3yr_reserved": Z}
        """
        result = {"on_demand": monthly_cost * 12}

        if reserved_term_years is None:
            return result

        # 40% discount for 1-year, 55% discount for 3-year
        if reserved_term_years >= 1:
            result["1yr_reserved"] = monthly_cost * 12 * 0.60

        if reserved_term_years >= 3:
            result["3yr_reserved"] = monthly_cost * 12 * 0.45

        return result
