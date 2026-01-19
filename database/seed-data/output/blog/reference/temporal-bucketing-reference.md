# **[Pattern] Temporal Bucketing for Time-Series Analytics**

---
## **1. Overview**
Temporal bucketing is a **database-driven** technique for organizing time-stamped data into discrete time intervals (e.g., days, weeks, months). By leveraging SQL functions like `DATE_TRUNC`, `DATE_FORMAT`, or `DATEPART`, you can aggregate raw event data into structured buckets for efficient time-series analytics.

Common use cases include:
- **Daily sales** (e.g., "Revenue per day")
- **Weekly active users** (e.g., "User engagement trends")
- **Monthly recurring revenue** (e.g., "MRR by contract term")

This pattern ensures **query performance** (typically **5–10ms** for 1M+ rows when indexed on the timestamp column) while minimizing application logic complexity.

---

## **2. Schema Reference**

| Column       | Data Type       | Description                                                                 |
|--------------|-----------------|-----------------------------------------------------------------------------|
| `timestamp`  | `TIMESTAMP`     | The original event or metric timestamp (indexed for performance).          |
| `bucket_key` | `VARCHAR`/`DATE`| Derived column grouping events into time intervals (e.g., `YYYY-MM-DD`). |

### **Supported Database Functions**
| Database    | Function          | Purpose                                                                 |
|-------------|-------------------|-------------------------------------------------------------------------|
| PostgreSQL  | `DATE_TRUNC(interval, timestamp)` | Truncate to second/hour/day/week/month/quarter/year.                   |
| MySQL       | `DATE_FORMAT(timestamp, '%Y-%m-%d')`  | Format as string (`YYYY-MM-DD`).                                        |
| SQLite      | `strftime('%Y-%m-%d', timestamp)`   | Format using `%` directives (`%Y` = year, `%m` = month, etc.).         |
| SQL Server  | `DATEPART(part, timestamp)`        | Extract `YEAR`, `MONTH`, `DAY`, `HOUR`, etc. (`DATEPART('YEAR', ...)`). |

### **Performance Considerations**
- **Indexing**: Ensure the `timestamp` column is indexed for fast bucketing.
- **Storage**: Store `bucket_key` as a `DATE` or `VARCHAR` to save space.
- **Aggregation**: Pre-aggregate (e.g., `COUNT`, `SUM`) in the same query to avoid post-processing.

---

## **3. Query Examples**

### **Example 1: Daily Sales Aggregation (PostgreSQL)**
```sql
-- Bucket sales by day, then sum revenue
SELECT
    DATE_TRUNC('day', transaction.timestamp) AS daily_bucket,
    SUM(amount) AS daily_revenue
FROM transactions
GROUP BY daily_bucket
ORDER BY daily_bucket;
```

### **Example 2: Weekly Active Users (MySQL)**
```sql
-- Count unique users per week (Monday–Sunday)
SELECT
    DATE_FORMAT(timestamp, '%Y-%u') AS weekly_bucket, -- Week of year (01–53)
    COUNT(DISTINCT user_id) AS weekly_active_users
FROM user_events
GROUP BY weekly_bucket
ORDER BY weekly_bucket;
```

### **Example 3: Monthly Recurring Revenue (SQLite)**
```sql
-- MRR by month (string format)
SELECT
    strftime('%Y-%m', timestamp) AS monthly_bucket,
    SUM(revenue) AS mrr
FROM subscriptions
GROUP BY monthly_bucket
ORDER BY monthly_bucket;
```

### **Example 4: Hourly Traffic Trends (SQL Server)**
```sql
-- Hourly traffic by day
SELECT
    DATEPART(YEAR, event_time) AS year,
    DATEPART(MONTH, event_time) AS month,
    DATEPART(HOUR, event_time) AS hour,
    COUNT(*) AS event_count
FROM logs
GROUP BY YEAR, MONTH, HOUR
ORDER BY year, month, hour;
```

---

## **4. Implementation Patterns**

### **A. Materialized Views (Pre-Aggregation)**
For frequently queried metrics, create a materialized view to avoid repeated bucketing:
```sql
-- PostgreSQL example: Refresh hourly
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT
    DATE_TRUNC('day', t.timestamp) AS day,
    SUM(t.amount) AS revenue
FROM transactions t
GROUP BY day;

-- Refresh logic (e.g., cron job)
REFRESH MATERIALIZED VIEW daily_revenue;
```

### **B. Time-Based Partitioning**
Partition tables by date ranges (e.g., monthly) to optimize storage and queries:
```sql
-- PostgreSQL: Create a partitioned table
CREATE TABLE analytics_data (
    timestamp TIMESTAMP,
    metric_value INTEGER
) PARTITION BY RANGE (DATE_TRUNC('month', timestamp));

-- Add partitions dynamically
CREATE TABLE analytics_data_y2023m01 PARTITION OF analytics_data
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
```

### **C. Hybrid Approach (Bucketing + Pre-Aggregation)**
Combine bucketing with pre-computed aggregates for balance:
1. **Raw data**: Store original events with `timestamp` indexed.
2. **Aggregates**: Store pre-computed buckets (e.g., `daily_metrics`) in a separate table.

```sql
-- Example schema for hybrid approach
CREATE TABLE event_buckets (
    bucket_date DATE PRIMARY KEY,
    event_count BIGINT,
    avg_duration INTERVAL
);
```

---

## **5. Best Practices**

| Practice               | Guidance                                                                 |
|------------------------|---------------------------------------------------------------------------|
| **Indexing**           | Index `timestamp` (and `bucket_key` if used directly).                     |
| **Bucket Granularity** | Start coarse (e.g., daily), then refine (e.g., hourly) for high-cardinality data. |
| **Time Zones**         | Standardize to UTC or a fixed timezone to avoid ambiguity.                 |
| **Empty Buckets**      | Use `LEFT JOIN` or `COALESCE` to handle missing intervals.                |
| **Dynamic Buckets**    | For variable intervals (e.g., rolling 7-day averages), use window functions. |

---

## **6. Edge Cases & Solutions**

| Issue                     | Solution                                                                 |
|---------------------------|---------------------------------------------------------------------------|
| **Sparse Data**           | Use `RIGHT JOIN` or `FULL OUTER JOIN` to include all dates.               |
| **Time Zone Conflicts**   | Cast timestamps to a fixed timezone before bucketing.                     |
| **High Cardinality**      | Use `DATE_TRUNC('month', ...)` for fewer buckets than `day`.             |
| **Real-Time Updates**     | Consider incremental aggregation (e.g., update pre-aggregates on insert). |

---

## **7. Related Patterns**
- **[Time-Series Partitioning](link)**: Organize data by fixed time ranges (e.g., monthly).
- **[Sliding Window Aggregations](link)**: Compute rolling averages (e.g., 7-day MA).
- **[Event Time vs. Processing Time](link)**: Differentiate between event timestamps and query execution time.
- **[Columnar Storage for Time-Series](link)**: Use Parquet/ORC for optimized analytics.

---
**Next Steps**:
- Review your database’s bucketing function syntax.
- Benchmark performance with indexed vs. non-indexed queries.
- Pre-aggregate if queries are read-heavy.