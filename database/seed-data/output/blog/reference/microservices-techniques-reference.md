# **[Pattern] Microservices Techniques: Reference Guide**

---

## **Overview**
This guide outlines **Microservices Techniques**, a software architectural pattern where an application is decomposed into smaller, independent services (microservices) that communicate via lightweight mechanisms (e.g., APIs, message queues). Each service focuses on a single business capability, runs its own processes, and is developed, deployed, and scaled independently. This approach enhances agility, fault isolation, and scalability but requires careful design around **service boundaries, communication, data management, and resilience**. Techniques cover deployment, inter-service communication, API design, and observability, enabling teams to build and manage complex systems with flexibility.

---

## **Schema Reference**
| **Aspect**               | **Description**                                                                                     | **Key Considerations**                                                                                                                                                                                                 |
|--------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Service Granularity**  | Defines the size and responsibility of a microservice.                                              | - Each service should encapsulate a **single domain** (e.g., "User Management," "Order Processing").<br>- Avoid over-fragmentation (e.g., splitting into "User Login" and "User Profile" if tightly coupled).<br>- Balance based on deployment frequency and team ownership. |
| **Bounded Context**      | A conceptual boundary within which a domain model is consistent (from Domain-Driven Design).         | - Align services with **ubiquitous language** used by business domains.<br>- Use **event storming** to map workflows and identify service boundaries.<br>- Document context mappings (e.g., how `UserService` interacts with `PaymentService`). |
| **Communication**        | How services interact (synchronous vs. asynchronous).                                             | - **Synchronous (REST/gRPC):** Simple but can lead to tight coupling and latency.<br>- **Asynchronous (Event-Driven):** Decouples services via events (e.g., Kafka, RabbitMQ).<br>- **Hybrid:** Combine for resilience (e.g., synchronous for requests, async for notifications). |
| **Data Management**      | Handling databases per service vs. shared databases.                                               | - **Database per Service:** Isolates data changes but requires **eventual consistency** for distributed transactions.<br>- **Shared Database:** Avoids duplication but risks coupling.<br>- Use **CQRS** (Command Query Responsibility Segregation) for read-heavy workloads. |
| **API Design**           | Contracts for inter-service communication.                                                          | - Design APIs with **versioning**, **rate limiting**, and **authentication** (e.g., OAuth, API keys).<br>- Use **OpenAPI/Swagger** for documentation.<br>- Prefer **resource-oriented** endpoints (e.g., `/orders/{id}`). |
| **Deployment**           | Strategies for scaling and deploying microservices.                                                | - **Containerization (Docker):** Ensures consistency across environments.<br>- **Orchestration (Kubernetes):** Manages scaling, networking, and failures.<br>- **CI/CD Pipelines:** Enable independent deployment (e.g., GitHub Actions, Jenkins).<br>- **Blue-Green/Canary Deployments:** Reduce risk. |
| **Resilience**           | Handling failures in distributed systems.                                                          | - **Circuit Breakers (Hystrix, Resilience4j):** Prevent cascading failures.<br>- **Retries with Backoff:** For transient errors.<br>- **Timeouts:** Prevent long-lived requests.<br>- **Idempotency:** Ensure safe retry of operations. |
| **Observability**        | Monitoring, logging, and tracing across services.                                                  | - **Centralized Logs (e.g., ELK Stack, Loki):** Aggregate logs for debugging.<br>- **Distributed Tracing (e.g., Jaeger, OpenTelemetry):** Track requests across services.<br>- **Metrics (Prometheus):** Monitor performance (e.g., latency, error rates). |
| **Security**             | Protecting services and data.                                                                   | - **Service Mesh (Istio, Linkerd):** Handles mTLS, auth, and traffic management.<br>- **API Gateways (Kong, Apache APISIX):** Centralize auth and rate limiting.<br>- **Secrets Management (Vault):** Secure credentials.<br>- **Zero Trust:** Assume breach; verify every request. |
| **Testing**              | Ensuring reliability of individual and integrated services.                                      | - **Unit/Integration Tests:** Per service.<br>- **Contract Tests (Pact):** Verify API contracts.<br>- **Chaos Engineering (Gremlin):** Test resilience to failures.<br>- **End-to-End Tests:** Simulate user flows. |
| **Team Structure**       | Organizing teams around services.                                                                | - **Cross-Functional Teams:** Own end-to-end features (e.g., "Order Team" handles order-related services).<br>- **Shared Services:** For cross-cutting concerns (e.g., "Auth Service").<br>- **DevOps Collaboration:** Bridge dev and ops. |

---

## **Implementation Details**

### **1. Defining Service Boundaries**
- **Domain-Driven Design (DDD):** Use **bounded contexts** to group services by business capabilities. Avoid splitting services based on technology (e.g., "Java Service" and "Python Service" for the same domain).
- **Event Storming:** Map business processes to identify **events** (e.g., `OrderCreated`, `PaymentProcessed`) that trigger service interactions.
- **Anti-Corruption Layer:** Wrap legacy systems with an adapter to decouple new services.

**Example Workflow:**
1. Identify a domain (e.g., "Inventory Management").
2. Extract capabilities (e.g., "Manage Stock Levels," "Track Inventory Moves").
3. Create a service per capability (e.g., `InventoryService`).

---

### **2. Inter-Service Communication**
#### **Synchronous (REST/gRPC)**
- **Use Case:** Request-response patterns (e.g., fetching user data).
- **Tools:**
  - **REST:** Lightweight, HTTP-based (e.g., Spring Boot, Express.js).
  - **gRPC:** High-performance, binary protocol (e.g., Protocol Buffers).
- **Best Practices:**
  - Keep APIs **stateless**.
  - Use **DTOs (Data Transfer Objects)** to avoid exposing internal models.
  - Implement **CORS** if needed.

**Example REST API Endpoint:**
```http
GET /api/v1/inventory/items/{id}
Headers: Authorization: Bearer {token}
Response:
{
  "id": "123",
  "name": "Laptop",
  "quantity": 10
}
```

#### **Asynchronous (Event-Driven)**
- **Use Case:** Decoupled workflows (e.g., "Order Created" → "Send Invoice" → "Notify Customer").
- **Tools:**
  - **Event Bus (Kafka, RabbitMQ):** Publish-subscribe model.
  - **Saga Pattern:** Manage distributed transactions via a series of local transactions.
- **Best Practices:**
  - Design events as **immutable records** (e.g., `OrderCreatedEvent`).
  - Use **event sourcing** for audit trails.
  - Implement **idempotency keys** to avoid duplicate processing.

**Example Kafka Event:**
```json
{
  "eventType": "OrderCreated",
  "orderId": "456",
  "userId": "789",
  "timestamp": "2023-10-01T12:00:00Z",
  "metadata": {
    "items": [{ "productId": "1", "quantity": 2 }]
  }
}
```

---

### **3. Data Management**
#### **Database per Service**
- **Pros:** Independent scaling, easier deployments.
- **Cons:** Data duplication, eventual consistency.
- **Patterns:**
  - **CQRS:** Separate read and write models (e.g., `OrderWriteModel`, `OrderReadModel`).
  - **Event Sourcing:** Store state changes as events for replayability.

**Example Schema (PostgreSQL):**
```sql
-- Order Service Database
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(36) REFERENCES users(id),
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **Shared Database (Avoid if Possible)**
- **When to Use:** Legacy systems or read-heavy analytics.
- **Mitigation:** Use **database views** or **denormalized tables** to limit coupling.

---

### **4. Deployment Techniques**
#### **Containerization (Docker)**
- **Example `Dockerfile` for a Microservice:**
  ```dockerfile
  FROM openjdk:17-jdk-slim
  WORKDIR /app
  COPY target/my-service.jar app.jar
  ENTRYPOINT ["java", "-jar", "app.jar"]
  ```
- **Best Practices:**
  - Use **multi-stage builds** to reduce image size.
  - Tag images with **semantic versioning** (e.g., `my-service:1.0.0`).

#### **Orchestration (Kubernetes)**
- **Deployment YAML Example:**
  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: inventory-service
  spec:
    replicas: 3
    selector:
      matchLabels:
        app: inventory-service
    template:
      spec:
        containers:
        - name: inventory-service
          image: my-registry/inventory:1.1.0
          ports:
          - containerPort: 8080
  ```
- **Scaling:**
  ```sh
  kubectl scale deployment inventory-service --replicas=5
  ```

#### **CI/CD Pipeline (GitHub Actions)**
- **Example Workflow (`/.github/workflows/deploy.yml`):**
  ```yaml
  name: Deploy to Kubernetes
  on:
    push:
      branches: [ main ]
  jobs:
    deploy:
      runs-on: ubuntu-latest
      steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t my-registry/inventory:latest .
      - name: Deploy to Kubernetes
        run: kubectl apply -f k8s/deployment.yaml
  ```

---

### **5. Resilience Patterns**
- **Circuit Breaker:**
  - **Tool:** Resilience4j (Java), Hystrix (legacy).
  - **Example (Resilience4j):**
    ```java
    @CircuitBreaker(name = "inventoryService", fallbackMethod = "fallback")
    public String getItem(String itemId) {
      return restTemplate.getForObject("http://inventory-service/items/" + itemId, String.class);
    }
    public String fallback(String itemId, Exception e) {
      return "Item not available";
    }
    ```
- **Retry with Backoff:**
  - Use exponential backoff (e.g., `retry: maxAttempts=3, initialInterval=1s, multiplier=2`).
- **Bulkhead:**
  - Limit concurrent executions per service (e.g., `Bulkhead(name = "orderService", type = CONNECTION, maxConcurrentCalls = 10)`).

---

### **6. Observability**
- **Centralized Logging (ELK Stack):**
  - **Setup:** Fluentd → Elasticsearch → Kibana.
  - **Example Log:**
    ```json
    {
      "timestamp": "2023-10-01T12:00:00Z",
      "level": "ERROR",
      "service": "inventory-service",
      "message": "Failed to connect to database",
      "traceId": "abc123"
    }
    ```
- **Distributed Tracing (Jaeger):**
  - Inject spans into HTTP requests:
    ```java
    // Using OpenTelemetry
    Span span = tracer.spanBuilder("getItem").startSpan();
    try (Scope scope = span.makeCurrent()) {
      String item = inventoryClient.getItem("123");
      span.addEvent("Item retrieved");
      return item;
    } finally {
      span.end();
    }
    ```

---

### **7. Security**
- **Service Mesh (Istio):**
  - **Features:** mTLS, traffic shifting, rate limiting.
  - **Example Istio VirtualService:**
    ```yaml
    apiVersion: networking.istio.io/v1alpha3
    kind: VirtualService
    metadata:
      name: inventory-service
    spec:
      hosts:
      - inventory-service
      http:
      - route:
        - destination:
            host: inventory-service
            subset: v1
          weight: 90
        - destination:
            host: inventory-service
            subset: v2
          weight: 10
    ```
- **API Gateway (Kong):**
  - **Plugins:** JWT validation, rate limiting.
  - **Example Kong Configuration:**
    ```json
    {
      "plugins": [
        {
          "name": "key-auth",
          "config": {
            "key_names": ["api-key"]
          }
        }
      ]
    }
    ```

---

## **Query Examples**
### **1. REST API Query (Get Order)**
**Request:**
```http
GET /api/v1/orders/123
Headers:
  Authorization: Bearer {token}
  Accept: application/json
```

**Response:**
```json
{
  "orderId": "123",
  "status": "SHIPPED",
  "items": [
    {
      "productId": "1",
      "quantity": 2
    }
  ],
  "createdAt": "2023-10-01T10:00:00Z"
}
```

---

### **2. gRPC Query (List Inventory Items)**
**Protocol Buffer Definition (`inventory.proto`):**
```proto
service InventoryService {
  rpc ListItems (ListItemsRequest) returns (ListItemsResponse);
}

message ListItemsRequest {
  string category = 1;
}

message ListItemsResponse {
  repeated Item items = 1;
}

message Item {
  string id = 1;
  string name = 2;
  int32 quantity = 3;
}
```

**gRPC Client Call (Python):**
```python
import grpc
from inventory_pb2 import ListItemsRequest
from inventory_pb2_grpc import InventoryServiceStub

channel = grpc.insecure_channel("localhost:50051")
stub = InventoryServiceStub(channel)
response = stub.ListItems(ListItemsRequest(category="Electronics"))
for item in response.items:
    print(f"ID: {item.id}, Name: {item.name}")
```

---

### **3. Event-Driven Query (Kafka Consumer)**
**Consumer Code (Python):**
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'order-events',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    event = message.value
    if event['eventType'] == 'OrderCreated':
        print(f"New order: {event['orderId']}")
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Event Sourcing**        | Stores state changes as a sequence of events for replayability.                                    | When audit trails or time-travel debugging are needed.                                              |
| **CQRS**                  | Separates read and write models to improve performance.                                             | For read-heavy applications or complex queries.                                                    |
| **Saga Pattern**          | Manages distributed transactions via a series of local transactions.                               | When ACID transactions cannot span services (e.g., cross-service workflows).                        |
| **API Gateway**           | Centralizes routing, authentication, and rate limiting for services.                               | To protect services and simplify client interactions.                                              |
| **Service Mesh**          | Handles service-to-service communication (e.g., mTLS, retries).                                    | For complex, high-traffic environments with many services.                                         |
| **Strangler Pattern**     | Gradually replaces a monolith by exposing services and migrating features.                          | When migrating from a monolith to microservices incrementally.                                    |
| **BFF (Backend for Frontend)** | Dedicated API layer per client (e.g., mobile, web) to aggregate microservices.                | When different clients (e.g., mobile vs. web) need tailored responses.                               |
| **Chaos Engineering**     | Introduces failures to test resilience.                                                            | To proactively identify and fix system vulnerabilities.                                            |

---

## **Key Considerations for Adoption**
1. **Start Small:** Begin with non-critical features or new projects.
2. **Avoid Overhead:** Microservices are not always better; evaluate trade-offs (e.g., complexity vs. scalability).
3. **Invest in Tooling:** Observability, CI/CD, and service meshes add complexity but are essential.
4. **Document Boundaries:** Clearly define service contracts and ownership.
5. **Monitor Performance:** Distributed systems introduce latency; optimize iteratively.