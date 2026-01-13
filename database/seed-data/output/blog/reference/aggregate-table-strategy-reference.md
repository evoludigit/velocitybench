---

# **[Pattern] Aggregate Tables for Pre-Computed Rollups (ta_*) – Reference Guide**

---

## **1. Overview**
Aggregate tables (prefixed with **`ta_`**) store pre-computed rollups of fact (e.g., `facts_*`) and dimension data at predefined time granularities (hourly, daily, monthly). This pattern improves query performance by **100x–1,000x** for analytical queries, trading storage space for speed.

**Use cases:**
- Billion-row fact tables with high cardinality dimensions (e.g., user sessions, transactions).
- Dashboards requiring frequent aggregations (sums, averages, counts) over time periods.
- Useful for time-series data (e.g., metrics, logs) where repeated aggregations are common.

**Key tradeoffs:**
| **Metrics**       | **Fact Tables**       | **Aggregate Tables**      |
|-------------------|-----------------------|----------------------------|
| Query Speed       | Slow (scans billions)  | Fast (scans millions)      |
| Storage Usage     | Low                   | High                       |
| Maintenance       | Simple (inserts only) | Complex (ETL + updates)    |

---

## **2. Schema Reference**
### **Core Components**
#### **Aggregate Tables (`ta_*` Prefix)**
| Field Type       | Example Name       | Description                                                                 | Data Type          | JSONB Flag |
|------------------|--------------------|-----------------------------------------------------------------------------|--------------------|------------|
| **Granularity**  | `time_bucket`      | Time period (e.g., `'2024-01-01'` for daily) or bucket (e.g., `'2024-01'`) | `timestamp` or `text` | ❌        |
| **Measures**     | `total_revenue`    | Pre-computed aggregations (SUM, AVG, COUNT, etc.)                           | `numeric`, `bigint` | ❌        |
| **Dimensions**   | `dimensions`       | Encoded dimensions (e.g., `category`, `region`) as JSONB                   | `jsonb`             | ✅         |
| **Row Count**    | `row_count`        | Number of source rows aggregated (for denormalization checks)               | `bigint`            | ❌        |
| **Meta**         | `updated_at`       | Last update timestamp (for incremental ETL)                                | `timestamp`         | ❌        |

**Example Table Definitions:**
```sql
CREATE TABLE ta_hourly_sales (
    time_bucket timestamp NOT NULL,
    total_revenue numeric,
    units_sold bigint,
    dimensions jsonb NOT NULL,
    row_count bigint,
    updated_at timestamp DEFAULT NOW(),
    PRIMARY KEY (time_bucket)
);

CREATE INDEX idx_ta_hourly_sales_dimensions ON ta_hourly_sales USING GIN (dimensions);
```

---

### **ETL Pipeline (Batch Job)**
| Component          | Purpose                                                                 | Tools/Techniques                          |
|--------------------|-------------------------------------------------------------------------|-------------------------------------------|
| **Source**         | Fact tables (e.g., `facts_sales`)                                       | PostgreSQL, Snowflake, BigQuery           |
| **Processing**     | Compute aggregations (GROUP BY + JSONB encoding)                       | Python (Pandas), SQL `WITH` clauses      |
| **Sink**           | Aggregate tables (`ta_*`)                                               | Direct SQL INSERT/UPDATE                  |
| **Scheduling**     | Run hourly/daily (e.g., Airflow, dbt)                                   | Cron jobs, cloud schedulers               |
| **Incremental**    | Update only new time periods (e.g., last 24 hours)                       | MERGE/UPDATE logic, database triggers     |

**Key SQL Logic (Simplified):**
```sql
-- Generate hourly aggregates from facts_sales
CREATE OR REPLACE VIEW vw_hourly_rollups AS
SELECT
    DATE_TRUNC('hour', event_time) AS time_bucket,
    SUM(revenue) AS total_revenue,
    COUNT(*) AS row_count,
    jsonb_agg(
        jsonb_build_object(
            'product_id', product_id,
            'category', category,
            'region', region
        )
    ) AS dimensions
FROM facts_sales
GROUP BY 1;
```

**Populate Aggregate Table:**
```sql
INSERT INTO ta_hourly_sales (time_bucket, total_revenue, dimensions, row_count)
SELECT * FROM vw_hourly_rollups
ON CONFLICT (time_bucket) DO UPDATE
SET total_revenue = EXCLUDED.total_revenue,
    dimensions = EXCLUDED.dimensions,
    updated_at = NOW();
```

---

### **Query Router (Intelligent Routing)**
Determines whether to query **fact tables** (raw data) or **aggregate tables** (pre-aggregated).

| **Decision Logic**               | **Query Target**       | Example Use Case                          |
|----------------------------------|------------------------|-------------------------------------------|
| Filter on `time_bucket` (e.g., `'2024-01'`) AND dimensions | Aggregate table (`ta_*`) | "Show daily revenue by country for January" |
| Filter on raw timestamp (e.g., `event_time > '2024-01-01'`) | Fact table (`facts_*`) | "Find all events in the last 7 days"       |
| No time filter + high cardinality | Fact table              | "List all unique users"                   |

**Implementation Approaches:**
1. **Application-Level Logic** (Recommended):
   ```python
   def get_query_target(where_clause: str) -> str:
       if "time_bucket" in where_clause and not any(
           t in ["event_time", "DATE_TRUNC"] for t in where_clause.split()
       ):
           return "ta_hourly_sales"
       return "facts_sales"
   ```
2. **Database Views** (PostgreSQL):
   ```sql
   CREATE VIEW vw_sales_query_router AS
   SELECT * FROM facts_sales
   WHERE NOT EXISTS (
       SELECT 1 FROM ta_hourly_sales
       WHERE time_bucket = DATE_TRUNC('hour', event_time)
   );
   ```
3. **Query Time Detection** (Advanced):
   Use `EXPLAIN` or `pg_stat_statements` to auto-detect slow queries and reroute.

---

### **Incremental Updates (Optimization)**
Avoid full table recalculations by updating only new periods.

**Strategies:**
1. **Time-Based Partitioning**:
   - Partition aggregate tables by `time_bucket` (e.g., monthly).
   - Drop old partitions (e.g., `> 3 years`) to save space.

   ```sql
   CREATE TABLE ta_daily_sales (
       time_bucket date NOT NULL,
       -- columns...
       PRIMARY KEY (time_bucket)
   ) PARTITION BY RANGE (time_bucket);
   ```

2. **Conditional Updates**:
   Update only missing or newer periods:
   ```sql
   UPDATE ta_hourly_sales
   SET total_revenue = (SELECT SUM(revenue) FROM facts_sales
                       WHERE DATE_TRUNC('hour', event_time) = ta_hourly_sales.time_bucket)
   WHERE updated_at < NOW() - INTERVAL '24 HOURS';
   ```

3. **Merge Operations**:
   Use `MERGE` (Snowflake, BigQuery) or `ON CONFLICT` (PostgreSQL) to upsert.

---

## **3. Query Examples**
### **Query 1: Pre-Aggregated Analytics (Fast)**
```sql
-- Fetch daily revenue by category (uses ta_daily_sales)
SELECT
    dimensions->>'category' AS category,
    total_revenue,
    SUM(total_revenue) OVER (PARTITION BY dimensions->>'region') AS regional_total
FROM ta_daily_sales
WHERE time_bucket::date BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY 1, 2;
```

### **Query 2: Raw Data (Slow, Avoid)**
```sql
-- Avoid this! Scans billions of rows.
SELECT
    category,
    SUM(revenue) AS revenue
FROM facts_sales
WHERE event_time BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY category;
```

### **Query 3: Hybrid Approach (Dim Filter + Aggregates)**
```sql
-- Filter dimensions in application, aggregate via ta_*
WITH filtered_agg AS (
    SELECT * FROM ta_hourly_sales
    WHERE dimensions @> '{"category": "electronics"}'
)
SELECT
    time_bucket,
    total_revenue,
    (SELECT AVG(total_revenue) FROM filtered_agg) AS avg_revenue
FROM filtered_agg
GROUP BY 1, 2;
```

---

## **4. Performance Considerations**
| **Factor**               | **Recommendation**                                                                 |
|--------------------------|------------------------------------------------------------------------------------|
| **Granularity**          | Start with daily, add hourly/monthly as needed.                                   |
| **JSONB Indexing**       | Always index `jsonb` columns (`GIN` in PostgreSQL, `json_index` in Elasticsearch). |
| **Partitioning**         | Partition by time to enable pruning.                                              |
| **Storage Limits**       | Monitor growth; compress JSONB or use columnar formats (e.g., Parquet).          |
| **ETL Latency**          | Batch updates (e.g., hourly) vs. real-time (Kafka + streaming).                  |

---

## **5. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **When to Combine**                          |
|--------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **[Time-Based Partitioning](https://example.com/partitioning)** | Split tables by time for efficient queries.                          | Use with aggregates to prune old partitions. |
| **[Materialized Views](https://example.com/mv)**          | Auto-update aggregates without manual ETL.                        | For simpler use cases (less control).       |
| **[Columnar Storage](https://example.com/columnar)**      | Store data in columnar formats (e.g., Parquet, Iceberg).         | Reduce JSONB overhead in aggregates.         |
| **[Denormalization](https://example.com/denormalize)**    | Store aggregated dimensions inline (e.g., `region_id` as integer). | Improve JSONB query performance.             |
| **[Incremental ETL](https://example.com/incremental)**     | Update aggregates only for new data.                                | Critical for near-real-time systems.          |

---

## **6. Anti-Patterns**
❌ **Over-Aggregation**:
   - Avoid pre-computing every possible combination (e.g., hourly + daily + monthly by 50+ dimensions).
   - *Solution*: Start with 1–2 granularities (e.g., daily + weekly).

❌ **Static Aggregates**:
   - Never skip incremental updates; full recalculations are expensive.
   - *Solution*: Use `MERGE` or conditional `UPDATE`.

❌ **Ignoring Storage Costs**:
   - Aggregate tables can grow **10–100x** larger than fact tables.
   - *Solution*: Set retention policies (e.g., drop >1-year-old data).

❌ **Poor JSONB Design**:
   - Embedding all dimensions in JSONB slows down filtering.
   - *Solution*: Store high-cardinality fields separately (e.g., `category_id`).

---
## **7. Tools & Technologies**
| **Tool**            | **Purpose**                                                                 | Example Commands/Config          |
|---------------------|-----------------------------------------------------------------------------|-----------------------------------|
| **dbt**             | Define aggregates in SQL; manage ETL.                                       | `models/ta_hourly_sales.sql`     |
| **Airflow**         | Schedule incremental ETL jobs.                                              | `DAG` with `PostgresOperator`    |
| **PostgreSQL**      | Native JSONB support + `WITH` clauses for aggregations.                     | `CREATE MATERIALIZED VIEW`       |
| **Snowflake**       | Time travel + semi-structured data types.                                   | `CLUSTER BY` + `PARTITION BY`    |
| **Apache Iceberg**  | Open-table format for scalable aggregates.                                  | `ALTER TABLE SET TBLPROPS`        |
| **Elasticsearch**   | Full-text search on aggregated JSONB data.                                 | ` Painless scripting`            |

---
## **8. Migration Checklist**
1. **Assess Fact Table Size**:
   - If >10M rows/day, consider aggregates.
2. **Define Granularities**:
   - Start with daily; add hourly/monthly based on query patterns.
3. **Build ETL Pipeline**:
   - Use `dbt` or native SQL to populate `ta_*` tables.
4. **Implement Query Router**:
   - Rewrite queries to prefer aggregates where possible.
5. **Monitor Performance**:
   - Compare query times before/after migration.
6. **Optimize Storage**:
   - Add partitioning, compression, or columnar storage.