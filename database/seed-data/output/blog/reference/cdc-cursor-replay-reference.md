# **[Pattern] CDC (Change Data Capture) Cursor-Based Replay Reference Guide**

---

## **Overview**
The **Cursor-Based Replay** pattern enables replaying changes from a database or data store into a target system (e.g., another database, application, or analytics engine) using **Change Data Capture (CDC)**. This pattern is ideal for **real-time data synchronization, auditing, and replaying historical changes** from a specific position (e.g., transaction ID, timestamp, or custom cursor).

Unlike traditional batch processing, the cursor-based approach ensures **consistent, incremental, and non-overlapping replay** of events by tracking a **logical position marker** (cursor) in the source system. This is particularly useful for:
- **Disaster recovery** (rebuilding a database from CDC logs)
- **Data warehouse synchronization** (incremental loading)
- **Audit trails** (replaying past changes for compliance)
- **Event-driven architectures** (processing state changes as they occur)

The pattern assumes the source system supports CDC (e.g., PostgreSQL logical decoding, Debezium, MySQL binlog, or Kafka Connect).

---

## **Key Concepts & Implementation Details**
### **1. Core Components**
| Component          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Source System**  | Database or data store emitting CDC events (e.g., PostgreSQL, MySQL).      |
| **Sink System**    | Target system receiving replayed changes (e.g., another database, Kafka). |
| **Cursor**         | A positional marker (e.g., LSN, transaction ID, or custom offset) indicating where replay should resume. |
| **CDC Pipeline**   | Infrastructure to capture, transmit, and process changes (e.g., Debezium, Kafka, or custom logic). |
| **Replay Engine**  | Logic to apply changes to the sink based on the cursor position.            |

### **2. Cursor Types**
| Cursor Type       | Example (PostgreSQL) | Description                                                                 |
|-------------------|----------------------|-----------------------------------------------------------------------------|
| **Log Sequence Number (LSN)** | `pg_logical_slot_get_changepos()` | Low-level binary position in WAL (Write-Ahead Log).                         |
| **Transaction ID** | `txid_current()`     | High-level ID of the transaction generating the change.                     |
| **Timestamp**     | `now()`              | Human-readable time (less precise for replay).                             |
| **Custom Offset** | Application-defined | E.g., sequence number in Kafka or a unique event ID.                        |

### **3. How It Works**
1. **Capture Changes**: The source system emits CDC events (e.g., INSERT/UPDATE/DELETE) and assigns a cursor value.
2. **Persist Cursor**: Store the cursor in a metadata table or external system (e.g., Kafka offset) to track progress.
3. **Replay Logic**:
   - Load the last recorded cursor.
   - Fetch changes from the source **after** that cursor.
   - Apply changes to the sink.
   - Update the cursor to the last processed position.
4. **Resilience**: If replay fails, restart from the last known cursor without reprocessing old data.

### **4. Fault Tolerance & Idempotency**
- **Idempotent Operations**: Ensure replaying the same event multiple times doesn’t corrupt data (e.g., ignore duplicates).
- **Checkpointing**: Periodically save the cursor to survive crashes (e.g., in a database table or file).
- **At-Least-Once Delivery**: Process each event at least once (duplicates are handled by idempotency).

### **5. Performance Considerations**
| Factor               | Recommendation                                                                 |
|----------------------|-------------------------------------------------------------------------------|
| **Batch Size**       | Process changes in batches (e.g., 1000 rows) to balance latency and throughput. |
| **Parallelism**      | Use multiple consumers if the sink supports parallel writes (e.g., Kafka partitions). |
| **Cursor Storage**   | Store cursors in a durable system (e.g., database) to recover from failures.  |
| **Network Overhead** | Compress CDC payloads if transmitting over high-latency links.                 |

---

## **Schema Reference**
### **1. Metadata Table for Cursor Tracking**
```sql
CREATE TABLE cursor_metadata (
    system_name VARCHAR(50) PRIMARY KEY,
    cursor_value BYTEA NOT NULL,   -- Stores LSN, transaction ID, etc.
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED'))
);
```
- **Purpose**: Track the current replay position per system.
- **Example Cursor Values**:
  - `cursor_value = E'\x00000000000000000000000000000001'` (PostgreSQL LSN in hex).

### **2. CDC Event Schema (Example for PostgreSQL)**
Debezium or logical decoding typically emits events like this:
```json
{
  "before": null,       // For INSERTs; contains old data for UPDATEs/DELETEs.
  "after": {           // New data (always present for INSERT/UPDATE).
    "id": 123,
    "name": "example"
  },
  "source": {
    "cdc": {
      "cursor": "0/1690A2F0",  // Example LSN cursor
      "lsn": "0/1690A2F0"
    }
  },
  "op": "c"              // Operation: "c"=create, "u"=update, "d"=delete
}
```
- **Critical Fields**: `source.cdc.cursor` (used to resume replay).

---

## **Query Examples**
### **1. Start a New Replay Session (PostgreSQL)**
```sql
-- Initialize a logical decoding slot (if using PostgreSQL)
SELECT pg_create_logical_replication_slot('replay_slot', 'pgoutput');

-- Enable CDC for a table (if not using Debezium)
ALTER TABLE users REPLICA IDENTITY FULL;
```

### **2. Fetch Changes Since Last Cursor (PostgreSQL)**
```sql
-- Using logical decoding (requires pgoutput plugin)
SELECT *
FROM pg_logical_slot_get_changes(
    'replay_slot',
    NULL,                -- Start position (NULL = from beginning)
    'include-xids',      -- Include transaction IDs
    'output-plugin-args:include-xids'
)
WHERE transaction_id > :last_txn_id;  -- Filter based on cursor
```

### **3. Apply Changes to Sink (Pseudocode)**
```python
def replay_changes(last_cursor):
    while True:
        changes = fetch_changes_since(last_cursor)
        if not changes:
            break  # No more changes

        for change in changes:
            apply_to_sink(change)  # INSERT/UPDATE/DELETE in sink
            last_cursor = change.source.cdc.cursor  # Update cursor

        save_cursor_to_metadata('users_system', last_cursor)  # Persist progress
```

### **4. Resume from Last Cursor (SQL)**
```sql
-- Get the last known cursor
SELECT cursor_value FROM cursor_metadata WHERE system_name = 'users_system';

-- Replay from that position (pseudocode)
REPEAT
    FETCH changes FROM source WHERE cursor > last_cursor;
    APPLY changes TO sink;
    UPDATE last_cursor TO current_cursor;
UN Til NO MORE CHANGES;
```

### **5. Handle Duplicate Events (Idempotency)**
```sql
-- Ensure no duplicates in sink (example for PostgreSQL)
INSERT INTO sink_users (id, name)
SELECT u.id, u.name
FROM users u
WHERE u.id NOT IN (SELECT id FROM sink_users)
  AND u.transaction_id > :last_txn_id;
```

---

## **Related Patterns**
| Pattern                        | Description                                                                 | When to Use                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Debezium CDC Pipeline**      | Framework for capturing and transmitting CDC events to Kafka.              | When using Kafka as a message broker for replay.                            |
| **Transactional Outbox Pattern** | Offloads CDC events to a queue/table for eventual processing.              | When the source system lacks native CDC or needs decoupled processing.     |
| **Materialized View**          | Pre-computes and updates views from CDC data.                              | For read-optimized replicas or analytics.                                   |
| **Event Sourcing**             | Stores state changes as immutable events (similar to CDC but application-focused). | When modeling state changes as a sequence of events.                        |
| **Batch Processing**           | Processes CDC data in bulk (e.g., nightly jobs).                           | When low latency isn’t required and throughput is prioritized.              |

---

## **Best Practices**
1. **Use Transaction IDs or LSNs**: More reliable than timestamps for replay.
2. **Validate Replay Integrity**: Periodically check for gaps or duplicates.
3. **Monitor Replay Lag**: Track the time between capturing and replaying changes.
4. **Handle Schema Changes**: Ensure the sink schema evolves alongside the source.
5. **Test Failover**: Simulate pipeline failures to verify cursor-based recovery.

---
## **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│  PostgreSQL │───▶│ Debezium    │───▶│   Kafka        │───▶│ Sink DB    │
│  (Source)   │    │ (Capture)   │    │ (Buffer)       │    │ (Target)   │
└─────────────┘    └─────────────┘    └─────────────────┘    └─────────────┘
         ^                                       ▲
         │                                       │
         └───────────────────────────────┬───────┘
                                          │
                                      ┌─────────────┐
                                      │ Cursor      │
                                      │ Metadata    │
                                      └─────────────┘
```
- **Cursor Metadata** is updated after processing each Kafka partition.