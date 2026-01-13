# **[Pattern] Deployment Monitoring – Reference Guide**

---

## **Overview**
Deployment Monitoring is a **post-deployment observability pattern** that ensures new releases are deployed correctly and perform as expected in production. This pattern combines **metrics, logs, traces, and synthetic monitoring** to:
- Detect anomalies (e.g., traffic spikes, errors, latency)
- Correlate failures across services
- Automate rollbacks or alerts
- Provide root-cause analysis (RCA) for incidents

Typically implemented with **distributed tracing (OpenTelemetry, Jaeger), monitoring tools (Prometheus, Datadog), and incident management (PagerDuty, Opsgenie)**.

---
## **Schema Reference**
| **Category**       | **Key Components**                                                                 | **Tools/Libraries**                          |
|--------------------|------------------------------------------------------------------------------------|---------------------------------------------|
| **Metrics**        | - Custom counters (success/failure requests)                                      | Prometheus, Grafana, Datadog               |
|                    | - Percentiles (p99 latency)                                                        |                                              |
|                    | - Throughput (RPS, error rates)                                                   |                                              |
| **Logs**           | - Structured logging (JSON) with correlation IDs                                   | Fluentd, ELK Stack                          |
|                    | - Anomaly detection (e.g., log spike alerts)                                        | Splunk, Datadog Logs                        |
| **Traces**         | - Distributed tracing (request flows, latency breakdown)                           | OpenTelemetry, Jaeger, Zipkin              |
|                    | - Auto-instrumentation (SDKs for APIs, databases, caches)                          |                                              |
| **Synthetic Checks**| - Synthetic transactions (HTTP/REST, browser rendering)                           | New Relic, Synthetics (AWS/GCP), Checkly    |
| **Alerting**       | - Multi-channel (email, Slack, PagerDuty)                                           | Alertmanager, Opsgenie                       |
|                    | - Adaptive thresholds (e.g., error rate < 0.1% baseline)                          |                                              |
| **Incident Management** | - RCA workflows (SRE playbooks)                                                   | Jira, Linear, GitHub Issues                 |
|                    | - Rollback triggers (automated or manual)                                          | Argo Rollouts, Flagger                      |

---

## **Key Concepts**
### **1. Pre-Deployment Checks**
- **Canary Deployment Validation**:
  Ensure traffic is routed to a subset of users before full release.
  ```yaml
  # Example: Argo Rollouts canary analysis
  canary:
    trafficRouting:
      nginx:
        service:
          port: 80
        canaryAnalysis:
          metrics:
            - name: "request_latency"
              threshold: 95
              interval: "1m"
  ```
- **Synthetic Checks**:
  Simulate user flows pre-deployment.
  ```json
  // Checkly pre-deployment script (JavaScript)
  http.get("https://api.example.com/health");
  expect(statusCode).to.equal(200);
  ```

### **2. Post-Deployment Monitoring**
- **Anomaly Detection**:
  Use statistical baselines (e.g., `PrometheusRecordExporter` + `Alertmanager`).
  ```promql
  # Alert if error rate exceeds 1% for 5m
  rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  ```
- **Distributed Tracing**:
  Trace end-to-end requests to identify bottlenecks.
  ```bash
  # Example OpenTelemetry trace query (Jaeger)
  find_service("payment-service").duration > 500ms | limit(10)
  ```

### **3. Automated Rollbacks**
- **Metrics-Based Rollback**:
  Trigger if error rate or latency exceeds thresholds.
  ```javascript
  // Example: Flagger rollback condition
  if (errorRate > 0.02) {
    triggerRollback();
  }
  ```
- **SLO-Driven Alerting**:
  Monitor error budgets (e.g., 1% error rate for 99.9% SLA).

---

## **Query Examples**
### **1. Prometheus Metrics Queries**
| Use Case                     | Query                                                                 |
|------------------------------|-----------------------------------------------------------------------|
| **High error rate**          | `rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.01` |
| **Latency degradation**      | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 100` |
| **Service dependency failure** | `up{service="payment-service"} == 0`                          |

### **2. OpenTelemetry Trace Analysis**
```bash
# Identify slow spans (500ms+)
otelquery \
  --query 'service.name="frontend" AND duration > 500ms' \
  --output=table
```

### **3. ELK Log Query (Kibana)**
```json
// Find errors with correlation ID
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "term": { "trace.id": "abc123" } }
      ]
    }
  }
}
```

---

## **Implementation Steps**
### **1. Instrumentation**
- **Metrics**: Emit Prometheus/Grafana-compatible metrics.
- **Logs**: Use structured JSON logging (e.g., `pino` in Node.js).
- **Traces**: Add OpenTelemetry SDK to applications.
  ```python
  # Python OpenTelemetry example
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("process_order"):
      # Business logic
  ```

### **2. Alerting Rules**
- **Prometheus Alerts**:
  ```yaml
  # alert_rule.yml
  groups:
  - name: deployment-monitoring
    rules:
    - alert: HighErrorRate
      expr: rate(http_errors_total[5m]) > 0.01
      for: 5m
      labels:
        severity: critical
  ```
- **Synthetic Check Alerts**:
  ```bash
  # Checkly alert condition (Python)
  if response.time > 3000:  # 3s timeout
      trigger_alert("HighLatency")
  ```

### **3. Automated Rollbacks**
- **Argo Rollouts Example**:
  ```yaml
  # rollout.yaml
  canary:
    analysis:
      template:
        name: metrics-analysis
      thresholds:
        success:
          successRate: 99
          interval: 10m
  ```

---

## **Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **Blue-Green Deployment**    | Minimize downtime by running two identical environments.                    |
| **Chaos Engineering**        | Proactively test failure resilience (e.g., `Gremlin`, `Chaos Mesh`).      |
| **Circuit Breakers**        | Stop cascading failures (e.g., `Hystrix`, `Resilience4j`).                  |
| **Service Mesh Observability** | Use Istio/Linkerd for fine-grained traffic control + metrics.              |
| **Feature Flags**           | Gradually roll out features without deployment.                             |

---

## **Troubleshooting**
| Issue                          | Diagnosis Tool               | Fix                                  |
|--------------------------------|-------------------------------|--------------------------------------|
| **High latency spikes**        | OpenTelemetry traces          | Check database queries, caches       |
| **Error rate increase**        | Prometheus metrics + logs    | Review recent code changes            |
| **Missing traces**             | Jaeger/Zipkin                 | Verify OpenTelemetry SDK instrumentation|
| **Alert fatigue**              | Adjust thresholds             | Tune SLOs or add multi-level alerts  |

---
## **Best Practices**
1. **Define SLIs/SLOs** upfront (e.g., "99.9% error-free requests").
2. **Combine synthetic + real-user monitoring** (SRE + DevOps).
3. **Use correlation IDs** to link logs, metrics, and traces.
4. **Automate rollbacks** with clear failure criteria.
5. **Document RCA processes** for future incidents.

---
**Version**: 1.0
**Last Updated**: `$(date +%Y-%m-%d)`
**Contributors**: [Your Team]