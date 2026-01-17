# **Debugging Partitioning & Time-Series Data: A Troubleshooting Guide**
*For Backend Engineers*

---

## **1. Symptom Checklist**
Before diving into fixes, confirm which symptoms align with your issue:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| ❌ **Full table scans**              | Queries scan months/years of data even when only recent data is queried.      |
| ❌ **Vacuum locks**                  | `VACUUM`, `ANALYZE`, or `REINDEX` operations block application queries for hours. |
| ❌ **Slow inserts**                  | High-latency writes (e.g., >100ms per row) even with indexed columns.          |
| ❌ **Storage bloat**                 | Disk usage grows uncontrollably despite archiving "old" data.                  |
| ❌ **High memory pressure**          | `pg_stat_activity` shows long-running queries with high `parallel_workers`.    |
| ❌ **Time-series skews**             | Uneven data distribution across partitions (e.g., one partition holds 90% of rows). |

If multiple symptoms persist, prioritize them by impact (e.g., **slow inserts** block transactional systems, while **storage bloat** is a long-term concern).

---

## **2. Common Issues and Fixes**
### **A. Full Table Scans**
**Root Cause:**
- Missing or inefficient partitioning keys (e.g., no time-based partitioning).
- Lack of proper indexes on partition keys.
- Queries using `WHERE` clauses that don’t leverage partitioning (e.g., filtering on a non-partitioned column).

**Fixes:**

#### **1. Ensure Proper Partitioning Strategy**
**Time-based partitioning (PostgreSQL):**
```sql
-- Create a partitioned table with time-based ranges
CREATE TABLE sensor_readings (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION,
    sensor_id INT
)
PARTITION BY RANGE (timestamp);

-- Add monthly partitions (adjust range to your needs)
CREATE TABLE sensor_readings_y2023m01 PARTITION OF sensor_readings
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');

CREATE TABLE sensor_readings_y2023m02 PARTITION OF sensor_readings
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
-- ... repeat for future months
```

**Verify partition usage:**
```sql
-- Check which partitions are being scanned
EXPLAIN ANALYZE SELECT * FROM sensor_readings WHERE timestamp > '2023-01-01';
```
**Expected Output:**
Should only scan `sensor_readings_y2023m01` (and similar recent partitions).

---

#### **2. Add Indexes on Partition Keys**
If querying by `sensor_id` frequently, add a **partitioned index**:
```sql
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings (sensor_id);
```
*For PostgreSQL 12+*, use **partial indexes** to reduce overhead:
```sql
CREATE INDEX idx_sensor_readings_recent_sensor_id
ON sensor_readings (sensor_id)
WHERE timestamp > '2023-01-01';
```

---

### **B. Vacuum/Maintenance Lockups**
**Root Cause:**
- Large tables with **high row count** (billions+) force full table scans during `VACUUM`.
- **Missing `VACUUM FREEZE`** leads to bloat over time.
- **Parallel vacuum** isn’t configured for large partitions (default `parallel_vacuum` is too low).

**Fixes:**

#### **1. Schedule Maintenance During Off-Peak Hours**
```sql
-- Run vacuum in parallel (adjust workers based on CPU cores)
ALTER SYSTEM SET parallel_vacuum_workers = 8;
ALTER SYSTEM SET maintenance_work_mem = '2GB'; -- For large tables
RELOAD pg_settings;
```
*Run during low-traffic periods:*
```bash
# Use pg_cron or a scheduled job (e.g., Cron)
VACUUM (VERBOSE, ANALYZE, PARALLEL 4) sensor_readings_y2023m01;
```

#### **2. Automate Partition Maintenance**
**PostgreSQL 12+** supports **partition-specific maintenance**:
```sql
-- Vacuum only recent partitions (e.g., last 6 months)
DO $$
DECLARE
    recent_threshold TIMESTAMPTZ := CURRENT_DATE - INTERVAL '6 months';
BEGIN
    FOR partition IN
        SELECT tablename FROM pg_partitioned_table_usage()
        WHERE partition_key_column = 'timestamp'
        AND partition_name LIKE 'sensor_readings_y%'
    LOOP
        EXECUTE format('VACUUM (VERBOSE, ANALYZE) "%s"', partition.tablename);
    END LOOP;
END $$;
```

---

### **C. Slow Inserts**
**Root Cause:**
- **Batch inserts** without `ON CONFLICT` or partitioning.
- **Missing indexes** on `INSERT` paths.
- **Network latency** (if writing via API/gateway).

**Fixes:**

#### **1. Use Batch Inserts with Partition Keys**
```sql
-- Insert into a specific partition (faster than full table)
INSERT INTO sensor_readings_y2023m05 (timestamp, value, sensor_id)
VALUES
    ('2023-05-01 10:00', 23.5, 1),
    ('2023-05-01 10:01', 24.1, 1)
RETURNING id;
```
*For bulk inserts (1000+ rows), use `COPY FROM`:*
```bash
COPY sensor_readings_y2023m05(timestamp, value, sensor_id)
FROM '/path/to/data.csv' DELIMITER ',' CSV;
```

#### **2. Optimize Insert Paths**
- **Upsert with `ON CONFLICT`** (avoids duplicate checks):
  ```sql
  INSERT INTO sensor_readings (timestamp, value, sensor_id)
  VALUES (now(), 23.5, 1)
  ON CONFLICT (sensor_id, timestamp)
  DO UPDATE SET value = EXCLUDED.value;
  ```
- **Use `INSERT ... SELECT`** for bulk loads from another table:
  ```sql
  INSERT INTO sensor_readings PARTITION FOR (timestamp)
  SELECT * FROM staging_data;
  ```

#### **3. Monitor Insert Latency**
```sql
-- Check slow insert queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE query LIKE '%INSERT INTO sensor_readings%'
ORDER BY mean_time DESC;
```
*If mean_time > 100ms, investigate partitioning or indexes.*

---

### **D. Storage Explosion**
**Root Cause:**
- **Retention policy violations** (data isn’t purged).
- **Unused partitions** accumulate (e.g., old monthly partitions).
- **Transaction logs** (`pg_xlog`) grow unbounded.

**Fixes:**

#### **1. Implement Automatic Archiving**
**Option 1: PostgreSQL Table Inheritance (Manual Cleanup)**
```sql
-- Drop old partitions (e.g., >1 year old)
DO $$
DECLARE
    cutoff_date TIMESTAMPTZ := CURRENT_DATE - INTERVAL '1 year';
BEGIN
    EXECUTE format('DROP TABLE IF EXISTS sensor_readings_y%', to_char(cutoff_date, 'YYYYMM'));
END $$;
```

**Option 2: Use `pg_partman` (Automated Partition Management)**
```bash
# Install pg_partman (PostgreSQL extension)
CREATE EXTENSION pg_partman;

-- Configure automatic partitioning
SELECT pg_partman.create_partition_by_range(
    'sensor_readings',
    'timestamp',
    NULL, -- Start date (default: oldest data)
    'END OF MONTH',
    'sensor_readings_y%YYYYMM',
    12  -- Retention months
);
```
*Now, partitions auto-drop after 12 months.*

#### **2. Compress Data with `TOAST` and `pg_compress`**
```sql
-- Enable TOAST for large columns (e.g., JSONB, TEXT)
ALTER TABLE sensor_readings SET (toast.compression = 'pg_lz4');
```
*For existing tables, run:*
```sql
-- Rebuild TOAST data
VACUUM (FULL, VERBOSE) sensor_readings_y2023m01;
```

#### **3. Monitor Disk Usage**
```sql
-- Check table sizes by partition
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as total_size,
    pg_size_pretty(pg_relation_size(tablename::regclass)) as heap_size
FROM pg_partitioned_table_usage()
WHERE tablename LIKE 'sensor_readings%';
```

---

## **3. Debugging Tools and Techniques**
### **A. PostgreSQL-Specific Tools**
| Tool                     | Purpose                                                                 |
|--------------------------|-------------------------------------------------------------------------|
| `EXPLAIN ANALYZE`        | Inspect query plans and identify full table scans.                      |
| `pg_partman`             | Automate partition management (create/drop/optimize).                   |
| `pg_stat_statements`     | Track slow queries and expensive inserts.                              |
| `pg_partitioned_table_usage()` | List all partitions and their sizes.                                  |
| `VACUUM VERBOSE`         | Pinpoint bloat in specific partitions.                                  |

**Example: Debug a Slow Query**
```sql
EXPLAIN ANALYZE
SELECT sensor_id, AVG(value)
FROM sensor_readings
WHERE timestamp > '2023-01-01'
  AND timestamp < '2023-01-31'
GROUP BY sensor_id;
```
**Fix if it scans all partitions:**
Add a **partition-specific index**:
```sql
CREATE INDEX idx_sensor_readings_2023m01_sensor_id
ON sensor_readings_y2023m01 (sensor_id);
```

---

### **B. External Tools**
| Tool               | Use Case                                  |
|--------------------|-------------------------------------------|
| **TimescaleDB**    | Hypertable extension for time-series (better compression/retention). |
| **Prometheus + Grafana** | Monitor partition sizes and query latency. |
| **pgBadger**       | Log analysis to detect vacuum/bloat issues. |
| **Cloud SQL Insights (GCP)** | Auto-diagnose partitioning mismatches. |

---

## **4. Prevention Strategies**
| **Strategy**                          | **Action Items**                                                                 |
|----------------------------------------|--------------------------------------------------------------------------------|
| **Enforce Retention Policies**        | Use `pg_partman` or custom scripts to drop old partitions.                     |
| **Limit Partition Granularity**       | Monthly partitions (not daily) reduce overhead.                                |
| **Batch Inserts > Single Row**        | Use `COPY FROM` or `INSERT ... VALUES` batches (1000+ rows).                   |
| **Monitor Partition Skew**            | Check `pg_stat_user_tables` for uneven row distributions.                      |
| **Schedule Maintenance**              | Run `VACUUM` during off-peak hours (e.g., midnight).                           |
| **Use Time-Series DBs for Heavy Loads** | Offload to TimescaleDB, ClickHouse, or InfluxDB if PostgreSQL struggles.       |

---

## **5. Quick Reference Table**
| **Symptom**               | **Likely Cause**               | **Immediate Fix**                          | **Long-Term Fix**                     |
|---------------------------|---------------------------------|--------------------------------------------|----------------------------------------|
| Full table scans           | Missing partitioning            | Add `PARTITION BY RANGE`                  | Use `pg_partman` for auto-management |
| Vacuum lockups             | Large partitions                | Run `VACUUM PARALLEL`                      | Increase `maintenance_work_mem`       |
| Slow inserts              | No partition key in `INSERT`    | Route inserts to correct partition        | Use `INSERT ... SELECT FROM staging`  |
| Storage bloat              | Unarchived old data             | Drop old partitions manually               | Set up `pg_partman` retention rules   |
| High memory pressure      | Parallel queries                | Limit `max_parallel_workers`               | Use `LIMIT` in queries                |

---

## **Next Steps**
1. **Start with the worst symptom** (e.g., full scans block reports; slow inserts break APIs).
2. **Validate fixes** with `EXPLAIN ANALYZE` and `pg_stat_statements`.
3. **Automate maintenance** (e.g., `pg_partman`, cron jobs).
4. **Consider specialized DBs** (TimescaleDB) if PostgreSQL remains a bottleneck.

By following this guide, you can resolve partitioning issues systematically—**from immediate fixes to scalable long-term solutions**.