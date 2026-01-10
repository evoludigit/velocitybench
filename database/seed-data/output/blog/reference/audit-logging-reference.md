# **[Pattern] Audit Logging Patterns – Reference Guide**

---

## **Overview**
The **Audit Logging Patterns** reference guide documents best practices for capturing, storing, and querying immutable records of system activity. This pattern ensures compliance with regulations (e.g., SOC2, HIPAA, GDPR), enables security incident investigations, aids debugging, and supports undo/redo functionality.

Audit logs track:
- **Who** performed an action (user/entity identifier).
- **What** was changed (action type, entity ID).
- **When** the action occurred (timestamps).
- **Before/After state** of affected data (delta snapshots).
- **Context** (IP address, origin system, user agent).

This guide covers core components (schema, middleware, data storage), implementation strategies, and query examples.

---

## **Key Concepts**

### **1. Core Components**
| Component            | Description                                                                                     | Example Structured Data (JSON)                                                                 |
|----------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Audit Trail**      | Immutable table storing all actions with metadata.                                             | ```{ event_id: "abc123", entity_id: "user_456", action: "DELETE", timestamp: "2024-01-20T12:00" }``` |
| **Before/After Snapshots** | Delta records capturing pre/post changes to data.                                        | ```{ field: "email", before: "old@example.com", after: "new@example.com" }```                    |
| **Context Capture**  | Middleware/logging proxy to auto-enrich logs with user/IP/timestamp.                          | ```{ user_id: "789", ip: "192.0.2.1", user_agent: "Browser/1.0" }```                            |

### **2. Design Principles**
- **Immutability**: Audit logs must not be altered post-creation (use append-only storage).
- **Granularity**: Log at the granularity of *business actions* (e.g., "user deleted," not "API call made").
- **Retention**: Align with compliance (e.g., GDPR requires 7 years for personal data).
- **Performance**: Optimize for read-heavy queries (e.g., partition by date).

---

## **Schema Reference**

### **1. Core Audit Trail Table**
```sql
CREATE TABLE audit_logs (
    event_id            UUID PRIMARY KEY,
    entity_id           VARCHAR(255) NOT NULL,  -- Targeted entity (e.g., user_id, order_id)
    entity_type         VARCHAR(50) NOT NULL,    -- "User", "Order", "Account"
    action              VARCHAR(50) NOT NULL,    -- "CREATE", "UPDATE", "DELETE"
    user_id             VARCHAR(255),           -- Actor (nullable if system-generated)
    ip_address          VARCHAR(45),            -- Source IP
    user_agent          VARCHAR(255),           -- Client metadata
    timestamp           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata            JSONB,                  -- Optional: free-form data (e.g., validation errors)
    is_sensitive        BOOLEAN DEFAULT FALSE   -- Flag for PII/PCI data
);
```

### **2. Before/After Snapshots Table**
```sql
CREATE TABLE audit_snapshots (
    snapshot_id         UUID PRIMARY KEY,
    event_id            UUID REFERENCES audit_logs(event_id),
    entity_id           VARCHAR(255) NOT NULL,
    entity_type         VARCHAR(50) NOT NULL,
    changes             JSONB NOT NULL,         -- Array of {field, before, after, type} objects
    checksum            VARCHAR(64)           -- SHA256 hash of original data (for validation)
);
```
**Example `changes` JSON**:
```json
[
    { "field": "email", "before": null, "after": "user@example.com", "type": "string" },
    { "field": "status", "before": "active", "after": "suspended", "type": "enum" }
]
```

### **3. Index Recommendations**
| Table               | Indexes                                                                                     |
|---------------------|---------------------------------------------------------------------------------------------|
| `audit_logs`        | `(entity_id, action, timestamp)` (for time-range queries)                                  |
|                     | `(event_id)` (foreign key lookup)                                                          |
| `audit_snapshots`   | `(event_id)` (foreign key lookup)                                                          |
|                     | `(entity_id, timestamp)` (for historical analysis)                                         |

---

## **Implementation Patterns**

### **1. Middleware-Based Capture**
Capture logs via middleware (e.g., database triggers, API gateways).
**Example (PostgreSQL Trigger)**:
```sql
CREATE OR REPLACE FUNCTION log_user_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert into audit_logs
    INSERT INTO audit_logs (event_id, entity_id, entity_type, action, user_id)
    VALUES (gen_random_uuid(), NEW.user_id, 'User', 'UPDATE', current_user);

    -- Insert into audit_snapshots
    INSERT INTO audit_snapshots (snapshot_id, event_id, entity_id, entity_type, changes, checksum)
    VALUES (
        gen_random_uuid(),
        (SELECT event_id FROM audit_logs ORDER BY timestamp DESC LIMIT 1),
        NEW.user_id,
        'User',
        jsonb_build_object('changes', ARRAY[
            jsonb_build_object('field', 'email', 'before', OLD.email, 'after', NEW.email, 'type', 'string')
        ]),
        digest(NEW::text, 'sha256')
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_user_update
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION log_user_update();
```

### **2. Decorator Pattern for Services**
Wrap service methods to auto-log actions:
```typescript
// Node.js example
class UserService {
    updateEmail(userId: string, newEmail: string) {
        const auditLog = {
            eventId: uuidv4(),
            entityId: userId,
            entityType: "User",
            action: "UPDATE",
            userId: this.currentUserId,
            timestamp: new Date(),
            metadata: { field: "email", before: oldEmail, after: newEmail }
        };

        // Log to database/queue
        this.auditLogger.log(auditLog);

        // Update user
        await this.userRepository.update(userId, { email: newEmail });
    }
}
```

### **3. Change Data Capture (CDC)**
For databases, use CDC tools (e.g., Debezium, PostgreSQL logical replication) to stream changes to a log table.

---

## **Query Examples**

### **1. Find All Actions on an Entity**
```sql
-- Basic query: Get all audit logs for a user
SELECT *
FROM audit_logs
WHERE entity_id = 'user_123'
ORDER BY timestamp DESC
LIMIT 100;
```

### **2. Reconstruct Entity State at a Point in Time**
```sql
-- Get the state of a user at a specific timestamp
WITH recent_snapshot AS (
    SELECT changes
    FROM audit_snapshots
    WHERE entity_id = 'user_123'
    ORDER BY timestamp DESC
    LIMIT 1
)
SELECT
    (SELECT jsonb_agg(
        jsonb_build_object(
            k, COALESCE(
                (SELECT value.from_ AS before FROM jsonb_populated_array(elements->k) AS value),
                NULL
            )
        )
    FROM jsonb_object_keys(recent_snapshot.changes)
    CROSS JOIN LATERAL jsonb_array_elements(recent_snapshot.changes->'changes') AS elements)->'0' AS before_state;
```

### **3. Detect Unauthorized Actions**
```sql
-- Flag suspicious actions (e.g., admin deleting user without context)
SELECT *
FROM audit_logs
WHERE user_id != 'admin_456'
AND action = 'DELETE'
AND entity_type = 'User';
```

### **4. Generate Compliance Reports**
```sql
-- GDPR: List all personal data changes for a user
SELECT
    a.*,
    s.changes->>'email' AS email_change
FROM audit_logs a
JOIN audit_snapshots s ON a.event_id = s.event_id
WHERE a.entity_id = 'user_789'
AND a.is_sensitive = TRUE;
```

---

## **Performance Considerations**
| Strategy               | Use Case                                      | Trade-offs                                  |
|------------------------|-----------------------------------------------|---------------------------------------------|
| **Sampling**           | High-volume systems (e.g., 1000x/month).     | May miss critical events.                   |
| **Partitioning**       | Time-based queries (e.g., `WHERE timestamp > '2024-01-01'`). | Requires re-partitioning for long retention. |
| **Archival Storage**   | Cold data (>30 days).                         | Higher query latency for old data.          |
| **Async Logs**         | Decouple logging from primary operations.     | Risk of data loss if async fails.           |

---

## **Related Patterns**
1. **[Event Sourcing]** – Store state transitions as a sequence of events (audit logs are a subset).
2. **[Immutable Data Stores]** – Use append-only storage (e.g., DynamoDB Streams) for logs.
3. **[Security Monitoring]** – Correlate audit logs with intrusion detection systems (e.g., SIEM tools).
4. **[Undo/Redo]** – Replay audit logs to revert states (e.g., "ROLLBACK TO snapshot_id=abc123").
5. **[Data Lineage]** – Track how data changes across systems (extend audit logs with ETL metadata).

---

## **Anti-Patterns to Avoid**
- **Logging Everything**: Over-logging inflates storage costs and slows queries. Focus on *business-critical* actions.
- **Mutable Logs**: Avoid updating audit logs (e.g., correcting timestamps). Use `is_deleted` flag instead.
- **Ignoring Context**: Omitting IP/user_agent makes logs useless for investigations.
- **No Retention Policy**: Risk of compliance violations or storage bloat. Automate purging old logs.

---
## **Tools & Libraries**
| Tool/Library          | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| **Databases**         | PostgreSQL (JSONB), MongoDB (change streams), Snowflake (audit log tables). |
| **Open Source**       | [Elastic Auditbeat](https://www.elastic.co/beats/auditbeat) (SIEM integration). |
| **Commercial**        | AWS CloudTrail, Azure Monitor, Datadog Audit Logs.                      |
| **Frameworks**        | Spring Audit, Django Auditing, Laravel Sanctum.                        |

---
**Last Updated**: [Insert Date]
**Version**: 1.0