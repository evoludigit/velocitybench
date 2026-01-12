# **Debugging "Database Standards" Pattern: A Troubleshooting Guide**

## **Introduction**
The **Database Standards Pattern** ensures consistency, maintainability, and efficiency in database design, schema management, and query execution across applications. When misapplied, it can lead to performance bottlenecks, data inconsistencies, or security vulnerabilities.

This guide provides a structured approach to diagnosing and resolving common issues related to database standards violations.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms to confirm if the issue stems from **Database Standards violations**:

| **Symptom**                     | **Possible Root Cause**                          |
|---------------------------------|------------------------------------------------|
| Slow query performance           | Poor indexing, inefficient joins, missing constraints |
| Data corruption/duplicates      | Lack of unique constraints, weak referential integrity |
| Schema drift (version mismatches)| Uncontrolled migrations, manual schema edits     |
| Security vulnerabilities         | Missing encryption, excessive permissions        |
| High memory/database load        | Unoptimized queries, missing partitioning        |
| Frequent timeouts                | Long-running transactions, missing indexes      |
| Application crashes (DB-related) | SQL injection risk, improper transaction handling |

---

## **2. Common Issues and Fixes**

### **2.1 Missing or Incorrect Indexes**
**Symptoms:**
- Full table scans (`TABLESCAN`) in slow queries (`EXPLAIN` shows sequential access).
- High CPU/disk I/O during read-heavy operations.

**Diagnosis:**
```sql
-- Check query execution plans
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```
**Fix:**
Ensure proper indexes exist for frequently queried columns:
```sql
-- Add missing index
CREATE INDEX idx_users_email ON users(email);

-- Drop unused indexes
DROP INDEX idx_users_old_name ON users;
```

---

### **2.2 Schema Drift (Version Mismatch)**
**Symptoms:**
- `ERROR: column does not exist` during migration.
- Application crashes with schema validation failures.

**Diagnosis:**
```bash
# Compare live DB to expected schema (using Flyway/Liquibase reports)
flyway info
```
**Fix:**
- **Rollback** recent migrations if safe.
- **Sync manually** (carefully—risky):
  ```sql
  ALTER TABLE orders ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
  ```

---

### **2.3 Poor Referential Integrity**
**Symptoms:**
- Orphaned records (e.g., `DELETE FROM orders WHERE customer_id=1` but `customer_id=1` exists).
- Foreign key constraint violations during bulk inserts.

**Diagnosis:**
```sql
-- Find orphaned records
SELECT customer_id FROM orders WHERE customer_id NOT IN (SELECT id FROM customers);
```
**Fix:**
- **Add missing constraints**:
  ```sql
  ALTER TABLE orders ADD CONSTRAINT fk_customer
  FOREIGN KEY (customer_id) REFERENCES customers(id);
  ```
- **Use transactions** for batch updates:
  ```sql
  BEGIN;
  INSERT INTO customers (id, name) VALUES (1, 'Test');
  INSERT INTO orders (customer_id) VALUES (1);
  COMMIT;
  ```

---

### **2.4 Unoptimized Queries**
**Symptoms:**
- `ERROR: cannot modify system table` (deadlocks, locks).
- Slow `JOIN` operations (`EXPLAIN` shows `Hash Join` with high cost).

**Diagnosis:**
```sql
EXPLAIN ANALYZE SELECT * FROM orders o JOIN users u ON o.customer_id = u.id;
```
**Fix:**
- **Partition large tables**:
  ```sql
  ALTER TABLE logs PARTITION BY RANGE (created_at);
  ```
- **Rewrite queries**:
  ```sql
  -- Bad: Joins across millions of rows
  SELECT * FROM huge_table1 JOIN huge_table2 ON ...;

  -- Good: Filter early
  SELECT ht1.* FROM huge_table1 ht1
  JOIN (SELECT id FROM huge_table2 WHERE status='active') ht2 ON ht1.id = ht2.id;
  ```

---

### **2.5 Security Issues**
**Symptoms:**
- SQL injection vulnerabilities.
- Excessive permissions (`GRANT ALL` on production DB).

**Diagnosis:**
```sql
-- Audit user permissions
SELECT * FROM information_schema.role_table_grants;
```
**Fix:**
- **Enforce least-privilege principle**:
  ```sql
  CREATE USER app_user WITH PASSWORD 'secure_pass';
  GRANT SELECT ON orders TO app_user;
  ```
- **Use prepared statements** (avoid string concatenation):
  ```python
  # Bad (SQLi risk)
  cursor.execute(f"SELECT * FROM users WHERE email='{user_input}'")

  # Good
  cursor.execute("SELECT * FROM users WHERE email=%s", (user_input,))
  ```

---

### **2.6 Missing Transactions & Locking**
**Symptoms:**
- Race conditions (e.g., double-bookings).
- Long-running transactions blocking queries.

**Diagnosis:**
```sql
-- Check active locks
SELECT * FROM pg_locks WHERE relation IS NOT NULL;
```
**Fix:**
- **Use transactions explicitly**:
  ```java
  // Good: Transaction per operation
  try (Connection conn = ds.getConnection()) {
      conn.setAutoCommit(false);
      stmt.executeUpdate("UPDATE accounts SET balance=balance-100");
      stmt.executeUpdate("INSERT INTO transactions...");
      conn.commit();
  }
  ```
- **Add timeouts**:
  ```sql
  SET LOCAL lock_timeout = '5s';  -- Prevents deadlocks
  ```

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique**       | **Purpose**                          | **Example**                          |
|--------------------------|--------------------------------------|--------------------------------------|
| `EXPLAIN ANALYZE`        | Analyze query performance            | `EXPLAIN ANALYZE SELECT * FROM t1 JOIN t2;` |
| `pg_stat_statements`     | Track slow queries (PostgreSQL)      | `CREATE EXTENSION pg_stat_statements;` |
| `pgbadger`               | Log analysis for slow queries/errors | `--dbname=mydb --log=debug.log pgbadger` |
| Schema diff tools        | Compare DB state vs. expected        | `flyway diff`                        |
| Stress testing tools     | Simulate load to find bottlenecks    | `wrk -t12 -c400 -d30s http://api.example.com` |

---

## **4. Prevention Strategies**
### **4.1 Enforce Standards via CI/CD**
- **Schema migrations**: Use **Flyway**/**Liquibase** with auto-apply to staging.
- **Linters**: Tools like **SQLfluff** to enforce SQL formatting/standards.

### **4.2 Automation & Monitoring**
- **Schema validation**: Automated checks in PRs (`pre-commit` hooks).
- **Query tuning alerts**: Set up alerts for queries >1s execution time.

### **4.3 Documentation & Training**
- **Internal standards doc**: Define naming conventions (e.g., `tbl_` prefix).
- **Onboarding**: Train DBAs/devs on **indexing best practices**.

### **4.4 Backup as a Last Resort**
- **Regular snapshots**: Use automated backups (e.g., **Backblaze B2**).
- **Rollback testing**: Simulate disasters with `pg_dump`/`mysqldump`.

---
## **Conclusion**
Database standards violations often stem from **cutting corners** (e.g., skipping indexes), **unsynchronized migrations**, or **security oversights**. This guide prioritizes **diagnosing performance bottlenecks, enforcing constraints, and securing queries**.

**Next Steps**:
1. Audit **slow queries** with `EXPLAIN`.
2. Review **migration history** for schema drift.
3. Check **permissions** for least privilege.
4. Automate **schema enforcement** in CI.

By addressing these areas systematically, you reduce downtime and improve reliability.