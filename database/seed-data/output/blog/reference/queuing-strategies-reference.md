```
**[Pattern] Queuing Strategies Reference Guide**

---
```

---
### **Overview**
The **Queuing Strategies** pattern organizes tasks or requests into queues to manage workload spikes, prioritize operations, and improve system reliability. Queues buffer demand, allowing systems to process items asynchronously while adhering to business policies like fairness, speed, or cost efficiency. Common use cases include:
- Handling user requests (e.g., APIs, webhooks).
- Processing background jobs (e.g., analytics, notifications).
- Managing IoT/device data streams.
- Load balancing distributed systems.

Queuing strategies determine *how* items enter/exit queues (e.g., FIFO, LIFO, priority-based) and *how* the system scales (e.g., parallel workers, retries, dead-letter queues). This guide covers implementation details, schema references, and examples for core strategies.

---

---
### **Key Concepts**
#### **1. Core Components**
| Term               | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Queue**          | A data structure (e.g., list, priority heap) storing unprocessed items.     |
| **Producer**       | Entity that enqueues items (e.g., a client API or microservice).             |
| **Consumer**       | Entity that dequeues and processes items (e.g., a worker thread or service).|
| **Worker Pool**    | Set of consumers processing queue items concurrently.                       |
| **Partitioning**   | Splitting queues into subgroups (e.g., by topic or key) for parallelism.   |
| **Durability**     | Persistent storage (e.g., disk) to survive system restarts.                |
| **Visibility Timeout** | Time an item remains "visible" to consumers before re-enqueuing.          |

#### **2. Common Strategies**
| Strategy               | Description                                                                      | Use Case                                  |
|------------------------|----------------------------------------------------------------------------------|-------------------------------------------|
| **FIFO (First-In, First-Out)** | Items processed in arrival order.                                             | Simple task scheduling (e.g., order processing). |
| **LIFO (Last-In, First-Out)** | Most recent items processed first.                                            | Stack-based reversals (rare).            |
| **Priority Queues**    | Items ordered by priority (e.g., numerical or time-based).                     | Urgent tasks (e.g., OTP codes).          |
| **Round-Robin**        | Items distributed cyclically among consumers.                                  | Balancing load across workers.           |
| **Rate Limiting**      | Controls enqueue/dequeue speed to avoid overload.                              | Throttling API calls.                    |
| **Fairness-Based**     | Guarantees equal distribution (e.g., per-user quotas).                        | Multi-tenant systems.                   |
| **Exponential Backoff**| Retries failed items with increasing delays.                                  | Fault-tolerant polling.                 |
| **Dead-Letter Queue (DLQ)** | Failed items moved to a separate queue for reprocessing.                     | Handling transient errors.               |
| **Work Stealing**      | Idle consumers "steal" tasks from overloaded ones.                            | Dynamic load balancing.                 |

---

---
### **Schema Reference**
Below are schema templates for queue configurations (adapt to your system). Useful for APIs, config files (e.g., JSON/YAML), or ORMs.

#### **1. Queue Definition (Basic)**
```json
{
  "queue": {
    "name": "user_notifications",
    "type": "priority",  // or "fifo", "lifo", etc.
    "durable": true,
    "visibility_timeout": "30s",
    "partition_key": "user_id",  // For partitioning
    "max_length": 10000,
    "ttl": "24h"  // Auto-delete after TTL
  }
}
```
- **`type`**: Strategy (see [Key Concepts](#key-concepts)).
- **`partition_key`**: Field to partition by (e.g., `user_id`).
- **`visibility_timeout`**: Max time an item stays "reserved" by a consumer.

#### **2. Consumer Configuration**
```json
{
  "consumers": [
    {
      "name": "notification_worker_1",
      "worker_pool": "high_priority",
      "prefetch_count": 10,  // Max items fetched at once
      "max_retries": 3,
      "max_backoff_delay": "5m"
    }
  ],
  "worker_pools": {
    "high_priority": {
      "max_workers": 10,
      "strategy": "round_robin"
    }
  }
}
```
- **`prefetch_count`**: Controls concurrency (buffer size).
- **`max_retries`**: Retries before moving to DLQ.
- **`strategy`**: How workers distribute items (e.g., `fairness`).

#### **3. Priority Queue Item Schema**
```json
{
  "priority": 2,  // Higher = higher priority (1 = critical)
  "data": {
    "user_id": "123",
    "message": "Urgent: Your account was locked."
  },
  "metadata": {
    "source": "api_endpoint",
    "timestamp": "2023-10-01T12:00:00Z"
  }
}
```
- **`priority`**: Numeric value (adjust based on business rules).

#### **4. Dead-Letter Queue (DLQ) Item**
```json
{
  "original_queue": "user_notifications",
  "failed_at": "2023-10-01T12:05:00Z",
  "error": "Database connection timeout",
  "item": {  // Original payload
    "priority": 2,
    "data": { ... }
  }
}
```

---

---
### **Query Examples**
Below are example queries for common operations. Adapt syntax to your queue system (e.g., Redis, RabbitMQ, Kafka).

#### **1. Enqueuing Items**
**FIFO Queue (Redis CLI):**
```bash
LPUSH user_notifications "{\"data\":{\"user_id\":\"123\"}}"
```

**Priority Queue (Kafka):**
```bash
echo '{"priority":1,"data":{"user_id":"456"}}' | \
  kafka-console-producer --topic high_priority_notifications --broker-list localhost:9092
```

#### **2. Dequeuing Items**
**Blind Poll (RabbitMQ):**
```bash
rabbitmqadmin get queue=user_notifications consumer=worker_1
```

**Priority Poll (Redis with ZSET):**
```bash
ZRANGE user_notifications 0 0 WITHSCORES  # Gets highest-priority item
```

#### **3. Partitioned Queue (Kafka):**
```bash
# Enqueue to partition by user_id=123
kafka-console-producer --topic user_events --partition 123 ...
```

#### **4. Querying Queue Status**
**Redis:**
```bash
LLANGE user_notifications 0 -1  # List all items
```

**Prometheus Metrics (Example):**
```promql
queue_length{queue="user_notifications"} > 1000  # Alert if queue exceeds size
```

#### **5. Handling Failures (DLQ)**
**Move to DLQ (Pseudocode):**
```python
if process_item(item) fails:
    dlq = DeadLetterQueue("user_notifications_dlq")
    dlq.enqueue(item, error="Timeout")
```

---

---
### **Implementation Considerations**
1. **Performance**:
   - Use **in-memory queues** (e.g., Redis) for low latency.
   - For high throughput, prioritize **partitioned queues** (e.g., Kafka).
2. **Durability**:
   - Persist queues to disk if restarts are likely.
   - Example: RabbitMQ’s `message_ttl` or Kafka’s `retention.ms`.
3. **Monitoring**:
   - Track metrics like:
     - Queue length (`queue_length`).
     - Processing time (`item_processing_duration`).
     - Error rates (`failed_items`).
4. **Scaling**:
   - **Horizontal scaling**: Add more consumers/workers.
   - **Vertical scaling**: Increase worker memory/CPU.
5. **Error Handling**:
   - Implement **exponential backoff** for retries.
   - Use **DLQs** to isolate problematic items.

---

---
### **Code Snippets (Pseudocode)**
#### **Producer (FIFO)**
```python
def enqueue(queue_name: str, item: dict):
    queue = QueueSystem.connect(queue_name)
    queue.enqueue(item)
```

#### **Consumer (Priority)**
```python
def process_high_priority_items():
    while True:
        item = priority_queue.dequeue(highest_priority=True)
        if not item:
            break
        process(item)
```

#### **Worker Pool (Round-Robin)**
```python
class WorkerPool:
    def __init__(self, queue_name: str, num_workers: int):
        self.queue = QueueSystem.connect(queue_name)
        self.workers = [Thread(target=self._worker) for _ in range(num_workers)]

    def _worker(self):
        while True:
            item = self.queue.dequeue()  # Round-robin by default
            self._process(item)
```

---

---
### **Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Command Queue**                | Queues tasks for later execution (similar to background jobs).              | Offloading non-critical work (e.g., analytics).                            |
| **Saga Pattern**                 | Manages distributed transactions via compensating actions.                 | Microservices with ACID requirements.                                      |
| **Rate Limiter**                 | Controls request volume to prevent overload.                               | API gateways or public-facing services.                                    |
| **Circuit Breaker**              | Stops cascading failures by halting calls to faulty services.               | Fault-tolerant architectures.                                             |
| **Bulkhead Pattern**             | Isolates workloads to prevent resource exhaustion.                          | Monolithic services with multiple dependencies.                           |
| **Event Sourcing**               | Stores state changes as immutable events (often paired with queues).      | Auditing or replaying system state.                                        |
| **Retry Policy**                 | Automatically retries failed operations with backoff.                      | Idempotent operations (e.g., HTTP requests).                              |

---
### **Anti-Patterns to Avoid**
1. **Unbounded Queues**: No `max_length` or `ttl` can lead to memory exhaustion.
2. **No Visibility Timeout**: Items "stuck" in processing may be dequeued multiple times.
3. **Ignoring Priority**: Treating all items equally in a high-priority system.
4. **No Monitoring**: Undetected queue bloating or processing bottlenecks.
5. **Over-Partitioning**: Too many partitions increases overhead (e.g., Kafka topics).

---
### **Tools/Libraries**
| Tool/Library       | Type          | Key Features                                  |
|--------------------|---------------|-----------------------------------------------|
| **Redis**          | In-memory     | Pub/Sub, Lists, Sorted Sets (for priorities). |
| **RabbitMQ**       | Message Broker| Queues, Exchanges, DLQs.                      |
| **Kafka**          | Distributed   | High-throughput, partitioned topics.         |
| **AWS SQS**        | Managed       | Serverless, FIFO/SLQ (standard/ordered).     |
| **Celery**         | Task Queue    | Python, supports retries and rate limiting.   |
| **Apache Pulsar**  | Unified       | Combines pub/sub and message queues.          |

---
### **Example Workflow: Urgent Notifications**
1. **Enqueue**:
   - User requests an OTP → Priority Queue (`priority=1`).
   ```json
   { "priority": 1, "data": { "user_id": "123", "message": "OTP: 123456" } }
   ```
2. **Consume**:
   - Worker fetches item (priority-first), sends OTP via SMS.
3. **Error Handling**:
   - If SMS fails, retry 3 times with backoff → move to DLQ.
4. **Monitor**:
   - Alert if queue length > 1000 or processing time > 1s.

---
### **Further Reading**
- **Books**:
  - *Designing Data-Intensive Applications* (Martin Kleppmann) – Chapter 11 (Queueing Systems).
- ** Papers**:
  - ["The Design of the FreeBSD Event Notification System"](https://www.usenix.org/legacy/publications/library/proceedings/fast02/full_papers/braham/fast02_braham.html).
- **Talks**:
  - ["Building Resilient Systems" (Martin Fowler)](https://martinfowler.com/articles/resilient-design.html).