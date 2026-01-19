# **Debugging Streaming Guidelines (Event-Driven Architecture) – A Troubleshooting Guide**
*A focused guide for diagnosing and resolving common issues in stream-based data processing systems (Kafka, Pulsar, RabbitMQ, AWS Kinesis, etc.).*

---

## **1. Introduction**
Streaming systems process data in real-time, ensuring low-latency event handling. However, they introduce complexity in event ordering, duplicate processing, backpressure management, and consumer reconnection. This guide provides a structured approach to diagnosing and fixing streaming-related issues.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms to confirm the problem domain:

### **Consumer-Side Issues**
✅ **Event ordering violations** (out-of-order messages)
✅ **Duplicate messages** appearing in consumer logs
✅ **Slow processing** (lag in consumer offsets vs. producer offsets)
✅ **Consumer crashes** (OOM, segmentation faults, or Java/Python exceptions)
✅ **Consumer disconnects** (reconnects loop, `Consumer` not waking up)
✅ **Infinite retries** on failed message processing

### **Producer-Side Issues**
✅ **Failed message deliveries** (retries not working)
✅ **Producer stuck** (no acknowledgments from broker)
✅ **Producer buffer overflow** (`BufferExhaustedException`)
✅ **Partitioning misconfiguration** (key-based vs. randomized)

### **Broker/Cluster Issues**
✅ **High disk I/O or CPU usage** (broker slowing down)
✅ **Broker crashes** (logs show `OutOfMemoryError` or `UnixError`)
✅ **Replication lag** (leader-follower synchronization delays)
✅ **Under-replicated partitions** (unhealthy broker cluster)
✅ **Slow commits** (`transactional` vs. `async` commits)

### **Application-Level Issues**
✅ **Unresponsive service** (streaming backend blocking main thread)
✅ **Metric alerts** (high `in-flight-requests`, `pending-commits`)
✅ **External dependency failures** (database locks, slow API responses)

---
## **3. Common Issues & Fixes (With Code Examples)**

### **⚠️ Issue 1: Duplicate Messages**
**Symptoms:**
- Logs contain the same event ID multiple times.
- Checksum failures in business logic.

**Root Causes:**
- Consumer crash & reconnect (initial offset reset).
- Producer retries due to transient failures.
- Idempotent producer not configured.

**Fixes:**

#### **A) Producer-Level Fix (Idempotent Producer)**
Ensure your producer uses idempotence (Kafka/Pulsar) to prevent duplicates:
```python
# Python (Confluent Kafka)
conf = {
    'bootstrap.servers': 'kafka:9092',
    'enable.idempotence': True,  # Disables retries for duplicates
    'max.in.flight.requests.per.connection': 5  # Default for idempotence
}
producer = Producer(conf)
```

#### **B) Consumer-Level Fix (Offset Management)**
Use `exactly_once` semantics (Kafka) or `transactional` consumers:
```java
// Java (Kafka)
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT, false);
props.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed"); // Filter duplicates
```

#### **C) Business Logic Fix (Idempotent Processing)**
If duplicates are unavoidable, use a deduplication mechanism (e.g., Redis or database):
```python
# Python (Example: Track processed event IDs)
seen = set()
while True:
    msg = consumer.poll(timeout=1.0)
    if msg.key() and msg.key().decode() not in seen:
        seen.add(msg.key().decode())
        process_message(msg.value())
```

---
### **⚠️ Issue 2: Event Ordering Violations**
**Symptoms:**
- Logs show `EventA` followed by `EventB`, but `EventA` should come after.
- Client-side timestamps are inconsistent.

**Root Causes:**
- Key-based partitioning mismatches.
- Consumer lag causing reordering.
- Broker-side compression reordering.

**Fixes:**

#### **A) Ensure Consistent Partitioning**
Use a stable key (e.g., `user_id`) for ordering:
```java
// Java (Kafka)
producer.send(new ProducerRecord<>("events", userId, eventData), (metadata, exception) -> {
    if (exception != null) log.error("Failed to send", exception);
});
```

#### **B) Consumer Parallelism Adjustment**
If using multiple consumers, ensure `partition.count` ≥ `consumer.instances`:
```yaml
# Kafka Consumer Group Config
partitions-per-consumer: 1  # Prevents interleaving
```

#### **C) Client-Side Time Synchronization**
If using timestamps, ensure all clients sync time (NTP):
```bash
# Fix time drift (Linux)
sudo apt install ntp
sudo systemctl enable --now ntp
```

---
### **⚠️ Issue 3: Consumer Lag**
**Symptoms:**
- `consumer-lag` metric spikes.
- `poll()` returns only nulls for long periods.

**Root Causes:**
- Slow processing (business logic bottlenecks).
- Under-provisioned consumers.
- Broker backpressure.

**Fixes:**

#### **A) Scale Consumers Horizontally**
Add more instances to parallelize work:
```bash
# Kubernetes Deployment Example
resources:
  limits:
    cpu: "2"
    memory: "2Gi"
replicas: 5  # Match partition count
```

#### **B) Optimize Polling**
Increase `fetch.min.bytes` and `fetch.max.wait.ms` to reduce overhead:
```yaml
# Kafka Consumer Config
fetch.min.bytes: 1024  # Wait for 1KB before responding
fetch.max.wait.ms: 500  # Max wait time
```

#### **C) Monitor & Alert on Lag**
Use Prometheus + Grafana to detect lag trends:
```bash
# Alert Rule (Prometheus)
ALERT HighConsumerLag IF
  kafka_consumer_lag{topic="orders"} > 10000
  FOR 5m
  LABELS{severity="critical"}
```

---
### **⚠️ Issue 4: Producer Backpressure**
**Symptoms:**
- `BufferExhaustedException` in logs.
- Producer stuck (`send()` timeouts).

**Root Causes:**
- High throughput without buffer tuning.
- Slow consumer (producer → broker bottleneck).

**Fixes:**

#### **A) Increase Buffer Size**
Adjust `buffer.memory` and `batch.size`:
```yaml
# Kafka Producer Config
buffer.memory: 33554432  # 32MB
batch.size: 16384       # 16KB per batch
```

#### **B) Implement Flow Control**
Use `max.block.ms` to avoid indefinite blocking:
```python
# Python (Confluent Kafka)
conf = {
    'max.block.ms': 1000,  # Block max 1 second
    'block.on.buffer.full': True
}
producer = Producer(conf)
```

#### **C) Queue Messages Offload**
Use a pre-commit queue (e.g., Redis) to decouple producer/consumer:
```python
# Python (Async Redis Queue)
import redis.asyncio as redis
r = redis.Redis(host="redis", db=0)
async def send_to_queue(data):
    await r.lpush("events", data)
```

---
### **⚠️ Issue 5: Broker Crashes**
**Symptoms:**
- `ZooKeeper` connection errors.
- `KafkaServer` OOM or segfault.

**Root Causes:**
- Disk I/O saturation.
- JVM heap exhaustion.
- Corrupt log segments.

**Fixes:**

#### **A) Check Disk I/O**
Monitor `iostat` and `df -h`:
```bash
# Check disk usage
df -h | grep /var/lib/kafka
# Check I/O wait (high > 10%)
iostat -x 1
```

#### **B) Adjust Kafka Server Heap**
Increase `kafka.server` JVM heap:
```ini
# config/server.properties
log4j.log4j.properties.appenders.FileAppender2.file=/var/log/kafka/server.log
kafka.logs.flush.interval.messages=10000  # Reduce disk writes
```

#### **C) Recover Corrupt Logs**
Use `kafka-dump-log-shared` to inspect:
```bash
kafka-dump-log-shared --files --print-data-log --offsets-only /tmp/kafka-logs
```
Then restore from a clean backup.

---
## **4. Debugging Tools & Techniques**
| Tool               | Purpose                          | Command/Usage                          |
|--------------------|----------------------------------|----------------------------------------|
| **Kafka Tools**    | Cluster health                   | `kafka-topics.sh --describe`           |
| **Confluent CLI**  | Producer/Consumer monitoring      | `kafka-console-consumer --bootstrap-server` |
| **Burrow**         | Consumer lag detection           | Install via Helm: `helm install burrow` |
| **JMX Exporter**   | Broker metrics (Prometheus)      | `kafka-server-start.sh --jmx-port=9999` |
| **Wireshark**      | Network-level inspection         | Filter `tcp.port == 9092`              |
| **GDB**            | Broker crash analysis             | `gdb --core=/var/lib/kafka/core`       |

**Key Metrics to Watch:**
- `UnderReplicatedPartitions`
- `RequestQueueTimeAvg` (broker backpressure)
- `RecordRejectedRate` (consumer lag)

---
## **5. Prevention Strategies**
1. **Infrastructure:**
   - **Auto-scaling:** Use Kubernetes HPA for consumers.
   - **Monitoring:** Set up alerts for `ConsumerLag`, `BrokerDiskPressure`.
   - **Backup:** Regularly snapshot Kafka logs (`kafka-log-dirs`).

2. **Code Best Practices:**
   - **Idempotency:** Always design for duplicates.
   - **Timeouts:** Set `max.poll.interval.ms` (default 5min → 300s).
   - **Retries:** Limit retries to avoid infinite loops (e.g., `max.poll.records=500`).

3. **Testing:**
   - **Chaos Testing:** Simulate broker failures (Gremlin).
   - **Load Testing:** Use `kafka-producer-perf-test`.
   - **End-to-End:** Test with `kafka-console-producer` + consumer app.

4. **Configuration:**
   - **Avoid Defaults:** Override `fetch.max.bytes`, `linger.ms`.
   - **Use Topics Wisely:** Avoid single-partition topics for parallelism.

---
## **6. Quick Reference Table**
| **Symptom**               | **Likely Cause**               | **Immediate Fix**                     |
|---------------------------|---------------------------------|----------------------------------------|
| Duplicate messages        | Consumer crash/reconnect       | Enable idempotence + checksum checks  |
| Event ordering broken     | Key-based partitioning mismatch | Use stable keys + `partitioner`        |
| Consumer lag              | Slow processing                | Scale consumers + optimize polling     |
| Producer stuck            | Buffer exhaustion              | Increase `buffer.memory` + flow control |
| Broker crashes            | Disk I/O or heap issues        | Check `iostat`, adjust JVM heap        |

---
## **7. Next Steps**
1. **Reproduce isolated:** Disable unrelated services (e.g., RBAC, auth).
2. **Check logs:** Broker (`server.log`), producer/consumer (`stdout`).
3. **Isolate component:** Test with a single partition/topic.
4. **Escalate if needed:** Engage Kafka/Pulsar community or vendor support.

---
**Final Tip:** Start with the **symptom checklist** to narrow down the issue before diving into logs. Use the **quick reference table** for immediate fixes, then implement long-term **prevention strategies**.

---
*Last updated: [Date]. For further reading, refer to the [Confluent Debugging Guide](https://docs.confluent.io/platform/current/installation/configuration/reference.html).*