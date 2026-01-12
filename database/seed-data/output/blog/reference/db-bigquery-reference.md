# **[Pattern] BigQuery Database Patterns – Reference Guide**

---

## **Overview**
BigQuery Database Patterns provide structured approaches to organizing data, optimizing performance, and ensuring scalability in large-scale analytics environments. This reference outlines four core patterns—**Partitioning, Clustering, Schema Design, and Data Modeling**—along with implementation details, schema examples, query optimizations, and best practices. These patterns help mitigate common pitfalls like high query costs, slow performance, or inefficient storage while enabling efficient data processing at scale.

---

## **Pattern 1: Partitioning**
Partitioning divides large tables into smaller, manageable segments based on a timestamp or integer column, improving query performance and cost efficiency.

### **Schema Reference**
| **Pattern Type**       | **Partitioning Key**       | **Use Case**                          | **Best Practices**                                                                 |
|------------------------|----------------------------|----------------------------------------|----------------------------------------------------------------------------------|
| **Time-Based**         | `_PARTITIONTIME` (timestamp)| Event data (e.g., logs, transactions)  | Partition by `DAY` for granular control; avoid over-partitioning.                |
| **Integer-Based**      | `INTEGER` column           | Geospatial data (e.g., `region_id`)   | Use range partitioning (e.g., `region_id BETWEEN 1 AND 100`).                     |
| **Dynamic Partitioning**| `DATE` or `TIMESTAMP`      | Incremental data loads (e.g., ETL)    | Enable with `TIMESTAMP_TRUNC()` for automatic partitioning.                       |

### **Query Examples**
#### **Time-Based Partitioning Query**
```sql
SELECT
  user_id,
  COUNT(*) AS event_count
FROM
  `project.dataset.events`
WHERE
  _PARTITIONTIME BETWEEN '2023-01-01' AND '2023-01-31'
  AND event_type = 'purchase'
```

#### **Integer-Based Partitioning Query**
```sql
SELECT
  region_id,
  SUM(revenue) AS total_revenue
FROM
  `project.dataset.sales`
WHERE
  region_id BETWEEN 50 AND 60
GROUP BY
  region_id
```

#### **Dynamic Partitioning (Insert with Partition Key)**
```sql
INSERT INTO
  `project.dataset.logs_dynamic`
  PARTITION BY DATE(timestamp)
SELECT
  *,
  timestamp AS timestamp
FROM
  `project.dataset.raw_logs`
WHERE
  timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
```

---

## **Pattern 2: Clustering**
Clustering sorts rows within partitions on specified columns, reducing scan volume for filtered queries.

### **Schema Reference**
| **Column**            | **Clustering Key**            | **Optimization Goal**                          | **Anti-Pattern**                                  |
|-----------------------|--------------------------------|-----------------------------------------------|--------------------------------------------------|
| `event_type`          | `event_type, user_id`          | Faster lookups for user-specific events       | Over-clustering (e.g., clustering on 10+ columns)|

### **Query Examples**
#### **Clustered Query (Reduces Scan)**
```sql
-- Without clustering (scans entire partition):
SELECT * FROM `project.dataset.events`
WHERE event_type = 'login' AND user_id = '123';

-- With clustering (only scans clustered rows):
SELECT * FROM `project.dataset.events`
WHERE event_type = 'login' AND user_id = '123';
```

#### **Create Clustered Table**
```sql
CREATE TABLE `project.dataset.clustered_events`
PARTITION BY DATE(timestamp)
CLUSTER BY event_type, user_id
AS
SELECT * FROM `project.dataset.events`;
```

---

## **Pattern 3: Schema Design**
Design schemas to balance flexibility and query efficiency.

### **Schema Reference**
| **Schema Type**       | **Structure**               | **Use Case**                          | **Tradeoff**                                  |
|-----------------------|-----------------------------|----------------------------------------|-----------------------------------------------|
| **Normalized**        | Separate tables for entities | Complex transactions (e.g., orders + items) | Higher join costs.                          |
| **Denormalized**      | Single table with repeated fields | Simplified ETL (e.g., `users_with_orders`) | Storage inefficiency.                        |
| **Time-Series**       | Nested/repeated columns     | Multi-event per user (e.g., `events` ARRAY) | Query complexity increases.                   |

### **Query Examples**
#### **Normalized Schema (Joins)**
```sql
SELECT
  u.user_id, u.name,
  o.order_id, SUM(oi.quantity * oi.price) AS total
FROM
  `project.dataset.users` u
JOIN
  `project.dataset.orders` o ON u.user_id = o.user_id
JOIN
  `project.dataset.order_items` oi ON o.order_id = oi.order_id
GROUP BY
  u.user_id, u.name, o.order_id;
```

#### **Denormalized Schema (Flattened)**
```sql
SELECT
  user_id, name,
  array_agg(order_id) AS orders,
  SUM(total_amount) AS lifetime_spend
FROM
  `project.dataset.users_with_orders`
GROUP BY
  user_id, name;
```

---

## **Pattern 4: Data Modeling**
Choose between **star schema**, **snowflake schema**, or **flattened schema** based on query patterns.

### **Schema Reference**
| **Model**             | **Description**                          | **Best For**                           | **Example Table Structure**               |
|-----------------------|------------------------------------------|-----------------------------------------|-------------------------------------------|
| **Star Schema**       | Central fact table + dimension tables   | OLAP reporting                          | `fact_sales`, `dim_date`, `dim_product`   |
| **Snowflake Schema**  | Normalized dimensions (further split)    | High cardinality dimensions            | `fact_sales`, `dim_customer` (split by `region`) |
| **Flattened Schema**  | Single table with repeated fields       | Simplicity over performance            | `all_data` (denormalized)                 |

### **Query Examples**
#### **Star Schema Query**
```sql
SELECT
  d.date_id, d.day_name,
  SUM(f.sales_amount) AS daily_sales
FROM
  `project.dataset.fact_sales` f
JOIN
  `project.dataset.dim_date` d ON f.date_id = d.date_id
WHERE
  d.month = 12
GROUP BY
  d.date_id, d.day_name;
```

#### **Snowflake Schema (Optimized for Cardinality)**
```sql
SELECT
  c.customer_id, r.region_name,
  SUM(s.sales_amount) AS region_sales
FROM
  `project.dataset.fact_sales` s
JOIN
  `project.dataset.dim_customer` c ON s.customer_id = c.customer_id
JOIN
  `project.dataset.dim_region` r ON c.region_id = r.region_id
GROUP BY
  c.customer_id, r.region_name;
```

---

## **Query Optimization Best Practices**
1. **Leverage Partition Pruning**: Always filter by `_PARTITIONTIME` or integer partition keys.
2. **Limit Clustered Columns**: Use 2–3 columns max for clustering to avoid over-scanning.
3. **Avoid SELECT ***: Explicitly list columns to reduce I/O.
4. **Use Materialized Views**: Pre-compute aggregations (e.g., daily metrics).
   ```sql
   CREATE MATERIALIZED VIEW `project.dataset.daily_metrics`
   AS
   SELECT
     DATE(timestamp) AS date,
     COUNT(DISTINCT user_id) AS active_users
   FROM
     `project.dataset.events`
   GROUP BY
     date;
   ```

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Impact**                          | **Solution**                                  |
|---------------------------------------|-------------------------------------|-----------------------------------------------|
| Over-partitioning                     | High storage costs, fragmented data | Consolidate small partitions; use `MERGE`      |
| Unclustered frequently filtered cols   | Full table scans                     | Cluster on high-cardinality filter columns    |
| Schema drift                          | Broken queries                      | Use `INFORMATION_SCHEMA` for validation      |
| Ignoring slot reservations             | Unpredictable costs                 | Reserve slots for critical workloads          |

---

## **Related Patterns**
1. **[BigQuery Query Optimization](link)** – Advanced techniques for JOINs, CTEs, and window functions.
2. **[BigQuery Data Pipeline Patterns](link)** – Patterns for ETL (e.g., batch vs. streaming).
3. **[BigQuery Security Patterns](link)** – IAM roles, column-level security, and data masking.
4. **[BigQuery Cost Control Patterns](link)** – Slot allocation, query caching, and pricing tiers.

---
**Last Updated**: [YY/MM/DD]
**Feedback**: [Contact Link]