---
# **[Pattern] Monitoring & Profiling Reference Guide**

---
## **Overview**
The **Monitoring & Profiling** pattern enables real-time or near-real-time observation of application performance, resource utilization, and behavioral patterns to identify bottlenecks, inefficiencies, and degradation in system health. This pattern is critical for **debugging, capacity planning, and proactively optimizing** distributed systems, microservices, and large-scale applications.

Monitoring focuses on **collecting metrics, logs, and traces** at scale to track system behavior, while profiling provides **deep-dive insights** into performance bottlenecks (CPU, memory, I/O, etc.) via sampling, tracing, or instrumentation. Together, they form a defensive strategy to maintain reliability, improve user experience, and reduce operational overhead.

---
## **Schema Reference**

### **1. Core Concepts**
| **Component**         | **Description**                                                                                                                                                                                                                                         | **Key Attributes**                                                                                          |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Metric**            | A quantifiable observation of system behavior (e.g., request latency, error rate, throughput).                                                                                                                                                          | `name`, `type` (counter, gauge, histogram), `unit` (ms, %, calls/sec), `tags` (service, environment).       |
| **Log**               | A timestamped record of events, errors, or debug info.                                                                                                                                                                                                     | `timestamp`, `severity`, `message`, `context` (service, request ID).                                       |
| **Trace/Trace Span**  | A record of a request’s journey across services (e.g., distributed tracing).                                                                                                                                                                        | `span ID`, `operation`, `start/end timestamp`, `duration`, `tags` (HTTP status, dependencies).              |
| **Profile Sample**    | A snapshot of CPU, memory, or other resource usage at runtime (e.g., heap allocation, lock contention).                                                                                                                                           | `sample ID`, `timestamp`, `CPU`, `memory`, `events` (thread stacks, GC pauses).                           |
| **Alert Rule**        | A condition triggering notifications when metrics/logs exceed thresholds.                                                                                                                                                                      | `rule name`, `threshold`, `alert message`, `severity` (critical/warning/info), `notification channels`.    |
| **Dashboard**         | A visualized aggregation of metrics/logs for operational insights.                                                                                                                                                                             | `widget type` (graphs, tables), `query filters`, `time range`, `data source` (metrics, traces).           |

---

### **2. Data Flow Schema**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Application│ →  │  Agent/Proxy │ →  │  Collector  │ →  │  Storage    │
└───────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                  ▲                   ▲                      ▲
       │                  │                   │                      │
┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐    ┌───────────────┴───────────────┐
│  Metrics    │    │  Logs      │    │  Traces     │    │  Alerts/Dashboards (UI/API)     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────────────────────────┘
```

**Key Components:**
- **Agent/Proxy**: Instruments the app (e.g., OpenTelemetry, Prometheus Node Exporter) or sits between clients/services (e.g., Envoy).
- **Collector**: Aggregates and processes data (e.g., Prometheus, Loki, Jaeger).
- **Storage**: Persists data for long-term analysis (e.g., time-series DBs like InfluxDB, search engines like Elasticsearch).
- **UI/API**: Provides observability tools (e.g., Grafana, Datadog, New Relic).

---

## **Implementation Details**

### **1. Monitoring vs. Profiling**
| **Aspect**          | **Monitoring**                                                                 | **Profiling**                                                                 |
|---------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Purpose**         | Track system health and performance trends.                                   | Identify root causes of bottlenecks (e.g., hot methods, memory leaks).      |
| **Granularity**     | Coarse (e.g., request latency, error rates).                                 | Fine (e.g., per-thread CPU usage, heap allocations).                         |
| **Tools**           | Prometheus, Datadog, Cloud Monitoring.                                       | PPROF (Go), YourKit, VisualVM, Java Flight Recorder.                        |
| **Frequency**       | High (continuous or periodic).                                               | Low (triggered on anomalies or manually).                                    |
| **Output**          | Metrics, logs, traces.                                                       | CPU/memory profiles, flame graphs, event logs.                                |

---

### **2. Key Techniques**
#### **A. Metrics Collection**
- **Counters**: Track cumulative values (e.g., total requests).
- **Gauges**: Instantaneous values (e.g., active connections).
- **Histograms**: Distributional data (e.g., request latency percentiles).
- **Tagging**: Categorize metrics (e.g., `service=auth`, `env=prod`).

**Example (Prometheus):**
```yaml
# Example metric definition in code (Python with Prometheus Client)
from prometheus_client import Counter, Gauge, Histogram

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)
ERRORS = Counter('http_request_errors_total', 'Total HTTP errors')
```

#### **B. Logging**
- **Structured Logging**: Use JSON for machine-parsable logs (e.g., `{ "timestamp": "2024-05-20T12:00:00Z", "level": "ERROR", "service": "order-service", "message": "DB timeout" }`).
- **Sampling**: Reduce log volume (e.g., sample 1% of requests).
- **Correlation IDs**: Link logs across services using trace IDs.

**Example (OpenTelemetry):**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

trace.set_tracer_provider(TracerProvider())
trace.get_tracer(__name__).start_as_current_span("processing_order").end()
```

#### **C. Distributed Tracing**
- **Trace Context Propagation**: Attach trace IDs to requests (e.g., via headers).
- **Span Attributes**: Add contextual data (e.g., `http.method=POST`, `db.query=SELECT * FROM users`).
- **Tools**: Jaeger, Zipkin, AWS X-Ray.

**Example (Tracer Usage):**
```python
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("database_query") as span:
    span.set_attribute("query", "SELECT * FROM users")
    # Database call here
```

#### **D. Profiling**
- **CPU Profiling**: Identify slow methods (e.g., `pprof` in Go).
  ```bash
  go tool pprof http://localhost:6060/debug/pprof/profile
  ```
- **Memory Profiling**: Detect leaks (e.g., `go tool pprof http://localhost:6060/debug/pprof/heap`).
- **Flame Graphs**: Visualize call stacks (e.g., `flamegraph.pl`).
- **Event-based Profiling**: Capture runtime events (e.g., GC pauses, lock waits).

**Example (Java Flight Recorder):**
```bash
# Start recording
jfr start /path/to/profile.jfr
# Trigger profiling (e.g., via JMX or profiling events)
jfr stop
```

---

### **3. Alerting**
- **Threshold-Based Alerts**: Trigger when metrics exceed thresholds (e.g., `error_rate > 1%`).
- **Anomaly Detection**: Use ML (e.g., Prometheus Alertmanager + ML-based rules).
- **SLOs (Service Level Objectives)**: Define acceptable error budgets (e.g., 99.9% availability).

**Example (Prometheus Alert Rule):**
```yaml
groups:
- name: error-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[1m]) / rate(http_requests_total[1m]) > 0.01
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.instance }}"
```

---

## **Query Examples**

### **1. Prometheus Queries**
| **Use Case**                          | **Query**                                                                                     | **Example Output**                          |
|----------------------------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------|
| **HTTP Error Rate**                   | `rate(http_requests_total{status=~"5.."}[1m]) / rate(http_requests_total[1m])`               | `0.015` (1.5% errors)                       |
| **Latency Percentiles**               | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`      | `95th percentile latency: 250ms`             |
| **Active Connections**                | `process_resident_memory_bytes{job="backend"}`                                               | `8.2 GB`                                    |
| **Database Query Time**                | `rate(db_query_duration_seconds_sum[1m]) / rate(db_query_count[1m])`                         | `Avg query time: 80ms`                      |
| **Alert Condition**                   | `sum(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance) < 0.1`                     | `Node <instance:10.0.0.1> is overloaded`    |

---

### **2. Loki Log Queries**
| **Query**                          | **Description**                                                                 |
|------------------------------------|---------------------------------------------------------------------------------|
| `{job="api"} | line_format "{{.message}}"`           | Filter logs from the `api` job.                                                 |
| `{service=~"user|order"} severity=error`           | Search logs for errors in `user` or `order` services.                           |
| `| json`                           | Parse logs as JSON (if structured).                                             |
| `stacktrace`                       | Filter logs containing "stacktrace" (common for errors).                         |

---

### **3. Jaeger Trace Queries**
| **Query**                          | **Description**                                                                 |
|------------------------------------|---------------------------------------------------------------------------------|
| `service:user-service`             | Search traces for the `user-service`.                                           |
| `operation:authenticate`           | Filter traces where the operation is `authenticate`.                             |
| `duration:>100ms`                  | Find slow traces (>100ms).                                                       |
| `error:true`                       | Show traces with errors.                                                         |

---

### **4. PPROF Profiling Commands**
| **Command**                        | **Description**                                                                 |
|-------------------------------------|---------------------------------------------------------------------------------|
| `go tool pprof http://localhost:6060/debug/pprof/profile` | Load CPU profile from HTTP endpoint.       |
| `web`                               | Open flame graph in browser.                                                    |
| `list main.goroutine`               | List functions in a goroutine.                                                  |
| `top`                               | Show top-consuming functions.                                                    |
| `web top`                           | Generate HTML for top-consuming functions.                                      |

---

## **Best Practices**

1. **Instrumentation**:
   - Instrument at the **right level** (e.g., per-endpoint for latency, per-method for profiling).
   - Avoid **excessive overhead** (e.g., sample logs/traces instead of capturing everything).

2. **Data Management**:
   - **Retention Policies**: Delete old data (e.g., 7 days for logs, 30 days for metrics).
   - **Sampling**: Reduce volume for high-cardinality metrics (e.g., `user_id` tags).

3. **Alerting**:
   - **Reduce Noise**: Use SLOs to filter non-critical alerts.
   - **Context**: Include relevant metrics/context in alerts (e.g., "DB load: 85%").

4. **Profiling**:
   - **Targeted Sampling**: Profile during peak load or after anomalies.
   - **Automation**: Integrate profilers with CI/CD (e.g., run on every deploy).

5. **Security**:
   - **PII Redaction**: Mask sensitive data in logs (e.g., `user_id`).
   - **Access Control**: Restrict observability tools to relevant teams.

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **[Distributed Tracing](#)** | Capture end-to-end request flows across microservices.                                                                                                                                                     | Debugging latency issues in distributed systems.                                                                    |
| **[Circuit Breaker](#)**   | Prevent cascading failures by stopping requests to failing services.                                                                                                                                       | Handling service degradation gracefully.                                                                              |
| **[Bulkhead](#)**         | Isolate failures to prevent resource exhaustion.                                                                                                                                                           | Protecting system stability during high load.                                                                       |
| **[Retry & Fallback](#)**  | Automatically retry failed requests or provide fallbacks.                                                                                                                                                   | Improving resilience in transient failure scenarios.                                                              |
| **[Rate Limiting](#)**    | Control request volume to prevent overload.                                                                                                                                                              | Managing API consumption and throttling abuse.                                                                    |
| **[Configuration Management](#)** | Dynamically adjust system behavior (e.g., feature flags, thresholds).                                                                                                                                  | Adapting to runtime conditions (e.g., adjusting alerts during maintenance).                                         |

---
## **Further Reading**
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Google’s PPROF Guide](https://github.com/google/pprof)
- [SRE Book (Google)](https://sre.google/sre-book/table-of-contents/) (Chapter 7: Observability)