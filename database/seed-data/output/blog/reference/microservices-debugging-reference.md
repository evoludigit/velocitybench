---
# **[Pattern] Microservices Debugging: Reference Guide**

---

## **Overview**
Debugging in microservices architectures presents unique challenges due to distributed nature, inter-service dependencies, and fragmented logs. This guide provides a structured approach to **isolate, analyze, and resolve issues** across loosely coupled services. Best practices include:

- **Centralized logging & tracing** (distributed tracing, structured logging).
- **Observability tools** (metrics, logs, and traces integration).
- **Service mesh integration** (e.g., Istio, Linkerd) for network-level debugging.
- **Pattern-specific debugging schemas** (e.g., circuit breaker retries, timeouts).
- **Automated root-cause analysis** (ML-driven anomaly detection).

---

## **Key Concepts & Implementation Details**

| **Concept**               | **Definition**                                                                 | **Example Tools/Technologies**                          |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------|
| **Distributed Tracing**   | Tracks requests across services using unique IDs (e.g., OpenTelemetry traces). | Jaeger, Zipkin, AWS X-Ray                               |
| **Structured Logging**    | Logs in machine-readable formats (JSON) for querying/filtering.               | ELK Stack (Elasticsearch, Logstash, Kibana), Loki      |
| **Metrics & Dashboards**  | Time-series data (latency, error rates) for proactive issue detection.       | Prometheus + Grafana, Datadog, New Relic               |
| **Service Mesh Debugging**| Intercepts service-to-service traffic for inspection/debugging.                | Istio, Linkerd, Consul Connect                        |
| **Dead Letter Queues (DLQ)** | Captures failed events/operations for post-mortem analysis.                  | Kafka DLQ, AWS SQS DLQ                                  |
| **Chaos Engineering**     | Simulates failures to validate resilience (e.g., killing pods).              | Gremlin, Chaos Mesh                                   |
| **Canary Analysis**       | Gradually rollbacks feature flags to isolate regression sources.             | LaunchDarkly, Flagger                                 |

---

## **Schema Reference**

### **1. Distributed Trace Schema**
| Field          | Type       | Description                                                                 | Example Value                     |
|----------------|------------|-----------------------------------------------------------------------------|-----------------------------------|
| `trace_id`     | String     | Unique identifier for a distributed trace.                                  | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6` |
| `span_id`      | String     | Sub-request identifier within a trace.                                       | `b2c3d4e5-f6g7-89h0-1i2j-3k4l5m6` |
| `service_name` | String     | Name of the service emitting the span.                                      | `payment-service`                 |
| `timestamp`    | Timestamp  | When the span was recorded.                                                  | `2023-10-15T14:30:45.123Z`       |
| `duration_ms`  | Integer    | Duration of the span in milliseconds.                                        | `45`                               |
| `tags`         | Object     | Key-value pairs (e.g., `http.method`, `db.query`).                          | `{ "http.method": "POST", "db.query": "SELECT *" }` |
| `logs`         | Array      | Structured log entries for the span.                                         | `[{ "message": "DB query failed", "severity": "ERROR" }]` |

---

### **2. Structured Log Schema**
| Field          | Type       | Description                                                                 | Example Value                     |
|----------------|------------|-----------------------------------------------------------------------------|-----------------------------------|
| `timestamp`    | Timestamp  | ISO 8601 timestamp of the log entry.                                         | `2023-10-15T14:30:45.123Z`       |
| `service`      | String     | Name of the service generating the log.                                      | `inventory-service`              |
| `level`        | String     | Severity level (DEBUG, INFO, WARN, ERROR, FATAL).                           | `ERROR`                           |
| `message`      | String     | Human-readable log message.                                                   | `Failed to fetch stock levels`     |
| `metadata`     | Object     | Contextual data (e.g., `user_id`, `request_id`).                             | `{ "user_id": "u123", "request_id": "req456" }` |
| `trace_id`     | String     | Link to distributed trace (if available).                                   | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6` |

---

### **3. Metrics Schema**
| Field          | Type       | Description                                                                 | Example Value                     |
|----------------|------------|-----------------------------------------------------------------------------|-----------------------------------|
| `metric_name`  | String     | Name of the metric (e.g., `http_requests_total`).                          | `service_latency_ms`              |
| `service`      | String     | Service emitting the metric.                                                | `checkout-service`                |
| `value`        | Float      | Numeric value of the metric.                                                | `342.5`                           |
| `unit`         | String     | Unit of measurement (e.g., `ms`, `count`).                                   | `milliseconds`                     |
| `labels`       | Object     | Key-value filters (e.g., `http_method`, `status_code`).                     | `{ "http_method": "POST", "status_code": "500" }` |
| `timestamp`    | Timestamp  | When the metric was recorded.                                                | `2023-10-15T14:30:45.123Z`       |

---

## **Query Examples**

---

### **1. Distributed Trace Query (Jaeger)**
**Use Case:** Trace a failed payment transaction from `checkout-service` to `payment-service`.
```sql
SELECT
  service_name,
  span_name,
  duration_ms,
  tags
FROM traces
WHERE
  trace_id = 'a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6'
  AND service_name IN ('checkout-service', 'payment-service')
ORDER BY timestamp ASC;
```
**Output Snippet:**
```json
[
  { "service_name": "checkout-service", "span_name": "process_payment", "duration_ms": 200, "tags": { "http.method": "POST", "payment.status": "FAILED" } },
  { "service_name": "payment-service", "span_name": "validate_card", "duration_ms": 150, "tags": { "db.query": "SELECT * FROM cards WHERE id = ?", "error": "SQL_TIMEOUT" } }
]
```

---

### **2. Structured Log Query (ELK/Kibana)**
**Use Case:** Filter `ERROR` logs from `inventory-service` related to user `u123`.
```kibana
service:inventory-service
 AND level:ERROR
 AND metadata.user_id:"u123"
 AND @timestamp>now-1h
```
**Output Snippet:**
```json
[
  { "timestamp": "2023-10-15T14:30:45.123Z", "service": "inventory-service", "level": "ERROR", "message": "Stock insufficient", "metadata": { "user_id": "u123", "product_id": "p789" } }
]
```

---

### **3. Metrics Query (Prometheus/Grafana)**
**Use Case:** Alert on `checkout-service` latency exceeding 500ms for 5 minutes.
```promql
rate(http_request_duration_seconds_bucket{service="checkout-service"}[5m])
  > 0.5
  AND histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="checkout-service"}[5m]))
  > 0.5
```
**Trigger:** Grafana alert with SLO breach notification.

---

### **4. Service Mesh Debugging (Istio)**
**Use Case:** Inspect traffic between `frontend-service` and `api-gateway`.
```bash
kubectl exec -it $(kubectl get pod -l istio-injection=enabled -o jsonpath='{.items[0].metadata.name}') -c istio-proxy -- curl -s http://localhost:15004/healthz/ready | jq
```
**Output:**
```json
{
  "outbound|443||api-gateway.default.svc.cluster.local": {
    "success": false,
    "reason": "CIRCUIT_BREAKER_OPEN"
  }
}
```

---

### **5. Chaos Engineering Query (Gremlin)**
**Use Case:** Simulate a `payment-service` failure to test circuit breakers.
```yaml
# gremlin.yaml
targets:
  - name: payment-service
    action: kill_pods
    probability: 0.3
    duration: 10s
```
**Result:** Observe `checkout-service` fallback to a backup payment processor.

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Resilience: Circuit Breaker]** | Limits cascading failures via automatic service degradation.                   | High-latency dependencies (e.g., third-party APIs).                          |
| **[Observability: Centralized Logging]** | Aggregates logs from all services in a single pipeline.                         | Debugging across multiservice transactions.                                  |
| **[Service Mesh: mTLS]**         | Encrypts inter-service traffic for security.                                   | Compliance-heavy environments (e.g., healthcare).                           |
| **[Chaos Engineering]**           | Proactively tests system resilience by injecting failures.                     | Pre-release stability validation.                                              |
| **[Canary Deployments]**          | Gradually rolls out changes to a subset of users for risk mitigation.         | Feature rollouts in production.                                                |

---

## **Troubleshooting Checklist**
1. **Reproduce the Issue:**
   - Check logs (`kubectl logs <pod>`) and traces (Jaeger UI).
   - Verify metrics (Prometheus/Grafana) for anomalies.
2. **Isolate the Service:**
   - Use `curl -v` or `istioctl authn tls` to inspect service traffic.
   - Test dependencies manually (e.g., mock database responses).
3. **Analyze Dependencies:**
   - Check DLQs for failed events (Kafka/SQS).
   - Review circuit breaker metrics (e.g., `istio_envoy_circuit_breakers`).
4. **Rollback or Mitigate:**
   - Trigger a canary rollback or manual retry.
   - Adjust timeouts/retry policies in config maps.

---
**Tools to Bookmark:**
- [OpenTelemetry Collector](https://opentelemetry.io/docs/instrumentation/) (Tracing/Metrics)
- [Loki](https://grafana.com/oss/loki/) (Log aggregation)
- [Chaos Mesh](https://chaos-mesh.org/) (Chaos engineering)
- [Istio CLI](https://istio.io/latest/docs/tasks/tools/install-istioctl/) (Service mesh debugging)