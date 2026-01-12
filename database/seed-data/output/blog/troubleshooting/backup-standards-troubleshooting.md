# **Debugging [Backup Standards]: A Troubleshooting Guide**
*Ensuring Reliable Data Backups with Best Practices*

---

## **1. Introduction**
The **Backup Standards** pattern ensures critical data is consistently reproduced, validated, and recoverable in case of failures. This guide focuses on diagnosing and resolving common issues in backup systems, covering infrastructure, processes, and tooling.

---

## **2. Symptom Checklist**
Before diving into fixes, assess the following symptoms to identify the root cause:

### **Backup System Symptoms**
- **[ ]** Backups fail without clear error logs.
- **[ ]** Backup files are corrupted or incomplete.
- **[ ]** Restores from backups fail (data loss, inconsistent state).
- **[ ]** Backup windows exceed SLAs (e.g., daily backups take 12+ hours).
- **[ ]** Storage capacity issues (disk full, inefficient storage policies).
- **[ ]** Network bottlenecks during backup transfers.
- **[ ]** Inconsistent backup metadata (e.g., missing timestamps, versioning).

### **Application/Database Symptoms**
- **[ ]** Applications reliant on backups fail to launch post-restoration.
- **[ ]** Transactional data missing in restores (incomplete WAL/redo logs).
- **[ ]** Schema migrations fail after restore.
- **[ ]** User permissions or roles not preserved in backups.

### **Tool/Configuration Symptoms**
- **[ ]** Backup agents or scheduler crashes repeatedly.
- **[ ]** Configuration drift (e.g., incorrect retention policies).
- **[ ]** Monitor alerts (e.g., high CPU/disk I/O during backups).
- **[ ]** Missing post-backup validation steps (checksums, consistency tests).

---

## **3. Common Issues and Fixes**
### **3.1 Backups Fail Silently (No Logs)**
**Symptoms:**
- Backup jobs complete but leave no meaningful logs.
- No email/SMS alerts, despite configuration.

**Diagnosis:**
- Check **scheduler logs** (e.g., cron, Kubernetes CronJob, Airflow DAG runs).
- Verify **agent logs** (e.g., rsync, `pg_dump`, Veeam, BackupPC).
- Ensure **alerting systems** (e.g., Nagios, Prometheus, Grafana) are configured.

**Fixes:**
#### **Code/Config Example: Enabling Rsync Debugging**
```bash
# Add verbose logging to rsync backup command
rsync -avx --verbose --log-file=/var/log/backups/rsync_$(date +%Y%m%d).log /source/ user@backup-server:/destination/
```
#### **Fixing Backup Agent Timeouts**
```python
# Example for a Python-based backup script (e.g., using boto3 for S3)
import boto3
import logging

logging.basicConfig(level=logging.INFO)
s3 = boto3.client('s3', region_name='us-east-1')

try:
    response = s3.upload_file(
        '/path/to/local/file',
        'my-bucket',
        'backup/file.tar.gz',
        ExtraArgs={'ServerSideEncryption': 'AES256'}
    )
    logging.info(f"Backup uploaded: {response['ResponseMetadata']['HTTPStatusCode']}")
except Exception as e:
    logging.error(f"Backup failed: {str(e)}", exc_info=True)
    raise
```

---

### **3.2 Corrupted Backup Files**
**Symptoms:**
- Restores fail with checksum mismatches.
- Database restores show truncated tables.

**Diagnosis:**
- Run **checksum validation** (e.g., `sha256sum` for files, `pg_checksums` for PostgreSQL).
- Test backup integrity by extracting a small subset of data.

**Fixes:**
#### **PostgreSQL Example: Verify Backups**
```sql
-- Check for corrupt tables
SELECT tablename FROM pg_tables
WHERE relfilenode NOT IN (
    SELECT pg_relation_filepath(oid) FROM pg_class
    WHERE relname = 'your_table'
);
```
#### **Fixing Incremental Backup Corruption**
If using `pg_basebackup`, ensure:
```bash
# Use full backup if incremental is suspect
pg_basebackup -D /backup/path -Fp -z -R -C
```

---

### **3.3 Sluggish Backup Performance**
**Symptoms:**
- Backups take 2x+ the expected time.
- High CPU/disk I/O during backups.

**Diagnosis:**
- Use `iostat`, `vmstat`, or `dstat` to monitor system load.
- Check network bandwidth (`nload`, `iftop`).

**Fixes:**
#### **Optimize Filesystem I/O**
```bash
# Example: Use XFS with compression for backups
mkfs.xfs -d suite=performance,swalloc=noreserve,inodealloc=noreserve,allocsize=1M /dev/sdX
```
#### **Parallelize Backups**
```bash
# Example: Use parallel tar for large directories
tar -cvJf backup.tar.xz -I 'pigz -p $(nproc)' /large/directory/
```

---

### **3.4 Restores Fail with "Inconsistent State"**
**Symptoms:**
- Restored data doesn’t match production.
- Database transactions appear lost.

**Diagnosis:**
- Compare **pre- and post-restore checksums**.
- Check **WAL/redo logs** (PostgreSQL) or binlog (MySQL).

**Fixes:**
#### **PostgreSQL: Recover Using WAL Archiving**
```bash
# Restore database with WAL recovery
pg_restore -d restored_db -C --clean --no-owner --no-privileges --host=localhost --port=5432 /backup/path
```
#### **MySQL: Use Binary Logs**
```bash
# Recover MySQL using binlog and GTID
mysqlbinlog --start-datetime='2023-01-01 00:00:00' --stop-never --execute 'SOURCE /tmp/backup/mysql-bin.000001' | mysql -uroot -p
```

---

### **3.5 Storage Overflows**
**Symptoms:**
- Storage quota exceeded during backups.
- Old backups not pruned automatically.

**Diagnosis:**
- Check disk usage (`df -h`).
- Audit backup retention policies.

**Fixes:**
#### **Automate Retention with `logrotate` (Linux)**
```bash
# Example: Rotate logs weekly, keep 4 weeks
/var/log/backups/*.log {
    rotate 4
    weekly
    missingok
    compress
    delaycompress
    notifempty
    create 0640 root root
}
```
#### **Cloud Backups: Set Lifecycle Policies (AWS S3)**
```json
{
  "Rules": [
    {
      "ID": "ArchiveOldBackups",
      "Status": "Enabled",
      "Filter": {"Prefix": "backups/year=2023/"},
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        }
      ],
      "Expiration": {"Days": 90}
    }
  ]
}
```

---

## **4. Debugging Tools and Techniques**
### **4.1 Essential Tools**
| Tool               | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| `journalctl`       | View system logs (systemd-based systems).                               |
| `dmesg`            | Kernel-level errors (hardware/device issues).                          |
| `pgbadger`         | PostgreSQL log analyzer (detect slow queries, errors).                 |
| `ncdu`             | Disk usage analyzer (find space hogs).                                  |
| `iotop`            | Monitor disk I/O per process.                                           |
| `tcpdump`          | Network troubleshooting (e.g., backup transfer failures).               |
| `aws cli`          | Debug S3/Glacier backups.                                              |
| `pg_dumpall`       | Validate full PostgreSQL backups.                                        |

### **4.2 Debugging Techniques**
1. **Isolate the Component**
   - Test backup **storage** (e.g., separate backup server, cloud bucket).
   - Test **agent** (e.g., run manually without scheduler).

2. **Reproduce in Staging**
   - Use a **test environment** identical to production to debug.

3. **Check for Race Conditions**
   - Example: Backups running while WAL files are being written (PostgreSQL).

4. **Validate with Checksums**
   - Use `sha256sum` for files or `pg_checksums` for databases.

5. **Review Alerts**
   - Check **Prometheus/Grafana** for anomalies (e.g., high latency).

---

## **5. Prevention Strategies**
### **5.1 Configuration Best Practices**
- **Retention Policies:**
  - **3-2-1 Rule:** 3 copies (1 primary, 2 backups), 2 media types, 1 offsite.
  - Example for `rsync`:
    ```bash
    # Keep weekly (7), monthly (4), yearly (3), and delete older
    rsync -avx --delete --max-size=10G /source/ user@backup:/destination/
    find /destination/ -type f -mtime +90 -delete  # Delete >90 days
    ```
- **Encryption:**
  - Encrypt in transit (TLS) and at rest (AES-256).
  - Example for S3:
    ```bash
    aws s3api put-bucket-encryption --bucket my-bucket --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
    ```

### **5.2 Automation and Monitoring**
- **Automate Validation:**
  - Run `pg_dump --verify` or checksum checks post-backup.
- **Monitor Backups:**
  - Use **Prometheus + Grafana** to track backup duration, failures.
- **Test Restores Weekly:**
  - Schedule a **dry run** restore to verify integrity.

### **5.3 Disaster Recovery Drills**
- **Quarterly Failover Tests:**
  - Simulate a primary failure and restore from backups.
- **Documented Recovery Steps:**
  - Maintain a **runbook** for critical services (e.g., database restore steps).

### **5.4 Tooling**
- **Open-Source Tools:**
  - **BorgBackup** (deduplication, encryption).
  - **Duplicati** (cross-platform, cloud-compatible).
- **Commercial Tools:**
  - **Veeam** (enterprise backups).
  - **Commvault** (scalable, multi-cloud).

---

## **6. Summary Checklist for Operators**
| Task                          | Done? |
|--------------------------------|-------|
| Verify backup logs are enabled. | []    |
| Test restore from last backup.| []    |
| Check storage quotas.         | []    |
| Validate checksums.           | []    |
| Review retention policies.     | []    |
| Monitor backup performance.   | []    |

---

## **7. Further Reading**
- **[PostgreSQL Backup Guide](https://www.postgresql.org/docs/current/backup.html)**
- **[AWS Backup Best Practices](https://docs.aws.amazon.com/backup/latest/devguide/backup-best-practices.html)**
- **[Rsync Advanced Usage](https://www.gnu.org/software/rsync/manual/html_node/Advanced-Talk.html)**

---
**Final Tip:** *If all else fails, start fresh—sometimes the simplest solution is to rebuild from a known-good backup.*