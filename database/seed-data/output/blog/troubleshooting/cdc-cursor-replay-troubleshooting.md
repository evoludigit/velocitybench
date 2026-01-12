---
# **Debugging CDC (Change Data Capture) Cursor-Based Replay: A Troubleshooting Guide**

## **Introduction**
Cursor-based CDC replay is a pattern used to reprocess or replay changes (e.g., from a database) after a specific offset or logical timestamp. This ensures **exactly-once processing** and **at-least-once resilience**. However, issues like **stuck replays**, **duplicate events**, **missed events**, or **position drift** can occur.

This guide provides a **structured debugging approach** to identify and resolve common problems efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, ensure the following symptoms align with the issue you’re facing:

| **Symptom**                     | **Description**                                                                 | **Key Indicators**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| Stuck Replay                     | Replay process hangs at a specific cursor position without progress.           | Logs show no new offsets processed; consumer lags behind producer.                 |
| Missing Events                   | Some events from the source are not being replayed.                           | Gaps in replayed records; source log position doesn’t match replayed position.    |
| Duplicate Events                 | Same events are being replayed multiple times.                                 | Duplicate entries in replayed logs; replay position oscillates.                   |
| Position Drift                   | Replay cursor is not advancing as expected (e.g., stuck in a loop).           | Logs show `read_position` and `last_committed_offset` diverging.                  |
| Slow Replay Speed                | Replay is processing events much slower than expected.                         | High latency between source and replay; low throughput.                          |
| Consumer Lag                     | Replay consumer is falling behind the source producer.                         | Metrics show `source_position > replay_position`.                                |
| Source Unavailable               | Underlying CDC source (e.g., DB) is not responding.                          | Connection errors, timeouts, or source-side failures.                             |

---
## **2. Common Issues & Fixes**

### **Issue 1: Stuck Replay (No Progress)**
**Symptoms:**
- Replay process is not advancing past a certain cursor.
- Logs show `read_position` unchanged for hours.

**Root Causes:**
- **Source-side blockage** (e.g., DB transaction lock, slow queries).
- **Consumer-side bottleneck** (e.g., slow processing, backpressure).
- **Cursor serialization/deserialization failure** (e.g., malformed offsets).

**Debugging Steps:**
1. **Verify Source Connectivity**
   - Check if the CDC source (e.g., Debezium, DB logs) is running.
   - Test a manual read of the latest offset:
     ```sql
     -- Example for PostgreSQL (Debezium)
     SELECT * FROM pg_logical_slot_get_changes('my_slot', NULL, NULL) LIMIT 1;
     ```
   - If stuck, check for **deadlocks** or **high contention**:
     ```sql
     SELECT * FROM pg_locks WHERE relation = 'my_table';
     ```

2. **Check Consumer Logs**
   - Look for **timeouts** or **deserialization errors**:
     ```log
     [ERROR] Failed to deserialize offset: Invalid format
     ```
   - Monitor **processing latency** (e.g., via Prometheus/Grafana).

3. **Inspect Cursor State**
   - If using **Debezium**, check the `server_id` and `file`/`pos`:
     ```json
     {
       "consumer": "my-consumer",
       "timestamp": "2024-01-01T00:00:00Z",
       "offset": {
         "file": "log.00000183",
         "pos": 12345,
         "offset": 1234567890,
         "transaction": null
       }
     }
     ```
   - If `pos` is stuck, the source may be **blocked**.

**Fixes:**
- **Increase Source Timeout** (e.g., Debezium `log.min.bytes`):
  ```yaml
  # debrisum.properties
  offset.storage.file.prefix=my_offsets
  offset.storage.file.flush.interval.ms=5000
  ```
- **Restart Consumer with Correct Offset** (if position is corrupted):
  ```java
  Properties props = new Properties();
  props.put(ConsumerConfig.GROUP_ID_CONFIG, "my-group");
  props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
  props.put("specific.avro.reader", "true"); // For Avro
  KafkaConsumer<String, AvroMessage> consumer =
      new KafkaConsumer<>(props, new AvroDeserializer());
  consumer.assign(Collections.singletonList(new TopicPartition("cdc-topic", earliestOffset)));
  ```
- **Manually Advance Cursor** (if stuck due to source issue):
  ```sql
  -- PostgreSQL: Move slot forward
  pg_advisory_xact_lock(12345); -- Lock to force advance
  ```

---

### **Issue 2: Missing Events**
**Symptoms:**
- Replayed events don’t match the source log.
- Gaps in `source_position` vs. `replayed_position`.

**Root Causes:**
- **Cursor not reset correctly** (e.g., after a restart).
- **Source changes not flushed** (e.g., MySQL binary logs not synced).
- **Consumer lag** due to slow processing.

**Debugging Steps:**
1. **Compare Source & Replay Offsets**
   - Query the **latest source offset** (e.g., Debezium’s `server_id`/`file`/`pos`).
   - Check the **consumer’s committed offset**:
     ```bash
     kafka-consumer-groups --bootstrap-server localhost:9092 \
       --group my-group --describe | grep "my-topic"
     ```
   - If they differ, **events are missing**.

2. **Check for Partial Writes**
   - If using **Debezium**, verify `snapshot` and `initial` records:
     ```json
     {
       "payload": {
         "before": null,  // New record (insert)
         "after": {...}   // Updated record (update)
       }
     }
     ```
   - If `before` is `null` but `after` exists, the event was missed.

**Fixes:**
- **Reset Consumer to Earliest Offset** (if missing initial data):
  ```java
  consumer.seekToBeginning(Collections.singletonList(new TopicPartition("cdc-topic")));
  ```
- **Increase Source Polling Interval** (e.g., Debezium `poll.interval.ms`):
  ```yaml
  poll.interval.ms=2000  # Default is 500ms; increase if source is slow
  ```
- **Check for Source Failures** (e.g., MySQL crash during replay).

---

### **Issue 3: Duplicate Events**
**Symptoms:**
- Same event appears multiple times in replay.
- Replay position **oscillates** between two offsets.

**Root Causes:**
- **At-least-once delivery** without idempotent processing.
- **Cursor corruption** (e.g., race condition in offset storage).
- **Consumer restart without checkpointing**.

**Debugging Steps:**
1. **Inspect Replay Logs for Duplicates**
   - Filter logs by event key (e.g., `message_id`):
     ```bash
     grep "DUPLICATE_KEY" replay.log | sort | uniq -c
     ```
2. **Check Kafka Consumer Offsets**
   - Compare **committed offsets** with **logical offsets**:
     ```bash
     kafka-consumer-groups --bootstrap-server localhost:9092 \
       --group my-group --describe | grep my-topic
     ```
   - If `LAG` > 0, the consumer is **replaying from wrong position**.

**Fixes:**
- **Enable Exactly-Once Processing** (Kafka + Kafka Streams):
  ```java
  StreamsBuilder builder = new StreamsBuilder();
  KStream<String, String> stream = builder.stream("cdc-topic");
  stream.process(() -> new KeyValueTransformer<String, String, KeyValue<String, String>>() {
      private final Map<String, Boolean> processed = new HashMap<>();
      @Override
      public KeyValue<String, String> transform(String key, String value) {
          if (!processed.getOrDefault(key, false)) {
              processed.put(key, true);
              return KeyValue.pair(key, value);
          }
          return KeyValue.pair(key, null); // Skip duplicates
      }
  });
  ```
- **Use `KafkaStreams` with `processing.guarantee=exactly_once`** (if using Kafka Streams).
- **Reset Offsets Manually** (if corrupted):
  ```bash
  kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group my-group --reset-offsets --execute --topic cdc-topic --to-earliest
  ```

---

### **Issue 4: Position Drift**
**Symptoms:**
- Replay cursor is **not advancing** despite source changes.
- `read_position` lags behind `source_position`.

**Root Causes:**
- **Consumer is stuck** (e.g., `poll()` blocking indefinitely).
- **Source is slower than replay** (e.g., DB replication lag).
- **Offset commit too aggressive** (e.g., committing before processing).

**Debugging Steps:**
1. **Monitor Consumer Lag**
   - Use `kafka-consumer-groups`:
     ```bash
     kafka-consumer-groups --bootstrap-server localhost:9092 \
       --group my-group --describe | grep "LAG"
     ```
2. **Check Consumer Polling**
   - If `poll()` is not called frequently enough:
     ```java
     consumer.poll(Duration.ofMillis(1000));  // Ensure short poll interval
     ```
3. **Inspect Source Lag**
   - For **Debezium**, check `source_connector` metrics:
     ```bash
     curl http://localhost:8080/connectors/my-connector/status
     ```
   - If `record-lag` > 0, the source is **behind**.

**Fixes:**
- **Increase Polling Frequency** (e.g., Kafka `max.poll.interval.ms`):
  ```properties
  max.poll.interval.ms=300000  # 5 mins (default is 5 mins)
  ```
- **Tune Source Performance** (e.g., Debezium `database.history.kafka.bootstrap.servers`).
- **Use `enable.auto.commit=false` and manual commits** (if using Kafka):
  ```java
  consumer.subscribe(Collections.singletonList("cdc-topic"));
  while (true) {
      ConsumerRecords records = consumer.poll(Duration.ofMillis(1000));
      for (ConsumerRecord record : records) {
          process(record);
      }
      consumer.commitSync();  // Manual commit
  }
  ```

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Metrics**
- **Enable Detailed Logging** (e.g., Kafka, Debezium):
  ```properties
  # Kafka consumer logs
  log4j.logger.org.apache.kafka.clients=DEBUG
  # Debezium connector logs
  confluent.log4j.logger.org.apache.kafka.connect=DEBUG
  ```
- **Key Metrics to Monitor:**
  | Metric                          | Tool                     | Expected Behavior                          |
  |----------------------------------|--------------------------|--------------------------------------------|
  | `consumer-lag`                   | `kafka-consumer-groups`  | Should be `0` if caught up.                |
  | `source_position` vs `offset`   | Prometheus/Grafana       | Should align over time.                    |
  | `poll_latency`                   | Kafka Consumer Metrics   | Should be < 1s (if polling frequently).    |
  | `record-processed-rate`          | Custom Instrumentation    | Should match source throughput.            |

### **B. Offset Debugging**
- **Dump Offset Storage** (e.g., Kafka offsets in RocksDB):
  ```bash
  # List all offsets for a consumer group
  kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group my-group --describe
  ```
- **Reset Offsets Programmatically**:
  ```java
  KafkaConsumer<String, String> consumer = new KafkaConsumer<>();
  consumer.assign(Collections.singletonList(new TopicPartition("cdc-topic", 0)));
  consumer.seekToBeginning(Collections.singletonList(new TopicPartition("cdc-topic", 0)));
  ```

### **C. Source-Specific Tools**
| **Source**       | **Debugging Tool**                          | **Command/Query**                          |
|------------------|--------------------------------------------|--------------------------------------------|
| **PostgreSQL**   | `pg_logical_slot_peek_changes`             | `SELECT * FROM pg_logical_slot_peek_changes('my_slot', NULL, NULL);` |
| **MySQL**        | `SHOW BINARY LOGS`                         | `SHOW BINARY LOGS; SHOW SLAVE STATUS;`     |
| **Debezium**     | Connector REST API                          | `curl http://localhost:8080/connectors`    |
| **Kafka**        | `kafka-console-consumer`                   | `kafka-console-consumer --topic cdc-topic --from-beginning` |

### **D. Distributed Tracing**
- **Use OpenTelemetry** to trace CDC pipelines:
  ```java
  // Example: Instrument Kafka consumer
  ConsumerRecords records = consumer.poll(Duration.ofMillis(1000));
  for (ConsumerRecord record : records) {
      Tracer.current().spanBuilder("process-event").startSpan().use(() -> {
          process(record);
      });
  }
  ```
- **Visualize with Jaeger** to identify bottlenecks.

---

## **4. Prevention Strategies**

### **A. Design-Time Mitigations**
1. **Use Idempotent Processing**
   - Ensure replay logic is **safe for duplicates** (e.g., upsert instead of insert).
   - Example (PostgreSQL):
     ```sql
     INSERT INTO target_table (id, data)
     VALUES (123, 'value')
     ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data;
     ```
2. **Enable Exactly-Once Semantics**
   - **Kafka + Kafka Streams**: Use `processing.guarantee=exactly_once`.
   - **Debezium**: Ensure `batch.size` and `max.queue.size` are tuned.
3. **Monitor Critical Offsets**
   - Use **Prometheus alerts** for:
     - `consumer_lag > threshold`
     - `source_position > replay_position + 1000`

### **B. Runtime Safeguards**
1. **Short Polling Intervals**
   - Set `poll.interval.ms` to **< 1s** (Kafka) to reduce lag.
2. **Backpressure Handling**
   - Implement **dynamic scaling** if consumer lags behind.
   - Use **Kafka’s `max.poll.records`** to control batch size:
     ```properties
     max.poll.records=1000  # Default is 500
     ```
3. **Automatic Recovery**
   - **Restart consumers on failure** (e.g., Spring Cloud Stream auto-restart).
   - **Use `ConsumerRebalanceListener`** to handle partition reassignments:
     ```java
     consumer.subscribe(topics, new ConsumerRebalanceListener() {
         @Override
         public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
             for (TopicPartition partition : partitions) {
                 consumer.seek(partition, consumer.position(partition) + 1);
             }
         }
     });
     ```

### **C. Testing Strategies**
1. **Chaos Engineering**
   - **Kill consumers randomly** to test recovery.
   - **Simulate source failures** (e.g., pause Debezium connector).
2. **End-to-End Tests**
   - **Test replay from arbitrary offsets**:
     ```java
     // Seek to a specific offset in Kafka
     consumer.seek(new TopicPartition("cdc-topic", 0), 1000L);
     ```
   - **Verify no duplicates/losses** with a test harvester:
     ```java
     List<String> seenEvents = new ArrayList<>();
     records.forEach(record -> {
         String key = record.key();
         if (!seenEvents.contains(key)) {
             seenEvents.add(key);
             process(record);
         }
     });
     ```

---

## **5. Summary Checklist for Quick Resolution**
| **Issue**               | **Quick Fix**                                                                 | **Long-Term Solution**                          |
|-------------------------|-----------------------------------------------------------------------------|------------------------------------------------|
| **Stuck Replay**        | Restart consumer with correct offset.                                        | Increase source timeouts; monitor locks.       |
| **Missing Events**      | Reset consumer to `earliest`.                                                | Tune `poll.interval.ms`; check source sync.    |
| **Duplicate Events**    | Enable idempotence; reset offsets.                                           | Use Kafka Streams EoS; deduplicate processing. |
| **Position Drift**      | Increase polling frequency; check consumer lag.                             | Auto-scale consumers; monitor source lag.      |
| **Slow Replay**         | Optimize batch size (`max.poll.records`).                                   | Distribute load; tune source performance.      |

---
## **Final Notes**
- **Always back up offsets** before manual resets.
- **Use infrastructure like Kafka Rest Proxy** for safer offset management.
- **Automate recovery** (e.g., Spring Retry, Kafka ConsumerRebalanceListener).

By following this guide, you should be able to **diagnose and resolve CDC cursor-based replay issues efficiently**. If issues persist, check **source-specific documentation** (e.g., Debezium, database logs) for deeper insights.