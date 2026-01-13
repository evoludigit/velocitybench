# **[Pattern] EXPLAIN ANALYZE Workflow Reference Guide**

---

## **Overview**
The **EXPLAIN ANALYZE** workflow is a systematic approach to identifying and optimizing slow-performing SQL queries in PostgreSQL (and other database engines that support `EXPLAIN`). This pattern involves analyzing query execution plans using `EXPLAIN` (or `EXPLAIN ANALYZE` for runtime statistics) to diagnose bottlenecks, then refining indexes, query structures, or database configuration until optimal performance is achieved.

The workflow follows these iterative steps:
1. **Capture Execution Plan** – Use `EXPLAIN` to inspect the logical flow of a query.
2. **Identify Bottlenecks** – Look for high-cost operations (e.g., full table scans, inefficient joins, or sequential I/O).
3. **Refine with `EXPLAIN ANALYZE`** – Execute with actual runtime data to validate assumptions.
4. **Optimize** – Adjust queries, indexes, or configuration (e.g., `pg_hint_plan`, `SET` variables).
5. **Revalidate** – Repeat `EXPLAIN ANALYZE` to confirm improvements.

This pattern is critical for database tuning, reducing latency, and cost savings in large-scale applications.

---

## **Schema Reference**
Below are common elements in execution plans (PostgreSQL-specific):

| **Field**               | **Description**                                                                 | **Key Values/Flags**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Seq Scan**            | Sequential full table scan.                                                     | `cost=X seq_page` (high `cost` indicates inefficiency).                              |
| **Index Scan**          | Uses an index (preferred over sequential scans).                                | `using index_name` + `cost` (lower is better).                                     |
| **Hash Join / Merge Join** | Join algorithms (Hash Join is faster for large tables).                         | `Join Filter` percentage indicates selectivity.                                      |
| **Bitmap Heap Scan**    | Combines index scan with bitmap filtering (use with caution).                   | `cost=X bitmap heap` (often expensive for post-filtering).                           |
| **NestLoop**            | Nested-loop join (default for small tables).                                    | `cost=X` (can become slow with large tables).                                       |
| **Sort**                | Temporary sort operation (avoid with proper indexes).                           | `cost=X sort` (high `sort cost` suggests missing `ORDER BY` index).                |
| **Function Scan**       | Scans a function (e.g., `unnest()`).                                          | Often inefficient; consider restructuring.                                         |
| **Aggregate**           | GROUP BY or window functions.                                                   | Check `HashAggregate` vs. `SortAggregate` (hash is faster if no ordering).          |
| **Filter**              | WHERE clause filtering (high cost suggests poor selectivity).                   | `Filter: (condition)` (low `filter`% means many rows pass through).                 |
| **Parallel Worker**     | Parallel query execution (PostgreSQL 10+).                                     | `Parallel Workers: N` (higher N = better for large scans, but adds overhead).     |
| **Planner Notes**       | PostgreSQL’s internal hints (e.g., `Plan (cost=X..Y rows=N)`).                  | Useful for debugging `pg_hint_plan` directives.                                      |

---

## **Query Examples**
### **1. Basic EXPLAIN (Logical Plan)**
```sql
EXPLAIN
SELECT user_id, COUNT(*)
FROM orders
WHERE order_date > '2023-01-01'
GROUP BY user_id;
```
**Output Highlights:**
- If `Seq Scan` on `orders`, add an index on `(order_date)` or `(user_id, order_date)`.
- If `HashAggregate`, ensure `GROUP BY` is supported by an index.

---

### **2. EXPLAIN ANALYZE (Runtime Statistics)**
```sql
EXPLAIN ANALYZE
SELECT o.user_id, COUNT(DISTINCT p.product_id)
FROM orders o
JOIN order_items p ON o.order_id = p.order_id
WHERE o.order_date > '2023-01-01'
GROUP BY o.user_id;
```
**Key Metrics to Check:**
- **Actual Rows:** Does the plan match expectations? (e.g., `rows=1000` vs. `rows=1000000`).
- **Execution Time:** `actual time=123.456..123.458 ms` (target: < 100ms).
- **Join Algorithms:** Avoid `NestLoop` on large tables (replace with `Hash Join` via hints).

---

### **3. Forcing a Join Algorithm**
```sql
EXPLAIN ANALYZE
SELECT *
FROM large_table lt
JOIN small_table st ON lt.id = st.ref_id
/*+ HashJoin(lt st) */
WHERE lt.date > '2023-01-01';
```
**Use Case:** Force `Hash Join` for large tables to avoid expensive `Merge Join`.

---

### **4. Debugging Missing Indexes**
```sql
EXPLAIN ANALYZE
SELECT *
FROM sales
WHERE region = 'West'
ORDER BY sale_date DESC
LIMIT 100;
```
**If Output Shows:**
```
Sort  (cost=0.00..12345.67 rows=100 width=8) (actual time=500.123..500.124 ms)
  ->  Seq Scan on sales  (cost=0.00..1234.56 rows=1000 width=8)
        Filter: ((region)::text = 'West'::text)
```
**Solution:** Add a composite index:
```sql
CREATE INDEX idx_sales_region_date ON sales(region, sale_date DESC);
```

---

### **5. Analyzing Subqueries**
```sql
EXPLAIN ANALYZE
SELECT *
FROM (
    SELECT user_id, SUM(amount) as total
    FROM transactions
    WHERE user_id IN (
        SELECT id FROM users WHERE signup_date > '2022-01-01'
    )
    GROUP BY user_id
) AS subq;
```
**Optimization Tips:**
- Replace `IN (SELECT...)` with a join.
- Use `EXPLAIN` on the subquery separately to find bottlenecks.

---

## **Step-by-Step Workflow**
### **1. Capture the Plan**
Run `EXPLAIN` (or `EXPLAIN ANALYZE` for runtime data) on the slow query.

### **2. Identify Costly Operations**
- **Seq Scan?** → Add an index.
- **High `cost`?** → Refactor query or adjust statistics (`ANALYZE` table).
- **Join Filter < 1%?** → The WHERE clause eliminates most rows; consider early filtering.

### **3. Validate with `EXPLAIN ANALYZE`**
Compare estimated (`estimate`) vs. actual (`actual`) rows/times. If mismatched:
- Run `ANALYZE table_name` to update statistics.
- Use `pg_stat_statements` to track slow queries.

### **4. Optimize**
- **Add/Remove Indexes:** Use `pg_stat_user_indexes` to verify usage.
- **Rewrite Queries:** Avoid `SELECT *`, subqueries in WHERE, or functions on columns.
- **Hints:** Use `/*+ Hint */` sparingly (e.g., force `Index Scan`).
- **Configuration:** Adjust `work_mem`, `maintenance_work_mem`, or `effective_cache_size`.

### **5. Revalidate**
Repeat `EXPLAIN ANALYZE` to ensure improvements. Benchmark with `pgbench` or real-world loads.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Index Selection Guide](#)** | How to choose between single-column, composite, and partial indexes.           | When `EXPLAIN` shows `Seq Scan` or high `cost`.                                |
| **[Query Rewriting](#)**  | Techniques to optimize complex queries (e.g., CTEs, lateral joins).             | For nested subqueries or recursive queries.                                   |
| **[Partitioning](#)**     | Splitting tables by range/hash to improve scan efficiency.                     | For large tables with time-based or high-cardinality filters.                  |
| **[Materialized Views](#)** | Pre-aggregating data for read-heavy workloads.                                | When the same query runs frequently.                                           |
| **[Connection Pooling](#)** | Managing database connections to reduce overhead.                             | For high-concurrency applications.                                             |
| **[Vacuum & Analyze](#)** | Maintaining index and table statistics.                                      | When `EXPLAIN` estimates diverge from actual performance.                       |

---

## **Common Pitfalls**
1. **Ignoring `actual time` in `EXPLAIN ANALYZE`**:
   - A plan may look "good" (low estimated cost) but still be slow due to I/O bottlenecks.

2. **Over-indexing**:
   - Every index adds write overhead; monitor `pg_stat_user_indexes` for unused indexes.

3. **Assuming `Hash Join` is always better**:
   - For large tables with skewed data, `Merge Join` may perform better due to lower memory usage.

4. **Not updating statistics**:
   - Run `ANALYZE` after bulk inserts/deletes to keep `EXPLAIN` accurate.

5. **Using `EXPLAIN` without `ANALYZE`**:
   - Estimates can be wildly off; always prefer `EXPLAIN ANALYZE` in production.

---
## **Tools to Supplement**
- **pgMustard**: Visualizes execution plans (like Squirrel PLAN).
- **pexpect**: Automates `EXPLAIN` queries via scripts.
- **pg_stat_statements**: Tracks slow queries post-optimization.
- **Brief**: Explains query plans in plain English.