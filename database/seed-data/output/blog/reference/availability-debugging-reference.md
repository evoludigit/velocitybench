# **[Pattern] Availability Debugging Reference Guide**

---

## **Overview**
The **Availability Debugging** pattern helps identify and resolve end-to-end system failures by systematically inspecting dependencies, performance bottlenecks, and resource constraints that degrade availability. This pattern is critical for SLO/SLA monitoring, incident resolution, and proactively mitigating outages.

Key objectives:
- **Trace root causes** of degraded availability (e.g., low throughput, high latency, errors).
- **Validate assumptions** about system behavior under load.
- **Diagnose cascading failures** across services and infrastructure.

This guide covers **concepts, data structures, query examples**, and complementary patterns for effective availability debugging.

---

## **Key Concepts & Implementation Details**

### **1. Availability Metrics & Signals**
Track these core signals to detect availability issues:
| **Metric**               | **Description**                                                                                     | **Tools/Examples**                          |
|--------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Availability (%)**     | % of time the system meets uptime targets (e.g., 99.9% SLO).                                         | CloudWatch, Prometheus, Datadog             |
| **Error Rate**           | Incident rate of failed requests (e.g., HTTP 5xx, API timeouts).                                     | OpenTelemetry, Jaeger, Kubernetes Events    |
| **Throughput**           | Requests/second (RPS) or transactions processed.                                                   | APM tools (e.g., New Relic, Dynatrace)      |
| **Latency (P99, P99.9)** | Percentile latency (e.g., 99th percentile response time).                                          | traceroute, Pingdom                           |
| **Resource Utilization** | CPU, memory, disk I/O, or database load under load.                                                | `top`, `vmstat`, Prometheus (`node_exporter`) |
| **Dependency Failures**  | Errors in upstream services (e.g., database timeouts, external API failures).                    | Service mesh (Istio, Linkerd), Circuit Breakers |

---

### **2. Debugging Phases**
Follow this **structured workflow** to isolate availability issues:

| **Phase**               | **Action Items**                                                                                     | **Tools/Queries**                          |
|-------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------|
| **1. Validate Observability Data** | Check if data is being collected (e.g., logs, metrics, traces).                                   | `kubectl logs`, Grafana dashboards         |
| **2. Correlate Symptoms**         | Align error metrics with business impact (e.g., "5xx errors spike during peak traffic").           | Log correlation (ELK, Splunk), Alertmanager |
| **3. Reproduce Under Load**       | Test under real-world conditions (e.g., Chaos Engineering, canary testing).                       | Locust, k6, Gremlin                          |
| **4. Isolate the Root Cause**   | Drill down from high-level metrics to low-level failures (e.g., DB connection leaks).           | Debugging tools (e.g., `strace`, `coredumps`) |
| **5. Validate Fixes**             | Confirm the fix resolves the issue without introducing regressions.                               | Automated rollback tests, A/B testing      |

---

### **3. Common Availability Pitfalls**
| **Pitfall**                     | **Description**                                                                                     | **Mitigation**                              |
|----------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Noisy Neighbor Syndrome**      | One process consumes excessive resources (e.g., CPU, memory), degrading others.                  | Resource quotas, container limits           |
| **Cascading Failures**           | A single dependency failure propagates across services.                                           | Circuit breakers, retries with backoff     |
| **Cold Start Latency**           | Delayed response due to initialization (e.g., serverless functions).                             | Warm-up requests, pre-initialized instances|
| **Thundering Herd**              | Sudden spike in requests overwhelming downstream services.                                       | Rate limiting, progressive scaling          |
| **Data Corruption**              | Silent failures due to inconsistent state (e.g., database inconsistencies).                      | Serializable transactions, backups         |

---

## **Schema Reference**

### **1. Availability Metrics Schema**
```json
{
  "availability": {
    "type": "object",
    "description": "System availability metrics over time.",
    "properties": {
      "timestamp": { "type": "string", "format": "date-time" },
      "uptime": { "type": "number", "format": "float", "minimum": 0, "maximum": 1 },
      "error_rate": { "type": "number", "format": "float", "minimum": 0 },
      "throughput": { "type": "integer", "minimum": 0 },
      "latency_p99": { "type": "number", "minimum": 0 },
      "dependencies": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "status": { "enum": ["up", "down", "degraded"] },
            "errors": { "type": "integer", "minimum": 0 }
          }
        }
      }
    }
  }
}
```

### **2. Debugging Session Schema**
```json
{
  "debug_session": {
    "type": "object",
    "properties": {
      "session_id": { "type": "string" },
      "start_time": { "type": "string", "format": "date-time" },
      "end_time": { "type": "string", "format": "date-time", "nullable": true },
      "steps": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "step": { "type": "string" },  // e.g., "check_logs", "load_test"
            "tools_used": { "type": "array", "items": { "type": "string" } },
            "findings": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": { "type": "string" },
                  "severity": { "enum": ["low", "medium", "high", "critical"] },
                  "recommendation": { "type": "string" }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## **Query Examples**

### **1. Detecting Anomalous Error Spikes (PromQL)**
```promql
# Find error rate spikes (e.g., HTTP 5xx) in the last hour
rate(http_requests_total{status=~"5.."}[1h]) by (service) > 0.1
```
**Action:** Investigate the `service` with escalating errors.

---

### **2. Identifying High-Latency Dependencies (OpenTelemetry)**
```sql
-- SQL-like query on OpenTelemetry traces (e.g., using Tempo)
SELECT
  service_name,
  AVG(duration),
  PERCENTILE(duration, 99) AS p99_latency
FROM traces
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND resource.labels.env = 'prod'
  AND status_code != 'OK'
GROUP BY service_name
ORDER BY p99_latency DESC
LIMIT 10;
```

---

### **3. Resource Utilization Alert (CloudWatch)**
```cloudwatch
# Alert if CPU > 90% for 5 minutes
METRIC: 'CPUUtilization'
  STATS: avg
  DIMENSION: InstanceId
  PERIOD: 300
  OPERATOR: GreaterThanThreshold
  THRESHOLD: 90
  DURATION: 300
  EVALUATION_PERIODS: 1
```

---

### **4. Dependency Failure Correlation (Grafana)**
**Visualization Query:**
```grafana
# Correlate "db_connection_errors" with "app_latency"
SELECT
  time,
  AVG(db_connection_errors),
  AVG(app_latency)
FROM metrics
WHERE time > now() - 1h
GROUP BY time
```
**Action:** Plot both metrics to identify coinciding spikes.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **Use When...**                              |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **[Distributed Tracing]** | Trace requests across services to identify bottlenecks.                                         | Latency spikes without clear error logs.     |
| **[Chaos Engineering]**   | Intentionally introduce failures to test resilience.                                             | Proactively validating high-availability SLOs.|
| **[Rate Limiting]**       | Control request volume to prevent cascading failures.                                           | Thundering herd during promotions.           |
| **[Circuit Breaker]**     | Automatically isolate failing dependencies.                                                      | External API timeouts degrading service.     |
| **[Canary Releases]**     | Gradually roll out changes to reduce blast radius.                                              | Feature flags causing availability drops.    |

---

## **Next Steps**
1. **Instrument your system** with observability tools (metrics, logs, traces).
2. **Define SLOs/SLIs** to baseline availability expectations.
3. **Automate alerts** for deviation from normal patterns.
4. **Reproduce issues** in staging using load tests.
5. **Document findings** in a structured debugging session schema.

---
**Feedback welcome!** Contribute to this guide on [GitHub](https://github.com/example/patterns).