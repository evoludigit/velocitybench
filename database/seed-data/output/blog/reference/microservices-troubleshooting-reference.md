# **[Pattern] Microservices Troubleshooting Reference Guide**

---

## **1. Overview**
Microservices architectures improve scalability, resilience, and independent deployment but introduce complexity in troubleshooting. Unlike monolithic applications, distributed systems require a structured approach to diagnose issues spanning multiple services, networks, dependencies, and operational states. This guide outlines key troubleshooting strategies, diagnostic tools, and workflows to efficiently isolate, analyze, and resolve failures in microservices deployments.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Challenges**
| **Challenge**               | **Description**                                                                 | **Solution Approach**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Distributed Tracing**     | Tracking requests across services with latency spikes or timeouts.            | Use distributed tracing (e.g., OpenTelemetry, Jaeger) to correlate logs/metrics.     |
| **Dependency Failures**     | One service failing cascades into others due to tight coupling.                | Implement circuit breakers (Hystrix, Resilience4j) and bulkheading.                  |
| **Network Latency/Timeouts**| Slow inter-service communication degrading performance.                     | Optimize timeouts, retry policies, and service mesh (Istio, Linkerd) configurations. |
| **Logging & Observability**  | Siloed logs make root-cause analysis difficult.                              | Aggregate logs (ELK, Loki), monitor metrics (Prometheus, Grafana), and set alerts. |
| **Configuration Drift**     | Misaligned configurations between environments.                             | Use GitOps (ArgoCD, Flux) and centralized config (Consul, etcd).                   |

---

### **2.2 Troubleshooting Workflow**
1. **Detect the Issue**
   - Monitor alerts (e.g., Prometheus alerts), dashboards (Grafana), or logging platforms (Datadog).
   - Check if the issue is user-reported or detected proactively (e.g., error spikes).

2. **Isolate the Problem**
   - **Service-Specific**: Check service logs, metrics, and health endpoints (`/health`).
   - **Dependency-Focused**: Verify upstream/downstream service availability using API gateways or service meshes.
   - **Cross-Cutting**: Use distributed tracing to follow requests through the system.

3. **Reproduce & Diagnose**
   - **Local Testing**: Spin up a local environment (e.g., Docker Compose, Minikube) to replicate the issue.
   - **Environment Comparison**: Compare production vs. staging configurations (e.g., DB versions, network policies).
   - **Dependency Inspection**: Use tools like `curl`, `Postman`, or `k6` to test inter-service calls.

4. **Resolve & Mitigate**
   - Apply fixes (code changes, config updates) via CI/CD pipelines.
   - Implement mitigations (e.g., fallback logic, rate limiting) to prevent recurrence.

5. **Postmortem & Improvement**
   - Document root causes in a postmortem report.
   - Update runbooks, alerts, or automation (e.g., Ansible, Terraform) to prevent future issues.

---

### **2.3 Diagnostic Tools**
| **Category**               | **Tool**               | **Purpose**                                                                 |
|----------------------------|------------------------|-----------------------------------------------------------------------------|
| **Distributed Tracing**    | OpenTelemetry, Jaeger  | Trace requests across services with timestamps and latency data.            |
| **Logging**                | ELK Stack, Loki       | Aggregate logs for correlating events.                                      |
| **Metrics**                | Prometheus, Grafana    | Monitor service health, performance, and custom business metrics.          |
| **Service Mesh**           | Istio, Linkerd        | Manage traffic, retries, timeouts, and observability at the service level. |
| **API Testing**            | Postman, k6            | Validate inter-service API contracts and performance.                      |
| **Database Debugging**     | pgBadger, SQLNoob     | Analyze slow queries or connection issues.                                  |
| **Network Diagnostics**    | `curl`, `tcpdump`, `mtr` | Inspect network latency, packet loss, or DNS resolution.                    |

---

## **3. Schema Reference**
Below are key schemas for troubleshooting microservices. Use these as templates for log parsing, metric queries, or alert rules.

### **3.1 Log Schema (JSON)**
```json
{
  "timestamp": "ISO_8601",
  "service_name": "string",
  "instance_id": "string",
  "level": "ERROR|WARN|INFO|DEBUG",
  "message": "string",
  "trace_id": "UUID",       // For distributed tracing
  "span_id": "UUID",        // Individual operation within a trace
  "context": {              // Custom metadata (e.g., user_id, request_id)
    "key": "value"
  }
}
```
**Example Query (Grok Pattern for Logstash):**
```groovy
%{TIMESTAMP_ISO8601:timestamp} %{DATA:service_name} %{DATA:instance_id} %{WORD:level}: %{GREEDYDATA:message}
```

---

### **3.2 Metric Schema (Prometheus)**
```plaintext
# Service-level metric (e.g., HTTP requests)
http_requests_total{
  service="order-service",
  method="POST",
  endpoint="/orders",
  status="200|500"
} 100.0

# Latency histogram (e.g., P99 response time)
http_request_duration_seconds_histogram{
  service="payment-service",
  quantile="0.99",
  method="POST"
} 0.8

# Error rate (ratio over sliding window)
error_rate{
  service="inventory-service",
  endpoint="/check_stock"
} 0.02
```

**Alert Rule Example:**
```yaml
- alert: HighErrorRate
  expr: error_rate{service="inventory-service"} > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate in inventory-service ({{$value}})"
```

---

### **3.3 Distributed Trace Schema (OpenTelemetry)**
```json
{
  "trace_id": "UUID",
  "spans": [
    {
      "span_id": "UUID",
      "name": "string",
      "start_time": "ISO_8601",
      "end_time": "ISO_8601",
      "service_name": "string",
      "attributes": {       // Key-value pairs (e.g., HTTP method, status)
        "http.method": "GET",
        "http.status_code": 500
      },
      "errors": [           // Error annotations
        {
          "message": "string",
          "type": "string"
        }
      ]
    }
  ]
}
```

---

## **4. Query Examples**

### **4.1 Log Query (Elasticsearch/Kibana)**
**Problem**: Identify 5xx errors in `order-service` over the last 1 hour.
```json
GET order-service/_search
{
  "query": {
    "bool": {
      "must": [
        { "range": { "timestamp": { "gte": "now-1h" } } },
        { "match": { "level": "ERROR" } },
        { "match_phrase": { "message": "5xx" } }
      ]
    }
  },
  "sort": [ { "timestamp": "desc" } ],
  "size": 50
}
```

---

### **4.2 Metric Query (Prometheus)**
**Problem**: Alert if `payment-service` fails to process 90% of requests in 5 minutes.
```promql
rate(http_requests_total{service="payment-service", status=~"5.."}[5m])
  /
rate(http_requests_total{service="payment-service"}[5m])
> 0.9
```

---

### **4.3 Distributed Trace Query (Jaeger)**
**Problem**: Find all traces where `order-service` failed to call `payment-service`.
```bash
# Filter traces where payment-service returned 5xx
jaeger query \
  --service='order-service' \
  --operation.name='call_payment_service' \
  --limit=50 \
  --filter 'http.response_code:5xx'
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Circuit Breaker**              | Dynamically disable failing dependencies to prevent cascading failures.       | When upstream services are unstable or prone to timeouts.                       |
| **Bulkheading**                  | Isolate resource usage per service to prevent one service from starving others. | High-contention environments (e.g., shared databases).                         |
| **Retries with Backoff**         | Exponentially backoff retries for transient failures.                          | Network partitions or throttled APIs.                                           |
| **Chaos Engineering**            | Proactively test resilience by injecting failures.                             | During development or canary deployments to validate recovery mechanisms.       |
| **Centralized Logging**          | Aggregate logs from all services for correlated debugging.                     | Large-scale deployments with distributed teams.                                |
| **Feature Flags**                | Gradually roll out changes without affecting all users.                        | Testing new features or mitigating production issues.                          |

---

## **6. Best Practices**
1. **Standardize Logging**: Use a structured format (JSON) and common tags (e.g., `service_name`, `trace_id`).
2. **Instrument Early**: Add observability (metrics, traces, logs) during development, not as an afterthought.
3. **Define SLOs/SLIs**: Set service-level objectives to proactively detect degradation.
4. **Automate Alerts**: Reduce alert fatigue with smart thresholds (e.g., P99 latency).
5. **Document Runbooks**: Maintain step-by-step guides for common issues (e.g., DB connection drops).
6. **Test Resilience**: Use chaos tools (Gremlin, Chaos Monkey) to validate failure recovery.

---
**References**:
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Istio Troubleshooting Guide](https://istio.io/latest/docs/tasks/observability/)

---
**Last Updated**: [Date]
**Version**: 1.0