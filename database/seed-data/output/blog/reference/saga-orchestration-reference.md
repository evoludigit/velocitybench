---
# **[Pattern] Saga Orchestration vs. Choreography Reference Guide**

---
## **1. Overview**
Distributed transactions introduce challenges like **eventual consistency, failure handling, and coordination** across microservices. The **Saga pattern** addresses these issues by breaking transactions into smaller, locally **ACID-compliant** steps while ensuring **eventual consistency** via compensating actions.

Two primary approaches exist:
- **Saga Orchestration**: A central coordinator (orchestrator) controls workflow execution, managing data flow and compensations.
- **Saga Choreography**: Services communicate **directly via events** (pub/sub), with each service managing its own part of the transaction and compensating when needed.

This guide contrasts the two approaches, outlining **key concepts, trade-offs, implementation details, and best practices** for each.

---

## **2. Key Concepts & Schema Reference**

| **Concept**               | **Saga Orchestration**                                                                 | **Saga Choreography**                                                                 |
|---------------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Control Flow**         | Centralized orchestrator drives logic (state machine).                                 | Decentralized; services emit events to trigger next steps.                           |
| **State Management**     | Orchestrator stores transaction state (e.g., in DB or external service).              | Each service maintains **event log** for local state + compensating actions.          |
| **Communication**        | Orchestrator **calls** services via APIs (synchronous or async).                       | Services **publish/subscribe** to event streams (e.g., Kafka, RabbitMQ).             |
| **Failure Handling**     | Orchestrator **rolls back** compensating steps if failure detected.                  | Services **listen for failure events** and execute compensations independently.      |
| **Complexity**           | Lower for orchestration; higher for choreography (requires event-driven design).       | Higher coordination overhead; harder to debug due to distributed logic.             |
| **Scalability**          | Bottleneck risk if orchestrator becomes a single point of failure.                     | Horizontally scalable; no central orchestrator.                                      |
| **Fault Isolation**      | If orchestrator fails, saga may stall.                                                 | Services can proceed independently; failures are contained.                          |
| **Use Cases**            | Well-defined workflows (e.g., order processing).                                       | Loosely coupled services (e.g., payment + shipping + inventory).                     |
| **Example Tools**        | Camunda, Zeebe, Temporal.                                                              | Kafka Streams, Spring Cloud Stream, Apache Pulsar.                                   |

---

## **3. Implementation Details**

### **3.1 Saga Orchestration**
#### **How It Works**
1. **Initiation**: An orchestrator (e.g., a state machine) starts a saga.
2. **Steps**: The orchestrator **calls** services sequentially (or parallel) via APIs.
3. **Compensation**: On failure, the orchestrator **executes compensating steps** (e.g., refund payment if shipping fails).

#### **Key Components**
| Component               | Description                                                                                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **Orchestrator**        | Manages saga lifecycle (state, workflow logic). Can be in-memory (ephemeral) or persistent (database-backed).                            |
| **Business Service**    | Each service performs a local transaction (ACID-compliant) and notifies the orchestrator of success/failure.                               |
| **Compensation Handler**| Defines rollback logic (e.g., "Cancel order" if "Shipment failed").                                                                       |
| **Persistence Layer**   | Stores saga state (e.g., Redis, PostgreSQL) to survive orchestrator restarts.                                                          |

#### **Example Workflow (Order Processing)**
1. **Start Saga**: Orchestrator creates a `SagaStarted` event.
2. **Check Inventory**: Orchestrator calls `InventoryService`. If success → proceed; if failure → **compensate** (e.g., `CancelOrder`).
3. **Process Payment**: Orchestrator calls `PaymentService`. If success → proceed; if failure → **compensate** (e.g., `ReleaseInventory`).
4. **Ship Order**: Orchestrator calls `ShippingService`. If success → saga completes; if failure → **compensate** (e.g., `RefundPayment`).

---
### **3.2 Saga Choreography**
#### **How It Works**
1. **Event Publication**: A service publishes an event (e.g., `OrderCreated`).
2. **Event Consumption**: Other services **asynchronously** consume the event and:
   - Perform their local transaction (e.g., `ReserveInventory`).
   - Publish their own events (e.g., `InventoryReserved`).
3. **Compensation**: If a downstream step fails, a service publishes a **compensation event** (e.g., `InventoryReleased`).

#### **Key Components**
| Component               | Description                                                                                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **Event Bus**           | Distributed messaging system (e.g., Kafka, RabbitMQ) for event propagation.                                                          |
| **Event Sourcing**      | Services maintain an **event log** to reconstruct saga state.                                                                             |
| **Compensating Actions**| Each service defines compensations (e.g., "Release inventory" if payment fails).                                                      |
| **Event Filters**       | Services subscribe to **specific events** they care about (e.g., `PaymentFailed`).                                                     |

#### **Example Workflow (Order Processing)**
1. **Order Service** publishes `OrderCreated`.
2. **Inventory Service** consumes `OrderCreated` → reserves items → publishes `InventoryReserved`.
3. **Payment Service** consumes `InventoryReserved` → processes payment → publishes `PaymentCompleted`.
4. **Shipping Service** consumes `PaymentCompleted` → ships order → publishes `OrderShipped`.
   - **Failure Case**: If `ShippingService` fails, it publishes `OrderShippingFailed`, triggering:
     - `PaymentService` → publishes `PaymentRefunded`.
     - `InventoryService` → publishes `InventoryReleased`.

---

## **4. Query Examples**
### **4.1 Orchestration (State Query Example)**
**Scenario**: Check the current state of a saga (e.g., "Is payment processed?").
**Query** (Pseudocode - using a saga DB):
```sql
SELECT status, last_step FROM sagas
WHERE saga_id = 'order_12345';
```
**Expected Output**:
```json
{
  "saga_id": "order_12345",
  "status": "IN_PROGRESS",
  "last_step": "PAYMENT_PROCESSED",
  "next_step": "SHIP_ORDER"
}
```

---
### **4.2 Choreography (Event Log Query Example)**
**Scenario**: Reconstruct the saga flow for debugging.
**Query** (using an event log in Kafka):
```bash
# List events for saga 'order_12345'
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic order_events \
  --filter "saga_id = 'order_12345'" \
  --from-beginning
```
**Expected Output**:
```
{
  "saga_id": "order_12345",
  "event": "OrderCreated",
  "timestamp": "2023-10-01T12:00:00Z"
}
{
  "saga_id": "order_12345",
  "event": "InventoryReserved",
  "timestamp": "2023-10-01T12:00:05Z"
}
{
  "saga_id": "order_12345",
  "event": "PaymentCompleted",
  "timestamp": "2023-10-01T12:00:10Z"
}
```

---

## **5. Trade-offs & Best Practices**

| **Aspect**               | **Saga Orchestration**                                                                 | **Saga Choreography**                                                                 |
|--------------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Complexity**           | Lower (centralized control).                                                          | Higher (event-driven design).                                                        |
| **Performance**          | Synchronous calls may introduce latency.                                               | Asynchronous; better for high-throughput systems.                                    |
| **Scalability**          | Limited by orchestrator (risk of bottleneck).                                         | Horizontally scalable; no single point of failure.                                   |
| **Debugging**            | Easier (single workflow).                                                              | Harder (distributed tracing required).                                               |
| **Fault Tolerance**      | Orchestrator failure → saga may stall.                                                | Services continue independently; failures are localized.                               |
| **When to Use**          | Well-defined, linear workflows (e.g., e-commerce orders).                             | Loosely coupled services (e.g., event-driven supply chains).                          |

---
### **5.1 Best Practices**
#### **For Orchestration**
- **Use a persistent orchestrator** (e.g., database-backed state machine) to survive failures.
- **Implement timeouts** for service calls to avoid deadlocks.
- **Log all saga steps** for auditability.
- **Minimize orchestration logic** in services; keep them stateless.

#### **For Choreography**
- **Design events carefully**: Use a schema registry (e.g., Avro, Protobuf) for backward compatibility.
- **Idempotency**: Ensure services can handle duplicate events (e.g., via `event_id` deduplication).
- **Eventual consistency**: Accept minor inconsistencies; use **saga completion events** to mark success.
- **Monitor event streams**: Use tools like **Kafka Lag Exporter** to detect bottlenecks.

---

## **6. Related Patterns**
| Pattern                  | Description                                                                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **Event Sourcing**       | Stores state changes as an **append-only event log**; complements choreography.                                                |
| **Command Query Responsibility Segregation (CQRS)** | Separates read (queries) and write (commands) models; useful with sagas for performance.    |
| **Idempotent Receiver**  | Ensures duplicate events don’t cause side effects (critical for choreography).                                                   |
| **Circuit Breaker**      | Protects services from cascading failures (e.g., Hystrix, Resilience4j).                                                           |
| **Saga Timeout**         | Automatically compensates if a saga steps times out (e.g., "Cancel order after 24h").                                            |
| **Distributed Locks**    | Prevents concurrent saga execution (e.g., Redis locks).                                                                              |

---
## **7. Tools & Frameworks**
| Approach          | Recommended Tools                                                                               |
|-------------------|------------------------------------------------------------------------------------------------|
| **Orchestration** | Camunda (workflow engine), Zeebe (lightweight orchestrator), Temporal (serverless workflows).  |
| **Choreography**  | Apache Kafka, RabbitMQ (event buses), Spring Cloud Stream, AWS EventBridge.                     |
| **Event Sourcing**| EventStoreDB, Apache Kafka Streams, Axon Framework.                                             |
| **Persistence**   | PostgreSQL (saga state), Redis (caching), DynamoDB (scalable key-value).                       |

---
## **8. Anti-Patterns to Avoid**
1. **Long-Running Sagas**: Avoid sagas that take hours/days (use **saga timeouts** or **human approvals**).
2. **Overly Complex Orchestration**: Don’t replicate business logic in the orchestrator; keep it simple.
3. **Ignoring Event Ordering**: In choreography, **out-of-order events** can cause issues; use **sequence IDs**.
4. **No Compensation Strategy**: Always define **how to undo** a saga step.
5. **Tight Coupling in Choreography**: Avoid direct API calls between services; use **events only**.

---
## **9. Example Code Snippets**
### **Orchestration (Zeeabe - Pseudocode)**
```javascript
// Pseudocode for Zeebe workflow
defineWorkflow("OrderProcessing") {
  start {
    emitEvent("OrderCreated", { orderId: "123" });
  }
  step("CheckInventory", (ctx) => {
    const inventory = await callService("InventoryService.checkStock", ctx.orderId);
    if (!inventory.available) {
      compensate("CancelOrder"); // Rollback step
    }
  });
  step("ProcessPayment", (ctx) => {
    await callService("PaymentService.charge", ctx.orderId, ctx.amount);
  });
  step("ShipOrder", (ctx) => {
    await callService("ShippingService.ship", ctx.orderId);
  });
}
```

### **Choreography (Kafka - Java)**
```java
// InventoryService consumes OrderCreated and publishes InventoryReserved
@KafkaListener(topics = "order_events")
public void handleOrderCreated(OrderCreatedEvent event) {
    if (reserveInventory(event.getOrderId())) {
        producer.send(
            "order_events",
            new InventoryReservedEvent(event.getOrderId(), event.getProductId())
        );
    }
}

// PaymentService compensates on failure
@KafkaListener(topics = "order_events")
public void handlePaymentFailed(PaymentFailedEvent event) {
    releaseInventory(event.getOrderId());
    producer.send(
        "order_events",
        new InventoryReleasedEvent(event.getOrderId(), event.getProductId())
    );
}
```

---
## **10. Further Reading**
- **Books**:
  - *Patterns of Enterprise Application Architecture* – Martin Fowler (Saga pattern).
  - *Designing Data-Intensive Applications* – Martin Kleppmann (eventual consistency).
- **Papers**:
  - [Saga Pattern in Practice](https://martinfowler.com/articles/patterns-of-distributed-systems/sagas.html) (Martin Fowler).
- **Tools**:
  - [Camunda Docs](https://docs.camunda.org/)
  - [Zeebe Tutorials](https://docs.zeebe.io/)

---
**Last Updated**: [Insert Date]
**Feedback**: [Contact for updates]