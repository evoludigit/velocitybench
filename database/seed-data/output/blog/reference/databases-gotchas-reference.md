# **[Pattern] Database Gotchas: Reference Guide**

---

## **Overview**
Database Gotchas refer to subtle, often counterintuitive behaviors in relational databases that can cause performance issues, logical errors, or unexpected results. These pitfalls arise from how databases handle concurrency, indexing, queries, transactions, and schema design. Recognizing and avoiding these gotchas is critical for writing reliable, efficient, and scalable database applications.

Common Gotchas include:
- **Concurrency anomalies** (dirty reads, phantom rows, mutable cursors).
- **Indexing misconceptions** (inefficient index usage, index fragmentation).
- **Querying pitfalls** (missing joins, improper `ORDER BY`, `NULL` handling).
- **Transaction limitations** (serialization failures, deadlocks).
- **Schema design flaws** (normalization vs. denormalization trade-offs).

This guide breaks down these issues with schema references, query examples, and mitigation strategies.

---

## **Schema Reference**

The following tables outline common database schema structures where Gotchas often manifest.

### **1. Basic E-Commerce Schema (For Query Examples)**
| Table       | Columns                                                                 | Key Gotcha Areas                     |
|-------------|--------------------------------------------------------------------------|--------------------------------------|
| **Customers** | `customer_id (PK)`, `name`, `email`, `created_at`                     | `NULL` handling, `GROUP BY` on non-aggregated columns |
| **Orders**   | `order_id (PK)`, `customer_id (FK)`, `order_date`, `total_amount`      | Phantom reads, transaction isolation |
| **Order_Items** | `item_id (PK)`, `order_id (FK)`, `product_id (FK)`, `quantity`, `price` | Mutable cursors, index inefficiency  |
| **Products** | `product_id (PK)`, `name`, `price`, `stock_quantity`                   | Race conditions on `stock_quantity`|

### **2. Concurrent Access Patterns**
| Scenario                | Database Behavior (PostgreSQL/MySQL)                     | Gotcha Description                                                                 |
|-------------------------|---------------------------------------------------------|------------------------------------------------------------------------------------|
| **Dirty Reads**         | `SELECT ... FOR UPDATE` without isolation level (`SERIALIZABLE`) | Uncommitted changes visible; leads to logical inconsistency.                           |
| **Phantom Reads**       | Query runs twice; second run returns rows not in first query.        | Caused by concurrent `INSERT`/`UPDATE` between executions.                          |
| **Non-Repeatable Reads**| Same query returns different results in same transaction.       | Due to concurrent `UPDATE`/`DELETE` on indexed rows.                                 |
| **Serializable Blocker**| Transaction blocks indefinitely due to conflicting locks.        | Long-running transactions hold locks; deadlocks or timeouts occur.                  |

---

## **Query Examples (Gotchas & Fixes)**

### **1. `NULL` Handling: Missing Aggregations**
**✅ Incorrect (Gotcha):**
```sql
-- Returns 0 for NULL counts, not NULL!
SELECT COUNT(*) FROM orders WHERE customer_id IS NULL;
```
**✅ Fixed:**
```sql
-- Use COUNT() with NULL-safe aggregation
SELECT COUNT(customer_id) FROM orders;
```

**❌ Gotcha:**
Querying non-aggregated columns in `GROUP BY` without explicit aggregation (PostgreSQL rejects this; MySQL silently promotes to aggregate).
```sql
-- MySQL: Returns arbitrary row per group (undefined behavior)
SELECT customer_id, name FROM orders GROUP BY customer_id;
```
**✅ Fixed:**
```sql
-- Explicitly aggregate or use window functions
SELECT customer_id, MAX(name) FROM orders GROUP BY customer_id;
```

---

### **2. Indexing Misuse: Covering Indexes**
**✅ Correct (Covering Index):**
```sql
-- Uses index on `(customer_id, order_date)` to avoid table scan
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
SELECT customer_id, order_date, total_amount FROM orders WHERE customer_id = 123;
```

**❌ Gotcha: Missing Indexed Column**
```sql
-- Forces a table scan (inefficient)
SELECT customer_id, order_date, total_amount FROM orders WHERE customer_id = 123;
-- Fix: Ensure all SELECT columns are in the index
```

---

### **3. Race Conditions: Incrementing Counters**
**✅ Incorrect (Gotcha):**
```sql
-- Race condition: Two transactions may read/save `stock_quantity` simultaneously!
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE product_id = 42;
```
**✅ Fixed (Atomic Operations):**
```sql
-- Use `RETURNING` or `UPDATE ... WHERE ...` with a condition
UPDATE products
SET stock_quantity = stock_quantity - 1
WHERE product_id = 42 AND stock_quantity > 0
RETURNING stock_quantity;
```

---

### **4. Transaction Isolation: Phantom Reads**
**✅ Setup (Reproduce Gotcha):**
```sql
-- Start transaction (reads all rows)
BEGIN;
SELECT * FROM orders WHERE customer_id = 100;
-- Concurrent INSERT occurs
INSERT INTO orders (customer_id, order_date) VALUES (100, NOW());
-- Second SELECT in same transaction misses the new row (phantom read)
SELECT * FROM orders WHERE customer_id = 100;
COMMIT;
```
**✅ Fixed (Use Serializable Isolation):**
```sql
-- Explicitly set isolation level
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT * FROM orders WHERE customer_id = 100 FOR SHARE;
```

---

### **5. Window Functions: Mutable Cursors**
**✅ Gotcha: Mutable Cursor Behavior**
```sql
-- Window function (e.g., ROW_NUMBER()) can return different results per row
WITH RankedOrders AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS rn
  FROM orders
)
SELECT * FROM RankedOrders WHERE rn = 1;  -- May return different rows due to execution order!
```
**✅ Fixed (Deterministic Execution):**
```sql
-- Force consistent ordering (e.g., with a stable sort)
WITH RankedOrders AS (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY customer_id
           ORDER BY order_date, order_id  -- Add a secondary key for stability
         ) AS rn
  FROM orders
)
SELECT * FROM RankedOrders WHERE rn = 1;
```

---

## **Mitigation Strategies**
| Gotcha Type               | Mitigation Strategy                                                                 |
|---------------------------|------------------------------------------------------------------------------------|
| **Concurrency Issues**    | Use appropriate isolation levels (`SERIALIZABLE`, `REPEATABLE READ`).               |
| **Index Inefficiency**    | Design indexes for query patterns; use `EXPLAIN ANALYZE` to diagnose scans.       |
| **NULL Handling**         | Avoid `WHERE col IS NULL`; use `NULLIF` or explicit `IS NULL` checks.              |
| **Race Conditions**       | Use optimistic locking (e.g., `VERSION` column) or `SELECT ... FOR UPDATE`.       |
| **Phantom Reads**         | Add filters to queries or use `NO KEY UPDATE` hints (MySQL).                       |
| **Query Optimization**    | Avoid `SELECT *`; prefer explicit columns, materialized views, or CTEs.            |

---

## **Related Patterns**
1. **[Idempotent Operations](https://example.com/idempotent-ops)**
   - Ensures retries or concurrent executions don’t cause duplicate side effects.
2. **[Optimistic Locking](https://example.com/optimistic-locking)**
   - Uses version columns to handle conflicts without pessimistic locks.
3. **[Batch Processing](https://example.com/batch-processing)**
   - Mitigates transactional overhead for bulk operations.
4. **[Database Sharding](https://example.com/sharding)**
   - Distributes data to reduce contention (but introduces new Gotchas like cross-shard joins).
5. **[Eventual Consistency](https://example.com/eventual-consistency)**
   - Trade-offs for high-availability systems (e.g., CQRS patterns).

---
**Note:** Specific behaviors vary by database (PostgreSQL, MySQL, SQL Server). Always test Gotcha scenarios in your target environment. For deeper dives, consult vendor documentation (e.g., [PostgreSQL docs](https://www.postgresql.org/docs/)).