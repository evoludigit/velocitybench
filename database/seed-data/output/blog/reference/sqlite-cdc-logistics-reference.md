# **[Pattern] SQLite CDC Logistics Reference Guide**

---

## **Overview**
This guide describes the **SQLite CDC Logistics (Change Data Capture) Pattern**, a lightweight mechanism for tracking incremental schema and data changes in SQLite databases. Unlike traditional CDC solutions (e.g., PostgreSQL logical decoding), this pattern leverages SQLite’s built-in features—**triggers**, **journal mode**, and **WAL (Write-Ahead Logging)**—to efficiently capture, replay, and process changes for analytics, replication, or auditing.

**Key Use Cases:**
- Real-time analytics on database changes.
- Database replication with minimal overhead.
- Audit trails and compliance tracking.
- Event sourcing for application state management.

This pattern is **SQLite-specific** and does not rely on external extensions (e.g., `sqlite_cdc`). It prioritizes **simplicity** and **performance** while ensuring consistency.

---
## **Key Concepts**

### **1. Core Components**
| Component               | Description                                                                 | SQLite Feature Leveraged          |
|-------------------------|-----------------------------------------------------------------------------|-----------------------------------|
| **Trigger Log Table**   | Stores metadata (e.g., `table_name`, `type`, `timestamp`) for each change. | `CREATE TRIGGER` + `INSERT` into a log table. |
| **WAL Mode**            | Enables atomic journaling for concurrent reads/writes.                     | `PRAGMA journal_mode=WAL;`        |
| **Change Tracking**     | Captures `INSERT`, `UPDATE`, `DELETE` operations via triggers.              | `BEFORE`/`AFTER` triggers.       |
| **Replay Mechanism**    | Reapplies logged changes to a target database (e.g., for replication).     | Batch processing of log entries.  |

### **2. Assumptions**
- SQLite ≥ **3.35.0** (required for WAL mode stability).
- **No concurrent writes** to the same table (use WAL for high concurrency).
- Log table schema is **fixed** (avoids schema migrations during CDC).

---
## **Schema Reference**

### **1. CDC Log Table Schema**
Stores metadata for each change operation. Example:

| Column            | Type         | Nullable | Description                                                                 |
|-------------------|--------------|----------|-----------------------------------------------------------------------------|
| `log_id`          | INTEGER      | NO       | Auto-incrementing primary key.                                             |
| `table_name`      | TEXT         | NO       | Name of the affected table.                                                |
| `type`            | TEXT         | NO       | Operation type: `'INSERT'`, `'UPDATE'`, `'DELETE'`.                        |
| `row_id`          | INTEGER      | YES      | Primary key of the affected row (for `UPDATE`/`DELETE`).                   |
| `old_data`        | JSON         | YES      | Serialized row data **before** the change (for `UPDATE`/`DELETE`).        |
| `new_data`        | JSON         | YES      | Serialized row data **after** the change (for `INSERT`/`UPDATE`).        |
| `timestamp`       | DATETIME     | NO       | When the change was logged.                                                |
| `transaction_id`  | TEXT         | YES      | Optional: Links related changes (e.g., multi-row updates).                 |

**Note:**
- Use `JSON` serialization (e.g., `INSTEAD OF TRIGGER`) to store row data.
- For large tables, consider partitioning the log table by `table_name` or `timestamp`.

---

### **2. Trigger Schema (Example)**
Each tracked table requires **two triggers**:
1. **`BEFORE` trigger**: Logs `old_data` for `UPDATE`/`DELETE`.
2. **`AFTER` trigger**: Logs `new_data` for `INSERT`/`UPDATE`.

**Example Trigger for `users` Table:**
```sql
-- Log old_data for UPDATE/DELETE
CREATE TRIGGER log_user_delete_before
AFTER DELETE ON users
BEGIN
    INSERT INTO cdc_log (table_name, type, old_data, row_id, timestamp)
    VALUES ('users', 'DELETE', json_object('id', OLD.id, 'name', OLD.name), OLD.id, datetime('now'));
END;

-- Log new_data for INSERT/UPDATE
CREATE TRIGGER log_user_after
AFTER INSERT OR UPDATE ON users
BEGIN
    INSERT INTO cdc_log (table_name, type, new_data, row_id, timestamp)
    VALUES (
        'users',
        CASE WHEN TYPE OF (NEW.id) = 'NULL' THEN 'INSERT' ELSE 'UPDATE' END,
        json_object('id', NEW.id, 'name', NEW.name),
        NEW.id,
        datetime('now')
    );
END;
```

---
## **Query Examples**

### **1. Replay Changes to a Target Database**
Reapply logged changes to replicate data (e.g., to a staging table):

```sql
-- Example: Replay all INSERTs to a staging table
INSERT INTO users_staging (id, name)
SELECT
    json_extract(new_data, '$.id'),
    json_extract(new_data, '$.name')
FROM cdc_log
WHERE type = 'INSERT' AND table_name = 'users'
ORDER BY timestamp;
```

**Handling Updates/Deletes:**
```sql
-- Delete from staging first (for updates/deletes)
DELETE FROM users_staging WHERE id IN (
    SELECT row_id FROM cdc_log WHERE type = 'DELETE' AND table_name = 'users'
);

-- Upsert new/updated data
INSERT OR REPLACE INTO users_staging (id, name)
SELECT
    json_extract(new_data, '$.id'),
    json_extract(new_data, '$.name')
FROM cdc_log
WHERE type = 'INSERT' OR type = 'UPDATE'
  AND table_name = 'users'
ORDER BY timestamp;
```

---

### **2. Filter Changes by Time Window**
Capture changes since a specific timestamp (e.g., for incremental backups):

```sql
-- Get all changes after a cutoff (e.g., 1 hour ago)
SELECT * FROM cdc_log
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp;
```

---

### **3. Track Transactions with `transaction_id`**
Group changes from a transaction (e.g., for atomic replays):

```sql
-- Enable transaction tracking (add to triggers)
-- Example: Generate a UUID for each transaction
PRAGMA busy_timeout = 5000; -- Prevent deadlocks
BEGIN TRANSACTION;
INSERT INTO cdc_log (...) VALUES (...);
-- Inside the same transaction, set transaction_id
UPDATE cdc_log SET transaction_id = 'txn_123' WHERE log_id = ...;
COMMIT;
```

**Replay by Transaction:**
```sql
-- Replay all changes in transaction 'txn_123'
INSERT INTO target_table (id, name)
SELECT ... FROM cdc_log
WHERE transaction_id = 'txn_123' ORDER BY timestamp;
```

---

### **4. Audit Trail with `SELECT` Triggers**
Log **reads** (if needed) by adding a `BEFORE SELECT` trigger:

```sql
CREATE TRIGGER log_user_read
BEFORE SELECT ON users
BEGIN
    -- Log reader identity (if using auth)
    INSERT INTO audit_log (table_name, action, user_id, timestamp)
    VALUES ('users', 'SELECT', current_user, datetime('now'));
END;
```

---
## **Setup & Optimization**

### **1. Enable WAL Mode**
```sql
PRAGMA journal_mode = WAL; -- Required for concurrent CDC.
PRAGMA synchronous = NORMAL; -- Balance durability/performance.
```

### **2. Disable Foreign Key Checks Temporarily**
During replay, disable constraints if needed:
```sql
PRAGMA foreign_keys = OFF;
-- Replay changes ...
PRAGMA foreign_keys = ON;
```

### **3. Batch Processing for Large Logs**
Process logs in batches to avoid locking:
```sql
-- Process 1000 rows at a time
WITH batch AS (
    SELECT * FROM cdc_log
    ORDER BY timestamp
    LIMIT 1000 OFFSET 0
)
INSERT INTO target_table (...) SELECT ... FROM batch;
```

---
## **Relationships to Other Patterns**

| Pattern/Concept          | Relationship to SQLite CDC Logistics                          | When to Use Together                                  |
|--------------------------|---------------------------------------------------------------|-------------------------------------------------------|
| **Materialized Views**   | CDC can populate materialized views incrementally.           | Real-time analytics on aggregated data.               |
| **Database Replication** | CDC logs can feed into a replica (e.g., via triggers).       | High availability or read scaling.                    |
| **Event Sourcing**       | Logs act as an event store for application state.            | Audit trail or replayable state.                      |
| **Partitioning**         | Split log table by `table_name` or `timestamp` for scalability. | Large-scale CDC with many tables.                    |
| **View-Based CDC**       | Views can filter CDC logs (e.g., `WHERE type = 'INSERT'`).   | Simplify replay logic for specific use cases.        |

---
## **Limitations & Considerations**

### **1. Performance Overhead**
- **Triggers add latency**: Benchmark with your workload (e.g., `EXPLAIN QUERY PLAN`).
- **Log bloat**: Large logs increase disk I/O. Consider archiving old entries.

### **2. No Native Deduplication**
- The log may contain redundant entries (e.g., multiple rows updated in a transaction).
- **Workaround**: Add a `checksum` column to detect duplicates.

### **3. Schema Migrations**
- **Breaking Change**: Altering the log table schema requires replaying historical logs.
- **Mitigation**: Freeze CDC during schema changes or use a separate migration log.

### **4. No Built-in Compaction**
- Unlike PostgreSQL’s logical decoding, SQLite CDC does not automatically clean up logs.
- **Solution**: Regularly vacuum the log table:
  ```sql
  VACUUM cdc_log; -- Reclaims space after deletions.
  ```

---
## **Example Workflow: End-to-End Replication**

### **Step 1: Source Database Setup**
1. Enable WAL mode.
2. Create `cdc_log` table and triggers for target tables.
3. Start logging changes.

### **Step 2: Replicate to Target**
1. **Initial Load**: Sync full table data:
   ```sql
   INSERT INTO target.users SELECT * FROM source.users;
   ```
2. **Incremental Sync**: Replay CDC logs:
   ```sql
   -- Process all INSERTs/UPDATEs since last sync
   INSERT OR REPLACE INTO target.users (...) SELECT ... FROM cdc_log WHERE timestamp > last_synced;
   ```
3. **Schedule**: Use SQLite’s `VACUUM` + replay script in a cron job.

---
## **Alternatives & Extensions**
| Option                     | Pros                                  | Cons                                  | Use Case                          |
|----------------------------|---------------------------------------|---------------------------------------|-----------------------------------|
| **SQLite CDC Extension**   | Pre-built logic (e.g., `sqlite_cdc`). | Heavy dependencies; not pure SQLite. | Quick setup, lower-code solutions.|
| **WAL-Based Tools**        | Tools like `sqliteman` or custom scripts. | Manual effort for replay logic.      | Custom replication pipelines.    |
| **JSON1 + Virtual Tables** | Store logs in a `json1` table for flexibility. | Slower queries.                       | Complex JSON filtering.           |

---
## **Troubleshooting**
| Issue                          | Diagnosis                          | Solution                                  |
|--------------------------------|------------------------------------|-------------------------------------------|
| **Triggers miss changes**      | Check `PRAGMA trigger_list`.       | Verify trigger syntax (e.g., `AFTER` vs `BEFORE`). |
| **Log table grows uncontrollably** | Monitor `cdc_log` size.            | Add a `PURGE` process for old logs.       |
| **Deadlocks during replay**    | Long-running transactions.          | Use `PRAGMA busy_timeout = 5000;`         |
| **Replay fails on constraints**| Foreign key violations.            | Temporarily disable FKs during replay.    |

---
## **Further Reading**
- SQLite WAL Documentation: [https://www.sqlite.org/wal.html](https://www.sqlite.org/wal.html)
- JSON1 Extension: [https://www.sqlite.org/json1.html](https://www.sqlite.org/json1.html)
- Example CDC Replication Script: [GitHub - sqlite-cdc-example](https://github.com/example/sqlite-cdc) *(hypothetical link)*.