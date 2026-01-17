**[Pattern] Reliability Monitoring Reference Guide**

---

### **1. Overview**
The **Reliability Monitoring** pattern enables organizations to continuously measure and track the availability, performance, and resilience of critical systems, services, or applications. By collecting and analyzing metrics—such as error rates, latency, uptime, and resource utilization—this pattern helps detect, diagnose, and mitigate failures before they affect end users. Reliability monitoring integrates with logging, alerting, and root-cause analysis systems to proactively improve system stability, reduce downtime, and ensure business continuity.

Key use cases include:
- Proactive issue detection (e.g., spikes in error rates).
- Performance optimization (e.g., identifying bottlenecks).
- Compliance validation (e.g., meeting uptime SLAs).
- Incident response (e.g., correlating metrics with logs).

---

### **2. Key Components**
Reliability monitoring relies on the following core components (see **Schema Reference** below for implementation details):

| **Component**          | **Description**                                                                 | **Example Metrics**                          |
|------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Telemetry Sources**  | Collect runtime data from systems (logs, metrics, traces).                     | CPU usage, disk I/O, HTTP request latency   |
| **Aggregation Layer**  | Process and store metrics (e.g., time-series databases).                        | 99th percentile latency, error count        |
| **Alerting System**    | Notify teams when metrics exceed thresholds (e.g., Prometheus + Alertmanager). | High error rates, service unavailability    |
| **Dashboards**         | Visualize trends (e.g., Grafana).                                               | Uptime %, request success rate              |
| **Anomaly Detection**  | Identify unusual patterns (e.g., ML-based tools like Datadog or New Relic).    | Sudden traffic spikes                       |
| **Incident Linking**   | Correlate metrics with logs/traces for root-cause analysis (e.g., OpenTelemetry). | Latency spikes + Nginx 5xx errors           |

---

### **3. Schema Reference**
Below is a normalized schema for a reliability monitoring system (adapt as needed for your infrastructure):

| **Field**               | **Type**      | **Description**                                                                 | **Example Values**                          |
|-------------------------|---------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `system_id`             | String        | Unique identifier for a monitored system (e.g., "order-service:prod").         | `"ecommerce-api:us-east-1"`                 |
| `metric_name`           | String        | Name of the metric (e.g., "http_request_duration").                             | `"database_query_latency"`                  |
| `metric_type`           | Enum          | Type of metric (e.g., "gauge", "counter", "histogram").                        | `"counter"`                                 |
| `value`                 | Number/Bool   | Numeric value or boolean status (e.g., uptime).                                | `42.3`, `true`                              |
| `timestamp`             | ISO 8601      | When the metric was recorded.                                                    | `"2024-01-15T12:00:00Z"`                   |
| `unit`                  | String        | Units of measurement (e.g., "ms", "requests").                                  | `"milliseconds"`, `"errors"`                |
| `labels`                | Key-Value Map | Dimensional filters (e.g., `service="auth-service"`, `env="staging"`).         | `{"env": "prod", "endpoint": "/login"}`     |
| `alert_threshold`       | Object        | Conditions for alerts (e.g., `{ "value": 1000, "duration_sec": 300 }`).         | `{"error_count": 5, "window": "5m"}`        |
| `sla_metric`            | Boolean       | `true` if this metric contributes to an SLA (e.g., uptime).                    | `true`                                      |
| `anomaly_score`         | Number        | Scored anomaly risk (0–100) from detection tools.                              | `78.2`                                      |

**Example Record:**
```json
{
  "system_id": "payment-gateway:prod",
  "metric_name": "http_request_latency",
  "metric_type": "histogram",
  "value": 312.5,
  "timestamp": "2024-01-15T12:05:00Z",
  "unit": "milliseconds",
  "labels": {"endpoint": "/charge", "region": "eu-west-1"},
  "alert_threshold": {"value": 500, "duration_sec": 60},
  "sla_metric": true,
  "anomaly_score": 85.1
}
```

---

### **4. Implementation Details**
#### **A. Telemetry Collection**
- **Metrics**: Use agents (e.g., Prometheus Node Exporter) or SDKs (e.g., OpenTelemetry Python SDK) to emit metrics.
- **Logs**: Ship logs to centralized systems (e.g., ELK Stack, Loki) with structured fields (e.g., `level=error`, `service=auth`).
- **Traces**: Instrument critical paths with distributed tracing (e.g., Jaeger, Zipkin).

**Example (OpenTelemetry SDK for Python):**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("process_payment"):
    # Business logic
    pass
```

#### **B. Storage & Querying**
- **Time-Series Databases**: Use Prometheus (for metrics) or InfluxDB (for high-cardinality data).
- **Query Language**: PromQL (Prometheus) or InfluxQL (InfluxDB) for aggregations:
  ```promql
  # Alert if HTTP errors exceed 1% in 5-minute window
  rate(http_requests_total{status=~"5.."}[5m]) /
    rate(http_requests_total[5m]) > 0.01
  ```

#### **C. Alerting**
- Define thresholds in the telemetry system (e.g., Prometheus Alertmanager YAML):
  ```yaml
  - alert: HighErrorRate
    expr: rate(http_errors_total[5m]) > 1000
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "High error rate in {{ $labels.service }}"
  ```
- Integrate with PagerDuty, Slack, or email.

#### **D. Dashboards**
- **Grafana**: Visualize key reliability metrics with dashboards (e.g., uptime %, error trends).
- **Custom Dashboards**: Use Prometheus’s `record` rules to precompute SLA metrics:
  ```promql
  # Record uptime percentage
  record:job:uptime_percent{job="ecommerce-api"} 100 -
    avg_over_time(job:http_requests_total{job="ecommerce-api"}[1d])
    /
    (avg_over_time(job:http_requests_total{job="ecommerce-api"}[1d])
     + avg_over_time(job:http_requests_total{status=~"5.."}[1d]))
  ```

---

### **5. Query Examples**
#### **Prometheus Queries**
1. **Error Rate by Service**:
   ```promql
   sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
     /
   sum(rate(http_requests_total[5m])) by (service)
   ```
2. **Uptime Percentage**:
   ```promql
   100 * (1 - (sum(rate(up{job="*"}[5m])) == 0))
   ```
3. **Anomaly Detection (Statistical Thresholds)**:
   ```promql
   # Alert if latency > mean + 3*stddev
   rate(http_request_duration_seconds[5m]) >
    avg_over_time(rate(http_request_duration_seconds[5m]))[1d]
    + 3 * stddev_over_time(rate(http_request_duration_seconds[5m])[1d])
   ```

#### **InfluxQL Queries**
1. **Moving Average (7-day uptime)**:
   ```sql
   SELECT mean("value") FROM "metrics"
     WHERE "system_id" = 'payment-gateway:prod'
     AND "metric_name" = 'uptime'
     AND time > now() - 7d
     GROUP BY time(1d)
   ```

---

### **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                                  |
|---------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Distributed Tracing**   | Track requests across microservices using traces.                               | Debugging latency in cross-service flows.     |
| **Log-Based Monitoring**  | Analyze logs for patterns (e.g., error correlations).                          | Root-cause analysis of failures.              |
| **Circuit Breaker**       | Isolate failures in dependent services to prevent cascading outages.           | Resilient service-to-service communication.   |
| **Chaos Engineering**     | Proactively test system resilience by injecting failures.                      | Validate reliability under stress.            |
| **Observability Pipeline**| Combine metrics, logs, and traces for holistic insights.                       | Unified reliability monitoring.               |

---

### **7. Best Practices**
1. **Instrument Early**: Add telemetry to new services during development.
2. **Standardize Labels**: Use consistent labels (e.g., `env`, `service`) for querying.
3. **Set Realistic SLAs**: Align thresholds with business impact (e.g., 99.9% uptime for payments).
4. **Reduce Noise**: Tune alerts to avoid alert fatigue (e.g., use "alert state" logic).
5. **Retention Policy**: Archive old metrics (e.g., 30 days) to reduce storage costs.
6. **Automate On-Call**: Integrate monitoring with on-call rotation tools (e.g., Opsgenie).

---
### **8. Limitations**
- **Cardinality Explosion**: High-dimensional labels (e.g., `endpoint`, `user_id`) can overwhelm storage.
- **Latency in Alerts**: Aggregation layers may introduce delay in anomaly detection.
- **False Positives**: Thresholds may trigger alerts for non-critical issues (mitigate with adaptive thresholds).

---
**[End of Guide]** (~1,000 words)
*For deeper dives, see:*
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Alertmanager Config](https://prometheus.io/docs/alerting/latest/configuration/)
- [Grafana Reliability Dashboard Templates](https://grafana.com/grafana/dashboards/)