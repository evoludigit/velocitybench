"""
Query Validator - Verifies GraphQL/REST queries return correct data

Tests:
1. All required queries are supported (ping, user, users, post, posts, etc.)
2. Queries return correct data shape
3. Relationships are resolved correctly (user.posts, post.author, etc.)
4. Mutations work and return updated data
5. Error handling works (invalid IDs, missing data)

Outputs:
- Query support matrix (which queries each framework supports)
- Data shape validation results
- Relationship resolution test results
"""

import httpx
import asyncio
import json
from typing import Dict, List, Any
from dataclasses import dataclass
from pathlib import Path
import time


@dataclass
class QueryTest:
    name: str
    query_type: str  # 'graphql' | 'rest'
    query: str  # GraphQL query or REST path
    variables: Dict[str, Any]
    expected_fields: List[str]
    expected_relationships: List[str]


class QueryValidator:
    """Validates framework query implementations."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_queries = self._load_test_queries()

    def _load_test_queries(self) -> Dict:
        """Load test queries from fixtures."""
        fixtures_path = Path(__file__).parent / 'fixtures' / 'test_queries.json'
        with open(fixtures_path) as f:
            return json.load(f)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def _replace_variables(self, data: Any, replacements: Dict[str, str]) -> Any:
        """Replace placeholder variables in queries/paths."""
        if isinstance(data, str):
            for key, value in replacements.items():
                data = data.replace(f"{{{{{key}}}}}", str(value))
            return data
        elif isinstance(data, dict):
            return {k: self._replace_variables(v, replacements) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables(item, replacements) for item in data]
        return data

    async def test_graphql_query(
        self,
        endpoint: str,
        query: str,
        variables: Dict = None
    ) -> Dict:
        """
        Execute GraphQL query and validate response.

        Returns:
            {
                'success': bool,
                'data': dict,
                'errors': list,
                'latency_ms': float
            }
        """
        start = time.time()
        try:
            response = await self.client.post(
                endpoint,
                json={'query': query, 'variables': variables or {}},
                headers={'Content-Type': 'application/json'}
            )
            latency_ms = (time.time() - start) * 1000

            if response.status_code != 200:
                return {
                    'success': False,
                    'data': None,
                    'errors': [f"HTTP {response.status_code}: {response.text}"],
                    'latency_ms': latency_ms
                }

            result = response.json()
            return {
                'success': 'errors' not in result or not result['errors'],
                'data': result.get('data'),
                'errors': result.get('errors'),
                'latency_ms': latency_ms
            }
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return {
                'success': False,
                'data': None,
                'errors': [str(e)],
                'latency_ms': latency_ms
            }

    async def test_rest_query(
        self,
        endpoint: str,
        method: str,
        path: str,
        params: Dict = None
    ) -> Dict:
        """Execute REST query and validate response."""
        start = time.time()
        try:
            url = f"{endpoint}{path}"
            response = await self.client.request(
                method,
                url,
                params=params
            )
            latency_ms = (time.time() - start) * 1000

            if response.status_code != 200:
                return {
                    'success': False,
                    'data': None,
                    'errors': [f"HTTP {response.status_code}: {response.text}"],
                    'latency_ms': latency_ms
                }

            result = response.json()
            return {
                'success': True,
                'data': result,
                'errors': None,
                'latency_ms': latency_ms
            }
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return {
                'success': False,
                'data': None,
                'errors': [str(e)],
                'latency_ms': latency_ms
            }

    def _validate_data_shape(
        self,
        data: Any,
        expected_fields: List[str]
    ) -> Dict:
        """
        Verify response has correct shape.

        Checks:
        - User has: id, username, first_name, last_name, bio
        - Post has: id, title, content, author
        - Comment has: id, content, author, post
        """
        if not data:
            return {
                'valid': False,
                'missing_fields': expected_fields,
                'issues': ['No data returned']
            }

        missing_fields = []
        for field in expected_fields:
            # Handle nested fields (e.g., "author.username")
            if '.' in field:
                parts = field.split('.')
                current = data
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        missing_fields.append(field)
                        break
            else:
                # Handle both camelCase and snake_case
                if field not in data:
                    # Try converting field name
                    snake_case = self._camel_to_snake(field)
                    camel_case = self._snake_to_camel(field)
                    if snake_case not in data and camel_case not in data:
                        missing_fields.append(field)

        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'issues': [f"Missing field: {f}" for f in missing_fields]
        }

    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case."""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    def _snake_to_camel(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        components = name.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    async def verify_query_support(
        self,
        framework: Dict,
        test_ids: Dict[str, str]
    ) -> Dict:
        """
        Test all standard queries against framework.

        Tests:
        - ping query
        - user(id: "...") query
        - users(limit: 10) query
        - user { posts { title } } nested query
        - post { author { username } } nested query
        - post { comments { author { username } } } deep nested query

        Returns:
            {
                'framework': 'fraiseql',
                'supported_queries': {
                    'ping': 'pass',
                    'user': 'pass',
                    'users': 'pass',
                    'user_with_posts': 'fail',  # if not working
                    ...
                },
                'issues': []
            }
        """
        supported_queries = {}
        issues = []

        # Build endpoint URL
        base_url = f"http://localhost:{framework['port']}"

        if framework['type'] == 'graphql':
            endpoint = f"{base_url}{framework['endpoint']}"
            queries = self.test_queries['graphql_queries']

            for query_name, query_info in queries.items():
                # Replace test IDs
                query = self._replace_variables(query_info['query'], test_ids)
                variables = self._replace_variables(query_info.get('variables', {}), test_ids)

                result = await self.test_graphql_query(endpoint, query, variables)

                if result['success']:
                    # Validate data shape if expected_fields specified
                    if 'expected_fields' in query_info and result['data']:
                        # Extract the root data object
                        data_obj = result['data']
                        # Find the first key (e.g., 'user', 'users', 'posts')
                        if data_obj:
                            first_key = next(iter(data_obj.keys()))
                            actual_data = data_obj[first_key]
                            # If it's a list, check first item
                            if isinstance(actual_data, list) and actual_data:
                                actual_data = actual_data[0]

                            shape_result = self._validate_data_shape(
                                actual_data,
                                query_info['expected_fields']
                            )
                            if not shape_result['valid']:
                                supported_queries[query_name] = 'warning'
                                issues.append(f"{query_name}: {', '.join(shape_result['issues'])}")
                            else:
                                supported_queries[query_name] = 'pass'
                        else:
                            supported_queries[query_name] = 'pass'
                    else:
                        supported_queries[query_name] = 'pass'
                else:
                    supported_queries[query_name] = 'fail'
                    error_msg = result['errors'][0] if result['errors'] else 'Unknown error'
                    issues.append(f"{query_name}: {error_msg}")

        else:  # REST
            endpoint = base_url
            queries = self.test_queries['rest_queries']

            for query_name, query_info in queries.items():
                path = self._replace_variables(query_info['path'], test_ids)
                method = query_info.get('method', 'GET')

                result = await self.test_rest_query(endpoint, method, path)

                if result['success']:
                    if 'expected_fields' in query_info:
                        shape_result = self._validate_data_shape(
                            result['data'],
                            query_info['expected_fields']
                        )
                        if not shape_result['valid']:
                            supported_queries[query_name] = 'warning'
                            issues.append(f"{query_name}: {', '.join(shape_result['issues'])}")
                        else:
                            supported_queries[query_name] = 'pass'
                    else:
                        supported_queries[query_name] = 'pass'
                else:
                    supported_queries[query_name] = 'fail'
                    error_msg = result['errors'][0] if result['errors'] else 'Unknown error'
                    issues.append(f"{query_name}: {error_msg}")

        return {
            'framework': framework['name'],
            'supported_queries': supported_queries,
            'issues': issues
        }


# Standalone test
async def main():
    """Test query validator."""
    import yaml

    # Load framework registry
    registry_path = Path(__file__).parent / 'framework_registry.yaml'
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    validator = QueryValidator()

    try:
        # Test IDs (these should be fetched from database in real usage)
        test_ids = {
            'TEST_USER_ID': '1',
            'TEST_POST_ID': '1',
            'TEST_COMMENT_ID': '1'
        }

        print("Query Validation Report")
        print("=" * 60)
        print()

        # Test first framework only for demo
        framework = registry['frameworks'][0]
        print(f"Testing {framework['name']}...")
        result = await validator.verify_query_support(framework, test_ids)

        print(f"\nSupported Queries:")
        for query, status in result['supported_queries'].items():
            icon = "✅" if status == 'pass' else ("⚠️" if status == 'warning' else "❌")
            print(f"  {icon} {query}: {status}")

        if result['issues']:
            print(f"\nIssues:")
            for issue in result['issues']:
                print(f"  - {issue}")

    finally:
        await validator.close()


if __name__ == '__main__':
    asyncio.run(main())
