# **[Pattern] On-Premise Monitoring: Reference Guide**

---

## **Overview**
On-Premise Monitoring (OPM) is a pattern for deploying monitoring infrastructure within an organization’s private data center or dedicated server environment. This approach ensures **data sovereignty, control over infrastructure, and reduced dependency on third-party services**, while enabling real-time visibility into application, infrastructure, and performance metrics.

OPM is ideal for businesses with:
- **Compliance or security requirements** (e.g., HIPAA, GDPR, PCI-DSS).
- **High-performance or latency-sensitive applications** requiring local processing.
- **Limited or unreliable external connectivity** (e.g., remote sites, air-gapped environments).
- **Need for custom telemetry pipelines** (e.g., proprietary data formats, legacy systems).

Unlike cloud-native monitoring (e.g., AWS CloudWatch, Azure Monitor), OPM requires manual deployment, maintenance, and scaling but offers **full ownership of monitoring telemetry** and **absence of vendor lock-in**.

---

## **Implementation Details**

### **Key Concepts**
| Concept               | Definition                                                                                     | Example Tools/Technologies                          |
|-----------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Agent-Based Monitoring** | Collects metrics via lightweight agents installed on monitored hosts.                            | Prometheus Agent, Telegraf, Datadog Agent            |
| **Centralized Logging** | Aggregates logs from applications and systems into a structured repository.                     | ELK Stack (Elasticsearch, Logstash, Kibana), Grafana Loki |
| **Metrics Collection**   | Gathers numerical data (e.g., CPU, memory, request latency) via polling or push-based models.    | Prometheus, Zabbix, Nagios                             |
| **Alerting**          | Triggers notifications when thresholds or anomalies are detected.                              | Alertmanager, PagerDuty, Opsgenie                      |
| **Data Storage**      | Persists metrics, logs, and traces for historical analysis and trend detection.                | InfluxDB, TimescaleDB, ClickHouse, PostgreSQL        |
| **Visualization**     | Renders dashboards and charts for operational insights.                                         | Grafana, Kibana, Datadog Dashboards                 |
| **Retention Policies** | Defines how long data is stored before being purged (e.g., 7 days, 1 year).                    | Configurable in Prometheus, Elasticsearch, etc.     |

### **Architecture Layers**
OPM typically follows a **4-layer architecture**:

1. **Data Sources** (Where metrics/logs are generated)
   - Applications, virtual machines, containers, IoT devices, databases.
   - Example: A Java app emitting logs via Java Agent.

2. **Collection Layer** (Ingests data into a standardized format)
   - Agents (e.g., Telegraf, Prometheus Node Exporter) or forwarders (e.g., Fluentd, Logstash).
   - Example: Telegraf collects system metrics and forwards them to InfluxDB.

3. **Processing Layer** (Normalizes, enriches, and stores data)
   - Time-series databases (TSDB), search engines (Elasticsearch), or warehouses (ClickHouse).
   - Example: Prometheus stores metrics; Elasticsearch indexes logs.

4. **Consumption Layer** (Provides insights to users)
   - Dashboards (Grafana), alerts (Alertmanager), and analytics tools.
   - Example: Grafana dashboard displaying CPU utilization over time.

---

## **Schema Reference**
The following tables define common OPM schemas for **metrics**, **logs**, and **alerts**.

### **1. Metrics Schema (Prometheus/InfluxDB-Compatible)**
| Field          | Type     | Description                                                                 | Example Value               |
|----------------|----------|-----------------------------------------------------------------------------|-----------------------------|
| `timestamp`    | `int64`  | Unix epoch time in milliseconds (ISO 8601 format).                          | `1712345678901`             |
| `metrics_type` | `string` | Category: `cpu`, `memory`, `disk`, `network`, `application`.                | `"cpu"`                     |
| `host`         | `string` | Identifies the monitored machine/user.                                      | `"web-server-01"`           |
| `namespace`    | `string` | Optional grouping (e.g., `deployment`, `service`).                          | `"nginx"`                   |
| `metric_name`  | `string` | Specific metric (e.g., `usage`, `latency`, `errors`).                       | `"cpu_usage_percent"`       |
| `value`        | `float`  | Numeric value of the metric.                                                 | `75.2`                      |
| `unit`         | `string` | SI unit (e.g., `percent`, `milliseconds`, `bytes`).                         | `"%"`                       |
| `labels`       | `map`    | Key-value pairs for filtering/dimensioning (e.g., `env:prod`, `region:eu`). | `{"env":"prod", "region":"eu"}` |

**Example Payload:**
```json
{
  "timestamp": 1712345678901,
  "metrics_type": "cpu",
  "host": "web-server-01",
  "namespace": "nginx",
  "metric_name": "cpu_usage_percent",
  "value": 75.2,
  "unit": "%",
  "labels": {"env": "prod", "region": "eu"}
}
```

---

### **2. Logs Schema (ELK-Compatible)**
| Field          | Type     | Description                                                                 | Example Value                     |
|----------------|----------|-----------------------------------------------------------------------------|-----------------------------------|
| `timestamp`    | `string` | ISO 8601 formatted log event time.                                          | `"2024-04-05T14:30:45.123Z"`     |
| `host`         | `string` | Name of the host generating the log.                                         | `"app-server-02"`                |
| `level`        | `string` | Severity: `debug`, `info`, `warn`, `error`, `fatal`.                        | `"error"`                        |
| `service`      | `string` | Application/component name.                                                 | `"auth-service"`                 |
| `message`      | `string` | Raw log content.                                                            | `"Failed to validate token"`      |
| `metadata`     | `map`    | Key-value pairs (e.g., `user_id`, `request_id`, `error_code`).              | `{"user_id": "123", "error_code": "E403"}` |

**Example Payload:**
```json
{
  "timestamp": "2024-04-05T14:30:45.123Z",
  "host": "app-server-02",
  "level": "error",
  "service": "auth-service",
  "message": "Failed to validate token",
  "metadata": {"user_id": "123", "error_code": "E403"}
}
```

---

### **3. Alerts Schema (Alertmanager-Compatible)**
| Field          | Type     | Description                                                                 | Example Value               |
|----------------|----------|-----------------------------------------------------------------------------|-----------------------------|
| `alert_name`   | `string` | Unique identifier for the alert rule.                                        | `"high_cpu_usage"`          |
| `status`       | `string` | `firing` (active), `resolved` (inactive), `pending` (not yet triggered).    | `"firing"`                   |
| `severity`     | `string` | Priority: `critical`, `high`, `medium`, `low`.                               | `"high"`                    |
| `timestamp`    | `string` | When the alert state changed (ISO 8601).                                     | `"2024-04-05T15:00:00Z"`    |
| `metrics`      | `map`    | Metrics that triggered the alert (e.g., `cpu_usage_percent > 90`).           | `{"cpu_usage_percent": 95}`  |
| `labels`       | `map`    | Contextual labels (e.g., `host`, `namespace`).                                | `{"host": "db-01"}`         |
| `annotations`  | `map`    | Human-readable details (e.g., `summary`, `description`).                      | `{"summary": "DB CPU overload"}` |

**Example Payload:**
```json
{
  "alert_name": "high_cpu_usage",
  "status": "firing",
  "severity": "high",
  "timestamp": "2024-04-05T15:00:00Z",
  "metrics": {"cpu_usage_percent": 95},
  "labels": {"host": "db-01"},
  "annotations": {
    "summary": "High CPU usage on db-01 (95%)",
    "description": "Check for resource contention or failing queries."
  }
}
```

---

## **Query Examples**
### **1. PromQL (Prometheus Query Language)**
**Query:** Find hosts where CPU usage exceeds 80% over the last 5 minutes.
```promql
sum by (host) (rate(node_cpu_seconds_total{mode="user"}[5m])) * 100 > 80
```
**Output:**
```
host="web-server-01" 92
host="db-01"          85
```

**Query:** Average response time for `/api/health` endpoints over 1 hour.
```promql
avg by (service) (http_request_duration_seconds{endpoint="/api/health"}[1h])
```
**Output:**
```
service="auth-service" 0.345
service="order-service" 0.456
```

---

### **2. LogQL (Elasticsearch/Grafana Loki)**
**Query:** Count `error`-level logs from `auth-service` in the last hour.
```logql
{service="auth-service", level="error"} | count() by level
```
**Output:**
```
level    count
error    12
```

**Query:** Find logs containing `"timeout"` and extract `request_id`.
```logql
{level="warn"} | regex (".*timeout.*request_id=(\\w+).*")
```
**Output:**
```
host    request_id
app-01  abc123
app-02  def456
```

---

### **3. Alertmanager Query (Filter Firing Alerts)**
**Query:** List all `critical` alerts for `db-*` hosts.
```yaml
groups:
- name: db-alerts
  rules:
  - alert: HighDBLoad
    expr: db_connections_used > 90% for 5m
    labels:
      severity: critical
    annotations:
      summary: "Database {{ $labels.instance }} is under high load"
```
**API Call:**
```bash
curl -X GET "http://localhost:9093/api/v2/alerts?status=firing&label_match~=severity=critical&label_match~=host=~db-.*"
```

---

## **Deployment Checklist**
| Step                          | Tools/Configurations                          | Notes                                  |
|-------------------------------|-----------------------------------------------|----------------------------------------|
| **1. Infrastructure Setup**  | Virtual machines, Kubernetes clusters, or bare metal. | Ensure redundancy for critical nodes. |
| **2. Agent Deployment**       | Prometheus Node Exporter, Telegraf, Datadog Agent. | Configure auto-updates for agents.    |
| **3. Data Storage**           | Prometheus, InfluxDB, Elasticsearch.          | Set retention policies (e.g., 30 days). |
| **4. Centralized Logging**    | Fluentd, Logstash, or Loki.                   | Index logs with relevant fields.      |
| **5. Alerting Rules**         | Alertmanager, PagerDuty, or Slack webhooks.   | Test alerts with mock data.            |
| **6. Visualization**          | Grafana dashboards, Kibana dashboards.       | Share dashboards via Grafana Cloud.   |
| **7. Backup & Recovery**      | Regular snapshots of databases (e.g., Prometheus, Elasticsearch). | Test restore procedures.           |

---

## **Related Patterns**
| Pattern                          | Use Case                                  | Integration with OPM                          |
|----------------------------------|-------------------------------------------|---------------------------------------------|
| **[Infrastructure as Code (IaC)]** | Automate OPM deployment (e.g., Terraform, Ansible). | Define monitoring stack in IaC templates. |
| **[Centralized Logging]**        | Aggregate logs from diverse sources.      | Use Fluentd/Logstash to forward logs to Elasticsearch. |
| **[Distributed Tracing]**        | Track requests across microservices.      | Integrate Jaeger or OpenTelemetry with OPM agents. |
| **[Chaos Engineering]**           | Test system resilience.                   | Use Gremlin or Chaos Mesh alongside OPM alerts. |
| **[ observability Mesh]**       | Unified metrics, logs, and traces.        | Adopt Grafana + Prometheus + Loki stack.   |

---

## **Best Practices**
1. **Start Small**: Deploy OPM for a single critical service before scaling.
2. **Monitor Agents Themselves**: Use Prometheus to track agent health (e.g., scrape latency).
3. **Optimize Retention**: purge old data to reduce storage costs (e.g., keep metrics for 30 days).
4. **Secure Data**: Encrypt logs/metrics in transit (TLS) and at rest (e.g., Elasticsearch encryption).
5. **Document Alert Policies**: Define SLA-based thresholds (e.g., "P99 latency > 500ms").
6. **Automate Scaling**: Use horizontal pod autoscalers (Kubernetes) or auto-scaling groups for agents.
7. **Monitor Agent Performance**: High-cardinality metrics (e.g., `job=*` in Prometheus) can overload storage.

---
**References**:
- [Prometheus Documentation](https://prometheus.io/docs/)
- [ELK Stack Guide](https://www.elastic.co/guide/en/elk-stack/index.html)
- [Grafana Documentation](https://grafana.com/docs/)
- [CNCF Observability Forums](https://community.cncf.io/)