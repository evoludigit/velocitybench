# **Debugging *Query Performance Optimization*: A Troubleshooting Guide**

## **1. Overview**
Query performance optimization is critical when dealing with slow database operations. Poor query execution—due to missing or inefficient indexes, suboptimal query structure, or excessive full table scans—can degrade application performance. This guide provides a structured approach to diagnosing and resolving query performance issues.

---

## **2. Symptom Checklist**
Before diving into debugging, confirm whether performance issues align with common symptoms:

| Symptom | Description |
|---------|------------|
| **Slow Query Execution** | Queries taking significantly longer than expected (e.g., seconds instead of milliseconds). |
| **Increased CPU/Memory Usage** | Database server CPU or memory saturation during query execution. |
| **High Disk I/O** | Excessive disk reads/writes (visible in performance monitors). |
| **Full Table Scans** | Queries scanning entire tables instead of using indexes (check `EXPLAIN` output). |
| **Long-Lived Locks** | Blocking due to slow-running queries holding locks on tables. |
| **Inconsistent Performance** | Query speed varies unpredictably (e.g., works fast in dev but slow in production). |
| **Large Temporary Tables** | Queries generating excessive temporary storage (indicates inefficient joins or sorting). |

**Action:**
If multiple symptoms exist, prioritize based on impact (e.g., locks > CPU spikes).

---

## **3. Common Issues & Fixes**

### **3.1 Missing or Inefficient Indexes**
**Symptom:** Full table scans (`TableScan` in `EXPLAIN`) for frequently queried columns.

#### **Debugging Steps:**
1. **Inspect Query Plan** (PostgreSQL/SQL Server/MySQL):
   ```sql
   EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;
   ```
   - Look for `Seq Scan` (full table scan) instead of `Index Scan`.
   - Check `Actual Time`: High execution time suggests inefficiency.

2. **Check Existing Indexes**:
   ```sql
   -- PostgreSQL
   SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'orders';

   -- MySQL
   SHOW INDEX FROM orders;
   ```

3. **Design Fixes**:
   - **Add Missing Indexes**:
     ```sql
     -- PostgreSQL
     CREATE INDEX idx_orders_customer_id ON orders(customer_id);

     -- MySQL
     ALTER TABLE orders ADD INDEX idx_customer_id (customer_id);
     ```
   - **Composite Indexes** (for multi-column filters):
     ```sql
     CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
     ```
   - **Covering Indexes** (include columns to avoid table lookup):
     ```sql
     CREATE INDEX idx_orders_covering ON orders(customer_id, order_date, total_amount);
     ```

#### **Code Example (Application-Level Check):**
```python
# Before adding an index, test query speed:
before = time.time()
cursor.execute("SELECT * FROM orders WHERE customer_id = %s", (123,))
after = time.time()
print(f"Query took {after - before:.4f}s")
```

---

### **3.2 Poorly Written Queries**
**Symptom:** Excessive computation, redundant filtering, or non-SARGable (non-indexable) predicates.

#### **Common Anti-Patterns & Fixes:**
| Anti-Pattern | Example | Fix |
|--------------|---------|-----|
| **LIKE with Leading Wildcard** | `WHERE name LIKE '%user%'` | Use `WHERE name LIKE 'user%'` or a full-text index. |
| **OR Without Parentheses** | `WHERE col1 = 'A' OR col2 > 10` | Rewrite as `(col1 = 'A') OR (col2 > 10)`. |
| **SELECT * Without Filtering** | `SELECT * FROM users` | Explicitly list columns: `SELECT id, name FROM users`. |
| **N+1 Query Problem** | Fetch users, then fetch each user’s orders separately. | Use `JOIN` or subqueries. |

#### **Example Fix:**
```sql
-- Slow (scans all rows)
SELECT * FROM users WHERE name LIKE '%john%';

-- Faster (uses prefix index, if one exists)
SELECT * FROM users WHERE name LIKE 'john%';
```

---

### **3.3 Inefficient Joins**
**Symptom:** High memory usage or `Nested Loop`/`Hash Join` with high cost in `EXPLAIN`.

#### **Debugging Steps:**
1. **Analyze Join Order**:
   ```sql
   EXPLAIN ANALYZE
   SELECT u.name, o.order_date
   FROM users u JOIN orders o ON u.id = o.user_id;
   ```
   - Look for expensive joins (e.g., `Hash Join  (cost=10000.00)`).

2. **Optimizations**:
   - **Join on Indexed Columns**: Ensure `u.id` and `o.user_id` are indexed.
   - **Merge Joins Over Hash Joins**:
     ```sql
     -- Force merge join (PostgreSQL)
     SELECT /*+ Merge(u o) */ u.name, o.order_date FROM users u JOIN orders o ON u.id = o.user_id;
     ```
   - **Reduce Join Size**: Filter early with `WHERE` clauses.

#### **Code Example (Avoiding Cartesian Products):**
```sql
-- Bad: Missing join condition → Cartesian product
SELECT * FROM users, orders;

-- Good: Explicit JOIN with condition
SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id;
```

---

### **3.4 Large Result Sets & Sorting**
**Symptom:** High memory usage or slow `Sort` operations in `EXPLAIN`.

#### **Fixes:**
1. **Limit Results Early**:
   ```sql
   SELECT id, name FROM users ORDER BY name LIMIT 1000;
   ```
2. **Use `EXISTS` Instead of `IN` for Subqueries**:
   ```sql
   -- Slow (transfers large result set)
   SELECT * FROM users WHERE id IN (SELECT user_id FROM orders);

   -- Faster (stops at first match)
   SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
   ```
3. **Batch Processing** (for paginated results):
   ```python
   # Process in chunks (e.g., 1000 records at a time)
   offset = 0
   while True:
       results = cursor.execute("SELECT * FROM large_table LIMIT 1000 OFFSET %s", (offset,))
       if not results.fetchone():
           break
       offset += 1000
   ```

---

### **3.5 Parameterized Queries vs. Dynamic SQL**
**Symptom:** Repeated query plans due to dynamic SQL.

#### **Fix:**
- **Use Parameterized Queries** (allows query plan reuse):
  ```python
  # Slow (new plan every time)
  cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

  # Fast (plan cached)
  cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
  ```
- **For Dynamic Columns**: Use a whitelist of allowed columns:
  ```python
  allowed_cols = {'id', 'name', 'email'}
  if column in allowed_cols:
      cursor.execute("SELECT %s FROM users WHERE id = %s", (column, user_id))
  ```

---

## **4. Debugging Tools & Techniques**

### **4.1 Query Profiling Tools**
| Tool | Purpose | Example Command |
|------|---------|-----------------|
| **PostgreSQL `EXPLAIN ANALYZE`** | Detailed query plan with execution stats. | `EXPLAIN ANALYZE SELECT * FROM table;` |
| **MySQL `EXPLAIN`** | Query optimization guide. | `EXPLAIN SELECT * FROM table WHERE id = 1;` |
| **SQL Server `SET SHOWPLAN_TEXT`** | Estimated vs. actual execution plans. | `SET SHOWPLAN_TEXT ON; GO` |
| **Database-Specific Profilers** | Continuous monitoring (e.g., pgBadger, Percona PMM). | Configure in `postgresql.conf`. |

### **4.2 Slow Query Logs**
- **PostgreSQL**:
  ```conf
  # postgresql.conf
  slow_query_log = on
  slow_query_threshold = 100ms
  ```
- **MySQL**:
  ```sql
  SET GLOBAL slow_query_log = 'ON';
  SET GLOBAL long_query_time = 1;
  ```

### **4.3 Application-Level Monitoring**
- **Logging Query Performance**:
  ```python
  import logging
  import time

  def log_query_time(query, cursor):
      start = time.time()
      cursor.execute(query)
      duration = time.time() - start
      logging.warning(f"Query took {duration:.4f}s: {query}")
  ```
- **APM Tools** (e.g., New Relic, Datadog) to track slow DB calls.

### **4.4 Index Optimization Tools**
- **PostgreSQL**: `pg_stat_user_indexes` (checks index usage).
  ```sql
  SELECT schemaname, tablename, indexname, idx_scan
  FROM pg_stat_user_indexes;
  ```
- **MySQL**: `SHOW INDEX FROM table;` (identify unused indexes).

---

## **5. Prevention Strategies**

### **5.1 Index Management**
- **Avoid Over-Indexing**: Each index adds write overhead.
- **Regularly Review Indexes**:
  ```sql
  -- PostgreSQL: Find unused indexes
  SELECT schemaname, tablename, indexname
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0
  AND n_live_tup > 0;
  ```
- **Use Partial Indexes** (for filtered data):
  ```sql
  CREATE INDEX idx_active_users ON users(id) WHERE is_active = true;
  ```

### **5.2 Query Standards**
- **Enforce SARGable Queries**: Only allow queries that use indexes.
- **Use Query Templates**: Standardize frequently used queries.
- **Avoid `SELECT *`**: Always specify columns.

### **5.3 Database Configuration**
- **Optimize `work_mem`** (PostgreSQL) for joins/sorts.
  ```conf
  # postgresql.conf
  work_mem = 16MB  # Adjust based on query complexity
  ```
- **Enable Query Caching**:
  ```sql
  -- PostgreSQL: Share plans for similar queries
  SET enable_seqscan = off; -- Force index usage (if safe)
  ```

### **5.4 Testing & CI Integration**
- **Performance Test in CI**:
  ```yaml
  # Example GitHub Actions step
  jobs:
    test-performance:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - run: |
            pgbench -i -s 100 database  # Load test data
            pgbench -c 10 -T 60 database  # Run benchmark
  ```
- **Canary Deployments**: Test slow query fixes in staging before production.

### **5.5 Schema Design**
- **Normalize for Reads, Denormalize for Writes**: Use views or materialized views.
  ```sql
  -- Materialized view for slow aggregate queries
  CREATE MATERIALIZED VIEW mv_monthly_sales AS
  SELECT user_id, SUM(amount) AS total
  FROM sales
  GROUP BY user_id;

  -- Refresh periodically
  REFRESH MATERIALIZED VIEW mv_monthly_sales;
  ```

---

## **6. Summary Checklist for Quick Resolution**
| Step | Action |
|------|--------|
| 1 | Check `EXPLAIN ANALYZE` for full scans or expensive operations. |
| 2 | Add missing indexes (prioritize high-selectivity columns). |
| 3 | Rewrite queries to use indexes (SARGable predicates). |
| 4 | Optimize joins (ensure indexed columns, batch processing if needed). |
| 5 | Enable slow query logs and review top offenders. |
| 6 | Test fixes in staging before production. |
| 7 | Monitor post-deployment for regression. |

---
**Final Note**: Performance tuning is iterative. Start with the most expensive queries, validate fixes, and repeat. Always correlate database metrics with application behavior.