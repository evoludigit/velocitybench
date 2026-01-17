# **[Pattern] Query Planning and Optimization Reference Guide**

---

## **Overview**
Query planning and optimization is a core database pattern that enhances performance by precomputing efficient execution strategies (*query plans*) during compilation. These plans—cached in the query planner—are reused for identical or similar queries, reducing runtime overhead. The pattern leverages metadata (e.g., table statistics, indexes) and cost-based analysis to select the most efficient path (e.g., full scan vs. indexed lookup) while accounting for database-specific constraints (e.g., parallelism, memory limits).

Optimization techniques include:
- **Selection of joins** (hash joins, merge joins, nested loops).
- **Predicate pushdown** (filtering data early in execution).
- **Statistics-driven pruning** (discarding irrelevant branches via cost estimates).
- **Rule-based tuning** (prioritizing known efficient operations, e.g., index scans).

This pattern is applicable to relational databases (PostgreSQL, SQL Server), NoSQL systems (MongoDB, Cassandra), and data warehouses (Snowflake, BigQuery), where it mitigates performance bottlenecks by **minimizing runtime decision-making** and **maximizing plan reuse**.

---

## **Key Concepts & Implementation Details**

### **1. Query Plan Phases**
| Phase               | Description                                                                                                                                                                                                                     | Example Action                                                                                     |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Parsing**         | Validates syntax, maps keywords to operators (e.g., `SELECT` → `Scan`, `JOIN` → `JoinNode`).                                                                                                                 | Converts `SELECT * FROM users JOIN orders WHERE users.id = orders.user_id` to an abstract syntax tree (AST). |
| **Binding**         | Resolves references (e.g., table aliases, column names) to database objects using metadata (e.g., catalog, schema).                                                                                             | Maps `users.id` to the actual `user_id` column in the `users` table.                             |
| **Optimization**    | Reorders, rewrites, or eliminates operations based on heuristics and statistics (e.g., removing redundant predicates, converting correlated subqueries to joins).                                           | Rewrites `EXISTS` subquery into a `JOIN` with a `WHERE` clause.                                  |
| **Generation**      | Compiles the optimized plan into a sequence of execution steps (e.g., `SeqScan` → `Sort` → `HashJoin`).                                                                                                       | Produces a physical plan: `SeqScan(users) → Join(orders, user_id=users.id) → Filter(orders.total > 100)`. |
| **Caching**         | Stores plans (e.g., in a plan cache) to avoid reprocessing identical queries.                                                                                                                                      | PostgreSQL’s `plancache` or SQL Server’s `Query Store` holds plans for 5 minutes by default.      |

---

### **2. Optimization Techniques**
| Technique               | Description                                                                                                                                                                                                                     | When to Use                                                                                         |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Statistics Collection** | Gathers metadata (e.g., row counts, histogram distributions) to estimate query costs.                                                                                                                          | Before plan generation (e.g., `ANALYZE` in PostgreSQL, `UPDATE STATISTICS` in SQL Server).        |
| **Index Selection**      | Chooses indexes to minimize I/O (e.g., `B-tree` for equality, `GIN` for text search).                                                                                                                                | Queries with `WHERE`, `JOIN`, or `ORDER BY` clauses.                                               |
| **Join Ordering**        | Determines the sequence of joins to minimize intermediate result sizes (e.g., Cartesian product risk).                                                                                                         | Multi-table joins (e.g., `A JOIN B JOIN C` vs. `A JOIN (B JOIN C)`).                              |
| **Predicate Pushdown**   | Applies filters (`WHERE`, `HAVING`) as early as possible (e.g., in a subquery or join).                                                                                                                            | Nested queries or views to reduce data early.                                                    |
| **Materialization**      | Pre-computes and stores intermediate results (e.g., Common Table Expressions, indexes).                                                                                                                        | Expensive subqueries or repeated computations.                                                     |
| **Parallelism**          | Distributes execution across threads/processes (e.g., hash partitions for joins).                                                                                                                                | Large datasets or CPU-bound operations.                                                            |
| **Rule-Based Rewrites**  | Applies predefined optimizations (e.g., converting `NOT IN` to `NOT EXISTS`).                                                                                                                                       | Legacy systems or queries with known inefficiencies.                                               |
| **Cost-Based Analysis**  | Weighs trade-offs (e.g., scan cost vs. join cost) using a cost model (e.g., I/O, CPU, memory).                                                                                                                   | Dynamic workloads where statistics fluctuate.                                                      |

---

### **3. Schema Considerations**
Optimization relies heavily on schema design. Key elements include:

| Component          | Description                                                                                                                                                                                                                     | Best Practices                                                                                      |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Indexes**        | Structures enabling fast lookups (e.g., `PRIMARY KEY`, `UNIQUE`, `BITMAP`).                                                                                                                                | Create indexes on `WHERE`, `JOIN`, and `ORDER BY` columns; avoid over-indexing.                     |
| **Partitioning**   | Splits tables by ranges, lists, or hashes to parallelize access.                                                                                                                                               | Use for large tables (e.g., `PARTITION BY RANGE (order_date)`).                                   |
| **Statistics**     | Database-maintained metadata (e.g., `pg_statistic` in PostgreSQL, `sys.dm_db_stats` in SQL Server).                                                                                                         | Run `ANALYZE` after schema changes or bulk data loads.                                             |
| **Constraints**    | `FOREIGN KEY`, `CHECK`, or `NOT NULL` to guide the planner.                                                                                                                                            | Enforce data integrity; avoid cascading updates that complicate plans.                             |
| **Data Types**     | Precision and storage impact performance (e.g., `VARCHAR(255)` vs. `TEXT`).                                                                                                                                     | Use appropriate types (e.g., `DATE` instead of `VARCHAR`).                                        |

---

## **Query Examples**

### **1. Basic Query Optimization**
**Before Optimization:**
```sql
-- Inefficient: Scan entire table twice for correlated subquery
SELECT name FROM users WHERE id IN (
    SELECT user_id FROM orders WHERE total > 100
);
```
**Optimized Plan:**
```sql
-- Rewritten as JOIN + predicate pushdown
JOIN(users, orders ON users.id = orders.user_id)
WHERE orders.total > 100
```
**Explanation:**
- The planner converts the subquery into a `JOIN`, reducing the full table scan to one pass.
- Uses an index on `(orders.user_id, orders.total)` if available.

---

### **2. Join Order Optimization**
**Schema:**
```sql
CREATE TABLE customers (id SERIAL PRIMARY KEY, name VARCHAR(100));
CREATE TABLE orders (id SERIAL PRIMARY KEY, customer_id INT REFERENCES customers(id), amount DECIMAL);
CREATE INDEX idx_orders_customer ON orders(customer_id);
```
**Original Query (Risky Join Order):**
```sql
-- May produce a Cartesian product if statistics are stale
SELECT c.name, o.amount
FROM customers c JOIN orders o ON c.id = o.customer_id;
```
**Optimized Query:**
```sql
-- Explicit join order hints (MySQL example)
SELECT c.name, o.amount
FROM custom_force_index(orders, idx_orders_customer) o
JOIN customers c ON o.customer_id = c.id;
```
**Explanation:**
- Joining `orders` (smaller table, indexed) first minimizes intermediate data.
- Hints (vendor-specific) override planner choices when statistics are unreliable.

---

### **3. Predicate Pushdown**
**Before:**
```sql
-- Full table scan + filter (inefficient for large data)
SELECT COUNT(*)
FROM (
    SELECT id FROM orders
) WHERE id > 1000;
```
**After:**
```sql
-- Push filter to subquery (better if executed as a scan with bounds)
SELECT COUNT(*)
FROM orders
WHERE id > 1000;
```
**Explanation:**
- The planner recognizes the subquery is redundant and pushes the predicate down.

---

### **4. Parallel Query Execution**
**Example (PostgreSQL):**
```sql
-- Force parallel execution for a large scan
EXPLAIN ANALYZE
SELECT * FROM large_table
WHERE column = 'value'
PARALLEL FORCE OFF;  -- Disable (default)
```
**Optimized with Parallelism:**
```sql
-- Enable parallelism (requires `work_mem` and `max_parallel_workers` tuning)
EXPLAIN ANALYZE
SELECT * FROM large_table
WHERE column = 'value'
PARALLEL FORCE ON;
```
**Output Plan:**
```
Parallel Seq Scan on large_table  (cost=0.00..100.00 rows=1000 width=100) (actual time=2.500..5.000 rows=500 loops=2)
  Parallel Workers: 2
```
**Explanation:**
- Divides the scan across 2 workers, reducing runtime from 8s → 5s.

---

## **Schema Reference**
| **Entity**               | **Description**                                                                                                                                                                                                                     | **Example Syntax**                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Statistics Table**     | Tracks column distribution (e.g., `pg_class`, `pg_stats` in PostgreSQL).                                                                                                                                                   | `SELECT attname, n_distinct FROM pg_stats WHERE tablename = 'users';`                                   |
| **Index**                | Accelerates access to specific columns.                                                                                                                                                                              | `CREATE INDEX idx_users_email ON users(email);`                                                          |
| **Materialized View**    | Pre-computes and stores results of complex queries.                                                                                                                                                                      | `CREATE MATERIALIZED VIEW mv_active_users AS SELECT * FROM users WHERE signup_date > '2023-01-01';`       |
| **Partition**            | Splits a table by key ranges/lists.                                                                                                                                                                               | `CREATE TABLE sales (id INT, revenue DECIMAL) PARTITION BY RANGE (id);`                               |
| **Query Plan Cache**     | Stores execution plans (e.g., PostgreSQL’s `plancache`).                                                                                                                                                               | `SHOW plancache_settings;`                                                                              |

---

## **Query Examples: Advanced Scenarios**

### **1. Handling Skewed Data**
**Problem:**
A `JOIN` between `users` (1M rows) and `orders` (10M rows) where 99% of `user_id` values are NULL (`user_id IS NULL`).
**Solution:**
```sql
-- Filter early to avoid processing NULLs
SELECT u.name, o.amount
FROM users u LEFT JOIN orders o ON u.id = o.user_id AND o.user_id IS NOT NULL;
```
**Optimized Plan:**
- Pushes `o.user_id IS NOT NULL` into the `JOIN` condition.

---

### **2. Dynamic SQL with Prepared Statements**
**Scenario:**
A stored procedure with varying filters (e.g., `WHERE department = ?`).
**Optimization:**
```sql
-- Cache plans for parameterized queries
PREPARE get_employees_by_dept(dept VARCHAR) AS
SELECT * FROM employees WHERE department = $1;
```
**Explanation:**
- The plan is reused for identical `dept` values, avoiding re-optimization.

---

### **3. Cost-Based vs. Rule-Based Optimization**
**Rule-Based (Legacy Systems):**
```sql
-- Rule: "Scan tables in ORDER BY column order"
SELECT name FROM users u JOIN orders o ON u.id = o.user_id ORDER BY u.name;
```
**Output Plan:**
- Always scans `users` first, then `orders`, regardless of statistics.

**Cost-Based (Modern Systems):**
```sql
-- Uses statistics to choose the cheaper path
SELECT name FROM users u JOIN orders o ON u.id = o.user_id ORDER BY u.name;
```
**Output Plan:**
- Chooses the join order based on `users.id` vs. `orders.user_id` cardinality.

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                                                                                     | **Synergy**                                                                                          |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Indexing Strategy]**          | Designs indexes to minimize I/O for common queries.                                                                                                                                                                            | Query planning uses indexes; this pattern ensures optimal indexes exist.                          |
| **[Table Partitioning]**        | Splits large tables to improve parallelism and maintenance.                                                                                                                                                               | Partition pruning reduces scan ranges in query plans.                                               |
| **[Query Caching]**              | Stores query results to avoid recomputation.                                                                                                                                                                            | Complements planning by reducing runtime for repeated queries.                                     |
| **[Materialized Views]**        | Pre-computes and stores aggregated data.                                                                                                                                                                              | Query planner may reuse materialized views instead of recalculating.                                |
| **[Statistics Maintenance]**     | Keeps metadata up-to-date for accurate cost estimation.                                                                                                                                                              | Poor statistics degrade plan quality; this pattern ensures accuracy.                               |
| **[Batch Processing]**           | Processes data in chunks to avoid locks/timeouts.                                                                                                                                                                        | Query plans can leverage partitioning for batch-friendly execution.                                  |
| **[Connection Pooling]**        | Reuses database connections to reduce overhead.                                                                                                                                                                         | Optimized plans benefit from consistent connection states.                                        |
| **[Query Rewriting]**            | Transforms queries into more efficient forms (e.g., `EXISTS` to `JOIN`).                                                                                                                                           | The planner’s rewrite rules implement this pattern.                                                |

---

## **Troubleshooting Common Issues**
| **Issue**                          | **Cause**                                                                                                                                                                                                                     | **Solution**                                                                                          |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Suboptimal Plan**                 | Outdated statistics or missed indexes.                                                                                                                                                                                | `ANALYZE table;` or `VACUUM ANALYZE;`; review `EXPLAIN ANALYZE`.                                    |
| **Plan Cache Overhead**             | Too many plans stored, increasing memory usage.                                                                                                                                                                        | Adjust `plancache_size` (PostgreSQL) or `query_store` settings (SQL Server).                        |
| **Parallelism Bottleneck**          | Too few workers or excessive coordination overhead.                                                                                                                                                                      | Increase `max_parallel_workers` and tune `work_mem`.                                                |
| **Join Order Heuristic Failure**    | Planner guesses incorrectly due to skewed data.                                                                                                                                                                       | Use `/*+ LEADING(table) */` hints (Oracle) or `OPTION (FORCE ORDER)` (SQL Server).                  |
| **Temp Table Spill**                | Query generates too much intermediate data for memory.                                                                                                                                                                    | Increase `work_mem` or rewrite query to reduce intermediate rows.                                    |
| **Statistics Staleness**            | `ANALYZE` not run after bulk inserts/updates.                                                                                                                                                                       | Schedule regular `ANALYZE` or use incremental statistics (PostgreSQL 16+).                        |

---

## **Vendor-Specific Notes**
| **Database**       | **Key Features**                                                                                                                                                                                                                     | **Commands/Options**                                                                                   |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **PostgreSQL**     | Rule-based + cost-based hybrid; extensive plan hints.                                                                                                                                                                   | `EXPLAIN ANALYZE`, `SET enable_seqscan = off;`, `plancache_size`.                                   |
| **SQL Server**     | Query Store for historical plan analysis; `OPTION` hints.                                                                                                                                                             | `SET STATISTICS PROFILE ON;`, `WITH (INDEX(idx_name))`, `OPTION (MAXDOP 4)`.                         |
| **MySQL**          | Limited parallelism; index merge optimizations.                                                                                                                                                                        | `EXPLAIN PARTITIONS`, `FORCE INDEX`, `innodb_buffer_pool_size`.                                       |
| **Oracle**         | Advanced optimization with `/*+ */` hints; adaptive planning.                                                                                                                                                                | `/*+ LEADING(t1 t2) */`, `DBMS_STATS.GATHER_TABLE_STATS`, `optimizer_adaptive_features`.           |
| **Snowflake**      | Auto-optimized plans; zero-copy cloning.                                                                                                                                                                             | `ANALYZE TABLE`, `ALTER TABLE SET CLUSTERING KEY`, `QUERY_TAG`.                                       |

---
**Key Takeaway:**
Query planning and optimization reduce runtime overhead by **precomputing execution strategies** and **leveraging metadata**. Pair this pattern with **indexing**, **partitioning**, and **statistics maintenance** for maximum efficiency. For complex workloads, use **plan hints** or **vendor-specific tools** to fine-tune performance.