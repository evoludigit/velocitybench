# **[Pattern] Reference Guide: Databases Monitoring**

---

## **Overview**
Database monitoring is a systematic approach to tracking, analyzing, and optimizing database performance, availability, and integrity. This pattern ensures proactive detection of issues (e.g., slow queries, high latency, or hardware failures) by collecting metrics, logs, and alerts. It integrates with **database management systems (DBMS)** like PostgreSQL, MySQL, MongoDB, or Oracle, alongside infrastructure monitoring tools (e.g., Prometheus, Datadog, or AWS CloudWatch). Key components include **metric collection** (CPU, memory, query latency), **log aggregation** (errors, deadlocks), and **alerting** (SLO breaches). This guide outlines implementation best practices, schema requirements, and query examples for scalable database monitoring.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Metrics**               | Quantitative data (e.g., query execution time, disk I/O, connection count).                        |
| **Logs**                  | Qualitative records (e.g., errors, slow queries, replication lag).                                  |
| **Alerts**                | Triggers for anomalies (e.g., "CPU usage > 90% for 5 mins").                                     |
| ** Baselines**             | Historical thresholds (e.g., average query latency) for anomaly detection.                        |
| **Data Retention Policy** | Rules for log/metric storage duration (e.g., 30 days for metrics, 7 days for logs).                 |
| **SLOs (Service Level Objectives)** | Targets like "99.9% query response time < 1s". Used to define alerts.                              |

---

## **Schema Reference**
Monitoring data is structured into **tables** for scalability. Below is a normalized schema for a relational database (adaptable to NoSQL via similar collections).

| **Table**          | **Columns**                                                                                     | **Description**                                                                                     |
|--------------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **`metrics`**      | `metric_id` (UUID), `database_id` (FK), `timestamp` (datetime), `metric_type` (enum: CPU, RAM, Disk), `value` (float), `unit` (e.g., "%", "ms"), `tags` (JSON) | Stores time-series numeric data. `tags` include `query_id`, `shard_id`, etc.                     |
| **`logs`**         | `log_id` (UUID), `database_id` (FK), `timestamp` (datetime), `log_level` (enum: ERROR, WARN, INFO), `message` (text), `context` (JSON) | Aggregates raw logs (e.g., `{ "query": "SELECT * FROM users", "duration": 2000 }`).          |
| **`alerts`**       | `alert_id` (UUID), `metric_id` (FK), `trigger_time` (datetime), `resolved_time` (datetime), `severity` (enum: CRITICAL, WARNING), `rule_id` (FK), `notes` (text) | Tracks alert lifecycle (e.g., "PostgreSQL connection pool exhausted").                           |
| **`rules`**        | `rule_id` (UUID), `rule_name` (string), `metric_type` (string), `threshold` (float), `operator` (enum: GT, LT), `window_minutes` (int), `slo_id` (FK) | Defines alerting conditions (e.g., `SELECT * FROM metrics WHERE value > threshold AND metric_type = 'CPU'`. |
| **`databases`**    | `database_id` (UUID), `name` (string), `type` (enum: PostgreSQL, MySQL), `host` (string), `port` (int), `user` (string) | Metadata for tracked databases (e.g., `{"type": "PostgreSQL", "host": "db.example.com"}`).     |
| **`queries`**      | `query_id` (UUID), `database_id` (FK), `sql` (text), `first_seen` (datetime), `execution_count` (int) | Catalogs slow/abnormal queries for analysis.                                                       |

---

## **Query Examples**
### **1. Fetch CPU Metrics for a Database**
Query to retrieve CPU usage metrics for a specific database over the last hour:
```sql
SELECT
    timestamp,
    value,
    tags->>'query_id' AS query_id
FROM metrics
WHERE database_id = 'db-123'
  AND metric_type = 'CPU'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```
**Output:**
| `timestamp`       | `value` | `query_id` |
|-------------------|---------|------------|
| 2024-05-20 14:30 | 85.2    | NULL       |

---

### **2. Find Slow Queries (Top 5 by Execution Time)**
Identify queries exceeding 1s latency in logs:
```sql
SELECT
    context->>'query' AS slow_query,
    COUNT(*) AS occurrences
FROM logs
WHERE log_level = 'WARN'
  AND context->>'duration'::int > 1000
GROUP BY context->>'query'
ORDER BY occurrences DESC
LIMIT 5;
```
**Output:**
| `slow_query`                     | `occurrences` |
|----------------------------------|---------------|
| `SELECT * FROM orders WHERE user_id = ?` | 142        |

---

### **3. Alert for CPU Spikes**
Trigger an alert if CPU exceeds 90% for 5 consecutive minutes:
```sql
-- Pseudocode (implemented in monitoring tool like Prometheus)
alert HighCPUUtilization
  IF sum(rate(cpu_usage[5m])) by (database_id) > 90
    FOR 5m
  ANNOTATIONS {
    summary = "{{$labels.database_id}} CPU usage spike",
    description = "CPU exceeded 90% for 5 minutes."
  }
```

---

### **4. Database Connection Pool Exhaustion**
Check for failed connection pool attempts:
```sql
SELECT COUNT(*) AS failed_connections
FROM logs
WHERE database_id = 'db-123'
  AND log_level = 'ERROR'
  AND message LIKE '%connection pool exhausted%'
  AND timestamp > NOW() - INTERVAL '15 minutes';
```
**Output:**
| `failed_connections` |
|---------------------|
| 42                  |

---

### **5. Replication Lag (Replica Vitals)**
Monitor replication lag in a master-slave setup:
```sql
-- Example for PostgreSQL (via pg_stat_replication)
SELECT
    slave_name,
    lag_byte as "lag_bytes",
    EXTRACT(EPOCH FROM (now() - replication_lag)) as "lag_seconds"
FROM replication_status;
```
**Output:**
| `slave_name` | `lag_bytes` | `lag_seconds` |
|--------------|-------------|---------------|
| replica1     | 5242880     | 30            |

---

## **Implementation Details**
### **1. Metric Collection**
- **Tools:** Prometheus (push/pull), Telegraf, or DBMS-native exporters (e.g., `pg_stat_statements` for PostgreSQL).
- **Sampling:** Adjust frequency (e.g., 1s for CPU, 5m for storage).
- **Tagging:** Include `database_id`, `query_id`, `shard_id` for granular analysis.

### **2. Log Aggregation**
- **Tools:** ELK Stack (Elasticsearch, Logstash, Kibana), Loki, or OpenSearch.
- **Retention:** Compress old logs (e.g., keep 7 days raw, 30 days aggregated).
- **Parsing:** Use structured logging (e.g., JSON) for queries like:
  ```json
  {"level":"WARN","query":"SELECT * FROM users","duration_ms":1500,"timestamp":"2024-05-20T14:30:00Z"}
  ```

### **3. Alerting Rules**
- **SLOs:** Define thresholds per database tier (e.g., prod: 99.9% uptime, staging: 95%).
- **Example Rule (PromQL):**
  ```
  alert: HighQueryLatency
    expr: histogram_quantile(0.95, rate(query_duration_bucket[5m])) > 500
    for: 10m
    labels:
      severity: warning
  ```
- **Avoid Alert Fatigue:** Use adaptive thresholds (e.g., `rate(metric[5m]) > p99 + 2*stddev`).

### **4. Data Retention**
- **Metrics:** 1 month (compressed), 1 year (aggregated).
- **Logs:** 7 days raw, 30 days aggregated (e.g., daily summaries).

### **5. Integration with DBMS**
| **Database**  | **Native Monitoring Tools**                          | **Integration Notes**                                                                 |
|---------------|------------------------------------------------------|---------------------------------------------------------------------------------------|
| PostgreSQL    | `pg_stat_statements`, `pg_badrune`, `pg_monitor`       | Enable `track_activity_query_size` in `postgresql.conf`.                              |
| MySQL         | `performance_schema`, `slow_query_log`              | Set `long_query_time = 1` to log slow queries (>1s).                                   |
| MongoDB       | `mongostat`, `db.currentOp()`                       | Use `profile: 1` for slow query profiling (sparingly).                                 |
| Oracle        | AWR, ASH, `v$session`                               | Schedule AWR snapshots hourly for trend analysis.                                       |

---

## **Query Examples for Common Scenarios**
| **Scenario**                     | **Query**                                                                                     | **Purpose**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Database Uptime**              | `SELECT uptime_seconds FROM system_metrics WHERE database_id = 'db-123'`                     | Monitor availability (e.g., `uptime_seconds / (60*60*24) > 30` = 30+ days uptime).           |
| **Disk I/O Latency**             | `SELECT p99_latency FROM disk_io_metrics WHERE database_id = 'db-123' AND metric_type = 'IO'` | Detect storage bottlenecks (e.g., `p99_latency > 10ms`).                                      |
| **Top Resource-Consuming Queries** | `SELECT query_plan, total_time FROM query_profiles ORDER BY total_time DESC LIMIT 10`        | Identify inefficient SQL (use `EXPLAIN ANALYZE` for plans).                                   |
| **Connection Leaks**             | `SELECT COUNT(*) FROM active_connections WHERE state = 'idle'`                              | Detect idle connections > threshold (e.g., 5000).                                              |
| **Replication Health**           | `SELECT status, lag_seconds FROM replication_metrics`                                     | Ensure replica syncs within SLO (e.g., `lag_seconds < 60`).                                    |

---

## **Related Patterns**
1. **[Auto-Scaling Databases](auto-scaling-databases.md)**
   - *Use Case:* Scale databases dynamically based on CPU/memory metrics from this pattern.
   - *Integration:* Trigger scaling when `metrics.value > threshold` in the `metrics` table.

2. **[Database Backups Monitoring](database-backups.md)**
   - *Use Case:* Track backup success/failure using logs from the `logs` table.
   - *Query:*
     ```sql
     SELECT COUNT(*) AS failed_backups
     FROM logs
     WHERE database_id = 'db-123'
       AND log_level = 'ERROR'
       AND message LIKE '%backup failed%';
     ```

3. **[Query Optimization](query-optimization.md)**
   - *Use Case:* Use slow query logs (`logs` table) to refactor `query` fields.
   - *Tool:* Integrate with `pg_stat_statements` or MySQL’s `slow_query_log`.

4. **[Chaos Engineering for Databases](chaos-engineering.md)**
   - *Use Case:* Inject failures (e.g., kill a replica) and monitor recovery via `alerts` table.
   - *Example:*
     ```sql
     -- Simulate failure, then check alerts
     DELETE FROM databases WHERE database_id = 'replica-1';
     SELECT * FROM alerts WHERE database_id = 'replica-1' ORDER BY trigger_time DESC LIMIT 5;
     ```

5. **[Multi-Region Database Replication](multi-region-replication.md)**
   - *Use Case:* Monitor replication lag across regions using `replication_status` metrics.

---

## **Best Practices**
1. **Start Small:** Monitor critical databases first (e.g., prod).
2. **Reduce Noise:** Use adaptive thresholds and SLOs to minimize false alerts.
3. **Automate Remediation:** Tie alerts to auto-scaling or failover (e.g., "If CPU > 90%, scale out").
4. **Document Queries:** Maintain a `queries` table to track performance regressions.
5. **Test Alerts:** Simulate failures (e.g., kill a DB process) to validate alerting.

---
**Further Reading:**
- [Prometheus Database Monitoring](https://prometheus.io/docs/practices/monitoring/database/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/using-pgadmin-4.html)
- [SRE Book: Observability](https://sre.google/sre-book/monitoring-distributed-systems/)