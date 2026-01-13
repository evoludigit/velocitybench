# **Debugging Analytics Schema Conventions & Best Practices: A Troubleshooting Guide**

## **1. Introduction**
A well-structured analytics schema improves query performance, maintainability, and scalability. This guide covers common issues in **table naming conventions (`tf_`/`ta_`), column design, and indexing**—critical for analytics databases (e.g., Snowflake, BigQuery, Redshift, Databricks).

---

## **2. Symptom Checklist**
Before diving into fixes, verify these issues:

### **A. Table Naming & Discovery Problems**
- [ ] **Manual table registration required** – The analytics engine (e.g., dbt, DataOps tools) doesn’t auto-detect fact/measure tables.
  - Example: `users`, `transactions` instead of `tf_users`, `ta_transactions`.
- [ ] **Mix of operational and analytical tables** – OLTP tables (e.g., `user_profile`) stored alongside analytics tables.

### **B. Performance Issues**
- [ ] **Slow queries on large datasets** – Missing optimal indexes (e.g., on `date`, `id` columns).
- [ ] **Inconsistent query speeds** – Some aggregations fast, others hours-long due to unoptimized joins.
- [ ] **High storage costs** – Unnecessary columns (e.g., unpartitioned raw data).

### **C. Schema Organization Problems**
- [ ] **No clear fact/dimension separation** – Business metrics mixed with reference data in the same table.
- [ ] **No partitioning strategy** – Tables scanned in full instead of partitioned by `date` or `customer_id`.
- [ ] **Schema drift** – New tables added without standardization (e.g., `new_metrics_2024`).

### **D. Tooling & Data Pipeline Issues**
- [ ] **ETL pipelines fail** – Missing foreign keys or improper data types.
- [ ] **Dashboards render slowly** – Underlying analytics tables lack clustering keys.

---
## **3. Common Issues & Fixes**

### **A. Table Naming Conventions Not Followed**
**Symptom:** `users` vs. expected `tf_users` (fact table) or `ta_user_dim` (dimension table).

#### **Fix: Enforce Naming Rules**
1. **Fact Tables (`tf_` prefix):**
   - Contain **aggregatable metrics** (e.g., sales, clicks).
   - Example: `tf_events`, `tf_revenue`.
   ```sql
   CREATE TABLE tf_clicks (
     click_id STRING,
     user_id STRING,
     event_time TIMESTAMP,
     device_type STRING
   );
   ```

2. **Dimension Tables (`ta_` prefix):**
   - Contain **descriptive attributes** (e.g., user name, product category).
   - Example: `ta_users`, `ta_products`.
   ```sql
   CREATE TABLE ta_users (
     user_id STRING,
     name STRING,
     signup_date TIMESTAMP,
     -- No aggregations here
   );
   ```

🔹 **Automation Tip:**
- Use **dbt macros** or **pre-commit hooks** to enforce naming.
- Example dbt macro (`templates/catalog_schema.yml`):
  ```yaml
  version: 2
  models:
    - name: "tf_.*"
      tests:
        - not_null: [id_column]  # Ensure fact tables have a primary key
    - name: "ta_.*"
      tests:
        - relationships:
            to: ref("tf_.*")  # Force relationships between dims and facts
  ```

---

### **B. Missing or Poor Indexing**
**Symptom:** Queries like `SELECT * FROM tf_clicks WHERE device_type = 'mobile'` take 30s+.

#### **Fix: Optimize Indexes by Pattern**
| **Use Case**               | **Solution**                                                                 | **Example (Snowflake)**                     |
|----------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Date-based filtering**   | Cluster by `event_time` or column sort order.                              | `CLUSTER BY (event_time)`                  |
| **High-cardinality keys**  | Create secondary indexes (if supported).                                     | `CREATE INDEX idx_user_id ON tf_clicks(user_id)` |
| **Common joins**           | Ensure foreign keys are indexed.                                             | `CREATE INDEX idx_user_fk ON tf_clicks(user_id)` |
| **Filter-heavy aggregations** | Use **materialized views** for common patterns.                            | `CREATE MATERIALIZED VIEW mv_daily_metrics AS SELECT ...` |

🔹 **Debugging Step:**
- Check query plans for `FULL SCAN` instead of index usage.
- **BigQuery/Redshift Tip:** Use `EXPLAIN` to find missing indexes.

---

### **C. Unpartitioned or Poorly Partitioned Tables**
**Symptom:** Daily aggregations scan **1TB** instead of ~1GB per day.

#### **Fix: Partition by Time or High-Cardinality Keys**
| **Database** | **Partitioning Syntax**                          | **Best Practice**                          |
|--------------|--------------------------------------------------|--------------------------------------------|
| **Snowflake** | `CLUSTER BY (date_trunc('day', event_time))`    | Partition by `date` + cluster by `user_id`  |
| **BigQuery**  | `PARTITION BY DATE(event_time)`                  | Expiry for old data: `PARTITION BY ... OPTIONS(max_partitions=365)` |
| **Redshift**  | `DISTSTYLE KEY DISTKEY (user_id)` + Sortkey    | Co-locate filters (`DISTKEY`) and sorts (`SORTKEY`). |

🔹 **Example (BigQuery):**
```sql
CREATE TABLE tf_events (
  event_id STRING,
  event_time TIMESTAMP,
  user_id STRING,
  value FLOAT64
)
PARTITION BY DATE(event_time)
OPTIONS(
  partition_expiration_days=365,  -- Auto-delete old partitions
  max_partitions=365             -- Prevent runaway partitions
);
```

---

### **D. Mixing OLTP and OLAP Tables**
**Symptom:** `SELECT * FROM user_profiles WHERE status = 'active'` joins to a fact table but is slow due to unoptimized joins.

#### **Fix: Separate Operational from Analytical Data**
1. **OLTP Tables (Fast Reads/Writes):**
   - Small, transactional.
   - Example: `user_profiles` (used in app logic).

2. **OLAP Tables (Analytics-Focused):**
   - Dedicated `ta_user_dim` with only needed attributes.
   ```sql
   -- Avoid this:
   CREATE TABLE user_profiles (
     id INT,
     name VARCHAR(100),
     email VARCHAR(255),
     last_order_date TIMESTAMP,  -- Not an OLAP column!
   );

   -- Do this instead:
   CREATE TABLE ta_user_dim (
     user_id INT PRIMARY KEY,
     name VARCHAR(100),
     signup_date TIMESTAMP,  -- Analytical focus
   );
   ```

🔹 **Rule of Thumb:**
- If a table has **>1TB**, it’s likely OLAP. Optimize for reads, not writes.

---

## **4. Debugging Tools & Techniques**
### **A. Query Profiler**
- **Snowflake:** `SHOW QUERY HISTORY` → Check `REASON` (e.g., "Scan").
- **BigQuery:** `EXPLAIN ANALYZE` to see index usage.
- **Redshift:** `EXPLAIN ANALYZE` + `STL_QUERY_METRICS`.

### **B. Schema Analyzer**
- **Snowflake:** `SHOW TABLES LIKE 'tf_%';`
- **BigQuery:** `INFORMATION_SCHEMA.TABLES` filter by `table_type='EXTERNAL_TABLE'`.
- **dbt:** `dbt docs schema` to visualize relationships.

### **C. Storage Optimization Checks**
- **BigQuery:** Run `SELECT * FROM `project.dataset.INFORMATION_SCHEMA.PARTITIONS` WHERE table_name = 'tf_clicks'`.
- **Snowflake:** `SELECT * FROM TABLE_INFO WHERE table_name = 'tf_clicks';` → Check `ROW_COUNT`.

### **D. Automated Testing**
- **dbt Tests:**
  ```sql
  {{ log("Testing tf_clicks for clustering", info=True) }}
  -- Check if table is clustered by date
  ```
- **Pre-commit Hooks:** Use `great_expectations` to validate schema structure.

---

## **5. Prevention Strategies**
### **A. Enforce Conventions via CI/CD**
- **Git Hook:** Run `schema_validator.py` before PR merges.
- **dbt Models:**
  ```yaml
  models:
    tf_.*:
      tests:
        - relationships:
            to: ref("ta_.*")  # Enforce dim-fact links
  ```

### **B. Document the Schema**
- **Markdown Guide:** Example:
  ```
  ## Table Naming Rules
  - **Fact Tables:** `tf_<entity>` (e.g., `tf_orders`)
  - **Dimension Tables:** `ta_<entity>` (e.g., `ta_products`)
  - **Excluded:** OLTP tables (`user_profiles`), staging tables (`st_raw_events`).
  ```

### **C. Adopt a Schema Review Process**
- **Weekly Schema Health Check:**
  ```sql
  -- Find unpartitioned tables
  SELECT table_name
  FROM information_schema.tables
  WHERE table_schema = 'analytics'
    AND table_name NOT LIKE 'tf_%'
    AND table_name NOT LIKE 'ta_%';
  ```

### **D. Use Templating for Common Patterns**
- **dbt Snippets:**
  ```jinja
  {{ config(materialized='table', cluster_by=['event_time']) }}

  SELECT
    {{ ref('ta_users') }}.user_id,
    {{ ref('st_events') }}.*  -- Staging table
  FROM {{ ref('st_events') }}
  ```

---

## **6. Summary of Key Fixes**
| **Issue**                     | **Quick Fix**                                      | **Long-Term Solution**               |
|-------------------------------|----------------------------------------------------|--------------------------------------|
| Undetected fact tables        | Use `tf_` prefix + dbt metadata                   | Enforce via CI/CD                     |
| Slow aggregations             | Add `CLUSTER BY` or materialized views             | Partition by time                     |
| Mixed OLTP/OLAP tables        | Split into `ta_`/`tf_`                              | Document separation rules             |
| High storage costs           | Delete old partitions, archive raw data           | Set retention policies                |

---
## **7. Final Checklist for Healthy Schema**
✅ All fact tables (`tf_*`) have a `CLUSTER BY` or `DISTKEY`.
✅ Dimension tables (`ta_*`) only contain descriptive attributes.
✅ Partitions expire automatically (e.g., 365 days).
✅ Queries use indexes (verify with `EXPLAIN`).
✅ No OLTP tables in the analytics layer.

---
**Next Steps:**
1. Audit your current schema with `SHOW TABLES`.
2. Fix the worst offenders (e.g., missing partitions).
3. Automate checks with dbt or pre-commit hooks.

By following this guide, you’ll reduce debugging time from hours to minutes and ensure scalable analytics.