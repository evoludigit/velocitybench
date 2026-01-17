# **[Pattern] Query Performance Monitoring Reference Guide**

---

## **Overview**
The **Query Performance Monitoring** pattern tracks execution metrics for database queries to identify inefficiencies, bottlenecks, or degraded performance. By capturing metrics like execution time, resource usage (CPU, I/O, memory), and query frequency, teams can optimize queries, refine database schemas, and ensure scalable system performance. This pattern is essential for databases (SQL/NoSQL) and application layers where slow queries impact end-user experience. Use this pattern to:
- Detect and resolve performance regressions early.
- Prioritize optimization efforts on high-impact queries.
- Monitor baseline performance trends over time.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                 | **Purpose**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Query Execution Time** | Latency from query submission to result delivery (wall-clock time).           | Identifies slow queries for tuning.                                         |
| **CPU Usage**          | Percentage of CPU time spent processing the query.                            | Helps diagnose CPU-bound query bottlenecks.                                |
| **I/O Latency**        | Time spent waiting for disk/network I/O (e.g., table scans, joins).          | Highlights inefficient scan operations or missing indexes.                  |
| **Query Frequency**    | Number of times a query is executed in a given period.                         | Flags overused queries or anomalies (e.g., sudden spikes).                   |
| **Memory Usage**       | Peak memory consumed during query execution (e.g., temporary tables, sorts).  | Detects memory-heavy operations (e.g., full-table sorts).                     |
| **Query Plan**         | Execution plan parsed from query optimization logs.                           | Reveals suboptimal strategies (e.g., hash joins vs. merge joins).           |
| **Baseline Thresholds** | Predefined metrics (e.g., "95th percentile execution time > 500ms").          | Automates alerts for performance degradation.                              |
| **Sampling vs. Full Logging** | Capturing metrics for a subset (sampling) or all queries.               | Balances overhead and coverage (sampling reduces DB load).                   |

---

## **Implementation Details**

### **1. Tracking Metrics**
Capture metrics at **query submission** and **completion** via:
- **Database Extensions**:
  - **PostgreSQL**: [`pg_stat_statements`](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-STATS-PG-STAT-STATEMENTS) (extension).
  - **MySQL**: `performance_schema` + `slow_query_log`.
  - **SQL Server**: [Query Store](https://learn.microsoft.com/en-us/sql/relational-databases/performance/query-store) (Enterprise) or [sp_who2](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-who2-transact-sql).
  - **NoSQL**: Use built-in monitors (e.g., MongoDB’s `db.currentOp()`) or middleware (e.g., Elasticsearch’s `slowlog`).
- **Application Layer**:
  - Instrument queries with custom timing (e.g., `START_TIME = gettime()` before query execution).
  - Use APM tools (e.g., New Relic, Datadog) to correlate application latency with DB queries.

**Example Metrics Schema** (see [Schema Reference](#schema-reference) below).

---

### **2. Logging and Storage**
Store metrics in:
- **Time-Series Databases**: Prometheus, InfluxDB (for temporal analysis).
- **Relational Databases**: Aggregate metrics in tables for ad-hoc queries.
- **Data Warehouses**: Load metrics into BigQuery/Snowflake for historical trends.
- **Log Files**: Raw logs (e.g., JSON) for debugging (e.g., ELK Stack).

**Retention Policy**:
- **Short-term (1–7 days)**: Raw query logs (high cardinality).
- **Long-term (months)**: Aggregated metrics (daily/weekly snapshots).

---
### **3. Alerting**
Trigger alerts when metrics exceed thresholds (e.g., via Prometheus Alertmanager or Slack webhooks):
```yaml
# Example Prometheus alert rule
- alert: HighQueryLatency
  expr: query_duration_seconds > 1000  # 1 second threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Query {{ $labels.query }} exceeded 1s latency"
```

---
### **4. Query Plan Analysis**
- **Parse Execution Plans**: Use tools like:
  - **PostgreSQL**: `EXPLAIN ANALYZE`.
  - **MySQL**: `EXPLAIN FORMAT=JSON`.
  - **SQL Server**: `SET SHOWPLAN_TEXT ON`.
- **Identify Patterns**:
  - Full table scans (`Seq Scan` in PostgreSQL).
  - Inefficient joins (e.g., nested loops vs. hash joins).
  - Missing indexes (high `Seq Scan` cost).

---
### **5. Sampling Strategies**
To reduce overhead:
- **Cost-Based Sampling**: Log queries above a CPU-time threshold (e.g., >100ms).
- **Frequency-Based**: Sample top-*N* slowest queries.
- **Application-Based**: Log queries tagged as "critical" (e.g., `is_payments_query: true`).

---
## **Schema Reference**
Use this schema to store query performance metrics in a relational database (e.g., PostgreSQL).

| **Column**            | **Type**          | **Description**                                                                 | **Example Values**                          |
|------------------------|-------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `query_id`            | UUID (PK)         | Unique identifier for the query instance.                                        | `550e8400-e29b-41d4-a716-446655440000`     |
| `user_id`             | VARCHAR           | Application/user context (for tracing).                                           | `app_123`                                   |
| `query_text`          | TEXT              | Exact query string (sanitized for sensitive data).                              | `SELECT * FROM users WHERE age > 30`         |
| `execution_time_ms`    | INTEGER           | Wall-clock time in milliseconds.                                                 | `850`                                       |
| `cpu_time_ms`         | INTEGER           | CPU time spent (user + system).                                                   | `500`                                       |
| `io_time_ms`          | INTEGER           | Time spent on I/O operations.                                                     | `300`                                       |
| `memory_usage_mb`     | DECIMAL(10,2)     | Peak memory usage in MB.                                                          | `12.50`                                     |
| `rows_examined`       | BIGINT            | Number of rows scanned.                                                           | `100000`                                    |
| `rows_returned`       | BIGINT            | Number of rows returned.                                                          | `100`                                       |
| `start_time`          | TIMESTAMP         | When the query started.                                                           | `2023-10-01 14:30:00.123`                  |
| `duration_msec`       | INTEGER           | Alias for `execution_time_ms` (for consistency).                                 | `850`                                       |
| `query_plan`          | JSONB             | Execution plan (e.g., `Seq Scan` cost breakdown).                                | `{"nested_loop": {"cost": 1000}}`           |
| `database_version`    | VARCHAR           | DB version (e.g., `PostgreSQL 14.5`).                                             | `MySQL 8.0.32`                             |
| `is_sampled`          | BOOLEAN           | `TRUE` if logged via sampling strategy.                                           | `FALSE`                                     |
| `tags`                | JSONB             | Metadata (e.g., `{ "priority": "high", "endpoint": "checkout" }`).               | `{ "service": "orders" }`                   |

---
## **Query Examples**
### **1. Find Slow Queries (Last 7 Days)**
```sql
-- PostgreSQL
SELECT
  AVG(execution_time_ms) as avg_latency,
  query_text,
  COUNT(*) as occurrences
FROM query_monitoring
WHERE start_time >= NOW() - INTERVAL '7 days'
GROUP BY query_text
HAVING AVG(execution_time_ms) > 500 -- >500ms
ORDER BY avg_latency DESC
LIMIT 20;
```

### **2. Top CPU-Intensive Queries**
```sql
-- MySQL (using performance_schema)
SELECT
  event_name,
  COUNT(*) as calls,
  AVG(timer_wait) as avg_wait_ms
FROM performance_schema.events_statements_summary_by_digest
WHERE event_name LIKE 'send_query%'
GROUP BY event_name
ORDER BY avg_wait_ms DESC
LIMIT 10;
```

### **3. Memory Usage Trends (Time Series)**
```sql
-- Aggregate memory usage by hour (for visualization)
SELECT
  DATE_TRUNC('hour', start_time) as hour,
  AVG(memory_usage_mb) as avg_memory_mb,
  COUNT(*) as query_count
FROM query_monitoring
WHERE memory_usage_mb > 10  -- Filter high-memory queries
GROUP BY hour
ORDER BY hour;
```

### **4. Correlate with Application Errors**
```sql
-- Join query logs with application error logs (e.g., error_tracking table)
SELECT
  q.query_text,
  COUNT(q.query_id) as failed_queries,
  e.error_type,
  COUNT(e.id) as error_count
FROM query_monitoring q
JOIN error_tracking e ON q.user_id = e.user_id
WHERE q.start_time BETWEEN '2023-10-01' AND '2023-10-02'
GROUP BY q.query_text, e.error_type
ORDER BY failed_queries DESC;
```

---
## **Optimization Actions**
Use the collected data to:
| **Problem**                          | **Diagnosis**                          | **Solution**                                                                 |
|--------------------------------------|----------------------------------------|------------------------------------------------------------------------------|
| High `execution_time_ms`              | Full table scans (`Seq Scan` cost >50%) | Add indexes, rewrite query (e.g., `WHERE` conditions).                     |
| Spiking `query_frequency`             | Cache missed or missing JOIN hints.     | Implement application caching (Redis) or force query plans.                  |
| `memory_usage_mb` > DB limit         | Sort operations or large temp tables.   | Optimize `ORDER BY`, use `LIMIT`, or partition tables.                     |
| Noisy neighbors (one query dominates)| Unbounded `SELECT *` or inefficient joins. | Restrict columns (e.g., `SELECT id, name`), use covering indexes.         |
| Plan regression (same query, worse time) | Index corruption or DB patch changes. | Rebuild indexes, check for [Query Plan Instability](https://www.brentozar.com/blitz/plan-instability/). |

---

## **Related Patterns**
1. **[Caching Layer Pattern](https://microservices.io/patterns/data/caching-layer.html)**
   - *How it helps*: Reduces query load by serving cached results for frequent queries.
   - *Complement*: Monitor cache hit ratios alongside query performance.

2. **[Connection Pooling Pattern](https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/cache-overview)**
   - *How it helps*: Minimizes connection overhead for high-frequency queries.
   - *Complement*: Track connection pool metrics (e.g., `pool_used`, `pool_available`).

3. **[Schema Design Patterns](https://use-the-index-luke.com/)**
   - *How it helps*: Optimized schemas (e.g., partitioning, denormalization) reduce query costs.
   - *Complement*: Analyze query plans to identify missing indexes or suboptimal joins.

4. **[Distributed Tracing](https://www.jaegertracing.io/)**
   - *How it helps*: Correlate DB queries with application latency traces.
   - *Complement*: Enrich query logs with trace IDs (e.g., `x-trace-id`).

5. **[Rate Limiting Pattern](https://aws.amazon.com/blogs/architecture/rate-limiting-best-practices/)**
   - *How it helps*: Prevents query floods (e.g., DDoS) from overwhelming the DB.
   - *Complement*: Monitor `query_frequency` to detect rate-limit violations.

---
## **Tools and Libraries**
| **Tool**               | **Purpose**                                                                 | **Link**                                      |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **PostgreSQL `pg_stat_statements`** | Track query stats (extension).                                             | [Docs](https://www.postgresql.org/docs/current/monitoring-stats.html)      |
| **Percona PMM**        | MySQL/PostgreSQL monitoring dashboard.                                       | [percona.com](https://www.percona.com/software/database-tools/percona-monitoring-and-management) |
| **New Relic**          | APM with DB query tracing.                                                  | [newrelic.com](https://newrelic.com/products/infrastructure-monitoring)  |
| **SQL Server Query Store** | Historical query performance tracking.                                      | [Microsoft Docs](https://learn.microsoft.com/en-us/sql/relational-databases/performance/query-store) |
| **Grafana + Prometheus** | Visualize query metrics in dashboards.                                      | [grafana.com](https://grafana.com/), [prometheus.io](https://prometheus.io/) |
| **AWS CloudWatch Logs Insights** | Analyze slow queries in AWS RDS.                                            | [AWS Docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/QuerySoftMetrics.html) |
| **Datadog APM**        | End-to-end query performance monitoring.                                     | [datadoghq.com](https://www.datadoghq.com/product/apm/)                   |

---
## **Best Practices**
1. **Start with Sampling**: Log 100% of queries initially, then sample after establishing baselines.
2. **Anonymize Sensitive Data**: Mask PII in `query_text` (e.g., `WHERE user_id = '***'`).
3. **Set Contextual Thresholds**: Define SLOs per query type (e.g., `SELECT` vs. `UPDATE`).
4. **Monitor Overhead**: Ensure metrics collection doesn’t degrade DB performance (test with `EXPLAIN ANALYZE`).
5. **Automate Alerts**: Use tools like Prometheus or Datadog to notify teams proactively.
6. **Document Patterns**: Share common slow queries and fixes in a wiki (e.g., Confluence).
7. **Review Regularly**: Quarterly audits of query performance to catch regressions.

---
## **Example Workflow**
1. **Detect**: Alert triggers for `execution_time_ms > 2s` (threshold).
2. **Diagnose**: Query plan shows a `Seq Scan` on `users` table with 1M rows.
3. **Optimize**: Add index on `(age)` column.
4. **Validate**: Re-run query; latency drops to `150ms`.
5. **Monitor**: Confirm fix via automated dashboard checks.

---
## **Troubleshooting**
| **Issue**                          | **Check**                                                  | **Solution**                                   |
|-------------------------------------|------------------------------------------------------------|------------------------------------------------|
| `execution_time_ms` fluctuates wildly| Check for [Plan Instability](https://brentozar.com/blitz/plan-instability/). | Use `OPTION (OPTIMIZE FOR UNKNOWN)` or force a plan. |
| High `rows_examined` but low `rows_returned` | Inefficient `WHERE` clause or missing filters.           | Add filters or use `EXISTS` instead of `IN`.   |
| Memory errors (`memory_usage_mb` > limit) | Large sorts or temp tables.                              | Use `TOP`/`LIMIT` or partition data.          |
| Slow queries after DB upgrade      | New optimizer behavior.                                    | Compare plans pre/post-upgrade.               |
| Sampling misses critical queries    | Low sampling rate or excluded queries.                     | Increase sampling rate or exclude less critical queries. |

---
## **Further Reading**
- [Brendan Gregg’s Query Performance Analysis](https://www.brentozar.com/blitz/)
- [Use The Index, Luke](https://use-the-index-luke.com/) (SQL query optimization guide)
- [PostgreSQL Performance FAQ](https://wiki.postgresql.org/wiki/SlowQuery)
- [MySQL 8.0 Query Optimization](https://dev.mysql.com/doc/refman/8.0/en/query-optimization.html)