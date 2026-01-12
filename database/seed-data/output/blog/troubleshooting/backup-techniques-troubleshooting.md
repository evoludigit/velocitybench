# **Debugging Backup Techniques: A Troubleshooting Guide**

## **Introduction**
Backup Techniques are critical for ensuring data durability, availability, and disaster recovery in distributed systems. Whether using **local backups, distributed replication, immutable snapshots, or cross-region replication**, failures can occur due to network issues, storage corruption, misconfigurations, or race conditions.

This guide provides a **fast-paced, actionable approach** to diagnosing and resolving common backup-related problems, focusing on **real-world scenarios** rather than theoretical explanations.

---

## **1. Symptom Checklist**
Before diving into debugging, systematically verify the following symptoms:

| **Symptom Category** | **Possible Causes** | **Quick Checks** |
|----------------------|-------------------|------------------|
| **Backup Failures** | - Permission issues
- Storage full/quota exceeded
- Corrupted backups
- Network timeouts | `ls -l /backup/dir` (disk space)
`kubectl logs backup-pod` (if Kubernetes-based)
`tail -f /var/log/backup-service.log` |
| **Slow/Stalled Backups** | - High I/O latency
- Throttling (e.g., S3 transfer limits)
- Large datasets | `iostat -x 1` (disk metrics)
`du -sh /data/to/backup` (file size) |
| **Restore Failures** | - Corrupted backup files
- Incompatible versions
- Missing dependencies | `checksum backup_file` (verify integrity)
`restore --dry-run` (test before actual restore) |
| **Replication Lag** | - Network congestion
- Replication filter misconfigurations
- Source system outage | `aws s3api list-object-versions --bucket backup-bucket` (S3 versioning)
`journalctl -u replication-service` (systemd logs) |
| **Missing Backups** | - Cron job failure
- Permission issues
- Logs not rotated | `last | grep backup` (cron history)
`cat /var/log/syslog | grep backup` |

---

## **2. Common Issues and Fixes**
### **Issue 1: Backup Job Fails with "Permissions Denied"**
**Symptoms:**
- Backup pod crashes with `Permission denied` in logs.
- Local backup script exits with `EACCES`.

**Root Cause:**
- Incorrect RBAC permissions (Kubernetes).
- Incorrect IAM roles (AWS/S3).
- Wrong filesystem permissions (`chmod` issues).

**Fixes:**
#### **Kubernetes (RBAC)**
```yaml
# Ensure the backup service account has read access to required resources
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backup-reader
rules:
- apiGroups: [""]
  resources: ["pods", "secrets"]
  verbs: ["get", "list"]
```
Apply with:
```bash
kubectl apply -f backup-role.yaml
```

#### **AWS S3 (IAM Policy)**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::your-backup-bucket",
        "arn:aws:s3:::your-backup-bucket/*"
      ]
    }
  ]
}
```
Attach this policy to the backup service role.

#### **Filesystem Permissions (Linux)**
```bash
# Fix directory permissions
chown -R backup-user:backup-group /path/to/backup
chmod -R 750 /path/to/backup

# Verify with
ls -ld /path/to/backup  # Should show -rwxr-x--- (750)
```

---

### **Issue 2: Backups Stuck in "Running" State**
**Symptoms:**
- `kubectl get jobs` shows backups stuck for hours.
- Logs indicate `No space left on device`.

**Root Cause:**
- PersistentVolume (PV) full.
- Backup script not killing long-running processes (e.g., `pg_dump` with `--format=plain` for large PostgreSQL dbs).

**Fixes:**
#### **Check Disk Space**
```bash
df -h /path/to/pv
# If full, clean up old backups:
find /backup -mtime +30 -delete
```

#### **Optimize PostgreSQL Backup (Example)**
```bash
# Instead of plaintext, use custom format (faster, smaller)
pg_dump -d dbname -Fc -f backup.dump --jobs=4 --max-worker-processes=4
```
- `-Fc`: Custom format (faster restore).
- `--jobs`: Parallelize dumping.

---

### **Issue 3: Restore Fails with "Data Corruption"**
**Symptoms:**
- `restic restore` fails with `invalid checksum`.
- S3 backup versioning shows incomplete files.

**Root Cause:**
- Network interruption during upload/download.
- S3 multipart upload failure.
- Restic checksum mismatch (e.g., `--checksum` flag not used).

**Fixes:**
#### **Verify Backup Integrity (Restic)**
```bash
# Force checksum validation
restic check --read-errors --checksum --path /backup/path
```
If corrupted:
```bash
# Recreate backup with checksums enabled
restic backup --one-file-system --exclude-cache --checksum /data/to/restore
```

#### **Retry Failed S3 Multipart Uploads**
```bash
# List incomplete multipart uploads (AWS CLI)
aws s3api list-multipart-uploads --bucket your-bucket

# Abort and retry
aws s3api abort-multipart-upload --bucket your-bucket --upload-id UPLOAD_ID
```

---

### **Issue 4: Replication Lag (Primary → Secondary)**
**Symptoms:**
- Secondary DB/bucket is hours behind.
- Logs show `replication lag exceeded threshold`.

**Root Cause:**
- Slow network between regions.
- Replication filter excluding critical tables.
- WAL (PostgreSQL)/binlog (MySQL) retention too short.

**Fixes:**
#### **Check Replication Lag (PostgreSQL)**
```sql
-- Query replication status
SELECT * FROM pg_stat_replication;
```
If lag is high:
```sql
-- Increase WAL retention (in postgresql.conf)
wal_keep_size = '1GB'
```
Restart PostgreSQL:
```bash
systemctl restart postgresql
```

#### **Optimize AWS DMS Replication**
```json
// Example: Increase batch size to reduce latency
{
  "BatchApply": {
    "BatchSize": 10000,
    "CommitTimeout": 30
  }
}
```
Apply changes via AWS Console or CLI.

---

### **Issue 5: Backup Service Crashes on Startup**
**Symptoms:**
- `systemctl status backup-service` shows `Exited with code 134 (SIGABRT)`.
- Logs contain `segmentation fault`.

**Root Cause:**
- Memory leak in backup tool (e.g., `mongodb-dump`).
- Corrupted config file.
- Missing dependencies.

**Fixes:**
#### **Check Logs for Memory Issues**
```bash
# Run backup with valgrind (if available)
valgrind --tool=memcheck backup-service
```
If memory issues persist:
```bash
# Reduce parallelism (example for `aws s3 sync`)
aws s3 sync source bucket --exclude "*" --include "small_file*" --dryrun
```

#### **Validate Config File**
```bash
# Example: Validate YAML config
yq eval . /etc/backup/config.yaml
```

---

## **3. Debugging Tools and Techniques**
### **Logging & Monitoring**
| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| `journalctl`           | Systemd service logs (Linux)                                                 | `journalctl -u backup-service -f`            |
| `kubectl logs`         | Kubernetes pod logs                                                         | `kubectl logs -n backup-ns backup-pod`       |
| `aws cloudwatch`       | AWS Lambda/EC2 logs                                                          | `aws logs get-log-events --log-group-name`   |
| `restic cat`           | Inspect backup contents without restoring                                   | `restic cat latest::/path/to/file`           |
| `pgbadger`             | PostgreSQL slow query analysis (if backups involve DB)                      | `pgbadger --log postgresql.log`              |

### **Network Debugging**
```bash
# Check latency between regions (for cross-region backups)
ping -c 4 backup-endpoint.amazonaws.com

# Trace route
mtr --report backup-endpoint.amazonaws.com

# AWS CLI: Test S3 connection
aws s3 ls s3://your-bucket --endpoint-url https://s3.us-east-1.amazonaws.com
```

### **Storage Debugging**
```bash
# Check filesystem health
fsck /dev/nvme0n1p2

# Test S3 bucket consistency
aws s3api get-object --bucket your-bucket --key testfile.txt --output text
```

### **Performance Profiling**
```bash
# Profile CPU usage (for slow backups)
perf record -g ./backup-script.sh
perf report

# Check disk I/O bottlenecks
iotop -o
```

---

## **4. Prevention Strategies**
### **Automated Health Checks**
- **Pre-backup checks:**
  ```bash
  # Ensure disk space before backing up
  if [ $(df -h /backup | awk 'NR==2 {print $4}') -lt 10G ]; then
    echo "ERROR: Insufficient disk space!" | mail -s "Backup Alert" admin@example.com
    exit 1
  fi
  ```
- **Post-backup validation:**
  ```bash
  # Verify checksums (example for Restic)
  restic check --read-errors --dry-run
  ```

### **Rate Limiting & Retries**
- **Exponential backoff for S3:**
  ```python
  import backoff

  @backoff.on_exception(backoff.expo, ConnectionError, max_tries=5)
  def upload_to_s3(bucket, filename):
      s3.put_object(Bucket=bucket, Key=filename, Body=open(filename, 'rb'))
  ```

### **Backup Testing (DR Drills)**
- **Schedule monthly restore tests:**
  ```bash
  # Test restore to a separate volume
  restic restore latest --target /tmp/test-restore
  diff -r /original/path /tmp/test-restore
  ```
- **Simulate failures:**
  ```bash
  # Kill a backup pod and verify rollback
  kubectl delete pod backup-pod --force --grace-period=0
  ```

### **Configuration Best Practices**
- **Use immutable backups:**
  ```bash
  # Example: Restic with immutable storage
  restic backup /data --repository s3:https://your-bucket --packer-threads 8
  ```
- **Enable versioning (S3/PostgreSQL):**
  ```sql
  -- PostgreSQL WAL archiving
  archive_command = 'aws s3 cp %p s3://your-bucket/wal/%f'
  archive_timeout = 30
  ```

---

## **5. Summary Checklist for Quick Resolution**
| **Scenario**               | **First Steps**                                                                 | **Escalation Path**                          |
|----------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| Backup fails with "Permission denied" | Check RBAC/IAM, `ls -l`, `chmod`                                               | Contact DevOps for policy adjustments        |
| Backups stuck               | `df -h`, `kubectl describe job`, `find /backup -mtime +30 -delete`              | Scale up storage or optimize backup scripts  |
| Restore corruption          | `restic check`, retry S3 uploads, `--dry-run`                                  | Recreate backup with `--checksum` enabled   |
| Replication lag             | `pg_stat_replication`, increase `wal_keep_size`, AWS DMS batch tuning          | Upgrade hardware or use cold standby         |
| Service crashes             | `journalctl`, `valgrind`, reduce parallelism                                   | Replace binary or upgrade to latest version |

---

## **Final Notes**
- **Isolate the problem:** Is it **storage**, **network**, or **application**?
- **Test in staging first:** Never debug production backups directly; replicate the issue in a test environment.
- **Document fixes:** Update runbooks for recurring issues (e.g., "PostgreSQL WAL retention was increased to 1GB after lag issues").

By following this structured approach, you can **minimize downtime** and **prevent data loss** while keeping backups reliable.