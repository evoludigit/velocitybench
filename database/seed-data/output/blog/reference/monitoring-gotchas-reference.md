# **[Pattern] Monitoring Gotchas – Reference Guide**

---

## **Overview**
Monitoring systems are critical for detecting performance issues, failures, and anomalies in distributed systems—but they can also introduce subtle pitfalls if misconfigured or misunderstood. The **"Monitoring Gotchas"** pattern highlights common blind spots (e.g., sampling errors, alert fatigue, metric normalization issues) that can lead to false positives, missed incidents, or misleading insights. This guide ensures observability teams design monitoring strategies that are **accurate, scalable, and actionable**, while avoiding pitfalls like:
- **Overlapping metrics** (e.g., conflicting alert thresholds).
- **Sampling bias** (e.g., monitoring only on production servers).
- **Unbounded retention policies** (e.g., storing metrics indefinitely).
- **Alert fatigue** (e.g., noisy alerts drowning out critical issues).

Well-implemented monitoring should balance **granularity** (detailed visibility) with **efficiency** (resource constraints). This pattern complements other observability patterns like **[Distributed Tracing]** and **[Log Aggregation]** by providing a checklist for robust monitoring setups.

---

## **Key Concepts & Implementation Details**

### **1. Common Monitoring Gotchas**
| **Gotcha**               | **Description**                                                                 | **Impact**                                                                 |
|--------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Sampling Errors**      | Metrics gathered from a representative subset (e.g., 1% of requests) may skew results. | Inaccurate performance trends or missed edge cases.                          |
| **Alert Fatigue**        | Too many alerts (e.g., 99%+ uptime alerts) lead to alert tunnel vision.       | Critical issues overlooked due to desensitization.                         |
| **Metric Normalization** | Unnormalized metrics (e.g., raw CPU usage) can hide true workload patterns. | Misleading trends (e.g., scaling decisions based on absolute values).        |
| **Lag in Aggregation**   | How often metrics are collected (e.g., 60s vs. 1s) affects anomaly detection.   | Slower response to spikes or degradation.                                   |
| **Retention Policies**   | Unlimited storage inflates costs and burdens query performance.               | High operational overhead; slower incident investigations.                   |
| **Overlapping Alerts**   | Multiple alerts trigger on the same issue (e.g., latency + error rate).        | Noise; difficulty isolating root causes.                                   |
| **Ignored Edge Cases**   | Monitoring on "typical" workloads may miss rare but critical failures.         | Undetected systemic risks (e.g., DoS attacks).                             |
| **Configuration Drift**  | Alert thresholds not updated after refactoring (e.g., new services).           | False negatives (e.g., unmonitored endpoints).                             |

---

### **2. Schema Reference**
Define a **monitoring configuration schema** to avoid common pitfalls. Use this as a template for your observability pipeline:

| **Field**               | **Type**       | **Description**                                                                                     | **Example Values**                                                                 |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `metric_name`           | String         | Name of the metric (e.g., `http.requests.per.second`).                                               | `response_time.avg`, `disk.io.ops`                                                   |
| `sampling_rate`         | Float (0.0–1.0)| Percentage of requests/events sampled (e.g., 0.1 = 10%).                                            | `0.5`, `0.01` (1%)                                                                 |
| `aggregation_window`    | Duration       | Time window for metric aggregation (e.g., 5s, 1m).                                                  | `PT1M`, `PT5S`                                                                     |
| `normalization_factor`  | String/Formula | How metric values are normalized (e.g., `total_requests / cores`).                                   | `total / (cpu_threads * 2)`, `requests / GB_ram`                                   |
| `alert_threshold`       | String         | Threshold logic (e.g., `> 95th percentile of last 5m`).                                              | `response_time > 500ms`, `error_rate > 0.5`                                          |
| `retention_policy`      | Duration       | How long raw/aggregated data is stored.                                                           | `PT1D` (1 day), `PT7D` (7 days)                                                     |
| `snooze_rules`          | JSON Array     | Alert suppression for known non-critical periods (e.g., weekends).                                 | `[{"start": "2024-01-01T00:00:00Z", "end": "2024-01-02T00:00:00Z"}]`             |
| `related_metrics`       | String Array   | Metrics correlated with this one (e.g., `latency` → `cpu_utilization`).                             | `["memory.usage", "requests.dropped"]`                                             |
| `owner`                 | String         | Team responsible for this metric’s interpretation.                                                    | `backend-team`, `database-admins`                                                   |

---
**Example Schema (JSON):**
```json
{
  "metric_name": "db.query.latency",
  "sampling_rate": 0.2,
  "aggregation_window": "PT15S",
  "normalization_factor": "total / (db_connections / 1000)",
  "alert_threshold": "value > p99(last_5m)",
  "retention_policy": "PT7D",
  "snooze_rules": [{"day_of_week": ["5", "6"]}],
  "related_metrics": ["memory.cache_hits", "cpu.query_load"],
  "owner": "database-team"
}
```

---

## **Query Examples**
Use these **Grafana/PromQL/Loki** queries to uncover gotchas in your monitoring setup.

### **1. Detect Sampling Bias**
```promql
# Compare sampled vs. unsampled metrics (if available)
sampled_latency: http_request_duration_seconds_sum{env="prod", sampling="10%"}
unsampled_latency: http_request_duration_seconds_sum{env="prod", sampling="100%"}
```
**Goal**: Ensure sampled data reflects unsampled trends (difference < 5%).

### **2. Alert Fatigue Analysis**
```promql
# Alerts fired per day (graph for the last 30 days)
count(alertmanager_alerts_fired_total[1d])
```
**Gotcha**: If > 50 alerts/day, consider adjusting thresholds or suppressions.

### **3. Metric Normalization Check**
```promql
# Normalized vs. raw CPU usage (should correlate)
raw_cpu: sum(rate(container_cpu_usage_seconds_total{namespace="app"}[1m]))
normalized_cpu: raw_cpu / count(container_spec_cpu_quota{namespace="app"})
```
**Goal**: Normalized metrics should align with expected workloads (e.g., `normalized_cpu < 0.8` for baseline).

### **4. Retention Policy Impact**
```loki
# Query time series longer than retention policy
{job="app"} | timeshift(~"PT7D") | count_over_time(~".*", 1h)
```
**Gotcha**: High volume after retention expiry indicates inefficient storage.

### **5. Overlapping Alerts**
```promql
# Alerts triggered on the same timestamp (potential noise)
on(timestamp) group_left()
count_over_time({alert="HighLatency", severity="critical"}[5m]) by (service)
```
**Fix**: Merge or suppress overlapping alerts.

---

## **Related Patterns**
To complement **Monitoring Gotchas**, integrate these patterns:

1. **[Distributed Tracing]**
   - **Why?** Traces reveal root causes of latency spikes (e.g., DB timeouts) that metrics alone may miss.
   - **Gotcha**: Ensure trace sampling aligns with metric sampling to avoid inconsistencies.

2. **[Log Aggregation]**
   - **Why?** Logs provide contextual details for metrics/alerts (e.g., `500 errors` → log the exact request payload).
   - **Gotcha**: Log volume can overwhelm parsers; use structured logging and retention filters.

3. **[Chaos Engineering]**
   - **Why?** Proactively test monitoring resilience (e.g., simulate region outages).
   - **Gotcha**: Monitor chaos experiments separately to avoid alert storms.

4. **[Canary Deployments]**
   - **Why?** Gradually roll out changes while monitoring for regressions.
   - **Gotcha**: Canary metrics (e.g., error rates) must be distinct from production metrics.

5. **[Observability Taxonomy]**
   - **Why?** Classify metrics/logs/traces to avoid silos (e.g., "Latency" vs. "Error Rate").
   - **Gotcha**: Ambiguous labels (e.g., `error`) lead to misdiagnosis.

---
## **Mitigation Checklist**
| **Gotcha**               | **Mitigation Strategy**                                                                 |
|--------------------------|----------------------------------------------------------------------------------------|
| Sampling Errors          | Use stratified sampling (e.g., by region/TrafficType).                                 |
| Alert Fatigue            | Implement alert severity tiers (P0–P3) and suppression rules.                          |
| Metric Normalization     | Document normalization formulas in metrics repository (e.g., GitHub/GitLab).          |
| Lag in Aggregation       | Adjust `scrape_interval` in Prometheus (e.g., `15s` for high-cardinality metrics).    |
| Retention Policies       | Set retention to `PT7D` for aggregations, `PT1D` for raw data.                          |
| Overlapping Alerts       | Use alert grouping (e.g., `group_by=["service"]`).                                     |
| Ignored Edge Cases       | Include stress-test scenarios in monitoring (e.g., `load=99th_percentile`).             |
| Configuration Drift      | Enforce metric/alert ownership (assign teams to specific metrics).                      |

---
## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                           | **Gotcha to Avoid**                                                                 |
|------------------------|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| Prometheus             | Time-series collection/alerting                                                   | High-cardinality metrics (e.g., `pod:` labels) cause memory bloat.                 |
| Grafana                | Visualization                                                                       | Dashboards with too many panels (>10) reduce usability.                              |
| Loki                   | Log aggregation                                                                     | Unstructured logs increase parsing overhead; prefer structured logs (e.g., JSON).   |
| Alertmanager           | Alert routing/suppression                                                           | Ignoring `snooze` rules leads to alert tunnel vision.                                |
| OpenTelemetry          | Unified metrics/traces/logs                                                        | Sampling misalignment between traces and metrics (e.g., `1%` trace sampling vs. `50%` metric sampling). |

---
## **Further Reading**
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [SRE Book: Monitoring Systems](https://sre.google/sre-book/monitoring-systems/)
- [Loki Documentation: Retention Policies](https://grafana.com/docs/loki/latest/configuration/)
- [Chaos Engineering Playbook](https://www.chaosengineering.io/playbook/)

---
**Note**: This guide assumes familiarity with **Prometheus**, **Grafana**, and **OpenTelemetry**. Adjust schemas/tools based on your stack (e.g., CloudWatch, Datadog, or Elasticsearch). Always validate changes in a **staging environment** before production.