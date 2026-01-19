# **Debugging Streaming Migration: A Troubleshooting Guide**

## **Overview**
The **Streaming Migration** pattern involves incrementally transferring data from an old system to a new one in real-time while maintaining consistency. This pattern ensures minimal downtime and near-zero data loss while migrating large datasets. However, misconfigurations, network issues, or data inconsistency problems can arise.

This guide provides a structured approach to diagnose and resolve common issues in a **Streaming Migration** implementation.

---

---

# **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

| **Symptom**                     | **Possible Cause**                          | **Action** |
|----------------------------------|--------------------------------------------|------------|
| **Partial data transfer**        | Out-of-order messages, dead letters        | Check consumer offsets, retry logic |
| **Duplicate records**            | Idempotent processing failure, retries     | Validate deduplication keys |
| **Consumer lag**                 | Slow processing, backpressure, network issues | Monitor Kafka lag, scaling needs |
| **Schema drift**                 | Version mismatch between source/target      | Check Avro/Protobuf compatibility |
| **System time skew**             | Timestamp mismatches in events              | Synchronize clocks, use event timestamps |
| **High error rates**             | Malformed data, schema validation failures | Log schema errors, validate payloads |
| **Unprocessed partitions**       | Consumer crash, improper partition assignment | Check consumer health, rebalancing |
| **Target system inconsistencies** | Failed writes, transaction rollbacks       | Audit database commits, check WAL |

---

# **2. Common Issues and Fixes**

### **Issue 1: Partial Data Transfer (Missing or Out-of-Order Records)**
**Symptoms:**
- Some records from the source system did not arrive in the target.
- Events appear in a different order than expected.

**Root Causes:**
- **Consumer failed before completing processing** (e.g., OOM, crash).
- **Dead-letter queue (DLQ) not configured**, causing retries to fail silently.
- **Consumer lag** due to slow processing or network bottlenecks.

**Solution:**
#### **A. Check Consumer Offsets**
Ensure consumers commit offsets only after successful processing.
```java
// Kafka Consumer Example (Java)
Records<byte[], byte[]> records = consumer.poll(Duration.ofMillis(100));
for (ConsumerRecord<byte[], byte[]> record : records) {
    try {
        process(record.value());
        consumer.commitSync(); // Only commit after success
    } catch (Exception e) {
        logger.error("Failed to process: " + record.key(), e);
        // Optionally, send to DLQ
    }
}
```
**Fix:** Use `consumer.commitAsync()` with manual error handling.

#### **B. Implement Dead-Letter Queue (DLQ)**
Configure a DLQ for failed messages.
```yaml
# Kafka Config (producer)
topic: "migration-topic"
producer:
  deliveryTimeoutMs: 300000
  retries: 5
```

#### **C. Monitor Consumer Lag**
Check consumer lag in Kafka Manager or `kafka-consumer-groups.sh`:
```bash
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group migration-consumer
```
**Fix:** Scale consumers if lag is high.

---

### **Issue 2: Duplicate Records**
**Symptoms:**
- Same record appears multiple times in the target system.

**Root Causes:**
- **Retries** (e.g., transient failures) cause reprocessing.
- **Idempotent processing not enforced** (e.g., INSERT instead of UPSERT).

**Solution:**
#### **A. Use Idempotent Keys**
Ensure each record has a unique identifier (e.g., UUID, transaction ID).
```python
# Example: Check if record exists before inserting
if not db.execute("SELECT COUNT(*) FROM target_table WHERE migrate_key = ?", (record_id,)):
    db.execute("INSERT INTO target_table (...) VALUES (?)", (record,))
```

#### **B. Implement Deduplication Logic**
Use a **cache (Redis) or database temp table** to track processed records.
```java
// Using Redis to track processed IDs
String key = "processed_" + recordId;
if (!redis.exists(key)) {
    redis.set(key, "1", 24 * 3600); // Cache for 24h
    process(record);
}
```

---

### **Issue 3: Consumer Lag & Backpressure**
**Symptoms:**
- Consumers fail to keep up with the source topic’s production rate.
- High `kafka.consumer.lag` metrics.

**Root Causes:**
- **Slow processing logic** (e.g., blocking I/O).
- **Insufficient consumer instances**.
- **Network throttling**.

**Solution:**
#### **A. Optimize Consumer Processing**
- **Parallelize work** (e.g., async DB writes).
- **Batch records** before processing.
```java
// Batch processing example
List<ConsumerRecord<byte[], byte[]>> batch = new ArrayList<>();
for (ConsumerRecord<byte[], byte[]> record : records) {
    batch.add(record);
    if (batch.size() >= 100) {
        processBatch(batch);
        batch.clear();
    }
}
```

#### **B. Scale Consumers Horizontally**
- Increase consumer count in Kafka consumer group.
- Use **partition keys** to ensure even distribution.

#### **C. Implement Backpressure**
- **Pause consumption** if the target system is overloaded.
```java
if (targetSystem.isOverloaded()) {
    consumer.pause(consumer.assignment()); // Temporarily pause
    Thread.sleep(5000); // Wait before resuming
    consumer.resume(consumer.assignment());
}
```

---

### **Issue 4: Schema Mismatch (Source vs. Target)**
**Symptoms:**
- `SchemaNotFoundException` in Avro/Protobuf.
- Invalid data in the target database.

**Root Causes:**
- **Version skew** between source and target schema.
- **Dynamic schema evolution** not handled.

**Solution:**
#### **A. Use Schema Registry (Apache Avro)**
Ensure both source and target use the same schema registry.
```java
// Schema Registry Client (Java)
Schema schema = Schema.parse(new String(SchemaRegistryClient.fetchLatestSchema(“topic”)));
```

#### **B. Handle Schema Evolution Gracefully**
- Use **backward-compatible changes** (e.g., adding optional fields).
- **Log schema mismatches** for debugging.
```java
try {
    parseAvroMessage(message);
} catch (SchemaParseException e) {
    logger.error("Schema mismatch: " + e.getMessage());
    // Optionally, reject or transform data
}
```

---

### **Issue 5: System Clock Skew**
**Symptoms:**
- Events appear **out of order** despite proper partitioning.
- **Duplicate events** due to timestamp misalignment.

**Root Causes:**
- **Source and target clocks differ by >5 min** (Kafka’s `clock.drift.allowed.ms`).
- **Using system time instead of event timestamps**.

**Solution:**
#### **A. Synchronize Clocks (NTP)**
Ensure all machines (Kafka, DB, app servers) use the same time source:
```bash
# Linux: Enable NTP service
sudo apt install ntp
sudo systemctl enable --now ntp
```

#### **B. Use Event-Time Processing**
- **Ignore system time**, use event timestamps (`event_timestamp` in Kafka).
```java
// Kafka Consumer with Event Time
Timestamp currentTimestamp = record.timestamp();
if (currentTimestamp.isBefore(lastProcessedTimestamp)) {
    logger.warn("Out-of-order event: " + currentTimestamp);
    // Optionally, buffer and reprocess
}
```

---

## **3. Debugging Tools & Techniques**

| **Tool**                     | **Purpose**                          | **Example Command/Setup** |
|------------------------------|---------------------------------------|---------------------------|
| **Kafka Consumer Groups CLI** | Check consumer lag & offsets          | `kafka-consumer-groups.sh` |
| **Kafka Manager**            | Monitor topic/partition health        | Web UI (https://kafka-manager.github.io) |
| **Prometheus + Grafana**     | Track CPU/memory/throughput            | Expose Kafka metrics |
| **JVM Profiler (Async Profiler)** | Find CPU bottlenecks | `async-profiler.sh` |
| **Redis CLI**                | Debug deduplication cache            | `redis-cli GET <key>` |
| **Schema Registry UI**       | Verify Avro/Protobuf schemas           | http://localhost:8081 |
| **Log Aggregator (ELK/Fluentd)** | Centralized logging for debugging | `logstash-filter` |

**Key Debugging Steps:**
1. **Check Kafka topic metrics** (`__consumer_offsets`, `kafka.server` metrics).
2. **Log message timestamps** (source vs. target).
3. **Test with a small dataset** before full migration.
4. **Use `kafka-console-consumer`** to inspect raw messages:
   ```bash
   kafka-console-consumer --bootstrap-server localhost:9092 \
     --topic migration-topic --from-beginning
   ```

---

## **4. Prevention Strategies**

### **1. Pre-Migration Checks**
✅ **Validate schema compatibility** (Avro/Protobuf).
✅ **Test with a subset of data** (e.g., 1% of records).
✅ **Ensure clock synchronization** (NTP).
✅ **Set up monitoring** (Prometheus + Alertmanager).

### **2. Runtime Safeguards**
🛡 **Enable dead-letter queues (DLQ)** for failed messages.
🛡 **Use idempotent processing** (avoid duplicate writes).
🛡 **Implement circuit breakers** for target system failures.
🛡 **Batch small records** to reduce overhead.

### **3. Post-Migration Validation**
🔍 **Run checksum comparison** between source & target.
🔍 **Check for missing/duplicate records** (write a validation query).
🔍 **Monitor for anomalies** in production (e.g., high error rates).

### **4. Rolling Back Safely**
- **If migration fails**, switch back to the old system.
- **Use a shadow database** for validation before full cutover.

---

## **5. Final Checklist Before Production**
| **Task**                          | **Status** |
|------------------------------------|------------|
| Schema compatibility verified      | ✅ / ❌     |
| Consumer group offsets initialized | ✅ / ❌     |
| DLQ configured                     | ✅ / ❌     |
| Clock synchronization checked      | ✅ / ❌     |
| Monitoring (Prometheus, Alerts)    | ✅ / ❌     |
| Small-scale test completed         | ✅ / ❌     |
| Rollback plan documented           | ✅ / ❌     |

---

## **Conclusion**
Streaming Migration is powerful but requires meticulous debugging. By following this guide, you can:
✔ **Identify partial transfers** (offsets, DLQ).
✔ **Fix duplicates** (idempotency, deduplication).
✔ **Reduce lag** (scaling, backpressure).
✔ **Prevent schema issues** (schema registry, backward compatibility).
✔ **Ensure clock alignment** (NTP, event-time processing).

**Next Steps:**
1. **Monitor key metrics** (consumer lag, error rates).
2. **Iterate on batch size** for optimal throughput.
3. **Automate rollback procedures**.

Would you like a **specific deep-dive** (e.g., Kafka tuning, database migration pitfalls)?