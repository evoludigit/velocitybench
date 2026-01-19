# **[Pattern] Query Timeout and Resource Limits – Reference Guide**

---

## **1. Overview**
Query execution in data processing systems must balance performance, efficiency, and fairness. The **Query Timeout & Resource Limits** pattern enforces constraints on execution time and resource consumption (CPU, memory, disk I/O) to prevent:
- **Runaway queries** (e.g., infinite loops, inefficient joins).
- **Resource starvation** (other queries being blocked by a single computationally expensive task).
- **System instability** (crashes due to unchecked memory exhaustion).

This pattern is widely used in **SQL databases (PostgreSQL, MySQL), big data tools (Spark, Hive), and cloud databases (BigQuery, Snowflake)**. It applies to both interactive queries and batch jobs. Below, we outline implementation strategies, configuration options, and best practices.

---

## **2. Schema Reference**

| **Category**               | **Field**                     | **Description**                                                                 | **Example Values**                                                                 | **Default (Common Cases)**                     |
|----------------------------|--------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------|
| **Execution Timeout**      | `query_timeout`               | Maximum allowed runtime (in seconds).                                         | `300` (5 minutes), `PT1H` (ISO 8601)                                                 | Varies by system (e.g., Spark: `60s`)         |
|                            | `abort_on_timeout`            | Whether to terminate the query after timeout (boolean).                        | `true`/`false`                                                                     | `true` (default in most systems)              |
| **CPU Limits**             | `max_cpu_time`                | Maximum CPU time allowed (seconds or cores).                                  | `60s`, `1.5c` (1.5 CPU cores)                                                       | N/A (usually inherited from cluster settings) |
|                            | `cpu_shares`                  | Resource fairness allocation (e.g., via cgroups).                            | `1024` (relative weight)                                                              | System-specific (e.g., Docker containers)     |
| **Memory Limits**          | `memory_limit`                | Hard cap on memory usage (bytes or MB/GB).                                   | `8GB`, `8388608000` (8GB in bytes)                                                  | Depends on system (e.g., Spark: `50% of executor mem`) |
| **Disk I/O Limits**        | `max_disk_bytes`              | Maximum temporary disk space per query.                                      | `10GB`, `10737418240` (10GB)                                                        | Typically `2x–4x` RAM (or system-configurable) |
| **Query Parameters**       | `max_concurrent_queries`      | Limits on parallel query execution.                                           | `10`, `unlimited`                                                                   | `unlimited` (unless enforced by cluster)     |
|                            | `query_priority`              | Priority level for query scheduling.                                          | `high`, `low`, `batch`                                                               | `normal` (default)                           |
| **Monitoring Metrics**     | `timeout_warnings`            | Log a warning before timeout (boolean).                                        | `true`/`false`                                                                     | `true` (recommended)                          |
|                            | `resource_usage_logs`         | Enable detailed usage logs for debugging.                                     | `all`, `errors_only`                                                               | `errors_only`                                |

---

## **3. Implementation Details by System**

### **3.1 SQL Databases**
#### **PostgreSQL**
- **Timeout**: Set via `statement_timeout` (in milliseconds) in `postgresql.conf` or per-session:
  ```sql
  SET statement_timeout TO '30s';  -- Session-level
  ```
- **Work Mem**: Temporary memory constraint:
  ```sql
  ALTER SYSTEM SET work_mem = '16MB';
  ```
- **CPU**: No native CPU limits (use `pg_stat_activity` to monitor).

#### **MySQL**
- **Timeout**: Configure `interactive_timeout` and `wait_timeout` in `my.cnf`:
  ```ini
  [mysqld]
  interactive_timeout = 600  -- 10 minutes
  ```
- **Resource Limits**: Use `resource_group` (Enterprise Edition) or `ulimit` on the OS level.

#### **SQL Server**
- **Timeout**: `SET QUERY_TIMEOUT` in T-SQL:
  ```sql
  SET QUERY_TIMEOUT 300;  -- 5 minutes
  ```
- **Memory**: `MAXDOP` (degree of parallelism) and `query_store` for tracking.

---

### **3.2 Big Data & Distributed Systems**
#### **Apache Spark**
- **Timeout**: Set in `SparkSession`:
  ```scala
  sparkconf.set("spark.sql.shuffle.partitions", "200")
    .set("spark.sql.execution.timeout", "60s")
    .set("spark.executor.cores", "2")
    .set("spark.executor.memory", "4g")
  ```
- **Resource Groups**: Use `ResourceGroup` API to allocate shares:
  ```scala
  spark.conf.set("spark.dynamicAllocation.enabled", "true")
    .set("spark.dynamicAllocation.resourceGroup", "high_priority")
  ```

#### **Apache Hive**
- **Timeout**: `hive.exec.timeout` (in seconds):
  ```sql
  SET hive.exec.timeout=1800;  -- 30 minutes
  ```
- **Memory**: `hive.execution.engine.spur` (for Tez/Spark) and `hive.temporary.local.dir`.

#### **Presto/Trino**
- **Timeout**: `query.max-run-time-ms` in `config.properties`:
  ```properties
  query.max-run-time-ms=1800000  -- 30 minutes
  ```
- **Resource Limits**: `memory-per-node` and `task-concurrency-per-node`.

---

### **3.3 Cloud Databases**
#### **Google BigQuery**
- **Timeout**: Implicit (24-hour max for batch jobs; interactive queries timeout after 10 minutes by default).
- **Resource Limits**: Slot commitments via `RESERVATION_ID`.

#### **Snowflake**
- **Query Timeout**: `QUERY_TIMEOUT` session parameter:
  ```sql
  ALTER SESSION SET QUERY_TIMEOUT = '10M';  -- 10 minutes
  ```
- **Resource Monitor**: `RESOURCE_MONITOR` roles to enforce limits.

#### **AWS Athena**
- **Timeout**: `workGroupConfig` in AWS Glue:
  ```json
  {
    "resultConfiguration": {
      "outputLocation": "s3://...",
      "encryptionConfiguration": { ... },
      "workGroup": {
        "queryResultConfiguration": {
          "maxResults": 1000,
          "timeout": 30  -- minutes
        }
      }
    }
  }
  ```

---

## **4. Query Examples**
### **4.1 Enforcing Timeouts in SQL**
```sql
-- PostgreSQL: Set session timeout to 1 minute
SET LOCAL statement_timeout TO '60000';  -- 60,000 ms
SELECT * FROM large_table WHERE slow_condition;

-- Spark: Timeout in Scala
val result = spark.sql("""
  SELECT * FROM big_table
  WHERE complex_join_condition
""").setQueryTimeout(120)  // 2 minutes
```

### **4.2 Dynamic Resource Allocation (Spark)**
```scala
// Allocate resources per job
spark.conf.set("spark.dynamicAllocation.executorAllocationRatio", "0.8")
  .set("spark.executor.memoryOverhead", "1g")

// Query with priority
spark.range(1000000)
  .filter("id > 500000")
  .write
  .format("parquet")
  .mode("overwrite")
  .option("path", "/data/output")
  .saveAsTable("high_priority_table")
```

### **4.3 Monitoring and Alerting (BigQuery)**
```sql
-- Check for long-running queries
SELECT
  query,
  creation_time,
  total_slot_ms,
  EXTRACT(EPOCH_SECOND FROM TIMESTAMP_DIFF(
    CURRENT_TIMESTAMP(), creation_time
  )) AS duration_seconds
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND total_slot_ms > 1000000  -- >1000s
ORDER BY duration_seconds DESC;
```

---

## **5. Best Practices**
1. **Start Conservatively**:
   - Begin with short timeouts (e.g., 5–10 minutes) and increase based on workload.
   - Use `SELECT /*+ MAX_EXECUTION_TIME(300) */ * FROM table` (Oracle) or hints in other DBs.

2. **Log and Alert**:
   - Enable warnings before timeouts (`timeout_warnings=true`).
   - Set up alerts for repeated timeouts (e.g., Prometheus + Alertmanager).

3. **Optimize Queries**:
   - Add indexes, partition tables, or use materialized views to reduce runtime.
   - Avoid `SELECT *`; fetch only necessary columns.

4. **Prioritize Workloads**:
   - Use resource groups (Spark) or query priorities (Snowflake) to allocate shares fairly.
   - Example: Batch jobs get lower priority than interactive queries.

5. **Monitor Resource Usage**:
   - Track metrics like `memory_used`, `cpu_time`, and `shuffle_spill`.
   - Tools: Ganglia, Datadog, or built-in dashboards (e.g., Spark UI).

6. **Handle Failures Gracefully**:
   - Implement retry logic for transient timeouts (e.g., exponential backoff).
   - Store query state (e.g., checkpointing in Spark) to resume after interruptions.

---

## **6. Common Pitfalls & Solutions**
| **Pitfall**                          | **Cause**                          | **Solution**                                                                 |
|--------------------------------------|------------------------------------|------------------------------------------------------------------------------|
| Queries hit timeout before completing | Inefficient joins/aggregations.    | Add indexes, use `EXPLAIN ANALYZE`, or split queries.                        |
| Memory exhaustion                     | Large intermediate results.        | Increase `memory_limit` or use approximate algorithms (e.g., `APPROX_COUNT_DISTINCT`). |
| CPU-bound queries block others       | Long-running serial tasks.         | Parallelize with `REPARTITION` (Spark) or distribute workload.             |
| Timeout settings too restrictive      | Overly pessimistic defaults.      | Test with representative workloads; start with 5–10x the expected runtime.  |

---

## **7. Related Patterns**
1. **Query Optimization** (*Optimize for Speed*)
   - Techniques to reduce execution time (e.g., indexing, query rewriting).

2. **Adaptive Execution**
   - Dynamically adjust execution plans (e.g., Spark’s adaptive query execution).

3. **Query Caching**
   - Cache frequent/expensive queries (e.g., Redis integration in PostgreSQL).

4. **Resource Isolation**
   - Use containers (Docker/Kubernetes) to isolate query workloads.

5. **Cost-Based Optimization**
   - For serverless databases (e.g., BigQuery), monitor slot usage to avoid unexpected charges.

6. **Fallback Mechanisms**
   - Implement circuit breakers for external dependencies in queries.

---
**References**:
- [PostgreSQL Documentation – Statement Timeout](https://www.postgresql.org/docs/current/runtime-config-query.html)
- [Spark SQL Configuration](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-spark-sql.html)
- [BigQuery Job Timeouts](https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/query#resource-representations)