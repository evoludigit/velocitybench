# **[Pattern] Queuing Integration – Reference Guide**

---

## **Overview**
The **Queuing Integration** pattern decouples processes by buffering requests or messages in a **queue**, enabling asynchronous communication, load balancing, and fault tolerance. This pattern is essential in distributed systems where high throughput, scalability, and resilience are priorities. Queues act as intermediaries, ensuring that producers and consumers operate independently, reducing direct dependencies and mitigating bottlenecks.

Queuing systems support **publish-subscribe, work distribution, and event-driven architectures**, making them ideal for:
- **Microservices communication** (e.g., order processing, notifications).
- **Background task execution** (e.g., report generation, batch processing).
- **Decoupled event processing** (e.g., logging, analytics).

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                 | **Example Implementations**                     |
|------------------------|---------------------------------------------------------------------------------|-------------------------------------------------|
| **Producer**           | Generates messages/items to be enqueued.                                      | REST API, database trigger, IoT sensor.         |
| **Queue**              | Stores messages temporarily until consumed.                                    | **In-Memory:** RabbitMQ, Apache Kafka.          |
| **Consumer**           | Processes messages from the queue.                                            | Microservice, serverless function, cron job.   |
| **Message**            | Structured data (e.g., JSON, XML) containing payload + metadata (e.g., queue ID). | `{"orderId": 123, "status": "placed", "timestamp": "2024-05-20"}` |
| **Queue Broker**       | Manages queues, message persistence, and delivery guarantees.                  | Amazon SQS, Azure Service Bus, ActiveMQ.       |
| **Message Broker**     | A type of queue broker supporting advanced features (e.g., topics, partitions). | Kafka, RabbitMQ (with exchanges).              |

---

### **2. Message Types & Delivery Guarantees**
| **Message Type**       | **Use Case**                          | **Delivery Guarantee**                     | **Example Broker**          |
|------------------------|---------------------------------------|--------------------------------------------|------------------------------|
| **Fire-and-forget**    | Non-critical notifications.            | No acknowledgment; may be lost.             | RabbitMQ (direct exchange).  |
| **At-least-once**      | Retries on failure (idempotent ops).  | Guaranteed delivery; duplicates possible.  | SQS, Kafka.                  |
| **Exactly-once**       | Critical transactions (e.g., payments).| No duplicates; requires transactional outbox. | Kafka + transactional writes. |

---

### **3. Queue Topologies**
| **Topology**           | **Description**                                                                 | **When to Use**                              |
|------------------------|---------------------------------------------------------------------------------|----------------------------------------------|
| **Point-to-Point (P2P)** | One producer → one consumer.                                                     | Simple task distribution (e.g., job queues). |
| **Publish-Subscribe**  | One producer → multiple consumers (topics).                                    | Event-driven architectures (e.g., logs).     |
| **Competing Consumers**| Multiple consumers compete for messages in a single queue.                       | Parallel processing (e.g., image resizing). |
| **Fanout**             | Broker forwards messages to all consumers (no filtering).                       | Broadcast notifications.                    |

---

## **Schema Reference**

### **Message Schema (JSON Example)**
```json
{
  "messageId": "uuid-v4",           // Unique identifier.
  "queueName": "order-processing",  // Target queue.
  "payload": {
    "orderId": "1001",
    "items": [{"productId": "A1", "quantity": 2}],
    "timestamp": "2024-05-20T12:00:00Z"
  },
  "metadata": {
    "priority": "high",             // Optional: "low"/"medium"/"high".
    "ttl": 3600,                    // Time-to-live in seconds (default: 0).
    "deliveryAttempts": 3           // Max retries before dead-letter. (Optional)
  }
}
```

### **Queue Schema**
| **Field**              | **Type**   | **Description**                                                                 | **Example**               |
|------------------------|------------|---------------------------------------------------------------------------------|---------------------------|
| `queueName`            | String     | Unique identifier for the queue.                                                | `order-events`            |
| `brokerType`           | Enum       | Broker implementation (e.g., `sqs`, `kafka`, `rabbitmq`).                       | `kafka`                   |
| `partitionKey`         | String     | Key for partitioning (e.g., `userId` for Kafka).                                | `user_123`                |
| `retainMessages`       | Boolean    | Persist messages after consumption (e.g., for auditing).                         | `true`                    |
| `maxLength`            | Integer    | Max messages before slow consumers are throttled.                                | `10000`                   |

---

## **Query Examples**
### **1. Enqueue a Message (Producer)**
#### **RabbitMQ (AMQP)**
```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='order-processing', durable=True)
channel.basic_publish(
    exchange='',
    routing_key='order-processing',
    body='{"orderId": 123, "status": "created"}',
    properties=pika.BasicProperties(delivery_mode=2)  # Persistent message
)
connection.close()
```

#### **AWS SQS**
```bash
aws sqs send-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/order-queue \
  --message-body '{"event": "order_created", "id": "123"}' \
  --message-group-id "order_123"  # For FIFO queues
```

---

### **2. Consume Messages (Consumer)**
#### **Kafka (Python)**
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'order-events',
    bootstrap_servers=['localhost:9092'],
    group_id='order-processor',
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    print(f"Received: {message.value}")
```

#### **Azure Service Bus**
```csharp
var client = new QueueClient(connectionString, "order-queue");
await client.ProcessMessagesAsync(async (message, cancellationToken) =>
{
    var order = JsonSerializer.Deserialize<Order>(message.Body.ToArray());
    await ProcessOrderAsync(order);
    await client.CompleteAsync(message);  // Acknowledge.
});
```

---

### **3. Dead-Letter Queue (DLQ) Handling**
```sql
-- SQS Dead-Letter Queue Policy (JSON)
{
  "deadLetterTargetArn": "arn:aws:sqs:us-east-1:123456789012:order-dlq",
  "maxReceiveCount": 3
}
```

---

## **Error Handling & Retries**
| **Scenario**               | **Solution**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Consumer fails**         | Use **exponential backoff** retries (e.g., SQS visibility timeout).         |
| **Duplicate processing**   | Implement **idempotency** (e.g., check `messageId` in DB before acting).     |
| **Queue overload**         | Enable **throttling** (e.g., Kafka `consumer.lag` monitoring).              |
| **Broker failure**         | Use **multi-AZ deployments** (e.g., Kafka replication factor > 1).          |

---

## **Performance Considerations**
| **Metric**               | **Optimization Strategy**                                                      |
|--------------------------|--------------------------------------------------------------------------------|
| **Latency**              | Use **in-memory queues** (e.g., RabbitMQ with `ha-mode: all`).                |
| **Throughput**           | Partition queues (Kafka) or use **multi-consumer groups**.                   |
| **Storage Cost**         | Set **TTL** for ephemeral messages (e.g., Kafka `retention.ms`).              |
| **Network Overhead**     | Compress payloads (e.g., gzip) or use **protocol buffers** instead of JSON. |

---

## **Related Patterns**
| **Pattern**               | **Connection to Queuing Integration**                                                                 | **Reference**                     |
|---------------------------|---------------------------------------------------------------------------------------------------------|-----------------------------------|
| **Saga Pattern**          | Uses queues to orchestrate distributed transactions (e.g., compensating actions on failure).          | [Eventual Consistency](link)      |
| **CQRS**                  | Queues decouple read/write models (e.g., event sourcing).                                              | [CQRS Guide](link)                |
| **Circuit Breaker**       | Queues can buffer requests during broker failures (e.g., Kafka retries).                                | [Resilience Patterns](link)       |
| **Event Sourcing**        | Queues persist events for replayable state reconstruction.                                               | [Domain-Driven Design](link)      |
| **Bulkhead**              | Limits queue depth to prevent resource exhaustion (e.g., SQS `QueueDepth`).                              | [Concurrency Control](link)      |

---

## **Troubleshooting**
| **Issue**                 | **Diagnosis**                                                                 | **Solution**                                                                 |
|---------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Messages lost**         | Check **broker logs** or **dead-letter queues**.                                 | Enable **persistence** (`durable=True` in RabbitMQ).                         |
| **Slow consumers**        | Monitor **consumer lag** (Kafka: `kafka-consumer-groups --describe`).          | Scale consumers or **increase partition count**.                              |
| **Throttling**            | Broker returns **429 Too Many Requests**.                                     | Adjust **consumer batch size** or **queue limits**.                          |
| **Idempotency failures**  | Duplicate messages processed.                                                    | Use **transactional outbox** or **message deduplication** (e.g., Kafka `max.in.flight`). |

---

## **Tools & Libraries**
| **Category**              | **Tools**                                                                     |
|---------------------------|-------------------------------------------------------------------------------|
| **Broker**                | RabbitMQ, Kafka, Amazon SQS, Azure Service Bus, Apache ActiveMQ.              |
| **Clients**               | `pika` (RabbitMQ), `confluent-kafka` (Kafka), `boto3` (SQS), `azure-messaging-servicebus`. |
| **Monitoring**            | Prometheus + Grafana, Datadog, New Relic.                                     |
| **Testing**               | **Unit:** Mock queues (e.g., `pytest-mock`).                                  |
|                           | **Integration:** TestContainers (e.g., Kafka in Docker).                     |

---

## **Best Practices**
1. **Design for Failure**: Assume queues will fail; implement **retry policies** and **circuit breakers**.
2. **Monitor End-to-End**: Track **queue depth**, **consumer lag**, and **message metrics** (e.g., Kafka lag).
3. **Optimize Partitions**: Partition queues by **key** (e.g., `userId`) to avoid hotspots.
4. **Secure Queues**: Use **IAM policies** (AWS), **ACLs** (RabbitMQ), or **SAS tokens** (Azure) for access control.
5. **Document Schema**: Maintain backward-compatible **message schemas** (e.g., Avro for Kafka).