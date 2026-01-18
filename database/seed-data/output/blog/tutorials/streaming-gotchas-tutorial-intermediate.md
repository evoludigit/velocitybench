```markdown
# **Streaming Gotchas: The Hidden Pitfalls of Real-Time Data Processing**

*How to avoid common mistakes when working with streams in backend systems—with practical examples and frank tradeoffs.*

---

## **Introduction: Why Streaming "Works" Isn’t Enough**

Real-time data processing is everywhere. From live analytics dashboards to notification systems, event logs, and even chat applications, streaming architectures enable your systems to react to events *as they happen*—not just in batches hours later.

But streaming isn’t just about "pushing data fast." It’s about managing **continuity**, **order**, **resource limits**, and **failures** in a way that batch processing never does. The moment you start relying on streams, you’re stepping into a world where:

- A single misconfigured consumer can **flood your system** with backlogged messages.
- A network blip can **lose critical events**, requiring complex recovery strategies.
- Your "simple" message queue becomes a **bottleneck** if you don’t account for exactly-once delivery.
- **Resource leaks** (like unclosed connections) can clog your infrastructure.

This is where **Streaming Gotchas** come into play. This isn’t about the *theory* of streaming (though we’ll touch on it). It’s about the **practical mistakes** that trip up even experienced engineers—and how to catch them before they become production fires.

---

## **The Problem: Why Streaming "Works" Isn’t Enough**

Let’s start with a **common scenario**: a microservice processing orders in real time. You set up a Kafka topic, a consumer group, and a handler that updates a database when new orders arrive. Sounds simple, right? Here’s how it *can* go wrong:

### **1. Order Guarantees Collapse Under Pressure**
If your consumer can’t keep up, messages start piling up. After the backlog grows, you might **lose events** because:
- Your consumer crashes and restarts, reprocessing old messages *again*.
- The order of messages breaks, leading to **inconsistent state** (e.g., a user getting duplicate order confirmations).
- **At-least-once delivery** becomes a nightmare when your downstream systems can’t handle retries gracefully.

#### Real-world Example:
Imagine a payment service that processes order events. If a payment fails and the event is enqueued again, your system *might* try to charge a customer twice—something you almost certainly don’t want.

### **2. Resources Leak Like Water**
In long-running streaming applications, **memory and connection leaks** are inevitable. For example:
- A consumer leaves open database connections after processing a batch.
- A webhook handler forgets to close a HTTP request body, causing a slow buildup of sockets.
- A background worker spins up too many threads, starving your system of CPU.

#### Real-world Example:
A chat application using WebSockets where each message allows a new connection. If a single user gets flooded with messages (or a bug prevents `onClose()` from firing), you could end up with **thousands of idle connections** overwhelming your server.

### **3. Backpressure Falls Through the Cracks**
When your system can’t handle incoming data fast enough, **backpressure** (slowing down production) becomes essential. But:
- No rate-limiting means consumers **starve producers**.
- No parallelism tuning means some messages **linger forever** in the queue.
- No circuit breakers mean your system **locks up** under load.

#### Real-world Example:
A logistics tracker where GPS updates from vehicles flood your system. Without backpressure, your consumers could spend **hours processing stale data** instead of reacting to the latest updates.

### **4. Fault Tolerance Isn’t Just About Retries**
Retries alone **aren’t enough**. What happens if:
- A consumer fails *between* successful commits to a database and acknowledgment to the broker?
- Your checkpointing system (e.g., Kafka’s `commit()`) is inconsistent?
- A network partition splits your cluster, leaving **orphaned offsets**?

#### Real-world Example:
A distributed ledger where transactions need to be **idempotent** (same input = same output). If a transaction is retried but the state wasn’t properly synced, you could end up with **duplicate balances**.

---

## **The Solution: Streaming Gotchas (And How to Avoid Them)**

The good news? These problems aren’t unsolvable. The key is **proactive design**—anticipating failure modes and embedding safeguards into your code. Here’s a breakdown of the core components you need:

| **Gotcha**               | **Solution Pattern**                     | **Tradeoff**                          |
|--------------------------|------------------------------------------|---------------------------------------|
| Event loss               | Idempotent processing + checkpoints      | Adds complexity to handling duplicates |
| Resource leaks           | Context managers + timeouts             | Slightly slower resource acquisition  |
| Backpressure             | Dynamic scaling + rate limiting          | Requires monitoring and tuning        |
| Fault tolerance          | Dead-letter queues + retries with backoff | Increased operational overhead       |
| Ordering issues          | Exactly-once semantics + transactional outbox | Harder to implement in distributed systems |

---

## **Code Examples: Streaming Gotchas in Action**

Let’s dive into practical examples across different languages and frameworks.

---

### **1. Handling Idempotent Processing (Kafka + Python)**
**Problem:** How do you avoid reprocessing the same event after a crash?

**Solution:** Use an **idempotency key** (e.g., a UUID or message version) and a database lookup to track processed events.

```python
from kafka import KafkaConsumer, KafkaProducer
from typing import Optional
import json
from psycopg2 import connect

# Database to track processed events
def has_processed(event_id: str) -> bool:
    with connect("dbname=streaming_gotchas") as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM processed_events WHERE event_id = %s LIMIT 1;",
                (event_id,)
            )
            return cursor.fetchone() is not None

# Process an order event
def process_order(event: dict) -> None:
    event_id = event["id"]
    if has_processed(event_id):
        print(f"Skipping duplicate event {event_id}")
        return

    # Business logic here...
    print(f"Processing order {event_id}...")
    with connect("dbname=streaming_gotchas") as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO processed_events (event_id) VALUES (%s)",
                (event_id,)
            )

# Consumer setup
consumer = KafkaConsumer(
    "orders",
    bootstrap_servers=["kafka:9092"],
    auto_offset_reset="earliest",
    enable_auto_commit=False
)

for message in consumer:
    event = json.loads(message.value)
    process_order(event)
    consumer.commit()  # Only commit after successful processing
```

**Key Takeaways:**
- Always **check for idempotency** before processing.
- **Commit offsets only after** business logic succeeds.
- Use a **transactional outbox** (like Debezium) for even stronger guarantees.

---

### **2. Preventing Resource Leaks (Go + gRPC)**
**Problem:** Unclosed connections flood memory.

**Solution:** Use **context managers** (`defer`, `context.WithTimeout`) to ensure cleanup.

```go
package main

import (
	"context"
	"fmt"
	"google.golang.org/grpc"
	"net"
)

type MessageHandler struct {
	conn *grpc.ClientConn
}

func (h *MessageHandler) HandleMessage(ctx context.Context, msg string) {
	// Ensure connection is closed on panic or after processing
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Recovered from panic:", r)
		}
		h.conn.Close() // Always close the connection
	}()

	// Simulate work
	fmt.Printf("Processing: %s\n", msg)

	// Use context to enforce timeouts
	timeoutCtx, cancel := context.WithTimeout(ctx, 3000*time.Millisecond)
	defer cancel()

	// Example: Call another service
	_, err := h.conn.NewStream(timeoutCtx, "/example.Service/Method")
	if err != nil {
		fmt.Println("RPC failed:", err)
	}
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		panic(err)
	}
	conn, err := grpc.Dial("localhost:50052", grpc.WithInsecure())
	if err != nil {
		panic(err)
	}

	handler := &MessageHandler{conn: conn}
	// ... handle messages
}
```

**Key Takeaways:**
- **Always defer cleanup** (connections, files, locks).
- **Use context** for timeouts and cancellation.
- **Test edge cases** (crashes, timeouts).

---

### **3. Managing Backpressure (Java + Apache Kafka)**
**Problem:** Consumers can’t keep up, causing a queue explosion.

**Solution:** Dynamically adjust parallelism and use **consumer groups** to distribute load.

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.Collections;

public class BackpressureAwareConsumer {
    private final KafkaConsumer<String, String> consumer;
    private final int maxParallelism;

    public BackpressureAwareConsumer(String topic, String groupId, int maxParallelism) {
        this.maxParallelism = maxParallelism;
        this.consumer = new KafkaConsumer<>(getConfig(topic, groupId));
    }

    private Map<String, Object> getConfig(String topic, String groupId) {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false"); // Manual commits
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, maxParallelism); // Control batch size
        return props;
    }

    public void consume() {
        consumer.subscribe(Collections.singletonList("orders"));

        while (true) {
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));

            if (records.isEmpty()) {
                // Simulate dynamic scaling: adjust parallelism based on lag
                int currentLag = getCurrentLag();
                if (currentLag > 1000) {
                    maxParallelism = Math.min(maxParallelism * 2, 16); // Double up to 16
                } else if (currentLag < 100) {
                    maxParallelism = Math.max(maxParallelism / 2, 1); // Halve down to 1
                }
                System.out.printf("Adjusted parallelism to %d (lag: %d)%n", maxParallelism, currentLag);
            } else {
                processRecords(records);
            }
        }
    }

    private int getCurrentLag() {
        // Implementation depends on your Kafka setup (e.g., JMX)
        return 0; // Placeholder
    }

    private void processRecords(ConsumerRecords<String, String> records) {
        try {
            for (Record<String, String> record : records) {
                processRecord(record);
            }
            consumer.commitSync(); // Commit all processed offsets
        } catch (Exception e) {
            // Handle error (e.g., dead-letter queue)
            e.printStackTrace();
            consumer.commitSync();
            throw e;
        }
    }

    private void processRecord(Record<String, String> record) {
        System.out.printf("Processing: %s - %s%n", record.key(), record.value());
    }

    public static void main(String[] args) {
        BackpressureAwareConsumer consumer = new BackpressureAwareConsumer("orders", "group1", 4);
        consumer.consume();
    }
}
```

**Key Takeaways:**
- **Monitor lag** and dynamically adjust parallelism.
- **Batch processing** reduces overhead but can hide backpressure.
- **Use circuit breakers** (e.g., Hystrix) to avoid cascading failures.

---

### **4. Dead-Letter Queues (DLQ) for Fault Tolerance**
**Problem:** Malformed or unprocessable messages get stuck.

**Solution:** Route them to a **dead-letter topic** for later inspection.

```python
from kafka import KafkaProducer, KafkaConsumer
from json import loads

# Producer with DLQ routing
producer = KafkaProducer(bootstrap_servers=["kafka:9092"])

def send_to_stream(topic: str, message: str, dlq_topic: str = "orders-dlq") -> None:
    try:
        producer.send(topic, value=message.encode("utf-8")).get(timeout=10)
    except Exception as e:
        print(f"Failed to send to {topic}: {e}")
        producer.send(dlq_topic, value=message.encode("utf-8")).get(timeout=10)

# Consumer with DLQ handling
consumer = KafkaConsumer(
    "orders",
    bootstrap_servers=["kafka:9092"],
    auto_offset_reset="earliest",
    enable_auto_commit=False
)

for message in consumer:
    try:
        data = loads(message.value)
        if not is_valid(data):
            raise ValueError("Invalid payload")
        process_order(data)
        consumer.commit()
    except Exception as e:
        print(f"Failed to process {message.value}: {e}")
        # Send to DLQ with error details
        send_to_stream("orders-dlq", message.value, error_message=str(e))
```

**Key Takeaways:**
- **Always handle errors**—don’t silently ignore them.
- **Augment DLQ messages** with error context for debugging.
- **Monitor DLQ size** to avoid it becoming a new bottleneck.

---

## **Implementation Guide: How to Stream Safely**

### **Step 1: Choose Your Streaming Backbone**
| Framework       | Best For                          | Gotchas to Watch For                     |
|-----------------|-----------------------------------|------------------------------------------|
| **Kafka**       | High-throughput, event streaming  | Partitioning, consumer lag, serialization |
| **Pulsar**      | Multi-tenancy, tiered storage      | Schema evolution, tiering costs          |
| **RabbitMQ**    | Simple pub/sub, RPC                | No native exactly-once semantics         |
| **AWS Kinesis** | Serverless streaming               | Cost at scale, vendor lock-in            |

**Recommendation:** Start with **Kafka** for most use cases due to its maturity and feature set.

### **Step 2: Design for Idempotency**
- Use **UUIDs or message versions** as idempotency keys.
- Store processed events in a **database or RocksDB** for fast lookups.
- Example schema:
  ```sql
  CREATE TABLE processed_events (
      event_id VARCHAR(36) PRIMARY KEY,
      processed_at TIMESTAMP DEFAULT NOW()
  );
  ```

### **Step 3: Enforce Backpressure**
- **Limit batch size** (e.g., `max.poll.records` in Kafka).
- **Dynamic scaling**: Adjust worker count based on lag (e.g., with Prometheus + Alertmanager).
- **Rate limiting**: Use tools like **Redis rate limiters** or **Envoy** for API consumers.

### **Step 4: Handle Failures Gracefully**
- **Dead-letter queues**: Route failed messages for inspection.
- **Exponential backoff**: Retry policies should avoid thundering herds.
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
  def retryable_task():
      try:
          # Your logic here
      except Exception as e:
          raise  # Retry will handle it
  ```
- **Circuit breakers**: Use **Hystrix** or **Resilience4j** to stop retries after repeated failures.

### **Step 5: Monitor and Alert**
- **Metrics to track**:
  - **Consumer lag** (`kafka-consumer-groups --describe`)
  - **Message latency** (P99, P95, P50)
  - **Error rates** (DLQ size, retries)
- **Alerts**:
  - Lag > 10% of total messages
  - DLQ growing uncontrollably
  - Consumer crashes

**Tools:**
- **Prometheus + Grafana** for metrics.
- **Datadog/Sentry** for logging and error tracking.

---

## **Common Mistakes to Avoid**

### **1. Ignoring Exactly-One Semantics**
**Mistake:** Assuming "at-least-once" is enough.
**Fix:** Use **transactional outbox patterns** (e.g., Kafka + Debezium) or **sagas** to ensure idempotency.

### **2. Not Testing Failure Scenarios**
**Mistake:** Writing integration tests only for happy paths.
**Fix:** Simulate:
- Network partitions (split-brain testing).
- Consumer crashes.
- Malformed messages.

### **3. Overlooking Resource Limits**
**Mistake:** Assuming "more workers = better throughput."
**Fix:**
- Set **memory limits** (e.g., `--max-heap` in Java).
- Use **process-based isolation** (e.g., Docker containers).
- Monitor **GC pauses** (for JVM-based systems).

### **4. Assuming Order = Partition Order**
**Mistake:** Treating Kafka partitions as FIFO queues without considering key distribution.
**Fix:**
- Use **partition keys** intentionally (e.g., `user_id` for user-specific events).
- If strict ordering is needed, **process messages in a single partition**.

### **5. Forgetting About Timeouts**
**Mistake:** No timeouts on RPC calls or database queries.
**Fix:**
- Use **context timeouts** (e.g., `context.WithTimeout` in Go).
- Set **JDBC connection timeouts**.
- **Gracefully degrade** on timeouts (e.g., return cached data).

---

## **Key Takeaways**
Here’s a quick checklist for streaming-safe code:

✅ **Idempotency:**
- Use unique keys for events.
- Store processed events to avoid duplicates.

✅ **Resource Management:**
- Close connections, files, and sockets **immediately**.
- Use **context managers** (`defer`, `try-finally`).

