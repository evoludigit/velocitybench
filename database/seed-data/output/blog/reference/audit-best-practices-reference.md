# **[Pattern] Audit Best Practices Reference Guide**

---

## **Overview**
The **Audit Best Practices** pattern ensures comprehensive, consistent, and actionable tracking of system changes, user activity, and compliance-related events. This pattern helps organizations maintain **data integrity, regulatory compliance (e.g., GDPR, HIPAA, SOC 2), forensic investigations, and operational transparency**. By standardizing audit trails, this pattern minimizes blind spots in accountability, reduces risk of fraud or misconfiguration, and supports automated remediation where applicable.

Key pillars of the pattern include:
- **Comprehensive Scope**: Capturing all relevant events (e.g., CRUD operations, policy violations, API calls).
- **Immutability**: Ensuring audit logs cannot be tampered with (e.g., via write-once storage or cryptographic signing).
- **Structured Data**: Using machine-readable formats (e.g., JSON, NoSQL) for querying and analysis.
- **Retention & Access Control**: Governing retention policies and least-privilege access to logs.
- **Integration**: Connecting audits with SIEM tools (e.g., Splunk, Datadog) or compliance frameworks (e.g., Open Policy Agent).

---

## **Schema Reference**
Below is a standardized schema for audit records. Adopt this or a compatible format (e.g., [OWASP Audit Log Standard](https://owasp.org/www-project-audit-log-standard/)):

| **Field**               | **Type**       | **Description**                                                                                     | **Examples**                                                                 |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `event_id`              | String (UUID)  | Unique identifier for the audit event.                                                               | `"a1b2c3d4-e5f6-7890-1234-567890abcdef"`                                  |
| `timestamp`             | ISO 8601       | When the event occurred (precise to milliseconds).                                                 | `"2024-05-20T10:30:45.123Z"`                                             |
| `event_type`            | String         | Category of event (e.g., `authentication`, `data_modification`, `policy_violation`).              | `"user_login"`, `"api_call"`                                              |
| `action`                | String         | Specific action performed (e.g., `create`, `delete`, `update`).                                    | `"delete_user"`, `"grant_permission"`                                     |
| `resource_id`           | String         | Unique identifier of the affected resource.                                                        | User ID: `"usr-123"`, Table Name: `"users"`                               |
| `resource_type`         | String         | Type of resource (e.g., `user`, `database_record`, `file`).                                       | `"database_record"`, `"config_file"`                                      |
| `user_id`               | String         | Identifier of the authenticated user (or `system` for automated events).                            | `"usr-456"`, `"system"`                                                   |
| `user_agent`            | String         | Client information (IP, device, OS, browser).                                                    | `"192.168.1.100; Chrome/120.0; Ubuntu"`                                  |
| `metadata`              | Object (JSON)  | Free-form key-value pairs for context (e.g., `user_role`, `location`).                             | `{ "user_role": "admin", "location": "NY" }`                             |
| `outcome`               | String         | Result of the event (`success`, `failure`, `pending`).                                            | `"success"`, `"failure"`                                                   |
| `error_code`            | String (optional) | Error details if applicable (e.g., `403_forbidden`, `DB_CONNECTION_TIMEOUT`).                     | `"403_forbidden"`                                                        |
| `source_system`         | String         | Origin of the event (e.g., `auth_service`, `api_gateway`, `custom_app`).                          | `"auth_service"`, `"third-party_api"`                                     |
| `signature`             | String (optional) | Cryptographic hash (e.g., HMAC) to verify log integrity.                                         | `"SHA256:abc123..."`                                                     |

---

## **Implementation Details**
### **1. Core Requirements**
| Requirement               | Implementation Notes                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------|
| **Scope**                 | Log **all** critical events (e.g., authentication, RBAC changes, data exports). Exclude trivial logs (e.g., HTTP 200). |
| **Immutability**          | Store logs in append-only storage (e.g., S3, cloud audit logs) with read-only access for analysts.      |
| **Retention**             | Follow regulatory requirements (e.g., 7 years for GDPR). Use automated purging for older logs.          |
| **Access Control**        | Enforce least privilege: Only auditors/forensics teams access raw logs; dashboards provide aggregated views. |
| **Timestamp Accuracy**    | Use server-side timestamps (not client-side) with <1s latency.                                          |
| **Structured Data**       | Avoid unstructured logs (e.g., plaintext). Use JSON or columnar formats (e.g., Parquet) for queries.     |

### **2. Event Categories**
| Category                  | Examples                                                                 | Tools/Integrations                          |
|---------------------------|---------------------------------------------------------------------------|---------------------------------------------|
| **Authentication**        | Login attempts, password changes, MFA events.                             | Okta, Auth0, cloud IAM logs                  |
| **Authorization**         | RBAC role assignments, permission changes.                                | Open Policy Agent, AWS IAM                  |
| **Data Access**           | Query execution, data exports, row-level changes.                         | Database audit plugins (e.g., PostgreSQL)   |
| **Configuration**         | API key rotations, infrastructure changes (e.g., Kubernetes pods).        | Terraform audit logs, Ansible callbacks     |
| **Policy Violations**     | Failed compliance checks (e.g., DLP triggers, anomaly detection).         | Prisma Cloud, Datadog                       |
| **System Events**         | Server restarts, backup completions, hardware failures.                   | Cloud provider logs (AWS CloudTrail)        |

### **3. Tools & Technologies**
| Component          | Recommended Tools                                                                 |
|--------------------|-----------------------------------------------------------------------------------|
| **Log Collection** | Fluentd, Logstash, AWS CloudWatch Logs, Datadog Infrastructure Monitoring.         |
| **Storage**        | S3 (immutable object storage), InfluxDB (time-series), or purpose-built (e.g., ELK). |
| **Querying**       | Elasticsearch/Kibana, Greylog, or SQL-based (e.g., PostgreSQL audit extensions).  |
| **Analysis**       | SIEMs (Splunk, IBM QRadar), open-source (Graylog, Wazuh).                        |
| **Immutability**   | Blockchain-based logs (e.g., Chainlink), WORM (Write Once, Read Many) drives.     |

---
## **Query Examples**
### **1. Find Failed Login Attempts (Last 24 Hours)**
```sql
-- Elasticsearch Query
GET /audit_logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event_type": "authentication" } },
        { "term": { "outcome": "failure" } },
        { "range": { "timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "failed_users": { "terms": { "field": "user_id" } }
  }
}
```

### **2. Identify Unauthorized API Calls**
```python
# Python (using PyMongo)
from datetime import datetime, timedelta
from pymongo import MongoClient

db = MongoClient("mongodb://localhost:27017").audit_logs
query = {
    "event_type": "api_call",
    "source_system": "third-party_api",
    "timestamp": {"$gte": datetime.now() - timedelta(days=7)},
    "user_id": {"$ne": "system"}  # Exclude automated events
}
results = db.logs.find(query).sort("timestamp", -1)
for log in results:
    print(f"User {log['user_id']} called {log['metadata']['api_endpoint']}")
```

### **3. Detect Data Modifications by High-Risk Users**
```bash
# ELK Stack (Kibana Discover)
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event_type": "data_modification" } },
        { "term": { "user_id": "admin_123" } },
        { "term": { "resource_type": "PII" } }
      ]
    }
  }
}
```

### **4. Compliance Gap Analysis (GDPR)**
```sql
-- Check for unsanctioned data exports
SELECT COUNT(*)
FROM audit_logs
WHERE event_type = 'data_export'
  AND metadata->>'purpose' NOT IN ('legitimate_business', 'user_request')
  AND timestamp > '2024-01-01';
```

---
## **Error Handling & Remediation**
| Scenario                     | Mitigation Strategy                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------------|
| **Log Corruption**           | Use checksums (e.g., MD5) or cryptographic signatures in logs. Replay from backups if needed.         |
| **Performance Overhead**     | Sample logs (e.g., 1% of events) or use async writers (e.g., Kafka buffers).                          |
| **False Positives**          | Define thresholds (e.g., "flag events with >3 failed login attempts in 5 mins").                      |
| **Missing Events**           | Implement health checks for log producers (e.g., Prometheus alerts).                                  |
| **Compliance Violations**    | Automate alerts via SIEM (e.g., Splunk SOAR) for policy breaches.                                     |

---

## **Related Patterns**
| Pattern                     | Description                                                                                          | Integration Points                                                                 |
|-----------------------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **[Open Policy Agent (OPA)**](https://www.openpolicyagent.org/) | Enforce policies as code (e.g., RBAC).                                                       | Audit events triggered by policy violations.                                      |
| **[Distributed Tracing]**   | Correlate audit logs with application traces (e.g., Jaeger) to debug issues.                     | Link `event_id` in audit logs to trace IDs (e.g., `trace_id: 1a2b3c...`).          |
| **[Secrecy Management]**     | Rotate credentials/keys.                                                                         | Audit `credential_rotation` events for compliance.                                  |
| **[Observability Stack]**    | Metrics + logs + traces for root-cause analysis.                                                   | Use audit logs to surface anomalies (e.g., "unusual export times").                 |
| **[Chaos Engineering]**      | Test audit resilience (e.g., simulate log corruption).                                             | Validate recovery procedures for immutable logs.                                   |

---

## **Checklist for Adoption**
1. **Inventory** critical systems/applications generating audit events.
2. **Standardize** schema (use the provided template or OWASP standard).
3. **Toolchain** select log collectors/storage/query tools.
4. **Access Controls** implement RBAC for audit data (e.g., read-only for analysts).
5. **Test** query examples (e.g., failed logins, policy violations).
6. **Automate** alerts for compliance gaps (e.g., GDPR retention).
7. **Document** retention/destruction procedures (e.g., "purge logs >7 years old").
8. **Train** teams on log analysis (e.g., SIEM dashboards).