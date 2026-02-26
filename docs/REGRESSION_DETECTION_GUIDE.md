# Regression Detection Guide

VelocityBench includes automated performance regression detection to catch slowdowns before they merge to main. This guide explains the regression detection system, how to use it, and how to interpret results.

## Overview

The regression detection system compares current performance metrics against baseline metrics to identify statistically significant performance degradation.

**Key Features**:
- ✅ Statistical analysis (confidence intervals, significance testing)
- ✅ Multiple comparison correction (Bonferroni method)
- ✅ Severity classification (INFO, WARNING, CRITICAL)
- ✅ Baseline versioning and management
- ✅ Multiple output formats (CLI, JSON, Markdown)
- ✅ CI/CD integration

**Location**: `tests/perf/scripts/detect-regressions.py`

## Quick Start

```bash
# Detect regressions against stable baseline
python tests/perf/scripts/detect-regressions.py \
  --results-dir tests/perf/results \
  --baseline stable

# Update baseline after performance improvements
python tests/perf/scripts/detect-regressions.py \
  --update-baseline stable \
  --reason "Optimized database queries"

# Generate Markdown report for PR
python tests/perf/scripts/detect-regressions.py \
  --baseline stable \
  --format markdown \
  --output regression-report.md
```

## How It Works

### Architecture

The regression detector consists of four main components:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. MetricsExtractor                                         │
│    - Reads JTL files (JMeter output)                        │
│    - Parses analysis JSON (percentiles, throughput)         │
│    - Aggregates metrics across multiple test runs          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. BaselineManager                                          │
│    - Loads baseline metrics from .baselines/                │
│    - Manages baseline versions (v1.0, v1.1, ...)           │
│    - Saves new baselines with metadata                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. RegressionDetector                                       │
│    - Compares current vs baseline metrics                  │
│    - Statistical significance testing (t-test, CI)         │
│    - Severity classification (INFO/WARNING/CRITICAL)       │
│    - N+1 query pattern detection                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. AlertFormatter                                           │
│    - Formats results for CLI (colored, emoji)              │
│    - Generates JSON (for CI tooling)                       │
│    - Creates Markdown reports (for PR comments)            │
└─────────────────────────────────────────────────────────────┘
```

### Statistical Analysis

#### Confidence Intervals (95%)

The detector calculates 95% confidence intervals for each metric:

```
CI = mean ± (1.96 * std_dev / sqrt(n))
```

Where:
- `mean` = average response time across samples
- `std_dev` = standard deviation
- `n` = number of samples
- `1.96` = z-score for 95% confidence

**Example**:
- Baseline p95: 45ms ± 5ms (95% CI: 40-50ms)
- Current p95: 68ms ± 7ms (95% CI: 61-75ms)
- **Regression detected**: Current CI doesn't overlap baseline CI

#### Statistical Significance

A regression is flagged only if:

1. **Non-overlapping CIs**: Current and baseline confidence intervals don't overlap
2. **Threshold exceeded**: Change exceeds configured threshold (e.g., +15%)
3. **Bonferroni corrected**: p-value adjusted for multiple comparisons

**Bonferroni Correction**:
```
adjusted_p_value = p_value * number_of_comparisons
```

This prevents false positives when testing many metrics simultaneously.

### Threshold Levels

Configured in `.baselines/regression-config.yaml`:

```yaml
thresholds:
  response_time:
    p50:
      warning_percent: 15      # Warn if p50 increases 15%
      critical_percent: 50     # Fail if p50 increases 50%
    p95:
      warning_percent: 20      # Warn if p95 increases 20%
      critical_percent: 60     # Fail if p95 increases 60%
    p99:
      warning_percent: 25      # Warn if p99 increases 25%
      critical_percent: 80     # Fail if p99 increases 80%

  throughput_rps:
    warning_percent: -15       # Warn if throughput drops 15%
    critical_percent: -40      # Fail if throughput drops 40%

  error_rate:
    warning_percent: 5         # Warn if error rate +5 percentage points
    critical_percent: 25       # Fail if error rate +25 percentage points
```

### Severity Classification

| Severity | Condition | CI Behavior |
|----------|-----------|-------------|
| **INFO** | Change detected but below warning threshold | ℹ️ Log only, pass CI |
| **WARNING** | Change exceeds warning threshold | ⚠️ Comment on PR, pass CI |
| **CRITICAL** | Change exceeds critical threshold | ❌ Fail CI, block merge |

## Baseline Management

### Baseline Structure

Baselines are stored in `.baselines/{version}/{name}/`:

```
.baselines/
├── regression-config.yaml       # Threshold configuration
└── v1.0/                        # Version directory
    ├── stable/                  # Baseline name
    │   ├── meta.json            # Metadata (created_at, git_ref, created_by)
    │   └── metrics.json         # Aggregated metrics
    └── pre-optimization/        # Alternative baseline
        ├── meta.json
        └── metrics.json
```

### Baseline Metadata (meta.json)

```json
{
  "version": "v1.0",
  "name": "stable",
  "created_at": "2025-01-30T10:00:00Z",
  "git_ref": "b1ece02",
  "created_by": "developer@example.com",
  "reason": "Established stable baseline after initial implementation",
  "test_profile": "read-heavy",
  "frameworks_included": ["fastapi-rest", "flask-rest", "strawberry", "..."],
  "total_requests": 500000,
  "test_duration_seconds": 300
}
```

### Baseline Metrics (metrics.json)

```json
{
  "fastapi-rest": {
    "latency": {
      "p50": {"mean": 12.3, "std_dev": 1.2, "ci_lower": 11.1, "ci_upper": 13.5},
      "p90": {"mean": 25.7, "std_dev": 2.3, "ci_lower": 23.4, "ci_upper": 28.0},
      "p95": {"mean": 32.1, "std_dev": 3.1, "ci_lower": 29.0, "ci_upper": 35.2},
      "p99": {"mean": 45.6, "std_dev": 5.2, "ci_lower": 40.4, "ci_upper": 50.8}
    },
    "throughput": {
      "rps": {"mean": 3245.2, "std_dev": 123.4, "ci_lower": 3121.8, "ci_upper": 3368.6}
    },
    "error_rate": {
      "percent": {"mean": 0.02, "std_dev": 0.01, "ci_lower": 0.01, "ci_upper": 0.03}
    },
    "database": {
      "queries_per_request": {"mean": 1.2, "std_dev": 0.1}
    }
  },
  "flask-rest": { ... },
  "strawberry": { ... }
}
```

### Creating a Baseline

```bash
# Run benchmarks first
make benchmark-all

# Create baseline from results
python tests/perf/scripts/detect-regressions.py \
  --update-baseline stable \
  --reason "Initial stable baseline" \
  --results-dir tests/perf/results
```

**Output**:
```
Creating baseline 'stable' in .baselines/v1.0/stable/
- Extracted metrics from 39 frameworks
- Total requests: 1,950,000
- Test duration: 195 minutes
- Git ref: b1ece02
✅ Baseline created successfully
```

### Listing Baselines

```bash
python tests/perf/scripts/detect-regressions.py --list-baselines
```

**Output**:
```
Available baselines:

v1.0:
  - stable (created 2025-01-30, b1ece02)
    Reason: Initial stable baseline
    Frameworks: 39

  - pre-optimization (created 2025-01-25, 7b3993d)
    Reason: Before database query optimization
    Frameworks: 39
```

## Running Regression Detection

### Basic Usage

```bash
# Detect regressions vs. stable baseline
python tests/perf/scripts/detect-regressions.py \
  --results-dir tests/perf/results \
  --baseline stable
```

**Output (CLI)**:
```
================================================================
        Performance Regression Detection Report
================================================================

Baseline: stable (v1.0)
Created: 2025-01-30T10:00:00Z
Git ref: b1ece02

Current results: tests/perf/results
Test duration: 5 minutes
Total requests: 150,000

================================================================
REGRESSIONS DETECTED
================================================================

❌ CRITICAL: fastapi-rest - p95 latency
  Baseline: 32.1ms (95% CI: 29.0-35.2ms)
  Current:  52.3ms (95% CI: 48.1-56.5ms)
  Change:   +62.9% (threshold: 60%)
  Impact:   Users will experience slower response times

⚠️  WARNING: strawberry - throughput
  Baseline: 1245 RPS (95% CI: 1180-1310 RPS)
  Current:  1050 RPS (95% CI: 995-1105 RPS)
  Change:   -15.7% (threshold: -15%)
  Impact:   Lower request handling capacity

ℹ️  INFO: flask-rest - p50 latency
  Baseline: 15.2ms (95% CI: 14.0-16.4ms)
  Current:  16.8ms (95% CI: 15.5-18.1ms)
  Change:   +10.5% (below warning threshold)

================================================================
SUMMARY
================================================================

Total frameworks tested: 39
Regressions found:
  - CRITICAL: 1
  - WARNING: 1
  - INFO: 1

✅ Pass: 36 frameworks
❌ FAILED: Blocking regressions detected

Exit code: 1 (CI should fail)
```

### JSON Output

For CI/CD tooling integration:

```bash
python tests/perf/scripts/detect-regressions.py \
  --baseline stable \
  --format json \
  --output regression-report.json
```

**Output (regression-report.json)**:
```json
{
  "baseline": {
    "name": "stable",
    "version": "v1.0",
    "created_at": "2025-01-30T10:00:00Z",
    "git_ref": "b1ece02"
  },
  "test_info": {
    "results_dir": "tests/perf/results",
    "duration_seconds": 300,
    "total_requests": 150000
  },
  "regressions": [
    {
      "framework": "fastapi-rest",
      "metric": "p95_latency",
      "severity": "CRITICAL",
      "baseline_value": 32.1,
      "current_value": 52.3,
      "change_percent": 62.9,
      "threshold_percent": 60,
      "confidence_interval": {
        "baseline": [29.0, 35.2],
        "current": [48.1, 56.5]
      },
      "statistically_significant": true
    }
  ],
  "summary": {
    "total_frameworks": 39,
    "regressions_critical": 1,
    "regressions_warning": 1,
    "regressions_info": 1,
    "passed": 36,
    "failed": true
  },
  "exit_code": 1
}
```

### Markdown Output

For GitHub PR comments:

```bash
python tests/perf/scripts/detect-regressions.py \
  --baseline stable \
  --format markdown \
  --output regression-report.md
```

**Output (regression-report.md)**:
```markdown
## 📊 Performance Regression Report

**Baseline**: `stable` (v1.0, b1ece02)
**Test Duration**: 5 minutes
**Total Requests**: 150,000

---

### ❌ Critical Regressions (1)

#### fastapi-rest - p95 latency

| Metric | Baseline | Current | Change | Threshold |
|--------|----------|---------|--------|-----------|
| **p95 latency** | 32.1ms | 52.3ms | **+62.9%** | 60% |

**Impact**: Users will experience slower response times at 95th percentile.

**Confidence Intervals**:
- Baseline: 29.0ms - 35.2ms (95% CI)
- Current: 48.1ms - 56.5ms (95% CI)

**Recommendation**: Investigate and fix before merging.

---

### ⚠️ Warnings (1)

#### strawberry - throughput

| Metric | Baseline | Current | Change | Threshold |
|--------|----------|---------|--------|-----------|
| **Throughput (RPS)** | 1245 | 1050 | **-15.7%** | -15% |

**Impact**: Lower request handling capacity.

---

### Summary

| Status | Count |
|--------|-------|
| ✅ Passed | 36 |
| ⚠️ Warnings | 1 |
| ❌ Critical | 1 |

**Result**: ❌ **FAILED** - Blocking regressions detected
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/regression-detection.yml
name: Performance Regression Detection

on:
  pull_request:
    branches: [main]

jobs:
  detect-regressions:
    runs-on: [self-hosted, benchmark]  # Dedicated benchmark machine
    steps:
      - uses: actions/checkout@v3

      - name: Run benchmarks
        run: |
          make benchmark-all

      - name: Detect regressions
        id: detect
        run: |
          python tests/perf/scripts/detect-regressions.py \
            --results-dir tests/perf/results \
            --baseline stable \
            --format json \
            --output regression-report.json
        continue-on-error: true  # Don't fail yet, we want to comment

      - name: Generate Markdown report
        if: always()
        run: |
          python tests/perf/scripts/detect-regressions.py \
            --results-dir tests/perf/results \
            --baseline stable \
            --format markdown \
            --output regression-report.md

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('regression-report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });

      - name: Fail if critical regressions
        if: steps.detect.outcome == 'failure'
        run: |
          echo "❌ Critical performance regressions detected!"
          cat regression-report.md
          exit 1
```

### Strict Mode

Fail on warnings (not just critical):

```bash
python tests/perf/scripts/detect-regressions.py \
  --baseline stable \
  --strict
```

## N+1 Query Detection

The regression detector includes N+1 query pattern detection:

```python
def _detect_n1_pattern(framework, metrics):
    """Detect N+1 query patterns."""
    queries_per_request = metrics["database"]["queries_per_request"]["mean"]

    # Expected: O(1) queries (1-3 queries via JOINs)
    # N+1: O(N) queries (1 + N queries per item)

    if queries_per_request > 10:
        return {
            "severity": "CRITICAL",
            "message": f"N+1 query detected: {queries_per_request:.1f} queries per request",
            "recommendation": "Use DataLoaders or JOIN queries"
        }
    elif queries_per_request > 5:
        return {
            "severity": "WARNING",
            "message": f"High query count: {queries_per_request:.1f} queries per request"
        }
    return None
```

## Best Practices

1. **Establish baseline early**: Create stable baseline after initial implementation
2. **Update baseline carefully**: Only update after verified performance improvements
3. **Run on dedicated hardware**: Use same machine for baseline and current tests
4. **Document baseline changes**: Always provide reason when updating baseline
5. **Review warnings**: Don't ignore warnings, investigate and fix or justify
6. **Use strict mode for critical paths**: Enable strict mode for performance-critical code
7. **Automate in CI**: Run regression detection on every PR

## Troubleshooting

### Issue: All frameworks flagged as regressions

**Cause**: Results from different machine or configuration

**Solution**: Ensure tests run on same machine with same configuration as baseline

### Issue: High variability in results

**Cause**: Noisy test environment (other processes running)

**Solution**: Run on dedicated machine, disable background processes

### Issue: Baseline not found

**Cause**: Baseline name or version incorrect

**Solution**: List baselines to verify name: `--list-baselines`

### Issue: Metrics extraction failed

**Cause**: JTL files corrupted or missing

**Solution**: Re-run benchmarks to generate fresh JTL files

## References

- [ADR-010: Benchmarking Methodology](adr/010-benchmarking-methodology.md)
- [Statistical Significance Testing](https://en.wikipedia.org/wiki/Statistical_significance)
- [Bonferroni Correction](https://en.wikipedia.org/wiki/Bonferroni_correction)
- [Confidence Intervals](https://en.wikipedia.org/wiki/Confidence_interval)
- [Performance Testing Best Practices](https://www.brendangregg.com/methodology.html)
