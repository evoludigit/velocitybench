# **[Pattern] Audit Monitoring – Reference Guide**

---
## **1. Overview**
**Audit Monitoring** is a defensive design pattern that captures, records, and tracks system activity, user actions, and critical events to maintain security, compliance, and accountability. It ensures observability of changes, helps detect anomalies, and provides forensic evidence in case of breaches.

**Key Use Cases:**
- **Compliance:** Meet regulatory requirements (e.g., GDPR, HIPAA, PCI-DSS).
- **Security:** Detect unauthorized access, data tampering, or policy violations.
- **Forensics:** Reconstruct events for root-cause analysis.
- **Operational Insights:** Monitor system changes for debugging and auditing.

---
## **2. Key Concepts**
| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Audit Logs**            | Structured records of events (e.g., user logins, file modifications).                              |
| **Audit Trail**           | Sequential chain of logs showing causality between events.                                            |
| **Audit Policy**          | Rules defining what actions/operations must be logged.                                              |
| **Audit Filtering**       | Parameters (e.g., severity, user role) to prioritize logged events.                                  |
| **Immutable Storage**     | Logs stored in a write-once-read-many (WORM) format to prevent tampering.                             |
| **Retention Policy**      | Duration logs are stored before deletion (e.g., 90 days for compliance, 30 days for debugging).      |
| **Event Correlation**     | Linking related logs (e.g., failed login followed by unauthorized access attempt).                  |

---
## **3. Schema Reference**
### **Core Audit Log Structure**
| **Field**          | **Type**       | **Description**                                                                                     | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------------------------|
| `event_id`         | String (UUID)  | Unique identifier for the log entry.                                                               | `"a1b2c3d4-e5f6-7890-g1h2-i3j4k5"` |
| `timestamp`        | ISO 8601       | When the event occurred (UTC).                                                                      | `"2024-05-20T14:30:45Z"`       |
| `event_type`       | Enum           | Type of event (e.g., `LOGIN_SUCCESS`, `DATA_MODIFIED`, `ACCESS_DENIED`).                          | `"DATA_MODIFIED"`                |
| `subject`          | Object         | Actor (user/system) triggering the event.                                                          | `{"type": "user", "id": "u123"}` |
| `object`           | Object         | Target of the event (e.g., file, database record).                                                 | `{"type": "file", "name": "report.pdf"}` |
| `action`           | String         | Specific operation performed (e.g., `READ`, `UPDATE`, `DELETE`).                                   | `"UPDATE"`                      |
| `result`           | String         | Success/failure status (e.g., `SUCCESS`, `FAILED_PERMISSION`).                                      | `"SUCCESS"`                     |
| `metadata`         | Object         | Additional context (e.g., IP address, payload changes).                                           | `{"ip": "192.168.1.1", "old_value": "old_data"}` |
| `correlation_id`   | String (UUID)  | Links related events in a session/transaction.                                                    | `"54b3d2c1-f6e7-90a1-b2c3-d4e5f6"` |

---
### **Example Schema (JSON)**
```json
{
  "event_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5",
  "timestamp": "2024-05-20T14:30:45Z",
  "event_type": "DATA_MODIFIED",
  "subject": {
    "type": "user",
    "id": "u123",
    "name": "Alice Smith"
  },
  "object": {
    "type": "database_record",
    "id": "r789",
    "table": "customers"
  },
  "action": "UPDATE",
  "result": "SUCCESS",
  "metadata": {
    "ip": "192.168.1.1",
    "old_value": "{\"name\": \"J Doe\"}",
    "new_value": "{\"name\": \"Alice Smith\"}"
  }
}
```

---
## **4. Implementation Details**
### **4.1. Log Collection**
- **Sources:** Application logs, API calls, database transactions, file system changes.
- **Methods:**
  - **Synchronized Logging:** Embed audit logs in application code (e.g., middleware interceptors).
  - **Agent-Based:** Deploy lightweight agents (e.g., Filebeat, Datadog Agents) to capture OS/application events.
  - **Database Triggers:** Log changes via `AFTER` triggers (e.g., PostgreSQL `LOG`).

### **4.2. Storage Design**
| **Storage Type** | **Use Case**                          | **Example Tools**               |
|------------------|---------------------------------------|----------------------------------|
| **Centralized Logs** | Aggregated logs for analysis.       | ELK Stack (Elasticsearch, Logstash, Kibana), Splunk |
| **Immutable DB**   | Tamper-proof logs (e.g., blockchains). | Amazon Quantum Ledger Database (QLDB), HashiCorp Vault Audit Logs |
| **Local Retention** | Short-term storage for debugging.    | Rotating log files (e.g., `syslog`, `journalctl`) |

### **4.3. Filtering & Retention**
- **Filters:** Use `event_type`, `severity`, or custom tags to reduce noise.
  ```sql
  -- Example filter (Pseudocode):
  SELECT * FROM audit_logs
  WHERE event_type = 'ACCESS_DENIED' AND timestamp > '2024-05-20T00:00:00Z';
  ```
- **Retention:** Enforce policies via tooling (e.g., AWS S3 lifecycle rules, log rotation in `rsyslog`).

### **4.4. Alerting & Response**
- **Thresholds:** Trigger alerts for:
  - Failed logins (`event_type = 'LOGIN_FAILED'`).
  - Unusual activity (e.g., `action = 'DELETE'` during off-hours).
- **Tools:**
  - SIEM (Security Information and Event Management): Splunk, IBM QRadar.
  - Alerting Engines: Prometheus + Alertmanager, Datadog.

---
## **5. Query Examples**
### **5.1. Finding Failed Logins by User**
```sql
SELECT subject.id, subject.name, timestamp
FROM audit_logs
WHERE event_type = 'LOGIN_FAILED'
  AND subject.type = 'user'
  AND timestamp BETWEEN '2024-05-15' AND '2024-05-20'
ORDER BY timestamp DESC;
```

### **5.2. Correlating Related Events (e.g., Session Hijacking)**
```sql
WITH failed_logins AS (
  SELECT event_id
  FROM audit_logs
  WHERE event_type = 'LOGIN_FAILED'
    AND timestamp > NOW() - INTERVAL '5 minutes'
)
SELECT l1.*
FROM audit_logs l1
JOIN failed_logins fl ON l1.correlation_id = fl.correlation_id
WHERE l1.event_type = 'AUTHORIZED_ACCESS';  -- Subsequent success after failure
```

### **5.3. Detecting Unauthorized Data Modifications**
```sql
SELECT subject.name, object.table, object.id, action, metadata.new_value
FROM audit_logs
WHERE event_type = 'DATA_MODIFIED'
  AND subject.role != 'admin'
  AND metadata.old_value != metadata.new_value;  -- Non-trivial changes
```

### **5.4. Exporting Logs for Compliance**
```bash
# Example: Export Splunk logs to CSV (pseudocode)
splunk search "index=audit_logs event_type=DATA_MODIFIED"
| export csv /compliance/audit_exports/2024-05-data_changes.csv
```

---
## **6. Best Practices**
1. **Minimize Privileges:** Ensure audit logs cannot be altered by applications.
2. **Standardize Formats:** Use structured logging (e.g., JSON) for parsing.
3. **Encrypt Logs:** In transit (TLS) and at rest (e.g., KMS encryption).
4. **Test Audit Paths:** Verify logs are captured during critical events (DR drills).
5. **Review Regularly:** Schedule audits of audit logs (e.g., quarterly compliance checks).

---
## **7. Common Pitfalls**
| **Pitfall**                          | **Mitigation**                                                                                     |
|---------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Log Overload**                     | Implement tiered retention (e.g., 7 days raw, 90 days summarized).                                  |
| **Tampering Risk**                    | Use WORM storage or digital signatures (e.g., HMAC).                                               |
| **Incomplete Coverage**               | Audit critical paths only (e.g., payment processing, admin actions).                               |
| **Performance Overhead**             | Batch log writes or use async queues (e.g., Kafka, AWS Kinesis).                                    |
| **False Positives**                   | Fine-tune filters and alert thresholds with historical data.                                       |

---
## **8. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use Together**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **[Defense in Depth]**    | Layered security controls to mitigate single points of failure.                                    | Combine with Audit Monitoring for multi-layered defense. |
| **[Least Privilege]**     | Restrict permissions to minimize damage from breaches.                                            | Critical for narrowing audit scope.               |
| **[Secrets Management]**  | Securely store credentials to reduce risk of exposure in logs.                                    | Ensure sensitive data (e.g., tokens) aren’t logged. |
| **[Incident Response]**   | Structured playbooks for handling breaches.                                                      | Audit logs feed into post-incident analysis.       |
| **[Observability]**       | Monitor system health via metrics/logs/tracing.                                                    | Correlate business metrics with audit events.     |

---
## **9. Tools & Libraries**
| **Category**               | **Tools/Libraries**                                                                              |
|-----------------------------|--------------------------------------------------------------------------------------------------|
| **Log Collection**         | Fluentd, Filebeat, AWS CloudTrail, Datadog                                                                 |
| **Storage**                | ELK Stack, Splunk, Amazon QLDB, Google Cloud Audit Logs                                        |
| **Analysis**               | Grafana, Kibana, Prisma Cloud (for IaaC audits)                                                 |
| **Language SDKs**          | Python: `requests` hooks, Java: `SLF4J`, Go: `zap` with audit middleware                          |

---
## **10. Further Reading**
- **Standards:**
  - [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) (Audit Requirements).
  - [ISO 27001](https://www.iso.org/isoiec-27001-information-security.html) (Compliance Framework).
- **Papers:**
  - ["Designing Secure Systems" by Google](https://google.github.io/engineering-guide/releng/security/) (Audit section).
  - ["The Art of Invisibility" by Kevin Mitnick](https://www.amazon.com/Art-Invisibility-Principles-Hiding-Digital/dp/0735219569) (Threat modeling).