# **[Pattern] Monitoring Setup – Reference Guide**

---

## **Overview**
The **Monitoring Setup** pattern provides a structured approach to deploying and configuring monitoring infrastructure in cloud-native applications. It ensures real-time observability, performance tracking, and alerting by integrating observability tools (metrics, logs, traces) with application components. This pattern is critical for proactive issue detection, resource optimization, and compliance monitoring.

Key use cases include:
- Enterprise applications requiring SLAs (Service Level Agreements)
- Microservices architectures with distributed tracing needs
- High-availability systems needing auto-scaling adjustments
- Compliance-driven environments (e.g., GDPR, HIPAA)

This guide covers foundational components (logs, metrics, traces) and orchestration (sampling, aggregation) while emphasizing scalability and cost efficiency.

---

## **Implementation Details**

### **1. Core Components**
| **Component**       | **Description**                                                                 | **Key Considerations**                                                                 |
|---------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Metrics**         | Numeric data (e.g., request count, latency, error rates). Exposed via APIs (Prometheus, OpenTelemetry). | Avoid over-collection; use sampling for high-cardinality metrics (e.g., error codes). |
| **Logs**            | Structured/unstructured text from application runtime (e.g., debug logs, event logs). | Centralized via Logstash, Fluentd, or Cloud Logging. Retention policies are critical. |
| **Traces**          | End-to-end requests traced across services (latency breakdowns).               | Use distributed tracing (Jaeger, OpenTelemetry Collector). Sample traces sparingly.   |
| **Alerts**          | Notifications for thresholds (e.g., 5xx errors > 1%).                          | Define alert rules (e.g., `p99 latency > 1s`) and alert policies (e.g., Slack/PagerDuty). |
| **Dashboards**      | Visualizations (Grafana, Amazon CloudWatch) for key metrics (e.g., CPU usage). | Customize dashboards per team (DevOps vs. SRE).                                    |
| **Sampling**        | Reducing trace/log volume by selecting representative samples (e.g., 10% of requests). | Adjust based on cost and observability needs.                                       |
| **Aggregation**     | Grouping metrics/logs (e.g., summing errors per service).                      | Use time-series databases (e.g., Prometheus) for efficiency.                        |

---

### **2. Architectural Patterns**
#### **A. Distributed Tracing Setup**
1. **Instrumentation**:
   - Add OpenTelemetry SDK to each service (e.g., `io.opentelemetry:opentelemetry-java`).
   - Example for a Java microservice:
     ```java
     Tracer tracer = GlobalTracerProvider.getTracer("my-app");
     try (Scope scope = tracer.spanBuilder("process-order").startScope()) {
         tracer.getCurrentSpan().setAttribute("order-id", "123");
     }
     ```
2. **Exporter**:
   - Configure `OpenTelemetry Collector` to export traces to Jaeger or OpenTelemetry Backend:
     ```yaml
     exporters:
       jaeger:
         endpoint: "jaeger-collector:14250"
         tls:
           insecure: true
     ```

#### **B. Metrics Pipeline**
1. **Push/Pull Model**:
   - **Push**: Services emit metrics to a collector (e.g., Prometheus Pushgateway).
   - **Pull**: Collector scrapes endpoints (e.g., `/metrics` endpoint in Spring Boot).
2. **Storage Backend**:
   - Use **Prometheus** for short-term (15–30 days) or **Thanos** for long-term retention.

#### **C. Log Aggregation**
1. **Fluentd Configuration** (example for collecting logs from containers):
   ```xml
   <source>
     @type tail
     path /var/log/containers/*.log
     pos_file /var/log/fluentd-containers.log.pos
     tag kubernetes.*
     <parse>
       @type json
     </parse>
   </source>
   ```
2. **Sink**:
   - Ship logs to **Google Cloud Logging**, **AWS CloudWatch**, or **Elasticsearch**.

---

## **Schema Reference**
| **Schema**               | **Purpose**                                                                 | **Example Format**                          |
|--------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Metric Schema**        | Defines metric types (counter, gauge, histogram).                          | `{ "name": "http_requests_total", "type": "counter" }` |
| **Log Schema**           | Structured logging fields (e.g., `timestamp`, `severity`, `service`).        | `{ "timestamp": "2024-01-01T12:00:00Z", "level": "ERROR" }` |
| **Trace Schema**         | Span attributes (e.g., `service.name`, `http.method`).                     | `{ "spans": [ { "name": "db-query", "attributes": { "db": "postgres" } } ] }` |
| **Alert Rule Schema**    | Defines conditions (e.g., `metric_name > threshold`).                       | `{ "expr": "rate(http_errors_total[5m]) > 0.1" }` |
| **Dashboard Layout**     | Panels for visualizing metrics/logs (e.g., line chart for latency).        | `{ "title": "API Latency", "type": "graph", "metrics": ["p99_latency"] }` |

---

## **Query Examples**
### **1. PromQL Queries**
- **Average response time (last 5 minutes):**
  ```promql
  rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
  ```
- **Error rate per service:**
  ```promql
  sum(rate(http_requests_total{status=~"5.."}[1m])) by (service)
  ```

### **2. LogQL Queries (Google Cloud Logging)**
- **Errors in the past hour:**
  ```logql
  log_name="projects/my-project/logs/app-logs"
  | jsonPayload.severity="ERROR"
  | timestamp > "1h"
  ```
- **Latency spikes:**
  ```logql
  log_name="projects/my-project/logs/api-logs"
  | parse_json_suffix severity
  | jsonPayload.response_time > 500
  ```

### **3. Jaeger Trace Query**
- **Filter traces by service and duration > 2s:**
  ```bash
  jaeger-cli query --service=payment-service --duration=2s
  ```

---

## **Requirements Checklist**
Before deploying, verify:
1. **Instrumentation**:
   - [ ] OpenTelemetry SDKs installed in all services.
   - [ ] Metrics endpoints exposed (`/metrics` or custom path).
2. **Data Flow**:
   - [ ] Collectors (Prometheus, Fluentd) configured.
   - [ ] Backend storage (e.g., Prometheus, Elasticsearch) accessible.
3. **Alerting**:
   - [ ] Alert rules defined (e.g., `p99 > 1s`).
   - [ ] Notification channels (Slack/Email) configured.
4. **Cost Control**:
   - [ ] Sampling rates set (e.g., 10% of traces).
   - [ ] Retention policies enforced.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Relation to Monitoring Setup**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **[Resilience Patterns]** | Handles failures (circuit breakers, retries).                                | Monitoring validates resilience (e.g., tracking failed retries).                                |
| **[Autoscaling]**         | Adjusts resources based on load (e.g., Kubernetes HPA).                      | Monitoring provides metrics (CPU/memory) for scaling decisions.                                  |
| **[Secure Configuration Management]** | Encrypts secrets (e.g., API keys).      | Logging audits secret access (e.g., `key=abc123` in logs).                                       |
| **[Canary Deployments]**  | Gradual rollouts with monitoring.                                             | Traces compare old/new versions for performance regressions.                                      |
| **[Distributed Locks]**   | Prevents contention in shared resources.                                    | Metrics track lock contention (e.g., `locked_requests > 0`).                                    |

---
**Note**: For cloud-specific implementations, refer to vendor docs (e.g., [AWS Distro for OpenTelemetry](https://aws-otel.github.io/)).

**Last Updated**: [Insert Date]
**Version**: 1.0