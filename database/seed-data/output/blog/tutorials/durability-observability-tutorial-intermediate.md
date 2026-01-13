```markdown
# **Durability Observability: How to Confirm Your Data Actually Stays Put**

*When your database says "done," does it actually mean "done"?*

You’ve built a robust system. Your API streams data at 10,000 requests/sec. Your transactions commit in milliseconds. But here’s the terrifying truth: **if you can’t *prove* data persists, it might not**. Durability observability—tracking whether your system truly meets its durability promises—isn’t just an academic concern. It’s the difference between a "temporarily unavailable" outage and a catastrophic data loss.

In this post, we’ll explore why durability observability exists, the common pitfalls that hide behind assumptions, and how to build real-world durability checks for databases, message queues, and distributed systems. We’ll use code examples in PostgreSQL, Kafka, and Go to show you how to validate your assumptions.

---

## **The Problem: When “Committed” ≠ “Persisted”**

Behind every durable system stands a fragile assumption: *"If the database says ‘success,’ the data is safe."* But databases don’t tell the whole story. Here’s what can go wrong:

### **1. Network Split-Brain**
A client commits to a database in New York, but the replication node in Los Angeles hasn’t acknowledged the write yet. A failover occurs, and the client’s changes are lost. The database returns "success," but without confirmation from the replica, you don’t know.

### **2. Persistence Latency**
Even after a commit, data might be buffered in memory before hitting disk. A crash or power failure in the middle of a sync could erase uncommitted writes. PostgreSQL’s `fsync` setting is a common culprit—enabling it adds durability but can degrade performance.

### **3. Queue Quirks**
Kafka partitions mark messages "acked" before they’re fully written to disk. If a broker crashes before applying the transaction, messages disappear. Worst case: your system assumes a message was processed, but it never was.

### **4. The "It’ll Be Fine" Fallacy**
Many developers rely on ACID guarantees but skip validation. Why bother adding checks if the database "already handles it"? Because **you’ve never seen your database under real-world stress**.

---

## **The Solution: Durability Observability**

Durability observability is the practice of **actively verifying** that your system meets its durability promises. It involves:

1. **Monitoring persistence** – Confirming data is flushed to disk.
2. **Cross-checking replicas** – Validating remote nodes match local writes.
3. **Tracking acknowledgments** – Ensuring consumers really received messages.
4. **Simulating failures** – Testing how your system behaves under outages.

### **Key Principles**
- **Assume nothing**: Don’t trust a single layer (e.g., "the database is durable").
- **Check, don’t rely**: Use explicit durability checks instead of implicit assumptions.
- **Measure under pressure**: Latency and durability are tradeoffs—your checks should work during spikes.
- **Fail fast**: If a durability check fails, alert immediately.

---

## **Components of Durability Observability**

### **1. Database-Level Durability Checks**
Most databases offer configuration for durability, but you need to verify they’re working.

#### **PostgreSQL: Confirm `fsync` and WAL Logging**
PostgreSQL’s durability depends on `fsync` and Write-Ahead Logging (WAL). Here’s how to check:

```sql
-- Check if fsync is enabled (default is ON)
SHOW fsync;

-- Verify data is written to WAL
SELECT pg_is_in_recovery();  -- Should return false in a primary node
```

**Go Implementation** – A simple PostgreSQL probe:
```go
package main

import (
	"database/sql"
	"fmt"
	_ "github.com/lib/pq"
)

func CheckDurability(db *sql.DB) error {
	// 1. Check fsync setting
	var fsync string
	err := db.QueryRow("SHOW fsync;").Scan(&fsync)
	if err != nil || fsync != "on" {
		return fmt.Errorf("fsync is not enabled")
	}

	// 2. Verify WAL is active
	var isRecovery bool
	err = db.QueryRow("SELECT pg_is_in_recovery();").Scan(&isRecovery)
	if err != nil || isRecovery {
		return fmt.Errorf("node appears in recovery mode")
	}

	// 3. Test a durability-sensitive operation (e.g., UNLOGGED table won't help)
	_, err = db.Exec("CREATE UNLOGGED TABLE temp (id int);")
	if err != nil {
		return fmt.Errorf("unlogged tables disabled (durability check failed)")
	}
	return nil
}
```

### **2. Replication Lag Monitoring**
If your database replicates to multiple nodes, verify they’re in sync.

```go
// Get replication lag in PostgreSQL
func GetReplicationLag(db *sql.DB) (float64, error) {
	// On PostgreSQL 9.5+, use pg_stat_replication
	rows, err := db.Query("SELECT pg_stat_replication.replay_lag / 1000 AS lag_seconds FROM pg_stat_replication")
	if err != nil {
		return 0, err
	}
	defer rows.Close()

	lag := 0.0
	for rows.Next() {
		var s float64
		if err := rows.Scan(&s); err == nil {
			lag = s
		}
	}
	return lag, nil
}
```

**Alert if lag > threshold**:
```go
lag := 5.0  // seconds
if lag > lag {
	log.Printf("Replication lag at %f seconds", lag)
	// Send alert
}
```

### **3. Queue Durability Validation**
For Kafka, configure `acks=all` and verify messages are fully committed.

```python
# Python example using confluent_kafka
from confluent_kafka import Producer

conf = {
    'bootstrap.servers': 'kafka:9092',
    'acks': 'all',  # Ensure all replicas commit
}

producer = Producer(conf)

def send_and_verify(topic, message):
    producer.produce(topic, message)
    producer.flush()  # Wait for acknowledgment

    # Simulate a durability check: query a consumer group offset
    from confluent_kafka import Consumer
    consumer = Consumer({'group.id': 'durability-check', **conf})
    consumer.subscribe([topic])
    offset = consumer.position(topic, 0)
    consumer.close()
    return offset > 0  # If true, message was consumed
```

### **4. External Durability Probes**
For critical systems, run **periodic durability checks** (e.g., "Is this table really updated?").

```go
// Periodic check for a table's last commit timestamp
func CheckTableDurability(db *sql.DB, table string) error {
	// Get current max timestamp from the table
	var lastWriteTime time.Time
	err := db.QueryRow(fmt.Sprintf("SELECT max(created_at) FROM %s", table)).Scan(&lastWriteTime)
	if err != nil {
		return err
	}

	// Compare with WAL timestamp (PostgreSQL specific)
	var walTime time.Time
	err = db.QueryRow("SELECT pg_current_wal_insert_lsn()::timestamp").Scan(&walTime)
	if err != nil {
		return err
	}

	// If lastWriteTime < walTime, something is wrong
	if lastWriteTime.Before(walTime) {
		return fmt.Errorf("table durability check failed: %s", lastWriteTime)
	}
	return nil
}
```

---

## **Implementation Guide**

### **Step 1: Define Your Durability Requirements**
- What’s "good enough"? (e.g., "Durable to disk in <100ms" or "99.99% availability")
- Which layers are critical? (e.g., database, queue, or both)

### **Step 2: Instrument Your Database**
- Enable `fsync` and set WAL to `archive_mode=on` (PostgreSQL).
- Monitor replication lag with tools like Prometheus or custom scripts.

### **Step 3: Add Cross-Validation Checks**
For every commit, run a lightweight durability check:
```go
// Example: Store a "durability marker" table
db.Exec("INSERT INTO durability_checks (timestamp) VALUES (NOW())")
db.Exec("SELECT * FROM durability_checks ORDER BY id DESC LIMIT 1 FOR UPDATE")  // Lock last row
```

### **Step 4: Test Under Load**
Simulate failures:
- Kill PostgreSQL’s background writer (`pg_ctl stop -m fast`).
- Crash Kafka brokers mid-message write.
- Monitor if your system recovers correctly.

### **Step 5: Automate Alerts**
- Use tools like Datadog, Prometheus, or custom scripts to alert on durability failures.
- Example: Alert if `replication_lag > 10s`.

---

## **Common Mistakes to Avoid**

### **1. Skipping Persistence Until Too Late**
- **Bad**: "We’ll fsync after the response."
- **Better**: Configure `fsync=on` at the OS level (not just in PostgreSQL).

### **2. Trusting Implicit Durability**
- **Bad**: "If the database says ‘success,’ it’s durable."
- **Better**: Explicitly check logs/WAL after every write.

### **3. Ignoring Replication Lag**
- **Bad**: Monitoring only primary node health.
- **Better**: Check replica lag and alert if it grows.

### **4. Not Testing Failure Scenarios**
- **Bad**: "Our system is production-ready."
- **Better**: Kill the database mid-write and verify recovery.

### **5. Overlooking Queue Durability**
- **Bad**: Kafka `acks=0` for "fast throughput."
- **Better**: Use `acks=all` and verify brokers are safe.

---

## **Key Takeaways**
- **Durability ≠ ACID alone**: You must verify it works in practice.
- **Check persistence, don’t assume it’s on**: `fsync`, WAL logs, and replication lag are critical.
- **Validate replicas**: A primary’s "success" isn’t enough; cross-check with backups.
- **Test failure modes**: Crash your system to see if it recovers.
- **Automate observability**: Alert on durability breaches proactively.

---

## **Conclusion**
Durability observability isn’t about guessing your system works—it’s about proving it. By adding lightweight checks around your database, queues, and replication layers, you can avoid the silent horror of "it worked until it didn’t."

**Start with small probes** (e.g., WAL checks in PostgreSQL), then expand to replication lag and queue validation. Over time, this approach will save you from catastrophic data loss—because durability isn’t a promise from the database, it’s something you *must verify yourself*.

**Next Steps**:
1. Run the durability checks in your local environment.
2. Add alerts for replication lag.
3. Test under failure conditions.

Now go build something that *actually* stays put.
```

---
**Word Count**: ~1800
**Tone**: Practical, code-first, honest about tradeoffs.
**Audience**: Intermediate backend engineers (Go/PostgreSQL/Kafka knowledge assumed).

Would you like additional coverage on specific databases (e.g., MongoDB, MySQL) or distributed systems (e.g., DynamoDB)?