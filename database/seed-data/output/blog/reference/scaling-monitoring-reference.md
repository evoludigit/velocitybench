---
# **[Pattern] Scaling Monitoring Reference Guide**

---

## **1. Overview**
The **Scaling Monitoring** pattern ensures that monitoring infrastructure grows proportionally with application scale, maintaining observability and performance insights across distributed systems. This pattern addresses challenges like:
- **Monitoring explosion**: Increased overhead from excessive metrics when scaling.
- **Latency sensitivity**: Slow aggregation or query performance under load.
- **Cost efficiency**: Balancing granularity with resource usage.
- **Cross-team scalability**: Supporting DevOps, SREs, and developers with consistent monitoring.

Scaling Monitoring combines **sampling**, **aggregation**, **sampling-based filtering**, and **multi-resolution time-series storage** to optimize data retention and query efficiency. By implementing this pattern, teams can avoid data overload while retaining critical insights for debugging, performance tuning, and capacity planning.

---

## **2. Schema Reference**

| **Component**               | **Purpose**                                                                 | **Key Properties**                                                                 | **Implementation Notes**                                                                                                                                                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Metric Collection Layer** | Captures raw telemetry (metrics, logs, traces) from distributed sources.    | - **Sampling rate** (e.g., 100%, 1%, 0.1%)<br>- **Data format** (Prometheus, OpenTelemetry)<br>- **Ingestion rate** (e.g., 10K/sec) | Use **adaptive sampling** for high-volume sources (e.g., web requests) to reduce load.                                                                                                                             |
| **Aggregation Layer**       | Reduces granularity for long-term storage or high-cardinality data.       | - **Aggregation windows** (e.g., 1m, 5m, 1h)<br>- **Functions** (avg, sum, max, percentiles)<br>- **Retention periods** | Precompute aggregations for **cost-efficient storage** (e.g., 7 days for high-cardinality metrics like HTTP 5xx errors).                                                                                             |
| **Storage Tier**            | Stores metrics at different resolutions (e.g., high-res for recent data).   | - **Resolution tiers** (e.g., 1s, 1m, 1d)<br>- **Compression** (e.g., Prometheus TSDB)<br>- **Sharding** (by timestamp/region) | Use **multi-resolution time-series databases** (e.g., Thanos, TimescaleDB) to balance query speed and storage costs.                                                                                                  |
| **Query Engine**           | Processes queries efficiently with filtered or pre-aggregated data.       | - **Query language** (PromQL, Grafana Explore)<br>- **Downsampling** (on-the-fly)<br>- **Caching layer** (e.g., Redis) | Optimize queries with **time-range filtering** and **metric selection** to avoid full-scans.                                                                                                                          |
| **Alerting System**        | Scales alert rules without overwhelming teams.                            | - **Deduplication** (e.g., rollup windows)<br>- **Pacing** (e.g., 1 alert/minute)<br>- **Severity-based routing** | Implement **adaptive alert suppression** (e.g., ignore duplicate alerts for the same error in 5 minutes).                                                                                                                 |
| **Log Sampling**           | Reduces log volume for analysis while preserving critical events.          | - **Sampling rate** (e.g., 5% of total logs)<br>- **Event-based filtering** (e.g., errors, timeouts)<br>- **Retry budget** | Use **stratified sampling** (e.g., sample 100% of 5xx errors, 1% of others).                                                                                                                                                 |
| **Trace Sampling**         | Limits distributed trace volume for cost and performance.                 | - **Sampling probability** (e.g., 0.01 for production)<br>- **Header-based rules** (e.g., skip for `GET /health`)<br>- **Dynamic adjustment** | Combine with **trace-based metrics** (e.g., latency percentiles) to avoid losing context.                                                                                                                              |
| **Dashboard Template**      | Scales dashboards dynamically based on cluster size.                      | - **Dynamic metric substitution** (e.g., `slowest_endpoints` per service)<br>- **Conditional panels** (e.g., show only if errors > 0)<br>- **Multi-tenancy support** | Use **variables** (e.g., `$cluster_id`) to auto-generate dashboards for new environments.                                                                                                                              |

---

## **3. Implementation Details**

### **3.1 Key Concepts**
1. **Adaptive Sampling**
   - Dynamically adjusts sampling rates based on:
     - **Traffic volume** (e.g., sample 1% during peak hours).
     - **Priority** (e.g., sample 100% for critical paths like auth flows).
   - *Tooling*: Use OpenTelemetry’s `sampler` configuration or Prometheus’s `recording rules` with `--web.console.lines=0` for high-cardinality queries.

2. **Multi-Resolution Storage**
   - **High-resolution tier**: 1-second metrics for recent data (e.g., last 24h).
   - **Low-resolution tier**: 1-minute or hourly aggregations for long-term analysis.
   - *Example*: Store raw traces for 7 days; aggregate latency percentiles daily for retention >1 year.

3. **Query Optimization**
   - **Pre-aggregation**: Compute rolling averages/percentiles during ingestion.
   - **Range vector operations**: Use PromQL’s `rate()` or `irate()` to avoid full-scans.
   - *Anti-pattern*: Avoid `sum(rate(http_requests_total[5m]))` without filtering by `service` or `route`.

4. **Cost Control**
   - **Cardinality reduction**:
     - Use **labels selectively** (e.g., `job`, `service` over `instance`).
     - Apply **bucketing** for high-cardinality labels (e.g., `http_method` → {`GET`, `POST`}).
   - **Retention policies**: Auto-delete old data (e.g., 7 days for debug, 1 year for trends).

5. **Cross-Team Scaling**
   - **Shared observability**: Centralize metrics for multi-team environments (e.g., shared `namespace` in Prometheus).
   - **Tenancy isolation**: Use **resource labels** (e.g., `team:backend`, `team:frontend`) for access control.

---

### **3.2 Implementation Steps**

#### **Step 1: Assess Current Load**
- **Metrics**:
  - Query ingestion rate: `sum(rate(prometheus_tsdb_head_samples_appended_total[1m]))`.
  - Storage growth: `increase(prometheus_tsdb_head_series[24h])`.
- **Tools**: Use `promtool` or Grafana’s **Data Link** to analyze query patterns.

#### **Step 2: Apply Sampling**
- **Prometheus**:
  ```yaml
  # config.yaml
  scrape_configs:
    - job_name: 'my_app'
      scrape_interval: 15s
      sampling_interval: 30s  # Only scrape every 30s (3x reduction)
      metrics_path: '/metrics'
  ```
- **OpenTelemetry**:
  ```yaml
  # sampler.config.yaml
  sampling_config:
    decision_wait_timeout: 100ms
    sampling_plane:
      type: "head"
      average_travel_time_ns: 100000000
      root_config:
        type: "rate_limiting"
        rate_limit: 0.01  # 1% sampling rate
  ```

#### **Step 3: Configure Storage Tiers**
- **Thanos**:
  ```yaml
  # thanos.yaml
  store:
    type: s3
    config:
      bucket: my-observability-bucket
  rule:
    group_by: [namespace, service]
    retention_resources:
      - name: "high-res"
        retention: 24h
        objective:
          max_shard_size: 128MB
      - name: "low-res"
        retention: 365d
        objective:
          max_shard_size: 256MB
  ```

#### **Step 4: Optimize Queries**
- **Pre-aggregate with Recording Rules**:
  ```yaml
  # prometheus.rules
  groups:
    - name: high-cardinality.rules
      rules:
        - record: job:http_request_duration_seconds:avg5m
          expr: avg_over_time(http_request_duration_seconds_sum[5m]) / avg_over_time(http_request_duration_seconds_count[5m])
  ```
- **Use `range` for Long-Term Data**:
  ```promql
  # Compare weekly trends (low-resolution)
  sum(rate(http_requests_total{service="api"}[1m])) by (service) > 1000
  ```

#### **Step 5: Scale Alerts**
- **Prometheus Alertmanager**:
  ```yaml
  # alertmanager.yml
  route:
    receiver: 'slack'
    group_by: [alertname, severity]
    repeat_interval: 4h
    group_wait: 10m
    group_interval: 5m
  inhibitors:
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
  ```
- **Dynamic Suppression**: Use `correlation_id` to deduplicate alerts.

#### **Step 6: Standardize Dashboards**
- **Grafana Dashboard Variables**:
  ```json
  // Variables for dynamic service selection
  {
    "name": "service",
    "type": "query",
    "query": "label_values(service[5m], service)",
    "refresh": 300
  }
  ```
- **Conditional Panels**:
  ```json
  // Show only if errors > 0
  "panels": [
    {
      "conditions": [
        { "operator": ">", "target": "http_requests_total{status=~\"5..\"}", "value": "0" }
      ],
      "targets": [...]
    }
  ]
  ```

---

## **4. Query Examples**

### **4.1 Basic Sampling Queries**
```promql
# Sample every 5th request (20% sampling rate)
rate(http_requests_total[1m]) / 5

# Filter high-cardinality labels
sum(rate(http_request_duration_seconds_sum[5m]))
  by (service)
  unless (service = "auth-service")

# Dynamic sampling based on traffic
max_over_time(http_requests_total[1h])
  unless (max_over_time(http_requests_total[1h]) < 1000)
```

### **4.2 Multi-Resolution Aggregations**
```promql
# High-res: 1s metrics for recent data
rate(http_requests_total[1m])

# Low-res: 1h aggregations for trends
(1 - rate(http_requests_total{status="5xx"}[5m]))
  by (service, route)
```

### **4.3 Alert Query with Sampling**
```promql
# Alert only if >1% of requests fail (implicit sampling)
sum(rate(http_requests_total{status="5xx"}[5m]))
  / sum(rate(http_requests_total[5m]))
  > 0.01
```

### **4.4 Trace-Based Sampling**
```yaml
# OpenTelemetry sampler config (head-based with probability)
sampler:
  decision_wait: 100ms
  type: "probabilistic"
  parameter: 0.01  # 1% sampling
```

---

## **5. Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Observability Tiering](link)** | Isolates monitoring for dev/prod/pre-prod environments.                     | Multi-environment deployments with varied SLOs.                                 |
| **[Signal Correlation](link)** | Links metrics, logs, and traces for root-cause analysis.                     | Complex distributed failures (e.g., database timeouts).                         |
| **[Canary Monitoring](link)** | Gradually rolls out monitoring to a subset of traffic.                       | Feature flags or blue-green deployments.                                       |
| **[Cost-Based Scaling](link)** | Balances monitoring overhead against operational costs.                       | Cloud-native apps with budget constraints.                                     |
| **[SLO-Driven Alerting](link)** | Alerts tied to business-critical metrics (e.g., "99.9% latency < 500ms").     | High-stakes applications (e.g., e-commerce checkout).                           |

---

## **6. Anti-Patterns to Avoid**
1. **Over-Sampling**:
   - *Problem*: Ingesting 100% of metrics for all services leads to storage bloat.
   - *Fix*: Use **adaptive sampling** (e.g., `0.1` for low-traffic services).

2. **Full-Resolution Long-Term Storage**:
   - *Problem*: Storing 1-second metrics for 1 year consumes excessive space.
   - *Fix*: **Multi-resolution storage** (e.g., 1m for >7 days).

3. **Ignoring Query Performance**:
   - *Problem*: Complex PromQL queries on high-cardinality data time out.
   - *Fix*: **Pre-aggregate** or use `rate()` instead of `increase()`.

4. **Static Alert Thresholds**:
   - *Problem*: Alerts trigger unnecessarily during traffic spikes.
   - *Fix*: **Dynamic thresholds** or **SLO-based alerting**.

5. **Silos Across Teams**:
   - *Problem*: DevOps and developers use separate monitoring tools.
   - *Fix*: **Shared observability** with consistent labeling (e.g., `team`, `environment`).

---
**Next Steps**:
- [ ] Audit current monitoring load with `promtool`.
- [ ] Implement sampling rules for top 3 high-cardinality services.
- [ ] Set up multi-resolution storage in Thanos/TimescaleDB.
- [ ] Test alert queries under load (e.g., using `prometheus pushgateway`).