# **[Pattern] Database Transaction Patterns – Reference Guide**

---

## **Overview**
Database transactions group a series of database operations into a single atomic unit—ensuring either all changes succeed (*commit*) or none are applied (*rollback*). Transactions leverage **ACID properties** (Atomicity, Consistency, Isolation, Durability) to maintain data integrity under concurrent access. This pattern is foundational for financial systems, inventory management, and distributed applications where correctness over raw speed is critical.

By structuring operations into transactions, developers mitigate race conditions and ensure consistency across related database changes. However, improper transaction design can lead to performance bottlenecks due to **locking contention** or **deadlocks**, emphasizing the need for **concurrency control** and **optimistic vs. pessimistic locking** strategies.

---

## **Key Concepts**

### **1. ACID Properties**
| **Property**    | **Definition**                                                                 | **Example**                                                                 |
|-----------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Atomicity**   | A transaction is a single, indivisible unit; either fully executed or aborted. | A bank transfer fails if either withdrawal or deposit succeeds.               |
| **Consistency** | The database remains in a valid state before/after the transaction.          | Checking account balances must always match total funds.                     |
| **Isolation**   | Concurrent transactions appear sequential (no interference).                  | Two users can’t read/write conflicting data during overlapping operations.    |
| **Durability**  | Committed changes persist even after system failures.                          | Journal log entries ensure recovery after crashes.                          |

---

### **2. Isolation Levels**
Transactions can operate at different **isolation levels**, balancing consistency vs. performance. Higher isolation reduces concurrency issues but may introduce **phantom reads** or **dirty reads**.

| **Level**        | **Description**                                                                 | **Potential Issues**                                                                                     | **Use Case**                          |
|------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|---------------------------------------|
| **Read Uncommitted** | Allows dirty reads (uncommitted changes).                                   | Dirty reads, non-repeatable reads, phantom reads.                                                     | Rarely used; only in high-performance scenarios where speed outweighs correctness. |
| **Read Committed**    | Prevents dirty reads; rows locked during reads.                                | Non-repeatable reads, phantom reads.                                                               | Default in Oracle; common for CRUD apps. |
| **Repeatable Read**    | Locks ranges (indexes) to avoid phantom reads; may use MVCC (Multi-Version Concurrency Control). | Phantom reads in some databases (e.g., MySQL).                                                     | PostgreSQL default; suitable for transaction-heavy workloads. |
| **Serializable**       | Strictest isolation; simulates serial execution of transactions.            | Highest overhead; deadlocks possible if not managed.                                                   | High-integrity systems (e.g., financial audits). |

---

### **3. Locking Mechanisms**
Locks enforce isolation but can cause **blocking** or **deadlocks**. Two primary strategies:
- **Pessimistic Locking**: Locks resources *before* access (prevents conflicts but risks blocking).
- **Optimistic Locking**: Assumes conflicts are rare; validates changes at commit (e.g., `SELECT ... FOR UPDATE`).

| **Lock Type**       | **Scope**               | **Use Case**                                                                 | **Risk**                          |
|---------------------|------------------------|-------------------------------------------------------------------------------|-----------------------------------|
| **Row Lock**        | Single row             | High-contention scenarios (e.g., inventory updates).                         | Scalability issues at scale.      |
| **Table Lock**      | Entire table           | Legacy systems or rare bulk operations.                                      | Prevents all other transactions.  |
| **Gap Lock**        | Key range (e.g., `BETWEEN` values) | Prevents phantom reads in `Repeatable Read` (e.g., MySQL).                 | Overhead for range queries.       |
| **Advisory Lock**   | Application-defined    | Non-blocking coordination (e.g., "Document X is being edited").             | Manual cleanup required.           |

---
### **4. Transaction Isolation Anomalies**
| **Anomaly**            | **Definition**                                                                 | **Example Scenario**                                                                 | **Mitigation**                          |
|------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|-----------------------------------------|
| **Dirty Read**         | Reads uncommitted data.                                                      | User A updates salary; User B reads it before commit.                                | Use `Read Committed` or higher.         |
| **Non-Repeatable Read**| Intermediate changes are visible across reads.                              | User queries order status; another user updates it before commit.                  | Use `Repeatable Read`.                  |
| **Phantom Read**       | New rows appear during a transaction (e.g., `WHERE id > 100`).              | User locks rows `101–200`; another inserts `201` between reads.                      | Use `Serializable` or gap locks.        |
| **Lost Update**        | Two transactions overwrite each other’s changes.                              | User A and B update the same row concurrently; only one change persists.            | Use optimistic locking (e.g., `VERSION` column). |

---

## **Schema Reference**
Below is a **normalized schema** for a **bank account transaction example**, demonstrating common transaction patterns.

```sql
-- Tables for transaction handling
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    version INT NOT NULL DEFAULT 1,  -- Optimistic locking
    -- Constraints for isolation
    CONSTRAINT positive_balance CHECK (balance >= 0)
);

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES accounts(account_id),
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Adds durability via WAL (Write-Ahead Logging)
    COMMENT 'Records all account changes for audit and rollback'
);

-- Indexes for performance
CREATE INDEX idx_account_balance ON accounts(balance);
CREATE INDEX idx_transaction_account ON transactions(account_id);
```

---

## **Query Examples**
### **1. Basic Transaction (Atomic Transfer)**
```sql
BEGIN TRANSACTION;

-- Step 1: Check sufficient balance (sequential consistency)
SELECT balance FROM accounts WHERE account_id = 1001 FOR UPDATE;
-- Locks the row to prevent concurrent modifications.

-- Step 2: Deduct amount
UPDATE accounts
SET balance = balance - 100.00, version = version + 1
WHERE account_id = 1001;

-- Step 3: Credit recipient
UPDATE accounts
SET balance = balance + 100.00, version = version + 1
WHERE account_id = 1002;

-- Step 4: Record transaction (durable log)
INSERT INTO transactions (account_id, amount, status)
VALUES (1001, -100.00, 'COMPLETED'), (1002, 100.00, 'COMPLETED');

COMMIT;
```

**Note:** Use `FOR UPDATE` to acquire row locks (pessimistic locking). For optimistic locking, replace the `WHERE` clause with `WHERE version = <expected_value>`.

---

### **2. Retry on Deadlock (Application-Level Handling)**
```sql
DO $$
DECLARE
    retries INT := 0;
    max_retries CONSTANT INT := 3;
BEGIN
    WHILE retries < max_retries LOOP
        BEGIN
            -- Attempt transfer inside a transaction
            -- (Code from Example 1)
            COMMIT;
            EXIT; -- Success
        EXCEPTION
            WHEN OTHERS THEN
                IF SQLERRM LIKE '%deadlock%' THEN
                    RAISE NOTICE 'Deadlock detected. Retrying...';
                    retries := retries + 1;
                ELSE
                    RAISE;
                END IF;
        END;
    END LOOP;
    RAISE EXCEPTION 'Transfer failed after % retries', max_retries;
END $$;
```

---

### **3. Savepoints for Partial Rollback**
```sql
BEGIN TRANSACTION;

-- Step 1: Update primary account
UPDATE accounts SET balance = balance - 500 WHERE account_id = 1001;

-- Savepoint for selective rollback
SAVEPOINT update_step1;

-- Step 2: Update secondary account (may fail)
UPDATE accounts SET balance = balance + 500 WHERE account_id = 1002
RETURNING amount;

-- If Step 2 fails, roll back to savepoint
ROLLBACK TO update_step1; -- Only undoes Step 2
COMMIT; -- Completes remaining steps
```

---
### **4. Batch Processing with Transactions**
```sql
BEGIN;

-- Process 1,000 rows in a single transaction (avoids partial updates)
INSERT INTO audit_log (operation, details)
SELECT 'TRANSFER', jsonb_build_object('from', a1.account_id, 'to', a2.account_id, 'amount', 100.00)
FROM accounts a1, accounts a2
WHERE a1.balance > 1000 AND a2.balance < 10000;

COMMIT;
```

**Caution:** Large transactions can hold locks for extended periods, blocking other operations.

---

## **Performance Considerations**
| **Factor**            | **Impact**                                                                 | **Mitigation Strategy**                                                                 |
|-----------------------|----------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Lock Contention**   | Long-running transactions block others.                                   | Use shorter transactions; implement retry logic for deadlocks.                        |
| **MVCC Overhead**     | Databases like PostgreSQL store historic versions for `Repeatable Read`.   | Tune `max_standby_archive_delay`; avoid excessive `SELECT ... FOR UPDATE`.            |
| **Network Latency**   | Distributed transactions (e.g., 2PC) increase latency.                    | Use **compensating transactions** or **saga patterns** for eventual consistency.       |
| **Index Scans**       | Wide tables with few indexes slow down `FOR UPDATE` locks.                | Add strategic indexes (e.g., `account_id`, `balance`).                                  |

---

## **Related Patterns**
1. **[Saga Pattern]**
   - For **long-running, distributed transactions** where ACID is too restrictive.
   - Uses **compensating transactions** to undo partial failures.
   - *Example:* Microservices order processing with inventory and payment services.

2. **[Command Query Responsibility Segregation (CQRS)]**
   - Separates read (optimized for performance) and write (strict ACID) paths.
   - *Example:* A read-optimized dashboard alongside a transactional order service.

3. **[Optimistic Concurrency Control]**
   - Avoids locks by validating version stamps at commit.
   - *Example:* `UPDATE users SET email = '...' WHERE user_id = 1 AND version = 5;`.

4. **[Two-Phase Commit (2PC)]**
   - Ensures **global atomicity** across databases (e.g., master-slave replication).
   - *Caution:* High latency; replace with **eventual consistency** where possible.

5. **[Retry Pattern]**
   - Handles transient failures (e.g., deadlocks) via exponential backoff.
   - *Example:* Retrying a `UPDATE` after `SQLSTATE 40P01` (serialization failure).

---

## **Anti-Patterns to Avoid**
| **Anti-Pattern**          | **Problem**                                                                 | **Fix**                                                                             |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Nesting Transactions**  | Child transactions aren’t atomic; may force explicit `SAVEPOINT` management. | Flatten transactions or use application-level retries.                              |
| **Long-Running Transactions** | Blocks resources; violates **isolation**.                                  | Break into smaller transactions or use **read-only** where possible.                |
| **Ignoring Deadlocks**    | Silent failures cause data corruption.                                     | Implement application-level deadlock detection (e.g., retry logic).                  |
| **Overusing Serializable** | Performance bottleneck for most apps.                                       | Default to `Repeatable Read`; use `Serializable` only for critical operations.    |

---
## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                 | **Example Use Case**                          |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **JDBC `Connection.setAutoCommit(false)`** | Manual transaction control in Java.                                         | Batch updates in Spring Boot.                  |
| **ORM Savepoints**     | Hibernate/JPA supports `savepoint()` for partial rollback.                 | Complex business rules with conditional commits. |
| **Database-Agnostic**  | Libraries like **Saga ORM** abstract distributed transactions.               | Microservices with Kafka/Saga integration.    |
| **Monitoring**         | **PGBadger** (PostgreSQL), **Percona Toolkit** (MySQL) for lock analysis.  | Diagnosing deadlocks in production.           |

---
## **Further Reading**
- [PostgreSQL Transaction Isolation Levels](https://www.postgresql.org/docs/current/transaction-iso.html)
- [SQL Standard Isolation Anomalies](https://en.wikipedia.org/wiki/Isolation_(database_systems))
- [Martin Fowler – Saga Pattern](https://martinfowler.com/articles/saga.html)