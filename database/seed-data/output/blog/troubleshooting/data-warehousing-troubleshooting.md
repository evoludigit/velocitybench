# **Debugging Data Warehouse Architecture: A Troubleshooting Guide**

Data warehouses (DWHs) are critical for analytical workloads, but they often face performance bottlenecks, scalability issues, and data consistency problems. This guide provides a structured approach to diagnosing and resolving common issues in **Data Warehouse Architecture**, focusing on efficiency, scalability, and correctness.

---

## **1. Symptom Checklist**
Before diving into fixes, identify symptoms to narrow down the problem:

| **Category**          | **Symptoms** |
|-----------------------|-------------|
| **Performance Issues** | Slow queries (minutes/hours instead of seconds) |
|                       | High query execution time despite indexing |
|                       | Frequent timeouts (`OOM`, `Max Worker Timeout`) |
|                       | Excessive disk I/O or CPU usage |
| **Scalability Problems** | Queries degrade as data grows (linear vs. logarithmic growth) |
|                       | Storage costs spiraling due to inefficient schemas |
|                       | Partitioning not improving performance |
| **Data Consistency**  | Incorrect aggregates (e.g., `COUNT(*)` vs. `SUM(1)` mismatches) |
|                       | Stale data in reports due to slow ETL |
|                       | Duplicate or missing records |
| **Schema & Design**   | High cardinality leading to poor joins |
|                       | Excessive small tables causing metadata bloat |
|                       | Unoptimized data types (e.g., `TEXT` instead of `VARCHAR(255)`) |
| **ETL & Ingestion**   | Failed batch loads or streaming delays |
|                       | Data skew in distributors (e.g., one node gets 90% of traffic) |
| **Resource Constraints** | Storage limits reached unexpectedly |
|                       | Query queues backing up due to resource starvation |

---

## **2. Common Issues & Fixes (with Code Examples)**
### **A. Slow Query Performance**
#### **Symptom:**
- Queries take longer than expected (e.g., 5 minutes vs. 5 seconds).
- `EXPLAIN ANALYZE` shows full scans or inefficient joins.

#### **Root Causes & Fixes**
1. **Lack of Proper Indexing**
   - **Fix:** Add composite indexes on frequently filtered columns.
   ```sql
   -- Example: Optimize a fact table with slow filters
   CREATE INDEX idx_fact_order_date_customer ON fact_sales(date, customer_id);
   ```

2. **Inefficient Joins (Cartesian Products)**
   - **Fix:** Ensure join keys match in cardinality (avoid joining big tables).
   ```sql
   -- Use a smaller dimension table instead of joining to two large tables
   SELECT f.*, d.dim_name  -- Instead of: SELECT f.*, c.*, p.*
   FROM fact_sales f
   JOIN dim_customers d ON f.customer_id = d.customer_id;
   ```

3. **Large Result Sets**
   - **Fix:** Use pagination (`LIMIT/OFFSET`) or approximate queries (e.g., `APPROX_COUNT_DISTINCT` in BigQuery).
   ```sql
   -- Paginate large result sets
   SELECT * FROM transactions LIMIT 10000 OFFSET 0;
   ```

4. **Missing Partitioning**
   - **Fix:** Partition by time or high-cardinality columns.
   ```sql
   -- Time-based partitioning in Snowflake
   CREATE TABLE optimized_sales (
     sale_id INT,
     sale_date DATE
   ) PARTITION BY RANGE(sale_date);
   ```

---

### **B. Data Skew & Hot Partitions**
#### **Symptom:**
- Some nodes handle 90% of the load, leading to bottlenecks.
- Skewed aggregations (e.g., `SUM()` on a skewed key).

#### **Fixes**
1. **Salting (Key Augmentation)**
   ```sql
   -- Distribute skewed keys evenly
   SELECT
     (customer_id * 100) % 100 AS salted_customer_id,
     SUM(amount)
   FROM transactions
   GROUP BY salted_customer_id;
   ```

2. **Dynamic Partition Pruning**
   - Ensure predicates filter partitions early.
   ```sql
   -- Query only needed partitions (e.g., last 30 days)
   SELECT * FROM sales PARTITION (DATE_TRUNC('day', sale_date) >= CURRENT_DATE - INTERVAL '30 days');
   ```

---

### **C. Incremental ETL Failures**
#### **Symptom:**
- Batch loads fail due to duplicates or schema drift.
- Streaming pipelines delay or lose data.

#### **Fixes**
1. **Checksum Validation**
   ```python
   # Validate ingested data against a checksum in Python
   def validate_chunk(chunk):
       expected_checksum = compute_checksum(chunk)
       if expected_checksum != stored_checksum:
           raise ValueError("Data corruption detected")
   ```

2. **Idempotent Writes**
   - Use merge operations (e.g., `INSERT ... ON CONFLICT` in PostgreSQL).
   ```sql
   -- Upsert in PostgreSQL
   INSERT INTO users (id, name)
   VALUES (1, 'Alice')
   ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
   ```

---

### **D. Storage Overrun**
#### **Symptom:**
- Unexpected storage costs despite compression.
- Tables grow larger than expected (e.g., JSON/varchars expanding).

#### **Fixes**
1. **Columnar Formats (Parquet/ORC)**
   ```sql
   -- Load data in Parquet for compression
   CREATE TABLE sales_optimized STORED AS PARQUET;
   ```

2. **Archive Old Data**
   ```sql
   -- Move cold data to a cheaper storage tier
   INSERT INTO cold_sales SELECT * FROM sales WHERE sale_date < '2020-01-01';
   ```

---

## **3. Debugging Tools & Techniques**
| **Tool/Technique**       | **Use Case** |
|--------------------------|-------------|
| **EXPLAIN ANALYZE**      | Inspect query execution plans (identify full scans, sorting). |
| **Query Profiler**       | Track slow queries (e.g., Snowflake Query History, Databricks Metrics). |
| **Distribution Analysis** | Check skew in distributed systems (e.g., `DESCRIBE TABLE` in Spark). |
| **Logging & Monitoring** | Set up alerts for ETL failures (e.g., Airflow, Datadog). |
| **Data Sampling**        | Validate data quality without full scans (e.g., `TABLESAMPLE`). |
| **Load Testing**         | Simulate peak traffic (e.g., k6, Locust). |

**Example Debugging Workflow:**
1. **Identify the slow query** → Use `EXPLAIN ANALYZE` to find bottlenecks.
2. **Check partitions** → Ensure data is evenly distributed.
3. **Review logs** → Look for ETL failures or timeouts.

---

## **4. Prevention Strategies**
### **Design Phase**
- **Schema Design:**
  - Star/Snowflake schemas for analytical queries.
  - Avoid normalized schemas (denormalize for performance).
- **Partitioning:**
  - Time-based (daily/weekly) for time-series data.
  - Range hash partitioning for high-cardinality keys.
- **Indexing:**
  - Composite indexes for common filters.
  - Avoid over-indexing (each index costs ~10% query overhead).

### **Operational Phase**
- **Automated Testing:**
  - Run data quality checks (e.g., `dbt tests`, Great Expectations).
- **Monitoring:**
  - Set up alerts for query timeouts, storage growth.
- **Cost Control:**
  - Use storage tiers (e.g., Snowflake’s `COMPACT` vs. `STANDARD`).
  - Set query timeouts to avoid runaway queries.

### **Example: Preventing Skew in Spark**
```python
# Use salting in PySpark
from pyspark.sql.functions import col

df = df.withColumn("salted_key", (col("skewed_key") * 100) % 100)
df.write.partitionBy("salted_key").saveAsTable("optimized_data")
```

---

## **5. Summary Checklist for Triage**
| **Step**               | **Action** |
|------------------------|------------|
| **1. Reproduce**       | Run the problematic query in isolation. |
| **2. Profile**         | Use `EXPLAIN ANALYZE` or profiler tools. |
| **3. Isolate**         | Check for skew, missing indexes, or resource limits. |
| **4. Fix**             | Apply fixes (indexes, partitioning, salting). |
| **5. Validate**        | Test with a subset of data first. |
| **6. Monitor**         | Set up alerts to catch regressions. |

---
### **Final Notes**
- **Start small:** Fix one query at a time.
- **Document:** Keep a change log for schema/modifications.
- **Iterate:** Continuously monitor and optimize.

By following this guide, you can systematically diagnose and resolve data warehouse issues while ensuring scalability and performance.