# **[Pattern] View Naming Convention (v_*, tv_*, mv_*, av_*) Reference Guide**

---

## **Overview**
The **View Naming Convention** ensures consistency and clarity in database view naming by categorizing views into distinct types using prefixing. This standard
- Improves maintainability by distinguishing view purposes (read-only, materialized, columnar).
- Reduces ambiguity by standardizing naming patterns.
- Supports scalable query optimization (e.g., for materialized views).

Prefixes:
- **`v_*`:** Standard base views (read-only, non-indexed).
- **`tv_*`:** Table-backed views (physically materialized as tables).
- **`mv_*`:** Materialized views (indexed, precomputed data).
- **`av_*`:** Arrow (columnar) views (optimized for analytical queries).

---
## **Schema Reference**
| **Prefix** | **View Type**               | **Purpose**                                                                 | **Physical Storage**               | **Optimized For**                     |
|------------|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------|---------------------------------------|
| `v_*`      | Base View                   | Virtual, query-only projections (no storage).                              | No physical storage                | Read consistency, ad-hoc queries     |
| `tv_*`     | Table-Backed View           | Physical copy of a table (with optional filtering/transformation).         | Separate table                     | OLTP-like operations                  |
| `mv_*`     | Materialized View           | Precomputed, indexed aggregations or joins (refreshable).                  | Indexed view (or table)            | Fast aggregations, time-series data  |
| `av_*`     | Arrow (Columnar) View       | Columnar storage optimized for analytical queries (e.g., Parquet/ORC).     | Columnar format (e.g., Delta Lake)  | OLAP workloads, large-scale scans    |

---
## **Implementation Details**

### **1. Use Cases**
- **Base Views (`v_*`):**
  Example: `v_customer_demographics`
  Use for derived data from multiple tables (e.g., JOINs) where no materialization is needed.
  ```sql
  CREATE VIEW v_customer_demographics AS
  SELECT c.*, d.age_group
  FROM customers c
  JOIN demographics d ON c.demographic_id = d.id;
  ```

- **Table-Backed Views (`tv_*`):**
  Example: `tv_active_customers` (physical copy of a filtered table).
  Use when a subset of data (e.g., filtered by date) is frequently queried.
  ```sql
  CREATE TABLE tv_active_customers AS
  SELECT * FROM customers
  WHERE signup_date > CURRENT_DATE - INTERVAL '30 days';
  ```

- **Materialized Views (`mv_*`):**
  Example: `mv_monthly_sales_summary`
  Use for precomputed aggregations (e.g., daily/weekly metrics) that change less frequently.
  ```sql
  CREATE MATERIALIZED VIEW mv_monthly_sales_summary AS
  SELECT
    DATE_TRUNC('month', order_date) AS month,
    SUM(revenue) AS total_revenue,
    COUNT(DISTINCT customer_id) AS active_customers
  FROM orders
  GROUP BY 1;
  ```
  **Refresh Strategy:** Automated (e.g., via `REFRESH MATERIALIZED VIEW`).

- **Arrow Views (`av_*`):**
  Example: `av_large_scale_log_analysis`
  Use for columnar storage to accelerate analytical queries (e.g., Spark SQL, Trino).
  ```sql
  CREATE VIEW av_large_scale_log_analysis AS
  SELECT * FROM logs
  STORED AS PARQUET;  -- Assumes columnar storage layer (e.g., Iceberg)
  ```

---
### **2. Naming Rules**
- **Prefix Mandatory:** All views **must** start with one of the defined prefixes.
- **Suffix Clarity:**
  - Append domain-specific suffixes (e.g., `_sales`, `_user_usage`).
    Example: `v_customer_orders`, `tv_active_subscriptions_2023`.
  - Avoid underscores in domain terms (e.g., `v_social_media_activity` > `v_social_media_activity`).
- **Capitalization:** CamelCase or UPPER_CASE (corporate standard).
  Example: `mv_DailyTrafficMetrics` or `mv_daily_traffic_metrics`.
- **Avoid Reserved Terms:** Do not use `view` or `summary` as standalone suffixes (e.g., `v_customer_view` → `v_customer_profile`).

---
### **3. Query Optimization Guidance**
| **View Type** | **Best Practices**                                                                 | **Avoid**                                  |
|---------------|-----------------------------------------------------------------------------------|--------------------------------------------|
| `v_*`         | Use for ad-hoc queries; avoid in `WHERE` clauses with large predicates.           | Joining to `v_*` in complex analytical queries. |
| `tv_*`        | Use `WITH CHECK OPTION` to enforce row-level constraints.                          | Overusing `tv_*` for dynamic data (refresh frequently). |
| `mv_*`        | Set up automated refreshes (e.g., cron jobs, change data capture).                  | Updating `mv_*` in real-time for volatile data. |
| `av_*`        | Partition views by time/ID for efficient pruning (e.g., `PARTITION BY DATE`).     | Querying without filters (full scans).    |

---
## **Query Examples**
### **1. Base View (`v_*`)**
```sql
-- Create
CREATE VIEW v_inactive_customers AS
SELECT customer_id, name
FROM customers
WHERE last_purchase_date < CURRENT_DATE - INTERVAL '30 days';

-- Query
SELECT COUNT(*) FROM v_inactive_customers;
```

### **2. Table-Backed View (`tv_*`)**
```sql
-- Create (PostgreSQL syntax)
CREATE TABLE tv_high_value_customers AS
SELECT * FROM customers
WHERE lifetime_value > 1000;

-- Query with constraints
SELECT * FROM tv_high_value_customers
WHERE region = 'North America';
```

### **3. Materialized View (`mv_*`)**
```sql
-- Create (Snowflake syntax)
CREATE MATERIALIZED VIEW mv_daily_active_users
REFRESH BY TIMESTAMP contiuously AS
SELECT
  DATE_TRUNC('day', login_time) AS day,
  COUNT(DISTINCT user_id) AS active_users
FROM logins
GROUP BY 1;

-- Query
SELECT * FROM mv_daily_active_users
WHERE day BETWEEN '2023-01-01' AND '2023-01-10';
```

### **4. Arrow View (`av_*`)**
```sql
-- Create (Apache Iceberg/Delta Lake)
CREATE VIEW av_sales_by_product_category
STORED AS PARQUET
LOCATION 's3://data/av_sales_by_product_category/'
AS SELECT
  product_category,
  SUM(revenue) AS total_revenue
FROM sales
GROUP BY 1;

-- Query (optimized for columnar access)
SELECT * FROM av_sales_by_product_category
WHERE revenue > 10000
ORDER BY total_revenue DESC;
```

---
## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                          |
|----------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Partitioning Strategy]**      | Divides data into segments (e.g., by time/ID) to improve query performance.     | Pair with `tv_*` or `av_*` for large tables. |
| **[View Indexing]**              | Adds indexes to materialized/views for faster lookups.                          | Use on `mv_*` with high-selectivity columns. |
| **[Change Data Capture (CDC)]**  | Tracks data changes to refresh materialized views incrementally.                | For `mv_*` with real-time requirements.  |
| **[Query Caching]**              | Caches frequent query results to reduce compute costs.                          | Complements `v_*` for repetitive queries. |

---
## **Best Practices**
1. **Document Purpose:** Add comments to views explaining logic/rigor (e.g., `mv_*` refresh frequency).
   ```sql
   COMMENT ON MATERIALIZED VIEW mv_monthly_sales_summary
   IS 'Refreshes daily at 2 AM. Contains 30-day rolling data.';
   ```
2. **Audit Access:**
   - Grant read-only permissions to `v_*`/`tv_*` by default.
   - Restrict writes to `mv_*`/`av_*` to DBA teams.
3. **Monitor Performance:**
   - Track query plans for `v_*`/`av_*` to avoid full scans.
   - Use `EXPLAIN` to validate materialization strategy for `mv_*`.
4. **Deprecation:**
   - Prefix deprecated views with `v_deprecated_*` and add a warning in comments.
   ```sql
   CREATE VIEW v_deprecated_old_customer_data AS ...;
   COMMENT ON VIEW v_deprecated_old_customer_data
   IS 'Deprecated: Use v_customer_profile instead.';
   ```

---
## **Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                              |
|-------------------------------------|-----------------------------------------|-------------------------------------------|
| Slow `v_*` queries                  | Complex JOINs without indexes.           | Replace with `mv_*` or pre-filter data.  |
| High refresh latency (`mv_*`)       | Large base table size.                  | Partition data or use incremental refresh. |
| `av_*` not optimized                 | No partitioning/filtration in queries.  | Add `WHERE` clauses or use bucketing.     |
| Orphaned `tv_*` views                | No ownership tracking.                   | Implement lifecycle policies (e.g., auto-drop after 6 months). |