# **[Pattern] CDC Archival Strategy Reference Guide**

---

## **Overview**
The **CDC (Change Data Capture) Archival Strategy** pattern ensures long-term persistence of historical data changes in a structured, queryable format by decoupling ongoing CDC capture from archival storage. This pattern is ideal for applications requiring compliance (e.g., regulatory audits), analytics (e.g., time-series queries), or historical replay capabilities (e.g., disaster recovery). By separating hot CDC data (active streams) from cold archival data (immutable logs), the pattern optimizes performance, reduces storage costs, and simplifies retrieval.

Key use cases include:
- Financial audits requiring 7+ years of transaction history.
- Machine learning models trained on historical data trends.
- Rollback/recovery scenarios in distributed systems.

---

## **Key Concepts**
| Term            | Definition                                                                                     |
|-----------------|-----------------------------------------------------------------------------------------------|
| **CDC Stream**  | A real-time stream of record-level changes (inserts, updates, deletes) from source systems.    |
| **Archival Bucket** | A durable storage layer (e.g., S3, HDFS) for immutable CDC logs, organized by time/partition.|
| **Compaction**  | Process of merging small CDC files into larger batches to reduce I/O overhead.               |
| **Snapshot**    | Periodic snapshots of the source state (e.g., full table dumps) used for reconciliation.      |
| **Partitioning**| Strategy to split archival data by time (e.g., day/month) or schema to optimize queries.     |
| **Metadata Store** | Database tracking archival state (e.g., last synced offset, compacted files).                |

---

## **Schema Reference**
The archival strategy assumes a **time-partitioned schema** for CDC logs, where each log entry includes:
- **Source System**: Database/table name (e.g., `orders#users`).
- **Change Type**: `{INSERT, UPDATE, DELETE}`.
- **Payload**: JSON blob of affected records (schema-variant).
- **Timestamp**: Exact change time (microsecond precision).
- **Partition Key**: `source_system#timestamp_bucket` (e.g., `orders#2023-10-01`).

### **Example Schema (JSON)**
```json
{
  "source_system": "orders#users",
  "change_type": "UPDATE",
  "payload": {
    "user_id": "123",
    "updated_at": "2023-10-15T12:34:56.789Z",
    "changes": {
      "name": "John Doe",
      "status": "ACTIVE"
    }
  },
  "partition_key": "orders#2023-10-01",
  "offset": "500000000001",  // Source system offset (e.g., Debezium)
  "metadata": {
    "compacted": true,
    "checksum": "sha256:abc..."
  }
}
```

### **Storage Layout**
```
s3://archival-bucket/
├── orders/
│   ├── users/
│   │   ├── 2023-10-01/  # Partitioned by date
│   │   │   ├── 2023-10-01T00-00-00.parquet  # Compacted file
│   │   │   └── metadata.json                # Partition manifest
│   │   └── 2023-10-02/
│   └── transactions/
│       └── 2023-10-01/
└── metadata/
    └── archival-state.db       # SQLite for tracking offsets
```

---

## **Implementation Steps**

### **1. CDC Pipeline Configuration**
- **Source**: Configure CDC (e.g., Debezium, Kafka Connect) to emit changes to a Kafka topic.
- **Sink**: Forward messages to an archival storage (e.g., S3, HDFS) via a transform layer (e.g., Flink, Spark Streaming).
- **Compaction Policy**:
  ```python
  # Pseudo-code for compaction job (e.g., Spark)
  spark.read.json("s3://raw-cdc-logs/")
    .filter("compacted = false")
    .groupBy("partition_key")
    .agg(collect_list("payload").as("compacted_payload"))
    .write.parquet("s3://compacted-logs/")
  ```

### **2. Partitioning Strategy**
| Strategy               | Use Case                          | Example Partition Key       |
|------------------------|-----------------------------------|-----------------------------|
| **Time-based**         | Time-series analytics              | `YYYY-MM-dd`                 |
| **Schema-based**       | Separate high/low-frequency tables | `source_system#table_name`  |
| **Hybrid**             | Mix of time + schema              | `source_system#YYYY-MM`     |

### **3. Metadata Management**
- Track **offsets** (last synced position in source) in a lightweight DB (e.g., SQLite).
- Example `archival_state` table:
  ```sql
  CREATE TABLE archival_state (
    source_system TEXT PRIMARY KEY,
    last_offset   BIGINT,
    last_compacted TIMESTAMP,
    retention_days INT DEFAULT 365
  );
  ```

---

## **Query Examples**

### **1. Reconstruct Table State at a Point-in-Time**
```sql
-- SQL query (simplified) to rebuild a table from archival logs
WITH deleted AS (
  SELECT payload.user_id
  FROM archival_logs
  WHERE source_system = 'orders#users'
    AND change_type = 'DELETE'
    AND partition_key = 'orders#2023-10-01'
),
updated AS (
  SELECT payload.user_id, payload.changes.name, payload.changes.status
  FROM archival_logs
  WHERE source_system = 'orders#users'
    AND change_type = 'UPDATE'
    AND partition_key = 'orders#2023-10-01'
),
inserted AS (
  SELECT payload.user_id, payload.name, payload.status
  FROM archival_logs
  WHERE source_system = 'orders#users'
    AND change_type = 'INSERT'
    AND partition_key = 'orders#2023-10-01'
)
SELECT user_id, name, status
FROM (
  SELECT * FROM inserted
  EXCEPT
  SELECT user_id FROM deleted
)
UNION ALL
SELECT user_id, name, status
FROM updated;
```

### **2. Query Archival Data with Athena/Presto**
```sql
-- Athena query on S3-parquet data
SELECT
  source_system,
  change_type,
  payload->>'user_id' AS user_id,
  TO_TIMESTAMP(payload->>'timestamp') AS event_time
FROM archival_db.orders.users
WHERE partition_key = 'orders#2023-10-01'
  AND TO_DATE(event_time) = '2023-10-15'
ORDER BY event_time DESC;
```

### **3. Find All Changes for a User ID**
```python
# PySpark example
df = spark.read.parquet("s3://compacted-logs/orders/users/")
df.filter("payload.user_id = '123'")
  .select(
    "partition_key",
    "change_type",
    "payload.name.as_user_name",
    "payload.status.as_user_status"
  )
  .orderBy("payload.timestamp")
  .show()
```

---

## **Performance Considerations**
| Factor               | Optimization Strategy                                  |
|----------------------|------------------------------------------------------|
| **Read Latency**     | Use columnar formats (Parquet/ORC) with predicate pushdown. |
| **Write Throughput** | Batch compaction jobs (e.g., hourly/daily).          |
| **Storage Cost**     | Tiered storage (e.g., S3 Intelligent-Tiering).       |
| **Schema Evolution** | Use AVRO/Protobuf for backward-compatible payloads. |

---

## **Related Patterns**
1. **[Event Sourcing]** – Complementary for storing immutable event streams alongside CDC.
2. **[Schema Registry]** – Required to resolve payload schemas over time.
3. **[Data Lakehouse]** – Integrates archival data with SQL engines (e.g., Delta Lake) for analytics.
4. **[Exactly-Once Semantics]** – Ensures no duplicate or missing changes in archival logs.
5. **[Cold/Warm Storage Tiering]** – Moves old archival data to cheaper storage (e.g., Glacier).

---

## **Error Handling & Reconciliation**
- **Checksum Validation**: Verify payload integrity via CRC32C or SHA-256.
- **Reconciliation Snapshots**: Periodically compare archival counts with source DB row counts.
- **Dead Letter Queue (DLQ)**: Route failed archival writes to a separate topic for debugging.

---
**Example Reconciliation Query**:
```sql
SELECT
  s.source_system,
  COUNT(*) AS source_rows,
  a.total_archived_changes,
  (COUNT(*) - a.total_archived_changes) AS missing_changes
FROM source_tables s
LEFT JOIN (
  SELECT source_system, COUNT(*) AS total_archived_changes
  FROM archival_logs
  GROUP BY source_system
) a ON s.source_system = a.source_system
WHERE s.last_updated > DATEADD(day, -7, CURRENT_DATE)
GROUP BY 1, 2;
```

---
**Tools & Frameworks**
| Component          | Tools/Frameworks                          |
|--------------------|-------------------------------------------|
| CDC Capture        | Debezium, Kafka Connect, AWS DMS          |
| Stream Processing  | Apache Flink, Spark Streaming            |
| Archival Storage   | S3, HDFS, Azure Blob Storage              |
| Query Engine       | Athena, Presto, Trino                    |
| Metadata DB        | SQLite, PostgreSQL, DynamoDB             |

---
**References**
- [Debezium CDC Documentation](https://debezium.io/documentation/reference/)
- [AWS S3 Durability](https://aws.amazon.com/s3/security/)
- [Apache Flink Compaction](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/fault-tolerance/checkpointing/)