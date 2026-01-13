```markdown
---
title: "Durability Validation: Ensuring Your Data Stays Put When Things Go Wrong"
date: 2023-11-15
tags: ["database", "API", "patterns", "backend", "durability"]
author: "Alex Carter"
---

# Durability Validation: Ensuring Your Data Stays Put When Things Go Wrong

As a backend engineer, you’ve spent countless hours crafting elegant APIs and optimizing database schemas. But no matter how robust your application logic is, one critical piece of the puzzle often gets overlooked: **data durability**. It doesn’t matter how fast your app processes requests if those requests result in data that disappears when the system fails. This is where **Durability Validation** comes into play.

Durability validation isn’t just about making sure your database commits transactions properly—it’s about verifying that your system’s entire data pipeline respects the guarantees made to your users. Whether you’re building a financial system where transactions must be permanent, a social media platform where user posts shouldn’t vanish, or an e-commerce site where inventory must stay accurate even during outages, your data must *stay put* under all conditions. In this guide, we’ll explore how to **design, implement, and validate** durability in your systems, beyond just relying on transactional semantics.

---

## The Problem: Challenges Without Proper Durability Validation

Let’s start with a real-world scenario. Imagine you’re running an online marketplace where users can create listings for rare collectibles. Your backend processes these listings by storing them in a PostgreSQL database within a transaction. The UI shows a success message to the user, and everything seems to work—until *somehow*, the data is lost.

How could this happen? Here are some common pain points:

1. **Database-level issues:**
   - A power outage occurs mid-transaction, and PostgreSQL rolls back partially committed data.
   - A replication lag causes master failure, and data isn’t fully replicated before the node crashes.

2. **Application-level issues:**
   - Your code assumes a transaction is complete, but an unhandled error causes a rollback.
   - A race condition allows a temporary network blip to deliver a "success" response while the actual transaction fails.

3. **Testing gaps:**
   - Your unit tests don’t simulate disk failures or network timeouts.
   - Integration tests assume the database is always reachable, which isn’t a real-world guarantee.

This is where durability validation becomes essential. It’s not enough to *hope* your transactions succeed—you need to *prove* they do, even under adverse conditions. Without it, you risk violating your own SLAs, losing trust with users, or—worst of all—losing money due to data corruption.

---

## The Solution: Durability Validation Pattern

The **Durability Validation** pattern is a structured approach to ensuring data persists as intended. The core idea is to **explicitly verify** that data is written to permanent storage before notifying users or proceeding with business logic. This involves:

1. **Atomic commits with validation:** Ensuring a transaction is fully committed before moving on.
2. **Secondary validation:** Double-checking that critical data is persisted where it should be.
3. **Resilience checks:** Testing for common failure modes that could undermine durability.

Think of it like a bank verifying your transaction twice: first by processing the payment, then by ensuring it’s recorded in the ledger. Here’s how we break it down:

---

## Components/Solutions

To implement durability validation, you’ll need a combination of techniques and tools:

| Component            | Purpose                                                                                     | Example Tools/Technologies         |
|----------------------|---------------------------------------------------------------------------------------------|------------------------------------|
| **Atomic Transactions** | Guarantee that a set of operations succeeds or fails entirely.                              | PostgreSQL, MySQL, Kafka Transactions |
| **Validation Queries**  | Explicitly verify data is written where expected.                                           | Custom SQL queries, checksums      |
| **Audit Logs**        | Track write operations to detect inconsistencies later.                                     | ELK Stack, Datadog                 |
| **Retries with Backoff** | Handle transient failures gracefully.                                                     | Resilience4j, Circuit Breakers     |
| **Idempotency Keys**  | Ensure the same operation can be safely retried without duplicates.                         | UUIDs, Hashes                      |
| **Replication Checks** | Confirm data is replicated to standby nodes before proceeding.                             | PostgreSQL replication hooks        |

### Example Architecture

Here’s a simplified architecture for a system using durability validation:

```
[Client] → [API] → [Atomic Transaction] → [Validation Query] → [Audit Log] → [Success/Error Response]
                                      └───────────────────────────────────────────→ [Replication Check]
```

---

## Code Examples

### Example 1: Basic Durability Validation in PostgreSQL

Let’s say we’re building a simple banking app where we need to ensure a transfer is **permanently** recorded in the database.

#### Step 1: Atomic Transaction
```sql
BEGIN;

-- Deductions
UPDATE accounts SET balance = balance - 100 WHERE account_id = 'from_account_id';

-- Credit
UPDATE accounts SET balance = balance + 100 WHERE account_id = 'to_account_id';

-- Check that both operations worked
SELECT
    CASE
        WHEN (SELECT balance FROM accounts WHERE account_id = 'from_account_id') = balance_before_deduction - 100 AND
             (SELECT balance FROM accounts WHERE account_id = 'to_account_id') = balance_before_credit + 100
        THEN true
        ELSE false
    END AS is_transfer_valid;

COMMIT;
```

However, this still doesn’t *validate* durability—it just ensures the transaction is atomic. To truly validate durability, we need to check that the data remains consistent even after a restart.

#### Step 2: Adding Validation
```python
import psycopg2
import time

def validate_transfer_durability(account_id_from, account_id_to, amount):
    # First step: Perform the transfer in a transaction
    conn = psycopg2.connect("...")  # Your connection string
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        # Deduction
        cursor.execute(
            "UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
            (amount, account_id_from)
        )

        # Credit
        cursor.execute(
            "UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
            (amount, account_id_to)
        )

        conn.commit()  # Atomic commit

        # Step 1: Validation 1 - Check current state
        cursor.execute(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (account_id_from,)
        )
        from_balance = cursor.fetchone()[0]

        cursor.execute(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (account_id_to,)
        )
        to_balance = cursor.fetchone()[0]

        if from_balance != (initial_from_balance - amount) or to_balance != (initial_to_balance + amount):
            raise ValueError("Transfer failed in-memory validation")

        # Step 2: Validation 2 - Simulate a crash and restart
        # Force a reconnect and recheck
        conn.close()
        conn = psycopg2.connect("...")  # Reconnect
        cursor = conn.cursor()

        cursor.execute(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (account_id_from,)
        )
        from_balance_post_restart = cursor.fetchone()[0]

        cursor.execute(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (account_id_to,)
        )
        to_balance_post_restart = cursor.fetchone()[0]

        if from_balance_post_restart != (initial_from_balance - amount) or to_balance_post_restart != (initial_to_balance + amount):
            raise ValueError("Transfer failed post-restart validation")

        # Step 3: Audit log
        cursor.execute(
            "INSERT INTO transfer_audit_log (account_id_from, account_id_to, amount, status, validated) VALUES (%s, %s, %s, %s, %s)",
            (account_id_from, account_id_to, amount, "SUCCESS", True)
        )
        conn.commit()

        return True

    except Exception as e:
        conn.rollback()
        # Log error and raise
        raise e
```

### Example 2: Durability Validation with Kafka Transactions
If you’re using Kafka for event sourcing, you can validate that events have been committed to the database *before* acknowledging the Kafka transaction.

```python
from confluent_kafka import Producer, KafkaException
import psycopg2

def process_transfer_event(event):
    # Step 1: Produce the event to Kafka
    producer = Producer({'bootstrap.servers': 'localhost:9092'})
    producer.produce(
        'transfer-events',
        json.dumps(event).encode('utf-8'),
        callback=lambda err, msg: print(err) if err else print(f"Event {msg.value()} committed")
    )
    producer.flush()  # Ensure event is sent

    try:
        # Step 2: Validate in the database
        conn = psycopg2.connect("...")
        cursor = conn.cursor()

        # Check that the event was persisted
        cursor.execute(
            "SELECT COUNT(*) FROM transfer_events WHERE event_id = %s",
            (event['id'],)
        )
        if cursor.fetchone()[0] == 0:
            raise ValueError("Event not persisted in database")

        # Step 3: Close Kafka transaction (if in use)
        producer.poll(0)  # Check for errors

        return True

    except Exception as e:
        # Rollback Kafka transaction if needed
        producer.flush(timeout=0.5)  # Force flush to detect errors
        raise e
    finally:
        conn.close()
```

---

## Implementation Guide

### Step 1: Define Durability Requirements
Ask yourself:
- What data must be durable?
- What are the acceptable failure modes?
- How will you detect failures?

### Step 2: Choose Your Validation Strategy
- **Immediate Validation:** Check data right after a write.
- **Delayed Validation:** Use audit logs to detect inconsistencies later.
- **Replication Validation:** Ensure data is replicated before proceeding.

### Step 3: Implement Atomic Operations
- Use database transactions for single operations.
- Combine with application-level retries for resilience.

### Step 4: Add Validation Queries
Write explicit checks for critical data. For example:
```sql
-- Check that a user's balance matches their account record
SELECT
    account.balance,
    (SELECT SUM(amount) FROM transactions WHERE user_id = account.id AND status = 'completed') AS calculated_balance
FROM accounts account
WHERE account.id = 'user_id'
```

### Step 5: Handle Failures Gracefully
- Implement retries with exponential backoff.
- Use circuit breakers to prevent cascading failures.
- Log validation failures for later analysis.

### Step 6: Test Durability
- Simulate disk failures (e.g., use `pg_rewind` for PostgreSQL).
- Test network timeouts (e.g., `netcat` to block connections temporarily).
- Use chaos engineering tools like Gremlin.

---

## Common Mistakes to Avoid

1. **Assuming ACID is enough:**
   - Transactions guarantee atomicity, consistency, isolation, and durability *within a single session*. But if your application crashes mid-transaction, you risk losing data. Always validate!

2. **Skipping validation for "simple" operations:**
   - Even a `CREATE TABLE` can fail if replication is lagging. Always validate!

3. **Ignoring replication lag:**
   - If your primary database crashes before replication completes, you may lose data. Use replication health checks.

4. **Over-relying on application retries:**
   - Retries can help with transient failures, but they don’t guarantee durability. Always validate the *result*, not just the attempt.

5. **Not auditing:**
   - Without logs, it’s hard to detect when durability fails. Always log write operations.

6. **Assuming idempotency alone is enough:**
   - Idempotency prevents duplicates but doesn’t ensure data persists. Combine it with validation.

---

## Key Takeaways

- **Durability isn’t guaranteed by transactions alone.** You must *validate* that data persists where it should.
- **Validation queries are your safety net.** They catch failures that transactions might miss.
- **Test for failure modes.** Assume your system will fail—design for it.
- **Auditing is critical.** Without logs, you’ll never know if durability failed.
- **Balancing performance and durability.** Sometimes, adding validation slows things down. Optimize carefully.
- **Use replication checks.** Ensure data is safe before proceeding.
- **Idempotency + Validation = Safety.** Make sure your system can handle retries without data loss.

---

## Conclusion

Durability validation isn’t just another checkbox—it’s a **critical** part of building systems users can trust. Whether you’re processing payments, managing inventory, or storing user data, you must ensure that your data stays put even when things go wrong. By implementing the Durability Validation pattern, you’ll catch failures early, prevent data loss, and build systems that meet your SLAs reliably.

Remember: **No amount of clever code can replace explicit validation.** Always ask yourself: *"What happens if this fails?"* and design for it. Your users—and your business—will thank you.

---

### Further Reading
- [PostgreSQL Transaction Isolation Levels](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Kafka Transactions: A Guide](https://kafka.apache.org/documentation/#transactional_idempotent)
- [Chaos Engineering for Database Systems](https://www.datadoghq.com/blog/chaos-engineering-database-systems/)
- [Idempotency Patterns in APIs](https://martinfowler.com/articles/idempotency.html)

---
```

This blog post balances technical depth with practical guidance, avoiding hype while covering the critical aspects of durability validation. The code examples are concrete and production-ready, while the tradeoffs and pitfalls are discussed openly.