"""Load profiling and production load projection.

Converts benchmark metrics (RPS from JMeter) to production load profiles,
including monthly volume estimation and peak load modeling.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class LoadProfile(Enum):
    """Predefined load profiles for testing different scenarios."""

    SMOKE = "smoke"  # Minimal: 10 RPS
    SMALL = "small"  # Light: 50 RPS
    MEDIUM = "medium"  # Moderate: 500 RPS
    LARGE = "large"  # Heavy: 5000 RPS
    PRODUCTION = "production"  # Full: 10000+ RPS


@dataclass
class LoadProjection:
    """Projected production load based on benchmark metrics."""

    rps_average: float  # Requests per second (steady state)
    rps_peak: float  # Peak RPS (with multiplier)
    requests_per_minute: float
    requests_per_hour: float
    requests_per_day: float
    requests_per_month: float  # 30-day month
    requests_per_year: float
    data_growth_gb_per_month: float  # Estimated data growth
    logs_gb_per_month: float  # Estimated log growth
    peak_variance: float  # Multiplier for peak load (e.g., 2.5x)


class LoadProfiler:
    """Profiles and projects production load from benchmark metrics.

    Converts steady-state RPS from JMeter results to monthly/yearly
    production volume estimates, accounting for peak load variations.
    """

    # Constants for load projection
    SECONDS_PER_MINUTE = 60
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_DAY = 86400
    DAYS_PER_MONTH = 30
    MONTHS_PER_YEAR = 12

    # Default peak load multiplier (2.5x average is typical for web traffic)
    DEFAULT_PEAK_MULTIPLIER = 2.5

    # Data growth estimates (GB per month)
    DATA_GROWTH_MULTIPLIER = 0.0001  # ~0.1 MB per request for typical app
    LOGS_GROWTH_MULTIPLIER = 0.00005  # ~0.05 MB per request for logs

    def __init__(self, peak_multiplier: float = DEFAULT_PEAK_MULTIPLIER):
        """Initialize load profiler.

        Args:
            peak_multiplier: Multiplier for peak load calculation (default 2.5x).
        """
        self.peak_multiplier = peak_multiplier

    def project_from_jmeter(
        self,
        rps: float,
        peak_multiplier: float | None = None,
    ) -> LoadProjection:
        """Project production load from JMeter RPS measurement.

        Args:
            rps: Requests per second from benchmark (steady-state average).
            peak_multiplier: Override default peak multiplier. If None, uses instance default.

        Returns:
            LoadProjection with monthly and yearly estimates.
        """
        if peak_multiplier is None:
            peak_multiplier = self.peak_multiplier

        rps_peak = rps * peak_multiplier
        rpm = rps * self.SECONDS_PER_MINUTE
        rph = rps * self.SECONDS_PER_HOUR
        rpd = rps * self.SECONDS_PER_DAY
        rpm_month = rpd * self.DAYS_PER_MONTH
        rpm_year = rpm_month * self.MONTHS_PER_YEAR

        # Data growth estimates
        data_growth_gb = rpm_month * self.DATA_GROWTH_MULTIPLIER / (1024 ** 3)
        logs_growth_gb = rpm_month * self.LOGS_GROWTH_MULTIPLIER / (1024 ** 3)

        return LoadProjection(
            rps_average=rps,
            rps_peak=rps_peak,
            requests_per_minute=rpm,
            requests_per_hour=rph,
            requests_per_day=rpd,
            requests_per_month=rpm_month,
            requests_per_year=rpm_year,
            data_growth_gb_per_month=data_growth_gb,
            logs_gb_per_month=logs_growth_gb,
            peak_variance=peak_multiplier,
        )

    def profile_from_load_profile(
        self,
        profile: LoadProfile,
    ) -> LoadProjection:
        """Generate load projection from predefined profile.

        Args:
            profile: LoadProfile enum (SMOKE, SMALL, MEDIUM, LARGE, PRODUCTION).

        Returns:
            LoadProjection for the profile.
        """
        profile_rps = {
            LoadProfile.SMOKE: 10.0,
            LoadProfile.SMALL: 50.0,
            LoadProfile.MEDIUM: 500.0,
            LoadProfile.LARGE: 5000.0,
            LoadProfile.PRODUCTION: 10000.0,
        }

        rps = profile_rps[profile]
        return self.project_from_jmeter(rps)

    def estimate_data_storage(
        self,
        load_projection: LoadProjection,
        months: int = 12,
        compression_ratio: float = 0.9,
        replication_factor: float = 2.0,
    ) -> dict[str, float]:
        """Estimate total data storage requirements.

        Args:
            load_projection: LoadProjection object.
            months: Number of months to project (default 12 for 1-year estimate).
            compression_ratio: Data compression ratio (0.9 = 10% reduction).
            replication_factor: Database replication factor (2.0 = 2x storage for redundancy).

        Returns:
            Dict with storage breakdown: {
                "data_gb": application data,
                "logs_gb": log storage,
                "backups_gb": backup storage (1 month retention),
                "total_primary_gb": primary storage after compression,
                "total_replicated_gb": total with replication,
            }
        """
        data_growth = load_projection.data_growth_gb_per_month * months
        logs_growth = load_projection.logs_gb_per_month * months
        backups = load_projection.data_growth_gb_per_month  # 1-month retention

        # Apply compression
        data_compressed = data_growth * compression_ratio
        logs_compressed = logs_growth * compression_ratio
        backups_compressed = backups * compression_ratio

        total_primary = data_compressed + logs_compressed + backups_compressed
        total_replicated = total_primary * replication_factor

        return {
            "data_gb": data_growth,
            "logs_gb": logs_growth,
            "backups_gb": backups,
            "total_primary_gb": total_primary,
            "total_replicated_gb": total_replicated,
        }

    def estimate_monthly_storage(
        self,
        load_projection: LoadProjection,
        compression_ratio: float = 0.9,
    ) -> dict[str, float]:
        """Estimate monthly incremental data storage.

        Args:
            load_projection: LoadProjection object.
            compression_ratio: Data compression ratio.

        Returns:
            Dict with monthly storage: {
                "data_gb": monthly new data,
                "logs_gb": monthly logs,
                "total_gb": total monthly storage after compression,
            }
        """
        data = load_projection.data_growth_gb_per_month
        logs = load_projection.logs_gb_per_month

        return {
            "data_gb": data * compression_ratio,
            "logs_gb": logs * compression_ratio,
            "total_gb": (data + logs) * compression_ratio,
        }

    def get_profile_description(self, profile: LoadProfile) -> dict[str, Any]:
        """Get human-readable description of a load profile.

        Args:
            profile: LoadProfile enum.

        Returns:
            Dict with profile description and characteristics.
        """
        descriptions = {
            LoadProfile.SMOKE: {
                "name": "Smoke Test",
                "rps": 10,
                "use_case": "Sanity testing",
                "typical_deployment": "Development",
            },
            LoadProfile.SMALL: {
                "name": "Small",
                "rps": 50,
                "use_case": "Light load testing",
                "typical_deployment": "Testing/Staging",
            },
            LoadProfile.MEDIUM: {
                "name": "Medium",
                "rps": 500,
                "use_case": "Moderate load testing",
                "typical_deployment": "Staging",
            },
            LoadProfile.LARGE: {
                "name": "Large",
                "rps": 5000,
                "use_case": "Heavy load testing",
                "typical_deployment": "Pre-production",
            },
            LoadProfile.PRODUCTION: {
                "name": "Production",
                "rps": 10000,
                "use_case": "Full capacity planning",
                "typical_deployment": "Production",
            },
        }
        return descriptions.get(
            profile,
            {"name": "Unknown", "rps": 0, "use_case": "Unknown"},
        )
