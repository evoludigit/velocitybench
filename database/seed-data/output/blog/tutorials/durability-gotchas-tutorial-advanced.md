```markdown
---
title: "Durability Gotchas: The Hidden Pitfalls That Can Break Your Data"
date: 2024-07-10
author: Jane Doe
tags: ["database", "distributed-systems", "backend-design", "durability"]
description: "A deep dive into the subtle but critical durability challenges in database and API design. Learn how to identify and fix common pitfalls that can corrupt your data or lose transactions."
---

# Durability Gotchas: The Hidden Pitfalls That Can Break Your Data

Durability—the guarantee that once data is committed to a database, it will survive system crashes, network failures, or even disk failures—is a cornerstone of reliable systems. But what if I told you that durability isn’t just about setting `autocommit=true` or relying on ACID transactions? In reality, **durability gotchas** are everywhere: in how you design APIs, handle retries, manage transactions, or even interpret error messages. These subtle issues can silently corrupt your data, lose transactions, or leave your system in an inconsistent state.

In this post, we’ll explore the **real-world durability gotchas** that even experienced engineers overlook. We’ll dissect the problems, show you how to spot them, and provide practical solutions—complete with code examples and tradeoffs—to ensure your data persists as expected. By the end, you’ll know how to design systems that *actually* survive failures, not just pretend to.

---

## The Problem: Why Durability Is Harder Than It Looks

Durability sounds simple: *"Once committed, data stays committed."* But in practice, durability is a layered problem with many moving parts. Let’s start with a common misconception:

> **"If I use a transactional database, my data is durable."**

This is partly true—but only if you understand how transactions interact with durability guarantees. For example:
- A transaction might commit successfully (you see `status=200`), but if the database crashes before flushing the log to disk, the data is **not durable**.
- Some databases (like PostgreSQL) provide **durability levers** (e.g., `fsync=on` vs. `off`), but misconfigurations can turn them into false positives.
- Distributed systems (e.g., Kafka, DynamoDB) often require additional patterns (like idempotent writes or checkpointers) to ensure durability across failures.

Here’s a real-world scenario that exposes durability flaws:

```javascript
// Example: Inconsistent "Order Completed" state after a crash
const order = await db.transaction(async (tx) => {
  await tx.query("UPDATE orders SET status='completed' WHERE id=?", [orderId]);
  await tx.query("UPDATE inventory SET quantity=quantity-1 WHERE productId=?", [productId]);
});
console.log("Order processed successfully!"); // But what if the DB crashes here?
```
If the database crashes after the `UPDATE inventory` succeeds but before the transaction commits, the order’s `status` remains `"pending"` while inventory is already reduced. **This is a durability failure.**

---
## The Solution: Durability Gotchas and How to Fix Them

Durability isn’t just about transactions—it’s about **end-to-end reliability**. Below are the most common gotchas and how to address them.

---

### 1. **Gotcha: "ACK Before Commit" (The Network Delay Trap)**
**Problem**: Your application sends an `ACK` to the client *before* the database acknowledges the write. If the network fails after `ACK` but before the database commits, the client thinks the operation succeeded while the data is lost.

**Example**:
```python
# Bad: ACK before commit (risky!)
@app.post("/orders")
def create_order():
    order = db.execute("INSERT INTO orders VALUES (?)", [data])
    # ❌ What if the DB crashes here? Client already got 201!
    return {"status": "created"}, 201
```

**Solution**: Use **two-phase commit (2PC)** or **saga patterns** to ensure the client only `ACK`s after the *entire* operation succeeds.

**Better Approach (Saga Pattern)**:
```python
# Saga-like solution: Retryable commands and compensating transactions
@app.post("/orders")
def create_order():
    try:
        # Step 1: Reserve inventory
        db.execute("UPDATE inventory SET reserved=reserved+1 WHERE productId=?", [productId])
        # Step 2: Commit order (if inventory step succeeds)
        order_id = db.execute("INSERT INTO orders VALUES (...) RETURNING id", [data])
        return {"order_id": order_id}, 201
    except Exception as e:
        # Step 3: Compensate (rollback inventory if order fails)
        db.execute("UPDATE inventory SET reserved=reserved-1 WHERE productId=?", [productId])
        raise e
```

**Tradeoff**: Safer but adds complexity (e.g., handling compensating transactions for failures).

---

### 2. **Gotcha: "Write-Ahead Logging (WAL) Misconfigurations"**
**Problem**: Databases like PostgreSQL rely on **WAL (Write-Ahead Logging)** to ensure durability. If WAL is disabled or misconfigured (e.g., `fsync=off`), crashes can lead to partial writes.

**Example**:
```sql
-- PostgreSQL misconfiguration (not recommended in production)
ALTER SYSTEM SET synchronous_commit = 'off';  -- ❌ Bad for durability
ALTER SYSTEM SET fsync = 'off';               -- ❌ Even worse!
```
**Solution**: Tune WAL settings aggressively for durability:
```sql
-- Recommended settings for PostgreSQL
ALTER SYSTEM SET synchronous_commit = 'on';      -- Ensure commits are durably logged
ALTER SYSTEM SET fsync = 'on';                  -- Force fsync after every write
ALTER SYSTEM SET wal_level = 'replica';          -- Required for point-in-time recovery
```

**Tradeoff**: Slower writes but **100% durability guarantees**.

---

### 3. **Gotcha: "Idempotency Without Retry Logic"**
**Problem**: If your API allows retries (e.g., for HTTP `429 Too Many Requests`), but your writes aren’t idempotent, duplicate operations can corrupt data.

**Example**:
```javascript
// Non-idempotent write (dangerous for retries!)
app.post("/transfer", async (req, res) => {
  await db.query("UPDATE accounts SET balance=balance-? WHERE id=?", [
    amount, senderId
  ]);
  await db.query("UPDATE accounts SET balance=balance+? WHERE id=?", [
    amount, receiverId
  ]);
  res.status(200).send("Transfer succeeded");
});
```
If the client retries after a `429`, the transfer may execute twice, corrupting balances.

**Solution**: Use **idempotency keys** (e.g., `request_id`) + **duplicate detection**:
```javascript
// Idempotent write with retry safety
app.post("/transfer", async (req, res) => {
  const { request_id } = req.headers;
  const result = await db.query(
    `INSERT INTO transfers (request_id, sender_id, receiver_id, amount)
     VALUES (?, ?, ?, ?)
     ON CONFLICT (request_id) DO NOTHING`,
    [request_id, senderId, receiverId, amount]
  );
  if (result.rowCount === 0) {
    return res.status(200).send("Already processed");
  }
  // Proceed with transfer...
});
```

**Tradeoff**: Adds overhead but prevents duplicates.

---

### 4. **Gotcha: "Eventual Consistency Without Checkpoints"**
**Problem**: In distributed systems (e.g., Kafka, DynamoDB), **eventual consistency** is the default. Without **checkpoints** (e.g., periodic snapshots), you risk losing state during crashes.

**Example**:
```python
# Kafka consumer: No checkpointing (data loss risk!)
def process_order(order):
    try:
        # Process order (e.g., update inventory)
        db.execute("UPDATE inventory SET quantity=quantity-1 WHERE productId=?", [productId])
    except Exception:
        # What if the process crashes here? Order is lost!
        pass
```

**Solution**: Use **checkpointing** (e.g., Kafka offsets) or **transactional outbox patterns**:
```python
# Kafka + Outbox Pattern (durable)
def process_order(order):
    try:
        # Step 1: Write to outbox
        db.execute(
            "INSERT INTO outbox (event_type, payload) VALUES (?, ?)",
            ["inventory_reserved", order.payload]
        )
        db.commit()
        # Step 2: Process (separate transaction)
        db.execute("UPDATE inventory SET quantity=quantity-1 WHERE productId=?", [productId])
        db.commit()
    except Exception:
        db.rollback()
        raise
```

**Tradeoff**: More complex but **failsafe**.

---

### 5. **Gotcha: "Race Conditions in Distributed Transactions"**
**Problem**: When multiple services update the same data (e.g., across microservices), **race conditions** can corrupt state even if each service is durable individually.

**Example**:
```python
# Microservice A: Update user balance
def deduct_balance(user_id, amount):
    db.execute("UPDATE users SET balance=balance-? WHERE id=?", [amount, user_id])

# Microservice B: Update user credits
def update_credits(user_id, credits):
    db.execute("UPDATE users SET credits=credits+? WHERE id=?", [credits, user_id])
```
If Microservice A and B run concurrently, the `users` table may end up with **inconsistent `balance` + `credits`** due to race conditions.

**Solution**: Use **pessimistic locks** or **distributed transactions** (e.g., Sage, 2PC):
```python
# With locking (PostgreSQL example)
db.execute("START TRANSACTION");
db.execute("SELECT * FROM users WHERE id=? FOR UPDATE", [user_id]);  // Lock row
db.execute("UPDATE users SET balance=balance-? WHERE id=?", [amount, user_id]);
db.commit();
```

**Tradeoff**: Locks slow down throughput but prevent races.

---

## Implementation Guide: How to Build Durable Systems

Now that you’ve seen the gotchas, here’s a **step-by-step guide** to building durable systems:

### 1. **Design for Failure**
   - Assume **every** operation may fail. Design APIs to be **idempotent** and **retriable**.
   - Example: Use **saga patterns** for long-running workflows.

### 2. **Tune Database Durability**
   - For PostgreSQL: `fsync=on`, `synchronous_commit=on`.
   - For MySQL: `innodb_flush_log_at_trx_commit=1`.
   - Avoid `NO_SYNC` modes unless you accept data loss.

### 3. **Implement Checkpointing**
   - For event-driven systems (Kafka, RabbitMQ), **checkpoint offsets** after successful processing.
   - Example:
     ```python
     # Kafka consumer with checkpointing
     def consume():
         while True:
             message = consumer.poll()
             try:
                 process(message)  # Business logic
                 consumer.commit()  # Checkpoint progress
             except Exception:
                 logger.error("Failed to process", exc_info=True)
     ```

### 4. **Use Compensating Transactions**
   - If a step fails, **undo prior steps** (e.g., release inventory if order cancelation fails).
   - Example (Pseudocode):
     ```python
     try:
         reserve_inventory()
         create_order()
         send_email()
     except:
         release_inventory()  # Compensating transaction
         raise
     ```

### 5. **Monitor Durability Breaches**
   - Log **WAL sync delays** (PostgreSQL: `pg_stat_wal_receiver`).
   - Alert on **transaction timeouts** or **retry storms**.

---

## Common Mistakes to Avoid

1. **Assuming "ACID" = Durable**
   - ACID guarantees **within a transaction**, but not **across failures**. Durability requires **persistent logs** (WAL) and **checkpointing**.

2. **Ignoring Network Partitions**
   - In distributed systems, **network failures ≠ crashes**. Design for **partial failures** (e.g., using CRDTs or operational transformations).

3. **Over-Reliance on "Eventual Consistency"**
   - Eventual consistency is **not** the same as durability. You still need **checkpoints** to recover from crashes.

4. **Not Testing Failures**
   - **Kill database processes mid-transaction** to test durability.
   - Use tools like [PostgreSQL’s `pg_rewind`](https://www.postgresql.org/docs/current/static/app-pgrewind.html) to simulate failures.

5. **Skipping Idempotency**
   - If your API allows retries (e.g., due to `429`), **always** implement idempotency keys.

---

## Key Takeaways

- **Durability ≠ Transactions Alone**: You need **WAL, checkpoints, and compensating transactions** for true durability.
- **Idempotency Saves Lives**: Without it, retries can corrupt data.
- **Locks vs. No Locks**: Pessimistic locks prevent races but slow down systems. Weigh tradeoffs.
- **Monitor Everything**: Log WAL sync times, transaction durations, and retry patterns.
- **Test Failures**: Simulate crashes, network drops, and disk failures in staging.

---

## Conclusion: Build for the Worst

Durability is **not** a one-size-fits-all feature. It’s a **layered discipline** that requires careful design choices at every level—from database tuning to API idempotency to failure recovery. The gotchas we’ve discussed aren’t just theoretical; they’re the **real-world reasons** why systems fail under pressure.

Your next project? Start with these principles:
1. **Assume failures will happen.**
2. **Design for idempotency and retries.**
3. **Tune your database’s durability settings.**
4. **Implement checkpoints and compensating transactions.**

Do these, and your data will survive the storms.

---
**Further Reading**:
- [PostgreSQL WAL Internals](https://www.postgresql.org/docs/current/static/wal-intro.html)
- [Saga Pattern for Distributed Transactions](https://microservices.io/patterns/data/saga.html)
- [Idempotency in APIs: Best Practices](https://www.apigee.com/blog/engineering/what-idempotency-and-why-it-matters-apis)
```