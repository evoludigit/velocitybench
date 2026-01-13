# **[Pattern] Durability Configuration Reference Guide**

---

## **Overview**
Durability Configuration ensures that data persistence, transactions, and system state remain intact across failures, crashes, or prolonged outages. This pattern defines how applications configure resilience mechanisms—such as transaction logs, backup strategies, checkpointing, and recovery protocols—to withstand unexpected disruptions while minimizing data loss.

Implementations vary by language, framework, and infrastructure (e.g., distributed systems vs. monolithic applications). This guide covers core configuration options, schema structures, and practical examples for setting up durable systems.

---

## **Key Concepts**

### **Core Principles**
| Concept               | Definition                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **Atomicity**         | Operations succeed fully or fail completely; no partial updates.                              |
| **Consistency**       | System state remains valid after failures (e.g., ACID compliance in databases).                |
| **Isolation**         | Concurrent operations don’t interfere (e.g., locks, MVCC).                                     |
| **Durability**        | Data survives system crashes (e.g., write-ahead logs, replication).                            |
| **Recovery**          | System restores state after failure (e.g., checkpointing, snapshots).                          |

### **Failure Scenarios Addressed**
- **Node Failures** (e.g., servers, containers)
- **Network Partitions** (e.g., microservices losing connectivity)
- **Data Corruption** (e.g., disk failures)
- **Human Error** (e.g., misconfigured deletes)

---

## **Schema Reference**

### **Durability Configuration Schema**
Below is a structured schema for durability settings (JSON/YAML-compatible). Fields are categorized by component:

| **Component**         | **Field**                | **Type**       | **Description**                                                                                                                                                                                                 | **Required?** | **Default/Notes**                                                                 |
|-----------------------|--------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------------------|
| **Transaction Log**   | `log_retention_days`     | Integer        | How long log entries are retained before pruning.                                                                                                                                                              | Optional       | `7` (days)                                                                           |
|                       | `sync_policy`            | Enum           | Log synchronization mode: `"async"` (fire-and-forget), `"sync"` (flush after commit), or `"fsync"` (disk sync).                                                                                        | Optional       | `"async"`                                                                           |
|                       | `compression_level`      | Integer (0–9)  | Compression level for log entries (0 = none, 9 = max).                                                                                                                                                       | Optional       | `6`                                                                                  |
| **Checkpointing**     | `checkpoint_interval`    | String         | Time-based interval (e.g., `"5m"`, `"1h"`) or size-based (e.g., `"100MB"`).                                                                                                                                       | Optional       | `"10m"` (10 minutes)                                                                |
|                       | `recovery_window`        | Integer (sec)  | Max time (seconds) to wait for recovery before aborting.                                                                                                                                                     | Optional       | `300` (5 minutes)                                                                   |
| **Backup**            | `backup_schedule`        | String         | Cron-like schedule (e.g., `"0 2 * * *"` for daily at 2 AM).                                                                                                                                                   | Optional       | `"0 3 * * *"` (3 AM daily)                                                            |
|                       | `backup_retention`       | Integer        | Number of backups to retain.                                                                                                                                                                               | Optional       | `7` (7 backups)                                                                     |
|                       | `backup_vault`           | String         | Storage provider (e.g., `"s3"`, `"azure_blob"`, `"local"`).                                                                                                                                                   | Optional       | `null` (local if unspecified)                                                        |
| **Retry Policy**      | `max_retries`            | Integer        | Max retries for transient failures (e.g., network timeouts).                                                                                                                                                  | Optional       | `3`                                                                                  |
|                       | `backoff_strategy`       | Enum           | `"exponential"` (default), `"linear"`, or `"constant"` delay.                                                                                                                                                 | Optional       | `"exponential"`                                                                      |
| **Replication**       | `replica_count`          | Integer        | Number of replicas for fault tolerance.                                                                                                                                                                      | Optional       | `3` (for HA setups)                                                                 |
|                       | `consistency_model`      | Enum           | `"strong"`, `"eventual"`, or `"causal"`.                                                                                                                                                                  | Optional       | `"strong"`                                                                           |

---

## **Implementation Examples**

### **1. Configuring Durability in a Database (PostgreSQL)**
```sql
-- Enable WAL (Write-Ahead Log) retention for durability
ALTER SYSTEM SET wal_keep_size TO '1GB';
ALTER SYSTEM SET checkpoint_timeout TO '10min';

-- Configure synchronous commits (durability)
ALTER SYSTEM SET synchronous_commit TO 'on';
ALTER SYSTEM SET hot_standby = 'on'; -- For replication
```

**YAML Equivalent:**
```yaml
postgresql:
  durability:
    wal_retention: "1GB"
    checkpoint_interval: "10m"
    sync_mode: "sync"  # Full sync on commit
    replica_count: 3
```

---

### **2. Durability in a Microservice (Node.js + Redis)**
```javascript
const redis = require("redis");
const client = redis.createClient({
  url: "redis://localhost:6379",
  durability: {
    checkpointIntervalMs: 5000,  // 5-second checkpoints
    maxRetries: 5,
    backoffStrategy: "exponential",
    backup: {
      schedule: "0 2 * * *",  // Daily backups at 2 AM
      retention: 7,
      provider: "s3",         // Configure AWS S3 credentials separately
    },
  },
});
```

**Key Flags:**
- `checkpointIntervalMs`: Triggers Redis snapshots.
- `backup.provider`: Links to an external backup service.

---

### **3. Kubernetes Durability (Pod Disruption Budget)**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: durable-app-pdb
spec:
  maxUnavailable: 1  # Ensures at least 2 replicas run
  selector:
    matchLabels:
      app: durable-app
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: durable-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime updates
  template:
    spec:
      containers:
      - name: app
        image: durable-app:v1
        volumeMounts:
        - name: persistent-storage
          mountPath: /data
      volumes:
      - name: persistent-storage
        persistentVolumeClaim:
          claimName: durable-app-pvc
```

**Durability Features:**
- **Replicas**: 3 pods for fault tolerance.
- **PersistentVolume**: Survives pod restarts.
- **Rolling Updates**: Zero-downtime deployments.

---

### **4. Distributed Durability (Apache Kafka)**
```json
{
  "durability": {
    "log_retention_days": 7,
    "min_insync_replicas": 2,  // Ensure at least 2 replicas commit
    "unclean_leader_election": "false",  // Prevent data loss under partition splits
    "replication_factor": 3
  },
  "checkpointing": {
    "interval": "5m",
    "offset_commit": true  // Ensure consumer offsets are durable
  }
}
```

**Key Takeaways:**
- `min_insync_replicas`: Critical for fault tolerance.
- `offset_commit`: Prevents consumer state loss.

---

## **Query Examples**

### **1. Checking Durability Status (Redis CLI)**
```bash
# Verify checkpointing is active
CONFIG GET checkpoint_frequency
# Output: 1) "checkpoint_frequency" 2) "5000"
```

### **2. PostgreSQL Recovery Verification**
```sql
-- Check last checkpoint and crash recovery readiness
SELECT pg_is_in_recovery(), pg_last_checkpoint_lsn();
```

### **3. Kubernetes Pod Duration (Durability Metrics)**
```bash
kubectl describe pod durable-app-7c8f5d7c4b
# Look for:
// - `Node Reserved` resources to ensure disaster recovery.
// - `Restart Count` to identify crashes.
```

---

## **Validation & Testing**
| **Test Case**               | **Tool/Command**                                                                 | **Expected Outcome**                                                                 |
|-----------------------------|----------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Crash Recovery              | Kill PostgreSQL; restart with `pg_ctl start`.                                   | Database recovers from last checkpoint.                                               |
| Backup Restoration          | Restore from S3 (`aws s3 sync s3://backup-bucket /tmp/restore`).                | Data matches pre-failure state.                                                      |
| Network Partition Tolerance | Use `iptables` to simulate network splits.                                      | Replicas remain consistent (e.g., Kafka `min_insync_replicas` holds).               |
| Retry Policy Test           | Simulate timeouts (`nc -l 8080` + kill server).                               | App retries with backoff (log `max_retries` reached).                                 |

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                               |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Prevents cascading failures by stopping requests to failing services.                                | High-latency or unreliable dependencies (e.g., third-party APIs).                          |
| **Idempotent Operations** | Designs operations to be safely retried without side effects.                                       | HTTP APIs, payments, or any state-changing operations.                                      |
| **Saga Pattern**          | Manages distributed transactions via compensating actions.                                          | Microservices with ACID requirements across services.                                     |
| **Leader Election**       | Ensures only one system component acts as "leader" during failures.                                 | Distributed systems needing a single point of control (e.g., Kafka brokers).               |
| **Immutable Infrastructure** | Treats infrastructure as code; deploys fresh instances post-failure.                              | Cloud-native apps where manual recovery is error-prone.                                   |

---

## **Best Practices**
1. **Trade-offs**:
   - **Durability vs. Performance**: Sync writes (`fsync`) increase latency but reduce data loss risk.
   - **Backup Frequency**: Higher retention = more storage cost but better recovery RPO.

2. **Monitoring**:
   - Track `checkpoint_lag` (PostgreSQL), `replication_offset` (Kafka), or `pod_restart_count` (K8s).
   - Set alerts for `backup_failure` or `replica_lag`.

3. **Disaster Recovery**:
   - Test **RPO** (Recovery Point Objective) and **RTO** (Recovery Time Objective) annually.
   - Use **multi-region replication** for global durability (e.g., S3 Cross-Region Replication).

4. **Avoid Anti-Patterns**:
   - ❌ **Async-only Writes**: Risk data loss on crash.
   - ❌ **No Checkpointing**: Long recovery times post-crash.
   - ❌ **Static Retry Limits**: May fail silently under sustained outages.

---
**References**:
- [PostgreSQL Durability Docs](https://www.postgresql.org/docs/current/runtime-config-wal.html)
- [Kubernetes Durability Guide](https://kubernetes.io/docs/concepts/workloads/pods/disruption/)
- [Circuit Breaker Pattern (Resilience4j)](https://resilience4j.readme.io/docs/circuitbreaker)