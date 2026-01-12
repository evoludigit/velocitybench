# **[Pattern] Backup Approaches – Reference Guide**

---

## **Overview**
The **Backup Approach** pattern defines strategies to ensure data integrity, availability, and recovery in systems where data loss or corruption could disrupt operations. This pattern categorizes backup methodologies based on **frequency, scope, storage location, and recovery efficiency**, enabling teams to select or combine approaches depending on business needs, compliance requirements, and risk tolerance. Common use cases include disaster recovery, compliance auditing, and efficient system recovery. This guide provides a structured framework for implementing, configuring, and evaluating backup strategies in enterprise environments.

---

## **Schema Reference**

| **Component**          | **Description**                                                                                     | **Key Attributes**                                                                                     | **Example Values**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Backup Scope**       | Defines the data or system assets included in the backup.                                             | - *Criticality* (Mission-critical, Non-critical)<br>- *Granularity* (File, Volume, Database, System) | - Database tables, Active Directory, Application settings<br>- Full virtual machine (VM) snapshots |
| **Backup Frequency**   | How often backups are executed to minimize data loss risk.                                           | - *Time-based* (Hourly, Daily, Weekly, Monthly)<br>- *Trigger-based* (On change, Event-driven)      | - Hourly snapshots for databases, Daily incremental backups for files                                |
| **Backup Storage**     | Where backups are stored and their accessibility characteristics.                                     | - *Local* (On-prem storage)<br>- *Cloud* (S3, Azure Blob, GCP Coldline)<br>- *Hybrid* (On-prem + Cloud) | - Azure Backup Vault, Local NAS with redundancy<br>- AWS EFS for shared storage                      |
| **Backup Type**        | The method used to capture and store data (e.g., full, incremental, differential).                   | - *Full* (Complete dataset)<br>- *Incremental* (Only changes since last backup)<br>- *Differential* (Changes since last full backup) | - Full daily, Incremental hourly, Differential weekly                                                |
| **Recovery Mechanism** | How backups are restored or rolled back (e.g., point-in-time recovery, versioning, snapshots).      | - *Point-in-Time Recovery (PITR)*<br>- *Versioning* (Multiple snapshots)<br>- *Snapshot* (Instant capture) | - VMware snapshots, PostgreSQL logical backups<br>- AWS RDS automated backups                       |
| **Retention Policy**   | Rules governing how long backups are retained and when they are purged.                              | - *Time-based* (7/30/90 days)<br>- *Capacity-based* (Storage limits)<br>- *Compliance-based* (Retain until audit ends) | - 7-day daily backups, 30-day weekly, 90-day monthly<br>- Compliance: 7 years for legal documents  |
| **Automation Level**   | How backups are triggered and managed (manual, scheduled, or event-driven).                        | - *Manual* (User-initiated)<br>- *Scheduled* (Cron jobs)<br>- *Event-driven* (API hooks, alerts)    | - Scheduled daily at 2 AM (UTC)<br>- Automated after database schema change                        |
| **Validation**         | Mechanisms to ensure backup integrity and recoverability.                                             | - *Checksums* (MD5, SHA-256)<br>- *Test Restores* (Periodic)<br>- *Monitoring* (Alerts for failures) | - Pre-backup checksum validation<br>- Quarterly test restore of critical databases                 |

---

## **Implementation Details**

### **1. Selecting a Backup Approach**
Choose based on the following trade-offs:

| **Factor**            | **Full Backup**                          | **Incremental Backup**                    | **Differential Backup**                  |
|-----------------------|------------------------------------------|-------------------------------------------|------------------------------------------|
| **Speed**             | Slow (longer duration)                    | Fastest (only changes)                    | Moderate (since last full backup)        |
| **Storage Overhead**  | High (full copy every time)               | Low (stores only deltas)                  | Moderate (larger than incremental)        |
| **Recovery Complexity**| Simple (single restore)                 | Complex (requires full + incremental restores) | Moderate (full + differential restore)   |
| **Use Case**          | Critical systems, compliance audits      | High-frequency changes (e.g., databases)  | Balanced approach for regular updates    |

**Example Workflow:**
- **Daily:** Full backup of production databases.
- **Hourly:** Incremental backups for transactional systems.
- **Weekly:** Differential backups for file servers with moderate activity.

---

### **2. Storage Considerations**
| **Storage Type**      | **Pros**                                      | **Cons**                                      | **Best For**                              |
|-----------------------|-----------------------------------------------|-----------------------------------------------|-------------------------------------------|
| **Local Storage (NAS/SAN)** | Fast access, no egress costs                | Risk of physical failure, limited scalability  | Development environments, small teams     |
| **Cloud Storage (Cold/Hot)** | Scalable, durable, geographically distributed | Latency, cost for high-frequency backups      | Enterprise DR, global compliance          |
| **Hybrid (On-Prem + Cloud)** | Balances cost and performance               | Complex setup, cross-network dependencies    | Critical systems with local recovery needs|

**Security Considerations:**
- Encrypt backups at rest (AES-256) and in transit (TLS 1.3).
- Use **immutable storage** (e.g., AWS S3 Object Lock) to prevent ransomware tampering.
- **Access Controls:** Role-based access (e.g., read-only for backup admins, write-only for backup processes).

---

### **3. Recovery Strategies**
| **Strategy**          | **Description**                                                                                     | **Tools/Examples**                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Point-in-Time Recovery (PITR)** | Restore data to a specific timestamp (e.g., 15 minutes before a corruption).                     | PostgreSQL WAL archives, SQL Server transaction logs, VM snapshots                                   |
| **Snapshot Recovery** | Instant capture of a system state (e.g., VM, database).                                             | VMware Snapshots, AWS EBS Snapshots, ZFS snapshots                                                 |
| **Versioned Backups** | Multiple snapshots retained (e.g., daily + weekly).                                                 | Git for code, RDS automated backups, Time Machine (macOS)                                          |
| **Disaster Recovery (DR) Sites** | Replicate data to a secondary location for failover.                                                  | AWS Multi-AZ deployments, Azure Site Recovery, On-prem DR sites                                      |
| **Immutable Backups** | Prevent backups from being modified or deleted (security against ransomware).                     | AWS S3 Object Lock, WORM (Write Once, Read Many) storage                                              |

**Recovery Time Objectives (RTO):**
- **Critical Systems (e.g., databases):** <5 minutes (PITR, snapshots).
- **Non-critical (e.g., file shares):** <1 hour (daily full + incremental).
- **Compliance (e.g., financial records):** <24 hours (immutable backups retained for 7+ years).

---

### **4. Automation and Orchestration**
Use tools to automate backup workflows, monitoring, and recovery:

| **Tool**              | **Purpose**                                                                                     | **Key Features**                                                                                      |
|-----------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Veeam Backup & Replication** | Hybrid cloud/on-prem backups for VMs, databases, and files.                                     | Agentless backups, PITR, DR orchestration                                                             |
| **AWS Backup**        | Centralized management of backups across AWS services.                                           | Lifecycle policies, cross-region replication, compliance tags                                         |
| **BorgBackup (DeDuplicating Backup)** | Efficient storage for large datasets (e.g., servers, VMs).                                      | Deduplication, encryption, incremental backups                                                            |
| **Duplicati**         | Open-source, client-side encrypted backups to cloud/local.                                       | S3, WebDAV, OneDrive support; scheduling and encryption                                                |
| **NetApp SnapManager** | Database-specific backups (e.g., Oracle, SQL Server) with SnapMirror for replication.            | Application-aware backups, point-in-time recovery                                                         |

**Example Automation Script (Python + AWS):**
```python
import boto3

def create_backup_snapshot(volume_id, tag_name):
    ec2 = boto3.client('ec2')
    response = ec2.create_snapshot(
        VolumeId=volume_id,
        Description=f"{tag_name} backup",
        TagSpecifications=[
            {
                'ResourceType': 'snapshot',
                'Tags': [{'Key': 'Name', 'Value': tag_name}]
            }
        ]
    )
    return response['SnapshotId']
```

---

## **Query Examples**

### **1. Querying Backup Status (SQL Example)**
Assume a `backups` table with columns: `backup_id`, `scope`, `frequency`, `status`, `last_run`, `storage_location`.

```sql
-- List all failed backups in the last 30 days
SELECT backup_id, scope, frequency, status, last_run
FROM backups
WHERE status = 'failed'
  AND last_run > DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY last_run DESC;
```

**Expected Output:**
| backup_id | scope          | frequency | status | last_run       |
|-----------|----------------|-----------|--------|----------------|
| 42        | Database       | Hourly    | failed | 2023-10-01 14:30:00 |

---

### **2. Calculating Storage Usage by Backup Type**
```sql
-- Breakdown of storage used by backup type (full/incremental)
SELECT
    backup_type,
    SUM(size_gb) as total_size_gb,
    COUNT(*) as backup_count
FROM backups
GROUP BY backup_type
ORDER BY total_size_gb DESC;
```

**Expected Output:**
| backup_type   | total_size_gb | backup_count |
|---------------|---------------|--------------|
| Full          | 1200          | 7            |
| Incremental   | 150           | 120          |

---

### **3. Checking Retention Compliance (PowerShell Example)**
```powershell
# List backups older than retention period (90 days for monthly backups)
$retentionDays = 90
$cutoffDate = (Get-Date).AddDays(-$retentionDays)

Get-ChildItem "C:\Backups\Monthly" |
    Where-Object { $_.LastWriteTime -lt $cutoffDate } |
    Select-Object Name, LastWriteTime
```

**Expected Output:**
```
Name                LastWriteTime
----                ---------------
backup-20230101.zip 2023-05-01 00:00:00
backup-20230201.zip 2023-06-01 00:00:00
```

---

## **Related Patterns**

1. **[Immutable Storage for Backups]**
   - Ensures backups cannot be altered (critical for ransomware protection). Combines with **Backup Approaches** for compliance and security.
   - *Tools:* AWS S3 Object Lock, Windows Storage Spaces Direct (WORM).

2. **[Multi-Region Replication]**
   - Extends **Backup Approaches** by replicating backups across regions for disaster recovery.
   - *Use Case:* Global enterprises with distributed teams.

3. **[Backup Validation Checks]**
   - Complements **Backup Approaches** by adding integrity checks (e.g., checksums, test restores).
   - *Practice:* Automate daily checksum validation for critical backups.

4. **[Tiered Storage for Backups]**
   - Optimizes storage costs by moving older backups to cheaper tiers (e.g., cloud cold storage).
   - *Example:* Full backups on SSD, incremental backups on S3 Standard, archives on Glacier Deep Archive.

5. **[Backup Encryption Standards]**
   - Adds a security layer to **Backup Approaches** by encrypting data at rest and in transit.
   - *Standards:* AES-256, TLS 1.3, FIPS 140-2.

6. **[Disaster Recovery Playbooks]**
   - Documents step-by-step recovery procedures using backups from the **Backup Approaches** pattern.
   - *Components:* RTO/RPO targets, recovery order, contact lists.

7. **[Backup Monitoring and Alerts]**
   - Integrates with **Backup Approaches** to alert on failures, storage thresholds, or expired backups.
   - *Tools:* Nagios, Prometheus + Grafana, AWS CloudWatch.

---
**References:**
- [AWS Backup Best Practices](https://docs.aws.amazon.com/AWBackups/latest/userguide/whatisbackup.html)
- [NASDAQ Backup Strategy Guide](https://resources.nasdaq.com/documents/backup-strategy-guide.pdf)
- [NIST SP 800-34 (Contingency Planning Guide)](https://csrc.nist.gov/publications/detail/sp/800-34/final)