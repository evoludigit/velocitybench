# **Debugging Event Ordering Guarantees (Sequence Numbers & CDC) – A Troubleshooting Guide**

This guide provides a structured approach to diagnosing and fixing issues related to **event ordering guarantees** in distributed systems, particularly when using **Change Data Capture (CDC) patterns**, sequence numbers, or causal ordering techniques. If events are processed out of order, leading to inconsistent state, lost updates, or race conditions, this guide will help you pinpoint and resolve the root cause efficiently.

---

## **1. Symptom Checklist**

Before diving into debugging, verify these symptoms to confirm that your issue relates to **event ordering guarantees**:

| **Symptom** | **Description** | **Likely Cause** |
|-------------|----------------|----------------|
| **Inconsistent state after replay** | Re-processing CDC logs produces different final state than live processing. | Event reordering, missing events, or race conditions. |
| **Cascading updates in wrong order** | Downstream services receive dependent events in the wrong sequence. | Lack of causal ordering or missing sequence numbers. |
| **Race conditions in event processing** | Two identical events cause conflicting updates (e.g., overcounting, duplicate state). | No idempotency enforcement or missing sequence checks. |
| **Lost updates** | Some events are skipped or reprocessed, leading to stale data. | Duplicate event detection failure or missing sequence tracking. |
| **High latency spikes** | Processing takes longer than expected due to waiting for missing events. | Suboptimal causal ordering or event dependency resolution. |
| **Deadlocks or timeouts** | Services stall waiting for events that never arrive. | Infinite waits due to missing sequence numbers or circular dependencies. |
| **Logical errors in downstream systems** | Events appear correct but cause incorrect business logic execution. | Missing event validation or sequence-based triggers not respected. |

**Next Step:** If multiple symptoms are present, prioritize the most critical (e.g., inconsistent state → **missing sequence checks**).

---

## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Missing Sequence Numbers or Incorrect Assignment**
**Symptom:**
Events lack sequence numbers, or sequences are not monotonically increasing, causing reprocessing to fail.

**Root Cause:**
- Sequence numbers are not generated per partition/logical unit.
- Sequence resets occur due to crashes or manual restarts.
- Clock skew in distributed systems leads to incorrect ordering.

**Fix:**
Implement **per-partition sequence numbers** and ensure atomicity.

#### **Example (Pseudocode – Kafka + Event Sourcing)**
```java
// Generate unique sequence per partition (Kafka topic partition)
public String generateEventId(String topic, String partition) {
    return topic + "_" + partition + "_" + nextSequenceId.getAndIncrement();
}

// Record event with sequence
public void sendEvent(Event event) {
    event.setSequenceId(generateEventId(topic, partition));
    producer.send(new ProducerRecord<>(topic, event));
}
```

**Prevention:**
- Use **UUIDs + monotonic counters** if global sequence is needed.
- Store the last processed sequence in a database for recovery.

---

### **Issue 2: Race Conditions Due to Duplicate Events**
**Symptom:**
Same event processed multiple times, causing overcounts or incorrect state.

**Root Cause:**
- Consumer deduplication fails (e.g., Kafka `isolation.level=read_committed` misconfigured).
- Retries on failed processing without idempotency checks.

**Fix:**
Implement **idempotent event processing** and **exactly-once semantics**.

#### **Example (Idempotent Processing in Java)**
```java
// Track processed events by (topic, partition, offset, sequenceId)
private final Map<String, Boolean> processedEvents = new ConcurrentHashMap<>();

public void processEvent(Event event) {
    String eventKey = event.getSequenceId(); // e.g., Kafka key
    if (!processedEvents.containsKey(eventKey)) {
        processedEvents.put(eventKey, true);
        // Apply event logic safely
    } else {
        log.warn("Duplicate event detected: " + eventKey);
    }
}
```

**Prevention:**
- Use **Kafka’s idempotent producer** (`enable.idempotence=true`).
- Store processed offsets in **Zookeeper/DB** for recovery.

---

### **Issue 3: Causal Ordering Violations**
**Symptom:**
Events that depend on each other arrive out of order.

**Root Cause:**
- No **causal ordering** enforcement (e.g., parent-child event dependencies).
- Different consumers processing events from the same partition in parallel.

**Fix:**
Enforce **per-partition ordering** + **event dependencies**.

#### **Example (Event Sourcing with Causal Tracking)**
```java
// Track dependency chains
public class EventProcessor {
    private final Map<String, Set<String>> causalDependencies = new HashMap<>();

    public void recordDependency(String parentEventId, String childEventId) {
        causalDependencies.computeIfAbsent(parentEventId, k -> new HashSet<>()).add(childEventId);
    }

    public List<Event> processEvents(List<Event> events) {
        // Process in causal order (topological sort)
        return events.stream()
            .sorted((e1, e2) -> {
                if (causalDependencies.containsKey(e1.getId()) &&
                    causalDependencies.get(e1.getId()).contains(e2.getId())) {
                    return -1; // e1 must come before e2
                }
                return 0;
            })
            .collect(Collectors.toList());
    }
}
```

**Prevention:**
- Use **Kafka Streams’ `process()` API** with stateful processing.
- Store dependencies in a **dedicated dependency graph DB**.

---

### **Issue 4: Event Loss During Reprocessing**
**Symptom:**
Some events are skipped during replay, causing gaps in state.

**Root Cause:**
- Offsets not persisted (e.g., manual `seekToOffset` without checkpointing).
- Consumer lag grows indefinitely due to slow processing.

**Fix:**
Implement **exactly-once checkpointing** and **offset management**.

#### **Example (Kafka Consumer with Offset Checkpoints)**
```java
// Enable exactly-once semantics
props.put("enable.auto.commit", "false");
props.put("isolation.level", "read_committed");

ConsumerRecords<String, Event> records = consumer.poll(Duration.ofSeconds(1));
for (ConsumerRecord<String, Event> record : records) {
    try {
        processEvent(record.value());
        consumer.commitSync(); // Atomic checkpoint
    } catch (Exception e) {
        // Dead letter queue (DLQ) or retry logic
        dlqProducer.send(new ProducerRecord<>(DLQ_TOPIC, record));
    }
}
```

**Prevention:**
- Use **Kafka’s `commitSync()`** for fault tolerance.
- Monitor **consumer lag** (`kafka-consumer-groups --describe`).

---

### **Issue 5: Clock Skew Causing Incorrect Timestamp-Based Ordering**
**Symptom:**
Events ordered incorrectly due to inconsistent timestamps (e.g., NTP drift).

**Root Cause:**
- Relying on **monotonic clock** without synchronization.
- Log-based ordering (e.g., Kafka’s `log.append()`) is skipped.

**Fix:**
Use **sequence numbers + timestamps** or **log-based ordering**.

#### **Example (Hybrid Ordering in Kafka)**
```java
// Store event with both sequence and timestamp
public class Event {
    private String sequenceId;
    private long timestamp; // System.nanoTime() + drift correction
    // ...
}

// Order by sequence first, then timestamp (if sequences are equal)
public int compareEvents(Event e1, Event e2) {
    int seqCompare = e1.getSequenceId().compareTo(e2.getSequenceId());
    if (seqCompare != 0) return seqCompare;
    return Long.compare(e1.getTimestamp(), e2.getTimestamp());
}
```

**Prevention:**
- Use **Kafka’s `timestamp.type=CREATE_TIME`** for consistent ordering.
- Deploy **NTP servers** in distributed environments.

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique** | **Purpose** | **Example Command/Setup** |
|--------------------|------------|---------------------------|
| **Kafka Consumer Groups Lag Check** | Identify slow consumers. | `kafka-consumer-groups --bootstrap-server <host>:9092 --describe` |
| **Kafka Offset Tracking** | Verify if events are reprocessed. | `kafka-consumer-groups --bootstrap-server <host>:9092 --group <group> --describe --offsets-only` |
| **JVM Profiling (Async Profiler, YourKit)** | Detect slow event processing. | `async-profiler.sh -d 60 -f flame <pid>` |
| **Kafka Producer/Consumer Metrics** | Monitor throughput & errors. | Enable `metrics.reporter` in Kafka configs. |
| **Dependency Graph Visualization** | Map causal dependencies. | Use **Graphviz** or **Elasticsearch + Kibana**. |
| **Logging Event Sequences** | Trace event ordering. | `logger.debug("Processing event {} (seq: {})", eventId, sequenceId);` |
| **PostgreSQL CDC (Debezium) Monitoring** | Track CDC lag & replay issues. | Debezium UI + Kafka Connect metrics. |
| **Chaos Engineering (Gremlin, Netflix Chaos Monkey)** | Test resilience to reordering. | Inject delays in Kafka partitions. |

**Key Debugging Workflow:**
1. **Check Kafka Consumer Lag** → Is the consumer caught up?
2. **Inspect Event Sequences** → Are sequences monotonically increasing?
3. **Replay Logs Manually** → Does reprocessing match live results?
4. **Visualize Dependencies** → Are there circular dependencies?
5. **Enable Detailed Logging** → Trace slow paths.

---

## **4. Prevention Strategies**

### **Design-Time Mitigations**
✅ **Use Per-Partition Sequences** → Ensures ordering within a partition.
✅ **Implement Idempotent Event Processing** → Prevents duplicate side effects.
✅ **Store Last Processed Offset** → Enables exact replay.
✅ **Leverage Kafka Streams/ksqlDB** → Built-in ordering guarantees.
✅ **Enforce Causal Ordering Early** → Reject out-of-order events in validation.

### **Runtime Monitoring**
🔍 **Alert on Consumer Lag** → `kafka-consumer-groups --bootstrap-server <host>:9092 --group <group> --describe | grep lag`.
🔍 **Monitor Sequence Gaps** → Check for `null` or duplicate sequences.
🔍 **Track Event Processing Time** → High variance = potential bottlenecks.
🔍 **Validate Checksums** → Ensure replay produces identical state.

### **Disaster Recovery Plan**
🚨 **Backup CDC Logs** → Use S3 + Kafka Mirrors.
🚨 **Test Replay Scripts** → Automate replay validation.
🚨 **Define Recovery SLAs** → Max allowed replay lag.

---

## **5. Final Checklist for Resolution**

Before marking the issue as resolved:
- [ ] **Sequence numbers** are correctly assigned and persisted.
- [ ] **Deduplication** works (idempotent processing).
- [ ] **Causal ordering** is enforced (no circular dependencies).
- [ ] **Consumer offsets** are checkpointed correctly.
- [ ] **Replay validation** matches live processing.
- [ ] **Monitoring** is in place for lag/errors.

---
### **When to Escalate?**
- If **sequence numbers reset unexpectedly** → Check for Kafka broker restarts.
- If **causal ordering is impossible** → Consider a different pattern (e.g., sagas).
- If **performance degrades under load** → Optimize partitioning or batching.

---
This guide should help you **quickly diagnose and fix** event ordering issues while preventing future regressions.