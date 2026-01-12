# **Debugging Consistency Patterns: A Troubleshooting Guide**
**Consistency Patterns** ensure that distributed systems maintain logical consistency across replicas or partitions, balancing availability, partition tolerance, and consistency (CAP Theorem). Common implementations include **Sagas, Event Sourcing, CRDTs, and Two-Phase Commit (2PC)**.

This guide focuses on debugging failures in **Sagas (for distributed transactions), Event Sourcing (for immutable logs), and 2PC (for strict consistency)**.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which **Consistency Pattern** is failing and its symptoms:

| **Symptom**                     | **Possible Cause**                          | **Pattern Affected**       |
|----------------------------------|---------------------------------------------|----------------------------|
| Inconsistent state across DBs   | Failed compensating transactions            | Sagas                     |
| Lost data on recovery           | Unreplayed/duplicate events                 | Event Sourcing            |
| Timeouts in distributed locks    | Network latency or deadlocks               | 2PC                       |
| Partial updates (dirty reads)   | Event propagation delay                     | Event Sourcing / Sagas     |
| Duplicate transactions           | Event replay or idempotency failure         | Event Sourcing            |
| Hanging transactions             | Long-running compensators or locks         | Sagas / 2PC               |
| Slow performance                 | High event load or unoptimized CRDT ops     | CRDTs                     |

**Quick Checks:**
- Are compensating transactions rolling back correctly?
- Are events being persisted and replayed reliably?
- Are distributed locks timed out or stuck?

---

## **2. Common Issues and Fixes**

### **A. Sagas (Distributed Transactions)**
**Issue 1: Failed Compensating Transactions**
**Symptoms:**
- A parent transaction succeeds, but compensators fail, leaving the system in an inconsistent state.
- Logs show compensators stuck or timing out.

**Debugging Steps:**
1. **Check Compensator Execution**
   - Verify if compensators are invoked in reverse order (LIFO).
   - Log compensator statuses (success/failure) in a saga orchestrator.

2. **Retry Failed Compensators (with Exponential Backoff)**
   ```java
   // Example: Retry failed compensators (Node.js)
   async function runCompensator(compensator, maxRetries = 3) {
       let retries = 0;
       while (retries < maxRetries) {
           try {
               await compensator();
               return true;
           } catch (err) {
               retries++;
               await delay(100 * retries); // Exponential backoff
           }
       }
       logError(`Compensator failed after ${maxRetries} retries`);
       return false;
   }
   ```

3. **Idempotency for Compensators**
   - Ensure compensators are idempotent (same result on multiple runs).
   - Example: Use `UPDATE ... WHERE id = ?` instead of `INSERT`.

**Issue 2: Choreography vs. Orchestration Failures**
**Symptoms:**
- Missing or delayed event notifications in choreography.
- Orchestrator goes offline.

**Fixes:**
- **Choreography:** Use **Pub/Sub** (Kafka, RabbitMQ) with **dead-letter queues (DLQ)** for failed messages.
  ```python
  # Kafka Producer (Python) with DLQ
  producer = KafkaProducer(
      bootstrap_servers="localhost:9092",
      error_handling_listener=True
  )
  try:
      producer.send("events", event_value)
  except KafkaError as e:
      logger.error(f"DLQ: Event failed - {e}")
      producer.send("dlq-events", event_value)  # Retry later
  ```

- **Orchestration:** Use **Saga libraries** (e.g., **Axoniq for Event Sourcing, Temporal.io for Workflows**).

**Issue 3: Timeout in Long-Running Sagas**
**Symptoms:**
- Transactions time out before completion.
- Compensators never trigger.

**Fix:**
- **Long Polling / Eventual Consistency:**
  - Use **saga timeouts** with **background workers** (Celery, AWS Step Functions).
  - Example: **AWS Step Functions** with **Activity Timeout**:
    ```yaml
    # AWS Step Functions Definition
    CompensateActivity:
      Type: Task
      Resource: arn:aws:lambda:us-east-1:123456789012:function:compensate-order
      TimeoutSeconds: 300  # 5 min
      Retry: [ { ErrorEquals: ["States.ALL"], IntervalSeconds: 10, MaxAttempts: 3 } ]
    ```

---

### **B. Event Sourcing**
**Issue 1: Lost Events on Recovery**
**Symptoms:**
- Data missing after a crash.
- Events not replayed correctly.

**Debugging Steps:**
1. **Check Event Persistence**
   - Events must be **append-only** (e.g., Kafka, PostgreSQL with WAL).
   - Use **eventual consistency** for reads:
     ```sql
     -- PostgreSQL: Ensure events are durable
     INSERT INTO events (id, type, payload)
     VALUES ('123', 'ORDER_CREATED', '{}')
     ON CONFLICT (id) DO UPDATE
     SET payload = EXCLUDED.payload;
     ```

2. **Replay Mechanism Failure**
   - If events are stored in a **DB**, ensure **transactions wrap event writes and projections**.
   - Example: **Projections (Materialized Views)** must replay from the start:
     ```java
     // Projection in Java (Akka Persistence)
     public void on(OrderCreated event, ProjectionContext ctx) {
         Optional<Order> existing = ctx.readStorage().findById(event.orderId);
         if (existing.isEmpty()) {
             Order newOrder = new Order(event.orderId, event.payload);
             ctx.writeStorage().save(newOrder);
         }
     }
     ```

3. **Idempotency for Event Handlers**
   - Use **event versioning** or **deduplication keys**:
     ```python
     # Idempotent event handler (Python)
     def handle_purchase(event):
         if not is_processed(event.id):
             process_event(event)
             mark_as_processed(event.id)
     ```

**Issue 2: Duplicate Events**
**Symptoms:**
- Business logic fails due to duplicate processing.

**Fix:**
- **Use Event Sourcing Libraries** (e.g., **EventStoreDB, Axon Framework**) with **built-in deduplication**.
- **Manual Deduplication:**
  ```sql
  -- SQL: Filter duplicates before processing
  INSERT INTO processed_orders (order_id)
  SELECT order_id
  FROM events
  WHERE type = 'ORDER_CREATED'
  ON CONFLICT (order_id) DO NOTHING;
  ```

---

### **C. Two-Phase Commit (2PC)**
**Issue 1: Hanging Transactions (Deadlocks)**
**Symptoms:**
- Transactions stuck in `prepared` state forever.
- No rollback after failure.

**Debugging Steps:**
1. **Check Timeout Configuration**
   - Increase **-prepare-timeout** and **commit-timeout**:
     ```sql
     -- PostgreSQL: Adjust 2PC timeout
     SET lock_timeout = '30s';
     SET statement_timeout = '60s';
     ```

2. **Use Saga Instead of 2PC**
   - If possible, replace 2PC with **compensating transactions** (Sagas).

3. **Logging 2PC State**
   - Log `prepare` and `commit/rollback` phases:
     ```java
     // Logging 2PC state (Java)
     log.info("Phase 1 (Prepare) - Transaction: {}", transactionId);
     if (allNodesAck) {
         log.info("Phase 2 (Commit) - Transaction: {}", transactionId);
     } else {
         log.warn("Phase 2 (Rollback) - Transaction: {}", transactionId);
     }
     ```

**Issue 2: Network Partitions**
**Symptoms:**
- Some nodes acknowledge `prepare` but fail on `commit`.

**Fix:**
- **Use Paxos/Raft** (e.g., **CockroachDB, etcd**) for **strong consistency**.
- **Fallback to Local Transactions** if partition detected.

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique**          | **Use Case**                                  | **Example**                                  |
|-----------------------------|-----------------------------------------------|----------------------------------------------|
| **Distributed Tracing**     | Track saga flow across services              | Jaeger, OpenTelemetry                         |
| **Logging Correlations**    | Link events to transactions                  | `X-Trace-ID` headers                         |
| **Event Store Replay**      | Debug lost/replayed events                    | EventStoreDB CLI, `esread`                   |
| **Lock Timeouts**           | Prevent hanging 2PC transactions             | PostgreSQL `SET lock_timeout`                |
| **Dead Letter Queues (DLQ)**| Capture failed events for manual review      | Kafka DLQ, RabbitMQ dead-letter exchanges    |
| **Saga Visualizer**         | Monitor saga state machine                   | Temporal Workflows UI                        |
| **Database Replication Lag**| Check for eventual consistency delays        | `pg_stat_replication` (PostgreSQL)           |

**Example Debugging Workflow (Saga):**
1. **Generate a Trace ID** for the saga:
   ```python
   # Set trace ID in headers
   headers = {"X-Trace-ID": str(uuid.uuid4())}
   ```
2. **Use Jaeger to Visualize:**
   ```sh
   jaeger query --endpoint=http://jaeger:16686 --span-id YOUR_TRACE_ID
   ```
3. **Check DLQ for Failed Events:**
   ```sh
   kafka-console-consumer --bootstrap-server localhost:9092 --topic dlq-events --from-beginning
   ```

---

## **4. Prevention Strategies**

### **A. For Sagas**
✅ **Design for Failure:**
- Assume **network partitions** and **timeouts**.
- Use **circuit breakers** (e.g., Hystrix, Resilience4j).

✅ **Monitor Compensators:**
- Set up **alerts for stuck compensators**.
- Example: **Prometheus + Grafana** for saga metrics:
  ```yaml
  # Alert if compensator fails
  - alert: SagaCompensatorFailed
      expr: saga_compensator_errors > 0
      for: 5m
      labels:
        severity: critical
  ```

✅ **Idempotency Guarantees:**
- Use **database UPSERTs** or **CRDTs** for state updates.

### **B. For Event Sourcing**
✅ **Ensure Event Durability:**
- Use **append-only storage** (Kafka, EventStoreDB).
- **Backup events** to S3/Blob Storage.

✅ **Projection Health Checks:**
- Schedule **projection replay jobs** on startup.

✅ **Event Versioning:**
- Avoid **breaking changes** in event schemas.

### **C. For 2PC**
✅ **Avoid Long-Running Transactions:**
- **Break into smaller Saga steps**.
- Use **optimistic locking** instead of 2PC.

✅ **Fallback to One-Phase Commit:**
- If **strict consistency isn’t critical**, use **eventual consistency**.

✅ **Monitor Replication Lag:**
- **PostgreSQL:**
  ```sql
  SELECT pg_is_in_recovery(), pg_last_xact_replay_timestamp();
  ```
- **CockroachDB:**
  ```sql
  SHOW TABLE status;
  ```

---

## **5. Final Checklist Before Production**
| **Check**                          | **Action**                                  |
|-------------------------------------|---------------------------------------------|
| Sagas: Compensators tested in staging | Run chaos engineering (e.g., kill orchestrator). |
| Event Sourcing: Event replay works  | Test full replay from snapshot.            |
| 2PC: Timeouts configured            | Set `lock_timeout` and `statement_timeout`.|
| Monitoring: Alerts for failures     | Set up Prometheus/Grafana dashboards.       |
| Idempotency: All handlers tested    | Verify no duplicates on replay.             |
| Backup: Events stored redundantly   | Use S3/Blob for event durability.           |

---

## **Conclusion**
Consistency Patterns are powerful but require **careful debugging** to handle failures. The key is:
1. **Log everything** (trace IDs, compensator statuses).
2. **Test edge cases** (timeouts, network splits).
3. **Use monitoring** (DLQs, tracing, alerts).
4. **Favor eventual consistency** where strict consistency isn’t critical.

By following this guide, you can **quickly diagnose and fix** consistency-related issues in distributed systems. 🚀