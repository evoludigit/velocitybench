# **[Pattern] Profiling Migration – Reference Guide**

---

## **Overview**
**Profiling Migration** is a **data migration pattern** that systematically analyzes and evaluates source data before, during, and after migration to ensure accuracy, consistency, and performance. It applies **profiling techniques** (e.g., statistical sampling, schema validation, and data quality checks) to identify discrepancies, risks, and anomalies in source systems. This pattern minimizes migration failures, reduces backfills, and enhances post-migration data reliability.

Key use cases include:
- **Large-scale database refactoring** (e.g., monetization, schema changes)
- **Legacy system modernization**
- **Data warehouse consolidation**
- **Regulatory compliance audits**

Ideal for teams where **data integrity > speed**, requiring rigorous validation before and after migration.

---

## **Schema Reference**
Below are core components of a **Profiling Migration** implementation:

| **Component**               | **Description**                                                                                                                                                                                                 | **Example Tools/Technologies**                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Pre-Migration Profiling**  | Analyzes source data to identify anomalies, duplicates, and compliance risks.                                                                                                                                   | Apache Spark, Great Expectations, Talend Data Quality, SQL-based sampling queries                |
| **Metadata Repository**      | Stores schema definitions, data samples, and validation rules.                                                                                                                                             | Databricks Delta Lake, PostgreSQL metadata tables, Aiven for metadata management                 |
| **Validation Layer**         | Runs checks against business rules (e.g., uniqueness, referential integrity).                                                                                                                               | DbUnit, Apache Kafka Streams (for real-time validation), custom Python scripts                  |
| **Post-Migration Audit**     | Compares source/target data for drift, completeness, and accuracy.                                                                                                                                           | Deltalake Time Travel, Apache Iceberg, custom reconciliation scripts                             |
| **Alerting System**          | Triggers notifications for deviations (e.g., SLA violations, schema shifts).                                                                                                                                   | Grafana, Datadog, PagerDuty, Slack/email alerts                                                  |
| **Rollback Mechanism**       | Enables rapid restoration if validation fails.                                                                                                                                                                | AWS DMS, Google Data Fusion, custom transactional rollback scripts                              |

---

## **Key Implementation Steps**
### **1. Pre-Migration Profiling**
**Purpose:** Understand source data before migration.
**Steps:**
1. **Schema Extraction:**
   - Capture **DDL, constraints, and relationships** from the source (e.g., `INFORMATION_SCHEMA` in SQL databases).
   - Example query (PostgreSQL):
     ```sql
     SELECT table_name, column_name, data_type, is_nullable
     FROM information_schema.columns
     WHERE table_schema = 'public';
     ```
2. **Data Sampling:**
   - Generate **statistical profiles** (e.g., row counts, null ratios, distributions).
   - Example (Python with Pandas):
     ```python
     import pandas as pd
     df = pd.read_sql("SELECT * FROM users LIMIT 10000", engine)
     print(df.describe(), df.isnull().sum())
     ```
3. **Anomaly Detection:**
   - Flag outliers (e.g., unrealistic values in `salary` or `created_at` timestamps).
   - Tools: **Great Expectations**, **Deequ** (for Spark).

### **2. Validation Rules Definition**
Define **tolerance thresholds** for critical fields (e.g., 99% data completeness).
Example rules (YAML for Great Expectations):
```yaml
expectations:
  - assert_column_values_between:
      column: user_age
      min_value: 1
      max_value: 120
  - assert_column_value_distinct_count:
      column: user_id
      min_distinct: 95%  # Allow 5% duplicates
```

### **3. Migration Execution**
- **Incremental vs. Full Load:**
  - For large datasets, use **CDC (Change Data Capture)** tools (e.g., Debezium, AWS DMS).
  - Example CDC pipeline:
    ```
    Source DB → Debezium → Kafka → Target DB (via ETL)
    ```
- **Parallel Processing:**
  - Split workloads by **partition keys** (e.g., by `customer_id` ranges).

### **4. Post-Migration Audit**
**Goal:** Ensure **data fidelity** between source and target.
**Steps:**
1. **Row-Level Comparison:**
   - Use **hash-based reconciliation** (e.g., SHA-256 hashes of critical fields).
   - Example (SQL):
     ```sql
     SELECT COUNT(*) FROM (
       SELECT source_id, HASHBYTES(2, source_column) AS hash
       FROM source_table
     ) AS source
     INTERSECT
     SELECT target_id, HASHBYTES(2, target_column)
     FROM target_table
     ) AS comparison;
     ```
2. **Statistical Validation:**
   - Compare **distributions** (e.g., mean, variance) using **Kolmogorov-Smirnov test**.
3. **Business Rule Checks:**
   - Verify **referential integrity** (e.g., `FOREIGN KEY` constraints).

### **5. Rollback Plan**
- **Atomic Transactions:**
  - Use **ACID-compliant databases** (e.g., PostgreSQL, Oracle) for point-in-time recovery.
- **Backup & Restore:**
  - Schedule **pre-migration backups** (e.g., AWS S3 snapshots, Veeam for VMs).

---

## **Query Examples**
### **1. Sample Data Profiling (SQL)**
**Purpose:** Generate a summary report for a `customers` table.
```sql
-- Basic statistics
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT email) AS unique_emails,
  SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) AS null_emails,
  AVG(order_count) AS avg_orders,
  MIN(created_at) AS oldest_record,
  MAX(created_at) AS newest_record
FROM customers;

-- Distribution of a categorical field
SELECT
  status,
  COUNT(*) AS count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customers), 2) AS percentage
FROM customers
GROUP BY status
ORDER BY count DESC;
```

### **2. Schema Drift Detection (Python)**
**Purpose:** Compare target schema post-migration.
```python
import sqlalchemy as sa
from great_expectations.dataset import PandasDataset

# Load source and target data
source_engine = sa.create_engine("postgresql://user:pass@source_db")
target_engine = sa.create_engine("postgresql://user:pass@target_db")

source_data = PandasDataset(source_engine.execute("SELECT * FROM users LIMIT 1000"))
target_data = PandasDataset(target_engine.execute("SELECT * FROM users LIMIT 1000"))

# Check for missing columns
missing_cols = set(source_data.list_columns()) - set(target_data.list_columns())
print(f"Missing columns: {missing_cols if missing_cols else 'None'}")
```

### **3. Referential Integrity Check (SQL)**
**Purpose:** Verify `orders` references valid `customers`.
```sql
-- Orders with invalid customer_ids (not in customers)
SELECT o.order_id, o.customer_id
FROM orders o
WHERE NOT EXISTS (
  SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id
);
```

---

## **Performance Considerations**
| **Factor**               | **Recommendation**                                                                                                                                 |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| **Sampling Size**        | Use **10%–30% of data** for initial profiling (adjust based on dataset size).                                                        |
| **Validation Overhead**  | Schedule checks **asynchronously** (e.g., Airflow DAGs) to avoid blocking migrations.                            |
| **CDC Tools**            | Prefer **Debezium** for Kafka-based CDC or **AWS DMS** for cloud migrations.                                               |
| **Parallelism**          | Partition workloads by **high-cardinality keys** (e.g., `user_id` ranges).                                        |
| **Storage Costs**        | Use **compression** (e.g., Parquet, ORC) for sampled data.                                                               |

---

## **Related Patterns**
1. **Incremental Migration**
   - Complements Profiling Migration by handling **partial loads** and **CDC**.
   - *When to use:* Large datasets where full stops are impractical.

2. **Canonical Data Model**
   - Ensures **consistent schema** across systems before migration.
   - *Tools:* AWS Glue Schema Registry, Confluent Schema Registry.

3. **Idempotent ETL**
   - Makes migrations **retry-safe** by avoiding duplicate operations.
   - *Example:* Use `MERGE` instead of `INSERT` in SQL.

4. **Data Governance Framework**
   - Provides **policies** for post-migration data stewardship.
   - *Standards:* ISO 38505, GDPR compliance checks.

5. **Blue-Green Deployment (for Databases)**
   - Reduces risk by **cutting over to a validated clone**.
   - *Tools:* PostgreSQL logical replication, Oracle Data Guard.

---
## **Failure Modes & Mitigations**
| **Failure Scenario**               | **Root Cause**                          | **Mitigation**                                                                                     |
|------------------------------------|----------------------------------------|----------------------------------------------------------------------------------------------------|
| Data loss during migration         | Poor backup strategy                   | Use **transaction logs** + **point-in-time recovery**.                                              |
| Schema drift                       | Unhandled nullable columns             | Enforce **strict schema validation** pre- and post-migration.                                     |
| Performance bottlenecks            | Unoptimized sampling queries           | **Pre-aggregate** data where possible; use **partitioned tables**.                                 |
| False negatives in validation      | Insufficient sample size               | Increase sample size to **95%+ confidence** (e.g., 5,000 rows for large tables).                     |
| Compliance violations              | Missing regulatory checks              | Integrate **audit logs** (e.g., AWS CloudTrail) with migration pipelines.                           |

---
## **Tools & Libraries**
| **Category**               | **Tools**                                                                 |
|---------------------------|----------------------------------------------------------------------------|
| **Profiling**             | Great Expectations, Deequ, Talend Data Quality, SQL-based sampling       |
| **ETL/ELT**               | Apache Airflow, dbt, Fivetran, Informatica PowerCenter                     |
| **CDC**                   | Debezium, AWS DMS, Google Data Fusion, Kafka Connect                        |
| **Validation**            | DbUnit, Apache Iceberg, Deltalake Time Travel                              |
| **Observability**         | Prometheus + Grafana, Datadog, New Relic                                   |
| **Metadata Management**  | Apache Atlas, Collibra, AWS Glue Data Catalog                             |

---
## **Best Practices**
1. **Automate Profiling:**
   - Use **CI/CD pipelines** (e.g., GitHub Actions) to run validation scripts on PRs.
2. **Document Assumptions:**
   - Record **known data quality issues** (e.g., "5% of `address` fields are NULL").
3. **Phased Rollout:**
   - Migrate **non-critical tables first** to validate the process.
4. **Stakeholder Alignment:**
   - Involve **data owners** in defining validation rules.
5. **Cost-Benefit Tradeoff:**
   - Balance **accuracy** (e.g., 100% sampling) vs. **speed** (e.g., 1% sampling).

---
## **When to Avoid This Pattern**
- **Small, simple migrations** (e.g., <100K rows) where manual validation suffices.
- **Real-time systems** where **latency** > data accuracy (use **CDC + streaming validation** instead).
- **Legacy systems with no metadata** (profiling becomes unfeasible; consider **manual mapping**).