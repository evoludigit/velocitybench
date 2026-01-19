# **Debugging **Streaming Testing**: A Troubleshooting Guide**
*For Backend Engineers Handling Real-Time Data Processing Pipelines*

---
## **1. Introduction**
Streaming Testing (e.g., Kafka, Kinesis, Pulsar, or custom streaming backends) involves processing data in real-time or near-real-time. Unlike batch processing, failures—such as data loss, lag, or incorrect transformations—can be harder to diagnose due to the event-driven nature of the system.

This guide focuses on **practical debugging** for common streaming issues, with a focus on **quick resolution** while maintaining data integrity.

---

## **2. Symptom Checklist**
Before diving into fixes, systematically check for these symptoms:

| **Symptom**                     | **Possible Root Cause**                          | **Quick Check**                                  |
|----------------------------------|--------------------------------------------------|--------------------------------------------------|
| **Data does not appear in target** | Producer failure, broker misconfiguration        | Check producer logs, topic existence, permissions |
| **High consumer lag**            | Slow processing, backpressure, or dead letters   | Monitor consumer metrics, log slow operations    |
| **Duplicate messages**           | At-least-once delivery, checkpoint issues       | Verify checkpointing logic, idempotent consumers   |
| **Lost messages**                | Broker failure, log compaction issues            | Check broker logs, topic retention settings      |
| **Schema mismatches**            | Producer/consumer version skew, Avro/Protobuf errors | Validate schema registry logs                     |
| **Throttling/rate-limiting**     | Quota enforcement, network congestion           | Check broker logs for rate limits, bandwidth     |
| **Crashes in streaming jobs**    | Unhandled exceptions, OOM errors                | Review job logs, increase heap size if needed     |

---

## **3. Common Issues and Fixes**
### **3.1 Producer Issues**
#### **Issue 1: Messages Not Sent**
**Symptoms:**
- `ProducerRecord` not appearing in topic.
- No errors in logs, but no data in consumers.

**Debugging Steps:**
1. **Verify producer config:**
   ```java
   props.put("bootstrap.servers", "localhost:9092");
   props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
   props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
   ```
   - Check if `bootstrap.servers` is correct.
   - Ensure `acks=all` (if durability is critical).

2. **Test with a simple producer:**
   ```java
   Producer<String, String> producer = new KafkaProducer<>(props);
   producer.send(new ProducerRecord<>("test-topic", "key", "value")).get();
   ```
   - If this fails, the issue is networking/broker-side.

3. **Check topic existence:**
   ```bash
   kafka-topics.sh --bootstrap-server localhost:9092 --list
   ```
   - If missing, create it:
     ```bash
     kafka-topics.sh --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
     ```

**Fix:**
- If permissions are denied:
  ```bash
  kafka-acls.sh --add --allow-principal User:admin --operation WRITE --topic test-topic
  ```

---

#### **Issue 2: Producer Timeouts**
**Symptoms:**
- `TimeoutException` or `NotEnoughReplicasException`.

**Debugging Steps:**
1. **Check broker health:**
   ```bash
   kafka-broker-api-versions.sh --bootstrap-server localhost:9092
   ```
   - If brokers are down, restore them.

2. **Increase timeouts:**
   ```java
   props.put("connection.timeout.ms", 10000); // 10s
   props.put("request.timeout.ms", 30000);  // 30s
   ```

3. **Ensure replication factor ≥ 2** (for high availability).

---

### **3.2 Consumer Issues**
#### **Issue 1: High Consumer Lag**
**Symptoms:**
- Consumers fall behind (`lag` in Kafka metrics).
- New messages pile up in the topic.

**Debugging Steps:**
1. **Check consumer metrics:**
   ```bash
   kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group my-group
   ```
   - If `lag > 0`, the consumer is slow.

2. **Profile slow processing:**
   ```java
   // Log processing time per message
   long start = System.currentTimeMillis();
   // ... processing logic ...
   System.out.println("Processing time: " + (System.currentTimeMillis() - start) + "ms");
   ```

3. **Increase partitions** (if single consumer is overloaded):
   ```bash
   kafka-topics.sh --alter --topic test-topic --partitions 4
   ```

**Fix:**
- Optimize business logic (e.g., parallelize processing).
- Enable **exactly-once processing** if needed:
  ```java
  props.put("enable.auto.commit", "false");
  props.put("isolation.level", "read_committed");
  ```

---

#### **Issue 2: Duplicate Messages**
**Symptoms:**
- Same message processed multiple times.

**Debuging Steps:**
1. **Check if it’s a Kafka retry:**
   - Kafka guarantees **at-least-once** delivery. If `max.in.flight.requests.per.connection > 1`, duplicates may occur.

2. **Verify checkpointing:**
   - If using **Spring Kafka**, ensure `errorHandler` discards duplicates:
     ```java
     @Bean
     public ContainerProperties.KafkaListenerContainerFactory<?> kafkaListenerContainerFactory(
         ConsumerFactory<Object, Object> consumerFactory) {
         KafkaMessageListenerContainerFactory<Object, Object> factory =
             new KafkaMessageListenerContainerFactory<>();
         factory.setConsumerFactory(consumerFactory);
         factory.setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
         return factory;
     }
     ```

3. **Idempotent processing:**
   - Design consumers to handle duplicates (e.g., deduplicate by `messageId`).

---

### **3.3 Broker Issues**
#### **Issue 1: Topic Not Found**
**Symptoms:**
- `TopicNotFoundException`.

**Fix:**
```bash
# Create topic
kafka-topics.sh --create --topic my-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 2
```

#### **Issue 2: Broker Crash**
**Symptoms:**
- Leaders fail, consumers get `NotLeaderForPartitionException`.

**Debugging Steps:**
1. **Check broker logs (`/logs/server.log`)** for errors.
2. **Restart the broker** (if recoverable):
   ```bash
   bin/zookeeper-server-stop.sh
   bin/kafka-server-stop.sh
   bin/zookeeper-server-start.sh
   bin/kafka-server-start.sh
   ```
3. **Monitor under-replicated partitions:**
   ```bash
   kafka-topics.sh --describe --topic my-topic --bootstrap-server localhost:9092
   ```
   - If `UnderReplicatedPartitions` > 0, wait or force rebalance.

---

### **3.4 Schema Registry Issues (Avro/Protobuf)**
#### **Issue 1: Schema Evolution Mismatch**
**Symptoms:**
- `SchemaMismatchException`.

**Debugging Steps:**
1. **Check schema version:**
   ```bash
   curl -X GET http://localhost:8081/subjects/my-topic-value/versions
   ```
2. **Update producer/consumer to match latest schema**.

**Fix:**
- If backward compatibility is needed, use **schema evolution** (e.g., adding optional fields).

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                          |
|------------------------|-----------------------------------------------|----------------------------------------------|
| **Kafka CLI**          | Topic/broker management                       | `kafka-topics.sh --describe`                 |
| **Kafka Consumer**     | Debugging consumed messages                   | `kafka-console-consumer.sh --topic test`     |
| **JMX Metrics**        | Monitoring producer/consumer lag             | `jconsole` (connect to Kafka JMX port)       |
| **Prometheus + Grafana** | Real-time monitoring (lag, throughput)      | Scrape Kafka metrics (`kafka-exporter`)    |
| **Kafka Streams Debug** | Testing stream transformations               | `StreamsBuilder` + `to()` for testing       |
| **Log4j Logging**      | Fine-grained debug logs                       | `log4j.logger.org/apache/kafka=DEBUG`        |
| **Kafka Test Containers** | Local dev testing                          | Docker + Kafka in tests                      |

---

## **5. Prevention Strategies**
### **5.1 Infrastructure Resilience**
- **Replication:** Ensure `replication.factor ≥ 2`.
- **Monitoring:** Set up alerts for:
  - High consumer lag (`kafka-consumer-groups --describe`).
  - Broker failures (`kafka-server-start` crashes).
- **Auto-scaling:** Use **Kafka Streams** or **Flink** for dynamic workloads.

### **5.2 Code Best Practices**
| **Practice**               | **Implementation**                          |
|----------------------------|---------------------------------------------|
| **Idempotent Consumers**   | Use transactional IDs or deduplication keys |
| **Checkpointing**          | Enable `enable.auto.commit=false`          |
| **Backpressure Handling**  | Throttle producers if consumers lag         |
| **Schema Evolution**       | Use **Schema Registry** for backward compatibility |
| **Error Handling**         | Dead-letter queues (DLQ) for failed records |

### **5.3 Testing Strategies**
| **Test Type**               | **Tool/Approach**                          |
|----------------------------|--------------------------------------------|
| **Unit Tests**             | Mock Kafka producers/consumers (`TestContainers`) |
| **Integration Tests**      | Deploy real Kafka cluster locally (`Docker`) |
| **Chaos Testing**          | Kill brokers/consumers to test recovery    |
| **Performance Testing**    | Load test with `kafka-producer-perf-test.sh` |

---

## **6. Quick Reference Cheat Sheet**
| **Problem**               | **First Steps**                              |
|---------------------------|----------------------------------------------|
| **Producer not sending**  | Check `bootstrap.servers`, topic existence  |
| **Consumer lagging**      | Profile slow operations, increase partitions |
| **Duplicates**            | Use `enable.auto.commit=false`              |
| **Broker down**           | Restart broker, check logs                   |
| **Schema errors**         | Update schema registry compliance           |

---
## **7. Final Notes**
- **Start small:** Test with a **single partition** before scaling.
- **Log everything:** Enable debug logs for producers/consumers.
- **Leverage metrics:** Use **Prometheus + Grafana** for observability.
- **Automate recovery:** Use **Kafka Streams** or **Flink** for resilient batch/stream processing.

For advanced debugging, refer to:
- [Kafka Debugging Guide](https://kafka.apache.org/documentation/)
- [Confluent Schema Registry Docs](https://docs.confluent.io/platform/current/schema-registry/index.html)

---
**Happy debugging!** 🚀