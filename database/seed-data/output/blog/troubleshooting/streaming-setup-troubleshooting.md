# **Debugging Streaming Setup: A Troubleshooting Guide**
*For Backend Engineers Handling Real-Time Data Pipelines*

---

## **1. Introduction**
The **"Streaming Setup"** pattern (e.g., Kafka, Pulsar, RabbitMQ, or custom pub/sub) involves producing, consuming, and processing data in real time. Misconfigurations, network issues, or serialization errors can disrupt data flow, leading to **lost messages, duplicates, or system jams**.

This guide provides a **structured approach** to diagnose and resolve common streaming failures efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom** | **Description** |
|-------------|----------------|
| **Producer Side** | ❌ Messages not being sent to the broker |
|  | ❌ High latency in publishing |
|  | ❌ Errors like `SerializationException` or `NoRouteToHostException` |
| **Consumer Side** | ❌ No consumer receipt of messages |
|  | ❌ Consumers stuck in `PENDING` state |
|  | ❌ Duplicate/consumed messages |
| **Broker Side** | ❌ Broker crashes/fails to start |
|  | ❌ High CPU/network usage |
|  | ❌ Partition out of sync |
| **Network** | ❌ Timeouts (`ConnectionRefused`, `ConnectionReset`) |
|  | ❌ Firewall/NAT blocking ports (e.g., 9092 for Kafka) |

**Quick first step:** Check logs (`/var/log/kafka/server.log`, `stdout` of consumer/producer apps) for recent errors.

---

## **3. Common Issues & Fixes (With Code Snippets)**

### **A. Producer Issues**

#### **1. Messages Not Being Sent**
**Symptom:**
- Producer logs show no errors, but messages vanish.

**Root Cause:**
- **Incorrect topic/partition configuration** (e.g., topic doesn’t exist).
- **Serialization failure** (e.g., wrong `Serializer` for message payload).

**Fix:**
```java
// Ensure topic exists before producing (Kafka)
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

// Create producer and verify topic exists
KafkaProducer<String, String> producer = new KafkaProducer<>(props);
try {
    producer.send(new ProducerRecord<>("my_topic", "key", "value"));
} catch (Exception e) {
    System.err.println("Topic/partition issue: " + e.getMessage());
}
```
**Debugging Tip:**
- Use `kafka-topics.sh` to list topics:
  `bin/kafka-topics.sh --list --bootstrap-server localhost:9092`

---

#### **2. High Latency**
**Symptom:**
- Messages take >1s to reach consumers.

**Root Cause:**
- **Small batch size** (`batch.size` too low).
- **Slow compression** (`compression.type=lz4` but CPU-bound).
- **Network congestion** (e.g., Kubernetes pod throttling).

**Fix:**
```java
props.put("batch.size", "16384");  // Increase batch size (default: 16KB)
props.put("linger.ms", "5");      // Wait up to 5ms for batching
props.put("compression.type", "snappy"); // Faster than lz4 for small payloads
```

**Debugging Tip:**
- Monitor broker metrics (`kafka-producer-perf-test.sh`) to check send delays.

---

### **B. Consumer Issues**

#### **1. No Messages Consumed**
**Symptom:**
- Consumer logs: `No more messages` or stuck in `poll()` with empty result.

**Root Cause:**
- **Consumer group misconfiguration** (e.g., wrong group.id).
- **Topic doesn’t exist** or is empty.
- **Consumer lag too high** (broker rebalances away partitions).

**Fix:**
```java
// Verify group.id and topic match
props.put("group.id", "my-consumer-group");
props.put("enable.auto.commit", "false"); // Manual commits reduce lag

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Collections.singletonList("my_topic"));

while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    if (!records.isEmpty()) {
        records.forEach(record -> System.out.println(record.value()));
    }
}
```
**Debugging Tip:**
- Check consumer lag:
  ```bash
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group my-consumer-group
  ```

---

#### **2. Duplicate Consumption**
**Symptom:**
- Same message processed multiple times.

**Root Cause:**
- **At-least-once delivery** (default in Kafka) with no idempotency.
- **Consumer rebalances** (e.g., after restart).

**Fix:**
- **Idempotent processing** (e.g., dedupe via DB or message ID).
- **Exactly-once semaphores** (Kafka `isolation.level=read_committed`).

**Example (Deduplication):**
```java
// Track seen IDs in a Set (e.g., Redis)
Set<String> seenIds = new HashSet<>();
for (ConsumerRecord record : records) {
    if (!seenIds.contains(record.key())) {
        process(record);
        seenIds.add(record.key());
    }
}
```

---

### **C. Broker Issues**

#### **1. Broker Crashes**
**Symptom:**
- Broker dies with `OutOfMemoryError` or disk full.

**Root Cause:**
- **Unbounded log retention** (`log.retention.ms` set too high).
- **No disk space** (`/tmp` or `logs` directory full).

**Fix:**
```bash
# Check disk usage
df -h

# Configure retention (Kafka config)
log.retention.hours=168    # 7-day retention
log.segment.bytes=1GB      # Split logs into 1GB chunks
```

**Debugging Tip:**
- Monitor broker JMX metrics (`kafka-run-class.sh` with `kafka.tools.JmxTool`).

---

#### **2. Partition Out of Sync**
**Symptom:**
- Leader/follower partitions misaligned.

**Root Cause:**
- **Network partition** (e.g., Kubernetes node failure).
- **Slave unreachable** (network timeout).

**Fix:**
```bash
# Force rebalance (Kafka)
kafka-leader-election.sh --bootstrap-server localhost:9092 --election-type leader --all-topic-partitions
```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique** | **Use Case** | **Example Command** |
|---------------------|-------------|----------------------|
| **Kafka CLI Tools** | Topic/partition checks | `kafka-topics.sh --describe --topic my_topic` |
| **Consumer Lag**    | Identify slow consumers | `kafka-consumer-groups.sh --describe` |
| **Producer Metrics** | Latency bottlenecks | `kafka-producer-perf-test.sh` |
| **JMX Monitoring**  | Broker health | `jconsole -J-Dcom.sun.management.jmxremote` |
| **Tracing (OpenTelemetry)** | End-to-end latency | `otel-agent --config file.yaml` |
| **Network Tools**   | Packet loss | `tcpdump port 9092` |

**Pro Tip:**
- Use **`kafka-consumer-groups.sh --bootstrap-server ... --group <group>`** to see active partitions.

---

## **5. Prevention Strategies**

### **A. Configuration Hardening**
| **Setting** | **Recommended Value** | **Why?** |
|-------------|----------------------|----------|
| `acks` | `1` or `all` | Balance durability/performance |
| `retries` | `3` | Handle transient failures |
| `max.in.flight.requests.per.connection` | `5` | Reduces duplicate messages |

### **B. Monitoring**
- **Broker:** `kafka-broker-api-versions.sh`, `kafka-server-start.sh --log4j.logger.kafka=DEBUG`
- **Consumer:** Track `records-lag-max` in Kafka metrics.
- **Network:** Use `netdata` or `Prometheus` for Kafka metrics.

### **C. Testing**
- **Chaos Engineering:** Use **Chaos Mesh** to simulate broker failures.
- **Load Testing:** `kafka-producer-perf-test.sh --topic test --num-records 1M --throughput -1 --record-size 1000`

### **D. Idempotency**
- **Kafka:** Enable `enable.idempotence=true`.
- **Custom:** Use message deduplication (e.g., UUIDs).

---

## **6. Summary Checklist for Quick Resolution**
1. **Check logs** (`/var/log/kafka/server.log`, app logs).
2. **Verify topic/partition existence** (`kafka-topics.sh`).
3. **Test producer/consumer connectivity** (`telnet localhost 9092`).
4. **Monitor consumer lag** (`kafka-consumer-groups.sh`).
5. **Adjust batching/compression** if latency is high.
6. **Check disk/CPU** for broker crashes.
7. **Enable idempotence** if duplicates persist.

---
**Final Note:** Streaming systems are **stateful**—always validate end-to-end flow (producer → broker → consumer) before scaling.

For deeper issues, refer to the [Kafka Troubleshooting Guide](https://kafka.apache.org/documentation/#troubleshooting).