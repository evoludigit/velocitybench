# **[Pattern] Entity Update Frequency Reference Guide**

---

## **1. Overview**
The **Entity Update Frequency** pattern tracks how often specific entities (e.g., documents, records, or database rows) are modified, inserted, or deleted. This pattern is critical for systems requiring auditing, change tracking, cost optimization, or anomaly detection in databases, filesystems, or distributed systems.

Common use cases include:
- **Database optimizations** (e.g., materialized views, caching strategies).
- **Audit logs** (e.g., compliance tracking for financial records).
- **Performance monitoring** (e.g., identifying frequently updated entities).
- **Batch processing** (e.g., syncing changes between systems).

The pattern typically involves storing a **last updated timestamp** or **version counter** alongside the entity, enabling efficient comparison of current vs. previous states.

---

## **2. Core Concepts**
| **Concept**               | **Definition**                                                                 | **Example**                          |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Entity Metadata**       | A lightweight record attached to an entity tracking changes (e.g., `last_modified`). | `{"user_id": 123, "last_update": "2024-01-15T10:00:00"}` |
| **Update Frequency**      | The rate at which an entity is modified (e.g., "updated 5 times in the last 24h"). | `SELECT COUNT(*) FROM logs WHERE entity_id = 1 AND updated_at > NOW() - INTERVAL '1 day'` |
| **Versioning**            | A counter/watermark (e.g., `version_id`) to track sequential updates.       | `v1 → v2 → v3` (e.g., for optimistic concurrency). |
| **Change Detection**      | Logic to compare current vs. previous entity states (e.g., diff algorithms). | `if (current.hash != previous.hash) { log_change(); }` |
| **Time-Based Intervals**  | Buckets for aggregation (e.g., hourly, daily, weekly updates).               | `GROUP BY DATE(updated_at)`          |

---

## **3. Schema Reference**
### **Primary Tables/Columns**
| **Table**         | **Column**               | **Type**       | **Description**                                                                 |
|-------------------|--------------------------|----------------|---------------------------------------------------------------------------------|
| `entities`        | `id`                     | `UUID/PK`      | Unique identifier for the tracked entity.                                       |
|                   | `metadata`               | `JSON`         | Store flexible update metadata (e.g., `{"last_updated": "2024-01-15 10:00"}`). |
| `update_logs`     | `entity_id`              | `UUID/FK`      | References the linked entity.                                                   |
|                   | `timestamp`              | `TIMESTAMP`    | When the entity was updated.                                                    |
|                   | `change_type`            | `ENUM`         | `"insert"`, `"update"`, or `"delete"`.                                         |
|                   | `old_value`              | `JSON`         | Pre-update state (if applicable).                                               |
|                   | `new_value`              | `JSON`         | Post-update state (if applicable).                                             |

### **Optimized Schema (For High Frequency)**
| **Table**         | **Column**               | **Type**       | **Description**                                                                 |
|-------------------|--------------------------|----------------|---------------------------------------------------------------------------------|
| `entities`        | `id`                     | `UUID/PK`      |                                                                                 |
|                   | `version`                | `BIGINT`       | Auto-incrementing counter for versioning.                                       |
|                   | `updated_at`             | `TIMESTAMP`    | Last update timestamp (indexed).                                               |
| `change_events`   | `entity_id`              | `UUID/FK`      |                                                                                 |
|                   | `version`                | `BIGINT/FK`    | Links to the entity’s current version.                                         |
|                   | `diff_hash`              | `VARCHAR(64)`  | SHA-256 hash of the entity’s state (for quick diffs).                          |

---

## **4. Implementation Examples**
### **A. Tracking Updates with Timestamps**
**Query to count updates per entity in the last 7 days:**
```sql
SELECT
    entity_id,
    COUNT(*) AS update_count,
    MAX(timestamp) AS last_updated
FROM update_logs
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY entity_id
ORDER BY update_count DESC;
```

**Query to find entities updated more than X times:**
```sql
SELECT entity_id
FROM update_logs
GROUP BY entity_id
HAVING COUNT(*) > 100  -- Threshold for "frequent updates"
ORDER BY COUNT(*) DESC;
```

### **B. Version-Based Change Detection**
**Store entity versions in a table:**
```sql
CREATE TABLE entity_versions (
    id SERIAL PRIMARY KEY,
    entity_id UUID NOT NULL,
    version BIGINT NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Insert a new version:**
```sql
INSERT INTO entity_versions (entity_id, version, data)
VALUES (
    'abc123',
    COALESCE(
        (SELECT MAX(version) FROM entity_versions WHERE entity_id = 'abc123'),
        0
    ) + 1,
    '{"key": "value"}'
);
```

**Find all versions between two timestamps:**
```sql
SELECT * FROM entity_versions
WHERE entity_id = 'abc123'
  AND created_at BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY version;
```

### **C. Optimistic Concurrency Control**
**Check for conflicts before updating:**
```python
# Pseudocode: Compare current version with expected version
def update_entity(entity_id, new_data, expected_version):
    current_version = db.query("SELECT version FROM entity_versions WHERE entity_id = ?", entity_id)
    if current_version.version != expected_version:
        raise ConflictError("Version mismatch")
    # Proceed with update...
```

---

## **5. Query Examples by Use Case**
### **A. Audit Logging**
**List all changes to a specific entity:**
```sql
SELECT
    timestamp,
    change_type,
    old_value,
    new_value
FROM update_logs
WHERE entity_id = 'user_456'
ORDER BY timestamp DESC;
```

### **B. Cost Optimization (Database)**
**Identify entities updated too frequently for caching:**
```sql
SELECT entity_id, update_count
FROM (
    SELECT entity_id, COUNT(*) AS update_count
    FROM update_logs
    GROUP BY entity_id
) AS stats
WHERE update_count > 1000;  -- Too frequent for cache
```

### **C. Anomaly Detection**
**Detect sudden spikes in updates:**
```sql
WITH hourly_counts AS (
    SELECT
        entity_id,
        DATE_TRUNC('hour', timestamp) AS hour,
        COUNT(*) AS updates
    FROM update_logs
    GROUP BY entity_id, hour
)
SELECT
    entity_id,
    AVG(updates) OVER (PARTITION BY entity_id) AS avg_updates_per_hour,
    updates
FROM hourly_counts
WHERE updates > (SELECT AVG(updates) FROM hourly_counts) * 2;  -- >2x average
```

---

## **6. Performance Considerations**
| **Aspect**            | **Recommendation**                                                                 |
|-----------------------|-----------------------------------------------------------------------------------|
| **Indexing**          | Index `update_logs(entity_id, timestamp)` for fast lookups.                        |
| **Batch Inserts**     | Use `ON CONFLICT (entity_id, timestamp)` for deduplication in PostgreSQL.          |
| **Storage**           | Archive old logs to cold storage (e.g., S3) after retention periods.                |
| **Diff Algorithms**   | For large entities, use incremental merges or hash comparisons.                   |
| **Concurrency**       | Use optimistic locking (version stamps) to avoid race conditions.                |

---

## **7. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                          |
|----------------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Change Data Capture (CDC)]** | Captures database changes in real-time (e.g., Debezium, Kafka Connect).       | Event-driven architectures.               |
| **[Immutable Logs]**             | Stores all changes as immutable entries (e.g., append-only log).              | Audit trails requiring no modifications. |
| **[Materialized Views]**         | Pre-computes aggregated data (e.g., `SELECT COUNT(*) FROM update_logs`).       | Reporting on update frequencies.         |
| **[CQRS]**                       | Separates read (queries) and write (commands) models for scalability.          | High-throughput write-heavy systems.     |
| **[Optimistic Concurrency]**     | Uses version numbers to handle conflicts without locks.                        | Distributed systems with eventual consistency. |

---

## **8. Anti-Patterns to Avoid**
- **Overhead from excessive logging**: Avoid tracking *every* minor change (e.g., typos).
- **Unindexed queries**: Without indexes, frequency analysis becomes slow.
- **No retention policy**: Unbounded logs consume storage and slow queries.
- **Ignoring version conflicts**: Without version checks, updates may overwrite each other.