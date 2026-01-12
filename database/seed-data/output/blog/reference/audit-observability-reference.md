**[Pattern] Audit Observability Reference Guide**

---

### **Overview**
**Audit Observability** is a design pattern for capturing, storing, and analyzing event logs, system states, and user interactions to detect anomalies, enforce compliance, and enable post-incident analysis. Unlike traditional logging (which often focuses on application-level events), Audit Observability emphasizes **traceability, forensics, and audit trails** for security, governance, and operational resilience.

This guide covers how to implement Audit Observability in distributed systems, cloud-native applications, and traditional enterprise environments. It includes core concepts, schema recommendations, query examples, and integrations with observability tools (e.g., Prometheus, OpenSearch, ELK).

---

### **Key Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Audit Event**       | A structured record of a significant system/user action (e.g., API call, role assignment, database query). Must include metadata like timestamp, actor identity, and outcome.                          |
| **Audit Trail**       | A chronological sequence of audit events for a specific entity (e.g., user, resource). Enables reconstruction of workflows.                                                                                   |
| **Immutability**      | Audit data should be **write-once, read-many (WORM)** to prevent tampering. Use append-only storage (e.g., S3, Blockchain-like ledgers, or immutable logs in OpenSearch).                          |
| **Granularity**       | Balance between verbosity and performance. Capture **what changed** (delta) rather than full state dumps unless critical. Example: Log schema changes, not their entire contents.                      |
| **Retention Policy**  | Define SLAs for compliance (e.g., 7 years for financial audits) or cost efficiency (e.g., 30 days for debugging). Partition data by time or event type.                                               |
| **Linking to Context**| Correlate audit events with observability signals (e.g., trace IDs in distributed systems, error codes in logs). Use tools like **OpenTelemetry** to attach context to audit events.                        |
| **Access Control**    | Restrict audit data access via RBAC (e.g., only security teams can query sensitive logs). Enable **audit of audits** (e.g., log who accessed audit data).                                           |
| **Anomaly Detection** | Use ML/models (e.g., Prometheus Alertmanager, ELK Anomaly Detection) to flag deviations (e.g., sudden spikes in failed logins). Integrate with SIEMs like Splunk or Datadog.                          |

---

### **Schema Reference**
Below is a **recommended schema** for audit events. Adapt fields based on your domain (e.g., add `hsm_operation_id` for HSM systems).

#### **Core Audit Event Schema**
| Field               | Type          | Required | Description                                                                                                                                                                                                 | Example Values                          |
|---------------------|---------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| `@timestamp`        | ISO 8601      | Yes      | Event timestamp (UTC). Use system clock with nanosecond precision.                                                                                                                                         | `2024-01-15T14:30:45.123Z`            |
| `event_id`          | UUID          | Yes      | Unique identifier for the event.                                                                                                                                                                          | `550e8400-e29b-41d4-a716-446655440000` |
| `event_type`        | String        | Yes      | High-level category (e.g., `authentication`, `configuration_change`, `data_access`).                                                                                                                      | `user_role_assignment`                  |
| `event_subtype`     | String        | No       | Subcategory for granularity (e.g., `password_reset`, `role_grant`).                                                                                                                                          | `role_grant`                            |
| `actor`             | Object        | Yes      | Identity of the actor (user/service).                                                                                                                                                                   | `{ "identity": "user:jdoe", "type": "user" }` |
| `resource`          | Object        | Yes      | Target of the event (e.g., DB table, API endpoint).                                                                                                                                                         | `{ "name": "orders_table", "type": "database" }` |
| `outcome`           | Enum          | Yes      | Result (e.g., `success`, `failure`, `denied`).                                                                                                                                                           | `success`                                |
| `details`           | Object        | No       | Free-form structured data (e.g., `{"old_role": "viewer", "new_role": "admin"}`). Use **OpenTelemetry spans** for distributed context.                                                               | `{ "ip_address": "192.168.1.1", "user_agent": "Postman/7.0" }` |
| `request_id`        | String        | No       | Correlates to observability traces (e.g., OpenTelemetry trace ID).                                                                                                                                            | `trace-12345-abcde`                     |
| `metadata`          | Object        | No       | Non-sensitive context (e.g., `environment: "prod"`, `region: "us-west-2"`).                                                                                                                              | `{ "source_ip": "10.0.0.1", "app_version": "1.2.0" }` |

#### **Example Payload**
```json
{
  "@timestamp": "2024-01-15T14:30:45.123Z",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "authentication",
  "event_subtype": "login_attempt",
  "actor": { "identity": "user:jdoe", "type": "user" },
  "resource": { "name": "api/auth", "type": "endpoint" },
  "outcome": "failure",
  "details": {
    "status_code": 403,
    "reason": "mfa_required",
    "failed_attempts": 3
  },
  "request_id": "trace-12345-abcde",
  "metadata": {
    "source_ip": "192.168.1.1",
    "environment": "prod"
  }
}
```

#### **Schema Validation**
- Use **JSON Schema** or **Protobuf** for validation.
- Validate at **ingestion time** (e.g., Fluentd, AWS Kinesis Firehose).
- Example Schema (simplified):
  ```json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["@timestamp", "event_id", "event_type", "actor", "resource", "outcome"],
    "properties": {
      "@timestamp": { "type": "string", "format": "date-time" },
      "details": { "type": ["object", "null"] }
    }
  }
  ```

---

### **Query Examples**
#### **1. Find Failed Login Attempts in the Last 24 Hours**
**Tool:** OpenSearch (DSL Query)
```json
GET /audit_events/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event_type": "authentication" } },
        { "match": { "event_subtype": "login_attempt" } },
        { "range": { "@timestamp": { "gte": "now-24h", "lte": "now" } } }
      ],
      "filter": [ { "term": { "outcome": "failure" } } ]
    }
  },
  "aggs": {
    "by_ip": { "terms": { "field": "details.source_ip" } }
  }
}
```
**Output:** Aggregates failed logins by IP.

#### **2. Correlate Audit Events with Traces (Distributed Systems)**
**Tool:** Loki + Prometheus
**Query (Loki):**
```logql
{job="audit_logs", event_type="authentication"} |= "user:jdoe" AND request_id="trace-12345-abcde"
```
**Correlate with Prometheus:**
```promql
up{job="service_a"} and on(trace_id) tracing_latency{job="service_a", trace_id="12345-abcde"}
```

#### **3. Identify Sensitive Data Access (GDPR Compliance)**
**Tool:** Datadog
**Query:**
```sql
SELECT *
FROM audit_events
WHERE event_type = 'data_access'
  AND resource.name IN ('user_profiles', 'health_records')
  AND actor.type = 'user'
  AND @timestamp > ago(90d)
LIMIT 1000
```
**Action:** Flag accesses to PII fields (e.g., `details.pii_fields` contains `"ssn"`).

#### **4. Detect Unusual Role Assignments**
**Tool:** ELK (Kibana Discover)
**Lucene Query:**
```
event_type: "role_assignment" AND "admin" IN details.new_role AND
not (actor.identity in ("user:admin", "user:root"))
```
**Visualization:** Create a **timeline** chart in Kibana to plot assignments over time.

---

### **Implementation Strategies**
| Strategy                          | Tools/Libraries                                                                 | When to Use                                                                 |
|-----------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Centralized Logging**           | Fluentd, Logstash, AWS CloudWatch Logs                                         | Monolithic apps or simple microservices.                                   |
| **Immutable Storage**             | S3 (Object Lock), OpenSearch (Index Lifecycle Management), Cassandra (Temporal Tables) | Compliance requirements (e.g., HIPAA, GDPR).                               |
| **Real-Time Processing**          | Kafka + Flink, AWS Kinesis + Lambda                                           | High-throughput systems needing anomaly detection in real time.             |
| **Distributed Tracing Integration** | OpenTelemetry, Jaeger, Zipkin                                               | Microservices where context propagation is critical (e.g., `request_id`).   |
| **Automated Alerting**            | Prometheus Alertmanager, Grafana Alerts, Datadog Events                        | Proactive response to suspicious activities (e.g., brute-force attacks).    |
| **Audit of Audit Data**           | Custom RBAC in OpenSearch, AWS IAM for S3, HashiCorp Vault                     | Ensure audit logs themselves are secured.                                   |

---

### **Related Patterns**
| Pattern                          | Description                                                                                                   | Integration with Audit Observability                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| **Distributed Tracing**          | Track requests across services using trace IDs.                                                               | Link audit events to traces (e.g., `request_id` in audit schema).                                                     |
| **Observability with Metrics**   | Use Prometheus/Grafana to monitor system health.                                                              | Correlate metrics (e.g., `error_rate`) with audit events (e.g., `outcome: failure`).                                    |
| **Sentry/Error Tracking**        | Capture exceptions and performance data.                                                                     | Augment audit events with error context (e.g., `details.exception: "NullPointerException"`).                             |
| **Event Sourcing**               | Store state changes as an immutable event log.                                                               | Audit events can mirror event sourcing logs (e.g., `event_type: "domain_event"`).                                     |
| **Zero Trust Security**          | Verify identity and context for every request.                                                               | Audit every access decision (e.g., `outcome: "denied"` due to zero-trust policy).                                     |
| **Chaos Engineering**            | Test system resilience by injecting failures.                                                                 | Audit events during chaos experiments to analyze impacts (e.g., `event_type: "chaos_experiment"`).                       |

---

### **Best Practices**
1. **Start Small**: Begin with high-value events (e.g., authentication, role changes) and expand.
2. **Standardize Event Types**: Use a **taxonomy** (e.g., [OWASP Audit Event Taxonomy](https://owasp.org/www-project-audit-event-taxonomy/)).
3. **Optimize Performance**: Avoid logging entire objects; use **event sourcing deltas** or **diff snapshots**.
4. **Automate Enrichment**: Add context dynamically (e.g., geolocation via IP, user attributes from a directory service).
5. **Test Retrieval**: Simulate audits (e.g., "Find all accesses to `user:ceo` in 2024") to validate schema/query design.
6. **Document Non-Events**: Explicitly log **denials** (e.g., `outcome: "denied": "rule: rate_limit_exceeded"`).
7. **Compliance Mapping**: Align schema fields with standards (e.g., ISO 27001, SOC 2).

---
### **Anti-Patterns**
| Anti-Pattern                      | Risk                                                                       | Fix                                                                         |
|-----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Over-Logging**                  | High storage costs, noise in queries.                                      | Focus on **significant changes** (e.g., config updates, not GET requests).|
| **No Immutability**               | Tampered logs undermining trust.                                           | Use append-only storage (e.g., S3 Object Lock).                           |
| **Weak Correlations**             | Inability to trace incidents end-to-end.                                   |Attach `request_id`, `trace_id`, or `span_id` to audit events.              |
| **Ignoring Anomalies**            | Undetected breaches or misconfigurations.                                  | Set up alerts for deviations (e.g., "50 failed logins in 1 minute").     |
| **Inconsistent Schema**           | Hard to query or analyze.                                                  | Enforce schema validation (e.g., JSON Schema, Protobuf).                 |

---
### **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│             │    │             │    │                 │    │                 │
│  Service A  ├───►│  OpenTelemetry│───►│  Kafka (Audit Topic)│───►│  OpenSearch   │
│             │    │  Collector   │    │                 │    │  (Immutable ILM)│
└─────────────┘    └────────┬───────┘    └─────────────────┘    └────────┬───────┘
                                                     │                   │
                                                     ▼                   ▼
                                          ┌─────────────────┐    ┌─────────────────┐
                                          │                 │    │                 │
                                          │  Fluentd (Filter)│───►│  Prometheus   │
                                          │                 │    │  Alertmanager   │
                                          └─────────────────┘    └────────┬───────┘
                                                                                    │
                                                                                    ▼
                                                              ┌─────────────────┐
                                                              │                 │
                                                              │   SIEM (Splunk) │
                                                              │                 │
                                                              └─────────────────┘
```
**Flow**:
1. Services emit audit events via OpenTelemetry.
2. Kafka buffers events for replayability.
3. Fluentd enriches/filters events before storing them in OpenSearch.
4. Prometheus detects anomalies (e.g., spikes in `outcome: failure`).
5. SIEM correlates events across tools.

---
### **Further Reading**
- [OWASP Audit Event Taxonomy](https://owasp.org/www-project-audit-event-taxonomy/)
- [OpenTelemetry Audit Logging](https://opentelemetry.io/docs/specs/otel/sdklogs/)
- [GDPR Compliance Guide for Logs](https://ico.org.uk/for-organisations/guide-to-data-protection/gdpr-article-30/)
- [Immutable Logs with AWS](https://aws.amazon.com/blogs/database/immutable-data-wal-and-amazon-aurora/)