---
# **[Pattern] Efficiency Conventions Reference Guide**

---

## **1. Overview**
The **Efficiency Conventions** pattern defines standardized data structures and query practices to optimize performance in data pipelines, analytics, and storage systems. By enforcing conventions around granularity, indexing, and query design, this pattern minimizes redundant computations, reduces storage bloat, and accelerates read/write operations. It is particularly valuable in time-series data, log aggregation, and large-scale distributed systems where inefficiencies can cascade into latency or resource contention.

**Key Goals:**
- **Granularity Alignment**: Ensure data is partitioned and indexed at the most efficient level for query workloads.
- **Indexing Economy**: Avoid over-indexing (redundant storage) while ensuring critical query paths are supported.
- **Materialization Control**: Pre-compute or lazy-load aggregated data based on access patterns.
- **Query Pattern Standardization**: Enforce predictable query structures (e.g., time-range filters, key-based lookups) to optimize plan generation.

---
## **2. Schema Reference**

### **Core Keywords & Conventions**
| **Term**               | **Definition**                                                                 | **Example Use Case**                          |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Grain**              | The lowest level of data granularity (e.g., second, hour, event).              | Time-series: `1-minute` granularity for metrics. |
| **Partitioning Schema** | How data is split (e.g., `time_bucket`, `customer_id`, `log_type`).          | `PARTITION BY time(ts, '1h')`.                |
| **Indexing Strategy**  | Primary (clustering) and secondary indexes (e.g., `(ts, metric)`).          | Time-series: `(ts DESC)` for recent data access. |
| **Materialization**    | Pre-computed aggregations (e.g., `SUM`, `AVG`) stored at a higher grain.     | `WITHIN HOUR` aggregations for daily reports.   |
| **Query Template**     | Standardized filter/join patterns (e.g., `WHERE ts BETWEEN ...`).            | `ts >= '2023-01-01' AND ts < '2023-01-02'`.    |

---

### **Example Schema Designs**
#### **a. Time-Series Data**
| **Field**       | **Type**       | **Convention**                          | **Notes**                                  |
|-----------------|----------------|-----------------------------------------|--------------------------------------------|
| `ts`            | `TIMESTAMP`    | Primary grain (e.g., `1s`, `5m`).       | Always indexed.                             |
| `metric_name`   | `STRING`       | Partition key.                          | Reduces I/O for single-metric queries.      |
| `value`         | `FLOAT`        | --                                       | Materialize sums/avgs at hour/daily levels. |
| `_aggregated`   | `BOOLEAN`      | Flag for pre-computed rows.              | Avoid recomputing during reads.            |

#### **b. Event Logs**
| **Field**       | **Type**       | **Convention**                          | **Notes**                                  |
|-----------------|----------------|-----------------------------------------|--------------------------------------------|
| `event_id`      | `UUID`         | Clustering key.                         | Fast lookups by ID.                        |
| `user_id`       | `STRING`       | Secondary index.                        | Common filter.                             |
| `event_time`    | `TIMESTAMP`    | Partitioning: `HOUR`.                    | Time-range queries optimized.              |
| `payload`       | `JSON`         | --                                       | Denormalized for fast access.              |

---
## **3. Implementation Details**

### **A. Granularity**
- **Rule 1:** Align grain with **access patterns**. For example:
  - **Fine grain** (e.g., `1s`) for ad-hoc queries.
  - **Coarse grain** (e.g., `1d`) for dashboards.
- **Trade-off:** Higher grain = less storage but slower point queries.
- **Implementation:**
  ```sql
  -- Pre-compute daily aggregations from fine-grained data
  CREATE TABLE hourly_metrics AS
  SELECT ts_bucket, metric_name, AVG(value) as avg_value
  FROM raw_metrics
  GROUP BY ts_bucket, metric_name;
  ```

### **B. Indexing**
- **Primary Index:** Always align with the **grain** (e.g., `(ts DESC)` for time-series).
- **Secondary Indexes:** Limit to **frequently filtered columns** (e.g., `user_id`, `log_type`).
  - **Avoid:** Indexing low-cardinality fields unless critical.
- **Example:**
  ```sql
  CREATE INDEX idx_user_id ON event_logs(user_id);
  ```

### **C. Materialization**
| **Strategy**          | **When to Use**                          | **Example**                                  |
|-----------------------|-----------------------------------------|----------------------------------------------|
| **Pre-aggregation**   | High-read, low-write patterns (e.g., reports). | `CREATE MATERIALIZED VIEW daily_sales AS ...` |
| **Lazy Materialization** | Ad-hoc queries (e.g., "show me all X where Y"). | Use `WITHIN` clauses in SQL (e.g., `WITHIN 1d`). |
| **View Over Tables**  | Virtual aggregations without storage cost. | `CREATE VIEW weekly Trends AS SELECT ... GROUP BY WEEK(ts)`. |

### **D. Query Patterns**
- **Standardize Filters:**
  - **Time-ranges:** Always use `<=`/`<` for open/closed intervals.
    ```sql
    -- Preferred (excludes end boundary)
    SELECT * FROM metrics WHERE ts >= '2023-01-01' AND ts < '2023-01-02';
    ```
  - **Key Lookups:** Use `=` for exact matches.
    ```sql
    SELECT * FROM logs WHERE user_id = 'user123';
    ```
- **Avoid Anti-Patterns:**
  - **Full scans:** `SELECT *` on large tables.
  - **Unbounded ranges:** `ts > '2020-01-01'` (use `ts >= ... AND ts < NOW()`).
  - **Wildcards in joins:** `LIKE '%user%'` on indexed columns.

---
## **4. Query Examples**

### **Example 1: Time-Series Aggregation (Optimized)**
```sql
-- Request: "Show hourly CPU usage for 'server_a' yesterday."
-- Convention: Pre-aggregated hourly data + time-range filter.
SELECT
    ts_bucket,
    AVG(value) as cpu_avg,
    COUNT(*) as samples
FROM hourly_cpu_usage
WHERE
    metric_name = 'server_a'
    AND ts_bucket >= '2023-01-01 00:00'
    AND ts_bucket < '2023-01-02 00:00'
ORDER BY ts_bucket;
```

### **Example 2: Event Log Filtering**
```sql
-- Request: "List all login events for user_id 'admin' in the last 7 days."
-- Convention: Partitioned by hour + secondary index on user_id.
SELECT
    event_id,
    event_time,
    payload
FROM event_logs
WHERE
    user_id = 'admin'
    AND event_time >= NOW() - INTERVAL '7 days'
ORDER BY event_time DESC;
```

### **Example 3: Unoptimized Query (Anti-Pattern)**
```sql
-- Inefficient: Full scan + unbounded time range + wildcard.
SELECT
    ts,
    value
FROM raw_metrics
WHERE
    ts > '2020-01-01'  -- Unbounded (risks high cardinality)
    AND metric_name LIKE '%load%';  -- Wildcard on indexed column
```
**Problem:** Likely triggers a full table scan and high I/O.

---
## **5. Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use Together**                          |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| **Schema Evolution**      | Ensure backward compatibility when applying Efficiency Conventions.           | Migrating from raw to pre-aggregated schemas.    |
| **Data Lifecycle**        | Tier data by access frequency (hot/warm/cold) to optimize storage.            | For large-scale log/data lakes.                   |
| **Query Federation**      | Split queries across optimized sources (e.g., pre-agg tables + raw).          | When multiple grains are needed (e.g., admins vs. users). |
| **Caching Strategy**      | Cache frequently accessed materialized views to reduce compute.               | For read-heavy dashboards.                        |
| **Idempotent Writes**     | Ensure efficiency conventions don’t break on duplicate updates.              | In event-sourced systems.                         |

---
## **6. Error Handling & Debugging**
- **Symptoms of Inefficiency:**
  - Long query durations (check `EXPLAIN ANALYZE`).
  - High I/O or CPU usage (monitor database metrics).
  - Unbounded result sets (e.g., missing `LIMIT` or `BETWEEN`).
- **Debugging Steps:**
  1. **Profile Queries:** Use `EXPLAIN` to identify full scans or inefficient joins.
  2. **Review Schema:** Ensure grain/partitioning matches access patterns.
  3. **Check Materialization:** Verify pre-computed aggregations are up-to-date.
  4. **Test Edge Cases:** Validate queries with extreme filter values (e.g., `ts = NULL`).

---
## **7. Example Migration Plan**
1. **Audit Current Schema:**
   - Identify grain misalignment (e.g., `1ms` for dashboard data).
   - List unused indexes or redundant materializations.
2. **Design New Schema:**
   - Define target grain (e.g., `1h` for metrics).
   - Create materialized views for common queries.
3. **Incremental Rollout:**
   - Stage pre-aggregated tables alongside raw data.
   - Gradually shift queries to use new conventions.
4. **Monitor & Optimize:**
   - Compare query performance pre/post-migration.
   - Adjust materialization based on access patterns.

---
## **8. Tools & Frameworks**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Apache Druid**       | Optimized for time-series with pre-aggregations and columnar storage.       |
| **ClickHouse**         | Efficient partitioning and materialized views for high-cardinality data.   |
| **Delta Lake**         | Schema enforcement + time-travel queries for data lakes.                   |
| **Presto/Trino**       | Query federation across optimized sources.                               |
| **Prometheus**         | Pre-built efficiency conventions for metrics (scraping + aggregation).     |

---
## **9. Best Practices Checklist**
- [ ] Align grain with **80/20 query patterns** (Pareto principle).
- [ ] Limit secondary indexes to **top 3–5 frequently filtered columns**.
- [ ] Pre-aggregate **read-heavy, write-sparse** data (e.g., reports).
- [ ] Document **query templates** for teams to follow.
- [ ] Schedule **materialized view refreshes** during low-traffic periods.
- [ ] Use **partition pruning** (e.g., `ts BETWEEN ...`) to avoid full scans.