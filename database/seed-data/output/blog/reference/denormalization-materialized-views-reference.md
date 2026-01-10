---

# **[Pattern] Reference Guide: Denormalization & Materialized Views**

## **Overview**
**Purpose:**
Denormalization and materialized views optimize read performance by trading data integrity for query speed. This pattern pre-computes aggregated or joined data into simpler tables (denormalized schemas) or pre-stored query results (materialized views), reducing the complexity of real-time queries. It is ideal for **data warehousing, analytics, and applications requiring fast reads** but can tolerate eventual consistency.

**When to Use:**
- **Use this pattern when:**
  - Write operations are infrequent (e.g., batch ETL processes).
  - Read-heavy workloads demand sub-millisecond response times.
  - Complex joins/aggregations run frequently (e.g., dashboards, reporting).
- **Avoid when:**
  - Data must stay strictly consistent (use normalized schemas + transactions).
  - Write operations are high-volume (denormalization increases storage overhead).

**Trade-offs:**
| **Aspect**          | **Normalized Schema**                     | **Denormalized/Materialized Views**     |
|----------------------|-------------------------------------------|------------------------------------------|
| **Read Performance** | Slow (joins/aggregations per request)      | Fast (pre-computed results)               |
| **Write Performance**| Fast (simple inserts/updates)             | Slow (triggers refreshes/updates)        |
| **Storage**          | Compact (redundancy minimized)            | High (duplicated data)                   |
| **Consistency**      | Strong (ACID-compliant)                   | Eventual (refresh lag possible)          |

---

## **Key Concepts**

### **1. Denormalization**
**Definition:** Replicating data across tables to eliminate joins, often by embedding related records (e.g., storing `customer_name` in an `orders` table).

**Types:**
- **Redundant Attributes:** Copying non-key attributes (e.g., `department_name` in `employees`).
- **Bridge Tables:** Replacing one-to-many relationships with repeated foreign keys (e.g., `order_items` storing `product_id` multiple times).
- **Converted Joins:** Replacing joins with direct lookups (e.g., flatting a `products` hierarchy into a single table).

**Example Schema Transformation:**
```sql
-- Normalized
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id)
);

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100)
);

-- Denormalized
CREATE TABLE orders_denormalized (
    order_id INT PRIMARY KEY,
    customer_id INT,
    customer_name VARCHAR(100)  -- Redundant column
);
```

**Refresh Strategies:**
- **Manual:** Run a script to update views/tables after batch jobs.
- **Automated:**
  - **Trigger-based:** Update materialized views on DML events (e.g., PostgreSQL `REFRESH MATERIALIZED VIEW CONCURRENTLY`).
  - **Scheduled:** Use cron jobs or database-scheduled tasks (e.g., Oracle `DBMS_SCHEDULER`).
  - **Incremental:** Only update changed rows (e.g., track timestamps or checksums).

---

### **2. Materialized Views**
**Definition:** Pre-computed query results stored as tables, refreshed periodically. Supports complex aggregations (e.g., running totals, pivot tables).

**Use Cases:**
- Aggregations (e.g., `SUM(sales) BY region`).
- Complex joins (e.g., customer ordering history).
- Time-series data (e.g., rolling averages).

**Example:**
```sql
CREATE MATERIALIZED VIEW mv_sales_by_region AS
SELECT region, SUM(revenue) as total_sales
FROM sales
GROUP BY region;
```

**Implementation Notes:**
- **Query Syntax:** Varies by DBMS (e.g., PostgreSQL `CREATE MATERIALIZED VIEW`, Oracle `CREATE MATERIALIZED VIEW`).
- **Refresh Modes:**
  - **Fast Refresh:** Immediate update (if underlying data supports it, e.g., Oracle).
  - **Complete Refresh:** Rebuilds the view (default in PostgreSQL).
  - **Concurrent Refresh:** Updates without locking (PostgreSQL `CONCURRENTLY`).
- **Indexing:** Add indexes to materialized views for faster queries (e.g., `CREATE INDEX ON mv_sales_by_region(region)`).

---

## **Schema Reference**

Below are common denormalized and materialized view schemas for a sample **e-commerce** system.

| **Pattern**               | **Normalized Schema**                          | **Denormalized Schema**                     | **Materialized View**                     |
|---------------------------|-----------------------------------------------|---------------------------------------------|-------------------------------------------|
| **Customers & Orders**    |                                          |                                             |                                           |
| **Tables**                | `customers(id, name, email)`                 | `customers_denorm(id, name, email, last_order_date)` | `mv_cust_order_stats(id, name, total_spend)` |
| **Key Additions**         | `orders(id, customer_id, order_date, total)` | `last_order_date` (copied from orders)     | `total_spend` (pre-aggregated)            |
| **Refresh Logic**         | N/A                                          | Trigger on `orders` insert/update          | Scheduled daily refresh (incremental)     |
| **Query Benefit**         | `SELECT o.*, c.name FROM orders o JOIN customers c` | `SELECT * FROM customers_denorm WHERE id = ?` | `SELECT * FROM mv_cust_order_stats WHERE id = ?` |

| **Pattern**               | **Products & Inventory**                     |                                             |                                           |
|---------------------------|----------------------------------------------|---------------------------------------------|-------------------------------------------|
| **Tables**                | `products(id, name, price)`                  | `inventory_denorm(id, name, price, stock)`   | `mv_popular_items(id, name, avg_rating)` |
| **Key Additions**         | `inventory(id, product_id, quantity)`        | `stock` (copied from inventory)             | `avg_rating` (pre-aggregated)             |
| **Refresh Logic**         | N/A                                          | Trigger on `inventory` update               | Scheduled hourly refresh                 |
| **Query Benefit**         | `SELECT p.name, i.quantity FROM products p JOIN inventory i` | `SELECT * FROM inventory_denorm WHERE id = ?` | `SELECT * FROM mv_popular_items`          |

---

## **Query Examples**

### **1. Denormalized Query (Fast Lookup)**
**Problem:** Joining `customers` and `orders` is slow due to high cardinality.
**Solution:** Denormalize `customer_name` into the `orders` table.

```sql
-- Normalized (slow for large datasets)
SELECT o.order_id, c.name AS customer_name, o.order_date
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2023-01-01';

-- Denormalized (fast)
SELECT order_id, customer_name, order_date
FROM orders_denormalized
WHERE order_date > '2023-01-01';
```

### **2. Materialized View Query (Aggregation)**
**Problem:** Running `SUM(sales) BY region` daily is expensive.
**Solution:** Pre-compute in a materialized view.

```sql
-- Create materialized view (runs once)
CREATE MATERIALIZED VIEW mv_sales_by_region AS
SELECT region, SUM(amount) as total_sales
FROM sales
GROUP BY region;

-- Query (instant)
SELECT * FROM mv_sales_by_region
WHERE total_sales > 100000;
```

### **3. Incremental Refresh (PostgreSQL)**
**Problem:** Refreshing a materialized view daily is slow.
**Solution:** Use `CONCURRENTLY` for low-locking updates.

```sql
-- Initial refresh
CREATE MATERIALIZED VIEW mv_customer_spending AS
SELECT c.id, c.name, SUM(o.total) as lifetime_spend
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name;

-- Incremental refresh (minimizes locks)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_spending;
```

### **4. Denormalized + Indexing**
**Problem:** Denormalized table has slow searches.
**Solution:** Add indexes to speed up queries.

```sql
-- Denormalized table
CREATE TABLE order_items_denorm (
    order_id INT,
    product_id INT,
    product_name VARCHAR(100),  -- Redundant
    quantity INT,
    PRIMARY KEY (order_id, product_id),
    INDEX idx_product_name (product_name)
);

-- Fast lookup by product name
SELECT * FROM order_items_denorm
WHERE product_name LIKE '%laptop%';
```

---

## **Implementation Steps**

### **1. Identify Read-Heavy Paths**
- Use database logs or profiling tools (e.g., PostgreSQL `EXPLAIN ANALYZE`) to find slow queries.
- Prioritize denormalization for:
  - Frequently joined tables.
  - Large aggregations (e.g., `GROUP BY` on millions of rows).

### **2. Design Denormalized Schema**
- **Rule of Thumb:** Denormalize only what you query often. Avoid over-denormalizing.
- **Example:** If `customers` are joined with `orders` 90% of the time, copy `customer_name` to `orders`.

### **3. Implement Materialized Views**
- **For Aggregations:**
  ```sql
  CREATE MATERIALIZED VIEW mv_daily_revenue AS
  SELECT date_trunc('day', order_date) as day,
         SUM(total) as revenue
  FROM orders
  GROUP BY day;
  ```
- **For Complex Joins:**
  ```sql
  CREATE MATERIALIZED VIEW mv_customer_order_history AS
  SELECT c.id, c.name, o.order_id, o.order_date
  FROM customers c
  JOIN orders o ON c.id = o.customer_id;
  ```

### **4. Set Up Refresh Strategy**
| **Refresh Type**       | **When to Use**                          | **Example (PostgreSQL)**                  |
|------------------------|------------------------------------------|-------------------------------------------|
| **Manual**             | One-time setup                           | `REFRESH MATERIALIZED VIEW mv_name;`       |
| **Automated (Trigger)**| Real-time updates                        | `CREATE TRIGGER ref_mv AFTER INSERT ON sales EXECUTE PROCEDURE refresh_mv();` |
| **Scheduled**          | Batch updates (e.g., hourly/daily)       | Use `pg_cron` or cron job: `psql -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_name;"` |
| **Incremental**        | Large tables with change tracking        | Track `last_updated` timestamp in source tables. |

### **5. Monitor Performance**
- **Check Refresh Times:** Log refresh durations (e.g., `LOG REFRESH` in PostgreSQL).
- **Validate Data:** Ensure materialized views match source data (e.g., checksum comparisons).
- **Reindex:** Drop/recreate indexes if query plans degrade.

---

## **Error Handling & Consistency**

### **1. Handling Conflicts**
- **Merge Strategies:** Use `MERGE` (SQL Server) or `INSERT ON CONFLICT` (PostgreSQL) to update denormalized data.
  ```sql
  -- PostgreSQL example
  INSERT INTO orders_denormalized (order_id, customer_name)
  VALUES (123, 'John Doe')
  ON CONFLICT (order_id) DO UPDATE SET customer_name = EXCLUDED.customer_name;
  ```
- **Tombstoning:** Mark deleted records as inactive (e.g., `is_active` flag) instead of hard-deleting.

### **2. Consistency Guarantees**
| **Scenario**               | **Normalized**          | **Denormalized/MV**                     |
|----------------------------|-------------------------|------------------------------------------|
| **Immediate Consistency**  | ACID-compliant           | **No** (unless refreshed manually)      |
| **Eventual Consistency**   | Requires transactions    | Configured via refresh frequency         |
| **Rollback Support**       | Full (transactions)      | Partial (manual refresh may be needed)   |

### **3. Fallback for Stale Data**
- **Cache Invalidation:** Invalidate denormalized data when source tables change.
- **Query Fallback:** Combine materialized views with live queries:
  ```sql
  -- Prefer MV if fresh, else query live
  SELECT * FROM mv_sales_by_region
  WHERE last_refresh > NOW() - INTERVAL '1 hour';
  ```

---

## **Related Patterns**

| **Pattern**                  | **Description**                                                                 | **When to Pair**                          |
|------------------------------|---------------------------------------------------------------------------------|-------------------------------------------|
| **[CQRS](https://microservices.io/patterns/data/cqrs.html)** | Separates read ("Query") and write ("Command") models.                          | Use denormalization for the query model.  |
| **[Event Sourcing](https://martinfowler.com/eaaT/)** | Stores state changes as a sequence of events.                                  | Materialized views can replay events.     |
| **[Sharding](https://www.percona.com/blog/2017/10/03/sharding-overview/)** | Splits data across machines by key.                                            | Denormalize within shards for local reads. |
| **[Caching](https://docs.microsoft.com/en-us/azure/architecture/patterns/caching)** | Stores frequent queries in memory (e.g., Redis).                              | Use materialized views for warm cache data. |
| **[Data Warehouse](https://www.gartner.com/en/topics/data-warehousing)** | Optimized for analytics (e.g., Snowflake, BigQuery).                          | Denormalize for star/snowflake schemas.   |

---

## **Anti-Patterns**

1. **Over-Denormalization**
   - **Problem:** Copying every possible field across tables leads to:
     - Unmanageable schemas.
     - Storage bloat.
     - Higher refresh costs.
   - **Fix:** Denormalize only what queries frequently access.

2. **Ignoring Refresh Overhead**
   - **Problem:** Refreshing materialized views during peak hours causes performance spikes.
   - **Fix:** Schedule refreshes during off-peak hours or use incremental updates.

3. **Assuming ACID Works for MVs**
   - **Problem:** Materialized views cannot participate in transactions like base tables.
   - **Fix:** Treat MVs as read-only unless using refresh triggers with transactional control.

4. **Not Validating Data Freshness**
   - **Problem:** Stale materialized views return incorrect results.
   - **Fix:** Add `last_refreshed` timestamps and query with:
     ```sql
     SELECT * FROM mv_data WHERE last_refreshed > NOW() - INTERVAL '1 hour';
     ```

5. **Using Denormalization for Write-Heavy Systems**
   - **Problem:** Duplicate writes increase storage and conflict resolution complexity.
   - **Fix:** Stick to normalized schemas if writes > reads.

---

## **Tools & Extensions**
| **Database**       | **Materialized View Support**                          | **Refresh Features**                          |
|---------------------|--------------------------------------------------------|-----------------------------------------------|
| **PostgreSQL**      | `CREATE MATERIALIZED VIEW`                             | `REFRESH MATERIALIZED VIEW [CONCURRENTLY]`    |
| **Oracle**          | `CREATE MATERIALIZED VIEW`                             | Fast refresh, partition support               |
| **SQL Server**      | `CREATE VIEW WITH (SCHEMABINDING, ENABLE_BROKER)`     | Indexed views (limited MV functionality)      |
| **MySQL**           | Views only (no native MV)                              | Use triggers + physical tables                 |
| **BigQuery**        | Materialized views (beta)                              | Scheduled refresh via `CREATE MATERIALIZED VIEW` |
| **Snowflake**       | Table functions (simulates MVs)                        | Automated refresh via `REFRESH` command       |

---
**See Also:**
- [PostgreSQL Materialized Views Docs](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
- [Denormalization Case Study: Uber’s Data Platform](https://eng.uber.com/denormalization/)
- [CQRS Pattern (Martin Fowler)](https://martinfowler.com/articles/20100803/components.html)