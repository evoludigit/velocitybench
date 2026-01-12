```markdown
---
title: "Change Data Capture (CDC) Cursor-Based Replay: A Beginner's Guide"
date: 2023-10-15
author: "Alex Carter"
description: "Learn how to implement CDC cursor-based replay for event replay and uptime resilience. Practical code examples included."
tags: ["database", "CDC", "event-driven", "replay", "patterns"]
---

# Change Data Capture (CDC) Cursor-Based Replay: A Beginner's Guide

![CDC Cursor-Based Replay Visualization](https://miro.medium.com/max/1400/1*ABC123XYZ.png)
*Imagine a cursor tracking your database's transactions like a bookmark in a journal.*

Have you ever wondered how services like Uber or PayPal ensure that a user’s ride or payment history *never* goes missing—even if the system crashes or restarts? The answer lies in **Change Data Capture (CDC) Cursor-Based Replay**, a pattern that acts like a replay button for database changes, ensuring no data is lost during disruptions.

In this guide, we’ll explore how cursor-based CDC works, why it’s valuable, and how to implement it in real-world applications. You’ll leave with practical SQL and application code examples, ready to build resilient systems from scratch.

---

## **The Problem: Without CDC Cursor-Based Replay, Systems Face Challenges**

Imagine this: Users trigger events (e.g., ordering a pizza, depositing money) via your app. Your database records these events, and your backend processes them asynchronously (e.g., sending notifications, updating analytics). But what happens if:

1. **A crash occurs mid-flight**: A system restart could cause events to be reprocessed—or worse, missed entirely.
2. **Network delays happen**: Queues can overflow, leading to lost data or duplicate processing.
3. **Manual recovery is tedious**: Without a clear checkpoint, rolling back or replaying events requires manual intervention.

This is where CDC (Change Data Capture) comes in. CDC monitors database changes and provides a structured way to replay them later. But **cursor-based replay** is the smart way to do it—it avoids reprocessing everything from scratch and instead resumes from the last known position.

---

## **The Solution: Cursor-Based CDC Replay**

Cursor-based CDC replay leverages database cursors to track the state of transactions. Here’s how it works:

1. **Database emits changes via logs** (e.g., PostgreSQL’s `pg_logical`, Debezium, or Devexpress tools).
2. **Your app consumes changes in batches**, using a cursor (like a bookmark) to track the last processed change.
3. **If the system crashes**, the cursor ensures replay starts from the right position, never missing or duplicating events.

### **Why Cursor-Based Replay?**
- **Efficiency**: Only reprocess changes after the cursor (no full history).
- **Exactly-once processing**: Avoids duplicates by tracking processed data.
- **Uptime resilience**: Critical for financial, e-commerce, or SaaS apps.

### **Tradeoffs**
- **Cursor management requires care**: If the cursor is lost, you risk reprocessing everything.
- **Not all databases support CDC natively**: PostgreSQL, MySQL (with binlogs), and MongoDB are common, but Oracle and SQL Server require extensions.

---

## **Components of a Cursor-Based CDC Replay System**

A cursor-based CDC system typically includes:

1. **Database CDC Source** (e.g., Debezium, Debezium Connector for MySQL/PostgreSQL).
2. **Cursor Storage** (a table to track the last processed position).
3. **Consumer Application** (processes changes via a message queue like Kafka/Pulsar).
4. **Retry & Dead-Letter Queue** (for failed reprocessing).

---

## **Step-by-Step Implementation Guide**

### **1. Set Up a Database Table for Cursor Tracking**
First, create a table to store the last processed position (e.g., `cdc_cursor`).

```sql
CREATE TABLE cdc_cursor (
    table_name VARCHAR(100) PRIMARY KEY,
    last_processed_id INT,  -- Unique ID or LSN (Log Sequence Number)
    last_processed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **2. Enable CDC in PostgreSQL (Example)**
If using PostgreSQL, enable `pg_logical_replication` and set up a logical decoding slot:

```sql
-- Enable replication
ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_replication_slots = 10;

-- Restart PostgreSQL

-- Create a slot (e.g., for the 'orders' table)
CREATE PUBLICATION cdc_orders FOR TABLE orders;
```

### **3. Consume Changes via Debezium (Kafka Integration)**
Debezium captures changes and streams them to Kafka. Configure a Debezium connector:

```yaml
# Example Debezium Connector Config (MySQL)
name: mysql-cdc-orders
config:
  connector.class: io.debezium.connector.mysql.MySqlConnector
  database.hostname: mysql-host
  database.port: 3306
  database.user: debezium
  database.password: dbz
  database.server.id: 184054
  database.server.name: mysql-primary
  database.include.list: orders
  database.history.kafka.bootstrap.servers: kafka:9092
  database.history.kafka.topic: dbhistory.orders
  include.schema.changes: true
```

### **4. Implement Cursor-Based Processing**
In your consumer application (e.g., Java/Kotlin), track the cursor and replay missed changes:

#### **Java Example (Kafka Consumer)**
```java
import org.apache.kafka.clients.consumer.*;

public class CursorAwareKafkaConsumer {
    private final KafkaConsumer<String, String> consumer;
    private final Map<String, Long> cursorState = new HashMap<>();

    public CursorAwareKafkaConsumer() {
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "cdc-processor");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");
        this.consumer = new KafkaConsumer<>(props);
    }

    public void processMessages() {
        consumer.subscribe(Collections.singletonList("orders-changes"));

        while (true) {
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofSeconds(1));
            for (ConsumerRecord<String, String> record : records) {
                String topicAndPartition = record.topic() + "." + record.partition();
                long offset = record.offset();

                // Track cursor per table/partition
                cursorState.merge(topicAndPartition, offset, Math::max);

                // Replay logic
                try {
                    processOrderChange(record.value());
                } catch (Exception e) {
                    // Retry or move to DLQ
                    System.err.println("Error processing: " + record.value());
                }
            }

            // Periodically persist cursor
            persistCursor();
        }
    }

    private void persistCursor() {
        // Save cursorState to database (e.g., `cdc_cursor` table)
        for (Map.Entry<String, Long> entry : cursorState.entrySet()) {
            String tableName = extractTableNameFromTopic(entry.getKey());
            saveCursor(tableName, entry.getValue());
        }
    }

    private void saveCursor(String tableName, long offset) {
        // SQL to update `cdc_cursor` table
        String sql = "INSERT INTO cdc_cursor (table_name, last_processed_id) VALUES ('" + tableName + "', " + offset + ") ON CONFLICT (table_name) DO UPDATE SET last_processed_id = EXCLUDED.last_processed_id";
        // Execute via JDBC or ORM
    }
}
```

#### **Python Example (Using Debezium + PostgreSQL)**
```python
import psycopg2
from kafka import KafkaConsumer

def get_last_cursor(table_name):
    conn = psycopg2.connect("dbname=your_db user=your_user")
    cursor = conn.cursor()
    cursor.execute("SELECT last_processed_id FROM cdc_cursor WHERE table_name = %s", (table_name,))
    return cursor.fetchone()[0] if cursor.rowcount > 0 else 0

def save_cursor(table_name, offset):
    conn = psycopg2.connect("dbname=your_db user=your_user")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cdc_cursor (table_name, last_processed_id) VALUES (%s, %s) ON CONFLICT (table_name) DO UPDATE SET last_processed_id = EXCLUDED.last_processed_id",
        (table_name, offset)
    )
    conn.commit()

def process_orders_changes():
    consumer = KafkaConsumer(
        'orders-changes',
        bootstrap_servers=['kafka:9092'],
        group_id='python-consumer',
        auto_offset_reset='earliest'
    )
    last_offset = get_last_cursor('orders')  # Load from cursor

    for message in consumer:
        if message.offset <= last_offset:
            continue  # Skip already processed

        try:
            process_order(message.value.decode('utf-8'))
            save_cursor('orders', message.offset)
        except Exception as e:
            print(f"Failed to process: {message.value}, offset: {message.offset}")
```

---

## **Common Mistakes to Avoid**

1. **Not persisting cursors frequently**
   - *Risk*: Cursor loss on crash → reprocessing from scratch.
   - *Fix*: Persist every N messages or on failure.

2. **Ignoring dead-letter queues (DLQ)**
   - *Risk*: Failed reprocessing silently drops data.
   - *Fix*: Use DLQ for retries or manual inspection.

3. **Assuming CDC is "set and forget"**
   - *Risk*: Schema changes may break consumers.
   - *Fix*: Test CDC with schema migrations.

4. **Overlooking timeouts**
   - *Risk*: Long-running transactions block reprocessing.
   - *Fix*: Set reasonable timeouts for CDC consumers.

5. **Not testing failure scenarios**
   - *Risk*: System fails silently during outages.
   - *Fix*: Simulate crashes and verify replay works.

---

## **Key Takeaways**

✅ **Cursor-based CDC replay** ensures no data loss during crashes.
✅ **Efficiency**: Only reprocess changes after the last cursor position.
✅ **Resilience**: Works with databases like PostgreSQL, MySQL, and MongoDB.
✅ **Tradeoffs**: Requires cursor management and testing for failure cases.

🚨 **Avoid**:
- Skipping cursor persistence.
- Ignoring dead-letter queues.
- Assuming CDC is foolproof.

---

## **Conclusion**

Cursor-based CDC replay is a powerful tool for building resilient, event-driven systems. By tracking the last processed position, you ensure uptime even during crashes or network issues. Start with PostgreSQL or MySQL + Debezium, then extend to other databases as needed.

**Next Steps**:
1. Deploy CDC on PostgreSQL/MySQL and test with simulated crashes.
2. Integrate a message queue (Kafka/Pulsar) for scalability.
3. Automate cursor recovery during restarts.

Happy coding—and may your systems never lose a transaction again! 🚀
```

---
**Appendix**:
- [Debezium Documentation](https://debezium.io/documentation/reference/stable/)
- [PostgreSQL CDC Guide](https://www.citusdata.com/blog/2019/04/24/postgresql-change-data-capture/)
- [Kafka Consumer API](https://kafka.apache.org/documentation/#consumerapi)