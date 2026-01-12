**[Pattern] Reference Guide: Audit Setup**
*Version: 1.0 | Last Updated: [Insert Date]*

---

### **Overview**
The **Audit Setup** pattern defines a structured approach to recording, accessing, and analyzing system changes, user activity, and operational metadata. It ensures compliance, debugging, and forensic analysis by capturing consistent, machine-readable audit logs for critical operations. This pattern applies to:
- **Service-oriented architectures** (microservices, APIs)
- **Database systems** (CRUD operations, schema changes)
- **User-facing applications** (authentication, role changes)
- **Infrastructure components** (deployments, config updates)

Key principles:
- **Immutability**: Logs must not be modified post-creation.
- **Completeness**: All relevant events (success/failure) are recorded.
- **Auditability**: Logs enable traceability (e.g., "Who deleted X at Y?").
- **Performance**: Minimal overhead on primary systems.

---

### **Schema Reference**
Audit logs adhere to the following **standardized schema**. Fields are categorized by relevance and mutability.

| **Category**       | **Field Name**       | **Data Type**       | **Required** | **Description**                                                                                     | **Example Values**                                                                                     |
|--------------------|----------------------|---------------------|--------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Metadata**       | `event_id`           | UUID                | Yes          | Unique identifier for the log entry (auto-generated).                                               | `550e8400-e29b-41d4-a716-446655440000`                                                                   |
|                    | `timestamp`          | ISO 8601 Timestamp  | Yes          | When the event occurred (system-generated).                                                          | `2023-11-15T14:30:45.123Z`                                                                             |
|                    | `event_type`         | Enum (`CREATE`, `UPDATE`, `DELETE`, `AUTHENTICATE`, `ERROR`) | Yes | Type of audited action.                                                                               | `DELETE`                                                                                                |
|                    | `source_system`      | String              | Yes          | Name of the system/application emitting the log (e.g., `auth-service`, `order-api`).                      | `payment-processor`                                                                                   |
|                    | `version`            | String              | No           | Schema version of the audit log (for backward compatibility).                                         | `v1.2`                                                                                                  |
| **Context**        | `user_id`            | UUID/Username       | Conditional  | Identifier of the user performing the action (omit for system events).                               | `john.doe@company.com`                                                                                 |
|                    | `action_user_ip`     | IPv4/IPv6           | Conditional  | Source IP of the user (if applicable).                                                                | `192.168.1.100`                                                                                         |
|                    | `correlation_id`     | UUID                | No           | Links related events (e.g., atomic transaction steps).                                                | `7d7d15cb-6d4d-40af-9b3c-88a7e6f5e1d2`                                                                   |
| **Details**        | `resource_type`      | Enum (`USER`, `DATA`, `SYSTEM`, `API`) | Yes | Type of resource modified.                                                                           | `DATA`                                                                                                   |
|                    | `resource_id`        | UUID/String         | Yes          | Unique identifier of the resource (e.g., database row ID).                                          | `#user-789`                                                                                           |
|                    | `resource_name`      | String              | Conditional  | Human-readable name of the resource.                                                                  | `customer_profile_12345`                                                                              |
|                    | `old_value`          | JSON/Blob           | Conditional  | Pre-change state (for `UPDATE`/`DELETE`).                                                             | `{"name": "Old Name", "status": "active"}`                                                           |
|                    | `new_value`          | JSON/Blob           | Conditional  | Post-change state (for `CREATE`/`UPDATE`).                                                           | `{"name": "New Name", "status": "inactive"}`                                                         |
|                    | `change_fields`      | Array[String]       | Conditional  | List of modified fields (e.g., `["status", "last_login"]`).                                          | `["status", "expiry_date"]`                                                                         |
| **Outcome**        | `status`             | Enum (`SUCCESS`, `FAILURE`) | Yes | Result of the audited action.                                                                        | `SUCCESS`                                                                                             |
|                    | `error_code`         | String              | Conditional  | Error details (if `status = FAILURE`).                                                               | `ERR-403`                                                                                              |
|                    | `error_message`      | String              | Conditional  | Human-readable error description.                                                                  | `"Insufficient permissions"`                                                                          |
| **Additional**     | `metadata`           | JSON                | No           | Extensible key-value pairs (e.g., `{"region": "us-west-2"}`).                                        | `{"client_app": "mobile_v1", "device": "iPhone"}`                                                     |

---
**Notes:**
- **Conditional fields**: Required only for specific `event_type`s (e.g., `user_id` for `AUTHENTICATE`).
- **JSON Blobs**: Use for complex data (e.g., nested objects). For large payloads, store a hash (`SHA-256`) and reference the full data in a separate "change log" table.
- **Compliance**: Align with standards like **ISO 27001**, **GDPR** (for user-data logs), or **SOC 2**.

---

### **Implementation Details**
#### **1. Log Generation**
**Components:**
- **Client-Side**: Embedded in applications (e.g., SDKs for SDKs in Python/Java).
- **Server-Side**: Middleware interceptors (e.g., API gateways, database triggers).
- **Infrastructure**: Cloud providers (AWS CloudTrail, Azure Monitor) or custom agents.

**Best Practices:**
- **Atomicity**: Log generation must succeed or fail with the primary operation (use transactions).
- **Asynchronous Writes**: Avoid blocking calls (e.g., queue logs to a service like AWS Kinesis).
- **Confidentiality**: Encrypt sensitive fields (e.g., `user_id`, `new_value`) at rest.

**Example Code Snippet (Pseudocode):**
```python
def audit_log(event_type: str, resource_id: str, new_value: dict):
    log_entry = {
        "event_id": uuid.uuid4(),
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "source_system": "order-service",
        "user_id": current_user_id,
        "resource_type": "DATA",
        "resource_id": resource_id,
        "new_value": new_value,
        "status": "SUCCESS"
    }
    async log_to_audit_queue(log_entry)  # Non-blocking
```

#### **2. Storage**
**Options:**
| **Storage Type**       | **Use Case**                                  | **Pros**                                      | **Cons**                                  |
|------------------------|-----------------------------------------------|-----------------------------------------------|-------------------------------------------|
| **Database**           | High-frequency queries (e.g., real-time dashboards) | Fast reads, ACID compliance                | High storage costs                       |
| **Log Aggregator**     | Centralized analysis (e.g., ELK Stack, Splunk) | Scalable, search-friendly                  | Delayed access                           |
| **Immutable Storage**  | Compliance (e.g., WORM - Write Once, Read Many) | Tamper-proof                             | Expensive, slow writes                   |
| **Hybrid**             | Combined (e.g., hot/cold data)                | Balances cost/performance                   | Complex setup                            |

**Recommendation**: Use a **time-series database** (e.g., TimescaleDB) for high-volume logs and **S3-compatible storage** for long-term retention.

#### **3. Enrichment**
Augment logs with:
- **User Context**: Merge with auth systems (e.g., `user_id` → `display_name`).
- **Geolocation**: IP → country (using services like MaxMind).
- **Business Metrics**: Link to KPIs (e.g., `event_type = "ORDER_CANCEL"` → `revenue_impact`).

**Example Query (Enrichment):**
```sql
-- Pseudocode for joining user profiles
SELECT
    a.*,
    u.display_name,
    COALESCE(g.country, 'Unknown') AS user_country
FROM audit_logs a
LEFT JOIN users u ON a.user_id = u.id
LEFT JOIN geolocation g ON a.action_user_ip = g.ip;
```

#### **4. Retention Policies**
| **Retention Level** | **Duration**       | **Purpose**                                  | **Storage Tier**         |
|---------------------|--------------------|---------------------------------------------|--------------------------|
| **Hot**             | 7–30 days          | Debugging, real-time alerts                 | Fast SSD                 |
| **Warm**            | 30–365 days        | Audits, compliance reports                  | HDD or cold storage      |
| **Cold**            | >365 days          | Historical analysis                         | Archival (e.g., S3 Glacier) |

**Automation**: Use **TTL (Time-to-Live)** indexes (e.g., MongoDB) or cloud lifecycle rules.

---

### **Query Examples**
#### **1. Find All Failed Payment Processing Logs**
```sql
-- PostgreSQL example
SELECT
    event_id,
    user_id,
    resource_id,
    error_code,
    error_message,
    timestamp
FROM audit_logs
WHERE event_type = 'PROCESS_PAYMENT'
  AND status = 'FAILURE'
  AND timestamp > '2023-11-01'
ORDER BY timestamp DESC;
```

#### **2. Track User Role Changes**
```sp
-- SQL Server stored procedure
CREATE PROCEDURE sp_get_user_role_changes
    @user_id VARCHAR(100)
AS
BEGIN
    SELECT
        event_id,
        user_id,
        new_value->>'$.role' AS new_role,
        old_value->>'$.role' AS old_role,
        timestamp
    FROM audit_logs
    WHERE user_id = @user_id
      AND resource_type = 'USER'
      AND ('$.role' IN (KEYS(old_value)) OR '$.role' IN (KEYS(new_value)))
    ORDER BY timestamp DESC;
```

#### **3. Aggregate API Usage by Endpoint**
```python
# Example using PySpark (for large-scale logs)
from pyspark.sql import functions as F

df = spark.read.parquet("audit_logs_parquet/")
df.filter(F.col("event_type") == "API_CALL") \
  .groupBy("timestamp", "resource_name") \
  .agg(
      F.count("*").alias("call_count"),
      F.first("user_id").alias("sample_user")
  ) \
  .orderBy("timestamp") \
  .show()
```

#### **4. Detect Anomalies (e.g., Unusual Login Attempts)**
```javascript
// Example using Elasticsearch query DSL
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event_type": "AUTHENTICATE" } },
        { "range": { "timestamp": { "gte": "now-1h/d" } } }
      ],
      "filter": [
        { "exists": { "field": "error_message" } },
        { "terms": { "status": ["FAILURE"] } }
      ]
    }
  },
  "aggs": {
    "failed_logins_by_ip": {
      "terms": { "field": "action_user_ip" },
      "aggs": {
        "count": { "value_count": { "field": "_id" } }
      }
    }
  }
}
```

---

### **Performance Considerations**
| **Optimization**               | **Impact**                          | **Implementation**                                                                 |
|--------------------------------|-------------------------------------|------------------------------------------------------------------------------------|
| **Log Batching**               | Reduces I/O overhead                | Group logs into batches (e.g., every 100ms) before writing.                           |
| **Compression**                | Lowers storage costs                | Use gzip/Snappy for JSON logs (e.g., `aws s3 cp --acl public-read --storage-class STANDARD_IA`). |
| **Sampling**                   | Balances load/granularity           | Log every Nth event (e.g., 1% of requests) for high-volume systems.               |
| **Sharding**                   | Scales horizontally                 | Partition logs by `event_type` or `timestamp` ranges.                              |

---

### **Related Patterns**
| **Pattern Name**               | **Purpose**                                                                 | **Connection to Audit Setup**                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **[Event Sourcing]**           | Store state changes as an immutable sequence of events.                     | Audit logs *are* a form of event sourcing (but typically non-transactional).              |
| **[CQRS]**                     | Separate read/write models for scalability.                                | Audit queries often require a *read-optimized* model.                                      |
| **[Canary Releases]**          | Gradually roll out changes to detect issues.                               | Compare audit logs pre/post-release to identify failures.                                  |
| **[Secrets Management]**       | Securely store and rotate credentials.                                    | Audit `SECRET_ROTATE` events for compliance.                                              |
| **[Data Masking]**             | Protect sensitive data in logs.                                            | Use for `new_value` fields (e.g., mask PII).                                               |
| **[Observability Stack]**      | Combine metrics, logs, and traces.                                           | Audit logs complement metrics (e.g., `latency` + `event_type = "ERROR"`).                 |

---
### **Compliance Checklist**
| **Requirement**               | **Audit Setup Implementation**                                                                 |
|-------------------------------|------------------------------------------------------------------------------------------------|
| **GDPR (Article 30)**         | Retain logs for user data access requests; enable subject access requests via API.               |
| **HIPAA (Audit Logs Rule)**   | Log all access to PHI (Protected Health Information) with timestamps and user IDs.              |
| **PCI DSS (Requirement 10)** | Audit all cardholder data access (e.g., `event_type = "ACCESS_CREDIT_CARD"`).                  |
| **SOC 2 Type II**             | Ensure logs are tamper-proof and retained for 90+ days.                                          |
| **ISO 27001**                 | Classify logs by sensitivity; enforce least-privilege access to audit data.                     |

---
### **Troubleshooting**
| **Issue**                     | **Diagnosis**                                                                 | **Solution**                                                                                     |
|-------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **High Latency in Logs**      | Queue backlog or slow storage writes.                                          | Scale writers (e.g., add Kinesis shards) or compress logs.                                       |
| **Missing Logs**              | Middleware failure or missing SDK integration.                               | Implement health checks for log producers; test with `event_type = "SYSTEM_HEALTHCHECK"`.       |
| **Storage Overruns**          | No retention policy or rapid growth.                                           | Enforce TTL indexes or bucket lifecycle rules.                                                  |
| **False Positives in Alerts** | Noisy event filtering (e.g., `status = FAILURE` includes retries).          | Add `is_retry = false` filter or classify errors by severity.                                   |
| **Compliance Gaps**           | Logs lack critical fields (e.g., `user_id` for `DATA` events).                 | Validate schema compliance via CI/CD (e.g., OpenAPI validation).                                |

---
### **Tools & Libraries**
| **Category**               | **Tools/Libraries**                                                                 | **Notes**                                                                                     |
|----------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Generators**            | AWS CloudTrail, Datadog Synthetics, OpenTelemetry SDKs                           | OpenTelemetry includes built-in audit logging.                                               |
| **Storage**               | Amazon OpenSearch, MongoDB Atlas, InfluxDB                                         | OpenSearch excels at log analytics.                                                          |
| **Analysis**              | Splunk, Graylog, ELK Stack                                                         | ELK is open-source; Splunk offers pre-built dashboards.                                       |
| **Enrichment**            | Datadog Context, Elastic Agent                                                    | Auto-correlate logs with metrics/traces.                                                     |
| **Compliance**            | IBM Audit Compliance Manager, Databricks Governance                                | Databricks integrates with Delta Lake for audit trails.                                        |