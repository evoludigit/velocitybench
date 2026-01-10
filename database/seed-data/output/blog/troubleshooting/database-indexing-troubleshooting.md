---
# **Debugging Database Indexing Strategies: A Troubleshooting Guide**
*Optimizing indexes to resolve slow queries, CPU bottlenecks, and lock contention*

---

## **1. Symptom Checklist**
Before diving into fixes, verify if indexing issues are the root cause:

✅ **Slow Queries**
- `EXPLAIN ANALYZE` shows **sequential scans (Seq Scan)** or **full table scans** (`Full Scan`).
- Long-running queries (e.g., > 1s) despite proper filtering.
- Queries with high **execution time but low rows processed** (indicating inefficient sorting/joins).

✅ **High CPU Usage**
- Database server (`postgres`, `mysql`, `mongodb`) CPU consistently **> 60%** under load.
- `top`/`htop` shows database threads (`postmaster`, `mysqld`, `mongod`) as top CPU consumers.
- CPU spikes correlate with **large result sets** or **missing indexes**.

✅ **Lock Contention**
- `pg_locks` (PostgreSQL) or `SHOW PROCESSLIST` (MySQL) shows **long-running locks**.
- Write operations (INSERT/UPDATE/DELETE) blocking reads for extended periods.
- High **deadlocks** (PostgreSQL: `pg_stat_activity`; MySQL: `SHOW ENGINE INNODB STATUS`).

✅ **Resource Wastage**
- High **I/O wait** (check `iostat` or `vmstat`).
- Memory pressure (high **buffer cache miss ratio** in PostgreSQL’s `pg_stat_database`).

✅ **Application Bottlenecks**
- APIs respond slowly despite backend code being optimized.
- **Time-based profiling** (e.g., `EXPLAIN ANALYZE`) confirms slow DB operations.

---
## **2. Common Issues & Fixes**
### **Issue 1: Missing Indexes**
**Symptoms**:
- `EXPLAIN ANALYZE` shows **Seq Scan** for queries with `WHERE`, `JOIN`, or `ORDER BY` clauses.
- Example:
  ```sql
  -- Slow query (missing index on `user_id`)
  SELECT * FROM orders WHERE user_id = 123 AND status = 'shipped';
  ```

**Fix**:
**Add composite indexes** for frequently filtered/sorted columns:
```sql
-- PostgreSQL/MySQL
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- MongoDB
db.orders.createIndex({ user_id: 1, status: 1 });
```
**Key**:
- **Order matters**: Place most selective columns first (e.g., `status` before `user_id` if filtering by status is rare).
- **Test with `EXPLAIN ANALYZE`** after adding:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123 AND status = 'shipped';
  ```

---

### **Issue 2: Over-Indexed Tables**
**Symptoms**:
- **High CPU** due to many indexes being scanned during `INSERT`/`UPDATE`.
- `pg_stat_all_indexes` (PostgreSQL) or `SHOW INDEX` (MySQL) shows **10+ indexes** on a table.
- Slower writes than reads.

**Fix**:
**Drop redundant indexes**:
```sql
-- PostgreSQL
DROP INDEX IF EXISTS idx_orders_unused;

-- MySQL
ALTER TABLE orders DROP INDEX idx_unused_column;
```
**Guidelines**:
- **Rule of 5**: Only index columns used in `WHERE`, `JOIN`, or `ORDER BY` **5%+ of the time**.
- **Unique indexes**: Use `UNIQUE` for `PRIMARY KEY` or `UNIQUE` constraints (e.g., `email` in users table).
- **Covering indexes**: Include all columns needed by the query to avoid table lookups:
  ```sql
  CREATE INDEX idx_orders_covering ON orders(user_id) INCLUDE (status, amount);
  ```

---

### **Issue 3: Inefficient Index Types**
**Symptoms**:
- **Prefix indexes** (e.g., `index ON email(3)`) fail to narrow searches.
- **Full-text search** queries are slow despite `FULLTEXT` indexes.
- **Range queries** on non-indexed columns (e.g., `WHERE created_at > '2023-01-01'`).

**Fix**:
**Choose the right index type**:
| Scenario               | Index Type               | Example                          |
|------------------------|--------------------------|----------------------------------|
| Exact matches (`=`)    | B-tree (default)         | `CREATE INDEX idx_user_email ON users(email);` |
| Range scans (`>`, `<`)  | B-tree                   | `CREATE INDEX idx_order_date ON orders(created_at);` |
| Text search            | GIN/GiST (PostgreSQL)    | `CREATE INDEX idx_post_content ON posts USING gin(to_tsvector('english', content));` |
| Geospatial             | GiST (PostgreSQL)        | `CREATE INDEX idx_geo_loc ON locations USING gist(geom);` |
| Partial matches        | Trigram (PostgreSQL)     | `CREATE EXTENSION pg_trgm; CREATE INDEX idx_user_name_trgm ON users USING gin(name gin_trgm_ops);` |

**Example (PostgreSQL for text search)**:
```sql
-- Add full-text search index
CREATE INDEX idx_blog_post_content ON blog_posts USING gin(to_tsvector('english', title) || ' ' || to_tsvector('english', content));

-- Query using ts_query
SELECT * FROM blog_posts WHERE to_tsvector('english', title || ' ' || content) @@ to_tsquery('web development');
```

---

### **Issue 4: Index Fragmentation**
**Symptoms**:
- **Slow inserts/updates** despite proper indexing.
- `pg_stat_user_tables` (PostgreSQL) shows **high `n_live_tup` vs. `n_dead_tup`**.
- `SHOW TABLE STATUS` (MySQL) reports **high `Avg_row_length`**.

**Fix**:
**Rebuild or reorganize indexes**:
```sql
-- PostgreSQL: Rebuild index (downtime)
REINDEX TABLE orders;

-- MySQL: Rebuild (less disruptive)
ALTER TABLE orders DISABLE KEYS, REPAIR TABLE orders, ENABLE KEYS;

-- PostgreSQL: Online index rebuild (v10+)
ALTER INDEX idx_orders_user_status REBUILD;
```

**Preventative Measures**:
- **Vacuum regularly** (PostgreSQL):
  ```sql
  VACUUM (VERBOSE, ANALYZE) orders;
  ```
- **Schedule maintenance**:
  ```sql
  -- MySQL: Optimize table
  OPTIMIZE TABLE orders;
  ```

---

### **Issue 5: Lock Contention from Indexing**
**Symptoms**:
- **Deadlocks** in `pg_stat_activity` (PostgreSQL) or `SHOW ENGINE INNODB STATUS` (MySQL).
- `LOCK TABLES` blocking reads/writes for minutes.
- High `pg_locks` wait events (PostgreSQL) or `Innodb_buffer_pool_wait_free` (MySQL).

**Fix**:
**Optimize locking strategies**:
1. **Avoid `SELECT FOR UPDATE` without necessity**:
   ```sql
   -- Bad: Blocks the row unnecessarily
   SELECT * FROM accounts WHERE id = 123 FOR UPDATE;

   -- Good: Use explicit locks only when needed
   BEGIN;
   UPDATE accounts SET balance = balance - 100 WHERE id = 123 AND balance > 100;
   COMMIT;
   ```
2. **Use `SKIP LOCKED` (PostgreSQL)** for retryable operations:
   ```sql
   SELECT * FROM orders WHERE status = 'pending' FOR UPDATE SKIP LOCKED;
   ```
3. **Increase `innodb_lock_wait_timeout` (MySQL)** (default: 50s):
   ```sql
   SET GLOBAL innodb_lock_wait_timeout = 120;
   ```
4. **Add indexes to frequently locked columns**:
   ```sql
   -- Index helps avoid full-table scans during locking
   CREATE INDEX idx_accounts_locked ON accounts(id);
   ```

---

### **Issue 6: Index-Only Scans Failing**
**Symptoms**:
- Query uses **index scan** (`Index Scan`) but still performs **table access** (`Heap Access`).
- `EXPLAIN ANALYZE` shows **extra "Seq Scan"** or **"Materialize"** steps.

**Fix**:
**Ensure covering indexes**:
```sql
-- Fix: Include all columns needed by the query
CREATE INDEX idx_orders_covering ON orders(user_id) INCLUDE (status, amount, created_at);

-- Query now uses only the index
EXPLAIN ANALYZE SELECT user_id, status, amount FROM orders WHERE user_id = 123;
```

**Debugging Steps**:
1. Run `EXPLAIN ANALYZE` to see if `Heap Fetch` or `Seq Scan` appears.
2. Add `INCLUDE` columns to cover all query needs.
3. For PostgreSQL, check `pg_stat_user_indexes` for `idx_scan` vs. `heap_access`.

---

## **3. Debugging Tools & Techniques**
### **PostgreSQL**
| Tool/Command               | Purpose                          |
|----------------------------|----------------------------------|
| `EXPLAIN ANALYZE`          | Show query execution plan + stats. |
| `pg_stat_statements`       | Track slow queries (enable with `shared_preload_libraries`). |
| `pg_buffercache`           | Inspect buffer cache hits/misses. |
| `pg_locks`                 | Check for lock contention.       |
| `pg_stat_user_tables`      | Monitor table bloat/fragmentation. |
| `VACUUM ANALYZE`           | Refresh statistics and clean up. |

**Example**:
```sql
-- Enable pg_stat_statements (postgresql.conf)
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all

-- Check slow queries
SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### **MySQL**
| Tool/Command               | Purpose                          |
|----------------------------|----------------------------------|
| `EXPLAIN`                  | Show query execution plan.       |
| `SHOW PROCESSLIST`         | Identify long-running queries.   |
| `pt-query-digest` (Percona) | Analyze query logs.              |
| `SHOW ENGINE INNODB STATUS`| Check locks/deadlocks.           |
| `ANALYZE TABLE`            | Update table statistics.         |
| `pt-index-usage` (Percona) | Find unused indexes.             |

**Example**:
```sql
-- Check index usage (MySQL 8.0+)
SELECT * FROM information_schema.innodb_index_stats WHERE unique_eq_ref IS NOT NULL LIMIT 10;
```

### **MongoDB**
| Tool/Command               | Purpose                          |
|----------------------------|----------------------------------|
| `explain("executionStats")`| Show query execution plan.       |
| `db.collection.aggregate([{ $explain: true }])` | Aggregate explanations. |
| `db.currentOp()`           | Monitor long-running ops.         |
| `db.stats()`               | Check database size/index usage.  |
| `db.collection.ensureIndex()` | Add/review indexes.             |

**Example**:
```javascript
// Explain a query
db.orders.find({ status: "shipped" }).explain("executionStats");

// Check index usage
db.system.indexes.find({ "ns": "orders" });
```

---
## **4. Prevention Strategies**
### **1. Design Indexes Early**
- **Schema Design**: Add indexes during schema creation, not as an afterthought.
- **Document Query Patterns**: Track frequent queries and index accordingly.
- **Automated Tools**:
  - **MySQL**: `pt-index-usage` to find unused indexes.
  - **PostgreSQL**: `pg_stat_statements` to log query patterns.

### **2. Monitor and Maintain Indexes**
- **Regular Vacuum/Reindex**:
  ```sql
  -- PostgreSQL: Schedule weekly vacuum
  CREATE OR REPLACE FUNCTION vacuum_routine()
  RETURNS TRIGGER AS $$
  BEGIN
    PERFORM vacuum('analyze', 'verbose', 'orders');
    RETURN NULL;
  END;
  $$ LANGUAGE plpgsql;
  ```
- **Set Up Alerts**:
  - **PostgreSQL**: Alert on `n_dead_tup > 0` in `pg_stat_user_tables`.
  - **MySQL**: Alert on `Table locks` in `SHOW PROCESSLIST`.

### **3. Optimize Query Writing**
- **Avoid `SELECT *`**: Fetch only needed columns.
  ```sql
  -- Bad
  SELECT * FROM users;

  -- Good
  SELECT id, email FROM users WHERE id = 123;
  ```
- **Limit Result Sets**:
  ```sql
  -- Bad: Returns all 1M rows
  SELECT * FROM logs;

  -- Good
  SELECT * FROM logs WHERE created_at > NOW() - INTERVAL '1 day' LIMIT 1000;
  ```
- **Use `EXPLAIN` Proactively**:
  ```sql
  EXPLAIN ANALYZE SELECT ... [BEFORE writing the query];
  ```

### **4. Database-Specific Tuning**
| Database      | Tuning Knob                          | Recommended Value                     |
|---------------|--------------------------------------|---------------------------------------|
| **PostgreSQL**| `maintenance_work_mem`               | `128MB–1GB` (for large vacuums)      |
|               | `shared_buffers`                     | `25–50% of RAM`                       |
| **MySQL**     | `innodb_buffer_pool_size`            | `80% of RAM`                          |
|               | `innodb_log_file_size`               | `25% of buffer pool size`             |
| **MongoDB**   | `wiredTigerCacheSizeGB`              | `50% of RAM`                          |
|               | `indexBuildProcessors`               | `4–8` (for large index builds)        |

### **5. CI/CD Pipeline Integration**
- **Pre-deploy Index Checks**:
  - Run `pg_stat_statements` or `EXPLAIN ANALYZE` in test environments.
  - Block deployments if queries exceed latency thresholds (e.g., > 500ms).
- **Automated Index Reviews**:
  - Use tools like **Percona’s `pt-online-schema-change`** to safely add indexes in production.

---
## **5. Step-by-Step Troubleshooting Workflow**
### **Step 1: Identify the Slow Query**
```bash
# PostgreSQL: Find top CPU consumers
SELECT query, total_time, calls FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;

# MySQL: Use pt-query-digest
pt-query-digest slow.log | head -20
```

### **Step 2: Analyze the Execution Plan**
```sql
EXPLAIN ANALYZE SELECT ... [your slow query];
```
**Flags to watch for**:
- `Seq Scan` (full table scan).
- `Sort` (high cost → add index to `ORDER BY` column).
- `Hash Join`/`Nested Loop` (inefficient joins → add indexes to join columns).

### **Step 3: Add Missing Indexes**
```sql
-- Example: Add index based on EXPLAIN output
CREATE INDEX idx_users_email_status ON users(email, status);
```

### **Step 4: Validate Fix**
```sql
EXPLAIN ANALYZE [same query];
```
**Goal**: `Index Scan` with low cost (< 1% of total query time).

### **Step 5: Monitor Impact**
- **Post-deploy**: Check `pg_stat_statements` or `SHOW PROCESSLIST` for regressions.
- **Alerting**: Set up dashboards (e.g., **Grafana + Prometheus**) for:
  - Query latency.
  - Lock contention.
  - Index bloat.

### **Step 6: Iterate**
- If the query remains slow, check for:
  - **Missing `INCLUDE` columns** (covering index issue).
  - **Inefficient joins** (add indexes to foreign keys).
  - **Application-side optimizations** (e.g., pagination, caching).

---
## **6. Common Pitfalls & Anti-Patterns**
| **Anti-Pattern**               | **Why It’s Bad**                          | **Fix**                                  |
|---------------------------------|-------------------------------------------|------------------------------------------|
| **Over-indexing**               | Slows writes (high `INSERT`/`UPDATE` cost). | Drop unused indexes (`pt-index-usage`). |
| **Indexing non-selective cols** | E.g., `CREATE INDEX ON users(last_name);` | Only index columns used in `WHERE`.     |
| **Ignoring `SELECT *`**         | Forces full table access even with indexes. | Fetch only needed columns.               |
| **Using `LIKE '%text%'`**       | Can’t use B-tree indexes (use full-text). | Use `LIKE 'text%'` or `ILIKE 'text%'` + trigram index. |
| **Not vacuuming**               | Fragmentation degrades performance.       | Schedule `VACUUM ANALYZE`.                |
| **Dynamic SQL without planning**| Queries change runtime → indexes may not help. | Use prepared statements.                |

---
## **7. Final Checklist for Resolution**
Before closing a ticket:
- [ ] **Query is now using `Index Scan`** (not `Seq Scan`).
- [ ] **Write performance (INSERT/UPDATE) is acceptable** (no CPU spikes).
- [ ] **Lock contention is resolved** (`SHOW PROCESSLIST` shows no long locks).
- [ ] **Index size is reasonable** (`pg_size_pretty(pg_relation_size('table'))`).
- [ ] **Monitoring is in place** (alerts for regressions).

---
## **References**
- **PostgreSQL**: [EXPLAIN Documentation](https://www.postgresql.org/docs/current/using-explain.html)
- **MySQL**: [Indexing Best Practices](https://dev.mysql.com/doc/refman/8.0/en/optimize-indexes.html)
- **MongoDB**: [Indexing Guide](https://www.mongodb.com/docs/manual/indexes/)
- **Tools**:
  - [Percona Toolkit](https://www.percona.com/doc/percona-toolkit/)
  - [pgMustard](https://pgmustard.com/) (PostgreSQL query analysis