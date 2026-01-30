"""
Integration tests for health check endpoints across all frameworks.

Tests validate:
- Health endpoints respond with correct status codes
- Response schema compliance
- Database connectivity checks
- Memory monitoring
- Probe type differentiation
"""

import asyncio
import json
from typing import Any, Dict, List

import httpx
import pytest

# Framework endpoints to test
FRAMEWORKS = [
    # Python frameworks
    {"name": "fastapi-rest", "port": 8001, "language": "python"},
    {"name": "flask-rest", "port": 8002, "language": "python"},
    {"name": "strawberry-graphql", "port": 8003, "language": "python"},
    {"name": "graphene-graphql", "port": 8004, "language": "python"},
    {"name": "fraiseql", "port": 8005, "language": "python"},
    # Add more frameworks as they are migrated to health checks
]

HEALTH_ENDPOINTS = [
    "/health",
    "/health/live",
    "/health/ready",
    "/health/startup",
]

REQUIRED_FIELDS = [
    "status",
    "timestamp",
    "uptime_ms",
    "version",
    "service",
    "environment",
    "probe_type",
    "checks",
]

VALID_STATUSES = ["up", "degraded", "down", "in_progress"]
VALID_PROBE_TYPES = ["liveness", "readiness", "startup"]


class TestHealthCheckSchema:
    """Test health check response schema compliance."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    async def test_health_endpoint_exists(self, framework: Dict[str, Any]):
        """Test that health endpoint exists and responds."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}/health"
            try:
                response = await client.get(url, timeout=5.0)
                assert response.status_code in [
                    200,
                    202,
                    503,
                ], f"{framework['name']}: Health endpoint returned {response.status_code}"
            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    @pytest.mark.parametrize("endpoint", HEALTH_ENDPOINTS)
    async def test_health_response_schema(
        self, framework: Dict[str, Any], endpoint: str
    ):
        """Test that health check response follows schema."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}{endpoint}"
            try:
                response = await client.get(url, timeout=5.0)
            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")

            # Should return JSON
            assert (
                "application/json" in response.headers.get("content-type", "")
            ), f"{framework['name']}: Not JSON response"

            data = response.json()

            # Check required fields
            for field in REQUIRED_FIELDS:
                assert (
                    field in data
                ), f"{framework['name']}: Missing field '{field}' in {endpoint}"

            # Validate field types
            assert isinstance(
                data["status"], str
            ), f"{framework['name']}: status must be string"
            assert isinstance(
                data["timestamp"], str
            ), f"{framework['name']}: timestamp must be string"
            assert isinstance(
                data["uptime_ms"], int
            ), f"{framework['name']}: uptime_ms must be int"
            assert isinstance(
                data["version"], str
            ), f"{framework['name']}: version must be string"
            assert isinstance(
                data["service"], str
            ), f"{framework['name']}: service must be string"
            assert isinstance(
                data["environment"], str
            ), f"{framework['name']}: environment must be string"
            assert isinstance(
                data["probe_type"], str
            ), f"{framework['name']}: probe_type must be string"
            assert isinstance(
                data["checks"], dict
            ), f"{framework['name']}: checks must be dict"

            # Validate enum values
            assert (
                data["status"] in VALID_STATUSES
            ), f"{framework['name']}: Invalid status '{data['status']}'"
            assert (
                data["probe_type"] in VALID_PROBE_TYPES
            ), f"{framework['name']}: Invalid probe_type '{data['probe_type']}'"


class TestHealthCheckBehavior:
    """Test health check behavior and logic."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    async def test_liveness_probe(self, framework: Dict[str, Any]):
        """Test liveness probe behavior."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}/health/live"
            try:
                response = await client.get(url, timeout=5.0)
            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")

            data = response.json()

            # Liveness should have probe_type = liveness
            assert (
                data["probe_type"] == "liveness"
            ), f"{framework['name']}: Liveness probe has wrong probe_type"

            # Liveness should include memory check
            assert (
                "memory" in data["checks"]
            ), f"{framework['name']}: Liveness missing memory check"

            # Liveness should NOT include database check (lightweight)
            # (This is a best practice, not a strict requirement)
            if "database" in data["checks"]:
                print(
                    f"Warning: {framework['name']} includes database in liveness probe (not recommended)"
                )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    async def test_readiness_probe(self, framework: Dict[str, Any]):
        """Test readiness probe behavior."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}/health/ready"
            try:
                response = await client.get(url, timeout=5.0)
            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")

            data = response.json()

            # Readiness should have probe_type = readiness
            assert (
                data["probe_type"] == "readiness"
            ), f"{framework['name']}: Readiness probe has wrong probe_type"

            # Readiness should include database check
            assert (
                "database" in data["checks"]
            ), f"{framework['name']}: Readiness missing database check"

            # Readiness should include memory check
            assert (
                "memory" in data["checks"]
            ), f"{framework['name']}: Readiness missing memory check"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    async def test_startup_probe(self, framework: Dict[str, Any]):
        """Test startup probe behavior."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}/health/startup"
            try:
                response = await client.get(url, timeout=5.0)
            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")

            data = response.json()

            # Startup should have probe_type = startup
            assert (
                data["probe_type"] == "startup"
            ), f"{framework['name']}: Startup probe has wrong probe_type"

            # Startup should include warmup check
            assert (
                "warmup" in data["checks"]
            ), f"{framework['name']}: Startup missing warmup check"

            # Warmup check should have progress info
            warmup = data["checks"]["warmup"]
            if warmup["status"] == "in_progress":
                assert (
                    "progress_percent" in warmup.get("additional_data", warmup)
                ), f"{framework['name']}: Warmup missing progress_percent"


class TestHealthCheckHTTPCodes:
    """Test HTTP status code behavior."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    async def test_http_status_codes(self, framework: Dict[str, Any]):
        """Test that HTTP status codes match health status."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}/health/ready"
            try:
                response = await client.get(url, timeout=5.0)
            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")

            data = response.json()
            status = data["status"]

            # Map status to expected HTTP code
            if status == "up" or status == "degraded":
                assert (
                    response.status_code == 200
                ), f"{framework['name']}: Status '{status}' should return 200"
            elif status == "down":
                assert (
                    response.status_code == 503
                ), f"{framework['name']}: Status 'down' should return 503"
            elif status == "in_progress":
                # In progress is 202 for startup probe, 200 for others
                probe_type = data["probe_type"]
                if probe_type == "startup":
                    assert (
                        response.status_code == 202
                    ), f"{framework['name']}: Startup in_progress should return 202"
                else:
                    assert (
                        response.status_code == 200
                    ), f"{framework['name']}: Non-startup in_progress should return 200"


class TestHealthCheckPerformance:
    """Test health check performance."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    async def test_health_check_response_time(self, framework: Dict[str, Any]):
        """Test that health checks respond quickly."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}/health/live"
            try:
                import time

                start = time.time()
                response = await client.get(url, timeout=5.0)
                elapsed = (time.time() - start) * 1000  # ms

                # Health checks should respond in < 1 second
                assert (
                    elapsed < 1000
                ), f"{framework['name']}: Liveness probe too slow ({elapsed:.0f}ms)"

                # Ideally < 100ms
                if elapsed > 100:
                    print(
                        f"Warning: {framework['name']} liveness took {elapsed:.0f}ms"
                    )

            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    async def test_health_check_caching(self, framework: Dict[str, Any]):
        """Test that health checks use caching."""
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{framework['port']}/health/ready"

            try:
                # Make two requests quickly
                response1 = await client.get(url, timeout=5.0)
                response2 = await client.get(url, timeout=5.0)

                data1 = response1.json()
                data2 = response2.json()

                # Timestamps should be identical (cached)
                assert (
                    data1["timestamp"] == data2["timestamp"]
                ), f"{framework['name']}: Health checks not cached (different timestamps)"

            except httpx.ConnectError:
                pytest.skip(f"{framework['name']} not running")


class TestCrossFrameworkConsistency:
    """Test consistency across frameworks."""

    @pytest.mark.asyncio
    async def test_all_frameworks_same_schema(self):
        """Test that all frameworks return consistent schema."""
        results: List[Dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            for framework in FRAMEWORKS:
                url = f"http://localhost:{framework['port']}/health"
                try:
                    response = await client.get(url, timeout=5.0)
                    data = response.json()
                    results.append({"framework": framework["name"], "data": data})
                except httpx.ConnectError:
                    continue

        if not results:
            pytest.skip("No frameworks running")

        # Compare all fields
        reference = results[0]["data"]
        for result in results[1:]:
            data = result["data"]

            # All should have same fields
            assert set(reference.keys()) == set(
                data.keys()
            ), f"Field mismatch: {reference.keys()} vs {data.keys()}"

            # All should have same check types
            ref_checks = set(reference["checks"].keys())
            data_checks = set(data["checks"].keys())
            assert (
                ref_checks == data_checks
            ), f"{result['framework']}: Check types differ from {results[0]['framework']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
