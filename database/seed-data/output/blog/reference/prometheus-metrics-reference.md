---

# **[Pattern] Prometheus Metrics Integration Patterns – Reference Guide**

---

## **Overview**
Prometheus is a powerful open-source monitoring tool for collecting, retrieving, and alerting on metrics from applications, infrastructure, and services. This reference guide outlines **best-practice integration patterns** for exposing, collecting, and querying metrics using Prometheus. It covers:
- **Exposition formats** (e.g., HTTP scraping, pushgates, remote write)
- **Common metric types** (gauges, counters, histograms, summaries)
- **Implementation strategies** (language-specific libraries, custom setups)
- **Performance considerations** (sampling, labeling, retention)
- **Troubleshooting** (common errors, debugging, and validation)

This guide assumes familiarity with Prometheus basics (e.g., `scrape_config`, `relabeling`) but provides actionable details for production deployments.

---

## **1. Core Schema Reference**
Prometheus metrics follow a **time-series** model, where each metric is identified by:
- **Name**: Required (e.g., `http_requests_total`).
- **Labels**: Key-value pairs for filtering (e.g., `method="GET"`, `service="api"`).
- **Value**: A numeric sample (e.g., `42.5`) at a specific timestamp.
- **Type**: Defines how the metric behaves over time (`counter`, `gauge`, `histogram`, `summary`, etc.).

| **Attribute**       | **Description**                                                                 | **Example**                          | **Notes**                                  |
|---------------------|-------------------------------------------------------------------------------|---------------------------------------|--------------------------------------------|
| **Metric Name**     | Unique identifier for the metric (use reverse-DNS notation for namespaces).   | `app.requests.total`                  | Must match scraping targets.               |
| **Labels**          | Dimensions for filtering/aggregation (e.g., `status`, `job`).                | `{status="200", job="web-server"}`    | Limit to 60 labels; use `relabeling` for renaming. |
| **Value Type**      | Defines metric semantics:                                                |                                       |                                            |
| - `counter`         | Monotonically increasing (e.g., event counts).                             | `http_requests_total`                 | Reset on restart (use `increments()`).      |
| - `gauge`           | Can increase/decrease (e.g., memory usage).                               | `memory.usage_bytes`                  | Supports manual updates.                   |
| - `histogram`       | Samples + buckets for distribution analysis.                               | `http_duration_seconds_bucket`        | Requires `sum` and `count` sub-metrics.    |
| - `summary`         | Quantile-based sampling (e.g., latency percentiles).                        | `http_request_duration_seconds`       | Less precise than histograms.               |
| **Timestamp**       | Unix epoch in seconds (Prometheus aligns to 15s by default).               | `1712345678`                          | Precision: ±1s (default scrape interval).    |
| **Exposition Format** | How metrics are served (default: `/metrics` endpoint).                   | `text/plain` (Prometheus format)      | Custom formats: JSON, OpenMetrics.         |
| **Sampling Rate**   | Scrape interval (default: 15s).                                           | `scrape_interval: 30s`                | Lower values increase load; higher values reduce freshness. |
| **Relabeling Rules**| Transform labels before ingestion (e.g., replace `host` with `pod`).      | `relabel_configs: - source_labels: [__address__] regex: '([^:]+):'` | Use `target_label` to preserve/drop labels. |

---

## **2. Implementation Patterns**

### **2.1. Scraping via HTTP (`/metrics` Endpoint)**
Prometheus scrapes metrics by HTTP GET requests to configured targets.
**Key Steps:**
1. **Expose Metrics**:
   - Use language libraries (e.g., `prometheus-client` for Go, `prometheus-python` for Python) to scrape `/metrics`.
   - Example Go endpoint:
     ```go
     func main() {
         reg := prometheus.NewRegistry()
         counters := prometheus.NewCounterVec(
             prometheus.CounterOpts{
                 Name: "http_requests_total",
                 Help: "Total HTTP requests processed.",
             },
             []string{"method", "endpoint"},
         )
         reg.MustRegister(counters)
         http.Handle("/metrics", promhttp.HandlerFor(reg, promhttp.HandlerOpts{}))
         log.Fatal(http.ListenAndServe(":8080", nil))
     }
     ```
   - Validate with `curl http://<host>:8080/metrics | grep http_requests_total`.

2. **Configure Scraping in Prometheus**:
   ```yaml
   scrape_configs:
     - job_name: "api"
       static_configs:
         - targets: ["app:8080"]
           labels:
             env: "production"
   ```

### **2.2. Push-Based Integration (Pushgates)**
Use cases: High-volume producers (e.g., IoT devices) where scraping is impractical.
**How it Works**:
- Application **pushes** metrics to a Pushgate proxy.
- Prometheus scrapes the Pushgate endpoint.
**Example Setup**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: "pushgates"
    scrape_interval: 15s
    metrics_path: "/metrics"
    static_configs:
      - targets: ["pushgateway:9091"]
```

**Client-Side Push (Python)**:
```python
from prometheus_client import push_to_gateway
push_to_gateway('pushgateway:9091', job='app-metrics', gauge=Gauge('app_version', 'Current version'))
```

### **2.3. Remote Write (Time-Series Databases)**
For large-scale collections (e.g., 10K+ instances), offload writes to a remote system like:
- **Thanos**, **Cortex**, or **VictoriaMetrics**.
**Configuration**:
```yaml
remote_write:
  - url: "http://thanos:1929/api/v1/receive"
    queue_config:
      capacity: 1000
      max_shards: 200
      max_samples_per_send: 1000
```

---
### **2.4. Custom Metric Types**
| **Type**       | **Use Case**                          | **Prometheus Metric**          | **Implementation Notes**                          |
|-----------------|---------------------------------------|----------------------------------|---------------------------------------------------|
| **Simple Gauge** | Current value (e.g., CPU usage).     | `cpu_usage_percent`              | Update via `gauge.Set()`.                         |
| **Counter**     | Event counts (e.g., failed logins).   | `login_failures_total`           | Increment with `counter.Inc()`.                   |
| **Histogram**   | Latency distributions.                | `request_latency_seconds_bucket` | Define buckets (e.g., `[0.1, 0.5, 1, 5]`).        |
| **Summary**     | Quantiles (e.g., p99 latency).        | `request_latency_seconds_sum`    | Use for high-cardinality metrics.                 |

**Example Histogram (Go)**:
```go
hist := prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "HTTP request latency in seconds.",
        Buckets: prometheus.DefBuckets,
    },
    []string{"method", "status"},
)
reg.MustRegister(hist)
// Record latency:
hist.WithLabelValues("GET", "200").Observe(0.5)
```

---
## **3. Query Examples**
Prometheus Query Language (PromQL) uses time-series expressions.

### **3.1. Basic Queries**
| **Query**                                      | **Purpose**                                  | **Example Output**                     |
|------------------------------------------------|-----------------------------------------------|-----------------------------------------|
| `http_requests_total`                          | Raw request count.                            | `1242`                                  |
| `rate(http_requests_total[5m])`                | Requests per second (5m window).              | `8.2`                                   |
| `sum(rate(http_requests_total[1m])) by (endpoint)` | Endpoint-level rates.                     | `{endpoint="/health"} 4.1`              |
| `histogram_quantile(0.95, rate(http_duration_seconds_bucket[5m]))` | 95th-percentile latency.                     | `0.324`                                 |
| `irate(http_requests_total[1m]) > 100`        | Alert if >100 requests/sec.                   | `true`/`false`                          |

### **3.2. Aggregations**
| **Aggregation**                         | **Query**                                  | **Use Case**                          |
|------------------------------------------|--------------------------------------------|---------------------------------------|
| **Group by label**                      | `sum(http_requests_total) by (status)`     | Breakdown by HTTP status codes.       |
| **Global sum**                          | `sum(http_requests_total)`                 | Total requests across all instances.   |
| **Time-based avg**                       | `avg_over_time(http_requests_total[1h])`   | Hourly averages.                      |
| **Anomaly detection**                    | `rate(http_requests_total[5m]) > 0.9 * avg_over_time(rate(http_requests_total[5m])[7d])` | Detect 10% traffic spikes. |

### **3.3. Alerting Rules**
```yaml
# alert_rules.yaml
groups:
- name: "api-alerts"
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: "critical"
    annotations:
      summary: "High error rate on {{ $labels.job }}"
```

---
## **4. Best Practices & Pitfalls**
### **4.1. Best Practices**
1. **Labeling**:
   - Use meaningful labels (e.g., `service`, `pod`, `region`).
   - Avoid high-cardinality labels (e.g., `user_id`). Aggregate if needed.
2. **Sampling**:
   - Start with `scrape_interval: 30s`; adjust based on load.
   - Use `sample_limit` to cap high-cardinality metrics.
3. **Metric Naming**:
   - Follow [Prometheus naming guidelines](https://prometheus.io/docs/practices/naming/).
   - Example: `app_name_subsystem_metric_type{labels}`.
4. **Retention**:
   - Configure `retention.time` (default: 15d) in Prometheus.
   - For long-term storage, use Thanos/Cortex.
5. **Rate vs. Instant**:
   - Use `rate()` for counters; `increase()` for historical comparisons.

### **4.2. Common Pitfalls**
| **Issue**                          | **Cause**                                  | **Fix**                                  |
|-------------------------------------|--------------------------------------------|------------------------------------------|
| High scrape load                    | Too many short-lived containers.           | Use `scrape_timeout: 10s`; batch metrics. |
| Label cardinality explosion         | Too many unique labels (e.g., `pod:1000`). | Aggregate with `group_by` in alerts.     |
| Counter resets                      | Service restarts trigger drops.            | Use `increase(counters[1h])` for trends. |
| Missing metrics                     | Misconfigured `/metrics` endpoint.        | Test with `curl -v http://host/metrics`. |
| Thanos/Cortex ingestion delays      | High write volume.                         | Increase `remote_write` queue capacity. |

---

## **5. Related Patterns**
1. **[Observability Patterns: Logging]**
   - Combine metrics with logs (e.g., correlate `error` metrics with log traces).
   - *Tools*: Loki, OpenTelemetry.

2. **[Service Discovery]**
   - Dynamic target management (e.g., Kubernetes `kube-state-metrics`).
   - *Tools*: Consul, etcd, Kubernetes Service Endpoints.

3. **[Alerting & Incident Management]**
   - Extend Prometheus alerts with Slack/PagerDuty integrations.
   - *Tools*: Alertmanager, Opsgenie.

4. **[Cost Optimization]**
   - Right-size scrape intervals for cost-sensitive environments (e.g., serverless).

5. **[OpenTelemetry Integration]**
   - Export metrics to Prometheus via OTLP (OpenTelemetry Protocol).
   - Example:
     ```yaml
     remote_write:
       - url: "http://otlp-collector:4317"
         otlp:
           metrics_endpoint: "/v1/metrics"
     ```

---
## **6. Further Reading**
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenMetrics Spec](https://github.com/OpenObservability/OpenMetrics)
- [Thanos Documentation](https://thanos.io/)
- [Kubernetes Metrics Server](https://github.com/kubernetes-sigs/metrics-server)