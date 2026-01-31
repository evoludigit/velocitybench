"""Centralized environment configuration with validation.

Provides structured configuration validation at application startup
to catch environment issues early with clear error messages.
"""

import os


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


class DatabaseConfig:
    """Database connection configuration with environment variable support."""

    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.host = self._get_required("DB_HOST", "localhost")
        self.port = self._get_int("DB_PORT", 5432)
        self.name = self._get_required("DB_NAME", "velocitybench_benchmark")
        self.user = self._get_required("DB_USER", "benchmark")
        # Password is REQUIRED - no default (must be explicitly set)
        self.password = self._get_required("DB_PASSWORD")

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


def get_db_config() -> DatabaseConfig:
    """Get or create database configuration.

    Returns:
        DatabaseConfig instance

    Raises:
        ConfigurationError: If environment variables are invalid
    """
    return DatabaseConfig()
