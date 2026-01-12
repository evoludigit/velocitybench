# **[Audit Patterns] Reference Guide**

---

## **Overview**
The **Audit Patterns** framework provides a standardized approach to tracking, recording, and analyzing system activity for security, compliance, forensic analysis, and operational transparency. This pattern defines how to capture **who**, **what**, **when**, **where**, and **why** actions occur in a system, facilitating auditability, change tracking, and incident response.

Audit Patterns are modular, allowing granular control over:
- **Audit Scope** (e.g., application-level, infrastructure, or cross-system)
- **Audit Granularity** (e.g., per operation, per API call, or per user session)
- **Audit Storage** (centralized logs, databases, or third-party SIEM tools)
- **Automation & Alerting** (real-time triggers for suspicious activity)

This guide outlines core concepts, schema standards, implementation best practices, and example queries for effectively deploying Audit Patterns.

---

## **Key Concepts & Implementation Details**
### **1. Core Principles**
- **Non-Repudiation**: Audit records must be immutable to prevent tampering.
- **Separation of Concerns**: Audit data should not interfere with application performance.
- **Contextual Richness**: Include metadata like IP addresses, user identities, and correlated events.
- **Scalability**: Design for high-volume logging without bottlenecks.

### **2. Audit Event Lifecycle**
1. **Trigger**: An event occurs (e.g., user login, file modification).
2. **Capture**: System records metadata before/after the event.
3. **Store**: Data is written to a persistent log or database.
4. **Retention**: Data is archived or purged based on compliance policies.
5. **Query/Analyze**: Tools ingest audit data for reporting or alerting.

### **3. Audit Patterns by Use Case**
| **Pattern Name**       | **Purpose**                          | **Example Scenarios**                          |
|------------------------|--------------------------------------|-----------------------------------------------|
| **Operation Audit**    | Track business-critical operations.   | Database queries, CRUD actions, workflow steps. |
| **Authentication Audit** | Monitor user/logon activity.         | Failed logins, session initiation, MFA events. |
| **Configuration Audit** | Detect systemic changes.             | Server updates, policy modifications.         |
| **Compliance Audit**   | Ensure regulatory adherence.         | GDPR access logs, SOX financial transactions.  |
| **Forensic Audit**     | Preserve evidence for investigations.| Failed login attempts, privileged user actions.|

---

## **Schema Reference**
Below is a **standardized JSON schema** for audit events. Customize fields based on your system’s needs.

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|----------------|-------------------------------------------------------------------------------|----------------------------------------|
| `event_id`              | UUID           | Unique identifier for the audit event.                                         | `550e8400-e29b-41d4-a716-446655440000` |
| `timestamp`             | ISO 8601       | When the event occurred (UTC).                                                 | `2023-10-15T14:30:00Z`               |
| `event_type`            | String         | Categorizes the event (e.g., `authentication`, `data_modification`).           | `user_login`                          |
| `user`                  | Object         | User identity and attributes.                                                   | `{ "id": "user123", "name": "Alice" }`|
| `user.ip_address`       | String         | Source IP of the user.                                                         | `192.168.1.100`                       |
| `source_system`         | String         | Originating system/application.                                                 | `app-v1`, `db-server`                 |
| `action`                | String         | Specific operation performed.                                                  | `create_record`, `update_password`    |
| `resource`              | Object         | Affected entity (e.g., database table, file).                                  | `{ "type": "table", "name": "users" }`|
| `outcome`               | Enum           | Success/failure status.                                                         | `success`, `failed`                   |
| `error_code`            | String         | Error details (if applicable).                                                  | `INVALID_CREDENTIALS`                 |
| `metadata`              | Object         | Additional context (e.g., API payload, referrer URL).                          | `{ "query": "SELECT * FROM users" }`   |
| `correlation_id`        | String         | Links related events (e.g., multi-step workflows).                             | `workflow-789`                        |

---

## **Query Examples**
### **1. Basic Filtering (SQL)**
```sql
-- Find all failed authentication attempts in the last 7 days
SELECT *
FROM audit_events
WHERE event_type = 'authentication'
  AND outcome = 'failed'
  AND timestamp >= DATEADD(day, -7, GETDATE())
ORDER BY timestamp DESC;
```

### **2. Aggregating User Activity (PostgreSQL)**
```sql
-- Count login attempts by user
SELECT
    user.id,
    user.name,
    COUNT(*) AS login_attempts,
    SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) AS failed_attempts
FROM audit_events
JOIN users ON audit_events.user_id = users.id
WHERE event_type = 'authentication'
  AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY user.id, user.name;
```

### **3. Correlating Events (Elasticsearch)**
```json
-- Find all events related to a specific record modification
GET /audit_events/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "resource.name": "customer_1001" } },
        { "range": { "timestamp": { "gte": "now-1d/d" } } }
      ]
    }
  }
}
```

### **4. Detecting Privilege Escalation (Python + Pandas)**
```python
# Check for rapid role changes (potential privilege escalation)
import pandas as pd

df = pd.read_json('audit_events.json')
suspicious = df[
    (df['event_type'] == 'authorization') &
    (df['action'] == 'role_assignment') &
    (df['timestamp'].diff().dt.total_seconds() < 60)  # <1 minute apart
]
print(suspicious[['timestamp', 'user.name', 'action', 'resource']])
```

---

## **Implementation Best Practices**
1. **Minimize Overhead**:
   - Avoid logging sensitive data (e.g., PII) unless required.
   - Use **asynchronous logging** to decouple performance impact.

2. **Retention Policies**:
   - Short-term (e.g., 30 days): High-frequency logs (e.g., API calls).
   - Long-term (e.g., 7 years): Critical events (e.g., financial transactions).

3. **Immutable Storage**:
   - Use **WORM (Write Once, Read Many)** storage (e.g., S3 versioning, database triggers).
   - Sign audit logs with **digital certificates** to prevent tampering.

4. **Automation**:
   - Integrate with **SIEM tools** (Splunk, ELK, Datadog) for real-time alerts.
   - Example alert rule:
     ```json
     -- Trigger if >5 failed logins in 5 minutes
     {
       "condition": "count > 5",
       "filter": {
         "event_type": "authentication",
         "outcome": "failed",
         "timestamp": { "$gte": "now-5m" }
       }
     }
     ```

5. **Testing**:
   - Validate audit trails with **chaos engineering** (e.g., simulate failed logins).
   - Verify **data integrity** by cross-referencing with application logs.

---

## **Schema Evolution**
To accommodate changes without breaking existing systems:
- **Versioning**: Add a `schema_version` field to audit events.
  ```json
  {
    "schema_version": "1.2",
    "event_type": "data_modification",
    "new_field": "value"  // Introduced in v1.2
  }
  ```
- **Backward Compatibility**: Avoid removing fields; instead, mark deprecated fields with `is_active: false`.

---

## **Related Patterns**
| **Pattern**               | **Relationship to Audit Patterns**                                                                 | **When to Use**                                  |
|---------------------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[Event Sourcing]**      | Audit Patterns often implement Event Sourcing by persisting raw event streams.                   | Systems requiring a complete history of state changes. |
| **[Immutable Logs]**      | Audit data is a subset of immutable logs.                                                     | High-security environments (e.g., healthcare).   |
| **[Activity Streams]**    | Lightweight alternative for user-facing activity feeds (e.g., "You modified File X at 2 PM").   | Collaborative tools (e.g., Git, Slack).          |
| **[Compliance Frameworks]** (e.g., GDPR, HIPAA) | Audit Patterns map directly to regulatory requirements (e.g., right to erasure tracking).    | Industries with strict legal/audit demands.      |
| **[Distributed Tracing]** | Audit Patterns can correlate across microservices using `correlation_id`.                    | Debugging latency issues in distributed systems. |

---

## **Tools & Libraries**
| **Category**       | **Tools**                                                                 | **Use Case**                          |
|--------------------|--------------------------------------------------------------------------|---------------------------------------|
| **Log Storage**    | ELK Stack, Splunk, AWS CloudTrail, Datadog                                | Centralized log management.           |
| **Database**       | PostgreSQL (TimescaleDB), ClickHouse, MongoDB Atlas                       | High-performance audit databases.     |
| **SDKs**           | AWS SDK (`aws-lambda-audit`), Python `auditbeat`, .NET `AuditLog`         | Server-side audit instrumentation.    |
| **SIEM**           | Wazuh, Graylog, IBM QRadar                                                | Real-time threat detection.           |
| **Forensics**      | Velociraptor, TheHive, OSQuery                                             | Post-breach investigation.            |

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                      |
|-------------------------------------|------------------------------------------------------------------------------|---------------------------------------------------|
| **High CPU/memory usage**           | Synchronous audit logging blocks application threads.                        | Switch to async logging (e.g., Kafka, SQS).       |
| **Missing critical events**         | Audit hooks not deployed in all components.                                 | Audit integration tests; use cross-cutting concerns (e.g., AOP). |
| **Log corruption**                  | Immutable storage misconfigured (e.g., unversioned S3 buckets).              | Enable versioning and enforce write-only policies.|
| **Slow queries**                    | No indexing on frequently queried fields (e.g., `user_id`, `timestamp`).    | Add GIN indexes (PostgreSQL) or dedicated search (Elasticsearch). |

---
## **Further Reading**
1. **Standards**:
   - [ISO 27001:2022](https://www.iso.org/standard/75581.html) (Audit Trail Requirements)
   - [NIST SP 800-92](https://nvlpubs.nist.gov/nistpubs/Legacy/sp/nistspecialpublication/800-92r2.pdf) (Guide to Computer Security Log Management)
2. **Open Source**:
   - [OpenTelemetry Audit Collector](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/audit)
3. **Case Studies**:
   - [How Uber Logs Billions of Events](https://eng.uber.com/audit-logging/)
   - [Netflix’s Distributed Audit Framework](https://netflixtechblog.com/)

---
**Feedback**: Contribute to schema extensions or query templates [here](LINK_TO_GITHUB).