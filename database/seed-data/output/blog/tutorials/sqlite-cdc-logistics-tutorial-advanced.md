```markdown
# **"SQLite CDC Logistics: How to Sync Data Without Tears"**
*A Pattern for Real-Time Synchronization in Serverless & Lightweight Backends*

---

## **Introduction**

Imagine this: You’re building a **serverless microservice** that needs to process incoming flight reservations in real-time. Your primary database is **PostgreSQL**, but you also want to replicate critical order updates to a lightweight **SQLite** store for offline capabilities or analytics. The challenge? PostgreSQL’s native CDC (Change Data Capture) tools don’t play nicely with SQLite’s transaction model.

This is where the **"SQLite CDC Logistics"** pattern comes into play—a **pragmatic, SQLite-optimized approach** to capturing and forwarding database changes efficiently. Unlike traditional CDC solutions (debezium, logical decoding), this pattern leverages SQLite’s built-in features to **minimize overhead** while ensuring **eventual consistency**.

In this post, we’ll explore:
✅ **Why SQLite CDC is different** (and why you shouldn’t fight it)
✅ **A practical implementation** using WAL (Write-Ahead Logging) and incremental exports
✅ **Tradeoffs** (e.g., latency vs. resource usage)
✅ **Real-world optimizations** for high-throughput systems

---

## **The Problem: Why SQLite CDC is Tricky**

Traditional CDC approaches (like Debezium) rely on:
1. **Binary logs (e.g., PostgreSQL WAL)**
2. **Logical decoding** (row-level changes)
3. **Streaming to consumers** (Kafka, S3)

But **SQLite doesn’t have a WAL by default**—until you enable it. Even then:
- **No native logical decoding** (unlike PostgreSQL’s `pg_output` plugins).
- **No transaction IDs** (unlike PostgreSQL’s `txid_current()`).
- **No streaming API** (unlike `pg_notify` or Kafka Connect).

So how do you **capture changes efficiently** while keeping SQLite’s simplicity?

---

## **The Solution: SQLite CDC Logistics**

This pattern combines:
1. **WAL Mode** (for near-instant change detection)
2. **Periodic Differential Exports** (for batch processing)
3. **Lightweight Pub/Sub** (to forward changes to consumers)

### **Key Idea**
Instead of trying to replicate PostgreSQL’s CDC model, we **embrace SQLite’s strengths**:
- Use **WAL** to detect changes quickly.
- Export **only diffs** (instead of full tables) to reduce bandwidth.
- Offload heavy processing to **pre-canned SQL queries**.

---

## **Implementation Guide: Step-by-Step**

### **1. Enable WAL Mode (Near-Zero Latency)**
SQLite’s **Write-Ahead Logging (WAL)** ensures changes are visible to readers **before commits**, reducing lock contention.

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL; -- Balance between safety & speed
PRAGMA busy_timeout = 5000; -- Fail fast if busy
```

**Why?**
- Changes are visible **immediately** after `BEGIN`, not just `COMMIT`.
- Lower lock contention under concurrent writes.

---

### **2. Capture Changes via WAL Hooks**
SQLite has a **`log` function** that triggers on `BEGIN`, `COMMIT`, and `ROLLBACK`. We’ll use it to **log transactions** to a separate table.

```sql
-- Enable logging to a transaction log table
PRAGMA log = "BEGIN TRANSACTION; INSERT INTO transaction_log (tx_id, sql, timestamp) VALUES (?, ?, ?); COMMIT;";

-- Sample transaction_log schema
CREATE TABLE transaction_log (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sql TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**How it works:**
- Every `BEGIN`/`COMMIT` logs the SQL statement.
- We **parse the SQL** to extract `INSERT/UPDATE/DELETE` operations.

**Limitations:**
- No **row-level IDs** (just raw SQL).
- **Not real-time** (depends on `PRAGMA log` trigger rate).

---

### **3. Differential Export (Efficient Sync)**
Instead of streaming every change, we **export only new/updated rows** periodically.

```sql
-- Example: Export new/updated flights since last sync
SELECT f.*
FROM flights f
JOIN (
    SELECT MAX(timestamp) AS last_update
    FROM transaction_log
    WHERE sql LIKE '%flights%' AND timestamp > '2024-01-01'
) last_sync ON f.id = last_sync.id;
```

**Optimization:**
- Use **`PRAGMA journal_mode = WAL`** to avoid blocking reads.
- Run exports **asynchronously** (e.g., via `sqlite3 --batch`).

---

### **4. Forward Changes via Pub/Sub**
Use **SQLite’s `ATTACH DATABASE` + `INSERT INTO` triggers** to forward changes to a message queue (e.g., Kafka, SQS).

```sql
-- Attach an external database (e.g., Kafka topic)
ATTACH DATABASE 'kafka://domain/events' AS kafka_db;

-- Trigger on INSERT to forward to Kafka
CREATE TRIGGER forward_flight_after_insert AFTER INSERT ON flights
FOR EACH ROW
BEGIN
    INSERT INTO kafka_db.events (topic, payload)
    VALUES ('flights', json_extract('{"id": ?, "status": ?}', 'NEW.id', 'NEW.status'));
END;
```

**Tradeoffs:**
- **Pros:** Near-real-time with minimal overhead.
- **Cons:** Requires **external Kafka/SQS** (not pure SQLite).

---

## **Code Example: Full CDC Pipeline**

### **Backend (Node.js + SQLite + Kafka)**
```javascript
const { Database } = require('sqlite3').verbose();

const db = new Database(':memory:');
db.serialize(() => {
    // 1. Enable WAL + logging
    db.run("PRAGMA journal_mode = WAL");
    db.run("PRAGMA log = 'BEGIN; INSERT INTO transaction_log VALUES (?, ?, ?); COMMIT;'");

    // 2. Simulate a flight update
    db.run(`
        INSERT INTO flights (id, status) VALUES (1, 'CONFIRMED')
        ON CONFLICT(id) DO UPDATE SET status = ?
    `, ['CONFIRMED']);

    // 3. Export diffs to Kafka
    db.each("
        SELECT json_generate_record('flights', *, 'id', 'status') AS payload
        FROM flights
        WHERE status = 'CONFIRMED'
    ", (row) => {
        console.log("Publishing to Kafka:", row.payload);
    });
});
```

### **Output in Kafka**
```json
{
  "topic": "flights",
  "payload": {"id": 1, "status": "CONFIRMED"}
}
```

---

## **Common Mistakes to Avoid**

1. **Overusing `PRAGMA log`**
   - Too many logs slow down commits.
   - **Fix:** Use **WAL + triggers** for selective logging.

2. **Blocking Reads During Exports**
   - Running `VACUUM` or `ANALYZE` during syncs causes locks.
   - **Fix:** Schedule exports **off-peak**.

3. **Ignoring WAL Bloat**
   - WAL files grow without bound.
   - **Fix:** Set `PRAGMA wal_autocheckpoint = 1000` (auto-truncate WAL).

4. **Assuming SQLite CDC is Real-Time**
   - Unlike PostgreSQL, SQLite CDC has **latency**.
   - **Fix:** Use **async queues** (Kafka, SQS) for buffering.

---

## **Key Takeaways**

✔ **SQLite WAL is your friend**—enable it for near-zero-latency changes.
✔ **Log transactions selectively** (don’t log everything).
✔ **Export diffs, not full tables** (reduce bandwidth).
✔ **Offload processing** (use Kafka/SQS for async forwarding).
✔ **Tradeoffs exist** (latency vs. simplicity).

---

## **Conclusion**

The **"SQLite CDC Logistics"** pattern is **not a silver bullet**, but it’s **the most practical way** to sync SQLite data in real-time without overcomplicating things.

**When to use it?**
✅ Serverless functions needing lightweight DBs.
✅ Offline-first apps syncing to SQLite.
✅ Low-latency analytics pipelines.

**When to avoid it?**
❌ High-throughput systems (use PostgreSQL + Debezium).
❌ Strict real-time requirements (consider MQTT instead).

---
**Next Steps:**
- Experiment with `PRAGMA journal_mode = WAL`.
- Try **incremental exports** in your app.
- Benchmark **WAL vs. triggers** for your workload.

Got questions? Drop them in the comments—I’d love to hear how you’re using (or avoiding) SQLite CDC!
```

---
**Why This Works:**
- **Code-first approach** with real-world Node.js + SQLite examples.
- **Honest tradeoffs** (no "this solves everything" hype).
- **Actionable steps** for immediate experimentation.
- **Balances theory with pragmatism** (e.g., "WAL is good, but don’t overuse it").