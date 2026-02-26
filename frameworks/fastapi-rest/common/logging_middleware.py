"""Request logging middleware for FastAPI and Flask.

Provides structured request logging with unique request IDs for tracing,
request duration tracking, and slow query/request detection.
"""

import logging
import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class RequestLogger:
    """Request logging utilities."""

    @staticmethod
    def generate_request_id() -> str:
        """Generate unique request ID for request tracing.

        Returns:
            UUID string for request identification
        """
        return str(uuid4())

    @staticmethod
    def log_request(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str,
        query_params: dict[str, Any] | None = None,
    ) -> None:
        """Log request with standardized format.

        Logs at different levels based on status code and duration:
        - 5xx errors: ERROR level
        - 4xx errors: WARNING level
        - Slow requests (>1s): WARNING level
        - Normal responses: INFO level

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            request_id: Unique request ID for tracing
            query_params: Optional query parameters dictionary
        """
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
        }

        if query_params:
            log_data["query_params"] = query_params

        # Use different log levels based on status code and duration
        if status_code >= 500:
            logger.error("Request failed", extra=log_data)
        elif status_code >= 400:
            logger.warning("Client error", extra=log_data)
        elif duration_ms > 1000:  # Slow request (>1s)
            logger.warning("Slow request", extra=log_data)
        else:
            logger.info("Request completed", extra=log_data)


class FastAPILoggingMiddleware:
    """ASGI middleware for FastAPI request logging.

    Logs all HTTP requests with method, path, status, duration, and request ID.
    Adds X-Request-ID header to responses for request tracing.
    """

    def __init__(self, app: Callable) -> None:
        """Initialize middleware.

        Args:
            app: ASGI application
        """
        self.app = app

    async def __call__(
        self, scope: dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """Log all HTTP requests.

        Args:
            scope: ASGI connection scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info
        method = scope.get("method", "")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode("utf-8")

        # Get or generate request ID
        request_id = None
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                request_id = value.decode("utf-8")
                break

        if not request_id:
            request_id = RequestLogger.generate_request_id()

        # Store request ID in scope for use by application
        scope["request_id"] = request_id

        # Track request timing
        start_time = time.time()
        status_code = 500  # Default to 500 if response never sent

        # Wrap send to capture status code and add request ID header
        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # Add request ID to response headers
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Log request after completion
            duration_ms = (time.time() - start_time) * 1000
            query_params = (
                {
                    param.split("=")[0]: param.split("=")[1]
                    for param in query_string.split("&")
                    if "=" in param
                }
                if query_string
                else None
            )

            RequestLogger.log_request(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                query_params=query_params,
            )


class FlaskLoggingMiddleware:
    """Flask middleware for request logging.

    Logs all HTTP requests with method, path, status, duration, and request ID.
    Adds X-Request-ID header to responses for request tracing.
    """

    def __init__(self, app: Any) -> None:
        """Initialize middleware.

        Args:
            app: Flask application instance
        """
        self.app = app

        @app.before_request
        def before_request() -> None:
            """Capture request start time and ID."""
            from flask import g, request

            g.start_time = time.time()
            g.request_id = request.headers.get(
                "X-Request-ID", RequestLogger.generate_request_id()
            )

        @app.after_request
        def after_request(response: Any) -> Any:
            """Log request after completion."""
            from flask import g, request

            duration_ms = (time.time() - g.start_time) * 1000

            # Add request ID to response headers
            response.headers["X-Request-ID"] = g.request_id

            RequestLogger.log_request(
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=g.request_id,
                query_params=dict(request.args) if request.args else None,
            )

            return response
