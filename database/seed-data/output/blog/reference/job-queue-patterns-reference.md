# **[Pattern] Job Queue Patterns (Celery & Bull) Reference Guide**

## **Overview**
Job Queue Patterns (Celery & Bull) enable asynchronous, scalable background task execution, decoupling time-consuming operations (e.g., email sending, data processing) from primary application logic. These patterns use message queues to offload tasks, ensuring responsiveness, reliability, and horizontal scalability. **Celery** (Python) relies on **Redis/RabbitMQ** for queue management, while **Bull** (Node.js) uses **Redis** by default, both leveraging worker pools for parallel processing. This guide covers implementation best practices, schema design, query patterns, and integrations.

---

## **1. Key Concepts**

| **Term**               | **Definition**                                                                 | **Example Use Case**                     |
|------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **Consumer**           | Application listening for and processing queue messages.                      | A Node.js app processing order tasks.    |
| **Producer**           | Application adding jobs to the queue.                                       | User submitting a file upload request.  |
| **Queue**              | FIFO/Priority list of pending tasks (e.g., `default`, `high_priority`).       | Redis/RabbitMQ-backed queue.             |
| **Worker**             | Process executing tasks pulled from the queue.                               | Celery workers or Bull worker processes. |
| **Retry Mechanism**    | Automatic re-attempts for failed jobs (exponential backoff, max retries).    | Transient database connection issues.   |
| **Rate Limiting**      | Controlled job dispatch to prevent queue overload.                           | Throttling spammy API calls.             |
| **Result Backend**     | Storage for job results (Redis, database).                                  | Celery `result_backend=redis://`.        |
| **Priority Queue**     | Jobs processed based on priority (e.g., `CRITICAL > HIGH > NORMAL`).         | Urgent notifications vs. analytics.     |
| **Delayed Tasks**      | Jobs scheduled for future execution (e.g., 1-hour delay).                     | Scheduled reports.                       |
| **Chain/Graph**        | Sequential or parallel job dependencies (Celery) or task grouping (Bull).    | "Upload → Process → Notify" workflow.    |

---

## **2. Schema Reference**

### **Celery Schema (Redis/RabbitMQ)**
| **Component**       | **Schema/Config**                                                                 | **Notes**                                  |
|---------------------|----------------------------------------------------------------------------------|--------------------------------------------|
| **Queue**           | `CELERY_BROKER_URL = "redis://localhost:6379/0"`                                | Supports RabbitMQ (`amqp://`).             |
| **Result Backend**  | `CELERY_RESULT_BACKEND = "redis://localhost:6379/1"`                           | Stores task results.                      |
| **Task Definition** | `@shared_task(bind=True)`                                                        | Decorator for async functions.             |
| **Retry Policy**    | `retries=3, max_retries=5, countdown=60`                                        | Exponential backoff via `expires` in Redis.|
| **Priority Queue**  | `queue="high_priority", routing_key="high"`                                    | Uses `x-priority` in Redis.               |
| **Delayed Task**    | `apply_async(countdown=3600)`                                                    | Scheduled via `delay()` or `schedule()`.   |
| **Chain**           | `task1.s() | task2.s()` or `call_chain()`                                                   | Sequential execution.                     |
| **Worker Setup**    | `celery -A proj worker --loglevel=INFO --concurrency=4`                         | Adjust concurrency for CPU/IO tasks.      |

---

### **Bull Schema (Redis)**
| **Component**       | **Schema/Config**                                                                 | **Notes**                                  |
|---------------------|----------------------------------------------------------------------------------|--------------------------------------------|
| **Queue**           | `const queue = new Queue(1, 'default', { redis: { host: '127.0.0.1' } })`     | `1` = Priority level.                     |
| **Job Creation**    | `await queue.add('processFile', { id: '123' }, { priority: 2 })`                | Priority: `1` (high) to `999` (low).       |
| **Retry Policy**    | `queue.on('failed', (job, err) => { if (job.attemptsMade < 3) job.retry(); })` | Built-in retry mechanism.                 |
| **Delayed Task**    | `await queue.add('notify', { user: 'alice' }, { delay: 30000 })`                 | Milliseconds delay.                        |
| **Parallel Jobs**   | `Promise.all([queue.add('task1'), queue.add('task2')])`                         | Batch processing.                          |
| **Worker**          | `queue.process({ concurrency: 2 })`                                               | Adjust for CPU/IO-bound tasks.             |
| **Rate Limiting**   | `queue.setMaxWaiting(1000)`                                                       | Limit queue size.                          |
| **Cleanup**         | `await queue.clean(0, 1000, 'failed')`                                           | Remove stale jobs.                         |

---

## **3. Query Examples**

### **Celery (Python)**
```python
# Add a task to the queue
from proj.tasks import process_data
process_data.delay(data)

# Delayed task (executes in 5 sec)
process_data.apply_async(countdown=5)

# Priority queue
process_data.apply_async(queue='high_priority', routing_key='urgent')

# Chain tasks
upload_task = upload_file.delay(file)
processing_task = process_file.s(upload_task.get())
```

### **Bull (Node.js)**
```javascript
// Add a job to the queue
const queue = new Queue(1, 'default', { redis });
await queue.add('resizeImage', { url: 'image.jpg' }, { priority: 2 });

// Delayed job (2 hours)
await queue.add('sendEmail', { to: 'user@example.com' }, { delay: 7200000 });

// Parallel jobs
await Promise.all([
  queue.add('task1'),
  queue.add('task2', {}, { priority: 1 }) // Higher priority
]);

// Process jobs
queue.process(async (job) => {
  await job.updateProgress(0.5); // Progress tracking
  const result = await someAsyncTask(job.data);
  await job.updateProgress(1);
});
```

---

## **4. Best Practices**

### **Performance Optimization**
- **Worker Concurrency**:
  - **CPU-bound tasks**: Set `concurrency=N_CPUS` (e.g., `4` for a 4-core machine).
  - **IO-bound tasks** (e.g., DB/API calls): Use higher concurrency (e.g., `10–50`).
- **Queue Partitioning**: Split queues by task type (e.g., `email`, `image_processing`).
- **Batching**: Process multiple small jobs in a single worker iteration (e.g., `queue.process(10)`).

### **Reliability**
- **Retry Logic**:
  - **Exponential backoff**: Increase delay between retries (e.g., `1s → 2s → 4s`).
  - **Max retries**: Avoid infinite loops (`max_retries=5`).
- **Dead Letter Queue (DLQ)**: Configure a separate queue for failed jobs:
  ```python
  # Celery
  task = upload_file.delay(file, queue='dlq', routing_key='failed_uploads')
  ```
  ```javascript
  // Bull
  queue.add('task', {}, { attempts: 3, backoff: { type: 'exponential', delay: 1000 } });
  ```

### **Monitoring & Observability**
- **Metrics**: Use tools like:
  - **Celery**: `celery flower` (web dashboard) or Prometheus exporters.
  - **Bull**: Built-in Redis metrics or `bull-board`.
- **Logging**: Log task start/end, errors, and durations:
  ```python
  @shared_task(bind=True)
  def process_data(self, data):
      logger.info(f"Task {self.request.id} started")
      try:
          result = heavy_computation(data)
          logger.info(f"Task {self.request.id} completed")
          return result
      except Exception as e:
          logger.error(f"Task {self.request.id} failed: {e}")
          raise
  ```
- **Alerts**: Set up alerts for:
  - High queue lengths.
  - Failed jobs exceeding retry limits.

### **Scaling**
- **Horizontal Workers**: Add more workers to handle load (Celery: `celery -A proj worker --pool=gevent`).
- **Queue Sharding**: Distribute queues across Redis instances for high throughput.
- **Cloud Integration**: Use serverless (e.g., AWS Lambda) for sporadic workloads.

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Integration**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Event Sourcing]**      | Store state changes as events for auditability and replayability.             | Celery/Bull can publish events post-task. |
| **[CQRS]**                | Separate read/write models (e.g., write via queues, read via cached views).   | Bull queues for write paths.            |
| **[Saga Pattern]**        | Manage distributed transactions via compensating actions.                   | Celery chains for workflows.            |
| **[Rate Limiting]**       | Throttle API requests to prevent abuse.                                      | Bull’s `setRateLimit()` or Redis `rate`. |
| **[Circuit Breaker]**     | Fail fast if downstream services degrade.                                   | Celery `on_failure` handlers.           |
| **[Asynchronous API]**    | Return `202 Accepted` immediately; notify via webhooks.                       | Celery tasks + webhook callers.         |

---

## **6. Troubleshooting**
| **Issue**                  | **Root Cause**                          | **Solution**                              |
|----------------------------|----------------------------------------|------------------------------------------|
| **Jobs stuck in queue**    | Worker crashes or low `concurrency`.    | Check logs; scale workers.               |
| **High latency**           | Slow tasks or blocked Redis.           | Optimize code; monitor Redis perf (`INFO stats`). |
| **Memory leaks**           | Unclosed connections in workers.       | Use connection pools (e.g., `aioredis`).  |
| **Priority not respected** | Wrong queue routing key.               | Verify `queue` and `routing_key` in task. |
| **Failed jobs**            | Retry logic misconfigured.             | Check `attemptsMade`; enable DLQ.         |

---
## **7. Migration Guide**
### **From Celery to Bull**
1. **Replace Broker**:
   - Replace RabbitMQ/Redis Celery config with Bull’s Redis setup.
2. **Task Definition**:
   - Convert `@shared_task` decorators to Bull `queue.add()`.
3. **Priority/Dependencies**:
   - Use Bull’s `priority` field instead of Celery’s `routing_key`.
4. **Result Backend**:
   - Replace Celery’s `result_backend` with Bull’s Redis storage (no direct equivalent).

### **From Bull to Celery**
1. **Broker Flexibility**:
   - Migrate Redis to RabbitMQ for better clustering.
2. **Task Chaining**:
   - Replace Bull’s parallel `Promise.all` with Celery chains (`task1.s() | task2.s()`).
3. **Priority Queues**:
   - Use Celery’s `queue` and `routing_key` for multi-priority queues.

---
## **8. Tools & Libraries**
| **Tool**               | **Purpose**                                      | **Link**                                  |
|------------------------|--------------------------------------------------|------------------------------------------|
| **Celery**             | Python async task queue.                        | [celery.readthedocs.io](https://docs.celeryq.dev/) |
| **Bull**               | Node.js Redis-based queue.                      | [github.com/Automattic/bull](https://github.com/Automattic/bull) |
| **Redis**              | In-memory data store for queues/results.        | [redis.io](https://redis.io/)             |
| **RabbitMQ**           | Message broker for Celery (alternative to Redis).| [rabbitmq.com](https://www.rabbitmq.com/) |
| **Flower**             | Celery monitoring dashboard.                     | [flower.readthedocs.io](https://flower.readthedocs.io/) |
| **Bull-Board**         | Bull web UI for monitoring.                     | [github.com/hunterhacker/bull-board](https://github.com/hunterhacker/bull-board) |

---
## **9. Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│   Client    │───▶│  API Gateway│───▶│    Redis       │
└─────────────┘    └─────────────┘    ├─┬───────────────┘
                               │    │
                               ▼    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│  Celery/Bull│    │  Worker Pool│    │   Database     │
│  Queue      │◀────┤ (Scalable) │◀───┤ (Results/Logs) │
└─────────────┘    └─────────────┘    └─────────────────┘
```
- **Client**: Submits tasks via API.
- **Redis**: Stores queues, priorities, and results.
- **Workers**: Process tasks in parallel; scale horizontally.
- **Database**: Optional for persistent results/logs.