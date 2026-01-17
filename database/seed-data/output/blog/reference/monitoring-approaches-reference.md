# **[Pattern] Monitoring Approaches Reference Guide**

---

## **Overview**
The **Monitoring Approaches** pattern provides a structured way to observe, analyze, and respond to system behavior, performance, and operational health. Monitoring ensures resilience, detects anomalies, and enables proactive troubleshooting. This pattern categorizes monitoring into four key approaches—**Infrastructure, Application, Log-based, and Synthetic Monitoring**—each with distinct tools, metrics, and use cases.

Each approach may be implemented independently or combined for comprehensive observability. This guide outlines the core concepts, schema constructs, implementation considerations, and example queries for each approach.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **Monitoring Approach** | A specific strategy to collect, analyze, and act on system telemetry (metrics, logs, traces).      |
| **Metric**             | A quantifiable measure of system behavior (e.g., CPU usage, request latency).                     |
| **Alert Condition**    | A rule defining when an alert is triggered (e.g., latency > 2s).                                  |
| **Data Source**        | Where telemetry is collected (e.g., Prometheus for metrics, ELK for logs).                        |
| **Integration**        | Plugins or APIs that connect monitoring tools to systems (e.g., Prometheus Node Exporter).        |

---

## **Schema Reference**
Below are schema tables for each monitoring approach.

### **1. Infrastructure Monitoring**
Collects hardware and OS-level telemetry (CPU, memory, disk, network).

| **Component**       | **Field**       | **Type**       | **Description**                                                                                     |
|--------------------|----------------|----------------|-----------------------------------------------------------------------------------------------------|
| `metric`           | `name`         | `string`       | Metric identifier (e.g., `cpu_usage`).                                                              |
|                    | `value`        | `float`        | Current metric value.                                                                               |
|                    | `unit`         | `string`       | Unit (e.g., "percent", "bytes").                                                                   |
| `node`             | `host`         | `string`       | Hostname/IP of the monitored node.                                                                  |
|                    | `os`           | `string`       | OS (e.g., "Linux", "Windows").                                                                     |
| `alert_condition`  | `threshold`    | `float`        | Alert threshold (e.g., 90 for CPU).                                                                  |
|                    | `severity`     | `string`       | Alert severity ("critical", "warning").                                                             |
|                    | `action`       | `string`       | Remediation step (e.g., "restart_service").                                                       |

---

### **2. Application Monitoring**
Tracks application performance, user requests, and business logic.

| **Component**       | **Field**       | **Type**       | **Description**                                                                                     |
|--------------------|----------------|----------------|-----------------------------------------------------------------------------------------------------|
| `metric`           | `type`         | `string`       | Metric category (e.g., "response_time", "error_rate").                                              |
|                    | `endpoint`     | `string`       | API endpoint (e.g., "/api/v1/users").                                                               |
| `request`          | `id`           | `string`       | Unique request ID.                                                                                 |
|                    | `method`       | `string`       | HTTP method (e.g., "GET", "POST").                                                                  |
| `alert_condition`  | `latency_ms`   | `int`          | Max allowed latency (e.g., 500).                                                                    |
|                    | `error_count`  | `int`          | Max allowed errors (e.g., 0).                                                                       |

---

### **3. Log-Based Monitoring**
Analyzes structured/log files for patterns (errors, warnings, performance).

| **Component**       | **Field**       | **Type**       | **Description**                                                                                     |
|--------------------|----------------|----------------|-----------------------------------------------------------------------------------------------------|
| `log`              | `timestamp`    | `datetime`     | Log entry timestamp.                                                                               |
|                    | `level`        | `string`       | Log severity ("INFO", "ERROR").                                                                     |
|                    | `message`      | `string`       | Raw log message.                                                                                   |
| `source`           | `app`          | `string`       | Application name (e.g., "auth-service").                                                            |
| `alert_condition`  | `pattern`      | `string`       | Regex or keyword (e.g., "DATABASE_CONNECTION_FAILED").                                             |
|                    | `count`        | `int`          | Max allowed occurrences (e.g., 3).                                                                  |

---

### **4. Synthetic Monitoring**
Simulates user interactions to test system availability and performance.

| **Component**       | **Field**       | **Type**       | **Description**                                                                                     |
|--------------------|----------------|----------------|-----------------------------------------------------------------------------------------------------|
| `test`             | `name`         | `string`       | Test identifier (e.g., "login_flow").                                                                |
|                    | `url`          | `string`       | Target URL (e.g., "https://example.com/login").                                                    |
| `result`           | `status`       | `string`       | Response status (e.g., "pass", "fail").                                                             |
|                    | `duration_ms`  | `int`          | Execution time.                                                                                   |
| `alert_condition`  | `freq`         | `int`          | Test frequency (e.g., "every 5m").                                                                 |
|                    | `timeout_ms`   | `int`          | Max allowed duration (e.g., 2000).                                                                |

---

## **Implementation Details**
### **1. Infrastructure Monitoring**
**Tools:** Prometheus, Grafana, Datadog, Zabbix
- **How it works:** Agents (e.g., Prometheus Node Exporter) collect metrics from OS and hardware.
- **Example Use Case:** Alert on high disk usage (>90%) to prevent failures.

```yaml
# Prometheus alert rule example
groups:
  - name: disk_alerts
    rules:
      - alert: HighDiskUsage
        expr: node_filesystem_usage{mountpoint="/"} > 0.9
        for: 5m
        labels:
          severity: critical
```

---

### **2. Application Monitoring**
**Tools:** New Relic, AppDynamics, OpenTelemetry
- **How it works:** Instrument code to emit metrics (e.g., request duration) or use APM tools.
- **Example Use Case:** Detect API latency spikes (e.g., >500ms) during traffic surges.

```sql
-- Example query in Prometheus
SELECT
  endpoint,
  avg(response_time_ms) as avg_latency
FROM application_metrics
WHERE timestamp > now() - 1h
GROUP BY endpoint
HAVING avg_latency > 500;
```

---

### **3. Log-Based Monitoring**
**Tools:** ELK Stack, Splunk, Loki
- **How it works:** Parse logs for structured data (e.g., JSON) and apply rules.
- **Example Use Case:** Alert on repeated "connection timeout" errors in logs.

```elk
# Kibana Lucene query for ELK
level: ERROR AND message: "connection timeout" AND @timestamp > now-1h
```

---

### **4. Synthetic Monitoring**
**Tools:** Synthetic.io, Pingdom, UptimeRobot
- **How it works:** Scheduled HTTP requests or scripts simulate user actions.
- **Example Use Case:** Verify a payment gateway is reachable every 15 minutes.

```python
# Python (requests) example for synthetic test
import requests
response = requests.get("https://example.com/api/payment", timeout=3)
assert response.status_code == 200, "Test failed"
```

---

## **Query Examples**
| **Approach**         | **Query Type**       | **Example**                                                                                     |
|----------------------|----------------------|-------------------------------------------------------------------------------------------------|
| **Infrastructure**   | Prometheus Alert     | `node_cpu_seconds_total > 10 AND on() rate(node_cpu_seconds_total[5m]) > 1`                  |
| **Application**      | Metrics Aggregation  | `avg(by(endpoint) (rate(http_requests_total[5m])) > 1000`                                     |
| **Log-Based**        | ELK Search           | `source: "auth-service" AND level: ERROR AND "failed login"`                                    |
| **Synthetic**        | Synthetic Dashboard  | `test_name: "checkout_flow" AND status: "fail"`                                               |

---

## **Related Patterns**
1. **[Resilience Patterns](link):** Use redundancy and retries to handle failures detected by monitoring.
2. **[Observability Patterns](link):** Combine metrics, logs, and traces for deeper insights.
3. **[Alerting Strategies](link):** Define how to prioritize and act on alerts (e.g., noise filtering).
4. **[Infrastructure as Code (IaC)](link):** Automate monitoring tool deployment (e.g., Prometheus via Terraform).

---
**Note:** Adjust tools and queries based on your tech stack (e.g., use OpenTelemetry for multi-language apps). For production, validate queries in staging first.