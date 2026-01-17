**[Pattern] Monolith-to-Microservices Migration Reference Guide**

---

### **Overview**
The **Monolith-to-Microservices Migration** pattern is a structured approach to refactoring a monolithic application into loosely coupled microservices. This process involves breaking down large, tightly integrated systems into smaller, independently deployable services while ensuring backward compatibility, minimal downtime, and gradual adoption. The goal is to improve scalability, fault isolation, and agility without replacing the entire system at once.

This pattern is critical for large-scale applications where the monolith has become unwieldy, affecting performance, team velocity, or deployment flexibility. It balances risk mitigation with business continuity by introducing microservices incrementally, often using design patterns like **Domain-Driven Design (DDD)**, **Strangler Fig**, or **Sidecar Services**.

---

### **Schema Reference**
The following table outlines key components and their roles in a monolith migration:

| **Component**               | **Description**                                                                                     | **Example**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Monolith Core**           | The existing, unmodified legacy system serving as the foundation.                                   | `OrderService` in a legacy e-commerce system.                             |
| **Microservice Boundary**   | Defined using DDD boundaries (e.g., Bounded Contexts) to isolate domains for modularity.          | `InventoryService`, `PaymentService`, `UserProfileService`.                |
| **API Gateway**             | Acts as a reverse proxy to route requests to legacy or new services, enabling phased migration.    | Kubernetes Ingress Controller or Kong.                                    |
| **Service Mesh**            | Manages inter-service communication (e.g., retries, circuit breaking, observability).              | Istio, Linkerd, or Consul Connect.                                         |
| **Event Bus**               | Decouples services via asynchronous messaging (e.g., Kafka, RabbitMQ) for eventual consistency.    | Order updates published to `PaymentService` via Kafka.                    |
| **Database Per Service**    | Each microservice owns its database (avoiding shared schemas) with eventual consistency models.   | `UserService` uses PostgreSQL; `OrderService` uses MongoDB.               |
| **Saga Pattern**            | Orchestrates distributed transactions across services using compensating actions.                 | "Order placed → Payment processed → Inventory deducted" workflow.         |
| **Feature Flags**           | Gradually roll out new microservices while hiding them from legacy clients.                       | Toggle `NewCheckoutFlow` for 10% of users.                                |
| **Migration Proxy**         | Translates requests between legacy and new services (e.g., REST ↔ gRPC).                        | Spring Cloud Gateway or AWS API Gateway.                                  |
| **Observability Tools**     | Monitors performance, traces, and logs across services (e.g., Prometheus, Jaeger).               | Metrics on `OrderService` latency post-migration.                         |

---

### **Implementation Details**
#### **1. Phased Migration Strategies**
Choose one or combine approaches based on risk tolerance:
- **Strangler Fig Pattern**:
  - Wrap legacy monolith functionality with new microservices.
  - Example: Replace `/orders` endpoint with a `OrderService` microservice while keeping the old endpoint as a proxy.
  - *Tools*: Spring Cloud OpenFeign, AWS Lambda@Edge.

- **Domain-Driven Decomposition**:
  - Identify bounded contexts (domains) to extract as microservices.
  - Example: Split `UserManagement` and `Billing` into separate services.
  - *Tools*: EventStorming workshops, Hexagonal Architecture.

- **Big Bang (Advanced)**:
  - Replace the monolith in one go (high risk; avoid unless absolutely necessary).

#### **2. Database Migration**
- **Option A: Dual-Write (Temporary)**
  - Write to both legacy and new databases until ready to cut over.
  - *Risk*: Data inconsistency; mitigate with transactions or eventual consistency.
- **Option B: CDC (Change Data Capture)**
  - Replicate changes from legacy DB to new DB streams (e.g., Debezium).
  - Example: Sync MySQL orders to a Kafka topic for `OrderService`.
- **Option C: Hybrid Reads**
  - Legacy services read from old DB; new services read from their own DB.
  - *Tool*: Read replicas or shared caches (Redis).

#### **3. API Contracts**
- **Backward Compatibility**:
  - Maintain legacy APIs for gradual adoption.
  - Use versioned endpoints: `/v1/orders`, `/v2/orders`.
- **Forward Compatibility**:
  - Introduce new schemas (e.g., JSON Schema) for future services.
  - *Tool*: OpenAPI/Swagger for contract-first design.

#### **4. Inter-Service Communication**
| **Pattern**          | **Use Case**                                  | **Example**                                  | **Tools**                     |
|----------------------|-----------------------------------------------|----------------------------------------------|-------------------------------|
| **Synchronous**      | Request-response (low latency).              | `OrderService` calls `PaymentService`.       | gRPC, REST, GraphQL.          |
| **Asynchronous**     | Event-driven (high throughput).              | Order created → `OrderCreatedEvent` published. | Kafka, RabbitMQ, NATS.        |
| **CQRS**             | Separate read/write models for performance.   | `OrderReadModel` and `OrderWriteModel`.      | DDD + Event Sourcing.         |
| **Sidecar Proxy**    | Translate protocols (e.g., REST ↔ gRPC).     | Legacy client → `sidecar` → `OrderService`.   | Envoy, Nginx.                  |

#### **5. Deployment Strategies**
- **Blue-Green Deployment**:
  - Run old and new versions in parallel; switch traffic via feature flags.
- **Canary Releases**:
  - Roll out to a subset of users (e.g., 5%) before full deployment.
- **Dark Launches**:
  - Deploy new services but hide them from users until ready.

---
### **Query Examples**
#### **1. Sync Request (gRPC)**
**Client (OrderService)**: Calls `PaymentService` to process payment.
```protobuf
service PaymentService {
  rpc ProcessPayment (PaymentRequest) returns (PaymentResponse) {}
}

message PaymentRequest {
  string order_id = 1;
  double amount = 2;
}
```
**Implementation** (Go):
```go
conn, _ := grpc.Dial("payment-service:50051", grpc.WithInsecure())
client := pb.NewPaymentServiceClient(conn)
resp, _ := client.ProcessPayment(ctx, &pb.PaymentRequest{OrderId: "123", Amount: 99.99})
```

#### **2. Async Event (Kafka)**
**OrderService** publishes an event when an order is created.
```json
{
  "event_type": "OrderCreated",
  "order_id": "456",
  "status": "PENDING",
  "metadata": { "user_id": "789", "items": [...] }
}
```
**PaymentService** consumes the event:
```python
def consume_order_created(message: dict):
    if message["event_type"] == "OrderCreated":
        process_payment(message["order_id"])
```

#### **3. Database Query (MongoDB)**
**OrderService** schema:
```json
{
  "_id": "7e3b0ce3-abc1-45dc-923b-4bb9e2f3e0c9",
  "user_id": "789",
  "items": [
    { "product_id": "101", "quantity": 2 }
  ],
  "status": "COMPLETED"
}
```
**Query** (Aggregation Pipeline):
```javascript
db.orders.aggregate([
  { $match: { status: "COMPLETED" } },
  { $group: { _id: "$user_id", total: { $sum: "$items.quantity" } } }
])
```

---
### **Error Handling & Resilience**
| **Scenario**               | **Mitigation Strategy**                          | **Tool/Pattern**                     |
|----------------------------|--------------------------------------------------|---------------------------------------|
| **Service Unavailable**    | Retry with exponential backoff.                 | Resilience4j, Hystrix.                |
| **Database Connection Loss**| Use connection pooling + retry.                 | HikariCP, PgBouncer.                  |
| **Event Delivery Failure** | Dead-letter queue for failed events.            | Kafka DLQ, Sqs Dead-Letter Queue.    |
| **Schema Mismatch**        | Schema registry (Avro/Protobuf).               | Confluent Schema Registry.            |
| **Cascading Failures**     | Circuit breakers to isolate failures.           | Istio, Spring Retry.                  |

---
### **Related Patterns**
1. **[Strangler Fig Pattern]**
   - Gradually replace monolith components with microservices while keeping the original system alive.
   - *Use case*: Incremental migration with minimal downtime.

2. **[Domain-Driven Design (DDD)]**
   - Model services around business domains (Bounded Contexts) to align with organizational boundaries.
   - *Tool*: EventStorming for workshopping domains.

3. **[Circuit Breaker]**
   - Prevents cascading failures by stopping requests to failing services.
   - *Tool*: Hystrix, Resilience4j.

4. **[Saga Pattern]**
   - Manages distributed transactions across microservices using compensating actions.
   - *Example*: "If payment fails, refund inventory."

5. **[Event Sourcing]**
   - Stores state changes as a sequence of events for auditability and replayability.
   - *Tool*: EventStoreDB, Axon Framework.

6. **[Service Mesh]**
   - Abstracts inter-service communication with features like retries, tracing, and mTLS.
   - *Tool*: Istio, Linkerd.

---
### **Anti-Patterns to Avoid**
1. **Premature Decomposition**:
   - Extracting too many microservices prematurely increases complexity without clear business value.
   - *Fix*: Start with 2–4 core domains.

2. **Shared Database**:
   - Microservices should avoid sharing databases to maintain loose coupling.
   - *Fix*: Database per service with eventual consistency.

3. **Synchronous Monoliths**:
   - Keeping all services tightly coupled via HTTP calls defeats microservices benefits.
   - *Fix*: Use async events (e.g., Kafka) for decoupling.

4. **Ignoring Observability**:
   - Without metrics, logs, and traces, debugging distributed systems is impossible.
   - *Fix*: Instrument with OpenTelemetry.

---
### **Tools & Technologies**
| **Category**          | **Tools**                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| **Service Mesh**      | Istio, Linkerd, Consul Connect                                               |
| **Event Bus**         | Kafka, RabbitMQ, NATS, AWS SNS/SQS                                         |
| **API Gateway**       | Kong, AWS API Gateway, Spring Cloud Gateway                                 |
| **Observability**     | Prometheus, Grafana, Jaeger, OpenTelemetry                                  |
| **CI/CD**             | ArgoCD, Jenkins, Tekton, GitHub Actions                                     |
| **Database**          | PostgreSQL, MongoDB, Cassandra, DynamoDB                                   |
| **Schema Management** | Avro, Protobuf, JSON Schema, Confluent Schema Registry                    |
| **Testing**           | Postman, Pact, Gatling, TestContainers                                       |

---
### **Checklist for Migration**
1. [ ] **Assess**: Profile the monolith (performance, dependencies, user traffic).
2. [ ] **Define Boundaries**: Identify Bounded Contexts using DDD.
3. [ ] **Start Small**: Begin with a non-critical domain (e.g., user profiles).
4. [ ] **Decompose**: Extract services one at a time (e.g., "Inventory" → `InventoryService`).
5. [ ] **Decouple**: Replace direct calls with events/APIs.
6. [ ] **Monitor**: Deploy observability tools early.
7. [ ] **Iterate**: Refactor incrementally; avoid big-bang replacements.
8. [ ] **Document**: Maintain API contracts and migration status.

---
**Note**: Migration success depends on **team buy-in**, **gradual rollout**, and **cross-functional collaboration** (DevOps, QA, Business). Start with a **proof-of-concept** (e.g., migrate a single feature) before full-scale deployment.