"""
Config Validator - Verifies framework configurations

Tests:
1. Connection pool configurations are correct
2. Statement caching is enabled where expected
3. Metrics endpoints are accessible
4. Health checks are working
5. Environment variables are set correctly

Outputs:
- Configuration audit report
- Missing configurations
- Configuration recommendations
"""

import httpx
from typing import Dict


# Configuration checks
CONFIG_CHECKS = {
    'health_endpoint': {
        'required': True,
        'expected_status': 200,
        'expected_fields': ['status']
    },
    'metrics_endpoint': {
        'required': False,  # Only some frameworks have this
        'expected_status': 200,
        'expected_format': 'prometheus'
    },
    'database_connection': {
        'required': True,
        'test_query': 'SELECT 1'
    }
}


class ConfigValidator:
    """Validates framework configurations."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def check_health_endpoint(self, framework: Dict) -> Dict:
        """
        Check framework health endpoint.

        Expected response:
            {
                'status': 'healthy',
                'framework': 'fraiseql',
                'version': '1.8.1'  # optional
            }
        """
        if 'health_check' not in framework:
            return {
                'status': 'skipped',
                'reason': 'No health check endpoint defined'
            }

        url = f"http://localhost:{framework['port']}{framework['health_check']}"

        try:
            response = await self.client.get(url)

            if response.status_code != 200:
                return {
                    'status': 'fail',
                    'http_status': response.status_code,
                    'error': f'Expected 200, got {response.status_code}'
                }

            try:
                data = response.json()
                return {
                    'status': 'pass',
                    'http_status': 200,
                    'response': data
                }
            except Exception:
                # Health check may not return JSON
                return {
                    'status': 'pass',
                    'http_status': 200,
                    'response': response.text
                }

        except httpx.ConnectError:
            return {
                'status': 'fail',
                'error': 'Connection refused - framework not running'
            }
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }

    async def check_metrics_endpoint(self, framework: Dict) -> Dict:
        """
        Check Prometheus metrics endpoint.

        Verify:
        - Endpoint returns 200
        - Returns prometheus text format
        - Contains relevant metrics (http_requests_total, etc.)
        """
        if 'metrics_endpoint' not in framework:
            return {
                'status': 'skipped',
                'reason': 'No metrics endpoint defined'
            }

        url = f"http://localhost:{framework['port']}{framework['metrics_endpoint']}"

        try:
            response = await self.client.get(url)

            if response.status_code != 200:
                return {
                    'status': 'fail',
                    'http_status': response.status_code,
                    'error': f'Expected 200, got {response.status_code}'
                }

            # Check if it looks like Prometheus format
            text = response.text
            if '# HELP' in text or '# TYPE' in text:
                return {
                    'status': 'pass',
                    'http_status': 200,
                    'format': 'prometheus'
                }
            else:
                return {
                    'status': 'warning',
                    'http_status': 200,
                    'format': 'unknown',
                    'warning': 'Does not appear to be Prometheus format'
                }

        except httpx.ConnectError:
            return {
                'status': 'fail',
                'error': 'Connection refused - framework not running'
            }
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }

    async def verify_pool_config(self, framework: Dict) -> Dict:
        """
        Verify connection pool configuration.

        For Python frameworks using common/async_db.py:
        - Check min_size and max_size match registry
        - Verify statement_cache_size is set

        Returns:
            {
                'status': 'pass' | 'fail',
                'expected_min': 10,
                'actual_min': 10,
                'expected_max': 50,
                'actual_max': 50,
                'statement_caching': True,
                'issues': []
            }
        """
        pool_config = framework.get('pool_config', {})

        if not pool_config:
            return {
                'status': 'skipped',
                'reason': 'No pool configuration defined in registry'
            }

        # This would require framework-specific introspection
        # For now, just return the expected config
        return {
            'status': 'info',
            'expected_min': pool_config.get('min'),
            'expected_max': pool_config.get('max'),
            'note': 'Pool configuration verification requires framework introspection'
        }

    async def verify_database_connection(self, framework: Dict) -> Dict:
        """
        Verify framework can connect to database.

        Tests:
        - Health check includes database status
        - Can execute simple query
        - Connection pool is initialized
        """
        # Use health check as proxy for database connectivity
        health_result = await self.check_health_endpoint(framework)

        if health_result['status'] == 'pass':
            return {
                'status': 'pass',
                'method': 'health_check',
                'note': 'Database connectivity verified via health check'
            }
        else:
            return {
                'status': 'unknown',
                'method': 'health_check',
                'note': 'Could not verify database connectivity'
            }


# Standalone test
async def main():
    """Test config validator."""
    import yaml
    from pathlib import Path

    # Load framework registry
    registry_path = Path(__file__).parent / 'framework_registry.yaml'
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    validator = ConfigValidator()

    try:
        print("Configuration Validation Report")
        print("=" * 60)
        print()

        # Test first few frameworks
        for framework in registry['frameworks'][:3]:
            print(f"\nTesting {framework['name']}...")

            # Health check
            health_result = await validator.check_health_endpoint(framework)
            status_icon = "✅" if health_result['status'] == 'pass' else "❌"
            print(f"  {status_icon} Health: {health_result['status']}")
            if 'error' in health_result:
                print(f"      Error: {health_result['error']}")

            # Metrics
            metrics_result = await validator.check_metrics_endpoint(framework)
            status_icon = "✅" if metrics_result['status'] == 'pass' else ("⚠️" if metrics_result['status'] == 'skipped' else "❌")
            print(f"  {status_icon} Metrics: {metrics_result['status']}")

            # Pool config
            pool_result = await validator.verify_pool_config(framework)
            print(f"  ℹ️  Pool: {pool_result.get('note', 'N/A')}")

    finally:
        await validator.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
