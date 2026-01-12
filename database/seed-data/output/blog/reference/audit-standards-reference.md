# **[Pattern] Audit Standards Reference Guide**

---

## **1. Overview**
The **Audit Standards** pattern ensures systematic tracking, validation, and compliance of records within a system. This pattern defines a standardized way to log, query, and report changes to critical data, ensuring traceability, accountability, and adherence to regulatory requirements (e.g., GDPR, HIPAA, SOX). Implementations typically include:
- **Audit Logs**: Immutable records of all significant actions (create, update, delete).
- **Validation Rules**: Predefined checks to enforce business/regulatory compliance.
- **Access Controls**: Restrictions to prevent unauthorized modifications.
- **Query Mechanisms**: Structured ways to retrieve, analyze, and export audit data.

Use this pattern when:
✔ Your system handles sensitive or high-risk data.
✔ Regulatory compliance is mandatory (e.g., financial, healthcare, or legal industries).
✔ Accountability for user actions is required (e.g., internal investigations, audits).

---

## **2. Key Concepts**

### **2.1 Core Components**
| **Component**       | **Description**                                                                 | **Example**                          |
|---------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Audit Record**    | Immutable log entry containing metadata (e.g., timestamp, user, action).      | `{"id": "AUD-1234", "action": "UPDATE", "user": "admin", "entity": "User#5"}` |
| **Action Types**    | Predefined verbs for standardizing logged operations (e.g., `CREATE`, `DELETE`). | `UPDATE`, `GRANT_PERMISSION`, `EXPORT` |
| **Validation Rules**| Business/logic checks enforced during data changes (e.g., "Age must be ≥18").  | `ValidateUserAge(user.age ≥ 18)`     |
| **Audit Trail**     | Sequential chain of audit records for an entity (e.g., a single user record).  | `[AUD-1234, AUD-1235, AUD-1236]`    |
| **Query Interface** | Methods to retrieve audit data (e.g., by time range, user, or entity).        | `GetAuditLog("2024-01-01", "2024-01-31")` |

---

### **2.2 Data Flow**
1. **Trigger**: An action (e.g., user edit, system update) occurs.
2. **Capture**: System records metadata (user, timestamp, action, affected entity).
3. **Validate**: Applicable rules are checked (e.g., data integrity, permissions).
4. **Log**: Record is added to the audit trail (immutable storage).
5. **Query/Report**: Admins/auditors retrieve logs via defined interfaces.

---
## **3. Schema Reference**
Below is the standardized schema for audit records. Extend fields as needed for your domain.

### **3.1 Audit Record Schema**
| **Field**          | **Type**       | **Required** | **Description**                                                                 | **Example Values**                     |
|--------------------|----------------|--------------|---------------------------------------------------------------------------------|----------------------------------------|
| `record_id`        | `UUID`         | ✅ Yes        | Unique identifier for the audit log entry.                                     | `a1b2c3d4-5678-90ef-ghij-klmnopqrstuv` |
| `timestamp`        | `ISO8601 Datetime` | ✅ Yes      | When the action occurred.                                                       | `2024-05-20T14:30:45Z`                |
| `user_id`          | `String`       | ✅ Yes        | Identifier of the user/actor.                                                   | `"sys-admin"`                         |
| `user_type`        | `Enum`         | ❌ No         | Role of the user (e.g., `ADMIN`, `END_USER`, `SYSTEM`).                         | `"ADMIN"`                             |
| `action`           | `Enum`         | ✅ Yes        | Standardized action verb (see **Action Types** below).                         | `"UPDATE"`, `"DELETE"`                 |
| `entity_id`        | `String`       | ✅ Yes        | ID of the affected data entity (e.g., `User#42`).                              | `"User#42"`                           |
| `entity_type`      | `String`       | ✅ Yes        | Type of entity (e.g., `User`, `Order`, `Payment`).                              | `"User"`                              |
| `before`           | `JSON`         | ❌ No         | Previous state of the entity (if applicable).                                   | `{"name": "Alice", "age": 25}`        |
| `after`            | `JSON`         | ❌ No         | New state of the entity (if applicable).                                        | `{"name": "Alicia", "age": 26}`       |
| `ip_address`       | `String`       | ❌ No         | Source IP of the request (if available).                                        | `"192.168.1.1"`                       |
| `status`           | `String`       | ✅ Yes        | Outcome of the action (`SUCCESS`, `FAILED`, `PENDING`).                         | `"SUCCESS"`                           |
| `error`            | `String`       | ❌ No         | Error message (if `status = "FAILED"`).                                        | `"Validation failed: Age must be ≥18"` |
| `metadata`         | `JSON`         | ❌ No         | Custom key-value pairs (e.g., `{"client_id": "ABC123"}`).                      | `{}`                                  |

---

### **3.2 Action Types (Enum)**
| **Action**               | **Description**                                                                 |
|--------------------------|---------------------------------------------------------------------------------|
| `CREATE`                 | New entity was added.                                                            |
| `UPDATE`                 | Entity was modified.                                                              |
| `DELETE`                 | Entity was removed.                                                               |
| `GRANT_PERMISSION`      | Access/permission was assigned.                                                   |
| `REVOKE_PERMISSION`     | Access/permission was revoked.                                                   |
| `EXPORT`                 | Data was exported (e.g., CSV, PDF).                                               |
| `LOGIN`/`LOGOUT`         | User session events.                                                              |
| `SYSTEM_MIGRATION`       | Bulk data changes (e.g., database schema update).                                 |

---

## **4. Implementation Details**
### **4.1 Storage**
- **Immutability**: Use a write-once storage (e.g., Amazon S3, Google Cloud Storage) or a database with timestamp-based append-only tables.
- **Retention Policy**: Automatically purge logs older than `X` days/months (compliance requirement).
- **Backup**: Regularly back up audit logs to a secure location.

### **4.2 Validation Rules**
Example rules (adjust per domain):
| **Rule**                          | **Trigger**               | **Action if Failed**               |
|-----------------------------------|---------------------------|------------------------------------|
| `UserAgeValidation`               | `CREATE`/`UPDATE` on `User`| Reject change; log `ERROR`.        |
| `PermissionCheck`                 | `GRANT_REVOKE_PERMISSION` | Require `ADMIN` role.             |
| `DataEncryptionCheck`             | All actions               | Ensure sensitive fields are encrypted. |

### **4.3 Access Controls**
- **Role-Based Access**:
  - `AUDITOR`: Read-only access to audit logs.
  - `ADMIN`: Full access (read/write).
  - `END_USER`: No direct access (only their own actions).
- **Audit Log Queries**: Restrict to specific time ranges/users (e.g., `GET_AUDIT_LOGS(user_id="sys-admin")`).

---

## **5. Query Examples**
### **5.1 Querying Audit Logs**
Assume a REST API endpoint: `GET /audit-logs?{filters}`

| **Query**                                                                 | **Purpose**                                      | **Example Response (JSON)**                                                                 |
|--------------------------------------------------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------|
| `GET /audit-logs?entity_type=User`                                       | Find all user-related actions.                   | `[{...}, {...}]` (list of audit records with `entity_type="User"`).                        |
| `GET /audit-logs?user_id=admin&start=2024-01-01&end=2024-01-31`           | Audit admin actions in January 2024.             | `[{...}, {...}]` (filtered by user and date range).                                         |
| `GET /audit-logs?action=UPDATE&status=FAILED`                            | Identify failed updates.                         | `[{...}]` (records where `status="FAILED"` and `action="UPDATE"`).                          |
| `GET /audit-logs?entity_id=User#42`                                      | Full audit trail for a specific user.            | `[{...}, {...}]` (all actions for `User#42`, ordered by `timestamp`).                       |
| `GET /audit-logs?metadata.client_id=ABC123`                               | Audit actions tied to a client.                  | `[{...}]` (records with `metadata.client_id="ABC123"`).                                    |

---

### **5.2 Exporting Audit Data**
- **CSV/JSON Export**: Use:
  ```bash
  curl -X GET "http://api.example.com/audit-logs?format=json" --output audit_logs.json
  ```
- **Aggregated Reports**: Example SQL for a database-backed audit system:
  ```sql
  -- Count failed updates by user
  SELECT user_id, COUNT(*) as failed_updates
  FROM audit_logs
  WHERE action = 'UPDATE' AND status = 'FAILED'
  GROUP BY user_id;
  ```

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use Together**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Immutable Data**        | Ensures data cannot be altered after creation (e.g., blockchain-like logs).    | When absolute immutability is required (e.g., financial transactions).                   |
| **Permission System**     | Manages fine-grained access controls (e.g., RBAC, ABAC).                     | When audit logs need to filter by user permissions.                                     |
| **Data Encryption**       | Protects sensitive audit data (e.g., PII in logs).                           | When audit logs contain personal or confidential information.                             |
| **Event Sourcing**        | Stores system state as a sequence of events (like audit logs).               | For complex audit needs (e.g., replaying system state changes).                           |
| **Compliance Checker**    | Validates logs against regulatory standards (e.g., GDPR right to erasure).     | When compliance is critical (e.g., healthcare, finance).                                  |
| **Audit Trail Visualization** | Dashboards/charts for audit data (e.g., Grafana, Tableau).      | When dashboards are needed for trend analysis or real-time monitoring.                  |

---
## **7. Best Practices**
1. **Granularity**: Log at the right level (e.g., log individual field changes in `UPDATE` actions).
2. **Performance**: Index frequently queried fields (e.g., `user_id`, `timestamp`).
3. **Compression**: Archive old logs to reduce storage costs.
4. **Alerting**: Set up notifications for critical events (e.g., failed `DELETE` on sensitive data).
5. **Documentation**: Clearly define rules and validate them during system design/review.
6. **Testing**: Simulate audit scenarios (e.g., "What if an admin deletes a record?").

---
## **8. Example Implementation (Pseudocode)**
```python
# Pseudocode for an Audit Service
class AuditService:
    def __init__(self, storage: Storage):
        self.storage = storage  # e.g., S3, PostgreSQL

    def log_action(self, action: str, entity_id: str, user_id: str, **metadata):
        record = {
            "record_id": uuid4(),
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "action": action,
            "entity_id": entity_id,
            "entity_type": metadata.get("entity_type"),
            "before": metadata.get("before"),
            "after": metadata.get("after"),
            "status": "SUCCESS",
            "error": None,
        }
        self.storage.append(record)

    def query_logs(self, filters: dict):
        # Example: filters = {"user_id": "admin", "start": "2024-01-01"}
        return self.storage.query(filters)

# Usage
audit = AuditService(S3Storage())
audit.log_action(
    action="UPDATE",
    entity_id="User#42",
    user_id="sys-admin",
    entity_type="User",
    before={"name": "Alice"},
    after={"name": "Alicia"},
)
```

---
## **9. Compliance Mapping**
| **Regulation** | **Requirement**                                                                 | **How Audit Standards Pattern Helps**                                                 |
|----------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **GDPR**       | Right to erasure (Article 17).                                               | Log all `DELETE` actions for data subjects; enable traceability.                      |
| **HIPAA**      | Audit controls for protected health information (PHI).                        | Track PHI access/modifications with `USER_ID`, `IP_ADDRESS`, and timestamps.            |
| **SOC 2**      | Continuous monitoring of system access.                                        | Audit logs provide evidence for access reviews.                                        |
| **SOX**        | Financial record integrity.                                                   | Immutable audit trails for financial transactions.                                     |
| **PCI DSS**    | Logging of all access to cardholder data.                                     | Log all `CREATE`/`UPDATE`/`DELETE` on payment data with `USER_ID` and `TIMESTAMP`.     |

---
## **10. Troubleshooting**
| **Issue**                          | **Cause**                                      | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------|-----------------------------------------------------------------------------|
| **Slow Queries**                   | Missing indexes on `user_id`/`timestamp`.      | Add indexes to frequently queried fields.                                  |
| **Storage Bloat**                  | Retaining logs beyond compliance requirements. | Implement automated cleanup (e.g., purge logs >1 year old).                |
| **False Negatives**                | Validation rules not covering all edge cases.  | Review rules periodically and add tests for new scenarios.                  |
| **Unauthorized Access to Logs**     | Insufficient RBAC for audit queries.           | Restrict `AUDITOR` role to read-only access.                               |
| **Missing Critical Logs**          | Logging middleware not capturing all actions.  | Audit all critical endpoints (e.g., admin API calls).                      |

---
## **11. Further Reading**
- [NIST Special Publication 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) (Audit Log Requirements)
- [OWASP Audit Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Audit_Logging_Cheat_Sheet.html)
- [GDPR Right to Erasure Guide](https://gdpr.eu/right-to-erasure/)