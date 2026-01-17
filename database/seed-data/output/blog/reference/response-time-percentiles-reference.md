# **[Pattern] Response Time Percentiles – Reference Guide**

---

## **1. Overview**
The **Response Time Percentiles** pattern monitors and tracks latency distributions across a system or application by capturing percentile-based response times (e.g., p50, p90, p99). Unlike simple average latency metrics, percentiles provide deeper insights into tail latency, ensuring reliable performance analysis and SLO/SLA validation. This pattern is widely used in observability, performance tuning, and capacity planning.

This guide covers:
- Key concepts and implementation considerations.
- A schema reference for defining percentiles in metrics.
- Query examples across common monitoring tools.
- Related patterns for comprehensive latency analysis.

---

## **2. Key Concepts**
### **2.1 Percentile Definitions**
Percentiles represent the response time below which a given percentage of requests fall:

| **Percentile** | **Description**                          | **Use Case**                          |
|---------------|------------------------------------------|---------------------------------------|
| **P50**       | Median response time (50% of requests)  | Baseline performance assessment       |
| **P75**       | 75% of requests completed within time    | Performance degradation detection     |
| **P90**       | 90% of requests completed within time    | Identifying occasional slowdowns      |
| **P95**       | 95% of requests completed within time    | Pre-tail latency alerts               |
| **P99**       | 99% of requests completed within time    | Severe outlier detection (SLO breach) |

### **2.2 Implementation Considerations**
- **Data Collection:**
  - Capture timestamps for all requests (e.g., start/end time).
  - Use histogram-style aggregations for accurate percentile calculation (avoid simple averages).
- **Sampling:**
  - High-cardinality metrics (e.g., per-endpoint/traffic-source) may require sampling or bucketing.
  - For distributed systems, ensure consistent global sampling rates.
- **Storage:**
  - Retain percentile metrics alongside raw latency distributions for trend analysis.
- **Alerting:**
  - Define SLOs using percentiles (e.g., "p99 ≤ 1s" for 99% uptime).
  - Use anomaly detection on percentile trends (e.g., sudden p99 spikes).

### **2.3 Relation to Other Metrics**
- **Latency vs. Percentiles:**
  - Average latency (mean) is misleading if skewed by outliers; percentiles focus on distribution.
  - Combine with **error rates** to detect correlated degradations (e.g., p99 latency + 5xx errors).
- **Throughput:**
  - Percentiles alone don’t show request volume. Pair with RPS (requests per second) for capacity planning.

---

## **3. Schema Reference**
Below is a standardized schema for **Response Time Percentiles** metrics. Adjust field names to match your telemetry system.

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **metric_name**         | String         | Name of the percentile (e.g., `latency_p99`, `api.response_time_p75`).          | `user_authentication_p90`                  |
| **service**             | String         | System/application context (e.g., `payment-service`, `frontend-api`).           | `ecommerce`                                 |
| **endpoint**            | String         | API/resource path (for granular analysis).                                      | `/checkout/process`                         |
| **percentile**          | Integer/Float  | Percentile value (p50 = 50, p99 = 99.0).                                         | 90, 99.9                                    |
| **value**               | Float          | Response time in milliseconds (or specified unit).                              | 125.4, 420.0                                |
| **unit**                | String         | Time unit (e.g., `ms`, `s`).                                                    | `ms`                                        |
| **timestamp**           | ISO 8601       | When the percentile was measured (e.g., rolling window).                        | `2024-05-20T14:30:00Z`                      |
| **dimensions**          | Object         | Optional filters (e.g., `user_segment`, `region`).                              | `{ region: "us-west-2", tier: "premium" }   |
| **sample_size**         | Integer        | Number of requests sampled for this percentile (for transparency).             | 10_000                                      |
| **data_source**         | String         | Where data was collected (e.g., `apm-agent`, `prometheus-histogram`).            | `jaeger`                                    |

---
**Example Metric:**
```json
{
  "metric_name": "api.response_time_p95",
  "service": "order-service",
  "endpoint": "/api/orders/create",
  "percentile": 95,
  "value": 850.2,
  "unit": "ms",
  "timestamp": "2024-05-20T14:30:00Z",
  "dimensions": { "user_segment": "vip" },
  "sample_size": 5_000
}
```

---

## **4. Query Examples**
Below are queries for common observability tools to extract or visualize percentiles.

---

### **4.1 Prometheus**
Use the **histogram_quantile** function to compute percentiles from histogram buckets.

**Query for p99 latency (ms):**
```promql
histogram_quantile(0.99, sum(rate(http_request_duration_ms_bucket[5m])) by (le))
```
**Filter by service and endpoint:**
```promql
histogram_quantile(0.95, sum(rate(api_latency_ms_bucket[1m])) by (le, service, endpoint))
    where service = "payment-service" and endpoint = "/pay"
```
**Alert on p99 > 1s:**
```promql
histogram_quantile(0.99, sum(rate(api_response_time_ms_bucket[5m])) by (le)) > 1000
```

---

### **4.2 Grafana Explore (Prometheus)**
1. Add a **PromQL** panel.
2. Query:
   ```
   histogram_quantile(0.99, sum(rate(my_app_latency_bucket[5m])) by (le))
   ```
3. Apply **Transform → Transform Variables** to auto-generate p50/p90/p99 panels.

---

### **4.3 OpenTelemetry/Jaeger**
Use **histogram aggregation** in traces:
```yaml
# In OpenTelemetry Collector config (OTLP)
aggregation:
  histogram:
    buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25, 50, 100, 250, 500, 1000]
    record_explicit_buckets: true
```
**Query percentiles in Jaeger UI:**
- Use the **Service Map** → select a trace → **Latency Distribution** tab.

---

### **4.4 Datadog**
**Time Series Query (for p99):**
```
metrics.query('avg:api.latency.p99{*}.as_count(),min_time:300s,max_time:300s')
```
**Histogram Analysis:**
1. Go to **Metrics → Histograms**.
2. Select your latency metric → **Percentile** tab → choose p90/p99.

---

### **4.5 InfluxDB**
Use **percentile_over_time** function:
```influxql
SELECT "percentile" AS percentile, "value" AS latency_ms
FROM "api_latency"
WHERE $timeFilter
GROUP BY time($__interval), "percentile"
FILL(null)
```
**Example with p75:**
```
SELECT "p75" AS percentile, "value" AS latency_ms
FROM "api_latency"
WHERE $timeFilter
GROUP BY time($__interval)
```

---

## **5. Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                 |
|--------------------------------------|------------------------------------------------------------------------------|
| **Skewed percentiles due to outliers** | Use **histogram buckets** (not summaries) and ignore extreme outliers.       |
| **High cardinality**                 | Sample data or bucket by service/endpoint early in the pipeline.             |
| **Incorrect time windows**           | Ensure rolling windows align with traffic patterns (e.g., 1m windows).      |
| **Missing p99 data**                  | Set up **autoscaling** probes to capture tail latency during traffic spikes.  |
| **Alert fatigue from noisy p99**      | Combine with **error rates** or **anomaly detection** (e.g., Prometheus Alertmanager). |

---

## **6. Related Patterns**
Complement **Response Time Percentiles** with these patterns for holistic latency analysis:

| **Pattern**                     | **Description**                                                                 | **Relation to Percentiles**                          |
|----------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------|
| **[Latency Histograms](#)**      | Capture full request time distributions (e.g., Prometheus histograms).      | Percentiles are derived from histograms.            |
| **[SLO/SLA Monitoring](#)**      | Define reliability targets (e.g., "p99 ≤ 500ms").                             | Percentiles are the primary signal for SLO breaches. |
| **[Error Budget Allocation](#)**  | Allocate error budgets based on SLO percentiles.                              | Track how much "budget" is consumed by p99 latency.  |
| **[Distributed Tracing](#)**     | Trace requests end-to-end to identify slow components.                        | Percentiles help prioritize slow spans in traces.    |
| **[Capacity Planning](#)**       | Forecast resource needs based on percentile growth.                          | Use p99 trends to size infrastructure for peak loads.|

---
### **7. Further Reading**
- [SRE Book: Observability](https://sre.google/sre-book/observability/) (Percentiles in Chapter 4).
- [Prometheus Metrics Guide: Histograms](https://prometheus.io/docs/practices/histograms/).
- [OpenTelemetry Percentile Exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/percentile).

---
**Version:** 1.0
**Last Updated:** 2024-05-20