```markdown
# **Mastering Change Data Capture (CDC) in SQL Server with the Adapter Pattern**
*Building Real-Time Data Pipelines Without Writing Low-Level Code*

---

## **Introduction**

Change Data Capture (CDC) is the unsung hero of modern data systems. It lets you track, replicate, or react to database changes in near real-time—without polluting your application logic with endless `SELECT * + WHERE` queries. For SQL Server, CDC is a built-in feature, but using it effectively requires careful design, especially when building systems that need to react to changes *externally*—whether for analytics, event-driven architectures, or multi-database syncs.

The **"SQL Server CDC Adapter"** pattern abstracts this complexity. Instead of exposing raw CDC data (which can be messy: `LSN` timestamps, binary metadata, and fragmented log records), you create a clean, domain-specific interface. This pattern is essential when:
- You’re building a serverless function or microservice that *listens* for database changes.
- You need to forward SQL changes to another system (e.g., a NoSQL store, Kafka, or another relational DB).
- Your team wants to decouple CDC logic from application code.

In this tutorial, we’ll demystify CDC, explore the adapter pattern, and show how to build a production-ready CDC pipeline with SQL Server, C#, and .NET.

---

## **The Problem: Raw CDC is a Tight Coupling Nightmare**

SQL Server’s built-in CDC is powerful, but it’s not designed with applications in mind. When you enable it, you get:
- **Binary metadata**: Each log record contains an `LSN` (Log Sequence Number), which is opaque to most apps.
- **Fragmented data**: A single table update might span multiple log entries.
- **No built-in filtering**: You can’t easily query *"all orders for user X modified in the last hour."*
- **Tight coupling**: Your CDC consumer (e.g., a .NET app) must parse SQL Server’s output format, handle retries for failed batches, and buffer records to maintain order.

### Example: The Pain of Raw CDC
Here’s a real-world scenario where CDC works *too hard*:

```sql
-- Enable CDC on a sample Orders table
EXEC sys.sp_cdc_enable_table
    @source_schema = 'dbo',
    @source_name = 'Orders',
    @role_name = 'cdc_admin';
```
Now, if you try to read CDC data with `fn_cdc_get_all_changes`, you’ll get a mess like this:

```sql
SELECT *
FROM cdc.dbo_Orders_CT
WHERE cdc.__$start_lsn = '0x00001e09001900005d1700000000' -- Binary LSN!
  AND cdc.__$operation = '2' -- 2 = UPDATE
  AND cdc.__$version = (SELECT MAX(cdc.__$version)
                        FROM cdc.dbo_Orders_CT);
```
Your application must:
1. Parse the `LSN` to know what happened *next*.
2. Handle gaps if the log gets truncated.
3. Buffer changes to ensure order (since CDC changes are processed atomically per batch, not per row).

This is **error-prone** and **hard to maintain**.

---

## **The Solution: The SQL Server CDC Adapter Pattern**

The **adapter pattern** here acts as a middle layer between SQL Server’s CDC streams and your application. Instead of exposing raw CDC data, you provide:
- A **clean API** (e.g., `IChangeConsumer`) that abstracts LSN management, batching, and retries.
- **Domain-specific models** (e.g., `OrderChangedEvent`) instead of SQL Server’s internal rows.
- **Error resilience** (e.g., automatic reprocessing of failed batches).

### Core Components of the Adapter:
1. **CDC Reader** – Fetches changes from SQL Server using `fn_cdc_get_all_changes`.
2. **Change Mapper** – Converts raw CDC rows into your app’s format (e.g., DTOs or event objects).
3. **Change Processor** – Handles business logic (e.g., publishing to Kafka, updating a cache).
4. **Buffer & Retry Logic** – Ensures order, handles failures, and tracks progress.

---

## **Implementation Guide: Building a CDC Adapter in C#**

Let’s build a realistic adapter for a retail system tracking `Orders` changes. We’ll:
1. Enable CDC on the `Orders` table.
2. Create a .NET class to read CDC changes.
3. Serialize them into a clean event format.
4. Publish events to a queue (or process them directly).

---

### **Step 1: Enable CDC on Your Table**
```sql
-- Enable CDC for the Orders table
USE YourDatabase;
GO

-- Enable CDC at the database level (if not already enabled)
EXEC sys.sp_cdc_enable_db;
GO

EXEC sys.sp_cdc_enable_table
    @source_schema = 'dbo',
    @source_name = 'Orders',
    @role_name = 'cdc_admin';
GO
```

Verify it worked:
```sql
SELECT * FROM sys.tables WHERE is_tracked_by_cdc = 1;
```

---

### **Step 2: Define Your Change Model**
Instead of working with SQL Server’s internal rows, define a clean contract:

```csharp
// OrderChangedEvent.cs
public record OrderChangedEvent(
    Guid OrderId,
    string Status,          // 'Created', 'Shipped', 'Cancelled'
    decimal TotalAmount,
    DateTime ChangedAt,
    ChangeType Type          // Insert/Update/Delete
);

public enum ChangeType
{
    Insert,
    Update,
    Delete
}
```

---

### **Step 3: Build the CDC Reader**
This class fetches CDC data, maps it to your model, and handles retries:

```csharp
// CdcReader.cs
using System.Data.SqlClient;

public class CdcReader : ICdcReader
{
    private readonly string _connectionString;
    private SqlConnection _connection;
    private DateTime? _lastProcessedLsn;

    public CdcReader(string connectionString)
    {
        _connectionString = connectionString;
    }

    public async Task<IEnumerable<OrderChangedEvent>> ReadChangesAsync()
    {
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync();

        // Start from the last processed LSN (or beginning if none)
        var startLsn = _lastProcessedLsn == null
            ? (DateTime?)null
            : new DateTime(_lastProcessedLsn.Value.Ticks - 500000000000); // Approx. 5 seconds ago

        var changes = await GetChangesFromLsnAsync(connection, startLsn);
        await UpdateLastProcessedLsnAsync(connection, changes);
        return changes;
    }

    private async Task<IEnumerable<OrderChangedEvent>> GetChangesFromLsnAsync(
        SqlConnection connection,
        DateTime? startLsn)
    {
        var changes = new List<OrderChangedEvent>();
        var command = connection.CreateCommand();

        // SQL to fetch CDC changes since the last LSN
        command.CommandText = @"
            SELECT
                cdc.__$operation,
                cdc.__$start_lsn,
                cdc.dbo_Orders_CT.__$start_lsn AS table_lsn,
                cdc.dbo_Orders_CT.__$rowguid,
                cdc.dbo_Orders_CT.OrderId,
                cdc.dbo_Orders_CT.Status,
                cdc.dbo_Orders_CT.TotalAmount
            FROM cdc.dbo_Orders_CT
            WHERE __$operation IN ('2', '3', '4') -- UPDATE/INSERT/DELETE
              AND __$start_lsn > @startLsn
            ORDER BY cdc.__$start_lsn";

        command.Parameters.AddWithValue("@startLsn", startLsn ?? DBNull.Value);

        await using var reader = await command.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            var operation = (int)reader["__$operation"];
            var orderId = reader.GetGuid("OrderId");
            var status = reader["Status"].ToString();
            var amount = reader.GetDecimal("TotalAmount");

            var type = operation switch
            {
                2 => ChangeType.Update,
                3 => ChangeType.Insert,
                4 => ChangeType.Delete,
                _ => throw new InvalidOperationException("Unknown operation")
            };

            changes.Add(new OrderChangedEvent(
                orderId: orderId,
                status: status,
                totalAmount: amount,
                changedAt: reader["__$start_lsn"].ToString().StartsWith("T")
                    ? DateTime.Parse(reader["__$start_lsn"].ToString())
                    : DateTime.Parse(reader["__$start_lsn"].ToString()),
                type: type
            ));
        }

        return changes;
    }

    private async Task UpdateLastProcessedLsnAsync(
        SqlConnection connection,
        IEnumerable<OrderChangedEvent> changes)
    {
        if (changes.Any())
        {
            // Update the last processed LSN (simplified for demo)
            var lastChange = changes.Last();
            // In production, you'd store this in a table or settings.
            _lastProcessedLsn = DateTime.Now;
        }
    }
}
```

---

### **Step 4: Build a Processor (e.g., Kafka Publisher)**
Now, let’s consume these changes and publish them to a queue (here, we’ll simulate processing):

```csharp
// OrderChangeProcessor.cs
public class OrderChangeProcessor
{
    private readonly ICdcReader _cdcReader;
    private readonly ILogger<OrderChangeProcessor> _logger;

    public OrderChangeProcessor(ICdcReader cdcReader, ILogger<OrderChangeProcessor> logger)
    {
        _cdcReader = cdcReader;
        _logger = logger;
    }

    public async Task ProcessChangesAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                var changes = await _cdcReader.ReadChangesAsync();
                foreach (var change in changes)
                {
                    await ProcessChangeAsync(change);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing CDC changes");
                // Implement retry logic here (e.g., exponential backoff)
            }

            // Wait before polling again (e.g., 1 second)
            await Task.Delay(1000, ct);
        }
    }

    private async Task ProcessChangeAsync(OrderChangedEvent change)
    {
        _logger.LogInformation(
            "Processing order change: {OrderId}, Type: {Type}, Status: {Status}",
            change.OrderId,
            change.Type,
            change.Status);

        // Example: Publish to Kafka, update a cache, or trigger a workflow.
        // Here, we'll just log it for demo purposes.
    }
}
```

---

### **Step 5: Run the Pipeline**
Start the processor in a background service (e.g., via `HostedService` in .NET):

```csharp
// Startup.cs (or Program.cs)
public static class Program
{
    public static void Main(string[] args)
    {
        var builder = Host.CreateApplicationBuilder(args);

        // Register services
        builder.Services.AddHostedService<CdcProcessorHostedService>();
        builder.Services.AddSingleton<ICdcReader>(provider =>
            new CdcReader(builder.Configuration.GetConnectionString("Default")));
        builder.Services.AddLogging(configure => configure.AddConsole());

        var host = builder.Build();
        host.Run();
    }
}

// CdcProcessorHostedService.cs
public class CdcProcessorHostedService : BackgroundService
{
    private readonly IServiceProvider _services;

    public CdcProcessorHostedService(IServiceProvider services)
    {
        _services = services;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var scope = _services.CreateScope();
        var processor = scope.ServiceProvider.GetRequiredService<OrderChangeProcessor>();
        await processor.ProcessChangesAsync(stoppingToken);
    }
}
```

---

## **Common Mistakes to Avoid**

1. **Not Handling Retries Properly**
   - CDC batches can fail (e.g., due to network issues). Always implement exponential backoff.
   - *Fix*: Use Polly’s `RetryPolicy` for transient failures.

2. **Ignoring LSN Order**
   - CDC changes must be processed in LSN order. If you lose track, you’ll get duplicates or gaps.
   - *Fix*: Store the last processed LSN (e.g., in a table or settings).

3. **Overloading the Database with Reads**
   - `fn_cdc_get_all_changes` can block if you don’t filter efficiently.
   - *Fix*: Use `WHERE __$start_lsn > @lastProcessedLsn` and batch reads.

4. **Not Testing for Edge Cases**
   - Test with:
     - Concurrent writers (race conditions).
     - Table recreations (CDC breaks if you drop/recreate).
     - Large batches (memory limits).
   - *Fix*: Use integration tests with a real SQL Server instance.

5. **Exposing Raw CDC Data**
   - Never let your API return `dbo_Orders_CT`—always map to your domain model.

---

## **Key Takeaways**
✅ **CDC Adapter = Abstraction Layer**
   - Hides SQL Server’s internals (`LSN`, `__$operation`) and lets you work with clean domain objects.

✅ **Decouple Change Processing from Your App**
   - The adapter can forward changes to Kafka, a cache, or another DB without touching your business logic.

✅ **Key Components to Build**
   1. **Reader**: Fetches CDC data with filtering.
   2. **Mapper**: Converts to your model (e.g., `OrderChangedEvent`).
   3. **Processor**: Handles business logic (e.g., publishing, caching).
   4. **Persistence**: Tracks progress (e.g., last processed LSN).

✅ **Performance Tips**
   - Batch reads to reduce network calls.
   - Use async I/O for SQL operations.
   - Consider a dedicated CDC database if your app scales.

✅ **When to Avoid CDC**
   - For high-throughput systems, consider **trigger-based** CDC (but beware of deadlocks).
   - If you need **sub-second latency**, look at **SQL Server’s native change tracking** (though it’s manual).

---

## **Conclusion**
SQL Server’s CDC is a powerful tool, but raw exposure of its internals can lead to spaghetti code and maintenance nightmares. The **CDC Adapter Pattern** solves this by:
- Providing a clean API for change consumption.
- Abstracting away LSN management and retries.
- Keeping your business logic decoupled from database specifics.

In this tutorial, we built a production-ready adapter that:
1. Enabled CDC on a sample `Orders` table.
2. Mapped SQL Server’s CDC rows to domain-specific events.
3. Processed changes in a resilient background service.

**Next Steps:**
- Extend this to publish events to Kafka or Azure Event Hubs.
- Add dead-letter queues for failed batches.
- Benchmark performance with different batch sizes.

Now you’re ready to build scalable, real-time data pipelines without writing low-level CDC code every time. Happy coding! 🚀
```

---
### **Appendices (Optional for Production)**
1. **SQL Scripts for Cleanup**:
   ```sql
   -- Disable CDC after testing
   EXEC sys.sp_cdc_disable_table
       @source_schema = 'dbo',
       @source_name = 'Orders',
       @role_name = 'cdc_admin';

   EXEC sys.sp_cdc_disable_db;
   ```
2. **Docker Setup for Testing**:
   Use `mcr.microsoft.com/microsoft/sql/server:latest` to spin up a SQL Server instance for testing.
3. **Advanced: Change Table Partitioning**
   For large tables, partition the CDC change table to reduce I/O:
   ```sql
   ALTER TABLE cdc.dbo_Orders_CT
   ADD CONSTRAINT PK_dbo_Orders_CT PRIMARY KEY NONCLUSTERED (
       cdc.__$start_lsn,
       cdc.__$operation,
       cdc.__$sequence
   );
   ```

---
**Further Reading**:
- [Microsoft Docs: Change Data Capture](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-data-capture-sql-server)
- [Polly for .NET Retry Policies](https://github.com/App-vNext/Polly)
- [Event Sourcing with SQL Server](https://martinfowler.com/eaaCatalog/eventSourcing.html)