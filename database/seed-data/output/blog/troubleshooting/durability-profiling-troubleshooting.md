# **Debugging Durability Profiling: A Troubleshooting Guide**
**Author:** Senior Backend Engineer
**Focus:** Quick Resolution for Production & High-Latency Issues

---

## **1. Introduction**
**Durability Profiling** ensures that critical writes (e.g., transaction logs, persistent state, or event sourcing) are consistently retained across failures. Poor durability can lead to:
- Data loss during crashes
- Inconsistent state recovery
- Slow recovery times after outages

This guide assumes familiarity with **durability patterns** (e.g., WAL, SSTable, Two-Phase Commit) and a distributed system environment (e.g., databases, Kafka, distributed caches).

---

## **2. Symptom Checklist**
Before diving into debugging, verify these symptoms:

| **Symptom**                          | **Root Cause Hypothesis**                     | **Action to Take**                          |
|---------------------------------------|-----------------------------------------------|----------------------------------------------|
| Data missing after server restart     | Log not flushed to disk                       | Check `fsync`/`O_DIRECT` for pending writes   |
| Slow recovery after outage            | SSTable index rebuilds                       | Monitor compaction metrics                   |
| Inconsistent reads after failure      | Uncommitted WAL entries                     | Audit `prepareCommit` vs. `commit` timings   |
| High latency on critical writes       | Disk I/O bottlenecks                         | Profile `sync` system calls                  |
| Kafka producer retries without success | Broker crash during `ISR` rebalancing        | Verify `unclean.leader.election.enable`      |

**Quick Check:** Use `dmesg` (Linux) to confirm disk I/O errors or `vmstat` to detect memory pressure.

---

## **3. Common Issues and Fixes**
### **3.1 Issue: Unflushed WAL Logs on Crash**
**Symptom:** Data lost on server restart due to unpersisted writes.
**Fix:**
- **For Log-Based Systems (e.g., Kafka, MySQL Binlog):**
  Ensure `fsync` is enabled and WAL is not in-memory:
  ```java
  // Kafka Producer Config
  props.put("acks", "all");  // Wait for leader + ISR sync
  props.put("delivery.timeout.ms", 120000); // Retry if disk delay

  // MySQL (InnoDB)
  SET innodb_flush_log_at_trx_commit = 2; // Flush on crash
  SET innodb_flush_method = O_DIRECT;    // Avoid OS buffer
  ```
  **Debug:** Check `sysctl fsync` latency spikes with `perf stat`.

- **For Custom Implementations:**
  Add a `sync()` call post-write (e.g., in Redis):
  ```c
  // After write():
  if (store_type == DURABLE) {
      fsync(fd);  // Force write to disk
  }
  ```

**Code Example (Go – Durable Writes with Sync):**
```go
func WriteToDurableStore(key, value string) error {
    if err := store.Write(key, value); err != nil {
        return err
    }
    if profile.Durability == FULL {
        if err := os.Fsync(int(store.Fd)); err != nil {
            return fmt.Errorf("fsync failed: %v", err)
        }
    }
    return nil
}
```

---

### **3.2 Issue: Slow Compaction in Key-Value Stores**
**Symptom:** High latency during `sstablecompaction` (e.g., RocksDB, Cassandra).
**Fix:**
- **Tune Compaction Settings:** Adjust `max_background_compactions` and `compaction_threshold`:
  ```properties
  # RocksDB Options
  db->Options().compaction_filter_factory.reset(
      new NewCompactionFilter("filter.txt")
  );
  db->Options().max_background_compactions = 4;  // Limit CPU threads
  ```
- **Offload to Dedicated Threads:**
  ```python
  # Cassandra: Configure external compaction tool
  nodetool compactionstats
  nodetool repair -pr
  ```

**Debug:**
- Monitor `rocksdb.dbstats` for stalled compactions.
- Use `strace -f compactor` to check disk I/O contention.

---

### **3.3 Issue: Two-Phase Commit Deadlocks**
**Symptom:** Long `prepareCommit` stalls due to timeouts.
**Fix:**
- **Optimize `prepareCommit` Logic:**
  ```java
  // Timeout after 5s if no ACK from all participants
  TPCProtocol.prepareCommit(
      request,
      clientTimeout -> clientTimeout.set(5, TimeUnit.SECONDS)
  );

  // Add retry logic for transient failures
  while (attempts < 3) {
      try {
          commit();
          break;
      } catch (TimeoutException e) {
          attempts++;
          Thread.sleep(1000);
      }
  }
  ```
- **Use Saga Pattern for Long-Running Workflows** (if TPC is impractical).

**Debug:**
- Check `XAResource.prepare()` logs for hangs.
- Use `jstack <pid>` to find blocked threads.

---

### **3.4 Issue: Disk I/O Bottlenecks**
**Symptom:** High `iops` but slow writes (e.g., `iotop` shows 100% disk usage).
**Fix:**
- **Check Disk Type:**
  - **HDD:** Use `noatime` mount option:
    ```bash
    mount -o noatime /dev/sdX /mount/point
    ```
  - **SSD:** Enable `O_DIRECT` for bypassing page cache:
    ```c
    off_t offset = /* ... */;
    write(fd, data, size, offset, O_DIRECT);
    ```
- **Profile I/O with `iotop`:**
  ```bash
  iotop -o  # Sort by latency
  ```

**Debug:**
- Use `vmstat 1` to check `bi`/`bo` (I/O operations).
- Compare `dd if=/dev/sdX bs=1M count=100` latency on test and prod disks.

---

## **4. Debugging Tools and Techniques**
### **4.1 Operational Tools**
| **Tool**               | **Use Case**                                  | **Example Command**                     |
|-------------------------|-----------------------------------------------|-----------------------------------------|
| `dmesg`                | Check disk errors                             | `dmesg -T \| grep -i error`             |
| `vmstat`, `iostat`     | Disk/memory pressure                          | `iostat -x 1`                           |
| `strace`               | Track `fsync`/`open` calls                    | `strace -f -o trace.log program`        |
| `perf`                 | Latency breakdown (e.g., `sync` system calls) | `perf record -g -e syscalls:sys_enter` |
| `tcpdump`              | Network latency between nodes                  | `tcpdump -i eth0 port 9092`             |
| `systemtap` (stap)     | Kernel-level profiling                        | `stap -p <pid> -e 'probe syscalls.sync:return { printf("%d", ret); }'` |

### **4.2 Log Analysis**
- **Key Log Patterns:**
  - **"WAL truncation failed"**: Check disk space (`df -h`).
  - **"Compaction stuck"**: Monitor `compaction_pending` in Prometheus.
  - **"XA resource timeout"**: Review `XAResource.prepare()` calls.

**Example Prometheus Alert:**
```yaml
- alert: HighCompactionLatency
  expr: rate(rocksdb_compaction_time_seconds_count[5m]) > 10
  for: 5m
  labels:
    severity: warning
```

---

## **5. Prevention Strategies**
### **5.1 Configuration Best Practices**
| **Setting**               | **Recommended Value**          | **Justification**                      |
|---------------------------|--------------------------------|----------------------------------------|
| `innodb_flush_log_at_trx_commit` | `2` (MySQL)                  | Balance durability vs. latency        |
| `rocksdb.write_buffer_size` | `128MB`                       | Avoid too-frequent flushes            |
| `kafka.log.flush.interval.messages` | `10000` | Reduce `fsync` overhead               |
| `cassandra.compaction_throughput_mb_per_sec` | `64` | Limit CPU usage during compaction     |

### **5.2 Architectural Safeguards**
1. **Write-Ahead Logging (WAL):**
   - Mandate `fsync` on critical paths (e.g., Kafka’s `unclean.leader.election.enable=false`).
2. **Periodic Snapshots:**
   - Schedule `cassandra-sstabletools` snapshots (e.g., nightly).
3. **Multi-Region Replication:**
   - Use `kafka-mirror-maker` for cross-DC durability.
4. **Chaos Engineering:**
   - Simulate disk failures with **Gremlin** or **Chaos Mesh**:
     ```yaml
     # Chaos Mesh Disk Failure Test
     podFailure:
       mode: one
       selector:
         labelSelector:
           app: kafka-broker
       duration: "1m"
       action: terminate
     ```

### **5.3 Monitoring**
- **Critical Metrics:**
  - `wal_bytes_written` (slow growth → I/O issues)
  - `compaction_queue_size` (growing → bottleneck)
  - `xalog_replay_time` (MySQL) (high → recovery lag)
- **Dashboards:**
  - **Prometheus + Grafana:** Track `write_latency` percentiles.
  - **DataDog:** Alert on `fsync` time > 100ms.

---

## **6. Step-by-Step Troubleshooting Flowchart**
```
[Symptom] →
  ↓
Is data lost on restart? →
  ↓ Yes → Check WAL fsync (Section 3.1)
  ↓ No →
    ↓ Slow recovery? → Audit compaction (Section 3.2)
    ↓ Deadlocks? → Examine TPC calls (Section 3.3)
    ↓ High I/O? → Profile with iostat (Section 4.1)
```

---
## **7. References**
- **RocksDB Durability Guide**: [https://rocksdb.org/blog/2020/12/01/durability.html](https://rocksdb.org/blog/2020/12/01/durability.html)
- **Kafka Durability Settings**: [https://kafka.apache.org/documentation/#durability_configs](https://kafka.apache.org/documentation/#durability_configs)
- **MySQL InnoDB Tuning**: [https://dev.mysql.com/doc/refman/8.0/en/innodb-tuning.html](https://dev.mysql.com/doc/refman/8.0/en/innodb-tuning.html)

---
**Final Tip:** Always test durability changes in a **staged environment** with `kill -9` to simulate crashes. Use `journalctl -f` (systemd) or `journalctl -u <service>` to debug post-crash behavior.