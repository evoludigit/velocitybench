# **[Pattern] Materialized Views Reference Guide**

---

## **Overview**
Materialized views are pre-computed query results stored as tables, enabling high-performance read operations by avoiding repeated expensive computations. Ideal for analytics, reporting, and scenarios requiring frequent access to complex aggregations or derived data. This pattern defines how to design, create, and maintain materialized views efficiently, balancing storage overhead with performance gains.

---

## **1. Key Concepts**

| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Base Table**        | Source table(s) containing raw data upon which the materialized view is built.                                                                                                                       |
| **Refresh Strategy**  | Mechanism to update materialized views (frequent incremental updates, full refreshes, or manual triggers).                                                                                               |
| **Refresh Interval**  | Time between updates (e.g., hourly, daily) to ensure data accuracy.                                                                                                                                       |
| **Storage Overhead**  | Trade-off between query speed and disk usage (materialized views persist data).                                                                                                                      |
| **Granularity**       | Level of detail (e.g., hourly, daily) used when aggregating data.                                                                                                                                         |
| **Concurrency**       | Handling concurrent refreshes or reads without conflicts (e.g., locks, partitions).                                                                                                                       |
| **Partitioning**      | Splitting materialized views by time/key to optimize storage and refreshes.                                                                                                                              |
| **Indexing**          | Adding indexes to materialized views for faster lookups (consider cost vs. benefit).                                                                                                                  |
| **TTL (Time-to-Live)**| Automatically drop outdated materialized views to free up space.                                                                                                                                         |
| **View Sources**      | Defines how a materialized view is constructed (e.g., `SELECT * FROM table WHERE date > '2023-01-01'`).                                                                                            |

---

## **2. Schema Reference**

### **Base Table Example**
```sql
CREATE TABLE sales (
    sale_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    sale_date TIMESTAMP NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    region VARCHAR(50) NOT NULL
);
```

### **Materialized View Definition**
```sql
CREATE MATERIALIZED VIEW mv_daily_sales_by_region AS
SELECT
    DATE(sale_date) AS sale_day,
    region,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count
FROM sales
GROUP BY 1, 2;
```

### **Common Supporting Tables**
| Table Name               | Purpose                                                                                                                                               |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `refresh_log`            | Tracks refresh timestamps and statuses.                                                                                                          |
| `mv_ttl_rules`           | Defines TTL policies (e.g., drop `mv_daily_sales_by_region` if `sale_day < CURRENT_DATE - 90`). |
| `partition_metadata`     | Manages partitioned materialized views (e.g., by month).                                                                                         |

---

## **3. Implementation Details**

### **A. Creating Materialized Views**
1. **Static Query-Based Materialized Views**:
   ```sql
   CREATE MATERIALIZED VIEW mv_customer_spend AS
   SELECT customer_id, SUM(amount) AS lifetime_spend
   FROM sales
   GROUP BY customer_id;
   ```
   - *Use Case*: Pre-compute aggregations rarely updated.

2. **Incremental Materialized Views** (for append-only tables):
   ```sql
   CREATE MATERIALIZED VIEW mv_new_customers AS
   SELECT customer_id, sale_date
   FROM sales
   WHERE sale_date > (SELECT MAX(sale_date) FROM mv_new_customers)
   ORDER BY sale_date;
   ```
   - *Use Case*: Track only new data since last refresh.

3. **Partitioned Materialized Views** (e.g., by month):
   ```sql
   CREATE MATERIALIZED VIEW mv_monthly_revenue (
       month_date DATE,
       revenue DECIMAL(10, 2)
   ) PARTITION BY RANGE (month_date);
   ```
   - *Use Case*: Large datasets requiring efficient partitioning.

### **B. Refresh Strategies**

| Strategy               | Implementation                                                                                                                                                     | When to Use                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Full Refresh**       | `REFRESH MATERIALIZED VIEW mv_daily_sales_by_region;`                                                                                                     | Data rarely changes, or full recomputation is acceptable.                                     |
| **Incremental Refresh**| Store `WHERE` clause filters (e.g., `sale_date > last_refresh`) to update only new rows.                                                                   | High-volume append-only data (e.g., logs).                                                   |
| **Scheduled Refresh**  | Use DB scheduler (e.g., `dbt run`, cron jobs, or database-native schedulers like `pg_cron`).                                                                  | Regular updates (e.g., nightly aggregations).                                                |
| **Trigger-Based**      | Run refreshes on DML changes (e.g., `AFTER INSERT ON sales`).                                                                                              | Critical aggregations requiring real-time updates.                                          |
| **Manual Refresh**     | Explicit `REFRESH` calls via API or CLI.                                                                                                                  | Ad-hoc or user-initiated updates.                                                             |

### **C. Performance Considerations**
- **Indexing**: Add indexes to materialized views for frequently filtered columns:
  ```sql
  CREATE INDEX idx_mv_daily_sales_region ON mv_daily_sales_by_region(region);
  ```
- **Partition Pruning**: Query only relevant partitions (e.g., `WHERE month_date BETWEEN '2023-01-01' AND '2023-12-31'`).
- **Storage Optimization**:
  - Compress large materialized views (e.g., `ALTER TABLE mv_large_data SET STORAGE PARQUET`).
  - Use columnar storage for analytics (e.g., ClickHouse, BigQuery).
- **Concurrency**:
  - Avoid locks during refreshes; use **serializable isolation** for critical paths.
  - For high-throughput systems, consider **asynchronous refreshes** (e.g., Kafka + DB updates).

### **D. Maintenance**
1. **TTL Automation**:
   ```sql
   CREATE OR REPLACE FUNCTION drop_old_mvs()
   RETURNS TRIGGER AS $$
   BEGIN
       DELETE FROM mv_daily_sales_by_region
       WHERE sale_day < CURRENT_DATE - INTERVAL '90 days';
       RETURN NULL;
   END;
   $$ LANGUAGE plpgsql;
   ```
   - Schedule with `pg_cron` or Airflow.

2. **Monitoring**:
   ```sql
   -- Track refresh performance
   SELECT mv_name, refresh_timestamp, rows_affected, duration_ms
   FROM mv_refresh_log
   ORDER BY duration_ms DESC LIMIT 10;
   ```
   - Use **Prometheus/Grafana** for dashboards.

3. **Fallback Strategy**:
   - Store a backup of base table snapshots (e.g., `sales_backup_<date>`) to rebuild materialized views if corrupted.

---

## **4. Query Examples**

### **A. Basic Queries**
```sql
-- Retrieve pre-aggregated data
SELECT region, total_sales FROM mv_daily_sales_by_region
WHERE sale_day = '2023-10-01';

-- Filter + join with base table
SELECT m.region, s.product_id
FROM mv_daily_sales_by_region m
JOIN sales s ON m.region = s.region AND m.sale_day = DATE(s.sale_date)
WHERE m.total_sales > 1000;
```

### **B. Advanced Operations**
```sql
-- Time-series analysis (using partitioned MV)
SELECT
    month_date,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY month_date) AS prev_month_revenue,
    revenue - LAG(revenue, 1) OVER (ORDER BY month_date) AS month_over_month_growth
FROM mv_monthly_revenue
WHERE month_date BETWEEN '2023-01-01' AND '2023-12-31';

-- Union with incremental MV
SELECT * FROM mv_new_customers
UNION ALL
SELECT * FROM mv_recent_updates;
```

---

## **5. Error Handling & Edge Cases**

| Scenario                          | Solution                                                                                                                                                     |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Data Skew**                     | Use **salting** (e.g., add random prefix to keys) or **distribute partitions** evenly.                                                                  |
| **Refresh Failures**              | Implement retry logic with exponential backoff. Log errors to `mv_refresh_log`.                                                                |
| **Concurrent Refreshes**          | Use **transaction isolation levels** (e.g., `SERIALIZABLE`) or **asynchronous queues** (e.g., RabbitMQ).                                            |
| **Schema Changes**                | Rebuild materialized views or use **view versioning** (e.g., `mv_daily_sales_v2`).                                                                  |
| **Storage Limits**                | Drop old partitions or use **compression** (e.g., `ORC`, `Snappy`).                                                                                   |
| **Stale Data**                    | Add a `valid_until` column to materialized views and query only rows where `valid_until > NOW()`.                                                     |

---

## **6. Related Patterns**

| Pattern                          | Description                                                                                                                                               | When to Combine                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Batch Processing**              | Process large datasets in chunks (e.g., Spark, Flink).                                                                                                      | When materialized views are updated from external data sources.                                   |
| **Event Sourcing**                | Store data changes as immutable events.                                                                                                                    | For real-time materialized views requiring audit trails.                                            |
| **Sharding**                      | Split data across servers by key (e.g., `customer_id % 10`).                                                                                            | Horizontal scaling of base tables feeding materialized views.                                       |
| **Caching (Redis/Memcached)**     | Cache hot materialized view results for ultra-low latency.                                                                                              | When materialized views are read frequently but updated rarely.                                    |
| **Data Vault**                    | Standardized enterprise data modeling.                                                                                                                    | Complex auditing or compliance requirements for materialized views.                               |
| **Change Data Capture (CDC)**     | Capture row-level changes (e.g., Debezium, AWS DMS).                                                                                                     | For near-real-time materialized view updates.                                                       |

---

## **7. Anti-Patterns**
- **Over-Granularity**: Avoid materializing every possible aggregation (e.g., hourly + daily for the same metric).
- **Unbounded TTL**: Never drop materialized views without a clear cleanup policy.
- **Ignoring Storage Costs**: Materialized views can grow unbounded; set quotas or automate cleanup.
- **No Monitoring**: Without tracking refresh performance or data freshness, materialized views may become outdated.
- **Tight Coupling**: Avoid referencing materialized views in other materialized views without clear dependencies (can cause cascading rebuilds).

---
## **8. Example Workflow**
1. **Define**: Create `mv_daily_sales_by_region` with daily granularity.
2. **Index**: Add an index on `region` for faster queries.
3. **Schedule**: Set up a daily full refresh at 2 AM via `pg_cron`.
4. **Monitor**: Log refresh durations and alert on failures.
5. **Optimize**: Partition by month and enable compression.
6. **Fallback**: Store a daily snapshot of `sales` for recovery.

---
**Tools/Libraries**:
- Databases: PostgreSQL (`REFRESH MATERIALIZED VIEW`), BigQuery, Snowflake, Redshift Spectrum.
- Orchestration: Airflow, dbt (for declarative materialized views), Presto/Trino.
- Monitoring: Prometheus, Datadog, custom SQL queries.