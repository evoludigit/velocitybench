# **Debugging Event-Driven Architecture (EDA): A Troubleshooting Guide**

---

## **1. Symptom Checklist**

Before diving into debugging, confirm which symptoms align with your issue:

| **Symptom**                     | **Description**                                                                 | **Key Question**                          |
|----------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Missing Events**               | Events are not being emitted or consumed.                                      | Are events being published?              |
| **Delayed/Stuck Events**         | Events are queued but not processed (e.g., stuck in a DLQ or slow consumer).  | Are consumers falling behind?            |
| **Duplicate Events**             | Same event processed multiple times (causing duplicate DB writes, etc.).       | Is idempotency in place?                 |
| **Event Ordering Issues**        | Events arrive out of sequence, breaking state synchronization.                | Is strict ordering required?             |
| **Consumer Overload**            | Consumers are overwhelmed (high latency, timeouts, or crashes).                | Is auto-scaling in effect?               |
| **Cascading Failures**           | A downstream service failure propagates through event chains.                   | Are retries or circuit breakers configured? |
| **Schema Mismatch**              | Event payloads change but consumers aren’t updated.                             | Are backward-compatible changes enforced? |
| **Permission Errors**            | Services lack access to event topics/queues.                                   | Are IAM/ACL policies correct?            |
| **Dead Letter Queue (DLQ) Spam** | Too many failed events flood the DLQ, obscuring real issues.                  | Is DLQ processing enabled?               |

---

## **2. Common Issues and Fixes**

### **A. Events Not Being Emitted**
**Symptom:** Publishers report success, but consumers never receive events.

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                                                                 | **Code Fix** |
|-------------------------------------|------------------------------------------------------------------------------------|--------------|
| **Broker/Queue Misconfiguration**   | Verify topic/queue names, permissions, and retention policies.                     | Example (Kafka): `producer.send(event_topic, event_value)` with correct `TopicPartitions`. |
| **Producer Errors**                 | Check connection timeouts, serialization issues, or broker unavailability.         | Validate `producer.send()` returns `RecordMetadata`. |
| **Schema Evolution**                | Event schema changed but consumers aren’t updated.                                  | Use **Avro/Protobuf** with backward-compatible changes. |
| **Network/Firewall Blocking**      | Outbound traffic from publisher is blocked.                                        | Check security groups/NACLs. Use `telnet <broker>:9092` to test. |

**Debugging Command (Kafka):**
```bash
# Check producer logs for errors
kubectl logs -f <pod-name> | grep "send"

# Verify topic existence
kafka-topics.sh --bootstrap-server <broker>:9092 --list
```

---

### **B. Consumers Falling Behind (Stuck Events)**
**Symptom:** Lag between broker and consumer grows indefinitely.

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                                                                 | **Code Fix** |
|-------------------------------------|------------------------------------------------------------------------------------|--------------|
| **Slow Processing**                 | Business logic is too slow (e.g., DB calls, external APIs).                          | Profile consumer with `tracing` (e.g., OpenTelemetry). |
| **Throttling**                      | Auto-scaling isn’t kicking in (e.g., Kubernetes HPA not enabled).                  | Set `minReplicas: 3` and `targetCPU: 70%`. |
| **Consumer Group Stuck**            | Offsets not committed due to crashes or `auto.commit` misconfiguration.              | Manually commit offsets in `doConsume()`: `consumer.commitSync()`. |
| **Schema Incompatibility**          | Consumer expects a different schema than the producer.                              | Validate schema registry (e.g., Confluent Schema Registry). |

**Debugging Command (Kafka):**
```bash
# Check consumer lag
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 --describe --group <group-id>

# Monitor offset commits
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 --groups --describe
```

**Optimized Consumer (Java - Spring Kafka):**
```java
@KafkaListener(topics = "event_topic", groupId = "consumer-group")
public void handleEvent(@Payload EventDto event, @Header(KafkaHeaders.OFFSET) Long offset) {
    try {
        // Process event
        service.process(event);
        // Explicit commit (if using manual_offset_store)
        offsetStore.sync(offset);
    } catch (Exception e) {
        // DLQ logic here
        dlqProducer.send("dlq_topic", event);
    }
}
```

---

### **C. Duplicate Events**
**Symptom:** Same event processed multiple times (e.g., duplicate DB writes).

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                                                                 | **Fix** |
|-------------------------------------|------------------------------------------------------------------------------------|---------|
| **Producer Retries**                | Idempotent producer (`enable.idempotence=true` in Kafka).                           | Enable idempotent writes. |
| **Consumer Rebalances**              | New consumers join group, reprocessing lagged partitions.                            | Use `spring.kafka.listener.poll-timeout=30000` to minimize rebalances. |
| **Manual Offset Commits**           | Consumer crashes before committing offset.                                           | Use `spring.kafka.listener.ack-mode=RECORD` (for manual commits). |
| **DLQ Reprocessing**                | Dead-lettered events are reprocessed.                                               | Implement **schema evolution** checks. |

**Idempotent Handler (Python - Confluent Kafka):**
```python
from confluent_kafka import Consumer, KafkaException

def handle_event(event):
    try:
        # Check if event already processed (e.g., DB lookup)
        if not db.check_processed(event.id):
            db.process(event)
    except KafkaException as e:
        # Handle DLQ
        dlq_producer.produce("dlq_topic", value=e)
```

---

### **D. Event Ordering Issues**
**Symptom:** Events arrive out of sequence (e.g., `order_created` after `payment_processed`).

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                                                                 | **Fix** |
|-------------------------------------|------------------------------------------------------------------------------------|---------|
| **Partitioning by Key**             | Events with same key go to same partition but arrive in order.                     | Use `key=order_id` when publishing. |
| **Multiple Consumers**              | Different workers process events asynchronously.                                   | Use a **single-consumer group** if strict ordering is needed. |
| **Retry Logic**                     | Retries arrive out of order if not correlated.                                      | Add `retry_id` to event payload. |

**Ordered Processing (Spring Kafka):**
```java
@KafkaListener(
    topics = "order_events",
    groupId = "orders-group",
    containerFactory = "orderedKafkaListenerContainerFactory"
)
public void handleOrder(@Payload OrderEvent event) {
    // Process in order
}
```

**Container Config (Java):**
```java
@Bean
public ConcurrentKafkaListenerContainerFactory<String, Object> orderedKafkaListenerContainerFactory() {
    ConcurrentKafkaListenerContainerFactory<String, Object> factory =
        new ConcurrentKafkaListenerContainerFactory<>();
    factory.setConsumerFactory(consumerFactory);
    factory.setConcurrency(1); // Single consumer for ordering
    return factory;
}
```

---

### **E. Cascading Failures**
**Symptom:** One service failure knocks out dependent services.

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                                                                 | **Fix** |
|-------------------------------------|------------------------------------------------------------------------------------|---------|
| **No Retries**                      | Consumer crashes silently without retry logic.                                       | Enable `max.poll.records=5` + exponential backoff. |
| **Circuit Breaker Missing**         | Downstream calls block indefinitely.                                                | Use **Resilience4j** or **Hystrix**. |
| **DLQ Overload**                    | Dead-letter queue fills up, starving new events.                                    | Set `retention.ms=604800000` (7 days) + alerting. |

**Resilience4j Retry (Java):**
```java
@Retry(name = "eventRetry", maxAttempts = 3)
public void processEvent(Event event) {
    downstreamService.handle(event);
}
```

**Circuit Breaker (Kotlin Coroutines):**
```kotlin
val circuitBreaker = CircuitBreaker(
    failureThreshold = 50,
    slowCallDurationThreshold = 2000
)

suspend fun safeProcessEvent(event: Event) {
    circuitBreaker.execute {
        downstreamClient.process(event)
    }
}
```

---

## **3. Debugging Tools and Techniques**

### **A. Logging & Observability**
| **Tool**               | **Use Case**                                                                       | **Example Command** |
|-------------------------|------------------------------------------------------------------------------------|---------------------|
| **Kafka Logs**          | Check producer/consumer logs for errors.                                          | `kubectl logs <pod>` |
| **Prometheus + Grafana** | Monitor broker/consumer metrics (lag, throughput).                                | `kafka_consumer_lag` metric |
| **OpenTelemetry**       | Trace event flow across services.                                                  | `otel-javaagent` |
| **DLQ Inspection**      | Debug stuck events.                                                                | `kafka-console-consumer --bootstrap-server <broker> --topic dlq_topic` |

**Key Metrics to Watch:**
- `kafka.consumer.lag` (Kafka)
- `event_processing_latency` (custom)
- `consumer_record_retry_count` (retry loops)

---

### **B. Schema Validation**
- **Confluent Schema Registry**: Enforce backward-compatibility.
  ```bash
  curl -X GET http://schema-registry:8081/subjects/event-topic-value/versions/latest
  ```
- **Avro/Protobuf Tools**: Validate schema changes.
  ```bash
  # Check compatibility
  avro schema-compatibility-check old.avsc new.avsc
  ```

---

### **C. Event Replay Testing**
Simulate failures with:
```bash
# Slow down producer (10x latency)
kafka-producer-perf-test --topic test --num-records 1000 --record-size 1000 --throughput -10 --producer-props acks=all,compression.type=lz4

# Inject delays in consumer
kubectl set env deployment/consumer DELAY_MS=5000 --overwrite
```

---

## **4. Prevention Strategies**

### **A. Design-Time Mitigations**
1. **Idempotency**: Design events to be replay-safe (e.g., `id` field + DB checks).
2. **Schema Management**:
   - Use **Avro/Protobuf** with backward-compatible changes.
   - Tag breaking changes with `event_version`.
3. **Circuit Breakers**: Isolate downstream failures (Resilience4j).
4. **Dead Letter Queues (DLQ)**:
   - Configure retention policies (e.g., 7 days).
   - Alert on DLQ growth (`kafka_consumer_lag > 1000`).

### **B. Runtime Safeguards**
1. **Rate Limiting**:
   - Use **Kafka `fetch.max.bytes`** or **Spring Kafka `maxPollRecords`**.
2. **Auto-Scaling**:
   - Enable HPA for consumers:
     ```yaml
     resources:
       limits:
         cpu: "2"
         memory: "2Gi"
     autoscaling:
       targetCPUUtilizationPercentage: 80
     ```
3. **Monitoring Alerts**:
   - Prometheus alert for `kafka_consumer_lag > 500`.
   - SLOs for `p99.event_processing_latency < 500ms`.

### **C. Testing Strategies**
1. **Chaos Engineering**:
   - Kill Kafka brokers randomly (`kubectl delete -f kafka-statefulset`).
   - Test consumer recovery.
2. **Event Replay**:
   - Capture events during staging, replay on prod with delays.
3. **Contract Testing**:
   - Use **Pact** to verify event schemas between services.

---

## **5. Quick Reference Cheat Sheet**

| **Issue**               | **Immediate Fix**                          | **Long-Term Fix**                |
|--------------------------|--------------------------------------------|----------------------------------|
| Events not published     | Check `producer.send()` logs.              | Validate broker connectivity.    |
| Consumer lag             | Scale up consumers.                        | Optimize `doConsume()` logic.    |
| Duplicates               | Enable idempotence.                        | Add `processed_at` timestamp.    |
| Ordering issues          | Single-consumer group.                     | Use `key` partitioning.          |
| Cascading failures       | Add circuit breakers.                     | Implement DLQ + retries.         |
| Schema drift             | Use Schema Registry.                       | Enforce backward-compatibility.   |

---

## **6. When to Escalate**
- **DLQ fills up in <1 hour** → Broker misconfiguration.
- **Consumer crashes repeatedly** → Memory leaks (check `OOMKilled` logs).
- **Schema breaks production** → Rollback immediately; freeze schema changes.

---
**Final Tip:** Start with **logs → metrics → traces** in that order. For Kafka-specific issues, `kafka-consumer-groups.sh` and `kafka-lag.sh` are your best friends.