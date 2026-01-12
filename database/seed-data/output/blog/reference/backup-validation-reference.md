# **[Pattern] Backup Validation Reference Guide**

---

## **Overview**
Backup validation is a critical process to ensure that data backups are **complete, accurate, readable, and recoverable**. This pattern defines automated and manual methods to verify that backups meet recovery objectives before they become dependencies for business continuity. Failure to validate backups can lead to catastrophic data loss or compliance violations if backups are untested when needed.

This guide covers **key concepts**, **implementation best practices**, **schema references**, and **query examples** for validation workflows. It applies to structured (relational) and unstructured data backups, including databases, file systems, cloud storage, and hybrid environments.

---

## **Implementation Details**

### **Core Principles**
1. **Automation First**: Validate backups in real-time or near-real-time using scripts, frameworks, or specialized tools.
2. **Checksum Integrity**: Verify file integrity using cryptographic hashes (e.g., MD5, SHA-256) or checksums.
3. **Data Sampling**: Randomly sample records to confirm logical/structural consistency (e.g., primary key checks, foreign key constraints).
4. **Role-Based Testing**: Assign owners to validate **individual** backups (e.g., DBAs for SQL backups, sysadmins for file backups).
5. **Reporting & Alerting**: Generate reports and trigger alerts for failed validations to enable remediation.
6. **Periodic Full Validation**: Conduct **full-restoration tests** quarterly/annually to validate recoverability.

---

### **Validation Types**
1. **Structural Validation**
   - Confirm schema (e.g., table names, column counts) matches the live database.
   - Example: Compare `INFORMATION_SCHEMA` in source vs. backup.

2. **Content Validation**
   - Verify data consistency using checksums or record counts.
   - Example: Count rows in `customers` table before/after backup.

3. **Functional Validation**
   - Test restorable backups in a staging environment.
   - Example: Restore a database and run sample queries.

4. **Metadata Validation**
   - Check backup metadata (e.g., timestamps, retention dates, encryption flags).

---

### **Implementation Steps**
1. **Pre-Validation**: Ensure backups are healthy (e.g., no corruption, correct retention).
2. **Basic Checks**: Verify file sizes, permissions, and timestamps.
3. **Deep Validation**: Use checksums or sampling to compare critical data.
4. **Final Test**: Attempt recovery in a non-production environment.

---

## **Schema Reference**

### **Backup Validation Schema (Example)**
| **Field**               | **Description**                                                                 | **Data Type**       | **Notes**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|---------------------|---------------------------------------------------------------------------|
| `backup_id`             | Unique identifier for the backup.                                           | UUID                | Must correlate to backup metadata.                                        |
| `source_system`         | Where the backup originated (e.g., `prod-sql-server`, `s3-bucket`).          | String              | Supports regex patterns for batch validation.                            |
| `validation_type`       | Type of validation (`checksum`, `sampling`, `functional`, `metadata`).       | Enum                | Required for automation pipelines.                                       |
| `expected_checksum`     | Precomputed hash of the backup (MD5/SHA-256).                                | String              | Used for automated integrity checks.                                     |
| `record_sample_size`    | Number of records to sample for validation.                                | Integer             | For large datasets (e.g., `1000` rows for a 1B-row table).              |
| `last_validated`        | Timestamp of the last validation run.                                        | Timestamp           | Critical for compliance audits.                                          |
| `validation_status`     | `passed`, `failed`, `partially_passed`, or `pending`.                        | Enum                | Required for alerting logic.                                              |
| `failed_reasons`        | Array of error messages or missing data.                                     | JSON Array          | Example: `[{"key": "schema_mismatch", "table": "users"}]`.               |
| `restored_in_env`       | Environment where the backup was tested (e.g., `staging-db-1`).               | String              | For functional validation.                                               |
| `automated`             | Boolean flag indicating if validation was automated.                          | Boolean             | Manual validations should be flagged.                                    |
| `validation_users`      | List of users who performed validation.                                     | Array of Strings    | Useful for accountability.                                                |
| `recovery_time_goal`    | Expected recovery time (e.g., `RPO_15min`, `RPO_1hour`).                       | String              | Correlates with SLA compliance.                                           |

---

## **Query Examples**

### **1. Check Backup Integrity with Checksums**
```sql
-- PostgreSQL: Verify backup checksums against expected hashes
SELECT
    backup_id,
    CASE
        WHEN checksum = expected_checksum THEN 'passed'
        ELSE 'failed (checksum mismatch)'
    END AS status
FROM backup_validation_logs
WHERE source_system = 'prod-sql-db'
  AND validation_type = 'checksum';
```

### **2. Sample Content Validation (Python)**
```python
import pandas as pd

# Sample 1000 records from the restored backup
sample = pd.read_sql("SELECT * FROM users LIMIT 1000", restored_connection)

# Compare against live data (e.g., using approximate record counts)
live_count = pd.read_sql("SELECT COUNT(*) FROM users", live_connection).iloc[0, 0]
if sample.shape[0] != live_count:
    print("Validation failed: Sample size mismatch")
```

### **3. Identify Unvalidated Backups**
```sql
-- Find backups not validated in the past 30 days (SQL)
WITH unvalidated AS (
    SELECT backup_id, last_validated
    FROM backups
    WHERE last_validated < NOW() - INTERVAL '30 days'
      AND validation_status != 'passed'
)
SELECT * FROM unvalidated;
```

### **4. Generate Retention Policy Reports**
```sql
-- PostgreSQL: List backups exceeding retention period
SELECT
    backup_id,
    source_system,
    last_validated,
    CASE
        WHEN last_validated < (NOW() - INTERVAL '90 days') THEN 'expired'
        ELSE 'valid'
    END AS retention_status
FROM backups
WHERE retention_days = 90;
```

---

## **Automation Tools & Frameworks**

| **Tool/Framework**       | **Use Case**                                                                 | **Example Integrations**                  |
|--------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Vault (HashiCorp)**    | Encrypted backup validation with role-based access.                        | Kubernetes, AWS.                         |
| **Chef/Puppet**          | Automated validation in DevOps pipelines.                                  | Database backups, file systems.          |
| **AWS Backup + Lambda**  | Schedule and validate AWS EBS/S3 backups.                                   | S3 checksums, RDS log stream validation. |
| **Liquibase**            | Database schema validation.                                                | MySQL, PostgreSQL.                       |
| **Python (`hashlib`)**  | Custom checksum validation scripts.                                        | Any filesystem, cloud storage.           |
| **WAL-G (PostgreSQL)**   | Validate PostgreSQL WAL backups.                                            | AWS S3, GCS.                             |

---

## **Related Patterns**

1. **Backup Retention Policies**
   - Define rules for keeping backups based on RPO/RTO (e.g., 30 days for critical data, 6 months for compliance).
   - *Reference:* [Backup Retention Pattern](link).

2. **Backup Encryption**
   - Encrypt backups at rest and in transit to meet compliance (e.g., GDPR, HIPAA).
   - *Reference:* [Encrypted Backups Pattern](link).

3. **Disaster Recovery (DR) Testing**
   - Simulate a full disaster scenario to validate backup recovery end-to-end.
   - *Reference:* [DR Simulation Pattern](link).

4. **Immutable Backups**
   - Prevent backups from being altered after creation (e.g., AWS S3 Object Lock).
   - *Reference:* [Immutable Storage Pattern](link).

5. **Backup Compression**
   - Optimize storage for large backups (e.g., LZ4 for databases, Zstd for files).
   - *Reference:* [Backup Compression Pattern](link).

6. **Backup Monitoring**
   - Track backup jobs, failures, and recovery times in observability tools (e.g., Prometheus, Datadog).
   - *Reference:* [Backup Observability Pattern](link).

7. **Backup as a Service (BaaS)**
   - Offload backup validation to a third-party provider (e.g., Rubrik, Commvault).
   - *Reference:* [Cloud Backup Services Pattern](link).

---

## **Best Practices**
1. **Validate Before Deletion**
   - Run validation **before** purging backups to avoid losing the only valid copy.

2. **Document Failures**
   - Log reasons for validation failures (e.g., "Schema drift detected").

3. **Test Recovery Paths**
   - Simulate a disaster (e.g., server failure) to confirm backups can be restored.

4. **Combine Automated + Manual Checks**
   - Automate checksums but require manual functional testing (e.g., restore a sample DB).

5. **Align with Compliance**
   - Ensure validation meets SLAs for audit trails (e.g., ISO 27001, SOC 2).

6. **Version Backups**
   - Label backups with version numbers (e.g., `prod-db-v20231001`) for traceability.

7. **Backup Backup Metadata**
   - Store validation logs in a separate, immutable backup.

---

## **Troubleshooting**
| **Symptom**                     | **Likely Cause**                          | **Solution**                                                                 |
|----------------------------------|-------------------------------------------|-----------------------------------------------------------------------------|
| Validation fails with "checksum mismatch" | Corrupted files or incomplete backup.  | Re-run backup; verify disk health.                                          |
| Sample data doesn’t match live | Schema drift or incorrect sampling.     | Compare schemas; adjust sample size or query logic.                        |
| Functional test fails            | Database corruption or environment issues. | Restore from a newer backup; test in a clean environment.                  |
| No validation logs               | Automation skipped or logs deleted.      | Check cron jobs/alerts; review retention policies for logs.                  |
| Slow validation                   | Large backups or inefficient queries.    | Parallelize checks; sample smaller datasets.                                |

---
**Last Updated:** [YYYY-MM-DD]
**Owner:** [Team/Contact]