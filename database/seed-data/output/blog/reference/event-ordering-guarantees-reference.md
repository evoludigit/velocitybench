# **[Pattern] Event Ordering Guarantees – Reference Guide**
*Ensuring Deterministic Replay and Cross-Entity Consistency in FraiseQL CDC*

---

## **1. Overview**
FraiseQL’s Change Data Capture (CDC) system provides **event ordering guarantees** to ensure deterministic replay, handle out-of-order events, and maintain consistency across distributed entities. By embedding **sequence numbers**, **timestamps**, and **causal metadata** into CDC events, FraiseQL enables reliable event processing even in high-latency or partitioned systems.

Key use cases:
- **Deterministic replay**: Reapply CDC logs to restore exact state changes.
- **Fault tolerance**: Recover from failures without data duplication or loss.
- **Consistent transactions**: Guarantee cross-entity causality (e.g., across microservices).

---

## **2. Schema Reference**
All CDC events include the following ordering metadata. Fields marked with `(*)` are required by FraiseQL.

| Field               | Type         | Description                                                                                                                                                                                                                                                                 |
|---------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **event_id**        | UUID         | Unique identifier for the event.                                                                                                                                                                                                                                    |
| **sequence_number***| uint64       | Monotonically increasing counter per **entity/table** (globally unique within a tenant). Determines **logical order** for replay.                                                                                                                   |
| **timestamp***      | RFC3339      | Server-side time (ISO 8601) when the event was captured. Used for **approximate ordering** alongside sequence numbers.                                                                                                                               |
| **causality_tag***  | string       | UUID-based identifier for **transactional causality**. Ensures events from the same transaction appear together (e.g., `txn_<transaction_id>`).                                                                                                |
| **source_timestamp**| RFC3339      | Optional: Timestamp from the source system (useful for reconciliation).                                                                                                                                                                                 |
| **partition_key**   | string       | Key identifying the **shard/partition** the event belongs to (for parallel processing).                                                                                                                                                              |
| **entity_type**     | string       | Schema name (e.g., `users`, `orders`). Used to group related events.                                                                                                                                                                                      |
| **entity_id**       | string       | Primary key of the affected entity.                                                                                                                                                                                                                         |

**Example Paylod Structure:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "sequence_number": 123456789,
  "timestamp": "2024-05-20T14:30:45.123Z",
  "causality_tag": "txn_abc123-xyz",
  "source_timestamp": "2024-05-20T14:30:44.987Z",
  "partition_key": "users#shard1",
  "entity_type": "users",
  "entity_id": "user_42",
  "payload": { "action": "update", "changes": { "name": "Alice" } }
}
```

---

## **3. Key Characteristics**
### **A. Sequence Number Semantics**
- **Global per-entity**: For a table `users`, `sequence_number` increments strictly per row modification (insert/update/delete).
- **Deterministic replay**: Events with lower `sequence_number` must be processed first.
- **Gaps allowed**: Missing numbers indicate retries or soft deletes (handled via `source_timestamp` reconciliation).

### **B. Causal Ordering**
- **Transactions**: Events tagged with the same `causality_tag` (e.g., `txn_<id>`) are **atomically grouped**.
- **Cross-service consistency**: Use `causality_tag` to link events across microservices (e.g., `order_<id>` → `payment_<id>`).

### **C. Timestamp Handling**
- **Primary order**: `sequence_number` takes precedence over `timestamp` for strict ordering.
- **Approximate clusters**: Events with similar `timestamp` ranges can be batched (e.g., for performance).

---

## **4. Query Examples**
### **A. Filter Events by Ordering Metadata**
```sql
-- Get all CDC events for 'users' entity in order
SELECT *
FROM cdc_events
WHERE entity_type = 'users'
ORDER BY sequence_number ASC;
```

### **B. Replay Events Deterministically**
```sql
-- Replay from sequence_number 100000, skipping gaps if needed
SELECT *
FROM cdc_events
WHERE entity_type = 'users'
  AND sequence_number >= 100000
ORDER BY sequence_number ASC;
```

### **C. Find Causal Dependencies**
```sql
-- Find all events related to a transaction (txn_abc123-xyz)
SELECT *
FROM cdc_events
WHERE causality_tag = 'txn_abc123-xyz';
```

### **D. Reconcile with Source Timestamps**
```sql
-- Handle out-of-order events by comparing source_timestamp
WITH ordered_events AS (
  SELECT
    *,
    LAG(source_timestamp) OVER (PARTITION BY entity_type, entity_id ORDER BY sequence_number) AS prev_time
  FROM cdc_events
)
SELECT *
FROM ordered_events
WHERE source_timestamp > prev_time;  -- Deduplicate or validate
```

### **E. Parallel Processing with Partition Keys**
```sql
-- Process events in parallel by partition_key
SELECT *
FROM cdc_events
WHERE partition_key = 'users#shard2'
ORDER BY sequence_number ASC;
```

---

## **5. Handling Edge Cases**
| Scenario                     | Solution                                                                                                                                                                                                 |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Gap in sequence numbers**  | Assume retries; use `source_timestamp` to validate logical order.                                                                                                                              |
| **Duplicate events**         | Deduplicate via `(entity_type, entity_id, sequence_number)`.                                                                                                                                    |
| **Late-arriving events**    | Buffer and reprocess using `sequence_number` (avoid strict timestamp-based ordering).                                                                                                     |
| **Cross-service causality**  | Use `causality_tag` to link events (e.g., `order_123` → `inventory_123`).                                                                                                                     |

---

## **6. Performance Considerations**
- **Indexing**: Add indexes on `(entity_type, entity_id, sequence_number)`, `(causality_tag)`, and `(partition_key, sequence_number)` for fast queries.
- **Batch processing**: Group events by `partition_key` to parallelize workloads.
- **Compression**: For large logs, consider compressing payloads while preserving metadata.

---

## **7. Related Patterns**
1. **Idempotent Operations**
   - Ensure replay safety by designing operations to handle duplicates (e.g., `UPSERT` for updates).
   - *Relevant Fields*: `entity_id`, `sequence_number` (avoid reprocessing).

2. **Transactional Outbox Pattern**
   - Bundle related events under a `causality_tag` to emulate ACID transactions.
   - *Use Case*: Linking `orders` and `payments` in a distributed system.

3. **Event Sourcing**
   - Store CDC events as immutable append-only logs for auditability.
   - *Synergy*: FraiseQL’s ordering guarantees align with event sourcing principles.

4. **Dead Letter Queue (DLQ)**
   - Route failed events to a DLQ for manual review, tagged with `causality_tag` for tracing.
   - *Query Example*:
     ```sql
     SELECT * FROM dlq_events
     WHERE causality_tag IN (SELECT causality_tag FROM failed_events);
     ```

5. **Materialized Views**
   - Pre-compute aggregations from CDC events to speed up analytics.
   - *Constraint*: Ensure views are updated atomically with `sequence_number`-based triggers.

---

## **8. Best Practices**
- **Monotonic Writes**: Ensure `sequence_number` increments without gaps (use database sequences or UUIDs + counters).
- **Clock Sync**: Align server clocks to minimize `timestamp` discrepancies (NTP recommended).
- **Audit Trails**: Log `causality_tag` in application logs for debugging cross-service flows.
- **Backpressure**: Throttle consumers if `sequence_number` lag exceeds tolerance thresholds.

---
**Last Updated**: [Insert Date]
**Version**: 1.2