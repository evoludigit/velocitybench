"""
Main Framework Validator - Orchestrates all validation checks

Runs all validators in order and generates comprehensive report.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import asyncpg
import yaml

from .config_validator import ConfigValidator
from .data_consistency_validator import DataConsistencyValidator
from .n1_detector import N1Detector
from .performance_validator import PerformanceValidator
from .query_validator import QueryValidator
from .schema_validator import SchemaValidator


class FrameworkValidator:
    """Main validation orchestrator."""

    def __init__(self, registry_path: str, config_path: str):
        """Load framework registry and validation config."""
        self.registry = self._load_yaml(registry_path)
        self.config = self._load_yaml(config_path)

        # Initialize validators
        self.schema_validator = SchemaValidator()
        self.query_validator = QueryValidator()
        self.n1_detector = N1Detector()
        self.consistency_validator = DataConsistencyValidator()
        self.config_validator = ConfigValidator()
        self.performance_validator = PerformanceValidator()

        self.test_ids = {}

    def _load_yaml(self, path: str) -> dict:
        """Load YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)

    async def _fetch_test_ids(self):
        """Fetch test IDs from database."""
        conn = await asyncpg.connect(self.config['database']['url'])
        try:
            # Get first user
            user = await conn.fetchrow('SELECT id FROM benchmark.tv_user LIMIT 1')
            if user:
                self.test_ids['TEST_USER_ID'] = str(user['id'])

            # Get first post
            post = await conn.fetchrow('SELECT id FROM benchmark.tv_post LIMIT 1')
            if post:
                self.test_ids['TEST_POST_ID'] = str(post['id'])

            # Get first comment
            comment = await conn.fetchrow('SELECT id FROM benchmark.tv_comment LIMIT 1')
            if comment:
                self.test_ids['TEST_COMMENT_ID'] = str(comment['id'])

        finally:
            await conn.close()

    async def validate_all_frameworks(self) -> dict:
        """
        Run all validation checks against all frameworks.

        Returns comprehensive validation report.
        """
        # Fetch test IDs from database
        print("Fetching test IDs from database...")
        await self._fetch_test_ids()
        print(f"Test IDs: {self.test_ids}\n")

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_frameworks': len(self.registry['frameworks']),
            'test_ids': self.test_ids,
            'frameworks': {}
        }

        # Connect database for schema validation
        await self.schema_validator.connect(self.config['database']['url'])
        await self.n1_detector.connect_to_db(self.config['database']['url'])

        try:
            for framework in self.registry['frameworks']:
                print(f"\n{'='*60}")
                print(f"Validating: {framework['name']} ({framework['language']} - {framework['type']})")
                print(f"{'='*60}")

                framework_results = await self._validate_framework(framework)
                results['frameworks'][framework['name']] = framework_results

        finally:
            await self.schema_validator.close()
            await self.n1_detector.close()
            await self.query_validator.close()
            await self.consistency_validator.close()
            await self.config_validator.close()
            await self.performance_validator.close()

        # Generate summary
        results['summary'] = self._generate_summary(results)

        return results

    async def _validate_framework(self, framework: dict) -> dict:
        """Run all validation checks for a single framework."""
        results = {
            'framework': framework['name'],
            'language': framework['language'],
            'type': framework['type'],
            'checks': {}
        }

        # 1. Schema validation
        print("  [1/6] Validating schema references...")
        results['checks']['schema'] = await self.schema_validator.verify_framework_schema(framework)
        status_icon = "✅" if results['checks']['schema']['status'] == 'pass' else "❌"
        print(f"        {status_icon} {results['checks']['schema']['status'].upper()}")

        # 2. Config validation
        print("  [2/6] Validating configuration...")
        results['checks']['config'] = {
            'health': await self.config_validator.check_health_endpoint(framework),
            'metrics': await self.config_validator.check_metrics_endpoint(framework),
            'pool': await self.config_validator.verify_pool_config(framework),
            'database': await self.config_validator.verify_database_connection(framework)
        }
        health_status = results['checks']['config']['health']['status']
        status_icon = "✅" if health_status == 'pass' else "❌"
        print(f"        {status_icon} Health: {health_status}")

        # Skip remaining checks if framework is not running
        if health_status != 'pass':
            print("        ⏭️  Skipping remaining checks (framework not running)")
            results['overall_status'] = 'broken'
            return results

        # 3. Query validation
        print("  [3/6] Validating query support...")
        results['checks']['queries'] = await self.query_validator.verify_query_support(framework, self.test_ids)
        supported = results['checks']['queries']['supported_queries']
        passing = sum(1 for v in supported.values() if v == 'pass')
        total = len(supported)
        print(f"        ℹ️  {passing}/{total} queries passing")

        # 4. N+1 detection (only for GraphQL)
        print("  [4/6] Detecting N+1 query patterns...")
        if framework['type'] == 'graphql':
            results['checks']['n1_queries'] = {}
            for test_case in ['users_with_posts', 'posts_with_authors']:
                result = await self.n1_detector.test_n1_pattern(framework, test_case)
                results['checks']['n1_queries'][test_case] = result
                if result.get('status') == 'pass':
                    print(f"        ✅ {test_case}: {result.get('query_count', 'N/A')} queries")
                elif result.get('status') == 'unavailable':
                    print(f"        ⚠️  {test_case}: {result.get('reason', 'N/A')}")
        else:
            results['checks']['n1_queries'] = {'status': 'skipped', 'reason': 'REST framework'}
            print("        ⏭️  Skipped (REST framework)")

        # 5. Performance sanity checks
        print("  [5/6] Running performance sanity checks...")
        if framework['type'] == 'graphql':
            ping_result = await self.performance_validator.measure_query_latency(framework, 'query { ping }', iterations=5)
            results['checks']['performance'] = {
                'ping': ping_result,
                'timeout_rate': await self.performance_validator.check_timeout_rate(framework, iterations=10)
            }
            if ping_result.get('status') == 'pass':
                print(f"        ✅ Avg latency: {ping_result['avg_latency_ms']:.2f}ms")
        else:
            results['checks']['performance'] = {'status': 'skipped'}
            print("        ⏭️  Skipped")

        # 6. Data consistency (will be run separately across all frameworks)
        print("  [6/6] Data consistency check...")
        print("        ⏭️  Will be compared against baseline later")

        # Calculate overall status
        results['overall_status'] = self._calculate_status(results['checks'])
        print(f"\n  Overall Status: {results['overall_status'].upper()}")

        return results

    def _calculate_status(self, checks: dict) -> str:
        """
        Calculate overall status based on all checks.

        Returns: 'pass' | 'warning' | 'fail' | 'broken'
        """
        # Check for broken status
        if checks.get('config', {}).get('health', {}).get('status') != 'pass':
            return 'broken'  # Framework not running

        # Check for critical failures
        schema_status = checks.get('schema', {}).get('status')
        if schema_status == 'fail':
            return 'fail'

        query_results = checks.get('queries', {}).get('supported_queries', {})
        if query_results:
            passing = sum(1 for v in query_results.values() if v == 'pass')
            if passing < len(query_results) * 0.5:  # Less than 50% passing
                return 'fail'

        # Check for warnings
        if checks.get('schema', {}).get('issues'):
            return 'warning'

        return 'pass'

    def _generate_summary(self, results: dict) -> dict:
        """Generate summary statistics."""
        frameworks = results['frameworks']

        statuses = [f['overall_status'] for f in frameworks.values()]

        return {
            'total_frameworks': len(frameworks),
            'status_breakdown': {
                'pass': statuses.count('pass'),
                'warning': statuses.count('warning'),
                'fail': statuses.count('fail'),
                'broken': statuses.count('broken')
            },
            'broken_frameworks': [
                name for name, f in frameworks.items()
                if f['overall_status'] == 'broken'
            ],
            'failing_frameworks': [
                name for name, f in frameworks.items()
                if f['overall_status'] == 'fail'
            ]
        }

    async def generate_report(self, results: dict, output_path: str):
        """Generate markdown validation report."""
        report = []

        report.append("# Framework Validation Report\n")
        report.append(f"**Generated**: {results['timestamp']}\n")
        report.append(f"**Total Frameworks**: {results['total_frameworks']}\n\n")

        # Summary
        report.append("## Summary\n")
        summary = results['summary']
        report.append(f"- ✅ **Pass**: {summary['status_breakdown']['pass']}")
        report.append(f"- ⚠️ **Warning**: {summary['status_breakdown']['warning']}")
        report.append(f"- ❌ **Fail**: {summary['status_breakdown']['fail']}")
        report.append(f"- 🚨 **Broken**: {summary['status_breakdown']['broken']}\n")

        if summary['broken_frameworks']:
            report.append("\n### 🚨 Broken Frameworks (Not Running)\n")
            for name in summary['broken_frameworks']:
                report.append(f"- {name}")

        if summary['failing_frameworks']:
            report.append("\n### ❌ Failing Frameworks\n")
            for name in summary['failing_frameworks']:
                report.append(f"- {name}")

        # Individual framework results
        report.append("\n## Individual Framework Results\n")

        for name, framework in results['frameworks'].items():
            status_icon = {
                'pass': '✅',
                'warning': '⚠️',
                'fail': '❌',
                'broken': '🚨'
            }[framework['overall_status']]

            report.append(f"\n### {status_icon} {name} ({framework['language']} - {framework['type']})\n")
            report.append(f"**Overall Status**: {framework['overall_status'].upper()}\n")

            # Schema check
            schema = framework['checks'].get('schema', {})
            report.append(f"\n**Schema Validation**: {schema.get('status', 'unknown')}")
            if schema.get('missing_tables'):
                report.append(f"  - Missing tables: {', '.join(schema['missing_tables'])}")

            # Query support
            queries = framework['checks'].get('queries', {})
            supported = queries.get('supported_queries', {})
            if supported:
                passing = sum(1 for v in supported.values() if v == 'pass')
                total = len(supported)
                report.append(f"\n**Query Support**: {passing}/{total} queries passing")

            # N+1 detection
            n1 = framework['checks'].get('n1_queries', {})
            if isinstance(n1, dict) and 'status' not in n1:
                has_n1 = any(test.get('has_n1_pattern') for test in n1.values() if isinstance(test, dict))
                report.append(f"\n**N+1 Queries**: {'❌ Detected' if has_n1 else '✅ None detected'}")

            # Performance
            perf = framework['checks'].get('performance', {})
            if perf.get('ping'):
                ping_data = perf['ping']
                if ping_data.get('status') == 'pass':
                    report.append(f"\n**Performance**: Ping {ping_data['avg_latency_ms']:.1f}ms avg")

        # Write report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))

        print(f"\n✅ Report generated: {output_path}")

    async def generate_json_report(self, results: dict, output_path: str):
        """Generate JSON validation report for programmatic use."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✅ JSON report generated: {output_path}")


# CLI entry point
async def main():
    """Main entry point for validation."""
    validator = FrameworkValidator(
        registry_path='tests/qa/framework_registry.yaml',
        config_path='tests/qa/validation_config.yaml'
    )

    print("Starting comprehensive framework validation...\n")
    results = await validator.validate_all_frameworks()

    # Generate reports
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    await validator.generate_report(
        results,
        f'reports/qa-verification-{date_str}.md'
    )
    await validator.generate_json_report(
        results,
        f'reports/qa-verification-{date_str}.json'
    )

    # Exit code based on results
    if results['summary']['status_breakdown']['broken'] > 0:
        print("\n🚨 CRITICAL: Some frameworks are broken and not running!")
        return 2
    elif results['summary']['status_breakdown']['fail'] > 0:
        print("\n❌ FAIL: Some frameworks failed validation!")
        return 1
    elif results['summary']['status_breakdown']['warning'] > 0:
        print("\n⚠️ WARNING: Some frameworks have issues but are functional")
        return 0
    else:
        print("\n✅ SUCCESS: All frameworks passed validation!")
        return 0


if __name__ == '__main__':
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
