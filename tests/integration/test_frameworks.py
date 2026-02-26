#!/usr/bin/env python3
"""
Integration Test Suite for FraiseQL Performance Assessment
Tests all frameworks for health, API responses, validation, and error handling
"""

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class TestResult:
    """Test result for a single test"""
    framework: str
    test_name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None


@dataclass
class FrameworkConfig:
    """Configuration for a framework"""
    name: str
    port: int
    type: str  # 'graphql' or 'rest'
    health: str
    endpoint: str
    language: str
    category: str


class IntegrationTester:
    """Main integration test class"""

    def __init__(self, config_file: Path, timeout: int = 5):
        self.config_file = config_file
        self.timeout = timeout
        self.results: List[TestResult] = []
        self.session = self._create_session()
        self.frameworks: Dict[str, FrameworkConfig] = {}

        # Load configuration
        self._load_config()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _load_config(self):
        """Load framework configuration from JSON"""
        with open(self.config_file) as f:
            config = json.load(f)

        for name, info in config["frameworks"].items():
            self.frameworks[name] = FrameworkConfig(
                name=name,
                port=info["port"],
                type=info["type"],
                health=info["health"],
                endpoint=info["endpoint"],
                language=info["language"],
                category=info["category"],
            )

    def test_health(self, framework: FrameworkConfig) -> TestResult:
        """Test framework health endpoint"""
        start = time.time()
        url = f"http://localhost:{framework.port}{framework.health}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            duration = (time.time() - start) * 1000

            if response.status_code == 200:
                return TestResult(
                    framework=framework.name,
                    test_name="health_check",
                    passed=True,
                    duration_ms=duration,
                    response_data=response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                )
            else:
                return TestResult(
                    framework=framework.name,
                    test_name="health_check",
                    passed=False,
                    duration_ms=duration,
                    error_message=f"HTTP {response.status_code}",
                )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                framework=framework.name,
                test_name="health_check",
                passed=False,
                duration_ms=duration,
                error_message=str(e),
            )

    def test_graphql_introspection(self, framework: FrameworkConfig) -> TestResult:
        """Test GraphQL introspection query"""
        start = time.time()
        url = f"http://localhost:{framework.port}{framework.endpoint}"

        query = {
            "query": "{ __typename }"
        }

        try:
            response = self.session.post(
                url,
                json=query,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            duration = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    return TestResult(
                        framework=framework.name,
                        test_name="graphql_introspection",
                        passed=True,
                        duration_ms=duration,
                        response_data=data,
                    )
                else:
                    return TestResult(
                        framework=framework.name,
                        test_name="graphql_introspection",
                        passed=False,
                        duration_ms=duration,
                        error_message=f"No 'data' field in response: {data}",
                    )
            else:
                return TestResult(
                    framework=framework.name,
                    test_name="graphql_introspection",
                    passed=False,
                    duration_ms=duration,
                    error_message=f"HTTP {response.status_code}",
                )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                framework=framework.name,
                test_name="graphql_introspection",
                passed=False,
                duration_ms=duration,
                error_message=str(e),
            )

    def test_rest_endpoint(self, framework: FrameworkConfig) -> TestResult:
        """Test REST endpoint"""
        start = time.time()
        url = f"http://localhost:{framework.port}{framework.endpoint}"

        try:
            response = self.session.get(url, timeout=self.timeout, params={"limit": 5})
            duration = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, (list, dict)):
                    return TestResult(
                        framework=framework.name,
                        test_name="rest_endpoint",
                        passed=True,
                        duration_ms=duration,
                        response_data=data if isinstance(data, dict) else {"count": len(data)},
                    )
                else:
                    return TestResult(
                        framework=framework.name,
                        test_name="rest_endpoint",
                        passed=False,
                        duration_ms=duration,
                        error_message=f"Invalid JSON response type: {type(data)}",
                    )
            else:
                return TestResult(
                    framework=framework.name,
                    test_name="rest_endpoint",
                    passed=False,
                    duration_ms=duration,
                    error_message=f"HTTP {response.status_code}",
                )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                framework=framework.name,
                test_name="rest_endpoint",
                passed=False,
                duration_ms=duration,
                error_message=str(e),
            )

    def test_metrics(self, framework: FrameworkConfig) -> TestResult:
        """Test metrics endpoint (optional)"""
        start = time.time()
        url = f"http://localhost:{framework.port}/metrics"

        try:
            response = self.session.get(url, timeout=self.timeout)
            duration = (time.time() - start) * 1000

            if response.status_code in [200, 404]:
                # 404 is acceptable (metrics not implemented)
                return TestResult(
                    framework=framework.name,
                    test_name="metrics_endpoint",
                    passed=True,
                    duration_ms=duration,
                    response_data={"available": response.status_code == 200},
                )
            else:
                return TestResult(
                    framework=framework.name,
                    test_name="metrics_endpoint",
                    passed=False,
                    duration_ms=duration,
                    error_message=f"HTTP {response.status_code}",
                )
        except Exception:
            duration = (time.time() - start) * 1000
            # Metrics is optional, so timeout is acceptable
            return TestResult(
                framework=framework.name,
                test_name="metrics_endpoint",
                passed=True,  # Pass even on error since it's optional
                duration_ms=duration,
                response_data={"available": False},
            )

    def test_framework(self, framework: FrameworkConfig) -> List[TestResult]:
        """Run all tests for a framework"""
        results = []

        print(f"\n{'='*70}")
        print(f"Testing: {framework.name} (Port: {framework.port}, Type: {framework.type})")
        print(f"{'='*70}")

        # Test 1: Health check
        print("  → Testing health endpoint...")
        health_result = self.test_health(framework)
        results.append(health_result)

        if health_result.passed:
            print(f"    ✓ Health check passed ({health_result.duration_ms:.1f}ms)")
        else:
            print(f"    ✗ Health check failed: {health_result.error_message}")
            print("    → Skipping remaining tests (framework not running)")
            return results

        # Test 2: API endpoint (type-specific)
        if framework.type == "graphql":
            print("  → Testing GraphQL introspection...")
            api_result = self.test_graphql_introspection(framework)
        else:
            print("  → Testing REST endpoint...")
            api_result = self.test_rest_endpoint(framework)

        results.append(api_result)

        if api_result.passed:
            print(f"    ✓ API test passed ({api_result.duration_ms:.1f}ms)")
        else:
            print(f"    ✗ API test failed: {api_result.error_message}")

        # Test 3: Metrics endpoint
        print("  → Testing metrics endpoint...")
        metrics_result = self.test_metrics(framework)
        results.append(metrics_result)

        if metrics_result.passed:
            available = metrics_result.response_data.get("available", False)
            status = "available" if available else "not implemented (optional)"
            print(f"    ✓ Metrics check passed - {status}")
        else:
            print(f"    ⚠ Metrics endpoint error: {metrics_result.error_message}")

        return results

    def run_all_tests(self, filter_framework: Optional[str] = None, filter_type: Optional[str] = None):
        """Run tests for all frameworks"""
        print("\n" + "="*70)
        print("  FraiseQL Performance Assessment - Integration Test Suite")
        print("  Testing all frameworks for health and functionality")
        print("="*70)

        frameworks_to_test = []
        for name, framework in self.frameworks.items():
            if filter_framework and name != filter_framework:
                continue
            if filter_type and framework.type != filter_type:
                continue
            frameworks_to_test.append(framework)

        print(f"\nTesting {len(frameworks_to_test)} frameworks...")

        for framework in frameworks_to_test:
            framework_results = self.test_framework(framework)
            self.results.extend(framework_results)

        self._print_summary()
        self._save_results()

    def _print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        print("\n" + "="*70)
        print("  Test Summary")
        print("="*70)
        print(f"\n  Total Tests:    {total}")
        print(f"  ✓ Passed:       {passed}")
        print(f"  ✗ Failed:       {failed}")

        if total > 0:
            success_rate = (passed / total) * 100
            print(f"\n  Success Rate:   {success_rate:.1f}%")

        # Group by framework
        framework_summary = {}
        for result in self.results:
            if result.framework not in framework_summary:
                framework_summary[result.framework] = {"passed": 0, "failed": 0}

            if result.passed:
                framework_summary[result.framework]["passed"] += 1
            else:
                framework_summary[result.framework]["failed"] += 1

        print("\n  Framework Summary:")
        print("  " + "-"*66)
        for framework, stats in sorted(framework_summary.items()):
            total_framework = stats["passed"] + stats["failed"]
            status = "✓" if stats["failed"] == 0 else "✗"
            print(f"  {status} {framework:20} {stats['passed']:2}/{total_framework}")

        print()

    def _save_results(self):
        """Save results to JSON file"""
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"test-results-{timestamp}.json"

        results_data = {
            "timestamp": timestamp,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "tests": [
                {
                    "framework": r.framework,
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "error_message": r.error_message,
                    "response_data": r.response_data,
                }
                for r in self.results
            ],
        }

        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)

        print(f"  Results saved to: {results_file}")
        print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Integration test suite for FraiseQL Performance Assessment"
    )
    parser.add_argument(
        "--framework",
        help="Test only specified framework",
    )
    parser.add_argument(
        "--type",
        choices=["graphql", "rest"],
        help="Test only GraphQL or REST frameworks",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5)",
    )

    args = parser.parse_args()

    config_file = Path(__file__).parent / "framework-config.json"
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)

    tester = IntegrationTester(config_file, timeout=args.timeout)
    tester.run_all_tests(filter_framework=args.framework, filter_type=args.type)

    # Exit with error code if any tests failed
    failed = sum(1 for r in tester.results if not r.passed)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
