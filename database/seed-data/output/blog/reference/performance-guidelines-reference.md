# **[Pattern] Performance Guidelines Reference Guide**

---

## **1. Overview**
The **Performance Guidelines** pattern provides best practices, benchmarks, and actionable recommendations to optimize system performance for applications, APIs, or microservices. This pattern helps developers and architects avoid common bottlenecks, reduce latency, and ensure scalable, efficient solutions by outlining:

- **Hard limits** (absolute thresholds, e.g., "Response time ≤ 200ms").
- **Soft limits** (recommendations, e.g., "Keep database query time < 500ms in 95% of cases").
- **Monitoring rules** (alerting criteria for degradation).
- **Mitigation strategies** (refactoring, caching, load balancing).

Use this pattern when designing or troubleshooting systems prone to latency spikes, resource contention, or high cloud costs. It complements other patterns like **Caching Strategies** or **Rate Limiting** by focusing on proactive performance tuning rather than reactive fixes.

---

## **2. Schema Reference**

| **Category**          | **Field**               | **Description**                                                                                     | **Format/Example**                                                                 | **Notes**                                                                                     |
|-----------------------|-------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **System Metrics**    | Baseline Latency        | Average response time under normal load (without optimizations).                                    | `MS: 320`, `s: 0.45`                                                                   | Measure via benchmarking tools (e.g., k6, JMeter).                                             |
|                       | Throttling Point        | Load at which performance degrades (e.g., 99th percentile latency spikes).                            | `Requests/sec: 2,500`                                                                | Use **PPM (Percentage of Perfect Minutes)** to define SLOs.                                   |
|                       | Memory/CPU Footprint    | Target usage thresholds to prevent GC pauses or throttling.                                         | `CPU < 80%`, `Heap < 70%`                                                              | Monitor with Prometheus/Grafana or APM tools (e.g., New Relic).                               |
| **Soft Limits**       | Recommended DB Queries  | Max queries per second per table to avoid locks/contention.                                         | `SELECT: < 1,000/s/table`, `WRITE: < 500/s/table`                                    | Adjust based on RDBMS tuning (e.g., PostgreSQL `max_connections`).                        |
|                       | Cache Hit Ratio         | Ideal cache effectiveness (e.g., 90%+ hits for static data).                                         | `> 0.90`                                                                              | Use Redis/Memcached metrics (`keyspace_hits`, `cache_miss_ratio`).                           |
|                       | API Payload Size        | Max response size to avoid slow clients (e.g., 1MB).                                                  | `JSON: < 1,000KB`                                                                     | Compress payloads (e.g., `gzip`) if exceeding limits.                                        |
| **Hard Limits**       | Max Response Time       | Absolute timeout for critical paths (e.g., payment processing).                                      | `RPS: < 500ms`                                                                         | Enforce via circuit breakers (e.g., Hystrix, Resilience4j).                                  |
|                       | Error Budget            | Allowed failure rate before degrading service (e.g., "1% errors allowed").                            | `ERR < 1%`                                                                             | tied to SLIs (e.g., "99.9% availability").                                                  |
| **Monitoring**        | SLOs/SLIs               | Service Level Objectives/Indicators (e.g., "95% of API calls < 300ms").                               | `SLI: p99_latency < 300ms`, `SLO: 99.95%`                                               | Define in Prometheus alert rules or Datadog dashboards.                                      |
|                       | Alert Thresholds        | Triggers for alerts (e.g., "Latency > 2x baseline").                                                 | `Alert if p99 > 1.5 * baseline`                                                       | Use multi-level alerts (warn/critical).                                                     |
| **Mitigation**        | Refactoring Rules       | Code-level optimizations (e.g., "Replace N+1 queries with JOINs").                                    | `Avoid ORM lazy-loading in hot paths`                                                  | Profile with tools like `YourKit` or `async-profiler`.                                       |
|                       | Database Indexes        | Required indexes for hot queries (e.g., `WHERE status = 'active'`).                                 | `CREATE INDEX idx_status ON orders(status)`                                             | Use `EXPLAIN ANALYZE` to validate query plans.                                              |
|                       | Scaling Strategies      | Auto-scaling policies (e.g., "Scale up if CPU > 70% for 5m").                                       | `Auto-scale: CPU > 80% for 10m`                                                          | Configure in Kubernetes HPA or AWS Auto Scaling.                                            |

---

## **3. Query Examples**

### **3.1 Define Baseline Performance**
```sql
-- Measure current avg response time (PostgreSQL example)
SELECT
  avg(execution_time_ms) AS avg_response_time,
  p99(execution_time_ms) AS p99_latency
FROM (
  SELECT (end_time - start_time) * 1000 AS execution_time_ms
  FROM api_requests
  WHERE timestamp BETWEEN NOW() - INTERVAL '1h' AND NOW()
) AS latency_stats;
```

**Output:**
| `avg_response_time` | `p99_latency` |
|---------------------|---------------|
| 420ms               | 1.2s          |

---

### **3.2 Detect Performance Degradation**
**Prometheus Query (Alert Rule):**
```promql
# Alert if p99 latency exceeds 2x baseline (320ms * 2 = 640ms)
alert(HighLatency) if (
  http_request_duration_seconds{quantile="0.99"} > 640
  and on() http_request_duration_seconds{quantile="0.99"} > 0
  for 15m
)
```

**Grafana Dashboard Panel:**
Visualize `p99` latency trends with a **threshold line** at `640ms` (baseline * 2x).

---

### **3.3 Validate Cache Effectiveness**
```sql
-- Check cache hit ratio (Redis example)
SELECT
  sum(hits)::float / (hits + misses) AS hit_ratio,
  sum(hits) AS total_hits,
  sum(misses) AS total_misses
FROM (
  SELECT
    sum(key_hits) AS hits,
    sum(key_misses) AS misses
  FROM redis_keyspace_hits
)
```
**Expected Output:**
```
hit_ratio: 0.92, total_hits: 1,250,000, total_misses: 110,000
```

---

### **3.4 Optimize Database Queries**
```sql
-- Identify slow queries (PostgreSQL)
SELECT
  query,
  avg(execution_time) AS avg_time_ms,
  rows,
  execution_count
FROM pg_stat_statements
ORDER BY avg_time_ms DESC
LIMIT 10;
```

**Actionable Output:**
| `query`                          | `avg_time_ms` | `rows` | `execution_count` |
|-----------------------------------|---------------|--------|-------------------|
| `SELECT * FROM orders WHERE user_id = ?` | 850           | 50     | 1,200             |

**Fix:** Add an index on `user_id` or replace with a cached view.

---

## **4. Implementation Steps**

### **Step 1: Benchmark Under Load**
- Use tools like:
  - **k6**: `import http from 'k6/http'; export default function () { ... }`
  - **JMeter**: Simulate 1,000 RPS and record latency percentiles.
- Record **baseline metrics** (latency, throughput, errors).

### **Step 2: Set Soft/Hard Limits**
| **Component**       | **Soft Limit**               | **Hard Limit**               |
|---------------------|------------------------------|------------------------------|
| API Responses       | p95 < 400ms                  | p99 < 600ms                  |
| Database Queries    | Avg < 500ms                  | Single query < 2s            |
| Cache Hit Ratio     | > 85%                        | < 70% → trigger cache review |

### **Step 3: Implement Monitoring**
- **Prometheus Alerts**:
  ```yaml
  - alert: HighDatabaseLatency
    expr: postgres_query_latency_seconds > 1000ms
    for: 5m
    labels:
      severity: critical
  ```
- **CloudWatch SLOs (AWS)**:
  Set a **latency SLO** (e.g., "99.9% of API calls < 500ms").

### **Step 4: Optimize Hot Paths**
- **Code**:
  - Replace N+1 queries with `JOIN`s or `FETCH FIRST`.
  - Use **connection pooling** (e.g., PgBouncer for PostgreSQL).
- **Database**:
  - Add **partial indexes** for filtered queries.
  - Enable **query caching** (e.g., `SET LOCAL enable_seqscan = off;`).
- **Network**:
  - **Compress responses** (`Content-Encoding: gzip`).
  - Use **CDNs** for static assets.

### **Step 5: Scale Horizontally**
- **Auto-scaling rules**:
  ```yaml
  # Kubernetes HPA example
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  ```
- **Load balancing**:
  Distribute traffic across regions (e.g., AWS Global Accelerator).

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Caching Strategies]**   | Guides on cache invalidation, TTL policies, and multi-level caching.           | When latency is dominated by repeated database/API calls.                       |
| **[Rate Limiting]**       | Controls request volume to prevent abuse and throttling.                       | For public APIs or user-facing endpoints.                                       |
| **[Retry & Backoff]**     | Handles transient failures with exponential backoff.                          | For resilient systems (e.g., cloud storage APIs).                              |
| **[Distributed Tracing]** | Tracks requests across microservices to identify bottlenecks.                  | In polyglot architectures (e.g., .NET + Java + Python).                        |
| **[Concurrency Control]** | Manages thread pools, async/await, and lock contention.                       | CPU-bound or I/O-heavy services.                                                |
| **[Observability]**        | Centralized logging/metrics for performance debugging.                         | For SRE teams or complex distributed systems.                                   |

---
## **6. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                       | **Fix**                                                                         |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Ignoring Tail Latency**       | P99 spikes cause user-facing timeouts.                                       | Use **percentile-based SLOs** and **tail sampling**.                          |
| **Over-Caching**                | Stale data or cache stampedes.                                               | Set **short TTLs** + **cache-aside** strategy.                                |
| **No Load Testing**             | Over-optimizing for synthetic benchmarks vs. real-world traffic.              | Simulate **real user distributions** (e.g., 80% reads, 20% writes).            |
| **Hardcoding Throttles**        | Limits become obsolete without monitoring.                                     | Use **dynamic scaling** based on SLOs.                                        |

---
## **7. Tools & Libraries**
| **Category**          | **Tool/Library**               | **Use Case**                                                                 |
|-----------------------|--------------------------------|-----------------------------------------------------------------------------|
| **Load Testing**      | k6, JMeter, Gatling              | Benchmark under simulated load.                                             |
| **APM**               | New Relic, Datadog, Dynatrace    | Distributed tracing and latency breakdown.                                  |
| **Monitoring**        | Prometheus, Grafana, CloudWatch | Track SLOs and alert on degradation.                                        |
| **Caching**           | Redis, Memcached, CDN (Cloudflare)| Reduce database load.                                                       |
| **Auto-Scaling**      | Kubernetes HPA, AWS Auto Scaling | Adjust resources based on metrics.                                         |
| **Database Tuning**   | pgBadger (PostgreSQL), SlowQuery| Identify and optimize slow queries.                                        |

---
**Key Takeaway**: Performance Guidelines are **proactive**, not reactive. Start by measuring baselines, then iteratively refine limits and optimizations based on real-world data. Combine this pattern with **Observability** and **Concurrency Control** for holistic performance improvements.