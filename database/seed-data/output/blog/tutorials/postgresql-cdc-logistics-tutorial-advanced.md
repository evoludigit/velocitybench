```markdown
---
title: "PostgreSQL CDC Logistics: Building Real-Time Data Pipelines with Logical Decoding"
date: "2023-11-15"
author: "Alex Martinez"
tags: ["PostgreSQL", "Change Data Capture", "CDC", "Database Design", "Real-Time Systems", "Logical Decoding", "Logistics"]
---

# PostgreSQL CDC Logistics: Designing Scalable Change Data Capture for Modern Applications

Change Data Capture (CDC) has emerged as a cornerstone of modern data architectures, enabling real-time data processing, synchronization, and analytics. PostgreSQL’s native support for **Logical Decoding** — through its `pg_logical` and `wal2json` extensions — provides a powerful but complex toolkit for capturing and distributing database changes efficiently. Whether you're building **microservices with eventual consistency**, **data warehousing pipelines**, or **distributed transaction processing systems**, understanding PostgreSQL’s CDC logistics is critical.

In this post, we’ll explore how to architect CDC solutions in PostgreSQL, focusing on **real-world tradeoffs**, **practical patterns**, and **anti-patterns** to avoid. We’ll cover:
- How triggers *don’t* scale for CDC
- Why PostgreSQL’s logical decoding works (and where it falls short)
- A battle-tested **logical decoding pipeline** with code examples
- Performance considerations for high-throughput CDC
- Common pitfalls and how to mitigate them

By the end, you’ll have a clear roadmap for designing PostgreSQL CDC solutions that balance **latency**, **fault tolerance**, and **developer experience**.

---

## The Problem: Why Triggers Are a Poor Fit for CDC

Historically, many developers turn to database triggers for change tracking. While simple, this approach creates significant headaches at scale:

```sql
CREATE OR REPLACE FUNCTION log_change() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (user_id, action, table_name, old_data, new_data)
    VALUES (current_user_id(), 'UPDATE', TG_TABLE_NAME, OLD.*, NEW.*);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_trigger
AFTER UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION log_change();
```

**Problems with this approach:**
1. **Performance overhead**: Triggers add I/O and locking contention, degrading write throughput.
2. **No transaction isolation**: Changes may be logged out of order or lost during crashes.
3. **Difficulty replaying**: Recovering from failures or replaying changes is error-prone.
4. **No event sourcing**: Misses key CDC features like **startup recovery** and **transaction boundaries**.

For applications requiring **eventual consistency**, **exactly-once processing**, or **historical replay**, triggers simply aren’t sufficient. This is where PostgreSQL’s **Logical Decoding** shines.

---

## The Solution: PostgreSQL’s Logical Decoding Pipeline

Logical decoding captures **WAL (Write-Ahead Log) records** and emits changes as structured events. It works by:

1. **Extracting changes** from PostgreSQL’s WAL, which records all transactions.
2. **Mapping changes** to a format (e.g., JSON, Protobuf) via a **plugin** (e.g., `wal2json`, `pgoutput`).
3. **Streaming events** to consumers (e.g., Kafka, Debezium, or custom consumers).

The key components:
| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **WAL (Write-Ahead Log)** | PostgreSQL’s replayable transaction log.                               |
| **Logical Decoding Plugin** | Converts WAL records into application-friendly events.               |
| **Subscription**   | Establishes a connection to receive decoded changes.                 |
| **Consumer**       | Processes events (e.g., Kafka, S3, or a microservice).                |

---

## Implementation Guide: A Practical CDC Pipeline

Let’s build a **real-time user analytics system** that logs user actions to a Kafka topic.

### Step 1: Enable Logical Decoding & WAL Level

First, configure PostgreSQL to generate WAL records for logical decoding:

```sql
-- Set WAL level to 'logical' (PostgreSQL 11+; for older versions, use 'replica')
ALTER SYSTEM SET wal_level = 'logical';

-- Restart PostgreSQL to apply changes.
```

### Step 2: Create a Logical Decoding Plugin

We’ll use [`wal2json`](https://github.com/eulerto/wal2json) for its simplicity:

1. **Install:**
   ```bash
   # Linux (Debian/Ubuntu)
   sudo apt-get install postgresql-15-wal2json  # Adjust version as needed
   ```

2. **Enable in `postgresql.conf`:**
   ```ini
   wal_level = logical
   wal_sender_timeout = 60000
   max_replication_slots = 10
   max_wal_senders = 10
   ```

### Step 3: Define a Publication & Subscription

```sql
-- Create a publication targeting 'users' table
CREATE PUBLICATION user_actions_pub FOR TABLE users;

-- Create a replication slot (required for startup recovery)
SELECT pg_create_logical_replication_slot('slot1', 'wal2json');
```

### Step 4: Stream Changes to Kafka

Use [`pg2kafka`](https://github.com/eulerto/pg2kafka) to bridge PostgreSQL and Kafka:

```bash
# Start pg2kafka to listen to the publication
pg2kafka --host=localhost --port=5432 \
         --dbname=analytics \
         --user=postgres \
         --publication=user_actions_pub \
         --topic=users.actions \
         --kafka-server=localhost:9092
```

### Step 5: Consumer Example (Python)

Here’s a Kafka consumer that processes user actions:

```python
from confluent_kafka import Consumer, KafkaException

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'user-actions-consumer',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)

# Subscribe to the topic
consumer.subscribe(['users.actions'])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())

        # Parse JSON (wal2json format)
        record = msg.value()
        change = json.loads(record)['data']
        print(f"Action: {change['action']} on user {change['key']['lsn']}")

except KeyboardInterrupt:
    pass
finally:
    consumer.close()
```

---

## Performance Considerations

### Throughput Limits
- **WAL generation**: WAL is always written, but logical decoding adds minimal overhead (~5-10% CPU).
- **Network bottleneck**: Streaming changes over TCP can saturate connections. Consider **compression** (e.g., `wal2json` supports `gzip`).
- **Consumer lag**: Use **Kafka’s consumer groups** to parallelize processing.

### Advanced Optimizations
1. **Batch processing**: Aggregate small changes (e.g., bulk inserts) before sending.
2. **Schema evolution**: Use **Protobuf** or **Avro** for backward-compatible event formats.
3. **Retention**: Configure `max_slot_wal_keep_size` to limit WAL retention.

---

## Common Mistakes to Avoid

| Mistake                          | Impact                                                                 | Solution                                                                 |
|----------------------------------|-------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Ignoring `wal_level`**         | No logical decoding available.                                          | Ensure `wal_level = logical` in `postgresql.conf`.                      |
| **No replication slot**          | Cannot recover after failures.                                           | Use `pg_create_logical_replication_slot`.                                |
| **Unbounded WAL retention**      | Disk space issues if consumers lag.                                      | Set `max_slot_wal_keep_size` to limit WAL storage.                     |
| **No error handling**            | Lost events if consumers fail.                                           | Implement **dead-letter queues** (e.g., Kafka DLQ) for failed records.  |
| **Overloading the WAL**          | High WAL generation overhead.                                            | Use **partitioned tables** or **batch transactions**.                  |
| **Tight coupling to plugins**    | Vendor lock-in (e.g., `wal2json`).                                       | Design for interchangeable plugins (e.g., use a JSON parser layer).      |

---

## Key Takeaways

✅ **PostgreSQL’s logical decoding** is the gold standard for CDC, offering **low-latency**, **exactly-once** processing.

✅ **Avoid triggers for CDC**: They’re not designed for real-time pipelines and add unnecessary overhead.

✅ **Start small**: Begin with a single publication and scale consumption horizontally (e.g., Kafka partitions).

✅ **Monitor WAL growth**: Use `pg_stat_replication` to track replication lag and adjust slot settings.

✅ **Design for failure**: Implement **dead-letter queues** and **transaction replay** logic.

✅ **Leverage Kafka or Debezium**: These tools abstract away many CDC complexities (e.g., schema management, offset tracking).

---

## Conclusion

PostgreSQL’s **Logical Decoding** is a powerful tool for building real-time data pipelines, but it requires careful architecture to avoid common pitfalls. By understanding the **WAL lifecycle**, **plugin tradeoffs**, and **consumer patterns**, you can design scalable CDC solutions that power modern applications.

### Next Steps
- Experiment with [`Debezium`](https://debezium.io/) for schema-aware CDC.
- Explore **binary format plugins** (e.g., `pgoutput`) for higher throughput.
- Benchmark your pipeline with tools like [`pgbench`](https://www.postgresql.org/docs/current/app-pgbench.html).

Happy decoding!
```