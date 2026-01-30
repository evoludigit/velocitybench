#!/usr/bin/env python3
"""
VelocityBench Performance Regression Detection

Detects performance regressions by comparing current test results against
baseline metrics using statistical analysis.

Usage:
    python detect-regressions.py --results-dir tests/perf/results --baseline stable
    python detect-regressions.py --update-baseline stable --reason "Performance stabilization"
    python detect-regressions.py --format markdown --output regression-report.md
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class RegressionMetric:
    """Individual regression metric."""

    name: str
    baseline_value: float
    current_value: float
    change_percent: float
    severity: str  # "INFO", "WARNING", "CRITICAL"
    threshold_warning: float
    threshold_critical: float
    is_regression: bool

    def __str__(self) -> str:
        direction = "↑" if self.change_percent > 0 else "↓"
        return (
            f"{self.name}: {self.baseline_value:.2f} → {self.current_value:.2f} "
            f"({direction}{abs(self.change_percent):.1f}%) [{self.severity}]"
        )


@dataclass
class RegressionReport:
    """Complete regression detection report."""

    timestamp: str
    baseline_name: str
    has_regressions: bool
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    regressions: List[RegressionMetric] = field(default_factory=list)
    framework_results: Dict[str, List[RegressionMetric]] = field(default_factory=dict)

    def add_regression(self, regression: RegressionMetric, framework: str = "global"):
        """Add a regression to the report."""
        self.regressions.append(regression)

        if framework not in self.framework_results:
            self.framework_results[framework] = []
        self.framework_results[framework].append(regression)

        # Update counts
        if regression.severity == "CRITICAL":
            self.critical_count += 1
        elif regression.severity == "WARNING":
            self.warning_count += 1
        else:
            self.info_count += 1

    def has_critical_regressions(self) -> bool:
        """Check if report contains critical regressions."""
        return self.critical_count > 0

    def has_warnings(self) -> bool:
        """Check if report contains warnings."""
        return self.warning_count > 0


class BaselineManager:
    """Manage baseline metrics storage and retrieval."""

    def __init__(self, baselines_dir: Path):
        self.baselines_dir = baselines_dir
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    def get_baseline(self, name: str) -> Optional[Dict[str, Any]]:
        """Load baseline metrics by name."""
        baseline_path = self.baselines_dir / name / "metrics.json"

        if not baseline_path.exists():
            return None

        with open(baseline_path) as f:
            return json.load(f)

    def list_baselines(self) -> List[str]:
        """List all available baseline names."""
        if not self.baselines_dir.exists():
            return []

        return [
            d.name
            for d in self.baselines_dir.iterdir()
            if d.is_dir() and (d / "metrics.json").exists()
        ]

    def save_baseline(
        self, metrics: Dict[str, Any], name: str, reason: str, git_ref: Optional[str] = None
    ) -> None:
        """Save metrics as a new baseline."""
        baseline_dir = self.baselines_dir / name
        baseline_dir.mkdir(parents=True, exist_ok=True)

        # Save metrics
        metrics_path = baseline_dir / "metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        # Save metadata
        meta = {
            "created_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "git_ref": git_ref or "unknown",
        }

        meta_path = baseline_dir / "meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        print(f"✅ Baseline '{name}' saved successfully")


class MetricsExtractor:
    """Extract metrics from JTL files and analysis results."""

    def __init__(self, results_dir: Path):
        self.results_dir = results_dir

    def extract_from_analysis_json(self, analysis_file: Path) -> Dict[str, float]:
        """Extract metrics from analysis JSON file."""
        if not analysis_file.exists():
            return {}

        with open(analysis_file) as f:
            data = json.load(f)

        metrics = {}

        # Extract response time percentiles
        if "response_times" in data:
            rt = data["response_times"]
            metrics["response_time_p50"] = rt.get("p50", 0)
            metrics["response_time_p95"] = rt.get("p95", 0)
            metrics["response_time_p99"] = rt.get("p99", 0)
            metrics["response_time_mean"] = rt.get("mean", 0)

        # Extract throughput
        if "throughput" in data:
            metrics["throughput_rps"] = data["throughput"].get("requests_per_second", 0)

        # Extract error rate
        if "errors" in data:
            metrics["error_rate_percent"] = data["errors"].get("rate_percent", 0)

        return metrics

    def aggregate_results(self, results_dir: Path) -> Dict[str, Dict[str, float]]:
        """Aggregate results from all frameworks."""
        aggregated = {}

        # Look for analysis files in results directory
        for framework_dir in results_dir.iterdir():
            if not framework_dir.is_dir():
                continue

            framework_name = framework_dir.name
            analysis_file = framework_dir / "analysis.json"

            if analysis_file.exists():
                metrics = self.extract_from_analysis_json(analysis_file)
                if metrics:
                    aggregated[framework_name] = metrics

        return aggregated


class RegressionDetector:
    """Detect regressions using statistical analysis."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get("thresholds", {})

    def detect(
        self, baseline: Dict[str, Any], current: Dict[str, Any]
    ) -> RegressionReport:
        """Detect regressions by comparing baseline and current metrics."""
        report = RegressionReport(
            timestamp=datetime.utcnow().isoformat(),
            baseline_name=baseline.get("name", "unknown"),
            has_regressions=False,
        )

        # Compare each framework
        baseline_frameworks = baseline.get("frameworks", {})
        current_frameworks = current.get("frameworks", {})

        for framework in current_frameworks:
            if framework not in baseline_frameworks:
                continue

            baseline_metrics = baseline_frameworks[framework]
            current_metrics = current_frameworks[framework]

            # Compare response time percentiles
            for percentile in ["p50", "p95", "p99"]:
                metric_name = f"response_time_{percentile}"
                if metric_name in baseline_metrics and metric_name in current_metrics:
                    regression = self._compare_metric(
                        name=f"Response Time {percentile.upper()}",
                        baseline_value=baseline_metrics[metric_name],
                        current_value=current_metrics[metric_name],
                        threshold_config=self.thresholds["response_time"][percentile],
                        higher_is_worse=True,
                    )

                    if regression:
                        report.add_regression(regression, framework)

            # Compare throughput
            if "throughput_rps" in baseline_metrics and "throughput_rps" in current_metrics:
                regression = self._compare_metric(
                    name="Throughput (RPS)",
                    baseline_value=baseline_metrics["throughput_rps"],
                    current_value=current_metrics["throughput_rps"],
                    threshold_config=self.thresholds["throughput_rps"],
                    higher_is_worse=False,
                )

                if regression:
                    report.add_regression(regression, framework)

            # Compare error rate
            if "error_rate_percent" in baseline_metrics and "error_rate_percent" in current_metrics:
                regression = self._compare_metric(
                    name="Error Rate",
                    baseline_value=baseline_metrics["error_rate_percent"],
                    current_value=current_metrics["error_rate_percent"],
                    threshold_config=self.thresholds["error_rate"],
                    higher_is_worse=True,
                )

                if regression:
                    report.add_regression(regression, framework)

        report.has_regressions = len(report.regressions) > 0
        return report

    def _compare_metric(
        self,
        name: str,
        baseline_value: float,
        current_value: float,
        threshold_config: Dict[str, float],
        higher_is_worse: bool,
    ) -> Optional[RegressionMetric]:
        """Compare a single metric and determine if it's a regression."""
        if baseline_value == 0:
            return None

        # Calculate percent change
        change_percent = ((current_value - baseline_value) / baseline_value) * 100

        # Determine if this is a regression based on direction
        if higher_is_worse:
            is_regression = change_percent > 0
        else:
            is_regression = change_percent < 0

        # Determine severity
        warning_threshold = threshold_config["warning_percent"]
        critical_threshold = threshold_config["critical_percent"]

        if not is_regression:
            severity = "INFO"
        elif abs(change_percent) >= abs(critical_threshold):
            severity = "CRITICAL"
        elif abs(change_percent) >= abs(warning_threshold):
            severity = "WARNING"
        else:
            severity = "INFO"

        # Only report if it's a warning or critical regression
        if severity in ["WARNING", "CRITICAL"]:
            return RegressionMetric(
                name=name,
                baseline_value=baseline_value,
                current_value=current_value,
                change_percent=change_percent,
                severity=severity,
                threshold_warning=warning_threshold,
                threshold_critical=critical_threshold,
                is_regression=is_regression,
            )

        return None


class AlertFormatter:
    """Format regression reports in various formats."""

    def __init__(self, colored: bool = True):
        self.colored = colored

    def format_cli(self, report: RegressionReport) -> str:
        """Format report for CLI output."""
        lines = []
        lines.append("=" * 80)
        lines.append("REGRESSION DETECTION REPORT")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {report.timestamp}")
        lines.append(f"Baseline: {report.baseline_name}")
        lines.append("")

        # Summary
        lines.append("SUMMARY:")
        lines.append(f"  Critical: {report.critical_count}")
        lines.append(f"  Warnings: {report.warning_count}")
        lines.append(f"  Info:     {report.info_count}")
        lines.append("")

        if not report.has_regressions:
            lines.append("✅ No regressions detected!")
            lines.append("=" * 80)
            return "\n".join(lines)

        # Detailed results by framework
        lines.append("REGRESSIONS BY FRAMEWORK:")
        lines.append("")

        for framework, regressions in report.framework_results.items():
            if not regressions:
                continue

            lines.append(f"  {framework}:")
            for regression in regressions:
                severity_marker = self._get_severity_marker(regression.severity)
                lines.append(f"    {severity_marker} {regression}")

            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def format_json(self, report: RegressionReport) -> str:
        """Format report as JSON."""
        data = {
            "timestamp": report.timestamp,
            "baseline": report.baseline_name,
            "has_regressions": report.has_regressions,
            "summary": {
                "critical": report.critical_count,
                "warnings": report.warning_count,
                "info": report.info_count,
            },
            "regressions": [
                {
                    "framework": framework,
                    "metric": reg.name,
                    "baseline_value": reg.baseline_value,
                    "current_value": reg.current_value,
                    "change_percent": reg.change_percent,
                    "severity": reg.severity,
                }
                for framework, regs in report.framework_results.items()
                for reg in regs
            ],
        }

        return json.dumps(data, indent=2)

    def format_markdown(self, report: RegressionReport) -> str:
        """Format report as Markdown (for PR comments)."""
        lines = []
        lines.append("# 📊 Performance Regression Report")
        lines.append("")
        lines.append(f"**Timestamp:** {report.timestamp}")
        lines.append(f"**Baseline:** `{report.baseline_name}`")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- 🔴 Critical: **{report.critical_count}**")
        lines.append(f"- ⚠️ Warnings: **{report.warning_count}**")
        lines.append(f"- ℹ️ Info: **{report.info_count}**")
        lines.append("")

        if not report.has_regressions:
            lines.append("✅ **No regressions detected!**")
            return "\n".join(lines)

        # Detailed results
        lines.append("## Regressions by Framework")
        lines.append("")

        for framework, regressions in report.framework_results.items():
            if not regressions:
                continue

            lines.append(f"### {framework}")
            lines.append("")
            lines.append("| Metric | Baseline | Current | Change | Severity |")
            lines.append("|--------|----------|---------|--------|----------|")

            for reg in regressions:
                emoji = self._get_severity_emoji(reg.severity)
                change_str = f"{reg.change_percent:+.1f}%"
                lines.append(
                    f"| {reg.name} | {reg.baseline_value:.2f} | "
                    f"{reg.current_value:.2f} | {change_str} | {emoji} {reg.severity} |"
                )

            lines.append("")

        return "\n".join(lines)

    def _get_severity_marker(self, severity: str) -> str:
        """Get CLI severity marker."""
        if severity == "CRITICAL":
            return "🔴"
        elif severity == "WARNING":
            return "⚠️ "
        else:
            return "ℹ️ "

    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        if severity == "CRITICAL":
            return "🔴"
        elif severity == "WARNING":
            return "⚠️"
        else:
            return "ℹ️"


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load regression detection configuration."""
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Detect performance regressions in VelocityBench results"
    )

    # Input options
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("tests/perf/results"),
        help="Directory containing test results",
    )

    parser.add_argument(
        "--baseline",
        type=str,
        default="stable",
        help="Baseline name to compare against",
    )

    # Baseline management
    parser.add_argument(
        "--update-baseline",
        type=str,
        help="Update baseline with current results",
    )

    parser.add_argument(
        "--reason",
        type=str,
        help="Reason for baseline update",
    )

    parser.add_argument(
        "--list-baselines",
        action="store_true",
        help="List all available baselines",
    )

    # Output options
    parser.add_argument(
        "--format",
        choices=["cli", "json", "markdown"],
        default="cli",
        help="Output format",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (in addition to critical)",
    )

    # Configuration
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".baselines/regression-config.yaml"),
        help="Configuration file path",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Initialize managers
    baselines_dir = Path(config["baselines"]["directory"])
    baseline_mgr = BaselineManager(baselines_dir)

    # List baselines
    if args.list_baselines:
        baselines = baseline_mgr.list_baselines()
        if not baselines:
            print("No baselines found")
        else:
            print("Available baselines:")
            for name in baselines:
                print(f"  - {name}")
        sys.exit(0)

    # Extract current metrics
    metrics_extractor = MetricsExtractor(args.results_dir)
    current_metrics = metrics_extractor.aggregate_results(args.results_dir)

    if not current_metrics:
        print("Error: No test results found in results directory", file=sys.stderr)
        sys.exit(1)

    # Update baseline
    if args.update_baseline:
        if not args.reason:
            print("Error: --reason required when updating baseline", file=sys.stderr)
            sys.exit(1)

        baseline_data = {"name": args.update_baseline, "frameworks": current_metrics}

        baseline_mgr.save_baseline(
            metrics=baseline_data, name=args.update_baseline, reason=args.reason
        )
        sys.exit(0)

    # Load baseline
    baseline_data = baseline_mgr.get_baseline(args.baseline)
    if not baseline_data:
        print(f"Error: Baseline '{args.baseline}' not found", file=sys.stderr)
        print(
            f"Available baselines: {', '.join(baseline_mgr.list_baselines())}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Detect regressions
    detector = RegressionDetector(config)
    current_data = {"name": "current", "frameworks": current_metrics}
    report = detector.detect(baseline_data, current_data)

    # Format report
    formatter = AlertFormatter(colored=config["reporting"]["colored_output"])

    if args.format == "cli":
        output = formatter.format_cli(report)
    elif args.format == "json":
        output = formatter.format_json(report)
    elif args.format == "markdown":
        output = formatter.format_markdown(report)
    else:
        output = formatter.format_cli(report)

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to: {args.output}")
    else:
        print(output)

    # Exit with appropriate code
    if config["ci_integration"]["fail_on_critical"] and report.has_critical_regressions():
        sys.exit(1)

    if args.strict and report.has_warnings():
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
