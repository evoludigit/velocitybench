# **Debugging Queuing Integration: A Troubleshooting Guide**
*(Applicable to Kafka, RabbitMQ, AWS SQS/SNS, Azure Service Bus, JMS, etc.)*

---

## **1. Title**
**Debugging Queuing Integration: A Practical Troubleshooting Guide**
*For message brokers, event-driven architectures, and asynchronous workflows*

---

## **2. Symptom Checklist**
Before diving into fixes, systematically verify these symptoms:

### **A. Broker-Specific Failures**
✅ **Connection Issues**
- Unable to establish TCP/UDP connection to broker (e.g., `ConnectionRefused`, `TimeoutError`).
- Clients repeatedly reconnecting (e.g., `RabbitMQ: AMQP channel closed`, `Kafka: Broker not available`).

✅ **Message Delivery Blockages**
- Messages **not arriving** in the target queue/consumer (e.g., `NoConsumers` in RabbitMQ, `UnderReplicatedPartitions` in Kafka).
- Messages **stuck in flight** (e.g., high `unacked` count in RabbitMQ, `inflight` messages in Kafka).
- **Duplicate messages** appearing in consumers (likely retry/logic issues).

✅ **Performance Degradation**
- High **latency** in message processing (e.g., slow `ack` confirmation, network bottlenecks).
- **Memory pressure** causing broker crashes (e.g., Kafka `OutOfDirectMemoryError`, RabbitMQ `disk_full`).
- **Disk I/O saturation** (especially for persistent queues like Kafka/SQS).

✅ **Consumer Lag**
- Consumers **falling behind** (e.g., `Kafka Consumer Lag > 1000`, `RabbitMQ unacked messages growing`).
- Consumers **crashing silently** (check logs for `NullPointerException`, `TimeoutException`).

✅ **Schema/Serialization Errors**
- Messages **malformed** on deserialization (e.g., `JSON parse error`, `ProtocolBuffer unknown field`).
- **Schema evolution** breaking consumers (e.g., new fields in Avro/Protobuf).

✅ **Dead Letter Queues (DLQ) Overload**
- DLQ filling up with **unprocessable messages** (e.g., `InvalidMessageFormatException`).
- **No DLQ** configured, causing lost messages.

✅ **Authentication/Authorization Failures**
- `403 Forbidden` (AWS SQS), `AUTH failure` (RabbitMQ), `Kafka ACL denied`.
- **Expired credentials** or misconfigured IAM roles (AWS), `VHost` permissions (RabbitMQ).

---

## **3. Common Issues & Fixes**
### **A. Connection Problems**
#### **Symptom**: Clients repeatedly fail to connect to the broker.
**Root Causes**:
1. Broker **not running** (e.g., `systemd` service crashed, Docker container down).
2. **Network firewall** blocking ports (e.g., Kafka `9092`, RabbitMQ `5672`).
3. **Misconfigured client settings** (e.g., wrong hostname/IP, TLS not enabled).

**Fixes**:
```java
// Example: Debugging Kafka connection in Java
Properties props = new Properties();
props.put("bootstrap.servers", "kafka-broker:9092"); // Verify hostname!
props.put("security.protocol", "SASL_SSL");         // Ensure TLS is configured
props.put("sasl.mechanism", "SCRAM-SHA-512");       // Check if broker supports this
props.put("debug", "all");                         // Enable debug logging

try (Producer<String, String> producer = new KafkaProducer<>(props)) {
    producer.send(new ProducerRecord<>("test", "hello"));
} catch (Exception e) {
    LOG.error("Connection failed: " + e.getMessage());
    // Check broker logs, network, credentials
}
```

**Debugging Steps**:
1. **Ping the broker**:
   ```bash
   # For Kafka
   nc -zv kafka-broker 9092

   # For RabbitMQ
   telnet rabbitmq 5672
   ```
2. **Check broker logs**:
   ```bash
   journalctl -u kafka -f  # Systemd-based systems
   docker logs kafka-broker  # Docker
   ```
3. **Verify network rules**:
   ```bash
   # Check firewall (Linux)
   sudo iptables -L

   # Check security groups (AWS/Azure)
   aws ec2 describe-security-groups
   ```

---

#### **Symptom**: **TLS/SSL handshake fails**.
**Fixes**:
- Ensure **certificates** are valid and not expired.
- Match **cipher suites** between client and broker.
  ```java
  // Kafka SSL config example
  props.put("ssl.truststore.location", "/path/to/truststore.jks");
  props.put("ssl.truststore.password", "password");
  props.put("ssl.keystore.location", "/path/to/keystore.jks");
  props.put("ssl.keystore.password", "password");
  props.put("ssl.key.password", "password");
  ```

---

### **B. Message Delivery Issues**
#### **Symptom**: **Messages disappear** (not delivered to consumers).
**Root Causes**:
1. **Consumer not subscribed** to the topic/queue.
2. **Consumer crashed** before processing (e.g., `UncaughtException`).
3. **Broker restart** without persistence (e.g., RabbitMQ `durable=false`).
4. **Client-side buffering** overflow (e.g., Kafka `buffer.memory` too small).

**Fixes**:
```python
# Example: Verify RabbitMQ consumer is bound to a queue
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)
channel.basic_consume(queue='task_queue', on_message_callback=callback, auto_ack=False)
channel.start_consuming()  # Ensure this runs!
```

**Debugging Steps**:
1. **Check broker metrics**:
   ```bash
   # Kafka
   kafka-consumer-groups --bootstrap-server localhost:9092 --describe

   # RabbitMQ (via HTTP API)
   curl http://localhost:15672/api/queues/%2F/task_queue
   ```
2. **Enable consumer logging**:
   ```java
   // Spring Kafka example
   @Bean
   public ConsumerFactory<String, String> consumerFactory() {
       DefaultKafkaConsumerFactory<String, String> factory = new DefaultKafkaConsumerFactory<>(consumerProps);
       factory.setListenerLogEnabled(true); // Logs consumer errors
       return factory;
   }
   ```
3. **Test with a dummy consumer**:
   ```bash
   # Kafka (manual consumer)
   kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning
   ```

---

#### **Symptom**: **Duplicate messages** appearing.
**Root Causes**:
1. **At-least-once delivery** (default in Kafka/RabbitMQ) + **manual ACK**.
2. **Consumer crash before ACK** → message redelivered.
3. **Retry logic** not idempotent (e.g., `INSERT` instead of `UPDATE`).

**Fixes**:
- **Use exactly-once semantics** (Kafka Idempotent Producer):
  ```java
  props.put("enable.idempotence", "true");
  props.put("acks", "all");
  ```
- **Implement deduplication** (e.g., track processed IDs in DB):
  ```python
  # Example: Idempotent consumer in Python
  processed_ids = set()
  def callback(ch, method, properties, body):
      msg_id = properties.headers.get(b'msg_id')
      if msg_id not in processed_ids:
          processed_ids.add(msg_id)
          process_message(body)
      else:
          ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
  ```

---

### **C. Performance Bottlenecks**
#### **Symptom**: **High consumer lag** (e.g., `Kafka consumer lag: 10,000 messages`).
**Root Causes**:
1. **Slow processing** (e.g., DB calls, external API calls).
2. **Small batch size** (e.g., `max.poll.records=1` in Kafka).
3. **Consumer too few** (e.g., only 1 consumer for high-throughput topic).

**Fixes**:
```java
// Optimize Kafka consumer batching
props.put("max.poll.records", "500");  // Increase batch size
props.put("fetch.min.bytes", "1048576"); // Wait for larger batches
props.put("fetch.max.wait.ms", "500");  // Increase poll timeout
```

**Debugging Steps**:
1. **Profile consumer processing**:
   ```bash
   # Use JMH or Spring Boot Actuator for latency metrics
   curl http://localhost:8080/actuator/heapdump
   ```
2. **Scale consumers**:
   ```bash
   # Run multiple Kafka consumers
   kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning --consumer-property group.id=consumer-group-1
   kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning --consumer-property group.id=consumer-group-2
   ```
3. **Monitor broker metrics**:
   ```bash
   # Kafka JMX metrics (via JConsole or Prometheus)
   jconsole localhost:9990
   ```

---

#### **Symptom**: **Broker disk full**.
**Root Causes**:
1. **Unlimited retention** (e.g., Kafka `log.retention.ms=-1`).
2. **Large message size** (e.g., 100MB messages in RabbitMQ).
3. **No DLQ** for failed messages.

**Fixes**:
```bash
# Kafka: Limit retention
ALTER TOPIC test WITH (retention.ms=604800000);  # 7 days

# RabbitMQ: Set message TTL
channel.queue_declare(
    queue='task_queue',
    durable=True,
    arguments={'x-message-ttl': 86400000}  # 24h TTL
)
```

---

### **D. Schema/Serialization Errors**
#### **Symptom**: **`InvalidMessageFormatException`**.
**Root Causes**:
1. **Schema evolution** (e.g., new field in Avro/Protobuf).
2. **Incorrect serializer/deserializer** (e.g., `String` vs `Bytes`).
3. **Corrupted messages** (e.g., network interference).

**Fixes**:
```java
// Example: Handle schema mismatch in Kafka
try {
    AvroDeserializer<String> deserializer = new AvroDeserializer<>();
    deserializer.configure(mapOf("specific.avro.reader", "true"), false);
    String message = deserializer.deserialize("test", bytes);
} catch (SerializationException e) {
    LOG.error("Schema mismatch: " + e.getMessage());
    // Fallback to raw bytes or DLQ
}
```

**Debugging Steps**:
1. **Compare schemas**:
   ```bash
   # Kafka Schema Registry
   curl http://schema-registry:8081/subjects/test-value/versions/latest
   ```
2. **Test serialization locally**:
   ```java
   GenericRecord record = new GenericData.Record(schema);
   record.put("field1", "value1");
   byte[] serialized = serializer.toBytes(record);
   ```

---

### **E. Dead Letter Queue (DLQ) Overload**
#### **Symptom**: **DLQ filling up with unprocessable messages**.
**Root Causes**:
1. **No DLQ configured**.
2. **Error handling bug** (e.g., `Nack` instead of `Reject` with requeue).

**Fixes**:
```python
# RabbitMQ: Configure DLQ
channel.queue_declare(queue='task_queue_dlq', durable=True)
channel.queue_declare(
    queue='task_queue',
    durable=True,
    arguments={
        'x-dead-letter-exchange': '',
        'x-dead-letter-routing-key': 'task_queue_dlq',
        'x-max-length': 1000  # Limit queue size
    }
)
```

**Debugging Steps**:
1. **Check DLQ size**:
   ```bash
   # RabbitMQ HTTP API
   curl http://localhost:15672/api/queues/%2F/task_queue_dlq
   ```
2. **Inspect failed messages**:
   ```bash
   # Dump DLQ messages
   rabbitmqadmin list queues name=task_queue_dlq | jq
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Kafka Tools**        | Topic inspection, consumer lag, producer metrics.                          | `kafka-topics --describe`                    |
| **RabbitMQ Management**| Monitor queues, consumers, message stats.                                   | `http://localhost:15672/#/queues`           |
| **JMX (JConsole/Grafana)** | Broker health, JVM metrics, transaction logs.                          | `jconsole localhost:9990` (Kafka default)   |
| **Prometheus + Grafana** | Long-term monitoring of lag, throughput, errors.                      | `http://grafana:3000/d/kafka-monitoring`    |
| **Log4j2/SLF4J**       | Client-side logging (filter `ERROR`/`WARN`).                              | `<logger name="org.apache.kafka" level="DEBUG"/>` |
| **Postman/curl**       | Test broker APIs (e.g., RabbitMQ HTTP plugin).                            | `curl -u guest:guest http://localhost:15672/api/queues` |
| **Wireshark/tcpdump**  | Network-level inspection (TLS handshakes, packet loss).                   | `tcpdump -i eth0 port 5672`                  |
| **Kafka Debug Producer** | Send test messages to verify delivery.                                    | `kafka-console-producer --topic test`       |
| **Schema Registry CLI** | Compare schemas between producers/consumers.                             | `curl http://schema-registry:8081/subjects` |

---

## **5. Prevention Strategies**
### **A. Design-Time Safeguards**
1. **Idempotent Consumers**
   - Use **transactional outbox** (e.g., Saga pattern) or **deduplication** (e.g., `UUID` + DB tracking).
   - Example: [Spring Kafka Idempotence](https://docs.spring.io/spring-kafka/docs/current/reference/html/#idempotent-producer).

2. **DLQ + Retry with Backoff**
   - Configure **exponential backoff** for retries (e.g., RabbitMQ `x-death` header).
   - Example:
     ```java
     // Kafka: DLQ setup
     props.put("delivery.attempts", "3");
     props.put("retry.backoff.ms", "1000");
     ```

3. **Schema Evolution Control**
   - Use **Schema Registry** (Confluent, Avro) or **versioned APIs**.
   - Example: [Avro Schema Compatibility](https://avro.apache.org/docs/current/spec.html#Compatibility).

4. **Monitoring & Alerts**
   - Set up **SLOs** for:
     - End-to-end latency (P99 < 1s).
     - Consumer lag (Alert if lag > 1000 messages for 5 mins).
     - Error rates (Alert if `ERROR` logs > 1% of messages).
   - Tools: Prometheus + Alertmanager, Datadog.

5. **Backpressure Handling**
   - **Dynamic consumer scaling** (Kubernetes Horizontal Pod Autoscaler for Kafka consumers).
   - **Consumer batching** (increase `max.poll.records` in Kafka).

---

### **B. Runtime Checks**
1. **Health Checks**
   - Broker: `GET /actuator/health` (Spring Boot), `curl http://localhost:15672/api/nodes`.
   - Consumer: Heartbeat monitoring (e.g., Kafka `heartbeat.interval.ms`).

2. **Circuit Breakers**
   - Use **Resilience4j** or **Hystrix** for downstream failures.
   ```java
   @CircuitBreaker(name = "externalService", fallbackMethod = "fallback")
   public void processMessage(String message) {
       // Call external API
   }
   ```

3. **Chaos Engineering**
   - **Kill broker pods** (simulate outage).
   - **Throttle network** (`tc qdisc` on Linux).
   - **Test retries** with `fail2ban`-style message injection.

---

### **C. Operational Best Practices**
1. **Log Everything (But Not All)**
   - Log **error messages**, **consumer lag**, and **schema mismatches**.
   - Example (Logback):
     ```xml
     <configuration>
         <appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
             <appender-ref ref="STDOUT"/>
             <queueSize>1000</queueSize>
         </appender>
         <logger name="org.apache.kafka" level="INFO"/>
     </configuration>
     ```

2. **Use Distributed Tracing**
   - **OpenTelemetry** or **Jaeger** to track message flows.
   ```java
   // Spring Cloud Sleuth + Zipkin example
   @Bean
   public TraceHttpServletRequestInterceptor requestInterceptor() {
       return new TraceHttpServletRequestInterceptor();
   }
   ```

3. **Automated Recovery**
   - **Kafka Consumer Rebalancing**: Ensure `enable.auto.commit=false` + manual ACK.
   - **RabbitMQ**: Use `automatically_delete=false` for durable queues.

4. **Disaster Recovery**
   - **Backup Kafka topics**:
     ```bash
     kafka-dump-log --bootstrap-server localhost:9092 --topic test --files ./backup/
     ```
   - **RabbitMQ snapshots**:
     ```bash
     rabbitmq-diagnostics snapshot /var/lib/rabbitmq/snapshot
     ```

---

## **6. Quick Reference Cheat Sheet**
| **Issue**               | **Quick Fix**                          | **Tools to Check**                  |
|-------------------------|----------------------------------------|-------------------------------------|
| Broker not reachable    | Verify `docker ps`, firewall, logs.    | `nc