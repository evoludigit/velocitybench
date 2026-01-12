# **[Pattern] Audit Testing Reference Guide**

---

## **Overview**
The **Audit Testing** pattern ensures data integrity, compliance, and accountability by validating system operations against predefined rules, logs, or business policies. This pattern is critical in financial systems, regulatory environments (e.g., GDPR, SOX), and any domain requiring traceable, non-repudiable transactions. Audit Testing automates verification of:
- **Data consistency** (e.g., no duplicated records, valid state transitions).
- **Policy adherence** (e.g., access control, transaction thresholds).
- **Operational integrity** (e.g., no unauthorized modifications, correct sequencing of events).

Implementations typically involve **rule-based engines**, **log analysis**, and **comparative validation** against golden sources or expected states. This guide outlines key concepts, schema standards, query techniques, and integration with complementary patterns.

---

## **Implementation Details**

### **Core Components**
| **Component**          | **Description**                                                                                                                                                                                                 | **Example Use Case**                          |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Audit Logs**         | Immutable records of system events (e.g., CRUD operations, access attempts, error logs). Must include timestamps, user IDs, entity metadata, and outcomes.                                                      | Tracking who modified a customer’s credit limit. |
| **Validation Rules**   | Predefined conditions (e.g., "No negative balances," "All transactions must have approvals > $10K"). Can be static or dynamic (e.g., role-based).                                                          | Rejecting a transfer exceeding department limits. |
| **Golden Source**      | Authoritative dataset (e.g., ERP system, regulatory database) used as a baseline for validation.                                                                                                                 | Cross-referencing audit logs with the accounting ledger. |
| **Rule Engine**        | Evaluates logs/transactions against rules (e.g., Drools, Apache NiFi, custom scripts). Often triggers alerts or remediation actions.                                                                         | Flagging transactions with mismatched timestamps. |
| **Reporting Dashboard**| Visualizes audit findings (e.g., anomalies, compliance gaps) with drill-down capabilities to logs or affected records.                                                                                         | Highlighting SOX violations in real time.      |
| **Remediation Workflow**| Defines corrective actions (e.g., rollback, user notification, automated fixes) tied to rule violations.                                                                                                       | Auto-reverting a failed transaction.          |

---

### **Key Design Principles**
1. **Immutability**: Audit logs must not be altered post-creation (e.g., append-only storage, blockchain-like hashes).
2. **Granularity**: Logs should capture **what**, **when**, **who**, and **why** (e.g., include justification for high-risk actions).
3. **Separation of Concerns**:
   - **Data Validation**: Ensure logs are complete (e.g., no null fields).
   - **Rule Logic**: Isolate business rules from audit logic for easier updates.
4. **Performance**: Optimize for log volume (e.g., batch processing, indexing by entity/type).
5. **Compliance Adaptability**: Design rules to accommodate regulatory changes (e.g., dynamic rule loading).

---

### **Schema Reference**
Below is a standardized schema for audit logs. Customize fields based on domain (e.g., add `transaction_id` for financial systems).

| **Field**               | **Data Type**       | **Description**                                                                                                                                                                                                 | **Example Values**                          | **Required?** |
|-------------------------|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|---------------|
| `audit_id`              | UUID/varchar        | Unique identifier for the log entry.                                                                                                                                                                             | `550e8400-e29b-41d4-a716-446655440000`     | Yes           |
| `entity_type`           | varchar             | Type of entity affected (e.g., `CUSTOMER`, `PAYMENT`, `ACCOUNT`).                                                                                                                                                 | `ACCOUNT`                                   | Yes           |
| `entity_id`             | varchar/UUID        | Primary key of the entity (e.g., customer ID).                                                                                                                                                               | `CUST-12345`                                | Yes           |
| `operation`             | varchar             | Type of action (e.g., `CREATE`, `UPDATE`, `DELETE`, `LOGIN`).                                                                                                                                                   | `UPDATE`                                    | Yes           |
| `user_id`               | varchar             | User/system account performing the action.                                                                                                                                                                     | `jdoe`                                       | Yes           |
| `timestamp`             | timestamp           | When the operation occurred (use UTC).                                                                                                                                                                             | `2023-10-15T14:30:00Z`                     | Yes           |
| `ip_address`            | varchar             | Source IP of the request (for remote actions).                                                                                                                                                                   | `192.168.1.100`                             | Conditional*  |
| `action_status`         | varchar             | Outcome (e.g., `SUCCESS`, `FAILED`, `PENDING`).                                                                                                                                                                   | `SUCCESS`                                   | Yes           |
| `error_code`            | varchar             | System error code (if `action_status = FAILED`).                                                                                                                                                               | `ERR-403`                                   | Conditional   |
| `request_data`          | JSON/object         | Input parameters (sanitized to avoid sensitive data leaks).                                                                                                                                                     | `{"amount": 1000, "currency": "USD"}`       | Conditional   |
| `response_data`         | JSON/object         | Output data (if applicable).                                                                                                                                                                                   | `{"balance": 2500}`                         | Conditional   |
| `metadata`              | JSON/object         | Extensible field for domain-specific data (e.g., approval chain, audit trail depth).                                                                                                                               | `{"approval": "manager@company.com"}`       | Conditional   |
| `correlation_id`        | varchar            | Links related events (e.g., multi-step transactions).                                                                                                                                                           | `txn-789abc`                                | Conditional   |

---
*`ip_address` is required for remote operations; skip for internal systems.

---
### **Database Indexing Recommendations**
To optimize query performance, index:
- `(entity_type, entity_id, operation)` for entity-specific searches.
- `(timestamp)` for time-range queries (e.g., "Show all logs from last 24 hours").
- `(user_id)` if user-level audits are frequent.
- `(action_status = 'FAILED')` for error analysis.

**Example Index Creation (PostgreSQL):**
```sql
CREATE INDEX idx_audit_operation ON audit_log(entity_type, entity_id, operation);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
```

---

## **Query Examples**

### **1. Find All Failed Transactions in the Last 30 Days**
```sql
SELECT
    entity_id,
    operation,
    user_id,
    timestamp,
    error_code
FROM audit_log
WHERE
    action_status = 'FAILED'
    AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;
```

### **2. List All Users Who Modified a Specific Customer**
```sql
SELECT DISTINCT user_id, COUNT(*) as modification_count
FROM audit_log
WHERE
    entity_type = 'CUSTOMER'
    AND entity_id = 'CUST-12345'
    AND operation IN ('UPDATE', 'CREATE', 'DELETE')
GROUP BY user_id
ORDER BY modification_count DESC;
```

### **3. Check for Data Integrity: Is the Current Balance Valid?**
*(Assuming a `balances` table is the golden source.)*
```sql
WITH final_balance AS (
    SELECT entity_id, MAX(timestamp) as last_update
    FROM audit_log
    WHERE entity_type = 'ACCOUNT'
        AND operation IN ('UPDATE', 'TRANSFER')
    GROUP BY entity_id
)
SELECT
    a.entity_id,
    CASE
        WHEN b.current_balance != COALESCE(aa.new_balance, aa.old_balance)
        THEN 'INCONSISTENT'
        ELSE 'VALID'
    END as integrity_status
FROM final_balance f
JOIN accounts b ON b.account_id = f.entity_id
JOIN (
    SELECT entity_id, request_data->>'new_balance' as new_balance, request_data->>'old_balance' as old_balance
    FROM audit_log
    WHERE operation = 'UPDATE'
        AND request_data->>'new_balance' IS NOT NULL
) aa ON aa.entity_id = f.entity_id
WHERE f.last_update = (
    SELECT MAX(timestamp)
    FROM audit_log
    WHERE entity_id = f.entity_id
);
```

### **4. Detect Unauthorized Login Attempts (Brute Force)**
```sql
SELECT
    user_id,
    COUNT(*) as attempt_count,
    MIN(timestamp) as first_attempt
FROM audit_log
WHERE
    operation = 'LOGIN'
    AND action_status = 'FAILED'
GROUP BY user_id
HAVING COUNT(*) > 5  -- Threshold for brute force
ORDER BY attempt_count DESC;
```

### **5. Generate aSOX-Compliant Report: Segregation of Duties (SoD) Violations**
```sql
WITH sensitive_operations AS (
    SELECT entity_id, operation, user_id
    FROM audit_log
    WHERE operation IN ('TRANSFER', 'PAYMENT_APPROVAL', 'ACCESS_GRANT')
        AND timestamp >= DATE_TRUNC('month', CURRENT_DATE)  -- Last month
),
user_roles AS (
    SELECT user_id, role
    FROM user_roles_table  -- Assume this table exists
)
SELECT
    s.operation,
    s.user_id,
    r.role,
    COUNT(DISTINCT s.entity_id) as sensitive_actions_count
FROM sensitive_operations s
JOIN user_roles r ON s.user_id = r.user_id
WHERE EXISTS (
    SELECT 1
    FROM user_roles r2
    WHERE r2.user_id = s.user_id
        AND r2.role = 'FINANCE_ADMIN'  -- SoD violation: one user can't approve AND transfer
)
GROUP BY s.operation, s.user_id, r.role
HAVING COUNT(DISTINCT s.entity_id) > 0;
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                                                                                                                                                     | **Connection to Audit Testing**                                                                                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Data Validation**       | Ensures input/output data meets structural and semantic requirements (e.g., format, constraints, business rules).                                                                                                         | Audit Testing relies on **Data Validation** to flag invalid operations in logs.                                                                                                                                                   |
| **Event Sourcing**        | Stores system state as a sequence of immutable events.                                                                                                                                                                          | Audit Testing leverages **Event Sourcing** for precise, time-ordered logs of all state changes.                                                                                                                              |
| **Immutable Infrastructure** | Uses infrastructure-as-code (IaC) and version control to prevent unauthorized changes.                                                                                                                                          | Audit Testing extends to **Immutable Infrastructure** by logging changes to configurations/deployments (e.g., Kubernetes manifest updates).                                                                                     |
| **Row-Level Security (RLS)** | Restricts database access to rows based on user attributes (e.g., `WHERE department_id = current_user().department_id`).                                                                                                  | Audit Testing logs **RLS violations** or successful access patterns to ensure compliance.                                                                                                                                  |
| **Chaos Engineering**     | Tests system resilience by injecting failures.                                                                                                                                                                              | Audit Testing records **Chaos Engineering** experiments to validate recovery procedures and log anomalies introduced during tests.                                                                                               |
| **Guardrails**            | Enforces policies at the API/database level (e.g., rate limiting, input sanitization).                                                                                                                                       | Audit Testing logs **Guardrail** violations (e.g., too many API calls from a single IP) for post-hoc analysis.                                                                                                               |
| **Consensus Protocols**   | Distributed systems (e.g., Kafka, blockchain) use consensus to ensure data consistency.                                                                                                                                       | Audit Testing validates that **consensus protocols** are followed (e.g., no duplicate transactions in a ledger).                                                                                                        |
| **NoSQL Event Stores**    | Stores high-velocity events (e.g., IoT sensor data) in schemaless databases.                                                                                                                                                   | Audit Testing adapts to **NoSQL Event Stores** by querying flexible log schemas (e.g., `SELECT * FROM audit_log WHERE operation = 'SENSOR_READING' AND timestamp > now() - 1h`).                                             |
| **Canary Releases**       | Gradually rolls out changes to a subset of users.                                                                                                                                                                           | Audit Testing compares logs between **canary** and production users to detect edge-case issues early.                                                                                                                       |
| **Policy as Code**        | Defines policies (e.g., IAM, network) in code for versioning and automation.                                                                                                                                                  | Audit Testing validates **Policy as Code** enforcement by logging policy evaluations (e.g., "User denied access per IAM rule X").                                                                                               |

---

## **Best Practices**
1. **Retention Policy**:
   - Store logs for **7–10 years** (e.g., financial audits) or indefinitely for critical systems.
   - Use **Tiered Storage**: Hot (frequently accessed), warm (archived), cold (long-term).

2. **Log Enrichment**:
   - Append contextual data (e.g., geolocation via `ip_address`, business rules metadata).

3. **Automated Alerts**:
   - Trigger alerts for:
     - **Rule violations** (e.g., "Suspicious login from China at 3 AM").
     - **Anomalies** (e.g., "User deleted 10 records in 5 seconds").
     - **Threshold breaches** (e.g., "More than 5 failed logins").

4. **Third-Party Integrations**:
   - Sync logs with **SIEM tools** (Splunk, ELK) for advanced threat detection.
   - Export findings to **compliance platforms** (e.g., ServiceNow for ITIL audits).

5. **Performance Optimization**:
   - **Sampling**: For high-volume systems, audit a sample (e.g., 1% of transactions).
   - **Denormalization**: Pre-aggregate common queries (e.g., user activity dashboards).

6. **Testing Audit Testing**:
   - Regularly validate your audit system itself (e.g., "Does the audit log log *all* operations?").
   - Use **red-team exercises** to simulate compliance violations.

7. **Documentation**:
   - Maintain a **rule registry** documenting all audit rules, owners, and business justification.
   - Include **failure modes** (e.g., "If the log database fails, we’ll rely on this backup").

---

## **Anti-Patterns**
| **Anti-Pattern**               | **Description**                                                                                                                                                                                                 | **Mitigation**                                                                                                                                                                                                 |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Over-Audit**                  | Logging every minor event (e.g., mouse clicks) creates noise and performance overhead.                                                                                                                 | Focus on **business-critical** operations (e.g., financial transactions). Use sampling for high-volume systems.                                                                                       |
| **After-the-Fact Justifications** | Adding metadata (e.g., `justification`) post-event to "explain" violations.                                                                                                                              | Enforce **real-time justification** (e.g., require comments during rule violations).                                                                                                                 |
| **Ignoring Logs**               | Failing to act on audit findings despite alerts.                                                                                                                                                            | Integrate with **incident management** systems (e.g., Jira, PagerDuty) to close loops on violations.                                                                                                   |
| **Inconsistent Logging**        | Missing fields (e.g., `user_id` omitted for internal scripts) or inconsistent formats.                                                                                                                 | Enforce **schema validation** on log entries (e.g., JSON validation). Use tools like **OpenTelemetry** for standardized telemetry.                                                                     |
| **Manual Rule Updates**         | Hardcoding rules in scripts without version control or rollback plans.                                                                                                                                   | Use **rule engines** (e.g., Drools) with **git-backed configuration**.                                                                                                                              |
| **Weak Immutability**           | Allowing log edits (e.g., via database `UPDATE` instead of appends).                                                                                                                                         | Store logs in **append-only** systems (e.g., Kafka, S3 Object Lock). Use **hash chains** to detect tampering.                                                                                           |

---
This guide provides a foundation for implementing robust **Audit Testing**. Customize schemas, rules, and queries to align with your organization’s compliance requirements and technical stack.