**[Pattern] Queuing Guidelines Reference Guide**

---

### **Overview**
The **Queuing Guidelines** pattern ensures predictable, controlled, and efficient processing of workloads by decoupling producers and consumers using a queue system. This pattern is ideal for high-volume requests, background jobs, or scenarios requiring graceful handling of spikes in demand. It mitigates risks like system overload, data loss, and inconsistent processing by buffering operations until resources are available.

Queues enforce **order independence**, allowing producers to continue operation while consumers process items at their own pace. Implementations often incorporate routing, priority handling, and fault tolerance mechanisms.

---

---

### **Key Concepts & Schema Reference**
| Concept          | Description                                                                                                                                                                                                                                                                 | Example Properties/Fields                                                                                                   |
|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| **Producer**     | A service or component that enqueues tasks/work items.                                                                                                                                                                                                          | `producerId`, `messageType`, `priority`, `ttl` (time-to-live)                                                                |
| **Consumer**     | A service or component that dequeues and processes tasks. May be single or distributed (e.g., via a worker pool).                                                                                                                                    | `consumerGroup`, `acknowledgementStrategy`, `batchSize`, `retryPolicy`                                                       |
| **Queue**        | A buffered data structure (FIFO/LIFO) that holds enqueued work items. Queues can be synchronous (blocking) or asynchronous (non-blocking).                                                                                                               | `queueName`, `maxLength`, `visibilityTimeout`, `deadLetterQueue`                                                               |
| **Message**      | A unit of work placed in the queue, containing data and metadata (e.g., payload, routing keys).                                                                                                                                                           | `messageId`, `payload`, `timestamp`, `correlationId`, `headers` (e.g., `source=API`, `priority=high`)                        |
| **Routing Keys** | Tags or labels used for targeted distribution (e.g., distributing messages to specific queues or consumers).                                                                                                                                                   | `routingKey` (e.g., `order-payment`, `notification-sms`)                                                                      |
| **Dead Letter Queue (DLQ)** | A queue for failed/undeliverable messages to enable recovery or logging.                                                                                                                                                                               | `dlqName`, `maxRetries`, `errorThreshold` (e.g., `maxRetries=3`, `errorThreshold=500ms`)                                        |
| **Priority Queue** | Queues where messages are processed based on precedence levels (e.g., critical vs. low-priority tasks).                                                                                                                                                            | `priorityLevel` (e.g., `1-5`), `priorityQueueName`                                                                           |
| **Consumer Groups**  | A logical grouping of consumers sharing a queue for parallel processing (e.g., scaling out consumers).                                                                                                                                                     | `groupName`, `memberCount`, `consumerId`                                                                                      |
| **Acknowledgement** | Confirmation from the consumer to the queue that a message has been processed successfully. Implementations may support manual or automatic acknowledgements.                                                                                                                    | `acknowledgementType` (e.g., `explicit`, `implicit`), `timeout` (e.g., `10s`)                                                      |
| **Retries**      | Automatic or manual retry logic for failed processing, with configurable delay/exponential backoff.                                                                                                                                                                  | `retryCount`, `backoffStrategy` (e.g., `linear:1s`, `exponential:100ms`), `maxDelay`                                         |
| **Monitoring Metrics** | Telemetry for queuing health (e.g., queue length, processing latency, error rates).                                                                                                                                                                         | `queueLength`, `processingTime`, `errorRate`, `consumerLag`                                                                    |
| **Load Balancing** | Distributing messages evenly among consumers to prevent bottlenecks.                                                                                                                                                                                           | `roundRobin`, `fairDispatch`, `customWeighting`                                                                               |
| **Visibility Timeout** | Duration a message remains "invisible" to consumers after being dequeued (to prevent reprocessing).                                                                                                                                                       | `visibilityTimeout` (e.g., `30s`)                                                                                             |
| **Client-Library Support** | SDKs or APIs for producers/consumers (e.g., RabbitMQ, Kafka, AWS SQS).                                                                                                                                                                                              | `libraryVersion`, `supportedFeatures` (e.g., `batchPublishing`, `exactlyOnceDelivery`)                                        |

---

---

### **Implementation Details**

#### **1. Queuing Systems & Choices**
Select a queue implementation based on use case:
| System       | Best For                                                                                     | Pros                                                                                                                                                     | Cons                                                                                                                                         |
|--------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| **RabbitMQ** | General-purpose messaging, pub/sub, routing.                                                | Highly reliable, supports complex topologies, rich features (e.g., dead letter exchanges).                                               | Steeper learning curve; requires manual admin (e.g., clustering).                                                              |
| **Kafka**    | High-throughput event streaming, log aggregation.                                            | Scalable, durable, supports partitioned topics; ideal for real-time analytics.                                                          | Not ideal for one-off tasks; higher latency than lightweight queues.                                                         |
| **Amazon SQS** | Serverless, scalable background processing (e.g., AWS Lambda).                              | Fully managed, pay-as-you-go, supports FIFO and standard queues.                                                              | Vendor lock-in; limited custom routing compared to RabbitMQ.                                                                  |
| **Azure Service Bus** | Enterprise-grade messaging with enterprise-grade security.                                  | High security, supports hybrid scenarios (on-prem + cloud).                                                                    | Expensive at scale; complex configuration.                                                                               |
| **Apache Kafka** (for low-latency) | Real-time pipelines (e.g., IoT, financial transactions).                                   | Low-latency, high-throughput, exactly-once processing.                                                                      | Overkill for simple task queues; requires operational expertise.                                                           |
| **Redis Streams** | Lightweight, in-memory pub/sub with persistence.                                           | Simple setup, supports backpressure, low latency.                                                                               | Limited to single-node; no built-in consumer groups.                                                                           |

---

#### **2. Producer Guidelines**
**Do:**
- **Batch messages** when possible to reduce network overhead (e.g., SQS batch publish).
- **Include metadata** (e.g., `correlationId`, `priority`) for traceability.
- **Set TTL** for temporary messages to auto-expire them (e.g., RabbitMQ `expiration`).
- **Use routing keys** to target specific queues (e.g., `order-payment`).

**Don’t:**
- Enqueue oversized payloads (>1MB); use external storage (e.g., S3) and reference URLs.
- Ignore errors during enqueue (e.g., queue full). Implement retry logic or circuit breakers.
- Assume FIFO ordering unless explicitly supported (e.g., SQS FIFO queues).

**Example Workflow:**
```python
# Pseudocode: Publish to RabbitMQ
producer = RabbitMQProducer("amazon_sqs")
message = {
    "payload": {"orderId": "123", "status": "pending"},
    "metadata": {
        "routingKey": "order-status",
        "priority": "high",
        "ttl": 86400  # 1 day
    }
}
producer.publish("orders_queue", message, priority="high")
```

---

#### **3. Consumer Guidelines**
**Do:**
- **Acknowledge messages explicitly** (e.g., `ack`/`nack` in RabbitMQ) to avoid reprocessing.
- **Process in batches** (e.g., SQS `ReceiveMessage` with `MaxNumberOfMessages=10`) for efficiency.
- **Implement retries with backoff** (e.g., exponential delay for transient errors).
- **Monitor lag** (difference between enqueued and processed messages).

**Don’t:**
- Process messages without validation (e.g., check `messageId` duplicates).
- Ignore dead-letter queue (DLQ) errors; log them for debugging.
- Overload consumers with high-volume queues without scaling.

**Example (RabbitMQ Consumer):**
```python
# Pseudocode: RabbitMQ Consumer with DLQ
def consume(queue_name):
    while True:
        message = queue.dequeue(queue_name)
        try:
            process_message(message)
            message.ack()  # Success
        except Exception as e:
            if message.redeliverable:
                message.nack(requeue=False)  # Move to DLQ
            else:
                log_error(e)
```

---

#### **4. Fault Tolerance & Recovery**
| Strategy                | Description                                                                                                                                                                                                                     | Example Tools/Features                                                                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Retry with Backoff**  | Automatically retry failed messages with increasing delays.                                                                                                                                                             | SQS `VisibilityTimeout`, RabbitMQ `retryExponentialMultiplier`                                                                                           |
| **Dead Letter Queue**   | Capture failed messages for analysis/reprocessing.                                                                                                                                                                 | RabbitMQ `dead_letter_exchange`, Kafka `max.poll.interval.ms`                                                                                           |
| **Exponential Backoff** | Delay retries exponentially (e.g., 1s, 2s, 4s) to avoid thundering herds.                                                                                                                                             | `retryCount=3`, `backoffFactor=2`                                                                                                                       |
| **Circuit Breaker**     | Stop enqueuing to a failing queue/consumer temporarily.                                                                                                                                                          | Hystrix, Redis Circuit Breaker                                                                                                                       |
| **Sticky Sessions**     | Route messages to the same consumer for stateful processing (e.g., long-running tasks).                                                                                                                              | Kafka `session.timeout.ms`                                                                                                                         |
| **Monitoring Alerts**   | Trigger alerts for high queue lag, errors, or consumer failures.                                                                                                                                                     | Prometheus + Grafana, AWS CloudWatch                                                                                                                 |

---

#### **5. Query Examples**
##### **A. Check Queue Length**
```bash
# RabbitMQ: List queues with length
rabbitmqctl list_queues name messages_ready messages_unacknowledged

# SQS: Get queue approximate size
aws sqs get-queue-attributes --queue-url https://queue-url --attribute-names ApproximateNumberOfMessages
```

##### **B. Publish a Message**
```bash
# RabbitMQ CLI (rabbitmqadmin)
rabbitmqadmin publish routing_key="orders" payload='{"orderId": "456"}' exchange="orders_exchange"
```

##### **C. Consumer Polling (Kafka)**
```bash
# Kafka Consumer CLI (console-consumer.sh)
./kafka-console-consumer.sh --bootstrap-server localhost:9092 \
    --topic orders \
    --from-beginning \
    --group my_consumer_group
```

##### **D. Query DLQ (RabbitMQ)**
```bash
# List dead-letter messages
rabbitmqadmin list messages dead_letter_exchange dead_letter_queue --vhost /
```

##### **E. Set Consumer Group (Kafka)**
```python
# Kafka Consumer Group
consumer = KafkaConsumer('orders', group_id='order-processors', auto_offset_reset='earliest')
```

---

---

### **Related Patterns**
| Pattern                          | Description                                                                                                                                                                                                                                                                 | When to Use                                                                                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Saga**                         | Manage distributed transactions via a series of local transactions and compensating actions.                                                                                                                                                     | Microservices with eventual consistency (e.g., order processing with payments and inventory).                                                       |
| **Circuit Breaker**              | Prevent cascading failures by stopping requests to a failing service after a threshold of errors.                                                                                                                                                 | Highly available systems where dependent services may fail intermittently.                                                                                |
| **Bulkhead**                     | Isolate workloads to prevent a single component’s failure from affecting others (e.g., thread pools).                                                                                                                                                | CPU/memory-constrained systems with concurrent tasks (e.g., batch processing).                                                                           |
| **Rate Limiting**                | Control request volume to a queue or service to avoid overload.                                                                                                                                                                             | Public APIs or systems with unpredictable traffic spikes.                                                                                                    |
| **Retry with Exponential Backoff** | Delay retries between failures to reduce load on the system.                                                                                                                                                                                 | Idempotent operations (e.g., API calls, database writes).                                                                                                   |
| **Event Sourcing**               | Store state changes as a sequence of events for replayability.                                                                                                                                                                             | Systems requiring full audit trails (e.g., financial ledgers, audit logs).                                                                                  |
| **Worker Pool**                  | Distribute work across a pool of consumers for parallel processing.                                                                                                                                                                         | High-throughput tasks (e.g., image processing, analytics).                                                                                                |
| **Request-Reply**                | Synchronously send a request and wait for a reply (e.g., via a queue).                                                                                                                                                                       | Real-time interactions (e.g., RPC, chatbots).                                                                                                           |
| **Priority Queue**               | Process high-priority messages before low-priority ones.                                                                                                                                                                                   | Time-sensitive tasks (e.g., alerts, critical updates).                                                                                                      |

---

---
### **Best Practices Checklist**
1. [ ] **Design for failure**: Assume queues/consumers may fail; implement DLQs and retries.
2. [ ] **Monitor queue metrics**: Track `queueLength`, `processingTime`, and `errorRate`.
3. [ ] **Batch messages** where possible to reduce network calls.
4. [ ] **Set TTLs** for temporary messages to avoid memory leaks.
5. [ ] **Use consumer groups** to scale horizontally.
6. [ ] **Validate messages** before processing to avoid malformed data.
7. [ ] **Log DLQ messages** for debugging.
8. [ ] **Test edge cases**: Empty queues, consumer crashes, and high-volume spikes.
9. [ ] **Secure queues**: Use TLS, IAM policies, or ACLs (e.g., RabbitMQ `configured_permissions`).
10. [ ] **Document schemas**: Define message formats (e.g., JSON, Avro) for producers/consumers.