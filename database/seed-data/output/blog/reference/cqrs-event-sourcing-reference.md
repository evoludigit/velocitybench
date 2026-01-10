# **[Pattern] CQRS & Event Sourcing Reference Guide**

---

## **Overview**
**CQRS (Command Query Responsibility Segregation) and Event Sourcing** are architectural patterns that decouple read and write operations while storing system state as a sequence of immutable events. This guide covers their core concepts, implementation trade-offs, and best practices.

### **Key Benefits**
- **Separation of Concerns**: Read and write models evolve independently.
- **Auditability**: Every state change is captured as an immutable event.
- **Scalability**: Reads and writes can scale independently.
- **Time Travel**: Replay events to reconstruct past states.

### **When to Use**
✅ Microservices with high write/read divergence
✅ Systems requiring strict audit trails (e.g., finance, healthcare)
✅ Temporal queries (e.g., "Show all orders between 2023-01-01 and 2023-01-31")
❌ Simple CRUD applications (overkill for trivial state)

---

## **Core Concepts**

| **Term**               | **Definition**                                                                                     | **Example**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Command**            | An operation that changes system state (e.g., `CreateOrder`, `CancelOrder`).                     | `{"action": "place_order", "customer_id": "123", "amount": 50.00}`         |
| **Query**              | A read-only operation that retrieves state (e.g., `GetOrderStatus`, `GetCustomerHistory`).       | `SELECT * FROM Orders WHERE customer_id = 123 AND status = 'completed'`    |
| **Event**              | Immutable record of an occurrence (e.g., `OrderCreated`, `PaymentFailed`).                      | `{                           "id": "evt-1001",                           "type": "OrderCreated",                           "timestamp": "2023-01-01T12:00:00Z",                           "payload": { "order_id": "ord-1001", "customer_id": "123" }               }` |
| **Event Store**        | Persistent log of all events (e.g., MongoDB, DynamoDB, or custom storage).                     | `/events/{customer_id}`                                                   |
| **Projection**         | Derived data structure (e.g., SQL tables, caches) rebuilt from events.                          | `Orders` table updated via `OrderCreated`/`OrderCancelled` events          |
| **Domain Event**       | Business-specific event (e.g., `InvoiceGenerated`, `ShipmentDelivered`).                         | `{ "type": "InvoiceGenerated", "invoice_id": "inv-456", "amount": 75.50 }` |
| **Snapshot**           | Optimized state representation of a sequence of events.                                           | `{ "state": { "order_status": "completed", "last_event_id": "evt-2000" }`} |
| **Event Bus**          | Mediates event distribution (e.g., Kafka, RabbitMQ).                                            | `OrderCreated → EventBus → PricingService`                                  |

---

## **Schema Reference**
### **1. Event Structure**
```json
{
  "id": "string (UUID)",
  "type": "EventType",  // e.g., "OrderCreated", "PaymentRefunded"
  "timestamp": "ISO 8601 date-time",
  "metadata": {          // Optional: non-payload metadata
    "source_system": "string",
    "version": "string"
  },
  "payload": {           // Domain-specific data
    "field1": "value1",
    "field2": "value2"
  }
}
```

### **2. Command Structure**
```json
{
  "command_id": "string (UUID)",
  "type": "CommandType",  // e.g., "PlaceOrder", "CancelOrder"
  "timestamp": "ISO 8601 date-time",
  "payload": {
    "customer_id": "string",
    "order_items": [{"product_id": "string", "quantity": "number"}]
  }
}
```

### **3. Projection Schema (Example: SQL)**
```sql
CREATE TABLE orders (
  order_id VARCHAR(36) PRIMARY KEY,
  status VARCHAR(50),  -- Derived from event sequence
  total_amount DECIMAL(10, 2),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE customer_order_history (
  history_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  customer_id VARCHAR(36),
  order_id VARCHAR(36),
  event_type VARCHAR(100),
  event_timestamp TIMESTAMP,
  metadata JSON
);
```

---

## **Implementation Workflow**
### **1. Write Path (Command Handling)**
1. **Client** sends a command (e.g., `PlaceOrder`).
2. **Command Handler** validates and dispatches to **Domain Service**.
3. **Domain Service** publishes **domain events** (e.g., `OrderCreated`).
4. **Event Store** persists events and triggers projections.
5. **Projections** update read models (e.g., SQL tables, caches).

**Example (Pseudocode):**
```javascript
// Command Handler
async handlePlaceOrder(command) {
  const order = new Order(command.payload);
  order.place();  // Triggers Domain Events
  eventBus.publish(order.publishedEvents);
}
```

### **2. Read Path (Query Handling)**
1. **Client** sends a query (e.g., `GetOrderStatus`).
2. **Query Handler** reads from optimized projections (e.g., SQL, Redis).
3. **Projection** may be stale (eventual consistency) but eventually accurate.

**Example Query:**
```sql
-- Get orders for a customer (projection)
SELECT * FROM orders
WHERE customer_id = '123'
AND status IN ('completed', 'cancelled');
```

---

## **Query Examples**
### **1. Temporal Query (Event Sourced)**
```sql
-- Find all events for an order between two timestamps
SELECT * FROM order_events
WHERE order_id = 'ord-1001'
AND timestamp >= '2023-01-01'
AND timestamp <= '2023-01-31'
ORDER BY timestamp ASC;
```

### **2. Aggregate State Reconstruction**
```javascript
// Replay events to build current state
function getOrderState(orderId) {
  const events = eventStore.getEventsFor(orderId);
  let currentState = { status: 'draft' };

  events.forEach(event => {
    switch (event.type) {
      case 'OrderCreated': currentState.status = 'created'; break;
      case 'OrderPaid': currentState.status = 'paid'; break;
      case 'OrderCancelled': currentState.status = 'cancelled'; break;
    }
  });

  return currentState;
}
```

### **3. Projection Query (Optimized Read)**
```sql
-- Get customer's latest order (materialized view)
SELECT
  o.order_id,
  o.status,
  o.total_amount,
  MAX(e.timestamp) AS last_updated
FROM orders o
JOIN order_events e ON o.order_id = e.order_id
WHERE o.customer_id = '123'
GROUP BY o.order_id;
```

---

## **Trade-offs**
| **Aspect**          | **Pros**                                      | **Cons**                                      |
|---------------------|-----------------------------------------------|-----------------------------------------------|
| **Complexity**      | Higher setup cost                            | Better separation of concerns                 |
| **Performance**     | Read/write scaling                            | Event replay can be slow                      |
| **Maintenance**     | Harder to debug                               | Long-term data integrity guarantees           |
| **Flexibility**     | Evolve models independently                   | Requires tooling (event stores, projections)  |

---

## **Best Practices**
1. **Event Design**
   - **Atomicity**: Keep events small and focused (e.g., `OrderItemAdded` instead of `OrderSubmitted`).
   - **Immutability**: Never update an event; append new events (e.g., `OrderStatusUpdated` instead of patching `OrderCreated`).

2. **Projection Management**
   - **Incremental Updates**: Only reproject changed data (e.g., via event stream processing).
   - **Caching**: Use Redis/Memorystore for hot projections.

3. **Error Handling**
   - **Idempotency**: Design commands to be retried safely (e.g., `command_id` + deduplication).
   - **Dead Letter Queue**: Handle failed event processing.

4. **Tooling**
   - **Event Stores**: Axon Framework, EventStoreDB, or custom Kafka-backed storage.
   - **Projections**: Use stream processing (e.g., Apache Flink, Kafka Streams).

---

## **Related Patterns**
| **Pattern**               | **Relationship to CQRS/ES**                                                                 | **Example Use Case**                          |
|---------------------------|-------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Command-Query Separation** | Underpinning principle of CQRS                                                            | Separate `CreateUser` (write) and `GetUser` (read) endpoints |
| **Aggregate**             | Groups events for consistency boundaries                                                | `Order` aggregate with `OrderCreated`, `OrderPaid` events |
| **Saga**                  | Manages distributed transactions via events                                              | Cross-service workflows (e.g., `Order → Payment → Inventory`) |
| **Materialized View**     | Projection that optimizes read queries                                                   | `Customer Orders Summary` table               |
| **Eventual Consistency**  | Accepts delay in projections (e.g., 5s–1m)                                              | Shopping cart updates                          |

---

## **Anti-Patterns**
1. **Overusing Events**
   - *Problem*: Publishing 100s of events for a single operation (e.g., `CustomerNameUpdated`, `CustomerEmailUpdated`).
   - *Fix*: Batch related changes into a single event (e.g., `CustomerProfileUpdated`).

2. **Ignoring Projections**
   - *Problem*: Only querying raw events for reads (performance bottleneck).
   - *Fix*: Maintain optimized projections (e.g., SQL tables).

3. **Tight Coupling with Events**
   - *Problem*: Domain logic depends on event structure (violates separation).
   - *Fix*: Use aggregates to encapsulate behavior.

---
## **Further Reading**
- **Books**:
  - *Domain-Driven Design* (Eric Evans) – Aggregates and bounded contexts.
  - *Event-Driven Microervices Architecture* (Chris Richardson) – ES in microservices.
- **Tools**:
  - [EventStoreDB](https://www.eventstore.com/) – Event store database.
  - [Axon Framework](https://axoniq.io/) – Java event sourcing library.
- **Articles**:
  - [CQRS Patterns and Practices](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf) (Greg Young).

---
**Last Updated:** [YYYY-MM-DD] | **Version:** 1.0