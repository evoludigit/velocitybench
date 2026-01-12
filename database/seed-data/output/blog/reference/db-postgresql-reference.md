# **[PostgreSQL Database Patterns] Reference Guide**

---

## **1. Overview**
PostgreSQL Database Patterns provide reusable, best-practice database designs to tackle common challenges in relational data modeling. These patterns leverage PostgreSQL’s advanced features—**JSONB, full-text search, extensible types, row-level security (RLS), and partitioning**—to optimize performance, scalability, and maintainability. This guide covers standard patterns (e.g., **Single-Table Inheritance, Event Sourcing**) along with PostgreSQL-specific implementations (**Composite Keys, JSONB Indexing, Materialized Views**). Each pattern includes schema diagrams, SQL examples, and anti-patterns to avoid.

---

## **2. Schema Reference**

### **Key Patterns & Templates**

| **Pattern**               | **Purpose**                                                                 | **Core Tables**                                                                 | **Key Features**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Single-Table Inheritance** | Consolidate related entities into one table using `jsonb` or `polymorphic` columns. | `users` (id, name, type: 'admin'/'customer', payload: jsonb)                     | Avoids horizontal scaling overhead; flexible schema evolution.                  |
| **Composite Key**         | Use multi-column uniqueness constraints for natural key relationships.      | `orders(order_id, customer_id, status)` (PRIMARY KEY (order_id, customer_id)) | Optimizes joins; enforces domain integrity.                                    |
| **Slowly Changing Dimensions (SCD)** | Track historical data changes via timestamps or versioning.           | `products(id, name, valid_from, valid_to)` + audit trail (`product_history`)   | Supports time-based queries; non-overlapping intervals.                        |
| **Hierarchical Data**     | Store nested structures with recursive paths (e.g., categories/subcategories). | `categories(id, parent_id, name, depth)`                                      | Use `CTE`s (`WITH RECURSIVE`) or materialized paths for efficient queries.       |
| **JSONB Columnar**        | Embed semi-structured data (e.g., metadata, configuration) in tables.       | `users(id, name, profile: jsonb)` (index on `profile->>'email'`)                | schema-less flexibility; indexed for common queries.                          |
| **Materialized Views**    | Pre-compute complex aggregations for fast reads.                             | `mv_sales_by_region` (REFRESH MATERIALIZED VIEW CONCURRENTLY)                   | Reduces OLAP query load; incremental refresh options.                         |
| **Row-Level Security (RLS)** | Enforce granular access control via policies.                             | `users(id, access_policy: pg_policys)` (CREATE POLICY...)                      | Column/row visibility; auditable via `security_label`.                        |
| **Partitioning**          | Split large tables by range/hash (e.g., by date or region).               | `logs(id, log_date, message)` → Partitioned by `log_date`                     | Improves query performance; simplifies maintenance.                            |

---

## **3. Query Examples**

### **3.1 Single-Table Inheritance**
```sql
-- Insert a customer with polymorphic type
INSERT INTO users (name, type, payload)
VALUES ('Alice', 'customer', '{"premium": true, "points": 100}'::jsonb);

-- Query by type
SELECT * FROM users WHERE type = 'customer';
```

### **3.2 Composite Key**
```sql
-- Create constraint
ALTER TABLE orders ADD CONSTRAINT pk_order UNIQUE (order_id, customer_id);

-- Insert with composite key
INSERT INTO orders (order_id, customer_id, status) VALUES (123, 456, 'pending');
```

### **3.3 JSONB Indexing**
```sql
-- Create index for email lookup
CREATE INDEX idx_users_email ON users USING gin (payload->>'email');

-- Query using GIN index
SELECT * FROM users WHERE payload->>'email' = 'alice@test.com';
```

### **3.4 Hierarchical Data (CTE)**
```sql
-- Recursive query to fetch categories with subcategories
WITH RECURSIVE category_tree AS (
  SELECT id, name, parent_id, 0 AS depth
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, ct.depth + 1
  FROM categories c JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY depth;
```

### **3.5 Materialized Views**
```sql
-- Create materialized view
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT date_trunc('day', order_date) AS day,
       SUM(amount) AS total_sales
FROM orders
GROUP BY day;

-- Refresh incrementally
REFRESH MATERIALIZED VIEW mv_daily_sales CONCURRENTLY;
```

### **3.6 Row-Level Security**
```sql
-- Enable RLS on a table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their orders
CREATE POLICY user_orders_policy ON orders
USING (customer_id = current_setting('app.current_user_id')::integer);
```

### **3.7 Partitioning**
```sql
-- Create range-partitioned table
CREATE TABLE logs (
  id SERIAL,
  log_date TIMESTAMP,
  message TEXT
) PARTITION BY RANGE (log_date);

-- Create monthly partitions
CREATE TABLE logs_2023_01 PARTITION OF logs
FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
```

---

## **4. Implementation Best Practices**

### **✅ Do:**
- **Use `jsonb` for semi-structured data** (better indexing than `json`).
- **Leverage RLS for fine-grained access control** without application logic.
- **Partition large tables** by date/range to avoid full scans.
- **Materialize aggregations** for read-heavy workloads.
- **Enforce composite keys** for natural relationships (e.g., orders + customers).

### **❌ Avoid:**
- **Overusing `jsonb` for normalised data** (risk of duplicate data).
- **Ignoring `LIMIT` on recursive CTEs** (risk of stack overflow).
- **Not indexing `jsonb` paths** (slow queries).
- **Static partitioning** (use `LIST` or `HASH` for non-date data).
- **Forgetting to refresh materialized views** (stale data).

---

## **5. Anti-Patterns & Pitfalls**

| **Anti-Pattern**               | **Risk**                                                                                     | **Solution**                                                                       |
|----------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Flattening hierarchical data** | Impossible to query parent-child relationships efficiently.                              | Use recursive CTEs or materialized paths.                                         |
| **Using `json` instead of `jsonb`** | No GIN index support for querying nested fields.                                          | Always use `jsonb` for queryable semi-structured data.                             |
| **Ignoring `CONCURRENTLY`**      | DDL operations block read/write access during refreshes.                                   | Prefix `REFRESH` with `CONCURRENTLY` for low-downtime updates.                    |
| **Over-partitioning**           | Too many empty partitions degrade performance.                                              | Monitor partition usage; consolidate when necessary.                              |
| **Hardcoding RLS policies**      | Policies become unmanageable in large schemas.                                             | Use `CREATE POLICY` with dynamic conditions (e.g., `USING (field = current_user)`). |

---

## **6. Related Patterns**
- **[Event Sourcing](https://wiki.postgresql.org/wiki/Event_Sourcing)** – Store state changes as immutable logs.
- **[CQRS](https://wiki.postgresql.org/wiki/CQRS)** – Separate read/write schemas using materialized views.
- **[Audit Logging](https://www.postgresql.org/docs/current/monitoring-stats.html)** – Track changes with triggers or `pg_audit`.
- **[Temporal Tables](https://www.postgresql.org/docs/current/replication-temporal.html)** – Store data history with `valid_from`/`valid_to` columns.
- **[Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)** – Use `tsvector` for text indexing (e.g., `to_tsvector('english', description)`).

---
### **Further Reading**
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [Materialized Views Guide](https://www.postgresql.org/docs/current/mv-overview.html)
- [Partitioning Strategies](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

---
**Last Updated:** [Insert Date]
**Version:** 1.2