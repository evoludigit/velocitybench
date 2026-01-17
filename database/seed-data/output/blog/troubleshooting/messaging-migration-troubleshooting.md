# **Debugging Messaging Migration: A Troubleshooting Guide**

## **Introduction**
Messaging Migration involves transitioning from one messaging system (e.g., Kafka → RabbitMQ, RabbitMQ → AWS SQS) while ensuring zero downtime, minimal disruption, and data consistency. Failures often arise from misconfigurations, network issues, or improper message handling.

This guide focuses on **practical debugging**—identifying root causes quickly and applying fixes efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm which symptoms are present:

| **Symptom**                          | **Possible Cause**                          |
|---------------------------------------|---------------------------------------------|
| Messages **disappearing** from queues | Consumers not properly acknowledging receipt |
| Messages **duplicated** or **lost**   | At-least-once delivery misconfiguration     |
| **High latency** in message processing | Consumer lag, slow processing, or throttling |
| **Connection drops** between brokers  | Network issues, firewall restrictions       |
| **Schema incompatibility** errors     | New system expects different message format |
| **Backpressure** (queues filling up)  | Consumers slower than producers            |
| **Timeouts** in message delivery      | Broker misconfiguration (TTL, retries)      |
| **Consumer crashes** during migration | New system unable to deserialize old format |

---

## **2. Common Issues & Fixes**

### **2.1 Messages Disappearing from Queues**
**Symptoms:**
- Logs show messages missing after migration.
- Consumers report no new messages despite producers sending.

**Root Cause:**
- Consumers did not **acknowledge (ACK) receipt** properly.
- Messages were **not committed** to a transactional system.

**Debugging Steps:**
1. **Check consumer logs** for `ACK` failures:
   ```bash
   # For RabbitMQ/Pulsar
   grep "NACK" /var/log/consumer.log

   # For Kafka
   kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>
   ```
2. **Verify ACK strategy** in consumer code:
   ```python
   # Wrong: ACKs only if no exception
   @on_message
   def on_message(message):
       try:
           process(message)
       except:  # Only ACKs on success
           pass  # No NACK → message lost!

   # Correct: Explicit ACK after processing
   @on_message
   def on_message(message):
       try:
           process(message)
           message.ack()  # Always ACK after success
       except Exception as e:
           message.nack(requeue=False)  # NACK and drop if fail
   ```
3. **Enable dead-letter queues (DLQ)** to isolate lost messages:
   ```yaml
   # Example for RabbitMQ (consumer.conf)
   consumer_settings:
     dead_letter_exchange: dlx
     dead_letter_routing_key: dlq
   ```

---

### **2.2 Duplicate or Lost Messages**
**Symptoms:**
- Some messages appear **twice** or **never arrive**.
- Audit logs show inconsistent counts.

**Root Cause:**
- **At-least-once** delivery without **idempotency**.
- **Retries** due to transient failures.

**Debugging Steps:**
1. **Check broker retry policies**:
   ```bash
   # Kafka
   kafka-configs --bootstrap-server <broker> --entity-type topics --describe --entity-name <topic> | grep "retries"
   ```
2. **Implement idempotent consumers** (dedupe by message ID or payload hash):
   ```python
   seen_messages = set()
   @on_message
   def on_message(message):
       msg_id = message.properties.get("message_id")
       if msg_id not in seen_messages:
           seen_messages.add(msg_id)
           process(message)
   ```
3. **Use exactly-once processing** (if supported):
   - Kafka: `enable.idempotence=true` + `transactional` sends.
   - RabbitMQ: Use `transaction` mode + `basic.ack` only after full processing.

---

### **2.3 High Latency in Message Processing**
**Symptoms:**
- Consumers fall behind producers.
- `kafka-consumer-groups` shows lag > 0.

**Root Cause:**
- Slow processing logic.
- Too few consumer instances.
- Network bottlenecks.

**Debugging Steps:**
1. **Monitor consumer lag**:
   ```bash
   # Kafka
   kafka-consumer-groups --bootstrap-server <broker> --describe --group <group> --topic <topic>
   ```
2. **Scale consumers horizontally** (add more workers).
3. **Optimize processing time** (parallelize work where possible).
4. **Enable compression** (if using Kafka/RabbitMQ):
   ```yaml
   # Kafka producer config
   compression.type: snappy
   ```

---

### **2.4 Connection Drops Between Brokers**
**Symptoms:**
- Brokers **disconnect** intermittently.
- `ZooKeeper(Kafka) / Erlang supervision` logs show failures.

**Root Cause:**
- **Network flapping** (MTU issues, VPN problems).
- **Broker misconfiguration** (insecure connections, timeouts).

**Debugging Steps:**
1. **Check network stability**:
   ```bash
   ping <broker_ip>
   mtr <broker_ip>  # For deeper analysis
   ```
2. **Enable broker logging**:
   ```bash
   # Kafka: Increase log level
   kafka-server-start.sh --override config/log4j.properties \
     --log4j.logger.kafka.authorizer=DEBUG ...
   ```
3. **Fix TLS/cert issues** (if using secure connections):
   ```bash
   openssl s_client -connect <broker>:9093 | openssl x509 -noout -text
   ```

---

### **2.5 Schema Incompatibility Errors**
**Symptoms:**
- New system rejects messages due to **schema mismatch**.
- Errors like `Avro/Protobuf validation failed`.

**Root Cause:**
- **Backward/forward incompatibility** in Avro schemas.
- **New fields** added without backward compatibility.

**Debugging Steps:**
1. **Compare old vs. new schemas**:
   ```bash
   # Avro schema diff
   avro-tools diff schema.old.avsc schema.new.avsc
   ```
2. **Use schema registry** (Confluent Schema Registry) for versioning:
   ```bash
   # Check schema compatibility
   curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
     --data '{"schema": "...", "id": 123}' \
     http://schema-registry:8081/subjects/my-topic-value/versions
   ```
3. **Graceful migration strategy**:
   - **Read old format** → **Transform** → **Write new format**.

---

### **2.6 Backpressure (Queues Filling Up)**
**Symptoms:**
- Broker memory pressure (`kafka-consumer-groups --describe` shows `error`).
- Disk usage spikes (for Kafka logs).

**Root Cause:**
- **Consumers too slow** for producer rate.
- **No flow control** in broker.

**Debugging Steps:**
1. **Increase consumer parallelism** (add more partitions/groups).
2. **Enable broker backpressure** (RabbitMQ: `prefetch_count`):
   ```python
   connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
   channel = connection.channel()
   channel.basic_qos(prefetch_count=100)  # Limit in-flight messages
   ```
3. **Monitor disk usage** (Kafka: `kafka-log-dirs-usage.sh`).

---

### **2.7 Timeouts in Message Delivery**
**Symptoms:**
- Messages **expire** before processing.
- Logs show `timeout` errors.

**Root Cause:**
- **TTL misconfigured**.
- **Network delays** > timeout threshold.

**Debugging Steps:**
1. **Check TTL settings**:
   ```bash
   # Kafka
   kafka-topics --describe --topic <topic> --bootstrap-server <broker>
   ```
2. **Adjust TTL** (e.g., increase from 1h → 24h):
   ```bash
   kafka-configs --alter --entity-type topics --entity-name <topic> \
     --add-config retention.ms=86400000
   ```
3. **Monitor network latency** (`ping`, `traceroute`).

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                          |
|------------------------|-----------------------------------------------|----------------------------------------------|
| **Kafka Consumer Groups** | Check lag, offset commits                     | `kafka-consumer-groups --describe`          |
| **RabbitMQ Management UI** | Monitor queues, consumers, connections      | `http://<broker>:15672`                     |
| **Prometheus + Grafana** | Broker metrics (latency, errors, throughput) | `kafka_server_persistent_request_handler_queue_time_avg` |
| **JMX Exporter**       | Monitor Kafka/RabbitMQ JMX metrics            | `jconsole` + `jmxtrans`                     |
| **Log Aggregation (ELK)** | Correlate logs across brokers/consumers      | `kibana`                                     |
| **`strace`/`tcpdump`** | Network-level debugging (e.g., TLS handshake) | `strace -e trace=network kafka-consumer`     |
| **Schema Registry CLI** | Validate Avro/Protobuf schemas               | `curl http://schema-registry:8081/subjects` |

**Key Metrics to Watch:**
- **Producer:** `MessageSendRate`, `RequestLatency`
- **Consumer:** `RecordConsumptionRate`, `CommittedOffsetLag`
- **Broker:** `UnderReplicatedPartitions`, `NetworkProcessorAvgIdlePercent`

---

## **4. Prevention Strategies**
### **4.1 Pre-Migration Checklist**
✅ **Test in staging** with realistic load.
✅ **Validate schema compatibility** (Avro/Protobuf).
✅ **Enable monitoring** (Prometheus + Alertmanager).
✅ **Back up old system** before cutting over.
✅ **Document rollback plan** (e.g., switch back to old broker).

### **4.2 Post-Migration Best Practices**
🔹 **Use dual-write** (send to old + new system during transition).
🔹 **Implement circuit breakers** for failed consumers.
🔹 **Rate-limit producers** to avoid overwhelming new system.
🔹 **Enable DLQs** to isolate bad messages.
🔹 **Gradual rollout** (canary testing for new consumers).

### **4.3 Automated Recovery**
- **Kafka:** Use `kafka-reassign-partitions.sh` for failed brokers.
- **RabbitMQ:** Restart `rabbitmq-server` and check `rabbitmqctl status`.
- **General:** Implement **self-healing consumers** (retries, dead-letter queues).

---

## **5. Rollback Plan (If Things Go Wrong)**
1. **Switch back to old system** (if dual-write was implemented).
2. **Disable new consumers** (set `auto.offset.reset=earliest` in Kafka).
3. **Monitor for drift** (compare message counts between systems).
4. **Reprocess lost messages** from DLQs.

---
## **Final Checklist Before Production**
| **Action**                          | **Status** |
|-------------------------------------|-----------|
| ✅ Schema compatibility tested      |           |
| ✅ Broker connectivity verified     |           |
| ✅ Consumer lag monitored           |           |
| ✅ Rollback plan documented         |           |
| ✅ Alerts configured for failures   |           |
| ✅ Dual-write enabled (if partial cutover) | |

---
### **Key Takeaways**
- **Always ACK messages explicitly** (don’t rely on exceptions).
- **Use idempotent processing** to avoid duplicates.
- **Monitor lag, errors, and network** proactively.
- **Test rollback** before going live.

By following this guide, you should **minimize downtime** and **resolve issues quickly** during messaging migrations. 🚀