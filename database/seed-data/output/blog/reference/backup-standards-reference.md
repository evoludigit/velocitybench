# **[Pattern] Backup Standards Reference Guide**

## **Overview**
The **Backup Standards** pattern ensures consistent, reliable, and recoverable data backups across systems and applications. It defines standardized procedures, frequency, retention policies, and recovery protocols to minimize downtime, data loss, and compliance risks. This guide outlines key components, schema references, query examples, and related patterns for implementing robust backup workflows.

---

## **Key Concepts & Implementation Details**

### **1. Core Principles**
- **Consistency**: Uniform backup processes across environments (dev, staging, prod).
- **Reliability**: Verified backups with integrity checks (checksums, validation).
- **Retention**: Clear policies for backup lifecycle (short-term vs. long-term).
- **Recovery**: Documented restore procedures with success metrics.
- **Compliance**: Alignment with legal/regulatory standards (e.g., GDPR, HIPAA).

### **2. Standardized Backup Types**
| **Type**         | **Purpose**                                                                 | **Frequency**       | **Retention**          |
|------------------|-----------------------------------------------------------------------------|---------------------|------------------------|
| **Full Backup**  | Complete dataset copy (baseline)                                            | Monthly/Quarterly   | Long-term (e.g., 12+ mo) |
| **Incremental**  | Captures changes since last backup                                         | Daily/Weekly        | 30–90 days             |
| **Differential** | Captures changes since last *full* backup                                  | Weekly              | 14–30 days             |
| **Snapshot**     | Point-in-time copy (e.g., VM, DB)                                           | On-demand           | 7–30 days              |
| **Log Backup**   | Transaction logs (for recovery points)                                      | Continuous/Real-time| 1–7 days               |

### **3. Backup Validation**
- **Checksums**: Verify data integrity (MD5, SHA-256).
- **Restore Tests**: Periodic dry-runs of recovery procedures (e.g., weekly).
- **Automation**: Use tools (e.g., Ansible, Terraform) to validate backups post-capture.

### **4. Frequencies & Policies**
| **Environment** | **Full Backups** | **Incremental** | **Retention (Days)** | **Restore Goal (RTO)** |
|-----------------|------------------|-----------------|-----------------------|-----------------------|
| Production      | Monthly          | Daily           | 90+                   | ≤4 hours              |
| Staging         | Bi-weekly        | Weekly          | 30                    | ≤24 hours             |
| Development     | Weekly           | Daily           | 14                    | ≤1 hour               |

---
## **Schema Reference**

### **1. Backup Metadata Schema**
```json
{
  "backup_id": "UUIDv4",       // Unique identifier
  "environment": "string",    // e.g., "prod", "staging"
  "type": "string",           // "full", "incremental", "snapshot"
  "capture_time": "ISO8601",  // e.g., "2024-02-15T10:30:00Z"
  "checksum": "string",       // SHA-256 hash of the backup
  "size": "bytes",            // Total backup size
  "status": "string",         // "completed", "failed", "pending"
  "validation": {
    "verified": "boolean",    // True if checksum matches
    "restored": "boolean"     // True if restore test passed
  },
  "retention_end": "ISO8601"  // Scheduled deletion date
}
```

### **2. Backup Policy Schema**
```json
{
  "policy_name": "string",    // e.g., "prod_database_backup"
  "frequency": {
    "full": "string",        // "monthly", "weekly"
    "incremental": "string"  // "daily", "hourly"
  },
  "retention": {
    "full": "number",        // Days
    "incremental": "number"  // Days
  },
  "automation": {
    "tool": "string",        // e.g., "Velero", "AWS Backup"
    "schedule": "CRON"       // e.g., "0 2 * * *" (2 AM daily)
  },
  "compliance": ["string"]   // ["GDPR", "HIPAA"]
}
```

---
## **Query Examples**

### **1. List All Backups for Production (Last 7 Days)**
```sql
SELECT *
FROM backups
WHERE environment = 'prod'
  AND capture_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY capture_time DESC;
```

### **2. Find Unvalidated Backups**
```sql
SELECT backup_id, type, status
FROM backups
WHERE validation.verified = FALSE
  OR validation.restored = FALSE;
```

### **3. Check Retention Compliance (Due for Deletion)**
```sql
SELECT backup_id, capture_time, retention_end
FROM backups
WHERE retention_end <= NOW();
```

### **4. Schedule a New Backup Policy (Terraform Example)**
```hcl
resource "aws_backup_plan" "prod_db_backup" {
  name = "prod-database-backup"

  rule {
    rule_name         = "daily-incremental"
    target            = aws_backup_selection.daily_incremental.id
    schedule          = "cron(0 3 * * ? *)"  # 3 AM daily
    start_window      = 60                  # 1-hour window
    completion_window = 120                 # 2-hour max runtime
    lifecycle {
      delete_after = 30  # Days
    }
  }
}
```

---
## **Related Patterns**

1. **Disaster Recovery (DR) Plan**
   - *Use Case*: Defines roles, escalation paths, and failover procedures alongside backups.
   - *Synergy*: Backup Standards provide the *data* component of DR.

2. **Immutable Backups**
   - *Use Case*: Prevents tampering with backups (e.g., WORM storage).
   - *Synergy*: Enhances trust in backup integrity (complements validation checks).

3. **Versioned Data Stores**
   - *Use Case*: Systems like Git or databases with time-travel queries.
   - *Synergy*: Reduces need for traditional backups (e.g., PostgreSQL logical backups).

4. **Chaos Engineering for Backups**
   - *Use Case*: Test failure scenarios (e.g., simulated data corruption).
   - *Synergy*: Validates backup/restore procedures under stress.

5. **Cross-Region Replication**
   - *Use Case*: Protects against regional outages.
   - *Synergy*: Extends backup Standards to global availability.

---
## **Best Practices**
- **Document Everything**: Keep a living backup policy document with approvals.
- **Monitor Alerts**: Set up notifications for failed backups or validation failures.
- **Offsite Storage**: Store at least one copy in a separate geographic location.
- **User Training**: Ensure teams know how to initiate/restore backups.
- **Cost Optimization**: Use tiered storage (e.g., cheap cold storage for old backups).