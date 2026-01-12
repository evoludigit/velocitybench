# **Debugging Backup & Disaster Recovery: A Troubleshooting Guide**

## **Introduction**
Data loss or corruption can cripple an application, leading to downtime, regulatory fines, and loss of customer trust. The **Backup & Disaster Recovery (BDR)** pattern ensures data integrity by implementing automated backups, failover mechanisms, and restore procedures. This guide provides a structured approach to diagnosing BDR failures and restoring systems quickly.

---

## **1. Symptom Checklist**
Before troubleshooting, confirm which failures have occurred:

| **Symptom**                     | **Description** |
|---------------------------------|----------------|
| **Disk/Storage Failure**        | Hard drive fails, RAID fails, or storage array becomes unreachable. |
| **Accidental Data Deletion**    | A `DELETE` query, script, or admin error wipes critical data. |
| **Ransomware Encryption**       | Database files or VMs are encrypted; backups may also be corrupt. |
| **Application-Level Corruption**| A bug or logic error causes data inconsistencies (e.g., duplicate records). |
| **Entire Data Center Outage**   | Primary and replica regions fail; no way to restore. |
| **Backup Fails**                | Backup jobs fail silently; retention policies not met. |
| **Slow/Failed Restores**        | Restore operations take too long or fail mid-process. |
| **Version Mismatch**            | Restored data doesn’t match schema or application version. |

---

## **2. Common Issues & Fixes**

### **2.1 Hard Drive / Storage Failure**
**Symptom:** Database unreadable; OS or storage controller fails.
**Root Causes:**
- Physical disk failure (SATA/SSD/HDD)
- RAID controller failure
- Storage network (iSCSI, FC) partition failure

#### **Quick Fixes:**
1. **Replace the Failed Disk (RAID 5/6):**
   ```bash
   # Check RAID status (Linux)
   sudo cat /proc/mdstat
   ```
   - If degraded, add a new disk:
     ```bash
     sudo mdadm --add /dev/mdX /dev/sdX
     ```
   - Rebuild array:
     ```bash
     sudo mdadm --manage /dev/mdX --scan
     ```

2. **Restore from Backup:**
   - If using **logical backups (PGDump, mysqldump)**, restore to a new server.
   - If using **physical backups (VM snapshots)**, boot from the snapshot.
   - If using **cloud storage (S3, GCS)**, sync back to a new EC2 instance.

3. **Check Storage Network**
   - For **iSCSI/NVMe-oF**, verify LUN connectivity:
     ```bash
     sudo multipath -v2 -l  # Check paths
     sudo multipath -r      # Re-map if lost
     ```

---

### **2.2 Accidental Data Deletion**
**Symptom:** Critical records disappear; no recent backups.
**Root Causes:**
- Miswritten `DROP TABLE` or `DELETE FROM`
- Scheduled job ran incorrectly
- Admin with full access made an error

#### **Quick Fixes:**
1. **Check Transaction Logs (PostgreSQL/MySQL):**
   ```sql
   -- PostgreSQL: Find recent transactions
   SELECT * FROM pg_stat_activity WHERE query LIKE '%DELETE%';
   ```
   ```sql
   -- MySQL: Check binary logs
   SHOW BINLOG EVENTS IN 'mysql-bin.000001';
   ```

2. **Restore from Backup:**
   - If using **transactional backups (WAL archiving)**, restore the latest backup + logs:
     ```bash
     # PostgreSQL: Restore with WAL replay
     pg_restore -d new_db -C -Fc backup.dump
     ```
   - If using **full database dumps**, reapply from scratch.

3. **Use Change Data Capture (CDC) Tools:**
   - **Debezium** (Kafka-based CDC) can replay deleted records.
   - **Aiven’s Flight Recorder** (for PostgreSQL) can audit deletions.

---

### **2.3 Ransomware Encryption**
**Symptom:** Database files (`*.db`, `*.mdf`, `*.ldf`) are encrypted; backups also corrupted.
**Root Causes:**
- Malware infected database server
- Unpatched OS/database vulnerabilities

#### **Quick Fixes:**
1. **Isolate the Infected System:**
   ```bash
   # Linux: Check for suspicious processes
   ps aux | grep -i "ransomware"
   ```
   - **Never pay ransom**—restore from known-clean backups.

2. **Restore from Offline/Isolated Backups:**
   - **Cloud backups (AWS S3, Backblaze B2)** are less likely to be infected.
   - **Air-gapped backups** (physical tapes, external drives) are safest.

3. **Prevent Future Attacks:**
   - Enable **database-level encryption** (TDE for SQL Server, PGcrypto for PostgreSQL).
   - Use **WORM (Write Once, Read Many) storage** for backups.

---

### **2.4 Application-Level Data Corruption**
**Symptom:** Data inconsistencies (duplicates, invalid states) despite intact storage.
**Root Causes:**
- Buggy application logic (race conditions, missing transactions)
- Improper schema changes
- Manually edited database files (`.mdf`, `.ibd`)

#### **Quick Fixes:**
1. **Rollback to Last Known Good State:**
   ```bash
   # PostgreSQL: Rewind cluster (if using WAL archiving)
   pg_rewind --verbose /path/to/old /path/to/new
   ```

2. **Use Database-Level Integrity Checks:**
   ```sql
   -- PostgreSQL: Check for orphaned rows
   SELECT * FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
   ```
   ```sql
   -- MySQL: Repair tables (if possible)
   mysqlcheck -r --all-databases
   ```

3. **Re-initialize Corrupt Tables:**
   ```sql
   -- Example: Drop and recreate a corrupted table
   DROP TABLE IF EXISTS corrupt_table;
   CREATE TABLE corrupt_table AS SELECT * FROM backup_table WHERE 1=0;
   ```

---

### **2.5 Entire Data Center Outage**
**Symptom:** Primary & replica regions fail; no way to restore.
**Root Causes:**
- Server room fire
- Power outage with no DR site
- Cloud provider outage (e.g., AWS AZ failure)

#### **Quick Fixes:**
1. **Failover to Disaster Recovery Site:**
   - **Cloud (AWS/GCP):** Use **Multi-AZ deployments** or **cross-region replication**.
   - **On-Prem:** Ensure a **hot standby** server is pre-configured.

2. **Restore from Cross-Region Backups:**
   ```bash
   # AWS: Sync S3 backups to another region
   aws s3 sync s3://bucket-us-east-1/ s3://bucket-us-west-2/ --region us-west-2
   ```

3. **Use Immutable Backups:**
   - **AWS S3 Object Lock** / **GCP Object Versioning** prevent accidental deletion.

---

## **3. Debugging Tools & Techniques**

### **3.1 Backup Verification**
- **PostgreSQL:** `pg_dump` + `pg_restore` with `--verify`
- **MySQL:** `--check-sum` flag in `mysqldump`
- **Cloud Backups:** Validate S3 checksums:
  ```bash
  aws s3 cp s3://bucket/path dump.sql --checksum
  ```

### **3.2 Point-in-Time Recovery (PITR)**
- **PostgreSQL:** Use `pg_basebackup --wal-method=stream`
- **MySQL:** Binary log positioning:
  ```sql
  SHOW MASTER STATUS;
  RESET MASTER;
  ```

### **3.3 Log Analysis**
- **Database Logs:**
  ```bash
  # PostgreSQL: Check recent errors
  grep "ERROR" /var/log/postgresql/postgresql*.log
  ```
- **Backup Logs:**
  ```bash
  # AWS Backup: Check CloudTrail for failed jobs
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=RunResourceBackupJob
  ```

### **3.4 Network & Storage Diagnostics**
- **iSCSI/Fibre Channel:**
  ```bash
  # Linux: Check multipath status
  multipath -ll
  ```
- **Cloud Storage Latency:**
  ```bash
  # AWS CLI: Measure S3 latency
  aws s3api get-object --bucket bucket --key testfile --sse aws:kms --output text | time wc -c
  ```

---

## **4. Prevention Strategies**

### **4.1 Backup Best Practices**
| **Strategy**          | **Implementation** |
|-----------------------|--------------------|
| **3-2-1 Rule**        | 3 copies, 2 media types, 1 offsite |
| **Incremental Backups** | Only back up changed data (PostgreSQL `pg_basebackup --format=t`) |
| **Immutable Backups** | Use **AWS S3 Versioning** or **WORM storage** |
| **Automated Testing** | Regularly restore backups to test viability |

### **4.2 Disaster Recovery Planning**
- **RPO (Recovery Point Objective):** Max acceptable data loss (e.g., 15 min for DB).
- **RTO (Recovery Time Objective):** Max downtime (e.g., 1 hour).
- **DR Drills:** Simulate failures (e.g., `kill -9` a primary node).

### **4.3 Monitoring & Alerts**
- **Database Alerts:**
  ```yaml
  # Prometheus Alert (PostgreSQL)
  - alert: HighBackupLatency
    expr: pg_backup_restore_time_seconds > 3600
    for: 5m
  ```
- **Backup Job Failures:**
  ```bash
  # Check AWS Backup job status
  aws backup get-job-for-started --job-id JOB123 --region us-east-1
  ```

### **4.4 Redundancy Strategies**
| **Layer**            | **Solution** |
|----------------------|-------------|
| **Database**         | Multi-AZ (AWS RDS) or logical replication |
| **Storage**          | RAID 10 + cloud sync |
| **Compute**          | Kubernetes HA + auto-scaling |

---

## **5. Conclusion**
Data loss incidents are often avoidable with **proactive monitoring, automated backups, and failover testing**. This guide provides a structured approach to:
1. **Identify** symptoms quickly
2. **Restore** from backups with minimal downtime
3. **Prevent** future failures with redundancy

**Final Checklist Before Going Live:**
✅ Test backups monthly
✅ Verify failover procedures annually
✅ Document recovery steps for the team

By following these steps, you can minimize downtime and ensure business continuity. 🚀