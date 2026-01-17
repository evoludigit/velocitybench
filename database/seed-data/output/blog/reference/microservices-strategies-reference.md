# **[Pattern] Microservices Strategies: Reference Guide**

---

## **Overview**
The **Microservices Strategies** pattern decomposes a monolithic application into loosely coupled, independently deployable services. Each microservice encapsulates a specific business capability, communicates via lightweight protocols (HTTP/REST, gRPC, or messaging queues), and operates autonomously with its own data store, scaling, and deployment pipeline. This approach improves **scalability, fault isolation, team agility**, and **technology flexibility**, but introduces challenges in **service discovery, data consistency, and cross-service transactions**.

Key trade-offs include:
✅ **Pros**: Faster innovation, independent scaling, fault isolation.
❌ **Cons**: Increased operational complexity, distributed system challenges, inter-service communication overhead.

---

## **Schema Reference**

| **Category**          | **Component**               | **Description**                                                                                     | **Example Tools**                                                                 |
|-----------------------|-----------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Service Decomposition** | **Bounded Context**        | Defines a logical boundary for a microservice (e.g., "Order Processing" vs. "Payment").             | Domain-Driven Design (DDD) principles                                                 |
|                       | **Service Granularity**     | Coarse-grained (fewer but larger services) vs. fine-grained (many smaller services).              | Heuristic: 100ms rule (service response time), team alignment, shared database anti-pattern |
|                       | **API Contracts**           | Defines how services interact via requests/responses or events.                                     | OpenAPI/Swagger, Protocol Buffers, AsyncAPI                                           |
| **Communication**     | **Synchronous (REST/gRPC)**| Direct HTTP/JSON or binary (Protocol Buffers) calls.                                             | Spring Cloud, gRPC, Kubernetes Ingress                                                   |
|                       | **Asynchronous (Events)**  | Event-driven (e.g., Kafka, RabbitMQ) for decoupled workflows.                                      | Apache Kafka, NATS, AWS EventBridge                                                    |
|                       | **Service Mesh**            | Manages service-to-service communication (retries, load balancing, TLS).                          | Istio, Linkerd, Consul                                                               |
| **Data Management**   | **Database per Service**    | Each service owns its data (avoids shared schemas).                                                | PostgreSQL, MongoDB, Redis                                                             |
|                       | **Event Sourcing**          | Stores state changes as an append-only event log (CQRS pattern).                                   | EventStoreDB, Kafka Streams                                                           |
|                       | **Distributed Transactions**| Patterns like Saga or 2PC for cross-service ACID guarantees.                                       | Saga Orchestrator (Camunda), TCC (Two-Phase Commit)                                  |
| **Deployment**        | **Containerization**        | Services packaged as Docker containers for consistency.                                           | Docker, Podman                                                                     |
|                       | **Orchestration**           | Manages container lifecycles, scaling, and networking.                                            | Kubernetes, Docker Swarm, Nomad                                                          |
|                       | **CI/CD Pipelines**         | Independent deployments for each service.                                                         | GitLab CI, Jenkins, ArgoCD                                                             |
| **Discovery & Resilience** | **Service Registry**     | Dynamically discovers service instances (e.g., Eureka, Consul).                                   | Eureka, Consul, Kubernetes Service Discovery                                           |
|                       | **Circuit Breakers**        | Prevents cascading failures (e.g., Hystrix, Resilience4j).                                       | Resilience4j, Spring Cloud Circuit Breaker                                             |
|                       | **Retries & Timeouts**      | Configures retry logic and failsafes for transient failures.                                      | Spring Retry, gRPC Deadline                                                           |
| **Observability**     | **Logging**                 | Centralized logs (e.g., ELK Stack, Loki).                                                         | ELK Stack, Loki, Datadog                                                              |
|                       | **Metrics**                 | Tracks service health (e.g., Prometheus + Grafana).                                               | Prometheus, Grafana, OpenTelemetry                                                      |
|                       | **Tracing**                 | Correlates requests across services (e.g., Jaeger, Zipkin).                                      | Jaeger, Zipkin, OpenTelemetry                                                            |
| **Security**          | **API Gateways**            | Centralized authentication/authorization (e.g., OAuth2, JWT).                                    | Kong, Apigee, AWS API Gateway                                                          |
|                       | **Mutual TLS (mTLS)**       | Encrypts service-to-service communication.                                                         | Istio, Linkerd                                                                       |
|                       | **Service Mesh Policies**   | Enforces zero-trust principles (e.g., fine-grained RBAC).                                        | Istio Authorization Policies                                                           |

---

## **Implementation Details**

### **1. Service Decomposition**
- **Bounded Context**: Align services with business capabilities (e.g., `OrderService`, `InventoryService`). Use **Domain-Driven Design (DDD)** to define contexts.
- **Granularity**:
  - **Coarse-grained**: Fewer services (e.g., `UserProfileService` handling auth + profile).
  - **Fine-grained**: Many services (e.g., `AuthService`, `ProfileService`).
  - *Rule of thumb*: Start coarse, split later if scaling bottlenecks emerge.
- **API Contracts**:
  - **Synchronous**: Define REST/gRPC endpoints with OpenAPI or Protobuf schemas.
  - **Asynchronous**: Publish events (e.g., `OrderCreated`) with schemas like Avro or JSON Schema.

---
### **2. Communication Strategies**
| **Strategy**       | **Use Case**                          | **Tools/Examples**                          | **Trade-offs**                                                                 |
|--------------------|---------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------|
| **REST/HTTP**      | Simple CRUD operations.                | Spring Boot, FastAPI                        | Latency due to blocking calls, no native streaming.                           |
| **gRPC**           | High-performance internal calls.       | Protocol Buffers, Envoy Proxy               | Complex setup, binary protocol overhead.                                       |
| **Event-Driven**   | Decoupled workflows (e.g., payments). | Kafka, RabbitMQ                             | Eventual consistency, debugging complexity.                                  |
| **Service Mesh**   | Resilient, secure inter-service calls. | Istio, Linkerd                             | Operational overhead, learning curve.                                           |

**Best Practices**:
- Prefer **asynchronous** for non-critical workflows (e.g., notifications).
- Use **synchronous** for real-time requests (e.g., payments).
- **Avoid chatty services**: Batch requests or use CQRS for read-heavy workloads.

---
### **3. Data Management**
- **Database per Service**: Isolate data to prevent tight coupling. Use polyglot persistence (e.g., PostgreSQL for transactions, Redis for caching).
- **Event Sourcing**: Store state changes as immutable events (e.g., `OrderPlaced`, `OrderCancelled`).
  - *Tools*: [EventStoreDB](https://www.eventstore.com/), Kafka Streams.
- **Distributed Transactions**:
  - **Saga Pattern**: Choreography or orchestration for long-running workflows.
    - *Example*: `OrderService` → `PaymentService` → `InventoryService` via compensating transactions.
  - **Two-Phase Commit (2PC)**: Rarely used due to complexity; prefer Sagas.

---
### **4. Deployment**
- **Containerization**: Use Docker + Kubernetes for consistency.
  - *Example*: `docker-compose.yml` for local dev, `Deployment` YAML for Kubernetes.
- **CI/CD**:
  - **Independent Pipelines**: Each service has its own pipeline (e.g., GitLab CI).
  - **Canary Deployments**: Roll out updates to a subset of users (e.g., Argo Rollouts).
- **Infrastructure as Code**: Define environments with Terraform or Pulumi.

---
### **5. Observability**
- **Logging**: Structured logs (JSON) with correlation IDs.
  - *Example*:
    ```json
    {
      "traceId": "123e4567-e89b-12d3-a456-426614174000",
      "level": "INFO",
      "message": "Order processed",
      "service": "OrderService"
    }
    ```
- **Metrics**: Track latency (P99), error rates, and throughput (e.g., Prometheus).
- **Tracing**: Instruments services with OpenTelemetry or Jaeger.
  - *Example*:
    ```bash
    # Jaeger query for a trace
    jaeger query --query=service:OrderService
    ```

---
### **6. Security**
- **API Gateways**: Centralize auth (e.g., Kong + OAuth2).
- **Service Mesh**: Enforce mTLS and fine-grained policies (e.g., Istio `DestinationRule`).
- **Secrets Management**: Use Vault or Kubernetes Secrets for credentials.

---

## **Query Examples**

### **1. Synchronous REST Call**
**Request**:
```bash
# Place an order via OrderService
curl -X POST http://orderservice:8080/orders \
  -H "Content-Type: application/json" \
  -d '{"userId": "123", "items": [{"productId": "456", "quantity": 2}]}'
```
**Response**:
```json
{
  "orderId": "789",
  "status": "CREATED",
  "events": [
    {"eventType": "ORDER_CREATED", "timestamp": "2023-10-01T12:00:00Z"}
  ]
}
```

### **2. Asynchronous Event Consumption**
**Kafka Producer (OrderService)**:
```java
// Publish OrderCreated event
producer.send(new ProducerRecord<>(
    "orders",
    new OrderCreatedEvent(orderId, userId, items)
));
```
**Consumer (InventoryService)**:
```java
@KafkaListener(topics = "orders", groupId = "inventory")
public void handleOrderCreated(OrderCreatedEvent event) {
    inventoryService.reserveStock(event.getItems());
}
```

### **3. gRPC Call**
**Protobuf Definition (`order.proto`)**:
```proto
service OrderService {
  rpc PlaceOrder (OrderRequest) returns (OrderResponse);
}
```
**Client Call**:
```go
conn, _ := grpc.Dial("orderservice:50051", grpc.WithInsecure())
client := pb.NewOrderServiceClient(conn)
resp, _ := client.PlaceOrder(ctx, &pb.OrderRequest{
    UserId: "123",
    Items:  []*pb.Item{{ProductId: "456", Quantity: 2}},
})
```

### **4. Service Mesh (Istio) Traffic Management**
**Apply a VirtualService to route traffic**:
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: orderservice
spec:
  hosts:
  - orderservice
  http:
  - route:
    - destination:
        host: orderservice
        subset: v1
    retries:
      attempts: 3
      perTryTimeout: 2s
```

---

## **Related Patterns**

| **Pattern**               | **Connection to Microservices**                                                                 | **When to Use**                                                                 |
|---------------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[CQRS](https://microservices.io/patterns/data/cqrs.html)** | Separates read (Query) and write (Command) operations for scalability.                     | High-read workloads (e.g., dashboards) or complex event sourcing.              |
| **[Saga](https://microservices.io/patterns/data/saga.html)** | Manages distributed transactions via compensating actions.                                   | Long-running workflows (e.g., travel bookings).                                 |
| **[API Gateway](https://microservices.io/patterns/application-programming-interface/gateway.html)** | Routes client requests to appropriate services.                                          | Simplifying client-facing APIs or adding cross-cutting concerns (auth, rate limiting). |
| **[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)** | Stores state changes as events for auditability.                                          | Audit trails, time-travel debugging, or audit-compliant systems.                  |
| **[Service Mesh](https://microservices.io/patterns/architecture/service-mesh.html)** | Handles service-to-service communication (retries, TLS, observability).               | Production environments with high resilience requirements.                     |
| **[Polyglot Persistence](https://microservices.io/patterns/data/polyglot-persistence.html)** | Uses multiple database technologies per service.                                         | Matching data models to service needs (e.g., SQL for transactions, NoSQL for scaling). |
| **[Strangler Fig Pattern](https://microservices.io/patterns/migration/strangler.html)**      | Gradually replaces a monolith with microservices.                                           | Migration from monolith to microservices.                                       |

---

## **Anti-Patterns to Avoid**
1. **Shared Database**: Tightly couples services; violates the microservices principle.
2. **Over-Fragmentation**: Too many services increase orchestration complexity.
3. **Synchronous Chains**: Nested HTTP calls create latency and failure cascades.
4. **Ignoring Data Consistency**: Assuming eventual consistency is always acceptable (e.g., for financial systems).
5. **No Observability**: Lack of logging/tracing makes debugging distributed failures impossible.