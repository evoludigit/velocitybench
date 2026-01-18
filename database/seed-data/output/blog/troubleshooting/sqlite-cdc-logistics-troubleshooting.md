# **Debugging SQLite CDC (Change Data Capture) Logistics: A Troubleshooting Guide**

*Last Updated: [Insert Date]*
*Pattern: SQLite CDC (Change Data Capture) Implementation*

---

## **1. Introduction**
SQLite does not natively support traditional Change Data Capture (CDC) like PostgreSQL or MySQL. Instead, applications must implement CDC by tracking changes via:
- **WAL (Write-Ahead Log) mode** + **journal-based triggers** (SQLite ≥ 3.35)
- **Periodic snapshots** + **DML event logging**
- **External CDC tools** (e.g., Debezium, PostgreSQL’s `pg_logical`)

This guide focuses on debugging **SQLite-specific CDC implementations**, particularly when using **triggers + WAL mode** or **external CDC pipelines**.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the symptoms:

| **Symptom**                          | **Question**                                                                 |
|--------------------------------------|------------------------------------------------------------------------------|
| Missing updates in CDC feed         | Are changes appearing delayed or skipped?                                    |
| High latency in CDC pipeline        | Is WAL log growth causing performance bottlenecks?                          |
| Duplicate/error records in CDC       | Are triggers firing unexpectedly or missing constraints?                   |
| CDC log corruption                   | Are WAL files growing uncontrollably or failing to compact?                 |
| Application crashes on DDL           | Does altering tables break CDC tracking?                                    |
| External CDC tool (e.g., Debezium) fails | Is the tool misconfigured for SQLite WAL?                                   |

---

## **3. Common Issues & Fixes**

### **Issue 1: CDC Events Are Missing**
**Symptoms:**
- No new rows inserted in CDC output after changes.
- Last CDC event is stuck in the past.

**Root Causes:**
- **WAL logging disabled** (`journal_mode=DELETE` or `OFF`).
- **Triggers not firing** (missing permissions, syntax errors).
- **CDC consumer lagging** (not processing logs fast enough).

#### **Fixes:**
1. **Enable WAL Mode** (Critical for CDC):
   ```sql
   PRAGMA journal_mode=WAL; -- Must be set before any DML!
   ```
   *Verify:* Check `PRAGMA journal_mode;` returns `wal`.

2. **Ensure Triggers Exist & Are Firing**:
   ```sql
   -- Example: Track INSERTs via INSERT triggers
   CREATE TRIGGER after_insert_log
   AFTER INSERT ON orders
   WHEN NEW.id IS NOT NULL
   BEGIN
     INSERT INTO cdc_log (operation, table_name, row_data)
     VALUES ('INSERT', 'orders', json_insert($NEW, '$', null));
   END;
   ```
   *Debug:* Run `SELECT sql FROM sqlite_master WHERE type='trigger';` to list triggers.

3. **Check CDC Consumer Health**:
   - If using an external tool (e.g., Debezium), verify:
     ```bash
     # Example Debezium config snippet for SQLite
     {
       "offset.storage.file.filename": "/path/to/offsets.dat"
     }
     ```
   - Monitor log delays with:
     ```bash
     psql -c "SELECT * FROM cdc_log ORDER BY timestamp DESC LIMIT 10;"
     ```

---

### **Issue 2: High WAL File Growth**
**Symptoms:**
- Database grows unexpectedly.
- Slow performance due to WAL bloat.

**Root Causes:**
- WAL not being checkpointed (compacting old logs).
- Too many small transactions (each writes to WAL).

#### **Fixes:**
1. **Force Checkpointing** (Compact WAL):
   ```sql
   PRAGMA wal_checkpoint(FULL); -- Forces truncation of old WAL files
   ```
   *Automate:* Set `PRAGMA wal_autocheckpoint=1000;` (checkpoint after 1000 pages).

2. **Merge Small Transactions**:
   ```sql
   -- Batch multiple INSERTs into one transaction
   BEGIN TRANSACTION;
   INSERT INTO table1 VALUES (...), (...);
   INSERT INTO table2 VALUES (...);
   COMMIT;
   ```

3. **Monitor WAL Size**:
   ```bash
   # Check WAL file size (Linux/macOS)
   du -sh /path/to/database.db-wal
   ```

---

### **Issue 3: Duplicate/CDC Errors**
**Symptoms:**
- Same row appears multiple times in CDC feed.
- CDC log contains `NULL` or malformed data.

**Root Causes:**
- Missing `WHEN` clause in triggers (fires on every DML).
- JSON parsing errors in trigger logic.
- Race conditions in concurrent writes.

#### **Fixes:**
1. **Add Filter Logic to Triggers**:
   ```sql
   CREATE TRIGGER after_insert_log
   AFTER INSERT ON orders
   WHEN NEW.status = 'active'  -- Only log active orders
   BEGIN
     INSERT INTO cdc_log (operation, table_name, row_data)
     VALUES ('INSERT', 'orders', json_object('id', NEW.id, 'customer', NEW.customer));
   END;
   ```

2. **Validate CDC Data**:
   ```sql
   -- Check for NULLs or duplicates
   SELECT operation, COUNT(*)
   FROM cdc_log
   GROUP BY operation HAVING COUNT(*) > 1;
   ```

3. **Use `BEGIN IMMEDIATE` for Isolation**:
   ```sql
   BEGIN IMMEDIATE; -- Prevents overlapping transactions
   -- Critical CDC operations
   COMMIT;
   ```

---

### **Issue 4: DDL Breaks CDC**
**Symptoms:**
- Altering a table drops CDC triggers.
- Schema migrations cause CDC lag.

**Root Causes:**
- Missing `CREATE TRIGGER` in schema migrations.
- WAL mode conflicts with `ALTER TABLE`.

#### **Fixes:**
1. **Recreate Triggers After DDL**:
   ```sql
   -- In your migration script:
   ALTER TABLE orders ADD COLUMN new_field TEXT;
   -- Reapply CDC triggers
   CREATE TRIGGER IF NOT EXISTS after_insert_log AFTER INSERT ON orders ...
   ```

2. **Use `PRAGMA busy_timeout` for Safe Migrations**:
   ```sql
   PRAGMA busy_timeout=5000; -- Retry after 5s if locked
   ```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                                                 | **Example Command**                                  |
|--------------------------|----------------------------------------------------------------------------|------------------------------------------------------|
| `PRAGMA` Queries         | Inspect SQLite internals                                                  | `PRAGMA wal_checkpoint; PRAGMA page_size;`            |
| `sqlite3 .schema`        | List all tables/triggers                                                  | `sqlite3 db.db .schema`                             |
| WAL Log Analyzer         | Decode WAL files manually                                                  | [SQLite WAL Viewer](https://sqlite.org/wal.html)      |
| External CDC Tools       | Validate against Debezium/PostgreSQL CDC                                    | `docker logs debezium-sqlite`                        |
| SQL Profiler             | Track slow CDC-triggered queries                                          | `PRAGMA enable_slow_query_log(1, 100);`             |
| `fsync` Testing          | Test WAL durability                                                       | `PRAGMA synchronous=NORMAL;` (default)              |

**Advanced Debugging:**
- **Enable SQL Logging** (for triggers):
  ```sql
  PRAGMA log=stdout; -- Logs all executed SQL
  ```
- **Use `sqlite3 .dump`** to compare schemas:
  ```bash
  sqlite3 db.db .dump > schema_dump.sql
  ```

---

## **5. Prevention Strategies**

### **Design-Time Fixes**
1. **Standardize CDC Triggers**:
   - Use a **template** for triggers (e.g., `after_<table>_log`).
   - Example:
     ```sql
     CREATE OR REPLACE TRIGGER after_users_log
     AFTER INSERT OR UPDATE OR DELETE ON users
     BEGIN
       INSERT INTO cdc_log
       VALUES (
         CASE WHEN NEW.id IS NOT NULL THEN 'INSERT'
              WHEN OLD.id IS NOT NULL THEN 'UPDATE'
              WHEN OLD.id IS NOT NULL AND NEW.id IS NULL THEN 'DELETE'
         END,
         'users',
         json_object('id', NEW.id, 'data', NEW.data)
       );
     END;
     ```

2. **Automate WAL Management**:
   - Set `PRAGMA wal_autocheckpoint=200;` (checkpoint every 200 pages).
   - Schedule `PRAGMA wal_checkpoint(FULL)` in cron.

3. **Unit Test CDC Triggers**:
   ```sql
   -- Test insert trigger
   INSERT INTO cdc_log_test VALUES ('INSERT', 'test_table', 'data');
   SELECT * FROM cdc_log_test; -- Verify output
   ```

### **Runtime Fixes**
1. **Monitor WAL Growth**:
   ```bash
   # Alert if WAL exceeds 1GB
   du -sh /path/to/db.db-wal | awk '$1 > 1000000000 { system("alert WAL too large!"); }'
   ```

2. **Back Up CDC Logs**:
   ```sql
   -- Export CDC log periodically
   .dump cdc_log > cdc_backup_$(date +%Y%m%d).sql
   ```

3. **Use Transactions for Bulk CDC**:
   ```python
   # Python example: Batch INSERT into CDC
   with db.cursor() as c:
       c.executemany(
           "INSERT INTO cdc_log VALUES (?, ?, ?)",
           [(op, table, data) for op, table, data in changes]
       )
       db.commit()
   ```

---

## **6. Final Checklist for CDC Health**
| **Action**                          | **Tool/Command**                          |
|-------------------------------------|-------------------------------------------|
| Verify WAL mode                     | `PRAGMA journal_mode;`                    |
| Check trigger existence             | `SELECT sql FROM sqlite_master WHERE type='trigger';` |
| Monitor WAL size                    | `du -sh /path/to/db.db-wal`              |
| Test CDC pipeline                   | `sqlite3 db.db "SELECT * FROM cdc_log ORDER BY 1 DESC LIMIT 5;"` |
| Validate no duplicates              | `SELECT operation, COUNT(*) FROM cdc_log GROUP BY operation HAVING COUNT(*) > 1;` |

---
**References:**
- [SQLite WAL Documentation](https://www.sqlite.org/wal.html)
- [Debezium SQLite Connector](https://debezium.io/documentation/reference/stable/connectors/sqlite.html)
- [SQLite Trigger Syntax](https://www.sqlite.org/langCreatetrigger.html)

---
**Note:** If using **Debezium**, ensure:
- `wal.enabled=true` in `sqlite.properties`.
- The **offset table** is correctly configured to avoid reprocessing.