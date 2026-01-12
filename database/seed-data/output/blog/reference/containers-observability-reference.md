# **[Pattern] Reference Guide: Containers Observability**

---

## **Overview**
The **Containers Observability** pattern ensures real-time visibility into containerized environments by collecting, aggregating, and analyzing metrics, logs, traces, and events from containers. This pattern helps monitor container health, performance, resource usage, dependencies, and application behavior, enabling proactive incident detection, debugging, and optimizations. It integrates key practices like **metrics collection**, **log aggregation**, **distributed tracing**, and **event correlation**, tailored for dynamic, scale-out containerized architectures.

Observability differs from monitoring by emphasizing **system understanding** over alerting—by combining **metrics (what is happening)**, **logs (why it’s happening)**, and **traces (how it flows)**. This guide covers implementation details, schema references for observability data, query examples, and related patterns.

---

## **Implementation Details**
### **1. Core Components**
| **Component**          | **Purpose**                                                                                     | **Tools/Technologies**                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Metrics Collection** | Gathers numerical data (CPU, memory, latency, request counts) to track system performance.     | Prometheus, Grafana, Datadog, New Relic, OpenTelemetry, Telegraf                        |
| **Log Aggregation**    | Centralizes container logs for filtering, searching, and analysis.                            | Fluentd, Loki, ELK Stack (Elasticsearch, Logstash), Splunk, OpenTelemetry             |
| **Distributed Tracing**| Tracks requests across microservices to diagnose performance bottlenecks.                     | Jaeger, Zipkin, OpenTelemetry, Datadog Trace, Lightstep                                 |
| **Event Correlation**   | Links logs, metrics, and traces to trace root causes of incidents.                            | Correlate with OpenTelemetry Context, Grafana Explore, Datadog Event Logs               |
| **Configuration**      | Defines how observability tools interact with containers (e.g., sidecars, daemonsets).        | Kubernetes Sidecar Pattern (e.g., Jaeger Agent, Prometheus Operator)                     |
| **Storage & Indexing**  | Stores observability data efficiently for querying.                                             | Time-series databases (TimescaleDB, InfluxDB), Elasticsearch, AWS OpenSearch             |

---

### **2. Key Concepts**
#### **A. Metrics**
- **Why**: Track resource utilization, application health, and performance KPIs.
- **Data Types**:
  - **Counter**: Monotonically increasing values (e.g., API requests served).
  - **Gauge**: Instantaneous values (e.g., memory usage).
  - **Histogram/Summary**: Distributions of values (e.g., request latencies).
- **Labels**: E.g., `{pod="nginx", namespace="default", container="web"}` for granular filtering.

#### **B. Logs**
- **Why**: Debug issues by examining runtime application logs.
- **Best Practices**:
  - Structured logging (JSON) for easier parsing.
  - Include container metadata (e.g., `pod_name`, `container_id`).
  - Filter sensitive data (e.g., tokens).

#### **C. Traces**
- **Why**: Diagnose latency and dependency issues in distributed systems.
- **Key Elements**:
  - **Span**: Represents a single operation (e.g., database query).
  - **Trace**: Aggregates spans for an end-to-end request.
  - **Context Propagation**: Attaches trace IDs to logs/metrics via headers.

#### **D. Events**
- **Why**: Alert on significant container lifecycle events (e.g., pod crashes, rescheduling).
- **Sources**:
  - Kubernetes Events API.
  - Custom events from applications (e.g., "Service degraded").

---

### **3. Implementation Steps**
#### **Step 1: Instrumentation**
- **Metrics**: Use client libraries (e.g., Prometheus client for Go/Python) or OpenTelemetry SDKs.
- **Logs**: Log structured data (e.g., `JSON`).
- **Traces**: Inject OpenTelemetry auto-instrumentation agents or SDKs.

**Example (Python with OpenTelemetry):**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

trace.set_tracer_provider(TracerProvider())
exporter = OTLPSpanExporter(endpoint="http://jaeger:4317")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_order") as span:
    span.set_attribute("order_id", "12345")
    # Business logic...
```

#### **Step 2: Data Collection**
- **Metrics**: Scrape endpoints (e.g., `/metrics`) or use sidecar agents (Prometheus Operator).
- **Logs**: Ship to a collector (e.g., Fluentd) with Kubernetes annotations:
  ```yaml
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - mountPath: /var/log
      name: logs
    # Fluentd sidecar
    - name: fluentd
      image: fluent/fluentd-kubernetes-daemonset
  ```
- **Traces**: Use OpenTelemetry Collector or vendor-specific agents (e.g., Jaeger Agent).

#### **Step 3: Storage & Querying**
- **Metrics**: Store in time-series databases (e.g., Prometheus, TimescaleDB).
- **Logs**: Index in Elasticsearch or Loki.
- **Traces**: Store in Jaeger/Zipkin.
- **Events**: Store in Kafka or a dedicated event bus.

#### **Step 4: Dashboards & Alerts**
- **Dashboards**: Build in Grafana or Datadog with pre-built panels (e.g., container CPU/memory).
- **Alerts**: Define rules in Prometheus (e.g., `container_cpu_usage > 90%` for 5m).

**Example Prometheus Alert:**
```yaml
groups:
- name: container-alerts
  rules:
  - alert: HighCPUUsage
    expr: container_cpu_usage > 90 * on() group_left(container_name) cluster_alert_limit
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High CPU on {{ $labels.container_name }}"
```

---

## **Schema Reference**
### **A. Metrics Schema**
| **Attribute**       | **Type**       | **Description**                                  | **Example**                          |
|---------------------|----------------|--------------------------------------------------|--------------------------------------|
| `metric_name`       | String         | Name of the metric (e.g., `container_cpu_usage`). | `container_cpu_usage`                |
| `timestamp`         | Unix Timestamp | When the metric was recorded.                   | `1672531200`                         |
| `value`             | Float          | Numeric value of the metric.                     | `85.3`                               |
| `labels`            | Object         | Key-value pairs for filtering.                  | `{pod: "nginx-1", namespace: "default}` |
| `container_id`      | String         | Unique ID of the container.                     | `docker://1a2b3c4d5e6f`               |
| `kubernetes_pod`    | Object         | Pod metadata.                                   | `{name: "nginx-1", uid: "abc123"}`    |

---

### **B. Logs Schema**
| **Attribute**       | **Type**       | **Description**                                  | **Example**                          |
|---------------------|----------------|--------------------------------------------------|--------------------------------------|
| `timestamp`         | Unix Timestamp | Log timestamp.                                  | `1672531200`                         |
| `container_id`      | String         | Container ID.                                    | `docker://1a2b3c4d5e6f`               |
| `pod_name`          | String         | Kubernetes pod name.                            | `nginx-1`                            |
| `stream`            | String         | Log stream (e.g., "stdout", "stderr").          | `stdout`                             |
| `message`           | String         | Raw log message.                                 | `"500 Internal Server Error"`         |
| `level`             | String         | Log severity (e.g., "info", "error").           | `error`                              |
| `custom_fields`     | Object         | Structured data (e.g., `{"user_id": "123"}`).   | `{request_id: "6789"}`               |

---

### **C. Traces Schema**
| **Attribute**       | **Type**       | **Description**                                  | **Example**                          |
|---------------------|----------------|--------------------------------------------------|--------------------------------------|
| `trace_id`          | String         | Unique ID for the trace.                         | `1a2b3c4d5e6f1a2b3c4d5e6f`           |
| `span_id`           | String         | Unique ID for the span.                          | `5e6f1a2b3c4d5e6f`                   |
| `name`              | String         | Span name (e.g., "GET /api/orders").             | `GET /api/orders`                    |
| `timestamp`         | Unix Timestamp | When the span started.                           | `1672531200`                         |
| `duration`          | Numeric        | Span duration in nanoseconds.                    | `1500000`                            |
| `attributes`        | Object         | Key-value pairs (e.g., `{"status": "success"}`). | `{http.method: "GET"}`               |
| `links`             | Array          | References to parent/child spans.                | `[{trace_id: "1b2c3d...", span_id: "..."}]` |

---

## **Query Examples**
### **1. Prometheus Queries (Metrics)**
**Find containers exceeding 90% CPU for 5 minutes:**
```promql
sum by (pod, container) (
  rate(container_cpu_usage{namespace="default"}[5m])
) > 0.9
```

**Average request latency by container:**
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, container))
```

---

### **2. Loki Log Queries**
**Find errors in `nginx` pods:**
```logql
{job="kubernetes-pods", namespace="default"} |= "500" AND container="nginx"
| json
| line_format "{{.message}} (User: {{.user_id}})"
```

---

### **3. Jaeger Trace Queries**
**Find slow API calls (`> 500ms`) in the past hour:**
```
duration: >500ms
service: api-service
startTime: >now()-1h
```

---

### **4. Elasticsearch Events**
**Find pod restarts in the last hour:**
```json
GET /events/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event_type": "Restarted" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}
```

---

## **Related Patterns**
1. **[Distributed Tracing]** – Extends Containers Observability by focusing solely on tracing requests across services.
2. **[Resilience Patterns]** – Complements observability by implementing retries, circuit breakers, and rate limiting to handle failures gracefully.
3. **[Configuration as Code]** – Use Helm/Kustomize to deploy observability agents (e.g., Prometheus Operator) alongside applications.
4. **[Service Mesh Observability]** – Integrates with Istio/Linkerd to observe service mesh metrics (e.g., sidecar proxy performance).
5. **[Chaos Engineering]** – Validates observability setup by inject failures (e.g., pod kills) and verifying alerts.
6. **[Infrastructure as Code]** – Deploy observability stacks (e.g., Loki + Prometheus) via Terraform or Pulumi.

---

## **Best Practices**
- **Minimize Overhead**: Sample metrics/logs aggressively to avoid resource contention.
- **Secure Data**: Encrypt observability data in transit (TLS) and at rest.
- **Retention Policies**: Define TTL for logs/metrics (e.g., 30 days for logs, 1 year for metrics).
- **Cost Optimization**: Use scalable backends (e.g., Loki for logs, Prometheus for metrics).
- **SLOs**: Define Service Level Objectives (SLOs) for observability (e.g., "99% of traces processed within 1s").

---
**Further Reading**:
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Kubernetes Logging Guide](https://kubernetes.io/docs/concepts/cluster-administration/logging/)