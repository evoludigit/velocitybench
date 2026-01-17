**[Pattern] Microservices Monitoring Reference Guide**

---

### **Overview**
Microservices Monitoring is a design pattern for observing, collecting, and analyzing runtime data from distributed microservices to ensure system reliability, performance, and debugging efficiency. Unlike monolithic applications, microservices operate independently but must collaborate—making centralized logging, metrics, and tracing essential. This guide outlines key concepts, implementation schemata, and practical query examples to establish a robust microservices monitoring framework.

---

### **Key Concepts & Implementation Details**
| **Term**               | **Definition**                                                                                                                                                     | **Use Case**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Metrics**            | Quantifiable data points (e.g., latency, error rates, throughput) collected via instrumentation.                                                                     | Performance benchmarking, anomaly detection.                                  |
| **Logs**               | Structured or unstructured runtime messages (e.g., debug, error) emitted by services.                                                                | Debugging failures, auditing.                                                  |
| **Traces**             | End-to-end requests across services with timestamps at each hop (distributed tracing).                                                      | Identifying latency bottlenecks in microservices interactions.               |
| **Dashboards**         | Visualized metrics/logs for real-time or historical monitoring.                                                                                             | Alerting, performance analytics.                                              |
| **Alerts**             | Notifications triggered by predefined thresholds (e.g., 99th percentile latency > 1s).                                                              | Proactive issue resolution.                                                   |
| **Instrumentation**    | Code or library hooks (e.g., OpenTelemetry) to emit metrics/logs/traces.                                                                                     | Minimal overhead data collection.                                             |
| **Aggregation**        | Consolidation of data (e.g., time-series databases, ELK stack) for scalability.                                                                             | Reducing noise in monitoring tools.                                           |
| **Sampling**           | Selecting subsets of traces/logs to reduce volume (e.g., 1% of requests).                                                                                   | Managing costs in high-traffic systems.                                       |

---

### **Schema Reference**
#### **1. Core Data Flows**
| **Component**       | **Data Type**       | **Example Schema**                                                                                     | **Storage**          |
|---------------------|---------------------|---------------------------------------------------------------------------------------------------------|----------------------|
| **Metrics**         | Time-series         | `{"service": "user-service", "metric": "http_request_duration", "value": 120, "timestamp": "2024-05-01"}` | InfluxDB, Prometheus |
| **Logs**            | Structured/JSON     | `{"level": "ERROR", "message": "DB connection failed", "service": "order-service", "timestamp": "..."}` | ELK, Loki            |
| **Traces**          | Graph/JSON          | `{"trace_id": "abc123", "spans": [{"service": "auth", "duration": 45}, {"service": "payment", "duration": 80}]}` | Jaeger, Zipkin       |

#### **2. Instrumentation Libraries**
| **Library**          | **Purpose**                                                                 | **Compatibility**                          |
|----------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **OpenTelemetry**    | Unified SDK for metrics, logs, traces (vendor-agnostic).                     | Java, Python, Go, Node.js                  |
| **Prometheus Client**| Metrics collection via HTTP endpoints.                                       | All languages                            |
| **ELK Stack**        | Logs aggregation (Elasticsearch, Logstash, Kibana).                          | JSON logs                                |
| **Zipkin/Jaeger**    | Distributed tracing with visualization.                                      | Java, .NET, Python (via OTLP exporter)     |

---

### **Query Examples**
#### **1. Metrics Queries (PromQL)**
**Example:** Find services with 99th percentile latency > 500ms.
```promql
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
  by(service)
  > 0.5
```
**Output:** List of services violating SLOs.

#### **2. Logs Queries (ELK Kibana)**
**Example:** Filter errors in `payment-service` from the last hour.
```
service: "payment-service" AND @timestamp > now-1h AND level: "ERROR"
```
**Output:** Search results with context (e.g., failed transactions).

#### **3. Traces Queries (Jaeger)**
**Example:** Find slow payment flows (duration > 300ms).
```
span.duration > 300ms AND tags.service = "payment-service"
```
**Output:** Visualized trace with bottleneck analysis.

---

### **Implementation Steps**
1. **Instrument Services**
   - Add OpenTelemetry SDK to each microservice (e.g., auto-instrument HTTP clients).
   - Example (Python):
     ```python
     from opentelemetry import trace
     tracer = trace.get_tracer(__name__)
     with tracer.start_as_current_span("process_order"):
         # Business logic
     ```

2. **Export Data**
   - Configure exporters (e.g., Prometheus, OTLP) to send metrics/logs to central systems.

3. **Store & Visualize**
   - **Metrics:** Prometheus → Grafana dashboards.
   - **Logs:** ELK Stack → Kibana dashboards.
   - **Traces:** Jaeger → Tracing UI.

4. **Set Alerts**
   - Define rules in Grafana/Prometheus:
     ```yaml
     - alert: HighLatency
       expr: histogram_quantile(0.95, rate(...)) > 1
       for: 5m
       labels: severity=high
     ```

---

### **Requirements Checklist**
| **Task**                          | **Tools**               | **Notes**                                  |
|-----------------------------------|-------------------------|--------------------------------------------|
| Instrument services               | OpenTelemetry, Prometheus | Minimal SDK impact.                        |
| Set up collectors                 | Fluentd, Grafana        | Batch logs/metrics for efficiency.         |
| Visualize dashboards              | Grafana, Kibana         | Pre-built templates for microservices.      |
| Configure alerts                  | Alertmanager, PagerDuty | Multi-channel notifications.                |
| Optimize sampling                 | Jaeger, Datadog         | Reduce trace volume for cost savings.      |

---

### **Related Patterns**
1. **[Resilience Patterns](link)**
   - Combine with circuit breakers (e.g., Retry, Rate Limiting) to correlate failures with monitoring data.
   - *Example:* Alert on `order-service` timeouts after a database collapse.

2. **[Distributed Tracing](link)**
   - Use tracing to debug failures across service boundaries (e.g., `user-service` → `auth-service` → `payment-service`).

3. **[Canary Releases](link)**
   - Monitor new versions of microservices in production with tailored metrics (e.g., error rates by version).

4. **[Observability as Code](link)**
   - Define dashboards/alerts via Git (e.g., Terraform for Prometheus Alertmanager).

5. **[Logging Aggregation](link)**
   - Centralize logs (e.g., Loki) to avoid per-service log analysis overhead.

---
**Best Practices**
- **Start small:** Monitor critical services first (e.g., API gateways).
- **Avoid overload:** Sample traces/logs if volume is high.
- **Correlate data:** Use trace IDs to link logs/metrics to a single request.