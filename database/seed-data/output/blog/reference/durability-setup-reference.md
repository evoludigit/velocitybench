# **[Pattern] Durability Setup Reference Guide**

## **Overview**
The **Durability Setup** pattern ensures that data persistence, recovery, and fault tolerance are configured consistently across distributed systems, microservices, or event-driven architectures. It standardizes how applications define durability requirements for storage, transactions, and replication, minimizing data loss and enabling reliable recovery after failures. This pattern is critical in environments where high availability, consistency, and durability are non-negotiable—such as financial systems, healthcare databases, or mission-critical enterprise applications.

Durability Setup encompasses three primary layers:
1. **Storage Layer** – Configuring durable storage backends (e.g., databases, object stores, block storage) with appropriate redundancy and backup policies.
2. **Transaction Layer** – Defining ACID (Atomicity, Consistency, Isolation, Durability) compliance and compensating actions for rollbacks.
3. **Replication Layer** – Ensuring synchronous or asynchronous replication to secondary nodes or geo-redundant locations.

By following this pattern, teams can avoid common pitfalls like **eventual consistency without recovery guarantees**, **unbounded retry loops**, or **incomplete data recovery**. This guide provides implementation details, schema references, and query examples to help architects and developers apply Durability Setup effectively.

---

## **Schema Reference**

Below is a structured schema for defining Durability Setup configurations in a declarative or runtime configuration format (e.g., YAML, JSON, or environment variables).

| **Component**          | **Field**               | **Description**                                                                                     | **Example Values**                                                                                     | **Required** |
|-------------------------|--------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|---------------|
| **Storage Configuration** | `storage_backend`        | Type of durable storage (e.g., relational, NoSQL, file-based).                                      | `postgresql`, `dynamodb`, `s3`, `ceph`                                                              | Yes           |
|                         | `replication_factor`     | Number of synchronous replicas for fault tolerance.                                                   | `3` (for RDBMS), `2` (for distributed key-value stores)                                               | Conditional*  |
|                         | `backup_policy`          | defines backup frequency, retention, and snapshot intervals.                                         | `daily_at_0300`, `retain_for_30_days`, `automatic_snapshot_every_6h`                               | Yes           |
|                         | `storage_class`          | Performance tier (e.g., SSD, HDD, cold storage).                                                     | `ssd`, `standard`, `glacier`                                                                         | Conditional*  |
| **Transaction Configuration** | `transaction_level`      | Isolation level (read-uncommitted, read-committed, repeatable-read, serializable).                 | `serializable`, `read-committed`                                                                       | Conditional*  |
|                         | `timeout_ms`             | Maximum transaction duration before rollback.                                                        | `5000`                                                                                               | Yes           |
|                         | `compensating_actions`   | List of rollback operations (e.g., refunds, cleanup).                                                | `[{"type": "database_rollback", "table": "orders"}, {"type": "s3_delete", "key": "temp_file.txt"}]` | Conditional*  |
| **Replication Configuration** | `replication_strategy`   | Synchronous (`sync`) or asynchronous (`async`) replication.                                          | `sync`, `async`                                                                                       | Yes           |
|                         | `replication_targets`    | List of target nodes/regions for replication.                                                         | `[{"region": "us-east-1", "weight": "1"}, {"region": "eu-west-1", "weight": "0.5"}]`                  | Yes           |
|                         | `conflict_resolution`    | Strategy for handling replication conflicts (e.g., `last_write_wins`, `manual_resolution`).           | `last_write_wins`                                                                                     | Conditional*  |

**Conditional Fields:**
- `replication_factor` is required for distributed databases but optional for single-node setups.
- `transaction_level` and `compensating_actions` depend on whether ACID compliance is critical.
- `storage_class` and `conflict_resolution` are often configurable but not always mandatory.

---

## **Example Implementations**

### **1. Declarative Configuration (YAML)**
```yaml
durability_setup:
  storage:
    backend: postgresql
    replication_factor: 3
    backup_policy:
      schedule: "0 3 * * *"  # Daily at 3 AM
      retention_days: 30
      snapshot_interval: 6h
    storage_class: ssd

  transactions:
    level: serializable
    timeout_ms: 5000
    compensating_actions:
      - type: database_rollback
        table: orders
      - type: s3_delete
        bucket: temp-data
        key: "order_${id}"

  replication:
    strategy: async
    targets:
      - region: us-east-1
        weight: 1.0
      - region: eu-west-1
        weight: 0.5
    conflict_resolution: last_write_wins
```

---

### **2. Runtime Configuration (Programmatic)**
```python
from dataclasses import dataclass

@dataclass
class DurabilityConfig:
    storage: dict = {
        "backend": "postgresql",
        "replication_factor": 3,
        "backup_policy": {
            "schedule": "daily",
            "retention_days": 30
        }
    }
    transactions: dict = {
        "level": "serializable",
        "timeout_ms": 5000,
        "compensating_actions": [
            {"type": "s3_delete", "bucket": "temp-data", "key": "order_${id}"}
        ]
    }
    replication: dict = {
        "strategy": "async",
        "targets": [{"region": "us-east-1", "weight": 1.0}],
        "conflict_resolution": "last_write_wins"
    }

config = DurabilityConfig()
```

---

## **Query Examples**

### **1. Checking Durability Configuration**
```sql
-- PostgreSQL example: Query to verify replication status
SELECT
    pg_is_in_recovery() AS is_replica,
    pg_current_wal_lsn() AS current_lsn,
    pg_last_wal_receive_lsn() AS last_received_lsn
FROM pg_stat_replication;
```

**Output:**
```
| is_replica | current_lsn      | last_received_lsn   |
|------------|------------------|---------------------|
| t          | 0/16C00000       | 0/16B00000         |  -- Indicates replication lag
```

---

### **2. Validating Transaction Isolation**
```python
# Python example using SQLAlchemy (checks isolation level)
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://user:pass@localhost/db")
with engine.connect() as conn:
    result = conn.execute(text("SHOW TRANSACTION ISOLATION LEVEL"))
    print(result.fetchone())  # Expected: 'serializable' or 'read-committed'
```

**Output:**
```
('serializable',)
```

---

### **3. Testing Backup Schedule**
```bash
# Linux cron job to verify backup execution
crontab -l | grep "/path/to/backup_script.sh"
```
**Expected Output:**
```
0 3 * * * /usr/bin/backup_script.sh --verify
```

---

## **Related Patterns**

To complement **Durability Setup**, consider integrating the following patterns:

1. **[Idempotency Pattern]**
   - Ensures operations (e.g., payments, order creates) can be safely retried without unintended side effects.
   - *Use Case:* Prevents duplicate transactions in event-driven systems.

2. **[Circuit Breaker Pattern]**
   - Mimits cascading failures by temporarily stopping calls to failing services after exceeded thresholds.
   - *Use Case:* Avoids overwhelming a replication target during high load.

3. **[Saga Pattern]**
   - Manages long-running transactions via a series of local transactions and compensating actions.
   - *Use Case:* Distributed workflows requiring ACID guarantees across microservices.

4. **[Retry with Exponential Backoff]**
   - Safely retries transient failures with increasing delays to reduce load.
   - *Use Case:* Handling temporary replication lag in async setups.

5. **[Data Shadowing]**
   - Maintains a lightweight, search-optimized copy of critical data for fast reads.
   - *Use Case:* Separating read/write durability (e.g., read replicas for analytics).

---

## **Best Practices**
1. **Default to Strong Consistency**
   - Use synchronous replication (`strategy: "sync"`) for critical data unless latency is prohibitive.

2. **Define Compensating Actions Early**
   - Document rollback procedures (e.g., refunds, cleanup) before deployment to avoid last-minute fixes.

3. **Monitor Replication Lag**
   - Set up alerts for `last_received_lsn` delays in distributed databases.

4. **Test Failure Scenarios**
   - Simulate node failures or network partitions to validate durability guarantees.

5. **Version Your Configurations**
   - Use feature flags or configuration versioning to roll back durability settings iteratively.

---
**See Also:**
- [ACID Transactions Guide](link)
- [Eventual Consistency Anti-Patterns](link)
- [Database Replication Checklist](link)