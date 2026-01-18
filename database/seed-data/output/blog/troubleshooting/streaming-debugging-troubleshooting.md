# **Debugging [Streaming Debugging]: A Troubleshooting Guide**
*Accelerating real-time diagnostics with structured logging and event-driven observability*

---

## **1. Introduction**
Streaming Debugging refers to the practice of capturing, analyzing, and resolving issues in **real-time or near-real-time** systems where traditional logging (batch-based) is insufficient. This includes:
- Event-driven architectures (Kafka, RabbitMQ, AWS Kinesis)
- Real-time analytics pipelines (Spark, Flink)
- IoT/streaming applications (MQTT, WebSockets)
- Microservices with high-throughput APIs

Unlike traditional debugging, which relies on historical logs or manual sampling, Streaming Debugging enables **proactive issue detection** and minimizes downtime.

---

## **2. Symptom Checklist: When to Apply Streaming Debugging**
Check if your system exhibits any of the following:

### **A. Performance & Latency Issues**
- [ ] High **end-to-end latency** (e.g., API responses > 1s)
- [ ] **Spikes in processing time** (e.g., sudden drops in throughput)
- [ ] **Backpressure** detected (e.g., Kafka consumer lag, buffer overflows)
- [ ] **Unstable metrics** (e.g., p99 latency fluctuating wildly)

### **B. Data Integrity & Consistency Problems**
- [ ] **Duplicate/missing events** in logs or databases
- [ ] **Schema mismatches** (e.g., Avro/Protobuf deserialization errors)
- [ ] **Corrupt payloads** (e.g., malformed JSON/XML)
- [ ] **Event ordering violations** (e.g., out-of-order processing)

### **C. System Instability & Errors**
- [ ] **Crashes in streaming workers** (e.g., Spark executors dying)
- [ ] **Resource exhaustion** (e.g., OOM errors in Kafka consumers)
- [ ] **Deadlocks in streaming pipelines** (e.g., stuck partitions)
- [ ] **Permission denied** (e.g., IAM roles failing in AWS Kinesis)

### **D. Observability Gaps**
- [ ] **Lack of real-time traces** (e.g., no distributed tracing in microservices)
- [ ] **No context in logs** (e.g., missing request IDs, timestamps)
- [ ] **Alert fatigue** (e.g., too many false positives in Prometheus/Grafana)
- [ ] **No correlation between logs and metrics** (e.g., logs don’t match Prometheus data)

---
## **3. Common Issues & Fixes (with Code Examples)**

### **Issue 1: High Latency in Kafka Consumers**
**Symptoms:**
- Consumer lag > 1 min (visible in **Kafka Consumer Lag Monitor**)
- **"Rebalance in progress"** errors

**Root Causes:**
- Slow consumer processing (e.g., blocking I/O, CPU-bound operations)
- **Partition count mismatch** (too few partitions → bottlenecks)
- **Network latency** between brokers and consumers

**Fixes:**

#### **Optimize Consumer Configuration (Java/Kafka)**
```java
Properties props = new Properties();
props.put("bootstrap.servers", "kafka:9092");
props.put("group.id", "my-group");
props.put("auto.offset.reset", "earliest");
props.put("enable.auto.commit", "false"); // Manual commits for better control
props.put("max.poll.interval.ms", "300000"); // Extend poll timeout if needed
props.put("fetch.max.bytes", "52428800"); // Increase for large messages
props.put("fetch.min.bytes", "1"); // Avoid small fetches
props.put("session.timeout.ms", "30000"); // Adjust if rebalances are frequent
```

#### **Monitor Lag with `kafka-consumer-groups`**
```bash
kafka-consumer-groups --bootstrap-server kafka:9092 --describe --group my-group
```
**Expected Output:**
```
GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
my-group        my-topic        0          10000           10005           5
```

#### **Scale Consumers Horizontally**
- Increase **number of consumers** (each handles one partition by default).
- Use **key-based partitioning** to avoid hot partitions:
  ```java
  props.put("partitioner.class", "com.example.MyPartitioner");
  ```

---

### **Issue 2: Schema Evolution Failures (Avro/Protobuf)**
**Symptoms:**
- **"Schema mismatch"** errors in logs
- **Failed deserialization** (e.g., `org.apache.avro.SchemaParseException`)

**Root Causes:**
- Backward/incompatible schema changes
- Missing **schema registry** (Confluent Schema Registry)

**Fixes:**

#### **Use a Schema Registry**
**Example (Confluent Schema Registry):**
```bash
# Register a schema
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
     --data '{"schema": "{\"type\":\"record\",\"name\":\"User\",\"fields\":[{\"name\":\"id\",\"type\":\"int\"}]}"}' \
     http://schema-registry:8081/subjects/user-value/versions
```

#### **Handle Schema Evolution Gracefully (Java)**
```java
// Using Confluent Kafka library
GenericRecord record = new GenericDeserializer<>(new Schema.Parser().parse(schema)).deserialize(
    null,
    (byte[]) message.value()
);
```

#### **Enable Schema Compatibility Mode**
```bash
# Allow backward compatibility
curl -X PUT -H "Content-Type: application/vnd.schemaregistry.v1+json" \
     -d '{"compatibility": "BACKWARD"}' \
     http://schema-registry:8081/config/user-value
```

---

### **Issue 3: Missing Events in Streaming Pipeline**
**Symptoms:**
- **Gaps in data** (e.g., 100 events expected, only 95 processed)
- **Log entries like "No records received"**

**Root Causes:**
- **Consumer offset not committed** (leading to reprocessing)
- **Topic configuration issues** (e.g., `retention.ms` too low)
- **Producer not sending messages reliably**

**Fixes:**

#### **Ensure Offsets Are Committed Properly**
```java
consumer.commitSync(); // Manual commit (recommended for critical data)
```
or (asynchronous):
```java
consumer.commitAsync((metadata, exception) -> {
    if (exception != null) {
        logger.error("Commit failed", exception);
    }
});
```

#### **Check Topic Retention Settings**
```bash
kafka-topics --bootstrap-server kafka:9092 --describe --topic my-topic
```
**Fix:** Increase retention if needed:
```bash
kafka-configs --bootstrap-server kafka:9092 --alter --entity-type topics \
             --entity-name my-topic --add-config retention.ms=604800000
```

#### **Verify Producer Acks**
```java
props.put("acks", "all"); // Ensure full commit to broker
props.put("retries", Integer.MAX_VALUE); // Retry indefinitely
```

---

### **Issue 4: Distributed Tracing Missing in Microservices**
**Symptoms:**
- **No trace IDs** in logs
- **Cannot correlate API calls → processing → database**

**Root Causes:**
- **No tracing library** (e.g., OpenTelemetry not configured)
- **Sampling rate too low** (missing critical traces)

**Fixes:**

#### **Add OpenTelemetry to Your App (Python Example)**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_order") as span:
    # Your business logic here
    span.set_attribute("user_id", "123")
```

#### **Configure Sampling in Jaeger/Zipkin**
```yaml
# jaeger.yaml (sampling rate 100%)
sampling:
  manager_host: jaeger-collector
  manager_port: 5778
  manager_path: /api/v1/sampling
  const_sampler:
    sampling_rate: 1.0
```

#### **Correlate Logs with Trace IDs**
Example log format:
```
[2023-10-01 12:00:00] [TRACE_ID=abc123] ERROR: Failed to process order
```

---

### **Issue 5: Resource Exhaustion (OOM in Stream Processors)**
**Symptoms:**
- **"Out of Memory"** errors in logs
- **Spark/Flink tasks crashing**

**Root Causes:**
- **Large state in RocksDB** (e.g., Spark StateStore)
- **Memory leaks in custom code**
- **Insufficient `memory.overhead` in Docker**

**Fixes:**

#### **Tune Spark Streaming Memory Settings**
```scala
val conf = new SparkConf()
  .set("spark.streaming.backpressure.enabled", "true") // Auto-adjust batch intervals
  .set("spark.default.parallelism", "200") // Match partition count
  .set("spark.executor.memory", "8g") // Increase executor memory
  .set("spark.memory.fraction", "0.6") // More memory for processing
  .set("spark.memory.storageFraction", "0.3") // Balance storage
```

#### **Use RocksDB for State (Flink Example)**
```java
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.days(1))
    .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
    .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
    .build();

ValueStateDescriptor<String> descriptor = new ValueStateDescriptor<>(
    "myState", String.class);
descriptor.enableTimeToLive(ttlConfig);
```

#### **Monitor Memory with `jcmd`**
```bash
jcmd <pid> VM.native_memory --detail
```
Look for **Heap, CodeCache, Metaspace** leaks.

---

## **4. Debugging Tools & Techniques**

### **A. Real-Time Monitoring**
| Tool               | Purpose                          | Command/Example                          |
|--------------------|----------------------------------|------------------------------------------|
| **Kafka Lag Monitor** | Track consumer lag               | `kafka-consumer-groups --bootstrap-server kafka:9092 --describe` |
| **Prometheus + Grafana** | Metrics dashboard | `prometheus query "rate(kafka_consumer_lag{topic='my-topic'}[5m])"` |
| **Jaeger/Zipkin**   | Distributed tracing              | `http://jaeger:16686/search?service=my-service` |
| **ELK Stack**       | Log aggregation & analysis       | `curl -X GET "elasticsearch:9200/my-index/_search?q=error:True"` |
| **Flink Web UI**    | Streaming job metrics            | `http://flink:8081`                      |

### **B. Debugging Workflow**
1. **Identify the source** (Producer? Consumer? Middleware?)
2. **Check logs in real-time** (`kubectl logs <pod> -f`)
3. **Correlate with traces** (Jaeger filter by `trace_id`)
4. **Reproduce locally** (Docker compose for Kafka/Flink)
5. **Isolate the failure** (e.g., test with a single partition)

### **C. Advanced Techniques**
- **Dynamic Retries**: Implement exponential backoff for failed messages:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
  def send_to_queue(message):
      producer.send(topic, message)
  ```
- **Dead Letter Queues (DLQ)**: Route failed messages to a separate topic.
- **Canary Deployments**: Gradually roll out changes with 100% monitoring.

---

## **5. Prevention Strategies**

### **A. Observability Best Practices**
✅ **Structured Logging** (JSON format):
```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "trace_id": "abc123",
  "level": "ERROR",
  "message": "Failed to process order",
  "order_id": "456",
  "partition": "0"
}
```

✅ **Metrics First**:
- Track **end-to-end latency**, **error rates**, **throughput**.
- Example Prometheus metrics:
  ```java
  counter("kafka_consumer_messages_total", "Total messages consumed");
  histogram("processing_latency_ms", "Time to process a message");
  ```

✅ **Schema Validation**:
- Use **Confluent Schema Registry** or **JSON Schema**.
- Reject malformed messages early:
  ```java
  try {
      schema.validate(record);
  } catch (SchemaException e) {
      log.error("Invalid schema: " + record);
      throw new ValidationException(e);
  }
  ```

### **B. Infrastructure Resilience**
🔹 **Auto-scaling Consumers**:
- Use **Kubernetes HPA** for Kafka consumers based on lag metrics.
- Example HPA rule:
  ```yaml
  metrics:
  - type: PodsMetricAverageValue
    pods:
      metric:
        name: kafka_consumer_lag
        target: 1000
  ```

🔹 **Chaos Engineering**:
- Test failure scenarios (e.g., kill a Kafka broker, simulate network partitions).
- Tools: **Gremlin**, **Chaos Mesh**.

🔹 **Backup & Disaster Recovery**:
- **Snapshot Kafka topics** periodically:
  ```bash
  kafka-dump-log --bootstrap-server kafka:9092 --topic my-topic --num-records 100000 > backup.json
  ```
- **Use S3/HDFS for durable storage**.

### **C. Developer Practices**
💡 **Local Testing with TestContainers**:
```java
@Container
KafkaContainer kafka = new KafkaContainer("confluentinc/cp-kafka:7.0.0");
@Test
void testStreamingPipeline() {
    // Simulate a producer-consumer flow
    kafka.start();
    String bootstrapServers = kafka.getBootstrapServers();
    // ...
}
```

💡 **Idempotent Processing**:
- Ensure reprocessing the same event doesn’t cause duplicates.
- Use **exactly-once semantics** in Kafka:
  ```java
  props.put("enable.idempotence", "true");
  props.put("transactional.id", "my-transactional-id");
  ```

💡 **Post-Mortem Reviews**:
- After an incident, answer:
  1. What happened?
  2. Why did it happen?
  3. How can we prevent it?
  4. What’s the timeline for fixes?

---

## **6. Quick Reference Cheat Sheet**
| **Issue**               | **First Check**                | **Quick Fix**                          |
|--------------------------|--------------------------------|----------------------------------------|
| Kafka consumer lag       | `kafka-consumer-groups`        | Scale consumers, check partitions      |
| Schema compatibility     | Schema Registry UI             | Set `compatibility=BACKWARD`            |
| Missing events           | `kafka-topics --describe`       | Check retention, offsets               |
| High latency             | Prometheus `processing_latency` | Tune parallelism, add caching          |
| OOM crashes              | `jcmd <pid> VM.native_memory`  | Increase memory, use RocksDB            |
| No traces                | Jaeger UI                      | Add OpenTelemetry + `tracer.start_as_current_span` |

---

## **7. Conclusion**
Streaming Debugging requires a **proactive approach**—shift from reacting to failures to **predicting and preventing them**. Key takeaways:
1. **Monitor in real-time** (Kafka lag, Prometheus metrics).
2. **Correlate logs with traces** (OpenTelemetry + Jaeger).
3. **Validate schemas early** (Schema Registry).
4. **Scale consumers dynamically** (Kubernetes HPA).
5. **Test for failures** (Chaos Engineering).

**Final Tip:** Start small—add structured logging and basic metrics to your existing system before overhauling everything. Small improvements in observability yield **huge ROI** in debugging speed.

---
**Next Steps:**
- [ ] Audit your Kafka topics for retention settings.
- [ ] Implement OpenTelemetry in 1 critical service.
- [ ] Set up a dashboard for consumer lag.