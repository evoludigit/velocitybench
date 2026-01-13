# **[Distributed Patterns] Reference Guide**

---

## **Overview**
**Distributed Patterns** are architectural and design principles used to build scalable, resilient, and fault-tolerant applications across multiple nodes, machines, or cloud environments. These patterns address challenges such as latency, network partitions, data consistency, and load distribution. Common use cases include microservices, cloud-native applications, and large-scale IoT systems.

Distributed systems rely on principles like **statelessness**, **idempotency**, **retries with backoff**, and **circuit breaking** to handle failures gracefully. Key considerations include **eventual consistency**, **partition tolerance**, and **CAP theorem trade-offs** (Consistency, Availability, Partition tolerance).

---
## **Schema Reference**

| **Pattern**               | **Purpose**                                                                 | **Key Components**                                                                 | **Trade-offs**                                                                                     |
|---------------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Prevent cascading failures by stopping calls to a failing service.          | Failure threshold, recovery timeout, fallback logic.                               | False positives (blocking healthy services).                                                      |
| **Retries with Backoff**  | Handle transient failures (e.g., network blips) with exponential delays.   | Initial retry delay, max retries, jitter (randomization).                          | Increased latency if retries are not needed.                                                      |
| **Idempotency**           | Ensure repeated operations (e.g., API calls) produce the same result.        | Unique request ID, deduplication logic.                                             | Complexity in implementing deduplication.                                                        |
| **Saga**                  | Manage distributed transactions via a sequence of local transactions.       | Orchestrator or choreography model, compensating transactions.                    | Complexity in error handling and rollback.                                                         |
| **Event Sourcing**        | Store state changes as a sequence of immutable events.                       | Event store, event handlers, event bus.                                              | Higher storage requirements.                                                                    |
| **CQRS**                  | Separate read and write operations for scalability.                          | Command model (writes), query model (reads), event sourcing or snapshots.          | Increased complexity in maintaining synchronization.                                               |
| **Bulkhead**              | Isolate resources (e.g., DB connections) to prevent overload.               | Pool size limits, thread pools, isolation boundaries.                               | Resource underutilization if limits are too restrictive.                                           |
| **Rate Limiting**         | Control request volume to prevent overload.                                 | Throttling algorithms (token bucket, leaky bucket), quotas.                        | Poor user experience if limits are too aggressive.                                                 |
| **Sidecar Pattern**       | Offload tasks (e.g., auth, logging) to a companion container.               | Sidecar container, shared volume, inter-process communication.                      | Increased deployment complexity.                                                                 |
| **Leader Election**       | Select a primary node for coordinating distributed tasks.                   | Consensus algorithms (Raft, Paxos), heartbeat mechanisms.                          | Performance overhead in election and failover.                                                     |
| **Partitioning**          | Distribute data across nodes for horizontal scaling.                         | Sharding keys (e.g., hash-based), replica sets.                                     | Hotspots if key distribution is uneven.                                                          |
| **Replication**           | Duplicate data across nodes for availability and fault tolerance.             | Leader-follower model, async replication.                                           | Eventual consistency delays.                                                                       |

---

## **Implementation Details**

### **Key Concepts**
1. **Statelessness**
   - Design services to avoid storing session data; use external stores (e.g., Redis, database).
   - *Example*: Stateless APIs return tokens (JWT) for client-side state management.

2. **Idempotency**
   - Ensure repeated identical requests (e.g., `POST /order`) don’t cause duplicates.
   - *Implementation*: Use a database or cache to track request IDs.

3. **CAP Theorem**
   - Choose between **Consistency**, **Availability**, or **Partition Tolerance** based on requirements.
   - *Example*: DynamoDB prioritizes **Availability + Partition Tolerance** (eventual consistency).

4. **Eventual Consistency**
   - Allow temporary inconsistencies for scalability (e.g., Redis, Cassandra).
   - *Mitigation*: Use conflict-free replicated data types (CRDTs).

5. **Saga Pattern**
   - For distributed transactions, break into local transactions with compensating actions.
   - *Example*:
     ```plaintext
     1. Order placed → Reserve inventory (local TX).
     2. Payment processed → Ship order (local TX).
     3. If payment fails → Release inventory (compensating TX).
     ```

---

### **Best Practices**
- **Use Asynchronous Communication**: Prefer event-driven architectures (Kafka, RabbitMQ) over RPC for decoupling.
- **Monitor Distributed Tracing**: Tools like Jaeger or OpenTelemetry track requests across services.
- **Optimize Network Calls**: Batch requests, use CDNs, and cache aggressively.
- **Graceful Degradation**: Prioritize core functionality when under heavy load.

---

## **Query Examples**

### **1. Circuit Breaker (Python - `PyBreaker`)**
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

@breaker
def call_external_service():
    return requests.get("http://unhealthy-service/api").json()
```

### **2. Retries with Backoff (Java - `Resilience4j`)**
```java
RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(5)
    .waitDuration(Duration.ofSeconds(1))
    .retryExceptions(TimeoutException.class)
    .build();

Retry retry = Retry.of("retryConfig", retryConfig);
retry.executeSupplier(() -> callExternalService());
```

### **3. Idempotency Key (REST API)**
```http
POST /orders HTTP/1.1
Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000
Content-Type: application/json

{"item": "laptop", "quantity": 1}
```
*Backend validation*:
```python
if request.headers.get("Idempotency-Key") in seen_ids:
    return Response("Already processed", status=200)
seen_ids.add(request.headers["Idempotency-Key"])
```

### **4. Saga (Event-Driven Workflow)**
```plaintext
// Step 1: Place order (event: OrderCreated)
Kafka producer → topic: "orders" → message: {"orderId": "123", "status": "created"}

// Step 2: Reserve inventory (event: InventoryReserved)
Stream processor → topic: "inventory" → message: {"orderId": "123", "action": "reserve"}

// Compensating action if payment fails:
Stream processor → topic: "inventory" → message: {"orderId": "123", "action": "release"}
```

### **5. Partitioning (MongoDB Sharding)**
```javascript
// Shard by "userId" for even distribution
sh.shardCollection("users", { "userId": 1 });
```

---

## **Related Patterns**

| **Pattern**               | **Relation to Distributed Patterns**                                                                 | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Microservices**         | Distributed Patterns enable scalable, independent services.                                         | When building modular, scalable applications.                                  |
| **Chaos Engineering**     | Tests failure handling (e.g., network partitions) using distributed patterns like Circuit Breakers. | Improving resilience in production.                                           |
| **Service Mesh**          | Manages service-to-service communication (e.g., Istio, Linkerd).                                  | Complex microservice architectures.                                            |
| **Database Sharding**     | Logical partitioning of data across nodes.                                                         | High-read/write workloads.                                                      |
| **Event-Driven Architecture** | Loosely coupled services via events (e.g., Kafka, NATS).                                          | Decoupled, scalable systems.                                                     |
| **Polyglot Persistence**  | Mix of databases (SQL/NoSQL) for optimal data storage.                                             | When a single database can’t meet all requirements.                             |
| **API Gateway**           | Routes requests to microservices, handles retries/rate limiting.                                   | Uniform entry point for client requests.                                        |

---
## **Further Reading**
- [AWS Distributed Systems Reading List](https://aws.amazon.com/distributed-systems-reading-list/)
- *Designing Data-Intensive Applications* – Martin Kleppmann
- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)