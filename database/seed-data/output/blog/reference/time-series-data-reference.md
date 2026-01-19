# **[Pattern] Time-Series Data Management Reference Guide**

---
## **Overview**
Time-Series Data Management organizes sequential measurements (e.g., sensor readings, financial ticks, IoT events) into structured datasets optimized for retrieval, analysis, and visualization over time. This pattern addresses challenges like:
- **Sparse or uneven intervals** (e.g., sensor data every 5 minutes vs. 10 minutes).
- **High cardinality** (millions of unique time-based entities).
- **Retention policies** (short-term high-resolution vs. long-term aggregated data).

Key trade-offs include storage efficiency vs. query performance, downsampling vs. raw retention, and ingestion speed vs. data integrity. This guide outlines core components, schema design, querying strategies, and best practices for implementing time-series systems.

---

## **1. Core Components**

| **Component**         | **Purpose**                                                                 | **Implementation Notes**                                                                                     |
|-----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Time Unit**         | Granularity of time measurements (e.g., seconds, milliseconds).             | Align with business needs (e.g., sub-second for trading data, hourly for environmental logs).             |
| **Entity**            | Unique identifier for a time-series (e.g., sensor ID, stock ticker).        | Use stable, immutable IDs (e.g., UUIDs) to avoid conflicts.                                               |
| **Measurement Value** | The actual metric (e.g., temperature, price).                                 | Support multiple data types (float, string, timestamp).                                                  |
| **Timestamp**         | Exact time of measurement (often in UTC).                                   | Use high-precision timestamps (nanoseconds) if required; avoid default system clocks.                     |
| **Tags/Attributes**   | Static metadata (e.g., `location="warehouse_1"`).                          | Reduce cardinality via controlled vocabularies (e.g., enum lists).                                        |
| **Downsampling**      | Aggregating data over time (e.g., average every 5 minutes).                 | Use windowed functions (e.g., `SELECT AVG(value) WHERE time >= '2023-01-01' GROUP BY 5min`).             |
| **Retention Policy**  | Rules for purging old data (e.g., "keep 1 year of raw data, 10 years of aggregates"). | Combine with storage tiering (hot/warm/cold).                                                            |
| **Ingestion Pipeline**| System for collecting and storing data (e.g., Kafka, Flink).                 | Optimize for throughput (batch vs. streaming) and fault tolerance.                                        |
| **Query Engine**      | Tool for analyzing time-series (e.g., InfluxDB, TimescaleDB, Prometheus).   | Choose based on language support (SQL vs. PromQL vs. custom APIs).                                          |

---

## **2. Schema Reference**

### **2.1 Basic Schema (Nested JSON)**
```json
{
  "entity": "sensor_001",
  "tags": {
    "location": "warehouse_1",
    "type": "temperature"
  },
  "measurements": [
    {
      "timestamp": "2023-10-01T12:00:00.123Z",
      "value": 25.3,
      "unit": "°C"
    },
    {
      "timestamp": "2023-10-01T12:05:00.456Z",
      "value": 25.1
    }
  ]
}
```
- **Best Practice**: Flatten nested data for simpler queries if cardinality is low.
- **Anti-Pattern**: Store raw JSON in a single column; normalize for indexing.

---

### **2.2 Columnar Storage Schema (SQL-Inspired)**
| **Column**      | **Type**       | **Description**                                                                 |
|------------------|----------------|---------------------------------------------------------------------------------|
| `entity`         | VARCHAR(64)    | Unique identifier for the time-series (e.g., sensor ID).                       |
| `timestamp`      | TIMESTAMPTZ    | High-precision UTC timestamp.                                                   |
| `measurement`    | DOUBLE         | Numeric value (extend to ARRAY for multi-metric series).                        |
| `tags`           | JSONB          | Key-value metadata (indexed for filtering).                                     |
| `retention_end`  | DATE           | Auto-delete timestamp (e.g., `CURRENT_DATE + INTERVAL '1 year'`).              |

- **Indexing**: Create composite indexes on `(entity, timestamp)` and `(tags, timestamp)`.
- **Partitioning**: Partition tables by time range (e.g., monthly) to reduce scan size.

---

### **2.3 Time-Series Specific Data Types**
| **Type**         | **Use Case**                          | **Example**                          | **Storage Optimizations**                  |
|-------------------|---------------------------------------|---------------------------------------|-------------------------------------------|
| **Timestamp**     | Exact measurement time.               | `2023-10-01 12:00:00.123456+00:00`   | Use `TIMESTAMPTZ` (with timezone) or `INTERVAL` for durations. |
| **Time-Interval** | Buckets for downsampling.             | `2023-10-01 00:00:00 TO 2023-10-01 05:00:00` | Store as `INTERVAL` or pre-computed key. |
| **Retention Tag** | Soft-delete marker.                   | `"$retention": "2024-01-01"`          | Query filter: `WHERE NOT tags->'$retention' IS NULL`. |

---

## **3. Query Examples**

### **3.1 Basic Retrieval**
**Scenario**: Fetch raw data for a sensor over a time range.
```sql
-- PostgreSQL (TimescaleDB)
SELECT entity, timestamp, measurement
FROM sensor_data
WHERE entity = 'sensor_001'
  AND timestamp BETWEEN '2023-10-01' AND '2023-10-02'
ORDER BY timestamp;
```

**Optimization**: Use a timebounded index (e.g., `CREATE INDEX ON sensor_data (entity, timestamp)`).

---

### **3.2 Downsampling**
**Scenario**: Compute 5-minute averages for a stock ticker.
```sql
-- InfluxQL (InfluxDB)
SELECT mean("close")
FROM "stocks"
WHERE "symbol" = 'AAPL'
  AND time >= '2023-10-01'
GROUP BY time(5m);
```

**Alternative (SQL)**:
```sql
-- TimescaleDB
SELECT
  time_bucket('5 minutes', timestamp) AS bucket,
  AVG(measurement) AS avg_value
FROM stock_data
WHERE entity = 'AAPL'
  AND timestamp >= '2023-10-01'
GROUP BY bucket;
```

---

### **3.3 Filtering by Tags**
**Scenario**: Find all temperature sensors in "warehouse_1" with values > 30°C.
```sql
-- JSONB indexing (PostgreSQL)
SELECT entity, timestamp, measurement
FROM sensor_data
WHERE tags->>'location' = 'warehouse_1'
  AND measurement > 30
  AND timestamp > NOW() - INTERVAL '1 hour';
```

**Optimization**: Ensure `tags` is indexed:
```sql
CREATE INDEX idx_sensor_tags_location ON sensor_data USING GIN (tags);
```

---

### **3.4 Alignment (Cross-Series Operations)**
**Scenario**: Join two time-series (e.g., temperature and humidity) on the same timestamps.
```python
# Using Pandas + TimescaleDB
import pandas as pd
from sqlalchemy import create_engine

# Fetch aligned data
temp_df = pd.read_sql(
    "SELECT timestamp, measurement AS temp FROM temp_data WHERE entity = 'sensor_001'",
    engine
)
humid_df = pd.read_sql(
    "SELECT timestamp, measurement AS humid FROM humid_data WHERE entity = 'sensor_001'",
    engine
)
# Merge on timestamp
result = pd.merge(
    temp_df,
    humid_df,
    on="timestamp",
    how="inner"
)
```

**Alternative (SQL)**:
```sql
-- Cross-series join (limited support; see TimescaleDB's hyperfunctions)
SELECT
  t.timestamp,
  t.measurement AS temp,
  h.measurement AS humid
FROM temp_data t
JOIN humid_data h ON t.entity = h.entity AND t.timestamp = h.timestamp;
```

---

### **3.5 Alerting Queries**
**Scenario**: Detect anomalies (e.g., temperature spikes).
```sql
-- Statistical deviation (PostgreSQL)
WITH stats AS (
  SELECT
    entity,
    STDDEV(measurement) AS stddev
  FROM sensor_data
  WHERE entity = 'sensor_001'
    AND timestamp > NOW() - INTERVAL '7 days'
  GROUP BY entity
)
SELECT s.*
FROM sensor_data s
CROSS JOIN stats
WHERE s.measurement > (stats.mean + 3 * stddev)
  AND timestamp > NOW() - INTERVAL '1 hour';
```

---

## **4. Best Practices**

| **Category**       | **Guideline**                                                                 | **Example**                                                                 |
|--------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Ingestion**      | Batch small writes; use async queues (e.g., Kafka).                           | Avoid single-row inserts; batch into 100–1,000 rows.                       |
| **Schema Design**  | Prefer columnar storage (e.g., TimescaleDB, Apache Druid) over row stores.    | Use `SUPER` tables in PostgreSQL for auto-created child tables per entity.   |
| **Compression**    | Enable columnar compression (e.g., Zstd, LZ4).                                | In TimescaleDB: `ALTER TABLE data SET (autovacuum_compression = true)`.    |
| **Retention**      | Tier data: hot (raw), warm (downsampled), cold (archived).                  | Move old data to S3/Parquet with a daily cron job.                         |
| **Querying**       | Use time-bound indexes and filters to limit scans.                           | Always include `WHERE timestamp > NOW() - INTERVAL '1d'`.                 |
| **Monitoring**     | Track write latency, query performance, and storage growth.                   | Use Prometheus + Grafana for metrics (e.g., `ingestion_duration_seconds`). |

---

## **5. Anti-Patterns**

| **Anti-Pattern**               | **Risk**                                                                     | **Fix**                                                                     |
|---------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Monolithic tables**          | Poor query performance; no downsampling.                                   | Partition by time/entity (e.g., `sensor_001_2023-10`).                     |
| **No retention policy**         | Unbounded storage growth.                                                   | Implement `ALTER TABLE ... SET (retention = '1 year')` in TimescaleDB.     |
| **Over-normalizing**            | Excessive joins; slow queries.                                              | Denormalize for time-series (e.g., store tags in a JSONB column).          |
| **Ignoring timezone**           | Incorrect alignment of global datasets.                                     | Store all timestamps in UTC; use `TIMESTAMPTZ`.                           |
| **Raw data only**               | Queries become unwieldy for long time ranges.                                | Pre-compute aggregates (e.g., daily summaries).                           |

---

## **6. Tooling Ecosystem**

| **Category**       | **Tools**                                                                   | **Notes**                                                                   |
|--------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Databases**      | InfluxDB, TimescaleDB, Prometheus, QuestDB, ClickHouse                      | TimescaleDB adds PostgreSQL compatibility; QuestDB is SQLite-based.        |
| **Ingestion**      | Kafka, Flink, AWS Kinesis, Apache Pulsar                                   | Use Flink for stateful processing (e.g., detecting anomalies).              |
| **Query Languages**| SQL (TimescaleDB), InfluxQL, PromQL, TimescaleDB’s hyperfunctions          | PromQL is declarative but limited to Prometheus.                           |
| **Visualization**  | Grafana, Metabase, Apache Superset, Kibana                                | Grafana supports multiple data sources; Metabase adds SQL flexibility.     |
| **Archival**       | S3/Parquet (Apache Arrow), Iceberg, Delta Lake                              | Use Arrow for cross-system compatibility.                                  |

---

## **7. Related Patterns**

1. ****[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)**
   - *Connection*: Time-series data often stems from event streams (e.g., sensor events).
   - *Divergence*: Event sourcing focuses on immutable logs; time-series emphasizes queries.

2. ****[Data Lakehouse](https://databricks.com/blog/data-lakehouse)**
   - *Connection*: Store raw time-series in Delta Lake/Parquet for analytics.
   - *Divergence*: Lakehouse patterns prioritize ACID transactions; time-series optimize for time-based access.

3. ****[CQRS](https://martinfowler.com/bliki/CQRS.html)**
   - *Connection*: Use separate read/write models (e.g., write to a time-series DB, read via a materialized view).
   - *Divergence*: Time-series adds the constraint of temporal ordering.

4. ****[Schema Evolution](https://www.postgresql.org/docs/current/ddl-schema-evolution.html)**
   - *Connection*: Time-series schemas may need to add columns (e.g., new sensors).
   - *Divergence*: Focus on backward compatibility (e.g., add `IF NOT EXISTS` to columns).

5. ****[Cost Optimization](https://cloud.google.com/blog/products/big-data/data-analytics-cost-optimization)**
   - *Connection*: Apply tiered storage and compression to time-series data.
   - *Divergence*: General data patterns may not account for time-series skew (e.g., hot/cold data separation).

---
## **8. Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Time-Indexed Data**  | Data where queries are predominantly filtered by time.                          |
| **Downsampling**       | Reducing granularity (e.g., summing every 5 minutes from 1-second data).       |
| **Hyperfunction**      | TimescaleDB’s extensible SQL functions (e.g., `time_bucket`) for time-series. |
| **Retention Policy**   | Rule to delete old data (e.g., "keep 30 days of raw data").                     |
| **Cardinality**        | Number of unique values in a column (high cardinality = poor indexing).       |
| **Materialized View**  | Pre-computed query result (e.g., daily averages) to speed up reads.           |