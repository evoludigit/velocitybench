```markdown
---
title: "Building a MySQL CDC Adapter: Real-Time Data Sync Made Simple"
author: "Alex Carter"
date: 2023-11-15
tags: ["database", "cdc", "mysql", "backend"]
image: "images/cdc-pipeline.jpg"
---

# Building a MySQL CDC Adapter: Real-Time Data Sync Made Simple

## Introduction

Let's talk about real-time data. Whether you're building a financial dashboard that needs to reflect transactions immediately, a customer service system that tracks activity in real time, or an analytics platform that updates insights as data flows in, you need data to move *fast*—not with batch delays of minutes or hours, but as it happens.

MySQL CDC (Change Data Capture) is your secret weapon here. It lets you watch database changes in real time and sync them to other systems before users even realize what happened. But MySQL's built-in CDC features (like the binary log) aren't always enough for production-grade applications. That's where a **CDC Adapter** comes in—it bridges the gap between your database and your downstream systems, making real-time data processing simple and reliable.

In this guide, I'll walk you through the **MySQL CDC Adapter pattern**, covering:
- Why CDC matters
- The challenges of doing it without an adapter
- How to build one step-by-step
- Practical code examples using Python and a popular CDC library
- Common pitfalls to avoid
- When (and when *not* to) use this pattern

Let's dive in.

---

## The Problem: Why You Need a CDC Adapter

### The Challenge of Raw CDC

MySQL tracks changes via the [binary log](https://dev.mysql.com/doc/refman/8.0/en/binary-log.html), which records every write operation (`INSERT`, `UPDATE`, `DELETE`) in a sequence. This is powerful, but raw binary log data is messy:

1. **Unstructured format**: The binary log isn’t in JSON or XML—it’s a binary format that requires parsing.
2. **No built-in delivery**: MySQL doesn’t ship logs to other systems automatically.
3. **Complexity for real-time apps**: If you try to consume the binary log directly (e.g., with `mysqlbinlog`), your code quickly becomes a maintenance nightmare. You’ll need to:
   - Decode each event manually.
   - Handle networking for remote replicas.
   - Manage failures and retries.

### The Cost of Batch Processing

If you don’t use CDC, you typically rely on **batch processing**, such as:
- Cron jobs that dump tables periodically.
- Nightly ETL pipelines.
- Scheduled snapshots.

These methods introduce:
- **Latency**: Users see stale data until the next batch.
- **Lots of transient data**: A system may process the same data multiple times in a batch window, leading to inconsistencies.
- **Hard-to-debug issues**: A batch job that fails might leave your system out of sync for hours.

### The Real-World Pain Points

As a backend engineer, you’ve probably seen these scenarios:
- A user updates their profile, but the UI doesn’t show changes until the next day because you’re using batch exports.
- Your analytics dashboard is slow because it’s based on last-night’s CSV dump.
- Your message broker starts receiving duplicate events after a server crash.

An adapter solves these problems by turning MySQL’s CDC into an easy-to-use API for real-time data.

---

## The Solution: What Is a MySQL CDC Adapter?

A **CDC Adapter** is a lightweight service that:
1. **Watches the binary log** for changes in MySQL.
2. **Transforms those changes** into a structured format (e.g., JSON, Avro).
3. **Delivers them** to subscribers (e.g., Kafka, HTTP endpoints, or a downstream database).
4. **Handles failures** automatically, ensuring no data is lost.

Think of it like a data filter that lets you consume MySQL changes in a way that’s easy to integrate with other systems.

### Why This Pattern?
This pattern is great for:
- **Real-time applications**: Dashboards, live updates, or fraud detection systems.
- **Analytics**: Near real-time reporting (e.g., Google Analytics-style tracking).
- **Data consistency**: Keeping multiple systems in sync (e.g., a microservices architecture).

---

## Components of a MySQL CDC Adapter

Here’s a high-level architecture of a CDC adapter:

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MySQL     │────>│   CDC Adapter  │────>│   Downstream    │
│             │     │  (Python/Java) │     │   System        │
│ - Table A   │     │ - Parses binlog │     │ - API           │
│ - Table B   │     │ - Processes    │     │ - Kafka topic   │
└─────────────┘     │   events         │     │ - Database      │
                    └─────────────────┘     └─────────────────┘
```

### Key Components:
1. **Binary Log Consumer**: Connects to MySQL’s binary log to read changes.
2. **Event Parser**: Decodes raw binary log events into structured data.
3. **Event Router**: Routes events to the right downstream system (API, Kafka, etc.).
4. **Fault Tolerance Layer**: Handles retries, dead-letter queues, or checkpointing.

---

## Implementation Guide: Building a Simple CDC Adapter

In this section, we’ll build a Python-based CDC adapter using the [`debezium`](https://debezium.io/) MySQL connector (via a Python wrapper) and Flask for HTTP delivery.

### Step 1: Set Up Your Environment

First, install the required libraries:

```bash
pip install mysql-connector-python flask
```

### Step 2: Connect to MySQL’s Binary Log

We’ll use Debezium’s MySQL Connector via the `mysqlbinlog` command, but for simplicity, we’ll simulate CDC with a lightweight parser. In production, you’d use a proper CDC tool like Debezium or Kafka Connect.

```python
# binlog_parser.py
import mysql.connector
from mysql.connector import Error

def get_binlog_position():
    """Get the current position of the binary log."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="your_user",
            password="your_password",
            database="your_db"
        )
        cursor = conn.cursor()
        cursor.execute("SHOW MASTER STATUS;")
        binlog_pos = cursor.fetchone()
        cursor.close()
        conn.close()
        return binlog_pos
    except Error as e:
        print(f"Error: {e}")
        return None
```

### Step 3: Parse Binlog Events (Simplified)

For simplicity, let’s simulate a CDC adapter that tracks changes to a `users` table. A real-world adapter would use Debezium or similar libraries.

```python
def simulate_cdc_events():
    """Simulate CDC events via a cursor."""
    # This is a mock-up; real CDC would stream from the binlog.
    events = [
        {"event": "INSERT", "table": "users", "data": {"id": 1, "name": "Alice"}},
        {"event": "UPDATE", "table": "users", "data": {"id": 1, "name": "Alice Smith"}},
    ]
    return events
```

### Step 4: Create an HTTP Endpoint to Deliver Events

We’ll use Flask to expose a REST endpoint that delivers CDC events in real time.

```python
# app.py
from flask import Flask, jsonify
from binlog_parser import simulate_cdc_events

app = Flask(__name__)

@app.route('/cdc/events', methods=['GET'])
def get_cdc_events():
    events = simulate_cdc_events()
    return jsonify({"data": events})

if __name__ == '__main__':
    app.run(port=5000)
```

### Step 5: Deploy a Real CDC Adapter with Debezium

The above example is a joke. Let’s instead use **Debezium**, a Kafka Connect connector for MySQL CDC.

#### Step 1: Set Up Kafka and Kafka Connect
Install Kafka and Kafka Connect locally (or use Confluent Platform).

#### Step 2: Configure Debezium MySQL Connector

Add this to your `connect-my-sql.properties`:

```properties
name.my-sql-connector=mysql-connector
connector.class=io.debezium.connector.mysql.MySqlConnector
database.hostname=localhost
database.port=3306
database.user=your_user
database.password=your_password
database.server.id=184054
database.server.name=mysql-server
database.include.list=your_db
database.history.kafka.bootstrap.servers=localhost:9092
database.history.kafka.topic=schema-changes.your_db
```

#### Step 3: Run the Connector

```bash
bin/connect-standalone.sh config/connect-standalone.properties config/connect-my-sql.properties
```

#### Step 4: Consume Events via Kafka

Use the Kafka CLI to read the CDC events:

```bash
kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic your_db.users \
    --from-beginning \
    --property print.key=true \
    --property key.separator=':' \
    --property schema.registry.url=http://localhost:8081
```

You’ll see structured JSON like:

```json
{
  "op": "c",
  "ts_ms": 1699999999,
  "row": {
    "id": 1,
    "name": "Alice",
    "updated_at": "2023-11-15T12:00:00Z"
  }
}
```

---

## Common Mistakes to Avoid

1. **Ignoring Failure Handling**
   - If your adapter crashes, CDC events may be lost. Always implement:
     - Checkpointing (track processed offsets).
     - Retries (exponential backoff).
     - Dead-letter queues for poison pills.

2. **Not Filtering Events**
   - If you’re watching many tables, only forward events for the ones your app cares about.

3. **Overloading the Adapter**
   - If your app depends on the adapter, make it resilient. Use:
     - Load balancing (if scaling).
     - Circuit breakers (if downstream systems fail).

4. **Assuming MySQL’s Binlog is Stable**
   - The binary log can be purged if `log_bin_truncate_on_expire` is set. Keep a backup strategy.

---

## Key Takeaways

- **CDC enables real-time data processing**, but raw MySQL binlog is hard to work with directly.
- A **CDC Adapter** acts as a bridge between MySQL’s CDC and your downstream systems (APIs, Kafka, databases).
- **Use Debezium or Kafka Connect** for production-grade CDC in MySQL.
- **Always account for failures**: Implement retries, checkpoints, and dead-letter queues.
- **Start simple**: Simulate CDC with mock data, then graduate to Debezium.

---

## Conclusion

Building a MySQL CDC adapter is a game-changer for real-time applications. By understanding the challenges of raw CDC and designing an adapter that handles parsing, delivery, and fault tolerance, you can turn MySQL’s change tracking into a powerful tool for keeping your data in sync across systems.

### Next Steps
1. Try running Debezium with your own MySQL database.
2. Explore **Kafka as a CDC bus**: Use Kafka to decouple producers (MySQL) from consumers.
3. Consider **event sourcing**: Store CDC events as immutable logs for auditing/replay.

Happy coding!

---
### Further Reading
- [Debezium MySQL Connector Docs](https://debezium.io/documentation/reference/stable/connectors/mysql.html)
- [Kafka Connect](https://kafka.apache.org/documentation/#connect)
- [MySQL Binary Log](https://dev.mysql.com/doc/refman/8.0/en/binlog.html)

---
```sql
-- Example MySQL schema for CDC testing
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```