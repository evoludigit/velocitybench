---
# **Debugging Durability Issues: A Troubleshooting Guide**

**Objective:** Quickly diagnose and resolve **data durability failures**, such as lost transactions, corrupted logs, or inconsistent state across nodes. Durability ensures that data survives crashes, network partitions, or failures of individual components.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue using these common symptoms:

| **Symptom**                          | **Description**                                                                 | **Action**                          |
|--------------------------------------|-------------------------------------------------------------------------------|-------------------------------------|
| **Data Loss**                        | Transactions or records missing after a restart or failure.                   | Verify logs, backups, and commit completeness. |
| **Inconsistent State**              | Different nodes show different data versions (e.g., primary-lag behind replicas). | Check replication lag, network latency, and conflict resolution. |
| **Crash-Consistent Failure**         | System crashes but recovers with partial/compromised state.                  | Review recovery logs and persistence checks. |
| **High Latency in Writes**           | Slow commit times or timeouts during write operations.                       | Monitor disk I/O, network, and FS sync delays. |
| **Log Corruption**                   | Log files are truncated, truncated, or unrecoverable.                         | Check disk health, logs, and persistence layer. |
| **Replication Lag**                  | Replicas fall behind the primary, risking durability loss.                   | Adjust replication settings, network, or hardware. |
| **Checkpoint Failures**              | System fails to save checkpoints, causing long recovery times.               | Validate disk writes, permissions, and checkpoint logic. |
| **Timeout Errors on Writes**         | Operations hang or return timeouts due to durability waits.                  | Tune `sync` settings, disk buffering, or network timeouts. |

---
## **2. Common Issues and Fixes**

### **Issue 1: **Transactions Not Persisted After Crash**
**Symptom:** System restarts, but the last N transactions are missing.
**Root Cause:** Data was not flushed to disk before the crash (e.g., no `fsync()` on logs).

#### **Fixes:**
1. **Ensure Synchronous Writes:**
   - **For file-based logs (e.g., WAL):**
     ```java
     // Java example: Enabling sync writes
     RandomAccessFile log = new RandomAccessFile("write_ahead.log", "rw");
     FileChannel channel = log.getChannel();
     MappedByteBuffer buf = channel.map(FileChannel.MapMode.READ_WRITE, 0, 64 * 1024);
     // Write data...
     buf.force(true); // Force sync to disk (OS-level fsync)
     ```
   - **For databases (e.g., PostgreSQL):**
     ```sql
     -- Ensure synchronous commits
     ALTER SYSTEM SET synchronous_commit = 'on';
     ```
   - **For distributed systems (e.g., Kafka):**
     ```properties
     # Ensure all follows are durable
     log.flush.interval.messages=1
     log.flush.interval.ms=1000
     unclean.leader.election.enable=false
     ```

2. **Verify Log Segment Rotation:**
   - If logs rotate too aggressively, transactions may be lost. Check:
     ```bash
     # Example: Check log rotation settings in Kafka (server.properties)
     log.segment.bytes=1GB
     ```

---

### **Issue 2: **Replication Lag Causing Data Loss**
**Symptom:** Primary node commits data, but replicas don’t catch up before a failover.
**Root Cause:** Replication is asynchronous, and the primary fails before replicas sync.

#### **Fixes:**
1. **Enforce Synchronous Replication:**
   - **PostgreSQL:**
     ```sql
     ALTER SYSTEM SET synchronous_commit = 'remote_apply';
     ```
   - **Distributed Systems (e.g., etcd):**
     ```yaml
     # etcd config: require synchronous replication
     replication:
       raft:
         election-tick: 1000
         heartbeat-tick: 100
     ```

2. **Tune Replication Timeout:**
   - Increase the timeout to allow more time for sync:
     ```java
     // Kafka example: Adjust replication factor and sync timeout
     Properties props = new Properties();
     props.put("replica.sync.config", "replication.factor=3");
     props.put("offsets.topic.replication.factor", 3);
     ```

---

### **Issue 3: **Checkpoint Failures During Crash**
**Symptom:** Long recovery time or failure to restore state after a crash.
**Root Cause:** Checkpoints are not written correctly (e.g., partial writes).

#### **Fixes:**
1. **Verify Checkpoint Sync:**
   - **Example (Custom System):**
     ```go
     func (s *StateStore) Checkpoint() error {
         if err := s.WriteCheckpoint(); err != nil {
             return err
         }
         return s.FlushToDisk() // Ensure fsync after writing checkpoint
     }
     ```
   - **Databases (e.g., RocksDB):**
     ```cpp
     // Ensure db->Flush() and db->Write(checkpoint_data, true) // true=sync
     ```

2. **Monitor Checkpoint Logs:**
   - Enable debug logs to track checkpoint progress:
     ```bash
     # Example: Enable debug logs in etcd
     --log-level=debug
     ```

---

### **Issue 4: **Log Corruption (Truncated WAL Files)**
**Symptom:** WAL (Write-Ahead Log) files are corrupted or incomplete.
**Root Cause:** Disk failure, improper shutdown, or filesystem issues.

#### **Fixes:**
1. **Validate Log Integrity:**
   - **PostgreSQL:**
     ```bash
     # Check for corruption
     postgres -D /var/lib/postgresql/data -c "SELECT pg_waldump('/path/to/wal')"
     ```
   - **Custom Systems:**
     ```python
     def validate_wal_log(log_path):
         with open(log_path, 'rb') as f:
             log = f.read()
         return len(log) % 4 == 0 and checksum_log(log)  # Example: Validate log structure
     ```

2. **Repair or Recover:**
   - If corruption is detected, restore from backups or use tools like:
     ```bash
     # For PostgreSQL: Use pg_resetwal or manual WAL recovery
     pg_resetwal -f /path/to/data
     ```

---

### **Issue 5: **Disk I/O Bottlenecks**
**Symptom:** High latency in write operations due to slow disks.
**Root Cause:** Disk is overloaded, or `sync` operations are too frequent.

#### **Fixes:**
1. **Optimize Disk Configuration:**
   - Use SSDs for WAL/log files:
     ```bash
     # Mount options for better performance
     /dev/nvme0n1p2  /var/lib/postgresql  ext4  discard,noatime,errors=remount-ro
     ```
   - Reduce `sync` frequency (if acceptable for durability trade-offs):
     ```python
     # Tunable: Reduce sync frequency (but risk minor data loss)
     os.fsync(log_file)  # Only on critical commits
     ```

2. **Monitor Disk Health:**
   - Use `iostat` or `fio` to check disk performance:
     ```bash
     iostat -x 1
     ```

---

## **3. Debugging Tools and Techniques**

### **A. Logging and Metrics**
| **Tool**          | **Purpose**                                                                 | **Example Command**                          |
|--------------------|----------------------------------------------------------------------------|----------------------------------------------|
| **Journalctl**     | Check systemd logs for disk/crash events.                                 | `journalctl -u postgresql --no-pager`        |
| **Prometheus**     | Monitor replication lag, disk latency, and sync delays.                  | `prometheus --config.file=prometheus.yml`   |
| **WAL-G**          | Validate WAL integrity and backups.                                        | `wal-g validate /backups/`                   |
| **Strace**         | Debug filesystem-level operations (e.g., `fsync` calls).                 | `strace -e trace=file -p <PID>`              |
| **Kafka Tools**    | Check log offsets and replication health.                                  | `kafka-consumer-groups --bootstrap-server`   |

### **B. Checklist for Debugging**
1. **Inspect Crash Logs:**
   - Look for `fsync`, `O_SYNC`, or `FDATASYNC` failures in system logs.
   - Example (Linux `dmesg`):
     ```bash
     dmesg | grep -i "error\|sync\|write"
     ```

2. **Replay WAL/Logs:**
   - Use tools like `pg_waldump` (PostgreSQL) or custom log replay scripts to validate transactions.

3. **Network Latency Tests:**
   - For distributed systems:
     ```bash
     ping <replica-node>  # Check RTT
     mtr --report <primary-node>  # Trace route delays
     ```

4. **Disk Health Scan:**
   - Run `smartctl` (for HDDs/SSDs):
     ```bash
     smartctl -a /dev/sdX | grep "Reallocated_Sector_Ct"
     ```

---

## **4. Prevention Strategies**
### **A. Configuration Best Practices**
| **Component**       | **Recommendation**                                                                 |
|---------------------|-----------------------------------------------------------------------------------|
| **Primary Replica** | Use synchronous replication (e.g., `synchronous_commit=remote_apply`).            |
| **Log Segments**    | Rotate logs frequently but ensure no data loss (e.g., WAL flush on every commit). |
| **Checkpoints**     | Schedule checkpoints during low-traffic periods or use incremental snapshots.     |
| **Backups**         | Enable WAL archiving + base backups (e.g., `pg_basebackup`).                      |
| **Disk I/O**        | Use SSDs for WAL, separate disks for data/logs, and enable `discard` for SSDs.     |

### **B. Code-Level Safeguards**
1. **Atomic Writes:**
   - Use temporary files + `rename()` (atomic operation) for log appends:
     ```java
     // Safe log append (Java)
     Path tempLog = Paths.get("wal.tmp");
     Files.write(tempLog, data, StandardOpenOption.CREATE);
     Files.move(tempLog, walPath, StandardCopyOption.REPLACE_EXISTING);
     ```

2. **Double-Write Buffering:**
   - Write to two disks before committing (for high durability):
     ```python
     def double_write(data, disk1, disk2):
         with open(disk1, 'ab') as f1, open(disk2, 'ab') as f2:
             f1.write(data)
             f2.write(data)
             f1.flush(); f2.flush()  # Force sync
     ```

3. **Time-Based Checkpoints:**
   - Take checkpoints every `N` seconds (not just on crashes):
     ```go
     // Example: Periodic checkpoint
     go func() {
         for {
             time.Sleep(60 * time.Second)
             if err := s.Checkpoint(); err != nil {
                 log.Error("Checkpoint failed", "err", err)
             }
         }
     }()
     ```

4. **Graceful Shutdown Handling:**
   - Ensure all writes are flushed before exiting:
     ```python
     import atexit
     atexit.register(lambda: fsync(log_file))
     ```

### **C. Disaster Recovery Plan**
1. **Automated Backups:**
   - Schedule regular WAL + base backups (e.g., `pg_dump` + `pg_basebackup`).
   - Test restores periodically.

2. **Chaos Engineering:**
   - Simulate crashes/failovers to validate durability (e.g., using `kill -9` on nodes).

3. **Monitoring Alerts:**
   - Set up alerts for:
     - Replication lag > `X` seconds.
     - Disk I/O saturation.
     - Checkpoint failures.

---
## **5. Summary of Key Takeaways**
| **Problem**               | **Root Cause**                          | **Quick Fix**                                  | **Prevention**                              |
|---------------------------|----------------------------------------|-----------------------------------------------|---------------------------------------------|
| **Lost Transactions**     | No `fsync` on writes                    | Enable sync writes (`fsync`/`O_SYNC`)          | Use synchronous replication.               |
| **Replication Lag**       | Async replication                     | Switch to sync replication (`synchronous_commit=remote_apply`) | Monitor lag with Prometheus.               |
| **Log Corruption**        | Disk failure or improper shutdown      | Restore from backups; validate logs           | Use WAL archiving + SSDs.                   |
| **Slow Writes**           | Disk bottleneck                        | Upgrade SSDs; reduce `sync` frequency          | Separate disks for data/logs.               |
| **Checkpoint Failures**   | Partial writes                         | Force `fsync` after checkpoints              | Schedule checkpoints during low traffic.    |

---
## **6. Final Checklist Before Production**
1. [ ] Test durability with `kill -9` on primary replicas.
2. [ ] Validate backups by restoring to a staging environment.
3. [ ] Monitor disk health (`smartctl`) and replication lag.
4. [ ] Ensure `fsync` is used for critical operations (WAL, checkpoints).
5. [ ] Document recovery procedures for each failure scenario.

---
**Note:** Durability is a trade-off between performance and safety. Always align settings with your **RPO (Recovery Point Objective)** and **RTO (Recovery Time Objective)**. For example:
- **High durability (e.g., banks):** Use synchronous replication + SSDs.
- **Low latency (e.g., gaming):** Accept minor data loss with async replication + fast SSDs.