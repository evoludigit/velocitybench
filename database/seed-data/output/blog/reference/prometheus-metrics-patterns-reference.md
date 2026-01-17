---
# **[Pattern] Prometheus Metrics Patterns: Reference Guide**

---

## **Overview**
The **Prometheus Metrics Patterns** guide outlines best practices for exposing and querying metrics in **FraiseQL** and Prometheus ecosystems. This pattern ensures **actionable monitoring** by exposing **15+ Prometheus-compatible metrics**—including **query latency histograms, mutation counters, cache hit rates, database operation counts, and error rates**—while maintaining **optimal label cardinality** for efficient Prometheus storage and alerting.

FraiseQL’s metrics follow **Prometheus conventions** (e.g., `_sum`, `_count`, `_max` suffixes) and include **synthetic labels** (e.g., `env`, `service`) for granular filtering. This guide covers **implementation details**, **schema design**, **query examples**, and **integrations** with Grafana, Alertmanager, and other tools.

---

## **Key Concepts**
### **1. Metric Types Exposed**
FraiseQL provides the following **Prometheus-compatible metrics**:

| **Category**          | **Metric Name**                     | **Description**                                                                 | **Label Examples**                          |
|-----------------------|-------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| **Query Performance** | `fraise_query_latency_seconds`      | Histogram of query execution time in seconds.                                 | `query_type={type}, env={environment}`     |
|                       | `fraise_query_count`                | Counter of total queries executed.                                            | `query_type={type}, status={code}`          |
| **Cache Efficiency**  | `fraise_cache_hits_total`           | Counter for cache hits (redundant fetches avoided).                            | `cache_type={type}, namespace={name}`       |
|                       | `fraise_cache_misses_total`         | Counter for cache misses (new fetches required).                              | Same as above                               |
| **Mutation Safety**   | `fraise_mutation_errors`            | Counter for failed mutations (e.g., schema conflicts).                         | `mutation_type={type}, error={description}` |
| **Database Operations**| `fraise_db_calls_total`             | Counter for database reads/writes.                                           | `db_type={type}, action={read/write}`       |
|                       | `fraise_db_errors_total`            | Counter for database errors (e.g., timeouts, connection failures).             | Same as above                               |
| **Error Tracking**    | `fraise_errors_total`               | Aggregated counter for all non-successful operations.                         | `error_type={type}, severity={critical/warn}` |
| **System Metrics**    | `fraise_process_resident_memory_bytes` | Gauge of FraiseQL’s memory usage.                                             | `env={environment}`                        |
|                       | `fraise_process_start_time_seconds` | Uniquely identifies process restart instances.                                | N/A                                        |

---

### **2. Label Cardinality Best Practices**
To avoid **high cardinality** in Prometheus:
- **Avoid overly granular labels** (e.g., replace `user_id` with `user_segment=premium`).
- **Standardize label values** (e.g., `env=prod/staging/dev`).
- **Use synthetic labels** (e.g., `service=fraiseql`) for cross-cutting dimensions.

**Example:**
✅ **Good:** `fraise_cache_hits_total{namespace="users", cache_type="LRU"}`
❌ **Bad:** `fraise_cache_hits_total{user_id="123", cache_type="LRU"}` *(risk of 1:1 label cardinality)*

---

### **3. Implementation Notes**
- **Exposure:** Metrics are auto-instrumented via FraiseQL’s Prometheus exporter (`/metrics` endpoint).
- **Retention:** Configure Prometheus `retention` (e.g., `24h` for high-cardinality histograms).
- **Alerting:** Use **PromQL aggregations** (e.g., `rate()`, `increase()`) to avoid alert fatigue.

---

## **Schema Reference**
Below is the **complete metric schema** with data types and labels.

| **Metric Name**               | **Type**   | **Help Text**                                                                 | **Labels**                                                                 |
|--------------------------------|------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `fraise_query_latency_seconds` | Histogram  | Query execution time in seconds (bucketed: 0.1s, 0.5s, 1s, 5s, 10s).        | `query_type`, `env`, `status`                                               |
| `fraise_query_count`           | Counter    | Total queries executed.                                                         | `query_type`, `status`                                                      |
| `fraise_cache_hits_total`      | Counter    | Cache hits (redundant fetches).                                                | `cache_type`, `namespace`                                                  |
| `fraise_cache_misses_total`    | Counter    | Cache misses (new fetches).                                                    | Same as above                                                                |
| `fraise_mutation_errors`       | Counter    | Failed mutations (e.g., schema conflicts).                                     | `mutation_type`, `error`                                                   |
| `fraise_db_calls_total`        | Counter    | Database read/write operations.                                                 | `db_type`, `action`                                                         |
| `fraise_db_errors_total`       | Counter    | Database errors (timeouts, failures).                                          | Same as above                                                                |
| `fraise_errors_total`          | Counter    | All non-successful operations.                                                 | `error_type`, `severity`                                                    |
| `fraise_process_resident_memory_bytes` | Gauge | Memory usage in bytes.                                              | `env`                                                                        |
| `fraise_process_start_time_seconds` | Gauge | Unix timestamp of FraiseQL process start.                                     | N/A                                                                        |

---
**Histogram Buckets:**
- Default buckets for `fraise_query_latency_seconds`: `[0.1, 0.5, 1, 5, 10, 30, 60, 120, 300, 600]` (seconds).
- Customize via `fraise_query_latency_seconds_bucket` metric.

---

## **Query Examples**
### **1. Basic Aggregations**
**Query Latency (99th Percentile):**
```promql
histogram_quantile(0.99, rate(fraise_query_latency_seconds_bucket[5m])) by (query_type)
```
**Result:** Latency percentiles per `query_type` (e.g., `SELECT`, `MUTATION`).

---

### **2. Cache Efficiency**
**Cache Hit Ratio:**
```promql
1 - (rate(fraise_cache_misses_total[1h]) / rate(fraise_cache_hits_total[1h] + fraise_cache_misses_total[1h]))
```
**Result:** Hit ratio as a scalar (0–1).

---

### **3. Error Alerting**
**Mutation Errors (Last 5 Minutes):**
```promql
increase(fraise_mutation_errors{mutation_type="schema_update"}[5m]) > 0
```
**Alert Rule:**
```yaml
- alert: HighMutationErrorRate
  expr: rate(fraise_mutation_errors[5m]) > 2
  labels:
    severity: warning
  annotations:
    summary: "Mutation errors spiking in {{ $labels.env }}"
```

---

### **4. Database Pressure**
**DB Call Rate (Per Second):**
```promql
rate(fraise_db_calls_total{db_type="postgres", action="write"}[1m])
```
**Result:** Writes/second to PostgreSQL.

---

### **5. Latency SLO Monitoring**
**Query Latency SLO Violation:**
```promql
histogram_quantile(0.95, rate(fraise_query_latency_seconds_bucket[1m])) > 100  # >100ms
```
**Alert:**
```yaml
- alert: QueryLatencySloViolation
  expr: histogram_quantile(0.99, rate(fraise_query_latency_seconds_bucket[1m])) > 200
  for: 5m
  labels:
    severity: critical
```

---

## **Query Optimization Tips**
1. **Use `rate()` for counters** (avoid `increase()` for high-cardinality metrics).
2. **Leverage `by()` for granularity** (e.g., `by (query_type, env)`).
3. **Bucket histograms wisely**—adjust buckets for your latency distribution.
4. **Avoid `count_over_time()`** on high-cardinality metrics (use `sum()` + `by()` instead).

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Integration**                     |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **[Grafana Dashboards]**         | Pre-built dashboards for FraiseQL metrics (e.g., latency trends, cache stats). | Grafana, Prometheus                  |
| **[Alertmanager Rules]**         | Structured alerting for errors, performance anomalies.                         | Alertmanager, Slack/Email            |
| **[Thanos Scaling]**             | Long-term metric retention and cross-cluster querying.                        | Thanos, Prometheus                   |
| **[Correlation with APM]**       | Link Prometheus metrics to tracing (e.g., Jaeger) for root-cause analysis.    | OpenTelemetry, Jaeger                |
| **[Service Mesh Metrics]**       | Export FraiseQL metrics to Istio/Envoy for network-aware observability.       | Istio, Envoy                         |

---

## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| **High Prometheus storage usage**   | Reduce label cardinality (e.g., aggregate `user_id` to `user_segment`).      |
| **Alert noise from high-cardinality** | Use `group_left()` or `group_right()` to reduce dimensions.               |
| **Missing metrics**                 | Verify FraiseQL exporter is running (`curl http://localhost:8080/metrics`).  |
| **Slow PromQL queries**             | Add `limit` clauses or use `approx_*` functions for large datasets.         |

---
**Example Fix for High Cardinality:**
```promql
# Bad: Too many dimensions
rate(fraise_errors_total{error_type="db", severity="critical"}) by (db_type, table)

# Good: Aggregate where possible
sum(rate(fraise_errors_total{severity="critical"})) by (db_type)
```

---
## **Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Histogram**          | Tracks distribution of values (e.g., latencies) with configurable buckets.    |
| **Counter**            | Monotonically increasing metric (e.g., total queries).                         |
| **Gauge**              | Instant value (e.g., memory usage).                                          |
| **PromQL**             | Prometheus Query Language for metric aggregation.                             |
| **Label Cardinality**  | Number of unique label value combinations (e.g., `env=prod,service=fraiseql`).|

---
## **Further Reading**
1. [Prometheus Documentation](https://prometheus.io/docs/)
2. [FraiseQL Metrics Exporter](https://docs.fraiseql.com/monitoring/metrics/)
3. [Best Practices for Scaling Prometheus](https://prometheus.io/docs/practices/operating/)
4. [Grafana Prometheus Data Source Guide](https://grafana.com/docs/grafana/latest/features/datasources/prometheus/)