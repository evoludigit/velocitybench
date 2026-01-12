# **Debugging CDC (Change Data Capture) Archival Strategy: A Troubleshooting Guide**

## **1. Introduction**
The **CDC Archival Strategy** pattern is used to store long-term change logs (e.g., for audit trails, compliance, or replayable event sources) by archiving CDC data to a durable, scalable storage system. Common issues include slow archival, failed writes, storage bloat, and inconsistencies between the source and archival store.

This guide provides a structured approach to diagnosing and resolving issues efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, verify the following symptoms:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| Slow archival throughput | Archival lag grows over time, affecting CDC reprocessing speed. | Degrades event replayability. |
| Failed archival writes | Errors in log files or metrics indicating write failures (e.g., `StorageFullError`, `NetworkTimeout`). | Data loss risk if not handled. |
| Inconsistent archival state | Replayed events don’t match database state (e.g., missing updates in archival). | Compliance/audit risks. |
| Storage bloat | Archival storage grows uncontrollably (e.g., unmanaged partitions, duplicate logs). | Higher costs, slower queries. |
| High CPU/memory usage | Archival workers consume excessive resources (e.g., due to inefficient serialization). | System instability. |
| Timeouts in CDC pipeline | Archival step hangs or exceeds processing timeouts (e.g., `RequestTimeout`). | CDC pipeline stalls. |
| Corrupted archived data | Reads from archival return malformed or invalid data. | Data accuracy issues. |

**Action:** If any symptom matches, proceed to diagnosis.

---

## **3. Common Issues & Fixes**

### **Issue 1: Slow Archival Throughput**
**Root Cause:**
- Archival workers overwhelmed by high-volume CDC streams.
- Inefficient serialization/deserialization (e.g., JSON vs. Protocol Buffers).
- Network bottlenecks between CDC source and archival store.

**Fixes with Code Examples**

#### **Optimize Serialization**
Replace verbose JSON with efficient binary formats (e.g., Avro, Protobuf).

**Before (JSON):**
```java
// Slow JSON serialization
String json = new ObjectMapper().writeValueAsString(cdcRecord);
```

**After (Avro):**
```java
// Faster Avro serialization
Binary avroRecord = new GenericDateline().toByteArray(cdcRecord);
```

#### **Scale Archival Workers**
Use a task queue (e.g., Kafka, RabbitMQ) to parallelize writes.

**Kafka-Based Archival:**
```python
# Consumer group distributes writes across workers
from confluent_kafka import Consumer
consumer = Consumer({'bootstrap.servers': 'kafka:9092', 'group.id': 'archival'})
while True:
    msg = consumer.poll(timeout=1.0)
    if msg.value():
        store_archival(msg.value())  # Parallel writes
```

#### **Monitor & Throttle**
Add adaptive backpressure using metrics.

```go
// Throttle if archival lag > threshold
const maxLag = 1000
if pendingArchives > maxLag {
    time.Sleep(100 * time.Millisecond)  // Backpressure
}
```

---

### **Issue 2: Failed Archival Writes**
**Root Causes:**
- Storage quota exceeded.
- Network partitions (e.g., S3/HDFS cluster outages).
- Schema mismatches (e.g., new fields added to CDC records).

**Fixes**

#### **Handle Storage Full Errors**
Implement exponential backoff + retry.

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def write_to_archive(data):
    try:
        s3-client.put_object(Bucket="archives", Key="data.json", Body=data)
    except ClientError as e:
        if e.response['Error']['Code'] == 'RequestThrottled':
            raise  # Stop retrying if throttled
        raise
```

#### **Validate Schema Compatibility**
Use schema registry (e.g., Avro/Protobuf) to enforce compatibility.

```java
// Avro schema validation
Schema avroSchema = new Schema.Parser().parse(new File("schema.avsc"));
try {
    avroSchema.validate(cdcRecord);  // Throws if incompatible
} catch (SchemaParseException e) {
    log.error("Schema mismatch: " + e.getMessage());
}
```

---

### **Issue 3: Inconsistent Archival State**
**Root Cause:**
- Lag between CDC captures and archival writes.
- Transaction rollbacks not reflected in archival.

**Fixes**

#### **Use Transactional CDC**
Ensure atomicity between source writes and archival.

```sql
-- PostgreSQL logical decoding with XID tracking
CREATE PUBLICATION archival_pub FOR TABLE users WITH (publish=insert, update);
-- Archive with transactional consistency
BEGIN;
INSERT INTO archival_table SELECT * FROM pg_logical_slot_get_changes(...);
COMMIT;
```

#### **Replay from Checkpoint**
If inconsistencies occur, replay from the latest archival checkpoint.

```python
# Replay from last archival offset
def replay_from_checkpoint(last_offset):
    for msg in source_stream.consumer(bootstrap_server="kafka", offset=last_offset):
        if msg.value() not in archival:
            store_archival(msg.value())  # Catch-up
```

---

### **Issue 4: Storage Bloat**
**Root Cause:**
- Unmanaged partitioning (e.g., no TTL).
- Duplicate logs due to retries.

**Fixes**

#### **Implement TTL Policies**
Use S3 Object Lock or DynamoDB TTL to auto-delete old logs.

```python
# DynamoDB TTL example
dynamodb.Table("archival").put_item(
    Item={
        "id": "record_123",
        "data": {...},
        "expires_at": int(time.time() + 86400)  # 24h TTL
    },
    ConditionExpression="attribute_not_exists(id)"
)
```

#### **Deduplicate Logs**
Track seen offsets/IDs to avoid reprocessing.

```python
seen_ids = set()
for record in cdc_stream:
    if record.id not in seen_ids:
        seen_ids.add(record.id)
        store_archival(record)
```

---

### **Issue 5: High Resource Usage**
**Root Cause:**
- Bulk inserts without batching.
- Inefficient storage engine (e.g., slow DB writes).

**Fixes**

#### **Batch Writes**
Use bulk inserts (e.g., JDBC batch, S3 multi-part upload).

```java
// JDBC batch insert
Connection conn = DriverManager.getConnection(url);
try (PreparedStatement stmt = conn.prepareStatement("INSERT ...", Statement.RETURN_GENERATED_KEYS)) {
    for (Object record : cdcBatch) {
        stmt.addBatch();
    }
    stmt.executeBatch();  // Single roundtrip
}
```

#### **Use Efficient Storage**
For high throughput, use:
- **S3/HDFS** (for cold storage).
- **DynamoDB** (for semi-structured data).
- **TimescaleDB** (for time-series archival).

---

## **4. Debugging Tools & Techniques**
### **A. Logging & Metrics**
- **Metrics to Track:**
  - `archival_latency` (P99 time to write).
  - `archival_errors` (failed writes per minute).
  - `storage_size` (current archival storage usage).
- **Tools:**
  - Prometheus + Grafana (for metrics).
  - ELK Stack (for logs).

**Example Metrics Query:**
```promql
rate(archival_errors_total[1m]) > 0  # Alert on errors
```

### **B. Distributed Tracing**
Use Jaeger/Zipkin to trace CDC → Archival flow.

```java
// Jaeger instrumentation
Tracer tracer = JaegerTracer.builder()
    .serviceName("archival-service")
    .build();
SpanContext context = tracer.extract(PropagationContext.fromHeaders(headers));
try (Span span = tracer.buildSpan("archive_write").asChildOf(context).startScope()) {
    // Write logic
}
```

### **C. Data Validation**
- **Checksums:** Hash archived payloads to detect corruption.
  ```python
  import hashlib
  def verify_checksum(data: bytes, expected_hash: str) -> bool:
      return hashlib.sha256(data).hexdigest() == expected_hash
  ```
- **Sampling:** Compare a sample of archived vs. source data.

### **D. Load Testing**
Simulate high-volume CDC to find bottlenecks.

```bash
# Use Kafka Producer to flood archival pipe
kafka-producer-perf-test \
  --topic cdc_topic \
  --record-size 1KB \
  --throughput -1 \
  --num-records 100000 \
  --producer-props bootstrap.servers=localhost:9092
```

---

## **5. Prevention Strategies**
### **A. Design-Time Mitigations**
1. **Partitioning Strategy:**
   - Use time-based partitioning (e.g., `year=2023/month=05/day=15` in S3).
   - Avoid "all-in-one" tables (use sharding if needed).

2. **Schema Evolution:**
   - Use schema registry (e.g., Confluent Schema Registry) to manage backward compatibility.

3. **Resource Planning:**
   - Size archival storage based on CDC volume (e.g., 3x current throughput).

### **B. Runtime Safeguards**
1. **Circuit Breakers:**
   - Stop archival if storage is degraded (e.g., using Hystrix).
   ```java
   @CircuitBreaker(name="archivalStore", fallbackMethod="fallbackArchive")
   public void archiveRecord(Record record) { ... }
   ```

2. **Dead Letter Queue (DLQ):**
   - Route failed archival attempts to a DLQ for manual review.
   ```python
   # Kafka DLQ example
   dlq_producer = KafkaProducer({"bootstrap.servers": "kafka:9092"})
   dlq_producer.send("archival-dlq", value=failed_record)
   ```

3. **Automated Retries with Exponential Backoff:**
   - Use libraries like `retry` (Python) or `Resilience4j` (Java).

### **C. Monitoring & Alerting**
1. **Key Alerts:**
   - `archival_lag > 5min` (slows replayability).
   - `storage_usage > 90%` (risk of outages).
   - `error_rate > 1%` (data integrity risk).

2. **Tools:**
   - **Prometheus Alertmanager** (for metrics).
   - **Datadog** (for distributed tracing).

### **D. Backup & Recovery**
1. **Cross-Region Replication:**
   - Use S3 Cross-Region Replication or DynamoDB Global Tables.
2. **Point-in-Time Recovery:**
   - For DB-based archival, enable WAL archiving (PostgreSQL) or binlog backup (MySQL).

---

## **6. Summary Checklist for Resolution**
| **Step** | **Action** |
|----------|------------|
| **1. Identify Symptoms** | Check logs/metrics for `archival_latency`, `errors`, `storage_size`. |
| **2. Isolate Root Cause** | Compare source vs. archival data; check for TTL violations. |
| **3. Apply Fix** | Optimize serialization, batch writes, or scale workers. |
| **4. Validate** | Replay archived data; verify checksums. |
| **5. Prevent Recurrence** | Add metrics, DLQ, and circuit breakers. |

---
**Final Tip:** Start with **metrics** (slow archival?) → **logs** (failed writes?) → **data validation** (inconsistencies?). Move methodically from observations to fixes.

Would you like a deeper dive into any specific area (e.g., DynamoDB optimizations)?