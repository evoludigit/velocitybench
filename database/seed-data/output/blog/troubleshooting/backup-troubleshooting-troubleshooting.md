# **Debugging Backup Troubleshooting: A Practical Guide**
*For Senior Backend Engineers*

Backups are critical for system reliability, but failures can lead to data loss or operational downtime. This guide provides a structured approach to diagnosing and resolving backup-related issues efficiently.

---

## **1. Symptom Checklist**
Use this checklist to quickly identify backup failures:

| Symptom | Possible Cause |
|---------|----------------|
| **Backup job fails silently** | Permission issues, disk full, misconfigured storage |
| **Log entries indicate errors** | Corrupt backups, timeout errors, network issues |
| **Inconsistent restore** | Backup data mismatch with live system |
| **Slow backup performance** | Underpowered storage, excessive log retention |
| **Retention policy not enforced** | Cron job misconfiguration, cleanup scripts failing |
| **Partial backups** | Disk space constraints, interrupted processes |

---
## **2. Common Issues and Fixes**

### **2.1 Backup Job Fails Due to Permissions**
**Symptom:** `Permission denied` errors in logs.

**Fix:**
```bash
# Check owner/permissions of backup directory
ls -ld /path/to/backup/
# Example output: drwxr-x--- 3 root backup 4096 Jun 10 10:00 /backups/

# Ensure the backup user has write access
sudo chown -R backupuser:backupgroup /backups/
sudo chmod -R 750 /backups/
```
**Code Snippet (Python with `paramiko` for remote backups):**
```python
import paramiko

ssh = paramiko.SSHClient()
ssh.connect(host, username="backupuser", key_filename="~/.ssh/id_rsa")

# Check remote permissions
stdin, stdout, stderr = ssh.exec_command("ls -ld /backups")
if b"Permission denied" in stderr.read():
    print("Fix permissions before retrying")
```

---

### **2.2 Disk Full or Quota Exceeded**
**Symptom:** `No space left on device` in logs.

**Fix:**
```bash
# Check disk usage
df -h

# Clean old backups (retention=7 days)
find /backups -type f -mtime +7 -delete

# Adjust retention policy (e.g., keep only last 30 days)
du -sh /backups/* | sort -rh | head -n 10
```
**Code Snippet (Bash for automated cleanup):**
```bash
#!/bin/bash
/backup/cleanup.sh 30  # Keep backups from last 30 days
find /backups -type f -mtime +30 -exec rm -f {} \;
```

---

### **2.3 Corrupt Backups (Checksum Mismatch)**
**Symptom:** `MD5 checksum failure` in logs.

**Fix:**
```bash
# Verify a single file
md5sum /backups/dump-20240610.tar.gz

# Re-run backup with integrity checks
/opt/backup/bin/backup.sh --checksum
```
**Code Snippet (Python with `hashlib`):**
```python
import hashlib

def verify_backup(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()
```

---

### **2.4 Network Issues (Remote Backups)**
**Symptom:** Timeout errors in logs.

**Fix:**
```bash
# Test network connectivity
ping backup-server.example.com
telnet backup-server.example.com 11000  # Check if backup port is open

# Retry with exponential backoff
/opt/backup/backup.sh --retries 3 --backoff 60
```
**Code Snippet (Go with retry logic):**
```go
package main

import (
	"time"
	"net/http"
)

func backupWithRetry(url string, maxRetries int) error {
	var lastErr error
	for i := 0; i < maxRetries; i++ {
		resp, err := http.Get(url)
		if err == nil {
			defer resp.Body.Close()
			return nil
		}
		lastErr = err
		time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
	}
	return lastErr
}
```

---

### **2.5 Slow Backups Due to Large Logs**
**Symptom:** Backup taking >4 hours for a 10GB DB.

**Fix:**
```bash
# Rotate logs before backup
logrotate -f /etc/logrotate.conf

# Exclude large logs from backup
tar --exclude='/var/log/mysql/*.log' -czvf /backups/db-backup.tar.gz /var/lib/mysql/
```
**Code Snippet (Bash for optimized backup):**
```bash
#!/bin/bash
# Exclude system logs, only backup DB
find /var/lib/mysql -not -path '*/tmp/*' -exec tar rzf /backups/mysql-backup.tar.gz {} +
```

---

## **3. Debugging Tools and Techniques**

### **3.1 Log Analysis**
Key logs to check:
- **Backup service logs:** `/var/log/backup/backup.log`
- **System logs:** `/var/log/syslog`
- **Storage logs:** Ceph/GlusterFS/S3 logs

**Example (Grep for errors):**
```bash
grep -i "error\|fail" /var/log/backup/backup.log | tail -n 20
```

---

### **3.2 Network Tracing**
```bash
# Check bandwidth usage during backup
iftop -i eth0

# Trace DNS/slow responses (if using S3)
curl -v https://s3.amazonaws.com/your-bucket/object
```

---

### **3.3 Dependency Checks**
```bash
# Test if storage backend is reachable
aws s3 ls s3://your-bucket --dryrun

# Check if backup service is running
systemctl status backup-service
```

---

### **3.4 Rotation & Retention Verification**
```bash
# List last 5 backups and verify timestamps
ls -lt /backups/ | head -5

# Check retention script execution
grep "cleanup" /var/log/cron
```

---

## **4. Prevention Strategies**

### **4.1 Automated Health Checks**
```bash
#!/bin/bash
# Pre-backup check
if ! df -h /backups | awk '$5 >= 90%'; then
    echo "ERROR: Disk space full, skipping backup" | mail admin@example.com
    exit 1
fi
```

### **4.2 Test Restores Regularly**
```bash
# Schedule a monthly dry-run restore
0 2 1 * * /backup/test-restore.sh
```

### **4.3 Monitor Backup Metrics**
Use **Prometheus + Grafana** to track:
- Backup duration
- Storage usage
- Error rates

**Example Prometheus Alert:**
```yaml
groups:
- name: backup-alerts
  rules:
  - alert: BackupFailed
    expr: backup_total_failed > 0
    for: 1h
    labels:
      severity: critical
```

### **4.4 Use Immutable Backups**
```bash
# Example: Store backups in WORM (Write Once, Read Many) storage
aws s3 cp /backups/db-backup.tar.gz s3://worm-bucket/ --acl bucket-owner-full-control
```

### **4.5 Disaster Recovery (DR) Plan**
- **Offsite backups:** Use **S3 Cross-Region Replication**
- **Air-gapped tapes:** For extreme compliance needs
- **DR drills:** Test restore procedures **quarterly**

---

## **Final Checklist for Resolution**
1. **Verify logs** for exact error messages.
2. **Check storage/permissions** (`df`, `ls -ld`).
3. **Test connectivity** (`ping`, `telnet`).
4. **Validate checksums** (`md5sum`).
5. **Optimize retention** (`logrotate`, `find`).
6. **Monitor post-fix** to prevent recurrence.

---
### **Key Takeaway**
Backup failures are often **permissions, storage, or network issues**. Use structured logs, automated checks, and retention policies to prevent outages.

**Next Steps:**
- Automate recovery playbooks.
- Document backup procedures in the **runbook**.
- Schedule **quarterly DR tests**.

Would you like a deeper dive into any specific section?