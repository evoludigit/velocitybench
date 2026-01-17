# **Debugging PostgreSQL Change Data Capture (CDC) with Triggers: A Troubleshooting Guide**

## **Introduction**
PostgreSQL Change Data Capture (CDC) using triggers is a powerful way to track and propagate database changes in real-time. This pattern is commonly used for auditing, event sourcing, or syncing data across systems. However, like any complex setup, it can encounter issues—particularly around trigger logic, deadlocks, performance bottlenecks, or incorrect data propagation.

This guide provides a structured approach to diagnosing and resolving common problems in PostgreSQL CDC triggered by database events.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which symptoms match your issue:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|-------------------|
| **Missing CDC events** | Changes to the database are not captured in logs/tables | Trigger not firing, function failing, or CDC table not updated |
| **Duplicate CDC records** | Same change appears multiple times in CDC logs | Trigger fired multiple times, or transaction retries |
| **Slow CDC processing** | High latency in capturing changes | Large trigger functions, missing indexes, or deadlocks |
| **Incorrect CDC data** | Captured data doesn’t match original change | Trigger logic error, incorrect `NEW`/`OLD` handling |
| **Trigger deadlocks** | Long-running transactions cause deadlocks in CDC | Heavy trigger workload, missing constraint checks |
| **CDC table corruption** | Stale or inconsistent CDC records | Transaction rollback, race conditions, or improper isolation |
| **Permission errors** | Trigger fails with `permission denied` | Missing `CREATE FUNCTION` or `EXECUTE` rights |
| **Missing dependencies** | Trigger fails due to missing objects | Schema changes, dropped functions, or referential integrity issues |

---

## **2. Common Issues and Fixes**

### **Issue 1: Triggers Are Not Firing**
**Symptoms:**
- No new rows in the CDC table despite database changes.
- Logs show no trigger execution.

**Possible Causes & Fixes:**

#### **A. Incorrect Trigger Definition**
```sql
-- Wrong: Missing FOR EACH ROW clause
CREATE TRIGGER log_changes
AFTER INSERT ON orders
BEGIN
    INSERT INTO cdc_log (table_name, change_type, data) VALUES ('orders', 'INSERT', NEW.*);
END;
```
❌ **Fix:** Ensure `FOR EACH ROW` is included (default in newer PostgreSQL versions).
```sql
CREATE OR REPLACE FUNCTION log_order_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO cdc_log (table_name, change_type, record_id, data)
    VALUES ('orders', TG_OP, NEW.id, to_jsonb(NEW));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_orders_cdc
AFTER INSERT OR UPDATE OR DELETE ON orders
FOR EACH ROW EXECUTE FUNCTION log_order_changes();
```

#### **B. Missing Permissions**
❌ **Symptom:** `permission denied` on `cdc_log` table.
🔧 **Fix:** Grant `INSERT` on the CDC table.
```sql
GRANT INSERT ON cdc_log TO trigger_user;
```

#### **C. Transaction Isolation Issues**
❌ **Symptom:** CDC records appear missing after a rollback.
🔧 **Fix:** Ensure triggers run within the same transaction context.
```sql
-- Wrap CDC logic in a single transaction if needed
BEGIN;
-- Business logic
COMMIT;
-- Trigger should still fire even on rollback (if using AFTER trigger)
```

---

### **Issue 2: Duplicate CDC Records**
**Symptoms:**
- Same row change appears multiple times in `cdc_log`.
- Logs show redundant `INSERT`/`UPDATE` entries.

**Possible Causes & Fixes:**

#### **A. Trigger Fires on Every DML Statement**
❌ **Problem:** If multiple rows are inserted in a single `INSERT` statement, the trigger fires once per row.
🔧 **Solution:** Use `INSERT ... RETURNING` or track batch changes.
```sql
-- Example: Track bulk inserts as a single event
CREATE OR REPLACE FUNCTION log_bulk_operations()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO cdc_log (table_name, change_type, record_count, data)
        VALUES ('orders', TG_OP, 1, to_jsonb(NEW));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to a row-level trigger
CREATE TRIGGER trg_orders_bulk_cdc
AFTER INSERT OR UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION log_bulk_operations();
```

#### **B. Retries Due to Constraints or Errors**
❌ **Problem:** If `cdc_log` has constraints, failed inserts may retry.
🔧 **Fix:** Ensure CDC table schema allows all types of changes.
```sql
-- Example: Handle NULLs and edge cases
CREATE TABLE cdc_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    change_type VARCHAR(10) CHECK (change_type IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id BIGINT,
    data JSONB,
    capture_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### **Issue 3: Slow CDC Processing**
**Symptoms:**
- High latency in logging changes.
- Long-running transactions blocking CDC.

**Possible Causes & Fixes:**

#### **A. Heavy Trigger Logic**
❌ **Problem:** Complex JSON serialization or large `NEW`/`OLD` processing.
🔧 **Fix:** Optimize trigger functions.
```sql
-- Avoid SELECTs in triggers (use direct field access)
CREATE OR REPLACE FUNCTION fast_log_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO cdc_log (table_name, change_type, record_id, data)
    VALUES ('orders', TG_OP, NEW.id, to_jsonb(NEW::jsonb - 'sensitive_field'));
    RETURN NEW;
END;
$$;
```

#### **B. Missing Indexes on CDC Table**
❌ **Problem:** Slow updates on `cdc_log`.
🔧 **Fix:** Add indexes for frequently queried columns.
```sql
CREATE INDEX idx_cdc_log_table_name ON cdc_log(table_name);
CREATE INDEX idx_cdc_log_change_type ON cdc_log(change_type);
CREATE INDEX idx_cdc_log_capture_time ON cdc_log(capture_time);
```

#### **C. Deadlocks Due to Heavy Load**
❌ **Problem:** Too many concurrent triggers causing deadlocks.
🔧 **Fix:** Limit trigger concurrency or batch CDC writes.
```sql
-- Use a buffered approach (e.g., with a queue table)
CREATE TABLE cdc_queue (
    id SERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE
);

-- Move heavy processing to a background worker
```

---

### **Issue 4: Incorrect CDC Data**
**Symptoms:**
- Captured data doesn’t match the original change.
- `OLD`/`NEW` values are missing or truncated.

**Possible Causes & Fixes:**

#### **A. Incorrect `NEW`/`OLD` Access**
❌ **Problem:** Missing a field in `NEW`/`OLD`.
🔧 **Fix:** Explicitly handle all required fields.
```sql
-- Ensure all fields are captured
CREATE OR REPLACE FUNCTION safe_log_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO cdc_log (table_name, change_type, record_id, old_data, new_data)
    VALUES (
        'orders',
        TG_OP,
        NEW.id,
        (OLD IS NOT NULL ? to_jsonb(OLD) : NULL),
        to_jsonb(NEW)
    );
    RETURN NEW;
END;
$$;
```

#### **B. Data Type Mismatches**
❌ **Problem:** `JSONB` conversion fails on large text or binary fields.
🔧 **Fix:** Use `to_jsonb()` with transformations.
```sql
-- Handle binary data safely
CREATE OR REPLACE FUNCTION log_with_binary_safe()
RETURNS TRIGGER AS $$
DECLARE
    safe_data JSONB;
BEGIN
    safe_data := to_jsonb(
        jsonb_build_object(
            'id', NEW.id,
            'product', NEW.product,
            'details', NEW.details::text  -- Force text conversion if needed
        )
    );
    INSERT INTO cdc_log (table_name, change_type, data)
    VALUES ('orders', TG_OP, safe_data);
    RETURN NEW;
END;
$$;
```

---

## **3. Debugging Tools and Techniques**

### **A. Querying Trigger Fires**
Check if triggers are executing:
```sql
-- List active triggers
SELECT * FROM information_schema.triggers WHERE event_object_table = 'orders';

-- Check trigger status (if using plpgsql debug)
SELECT * FROM pg_triggers WHERE tgname = 'trg_orders_cdc';
```

### **B. Logging Trigger Execution**
Add debug logs to triggers:
```sql
CREATE OR REPLACE FUNCTION debug_log_changes()
RETURNS TRIGGER AS $$
BEGIN
    RAISE NOTICE 'Trigger fired for row %: %', TG_OP, NEW.id;
    INSERT INTO cdc_log (...) VALUES (...);
    RETURN NEW;
END;
$$;
```

### **C. Using `pg_stat_statements` for Performance Analysis**
Install and enable the extension:
```sql
CREATE EXTENSION pg_stat_statements;
```
Then check trigger-related statements:
```sql
SELECT * FROM pg_stat_statements
WHERE query LIKE '%log_order_changes%'
ORDER BY total_time DESC;
```

### **D. Reproducing Issues with Test Data**
Create a controlled test case:
```sql
-- Reset test data
DELETE FROM orders;
INSERT INTO orders (id, product, amount) VALUES (1, 'Test', 100);

-- Force a trigger firing
INSERT INTO orders (id, product, amount) VALUES (2, 'Another', 200)
RETURNING id;
```

### **E. Using `pg_dump` and `pg_restore` for Recovery**
If CDC data is corrupted:
```bash
pg_dump -t cdc_log -U postgres > cdc_log_backup.sql
```

---

## **4. Prevention Strategies**

### **A. Design for Scalability**
- **Batch CDC Writes:** Use a queue table to avoid blocking.
- **Partition CDC Tables:** Split logs by time or table.
- **Use Asynchronous Processing:** Offload CDC to a background worker.

### **B. Error Handling in Triggers**
```sql
CREATE OR REPLACE FUNCTION robust_log_changes()
RETURNS TRIGGER AS $$
BEGIN
    BEGIN
        INSERT INTO cdc_log (...) VALUES (...);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'CDC log failed for row %: %', NEW.id, SQLERRM;
        RETURN NEW;
    END;
    RETURN NEW;
END;
$$;
```

### **C. Monitor Trigger Performance**
- Set up alerts for slow triggers in `pg_stat_statements`.
- Use `pgBadger` or `pganalyze` for log analysis.

### **D. Schema Evolution**
- **Avoid Breaking Changes:** Document CDC table schema versioning.
- **Backward Compatibility:** Ensure old CDC records remain readable.

### **E. Use `ON UPDATE` Carefully**
- If `ON UPDATE` causes unexpected behavior, consider a `BEFORE UPDATE` trigger to validate changes first.

---

## **Conclusion**
PostgreSQL CDC with triggers is a robust pattern, but it requires careful tuning to avoid common pitfalls. By following this guide—checking symptoms, optimizing triggers, and preventing issues proactively—you can ensure reliable change tracking.

**Key Takeaways:**
✅ Verify triggers fire correctly.
✅ Optimize trigger logic and indexing.
✅ Handle duplicates and data integrity.
✅ Monitor performance with `pg_stat_statements`.
✅ Test edge cases in a controlled environment.

For persistent issues, consider alternatives like **Logical Decoding (WAL-based CDC)** or **Debezium**, which handle scale better than triggers.