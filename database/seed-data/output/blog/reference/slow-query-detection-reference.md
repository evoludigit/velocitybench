# **[Pattern] Slow Query Detection Reference Guide**

## **Overview**
**Slow Query Detection** is a performance monitoring pattern used to identify and analyze queries that execute slower than predefined thresholds in database systems. This pattern helps pinpoint inefficient queries, enabling database administrators and developers to optimize performance, reduce latency, and improve overall application responsiveness.

By leveraging query execution logs, historical performance data, and real-time monitoring, this pattern allows for proactive detection of slow queries—those exceeding thresholds like execution time, I/O operations, or resource consumption. The goal is to isolate bottlenecks and apply optimizations without disrupting production workloads.

---

## **Schema Reference**

The following tables outline the core components required for implementing **Slow Query Detection**.

### **1. Schema for Query Execution Logs**
Stores historical query performance data.

| **Field**               | **Data Type** | **Description**                                                                 |
|-------------------------|---------------|---------------------------------------------------------------------------------|
| `query_id`              | VARCHAR(64)   | Unique identifier for a query execution.                                       |
| `database_name`         | VARCHAR(128)  | Name of the database where the query executed.                                 |
| `schema_name`           | VARCHAR(128)  | Schema (optional, if applicable).                                             |
| `query_text`            | TEXT          | The actual SQL query (sanitized or anonymized if sensitive).                   |
| `execution_time_ms`     | INT           | Total time taken for the query to execute in milliseconds.                     |
| `rows_examined`         | INT           | Number of rows scanned by the query (filtering helps identify inefficient scans). |
| `rows_returned`         | INT           | Number of rows returned by the query.                                          |
| `start_time`            | TIMESTAMP     | Timestamp when the query began execution.                                      |
| `end_time`              | TIMESTAMP     | Timestamp when the query completed.                                           |
| `user`                  | VARCHAR(64)   | Username or client application executing the query.                            |
| `client_ip`             | VARCHAR(64)   | IP address of the client issuing the query.                                    |
| `database_version`      | VARCHAR(64)   | Version of the database system (e.g., MySQL 8.0, PostgreSQL 15).                |

---

### **2. Schema for Slow Query Thresholds**
Defines performance thresholds to classify queries.

| **Field**               | **Data Type** | **Description**                                                                 |
|-------------------------|---------------|---------------------------------------------------------------------------------|
| `threshold_id`          | INT (PK)      | Auto-incremented identifier for the threshold rule.                            |
| `database_name`         | VARCHAR(128)  | Database name the threshold applies to (use `ALL` for global thresholds).       |
| `max_execution_time_ms` | INT           | Maximum allowed execution time (e.g., `1000` for 1 second).                     |
| `max_rows_examined`     | INT           | Maximum allowed rows to scan (e.g., `1000` to prevent full table scans).        |
| `max_iops`              | INT           | Maximum I/O operations per second (if applicable).                             |
| `enabled`               | BOOLEAN       | Boolean flag to enable/disable the threshold rule.                              |
| `created_at`            | TIMESTAMP     | When the rule was created.                                                    |
| `updated_at`            | TIMESTAMP     | Last modification timestamp.                                                  |

---

### **3. Schema for Alerts**
Tracks detected slow queries and triggers notifications.

| **Field**               | **Data Type** | **Description**                                                                 |
|-------------------------|---------------|---------------------------------------------------------------------------------|
| `alert_id`              | INT (PK)      | Auto-incremented identifier for the alert.                                       |
| `query_id`              | VARCHAR(64)   | Reference to the `query_id` from the execution log.                             |
| `threshold_id`          | INT           | Reference to the violated threshold rule.                                       |
| `severity`              | VARCHAR(32)   | Classification (e.g., `high`, `medium`, `low`).                                  |
| `detection_time`        | TIMESTAMP     | When the alert was generated.                                                   |
| `is_resolved`           | BOOLEAN       | Whether the issue has been addressed.                                           |
| `resolved_at`           | TIMESTAMP     | Timestamp if resolved.                                                          |
| `notes`                 | TEXT          | Additional context (e.g., "Missing index detected").                             |

---

### **4. Schema for Query Performance Metrics**
Aggregated data for trend analysis.

| **Field**               | **Data Type** | **Description**                                                                 |
|-------------------------|---------------|---------------------------------------------------------------------------------|
| `metric_id`             | INT (PK)      | Auto-incremented identifier.                                                    |
| `database_name`         | VARCHAR(128)  | Database name.                                                                   |
| `query_hash`            | VARCHAR(64)   | Hash of the `query_text` for consistent grouping (e.g., MD5).                  |
| `avg_execution_time_ms` | FLOAT         | Average execution time over a time window (e.g., 24 hours).                     |
| `max_execution_time_ms` | FLOAT         | Peak execution time observed.                                                   |
| `row_count`             | INT           | Total rows examined in the time window.                                         |
| `sample_period`         | VARCHAR(32)   | Time window (e.g., `1h`, `6h`, `24h`).                                           |
| `updated_at`            | TIMESTAMP     | Last time the metric was updated.                                               |

---

## **Query Examples**

### **1. Insert a New Query Execution Log**
```sql
INSERT INTO query_executions (
    query_id,
    database_name,
    schema_name,
    query_text,
    execution_time_ms,
    rows_examined,
    rows_returned,
    start_time,
    end_time,
    user,
    client_ip,
    database_version
)
VALUES (
    'q123abc',
    'ecommerce_db',
    'orders',
    'SELECT * FROM customers WHERE signup_date > "2023-01-01"',
    1500,
    500000,
    120,
    '2023-10-15 14:30:45',
    '2023-10-15 14:33:35',
    'app_user',
    '192.168.1.1',
    'PostgreSQL 14'
);
```

### **2. Check for Slow Queries Against Thresholds**
```sql
SELECT
    q.query_id,
    q.database_name,
    q.query_text,
    q.execution_time_ms,
    t.max_execution_time_ms,
    t.max_rows_examined
FROM
    query_executions q
JOIN
    slow_query_thresholds t
    ON q.database_name = t.database_name
WHERE
    q.execution_time_ms > t.max_execution_time_ms
    OR q.rows_examined > t.max_rows_examined
    AND q.start_time > CURRENT_TIMESTAMP - INTERVAL '1 hour';
```

### **3. Generate an Alert for Slow Queries**
```sql
INSERT INTO slow_query_alerts (
    query_id,
    threshold_id,
    severity,
    detection_time,
    is_resolved
)
SELECT
    q.query_id,
    t.threshold_id,
    CASE
        WHEN q.execution_time_ms > 2000 THEN 'high'
        WHEN q.execution_time_ms > 1000 THEN 'medium'
        ELSE 'low'
    END,
    CURRENT_TIMESTAMP,
    FALSE
FROM
    query_executions q
JOIN
    slow_query_thresholds t ON q.database_name = t.database_name
WHERE
    q.execution_time_ms > t.max_execution_time_ms;
```

### **4. Compute Aggregated Metrics for Performance Analysis**
```sql
WITH daily_metrics AS (
    SELECT
        query_hash,
        database_name,
        AVG(execution_time_ms) AS avg_execution_time_ms,
        MAX(execution_time_ms) AS max_execution_time_ms,
        SUM(rows_examined) AS total_rows_examined,
        COUNT(*) AS query_count
    FROM
        query_executions
    WHERE
        start_time >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY
        query_hash, database_name
)
SELECT
    database_name,
    query_hash,
    avg_execution_time_ms,
    max_execution_time_ms,
    total_rows_examined,
    query_count,
    -- Flag queries exceeding thresholds
    CASE WHEN avg_execution_time_ms > 500 THEN 'WARNING' ELSE 'OK' END AS performance_status
FROM
    daily_metrics
ORDER BY
    max_execution_time_ms DESC;
```

### **5. Resolve an Alert (Mark as Fixed)**
```sql
UPDATE slow_query_alerts
SET
    is_resolved = TRUE,
    resolved_at = CURRENT_TIMESTAMP,
    notes = 'Added index on "signup_date" column'
WHERE
    alert_id = 42;
```

---

## **Related Patterns**

1. **Query Optimization Guide**
   - Techniques for rewriting queries (e.g., avoiding `SELECT *`, using `EXPLAIN ANALYZE`, partitioning large tables).
   - *Example:* [PostgreSQL Query Optimization Best Practices](https://www.postgresql.org/docs/current/queries-planning.html).

2. **Database Indexing Strategy**
   - Designing indexes to accelerate common query patterns (B-tree, hash, GiST).
   - *Example:* [MySQL Indexing for Performance](https://dev.mysql.com/doc/refman/8.0/en/mysql-indexes.html).

3. **Real-Time Monitoring Dashboard**
   - Visualizing slow query trends with tools like Grafana, Prometheus, or cloud-native solutions (AWS RDS Performance Insights).
   - *Example:* [Grafana Slow Query Dashboard Template](https://grafana.com/grafana/dashboards/).

4. **Load Testing for Query Scalability**
   - Simulating high traffic to identify query bottlenecks under stress (using tools like JMeter or Locust).
   - *Example:* [Locust Load Testing Framework](https://locust.io/).

5. **Automated Query Review**
   - Integrating static analysis tools (e.g., `pgAudit` for PostgreSQL) to flag inefficient queries during CI/CD.
   - *Example:* [pgAudit Documentation](https://www.pgaudit.org/).

---

## **Implementation Notes**
- **Data Privacy:** Sanitize or hash sensitive query text in logs (e.g., `MD5(query_text)`).
- **Sampling:** For high-volume databases, sample query logs instead of logging every execution.
- **Threshold Tuning:** Start with conservative thresholds (e.g., `max_execution_time_ms = 500ms`) and adjust based on workload.
- **Integration:** Connect to existing monitoring systems (e.g., ELK Stack, Datadog) via APIs or log shipping.