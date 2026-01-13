# **Debugging Durability Best Practices: A Troubleshooting Guide**

Durability involves ensuring that data persists reliably even in the face of failures (e.g., crashes, network outages, or hardware failures). Common durability patterns include:
- **Idempotent Operations** (e.g., retry-safe APIs)
- **WAL (Write-Ahead Logging)**
- **Data Replication & Sync**
- **Atomic Writes & Transactions**
- **Checkpointing (for stateful systems)**

This guide provides a structured approach to debugging durability-related issues.

---

## **1. Symptom Checklist**

Before diving into fixes, confirm the symptoms:

| **Symptom**                          | **Possible Cause**                          | **Impact**                          |
|--------------------------------------|--------------------------------------------|-------------------------------------|
| Data loss after system crash         | No WAL or improper logging                 | Permanent data corruption          |
| Inconsistent state across replicas    | Out-of-sync replication                    | Read/write anomalies                |
| Failed transactions roll back        | Uncommitted writes or deadlocks            | Lost transactions                   |
| High latency in write operations    | Slow disk I/O or network bottlenecks       | Poor user experience                |
| Duplicate operations on retries      | Non-idempotent API calls                    | Data corruption                     |
| Incomplete state after restart       | Missing checkpoints                        | Partial system failure              |
| High error rates on durable writes   | Storage/DB connection issues               | Service outages                     |

**Next Steps:**
- Verify if the issue is intermittent or persistent.
- Check logs for `ERROR`, `WARN`, or `RETRY` messages.
- Reproduce the issue in a non-production environment.

---

## **2. Common Issues & Fixes**

### **A. WAL (Write-Ahead Logging) Failures**
**Symptom:** Crashes lead to data loss.
**Root Cause:** No WAL enabled or log files corrupted/disconnected.

#### **Fix: Enable & Validate WAL**
```python
# Example: Using PostgreSQL's fsync for durability
import psycopg2

conn = psycopg2.connect("dbname=test user=postgres")
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
conn.autocommit = True

# Ensure writes are durably logged before returning
def safe_write(data):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs VALUES (%s)", (data,))
    conn.commit()  # Forces fsync on disk
    return True
```

**Debugging:**
- Check storage logs (`dmesg`, `syslog`) for disk I/O errors.
- Ensure `fsync()` is called after critical writes (PostgreSQL, MySQL, etc.).

---

### **B. Non-Idempotent Operations**
**Symptom:** Duplicate transactions after retries (e.g., API calls failing intermittently).
**Root Cause:** Missing idempotency keys or retry logic.

#### **Fix: Implement Idempotency Keys**
**Approach 1:** Use UUIDs for retries.
```javascript
// Express.js example with Redis for idempotency
const { v4: uuidv4 } = require('uuid');
const redis = require('redis');

const client = redis.createClient();

async function idempotentOrderCreate(order) {
  const idempotencyKey = uuidv4();
  const cached = await client.get(idempotencyKey);

  if (cached) return; // Skip if already processed

  await db.saveOrder(order);
  await client.set(idempotencyKey, 'processed', 'EX', 3600); // TTL: 1 hour
}
```

**Approach 2:** Use database-side idempotency tables.
```sql
-- SQL schema for idempotency tracking
CREATE TABLE idempotency_keys (
  key VARCHAR(255) PRIMARY KEY,
  payload JSONB NOT NULL,
  processed_at TIMESTAMP
);

-- Check before processing
INSERT INTO orders (data)
SELECT * FROM jsonb_populate_record(NULL::order, payload)
WHERE NOT EXISTS (
  SELECT 1 FROM idempotency_keys WHERE key = 'abc123'
);
```

**Debugging:**
- Monitor retry attempts (`429 Too Many Requests` in logs).
- Use tools like **Prometheus + Alertmanager** to track duplicate operations.

---

### **C. Replication Lag**
**Symptom:** Master-slave replication out of sync.
**Root Cause:** Slow network, high write load, or misconfigured replication.

#### **Fix: Optimize Replication**
```bash
# PostgreSQL: Check replication lag
psql -c "SELECT pg_stat_replication;"

# MySQL: Adjust replication settings
SET GLOBAL binlog_format = ROW;
SET GLOBAL sync_binlog = 1;  # Waits for disk write confirmation
```

**Debugging:**
- Check `pg_stat_replication` (PostgreSQL) or `SHOW SLAVE STATUS` (MySQL).
- Use tools like **pt-table-checksum** (Percona) to verify data consistency.

---

### **D. Checkpointing Failures**
**Symptom:** Stateful services (e.g., Kafka, Redis) lose state on restart.
**Root Cause:** Checkpoints not persisted or corrupted.

#### **Fix: Implement Proper Checkpointing**
```java
// Kafka Streams example: Enable checkpointing
Properties props = new Properties();
props.put(StreamsConfig.APPLICATION_ID_CONFIG, "stream-app");
props.put(StreamsConfig.CACHE_MAX_BYTES_BUFFERING_CONFIG, 33554432L); // 32MB buffer
props.put(StreamsConfig.STATE_STORE_CACHE_MAX_BYTES_CONFIG, 1073741824L); // 1GB cache

StreamsBuilder builder = new StreamsBuilder();
KTable<String, String> table = builder.table("input-topic");
table.toStream().to("output-topic");

KafkaStreams streams = new KafkaStreams(builder.build(), props);
streams.start();

// Configure durable state
props.put(StreamsConfig.STATE_DIR_CONFIG, "/var/lib/kafka/streams/checkpoints");
```

**Debugging:**
- Check Kafka consumer lag: `./kafka-consumer-groups.sh --describe --group stream-app --bootstrap-server localhost:9092`.
- Validate checkpoint files (`/var/lib/kafka/streams/checkpoints`).

---

### **E. Atomic Writes Failures**
**Symptom:** Partial writes (e.g., one row committed, another not).
**Root Cause:** Lack of transactions or improper commit handling.

#### **Fix: Use Transactions**
```python
# PostgreSQL transaction example
import psycopg2

conn = psycopg2.connect("dbname=test")
try:
    with conn.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("INSERT INTO table1 VALUES (1, 'A')")
        cursor.execute("INSERT INTO table2 VALUES (2, 'B')")
        conn.commit()  # All or nothing
except Exception as e:
    conn.rollback()
    print(f"Failed: {e}")
```

**Debugging:**
- Check `pg_stat_activity` for long-running transactions.
- Use **pgBadger** to analyze transaction logs.

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Purpose**                                      | **Example Command/Query**                     |
|-------------------------|--------------------------------------------------|-----------------------------------------------|
| **Prometheus + Grafana** | Monitor durability metrics (latency, errors)   | `rate(durable_writes_total[1m]) > 100`        |
| **pgBadger**            | PostgreSQL log analysis                          | `pgbadger /var/log/postgresql/postgresql.log` |
| **pt-table-checksum**   | MySQL replication consistency check                | `pt-table-checksum -u user -p'pass' -n 2 h=master,slave` |
| **Kafka Consumer Lag**  | Check Kafka consumer lag                          | `./kafka-consumer-groups.sh --describe`      |
| **Strace**              | Debug filesystem I/O bottlenecks                 | `strace -f -e trace=file -o /tmp/strace.log <pid>` |
| **Redis CLI**           | Check Redis persistence status                   | `INFO Persistence`                           |

**Key Metrics to Monitor:**
- **WAL/Log Write Latency** (should be <100ms)
- **Replication Lag** (should be near-zero)
- **Transaction Rollback Rate** (should be close to zero)
- **Checkpoint Duration** (should be fast)

---

## **4. Prevention Strategies**

### **A. Infrastructure-Level Durability**
1. **Use SSD/NVMe storage** for low-latency durability.
2. **Enable RAID 10** for critical databases.
3. **Replicate across AZs** (AWS RDS Multi-AZ, GCP Persistent Disk).

### **B. Application-Level Safeguards**
1. **Always validate WAL persistence** (e.g., `fsync` after writes).
2. **Use connection pooling** (e.g., PgBouncer) to avoid stale connections.
3. **Implement circuit breakers** (e.g., Hystrix) for retries.
4. **Regularly test failover** (chaos engineering).

### **C. Observability & Alerting**
1. **Set up alerts for:**
   - High replication lag (>1s).
   - WAL log corruption errors.
   - Duplicate operations (>1% of total writes).
2. **Use distributed tracing** (Jaeger, OpenTelemetry) to track data flow.

### **D. Disaster Recovery (DR) Plan**
- **Automated backups** (e.g., PostgreSQL `pg_dump`, MySQL `mysqldump`).
- **Regular disaster recovery drills**.
- **Multi-region failover testing**.

---

## **5. Step-by-Step Debugging Workflow**
1. **Reproduce the issue** (e.g., simulate a crash).
2. **Check logs** (`/var/log/syslog`, application logs).
3. **Monitor metrics** (Prometheus, DataDog).
4. **Isolate the component** (WAL? Replication? Transactions?).
5. **Apply fixes** (e.g., enable WAL, add idempotency key).
6. **Validate with tests** (e.g., `chaos-mesh`).
7. **Deploy to staging** and monitor.
8. **Roll out to production** with a canary release.

---

## **6. Example Debugging Session: WAL Corruption**
**Symptom:** PostgreSQL crashes after writes, data lost.
**Steps:**
1. **Check OS logs:**
   ```bash
   journalctl -u postgresql --no-pager | grep -i "error"
   ```
2. **Verify WAL directory integrity:**
   ```bash
   ls -la /var/lib/postgresql/14/main/pg_wal/
   ```
   (If empty, WAL is not being logged.)
3. **Enable `fsync` in `postgresql.conf`:**
   ```ini
   fsync = on
   synchronous_commit = on
   ```
4. **Restart PostgreSQL and test durability.**
5. **Monitor with `pg_stat_activity` for long-running transactions.**

---

## **7. Final Checklist Before Production**
| **Check**                          | **Pass/Fail** |
|-------------------------------------|---------------|
| WAL is enabled and logged to disk   | ✅/❌          |
| Replication lag < 1s                | ✅/❌          |
| Idempotency keys implemented        | ✅/❌          |
| Transactions properly committed     | ✅/❌          |
| Checkpoints validated on restart     | ✅/❌          |
| Backups automated & tested          | ✅/❌          |

---

### **Key Takeaways**
- **Durability is about persistence + consistency** (WAL, transactions, idempotency).
- **Logs and metrics are your best friends** (Prometheus, pgBadger).
- **Test failover regularly** (chaos engineering).
- **Use replication + backups** for high availability.

By following this guide, you can systematically diagnose and resolve durability issues while preventing future outages.