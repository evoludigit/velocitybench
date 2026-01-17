# **[Pattern] Partitioning & Time-Series Data Reference Guide**

## **Overview**
Partitioning is a database optimization technique that splits large tables into smaller, manageable segments—called *partitions*—to improve query performance, simplify maintenance, and enforce data lifecycle policies. This pattern is critical for **time-series data**, where historical data is often queried in temporal ranges (e.g., hourly, daily, or monthly aggregates).

By partitioning data by time or other logical keys (e.g., region, customer ID), systems reduce I/O overhead, accelerate analytics, and enable efficient archival or deletion of stale data. For time-series workloads, partitioning aligns with the natural temporal granularity of events (e.g., sensor readings, logs), ensuring that only relevant partitions are scanned during queries. Common partitioning strategies include:
- **Time-based** (e.g., `YYYY-MM-DD` for daily partitions)
- **Range-based** (e.g., integer IDs, numeric ranges)
- **List-based** (e.g., fixed categories like `region A, B, C`)

This guide covers key concepts, schema design, query patterns, and tools for implementing partitioning effectively.

---

## **Schema Reference**

### **1. Partitioned Table Structure**
A partitioned table typically follows this schema convention:

| Column | Type          | Description                                                                 |
|--------|---------------|-----------------------------------------------------------------------------|
| `event_id` | UUID/SERIAL  | Unique identifier for each record.                                           |
| `timestamp` | TIMESTAMP    | When the event occurred (partition key).                                     |
| `metric_value` | FLOAT/INT    | Numeric value of the time-series event (e.g., temperature, stock price).     |
| `sensor_id`  | VARCHAR       | Identifier for the source (e.g., `sensor_123`).                               |
| `location`   | VARCHAR       | Geographic or logical grouping (e.g., `us-east-1`).                          |
| `other_metadata` | JSONB/TEXT | Additional attributes (e.g., `{ "status": "active", "tags": ["important"] }`). |

### **2. Partition Key Examples**
| Strategy       | Example Partition Scheme                          | Use Case                                  |
|----------------|---------------------------------------------------|-------------------------------------------|
| **Date-based** | `partition_key = date_trunc('day', timestamp)`    | Daily aggregates for logs/metrics.        |
| **Time-based** | `partition_key = date_trunc('hour', timestamp)`   | High-frequency time-series data.         |
| **Range-based**| `partition_key = (sensor_id::text || '-' || metric_value)` | Grouping by sensor + value ranges.      |
| **List-based** | `partition_key = location` (predefined values)    | Regional data isolation.                 |

### **3. Partitioning Syntax (PostgreSQL Example)**
```sql
-- Create a time-based partitioned table
CREATE TABLE time_series_data (
    event_id UUID,
    timestamp TIMESTAMP NOT NULL,
    metric_value FLOAT,
    sensor_id VARCHAR(50),
    location VARCHAR(50)
) PARTITION BY RANGE (timestamp);

-- Create daily partitions for 30 days ahead
CREATE TABLE time_series_data_y2023m01 PARTITION OF time_series_data
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');

CREATE TABLE time_series_data_y2023m02 PARTITION OF time_series_data
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
-- Repeat for future partitions (e.g., using a script).
```

> **Note**: Syntax varies by database (e.g., `DATE_TRUNC` in PostgreSQL vs. `DATE` functions in MySQL/SQL Server). See [Database-Specific Partitioning](#database-specific-guidelines) for details.

---

## **Query Examples**

### **1. Querying Partitioned Data**
Partitioned tables automatically filter scans to relevant partitions. Example:
```sql
-- Efficiently query data from a specific day (only scans `time_series_data_y2023m01`).
SELECT * FROM time_series_data
WHERE timestamp BETWEEN '2023-01-15' AND '2023-01-20';
```

### **2. Aggregations Across Partitions**
```sql
-- Sum metric values by sensor, partitioned by day.
SELECT
    sensor_id,
    DATE(timestamp) AS day,
    SUM(metric_value) AS total
FROM time_series_data
WHERE timestamp >= '2023-01-01'
GROUP BY sensor_id, DATE(timestamp)
ORDER BY day;
```

### **3. Partition Pruning**
Databases prune irrelevant partitions. Example:
```sql
-- Only scans partitions where date_trunc('month', timestamp) = '2023-01'.
SELECT AVG(metric_value)
FROM time_series_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-31';
```

### **4. Managing Partitions**
```sql
-- Attach a new partition for February 2023.
ALTER TABLE time_series_data
ATTACH PARTITION time_series_data_y2023m02
FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');

-- Drop stale partitions (e.g., data older than 1 year).
DROP TABLE IF EXISTS time_series_data_y2022m01;
```

### **5. Handling Large Time Ranges**
For cross-partition queries (e.g., monthly aggregates), use **partitioned indexes**:
```sql
-- Create a GIN index on JSONB data (if applicable).
CREATE INDEX idx_time_series_data_json ON time_series_data USING GIN (other_metadata);
```

---

## **Database-Specific Guidelines**

| Database       | Partitioning Features                          | Example Command                          |
|----------------|-----------------------------------------------|------------------------------------------|
| **PostgreSQL** | `RANGE` (date, integer), `LIST`, `HASH`      | `PARTITION BY RANGE (date_trunc('day', col))` |
| **MySQL**      | `RANGE` (column), `LIST`, `KEY` (hashed)     | `PARTITION BY RANGE (YEAR(col))`         |
| **SQL Server** | `RANGE` (dates, rows), `LIST`, `HASH`        | `PARTITION BY RANGE RIGHT FOR VALUES FROM`|
| **BigQuery**   | Automatic time-partitioned tables            | `-- Partition by DATE(timestamp)`        |
| **Snowflake**  | `DATE_TRUNC`, `GENERATOR` for dynamic parts | `CLUSTER BY DATE_TRUNC('DAY', timestamp)`|

> **Pro Tip**: Use **partition elimination** (e.g., `WHERE` clauses) to avoid full table scans. Monitor partition sizes with:
> ```sql
> -- PostgreSQL example
> SELECT tablename, relname, pg_size_pretty(pg_total_relation_size(oid))
> FROM pg_tables
> JOIN pg_class ON pg_tables.tablename = pg_class.relname;
> ```

---

## **Best Practices**

### **1. Partition Key Selection**
- **Time-series**: Use `DATE_TRUNC` (PostgreSQL) or `DATE` functions to avoid skew.
- **Range partitions**: Avoid uneven splits (e.g., `PARTITION BY RANGE (id)` where `id` is skewed).
- **List partitions**: Limit to ~100 partitions to avoid overhead.

### **2. Partition Maintenance**
- **Automate partition creation**: Use scripts to pre-create future partitions (e.g., weekly).
- **Expiry policies**: Drop old partitions via:
  ```sql
  -- PostgreSQL: Use `pg_cron` or `pg_partman` to auto-drop partitions.
  DROP TABLE IF EXISTS time_series_data_y2022m01;
  ```
- **Vacuum/Analyze**: Regularly run `VACUUM` on partitions to reclaim space.

### **3. Query Optimization**
- **Avoid `SELECT *`**: Fetch only required columns.
- **Use `EXPLAIN ANALYZE`**:
  ```sql
  EXPLAIN ANALYZE
  SELECT sensor_id, AVG(metric_value)
  FROM time_series_data
  WHERE timestamp > '2023-01-01';
  ```
- **Partitioned indexes**: Add indexes on non-partitioned columns (e.g., `sensor_id`).

### **4. Tools & Extensions**
| Tool/Extension       | Purpose                                      |
|----------------------|---------------------------------------------|
| **pg_partman**       | Automate PostgreSQL partition management.    |
| **TimescaleDB**      | Hypertable extension for time-series.       |
| **AWS Timestream**   | Managed time-series database with auto-partitioning. |
| **ClickHouse**       | Columnar DB optimized for fast time-series queries. |

---

## **Related Patterns**

1. **[Time-Series Indexing]**
   - Use **GIN indexes** (for JSON) or **BRIN indexes** (for time-series) to speed up range queries.
   - Example:
     ```sql
     CREATE INDEX idx_time_series_brin ON time_series_data USING BRIN (timestamp);
     ```

2. **[Data Lifecycle Management]**
   - Combine partitioning with **TTL (Time-to-Live)** or **archive tables** to automatically expire old data.
   - Tools: PostgreSQL’s `ALTER TABLE ... SET TTL`, Snowflake’s `CLONE` + `COPY` commands.

3. **[Materialized Views for Time-Series]**
   - Pre-aggregate data into materialized views for dashboards:
     ```sql
     CREATE MATERIALIZED VIEW daily_avg AS
     SELECT
         DATE(timestamp) AS day,
         sensor_id,
         AVG(metric_value) AS avg_value
     FROM time_series_data
     GROUP BY 1, 2;
     -- Refresh periodically:
     REFRESH MATERIALIZED VIEW daily_avg;
     ```

4. **[Sharding for Horizontal Scaling]**
   - For **non-time-series data**, use **hash sharding** (e.g., by `user_id`) to distribute load across nodes.

---

## **Common Pitfalls & Mitigations**

| Pitfall                          | Mitigation                                  |
|----------------------------------|--------------------------------------------|
| **Partition skew** (uneven data distribution) | Use `RANGE` with balanced boundaries (e.g., `PARTITION BY RANGE (id) VALUES (..., ..., ...)`). |
| **Too many small partitions**    | Merge partitions when size exceeds 10GB (PostgreSQL default). |
| **Over-partitioning**            | Limit to ~200 partitions per table.         |
| **Lack of partition indexes**    | Add indexes on frequently queried columns.  |
| **No partition maintenance**     | Schedule `VACUUM`, `ANALYZE`, and cleanup scripts. |

---

## **When to Use This Pattern**
- **Use partitioning when**:
  - Tables exceed **100M+ rows** or **10GB+**.
  - Queries frequently filter by **time, ranges, or categories**.
  - Data has a **natural lifespan** (e.g., logs, sensor data).
- **Avoid partitioning when**:
  - Tables are small (<10M rows).
  - Queries are **write-heavy** (inserts/deletes across partitions add overhead).
  - Partitioning complexity outweighs benefits (e.g., simple CRUD apps).

---
**Final Note**: Partitioning is a powerful tool, but design requires foresight. Monitor partition growth and query plans to ensure optimal performance. For advanced use cases, consider specialized time-series databases like **InfluxDB** or **TimescaleDB**.