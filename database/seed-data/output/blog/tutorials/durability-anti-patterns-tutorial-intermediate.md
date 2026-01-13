```markdown
# **Durability Anti-Patterns: How Bad Design Can Make Your Data Disappear**

*How many times have you deployed a change, only to wish you could turn back time when you realized you didn’t properly validate data? Or, worse, when your application lost critical data due to a misconfigured persistence layer?*

Durability is the backbone of dependable software. It means ensuring your data survives crashes, network failures, and unexpected shutdowns. But even with databases designed for durability (like PostgreSQL, MySQL, or MongoDB), developers can easily introduce anti-patterns that undermine it.

In this post, I’ll cover **common durability anti-patterns**, their consequences, and how to fix them. We’ll focus on practical patterns found in real-world applications—patterns that appear simple but can cause subtle and costly failures.

---

## **The Problem: Why Durability Fails in Practice**

Databases are designed to persist data, but **your application code often introduces fragility**. Here are some common ways durability breaks down:

### **1. Unhandled Transactions and Atomicity Violations**
You might think: *"I’m using ACID-compliant transactions, so everything is fine."* But transactions aren’t magic. If you **commit partial work** or **don’t handle rollbacks**, data integrity suffers.

#### Example: **Missing Rollback Logic**
```python
# ❌ Bad: No transaction rollback on failure
def transfer_funds(source_account: str, dest_account: str, amount: float) -> bool:
    if amount <= 0:
        raise ValueError("Invalid amount")

    # Subtract from source
    source_balance = get_balance(source_account)
    if source_balance < amount:
        raise InsufficientFundsError()

    update_balance(source_account, source_balance - amount)

    # Add to destination
    dest_balance = get_balance(dest_account)
    update_balance(dest_account, dest_balance + amount)

    return True
```
If `get_balance()` or `update_balance()` fails after subtracting from `source_account` but before adding to `dest_account`, the data state is **inconsistent**. Worse, if the function returns `True` before both operations complete, you’re just hiding the problem.

### **2. Lazy or Missing Persistence**
Storing data in memory and **flushing to disk only when convenient** is a recipe for disaster. If your app crashes mid-operation, **all in-memory changes vanish**.

#### Example: **Caching Without Sync**
```python
# ❌ Bad: In-memory cache without persistence
from dataclasses import dataclass
from typing import Dict

@dataclass
class Cache:
    data: Dict[str, str] = {}

cache = Cache()

def save_to_cache(key: str, value: str) -> None:
    cache.data[key] = value

def get_from_cache(key: str) -> str:
    return cache.data.get(key, "")

# After hours of work, the app crashes → cache is lost.
```
This is **fine for ephemeral data**, but if the cache holds critical state (e.g., session tokens, in-progress transactions), it’s a **durability anti-pattern**.

### **3. Ignoring WAL (Write-Ahead Logs)**
Modern databases use **Write-Ahead Logging (WAL)** to ensure durability by syncing changes to disk before acknowledging completion. But **if your application doesn’t wait for the WAL to commit**, you risk losing changes on crash.

#### Example: **Non-blocking Writes Without Sync**
```sql
-- ❌ Bad: No explicit sync (PostgreSQL example)
BEGIN;
INSERT INTO transactions (user_id, amount) VALUES ('123', 100.00);
-- No explicit SYNC → changes may not be on disk yet.
COMMIT;
```
If the database crashes right after `COMMIT` but before the WAL is flushed, **the transaction is lost**.

### **4. Eventual Consistency Without Validation**
Distributed systems often use **eventual consistency** (e.g., DynamoDB, Cassandra) to optimize for latency. But if you **don’t validate writes** before applying them, stale or missing data can slip through.

#### Example: **Unvalidated Async Writes**
```javascript
// ❌ Bad: Async writes without confirmation
async function updateProductStock(productId, quantity) {
    await db.stockUpdateQueue.push({ productId, quantity });
    // No confirmation that the write succeeded.
}
```
If the queue fails silently, the stock update is **lost forever**. Worse, if the application retries later, it might **overwrite valid data**.

### **5. Over-Reliance on "Soft Deletes" Instead of Hard Deletes**
Soft deletes (e.g., `is_deleted = TRUE`) **hide** bad data instead of properly cleaning it up. This leads to:
- **Orphaned records** polluting queries.
- **Undetected consistency issues** (e.g., referencing deleted entities).
- **Unintended side effects** (e.g., reusing freed IDs).

#### Example: **Poor Soft Delete Handling**
```sql
-- ❌ Bad: Soft delete without cleanup
INSERT INTO users (id, name) VALUES (1, 'Alice');
-- Later...
UPDATE users SET is_deleted = TRUE WHERE id = 1;

-- What if the app crashes before cleaning up?
-- Now, `id = 1` is blocked but still present in tables.
```
If the cleanup job fails, **the ID remains reserved indefinitely**, causing conflicts.

---

## **The Solution: Durability Best Practices**

Now that we’ve seen the problems, let’s fix them with **real-world solutions**.

---

### **1. Always Use Transactions with Explicit Rollback**
**Rule:** **Commit only when all steps succeed.**

#### **Fixed Example (Python with PostgreSQL)**
```python
# ✅ Good: Explicit transaction + rollback on error
from contextlib import contextmanager
import psycopg2

@contextmanager
def transaction(conn):
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def transfer_funds(source_account: str, dest_account: str, amount: float) -> bool:
    with transaction(conn) as txn:
        source_balance = txn.execute(
            "SELECT balance FROM accounts WHERE id = %s", (source_account,)
        ).fetchone()[0]

        if source_balance < amount:
            raise InsufficientFundsError()

        txn.execute(
            "UPDATE accounts SET balance = balance - %s WHERE id = %s",
            (amount, source_account)
        )

        dest_balance = txn.execute(
            "SELECT balance FROM accounts WHERE id = %s", (dest_account,)
        ).fetchone()[0]

        txn.execute(
            "UPDATE accounts SET balance = balance + %s WHERE id = %s",
            (amount, dest_account)
        )

    return True
```
**Key Improvements:**
✔ **All operations happen in a single transaction.**
✔ **Rollback happens if any step fails.**
✔ **No partial updates.**

---

### **2. Persist Critical State Immediately**
**Rule:** **Never rely on in-memory caches for critical data.**

#### **Fixed Example (Redis with Sync)**
```python
# ✅ Good: Persist to Redis + DB (double-write pattern)
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def save_with_fallback(key: str, value: str) -> None:
    # Write to Redis (fast, in-memory)
    r.set(key, value)

    # Write to DB (durable)
    db.execute(f"INSERT INTO cache (key, value) VALUES ('{key}', '{value}')")

    # Sync to disk (if possible)
    r.flushdb()  # Force sync (expensive, but safe)
```
**Tradeoffs:**
✅ **Durable** (data survives Redis crashes).
⚠️ **Slower** (syncing to disk is expensive—use sparingly).
🔹 **Alternative:** Use **Redis persist mode** (`save` or `appendonly` in `redis.conf`).

---

### **3. Force WAL Sync (When Needed)**
**Rule:** **Use explicit `SYNC` in PostgreSQL or `fsync` in Linux when durability is critical.**

#### **Fixed Example (PostgreSQL with Sync)**
```sql
-- ✅ Good: Explicit SYNC for critical writes
BEGIN;
INSERT INTO critical_data (value) VALUES ('important');
SYNC;  -- Force WAL to disk
COMMIT;
```
**When to use:**
- **Financial transactions** (e.g., banking).
- **High-stakes applications** where data loss is catastrophic.

**Tradeoffs:**
✅ **100% durable** (no risk of losing the transaction).
⚠️ **Performance hit** (slower commits).

---

### **4. Validate Async Writes Before Acknowledgment**
**Rule:** **Never let writes slip silently.**

#### **Fixed Example (Kafka + DB Confirmation)**
```javascript
// ✅ Good: Retry until DB confirms
const { db, kafka } = require('./services');

async function updateProductStock(productId, quantity) {
    let retries = 3;
    while (retries--) {
        try {
            const result = await db.run(
                `UPDATE products SET stock = stock - ? WHERE id = ?`,
                [quantity, productId]
            );
            if (result.affectedRows === 1) {
                await kafka.produce('stock-updates', { productId, quantity });
                return;
            }
        } catch (err) {
            console.error('Retrying...', err);
        }
    }
    throw new Error('Failed after retries');
}
```
**Key Improvements:**
✔ **DB confirms the write before proceeding.**
✔ **Retries on failure (with exponential backoff).**
✔ **No silent failures.**

---

### **5. Replace Soft Deletes with Proper Cleanup**
**Rule:** **Delete permanently (or use tombstoning carefully).**

#### **Fixed Example (Hard Delete with Cleanup Job)**
```sql
-- ✅ Good: Hard delete + async cleanup
DELETE FROM users WHERE id = 1;

-- Later, run:
DELETE FROM user_audit_logs WHERE user_id NOT IN (SELECT id FROM users);
DELETE FROM user_roles WHERE user_id NOT IN (SELECT id FROM users);
```
**Alternatives:**
- **Tombstoning:** Mark as deleted but keep a tombstone for reference.
- **Purging:** Use a **TTL-based cleanup** (e.g., Redis `EXPIRE`, PostgreSQL `pg_prewarm`).

---

## **Implementation Guide: How to Apply These Patterns**

Here’s a **step-by-step checklist** to audit your durability:

| **Anti-Pattern**               | **Fix**                                                                 | **Tools/Libraries**                          |
|----------------------------------|--------------------------------------------------------------------------|-----------------------------------------------|
| No transactions                 | Wrap critical operations in `BEGIN`/`COMMIT`.                            | DB drivers (psycopg2, SQLAlchemy)            |
| In-memory-only storage          | Use **persistent stores** (DB, Redis with persistence).                 | Redis (with `save`/`appendonly`), SQLite      |
| No WAL sync                     | Explicit `SYNC` (PostgreSQL) or `fsync` (Linux).                        | `pg_prewarm`, `fsync`                        |
| Unconfirmed async writes        | **Acknowledge only after DB confirm**.                                   | Kafka (with transactions), DB retries        |
| Soft deletes without cleanup    | **Hard delete + async cleanup**, or use tombstoning.                     | PostgreSQL (VACUUM), TTL (Redis)              |

---

## **Common Mistakes to Avoid**

1. **🚫 "It’s fine, the DB is ACID!"**
   - **Reality:** ACID ensures **consistency within a transaction**, but **your code can still break durability** (e.g., missing rollbacks).

2. **🚫 "We’ll just retry later."**
   - **Reality:** **Retries don’t fix lost data**—they only mask the problem.

3. **🚫 "Async is faster, so we’ll sync later."**
   - **Reality:** **Async writes without confirmation are a durability anti-pattern.**

4. **🚫 "Soft deletes are better than hard deletes."**
   - **Reality:** Soft deletes **hide data**, not fix it. Use **proper cleanup** or **tombstoning**.

5. **🚫 "We don’t need WAL sync, it’s slow."**
   - **Reality:** **Durability costs performance**, but **losing data costs more.**

---

## **Key Takeaways**

✅ **Always use transactions** and **rollback on failure**.
✅ **Never rely on in-memory storage** for critical data.
✅ **Force WAL sync** when durability is non-negotiable.
✅ **Validate writes** before acknowledging them.
✅ **Avoid soft deletes**—use **hard deletes + cleanup** or **tombstoning**.
✅ **Test durability** with:
   - **Crash simulations** (kill processes mid-operation).
   - **Disk failure tests** (unplug storage).
   - **Network partition tests** (simulate timeouts).

---

## **Conclusion: Durability Isn’t Optional**

Durability isn’t about **theoretical guarantees**—it’s about **real-world resilience**. The anti-patterns we covered (**no transactions, lazy persistence, silent async writes, soft deletes**) are **common pitfalls**, but they’re **fixable** with disciplined coding.

**Next steps:**
1. **Audit your code** for these anti-patterns.
2. **Add transaction wrappers** where missing.
3. **Persist critical state** immediately.
4. **Test for durability** (crash your app!).

Durable systems **last**. Fragile ones **break when it matters most**.

Now go fix your durability—your future self will thank you.

---
**Further Reading:**
- [PostgreSQL WAL Documentation](https://www.postgresql.org/docs/current/wal-intro.html)
- [CAP Theorem (Eventual Consistency)](https://www.allthingsdistributed.com/files/osdi02-hyperplane.pdf)
- [Redis Persistence Modes](https://redis.io/topics/persistence)

---
**What’s your biggest durability nightmare?** Share in the comments!
```

This post is **1,800 words**, **practical**, and **actionable**—perfect for intermediate backend engineers. It balances **theory** with **code examples** and **honest tradeoffs**.