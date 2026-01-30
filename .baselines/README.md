# VelocityBench Performance Baselines

This directory contains baseline metrics for regression detection.

## Directory Structure

```
.baselines/
├── regression-config.yaml     # Configuration for regression detection
├── stable/                    # Stable baseline (default)
│   ├── meta.json             # Metadata (created_at, reason, git_ref)
│   └── metrics.json          # Performance metrics
├── v1.0/                     # Version-specific baseline
│   ├── meta.json
│   └── metrics.json
└── experimental/             # Experimental baseline
    ├── meta.json
    └── metrics.json
```

## Baseline Structure

### meta.json

Contains metadata about when and why the baseline was created:

```json
{
  "created_at": "2025-01-30T12:00:00.000000",
  "reason": "Initial stable baseline",
  "git_ref": "main"
}
```

### metrics.json

Contains performance metrics for all frameworks:

```json
{
  "name": "stable",
  "frameworks": {
    "fastapi-rest": {
      "response_time_p50": 12.5,
      "response_time_p95": 45.2,
      "response_time_p99": 78.3,
      "response_time_mean": 18.7,
      "throughput_rps": 850.2,
      "error_rate_percent": 0.1
    },
    "flask-rest": {
      "response_time_p50": 15.3,
      "response_time_p95": 52.1,
      "response_time_p99": 89.4,
      "response_time_mean": 21.2,
      "throughput_rps": 720.5,
      "error_rate_percent": 0.2
    }
  }
}
```

## Usage

### List Available Baselines

```bash
python tests/perf/scripts/detect-regressions.py --list-baselines
```

### Create a New Baseline

```bash
python tests/perf/scripts/detect-regressions.py \
  --results-dir tests/perf/results \
  --update-baseline stable \
  --reason "Performance stabilization after optimization"
```

### Detect Regressions

Compare current results against stable baseline:

```bash
python tests/perf/scripts/detect-regressions.py \
  --results-dir tests/perf/results \
  --baseline stable
```

Generate markdown report:

```bash
python tests/perf/scripts/detect-regressions.py \
  --results-dir tests/perf/results \
  --baseline stable \
  --format markdown \
  --output regression-report.md
```

Strict mode (fail on warnings):

```bash
python tests/perf/scripts/detect-regressions.py \
  --results-dir tests/perf/results \
  --baseline stable \
  --strict
```

## Baseline Management Best Practices

### When to Create a Baseline

- **Initial Setup**: Create `stable` baseline after initial performance testing
- **After Optimization**: Create new baseline after significant performance improvements
- **Version Releases**: Create version-specific baselines (e.g., `v1.0`, `v2.0`)
- **Before Major Changes**: Create baseline before architectural changes

### Baseline Naming Conventions

- `stable` - Current stable baseline (default)
- `v{major}.{minor}` - Version-specific baselines (e.g., `v1.0`, `v2.1`)
- `experimental` - Experimental/development baseline
- `pre-{feature}` - Before major feature implementation
- `post-{feature}` - After major feature implementation

### Baseline Retention

- Keep at least 3-5 historical baselines
- Archive old baselines to `.baselines/archive/`
- Document significant changes in meta.json `reason` field

## Configuration

Edit `.baselines/regression-config.yaml` to customize:

- Threshold percentages (warning/critical)
- Statistical analysis settings
- CI/CD integration behavior
- Report formatting options

See `regression-config.yaml` for detailed configuration options.
