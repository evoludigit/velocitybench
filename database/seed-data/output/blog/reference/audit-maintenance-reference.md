# **[Pattern] Audit Maintenance Reference Guide**
**Version:** 1.0
**Last Updated:** [Insert Date]

---

## **1. Overview**
The **Audit Maintenance** pattern ensures that all changes to critical data—such as configuration, policies, or system states—are persistently recorded for traceability, compliance, and diagnostics. This pattern prevents loss of context by capturing metadata (e.g., who/when/what changed) alongside the modified data. It is essential for systems requiring **immutable audit trails** (e.g., financial systems, healthcare records, or regulatory-compliant environments).

Key features:
- **Automatic logging** of state changes via triggers (e.g., database triggers, event streams).
- **Immutable storage** of audit entries to prevent tampering.
- **Queryable for historical analysis** (e.g., "Who modified user X’s role 3 days ago?").
- **Supports rollback** for accidental changes via snapshots.

---

## **2. Schema Reference**
Below is the **core audit schema** and related configurations.

| **Field**               | **Type**         | **Description**                                                                 | **Example**                          | **Mandatory?** |
|--------------------------|------------------|---------------------------------------------------------------------------------|--------------------------------------|-----------------|
| `audit_id`               | UUID             | Unique identifier for the audit entry.                                          | `"a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6"`  | ✅              |
| `entity_id`              | String           | ID of the entity modified (e.g., `user_123`, `policy_456`).                      | `"config_db_connection"`              | ✅              |
| `entity_type`            | Enum             | Classifies the entity type (e.g., `user`, `system_setting`, `file`).            | `"system_setting"`                    | ✅              |
| `change_type`            | Enum             | Type of change: `create`, `update`, `delete`, `revert`.                         | `"update"`                           | ✅              |
| `old_value`              | JSON/Blob        | Previous state (for updates/deletes).                                           | `{"timeout": 30}`                     | ❌ (Conditional) |
| `new_value`              | JSON/Blob        | New state (for creates/updates).                                               | `{"timeout": 60}`                     | ❌ (Conditional) |
| `changed_by`             | String           | User/process ID (e.g., `admin:jdoe`, `api_service:backup`).                    | `"admin:jdoe"`                        | ✅              |
| `change_timestamp`       | Timestamp        | When the change occurred (ISO 8601 format).                                     | `"2024-05-20T14:30:00Z"`             | ✅              |
| `metadata`               | JSON             | Additional context (e.g., `reason`, `ip_address`, `batch_id`).                   | `{"reason": "security_update"}`      | ❌              |
| `is_active`              | Boolean          | Flags if the audit entry reflects the current state (`true` for live changes).  | `true`                               | ✅              |

---
### **Related Tables/Collections**
| **Component**       | **Purpose**                                                                 | **Example Fields**                          |
|---------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `entities`          | Stores current state of audited entities (linked via `entity_id`).        | `id`, `name`, `value`                       |
| `audit_actions`     | Maps change types to human-readable labels (for UI/localization).          | `code`, `description`                       |
| `snapshots`         | Point-in-time backups of entities (for rollback).                          | `snapshot_id`, `entity_id`, `data`          |

---

## **3. Implementation Details**

### **3.1 Core Components**
1. **Audit Generator**
   - Triggers on entity changes (e.g., database triggers, application events).
   - Validates metadata before logging (e.g., checks `changed_by` for auth).

2. **Audit Store**
   - Immutable database (e.g., **TimescaleDB**, **Amazon Timestream**, or **PostgreSQL with temporal tables**).
   - Sharding by `entity_type`/`change_timestamp` for scalability.

3. **Query Engine**
   - Optimized for:
     - **Time-range queries** (e.g., "Show changes in the last 7 days").
     - **Entity-specific history** (e.g., "Rollback `user_123` to 2024-05-15").

4. **Rollback Mechanism**
   - Uses `snapshots` to revert to a previous state if `change_type = "revert"`.

---

### **3.2 Supported Change Types**
| **Type**     | **Trigger Example**               | **Audit Entry Logic**                                                                 |
|--------------|-----------------------------------|---------------------------------------------------------------------------------------|
| `create`     | New user registration.             | Log `old_value = null`, `new_value = {user_data}`.                                      |
| `update`     | Modify a configuration file.       | Log diff between `old_value` and `new_value` (e.g., using JSON patch).                 |
| `delete`     | Soft-delete a user.                | Log `new_value = null`, `is_active = false` in `entities`.                              |
| `revert`     | Undo a misconfiguration.           | Query `snapshots` for the target timestamp; log `change_type = "revert"`.               |
| `batch`      | Bulk import of users.              | Group multiple changes under a single `batch_id` in `metadata`.                         |

---

### **3.3 Validation Rules**
| **Rule**                          | **Enforcement**                                                                 | **Example**                                  |
|------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Audit immutability**             | Write-only access to audit logs (e.g., database triggers disallow updates).     | Use a `VIEW` with `WITH CHECK OPTION`.       |
| **Metadata completeness**         | Require `changed_by` and `change_timestamp` on all entries.                   | Reject logs missing these fields.            |
| **Privilege checks**               | Only administrators can log system-wide changes (e.g., `entity_type = "core"`). | Reject if `changed_by` lacks `admin` role.   |
| **Data integrity**                | `entity_id` in audit logs must match a record in `entities`.                  | Reject orphaned audit entries.               |

---

## **4. Query Examples**
### **4.1 Basic Queries**
#### **List all updates to a user in the last 30 days**
```sql
SELECT
  changed_by,
  change_timestamp,
  old_value,
  new_value
FROM audit_logs
WHERE entity_id = 'user_123'
  AND entity_type = 'user'
  AND change_type = 'update'
  AND change_timestamp >= NOW() - INTERVAL '30 days'
ORDER BY change_timestamp DESC;
```

#### **Find the last 5 changes to a database config**
```sql
SELECT
  changed_by,
  change_timestamp,
  JSONB_PRETTY(new_value)
FROM audit_logs
WHERE entity_type = 'system_setting'
  AND entity_id = 'db_connection_pool'
ORDER BY change_timestamp DESC
LIMIT 5;
```

---

### **4.2 Advanced Queries**
#### **Rollback a configuration to a specific snapshot**
```sql
-- 1. Find the snapshot ID
SELECT snapshot_id, change_timestamp
FROM snapshots
WHERE entity_id = 'db_connection_pool'
  AND change_timestamp < '2024-05-18T10:00:00Z'  -- Target timestamp
ORDER BY change_timestamp DESC
LIMIT 1;

-- 2. Apply the rollback via an application script
UPDATE entities
SET value = (SELECT data FROM snapshots WHERE snapshot_id = 'snap_42')
WHERE id = 'db_connection_pool';

-- 3. Log the revert action
INSERT INTO audit_logs (
  audit_id, entity_id, entity_type, change_type,
  changed_by, change_timestamp, metadata
)
VALUES (
  gen_random_uuid(),
  'db_connection_pool',
  'system_setting',
  'revert',
  'admin:jdoe',
  NOW(),
  '{"snapshot_id": "snap_42", "reason": "reverting to stable config"}'
);
```

#### **Detect anomalies (e.g., rapid-fire changes)**
```sql
WITH rapid_changes AS (
  SELECT
    entity_id,
    changed_by,
    COUNT(*) AS change_count,
    MIN(change_timestamp) AS first_change,
    MAX(change_timestamp) AS last_change
  FROM audit_logs
  WHERE change_timestamp >= NOW() - INTERVAL '5 minutes'
  GROUP BY entity_id, changed_by
  HAVING COUNT(*) > 10  -- Threshold for "rapid"
)
SELECT * FROM rapid_changes
ORDER BY change_count DESC;
```

---

## **5. Related Patterns**
| **Pattern Name**               | **Connection to Audit Maintenance**                                                                 | **When to Combine**                          |
|---------------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------|
| **[CQRS](https://microservices.io/)** | Audit logs can serve as the **read model** for historical queries.                              | Use CQRS for high-throughput audit systems.   |
| **[Event Sourcing](https://martinfowler.com/eaaTutorial/memento.html)** | Audit logs are a form of **event store**; integrate with event streams for real-time processing.   | Replace traditional database triggers.       |
| **[Immutable Infrastructure](https://www.oreilly.com/library/view/immutable-infrastructure-patterns/9781937785659/)** | Audits prove compliance with infrastructure-as-code changes.                                  | Enforce with CI/CD pipelines.               |
| **[Canary Releases](https://www.oreilly.com/library/view/building-microservices/9781491950358/ch06.html)** | Track changes in A/B test environments via audit logs.                                         | Correlate deployments with user impact.     |
| **[Temporal Database](https://www.timescale.com/blog/time-series-database/)** | Optimized for time-series audit data (e.g., IoT devices, logs).                                | Replace flat tables with hypertable storage. |

---

## **6. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                                       | **Fix**                                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **Logging every change**        | Overwhelms storage and query performance.                                                   | Filter sensitive fields (e.g., PII) and aggregate non-critical changes.                     |
| **Storing raw binaries**        | Audit logs bloat with large files (e.g., config file dumps).                                     | Store hashes or deltas (e.g., `md5` checksums) + reference external storage.               |
| **Manual audit log updates**    | Introduces inconsistencies if logs are edited post-facto.                                        | Use write-once storage (e.g., append-only logs).                                           |
| **Ignoring metadata enrichment**| Reduces diagnostic value (e.g., missing `reason` for changes).                                  | Enforce metadata collection via middleware (e.g., OpenTelemetry).                         |
| **No rollback strategy**        | Accidental changes cannot be undone.                                                          | Pair with `snapshots` or versioned entities.                                               |

---
## **7. Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                                     | **Links**                                                                                  |
|---------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **PostgreSQL + Temporal Tables** | Native time-based auditing.                                                                   | [PostgreSQL Docs](https://www.postgresql.org/docs/current/ddl-temporal.html)               |
| **TimescaleDB**           | Time-series optimized audit logs.                                                              | [TimescaleDB](https://www.timescale.com/)                                                 |
| **Amazon Timestream**     | Serverless time-series database for audits.                                                    | [AWS Timestream](https://aws.amazon.com/timestream/)                                      |
| **OpenTelemetry SDK**     | Standardized audit metadata collection.                                                         | [OpenTelemetry Audit](https://opentelemetry.io/docs/specs/otlp/2.0/)                        |
| **Loki + Promtail**       | Log aggregation for audit trails (alternative to databases).                                   | [Grafana Loki](https://grafana.com/oss/loki/)                                             |
| **AWS CloudTrail**        | Pre-built audit logs for AWS services.                                                          | [AWS CloudTrail](https://aws.amazon.com/cloudtrail/)                                       |

---
## **8. Compliance Notes**
| **Regulation**       | **Audit Requirements**                                                                         | **Pattern Alignment**                                                                     |
|----------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **GDPR**             | Right to erasure: Pseudonymize PII in audit logs; allow deletion requests.                      | Store `entity_id` as hashed where sensitive.                                              |
| **SOX**              | Tamper-evident logs for financial transactions.                                                 | Use write-once storage + cryptographic signatures.                                       |
| **HIPAA**            | Audit all access/modifications to patient records.                                              | Enforce `changed_by` for healthcare staff; log `ip_address`.                            |
| **PCI DSS**          | Track all changes to payment systems.                                                          | Integrate with SIEM for anomaly detection.                                               |

---
**Appendix: Example Audit Flow (Diagram)**
*(Visualize a sequence diagram showing: Application → Audit Generator → Immutable Store → Query UI.)*

---
**Feedback?** Report issues or suggest improvements in the [GitHub repo](https://github.com/your-org/audit-pattern).