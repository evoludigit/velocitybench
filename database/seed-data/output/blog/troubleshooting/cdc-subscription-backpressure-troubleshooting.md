# **Debugging CDC (Change Data Capture) Backpressure Handling: A Troubleshooting Guide**

## **Introduction**
Change Data Capture (CDC) systems process high-volume streams of database changes (inserts, updates, deletes) in near real-time. When subscribers (consumers) cannot keep up with the ingestion rate, **backpressure** occurs—leading to queue buildup, slower processing, or even system overload.

This guide provides a structured approach to diagnosing, fixing, and preventing backpressure issues in CDC systems.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which symptoms align with your issue:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| **Queue Length Growth**              | CDC log/queue (e.g., Kafka, Debezium, Kafka Connect) grows continuously.       |
| **Slow Consumer Processing**         | Consumers take longer than expected to process events (latency spikes).          |
| **Consumer Lag**                     | Event time lag between producer and consumer increases (e.g., "Lag: 10,000+"). |
| **Resource Exhaustion**              | High CPU, memory, or disk usage in producers/consumers.                         |
| **Timeout Errors**                   | Consumers fail due to timeouts (e.g., `TimeoutException`, `PollTimeoutException`). |
| **Producer Backlog**                 | CDC producer (e.g., Debezium, Kafka Connect) buffers more events than usual.    |
| **Slow Database WAL Replication**    | CDC source (e.g., PostgreSQL WAL, MySQL binlog) lags behind commits.            |

---
**Quick Check:**
- **Is the queue growing?** → Likely producer/consumer mismatch.
- **Are consumers lagging?** → Consumer performance issue.
- **Are timeouts frequent?** → Resource constraint or inefficient processing.

---

## **2. Common Issues and Fixes**

### **Issue 1: Consumer Cannot Keep Up with Ingestion Rate**
**Symptoms:**
- High consumer lag (`kafka-consumer-groups.sh --describe` shows large lag).
- Queue length increases despite running consumers.

**Root Cause:**
- Consumers are slower than producers (e.g., heavy processing, inadequate scaling).
- Network throttling or slow downstream systems.

**Fixes:**

#### **A. Scale Consumers Horizontally**
- **Add more consumer instances** (partition-based scaling).
- **Example (Kafka Consumer):**
  ```java
  // Increase parallelism (per-partition)
  props.put(ConsumerConfig.PARTITION_ASSIGNMENT_STRATEGY_CONFIG, DefaultPartitionAssignment.class.getName());
  props.put(ConsumerConfig.GROUP_ID_CONFIG, "my-group");
  ```
  - **Key:** Ensure partitions are evenly distributed.

#### **B. Optimize Consumer Processing**
- **Batch processing** (reduce per-event overhead):
  ```java
  props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500); // Default: 500
  ```
- **Async processing** (avoid blocking calls):
  ```java
  // Example: Async DB upsert
  CompletableFuture.runAsync(() -> {
      dbService.save(event);
  });
  ```

#### **C. Monitor & Auto-Scale (Kubernetes Example)**
```yaml
# HPA (Horizontal Pod Autoscaler) for Kafka consumers
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cdc-consumer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cdc-consumer
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

### **Issue 2: Producer Backlog Due to Slow Database Replication**
**Symptoms:**
- WAL (Write-Ahead Log) or binlog replay lag (`SHOW SLAVE STATUS` in MySQL).
- Debezium/Kafka Connect source connector stalls.

**Root Cause:**
- Database replication is slower than CDC ingestion.
- Poorly tuned CDC source (e.g., Debezium batching).

**Fixes:**

#### **A. Adjust Debezium Batching**
```yaml
# Increase batch size (if high throughput)
batchSize: 1000
# Reduce batch timeout (if latency is critical)
maxBatchSize: 10000
pollIntervalMs: 1000
```
- **Trade-off:** Larger batches reduce overhead but increase latency.

#### **B. Optimize Database Replication**
- **For PostgreSQL:** Tune `wal_level` and `max_replication_slots`.
  ```sql
  ALTER SYSTEM SET wal_level = replica;
  ALTER SYSTEM SET max_replication_slots = 10;
  ```
- **For MySQL:** Increase `binlog_row_image` and `replicate-wild-do`.
  ```ini
  [mysqld]
  binlog_row_image = FULL
  replicate-ignore-table=db.ignored_table
  ```

---

### **Issue 3: Network or Broker Bottlenecks**
**Symptoms:**
- High `request.queue.time.ms` in Kafka broker metrics.
- `ProducerRecord` timeouts (`RecordTooLargeException`).

**Root Cause:**
- Kafka broker overwhelmed by CDC traffic.
- Network latency between producer/consumer.

**Fixes:**

#### **A. Monitor Kafka Broker Metrics**
```bash
# Check broker load
kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```
- **Key metrics:**
  - `UnderReplicatedPartitions` (replication lag).
  - `RequestQueueTimeAvg` (network delays).

#### **B. Scale Kafka Brokers**
- Add more brokers to distribute load.
- Example Kubernetes deployment:
  ```yaml
  resources:
    requests:
      cpu: "2"
      memory: "4Gi"
    limits:
      cpu: "4"
      memory: "8Gi"
  ```

#### **C. Adjust Kafka Producer/Sender Settings**
```java
// Reduce send buffer (if network slow)
props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 33554432); // 32MB
props.put(ProducerConfig.LINGER_MS_CONFIG, 5); // Wait up to 5ms for batching
```

---

### **Issue 4: Consumer Crashes or Timeouts**
**Symptoms:**
- `PollTimeoutException` or `WakeupException`.
- Consumers restart frequently (`kafka-consumer-groups.sh --describe` shows dead groups).

**Root Cause:**
- Unhandled exceptions in consumer logic.
- Resource constraints (OOM, CPU throttling).

**Fixes:**

#### **A. Add Retry & Dead Letter Queue (DLQ)**
```java
// Example: Retry with exponential backoff
RetryPolicy retryPolicy = RetryPolicy.builder()
    .maxRetries(3)
    .retryInterval(Duration.ofSeconds(1))
    .build();

try {
    processEvent(event);
} catch (Exception e) {
    retryPolicy.onError(e);
    dlqService.sendToDLQ(event); // Send to DLQ
}
```

#### **B. Graceful Shutdown Handling**
```java
// Prevent abrupt shutdowns
Runtime.getRuntime().addShutdownHook(new Thread(() -> {
    consumer.wakeup(); // Gracefully exit poll loop
}));
```

---

## **3. Debugging Tools and Techniques**

### **A. Logging & Metrics**
- **Kafka Consumer Lag Monitoring:**
  ```bash
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group my-group --describe
  ```
- **Debezium Logs:** Check `ConnectorConfig.TOPIC_PREFIX` logs for errors.

### **B. Profiling Tools**
- **JVM Profiling:**
  - **Async Profiler** for CPU bottlenecks.
  - **VisualVM** for memory leaks.
- **Kafka Metrics:**
  - `kafka-producer-perf-test.sh` (load testing).
  - `kafka-consumer-perf-test.sh` (benchmarking).

### **C. Tracing (Distributed Debugging)**
- **OpenTelemetry + Jaeger** to trace CDC flow:
  ```java
  // Add OTLP instrumentation
  OpenTelemetrySdk.initialize(SDKBuilder.fromConfig(config));
  ```

---

## **4. Prevention Strategies**

| **Strategy**               | **Action**                                                                 |
|----------------------------|----------------------------------------------------------------------------|
| **Right-Sizing Partitions** | Start with `2x` consumers per partition; adjust based on lag.            |
| **Load Testing**           | Simulate CDC traffic with `kafka-producer-perf-test.sh`.                 |
| **Alerting**               | Set up alerts for: <br> - `Lag >= 10,000` <br> - `ProducerQueueSize > 1GB` |
| **Circuit Breakers**       | Implement retry logic with `Resilience4j`.                                 |
| **Schema Evolution**       | Use Avro/Protobuf with backward-compatible schema changes.                |
| **Resource Limits**        | Set container resource requests/limits (Kubernetes HPA).                  |

---
**Example Alert Rule (Prometheus):**
```yaml
- alert: HighCDCBackpressure
  expr: kafka_consumer_lag > 10000
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "CDC Consumer {{ $labels.group }} is lagging ({{ $value }} messages)"
```

---

## **5. Conclusion**
CDC backpressure is typically resolved by:
1. **Scaling consumers** (horizontal scaling).
2. **Optimizing producer bottlenecks** (Debezium tuning, database replication).
3. **Improving consumer reliability** (retries, DLQ, graceful shutdowns).
4. **Monitoring and alerting** proactively.

**Next Steps:**
- Start with **queue length checks** (`kafka-consumer-groups.sh`).
- If lag persists, **scale consumers** or **optimize processing**.
- For producers, **tune Debezium/Kafka Connect** and **database replication**.

By following this guide, you can systematically diagnose and resolve CDC backpressure issues efficiently.