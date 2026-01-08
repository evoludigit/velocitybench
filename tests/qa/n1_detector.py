"""
N+1 Query Detector - Detects N+1 query patterns

Tests:
1. Monitors database query count during GraphQL operations
2. Detects if fetching N items triggers N+1 database queries
3. Validates DataLoader/batching is working correctly

Approach:
- Enable PostgreSQL query logging
- Execute test queries that should trigger batching
- Count actual database queries executed
- Compare against expected query count

Outputs:
- Query count per operation
- N+1 detection results
- Batching efficiency score
"""

import asyncpg
import httpx
from typing import Dict, List
import re
import time


# Test cases for N+1 detection
N1_TEST_CASES = {
    'users_with_posts': {
        'query': '''
            query {
                users(limit: 10) {
                    id
                    username
                    posts(limit: 5) {
                        id
                        title
                    }
                }
            }
        ''',
        'expected_queries': 2,  # 1 for users, 1 batched for all posts
        'max_acceptable_queries': 3
    },
    'posts_with_authors': {
        'query': '''
            query {
                posts(limit: 10) {
                    id
                    title
                    author {
                        id
                        username
                    }
                }
            }
        ''',
        'expected_queries': 2,  # 1 for posts, 1 batched for authors
        'max_acceptable_queries': 3
    },
    'posts_with_comments_and_authors': {
        'query': '''
            query {
                posts(limit: 10) {
                    id
                    title
                    comments(limit: 5) {
                        id
                        content
                        author {
                            username
                        }
                    }
                }
            }
        ''',
        'expected_queries': 3,  # posts, comments (batched), authors (batched)
        'max_acceptable_queries': 4
    }
}


class N1Detector:
    """Detects N+1 query anti-patterns."""

    def __init__(self):
        self.conn: asyncpg.Connection | None = None
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def connect_to_db(self, db_url: str):
        """Connect directly to PostgreSQL for query monitoring."""
        self.conn = await asyncpg.connect(db_url)

    async def close(self):
        """Close connections."""
        if self.conn:
            await self.conn.close()
        await self.http_client.aclose()

    async def enable_query_logging(self):
        """
        Enable PostgreSQL query logging for this session.

        Uses pg_stat_statements extension if available.
        """
        try:
            # Check if pg_stat_statements is available
            result = await self.conn.fetchval(
                "SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements'"
            )
            if result > 0:
                # Reset statistics
                await self.conn.execute("SELECT pg_stat_statements_reset()")
                return True
            return False
        except Exception:
            return False

    async def get_query_count(self) -> int:
        """
        Get number of queries executed since last reset.

        Query:
            SELECT COUNT(*) FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat%'
        """
        try:
            count = await self.conn.fetchval("""
                SELECT COUNT(DISTINCT query)
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat%'
                    AND query NOT LIKE '%pg_extension%'
                    AND query NOT LIKE 'SELECT%pg_catalog%'
            """)
            return count or 0
        except Exception:
            return -1  # pg_stat_statements not available

    async def get_queries_executed(self) -> List[str]:
        """Get list of queries executed since last reset."""
        try:
            rows = await self.conn.fetch("""
                SELECT query, calls
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat%'
                    AND query NOT LIKE '%pg_extension%'
                    AND query NOT LIKE 'SELECT%pg_catalog%'
                ORDER BY calls DESC
            """)
            return [(row['query'], row['calls']) for row in rows]
        except Exception:
            return []

    async def test_n1_pattern(
        self,
        framework: Dict,
        test_case: str
    ) -> Dict:
        """
        Test for N+1 queries.

        Test cases:
        1. "users_with_posts": Fetch 10 users with their posts
           - Expected queries: 1 (users) + 1 (batched posts) = 2
           - N+1 pattern: 1 (users) + 10 (individual post queries) = 11

        2. "posts_with_authors_and_comments": Fetch 10 posts with authors and comments
           - Expected: 1 (posts) + 1 (authors) + 1 (comments) = 3
           - N+1 pattern: 1 + 10 + 10 = 21

        Returns:
            {
                'test_case': 'users_with_posts',
                'items_fetched': 10,
                'query_count': 2,
                'expected_query_count': 2,
                'status': 'pass' | 'fail',
                'efficiency_score': 1.0,  # expected / actual
                'has_n1_pattern': False
            }
        """
        if test_case not in N1_TEST_CASES:
            return {
                'test_case': test_case,
                'status': 'error',
                'error': f'Unknown test case: {test_case}'
            }

        test_info = N1_TEST_CASES[test_case]

        # Only test GraphQL frameworks
        if framework['type'] != 'graphql':
            return {
                'test_case': test_case,
                'status': 'skipped',
                'reason': 'N+1 detection only for GraphQL'
            }

        # Reset query statistics
        await self.enable_query_logging()
        query_count_before = await self.get_query_count()

        # Execute test query
        endpoint = f"http://localhost:{framework['port']}{framework['endpoint']}"
        try:
            response = await self.http_client.post(
                endpoint,
                json={'query': test_info['query']},
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code != 200:
                return {
                    'test_case': test_case,
                    'status': 'error',
                    'error': f'HTTP {response.status_code}'
                }

            result = response.json()
            if 'errors' in result:
                return {
                    'test_case': test_case,
                    'status': 'error',
                    'error': str(result['errors'])
                }

        except Exception as e:
            return {
                'test_case': test_case,
                'status': 'error',
                'error': str(e)
            }

        # Get query count after
        query_count_after = await self.get_query_count()

        if query_count_before == -1 or query_count_after == -1:
            return {
                'test_case': test_case,
                'status': 'unavailable',
                'reason': 'pg_stat_statements extension not available'
            }

        actual_query_count = query_count_after - query_count_before
        expected_query_count = test_info['expected_queries']
        max_acceptable = test_info['max_acceptable_queries']

        has_n1_pattern = actual_query_count > max_acceptable
        efficiency_score = expected_query_count / max(actual_query_count, 1)

        status = 'pass' if actual_query_count <= max_acceptable else 'fail'

        return {
            'test_case': test_case,
            'items_fetched': 10,  # Hard-coded for now
            'query_count': actual_query_count,
            'expected_query_count': expected_query_count,
            'max_acceptable_queries': max_acceptable,
            'status': status,
            'efficiency_score': efficiency_score,
            'has_n1_pattern': has_n1_pattern
        }

    async def analyze_query_patterns(self, queries: List[tuple]) -> Dict:
        """
        Analyze query patterns to detect batching.

        Look for:
        - "WHERE id = ANY($1)" - batch loading pattern
        - "WHERE id IN (...)" - batch loading pattern
        - "WHERE id = $1" in loop - N+1 pattern
        """
        batch_patterns = []
        n1_patterns = []

        for query, calls in queries:
            # Batch loading patterns
            if 'ANY($' in query or 'IN (' in query:
                batch_patterns.append({'query': query, 'calls': calls})
            # N+1 pattern: same query called multiple times
            elif calls > 5:
                n1_patterns.append({'query': query, 'calls': calls})

        return {
            'batch_patterns_found': len(batch_patterns),
            'potential_n1_patterns': len(n1_patterns),
            'batch_queries': batch_patterns,
            'n1_queries': n1_patterns
        }


# Standalone test
async def main():
    """Test N+1 detector."""
    import yaml
    from pathlib import Path

    # Load framework registry
    registry_path = Path(__file__).parent / 'framework_registry.yaml'
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    # Load config
    config_path = Path(__file__).parent / 'validation_config.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)

    detector = N1Detector()
    await detector.connect_to_db(config['database']['url'])

    try:
        print("N+1 Query Detection Report")
        print("=" * 60)
        print()

        # Test first GraphQL framework
        frameworks = [f for f in registry['frameworks'] if f['type'] == 'graphql']
        if frameworks:
            framework = frameworks[0]
            print(f"Testing {framework['name']}...")

            for test_case in N1_TEST_CASES.keys():
                result = await detector.test_n1_pattern(framework, test_case)
                status_icon = "✅" if result['status'] == 'pass' else "❌"
                print(f"\n{status_icon} {test_case}:")
                if 'query_count' in result:
                    print(f"  Queries executed: {result['query_count']}")
                    print(f"  Expected: {result['expected_query_count']}")
                    print(f"  Efficiency: {result['efficiency_score']:.2f}")
                    print(f"  Has N+1: {result['has_n1_pattern']}")
                elif 'reason' in result:
                    print(f"  Status: {result['status']} - {result['reason']}")
                elif 'error' in result:
                    print(f"  Error: {result['error']}")

    finally:
        await detector.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
