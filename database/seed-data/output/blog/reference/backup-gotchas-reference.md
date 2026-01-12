# **[Pattern] Backup Gotchas: Reference Guide**

---

## **Overview**
Backups are a critical safeguard against data loss, but misconfigurations or oversight can turn them into a false sense of security. The **"Backup Gotchas"** pattern documents common pitfalls—from missing critical data to corruption, inefficiency, or legal/regulatory risks—that compromise backup reliability. This guide outlines key failure modes, detection strategies, and mitigation techniques to ensure backups remain resilient, recoverable, and trustworthy.

---

## **Core Concepts**
Backup "gotchas" are hidden or overlooked issues that undermine backup effectiveness. They typically fall into these categories:

| **Category**          | **Description**                                                                 | **Impact**                                                                 |
|-----------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Data Inclusion**    | Backups omit critical data, databases, or application states.                  | Incomplete recovery; critical systems unreachable.                         |
| **Integrity**         | Corruption, checksum errors, or silent failures render backups unusable.      | Failed recovery attempts; wasted operational time.                        |
| **Performance**       | Backups consume excessive resources (storage, bandwidth, CPU).                | Degraded system performance; missed backup windows.                       |
| **Retention/Compliance** | Non-compliance with SLAs or legal retention periods.                         | Legal risks (e.g., GDPR violations), audits fail, or lost evidence.       |
| **Recovery Complexity** | Overly complex recovery processes delay or prevent restores.                 | Business downtime; operational inefficiency.                              |
| **Technical Debt**    | Unmaintained backups (e.g., outdated software, unsupported storage).          | Unsupported restore paths; security vulnerabilities.                      |
| **Human Error**       | Misconfigured policies, manual oversight failures, or lack of testing.        | Silent corruption; undetected gaps in coverage.                           |

---

## **Schema Reference**
Use this schema to assess and document backup gotchas within your environment.

| **Field**               | **Description**                                                                 | **Example Values**                                                                 |
|--------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Gotcha Category**      | Classification (e.g., Data Inclusion, Integrity, Performance).                 | `Data Inclusion`, `Integrity`, `Compliance`                                         |
| **Failure Mode**         | Specific issue (e.g., "Missing database snapshots," "Checksum mismatches").    | `Orphaned backup chains`, `Unencrypted backups`, `Exceeding storage quotas`      |
| **Root Cause**           | Likely trigger (e.g., misconfigured cron jobs, unsupported file systems).       | `Improper retention policy`, `Lack of checksum validation`, `Third-party tool bugs` |
| **Detection Method**     | How to identify (e.g., logs, metrics, automated checks).                      | `Monitor backup job completion rates`, `Run consistency tests`, `Audit retention logs` |
| **Mitigation Strategy**  | Fix or workaround (e.g., enable checksums, test restores quarterly).           | `Automate validation scripts`, `Enforce retention policies`, `Use supported storage media` |
| **Severity**             | Impact level (Critical/High/Medium/Low).                                      | `High` (full system restore risk), `Medium` (partial data loss)                 |
| **Owner**                | Responsible team/role (e.g., DevOps, Compliance).                             | `Backup Team`, `Security`, `Application Owner`                                    |
| **Documentation Link**   | Reference to internal docs or tools.                                           | `Confluence: Backup Policy v3`, `Tool: Veeam Verification Dashboard`              |

---

## **Query Examples**
Use these queries to detect backup gotchas in your environment.

---

### **1. Missing or Stale Backups (Data Inclusion Gotcha)**
**Objective**: Identify backup jobs that failed, were skipped, or produce incomplete data.

#### **Log-Based Query (ELK/CloudWatch)**
```sql
logs
| where (status == "Failed" OR status == "Partial" OR (start_time > last_success_time - 2d))
| summarize count() by backup_type, source_system
| sort by count desc
```
**Key Indicators**:
- Jobs with `status: Failed` or `Partial`.
- Gaps in `last_success_time` exceeding retention windows.

---

#### **Script-Based Check (Python Example)**
```python
import subprocess

def check_backup_completeness(job_name):
    result = subprocess.run(
        ["/opt/backup-tools/check_backup", job_name],
        capture_output=True,
        text=True
    )
    if "Critical data missing" in result.stderr:
        raise BackupWarning(f"{job_name}: {result.stderr.strip()}")
```
**Expected Output**:
```
WARNING: [Job: DB_SNAPSHOT] - Missing table: orders_2023
```

---

### **2. Integrity Issues (Checksum Mismatches)**
**Objective**: Verify backup files against checksums to catch corruption.

#### **Using `md5sum` (Linux)**
```bash
# Compare checksums of backup files against a manifest
diff -q checksums.txt <(md5sum /mnt/backup/*.tar.gz | sort)
```
**Gotcha**: If `diff` outputs lines, the backups are corrupted.

---

#### **Automated Validation (Bash Script)**
```bash
#!/bin/bash
BACKUP_DIR="/mnt/backup"
CHECKSUMS="checksums.csv"

while read -r line; do
    hash=$(echo "$line" | awk '{print $1}')
    file=$(echo "$line" | awk '{print $2}')
    actual_hash=$(md5sum "$BACKUP_DIR/$file" | awk '{print $1}')
    if [ "$hash" != "$actual_hash" ]; then
        echo "ERROR: Checksum mismatch for $file" >> /var/log/backup_warnings.log
    fi
done < "$CHECKSUMS"
```

---

### **3. Performance Bottlenecks (Resource Consumption)**
**Objective**: Detect backups causing storage or CPU overload.

#### **CloudWatch Metric Query (AWS)**
```sql
metric_filter "BackupJobStatus"
| where JobStatus == "InProgress"
| filter CPUUtilization > 90 OR DiskSpaceUsed > 80% of 100GB
| sort by CPUUtilization desc
```
**Gotcha**: Backups exceeding SLA thresholds (e.g., >90% CPU for >1h).

---

#### **Terraform Check (Infrastructure-as-Code)**
```hcl
resource "aws_sns_topic_policy" "backup_alert" {
  arn    = aws_sns_topic.backup_alert.arn
  policy = data.aws_iam_policy_document.alert_policy.json
}

data "aws_iam_policy_document" "alert_policy" {
  statement {
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.backup_alert.arn]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:events:*:*:rule/backup-alert"]
    }
  }
}
```
**Trigger**: Alert when `CPUUtilization` or `DiskReadOps` spikes during backups.

---

### **4. Compliance Violations (Retention/Legal Risks)**
**Objective**: Ensure backups meet regulatory retention periods (e.g., GDPR: 7 years).

#### **SQL Query (PostgreSQL)**
```sql
SELECT
    backup_id,
    DATEDIFF(day, backup_time, CURRENT_DATE) AS days_since_backup,
    retention_period_years
FROM backups
WHERE days_since_backup > retention_period_years * 365;
```
**Gotcha**: Backups exceeding retention periods (high legal risk).

---

### **5. Recovery Complexity (Test Failures)**
**Objective**: Identify backups that fail during restore tests.

#### **JIRA Query (Confluence/CSV Export)**
```
status = "Failed" AND project = "Backup-Tests" AND created > -30d
```
**Key Metric**: >5% restore failures in QA environments.

---

## **Detection Tools**
| **Tool**               | **Purpose**                                                                 | **Example Use Case**                                                      |
|-------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Veeam Backup & Replication** | Integrity checks, job monitoring.                                           | Detects orphaned backups.                                                 |
| **AWS Backup Insights**  | Cloud-native backup analysis (e.g., resource usage trends).                 | Alerts when backup jobs exceed CPU quotas.                                  |
| **OpenSCAP (Compliance)** | Audit retention policies against frameworks (e.g., NIST).                 | Flags backups not meeting GDPR 7-year retention.                            |
| **Custom Scripts (Bash/Python)** | Checksum validation, log parsing.                                        | Verify S3 backups against local checksums.                                  |
| **Terraform/CloudFormation** | Enforce SLAs (e.g., max backup window).                                  | Enforce "backups must complete within 2h."                                  |

---

## **Mitigation Strategies**
| **Gotcha**               | **Mitigation**                                                                 | **Implementation**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Missing Data**          | Automate coverage validation.                                                 | Use tools like [Grailio](https://grailio.com/) or custom scripts to cross-check backup snapshots vs. live systems. |
| **Corruption**            | Enable checksums + daily integrity tests.                                    | Configure `rsync --checksum` or `tar --checkpoint`.                               |
| **Performance Issues**    | Schedule backups during off-peak hours; tier storage (e.g., cold/hot).     | Use AWS Lifecycle Policies or Azure Blob Storage tiers.                           |
| **Compliance Risks**      | Enforce retention policies via tools like **Scality Ring** or **Backblaze**. | Deploy retention hooks in Terraform: `lifecycle_rule = { expiration_days = 2555 }`. |
| **Recovery Failures**     | Test restores quarterly.                                                      | Automate restore tests with [TestDrive](https://github.com/testdriveio/testdrive). |
| **Technical Debt**        | Deprecate unsupported backups; migrate to modern formats (e.g., VSS).      | Audit backup tools with [BackupAgents.io](https://backupagents.io/).              |
| **Human Error**           | Automate alerts + reduce manual intervention.                                | Set up Slack/Teams alerts for failed backups (e.g., [SnapCenter](https://docs.netapp.com/us-en/snapcenter/). |

---

## **Query Templates for Common Scenarios**
| **Scenario**                  | **Query Template**                                                                 |
|--------------------------------|-----------------------------------------------------------------------------------|
| **Orphaned Backups**           | `find /mnt/backup -type f -mtime +30d ! -path "*checksum*"`                      |
| **Unencrypted Backups**        | `grep -r "encryption: off" /etc/backup-config/ | sort`                                |
| **Backup Job Failures**        | `journalctl -u backup.service --since "1d ago" | grep "Failed"`                      |
| **Storage Quota Exceeded**     | `df -h | grep /mnt/backup; if [ $(df -h /mnt/backup | awk '{print $5}' | cut -d'%' -f1) -gt 95 ]; then alert; fi` |

---

## **Related Patterns**
1. **[Idempotent Backups]** – Design backups to safely rerun without corruption.
   - *Key Idea*: Use atomic snapshots (e.g., ZFS send/receive) to ensure consistency.
   - *Reference*: [ZFS Best Practices](https://zfsonlinux.org/wiki/ZFS_Best_Practices).

2. **[Backup Verification Automations]** – Automate integrity checks post-backup.
   - *Key Idea*: Integrate checksum validation into CI/CD (e.g., GitHub Actions).
   - *Example*: [Backup Verification Script](https://github.com/librecoresystems/backup-verify).

3. **[Disaster Recovery Playbooks]** – Document step-by-step recovery procedures.
   - *Key Idea*: Include "Gotchas" section in playbooks (e.g., "If backup fails, use shadow copies").
   - *Template*: [AWS Disaster Recovery Guide](https://aws.amazon.com/dr/).

4. **[Immutable Storage for Backups]** – Prevent ransomware tampering.
   - *Key Idea*: Store backups in WORM (Write Once, Read Many) storage (e.g., Azure Immutable Blobs).
   - *Risk Mitigated*: Backup corruption by malicious actors.

5. **[Backup Testing Framework]** – Simulate failure scenarios (e.g., disk death).
   - *Key Idea*: Use tools like [Chaos Engineering](https://www.chaosengineering.io/) to test restore paths.
   - *Example*: [Gremlin for Backups](https://gremlin.com/).

---

## **Audit Checklist**
Use this checklist to proactively identify backup gotchas:
- [ ] **Data Inclusion**: Do backups cover all critical databases/applications?
- [ ] **Integrity**: Are checksums validated post-backup?
- [ ] **Performance**: Are backups scheduled during off-peak hours?
- [ ] **Retention**: Do backups meet legal/compliance SLAs?
- [ ] **Recovery**: Have restores been tested in the last 90 days?
- [ ] **Technical Debt**: Are deprecated backup tools still in use?
- [ ] **Human Error**: Are backup alerts monitored 24/7?
- [ ] **Immutability**: Are backups protected from tampering?

---
**Note**: Document findings in a **Backup Risk Register** (template [here](https://www.metrigy.com/resources/backup-risk-register-template/)).

---
**Last Updated**: `[Insert Date]`
**Version**: `1.2`