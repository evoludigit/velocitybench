# **[Pattern] Hybrid Patterns Reference Guide**

---

## **Overview**
**Hybrid Patterns** blend attributes of multiple architectural patterns or paradigms—such as request-response, event-driven, and CQRS—to create flexible, adaptive systems that leverage the strengths of each while mitigating their individual weaknesses. This pattern is ideal for complex, distributed applications requiring **scalability**, **resilience**, and **performance optimization** across heterogeneous environments (e.g., microservices, batch processing, or real-time analytics). By strategically combining synchronous and asynchronous flows, stateful and stateless components, and event-sourcing with command-query separation, Hybrid Patterns enable granular control over system behavior. Common use cases include **multi-channel applications** (e.g., mobile + backend APIs), **hybrid transactional/analytical processing (HTAP)**, or **legacy modernization** where phase-out or refactoring isn’t feasible.

---

## **Schema Reference**
The following table outlines the core components and their interactions in Hybrid Patterns. Columns describe **purpose**, **implementation types**, **dependencies**, and **trade-offs**.

| **Component**          | **Purpose**                                                                                     | **Implementation Types**                                                                                     | **Dependencies**                          | **Trade-offs**                                                                                     |
|-------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Synchronous Core**    | Handles time-sensitive, transactional workflows (e.g., user requests, critical operations).      | REST/gRPC APIs, HTTP handlers                                                                             | Shared state, databases                   | Latency overhead; not ideal for high-throughput async workloads.                                  |
| **Asynchronous Layer**  | Decouples long-running or background tasks (e.g., notifications, aggregations, event processing). | Message brokers (Kafka, RabbitMQ), event streams                                                           | Event stores, sinks/queues                 | Eventual consistency; requires idempotency and retry mechanisms.                                |
| **Command Layer**       | Emits domain events or updates state in response to user actions (CQRS).                          | Command handlers, event publishers (e.g., Axon, EventStoreDB)                                               | Persistent event logs                      | Complexity in recovery; needs event sourcing for auditability.                                   |
| **Query Layer**         | Serves read-heavy queries via optimized data structures (e.g., materialized views, caches).      | Read models (SQL views, Redis, Elasticsearch), query APIs                                                      | Synchronous core, event processor          | Stale data if not synchronized with command layer.                                               |
| **Hybrid Sync/Async**   | Combines both flows via adapters (e.g., async-to-sync bridges for real-time updates).            | Event-driven APIs (e.g., WebSockets), polling with event triggers                                             | Both synchronous and async layers         | Overhead from sync/async coordination; requires careful partition management.                     |
| **State Management**    | Balances consistency guarantees (e.g., transactions for sync, eventual consistency for async).   | Distributed transactions (Saga pattern), CRDTs, or optimistic concurrency                                     | Database transactions, distributed locks | Sacrifices simplicity for scalability; complexity in failure scenarios.                         |
| **Resilience Layer**    | Ensures fault tolerance via retries, circuit breakers, or fallback mechanisms.                   | Polly (retries), Hystrix (circuit breakers), or custom async timeouts                                         | Observability tools (Prometheus, OpenTelemetry) | Increased latency during failures; requires monitoring.                                         |

---

## **Implementation Details**

### **Key Concepts**
1. **Seamless Orchestration**
   - Use **mediators** (e.g., a lightweight service) to translate between sync/async boundaries. Example: A REST API (synchronous) forwards a request to an async processor (Kafka) for background tasks.
   - **Anti-pattern:** Avoid deep nesting of sync/async calls (e.g., async callbacks inside synchronous loops).

2. **Event-Driven Extensions**
   - **Outbox Pattern:** Queue command events (e.g., via SQL `pending_events` table) to ensure durability before publishing to a broker.
   - **Event Sourcing:** Store state changes as immutable events; replay events to rebuild state if needed.

3. **Query/Command Separation (CQRS)**
   - **Commands:** Modify state (e.g., `CreateOrder`).
   - **Queries:** Read state (e.g., `GetOrderStatus`).
   - **Implementation:** Use separate DDD-style aggregates for each.

4. **Hybrid Persistence**
   - **Synchronous:** ACID-compliant databases (PostgreSQL, MongoDB).
   - **Asynchronous:** Event logs (Kafka, EventStoreDB) or append-only stores.

5. **Observability**
   - Trace sync/async interactions with **distributed tracing** (e.g., OpenTelemetry). Example: Tag requests with a correlation ID to track from API to async processor.

---

### **Implementation Steps**
1. **Design the Hybrid Flow**
   - Map user interactions to **synchronous** (e.g., login) or **asynchronous** (e.g., analytics) paths.
   - Example:
     ```mermaid
     graph TD
       A[User Request: CreateOrder] --> B[Sync: Validate Order]
       B --> C{Order Valid?}
       C -->|Yes| D[Async: Process Payment]
       C -->|No| E[Sync: Reject Order]
       D --> F[Publish OrderCreated Event]
       F --> G[Async: Notify Merchant]
       F --> H[Async: Update Inventory]
     ```

2. **Infrastructure Setup**
   - **Sync Layer:** Deploy API gateway (e.g., Kong, AWS ALB) with load balancing.
   - **Async Layer:**
     - Broker: Kafka (for high throughput) or RabbitMQ (for simplicity).
     - Processing: Stream processors (e.g., Flink, Spark) or serverless (AWS Lambda).
   - **State:** Use a database with **multi-model support** (e.g., CockroachDB) or separate stores (SQL for sync, NoSQL for async).

3. **Code Implementation**
   - **Sync Example (Go/Python):**
     ```python
     # FastAPI (sync) + async worker
     from fastapi import FastAPI
     from concurrent.futures import ThreadPoolExecutor

     app = FastAPI()
     executor = ThreadPoolExecutor(max_workers=10)

     @app.post("/order")
     async def create_order(order: dict):
         # Sync validation
         if not validate_order(order):
             return {"error": "Invalid"}
         # Async task submission
         executor.submit(process_order_async, order)
         return {"status": "Queued"}
     ```
   - **Async Example (Kafka Consumer):**
     ```java
     // Kafka consumer processing events
     public class OrderProcessor {
         @KafkaListener(topics = "orders")
         public void handle(OrderEvent event) {
             // Async logic: update inventory, send email, etc.
             inventoryService.update(event.getId());
             emailService.send(event.getCustomer());
         }
     }
     ```

4. **Testing**
   - **Sync:** Unit tests for handlers; integration tests for API calls.
   - **Async:** Test event sourcing with `EventStoreDB` or Kafka replay.
   - **Hybrid:** End-to-end tests with tools like **Pact** (contract testing) or **Postman** for sync/async flows.

5. **Monitoring**
   - **Metrics:** Track:
     - Sync: Latency (p99), error rates.
     - Async: Event lag, consumer lag, processing time.
   - **Alerts:** Set up alerts for:
     - Kafka consumer lag > 1 minute.
     - Sync API failures > 5%.
   - **Tools:** Prometheus + Grafana, Datadog, or AWS CloudWatch.

---

## **Query Examples**
### **1. Hybrid Sync/Async Workflow (API + Kafka)**
**Scenario:** A user submits a form; the server validates it sync and queues async processing.

```sql
-- Sync step: Validate form in database
INSERT INTO pending_forms (user_id, data, status)
VALUES (123, '{"name":"John"}', 'validating')
ON CONFLICT (user_id) DO UPDATE SET status = 'validating';

-- Async step: Kafka producer publishes event
PRODUCE TO 'form_events' {
  KEY: 123,
  VALUE: '{"type": "form_submitted", "payload": {...}}'
}
```

**Query to Check Status:**
```sql
-- Sync read (optimistic)
SELECT status FROM pending_forms WHERE user_id = 123;
```

---

### **2. CQRS with Event Sourcing**
**Command (Sync):**
```http
POST /orders
{
  "product_id": "101",
  "quantity": 2
}
```
**Event Published (Async):**
```json
{
  "eventId": "e123",
  "type": "OrderCreated",
  "timestamp": "2023-10-01T12:00:00Z",
  "data": {"orderId": "o456", "productId": "101", "quantity": 2}
}
```
**Projection (Query Layer):**
```javascript
// Materialized view update (e.g., in Redis)
await redis.hset(`order:${orderId}`,
  "status", "processed",
  "products", '[{"id": "101", "qty": 2}]'
);
```
**Query:**
```sql
-- Read from projection (optimized for speed)
SELECT * FROM orders_projection WHERE order_id = 'o456';
```

---

### **3. Saga Pattern for Distributed Transactions**
**Scenario:** Transfer money between accounts (async).

1. **Sync Start:**
   ```java
   // Debit account (sync)
   accountService.debit("acc1", 100);
   ```
2. **Async Compensating Transaction:**
   ```json
   // Publish DebitEvent
   {"type": "DebitEvent", "account": "acc1", "amount": 100}
   ```
   ```java
   // Credit account (async)
   @KafkaListener(topics = "debit_events")
   public void handle(DebitEvent event) {
       accountService.credit("acc2", 100);
   }
   ```
3. **Fallback (if debit fails):**
   ```java
   // Compensating transaction (credit acc1 back)
   @Transactional
   public void compensate(DebitEvent event) {
       accountService.credit("acc1", 100);
   }
   ```

---

## **Related Patterns**
| **Pattern**               | **Relation to Hybrid Patterns**                                                                                     | **When to Use Together**                                                                                     |
|---------------------------|--------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **CQRS**                  | Hybrid Patterns often implement CQRS by separating sync commands (write) and async queries (read).                | When read/write models grow divergent or require performance optimization.                                  |
| **Event Sourcing**        | Asynchronous layers in Hybrid Patterns frequently use event sourcing for auditability and replayability.           | For systems needing full state reconstruction or compliance audits.                                        |
| **Saga Pattern**          | Used within async layers to manage distributed transactions across services.                                    | When synchronous transactions span multiple services (e.g., microservices orchestration).                  |
| **Outbox Pattern**        | Ensures async events are reliably published from synchronous transitions.                                       | When durability of async events is critical (e.g., financial systems).                                    |
| **Circuit Breaker**       | Resilience layer in Hybrid Patterns protects against async failures (e.g., Kafka broker downtime).               | To prevent cascading failures in hybrid architectures.                                                   |
| **API Gateway**           | Sync layer in Hybrid Patterns often routes to backend services via an API gateway.                              | For centralized request routing, rate limiting, and load balancing.                                        |
| **Serverless (Async)**    | Async layers can offload processing to serverless functions (e.g., AWS Lambda, Azure Functions).                 | For cost-effective, scalable background tasks with event triggers.                                          |
| **Materialized Views**    | Query layer in Hybrid Patterns often uses materialized views for fast reads.                                   | When OLTP queries need OLAP performance (e.g., real-time dashboards).                                     |

---

## **Anti-Patterns & Pitfalls**
1. **Over-Asynching**
   - **Problem:** Using async for everything leads to **debugging nightmares** (e.g., tracking a request through 10 async hops).
   - **Fix:** Keep synchronous paths for user-facing, latency-sensitive operations.

2. **Ignoring Event Order**
   - **Problem:** Event-driven systems may process events out of order, causing inconsistencies.
   - **Fix:** Use **exactly-once processing** (e.g., Kafka’s idempotent producers) and **transactional outbox**.

3. **Tight Coupling Between Layers**
   - **Problem:** Direct dependencies between sync/async layers reduce flexibility.
   - **Fix:** Use **adapters** (e.g., event bus) and **polyglot persistence**.

4. **No Fallback for Sync Failures**
   - **Problem:** If async processing fails but sync doesn’t retry, data is lost.
   - **Fix:** Implement **dead-letter queues** and **compensating transactions**.

5. **Underestimating Observability Costs**
   - **Problem:** Hybrid systems require **distributed tracing** and **metrics** for both sync/async paths.
   - **Fix:** Invest in tools like **Jaeger** (tracing) and **Prometheus** early.

---
**Key Takeaway:** Hybrid Patterns thrive when **synchronous critical paths** are optimized for users and **asynchronous extensions** handle scalability. Start small—prioritize clear boundaries between layers, and monitor aggressively.