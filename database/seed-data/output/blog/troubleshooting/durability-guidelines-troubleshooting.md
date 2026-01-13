# **Debugging Durability Guidelines: A Troubleshooting Guide**
*A focused approach to ensuring data reliability in distributed systems*

---

## **1. Introduction**
Durability is the guarantee that once data is persisted, it remains accessible even in the face of failures (e.g., node crashes, network partitions, or disk corruption). The **Durability Guidelines** pattern ensures that writes are synced to persistent storage (e.g., disk, replicated databases) before acknowledgment to clients. This guide helps diagnose and resolve common durability failures in distributed systems.

---

## **2. Symptom Checklist**
Before diving into fixes, validate these symptoms:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| **Lost Writes**                      | Data written to the system disappears after restarts or failures.               |
| **Inconsistent Reads**               | Clients read stale or missing data despite recent writes.                       |
| **Slow Write Performance**           | Persistence operations take unusually long, delaying client acknowledgments.    |
| **Crash on Write**                   | The system crashes or hangs when writing to persistent storage.                 |
| **Replication Lag**                  | Replicas fall behind the primary, causing delayed durability guarantees.        |
| **Timeout Errors**                   | Clients time out waiting for persistence confirmation (e.g., `WriteTimeout`).   |

*If any symptom matches, skip to the relevant section below.*

---

## **3. Common Issues and Fixes**

### **Issue 1: Writes Not Persisted Before Acknowledgment**
**Symptom**: Data is lost on restart or node failure.
**Root Cause**:
- Missing explicit `fsync()`, `commit()`, or replication confirmation.
- Async writes without a blocking barrier (e.g., using `saveAsync()` without `await`).
- Hardware/OS buffers bypassing persistence (e.g., `O_DIRECT` not used).

#### **Fix: Enforce Synchronous Persistence**
**For Filesystems (Linux):**
```bash
# Disable OS buffering (force synchronous writes)
truncate --size 0 /dev/pmem0  # Example for PMem (if using RAMdisk, avoid this)
```
**Code Fix (Node.js + File System):**
```javascript
// Before: Async write
fs.writeFileSync(filePath, data); // ✅ Force synchronous write

// After: Add fsync for extra durability
fs.writeFileSync(filePath, data);
fs.fsync(fds[0]); // Sync file descriptor
```

**For Databases (PostgreSQL):**
```sql
-- Ensure WAL (Write-Ahead Log) is enabled (default, but check config)
wal_level = replica;
synchronous_commit = on;  -- Critical for durability
```

---

### **Issue 2: Replication Lag Causing Inconsistent Reads**
**Symptom**: Clients read stale data from lagging replicas.
**Root Cause**:
- Replicas cannot keep up with the primary (e.g., network latency, slow disks).
- No health checks for replica lag.
- `async_replica_placement` misconfigured (e.g., cloud providers like AWS RDS).

#### **Fix: Monitor and Adjust Replication**
**Tool: `pg_stat_replication` (PostgreSQL)**
```sql
SELECT pg_stat_replication;
```
*Check `state` (must be "streaming") and `replay_lag`.*

**Code Fix (Node.js + Redis Cluster):**
```javascript
const redis = require("redis");
const client = redis.createClient();

// Set master timeout (adjust based on network RTT)
client.config("set", "replica-priority", "100");
client.config("set", "replica-connect-timeout", "5000");
```

**Prevention**: Use **quorum-based reads** (e.g., DynamoDB’s `ConsistentRead`).

---

### **Issue 3: Slow Write Performance Due to Overhead**
**Symptom**: Writes are slow, causing client timeouts.
**Root Cause**:
- Overuse of `fsync()` or synchronous DB commits.
- Too many small writes (e.g., logging every API call).
- Disk I/O bottlenecks (e.g., HDD vs. SSD).

#### **Fix: Optimize Persistence**
**Option A: Batch Writes**
```python
# Bad: Per-request writes
for request in requests:
    db.write(request)

# Good: Batch writes (e.g., PostgreSQL `COPY` or bulk inserts)
db.bulk_write(requests)
```

**Option B: Use Async with Fallback Sync**
```javascript
// Async write with fallback
fs.writeFileAsync(filePath, data)
  .then(() => fs.fsync(fds[0]))  // Sync on success
  .catch(err => console.error("Retry with fsync:", err));
```

**Hardware Fix**: Migrate to SSDs or use NVMe for critical workloads.

---

### **Issue 4: Crash on Write (OOM or Disk Full)**
**Symptom**: System crashes when writing large data.
**Root Cause**:
- Out-of-memory (OOM) killer kills the process.
- Disk is full (`df -h` shows 100% usage).
- Corrupt storage (e.g., RAID failure).

#### **Fix: Handle Errors Gracefully**
**Code Fix (Node.js):**
```javascript
fs.writeFile(filePath, data, (err) => {
  if (err) {
    if (err.code === 'ENOSPC') {
      // Disk full: log and retry later
      retryLater(err);
    } else {
      throw err;
    }
  }
});
```

**Prevention**:
- **Monitor disk space** (`df -h` + alerts).
- **Set `ulimit -n`** to increase open file descriptors.
- **Use distributed storage** (e.g., S3 + DynamoDB for cold data).

---

### **Issue 5: Timeouts During Replication Sync**
**Symptom**: Clients timeout waiting for replication confirmation.
**Root Cause**:
- Replica sync is slow (e.g., cross-region replication).
- No timeouts configured for replication lag.

#### **Fix: Set Replication Timeouts**
**For Kafka**:
```bash
# Increase replica.fetch.max.bytes and replica.fetch.wait.max.ms
kafka-configs.sh --entity-type topics --entity-name my-topic --alter --add-config "replica.fetch.max.bytes=104857600" --alter --add-config "replica.fetch.wait.max.ms=5000"
```

**For DynamoDB Streams**:
```javascript
// Enable DynamoDB Streams with delayed reads
const dynamodb = new AWS.DynamoDB();
const params = {
  StreamSpecification: {
    StreamEnabled: true,
    StreamViewType: "NEW_IMAGE"
  },
  // Enable checkpointing for lag detection
  CountdownWaitTimeInSeconds: 60
};
```

---

## **4. Debugging Tools and Techniques**

### **A. Log Analysis**
- **Check persistence logs**:
  - PostgreSQL: `pg_log` (check for `SYNC` delays).
  - Redis: `redis-cli debug loglevel verbose`.
  - Filesystem: `dmesg | grep sd` (Linux disk errors).
- **Example (PostgreSQL)**:
  ```sql
  SELECT now() - xact_commit_timestamp AS commit_lag
  FROM pg_stat_activity
  WHERE state = 'active' AND xact_commit_timestamp IS NOT NULL;
  ```

### **B. Network Diagnostics**
- **Test latency**: `ping` + `mtr` (network path analysis).
- **Check replication health**:
  ```bash
  # PostgreSQL replication lag
  SELECT * FROM pg_stat_replication;
  ```

### **C. Storage Inspection**
- **Filesystem checks**:
  ```bash
  fsck /dev/sdX  # Run if disk errors suspected
  ```
- **Disk I/O latency**:
  ```bash
  iostat -x 1  # Check avgqu-sz (queue length)
  ```

### **D. Client-Side Validation**
- **Replay writes** during a failure:
  ```python
  # Simulate crash and replay
  def replay_writes(log_file):
      with open(log_file, 'r') as f:
          for line in f:
              db.write(line)
  ```

---

## **5. Prevention Strategies**

### **A. Design for Durability Upfront**
1. **Use WAL (Write-Ahead Logging)**:
   - PostgreSQL: `wal_level = replica`.
   - Kafka: Enable `log.flush.interval.messages`.
2. **Implement Quorum Reads**:
   - DynamoDB: Use `ConsistentRead` for critical data.
   - Cassandra: Set `read_request_timeout_in_ms` higher than replication factor.
3. **Batch Writes**:
   - Reduce `fsync()` calls (e.g., batch 1000 writes into 1 sync).

### **B. Monitoring and Alerts**
- **Set up alerts for**:
  - Replication lag (`pg_stat_replication` > 5s).
  - Disk space (`df -h` < 20%).
  - Slow writes (`p99 latency > 100ms`).
- **Tools**:
  - Prometheus + Grafana (for metrics).
  - Datadog (for distributed traces).

### **C. Testing Strategies**
1. **Chaos Engineering**:
   - Kill nodes randomly (`kubeclt delete pod -n <namespace> <pod>`).
   - Test disk failures (`dd if=/dev/zero of=/dev/sdX bs=1M count=1024`).
2. **Load Testing**:
   - Use **Locust** or **k6** to simulate high-write loads.
   - Verify durability under `99th percentile` latency.

### **D. Backup and Recovery Plan**
- **Automate backups**:
  - PostgreSQL: `pg_basebackup`.
  - S3: Enable versioning + lifecycle policies.
- **Test restores**:
  ```bash
  # Restore from backup (example)
  pg_restore -d mydb -U postgres /backups/mydb.dump
  ```

---

## **6. Summary of Key Fixes**
| **Issue**                  | **Quick Fix**                                  | **Long-Term Solution**                     |
|----------------------------|-----------------------------------------------|--------------------------------------------|
| Lost writes                | Use `fsync()` + WAL.                          | Design for append-only logs.               |
| Replication lag            | Increase `replica.fetch.timeout`.            | Use multi-AZ deployments.                  |
| Slow writes                | Batch writes + async with sync fallback.      | Upgrade to SSDs/NVMe.                     |
| Crashes on write           | Handle `ENOSPC`/`EIO` errors.                 | Monitor disk space + auto-scale storage.  |
| Timeouts                   | Adjust `replica.lag.timeout`.                 | Use quorum reads.                          |

---

## **7. Final Checklist Before Production**
1. [ ] Durability enabled (`fsync`, WAL, or DB-level sync).
2. [ ] Replication lag < 1s (monitored).
3. [ ] Disk space > 20% (alerted).
4. [ ] Writes batched where possible.
5. [ ] Chaos tests passed (node kills, disk failures).
6. [ ] Backups automated + tested weekly.

---
**Next Steps**:
- If issues persist, check **kernel logs** (`dmesg`) and **OS tuning** (`vm.swappiness=10`).
- For databases, review **query plans** (`EXPLAIN ANALYZE`).