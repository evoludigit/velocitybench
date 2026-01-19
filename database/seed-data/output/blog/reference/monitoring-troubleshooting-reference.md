---
**[Pattern] Monitoring Troubleshooting – Reference Guide**
*Technical Documentation*

---

### **1. Overview**
The **Monitoring Troubleshooting** pattern provides a structured approach to identifying, diagnosing, and resolving performance degradation, failures, or anomalies in distributed systems. This pattern combines:
- **Proactive health checks** (e.g., alerts, dashboards).
- **Root cause analysis** (e.g., tracing, logs, metrics).
- **Automated remediation** (e.g., failover, scaling).

It’s critical for SREs, DevOps engineers, and observability teams ensuring system reliability by bridging monitoring data with troubleshooting workflows.

---

### **2. Key Concepts**
| **Term**               | **Definition**                                                                 | **Example Tools**                     |
|------------------------|-------------------------------------------------------------------------------|---------------------------------------|
| **Metrics**            | Quantitative data (e.g., CPU usage, latency) used to measure system health.   | Prometheus, Datadog                  |
| **Logs**               | Textual records of system events for debugging.                              | ELK (Elasticsearch, Logstash, Kibana) |
| **Traces**             | End-to-end request flows (e.g., distributed tracing) for latency analysis.   | Jaeger, OpenTelemetry                 |
| **Alerts**             | Notifications triggered by anomaly thresholds (e.g., error rates > 1%).        | PagerDuty, Opsgenie                   |
| **SLOs/SLIs**          | Service Level Objectives (e.g., "99.9% request latency < 500ms") and Indicators. | Google SLOs, CloudWatch SLOs         |
| **Autoscaling**        | Dynamic resource allocation to mitigate bottlenecks.                          | Kubernetes HPA, AWS Auto Scaling      |
| **Canary Releases**    | Gradual deployment to isolate failures.                                      | Istio, Flagger                       |
| **Blame Assignment**   | Attributing incidents to specific services/teams (e.g., "DB latency spikes"). | JIRA, ServiceNow                     |

---

### **3. Schema Reference**
#### **A. Core Components**
| **Component**          | **Fields**                                                                 | **Description**                                                                 |
|------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Alert Rule**         | `name`, `threshold`, `severity`, `trigger`, `action`                     | Defines alert policies (e.g., `CPU > 90% for 5 mins`).                          |
| **Metric**             | `name`, `value`, `timestamp`, `unit`, `labels`                           | Example: `http_requests_total{status="5xx"}`                                    |
| **Log Entry**          | `timestamp`, `level`, `service`, `message`, `context`                     | Structured logs: `{"level":"ERROR","service":"api-gateway","message":"503"}`   |
| **Trace Span**         | `span_id`, `operation`, `start_time`, `end_time`, `duration`              | Distributed tracing span: `{span_id: "abc123", operation: "auth-check"}`         |
| **Incident Ticket**    | `id`, `status`, `created_at`, `resolved_at`, `root_cause`                | Tracks issues (e.g., `status: "investigating"`, `root_cause: "network partition"`). |

#### **B. Relationships**
- **Alert → Incident**: Alerts escalate to tickets if unresolved (e.g., `Alert ID: #42 → Ticket: INC-123`).
- **Trace → Bottleneck**: Traces link to metrics (e.g., a 2-second `db_query` span correlates with `db_latency_metrics`).
- **Log → Error Type**: Logs classify errors (e.g., `500 errors` → `log_pattern: "databaseConnectionTimeout"`).

---

### **4. Implementation Workflow**
#### **Step 1: Instrumentation**
- **Metrics**: Export Prometheus metrics (e.g., `http_request_duration_seconds`).
  ```python
  # Example: Instrumenting a Flask app
  from prometheus_client import make_wsgi_app, Counter
  REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
  @app.route('/')
  def home():
      REQUEST_COUNT.inc()
      return "Hello"
  app.wsgi_app = make_wsgi_app()
  ```
- **Logs**: Use structured JSON logs (e.g., `{"event": "failed_login", "user": "john"}`).
- **Traces**: Instrument with OpenTelemetry SDKs.
  ```java
  // OpenTelemetry auto-instrumentation (Java)
  InstrumentationConfig instrumentationConfig = InstrumentationConfig.builder()
      .instrumentedTypes("com.example.MyClass")
      .build();
  TracerProvider provider = OpenTelemetrySdk.getTracerProvider();
  ```

#### **Step 2: Alerting**
Configure alerts in Prometheus (e.g., alert if `error_rate > 0.01`):
```yaml
groups:
- name: error-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status="5xx"}[1m]) > 0.01
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "5xx errors spiked"
```

#### **Step 3: Root Cause Analysis (RCA)**
- **Tools**:
  - **Metrics**: Query PromQL:
    ```promql
    # Latency Percentiles (99th percentile)
    histograms_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
    ```
  - **Logs**: Aggregate logs in Kibana:
    ```
    kibana: ~"ERROR" AND service:api-gateway | stats count by status_code
    ```
  - **Traces**: Analyze slow spans in Jaeger:
    ```
    service:payment AND duration > 500ms
    ```
- **RCA Techniques**:
  - **Blame Assignment**: Use `labels` (e.g., `env:prod`, `service:payment`) to pinpoint sources.
  - **Correlation**: Cross-reference metrics/logs/traces (e.g., a `503` error in logs may correlate with `http_server_errors` in metrics).

#### **Step 4: Remediation**
- **Automated**:
  - **Auto-scaling**: Trigger HPA based on CPU:
    ```yaml
    # Kubernetes HPA
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    ```
  - **Canary Rollouts**: Use Flagger to detect failures in new deployments.
- **Manual**:
  - **Incident Tickets**: Assign to the team owning the affected service (e.g., `database` team).
  - **Postmortems**: Document root causes and mitigation plans in a wiki (e.g., Confluence).

---

### **5. Query Examples**
#### **PromQL (Metrics)**
```promql
# 1. Errors per endpoint
sum(rate(http_requests_total{status=~"5.."}[1m])) by (route)

# 2. Latency spikes
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# 3. Alert when metric violates SLO
rate(db_query_latency_seconds{environment="prod"}[5m]) > 100
```

#### **Elasticsearch (Logs)**
```json
# Query: Find 4xx errors in the last hour
GET /logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "range": { "@timestamp": { "gte": "now-1h" } } },
        { "term": { "status_code": "4xx" } }
      ]
    }
  }
}
```

#### **Jaeger (Traces)**
```plaintext
# CLI: Find slow traces in the payment service
jaeger query traces \
  --service=payment \
  --duration=30s \
  --sort-by=duration \
  --limit=10
```

---

### **6. Common Pitfalls & Best Practices**
| **Pitfall**                          | **Best Practice**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------|
| **Alert Fatigue**                     | Set realistic thresholds (e.g., use SLOs to define "critical").                  |
| **Noisy Logs**                        | Enforce structured logging (e.g., JSON) and filter by severity.                  |
| **Overhead from Traces**              | Sample traces (e.g., 1% of requests) and exclude low-value services.              |
| **Unclear Ownership**                 | Assign SLOs per team/service (e.g., `database-team` owns `db_latency`).         |
| **Manual RCA**                        | Use correlation tools (e.g., Grafana, Datadog) to link metrics/logs/traces.      |

---

### **7. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                  |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **Circuit Breaker**       | Prevent cascading failures by stopping requests to unhealthy services.     | High-latency dependencies (e.g., payment APIs).   |
| **Rate Limiting**         | Protect APIs from overload by throttling requests.                        | Public-facing APIs (e.g., `/login`).              |
| **Chaos Engineering**     | Proactively test system resilience by injecting failures.                   | Pre-launch reliability testing.                    |
| **Distributed Tracing**   | Trace requests across microservices for latency analysis.                   | Debugging cross-service bottlenecks.              |
| **Canary Deployments**    | Gradually roll out changes to detect issues early.                          | Production deployments.                           |

---
**References**:
- Prometheus Documentation: [prometheus.io](https://prometheus.io/docs/prometheus/latest/querying/)
- OpenTelemetry: [opentelemetry.io](https://opentelemetry.io/docs/)
- SRE Book (Google): [sre.google/sre-book/](https://sre.google/sre-book/table-of-contents/)