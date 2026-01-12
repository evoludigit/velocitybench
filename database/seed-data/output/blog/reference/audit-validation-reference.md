# **[Pattern] Audit Validation Reference Guide**

---

## **Overview**
The **Audit Validation** pattern ensures that critical system state changes are reviewable, traceable, and reversible by maintaining immutable audit logs. This pattern is essential for compliance, debugging, and security operations in distributed systems, APIs, and application workflows.

Audit Validation enforces **consistency**, **accountability**, and **recovery** by recording:
- **Who** performed the action.
- **What** was changed (fields, values).
- **When** the change occurred.
- **Why** (contextual metadata).

Players:
- **Producer**: System component generating events (e.g., databases, microservices).
- **Validator**: Business logic enforcing pre/post-change rules.
- **Consumer**: Analytics/Compliance systems querying audit trails.

---

## **Implementation Details**

### **1. Core Components**
| Component       | Description                                                                                     |
|-----------------|-------------------------------------------------------------------------------------------------|
| **Immutable Log** | Time-stamped, append-only record of all changes (e.g., using distributed ledgers like Kafka/Pulsar). |
| **Validation Rules** | Business rules executed *before* and *after* a change (e.g., "No null values in `user.email`"). |
| **Change Capture** | Delta updates (JSON patches) rather than full object snapshots to minimize log size.          |
| **Audit Index** | Efficient lookups by entity ID, timestamps, or user (e.g., Elasticsearch/Lucidworks).         |
| **Replay System** | Mechanisms to rollback or replay validated changes (e.g., sagas, transaction logs).           |

---

### **2. Validation Workflow**
1. **Pre-Validation**: Check if the change violates constraints (e.g., "Is the `status` change authorized?").
2. **Change Execution**: Apply the change to the primary system (e.g., database).
3. **Post-Validation**: Verify integrity (e.g., "Does the sum of `balance` fields equal zero across accounts?").
4. **Audit Logging**: Record the event in the immutable log.
5. **Notification**: Alert stakeholders (e.g., "High-impact change detected").

**Example Pre-Post Rules**:
```json
{
  "pre_rules": [
    { "field": "user.status", "allow": ["active", "suspended"] },
    { "check": "user.id == session.user_id" }
  ],
  "post_rules": [
    { "check": "user.status != 'active' || user.email_verified == true" }
  ]
}
```

---

### **3. Data Model**
#### **Audit Event Schema**
| Field            | Type       | Description                                                                                     |
|------------------|------------|-------------------------------------------------------------------------------------------------|
| `event_id`       | UUID       | Unique identifier for the audit entry.                                                         |
| `entity_type`    | String     | Resource type (e.g., `user`, `order`).                                                          |
| `entity_id`      | String     | Primary key of the affected entity.                                                              |
| `user_id`        | String     | Account performing the action.                                                                  |
| `action`         | Enum       | `CREATE`, `UPDATE`, `DELETE`, `REVOKE`, etc.                                                  |
| `timestamp`      | Timestamp  | UTC time of the event (system-generated).                                                       |
| `metadata`       | JSON       | Context (e.g., `{"reason": "user_requested","ip": "192.168.1.1"}`).                             |
| `changes`        | JSON Patch  | Delta of modified fields (e.g., `{"op": "replace", "path": "/status", "value": "suspended"}`). |
| `validation`     | Object     | Results of pre/post rules.                                                                     |
| `signatures`     | List<Sig>  | Cryptographic proofs (e.g., HSM-signed hashes of the event).                                   |

**Example Event**:
```json
{
  "event_id": "e1234567-89ab-cdef-0123-456789abcdef",
  "entity_type": "user",
  "entity_id": "usr_789",
  "user_id": "admin_123",
  "action": "UPDATE",
  "timestamp": "2023-10-25T14:30:00Z",
  "metadata": {
    "reason": "security_review",
    "ip": "10.0.0.1"
  },
  "changes": [
    { "op": "replace", "path": "/status", "value": "suspended" }
  ],
  "validation": {
    "pre_pass": true,
    "post_pass": true,
    "rules_checked": ["status_authorized", "balance_positive"]
  }
}
```

---

## **Schema Reference**
### **1. Audit Log Table (SQL Example)**
```sql
CREATE TABLE audit_log (
  event_id UUID PRIMARY KEY,
  entity_type VARCHAR(50) NOT NULL,
  entity_id VARCHAR(100) NOT NULL,
  user_id VARCHAR(100),
  action VARCHAR(20) CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'REVOKE')),
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  metadata JSONB,
  changes JSONB NOT NULL,
  validation JSONB,
  signatures BYTEA[]
);
```

### **2. JSON Patch RFC 6902 Compliance**
| Field     | Example Value                                                                 |
|-----------|---------------------------------------------------------------------------------|
| `op`      | `"add"`, `"remove"`, `"replace"`, `"copy"`, `"move"`, `"test"`                   |
| `path`    | `" /user/preferences/notifications"` (JSON Pointer syntax)                       |
| `value`   | Arbitrary JSON/PLAIN value                                                        |
| `from`    | Used in `copy`/`move` operations (source path)                                  |

**Example Patch**:
```json
[
  { "op": "replace", "path": "/user/status", "value": "suspended" },
  { "op": "remove", "path": "/temp/token" }
]
```

---

## **Query Examples**
### **1. Find All Suspensions in the Last 7 Days**
```sql
SELECT *
FROM audit_log
WHERE action = 'UPDATE'
  AND changes->>'$[0].op' = 'replace'
  AND changes->>'$[0].path' LIKE '%/status%'
  AND changes->>'$[0].value' = 'suspended'
  AND timestamp >= NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### **2. Reconstruct a User’s Full History (PostgreSQL)**
```sql
WITH RECURSIVE user_history AS (
  SELECT
    event_id, entity_id, changes,
    CASE changes->>'$[0].op'
      WHEN 'add' THEN PARSE_JSON(changes->>'$[0].value')
      WHEN 'replace' THEN PARSE_JSON(changes->>'$[0].value')
      ELSE NULL END AS new_value,
    1 AS depth
  FROM audit_log
  WHERE entity_type = 'user' AND entity_id = 'usr_789'
  AND action = 'UPDATE'

  UNION ALL

  SELECT
    a.event_id, a.entity_id, a.changes,
    CASE a.changes->>'$[0].op'
      WHEN 'add' THEN PARSE_JSON(a.changes->>'$[0].value')
      ELSE NULL END AS new_value,
    h.depth + 1
  FROM audit_log a
  JOIN user_history h ON a.timestamp > h.timestamp
  WHERE a.entity_type = 'user' AND a.entity_id = 'usr_789'
  AND a.action = 'UPDATE'
)
SELECT
  event_id,
  timestamp,
  new_value,
  LAG(new_value) OVER (ORDER BY timestamp) AS previous_value,
  changes
FROM user_history
ORDER BY timestamp DESC;
```

### **3. Aggregated Statistics (Elasticsearch/Kibana)**
```json
GET /audit_log/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "action": "UPDATE" } },
        { "range": { "timestamp": { "gte": "now-7d" } } }
      ]
    }
  },
  "aggs": {
    "by_user": { "terms": { "field": "user_id" } },
    "by_entity": { "terms": { "field": "entity_type" } },
    "critical_errors": {
      "filter": { "term": { "validation.pre_pass": false } }
    }
  }
}
```

---

## **Implementation Strategies**
| Strategy               | Use Case                                      | Tools/Techniques                          |
|------------------------|-----------------------------------------------|-------------------------------------------|
| **Append-Only Logs**   | Durability, replayability.                    | Kafka, S3, Cassandra’s Time-Series Tables. |
| **Immediate Validation** | Real-time compliance checks.                 | gRPC streaming, Webhooks.                 |
| **Batch Processing**   | Large-scale data migrations.                  | Spark/Flink for log replay.               |
| **Cryptographic Proofs** | Tamper-evidence.                          | Ed25519 signatures, Merkle trees.        |
| **Rule Engine**        | Dynamic validation logic.                     | Drools, OpenPolicyAgent.                  |

---

## **Error Handling**
| Scenario                     | Solution                                                                 |
|------------------------------|--------------------------------------------------------------------------|
| **Validation Failure**       | Reject the change; log `validation.pre_pass: false` with error details. |
| **Log Write Failure**        | Queue the event for retry + fallback to in-memory buffer.               |
| **Entity Not Found**         | Return `404` for `DELETE`/`UPDATE`; log `entity_id` + timestamp.         |
| **Rate Limiting**            | Throttle logs; use probabilistic sampling for high-volume systems.      |

---

## **Best Practices**
1. **Granularity**: Log at the field level, not object level.
2. **Performance**: Partition logs by `entity_type` + timestamp (e.g., Hive/S3).
3. **Retention**: Balance compliance needs (e.g., GDPR 7 years) with cost (e.g., 30-day hot storage).
4. **Security**:
   - Encrypt sensitive fields (e.g., PII) in logs.
   - Restrict access to audit logs via RBAC.
5. **Replay Safety**: Design idempotent operations (e.g., `UPDATE IF EXISTS`).
6. **Testing**: Unit-test validation rules; stress-test log ingestion.

---

## **Related Patterns**
| Pattern                | Relationship to Audit Validation                          | Reference                          |
|------------------------|----------------------------------------------------------|------------------------------------|
| **Command Query         | Audit logs often serve as the "query" for operational    | CQRS                             |
| Responsibility**       |                                          |                                    |
| **Saga Pattern**       | Audit events help track compensating transactions.       | [Saga Pattern Guide](#)            |
| **Immutable Database** | Logs mirror the principle of not allowing updates.       | Time-Series DBs (e.g., InfluxDB)   |
| **Policy as Code**     | Validation rules are defined in declarative configs.        | Open Policy Agent (OPA)           |
| **Distributed Locks**  | Prevent concurrent validations from overwriting logs.     | ZooKeeper, Redis                  |

---

## **Anti-Patterns**
1. **Log Everything**: Avoid bloating logs with trivial changes (e.g., cache hits).
2. **Block on Logging**: Never make validation dependent on log write success.
3. **Silent Failures**: Always log *why* a validation failed (e.g., `user_id: null`).
4. **Manual Audits**: Avoid ad-hoc scripts; automate with scheduled queries.

---
**Note**: For production systems, pair Audit Validation with **Monitoring (e.g., Prometheus)** to track log latency and validation pass rates.