**[Pattern] CDC Idempotent Processing Reference Guide**

---

### **Overview**
Change Data Capture (CDC) streams can contain duplicate events due to retries, network issues, or downstream delays. The **Idempotent Processing** pattern ensures that reprocessing the same event produces the same outcome—avoiding partial updates, race conditions, or resource contention. This guide covers how to implement idempotency in CDC workflows, including key concepts, schema design, query examples, and related patterns.

---

### **Implementation Details**

#### **Key Concepts**
1. **Idempotency Key**
   - A unique identifier (e.g., `event_id`, `source_timestamp_+_source_sequence`) assigned to each CDC event.
   - Ensures the same event is treated as a single operation, regardless of duplicates.

2. **Idempotency Storage**
   - A durable store (e.g., database table, Redis) tracks processed event keys.
   - Example schema below.

3. **Retry Handling**
   - Skip processing if the key exists (no-op).
   - Log duplicates for auditing (optional).

4. **Event Schema Validation**
   - Verify CDC payload integrity (e.g., schema checksum, payload signature) before processing.

---

### **Schema Reference**

#### **1. Idempotency Tracking Table**
Stores processed event keys to avoid reprocessing.

| Column          | Type         | Description                                                                 |
|-----------------|--------------|-----------------------------------------------------------------------------|
| `idempotency_key` | VARCHAR(255) | Composite key (e.g., `event_id + sourceTimestamp + sourceSequence`).        |
| `processed_at`    | TIMESTAMP    | When the event was last processed (UTC).                                   |
| `schema_version` | INTEGER      | CDC payload schema version for validation.                                 |
| `source_system`   | VARCHAR(50)  | Source system name (e.g., `kafka`, `debezium`).                             |

**Example Key Format**:
`<source_system>:<event_id>:<source_timestamp_ms>:<source_sequence>`

---

#### **2. CDC Event Schema (Example)**
Payload schema for CDC events (adapt to your source).

| Column          | Type            | Description                                                                 |
|-----------------|-----------------|-----------------------------------------------------------------------------|
| `event_id`      | UUID            | Unique identifier (source system assigned).                              |
| `source`        | JSON            | Raw event data from CDC (e.g., `{ "table": "users", "op": "insert", "data": {...} }` ). |
| `source_timestamp` | BIGINT        | Unix timestamp (milliseconds) from source.                                  |
| `source_sequence` | BIGINT          | Sequential number per source (for ordering).                               |

---

### **Query Examples**

#### **1. Check if an Event was Processed**
```sql
SELECT COUNT(*)
FROM idempotency_tracking
WHERE idempotency_key = '<key>'
  AND processed_at >= NOW() - INTERVAL '24h' -- Ensure recent checks don't miss retries.
```

#### **2. Insert Unprocessed Events (Idempotent Upsert)**
```sql
INSERT INTO idempotency_tracking (
  idempotency_key,
  processed_at,
  schema_version,
  source_system
)
VALUES (
  '<key>',
  NOW(),
  '<schema_version>',
  '<source_system>'
)
ON CONFLICT (idempotency_key)
DO UPDATE SET
  processed_at = EXCLUDED.processed_at,
  schema_version = EXCLUDED.schema_version;
```

#### **3. Query CDC Events for New Processing**
```sql
SELECT *
FROM cdc_events
WHERE NOT EXISTS (
  SELECT 1 FROM idempotency_tracking
  WHERE idempotency_key =
    CONCAT('<source_system>', ':', event_id, ':', source_timestamp, ':', source_sequence)
);
```

#### **4. Audit Duplicate Events**
```sql
SELECT COUNT(*) as duplicate_count, source_system
FROM idempotency_tracking t
JOIN (
  SELECT idempotency_key, processed_at
  FROM idempotency_tracking
  GROUP BY idempotency_key
  HAVING COUNT(*) > 1
) dup ON t.idempotency_key = dup.idempotency_key
GROUP BY source_system;
```

---

### **Implementation Best Practices**

1. **Key Design**
   - Use a **composite key** combining `source_system`, `event_id`, `timestamp`, and `sequence` to minimize collisions.
   - Example: `<source>:<event_id>:<ts_ms>:<seq>`.

2. **Performance**
   - Index the `idempotency_key` column in the tracking table for fast lookups.
   - Consider partitioning the table by `source_system` or date ranges.

3. **Schema Validation**
   - Store the **schema version** in the tracking table to validate payloads against expected formats.

4. **Retry Logic**
   - Implement exponential backoff for retries of failed events (outside the idempotency scope).

5. **Event TTL**
   - Optionally, add a `TTL` column to expire old keys (e.g., after 30 days) to reduce storage overhead.

---

### **Error Handling**
| Scenario               | Action                                                                 |
|------------------------|------------------------------------------------------------------------|
| Duplicate key found    | Log warning, skip processing.                                         |
| Schema mismatch        | Reject event with `schema_version` mismatch.                         |
| Tracking table failure | Fall back to a local cache (short-term) or fail fast.                 |
| Payload validation fail| Reject or reprocess with retries (handle transient errors).          |

---

### **Related Patterns**

1. **Exactly-Once Processing (E1EP)**
   - Combines CDC idempotency with transactional guarantees at the consumer (e.g., Kafka transactions).
   - *Use case*: Critical financial transactions requiring atomicity.

2. **Dead Letter Queue (DLQ)**
   - Routes failed events to a queue for manual review after retries are exhausted.
   - *Use case*: Debugging stuck CDC events.

3. **Schema Registry**
   - Centralized storage for CDC payload schemas to ensure versioning and compatibility.
   - *Use case*: Multi-team environments with evolving schemas.

4. **Event Sourcing**
   - Stores CDC events as immutable logs for replayability.
   - *Use case*: Auditing or rebuilding system state from scratch.

5. **Compensating Transactions**
   - Rolls back side effects of duplicated events (e.g., database updates).
   - *Use case*: Stateful CDC processing (rare, but required for strong consistency).

---

### **Example Workflow**
1. **CDC Producer** emits events (e.g., Kafka topic `users.changes`).
2. **Consumer** reads events and checks the `idempotency_key` in the tracking table.
3. If the key doesn’t exist:
   - Process the event (e.g., update a database).
   - Insert the key into `idempotency_tracking`.
4. If the key exists:
   - Log a duplicate (optional).
   - Skip processing or retry later (if transient).

---
**Note**: Adapt the schema and queries to your database (e.g., PostgreSQL, MongoDB) or key-value store (Redis). For high-volume systems, consider partitioning the tracking table.