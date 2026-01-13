# **[Pattern] Backup Troubleshooting Reference Guide**

---

## **Overview**
This reference guide provides a structured approach to diagnosing and resolving backup failures in enterprise systems, ensuring minimal data loss and operational downtime. Covered are common failure modes, diagnostic methods, and remediation steps for backup platforms (e.g., traditional tape/NAS, SaaS-backed solutions, or hybrid models). The guide follows a **logical troubleshooting workflow**:
   1. **Identify the failure** (e.g., backup job hung, incomplete restore).
   2. **Gather diagnostic data** (logs, metrics, configuration).
   3. **Apply targeted fixes** (configuration tweaks, retries, or rollback).
   4. **Validate resolution** and monitor long-term stability.

Best suited for administrators, DevOps engineers, and SREs, this guide assumes familiarity with backup infrastructure components (agents, repositories, consoles) but abstracts vendor-specific details where possible.

---

## **Schema Reference**
Use the following schema to standardize troubleshooting efforts. Columns marked `*` are required.

| **Field**               | **Description**                                                                 | **Example Value**                          | **Required\*** |
|--------------------------|---------------------------------------------------------------------------------|--------------------------------------------|----------------|
| `failure_type`           | Category of failure (e.g., agent, network, storage).                            | `storage_capacity`                         | Yes            |
| `backup_job_name`        | Name of the affected backup job.                                                | `prod_db_weekly`                           | Yes            |
| `last_run_status`        | Output from the backup job’s final status field.                                | `CRITICAL: "Disk full in /backup/repo"`    | Yes            |
| `timestamp`              | UTC timestamp of failure discovery.                                             | `2024-01-15T08:45:00Z`                     | Yes            |
| `diagnostic_method`      | Tools/logs used (e.g., `repository_logs`, `network_latency_test`).              | `repository_logs + disk_health_check`      | No             |
| `root_cause`             | Root cause as identified (e.g., `stale_certs`, `throttled_repository`).         | `repository_throttling`                    | Yes            |
| `proposed_fix`           | Step-by-step actions to resolve.                                                | `1. Contact storage admin to increase I/O; 2. Retry job with --retry-limit 5` | Yes       |
| `verification_step`      | How to confirm the fix worked.                                                 | ``Check backup job status for `SUCCESS` after 24 hours`` | Yes          |
| `mitigation_mechanism`    | Short-term workaround (if applicable).                                         | `Use local backup repo until permanent fix` | No             |
| `preventive_action`      | Long-term fix to avoid recurrence.                                              | `Schedule monthly storage capacity reviews` | No             |

---

## **Key Troubleshooting Patterns**
This section categorizes failures by root cause and provides step-by-step resolution.

---

### **1. Agent/Client-Side Failures**
**Common Symptoms:**
- Backups report `TIMEOUT` or `CONNECTION_REFUSED`.
- Agent logs show `SSL handshake failure` or `authentication declined`.

#### **Diagnostic Steps**
| **Step** | **Action**                                                                                     | **Tools/Commands**                                                                 |
|----------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| 1        | Verify agent connectivity to the backup server.                                               | `telnet backup-server.example.com 443`                                            |
| 2        | Check agent logs for authentication/SSL errors in `/var/log/backup-agent/agent.log`.          | `grep "ERROR" /var/log/backup-agent/agent.log`                                     |
| 3        | Confirm client certs haven’t expired.                                                          | `openssl x509 -noout -dates -in /etc/ssl/certs/client-cert.pem`                   |

#### **Common Fixes**
| **Root Cause**               | **Remediation**                                                                         | **Preventive Action**                          |
|------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------|
| Invalid credentials          | Reset credentials via console or `bkp-cli update-account --token <new_token>`.           | Enforce credential rotation policies.          |
| Expired SSL certs            | Renew certs using `certbot` or vendor’s CA.                                             | Set calendar alerts for cert expiration.       |
| Firewall port blocking       | Whitelist ports `80/443` and `9000` (agent protocol) in firewall rules.                  | Document ports used by backup agents.          |

---

### **2. Repository (Storage)-Level Failures**
**Common Symptoms:**
- Backups fail with `STORAGE_ERROR` or `QUOTA_EXCEEDED`.
- Restores take significantly longer than usual.

#### **Diagnostic Steps**
| **Step** | **Action**                                                                                     | **Tools/Commands**                                                                 |
|----------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| 1        | Check repository disk space.                                                                 | `df -h /backup/repo`                                                               |
| 2        | Monitor repository I/O latency with `iotop` or `vmstat`.                                       | `iotop -o`                                                                         |
| 3        | Review repository logs for errors.                                                            | `journalctl -u backup-repo.service` or `rsync -av --info=stats3 /backup/repo`    |

#### **Common Fixes**
| **Root Cause**               | **Remediation**                                                                         | **Preventive Action**                          |
|------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------|
| Repository full              | Move old backups to archive storage or delete via console.                              | Set up alerts at 80% capacity.                 |
| High I/O contention          | Restructure repository into separate directories per backup type.                      | Distribute I/O load across disks.              |
| Throttled repository         | Increase throughput with vendor-specific settings (e.g., `--max-rps 1000`).              | Monitor repository performance weekly.         |

---

### **3. Network-Related Failures**
**Common Symptoms:**
- Backups fail with `NETWORK_TIMEOUT` or `DNS_FAILURE`.
- Restores are slow or intermittent.

#### **Diagnostic Steps**
| **Step** | **Action**                                                                                     | **Tools/Commands**                                                                 |
|----------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| 1        | Ping backup server from agent host.                                                           | `ping -c 5 backup-server.example.com`                                              |
| 2        | Test DNS resolution.                                                                        | `dig backup-server.example.com`                                                     |
| 3        | Measure round-trip time (RTT) and packet loss.                                               | `mtr --report backup-server.example.com`                                           |

#### **Common Fixes**
| **Root Cause**               | **Remediation**                                                                         | **Preventive Action**                          |
|------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------|
| Poor DNS configuration      | Update `/etc/resolv.conf` with correct DNS servers (e.g., `8.8.8.8`).                   | Validate DNS before major outages.              |
| High latency                 | Use VPN or prioritize backup traffic with QoS policies.                                   | Schedule backups during off-peak hours.         |
| Firewall ACL misconfiguration | Add `allow tcp 9000` rules on all hop routers.                                           | Document network paths for backup traffic.      |

---

### **4. Job Configuration Errors**
**Common Symptoms:**
- Backups fail with `CONFIG_INVALID` or exclude critical data.
- Jitter in backup durations (some jobs take minutes longer).

#### **Diagnostic Steps**
| **Step** | **Action**                                                                                     | **Tools/Commands**                                                                 |
|----------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| 1        | Validate job configuration via `bkp-cli validate-job`.                                         | `bkp-cli validate-job prod_db_backup`                                               |
| 2        | Audit log retention policies.                                                                 | `grep "retention" /etc/backup/job-config.yaml`                                     |
| 3        | Check for overlapping backup windows.                                                        | Query backup scheduler logs.                                                        |

#### **Common Fixes**
| **Root Cause**               | **Remediation**                                                                         | **Preventive Action**                          |
|------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------|
| Missing exclusions           | Update job config to exclude `/var/log/` or `/tmp/`.                                    | Document file patterns to exclude.             |
| Overlapping windows          | Stagger job schedules by `±15 minutes`.                                                  | Use backup scheduling tools (e.g., Ansible).   |
| Stale config                 | Reapply config via `bkp-cli apply-job-config`.                                          | Automate config versioning.                     |

---

## **Query Examples**
### **1. Find Failed Backups in the Last 7 Days**
```sql
SELECT
    backup_job_name,
    last_run_status,
    timestamp,
    root_cause
FROM backup_troubleshooting_logs
WHERE
    timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
    AND last_run_status NOT LIKE '%SUCCESS%';
```

### **2. Identify High-Latency Repository Queries**
```sql
SELECT
    repository_name,
    AVG(rt_time_ms) AS avg_latency
FROM repository_latency_metrics
WHERE
    rt_time_ms > 5000  -- Threshold of 5s
GROUP BY repository_name
ORDER BY avg_latency DESC;
```

### **3. Check Agent Health**
```bash
# List all agents with failed logins
bkp-cli list-agents --filter "last_login_status=FAILED"

# Check agent resource usage
docker stats backup-agent-container
```

---

## **Related Patterns**
| **Pattern Name**               | **Description**                                                                                     | **Dependency**                                      |
|---------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| [Backup Validation](link)       | Automate post-backup integrity checks (e.g., checksum validation).                                 | Backup Troubleshooting                            |
| [Disaster Recovery Plan](link) | Step-by-step guide for restoring from backup in a crisis.                                           | Backup Troubleshooting                            |
| [Monitoring for Backup Health](link) | Set up alerts for backup failures, repository health, and agent connectivity.                 | Backup Troubleshooting + Observability Patterns   |
| [Backup Automation](link)      | Script backup jobs using CI/CD tools (e.g., GitLab CI, ArgoCD).                                     | Backup Troubleshooting (post-failure workflows)   |

---
**Notes:**
- Replace `link` with actual pattern references.
- For vendor-specific details (e.g., Veeam, AWS Backup), include a **Vendor-Specific Notes** section.