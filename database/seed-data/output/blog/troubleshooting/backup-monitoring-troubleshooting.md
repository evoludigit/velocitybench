# **Debugging Backup Monitoring: A Troubleshooting Guide**
*Patterns: Observability & Reliability*
*Version: 1.0*
*Last Updated: [Insert Date]*

---

## **Overview**
Backup monitoring ensures that backups are executed successfully, validated, and restored when needed. If the backup system fails silently or produces corrupted/restorable data, critical recovery operations may fail. This guide focuses on quickly diagnosing and resolving common issues in backup monitoring systems.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the following symptoms:

| **Symptom**                          | **Question to Ask**                                                                 |
|--------------------------------------|------------------------------------------------------------------------------------|
| Backups fail to execute.             | Are cron jobs, event triggers, or scheduled tasks running?                         |
| Backups appear to run but fail silently. | Is the backup process logging errors? Are retries unsuccessful?                   |
| Backups are incomplete or truncated. | Is the storage quotas full? Are temporary files removed?                          |
| Validation checks fail.              | Are restore tests executed? Are checksums/MD5/SHA mismatched?                      |
| Alerts are not triggered.            | Are monitoring (Prometheus/Grafana) or alerting systems (PagerDuty/Slack) functional? |
| Restores fail even with valid backups.| Are storage paths correct? Are permissions restored?                              |
| Backups take excessively long.       | Is the system under load? Are snapshots too large?                                |
| Logs show errors but no alarms.      | Are log levels set correctly? Are monitoring systems receiving logs?               |

---
## **2. Common Issues & Fixes**
### **2.1 Backups Not Running (Execution Failures)**
#### **Symptom:**
- Logs show no backup execution.
- Cron jobs appear inactive.
- Scheduled backups are missing.

#### **Common Causes & Fixes:**

| **Cause**                          | **Debugging Steps**                                                                 | **Fix**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Cron job misconfiguration**      | Run `cron -l` to check active cron entries.                                           | Verify cron syntax (`0 2 * * * /path/to/backup.sh`).                    |
| **Permission issues**              | Check user permissions (`ls -l /path/to/backup`).                                    | Ensure the backup user has execute/write access on backup scripts and targets. |
| **Service not running**            | Check if the backup service (e.g., `rclone`, `rsync`, or custom script) is active. | Restart the service (`systemctl restart backup-service`).                |
| **Network downtime**               | Test connectivity to remote storage (e.g., S3, NFSServer).                           | Verify network routes (`ping`, `traceroute`).                          |
| **Disk full**                      | Check free space (`df -h`).                                                          | Free up space or expand storage.                                       |

#### **Example Fix (Cron Debugging):**
```bash
# Check cron logs
grep CRON /var/log/syslog

# Manually trigger a backup test
/path/to/backup.sh >> /var/log/backup_debug.log 2>&1
```

---

### **2.2 Silent Failures (No Logs/Alerts)**
#### **Symptom:**
- Backups seem to run but no errors are logged.
- Alerting systems (Prometheus/Grafana) don’t trigger.

#### **Common Causes & Fixes:**

| **Cause**                          | **Debugging Steps**                                                                 | **Fix**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Logs redirected/overwritten**   | Check if `>>` is used instead of `>>` in scripts.                                   | Modify scripts to append logs (`>> /var/log/backups/backup_$(date +\%Y\%m\%d).log`). |
| **Monitoring misconfigured**       | Verify Prometheus/Grafana alert rules.                                               | Test alerts with `curl -X POST http://localhost:9093/api/v1/alerts`.    |
| **Backup tool logging disabled**   | Check `rclone`, `mysqldump`, or custom tool logs.                                    | Enable verbose logging in config (e.g., `rclone --verbose`).           |
| **No exit code checking**          | Scripts may exit 0 even on failure.                                                  | Add checks in scripts: `if [ $? -ne 0 ]; then notify-send "Backup failed"; fi`. |

#### **Example Fix (Logging Check):**
```bash
#!/bin/bash
# Ensure logs are written, not redirected
exec 2>> /var/log/backup_errors.log
exec 1>> /var/log/backup_debug.log

# Test a backup
mysqldump --all-databases | gzip > /backup/mysql_$(date +\%Y\%m\%d).sql.gz
if [ $? -ne 0 ]; then
    mail -s "Backup Failed" admin@example.com < /var/log/backup_errors.log
fi
```

---

### **2.3 Incomplete/Truncated Backups**
#### **Symptom:**
- Backup files are smaller than expected.
- `du -sh /backups` shows incomplete data.

#### **Common Causes & Fixes:**

| **Cause**                          | **Debugging Steps**                                                                 | **Fix**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Premature script termination**   | Check for `timeout` or hard disk errors.                                             | Disable `ulimit -t` or increase timeout in scripts.                     |
| **Storage limits**                 | Check quotas (`quota -v`) or S3 bucket limits.                                      | Request quota increase or verify bucket policies.                       |
| **Network timeout**                | Slow transfers (e.g., WAN backups) may fail silently.                              | Adjust `rclone` buffer size or use `rsync --partial`.                  |
| **Corrupted storage**              | Bad blocks on HDD or failing SSD.                                                   | Run `badblocks` or replace storage.                                     |

#### **Example Fix (Rsync Partial Resume):**
```bash
# Configure rsync to resume partial transfers
rsync -avz --partial --progress /source/ user@backup-server:/backup/
```

---

### **2.4 Validation Failures (Checksum Mismatches)**
#### **Symptom:**
- `md5sum`/`sha256sum` fails on backup files.
- Restore fails with "corrupt archive" errors.

#### **Common Causes & Fixes:**

| **Cause**                          | **Debugging Steps**                                                                 | **Fix**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Partial transfers**              | Interrupts due to network issues.                                                  | Use `rsync --partial` or `rclone --checksum` for integrity.              |
| **Checksum tool mismatch**         | Different tools (e.g., `md5sum` vs. `sha256sum`) may produce different hashes.    | Standardize on one checksum tool.                                       |
| **Compression corruption**         | `.gz`/`.tar.gz` files may be incomplete.                                           | Verify with `gzip -t file.gz`.                                         |
| **Database backup corruption**     | MySQL/PG dumps may be truncated.                                                   | Check `mysqldump --routines --triggers --events --flush-logs`.          |

#### **Example Fix (Verify Integrity):**
```bash
# Check MySQL dump integrity
mysql --batch -e "SELECT COUNT(*) FROM information_schema.tables;" > /dev/null
if [ $? -ne 0 ]; then
    echo "Database empty or corrupted!" | mail admin@example.com
fi
```

---

### **2.5 Alerts Not Triggering**
#### **Symptom:**
- Prometheus/Grafana alerts silent.
- Slack/PagerDuty not notified.

#### **Common Causes & Fixes:**

| **Cause**                          | **Debugging Steps**                                                                 | **Fix**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Alertmanager misconfigured**     | Check `/etc/alertmanager/config.yml` for route rules.                              | Test with `curl -X POST http://localhost:9093/api/v2/alerts`.           |
| **Prometheus scrape failure**      | Verify `scrape_configs` in `prometheus.yml`.                                        | Test with `curl http://localhost:9090/api/v1/targets`.                 |
| **Integration API issues**         | PagerDuty/Slack webhook timeouts.                                                   | Check endpoint availability (`curl -v https://hooks.slack.com/...`).    |
| **Threshold too high**             | Alerts set to `backup_errors > 1` but only `backup_errors > 5` triggers.         | Adjust thresholds in Grafana/Prometheus.                               |

#### **Example Fix (Debug Alerts):**
```promql
# Check if Prometheus is scraping backup logs
up{job="backup_scraper"} == 0

# Test alert query
alert("BackupFailed") if (backup_errors > 0)
```

---

## **3. Debugging Tools & Techniques**
### **3.1 Logging & Observability**
| **Tool**               | **Use Case**                                                                       | **Example Command**                                  |
|------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------|
| **Journalctl**         | Debug systemd-based backup services.                                              | `journalctl -u backup-service.service -f`            |
| **Logrotate**          | Manage backup logs to prevent disk fills.                                         | Edit `/etc/logrotate.d/backups`                     |
| **Prometheus**         | Monitor backup execution time, error rates.                                       | `curl http://localhost:9090/graph`                  |
| **Grafana**            | Visualize backup trends (success rate, duration).                                  | Import `backup-monitoring-dashboard.json`            |
| **Rclone Logs**        | Debug S3/FTP transfers.                                                            | `rclone logtail backup:`                            |
| **Mysqldump --debug**  | Capture low-level SQL errors.                                                      | `mysqldump --debug=D,test --all-databases`           |

### **3.2 Storage Debugging**
| **Tool**               | **Use Case**                                                                       | **Example Command**                                  |
|------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------|
| **`df -h`**            | Check disk space.                                                                 | `df -h /backups`                                   |
| **`du -sh`**           | Verify backup file sizes.                                                          | `du -sh /backups/*.tar.gz`                          |
| **`badblocks`**        | Test for physical disk corruption.                                                 | `sudo badblocks -v /dev/sdb1`                        |
| **`fsck`**             | Check filesystem integrity.                                                         | `sudo fsck -f /dev/nvme0n1p2`                       |
| **`lsof`**             | Check for locked backup files.                                                     | `lsof /backups/mysql_*.sql.gz`                      |

### **3.3 Network Debugging**
| **Tool**               | **Use Case**                                                                       | **Example Command**                                  |
|------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------|
| **`ping`/`traceroute`** | Verify remote storage connectivity.                                                | `ping s3.amazonaws.com`                             |
| **`nc -zv`**           | Test port connectivity (e.g., S3 API).                                             | `nc -zv backup-server 80`                           |
| **`rclone lsjson`**    | Check S3 bucket permissions.                                                       | `rclone lsjson s3:mybucket`                         |
| **`tcpdump`**          | Capture network packets for failed transfers.                                      | `sudo tcpdump -i eth0 port 22`                       |

### **3.4 Validation Techniques**
| **Tool**               | **Use Case**                                                                       | **Example Command**                                  |
|------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------|
| **`sha256sum`**        | Verify backup file integrity.                                                      | `sha256sum /backups/db_20240101.sql.gz`             |
| **`tar -tvf`**         | Inspect `.tar` file contents.                                                      | `tar -tvf /backups/database.tar`                    |
| **`zcat`**             | Check `.gz` file structure without extraction.                                    | `zcat /backups/logs.gz | head`                        |
| **Database restore test** | Test restore on a staging server.                                                  | `mysql < /backups/db.sql`                           |

---

## **4. Prevention Strategies**
### **4.1 Design-Time Mitigations**
| **Strategy**                          | **Implementation**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------|
| **Idempotent backups**                | Use `rsync --inplace` or `rclone --update` to avoid overwriting.                  |
| **Checksum validation**               | Always compute `sha256sum` on backups and store hashes in metadata.               |
| **Multi-region backups**              | Use S3 Cross-Region Replication (CRR) or `rclone` to duplicate backups.           |
| **Retention policies**                | Enforce `7+30+90` day retention (7 for daily, 30 for weekly, 90 for monthly).     |
| **Dry-run tests**                     | Run `mysqldump --dummy` or `tar --list` before real execution.                   |

### **4.2 Runtime Monitoring**
| **Strategy**                          | **Implementation**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------|
| **Heartbeat alerts**                  | Use Prometheus to alert if backups don’t complete in `X` minutes.                  |
| **Log aggregation**                  | Ship logs to ELK Stack (Elasticsearch, Logstash, Kibana) or Loki.                  |
| **Automated validation**              | Run `sha256sum -c checksums.txt` post-backup.                                     |
| **Backup success emails**             | Send Slack/PagerDuty notifications on success *and* failure.                      |

### **4.3 Post-Mortem Procedures**
| **Strategy**                          | **Implementation**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------|
| **Blame assignment**                  | Document who owns the backup system (DevOps/SRE/DBAs).                            |
| **Runbooks**                          | Create a backup failure playbook with steps for restoration.                      |
| **Post-mortem reviews**               | After a critical failure, hold a retrospective to identify root causes.            |
| **Incremental testing**               | Simulate failures (e.g., kill backup process, corrupt a file) to test recovery.   |

---

## **5. Checklist for Quick Resolution**
1. **Confirm the backup failed** (logs, alerts, or restore attempts).
2. **Check logs** (`journalctl`, `rclone logs`, custom script logs).
3. **Validate storage** (`df`, `du`, `fsck`).
4. **Test connectivity** (`ping`, `nc`, `rclone lsjson`).
5. **Compare checksums** (`sha256sum -c`).
6. **Trigger a manual test backup** and observe execution.
7. **Restore from a known-good backup** to verify recovery.
8. **Fix the root cause** (permissions, quotas, network) and test again.
9. **Update monitoring** (Prometheus/Grafana) to catch future issues.
10. **Document the fix** in the runbook for future reference.

---
## **6. Example Debugging Workflow**
**Scenario:** Backups fail silently, no alerts, but storage is full.

1. **Check logs:**
   ```bash
   grep backup /var/log/syslog | tail -20
   ```
   → Finds `disk full` errors.

2. **Verify disk space:**
   ```bash
   df -h /backups
   ```
   → Shows `/backups` at 98% usage.

3. **Delete oldest backups:**
   ```bash
   find /backups -type f -mtime +30 -delete
   ```

4. **Restart backup service:**
   ```bash
   systemctl restart backup-service
   ```

5. **Set up disk quota alerts:**
   ```yaml
   # Prometheus alert rule
   - alert: BackupDiskFull
     expr: node_filesystem_avail_bytes{mountpoint="/backups"} / node_filesystem_size_bytes{mountpoint="/backups"} < 0.1
     for: 5m
     labels:
       severity: critical
   ```

---

## **7. References**
- [Prometheus Backup Monitoring](https://prometheus.io/docs/operating/alerting/)
- [Rclone Debugging Guide](https://rclone.org/command/)
- [MySQL Backup Best Practices](https://dev.mysql.com/doc/refman/8.0/en/backup-and-recovery.html)
- [SRE Book: Monitoring](https://sre.google/sre-book/monitoring-system/)

---
**End of Guide.**
*For further issues, escalate to the backup owners (SRE/DBAs) with logs and reproduction steps.*