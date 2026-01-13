# **Debugging Durability Monitoring: A Troubleshooting Guide**

Durability Monitoring ensures that critical data and transactions persist reliably despite failures. This pattern is essential in systems requiring **ACID compliance** (atomicity, consistency, isolation, durability), such as financial systems, databases, and event-driven architectures.

When durability issues arise, they often manifest as:
- **Lost or corrupted data** after failures (e.g., crashes, network splits).
- **Transaction rollbacks** that shouldn’t happen.
- **Slow recovery times** post-failure.
- **Inconsistent state** between replicas or shards.

This guide provides a structured approach to diagnosing and resolving durability-related problems efficiently.

---

## **🔍 Symptom Checklist**
Before diving into fixes, confirm the issue by checking:

| **Symptom** | **How to Detect** |
|-------------|------------------|
| Data loss after a crash | Compare pre- and post-crash snapshots (e.g., `SELECT COUNT(*)` in DBs) |
| Failed transaction commits | Check logs for `ROLLBACK` events (e.g., PostgreSQL `pg_stat_transaction`) |
| Slow recovery | Monitor recovery time (e.g., `pg_isready -d dbname -U user`) |
| Replica lag | Check replica lag (e.g., `SHOW REPLICA STATUS` in MySQL) |
| Network split-induced inconsistencies | Verify replication lag or split-brain scenarios |
| Persistent storage corruption | Run `fsck` (Linux) or database `VACUUM ANALYZE` |

---
## **🐞 Common Issues & Fixes**

### **1. Transactions Not Committing (Non-Durable Writes)**
**Symptom:**
- Transactions appear committed but data is lost after a crash.

**Root Cause:**
- WAL (Write-Ahead Log) not configured properly.
- `fsync` disabled (critical for durability).

**Fixes:**
#### **For PostgreSQL:**
```sql
-- Enable synchronous commit (default: 'on')
ALTER SYSTEM SET synchronous_commit = 'on';

-- Ensure WAL is properly archived (prevents loss on crash)
ALTER SYSTEM SET wal_level = 'replica';
```
**Check logs:**
```bash
grep "wal archiving" /var/log/postgresql/postgresql-*.log
```

#### **For MySQL:**
```sql
-- Ensure binary logs are enabled
SET GLOBAL log_bin = ON;
SET GLOBAL sync_binlog = 1;  -- Force fsync after each commit
```
**Verify:**
```sql
SHOW VARIABLES LIKE 'binlog_sync%';
```

---

### **2. Replication Lag or Failures**
**Symptom:**
- Replicas fall behind the primary or drop connections.

**Root Causes:**
- High network latency.
- Replica underpowered (CPU/RAM).
- Binary log (binlog) not properly synced.

**Fixes:**
#### **MySQL/MariaDB:**
```sql
-- Check replica status
SHOW SLAVE STATUS;

-- If lag exists, restart replication (if safe)
STOP SLAVE; RESET SLAVE ALL; START SLAVE;
```
**Tune replication:**
```sql
-- Increase binlog retention (prevents log gaps)
SET GLOBAL expire_logs_days = 7;
```

#### **PostgreSQL (Streaming Replica):**
```bash
-- Check replica lag
SELECT * FROM pg_stat_replication;

-- If lag is severe, reset with care
pg_ctl stop -D /path/to/replica_data
rm -rf /path/to/replica_data/pg_xlog/*
pg_ctl start -D /path/to/replica_data
```

---

### **3. Storage Corruption (Physical Layer Issues)**
**Symptom:**
- Database crashes on startup with `could not open file` errors.

**Root Causes:**
- Disk failure or full storage.
- Improper `fsync` or `O_DIRECT` I/O settings.

**Fixes:**
#### **Linux (Filesystem Check):**
```bash
# Shutdown DB gracefully
sudo systemctl stop postgresql

# Run fsck
sudo fsck -fy /dev/sdX  # Replace with actual disk

# Restart DB
sudo systemctl start postgresql
```

#### **Database-Level Fixes (PostgreSQL):**
```sql
-- Check for corrupted tables
SELECT * FROM pg_table_checksum();

-- If corruption found, restore from backup
pg_restore -d dbname /path/to/backup
```

---

### **4. Split-Brain Scenario (Cluster Managed Replication)**
**Symptom:**
- Multiple nodes claim leadership, causing inconsistencies.

**Root Causes:**
- Network partition without proper quorum detection.
- Improper `pglogical` or `pg_auto_failover` config.

**Fixes:**
#### **PostgreSQL (pg_auto_failover):**
```bash
# Check cluster status
pg_ctl cluster status

# Force a leader election (if needed)
pg_autoctl pause  # Temporarily pause auto-failover
pg_autoctl resume
```

#### **General Quorum Check:**
```sql
-- Ensure majority of nodes are reachable
SELECT COUNT(*) FROM pg_stat_replication WHERE application_name != 'autovacuum';
```
**If <50% nodes respond, investigate network issues.**

---

### **5. Slow Recovery After Crash**
**Symptom:**
- Database takes >30s to restart after a crash.

**Root Causes:**
- Large WAL archives.
- Slow storage (HDD vs. SSD).
- Missing `checkpoint_segments` tuning.

**Fixes:**
#### **PostgreSQL Tuning:**
```sql
-- Increase checkpoint frequency (reduce recovery time)
ALTER SYSTEM SET checkpoint_segments = 16;  # Default: 3

-- Enable background checkpoints
ALTER SYSTEM SET checkpoint_timeout = 30min;
```
**Verify recovery:**
```bash
time pg_ctl start -l /var/log/postgresql/startup.log
```

---

## **🛠 Debugging Tools & Techniques**
### **1. Log Analysis**
- **PostgreSQL:**
  ```bash
  grep "ERROR\|PANIC" /var/log/postgresql/postgresql-*.log
  ```
- **MySQL:**
  ```bash
  zcat /var/log/mysql/error.log.* | grep -i "error\|warning"
  ```

### **2. System Monitoring**
- **Disk I/O:**
  ```bash
  iotop -o  # Check disk usage by processes
  ```
- **CPU/RAM:**
  ```bash
  top -o %CPU
  free -h
  ```

### **3. Database-Specific Commands**
| Database | Command |
|----------|---------|
| PostgreSQL | `pg_stat_activity` (check active transactions) |
| MySQL | `SHOW PROCESSLIST` |
| MongoDB | `db.serverStatus().opcounters` |

### **4. Network Diagnostics**
```bash
# Check replication network health
nc -zv replica_host 5432  # PostgreSQL
```
```bash
# Check packet loss
ping replica_host -c 10
```

---

## **⚡ Prevention Strategies**
1. **Enable WAL Archiving (PostgreSQL)**
   ```bash
   # Configure archiving in postgresql.conf
   wal_level = replica
   archive_mode = on
   archive_command = 'test ! -f /path/to/wal/%f && cp %p /path/to/wal/%f'
   ```
2. **Regular Backups**
   ```bash
   # PostgreSQL: Logical backup
   pg_dump -Fc dbname > backup.dump

   # MySQL: Hot backup
   mysqldump --all-databases -u user -p > full_backup.sql
   ```
3. **Monitor Replication Lag**
   ```sql
   -- PostgreSQL: Set up alerts for lag
   CREATE OR REPLACE FUNCTION check_replica_lag()
   RETURNS TRIGGER AS $$
   BEGIN
     IF (SELECT pg_stat_replication.relname FROM pg_stat_replication WHERE state = 'streaming' AND pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.pg_stat_replication.
     -- Add alert logic here
   END;
   $$ LANGUAGE plpgsql;
   ```
4. **Use SSDs for Critical Storage**
   ```bash
   # Check disk type
   sudo hdparm -I /dev/sdX | grep -i "ssd\|sata"
   ```
5. **Test Failure Scenarios (Chaos Engineering)**
   ```bash
   # Kill a replica node (for testing)
   sudo pkill -9 postgres
   ```

---

## **📌 Summary**
| **Issue** | **Quick Fix** | **Prevention** |
|-----------|--------------|---------------|
| Non-durable writes | Check `fsync` & WAL settings | Enable `synchronous_commit` |
| Replication lag | Reset & optimize binlog | Monitor `SHOW SLAVE STATUS` |
| Storage corruption | Run `fsck` | Use `fsync` + SSDs |
| Split-brain | Run `pg_autoctl resume` | Ensure quorum majority |
| Slow recovery | Tune `checkpoint_segments` | Regular backups |

### **Final Checklist Before Going Live**
✅ **WAL/Binlog enabled & archived?**
✅ **Replication lag < 10s?**
✅ **Storage I/O optimized (SSD)?**
✅ **Backup & recovery tested?**
✅ **Network monitoring in place?**

---
**Next Steps:**
- If the issue persists, check **database-specific docs** (e.g., [PostgreSQL WAL Docs](https://www.postgresql.org/docs/current/wal-configuration.html)).
- Consider **manual recovery** if corruption is severe (consult DB vendor guides).

This guide ensures **minimal downtime** by focusing on **practical fixes** rather than theoretical explanations. 🚀