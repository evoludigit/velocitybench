# **[Pattern] Monitoring & Troubleshooting Reference Guide**

---

## **Overview**
The **"Monitoring & Troubleshooting"** pattern provides a structured approach to detecting, diagnosing, and resolving issues in systems, applications, or services. By implementing proactive monitoring, automated alerting, and systematic troubleshooting workflows, this pattern minimizes downtime, reduces resolution time, and improves system reliability. This guide covers key components—such as metrics collection, alerting rules, log analysis, and incident response—along with implementation best practices for different environments (cloud, on-premises, or hybrid).

---
## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                 | **Key Attributes**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Monitoring System**  | Collects system, application, and business metrics (e.g., CPU, latency, errors). | Supports open-source (Prometheus, Grafana) or vendor tools (New Relic, Datadog).  |
| **Alerting Rules**     | Defines thresholds for triggering alerts (e.g., "Error rate > 10% for 5 mins"). | Adjustable sensitivity (critical/warning/info), notification channels (Slack, PagerDuty). |
| **Log Analysis**       | Parses and correlates logs for root-cause analysis (e.g., `fail2ban` blocks). | Uses structured logging (JSON) + tools like ELK Stack or Loki.                   |
| **Incident Management**| Standardizes triage, escalation, and remediation workflows.                    | Integrates with Jira, ServiceNow, or custom runbooks.                             |
| **Performance Baselines** | Establishes normal behavior (e.g., "95th percentile latency < 500ms").        | Tracks anomalies via statistical methods (e.g., Z-score, moving averages).         |

---

### **2. Data Flow**
1. **Collect** metrics/logs from sources (hosts, databases, APIs).
2. **Aggregate** data (e.g., per-minute averages) to reduce noise.
3. **Alert** on deviations (e.g., "Disk usage > 90%").
4. **Analyze** logs/metrics to confirm root causes.
5. **Resolve** issues via automated remediation or human intervention.
6. **Review** post-mortems to prevent recurrence.

**Tools:** Prometheus (metrics), Fluentd/Fluent Bit (logs), OpenTelemetry (distributed tracing).

---

### **3. Best Practices**
- **Granularity:** Monitor at a sufficient level (e.g., per-container vs. per-host).
- **Retention:** Store critical metrics/logs for at least 30–90 days.
- **Alert Fatigue:** Limit alerts to actionable events; use "alert silencing" for non-critical periods.
- **Root Cause Analysis (RCA):** Correlate metrics/logs (e.g., spikes in `5xx` errors → database timeouts).
- **Automation:** Use playbooks (Ansible, Terraform) for repetitive fixes (e.g., restarting a failed service).

---

## **Schema Reference**
### **Monitoring Metric Schema**
| **Field**            | **Type**       | **Description**                                                                 | **Example Values**                          |
|----------------------|----------------|-------------------------------------------------------------------------------|---------------------------------------------|
| `metric_name`        | String         | Unique identifier (e.g., `http_requests_total`).                             | `"error_rate"`                              |
| `labels`             | Key-Value Map  | Categorical dimensions (e.g., `env=prod`, `service=api`).                    | `{"environment": "production", "service": "auth"}` |
| `value`              | Numeric        | Numeric data point (e.g., 15.2, 0.85).                                      | `42.0` (requests per second)                |
| `timestamp`          | ISO 8601       | When the data was recorded (UTC).                                            | `"2024-01-15T14:30:00Z"`                   |
| `unit`               | String         | Measurement unit (e.g., `requests/sec`, `milliseconds`).                    | `"ms"`                                      |

---
### **Alert Rule Schema**
| **Field**            | **Type**       | **Description**                                                                 | **Example**                                 |
|----------------------|----------------|-------------------------------------------------------------------------------|---------------------------------------------|
| `name`               | String         | Human-readable alert name (e.g., "High Database Latency").                   | `"db_sluggish"`                             |
| `expression`         | String         | PromQL/Grafana expression (e.g., `rate(http_errors[5m]) > 0.1`).              | `sum(rate(api_errors_total{env="prod"}[5m])) by (service) > 10` |
| `severity`           | String         | Priority level (`critical`, `warning`, `info`).                               | `"warning"`                                 |
| `channels`           | Array          | Notification targets (Slack, email, PagerDuty).                               | `["slack", "email"]`                        |
| `silence_duration`   | Duration       | Auto-suppress alerts if unresolved (e.g., `5m`).                             | `"PT1H"` (1 hour)                           |
| `annotations`        | Key-Value Map  | Additional context for alerts (e.g., `deployment: "v1.2.3"`).                | `{"deployment": "blue", "team": "backend"}` |

---

## **Query Examples**
### **1. PromQL Queries**
**a) High Error Rate:**
```promql
rate(http_requests_total{status=~"5.."}[1m]) / rate(http_requests_total[1m]) > 0.05
```
**b) Disk Space Alert:**
```promql
(node_filesystem_usage{device="/", mountpoint="/"} * 100) > 85
```
**c) Custom Service-Specific Metric:**
```promql
sum(rate(api_payment_failures_total[5m])) by (region) > 5
```

### **2. Log Query (Grafana Loki)**
**a) Find Failed API Calls:**
```loki
{job="api-service"} | json | status_code == "500" | count_over_time(30m)
```
**b) Filter by Error Type:**
```loki
{job="backend"} |~ "ERROR: .*" | count by (service)
```

### **3. Incidence Analysis (JQL-like)**
**Filter active incidents for a service:**
```sql
SELECT id, status, created_at
FROM incidents
WHERE service = 'payment' AND status = 'open'
ORDER BY created_at DESC
LIMIT 10
```

---

## **Implementation Steps**
### **1. Set Up Monitoring**
- **Metrics:** Deploy Prometheus + Grafana for scraping endpoints (e.g., `/metrics`).
- **Logs:** Ship logs to Loki/ELK via Fluentd:
  ```ini
  [OUTPUT]
      Name forward
      Match *
      Host grafana-loki
      Port 3100
  ```
- **Metrics:** Instrument applications with SDKs (e.g., OpenTelemetry for distributed tracing).

### **2. Configure Alerts**
**Example Prometheus Alert Rule (`alert.rules`):**
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_duration_seconds_bucket[5m])) > 1.0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High 95th percentile latency"
    description: "Duration > 1s for {{ $labels.job }}"
```
**Enable in Prometheus:**
```yaml
rule_files:
  - "/etc/prometheus/alert.rules.yml"
```

### **3. Troubleshoot**
**Scenario:** Sudden spikes in `http_5xx` errors.
1. **Check Alerts:** Confirm if the alert fired (Grafana Dashboard).
2. **Drill into Logs:**
   ```loki
   {job="api"} | json | status_code == "500" | line_format "{{.status_code}}: {{.error_message}}"
   ```
3. **Compare with Metrics:**
   - Plot `http_requests_total` vs. `db_connections`.
   - Look for spikes in `db_response_time`.
4. **Resolve:** Scale out database or fix query bottleneck.

### **4. Automate Remediation**
**Example: Auto-restart Failed Service (Terraform)**
```hcl
resource "null_resource" "restart_service" {
  triggers = {
    last_modified = timestamp()
  }

  provisioner "local-exec" {
    command = "if curl -s http://localhost:8080/health | grep -q 'error'; then docker restart api-service; fi"
  }
}
```

---

## **Query Examples by Use Case**

| **Use Case**               | **Query Type**       | **Example Query**                                                                 |
|----------------------------|----------------------|-----------------------------------------------------------------------------------|
| **CPU Overload**           | PromQL               | `rate(container_cpu_usage_seconds_total{image!="pause"}[5m]) > 1.0`               |
| **Database Connection Leaks** | PromQL       | `increase(db_connections{mode="active"}[5m]) > 500`                               |
| **Slow API Endpoints**     | Grafana Loki         | `{job="api"} | json | duration > 2000 | count by (endpoint)`                     |
| **Failed Deployments**     | PromQL + Logs        | `on(job) group_left promhttp_scrape_error > 0 union on(job) {job="app"} |~ "Deployment failed"` |
| **Network Latency Spikes** | PromQL               | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 500` |

---

## **Related Patterns**
1. **[Observability Pattern]**
   - **Connection:** Extends monitoring with distributed tracing and APM (Application Performance Monitoring).
   - **Tools:** Jaeger, Zipkin, Datadog APM.

2. **[Chaos Engineering Pattern]**
   - **Connection:** Uses controlled failures to test monitoring/troubleshooting resilience.
   - **Tools:** Gremlin, Chaos Mesh.

3. **[Auto-Scaling Pattern]**
   - **Connection:** Dynamic scaling triggers when monitoring detects resource constraints.
   - **Example:** Scale up Kubernetes pods if `cpu_usage > 80%`.

4. **[Infrastructure as Code (IaC)]**
   - **Connection:** Deploys monitoring tools consistently via Terraform/Ansible.
   - **Example:** Prometheus operator for Kubernetes.

5. **[Security Monitoring Pattern]**
   - **Connection:** Focuses on anomaly detection in logs/metrics (e.g., unusual login attempts).
   - **Tools:** Falcon, Aqua Security.

6. **[Goldilocks Principle]**
   - **Connection:** Balances monitoring overhead (e.g., sampling high-cardinality metrics).

---
## **Troubleshooting Checklist**
| **Step**               | **Action Items**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------|
| **Alert Spark**         | Verify alert configuration in Prometheus/Grafana.                                                  |
| **Data Corruption**     | Check for incomplete scrapes (`prometheus_tsdb_head_samples` metric).                              |
| **Log Parsing Issues**  | Validate log format (e.g., `logfmt` vs. JSON).                                                     |
| **False Positives**     | Adjust thresholds or add exclude labels (e.g., `env="dev"`).                                       |
| **Performance Bottleneck** | Profile with `pprof` or OpenTelemetry.                                                           |
| **Incident Backlog**    | Apply RCA templates (e.g., "5 Whys" or "Fishbone Diagram").                                         |

---
## **Common Pitfalls & Mitigations**
| **Pitfall**                     | **Mitigation**                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------|
| Alert Fatigue                    | Implement "alert damping" (e.g., only alert if state changes).                                    |
| Over-Monitoring                  | Limit dimensions (labels) to avoid cardinality explosion.                                        |
| Reactive Troubleshooting        | Use structured logs + metrics for proactive root-cause analysis.                                  |
| Vendor Lock-in                   | Use open formats (PromQL, OpenTelemetry) for portability.                                        |
| Ignoring Business Metrics        | Include KPIs (e.g., "revenue_churn" alongside technical metrics).                                |

---
## **Further Reading**
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Loki Guide](https://grafana.com/docs/loki/latest/)
- [SRE Book (Google)](https://sre.google/sre-book/table-of-contents/)
- [OpenTelemetry Specifications](https://opentelemetry.io/docs/specs/)