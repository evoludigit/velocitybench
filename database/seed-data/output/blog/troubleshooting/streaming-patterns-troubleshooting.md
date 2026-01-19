# **Debugging Streaming Patterns: A Troubleshooting Guide**
**Author:** Senior Backend Engineer
**Last Updated:** [Date]

---
## **1. Introduction**
Streaming patterns (e.g., **Kafka Streams, Flink, Spark Streaming, or real-time event processing pipelines**) are essential for building scalable, low-latency data pipelines. However, they introduce unique challenges: **event order anomalies, backpressure, state management issues, and network partitions**.

This guide provides a structured approach to diagnosing and resolving common streaming-related issues.

---

## **2. Symptom Checklist**
Before diving into fixes, verify the following symptoms:

| **Symptom Category**       | **Specific Symptoms**                                                                 |
|----------------------------|--------------------------------------------------------------------------------------|
| **Data Loss / Duplication** | Missing records, duplicate events, or incomplete window aggregations.                |
| **Performance Issues**     | Slow processing, timeouts, or backpressure accumulation (e.g., buffer overflows).     |
| **State Corruption**       | Incorrect aggregations, stale state, or inconsistent results.                        |
| **Network / Connectivity** | Timeouts, broker connectivity drops, or increased retry attempts.                    |
| **Ordering Issues**        | Out-of-order events in consumer processing or windowed aggregations.                 |
| **Resource Exhaustion**     | High CPU/memory usage, OOM errors, or container crashes.                              |
| **Schema Mismatch**        | Serialization errors (e.g., Avro/JSON parsing failures) or version incompatibility.  |

**Action:** Check logs (`ERROR`, `WARN`, `INFO`) and monitoring dashboards (Prometheus, Grafana) before proceeding.

---

## **3. Common Issues and Fixes**

### **3.1 Data Loss / Duplication**
#### **Issue: Missing Events in Processing**
- **Root Cause:**
  - Consumer lag exceeds rebalance threshold (Kafka Streams/Flink).
  - Manual commits without `exactly-once` semantics.
  - Windowed aggregations dropping late data (e.g., `tumblingWindow` with `allowedLateness` misconfigured).

#### **Fixes:**
**Kafka Streams (Java)**
```java
// Enable exactly-once processing
Properties props = new Properties();
props.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, 1000);
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, ProcessingGuarantee.EXACTLY_ONCE);

// For windowed aggregations, allow late data
StreamBuilder builder = new StreamBuilder();
KTable<Key, Value> windowedTable = builder.table("input-topic")
    .groupByKey()
    .windowedBy(TimeWindows.of(Duration.ofMinutes(5)))
    .aggregate(...)
    .allowedLateness(Duration.ofMinutes(2)); // Add buffer for late data
```

**Apache Flink (Java)**
```java
// Ensure event time processing with watermarks
DataStream<Event> events = env.addSource(source)
    .assignTimestampsAndWatermarks(
        WatermarkStrategy
            .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(3))
            .withTimestampAssigner((event, ts) -> event.getTimestamp())
    );

// Use state backend with checkpointing
events.keyBy(Event::getKey)
    .window(TumblingEventTimeWindows.of(Time.seconds(60)))
    .aggregate(new MyAggregateFunction())
    .addSink(sink);
```

---

#### **Issue: Duplicate Events**
- **Root Cause:**
  - Consumer rebalances due to broker failures (Kafka).
  - Retries on transient failures (e.g., network issues).
  - Idempotent producers not enforced (Kafka `enable.idempotence=true`).

#### **Fixes:**
**Kafka Producer (Idempotent Setting)**
```java
Properties props = new Properties();
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
props.put(ProducerConfig.ACKS_CONFIG, "all");
props.put(ProducerConfig.RETRIES_CONFIG, Integer.MAX_VALUE);
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, "5");
```

**Consumer-Side Deduplication (Kafka Streams)**
```java
// Use a state store for tracking processed keys
Stores.Builder<KeyValueStore<String, Boolean>> storeBuilder =
    Stores.keyValueStoreBuilder(
        Stores.persistentKeyValueStore("dedup-store"),
        Serdes.String(),
        Serdes.Boolean());

KStream<String, String> stream = builder.stream("input-topic", Consumed.with(...))
    .filter((key, value) -> {
        KeyValueStore<String, Boolean> dedupStore = context.getStateStore(storeBuilder.build().name());
        if (dedupStore.get(key) != null) {
            return false; // Skip duplicates
        }
        dedupStore.put(key, true);
        return true;
    });
```

---

### **3.2 Performance Issues (Backpressure & Latency)**
#### **Issue: Backpressure Accumulation**
- **Root Cause:**
  - Consumer lag > producer speed (Kafka).
  - Slow downstream processing (e.g., DB writes, external API calls).
  - Small batch sizes or inefficient serializers.

#### **Fixes:**
**Kafka Streams (Adjust Processing config)**
```java
props.put(StreamsConfig.CACHE_MAX_BYTES_BUFFERING_CONFIG, 104857600); // 100MB
props.put(StreamsConfig.FETCH_MIN_BYTES_CONFIG, 1); // Reduce fetch overhead
props.put(StreamsConfig.FETCH_MAX_WAIT_MS_CONFIG, 500); // Balance latency/throughput
```

**Flink (Dynamic Scaling & Parallelism)**
```java
// Enable incremental checkpointing
env.enableCheckpointing(1000); // 1s interval
env.getCheckpointConfig().setCheckpointStorage("file:///checkpoints");

// Scale parallelism based on load
env.setParallelism(new RuntimeContext() {
    @Override
    public int getParallelism() {
        return Runtime.getRuntime().availableProcessors() * 2;
    }
});
```

**Monitoring Backpressure (Flink)**
```bash
# Check backpressure metrics in Flink UI or CLI
flink list | grep "backpressure"
```

---

### **3.3 State Management Issues**
#### **Issue: State Corruption / Stale Data**
- **Root Cause:**
  - Failed checkpoints (Flink/Kafka Streams).
  - State store not persisted (` RocksDB` misconfigured).
  - Manual state updates without transactions.

#### **Fixes:**
**Flink (Restore from Checkpoint)**
```bash
# Restart Flink job with --restartStrategy=fixed-delay-timeout
# Or restore manually from saved state directory
./bin/flink run \
  --restart-strategy=fixed-delay-timeout \
  --jobmanager.memory.process.size=4096m \
  -m localhost:8081 \
  /path/to/job.jar
```

**Kafka Streams (State Store Cleanup)**
```java
// Ensure state store is configured for persistence
Stores.Builder<KeyValueStore<String, Long>> storeBuilder =
    Stores.persistentKeyValueStore("count-store"); // Auto-cleanup on restart
builder.addStateStore(storeBuilder.build());
```

**Idempotent State Updates**
```java
// Use transactional writes (Kafka Streams)
KafkaStreams streams = new KafkaStreams(builder.build(), props);
streams.start();
streams.cleanUp(); // Clean up incomplete state
```

---

### **3.4 Network / Connectivity Problems**
#### **Issue: Broker Timeouts or Partitions**
- **Root Cause:**
  - Kafka broker unreachable (network split brain).
  - Consumer lag > rebalance threshold (`session.timeout.ms` too low).
  - Schema registry unavailable (Avro/Protobuf serialization).

#### **Fixes:**
**Kafka Consumer (Increase Timeouts)**
```java
props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, 30000); // 30s
props.put(ConsumerConfig.HEARTBEAT_INTERVAL_MS_CONFIG, 10000);
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500); // Reduce fetch overhead
```

**Schema Registry (Fallback Handling)**
```java
// Use a try-catch for schema resolution (Avro)
try {
    GenericRecord record = serializer.deserialize(value, GenericRecord Creator);
} catch (SchemaException e) {
    log.error("Schema mismatch, falling back to raw JSON", e);
    return handleFallback(value);
}
```

---

### **3.5 Ordering Issues (Event Time vs Processing Time)**
#### **Issue: Late Data in Windowed Aggregations**
- **Root Cause:**
  - Watermark generation too slow (e.g., no timestamp extractor).
  - `allowedLateness` too short for real-world delays.

#### **Fixes:**
**Kafka Streams (Event Time + Late Data Handling)**
```java
// Define a timestamp extractor
TimestampExtractor<Event> extractor = (event, timestamp) -> event.getEventTime();

// Configure watermark interval
props.put(StreamsConfig.DEFAULT_TIMESTAMP_EXTRACTOR_CLASS_CONFIG, extractor);
props.put(StreamsConfig.DEFAULT_TIMESTAMP_EXTRACTOR_BATCH_DELAY_MS_CONFIG, 500);

// Allow late data
builder.table("input-topic", Consumed.with(...))
    .groupByKey()
    .windowedBy(TimeWindows.of(Duration.ofMinutes(5)))
    .aggregate(new MyAggregate(), Materialized.with(...))
    .allowedLateness(Duration.ofMinutes(10));
```

**Flink (Ascending Watermarks)**
```java
// Use periodic watermarks with bounded out-of-orderness
SingleOutputStreamOperator<Event> events = env.addSource(source)
    .assignTimestampsAndWatermarks(
        WatermarkStrategy
            .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
            .withTimestampAssigner((event, ts) -> event.getTimestamp())
    );
```

---

## **4. Debugging Tools and Techniques**

### **4.1 Log Analysis**
- **Kafka Streams/Flink:**
  - Check `application.log` for `TaskManager`/`Worker` errors.
  - Look for `REBALANCE`, `BACKPRESSURE`, or `CHECKPOINT` logs.
- **Example Log Patterns:**
  ```
  [ERROR] Task [1] failed: java.io.IOException: State backend failed
  [WARN] Watermark is slower than expected (current: 100s, expected: 50s)
  ```

### **4.2 Metrics and Dashboards**
| **Tool**          | **Key Metrics to Monitor**                          |
|--------------------|----------------------------------------------------|
| **Kafka Streams**  | `records-lag`, `processing-time`, `commit-rate`    |
| **Flink**          | `numRecordsIn/Out`, `latency`, `backpressure`       |
| **Prometheus**     | `kafka_consumer_lag`, `flink_task_backpressure`     |
| **Grafana**        | Custom dashboards for `watermark`, `state-size`     |

**Query Example (PromQL):**
```promql
rate(kafka_consumer_lag{topic="input-topic"}[1m]) > 1000
```

### **4.3 Interactive Debugging**
**Kafka Streams CLI:**
```bash
# List consumer groups
kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Describe group for a topic
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-group --describe --topic input-topic
```

**Flink Web UI:**
- Navigate to `http://<jobmanager>:8081` to inspect:
  - **Vertices** (data sources/sinks).
  - **Backpressure indicators** (red/yellow bars).
  - **Checkpoint durations**.

### **4.4 Unit Testing**
**Kafka Streams (TestContainer + Mocks)**
```java
@Test
public void testWindowedAggregate() {
    TestInputTopic<String, String> input = new TestInputTopic<>(
        streamsMockBuilder, "input-topic"
    );

    input.addRecord("key1", "value1");
    input.addRecord("key1", "value2");

    KTable<String, Long> result = streamsMockBuilder.table("input-topic");
    assertEquals(2, result.get("key1").getValue());
}
```

---

## **5. Prevention Strategies**

### **5.1 Configuration Best Practices**
| **Component**       | **Recommendation**                                                                 |
|----------------------|-------------------------------------------------------------------------------------|
| **Kafka**            | Enable `idempotence`, `acks=all`, and monitor `under-replicated-partitions`.         |
| **Kafka Streams/Flink** | Use `exactly-once` processing, proper `timestamp.extractor`, and `checkpointing`. |
| **State Stores**     | Configure `RocksDB` compaction (`writeBufferSizeMB`, `maxOpenFiles`).                |
| **Network**          | Use TLS for broker-to-broker communication; monitor `request-lag`.                  |

### **5.2 Design Patterns**
- **Idempotent Sinks:** Ensure downstream writes (DBs, APIs) handle duplicates.
  ```java
  // Example: Upsert in PostgreSQL
  String upsertSql = "INSERT INTO table (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value";
  ```
- **Circuit Breakers:** Fail fast on downstream failures (e.g., Resilience4j for Flink).
  ```java
  @Bean
  public CircuitBreaker circuitBreaker() {
      return CircuitBreaker.ofDefaults("db-breaker");
  }
  ```

### **5.3 Monitoring and Alerts**
- **Key Alerts:**
  - Kafka consumer lag > threshold (`10% of total partitions`).
  - Flink checkpoint failures (`lastCheckpointDuration > 5s`).
  - State store growth (`> 80% of disk space`).
- **Tools:**
  - **Prometheus Alertmanager** for SLO violations.
  - **Kafka Lag Exporter** for consumer lag alerts.

### **5.4 Disaster Recovery**
- **Backup State:**
  - **Flink:** Savepoints (`flink savepoint <jobId>`).
  - **Kafka Streams:** Manually save state store snapshots.
- **Restart Strategy:**
  ```yaml
  # Flink restart config (flink-conf.yaml)
  restart-strategy: fixed-delay-timeout
  restart-delay: 10s
  timeout: 1m
  ```

---

## **6. Quick Reference Table**
| **Issue**               | **Root Cause**               | **Immediate Fix**                          | **Long-Term Fix**                          |
|-------------------------|------------------------------|--------------------------------------------|--------------------------------------------|
| Data loss               | Consumer lag > rebalance     | Increase `fetch.max.bytes`                 | Enable `exactly-once` + `allowedLateness`   |
| Duplicates              | Idempotence disabled         | Enable `enable.idempotence=true`           | Add deduplication state store              |
| Backpressure            | Slow processing              | Scale parallelism                          | Optimize downstream (batch DB writes)      |
| Stale state             | Failed checkpoint            | Manually restore from savepoint            | Test state recovery + monitoring           |
| Network timeout         | Broker unreachable           | Increase `session.timeout.ms`              | Use TLS + retry policies                   |
| Late data               | Watermark too slow           | Increase `allowedLateness`                 | Adjust `timestamp.extractor` + buffering   |

---
## **7. Conclusion**
Streaming patterns are powerful but require **proactive monitoring, idempotent designs, and robust error handling**. Follow this guide to:
1. **Diagnose** issues using logs, metrics, and debugging tools.
2. **Fix** problems with targeted configuration changes.
3. **Prevent** recurrences via best practices and automated alerts.

**Further Reading:**
- [Kafka Streams Best Practices](https://kafka.apache.org/documentation/streams/developer-guide)
- [Flink State Backend Guide](https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/state_backends/)
- [Real-Time Data Pipelines Anti-Patterns](https://www.oreilly.com/library/view/real-time-data/9781491943351/)

---
**Last Updated:** [MM/YYYY]
**Version:** 1.2 (Added Flink 1.16+ optimizations)