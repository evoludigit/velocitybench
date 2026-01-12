# **Debugging *Consistency Setup* Pattern: A Troubleshooting Guide**
*(Event Sourcing, CQRS, and Saga-Based Systems)*

## **Introduction**
The **Consistency Setup** pattern ensures that distributed systems maintain correctness across multiple services, databases, or event streams. Common implementations include **event sourcing, CQRS, sagas (Choreography vs. Orchestration), and eventual consistency resolutions**.

This guide focuses on debugging consistency-related issues in distributed systems, particularly when:
- Events are lost or duplicated.
- State mismatches occur between services.
- Transactions fail or time out.
- Saga workflows deadlock or stall.

---

## **1. Symptom Checklist**
| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| ✅ Missing Events                    | A service expects an event but doesn’t receive it (e.g., `OrderShipped` not fired). |
| ✅ Duplicate Events                  | An event is processed multiple times (e.g., due to retries or dead-letter queues). |
| ✅ State Inconsistency               | A service’s view differs from another (e.g., inventory says 10 items, but DB has 5). |
| ✅ Deadlock in Saga                   | A saga waits indefinitely on a compensating transaction that never completes. |
| ✅ Timeout Errors                    | Long-running transactions or sagas exceeding configured timeouts.              |
| ✅ Duplicate Transactions            | Orders placed twice without proper idempotency handling.                       |
| ✅ Event Ordering Issues             | Events arrive out of sequence (common in asynchronous systems).                |
| ✅ Unhandled Exception in Saga        | A compensating action fails silently, leaving the system in an invalid state.   |

---

## **2. Common Issues & Fixes**

### **2.1 Event Duplication (Lost or Duplicate Events)**
**Symptom:** Events are processed multiple times or skipped entirely.

#### **Root Causes:**
- **Retries without deduplication** (e.g., Kafka consumer retries same event).
- **Faulty event sourcing** (event not stored correctly).
- **Network issues** (messages lost in transit).
- **Missing event IDs** (causing reprocessing).

#### **Debugging Steps:**
1. **Check Event Store:**
   ```bash
   # Example: Query event store for duplicates
   SELECT COUNT(*), event_id FROM events GROUP BY event_id HAVING COUNT(*) > 1;
   ```
   - **Fix:** Ensure events have unique IDs and use **idempotency keys** (e.g., `OrderId + EventType`).

2. **Log Event Processing:**
   ```java
   // Example: Track processed events in a map
   private final Map<String, Boolean> processedEvents = new ConcurrentHashMap<>();

   @Override
   public void handleEvent(OrderProcessedEvent event) {
       if (processedEvents.containsKey(event.getOrderId())) {
           log.warn("Duplicate event for order: {}", event.getOrderId());
           return;
       }
       processedEvents.put(event.getOrderId(), true);
       // Process the event
   }
   ```

3. **Use Dead-Letter Queues (DLQ):**
   - Configure a DLQ for failed/duplicate events in Kafka/RabbitMQ.
   - Example (Kafka):
     ```bash
     kafka-topics --create --topic orders-dlq --partitions 3 --replication-factor 1
     ```

4. **Implement Event Sourcing Safely:**
   ```python
   # Example: Append-only event store (Python/SQL)
   def store_event(order_id, event_type, payload):
       with transaction:
           append_event(order_id, event_type, payload)
           if not valid_event(event_type, payload):  # Prevent bad state
               raise ValueError("Invalid event")
   ```

---

### **2.2 State Inconsistency (CQRS Mismatch)**
**Symptom:** A read view (e.g., `CustomerView`) differs from the event log.

#### **Root Causes:**
- **Event not replayed** during projection rebuild.
- **Projection error** (e.g., race condition in DB update).
- **Missing event** in the event log.

#### **Debugging Steps:**
1. **Compare Event Log & Projection:**
   ```sql
   -- Check if all events were applied to the projection
   SELECT COUNT(*) as events_applied, COUNT(DISTINCT order_id) as unique_orders
   FROM events
   JOIN projections ON projections.order_id = events.order_id
   WHERE events.event_type = 'OrderShipped';
   ```
   - **Fix:** Replay events from the store if projections are stale.

2. **Use Event Versioning:**
   ```java
   // Ensure projections match the latest event
   public void rebuildProjection(OrderId orderId) {
       Projection projection = projections.get(orderId);
       EventStore store = new EventStore();

       // Rebuild from scratch
       store.getEventsAfter(orderId, 0L)
            .forEach(event -> projection.applyEvent(event));
   }
   ```

3. **Idempotent Projections:**
   - If reprocessing is needed, ensure projections handle duplicates:
   ```python
   def apply_order_shipped(event):
       with db_session:
           projection = db.query(Projection).filter_by(order_id=event.order_id).first()
           if not projection:
               projection = Projection(order_id=event.order_id, status="SHIPPED")
           elif projection.status != "SHIPPED":
               log.warn("Projection out of sync for order: {}", event.order_id)
           db.add(projection)
   ```

---

### **2.3 Saga Deadlocks (Orchestration Issue)**
**Symptom:** A saga waits indefinitely on a compensating transaction.

#### **Root Causes:**
- **Ordering problem** (e.g., `ShipOrder` compensates before `PayOrder` completes).
- **External service unavailable** (e.g., payment service down).
- **No timeout/retries** on compensating actions.

#### **Debugging Steps:**
1. **Visualize Saga Flow:**
   ```mermaid
   graph TD
       A[Start Order] --> B[Pay Order]
       B --> C[Check Inventory]
       C --> D[Ship Order]
       D -->|Error| E[Compensate Pay]
       E --> F[Compensate Ship]
   ```
   - **Fix:** Ensure steps are **declarative** and **time-bound**.

2. **Add Timeouts & Retries:**
   ```java
   // Example: Saga with retries (Spring Retry)
   @Retryable(maxAttempts = 3)
   public void payOrder(Order order) {
       paymentService.charge(order.getAmount());
   }

   @Recover
   public void recover(Order order, Exception e) {
       // Compensate
       paymentService.refund(order.getAmount());
   }
   ```

3. **Check Compensating Logic:**
   - Ensure compensations are **retryable** and **idempotent**:
   ```python
   def compensate_payment(order_id):
       try:
           payment_service.refund(order_id)
       except:
           log.error("Failed to compensate payment for %s", order_id)
           # Retry or notify ops
   ```

4. **Deadline Tracking:**
   - Use **Temporal/AWS Step Functions** to set deadlines:
   ```bash
   # Example: Temporal deadline for saga steps
   saga = workflow.get_current_activity_stub()
   saga.execute("PayOrder", deadline=300)  # 5 minutes
   ```

---

### **2.4 Event Ordering Issues**
**Symptom:** Events arrive out of sequence (e.g., `PaymentConfirmed` after `OrderShipped`).

#### **Root Causes:**
- **Asynchronous processing** (events not batched).
- **Network latency** (events reordered).
- **No total order guarantee** (e.g., Kafka partitions).

#### **Debugging Steps:**
1. **Use Event Sequencing:**
   ```java
   // Example: Sequential event IDs
   public class OrderService {
       private AtomicLong nextEventId = new AtomicLong(0);

       public void placeOrder(Order order) {
           long eventId = nextEventId.incrementAndGet();
           eventStore.append(new Event(orderId, eventId, "OrderPlaced"));
       }
   }
   ```

2. **Batch Events with Durability:**
   ```bash
   # Kafka: Ensure in-order delivery per partition
   kafka-console-producer --topic orders --broker localhost:9092 --property partition.key=order_id
   ```

3. **Replay Events in Order:**
   - If order matters (e.g., payments), enforce sequence:
   ```python
   def process_events():
       events = event_store.get_events_since(last_processed_id)
       events.sort(key=lambda e: e.sequence_id)  # Ensure sequential
       for event in events:
           if event.sequence_id <= last_processed_id:
               continue
           apply_event(event)
   ```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**               | **Use Case**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| **Event Store Debugger**         | Replay events to check for gaps/duplicates (e.g., `EventStoreDB CLI`).    |
| **Distributed Tracing** (Jaeger) | Track saga flow across services (e.g., payment → shipping → inventory).      |
| **Dead-Letter Queue (DLQ)**       | Inspect failed events (Kafka/RabbitMQ DLQ).                                |
| **Database Corruption Check**    | Run `CHECK TABLE` (MySQL) or `pg_checksums` (PostgreSQL).                 |
| **Logging with Correlation IDs** | Trace requests across services (e.g., `X-Correlation-ID`).                  |
| **Saga Simulation Tool**          | Mock external services (e.g., `Testcontainers` for Kafka).                 |

**Example: Debugging with Jaeger**
```bash
# Start Jaeger sampling agent
docker run -d -p 6831:6831 jaegertracing/all-in-one:latest

# Inject tracing headers
curl -H "X-Jaeger-Uuid: 1234-5678-90" http://service/api/order
```

---

## **4. Prevention Strategies**

### **4.1 Architectural Best Practices**
- **Use Event Sourcing for Full Auditability:**
  - Store all state changes as immutable events.
  - Example:
    ```python
    class OrderStore:
        def __init__(self):
            self.events = []

        def place_order(self, order):
            self.events.append(("OrderPlaced", order))
            return self.events[-1]
    ```

- **Implement Idempotency at the API Level:**
  ```http
  # Example: Idempotency key in HTTP headers
  POST /orders
  Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000
  ```

- **Saga Orchestration > Choreography (When Possible):**
  - Orchestration (central controller) handles retries/offsets better than events.

### **4.2 Monitoring & Alerts**
- **Monitor Event Lag:**
  ```bash
  # Kafka consumer lag
  kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group orders-group
  ```
  - **Alert:** If lag > 10 seconds, investigate.

- **Track Projection Health:**
  - Use Prometheus to monitor projection rebuild times.

### **4.3 Testing Strategies**
- **Chaos Engineering for Event Systems:**
  - Kill Kafka brokers randomly to test recovery.
  - Example (Chaos Mesh):
    ```yaml
    apiVersion: chaos-mesh.org/v1alpha1
    kind: PodChaos
    metadata:
      name: kill-kafka-broker
    spec:
      action: pod-kill
      mode: one
      selector:
        namespaces: ["kafka"]
        labelSelectors: ["app=kafka"]
    ```

- **Event Sourcing Testing:**
  - Write tests that replay events to verify state.
  ```python
  def test_order_state():
      store = OrderStore()
      store.place_order({"id": 1, "amount": 100})
      assert store.get_order(1)["status"] == "PLACED"
  ```

---

## **5. Final Checklist for Resolution**
1. **Isolate the symptom** (e.g., missing event vs. duplicate).
2. **Check logs/events** (DLQ, event store, application logs).
3. **Verify idempotency** (no duplicate processing).
4. **Test compensations** (do they roll back correctly?).
5. **Monitor for deadlocks** (timeouts, retries).
6. **Replay events** if projections are stale.
7. **Implement circuit breakers** for external calls.

---
**Example Full Debugging Workflow:**
1. **User reports:** "Order was placed but not shipped."
2. **Check:** `SELECT COUNT(*) FROM events WHERE event_type = 'OrderShipped';` → **0**.
3. **Root Cause:** Saga `ShipOrder` step failed silently.
4. **Fix:** Add retry + DLQ + logging.
5. **Prevent:** Add saga deadlines + health checks.

---
By following this guide, you can systematically debug consistency issues in distributed systems. **Start with logs, then validate with tools like Jaeger, and enforce idempotency to prevent recurrence.**