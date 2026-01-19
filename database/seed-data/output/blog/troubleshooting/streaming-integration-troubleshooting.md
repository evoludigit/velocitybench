# **Debugging Streaming Integration: A Troubleshooting Guide**
*For Backend Engineers Handling Real-Time Data Pipelines*

This guide provides a step-by-step approach to diagnosing and resolving issues in **Streaming Integration** systems, ensuring minimal downtime and efficient troubleshooting.

---

## **1. Symptom Checklist**
Before diving into fixes, verify the following symptoms:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| **Data Loss / Duplication** | Messages missing or appearing twice in consumers. | Incorrect analytics, missed business logic. |
| **Slow Processing** | High latency between event ingestion and processing. | Poor user experience, delayed actions. |
| **Connection Drops** | Intermittent disconnections between producers/consumers. | Lost data, retries, or failed transactions. |
| **Consumer Backlog** | Queues growing indefinitely (e.g., Kafka lag increasing). | System overload, potential crashes. |
| **Crashes / Timeouts** | Workers/consumers failing with `TimeoutException` or OOM. | Service degradation, unhandled state. |
| **Schema Mismatches** | Incompatible data formats between stages. | Failures in serialization/deserialization. |
| **Resource Starvation** | High CPU/memory usage in brokers or consumers. | Performance degradation, eventual failure. |
| **Authentication / Permissions Issues** | `403 Forbidden` or `Unauthorized` errors in APIs. | Secure failures, no data flow. |
| **Ordering Violations** | Events arriving out of sequence. | Logical errors in downstream systems. |
| **Checkpointing Failures** | Persisted state not updating correctly. | Re-processing of old messages. |

---
**Quick Check:**
- **Is the problem intermittent or persistent?**
- **Which component is affected?**
  (Producer → Broker → Consumer → Storage)
- **Are logs available?**
  (Check `stdout`, `stderr`, cloud provider logs, or monitoring tools.)

---

## **2. Common Issues & Fixes**
### **Issue 1: Data Loss Due to Unhandled Failures**
**Symptom:**
- Critical events (e.g., payments, user actions) missing in the target system.

**Root Causes:**
- Consumer crashes before committing offsets.
- Producer fails silently without retry logic.

**Fixes:**

#### **For Consumers (Kafka/Pulsar/SNS/SQS)**
```python
# Example: Kafka Consumer with Exactly-Once Semantics
from confluent_kafka import Consumer

conf = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'my-group',
    'auto.offset.reset': 'earliest',  # Start from beginning if no offset
    'enable.auto.commit': False,     # Manual commits for reliability
}

consumer = Consumer(conf)
try:
    consumer.subscribe(['topic'])
    while True:
        msg = consumer.poll(1.0)  # Wait for message
        if msg is None:
            continue
        try:
            process_message(msg.value())
            consumer.commit(msg)  # Only commit after success
        except Exception as e:
            logger.error(f"Failed to process: {e}")
            # Retry or send to dead-letter queue (DLQ)
            send_to_dlq(msg)
```

**Key Fixes:**
✅ **Disable `auto.offset.commit`** → Use manual commits after successful processing.
✅ **Implement retries (with jitter)** → Avoid thundering herd.
✅ **Dead-Letter Queue (DLQ)** → Route failed messages for later inspection.

---

#### **For Producers (Kafka/Pulsar)**
```java
// Example: Kafka Producer with Retry & Idempotence
Properties props = new Properties();
props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
props.put(ProducerConfig.RETRIES_CONFIG, 5); // Retry on failures
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 1); // Exactly-once
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);

Producer<String, String> producer = new KafkaProducer<>(props);

try {
    producer.send(new ProducerRecord<>("topic", key, value), (metadata, exception) -> {
        if (exception != null) {
            logger.error("Failed to send: " + exception.getMessage());
            // Implement retry logic or alert
        } else {
            logger.debug("Sent to partition {} offset {}", metadata.partition(), metadata.offset());
        }
    }).get(); // Block until send completes (for idempotence)
} catch (ExecutionException | InterruptedException e) {
    handle_failure(e);
}
```

**Key Fixes:**
✅ **Enable idempotence** → Prevent duplicate processing.
✅ **Configure retries** → Handle transient network issues.
✅ **Monitor send errors** → Alert on repeated failures.

---

---

### **Issue 2: High Consumer Lag (Backlog Growing)**
**Symptom:**
- Kafka consumer lag increases over time (e.g., `kafka-consumer-groups --describe` shows stagnation).

**Root Causes:**
- Slow processing logic.
- Too few consumer instances.
- Serialization/deserialization bottlenecks.

**Fixes:**

#### **Optimize Consumer Parallelism**
```bash
# Check topic partitions vs. consumer instances
kafka-topics --describe --topic my-topic --bootstrap-server kafka:9092
# Output: Partitions = 10
# Solution: Scale consumers to match partitions (1:1 ratio)
```

#### **Profile Slow Processing**
```python
# Example: Add timing metrics to processing function
def process_message(data):
    start_time = time.time()
    try:
        # Business logic here
        result = expensive_operation(data)
        commit_offset()
        logger.info(f"Processed in {time.time() - start_time:.2f}s")
    except Exception as e:
        log_error(e)
```

**Key Fixes:**
✅ **Scale consumers horizontally** → Match partitions.
✅ **Optimize hot paths** → Use async I/O, caching, or batch processing.
✅ **Monitor per-message latency** → Identify bottlenecks.

---

### **Issue 3: Connection Drops (Network/Broker Issues)**
**Symptom:**
- `DisconnectException` or `TimeoutException` in logs.

**Root Causes:**
- Network instability (cloud provider issues, VPN drops).
- Broker overloaded.
- Incorrect `reconnection.backoff.ms` settings.

**Fixes:**

#### **Producer Configuration**
```properties
# Kafka Producer (exponential backoff)
reconnection.backoff.ms=500
request.timeout.ms=30000
delivery.timeout.ms=120000
```

#### **Consumer Configuration**
```python
# Kafka Consumer (rebalance handling)
conf = {
    'heartbeat.interval.ms': 3000,  # Keep-alive heartbeat
    'session.timeout.ms': 10000,   # Allow 3 heartbeats before rebalance
    'max.poll.interval.ms': 300000, # Longer poll timeout for slow consumers
}
```

**Key Fixes:**
✅ **Tune timeouts** → Balance reliability vs. responsiveness.
✅ **Handle reconnects gracefully** → Retry logic with jitter.
✅ **Monitor broker health** → Check `kafka-broker-api-versions` and `kafka-server-stats`.

---

### **Issue 4: Schema Mismatches (Avro/Protobuf)**
**Symptom:**
- `SchemaMismatchException` or `InvalidMessageException`.

**Root Causes:**
- Schema evolution not handled (e.g., adding a field).
- Incorrect serializer/deserializer in code.

**Fixes:**

#### **Example: Avro Schema Registry Handling**
```java
// Use SchemaRegistryClient for backward/forward compatibility
SchemaRegistryClient schemaRegistry = new SchemaRegistryClient(
    "http://schema-registry:8081",
    30000
);

GenericRecord message = new GenericData.Record(schema);
message.put("id", id);
message.put("new_field", newValue); // Adding a field

// Serialize with latest schema
byte[] serialized = new BinaryEncoder().encode(schemaRegistry.getLatestSchema("topic"));
```

**Key Fixes:**
✅ **Use a schema registry** (Confluent, Apicoro).
✅ **Test schema evolution** → Ensure consumers handle optional fields.
✅ **Validate schemas programmatically**:
   ```python
   from confluent_kafka.schema_registry import SchemaRegistryClient

   client = SchemaRegistryClient("http://schema-registry:8081")
   schema = client.get_latest_schema("topic")
   assert "new_field" in schema.subject()  # Check for breaking changes
   ```

---

### **Issue 5: Resource Starvation (OOM/High CPU)**
**Symptom:**
- `OutOfMemoryError` in consumers or brokers.
- High CPU usage in `kafka-server` or `kafka-consumer`.

**Root Causes:**
- Unbounded batches in consumers.
- Memory leaks in custom deserializers.
- Lack of garbage collection tuning.

**Fixes:**

#### **Consumer-Side Optimizations**
```python
# Limit max.poll.records to control memory usage
conf = {
    'max.poll.records': 500,  # Default is unbounded
    'fetch.max.bytes': 52428800,  # 50MB per fetch
    'fetch.wait.max.ms': 500,  # Reduce latency
}
```

#### **Broker-Side Tuning**
```properties
# Kafka Server (in server.properties)
log.segment.bytes=1GB  # Reduce log segment size
num.network.threads=8  # Handle more connections
num.io.threads=8
```

**Key Fixes:**
✅ **Set batch limits** → Avoid memory overload.
✅ **Monitor GC logs** → Use `GC_LOGGING_PROPS` to debug.
✅ **Use smaller partitions** → If partitions are too large, split them.

---

## **3. Debugging Tools & Techniques**
| **Tool** | **Purpose** | **Example Command/Usage** |
|----------|------------|---------------------------|
| **`kafka-consumer-groups`** | Check consumer lag | `kafka-consumer-groups --bootstrap-server kafka:9092 --describe --group my-group` |
| **`kafka-topics`** | Inspect topic health | `kafka-topics --describe --topic my-topic --bootstrap-server kafka:9092` |
| **`kafka-console-consumer`** | Debug message format | `kafka-console-consumer --bootstrap-server kafka:9092 --topic my-topic --from-beginning` |
| **Prometheus + Grafana** | Monitor metrics | Query `kafka_server_replicated_partitions`, `kafka_consumer_lag` |
| **JMX Exporter** | Broker metrics | `jmx_port=9999` in `server.properties` |
| **`kubectl logs` (K8s)** | Container logs | `kubectl logs -l app=kafka-consumer --tail=50` |
| **Schema Registry UI** | Validate schemas | `http://schema-registry:8081/subjects` |
| **`kafka-producer-perf-test`** | Test throughput | `kafka-producer-perf-test --topic test --num-records 100000 --throughput -3 --record-size 1000` |
| **`strace` / `ltrace`** | Low-level I/O debugging | `strace -f -e trace=network java -jar myconsumer.jar` |

**Advanced Debugging:**
- **Enable Debug Logging** (e.g., `LOG_LEVEL=DEBUG` in `log4j.properties`).
- **Use `kafka-run-class` for Ad-Hoc Debugging**:
  ```bash
  kafka-run-class kafka.tools.GetOffsetShell --bootstrap-server kafka:9092 --topic my-topic --group my-group
  ```
- **Network Tracing** (for TCP issues):
  ```bash
  tcpdump -i any -w kafka_traffic.pcap port 9092
  ```

---

## **4. Prevention Strategies**
### **A. Design-Time Mitigations**
1. **Idempotent Consumers**
   - Ensure reprocessing the same message doesn’t cause side effects (e.g., use `idempotent_sinks` in Flink).
2. **Schema Evolution Planning**
   - Use **backward-compatible** changes (add optional fields, not required ones).
   - Test with `Schema Registry` compatibility checks.
3. **Resource Quotas**
   - Set **Kubernetes Resource Limits** for consumers/brokers.
   - Use **Kafka quotas** (`BrokerQuota`) to prevent abuse.

   ```yaml
   # Example: Kafka Quota (via Kafka Admin API)
   {
     "entity_name": "app-team",
     "entity_type": "CLIENT",
     "producer_byte_rate": 10485760,  # 10MB/s
     "consumer_byte_rate": 5242880
   }
   ```
4. **Monitoring & Alerts**
   - **Key Metrics to Alert On**:
     - `kafka_consumer_lag` > 10% of partition count.
     - `kafka_network_processing_time_avg` > 1s.
     - `kafka_request_queue_time_avg` > 500ms.
   - **Tools**: Prometheus + Alertmanager, Datadog, New Relic.

### **B. Runtime Strategies**
1. **Chaos Engineering**
   - Test failure scenarios (e.g., kill a broker, throttle network).
   - Use **Chaos Mesh** (K8s) or **Gremlin**.
2. **Circuit Breakers**
   - Implement **resilience patterns** (Hystrix, Retries with Backoff).
   - Example (Python + `tenacity`):
     ```python
     from tenacity import retry, stop_after_attempt, wait_exponential

     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
     def send_to_upstream(message):
         try:
             upstream_client.send(message)
         except TimeoutError:
             logger.warn("Upstream timeout, retrying...")
     ```
3. **Blue-Green Deployments**
   - Deploy new consumer versions alongside old ones to avoid downtime.
   - Use **consumer groups with multiple clients** (e.g., `group.my-app-v2`).

### **C. Operational Best Practices**
1. **Log Everything (But Strategically)**
   - **Structured Logging** (JSON) for easier parsing:
     ```python
     logger.info({
         "event": "message_processed",
         "topic": "orders",
         "partition": msg.partition(),
         "offset": msg.offset(),
         "timestamp": datetime.utcnow().isoformat()
     })
     ```
   - **Correlation IDs** for tracing:
     ```java
     String correlationId = UUID.randomUUID().toString();
     producer.send(new ProducerRecord<>(topic, key, value), callback(correlationId));
     ```
2. **Automated Recovery**
   - **Kubernetes Liveness/Readiness Probes**:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 30
       periodSeconds: 10
     ```
   - **Dead Letter Queues (DLQ)** for failed messages.
3. **Document Everything**
   - **Streaming Schema Registry** → Version-controlled schemas.
   - **Runbooks** for common failures (e.g., "If consumer lag > 1000, scale to 4 instances").

---

## **5. Summary Checklist for Quick Resolution**
| **Step** | **Action** | **Tools** |
|----------|------------|-----------|
| 1 | Check logs for errors | `journalctl`, `kubectl logs`, `tail -f /var/log/kafka/` |
| 2 | Verify consumer lag | `kafka-consumer-groups --describe` |
| 3 | Monitor broker health | `kafka-broker-api-versions`, Prometheus |
| 4 | Test schema compatibility | Schema Registry UI |
| 5 | Adjust parallelism | Scale consumers to partition count |
| 6 | Enable debug logging | `LOG_LEVEL=DEBUG` in config |
| 7 | Check network connectivity | `ping`, `telnet kafka:9092`, `tcpdump` |
| 8 | Implement retries/timeouts | Producer/Consumer config tuning |
| 9 | Validate DLQ | Check for failed messages |
| 10 | Restart consumers (if needed) | `kubectl rollout restart` or `kafka-consumer-groups --reset-offsets` |

---

## **Final Notes**
- **Streaming systems are complex** → Focus on **observability** (logs, metrics, traces).
- **Start small** → Fix one consumer/group at a time.
- **Automate recovery** → Use DLQ, retries, and circuit breakers.
- **Test failure scenarios** → Chaos engineering prevents surprises.

By following this guide, you should be able to **isolate, diagnose, and resolve** most Streaming Integration issues efficiently. For persistent problems, consider:
- **Upgrading Kafka/Pulsar** (check release notes for known issues).
- **Re-evaluating architecture** (e.g., switching to a managed service like Confluent Cloud).