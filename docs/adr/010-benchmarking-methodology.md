# ADR-010: Performance Benchmarking Methodology

**Status**: Accepted
**Date**: 2025-01-30
**Author**: VelocityBench Team

## Context

VelocityBench's primary goal is to provide fair, reproducible performance comparisons across 39 frameworks in 8 languages. Performance benchmarking is notoriously difficult to do correctly:

1. **Variability**: Network latency, OS scheduling, garbage collection cause measurement noise
2. **Warmup**: JIT compilers, connection pools, caches need time to stabilize
3. **Tool Selection**: Many load testing tools available (JMeter, k6, wrk, ab, Gatling)
4. **Metrics**: Which metrics matter? (throughput, latency, percentiles, error rate)
5. **Test Profiles**: Real-world workloads vary (read-heavy, write-heavy, mixed)
6. **Regression Detection**: How to know if a change made things slower?

Poor methodology leads to misleading results that don't reflect real-world performance.

## Decision

**Use Apache JMeter with standardized test profiles, warm-up cycles, and statistical regression detection.**

### Load Testing Tool: Apache JMeter

**Why JMeter**:
- ✅ Industry standard (20+ years, battle-tested)
- ✅ Comprehensive reporting (percentiles, throughput, error rates)
- ✅ Plugin ecosystem (GraphQL support, advanced reporting)
- ✅ JTL output format (easy to parse for regression detection)
- ✅ GUI and CLI modes (development + CI/CD)
- ✅ Thread pool simulation (realistic concurrent users)

**Installation**:
```bash
# JMeter 5.6.3
brew install jmeter  # macOS
apt install jmeter   # Ubuntu
```

### Test Profiles

VelocityBench defines 5 test profiles matching real-world usage patterns:

#### Profile 1: Read-Heavy (80/20)

**Workload**: 80% reads, 20% writes
**Use Case**: Blog, news site, social media feed
**Queries**:
- 40% `GET /users/:id` (user profile view)
- 30% `GET /posts?limit=20` (post feed)
- 10% `GET /posts/:id/comments` (post detail + comments)
- 15% `POST /comments` (create comment)
- 5% `PUT /posts/:id` (update post)

**JMeter File**: `tests/perf/profiles/read-heavy.jmx`

#### Profile 2: Write-Heavy (40/60)

**Workload**: 40% reads, 60% writes
**Use Case**: Data entry system, logging application
**Queries**:
- 20% `GET /users/:id`
- 20% `GET /posts?limit=10`
- 30% `POST /posts` (create post)
- 25% `POST /comments` (create comment)
- 5% `DELETE /comments/:id` (delete comment)

**JMeter File**: `tests/perf/profiles/write-heavy.jmx`

#### Profile 3: GraphQL Complex

**Workload**: Nested GraphQL queries
**Use Case**: Rich web application with complex data requirements
**Queries**:
```graphql
# 40% - User profile with posts
query UserWithPosts {
  user(id: $id) {
    id
    name
    posts(limit: 10) {
      id
      title
      commentCount
    }
  }
}

# 30% - Post with comments and authors
query PostDetail {
  post(id: $id) {
    id
    title
    content
    author { id, name }
    comments(limit: 20) {
      id
      content
      author { id, name }
    }
  }
}

# 20% - Feed query (multiple posts)
query Feed {
  posts(limit: 20) {
    id
    title
    author { name }
    commentCount
  }
}

# 10% - Mutations
mutation CreateComment {
  createComment(input: { postId: $postId, content: $content }) {
    id
    content
  }
}
```

**JMeter File**: `tests/perf/profiles/graphql-complex.jmx`

#### Profile 4: REST Simple

**Workload**: Simple REST queries (no joins)
**Use Case**: Microservice, simple CRUD API
**Queries**:
- 50% `GET /users`
- 30% `GET /users/:id`
- 10% `POST /users`
- 10% `PUT /users/:id`

**JMeter File**: `tests/perf/profiles/rest-simple.jmx`

#### Profile 5: Stress Test

**Workload**: Gradual ramp-up to find breaking point
**Use Case**: Capacity planning, finding resource limits
**Pattern**:
- Start: 10 users
- Ramp up: +50 users every 30 seconds
- Max: 1000 users
- Duration: 10 minutes

**JMeter File**: `tests/perf/profiles/stress.jmx`

### Benchmarking Protocol

#### Phase 1: Warmup (2 minutes)

**Goal**: Stabilize JIT compilation, connection pools, caches

```bash
# Run light load to warm up
jmeter -n \
  -t tests/perf/profiles/read-heavy.jmx \
  -Jusers=10 \
  -Jduration=120 \
  -Jhost=localhost \
  -Jport=8000
```

**Why 2 minutes**:
- JVM JIT: Optimizations kick in after ~30-60 seconds
- Connection pools: Fill to steady state
- OS caches: Buffer cache warms up

#### Phase 2: Measurement (5 minutes)

**Goal**: Collect stable performance metrics

```bash
# Run actual benchmark
jmeter -n \
  -t tests/perf/profiles/read-heavy.jmx \
  -Jusers=100 \
  -Jduration=300 \
  -Jhost=localhost \
  -Jport=8000 \
  -l results/fastapi-rest-read-heavy.jtl
```

**Output**: JTL file with per-request timing data

#### Phase 3: Analysis

**Goal**: Extract percentiles, throughput, error rates

```bash
# Generate report
jmeter -g results/fastapi-rest-read-heavy.jtl \
  -o results/fastapi-rest-read-heavy-report/

# Extract metrics
python tests/perf/scripts/extract-metrics.py \
  results/fastapi-rest-read-heavy.jtl \
  > results/fastapi-rest-metrics.json
```

**Metrics Extracted**:
- **Latency**: p50, p90, p95, p99, p99.9 (milliseconds)
- **Throughput**: Requests per second (RPS)
- **Error Rate**: % of failed requests
- **Bandwidth**: MB/sec transferred
- **Concurrency**: Active connections

### Key Metrics

#### Primary Metrics (P0)

1. **p95 Latency** - 95th percentile response time
   - Why: Represents "typical worst case" user experience
   - Target: < 100ms for simple queries, < 500ms for complex

2. **Throughput (RPS)** - Requests per second
   - Why: Measures scalability and resource efficiency
   - Target: > 1000 RPS for REST, > 500 RPS for GraphQL

3. **Error Rate** - Percentage of failed requests
   - Why: Reliability under load
   - Target: < 0.1% (1 in 1000)

#### Secondary Metrics (P1)

4. **p50 Latency** - Median response time (typical case)
5. **p99 Latency** - 99th percentile (worst 1% of requests)
6. **Memory Usage** - Peak RAM consumption
7. **CPU Utilization** - % CPU used during benchmark

#### Tertiary Metrics (P2)

8. **Connection Pool Utilization** - % of pool used
9. **Database Query Count** - # of queries per request (N+1 detection)
10. **Bandwidth** - Network throughput (MB/sec)

### Test Environment Consistency

**Infrastructure**:
- **Machine**: Dedicated EC2 instance (m5.2xlarge: 8 vCPU, 32 GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **PostgreSQL**: 15.5 (shared instance, isolated databases per framework)
- **Network**: Localhost (eliminate network variability)
- **Load**: No other processes running during benchmark

**Database State**:
- **Data Size**: 10,000 users, 100,000 posts, 1,000,000 comments (consistent across all tests)
- **Seed**: Deterministic seed (same data every run)
- **Reset**: Database reset between framework benchmarks

**Framework Configuration**:
- **Workers**: 4 (match vCPU count / 2)
- **Connection Pool**: 50 connections max
- **Logging**: Disabled during benchmarks (to avoid I/O overhead)
- **Debug Mode**: Disabled

### Regression Detection

**Algorithm**: Statistical comparison against baseline metrics

**Threshold Levels**:
```yaml
thresholds:
  p95_latency:
    warning: +15%    # Alert if 15% slower
    critical: +50%   # Fail CI if 50% slower
  throughput_rps:
    warning: -15%    # Alert if 15% lower throughput
    critical: -40%   # Fail CI if 40% lower
  error_rate:
    warning: +5%     # Alert if error rate increases 5 percentage points
    critical: +25%   # Fail if 25 percentage points higher
```

**Implementation**: See ADR-012 and `tests/perf/scripts/detect-regressions.py`

## Consequences

### Positive

✅ **Reproducible**: Standardized profiles ensure consistent testing
✅ **Industry Standard**: JMeter is widely recognized and trusted
✅ **Comprehensive**: 5 profiles cover diverse real-world workloads
✅ **Fair**: All frameworks tested under identical conditions
✅ **Automated**: CI/CD integration for continuous benchmarking
✅ **Statistical**: Regression detection prevents performance degradation
✅ **Warmup**: Eliminates cold-start bias in results

### Negative

❌ **Complex Setup**: JMeter configuration has learning curve
❌ **Long Runtime**: 7 minutes per framework × 39 frameworks = 4.5 hours for full suite
❌ **Resource Intensive**: Requires dedicated machine for consistent results
❌ **JMeter Overhead**: JMeter itself consumes CPU/memory (mitigated by running on separate machine)
❌ **Not Real Users**: Simulated load doesn't capture all real-world patterns

## Alternatives Considered

### Alternative 1: k6 (Modern JavaScript-Based)

- **Pros**: Modern, scriptable in JS, cloud-native, better GraphQL support
- **Cons**: Less mature than JMeter, smaller ecosystem, steeper learning curve
- **Rejected**: JMeter's maturity and ecosystem outweigh k6's modernness

### Alternative 2: wrk (C-Based, High Performance)

- **Pros**: Extremely fast, low overhead, simple
- **Cons**: No GUI, limited reporting, hard to configure complex scenarios
- **Rejected**: Too limited for diverse test profiles

### Alternative 3: Gatling (Scala-Based)

- **Pros**: Modern, great reporting, code-as-configuration
- **Cons**: Requires Scala knowledge, smaller community than JMeter
- **Rejected**: Scala requirement adds barrier to contribution

### Alternative 4: Apache Bench (ab)

- **Pros**: Simple, fast, widely available
- **Cons**: No percentiles, no complex scenarios, deprecated
- **Rejected**: Too simplistic for realistic benchmarking

### Alternative 5: Custom Load Tester

- **Pros**: Perfect fit for our use case, no external dependencies
- **Cons**: Development + maintenance burden, not trusted by community
- **Rejected**: Reinventing the wheel, trust issues

## Related Decisions

- **ADR-009**: Six-Dimensional QA Testing - QA validation precedes performance benchmarking
- **ADR-002**: Framework Isolation - Each framework gets dedicated database for fair testing
- **Regression Detection** (Phase 5): Statistical analysis of benchmark results

## Implementation Status

✅ **Complete** - JMeter profiles, scripts, and CI integration operational

## Running Benchmarks Locally

```bash
# Full benchmark suite (all profiles, all frameworks)
make benchmark-all

# Single framework, single profile
make benchmark FRAMEWORK=fastapi-rest PROFILE=read-heavy

# With regression detection
make benchmark-and-detect FRAMEWORK=fastapi-rest
```

## CI Integration

```yaml
# .github/workflows/benchmark.yml
benchmark:
  runs-on: [self-hosted, benchmark]  # Dedicated machine
  steps:
    - name: Warmup
      run: make benchmark-warmup FRAMEWORK=${{ matrix.framework }}

    - name: Run benchmark
      run: make benchmark FRAMEWORK=${{ matrix.framework }} PROFILE=read-heavy

    - name: Detect regressions
      run: python tests/perf/scripts/detect-regressions.py \
        --results-dir results/ \
        --baseline stable \
        --framework ${{ matrix.framework }}
```

## References

- [Apache JMeter](https://jmeter.apache.org/) - Official documentation
- [JMeter Best Practices](https://jmeter.apache.org/usermanual/best-practices.html)
- [How NOT to Measure Latency](https://www.youtube.com/watch?v=lJ8ydIuPFeU) - Gil Tene's talk on measurement accuracy
- [Coordinated Omission](https://www.scylladb.com/glossary/coordinated-omission/) - Common benchmarking pitfall
- [TechEmpower Benchmarks](https://www.techempower.com/benchmarks/) - Similar methodology
