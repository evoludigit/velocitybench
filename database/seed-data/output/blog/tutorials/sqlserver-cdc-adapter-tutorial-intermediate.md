```markdown
---
title: "SQL Server CDC Adapter Pattern: Real-Time Data Sync Made Simple"
date: "2023-11-15"
tags: ["database", "sql-server", "change-data-capture", "patterns", "real-time"]
author: "Alex Knight"
---

# **SQL Server CDC Adapter Pattern: Real-Time Data Sync Made Simple**

Change Data Capture (CDC) in SQL Server is a powerful tool for tracking database changes, but exposing it to application logic often feels like wrestling with a tangled web of low-level APIs. The **SQL Server CDC Adapter Pattern** helps bridge this gap by encapsulating CDC logic into reusable, maintainable components that your services can consume cleanly.

In this post, we’ll explore how to build a **CDC adapter layer** that abstracts the complexity of SQL Server’s CDC system, allowing your backend services to subscribe to database changes effortlessly. We’ll cover the problem, solution architecture, code examples, and pitfalls to avoid. Let’s dive in!

---

## **Introduction: The Challenge of CDC in SQL Server**

SQL Server’s Change Data Capture (CDC) provides a built-in mechanism to track INSERTs, UPDATEs, and DELETEs across database tables. It’s a game-changer for real-time applications—think event-driven architectures, data replication, or even maintaining secondary indexes.

But here’s the catch: **SQL Server’s CDC APIs are procedural and low-level**. If you’re building a service that needs to react to changes (e.g., updating a cache, triggering notifications, or syncing with another system), you’ll often end up writing boilerplate SQL queries, parsing JSON payloads (`__$start_lsn`, `__$end_lsn`, etc.), and managing LSN (Log Sequence Number) cursors manually. This quickly becomes messy, hard to debug, and coupled to the database.

This is where the **CDC Adapter Pattern** shines. By abstracting the CDC-specific details into a clean interface, you can:

- **Decouple** application logic from database internals.
- **Reuse** CDC logic across multiple services.
- **Easily swap** CDC implementations (e.g., switching from SQL Server to PostgreSQL CDC).
- **Add resilience** with retries, dead-letter queues, and batching.

---

## **The Problem: Why CDC Feels Like a Chore**

Let’s say you’re building a **real-time analytics dashboard** that needs to react to changes in a `Sales` table. Without an adapter, your code might look like this (in C#):

```csharp
public class SalesChangeListener
{
    private SqlConnection _connection;

    public SalesChangeListener(string connectionString)
    {
        _connection = new SqlConnection(connectionString);
        _connection.Open();
    }

    public async Task ProcessChanges()
    {
        using var cmd = new SqlCommand(
            @"SELECT s.*, c.__$start_lsn, c.__$operation
             FROM Sales s
             CROSS APPLY dbo.fn_cdc_get_net_changes_cdc('Sales', 2, NULL, NULL)",
            _connection);

        using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            string operation = reader["__$operation"].ToString();
            var salesRecord = new SalesRecord
            {
                Id = reader["Id"].ToString(),
                Amount = Convert.ToDecimal(reader["Amount"])
            };

            // Forward to analytics service or cache
            if (operation == "INSERT")
                await AnalyticsService.LogNewSale(salesRecord);
            else if (operation == "DELETE")
                await AnalyticsService.RemoveSale(salesRecord.Id);
        }
    }
}
```

**Problems with this approach:**
1. **Tight coupling**: The code knows too much about CDC internals (`fn_cdc_get_net_changes`, `__$operation`).
2. **Error-prone**: Parsing JSON or handling LSN cursors incorrectly can break change tracking.
3. **Scalability**: Managing connections, retries, and backpressure is manual.
4. **Hard to test**: Mocking the CDC stream is cumbersome.

This is where the **CDC Adapter Pattern** helps.

---

## **The Solution: The CDC Adapter Pattern**

The **SQL Server CDC Adapter Pattern** introduces an abstraction layer between your application and the CDC system. Your code interacts with a **high-level interface** (e.g., `ICdcStream<T>`), while the adapter handles:
- Connection management.
- LSN tracking and cursor cleanup.
- Change deserialization.
- Retries and backpressure.

### **Core Components**
| Component               | Responsibility                                                                 |
|-------------------------|-------------------------------------------------------------------------------|
| `ICdcStream<T>`          | Defines a contract for consuming CDC changes (e.g., `GetChangesAsync`).      |
| `SqlServerCdcAdapter`   | Implements `ICdcStream<T>` using SQL Server’s CDC functions.                  |
| `ChangeHandler<T>`       | Decouples change processing logic (e.g., `OnInsert`, `OnUpdate`).             |
| `ChangeBatchProcessor`  | Handles batching, retries, and error handling for individual records.       |

---

## **Implementation Guide**

### **Step 1: Define the CDC Interface**
First, create a clean interface for your application to consume CDC changes:

```csharp
public interface ICdcStream<TEntity>
{
    Task<IEnumerable<TEntity>> GetChangesAsync(
        DateTime? since = null,
        int batchSize = 100,
        CancellationToken ct = default);
}
```

### **Step 2: Implement the SQL Server Adapter**
The adapter translates CDC-specific operations into the interface. Here’s a full implementation for SQL Server:

```csharp
public class SqlServerCdcAdapter<TEntity> : ICdcStream<TEntity>
    where TEntity : class
{
    private readonly string _connectionString;
    private readonly Func<SqlDataReader, TEntity> _deserializer;
    private readonly string _cdcSchemaName = "[dbo]";
    private readonly string _cdcTableName;

    public SqlServerCdcAdapter(
        string connectionString,
        string tableName,
        Func<SqlDataReader, TEntity> deserializer)
    {
        _connectionString = connectionString;
        _cdcTableName = tableName;
        _deserializer = deserializer;
    }

    public async Task<IEnumerable<TEntity>> GetChangesAsync(
        DateTime? since = null,
        int batchSize = 100,
        CancellationToken ct = default)
    {
        var changes = new List<TEntity>();
        using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(ct);

        // Get latest LSN or use a default if none provided
        var startLsn = since.HasValue ? GetLsnForTimestamp(since.Value) : null;
        var endLsn = null as string; // Optional: Use null to track all changes

        using var cmd = new SqlCommand(
            $@"
            SELECT c.*
            FROM {_cdcSchemaName}.{_cdcTableName}_CT c
            WHERE c.__$start_lsn > {GetCdcLsnParameter(startLsn)}
            ORDER BY c.__$start_lsn",
            connection);

        // Add parameters for LSN filtering
        if (startLsn != null)
            cmd.Parameters.AddWithValue("@startLsn", startLsn);

        using var reader = await cmd.ExecuteReaderAsync(CommandBehavior.SequentialAccess, ct);
        while (await reader.ReadAsync(ct))
        {
            changes.Add(_deserializer(reader));
            if (changes.Count >= batchSize)
                break;
        }

        return changes;
    }

    private string GetLsnForTimestamp(DateTime timestamp)
    {
        // Helper to convert a timestamp to LSN (simplified; use fn_cdc_map_time_to_lsn in production)
        return "0x0000000000000000"; // Placeholder
    }

    private SqlParameter GetCdcLsnParameter(string? lsn)
    {
        var param = new SqlParameter("@startLsn", SqlDbType.VarBinary);
        param.Value = lsn ?? DBNull.Value;
        return param;
    }
}
```

### **Step 3: Define Change Handlers**
Decouple the CDC processing from business logic using a handler:

```csharp
public class SalesChangeHandler
{
    public async Task OnInsert(SalesRecord sales)
    {
        await AnalyticsService.LogNewSale(sales);
    }

    public async Task OnUpdate(SalesRecord sales, SalesRecord previous)
    {
        await AnalyticsService.UpdateSale(sales, previous);
    }

    public async Task OnDelete(SalesRecord sales)
    {
        await AnalyticsService.RemoveSale(sales.Id);
    }
}
```

### **Step 4: Assemble the Pipeline**
Now, tie everything together with a `ChangeBatchProcessor`:

```csharp
public class ChangeBatchProcessor
{
    private readonly ICdcStream<SalesRecord> _cdcStream;
    private readonly SalesChangeHandler _handler;

    public ChangeBatchProcessor(ICdcStream<SalesRecord> cdcStream, SalesChangeHandler handler)
    {
        _cdcStream = cdcStream;
        _handler = handler;
    }

    public async Task ProcessChangesAsync(
        DateTime? since = null,
        int batchSize = 100,
        CancellationToken ct = default)
    {
        var changes = await _cdcStream.GetChangesAsync(since, batchSize, ct);

        foreach (var change in changes)
        {
            // In a real app, you’d track the operation type (INSERT/UPDATE/DELETE)
            await _handler.OnInsert(change);
        }
    }
}
```

### **Step 5: Set Up CDC on SQL Server**
Before running this, ensure CDC is enabled on your table:

```sql
-- Enable CDC on SQL Server (once per database)
EXEC sys.sp_cdc_enable_db;
EXEC sys.sp_cdc_enable_table
    @source_schema = 'dbo',
    @source_name = 'Sales',
    @role_name = NULL,
    @supports_net_changes = 1;
```

### **Step 6: Usage Example**
Now, your application can consume CDC changes cleanly:

```csharp
var adapter = new SqlServerCdcAdapter<SalesRecord>(
    "Server=.;Database=YourDb;Integrated Security=true",
    "Sales",
    (reader) => new SalesRecord
    {
        Id = reader["Id"].ToString(),
        Amount = Convert.ToDecimal(reader["Amount"]),
        Product = reader["Product"].ToString()
    });

var handler = new SalesChangeHandler();
var processor = new ChangeBatchProcessor(adapter, handler);

await processor.ProcessChangesAsync();
```

---

## **Common Mistakes to Avoid**

1. **Ignoring LSN Tracking**
   - If you don’t track the latest LSN (`__$start_lsn`), you’ll reprocess the same changes repeatedly. Store the LSN in your app or use a separate tracking table.

2. **Not Handling Connection Resilience**
   - Database connections can fail. Implement retries with exponential backoff.

3. **Batching Too Aggressively**
   - If your batch size is too large, you risk memory issues. Start with `batchSize = 100` and adjust.

4. **Assuming CDC is Transactional**
   - CDC tracks log changes, not necessarily database transactions. A single transaction could generate multiple CDC records.

5. **Forgetting to Clean Up**
   - If you use `fn_cdc_get_net_changes`, ensure you mark changes as processed (e.g., with `fn_cdc_cleanup_changes_table`).

6. **Not Testing Edge Cases**
   - Test with:
     - Empty batches.
     - Malformed records.
     - Connections that time out.

---

## **Key Takeaways**

✅ **Decouple** your app from CDC specifics using interfaces.
✅ **Reuse** the adapter across multiple services.
✅ **Handle errors gracefully** with retries and dead-letter queues.
✅ **Start small**—begin with a single table, then expand.
✅ **Monitor performance**—CDC can be resource-intensive for high-volume tables.
✅ **Consider alternatives** like SQL Server’s `CHANGE TABLE` or CDC with Kafka for distributed systems.

---

## **Conclusion: A Cleaner Path to Real-Time Data**

SQL Server’s CDC is powerful, but its raw APIs can quickly turn into spaghetti code. The **CDC Adapter Pattern** provides a clean, maintainable way to consume CDC changes without sacrificing flexibility.

By abstracting the low-level details, you:
- Reduce boilerplate.
- Improve testability.
- Future-proof your code for CDC migrations.

Now, you can focus on **business logic** instead of wrestling with LSN cursors. Try it out, and let me know how it works for your use case!

---
**Further Reading:**
- [SQL Server CDC Documentation](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/change-data-capture)
- [Event Sourcing with CDC](https://datasystemsdesign.com/patterns/event-sourcing/)
```

---

### **Why This Approach Works**
This pattern is **practical**—you can start small and iterate. It’s **scalable**—add more tables or services without rewriting the adapter. And it’s **real-world tested**—many enterprise systems use variations of this pattern.

Got questions or feedback? Drop them in the comments!