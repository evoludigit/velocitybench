# **Debugging Data Warehouse Architecture & Best Practices: A Troubleshooting Guide**
*For high-performance analytical query performance at scale*

---

## **1. Introduction**
Data warehouses (DWs) power business intelligence, reporting, and analytics. When poorly optimized, they suffer from slow queries, high storage costs, partitioning failures, and scalability bottlenecks.

This guide helps **backend engineers** diagnose and resolve common issues in data warehouse architectures using **AWS Redshift, Snowflake, BigQuery, or similar tools**.

---

## **2. Symptom Checklist: When Something’s Wrong**
| **Symptom**                          | **Possible Cause**                          | **Impact** |
|--------------------------------------|---------------------------------------------|------------|
| ✅ Analytical queries take >30s      | Poor partitioning, inefficient joins       | Slow insights |
| ✅ Unexpected storage bloat (10x+ growth) | No data lifecycle policy, redundant models | High costs |
| ✅ Frequent query timeouts (OOM, deadlocks) | Unoptimized table scans, large intermediate datasets | Failed analytics |
| ✅ Join performance degrades over time | Partition evaporation, lack of indexing | Broken BI dashboards |
| ✅ ETL pipelines stuck for hours      | DDL constraints, concurrency limits        | Delayed reporting |
| ✅ Cost overruns after data growth    | No cost controls, unbounded table growth    | Budget alerts |

If you see **any of these**, check the sections below.

---

## **3. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Slow Query Performance (Full Table Scans)**
**Symptoms:**
- `EXPLAIN` shows `SeqScan` (full table scans) instead of optimized joins.
- Query durations spike after new data ingestion.

**Root Cause:**
- Lack of proper **partitioning** or **indexing**.
- Large joins without filtering (missing `WHERE` clauses).

**Fixes:**

#### **For Amazon Redshift:**
✔ **Enable Sort Keys & Distkeys**
```sql
-- Example: Optimize for frequent `date` and `user_id` filters
CREATE TABLE fact_sales (
    sale_id BIGINT,
    user_id INT,
    sale_date TIMESTAMP
) DISTSTYLE KEY  -- Distribute by high-cardinality column
DISTKEY (user_id)
SORTKEY (sale_date);

-- Force Redshift to use the sort key:
-- EXPLAIN SELECT * FROM fact_sales WHERE sale_date > '2023-01-01';
```

✔ **Use LATERAL JOINs for Large Datasets**
```sql
-- Instead of:
SELECT t1.*, t2.*
FROM large_table t1, small_table t2
WHERE t1.id = t2.id  -- Inefficient cross join

-- Use LATERAL for better optimization:
SELECT t1.*, t2.*
FROM large_table t1
LATERAL JOIN small_table t2 ON t1.id = t2.id;
```

---

#### **For Snowflake:**
✔ **Enable Cluster Keys**
```sql
CREATE TABLE fact_sales (
    sale_id NUMBER,
    user_id NUMBER,
    sale_date TIMESTAMP
)
CLUSTER BY (user_id, sale_date);
```

✔ **Use Result Caches**
```sql
-- Enable query caching for frequent queries:
ALTER DATABASE CACHE_TABLES = ON;
```

---

#### **For BigQuery:**
✔ **Partitioning & Clustering**
```sql
CREATE TABLE `project.dataset.fact_sales`
PARTITION BY DATE(sale_date)
CLUSTER BY user_id
AS SELECT * FROM raw_sales;
```

---

### **Issue 2: Storage Bloat & High Costs**
**Symptoms:**
- Storage usage grows **unexpectedly** (e.g., 1TB → 10TB in months).
- Cost alerts from cloud provider.

**Root Cause:**
- No **TTL (Time-to-Live)** policies.
- Staging tables retained indefinitely.
- Duplicate data in dimension tables.

**Fixes:**

#### **Amazon Redshift:**
✔ **Set Table Time Integrity (TTL)**
```sql
-- Drop old data older than 30 days:
CREATE TABLE fact_sales (
    sale_id BIGINT,
    sale_date TIMESTAMP,
    -- ...
    CONSTRAINT ttl_sales
        TIMESTAMP (sale_date) EXPIRE CHAIN (30 DAYS)
);
```

✔ **Use Redshift Spectrum for Cold Data**
```sql
-- Offload old data to S3 for cheaper storage:
CREATE EXTERNAL TABLE fact_sales_old
STORED AS PARQUET
LOCATION 's3://bucket/sales_old/';
```

---

#### **Snowflake:**
✔ **Enable Auto-Clustering & Time Travel**
```sql
-- Auto-optimize clusters:
ALTER TABLE fact_sales SET CLUSTERING = ON;

-- Set TTL for staging tables:
ALTER TABLE staging_sales SET TIMESTAMP_LAG = 90;
```

---

### **Issue 3: ETL Pipeline Failures (DDL Constraints)**
**Symptoms:**
- `ETL job stuck at "DDL" step`.
- `Concurrency limit exceeded` errors.

**Root Cause:**
- **Explicit DDL** (e.g., `CREATE TABLE`) during bulk loads.
- **Concurrency throttling** (e.g., Redshift’s `wlm_query_slot_count`).

**Fixes:**

✔ **Use `COPY FROM` Instead of `INSERT` (Redshift)**
```sql
-- BAD: Slow row-by-row inserts
COPY fact_sales FROM 's3://bucket/sales/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftLoadRole';

-- GOOD: Use STV (Sort/Storage Key Validation)
SET enable_stv = on;
```

✔ **Adjust Workload Management (WLM)**
```sql
-- Increase query slots for ETL:
ALTER DATABASE mydb
SET WLM_QUERY_SLOTS TO 50;
```

---

### **Issue 4: Join Performance Degradation Over Time**
**Symptoms:**
- Join queries **slow down after data grows**.
- `EXPLAIN` shows `Sort Merge Join` with high cost.

**Root Cause:**
- **Partition evaporation** (Redshift) – missing data in new slices.
- **No incremental refresh** (Snowflake/BigQuery).

**Fixes:**

#### **Amazon Redshift:**
✔ **Re-distribute Data Evenly**
```sql
-- Check for skew:
SELECT count(*), table_name, diststyle
FROM svv_table_info;

-- Re-distribute if needed:
ALTER TABLE fact_sales RESET DISTSTYLE DISTKEY (user_id);
```

✔ **Use `ANALYZE` After Data Changes**
```sql
-- Force Redshift to recompute stats:
ANALYZE fact_sales;
```

#### **Snowflake:**
✔ **Enable Auto-Optimization**
```sql
-- Enable auto-cluster tuning:
ALTER TABLE fact_sales SET OPTIMIZE_FOR SCAN;
```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Purpose**                                  | **Command/Example** |
|------------------------|---------------------------------------------|---------------------|
| **Redshift `EXPLAIN`** | Analyze query execution plan.              | `EXPLAIN SELECT * FROM sales JOIN users ON ...` |
| **Snowflake `DBMS_LN`** | Check query history & performance.         | `SELECT * FROM TABLE(INFORMATION_SCHEMA.SQL_QUERIES);` |
| **BigQuery `INFORMATION_SCHEMA`** | Track query costs & slowdowns.          | `SELECT * FROM `project.dataset.INFORMATION_SCHEMA.JOBS_BY_PROJECT`;` |
| **AWS CloudWatch**     | Monitor Redshift CPU/Memory usage.         | `GetMetricStatistics (Namespace="AWS/Redshift", MetricName="CPUUtilization")` |
| **Redshift `STL_QUERY`** | Debug stuck queries.                       | `SELECT * FROM stl_query WHERE query IS NOT NULL;` |
| **Snowflake `SNOWSQL`** | Log slow queries.                          | `SET LOG_QUERIES = ON;` |

---

## **5. Prevention Strategies (Proactive Checklist)**
| **Area**               | **Best Practice**                          | **Implementation** |
|------------------------|--------------------------------------------|---------------------|
| **Partitioning**       | Use time-based partitioning (date)        | `PARTITION BY DATE(sale_date)` |
| **Indexing**           | Apply sort/dist keys (Redshift)            | `DISTKEY (user_id), SORTKEY (date)` |
| **Cost Control**       | Enforce TTL policies                      | `CONSTRAINT ttl_expire CHAIN (30 DAYS)` |
| **ETL Optimization**   | Use bulk loads instead of row inserts     | `COPY FROM S3` (not `INSERT INTO`) |
| **Query Monitoring**   | Set up alerts for slow queries            | CloudWatch/Snowflake Alerts |
| **Data Lifecycle**     | Archive cold data to cheaper storage      | Redshift Spectrum / Snowflake Stage |

---

## **6. Final Checklist Before Deployment**
✅ **Test with `EXPLAIN`** – Ensure optimal execution plans.
✅ **Benchmark ETL** – Measure load times under production load.
✅ **Set Cost Alerts** – Avoid unexpected bills.
✅ **Monitor Partition Health** – Check for skew (Redshift `stl_partitions`).
✅ **Automate Maintenance** – Schedule `VACUUM`, `ANALYZE`, or `CLUSTER BY`.

---
### **When to Seek Help**
- If queries remain slow **after optimizations**, check for **underlying schema design issues** (e.g., normalizing too much for analytics).
- If storage costs **keep rising**, review **data retention policies**.

This guide ensures **fast troubleshooting** for data warehouse bottlenecks. 🚀