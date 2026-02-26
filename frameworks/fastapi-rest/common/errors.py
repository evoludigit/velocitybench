"""Application error hierarchy with HTTP status code mapping.

Provides specific exception types for different error scenarios with
appropriate HTTP status codes and structured error response formatting.
"""

from typing import Any


class AppError(Exception):
    """Base application error with HTTP status code.

    All application errors should inherit from this class to ensure
    consistent error handling and response formatting.
    """

    status_code = 500
    error_code = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize application error.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to error response dictionary.

        Returns:
            Dictionary with error code, message, status, and optional details
        """
        result = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status": self.status_code,
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        return result


class DatabaseError(AppError):
    """Database connection or query error (transient).

    Indicates a temporary database connectivity or query issue.
    Client should retry the operation.
    """

    status_code = 503  # Service Unavailable
    error_code = "DATABASE_ERROR"


class DatabaseTimeoutError(DatabaseError):
    """Database query timeout (transient).

    Indicates that a database query exceeded the configured timeout.
    Client should retry the operation with exponential backoff.
    """

    status_code = 408  # Request Timeout
    error_code = "DATABASE_TIMEOUT"


class ResourceNotFoundError(AppError):
    """Requested resource not found (permanent).

    Indicates that the requested resource does not exist.
    Retrying the same request will not succeed.
    """

    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"


class InputValidationError(AppError):
    """Input validation failed (permanent).

    Indicates that the client provided invalid input.
    Client must fix the input and retry.
    """

    status_code = 400
    error_code = "VALIDATION_ERROR"


class ConfigurationError(AppError):
    """Application configuration error (permanent).

    Indicates that the application is misconfigured.
    System administrator must fix the configuration.
    """

    status_code = 500
    error_code = "CONFIGURATION_ERROR"


def wrap_database_error(
    e: Exception,
) -> DatabaseError | DatabaseTimeoutError:
    """Wrap database exception in appropriate error type.

    Converts database-specific exceptions into standardized error types
    for consistent error handling and response formatting.

    Args:
        e: Original database exception

    Returns:
        Appropriate DatabaseError or DatabaseTimeoutError subclass
    """
    import asyncio

    if isinstance(e, asyncio.TimeoutError):
        return DatabaseTimeoutError(f"Database query timeout: {e!s}")
    else:
        return DatabaseError(f"Database error: {e!s}")
