# **[Pattern] Index Strategy for Compiled Queries: Reference Guide**

---

## **Overview**
The **Index Strategy for Compiled Queries** pattern optimizes performance for deterministic, frequently executed queries by leveraging compiled query plans and strategically designed indexes. This pattern is ideal for scenarios where queries follow predictable patterns (e.g., reporting, analytics, or business logic with fixed parameters).

By combining **compilation** (avoiding repeated query plan generation) with **indexing** (reducing I/O overhead), this approach minimizes runtime execution time and resource consumption. It’s particularly effective in **OLTP and OLAP workloads** where query consistency is critical.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Compiled Query**        | A pre-generated execution plan for a deterministic query, avoiding repeated parsing and optimization at runtime.                                                   |
| **Deterministic Query**   | A query whose results depend only on input parameters, not execution context (e.g., fixed joins, no procedural logic).                                         |
| **Index-Interference**    | When indexes slow down writes (e.g., `INSERT/UPDATE`) due to excessive overhead. Mitigated by careful index selection.                                            |
| **Compilation Cache**     | A storage mechanism (e.g., SQL Server’s `Plan Cache`, Entity Framework’s `CompiledQuery` cache) that stores compiled plans for reuse.                        |
| **Partial Indexing**      | Indexing only a subset of rows to reduce storage and maintenance costs (e.g., filtering on `ActiveFlag = true`).                                                    |

---

## **Implementation Details**

### **When to Apply This Pattern**
Use this pattern when:
- Queries are **repeated frequently** (e.g., daily reports).
- Queries are **deterministic** (same input → same output).
- The **query plan is expensive to generate** (e.g., complex joins, aggregations).
- **Read-heavy workloads** dominate (write performance can tolerate slight degradations).

### **Trade-offs**
| **Pros**                          | **Cons**                                                                 |
|-----------------------------------|---------------------------------------------------------------------------|
| Reduced query latency.           | Higher storage overhead for indexes.                                     |
| Consistent performance.          | Potential write bottlenecks if indexes are overused.                     |
| Easier maintenance (no ad-hoc SQL).| Index tuning required for dynamic workloads.                             |

---

## **Schema Reference**
Below are example tables and recommended indexes for a **SalesOrder** system.

| **Table**          | **Key Columns**               | **Recommended Indexes**                                                                 |
|--------------------|-------------------------------|----------------------------------------------------------------------------------------|
| `SalesOrder`       | `OrderId (PK)`, `CustomerId`, `OrderDate`, `Status` | `IX_SalesOrder_CustomerId` (clustered), `IX_SalesOrder_DateStatus` (nonclustered) |
| `Customer`         | `CustomerId (PK)`, `Name`, `Region` | `IX_Customer_Region` (nonclustered)                                                     |
| `OrderItem`        | `OrderItemId (PK)`, `OrderId (FK)`, `ProductId (FK)`, `Quantity` | `IX_OrderItem_OrderId_ProductId` (composite)                                          |

### **Index Strategy Breakdown**
1. **Clustered Index on `SalesOrder(OrderId)`**
   - Default primary key; ensures fast lookups for individual orders.
2. **Nonclustered Index on `SalesOrder(CustomerId, OrderDate, Status)`**
   - Accelerates queries filtering by customer or date ranges.
3. **Composite Index on `OrderItem(OrderId, ProductId)`**
   - Speeds up joins between `SalesOrder` and `OrderItem` tables.

---
## **Query Examples**

### **1. Compiled Query with Indexing (Entity Framework Core)**
```csharp
// Define a compiled query for a deterministic sales report.
public static readonly Func<DbContext, int, DateTime, IEnumerable<SalesOrder>> GetOrdersByCustomer =
    CompiledQuery.Compile((DbContext ctx, int customerId, DateTime startDate) =>
        ctx.SalesOrders
            .Where(o => o.CustomerId == customerId && o.OrderDate >= startDate)
            .OrderBy(o => o.OrderDate));

// Usage:
var orders = GetOrdersByCustomer.Invoke(context, 123, new DateTime(2023, 1, 1));
```
**Why it works:**
- The index `IX_SalesOrder_CustomerId` (covering `CustomerId` and `OrderDate`) avoids table scans.
- Compilation ensures the plan is generated once.

---

### **2. SQL Server Compiled Query with Index Hint**
```sql
-- Create a deterministic stored procedure with an index hint.
CREATE PROCEDURE dbo.GetActiveOrders
    @CustomerId INT,
    @Region VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT o.*
    FROM SalesOrder o WITH (INDEX(IX_SalesOrder_CustomerId))
    INNER JOIN Customer c ON o.CustomerId = c.CustomerId
    WHERE o.CustomerId = @CustomerId AND c.Region = @Region AND o.Status = 'Active';
END;
```
**Key Optimizations:**
- `WITH (INDEX(...))` forces the optimizer to use the pre-defined index.
- The `Region` filter leverages `IX_Customer_Region`.

---

### **3. Partial Index for Active Orders Only**
```sql
-- Create a filtered index for active orders.
CREATE INDEX IX_SalesOrder_ActiveCustomer ON SalesOrder(CustomerId)
WHERE Status = 'Active';
```
**Use Case:**
- Reduces index size by 80% if only 20% of orders are "Active."
- Speeds up queries like `WHERE Status = 'Active' AND CustomerId = X`.

---

## **Performance Considerations**
| **Scenario**               | **Recommendation**                                                                 |
|----------------------------|------------------------------------------------------------------------------------|
| **High Write Volatility**  | Avoid over-indexing; consider partial indexes.                                     |
| **Dynamic Parameters**     | Use indexed views or materialized views for complex filters.                       |
| **Query Plan Regression**  | Monitor with `sp_BlitzFirst` or `DMVs`; update indexes periodically.               |
| **Concurrency Issues**     | Use `WITH (UPGRADABLE)` hints if row locks are critical.                            |

---

## **Related Patterns**
1. **[Indexing Strategy for Read-Heavy Workloads]** – General index design principles.
2. **[Compiled Query Pattern]** – Advanced caching for non-deterministic queries.
3. **[Indexed View]** – Pre-compute aggregations for complex reports.
4. **[Partial Indexing]** – Filter indexes for specific data subsets.
5. **[Query Store]** – Track and optimize query performance over time.

---
## **Further Reading**
- **SQL Server**: [`CREATE INDEX`](https://docs.microsoft.com/en-us/sql/t-sql/statements/create-index-transact-sql) (Filtered Indexes)
- **Entity Framework**: [Compiled Queries](https://docs.microsoft.com/en-us/ef/core/miscellaneous/compiled-queries)
- **Books**: *SQL Server Performance Tuning* (Grant Fritchey) – Covering index strategies.

---
**Last Updated:** [Insert Date]
**Version:** 1.0