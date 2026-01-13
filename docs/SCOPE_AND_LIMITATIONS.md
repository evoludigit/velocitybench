# VelocityBench Scope and Limitations

**Document Version**: 1.0
**Date**: 2026-01-08
**Status**: Phase 9 - Foundation

---

## Executive Summary

VelocityBench provides comprehensive performance benchmarking across 28 GraphQL and REST frameworks in 8 programming languages. This document defines exactly what is measured, what is not measured, and how to interpret the results.

**Key Principle**: VelocityBench measures framework performance under controlled conditions on a single machine. Results reflect synthetic workloads and do not represent real-world application performance.

---

## What We Test ✅

### Performance Metrics

1. **Throughput (Requests Per Second - RPS)**
   - Requests processed per second at various concurrency levels (1, 10, 50, 100, 500)
   - Includes both successful requests and errors
   - Measured at 95th, 99th percentiles under sustained load

2. **Latency (Response Time)**
   - Minimum, mean, median (p50), p95, p99, p99.9 latencies
   - End-to-end timing from request start to response end
   - Includes network roundtrip time (negligible on localhost)

3. **Resource Usage**
   - CPU utilization (user + system time, averaged across cores)
   - Memory consumption (RSS - resident set size)
   - I/O operations per request
   - Garbage collection pause times (where applicable)

4. **Warm vs Cold Performance**
   - Cold start: Time to first request response
   - Warm performance: Steady-state metrics after warmup period
   - Connection pooling and caching effects

5. **Query Complexity Scenarios**
   - Simple queries (small response payload)
   - Complex nested queries (larger response payload)
   - Real-world query patterns

### Framework Coverage

- **28 frameworks** tested across 8 languages:
  - Python: Strawberry, Graphene, FastAPI, Flask
  - TypeScript/Node.js: Apollo Server, Express.js, PostGraphile
  - Go: gqlgen, gin, graphql-go
  - Java: Spring Boot
  - Rust: Async-graphql, Actix-web
  - PHP: Laravel (Lighthouse)
  - Ruby: Rails (GraphQL)
  - C#: .NET Core
  - Managed: Hasura

### Test Types

1. **Unit Tests** (80%+ coverage target)
   - Resolver/handler logic
   - Input validation
   - Error handling
   - Type safety

2. **Integration Tests**
   - Framework + database integration
   - Connection pooling
   - Transaction handling
   - Schema execution

3. **Performance Tests**
   - Throughput measurement (JMeter/custom)
   - Latency distribution (percentiles)
   - Resource monitoring (Prometheus)
   - Sustained load testing

### Test Scenarios

- **Standard Dataset**: PostgreSQL with ~100K rows across 5 tables
- **Workload Patterns**:
  - Simple read queries
  - Complex nested queries
  - Mutation operations
  - Batch operations
  - Concurrent requests

---

## What We Do NOT Test ❌

### Network and Infrastructure

- **Network latency**: All tests run on localhost (no network delay)
- **Distributed systems**: Single machine only
- **Network failures**: No packet loss, timeouts, or degradation
- **High-latency backends**: Database/cache on same machine

### Production Scenarios

- **Long-running stability**: Tests run for minutes, not hours/days
- **Memory leaks**: Detected only over short periods
- **Connection limits**: Not tested with thousands of connections
- **Recovery from failures**: Graceful degradation not tested

### Business Logic

- **Authentication/Authorization**: Not tested
- **Complex business rules**: Synthetic workloads only
- **Custom middleware**: Not tested
- **Real data patterns**: Synthetic data only
- **Concurrency issues**: Not tested

### Security

- **SQL injection prevention**: Not tested
- **XSS protection**: Not tested
- **Authentication bypass**: Not tested
- **Data privacy compliance**: Not tested

### Application Layer

- **Third-party integrations**: Not tested
- **Custom business logic**: Not tested
- **Caching strategies**: Default configs only
- **Database optimization**: Standard configurations
- **ORM performance**: Using default settings

### Operational Concerns

- **Deployment complexity**: Not measured
- **Monitoring overhead**: Not included in metrics
- **Logging overhead**: Can affect performance significantly
- **Development velocity**: Not measured
- **Team familiarity**: Not considered
- **Ecosystem maturity**: Not evaluated

---

## Test Environment Specifications

### Hardware

- **CPU**: Single machine (specifications in test run metadata)
- **Memory**: Sufficient for all frameworks + database
- **Storage**: Local SSD (not network storage)
- **Network**: Localhost only (zero network latency)

### Software

- **Operating System**: Linux
- **Database**: PostgreSQL 14+
- **Language Versions**:
  - Python 3.10+
  - Node.js 18+
  - Go 1.21+
  - Java 17+
  - Rust 1.70+
  - PHP 8.1+
  - Ruby 3.0+
  - C# .NET 6+

### Isolation

- Each framework runs in isolated container
- Dedicated database connections
- No cross-framework interference
- Fresh database state for each test run

---

## How to Interpret Results

### Comparing Frameworks

✅ **Valid Comparisons**:
- "Framework A has 10% higher throughput than Framework B"
- "Framework A uses 20% less memory than Framework B"
- "Framework A has better p99 latency than Framework B"
- "Framework A scales better from 1 to 100 concurrent connections"

❌ **Invalid Conclusions**:
- "Framework A is 10% faster than B in production" (not guaranteed)
- "Framework A will handle 100K RPS" (extrapolation beyond test results)
- "Framework A is the best choice for my application" (depends on many factors)
- "Framework A has better memory management" (GC behavior may vary in production)

### Context Factors

Before choosing a framework based on VelocityBench results, consider:

1. **Your Workload Pattern**
   - Does your query pattern match our test scenarios?
   - Is throughput the bottleneck, or latency?
   - What concurrency level is realistic?

2. **Your Infrastructure**
   - These tests run on a single machine
   - Your application may be distributed
   - Network latency will affect results differently

3. **Your Team**
   - Developer experience with the language/framework
   - Time to production (VelocityBench measures runtime performance only)
   - Operational complexity (not measured)
   - Available libraries and ecosystem

4. **Your Constraints**
   - Language requirements
   - Deployment environment
   - Monitoring and observability needs
   - Maintenance and support availability

### Variability and Significance

- **Differences < 5%**: Likely noise, not significant
- **Differences 5-10%**: May be significant, verify with your workload
- **Differences > 10%**: Likely significant, consider other factors
- **Outliers**: Look at percentile distribution, not just means

---

## Methodology

### Test Execution

1. **Framework Startup**: Fresh process for each test run
2. **Warmup Phase**: 1000 requests before measurement (JIT compilation, connection pooling)
3. **Measurement Phase**: Sustained load for 60 seconds
4. **Concurrency Levels**: 1, 10, 50, 100, 500 concurrent connections
5. **Cooldown**: 30 seconds between tests

### Metric Collection

- **Throughput**: Counted from start to finish of load test
- **Latency**: Measured end-to-end including network stack
- **Resources**: Sampled every 100ms during test
- **Percentiles**: Using standard percentile calculation (not interpolated)

### Verification

- Multiple runs for each test (minimum 3 runs)
- Consistent results across runs indicate reliability
- Outliers excluded if > 2 standard deviations
- Results normalized for hardware/environment differences

---

## Known Limitations

### Framework-Specific

- **ORM Performance**: Using default configurations, not optimized
- **Query Optimization**: No query plan analysis or optimization
- **Caching**: Testing default cache settings only
- **Middleware**: Minimal middleware, custom middleware not tested

### Measurement

- **JIT Warmup**: First run may not represent steady state
- **Garbage Collection**: GC pause times not isolated
- **Context Switching**: Not isolated from other processes
- **CPU Frequency Scaling**: Not controlled

### Generalization

- Results specific to tested query patterns
- Synthetic data may not match real data distributions
- Single machine limitations apply
- Specific PostgreSQL configuration used

---

## Reproducibility

All tests are designed to be reproducible:

1. **Infrastructure as Code**: Docker Compose for all frameworks
2. **Seed Data**: Deterministic database population
3. **Test Plans**: JMeter plans or equivalent configs
4. **Environment**: Full specification in results metadata
5. **Source Code**: All framework implementations included

To reproduce results:
```bash
# Same hardware/OS
docker-compose up -d
make test-all
make benchmark-all
```

---

## Data Quality Assurance

### Before Publishing Results

- [ ] All frameworks operational and responding correctly
- [ ] Integration tests passing (100% success rate)
- [ ] No errors during measurement phase
- [ ] Consistent results across multiple runs
- [ ] No outliers > 2 standard deviations
- [ ] Resource usage within expected ranges

### Result Verification

- [ ] Database integrity verified post-test
- [ ] Response validation (correct query results)
- [ ] Concurrent operation integrity
- [ ] Transaction rollback verification
- [ ] Connection cleanup verification

---

## Using VelocityBench Responsibly

### Do

✅ Use for understanding relative performance trends
✅ Use for identifying framework strengths/weaknesses
✅ Benchmark YOUR workload with VelocityBench code as template
✅ Compare frameworks under identical conditions
✅ Look at multiple metrics, not just throughput

### Don't

❌ Claim results represent production performance
❌ Extrapolate beyond tested scenarios
❌ Use as sole basis for framework selection
❌ Ignore other important factors (ecosystem, team experience)
❌ Compare with results from different test environments

---

## Questions and Feedback

If you have questions about:

- **Scope**: What is/isn't tested?
- **Methodology**: How are tests run?
- **Interpretation**: What do results mean?
- **Reproduction**: How to verify results?

See [docs/](docs/) for detailed documentation or file an issue on GitHub.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-08 | Initial Phase 9 scope definition |

---

## Related Documents

- [TESTING_STANDARDS.md](TESTING_STANDARDS.md) - How tests are written
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to add new frameworks
- [docs/](docs/) - Detailed framework documentation
- [phase-plans/](phase-plans/) - Implementation timeline
