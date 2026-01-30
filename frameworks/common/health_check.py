"""
Health check manager for VelocityBench Python frameworks.

Provides unified health check functionality with support for:
- Kubernetes liveness, readiness, and startup probes
- Database connectivity checks
- Memory monitoring
- Connection pool statistics
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timezone

from .async_db import AsyncDatabase
from .types import (
    HealthStatus,
    ProbeType,
    HealthCheck,
    HealthCheckResponse,
    ChecksDict,
)

logger = logging.getLogger(__name__)


class HealthCheckManager:
    """
    Manage health checks for a VelocityBench framework.

    Features:
    - Liveness probe (process alive?)
    - Readiness probe (can serve traffic?)
    - Startup probe (initialization complete?)
    - Database health checks
    - Memory monitoring
    - Connection pool statistics
    """

    def __init__(
        self,
        service_name: str,
        version: str,
        database: AsyncDatabase | None = None,
        environment: str = "development",
        startup_duration_ms: int = 30000,  # 30 seconds warmup
    ):
        """
        Initialize health check manager.

        Args:
            service_name: Name of the service (e.g., "fastapi-rest")
            version: Service version (semantic versioning)
            database: AsyncDatabase instance for database checks
            environment: Environment name (development, staging, production)
            startup_duration_ms: Warmup period in milliseconds
        """
        self.service_name = service_name
        self.version = version
        self.database = database
        self.environment = environment
        self.startup_duration_ms = startup_duration_ms
        self.start_time = time.time()
        self.process = psutil.Process()

        # Cache for health check results (avoid hammering DB)
        self._cache: dict[str, tuple[HealthCheckResponse, float]] = {}
        self._cache_ttl = 5.0  # 5 seconds

    async def probe(self, probe_type: str) -> HealthCheckResponse:
        """
        Execute a health check probe.

        Args:
            probe_type: "liveness", "readiness", or "startup"

        Returns:
            HealthCheckResponse with status and check results
        """
        probe_enum = ProbeType(probe_type.lower())

        # Check cache
        cached = self._get_cached_result(probe_enum)
        if cached:
            return cached

        # Execute probe
        if probe_enum == ProbeType.LIVENESS:
            result = await self._liveness_probe()
        elif probe_enum == ProbeType.READINESS:
            result = await self._readiness_probe()
        elif probe_enum == ProbeType.STARTUP:
            result = await self._startup_probe()
        else:
            raise ValueError(f"Invalid probe type: {probe_type}")

        # Cache result
        self._cache[probe_enum.value] = (result, time.time())

        return result

    def _get_cached_result(self, probe_type: ProbeType) -> HealthCheckResponse | None:
        """Get cached health check result if still valid."""
        if probe_type.value in self._cache:
            result, cached_at = self._cache[probe_type.value]
            if time.time() - cached_at < self._cache_ttl:
                return result
        return None

    async def _liveness_probe(self) -> HealthCheckResponse:
        """
        Liveness probe: Is the process alive?

        Checks:
        - Process is running
        - Event loop is responsive

        Does NOT check database or external dependencies.
        """
        checks: ChecksDict = {}

        # Memory check (lightweight, no DB required)
        memory_check = self._check_memory()
        checks["memory"] = memory_check

        # Determine overall status
        overall_status = HealthStatus.UP

        return HealthCheckResponse(
            status=overall_status,
            timestamp=self._get_timestamp(),
            uptime_ms=self._get_uptime_ms(),
            version=self.version,
            service=self.service_name,
            environment=self.environment,
            probe_type=ProbeType.LIVENESS,
            checks=checks,
        )

    async def _readiness_probe(self) -> HealthCheckResponse:
        """
        Readiness probe: Can the service handle traffic?

        Checks:
        - Process is running
        - Database connection is healthy
        - Connection pool has capacity
        - Memory usage is acceptable
        """
        checks: ChecksDict = {}

        # Database check
        if self.database:
            db_check = await self._check_database()
            checks["database"] = db_check

        # Memory check
        memory_check = self._check_memory()
        checks["memory"] = memory_check

        # Determine overall status
        overall_status = self._compute_overall_status(checks)

        return HealthCheckResponse(
            status=overall_status,
            timestamp=self._get_timestamp(),
            uptime_ms=self._get_uptime_ms(),
            version=self.version,
            service=self.service_name,
            environment=self.environment,
            probe_type=ProbeType.READINESS,
            checks=checks,
        )

    async def _startup_probe(self) -> HealthCheckResponse:
        """
        Startup probe: Has initialization completed?

        Checks:
        - Process is running
        - Database connection established
        - Warmup period finished
        """
        checks: ChecksDict = {}

        # Database check
        if self.database:
            db_check = await self._check_database()
            checks["database"] = db_check

        # Warmup check
        warmup_check = self._check_warmup()
        checks["warmup"] = warmup_check

        # Memory check
        memory_check = self._check_memory()
        checks["memory"] = memory_check

        # Determine overall status
        overall_status = self._compute_overall_status(checks)

        return HealthCheckResponse(
            status=overall_status,
            timestamp=self._get_timestamp(),
            uptime_ms=self._get_uptime_ms(),
            version=self.version,
            service=self.service_name,
            environment=self.environment,
            probe_type=ProbeType.STARTUP,
            checks=checks,
        )

    async def _check_database(self) -> HealthCheck:
        """Check database connectivity and pool health."""
        if not self.database or not self.database.pool:
            return HealthCheck(
                status=HealthStatus.DOWN,
                error="Database pool not initialized",
            )

        start = time.time()

        try:
            # Execute simple query to verify connectivity
            await asyncio.wait_for(
                self.database.fetch("SELECT 1 as health_check"),
                timeout=3.0  # 3 second timeout
            )

            response_time = (time.time() - start) * 1000  # Convert to ms

            # Get pool statistics
            pool = self.database.pool
            pool_size = pool.get_size()
            pool_max_size = pool.get_max_size()
            pool_min_size = pool.get_min_size()

            # Calculate available connections (approximate)
            # asyncpg doesn't expose idle count directly, so we estimate
            available = pool_max_size - pool_size if pool_size < pool_max_size else 0

            # Determine status based on pool utilization
            utilization = (pool_size / pool_max_size) * 100

            if utilization > 95:
                status = HealthStatus.DEGRADED
                warning = f"Connection pool nearly exhausted ({pool_size}/{pool_max_size})"
            elif utilization > 80:
                status = HealthStatus.UP
                warning = f"High connection pool utilization ({utilization:.1f}%)"
            else:
                status = HealthStatus.UP
                warning = None

            return HealthCheck(
                status=status,
                response_time_ms=response_time,
                warning=warning,
                additional_data={
                    "pool_size": pool_size,
                    "pool_max_size": pool_max_size,
                    "pool_min_size": pool_min_size,
                    "estimated_available": available,
                },
            )

        except asyncio.TimeoutError:
            return HealthCheck(
                status=HealthStatus.DOWN,
                error="Database query timeout (>3s)",
            )
        except Exception as e:
            logger.exception("Database health check failed")
            return HealthCheck(
                status=HealthStatus.DOWN,
                error=f"Database connection error: {str(e)}",
            )

    def _check_memory(self) -> HealthCheck:
        """Check memory usage."""
        try:
            memory_info = self.process.memory_info()
            rss_mb = memory_info.rss / 1024 / 1024  # Convert to MB

            # Get system memory (if available)
            try:
                virtual_mem = psutil.virtual_memory()
                total_mb = virtual_mem.total / 1024 / 1024
                utilization = (rss_mb / total_mb) * 100
            except Exception:
                total_mb = None
                utilization = None

            # Determine status based on memory usage
            if utilization and utilization > 95:
                status = HealthStatus.DEGRADED
                warning = f"Critical memory usage ({utilization:.1f}%)"
            elif utilization and utilization > 80:
                status = HealthStatus.UP
                warning = f"High memory usage ({utilization:.1f}%)"
            else:
                status = HealthStatus.UP
                warning = None

            additional_data = {
                "used_mb": round(rss_mb, 2),
            }

            if total_mb:
                additional_data["total_mb"] = round(total_mb, 2)
                additional_data["utilization_percent"] = round(utilization, 2)

            return HealthCheck(
                status=status,
                warning=warning,
                additional_data=additional_data,
            )

        except Exception as e:
            logger.exception("Memory check failed")
            return HealthCheck(
                status=HealthStatus.DEGRADED,
                warning=f"Memory check error: {str(e)}",
            )

    def _check_warmup(self) -> HealthCheck:
        """Check if warmup period has completed."""
        uptime_ms = self._get_uptime_ms()

        if uptime_ms < self.startup_duration_ms:
            progress = (uptime_ms / self.startup_duration_ms) * 100
            return HealthCheck(
                status=HealthStatus.IN_PROGRESS,
                info=f"Warming up ({progress:.0f}% complete)",
                additional_data={
                    "progress_percent": round(progress, 1),
                    "uptime_ms": uptime_ms,
                    "target_ms": self.startup_duration_ms,
                },
            )
        else:
            return HealthCheck(
                status=HealthStatus.UP,
                info="Warmup complete",
            )

    def _compute_overall_status(self, checks: ChecksDict) -> HealthStatus:
        """
        Compute overall health status from individual checks.

        Logic:
        - If any check is DOWN, overall is DOWN
        - If any check is IN_PROGRESS, overall is IN_PROGRESS
        - If any check is DEGRADED, overall is DEGRADED
        - Otherwise, overall is UP
        """
        statuses = [check.status for check in checks.values()]

        if HealthStatus.DOWN in statuses:
            return HealthStatus.DOWN
        elif HealthStatus.IN_PROGRESS in statuses:
            return HealthStatus.IN_PROGRESS
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UP

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format (UTC)."""
        return datetime.now(timezone.utc).isoformat()

    def _get_uptime_ms(self) -> int:
        """Get service uptime in milliseconds."""
        return int((time.time() - self.start_time) * 1000)
