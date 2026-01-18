# **[Pattern] Consistency Troubleshooting Reference Guide**

---

## **Overview**
This guide provides a structured approach to identifying, diagnosing, and resolving **distributed system inconsistency**—where data replication lags, logical conflicts occur, or perceived inconsistencies arise despite eventual consistency guarantees. Common in event-sourced systems, databases with replication, or microservices architectures, inconsistencies can lead to **lost updates, stale reads, or cascading failures**.

This pattern covers:
- **Symptom categorization** (e.g., lag vs. logical divergence)
- **Root cause analysis** (tracing through replication pipelines, transaction logs, or event streams)
- **Mitigation strategies** (tuning, compensating transactions, or schema adjustments)
- **Proactive monitoring** (alert thresholds, consistency checks)

---

## **Schema Reference**
Below are key schemas for diagnosing and modeling inconsistency cases.

### **1. Inconsistency Event Log Schema**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `event_id`          | UUID       | Unique identifier for the inconsistency event.                              |
| `timestamp`         | ISO-8601   | When the event was detected/recorded.                                       |
| `system`            | String     | Affected system (e.g., `payment-service`, `inventory-db`).                  |
| `severity`          | Enum       | `critical`, `warning`, `info` (e.g., `CRITICAL` if transaction failure).    |
| `type`              | Enum       | `read-write`, `replication-lag`, `schema-mismatch`, `event-loss`.          |
| `affected_entities` | Array      | List of IDs/keys where inconsistency occurred (e.g., `["order-42", "user-123"]`). |
| `root_cause`        | String     | Initial hypothesis (e.g., `network_partition` or `deadlock`).               |
| `resolved_at`       | ISO-8601   | Timestamp if resolved; `null` otherwise.                                   |
| `resolution`        | String     | Steps taken (e.g., `restart_replicas`, `manual_rollback`).                  |
| `tags`              | Array      | Metadata (e.g., `["event-sourcing"]`, `["postgres"]`).                      |

---

### **2. Replication Lag Metrics Schema**
| Metric               | Unit       | Description                                                                 |
|----------------------|------------|-----------------------------------------------------------------------------|
| `source_to_target_latency` | Milliseconds | End-to-end delay from producer to consumer (e.g., Kafka lag).              |
| `pending_events`     | Integer    | Number of unprocessed events in the queue.                                 |
| `throughput`         | Events/s   | Events processed per second (indicator of bottleneck).                     |
| `partition_lead`     | Integer    | Leader-follower lag in milliseconds (for DB replication).                  |
| `error_rate`         | Percentage | % of failed replication attempts.                                           |

---

### **3. Consistency Check Query Template**
```sql
-- Detect divergent reads across replicas
SELECT
    user_id,
    MAX(CASE WHEN source_system = 'primary' THEN value END) AS primary_value,
    MAX(CASE WHEN source_system = 'replica' THEN value END) AS replica_value,
    COUNT(*) AS discrepancy_count
FROM event_logs
WHERE event_type = 'user_profile_update'
  AND source_system IN ('primary', 'replica')
GROUP BY user_id
HAVING MIN(primary_value) != MIN(replica_value);
```

---

## **Implementation Details**

### **Key Concepts**
1. **Eventual vs. Strong Consistency**:
   - *Eventual*: Data converges over time (e.g., DynamoDB).
   - *Strong*: Immediate consistency (e.g., ACID transactions in PostgreSQL).
   - **Troubleshooting focus**: Identify if divergence is *tolerable delay* or *permanent split*.

2. **Consistency Boundaries**:
   - **Local**: Within a single database/table.
   - **Global**: Across services (e.g., order + payment).
   - **Temporal**: Between snapshot and real-time (e.g., reports vs. live data).

3. **Failure Modes**:
   - **Replication Lag**: Followers fall behind (e.g., Kafka consumer lag).
   - **Event Loss**: Messages dropped in transit (e.g., network partition).
   - **Schema Drift**: Schema changes misalign replicas (e.g., adding a column without backward compatibility).
   - **Concurrency Conflicts**: Lost updates in non-atomic writes.

---

### **Step-by-Step Troubleshooting Workflow**
#### **1. Detect Inconsistency**
- **Symptoms**:
  - `SELECT * FROM orders WHERE user_id = 123` returns `quantity=5` on primary but `quantity=4` on replica.
  - Application logs show `DuplicateTransactionException` for a payment.
- **Tools**:
  - **Replication lag alerts**: Prometheus/Grafana dashboards for `replication_lag_seconds`.
  - **Distributed tracing**: Jaeger/Zipkin to track event flow across services.
  - **Schema diff tools**: Compare schema versions (e.g., `pg_dump` for PostgreSQL).

#### **2. Isolate the Scope**
- **Narrow to affected entities**: Query logs for `user_id`, `order_id`, or `transaction_id`.
- **Check replication topology**:
  ```bash
  # Example PostgreSQL replication status
  psql -c "SELECT pg_stat_replication;"
  ```
  - Look for `sent_lsn` vs. `replay_lsn` gaps.

#### **3. Root Cause Analysis**
| **Symptom**               | **Possible Root Cause**               | **Diagnostic Query/Command**                          |
|---------------------------|---------------------------------------|-------------------------------------------------------|
| High replication lag      | Consumer overloaded                   | `kafka-consumer-groups --describe` (for Kafka)       |
| Event loss                | Network partition                     | Check Broker logs for `UNMET_REQUIRED_ACKS` errors   |
| Schema mismatch           | Backward-incompatible migration       | `SELECT column_name FROM information_schema.columns`  |
| Lost updates              | No conflict resolution (e.g., NDB)    | Audit `last_commit_ts` in event logs                  |

#### **4. Mitigation Strategies**
| **Strategy**              | **When to Use**                          | **Implementation Example**                          |
|---------------------------|------------------------------------------|----------------------------------------------------|
| **Increase replication throughput** | Consumer lag due to slow processing | Scale Kafka brokers or partition topics.            |
| **Use compensating transactions** | Idempotent writes failed | Implement `rollback_order` microservice.            |
| **Adopt CRDTs**           | Conflict-free data types                | Use `Yjs` or `Automerge` for collaborative edits. |
| **Temporarily break strong consistency** | High availability > consistency | Use eventual consistency (e.g., Redis Cluster).    |
| **Schema evolution**      | Adding optional fields                 | Backward-compatible migrations (e.g., PostgreSQL `ALTER TABLE`). |

#### **5. Proactive Monitoring**
- **Alerts**:
  - Replication lag > 5 seconds (adjust threshold based on SLA).
  - Event loss > 0% in 1-hour window.
- **Consistency checks**:
  ```sql
  -- Cron job to validate invariants
  CREATE OR REPLACE FUNCTION check_inventory_balance()
  RETURNS void AS $$
  BEGIN
    FOR r IN SELECT product_id, SUM(quantity) FROM orders GROUP BY product_id
    LOOP
      EXECUTE format('SELECT * FROM inventory WHERE product_id = %s AND quantity != %s',
                    r.product_id, r.quantity);
      IF FOUND THEN RAISE EXCEPTION 'Inconsistency detected!';
      END IF;
    END LOOP;
  END;
  $$ LANGUAGE plpgsql;
  ```

---

## **Query Examples**

### **1. Detect Replication Lag (PostgreSQL)**
```sql
-- Identify lagging replicas
SELECT
    pg_stat_replication.pid,
    pg_stat_replication.client_addr,
    (now() - pg_stat_replication.replay_lag) AS lag_seconds,
    pg_stat_replication.state
FROM pg_stat_replication
WHERE state = 'streaming' AND lag_seconds > 5;
```

### **2. Find Orphaned Events (Kafka)**
```bash
# List unassigned partitions (potential lag)
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-consumer-group \
  --describe --all-topics | grep "LAG"
```

### **3. Schema Drift Detection (Python)**
```python
from typing import Dict, List
import pandas as pd

def compare_schemas(replica1_schema: Dict, replica2_schema: Dict) -> List[str]:
    """Identify missing/extra columns."""
    set1 = set(replica1_schema.keys())
    set2 = set(replica2_schema.keys())
    return list(set1.symmetric_difference(set2))
```

### **4. Transaction Conflict Audit (Event Sourcing)**
```sql
-- Find conflicting writes to the same aggregate
WITH conflicted_aggregates AS (
  SELECT
    aggregate_id,
    COUNT(*) AS write_count,
    MAX(timestamp) AS last_write
  FROM events
  WHERE event_type = 'UpdateOrder'
  GROUP BY aggregate_id
  HAVING COUNT(*) > 1
)
SELECT * FROM conflicted_aggregates
ORDER BY write_count DESC;
```

---

## **Related Patterns**
| **Pattern**                     | **Use Case**                                                                 | **Connection to Consistency Troubleshooting**                     |
|----------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------|
| **[Saga Pattern]**               | Distributed transactions                                                | Use compensating transactions to recover from inconsistencies.      |
| **[Event Sourcing]**             | Audit trail for state changes                                             | Log all events to detect drift; replay to reconcile replicas.      |
| **[CQRS]**                       | Read/write separation                                                     | Design separate consistency guarantees for each model.             |
| **[CRDTs]**                      | Conflict-free collaborative editing                                        | Replace locks with convergent data types.                          |
| **[Database Per Service]**       | Microservices isolation                                                   | Avoid cross-service consistency; use event bridges instead.        |
| **[Retry with Backoff]**         | Resilient retry mechanisms                                                | Mitigate transient replication failures.                           |

---

## **Best Practices**
1. **Instrumentation**:
   - Log `replication_lag` and `event_processing_time` to distributed tracing (e.g., OpenTelemetry).
   - Use **canary releases** to test schema changes before full rollout.

2. **Testing**:
   - **Chaos engineering**: Simulate network partitions (e.g., with [Chaos Mesh](https://chaos-mesh.org/)).
   - **Regression tests**: Validate invariants after deployments (e.g., `quantity >= 0`).

3. **Trade-offs**:
   - **Strong consistency**: Higher latency/throughput cost (e.g., 2PC vs. eventual consistency).
   - **Eventual consistency**: Risk of stale reads; use **read repair** or **hinted handoff** (e.g., Cassandra).

4. **Documentation**:
   - Maintain a **consistency matrix** (e.g., [this example](https://github.com/eventuated/consistency-matrix)).
   - Label events with `consistency_level` (e.g., `STRONG`, `EVENTUAL`).

---
**See also**:
- [CAP Theorem](https://www.informit.com/articles/article.aspx?p=2091451)
- [Eventual Consistency Patterns](https://martinfowler.com/articles/patterns-of-distributed-systems.html#EventualConsistency) (Martin Fowler)