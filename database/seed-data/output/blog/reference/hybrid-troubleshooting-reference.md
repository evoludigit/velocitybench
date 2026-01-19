# **[Pattern] Hybrid Troubleshooting Reference Guide**

---
## **Overview**
Hybrid Troubleshooting combines *on-premises* and *cloud-based* diagnostics to resolve issues spanning heterogeneous environments (e.g., legacy systems + SaaS integrations). This pattern leverages **centralized logging, distributed tracing, AI-driven anomaly detection, and cross-platform agents** to triangulate root causes efficiently.

The key benefit is **reduced diagnostic time** in multi-cloud or mixed-environment deployments, where traditional siloed tools (e.g., Wireshark for LAN, Prometheus for microservices) fail to correlate events across boundaries. This guide covers architecture, schema, query patterns, and complementary techniques.

---
## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Hybrid Agent**       | Lightweight proxy (e.g., Fluent Bit, OpenTelemetry Collector) that bridges on-prem → cloud.      | Agent logs Kubernetes events to Loki while forwarding Windows Event Logs to Datadog.          |
| **Telemetry Hub**      | Cloud-native platform (e.g., Grafana Cloud, Splunk) where hybrid data converges.                | Centralized timeline correlating AWS CloudTrail + local Nginx logs.                                |
| **Cross-Platform Tracing** | Distributed tracing (e.g., OpenTelemetry) linking requests across hybrid layers (API → DB → edge). | Trace: `Browser → API Gateway (AWS) → Local Monolith → Database (SQL Server)`.              |
| **Anomaly Correlation** | AI/ML models (e.g., Prometheus Alertmanager, Elastic SIEM) comparing on-prem baselines vs. cloud metrics. | Detects "unusually high" local CPU usage (baseline: 10%) + missing cloud audit logs (cloud: 0%). |

---
## **Schema Reference**
### **1. Event Schema (Structured Logging)**
| **Field**          | **Type**       | **Description**                                                                                     | **Example**                                  |
|--------------------|----------------|----------------------------------------------------------------------------------------------------|----------------------------------------------|
| `timestamp`        | ISO 8601       | Event recorded time (UTC).                                                                      | `"2024-05-20T14:30:00Z"`                    |
| `source`           | String         | Hybrid source (e.g., `"k8s-pod"`, `"aws-kms"`, `"on-prem-sql"`).                               | `"on-prem-sql"`                              |
| `severity`         | Enum (DEBUG/WARN/ERROR/CRITICAL) | Log level for prioritization.                                                              | `"ERROR"`                                    |
| `trace_id`         | UUID           | Distributed trace identifier (correlates across systems).                                        | `"550e8400-e29b-41d4-a716-446655440000"`      |
| `correlation_id`   | String         | Business transaction ID (e.g., order ID).                                                       | `"order_abc123"`                             |
| `metadata`         | JSON           | Key-value pairs for context (e.g., `{"user_id": "123", "pod_name": "web-server01"}`).         | `{"host": "db-prod-01", "status": "TIMEOUT"}` |

---
### **2. Hybrid Trace Schema (OpenTelemetry)**
| **Attribute**       | **Type**       | **Description**                                                                                     | **Example**                                  |
|--------------------|----------------|----------------------------------------------------------------------------------------------------|----------------------------------------------|
| `span.name`        | String         | Operation name (e.g., `"authenticate_user"`).                                                       | `"call_aws_lambda"`                          |
| `service.name`     | String         | System/container name (e.g., `"on-prem-webapp"`, `"aws-dynamodb"`).                              | `"on-prem-webapp"`                           |
| `attributes`       | JSON           | Custom context (e.g., `"{http.method: 'POST', db.query: 'SELECT * FROM users'}"`).
| `links`            | Array[Link]    | References to parent/child spans across boundaries.                                                 | `[{trace_id: "other-uuid", span_id: "child"}]` |

---
### **3. Correlation Rules (SIEM/Alertmanager)**
| **Rule Type**       | **Condition**                                                                                     | **Action**                                                                                     |
|---------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Cross-Source Alert** | `source="on-prem-sql" AND severity=ERROR AND "timeout" IN metadata.query` **OR** `source="aws-cloudtrail" AND action="Deny"` | Trigger incident: `{"type": "security", "priority": "P1", "details": {}}`       |
| **Hybrid Baseline Drift** | `(cloud_metric="aws_cpu_util") > (on-prem_baseline_cpu + 3%)` **OR** `(latency_p95 > 1.5 * baseline)` | Escalate to SRE team via PagerDuty.                                                           |

---
## **Query Examples**
### **1. Correlate Logs Across Sources (Loki/Grafana)**
```sql
# Find on-prem SQL errors linked to AWS cloudtrail API calls
log
  | json
  | filter(
      (source="on-prem-sql" AND severity="ERROR") OR
      (source="aws-cloudtrail" AND eventName="CreateTable")
    )
  | line_format `{{.timestamp}} {{.source}}: {{.metadata}}`
```
**Output:**
```
2024-05-20T14:30:00Z on-prem-sql: {"query": "SELECT * FROM users", "error": "timeout"}
2024-05-20T14:31:00Z aws-cloudtrail: {"eventName": "CreateTable", "userIdentity": "admin"}
```

---
### **2. Distributed Trace Analysis (Jaeger/Zipkin)**
```bash
# Query traces where on-prem server -> AWS Lambda
curl -G \
  --url "http://jaeger-query:16686/search" \
  -d "query=%22service.name%3D%22on-prem-webapp%22%20AND%20service.name%3D%22aws-lambda%22%22"
```
**Key Fields to Inspect:**
- `duration` (latency spikes).
- `attributes.http.method` (unexpected `POST` calls).
- `links` (child spans in Lambda).

---
### **3. Anomaly Detection (Prometheus + Rule Groups)**
```yaml
# alerts.yaml
groups:
- name: hybrid-baseline-alerts
  rules:
  - alert: HighCloudTrailErrors
    expr: >-
      cloudwatch_metric.aws_cloudtrail_errors
      > (on_prem_average_errors * 1.5)
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "CloudTrail errors spike ({{$value}} > {{(on_prem_average_errors * 1.5)}})"
```

---
## **Implementation Steps**
### **1. Deploy Hybrid Agents**
- **On-Premise:** Install Fluent Bit (log shipper) + OpenTelemetry Collector (trace agent).
  ```bash
  # Example: Ship Windows Event Logs to Loki
  fluent-bit.service {
    [OUTPUT]
      Name          loki
      Match         *
      Host          loki.example.com
      Label_Job     windows_events
      Label_Stream  security
  }
  ```
- **Cloud:** Use native agents (e.g., AWS CloudWatch Agent) + forward to on-prem SIEM (Splunk).

### **2. Correlate Data in Central Hub**
- **Option A (Loki + Grafana):**
  ```bash
  # Create a Dashboard with:
  # 1. On-prem logs (Loki).
  # 2. Cloud metrics (Prometheus).
  # 3. Distributed traces (Jaeger).
  ```
- **Option B (Elasticsearch + Beats):**
  ```json
  # Elasticsearch mapping for hybrid events
  {
    "mappings": {
      "properties": {
        "source": { "type": "keyword" },
        "trace_id": { "type": "keyword" },
        "correlation_id": { "type": "keyword" }
      }
    }
  }
  ```

### **3. Set Up Correlation Rules**
- **SIEM (Splunk):**
  ```spl
  # Correlate on-prem failures + cloud API errors
  index=hybrid
  | rex field=_raw "source=(?<source>.+?), severity=(?<severity>.+)"
  | stats valuesSeverity=severity by source, correlation_id
  | where severity="ERROR" AND count > 1
  ```
- **Alertmanager (Prometheus):**
  ```yaml
  # Group alerts by correlation_id
  group_by: [correlation_id]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  ```

---
## **Query Patterns for Common Scenarios**
| **Scenario**                          | **Query/Rule**                                                                                     | **Tools**                              |
|----------------------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------|
| **On-prem DB timeout → Cloud API error** | `log | filter(source="on-prem-sql" AND "timeout") OR (source="aws-api-gateway" AND status=500)`   | Loki/Grafana                         |
| **Increased latency in hybrid flow**   | `trace | filter(service.name="on-prem" OR service.name="aws") | hist(latency)`                        | Jaeger/Zipkin                        |
| **Security anomaly (e.g., unsanctioned access)** | `cloudtrail | filter(action="AssumeRole") AND not userIdentity="known-admin"` | CloudWatch/SIEM (Splunk)          |
| **Resource exhaustion (on-prem + cloud)** | `metric | alert if (on_prem_cpu > 90% AND cloud_cpu > on_prem_baseline * 1.2)` | Prometheus/Grafana Cloud         |

---
## **Related Patterns**
1. **[Distributed Tracing]** – Foundational for cross-system correlation (see OpenTelemetry docs).
2. **[Centralized Logging]** – Prerequisite for hybrid analysis (e.g., Fluent Bit → Loki).
3. **[Chaos Engineering]** – Validate resilience of hybrid workflows (e.g., kill on-prem pods to test cloud failover).
4. **[Service Mesh (Istio/Linkerd)** – Simplifies hybrid service-to-service observability.
5. **[GitOps Observability]** – Sync dashboards/configs via Git (e.g., Prometheus + ArgoCD).

---
## **Troubleshooting Tips**
| **Issue**                          | **Checklist**                                                                                     | **Tools**                          |
|-------------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------|
| **Missing logs in cloud hub**       | - Verify agent config (`fluent-bit -D`).                                                           | `journalctl -u fluent-bit`         |
|                                   | - Check network (firewall, VPN).                                                                  | `tcpdump`                          |
| **Correlation ID mismatches**       | - Validate `trace_id`/`correlation_id` in logs vs. traces.                                        | Jaeger UI                          |
| **High latency in hybrid flow**     | - Compare on-prem vs. cloud P99 latencies.                                                           | Grafana Explore                     |
|                                   | - Look for `db.query` attributes in traces.                                                       | OpenTelemetry Collector Metrics   |
| **False positives in alerts**       | - Adjust baseline thresholds (e.g., `on_prem_baseline_cpu`).                                       | Prometheus Rule Groups             |

---
## **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  On-Prem     │    │  Hybrid     │    │  Cloud     │
│  (Windows/)  │    │  Agent      │    │  (AWS/GCP)  │
│  - SQL       │───▶│ (Fluent Bit)|───▶│  - Lambda  │
│  - K8s Pods  │    │ (OpenTelos.)│    │  - DynamoDB │
└─────────────┘    └─────────────┘    └─────────────┘
                             ▲
                             │ (HTTP/OTLP)
                             ▼
┌─────────────────────────────────────────────────────┐
│                 Central Hub (Grafana/Splunk)         │
│  - Loki (Logs) │ Prometheus (Metrics) │ Jaeger (Traces) │
└─────────────────────────────────────────────────────┘
```

---
## **Further Reading**
- [OpenTelemetry Hybrid Collector Docs](https://opentelemetry.io/docs/collector/)
- [Loki + Jaeger Integration Guide](https://grafana.com/docs/loki/latest/clients/jaeger/)
- [Prometheus Hybrid Alerting](https://prometheus.io/docs/alerting/latest/)

---
**Last Updated:** `2024-05-20`
**Version:** `1.2` (Added Jaeger integration examples).