# VelocityBench Benchmark Methodology

This document describes the methodology used for VelocityBench framework comparisons to ensure fair, reproducible, and meaningful results.

## Principles

1. **Fair Comparison**: All frameworks use the same database, schema, and seed data
2. **Realistic Workloads**: Based on production traffic patterns (blog/CMS application)
3. **Reproducible**: Any run should produce similar results (within 5% variance)
4. **Transparent**: All configuration, scripts, and raw data are public

---

## Test Environment

### Hardware Requirements

For reproducible results, benchmarks should run on consistent hardware:

| Component | Specification |
|-----------|---------------|
| **CPU** | 8+ cores (dedicated, no shared VMs) |
| **RAM** | 32GB minimum |
| **Storage** | SSD (NVMe preferred) |
| **Network** | All containers on same Docker network |

### Software Stack

| Component | Version | Notes |
|-----------|---------|-------|
| **PostgreSQL** | 15+ | Dedicated instance |
| **Docker** | 24+ | Resource limits configured |
| **JMeter** | 5.6+ | Headless mode |
| **Prometheus** | 2.45+ | Metrics collection |
| **Grafana** | 10+ | Visualization |

### Isolation Requirements

- **One framework at a time**: No resource contention between frameworks
- **Database warmup**: PostgreSQL caches warmed before measurement
- **Container isolation**: Each framework runs in dedicated container
- **Network**: All containers on `velocitybench_network` bridge

### Standardized Ports

All frameworks use standardized ports since benchmarks run sequentially:

| Type | Port | Notes |
|------|------|-------|
| **GraphQL** | 4000 | All GraphQL frameworks expose 4000 |
| **REST** | 8080 | All REST frameworks expose 8080 |

**Why standardized ports?**
- JMeter configuration stays simple (always targets same port)
- No port conflicts between services
- Matches production deployment patterns
- Docker Compose profiles ensure only one framework runs at a time

---

## Workload Types

VelocityBench includes 9 workload types covering different access patterns:

| Workload | Description | Real-World Analog | File |
|----------|-------------|-------------------|------|
| `simple` | Single entity fetch | Homepage load | `simple.jmx` |
| `parameterized` | Filtered queries with IDs | User profile lookup | `parameterized.jmx` |
| `pagination` | Offset/limit queries | List views | `pagination.jmx` |
| `aggregation` | COUNT, SUM, AVG operations | Dashboard stats | `aggregation.jmx` |
| `deep-traversal` | Nested relationships (3+ levels) | Detail pages | `deep-traversal.jmx` |
| `fulltext` | Text search queries | Search feature | `fulltext.jmx` |
| `mutations` | Write operations (create, update) | Form submissions | `mutations.jmx` |
| `mixed` | 70% read, 30% write | Production traffic | `mixed.jmx` |
| **`blog-page`** | **Complete page load comparison** | **Single blog post** | `blog-page.jmx` |

### Blog Page Load Workload (Flagship)

The `blog-page` workload is the **flagship benchmark** because it demonstrates the core REST vs GraphQL trade-off:

#### Scenario
User visits a blog post page needing:
- Post content (title, body, excerpt, date)
- Author info (name, bio, avatar)
- 10 comments with their authors

#### Approaches Compared

| Approach | Requests | Typical Latency | DB Queries |
|----------|----------|-----------------|------------|
| **GraphQL** | 1 | ~12-20ms | 1-3 |
| **REST (Batched)** | 3 | ~35-50ms | 3-4 |
| **REST (Naive)** | 13+ | ~100-200ms | 13+ |

---

## Load Levels

| Level | Concurrent Users | Duration | Ramp-up | Purpose |
|-------|------------------|----------|---------|---------|
| `smoke` | 1 | 30s | 0s | Verify functionality |
| `light` | 10 | 60s | 10s | Baseline performance |
| `medium` | 50 | 120s | 30s | Typical production load |
| `heavy` | 200 | 300s | 60s | Peak load testing |
| `stress` | 500 | 300s | 120s | Breaking point discovery |

### JMeter Parameters

```bash
# Example: Medium load
jmeter -n -t workloads/blog-page.jmx \
  -Jthreads=50 \
  -Jrampup=30 \
  -Jloops=100 \
  -Jgraphql_host=localhost \
  -Jgraphql_port=4000 \
  -Jrest_host=localhost \
  -Jrest_port=8080
```

---

## Warmup Protocol

Before each benchmark run:

1. **Start framework container**
   ```bash
   docker-compose up -d fraiseql
   ```

2. **Wait for health check**
   ```bash
   ./tests/perf/scripts/warmup.sh fraiseql
   ```
   - Polls `/health` until HTTP 200
   - Maximum wait: 60 seconds

3. **Warmup requests** (discarded from results)
   - Run 100 requests to `/graphql` or `/ping`
   - Ensures JIT compilation, connection pool warm

4. **Database cache warmup**
   - Run sample queries to populate PostgreSQL buffers
   - Wait 5 seconds for stability

5. **Begin measurement**

---

## Metrics Collected

### Latency Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| **p50** | Median response time | ms |
| **p95** | 95th percentile | ms |
| **p99** | 99th percentile | ms |
| **max** | Maximum response time | ms |
| **mean** | Average response time | ms |

### Throughput Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| **RPS** | Requests per second | req/s |
| **TPS** | Transactions per second (for grouped requests) | txn/s |

### Error Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Error Rate** | % of non-2xx responses | < 0.1% |
| **Timeout Rate** | % of requests exceeding timeout | < 0.01% |

### Resource Metrics (via Prometheus)

| Metric | Description | Collection |
|--------|-------------|------------|
| **CPU %** | Container CPU utilization | cAdvisor |
| **Memory MB** | Container memory usage | cAdvisor |
| **DB Connections** | Active pool connections | pg_stat |
| **GC Pauses** | Garbage collection time (where applicable) | Framework metrics |

---

## Standardized Configuration

### Connection Pooling

All frameworks must use identical pool settings:

| Setting | Value | Notes |
|---------|-------|-------|
| **Min Connections** | 10 | Pre-warmed |
| **Max Connections** | 50 | Cap for fair comparison |
| **Statement Cache** | 100 | Where supported |
| **Idle Timeout** | 300s | Return idle connections |
| **Max Lifetime** | 3600s | Refresh connections hourly |

### HTTP Settings

| Setting | Value |
|---------|-------|
| **Keep-Alive** | Enabled |
| **HTTP Version** | 1.1 |
| **Response Timeout** | 30s |
| **Connection Timeout** | 5s |

### Database

| Setting | Value |
|---------|-------|
| **Same PostgreSQL instance** | All frameworks connect to same DB |
| **Same schema** | `benchmark` schema with tb_*, v_*, tv_* |
| **Same seed data** | 10,000+ blog posts, users, comments |

---

## Test Data

### Seed Data Volume

| Entity | Count | Notes |
|--------|-------|-------|
| **Users** | 1,000+ | Realistic profiles |
| **Posts** | 10,000+ | Blog posts with varied content |
| **Comments** | 50,000+ | Threaded comments |
| **Tags** | 500+ | Post categorization |

### Test Data Files

| File | Description | Generated By |
|------|-------------|--------------|
| `post_ids.csv` | 1,000 random post IDs | `generate-post-ids.py` |
| `user_ids.csv` | 1,000 random user IDs | `generate-user-ids.py` |

Generate test data:
```bash
cd tests/perf/scripts
python generate-post-ids.py --count 1000 --output ../data/post_ids.csv
```

---

## Running Benchmarks

### Quick Start

```bash
# 1. Start infrastructure
docker-compose up -d postgres prometheus grafana

# 2. Seed database
cd database && python scripts/seed.py

# 3. Generate test data
cd tests/perf/scripts && python generate-post-ids.py

# 4. Start framework
docker-compose up -d fraiseql

# 5. Run benchmark
./tests/perf/scripts/run-benchmark.sh fraiseql blog-page medium
```

### Full Benchmark Suite

```bash
# Run all Tier 1 frameworks
make benchmark-all WORKLOAD=blog-page LOAD=medium

# Generate comparison report
make report
```

### Individual Framework

```bash
# Run specific framework
./tests/perf/scripts/run-benchmark.sh <framework> <workload> <load>

# Examples:
./tests/perf/scripts/run-benchmark.sh fraiseql blog-page medium
./tests/perf/scripts/run-benchmark.sh strawberry mixed heavy
./tests/perf/scripts/run-benchmark.sh fastapi-rest simple light
```

---

## Result Analysis

### Output Files

Each benchmark run produces:

| File | Content |
|------|---------|
| `results/<framework>/<workload>/<load>/summary.csv` | Aggregate statistics |
| `results/<framework>/<workload>/<load>/raw.jtl` | Raw JMeter results |
| `results/<framework>/<workload>/<load>/metrics.json` | Prometheus snapshot |

### Statistical Significance

For meaningful comparisons:

- **Minimum 3 runs** per configuration
- **Report median** of multiple runs (not single run)
- **Note variance** if > 5% between runs
- **Discard outlier runs** with errors > 0.1%

### Comparison Guidelines

When comparing frameworks:

1. **Same workload**: Compare `blog-page` to `blog-page`, not to `simple`
2. **Same load level**: Compare `medium` to `medium`
3. **Same measurement**: Compare p99 to p99, not p99 to mean
4. **Note caveats**: Document any configuration differences

---

## Reporting Results

### Required Information

Every benchmark report should include:

- Date and time of run
- Hardware specifications
- Software versions
- Load level and duration
- Raw data location
- Any anomalies noted

### Result Format

```markdown
## Benchmark Results - Blog Page Load (Medium Load)

**Date**: 2024-01-15
**Load**: 50 concurrent users, 120s duration

| Framework | p50 (ms) | p95 (ms) | p99 (ms) | RPS | Error % |
|-----------|----------|----------|----------|-----|---------|
| FraiseQL | 12 | 18 | 25 | 4,200 | 0.00% |
| Strawberry | 15 | 22 | 32 | 3,400 | 0.00% |
| FastAPI (batched) | 42 | 65 | 85 | 1,200 | 0.00% |
| FastAPI (naive) | 145 | 210 | 280 | 340 | 0.02% |
```

---

## Reproducibility Checklist

Before publishing results, verify:

- [ ] All frameworks using same PostgreSQL instance
- [ ] Connection pool settings match specification
- [ ] Test data freshly generated
- [ ] Warmup protocol followed
- [ ] At least 3 runs completed
- [ ] Error rate < 0.1%
- [ ] Raw data preserved
- [ ] Hardware specs documented

---

## Known Limitations

1. **Single-node testing**: Does not test distributed scenarios
2. **Synthetic workload**: Real traffic patterns may differ
3. **Hardware variance**: Results vary on different hardware
4. **Framework versions**: Results specific to tested versions

---

## Related Documentation

- [FRAMEWORKS.md](FRAMEWORKS.md) - Framework registry and status
- [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) - Latest benchmark results
- [README.md](README.md) - Project overview
