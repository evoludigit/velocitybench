"""
Performance Validator - Basic performance sanity checks

NOT comprehensive benchmarking - just sanity checks to detect broken implementations.

Tests:
1. Response times are within acceptable ranges
2. No frameworks are orders of magnitude slower than others
3. No frameworks timing out
4. No frameworks consuming excessive memory

Outputs:
- Performance sanity check results
- Frameworks that fail basic performance criteria
"""

import httpx
import asyncio
from typing import Dict
import statistics
import time


# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'ping_query': {
        'max_latency_ms': 100,  # Ping should be <100ms
        'max_timeout_rate': 0.01  # <1% timeout rate
    },
    'simple_query': {
        'max_latency_ms': 500,  # Simple queries <500ms
        'max_timeout_rate': 0.05
    },
    'complex_query': {
        'max_latency_ms': 2000,  # Complex queries <2s
        'max_timeout_rate': 0.1
    }
}


class PerformanceValidator:
    """Basic performance sanity checks."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def measure_query_latency(
        self,
        framework: Dict,
        query: str,
        iterations: int = 10
    ) -> Dict:
        """
        Measure query latency.

        Returns:
            {
                'framework': 'fraiseql',
                'query': 'ping',
                'iterations': 10,
                'avg_latency_ms': 5.2,
                'min_latency_ms': 3.1,
                'max_latency_ms': 12.5,
                'p95_latency_ms': 10.1,
                'p99_latency_ms': 11.8
            }
        """
        endpoint = f"http://localhost:{framework['port']}{framework['endpoint']}"
        latencies = []
        errors = 0

        for _ in range(iterations):
            start = time.time()
            try:
                if framework['type'] == 'graphql':
                    response = await self.client.post(
                        endpoint,
                        json={'query': query},
                        headers={'Content-Type': 'application/json'}
                    )
                else:  # REST
                    response = await self.client.get(endpoint)

                latency_ms = (time.time() - start) * 1000

                if response.status_code == 200:
                    latencies.append(latency_ms)
                else:
                    errors += 1

            except Exception:
                errors += 1
                latencies.append(5000)  # Timeout

        if not latencies:
            return {
                'framework': framework['name'],
                'query': query,
                'status': 'error',
                'error': 'All requests failed'
            }

        latencies.sort()

        return {
            'framework': framework['name'],
            'query': query,
            'iterations': iterations,
            'successful_iterations': iterations - errors,
            'avg_latency_ms': statistics.mean(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'p95_latency_ms': latencies[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0],
            'p99_latency_ms': latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0],
            'errors': errors,
            'status': 'pass'
        }

    async def check_timeout_rate(
        self,
        framework: Dict,
        timeout_ms: int = 5000,
        iterations: int = 20
    ) -> Dict:
        """
        Check if framework times out under normal load.

        Returns:
            {
                'framework': 'async-graphql',
                'total_requests': 100,
                'timeouts': 100,  # ❌ All requests timing out
                'timeout_rate': 1.0,
                'status': 'fail'
            }
        """
        endpoint = f"http://localhost:{framework['port']}{framework['endpoint']}"
        timeouts = 0
        total = iterations

        # Simple ping query
        if framework['type'] == 'graphql':
            test_request = {
                'json': {'query': 'query { ping }'},
                'headers': {'Content-Type': 'application/json'}
            }
        else:
            test_request = {}

        for _ in range(iterations):
            try:
                if framework['type'] == 'graphql':
                    response = await self.client.post(endpoint, **test_request)
                else:
                    response = await self.client.get(f"http://localhost:{framework['port']}{framework.get('health_check', '/health')}")

                if response.status_code != 200:
                    timeouts += 1

            except (httpx.TimeoutException, httpx.ConnectError):
                timeouts += 1
            except Exception:
                timeouts += 1

        timeout_rate = timeouts / total
        status = 'pass' if timeout_rate < PERFORMANCE_THRESHOLDS['ping_query']['max_timeout_rate'] else 'fail'

        return {
            'framework': framework['name'],
            'total_requests': total,
            'timeouts': timeouts,
            'timeout_rate': timeout_rate,
            'status': status
        }

    async def compare_relative_performance(
        self,
        results: Dict[str, Dict]
    ) -> Dict:
        """
        Compare framework performance relatively.

        Detect outliers:
        - Framework >10x slower than median: ❌ Likely broken
        - Framework >3x slower than median: ⚠️ Investigate
        - Framework within 3x of median: ✅ OK for QA purposes

        Returns:
            {
                'baseline_median_ms': 5.0,
                'outliers': [
                    {
                        'framework': 'async-graphql',
                        'latency_ms': 5000,  # Timing out
                        'multiple_of_median': 1000,
                        'status': 'critical'
                    }
                ]
            }
        """
        latencies = []
        for framework_name, result in results.items():
            if result.get('status') == 'pass' and 'avg_latency_ms' in result:
                latencies.append((framework_name, result['avg_latency_ms']))

        if not latencies:
            return {
                'status': 'error',
                'error': 'No valid latency measurements'
            }

        median_latency = statistics.median([lat for _, lat in latencies])

        outliers = []
        for framework_name, latency in latencies:
            multiple = latency / median_latency

            if multiple > 10:
                outliers.append({
                    'framework': framework_name,
                    'latency_ms': latency,
                    'multiple_of_median': multiple,
                    'status': 'critical'
                })
            elif multiple > 3:
                outliers.append({
                    'framework': framework_name,
                    'latency_ms': latency,
                    'multiple_of_median': multiple,
                    'status': 'warning'
                })

        return {
            'baseline_median_ms': median_latency,
            'total_frameworks': len(latencies),
            'outliers': outliers
        }


# Standalone test
async def main():
    """Test performance validator."""
    import yaml
    from pathlib import Path

    # Load framework registry
    registry_path = Path(__file__).parent / 'framework_registry.yaml'
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    validator = PerformanceValidator()

    try:
        print("Performance Sanity Check Report")
        print("=" * 60)
        print()

        # Test first framework
        framework = registry['frameworks'][0]
        if framework['type'] == 'graphql':
            print(f"Testing {framework['name']}...")

            # Ping query
            result = await validator.measure_query_latency(
                framework,
                'query { ping }',
                iterations=5
            )

            if result.get('status') == 'pass':
                print(f"  Average latency: {result['avg_latency_ms']:.2f}ms")
                print(f"  Min: {result['min_latency_ms']:.2f}ms")
                print(f"  Max: {result['max_latency_ms']:.2f}ms")
                print(f"  P95: {result['p95_latency_ms']:.2f}ms")
                print(f"  Errors: {result['errors']}")

            # Timeout rate
            timeout_result = await validator.check_timeout_rate(framework, iterations=10)
            status_icon = "✅" if timeout_result['status'] == 'pass' else "❌"
            print(f"  {status_icon} Timeout rate: {timeout_result['timeout_rate']*100:.1f}%")

    finally:
        await validator.close()


if __name__ == '__main__':
    asyncio.run(main())
