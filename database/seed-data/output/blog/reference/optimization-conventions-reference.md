---
# **[Pattern] Optimization Conventions Reference Guide**
*Standardized practices for efficient query execution and data processing in [System Name]*

---

## **Overview**
Optimization Conventions define a set of **consistent rules** for structuring queries, indexing, and data access patterns to improve performance, reduce overhead, and ensure predictable behavior in [System Name]. This pattern ensures that:
- Queries are **scannable** and **maintainable** by developers and analysts.
- Indexes and materialized views are **strategically applied** to avoid unnecessary full-table scans.
- Data processing **avoids anti-patterns** (e.g., `SELECT *`, `NOT IN` clauses, or nested subqueries).

These conventions apply to **SQL queries, API calls, and application-layer optimizations**, covering use cases like reporting, analytics, and transactional workloads.

---

## **Key Concepts**
| Concept               | Definition                                                                                     | Purpose                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Query Granularity** | Limiting fetched columns (`SELECT column1, column2`) vs. `SELECT *`.                        | Reduces network overhead and memory usage.                                               |
| **Index Selection**   | Prefer indexed columns in `WHERE`, `JOIN`, or `ORDER BY` clauses.                           | Speeds up data retrieval; avoids full scans.                                             |
| **Batch Processing**  | Using `BULK INSERT`, `MERGE`, or batch API calls instead of row-by-row operations.          | Reduces transaction log bloat and improves throughput.                                      |
| **Pagination**        | Implementing `LIMIT/OFFSET` or keyset pagination (`WHERE id > last_id`) instead of loading all rows. | Lowers memory pressure and improves responsiveness.                                      |
| **Materialized Views**| Pre-computing aggregations or joins for repeated queries.                                   | Offloads computation at query time.                                                        |
| **Query Hints**       | Explicitly guiding the query optimizer (e.g., `FORCE INDEX`).                                 | Ensures consistent performance when the optimizer’s choices are unpredictable.           |
| **Data Partitioning** | Structuring tables by date, region, or tenant to limit scanned data.                        | Accelerates queries filtering on partition keys.                                          |

---

## **Schema Reference**
Optimization conventions apply to **tables, indexes, and constraints**. Below are key schema components and their optimization implications.

### **1. Table Design**
| Attribute          | Recommended Format                          | Example                          | Why?                                                                                     |
|--------------------|---------------------------------------------|----------------------------------|-----------------------------------------------------------------------------------------|
| **Primary Key**    | Unique, non-nullable, indexed (e.g., `ID INT PRIMARY KEY`). | `PRIMARY KEY (customer_id, created_at)` | Enables fast lookups; supports time-series partitioning.                                |
| **Foreign Keys**   | Indexed references to avoid full scans.      | `FOREIGN KEY (user_id) REFERENCES users(id)` | Optimizes joins; reduces join overhead.                                                 |
| **Partitioning Key** | High-cardinality, frequent filter column.  | `PARTITION BY RANGE (YEAR(order_date))` | Speeds up range-based queries.                                                            |
| **Avoid `SELECT *`** | Explicitly list columns.                   | `SELECT col1, col2 FROM table`     | Reduces I/O and memory; improves query planning.                                         |

### **2. Indexes**
| Index Type          | Use Case                                      | Example Command                          | Notes                                                                                   |
|---------------------|-----------------------------------------------|------------------------------------------|----------------------------------------------------------------------------------------|
| **B-tree Index**    | Equality/range scans on single columns.       | `CREATE INDEX idx_name ON table(name);`   | Default choice; efficient for most queries.                                           |
| **Composite Index** | Multi-column filters (`WHERE a = X AND b = Y`). | `CREATE INDEX idx_a_b ON table(a, b);`    | Order columns by selectivity (most selective first).                                     |
| **Covering Index**  | Include all columns needed for a query.       | `CREATE INDEX idx_cover ON table(col1, col2)` | Eliminates table access; speeds up `SELECT` statements with `WHERE` on index columns.  |
| **Full-Text Index** | Text search operations.                       | `CREATE FULLTEXT INDEX idx_search ON table(content);` | Optimized for `LIKE '%term%'` or `CONTAINS` queries.                                    |
| **Hash Index**      | Exact-match lookups (e.g., caches, sessions). | *(Not natively supported in all DBs; use in-memory structures like Redis.)* | Low-latency for point queries.                                                          |

### **3. Constraints**
| Constraint          | Optimization Impact                                   | Example                                                                 |
|---------------------|-------------------------------------------------------|-------------------------------------------------------------------------|
| **UNIQUE**          | Guarantees no duplicates; often uses an implicit index. | `ALTER TABLE orders ADD UNIQUE (email);`                              |
| **CHECK**           | Reduces invalid data early; may use index hints.       | `ALTER TABLE users ADD CHECK (age > 0);`                               |
| **NOT NULL**        | Avoids NULL handling overhead in joins/aggregations.    | `ALTER TABLE logs ADD COLUMN status VARCHAR(10) NOT NULL;`              |

---

## **Query Examples**
### **1. Optimized SELECT**
✅ **Best Practice:**
```sql
-- Fetches only needed columns; uses indexed join.
SELECT user_id, order_count, total_spent
FROM (
    SELECT
        user_id,
        COUNT(*) AS order_count,
        SUM(amount) AS total_spent
    FROM orders
    WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31'
    GROUP BY user_id
    HAVING COUNT(*) > 5
) AS user_stats
WHERE user_id IN (SELECT id FROM premium_users);
```
❌ **Anti-Pattern:**
```sql
-- Unnecessary columns, full table scan, `NOT IN` (expensive).
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM orders);
```

---

### **2. Batch Insert/Update**
✅ **Best Practice (Bulk API):**
```http
POST /api/bulk-orders
Content-Type: application/json
{
    "orders": [
        {"user_id": 1, "item": "A", "quantity": 2},
        {"user_id": 2, "item": "B", "quantity": 1}
    ]
}
```
❌ **Anti-Pattern (Row-by-Row):**
```python
for item in cart:
    db.execute("INSERT INTO orders VALUES (?, ?, ?)", user_id, item, quantity)
```

---

### **3. Pagination**
✅ **Keyset Pagination (Efficient):**
```sql
-- Uses existing index; avoids OFFSET overhead.
SELECT * FROM products
WHERE id > 1000
ORDER BY id
LIMIT 50;
```
❌ **Offset Pagination (Inefficient):**
```sql
-- Triggers full rescan for `OFFSET 1000` rows.
SELECT * FROM products ORDER BY id LIMIT 50 OFFSET 1000;
```

---

### **4. Materialized Views**
✅ **Pre-Computed Aggregation:**
```sql
-- Refresh daily via job; query is instant.
CREATE MATERIALIZED VIEW daily_sales AS
SELECT
    date_trunc('day', order_time) AS day,
    SUM(amount) AS revenue
FROM orders
GROUP BY 1;

-- Query:
SELECT * FROM daily_sales WHERE day = '2023-10-01';
```
❌ **Computed on the Fly:**
```sql
-- Scans `orders` table repeatedly; slow for large datasets.
SELECT SUM(amount) FROM orders WHERE order_time BETWEEN '2023-10-01' AND '2023-10-01';
```

---

### **5. JOIN Optimization**
✅ **Small-to-Large Join:**
```sql
-- Forces the smaller table (`users`) to drive the join.
SELECT u.name, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.order_date > '2023-01-01';
```
❌ **Large-to-Small Join (Anti-Pattern):**
```sql
-- Scans `orders` first; inefficient if `users` is small.
SELECT u.name, o.amount
FROM orders o
INNER JOIN users u ON o.user_id = u.id
WHERE o.order_date > '2023-01-01';
```

---

## **Advanced Techniques**
| Technique               | When to Use                                      | Example                                                                 |
|-------------------------|--------------------------------------------------|-------------------------------------------------------------------------|
| **Query Hints**         | Bypass optimizer for predictable plans.          | `SELECT /*+ INDEX(t orders_idx) */ * FROM orders;`                    |
| **Partition Pruning**   | Filter data by partition key.                   | `SELECT * FROM sales PARTITION (p_2023)`;                              |
| **Window Functions**    | Replace self-joins for rankings/aggregations.    | `SELECT *, RANK() OVER (ORDER BY score DESC) FROM leaders;`             |
| **CTEs (WITH Clause)**  | Break complex queries into logical stages.       | `WITH filtered_orders AS (...)` SELECT * FROM filtered_orders WHERE ...;` |

---

## **Query Anti-Patterns to Avoid**
| Pattern               | Problem                                                                 | Solution                                                                 |
|-----------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **`SELECT *`**        | Excessive data transfer; slow parsing.                                   | Explicitly list columns.                                                 |
| **`NOT IN`/`NOT EXISTS`** | Expensive; can’t use indexes effectively.                          | Rewrite as `LEFT JOIN ... IS NULL`.                                      |
| **Unbounded `LIKE`** | Full-table scans (e.g., `LIKE '%term%'`).                               | Use full-text indexes or prefix searches (`LIKE 'term%'`).                |
| **Nested Subqueries** | Performance hits for correlated subqueries.                              | Use JOINs or lateral joins.                                               |
| **Large Temporary Tables** | High memory usage; slow writes.                     | Use temporary tables with constraints or process in batches.               |

---

## **Validation & Monitoring**
### **1. Query Performance Checklist**
Before deploying:
1. **Use `EXPLAIN`** to analyze execution plans:
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM users WHERE email = 'test@example.com';
   ```
   - Check for **full scans**, **missing indexes**, or **inefficient joins**.
2. **Monitor Slow Queries**:
   - Enable database slow-log (e.g., MySQL’s `slow_query_log`).
   - Set a threshold (e.g., >500ms) for alerts.

### **2. Index Maintenance**
- **Update statistics**:
  ```sql
  ANALYZE TABLE table_name;
  ```
- **Add/drop indexes** based on usage:
  ```sql
  -- Check usage first:
  SELECT * FROM pg_stat_user_indexes; -- PostgreSQL
  -- Or enable `pg_stat_statements` for per-query stats.
  ```

### **3. API Layer Optimization**
- **Cache frequent queries** (e.g., Redis for dashboard data).
- **Implement rate-limiting** to avoid resource exhaustion.

---

## **Related Patterns**
| Pattern                          | Purpose                                                                 | When to Use                                                                 |
|----------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **[Index-Strategy Pattern]**      | Guidelines for creating indexes based on query patterns.               | When optimizing read-heavy workloads.                                       |
| **[Batch Processing Pattern]**   | Designing APIs/ETL pipelines for bulk operations.                     | For high-throughput data ingestion.                                        |
| **[Partitioning Strategy]**      | Structuring tables for large-scale data by time/tenant/region.         | When tables exceed 100M rows or queries filter on specific dimensions.       |
| **[Materialized View Pattern]**  | Pre-computing aggregations for analytical queries.                     | For dashboards/reports with repeated complex calculations.                 |
| **[Pagination Pattern]**         | Efficiently fetching large result sets.                                | For infinite scroll or data tables with >10k rows.                         |

---
## **Tooling Support**
| Tool/Feature               | Purpose                                                                 | Example                                                                     |
|----------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Database-Level**         |                                                                         |                                                                           |
| `EXPLAIN`                  | Analyze query execution plans.                                           | `EXPLAIN SELECT * FROM large_table WHERE id = 1;`                          |
| Slow Query Log             | Log queries exceeding a threshold.                                       | MySQL: `slow_query_log = 1`, `long_query_time = 1`                        |
| **Application-Level**     |                                                                         |                                                                           |
| Query Profiler (e.g., DBeaver, pgAdmin) | Visualize slow queries.           | Identify N+1 query anti-patterns in ORMs.                                  |
| API Gateway (Kong, Envoy)  | Cache responses for identical requests.                                 | `Cache-Control: max-age=300` for GET /reports?date=2023-10-01              |
| **Third-Party**            |                                                                         |                                                                           |
| Percona PMM / Datadog      | Monitor query performance at scale.                                     | Alert on `max_execution_time > 2s`.                                       |
| pgBadger / MySQLTuner     | Analyze slow logs for common issues.                                    | Detects missing indexes or full scans.                                    |

---
## **Troubleshooting**
| Issue                          | Root Cause                                  | Solution                                                                 |
|--------------------------------|---------------------------------------------|--------------------------------------------------------------------------|
| **Full Table Scans**           | Missing indexes or poor query structure.    | Add indexes, rename columns for better selectivity, or use `FORCE INDEX`. |
| **High Latency on JOINs**      | Large tables joined ineffectively.          | Use `EXPLAIN` to identify the smaller driver table; consider denormalization. |
| **Memory Pressure**            | `SELECT *` or unsorted data in `LIMIT`.     | Fetch only needed columns; sort data before pagination.                 |
| **Lock Contention**            | Long-running transactions.                  | Break into smaller transactions; use optimistic locking.                  |
| **Stale Materialized Views**   | Views not refreshed.                        | Schedule refresh jobs (e.g., cron + `REFRESH MATERIALIZED VIEW`).        |

---
## **Best Practices Summary**
1. **Default to Explicit**: Always specify columns in `SELECT`, `INSERT`, etc.
2. **Index Strategically**: Cover all `WHERE`, `JOIN`, and `ORDER BY` columns.
3. **Avoid Anti-Patterns**: Never use `SELECT *`, `NOT IN`, or unbounded `LIKE`.
4. **Leverage Batching**: Use bulk APIs or batch processing for writes.
5. **Monitor & Profile**: Enable slow logs and review execution plans regularly.
6. **Denormalize Judiciously**: Pre-aggregate data for read-heavy workloads.
7. **Partition Early**: Plan for scale by partitioning tables upfront.