# **Debugging Durability Migration: A Troubleshooting Guide**

Durability Migration (also known as **Eventual Consistency with Durability**) is a pattern used to ensure data reliability across distributed systems by persisting state changes before acknowledging them to clients. This pattern is common in microservices, CQRS (Command Query Responsibility Segregation), and sagas where transactional durability is critical.

This guide provides a structured approach to diagnosing and resolving common issues during implementation, deployment, and runtime.

---

## **1. Symptom Checklist**
Before diving into debugging, identify which of the following symptoms align with your issue:

| **Symptom**                                                                 | **Possible Cause**                          |
|----------------------------------------------------------------------------|--------------------------------------------|
| **Inconsistent data across services** (e.g., POMs not updated in DB)     | Failed persistence before acknowledgment   |
| **Clients receive "Success" but state is lost on restart**              | Missing event replay or durability layer   |
| **High latency or timeouts when processing events**                     | Slow persistence layer (DB, Kafka, etc.)   |
| **Deadlocks or hanging transactions**                                    | Improper transaction management            |
| **Duplicate events processed**                                           | Event replay failed or idempotency missing  |
| **Application crashes on startup** (e.g., failed event replay)          | Corrupt or missing persistence store       |
| **Race conditions in event processing**                                  | Missing sequence IDs or validation checks |
| **Performance degradation post-migration**                               | Suboptimal persistence strategy            |

If multiple symptoms appear together, prioritize **persistency before acknowledgment** and **event replay** issues first.

---

## **2. Common Issues and Fixes**

### **Issue 1: State Not Persisted Before Acknowledgment**
**Symptoms:**
- Clients receive `"Success"` but changes disappear on restart.
- Logs show `"Event processed but not persisted"`.

**Root Cause:**
The event was enqueued (e.g., Kafka, RabbitMQ) but failed to persist before the client was acknowledged.

**Fix:**
Ensure **asynchronous acknowledgment** with at-least-once delivery:
```java
// Example in Spring Kafka with Durable Sink
@KafkaListener(id = "${spring.kafka.listener.container.id}", groupId = "durable-group")
public void listen(ConsumerRecord<String, OrderEvent> record) {
    try {
        // 1. Persist event to DB first
        eventRepository.save(record.value());

        // 2. Acknowledge AFTER persistence
        ack(record);

        // 3. Process business logic
        processOrder(record.value());
    } catch (Exception e) {
        // 4. Re-throw for dead-letter queue (DLQ)
        throw new KafkaException("Failed to process event", e);
    }
}
```
**Key Checks:**
✅ Use **transactional outbox pattern** (Spring Kafka + DB transactions).
✅ Enable **idempotent processing** (check sequence IDs before replay).

---

### **Issue 2: Event Replay Fails on Restart**
**Symptoms:**
- Application crashes on startup with `EventReplayException`.
- Logs show missing/duplicate events.

**Root Cause:**
- The event store (DB, Kafka, etc.) is corrupted.
- Missing **offset tracking** (e.g., Kafka consumer offsets not saved).

**Fix:**
1. **Verify event replay logic:**
   ```python
   # PySpark Kafka replay example
   from pyspark.sql import functions as F

   # Check for missing offsets
   df = spark.read.format("kafka") \
       .option("subscribe", "orders") \
       .option("startingOffsets", "earliest") \
       .load()

   # Ensure no duplicates (check sequence_id)
   duplicates = df.filter(F.col("sequence_id").duplicated())
   if duplicates.count() > 0:
       raise ValueError("Duplicate events detected!")
   ```

2. **Use durable offsets** (Kafka):
   ```java
   // Configure KafkaConsumer for durable offsets
   Properties props = new Properties();
   props.put(ConsumerConfig.ENABLE_AUTO_COMMIT, "false"); // Manual offsets
   props.put(ConsumerConfig.GROUP_ID_CONFIG, "durable-group");
   ```

3. **Retry with exponential backoff:**
   ```javascript
   // Node.js with KafkaJS
   const { Kafka } = require('kafkajs');
   const kafka = new Kafka({ brokers: ['kafka:9092'] });
   const consumer = kafka.consumer({ groupId: 'durable-group' });

   async function replayEvents() {
     await consumer.connect();
     await consumer.subscribe({ topic: 'orders', fromBeginning: true });

     let retries = 0;
     while (retries < 5) {
       try {
         await consumer.run({
           eachMessage: async ({ topic, partition, message }) => {
             await processEvent(message.value.toString());
             await consumer.commitOffsets([{ topic, partition, offset: message.offset }]);
           },
         });
         break;
       } catch (err) {
         retries++;
         await new Promise(resolve => setTimeout(resolve, 1000 * retries));
       }
     }
   }
   ```

---

### **Issue 3: Performance Bottlenecks**
**Symptoms:**
- Slow event processing (high latency).
- DB under heavy load due to excessive writes.

**Root Cause:**
- **Over-persisting** (e.g., writing every event to DB).
- **Blocking I/O** (synchronous DB calls).
- **No batching** (small transactions).

**Fix:**
1. **Batch writes** (e.g., Kafka + DB transaction batching):
   ```java
   // Spring Kafka + JPA batching
   @KafkaListener(id = "batch-listener", groupId = "durable-group")
   public void processBatch(ConsumerRecord<String, OrderEvent>[] records) {
       List<OrderEvent> events = Arrays.stream(records)
           .map(ConsumerRecord::value)
           .collect(Collectors.toList());

       // Batch insert (using Spring Data JPA)
       eventRepository.saveAll(events); // Single DB call
   }
   ```

2. **Use async persistence:**
   ```javascript
   // Node.js with async DB writes
   const { Kafka } = require('kafkajs');
   const { pool } = require('./db');

   const kafka = new Kafka();
   const producer = kafka.producer();

   async function processEvent(event) {
     await pool.query('BEGIN');
     try {
       await pool.query('INSERT INTO events VALUES($1)', [event]);
       await producer.send({ topic: 'ack', messages: [{ value: event.id }] });
       await pool.query('COMMIT');
     } catch (err) {
       await pool.query('ROLLBACK');
       throw err;
     }
   }
   ```

3. **Optimize DB schema:**
   - Use **partitioning** (e.g., `events(id, topic, sequence_id)`).
   - Add **indexes** on `topic` and `sequence_id`.

---

### **Issue 4: Deadlocks or Hanging Transactions**
**Symptoms:**
- Long-running transactions.
- `TimeoutException` in DB or Kafka.

**Root Cause:**
- **Long-running business logic** blocking acknowledgment.
- **Nested transactions** without proper isolation.

**Fix:**
1. **Short-circuit acknowledgment:**
   ```java
   // Spring Kafka + async processing
   @KafkaListener(id = "async-listener", groupId = "durable-group")
   public void listen(ConsumerRecord<String, OrderEvent> record) {
       // 1. Persist first
       eventRepository.save(record.value());

       // 2. ACK immediately
       ack(record);

       // 3. Process asynchronously
       executorService.submit(() -> processOrder(record.value()));
   }
   ```

2. **Use **SAGA pattern** (for complex workflows):**
   ```java
   // Saga orchestrator example
   public class OrderSaga {
       private final EventRepository eventRepo;

       public void execute(OrderEvent event) {
           if (!eventRepo.existsById(event.getId())) { // Duplicate check
               eventRepo.save(event);
               notifyNextService(event); // Async call
           }
       }
   }
   ```

---

### **Issue 5: Duplicate Events**
**Symptoms:**
- Same event processed multiple times.
- Data corruption (e.g., double payments).

**Root Cause:**
- **Idempotent processing missing.**
- **Kafka consumer re-processing** due to failed offsets.

**Fix:**
1. **Implement idempotency:**
   ```java
   // Check for duplicates before processing
   public void processOrder(OrderEvent event) {
       if (orderService.existsById(event.getOrderId())) {
           log.warn("Duplicate event skipped: {}", event.getId());
           return;
       }
       orderService.createOrder(event);
   }
   ```

2. **Use Kafka **isolation.level=read_committed** (if using transactions):**
   ```java
   Properties props = new Properties();
   props.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed");
   ```

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique**               | **Use Case**                                      | **Example Command/Code**                     |
|-----------------------------------|---------------------------------------------------|---------------------------------------------|
| **Kafka Consumer Group Monitoring** | Check lag in event processing                    | `kafka-consumer-groups --describe --bootstrap-server localhost:9092 --group durable-group` |
| **DB Query Profiling**            | Identify slow SQL                                | `EXPLAIN ANALYZE SELECT * FROM events WHERE topic = 'orders';` (PostgreSQL) |
| **Logging & Metrics**             | Track event processing latency                   | Prometheus + Grafana (Spring Boot Actuator) |
| **Dead Letter Queue (DLQ)**       | Capture failed events for analysis               | Configure Kafka `max.poll.interval.ms` + DLQ topic |
| **Transaction Log Analysis**      | Debug failed commits                             | `SELECT * FROM pg_xact_commit_timestamp();` (PostgreSQL) |
| **Chaos Engineering (Gremlin)**   | Test durability under failure                    | Simulate DB failures: `greeting().times(100).send()` |

**Example Debugging Workflow:**
1. **Check Kafka lag:**
   ```bash
   kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group durable-group
   ```
2. **Inspect DB performance:**
   ```bash
   pg_stat_activity;  # PostgreSQL
   ```
3. **Review DLQ for failed events:**
   ```bash
   kafka-console-consumer --bootstrap-server localhost:9092 --topic dlq-orders --from-beginning
   ```

---

## **4. Prevention Strategies**

### **Design-Time Checks**
✅ **Enforce durable acknowledgment** (never ack before persistence).
✅ **Use outbox pattern** (decouple event publishing from DB transactions).
✅ **Implement idempotency** (check sequence IDs or event IDs).
✅ **Batch writes** (reduce DB load).

### **Runtime Safeguards**
🔹 **Monitor Kafka consumer lag** (alert if >1000 messages).
🔹 **Set up DLQ** for failed events (e.g., Kafka `max.poll.interval.ms=300000`).
🔹 **Enable transactional writes** (Kafka + DB transactions).
🔹 **Use circuit breakers** (e.g., Resilience4j) for DB failures.

### **Testing Strategies**
🧪 **Chaos Testing:**
   - Kill DB/kafka pods randomly (simulate failures).
   - Verify event replay works.

🧪 **Load Testing:**
   - Simulate high-throughput events (e.g., 10K/s).
   - Check for timeouts or duplicate processing.

🧪 **Unit Tests for Idempotency:**
   ```java
   @Test
   public void testIdempotentProcessing() {
       OrderEvent event = new OrderEvent("123", "CREATE");
       orderService.process(event); // First call
       orderService.process(event); // Duplicate - should skip
       assertEquals(1, orderRepository.count()); // Only one record
   }
   ```

---

## **5. Final Checklist for Durability Migration**
| **Step**                          | **Action**                                      | **Tool/Example**                          |
|-----------------------------------|-------------------------------------------------|-------------------------------------------|
| **1. Persist before acknowledgment** | Ensure DB write happens before `ack()`       | Kafka `transactional.id` + DB transactions |
| **2. Enable event replay**        | Check for missing offsets                      | Kafka `fromBeginning=true`                |
| **3. Batch writes**               | Reduce DB load with `saveAll()`                | Spring Data JPA batching                  |
| **4. Monitor consumer lag**       | Alert if lag exceeds threshold                 | Kafka Consumer Group Monitor             |
| **5. Implement idempotency**      | Skip duplicates with `existsById()`            | Custom `IdempotentConsumer`                |
| **6. Test failure scenarios**     | Simulate DB/kafka outages                      | Gremlin chaos testing                     |

---

## **Conclusion**
Durability Migration is critical for reliable distributed systems. The most common pitfalls—**missing persistence before acknowledgment**, **failed event replay**, and **performance bottlenecks**—can be mitigated with:
- **At-least-once processing** (Kafka + DB transactions).
- **Idempotent event handling**.
- **Batching and async I/O**.
- **Proactive monitoring** (Kafka lag, DB queries).

By following this guide, you can **diagnose issues quickly** and **prevent regressions** in production. Always **test failure scenarios** and **monitor consumer lag** to ensure long-term reliability.