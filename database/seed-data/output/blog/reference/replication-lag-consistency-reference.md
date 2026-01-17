---
# **[Pattern] Database Replication Lag & Consistency Reference Guide**

---

## **1. Overview**
Database replication allows horizontal scaling for read workloads by distributing data across multiple nodes (primaries and replicas). However, lag (asynchrony) between updates on the primary and replication lag occurs due to network latency, batching, or failover delays. This pattern addresses **consistency models**, **lag detection**, and **stale-read handling** to manage trade-offs between performance and data accuracy.

### **Key Considerations**
- **Trade-off**: Higher replication consistency (e.g., strict sync) reduces lag but hurts write performance.
- **Use cases**: High-availability systems (e.g., web apps), analytics workloads (tolerates eventual consistency), or financial systems (requires strong consistency).
- **Patterns**: Eventual consistency, causal consistency, quorum-based consistency.

---

## **2. Schema Reference**
### **2.1. Core Tables**
*(Simplified for illustration; adjust per DBMS—e.g., PostgreSQL, MySQL, MongoDB.)*

| **Table**               | **Description**                                                                 | **Key Fields**                     |
|-------------------------|-------------------------------------------------------------------------------|-------------------------------------|
| `replication_status`    | Tracks replication health and lag metrics.                                    | `replica_id`, `primary_id`, `lag_seconds`, `last_sync_time` |
| `replica_topology`      | Defines replica hierarchy (e.g., leader-follower, multi-master).               | `replica_id`, `role` (leader/follower), `priority` |
| `event_log`             | Audit log of write operations for causal consistency tracking.                 | `event_id`, `timestamp`, `operation_type`, `replica_id` |

### **2.2. Consistency Models Table**
*(For reference—implement tailored to your DBMS.)*

| **Model**               | **Definition**                                                                 | **When to Use**                          | **Tools/Libraries**                     |
|-------------------------|-------------------------------------------------------------------------------|-----------------------------------------|-----------------------------------------|
| **Strong Consistency**  | Reads always reflect the latest write (blocking writes if replicas fall behind). | Financial transactions, inventory systems. | PostgreSQL `synchronous_commit = remote_apply`, Raft protocol. |
| **Eventual Consistency**| Reads may reflect stale data until replication completes.                     | Analytics dashboards, social media feeds. | DynamoDB, Cassandra, Kafka.             |
| **Causal Consistency**  | Preserves ordering of causally related events (but not global order).         | Collaborative editing (e.g., Google Docs). | CRDTs, Operational Transformation.     |
| **Quorum Consistency**  | Reads require a majority of replicas to agree.                                | Distributed key-value stores.            | etcd, ZooKeeper.                        |

---

## **3. Query Examples**
### **3.1. Detecting Replication Lag**
*(PostgreSQL example; adapt for other DBMS.)*
**Query:** Check lag across all replicas.
```sql
SELECT
    replica_id,
    primary_id,
    EXTRACT(EPOCH FROM (NOW() - last_sync_time)) AS lag_seconds,
    CASE
        WHEN lag_seconds > 5 THEN 'ALERT: High Lag'
        WHEN lag_seconds > 1 THEN 'WARN: Moderate Lag'
        ELSE 'OK'
    END AS status
FROM replication_status;
```

**Output:**
| `replica_id` | `primary_id` | `lag_seconds` | `status`             |
|--------------|--------------|---------------|----------------------|
| `r1`         | `p1`         | 2.4           | WARN: Moderate Lag    |
| `r2`         | `p1`         | 0.1           | OK                    |

---

### **3.2. Querying Stale Data (Eventual Consistency)**
*(MongoDB example with `lastWriteTimestamp`.)*
```javascript
db.order_items.find(
    { status: "pending" },
    {
        _id: 1,
        product_id: 1,
        createdAt: 1,
        replication_time: { $lte: new Date(Date.now() - 10000) } // <10s old
    }
);
```

**Output:**
```json
[
    { "_id": "oid1", "product_id": "p123", "createdAt": ISODate("2023-10-01T10:00:00Z"), "replication_time": ISODate("2023-10-01T09:55:00Z") }
]
```
*(Flag records older than your SLA for reprocessing.)*

---

### **3.3. Causal Consistency Check**
*(PostgreSQL with event_log join.)*
```sql
WITH causal_chain AS (
    SELECT
        event_id,
        ARRAY_AGG(e2.event_id ORDER BY e2.timestamp) AS dependencies
    FROM event_log e1
    LEFT JOIN event_log e2 ON e1.event_id = e2.dependency_id
    GROUP BY event_id
)
SELECT
    c.event_id,
    c.dependencies,
    r.replica_id,
    CASE
        WHEN c.dependencies[1] IS NULL
        THEN 'No dependencies (safe to read)'
        ELSE 'Possible causal conflict'
    END AS consistency_check
FROM causal_chain c
JOIN (
    SELECT replica_id, MAX(last_sync_time) AS sync_time
    FROM replication_status
    GROUP BY replica_id
) r ON TRUE;
```

---

## **4. Implementation Details**
### **4.1. Lag Mitigation Strategies**
| **Strategy**               | **Description**                                                                 | **Pros**                          | **Cons**                          |
|----------------------------|-------------------------------------------------------------------------------|-----------------------------------|-----------------------------------|
| **Primary Replication**    | All writes go to a single primary; replicas sync asynchronously.               | Simple setup.                     | Single point of failure.          |
| **Multi-Primary (Active-Active)** | Multiple replicas accept writes; conflicts resolved via application logic.  | High availability.                | Complexity in conflict resolution.|
| **Read Replicas + Caching**| Cache hot data in Redis/Memcached to reduce replica load.                      | Low latency reads.                | Stale cache invalidation needed.  |
| **Change Data Capture (CDC)** | Stream writes to a message queue (e.g., Debezium, Kafka Connect) for async processing. | Decouples writes/reads.           | Adds infra complexity.             |
| **Quorum Reads**           | Require `N` replicas to agree before proceeding (e.g., DynamoDB’s `ConsistentRead`). | Strong consistency.               | Higher latency.                    |

---

### **4.2. Consistency Tools**
| **Tool**               | **Purpose**                                                                 | **DBMS Support**          |
|------------------------|-----------------------------------------------------------------------------|---------------------------|
| **PostgreSQL `pg_repack`** | Rebuild replicas with minimal downtime.                                     | PostgreSQL.               |
| **MySQL `mysqldump` + PT-Table-Sync** | Sync schemas/data between replicas.                                         | MySQL.                    |
| **Debezium**           | Capture DB changes and stream to Kafka for async processing.                 | PostgreSQL, MySQL, MongoDB.|
| **CockroachDB**        | Distributed SQL with built-in strong consistency.                            | Self-hosted/managed.      |
| **AWS DMS**            | Database migration/replication service.                                      | Multi-DB support.         |

---

### **4.3. Detecting Lag Alerts**
**Example (Prometheus + Alertmanager):**
```yaml
# alert.rules.yml
- alert: HighReplicationLag
  expr: replication_lag_seconds > 5
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Replica {{ $labels.replica_id }} lagging by {{ $value }}s"
    description: "Primary {{ $labels.primary_id }} has {{ $value }}s of lag."
```
*(Metrics sourced from `pg_stat_replication` or custom probes.)*

---

## **5. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **When to Use**                          |
|--------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------|
| **[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)** | Store state changes as an immutable log for auditability.                     | Audit trails, compliance.               |
| **[Command Query Responsibility Segregation (CQRS)](https://martinfowler.com/bliki/CQRS.html)** | Separate read/write models to optimize each.                                | High-scale read-heavy systems.          |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Manage distributed transactions via compensating actions.                     | Microservices with eventual consistency.|
| **[Bulkhead Pattern](https://microservices.io/patterns/resilience/bulkhead.html)** | Isolate replica failures to prevent cascading outages.                        | Resilience in multi-replica setups.     |
| **[Idempotent Operations](https://martinfowler.com/bliki/IdempotentOperation.html)** | Ensure repeated writes (e.g., due to retries) don’t cause duplicates.        | Idempotent APIs (e.g., payments).        |

---

## **6. Best Practices**
1. **Monitor Lag**: Use tools like `pgBadger` (PostgreSQL), `pt-heartbeat` (MySQL), or Prometheus.
2. **Define SLAs**: Acceptable lag thresholds (e.g., <1s for transactions, >5s for analytics).
3. **Prioritize Replicas**: Promote replicas with lower lag for critical reads.
4. **Backfill Stale Data**: Use CDC or batch jobs to sync delayed updates.
5. **Test Failovers**: Simulate primary failures to validate recovery lag.
6. **Document Trade-offs**: Clearly communicate consistency guarantees to consumers.

---
**References**
- [PostgreSQL Replication Docs](https://www.postgresql.org/docs/current/replication.html)
- [Cassandra Consistent Reads](https://cassandra.apache.org/doc/latest/cql/consistency.html)
- [Eventual Consistency Explained](https://www.allthingsdistributed.com/files/amazon-dynamodb-simple-version-2.pdf)