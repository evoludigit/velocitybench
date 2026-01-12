# **Debugging Backup Conventions: A Troubleshooting Guide**

## **1. Introduction**
Backup conventions ensure data integrity, versioning, and recoverability by enforcing standardized naming, retention, and location rules for backups. Common issues arise from misconfigured retention policies, inconsistent naming, or improper backup storage. This guide provides a structured approach to diagnosing and resolving these problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms to confirm the issue relates to backup conventions:

| **Symptom**                          | **Question to Ask**                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------------|
| Backups fail or are incomplete        | Are log files or job reports indicating failures due to naming/retention constraints? |
| Old backups are not pruned automatically | Are retention policies misconfigured?                                               |
| Restores fail due to missing versions  | Are backup prefixes/suffixes not following expected conventions?                   |
| Storage space fills up unexpectedly  | Are backups overwriting each other due to poor versioning?                         |
| Missing critical backup files         | Are wildcards or naming patterns misconfigured in backup scripts?                   |

---

## **3. Common Issues and Fixes**

### **Issue 1: Retention Policy Not Working**
**Symptom:** Backups older than X days are not deleted.

**Root Cause:**
- Retention cron jobs are misconfigured.
- Scripts lack proper cleanup logic.

**Fix:**
- **Check Cron Job:**
  ```bash
  crontab -l  # Verify retention cleanup job exists
  ```
  Example cron entry:
  ```bash
  0 3 * * * /path/to/backup_cleanup.sh /backups/ --days-to-keep 30
  ```
- **Implement Cleanup Script (Python Example):**
  ```python
  import os
  import glob
  from datetime import datetime, timedelta

  days_to_keep = 30
  backup_dir = "/backups"

  def cleanup_old_backups():
      cutoff_date = datetime.now() - timedelta(days=days_to_keep)
      for backup_file in glob.glob(f"{backup_dir}/backup_*.tar.gz"):
          file_date = datetime.strptime(backup_file.split("_")[-1].split(".")[0], "%Y%m%d")
          if file_date < cutoff_date:
              os.remove(backup_file)

  cleanup_old_backups()
  ```

---

### **Issue 2: Naming Convention Mismatch**
**Symptom:** Restores fail because backup filenames don’t match expected patterns.

**Root Cause:**
- Scripts don’t follow `YYYYMMDD` or hostname-based naming.
- Backup tool misconfigured (e.g., `mysqldump` without custom naming).

**Fix:**
- **Ensure Consistent Naming in Scripts:**
  ```bash
  # Correct: Include timestamp and version
  mysqldump -u user -p db_name | gzip > /backups/db_backup_$(date +%Y%m%d).tar.gz

  # Incorrect: No versioning
  mysqldump -u user -p db_name | gzip > /backups/db_backup.tar.gz
  ```
- **Validate Backup Naming Programmatically:**
  ```python
  import re
  from datetime import datetime

  def validate_backup_name(filename):
      pattern = r"backup_(?P<date>\d{8})_(?P<version>\d+)\.tar\.gz"
      match = re.match(pattern, filename)
      if not match:
          raise ValueError("Backup filename doesn't match pattern!")
      return match.group("date"), match.group("version")
  ```

---

### **Issue 3: Storage Quotas Exceeded**
**Symptom:** Disk fills up despite retention policies.

**Root Cause:**
- Backup scripts overwrite old versions without proper versioning.
- No hard limit on backup count.

**Fix:**
- **Add Versioning to Backup Scripts:**
  ```bash
  # Track last backup version
  LAST_VERSION=$(ls /backups/db_backup_*.tar.gz | grep -oE '[0-9]+$' | sort -nr | head -1)
  VERSION=$((LAST_VERSION + 1))

  mysqldump -u user -p db_name | gzip > /backups/db_backup_$(date +%Y%m%d)_${VERSION}.tar.gz
  ```
- **Use `find` to Enforce Limits:**
  ```bash
  find /backups -name "backup_*.tar.gz" -mtime +30 -delete  # Delete >30 days
  find /backups -name "backup_*.tar.gz" | wc -l  # Monitor count
  ```

---

### **Issue 4: Cross-Backup Corruption**
**Symptom:** Partial backups due to interrupted jobs.

**Root Cause:**
- No checksum validation.
- No incremental backup strategy.

**Fix:**
- **Add Checksum Validation:**
  ```bash
  # Generate and verify checksums
  gzip -c db_dump.sql > /backups/db_backup_$(date +%Y%m%d).sql.gz
  md5sum /backups/db_backup_$(date +%Y%m%d).sql.gz > /backups/checksums/md5sum_$(date +%Y%m%d).txt
  ```
  **Verify:**
  ```bash
  cat /backups/checksums/md5sum_*.txt | grep -i "corrupt\|match"
  ```

---

## **4. Debugging Tools & Techniques**
### **A. Automated Validation Scripts**
- **Check Backup Integrity:**
  ```bash
  # Script to verify all backups are valid
  for backup in /backups/backup_*.tar.gz; do
      if ! tar -tzf "$backup" &>/dev/null; then
          echo "Corrupt backup: $backup" >> /logs/backup_errors.log
      fi
  done
  ```

### **B. Logging & Monitoring**
- **Enable Detailed Logging in Backup Tools:**
  ```bash
  # Example for rsync
  rsync -avz --log-file=/var/log/backup_rsync.log /source/ /dest/
  ```
- **Use `systemd` Journal for Cron Jobs:**
  ```bash
  journalctl -u backup_cleanup.service -f  # Monitor retention jobs
  ```

### **C. Dry Runs**
- **Test Retention Without Deleting:**
  ```bash
  find /backups -name "backup_*.tar.gz" -mtime +30 -print  # List what would be deleted
  ```

---

## **5. Prevention Strategies**
### **A. Enforce Naming Standards**
- Use **predefined templates** (e.g., `app_name_YYYYMMDD_version.tar.gz`).
- **Validate filenames** on backup creation.

### **B. Automate Validation**
- **Post-backup checks** for checksums/completeness.
- **Alert on anomalies** (e.g., via Slack/email).

### **C. Document Retention Policies**
- **Store retention rules** in config files (e.g., `/etc/backup/policy.json`):
  ```json
  {
    "retention_days": 30,
    "max_backups": 5,
    "alert_threshold": 80  # % storage used
  }
  ```

### **D. Use Infrastructure as Code (IaC)**
- **Define backup conventions in Terraform/Ansible:**
  ```yaml
  # Ansible backup task with naming
  - name: Backup database with versioned names
    command: mysqldump db_name | gzip > "/backups/db_backup_{{ lookup('pipe', 'date +%Y%m%d') }}_{{ lookup('pipe', 'date +%H%M%S') }}.tar.gz"
  ```

---

## **6. Final Checklist for Resolution**
| **Step**               | **Action**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| Verify logs             | Check backup scripts, cron, and app logs for errors.                        |
| Test retention         | Run cleanup scripts in dry mode first.                                      |
| Validate naming         | Confirm all backups follow the pattern.                                    |
| Monitor storage         | Use `df -h` or tools like `nmon` for anomalies.                            |
| Restore test backup     | Verify a recent backup restores correctly.                                  |

---

## **Conclusion**
Backup conventions are only effective if enforced rigorously. By following this guide, you can:
1. **Quickly identify** naming/retention issues.
2. **Automate fixes** with scripts and cron jobs.
3. **Prevent future problems** through validation and monitoring.

For persistent issues, consider **audit trails** (e.g., logging all backup operations) and **automated alerts** (e.g., Prometheus + Grafana for storage trends).

---
**Need further help?** Check the upstream tool docs (e.g., `mysqldump`, `rsync`) for version-specific quirks.