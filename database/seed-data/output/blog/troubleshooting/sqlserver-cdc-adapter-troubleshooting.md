# Debugging **SQL Server CDC Adapter Pattern**: A Troubleshooting Guide

---

## **Introduction**
Change Data Capture (CDC) in SQL Server enables tracking row-level changes (inserts, updates, deletes) across a database, which is critical for real-time data replication, analytics, or event-driven architectures. The **SQL Server CDC Adapter Pattern** typically involves:
- Enabling CDC on SQL Server tables.
- Capturing changes via a CDC-enabled log stream.
- Reading CDC data using `sys.fn_cdc_get_net_changes` or `sys.fn_cdc_get_all_changes`.
- Parsing and forwarding changes to downstream systems (e.g., Kafka, Service Bus, or an application layer).

This guide focuses on **practical debugging** for common issues encountered in CDC pipelines.

---

## **1. Symptom Checklist**
Before diving into fixes, verify the following symptoms systematically:

| **Category**               | **Symptom**                                                                 | **Question to Ask**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **CDC Not Enabled**        | No changes captured after table modifications.                              | Is CDC enabled on the source table? (`SELECT * FROM sys.tables WHERE is_tracked_by_cdc = 1`) |
| **No Recent Changes**      | No output from `fn_cdc_get_net_changes` or `fn_cdc_get_all_changes`.        | Are there actual changes in the table? Check `CDC.dbo_ct` for entries.              |
| **Performance Issues**     | High CPU/memory usage or slow CDC reads.                                   | Are there large batches of changes being processed? Is CDC log retention too long? |
| **Adapter/Streaming Errors** | CDC data not reaching downstream systems (e.g., Kafka, Service Bus).      | Are there dead-letter queues (DLQ) or logging errors in the middleware?            |
| **Time Synchronization**   | CDC timestamps are out of sync with expected changes.                      | Is the server clock synchronized? Are `CT` (change timestamp) values logical?      |
| **Schema Mismatch**        | Parsing errors when reading CDC changes (e.g., column type mismatches).    | Does the downstream system expect the same schema as the CDC output?               |
| **Memory Pressure**        | `fn_cdc_get_net_changes` fails with "Insufficient memory" errors.          | Are CDC logs too large? Is the `max transactions in snapshot` setting optimized?   |

---
---

## **2. Common Issues and Fixes**

### **Issue 1: CDC Not Enabled on a Table**
**Symptom:**
No changes appear in `fn_cdc_get_net_changes`, even though data is modified.

**Root Cause:**
CDC must be manually enabled on each tracked table.

**Fix:**
Enable CDC for a table:
```sql
-- Enable CDC at database level (if not already enabled)
EXEC sys.sp_cdc_enable_db;

-- Enable CDC for a specific table
EXEC sys.sp_cdc_enable_table
    @source_schema = 'dbo',
    @source_name = 'YourTable',
    @role_name = NULL; -- Uses DEFAULT_CDC_ADMINS role
```
**Verification:**
```sql
-- Check if CDC is enabled for the table
SELECT * FROM sys.tables WHERE is_tracked_by_cdc = 1 AND name = 'YourTable';
```

**Common Pitfalls:**
- Forgetting to enable CDC at the **database level** (`sp_cdc_enable_db`).
- Not granting `CDC_ADMIN` permissions to the CDC user.

---

### **Issue 2: No Recent Changes in `fn_cdc_get_net_changes`**
**Symptom:**
No changes are returned despite actual table updates.

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     |
|-------------------------------------|---------------------------------------------------------------------------------------------|
| **Retention period too short**      | Increase `cdc_retention_in_minutes` (default: 1440 mins = 24h).                          |
| **CDS logs not flushed**            | Run `DBCC CDC FLUSH_WITH_NO_TOMBSTONE` to force a snapshot.                                |
| **No CDC-enabled user**             | Ensure the user running the query has `SELECT` on `dbo_ct` and `dbo_lsn`.                 |
| **Table not in `sys.tables`**       | Re-enable CDC for the table: `EXEC sp_cdc_enable_table`.                                   |

**Debugging Query:**
```sql
-- Check CDC status and last change
SELECT
    name AS table_name,
    is_tracked_by_cdc,
    cdc.lsn_captured,
    cdc.lsn_retention,
    cdc.lsn_current_time
FROM sys.tables t
JOIN sys.dm_cdc_tables cdc ON t.object_id = cdc.object_id
WHERE t.name = 'YourTable';
```

---

### **Issue 3: High CPU/Memory Usage by CDC**
**Symptom:**
`sqlserver.exe` consumes excessive CPU or memory when running CDC queries.

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     |
|-------------------------------------|---------------------------------------------------------------------------------------------|
| **Large CDC logs**                  | Reduce `cdc_retention_in_minutes` if logs are accumulating too quickly.                      |
| **Inefficient `fn_cdc_get_all_changes`** | Use `fn_cdc_get_net_changes` instead for incremental reads.                              |
| **Missing indexes**                 | Ensure CDC-generated columns (`__$start_lsn`, `__$end_lsn`, `__$operation`) are indexed.   |
| **Bulk operations**                 | Avoid loading large datasets with `SELECT *` from CDC tables.                              |

**Optimization:**
```sql
-- Use a smaller time window to reduce row count
DECLARE @since_lsn UNIQUEIDENTIFIER = sys.fn_cdc_get_min_lsn('dbo_YourTable');
DECLARE @until_lsn UNIQUEIDENTIFIER = sys.fn_cdc_get_net_changes_dbo_YourTable(@since_lsn, 'ALL');
-- Fetch changes with a time limit
SELECT * FROM
    cdc.fn_cdc_get_net_changes_dbo_YourTable(@since_lsn, @until_lsn, 'ALL')
OPTION (MAXDOP 1); -- Limit parallelism
```

---

### **Issue 4: CDC Data Not Reaching Downstream (e.g., Kafka)**
**Symptom:**
Changes are captured but not delivered to Kafka/Service Bus.

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     |
|-------------------------------------|---------------------------------------------------------------------------------------------|
| **Middleware misconfiguration**      | Check Kafka/Service Bus consumer logs for errors (e.g., schema mismatch).                 |
| **CDC adapter deadlocks**           | Use transactions with `SET XACT_ABORT ON` in the adapter code.                            |
| **Network timeouts**                | Increase `max_retries` or `retry_interval` in the adapter.                                |
| **Schema evolution**                | Ensure downstream systems handle CDC schema changes (e.g., `sys.fn_cdc_get_change_data` output). |

**Example Adapter Code (C#):**
```csharp
using (var connection = new SqlConnection(cdcConnectionString))
{
    connection.Open();
    var command = new SqlCommand(
        "SELECT * FROM cdc.fn_cdc_get_net_changes_dbo_YourTable(@since_lsn, @until_lsn, 'ALL')",
        connection
    );
    command.Parameters.AddWithValue("@since_lsn", sinceLsn);
    command.Parameters.AddWithValue("@until_lsn", untilLsn);

    using (var reader = command.ExecuteReader())
    {
        while (reader.Read())
        {
            try
            {
                // Map CDC row to message and send to Kafka
                var message = new
                {
                    Table = reader["__$start_lsn"].ToString(),
                    Operation = reader["__$operation"].ToString(),
                    Data = reader.GetSqlJson(0) // Use SqlJson for complex types
                };
                producer.Produce(topic, new Message<byte[], string> { Value = message });
            }
            catch (Exception ex)
            {
                // Log to DLQ
                DeadLetterQueue.Enqueue(ex, reader);
            }
        }
    }
}
```

**Debugging Steps:**
1. **Log raw CDC output** before processing:
   ```sql
   SELECT TOP 10 * FROM cdc.fn_cdc_get_net_changes_dbo_YourTable(NULL, NULL, 'ALL');
   ```
2. **Check middleware logs** for timeouts or schema errors.
3. **Monitor network latency** between SQL Server and the adapter.

---

### **Issue 5: Time Desynchronization in CDC**
**Symptom:**
`__$start_lsn` or `CT` (change timestamp) values appear out of order.

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     |
|-------------------------------------|---------------------------------------------------------------------------------------------|
| **Server clock drift**              | Sync SQL Server clock with domain time (`sp_configure 'clock tick', 1`).                    |
| **CDC log corruption**              | Restore from backup or re-enable CDC on the table.                                         |
| **Time zone mismatches**            | Ensure `CT` column is compared in the same timezone as the source.                          |

**Verification:**
```sql
-- Check if CDC logs are contiguous
SELECT
    MIN(lsn_captured) AS min_lsn,
    MAX(lsn_captured) AS max_lsn,
    DATEDIFF(minute, CAST(lsn_captured AS DATETIME), GETDATE()) AS time_since_last_change
FROM sys.dm_cdc_lsn_graph('YourDatabase');
```

---

### **Issue 6: Memory Errors in `fn_cdc_get_all_changes`**
**Symptom:**
`Out of memory` error when running `fn_cdc_get_all_changes`.

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     |
|-------------------------------------|---------------------------------------------------------------------------------------------|
| **No pagination**                   | Use `fn_cdc_get_net_changes` with `@since_lsn`/`@until_lsn` to fetch changes incrementally.|
| **Large CDC retention**             | Reduce `cdc_retention_in_minutes` (default: 1440 mins).                                    |
| **Missing indexes**                 | Add an index on `__$start_lsn` and `__$operation` columns.                               |

**Example Paginated Query:**
```sql
-- Fetch changes in batches
DECLARE @since_lsn UNIQUEIDENTIFIER = sys.fn_cdc_get_min_lsn('dbo_YourTable');
DECLARE @until_lsn UNIQUEIDENTIFIER;

WHILE @since_lsn IS NOT NULL
BEGIN
    SET @until_lsn = sys.fn_cdc_get_net_changes_dbo_YourTable(@since_lsn, 'ALL');

    INSERT INTO StagingTable
    SELECT * FROM cdc.fn_cdc_get_net_changes_dbo_YourTable(@since_lsn, @until_lsn, 'ALL');

    SET @since_lsn = @until_lsn; -- Get next batch
END
```

---

## **3. Debugging Tools and Techniques**
### **A. SQL Server Built-in Tools**
1. **`sys.dm_cdc_tables`**
   - Check CDC status for all tables.
   ```sql
   SELECT * FROM sys.dm_cdc_tables WHERE database_id = DB_ID();
   ```
2. **`sys.fn_cdc_event_trace_get_table`**
   - Inspect CDC events (requires trace flag 3604 activated).
   ```sql
   -- Enable tracing (run once)
   DBCC TRACEON(3604, -1);

   -- Check CDC events
   SELECT * FROM sys.fn_cdc_event_trace_get_table(DB_ID(), NULL, 1000000);
   ```
3. **`DBCC TRACEON(3604)`**
   - Logs CDC operations to the error log.

### **B. Extended Events (Advanced)**
Capture CDC-related events:
```sql
CREATE EVENT SESSION [CDC_Debug] ON SERVER
ADD EVENT sqlserver.cdc_event(
    ACTION(sqlserver.sql_text, sqlserver.lsn_current, sqlserver.database_id)
    WHERE database_id = DB_ID('YourDatabase'))
ADD TARGET package0.event_file(SET filename=N'CDC_Debug.xel');
ALTER EVENT SESSION [CDC_Debug] ON SERVER STATE = START;
GO
```
**Review logs** in `C:\Program Files\Microsoft SQL Server\MSSQL15.MSSQLSERVER\MSSQL\Log\CDC_Debug_*.xel`.

### **C. Application-Level Debugging**
1. **Logging CDC Output**
   - Log the raw CDC payload before processing:
     ```csharp
     var changes = command.ExecuteReader();
     while (changes.Read())
     {
         Debug.WriteLine(changes["__$start_lsn"].ToString() + " | " + changes["__$operation"]);
     }
     ```
2. **Dead-Letter Queue (DLQ)**
   - Implement a DLQ for failed records:
     ```sql
     CREATE TABLE CDC_DLQ (
         ErrorTime DATETIME,
         ErrorMessage NVARCHAR(MAX),
         CDCData XML -- Store raw CDC row
     );
     GO
     ```

### **D. Performance Profiling**
- Use **SQL Server Profiler** or **Extended Events** to monitor:
  - `fn_cdc_get_net_changes` execution time.
  - Blocking operations on `sys.tables` or `sys.dm_cdc_tables`.
- **Query Store** can track slow CDC queries:
  ```sql
  SELECT query_sql_text, execution_count, average_duration
  FROM sys.query_store_query_text AS qt
  JOIN sys.query_store_plan AS qp ON qt.query_text_id = qp.query_text_id
  JOIN sys.query_store_runtime_stats AS rs ON qp.plan_id = rs.plan_id
  WHERE qt.query_sql_text LIKE '%fn_cdc_get%'
  ORDER BY average_duration DESC;
  ```

---

## **4. Prevention Strategies**
### **A. Design Time**
1. **Enable CDC Early**
   - Enable CDC on tables **before** production data is loaded to avoid gaps.
2. **Use Staging Tables**
   - Store CDC data in a staging table before processing:
     ```sql
     CREATE TABLE CDC_Staging (
         LSN UNIQUEIDENTIFIER,
         TableName NVARCHAR(128),
         Operation NVARCHAR(1),
         Data XML
     );
     ```
3. **Schema Alignment**
   - Ensure downstream systems match the CDC output schema. Use `sys.fn_cdc_get_change_data` for dynamic columns.
4. **Monitor Retention**
   - Set `cdc_retention_in_minutes` to a reasonable value (e.g., 60 mins for near-real-time systems).

### **B. Runtime**
1. **Error Handling**
   - Implement retry logic with exponential backoff for transient failures:
     ```csharp
     private void ProcessCDCChanges(RetryPolicy retryPolicy)
     {
         var retryAttempt = 0;
         while (retryAttempt < retryPolicy.MaxAttempts)
         {
             try
             {
                 var changes = GetCDCChanges();
                 ProcessChanges(changes);
                 break;
             }
             catch (SqlException ex) when (ex.Number == 1205) // Lock timeout
             {
                 retryAttempt++;
                 Thread.Sleep(retryPolicy.BackoffFactor * retryAttempt);
             }
         }
     }
     ```
2. **Batch Processing**
   - Process CDC changes in batches to avoid memory issues:
     ```sql
     DECLARE @batch_size INT = 1000;
     DECLARE @since_lsn UNIQUEIDENTIFIER = NULL;
     DECLARE @until_lsn UNIQUEIDENTIFIER;

     WHILE 1 = 1
     BEGIN
         SET @until_lsn = sys.fn_cdc_get_net_changes_dbo_YourTable(@since_lsn, 'ALL');
         IF @until_lsn IS NULL BREAK;

         -- Process up to @batch_size rows
         INSERT INTO DownstreamTable
         SELECT TOP (@batch_size) *
         FROM cdc.fn_cdc_get_net_changes_dbo_YourTable(@since_lsn, @until_lsn, 'ALL')
         OPTION (MAXDOP 1);

         SET @since_lsn = @until_lsn;
     END
     ```
3. **Health Checks**
   - Monitor CDC health with a heartbeat query:
     ```sql
     CREATE PROCEDURE usp_CheckCDCHealth
     AS
     BEGIN
         IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE is_tracked_by_cdc = 1)
             RAISERROR('No CDC-enabled tables!', 16, 1);

         IF NOT EXISTS (SELECT 1 FROM sys.dm_cdc_tables WHERE is_tracked_by_cdc = 1)
             RAISERROR('CDC not enabled at database level!', 16, 1);
     END;
     GO
     ```
   - Schedule this via **SQL Agent** or **PowerShell**.

### **C. Backup and Recovery**
1. **CDC Log Backups**
   - Regularly back up CDC logs to prevent corruption:
     ```sql
     -- Backup CDC logs (run during low-traffic periods)
     BACKUP DATABASE YourDatabase TO DISK = 'C:\Backups\CDCLog.bak'
     WITH LOG, INIT, STATS = 10;
     ```
2. **Restore Test Plan**
   - Document steps to restore CDC logs from backup:
     ```sql
     -- Restore CDC logs (use WITH MOVE to point to new paths)
     RESTORE DATABASE YourDatabase
     FROM DISK = 'C:\Backups\CDCLog.bak'
     WITH FILE = 1, MOVE 'YourDatabase_Data' TO 'C:\Data\YourDatabase.mdf',
                MOVE 'YourDatabase_Log' TO 'C:\Log\YourDatabase.ldf',
                NORECOVERY;
     ```

---

## **5. Summary Checklist for Rapid Resolution**
| **Step**                          | **Action**                                                                                     |
|-----------------------------------|------------------------------------------------------------------------------------------------|
| **Verify CDC is enabled**         | Check `sys.tables` for `is_tracked_by_cdc = 1`.                                               |
| **Check for recent changes**      | Run `fn_cdc_get_net_changes` with `@since_lsn = NULL`.                                        |
| **Inspect retention settings**     | Adjust `cdc_retention_in_minutes` if logs are too large.                                      |
| **Monitor server health**         | Check for memory/CPU pressure on SQL Server.                                                  |
| **Validate downstream delivery**   | Log CDC output and middleware errors.                                                          |
| **Time synchronization**           | Ensure server clock is accurate.                                                               |
| **Optimize queries**              | Use pagination (`fn_cdc_get_net_changes`) instead of `fn_cdc_get_all_changes`.