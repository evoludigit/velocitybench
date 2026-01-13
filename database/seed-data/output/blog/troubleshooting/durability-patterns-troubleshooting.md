# **Debugging Durability Patterns: A Troubleshooting Guide**
*(For Distributed Systems, Event Sourcing, and Persistence Concerns)*

Durability Patterns ensure that data remains intact despite failures—whether temporary (crashes, network latency) or permanent (disk corruption, hardware failure). Misconfigurations, race conditions, or incorrect recovery logic can lead to data loss or inconsistencies. This guide focuses on **practical debugging** for common durability issues in distributed systems.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue is related to **durability** (not performance, correctness, or networking). Check for:

### **General Symptoms**
- **[ ]** Data appears lost after **restarts, network partitions, or crashes** (even temporary ones).
- **[ ]** **Idempotent operations** (e.g., retries) produce **inconsistent results**.
- **[ ]** Logs show **" transaction aborted," "timeout," or "retry limit exceeded"** without clear recovery.
- **[ ]** **Eventual consistency** fails—some nodes disagree on state, and manual syncs are needed.
- **[ ]** **Recovery checks** (e.g., `CHECKPOINT`) fail or take unusually long.
- **[ ]** **Consistency proofs** (e.g., linearizability) are violated—e.g., reads return stale data.
- **[ ]** **Durable queues** (Kafka, RabbitMQ) show unprocessed messages after failures.
- **[ ]** **Write-ahead logging (WAL)** files are corrupted or incomplete.
- **[ ]** **Deadlocks** during recovery (e.g., two nodes waiting for each other to commit).
- **[ ]** **Timeouts** during recovery, leading to **partial writes**.

---
## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Data Loss on Crash (No Proper WAL)**
**Symptom:**
- System recovers to a **partial state** (e.g., some transactions lost).
- Logs show **"No active log segment"** or **"Last commit ID missing."**

**Root Cause:**
- Missing **write-ahead logging (WAL)** or **durable storage** before acknowledgment.
- **Race condition** between write and commit.

**Fix:**
Ensure **atomic writes** using WAL (e.g., PostgreSQL’s `fsync`, Kafka’s `min.insync.replicas`).

#### **Example: Durable Queue (Kafka/RabbitMQ)**
```python
# Pseudocode for durable message publishing
def publish_message(topic, message):
    producer = KafkaProducer(enable_idempotence=True)  # Idempotent writes
    producer.send(topic, message)

    # Wait for acknowledgment (ACK_ALL)
    record_metadata = producer.send_and_wait(topic, message)
    if record_metadata.error():
        logger.error(f"Failed to publish: {record_metadata.error()}")
        # Implement retry with exponential backoff
        retry_publish(topic, message)
```

**Key Fixes:**
✅ **Idempotency** (prevent duplicates on retry).
✅ **ACK_ALL** (ensure all replicas acknowledge).
✅ **Short-lived sessions** (avoid long-running transactions).

---

### **Issue 2: Stale Reads (Eventual Consistency Violation)**
**Symptom:**
- A node reads **uncommitted data** or **old state**.
- **Read-after-write** consistency broken (e.g., user sees their update before it’s applied).

**Root Cause:**
- **No strong consistency guarantees** (e.g., eventual consistency model).
- **Reads from unstable storage** (e.g., in-memory cache without sync).
- **No versioning** (e.g., SQLite without `PRAGMA journal_mode=WAL`).

**Fix:**
Use **strong consistency patterns** (e.g., Paxos, Raft) or **versioned reads**.

#### **Example: SQL with Row Versioning**
```sql
-- Start transaction (WAL-enabled)
BEGIN TRANSACTION;
-- Use row versioning to prevent stale reads
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
-- Apply changes (automatically durable)
UPDATE accounts SET balance = balance + 100 WHERE id = 1;
COMMIT;
```

**Key Fixes:**
✅ **`FOR UPDATE` locks** (prevents reads during writes).
✅ **WAL mode** (PostgreSQL/SQLite) for atomic commits.
✅ **Optimistic concurrency control (OCC)** for distributed reads.

---

### **Issue 3: Recovery Failures (Corrupted Checkpoints)**
**Symptom:**
- System crashes on startup with:
  ```
  Error: "Checkpoint file corrupt. Skipping recovery."
  ```
- **Partial state recovery** (e.g., some tables restored, others not).

**Root Cause:**
- **Checkpoint files not atomically written** (race condition).
- **Checkpoint size too large** (slows down recovery).
- **No validation** of checkpoint integrity.

**Fix:**
Implement **atomic checkpoints** with **CRC validation**.

#### **Example: Atomic Checkpointing (Pseudocode)**
```python
def save_checkpoint(state):
    checkpoint_path = "/var/checkpoints/last_state.bin"
    temp_path = checkpoint_path + ".tmp"

    # Serialize state safely
    try:
        with open(temp_path, "wb") as f:
            pickle.dump(state, f)

        # Atomic rename (or filesystem-level fsync)
        os.rename(temp_path, checkpoint_path)
        os.fsync(os.open(checkpoint_path, os.O_RDONLY))  # Force to disk
    except Exception as e:
        logger.error(f"Checkpoint failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
```

**Key Fixes:**
✅ **Atomic filesystem operations** (`rename` + `fsync`).
✅ **Checksum validation** before loading checkpoints.
✅ **Periodic smaller checkpoints** (e.g., every 500ms).

---

### **Issue 4: Deadlocks During Recovery**
**Symptom:**
- Recovery hangs indefinitely with:
  ```
  Deadlock detected: Node A waiting for Node B, Node B waiting for Node A.
  ```
- **Timeout errors** during leader election.

**Root Cause:**
- **Circular dependencies** in recovery (e.g., Node A needs Node B’s state, but Node B is waiting for A).
- **No timeout** for stuck recovery attempts.

**Fix:**
Implement **non-blocking recovery** with **timeouts** and **priority ordering**.

#### **Example: Non-Blocking Recovery (Paxos/Raft)**
```python
def recover_node():
    start_time = time.time()
    timeout = 10  # Seconds

    while time.time() - start_time < timeout:
        try:
            leader = get_leader()  # Network call
            if leader and leader != self.id:
                # Request state transfer with timeout
                state = leader.request_state(self.id, timeout=5)
                if state:
                    return apply_state(state)
                else:
                    logger.warning("Timeout waiting for leader")
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            time.sleep(1)  # Backoff

    raise RecoveryTimeoutError("Could not recover within timeout")
```

**Key Fixes:**
✅ **Strict timeout** for recovery attempts.
✅ **Leader election priority** (avoid circular waits).
✅ **Idempotent recovery** (retries don’t cause duplicates).

---

### **Issue 5: Slow Recovery (Large Logs/State)**
**Symptom:**
- Recovery takes **minutes/hours** (e.g., 1TB of logs).
- **Tail latency spikes** during startup.

**Root Cause:**
- **No log compaction** (unnecessary old data retained).
- **Linear scan of logs** (no indexing).
- **No parallel recovery**.

**Fix:**
- **Compacting logs** (e.g., Kafka’s `log.compaction.interval.ms`).
- **Incremental state snapshots** (like ZooKeeper’s snapshots).
- **Parallel recovery** (e.g., Raft’s `leader.appendEntries`).

#### **Example: Compacting Logs (Kafka)**
```bash
# Enable log compaction (turns key-value logs into a single latest value per key)
kafka-log-cleaner --topic transactions --config value.compact=true
```

**Key Fixes:**
✅ **Log compaction** (reduces size).
✅ **Snapshotting** (store periodic state snapshots).
✅ **Parallel processing** (e.g., Kafka’s `log.flush.interval.messages`).

---

## **3. Debugging Tools & Techniques**
| **Tool/Technique**          | **Purpose**                                                                 | **Example Command/Usage**                          |
|-----------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **WAL Inspection**          | Check if writes were logged before commit.                                  | `fsstat -d /var/log/wal` (PostgreSQL)             |
| **Checkpoint Validation**   | Verify checkpoint integrity (e.g., CRC).                                   | `python validate_checkpoint.py /checkpoints/last` |
| **Network Packet Capture**  | Inspect RPC failures (e.g., gRPC timeouts).                                | `tcpdump -i eth0 port 50051`                     |
| **Distributed Tracing**     | Track transactions across nodes (e.g., Jaeger).                             | `otel-collector --config-file jaeger-config.yaml` |
| **Log Analysis**            | Search for **"aborted," "timeout," "retry"** in logs.                       | `grep -i "aborted" /var/log/app/*.log`            |
| **Memory Dump Analysis**    | Debug deadlocks (e.g., `gcore`, `gdb`).                                    | `gcore <pid>`; `gdb ./myapp core`                |
| **Stress Testing**          | Simulate crashes to test recovery.                                          | `ab -n 100000 -c 1000 http://localhost:8080/api` |
| **SQL Query Plan**          | Check for slow recovery queries.                                            | `EXPLAIN ANALYZE SELECT * FROM huge_table;`       |
| **Disk I/O Monitoring**     | Detect slow `fsync` or large checkpoint writes.                             | `iostat -x 1`                                     |

---

## **4. Prevention Strategies**
| **Strategy**               | **How to Implement**                                                                 | **Example**                                      |
|----------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------|
| **Idempotent Operations**  | Design APIs to be retry-safe (use `idempotency_key`).                              | `POST /payments?idempotency_key=123`             |
| **Atomic WAL**             | Use filesystem-level durability (e.g., `fsync`, `O_DSYNC`).                       | `open(file, O_WRONLY | O_DSYNC)`     |
| **Strong Consistency**     | Enforce linearizability (e.g., Raft, Paxos).                                       | Use `etcd` or `Consul` for leader election.      |
| **Checkpoint Validation**  | Add checksums to checkpoints.                                                      | `sha256sum checkpoint.bin > checksum.txt`       |
| **Timeouts Everywhere**     | Set reasonable timeouts for all external calls.                                   | `go net/http.Timeout: 5s`                        |
| **Log Compaction**         | Reduce log size over time (e.g., Kafka compaction).                              | `log.compaction=time`                           |
| **Parallel Recovery**       | Process log segments concurrently.                                                | `goroutine` for log replay                       |
| **Chaos Testing**          | Simulate failures (e.g., `chaos-mesh`, `Chaos Monkey`).                           | `kill -9 $(pidof myapp)` (randomly)              |
| **Monitoring**             | Track `recovery_time`, `log_size`, `checkpoint_errors`.                           | Prometheus alert: `recovery_time > 60s`         |
| **Backup Validation**      | Test restore from backups periodically.                                           | `restic check`                                   |

---

## **5. Quick Reference Cheat Sheet**
| **Symptom**               | **Likely Cause**               | **Immediate Fix**                          | **Long-Term Fix**                  |
|---------------------------|--------------------------------|-------------------------------------------|------------------------------------|
| Data lost on crash        | Missing WAL                    | Enable `fsync`                              | Add WAL + idempotency checks       |
| Stale reads               | Weak consistency              | Use `FOR UPDATE` or Paxos                 | Implement versioned reads          |
| Corrupted checkpoints     | Non-atomic write               | Use atomic `rename` + `fsync`              | Add CRC validation                 |
| Recovery deadlock         | Circular dependencies          | Add timeouts                               | Non-blocking recovery with priorities |
| Slow recovery             | Large logs                     | Compact logs                               | Incremental snapshots              |
| Duplicate transactions    | No idempotency                 | Add `idempotency_key`                      | Use transactional outbox pattern   |

---

## **Final Checklist Before Deployment**
1. **[ ]** WAL is enabled (`fsync`, `O_DSYNC`, or equivalent).
2. **[ ]** Checkpoints are atomic (no partial writes).
3. **[ ]** Idempotent operations are enforced (retries don’t cause duplicates).
4. **[ ]** Timeouts are set for all RPCs and recovery steps.
5. **[ ]** Logs are compacted/compressed where possible.
6. **[ ]** Recovery is tested under failure scenarios (crash, network split).
7. **[ ]** Monitoring alerts for `recovery_time > threshold`.
8. **[ ]** Backups are validated periodically.

---
**Next Steps:**
- If the issue persists, **reproduce in a staging environment** with logs enabled.
- Use **distributed tracing** (Jaeger, OpenTelemetry) to trace transactions.
- Consider **rewriting critical paths** in a lower-level language (e.g., Rust for WAL).

By following this guide, you should **quickly isolate and fix** durability issues in distributed systems.