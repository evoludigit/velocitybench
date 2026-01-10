# **[Pattern] Database Locks & Deadlocks Reference Guide**

---

## **1. Overview**
Database locks ensure data integrity in concurrent environments by preventing simultaneous unauthorized modifications to shared resources. Proper lock management is critical for avoiding deadlocks, performance bottlenecks, and application failures. This guide covers lock types, mechanisms, detection, mitigation, and recovery strategies across relational databases (e.g., PostgreSQL, MySQL, SQL Server).

Key challenges include:
- **Lock contention** (unnecessary blocking).
- **Deadlocks** (circular wait states).
- **Performance trade-offs** (duration/granularity of locks).

---

## **2. Schema Reference**

### **2.1 Lock Types**
| **Lock Type**          | **Description**                                                                 | **Lock Scope**         | **Database Examples**                     |
|------------------------|---------------------------------------------------------------------------------|------------------------|-------------------------------------------|
| **Shared (S)**         | Allows concurrent reads but blocks writes.                                      | Row/table/database     | `SELECT ... FOR SHARE` (PostgreSQL)      |
| **Exclusive (X)**      | Blocks all other locks (reads/writes).                                          | Row/table/database     | `SELECT ... FOR UPDATE`                   |
| **Intent Locks**       | Indicate intent to acquire higher-level locks (reduces lock escalation).       | Table/database         | Implicit in SQL Server/MySQL              |
| **Advisory Locks**     | Application-managed (non-standardized).                                         | Arbitrary (e.g., keys) | `SELECT ... IN SHARE MODE` (MySQL)       |
| **Optimistic Locks**   | Uses version columns to detect conflicts at commit (no blocking).               | Row                    | `WHERE version = @expected_version`      |
| **Gap Locks**          | Prevents concurrent inserts/deletes in a range (sparse table scenarios).       | Range (row gap)        | `SELECT ... IN ACCESS EXCLUSIVE MODE`     |
| **Next-Key Locks**     | Combines row + gap locks (default in PostgreSQL for `serializable`).             | Row + adjacent gap     | PostgreSQL `serializable` isolation       |

---

### **2.2 Lock Isolation Levels**
| **Level**             | **Locking Behavior**                                                                 | **Deadlock Risk** | **Database Examples**                     |
|-----------------------|-------------------------------------------------------------------------------------|-------------------|-------------------------------------------|
| **Read Uncommitted**  | No locks; dirty reads allowed.                                                      | Minimal           | `SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED` |
| **Read Committed**    | Shared locks on rows read; auto-released at commit.                                | Low               | Default in MySQL, SQL Server             |
| **Repeatable Read**   | Shared locks held until transaction end; gap locks may apply.                      | Medium            | PostgreSQL default, `REPEATABLE READ`     |
| **Serializable**      | Strongest consistency; uses gaps/next-key locks (high contention).                  | High              | PostgreSQL `SERIALIZABLE`                 |
| **Snapshot Isolation**| Logical snapshots; no locks (PostgreSQL only).                                      | None              | `SNAPSHOT` mode (PostgreSQL)             |

---

## **3. Query Examples**

### **3.1 Acquiring Locks**
#### **PostgreSQL: Explicit Locking**
```sql
-- Lock a row for update (X-lock)
SELECT * FROM orders WHERE id = 1 FOR UPDATE;

-- Lock a table for shared access
LOCK TABLE customers IN SHARE MODE;
```

#### **SQL Server: Table-Lock Hint**
```sql
-- Force exclusive table lock (use cautiously!)
SELECT * FROM products WITH (TABLOCKX);
```

#### **MySQL: Advisory Locks**
```sql
-- Lock multiple rows by key (key=123)
SELECT * FROM inventory WHERE item_id = 123 IN SHARE MODE;
```

---

### **3.2 Deadlock Detection & Recovery**
#### **PostgreSQL: Identify Deadlocks**
```sql
-- Check for active locks
SELECT locktype, relation::regclass, mode, transactionid AS tid
FROM pg_locks
WHERE NOT granted;
```

#### **SQL Server: Resolve Deadlocks**
```sql
-- Enable deadlock logging (first, check existing deadlocks)
DBCC TRACEON(1201);
-- Then resolve via application logic (e.g., retry with adjusted order).
```

#### **MySQL: Escape Deadlocks**
```sql
-- Use `FLUSH TABLES ... FOR EXPORT` to break locks (last resort).
FLUSH TABLES products METADATA LOCKED;
```

---

### **3.3 Optimistic Locking (No Locks)**
#### **Entity Framework Core (C#)**
```csharp
// Add version column to model:
public class Product { public int Id { get; set; } public int Version { get; set; } }

// Update with check:
var product = await _context.Products.FindAsync(id);
if (product.Version != expectedVersion)
    throw new ConcurrencyException("Conflict");
_context.Update(product);
await _context.SaveChangesAsync();
```

#### **SQL (Version Column)**
```sql
-- Update with version check
UPDATE products
SET stock = stock - 1
WHERE id = 100 AND version = @currentVersion;
```

---

## **4. Deadlock Prevention Strategies**
| **Strategy**               | **Description**                                                                                     | **Pros**                          | **Cons**                          |
|----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------|-----------------------------------|
| **Lock Ordering**          | Enforce consistent lock acquisition order (e.g., always lock `A` before `B`).                      | Prevents deadlocks                | Requires discipline               |
| **Short-Lived Transactions**| Minimize transaction duration to reduce lock hold time.                                             | Lower contention                  | May increase retry logic          |
| **Retry Logic**            | Implement exponential backoff for deadlock errors (e.g., `SQLSTATE 40501`).                        | Resilient                         | Performance overhead              |
| **Optimistic Concurrency** | Rely on version checks instead of locks (PostgreSQL/SQL Server snapshot isolation).*               | No blocking                        | Conflict resolution overhead      |
| **Selective Locking**      | Use `FOR UPDATE SKIP LOCKED` (PostgreSQL) to skip locked rows.                                   | Reduces contention                | May miss data                     |
| **Database-Specific Tuning**| Adjust `max_locks`, `lock_timeout` (PostgreSQL), or `deadlock_priority` (SQL Server).             | Fine-grained control              | Configuration complexity          |

*Requires `ISOLATION LEVEL SNAPSHOT` (SQL Server/PostgreSQL) or `READ COMMITTED SNAPSHOT`.

---

## **5. Recovery Procedures**
1. **Terminate Transactions**
   - **PostgreSQL**:
     ```sql
     SELECT pg_terminate_backend(pid)
     FROM pg_stat_activity
     WHERE pid = <target_pid>;
     ```
   - **SQL Server**:
     ```sql
     KILL <session_id>;
     ```

2. **Rollback & Retry**
   - Implement retry logic in the application (e.g., .NET’s `RetryPolicy` or Python’s `tenacity`).
   - Example (Python):
     ```python
     from tenacity import retry, stop_after_attempt, wait_exponential

     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
     def update_order(order_id):
         # Retry on deadlock (SQLAlchemy/psycopg2)
         try:
             db.session.execute(f"UPDATE orders SET status='processed' WHERE id={order_id}")
         except psycopg2.Error as e:
             if "deadlock" in str(e).lower():
                 raise e
     ```

3. **Schema Changes**
   - If deadlocks persist, reconsider schema design (e.g., denormalization, separate tables for hotspots).

---

## **6. Performance Considerations**
- **Lock Granularity**:
  - **Fine-grained (row)**: Lower contention but higher overhead.
  - **Coarse-grained (table)**: Faster but risks blocking.
- **Isolation Trade-offs**:
  - `READ COMMITTED` (default) balances concurrency and consistency.
  - `REPEATABLE READ`/`SERIALIZABLE` reduce dirty reads but increase locking.
- **Monitoring**:
  - Track `pg_locks` (PostgreSQL), `sys.dm_tran_locks` (SQL Server), or `SHOW ENGINE INNODB STATUS` (MySQL).

---

## **7. Related Patterns**
1. **[Two-Phase Commit]** – Ensures distributed transaction consistency (complements locks).
2. **[Command Query Responsibility Segregation (CQRS)]** – Separates reads/writes to reduce contention.
3. **[Event Sourcing]** – Decouples state changes to minimize lock duration.
4. **[Bulkhead Pattern]** – Isolates database operations to prevent cascading failures.
5. **[Retry with Backoff]** – Handles transient lock conflicts gracefully.

---
**Appendix**
- **PostgreSQL**: [`FOR UPDATE`](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
- **SQL Server**: [`LOCK_HINT`](https://learn.microsoft.com/en-us/sql/t-sql/statements/select-transact-sql-lock-hints)
- **MySQL**: [`FLUSH TABLES`](https://dev.mysql.com/doc/refman/8.0/en/flush.html)