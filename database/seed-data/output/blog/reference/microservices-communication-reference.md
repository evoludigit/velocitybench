# **[Pattern] Microservices Communication Patterns – Reference Guide**
*Optimal strategies for synchronous and asynchronous communication in distributed systems.*

---

## **Overview**
Microservices rely on **inter-process communication (IPC)** to interact across service boundaries. This pattern categorizes two primary communication paradigms:
1. **Synchronous (Request-Response)** – Direct, two-way communication (e.g., REST/HTTP, gRPC).
2. **Asynchronous (Event-Driven/Messaging)** – Indirect, one-way message exchanges (e.g., Kafka, RabbitMQ).

Key trade-offs:
- **Synchronous**:
  - *Pros*: Simple to implement, immediate responses, strong consistency.
  - *Cons*: Tight coupling, latency-sensitive, blocking calls.
- **Asynchronous**:
  - *Pros*: Decoupled services, fault tolerance, scalability.
  - *Cons*: Complex event handling, eventual consistency, debugging overhead.

Choosing the right pattern depends on use cases (e.g., high-throughput vs. low-latency) and adherence to the **Single Responsibility Principle** (SRP).

---

## **1. Synchronous Communication**

### **Key Concepts**
| **Component**               | **Description**                                                                                     | **Example Technologies**          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------|
| **API Gateway**            | Acts as a reverse proxy to route requests to the appropriate microservice.                        | Kong, Apigee, AWS API Gateway     |
| **Service Mesh**           | Handles service-to-service communication (traffic routing, load balancing, retries).             | Istio, Linkerd, Consul            |
| **Protocol Buffers (protobuf)** | Binary serialization for efficient request/response payloads.                                      | gRPC, REST (JSON)                 |
| **Timeout & Retry Policies** | Configurable timeouts and exponential backoff to handle transient failures.                       | Resilience4j (Java), Polly (.NET) |
| **Circuit Breaker**        | Prevents cascading failures by stopping calls to a failing service after a threshold is hit.       | Hystrix, Netflix OSS              |
| **Idempotency Keys**       | Ensures retries don’t cause duplicate side effects (e.g., duplicate orders).                     | UUIDs, database sequences         |

---

### **Implementation Workflow**
1. **Client** sends a request to a service via HTTP/gRPC.
2. **Service Mesh/API Gateway** routes the request (e.g., based on service discovery).
3. **Target Service** processes the request, applies business logic, and returns a response.
4. **Error Handling**: Circuit breakers or retries manage failures; clients handle 4xx/5xx status codes.

---

### **Schema Reference**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------|
| `requestId`             | String (UUID)  | Unique identifier for tracing requests across services.                          | `123e4567-e89b-12d3-a456-426614174000` |
| `serviceName`           | String         | Name of the target microservice (e.g., `order-service`, `payment-service`).     | `order-service`                      |
| `headers`               | Object         | HTTP headers (e.g., `Authorization`, `Content-Type`).                           | `{ "Authorization": "Bearer xxxx" }`  |
| `body`                  | JSON/Protobuf  | Request payload (varies by endpoint).                                           | `{ "userId": 123, "amount": 99.99 }`  |
| `timeoutMs`             | Integer        | Max time (ms) to wait for a response.                                           | `3000`                                |
| `retryPolicy`           | Object         | Retry strategy for transient failures.                                          | `{ "maxAttempts": 3, "backoff": "exponential" }` |
| `response`              | JSON/Protobuf  | Success/failure response from the service.                                       | `{ "status": "success", "orderId": 456 }` |

---

### **Query Examples**
#### **1. REST API (HTTP/JSON)**
**Request:**
```http
POST /orders HTTP/1.1
Host: order-service.example.com
Content-Type: application/json
Authorization: Bearer xxxx

{
  "userId": 123,
  "items": [
    { "productId": "prod1", "quantity": 2 }
  ]
}
```
**Response (Success):**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "orderId": "ord_789",
  "status": "created",
  "total": 39.99
}
```
**Response (Error):**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 10
```

#### **2. gRPC (Protobuf)**
**`.proto` Definition:**
```protobuf
service OrderService {
  rpc CreateOrder (OrderRequest) returns (OrderResponse);
}

message OrderRequest {
  string user_id = 1;
  repeated ProductItem items = 2;
}

message OrderResponse {
  string order_id = 1;
  string status = 2;
  double total = 3;
}
```
**gRPC Call (Client-Side):**
```python
# Using Python's gRPC
order = order_service.CreateOrder(OrderRequest(user_id="123", items=[...]))
print(order.order_id)  # "ord_789"
```

#### **3. Service Mesh Routing (Istio)**
**VirtualService (YAML):**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: payment-service
spec:
  hosts:
  - payment-service
  http:
  - route:
    - destination:
        host: payment-service
        subset: v1
    retries:
      attempts: 3
      perTryTimeout: 2s
```

---

## **2. Asynchronous Communication**

### **Key Concepts**
| **Component**               | **Description**                                                                                     | **Example Technologies**          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------|
| **Event Broker**           | Centralized system for publishing/subcribing to events (e.g., order-created, payment-processed). | Apache Kafka, RabbitMQ, AWS SNS |
| **Event Sourcing**         | Stores state changes as a sequence of events for auditability.                                      | EventStoreDB, Kafka Streams       |
| **Message Schema**         | Structured event payloads (e.g., Avro, Protobuf, JSON Schema).                                    | Schema Registry (Confluent)       |
| **Dead Letter Queue (DLQ)** | Captures failed events for manual review/reprocessing.                                             | Kafka DLQ, SNS Dead-Letter Topic  |
| **Saga Pattern**           | Manages distributed transactions via local transactions + compensating actions.                     | Choreography (events) or Orchestration (state machine) |

---

### **Implementation Workflow**
1. **Service A** publishes an event (e.g., `OrderCreated`) to a topic.
2. **Event Broker** delivers the event to subscribed services (e.g., `NotificationService`, `InventoryService`).
3. **Service B** processes the event asynchronously and may publish follow-up events (e.g., `PaymentInitiated`).
4. **Monitoring**: Tools track event consumption (e.g., Kafka consumer lag).

---

### **Schema Reference**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------|
| `eventId`               | String (UUID)  | Unique identifier for the event.                                               | `550e8400-e29b-41d4-a716-446655440000` |
| `eventType`             | String (Enum)  | Type of event (e.g., `ORDER_CREATED`, `PAYMENT_FAILED`).                        | `ORDER_CREATED`                      |
| `timestamp`             | ISO 8601       | When the event was published.                                                   | `2023-10-01T12:00:00Z`               |
| `sourceService`         | String         | Name of the service emitting the event.                                         | `order-service`                      |
| `payload`               | JSON/Protobuf  | Event-specific data.                                                           | `{ "orderId": "ord_789", "userId": 123 }` |
| `metadata`              | Object         | Contextual data (e.g., `correlationId` for tracing).                            | `{ "correlationId": "123e4567..." }` |
| `schemaVersion`         | String         | Version of the event schema (for backward compatibility).                       | `1.0`                                 |

---

### **Event Examples**
#### **1. Kafka Topic (`order-events`)**
**Event Payload (JSON):**
```json
{
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "eventType": "ORDER_CREATED",
  "timestamp": "2023-10-01T12:00:00Z",
  "sourceService": "order-service",
  "payload": {
    "orderId": "ord_789",
    "userId": 123,
    "items": [
      { "productId": "prod1", "quantity": 2 }
    ]
  },
  "metadata": {
    "correlationId": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

#### **2. Consumer (Python with Kafka-Python)**
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'order-events',
    bootstrap_servers=['kafka-broker:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    event = message.value
    if event['eventType'] == 'ORDER_CREATED':
        print(f"Processing order {event['payload']['orderId']}")
        # Trigger downstream logic (e.g., send email)
```

#### **3. Saga Pattern (Choreography)**
**Order Service (Publishes `ORDER_CREATED`):**
```python
def create_order(user_id, items):
    order = save_order(user_id, items)
    event_bus.publish(
        eventType='ORDER_CREATED',
        payload={'orderId': order.id, 'userId': user_id}
    )
```

**Payment Service (Subscribes to `ORDER_CREATED`):**
```python
@event_bus.subscribe('ORDER_CREATED')
def handle_order_created(event):
    if is_payment_required(event.payload):
        initiate_payment(event.payload['orderId'])
        event_bus.publish(
            eventType='PAYMENT_INITIATED',
            payload={'orderId': event.payload['orderId']}
        )
```

---

## **3. Hybrid Approach**
Combine both patterns for optimal resilience:
- Use **synchronous** for critical, low-latency operations (e.g., auth checks).
- Use **asynchronous** for non-critical, event-driven workflows (e.g., notifications).
- Example:
  - **API Gateway** routes a `POST /orders` to the `OrderService` (sync).
  - `OrderService` publishes an `ORDER_CREATED` event (async).

---

## **Schema Migration**
| **Field**          | **Old Schema (v1.0)**       | **New Schema (v2.0)**       | **Migration Strategy**                |
|--------------------|----------------------------|----------------------------|---------------------------------------|
| `currency`         | String                     | Enum (`USD`, `EUR`, `GBP`)  | Add validation layer in v1 → v2.       |
| `shippingAddress`  | Partial object             | Full object (mandatory)    | Backward-compatible with defaults.    |

---

## **Query Examples (Async)**
#### **1. Publishing an Event (Java with Spring Kafka)**
```java
@Bean
public KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate() {
    return new KafkaTemplate<>(producerFactory());
}

public void createOrder(Order order) {
    OrderCreatedEvent event = new OrderCreatedEvent(order.getId(), order.getUserId());
    kafkaTemplate.send("order-events", event);
}
```

#### **2. Consuming with Error Handling**
```python
def consume_with_retry(topic, max_retries=3):
    for attempt in range(max_retries):
        try:
            for message in KafkaConsumer(topic, ...):
                process_event(message.value)
                break  # Success
        except Exception as e:
            if attempt == max_retries - 1:
                send_to_dlq(message.value)
            time.sleep(2 ** attempt)  # Exponential backoff
```

---

## **Related Patterns**
1. **[Service Discovery]** – Dynamically locate services (e.g., Consul, Eureka).
2. **[Circuit Breaker]** – Prevent cascading failures (e.g., Hystrix, Resilience4j).
3. **[Retries & Backoff]** – Handle transient failures gracefully.
4. **[Idempotency]** – Ensure safe retries (e.g., duplicate order prevention).
5. **[Event Sourcing]** – Store state as a sequence of events for auditability.
6. **[Saga Pattern]** – Manage distributed transactions via events/choreography.
7. **[API Gateway]** – Centralized entry point for microservices.
8. **[Service Mesh]** – Handle service-to-service communication (e.g., Istio).

---
## **Best Practices**
- **Synchronous**:
  - Limit payload sizes (<1MB) to avoid latency.
  - Use **gRPC** for performance-critical paths.
  - Implement **timeouts** and **circuit breakers**.
- **Asynchronous**:
  - Design for **eventual consistency** (not strong consistency).
  - Use **idempotent producers/consumers** to avoid duplicates.
  - Monitor **consumer lag** in brokers like Kafka.
- **Hybrid**:
  - Start with sync for MVP, introduce async for scalability.
  - Use **event schemas** to enforce backward compatibility.

---
## **Anti-Patterns**
- **Tight Coupling**: Avoid direct service references; use API contracts.
- **Fire-and-Forget**: Never assume async messages are delivered (use acknowledgments).
- **Synchronous Blast Radius**: Don’t chain sync calls across services (use async).
- **Unbounded Retries**: Exponential backoff prevents overload.
- **Schema Drift**: Version schemas to avoid breaking changes.