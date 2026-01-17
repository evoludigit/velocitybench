# **[Pattern] Observability: Metrics, Logs, and Traces – Reference Guide**

---

## **1. Overview**
Observability is a systematic approach to monitoring and understanding software systems by merging **Metrics**, **Logs**, and **Traces**. This pattern enables teams to **proactively detect anomalies**, **debug production failures**, and **optimize performance** in distributed systems.

- **Metrics** provide quantitative performance data (e.g., latency, error rates).
- **Logs** offer detailed event-level insights into system behavior.
- **Traces** visualize request flows across microservices, pinpointing bottlenecks.

Together, they form a **unified observability stack**, ensuring visibility into system health, troubleshooting efficiency, and automated alerting.

---

## **2. Schema Reference**

| **Component** | **Purpose**                          | **Key Metrics/Attributes**                     | **Storage/Processing Tools**       |
|---------------|--------------------------------------|-----------------------------------------------|------------------------------------|
| **Metrics**   | Quantify system performance          | - Request latency (p99, avg)                  | Prometheus, Datadog, Grafana       |
|               |                                      | - Error rate, throughput (RPM)                |                                    |
|               |                                      | - Resource utilization (CPU, memory)         |                                    |
| **Logs**      | Capture event-level system activity  | - Timestamp, log level (ERROR, INFO)          | ELK Stack (Elasticsearch, Logstash)| |
|               |                                      | - Request/response payloads (sanitized)       | Fluentd, Loki                      |
|               |                                      | - Correlation IDs (for tracing)               |                                    |
| **Traces**    | Track request flows across services   | - Service-to-service latency                  | Jaeger, Zipkin, OpenTelemetry      |
|               |                                      | - Dependency graphs (service dependencies)    |                                    |
|               |                                      | - Error spans (failed operations)             |                                    |

---

## **3. Query Examples**

### **Metrics (Prometheus Query Language - PromQL)**
**Example 1: High Latency Alert**
```promql
# Alert if p99 request latency exceeds 500ms
sum(rate(http_request_duration_seconds_bucket{quantile="0.99"}[5m])) by (service)
> 0.5
```

**Example 2: Error Rate Trend**
```promql
# Calculate error rate per second
rate(http_requests_total{status=~"5.."}[1m])
/ rate(http_requests_total[1m])
```

### **Logs (ELK Query DSL – Kibana)**
**Example 1: Filter ERROR logs by service**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "match": { "service": "api-gateway" } }
      ]
    }
  }
}
```

**Example 2: Search logs with correlation ID**
```json
{
  "query": {
    "term": {
      "x-correlation-id": "abc123"
    }
  }
}
```

### **Traces (Jaeger Query API)**
**Example 1: Search by operation name**
```
service:payment-service
operation:process-payment
```

**Example 2: Filter traces with errors**
```
tags.error=true
```

---

## **4. Implementation Details**

### **4.1 Metrics Collection**
- **Instrumentation**: Use OpenTelemetry, Prometheus client libraries.
- **Sampling**: Adjust sampling rate (e.g., 1% for high-cardinality metrics).
- **Aggregation**: Pre-aggregate metrics at source to reduce cardinality.

### **4.2 Logs Management**
- **Structured Logging**: Use JSON format for easier parsing.
- **Retention Policy**: Configure log rotation (e.g., 30 days in ELK).
- **Correlation IDs**: Attach trace IDs to logs for context.

### **4.3 Distributed Tracing**
- **Auto-Instrumentation**: Use OpenTelemetry auto-instrumentation for frameworks (e.g., Spring Boot, Node.js).
- **Span Context Propagation**: Ensure trace IDs flow across service boundaries.
- **Limiting Context**: Avoid excessive payload size in traces.

### **4.4 Alerting**
- **Anomaly Detection**: Use ML-based rules (e.g., Prometheus Alertmanager).
- **SLO-Based Alerts**: Alert on error budgets (e.g., >5% error rate).

---

## **5. Related Patterns**
| **Pattern**               | **Connection to Observability**                          |
|---------------------------|----------------------------------------------------------|
| **Resilience Pattern**    | Observability helps detect and recover from failures.      |
| **Circuit Breaker**       | Logs and metrics track circuit-breaker trip events.        |
| **Service Mesh**          | Envoy/Linkerd injects metrics and traces into service mesh.|
| **Feature Flags**         | Logs track flag usage and impact.                         |

---

## **6. Common Pitfalls & Mitigations**
| **Pitfall**                     | **Mitigation**                                      |
|----------------------------------|------------------------------------------------------|
| **Metric cardinality explosion** | Aggregate high-cardinality metrics upfront.          |
| **Log overload**                 | Enforce log-level filtering (e.g., disable DEBUG in prod). |
| **Trace sampling too low**       | Start with 1-5% sampling, increase for critical paths. |

---
**Last Updated:** `[Insert Date]`
**Version:** `1.2.0`