"""
Shared type definitions for VelocityBench Python frameworks.

Includes:
- Health check types and enums
- Common data structures
- Type aliases
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    """Health check status values."""

    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"
    IN_PROGRESS = "in_progress"


class ProbeType(str, Enum):
    """Health check probe types (Kubernetes-compatible)."""

    LIVENESS = "liveness"
    READINESS = "readiness"
    STARTUP = "startup"


@dataclass
class HealthCheck:
    """Individual health check result."""

    status: HealthStatus
    response_time_ms: float | None = None
    error: str | None = None
    warning: str | None = None
    info: str | None = None
    additional_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {
            "status": self.status.value,
        }

        if self.response_time_ms is not None:
            result["response_time_ms"] = round(self.response_time_ms, 2)

        if self.error:
            result["error"] = self.error

        if self.warning:
            result["warning"] = self.warning

        if self.info:
            result["info"] = self.info

        # Add any additional data
        result.update(self.additional_data)

        return result


@dataclass
class HealthCheckResponse:
    """Complete health check response."""

    status: HealthStatus
    timestamp: str  # ISO 8601 format
    uptime_ms: int
    version: str
    service: str
    environment: str
    probe_type: ProbeType
    checks: dict[str, HealthCheck]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "uptime_ms": self.uptime_ms,
            "version": self.version,
            "service": self.service,
            "environment": self.environment,
            "probe_type": self.probe_type.value,
            "checks": {
                name: check.to_dict()
                for name, check in self.checks.items()
            }
        }

    def get_http_status_code(self) -> int:
        """
        Get HTTP status code based on health status.

        Returns:
            200: up or degraded
            202: in_progress (startup probe only)
            503: down
        """
        if self.status == HealthStatus.DOWN:
            return 503
        elif self.status == HealthStatus.IN_PROGRESS and self.probe_type == ProbeType.STARTUP:
            return 202
        else:
            return 200


# Type aliases for common use cases
ChecksDict = dict[str, HealthCheck]
