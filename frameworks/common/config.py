"""Centralized environment configuration with validation.

Provides structured configuration validation at application startup
to catch environment issues early with clear error messages.
"""

import os
from dataclasses import dataclass, field


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


@dataclass
class PoolConfig:
    """Database connection pool configuration."""

    min_size: int = 10
    max_size: int = 50
    statement_cache_size: int = 100
    command_timeout: int = 30

    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.min_size = self._get_int("DB_POOL_MIN_SIZE", self.min_size)
        self.max_size = self._get_int("DB_POOL_MAX_SIZE", self.max_size)
        self.statement_cache_size = self._get_int(
            "DB_POOL_STATEMENT_CACHE_SIZE", self.statement_cache_size
        )
        self.command_timeout = self._get_int("DB_COMMAND_TIMEOUT", self.command_timeout)

        # Validate pool size constraints
        if self.min_size < 1:
            raise ConfigurationError("Pool min_size must be >= 1")
        if self.max_size < self.min_size:
            raise ConfigurationError("Pool max_size must be >= min_size")

    @staticmethod
    def _get_int(key: str, default: int) -> int:
        """Get integer environment variable with validation.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Integer environment variable value or default

        Raises:
            ConfigurationError: If value is not a valid integer
        """
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError as e:
            raise ConfigurationError(
                f"Environment variable {key}={value} is not a valid integer"
            ) from e


class DatabaseConfig:
    """Database connection configuration with environment variable support."""

    def __init__(self) -> None:
        """Initialize database configuration from environment variables."""
        self.host = self._get_required("DB_HOST", "localhost")
        self.port = self._get_int("DB_PORT", 5432)
        self.name = self._get_required("DB_NAME", "velocitybench_benchmark")
        self.user = self._get_required("DB_USER", "benchmark")
        # Password is REQUIRED - no default (must be explicitly set)
        self.password = self._get_required("DB_PASSWORD")
        self.pool = PoolConfig()

    def _get_required(self, key: str, default: str | None = None) -> str:
        """Get required environment variable with optional default.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Environment variable value or default

        Raises:
            ConfigurationError: If required variable is missing
        """
        value = os.getenv(key, default)
        if value is None or value == "":
            raise ConfigurationError(f"Required environment variable {key} is not set")
        return value

    def _get_int(self, key: str, default: int) -> int:
        """Get integer environment variable with validation.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Integer environment variable value or default

        Raises:
            ConfigurationError: If value is not a valid integer
        """
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError as e:
            raise ConfigurationError(
                f"Environment variable {key}={value} is not a valid integer"
            ) from e


@dataclass
class AppConfig:
    """Complete application configuration."""

    service_name: str
    version: str = "1.0.0"
    port: int = 8000
    environment: str = "development"
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    def __post_init__(self) -> None:
        """Load application configuration from environment."""
        self.version = os.getenv("VERSION", self.version)
        self.port = int(os.getenv("PORT", str(self.port)))
        self.environment = os.getenv("ENVIRONMENT", self.environment)


def get_db_config() -> DatabaseConfig:
    """Get or create database configuration.

    Returns:
        DatabaseConfig instance

    Raises:
        ConfigurationError: If environment variables are invalid
    """
    return DatabaseConfig()


def get_app_config(service_name: str, default_port: int = 8000) -> AppConfig:
    """Get application configuration.

    Args:
        service_name: Name of the service (e.g., "fastapi-rest")
        default_port: Default port if PORT env var not set

    Returns:
        AppConfig instance

    Raises:
        ConfigurationError: If environment variables are invalid
    """
    return AppConfig(service_name=service_name, port=default_port)
