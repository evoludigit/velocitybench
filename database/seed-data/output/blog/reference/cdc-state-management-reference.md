**[Pattern] CDC State Management Reference Guide**
*Version 1.0*
*Last Updated: [Insert Date]*

---

### **1. Overview**
The **Change Data Capture (CDC) State Management** pattern ensures reliable, scalable processing of incremental data changes by maintaining subscription state across distributed systems. This pattern addresses challenges in event-driven architectures where subscribers (e.g., microservices, batch processors, or analytics engines) must reprocess or ignore outdated events.

Key use cases include:
- **Event Sourcing:** Replaying historical changes to a stateful consumer.
- **Idempotent Processing:** Preventing duplicate work when a subscriber restart occurs.
- **Partitioned Streams:** Scaling CDC pipelines across multiple subscribers without conflicts.
- **Exactly-Once Processing:** Guaranteeing no data loss or duplication in distributed workflows.

The pattern leverages a **state repository** (e.g., a database, key-value store, or topic offset manager) to track consumed records. Subscribers regularly check their state against the CDC source (e.g., a database log, Kafka topic, or message queue) and apply only new or unreplicated changes.

---
### **2. Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                                                                                 | **Example**                                                                                     |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |-------------------------------------------------------------------------------------------------|
| **CDC Source**            | The system emitting change events (e.g., database WAL, Kafka topic, or log-based system).                                                                                                                                                                         | PostgreSQL logical decoding, Debezium, or Kafka Connect.                                           |
| **State Repository**      | A durable store tracking which records a subscriber has processed.                                                                                                                                                                                              | Redis, DynamoDB, or a database table with `(topic, partition, offset)` columns.                   |
| **Subscription State**    | The latest consumed position (e.g., offset, timestamp, or transaction ID) per subscriber.                                                                                                                                                                       | `{"kafka_topic": "orders", "partition": 0, "offset": 1000}`                                       |
| **Checkpointing**         | Periodically writing subscription state to the repository (e.g., after processing *N* records or on failover).                                                                                                                                          | Synchronous write to state repo after every batch.                                                |
| **Rebalancing**           | Redistributing partitions/subscriptions when a subscriber fails or scales.                                                                                                                                                                                        | Kafka consumer rebalance on group leader change.                                                   |
| **Idempotency Key**       | A unique identifier ensuring reprocessed events are safely applied (e.g., a row’s primary key or event timestamp).                                                                                                                                          | `order_id = "ORD-123"` prevents duplicate order processing.                                         |
| **Slack Period**          | The allowed time gap between CDC source updates and subscriber processing (configurable for fault tolerance).                                                                                                                                                    | A 5-minute lag for high-throughput systems.                                                       |
| **Compaction**            | Removing stale state entries (e.g., after processing a checkpointed batch) to reduce storage overhead.                                                                                                                                                 | Truncate state entries older than 24 hours.                                                      |

---
### **3. Schema Reference**
The **State Repository** requires a schema to store subscription state for scalable, distributed CDC consumers. Below are common designs:

#### **Option 1: Key-Value Store (Redis/DynamoDB)**
| **Field**          | **Type**       | **Description**                                                                                     | **Example Value**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `subscription_id`  | String (PK)    | Unique identifier for the subscriber (e.g., Kafka consumer group ID).                              | `"orders-service-group"`               |
| `topic`            | String         | Name of the CDC source topic/stream.                                                               | `"orders"`                            |
| `partition`        | Integer        | Partition ID for partitioned streams (set to `null` for non-partitioned sources).                 | `2`                                   |
| `offset`           | Integer/UUID   | Latest processed offset (or checkpoint ID).                                                       | `1500`                                |
| `last_checkpoint`  | Timestamp      | When the state was last updated (for lag calculations).                                            | `"2024-02-20T14:30:00Z"`              |
| `slack_period_sec` | Integer        | Maximum allowed lag in seconds (default: `300`).                                                  | `600`                                 |

**Query:** `GET {subscription_id}`
**Response:**
```json
{
  "topic": "orders",
  "partition": 2,
  "offset": 1500,
  "last_checkpoint": "2024-02-20T14:30:00Z"
}
```

---

#### **Option 2: Relational Database (PostgreSQL/MySQL)**
| **Column**         | **Type**       | **Description**                                                                                     | **Example**               |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------|
| `subscription_id`  | `VARCHAR(64)`  | Unique subscriber ID (primary key).                                                              | `"orders-consumer"`       |
| `source_type`      | `VARCHAR(32)`  | Type of CDC source (e.g., `"kafka"`, `"debezium"`).                                               | `"kafka"`                 |
| `source_name`      | `VARCHAR(128)` | Name of the source (e.g., topic, schema, or table).                                               | `"orders"`                |
| `partition`        | `INTEGER`      | Partition ID (nullable for non-partitioned sources).                                               | `NULL`                    |
| `offset`           | `BIGINT/UUID`  | Latest processed offset or checkpoint.                                                           | `1500`                     |
| `processing_time`  | `TIMESTAMP`    | When the offset was last applied (for monitoring).                                               | `"2024-02-20 14:30:00"`  |
| `lag_seconds`      | `INTEGER`      | Current lag (source_offset - processed_offset).                                                  | `30`                      |

**SQL Example (Insert):**
```sql
INSERT INTO subscription_state (
  subscription_id, source_type, source_name, partition, offset, processing_time
) VALUES (
  'orders-consumer', 'kafka', 'orders', 2, 1500, NOW()
);
```

**SQL Example (Update Lag):**
```sql
UPDATE subscription_state
SET lag_seconds = (
  SELECT COUNT(*) FROM kafka_offsets
  WHERE topic = 'orders' AND partition = 2 AND offset > 1500
)
WHERE subscription_id = 'orders-consumer';
```

---
#### **Option 3: File-Based State (Local Storage)**
For lightweight consumers (e.g., standalone scripts), use a JSON file:
```json
{
  "subscriptions": {
    "orders-service": {
      "source": "kafka",
      "topic": "orders",
      "partition": 2,
      "offset": "1500",
      "last_updated": "2024-02-20T14:30:00Z"
    }
  }
}
```
**Tools:** Use `etcd` or `Consul` for cluster-wide file synchronization.

---
### **4. Query Examples**
#### **A. Check Current Subscription State**
**Redis:**
```bash
GET "orders-service:orders:2"
# => "1500"
```

**SQL:**
```sql
SELECT offset, processing_time
FROM subscription_state
WHERE subscription_id = 'orders-consumer';
```

#### **B. Calculate Lag (Unprocessed Records)**
**SQL (Kafka Example):**
```sql
WITH latest_offset AS (
  SELECT offset FROM kafka_offsets
  WHERE topic = 'orders' AND partition = 2
  ORDER BY offset DESC LIMIT 1
)
SELECT
  (SELECT offset FROM latest_offset) - s.offset AS lag,
  NOW() - s.processing_time AS processing_lag
FROM subscription_state s
WHERE s.subscription_id = 'orders-consumer';
```

**Python (Using Kafka Python Client):**
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer('orders', group_id='orders-consumer')
latest_offset = consumer.end_offsets([2])[2]  # Partition 2
state_offset = redis.get(f"orders-consumer:orders:2")
lag = latest_offset - int(state_offset)
print(f"Current lag: {lag}")
```

#### **C. Update State After Processing Batch**
**Redis (Pipeline):**
```python
pipeline = redis.pipeline()
pipeline.set("orders-consumer:orders:2", 1600)
pipeline.set("orders-consumer:last_checkpoint", datetime.now())
pipeline.execute()
```

**SQL:**
```sql
UPDATE subscription_state
SET offset = 1600,
    processing_time = NOW(),
    lag_seconds = (
      SELECT COUNT(*) FROM kafka_offsets
      WHERE topic = 'orders' AND partition = 2 AND offset > 1600
    )
WHERE subscription_id = 'orders-consumer';
```

#### **D. Handle Subscriber Failover**
1. **Detect Failover:** Monitor `last_checkpoint` timeouts (e.g., >300s).
2. **Recover State:**
   ```sql
   -- Reset to earliest processed offset (if idempotent)
   UPDATE subscription_state
   SET offset = 0
   WHERE subscription_id = 'orders-consumer';
   ```
   Or replay from a checkpoint:
   ```python
   # Replay from known safe offset
   consumer.seek(2, 1500)  # Partition 2, offset 1500
   ```

---
### **5. Implementation Steps**
#### **Step 1: Define Subscription State**
- **For Kafka:** Use `ConsumerGroupCoordinator` offsets or a custom state repo.
- **For Database CDC:** Track `lsn` (Log Sequence Number) or transaction IDs.
- **For Event Sourcing:** Store event IDs (e.g., `event_id`, `processed_at`).

#### **Step 2: Checkpoint State Periodically**
```python
def process_batch(consumer, state_key, batch_size=1000):
    records = consumer.poll(timeout_ms=1000, max_records=batch_size)
    for record in records:
        process_record(record.value)
    state = redis.get(state_key)
    redis.set(state_key, consumer.position())  # Update offset
```
**Triggers:**
- After processing *N* records.
- On consumer group rebalance.
- Before application shutdown.

#### **Step 3: Handle Rebalances**
- **Kafka:** Implement `on_partitions_revoked` hook to checkpoint state.
- **Custom:** Use lease-based coordination (e.g., ZooKeeper/Kafka leader election).

#### **Step 4: Monitor Lag**
```sql
-- Alert if lag > 5 minutes
SELECT subscription_id, lag_seconds
FROM subscription_state
WHERE lag_seconds > 300;
```
**Tools:** Prometheus + Grafana for metrics (e.g., `cdc_subscription_lag_seconds`).

#### **Step 5: Ensure Idempotency**
- **Database CDC:** Use `UPDATE ... ON CONFLICT` or transaction IDs.
  ```sql
  INSERT INTO orders (id, status)
  VALUES ('ORD-123', 'PROCESSED')
  ON CONFLICT (id) DO NOTHING;
  ```
- **Kafka:** Use `transactional_id` for exactly-once semantics.

---
### **6. Query Examples for Common Scenarios**
| **Scenario**               | **Query**                                                                                     | **Purpose**                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Verify subscriber health** | `SELECT processing_time FROM subscription_state ORDER BY processing_time;`                   | Detect stalled consumers.                                                                        |
| **Find orphaned partitions** | `SELECT partition FROM subscription_state WHERE offset = 0;`                                 | Identify partitions not yet assigned to a subscriber.                                           |
| **Calculate global lag**      | `SELECT AVG(lag_seconds) FROM subscription_state;`                                            | Monitor system-wide CDC health.                                                              |
| **Roll back to checkpoint**  | `UPDATE subscription_state SET offset = 999 WHERE subscription_id = 'faulty-consumer';`      | Recover from a crashed subscriber.                                                            |
| **Compact old state**       | `DELETE FROM subscription_state WHERE processing_time < NOW() - INTERVAL '7 days';`           | Free up storage for long-running consumers.                                                   |

---
### **7. Error Handling**
| **Error**                          | **Solution**                                                                                     | **Example**                                                                                     |
|------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **State repo unavailable**         | Fallback to last known good offset or replay from source beginning.                            | `offset = 0` if state repo fails.                                                              |
| **Duplicate processing**           | Use idempotent operations (e.g., `INSERT ... ON CONFLICT`).                                       | `ON CONFLICT (order_id) DO UPDATE SET status = 'PROCESSED';`                                  |
| **Lag too high**                   | Scale out subscribers or increase `slack_period_sec`.                                            | Add a new consumer instance to partition 2.                                                    |
| **State repo corruption**          | Rebuild from source logs (e.g., Kafka `__consumer_offsets` table).                             | `SELECT * FROM __consumer_offsets WHERE group_id = 'orders-consumer';`                         |
| **Source offset out of sync**      | Replay from the latest checkpoint in the state repo.                                            | Seek to `redis.get("orders-consumer:offset")` in Kafka.                                       |

---
### **8. Performance Considerations**
| **Factor**               | **Recommendation**                                                                                     | **Tradeoff**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Checkpoint Frequency** | Write state after every batch (e.g., 1000 records) or on failover.                                   | Higher I/O overhead vs. risk of losing uncheckpointed work.                                       |
| **State Repository**      | Use low-latency stores (Redis, DynamoDB) for high-throughput systems.                               | Higher cost vs. durability guarantees.                                                          |
| **Batch Size**           | Balance CPU usage (small batches) vs. network overhead (large batches).                            | Smaller batches reduce memory pressure but increase checkpoint frequency.                         |
| **Idempotency Overhead** | Use transaction IDs or hashes (e.g., `SHA-256(event)`) for deduplication.                          | Slightly slower processing if deduplication is required.                                          |
| **Rebalance Strategy**   | Prefer `cooperative_rebalance` (Kafka) over manual assignment for dynamic workloads.                | Slower rebalance vs. deterministic assignment.                                                   |

---
### **9. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Event-Driven Architecture](https://docs.microsoft.com/en-us/azure/architecture/patterns/event-driven-architecture)** | Decouples producers and consumers using events.                                                   | When CDC feeds multiple independent systems (e.g., notifications + analytics).                      |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Manages distributed transactions via local transactions and compensating actions.                 | When CDC changes require complex workflows (e.g., order processing with payments).                 |
| **[CQRS](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)** | Separates read and write models to optimize performance.                                           | When read-heavy analytical workloads conflict with write-heavy CDC.                                 |
| **[Backpressure Handling](https://www.baeldung.com/java-backpressure)** | Controls consumer speed to avoid overwhelming downstream systems.                                 | When subscribers cannot keep up with CDC throughput.                                              |
| **[Dead Letter Queue (DLQ)](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-queue-output)** | Routes failed records for manual inspection.                                                       | When CDC data contains malformed records or business logic errors.                               |
| **[Exactly-Once Processing](https://www.confluent.io/blog/kafka-exactly-once-semantics-made-simple/)** | Ensures each record is processed once using transactions.                                       | Critical systems where data integrity is non-negotiable (e.g., finance).                          |

---
### **10. Example Implementation (Python + Kafka + Redis)**
```python
import redis
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

class CDCSubscriber:
    def __init__(self, subscription_id, topic, partition=0):
        self.subscription_id = subscription_id
        self.topic = topic
        self.partition = partition
        self.redis = redis.Redis(host='localhost', port=6379)
        self.consumer = KafkaConsumer(
            topic,
            group_id=subscription_id,
            bootstrap_servers='localhost:9092',
            enable_auto_commit=False
        )

    def process_batch(self, batch_size=1000):
        records = self.consumer.poll(timeout_ms=1000, max_records=batch_size)
        if not records:
            return
        for record in records[self.topic][self.partition]:
            self._process_record(record.value)
        # Checkpoint after batch
        self._checkpoint()

    def _process_record(self, record):
        # Idempotent processing logic
        order_id = record["order_id"]
        # Update database or external system
        # Example: upsert into PostgreSQL
        pass

    def _checkpoint(self):
        try:
            offset = self.consumer.position(self.topic, self.partition)
            self.redis.set(
                f"{self.subscription_id}:{self.topic}:{self.partition}",
                offset
            )
        except NoBrokersAvailable:
            print("Failed to checkpoint: Kafka unavailable")

# Usage
subscriber = CDCSubscriber("orders-consumer", "orders")
while True:
    subscriber.process_batch()
```

---
### **11. Anti-Patterns**
1. **Avoid** storing state in application memory.
   - *Problem:* State lost on restart or failover.
   - *Fix:* Use a durable state repository.

2. **Avoid** long-running transactions for CDC.
   - *Problem:* Blocks partitions and increases latency.
   - *Fix:* Process records asynchronously or use small batches.

3. **Avoid** ignoring `partition` in state tracking.
   - *Problem:* Conflicts if multiple subscribers process the same partition.
   - *Fix:* Scope state to `(subscription_id, topic, partition)`.

4. **Avoid** tight coupling between CDC source and subscriber.
   - *Problem:* Vendor lock-in (e.g., Kafka-specific offsets).
   - *Fix:* Abstract state via a unified schema (e.g., `offset`, `timestamp`).

