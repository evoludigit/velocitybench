# **[Pattern] Durability Tuning - Reference Guide**

## **Overview**
Durability tuning ensures that data persistence is optimized for reliability, consistency, and recovery resilience in distributed systems, databases, or event-driven architectures. This guide covers strategies to balance performance with data durability, including retries, idempotency, checkpointing, and replication configurations. Durability tuning is critical for fault-tolerant applications where data loss must be minimized, such as financial systems, IoT telemetry, or critical infrastructure logs.

---

## **Key Concepts**
### **1. Durability Defined**
Durability ensures that once data is written to storage, it remains intact even after system failures (e.g., crashes, network disconnections, or node outages). Durability is often quantified by **Paxos consensus algorithms** (e.g., Kafka’s ISR window) or **replication factors**.

### **2. Trade-offs**
| **Aspect**       | **High Durability**                          | **Low Durability**                          |
|------------------|---------------------------------------------|---------------------------------------------|
| **Performance**  | Slower writes (acks=all, checkpointing)     | Faster writes (acks=1, eventual consistency) |
| **Recovery**     | Slower fault recovery                       | Faster recovery                             |
| **Cost**         | Higher storage/replication overhead         | Lower overhead                              |
| **Use Case**     | Financial transactions, medical records     | Non-critical logs, analytics pipelines       |

### **3. Core Mechanisms**
| **Mechanism**          | **Description**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **Acks (Acknowledgment Levels)** | Controls how many replicas confirm a write before success (e.g., `acks=1`, `acks=all`).          |
| **Checkpointing**       | Periodically saving state to disk to avoid losing uncommitted writes.                                |
| **Replication**         | Duplicating data across nodes (e.g., Kafka’s ISR, PostgreSQL’s WAL).                              |
| **Idempotency**         | Ensuring retries don’t duplicate side effects (e.g., using keys in HTTP requests).                 |
| **Write-Ahead Log (WAL)** | Writing transactions to disk before applying them to ensure persistence.                           |
| **Backpressure**        | Slowing down producers when durability bottlenecks are detected (e.g., Kafka’s `request.timeout.ms`). |

---

## **Schema Reference**
Below are common configurations for durability tuning across systems:

| **Component**       | **Property**               | **Type**   | **Description**                                                                                                                                                     | **Example Values**                     |
|---------------------|----------------------------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| **Kafka Producer**  | `acks`                     | Integer    | Number of brokers acknowledging a write. `0` = fire-and-forget, `1` = leader acknowledgment, `all` = full commit.                                                     | `acks=1`, `acks=all`                   |
|                     | `retries`                  | Integer    | Max retry attempts for failed writes (with backoff).                                                                                                               | `retries=3`                            |
|                     | `delivery.timeout.ms`      | Millis     | Total time allowed for delivery (including retries).                                                                                                                | `120000` (2 minutes)                   |
|                     | `enable.idempotence`       | Boolean    | Enables idempotent writes (deduplication).                                                                                                                       | `true`                                  |
| **PostgreSQL**      | `fsync`                    | Boolean    | Forces writes to physical disk (slower but more durable).                                                                                                           | `on`                                    |
|                     | `synchronous_commit`       | String     | Commit mode (off, remote_apply, remote_write, local). Higher values increase durability but reduce performance.                                                      | `remote_write`                         |
|                     | `wal_level`                | String     | Log level (minimal, replica, logical). Higher levels improve durability for backups/replication.                                                                     | `replica`                              |
| **Distributed DB**  | `replication.factor`       | Integer    | Number of replicas for a partition. Higher values improve fault tolerance.                                                                                           | `replication.factor=3`                 |
|                     | `min.insync.replicas`      | Integer    | Minimum replicas acknowledging a write (e.g., Kafka’s `min.insync.replicas=2`).                                                                        | `2`                                     |
| **Application**     | Retry policy               | Config     | Exponential backoff + jitter for retries (e.g., `maxAttempts: 5`, `backoff: 100ms`).                                                                                  | `{ maxAttempts: 3, backoff: 500ms }    |
|                     | Idempotency key            | String     | Unique key for deduplicating retries (e.g., `requestId`).                                                                                                          | `requestId: "txn_12345"`               |

---

## **Implementation Details**
### **1. Configuring Durability in Kafka**
- **Producer Settings:**
  ```properties
  acks=all
  retries=5
  delivery.timeout.ms=30000
  enable.idempotence=true
  ```
- **Broker Settings (for durability):**
  ```properties
  min.insync.replicas=2
  default.replication.factor=3
  log.flush.interval.messages=10000
  log.flush.interval.ms=1000
  ```

- **Impact:**
  - `acks=all` ensures full commit but slows writes.
  - `min.insync.replicas=2` guarantees durability even if one replica fails.

### **2. Tuning PostgreSQL for Durability**
- **PostgreSQL `postgresql.conf`:**
  ```ini
  fsync = on               # Enforce disk sync
  synchronous_commit = remote_apply  # Balance speed/durability
  wal_level = replica      # Enable WAL for replication
  archive_mode = on        # Enable WAL archiving for backups
  ```
- **Impact:**
  - `fsync=on` ensures no data loss on crashes (but increases latency).
  - `synchronous_commit=remote_apply` commits to local + remote replicas before acknowledging.

### **3. Retry and Backpressure Strategies**
- **Exponential Backoff:**
  ```python
  def retry_with_backoff(max_attempts=3, base_delay_ms=100):
      for attempt in range(max_attempts):
          try:
              return execute_write()  # Your write operation
          except Exception as e:
              if attempt == max_attempts - 1:
                  raise e
              time.sleep(base_delay_ms * (2 ** attempt) + random.uniform(0, 0.1))  # Jitter
  ```
- **Backpressure in Consumers:**
  - Use Kafka’s `max.poll.interval.ms` or consumer lag metrics to throttle producers when durability bottlenecks occur.

### **4. Checkpointing (State Persistence)**
- **Example (Python + Redis):**
  ```python
  # Periodically save state to Redis
  def checkpoint(state, redis_client, interval_sec=60):
      while True:
          redis_client.set("app_state", json.dumps(state))
          time.sleep(interval_sec)
  ```
- **Key Considerations:**
  - Trade-off between checkpoint frequency (lower latency vs. higher risk of loss).
  - Use atomic operations (e.g., Redis `MSET`) for consistency.

---

## **Query Examples**
### **1. Kafka Durability Checks**
```bash
# Check under-replicated partitions (durability risk)
kafka-topics --bootstrap-server localhost:9092 --describe --topic my_topic

# Monitor broker replication lag
kafka-consumer-groups --bootstrap-server localhost:9092 --group my_group --describe
```

### **2. PostgreSQL Durability Audit**
```sql
-- Check WAL archiving status
SELECT pg_is_in_recovery(), pg_wal_lsn_diff(now(), pg_last_wal_replay_lsn());

-- Verify replication lag
SELECT pg_stat_replication;
```

### **3. Application-Level Durability Logging**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("durability")

def log_durability_metrics(acks, replicas_acked, latency_ms):
    logger.info(f"Write acked by {replicas_acked}/{replicas} replicas. "
                f"Latency: {latency_ms}ms. Acks: {acks}")
```

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Root Cause**                          | **Mitigation**                                                                 |
|--------------------------------------|----------------------------------------|---------------------------------------------------------------------------------|
| **Data loss on crashes**             | `fsync` disabled or `ack=0`            | Enable `fsync`, use `acks=all`, or WAL.                                         |
| **Thundering herd on retries**       | No backoff/jitter                       | Implement exponential backoff + jitter.                                       |
| **Replication lag**                  | Slow followers                         | Tune `replication.slot.max.messages` (Kafka) or `wal_writer_delay` (PostgreSQL). |
| **Idempotency violations**           | Missing request IDs                    | Enforce idempotency keys (e.g., UUIDs) in producers/consumers.                   |
| **Checkpointing overload**           | Too-frequent writes                    | Use async checkpointing or batch writes.                                        |

---

## **Related Patterns**
1. **Eventual Consistency**
   - Trade-off between durability and latency (e.g., DynamoDB’s `Strong` vs. `Eventual` consistency).
   - *See:* [Pattern] Eventual Consistency - Reference Guide.

2. **Circuit Breaker**
   - Prevents cascading failures during durability bottlenecks (e.g., Kafka broker unavailability).
   - *See:* [Pattern] Circuit Breaker - Reference Guide.

3. **Saga Pattern**
   - Manages distributed transactions with compensating actions for durability in microservices.
   - *See:* [Pattern] Saga Pattern - Reference Guide.

4. **Leader Election (for Replication)**
   - Ensures a single leader for writes in systems like ZooKeeper or etcd.
   - *See:* [Pattern] Leader Election - Reference Guide.

5. **Data Sharding**
   - Distributes writes to reduce hotspots in high-durability systems (e.g., Cassandra).
   - *See:* [Pattern] Data Sharding - Reference Guide.

---
## **Further Reading**
- [Kafka Durability Docs](https://kafka.apache.org/documentation/#durability)
- [PostgreSQL WAL Tuning Guide](https://www.postgresql.org/docs/current/runtime-config-wal.html)
- [CAP Theorem](https://en.wikipedia.org/wiki/CAP_theorem) (Durability vs. Consistency trade-offs).