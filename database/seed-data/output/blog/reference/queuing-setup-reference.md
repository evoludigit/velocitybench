# **[Pattern] Queuing Setup Reference Guide**

---

## **Overview**
The **Queuing Setup Pattern** provides a structured approach to managing asynchronous tasks, workflows, and event-driven processing using queues. Queues are essential for decoupling producers (requesters) from consumers (processors) to improve scalability, fault tolerance, and throughput. This pattern ensures that messages or jobs are stored and processed in a first-in-first-out (FIFO) order, optimizing system performance and reliability.

This guide covers:
- Core concepts (queues, consumers, producers, brokers)
- Schema reference for common queue configurations
- SQL/NoSQL query examples for queue management
- Integration patterns with related workflows

---

## **Implementation Details**

### **Key Components**
1. **Queue Broker** – Middleware (e.g., RabbitMQ, Apache Kafka, AWS SQS) managing message storage and routing.
2. **Producer** – Application/service that enqueues messages/jobs.
3. **Consumer** – Application/service that dequeues and processes messages.
4. **Queue** – FIFO storage for messages or tasks (can be prioritized or partitioned).
5. **Message** – Data payload (e.g., JSON) sent via the queue.

### **Common Use Cases**
- **Task batching** (e.g., image resizing, report generation).
- **Event-driven workflows** (e.g., order processing, notifications).
- **Load leveling** (e.g., handling spikes in API requests).

---

## **Schema Reference**

### **1. Queue Schema (Generic)**
| Field               | Type          | Description                                                                 | Example Values                     |
|---------------------|---------------|-----------------------------------------------------------------------------|-------------------------------------|
| `queue_id`          | String (UUID) | Unique identifier for the queue.                                            | `550e8400-e29b-41d4-a716-446655440000` |
| `name`              | String        | Human-readable name for the queue.                                           | `image_processing_tasks`           |
| `broker`            | String        | Broker service (e.g., `rabbitmq`, `kafka`).                                 | `rabbitmq`                          |
| `type`              | Enum          | Queue type (e.g., `standard`, `priority`, `partitioned`).                   | `standard`                          |
| `visibility_timeout`| Integer (ms)  | Time (ms) a message stays invisible to consumers after processing starts.   | `30000` (30s)                       |
| `max_length`        | Integer       | Maximum messages allowed before blocking producers.                         | `10000`                             |
| `retry_policy`      | JSON          | Retry settings (e.g., `max_retries: 3`, `delay: 5000`).                     | `{"max_retries": 3, "delay": 5000}` |
| `created_at`        | Timestamp     | Queue creation timestamp.                                                   | `2024-05-01 12:00:00 UTC`           |
| `updated_at`        | Timestamp     | Last modification timestamp.                                               | `2024-05-02 10:30:00 UTC`           |

---

### **2. Message Schema**
| Field          | Type    | Description                                                                 | Example Values                     |
|----------------|---------|-----------------------------------------------------------------------------|-------------------------------------|
| `message_id`   | String  | Unique identifier for the message.                                           | `msg_789abc123`                    |
| `queue_id`     | String  | Reference to the queue this message belongs to.                             | `550e8400-e29b-41d4-a716-446655440000` |
| `payload`      | JSON    | Message content (e.g., task data, event details).                           | `{"task": "resize_image", "url": "img.jpg"}` |
| `priority`     | Integer | Priority level (for prioritized queues).                                    | `2` (higher = higher priority)      |
| `status`       | Enum    | `pending`, `processing`, `completed`, `failed`.                              | `pending`                           |
| `attempts`     | Integer | Number of processing attempts.                                               | `1`                                 |
| `created_at`   | Timestamp| Message enqueue timestamp.                                                  | `2024-05-01 12:05:00 UTC`           |
| `processed_at` | Timestamp| Timestamp when processing started/finished.                                 | `2024-05-01 12:07:00 UTC`           |

---

### **3. Consumer Schema**
| Field               | Type      | Description                                                                 | Example Values                     |
|---------------------|-----------|-----------------------------------------------------------------------------|-------------------------------------|
| `consumer_id`       | String    | Unique identifier for the consumer.                                         | `consumer_123`                     |
| `queue_id`          | String    | Queue this consumer processes.                                              | `550e8400-e29b-41d4-a716-446655440000` |
| `worker_pool_size`  | Integer   | Number of concurrent workers.                                               | `4`                                 |
| `max_batch_size`    | Integer   | Max messages processed per batch.                                           | `10`                                |
| `last_heartbeat`    | Timestamp | Last heartbeat timestamp (for health checks).                               | `2024-05-01 12:10:00 UTC`           |
| `active`            | Boolean   | Whether the consumer is active.                                             | `true`                              |

---

## **Query Examples**

### **1. SQL (Relational Database)**
#### **Create a Queue**
```sql
INSERT INTO queues (queue_id, name, broker, type, visibility_timeout, max_length, retry_policy)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'image_processing_tasks',
    'rabbitmq',
    'standard',
    30000,
    10000,
    '{"max_retries": 3, "delay": 5000}'
);
```

#### **Enqueue a Message**
```sql
INSERT INTO messages (message_id, queue_id, payload, priority, status)
VALUES (
    'msg_789abc123',
    '550e8400-e29b-41d4-a716-446655440000',
    '{"task": "resize_image", "url": "img.jpg"}',
    2,
    'pending'
);
```

#### **Update Message Status (Processing)**
```sql
UPDATE messages
SET status = 'processing', processed_at = NOW()
WHERE message_id = 'msg_789abc123';
```

#### **Query Pending Messages for a Consumer**
```sql
SELECT m.*
FROM messages m
LEFT JOIN consumers c ON m.queue_id = c.queue_id
WHERE m.status = 'pending'
  AND c.consumer_id = 'consumer_123'
  AND c.active = true
LIMIT 10;  -- Batch size
```

---

### **2. NoSQL (MongoDB)**
#### **Create a Queue Document**
```javascript
db.queues.insertOne({
    queue_id: "550e8400-e29b-41d4-a716-446655440000",
    name: "image_processing_tasks",
    broker: "rabbitmq",
    type: "standard",
    visibility_timeout: 30000,
    max_length: 10000,
    retry_policy: { max_retries: 3, delay: 5000 },
    created_at: ISODate("2024-05-01T12:00:00Z")
});
```

#### **Enqueue a Message**
```javascript
db.messages.insertOne({
    message_id: "msg_789abc123",
    queue_id: "550e8400-e29b-41d4-a716-446655440000",
    payload: { task: "resize_image", url: "img.jpg" },
    priority: 2,
    status: "pending",
    created_at: ISODate("2024-05-01T12:05:00Z")
});
```

#### **Update Message Status (Failed)**
```javascript
db.messages.updateOne(
    { message_id: "msg_789abc123" },
    { $set: { status: "failed", attempts: 2 } }
);
```

#### **Find Pending Messages for a Consumer (Aggregation)**
```javascript
db.messages.aggregate([
    { $match: {
        status: "pending",
        queue_id: "550e8400-e29b-41d4-a716-446655440000"
    }},
    { $lookup: {
        from: "consumers",
        localField: "queue_id",
        foreignField: "queue_id",
        as: "consumer"
    }},
    { $match: { "consumer.active": true, "consumer.consumer_id": "consumer_123" }},
    { $limit: 10 }
]);
```

---

### **3. Broker-Specific Commands**
#### **RabbitMQ (CLI)**
```bash
# Create a queue
rabbitmqadmin declare queue name="image_processing_tasks" durable=true

# Publish a message
rabbitmqadmin publish routing_key="" payload='{"task":"resize_image"}' queue="image_processing_tasks"

# Consume messages
rabbitmqctl consume image_processing_tasks consumer_123
```

#### **AWS SQS (API)**
```bash
# Create a queue
aws sqs create-queue --queue-name image_processing_tasks

# Send a message
aws sqs send-message --queue-url "https://sqs.us-east-1.amazonaws.com/1234567890/image_processing_tasks" --message-body '{"task":"resize_image"}'

# Receive messages
aws sqs receive-message --queue-url "https://sqs.us-east-1.amazonaws.com/1234567890/image_processing_tasks" --max-number-of-messages 10
```

---

## **Related Patterns**

| Pattern                     | Description                                                                 | Integration Points                          |
|-----------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **Event Sourcing**          | Store state changes as a sequence of events.                                | Queues can persist event payloads.          |
| **Command Query Responsibility Segregation (CQRS)** | Separate read/write operations.        | Queues decouple write commands from queries.  |
| **Saga Pattern**           | Manage distributed transactions via compensating actions.                  | Queues track saga steps (e.g., `order_processed`). |
| **Circuit Breaker**         | Prevent cascading failures by throttling retries.                          | Queue retry policies integrate with breakers. |
| **Bulkhead Pattern**       | Isolate workloads to prevent resource exhaustion.                          | Queues limit concurrent tasks per bulkhead.  |
| **Retry with Backoff**     | Exponential backoff for failed messages.                                    | Queue `retry_policy` configures this.        |

---

## **Best Practices**
1. **Monitoring**: Track queue lengths, processing times, and failures (e.g., via Prometheus).
2. **Scaling**: Use horizontal scaling for consumers (e.g., Kubernetes pods for SQS workers).
3. **Idempotency**: Design messages to be reprocessable safely (e.g., use `message_id` for deduplication).
4. **TTL**: Set message time-to-live (TTL) to avoid stale tasks (e.g., Kafka message expiration).
5. **Dead Letter Queues (DLQ)**: Route failed messages to a separate queue for analysis.

---
**See Also**:
- [Broker-Specific Guides](link_to_rabbitmq_kafka_sqs_docs)
- [Error Handling Deep Dive](link_to_error_handling_patterns)