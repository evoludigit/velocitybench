**[Pattern] Audit Tuning – Reference Guide**

---

### **Overview**
The **Audit Tuning** pattern optimizes audit logging to balance security, performance, and cost efficiency. It involves configuring audit policies, filtering irrelevant events, optimizing data retention, and leveraging sampling or aggregation to reduce noise while maintaining critical insights. This pattern is critical for environments where audit logs are essential for compliance, incident response, and security monitoring but where raw log volume could overwhelm systems or increase storage costs.

Audit tuning refines logging strategies by:
- **Reducing verbosity** (e.g., ignoring low-risk operations).
- **Selectively capturing sensitive data** (e.g., masking PII) or high-impact events (e.g., privilege escalations).
- **Implementing retention policies** to purge old logs efficiently.
- **Using sampling** for high-frequency events (e.g., API calls) or **aggregation** for near-duplicate patterns.
- **Optimizing query performance** in audit databases (e.g., indexing critical fields).

This guide covers key concepts, schema references, implementation best practices, and query examples to help enforce audit tuning effectively.

---

### **Key Concepts & Implementation Details**
#### **1. Audit Log Granularity**
Define the scope of logged events:
- **Critical events**: Authentication failures, privilege changes, or data exfiltration attempts.
- **Informational events**: Regular user logins or non-sensitive configuration changes.
- **Irrelevant events**: Debug-level logs or repeated low-risk actions (e.g., file reads by non-privileged users).

#### **2. Filtering & Sampling**
- **Static filtering**: Exclude known benign events (e.g., SSH key updates) via log rules.
  ```json
  exclude_events: [
      "USER_LOGIN_SUCCESSFUL",
      "FILE_READ_ACCESS"
  ]
  ```
- **Dynamic filtering**: Use runtime conditions (e.g., IP reputation, user role) to suppress logs.
- **Sampling**: Log a subset of high-frequency events (e.g., 1% of API calls) to reduce volume.
  ```yaml
  sampling_rate: 0.01  # Log 1 event per 100 for "USER_API_CALL"
  ```

#### **3. Data Retention Policies**
- **Time-based**: Retain logs for 30–90 days (default for compliance) or longer for investigations.
- **Event-based**: Delete logs after correlated incidents are resolved (e.g., post-breach).
- **Tiered storage**: Archive older logs to cold storage (e.g., S3 Glacier) with slower access.

#### **4. Data Masking & Anonymization**
- Replace PII (e.g., usernames, IPs) with tokens or hashes during ingestion or query time.
  ```sql
  SELECT tokenize(user_email) AS masked_email, event_from_ip AS ip_hash,
         event_timestamp FROM audit_logs;
  ```
- Use field-level encryption for sensitive data (e.g., passwords in auth logs).

#### **5. Query Optimization**
- **Index critical fields**: `event_type`, `user_id`, `resource_id`, `event_timestamp`.
- **Partition tables**: By date or event type to speed up range queries.
- **Materialized views**: Pre-aggregate common queries (e.g., "failed logins by hour").

#### **6. Storage & Cost Management**
- **Compress logs**: Use formats like Parquet or GZIP for storage efficiency.
- **Tiered replication**: Keep hot logs in fast storage (e.g., SSD) and cold logs in cheaper media.
- **Auto-scaling**: Adjust log ingestion capacity based on traffic spikes.

---

### **Schema Reference**
| Field               | Type         | Description                                                                 | Example Values                          | Notes                                  |
|---------------------|--------------|-----------------------------------------------------------------------------|-----------------------------------------|----------------------------------------|
| `event_id`          | UUID         | Unique identifier for the event.                                            | `550e8400-e29b-41d4-a716-446655440000` | Primary key.                           |
| `event_timestamp`   | TIMESTAMP    | When the event occurred (ISO 8601).                                         | `2023-10-15T14:30:00Z`                | Indexed for time-range queries.        |
| `event_type`        | VARCHAR(50)  | Categorization of the event (e.g., `AUTHENTICATION_FAILURE`).                | `FILE_MODIFICATION`, `API_CALL`        | Use for filtering.                     |
| `user_id`           | VARCHAR(64)  | Identifier of the user/process.                                              | `uid12345`                             | Masked in public queries.              |
| `resource_id`       | VARCHAR(128) | Target of the event (e.g., file path, API endpoint).                       | `/home/user/secret.pem`                | Indexed for resource-specific queries. |
| `action`            | VARCHAR(30)  | Specific operation performed (e.g., `CREATE`, `DELETE`).                   | `REVOKE_PERMISSION`                    | Part of `event_type` classification.   |
| `status`            | VARCHAR(20)  | Success/failure outcome.                                                     | `SUCCESS`, `FAILED`                    | Filter by `status = FAILED`.            |
| `severity`          | ENUM          | Priority level (CRITICAL, HIGH, MEDIUM, LOW).                               | `HIGH`                                 | Used for alerting.                     |
| `sensitive_data`    | JSONB         | Structured sensitive data (masked).                                         | `{"ip": "192.168.1.1", "token": "..."}`| Encrypted at rest.                     |
| `source_ip`         | VARCHAR(15)  | Originating IP address.                                                      | `10.0.0.5`                             | May be anonymized.                     |
| `metadata`          | JSONB         | Additional context (e.g., `{"user_agent": "curl/7.81.0"}`).                   |                                         | Flexible for future fields.            |

**Example Table Definition (PostgreSQL):**
```sql
CREATE TABLE audit_logs (
    event_id UUID PRIMARY KEY,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(64),
    resource_id VARCHAR(128),
    action VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    severity ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW') NOT NULL,
    sensitive_data JSONB,
    source_ip VARCHAR(15),
    metadata JSONB,
    INDEX idx_event_type (event_type),
    INDEX idx_user_id (user_id),
    INDEX idx_resource_id (resource_id),
    INDEX idx_timestamp (event_timestamp)
);
```

---

### **Query Examples**
#### **1. Filter Critical Failures by User**
```sql
SELECT user_id, event_timestamp, action, resource_id
FROM audit_logs
WHERE status = 'FAILED' AND severity IN ('CRITICAL', 'HIGH')
  AND user_id LIKE 'uid%'  -- Filter for specific users
ORDER BY event_timestamp DESC
LIMIT 100;
```

#### **2. Aggregate Failed Logins by IP (Anonymized)**
```sql
SELECT
    tokenize(source_ip) AS anonymized_ip,
    COUNT(*) AS failure_count,
    MAX(event_timestamp) AS last_failure
FROM audit_logs
WHERE event_type = 'AUTHENTICATION_FAILURE'
GROUP BY anonymized_ip
HAVING COUNT(*) > 5  -- Flag suspicious IPs
ORDER BY failure_count DESC;
```

#### **3. Find Privilege Escalations**
```sql
SELECT
    user_id,
    event_timestamp,
    action,
    resource_id
FROM audit_logs
WHERE event_type = 'PERMISSION_CHANGE'
  AND action IN ('ADD_ROLE', 'GRANT_ACCESS')
ORDER BY event_timestamp DESC;
```

#### **4. Sample High-Frequency API Calls (1%)**
```sql
-- PostgreSQL: Use a window function to sample
WITH sample_api_calls AS (
    SELECT
        event_id,
        event_timestamp,
        user_id,
        resource_id,
        action,
        ROW_NUMBER() OVER (
            PARTITION BY hash(user_id || resource_id)
            ORDER BY RANDOM()
        ) AS row_num
    FROM audit_logs
    WHERE event_type = 'API_CALL'
)
SELECT event_id, event_timestamp, user_id, resource_id, action
FROM sample_api_calls
WHERE row_num = 1;  -- 1 row per unique user+resource pair
```

#### **5. Retention Policy Enforcement (Delete Old Logs)**
```sql
-- PostgreSQL: Delete logs older than 90 days
DELETE FROM audit_logs
WHERE event_timestamp < NOW() - INTERVAL '90 days';
```

---

### **Related Patterns**
1. **[Centralized Logging]** – Aggregate audit logs from multiple sources (e.g., ELK Stack, Splunk) for unified analysis.
2. **[Log Enrichment]** – Augment audit data with contextual info (e.g., user roles, IP geolocation) via tools like [Serilog](https://serilog.net/).
3. **[Incident Response Workflow]** – Integrate audit logs with SIEM tools (e.g., Splunk, Chronicle) to detect and respond to threats.
4. **[Data Minimization]** – Reduce PII collection in logs to comply with regulations like GDPR.
5. **[Audit Trail Validation]** – Use checksums or digital signatures to verify log integrity post-event.

---
### **Further Reading**
- [NIST SP 800-92](https://csrc.nist.gov/publications/detail/sp/800-92/final) (Guideline for Audit Log Management).
- [CIS Controls v8](https://www.cisecurity.org/cis-controls/) (Audit logging best practices).
- [Elasticsearch Auditbeat](https://www.elastic.co/guide/en/beats/auditbeat/current/auditbeat-reference.html) (Example implementation).