---
# **[Pattern] Metric Collection Patterns – Reference Guide**

---
## **1. Overview**
The **Metric Collection Patterns** define structured approaches to gathering, categorizing, and standardizing telemetry data (metrics) across distributed systems. This pattern ensures consistency, scalability, and observability by enforcing naming conventions, classification hierarchies, and aggregation strategies.

Metrics are critical for monitoring performance, resource utilization, and system health. Misalignment in collection methods can lead to:
- **Inconsistent data** (e.g., `request_latency_ms` vs. `requestLatencyMs`).
- **Overhead** from redundant or inefficient collection.
- **Observability gaps** due to missing or poorly categorized metrics.

This guide covers schemas, implementation best practices, and related patterns to standardize metric collection across microservices, containers, and hybrid cloud environments.

---

## **2. Key Concepts**
| **Concept**          | **Definition**                                                                 | **Example**                          |
|----------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Metric Type**      | Categorizes metrics by purpose (e.g., counter, gauge, histogram).             | `request_count` (counter), `cpu_usage` (gauge) |
| **Dimension**        | Key-value pairs tagging metrics (e.g., `service=<name>`, `region=<us-west>`).| `service=order-service; region=us-west` |
| **Metric Naming**    | Standardized `lowercase_with_underscores` convention for readability.       | `error_rate` (not `ErrorRate`)       |
| **Aggregation**      | How metrics are summed/averaged (e.g., per-second, per-minute rates).         | `requests_per_second`                |
| **Collection Granularity** | Frequency of data points (e.g., 1s, 5m, 1h).                               | `cpu_usage` every 30 seconds.        |

---

## **3. Schema Reference**
Metrics must adhere to the following schema to ensure interoperability:

### **3.1 Core Metric Structure**
| **Field**          | **Type**   | **Description**                                                                 | **Example**                          |
|--------------------|------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Name**           | `string`   | **Required**. Uses `lowercase_with_underscores`.                              | `http_requests_total`                |
| **Type**           | `enum`     | `counter`, `gauge`, `histogram`, `summary`, or `untyped`.                    | `counter`                            |
| **Dimensions**     | `map<string,string>` | Optional key-value pairs for filtering/multi-dimensional analysis. | `{service: "user-service", env: "prod"}` |
| **Unit**           | `string`   | Physical/logical unit (e.g., `bytes`, `seconds`). *Optional but recommended.* | `bytes`                              |
| **Description**    | `string`   | Human-readable purpose of the metric.                                        | `"Total HTTP requests routed"`       |
| **Tags**           | `list<string>` | Metadata (e.g., `source="backend"`, `severity="info"`).                     | `[source="backend"]`                 |

---

### **3.2 Supported Metric Types**
| **Type**      | **Behavior**                                                                 | **Use Case**                          |
|---------------|-----------------------------------------------------------------------------|---------------------------------------|
| **Counter**   | Monotonically increasing integer (e.g., event counts).                      | Request counts, errors.              |
| **Gauge**     | Instant value (e.g., memory usage, temperature).                            | CPU load, disk space.                |
| **Histogram** | Distributes values into buckets (e.g., latency percentiles).               | Request duration.                     |
| **Summary**   | Tracks min/max/avg/count over a time window.                                | Custom aggregations.                  |
| **Untyped**   | Generic string values (deprecated; prefer typed metrics).                   | Legacy systems.                       |

---

### **3.3 Example Metric Schemas**
#### **Counter (Request Counts)**
```json
{
  "name": "http_requests_total",
  "type": "counter",
  "dimensions": {"route": "/api/v1/users", "method": "POST"},
  "unit": "1",
  "description": "Total HTTP POST requests to /api/v1/users."
}
```

#### **Gauge (CPU Usage)**
```json
{
  "name": "cpu_usage_percent",
  "type": "gauge",
  "dimensions": {"service": "auth-service", "pod": "auth-pod-123"},
  "unit": "%",
  "description": "Current CPU utilization percentage."
}
```

#### **Histogram (Latency)**
```json
{
  "name": "request_latency_seconds",
  "type": "histogram",
  "dimensions": {"service": "payment-service"},
  "description": "Latency of payment processing requests (p99=1.2s).",
  "buckets": [0.1, 0.5, 1.0, 2.0]  // Customizable
}
```

---

## **4. Query Examples**
Use the following queries to extract insights from collected metrics (assuming a Prometheus-like query language).

### **4.1 Basic Aggregations**
| **Query**                                      | **Purpose**                              |
|-----------------------------------------------|------------------------------------------|
| `sum(http_requests_total)`                    | Total requests across all services.     |
| `avg(cpu_usage_percent)`                      | Average CPU usage.                       |
| `rate(http_requests_total[5m])`               | Requests per second (5-minute rate).     |

### **4.2 Filtering by Dimensions**
| **Query**                                      | **Purpose**                              |
|-----------------------------------------------|------------------------------------------|
| `http_requests_total{route="/api/v1/users"}`   | Filter requests to `/api/v1/users`.       |
| `sum by (service) (http_requests_total)`      | Requests per service.                    |
| `histogram_quantile(0.99, sum by (le) (rate(request_latency_seconds_bucket[1m])))` | P99 latency. |

### **4.3 Alerting Conditions**
| **Query**                                      | **Alert Trigger**                        |
|-----------------------------------------------|------------------------------------------|
| `rate(error_total[1m]) > 10`                  | >10 errors/minute.                       |
| `cpu_usage_percent > 90`                      | High CPU load.                          |
| `sum by (pod) (kube_pod_container_status_waiting{namespace="default"}) > 0` | Pods stuck in `Waiting` state.         |

---

## **5. Implementation Patterns**
### **5.1 Naming Conventions**
- **Prefixes**: Avoid vendor-specific prefixes (e.g., `aws_`, `gcp_`). Use standardized names.
  - ❌ `aws_cpu_utilization`
  - ✅ `cpu_usage_percent`
- **Avoid**:
  - Uppercase (`ErrorCount` → `error_count`).
  - Spaces/hyphens (`request latency` → `request_latency`).

### **5.2 Dimension Best Practices**
- **Keep dimensions sparse**: Limit to 3–5 key-value pairs max.
  - ✅ `service`, `env`, `version`
  - ❌ `service`, `env`, `version`, `team`, `project`, `region`
- **Standardize values**: Use consistent tags (e.g., `env=prod/staging/dev`).
- **Avoid sensitive data**: Exclude secrets (e.g., `db_password`) in dimensions.

### **5.3 Collection Frequency**
| **Use Case**               | **Recommended Granularity** |
|---------------------------|----------------------------|
| High cardinality (e.g., errors) | 1 minute                  |
| Low-cardinality gauges (e.g., memory) | 5–30 seconds       |
| Aggregated metrics (e.g., daily trends) | 1 hour or daily      |

---
## **6. Tools & Ecosystem**
| **Component**               | **Purpose**                                  | **Example Tools**                     |
|-----------------------------|---------------------------------------------|---------------------------------------|
| **Instrumentation**         | Embed metrics in code (SDKs, libraries).   | OpenTelemetry, Prometheus Client Libs |
| **Storage**                 | Store metrics for querying.                 | Prometheus, InfluxDB, TimescaleDB   |
| **Collection**              | Aggregate/scrape metrics from sources.      | Prometheus Server, Telegraf           |
| **Visualization**           | Dashboards/alerts.                          | Grafana, Datadog, New Relic          |
| **Processing**              | Enrich/transform metrics.                  | Fluentd, Metricbeat, PromQL           |

---

## **7. Related Patterns**
| **Pattern**                 | **Relationship**                                                                 | **When to Use Together**                     |
|-----------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **[Distributed Tracing]**   | Metrics complement traces by providing aggregated performance data.             | Analyzing latency spikes in microservices.   |
| **[Logging Patterns]**      | Logs provide raw events; metrics aggregate trends.                                | Correlating errors in logs with high-metric spikes. |
| **[Configuration as Code]** | Standardizes metric endpoints/naming across environments.                       | Deploying observability stacks consistently. |
| **[Observability Mesh]**    | Unified platform for metrics, logs, and traces.                                  | Consolidating telemetry in Kubernetes.      |

---
## **8. Anti-Patterns**
| **Anti-Pattern**               | **Risk**                                                                       | **Fix**                                    |
|---------------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| **Over-collecting**             | Noise from irrelevant metrics (e.g., `all_PID_stats`).                        | Stick to business-critical metrics.       |
| **Inconsistent Naming**         | `error_rate` vs. `errors_per_sec` in the same system.                         | Enforce schema via CI/CD.                 |
| **Ignoring Dimensions**         | Losing context (e.g., `cpu_usage` without `service`).                         | Tag all metrics with critical attributes.|
| **Untyped Metrics**             | Harder to query/aggregate.                                                    | Use `counter`/`gauge` instead of strings. |

---
## **9. Further Reading**
- [Prometheus Documentation: Metrics](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Schema](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/metrics/data-model.md)
- [SLOs & Error Budgets (Google SRE Book)](https://sites.google.com/a/google.com/srebook/)


---
**Version**: 1.0
**Last Updated**: `YYYY-MM-DD`
**License**: [MIT](https://opensource.org/licenses/MIT)