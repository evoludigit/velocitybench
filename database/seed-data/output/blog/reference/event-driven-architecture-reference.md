# **[Pattern] Event-Driven Architecture (EDA) – Reference Guide**

---

## **Overview**
Event-Driven Architecture (EDA) is a **decoupled messaging paradigm** where services communicate asynchronously via **events**—self-contained records of significant occurrences. Unlike request-response models, EDA enables **scalable, resilient, and loosely coupled** systems by separating event production and consumption.

**Key benefits:**
- **Decoupling** – Producers and consumers don’t need direct dependencies.
- **Scalability** – Services scale independently based on event volume.
- **Resilience** – Failure in one service doesn’t block others.
- **Real-time reactivity** – Consumers respond dynamically to business changes.

EDA is widely used for **microservices, IoT, financial systems, and real-time analytics**.

---

## **Core Concepts & Implementation Details**

### **1. Event**
- **Definition**: An immutable **record of a change** (e.g., `OrderCreated`, `PaymentFailed`).
- **Structure**:
  ```json
  {
    "id": "event-123",          // Unique identifier
    "type": "UserRegistered",   // Event classification (schema)
    "timestamp": "2024-05-20T12:00Z",  // When the event occurred
    "source": "auth-service",   // Producer service name
    "data": {                   // Payload (domain-specific)
      "userId": "u456",
      "email": "user@example.com"
    }
  }
  ```
- **Constraints**:
  - **Idempotent**: Safe to reprocess (e.g., via `eventId` or `version`).
  - **Small payload**: Avoid large attachments (use references instead).

---

### **2. Producer/Publisher**
- **Role**: Emits events when business logic triggers an action.
- **Implementation**:
  - Publish events **asynchronously** (never block).
  - Include **contextual metadata** (e.g., correlation IDs for tracing).
  - Example (pseudocode):
    ```python
    def on_user_registered(user: User):
        event = Event(
            type="UserRegistered",
            data={"userId": user.id, "email": user.email}
        )
        event_broker.publish(event)  # Async
    ```
- **Best Practices**:
  - Fail gracefully if the broker is unavailable (retries + dead-letter queue).
  - Tag events with `correlationId` for tracing across services.

---

### **3. Consumer/Subscriber**
- **Role**: Receives and processes events based on **interest** (e.g., `OrderCreated` → update inventory).
- **Implementation**:
  - Subscribe to **specific event types** (no wildcards).
  - Process events **idempotently** (e.g., deduplicate via `eventId`).
  - Example (pseudocode):
    ```python
    @event_subscriber("OrderCreated")
    def handle_order_created(event: Event):
        inventory_service.update_stock(event.data["productId"])
    ```
- **Best Practices**:
  - Use **checkpointing** (track last processed `eventId`) to avoid reprocessing.
  - Implement **backoff/retry** for failures (configurable delays).

---

### **4. Event Broker**
- **Role**: Middleware that **routes events** from producers to consumers.
- **Key Features**:
  | Feature               | Description                                                                 |
  |-----------------------|-----------------------------------------------------------------------------|
  | **Persistence**       | Stores events for late/slow consumers (e.g., Kafka, RabbitMQ).             |
  | **Partitioning**      | Scales by sharding topics (e.g., Kafka partitions).                        |
  | **Subscription Filtering** | Consumers subscribe to specific event types (e.g., `OrderCreated`).     |
  | **Retention**         | Configurable TTL (e.g., 7 days of event history).                          |
  | **Monitoring**        | Tracks lag, throughput, and failures (e.g., Prometheus metrics).          |

- **Popular Brokers**:
  - **Kafka** (high throughput, partitioned topics).
  - **RabbitMQ** (lightweight, queues).
  - **AWS SNS/SQS** (serverless event bus).
  - **Azure Event Hubs** (scalable for IoT).

---

### **5. Event Schema Registry**
- **Purpose**: Defines **contracts** for event types to ensure consistency.
- **Example Schema (JSON Schema)**:
  ```json
  {
    "$id": "https://api.example.com/schemas/UserRegistered.json",
    "type": "object",
    "properties": {
      "userId": { "type": "string" },
      "email": { "type": "string", "format": "email" }
    },
    "required": ["userId", "email"]
  }
  ```
- **Tools**:
  - **Confluent Schema Registry** (for Kafka).
  - **Apicurio** (open-source schema management).

---

### **6. Correlation & Tracing**
- **Correlation ID**: Links related events across services (e.g., order processing).
  ```json
  {
    "correlationId": "order-789",  // Links to previous event
    "parentEventId": "user-123"     // Optional: for nested events
  }
  ```
- **Tools**:
  - **Distributed tracing**: Jaeger, Zipkin.
  - **Logging**: Structured logs with `traceId`/`spanId`.

---

## **Schema Reference**
Use this table to validate event payloads.

| Field          | Type     | Required | Description                                  | Example Value                     |
|----------------|----------|----------|----------------------------------------------|-----------------------------------|
| `eventId`      | string   | Yes      | Unique identifier for the event.             | `evt-uuid456`                     |
| `eventType`    | string   | Yes      | Schema-defined event name (e.g., `OrderCreated`). | `OrderCreated`                   |
| `timestamp`    | ISO 8601 | Yes      | When the event occurred.                     | `2024-05-20T12:00:00Z`           |
| `source`       | string   | Yes      | Service that published the event.            | `order-service`                  |
| `data`         | object   | No       | Domain-specific payload.                    | `{ "orderId": "123", ... }`      |
| `correlationId`| string   | No       | Links to related events.                     | `order-456`                       |
| `metadata`     | object   | No       | Additional context (e.g., `tenantId`).       | `{ "tenant": "company-a" }`      |

---

## **Query Examples**
### **1. Publishing an Event (Producer)**
**Tool**: Kafka Producer (Python)
```python
from confluent_kafka import Producer

conf = {"bootstrap.servers": "kafka:9092"}
producer = Producer(conf)

event = {
    "eventId": "evt-uuid456",
    "eventType": "OrderCreated",
    "data": {"orderId": "123", "status": "pending"}
}
producer.produce("orders-topic", json.dumps(event).encode("utf-8"))
producer.flush()  # Ensure delivery
```

### **2. Subscribing to Events (Consumer)**
**Tool**: RabbitMQ Consumer (Node.js)
```javascript
const amqp = require("amqplib");

async function subscribe() {
  const conn = await amqp.connect("amqp://rabbitmq:5672");
  const channel = await conn.createChannel();
  await channel.assertQueue("orders-queue", { durable: true });

  channel.consume("orders-queue", async (msg) => {
    if (msg) {
      const event = JSON.parse(msg.content.toString());
      console.log(`Processing ${event.eventType}:`, event.data);
      // Business logic here
      channel.ack(msg);  // Acknowledge receipt
    }
  });
}

subscribe();
```

### **3. Schema Validation (Avro)**
**Tool**: Confluent Schema Registry
```bash
# Publish an event with Avro schema validation
curl -X POST \
  -H "Content-Type: application/vnd.kafka.json.v2+json" \
  --data '{"records":[{"value":{"userId":"u456","email":"test@example.com"}}]}' \
  --header "Content-Type: application/vnd.kafka.avro+json; version=2" \
  https://schema-registry:8081/subjects/UserRegistered-value/versions/latest
```

---

## **Related Patterns**
| Pattern                          | Description                                                                 | When to Use                          |
|----------------------------------|-----------------------------------------------------------------------------|--------------------------------------|
| **CQRS**                         | Separates read/write models using event sourcing.                          | Complex queries, audit trails.       |
| **Saga Pattern**                 | Manages distributed transactions via local compensating actions.           | Multi-service workflows.             |
| **Command Query Responsibility Segregation (CQRS)** | Decouples read/write operations via events. | High-read scalability.               |
| **Event Sourcing**               | Stores state changes as an append-only event log.                          | Auditability, time-travel queries.   |
| **Pipeline Pattern**             | Processes events in a sequential pipeline (e.g., validation → enrichment).  | Data processing workflows.           |
| **Event Carousel**               | Pre-computes events for high-frequency consumers.                          | Predictable workloads.               |

---

## **Anti-Patterns**
| **Anti-Pattern**               | **Problem**                                                                 | **Solution**                          |
|---------------------------------|-----------------------------------------------------------------------------|---------------------------------------|
| **Event Storming Without Context** | Overly granular events lead to chaos.                                     | Group events into bounded contexts.   |
| **Blocking Producers**          | Producers wait for consumers (violates async principle).                   | Use async publish + dead-letter queue.|
| **No Idempotency**              | Duplicate events cause side effects (e.g., duplicate payments).             | Use `eventId` + dedupe logic.         |
| **Tight Coupling to Broker**    | Direct broker dependencies make systems fragile.                          | Abstract behind an interface (e.g., `IEventBroker`). |
| **Ignoring Retention**          | Events vanish after TTL (e.g., debug failure).                            | Configure long retention + archival. |

---

## **Troubleshooting**
| **Issue**                     | **Diagnosis**                          | **Fix**                              |
|-------------------------------|----------------------------------------|--------------------------------------|
| **Consumer Lag**              | Consumers fall behind event stream.    | Scale consumers or optimize processing. |
| **Duplicate Events**          | Event reprocessing due to retries.    | Implement idempotency keys.           |
| **Broker Overload**           | High throughput crashes the broker.    | Partition topics or use a managed broker (e.g., Kafka Cluster). |
| **Missing Events**            | Events not delivered to consumers.     | Check broker logs + consumer offsets. |
| **Schema Mismatch**           | Producer/consumer use incompatible schemas. | Enforce schema registry compliance. |

---

## **Tools & Libraries**
| **Component**       | **Tools/Libraries**                                                                 |
|---------------------|------------------------------------------------------------------------------------|
| **Event Brokers**   | Kafka, RabbitMQ, AWS SNS/SQS, Azure Event Hubs, NATS                          |
| **Schemas**         | Avro, Protobuf, JSON Schema, Confluent Schema Registry                          |
| **Serialization**   | Protobuf (binary), Avro (schema evolution), JSON (human-readable)               |
| **Tracing**         | Jaeger, Zipkin, OpenTelemetry                                                   |
| **Monitoring**      | Prometheus + Grafana, Kafka Lag Exporter, Datadog                              |
| **Testing**         | TestContainers (broker tests), Kafka Unit (message testing)                     |

---

## **Best Practices**
1. **Design for Failure**
   - Assume the broker or services will fail; implement retries + dead-letter queues.
2. **Keep Events Small**
   - Large payloads slow down processing. Use references (e.g., `{"transactionId": "123", "url": "/transactions/123"}`).
3. **Version Events**
   - Use backward-compatible schemas (e.g., add optional fields).
4. **Monitor End-to-End**
   - Track event throughput, latency, and consumer lag.
5. **Secure Events**
   - Sign events (e.g., JWT) or use broker ACLs to prevent spoofing.
6. **Document Schemas**
   - Publish schemas in a registry (e.g., `user-registered-v1.json`).

---
**Further Reading**:
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Event-Driven Architecture Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/)
- [CQRS and Event Sourcing](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)