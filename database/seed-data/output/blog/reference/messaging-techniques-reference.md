**[Pattern] Messaging Techniques: Reference Guide**

---

### **Overview**
The **Messaging Techniques** pattern enables decoupled communication between systems, components, or services via asynchronous message exchange. This pattern supports event-driven architectures, scalability, and resilience by decoupling senders and receivers. Common techniques include **Synchronous Request-Reply**, **Asynchronous Publish-Subscribe**, **Message Queues**, and **Event Sourcing**. Proper implementation ensures reliable message delivery, fault tolerance, and efficient resource utilization.

Key use cases include:
- **Decoupled workflows** (e.g., order processing → payment → inventory updates).
- **Load balancing** (distributing tasks across services).
- **Event-driven notifications** (e.g., user actions, system state changes).
- **Resilience** (handling failures without cascading downtime).

---

---

### **1. Key Concepts & Schema Reference**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Schema Example (JSON)**                                                                                                      |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Producer**              | Sender of messages (e.g., API, microservice, event generator).                                                                                                                                               | `{ "event": "OrderCreated", "payload": { "orderId": "123", "userId": "456" } }`                                        |
| **Consumer**              | Receiver of messages (e.g., payment service, notification service).                                                                                                                                         | N/A                                                                                                                            |
| **Message Broker**        | Middleware (e.g., RabbitMQ, Kafka, AWS SQS) that buffers, routes, and ensures delivery of messages.                                                                                                        | N/A                                                                                                                            |
| **Message Queue**         | FIFO structure for **point-to-point** communication (e.g., a service sends a task to a worker queue).                                                                                                    | N/A                                                                                                                            |
| **Topic/Channel**         | Logical namespace for **publish-subscribe** (e.g., `orders.created`, `payments.failed`).                                                                                                                     | N/A                                                                                                                            |
| **Message Schema**        | Structured format defining payload fields (e.g., Avro, Protobuf, JSON Schema).                                                                                                                               | ```{ "type": "object", "properties": { "orderId": { "type": "string" } } }```                                              |
| **Acknowledgment (ACK/NACK)** | Confirmation from consumer to broker that a message was processed successfully (or failed).                                                                                                              | `ACK`: `{ "status": "processed", "messageId": "msg_123" }`                          |
| **Durability**            | Guarantee that messages persist until consumed (e.g., persistent queues, transaction logs).                                                                                                                   | Broker config: `{"persistence": "disk", "retention": "14d"}`                                                                 |
| **Idempotency**           | Design ensuring repeated messages cause no duplicate side effects (e.g., via message deduplication keys).                                                                                                  | `payload.id`: `orderId` (used to skip reprocessing)                                                                         |
| **Dead Letter Queue (DLQ)**| Queue for messages that fail processing (e.g., due to invalid payloads or timeouts).                                                                                                                      | `DLQ`: `{ "originalQueue": "order.queue", "failedAt": "2024-01-01T12:00:00Z", "error": "InvalidOrder" }`                  |
| **Partitioning**          | Splitting topics into parallel streams (e.g., Kafka partitions) for scalability.                                                                                                                           | `partitionKey`: `userId` (routes messages to the same partition for a user)                                               |

---

---

### **2. Implementation Techniques**

#### **A. Synchronous Request-Reply**
**Use Case:** Direct, real-time responses (e.g., API calls to a backend).
**Schema:**
```json
{
  "request": {
    "method": "POST",
    "path": "/orders",
    "headers": { "Content-Type": "application/json" },
    "body": { "item": "laptop", "quantity": 1 }
  },
  "response": {
    "status": 200,
    "body": { "orderId": "abc123" }
  }
}
```

**Key Properties:**
- **Timeout Handling:** Define a `timeout` field in the request (e.g., `timeoutMs: 5000`).
- **Retry Logic:** Implement exponential backoff for transient failures.
- **Idempotency Key:** Use a `requestId` to avoid duplicate processing.

**Example (gRPC):**
```protobuf
service OrderService {
  rpc CreateOrder (OrderRequest) returns (OrderResponse) {}
}
```

---

#### **B. Asynchronous Publish-Subscribe**
**Use Case:** Event broadcasting (e.g., "UserLoggedIn" → notify multiple services).
**Schema:**
```json
{
  "event": "UserLoggedIn",
  "payload": {
    "userId": "789",
    "timestamp": "2024-01-01T10:00:00Z"
  },
  "metadata": {
    "source": "auth-service",
    "version": "1.0"
  }
}
```

**Broker Configuration (Kafka):**
```json
{
  "topic": "user.events",
  "partitions": 3,          // For parallel processing
  "replicationFactor": 2,   // High availability
  "retentionMs": 604800000  // 7 days
}
```

**Consumer Groups:**
- Multiple consumers can subscribe to the same topic **partition** (load balancing).
- Example: A `notification-service` and `analytics-service` consume `user.events`.

---

#### **C. Message Queues (Point-to-Point)**
**Use Case:** Task distribution (e.g., thumbnail generation, background jobs).
**Schema:**
```json
{
  "task": "generate-thumbnail",
  "input": {
    "imageUrl": "https://example.com/image.jpg",
    "width": 200
  },
  "priority": "normal"
}
```

**Queue Types:**
| **Queue**       | **Purpose**                                  | **Example**                          |
|------------------|----------------------------------------------|--------------------------------------|
| **Priority Queue** | Higher-priority tasks first (e.g., urgent orders). | `priority: "high"` → processed before `priority: "low"`. |
| **Delayed Queue** | Schedule task execution (e.g., "send reminder in 1 hour"). | `{ "delay": 3600000 }` (1 hour).     |

**Example (AWS SQS):**
```json
{
  "MessageBody": "{\"action\": \"send-email\"}",
  "DelaySeconds": 60,  // Delay by 60 seconds
  "MessageGroupId": "user_123"  // For FIFO queues
}
```

---

#### **D. Event Sourcing**
**Use Case:** Auditing and replaying state changes (e.g., financial transactions).
**Schema:**
```json
{
  "eventId": "ev_1001",
  "eventType": "OrderPlaced",
  "aggregateId": "order_abc123",
  "timestamp": "2024-01-01T09:00:00Z",
  "data": {
    "items": [{"product": "book", "price": 19.99}],
    "total": 19.99
  }
}
```

**Storage Backend:**
- Use a **time-series database** (e.g., InfluxDB) or **event store** (e.g., EventStoreDB).
- Example query to replay events for an order:
  ```sql
  SELECT * FROM events
  WHERE aggregateId = 'order_abc123'
  ORDER BY timestamp;
  ```

**Projection:**
```json
{
  "currentState": {
    "orderId": "abc123",
    "status": "paid",  // Derived from events
    "total": 19.99
  }
}
```

---

---
### **3. Query Examples**
#### **A. Querying a Message Broker (Kafka)**
**Find all failed payments in the last 24 hours:**
```sql
SELECT *
FROM payments_failed
WHERE timestamp >= now() - INTERVAL '24 hour'
AND status = 'failed';
```

**Filter by topic:**
```bash
kafka-console-consumer --topic payments.failed --bootstrap-server broker:9092 --from-beginning
```

---

#### **B. Querying a Message Queue (SQS)**
**List unprocessed messages in a queue:**
```bash
aws sqs list-queue-attributes --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/order-worker-queue
```

**Peek at messages (without deletion):**
```bash
aws sqs receive-message --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/order-worker-queue --max-number-of-messages 10 --message-attribute-names All
```

---

#### **C. Event Sourcing Query**
**Reconstruct order state from events:**
```python
def get_order_state(order_id):
    events = event_store.query(aggregate_id=order_id)
    state = initial_state()
    for event in events:
        state = apply_event(state, event)
    return state
```

---

---
### **4. Error Handling & Best Practices**
| **Scenario**               | **Solution**                                                                                                                                                                                                 | **Example**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Message Duplication**     | Use idempotency keys (e.g., `orderId`) to skip reprocessing.                                                                                                                                                   | If `orderId: "abc123"` already processed, NACK the message.                                   |
| **Consumer Lag**            | Monitor broker metrics (e.g., Kafka’s `consumer-lag`). Scale consumers or increase partition count.                                                                                                          | ```bash
kafka-consumer-groups --bootstrap-server broker:9092 --describe --group notification-service
```                                                                                               |
| **Network Partition**       | Implement circuit breakers (e.g., Hystrix) to fail fast.                                                                                                                                                       | Throttle requests after 3 consecutive failures.                                                 |
| **Schema Evolution**        | Use forward/backward compatibility (e.g., Protobuf, Avro).                                                                                                                                                   | Add optional fields: `{ "newField": { "type": "string", "default": "" } }`                     |
| **Message Timeouts**        | Set `deliveryTimeoutMs` in brokers (e.g., Kafka: 7 days).                                                                                                                                                 | ```json
{ "deliveryTimeoutMs": 604800000 }  // 7 days
```                                                                                               |

---

---
### **5. Related Patterns**
| **Pattern**                  | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **CQRS**                     | Separate read and write models using events.                                                                                                                                                           | High-read-load scenarios (e.g., e-commerce dashboards).                                         |
| **Saga**                     | Manage distributed transactions via compensating actions.                                                                                                                                               | Microservices with multiple steps (e.g., order → shipping → payment).                            |
| **Event-Driven Architecture**| Loosely coupled services communicating via events.                                                                                                                                                      | Real-time systems (e.g., IoT, live updates).                                                    |
| **Polling vs. Push**         | Consumers **poll** (e.g., REST polling) vs. **push** (e.g., Kafka).                                                                                                                                         | Push for high throughput; polling for low-latency control.                                      |
| **Bulkhead Pattern**         | Isolate message processing threads to prevent cascading failures.                                                                                                                                          | High-volume systems (e.g., payment processing).                                                  |

---

---
### **6. Tools & Libraries**
| **Component**               | **Tools/Libraries**                                                                                                                                                                                                 | **Language Support**                          |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| **Message Brokers**          | RabbitMQ, Apache Kafka, Amazon SQS, NATS                                                                                                                                                               | Multi-language                                 |
| **Serialization**            | Protobuf, Avro, MessagePack, JSON                                                                                                                                                                         | All major languages                           |
| **Clients**                  | Kafka Java/Python SDK, RabbitMQ AMQP, AWS SDK for SQS                                                                                                                                                     | Language-specific                              |
| **Monitoring**               | Prometheus + Grafana, Datadog, Kafka Manager                                                                                                                                                           | Web-based                                    |
| **Event Sourcing**           | EventStoreDB, Axon Framework, EventSourced                                                                                                                                                               | Java/Python/C#                                |

---
### **7. Example Workflow: Order Processing**
1. **Producer** (Order Service):
   ```json
   {
     "event": "OrderCreated",
     "payload": {
       "orderId": "abc123",
       "items": [{"product": "book", "price": 19.99}],
       "total": 19.99
     }
   }
   ```
   → Published to `orders.events` (Kafka topic).

2. **Consumer 1** (Payment Service):
   - Subscribes to `orders.events`.
   - Processes payment; publishes `PaymentProcessed` if successful or `PaymentFailed` otherwise.

3. **Consumer 2** (Inventory Service):
   - Subscribes to `orders.events`.
   - Deducts stock; publishes `InventoryUpdated`.

4. **Saga Orchestrator** (if needed):
   - Waits for `PaymentProcessed` and `InventoryUpdated` before publishing `OrderFulfilled`.

5. **Event Sourcing Store**:
   - Persists all events for `orderId: "abc123"` to replay state.

---
### **8. Performance Considerations**
- **Throughput:** Scale consumers horizontally (more partitions → more consumers).
- **Latency:** Prioritize low-latency brokers (e.g., NATS) for real-time needs.
- **Storage:** Use compressed formats (e.g., Protobuf) for large payloads.
- **Idempotency:** Cache processed messages (e.g., Redis) to avoid reprocessing.