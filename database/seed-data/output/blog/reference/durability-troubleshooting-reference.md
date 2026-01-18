---

**[Pattern] Durability Troubleshooting Reference Guide**
*Ensure reliable system resilience with structured diagnostics and recovery procedures.*

---

## **1. Overview**
Durability troubleshooting ensures that systems recover from failures while maintaining data integrity. This guide covers diagnostics for common durability issues (e.g., partial writes, delayed commits, or crashes) and outlines recovery patterns like **checkpointing**, **transaction logging**, and **retry mechanisms**. It assumes familiarity with distributed systems, state machines, and basic error handling.

**Key Focus Areas:**
- Identifying transient vs. permanent failures.
- Debugging consistency gaps in distributed systems.
- Implementing fallback and retry logic.
- Validating recovery correctness.

---

## **2. Key Concepts & Implementation Details**

### **A. Core Definitions**
| Term               | Definition                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Durability**     | Guarantee that committed data persists despite failures.                                       |
| **Transient Failure** | Temporary issue (e.g., network latency).                                                     |
| **Permanent Failure** | Hardware/corruption causing irreversible data loss (e.g., disk failure).                      |
| **Crash Consistency** | System ensures committed state is preserved on restart.                                        |
| **Eventual Consistency** | System converges to a shared state over time (e.g., via propagation delays).                  |

### **B. Failure Modes to Troubleshoot**
| Mode                | Example Scenario                                                                 | Impact                                                                 |
|---------------------|------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| **Partial Writes**  | Network failure mid-write; some nodes receive updates, others don’t.               | Data divergence; inconsistent reads.                                  |
| **Delayed Commits** | Long-running transactions; commit timeout before acknowledgment.                    | Zombie transactions; resource leaks.                                  |
| **Crash on Commit** | Server dies during write; no durability guarantees.                                 | Lost state; requires manual recovery.                                  |
| **Disk Corruption** | Media failure or filesystem errors invalidate committed data.                     | Silent data loss; no immediate errors.                                 |

### **C. Mitigation Patterns**
| Pattern              | Description                                                                         | Use Case                                  |
|----------------------|-------------------------------------------------------------------------------------|-------------------------------------------|
| **Checkpointing**    | Periodically snapshot system state; restore on crash.                               | Stateful services (e.g., databases).     |
| **Write-Ahead Log**  | Log every write before applying; replay on restart.                                | ACID compliance, recovery from crashes.   |
| **Quorum Replication**| Require majority acknowledgment for durability.                                     | Distributed caches (e.g., DynamoDB).    |
| **Idempotent Retries**| Design operations to be safely repeated; retry transient failures.                  | External API calls.                      |
| **Time-Based Recovery**| Automatically retry operations after system recovery (e.g., after network outage). | Microservices with retry queues.         |

**Implementation Notes:**
- **Checkpointing:** Use lightweight snapshots (e.g., Redis RDB, etcd snapshots).
- **WAL:** Append-only log format (e.g., PostgreSQL’s `pg_wal`).
- **Quorum:** Adjust consistency levels (e.g., Cassandra’s `QUORUM` writes).

---

## **3. Schema Reference**
**Durability Troubleshooting Workflow**

| Step               | Action Items                                                                 | Tools/Techniques                          |
|--------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **1. Identify Failure** | Check logs for partial writes, timeouts, or crashes.                          | Log aggregation (ELK, Datadog), metrics (Prometheus). |
| **2. Classify Cause** | Transient (network)? Permanent (disk)?                                       | Tracing (Jaeger), system calls (`strace`).   |
| **3. Validate State** | Compare committed vs. actual state (e.g., checksums, transaction IDs).       | Consensus tools (Raft, Paxos observers).   |
| **4. Apply Recovery** | Restore from checkpoint, replay logs, or reprocess idempotent ops.           | CRC32 checksums, transaction IDs.          |
| **5. Test Resilience** | Simulate failures (e.g., `kill -9` servers) and verify recovery.              | Chaos engineering (Gremlin, Chaos Monkey). |

---

## **4. Query Examples**
### **A. Detecting Partial Writes (SQL)**
```sql
-- Find uncommitted writes in a DB (e.g., PostgreSQL)
SELECT transaction_id, commit_timestamp
FROM pg_stat_activity
WHERE state = 'active' AND commit_timestamp IS NULL;
```
**Output:**
| transaction_id | commit_timestamp |
|----------------|------------------|
| 1234           | NULL             |

---

### **B. Replaying a Write-Ahead Log (Python Pseudocode)**
```python
import json

# Replay log entries after a crash
def replay_log(log_path):
    with open(log_path) as f:
        for entry in f:
            data = json.loads(entry)
            if data["type"] == "WRITE":
                apply_write(data["key"], data["value"])
```

---

### **C. Quorum Check (Cassandra CLI)**
```bash
# Verify write consistency (2/3 quorum required)
nodetool cfstats keyspace table
# Check if writes were acknowledged by majority
nodetool tablestats keyspace table | grep "Read Repair Chance"
```

**Expected Output:**
```
Read Repair Chance: 0.0 (quorum met)
```

---

### **D. Idempotent Retry Logic (Node.js)**
```javascript
async function retryWithBackoff(op, maxRetries = 3, delay = 1000) {
  let retries = 0;
  let lastError;
  while (retries < maxRetries) {
    try {
      await op();
      return; // Success
    } catch (error) {
      lastError = error;
      retries++;
      if (retries < maxRetries) await new Promise(resolve => setTimeout(resolve, delay * retries));
    }
  }
  throw lastError; // Re-throw after max retries
}
```

---

## **5. Diagnostic Commands**
| Tool               | Command                                                                 | Purpose                                  |
|--------------------|-------------------------------------------------------------------------|------------------------------------------|
| **PostgreSQL**     | `pg_isready -U user`                                                    | Check DB connectivity.                  |
| **etcd**           | `etcdctl endpoint health --write-out=table`                              | Verify cluster health.                   |
| **Kubernetes**     | `kubectl get pods --field-selector=status.phase=Pending`               | Identify stalled pods.                  |
| **Linux**          | `dmesg | grep -i error`                                                          | Check kernel crashes.                   |
| **Prometheus**     | `alertmanager --web.listen-address=:9093 --config.file=/etc/alerts.yml` | Monitor durability alerts.               |

---

## **6. Recovery Patterns**
### **A. Checkpoint-Restore**
1. **Trigger:** System crash detected.
2. **Action:**
   ```bash
   # Restore from latest checkpoint (e.g., Zookeeper)
   ./zookeeper-server-start.sh zookeeper.properties --recover
   ```
3. **Validation:**
   ```bash
   # Verify consistency
   zookeeper-shell localhost:2181 ls / | grep "checkpoint"
   ```

### **B. Log Replay**
```python
# Replay a truncated log (e.g., after disk corruption)
def replay_truncated_log(log_path, start_offset):
    with open(log_path, 'rb') as f:
        f.seek(start_offset)
        for entry in f:
            parse_and_apply(entry)
```

### **C. Time-Based Retry (Spring Boot)**
```yaml
# application.properties
spring.cloud.gateway.retry.retry-on-next: true
spring.cloud.gateway.retry.max-attempts: 5
spring.cloud.gateway.retry.backoff.initial-interval: 1s
```

---

## **7. Related Patterns**
| Pattern Name               | Description                                                                 | Reference Link                     |
|----------------------------|-----------------------------------------------------------------------------|------------------------------------|
| **Circuit Breaker**        | Prevent cascading failures by halting retries after a threshold.           | [Resilience4j Docs](https://resilience4j.readme.io/docs) |
| **Sagas**                  | Manage long-running transactions via compensating actions.                | [Event-Driven Microservices](https://microservices.io/) |
| **Exactly-Once Processing**| Ensure no duplicates in event streams (e.g., Kafka).                      | [Kafka Docs](https://kafka.apache.org/documentation/) |
| **Consensus Algorithms**   | Raft/Paxos for distributed state consistency.                            | [Raft Paper](https://raft.github.io/) |
| **Idempotency Keys**       | Unique identifiers to deduplicate duplicate requests.                    | [AWS Idempotency](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-idempotency.html) |

---

## **8. Anti-Patterns**
| **Anti-Pattern**               | **Risk**                                                                 | **Mitigation**                          |
|---------------------------------|--------------------------------------------------------------------------|------------------------------------------|
| **No Checkpointing**           | Full state must be reprocessed on restart.                              | Implement periodic snapshots.            |
| **Hardcoded Retry Delays**      | Exponential backoff ignored; thundering herd.                            | Use jittered retries.                   |
| **Ignoring WAL Corruption**     | Silent data loss; undetected until inconsistency arises.                 | Validate logs with checksums.            |
| **Single-Node Durability**      | No replication; crash = data loss.                                      | Use quorum replication.                  |
| **Manual Recovery Procedures** | Inconsistent execution; human error.                                   | Automate recovery scripts.               |

---

## **9. Tools & Libraries**
| Category          | Tools/Libraries                                                                 |
|-------------------|---------------------------------------------------------------------------------|
| **Logging**       | ELK Stack, Loki, Datadog.                                                        |
| **Monitoring**    | Prometheus, Grafana, New Relic.                                                  |
| **Chaos Engineering** | Gremlin, Chaos Mesh, Chaos Monkey.                                             |
| **Consistency**   | Spanner, CockroachDB (for distributed durability).                              |
| **Serialization** | Protocol Buffers, Avro (for log replay).                                       |
| **Retry**         | Resilience4j, Hystrix, Polly (.NET).                                           |

---

## **10. Example Workflow: Debugging a Partial Write**
### **Scenario**
A microservice fails to process orders due to a network split-brain during a write to a distributed cache (Redis Cluster).

### **Steps**
1. **Check Logs:**
   ```bash
   # Aggregated logs show Redis command timeouts
   grep "CONNECT_TIMEOUT" /var/log/app.log
   ```
   **Output:**
   ```
   ERROR: Redis timeout after 3 retries (order_id=1234)
   ```

2. **Validate State:**
   ```bash
   # Compare primary and replica states
   redis-cli -h primary-node info replication | grep "role:master"
   redis-cli -h replica-node info replication | grep "connected"
   ```
   **Output:**
   - Primary: `role:master, connected_slaves=1`
   - Replica: `connected_slaves:0` (split-brain)

3. **Recovery:**
   ```bash
   # Force replica sync (admins-only!)
   redis-cli -h replica-node replconf forcing-replication
   redis-cli -h replica-node sync
   ```

4. **Prevent Future Issues:**
   - Enable Redis Cluster’s `cluster-require-full-coverage`.
   - Configure client-side retries with jitter:
     ```javascript
     const redis = require("redis");
     const client = redis.createClient({
       retry_strategy: (options) => Math.min(options.attempt * 100, 5000)
     });
     ```

---

## **11. Best Practices**
1. **Design for Failures:**
   - Assume networks and nodes will fail; build retries and fallbacks.
2. **Monitor Durability Metrics:**
   - Track `write_latency`, `retry_count`, and `recovery_time`.
3. **Test Recovery Scenarios:**
   - Simulate crashes with `chaos-mesh`.
4. **Document Recovery Procedures:**
   - Include steps for manual intervention (e.g., `README.RECOVERY.md`).
5. **Use Idempotent Operations:**
   - Ensure retries don’t duplicate side effects (e.g., payment processing).

---
**[End of Guide]** *(Word count: ~950)*