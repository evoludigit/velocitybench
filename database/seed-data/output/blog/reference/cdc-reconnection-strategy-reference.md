# **[Pattern] CDC Reconnection Strategy Reference Guide**

---

## **Overview**
This reference guide documents the **Change Data Capture (CDC) Reconnection Strategy** pattern—a structured approach to managing failed or interrupted subscriptions to CDC streams (e.g., Debezium, Kafka Connect, or AWS DMS). It ensures resilient event processing by automating reconnection logic, minimizing data loss, and maintaining processing continuity.

Key use cases include:
- **Streaming pipelines** (e.g., Kafka, AWS Kinesis) where transient failures occur.
- **Event-driven architectures** requiring atomic processing guarantees.
- **Hybrid systems** combining CDC with downstream sinks (databases, APIs, data warehouses).

The pattern balances **reliability** (redundant checks, backoff strategies) with **performance** (minimal latency, efficient retry loops).

---

## **1. Key Concepts**
| Term               | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Subscription**   | A long-lived connection to a CDC stream (topic/stream/table).             |
| **Offset**         | Position in the CDC log (e.g., Kafka offset, Debezium log position).       |
| **Backoff**        | Exponential delay between reconnection attempts to avoid thundering herds. |
| **Consumer Lag**   | Time/record delay between CDC producer and consumer.                        |
| **Checkpointing**  | Periodically saving consumer offset to resume from last-known position.    |

---

## **2. Schema Reference**
The reconnection strategy relies on two core components: **subscription state** and **retry logic**. Below are essential schemas.

### **2.1 Subscription State Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "subscriptionId": { "type": "string", "description": "Unique ID for the subscription (e.g., Kafka topic + group ID)." },
    "streamType": {
      "type": "string",
      "enum": ["KAFKA", "DEBEZIUM", "AWS_DMS", "OTHER"],
      "description": "Type of CDC source."
    },
    "currentOffset": { "type": "string", "description": "Last committed offset (e.g., Kafka's `topic:partition:offset`)." },
    "lastError": {
      "type": "object",
      "properties": {
        "timestamp": { "type": "string", "format": "date-time" },
        "message": { "type": "string" },
        "errorCode": { "type": "string" }
      }
    },
    "connectionStatus": {
      "type": "string",
      "enum": ["ACTIVE", "RECONNECTING", "FAILED", "TERMINATED"],
      "default": "ACTIVE"
    },
    "checkpointIntervalMs": { "type": "integer", "description": "Interval (ms) for saving offsets." },
    "maxRetries": { "type": "integer", "default": 5, "description": "Max reconnection attempts." }
  },
  "required": ["subscriptionId", "streamType", "currentOffset", "connectionStatus"]
}
```

### **2.2 Backoff Strategy Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "maxDelayMs": { "type": "integer", "default": 300000, "description": "Max backoff delay (5 minutes)." },
    "baseDelayMs": { "type": "integer", "default": 1000, "description": "Initial delay (1 second)." },
    "backoffFactor": { "type": "number", "default": 2, "description": "Exponential factor (e.g., 2 = 1s, 2s, 4s...)." },
    "jitterFactor": { "type": "number", "default": 0.1, "description": "Randomness to avoid synchronized retries." }
  },
  "required": []
}
```

---

## **3. Implementation Patterns**
### **3.1 Core Flow**
1. **Monitor Subscriptions**: Continuously check `connectionStatus` for `FAILED` or `RECONNECTING`.
2. **Exponential Backoff**: For failed subscriptions, wait `(baseDelay * backoffFactor^attempt) * jitter`.
3. **Reconnect Logic**:
   - Re-establish connection to CDC source.
   - **Resync** if offset is stale (e.g., using `DEBEZIUM`’s `server_timestamp` or `KafkaConsumer.seek()`).
   - **Checkpoint** new offset after successful reconnect.
4. **Terminate on Persistent Failures**:
   - If `maxRetries` exceeded or error is critical (e.g., `UNAVAILABLE`), transition to `TERMINATED`.

### **3.2 Resynchronization Strategies**
| Scenario                          | Action                                                                 |
|-----------------------------------|------------------------------------------------------------------------|
| **Offset Stale (>10min lag)**     | Re-fetch snapshot from CDC source (e.g., Debezium’s `binlog_position`). |
| **Topic/Stream Deleted**          | Transition to `TERMINATED`; notify operator.                          |
| **Temporary Outage**              | Resume from last checkpointed offset.                                 |
| **Schema Evolution**              | Validate compatibility; fall back to last working offset.             |

---

## **4. Query Examples**
### **4.1 Check Subscription Status**
```sql
-- SQL-like pseudocode for monitoring
SELECT
  subscriptionId,
  streamType,
  connectionStatus,
  lastError.timestamp,
  (current_time - lastError.timestamp) AS uptime_since_error
FROM subscriptions
WHERE connectionStatus != 'ACTIVE'
ORDER BY lastError.timestamp DESC;
```

### **4.2 Calculate Backoff Delay**
```bash
# Script to compute delay (Python)
import time
import random

def calculate_delay(attempt, config):
    delay = config["baseDelayMs"] * (config["backoffFactor"] ** (attempt - 1))
    delay *= (1 + random.uniform(-config["jitterFactor"], config["jitterFactor"]))
    return min(delay, config["maxDelayMs"])

print(calculate_delay(3, {"baseDelayMs": 1000, "backoffFactor": 2, "jitterFactor": 0.1}))
# Output: ~7.2s (approx.)
```

### **4.3 Resync Offset (Kafka Example)**
```java
// Java snippet to seek to last checkpointed offset
Properties props = new Properties();
props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
props.put(ConsumerConfig.GROUP_ID_CONFIG, "my-group");
props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");
props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Collections.singletonList("my-topic"));
consumer.seek(new TopicPartition("my-topic", 0), new OffsetAndMetadata(lastCheckpointedOffset));
```

---

## **5. Configuration Parameters**
| Parameter                     | Default       | Description                                                                 |
|-------------------------------|---------------|-----------------------------------------------------------------------------|
| `maxRetries`                  | `5`           | Max reconnection attempts before termination.                             |
| `checkpointIntervalMs`        | `5000`        | Frequency (ms) to save offsets.                                             |
| `maxConsumerLagMs`            | `300000`      | Lag threshold (ms) before resyncing.                                       |
| `enableJitter`                | `true`        | Add randomness to backoff delays.                                           |
| `retryOnCriticalErrorsOnly`   | `false`       | Only retry for recoverable errors (e.g., `CONNECTION_CLOSED`).              |

---

## **6. Related Patterns**
| Pattern Name                  | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| **Exactly-Once Processing**   | Ensures CDC events are processed once, even across reconnects.              |
| **Dead Letter Queue (DLQ)**   | Routes failed events to a queue for manual review/replay.                    |
| **Idempotent Sinks**          | Design sinks (e.g., databases) to handle duplicate events safely.          |
| **Metrics-Driven Alerts**     | Monitor `consumer_lag` and `reconnect_attempts` to trigger alerts.         |
| **Snapshot-Based Recovery**   | Periodically take CDC snapshots for full recovery in case of catastrophic failures. |

---

## **7. Troubleshooting**
### **7.1 Common Issues & Fixes**
| Issue                          | Cause                          | Solution                                                                 |
|--------------------------------|--------------------------------|--------------------------------------------------------------------------|
| **Infinite Loop on Reconnect** | Backoff max delay too low.      | Increase `maxDelayMs` or adjust `backoffFactor`.                          |
| **Duplicate Events**           | Offset not checkpointed.       | Enable checkpointing with `enable.auto.commit=false`.                    |
| **Offset Out of Range**        | CDC source compacted offsets.  | Reconfigure consumer to handle `OffsetOutOfRangeException`.              |
| **Operator Overload**          | Too many reconnection attempts.| Cap `maxRetries` or implement circuit breaker.                           |

### **7.2 Logging Recommendations**
```json
{
  "event": "RECONNECT_ATTEMPT",
  "subscriptionId": "sub-123",
  "attempt": 3,
  "delayMs": 4000,
  "error": "CONNECTION_REFUSED",
  "checkpointOffset": "topic:100"
}
```

---
## **8. Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│             │    │             │    │                 │
│   CDC       ├─▶▶│ Reconnection│───▶│ Event Processor │
│   Source     │    │  Controller │    │ (e.g., Flink)  │
│ (Debezium)   │    │             │    │                 │
└─────────────┘    └───────────┬────┘    └───────────────┘
                                      │
                                      ▼
                            ┌─────────────────┐
                            │  Checkpoint DB  │
                            │ (PostgreSQL)   │
                            └───────────────┘
```

---
**Note**: Adjust parameters based on latency/throughput requirements. For high-volume streams, reduce `checkpointIntervalMs`; for reliability, increase `maxRetries`.