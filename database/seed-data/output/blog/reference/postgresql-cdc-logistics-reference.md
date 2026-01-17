# **[Pattern] PostgreSQL Change Data Capture (CDC) Logistics Reference Guide**

---

## **1. Overview**
This **PostgreSQL Change Data Capture (CDC) Logistics** pattern provides a structured approach to capturing, storing, and processing row-level changes in a database. It leverages **triggers, logical decoding (WAL), and auxiliary tables** to log modifications (inserts, updates, deletes) while maintaining minimal performance overhead. This method is ideal for:
- Auditing changes
- Replication to secondary systems
- Event sourcing architectures
- Near-real-time analytics

Key features include:
✔ **Low-latency change tracking** (via triggers)
✔ **Scalable logging** (auxiliary tables for CDC data)
✔ **Flexible event processing** (replayable changes via queries)
✔ **Compliance-ready** (immutable audit trail)

---

## **2. Key Concepts & Implementation Details**

### **2.1. Core Components**
| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Primary Table**  | Source table with triggers attached to capture changes.                  |
| **CDC Audit Table**| Stores metadata (operation type, timestamp, user).                      |
| **CDC Data Table** | Persists actual changed rows (for complex types like JSON/arrays).      |
| **Trigger Function**| Determines change type (INSERT/UPDATE/DELETE) and records it in audit.  |
| **Logical Decoding (Optional)** | Optional alternative to triggers (via `pg_logical` or `debezium`).     |

### **2.2. Change Tracking Logic**
PostgreSQL triggers fire on `INSERT`, `UPDATE`, and `DELETE` events. The **logistics pattern** standardizes how changes are logged:

- **Operation Type**: Stored as an enum (`INSERT`, `UPDATE`, `DELETE`).
- **Timestamps**:
  - `captured_at` (when change was recorded)
  - `transaction_timestamp` (original PostgreSQL timestamp).
- **User Context**: Captured via `current_user` (for security/audit).
- **Data Payload**: Only modified columns stored in a secondary table.

### **2.3. Performance Considerations**
| Technique               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Batch Logging**       | Aggregate changes in a single transaction to reduce disk I/O.              |
| **Partitioning**        | Shard CDC tables by date/tenant to improve query performance.              |
| **Trigger Delay**       | Non-critical tables can defer triggers to reduce latency.                   |
| **Indexing**            | Add indexes on `transaction_id`, `captured_at`, and `table_name` for fast lookups. |

---

## **3. Schema Reference**

### **3.1. Audit Table Schema**
Stores metadata about changes (lightweight).

```sql
CREATE TABLE audit_cdc (
    audit_id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL, -- Name of the source table
    record_id BIGINT NOT NULL, -- Primary key of changed row (NULL for INSERTs)
    operation_type TEXT NOT NULL CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    transaction_timestamp TIMESTAMPTZ NOT NULL,
    performed_by TEXT NOT NULL, -- Current user or app caller
    -- Optional fields for tracing
    client_addr INET,
    query_hash TEXT, -- Hash of the original SQL (for replayability)
    CONSTRAINT unique_table_record_operation UNIQUE (table_name, record_id, operation_type)
);
```

### **3.2. Data Table Schema**
Stores actual changed rows (for non-trivial data types).

```sql
CREATE TABLE cdc_data (
    data_id BIGSERIAL PRIMARY KEY,
    audit_id BIGINT REFERENCES audit_cdc(audit_id),
    table_name TEXT NOT NULL,
    record_id BIGINT NOT NULL,
    operation_type TEXT NOT NULL,
    old_data JSONB,   -- For UPDATE/DELETE (pre-change state)
    new_data JSONB,   -- For INSERT/UPDATE (post-change state)
    -- For complex types, serialize/deserialize using pg_dump's --data-only
    CHECK (
        (operation_type = 'INSERT' AND new_data IS NOT NULL AND old_data IS NULL)
        OR (operation_type = 'UPDATE' AND old_data IS NOT NULL AND new_data IS NOT NULL)
        OR (operation_type = 'DELETE' AND old_data IS NOT NULL AND new_data IS NULL)
    )
);
```

### **3.3. Trigger Function Template**
```sql
CREATE OR REPLACE FUNCTION capture_table_changes()
RETURNS TRIGGER AS $$
DECLARE
    op_type TEXT;
BEGIN
    -- Determine operation type
    IF TG_OP = 'INSERT' THEN
        op_type := 'INSERT';
    ELSIF TG_OP = 'UPDATE' THEN
        op_type := 'UPDATE';
    ELSIF TG_OP = 'DELETE' THEN
        op_type := 'DELETE';
    END IF;

    -- Insert into audit log (lightweight)
    INSERT INTO audit_cdc (
        table_name, record_id, operation_type, transaction_timestamp, performed_by
    ) VALUES (
        TG_TABLE_NAME, NEW.id, op_type, current_timestamp, current_user
    );

    -- Insert into data log (if needed)
    IF op_type <> 'INSERT' THEN -- No old_data for INSERTs
        INSERT INTO cdc_data (
            audit_id, table_name, record_id, operation_type, old_data
        ) VALUES (
            (SELECT audit_id FROM audit_cdc ORDER BY audit_id DESC LIMIT 1),
            TG_TABLE_NAME, NEW.id, op_type, OLD.*
        );
    END IF;

    IF op_type <> 'DELETE' THEN -- No new_data for DELETEs
        INSERT INTO cdc_data (
            audit_id, table_name, record_id, operation_type, new_data
        ) VALUES (
            (SELECT audit_id FROM audit_cdc ORDER BY audit_id DESC LIMIT 1),
            TG_TABLE_NAME, NEW.id, op_type, NEW.*
        );
    END IF;

    RETURN NULL; -- Required for TRIGGER
END;
$$ LANGUAGE plpgsql;
```

---

## **4. Query Examples**

### **4.1. Query CDC Logs for a Table**
```sql
-- Get all changes for 'users' table in the last hour
SELECT *
FROM audit_cdc
WHERE table_name = 'users'
  AND captured_at > NOW() - INTERVAL '1 hour'
ORDER BY captured_at;
```

### **4.2. Replay Changes to a Target System**
```sql
-- Generate INSERT statements from CDC logs (simplified)
SELECT
    format('INSERT INTO %I VALUES (%s);',
           table_name,
           format_array(
               COALESCE(
                   jsonb_agg(format('%%L', k) || ' = ' || format('%I', v)::TEXT,
                             '{},'::TEXT))
               || 'true'::TEXT,
               (SELECT jsonb_object_keys(new_data)) AS keys
           )
    ) AS replay_sql
FROM (
    SELECT
        table_name,
        new_data,
        row_to_json(array_agg(structure(k, v))) AS jsonb_agg
    FROM cdc_data
    WHERE operation_type = 'INSERT'
      AND table_name = 'orders'
      AND captured_at > NOW() - INTERVAL '1 day'
    GROUP BY table_name, new_data
) t;
```

### **4.3. Find All Columns Changed in an Update**
```sql
-- Get columns modified in a specific update
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'users'
  AND column_name IN (
      SELECT
          jsonb_object_keys(old_data)
      FROM cdc_data
      WHERE table_name = 'users'
        AND operation_type = 'UPDATE'
        AND record_id = 12345
  );
```

### **4.4. Audit Trail for a Specific Row**
```sql
-- Get full history for a specific row (e.g., user_id = 100)
SELECT
    a.operation_type,
    a.captured_at,
    a.performed_by,
    COALESCE(
        (SELECT jsonb_pretty(b.new_data) FROM cdc_data b
         WHERE b.audit_id = a.audit_id AND b.operation_type = 'UPDATE'),
        (SELECT jsonb_pretty(b.old_data) FROM cdc_data b
         WHERE b.audit_id = a.audit_id AND b.operation_type = 'DELETE')
    ) AS row_state
FROM audit_cdc a
WHERE a.table_name = 'users'
  AND (
      (a.operation_type = 'UPDATE' AND a.record_id = 100)
      OR (a.operation_type = 'DELETE' AND a.record_id = 100)
  )
ORDER BY a.captured_at DESC;
```

---

## **5. Related Patterns**

| Pattern                    | Description                                                                                     | When to Use                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Logical Decoding CDC]** | Uses WAL (Write-Ahead Log) for high-speed change capture (via `pg_logical` or `debezium`).    | High-throughput systems where triggers are too slow.                                             |
| **[Materialized View CDC]**| Refreshes a materialized view on change (via `REFRESH MATERIALIZED VIEW CONCURRENTLY`).      | Read-optimized reporting where incremental refreshes are needed.                                |
| **[Temporal Tables]**      | PostgreSQL’s native `FOR SYSTEM_TIME` tables for time-travel queries.                          | Systems requiring full historical querying without CDC.                                         |
| **[Trigger + Sink Queue]**  | Offloads CDC processing to a message queue (e.g., Kafka, RabbitMQ).                          | Distributed architectures where changes need async processing.                                  |
| **[Audit Extension]**      | Uses `pg_audit` or custom extensions for built-in auditing without triggers.                  | Simplicity; when full CDC is not required (e.g., compliance-only tracking).                     |

---

## **6. Migration Guide**
### **6.1. Existing Tables**
1. **Add CDC tables**:
   ```sql
   -- Run for each table needing CDC
   CREATE TABLE audit_cdc (...);
   CREATE TABLE cdc_data (...);
   ```
2. **Create triggers**:
   ```sql
   CREATE TRIGGER trg_users_cdc AFTER INSERT OR UPDATE OR DELETE ON users
   FOR EACH ROW EXECUTE FUNCTION capture_table_changes();
   ```

### **6.2. New Tables**
1. **Add CDC tables as part of schema**:
   ```sql
   CREATE TABLE my_table (
       id SERIAL PRIMARY KEY,
       name TEXT NOT NULL
   ) WITH (capture_changes = ON); -- Hypothetical extension flag
   ```

### **6.3. Performance Tuning**
- **Analyze CDC tables**:
  ```sql
  ANALYZE audit_cdc;
  ANALYZE cdc_data;
  ```
- **Vacuum regularly** (especially for high-write tables):
  ```sql
  VACUUM (VERBOSE, ANALYZE) audit_cdc;
  ```

---

## **7. Caveats & Limitations**
| Issue                     | Workaround                                                                                     |
|---------------------------|------------------------------------------------------------------------------------------------|
| **Circular Dependencies** | Avoid triggers on CDC tables themselves.                                                     |
| **Large Objects**         | Use `pg_largeobject` or external storage (S3/GCS) for binary data.                            |
| **Concurrency Risks**     | Use `ON CONFLICT` clauses or advisory locks for high-contention tables.                        |
| **Complex Types**         | Convert JSON/arrays to text or use PostgreSQL’s `jsonb`/`array` serialization.                 |
| **Slow Queries**          | Add indexes on frequently queried columns (`transaction_id`, `captured_at`).                     |

---
**Appendix**: [Example DDL for a Full Implementation](https://github.com/example/postgres-cdc-pattern)