# Cost Simulation Engine for VelocityBench

A comprehensive system for analyzing and comparing the running costs of different web frameworks across multiple cloud providers.

## Overview

The Cost Simulation Engine answers critical questions for framework selection:

1. **"How much will it cost to run this framework in production?"**
   - Monthly infrastructure cost (compute, database, storage)
   - Yearly cost with reserved instance discounts
   - Multi-cloud comparison (AWS, GCP, Azure)

2. **"What infrastructure is needed for a given load?"**
   - CPU cores required (with 30% headroom)
   - RAM needed (with buffers)
   - Storage needed (application + data + backups)
   - Recommended instance type

3. **"Which framework is most cost-efficient?"**
   - Cost per request ($/request)
   - Efficiency score (0-10)
   - Framework ranking
   - ROI analysis

## Quick Start

### Installation

```bash
# Cost simulation is part of VelocityBench
cd /home/lionel/code/velocitybench
python -m pytest costs/tests/ -v  # Run tests to verify
```

### Basic Usage

```python
from costs.load_profiler import LoadProfiler, LoadProfile
from costs.resource_calculator import ResourceCalculator
from costs.cost_config import CostConfiguration

# 1. Project load from benchmark RPS
profiler = LoadProfiler()
projection = profiler.project_from_jmeter(rps=125.3)

# 2. Calculate infrastructure requirements
calc = ResourceCalculator()
requirements = calc.calculate_requirements(projection)

print(f"CPU cores: {requirements.cpu_cores}")
print(f"Memory: {requirements.memory_gb:.1f} GB")
print(f"Storage: {requirements.storage_gb:.1f} GB")

# 3. Look up cloud provider pricing
config = CostConfiguration()
instances = config.get_compute_instances_for_cores(min_cores=requirements.cpu_cores)
best_instance = instances[0]  # Cheapest option
print(f"Best AWS instance: {best_instance.instance_id} at ${best_instance.aws_hourly:.4f}/hour")
```

## Architecture

### Phase 1: Core Engine (✅ Complete)

**Modules**:
- `cost_config.py` (268 lines): Cloud provider pricing configuration
- `load_profiler.py` (311 lines): JMeter RPS → production load projection
- `resource_calculator.py` (301 lines): Load → infrastructure requirements
- `exceptions.py` (28 lines): Custom exception types

**Status**: 45/45 tests passing ✅

### Phase 2: Calculation Engine (Coming Soon)

**Modules**:
- `cost_calculator.py`: Cloud cost calculations (compute, database, storage, transfer)
- `efficiency_analyzer.py`: Efficiency metrics and framework ranking

### Phase 3: Reporting (Coming Soon)

**Modules**:
- `result_builder.py`: JSON, HTML, CSV report generation
- `integration.py`: Pipeline orchestration with run-benchmarks.py

### Phase 4: Grafana Dashboard (Coming Soon)

- Cost comparison visualization
- Efficiency rankings
- Cost trends over time

## Module Details

### cost_config.py
Manages cloud provider pricing for AWS, GCP, and Azure.

```python
from costs.cost_config import CostConfiguration

config = CostConfiguration()

# Get instance pricing
instance = config.get_instance("aws_m5_xlarge")
print(f"Hourly cost: ${instance.aws_hourly}")
print(f"1-year reserved: ${instance.aws_1yr_reserved}")

# Find instances matching requirements
instances = config.get_compute_instances_for_cores(min_cores=4)
```

### load_profiler.py
Projects production load from JMeter benchmark metrics.

```python
from costs.load_profiler import LoadProfiler, LoadProfile

profiler = LoadProfiler()

# From actual benchmark results
projection = profiler.project_from_jmeter(rps=125.3)
print(f"Monthly volume: {projection.requests_per_month:,.0f}")
print(f"Peak RPS: {projection.rps_peak:.1f}")

# Or from predefined profiles
projection = profiler.profile_from_load_profile(LoadProfile.SMALL)
```

### resource_calculator.py
Calculates infrastructure requirements based on load.

```python
from costs.resource_calculator import ResourceCalculator

calc = ResourceCalculator()
requirements = calc.calculate_requirements(projection)

# Get human-readable description
desc = calc.get_resource_profile_description(requirements)
print(f"CPU: {desc['cpu']['description']}")
print(f"Memory: {desc['memory']['description']}")
```

## Testing

Run all tests:
```bash
python -m pytest costs/tests/ -v
```

Run specific test module:
```bash
python -m pytest costs/tests/test_cost_config.py -v
```

Run with coverage:
```bash
python -m pytest costs/tests/ --cov=costs --cov-report=html
```

## Load Profiles

Predefined load profiles for different testing scenarios:

| Profile | RPS | Use Case | Deployment |
|---------|-----|----------|------------|
| SMOKE | 10 | Sanity testing | Development |
| SMALL | 50 | Light load | Testing/Staging |
| MEDIUM | 500 | Moderate load | Staging |
| LARGE | 5,000 | Heavy load | Pre-production |
| PRODUCTION | 10,000 | Full capacity | Production |

## Key Formulas

### Load Projection
```
Daily volume = RPS × 86,400 seconds/day
Monthly volume = Daily volume × 30 days
Peak RPS = Average RPS × 2.5
```

### Resource Calculation
```
CPU cores = ceil(Peak RPS / RPS_per_core × 1.30)
Memory GB = (baseline + pool_size × mem_per_conn) × 1.20 / 1024
Storage GB = (data + logs + backups) × compression_ratio × replication_factor
```

### Cost Estimation (Phase 2)
```
Monthly cost = (instance_hourly × 730 hours) + database + storage + transfer + monitoring
Yearly cost = monthly_cost × 12 × escalation_factor
Reserved cost = monthly_cost × 12 × discount_factor (40% 1-year, 55% 3-year)
```

## Configuration

### Default Values

**ResourceCalculator defaults**:
- RPS per core: 100 (typical web framework)
- Application memory: 256 MB
- Connection pool size: 50
- Memory per connection: 5 MB
- Application storage: 1 GB

**LoadProfiler defaults**:
- Peak multiplier: 2.5x (industry standard)
- Data growth: 0.0001 GB per request
- Log growth: 0.00005 GB per request
- Compression ratio: 0.9 (10% reduction)
- Replication factor: 2.0 (for redundancy)

### Customization

Override defaults when creating instances:

```python
from costs.resource_calculator import ResourceCalculator

calc = ResourceCalculator(
    rps_per_core=150,  # Your framework can do 150 RPS/core
    app_memory_mb=512,  # More memory intensive
    conn_pool_size=100,
)
```

## Cloud Providers

### Supported Clouds
- **AWS**: EC2, RDS, EBS, S3
- **GCP**: Compute Engine, Cloud SQL, Persistent Disks, Cloud Storage
- **Azure**: VMs, Database for PostgreSQL, Managed Disks, Blob Storage

### Pricing Updates

Pricing data is version-controlled in `cost_config.py`. Update quarterly:

1. Check official cloud provider pricing
2. Update hourly rates in `CostConfiguration._load_default_pricing()`
3. Commit with message: `chore(costs): Update cloud provider pricing - {date}`

## Integration with VelocityBench

### Current Integration Points (Phase 2)
- Input: JMeter results from `tests/perf/results/*/results.jtl`
- Input: Framework config from `tests/integration/framework-config.json`
- Output: Cost analysis to `tests/perf/results/{framework}/cost-analysis.json`

### Future Integration (Phase 3)
- Hook into `scripts/run-benchmarks.py`
- Grafana dashboard at `monitoring/grafana/`
- CLI tool at `costs/cli.py`

## Development

See `DEVELOPMENT.md` for setup, testing, and contribution guidelines.

See `PHASE_1_SUMMARY.md` for detailed implementation status.

## License

Part of VelocityBench. See root LICENSE file.

---

## Status

**Phase 1** (Core Engine): ✅ Complete
- 45/45 tests passing
- 909 lines of production code
- Ready for Phase 2

**Phase 2** (Calculation): Coming soon
**Phase 3** (Reporting): Coming soon
**Phase 4** (Dashboard): Coming soon
