# VelocityBench Performance Baseline Guide

This guide explains how to establish, maintain, and compare against performance baselines in VelocityBench.

## Overview

A **baseline** is a recorded set of performance metrics (throughput, latency, memory, etc.) for all frameworks at a specific point in time. Baselines enable:

- **Regression detection** - Identify when changes degrade performance
- **Trend analysis** - Track performance improvements over time
- **Comparative benchmarking** - Compare frameworks against each other
- **Optimization targeting** - Focus efforts on bottlenecks
- **Release readiness** - Ensure performance standards met

---

## Establishing a Baseline

### 1. Prerequisites

```bash
# Ensure Docker is running and PostgreSQL is started
docker-compose up -d postgres

# Wait for database to be healthy
docker exec postgres pg_isready -U postgres

# Start all frameworks
docker-compose up -d

# Wait ~30 seconds for all services to be ready
sleep 30
```

### 2. Verify Framework Health

Before running benchmarks, verify all frameworks are responsive:

```bash
# Run smoke tests
./tests/integration/smoke-test.sh

# Expected output:
# ✅ Framework name                  http://localhost:port (status: 200)
```

All frameworks should return **status: 200** or **status: 000** if not running.

### 3. Generate Baseline

```bash
# Run full performance suite
make perf

# Or with specific configuration
make perf PROFILE=default DURATION=300

# Expected output:
# Running performance benchmarks...
# Generated: tests/perf/results/baseline-YYYY-MM-DD-HHmmss.json
```

**Time required**: 20-45 minutes depending on profile

### 4. Review Results

```bash
# View baseline summary
python scripts/analyze-baseline.py tests/perf/results/baseline-YYYY-MM-DD-HHmmss.json

# Or check raw JSON
cat tests/perf/results/baseline-YYYY-MM-DD-HHmmss.json | python -m json.tool
```

Expected output includes:
```json
{
  "metadata": {
    "timestamp": "2026-01-31T12:00:00Z",
    "duration_seconds": 1200,
    "frameworks_count": 38,
    "queries_per_framework": 1000
  },
  "frameworks": {
    "fastapi-rest": {
      "throughput": {
        "mean": 8500,
        "std_dev": 250,
        "min": 7950,
        "max": 9100
      },
      "latency_ms": {
        "p50": 11.2,
        "p95": 18.5,
        "p99": 25.3
      },
      "memory_mb": 85,
      "error_rate": 0.0
    }
    ...
  }
}
```

### 5. Commit Baseline

Once satisfied with results:

```bash
# Copy to baseline location
cp tests/perf/results/baseline-YYYY-MM-DD-HHmmss.json tests/perf/results/baseline.json

# Commit to git
git add tests/perf/results/baseline.json
git commit -m "perf: Establish new performance baseline

Framework performance measured on $(date +%Y-%m-%d):
- All frameworks healthy and responsive
- Baseline captured across all 38 implementations
- Results: tests/perf/results/baseline.json

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Comparing Against Baseline

### 1. Run Current Performance Test

After code changes, run performance benchmarks again:

```bash
# Run benchmarks with same configuration as baseline
make perf PROFILE=default

# Results saved to: tests/perf/results/comparison-YYYY-MM-DD-HHmmss.json
```

### 2. Compare Against Baseline

```bash
# Show differences from baseline
python scripts/compare-baseline.py \
  tests/perf/results/baseline.json \
  tests/perf/results/comparison-YYYY-MM-DD-HHmmss.json

# Example output:
# FastAPI REST:
#   Throughput:  8500 → 8350 (Δ -1.8%) ⚠️  REGRESSION
#   Latency P50: 11.2ms → 11.5ms (Δ +2.7%)
#   Memory:      85MB → 86MB (Δ +1.2%)
#
# Flask REST:
#   Throughput:  5200 → 5250 (Δ +0.96%) ✅ IMPROVEMENT
#   Latency P50: 19.2ms → 18.8ms (Δ -2.1%)
#   Memory:      90MB → 89MB (Δ -1.1%)
```

### 3. Interpret Results

**Throughput (req/sec)**
- ✅ Good: ≥ -5% regression (normal variation)
- ⚠️ Warning: 5-15% regression (investigate)
- ❌ Critical: > 15% regression (block merge)

**Latency (p99, milliseconds)**
- ✅ Good: ≤ +10% regression
- ⚠️ Warning: 10-25% regression
- ❌ Critical: > 25% regression

**Memory (MB)**
- ✅ Good: ≤ +5% increase
- ⚠️ Warning: 5-15% increase
- ❌ Critical: > 15% increase

### 4. Investigate Regressions

If regression detected:

```bash
# 1. Review recent code changes
git log --oneline -10

# 2. Check which files changed
git diff HEAD~1 HEAD

# 3. Profile the specific framework
cd frameworks/fastapi-rest
python -m cProfile -s cumtime src/app.py | head -50

# 4. Check for common issues:
# - New database queries?
# - Removed connection pooling?
# - Synchronous code in async path?
# - Missing indexes?
# - Increased memory allocation?

# 5. Fix and re-benchmark
make perf
```

---

## Baseline Maintenance

### Update Frequency

Update your baseline when:

- **Weekly**: Regular development (recommended)
- **Before release**: Ensure release quality
- **After optimization**: Record improvements
- **After dependency update**: Capture side effects
- **After database schema change**: Reflect new structure

```bash
# Weekly baseline update schedule
# Add to cron (runs every Monday at 2 AM)
0 2 * * 1 cd /home/user/velocitybench && make perf && \
  cp tests/perf/results/baseline-*.json tests/perf/results/baseline.json && \
  git add tests/perf/results/baseline.json && \
  git commit -m "perf: Update weekly baseline"
```

### Version Baseline with Releases

Tag baselines with releases:

```bash
# Before releasing v0.3.0
make perf
cp tests/perf/results/baseline-*.json tests/perf/results/baseline-v0.3.0.json

# Commit both current and versioned
git add tests/perf/results/baseline.json tests/perf/results/baseline-v0.3.0.json
git commit -m "perf: Baseline for v0.3.0 release"
git tag -a v0.3.0 -m "Release v0.3.0 with performance baseline"
```

### Archive Old Baselines

Keep history of baselines:

```bash
# Create archive directory
mkdir -p tests/perf/results/archived

# Move old baselines
mv tests/perf/results/baseline-*.json tests/perf/results/archived/

# Keep only current baseline active
# Archived baselines available for historical comparison
```

---

## Baseline Configuration Profiles

Different benchmark profiles for different scenarios:

### Profile: Default
- **Duration**: 5 minutes per framework
- **Concurrency**: 100 concurrent requests
- **Query mix**: 60% simple, 40% complex
- **Use case**: CI/CD validation
- **Time**: ~30 minutes total

```bash
make perf PROFILE=default
```

### Profile: Extended
- **Duration**: 15 minutes per framework
- **Concurrency**: 200 concurrent requests
- **Query mix**: 40% simple, 60% complex
- **Use case**: Weekly baseline updates
- **Time**: ~90 minutes total

```bash
make perf PROFILE=extended
```

### Profile: Stress Test
- **Duration**: 30 minutes per framework
- **Concurrency**: 500 concurrent requests
- **Query mix**: 20% simple, 80% complex
- **Use case**: Stability testing
- **Time**: ~3 hours total

```bash
make perf PROFILE=stress
```

### Profile: Quick Check
- **Duration**: 1 minute per framework
- **Concurrency**: 50 concurrent requests
- **Query mix**: 80% simple, 20% complex
- **Use case**: Quick validation
- **Time**: ~10 minutes total

```bash
make perf PROFILE=quick
```

---

## Baseline Storage and Structure

Baselines are stored in `tests/perf/results/`:

```
tests/perf/results/
├── baseline.json                    # Current active baseline
├── baseline-v0.2.0.json            # Release 0.2.0 baseline
├── baseline-v0.1.0.json            # Release 0.1.0 baseline
├── comparison-2026-01-31-120000.json # Latest comparison run
├── archived/
│   ├── baseline-2026-01-24.json
│   ├── baseline-2026-01-17.json
│   └── ...
└── README.md                        # This documentation
```

### Baseline File Format

```json
{
  "metadata": {
    "timestamp": "2026-01-31T12:00:00Z",
    "version": "0.2.0",
    "profile": "default",
    "duration_seconds": 1200,
    "frameworks_count": 38,
    "queries_per_framework": 1000,
    "environment": {
      "os": "linux-ubuntu-22.04",
      "python_version": "3.12.1",
      "node_version": "18.19.0",
      "docker_version": "24.0.0"
    }
  },
  "frameworks": {
    "fastapi-rest": {
      "type": "rest",
      "language": "python",
      "throughput": {
        "mean": 8500,
        "std_dev": 250,
        "min": 7950,
        "max": 9100,
        "unit": "req/sec"
      },
      "latency_ms": {
        "p50": 11.2,
        "p95": 18.5,
        "p99": 25.3,
        "max": 45.2,
        "unit": "milliseconds"
      },
      "memory_mb": 85,
      "cpu_percent": 42.5,
      "error_rate": 0.0,
      "connection_pool_size": 20,
      "uptime_seconds": 1200
    }
    ...
  },
  "summary": {
    "frameworks_tested": 38,
    "frameworks_passed": 36,
    "frameworks_failed": 2,
    "fastest_framework": {
      "name": "actix-web-rest",
      "throughput": 12500
    },
    "slowest_framework": {
      "name": "django",
      "throughput": 5100
    },
    "highest_memory": {
      "name": "spring-boot",
      "memory_mb": 210
    },
    "lowest_memory": {
      "name": "gin-rest",
      "memory_mb": 25
    }
  }
}
```

---

## Automated Baseline Comparisons in CI/CD

GitHub Actions automatically compares against baseline on PR:

```yaml
# See .github/workflows/performance-regression.yml
# Automatically runs on all PRs to main
# Comments on PR with regression analysis
```

### PR Comment Example

```
## 📊 Performance Regression Check

✅ **FastAPI**: No regression (Δ -0.5%)
⚠️ **Flask**: Minor regression (Δ -4.2%)
✅ **Strawberry**: Improved (Δ +2.1%)
❌ **Django**: Significant regression (Δ -18.5%)

⚠️ **1 regression detected** - Review changes before merge

**Action Items**:
- [ ] Review Django performance impact
- [ ] Run profiling: `python -m cProfile ...`
- [ ] Check for N+1 queries
- [ ] Verify indexes on new tables
```

---

## Troubleshooting

### Baseline Results Seem Off

**Issue**: Results vary significantly between runs

**Solution**:
1. Ensure no other processes running: `ps aux | grep python`
2. Stop all frameworks: `docker-compose down`
3. Wait 30 seconds for system to cool
4. Run baseline again
5. Results should be consistent within ±5%

### Database Not Seeded

**Issue**: "Database not found" errors during benchmark

**Solution**:
```bash
# Seed database
docker exec postgres psql -U postgres -d velocitybench \
  -f /home/lionel/code/velocitybench/database/schema.sql

# Verify
docker exec postgres psql -U postgres -d velocitybench \
  -c "SELECT COUNT(*) FROM users;"
```

### Memory Limits on CI

**Issue**: Baseline fails on CI due to memory constraints

**Solution**:
Use "Quick" profile on CI, full profile on dedicated machine:

```yaml
# In GitHub Actions
- name: Run performance check
  run: make perf PROFILE=quick
```

### Comparing Different Architectures

**Issue**: ARM baseline vs x86 baseline are different

**Solution**:
Keep separate baselines:
```bash
cp tests/perf/results/baseline.json \
   tests/perf/results/baseline-arm64.json
```

---

## Best Practices

1. **Establish baseline before major changes**
   - Establishes known-good state
   - Enables easy regression detection

2. **Compare before merging PRs**
   - Catch regressions early
   - Prevent performance degradation in main branch

3. **Document deviations**
   - If regression is expected, document why
   - Add comment to PR explaining trade-offs

4. **Review quarterly**
   - Check trends over time
   - Identify patterns in performance
   - Plan optimizations

5. **Version baselines with releases**
   - Track performance per release
   - Enable comparison across versions
   - Useful for release notes

6. **Keep environment consistent**
   - Same hardware when possible
   - Same OS/container setup
   - Same database seed data

---

## Scripts and Tools

### analyze-baseline.py

```bash
python scripts/analyze-baseline.py [baseline-file]

# Example
python scripts/analyze-baseline.py tests/perf/results/baseline.json

# Output
# FastAPI REST:      8500 req/sec, 11.2ms p50, 85MB memory
# Flask REST:        5200 req/sec, 19.2ms p50, 90MB memory
# ...
```

### compare-baseline.py

```bash
python scripts/compare-baseline.py [baseline1] [baseline2]

# Example
python scripts/compare-baseline.py \
  tests/perf/results/baseline.json \
  tests/perf/results/comparison-latest.json
```

### generate-report.py

```bash
python scripts/generate-report.py [baseline-file] --format html

# Outputs HTML report for sharing
# outputs/performance-report.html
```

---

## Resources

- **Detailed Setup**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **Testing Standards**: [TESTING_STANDARDS.md](../TESTING_STANDARDS.md)
- **Regression Detection**: [REGRESSION_DETECTION_GUIDE.md](REGRESSION_DETECTION_GUIDE.md)
- **Performance Analysis**: [docs/PERFORMANCE_ANALYSIS.md](PERFORMANCE_ANALYSIS.md)

---

**Last Updated**: 2026-01-31
**Maintainers**: VelocityBench Core Team

Questions? See [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue.
