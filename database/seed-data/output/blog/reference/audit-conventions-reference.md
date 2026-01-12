# **[Pattern] Audit Conventions Reference Guide**

---

## **Overview**
Audit Conventions standardize how changes to system data are tracked, recorded, and interpreted across an organization or application. This reference guide defines essential structuring rules, metadata fields, and operational behaviors for audit logs. By adhering to these conventions, teams ensure consistency in debugging, compliance auditing, and system integrity enforcement. Key principles include **immutability** (logs cannot be modified post-creation), **completeness** (all relevant changes are captured), and **clarity** (fields map to business logic).

---

## **Implementation Details**

### **Core Concepts**
| Concept               | Description                                                                                     | Example Use Case                          |
|-----------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------|
| **Audit Record**      | A immutable entry capturing a single action event.                                             | Database row update, user login attempt.  |
| **Immutable Timestamp** | A universally readable timestamp that cannot be altered (e.g., ISO-8601).                   | `2023-11-15T14:30:00Z`                     |
| **Change Vector**     | Fields describing what *changed* (delta) in an audit record.                                   | `{ "field": "price", "old_value": 9.99, "new_value": 10.99 }` |
| **Actor Metadata**    | Contextual info about who/what performed the action (e.g., user ID, service name).             | `{ "actor": "user-1234", "service": "api-gateway" }` |
| ** Severity Level**   | Categorization of action importance (e.g., CRITICAL, INFO).                                   | `SEVERITY: CRITICAL` (e.g., failed login). |

---

### **Standard Fields**
Audit records must include the following fields (with **required** or *optional* annotations):

| Field               | Type              | Required | Description                                                                                     | Constraints/Format                                |
|---------------------|-------------------|----------|-------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **`record_id`**     | UUID              | ✅        | Unique identifier for the audit record.                                                       | RFC 4122 compliant.                               |
| **`event_timestamp`** | ISO-8601 datetime | ✅        | When the action occurred.                                                                       | `YYYY-MM-DDTHH:MM:SSZ`.                            |
| **`event_type`**    | String            | ✅        | Type of event (e.g., `USER_LOGIN`, `DATABASE_UPDATE`).                                         | Predefined taxonomy (see **Taxonomy** section).     |
| **`resource_id`**   | String            | *         | Identifier of affected resource (e.g., `order-5678`).                                          | Depends on domain logic.                          |
| **`actor_id`**      | String            | *         | Unique identifier of the entity performing the action (e.g., user/role/service).              | User UUID, system-generated ID, or API key.         |
| **`actor_type`**    | Enum              | *         | Classification of the actor (e.g., `USER`, `SERVICE`).                                         | `USER`, `SERVICE`, `SYSTEM`.                      |
| **`change_vector`** | JSON object       | *         | Delta of changes (key-value pairs for affected fields).                                       | See **Change Vector Schema** below.                |
| **`metadata`**      | JSON object       | *         | Additional context (e.g., IP address, correlated request IDs).                               | Customizable by domain.                           |
| **`severity`**      | Enum              | ✅        | Impact/importance of the event.                                                             | `INFO`, `WARNING`, `CRITICAL`, `AUDIT`.            |

---

## **Change Vector Schema**
If present, `change_vector` must adhere to this structure:

| Field          | Type      | Description                                                                                     | Example Value                          |
|----------------|-----------|-------------------------------------------------------------------------------------------------|----------------------------------------|
| **`field`**    | String    | Name of changed field.                                                                         | `"price"`                               |
| **`old_value`**| Any       | Previous value (if applicable).                                                                | `9.99`, `null`                         |
| **`new_value`**| Any       | New value after change.                                                                       | `"10.99"`, `[{"id": 1}, {"id": 2}]`    |
| **`timestamp`**| ISO-8601  | When the change was applied (optional if `event_timestamp` suffices).                         | `2023-11-15T14:31:00Z`                 |

---
**Note:** For bulk operations (e.g., database migrations), include an array of `change_vector` entries.

---

## **Taxonomy of Event Types**
Predefined `event_type` values must align with the following categories:

| Category               | Example Event Types                                                                       |
|------------------------|-----------------------------------------------------------------------------------------|
| **Authentication**     | `USER_LOGIN`, `SSO_AUTHENTICATION`, `PASSWORD_RESET`, `FAILED_LOGIN`                     |
| **Authorization**      | `ROLE_ASSIGNMENT`, `PERMISSION_REVOKE`, `ACCESS_DENIED`                                  |
| **Data Operations**    | `DATABASE_INSERT`, `DATABASE_UPDATE`, `DATABASE_DELETE`, `DATA_EXPORT`                 |
| **Configuration**      | `API_KEY_ROTATE`, `FEATURE_FLAG_TOGGLE`, `THRESHOLD_UPDATE`                             |
| **Security Events**    | `BRUTE_FORCE_DETECTED`, `INTEGRITY_CHECK_FAILED`, `ANOMALY_DETECTED`                    |
| **System Events**      | `SERVICE_DEPLOYMENT`, `SCALE_UP`, `LOG_RETENTION_PURGE`                                  |

---
**Custom Types:** Domain-specific events (e.g., `INVOICE_GENERATED`) must be preapproved by the audit review board.

---

## **Query Examples**
### **1. Find All Critical Login Failures (Last 7 Days)**
```sql
SELECT *
FROM audit_logs
WHERE event_type = 'FAILED_LOGIN'
  AND severity = 'CRITICAL'
  AND event_timestamp >= DATEADD(day, -7, GETDATE());
```

### **2. Trace a Resource’s Changes (e.g., Order #5678)**
```sql
SELECT *
FROM audit_logs
WHERE resource_id = 'order-5678'
  AND event_type IN ('DATABASE_UPDATE', 'DATABASE_DELETE')
ORDER BY event_timestamp DESC;
```

### **3. Cross-Reference Actor Actions (e.g., User 1234)**
```sql
SELECT actor_id, event_type, resource_id, change_vector
FROM audit_logs
WHERE actor_id = 'user-1234'
  AND event_timestamp > '2023-11-01';
```

### **4. Bulk Export for Compliance (GDPR)**
```sql
-- Export all user-related events (mask PII if needed)
SELECT
  record_id,
  event_timestamp,
  event_type,
  resource_id,
  actor_id,
  -- Sensitive fields sanitized (see **Data Protection** section)
  JSON_REMOVE(metadata, '$.ip_address')
FROM audit_logs
WHERE actor_type = 'USER'
  AND event_timestamp BETWEEN '2023-01-01' AND '2023-12-31';
```

---

## **Data Protection**
- **PII Handling:** Mask or exclude sensitive fields (e.g., `metadata.ip_address`) unless required by law.
- **Retention:** Audit logs must comply with organizational retention policies (default: **365 days** for critical events).
- **Access Control:** Restrict query access via RBAC (e.g., `audit:view` permission).

---

## **Error Handling**
| Error Code | Condition                          | Recommended Action                                      |
|------------|------------------------------------|--------------------------------------------------------|
| `E001`     | Missing `event_timestamp`           | Reject record; log as `SYSTEM_ERROR` in new record.     |
| `E002`     | Invalid `change_vector` format      | Reject record; send notification to ops team.          |
| `E003`     | Duplicate `record_id`               | Overwrite record (if recent) or escalate to auditor.   |

---

## **Related Patterns**
1. **[Event Sourcing](link)**
   - *For* applications requiring a full history of state changes (e.g., financial systems).
   - *Contrast* with Audit Conventions, which focus on *who/what/when* rather than *how*.

2. **[Immutable Logs](link)**
   - *For* ensuring logs cannot be tampered with post-creation (e.g., WORM storage).

3. **[Data Lineage](link)**
   - *For* tracking *how* data was derived (e.g., ETL pipelines) alongside *who* modified it.

4. **[Activity Streams](link)**
   - *For* user-facing activity feeds (e.g., social media timelines) where readability > strict schema.

5. **[Compliance Traceability](link)**
   - *For* mapping audit logs to regulatory requirements (e.g., HIPAA, SOX).

---
## **Best Practices**
1. **Standardize Tools:** Use unified logging frameworks (e.g., ELK Stack, Splunk, AWS CloudTrail).
2. **Automate Tagging:** Tag records with `environment` (e.g., `prod`, `staging`) and `region`.
3. **Alerting:** Configure alerts for `severity=CRITICAL` or `event_type=FAILED_LOGIN`.
4. **Document Exceptions:** Clearly document deviations from conventions (e.g., legacy systems).
5. **Audit Logs for Logs:** Track changes to audit log configurations (e.g., `AUDIT_CONFIG_UPDATE`).

---
**Last Updated:** `2023-11-15`
**Owner:** [CISO/Architecture Team]