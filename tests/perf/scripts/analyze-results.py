#!/usr/bin/env python3
"""
Statistical Analysis Script for JMeter Results
Calculates comprehensive statistics with confidence intervals and percentile distributions
"""

import sys
import json
import csv
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
    print("Warning: numpy not available - using basic statistics")

try:
    from scipy import stats as scipy_stats

    HAS_SCIPY = True
except ImportError:
    scipy_stats = None
    HAS_SCIPY = False
    print("Warning: scipy not available - confidence intervals disabled")


class JMeterStatisticsAnalyzer:
    def __init__(self):
        self.confidence_level = 0.95  # 95% confidence intervals

    def parse_jtl_file(self, jtl_file: str) -> List[Dict[str, Any]]:
        """Parse JMeter JTL results file"""
        results = []

        try:
            with open(jtl_file, "r", encoding="utf-8") as f:
                # Skip header if present
                first_line = f.readline().strip()
                if not first_line.replace(",", "").replace('"', "").isdigit():
                    # Header line, skip it
                    pass
                else:
                    # No header, process first line
                    results.append(self._parse_jtl_line(first_line))

                # Process remaining lines
                for line in f:
                    line = line.strip()
                    if line:
                        result = self._parse_jtl_line(line)
                        if result:
                            results.append(result)

        except FileNotFoundError:
            print(f"Error: JTL file not found: {jtl_file}")
            return []
        except Exception as e:
            print(f"Error parsing JTL file: {e}")
            return []

        return results

    def _parse_jtl_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single JTL line"""
        try:
            # JTL format: timestamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,grpThreads,allThreads,URL,Latency,IdleTime,Connect
            parts = line.split(",")
            if len(parts) < 15:
                return None

            return {
                "timestamp": int(parts[0]),
                "elapsed": int(parts[1]),  # Response time in ms
                "label": parts[2],
                "response_code": parts[3],
                "success": parts[7].lower() == "true",
                "bytes": int(parts[9]) if parts[9].isdigit() else 0,
                "latency": int(parts[13])
                if len(parts) > 13 and parts[13].isdigit()
                else 0,
                "connect_time": int(parts[15])
                if len(parts) > 15 and parts[15].isdigit()
                else 0,
            }
        except (ValueError, IndexError):
            return None

    def calculate_statistics(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate comprehensive statistics with confidence intervals"""
        if not response_times:
            return {}

        # Basic statistics using statistics module
        stats_dict = {
            "count": len(response_times),
            "mean": statistics.mean(response_times),
            "std": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "min": min(response_times),
            "max": max(response_times),
            "median": statistics.median(response_times),
        }

        # Percentiles using sorted data
        sorted_times = sorted(response_times)

        def percentile(p):
            k = (len(sorted_times) - 1) * (p / 100)
            f = int(k)
            c = k - f
            if f + 1 < len(sorted_times):
                return sorted_times[f] + c * (sorted_times[f + 1] - sorted_times[f])
            else:
                return sorted_times[f]

        # Standard percentiles
        for p in [50, 75, 90, 95, 99, 99.9]:
            stats_dict[f"p{p}"] = percentile(p)

        # Additional percentiles for detailed analysis
        for p in [25, 80, 85, 96, 97, 98, 99.5, 99.99]:
            stats_dict[f"p{p}"] = percentile(p)

        # Confidence interval for mean (simplified calculation)
        if len(response_times) > 1 and HAS_SCIPY and HAS_NUMPY and scipy_stats and np:
            try:
                data = np.array(response_times)
                ci = scipy_stats.t.interval(
                    self.confidence_level,
                    len(data) - 1,
                    loc=np.mean(data),
                    scale=scipy_stats.sem(data),
                )
                stats_dict["ci_95_lower"] = float(ci[0])
                stats_dict["ci_95_upper"] = float(ci[1])
                stats_dict["ci_95_width"] = float(ci[1] - ci[0])
            except (ValueError, TypeError):
                pass

        # Fallback confidence interval calculation
        if "ci_95_lower" not in stats_dict and len(response_times) > 1:
            # Simple approximation using standard error
            se = stats_dict["std"] / (len(response_times) ** 0.5)
            t_value = 1.96  # Approximation for 95% CI with large samples
            margin = t_value * se
            stats_dict["ci_95_lower"] = stats_dict["mean"] - margin
            stats_dict["ci_95_upper"] = stats_dict["mean"] + margin
            stats_dict["ci_95_width"] = 2 * margin

        # Skewness and kurtosis (simplified calculation if numpy available)
        if HAS_NUMPY and HAS_SCIPY and np and scipy_stats:
            try:
                data = np.array(response_times)
                stats_dict["skewness"] = float(scipy_stats.skew(data))
                stats_dict["kurtosis"] = float(scipy_stats.kurtosis(data))
            except (ValueError, TypeError):
                stats_dict["skewness"] = 0.0
                stats_dict["kurtosis"] = 0.0
        else:
            stats_dict["skewness"] = 0.0
            stats_dict["kurtosis"] = 0.0

        # Coefficient of variation
        if stats_dict["mean"] > 0:
            stats_dict["cv"] = stats_dict["std"] / stats_dict["mean"]
        else:
            stats_dict["cv"] = 0.0

        # Quartiles
        stats_dict["q1"] = percentile(25)
        stats_dict["q3"] = percentile(75)
        stats_dict["iqr"] = stats_dict["q3"] - stats_dict["q1"]

        # Validate statistical results
        if not self._validate_statistics(stats_dict):
            print("⚠️  Warning: Statistical results may be unreliable")

        return stats_dict

    def _validate_statistics(self, stats: Dict[str, float]) -> bool:
        """Validate statistical results for reasonableness"""
        # Check for basic validity
        if stats.get("count", 0) <= 0:
            return False

        # Check that percentiles are ordered correctly
        p50 = stats.get("p50", 0)
        p95 = stats.get("p95", 0)
        p99 = stats.get("p99", 0)

        if not (p50 <= p95 <= p99):
            print(f"⚠️  Percentile ordering issue: p50={p50}, p95={p95}, p99={p99}")
            return False

        # Check that mean is reasonable (not too far from median)
        mean = stats.get("mean", 0)
        median = stats.get("median", 0)
        if abs(mean - median) > 10 * median:  # More than 10x difference
            print(f"⚠️  Mean ({mean}) significantly different from median ({median})")
            return False

        # Check for reasonable standard deviation
        std = stats.get("std", 0)
        if std < 0 or std > 100 * mean:  # Std dev shouldn't be negative or > 100x mean
            print(f"⚠️  Unusual standard deviation: {std}")
            return False

        return True

    def calculate_throughput_stats(
        self, timestamps: List[int], total_duration_sec: float
    ) -> Dict[str, float]:
        """Calculate throughput statistics"""
        if not timestamps:
            return {}

        # Sort timestamps
        sorted_times = sorted(timestamps)

        # Calculate requests per second over time
        start_time = sorted_times[0] / 1000  # Convert to seconds
        end_time = sorted_times[-1] / 1000
        duration = end_time - start_time

        if duration > 0:
            throughput_rps = len(sorted_times) / duration
        else:
            throughput_rps = 0

        return {
            "throughput_rps": throughput_rps,
            "total_duration_sec": total_duration_sec,
            "total_requests": len(sorted_times),
        }

    def analyze_jtl_file(self, jtl_file: str) -> Dict[str, Any]:
        """Comprehensive analysis of JMeter JTL file"""
        print(f"📊 Analyzing {jtl_file}...")

        # Parse results
        results = self.parse_jtl_file(jtl_file)
        if not results:
            return {"error": "No valid results found"}

        # Extract successful response times
        successful_times = [r["elapsed"] for r in results if r["success"]]

        if not successful_times:
            return {"error": "No successful requests found"}

        # Calculate statistics
        stats = self.calculate_statistics(successful_times)

        # Extract timestamps for throughput analysis
        timestamps = [r["timestamp"] for r in results if r["success"]]
        total_duration = (max(timestamps) - min(timestamps)) / 1000 if timestamps else 0

        throughput_stats = self.calculate_throughput_stats(timestamps, total_duration)

        # Overall success rate
        total_requests = len(results)
        successful_requests = len(successful_times)
        success_rate = (
            successful_requests / total_requests * 100 if total_requests > 0 else 0
        )

        # Error analysis
        errors = [r for r in results if not r["success"]]
        error_codes = {}
        for error in errors:
            code = error.get("response_code", "unknown")
            error_codes[code] = error_codes.get(code, 0) + 1

        # Latency analysis
        latencies = [r.get("latency", 0) for r in results if r["success"]]
        latency_stats = self.calculate_statistics(latencies) if latencies else {}

        return {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "error_count": len(errors),
                "test_duration_sec": total_duration,
                **throughput_stats,
            },
            "response_time_stats": stats,
            "latency_stats": latency_stats,
            "error_breakdown": error_codes,
            "raw_data_points": len(successful_times),
        }

    def save_analysis(self, analysis: Dict[str, Any], output_file: str):
        """Save analysis results to JSON file"""
        try:
            with open(output_file, "w") as f:
                json.dump(analysis, f, indent=2, default=str)
            print(f"✅ Analysis saved to {output_file}")
        except Exception as e:
            print(f"❌ Failed to save analysis: {e}")


def main():
    parser = argparse.ArgumentParser(description="JMeter Results Statistical Analysis")
    parser.add_argument("jtl_file", help="JMeter JTL results file")
    parser.add_argument(
        "-o", "--output", help="Output JSON file (default: analysis.json)"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="Confidence level for intervals (default: 0.95)",
    )

    args = parser.parse_args()

    analyzer = JMeterStatisticsAnalyzer()
    analyzer.confidence_level = args.confidence

    # Analyze the JTL file
    analysis = analyzer.analyze_jtl_file(args.jtl_file)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        jtl_path = Path(args.jtl_file)
        output_file = str(jtl_path.parent / f"{jtl_path.stem}_analysis.json")

    # Save analysis
    analyzer.save_analysis(analysis, output_file)

    # Print summary
    if "error" not in analysis:
        summary = analysis["summary"]
        stats = analysis["response_time_stats"]

        print("\n📈 ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        print(f"Throughput: {summary['throughput_rps']:.2f} req/sec")
        print()
        print("Response Time Statistics (ms):")
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")
        print(
            f"95% Confidence Interval: [{stats.get('ci_95_lower', 'N/A'):.2f}, {stats.get('ci_95_upper', 'N/A'):.2f}]"
        )


if __name__ == "__main__":
    main()
