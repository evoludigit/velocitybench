"""
ASGI middleware for automatic health check endpoint handling.

Intercepts requests to /health* endpoints and routes them to the
HealthCheckManager without requiring framework-specific endpoint definitions.
"""

import asyncio
import json
import logging
from typing import Callable, Awaitable

from ..health_check import HealthCheckManager
from ..types import ProbeType

logger = logging.getLogger(__name__)


class HealthCheckMiddleware:
    """
    ASGI middleware for health check endpoints.

    Automatically handles:
    - GET /health (defaults to readiness probe)
    - GET /health/live (liveness probe)
    - GET /health/ready (readiness probe)
    - GET /health/startup (startup probe)

    Usage:
        from frameworks.common.middleware import HealthCheckMiddleware
        from frameworks.common.health_check import HealthCheckManager

        health_manager = HealthCheckManager(
            service_name="fastapi-rest",
            version="1.0.0",
            database=db
        )

        app.add_middleware(HealthCheckMiddleware, health_manager=health_manager)
    """

    def __init__(
        self,
        app: Callable,
        health_manager: HealthCheckManager,
    ):
        """
        Initialize health check middleware.

        Args:
            app: ASGI application
            health_manager: HealthCheckManager instance
        """
        self.app = app
        self.health_manager = health_manager

    async def __call__(self, scope, receive, send):
        """ASGI application interface."""
        if scope["type"] != "http":
            # Not an HTTP request, pass through
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "GET")

        # Check if this is a health check endpoint
        if method == "GET" and path.startswith("/health"):
            await self._handle_health_check(scope, receive, send, path)
        else:
            # Not a health check, pass to application
            await self.app(scope, receive, send)

    async def _handle_health_check(self, scope, receive, send, path: str):
        """Handle health check request."""
        # Determine probe type from path
        if path == "/health":
            probe_type = ProbeType.READINESS  # Default to readiness
        elif path == "/health/live":
            probe_type = ProbeType.LIVENESS
        elif path == "/health/ready":
            probe_type = ProbeType.READINESS
        elif path == "/health/startup":
            probe_type = ProbeType.STARTUP
        else:
            # Unknown health endpoint, return 404
            await self._send_response(
                send,
                status=404,
                body={"error": "Unknown health endpoint"},
            )
            return

        try:
            # Execute health check
            result = await self.health_manager.probe(probe_type.value)

            # Send response
            await self._send_response(
                send,
                status=result.get_http_status_code(),
                body=result.to_dict(),
            )

        except (OSError, asyncio.TimeoutError) as e:
            logger.exception(f"Health check failed: {e}")
            await self._send_response(
                send,
                status=503,
                body={
                    "status": "down",
                    "error": f"Health check error: {str(e)}",
                },
            )

    async def _send_response(self, send, status: int, body: dict):
        """Send JSON response."""
        body_bytes = json.dumps(body, indent=2).encode("utf-8")

        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body_bytes)).encode()],
            ],
        })

        await send({
            "type": "http.response.body",
            "body": body_bytes,
        })
