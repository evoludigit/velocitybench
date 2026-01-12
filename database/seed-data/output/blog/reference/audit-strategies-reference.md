# **[Pattern] Audit Strategies Reference Guide**

---
### **Overview**
Audit Strategies define a structured approach to logging system changes, user actions, or operational events to ensure traceability, compliance, and debugging capabilities. This pattern provides **five core strategies**—**Full Audit, Change Delta, Event-Based Audit, Aggregated Audit, and Sampling Audit**—to capture varying levels of detail while optimizing performance and storage. Implementers can select or combine strategies based on business requirements, resource constraints, and risk exposure.

The **Audit Strategies** pattern aims to:
- Improve compliance with regulations (e.g., **GDPR, HIPAA, PCI-DSS**).
- Enable forensic analysis by preserving detailed activity logs.
- Reduce storage overhead via selective or aggregated recording.
- Support real-time monitoring and anomaly detection.

---
### **Key Concepts**

| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Audit Record**       | A structured log entry capturing metadata (timestamp, user, action type).    |
| **Delta Changes**      | Only records differences (e.g., `fieldA: oldValue → newValue`) rather than full snapshots. |
| **Event-Based**        | Triggers audit logging in response to specific events (e.g., login failures, policy violations). |
| **Aggregation Window** | Time period (e.g., hourly/daily) during which events are grouped for summary records. |
| **Sampling Rate**      | Percentage/frequency (e.g., 10% of operations) to balance granularity and storage. |

---
### **Schema Reference**
All audit records conform to this **standard schema** (adaptable per use case):

| **Field**              | **Type**       | **Description**                                                                 | **Required?** |
|------------------------|----------------|-------------------------------------------------------------------------------|
| `auditId`              | `UUID`         | Unique identifier for the audit entry.                                       |
| `timestamp`            | `ISO 8601`     | When the action occurred (microsecond precision).                           |
| `userId`               | `String`       | Identifier of the user/entity performing the action.                        |
| `actionType`           | `Enum`         | Predefined action (e.g., `CREATE_USER`, `DELETE_RECORD`, `CHANGE_PASSWORD`). |
| `resourceId`           | `String`       | Identifier of the affected record/resource.                                  |
| `oldValue`/`newValue`  | `JSON`         | For **Delta Changes**: Field values before/after the modification. (Optional for others). |
| `context`              | `Map<String, Object>` | Additional metadata (e.g., `{"ipAddress": "192.168.0.1", "location": "EU"}`). |
| `strategy`             | `String`       | Audit strategy applied (e.g., `"FULL_AUDIT"`, `"AGGREGATED_HOURLY"`).       |

---
### **Implementation Strategies**
Choose a strategy based on your needs:

| **Strategy**           | **Use Case**                                                                 | **Trade-offs**                                                                 |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **1. Full Audit**      | Critical systems (e.g., financial transactions) where **no data loss** is acceptable. | High storage/processing overhead; may slow performance.                      |
| **2. Change Delta**    | Databases or configurations where **only modifications** matter.              | Reduces record size but requires schema awareness.                           |
| **3. Event-Based**     | High-risk actions (e.g., `PASSWORD_RESET`, `ADMIN_PRIVILEGE_CHANGE`).       | Low overhead until triggers fire; may miss "normal" events.                   |
| **4. Aggregated Audit**| Monitoring dashboards needing **summary insights** (e.g., daily API failures). | Loses granularity for individual events.                                      |
| **5. Sampling Audit**  | Large-scale systems where **statistical trends** are sufficient.               | Risk of missing critical events; configurable sampling rate.                 |

---
### **Query Examples**
Retrieve audit data using the following patterns:

#### **1. Filter by User and Resource (Full Audit)**
```sql
SELECT *
FROM audit_logs
WHERE userId = 'user123'
  AND resourceId LIKE 'user_profile/%'
  AND strategy = 'FULL_AUDIT'
ORDER BY timestamp DESC
LIMIT 100;
```

#### **2. Find Delta Changes for a Database Field**
```sql
SELECT resourceId, fieldName,
       oldValue AS "Before", newValue AS "After"
FROM delta_changes
WHERE schemaName = 'inventory'
  AND fieldName = 'stockQuantity'
ORDER BY timestamp;
```

#### **3. Aggregate Failed Login Events**
```sql
SELECT
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) AS attempts,
    COUNT(DISTINCT userId) AS unique_users
FROM audit_logs
WHERE actionType = 'LOGIN_FAILURE'
  AND strategy = 'EVENT_BASED'
GROUP BY 1
ORDER BY 1;
```

#### **4. Check for Privilege Escalations**
```sql
SELECT u.userId, a.actionType, a.timestamp
FROM audit_logs a
JOIN users u ON a.userId = u.id
WHERE a.actionType IN ('GRANT_ROLE', 'CHANGE_PASSWORD')
  AND u.role = 'ADMIN'
ORDER BY a.timestamp DESC;
```

---
### **Performance Considerations**
- **Indexing**: Add indexes on `userId`, `resourceId`, `timestamp`, and `actionType` for fast queries.
- **Partitioning**: Partition log tables by date (e.g., `audit_logs_2023_10`) to reduce I/O.
- **Retention Policies**: Use **TTL (Time-To-Live)** or periodic cleanup (e.g., delete data older than 90 days).

---
### **Related Patterns**
| **Pattern**            | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **[Immutable Logs](https://docs.example.com/patterns/immutable-logs)** | Ensures logs cannot be altered post-writing; critical for forensics.       |
| **[Audit Trail Generation](https://docs.example.com/patterns/audit-trail)** | Automates audit log creation from system events (e.g., via middleware).   |
| **[Audit Compliance Dashboard](https://docs.example.com/patterns/dashboard)** | Visualizes audit data for regulatory reporting (e.g., GDPR impact analysis). |
| **[Event Sourcing](https://docs.example.com/patterns/event-sourcing)** | Stores state changes as a sequence of immutable events; can complement audit strategies. |

---
### **Example Implementation (Pseudocode)**
```python
class AuditLogger:
    def __init__(self, strategy: str):
        self.strategy = strategy
        self.storage = ... # Database/Storage backend

    def log(self, action: dict):
        record = {
            "auditId": uuid4(),
            "timestamp": datetime.utcnow(),
            "strategy": self.strategy,
            **action  # Merge action metadata (userId, resourceId, etc.)
        }

        # Apply strategy-specific logic
        if self.strategy == "DELTA":
            record["oldValue"] = get_previous_value(action["resourceId"])
        elif self.strategy == "AGGREGATED":
            record["summary"] = aggregate_event(action)  # e.g., "Failed 3x in 5 mins"

        self.storage.insert(record)
```

---
### **Best Practices**
1. **Classify Data Sensitivity**: Prioritize high-risk actions (e.g., `DELETE_RECORD`) for full auditing.
2. **Use Metadata**: Include `ipAddress`, `userAgent`, and `location` to enrich investigations.
3. **Standardize Naming**: Define a schema for `actionType` (e.g., `CREATE_USER_1234` instead of ad-hoc strings).
4. **Test Recovery**: Verify you can reconstruct system state from audit logs (e.g., restore deleted records).
5. **Monitor Log Volume**: Set alerts for unexpected spikes (e.g., sudden 10x increase in `FULL_AUDIT` records).