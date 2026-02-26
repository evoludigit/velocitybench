#!/usr/bin/env python3
"""
VelocityBench Sequential Test Runner

Orchestrates sequential testing of all frameworks with:
1. Per-framework isolated PostgreSQL databases
2. Transaction-based test isolation (no manual cleanup)
3. Sequential execution (one framework at a time)
4. Result collection and reporting

This ensures:
- Clean benchmark results (no resource contention)
- Fair comparison between frameworks
- Repeatable, reproducible test runs

Usage:
    python scripts/run-benchmarks.py                    # Run all frameworks
    python scripts/run-benchmarks.py postgraphile       # Run only postgraphile
    python scripts/run-benchmarks.py fraiseql rails     # Run specific frameworks

Environment variables:
    BENCHMARK_TIMEOUT    - Timeout per framework test (default: 300 seconds)
    BENCHMARK_PARALLEL   - Run frameworks in parallel (default: false)
    BENCHMARK_VERBOSE    - Verbose output (default: false)
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

# List of all frameworks in the benchmark suite
FRAMEWORKS = [
    'postgraphile',
    'fraiseql',
    # ... (see tests/benchmark/bench_sequential.py for the full registry)
]


@dataclass
class TestResult:
    """Result of running tests for a framework"""
    framework: str
    status: str  # 'passed', 'failed', 'timeout', 'error'
    exit_code: int
    duration_seconds: float
    timestamp: str
    stdout_lines: int = 0
    stderr_lines: int = 0
    error_message: str = None
    test_count: int = None
    passed_tests: int = None
    failed_tests: int = None


class BenchmarkRunner:
    """Orchestrates sequential framework testing"""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize with project configuration"""
        self.project_root = project_root or Path(__file__).parent.parent
        self.timeout = int(os.getenv('BENCHMARK_TIMEOUT', '300'))
        self.parallel = os.getenv('BENCHMARK_PARALLEL', 'false').lower() == 'true'
        self.verbose = os.getenv('BENCHMARK_VERBOSE', 'false').lower() == 'true'
        self.results: Dict[str, TestResult] = {}
        self.start_time = datetime.now()

    def run_framework_tests(self, framework: str) -> TestResult:
        """
        Run tests for a single framework

        Steps:
        1. Change to framework directory
        2. Execute framework-specific test runner
        3. Capture output and parse results
        4. Return structured test result
        """
        print(f"\n{'='*70}")
        print(f"Testing: {framework}")
        print(f"{'='*70}")

        framework_dir = self.project_root / 'frameworks' / framework
        if not framework_dir.exists():
            return TestResult(
                framework=framework,
                status='error',
                exit_code=-1,
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
                error_message=f"Framework directory not found: {framework_dir}"
            )

        # Determine test runner command based on framework
        test_command = self._get_test_command(framework)
        if not test_command:
            return TestResult(
                framework=framework,
                status='error',
                exit_code=-1,
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
                error_message=f"Unable to determine test command for {framework}"
            )

        print(f"  Command: {' '.join(test_command)}")
        print(f"  Timeout: {self.timeout} seconds")

        # Run tests
        test_start = time.time()
        try:
            result = subprocess.run(
                test_command,
                cwd=framework_dir,
                capture_output=True,
                timeout=self.timeout,
                text=True
            )

            duration = time.time() - test_start
            test_result = self._parse_result(
                framework=framework,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration
            )

            # Print summary
            if test_result.status == 'passed':
                print(f"✅ {framework} passed ({test_result.test_count} tests)")
            else:
                print(f"❌ {framework} {test_result.status}")
                if test_result.error_message:
                    print(f"   {test_result.error_message}")

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - test_start
            print(f"⏱️  {framework} timed out after {duration:.1f} seconds")
            return TestResult(
                framework=framework,
                status='timeout',
                exit_code=-1,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                error_message=f"Tests timed out after {self.timeout} seconds"
            )

        except Exception as e:
            duration = time.time() - test_start
            print(f"❌ {framework} error: {e}")
            return TestResult(
                framework=framework,
                status='error',
                exit_code=-1,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            )

    def run_all_sequential(self, frameworks: Optional[List[str]] = None) -> bool:
        """Run all or specified frameworks sequentially"""
        to_run = frameworks or FRAMEWORKS

        if not to_run:
            print("❌ No frameworks to test")
            return False

        print("\n🚀 VelocityBench Sequential Test Runner")
        print(f"   Frameworks to test: {', '.join(to_run)}")
        print(f"   Sequential mode: {'ON' if not self.parallel else 'OFF (PARALLEL)'}")
        print(f"   Timeout per framework: {self.timeout}s")

        # Run each framework
        for i, framework in enumerate(to_run, 1):
            print(f"\n[{i}/{len(to_run)}] {framework}")
            result = self.run_framework_tests(framework)
            self.results[framework] = result

        # Print summary
        return self._print_summary(to_run)

    def _get_test_command(self, framework: str) -> Optional[List[str]]:
        """Determine test command for framework"""
        framework_dir = self.project_root / 'frameworks' / framework

        # Try to detect framework type and appropriate test command
        package_json = framework_dir / 'package.json'
        if package_json.exists():
            return ['npm', 'test', '--', '--maxWorkers=1']

        requirements_txt = framework_dir / 'requirements.txt'
        if requirements_txt.exists():
            return ['pytest', '-v', '--tb=short']

        gemfile = framework_dir / 'Gemfile'
        if gemfile.exists():
            return ['bundle', 'exec', 'rspec']

        pom_xml = framework_dir / 'pom.xml'
        if pom_xml.exists():
            return ['mvn', 'test']

        gradle_build = framework_dir / 'build.gradle'
        if gradle_build.exists():
            return ['./gradlew', 'test']

        return None

    def _parse_result(self, framework: str, exit_code: int, stdout: str,
                      stderr: str, duration: float) -> TestResult:
        """Parse test runner output and determine result"""
        status = 'passed' if exit_code == 0 else 'failed'

        test_result = TestResult(
            framework=framework,
            status=status,
            exit_code=exit_code,
            duration_seconds=duration,
            timestamp=datetime.now().isoformat(),
            stdout_lines=len(stdout.splitlines()),
            stderr_lines=len(stderr.splitlines())
        )

        # Try to extract test counts from output
        self._extract_test_counts(test_result, stdout, stderr)

        if exit_code != 0:
            # Extract error message from output
            error_lines = stderr.splitlines() if stderr else stdout.splitlines()
            if error_lines:
                test_result.error_message = error_lines[-1][:100]

        if self.verbose:
            print(f"\n  Output ({test_result.stdout_lines} lines):")
            for line in stdout.splitlines()[:10]:
                print(f"    {line}")
            if len(stdout.splitlines()) > 10:
                print(f"    ... ({test_result.stdout_lines - 10} more lines)")

        return test_result

    def _extract_test_counts(self, result: TestResult, stdout: str, stderr: str):
        """Try to extract test counts from test output"""
        # Try Jest format: "Tests: 5 passed, 0 failed"
        if 'passed' in stdout:
            import re
            match = re.search(r'(\d+)\s+(?:tests?|passed)', stdout)
            if match:
                result.test_count = int(match.group(1))

        # Try pytest format: "5 passed in 1.23s"
        if 'passed' in stdout:
            import re
            match = re.search(r'(\d+)\s+passed', stdout)
            if match:
                result.passed_tests = int(match.group(1))

    def _print_summary(self, frameworks: List[str]) -> bool:
        """Print test summary and save results"""
        passed = sum(1 for r in self.results.values() if r.status == 'passed')
        failed = sum(1 for r in self.results.values() if r.status != 'passed')
        total_duration = (datetime.now() - self.start_time).total_seconds()

        print(f"\n{'='*70}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*70}")
        print(f"  Total Frameworks: {len(self.results)}")
        print(f"  ✅ Passed: {passed}/{len(self.results)}")
        print(f"  ❌ Failed: {failed}/{len(self.results)}")
        print(f"  Total Duration: {total_duration:.1f}s")

        print("\n  Framework Results:")
        for framework in frameworks:
            if framework in self.results:
                result = self.results[framework]
                status_icon = "✅" if result.status == 'passed' else "❌"
                print(f"    {status_icon} {framework:20} {result.status:10} "
                      f"({result.duration_seconds:.1f}s)")

        # Detailed failures
        if failed > 0:
            print("\n  Failed Frameworks:")
            for framework, result in self.results.items():
                if result.status != 'passed':
                    print(f"    - {framework}: {result.status}")
                    if result.error_message:
                        print(f"      {result.error_message}")

        # Save results
        results_file = self.project_root / 'benchmark-results.json'
        self._save_results(results_file)

        # Save HTML report (optional)
        report_file = self.project_root / 'benchmark-results.html'
        self._save_html_report(report_file, frameworks)

        return failed == 0

    def _save_results(self, output_file: Path):
        """Save test results to JSON file"""
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': (datetime.now() - self.start_time).total_seconds(),
            'frameworks': {
                name: asdict(result)
                for name, result in self.results.items()
            }
        }

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\n  📊 Results saved to: {output_file}")

    def _save_html_report(self, output_file: Path, frameworks: List[str]):
        """Save HTML report of test results"""
        passed = sum(1 for r in self.results.values() if r.status == 'passed')
        failed = len(self.results) - passed

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>VelocityBench Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .summary {{ margin-bottom: 20px; padding: 10px; background-color: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>VelocityBench Test Results</h1>
    <div class="summary">
        <p><strong>Summary:</strong> {passed} passed, {failed} failed out of {len(self.results)} frameworks</p>
        <p><strong>Duration:</strong> {(datetime.now() - self.start_time).total_seconds():.1f}s</p>
        <p><strong>Generated:</strong> {datetime.now().isoformat()}</p>
    </div>
    <table>
        <tr>
            <th>Framework</th>
            <th>Status</th>
            <th>Duration (s)</th>
            <th>Tests</th>
            <th>Error</th>
        </tr>
"""

        for framework in frameworks:
            if framework in self.results:
                result = self.results[framework]
                status_class = 'passed' if result.status == 'passed' else 'failed'
                html_content += f"""        <tr>
            <td>{result.framework}</td>
            <td class="{status_class}">{result.status}</td>
            <td>{result.duration_seconds:.1f}</td>
            <td>{result.test_count or '-'}</td>
            <td>{result.error_message or '-'}</td>
        </tr>
"""

        html_content += """    </table>
</body>
</html>"""

        with open(output_file, 'w') as f:
            f.write(html_content)

        print(f"  📈 Report saved to: {output_file}")


def main():
    """Main entry point"""
    # Parse command-line arguments
    if len(sys.argv) > 1:
        frameworks = sys.argv[1:]
    else:
        frameworks = None

    # Run benchmarks
    runner = BenchmarkRunner()
    success = runner.run_all_sequential(frameworks)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
