---
# **[Pattern] Reference Guide: Metrics Collection & Visualization**

---

## **1. Overview**
**Metrics Collection & Visualization** is a foundational software engineering pattern for capturing, storing, processing, and presenting quantitative data about system performance, behavior, and health. This pattern ensures data-driven decision-making, performance tuning, and proactive issue detection by providing structured workflows for collecting raw telemetry (e.g., CPU, memory, latency) and transforming it into actionable insights via dashboards, alerts, and reports.

Key objectives include:
- **Completeness**: Instrumenting all critical components (applications, infrastructure, databases).
- **Scalability**: Handling high-throughput telemetry without performance degradation.
- **Interpretability**: Visualizing metrics with context to identify trends or anomalies.
- **Retention**: Balancing cost vs. retention policies for long-term analysis.

Target audiences include DevOps engineers, SREs, data analysts, and application developers responsible for monitoring and observability.

---

## **2. Schema Reference**
The following table outlines core components and their attributes. Assign IDs for referencing in queries or configurations.

| **Category**            | **Component**               | **Attributes**                                                                                     | **Example Values**                                                                                     | **Notes**                                                                                     |
|-------------------------|-----------------------------|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Data Sources**        | Metric Source               | `id`, `type` (e.g., `APP`, `INFRA`, `DB`), `tags` (KV pairs), `sampling_rate` (integer)          | `type=APP`, `tags={"env":"prod","app":"payments"}`                                                   | High-cardinality tags require careful indexing (see [Tagging Best Practices](#best-practices)).   |
|                         | Metric Definition           | `id`, `name` (human-readable), `unit`, `description`, `gauge/rate/counter` type                | `name="HTTP 5xx errors", unit="count", type="counter`                                                | Metric types define aggregation behavior (e.g., counters reset vs. gauges).                      |
| **Ingestion**           | Ingestion Pipeline          | `id`, `source_id`, `processor` (e.g., `fluentd`, `openTelemetry`), `batch_interval` (seconds)     | `processor="otel-collector", batch_interval=10`                                                      | Batch intervals trade off latency vs. throughput.                                                 |
|                         | Data Transformer            | `id`, `source_id`, `policy` (e.g., `downsampling`, `anomaly_detection`)                           | `policy="downsampling:1m->5m"`                                                                      | Transformers modify data before storage.                                                         |
| **Storage**             | Data Storage                | `id`, `backend` (e.g., `Prometheus`, `InfluxDB`, `TimescaleDB`), `retention_policy` (e.g., `7d`)  | `backend="timescaledb", retention_policy="30d"`                                                      | Timescaledb excels at time-series with SQL; Prometheus favors high-cardinality metrics.           |
|                         | Queryable View              | `id`, `storage_id`, `sql_query` (for derived metrics)                                             | `sql_query="SELECT AVG(value) FROM http_errors WHERE path='api/users' GROUP BY time_bucket('1h')"   | Views enable ad-hoc analysis without duplicating data.                                          |
| **Visualization**       | Dashboard                  | `id`, `storage_id`, `widgets` (array of `widget_id`, `type`, `params`)                          | `widgets=[{type:"line", params:{metric_id:"cpu_usage"}}]`                                            | Dashboards in Grafana/Prometheus can use templating for dynamic queries.                        |
|                         | Alert Rule                 | `id`, `metric_ids` (array), `threshold` (e.g., `{ "gt": 90 }`), `severity` (e.g., `CRITICAL`)     | `metric_ids=["latency_p99"], threshold={ "gt": 500 }, severity="HIGH"`                            | Integrate with tools like PagerDuty/Opsgenie for notifications.                                |

---

## **3. Implementation Workflow**

### **3.1 Collect Metrics**
**Sources**: Instrument applications (e.g., OpenTelemetry auto-instrumentation), infrastructure agents (e.g., Prometheus Node Exporter), or logs (e.g., Fluentd parsing).

**Key Steps**:
1. **Define Metrics**: Use semantic conventions (e.g., `http_server_requests_total` from OpenTelemetry).
2. **Instrument Code**:
   ```python
   from opentelemetry import metrics
   meter = metrics.get_meter("app.metrics")
   request_counter = meter.create_counter("http_requests_total", "HTTP request count")
   request_counter.add(1, {"method": "GET", "path": "/users"})
   ```
3. **Agent Configuration**:
   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: 'app'
       static_configs:
         - targets: ['localhost:8080']  # Metrics endpoint
   ```

### **3.2 Process & Store**
**Pipelines**: Use tools like Prometheus, Telegraf, or OpenTelemetry Collector to:
- **Aggregate**: Downsample metrics (e.g., `http_errors` from 1s to 5m).
- **Enrich**: Add metadata (e.g., business context via labels).
- **Filter**: Discard irrelevant data early (e.g., `drop_tags=["debug"]`).

**Storage**:
| **Backend**       | **Use Case**                          | **Query Language**       | **Pros**                                  | **Cons**                                  |
|--------------------|---------------------------------------|--------------------------|-------------------------------------------|-------------------------------------------|
| **Prometheus**     | Real-time alerts, short-term storage  | PromQL                   | Pull-based, rich aggregations             | No native long-term retention             |
| **InfluxDB**       | Time-series with SQL                   | Flux/InfluxQL            | Flexible SQL, high write throughput       | Complex scaling for high cardinality      |
| **TimescaleDB**    | Hybrid time-series + SQL analytics     | PostgreSQL               | Full SQL power                            | Higher storage cost                       |
| **BigQuery**       | Large-scale analytics                  | Standard SQL             | Serverless, petabyte-scale               | Cold query latency                         |

**Example Query (PromQL)**:
```promql
# Average latency over 5-minute windows
100 * avg by (route) (rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))
```

### **3.3 Visualize & Alert**
**Dashboards**:
- **Grafana**: Use variables for dynamic panel updates.
  ```yaml
  # dashboard variables
  variables:
    env:
      values: ['prod', 'staging']
      label: Environment
  ```
- **Prometheus**: Static dashboards with pre-defined queries.

**Alerts**:
```yaml
# Prometheus alert rule
groups:
- name: latency-alerts
  rules:
  - alert: HighLatency
    expr: rate(http_request_duration_seconds{quantile="0.99"}>1)[5m]
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High P99 latency on {{ $labels.route }}"
```

---

## **4. Query Examples**
### **4.1 Aggregations**
**Problem**: Find the top 3 API endpoints by error rate.
**PromQL**:
```promql
topk(3, sum(rate(http_server_errors_total[5m])) by (route) /
     sum(rate(http_server_requests_total[5m])) by (route))
```

**InfluxQL**:
```sql
SELECT
    "route",
    sum("errors") / sum("requests")
FROM "http_errors"
GROUP BY "route"
ORDER BY DESC LIMIT 3
```

### **4.2 Time-Series Analysis**
**Problem**: Identify anomalies in database connection time.
**SQL (TimescaleDB)**:
```sql
SELECT
    time_bucket('1m', time) AS bucket,
    avg(connection_time_ms),
    "threshold" = avg(connection_time_ms) > 1000
FROM "db_connections"
WHERE time > now() - interval '7 days'
GROUP BY bucket
ORDER BY bucket;
```

### **4.3 Correlations**
**Problem**: Correlate CPU usage with error spikes.
**Grafana Example**: Use a dual-axis panel with:
- Left Y-axis: `sum(rate(http_errors_total[5m]))`
- Right Y-axis: `avg(rate(jvm_memory_bytes_used{area="heap"}[5m]))`

---

## **5. Best Practices**

### **5.1 Tagging & Labeling**
- **Limit cardinality**: Avoid combinatorial explosion (e.g., `host`, `service` are safe; `user_id` is not).
- **Use prefixes**: `env=prod` instead of `environment=production`.

### **5.2 Sampling**
- **High cardinality**: Sample metrics like `user_id` (e.g., `sample 0.1`).
- **Real-time**: Use lower sampling for low-frequency metrics (e.g., `1m` instead of `1s`).

### **5.3 Storage Optimization**
- **Retention**: Use shorter retention (e.g., 7 days) for volatile metrics, longer (e.g., 90 days) for business KPIs.
- **Compression**: Enable Prometheus’s `retention.time` + `retention.size`.

### **5.4 Visualization**
- **Contextualize**: Add reference lines (e.g., SLO thresholds).
- **Multi-panel**: Combine time-series with histograms (e.g., request sizes).

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **Reference Guide Link**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **[Observability Stack]**  | Holistic approach combining metrics, logs, and traces.                                               | [Observability Stack](link)                                                              |
| **[Distributed Tracing]** | End-to-end request tracing for latency analysis.                                                    | [Distributed Tracing](link)                                                              |
| **[Logging Pattern]**     | Structured logging for correlation with metrics.                                                    | [Logging Pattern](link)                                                                  |
| **[Performance Tuning]**  | Uses metrics to identify and resolve bottlenecks.                                                  | [Performance Tuning](link)                                                              |
| **[Cost Monitoring]**     | Tracks cloud spend via metrics like `aws_billed_resources`.                                        | [Cost Monitoring](link)                                                                |

---

## **7. Anti-Patterns**
| **Anti-Pattern**          | **Problem**                                                                                       | **Solution**                                                                               |
|---------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Over-collecting**       | High cardinality metrics overwhelm storage/queries.                                               | Use sampling, anonymize PII, adhere to [Google’s Metric Naming](https://cloud.google.com/blog/products/management-tools/naming-and-tagging-guidelines-for-cloud-monitoring-metrics). |
| **Static Thresholds**     | Alerts trigger only when metrics cross fixed values (e.g., >90% CPU).                              | Use statistical methods (e.g., [Slack/Doug’s method](https://landing.google.com/sre/sre-book/table-of-contents/ch03.html#alarm-design)). |
| **Ignoring Retention**    | Unlimited retention bloats storage costs.                                                          | Enforce retention policies (e.g., Prometheus’s `retention` config).                       |
| **No Context**           | Metrics lack labels/tags for downstream analysis.                                                   | Standardize tags (e.g., `env`, `service`, `version`) and avoid ad-hoc labels.             |
| **Alert Fatigue**         | Too many alerts reduce reliability (e.g., 50+ per engineer/day).                                    | Prioritize alerts with severity levels and auto-remediation where possible.                 |