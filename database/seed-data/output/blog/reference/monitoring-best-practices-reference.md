# **[Pattern] Monitoring Best Practices – Reference Guide**

## **Overview**
Effective monitoring ensures system reliability, performance, and rapid incident resolution. This guide outlines **best practices** for designing, implementing, and maintaining a robust monitoring solution. It covers key concepts (e.g., observability, thresholds, alerting), implementation considerations (e.g., tools, data retention), and actionable patterns for distributed systems, microservices, and infrastructure.

Best practices emphasized:
✔ **Comprehensive observability** (metrics, logs, traces)
✔ **Proactive alerting** (SLA-driven thresholds)
✔ **Scalable tooling** (centralized vs. agent-based approaches)
✔ **Minimal noise** (alert fatigue prevention)
✔ **Cost-efficient storage** (retention policies, sampling)

---

## **Schema Reference**
| **Category**       | **Key Attributes**                                                                 | **Example Values**                                                                 |
|--------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Metrics**        | Name, Unit, Data Type, Frequency, Aggregation Method, Thresholds, Alert Condition | `CPU_Usage (%, gauge, per 5m, avg, >90% → Alert)`                                  |
| **Logs**          | Log Level, Source, Retention Days, Structured/Unstructured, Sampling Rate        | `{level: "ERROR", source: "api-service", retention: "7d", structured: true}`       |
| **Traces**        | Trace ID, Span Sampling Rate, Maximum Duration, Storage Backend                   | `trace_id: "123x45y6-z789", rate: 0.1, backend: "OTLP"`                            |
| **Alerts**        | Condition, Severity, Notification Channels, Dedup Window, Silence Rules            | `{condition: "cpu > 90% for 10m", severity: "CRITICAL", channels: ["email", "SMS"]}` |
| **Dashboards**    | Widgets, Time Range, Shared Access, Widget Refresh Rate                           | `widgets: ["CPU Usage (5m avg)", "Latency Percentiles"], shared: true, refresh: 5m` |
| **Incidents**     | Status (Open/Resolved), Owner, Root Cause Analysis, Resolution Time               | `status: "OPEN", owner: "ops-team", rca: "disk-full-snapshot", time: "12h"`         |

---

## **Implementation Details**

### **1. Observability Principles**
**Core Components:**
- **Metrics:** Numerical data (e.g., CPU, requests/sec) used for performance tracking.
- **Logs:** Textual records of events (structured or raw).
- **Traces:** End-to-end request flows (latency, dependencies).

**Tool Selection:**
| **Use Case**               | **Recommended Tools**                          | **Why?**                                                                         |
|----------------------------|-----------------------------------------------|---------------------------------------------------------------------------------|
| **Metrics**                | Prometheus, Datadog, Cloud Monitoring         | High-cardinality support, alerting rules                                         |
| **Logs**                   | ELK Stack (Elasticsearch, Logstash, Kibana), Lumberjack | Full-text search, log enrichment, retention policies                             |
| **Traces**                 | OpenTelemetry, Jaeger, Zipkin                   | Distributed tracing, sampling optimization                                       |
| **Alerting**               | Alertmanager, PagerDuty, Opsgenie              | Multi-channel notifications, incident workflows                                  |

**Best Practices:**
-Use **OpenTelemetry (OTel)** for vendor-agnostic telemetry collection.
-Store **logs as structured JSON** where possible (e.g., `{"timestamp": "2023-10-01T12:00:00", "level": "ERROR", "error": "DB timeout"}`).

---

### **2. Metrics: Design & Thresholding**
**Key Considerations:**
- **Time Series Granularity:** Higher frequency (e.g., 1m) for dynamic systems; lower (e.g., 5m) for static metrics.
- **Thresholds:** Avoid hardcoded values; base on **Service Level Objectives (SLOs)**.
  Example SLO: "99.9% of API requests < 500ms latency."
- **Warn vs. Critical:**
  - **Warn:** 95th percentile latency > 300ms.
  - **Critical:** 99.9th percentile > 500ms for 5m.

**Query Examples (PromQL):**
```promql
# 1. CPU Usage (per-core avg)
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (node) / sum(container_spec_cpu_shares{container!=""}) by (node)

# 2. API Latency P99 (filter by endpoint)
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, route))
```

---

### **3. Alerting: Avoiding Noise**
**Anti-Patterns:**
- Alerting on **flapping metrics** (e.g., "CPU > 90%" for 1m).
- **Noisy thresholds** (e.g., alerting on every 1% increase in latency).

**Solutions:**
- **Deduplication:** Group alerts by root cause (e.g., "all pods in `nginx` namespace down").
- **Slack/Email Silence:** Auto-suppress alerts for planned outages (e.g., "maintenance at 2023-10-05 08:00 UTC").
- **Alert Condition Templates:**
  ```yaml
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01 * rate(http_requests_total[5m])
    labels:
      severity: warning
    annotations:
      summary: "High error rate ({{ $value }}% errors)"
  ```

**Tools for Noise Reduction:**
- **Correlate alerts** (e.g., Alertmanager’s `group_by`).
- **Alert fatique:** Use **severeity levels** (e.g., CRITICAL → SLACK; WARNING → Email).

---

### **4. Logs: Storage & Analysis**
**Best Practices:**
- **Retention Policies:**
  - **High Volume (e.g., application logs):** 7–30 days (compressed).
  - **Critical Logs (e.g., auth failures):** 90+ days (immutable storage).
- **Sampling:** Reduce volume for non-critical services (e.g., `sampling_rate: 0.1`).
- **Enrichment:** Add contextual data (e.g., `request_id`, `user_session`).

**Log Query Examples (Kibana):**
```json
// Filter errors in API gateway for the last 24h
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } },
        { "term": { "service": "api-gateway" } }
      ]
    }
  }
}
```

---

### **5. Traces: Distributed Systems**
**Key Metrics:**
- **Latency Percentiles** (P50, P90, P99).
- **Error Rates** per service.
- **Dependency Graphs** (e.g., "DB calls from `user-service` take 80% of response time").

**Sampling Strategy:**
- **Production:** 1–10% sampling rate (reduce load).
- **Debugging:** 100% sampling (short-lived).

**Trace Query Example (Jaeger CLI):**
```bash
# Find slowest endpoints in the last hour
jaeger query --query 'service:user-service AND duration > 500ms AND duration < 2000ms'
```

---

### **6. Dashboards: Actionable Views**
**Design Principles:**
- **Focus on SLOs:** Dashboards should reflect **reliability, performance, and cost**.
- **Avoid Overloading:** Limit to 5–7 key metrics per dashboard.
- **Dynamic Time Ranges:** Default to last 6h, allow "last 24h" toggle.

**Example Dashboard Layout:**
1. **Health Check** (status of critical services).
2. **Latency Breakdown** (request flow by service).
3. **Error Rate** (per endpoint).
4. **Resource Utilization** (CPU, memory, disk).
5. **Business Metrics** (e.g., "active users").

**Tools:**
- **Grafana** (templates, variables for multi-tenant dashboards).
- **Dynatrace** (auto-detection of dependencies).

---

### **7. Incident Response & Postmortems**
**Checklist for Handling Alerts:**
1. **Acknowledge** within 5m (e.g., "Alerting team on it").
2. **Diagnose:**
   - Isolate the issue (e.g., "All pods in `db` namespace crashing").
   - Check related metrics/logs (e.g., "OOMKilled events").
3. **Resolve:** Follow runbooks (e.g., "Restart pods").
4. **Communicate:** Update teams via Slack/email.
5. **Postmortem:** Document root cause, fixes, and prevention (e.g., "Add resource limits").

**Tools:**
- **Incident Management:** PagerDuty, Jira Service Desk.
- **Postmortem Templates:**
  ```markdown
  # Incident: DB Connection Pools Exhausted
  - **Time:** 2023-10-02 14:30–15:15 UTC
  - **Impact:** API 5xx errors for 45m.
  - **Root Cause:** Misconfigured `max_connections` in PostgreSQL.
  - **Fix:** Scaled up replicas.
  - **Prevention:** Add alert for `pg_connections` > 80% for 5m.
  ```

---

## **Query Examples**

### **Prometheus Alert Rule (YAML)**
```yaml
groups:
- name: api-alerts
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 500
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High P99 latency on {{ $labels.route }} ({{ $value }}s)"
```

### **Grafana Dashboard Variables**
```json
// Define a variable for environments (dev/stage/prod)
{
  "name": "env",
  "type": "query",
  "current": {"text": "prod", "value": "prod"},
  "options": [
    { "text": "Development", "value": "dev" },
    { "text": "Staging",     "value": "stage" },
    { "text": "Production",  "value": "prod" }
  ]
}
```

### **Elasticsearch Log Filter (KQL)**
```json
// Find duplicate errors in the last hour
{
  "query": {
    "bool": {
      "must": [
        { "term": { "message": "Connection refused" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    },
    "aggs": {
      "hosts": { "terms": { "field": "host" } }
    }
  }
}
```

---

## **Related Patterns**
1. **[Resilience Patterns](link)** – Circuit breakers, retries, and timeouts to handle failures gracefully.
2. **[SLO & Error Budgeting](link)** – Define reliability targets and allocate "error budgets."
3. **[Chaos Engineering](link)** – Proactively test system resilience with controlled failures.
4. **[Infrastructure as Code (IaC)](link)** – Deploy monitoring tooling via Terraform/CloudFormation.
5. **[Security Monitoring](link)** – Log anomalous behavior (e.g., failed auth attempts).

---
**Key Takeaways:**
- **Start small:** Focus on critical SLOs before expanding monitoring scope.
- **Automate everything:** Use tools to reduce manual alert triage.
- **Review regularly:** Update thresholds and dashboards quarterly.