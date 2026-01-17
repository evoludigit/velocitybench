# **[Event-Driven Messaging Patterns] Reference Guide**
*Async Communication with RabbitMQ & Kafka*

---

## **Overview**
This pattern enables **decoupled, scalable, and resilient** asynchronous communication between applications using message brokers like **RabbitMQ** and **Apache Kafka**. By decoupling producers and consumers, systems improve **latency tolerance**, **scalability**, and **fault isolation**.

Key use cases:
✔ **Event sourcing** – Persist app state changes as a log of events.
✔ **Stream processing** – Real-time analytics (e.g., fraud detection, logs aggregation).
✔ **Microservices orchestration** – Asynchronous workflows without direct dependencies.
✔ **Batch processing** – Offload heavy tasks (e.g., report generation).

This guide covers **core concepts**, **message broker schemas**, **best practices**, and **anti-patterns**.

---

## **1. Key Concepts**

### **1.1 Producer & Consumer**
- **Producer**: Generates messages (e.g., an API, microservice, or IoT device).
- **Consumer**: Processes messages (e.g., a backend service or analytics tool).

### **1.2 Message Broker Roles**
| Broker  | Best For                          | Key Features                                                                 |
|---------|-----------------------------------|------------------------------------------------------------------------------|
| **RabbitMQ** | Lightweight, AMQP-compliant      | Reliability (acknowledgments), QoS, pub/sub, direct/queue routing.          |
| **Kafka**   | High-throughput event streaming | Scalable partitions, durability (log retention), consumer groups, exactly-once processing. |

### **1.3 Core Patterns**
| Pattern               | Description                                                                 | Use Case Example                          |
|-----------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **Pub/Sub**           | Producers broadcast; consumers subscribe.                                     | Notifications (e.g., Slack alerts).       |
| **Point-to-Point**    | One producer → one consumer (queues).                                        | Task queues (e.g., file processing).       |
| **Event Sourcing**    | Append-only event log for state reconstruction.                               | E-commerce order tracking.                |
| **Stream Processing** | Real-time data transformation (e.g., aggregations).                         | Clickstream analytics.                    |
| **CQRS**              | Separate read/write models via messages.                                     | High-traffic dashboards.                  |
| **Dead Letter Queue** | Route failed messages for reprocessing.                                      | Retries failed payments.                  |

---

## **2. Schema Reference**

### **2.1 RabbitMQ Message Schema**
| Field          | Type     | Description                                                                 | Example Value                     |
|----------------|----------|-----------------------------------------------------------------------------|-----------------------------------|
| `message_id`   | String   | Unique identifier (e.g., UUID).                                             | `a1b2c3d4-e5f6-7890`              |
| `timestamp`    | ISO 8601 | When the message was produced.                                              | `2024-05-20T12:00:00Z`            |
| `topic`        | String   | Message category (e.g., `orders.created`, `payments.failed`).              | `inventory.stock_updated`         |
| `payload`      | JSON     | Structured data (e.g., `{ "user_id": 123, "product": "laptop" }`).       | `{"status": "shipped", "track_id": "X123"}` |
| `headers`      | Key-Value| Metadata (e.g., `priority: high`, `source: webapp`).                     | `{"app": "checkout-service", "version": "1.0"}` |

**Example RabbitMQ Exchange Binding:**
```json
{
  "exchange": "orders",
  "routing_key": "orders.created",
  "queue": "shipping_queue",
  "binding": "orders.created => shipping_queue"
}
```

---

### **2.2 Kafka Topic Schema**
| Field          | Type     | Description                                                                 | Example Value                     |
|----------------|----------|-----------------------------------------------------------------------------|-----------------------------------|
| `partition`    | Integer  | Key for ordering (0–N).                                                    | `0`                                |
| `offset`       | Integer  | Position in the log.                                                        | `42`                               |
| `key`          | String   | Partitioning key (e.g., `user_id`).                                         | `user_123`                         |
| `value`        | JSON     | Message payload.                                                             | `{"action": "purchase", "amount": 99.99}` |
| `timestamp`    | Long     | Unix epoch (ms).                                                              | `1716200000000`                    |

**Example Kafka Topic:**
```json
{
  "topic": "user_activity",
  "partitions": 3,
  "replication_factor": 2,
  "records": [
    {"key": "user_1", "value": {"action": "login"}},
    {"key": "user_2", "value": {"action": "logout"}}
  ]
}
```

---

## **3. Query Examples**

### **3.1 RabbitMQ (AMQP 0-9-1)**
**Publish a message:**
```javascript
// Using RabbitMQ Node.js client
const amqp = require('amqp');
const conn = amqp.createConnection();
conn.on('ready', () => {
  const channel = conn.queue('orders', { durable: true });
  channel.publish('orders', 'orders.created', JSON.stringify({
    message_id: 'abc123',
    payload: { user_id: 1, product: 'laptop' }
  }));
});
```

**Consume with QoS (fair dispatch):**
```python
# Using Pika (Python)
import pika
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.basic_qos(prefetch_count=1)  # One message at a time
channel.basic_consume('orders', callback, queue='orders.queue')
```

---

### **3.2 Kafka (Producer/Consumer)**
**Produce a message:**
```java
// Java Producer
Properties props = new Properties();
props.put("bootstrap.servers", "kafka:9092");
Producer<String, String> producer = new KafkaProducer<>(props);
producer.send(new ProducerRecord<>("user_activity", "user_123",
  "{\"action\": \"checkout\"}"));
```

**Subscribe with consumer group:**
```python
# Python Consumer (confluent-kafka)
from confluent_kafka import Consumer
conf = {"bootstrap.servers": "kafka:9092", "group.id": "analytics"}
c = Consumer(conf)
c.subscribe(["user_activity"])
while True:
    msg = c.poll(1.0)
    print(f"Key: {msg.key()}, Value: {msg.value()}")
```

---

## **4. Best Practices**
| Area               | RabbitMQ                                      | Kafka                                         |
|--------------------|-----------------------------------------------|-----------------------------------------------|
| **Message Idempotency** | Use `message_id` + `headers` to deduplicate.  | Enable `idempotence` producer config.          |
| **Durability**     | Declare queues as `durable: true`.            | Set `retention.ms` and `min.insync.replicas`. |
| **Scaling**        | Add consumers to parallel queues.             | Increase partitions (keyed by `user_id`).      |
| **Monitoring**     | RabbitMQ Management Plugin.                   | Kafka Manager (RMK) or Prometheus.             |
| **Error Handling** | Dead-letter exchange (`x-dead-letter-exchange`). | Retry with `max.poll.interval.ms`.           |

---

## **5. Anti-Patterns**
❌ **Fire-and-forget without retries** → Use **exactly-once semantics** (Kafka transactions/RabbitMQ acknowledgments).
❌ **Single-partition Kafka topics** → Risk of bottlenecks; distribute by `user_id` or `region`.
❌ **Blocking producers/consumers** → Use async APIs (e.g., `Producer.send()` + callbacks).
❌ **No message TTL** → Set `message_ttl` (RabbitMQ) or `retention.ms` (Kafka) to auto-expire old data.

---

## **6. Related Patterns**
| Pattern                          | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| **[CQRS](https://microservices.io/patterns/data/cqrs.html)** | Separate read/write models via messages.                                     |
| **[Saga Pattern]**               | Orchestrate distributed transactions using compensating actions.              |
| **[Circuit Breaker]**             | Fail fast with RabbitMQ/Kafka timeouts.                                       |
| **[Event Sourcing]**             | Store state changes as immutable events (e.g., Kafka topics).               |
| **[Bulkhead Isolation]**          | Limit consumer queue depth to prevent overload.                              |

---

## **Further Reading**
- [RabbitMQ Official Docs](https://www.rabbitmq.com/documentation.html)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- *Designing Event-Driven Microservices* (Bojan Ozimec)
- *Kafka: The Definitive Guide* (Neha Narkhede et al.)