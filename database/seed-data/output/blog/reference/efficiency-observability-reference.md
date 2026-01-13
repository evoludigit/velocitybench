---
**[Pattern] Efficiency Observability: Reference Guide**
*Last Updated: [YYYY-MM-DD] | Version: [X.X.X]*

---

### **1. Overview**
Efficiency Observability is an **observability pattern** designed to monitor, measure, and optimize system resource utilization—CPU, memory, I/O, network, and concurrency—across microservices, containers, or distributed workloads. Unlike traditional metrics (e.g., response time), this pattern focuses on **latency-aware efficiency**, identifying inefficiencies like:
- **Unbounded resource growth** (e.g., memory leaks in long-running processes).
- **Hotspots** (e.g., CPU throttling due to inefficient algorithms).
- **Waste** (e.g., unused threads, over-provisioned queues).

By combining **per-request telemetry** with **long-term trend analysis**, teams can proactively address inefficiencies before they degrade performance.

---

### **2. Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 | **Example Use Case**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Efficiency Metric**  | Quantifiable measure of resource usage per unit of work (e.g., "GB/s of memory consumed per request").                                                                                                           | Tracking "CPU cycles per API invocation" to detect inefficient code paths.                              |
| **Baseline Threshold** | Historical average or percentile (e.g., 95th percentile CPU usage) used to flag anomalies.                                                                                                                     | Alerting when memory per request exceeds the 99th percentile by 30%.                                     |
| **Latency Decomposition** | Breaking down request latency into stages (e.g., DB query, serialization) to pinpoint inefficient components.                                                                                                 | Identifying a 1-second DB query as the bottleneck in a 2-second response.                                |
| **Utilization Efficiency** | Ratio of actual resource usage to theoretical maximum (e.g., 60% CPU utilization during peak traffic).                                                                                                      | Detecting underutilized services during off-peak hours to optimize scaling.                              |
| **Causal Path**        | A chain of dependencies (e.g., `UserService → PaymentService → DB`) where inefficiencies cascade.                                                                                                           | Tracing a memory spike from `PaymentService` back to a misconfigured retry loop.                         |

---

### **3. Schema Reference**
Use the following schemas to model efficiency observability data in your observability pipeline (e.g., Prometheus, OpenTelemetry, or custom databases).

#### **Core Metrics Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `request_id`            | `string`       | Unique identifier for a single user request (correlate across services).                                                                                                                                       | `"req-168f9e2c-3a4b-5c6d"`             |
| `timestamp`             | `timestamp`    | When the request was processed (ISO 8601).                                                                                                                                                                       | `"2024-05-15T14:30:45.123Z"`          |
| `service_name`          | `string`       | Name of the service processing the request (e.g., `auth-service`).                                                                                                                                                   | `"user-service"`                       |
| `operation_name`        | `string`       | Specific operation (e.g., `get_user`, `process_payment`).                                                                                                                                                         | `"validate_credentials"`              |
| `resource_type`         | `enum`         | Type of resource being measured (`CPU`, `memory`, `network`, `disk`, `threads`).                                                                                                                               | `"CPU"`                                |
| `utilization`           | `float`        | Resource usage (normalized to 0–1 or absolute units).                                                                                                                                                             | `0.75` (75% CPU)                       |
| `concurrency`           | `integer`      | Number of parallel threads/processes using the resource.                                                                                                                                                         | `4`                                    |
| `baseline_threshold`    | `float`        | Historical 95th percentile for this metric.                                                                                                                                                                     | `0.5` (CPU)                            |
| `waste_percent`         | `float`        | Percentage of resource wasted (e.g., idle time or over-provisioning).                                                                                                                                             | `20`                                   |
| `latency_breakdown`     | `object`       | Nested phases (e.g., `db_query`, `serialization`) with their own metrics.                                                                                                                                         | `{ "db_query": { "latency_ms": 1200 } }`|
| `dependencies`          | `array`        | Upstream/downstream services impacted by this request.                                                                                                                                                             | `["db-service", "cache-service"]`      |

#### **Efficiency Trend Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `service_name`          | `string`       | Name of the service.                                                                                                                                                                                               | `"order-service"`                      |
| `metric_name`           | `enum`         | Type of trend (`cpu_utilization`, `memory_leak_rate`, `thread_idle_time`).                                                                                                                                    | `"memory_leak_rate"`                   |
| `time_range`            | `object`       | Start/end of the trend window (UTC).                                                                                                                                                                            | `{ "start": "2024-05-15T00:00:00Z", "end": "2024-05-16T00:00:00Z" }` |
| `trend_value`           | `float`        | Aggregated value (e.g., MB/s leaked per hour).                                                                                                                                                                   | `42.5` (MB/hour)                       |
| `anomaly_score`         | `float`        | Score (0–1) indicating deviation from baseline (higher = more severe).                                                                                                                                         | `0.92`                                 |

---

### **4. Query Examples**
#### **Query 1: Identify CPU Hotspots in Real-Time**
**Goal**: Find services where CPU utilization exceeds the 95th percentile baseline for 5+ minutes.
**Query (Prometheus)**:
```promql
rate(cpu_usage_seconds_total{service!~"monitoring-.*"}[5m])
  > histogram_quantile(0.95, sum by(service) (rate(cpu_usage_seconds_total[1h])))
  and on(service) group_left
  sum(up{service}) by(service)
```
**Output Interpretation**:
- Services with `cpu_usage_seconds_total` > threshold are flagged.
- Narrow down with `service_labels` to isolate problematic endpoints.

---

#### **Query 2: Detect Memory Leaks Over Time**
**Goal**: Calculate memory leak rate (MB/sec) per service.
**Query (OpenTelemetry)**:
```sql
SELECT
  service_name,
  (memory_bytes_used - memory_bytes_used_prev) / EXTRACT(EPOCH FROM (timestamp - timestamp_prev)) AS leak_rate_mb_sec
FROM (
  SELECT
    service_name,
    memory_bytes_used,
    timestamp,
    LAG(memory_bytes_used) OVER (PARTITION BY service_name ORDER BY timestamp) AS memory_bytes_used_prev,
    LAG(timestamp) OVER (PARTITION BY service_name ORDER BY timestamp) AS timestamp_prev
  FROM memory_usage_metrics
  WHERE timestamp >= NOW() - INTERVAL '30 days'
)
WHERE leak_rate_mb_sec > 0.1;  -- Alert if > 100KB/sec
```
**Output Interpretation**:
- Services with `leak_rate_mb_sec` > 0.1 MB/sec are candidates for leak investigation.
- Combine with `process_name` to isolate specific threads (e.g., "auth-service:token-generator").

---

#### **Query 3: Analyze Causal Path Inefficiencies**
**Goal**: Find requests where a downstream service’s inefficiency cascades to upstream latency.
**Query (Jaeger/Zipkin Trace API)**:
```http
GET /api/traces?filter=service:order-service AND duration:>1000ms
  AND dependency.service:payment-service AND cpu.utilization:>0.8
```
**Output Interpretation**:
- Traces where `payment-service` has high CPU (>80%) and `order-service` latency >1s are prioritized.
- Use `dependencies` field to visualize the impact chain.

---

### **5. Implementation Steps**
#### **Step 1: Instrumentation**
- **Add Efficiency Metrics**:
  Use OpenTelemetry’s `Resource` API to tag spans with:
  ```go
  // Example: Tag a span with CPU usage
  ctx := otel.GetTextMapPropagator().Extract(
      context.Background(),
      otel.TextMapCarrier{...},
  )
  span := otel.StartSpan(
      "process_order",
      trace.SpanKindServer,
      otel.WithResource(
          otel.ResourceFromValues(
              "service.name", "order-service",
              "cpu.utilization", 0.75,  // Record during span
              "memory.bytes", 128*1024*1024,
          ),
      ),
  )
  defer span.End()
  ```
- **Sample Rate**: For high-cardinality services, use **adaptive sampling** (e.g., sample 100% during peak hours, 10% otherwise).

#### **Step 2: Baseline Calculation**
- **Compute Percentiles**:
  Use tools like **Prometheus alertmanager** or **Grafana’s Explore** to calculate 95th/99th percentiles over a 7-day window.
  Example (Prometheus):
  ```promql
  histogram_quantile(0.95, rate(cpu_seconds_total[5m]))
  ```
- **Store Baselines**: Persist thresholds in a database (e.g., TimescaleDB) for offline analysis.

#### **Step 3: Alerting**
- **Anomaly Detection**:
  Use **sliding windows** to detect sudden spikes (e.g., 3× baseline for 5 minutes).
  Example (Alertmanager):
  ```yaml
  groups:
  - name: efficiency-alerts
    rules:
    - alert: HighMemoryWaste
      expr: memory_waste_percent > 30
      for: 5m
      labels:
        severity: warning
  ```
- **Contextual Alerts**:
  Correlate with business events (e.g., "memory spike during payment processing").

#### **Step 4: Visualization**
- **Dashboards**:
  - **Time-series**: Plot `utilization_efficiency` over time per service.
  - **Heatmaps**: Show hotspots by endpoint (e.g., `GET /api/orders`).
  - **Dependency Graphs**: Visualize causal paths with inefficiency scores.
- **Tools**:
  - **Grafana**: Use [Prometheus](https://grafana.com/docs/grafana/latest/datasources/prometheus/) or [Loki](https://grafana.com/docs/loki/latest/) for logs.
  - **Datadog**: Pre-built efficiency dashboards for JVM/Go services.

---
### **6. Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                      |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **[Latency Decomposition](...)** | Breaks down request latency into phases (e.g., DB, network) to identify bottlenecks.                                                                                                                        | When response time is degraded but efficiency metrics are unclear.                                  |
| **[Resource Quotas](...)**       | Enforces limits (e.g., "no service can exceed 80% CPU") to prevent cascading failures.                                                                                                                     | During capacity planning or when efficiency metrics exceed thresholds.                                |
| **[Adaptive Sampling](...)**    | Dynamically adjusts sampling rate based on traffic patterns to reduce cardinality.                                                                                                                         | For high-cardinality services (e.g., 10,000+ endpoints).                                            |
| **[Circuit Breaker](...)**       | Limits calls to failing services to prevent resource exhaustion.                                                                                                                                               | When inefficient dependencies (e.g., slow DB) are causing cascading inefficiencies.                  |
| **[Chaos Engineering](...)**     | Intentionally injects failures to test resource limits (e.g., "kill 10% of pods").                                                                                                                       | To validate efficiency metrics under stress.                                                         |

---
### **7. Anti-Patterns**
- **Ignoring Baseline Drift**: Static thresholds become obsolete over time (e.g., "CPU < 50%" may be irrelevant after scaling).
  **Fix**: Use **adaptive baselines** (e.g., `95th percentile over 30 days`).
- **Over-Sampling**: Collecting per-request metrics for every endpoint increases cardinality and storage costs.
  **Fix**: Implement **stratified sampling** (e.g., sample 100% for slow requests).
- **Silos**: Treating efficiency metrics in isolation (e.g., "CPU is fine, but memory is high") without tracing dependencies.
  **Fix**: Always correlate with **causal paths** and **latency breakdowns**.

---
### **8. Tools Ecosystem**
| **Category**          | **Tools**                                                                                                                                                                                                 | **Key Features**                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Metrics**           | Prometheus, Datadog, New Relic, OpenTelemetry Collector                                                                                                                                                       | Querying, alerting, and long-term storage.                                                             |
| **Tracing**           | Jaeger, Zipkin, OpenTelemetry Trace Exporter                                                                                                                                                            | End-to-end request tracing and dependency visualization.                                              |
| **Log Analysis**      | Loki, ELK Stack, Datadog Logs                                                                                                                                                                           | Correlating logs with efficiency metrics.                                                               |
| **Baseline DB**       | TimescaleDB, InfluxDB, BigQuery                                                                                                                                                                         | Storing percentiles and trend data.                                                                   |
| **Visualization**     | Grafana, Kibana, Datadog Dashboards                                                                                                                                                                      | Custom dashboards for efficiency KPIs.                                                                  |

---
### **9. Example Workflow**
1. **Detect**: A 99th-percentile CPU spike in `payment-service` during checkout.
   - **Query**: `rate(cpu_seconds_total{service="payment-service"}[5m]) > histogram_quantile(0.99, ...)`.
2. **Investigate**: Trace the causal path:
   - **Tool**: Jaeger query for `payment-service` spans with `cpu.utilization > 0.8`.
   - **Find**: A misconfigured retry loop in `validate_payment`.
3. **Fix**: Adjust retry settings and monitor `waste_percent` (now 15% → 5%).
4. **Prevent**: Update baseline for `payment-service` to reflect new limits.

---
### **10. Further Reading**
- [OpenTelemetry Semantic Conventions](https://github.com/open-telemetry/semantic-conventions) (for standard metric names).
- [Prometheus Alertmanager Docs](https://prometheus.io/docs/alerting/latest/alertmanager/) (for efficiency alerts).
- [Kubernetes Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) (to enforce efficiency limits).