# **Debugging Conditional Aggregates with `FILTER` and `CASE WHEN` in SQL: A Troubleshooting Guide**

## **Introduction**
When working with conditional aggregates (e.g., revenue by payment method, error counts by type), poor execution can lead to inefficient queries, excessive CPU/memory usage, or even timeouts. This guide helps you diagnose and resolve common performance and logical issues with `FILTER`, `CASE WHEN`, and similar patterns.

---

## **1. Symptom Checklist**
Before diving into fixes, identify if your query suffers from any of these symptoms:

### **Performance-Related Symptoms**
- [ ] The database generates **multiple subqueries for filtering** (e.g., three separate `SUM()` calls for different payment methods).
- [ ] The query execution plan shows **nested loops, hash joins, or sequential scans** on large tables.
- [ ] **Memory pressure** (OOM errors) during aggregation, especially with `GROUP BY` + `CASE WHEN`.
- [ ] **Slow response times** when adding new conditional branches (e.g., `CASE WHEN` grows, performance degrades).
- [ ] **High tempdb usage** (sort operations in `GROUP BY` or `ORDER BY`).

### **Logical/Functional Symptoms**
- [ ] **Incorrect results** (e.g., zeroes where expected values appear, or reverse logic).
- [ ] **Missing rows** in the output due to misapplied `WHERE` or `CASE WHEN`.
- [ ] **Duplicates in aggregated results** due to improper `DISTINCT` or `GROUP BY`.

---

## **2. Common Issues and Fixes**

### **Issue 1: Multiple Queries for Filtered Aggregates**
**Symptoms:**
- Three separate `SUM(revenue)` calls for card, PayPal, bank transfers.
- Query plan shows **duplicate filtering logic** (e.g., `WHERE payment_method = 'card'` repeated three times).

**Root Cause:**
Manual `CASE WHEN` or multiple `UNION`/`UNION ALL` queries force the database to process each branch separately.

**Fix: Use `FILTER` (Modern SQL) or `CASE WHEN` with `GROUP BY`**
```sql
-- Bad (multiple subqueries)
SELECT SUM(revenue) AS card_revenue FROM transactions WHERE payment_method = 'card';
SELECT SUM(revenue) AS paypal_revenue FROM transactions WHERE payment_method = 'paypal';
-- ...

-- Better (single query with FILTER in SQL Server 2022+)
SELECT
    SUM(revenue) FILTER (WHERE payment_method = 'card') AS card_revenue,
    SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS paypal_revenue
FROM transactions;

-- Works in older SQL (CASE + GROUP BY)
SELECT
    SUM(CASE WHEN payment_method = 'card' THEN revenue ELSE 0 END) AS card_revenue,
    SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE 0 END) AS paypal_revenue
FROM transactions;
```

**Optimization Tip:**
- If using `CASE WHEN`, **include all branches** to prevent null/zero mismatches.
- For **MySQL/MSSQL**, `FILTER` is faster than `CASE WHEN` in large datasets.

---

### **Issue 2: Complex UNION Queries for Breakdowns**
**Symptoms:**
- A `UNION` of `SELECT` statements with different `WHERE` clauses.
- High **local temporary table** usage in the plan.

**Root Cause:**
Each `UNION` branch forces a full scan and merge sort.

**Fix: Pivot with `CASE WHEN` + `GROUP BY`**
```sql
-- Bad (UNION approach)
SELECT 'card' AS method, SUM(revenue) AS amount FROM transactions WHERE payment_method = 'card'
UNION ALL
SELECT 'paypal', SUM(revenue) FROM transactions WHERE payment_method = 'paypal';

-- Better (single query)
SELECT
    CASE WHEN payment_method = 'card' THEN 'card'
         WHEN payment_method = 'paypal' THEN 'paypal' END AS method,
    SUM(revenue) AS amount
FROM transactions
GROUP BY
    CASE WHEN payment_method = 'card' THEN 'card'
         WHEN payment_method = 'paypal' THEN 'paypal' END;
```

**Optimization Tip:**
- **Avoid `UNION ALL` unless necessary** (use `UNION` only if duplicates exist).
- **Filter early** (e.g., `WHERE payment_method IN ('card', 'paypal')`) before `GROUP BY`.

---

### **Issue 3: Application-Side Pivot Logic**
**Symptoms:**
- Database returns all rows, and the app filters/calculates aggregations in code.
- High **network latency** due to large datasets.

**Root Cause:**
Shifting aggregation logic to the application bypasses database optimizations.

**Fix: Push Logic to the Database**
```python
# Bad (app-side pivot)
df = db.query("SELECT * FROM transactions")
pivoted = df.pivot_table(index='date', columns='payment_method', values='revenue', aggfunc='sum')

# Better (database handles aggregation)
SELECT
    date,
    SUM(CASE WHEN payment_method = 'card' THEN revenue ELSE 0 END) AS card_revenue,
    SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE 0 END) AS paypal_revenue
FROM transactions
GROUP BY date;
```

**Optimization Tip:**
- **Use stored procedures** for complex pivots to avoid N+1 queries.
- **Leverage window functions** (`RANK()`, `DENSE_RANK()`) if ordering matters.

---

### **Issue 4: `CASE WHEN` Performance Degradation**
**Symptoms:**
- Adding a new `CASE WHEN` branch **dramatically slows down** the query.
- The query plan **changes from hash aggregate to sort merge**.

**Root Cause:**
`CASE WHEN` inside `SUM()` forces **per-row evaluation**, increasing I/O.

**Fix: Pre-filter with `JOIN` or `WHERE`**
```sql
-- Bad (inefficient CASE in SUM)
SELECT
    SUM(CASE WHEN status = 'success' THEN amount ELSE 0 END) AS success_amount,
    SUM(CASE WHEN status = 'failed' THEN amount ELSE 0 END) AS failed_amount
FROM orders;

-- Better (filter first, then aggregate)
SELECT
    SUM(amount) AS success_amount,
    COUNT(*) AS failed_amount
FROM orders
WHERE status = 'success';

-- Combine with window functions (PostgreSQL/Oracle)
SELECT
    status,
    SUM(amount) AS total_amount,
    COUNT(*) AS order_count
FROM orders
GROUP BY status;
```

**Optimization Tip:**
- **Use `PARTITION BY` with `SUM()`** for multi-level aggregations.
- **Materialized views** (PostgreSQL) or **indexed views** (SQL Server) can cache expensive pivots.

---

### **Issue 5: Incorrect Aggregation Results**
**Symptoms:**
- **Missing rows** in output.
- **Null/zero values** where expected values appear.
- **Incorrect grouping** due to `CASE WHEN` logic.

**Root Cause:**
- **Missing `ELSE 0`** in `CASE WHEN`.
- **Improper `GROUP BY` alignment** with `CASE`.
- **Hidden NULLs** in grouped columns.

**Fix: Validate Logic and Grouping**
```sql
-- Ensure all branches are covered (no missing ELSE)
SELECT
    SUM(CASE WHEN payment_method = 'card' THEN revenue ELSE 0 END) AS card_revenue,
    SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE 0 END) AS paypal_revenue
FROM transactions;

-- Debug: Check for NULLs in grouped columns
SELECT COUNT(*), COUNT(payment_method)
FROM transactions
WHERE payment_method IS NULL;
```

**Optimization Tip:**
- **Use `COALESCE`** to handle NULLs in `GROUP BY`.
- **Test with `LIMIT`** to verify small subsets before full runs.

---

## **3. Debugging Tools and Techniques**

### **Query Execution Plan Analysis**
- **SQL Server:** `SET STATISTICS IO, TIME ON;`
- **PostgreSQL:** `EXPLAIN ANALYZE`
- **MySQL:** `EXPLAIN FORMAT=JSON`
- **Look for:**
  - **Nested loops** (bad for large tables).
  - **Sort operations** (high memory usage).
  - **Duplicate filtering** (multiple `SUM()` calls).

### **Performance Tuning Steps**
1. **Check Indexes:**
   - Ensure `payment_method`, `status`, and `date` are indexed if used in `WHERE`/`GROUP BY`.
   - Run `ANALYZE TABLE` (MySQL) or `UPDATE STATISTICS` (SQL Server).

2. **Test with Smaller Data:**
   ```sql
   -- Debug by sampling 1% of data
   SELECT * FROM transactions TABLESAMPLE SYSTEM(1);
   ```

3. **Compare `CASE WHEN` vs. `FILTER`:**
   - In SQL Server 2022+, `FILTER` is often faster:
     ```sql
     SELECT SUM(revenue) FILTER (WHERE payment_method = 'card') AS card_revenue
     FROM transactions;
     ```

4. **Use `WITH` (CTE) for Readability:**
   ```sql
   WITH filtered_transactions AS (
       SELECT * FROM transactions
       WHERE payment_method IN ('card', 'paypal')
   )
   SELECT
       SUM(CASE WHEN payment_method = 'card' THEN revenue ELSE 0 END) AS card_revenue
   FROM filtered_transactions;
   ```

---

## **4. Prevention Strategies**

### **Design-Time Best Practices**
1. **Prefer `FILTER` over `CASE WHEN`** (SQL Server 2022+).
2. **Avoid `UNION`/`UNION ALL`** for conditional aggregations.
3. **Use `PARTITION BY`** for multi-level groupings:
   ```sql
   SELECT
       date,
       payment_method,
       SUM(amount) AS total_sales
   FROM sales
   GROUP BY date, payment_method;
   ```

### **Development-Time Checks**
- **Test Edge Cases:**
  - Empty tables.
  - NULL values in grouped columns.
  - New `CASE WHEN` branches.
- **Benchmark Changes:**
  - Compare old vs. new query performance.
  - Use `EXECUTE AS` to check permissions (if applicable).

### **Deployment-Time Safeguards**
- **Use Query Store (SQL Server)** to track regression.
- **Set Up Alerts** for slow queries:
  ```sql
  -- SQL Server Alert for queries > 5s
  CREATE EVENT SESSION [LongRunningQueries] ON SERVER
  ADD EVENT sqlserver.sql_statement_completed
  WHERE duration > 5000000;
  ```

---

## **Conclusion**
Conditional aggregates with `FILTER`/`CASE WHEN` are powerful but require careful tuning. Focus on:
1. **Eliminating redundant filtering** (use `FILTER` or pre-filtering).
2. **Avoiding `UNION` for pivots** (use `CASE WHEN` + `GROUP BY`).
3. **Debugging with execution plans** (watch for nested loops/sorts).
4. **Preventing NULL/zero issues** (include all `CASE` branches).

By following this guide, you can resolve performance bottlenecks and ensure accurate conditional aggregations.