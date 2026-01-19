# **[Pattern] Transaction Isolation Levels – Reference Guide**

---

## **1. Overview**
Transaction isolation levels define how concurrent database transactions interact—ensuring data consistency while balancing performance and isolation. Higher isolation levels (e.g., `SERIALIZABLE`) reduce concurrency conflicts but increase overhead, while lower levels (e.g., `READ UNCOMMITTED`) improve performance but may expose dirty or phantom reads.

This pattern outlines **five standard SQL isolation levels** (per the [ISO/IEC 23001](https://standards.iso.org/iso/23001/) standard) and their trade-offs, implementation techniques, and use cases. Properly configuring isolation levels mitigates common issues like **dirty reads**, **non-repeatable reads**, and **phantom reads** while optimizing system efficiency.

---

## **2. Key Concepts**

### **2.1 Isolation Levels Hierarchy**
Isolation levels are ranked from weakest to strongest:
- **`READ UNCOMMITTED`** (dirty reads allowed)
- **`READ COMMITTED`** (dirty reads prevented)
- **`REPEATABLE READ`** (non-repeatable reads prevented)
- **`SERIALIZABLE`** (phantom reads prevented)
- *Database-specific:* `READ COMMITTED SNAPSHOT` (optional, reduces blocking)

### **2.2 Common Issues Addressed**
| **Problem**               | **Isolation Level Impact**                     | **Example**                          |
|---------------------------|-----------------------------------------------|--------------------------------------|
| **Dirty Read**            | Allowed in `READ UNCOMMITTED`; blocked in others | T1 reads uncommitted changes from T2. |
| **Non-Repeatable Read**   | Allowed in `READ COMMITTED`; blocked in higher levels | T1 reads a row; T2 updates it before T1 retries. |
| **Phantom Read**          | Allowed in `SERIALIZABLE` (requires locks)    | T1 queries for `id > 10`; T2 inserts `id=11` between reads. |

### **2.3 Locking Mechanisms**
- **`READ COMMITTED`**: Shared locks (S-locks) on rows during reads; auto-released after transaction.
- **`REPEATABLE READ`**: Exclusive locks (X-locks) on keys during writes; row-level locks hold until commit.
- **`SERIALIZABLE`**: Gap locks (prevents phantoms) + shared locks; complex and slow for high concurrency.
- **`READ UNCOMMITTED`**: No locks; risky but fast for read-heavy workloads.

---
## **3. Schema Reference**
Below is a comparison of isolation levels across major databases:

| **Isolation Level**      | **SQL Standard** | **PostgreSQL** | **MySQL**       | **SQL Server** | **Oracle**       | **Key Behavior**                                                                 |
|---------------------------|------------------|-----------------|-----------------|-----------------|-----------------|---------------------------------------------------------------------------------|
| `READ UNCOMMITTED`        | ISO 23001       | `READ UNCOMMITTED` | `READ UNCOMMITTED` | `READ UNCOMMITTED` | `READ UNCOMMITTED` | Allows dirty reads; no locks.                                                |
| `READ COMMITTED`          | ISO 23001       | `READ COMMITTED` | `READ COMMITTED` (default) | `READ COMMITTED` | `READ COMMITTED` | Prevents dirty reads; shared locks during reads.                              |
| `REPEATABLE READ`         | ISO 23001       | `REPEATABLE READ` (MVCC) | `REPEATABLE READ` | `REPEATABLE READ` | `SERIALIZABLE`* | Prevents non-repeatable reads; row locks held until commit.                  |
| `SERIALIZABLE`            | ISO 23001       | `SERIALIZABLE` | `SERIALIZABLE` (InnoDB) | `SERIALIZABLE` | `SERIALIZABLE` | Prevents phantoms; gap locks + row locks; highest consistency cost.           |
| `READ COMMITTED SNAPSHOT` | N/A             | `READ COMMITTED SNAPSHOT` | N/A          | N/A          | N/A          | Like `READ COMMITTED` but uses MVCC; reduces blocking (PostgreSQL only).      |

*Oracle’s `REPEATABLE READ` defaults to `SERIALIZABLE` for full compatibility.*

---
## **4. Implementation Techniques**

### **4.1 Configuring Isolation Levels**
#### **Database-Specific Syntax**
```sql
-- PostgreSQL
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- MySQL
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- SQL Server (via T-SQL)
BEGIN TRANSACTION WITH TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Oracle (via PL/SQL)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

#### **Application-Level Control**
- **JDBC**: Configure via `Connection.setTransactionIsolation()`:
  ```java
  conn.setTransactionIsolation(Connection.TRANSACTION_SERIALIZABLE);
  ```
- **Spring Boot**: Use `@Transactional(isolation = Isolation.SERIALIZABLE)`.
- **ORM Frameworks**: Configure in `persistence.xml` (JPA) or `application.properties` (Hibernate).

---

### **4.2 Optimizing Performance**
| **Strategy**                          | **Use Case**                                  | **Trade-off**                          |
|---------------------------------------|-----------------------------------------------|----------------------------------------|
| **Isolation Level Tuning**            | Reduce to `READ COMMITTED` for read-heavy apps. | Risk of dirty reads.                  |
| **MVCC (Multi-Version Concurrency)**  | PostgreSQL’s `READ COMMITTED SNAPSHOT`        | Higher storage overhead.              |
| **Retry Logic**                       | Handle `SERIALIZABLE` deadlocks via `RETRY`   | Temporary performance degradation.     |
| **Database-Specific Optimizations**  | MySQL: `innodb_lock_wait_timeout` tuning.     | Requires DBA expertise.                |

---

## **5. Query Examples**

### **5.1 Dirty Read (Allowed in `READ UNCOMMITTED`)**
```sql
-- Transaction 1 (Isolation: READ UNCOMMITTED)
BEGIN TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1; -- Uncommitted

-- Transaction 2 (Isolation: READ UNCOMMITTED)
BEGIN TRANSACTION;
SELECT balance FROM accounts WHERE id = 1; -- Reads uncommitted change!
COMMIT;
```
**Result**: T2 sees T1’s uncommitted update.

---

### **5.2 Non-Repeatable Read (Prevented in `REPEATABLE READ`)**
```sql
-- Transaction 1 (Isolation: READ COMMITTED)
SELECT balance FROM accounts WHERE id = 1; -- Returns $100

-- Transaction 2 (Isolation: READ COMMITTED)
BEGIN TRANSACTION;
UPDATE accounts SET balance = balance + 50 WHERE id = 1; -- Updates to $150
COMMIT;

-- Transaction 1 retry
SELECT balance FROM accounts WHERE id = 1; -- Now returns $150 (non-repeatable)
```
**Solution**: Upgrade to `REPEATABLE READ` to lock the row.

---

### **5.3 Phantom Read (Prevented in `SERIALIZABLE`)**
```sql
-- Transaction 1 (Isolation: SERIALIZABLE)
SELECT * FROM products WHERE price < 100; -- Returns 5 items

-- Transaction 2 (Isolation: SERIALIZABLE)
BEGIN TRANSACTION;
INSERT INTO products (name, price) VALUES ('Widget', 80); -- New "phantom" row
COMMIT;

-- Transaction 1 retry
SELECT * FROM products WHERE price < 100; -- Returns 6 items (phantom read)
```
**Solution**: Use `SERIALIZABLE` with gap locks (e.g., in PostgreSQL via `SELECT ... FOR UPDATE`).

---

## **6. Query Examples: Error Conditions**
### **6.1 Deadlock (Common with `SERIALIZABLE`)**
```sql
-- Transaction 1
BEGIN TRANSACTION;
UPDATE accounts SET balance = balance - 50 WHERE id = 1; -- Locks row 1
UPDATE accounts SET balance = balance + 50 WHERE id = 2; -- Waits for row 2

-- Transaction 2 (Runs concurrently)
BEGIN TRANSACTION;
UPDATE accounts SET balance = balance - 50 WHERE id = 2; -- Locks row 2
UPDATE accounts SET balance = balance + 50 WHERE id = 1; -- Waits for row 1
```
**Result**: Deadlock. Handle via `RETRY` or reduce isolation level.

---

## **7. Related Patterns**
| **Pattern**                     | **Purpose**                                                                 | **When to Use**                                  |
|----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **[Optimistic Locking]**        | Uses version columns to detect conflicts without locks.                    | Low-contention apps; caching-friendly.           |
| **[Retry with Exponential Backoff]** | Handles transient failures (e.g., deadlocks).                         | High-latency environments.                       |
| **[MVCC (Multi-Version Concurrency)]** | Isolates reads via temporal versioning.                     | Read-heavy workloads (PostgreSQL, Oracle).       |
| **[Distributed Transactions (2PC)]** | Coordinates locks across databases.                             | Microservices with cross-database consistency.   |
| **[Compensating Transactions]**  | Rolls back changes if primary transaction fails.                     | Eventual consistency scenarios.                  |

---

## **8. Best Practices**
1. **Default**: Start with `READ COMMITTED` (balance of safety/performance).
2. **Profile**: Use database tools (e.g., `pg_stat_activity` in PostgreSQL) to detect contention.
3. **Avoid `SERIALIZABLE`**: Use only for critical data integrity (e.g., banking).
4. **Application Logic**: Design for retries where possible (e.g., `RETRY` on `SQLState '40001'`).
5. **Database-Specific**: Leverage MVCC (`READ COMMITTED SNAPSHOT`) in PostgreSQL to reduce locks.

---
## **9. Further Reading**
- [ISO/IEC 23001:2018 (Database Standard)](https://standards.iso.org/iso/23001/)
- PostgreSQL: [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- MySQL: [InnoDB Locking](https://dev.mysql.com/doc/refman/8.0/en/innodb-locking.html)
- [ACID Properties Explained](https://www.cockroachlabs.com/blog/acid-transactions/)

---
**Last Updated**: [`YYYY-MM-DD`]
**Version**: `1.0`