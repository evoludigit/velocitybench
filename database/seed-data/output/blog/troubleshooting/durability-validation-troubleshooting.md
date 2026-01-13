# **Debugging Durability Validation: A Troubleshooting Guide**
*Ensuring Persistence and Reliability in Distributed Systems*

---

## **1. Introduction**
Durability validation ensures that data persists reliably across system failures, network partitions, or node crashes. This guide provides a structured approach to diagnosing and resolving common issues in durability validation patterns, such as **write-ahead logging (WAL), crash recovery, and acknowledgment-based persistence**.

---

## **2. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

| **Category**               | **Symptoms**                                                                 |
|----------------------------|------------------------------------------------------------------------------|
| **Data Loss**              | Missing records in databases/logs after a crash.                             |
| **Inconsistency**          | Replicated data diverges between nodes.                                     |
| **Slow Recovery**          | Extended downtime after a failure (e.g., secondary node sync delay > 1 hour). |
| **Retries & Timeouts**     | Persistence operations repeatedly failing (`5xx` errors, timeouts).           |
| **Logging Issues**         | Missing or corrupted WAL (Write-Ahead Log) entries.                         |
| **Replication Lag**         | Leaders/secondaries fall behind due to unresolved durability checks.         |
| **Client-Reported Failures**| Clients fail to commit transactions (e.g., "Transaction not durable").      |
| **Metrics Spikes**         | Sudden drops in "durability success rate" or "replication lag" in monitoring. |

**Quick Checks:**
- Are crashes correlated with high system load or outages?
- Are logs consistent across all nodes?
- Do persistent storage devices (e.g., disks) show errors?

---

## **3. Common Issues & Fixes**
### **3.1 Issue 1: Data Not Persisted (Transient Loss)**
**Symptoms:**
- Recent writes disappear post-crash.
- `DiskWriteAheadLogs` shows no entries for the affected period.

**Root Cause:**
- **Missing or incomplete WAL flushing** (WAL not synced to disk before `ACK`).
- **Storage layer issues** (e.g., disk full, I/O errors).
- **Race condition** in durability checks (write → crash → persistence fails).

**Fixes:**

#### **Code: Ensure WAL Sync on ACK**
```java
// Before returning ACK, enforce fsync (or equivalent)
public boolean writeAndAcknowledge(byte[] data) {
    // 1. Write to WAL
    wal.append(data);

    // 2. Force disk sync (critical for durability)
    Files.write(walPath, data, StandardOpenOption.APPEND);
    Files.getFileStore(walPath).sync(); // Blocking sync

    // 3. Return ACK only after sync
    return true;
}
```
**Alternative (Async + Verify):**
```python
# Async WAL + background sync
async def write_and_acknowledge(data):
    await wal.append(data)
    await asyncio.create_task(disk_sync(wal_path))
    return True

async def disk_sync(path):
    with open(path, 'ab') as f:
        f.write(data)
        os.fsync(f.fileno())  # Force sync
```

#### **Debugging Steps:**
1. **Check WAL integrity**:
   ```bash
   # For PostgreSQL: pg_isready -U postgres; pg_controldata /var/lib/postgresql/data
   # For custom WAL: `ls -lh /path/to/wal | tail -n 5`
   ```
2. **Inspect system logs** for `ENOSPC` (disk full) or `EIO` (I/O errors).
3. **Enable WAL validation**:
   ```bash
   # Enable debug logging for durability checks
   export DURABILITY_LOG_LEVEL=DEBUG
   ```

---

### **3.2 Issue 2: Replication Lag (Stale Data)**
**Symptoms:**
- Secondary nodes show outdated data.
- Leaders ignore writes from lagging secondaries.

**Root Cause:**
- **Slow disk I/O** on replicas (e.g., HDD vs. SSD).
- **Network congestion** between nodes.
- **Durability checks too strict** (e.g., `sync_writes=true` on slow disks).

**Fixes:**

#### **Code: Optimize Replication Sync**
```go
// Adjust replication sync strategy (e.g., async with batching)
func replicateWrite(data []byte) error {
    // Batch writes and sync periodically (not per-operation)
    batch := append(batch, data)
    if len(batch) >= 1000 {
        err := syncDisk(batch)
        if err != nil {
            return fmt.Errorf("replication sync failed: %v", err)
        }
        batch = nil
    }
    return nil
}

func syncDisk(batch [][]byte) error {
    file, err := os.OpenFile(replLogPath, os.O_APPEND|os.O_WRONLY, 0644)
    if err != nil {
        return err
    }
    defer file.Close()

    // Write all batches at once
    _, err = file.Write(batchBytes(batch))
    if err != nil {
        return err
    }
    return file.Sync() // Sync after batch
}
```

#### **Debugging Steps:**
1. **Measure replication latency**:
   ```bash
   # Check network latency between nodes
   ping <leader-ip> && ping <replica-ip>
   ```
2. **Monitor disk I/O**:
   ```bash
   iostat -x 1  # Check disk saturation
   ```
3. **Adjust sync settings**:
   - If using Kafka: Set `unclean.leader.election.enable=false`.
   - If using Raft: Tune `raft_slow_commit_timeout`.

---

### **3.3 Issue 3: Crash Recovery Fails**
**Symptoms:**
- Node fails to recover after restart (`ERROR: Recovery timeout exceeded`).
- Logs show `Corrupted WAL segment`.

**Root Cause:**
- **Corrupt WAL files** (partial writes, disk errors).
- **Version mismatch** between node and WAL format.
- **Timeout too short** for large WAL replay.

**Fixes:**

#### **Code: Robust Recovery Handler**
```javascript
// Node.js example with WAL replay timeout
async function recover() {
    const wal = await WAL.open('/var/log/wal');
    const replayTimeout = setTimeout(() => {
        console.error('Recovery timeout: WAL replay too slow');
        process.exit(1);
    }, 60000); // 60s timeout

    try {
        await wal.replayAll((entry) => {
            // Apply entry to state
            return applyEntry(entry);
        });
    } catch (err) {
        console.error('Recovery failed:', err);
        throw err;
    } finally {
        clearTimeout(replayTimeout);
    }
}
```

#### **Debugging Steps:**
1. **Validate WAL integrity**:
   ```bash
   # Check WAL for corruption (tools like `wal-check` or custom scripts)
   python3 validate_wal.py /var/log/wal
   ```
2. **Increase recovery timeout**:
   - In Kafka: `offsets.topic.replication.factor=3`.
   - In custom systems: Double the default timeout (e.g., 60s → 120s).
3. **Recreate corrupted WAL** (last resort):
   ```bash
   # For PostgreSQL: pg_resetwal /var/lib/postgresql/data
   # For custom: rm -f /var/log/wal/*
   ```

---

### **3.4 Issue 4: Acknowledgment Timeouts**
**Symptoms:**
- Clients receive `TIMEOUT` for durability ACKs.
- High `5xx` error rates in metrics.

**Root Cause:**
- **Network partition** between client and server.
- **Server overloaded** (CPU/disk bottlenecks).
- **Durability checks too slow** (e.g., `fsync` on slow storage).

**Fixes:**

#### **Code: Non-Blocking Durability with Retries**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def write_with_durability(data):
    # Write to WAL
    wal.append(data)

    # Non-blocking sync (async)
    loop.create_task(disk_sync(data))

    # Return immediately (optimistic ACK)
    return True

async def disk_sync(data):
    with open(wal_path, 'ab') as f:
        f.write(data)
        await loop.run_in_executor(None, os.fsync, f.fileno())
```

#### **Debugging Steps:**
1. **Check network connectivity**:
   ```bash
   tcpdump -i any port 9092  # Kafka example
   ```
2. **Profile sync overhead**:
   ```bash
   # Use perf to check disk sync latency
   perf record -g -- sleep 5; perf report
   ```
3. **Adjust timeout thresholds**:
   - Increase `durability.timeout.ms` in Kafka.
   - Use client-side retries with exponential backoff.

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**          | **Use Case**                                                                 | **Example Command**                          |
|-----------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **WAL Validation Scripts**   | Check for corruption in log segments.                                        | `./validate_wal.sh /var/log/wal`             |
| **Disk I/O Monitors**       | Identify slow or failing storage.                                            | `iostat -x 1`                                |
| **Network Latency Probes**  | Measure replication delays between nodes.                                    | `ping`, `mtr`                                 |
| **Metrics Exporters**       | Track durability success/failure rates.                                      | Prometheus + Grafana                         |
| **Crash Dumps**             | Analyze system state at failure.                                             | `gcore <pid>` (Linux)                        |
| **Replay Testing**          | Simulate WAL replay under load.                                              | `./replay_wal.py --input=/var/log/wal`      |
| **Log Analysis**            | Filter logs for durability errors.                                           | `grep -i "durability\|sync" /var/log/syslog` |

**Advanced Technique: Chaos Engineering**
- **Kill node processes randomly** to test recovery:
  ```bash
  # Auto-kill a process every 5 minutes (for testing)
  while true; do kill -9 $(pgrep -f "durability_service"); sleep 300; done
  ```

---

## **5. Prevention Strategies**
### **5.1 Design-Time Mitigations**
1. **Layered Durability**:
   - Use **two-phase commit (2PC)** for cross-service transactions.
   - Example:
     ```javascript
     async function twoPhaseCommit(tx) {
         // Phase 1: Pre-commit
         await db.prepare(tx);
         await replicatedDB.preCommit(tx);

         // Phase 2: Commit or Abort
         if (rand() > 0.01) { // Simulate failure
             await replicatedDB.commit(tx);
         } else {
             await replicatedDB.abort(tx);
         }
     }
     ```
2. **Quorum-Based Writes**:
   - Require `N/2+1` ACKs for durable writes (e.g., Raft, DynamoDB).
3. **Write-Ahead Log (WAL) Optimization**:
   - Segmented WALs for faster recovery.
   - Compression (e.g., Snappy for WAL entries).

### **5.2 Runtime Monitoring**
- **Metrics to Track**:
  - `durability.ack.latency` (p99, p95, p50).
  - `wal.replay.time` (recovery duration).
  - `replication.lag` (seconds behind leader).
- **Alerting Rules**:
  ```
  ALERT HighDurabilityLatency
    IF durability.ack.latency > 500ms FOR 5m
    ANNOTATION "Failed durability check for 5 minutes"
  ```

### **5.3 Operational Practices**
1. **Regular WAL Validation**:
   ```bash
   # Schedule weekly WAL checks
   0 3 * * 0 /path/to/wal_check.sh
   ```
2. **Disk Redundancy**:
   - Use **RAID-10** for WAL storage.
   - Monitor `smartctl` for disk health:
     ```bash
     smartctl -a /dev/sdX | grep "Reallocated_Sector_Ct"
     ```
3. **Graceful Degradation**:
   - Allow **read-after-write** for non-critical data.
   - Example:
     ```python
     def read_with_durability_check(key):
         data = db.get(key)
         if not db.is_durable(key):
             raise DurabilityNotYetAckError
         return data
     ```

### **5.4 Testing Strategies**
1. **Chaos Testing**:
   - **Kill nodes** during load tests.
   - **Simulate network partitions**:
     ```bash
     tcpdump -i any -w capture.pcap; # Capture traffic
     tc qdisc add dev eth0 handle 1: htb default 11
     tc class add dev eth0 parent 1: classid 1:1 htb rate 10mbit
     ```
2. **WAL Corruption Tests**:
   - Inject partial writes to WAL:
     ```python
     def corrupt_wal_segment():
         with open(wal_path, 'rb') as f:
             data = f.read()
             f.seek(0)
             f.write(data[:len(data)//2])  # Truncate half
     ```

---

## **6. Conclusion**
Durability validation is critical for fault-tolerant systems. Follow this guide to:
1. **Isolate symptoms** using the symptom checklist.
2. **Apply targeted fixes** (e.g., WAL sync, replication tuning).
3. **Leverage tools** like `iostat`, `tcpdump`, and metrics for deep dives.
4. **Prevent issues** with layered durability, monitoring, and chaos testing.

**Final Checklist Before Production:**
- [ ] WAL syncs are blocking and fsync’d.
- [ ] Replication lag < 1s under load.
- [ ] Recovery tests pass in CI.
- [ ] Alerts for durability failures are configured.

By combining **practical debugging** with **proactive prevention**, you can ensure your system remains durable under real-world conditions.