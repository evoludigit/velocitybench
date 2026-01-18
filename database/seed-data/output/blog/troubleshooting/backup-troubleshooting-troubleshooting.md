# **Debugging Backup Failures: A Practical Troubleshooting Guide**
*For Senior Backend Engineers*
*Version: 1.0*

---

## **Introduction**
Backups are critical for data integrity, disaster recovery, and compliance. When backups fail, they can lead to data loss, operational downtime, and regulatory penalties. This guide provides a systematic approach to diagnosing and resolving common backup issues efficiently.

---

## **Symptom Checklist: Is Your Backup Failing?**
Before diving into fixes, rule out the most common signs of backup failure.

| **Symptom**                     | **Possible Cause**                          | **Action** |
|---------------------------------|--------------------------------------------|------------|
| ✅ Backup job reports "Failed" in monitoring tools (e.g., Prometheus, Nagios) | Permissions, network issues, or corruption | Check logs, verify credentials, test connectivity |
| ✅ Backup completes but restores fail with "Invalid checksum" | Corrupted data or incomplete backup | Validate checksums, retry backup, verify storage health |
| ✅ Backups take significantly longer than usual | Slow storage, I/O bottlenecks, or resource contention | Monitor disk I/O, check for storage performance degradation |
| ✅ No logs generated (no entry in backup logs) | Application/cron job misconfiguration | Verify cron schedules, check `journalctl`/`syslog` |
| ✅ "Disk full" errors in logs | Insufficient storage space | Check disk usage (`df -h`), clean up old backups |
| ✅ "Permission denied" errors | Incorrect I/O permissions | Verify `chmod/chown` on backup files, check SELinux/AppArmor |
| ✅ Backup job skips critical tables/files | Exclusion rules misconfigured | Review backup scripts/configs for exclusions |
| ✅ Restores work on one machine but fail on another | Environment-specific issues (e.g., file paths, dependencies) | Test restore in a controlled environment |
| ✅ Backups work intermittently | Network flapping, storage latency | Enable packet capture (`tcpdump`), check storage SAN performance |

---
**Pro Tip:** Start with the most likely causes (permissions, network, storage) before digging deeper.

---

## **Common Issues & Fixes (With Code Examples)**

### **1. Permission Issues**
**Symptom:** `Permission denied` in logs, backup fails silently.
**Root Cause:** Backup scripts (e.g., `mysqldump`, `rsync`) lack write/execute permissions on critical directories.

#### **Debugging Steps:**
```bash
# Check if the backup user has proper permissions
ls -ld /backups  # Should show ownership and permissions (e.g., drwxr-x---)
whoami          # Verify running user (should match backup user)
```

#### **Fix:**
```bash
# Grant necessary permissions to the backup user
chown -R backupuser:backupsgroup /backups
chmod 750 /backups  # Read/write/execute for owner, read/execute for group
```

**For SELinux/AppArmor:**
```bash
# Relabel files if SELinux is enforcing
restorecon -Rv /backups
setenforce 0       # Temporarily disable SELinux to test (use `setenforce 1` to re-enable)
```

---

### **2. Network-Related Failures**
**Symptom:** Timeouts, "Connection refused," or slow transfer speeds.
**Root Cause:** Firewall rules, VPN instability, or misconfigured backup targets (e.g., S3, remote servers).

#### **Debugging Steps:**
```bash
# Test connectivity to the backup target (e.g., S3 endpoint)
telnet s3.amazonaws.com 443  # Should succeed
ping backup-target.example.com

# Check firewall rules (Linux)
sudo iptables -L -n  # Verify no drops on outgoing traffic
```

#### **Fix:**
- **For S3 backups (AWS CLI):**
  Ensure AWS credentials are valid and IAM policies allow `s3:PutObject`:
  ```bash
  aws s3 ls s3://your-bucket-name  # Test credentials
  ```
  If using a **VPC endpoint**, verify it’s attached to the subnet:
  ```bash
  aws ec2 describe-vpc-endpoints --filters "Name=vpc-endpoint-type,Values=Interface"
  ```

- **For `rsync` over SSH:**
  Ensure SSH keys are configured and the remote user has permissions:
  ```bash
  rsync -avz --progress /source/ user@remote:/destination/  # Dry run first
  ```

---

### **3. Storage Corruption or Full Disks**
**Symptom:** "Disk full" or "I/O error" in logs.
**Root Cause:** Insufficient space, disk failures, or misconfigured retention policies.

#### **Debugging Steps:**
```bash
# Check disk usage
df -h /backups  # Should have >10% free space
du -sh /backups/*  # Find largest files/directories

# Check for disk errors (Linux)
sudo smartctl -a /dev/sdX  # Replace X with your disk
```

#### **Fix:**
- **Clean up old backups:**
  ```bash
  # Example: Keep only 30 days of backups
  find /backups -type f -mtime +30 -delete
  ```
- **Expand storage (if using EBS/NFS):**
  ```bash
  # For AWS EBS: Increase volume size and resize filesystem
  sudo growpart /dev/nvme0n1 1  # Resize partition
  sudo resize2fs /dev/nvme0n1p1  # Resize filesystem
  ```

---

### **4. Backup Script/Configuration Errors**
**Symptom:** Script exits with non-zero status or incomplete data.
**Root Cause:** Misconfigured exclusion rules, missing dependencies, or syntax errors.

#### **Debugging Steps:**
```bash
# Run backup in verbose mode
mysqldump --verbose -u user -p database > /dev/stderr  # For MySQL
rsync -avv /source/ /destination/  # Verbose rsync

# Check for warnings in logs
tail -n 50 /var/log/backup.log
```

#### **Fix:**
- **For MySQL backups:**
  Ensure `--single-transaction` is used for InnoDB tables:
  ```bash
  mysqldump --single-transaction --routines --triggers -u user -p database > backup.sql
  ```
- **For `rsync` exclusions:**
  Verify `.rsyncfilter` or `--exclude` rules:
  ```bash
  rsync -av --exclude='tmp/*' --exclude='log/*' /source/ /destination/
  ```

---

### **5. Checksum Mismatches (Data Integrity Issues)**
**Symptom:** Restore fails with "MD5 checksum mismatch."
**Root Cause:** Corrupted backup files, incomplete transfers, or checksums not being verified.

#### **Debugging Steps:**
```bash
# Verify checksum before restore
md5sum /path/to/backup.sql | grep "expected_checksum"  # Compare with original
```

#### **Fix:**
- **Re-run backup with integrity checks:**
  ```bash
  # For MySQL
  mysqldump --single-transaction --quick --checksum -u user -p database > backup.sql

  # For general files
  sha256sum /source/* > checksums.txt
  scp checksums.txt user@remote:/destination/
  ```
- **If corruption is confirmed, restore from a known-good backup.**

---

## **Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                  | **Example Command**                          |
|------------------------|-----------------------------------------------|----------------------------------------------|
| `journalctl`           | Check systemd-service logs (e.g., `mysqldump`) | `journalctl -u mysqldump.service -xe`         |
| `tcpdump`              | Capture network traffic for SSH/S3 issues    | `sudo tcpdump -i eth0 port 22 or 443`         |
| `aws s3api`            | Debug S3 API failures                         | `aws s3api list-objects --bucket your-bucket` |
| `iostat`               | Monitor disk I/O performance                  | `iostat -x 1`                                |
| `strace`               | Trace system calls (e.g., `rsync`)            | `strace -f rsync -avz /source/ /dest/`       |
| `lsof`                 | Check file locks (e.g., databases)            | `lsof -p $(pgrep mysqld)`                     |

**Pro Tip:**
- Use **temporary logging** to capture real-time issues:
  ```bash
  # Redirect all backup logs to a file
  /usr/local/bin/mysqldump -u user -p database 2>&1 | tee /tmp/backup_debug.log
  ```

---

## **Prevention Strategies**

### **1. Automated Health Checks**
- **Pre-backup checks:**
  ```bash
  # Example: Run pre-flight checks in a cron job
  if ! df -h /backups | awk '$6 < 10'; then
      echo "ERROR: Low disk space! Aborting backup." | mail -s "FAIL: Low disk space" admin@example.com
      exit 1
  fi
  ```
- **Post-backup verification:**
  ```bash
  # Compare backup file size against expected size
  expected_size=$(du -sb /source/ | cut -f1)
  actual_size=$(du -sb /backups/latest | cut -f1)
  if [ "$expected_size" -ne "$actual_size" ]; then
      alert "Backup size mismatch!"
  fi
  ```

### **2. Test Restores Regularly**
- **Automate restore tests:**
  ```bash
  # Example: Restore to a staging environment
  rsync -av /backups/20231001/ /staging/ --dry-run  # Dry run first
  rsync -av /backups/20231001/ /staging/            # Actual restore
  ```
- **Use tools like `aws s3 restore` for S3:**
  ```bash
  aws s3 cp s3://bucket/backup.zip /tmp/backup.zip
  unzip /tmp/backup.zip -d /tmp/restore_test
  ```

### **3. Monitor Backup Jobs**
- **Prometheus + Alertmanager:**
  ```yaml
  # Example Prometheus alert for failed backups
  - alert: BackupFailed
    expr: backup_job_status == 0  # Assuming 0 = failed
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Backup failed: {{ $labels.job }}"
  ```
- **Log aggregation (ELK Stack/Grafana):**
  Visualize backup trends (success/failure rates, duration).

### **4. Retention Policies**
- **Automate cleanup with `find`:**
  ```bash
  # Delete backups older than 30 days
  find /backups -type f -mtime +30 -delete
  ```
- **For cloud storage (S3/GCS):**
  ```yaml
  # AWS S3 Lifecycle Policy (JSON)
  {
    "Rules": [
      {
        "ID": "DeleteOldBackups",
        "Status": "Enabled",
        "Filter": { "Prefix": "backups/old/" },
        "Expiration": { "Days": 90 }
      }
    ]
  }
  ```

### **5. Document Critical Steps**
- Maintain a **runbook** with:
  - Backup scripts + versions.
  - Known failures and fixes.
  - Contact list for escalation (storage vendor, cloud support).

---

## **Final Checklist Before Escalating**
✅ **Permissions:** Verified with `ls -ld`, `chmod/chown`.
✅ **Network:** Tested with `telnet`, `ping`, `tcpdump`.
✅ **Storage:** Checked with `df -h`, `smartctl`.
✅ **Logs:** Reviewed `journalctl`, application logs.
✅ **Configuration:** Validated backup scripts/configs.
✅ **Integrity:** Verified checksums before restore.

---
**Escalation Path:**
If the issue persists, involve:
1. **Storage admin** (if using SAN/NFS).
2. **Cloud provider** (if using S3/EBS).
3. **Database admin** (for schema/locking issues).

---
**Key Takeaway:**
Backup failures are often **environmental** (permissions, network, storage) rather than code-related. Start with the **5 Whys** method to drill down quickly. Automate checks and tests to prevent recurrence.