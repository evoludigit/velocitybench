# **Debugging Streaming Monitoring: A Practical Troubleshooting Guide**
*For Backend Engineers*

---

## **1. Introduction**
The **Streaming Monitoring** pattern involves real-time data ingestion, processing, and alerting—typically using Kafka, Pulsar, or similar streaming platforms. When misconfigured or under stress, this can lead to latency spikes, missed alerts, or data loss.

This guide focuses on **quick resolution** for common failures, with actionable steps, code snippets, and prevention tips.

---

## **2. Symptom Checklist**
Before diving into fixes, check if your issue matches these symptoms:

| **Symptom**               | **Possible Cause**                          |
|---------------------------|---------------------------------------------|
| Alerts delayed by >30s    | Kafka lag, slow consumers, or rate limits   |
| Missing events in logs    | Consumer rebalancing, offset errors         |
| High CPU/memory in workers| Backpressure, inefficient processing        |
| Crashes on scale-up       | Resource contention, Zookeeper issues       |
| Produced events lost      | Broker failures, ack timeout misconfig      |
| Slow query response       | Schema evolution, unoptimized aggregations  |

**Next Step:** If multiple symptoms exist, prioritize based on SLA impact.

---

## **3. Common Issues and Fixes**

### **Issue 1: Kafka Consumer Lag**
**Scenario:** Alerts are delayed because consumers can’t keep up with producers.
**Root Cause:** Underpowered consumers, slow processing logic, or high throughput.

#### **Debugging Steps:**
1. **Check Consumer Lag**
   ```bash
   bin/kafka-consumer-groups.sh --bootstrap-server <broker> --group <group-id> --describe
   ```
   - If `LAG` > 10x partition count → scale consumers or optimize processing.

2. **Optimize Consumer**
   ```java
   // Use larger batches to reduce overhead
   props.put(ConsumerConfig.FETCH_MAX_BYTES_CONFIG, 52428800); // 50MB
   props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);
   ```
   - *Alternative:* Increase parallelism with `--partitions` flag.

3. **Monitor Backpressure**
   ```bash
   jstack <pid> | grep "java.nio.channels.ClosedByInterruptException"
   ```
   - If present, adjust `fetch.min.bytes` or retry logic.

---

### **Issue 2: Missing Events (Offset Errors)**
**Scenario:** Data is lost after restarts or rebalances.

#### **Debugging Steps:**
1. **Verify Offset Commitments**
   ```bash
   bin/kafka-consumer-groups.sh --bootstrap-server <broker> --group <group-id> --describe --verbose
   ```
   - Check `COMMITTED OFFSET` vs `LAG`. If inconsistent, enable `enable.auto.commit` with a low `interval.ms`.

2. **Use Exactly-Once Semantics**
   ```java
   // Enable idempotent producer
   props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
   props.put(ProducerConfig.ACKS_CONFIG, "all");
   ```

3. **Handle Rebalances Gracefully**
   ```java
   // In consumer poll loop:
   try {
       records = consumer.poll(Duration.ofMillis(100));
   } catch (WakeupException e) {
       // Rebalancing in progress, reset offset
       consumer.seekToEnd(partition);
   }
   ```

---

### **Issue 3: High CPU/Memory Spikes**
**Scenario:** Workers crash due to unmanaged resources.

#### **Debugging Steps:**
1. **Profile Memory Usage**
   ```bash
   jcmd <pid> GC.heap_histogram > heap.txt  # Analyze heap dumps
   ```
   - Look for leaks in caches or event stores.

2. **Optimize Processing**
   ```java
   // Avoid blocking calls in consumer logic
   CompletableFuture.supplyAsync(() -> processEvent(event))
       .thenAccept(this::handleResult);
   ```

3. **Set Resource Limits**
   ```yaml
   # Docker/Kubernetes resource constraints
   resources:
     limits:
       cpu: "2"
       memory: "4Gi"
   ```

---

### **Issue 4: Broker Failures**
**Scenario:** Producers fail with "Not Enough In-Sync Replicas" errors.

#### **Debugging Steps:**
1. **Check Replication Health**
   ```bash
   bin/kafka-topics.sh --describe --topic <topic>
   ```
   - If `ISR` size < `min.insync.replicas` (default: 1), adjust:
     ```bash
     bin/kafka-configs.sh --alter --entity-type topics --entity-name <topic> --add-config min.insync.replicas=2
     ```

2. **Monitor Broker Health**
   ```bash
   curl http://<broker>:6060/v1/broker/topics/<topic>/partitions/<partition>
   ```
   - Look for `leader` vs `replicas` mismatch.

---

### **Issue 5: Schema Evolution Failures**
**Scenario:** Consumers reject events due to schema drift.

#### **Debugging Steps:**
1. **Validate Schema Compatibility**
   ```bash
   avro schema-validate --schema-file schema_1.avsc --data-file event.json --schema-file schema_2.avsc
   ```
   - Ensure backward/forward compatibility.

2. **Use Schema Registry**
   ```java
   // Configure in producer
   props.put("schema.registry.url", "http://schema-registry:8081");
   props.put("value.schema", "avro");
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                          | **Example Command**                     |
|------------------------|---------------------------------------|-----------------------------------------|
| `kafka-consumer-groups`| Monitor consumer lag                  | `--bootstrap-server <broker> --group <id> --describe` |
| `jstack`               | Debug thread deadlocks                | `jstack <pid> > threads.txt`            |
| `ksqldb`               | SQL-based streaming analytics          | `CREATE TABLE events WITH (...)`          |
| `kafka-producer-perf-test` | Stress-test producers | `--topic <topic> --num-records 100000` |

**Quick Tip:** Use Kubernetes `livenessProbe` to detect unhealthy consumers:
```yaml
livenessProbe:
  exec:
    command: ["/bin/sh", "-c", "kafka-consumer-groups --bootstrap-server <broker> --describe > /dev/null"]
```

---

## **5. Prevention Strategies**
1. **Monitor Kafka Metrics**
   - Track `kafka.server:type=KafkaServer,name=BytesInPerSec` in Prometheus.
   - Set up alerts for `consumer-lag > 1000`.

2. **Autoscale Consumers**
   - Use K8s `HorizontalPodAutoscaler` with custom metrics from Kafka.

3. **Test Failover**
   ```bash
   # Simulate broker failure
   kafka-consumer-perf-test --bootstrap-server <broker> --topic test --failed-broker-ratio 0.5
   ```

4. **Idempotent Processing**
   - Store events in a transactional sink (e.g., DynamoDB TTL + replay logic).

---

## **6. Quick Reference Cheat Sheet**
| **Issue**               | **Immediate Fix**                     | **Long-Term Fix**                     |
|-------------------------|---------------------------------------|---------------------------------------|
| Consumer lag            | Scale consumers or increase batch size | Optimize processing logic           |
| Missing events          | Enable `enable.auto.commit`           | Use exactly-once semantics            |
| High CPU                | Limit parallelism or optimize code    | Profile with `async-profiler`         |
| Broker failure          | Increase `min.insync.replicas`        | Add replica brokers                   |
| Schema conflicts        | Rollback schema change                | Use schema registry + backward compat|

---

## **7. Conclusion**
Streaming Monitoring failures often stem from **misconfigured consumers, replication issues, or inefficient processing**. This guide prioritizes:
1. **Symptom tracking** (lag, crashes, missing data).
2. **Root-cause analysis** (metrics, logs, code).
3. **Quick fixes** (offsets, batching, scaling).

**Final Checklist Before Deployment:**
- [ ] Test failover scenarios.
- [ ] Validate schema compatibility.
- [ ] Set up alerting for `consumer-lag` and `broker-health`.

By following these steps, you’ll resolve 90% of streaming issues within **30 minutes**. For persistent problems, consider tracing with **OpenTelemetry** or **Jaeger**.