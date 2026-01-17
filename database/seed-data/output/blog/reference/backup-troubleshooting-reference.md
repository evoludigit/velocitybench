# **[Pattern] Backup Troubleshooting Reference Guide**

---

## **Overview**
Backup troubleshooting ensures data integrity and system reliability when backups fail or behave unexpectedly. This guide provides a structured approach to diagnosing, resolving, and preventing backup-related issues. It covers common failure scenarios, validation techniques, logs, and recovery workflows, while addressing both logical (data corruption, partial restores) and physical (media failures, network issues) failures. The guide follows a diagnostic methodology—**Isolate → Diagnose → Resolve → Prevent**—to streamline troubleshooting and minimize downtime.

---

## **Schema Reference**

The following tables outline key components of the **Backup Troubleshooting** pattern, organized by category.

### **1. Common Backup Failure Types**
| **Failure Type**         | **Description**                                                                                     | **Root Causes**                                                                                     | **Impact Level** |
|--------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|-------------------|
| **Logical Failure**      | Data corruption, incomplete backups, or missing files                                               | - Incorrect backup policies<br>- Disk I/O errors<br>- Application inconsistencies<br>- Metadata corruption | High              |
| **Physical Failure**     | Hardware issues (storage, network, backup appliances)                                                  | - Media wear/tear<br>- Network timeouts<br>- Insufficient storage space<br>- Power surges           | Critical          |
| **Resource Failure**     | Insufficient CPU/memory, disk throttling, or saturation                                              | - High system load<br>- Disk I/O bottlenecks<br>- Backup client resource starvation                 | Medium            |
| **Authentication Failure**| Permissions, credentials, or access restrictions                                                      | - Expired credentials<br>- Incorrect ACLs<br>- Service account lockout                                   | High              |
| **Network Failure**      | Timeouts, connectivity drops, or encryption mismatches                                                | - Firewall blocking ports<br>- VPN disconnections<br>- MTU mismatches<br>- Certificate expiration   | Critical          |
| **Validation Failure**   | Failed integrity checks (hash mismatches, checksum errors)                                            | - Corrupt backup media<br>- Rsync/consistency tool failures<br>- Network interference during transfer | Medium            |

---

### **2. Diagnostic Tools & Logs**
| **Tool/Log**             | **Purpose**                                                                                     | **Location**                                                                                     | **Key Metrics**                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Backup Agent Logs**    | Detailed execution logs (start/stop times, errors, retries)                                       | `/var/log/<backup-agent>/backup.log` (Linux)<br>`C:\ProgramFiles\<BackupAgent>\logs` (Windows) | `BackupStartTime`, `ErrorCode`, `RetryCount`, `BytesTransferred`                                  |
| **Storage Array Logs**   | I/O errors, latency, or storage capacity alerts                                                   | Array management console (e.g., Dell EMC Unisphere, NetApp ONTAP)                                | `ReadLatency`, `WriteErrors`, `DiskUtilization`, `IOPS`                                           |
| **Network Diagnostics**  | Packet loss, latency, or protocol-level issues                                                    | `tcpdump`, `Wireshark` (Linux/Windows), `netstat -s`                                              | `PacketLoss`, `RTT`, `TCPRetransmits`, `EncryptionHandshakeFailures`                              |
| **Validation Scripts**   | Post-backup integrity checks (hash comparisons, file counts)                                       | Custom scripts, `dd` (Linux), `certutil` (Windows)                                               | `HashMismatchCount`, `MissingFiles`, `CorruptBlocks`                                            |
| **Backup Policy Logs**   | Policy violations (e.g., retention exceedances, failed schedules)                                | `Backup Service Console` (e.g., Veeam, Commvault)                                                | `PolicyViolationType`, `SchedulesSkipped`, `QuotaExceeded`                                        |
| **DNS/Active Directory** | Authentication and resolution failures                                                             | Active Directory Event Logs, `nslookup`, `dig`                                                   | `FailedLogins`, `DNSResolutionFailures`, `KerberosTickets`                                       |

---

### **3. Recovery Workflows**
| **Scenario**              | **Recovery Steps**                                                                               | **Tools/Commands**                                                                               |
|---------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Partial Backup**       | - Identify missing files via validation script.<br>- Re-run selective backup for missing data.   | `rsync -av --checksum /source /backup` (Linux)<br>`robocopy /MIR` (Windows)                     |
| **Corrupt Backup Media** | - Verify media health (SMART tests).<br>- Restore to a clean target if corruption is detected.    | `smartctl -a /dev/sdX` (Linux)<br>`Disk Management` (Windows)                                    |
| **Network Disruption**   | - Restart backup service.<br>- Check firewall rules and MTU settings.<br>- Retry transfer.       | `iptables -L` (Linux)<br>`netsh int ipv4 set subinterface <ID> mtu=<value>` (Windows)            |
| **Permission Issues**    | - Reapply ACLs or user permissions.<br>- Test backup with elevated privileges.                 | `chmod -R 755 /backup-dir` (Linux)<br>`icacls /grant <user>:F` (Windows)                        |
| **Storage Full**          | - Add storage capacity.<br>- Archive old backups.<br>- Adjust retention policies.               | `df -h` (Linux)<br>`fsutil volume diskfree C:` (Windows)                                        |
| **Backup Agent Crash**   | - Restart service.<br>- Review logs for resource constraints.<br>- Update agent to latest version. | `service <backup-agent> restart` (Linux)<br>`sc stop/start` (Windows)                          |

---

### **4. Prevention Measures**
| **Measure**               | **Description**                                                                                     | **Implementation**                                                                               |
|---------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Regular Validation**   | Schedule automated hash/checksum comparisons.                                                      | Cron job (Linux): `0 3 * * * /backup/validate.sh`<br>Task Scheduler (Windows)                    |
| **Resource Monitoring**  | Set alerts for CPU/memory/disk thresholds.                                                          | Prometheus/Grafana (Linux)<br>`Performance Monitor` (Windows)                                   |
| **Redundancy**            | Distribute backups across multiple storage targets.                                                | Multi-site replication (e.g., Veeam, Azure Site Recovery)                                       |
| **Automated Rollback**   | Implement pre-backup snapshots for quick recovery.                                                 | `zfs snapshot` (Linux)<br>`VSS (Volume Shadow Copy)` (Windows)                                   |
| **Credential Rotation**   | Automate credential updates for service accounts.                                                 | `hashicorp/vault` for secrets management                                                          |
| **Log Retention**        | Configure log retention policies (e.g., 90 days).                                                  | AWS CloudTrail, `logrotate` (Linux)                                                               |

---

## **Query Examples**
Use these queries to diagnose issues in logs or monitoring systems.

### **1. Identify Failed Backups in Veeam Logs**
```sql
SELECT
    JobName,
    StartTime,
    EndTime,
    Status,
    ErrorType,
    ErrorMessage
FROM
    VeeamJobLogs
WHERE
    EndTime > DATEADD(DAY, -7, GETDATE())
    AND Status = 'Failed';
```

### **2. Check Disk Health with `smartctl` (Linux)**
```bash
smartctl -a /dev/sdX | grep -i "reallocated_sector_ct\|udma_crc_error_count\|power_on_hours"
```
- **Expected Output:**
  ```
  Reallocated_Sector_Ct   0x0033   106   106   000   Old_age   Always       -       3
  UDMACRCErrorCount   0x003b   200   200   000   Old_age   Always       -       0
  Power_On_Hours   0x0032   089   089   000   Old_age   Always       -       1200
  ```

### **3. Validate Backup Integrity with `sha256sum` (Linux)**
```bash
sha256sum -c /backup/integrity_checksum.txt
```
- **Expected Output (No Errors):**
  ```
  /path/to/file1.dat: OK
  /path/to/file2.dat: OK
  ```

### **4. Check Network Latency (Ping + Traceroute)**
```bash
ping -c 10 backup.target.example.com
traceroute backup.target.example.com
```
- **Alert if:**
  - `> 10% packet loss` or
  - RTT consistently `> 200ms`.

### **5. Query Azure Backup Status (Azure CLI)**
```bash
az backup vault backup-item list --vault-name <VaultName> --resource-group <RGName> --query "[].{Status:status, Error:lastError}"
```

---

## **Related Patterns**
To complement **Backup Troubleshooting**, consider these patterns for broader data protection:

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Disaster Recovery]**   | Plan for catastrophic failures (e.g., site outages, ransomware)                                    | When backup alone cannot restore critical systems within SLA.                                      |
| **[Immutable Backups]**   | Prevent tampering with backups using write-once-read-many (WORM) storage.                       | High-security environments (e.g., healthcare, finance) where compliance is critical.             |
| **[Incremental Forever]** | Retain only new changes since the last full backup to reduce storage overhead.                  | Long-term retention requirements (e.g., compliance archives).                                     |
| **[Multi-Cloud Backup]**  | Distribute backups across cloud providers for redundancy.                                           | Global deployments requiring regional compliance or geo-redundancy.                                |
| **[Backup Automation]**   | Script backup jobs, monitoring, and alerts to reduce manual effort.                                | Large-scale environments with frequent backups.                                                    |
| **[Backup Verification]** | Automate validation checks (e.g., restore tests, checksums) to ensure recoverability.             | Critical systems where data loss cannot be risked.                                                |

---
**Note:** For cloud-specific backups, refer to the provider’s documentation (e.g., **AWS Backup**, **Azure Backup**, **Google Cloud Storage**). Always test restores in a staging environment.