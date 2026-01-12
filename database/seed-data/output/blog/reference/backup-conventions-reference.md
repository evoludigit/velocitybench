---
# **[Pattern] Backup Conventions Reference Guide**

---

## **Overview**
The **Backup Conventions** pattern defines standardized rules for organizing, naming, and managing backup files and directories to ensure reliability, recoverability, and scalability across systems and applications. This pattern resolves common challenges like versioning conflicts, retention policies, and cross-platform compatibility. By implementing consistent conventions, teams minimize human error, automate recovery processes, and streamline audits. This guide covers naming schemes, directory structures, metadata requirements, and query patterns for querying backup state.

---

## **Key Concepts**

| **Concept**               | **Definition**                                                                                                                                                                                                                         |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Convention**            | A predefined rule (e.g., naming, structure, or metadata format) that all backups must adhere to.                                                                                                                                    |
| **Versioning**            | A system for distinguishing backups by version (e.g., incremental, full, or dated snapshots).                                                                                                                          |
| **Retention Policy**      | Specifies how long backups are retained (e.g., daily for 7 days, monthly for 30 days).                                                                                                                                            |
| **Metadata**              | Structured data (e.g., timestamps, source path, backup type) stored with or alongside backup files to improve queryability.                                                                                             |
| **Encryption**            | Security measure to protect backup integrity and confidentiality (e.g., AES-256 or key-based hashing).                                                                                                                     |
| **Cross-Platform Compatibility** | Ensures backups can be restored across different OSes, cloud providers, or storage systems by avoiding platform-specific naming or dependency conflicts.                                                                  |

---

## **Schema Reference**
Below is the standard schema for organizing backup files and directories.

### **1. Directory Structure**
| **Path Component**       | **Description**                                                                                                                                                                                                             | **Example**                          |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `/backups/`              | Root directory for all backup sets.                                                                                                                                                                                       | `/mnt/data/backups/`                 |
| `/backups/{app-name}/`   | Subdirectory for each application/service.                                                                                                                                                                             | `/backups/app-login-service/`        |
| `/backups/{app-name}/{env}/` | Environment-specific (dev/stage/prod) backup directories to avoid conflicts.                                                                                                                                      | `/backups/app-login-service/prod/`   |
| `/backups/{app-name}/{env}/latest/` | Directory for the most recent backup version (linked to current backup).                                                                                                                                       | `/backups/app-login-service/prod/latest/` |
| `/backups/{app-name}/{env}/v{version}/` | Nested directory for historical versions (e.g., `v1.0`, `v2.0`).                                                                                                                                                     | `/backups/app-login-service/prod/v1.0/` |

---

### **2. File Naming Convention**
| **File Component**       | **Format**                                   | **Description**                                                                                                                                                                       | **Example**                                  |
|--------------------------|----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Backup Type Prefix**   | `full_` or `inc_`                            | Indicates whether the backup is a full or incremental snapshot.                                                                                                                    | `full_2024-05-15.db`                        |
| **Timestamp**            | `YYYY-MM-DD` or `ISO8601` (e.g., `2024-05-15T12:30:00`) | Unambiguous date/time stamp.                                                                                                                                                     | `inc_2024-05-15T15:30:00.gz`                |
| **Extension**            | `.db`, `.sql`, `.tar.gz`, `.enc`, etc.       | Represents the format of the backup (e.g., database dump, archived files).                                                                                                        | `full_2024-05-15.db.sql`                    |
| **Checksum**             | `sha256:` followed by 64-character hash        | Ensures file integrity. Optional but recommended.                                                                                                                                        | `full_2024-05-15.db.sql.sha256:abc123...`  |

---

### **3. Metadata File**
Each backup directory (`/v{version}/`) includes a **metadata file** (`metadata.json`) with structured data:

```json
{
  "backup_date": "2024-05-15T12:30:00Z",
  "backup_type": "full",
  "source_system": "db-prod-01",
  "source_path": "/var/lib/mysql/data",
  "retention_days": 30,
  "encryption": {
    "algorithm": "AES-256",
    "key_id": "abc123"
  },
  "checksum": "sha256:abc123...",
  "tags": ["prod", "critical"]
}
```

---

## **Implementation Requirements**
### **1. Naming Rules**
- **Do**:
  - Use lowercase letters and hyphens for clarity.
  - Include timestamps in ISO8601 format for global compatibility.
  - Prepend backup type (`full_`, `inc_`) to avoid ambiguity.
- **Avoid**:
  - Spaces or special characters in paths/filenames.
  - Platform-specific extensions (e.g., `.bak` without format specificity).

### **2. Directory Permissions**
| **Directory**                     | **Permissions** | **Reason**                                                                         |
|------------------------------------|-----------------|-------------------------------------------------------------------------------------|
| `/backups/`                       | `750`           | Restrict access to admins only.                                                     |
| `/backups/{app-name}/{env}/`      | `750`           | Environment isolation.                                                               |
| Individual backup files           | `640` or `600`  | Restrict read/write to the backup service account.                                   |

### **3. Retention Policy Enforcement**
| **Retention Level** | **Days** | **Action**                                                                                            | **Example**                          |
|----------------------|----------|-------------------------------------------------------------------------------------------------------|--------------------------------------|
| Daily                | 7        | Delete backups older than 7 days.                                                                     | `rm -rf /backups/{app}/*.db >7 days`   |
| Weekly               | 30       | Retain weekly full backups for 30 days.                                                            | Keep `full_YYYY-MM-DD.db`             |
| Long-term            | 90       | Move to cold storage or archive.                                                                     | `aws s3 cp backups/ s3://archive/ --acl public-read` |

---

## **Query Examples**
### **1. List All Full Backups for an App Within 30 Days**
```bash
find /backups/app-login-service/prod/ -maxdepth 1 -name "full_*.db*" -newermt "30 days ago"
```

### **2. Verify Checksum of a Backup**
```bash
sha256sum /backups/app-login-service/prod/v1.0/full_2024-05-15.db.sql | grep abc123
```

### **3. Check Retention Status (Days Since Backup)**
```bash
for file in /backups/*/*.db*; do
  days_old=$(date -d "$(stat -c %y "$file")" +%s | awk "{print int($1/86400)}")
  echo "File: $file, Age: $days_old days";
done | grep -E 'Age: [0-9]{2,}'
```

### **4. Query Metadata for Backups Tagged "critical"**
```bash
jq '.backup_date, .encryption.key_id' /backups/{app}/prod/v*/metadata.json | grep -E '"tags.*critical"'
```

### **5. Restore Latest Full Backup**
```bash
ln -s /backups/app-login-service/prod/latest/full_2024-05-15.db.sql /restore-point/
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Immutable Backups**     | Prevents accidental deletion/modification of backups by making them read-only after creation.       | High-security environments where tampering is a risk.                                             |
| **Versioned Snapshots**   | Uses immutable timestamps and checksums to track backup versions over time.                       | Applications requiring rollback to previous states (e.g., databases).                                |
| **Cross-Region Replication** | Replicates backups to geographically dispersed locations for disaster recovery.                   | Global applications with low-tolerance for downtime.                                              |
| **Automated Integrity Checks** | Schedules periodic checksum validation to detect corruption.                                       | Long-term archival where data integrity is critical.                                               |
| **Policy-Based Retention** | Enforces retention rules via scripts or tools (e.g., Lifecycle Manager for S3).                   | Automating cleanup of old backups to save storage costs.                                           |

---
### **References**
- [NASA Backup Conventions](https://www.nasa.gov/) (space-grade backup practices).
- [AWS Backup Best Practices](https://docs.aws.amazon.com/backup/latest/devguide/).
- [OpenStack Backup Services](https://docs.openstack.org/).

---
**Last Updated:** *YYYY-MM-DD*
**Maintainer:** *@team-backups*