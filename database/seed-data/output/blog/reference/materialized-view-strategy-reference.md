# **[Pattern] Materialized View Reference Guide**

## **Overview**
The **Materialized View Strategy** pattern addresses performance bottlenecks by pre-computing and storing expensive aggregations or derived results, avoiding repeated computation during runtime. This pattern is ideal for scenarios where frequent reads of large datasets (e.g., reports, dashboards, or analytical queries) dominate the workload. By materializing results in a separate table or cache, query execution improves significantly while reducing load on source systems.

The pattern is particularly useful for:
- **Data warehouses** (e.g., Snowflake, Redshift)
- **OLAP databases** (e.g., PostgreSQL, ClickHouse)
- **Analytics platforms** where query performance is critical.

Unlike indexes, materialized views store entire result sets, making them highly effective for multidimensional aggregations (e.g., time-series rollups, pivot tables).

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Use Case**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Base Table**         | The source table(s) that feed data into the materialized view.                                     | `sales`, `customers`, or `transactions`.                                                          |
| **Materialized View**  | A pre-computed table containing aggregated or derived results.                                     | Pre-calculated daily/weekly revenue by region.                                                  |
| **Refresh Strategy**   | Defines how/when the materialized view is updated (e.g., incremental, full refresh).              | Automated nightly full refresh or real-time incremental updates.                                |
| **Query Reuse**        | Leveraging the materialized view to return results without recomputing from source.               | Avoiding expensive `GROUP BY` or `JOIN` operations on large datasets.                            |
| **Incremental Update** | Updating only changed data (via timestamps/primary keys) to reduce refresh overhead.               | Real-time analytics on streaming data (e.g., Kafka → database).                                 |

---

## **Schema Reference**
Below are common schema patterns for materialized views.

### **1. Basic Aggregation (Time-Based Rollup)**
```sql
-- Source table (e.g., sales transactions)
CREATE TABLE sales (
    transaction_id UUID PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    customer_id INT REFERENCES customers(customer_id),
    amount DECIMAL(10,2),
    transaction_date TIMESTAMP
);

-- Materialized view (daily revenue by product)
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT
    product_id,
    DATE(transaction_date) AS day,
    SUM(amount) AS total_revenue,
    COUNT(*) AS transactions_count
FROM sales
GROUP BY product_id, DATE(transaction_date);
```

| **Column**          | **Type**       | **Description**                                      |
|---------------------|----------------|------------------------------------------------------|
| `product_id`        | `INT`          | Foreign key to `products(product_id)`.                |
| `day`               | `DATE`         | Aggregated by day (pre-computed).                    |
| `total_revenue`     | `DECIMAL(10,2)`| Sum of `amount` for the day.                          |
| `transactions_count`| `INT`          | Count of transactions.                                |

---

### **2. Multi-Dimensional Pivot (Cross-Tabular Aggregation)**
```sql
-- Source: customer segments + regions
CREATE TABLE customer_segment_views AS
SELECT
    customer_id,
    region,
    segment,
    COUNT(*) AS customer_count,
    SUM(sales) AS total_spend
FROM customer_streams
GROUP BY customer_id, region, segment;
```

| **Column**          | **Type** | **Description**                                      |
|---------------------|----------|------------------------------------------------------|
| `region`            | `VARCHAR`| e.g., `North America`, `Europe`.                    |
| `segment`           | `VARCHAR`| e.g., `Premium`, `Standard`.                         |
| `customer_count`    | `INT`    | Pre-computed count of customers in the segment.      |
| `total_spend`       | `DECIMAL`| Sum of spending for the segment/region.              |

---

### **3. Window Function Materialized View**
```sql
-- Source: time-series metrics (e.g., server load)
CREATE MATERIALIZED VIEW mv_load_trends AS
SELECT
    server_id,
    DATE_TRUNC('hour', timestamp) AS hour,
    value AS load,
    AVG(value) OVER (
        PARTITION BY server_id
        ORDER BY timestamp
        ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_24h
FROM server_metrics;
```

| **Column**          | **Type**       | **Description**                                      |
|---------------------|----------------|------------------------------------------------------|
| `server_id`         | `INT`          | Identifies the server.                               |
| `hour`              | `TIMESTAMPTZ`  | Truncated to hourly granularity.                     |
| `load`              | `FLOAT`        | Current load value.                                  |
| `rolling_avg_24h`   | `FLOAT`        | 24-hour rolling average (window function).           |

---

## **Query Examples**
### **1. Querying a Materialized View Directly**
```sql
-- Fast lookup for weekly revenue by product
SELECT
    product_id,
    SUM(total_revenue) AS weekly_revenue
FROM mv_daily_revenue
WHERE day BETWEEN '2023-11-01' AND '2023-11-07'
GROUP BY product_id;
```
**Performance:** O(1) for pre-aggregated data vs. O(n log n) for recomputing from `sales`.

---

### **2. Incremental Refresh (PostgreSQL Example)**
```sql
-- Define a refresh policy with incremental changes
REFRESH MATERIALIZED VIEW mv_daily_revenue
WITH DATA
FROM sales
WHERE transaction_date > (SELECT MAX(day) FROM mv_daily_revenue);
```
**Key:** Only processes new/updated rows since the last refresh.

---

### **3. Joining Base Table + Materialized View**
```sql
-- Correlate pre-aggregated trends with real-time data
SELECT
    m.product_id,
    m.total_revenue,
    s.last_order_date
FROM mv_daily_revenue m
JOIN (
    SELECT product_id, MAX(transaction_date) AS last_order_date
    FROM sales
    GROUP BY product_id
) s ON m.product_id = s.product_id;
```

---

### **4. Conditional Aggregation via MV**
```sql
-- Filtered aggregation (e.g., "high-value customers")
SELECT
    region,
    SUM(total_spend) AS regional_spend
FROM customer_segment_views
WHERE segment = 'Premium'
GROUP BY region;
```

---

## **Refresh Strategies**
| **Strategy**         | **When to Use**                                  | **Example Syntax**                                  |
|----------------------|--------------------------------------------------|----------------------------------------------------|
| **Full Refresh**     | Low-frequency updates (daily/weekly).           | `REFRESH MATERIALIZED VIEW mv_name WITH DATA;`     |
| **Incremental**      | High-frequency updates (real-time).              | Check for `WHERE timestamp > last_refresh_time`.   |
| **Time-Based**       | Scheduled (e.g., hourly/daily).                 | CRON job with `REFRESH` command.                  |
| **Manual Trigger**   | On-demand (e.g., after ETL).                     | Run `REFRESH` via application logic.               |

---

## **Performance Considerations**
- **Storage Overhead:** Materialized views duplicate data. Trade-off: faster reads vs. higher storage.
- **Refresh Overhead:** Full refreshes can block writes. Use incremental updates for high-throughput systems.
- **Stale Data:** Define a "validity window" (e.g., "MV is accurate within 5 minutes").
- **Concurrency:** Avoid refreshes during peak query loads. Use asynchronous refreshes (e.g., background jobs).

---

## **Related Patterns**
| **Pattern**               | **Connection to Materialized View**                                                                 | **When to Pair**                                      |
|---------------------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **CQRS**                  | Separates read (materialized views) and write (base tables) paths.                                    | For microservices with analytical workloads.         |
| **Event Sourcing**        | Materialized views can consume events for incremental updates.                                       | Real-time analytics on event streams.                 |
| **Partitioning**          | Combine with partitioned base tables for scalable refreshes.                                        | Large datasets (e.g., daily partitions).              |
| **Caching (Redis)**       | Materialized views feed a cache layer for sub-millisecond latency.                                  | Low-latency API responses.                           |
| **Denormalization**       | Pre-compute joins to flatten query plans.                                                           | OLAP-heavy workloads with high JOIN complexity.       |

---

## **Anti-Patterns**
1. **Over-Materializing:**
   - *Problem:* Creating too many MVs leads to maintenance overhead.
   - *Fix:* Prioritize high-impact queries (e.g., top 10% slowest).

2. **Ignoring Refresh Overhead:**
   - *Problem:* Full refreshes on large tables cause downtime.
   - *Fix:* Use incremental strategies or schedule refreshes off-peak.

3. **Materializing ephemeral data:**
   - *Problem:* Views that change too frequently lose value.
   - *Fix:* Only materialize stable aggregations (e.g., daily metrics).

4. **Not validating MV accuracy:**
   - *Problem:* Discrepancies between MV and base data.
   - *Fix:* Regularly run `SELECT * FROM mv_name EXCEPT SELECT ... FROM base_table`.

---

## **Tools & Frameworks**
| **Tool/Database**       | **Materialized View Support**                                                                     |
|-------------------------|--------------------------------------------------------------------------------------------------|
| **PostgreSQL**          | Native `CREATE MATERIALIZED VIEW; REFRESH [MULTI|CONCURRENT]`.                               |
| **Snowflake**           | `CREATE MATERIALIZED VIEW ... CLUSTER BY` + auto-incremental refresh.                           |
| **Redshift**            | `CREATE MATERIALIZED VIEW` + `REFRESH` command.                                                 |
| **ClickHouse**          | `CREATE MATERIALIZED VIEW` with `ENGINE = MergeTree`.                                          |
| **Presto/Spark SQL**    | Temporary MVs via `WITH` clauses or `CREATE VIEW` (persistent).                               |
| **Apache Druid**        | Pre-aggregation via segments (similar concept).                                                  |

---
**Note:** Some tools require manual partitioning or external tools (e.g., Airflow) for orchestration.

---
**End of Reference Guide** (Word count: ~950)