# **Debugging Durability Strategies: A Troubleshooting Guide**

Durability strategies ensure that critical data persists even in failures (e.g., node crashes, network partitions, or storage failures). Common implementations include **write-aheads logs (WAL), persistent queues, checkpointing, and replication**. This guide provides a structured approach to diagnosing and resolving durability-related issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these common symptoms:

| Symptom | Likely Cause |
|---------|-------------|
| **Data loss after crashes** | Missing WAL flushing, improper checkpointing |
| **Delayed writes appearing lost** | Buffering without persistence |
| **Replication lag or inconsistencies** | Network issues, network partition detection failures |
| **Slow recovery after restart** | Large log files, inefficient checkpointing |
| **Failed operations (e.g., `Write` calls hang or return errors)** | Deadlocks in writer threads, disk I/O bottlenecks |
| **Inconsistent cluster state post-failure** | Replication lag, leader election issues |
| **Logs indicating lost WAL segments** | Manual disk deletions, storage corruption |
| **Applications crashing due to "Durability not confirmed"** | Misconfigured durability guarantees (e.g., `SYNCHRONOUS` vs. `ASYNCHRONOUS` writes) |

---

## **2. Common Issues and Fixes**

### **Issue 1: Data Loss After Node Crash (Missing WAL Flushes)**
**Symptoms:**
- Recent transactions disappear on restart.
- Logs show `WAL not flushed before crash`.

**Root Cause:**
- **Asynchronous writes**: Data buffered in memory but not persisted.
- **Improper `fsync()` calls**: Missing sync operations before acknowledging writes.
- **Log rotation not configured**: WAL segments grow indefinitely, increasing recovery time.

**Fixes:**
#### **A. Ensure Synchronous WAL Flushes**
```java
// Good: Synchronous write (durable)
try {
    FileOutputStream fos = new FileOutputStream("wal.log", true);
    fos.write(data);
    fos.getChannel().force(true); // fsync equivalent in Java NIO
    fos.close();
} catch (IOException e) {
    log.error("WAL write failed: " + e.getMessage());
    throw e;
}
```

#### **B. Configure Proper Log Rotation**
Add log rotation (e.g., in `logrotate` or custom script):
```bash
# Rotate WAL every 1GB, keep 3 backups
find /var/log/wal -name "*.log" -size +1G -exec mv {} {}.old \;
mv /var/log/wal/*.old /var/log/wal/archived
```

#### **C. Use `fsync` for Critical Writes**
```python
# Python example with synchronous fsync
with open("wal.log", "ab") as f:
    f.write(data)
    os.fsync(f.fileno())  # Force write to disk
```

---

### **Issue 2: Replication Lag or Inconsistencies**
**Symptoms:**
- Follower nodes lag behind the leader.
- `GET` operations return stale data.
- Replication logs show timeouts or errors.

**Root Cause:**
- **Network partitions**: Followers disconnected during leader changes.
- **High latency**: Replication bandwidth too slow.
- **Misconfigured Raft/Paxos consensus**: Too many election timeouts.

**Fixes:**
#### **A. Check Network Stability**
- **Ping test**: Verify latency between nodes.
  ```bash
  ping <leader-node> -c 10
  ```
- **Packet loss check**:
  ```bash
  mtr <follower-node>  # Advanced network tracing
  ```

#### **B. Adjust Replication Timeout Settings**
For Raft-based systems (e.g., etcd, Consul):
```yaml
# Example etcd config (adjust election_timeout)
raft:
  election_timeout: 10s  # Default 10s (too short? Increase)
  heartbeat_interval: 2s
```

#### **C. Enable Quorum-Based Writes**
Ensure writes are acknowledged by a majority of replicas:
```go
// Pseudocode for quorum writes
func Write(data []byte) error {
    for _, node := range replicas {
        if !node.Acknowledge(data) {
            return ErrQuorumNotMet
        }
    }
    return nil
}
```

---

### **Issue 3: Slow Recovery After Restart**
**Symptoms:**
- Startup takes >5 minutes.
- Logs show `WAL replay is slow`.

**Root Cause:**
- **Large WAL files**: Uncompressed or unrotated logs.
- **Missing checkpoints**: Replaying every log instead of snapshots.

**Fixes:**
#### **A. Implement Checkpointing**
Periodically snapshot the state:
```java
// Pseudocode for checkpointing
public void checkpoint() {
    try {
        FileOutputStream fos = new FileOutputStream("checkpoint.bin");
        ObjectOutputStream oos = new ObjectOutputStream(fos);
        oos.writeObject(currentState);
        oos.close();
    } catch (IOException e) {
        log.error("Checkpoint failed: " + e);
    }
}
```

#### **B. Compress WAL Segments**
Reduce log size with gzip:
```bash
# Compress existing WAL logs
gzip -c wal.log > wal.log.gz
```

#### **C. Parallelize WAL Replay**
Use multiple threads to replay logs:
```python
from concurrent.futures import ThreadPoolExecutor

def replay_wal_in_parallel():
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(replay_segment, wal_segments)
```

---

### **Issue 4: Deadlocks in Writer Threads**
**Symptoms:**
- Writes hang indefinitely.
- Threads stuck in `LOCK_WAIT` (DBs) or `waiting for I/O`.

**Root Cause:**
- **Missing timeouts**: Writers block forever on disk I/O.
- **Improper locking**: Deadlocks between log and state writes.

**Fixes:**
#### **A. Add Timeouts to I/O Operations**
```java
// Java NIO with timeout
try (FileChannel channel = new RandomAccessFile("wal.log", "rw").getChannel()) {
    channel.write(ByteBuffer.wrap(data));
    channel.force(true);
} catch (IOException e) {
    log.error("I/O timeout: " + e);
    throw new RuntimeException("Durability timeout", e);
}
```

#### **B. Use Non-Blocking I/O (e.g., Netty, Java NIO)**
```java
// Example: Non-blocking write with Future
Channel channel = ...;
channel.writeAndFlush(data)
    .addListener(future -> {
        if (future.isSuccess()) {
            channel.force(true); // Sync on success
        } else {
            log.error("Write failed", future.cause());
        }
    });
```

---

## **3. Debugging Tools and Techniques**

| Tool/Technique | Purpose | Example Command |
|----------------|---------|-----------------|
| **`fsync`/`fdisk -T`** | Check disk sync behavior | `fdisk -T /dev/sdb` (check sync delays) |
| **`iostat`/`vmstat`** | Monitor I/O bottlenecks | `iostat -x 1` |
| **`strace`** | Trace system calls | `strace -f -e trace=file java -jar app.jar` |
| **WAL Analyzer Script** | Check log corruption | `python wal\_analyzer.py --file wal.log` |
| **Prometheus + Grafana** | Track replication lag | `prometheus alert on UP{cluster="db"} == 0` |
| **Journalctl (Linux)** | Check systemd service crashes | `journalctl -u my-database.service --no-pager` |
| **Netdata** | Real-time system metrics | `netdata` dashboard |
| **Replay Tool** | Simulate crashes | `./replay\_wal.sh --crash-at 5s` |

---

## **4. Prevention Strategies**

### **A. Configuration Best Practices**
- **WAL Settings**:
  - Use **synchronous writes** (`SYNC=ON` in PostgreSQL, `fsync=forced` in MySQL).
  - Rotate logs **daily/per-size** (e.g., `wal_segment_size=100MB`).
- **Replication**:
  - Set **heartbeat intervals** shorter than election timeouts.
  - Use **compression** for WAN replication (e.g., `raft_compression=true`).

### **B. Automated Health Checks**
- **Liveness Probes**:
  ```yaml
  # Kubernetes liveness probe
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  ```
- **Monitor WAL Backlog**:
  ```bash
  # Script to alert if WAL grows >10GB
  if [ $(du -h wal.log | awk '{print $1}') -gt "10G" ]; then
      slack_alert "WAL over 10GB!"
  fi
  ```

### **C. Disaster Recovery Plan**
- **Backup WALs Offsite**:
  ```bash
  # Sync WALs to S3 every hour
  aws s3 sync /var/log/wal s3://my-db-wals/ --delete
  ```
- **Test Failover**:
  ```bash
  # Simulate node failure
  kill -9 $(pgrep -f "postgres -D /var/lib/postgresql")
  # Verify recovery logs
  journalctl -u postgresql -f
  ```

---

## **5. Summary of Key Actions**
| Issue | Immediate Fix | Long-Term Fix |
|-------|--------------|---------------|
| Data loss | Flush WAL manually (`fsync`) | Enable checkpointing |
| Replication lag | Increase heartbeat timeout | Optimize network (MTU, QoS) |
| Slow recovery | Disable WAL replay (for testing) | Compress logs + parallel replay |
| Deadlocks | Kill hanging threads | Use non-blocking I/O |
| Crashes | Check `journalctl`/`logs` | Add health checks |

---
**Final Note**: Durability is a **balance** between performance and safety. Always benchmark changes (e.g., `fsync` overhead) and test failover scenarios. For distributed systems, prioritize **consensus protocols** (Raft, Paxos) over custom solutions.