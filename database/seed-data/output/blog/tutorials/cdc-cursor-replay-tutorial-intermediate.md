```markdown
# **Change Data Capture (CDC) Cursor-Based Replay: How to Rebuild State from Scratch**

*Eventual consistency is great, but what if you need to rebuild a system from scratch? Learn how to use CDC cursor-based replay to replay events from a specific point in time, ensuring data consistency and recovery.*

---

## **Introduction**

As backend developers, we’ve all faced the classic challenge: *How do we rebuild our system’s state when things go wrong?* If your service relies on eventual consistency or asynchronous event-driven workflows, you might need to replay historical events to restore a consistent state. Traditional transactional systems rely on point-in-time recovery using logs or snapshots, but for distributed systems with CDC (Change Data Capture), a more flexible approach is needed.

Enter **cursor-based replay**. This technique allows you to replay events from a specific position in your CDC stream, enabling features like:
- **State reconstruction** (e.g., rebuilding a system after a massive failure)
- **Data migration** (e.g., transitioning from one database to another)
- **Event sourcing recovery** (e.g., replaying events to a new event store)

In this post, we’ll explore how cursor-based replay works, its tradeoffs, and how to implement it in PostgreSQL with Debezium (a popular CDC tool) and Python.

---

## **The Problem: Why Replay from a Cursor?**

Before diving into solutions, let’s define the problem:

1. **No Built-in Recovery Mechanism**
   Traditional databases (like PostgreSQL) support point-in-time recovery (PITR) via WAL (Write-Ahead Log), but this is designed for transactional consistency—not replaying *application-level events*.
   - *Example*: If your app deletes a user via an API call, you want to replay that event to ensure all downstream services reflect the deletion.

2. **Eventual Consistency Needs Refreshes**
   In distributed systems, eventual consistency means that after an event (e.g., `user_deleted`), downstream services *will* process it—but not immediately. If you need to rebuild a service from scratch (e.g., after a VM crash), you must replay all relevant events since the last snapshot.

3. **Data Migration Without Downtime**
   Suppose you’re migrating from PostgreSQL to MongoDB. You can’t just dump tables—you need to replay all changes (inserts, updates, deletes) in the correct order to maintain consistency.

4. **Handling Long-Running Transactions**
   If a transaction spans minutes (e.g., a complex order processing workflow), you might need to replay its progress in case of failure.

---

## **The Solution: Cursor-Based Replay**

Cursor-based replay is a CDC pattern where you:
1. **Start from a known offset** (a "cursor" or LSN—Log Sequence Number in PostgreSQL) in the CDC stream.
2. **Replay all changes** sequentially, applying them to your target system (database, cache, or event store).
3. **Handle gaps** (e.g., if some events were lost or skipped during replay).

This approach is more flexible than PITR because:
- It works with *application-level events*, not just transaction logs.
- It supports **partial replay** (e.g., replay only events after a certain timestamp).
- It integrates with CDC tools like Debezium, AWS DMS, or Debezium connectors.

---

## **Components/Solutions**

To implement cursor-based replay, you’ll need:

| Component          | Purpose                                                                 | Examples                                                                 |
|--------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **CDC Tool**       | Captures changes from the source database.                             | Debezium, AWS Database Migration Service (DMS), Debezium Connector for PostgreSQL |
| **Event Store**    | Stores replayable events (e.g., Kafka, S3, or a custom database table). | Apache Kafka, Amazon S3, PostgreSQL `changes` table                          |
| **Replay Logic**   | Reads events from the cursor and applies them to the target.            | Python script, Kubernetes job, Airflow DAG                                |
| **Cursor Tracking**| Tracks progress (e.g., last replayed LSN/timestamp).                    | Debezium offsets, PostgreSQL `pg_lsn` or timestamp columns                 |

---

## **Code Examples: Implementing Cursor-Based Replay**

Let’s walk through a concrete example using:
- **PostgreSQL** as the source database.
- **Debezium** to capture CDC changes.
- **Python** to replay events from a cursor.

---

### **1. Setting Up Debezium for CDC**
Debezium connects to PostgreSQL and streams changes to Kafka. First, ensure you have:
- A running Kafka cluster (e.g., using `docker-compose`).
- A PostgreSQL database with a test table.

#### **Schema Setup**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

INSERT INTO users (name, email) VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com');
```

#### **Running Debezium Connector**
Deploy the Debezium PostgreSQL connector (example config in `debezium.properties`):
```properties
name=postgres-connector
connector.class=io.debezium.connector.postgresql.PostgresConnector
database.hostname=localhost
database.port=5432
database.user=debezium
database.password=dbz
database.dbname=test_db
database.server.name=postgres
include.schema.changes=false
slot.name=debezium
```

Start the connector and verify data in Kafka:
```bash
kafka-console-consumer --bootstrap-server localhost:9092 \
    --topic postgres.test_db.users \
    --from-beginning \
    --property print.key=true \
    --property key.separator=: \
    --property schema.ignore=true
```
You’ll see payloads like:
```json
{
  "op": "c",
  "ts_ms": 1712345678901,
  "source": {"version": "1.0", "connector": "postgresql", ...},
  "payload": {
    "after": {"id": 1, "name": "Alice", "email": "alice@example.com"},
    "before": null,
    "lsn": "0/7D000000"
  }
}
```

---

### **2. Replaying Events from a Cursor**
Now, let’s write a Python script to replay events from a specific LSN (Log Sequence Number).

#### **Python Script: `replay_from_cursor.py`**
```python
import json
from kafka import KafkaConsumer
from psycopg2 import connect, sql

# Config
KAFKA_BROKER = "localhost:9092"
TOPIC = "postgres.test_db.users"
SOURCE_DB = {
    "host": "localhost",
    "database": "test_db",
    "user": "postgres",
    "password": "postgres"
}
START_LSN = "0/7D000000"  # Your starting cursor (e.g., from a previous run)

def get_consumer():
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        group_id="replay-group"
    )

def apply_change(change, db_conn):
    """Apply a CDC change to PostgreSQL."""
    op = change["payload"]["op"]
    data = change["payload"]["after"]

    if op == "c":  # Create
        db_conn.execute(
            sql.SQL("INSERT INTO users (name, email) VALUES (%s, %s)"),
            (data["name"], data["email"])
        )
    elif op == "u":  # Update
        db_conn.execute(
            sql.SQL("UPDATE users SET name=%s, email=%s WHERE id=%s"),
            (data["name"], data["email"], data["id"])
        )
    elif op == "d":  # Delete
        db_conn.execute(
            sql.SQL("DELETE FROM users WHERE id=%s"),
            (data["id"],)
        )
    print(f"Applied {op}: {data}")

def replay_from_lsn(lsn):
    consumer = get_consumer()
    db_conn = connect(**SOURCE_DB)
    cursor = db_conn.cursor()

    for message in consumer:
        change = message.value
        if change["payload"]["lsn"] >= lsn:
            apply_change(change, db_conn)
            print(f"Replayed LSN: {change['payload']['lsn']}")
        else:
            print(f"Skipping LSN (older than {lsn}): {change['payload']['lsn']}")

    db_conn.commit()
    db_conn.close()
    consumer.close()

if __name__ == "__main__":
    replay_from_lsn(START_LSN)
```

---

### **3. Running the Replay**
1. Start Debezium (if not running).
2. Run the script:
   ```bash
   python replay_from_cursor.py
   ```
3. Verify the target database:
   ```sql
   SELECT * FROM users;
   -- Should now match the source!
   ```

---

### **4. Handling Gaps and Errors**
Replay isn’t perfect. Here’s how to handle issues:

#### **a) Tracking Progress (Cursor Persistence)**
Store the last replayed LSN in a file or database:
```python
import json

def save_cursor(lsn):
    with open("last_lsn.json", "w") as f:
        json.dump({"lsn": lsn}, f)

def load_cursor():
    try:
        with open("last_lsn.json", "r") as f:
            return json.load(f)["lsn"]
    except FileNotFoundError:
        return START_LSN
```

#### **b) Retrying Failed Events**
Wrap `apply_change` in a retry loop:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def apply_change(change, db_conn):
    try:
        # Existing logic...
    except Exception as e:
        print(f"Failed to apply {change['payload']['op']}: {e}")
        raise
```

#### **c) Idempotent Operations**
Ensure your replay logic is idempotent (safe to replay the same event multiple times). For example:
- Use `ON CONFLICT DO NOTHING` for inserts.
- Compare timestamps to avoid double-ups.

```python
if op == "c":
    db_conn.execute(
        sql.SQL("""
            INSERT INTO users (name, email)
            VALUES (%s, %s)
            ON CONFLICT (email) DO NOTHING
        """),
        (data["name"], data["email"])
    )
```

---

## **Implementation Guide**

### **Step 1: Choose a CDC Tool**
| Tool               | Use Case                          | Pros                          | Cons                          |
|--------------------|-----------------------------------|-------------------------------|-------------------------------|
| Debezium           | Kafka-based CDC                   | Mature, supports many DBs     | Requires Kafka infrastructure |
| AWS DMS            | Cloud-native migration            | Fully managed                 | Expensive                     |
| Debezium + S3      | Immutable event storage           | Cheap, durable                | No real-time replay           |
| Custom PostgreSQL  | Lightweight CDC                   | No dependencies               | Harder to maintain            |

### **Step 2: Define Your Cursor Strategy**
- **LSN (Log Sequence Number)**: Used by Debezium/PostgreSQL. Best for raw performance.
- **Timestamp**: Human-readable but less precise (may miss events).
- **Sequence ID**: Database-specific (e.g., `id` column). Simple but not scalable.

### **Step 3: Design Your Replay Logic**
1. **Parse CDC Events**: Use the tool’s output format (e.g., Debezium’s Kafka payload).
2. **Apply Changes**: Use your target database’s API (e.g., `INSERT`, `UPDATE`, `DELETE`).
3. **Track Progress**: Save the last LSN/timestamp to resume later.

### **Step 4: Test Thoroughly**
- **Edge Cases**:
  - Replay empty streams.
  - Replay with gaps (simulate dropped events).
  - Handle schema changes (e.g., column additions).
- **Performance**: Test with large datasets. Consider batching changes.

### **Step 5: Monitor and Alert**
- Log replay progress (e.g., `INFO: Replayed 1000 events since LSN X`).
- Alert on failures (e.g., "Replay stalled at LSN Y for 5 minutes").

---

## **Common Mistakes to Avoid**

### **1. Ignoring Idempotency**
Replaying the same event twice can corrupt data. Use:
- Database constraints (`UNIQUE`, `ON CONFLICT DO NOTHING`).
- Event timestamps to detect duplicates.

### **2. Not Handling Schema Changes**
If your database schema evolves (e.g., adding a column), your replay script may fail. Solutions:
- Use a schema registry (e.g., Debezium’s `schema.evolution`).
- Write dynamic SQL generators.

### **3. Overlooking Performance**
Replaying millions of events can be slow. Optimize with:
- **Batching**: Apply changes in bulk (e.g., `INSERT ... VALUES (v1), (v2)`).
- **Parallelism**: Use multiple consumers (but ensure order constraints).
- **Indexing**: Build indexes on replayed tables before replaying.

### **4. Not Tracking Cursor Progress**
Without persisting the last LSN, you’ll replay everything every time. Use:
- A file (simple but prone to loss).
- A database table (more reliable).
- Kafka consumer offsets (if using Kafka).

### **5. Assuming CDC is Real-Time**
CDC tools buffer changes. If your replay script is slow, you may fall behind. Mitigate with:
- Asynchronous replay (e.g., a Kubernetes job).
- Checkpointing (save progress frequently).

---

## **Key Takeaways**

- **Cursor-based replay** is essential for rebuilding system state from CDC streams.
- **Components**:
  - CDC tool (Debezium, DMS).
  - Event store (Kafka, S3).
  - Replay logic (Python, Java, etc.).
  - Cursor tracking (LSN, timestamp, or sequence ID).
- **Best Practices**:
  - Design replay logic to be **idempotent**.
  - Handle **schema changes** gracefully.
  - Optimize for **performance** (batch, parallelize).
  - **Persist cursor progress** to avoid full replays.
- **Tradeoffs**:
  - **Pros**: Flexible, supports partial replay, works with any event store.
  - **Cons**: Complex to implement, requires monitoring, and can be slow for large datasets.

---

## **Conclusion**

Cursor-based replay is a powerful technique for rebuilding system state from CDC data. Whether you’re recovering from a failure, migrating data, or experimenting with event sourcing, this pattern gives you the flexibility to replay events from any point in time.

Start small:
1. Set up Debezium or your preferred CDC tool.
2. Replay a subset of events to a test database.
3. Gradually incorporate retries, error handling, and performance optimizations.

For production systems, consider:
- **Automating replays** (e.g., with Airflow or Kubernetes).
- **Monitoring replay progress** (e.g., Prometheus metrics).
- **Backing up your cursor state** (e.g., in a distributed lock).

By mastering cursor-based replay, you’ll gain the confidence to handle the most challenging data recovery scenarios—without pulling your hair out.

---
**Further Reading:**
- [Debezium Documentation](https://debezium.io/documentation/reference/)
- [PostgreSQL CDC with Logical Decoding](https://www.postgresql.org/docs/current/logicaldecoding.html)
- [Event Sourcing Patterns](https://eventstore.com/blog/event-sourcing-patterns)

**Got questions?** Drop them in the comments—or tweet at me @your_handle. Happy replaying!
```