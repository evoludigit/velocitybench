# **[Pattern] Backup Strategies: Reference Guide**

## **Overview**
The **Backup Strategies** pattern defines a structured approach to designing, implementing, and maintaining data backup solutions to ensure **data durability, availability, and recoverability** in response to failures, corruption, or disasters. This pattern helps organizations balance **cost, speed, reliability, and compliance** by defining clear policies for backup frequency, retention periods, redundancy, and recovery procedures. It is applicable across **databases, file systems, cloud storage, and hybrid environments**, and should be tailored to specific **RTO (Recovery Time Objective)** and **RPO (Recovery Point Objective)** requirements.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 | **Example**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **RTO (Recovery Time Objective)** | Maximum tolerable downtime before business operations are restored.                                                                                                                                              | *"95% uptime (≤4h downtime/year)"* or *"<1h for critical systems."*                           |
| **RPO (Recovery Point Objective)** | Maximum acceptable data loss (time between last backup and failure).                                                                                                                                              | *"1h"* (hourly backups), *"5 min"* (real-time replication).                                    |
| **Backup Strategy**     | A predefined approach to back up data, including **type (full/incremental/differential), frequency, storage, and retention rules**.                                                                    | *"Daily full backups + hourly incremental backups for 7 days + monthly full backups for 12 months."* |
| **Backup Type**         | How backups are performed:                                                                                                                                                                                     |                                                                                                 |
| - **Full Backup**       | Copies **all data** in a dataset or system. Slower but simplest to restore.                                                                                                                                       | Nightly full database dump.                                                                     |
| - **Incremental Backup** | Copies **only changed data** since the last backup (full or incremental). Faster but requires chain of backups for restore.                                                                                     | Hourly incremental backups for transactional databases.                                        |
| - **Differential Backup** | Copies **all data changed since the last full backup**. Balances speed and restore complexity.                                                                                                              | Daily differential backups for file servers.                                                   |
| - **Snapshot**          | Point-in-time **copy** of a filesystem/VM (no data copied; linked to original). Fast but limited by storage and underlying system.                                                                                   | VM snapshots in cloud environments.                                                             |
| **Retention Policy**     | Rules defining **how long backups are stored** (e.g., short-term: 7 days, medium-term: 30 days, long-term: 12+ months).                                                                                           | *"7-day hot backups + 30-day cold backups + 1-year archival."*                                 |
| **Redundancy**          | **Duplication** of backups across **geographical locations** or **storage media** (e.g., on-prem + cloud). Mitigates single-point failures.                                                                                 | *"3 copies: 2 on-premises, 1 in multi-region cloud storage."*                                  |
| **Storage Tier**        | **Performance vs. cost trade-off** for backup storage:                                                                                                                                                         |                                                                                                 |
| - **Hot Storage**       | Fast access (e.g., NAS, SAN), ideal for **frequent restores**.                                                                                                                                                 | Primary disk backups for disaster recovery drills.                                             |
| - **Warm Storage**      | Balanced cost/performance (e.g., cloud S3 Standard).                                                                                                                                                               | Monthly backups stored in a regional cloud bucket.                                             |
| - **Cold Storage**      | Low cost, slower access (e.g., cloud Glacier, tape). Used for **long-term archival**.                                                                                                                                | Annual backups stored in cold cloud storage.                                                    |
| **Backup Validation**    | **Testing** backups to ensure **restorability** (e.g., point-in-time recovery tests).                                                                                                                                | Monthly restore drills for critical databases.                                                  |
| **Automation**          | **Scheduled, scripted, or orchestrated** backup processes to reduce human error.                                                                                                                                     | Cron jobs for nightly backups + automated alerts for failures.                                |
| **Immutable Backups**   | Backups **cannot be altered or deleted** (e.g., WORM storage, cloud object locking). Prevents ransomware corruption.                                                                                                   | Backups stored in S3 Object Lock or tape with write-once policies.                              |

---

## **Implementation Schema**

Below is a **structured schema** for defining a backup strategy. Customize fields based on your environment.

| **Category**            | **Field**               | **Description**                                                                                                                                                                                                 | **Example Values**                                                                                     |
|-------------------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Scope**               | **System/Application**  | Target system/database/application (e.g., "PostgreSQL," "Linux file server").                                                                                                                                  | `MySQL DB Cluster`, `Active Directory`, `VMWare ESXi Hosts`                                          |
|                         | **Data Volume**         | Estimated size of data to back up (e.g., "100GB").                                                                                                                                                               | `500TB`, `10GB`                                                                                       |
|                         | **Criticality**         | Impact if data is lost (e.g., "Critical," "High," "Medium," "Low").                                                                                                                                             | `Critical`, `High`                                                                                     |
| **Backup Type**         | **Primary Strategy**    | Selected backup type(s) (`Full`, `Incremental`, `Differential`, `Snapshot`).                                                                                                                                     | `Full (daily) + Incremental (hourly)`                                                                |
|                         | **Secondary Strategy**  | Fallback strategy (e.g., "Air-gapped tapes," "Multi-cloud replication").                                                                                                                                         | `Tape backup for cold storage`                                                                       |
| **Frequency**           | **Full Backups**        | How often full backups occur (e.g., "Daily," "Weekly").                                                                                                                                                           | `Weekly (Sun 2AM)`                                                                                     |
|                         | **Incremental/Diff**    | How often incremental/differential backups occur (e.g., "Hourly," "Every 15 min").                                                                                                                                 | `Hourly (7x/day) + 15-min during business hours`                                                      |
| **Retention Policy**    | **Short-Term (Hot)**    | Duration backups are stored in hot/cold storage (e.g., "7 days," "30 days").                                                                                                                                      | `7 days (hot) + 30 days (warm)`                                                                       |
|                         | **Medium-Term (Warm)**  |                                                                                                                                                                                                                 | `90 days (warm)`                                                                                      |
|                         | **Long-Term (Cold)**    |                                                                                                                                                                                                                 | `12 months (cold) + 5 years (archival)`                                                               |
| **Destinations**        | **Primary Location**    | Where primary backups are stored (e.g., "On-prem NAS," "AWS S3").                                                                                                                                                 | `Local Veeam Backup Server`, `Azure Blob Storage (Region A)`                                         |
|                         | **Secondary Location**  | Redundant location (e.g., "Cloud DR site," "Offsite tape vault").                                                                                                                                                 | `AWS S3 (Region B)`, `Iron Mountain Vault`                                                           |
|                         | **Tertiary Location**   | Optional third copy (e.g., "Another cloud region," "Air-gapped tape").                                                                                                                                             | `Backblaze B2 (Global)`                                                                            |
| **Storage Tier**        | **Hot Storage**         | Storage type for hot backups (e.g., "NAS," "Azure Blob Standard").                                                                                                                                                 | `Dell PowerScale`, `AWS S3 Standard`                                                                |
|                         | **Warm Storage**        |                                                                                                                                                                                                                 | `AWS S3 Intelligent-Tiering`                                                                      |
|                         | **Cold Storage**        |                                                                                                                                                                                                                 | `AWS Glacier Deep Archive`, `IBM Cold Storage`                                                      |
| **Validation**          | **Restore Testing**     | How often backups are tested (e.g., "Monthly," "Quarterly").                                                                                                                                                     | `Quarterly full restore drills`                                                                      |
|                         | **Point-in-Time (PITR)** | Whether point-in-time recovery is supported (e.g., "Yes (5-min granularity)," "No").                                                                                                                                | `Yes (1h granularity for DBs)`                                                                       |
| **Automation**          | **Scheduling**          | Tool/framework used (e.g., "Cron," "Veeam," "AWS Backup").                                                                                                                                                           | `Veeam Agent for Linux`, `Terraform + AWS Backup`                                                   |
|                         | **Alerting**            | How failures are notified (e.g., "Slack," "Email," "PagerDuty").                                                                                                                                                 | `Slack + Email`, `Datadog Alerts`                                                                  |
| **Immutable Protection**| **WORM Enabled**        | Whether backups are write-once-readable-many (e.g., "Yes," "No").                                                                                                                                               | `Yes (S3 Object Lock)`                                                                        |
| **Compliance**          | **Regulatory Rules**    | Applicable laws (e.g., "GDPR," "HIPAA," "SOC2").                                                                                                                                                               | `GDPR (7-year retention)`, `HIPAA (6-year retention for PHI)`                                       |
| **Disaster Recovery**   | **RTO**                 | Maximum acceptable downtime (e.g., "4h," "24h").                                                                                                                                                                   | `4h for critical apps`, `24h for non-critical`                                                      |
|                         | **RPO**                 | Maximum acceptable data loss (e.g., "5 min," "1h").                                                                                                                                                               | `5 min for financial systems`, `1h for analytics`                                                   |

---

## **Query Examples**

### **1. Schema Validation (Check Backup Strategy Compliance)**
Use this SQL-like pseudocode to validate a backup strategy against RTO/RPO:

```sql
SELECT
    system_name,
    backup_strategy_type,
    last_full_backup_time,
    last_incremental_backup_time,
    retention_days_hot,
    retention_days_cold,
    primary_destination,
    secondary_destination,
    rto,
    rpo
FROM backup_strategies
WHERE
    last_full_backup_time > (CURRENT_TIMESTAMP - INTERVAL '7 days')
    AND retention_days_hot < 7  -- Ensures short-term backups don’t expire too soon
    AND (primary_destination = 'S3' OR secondary_destination IS NOT NULL);  -- Redundancy check
```

**Output Example:**
| `system_name`       | `backup_strategy_type` | `last_full_backup_time` | `retention_days_hot` | `rto` | **Compliant?** |
|---------------------|------------------------|--------------------------|-----------------------|-------|----------------|
| `PostgreSQL DB`     | `Full (Sun) + Incremental (Hourly)` | `2024-05-15 02:00:00` | `7` | `4h` | ✅ Yes          |
| `File Server`       | `Differential (Daily)` | `2024-05-14 23:00:00` | `5` | `24h` | ❌ No (Hot retention <7) |

---

### **2. Capacity Planning (Estimate Storage Needs)**
Calculate total storage required for a backup strategy:

```python
def estimate_backup_storage(systems: list[dict], days_retention_hot: int, days_retention_cold: int):
    total_hot_storage = 0
    total_cold_storage = 0

    for system in systems:
        # Hot storage: last `days_retention_hot` backups
        hot_backups = days_retention_hot * system["backup_interval_hours"]
        total_hot_storage += system["data_size_gb"] * hot_backups

        # Cold storage: remaining backups
        cold_backups = system["retention_total_days"] - days_retention_hot
        total_cold_storage += system["data_size_gb"] * cold_backups

    return {
        "hot_storage_gb": total_hot_storage,
        "cold_storage_gb": total_cold_storage
    }

# Example:
systems = [
    {"name": "ERP Database", "data_size_gb": 100, "backup_interval_hours": 1, "retention_total_days": 365},
    {"name": "File Shares", "data_size_gb": 500, "backup_interval_hours": 24, "retention_total_days": 90}
]
print(estimate_backup_storage(systems, days_retention_hot=7, days_retention_cold=365))
```
**Output:**
```json
{
  "hot_storage_gb": 700,  // 100GB/day * 7 days + 500GB/week * 7 days
  "cold_storage_gb": 182,500  // ERP: 100GB/year * 358 days + Files: 500GB/year * 83 weeks
}
```

---

### **3. Retention Policy Enforcement (Purge Old Backups)**
Automate cleanup of expired backups (e.g., Python script):

```bash
#!/bin/bash
# Purge backups older than `retention_days` in S3 bucket
RETENTION_DAYS=90
BUCKET="my-backups"
PREFIX="erp-database/"

aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "$PREFIX" \
  --query "Contents[?LastModified <= `$(date -d \"$RETENTION_DAYS days ago\" +%Y-%m-%dT%H:%M:%SZ)`].Key" \
  --output text | xargs -I {} aws s3 rm "s3://$BUCKET/{}" --recursive
```

---

### **4. Recovery Time Validation (Simulate Restore)**
Test if backups meet RTO by simulating a restore:

```plaintext
# Example: Restore a PostgreSQL database from backup
# 1. Stop application: `systemctl stop app-service`
# 2. Restore from backup (Veeam example):
   veeam --restore --db postgresql --backup "2024-05-15_Full" --target "/recovery/db/"
# 3. Verify restored data:
   psql -d recovered_db -c "SELECT COUNT(*) FROM critical_table;"
# 4. Time taken: 30 minutes (meets RTO of 4h)
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Data Partitioning](link)** | Organizes data into logical or physical segments for scalability and management.                                                                                                                          | When **sharding** or **scaling** databases/applications.                                           |
| **[Data Replication](link)** | Copies data across systems to improve **availability** and **failover**.                                                                                                                                      | For **high-availability** (HA) clusters or **disaster recovery**.                                  |
| **[Immutable Infrastructure](link)** | Ensures infrastructure is **stateless** and **reproducible**, simplifying backups.                                                                                                                       | In **cloud-native** or **containerized** environments (e.g., Kubernetes).                         |
| **[Backup-as-a-Service (BaaS)](link)** | Outsources backup operations to a third-party provider (e.g., **AWS Backup, Veeam Cloud Connect**).                                                                                                     | When **in-house expertise is lacking** or **cost efficiency** is needed.                          |
| **[Time-Based Retention](link)** | Automatically **archives or deletes** backups based on **time thresholds** (e.g., GDPR compliance).                                                                                                   | For **legal/regulatory compliance** (e.g., financial, healthcare).                                |
| **[Checksum Validation](link)** | Uses **hashing (SHA-256, CRC32)** to verify backup integrity.                                                                                                                                                  | When **data corruption** is a risk (e.g., network issues, hardware failures).                    |
| **[Disaster Recovery Plan](link)** | Defines **step-by-step procedures** to restore operations after a disaster (includes backups, failover, and testing).                                                                                       | For **large-scale outages** or **critical systems**.                                             |

---

## **Best Practices**
1. **Define Clear RTO/RPO**: Align backups with business impact (e.g., "Financial systems: 5-min RPO, 1h RTO").
2. **Test Restores Regularly**: Validate backups **quarterly** or after major changes.
3. **Use Immutable Storage**: Enable **WORM** (Write Once, Read Many) for critical backups to prevent ransomware.
4. **Leverage Multi-Region Storage**: For **global applications**, store backups in **at least 2 geographically separate locations**.
5. **Automate Everything**: Use **configuration-as-code** (e.g., Terraform, Ansible) for consistent backup policies.
6. **Monitor Backup Health**: Set up **alerts** for failed backups or missed schedules.
7. **Document Recovery Procedures**: Include **step-by-step guides** for different failure scenarios.
8. **Balance Cost and Redundancy**: Cold storage for long-term archival; hot storage for frequent access.
9. **Train Teams**: Ensure **DevOps, DBAs, and admins** know how to restore backups.
10. **Review Retention Policies Annually**: Adjust based on **regulatory changes** or **business needs**.

---
**See Also:**
- [AWS Backup Documentation](https://docs.aws.amazon.com/backup/latest/devguide/)
- [Veeam Backup Strategies](https://www.veeam.com/vacuum.html)
- [NIST SP 800-34: Contingency Planning Guide](https://csrc.nist.gov/publications/detail/sp/800-34/rev-2/final)