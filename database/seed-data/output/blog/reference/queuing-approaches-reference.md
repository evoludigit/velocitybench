# **[Pattern] Queuing Approaches – Reference Guide**

---

## **1. Overview**
The **Queuing Approaches** pattern organizes tasks, events, or requests into queues to manage workloads efficiently, decouple components, and improve system scalability. Queues act as intermediaries between producers (who enqueue items) and consumers (who dequeue and process them), ensuring smooth resource allocation and failure resilience. This pattern is widely used in microservices, distributed systems, and event-driven architectures to:
- Decouple request handling from processing.
- Handle variable workloads (e.g., burst traffic).
- Process tasks asynchronously (e.g., background jobs).
- Implement retry logic for failed operations.

Queuing approaches differ in **persistence**, **ordering guarantees**, **concurrency**, and **error handling**, making them suitable for specific scenarios (e.g., real-time vs. batch processing).

---

## **2. Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 | **Use Case Examples**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Queue**              | A FIFO (First-In-First-Out) data structure where items are added (enqueued) and removed (dequeued) in order.                                                                                             | Requests in a web server, background job processing.                                                     |
| **Producer**           | The component that enqueues items (e.g., an API, a sensor, or a user action).                                                                                                                                  | Mobile app submitting orders, IoT device sending telemetry data.                                       |
| **Consumer**           | The component that dequeues and processes items. Consumers may be synchronous (immediate) or asynchronous (background).                                                                                 | Payment service processing transactions, email digest generation.                                       |
| **Message**            | A unit of data (payload) in a queue, often including metadata (e.g., priority, timestamps, or correlation IDs).                                                                                             | A JSON payload containing a user order with metadata like `priority: "high"`.                           |
| **Persistent Queue**    | A queue that stores messages durably (e.g., on disk) to survive restarts or failures.                                                                                                                      | High-availability systems where messages must not be lost.                                              |
| **In-Memory Queue**     | A queue stored in RAM (non-persistent) for low-latency, ephemeral workloads.                                                                                                                              | Temporary task queues in local services (e.g., caching layers).                                        |
| **Durable Queue**       | A subset of persistent queues where messages remain until explicitly deleted (e.g., Kafka topics).                                                                                                       | Event sourcing or audit logging where historical data is critical.                                      |
| **Priority Queue**      | A queue that processes messages based on predefined priorities (e.g., "critical" vs. "low").                                                                                                                 | Urgent notifications in a chat app vs. scheduled maintenance tasks.                                     |
| **Work Distribution**  | Splitting tasks across multiple consumers (e.g., load balancing) to parallelize processing.                                                                                                               | Distributed task queues (e.g., Celery, RabbitMQ with multiple workers).                                 |
| **Retention Policy**    | Rules governing how long messages are kept in the queue (e.g., TTL: Time-To-Live).                                                                                                                       | Temporary queues for processing time-sensitive data (e.g., session tokens).                            |
| **Dead-Letter Queue (DLQ)** | A queue for messages that failed processing after retries, often with diagnostic information.                                                                                                           | Failed payment transactions requiring manual review.                                                    |
| **At-Least-Once Delivery** | A guarantee that a message is delivered *at least once* (may duplicate if retries occur).                                                                                                               | Idempotent operations (e.g., updating a user profile).                                                  |
| **Exactly-Once Delivery** | A guarantee that a message is delivered *exactly once* (requires deduplication logic).                                                                                                                 | Financial transactions where duplicates are catastrophic.                                             |
| **Broadcast Queue**    | A queue where messages are sent to all consumers (e.g., pub-sub model).                                                                                                                                  | Real-time notifications (e.g., Slack alerting all admins).                                             |
| **Point-to-Point Queue** | A queue where messages are sent to a single consumer (default in most systems).                                                                                                                            | Request-response patterns (e.g., RPC calls).                                                            |

---

## **3. Schema Reference**
Below are common queue system schemas. Adjust based on your technology (e.g., RabbitMQ, Kafka, AWS SQS).

### **Basic Queue Schema**
| **Field**            | **Type**       | **Description**                                                                                                       | **Example**                          |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `message_id`         | `string` (UUID) | Unique identifier for the message (for deduplication).                                                               | `"550e8400-e29b-41d4-a716-446655440000"` |
| `payload`            | `JSON`         | The actual data being queued (e.g., user order).                                                                    | `{"user_id": "123", "product": "X"}` |
| `enqueue_time`       | `timestamp`    | When the message was added to the queue.                                                                             | `"2024-05-20T14:30:00Z"`             |
| `priority`           | `integer`      | Numeric priority (higher = processed first).                                                                          | `2` (critical) or `0` (default)      |
| `ttl`                | `duration`     | Time-to-live (messages auto-deleted after this).                                                                    | `"PT1H"` (1 hour)                    |
| `retry_count`        | `integer`      | Number of failed attempts (for DLQ logic).                                                                           | `0` (first attempt)                  |
| `correlation_id`     | `string`       | Links related messages (e.g., for tracking a multi-step workflow).                                                   | `"order_123"`                        |
| `source`             | `string`       | Producer identifier (e.g., service name).                                                                        | `"user-service"`                     |
| `status`             | `enum`         | Current state (e.g., `pending`, `processing`, `completed`, `failed`).                                               | `"processing"`                       |

---

### **Extended Schema for Distributed Systems**
Add these fields for advanced use cases:
| **Field**            | **Type**       | **Description**                                                                                                       | **Example**                          |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `consumer_group`     | `string`       | Consumer group ID for work distribution (e.g., `celery-worker-1`).                                                   | `"payment-service"`                  |
| `partition_key`      | `string`       | Key for partitioning (e.g., Kafka topics).                                                                           | `"user_id:456"`                      |
| `acknowledgment_id`  | `string`       | ID for confirming message processing (e.g., `consumer-generated`).                                                   | `"ack_789"`                          |
| `error_metadata`     | `JSON`         | Details of processing errors (for DLQ).                                                                              | `{"error": "DatabaseTimeout", "stack": "..."}` |

---

## **4. Query Examples**
Queuing patterns rarely involve "queries" in the traditional SQL sense, but consumers interact with queues via **dequeue/polling** or **event subscriptions**. Below are examples for common operations:

---

### **4.1 Enqueueing a Message**
#### **RabbitMQ (AMQP)**
```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='tasks', durable=True)  # Persistent queue
channel.basic_publish(
    exchange='',
    routing_key='tasks',
    body='{"user_id": "123", "priority": 2}',
    properties=pika.BasicProperties(delivery_mode=2)  # Persistent
)
connection.close()
```

#### **AWS SQS**
```bash
aws sqs send-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/123456789012/tasks" \
  --message-body '{"user_id": "123", "priority": 2}' \
  --message-deduplication-id "order_123" \
  --message-group-id "user_123"  # For FIFO queues
```

---

### **4.2 Dequeueing Messages (Polling)**
#### **RabbitMQ (Consumer)**
```python
def callback(ch, method, properties, body):
    print(f" [x] Received {body}")
    ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge

channel.basic_consume(queue='tasks', on_message_callback=callback, auto_ack=False)
channel.start_consuming()
```

#### **Kafka (Consumer Group)**
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'orders',
    bootstrap_servers=['localhost:9092'],
    group_id='payment-service',
    auto_offset_reset='earliest'
)

for message in consumer:
    print(f"Key: {message.key}, Value: {message.value}")
```

#### **AWS SQS (Long Polling)**
```bash
aws sqs receive-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/123456789012/tasks" \
  --max-number-of-messages 10 \
  --wait-time-seconds 20  # Long polling to reduce costs
```

---

### **4.3 Querying Queue Metadata**
#### **RabbitMQ (Check Queue Length)**
```bash
rabbitmqctl list_queues name messages_ready messages_unacknowledged
```
Output:
```
Listing queues ...
tasks    45       0
```

#### **AWS SQS (Describe Queue)**
```bash
aws sqs get-queue-attributes \
  --queue-url "https://sqs.us-east-1.amazonaws.com/123456789012/tasks" \
  --attribute-names ApproximateNumberOfMessages
```

---

### **4.4 Handling Failures (Dead-Letter Queue)**
#### **RabbitMQ (DLQ Setup)**
```python
channel.queue_declare(queue='dlq', durable=True)
channel.exchange_declare(exchange='failed_exchange', durable=True, type='direct')
channel.queue_bind(queue='dlq', exchange='failed_exchange', routing_key='failed')

# Redirect failed messages
prefetch_count = 1
channel.basic_qos(prefetch_count=prefetch_count)

def on_failure(ch, method, properties, body):
    ch.basic_publish(
        exchange='failed_exchange',
        routing_key='failed',
        body=body,
        properties=pika.BasicProperties(
            message_id=properties.message_id,
            headers={"original_queue": "tasks"}
        )
    )
```

---

## **5. Implementation Decisions**
Choose a queuing approach based on these trade-offs:

| **Decision Point**          | **Options**                                                                 | **Trade-offs**                                                                                     | **Recommended When**                          |
|-----------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Persistence**             | In-memory vs. Persistent                                                   | In-memory: Fast but lost on restart; Persistent: Slower but reliable.                          | Use persistent for critical workloads.       |
| **Ordering Guarantees**      | FIFO vs. No Guarantee                                                     | FIFO: Ordered but may require partitioning; No Guarantee: Higher throughput.                    | FIFO for sequential tasks (e.g., orders).     |
| **Delivery Semantics**       | At-least-once vs. Exactly-once                                             | At-least-once: Simpler but may duplicate; Exactly-once: Complex but no duplicates.              | Exactly-once for financial transactions.      |
| **Scalability**             | Single-node vs. Distributed                                                 | Single-node: Simpler; Distributed: Higher throughput but complex setup.                          | Distributed for high-scale systems.          |
| **Priority Handling**       | Simple priority vs. Weighted fair queueing                                  | Simple: Faster but skewed; Weighted: Fairer distribution.                                        | Weighted for mixed-priority loads.            |
| **Error Handling**          | Retry + DLQ vs. Immediate Failure                                           | Retry + DLQ: Resilient but may waste resources; Immediate: Faster but less graceful.            | DLQ for recoverable failures.                 |
| **Monitoring**              | Basic metrics vs. Advanced telemetry                                        | Basic: Lightweight; Advanced: More overhead but better insights.                                 | Advanced for SLA-sensitive systems.           |

---

## **6. Query Examples for Monitoring**
Use these SQL-like patterns (via tools like **Prometheus**, **Datadog**, or **CloudWatch**) to monitor queues:

| **Query**                          | **Purpose**                                                                 | **Example Tools**                     |
|------------------------------------|-----------------------------------------------------------------------------|----------------------------------------|
| `SELECT COUNT(*) FROM queue_messages WHERE status = 'pending' AND ttl < 1h` | Find stale messages.                                                          | PromQL: `rate(queue_messages_pending{ttl="<1h"}[1m])` |
| `SELECT SUM(bytes_processed) FROM consumer_metrics WHERE group = 'payment-service'` | Track consumer throughput.                                                    | CloudWatch Metric: `Sum: SQS.Metrics.ConsumedMessageCount` |
| `SELECT DISTINCT error_code FROM dlq_messages LIMIT 10` | Identify common failure types.                                               | AWS SQS DLQ analytics.                 |
| `SELECT AVG(processing_time) FROM tasks WHERE priority = 'high'` | Measure latency for critical tasks.                                          | Custom application metrics.            |

---

## **7. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Combine**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Saga**                  | Manage distributed transactions by breaking them into local transactions linked via queues.                                                                                                           | Use queues to coordinate Saga steps (e.g., `order_placed` → `inventory_reserved` → `payment_processed`). |
| **CQRS**                  | Separate read and write models using event sourcing; queues provide event delivery.                                                                                                                 | Combine with event-driven queues for real-time updates (e.g., Kafka topics).                           |
| **Circuit Breaker**       | Protect consumers from cascading failures by queueing requests during outages.                                                                                                                       | Queue requests to a "waitlist" during service degradation.                                             |
| **Bulkhead**              | Isolate consumers to prevent resource exhaustion; queues can limit concurrency per consumer.                                                                                                          | Use queues to throttle consumers (e.g., `rate: 100 msg/sec`).                                           |
| **Rate Limiting**         | Control producer/consumer throughput; queues can buffer excess requests.                                                                                                                               | Implement with a queue that discards or delays messages beyond the limit.                             |
| **Event Sourcing**        | Store state changes as an append-only event log; queues distribute events to consumers.                                                                                                             | Use queues to fan-out events to subscribers (e.g., Kafka + event sinks).                            |
| **Retry with Backoff**    | Exponentially increase retry delays for failed messages in the queue.                                                                                                                               | Combine with DLQ for failed retries after max attempts.                                               |

---

## **8. Anti-Patterns & Pitfalls**
- **Fire-and-Forget Without Monitoring**:
  *Problem*: Queues can hide latency or failures.
  *Solution*: Track metrics (e.g., `processing_time`, `error_rate`) and set up alerts.

- **Unbounded Queue Growth**:
  *Problem*: Unlimited retention can flood storage.
  *Solution*: Enforce TTL policies and archive old messages.

- **No Consumer Scaling**:
  *Problem*: Bottlenecks at consumers under load.
  *Solution*: Use work distribution (e.g., Kafka partitions, RabbitMQ prefetch).

- **Ignoring Exactly-Once Deliveries**:
  *Problem*: Duplicate processing in at-least-once systems.
  *Solution*: Design idempotent consumers or use exactly-once semantics (e.g., Kafka transactions).

- **Overusing Priorities Without Limits**:
  *Problem*: High-priority messages starve low-priority ones.
  *Solution*: Cap priority queues or use weighted fair scheduling.

- **Tight Coupling to Queue Implementation**:
  *Problem*: Vendor lock-in (e.g., AWS SQS-specific code).
  *Solution*: Abstract queues with interfaces (e.g., `IQueueProducer`).

---

## **9. Technology References**
| **Technology**       | **Type**               | **Key Features**                                                                                          | **Best For**                          |
|----------------------|------------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------|
| **RabbitMQ**         | Message Broker         | AMQP, pluggable protocols, durable queues, DLQ, clustering.                                            | Enterprise apps, complex routing.     |
| **Apache Kafka**     | Distributed Event Bus  | High-throughput, persistence, partitioning, exactly-once semantics.                                   | Streaming, event sourcing.            |
| **AWS SQS/SNS**      | Managed Queues         | Serverless, auto-scaling, FIFO queues, integration with Lambda.                                        | Serverless architectures.             |
| **Celery**           | Task Queue             | Distributed task queues with Redis/RabbitMQ backend, retries, beat scheduler.                          | Python background jobs.                |
| **NATS**             | Lightweight Broker     | Ultra-low latency, pub-sub, request/reply.                                                             | Real-time systems.                    |
| **Redis Streams**    | In-Memory Queue        | Persistent, append-only, consumer groups, LIFO/FIFO ordering.                                           | Low-latency, ephemeral workloads.     |
| **Azure Service Bus**| Managed Queue          | Hybrid queues/topics, session support, auto-scalable.                                                   | Microsoft ecosystem.                  |

---

## **10. Example Workflow: Order Processing**
```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant OrderQueue
    participant PaymentService
    participant InventoryService

    User->>WebApp: Submit Order
    WebApp->>OrderQueue: Enqueue {order_id: "123", user_id: "456", status: "pending"}
    OrderQueue-->>PaymentService: Dequeue (Consumer Group: "payments")
    PaymentService->>OrderQueue: Acknowledge
    PaymentService->>InventoryService: Check Stock (via HTTP/RPC)
    InventoryService-->>PaymentService: Stock Available
    PaymentService->>OrderQueue: Enqueue {order_id: "123", status: "paid"}
   