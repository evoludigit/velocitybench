---
# **[Pattern] Logging Maintenance Reference Guide**

---

## **Overview**
Logging Maintenance is a systematic approach to managing log data across its lifecycle—from generation to archival or deletion—ensuring compliance, performance, and troubleshooting efficiency. This pattern standardizes log retention policies, rotation strategies, and cleanup processes while integrating with monitoring and alerting systems. By applying structured retention rules (e.g., time-based or size-based), organizations mitigate storage costs, reduce noise, and align logs with regulatory requirements (e.g., GDPR, HIPAA).

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Log Retention**      | Duration logs are preserved before deletion/archival.                                              | Retain logs for 30 days for debug, 90 days for security audits.                              |
| **Log Rotation**       | Process of splitting log files to manage size (e.g., daily rotation).                             | `app.log` → `app.log.2023-10-01`, `app.log.2023-10-02`.                                       |
| **Compression**        | Compressing old logs to save storage space (e.g., gzip).                                          | `log-2023-10-01.gz`.                                                                           |
| **Purge Policy**       | Rules defining when logs are deleted (e.g., "Delete logs older than X days").                     | Automated deletion of logs older than 365 days.                                               |
| **Log Sharding**       | Splitting logs by attributes (e.g., per-service, per-region) to improve query performance.      | `logs/2023-10/serviceA`, `logs/2023-10/serviceB`.                                             |
| **Audit Logs**         | Logs capturing administrative actions (e.g., user logins, config changes).                       | `audit.log` with entries like `{"action": "user_login", "user": "admin", "timestamp": "..."}` |

---

## **Implementation Details**

### **1. Log Retention Strategy**
Define retention policies based on log type and compliance needs:
- **Time-Based**: Delete logs after X days/weeks (e.g., 90 days for debugging logs).
- **Size-Based**: Rotate/logs when size exceeds Y MB (e.g., 100 MB).
- **Event-Based**: Delete logs after a specific event (e.g., user logout).

**Best Practices**:
- Prioritize critical logs (e.g., errors, security events) over less important ones (e.g., INFO-level logs).
- Use tiered retention (e.g., 30 days for standard logs, 7 years for compliance logs).

---

### **2. Log Rotation**
Configure rotation manually (e.g., via cron jobs) or use framework-specific tools:
- **Linux (`logrotate`)**:
  ```ini
  /var/log/app.log {
      daily
      missingok
      rotate 14
      compress
      delaycompress
      notifempty
      create 640 root adm
  }
  ```
- **Windows (`LogRotate` or PowerShell)**:
  ```powershell
  (Get-ChildItem -Path "C:\logs" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }) | Remove-Item -Force
  ```
- **Programming Languages**:
  - **Python** (with `logging.handlers.TimedRotatingFileHandler`):
    ```python
    handler = TimedRotatingFileHandler(
        filename='app.log',
        when='midnight',
        interval=1,
        backupCount=7
    )
    ```

---

### **3. Compression**
Compress logs to reduce storage overhead:
- **Tools**:
  - `gzip` (Unix):
    ```bash
    gzip -9 /var/log/app.log
    ```
  - **Python**:
    ```python
    import gzip
    with open('app.log', 'rb') as f_in:
        with gzip.open('app.log.gz', 'wb') as f_out:
            f_out.writelines(f_in)
    ```

---

### **4. Log Sharding**
Split logs by metadata (e.g., service name, timestamp) for parallel processing:
- **Example Structure**:
  ```
  logs/
  ├── 2023-10/
  │   ├── serviceA/
  │   │   ├── app.log
  │   │   └── app.log.gz
  │   └── serviceB/
  │       ├── app.log
  │       └── app.log.gz
  ```

---

### **5. Purge Automation**
Schedule deletions using:
- **Cron Jobs (Unix)**:
  ```bash
  0 0 * * * /usr/bin/find /var/log -name "*.log" -mtime +30 -delete
  ```
- **Azure Functions/Cloud Scheduler**:
  Trigger Lambda functions to delete old logs in S3/Blob Storage.
- **Custom Scripts**:
  ```python
  import os
  from datetime import datetime, timedelta

  threshold = datetime.now() - timedelta(days=30)
  for log_file in os.listdir('/var/log'):
      if log_file.endswith('.log') and os.path.getmtime(log_file) < threshold.timestamp():
          os.remove(log_file)
  ```

---

### **6. Audit Logging**
Track maintenance actions (e.g., log purges) in a separate audit log:
```json
{
  "event": "log_purge",
  "timestamp": "2023-10-01T12:00:00Z",
  "user": "admin",
  "action": "delete_logs",
  "retention_policy": "older_than_30_days",
  "logs_affected": ["/var/log/app.log.2023-09*"]
}
```

---

## **Schema Reference**
Below is a schema for a **Log Maintenance Configuration File** (e.g., `log-maintenance.yml`):

| **Field**               | **Type**       | **Description**                                                                                     | **Example**                                                                                   |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `retention_policies`    | Object[]       | Array of retention rules per log directory.                                                       | `["/var/log": { "days": 30, "compress": true }]`                                   |
| `rotation`              | Object         | Rotation settings (size/time-based).                                                             | `{"size_mb": 100, "time_interval": "daily"}`                                         |
| `exclusions`            | String[]       | Files/directories to exclude from cleanup.                                                        | `["/var/log/audit_secure", "/var/log/backup"]`                                        |
| `audit_log_path`        | String         | Path to store maintenance audit logs.                                                              | `/var/log/audit/log-maintenance.log`                                                    |
| `schedules`             | Object         | Cron-like schedule for maintenance tasks.                                                         | `{"purge": "0 0 * * *", "compress": "30 0 * * *"}`                                |

**Example `log-maintenance.yml`**:
```yaml
retention_policies:
  - path: "/var/log/app"
    days: 30
    compress: true
rotation:
  size_mb: 100
  time_interval: "daily"
exclusions:
  - "/var/log/audit_secure"
  - "/var/log/backup"
audit_log_path: "/var/log/audit/log-maintenance.log"
schedules:
  purge: "0 0 * * *"
  compress: "30 0 * * *"
```

---

## **Query Examples**
### **1. Find Logs Older Than 7 Days (Unix)**
```bash
find /var/log/app -type f -name "*.log" -mtime +7 -exec ls -lh {} \;
```

### **2. List Compressed Logs (Python)**
```python
import glob
for log_file in glob.glob("/var/log/app/*.log.gz"):
    print(f"Compressed log: {log_file}")
```

### **3. Query Log Shards (SQL-like Pseudocode)**
```sql
SELECT * FROM logs
WHERE service = 'serviceA'
  AND timestamp BETWEEN '2023-10-01' AND '2023-10-31';
```

---

## **Related Patterns**
1. **Structured Logging**
   - Ensures logs have a consistent format (e.g., JSON) for easier parsing and querying.
   - *Use Case*: Combine with Log Maintenance to standardize retention across systems.

2. **Log Centralization**
   - Aggregate logs from multiple sources (e.g., ELK Stack, Splunk) before applying maintenance.
   - *Use Case*: Apply global retention policies to centralized logs.

3. **Anomaly Detection**
   - Integrate with monitoring tools (e.g., Prometheus, Datadog) to flag unexpected log patterns during maintenance.
   - *Use Case*: Detect corrupted logs during purge operations.

4. **Log Encryption**
   - Encrypt sensitive logs (e.g., PII) before archival.
   - *Use Case*: Comply with GDPR while maintaining logs for 7 years.

5. **Canary Releases**
   - Test log maintenance changes (e.g., purge scripts) in a staging environment before production.
   - *Use Case*: Validate retention rules without impacting live systems.

---

## **Troubleshooting**
| **Issue**                          | **Root Cause**               | **Solution**                                                                                     |
|------------------------------------|-----------------------------|-------------------------------------------------------------------------------------------------|
| Logs not rotating                   | Incorrect `logrotate` config | Verify `daily`, `size`, and `rotate` settings.                                                  |
| Compression failing                | Permission denied           | Ensure `gzip` has read/write access to log directories.                                          |
| Purge missing logs                  | Exclusion pattern mismatch  | Double-check `exclusions` in config files.                                                      |
| Audit logs not recording actions    | Misconfigured audit path     | Verify `audit_log_path` exists and permissions are correct.                                       |
| Performance degradation             | Inefficient sharding        | Reduce shard granularity or use distributed file systems (e.g., HDFS).                          |

---

## **Tools & Libraries**
| **Tool/Library**       | **Purpose**                                                                                     | **Link**                                                                                       |
|------------------------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `logrotate`            | Automated log rotation/compression.                                                           | [Man Page](https://linux.die.net/man/8/logrotate)                                             |
| `AWS Lambda`           | Serverless log cleanup for cloud environments.                                                 | [AWS Docs](https://aws.amazon.com/lambda/)                                                     |
| `Python `logging`      | Built-in log rotation (via `RotatingFileHandler`).                                            | [Python Docs](https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler)    |
| `ELK Stack`            | Centralized log storage with retention policies.                                               | [ELK Info](https://www.elastic.co/elk-stack)                                                   |
| `Prometheus`           | Monitor log maintenance jobs (e.g., purge latency).                                           | [Prometheus](https://prometheus.io/)                                                         |

---
**Note**: Customize retention policies and tools based on your infrastructure (e.g., on-prem vs. cloud). Always back up logs before maintenance operations.