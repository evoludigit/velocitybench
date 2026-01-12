# **Debugging CDC (Change Data Capture) Real-Time Metrics: A Troubleshooting Guide**

## **Overview**
This guide provides a structured approach to diagnosing and resolving issues with **CDC Real-Time Metrics**, a pattern that captures and streams changes from databases (via CDC) to compute live metrics in real time. The goal is to help engineers quickly identify bottlenecks, misconfigurations, or failures in the CDC pipeline.

---

## **1. Symptom Checklist**
Before diving into fixes, verify the following symptoms:

| **Symptom** | **Description** | **Indicators** |
|-------------|----------------|----------------|
| **No Metrics Emitted** | CDC pipeline is running, but no metrics appear in the destination (e.g., Prometheus, Kafka topic, or custom sink). | - No logs in Prometheus/Promtail or Kafka consumer. <br> - CDC consumer process is alive but not processing data. |
| **Delayed Metrics** | Metrics arrive much later than expected (e.g., minutes/hours instead of near real-time). | - Log timestamps show CDC lag (`last_checkpoint_ts`, `current_watermark`). <br> - Consumer lag metrics (e.g., `kafka_consumer_lag`) are high. |
| **Partial Metrics** | Only some CDC events are processed, while others are dropped. | - Missing records in the sink compared to the source. <br> - Error logs showing `retry failures` or `partition out of range`. |
| **High Latency in Metrics Processing** | Metrics are slow to compute (e.g., aggregations take too long). | - Long-running queries in the metrics processor. <br> - High CPU/memory usage in the metrics backend. |
| **Duplicates or Missing States** | Metrics show duplicate values or incorrect aggregations (e.g., missing updates). | - Logs showing `duplicate key detected` or `state mismatch`. <br> - Inconsistent metric values across restarts. |
| **Resource Exhaustion** | System crashes due to OOM, high CPU, or disk I/O bottlenecks. | - Crash logs (`java.lang.OutOfMemoryError`, `disk full`). <br> - High `system load average` or `CPU usage`. |

---

## **2. Common Issues & Fixes**

### **A) No Metrics Emitted**
#### **Root Cause 1: CDC Connection Failed**
- The CDC consumer (e.g., Debezium, Kafka Connect) cannot connect to the source database.
- **Fix:**
  - Check database connection settings (`jdbc.url`, `username`, `password`).
  - Verify network connectivity (e.g., VPC peering, firewall rules).
  - Example (Debezium config for PostgreSQL):
    ```yaml
    name: postgres-connector
    config:
      connector.class: io.debezium.connector.postgresql.PostgresConnector
      database.hostname: db-instance
      database.port: 5432
      database.user: debezium
      database.password: secret
      database.dbname: app_db
      plugin.name: pgoutput
    ```

#### **Root Cause 2: Kafka Topic/Partition Issues**
- The CDC events are not being published to the expected Kafka topic or partition.
- **Fix:**
  - Verify topic exists (`kafka-topics --describe`).
  - Check consumer group state (`kafka-consumer-groups --describe`).
  - If using Kafka Connect, ensure the sink is active:
    ```bash
    curl http://localhost:8083/connectors -G
    ```

#### **Root Cause 3: Metrics Processor Not Running**
- The backend service (e.g., Flink, Spark, or custom processor) failed to start.
- **Fix:**
  - Check service logs for exceptions (e.g., missing JAR, misconfigured state backend).
  - Example (Flink checkpoints failing):
    ```bash
    # Check Flink jobmanager logs for checkpoint errors
    docker logs flink-jobmanager
    ```
  - Ensure external dependencies (e.g., Redis for state) are reachable.

---

### **B) Delayed Metrics**
#### **Root Cause 1: CDC Lag**
- The source database is slower than the CDC consumer can keep up.
- **Fix:**
  - Scale the Kafka brokers or increase `fetch.max.bytes`.
  - Optimize CDC consumer settings:
    ```yaml
    # Debezium config for performance tuning
    offset.storage.topic: debezium-offsets
    offset.storage.flush.interval.ms: 1000
    offset.flush.timeout.ms: 30000
    ```
  - Monitor lag with:
    ```bash
    kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group metrics-processor
    ```

#### **Root Cause 2: Slow Metrics Aggregation**
- The backend (e.g., Flink) is spending too long on aggregations.
- **Fix:**
  - Use **incremental checkpoints** (Flink) to reduce state flush overhead.
  - Optimize SQL queries (e.g., avoid `SELECT *` with large tables).
  - Example (Flink TuneConfig):
    ```java
    env.enableCheckpointing(5000); // Checkpoint every 5s
    env.getCheckpointConfig().setCheckpointStorage("s3://checkpoints/");
    ```

#### **Root Cause 3: Sink Bottleneck**
- The destination (e.g., Prometheus, S3, DB) is slow to accept writes.
- **Fix:**
  - Batch writes (e.g., Kafka producer `linger.ms=100`).
  - Use async sinks (e.g., Flink’s `AsyncSink`).
  - Example (Kafka producer batching):
    ```yaml
    producer:
      batch.size: 16384
      linger.ms: 100
      buffer.memory: 33554432
    ```

---

### **C) Partial Metrics (Dropped Events)**
#### **Root Cause 1: Consumer Rebalancing**
- Kafka consumer groups rebalance too frequently, causing missed messages.
- **Fix:**
  - Increase `session.timeout.ms` and `heartbeat.interval.ms`:
    ```yaml
    consumer:
      session.timeout.ms: 30000
      heartbeat.interval.ms: 5000
    ```

#### **Root Cause 2: Schema Mismatch**
- The CDC payload schema changed, but the consumer is not handling it.
- **Fix:**
  - Use **Avro/Protobuf** with backward-compatible updates.
  - Example (Debezium schema registry):
    ```yaml
    schema.registry.url: http://schema-registry:8081
    ```

#### **Root Cause 3: State Backend Issues**
- Flink/Spark state is corrupted or not persisting correctly.
- **Fix:**
  - Enable `state.backend.fs.checkpoints.dir` (Flink).
  - Use **RocksDB** for large state:
    ```yaml
    state.backend: rocksdb
    state.checkpoints.dir: s3://checkpoints/
    ```

---

### **D) High Latency in Metrics Processing**
#### **Root Cause 1: Slow State Updates**
- Stateful operations (e.g., counting, aggregating) are blocking.
- **Fix:**
  - Use **Flink’s `AsyncDataStream`** for external calls (e.g., DB lookups).
  - Example (Flink Async I/O):
    ```java
    AsyncDataStream.unorderedWait(
        events,
        new AsyncDatabaseRequest(),
        1000, TimeUnit.MILLISECONDS, 100
    );
    ```

#### **Root Cause 2: GC Overhead**
- Long GC pauses due to high memory usage.
- **Fix:**
  - Tune JVM heap (`-Xms4G -Xmx4G`).
  - Use **G1GC** for large heaps:
    ```bash
    -XX:+UseG1GC -XX:MaxGCPauseMillis=200
    ```

#### **Root Cause 3: External API Throttling**
- Third-party APIs (e.g., Prometheus pushgateway) are rate-limiting.
- **Fix:**
  - Implement **exponential backoff** in retries.
  - Example (Flink retry logic):
    ```java
    env.addSink(mySink)
        .uid("metrics-sink")
        .setParallelism(1)
        .name("PrometheusSink");
    ```

---

## **3. Debugging Tools & Techniques**

### **A) Observability Stack**
| **Tool**          | **Purpose** | **Commands/Configs** |
|-------------------|------------|----------------------|
| **Kafka Consumer Lag** | Check CDC processing delay | `kafka-consumer-groups --describe --group metrics-processor` |
| **Prometheus + Grafana** | Monitor metrics pipeline | `rate(kafka_consumer_records_lag{...})` |
| **Flink UI** | Inspect Flink job state | `http://localhost:8081/#/jobmanager` |
| **Debezium UI** | Debug CDC source issues | `http://localhost:8080/metrics` |
| **JVM Profiling** | Find memory leaks | `jcmd <pid> GC.heap_dump` |

### **B) Logging & Tracing**
- **Enable Debug Logs:**
  ```bash
  # Flink debug mode
  bin/flink run -Dlog.level=DEBUG ...
  ```
- **Distributed Tracing (Jaeger/Zipkin):**
  ```yaml
  # Flink tracing config
  environment:
    JAEGER_SAMPLER_TYPE: const
    JAEGER_SAMPLER_PARAM: 1
    JAEGER_ENDPOINT: http://jaeger:14268/api/traces
  ```

### **C) Benchmarking**
- **Load Test CDC Pipeline:**
  ```bash
  # Simulate high-throughput inserts
  pgbench -i -s 100 app_db
  ```
- **Measure End-to-End Latency:**
  ```bash
  # Track time from DB write to metric push
  time curl -X POST -d '{"key":"test"}' http://metrics-service
  ```

---

## **4. Prevention Strategies**

| **Strategy** | **Action Items** | **Tools** |
|-------------|----------------|----------|
| **Automated Alerts** | Set up alerts for CDC lag >5s. | Prometheus Alertmanager, Datadog |
| **Chaos Engineering** | Simulate CDC failures (e.g., kill Kafka brokers). | Gremlin, Chaos Mesh |
| **Backpressure Handling** | Use Flink’s `backpressuring` strategy. | Flink `setBufferTimeout` |
| **Schema Evolution** | Enforce backward-compatible CDC schema changes. | Avro Schema Registry |
| **Scalable State Management** | Partition state by key (e.g., `state.backend.rocksdb.partitions=1000`). | Flink RocksDB |
| **Multi-AZ Replication** | Ensure CDC source is HA (e.g., PostgreSQL async repl). | AWS RDS, Kubernetes StatefulSets |

---

## **5. Summary Checklist for Quick Resolution**
1. **Verify CDC Source:** Check Debezium/Kafka Connect logs.
2. **Check Kafka Topic:** Ensure topic exists and partitions are active.
3. **Monitor Consumer Lag:** `kafka-consumer-groups --describe`.
4. **Inspect Backend Logs:** Flink/Spark jobmanager logs.
5. **Test Sink Connection:** Push test data to Prometheus/Kafka.
6. **Optimize Bottlenecks:** Batch writes, tune GC, enable async I/O.
7. **Enable Tracing:** Jaeger for distributed latency analysis.
8. **Prevent Recurrence:** Add alerts and load test.

---
**Final Note:** For persistent issues, isolate the component (CDC → Kafka → Backend → Sink) and use **binary search** to narrow down the culprit. Example:
- If metrics work locally but fail in staging, check **network policies**.
- If Flink fails, test with a **hello-world job** to rule out config issues.

This guide ensures you can diagnose and fix CDC Real-Time Metrics issues **within hours**, not days.