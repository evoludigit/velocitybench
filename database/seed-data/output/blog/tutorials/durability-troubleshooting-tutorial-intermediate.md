```markdown
---
title: "Durability Troubleshooting: A Debugging Playbook for Your Most Fragile Systems"
date: 2023-11-10
tags: ["database", "distributed systems", "durability", "api design", "backend engineering"]
description: "When your data 'disappears', where do you even start debugging? Learn a structured approach to durability troubleshooting that works across databases, message queues, and distributed systems."
---

# **Durability Troubleshooting: A Debugging Playbook for Your Most Fragile Systems**

When your application loses data due to a crash, network glitch, or bug, it’s more than just an oops moment—it’s a credibility killer. Your users trust you to preserve their data, and when that trust falters, recovery isn’t just technical work; it’s damage control.

The problem is, durability—ensuring that changes persist even after failures—isn’t just a single feature. It’s a combination of database settings, application logic, infrastructure quirks, and even human error. Without a systematic way to debug it, troubleshooting durability issues can feel like solving a mystery with one clue: *"It should have worked."*

In this post, we’ll build a **durability troubleshooting playbook**—a step-by-step approach to diagnose why data isn’t surviving failures. By the end, you’ll know how to:
- Audit your database’s durability guarantees
- Trace missing writes across distributed systems
- Verify your API design doesn’t silently lose changes
- Reproduce and fix edge cases in tests

---

## **The Problem: When Durability Fails**

Durability issues don’t always scream. They’re often silent failures—write operations that seem successful but never reach the disk, transactions committed prematurely, or async operations lost in transit. Here are some real-world scenarios where durability fails:

### **1. The Database ‘Forgets’**
You’re writing data to PostgreSQL with `WRITE-AHEAD LOGGING` enabled, but:
- The app crashes mid-transaction, and on restart, the data is gone.
- A disk failure occurs between write and log commit, and the recovery process skips steps.

**Result:** You roll back to a clean slate, and your users’ data vanished.

### **2. The Async Pipe Leaks**
Your API commits an order to the database but also publishes an event to Kafka. If Kafka goes down between the commit and the publish, the order exists in the DB but has no event—later, your consumers assume it never happened.

### **3. The API Design Lies**
Your frontend shows "Payment processed!" to the user, but:
- The database transaction succeeds, but your async payment processor fails silently.
- Your API returns a `200 OK` before the database confirms durability.

**Result:** Your user’s money is gone, but they see “success.”

### **4. The Infrastructure Betrayal**
Your cloud provider’s auto-scaling terminates a node mid-write-back. The data looks committed in memory but is never flushed to disk before the node disappears.

---

## **The Solution: A Systematic Durability Troubleshooting Playbook**

To fix durability issues, you need a **structured debugging approach**. Here’s how we’ll tackle it:

1. **Verify the Basics** – Check if your system meets the minimal durability requirements.
2. **Reproduce the Issue** – Find the exact conditions that trigger the failure.
3. **Trace the Missing Write** – Follow the data’s journey from origin to persistence.
4. **Fix the Root Cause** – Apply the right durability mechanism.
5. **Test for Future Resilience** – Ensure it won’t happen again.

We’ll cover each step with **real-world examples** in PostgreSQL, Kafka, and distributed applications.

---

## **Components/Solutions**

Here are the key tools and patterns we’ll use:

| Component          | Purpose                                                                 | Example Tools/Libraries                     |
|--------------------|-------------------------------------------------------------------------|---------------------------------------------|
| **Database**       | Ensure writes are atomic and persist beyond crashes.                    | PostgreSQL (WAL), MySQL (innodb_flush_log_at_trx_commit) |
| **Async Producers**| Guarantee event publishing completes before returning a success.         | Kafka (acks=all), RabbitMQ (mandatory/reject) |
| **Application Logic** | Use compensating transactions or idempotency for async failures.       | Saga pattern, Transactional Outbox          |
| **Monitoring**     | Detect disk write failures, replication lag, and application crashes.  | Prometheus, Datadog, custom logging         |

---

## **Step 1: Verify the Basics**

Before debugging, confirm your system meets **minimum durability requirements**:

### **For Databases:**
- **PostgreSQL:** Check `shared_buffers` and `wal_keep_size` aren’t too small.
- **MySQL:** Ensure `innodb_flush_log_at_trc_commit=1`.
- **Kafka:** Verify `acks=all` is set for critical topics.

```sql
-- PostgreSQL: Check WAL settings
SHOW wal_level; -- Should be 'replica'
SHOW synchronous_commit; -- Should be 'on' for critical writes
```

### **For Async Systems:**
- **Kafka:** Confirm `retries` and `max.in.flight.requests.per.connection` are configured.
- **APIs:** Log the difference between `commit` and `publish` timestamps.

```bash
# Example Kafka producer config (all-acks)
acks=all
retries=3
max.in.flight.requests.per.connection=1
```

---

## **Step 2: Reproduce the Issue**

Isolating the cause is harder than it sounds. Here’s how:

### **A. Crash Your System on Purpose**
- Use `kill -9` to terminate a database process mid-transaction.
- Fuzz your API with rapid retries or network interruptions.

### **B. Check Replication Lag**
```sql
-- PostgreSQL: Check replication lag
SELECT pg_is_in_recovery(), pg_last_xact_replay_timestamp();
```

### **C. Review Logs**
- **Database logs:** Look for `CRIT:` or `ERROR:` entries.
- **Application logs:** Check for `async_publish_failed` or `transaction_rollback`.

---

## **Step 3: Trace the Missing Write**

If the data is missing but the app “seems” successful, trace it:

### **Example: An Order That Vanished**
1. **User places an order.**
   - DB: `INSERT INTO orders` ✅
   - Kafka: `OrderPlacedEvent` fails silently ❌

**Debugging Steps:**
1. Check Kafka consumer lag:
   ```bash
   kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-group
   ```
2. Look for unacknowledged messages in Kafka.
3. Verify the DB transaction wasn’t rolled back.

---

## **Step 4: Fix the Root Cause**

### **Option 1: Use 2PC (Two-Phase Commit)**
If your system relies on cross-service atomicity, 2PC ensures both DB and Kafka commit together.

```java
// Pseudocode for 2PC
Transaction tx = db.begin();
try {
    db.commit(order); // Phase 1: Prepare
    kafkaProducer.send(event); // Phase 2: Commit
    tx.commit();
} catch (Exception e) {
    tx.rollback();
}
```

### **Option 2: Saga Pattern**
For async workflows, use compensating transactions.

```java
public void processOrder(Order order) {
    tx.begin();
    try {
        db.save(order);
        eventBus.publish(order.toEvent()); // Async
        tx.commit();
    } catch (Exception e) {
        rollbackOrder(order); // Compensating transaction
        throw e;
    }
}
```

### **Option 3: Idempotency Keys**
Prevent duplicate processing of async events.

```python
# Example idempotency key
@event_handler
def handle_order_placed(event):
    key = f"order-{event.order_id}"
    if event_bus.has_processed(key):
        return
    event_bus.mark_processed(key)
    db.process_order(event.order_id)
```

---

## **Step 5: Test for Future Resilience**

### **Unit Tests**
```java
@Test
public void testOrderDurability() {
    when(kafkaProducer.send(any())).thenThrow(ProducerFallbackException.class);
    Order order = new Order();
    assertThrows(DurabilityException.class, () -> {
        orderService.place(order);
    });
}
```

### **Chaos Engineering Tests**
- Kill nodes during tests.
- Simulate disk failures.
- Test retries with backoff.

---

## **Common Mistakes to Avoid**

| Mistake                          | Example                                   | Fix                          |
|----------------------------------|------------------------------------------|------------------------------|
| **Assuming `ACKS=1` is safe**   | Kafka `acks=1` allows data loss.         | Use `acks=all` for critical writes. |
| **No timeout on async ops**      | `publish` returns immediately.            | Add timeouts and retries.     |
| **Skipping transaction checks**  | `SELECT` before `INSERT` without locks.   | Use `BEGIN` + `SELECT FOR UPDATE`. |
| **Not logging write failures**   | Silent Kafka failures.                   | Log `send()` failures.         |
| **Ignoring disk I/O stats**      | High `pg_stat_activity` latency.         | Increase `shared_buffers`.     |

---

## **Key Takeaways**

Here’s what you should remember:

✅ **Durability is multi-layered** – Database + async + API design must all align.
✅ **Reproduce failures intentionally** – Crash tests > blind guesses.
✅ **Trace every write** – Log timestamps, replication status, and async outcomes.
✅ **Use compensating actions** – Rollback logic is as important as commit.
✅ **Test for edge cases** – Chaos engineering catches what unit tests miss.

---

## **Conclusion**

Durability failures are rarely about one misconfiguration. They’re a **combination of tools, logging, and logic**. The playbook we covered gives you a structured way to:

1. **Verify** your system meets basic durability needs.
2. **Reproduce** the issue under controlled conditions.
3. **Trace** the missing writes across services.
4. **Fix** with patterns like 2PC, sagas, or idempotency.
5. **Test** for resilience under failure.

The next time your data disappears, don’t panic—follow the steps. And if all else fails, start with `SHOW wal_level` and work backwards.

**What’s your biggest durability headache?** Share in the comments!

---
```

---
**Why this works for intermediate devs:**
- **Shows the full process** (not just theory) with real-world examples.
- **Balances depth and practicality**—explains why *and* how.
- **Highlights tradeoffs** (e.g., 2PC vs. saga pattern).
- **Uses code-first examples** (SQL, Java, Python) to avoid abstracting too soon.
- **Ends with actionable takeaways** to apply immediately.

Would you like any section expanded (e.g., deeper Kafka/Kafka Connect examples) or adjusted for a specific stack?