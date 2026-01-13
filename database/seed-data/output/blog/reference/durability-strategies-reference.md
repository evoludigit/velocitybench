# **[Pattern] Durability Strategies Reference Guide**

---

## **Overview**
Durability in distributed systems ensures that data persists reliably despite failures—such as node crashes, network partitions, or prolonged outages. This guide outlines key **Durability Strategies** to design resilient applications by mitigating data loss and ensuring recoverability. The strategies range from basic *in-memory persistence* to advanced *replica management* and *event sourcing*. Each approach balances **consistency**, **availability**, and **partition tolerance** (CAP Theorem trade-offs) while addressing latency and write overhead.

This guide covers **key techniques**:
- **Replication** (primary-secondary, multi-leader)
- **WAL (Write-Ahead Logging)**
- **Durable Queues**
- **Event Sourcing & CQRS**
- **Periodic Snapshots**
- **Idempotency & Retries**

---

## **Implementation Details**

### **Key Concepts**
| **Term**               | **Definition**                                                                 | **Use Case**                                                                 |
|------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Atomic Writes**      | Ensures data is written completely or not at all; no partial updates.          | Financial transactions, inventory systems.                                 |
| **Crash Recovery**     | Restores system state from consistent checkpoints after a failure.             | Database recovery, distributed queues.                                       |
| **Consistency Models** | Strong (immediate sync), Eventual (asynchronous sync), Tunable (configurable). | Trade-offs between performance and reliability.                             |
| **WAL (Write-Ahead Log)** | Logs all writes before applying them to storage; enables recovery.           | Databases (PostgreSQL, MongoDB), message brokers.                            |
| **Idempotency**        | Ensures repeated operations have the same outcome.                             | Retries for failed requests without duplication.                            |
| **Quorum Writes**      | Replicates data to a majority of nodes before acknowledging a write.           | Distributed databases (Cassandra, DynamoDB).                                |

---

## **Schema Reference**
Below are table schemas for common durability implementations.

### **1. Primary-Secondary Replication**
| **Field**          | **Type**       | **Description**                                                                 | **Example**                     |
|--------------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `primary_node`     | String         | IP/hostname of the primary node handling writes.                                | `primary.db.example.com`        |
| `secondary_nodes`  | Array[String]  | List of replica nodes syncing data from the primary.                           | `["secondary1", "secondary2"]`  |
| `sync_strategy`    | Enum           | *"sync"* (blocking) or *"async"* (fire-and-forget).                            | `sync`                          |
| `replication_lag`  | Integer        | Max allowed delay (ms) before failover.                                        | `1000`                          |

**Example JSON:**
```json
{
  "primary_node": "db-primary.region1",
  "secondary_nodes": ["db-secondary.region1", "db-secondary.region2"],
  "sync_strategy": "sync",
  "replication_lag": 1000
}
```

---

### **2. Write-Ahead Log (WAL)**
| **Field**          | **Type**       | **Description**                                                                 | **Example**                     |
|--------------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `log_file`         | String         | Path to the WAL file (e.g., segment log).                                     | `/var/log/wal_segment.1.log`     |
| `log_retention`    | Duration       | How long to keep logs before archiving/deletion.                               | `"P7D"` (7 days)                |
| `fsync_interval`   | Duration       | How often to flush log to disk (reduces crash risk).                          | `"100ms"`                       |
| `recovery_hook`    | Function       | Callback to replay logs on startup.                                           | `onRecovery()`                  |

**Example (Pseudocode):**
```python
wal_config = {
  "log_file": "/opt/wal/data.log",
  "log_retention": "P7D",
  "fsync_interval": "100ms",
  "recovery_hook": lambda: replay_logs()
}
```

---

### **3. Durable Queue (Kafka/RabbitMQ)**
| **Field**          | **Type**       | **Description**                                                                 | **Example**                     |
|--------------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `queue_name`       | String         | Name of the durable queue.                                                     | `orders.processing`             |
| `partition_count`  | Integer        | Number of partitions for parallelism.                                          | `3`                             |
| `retention_policy` | Enum           | *"delete"*, *"compact"*, or *"time-based"* (e.g., `7d`).                      | `"compact"`                     |
| `ack_policy`       | Enum           | *"all"*, *"manual"*, or *"batch"* (confirmation strategy).                      | `"manual"`                      |

**Example (Kafka Config):**
```json
{
  "queue_name": "user-activity",
  "partition_count": 4,
  "retention_policy": "time-based:P30D",
  "ack_policy": "all"
}
```

---

### **4. Event Sourcing**
| **Field**          | **Type**       | **Description**                                                                 | **Example**                     |
|--------------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `event_store`      | String         | URI to the event store (e.g., DynamoDB table).                                 | `"arn:aws:dynamodb:us-east-1:1234567890:table/events"` |
| `event_version`    | String         | Schema version for events (e.g., `v1`).                                         | `"v1"`                          |
| `projection`       | Function       | Function to materialize state from events.                                      | `projectOrderState()`           |
| `event_ttl`        | Duration       | Time-to-live for expired events.                                                | `"P90D"`                        |

**Example:**
```python
event_sourcing_config = {
  "event_store": "dynamodb://events_table",
  "event_version": "v1",
  "projection": lambda events: {"orders": process_orders(events)}
}
```

---

## **Query Examples**

### **1. Check Replication Lag**
**Context**: Monitor how long it takes for secondaries to sync with the primary.
**Query (Prometheus):**
```promql
replication_lag_seconds{application="orders-service"} > 5
```
**Output**:
```
replication_lag_seconds{application="orders-service", node="secondary1"} 7.2
```
**Action**: If lag exceeds threshold, trigger failover.

---

### **2. Replay WAL for Recovery**
**Command (PostgreSQL):**
```sql
RECOVER FROM LOG '/var/lib/postgresql/wal_segment.2' TIMELINE=2;
```
**Pseudocode (Custom WAL Replayer):**
```python
def replay_wal(log_path):
    with open(log_path, 'r') as f:
        for entry in parse_log(f):
            if entry["type"] == "INSERT":
                apply_to_db(entry["data"])
```

---

### **3. Durable Queue Consumption with Retries**
**Language**: Python (using `pika` for RabbitMQ)
```python
def consume_messages(queue, max_retries=3):
    channel.basic_consume(
        queue=queue,
        on_message_callback=lambda ch, method, props, body:
            process_with_retry(body, max_retries),
        auto_ack=False
    )
    channel.start_consuming()

def process_with_retry(body, retries=0):
    try:
        process_order(body)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        if retries < 3:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            process_with_retry(body, retries+1)
        else:
            log_failed(body, e)
```

---

### **4. Event Sourcing Projection**
**Language**: JavaScript
```javascript
function projectOrders(events) {
  let state = { orders: [] };
  events.forEach(event => {
    switch (event.type) {
      case "ORDER_CREATED":
        state.orders.push(event.payload);
        break;
      case "ORDER_CANCELED":
        state.orders = state.orders.filter(o => o.id !== event.payload.id);
        break;
    }
  });
  return state;
}
```

---

## **Common Patterns & Anti-Patterns**

### **✅ Do:**
- **Use WAL** for crash recovery in databases (e.g., PostgreSQL, MongoDB).
- **Implement idempotent operations** to handle retries safely.
- **Monitor replication lag** and auto-failover if thresholds are breached.
- **Combine event sourcing with CQRS** for scalable read/write separation.
- **Test durability** under load (e.g., simulate network partitions).

### **❌ Avoid:**
- **Single-writer anti-pattern**: No replication → risk of data loss.
- **Blocking sync replication**: Can bottleneck writes (use async where possible).
- **Ignoring WAL fsync intervals**: Increases crash risk (tune `fsync_interval`).
- **Over-relying on retries without idempotency** (risk of duplicate processing).
- **Storing state only in memory** (e.g., Redis without persistence).

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Combine**                          |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Idempotent Operations** | Ensures retries don’t cause side effects; pairs well with durability.            | High-latency networks, retries.             |
| **Circuit Breaker**       | Prevents cascading failures when durability checks fail (e.g., replica unhealth). | Distributed systems with transient errors. |
| **Saga Pattern**          | Manages long-running transactions via durability (e.g., WAL + compensating actions). | Microservices with distributed ACID.       |
| **Leader Election**       | Dynamically selects primary nodes for replication; critical for multi-leader setups. | Geo-replicated databases.                  |
| **Slacking Consumers**    | Processes messages out-of-order in event sourcing; requires idempotent operations. | Event-driven architectures.                 |

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Replication lag > threshold**     | Primary node overwhelmed or secondary slow.                                  | Scale primary, increase `replication_lag`.                                    |
| **WAL replay fails**                | Log corrupted or missing segments.                                           | Check `log_retention`, restore from backup.                                  |
| **Queue messages lost**             | `ack_policy="auto"` without durability.                                      | Set `ack_policy="manual"` + transactional writes.                           |
| **Event sourcing projection stale** | Events not replayed on startup.                                              | Ensure `recovery_hook` runs on startup.                                       |
| **Crash leads to data loss**        | No WAL or `fsync_interval` too long.                                         | Enable WAL, reduce `fsync_interval` to `10ms`.                               |

---
**References**:
- [CAP Theorem](https://www.allthingsdistributed.com/files/osdi02-hyperspace.pdf)
- [PostgreSQL WAL](https://www.postgresql.org/docs/current/wal-introduction.html)
- [Event Sourcing (DDD)](https://martinfowler.com/eaaP/evs.html)