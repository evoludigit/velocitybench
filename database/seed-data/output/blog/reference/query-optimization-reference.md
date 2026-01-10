---
# **[Pattern] SQL Query Optimization – Reference Guide**

Optimized SQL queries minimize execution time and resource usage by leveraging database engine capabilities. This guide covers techniques to analyze, restructure, and execute queries efficiently, ensuring scalability and performance in production environments.

---

## **Overview**
Query optimization reduces latency by eliminating inefficiencies like full table scans, unnecessary computations, or suboptimal join strategies. Key focus areas include:
- **Analyzing query plans** with `EXPLAIN`/`EXPLAIN ANALYZE` to identify bottlenecks.
- **Using indexes** effectively to avoid expensive operations.
- **Restructuring queries** (e.g., avoiding `SELECT *`, using CTEs wisely).
- **Leveraging database-specific features** like materialized views, partitioning, or query hints.

A 100x performance gain is achievable by following best practices. This guide provides actionable patterns with code examples and schema references.

---

## **Schema Reference**
Below is a sample schema used in query examples:

| Table          | Columns                          | Purpose                                      |
|----------------|----------------------------------|----------------------------------------------|
| `customers`    | `id (PK)`, `name`, `email`, `join_date` | Stores customer data.                        |
| `orders`       | `id (PK)`, `customer_id (FK)`, `order_date`, `total_amount` | Order records linked to customers.           |
| `order_items`  | `id (PK)`, `order_id (FK)`, `product_id`, `quantity`, `price` | Line items for orders.                       |
| `products`     | `id (PK)`, `name`, `category_id`, `stock` | Product catalog.                            |

---

## **Components/Solutions**

### **1. EXPLAIN ANALYZE (Tool)**
Analyze query plans to identify performance issues:
```sql
-- PostgreSQL / SQLite
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;

-- MySQL
EXPLAIN FORMAT=JSON SELECT * FROM orders WHERE customer_id = 123;

-- SQL Server
SET STATISTICS TIME, IO ON;
SELECT * FROM orders WHERE customer_id = 123;
```

**Key Metrics to Check:**
- `Seq Scan` vs. `Index Scan` (index usage).
- `Rows` estimated vs. actual (query planner accuracy).
- `Time` or `Duration` (execution latency).

---

### **2. Index Utilization (Technique)**
**When to Use:**
- Columns frequently used in `WHERE`, `JOIN`, or `ORDER BY` clauses.
- Avoid overly broad indexes (e.g., `SELECT *` on indexed columns).

**Example: Adding an Index**
```sql
-- PostgreSQL / MySQL / SQLite
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);

-- SQL Server
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date)
INCLUDE (total_amount); -- Covers additional columns.
```

**Anti-Pattern:**
```sql
-- Inefficient: Full table scan
SELECT * FROM orders WHERE order_date > '2023-01-01';
```
**Optimized:**
```sql
-- Uses index
SELECT id, customer_id, order_date FROM orders WHERE order_date > '2023-01-01';
```

---

### **3. Query Rewriting (Technique)**

#### **A. Avoid `SELECT *`**
Retrieve only necessary columns to reduce I/O and CPU overhead.
```sql
-- Anti-Pattern
SELECT * FROM customers WHERE join_date > '2020-01-01';

-- Optimized
SELECT id, name, email FROM customers WHERE join_date > '2020-01-01';
```

#### **B. Use Common Table Expressions (CTEs) Wisely**
CTEs improve readability but may not always optimize performance. Test with `EXPLAIN`.
```sql
-- Example: CTE for a derived table
WITH high_value_orders AS (
    SELECT customer_id, SUM(total_amount) as total_spent
    FROM orders
    WHERE order_date > '2023-01-01'
    GROUP BY customer_id
    HAVING SUM(total_amount) > 1000
)
SELECT c.name, hvo.total_spent
FROM customers c
JOIN high_value_orders hvo ON c.id = hvo.customer_id;
```

#### **C. Optimize Joins**
- **Join Order**: Place the smallest table first.
- **Join Type**: Prefer `INNER JOIN` over `LEFT JOIN` if possible.

```sql
-- Anti-Pattern: Cartesian product
SELECT * FROM customers, orders WHERE customers.id = orders.customer_id;

-- Optimized: Explicit JOIN
SELECT c.name, o.order_date
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
WHERE o.order_date > '2023-01-01';
```

#### **D. Partitioning Large Tables**
For tables >100M rows, partition by date or range:
```sql
-- PostgreSQL: Create a partitioned table
CREATE TABLE orders_partitioned (
    id INT,
    customer_id INT,
    order_date DATE,
    total_amount DECIMAL
)
PARTITION BY RANGE (order_date);

-- MySQL: Partitioned table
CREATE TABLE orders_partitioned (
    id INT,
    customer_id INT,
    order_date DATE,
    total_amount DECIMAL
) PARTITION BY RANGE (YEAR(order_date)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025)
);
```

---

## **Query Examples**

### **Example 1: Optimized Report Query**
**Problem:** Slow due to full table scans and unnecessary columns.
```sql
-- Anti-Pattern
SELECT c.*, o.*, oi.*
FROM customers c
JOIN orders o ON c.id = o.customer_id
JOIN order_items oi ON o.id = oi.order_id
WHERE o.order_date > '2023-01-01';
```

**Optimized:**
```sql
-- Uses indexes, limits columns, and filters early
SELECT
    c.id, c.name, c.email,
    o.order_date, o.total_amount,
    oi.product_id, oi.quantity
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
    AND o.order_date > '2023-01-01'  -- Early filter
INNER JOIN order_items oi ON o.id = oi.order_id
WHERE oi.quantity > 1;  -- Additional filter
```

### **Example 2: Pagination with OFFSET**
**Problem:** `OFFSET` can be slow for large datasets.
```sql
-- Anti-Pattern: Inefficient pagination
SELECT * FROM orders ORDER BY order_date LIMIT 10 OFFSET 100;
```

**Optimized:**
- Use **keyset pagination** (recommended for large datasets):
```sql
-- Fetch next 10 orders after a given order_date
SELECT * FROM orders
WHERE order_date > '2023-02-01'
ORDER BY order_date
LIMIT 10;
```

---

## **Related Patterns**
1. **[Database Indexing]** – Design strategies for efficient indexing.
2. **[Batch Processing]** – Process large datasets in chunks.
3. **[Query Caching]** – Cache frequent/expensive queries (e.g., Redis, materialized views).
4. **[Connection Pooling]** – Manage database connections efficiently.
5. **[Microservices Data Design]** – Split large monolithic tables into smaller, optimized tables.

---

## **Best Practices Summary**
| Technique               | Action Items                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Analyze Plans**       | Use `EXPLAIN ANALYZE` regularly.                                             |
| **Index Wisely**        | Cover frequently queried columns; avoid over-indexing.                      |
| **Limit Columns**       | Avoid `SELECT *`; fetch only needed data.                                    |
| **Optimize Joins**      | Use `INNER JOIN`, order smallest tables first.                              |
| **Leverage CTEs**       | Test for performance gain; avoid overusing.                                  |
| **Partition Large Tables** | Split by date/range for better scan efficiency.                            |
| **Avoid `OFFSET`**      | Use keyset pagination for large datasets.                                   |

---
**Final Note:** Always test optimizations in a staging environment before applying to production. Monitor query performance over time as data grows.