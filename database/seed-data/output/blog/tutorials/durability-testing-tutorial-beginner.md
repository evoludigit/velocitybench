```markdown
---
title: "Durability Testing: Keeping Your Data Safe During Chaos"
description: "Learn about durability testing—how to test your database systems for resilience against crashes, outages, and data loss. Practical examples and real-world lessons for junior backend engineers."
date: 2023-10-15
tags: ["database", "testing", "resilience", "patterns"]
---

# **Durability Testing: Keeping Your Data Safe During Chaos**

Data is the lifeblood of any application. When users rely on your system to store their information—whether it’s customer orders, financial records, or personal preferences—you need absolute confidence that their data won’t vanish if a server crashes, a power outage strikes, or a bug corrupts your database. That’s where **durability testing** comes in.

Durability testing isn’t just about writing unit tests for database operations. It’s about simulating real-world failures—network partitions, disk corruption, or transaction failures—and verifying that your system survives them. If you’ve ever pulled your hair out after a deployment because user data disappeared or transactions were lost, you’ve felt the pain of ignoring durability.

In this guide, we’ll explore what durability testing actually means, why it’s critical, and how to implement it step-by-step. You’ll see concrete examples in Python (with SQLAlchemy) and JavaScript (with MongoDB and Prisma), learn about common pitfalls, and get actionable advice to make your systems robust.

---

## **The Problem: Why Durability Testing Matters**

Most backend engineers focus on writing code that works *in the lab*—under ideal conditions. But in production, chaos reigns. Here are some painful scenarios you’ll face if you skip durability testing:

### 1. **Data Loss After a Crash**
   - You deploy a new feature that uses optimistic concurrency locks, but you forgot to handle `StaleObjectError`.
   - A user’s transaction gets lost because the database connection died mid-write.
   - **Result:** Users lose money, orders disappear, or critical data vanishes.

### 2. **Inconsistent State After a Rollback**
   - Your service writes to multiple databases (e.g., PostgreSQL for orders and Redis for caching). If one succeeds but the other fails, your system is left in an inconsistent state.
   - **Result:** Users see stale data or get "invalid state" errors.

### 3. **Race Conditions Under High Load**
   - Your API allows parallel requests to update the same record (e.g., modifying a user’s profile).
   - Without proper locking or transaction isolation, the second request might overwrite the first.
   - **Result:** Corrupted data or race conditions that crash your app.

### 4. **Slow Recovery from Failures**
   - Your database goes offline for 10 minutes. When it comes back, some transactions are lost because you didn’t enable `RETRY` logic.
   - **Result:** Downtime that lasts longer than necessary.

### 5. **Hidden Bugs in Distributed Systems**
   - You use Kafka for event sourcing, but a producer fails to acknowledge a message after writing to the queue.
   - **Result:** Events are duplicated or lost, leading to inconsistent state across services.

---
## **The Solution: Durability Testing Patterns**

Durability testing isn’t one monolithic approach—it’s a combination of strategies to ensure your system survives failures. Here’s how we’ll tackle it:

1. **Test for Atomicity**: Verify that transactions either complete fully or not at all.
2. **Simulate Failures**: Force crashes, network partitions, and timeouts to see how your app reacts.
3. **Check for Isolation**: Ensure concurrent operations don’t corrupt data.
4. **Validate Recovery**: Test how your system restores from backups or failed states.
5. **Monitor for Side Effects**: Catch cases where one failure cascades into others.

We’ll use **three real-world examples**:
   - A **Python/PostgreSQL** order processing system (with SQLAlchemy).
   - A **Node.js/MongoDB** user profile service (with Prisma).
   - A **distributed microservice** example with Kafka.

---

## **Components/Solutions**

### 1. **Atomicity Testing**
   Ensure transactions are either fully committed or fully rolled back.

   **Example: SQLAlchemy (Python)**
   ```python
   from sqlalchemy import create_engine, Column, Integer, String
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy.orm import sessionmaker

   Base = declarative_base()

   class Order(Base):
       __tablename__ = 'orders'
       id = Column(Integer, primary_key=True)
       user_id = Column(Integer)
       amount = Column(Integer)
       status = Column(String)

   # Test setup
   engine = create_engine('postgresql://user:pass@localhost/test_db')
   Base.metadata.create_all(engine)
   Session = sessionmaker(bind=engine)

   def place_order(user_id, amount):
       session = Session()
       try:
           # Simulate a failure (e.g., network timeout)
           if amount < 0:  # Invalid amount → rollback
               raise ValueError("Negative amount")

           order = Order(user_id=user_id, amount=amount, status="pending")
           session.add(order)
           session.commit()  # Atomic commit
       except Exception as e:
           session.rollback()  # Rollback on failure
           print(f"Failed to place order: {e}")
           raise
       finally:
           session.close()

   # Test durability: Force a rollback
   place_order(1, -100)  # Should rollback due to invalid amount
   ```

   **Key Takeaway:** Always wrap database operations in a `try-except-finally` block to ensure rollbacks.

---

### 2. **Failure Injection Testing**
   Simulate crashes, timeouts, and network failures.

   **Example: MongoDB with Prisma (Node.js)**
   ```javascript
   import { PrismaClient } from '@prisma/client'

   const prisma = new PrismaClient()

   async function updateUserProfile(userId, { name, email }) {
       try {
           // Simulate a slow network call (e.g., 5s delay)
           await new Promise(resolve => setTimeout(resolve, 5000))

           // Update user
           await prisma.user.update({
               where: { id: userId },
               data: { name, email }
           })
           console.log("Profile updated successfully")
       } catch (error) {
           if (error.code === 'ETIMEDOUT') {
               console.error("Network timeout! Retrying...")
               await updateUserProfile(userId, { name, email })  // Retry
           } else {
               throw error
           }
       }
   }

   // Run the function with a forced timeout
   updateUserProfile(1, { name: "Alice", email: "alice@example.com" })
   ```

   **Key Takeaway:** Use **exponential backoff** in retries to avoid overwhelming systems.

---

### 3. **Concurrency Testing**
   Ensure thread-safe operations under high load.

   **Example: PostgreSQL with SQLAlchemy (Python)**
   ```python
   from concurrent.futures import ThreadPoolExecutor

   def modify_user_balance(user_id, amount):
       session = Session()
       try:
           user = session.query(User).get(user_id)
           user.balance += amount
           session.commit()
       except Exception as e:
           session.rollback()
           raise e
       finally:
           session.close()

   # Simulate concurrent updates (race condition potential)
   with ThreadPoolExecutor(max_workers=10) as executor:
       executor.map(lambda: modify_user_balance(1, 100), range(20))
   ```

   **Fix:** Use `SELECT FOR UPDATE` to lock rows during edits.
   ```python
   user = session.query(User).with_for_update().get(user_id)  # Lock row
   ```

   **Key Takeaway:** Always use **pessimistic locks** (`FOR UPDATE`) for critical operations.

---

### 4. **Recovery Testing**
   Test how your system handles backups and restores.

   **Example: Kafka Event Sourcing (Pseudocode)**
   ```python
   # Simulate a Kafka producer failure
   def produce_event(event):
       try:
           producer.send(event)  # May fail (network issues)
           producer.flush()      # Wait for acknowledgment
       except Exception as e:
           print(f"Failed to produce event: {e}")
           # Fallback: Write to a local queue for retry later
           local_queue.append(event)

   # Later, replay local queue if Kafka is down
   for event in local_queue:
       produce_event(event)
   ```

   **Key Takeaway:** Implement **idempotent operations** (e.g., dedupe events).

---

## **Implementation Guide**

Here’s a step-by-step plan to add durability testing to your project:

### 1. **Create Test Doubles for Databases**
   Use tools like:
   - **Testcontainers** (run real DBs in Docker for tests).
   - **Mock databases** (e.g., `pytest-mock` for SQLAlchemy).
   - **Fake databases** (e.g., `sqlite3` for fast local testing).

   **Example with Testcontainers (Python):**
   ```python
   from testcontainers.postgres import PostgresContainer

   with PostgresContainer("postgres:13") as db:
       db.start()
       engine = create_engine(f"postgresql://{db.get_connection_uri()}")
       # Run durability tests here
   ```

### 2. **Inject Failures Manually**
   Use libraries like:
   - **Chaos Engineering Tools** (e.g., [Gremlin](https://www.gremlin.com/), [Chaos Mesh](https://chaos-mesh.org/)).
   - **Custom timeouts** (e.g., force `TimeoutException` in tests).

   **Example with Python’s `unittest.mock`:**
   ```python
   from unittest.mock import patch

   def test_order_rollback_on_failure():
       with patch('sqlalchemy.engine.Connection.execute', side_effect=Exception("DB crash")):
           with pytest.raises(Exception):
               place_order(1, 100)
   ```

### 3. **Use Transaction Logs**
   Enable **WAL (Write-Ahead Logging)** in PostgreSQL or **MongoDB oplog** to verify durability.

   **PostgreSQL Example:**
   ```sql
   -- Check WAL settings
   SHOW wal_level;  -- Should be "replica" or "logical"
   ```

### 4. **Automate Recovery Tests**
   Write scripts to:
   - Restore from backups.
   - Verify data consistency after a crash.
   - Test failover scenarios.

   **Example Bash Script:**
   ```bash
   # Simulate a crash, then recover
   docker stop postgres_db
   docker start postgres_db
   psql -U postgres -d test_db -c "SELECT COUNT(*) FROM orders;"  # Verify data
   ```

### 5. **Monitor for Side Effects**
   Use tools like:
   - **Prometheus/Grafana** to track retry attempts.
   - **Sentry** to log durability failures.

---

## **Common Mistakes to Avoid**

1. **Ignoring Retry Logic**
   - ❌ Don’t assume `TRY` or `EXECUTE` will auto-retry.
   - ✅ Always implement retries with backoff.

2. **Overusing Optimistic Locking**
   - ❌ `VERSION` fields in SQL can cause deadlocks under high load.
   - ✅ Prefer `FOR UPDATE` for critical operations.

3. **Not Testing Partial Failures**
   - ❌ Test only complete successes/failures, not mixed scenarios.
   - ✅ Simulate partial transactions (e.g., one DB succeeds, another fails).

4. **Skipping Recovery Testing**
   - ❌ Assume backups work perfectly.
   - ✅ Test restore procedures regularly.

5. **Assuming ACID is Enough**
   - ❌ ACID guarantees atomicity/commit, but not **durability** in distributed systems.
   - ✅ Use distributed transaction managers (e.g., Saga pattern, compensating transactions).

---

## **Key Takeaways**

✅ **Durability testing is not optional**—it’s how you prevent data loss in production.
✅ **Atomicity first**: Always wrap DB ops in transactions with `COMMIT`/`ROLLBACK`.
✅ **Simulate failures**: Use chaos engineering tools to test resilience.
✅ **Concurrency is tricky**: Use locks (`FOR UPDATE`) or optimistic locking carefully.
✅ **Automate recovery**: Test backup/restore procedures as part of CI/CD.
✅ **Monitor failures**: Log retries, timeouts, and partial successes.

---

## **Conclusion**

Durability testing is the difference between a reliable system and one that crumbles under pressure. By following the patterns in this guide—atomic transactions, failure injection, concurrency control, and recovery testing—you’ll build applications that survive crashes, network issues, and bugs.

Start small:
1. Add a basic retry mechanism to your database calls.
2. Simulate a single failure in your tests.
3. Gradually expand to more complex scenarios.

Your users (and your sanity) will thank you.

---
**Further Reading:**
- [PostgreSQL’s Durability Guide](https://www.postgresql.org/docs/current/runtime-config-wal.html)
- [Chaos Engineering Principles (Netflix)](https://chaosengineering.io/)
- [Saga Pattern for Distributed Transactions](https://microservices.io/patterns/data/saga.html)

**Got questions?** Drop them in the comments or tweet at me @backend_guide. Happy testing!
```

---
**Notes for the author:**
- Expanded code examples with clear context.
- Added real-world tradeoffs (e.g., locks vs. retries).
- Included actionable advice for beginners.
- Structured for readability with actionable sections.
- Balanced theory with practical steps.