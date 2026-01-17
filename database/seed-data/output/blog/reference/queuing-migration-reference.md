# **[Pattern] Queuing Migration Reference Guide**

---

## **Overview**
The **Queuing Migration** pattern is used to **asynchronously process large-scale data migration** with minimal downtime while ensuring fault tolerance, scalability, and eventual consistency. This pattern divides the migration task into smaller batches, processes them via a **message queue** (e.g., RabbitMQ, Kafka, or AWS SQS), and tracks progress through a **control table** or state management mechanism. Ideal for:
- Migrating legacy systems to modern databases.
- Offloading batch jobs from transactional systems.
- Handling high-volume data without blocking operations.

Key benefits:
✔ **Decouples** migration logic from application code.
✔ **Retries failed tasks** automatically (e.g., via dead-letter queues).
✔ **Scalable**—processes can run across multiple workers.
✔ **Resumable**—supports re-entrant processing if interrupted.

---

## **Implementation Details**

### **Key Components**
| Component          | Purpose                                                                 | Example Tools/Technologies                     |
|--------------------|-------------------------------------------------------------------------|------------------------------------------------|
| **Source System**  | Original data repository (legacy DB, file, API).                       | PostgreSQL, Oracle, S3, REST APIs             |
| **Queue**          | Decouples producers (data fetchers) from consumers (migration workers). | RabbitMQ, Kafka, AWS SQS, Azure Service Bus   |
| **Worker Pool**    | Processes queue items in parallel (batch size configurable).            | Python (`celery`), Java (`Spring Batch`), Go   |
| **Sink System**    | Target repository (new DB, storage, or service).                       | MongoDB, Snowflake, DynamoDB                  |
| **Control Table**  | Tracks migration status (processed, failed, retries).                  | PostgreSQL `migration_status` table           |
| **Retry Logic**    | Automates retries for transient failures (timeouts, throttling).       | Exponential backoff, dead-letter queues (DLQ) |
| **Monitoring**     | Logs progress, errors, and performance metrics.                         | Prometheus + Grafana, AWS CloudWatch         |

---

### **Schema Reference**
#### **1. Control Table (`migration_jobs`)**
```sql
CREATE TABLE migration_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,  -- e.g., "users_v1_to_v2"
    source_id VARCHAR(255) NOT NULL, -- Unique identifier in source (e.g., UUID)
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    attempt_count INT DEFAULT 0,
    last_attempt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB             -- Optional: Custom metadata (e.g., batch_size)
);
```

#### **2. Queue Table (if using a DB-backed queue)**
```sql
CREATE TABLE migration_queue (
    id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) REFERENCES migration_jobs(job_name),
    source_id VARCHAR(255) REFERENCES migration_jobs(source_id),
    payload JSONB NOT NULL,       -- Serialized data to migrate (e.g., user record)
    attempted_at TIMESTAMP,
    locked_until TIMESTAMP        -- For distributed locking (e.g., Redis)
);
```

---

### **Query Examples**

#### **1. Initialize Migration Jobs**
Fetch a batch of pending records from the source and enqueue them:
```sql
-- PostgreSQL (using `LATERAL` for batching)
INSERT INTO migration_queue (job_name, source_id, payload)
SELECT
    'users_v1_to_v2' AS job_name,
    u.user_id,
    to_jsonb(u)::jsonb  -- Serialize user record
FROM users_v1 AS u
WHERE u.migrated = FALSE
LIMIT 1000;  -- Batch size
```

#### **2. Lock a Job for Processing (Avoid Duplicates)**
```sql
-- Atomic check + lock (PostgreSQL)
UPDATE migration_queue
SET locked_until = NOW() + INTERVAL '5 minutes',
    attempted_at = NOW()
WHERE id = :job_id
  AND locked_until IS NULL;  -- FailSilently if already locked
```

#### **3. Update Job Status After Processing**
```sql
-- Success
UPDATE migration_jobs
SET status = 'completed', updated_at = NOW()
WHERE id = :job_id;

-- Failure (with retry logic)
UPDATE migration_jobs
SET status = 'failed', attempt_count = attempt_count + 1,
    last_attempt_at = NOW()
WHERE id = :job_id;
```

#### **4. Dead-Letter Queue (DLQ) Ingestion**
Move failed jobs to a DLQ after `max_retries`:
```sql
INSERT INTO migration_dlq (job_id, error_message)
SELECT id, 'Processing failed after 3 attempts'
FROM migration_jobs
WHERE status = 'failed' AND attempt_count >= 3;
```

---

## **Step-by-Step Workflow**
1. **Source → Queue**
   - A **producer** (e.g., a Python script) queries the legacy system and enqueues records as JSON payloads.
   - Example:
     ```python
     # Pseudocode (e.g., using RabbitMQ)
     def produce_records():
         for record in db.query("SELECT * FROM users_v1 WHERE migrated = FALSE LIMIT 1000"):
             queue.publish(json.dumps(record), routing_key="migration_jobs")
     ```

2. **Queue → Workers**
   - **Consumers** (workers) poll the queue, lock jobs, and process them:
     ```python
     # Celery task example
     @celery.task(bind=True)
     def migrate_user(self, payload):
         try:
             user = json.loads(payload)
             db.execute("INSERT INTO users_v2 (...) VALUES (...)", user)
             self.update_status("completed")
         except Exception as e:
             self.update_status("failed")
             raise e
     ```

3. **Sink → Validation**
   - Post-migration, validate data integrity (e.g., checksum comparison).
   - Example:
     ```sql
     SELECT COUNT(*) AS records_migrated
     FROM users_v2
     WHERE checksum = (
         SELECT checksum FROM users_v1
         WHERE migrated = TRUE
     );
     ```

---

## **Error Handling & Resilience**
| Issue               | Solution                                                                 |
|----------------------|--------------------------------------------------------------------------|
| **Duplicate processing** | Use distributed locks (e.g., `locked_until` timestamp + `SELECT FOR UPDATE`). |
| **Worker crashes**    | Queue systems (RabbitMQ/Kafka) support **message persistence** and retries. |
| **Schema drift**     | Validate payloads against a **schema registry** (e.g., JSON Schema).     |
| **Target DB failures**| Implement **circuit breakers** (e.g., Hystrix) or batch retries.          |

**Retry Strategy Example (Exponential Backoff):**
```python
def retry_operation(max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return process_job()  # Actual migration logic
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            sleep_time = 2 ** attempt  # 1s, 2s, 4s, etc.
            time.sleep(sleep_time)
```

---

## **Performance Considerations**
| Factor               | Optimization Strategy                                  |
|----------------------|-------------------------------------------------------|
| **Throughput**       | Scale workers horizontally; tune queue batch size.   |
| **Latency**          | Use **in-memory queues** (e.g., Redis) for low-latency. |
| **Storage**          | Compress payloads (e.g., gzip) if queue grows large.   |
| **Idempotency**      | Design workers to handle **duplicate payloads** safely. |

---

## **Related Patterns**
| Pattern                     | When to Use                                                                 | Example Use Case                          |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **Saga Pattern**            | Long-running transactions across services.                                  | Order fulfillment with 3rd-party payments. |
| **CQRS**                    | Read-heavy migrations with optimized views.                               | Reporting dashboards for legacy data.    |
| **Event Sourcing**          | Audit migration changes as immutable events.                              | Financial compliance logs.                |
| **Batch Processing**        | Large, one-time data loads.                                                | Monthly ETL jobs.                         |
| **Circuit Breaker**         | Protect workers from cascading failures in the target system.             | DB overload during peak migration.       |

---
## **Tools & Libraries**
| Category          | Tools                                                                 |
|-------------------|------------------------------------------------------------------------|
| **Queues**        | RabbitMQ, Apache Kafka, AWS SQS, Azure Service Bus, NATS              |
| **Workers**       | Celery (Python), Spring Batch (Java), AWS Step Functions, Go Channels |
| **Databases**     | PostgreSQL (for control tables), MongoDB (for JSON payloads)          |
| **Monitoring**    | Prometheus + Grafana, Datadog, AWS CloudWatch                        |
| **Schema Validation** | JSON Schema, Avro, Protobuf                                          |

---
## **Troubleshooting**
| Symptom               | Cause                          | Solution                                  |
|-----------------------|--------------------------------|-------------------------------------------|
| Jobs stuck in queue   | Worker crash/overload.         | Scale workers; check DLQ for locked jobs. |
| Data duplication      | No idempotency in workers.     | Add `unique_constraint` to sink table.    |
| Slow migration        | Small batch size.              | Increase batch size (e.g., 10K records).  |
| Target DB timeouts    | Large transactions.            | Use **batch inserts** (e.g., PostgreSQL `COPY`). |

---
**Note:** Replace placeholders (e.g., `users_v1`, `db`) with your system’s actual schema. For production, add **idempotency keys**, **rate limiting**, and **end-to-end encryption** for sensitive data.