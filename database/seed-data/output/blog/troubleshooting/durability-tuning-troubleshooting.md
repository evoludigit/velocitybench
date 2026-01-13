# **Debugging Durability Tuning: A Troubleshooting Guide**

## **Introduction**
Durability Tuning ensures that writes are reliably persisted to storage, balancing between performance and data integrity. Poor durability settings can lead to data loss, corrupted transaction logs, or degraded system performance. This guide provides a structured approach to diagnosing and resolving durability-related issues in distributed systems (e.g., databases, event stores, or message queues).

---

## **1. Symptom Checklist**
Before diving into debugging, verify if the issue aligns with known durability-related symptoms:

| **Symptom** | **Possible Cause** |
|-------------|-------------------|
| Data loss after system failure (crash, reboot, or outage) | Improper write-ahead log (WAL) durability settings |
| Slow write operations despite sufficient I/O throughput | Overly strict fsync or synchronous commit delays |
| Transaction logs or checkpoints growing uncontrollably | Insufficient log rotation or backoff strategies |
| Inconsistent reads after recovery | Corrupted or incomplete WAL segments |
| High CPU/memory usage during writes | Unoptimized durability checks (e.g., redundant fsync) |
| Timeout errors during high-latency write operations | Network partition or remote durability delays |
| Missing messages in event-sourced systems | Insufficient replay mechanism or durable subscription checks |

---
## **2. Common Issues & Fixes**

### **2.1 Issue: Data Loss After System Crash**
**Root Cause:** The system failed to persist writes before a crash (e.g., no WAL or too aggressive cache eviction).

#### **Fix: Configure Proper Write-Ahead Logging (WAL)**
Ensure all writes are logged before acknowledgment:
```java
// PostgreSQL example: Enable WAL + synchronous commit
ALTER SYSTEM SET synchronous_commit = 'on';
ALTER SYSTEM SET wal_level = 'replica';
```
**For databases with tunable durability (e.g., MongoDB):**
```json
// MongoDB durability settings (in config.yaml)
storage:
  engine: wiredTiger
  wiredTiger:
    engineConfig:
      durability: NORMAL  # or STRICT for no data loss risk
```
**For custom implementations (e.g., Kafka, Redis):**
- Kafka: Ensure `unclean.leader.election.enable=false` and proper `log.flush.interval.messages`.
- Redis: Use `APPENDONLY` mode with `save` settings:
  ```bash
  redis-cli config set appendonly yes
  redis-cli config set save 900 1  # Save every 15 mins or after 1 change
  ```

#### **Debugging Steps:**
1. Check transaction logs for unflushed writes:
   ```bash
   # For PostgreSQL: Look for incomplete WAL segments
   ls /var/lib/postgresql/pg_wal/
   ```
2. Verify recovery logs for missing data:
   ```bash
   # Check PostgreSQL recovery logs
   tail -n 50 /var/log/postgresql/postgresql-*.log
   ```
3. Test with a controlled crash:
   ```bash
   # Simulate a crash (kill PostgreSQL, then restart)
   sudo systemctl stop postgresql
   sudo systemctl start postgresql
   ```

---

### **2.2 Issue: Slow Writes Due to fsync Overhead**
**Root Cause:** Frequent `fsync` calls (e.g., `synchronous_commit=on` in PostgreSQL) block I/O.

#### **Fix: Optimize Durability Settings**
- **Option 1 (Faster Writes, Higher Risk):** Reduce fsync frequency:
  ```sql
  -- PostgreSQL: Allow some data loss on crash (use with caution!)
  ALTER SYSTEM SET synchronous_commit = 'remote_apply';
  ```
- **Option 2 (Balanced):** Use `fsync` only for critical segments:
  ```python
  # Python (SQLAlchemy): Disable fsync unless critical
  engine = create_engine("postgresql://user:pass@host/db",
                         connect_args={"fsync": False})  # Disable fsync
  ```
- **Option 3 (Async fsync):** Use OS-level helpers:
  ```bash
  # Adjust Linux `dirty_ratio`/`ratio` to reduce fsync pressure
  echo 90 > /proc/sys/vm/dirty_ratio
  ```

#### **Debugging Steps:**
1. Monitor fsync latency:
   ```bash
   # Check PostgreSQL pg_stat_activity for slow fsync
   SELECT pid, now() - query_start AS duration FROM pg_stat_activity;
   ```
2. Test with `strace` to identify I/O bottlenecks:
   ```bash
   strace -e trace=file -p <postgresql_pid>
   ```
3. Use `iostat` to check disk saturation:
   ```bash
   iostat -x 1
   ```

---

### **2.3 Issue: Unbounded Log Growth**
**Root Cause:** Missing log rotation or checkpointing.

#### **Fix: Implement Log Rotation & Checkpointing**
- **PostgreSQL:** Adjust `checkpoint_timeout` and `checkpoint_completion_target`:
  ```sql
  ALTER SYSTEM SET checkpoint_timeout = '15min';
  ALTER SYSTEM SET checkpoint_completion_target = 0.9;  # 90% done by timeout
  ```
- **Custom Systems:** Add log truncation on recovery:
  ```go
  // Pseudo-code for durable log cleanup
  func CleanupOldLogs(logDir string) error {
      files, err := ioutil.ReadDir(logDir)
      if err != nil { return err }
      for _, f := range files {
          if time.Since(f.ModTime()) > 24*time.Hour { // Keep logs <24h
              os.RemoveAll(filepath.Join(logDir, f.Name()))
          }
      }
      return nil
  }
  ```

#### **Debugging Steps:**
1. Check log file sizes:
   ```bash
   du -sh /var/lib/postgresql/pg_wal/
   ```
2. Review PostgreSQL `pg_stat_archiver` for archiving issues:
   ```sql
   SELECT * FROM pg_stat_archiver;
   ```
3. Simulate a crash and verify log recovery:
   ```bash
   # Force a checkpoint (PostgreSQL)
   SELECT pg_checkpoint('fast');
   ```

---

### **2.4 Issue: Inconsistent Reads Post-Recovery**
**Root Cause:** Corrupted WAL or incomplete recovery.

#### **Fix: Validate & Recover WAL**
1. **PostgreSQL:** Run `pg_resetwal` (if logs are severely corrupted):
   ```bash
   sudo -u postgres pg_resetwal -f
   ```
2. **Custom Logs:** Implement checksum validation:
   ```python
   def verify_wal_segment(segment: bytes) -> bool:
       expected_checksum = crc32(segment[:-4])
       return expected_checksum == int.from_bytes(segment[-4:], 'big')
   ```

#### **Debugging Steps:**
1. Check for WAL corruption:
   ```bash
   # PostgreSQL: Look for truncated files
   find /var/lib/postgresql/pg_wal/ -size 0
   ```
2. Test recovery with `postgres -D /path/to/data --single -c config_file`:
   ```bash
   postgres -D /tmp/test_db -c /etc/postgresql/test.conf --single
   ```
3. Enable `log_recovery_min_segments` to catch issues early:
   ```sql
   ALTER SYSTEM SET log_recovery_min_segments = 5;  # Log if <5 segments remain
   ```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                          | **Example Command**                  |
|------------------------|---------------------------------------|--------------------------------------|
| `pgbadger`             | PostgreSQL log analysis                | `pgbadger /var/log/postgresql/*.log` |
| `strace`               | I/O blocking investigation            | `strace -e trace=file -p <pid>`      |
| `iostat`/`vmstat`      | Disk/CPU/memory pressure               | `iostat -x 1`                        |
| `sysstat`              | Long-term system metrics              | `sar -d 1`                           |
| `WAL-G` (PostgreSQL)   | WAL backup/validation                 | `wal-g backup postgres://user@host`  |
| Custom WAL validators  | Verify log integrity                   | `./validate_wal.sh /var/log/wal/`    |
| `perf`                 | Low-level I/O latency analysis         | `perf record -e syscalls:sys_enter_write` |

**Advanced Technique: Stress Testing Durability**
```bash
# Simulate disk failures (use with caution!)
sudo dd if=/dev/zero of=/dev/sdX bs=1M count=1000
# Recover and verify data consistency
```

---

## **4. Prevention Strategies**

### **4.1 Configuration Best Practices**
| **System**       | **Durability Setting**                     | **Recommendation**                          |
|------------------|--------------------------------------------|---------------------------------------------|
| PostgreSQL       | `synchronous_commit`                       | `on` (for critical data), `remote_apply`  |
| MongoDB          | `durability`                              | `STRICT` (production), `NORMAL` (dev)       |
| Redis            | `appendonly` + `save`                     | `yes` + aggressive save intervals          |
| Kafka            | `log.flush.interval.messages`             | `10000` (balance speed/durability)         |
| Custom Systems   | Log flush policy                          | Flush after N writes or X ms delay          |

### **4.2 Monitoring**
- **Metrics to Track:**
  - `pg_stat_activity` (PostgreSQL): `transaction_count`, `blocked_pids`
  - `fsync` latency (`strace` or `perf`)
  - WAL size (`pg_stat_database`)
  - Disk I/O (`iostat`)

- **Alerts:**
  - Trigger on `WAL size > 10GB`
  - Warn if `fsync latency > 100ms` (adjustable)

### **4.3 Recovery Playbooks**
1. **Post-Crash:**
   - Verify `postgres` log for errors:
     ```bash
     grep "PANIC" /var/log/postgresql/postgresql-*.log
     ```
   - Run `pg_checksums` (PostgreSQL 12+):
     ```sql
     SELECT * FROM pg_checksums();
     ```
2. **Data Corruption:**
   - Use `pg_dump` + `pg_restore` for clean recovery:
     ```bash
     pg_dump -Fc db_name | gzip > backup.dump.gz
     gunzip < backup.dump.gz | pg_restore -d db_name
     ```
3. **Performance Degradation:**
   - Scale out replicas or increase `shared_buffers`:
     ```sql
     ALTER SYSTEM SET shared_buffers = '8GB';
     ```

### **4.4 Testing**
- **Chaos Engineering:**
  - Kill PostgreSQL master and verify failover:
    ```bash
    sudo systemctl stop postgresql
    sudo systemctl start postgresql
    ```
  - Test disk failures with `fstrim` or `dd` (see above).
- **Automated Checks:**
  ```bash
  # Verify WAL integrity (custom script)
  ./check_wal_integrity.sh || (echo "WAL corruption detected!" && alert)
  ```

---

## **5. Summary Checklist for Debugging**
1. **Symptom Identification:** Match symptoms to durability issues (e.g., data loss → WAL misconfiguration).
2. **Configuration Review:** Check `synchronous_commit`, `fsync`, and log settings.
3. **Log Analysis:** Examine WAL, crash logs, and recovery logs.
4. **Performance Profiling:** Use `strace`, `perf`, or `iostat` to find bottlenecks.
5. **Recovery Test:** Simulate crashes and verify consistency.
6. **Prevention:** Adjust settings, add monitoring, and document recovery steps.

---
## **Final Notes**
- **Trade-offs:** Durability vs. performance is inevitable. Tune based on SLAs (e.g., `synchronous_commit=remote_apply` for low-latency apps).
- **Idempotency:** Design systems to handle duplicate writes (e.g., Kafka + idempotent producers).
- **Documentation:** Maintain a runbook for durability failures (e.g., "If WAL corruption is detected, run `pg_resetwal -f` before recovery").