"""Infrastructure resource requirement calculations.

Calculates CPU, memory, and storage requirements based on load
projections and framework characteristics.
"""

from dataclasses import dataclass
from typing import Any
from .load_profiler import LoadProjection


@dataclass
class ResourceRequirements:
    """Infrastructure requirements for a given load."""

    cpu_cores: int  # Number of CPU cores
    memory_gb: float  # RAM in GB
    storage_gb: float  # Storage in GB
    network_bandwidth_mbps: float  # Network bandwidth in Mbps

    # Recommended instance type (will be set by cost calculator)
    recommended_instance_aws: str | None = None
    recommended_instance_gcp: str | None = None
    recommended_instance_azure: str | None = None

    # Headroom percentages
    cpu_headroom_percent: float = 30.0
    memory_headroom_percent: float = 20.0


class ResourceCalculator:
    """Calculates infrastructure resource requirements.

    Based on load projections and framework characteristics, determines
    the CPU, memory, and storage needed to run the framework at scale.
    """

    # Default framework characteristics
    DEFAULT_RPS_PER_CORE = 100  # Typical web framework throughput
    DEFAULT_APP_MEMORY_MB = 256  # Base application memory
    DEFAULT_CONN_POOL_SIZE = 50
    DEFAULT_MEMORY_PER_CONN_MB = 5
    DEFAULT_APP_STORAGE_GB = 1  # Code and static assets

    # Network throughput (rough estimate)
    MB_PER_REQUEST = 0.01  # Average response size in MB
    SECONDS_PER_HOUR = 3600

    def __init__(
        self,
        rps_per_core: float = DEFAULT_RPS_PER_CORE,
        app_memory_mb: float = DEFAULT_APP_MEMORY_MB,
        conn_pool_size: int = DEFAULT_CONN_POOL_SIZE,
        memory_per_conn_mb: float = DEFAULT_MEMORY_PER_CONN_MB,
        app_storage_gb: float = DEFAULT_APP_STORAGE_GB,
    ):
        """Initialize resource calculator.

        Args:
            rps_per_core: Requests per second per CPU core.
            app_memory_mb: Base application memory usage.
            conn_pool_size: Database connection pool size.
            memory_per_conn_mb: Memory per database connection.
            app_storage_gb: Storage for application code and static assets.
        """
        self.rps_per_core = rps_per_core
        self.app_memory_mb = app_memory_mb
        self.conn_pool_size = conn_pool_size
        self.memory_per_conn_mb = memory_per_conn_mb
        self.app_storage_gb = app_storage_gb

    def calculate_cpu_cores(
        self,
        load_projection: LoadProjection,
        headroom_percent: float = 30.0,
    ) -> int:
        """Calculate CPU cores needed.

        Uses peak RPS and adds headroom for spikes and background work.

        Args:
            load_projection: LoadProjection object with RPS data.
            headroom_percent: Headroom percentage (default 30%).

        Returns:
            Number of CPU cores needed (minimum 1).
        """
        import math

        cores_needed = load_projection.rps_peak / self.rps_per_core
        cores_with_headroom = cores_needed * (1.0 + headroom_percent / 100.0)
        return max(1, math.ceil(cores_with_headroom))

    def calculate_memory_gb(
        self,
        headroom_percent: float = 20.0,
    ) -> float:
        """Calculate memory (RAM) needed.

        Includes application baseline, connection pool, and buffer.

        Args:
            headroom_percent: Headroom percentage (default 20%).

        Returns:
            Memory in GB.
        """
        app_mem = self.app_memory_mb
        pool_mem = self.conn_pool_size * self.memory_per_conn_mb
        total_mb = app_mem + pool_mem

        with_headroom = total_mb * (1.0 + headroom_percent / 100.0)
        memory_gb = with_headroom / 1024

        return memory_gb

    def calculate_storage_gb(
        self,
        load_projection: LoadProjection,
        months: int = 12,
        compression_ratio: float = 0.9,
        replication_factor: float = 2.0,
    ) -> float:
        """Calculate storage needed.

        Includes application code, data, logs, and backups.

        Args:
            load_projection: LoadProjection object with data growth.
            months: Number of months to project.
            compression_ratio: Data compression ratio.
            replication_factor: Database replication factor.

        Returns:
            Total storage in GB (after compression and replication).
        """
        # Application code and static assets
        app_storage = self.app_storage_gb

        # Data growth (12 months)
        data_monthly = load_projection.data_growth_gb_per_month
        data_growth = data_monthly * months * compression_ratio

        # Logs (keep 1 month)
        logs = load_projection.logs_gb_per_month * compression_ratio

        # Backups (keep 1 month of daily backups = 4 backups)
        backups = (data_monthly * compression_ratio) * 4

        # Total primary storage
        total_primary = app_storage + data_growth + logs + backups

        # Total with replication
        total_replicated = total_primary * replication_factor

        return total_replicated

    def calculate_network_bandwidth(
        self,
        load_projection: LoadProjection,
    ) -> float:
        """Calculate network bandwidth needs.

        Estimates peak bandwidth based on response size and peak RPS.

        Args:
            load_projection: LoadProjection object.

        Returns:
            Bandwidth in Mbps.
        """
        # Peak bandwidth: peak_rps × bytes_per_request / 125,000 (bytes to Mbps)
        peak_throughput_mbps = (
            load_projection.rps_peak * self.MB_PER_REQUEST * 8
        )  # *8 to convert MB to Mb

        return peak_throughput_mbps

    def calculate_requirements(
        self,
        load_projection: LoadProjection,
        cpu_headroom_percent: float = 30.0,
        memory_headroom_percent: float = 20.0,
        months: int = 12,
    ) -> ResourceRequirements:
        """Calculate all resource requirements.

        Args:
            load_projection: LoadProjection object.
            cpu_headroom_percent: CPU headroom percentage.
            memory_headroom_percent: Memory headroom percentage.
            months: Projection period in months.

        Returns:
            ResourceRequirements object.
        """
        cpu_cores = self.calculate_cpu_cores(
            load_projection,
            cpu_headroom_percent,
        )
        memory_gb = self.calculate_memory_gb(memory_headroom_percent)
        storage_gb = self.calculate_storage_gb(load_projection, months)
        bandwidth_mbps = self.calculate_network_bandwidth(load_projection)

        return ResourceRequirements(
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            storage_gb=storage_gb,
            network_bandwidth_mbps=bandwidth_mbps,
            cpu_headroom_percent=cpu_headroom_percent,
            memory_headroom_percent=memory_headroom_percent,
        )

    def get_resource_profile_description(
        self,
        requirements: ResourceRequirements,
    ) -> dict[str, Any]:
        """Get human-readable description of resource requirements.

        Args:
            requirements: ResourceRequirements object.

        Returns:
            Dict with descriptions and recommendations.
        """
        return {
            "cpu": {
                "cores": requirements.cpu_cores,
                "description": f"{requirements.cpu_cores} cores "
                               f"(with {requirements.cpu_headroom_percent:.0f}% headroom)",
                "suitable_for": "light" if requirements.cpu_cores < 2
                               else "moderate" if requirements.cpu_cores < 4
                               else "heavy" if requirements.cpu_cores < 8
                               else "very heavy",
            },
            "memory": {
                "gb": round(requirements.memory_gb, 1),
                "description": f"{requirements.memory_gb:.1f} GB RAM "
                               f"(with {requirements.memory_headroom_percent:.0f}% headroom)",
                "suitable_for": "lightweight" if requirements.memory_gb < 4
                               else "small" if requirements.memory_gb < 8
                               else "medium" if requirements.memory_gb < 16
                               else "large",
            },
            "storage": {
                "gb": round(requirements.storage_gb, 1),
                "description": f"{requirements.storage_gb:.1f} GB "
                               f"(application + data + logs + backups + replication)",
            },
            "network": {
                "mbps": round(requirements.network_bandwidth_mbps, 1),
                "description": f"{requirements.network_bandwidth_mbps:.1f} Mbps "
                               f"peak bandwidth",
            },
        }
