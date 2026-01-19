# Debugging **Stream Processing with Kafka Streams**: A Troubleshooting Guide

Streaming data processing, especially with **Kafka Streams**, enables real-time event processing but introduces unique challenges (e.g., late data, rebalancing, and transactional guarantees). This guide covers symptoms, common pitfalls, debugging tools, and prevention strategies to resolve issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, systematically check for these common symptoms:

| **Symptom**                     | **Possible Causes**                          |
|---------------------------------|---------------------------------------------|
| **Application crashes**         | Unhandled exceptions, OOM errors, or deadlocks |
| **Slow processing**             | Backpressure, low consumer lag, or inefficient joins |
| **Duplicate/out-of-order events** | Consumer lag, rebalancing, or incorrect timestamps |
| **Failed transactions (exactly-once)** | Transaction timeouts, dead letter queue issues |
| **Rebalancing spikes**          | Under-replicated partitions, broker failures |
| **Producer backpressure**       | High throughput + slow consumer processing  |
| **State store corruption**      | Uneven state partitioning, improper rebuilds |

---

## **2. Common Issues & Fixes**
### **Issue 1: High Consumer Lag & Slow Processing**
**Symptoms:**
- `kafka-consumer-groups --describe` shows high `LAG`.
- Logs show `poll()` taking >1s unnecessarily.

**Root Causes:**
- **Inefficient joins** (e.g., inner joins over large datasets).
- **Small batch size** (high overhead for small records).
- **State store thrashing** (frequent rebuilds due to uneven distribution).

**Fixes:**
```java
// Optimize batch size (default: 2048 records)
Properties props = new Properties();
props.put(StreamsConfig.DEFAULT_PROCESSING_GUARANTEE_CONFIG, "exactly_once");
props.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, "1000"); // Reduce commits for small batches
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, "exactly_once");

// Use windowed joins for large datasets
StreamsBuilder builder = new StreamsBuilder();
KStream<String, Integer> events = builder.stream("input");
events.groupByKey()
       .windowedBy(TimeWindows.of(Duration.ofSeconds(30)))
       .reduce(Integer::sum)
       .toStream();
```

**Debugging Steps:**
1. Check `kafka-consumer-groups` lag metrics.
2. Use **JMX metrics** (`kafka.streams.processing-rate`) to identify bottlenecks.
3. Profile CPU/memory usage (`jstack`, `VisualVM`).

---

### **Issue 2: Late Records & Out-of-Order Processing**
**Symptoms:**
- `println(record.key() + ":" + record.timestamp())` shows timestamp skew.
- Late data triggers `StreamsUncaughtExceptionHandler` (e.g., `TooLateException`).

**Root Causes:**
- **Clock skew** (client/server time misalignment).
- **Slow processing** (records expire before reprocessing).
- **Incorrect `timestamp-extractor`** (default: `WallClockTimestampExtractor`).

**Fixes:**
```java
// Use event-time processing with watermarks
builder.stream("input")
       .groupByKey()
       .windowedBy(TimeWindows.of(Duration.ofSeconds(30)).grace(Duration.ofSeconds(10)))
       .reduce(Integer::sum)
       .toStream();
```

**Debugging Steps:**
1. Verify `log4j` logs for watermark updates (`[StreamsApp] Watermark: 1000`).
2. Check `kafka-streams` JMX metrics (`kafka.streams.processing-rate` vs `kafka.streams.num-records-late`).

---

### **Issue 3: Failed Transactions (Exactly-Once Delivery)**
**Symptoms:**
- `KafkaStreamsException: Transactional id` errors.
- Duplicate records in downstream systems.

**Root Causes:**
- **Transaction timeout** (default: 60s, but processing may take longer).
- **Failed producer send** (network issues, broker unavailability).
- **Improper error handling** (e.g., swallowing `ProducerException`).

**Fixes:**
```java
// Increase transaction timeout (if processing is slow)
props.put(StreamsConfig.PRODUCER_TYPE_CONFIG, ProducerType.LOG_COMPACTED);
props.put(StreamsConfig.REPLICATION_FACTOR_CONFIG, 3);
props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.Integer().getClass());

// Handle failures gracefully
try {
    builder.stream("input").process((key, value, ctx) -> {
        // Logic here
        return KeyValue.pair(key, value * 2);
    }).to("output");
} catch (Exception e) {
    log.error("Processing failed", e);
    throw new RecordAlreadyProcessedException(); // Bypass commit
}
```

**Debugging Steps:**
1. Enable **transaction monitoring** in Kafka logs (`transactions.properties`).
2. Check **dead letter queue** (DLQ) for failed records.
3. Use `kafka-streams-console-producer` to test transactional sends.

---

### **Issue 4: Rebalancing Spikes & Consumer Crashes**
**Symptoms:**
- `kafka-streams` logs show `RebalanceListener` events.
- `ReassignedPartitionsEvent` triggers frequent state rebuilds.

**Root Causes:**
- **Broker failures** (under-replicated partitions).
- **Uneven state partitioning** (hot keys).
- **Small `num.stream.threads`** (default: `Runtime.getRuntime().availableProcessors()`).

**Fixes:**
```java
// Optimize thread count for skewed workloads
props.put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, 4);

// Use key serialization for even distribution
props.put(StreamsConfig.KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
props.put(StreamsConfig.VALUE_SERDE_CLASS_CONFIG, Serdes.Integer().getClass());
```

**Debugging Steps:**
1. Monitor **partition reassignments** (`kafka-topics --describe`).
2. Check **state store metrics** (`kafka.streams.cache-hit-rate`).
3. Use **`kafka-streams-console-consumer`** to verify partition assignment stability.

---

## **3. Debugging Tools & Techniques**
### **A. Kafka Streams CLI Tools**
| Tool | Purpose |
|------|---------|
| `kafka-streams-application-reset` | Reset state store (careful! use `--clean` only for testing) |
| `kafka-consumer-groups` | Check lag, rebalance status |
| `kafka-streams-topology-deserializer` | Debug topology structure |

**Example: Reset state store (dev only)**
```bash
kafka-streams-application-reset --bootstrap-server localhost:9092 \
  --application-id my-streams-app \
  --clean true
```

### **B. JMX Metrics Monitoring**
Key metrics to watch:
- `kafka.streams.processing-rate`
- `kafka.streams.num-records-late`
- `kafka.streams.cache-hit-rate` (state store efficiency)
- `kafka.streams.processing-rate` vs `kafka.streams.commits-per-second`

**Example: Use Prometheus + Grafana**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'kafka-streams'
    metrics_path: '/jmx'
    params:
      'output': ['text']
    static_configs:
      - targets: ['localhost:9757']
```

### **C. Logging & Stack Traces**
- **Enable DEBUG logs** for Kafka Streams:
  ```xml
  <logger name="org.apache.kafka.streams" level="DEBUG" />
  ```
- **Key log patterns**:
  - `Rebalance` → Check partition assignment.
  - `TooLateException` → Adjust watermark grace period.
  - `OOMError` → Increase `task.max.memory` (default: `64m`).

### **D. Unit Testing with `TestInputTopic`**
```java
@RunWith(KafkaStreamsTestDriveRunner.class)
public class MyStreamsTest {
    @Test
    public void testStreamProcessing() {
        StreamsTestDrive drive = new StreamsTestDrive();
        drive.setUp(new Properties()); // Configure streams

        // Simulate input
        drive.addInput("input", KeyValue.pair("key1", 1));
        drive.addInput("input", KeyValue.pair("key2", 2));

        // Process and verify
        drive.assertOutputEquals("output", Collections.singletonMap("key1", 2));
    }
}
```

---

## **4. Prevention Strategies**
### **A. Performance Tuning**
| Config | Default | Recommended |
|--------|---------|-------------|
| `num.stream.threads` | Cores | `2-4` (for skewed data) |
| `cache.max.bytes.buffering` | 64M | `256M-1G` (for large state) |
| `commit.interval.ms` | 30000 | `1000-5000` (reduce for low-latency) |
| `max.poll.interval.ms` | 5 min | `300000` (Kafka limit) |

### **B. Reliability Checks**
1. **Test with `kafka-reassign-partitions`**
   Simulate broker failures:
   ```bash
   kafka-reassign-partitions --bootstrap-server localhost:9092 \
     --reassignment-json-file reassignment.json \
     --execute
   ```
2. **Enable `interceptor` for monitoring**
   ```java
   props.put(ConsumerConfig.INTERCEPTOR_CLASSES_CONFIG,
             "io.confluent.monitoring.clients.interceptor.MonitoringConsumerInterceptor");
   ```
3. **Use `StreamThread` metrics** to detect hung tasks.

### **C. Schema & Data Validation**
- **Use Avro/Protobuf** for schema evolution:
  ```java
  props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG,
            ConfluentAvroSerde.class);
  ```
- **Validate records** before processing:
  ```java
  builder.stream("input")
         .filter((key, value) -> isValid(value))
         .process(...);
  ```

---

## **Summary of Key Fixes**
| Issue | Quick Fix | Long-Term Solution |
|-------|-----------|--------------------|
| High Lag | Increase `batch.size`, optimize joins | Redesign topology (e.g., use `windowed joins`) |
| Late Data | Adjust watermark grace period | Use event-time processing |
| Transaction Failures | Increase `transaction.timeout.ms` | Test with `kafka-streams-console-producer` |
| Rebalancing Spikes | Increase `num.stream.threads` | Monitor broker health |

---
**Final Tip:** For production issues, always:
1. Check **Kafka broker logs** (`/var/log/kafka/server.log`).
2. Use **`kafka-streams-topology-deserializer`** to inspect the live topology.
3. Reproduce in a **dev environment** with `TestInputTopic`.

By following this guide, you can quickly diagnose and resolve Kafka Streams issues while preventing recurrence.