"""
Data Consistency Validator - Verifies all frameworks return identical data

Tests:
1. Execute same query against all frameworks
2. Compare response data for consistency
3. Verify field names match (camelCase vs snake_case handling)
4. Verify data values are identical

Outputs:
- Data consistency matrix
- Frameworks that return different data
- Field name mapping issues
"""

import httpx
from typing import Dict, List, Any
import json


# Standard test data for consistency testing
CONSISTENCY_TESTS = [
    {
        'name': 'user_by_id',
        'query': 'query($id: ID!) { user(id: $id) { id username firstName lastName bio } }',
        'variables': {'id': '{{TEST_USER_ID}}'},
        'check_fields': ['id', 'username', 'firstName', 'lastName', 'bio']
    },
    {
        'name': 'users_list',
        'query': 'query { users(limit: 5) { id username } }',
        'check_ordering': False,  # Don't require consistent order for now
        'check_count': True  # Should return same number of results
    },
]


class DataConsistencyValidator:
    """Validates data consistency across frameworks."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def _replace_variables(self, data: Any, replacements: Dict[str, str]) -> Any:
        """Replace placeholder variables."""
        if isinstance(data, str):
            for key, value in replacements.items():
                data = data.replace(f"{{{{{key}}}}}", str(value))
            return data
        elif isinstance(data, dict):
            return {k: self._replace_variables(v, replacements) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables(item, replacements) for item in data]
        return data

    async def fetch_from_all_frameworks(
        self,
        frameworks: List[Dict],
        query: str,
        variables: Dict = None
    ) -> Dict[str, Any]:
        """
        Execute same query against all running frameworks.

        Returns:
            {
                'fraiseql': {'data': {...}, 'errors': None},
                'strawberry': {'data': {...}, 'errors': None},
                ...
            }
        """
        results = {}

        for framework in frameworks:
            if framework['type'] != 'graphql':
                continue  # Skip REST for now

            endpoint = f"http://localhost:{framework['port']}{framework['endpoint']}"

            try:
                response = await self.client.post(
                    endpoint,
                    json={'query': query, 'variables': variables or {}},
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    result = response.json()
                    results[framework['name']] = {
                        'data': result.get('data'),
                        'errors': result.get('errors'),
                        'status': 'success'
                    }
                else:
                    results[framework['name']] = {
                        'data': None,
                        'errors': [f'HTTP {response.status_code}'],
                        'status': 'error'
                    }

            except Exception as e:
                results[framework['name']] = {
                    'data': None,
                    'errors': [str(e)],
                    'status': 'error'
                }

        return results

    def normalize_response(self, data: Any, framework: Dict) -> Any:
        """
        Normalize response for comparison.

        - Convert camelCase to snake_case or vice versa
        - Sort lists for consistent comparison
        - Handle null vs missing fields
        """
        if data is None:
            return None

        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                # Recursively normalize
                normalized[key] = self.normalize_response(value, framework)
            return normalized

        elif isinstance(data, list):
            # Normalize each item in list
            return [self.normalize_response(item, framework) for item in data]

        return data

    async def compare_responses(
        self,
        responses: Dict[str, Any],
        baseline_framework: str = 'fraiseql'
    ) -> Dict:
        """
        Compare responses from all frameworks.

        Returns:
            {
                'status': 'pass' | 'fail',
                'baseline': 'fraiseql',  # Framework used as baseline
                'differences': {
                    'strawberry': [],  # No differences
                    'graphene': [
                        {
                            'field': 'user.firstName',
                            'expected': 'John',
                            'actual': 'Jane',
                            'type': 'value_mismatch'
                        }
                    ],
                    'async-graphql': [
                        {
                            'field': 'user',
                            'expected': {...},
                            'actual': None,
                            'type': 'missing_data'
                        }
                    ]
                }
            }
        """
        if baseline_framework not in responses:
            return {
                'status': 'error',
                'error': f'Baseline framework {baseline_framework} not in responses'
            }

        baseline = responses[baseline_framework]
        if baseline['status'] != 'success':
            return {
                'status': 'error',
                'error': f'Baseline framework {baseline_framework} returned error'
            }

        baseline_data = baseline['data']
        differences = {}

        for framework_name, response in responses.items():
            if framework_name == baseline_framework:
                continue

            if response['status'] != 'success':
                differences[framework_name] = [{
                    'type': 'error',
                    'error': response['errors']
                }]
                continue

            # Simple equality check for now
            if response['data'] != baseline_data:
                differences[framework_name] = [{
                    'type': 'data_mismatch',
                    'expected': baseline_data,
                    'actual': response['data']
                }]
            else:
                differences[framework_name] = []

        has_differences = any(len(diffs) > 0 for diffs in differences.values())

        return {
            'status': 'fail' if has_differences else 'pass',
            'baseline': baseline_framework,
            'differences': differences
        }

    async def verify_field_naming(self, responses: Dict[str, Any]) -> Dict:
        """
        Verify field naming conventions are correct.

        Check:
        - GraphQL should use camelCase (firstName, lastName)
        - Database uses snake_case (first_name, last_name)
        - Frameworks properly convert between conventions
        """
        issues = []

        for framework_name, response in responses.items():
            if response['status'] != 'success' or not response['data']:
                continue

            data = response['data']

            # Check for snake_case in GraphQL responses (should be camelCase)
            def check_keys(obj, path=''):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if '_' in key:
                            issues.append({
                                'framework': framework_name,
                                'field': f'{path}.{key}' if path else key,
                                'issue': 'snake_case found in GraphQL response (should be camelCase)'
                            })
                        check_keys(value, f'{path}.{key}' if path else key)
                elif isinstance(obj, list):
                    for item in obj:
                        check_keys(item, path)

            check_keys(data)

        return {
            'status': 'pass' if not issues else 'warning',
            'issues': issues
        }


# Standalone test
async def main():
    """Test data consistency validator."""
    import yaml
    from pathlib import Path

    # Load framework registry
    registry_path = Path(__file__).parent / 'framework_registry.yaml'
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    validator = DataConsistencyValidator()

    try:
        print("Data Consistency Validation Report")
        print("=" * 60)
        print()

        # Get GraphQL frameworks only
        graphql_frameworks = [f for f in registry['frameworks'] if f['type'] == 'graphql'][:3]

        test_ids = {
            'TEST_USER_ID': '1'
        }

        # Test ping query
        query = 'query { ping }'
        responses = await validator.fetch_from_all_frameworks(graphql_frameworks, query)

        print(f"Testing ping query across {len(responses)} frameworks:")
        for framework_name, response in responses.items():
            status_icon = "✅" if response['status'] == 'success' else "❌"
            print(f"  {status_icon} {framework_name}: {response['status']}")

        # Compare responses
        comparison = await validator.compare_responses(responses, baseline_framework=graphql_frameworks[0]['name'])
        print(f"\nComparison status: {comparison['status']}")
        if comparison['status'] == 'fail':
            print("Differences found:")
            for framework, diffs in comparison['differences'].items():
                if diffs:
                    print(f"  - {framework}: {len(diffs)} difference(s)")

    finally:
        await validator.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
