# **Debugging *Streaming Conventions*: A Troubleshooting Guide**
*For Backend Engineers Working with Event-Driven & Stream Processing Systems*

---

## **Introduction**
The **Streaming Conventions** pattern ensures consistency in how events are published, consumed, and processed across distributed systems. Common implementations include:
- **Event Schemas** (Avro, Protobuf, JSON)
- **Event Serialization/Deserialization**
- **Idempotency & Deduplication**
- **Schema Evolution Handling**
- **Consumer Offset Management**

When misconfigured or misused, this pattern can lead to:
✅ **Lost events** (consumers fail to read due to misaligned offsets)
✅ **Schema validation failures** (mismatched producer/consumer schemas)
✅ **Duplicate processing** (event replay without idempotency)
✅ **Backpressure** (slow producers/consumers causing bottlenecks)

This guide provides a structured approach to diagnosing and fixing issues.

---

## **📋 Symptom Checklist**
Before diving into debugging, confirm which of these symptoms match your problem:

| **Symptom**                     | **Possible Cause**                          | **Impact Scope**               |
|---------------------------------|--------------------------------------------|--------------------------------|
| Consumers fail on startup       | Schema mismatch, broken serialization      | High (service downtime)        |
| Events appear duplicated        | Consumer lag, no idempotency, retry loops     | High (data corruption)         |
| High latency in processing      | Serialization overhead, small batches       | Medium (user-facing delays)     |
| Events lost after restart       | Offset commit failures, missing acks        | Critical (data loss)            |
| Schema evolution breaks consumers| Backward-incompatible changes               | High (app crashes)              |
| Backpressure in producers       | Slow consumers, no batching                 | Medium (resource contention)   |
| Debug logs show "Deserialization failed" | Broken schema, null fields, malformed data | Critical (processing halts)     |

---
## **🔍 Common Issues & Fixes**
### **1. Schema Mismatch (Avro/Protobuf/JSON)**
**Symptom:**
Consumers throw `java.io.IOException: Schema mismatch` or `Type mismatch` errors.

**Debugging Steps:**
- **Check producer schema:** Verify the schema used when publishing.
- **Check consumer schema:** Compare with schemas registered in the broker (e.g., Kafka schema registry).
- **Validate dynamically:** Use `SchemaRegistryClient` or `Protobuf` reflection.

**Fixes:**
#### **A. Ensure Backward Compatibility**
If using **Avro**, add new fields with `DEFAULT` values:
```java
// Producer
Schema producerSchema = new Schema.Parser().parse("{\"type\":\"record\",\"name\":\"UserEvent\",\"fields\":"
    + "[{\"name\":\"id\",\"type\":\"string\"}, {\"name\":\"name\",\"type\":\"string\", \"default\": \"\"}]}");
```
#### **B. Force Schema Registration in Kafka**
```java
// Register schema on startup (if using Confluent Schema Registry)
Schema schema = new Schema.Parser().parse("...");
// Register
SchemaRegistryClient client = new SchemaRegistryClient("http://schema-registry:8081", "user");
client.register("user-event", schema.getName(), schema);
```

#### **C. Use JSON Schema for Flexibility**
If dynamic schemas are needed:
```java
// Use a library like JSON Schema Validator
JSONObject event = new JSONObject("{ \"id\": \"123\", \"name\": \"John\" }");
JSONAssert.assertEquals(expectedSchema, event, true); // Check structure
```

---

### **2. Offset Commit Failures (Lost Events)**
**Symptom:**
Events disappear after consumer restarts or broker restart.

**Root Cause:**
- Manual commits without `auto.offset.reset = earliest`
- Unhandled exceptions causing incomplete commits
- Consumer lag exceeding `max.poll.interval.ms`

**Debugging Steps:**
- Check Kafka consumer logs for `OffsetCommitFailedException`.
- Run `kafka-consumer-groups` to see lag:
  ```bash
  kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-group
  ```
- Verify `enable.auto.commit` vs. `auto.commit.interval.ms`.

**Fixes:**
#### **A. Use `earliest` Reset for Recovered Events**
```yaml
# consumer props
config.put("auto.offset.reset", "earliest"); // Replay from start
config.put("enable.auto.commit", false);    // Manual commits
```

#### **B. Implement Manual Commit with Exponential Backoff**
```java
try {
    ConsumerRecords<String, Event> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, Event> record : records) {
        processEvent(record.value());
    }
    consumer.commitSync(); // Sync commit to avoid loss
} catch (KafkaException e) {
    // Retry with backoff
    Thread.sleep(1000 * (exponential backoff logic));
}
```

#### **C. Monitor Consumer Lag**
```java
// Check lag periodically
long offset = consumer.position(topicPartition);
long endOffset = consumer.endOffset(topicPartition);
long lag = endOffset - offset;
if (lag > THRESHOLD) {
    log.warn("Consumer lagging behind! Lag: {}", lag);
}
```

---

### **3. Duplicate Events (No Idempotency)**
**Symptom:**
The same event triggers multiple times in the application.

**Root Cause:**
- No idempotency keys
- Retries without deduplication
- Consumer offset rollback on failures

**Debugging Steps:**
- Check for duplicate `eventId` or `transactionId` in logs.
- Review retry logic (e.g., `resilience4j` or `Hystrix` retries).

**Fixes:**
#### **A. Use Idempotent Sinks**
```java
// Example: Idempotent write to database (using transactionId)
@Transactional
public void saveEvent(Event event) {
    if (!eventRepository.existsById(event.getTransactionId())) {
        eventRepository.save(event);
    }
}
```

#### **B. Deduplicate at the Broker Level (Kafka)**
```yaml
# Enable idempotent producer
props.put("enable.idempotence", true);
props.put("transactional.id", "my-producer");
```
```java
// Start transaction
producer.initTransactions();
producer.beginTransaction();
try {
    producer.send(record).get(); // Send with retry
    producer.commitTransaction();
} catch (Exception e) {
    producer.abortTransaction();
}
```

#### **C. Track Processed Events in a DB**
```java
// Use a separate "processed_events" table
@Scheduled(fixedRate = 60000)
public void cleanupDuplicates() {
    long cutoff = System.currentTimeMillis() - (3600 * 1000); // 1 hour
    eventRepository.deleteByTimestampLessThanAndIdNotIn(
        cutoff,
        eventRepository.findAllIdsLastHour()
    );
}
```

---

### **4. Slow Processing (Backpressure)**
**Symptom:**
Producer stall due to slow consumers.

**Root Cause:**
- No batching (`batch.size` too small)
- Heavy serialization/deserialization
- CPU-bound processing

**Debugging Steps:**
- Monitor `kafka-consumer-offsets` for lag.
- Check producer metrics (`record-send-rate`, `record-error-rate`).

**Fixes:**
#### **A. Increase Batch Size**
```yaml
# Producer config
props.put("batch.size", 65536);   // Default: 16KB
props.put("linger.ms", 20);       // Wait up to 20ms for more records
```

#### **B. Use Async Processing**
```java
// Offload processing to a thread pool
ExecutorService executor = Executors.newFixedThreadPool(10);
producer.send(record).thenAccept(recordMetadata -> {
    executor.submit(() -> processEvent(record.value()));
});
```

#### **C. Optimize Serialization**
Replace JSON with **Protobuf** or **Avro** for faster parsing:
```java
// Protobuf example
EventProto.Event eventProto = EventProto.Event.newBuilder()
    .setId("123")
    .setName("John")
    .build();
byte[] data = eventProto.toByteArray(); // Faster than JSON
```

---

### **5. Schema Evolution Breaks Consumers**
**Symptom:**
Consumers crash when new fields are added.

**Root Cause:**
- **Forward compatibility** not handled (e.g., required fields removed).
- No backward-compatible schema changes.

**Debugging Steps:**
- Compare `schema-registry` versions.
- Test with old consumers against new events.

**Fixes:**
#### **A. Use Avro’s Backward/Forward Compatibility Rules**
| Change Type          | Backward? | Forward? | Allowed? |
|----------------------|-----------|----------|----------|
| Add field            | ✅ Yes     | ✅ Yes    | ✅ Yes    |
| Remove field         | ❌ No      | ✅ Yes    | ❌ No     |
| Change field type    | ❌ No      | ✅ Yes    | ❌ No     |
| Rename field         | ❌ No      | ❌ No     | ❌ No     |

**Example: Safe Schema Update**
```java
// Producer adds a new optional field
Schema updatedSchema = new Schema.Parser().parse("""
    {
        "type": "record",
        "name": "UserEvent",
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "email", "type": ["null", "string"], "default": null}
        ]
    }
""");
```

#### **B. Use Schema Registry with Compatibility Checks**
```java
// Test compatibility before deployment
Schema compatibilityCheck = client.getLatestCompatibleSchema("user-event");
if (compatibilityCheck == null) {
    throw new IllegalStateException("Schema incompatible with consumers!");
}
```

---

## **🛠 Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                          |
|-------------------------|-----------------------------------------------|---------------------------------------------|
| **Kafka Consumer Offset Checker** | Verify consumer lag                           | `kafka-consumer-groups --describe`          |
| **Schema Registry CLI** | Inspect schemas                               | `curl http://schema-registry:8081/subjects/` |
| **JTracing**            | Monitor Kafka producer/consumer latency      | Add `MetricsConfig` to producer/consumer   |
| **Prometheus + Grafana** | Track schema evolution metrics               | `schema_registry_subjects_count`           |
| **Kafka Topic Inspector** | Check record counts, offsets                 | `kafka-topics --describe --topic events`   |
| **JSON Schema Validator** | Validate runtime JSON events                 | `jsonschema --strict validate schema.json event.json` |
| **ByteBuddy**           | Dynamically patch deserialization            | Use for schema evolution in Java           |

**Example: Debugging with `kafka-consumer-groups`**
```bash
# List groups with lag
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-group

# Force rebalance
kafka-consumer-groups --bootstrap-server localhost:9092 --alter --group my-group --new-offset 1000
```

---

## **🔧 Prevention Strategies**
### **1. Schema Governance**
- **Enforce backward compatibility** in all changes.
- **Use Schema Registry** and auto-generate types (Java/JS/Python).
- **Test schema changes** with old consumers in CI.

### **2. Consumer Resilience**
- **Implement circuit breakers** for slow consumers.
- **Use exactly-once processing** with Kafka transactions.
- **Monitor consumer lag** and auto-scale consumer groups.

### **3. Idempotency by Default**
- **Tag all events with a unique `transactionId`**.
- **Use database locks** for critical operations.

### **4. Performance Tuning**
- **Benchmark serialization** (Protobuf > JSON > Avro in some cases).
- **Tune batching** (`linger.ms`, `batch.size`).
- **Use async I/O** for non-blocking processing.

### **5. Observability**
- **Log schema versions** with events.
- **Track consumer lag** in metrics (Prometheus).
- **Alert on offset drift** (`lag > threshold`).

---

## **📚 Further Reading**
- [Kafka Schema Registry Docs](https://docs.confluent.io/platform/current/schema-registry/index.html)
- [Avro Schema Compatibility Guide](https://avro.apache.org/docs/current/spec.html#schema_compatibility)
- [Protobuf Best Practices](https://developers.google.com/protocol-buffers/docs/best-practices)

---

## **🎯 Checklist for Quick Resolution**
1. **Is the issue schema-related?** → Check `SchemaRegistry` compatibility.
2. **Are events lost?** → Verify `auto.offset.reset` and commits.
3. **Are there duplicates?** → Implement idempotency keys.
4. **Is processing slow?** → Optimize batching/serialization.
5. **Does schema evolution break consumers?** → Follow backward-compatible changes.

By following this guide, you should be able to diagnose and fix **90% of Streaming Conventions issues** within an hour. For complex cases, leverage **Kafka’s metrics** and **schema registry tools** for deeper insights.