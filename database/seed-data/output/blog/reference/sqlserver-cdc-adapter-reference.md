# **[Pattern] SQL Server CDC Adapter Reference Guide**

---

## **Overview**
The **SQL Server Change Data Capture (CDC) Adapter Pattern** enables real-time or near-real-time synchronization of changes from SQL Server databases into other systems (e.g., data warehouses, messaging queues, or applications). By leveraging SQL Server’s built-in CDC functionality, this pattern captures **INSERT, UPDATE, and DELETE** operations, formats them into structured events, and routes them via an adapter to downstream consumers.

This guide covers:
- **Key concepts** (CDC tables, operations, and metadata)
- **Schema structure** of CDC-related tables
- **Query patterns** for capturing and processing changes
- **Integration considerations** (ETL/ELT pipelines, event-driven architectures)
- **Best practices** for performance, error handling, and scalability

---

## **Key Concepts**

### **1. SQL Server CDC Core Components**
| **Component**          | **Description**                                                                                     | **Lifespan**                     |
|------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------|
| **CDC Enablement**     | Logical flag applied to database or schema to track changes.                                         | Persists until disabled.         |
| **Change Tables**      | Shadow tables (`__cdc.<tablename>`) storing historical changes.                                     | Retained until purge.            |
| **LSN (Log Sequence Numbers)** | Unique identifiers tracking transaction logs. Used to track progress.              | Ephemeral (per session).         |
| **Operations**         | `START`, `INSERT`, `UPDATE`, `DELETE`, `END` markers defining change boundaries.                    | Temporary during capture.        |

### **2. CDC States & Progress Tracking**
SQL Server maintains CDC state via:
- **`msdb.dbo.cdc_<dbname>_<schema>_<table>_ct`** (change tracking table)
- **`sys.change_tracking_*`** (system views for manual CDC enablement)
- **`sys.change_tracking_tables`** (metadata for enabled tables)

---
## **Schema Reference**

### **1. CDC Change Tables (`__cdc.<tablename>`)**
Each CDC-enabled table generates a shadow table with these columns:

| **Column**            | **Data Type**       | **Description**                                                                                     |
|-----------------------|---------------------|-----------------------------------------------------------------------------------------------------|
| `__$start_lsn`        | `VARBINARY(10)`     | Log Sequence Number marking the start of the operation.                                             |
| `__$end_lsn`          | `VARBINARY(10)`     | Log Sequence Number marking the end of the operation.                                               |
| `__$operation`        | `VARCHAR(1)`        | `'I'` (INSERT), `'U'` (UPDATE), `'D'` (DELETE), or `'S'` (START).                                  |
| `__$update_mask`      | `VARBINARY(8000)`   | Bitmask indicating modified columns (for `U` operations).                                           |
| `__$seqval`           | `BIGINT`            | Sequence value for ordering changes (if enabled).                                                   |
| **Original Columns**  | (Same as schema)    | Data values (NULL for `DELETE` or before `UPDATE`).                                                 |

**Example Shadow Table:**
```sql
SELECT * FROM __cdc.Orders
WHERE __$operation IN ('I', 'U', 'D')
ORDER BY __$start_lsn;
```

---

### **2. System Metadata Tables**
| **Table**                          | **Purpose**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------------------------|
| `sys.change_tracking_tables`       | Lists enabled tables with CDC settings (`is_tracked_by_lsn`, `is_tracked_by_version`).        |
| `msdb.dbo.cdc_<dbname>_<schema>_<table>_ct` | Tracks progress (last captured LSN, next LSN to read).        |
| `sys.fn_cdc_get_all_changes_<type>` | Functions to query changes (`DC`, `DC_N`, `DC_T`, `DS_N`, `DS_T`).                           |

---

## **Query Examples**

### **1. Enabling CDC for a Database**
```sql
-- Enable CDC at the database level (SQL Server 2008+)
ALTER DATABASE YourDB SET CDC = ON WITH TRACKED BY DEFAULT;

-- Enable CDC for a specific schema/table
EXEC sys.sp_cdc_enable_table
    @source_schema = 'dbo',
    @source_name = 'Orders',
    @role_name = NULL,  -- Default role
    @capture_instance = 'YourCaptureInstance';
```

### **2. Capturing Changes**
#### **Option A: All Changes (Since Last Sync)**
```sql
-- Get all changes (new/updated/deleted rows)
DECLARE @FromLSN UNIQUEIDENTIFIER, @ToLSN UNIQUEIDENTIFIER;
SET @FromLSN = '00000001000100000000000D'; -- Replace with last known LSN
SET @ToLSN = '000000010001000100000017'; -- Replace with next LSN (or NULL for latest)

SELECT * FROM sys.fn_cdc_get_all_changes_ct(
    N'YourDB', N'dbo', N'Orders',
    @FromLSN, @ToLSN, 'ALL', 'LATEST');
```

#### **Option B: New Rows Only**
```sql
-- Filter only INSERT operations
SELECT __$start_lsn, *
FROM __cdc.Orders
WHERE __$operation = 'I';
```

#### **Option C: Using Change Tables Directly**
```sql
-- Read CDC table with pagination (for large tables)
DECLARE @BatchSize INT = 1000;
DECLARE @MaxLSN UNIQUEIDENTIFIER = NULL;

WHILE 1 = 1
BEGIN
    SELECT TOP (@BatchSize) *
    FROM __cdc.Orders
    WHERE (__$operation IN ('I', 'U', 'D'))
      AND (@MaxLSN IS NULL OR __$start_lsn > @MaxLSN)
    ORDER BY __$start_lsn;

    -- Update @MaxLSN to the last processed LSN (if any rows returned)
    -- Break if no more rows...
END
```

### **3. Tracking Progress**
```sql
-- Get the last captured LSN for a table
SELECT __$start_lsn AS last_captured_lsn
FROM __cdc.Orders
ORDER BY __$start_lsn DESC
OFFSET 0 ROWS
FETCH NEXT 1 ROW ONLY;

-- Reset CDC progress (for resync)
EXEC sys.sp_cdc_truncate_table
    @source_schema = 'dbo',
    @source_name = 'Orders';
```

### **4. Handling Gaps or Errors**
```sql
-- Restart CDC from a known LSN (e.g., after failure)
DECLARE @StartLSN UNIQUEIDENTIFIER = '000000010001000000000010';
SELECT * FROM sys.fn_cdc_get_net_changes_ct(
    N'YourDB', N'dbo', N'Orders',
    @StartLSN, 'ALL', 'LATEST');
```

---

## **Best Practices**

### **1. Performance Considerations**
- **Batch Processing:** Process changes in batches (e.g., 1,000–10,000 rows) to avoid blocking.
- **Indexing:** Ensure CDC shadow tables have indexes on `__$start_lsn` and `__$seqval`.
- **Log Retention:** Configure `cdc_retention` (in hours) to balance latency and storage:
  ```sql
  ALTER DATABASE YourDB SET CDC = ON WITH TRACKED BY DEFAULT, RETENTION = 24;
  ```

### **2. Error Handling**
- **Deadlocks:** Use `READPAST` to skip locked rows:
  ```sql
  SET TRANSACTION ISOLATION LEVEL READPAST;
  ```
- **Retry Logic:** Implement exponential backoff for transient failures (e.g., network issues).

### **3. Scalability**
- **Parallel Processing:** Use multiple worker threads to read CDC tables concurrently.
- **Partitioning:** For large tables, split CDC processing by partitions (e.g., by date).

### **4. Security**
- **Permissions:** Grant `SELECT` on shadow tables to CDC consumers only.
- **Audit Logs:** Monitor `sys.fn_cdc_get_all_changes_DDL()` for schema changes.

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                     | **Use Case**                                      |
|----------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **[Database Change Data Capture]** | High-level pattern for syncing database changes to other systems.                                  | Real-time sync with external systems.            |
| **[Event Sourcing]**             | Appends changes as immutable events to a log.                                                     | Audit trails, replayable state.                   |
| **[CDC + Kafka/Event Hub]**      | Streams CDC changes to a message broker for decoupled processing.                                  | Microservices, analytics pipelines.               |
| **[Hybrid CDC + CDC]**           | Combines SQL Server CDC with a secondary CDC system (e.g., Debezium) for cross-database sync.   | Multi-database replication.                       |
| **[Incremental Data Loading]**   | Loads only changed data into a data warehouse (e.g., via `MERGE` or staging tables).            | ETL/ELT pipelines.                               |

---
## **References**
- [Microsoft Docs: Change Data Capture Overview](https://docs.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-data-capture)
- [SQL Server CDC Functions](https://docs.microsoft.com/en-us/sql/relational-databases/track-changes/cdc-functions-transact-sql)
- [Debezium SQL Server Connector](https://debezium.io/documentation/reference/connectors/sqlserver.html) (for alternative CDC solutions).