# **[Pattern] Audit Integration Reference Guide**

## **Overview**
Audit Integration is a design pattern used to systematically capture, store, and log changes to system data, configurations, and events for **compliance, security, and observability**. It ensures an immutable history of all modifications, enabling auditing, forensics, and regulatory adherence. This pattern applies across systems like databases, APIs, microservices, and configuration management tools, acting as a **single source of truth** for audit records.

Audit Integration differs from traditional logging by focusing on **recorded changes** rather than transient events. It supports:
- **Compliance reporting** (e.g., GDPR, SOC2, HIPAA)
- **Security incident response** (e.g., identifying unauthorized modifications)
- **Change tracking** (e.g., CI/CD pipelines, configuration drifts)

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| Component               | Description                                                                                     | Example                                          |
|-------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Audit Log Source**    | Generates raw audit events (e.g., API calls, DB transactions, file modifications).              | Database triggers, middleware interceptors      |
| **Audit Pipeline**      | Processes logs (filtering, enrichment, deduplication).                                        | Apache Flume, AWS Kinesis                        |
| **Audit Storage**       | Persists logs in a queryable format (e.g., immutable time-series DB, SIEM).                  | Elasticsearch, Splunk, AWS CloudTrail            |
| **Audit Consumer**      | Analyzes logs for alerts, compliance checks, or metrics.                                      | Custom scripts, SIEM dashboards, third-party tools|
| **Audit Schema**        | Standardized structure for logs (fields like `user`, `timestamp`, `action`, `resource`).       | JSON schema, OpenSearch Audit Log Standard       |

---

### **2. Audit Integration Strategies**
| Strategy               | Description                                                                                     | Use Case Example                                  |
|-------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Database Triggers**   | Automatically log changes to tables via DB hooks (e.g., PostgreSQL `AFTER` triggers).         | Tracking user credentials updates.               |
| **API Gateways**        | Intercept HTTP requests/responses to log metadata (e.g., requester IP, payload).             | Monitoring REST API calls.                       |
| **Middleware Interceptors** | Wrap services to log method invocations (e.g., Spring AOP, AWS Lambda layers).              | Microservices activity tracking.                 |
| **Configuration Management** | Hook into tools like Ansible/Puppet to log infrastructure changes.                          | Cloud resource provisioning.                    |
| **Hybrid Approach**     | Combine multiple sources (e.g., DB + API) for comprehensive auditing.                        | Multi-tiered application monitoring.             |

---

### **3. Data Retention & Compliance**
- **Retention Policies**: Define how long logs are stored (e.g., 7 days for debug, 7+ years for compliance).
- **Immutable Storage**: Use write-once-read-many (WORM) storage (e.g., S3 Object Lock, Azure Blob Immutability).
- **Access Control**: Implement **least-privilege access** for audit logs (e.g., read-only for analysts).
- **Regulatory Mapping**: Align with frameworks like:
  - **GDPR**: Right to erasure (pseudo-anonymize PII).
  - **SOC2**: Continuous monitoring of system changes.
  - **HIPAA**: Audit trails for protected health info.

---

## **Schema Reference**
Below is a **standardized audit log schema** (JSON format) supporting most use cases. Adjust fields as needed.

| Field               | Type     | Required | Description                                                                                     | Example Values                          |
|---------------------|----------|----------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| `@timestamp`        | String   | Yes      | ISO-8601 timestamp of the event.                                                              | `"2024-05-20T14:30:45Z"`               |
| `event_id`          | String   | Yes      | Unique identifier for the audit event.                                                        | `"audit-12345"`                          |
| `event_type`        | String   | Yes      | Category of event (e.g., `authentication`, `data_modification`).                              | `"user_creation"`                       |
| `resource`          | Object   | Yes      | Details of the affected resource (e.g., `table`, `API_endpoint`).                             | `{"type": "user", "name": "john_doe"}`  |
| `action`            | String   | Yes      | Verb describing the change (e.g., `create`, `update`, `delete`).                             | `"update_password"`                     |
| `actor`             | Object   | Yes      | User/system performing the action.                                                          | `{"id": "user_6789", "type": "user"}`   |
| `old_value`         | Any      | No       | Pre-change state (for `update`/`delete`).                                                    | `{"password": "old_123"}`              |
| `new_value`         | Any      | No       | Post-change state (for `create`/`update`).                                                  | `{"password": "new_abc456"}`            |
| `metadata`          | Object   | No       | Contextual data (e.g., `ip_address`, `correlation_id`).                                     | `{"ip": "192.168.1.1", "session": "xyz"}`|
| `status`            | String   | No       | Success/failure outcome (e.g., `success`, `failed`).                                         | `"success"`                             |
| `error`             | String   | No       | Error details if applicable.                                                              | `"Invalid password format"`             |

---

## **Query Examples**
### **1. Find All Failed Login Attempts (Last 7 Days)**
```sql
SELECT *
FROM audit_logs
WHERE event_type = 'authentication'
  AND action = 'login_attempt'
  AND status = 'failed'
  AND @timestamp >= NOW() - INTERVAL '7 days'
ORDER BY @timestamp DESC;
```

### **2. List Users Modified by a Specific Admin**
```json
// Elasticsearch Query
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event_type": "user_modification" } },
        { "match": { "actor.type": "admin" } },
        { "match": { "actor.id": "admin_101" } }
      ]
    }
  }
}
```

### **3. Track Database Table Changes (SQL)**
```sql
SELECT r.resource, a.action, a.old_value, a.new_value, a.@timestamp
FROM audit_logs a
JOIN resource_mapping r ON a.resource_id = r.id
WHERE r.type = 'table'
  AND a.action IN ('update', 'delete')
  AND a.resource.name = 'user_profiles'
ORDER BY a.@timestamp DESC;
```

### **4. Find Unusual API Access Patterns (Python/Pandas)**
```python
import pandas as pd
from datetime import datetime, timedelta

# Load logs (assume CSV)
logs = pd.read_csv('audit_logs.csv')
logs['@timestamp'] = pd.to_datetime(logs['@timestamp'])

# Filter unusual access (e.g., multiple failed logins in 1 minute)
unusual_access = logs[
    (logs['event_type'] == 'authentication') &
    (logs['action'] == 'login_attempt') &
    (logs['status'] == 'failed') &
    (logs['@timestamp'].dtMinute == logs['@timestamp'].shift(1).dtMinute)
]
print(unusual_access)
```

---

## **Implementation Best Practices**

### **1. Performance Considerations**
- **Batch Processing**: Aggregate logs before storage (e.g., 1-second intervals).
- **Sampling**: Reduce verbosity for non-critical events (e.g., non-sensitive `GET` requests).
- **Indexing**: Use time-series databases (e.g., InfluxDB) or full-text search (Elasticsearch) for fast queries.

### **2. Security**
- **Encryption**: Encrypt sensitive fields (e.g., passwords) in transit (`TLS`) and at rest (`AES-256`).
- **Anonymization**: Mask PII unless compliance requires retention (e.g., GDPR).
- **Integrity Checks**: Use cryptographic hashes (e.g., HMAC) to detect tampering.

### **3. Scalability**
- **Sharding**: Distribute logs by `resource_type` or `@timestamp` ranges.
- **Hot/Warm Storage**: Move older logs to cheaper archival storage (e.g., S3 Glacier).
- **Stream Processing**: Use Kafka or Pulsar for real-time analysis.

---

## **Related Patterns**

| Pattern                  | Description                                                                                     | When to Use                                  |
|--------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Event Sourcing**       | Store state changes as an immutable event log.                                                 | When full auditability is critical (e.g., financial systems). |
| **Centralized Logging**  | Aggregate logs from all services into a single system (e.g., ELK Stack).                       | For unified observability and debugging.     |
| **Immutable Infrastructure** | Treat infrastructure as code with version control (e.g., Terraform).              | Cloud environments with frequent deployments. |
| **SIEM Integration**     | Feed audit logs into a Security Information and Event Management system (e.g., Splunk).      | For threat detection and incident response.   |
| **Change Data Capture (CDC)** | Capture DB changes in real-time (e.g., Debezium).                                          | Sync audit logs with external systems.        |
| **Policy as Code**       | Enforce audit policies via tools like Open Policy Agent (OPA).                                | For automated compliance checks.             |

---

## **Troubleshooting**
| Issue                     | Cause                          | Solution                                                                 |
|---------------------------|--------------------------------|-------------------------------------------------------------------------|
| **High Storage Costs**    | Unfiltered logs accumulate.     | Implement retention policies + sampling.                                 |
| **Slow Queries**          | Missing indexes or complex joins. | Optimize schema (e.g., denormalize `actor` data).                       |
| **Data Loss**             | Pipeline failures.             | Use dead-letter queues (e.g., Kafka DLQ) + manual reprocessing.          |
| **False Positives**       | Noisy alerts in SIEM.          | Adjust query thresholds or add context (e.g., `metadata.correlation_id`). |
| **Compliance Gaps**       | Missing required fields.       | Validate logs against frameworks (e.g., GDPR checklist).                  |

---
**See Also:**
- [NIST SP 800-92](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistsp800-92.pdf) (Guide to Computer Security Log Management)
- [OpenSearch Audit Log Standard](https://opensearch.org/blog/2022/05/03/opensearch-audit-log-standard/)
- [AWS Config](https://aws.amazon.com/config/) (Pre-built audit solution for AWS).