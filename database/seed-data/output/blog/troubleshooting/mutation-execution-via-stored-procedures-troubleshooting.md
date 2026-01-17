# **Debugging "Mutation Execution via Stored Procedures": A Troubleshooting Guide**

## **1. Introduction**
Storing mutation logic in database stored procedures (SPs) can improve security, performance, and consistency by centralizing business rules. However, this approach can introduce debugging challenges due to:
- **Opaque logic** (hard to trace mutations without SQL logs)
- **Object-relational mismatch** (ORM-generated queries vs. SP calls)
- **Transaction boundary issues** (implicit commits in SPs)

This guide provides a structured approach to diagnosing and resolving common issues when mutations rely on stored procedures.

---

## **2. Symptom Checklist**
Before diving into debugging, verify whether your issue aligns with these symptoms:

| **Symptom**                     | **Possible Cause**                          | **Checklist Item** |
|----------------------------------|---------------------------------------------|--------------------|
| Mutations fail intermittently    | SP timeout, deadlock, or resource contention | Log SP execution time, check table locks. |
| Inconsistent data after mutations | SP logic violates ACID rules (e.g., no transaction or improper rollback) | Verify transaction isolation level, check for implicit commits. |
| Slow mutation performance        | Inefficient SP queries or blocking queries  | Review SP execution plan, identify bottlenecks. |
| Unexpected errors from DB        | Invalid parameters, missing permissions     | Validate input parameters, check SP error logs. |
| Hardcoded IDs in mutations       | SPs generate IDs instead of letting ORM handle them | Confirm if your ORM can auto-generate IDs. |
| Debugging requires SQL access     | ORM bypasses SPs, or SP logs are unavailable | Ensure SPs log errors and parameters. |

---

## **3. Common Issues and Fixes**

### **Issue 1: Unhandled SP Errors (No Error Propagation)**
**Symptoms:**
- Application crashes silently.
- Errors in SP logs but no feedback to the client.

**Root Cause:**
- SPs may not return proper error codes or log exceptions.
- ORM may swallow database exceptions.

**Fix:**
#### **Option A: Modify SP to Return Errors Explicitly**
```sql
-- SQL Server Example
CREATE PROCEDURE CreateOrder_WithErrorHandling
    @CustomerId INT,
    @Amount DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        -- Your logic here
        IF @Amount <= 0
            RAISERROR('Invalid amount', 16, 1);

        INSERT INTO Orders (CustomerId, Amount) VALUES (@CustomerId, @Amount);
        RETURN 1; -- Success
    END TRY
    BEGIN CATCH
        -- Log error details
        INSERT INTO ErrorLog (ErrorMessage, StackTrace)
        VALUES (ERROR_MESSAGE(), ERROR_PROCEDURE());
        RETURN -1; -- Failure
    END CATCH
END;
```

#### **Option B: Catch Errors in Application Code**
```typescript
// Example in TypeScript (using Prisma)
try {
    const result = await prisma.$executeRaw`
        CALL CreateOrder_WithErrorHandling(${customerId}, ${amount})
    `;

    if (result === -1) {
        throw new Error("Order creation failed");
    }
} catch (error) {
    console.error("SP Failed:", error);
    // Retry or notify user
}
```

---

### **Issue 2: Missing Transactions (Data Inconsistency)**
**Symptoms:**
- Partial mutations (e.g., email sent but order not created).
- Violations of referential integrity.

**Root Cause:**
- SPs default to autocommit.
- Application transaction doesn’t wrap SP calls.

**Fix:**
#### **Option A: Explicit Transaction in SP**
```sql
-- PostgreSQL Example
CREATE OR REPLACE PROCEDURE ProcessOrder(
    IN p_customer_id INT,
    IN p_amount DECIMAL(10,2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Start transaction (implied in PL/pgSQL)
    INSERT INTO Orders (CustomerId, Amount) VALUES (p_customer_id, p_amount);

    -- Simulate a failure (for testing)
    IF p_amount < 100 THEN
        ROLLBACK;
        RAISERROR('Order too small', 16, 1);
    END IF;

    COMMIT;
END;
$$;
```

#### **Option B: Application-Level Transaction**
```javascript
// Node.js + Knex
await db.transaction(async (trx) => {
    // Call SP within transaction
    const spResult = await trx.raw(
        `CALL ProcessOrder(?, ?)`, [customerId, amount]
    );

    if (spResult[0].affectedRows === 0) {
        throw new Error("Transaction failed");
    }
});
```

---

### **Issue 3: SP Logs Are Unavailable**
**Symptoms:**
- No visibility into SP execution.
- Hard to debug parameter issues.

**Root Cause:**
- Database logs are off or not monitored.
- ORM hides SP calls.

**Fix:**
#### **Option A: Enable SP Logging**
##### **SQL Server (via Extended Events)**
```sql
CREATE EVENT SESSION [SP_Logging] ON SERVER
ADD EVENT sqlserver.sp_statement_completed(
    WHERE ([sqlserver].[database_id] = DB_ID('YourDB'))
    AND ([sqlserver].[client_app_name] LIKE '%YourApp%'))
ADD TARGET package0.event_file(SET filename=N'SP_Logs');
GO
```

##### **PostgreSQL (via `log_statement`)**
```sql
ALTER SYSTEM SET log_statement = 'all'; -- Logs all SP calls
```

#### **Option B: Log Parameters in SP**
```sql
-- MySQL Example
DELIMITER //
CREATE PROCEDURE LoggedCreateOrder(IN customer_id INT, IN amount DECIMAL(10,2))
BEGIN
    -- Log call details
    SET @sql = CONCAT('INSERT INTO SP_Logs (Procedure, Args) VALUES ("CreateOrder", JSON_OBJECT("customer_id", ', customer_id, ', "amount", ', amount, '))');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;

    -- Actual logic
    INSERT INTO Orders (CustomerId, Amount) VALUES (customer_id, amount);
END //
DELIMITER ;
```

---

### **Issue 4: ORM vs. SP Mismatch**
**Symptoms:**
- SP generates IDs, but ORM expects auto-increment.
- SP modifies unrelated tables, breaking ORM assumptions.

**Root Cause:**
- Tight coupling between ORM and SP logic.
- SP bypasses ORM optimizations.

**Fix:**
#### **Option A: Hybrid Approach (ORM + SP)**
```typescript
// Fetch ID from ORM, pass to SP
const newOrder = await prisma.order.create({
    data: { CustomerId: customerId },
});
const finalId = await prisma.$executeRaw`SELECT SCOPE_IDENTITY()`;

// Pass ID to SP for side effects
await prisma.$executeRaw`
    CALL ValidateOrder(?, ${newOrder.ID})
`, [customerId];
```

#### **Option B: SP Returns Output Parameters**
```sql
CREATE PROCEDURE CreateOrder_WithOutput
    @OrderId INT OUTPUT,
    @CustomerId INT,
    @Amount DECIMAL(18,2)
AS
BEGIN
    INSERT INTO Orders (CustomerId, Amount) OUTPUT INSERTED.ID INTO @OrderId
    VALUES (@CustomerId, @Amount);
END;
```
**Call with output:**
```typescript
const [rows] = await prisma.$queryRaw`CALL CreateOrder_WithOutput(?, ?, ?)`, [
    prisma.$ref('OrderId'), // Output
    customerId,
    amount
];
```

---

### **Issue 5: SP Timeout or Deadlocks**
**Symptoms:**
- Mutations fail after some time.
- Long-running transactions.

**Root Cause:**
- SP contains inefficient loops or long-running queries.
- Missing timeouts or retry logic.

**Fix:**
#### **Option A: Optimize SP Queries**
```sql
-- Avoid SELECT * in loops; fetch only needed columns
WITH OrderedCustomers AS (
    SELECT id, name FROM Customers WHERE is_active = 1
)
SELECT id, name FROM OrderedCustomers;
```

#### **Option B: Add Timeout Handling**
```typescript
// Node.js with retry
async function callWithRetry(spName, params) {
    let retries = 3;
    while (retries--) {
        try {
            const result = await prisma.$executeRaw(spName, params);
            return result;
        } catch (error) {
            if (error.message.includes('timeout')) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                continue;
            }
            throw error;
        }
    }
    throw new Error("SP call failed after retries");
}
```

---

## **4. Debugging Tools and Techniques**

| **Tool/Technique**               | **Use Case**                                  | **Example** |
|-----------------------------------|-----------------------------------------------|-------------|
| **Database Profiler**             | Capture SP execution plans                   | SQL Server Profiler, PostgreSQL `pg_stat_statements` |
| **Log Analysis**                  | Filter SP errors                             | `SELECT * FROM ErrorLog WHERE Procedure = 'CreateOrder'` |
| **ORM Query Hooks**               | Log SP calls from application                | Prisma Middleware, TypeORM Interceptors |
| **Transaction Logs**              | Replay failed transactions                  | `pg_backup_start` (PostgreSQL), `VSS backup` (SQL Server) |
| **Deadlock Graphs**               | Identify blocking SPs                        | `sys.dm_tran_locks` (SQL Server) |

---

## **5. Prevention Strategies**

### **Best Practices to Avoid Future Issues**
1. **Centralize SP Logic:**
   - Use a single source of truth for business rules (e.g., application code) and delegate only data access to SPs.

2. **Mock SPs in Tests:**
   ```typescript
   // Jest + Knex mock
   const spStub = jest.fn();
   knex.raw.mockImplementation((query) => {
       if (query.includes("ProcessOrder")) return spStub();
       return knex.raw(query);
   });
   ```

3. **Enforce SP Naming Conventions:**
   - `Prefix with "sp_"` and suffix with verb (e.g., `sp_GetCustomerOrders`).

4. **Document SP Dependencies:**
   - Maintain a DB schema diagram showing which tables SPs modify.

5. **Automated SP Testing:**
   ```bash
   # Example: SQL Server CI test with `sqlpackage`
   sqlpackage.exe /Action:Test /SourceFile:Database.sql /TestFolder:Tests
   ```

6. **Monitor SP Performance:**
   - Set up alerts for SPs exceeding threshold execution times.

---

## **6. When to Refactor**
Consider refactoring mutations out of SPs if:
- Logic is **complex** (multiple pages of SQL).
- You need **versioning** (e.g., Git track changes).
- **Debugging is too slow** (SPs hide logic from devs).

**Alternative Pattern: Repository + DTOs**
```typescript
// Repository class
class OrderRepository {
    async create(customerId: number, amount: number) {
        return await db.transaction(async (trx) => {
            const order = await trx('Orders').insertAndFetch({
                CustomerId: customerId,
                Amount: amount,
            });
            await this.sendOrderConfirmation(order.ID);
            return order;
        });
    }
}
```

---

## **7. Summary Checklist**
| **Step**                     | **Action Items** |
|------------------------------|------------------|
| **Check Symptoms**           | Verify if it’s SP-related (use profiler). |
| **Review SP Logic**          | Look for implicit commits, deadlocks, or errors. |
| **Enable Logging**           | Turn on SP logging and error tracking. |
| **Test in Isolation**        | Run SP directly in DB client (e.g., DBeaver). |
| **Fix Application Code**     | Ensure transactions wrap SP calls. |
| **Optimize SP**              | Add indexes, avoid loops, use CTEs. |
| **Prevent Future Issues**    | Automate tests, document SPs, and monitor performance. |

---
**Final Note:** Stored procedures can be powerful but require discipline to debug. The key is **reducing coupling** between application logic and SPs while ensuring **transactions and errors** are handled consistently. Start with symptoms, isolate the SP, and work backward to the application layer.