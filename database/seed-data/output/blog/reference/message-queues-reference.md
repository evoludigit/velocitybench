---

# **[Pattern] Message Queues and Event Streaming Reference Guide**

---

## **1. Overview**
Message Queues and Event Streaming is an asynchronous communication pattern that decouples services by buffering messages until consumers are ready to process them. This pattern enables **loosely coupled architectures**, **scalable workloads**, and **reliable event handling** through persistent storage.

Key use cases:
- **Decoupling services** (e.g., order processing → inventory updates).
- **Handling spikes in load** (e.g., batch processing jobs).
- **Event-driven workflows** (e.g., real-time analytics, notifications).
- **Fault tolerance** (e.g., retries, dead-letter queues).

Three core variants exist:
1. **Traditional Message Queues** (RabbitMQ, SQS)
   - Point-to-point or pub/sub communication.
   - Simple FIFO or priority-based delivery.
2. **Event Streaming** (Kafka, Pulsar)
   - High-throughput, ordered, append-only log.
   - Supports replay, partitioning, and consumer groups.
3. **Cloud Queues** (AWS SQS, Google Pub/Sub)
   - Serverless, auto-scaling, minimal operational overhead.

**Trade-offs:**
| Feature          | Queues (RabbitMQ) | Event Streaming (Kafka) | Cloud Queues (SQS/PubSub) |
|------------------|------------------|-------------------------|--------------------------|
| **Throughput**   | Moderate         | High                    | Scales to millions      |
| **Ordering**     | Per queue        | Per partition           | At-least-once            |
| **Replay**       | Limited          | Native (full history)   | Limited (via logs)       |
| **Durability**   | Configurable     | Strong                   | Serverless guarantee     |
| **Ops Complexity**| High            | Moderate                | None                     |

---

## **2. Schema Reference**
### **2.1 Core Components**
| Component      | Description                                                                 | Example Implementations               |
|----------------|-----------------------------------------------------------------------------|----------------------------------------|
| **Producer**   | Service/application that publishes messages.                               | Java/Python client, Kafka Producer.   |
| **Broker**     | Manages message storage, routing, and persistence.                        | RabbitMQ server, Kafka cluster.       |
| **Queue/Topic**| Logical buffer where messages are stored (queues = 1:N; topics = 1:M).   | RabbitMQ queue, Kafka topic.          |
| **Consumer**   | Service/application that processes messages.                               | Webhook, microservice, stream processor. |
| **Exchange**   | (RabbitMQ) Routes messages to queues based on bindings (e.g., direct/fanout). | —                                      |
| **Partition**  | (Kafka) Splits a topic into ordered segments for parallelism.             | Kafka `topic.partition`.              |

### **2.2 Message Structure**
```plaintext
{
  "header": {
    "message_id": "uuid-v4",          // Unique identifier
    "timestamp": "ISO-8601",          // Creation time
    "source": "service-name",         // Producer app
    "destination": "queue/topic"      // Target
  },
  "payload": {
    "type": "event-type",             // e.g., "OrderCreated"
    "data": { "key": "value" }        // Structured content
  },
  "metadata": {
    "priority": "high/medium/low",    // (RabbitMQ only)
    "ttl": "3600"                     // Time-to-live (seconds)
  }
}
```

---

## **3. Implementation Details**
### **3.1 Key Concepts**
#### **A. Message Delivery Semantics**
| Semantic         | Description                                                           | Use Case                          |
|------------------|-------------------------------------------------------------------------|-----------------------------------|
| **At-Least-Once**| Message may be delivered 1+ times (duplicates possible).                | Cloud queues (SQS/PubSub).        |
| **Exactly-Once** | Guaranteed no duplicates (requires idempotency).                        | Kafka (with `transactional` writes). |
| **Fire-and-Forget**| No acknowledgment; message lost if broker fails.                     | High-latency tolerance systems.  |

#### **B. Durability Guarantees**
| Level            | Description                                                                 | Example                          |
|------------------|-----------------------------------------------------------------------------|----------------------------------|
| **No Durability**| Messages lost if broker crashes.                                           | In-memory queues (e.g., RabbitMQ "none"). |
| **Transient**    | Messages persisted until acknowledged.                                      | Kafka `acks=1`.                  |
| **Persistent**   | Messages survive broker restarts (disk-backed).                            | Kafka `acks=all`.                |

#### **C. Partitioning & Parallelism**
- **Queues (RabbitMQ/SQS):** Single-consumer FIFO (no native parallelism).
- **Topics (Kafka):** Partitions enable **parallel consumption** (e.g., 3 partitions → 3 consumers).
- **Cloud Pub/Sub:** Subscription-based parallelism (e.g., 10 subscribers per topic).

---

### **3.2 Common Patterns**
#### **A. Dead-Letter Queue (DLQ)**
- Route failed messages to a separate queue for analysis.
- **Example (RabbitMQ):**
  ```plaintext
  {
    "error": "InvalidPayload",
    "attempts": 3,
    "original_queue": "primary_queue"
  }
  ```
  **Config:**
  ```json
  {
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "failed.messages",
    "message-ttl": 86400000  // 1 day
  }
  ```

#### **B. Event Sourcing**
- Store messages as immutable event logs (e.g., Kafka topics as the single source of truth).
- **Workflow:**
  ```mermaid
  sequenceDiagram
      Producer->>Broker: Publish event
      Broker->>Topic: Append to partition
      Consumer->>Broker: Subscribe/consume
      Consumer->>DB: Rebuild state from events
  ```

#### **C. Competitive Consumption**
- Multiple consumers compete for messages (e.g., load balancing).
- **Kafka Example:**
  ```python
  # Python (confluent-kafka)
  from confluent_kafka import Consumer
  conf = {"bootstrap.servers": "kafka:9092", "group.id": "my-group"}
  consumer = Consumer(conf)
  consumer.subscribe(["my_topic"])
  while True:
      msg = consumer.poll(timeout=1.0)
      if msg.error(): break
      process(msg.value())
  ```

---

## **4. Query Examples**
### **4.1 Kafka (CLI)**
**List topics:**
```bash
kafka-topics --bootstrap-server localhost:9092 --list
```
**Describe topic partitions:**
```bash
kafka-topics --bootstrap-server localhost:9092 --topic orders --describe
```
**Consume messages (streaming):**
```bash
kafka-console-consumer --bootstrap-server localhost:9092 --topic orders --from-beginning
```
**Produce a message:**
```bash
echo '{"event":"OrderCreated","id":"123"}' | kafka-console-producer --broker-list localhost:9092 --topic orders
```

### **4.2 RabbitMQ (Management UI/API)**
**Check queues:**
```bash
curl -u guest:guest http://localhost:15672/api/queues/%2f
```
**Publish (via CLI):**
```bash
rabbitmqadmin publish routing_key="order.queue" payload='{"order_id":42}'
```

### **4.3 AWS SQS (AWS CLI)**
**List queues:**
```bash
aws sqs list-queues --queue-name-prefix "orders."
```
**Send message:**
```bash
aws sqs send-message --queue-url "https://sqs.region.amazonaws.com/1234567890/orders" --message-body '{"status":"pending"}'
```
**Receive messages:**
```bash
aws sqs receive-message --queue-url "https://sqs.region.amazonaws.com/1234567890/orders" --max-number-of-messages 10
```

---

## **5. Related Patterns**
| Pattern                          | Description                                                                 | Integration Example                          |
|----------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **CQRS**                         | Separate read/write models; event streams power the read side.               | Kafka topics → Materialized Views.           |
| **Saga Pattern**                 | Distributed transactions using compensating events.                        | Kafka topics for `OrderCreated`/`PaymentFailed`. |
| **Event Sourcing**               | Full audit trail via immutable events.                                      | Kafka + EventStore DB.                      |
| **Fan-Out**                      | Broadcast messages to multiple consumers (e.g., Pub/Sub).                   | Kafka topic → 3 consumer groups.             |
| **Rate Limiting**                | Control consumer throughput (e.g., Kafka consumer lag monitoring).         | Prometheus + Grafana alerts.                |
| **Circuit Breaker**              | Fail fast if broker is unavailable (e.g., RabbitMQ health checks).        | Resilience4j integration.                    |

---

## **6. Selection Guide**
| Requirement                     | Recommended Solution               |
|----------------------------------|------------------------------------|
| **High-throughput streaming**    | Kafka (or Pulsar).                 |
| **Simple point-to-point**       | RabbitMQ/SQS.                      |
| **Serverless ops**               | AWS SQS/Google PubSub.             |
| **Event replay**                 | Kafka (compaction + retention).   |
| **Low-latency pub/sub**          | RabbitMQ (fanout exchange).        |
| **Idempotent processing**        | Kafka transactions + deduplication.|

---
**Notes:**
- For **new projects**, prioritize Kafka if event streaming is critical; SQS/PubSub for simplicity.
- Benchmark **end-to-end latency** (e.g., producer→consumer) and **cost** (e.g., Kafka brokers vs. SQS quotas).
- Use **dead-letter queues** to debug failures in production.