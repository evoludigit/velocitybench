# **Debugging CDC Reconnection Strategy: A Troubleshooting Guide**

## **Introduction**
Change Data Capture (CDC) systems often rely on **reconnection strategies** to maintain persistent subscriptions when network issues, broker failures, or client disconnects occur. If the reconnection logic fails, subscribers may miss events, experience duplicate processing, or enter an unstable state.

This guide provides a structured approach to diagnosing and resolving reconnection-related issues in CDC patterns.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if your system exhibits any of these symptoms:

✅ **Subscriptions dropping indefinitely** – The CDC consumer fails to re-establish a connection after disruptions.
✅ **Missed events or gaps in data** – Some records are not reprocessed after a reconnect.
✅ **Duplicate processing** – Events are replayed multiple times due to improper reconnection handling.
✅ **High latency in subscription recovery** – The consumer takes too long to reconnect and resume processing.
✅ **Error messages related to reconnection delays** – Logs show `Connection Timeout`, `Invalid Offset`, or `Failed to Resubscribe`.
✅ **Resource exhaustion** – The consumer exhausts retries, causing crashes (e.g., `TooManyRequests`).
✅ **Unstable offset tracking** – The consumer fails to correctly track the last processed offset after reconnecting.
✅ **Broker-specific errors** – Kafka, Pulsar, or AWS Kinesis may return connection reset or auth-related failures.

If you see **multiple symptoms**, the issue may be **multi-layered** (e.g., a combination of reconnection logic, offset management, and network stability).

---

## **2. Common Issues & Fixes (With Code)**

### **A. Reconnection Logic Not Respecting Backoff Exponentials**
**Symptom:** The consumer rapidly retries without delay, leading to broker overload.

**Root Cause:**
- Hardcoded retry delays (e.g., fixed `5-second` backoff).
- No exponential backoff with jitter.
- No max retry limit.

**Fix (Kafka Example - Scala/Java):**
```scala
import org.apache.kafka.clients.consumer.ConsumerConfig
import java.util.Properties

val props = new Properties()
props.put(ConsumerConfig.RETRY_BACKOFF_MS_CONFIG, "100") // Initial backoff
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "100") // Prevent memory overload
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false") // Manual commit for safety
props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "latest") // Handle missed events
```
**Best Practice:**
Use **exponential backoff with jitter** (e.g., using a library like `retry` or `backoff-java`).

---

### **B. Offset Tracking Fails After Reconnection**
**Symptom:** The consumer resubscribes but starts from the wrong offset, missing or duplicating data.

**Root Cause:**
- **No offset commit on failure** (e.g., `auto.commit=false` but consumer crashes before committing).
- **Incorrect `auto.offset.reset`** (e.g., `earliest` vs. `latest`).
- **Manual offset tracking logic is buggy** (e.g., not updating on `onPartitionsAssigned`).

**Fix (Kafka - Manual Offset Handling):**
```java
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");

kafkaConsumer.subscribe(topic);
kafkaConsumer.seekToBeginning(partitions); // Reset to earliest if needed

// After processing a batch:
kafkaConsumer.commitSync(); // Atomic commit
```

**Fix (Pulsar - Subscription Redelivery Policy):**
```java
SubscriptionConfig subscriptionConfig = SubscriptionConfig.builder()
    .topic(topic)
    .subscriptionName(subName)
    .redeliveryPolicy(new RedeliveryPolicy(3, // maxRedeliverCount
                                           60, // maxRedeliverInterval
                                           500)) // initialRedeliverInterval
    .build();
```

**Debugging Tip:**
- Log the **current offset** before and after reconnect:
  ```scala
  val currentOffset = kafkaConsumer.position(topicPartition)
  println(s"Last processed offset: $currentOffset")
  ```

---

### **C. Network Issues Preventing Reconnection**
**Symptom:** Broker unreachable, timeouts, or DNS resolution failures.

**Root Cause:**
- **No retry on transient errors** (e.g., `SocketTimeoutException`).
- **Hardcoded broker addresses** (no fallback).
- **No heartbeat monitoring** (Kafka’s `session.timeout.ms`).

**Fix (Kafka - Resilient Consumption):**
```java
props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, "30000") // Longer than retry.backoff.ms
props.put(ConsumerConfig.REQUEST_TIMEOUT_MS_CONFIG, "5000") // Adjust per network stability
props.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, "300000") // Prevent disconnections
```

**Fix (AWS Kinesis - Retry with Exponential Backoff):**
```python
import boto3
from botocore.config import Config

kinesis = boto3.client('kinesis',
    config=Config(
        retries={
            'max_attempts': 5,
            'mode': 'adaptive'  # Exponential backoff
        }
    )
)
```

---

### **D. Race Conditions in Reconnect Logic**
**Symptom:** Duplicate processing due to overlapping subscriptions.

**Root Cause:**
- **No mutex/lock** when reassigning partitions.
- **Race between `onPartitionsAssigned` and `onPartitionsRevoked`**.

**Fix (Kafka - Atomic Partition Handling):**
```java
var isProcessing = false

override fun onPartitionsAssigned(partitions: List<TopicPartition>) {
    if (!isProcessing) {
        isProcessing = true
        kafkaConsumer.seek(partitions.map { it.offset(Offset.beginningOffsets()) })
        // Start processing
    }
}
```

---

### **E. Broker-Specific Reconnection Failures**
| **Broker** | **Issue** | **Fix** |
|------------|-----------|---------|
| **Kafka**  | `OffsetOutOfRangeException` | Use `auto.offset.reset=earliest` temporarily during debugging. |
| **Pulsar** | `SubscriptionAlreadyExists` | Check for duplicate subscription names. |
| **AWS Kinesis** | `ProvisionedThroughputExceeded` | Increase shard capacity or use `On-Demand` mode. |
| **NATS** | `ConnectionRefused` | Verify NATS server is running (`NATS_PORT` mismatch). |

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Observability**
- **Enable debug logs** (Kafka: `DEBUG` for `org.apache.kafka`).
- **Track reconnection attempts** with timestamps:
  ```scala
  logger.info(s"Attempting reconnect #${retryCount} at ${new Date()}")
  ```
- **Use structured logging** (JSON) for easier parsing:
  ```json
  {
    "event": "reconnect_attempt",
    "topic": "orders",
    "retry_count": 3,
    "offset": 1005,
    "error": "TimeoutException"
  }
  ```

### **B. Metrics & Monitoring**
- **Expose reconnection metrics** (Prometheus/Grafana):
  ```java
  Counter reconnectionAttempts = Metrics.counter("cdc_reconnect_attempts_total");
  reconnectionAttempts.inc();
  ```
- **Monitor `poll()` latency** (Kafka):
  ```scala
  val startTime = System.currentTimeMillis()
  val records = kafkaConsumer.poll(Duration.ofMillis(1000))
  val latency = System.currentTimeMillis() - startTime
  metrics.record("poll_latency_ms", latency)
  ```
- **Watch for `Rebalance` events** (Kafka):
  ```scala
  override fun onPartitionsRevoked(partitions: List<TopicPartition>) {
    logger.warn("Rebalance detected, awaiting new assignments")
  }
  ```

### **C. Testing Strategies**
| **Scenario** | **Test Method** | **Tool** |
|--------------|----------------|----------|
| **Network Failures** | Simulate timeouts | `Vagrant` + `iptables` |
| **Broker Restarts** | Graceful shutdown | `docker stop kafka` |
| **Offset Tracking** | Manually corrupt offset commit | `kafka-consumer-groups` |
| **Concurrent Reconnects** | Load test with multiple consumers | `Locust` |

**Example (Kafka Unit Test):**
```java
@Test
public void testReconnectOnOffsetError() throws Exception {
    // Mock KafkaConsumer to throw OffsetOutOfRangeException
    when(kafkaConsumer.position(any())).thenThrow(new OffsetOutOfRangeException());

    // Expect retry behavior
    assertTrue(consumerHandler.attemptedReconnect());
}
```

---

## **4. Prevention Strategies**

### **A. Design Principles**
✔ **Idempotent Processing** – Ensure reprocessing the same event is safe.
✔ **Atomic Commits** – Never commit offsets until processing succeeds.
✔ **Dead Letter Queue (DLQ)** – Route failed records for later inspection.
✔ **Graceful Degradation** – Fall back to manual processing if auto-reconnect fails.

### **B. Best Practices**
- **Use a circuit breaker** (e.g., Resilience4j) to prevent cascading failures.
- **Implement health checks** for the CDC consumer.
- **Monitor SLA violations** (e.g., max allowed delay between reconnects).
- **Automate recovery** (e.g., Kubernetes `LivenessProbe` for CDC pods).

### **C. Configuration Hardening**
| **Setting** | **Recommended Value** | **Purpose** |
|-------------|----------------------|-------------|
| `retry.backoff.ms` (Kafka) | `1000, 2000, 4000` | Exponential backoff |
| `max.poll.interval.ms` | `300000` | Prevent disconnections |
| `session.timeout.ms` | `60000` | Detect stale connections |
| `heartbeat.interval.ms` | `10000` | Keep alive broker connections |

---

## **5. Final Checklist for Resolving Issues**
1. **Verify logs** for `reconnect_attempt` or `offset` errors.
2. **Check broker health** (e.g., Kafka `kafka-topics.sh`).
3. **Test connectivity** (ping, telnet, or `nc` to broker port).
4. **Monitor metrics** (latency, retry counts, partition assignments).
5. **Audit offset commits** (are they atomic?).
6. **Simulate failures** (kill consumer, check recovery).
7. **Apply fixes incrementally** (one change at a time).

---

## **Conclusion**
CDC reconnection issues often stem from **misconfigured backoff, broken offset tracking, or unstable networking**. By following this guide—**logging issues, testing reconnection logic, and hardening configurations**—you can diagnose and resolve problems efficiently.

**Key Takeaways:**
✅ **Use exponential backoff with jitter.**
✅ **Commit offsets only after successful processing.**
✅ **Monitor reconnections via metrics and logs.**
✅ **Test failure scenarios in staging.**

If the problem persists, **narrow it down** (network vs. application logic) and **consult broker-specific docs** (Kafka, Pulsar, etc.).