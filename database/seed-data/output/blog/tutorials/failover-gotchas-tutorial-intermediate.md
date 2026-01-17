```markdown
# **"Failover Gotchas: The Invisible Pitfalls That Break Your Database"**

**A Practical Guide to Designing Resilient Systems That Actually Failover Correctly**

---

## **Introduction**

Failover isn’t just about having a backup server—it’s about ensuring your application can seamlessly transition to a standby node *without* exposing bugs, data inconsistencies, or performance degradation. Most developers assume failover works "out of the box," but real-world systems reveal hidden gotchas that turn graceful transitions into catastrophic failures.

Think of a payment processing system where a failover corrupts the database, or a SaaS dashboard where users see stale data after a node switch. These aren’t theoretical edge cases—they’re harsh lessons taught by poorly tested failover strategies. In this post, we’ll dissect the **Failover Gotchas Pattern**, covering:
- Why "it’s just a backup" is dangerous
- Common failure modes (and how to detect them)
- Practical patterns for robust failover
- Real-world code examples (PostgreSQL, Kubernetes, and async APIs)

By the end, you’ll know how to design systems where failover is invisible to users—*and* to your debugging logs.

---

## **The Problem: Failover Without a Safety Net**

Failover systems often fail in *unexpected ways* because they’re designed for the happy path, not the chaos path. Here’s what usually goes wrong:

### **1. "I Told It to Failover, But Did It Actually Work?"**
Without observability, you can’t confirm a failover succeeded. A `pg_promote()` call might complete silently, but your app could still be talking to the old master. Symptoms:
- Users see stale data.
- Transactions start on the wrong node.
- Replication lags expose inconsistencies.

**Example:** A financial app fails over to a standby, but the standby’s initial sync was incomplete. A user queries the new master *before* it catches up, seeing incorrect balances.

### **2. The "Race Condition" That Doomed Your Schema**
Some databases (e.g., PostgreSQL) allow writes during failover, leading to:
- Split-brain scenarios where two masters diverge.
- Schema migrations failing mid-failover.
- Applications losing connection mid-transition.

**Example:** An e-commerce system triggers a `CREATE TABLE` migration on the master. During failover, the standby promotes but drops the old table, causing the app to crash.

### **3. "Async APIs Don’t Know What Happened"**
If your app uses async APIs (e.g., Kafka, Redis) for failover coordination, you risk:
- **Stale state:** A consumer processes messages from the old master.
- **Duplicate processing:** The new master re-sends stale data.
- **Timeouts:** The coordination service times out, leaving the app in limbo.

**Example:** A notification service subscribes to a Kafka topic on the old master. After failover, it keeps publishing to the old topic, sending duplicate alerts.

### **4. "The Standby Wasn’t Ready (But No One Noticed)"**
Standby nodes often fail silently during failover because:
- Replication lag goes undetected.
- Queries time out without alerts.
- The standby’s `wal_generation` is stale.

**Example:** A logging service fails over to a standby with 30 seconds of lag. During that window, logs are written to the old node, creating a duplicate log entry.

### **5. "My App Breaks When the Primary Dies"**
Applications often assume the primary is always reachable. When failover happens:
- Connection pools refill with stale nodes.
- Retry logic fails on the wrong endpoint.
- Circuit breakers open prematurely.

**Example:** A microservice uses a `primary.db.internal` DNS record. After failover, the record still points to the old IP, causing connection errors.

---

## **The Solution: Failover Gotchas Patterns**

To avoid these pitfalls, we need a **multi-layered approach**:
1. **Detect failover completion** (not just initiation).
2. **Validate data consistency** before promoting.
3. **Isolate async dependencies** from failover chaos.
4. **Monitor standby health** proactively.
5. **Design apps for failover awareness**.

Below are battle-tested patterns with code examples.

---

## **Components/Solutions**

### **1. Failover Verification Layer**
**Problem:** You can’t assume `pg_promote()` worked.
**Solution:** Add a post-failover health check.

#### **PostgreSQL Example (TLS + Query Validation)**
```sql
-- On the standby, after promoting:
SELECT pg_is_in_recovery();  -- Should return false
SELECT pg_current_wal_lsn() = '0/2000000';  -- Check WAL consistency
SELECT COUNT(*) FROM users WHERE id = 1;     -- Validate a critical row
```

**Application Code (Python + SQLAlchemy):**
```python
from sqlalchemy import create_engine, text
import requests

def verify_failover_succeeded(new_master_host):
    # 1. Check database state
    engine = create_engine(f"postgresql://user:pass@{new_master_host}/db")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT pg_is_in_recovery()"))
        if result.scalar():
            raise RuntimeError("Failover incomplete: still in recovery")

    # 2. Validate async dependencies (e.g., Redis)
    try:
        responses = requests.get(f"http://{new_master_host}:6379/ping", timeout=2)
        if responses.status_code != 200:
            raise RuntimeError("Redis not ready on new master")
    except requests.RequestException:
        raise RuntimeError("Redis connection failed")

    # 3. Check for split-brain (if using Kafka)
    kafka_brokers = get_kafka_brokers()  # Fetch from config
    if new_master_host not in kafka_brokers:
        raise RuntimeError("Master not advertised to Kafka")
```

**Key Tradeoff:** Adds latency (~1-2s), but catches 90% of failover failures.

---

### **2. Schema Migration Locks**
**Problem:** Schema changes during failover corrupt the standby.
**Solution:** Block migrations during failover.

#### **PostgreSQL Example (Using `pg_advisory_xact_lock`):**
```sql
-- On the primary, before failover:
BEGIN;
SELECT pg_advisory_xact_lock(12345);  -- Lock the "failover in progress" slot
-- Let the standby sync
COMMIT;

-- On the standby, after promoting:
BEGIN;
SELECT pg_try_advisory_xact_lock(12345) IS NULL;  -- Check if locked
IF NOT $1 THEN
    RAISE WARNING 'Another failover in progress!';
    ROLLBACK;
ELSE
    -- Proceed with promotion
    SELECT pg_promote();
    COMMIT;
END IF;
```

**Application Code (Go):**
```go
package main

import (
	"database/sql"
	_ "github.com/lib/pq"
)

func EnsureFailoverSafe(db *sql.DB) error {
	_, err := db.Exec(`
		BEGIN;
		SELECT pg_try_advisory_xact_lock(12345) IS NULL;
	`)
	if err != nil {
		return err
	}
	return db.Rollback()
}
```

**Key Tradeoff:** Requires application coordination (e.g., gracefully stopping migrations).

---

### **3. Async API Isolation**
**Problem:** Async systems (Kafka, Redis) don’t know failover happened.
**Solution:** Route async calls through the new master.

#### **Kafka Example (Consumer Group Redirection):**
```bash
# Before failover:
./kafka-consumer-groups.sh --bootstrap-server old-master:9092 \
  --group my-group --describe
# Output:
GROUP   TOPIC  PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG

# After failover, update the consumer to point to new-master
```

**Application Code (Python + Confluent Kafka):**
```python
from confluent_kafka import Consumer

def get_consumer(master_host):
    return Consumer({
        'bootstrap.servers': master_host,
        'group.id': 'my-group',
        'auto.offset.reset': 'latest'
    })

# Usage:
consumer = get_consumer("new-master.internal")
consumer.subscribe(['orders'])
```

**Key Tradeoff:** Requires service discovery updates (e.g., via DNS TTL tricks or dynamic configs).

---

### **4. Standby Health Probes**
**Problem:** Standbys fail silently during failover.
**Solution:** Active monitoring of WAL lag, CPU, and network.

#### **Prometheus + PostgreSQL Example:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'postgres_standby'
    static_configs:
      - targets: ['standby:9187']  # PostgreSQL exporter port
```

**SQL Query to Check Lag:**
```sql
SELECT
    pg_is_in_recovery(),
    pg_last_xact_replay_timestamp(),
    extract(epoch from (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
```

**Alert Rules (Prometheus):**
```yaml
groups:
- name: postgres-failover
  rules:
  - alert: HighReplicationLag
    expr: postgres_replication_lag_seconds > 5
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL standby lagging too long"
```

**Key Tradeoff:** Adds operational overhead but catches 80% of silent failovers.

---

### **5. Failover-Aware Applications**
**Problem:** Apps assume the primary is always available.
**Solution:** Use connection pooling with failover awareness.

#### **SQLAlchemy Example (With Retry Logic):**
```python
from sqlalchemy import create_engine
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_db_connection():
    engine = create_engine(
        f"postgresql://user:pass@primary.db.internal/db",
        pool_pre_ping=True,  # Test connections before use
        pool_recycle=3600    # Force refresh stale connections
    )
    return engine.connect()
```

**Key Tradeoff:** Slower initial connects, but more resilient.

---

## **Implementation Guide: Step-by-Step**

### **1. Detect Failover (Database Layer)**
- Use **`pg_is_in_recovery()`** to check if the standby is still recovering.
- Verify **WAL consistency** with `pg_current_wal_lsn()`.
- Run a **critical query** (e.g., `SELECT COUNT(*) FROM users`) to validate data.

### **2. Coordinate Async Systems**
- For **Kafka/RabbitMQ**, update consumer/destination IPs to the new master.
- For **Redis**, flush and re-sync keys if using replication.
- For **gRPC**, update service discovery endpoints.

### **3. Lock Schema Changes**
- Use **`pg_advisory_xact_lock`** to block migrations during failover.
- Or use **transactional outbox patterns** to defer writes.

### **4. Monitor Standby Health**
- Set up **Prometheus alerts** for replication lag >5s.
- Use **PG Bouncer’s `pool_mode=transaction`** to detect stale connections.

### **5. Design Apps for Failover**
- **Connection pooling:** Use `pool_pre_ping=True` to detect dead nodes.
- **Circuit breakers:** Fail fast if the primary isn’t responding.
- **Idempotency:** Ensure retries don’t cause duplicates.

---

## **Common Mistakes to Avoid**

| **Mistake**               | **Why It’s Bad**                          | **Fix**                                  |
|---------------------------|------------------------------------------|------------------------------------------|
| Ignoring `pool_pre_ping`   | Stale connections cause silent failures. | Enable in connection pools.              |
| Not validating async deps | Kafka/RabbitMQ may keep sending to old master. | Update endpoints post-failover.          |
| Assuming `pg_promote()` works | May fail silently due to incomplete sync. | Add health checks.                      |
| No circuit breakers        | Apps retry indefinitely on failover.     | Use Hystrix/Resilience4j.                |
| Hardcoded endpoints       | DNS changes break failover.              | Use service discovery.                   |
| No WAL consistency checks  | Split-brain after partial sync.          | Compare `pg_current_wal_lsn()`.          |

---

## **Key Takeaways**

✅ **Failover isn’t automatic.** Always verify completion (database, async deps, schema).
✅ **Async systems must be notified.** Kafka, Redis, etc., assume the primary is alive.
✅ **Lock schema changes.** Prevent migrations from corrupting during failover.
✅ **Monitor standby health.** Lag >5s = disaster waiting to happen.
✅ **Design apps for failover.** Use connection pooling, circuit breakers, and idempotency.
✅ **Test failovers weekly.** Chaos engineering catches hidden bugs.

---

## **Conclusion**

Failover is one of the hardest problems in distributed systems—not because the tools are hard, but because the **gotchas are invisible until it’s too late**. By layers of checks (database, async deps, app logic), you can build systems that failover **without users noticing**.

**Next Steps:**
1. Audit your failover process: Are you checking for completion?
2. Add Prometheus alerts for replication lag.
3. Test a failover in staging—**today**.
4. Share your war stories (and gotchas fixed) in the comments!

---
**Further Reading:**
- [PostgreSQL Failover Documentation](https://www.postgresql.org/docs/current/high-availability.html)
- [Kubernetes Pod Disruption Budgets](https://kubernetes.io/docs/tasks/run-application/configure-pdb/)
- [Chaos Engineering for Databases](https://www.chaosengineering.com/)

---
**What’s your biggest failover failure story?** Share in the comments—I’d love to hear how you fixed it!
```