# **[Pattern] Datadog Monitoring Integration Patterns – Reference Guide**

---
## **Overview**

This reference guide outlines **Datadog Monitoring Integration Patterns**, detailing how to effectively integrate Datadog with infrastructure, applications, and custom systems. Datadog serves as a unified observability platform for metrics, logs, and traces, enabling real-time monitoring, alerting, and performance analysis. This pattern covers **common integration approaches**, including:

- **Agent-based monitoring** (infrastructure telemetry)
- **API-based instrumentation** (metrics, logs, and traces)
- **Third-party integration** (via custom APIs, webhooks, or connectors)
- **Event-forwarding and log management**
- **SLO-based alerting and observability**

This guide provides **implementation details**, **best practices**, and **common pitfalls** to ensure seamless integration while maximizing Datadog’s observability capabilities.

---

## **2. Schema Reference**

Below are the core **Datadog integration components** and their supported schemas:

| **Category**               | **Component**               | **Description**                                                                 | **Supported Data Types**                          |
|----------------------------|-----------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Host Agents**            | `dd-agent`                  | Collects system metrics (CPU, memory, disk, network).                           | Metrics, Logs, Traces, APM                          |
| **API Integrations**       | `Metrics API`               | Pushes custom metrics via REST API.                                             | Time-series metrics (double, int, string values) |
|                            | `Logs API`                  | Ingests structured/unstructured logs.                                          | JSON, raw text, structured logs (OpenTelemetry)  |
|                            | `Traces API`                | Sent via OpenTelemetry or custom instrumentation.                                | Trace spans, metrics                                |
| **Custom Integrations**    | `Custom Metrics`            | User-defined metrics (e.g., business KPIs).                                    | Metrics, alerts                                    |
|                            | `Event Forwarding`          | Sends external events (e.g., API errors, SLA breaches) to Datadog.              | JSON events                                        |
| **Third-Party Integrations**| `Marketplace Apps**         | Pre-built integrations (AWS, Kubernetes, Prometheus, etc.).                    | Depends on app capabilities                        |
|                            | `Webhooks`                   | Triggers Datadog actions (e.g., alerts, dashboards) from external systems.     | JSON payloads                                      |
| **Infrastructure**         | `Infrastructure Monitoring` | Collects cloud provider metrics (AWS, GCP, Azure).                              | Cloud provider-specific metrics                   |

---

## **3. Implementation Details**

### **3.1 Agent-Based Monitoring (`dd-agent`)**
Deploy the **Datadog Agent** to collect system-level metrics, logs, and traces.

#### **Installation**
```bash
# Linux (Debian/Ubuntu)
curl -L https://raw.githubusercontent.com/DataDog/dd-agent/master/packaging/ddeb/deb/dd-agent.list > /etc/apt/sources.list.d/dd-agent.list
apt-get update && apt-get install dd-agent

# Windows (Chocolatey)
choco install datadog-agent
```

#### **Configuration**
Edit `/etc/dd-agent/dd-agent.conf` and configure:
```yaml
apm_enabled: true
logs_enabled: true
metrics_interval: 10
```

Restart the agent:
```bash
service datadog-agent restart
```

#### **Key Metrics Collected**
| Metric Type       | Example Metrics                          |
|-------------------|------------------------------------------|
| **System**        | CPU usage, memory, disk I/O, network     |
| **Processes**     | Running processes, PID, CPU time         |
| **Logs**          | Application logs (structured/unstructured) |

---

### **3.2 API-Based Instrumentation**

#### **3.2.1 Metrics API**
Push custom metrics via the **Datadog Metrics API**:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "DD-API-KEY: <API_KEY>" \
  -H "DD-APPLICATION-KEY: <APP_KEY>" \
  -d '{
    "series": [
      {
        "metric": "my.custom.metric",
        "points": [[1672531200, 42.0]],
        "tags": ["env:prod", "service:web"]
      }
    ]
  }' \
  "https://api.datadoghq.com/api/v1/series"
```

#### **3.2.2 Logs API**
Ingest logs via HTTP POST:

```bash
curl -X POST \
  -H "DD-API-KEY: <API_KEY>" \
  -H "DD-APPLICATION-KEY: <APP_KEY>" \
  -d @/var/log/app.log \
  "https://http-intake.logs.datadoghq.com/api/v2/logs?dd-api-key=<API_KEY>&dd-source=appLogs&dd-version=1"
```

#### **3.2.3 Traces API (OpenTelemetry)**
Instrument applications with OpenTelemetry:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.datadog import DatadogTraceExporter

provider = TracerProvider()
exporter = DatadogTraceExporter(
    service="my-service",
    api_key="<DD_API_KEY>",
    site="datadoghq.com"
)
provider.add_span_processor(exporter)
trace.set_tracer_provider(provider)
```

---

### **3.3 Third-Party Integrations**

#### **3.3.1 Marketplace Apps**
Use **Datadog’s Marketplace** for pre-built integrations (e.g., AWS CloudWatch, Kubernetes):

```bash
# Example: AWS Integration via CLI
aws cloudwatch put-metric-data --metric-data "Name=MyCustomMetric,Value=100"
```

#### **3.3.2 Webhooks**
Trigger Datadog actions (e.g., alerts) from external systems:

```json
# Example Webhook Payload (Alert Trigger)
{
  "event_type": "MyCustomEvent",
  "title": "High Error Rate",
  "url": "https://app.datadoghq.com/alerts",
  "alert_type": "api_key_authentication_failed"
}
```

---

### **3.4 Event Forwarding & Log Management**
Use **Datadog Events API** to forward custom events:

```bash
curl -X POST \
  -H "DD-API-KEY: <API_KEY>" \
  -H "DD-APPLICATION-KEY: <APP_KEY>" \
  -d '{
    "title": "Server Down",
    "text": "Node-001 is unreachable",
    "tags": ["server:node-001", "status:critical"]
  }' \
  "https://api.datadoghq.com/api/v1/events"
```

---

## **4. Query Examples**

### **4.1 Metrics Queries (Timeseries)**
```sql
-- Avg CPU over last 5 minutes
metrics.last(300, "avg:system.cpu.user{*}")

-- Error rate in API service
metrics.last(60, "api.errors:rate{service:api-web} by {env}")
```

### **4.2 Log Queries (Log Search)**
```sql
-- Find 404 errors in production
logs@*: "404" environment:prod
```

### **4.3 Trace Queries (APM)**
```sql
-- Slowest API calls
apm.query("trace_id:123456", "duration:>1000", sort:duration:desc)
```

---

## **5. Best Practices**

✅ **Use Tags for Filtering**
Always tag metrics/logs with `service`, `env`, and `host` for easier querying.

✅ **Optimize Metric Resolution**
High-cardinality tags (e.g., `user_id`) can impact performance—use aggregations.

✅ **Leverage Alert Rules**
Define **SLOs** (Service Level Objectives) with `downtime`, `thresholds`, and `notifications`.

✅ **Centralize Logs**
Use **Log Management** (`logs@*`) to avoid siloed log sources.

✅ **Security Best Practices**
- Use **IAM roles** for AWS/GCP integrations.
- Rotate **API keys** periodically.
- Encrypt sensitive logs.

---

## **6. Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                      |
|--------------------------------------|----------------------------------------------------|
| **High cardinality**               | Use aggregations (`sum`, `avg`) instead of raw data |
| **Agent misconfigurations**         | Validate `dd-agent` logs (`/var/log/datadog/datadog-agent.log`) |
| **Log flooding**                     | Set log-level filters (e.g., `DEBUG`, `INFO`)       |
| **API rate limits**                  | Implement exponential backoff in API clients        |
| **Missing traces**                   | Ensure OpenTelemetry SDK is properly initialized    |

---

## **7. Related Patterns**
- **[Observability Stack]** – Combine Datadog with Prometheus, Loki, or ELK.
- **[SLO-Based Alerting]** – Define SLIs and SLOs for proactive monitoring.
- **[Multi-Cloud Monitoring]** – Use Datadog’s native cloud provider integrations.
- **[Infrastructure as Code]** – Deploy Datadog with Terraform/Ansible.

---
**Further Reading:**
- [Datadog Docs – Integrations](https://docs.datadoghq.com/integrations/)
- [OpenTelemetry Guide](https://docs.datadoghq.com/extra_guides/opentelemetry/)