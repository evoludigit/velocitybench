# **[Pattern] Microservices Observability – Reference Guide**

---

## **1. Overview**
Microservices Observability refers to the ability to monitor, diagnose, and troubleshoot distributed systems composed of multiple independent services. Unlike traditional monolithic applications, microservices introduce complexity through decentralized data, asynchronous communication, and dynamic scaling. Observability ensures teams can **measure behavior**, **detect anomalies**, and **correlate events** across services, improving reliability, performance, and debugging efficiency.

Key goals include:
- **Real-time insights** into service health and dependencies.
- **Proactive anomaly detection** using metrics, logs, and traces.
- **Contextual debugging** by tracing requests across services.
- **Performance optimization** via latency analysis and resource utilization.

This guide covers foundational concepts, implementation schemas, query examples (for metrics/logs/traces), and related observability patterns.

---

## **2. Schema Reference**
Below are standardized schemas for **metrics**, **logs**, and **traces** used in microservices observability.

| **Schema**          | **Description**                                                                 | **Example Fields**                                                                 |
|---------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Metrics Schema**  | Time-series data for monitoring performance, errors, and resource usage.         | `timestamp`, `service_name`, `metric_type` (e.g., `latency_ms`), `value`, `labels` |
| **Log Schema**      | Structured logs with contextual metadata for debugging.                          | `timestamp`, `service_name`, `log_level`, `message`, `correlation_id`, `context`    |
| **Trace Schema**    | Request flows across services with span information (start/end timestamps).     | `trace_id`, `span_id`, `service_name`, `operation`, `start_time`, `duration_ms`, `tags`|

---
### **Key Metric Types**
| **Metric Type**         | **Definition**                                                                 | **Use Case**                                      |
|-------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| `request_count`         | Total HTTP/API requests per service.                                           | Monitor traffic demand.                           |
| `latency_p95`           | 95th percentile latency of requests.                                           | Identify slow services.                           |
| `error_rate`            | Ratio of failed requests to total requests.                                    | Detect failures early.                            |
| `memory_usage`          | Current memory consumption (MB/GB) per service.                               | Optimize resource allocation.                     |
| `dependency_latency`    | Latency contributed by downstream services.                                  | Pinpoint bottlenecks in inter-service calls.      |

---

## **2. Query Examples**

### **A. Metrics Queries**
#### **1. Average Latency per Service**
```sql
SELECT service_name, avg(latency_ms)
FROM metrics
WHERE timestamp > now() - 1h
GROUP BY service_name
ORDER BY avg(latency_ms) DESC;
```
**Output:** Ranks services by latency to identify performance laggards.

#### **2. Error Rate Spike Detection**
```promql
rate(error_count[5m]) / rate(request_count[5m]) > 0.05
```
**Tool:** Prometheus (PromQL).
**Use:** Alert if error rate exceeds 5% in 5-minute windows.

#### **3. Memory Leaks (Growing Usage)**
```sql
increase(memory_usage{service="payment-service"}[1h]) > 1000
```
**Tool:** Grafana with Prometheus.
**Use:** Detect abnormal memory growth in `payment-service`.

---

### **B. Log Queries**
#### **1. Filter Logs by Correlation ID**
```json
// ELK Stack (Logstash/Kibana) Query
{
  "query_string": {
    "query": "correlation_id: \"abc123\" AND log_level: ERROR"
  }
}
```
**Output:** Shows all logs tied to a specific request flow.

#### **2. Error Logs with Time Window**
```csv
// Splunk Query
index=app_errors sourcetype="json" "timestamp > @now-1d" | stats count by service_name, error_type
```
**Use:** Identify recurring errors in the last day.

---

### **C. Trace Queries**
#### **1. Trace a User Request Across Services**
```yaml
# Jaeger Query (GraphQL-like)
query {
  findTraces(
    serviceNames: ["auth-service", "order-service"]
    startTime: "2024-05-20T12:00:00Z"
    duration: 60s
  ) {
    spans {
      operationName
      duration
      tags {
        key
        value
      }
    }
  }
}
```
**Output:** Visualizes the flow from `auth-service` → `payment-service`.

#### **2. Slowest Dependencies**
```sql
SELECT service_name, avg(duration_ms)
FROM traces
WHERE timestamp > now() - 1h
GROUP BY service_name
ORDER BY avg(duration_ms) DESC
LIMIT 5;
```
**Use:** Identify inter-service calls causing delays.

---

## **3. Implementation Details**

### **A. Key Components**
1. **Metrics Collection**
   - **Tools:** Prometheus, Datadog, New Relic.
   - **Best Practice:** Instrument business-critical paths (e.g., checkout flow).

2. **Logging**
   - **Tools:** ELK Stack (Elasticsearch, Logstash, Kibana), Loki (Grafana).
   - **Best Practice:** Use structured JSON logs with `correlation_id` for traces.

3. **Distributed Tracing**
   - **Tools:** OpenTelemetry, Jaeger, Zipkin.
   - **Best Practice:** Auto-instrument HTTP clients/servers to capture spans.

### **B. Data Correlation**
- **Context Propagation:** Use headers (e.g., `X-Trace-ID`) to link logs/traces/metrics.
- **Example Header:**
  ```
  X-Trace-ID: abc123-xyz456
  Correlation-ID: abc123
  ```

### **C. Alerting Rules**
| **Metric**               | **Threshold**       | **Alert Rule**                          |
|--------------------------|---------------------|-----------------------------------------|
| `latency_p99`            | > 500ms             | `IF avg_over_time(...) > 500` THEN ALERT|
| `error_rate`             | > 1%                | `rate(...) > 0.01`                      |
| `memory_usage`           | > 80% of limit      | `increase(...) > 80%`                   |

---
## **4. Related Patterns**
1. **[Service Mesh Observability](https://example.com/service-mesh-pattern)**
   - Use Istio/Linkerd to observe sidecar-proxied traffic.

2. **[Centralized Logging](https://example.com/logging-pattern)**
   - Aggregate logs from all microservices into a single dashboard (ELK, Splunk).

3. **[Canary Analysis](https://example.com/canary-pattern)**
   - Gradually roll out changes while monitoring observability metrics.

4. **[Circuit Breaker](https://example.com/circuit-breaker-pattern)**
   - Combine with observability to detect cascading failures.

5. **[Distributed Idempotency](https://example.com/idempotency-pattern)**
   - Ensure observability traces don’t duplicate work during retries.

---

## **5. Anti-Patterns to Avoid**
- **Log Spam:** Avoid excessive logging (e.g., `debug` logs in production).
- **Uncorrelated Traces:** Ensure `trace_id`/`correlation_id` are propagated.
- **Metric Overhead:** Only instrument critical paths to avoid performance impact.
- **Alert Fatigue:** Set meaningful thresholds (e.g., P99, not P95 for latency).

---
## **6. Tools Comparison**
| **Tool**          | **Metrics** | **Logs** | **Traces** | **Best For**               |
|-------------------|------------|----------|-----------|----------------------------|
| **Prometheus**    | ✅         | ❌       | ❌        | Time-series monitoring     |
| **Grafana**       | ✅         | ✅ (Loki)| ❌        | Dashboards                 |
| **Jaeger**        | ❌         | ❌       | ✅        | Distributed tracing        |
| **ELK Stack**     | ❌         | ✅       | ❌        | Log analysis               |
| **OpenTelemetry** | ✅         | ✅       | ✅        | Unified observability      |

---
## **7. Further Reading**
- [CNCF Observability Whitepaper](https://www.cncf.io/whitepapers/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Distributed Tracing Explained (Google)](https://cloud.google.com/trace/docs)