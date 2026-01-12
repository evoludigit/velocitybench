# **[Pattern] Backup Setup – Reference Guide**

---

## **Overview**
The **Backup Setup** pattern ensures critical data is protected via automated, scheduled, or on-demand backups. Backups store copies of databases, files, or applications to restore them in case of data loss, corruption, or system failure. This pattern supports **recovery point objectives (RPO)** and **recovery time objectives (RTO)** by defining backup frequency, retention policies, and storage mechanisms.

Common use cases include:
- **Disaster recovery (DR):** Restore systems after severe failures (e.g., ransomware, hardware failure).
- **Compliance & audit:** Meet regulatory requirements (e.g., GDPR, HIPAA) by retaining historical data.
- **Accidental data loss mitigation:** Recover from user errors or unintended deletions.

This guide covers implementation requirements, schema references, and query examples for configuring backups.

---

## **Key Concepts**
| **Concept**               | **Definition**                                                                 | **Example**                          |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **Backup Type**           | How backups are stored (e.g., full, incremental, differential).                | Full backup (complete dataset copy)  |
| **Backup Frequency**      | How often backups occur (daily, hourly, real-time).                           | Daily at 2 AM                       |
| **Retention Policy**      | Rules defining how long backups are kept (e.g., 30 days, weekly snapshots).   | Keep daily backups for 7 days        |
| **Storage Location**      | Where backups are stored (on-prem, cloud, tape, local disk).                   | AWS S3, local NAS drive             |
| **Encryption**            | Security measures to protect backup data (e.g., AES-256, TLS).               | Encrypted backups in transit/at rest |
| **Verification**          | Methods to confirm backup integrity (checksums, restore tests).                | Weekly restore test                  |

---

## **Schema Reference**

### **1. Backup Configuration Schema**
| **Field**          | **Type**   | **Description**                                                                 | **Required** | **Default** |
|--------------------|------------|---------------------------------------------------------------------------------|--------------|-------------|
| `backup_id`        | String     | Unique identifier for the backup job.                                           | Yes          | Auto-gen    |
| `name`             | String     | Descriptive name for the backup job (e.g., "Database-Backup").                 | Yes          | -           |
| `type`             | Enum       | Backup type (`full`, `incremental`, `differential`, `snapshot`).                | Yes          | -           |
| `schedule`         | Object     | Cron expression or fixed schedule (e.g., `0 2 * * *` for daily at 2 AM).       | Yes          | -           |
| `source`           | Object     | Source details (e.g., database name, file path).                              | Yes          | -           |
| `destination`      | Object     | Storage location (e.g., `s3://bucket/prefix`, `/mnt/backups`).                  | Yes          | -           |
| `retention_policy` | Object     | Rules for deletion (e.g., `keep_daily_for: 7`, `keep_monthly_for: 12`).        | Yes          | -           |
| `encryption`       | Object     | Encryption settings (e.g., `algorithm: AES-256`, `key_id: ...`).                | No           | Unencrypted |
| `verification`     | Boolean    | Enable restore verification after backup.                                      | No           | `false`     |

#### **Schema Example (JSON)**
```json
{
  "backup_id": "db-backup-001",
  "name": "prod-database-full-backup",
  "type": "full",
  "schedule": { "cron": "0 2 * * *" },  // Daily at 2 AM
  "source": {
    "database": {
      "name": "production_db",
      "host": "db-prod.example.com",
      "port": 5432
    }
  },
  "destination": {
    "s3": {
      "bucket": "backups-prod",
      "prefix": "database/production_db/"
    }
  },
  "retention_policy": {
    "keep_daily_for": 7,
    "keep_weekly_for": 4,
    "keep_monthly_for": 12
  },
  "encryption": {
    "algorithm": "AES-256",
    "key_id": "arn:aws:kms:us-east-1:123456789012:key/abcd1234"
  },
  "verification": true
}
```

---

### **2. Backup Status Schema**
| **Field**          | **Type**   | **Description**                                                                 | **Example**          |
|--------------------|------------|---------------------------------------------------------------------------------|----------------------|
| `backup_id`        | String     | ID of the backup job.                                                          | `db-backup-001`      |
| `status`           | Enum       | Current state (`pending`, `in_progress`, `completed`, `failed`, `archived`).     | `completed`          |
| `start_time`       | Timestamp  | When the backup began.                                                          | `2024-05-20T02:00:00Z` |
| `end_time`         | Timestamp  | When the backup finished (or failed).                                           | `2024-05-20T03:15:42Z` |
| `size`             | String     | Estimated backup size (e.g., `12.5GB`).                                        | `12.5GB`             |
| `errors`           | Array      | List of error messages (if any).                                               | `[{"code": "E001", "msg": "Permission denied"}]` |

#### **Schema Example (JSON)**
```json
{
  "backup_id": "db-backup-001",
  "status": "completed",
  "start_time": "2024-05-20T02:00:00Z",
  "end_time": "2024-05-20T03:15:42Z",
  "size": "12.5GB",
  "errors": []
}
```

---

## **Query Examples**

### **1. Create a Backup Job**
**Request (HTTP POST)**
```http
POST /api/v1/backups
Content-Type: application/json

{
  "name": "app-files-backup",
  "type": "full",
  "schedule": { "cron": "0 3 * * 0" },  // Weekly on Sunday at 3 AM
  "source": {
    "filesystem": {
      "path": "/var/www/app-data",
      "exclude": [".git", "tmp/"]
    }
  },
  "destination": {
    "local": {
      "path": "/mnt/backups/app_data"
    }
  },
  "retention_policy": {
    "keep_weekly_for": 4
  }
}
```

**Response (201 Created)**
```json
{
  "backup_id": "files-backup-001",
  "status": "pending",
  "next_run": "2024-05-26T03:00:00Z"
}
```

---

### **2. List All Backup Jobs**
**Request (HTTP GET)**
```http
GET /api/v1/backups
```

**Response (200 OK)**
```json
[
  {
    "backup_id": "db-backup-001",
    "name": "prod-database-full-backup",
    "type": "full",
    "status": "completed",
    "last_run": "2024-05-20T03:15:42Z"
  },
  {
    "backup_id": "files-backup-001",
    "name": "app-files-backup",
    "type": "full",
    "status": "pending",
    "next_run": "2024-05-26T03:00:00Z"
  }
]
```

---

### **3. Trigger a Manual Backup**
**Request (HTTP POST)**
```http
POST /api/v1/backups/files-backup-001/run
```

**Response (202 Accepted)**
```json
{
  "backup_id": "files-backup-001",
  "status": "in_progress",
  "start_time": "2024-05-20T14:30:00Z"
}
```

---

### **4. Check Backup Status**
**Request (HTTP GET)**
```http
GET /api/v1/backups/db-backup-001/status
```

**Response (200 OK)**
```json
{
  "backup_id": "db-backup-001",
  "status": "completed",
  "start_time": "2024-05-20T02:00:00Z",
  "end_time": "2024-05-20T03:15:42Z",
  "size": "12.5GB",
  "errors": []
}
```

---

### **5. Restore from Backup**
**Request (HTTP POST)**
```http
POST /api/v1/backups/db-backup-001/restore
{
  "target": {
    "database": {
      "name": "production_db_restored",
      "host": "db-restore.example.com"
    }
  }
}
```

**Response (202 Accepted)**
```json
{
  "restore_id": "db-restore-001",
  "status": "in_progress",
  "backup_id": "db-backup-001",
  "target": "db-restore.example.com:production_db_restored"
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                          |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **[Disaster Recovery]**   | Defines strategies to recover systems after catastrophic failures.              | Recover from ransomware or hardware failure. |
| **[Data Replication]**    | Synchronizes data across multiple locations for high availability.               | Ensure low RTO during region outages. |
| **[Immutable Backups]**   | Prevents backups from being altered or deleted accidentally.                   | Protect against ransomware.          |
| **[Versioned Storage]**   | Tracks changes to data over time (e.g., Git-like history).                     | Revert to previous data states.      |
| **[Backup Monitoring]**   | Tracks backup health and alerts on failures.                                  | Proactively detect backup issues.   |

---

## **Best Practices**
1. **Test Restores:** Regularly verify backups can be restored (e.g., weekly).
2. **Encryption:** Always encrypt backups in transit and at rest.
3. **Retention:** Align retention policies with compliance (e.g., 7 years for legal).
4. **Offsite Storage:** Store critical backups in a separate geographic location.
5. **Automation:** Use cron jobs or orchestration tools (e.g., Terraform, Ansible) for consistency.

---
**Last Updated:** [Insert Date]
**Version:** 1.2