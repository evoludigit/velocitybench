# **Debugging Backup Guidelines: A Troubleshooting Guide**
*By [Your Name], Senior Backend Engineer*

---

## **Table of Contents**
1. [Introduction](#introduction)
2. [Symptom Checklist](#symptom-checklist)
3. [Common Issues and Fixes](#common-issues-and-fixes)
4. [Debugging Tools and Techniques](#debugging-tools-and-techniques)
5. [Prevention Strategies](#prevention-strategies)

---

## **1. Introduction**
The **Backup Guidelines** pattern ensures reliable data recovery by defining structured backup procedures, storage policies, and recovery mechanisms. Issues in this pattern often stem from misconfigured backups, improper validation, or failure to follow best practices.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving backup-related failures, minimizing downtime.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms to isolate the root cause:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|---------------------------------------------|
| Backups fail silently or report errors | Incorrect permissions, corrupted data, or storage issues |
| Restores take longer than expected   | Slow storage, network latency, or compressed files |
| Partial backups (missing critical data) | Incomplete snapshot, failed retention checks |
| High storage costs (unexpected growth) | Unbounded retention policies, duplicate backups |
| Backup logs show `Permission Denied`  | Misconfigured IAM roles, SELinux/AppArmor blocking access |
| Backups skip critical databases       | Excluded patterns in backup config          |
| Recovery fails with "Data Corruption" | Unstable storage (e.g., failing disks, network blips) |
| Alerts for "Backup Window Missed"    | Scheduled backups disabled or misconfigured |

**Action:** Cross-check logs, storage metrics, and backup config files before proceeding.

---

## **3. Common Issues and Fixes**

### **A. Backups Fail Due to Permission Issues**
**Symptom:** `Permission denied` in logs, backup scripts exit with `1` (failure).

**Root Causes:**
- Incorrect user privileges (e.g., `root` vs. `backup-user`).
- SELinux/AppArmor blocking backup tools like `rsync` or `vault`.

**Fixes:**

#### **1. Verify & Fix File Permissions**
```bash
# Check permissions on source & backup dirs (example for rsync)
ls -ld /var/log /backup/logs/
```
**Expected Output:**
```
drwxr-x--- 2 root backup 4096 Oct 10 10:00 /var/log
drwxrwx--- 3 root backup 4096 Oct 10 10:01 /backup/logs/
```
**Fix Permissions:**
```bash
sudo chown -R backup-user:backup-group /backup/logs
sudo chmod 750 /backup/logs  # Only owner can write
```

#### **2. Adjust SELinux (if enabled)**
```bash
# Temporarily allow rsync (for testing)
sudo setenforce 0  # Disables SELinux (use cautiously)
```
**Permanent Fix (recommended):**
```bash
sudo semanage fcontext -a -t public_content_rw_t "/backup/logs(/.*)?"
sudo restorecon -Rv /backup/logs
```

#### **3. Use `sudo` in Backup Scripts**
Modify backup scripts to escalate privileges:
```bash
sudo rsync -avz --delete /var/log/ /backup/logs/
```

---

### **B. Backups Skip Critical Databases**
**Symptom:** Missing database backups in logs or recovery fails.

**Root Causes:**
- Database excluded via pattern (e.g., `!db1` in config).
- Backup tool lacks DB-specific plugins (e.g., `mysqldump` for MySQL).

**Fixes:**

#### **1. Check Backup Exclusion Patterns**
```bash
# Example for Duplicati (config file)
grep -i "exclude" /etc/duplicati/global.config
```
**Fix:** Remove exclusions or add explicit includes:
```xml
<!-- Example for Duplicati -->
<add key="includePatterns" value="*.db,/var/lib/mysql/*" />
```

#### **2. Use Database-Specific Tools**
For **MySQL/MariaDB**, replace `rsync` with:
```bash
mysqldump --all-databases --user=backup_user --password="XXX" > /backup/mysql.dump
```
For **PostgreSQL**:
```bash
pg_dumpall -U postgres > /backup/postgres.dump
```

---

### **C. Storage Issues (Slow/Full/Failed Backups)**
**Symptom:** Backups stall, time out, or show `IOError`.

**Root Causes:**
- Network-attached storage (NAS) latency.
- Disk full or corrupted.
- Throttled cloud storage (e.g., S3).

**Fixes:**

#### **1. Check Storage Health**
```bash
# Disk usage
df -h /backup/
# Disk health (SMART data)
sudo smartctl -a /dev/sdX
```
**Fix:** Clean up old backups or add more storage.

#### **2. Optimize Backup Tools**
For **S3-backed backups**, ensure retries are enabled:
```bash
# Example for Duplicati S3 remote
<add key="remoteUri" value="s3://bucket-name/" />
<add key="remotePassword" value="AWS_ACCESS_KEY" />
<add key="s3Encryption" value="AES256" />
```

#### **3. Compress Backups**
Add compression in `rsync`:
```bash
rsync -avz --delete --compress /data /backup/data/
```

---

### **D. Backup Logs Missing Critical Errors**
**Symptom:** No errors in logs, but backups appear incomplete.

**Root Causes:**
- Log rotation truncates errors.
- Backup tool logs to a file with incorrect permissions.

**Fixes:**

#### **1. Enable Debug Logging**
For **Duplicati**:
```xml
<add key="logLevel" value="Debug" />
<add key="logFile" value="/var/log/duplicati.log" />
```
For **custom scripts**:
```bash
#!/bin/bash
exec >> /var/log/backup.log 2>&1
# Rest of script...
```

#### **2. Check Log Retention**
```bash
# Example: Rotate logs daily
logger "Backup started" | tee /var/log/backup.log
```

---

### **E. Recovery Fails with "Data Corruption"**
**Symptom:** Restored data is incomplete or corrupted.

**Root Causes:**
- Backup was interrupted mid-transfer.
- Checksum validation failed.

**Fixes:**

#### **1. Validate Checksums**
For **Duplicati**, use:
```bash
duplicati-server --verify-bucket
```
For **custom backups**, compare before/after:
```bash
sha256sum /original/file.txt
sha256sum /restored/file.txt
```

#### **2. Retry from Partial Backups**
If backup failed mid-way, restore only the last successful snapshot:
```bash
# Example: Restore from 2023-10-10
aws s3 cp s3://bucket/backup-2023-10-10.tar.gz /restore/
tar -xzf /restore/backup-2023-10-10.tar.gz -C /target/
```

---

## **4. Debugging Tools and Techniques**
| **Tool/Technique**               | **Use Case**                          | **Example Command**                     |
|-----------------------------------|---------------------------------------|-----------------------------------------|
| `rsync --progress`                | Monitor real-time transfer           | `rsync -avz --progress /data /backup/`  |
| `iotop`                           | Identify storage bandwidth hogs      | `sudo iotop -o`                         |
| `strace`                          | Debug low-level system calls          | `strace -f rsync ...`                  |
| `journalctl` (systemd)           | Check backup service logs            | `journalctl -u duplicati.service`       |
| `aws s3 ls --recursive`           | Verify S3 backup integrity           | `aws s3 ls s3://bucket/backup/`         |
| `du` + `--human-readable`         | Check disk space usage               | `du -sh /backup/*`                     |
| `tcpdump`                         | Network latency issues                | `tcpdump -i eth0 port 9022` (for S3)    |

---

## **5. Prevention Strategies**
### **A. Automate Validation**
- **Test restores weekly** (e.g., restore a small file daily).
- **Use checksums** (e.g., `md5sum`, `sha256sum`) for critical data.

### **B. Implement Retention Policies**
- **Example for Duplicati**:
  ```xml
  <add key="versioning" value="Weekly,Monthly,Yearly" />
  <add key="versioningKeepFreeSpace" value="10%" />
  ```
- **Cloud Storage**: Use S3 lifecycle rules to auto-delete old backups.

### **C. Monitor Backups**
- **Prometheus + Grafana**: Track backup duration, size, and failures.
- **Alerting**: Set up Slack/email alerts for failed backups.

### **D. Document Failover Procedures**
- **Runbook**: Step-by-step recovery for critical systems.
- **Example**:
  ```markdown
  # MySQL Recovery
  1. Stop MySQL: `sudo systemctl stop mysql`
  2. Restore dump: `mysql -u root < /backup/mysql.dump`
  3. Restart: `sudo systemctl start mysql`
  ```

### **E. Use Immutable Storage (Optional)**
For cloud backups, enable **S3 Object Lock** or **AWS Glacier Deep Archive** to prevent accidental overwrites.

---

## **6. Final Checklist Before Going Live**
| **Task**                                  | **Status**       |
|-------------------------------------------|------------------|
| Test backup & restore on staging         | [ ]               |
| Verify permissions for backup dirs       | [ ]               |
| Enable debug logging                     | [ ]               |
| Set up retention policies                | [ ]               |
| Configure alerts for failures            | [ ]               |
| Document recovery steps                  | [ ]               |
| Monitor first 3 backups                  | [ ]               |

---

## **Conclusion**
Backup failures often stem from **permissions, storage issues, or misconfigurations**. By following this guide:
1. **Systematically check symptoms** (logs, storage, permissions).
2. **Apply targeted fixes** (e.g., SELinux tweaks, checksum validation).
3. **Prevent future issues** (automated tests, retention policies, monitoring).

**Next Steps:**
- Schedule a **full backup validation** in a non-production environment.
- Review **log retention** for debugging past failures.

---
*Need deeper troubleshooting? Check the [Backup Tool’s Official Docs](#).*