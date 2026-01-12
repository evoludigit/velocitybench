# **[Pattern] Arrow Format Analytics (av_*) Reference Guide**

---

## **1. Overview**
The **Arrow Format Analytics (av_*)** pattern in FraiseQL enables columnar, compressed data access optimized for analytical workloads. These views (prefixed with `av_*`) expose data in **Apache Arrow** format—a memory-efficient, column-oriented structure ideal for tools like **Tableau, Power BI, Spark, or direct Arrow-based processing**.

This pattern supports:
- **Compression** (e.g., Zstd, LZ4) to reduce scanning overhead.
- **Partitioned reads** to skip irrelevant data faster.
- **Metadata-aware filtering** (pushdown predicates) for efficient query execution.
- **Batch fetching** to minimize round-trips to storage.

Use this pattern when targeting analytics tooling that natively consumes Arrow or requires low-latency column scans.

---

## **2. Schema Reference**
Arrow views follow a standardized schema with the following components:

| Attribute          | Type          | Description                                                                 | Example Values                     |
|--------------------|---------------|-----------------------------------------------------------------------------|------------------------------------|
| `table_name`       | `string`      | The underlying table (e.g., `sales_2023`).                                  | `av_sales_2023`                    |
| `schema_id`        | `int`         | Unique identifier for the Arrow schema definition.                          | `12345`                            |
| `compression`      | `string`      | Compression algorithm (e.g., `zstd`, `lz4`, `none`).                       | `"zstd"`                           |
| `partition_cols`   | `array<string>`| Columns used for partitioning/filtering.                                   | `["date", "region"]`               |
| `metadata`         | `json`        | Additional schema metadata (e.g., data types, nullability).                 | `{"column_types": {"date": "timestamp"}}` |
| `rows`             | `int`         | Approximate row count (for planning).                                       | `42_000_000`                       |
| `last_updated`     | `timestamp`   | When the view was last refreshed.                                           | `2024-02-20 14:30:00`             |

### **Example Schema Output**
```sql
SELECT * FROM av_sales_2023 WHERE table_name = 'sales_2023';
```
Result:
```
┌─────────────┬───────────┬─────────────────┬────────────────┬─────────────┬─────────────────┬─────────┐
│ table_name  │ schema_id │ compression    │ partition_cols │ metadata      │ rows          │ last_updated │
├─────────────┼───────────┼─────────────────┼────────────────┼─────────────┼─────────────────┼─────────┤
│ sales_2023  │ 12345     │ zstd           │ [date, region]  │ {...}        │ 42000000      │ 2024-02-20 │
└─────────────┴───────────┴─────────────────┴────────────────┴─────────────┴─────────────────┴─────────┘
```

---

## **3. Query Examples**

### **A. Basic Arrow View Access**
```sql
-- Retrieve data as an Arrow stream (compatible with Arrow consumers)
SELECT * FROM av_sales_2023;
```
**Output**: Returns data in columnar Arrow format (e.g., for direct ingestion into Tableau/Power BI).

---

### **B. Filtering with Pushdown Predicates**
Leverage partition columns for efficient scanning:
```sql
-- Filter by date (uses partitioned index)
SELECT * FROM av_sales_2023
WHERE date >= '2023-01-01' AND region = 'EU';
```
**Note**: Only scans the `EU` partition for dates ≥ `2023-01-01`.

---

### **C. Column Projection**
Select specific columns to reduce data transfer:
```sql
-- Fetch only high-value columns (e.g., for Spark/SQL engines)
SELECT customer_id, amount, transaction_date
FROM av_sales_2023;
```

---

### **D. Aggregations with Arrow Optimizations**
```sql
-- Group-by with Arrow’s columnar execution
SELECT region, SUM(amount) AS total_sales
FROM av_sales_2023
GROUP BY region;
```
**Performance**: Aggregations run in-memory on Arrow batches.

---

### **E. Dynamic Schema Evolution**
Update compression or partition columns without recreating the view:
```sql
-- Add a new partition column dynamically
ALTER TABLE av_sales_2023 ADD PARTITION COLUMN product_category;
```

---

## **4. Implementation Details**

### **A. Compression Algorithms**
| Compression    | Use Case                          | Overhead |
|-----------------|-----------------------------------|----------|
| `zstd`          | Balanced speed/compression        | Medium   |
| `lz4`           | Low-latency decompression        | Low      |
| `none`          | No compression (dev/testing)     | High     |

**Recommendation**: Use `zstd` for most workloads.

---

### **B. Partitioning Strategy**
- **Static**: Predefined (e.g., `date`, `region`).
- **Dynamic**: Add runtime partitions (e.g., `product_category`) via `ALTER TABLE`.

**Example Partitioning**:
```sql
-- Pre-partitioned by date (monthly)
CREATE VIEW av_sales_2023 (
  table_name = 'sales_2023',
  partition_cols = ['date', 'region'],
  compression = 'zstd'
) AS SELECT * FROM sales_2023;
```

---

### **C. Metadata Handling**
Arrow views store schema metadata in the `metadata` field:
```json
{
  "column_types": {
    "customer_id": "int64",
    "amount": "float64",
    "transaction_date": "timestamp[us]"
  },
  "null_values": ["customer_id": false]
}
```
**Tools**: consumers (e.g., Tableau) auto-detect types from this field.

---

## **5. Query Optimization Rules**
1. **Predicate Pushdown**: FraiseQL pushes filters to Arrow metadata if possible.
   - Example: `WHERE region = 'EU'` skips non-EU partitions.
2. **Batch Fetching**: Data is streamed in chunks (e.g., 1MB) to avoid OOM errors.
3. **Column Pruning**: Only selected columns are materialized.

---

## **6. Limitations**
- **No Upserts**: Arrow views are read-only (append-only updates via `INSERT`).
- **Tool Dependencies**: Requires Arrow-native consumers (e.g., PyArrow, Tableau).
- **Schema Stability**: Avoid frequent schema changes (e.g., column deletions).

---

## **7. Related Patterns**
| Pattern               | Purpose                                                                 | When to Use                          |
|-----------------------|-------------------------------------------------------------------------|--------------------------------------|
| **Materialized Views**  | Pre-compute aggregates for repeated queries.                            | OLAP workloads with fixed aggregations. |
| **Delta Lake**         | ACID transactions on Arrow data.                                        | Shared datasets needing versioning.   |
| **Iceberg**            | Schema evolution + time travel for Arrow tables.                         | Large-scale data lakes.              |
| **Parquet Optimization**| Columnar storage (non Arrow) with Snappy/Zstd.                         | Legacy tooling (e.g., Hive).         |

---

## **8. Troubleshooting**
| Issue                     | Diagnosis                          | Solution                                  |
|---------------------------|-------------------------------------|-------------------------------------------|
| Slow scans                | No predicate pushdown.              | Add `WHERE` clauses to filter partitions. |
| Corrupted Arrow data      | Compression mismatch.               | Rebuild with `compression = 'none'`.      |
| Tool compatibility issue   | Schema mismatch.                    | Check `metadata` JSON in FraiseQL.        |

---

## **9. Example Workflow**
```sql
-- 1. Create a partitioned Arrow view
CREATE VIEW av_logs_2024 (
  table_name = 'app_logs',
  partition_cols = ['timestamp', 'service'],
  compression = 'lz4'
) AS SELECT * FROM app_logs WHERE timestamp > '2024-01-01';

-- 2. Export to Tableau (Arrow format)
SELECT * FROM av_logs_2024
WHERE service = 'auth' AND timestamp BETWEEN '2024-02-01' AND '2024-02-28';
```
**Result**: Tableau imports data directly as an Arrow table.