# **[Queuing Patterns] Reference Guide**

---
## **Overview**
Queuing patterns provide mechanisms for asynchronous processing, decoupling producers from consumers, and managing workload spikes. These patterns are essential for systems requiring scalability, fault tolerance, and efficient resource utilization. Common use cases include task scheduling, event-driven architectures, batch processing, and handling high-throughput requests with variable arrival rates. By buffering work items in a queue, systems can balance load, reduce bottlenecks, and ensure resilience. This guide covers core queuing patterns, their implementation considerations, and examples for key scenarios.

---

## **Schema Reference**

| **Pattern**               | **Purpose**                                                                 | **Components**                                                                                     | **Key Characteristics**                                                                 | **Best Practices**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Simple Queue**          | Basic FIFO (first-in-first-out) task handling.                              | Producer, Queue, Consumer(s)                                                                         | - Order preserved <br> - No parallelism <br> - Low latency for single consumer <br> - Susceptible to consumer overload | Monitor queue depth to avoid starvation <br> Implement retry logic for failed tasks <br> Limit consumer concurrency |
| **Priority Queue**         | Tasks with urgency ranked for execution.                                   | Producer, Priority Queue, Consumers with priority handling logic                                  | - Tasks prioritized by weight/class <br> - May introduce delay for lower-priority tasks      | Define clear priority rules <br> Monitor starvation of low-priority tasks <br> Use bounded queues |
| **Work Queue**            | Distributes tasks across multiple workers to improve throughput.           | Producer, Queue, Worker Pool (multiple consumers)                                                 | - Parallel processing <br> - Scalable workload distribution <br> - No strict ordering      | Scale workers dynamically <br> Implement circuit breakers <br> Use load balancing for tasks      |
| **Retry Queue**           | Handles transient failures by re-queuing tasks after delays.               | Producer, Queue, Consumer with retry logic, Delay Mechanism                                        | - Automatic retries <br> - Exponential backoff support <br> - Reduces manual intervention | Configure max retry attempts <br> Use Jitter to avoid thundering herd <br> Log retries for analysis |
| **Dead-Letter Queue (DLQ)** | Captures tasks that repeatedly fail for inspection.                         | Producer, Main Queue, DLQ, Consumer + Dead-Letter Handler                                         | - Isolates problematic tasks <br> - Allows manual resolution <br> - Prevents infinite loops      | Set clear failure thresholds <br> Monitor DLQ size <br> Implement alerts for persistent failures |
| **Multicast Queue**        | Broadcasts a task to multiple consumers (e.g., notifications).              | Producer, Queue, Multiple Consumers (subscribers)                                                 | - Parallel processing <br> - Duplication risk <br> - Useful for fan-out patterns             | Use idempotent tasks <br> Implement deduplication <br> Track consumer health                   |
| **Competing Consumers**   | Multiple consumers compete for tasks (e.g., load balancing).               | Producer, Queue, Multiple Consumers with locking/lease mechanisms                                | - Load distribution <br> - No strict ordering <br> - High concurrency possible            | Avoid lock contention <br> Implement timeouts <br> Monitor queue drain speed                  |
| **Broadcast Queue**       | Sends a single task to all subscribers (e.g., event notifications).        | Producer, Queue, Publisher-Subscriber Model                                                      | - Real-time updates <br> - High throughput for events <br> - Potential for duplication     | Use reliable delivery mechanisms <br> Implement acknowledgments <br> Filter irrelevant subscribers |
| **Priority Queue with Expiry** | Combines priority with task expiration (e.g., time-sensitive tasks).     | Producer, Priority Queue with TTL, Expiry Checker                                                 | - Time-bound prioritization <br> - Prevents stale tasks <br> - Ideal for session management   | Configure expiry policies <br> Monitor for expired tasks <br> Alert on premature expirations     |
| **Task Queue with Dependencies** | Manages tasks with precedence constraints (e.g., workflows).           | Producer, Directed Acyclic Graph (DAG) Queue, Task Dependency Tracker                          | - Ordered execution <br> - Handles async dependencies <br> - Complex workflows supported    | Model dependencies clearly <br> Monitor deadlocks <br> Use persistence for recovery           |

---

## **Implementation Details**

### **1. Core Concepts**
- **Producer**: Entity that enqueues tasks (e.g., HTTP requests, event generators).
- **Queue**: Buffered storage for tasks (in-memory, disk, distributed).
- **Consumer**: Entity that dequeues and processes tasks (single or multiple).
- **Persistence**: Ensures tasks survive restarts (e.g., database-backed queues).
- **Scalability**: Horizontal scaling of producers/consumers to handle load.

### **2. Key Considerations**
- **Ordering**: FIFO vs. priority queues. Use strict ordering when required (e.g., financial transactions).
- **Durability**: Persistent storage prevents data loss during failures.
- **Throughput vs. Latency**: High throughput may increase latency (e.g., work queues).
- **Fault Tolerance**: Consumers should handle crashes gracefully (e.g., retry queues).
- **Monitoring**: Track queue depth, processing time, and error rates.

### **3. Technology Stack Options**
| **Component**       | **Options**                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Queue System**    | Apache Kafka, RabbitMQ, Amazon SQS, Azure Service Bus, Redis Streams        |
| **Language SDKs**   | Python (Kafka, SQS), Java (Spring Kafka, RabbitMQ), Go (NATS, Kafka)    |
| **Storage**         | Disk (SQL/NoSQL), Distributed (Kafka topics, Redis)                     |
| **Orchestration**   | Kubernetes (scaling consumers), Serverless (AWS Lambda triggers)         |

---

## **Query Examples**

### **1. Enqueueing Tasks**
```python
# Python (using SQS)
import boto3

sqs = boto3.client('sqs')
response = sqs.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/1234567890/my-queue',
    MessageBody='{"task": "process_invoice", "priority": "high"}'
)
print(response['MessageId'])
```

```java
// Java (using RabbitMQ)
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;

// Enqueue with priority
ConnectionFactory factory = new ConnectionFactory();
Connection connection = factory.newConnection();
Channel channel = connection.createChannel();

channel.queueDeclare("priority_task", true, false, false, null);
channel.basicPublish("", "priority_task",
    new AMQP.BasicProperties.Builder()
        .priority(2)  // High priority
        .build(),
    "Task data".getBytes()
);
```

---

### **2. Consuming Tasks**
```bash
# Consume from Kafka (cli)
kafka-console-consumer --bootstrap-server localhost:9092 \
    --topic task_queue \
    --from-beginning \
    --property print.key=true
```

```typescript
// Node.js (using BullMQ for Redis)
import { Queue } from 'bullmq';

const queue = new Queue('task_queue', { connection: redis });

async function processTask(job: any) {
    console.log(`Processing: ${job.data}`);
    await job.process(1000); // 1s timeout
}

queue.process('default', processTask);
```

---

### **3. Handling Retries (Exponential Backoff)**
```python
# Python (with Retry Queue)
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_task(task):
    try:
        # Attempt to process (may fail)
        result = execute_task(task)
        return result
    except TaskError as e:
        raise e  # Retry automatically
```

```java
// Java (with Dead-Letter Handling)
public class Consumer {
    public void consume(Message message) {
        try {
            // Process task
            execute(message);
        } catch (TaskException e) {
            // Move to DLQ after retries
            dlq.send(message, "task_failed_" + message.getMessageId());
        }
    }
}
```

---

### **4. Monitoring Queue Metrics**
```sql
-- PostgreSQL example (for a custom queue table)
SELECT
    COUNT(*) as total_tasks,
    AVG(processing_time) as avg_processing_time,
    SUM(failed_attempts > 0) as failed_tasks
FROM queue_tasks
WHERE status = 'active';
```

```bash
# Kafka Lag Monitoring
kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group my-consumer-group \
    --describe --match-all
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                                   |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Temporarily stops calls to a failing service to prevent cascading failures.    | When consumers depend on unreliable external systems.                                        |
| **Bulkhead**              | Isolates workloads to limit resource contention.                                 | Preventing one consumer from starving others (e.g., in work queues).                            |
| **Saga**                  | Manages distributed transactions via compensating actions.                     | Complex workflows requiring rollback (e.g., cross-service transactions).                       |
| **Event Sourcing**        | Stores state changes as a sequence of events.                                    | Audit trails, time travel debugging, or event-driven architectures.                            |
| **Rate Limiting**         | Controls request volume to avoid overload.                                       | Protecting APIs or databases from spikes (often paired with queues).                          |
| **Backpressure**          | Signals producers to slow down when consumers are overwhelmed.                 | Dynamic workload adjustment (e.g., Kafka consumer lag detection).                             |
| **Fan-Out/Fan-In**        | Parallelizes processing (fan-out) or merges results (fan-in).                   | High-throughput parallel tasks (e.g., image processing pipelines).                             |
| **Asynchronous API**      | Decouples request/response with callbacks or queues.                            | Long-running tasks (e.g., file processing, ML inference).                                     |

---
## **Anti-Patterns to Avoid**
1. **Single Consumer Bottleneck**: Avoid using a single consumer for high-throughput queues.
2. **Unbounded Queues**: Queues with no size limits can cause memory exhaustion.
3. **No Monitoring**: Lack of metrics leads to blind spots in performance or failures.
4. **Ignored Dead-Letter Queues**: Unchecked DLQs accumulate unresolved issues.
5. **Over-Prioritization**: Favor high-priority tasks indefinitely, starving others.
6. **Tight Coupling**: Consumers should not be tightly coupled to producers (use queues as intermediaries).
7. **No Retry Logic**: Tasks should retry failures with backoff to avoid cascading errors.