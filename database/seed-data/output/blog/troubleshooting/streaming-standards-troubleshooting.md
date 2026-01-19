# **Debugging Streaming Standards Pattern: A Troubleshooting Guide**

This guide provides a structured approach to diagnosing and resolving issues commonly encountered when implementing the **Streaming Standards Pattern**, a framework for building scalable, fault-tolerant streaming pipelines (e.g., Apache Kafka, Apache Pulsar, or AWS Kinesis-based systems). The pattern ensures consistency between producers, consumers, and storage while handling backpressure and retries efficiently.

---

## **1. Symptom Checklist**
When troubleshooting streaming system issues, systematically verify the following:

| **Symptom**                     | **Possible Root Cause**                          |
|---------------------------------|-----------------------------------------------|
| **Producer Side**               |                                               |
| - Messages not being published to the broker | Broker unavailability, credentials issue, or network failure |
| - High latency in message send    | Overloaded broker, slow network, or producer retries spinning up |
| - Duplicate messages             | Idempotent producer misconfigured, retries without deduplication |
| - Connection errors (`Timeout`, `Authorization`) | Invalid SASL/SSL config, quota exceeded, or broker misconfiguration |
| **Broker Side**                 |                                               |
| - High CPU/memory usage         | Consumer lag, partition imbalance, or inefficient serialization |
| - Disk usage rapidly increasing  | Retention policy misconfigured, log segments not compacted |
| - Slow commit/offset sync       | Consumer lag, transactional writes failing |
| - Under-replicated partitions    | Unhealthy broker nodes, replication lag        |
| **Consumer Side**               |                                               |
| - Consumers stuck at `PENDING`   | Offset commit failures, small batch sizes, or stuck retries |
| - Messages lost/duplicates       | Consumer crash without commit, manual commits, or incorrect `max.poll.records` |
| - High lag between producers/consumers | Slow processing logic, under-provisioned workers, or serialization bottlenecks |
| - `ConsumerRebalanceFailedException` | Invalid consumer group config, topic misconfiguration (`min.insync.replicas`) |
| **System-Wide**                 |                                               |
| - Entire pipeline failure        | Broker cluster down, network partitions, or global quotas exceeded |
| - Serialization errors (`DeserializationException`) | Incompatible schema versions, missing dependencies |
| - Slow end-to-end latency        | Unoptimized batching, serialization, or network hops |

---

## **2. Common Issues and Fixes**

### **Issue 1: Producers Failing to Publish Messages**
**Symptoms:**
- `ProducerBootstrapException` (connection refused)
- `AuthorizationException` (invalid credentials)
- High `send()` latency

**Root Causes & Fixes:**
| **Cause**                          | **Solution**                                                                                     | **Code Example**                                                                                     |
|-----------------------------------|------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Broker unreachable**            | Check broker health, DNS resolver, or firewall rules.                                             | ```java<br>Properties props = new Properties();<br>props.put("bootstrap.servers", "kafka1:9092,kafka2:9092");<br>Producer<String, String> producer = new KafkaProducer<>(props);``` |
| **SASL/SSL misconfiguration**      | Ensure correct credentials and cipher suites.                                                    | ```java<br>props.put("security.protocol", "SASL_SSL");<br>props.put("sasl.mechanism", "SCRAM-SHA-512");<br>props.put("sasl.jaas.config", "org.apache.kafka.common.security.scram.ScramLoginModule required username=\"user\" password=\"pass\";");``` |
| **Quota exceeded**                | Monitor broker quotas (`quota.producer_bytes_per_second`).                                        | ```bash<br>kafka-configs.sh --alter --entity-type brokers --entity-name <broker-id> --add-config "quota.producer_bytes_per_second=-1"``` |
| **Idempotent producer not working** | Enable `enable.idempotence=true` and monitor `transactional.id` for retries.                      | ```java<br>props.put("enable.idempotence", "true");<br>props.put("transactional.id", "transactional-producer");``` |

**Debugging Steps:**
1. Verify broker connectivity with `telnet broker-host 9092`.
2. Check producer metrics (`record-error-rate`, `record-retry-rate`) in JMX or Prometheus.
3. Enable debug logging (`log4j.logger.org.apache.kafka=DEBUG`).

---

### **Issue 2: Consumer Lag & Stuck Processing**
**Symptoms:**
- Consumer lag (`PENDING` records not processed).
- Slow `poll()` calls (<100ms throughput).

**Root Causes & Fixes:**
| **Cause**                          | **Solution**                                                                                     | **Code Example**                                                                                     |
|-----------------------------------|------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Small `fetch.min.bytes`**       | Increment `fetch.min.bytes` to reduce small fetches (default: 1).                               | ```java<br>props.put("fetch.min.bytes", "5242880"); // 5MB<br>props.put("fetch.max.wait.ms", "500"); // 500ms wait``` |
| **High `max.poll.records`**       | Reduce batch size to avoid slow consumers.                                                       | ```java<br>props.put("max.poll.records", "500"); // Default: 500, but tune based on processing time``` |
| **Stuck retries (`REBALANCE_FAILED`)** | Increase `max.poll.interval.ms` and check for deadlocks.                                         | ```java<br>props.put("max.poll.interval.ms", "300000"); // 5min max lag``` |
| **Offset commits failing**        | Ensure `enable.auto.commit=false` and commit manually after processing.                          | ```java<br>consumer.commitSync(); // Manual commit<br>// OR<br>consumer.commitAsync((metadata, exception) -> { ... });``` |
| **Slow processing logic**         | Profile CPU/memory usage; consider async processing or parallelism.                               | ```java<br>// Example: Async processing with CompletableFuture<br>List<ConsumerRecord> records = consumer.poll(Duration.ofMillis(100));<br>records.forEach(record -> {<br>    CompletableFuture.runAsync(() -> process(record));<br>});``` |

**Debugging Steps:**
1. Monitor consumer lag in Kafka Manager or Kafka Lag Dashboard.
2. Check `poll()` metrics (`records-lag-max`, `records-consumed-rate`).
3. Enable `all.topics` tracing in consumer logs:
   ```java
   props.put("consumer.interceptor.classes", "com.example.debug.OffsetDebugInterceptor");
   ```

---

### **Issue 3: Duplicate Messages in Pipeline**
**Symptoms:**
- Consumer sees duplicates due to retries or crashes.
- Producer sends retries without deduplication.

**Root Causes & Fixes:**
| **Cause**                          | **Solution**                                                                                     | **Code Example**                                                                                     |
|-----------------------------------|------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Producer retries without idempotence** | Enable `enable.idempotence=true` and ensure `key` uniqueness.                                   | ```java<br>props.put("enable.idempotence", "true");<br>// Use a unique key (e.g., UUID)<br>producer.send(new ProducerRecord<>("topic", key, value));``` |
| **Consumer crashes before commit** | Use `enable.auto.commit=false` + manual commits or transactional consumes.                   | ```java<br>// Transactional consume<br>props.put("isolation.level", "read_committed");<br>ConsumerRecords records = consumer.poll();<br>try {<br>    for (ConsumerRecord record : records) {<br>        process(record);<br>    }<br>    consumer.commitSync();<br>} catch (Exception e) {<br>    consumer.close();<br>    throw e;<br>}``` |
| **Schema evolution mismatches**   | Use Avro/Kafka Schema Registry with backward-compatible changes.                                 | ```java<br>// Register schema<br>Schema schema = new Schema.Parser().parse(new File("schema.avsc"));<br>SchemaRegistryClient registry = new SchemaRegistryClient("http://schema-registry:8081");<br>registry.register("topic", schema);``` |

**Debugging Steps:**
1. Enable `duplicate.monitoring` in consumer (custom interceptor).
2. Check broker logs for `RECORD_METADATA` failures.
3. Use Kafka’s `describe.topics` to check `isolation.level`.

---

### **Issue 4: Broker Resource Exhaustion (High CPU/Disk)**
**Symptoms:**
- Broker OOM errors or `ReplicaFetchError`.
- Disk usage spikes due to unbounded log retention.

**Root Causes & Fixes:**
| **Cause**                          | **Solution**                                                                                     | **Command/Config**                                                                                 |
|-----------------------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Unbounded retention**           | Set `log.retention.hours` and `log.segment.bytes`.                                             | ```bash<br>kafka-configs.sh --alter --entity-type topics --entity-name <topic> --add-config "log.retention.hours=168"<br>log.segment.bytes=1GB``` |
| **Compacted topics not working**  | Ensure `cleanup.policy=compact` and `delete retention` is set.                                 | ```bash<br>kafka-topics.sh --alter --topic <topic> --config cleanup.policy=compact<br>--config delete.retention.ms=86400000``` |
| **Replication lag**               | Increase `unclean.leader.election.enable=false` and monitor `under-replicated-partitions`.   | ```bash<br>kafka-configs.sh --alter --entity-type brokers --entity-name <broker> --add-config "unclean.leader.election.enable=false"` |
| **High network I/O**              | Tune `num.network.threads` and `num.io.threads`.                                                 | ```bash<br>kafka-server-start.sh --override config/server.properties<br>num.network.threads=8<br>num.io.threads=16``` |

**Debugging Steps:**
1. Check broker JMX metrics (`kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec`).
2. Use `kafka-consumer-groups.sh --describe` to find laggy partitions.
3. Run `kafka-log-dirs.sh --describe` to inspect log segment sizes.

---

## **3. Debugging Tools and Techniques**
### **A. Kafka-Specific Tools**
| **Tool**                          | **Purpose**                                                                                     | **Usage**                                                                                           |
|-----------------------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **kafka-consumer-groups**         | Monitor consumer lag and offsets.                                                              | ```bash<br>kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group my-group``` |
| **kafka-topics**                  | Check topic config, partitions, and retention.                                                 | ```bash<br>kafka-topics.sh --describe --topic my-topic --bootstrap-server localhost:9092```       |
| **kafka-producer-perf-test**      | Benchmark producer throughput.                                                                | ```bash<br>kafka-producer-perf-test.sh --topic test --num-records 1000000 --throughput -1 --record-size 1000``` |
| **kafka-lag-exporter** (Prometheus) | Expose consumer lag metrics to Prometheus.                                                     | Deploy [kafka-lag-exporter](https://github.com/danielqsj/kafka-lag-exporter) with Prometheus.    |
| **Kafka Manager**                 | Web UI for monitoring brokers, topics, and consumers.                                          | [https://kafkamanager.github.io/](https://kafkamanager.github.io/)                                 |

### **B. Logging & Tracing**
1. **Enable Debug Logs**:
   ```bash
   # In logs/kafka-server.log
   log4j.logger.org.apache.kafka=DEBUG
   ```
2. **Consumer Interceptor for Debugging**:
   ```java
   public class OffsetDebugInterceptor implements ConsumerInterceptor {
       @Override
       public ConsumerRecords<String, String> onConsume(ConsumerRecords records) {
           System.out.printf("Consumer %s received %d records%n", Thread.currentThread().getId(), records.count());
           return records;
       }
       // Other methods...
   }
   ```
3. **Distributed Tracing** (OpenTelemetry):
   - Instrument consumers/producers with OTel to trace requests across services.

### **C. Performance Profiling**
- **JVM Profiling**: Use `jcmd <pid> Thread.print` to detect blocked threads.
- **Kafka Producer/Consumer Metrics**:
  - `record-error-rate`, `record-retry-rate`, `records-per-request-rate`.
- **Network Latency**: Use `ping`/`traceroute` to check broker connectivity.

---

## **4. Prevention Strategies**
### **A. Configuration Best Practices**
| **Component**       | **Recommended Setting**                                                                       |
|--------------------|---------------------------------------------------------------------------------------------|
| **Producer**        | `enable.idempotence=true`, `acks=all`, `linger.ms=5`, `batch.size=16KB`                     |
| **Consumer**        | `enable.auto.commit=false`, `max.poll.records=500`, `fetch.min.bytes=5MB`                 |
| **Broker**          | `log.retention.hours=168`, `log.segment.bytes=1GB`, `num.partitions=high` (e.g., 64)      |
| **Transactions**    | Use `transactional.id` for exactly-once semantics                                          |

### **B. Monitoring & Alerts**
1. **Critical Metrics to Monitor**:
   - Producer/Consumer `error-rate`, `latency`, and `throughput`.
   - Broker `under-replicated-partitions`, `request-lag`, and `disk-usage`.
   - Consumer `lag`, `rebalance-rate`, and `poll-timeout`.
2. **Alert Rules (Prometheus Example)**:
   ```yaml
   - alert: HighConsumerLag
     expr: kafka_consumer_lag{group="my-group"} > 1000
     for: 5m
     labels:
       severity: critical
     annotations:
       summary: "Consumer {{ $labels.group }} lagging by {{ $value }} messages"
   ```

### **C. Disaster Recovery**
1. **Backup Critical Topics**:
   ```bash
   kafka-dump-log.sh --files /path/to/logs --print-data-log --print-topic-details
   ```
2. **Replication Checks**:
   ```bash
   kafka-topics.sh --describe --under-replicated-partitions
   ```
3. **Chaos Engineering**:
   - Test failover with `kafka-preferred-replica-election.sh --bootstrap-server localhost:9092 --all-topics --all-partitions`.

### **D. Schema Evolution**
- Use **Kafka Schema Registry** for Avro/Protobuf schemas.
- Enforce backward/forward compatibility:
  ```java
  SchemaCompatibilityValidator validator = SchemaCompatibilityValidator.version(1);
  SchemaCompatibilityResult result = validator.validate("topic", newSchema, oldSchema);
  ```

---

## **5. Summary of Key Takeaways**
| **Problem Area**       | **Quick Fix**                                                                               | **Long-Term Solution**                                                                             |
|-----------------------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Producer Issues**   | Check broker health, SASL/SSL, and quotas.                                               | Enable idempotence, monitor retries, and use transactional produces.                          |
| **Consumer Lag**      | Increase `fetch.min.bytes` and reduce `max.poll.records`.                               | Optimize processing logic, use async consumers, and monitor lag metrics.                      |
| **Duplicates**        | Use `enable.idempotence=true` + manual commits.                                          | Implement idempotent consumers and schema registry for safety.                                  |
| **Broker Overload**   | Tune `log.retention` and `num.partitions`.                                               | Right-size partitions, enable compaction, and monitor disk usage.                              |
| **Debugging**         | Use `kafka-consumer-groups` and JMX metrics.                                            | Instrument with OTel, set up Prometheus alerts, and use Kafka Manager for UI insights.           |

---
**Final Note**: For production systems, automate debugging with **custom scripts** (e.g., `check_kafka_health.sh`) and **CI/CD checks** (e.g., pre-deploy topic configuration validation). Always test changes in a staging environment with realistic load.