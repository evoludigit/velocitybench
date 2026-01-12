# **Debugging the Backup Migration Pattern: A Troubleshooting Guide**
*For senior backend engineers troubleshooting data migration failures, inconsistencies, or performance issues in backup-based migration workflows.*

---

## **1. Introduction**
The **Backup Migration Pattern** involves taking a consistent backup of data, restoring it to a staging environment, and then migrating to the target system while minimizing downtime. While reliable, this pattern can fail due to backup corruption, network issues, schema mismatches, or application inconsistencies.

This guide focuses on **quick root-cause analysis** and **practical fixes** for common Backup Migration issues.

---

## **2. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

| ✅ **Symptom** | **Likely Cause** | **Severity** |
|---------------|------------------|-------------|
| Backup files are incomplete or corrupted (`checksum mismatches`) | Disk failures, interrupted processes, or invalid backup tools | Critical |
| Migration fails with "Schema mismatch" errors | Target DB schema differs from source DB | Critical |
| Slow migration performance (`high CPU, I/O bottlenecks`) | Large dataset, inefficient batching, or network latency | High |
| Application crashes after migration (`foreign key violations`) | Data integrity issues (orphaned records, etc.) | High |
| Backup restore hangs (`timeout errors`) | Network issues, storage performance, or deadlocks | High |
| Post-migration queries return incorrect results (`stale data`) | Backup snapshot not reflecting latest state | Medium |

---
## **3. Common Issues & Fixes**
### **3.1 Backup Corruption or Inconsistency**
**Symptoms:**
- `pg_verifybackups` (PostgreSQL) or `mysqldump --check` fails.
- Restore gives `CRC errors` or `disk full` warnings.

**Root Causes:**
- Incomplete backup (e.g., interrupted `mysqldump` or `pg_basebackup`).
- Filesystem corruption.
- Backup tool misconfiguration (e.g., `pg_dump` without `--lock-none`).

**Fixes:**
#### **A. Recover an Incomplete Backup (PostgreSQL)**
```bash
# Check backup integrity
pg_verifybackups -d /path/to/backup

# If corrupted, restore from a known-good backup
pg_restore -U postgres -d target_db -C /path/to/good/backup
```

#### **B. Fix MySQL Backup Corruption**
```bash
# Use `--single-transaction` flag in mysqldump
mysqldump --single-transaction --routines --triggers db_name > db.dump

# Verify dump (if possible) before restoring
mysqlcheck --check --silent db_name < db.dump
```

#### **C. Pre-Backup Validation**
```python
# Python example: Check backup file size & metadata
import os
backup_path = "/backups/db_20240501"
if os.path.getsize(backup_path) < expected_size:
    raise RuntimeError("Backup is incomplete!")
```

---

### **3.2 Schema Mismatch**
**Symptoms:**
```
ERROR: schema "public" does not exist
ERROR: column "new_column" does not exist
```

**Root Causes:**
- Target DB has a different schema (e.g., dropped columns).
- Backup was taken with an older schema version.

**Fixes:**
#### **A. Script to Compare Schemas**
```bash
# Compare schemas (PostgreSQL)
pg_dump -s source_db > schema.sql
pg_dump -s target_db > target_schema.sql
diff schema.sql target_schema.sql
```

#### **B. Automated Migration Script (Python)**
```python
import psycopg2
from sqlparse import parse

def migrate_schema(source_conn, target_conn):
    with source_conn.cursor() as cur:
        cur.execute("SELECT pg_get_tabledef('users')")
        table_def = cur.fetchone()[0]

    # Apply to target DB (adjust for schema differences)
    with target_conn.cursor() as cur:
        cur.execute(table_def)
        target_conn.commit()
```

#### **C. Use Schema Versioning**
```yaml
# Schema versioning in config (example)
schema_version: "v2.1"
pre_migration_steps:
  - ALTER TABLE users ADD COLUMN preferred_language VARCHAR(20)
```

---

### **3.3 Slow Migration Performance**
**Symptoms:**
- Migration takes hours instead of minutes.
- High CPU/Disk I/O during restore.

**Root Causes:**
- Large dataset with no batching.
- Network bottlenecks (e.g., S3 restore over slow connection).
- Missing indexes in target DB.

**Fixes:**
#### **A. Batch Inserts (PostgreSQL)**
```sql
-- Process in chunks (e.g., 10k rows at a time)
INSERT INTO target.users (id, email) VALUES
(1, 'a@example.com'), (2, 'b@example.com'), ...
WHERE NOT EXISTS (SELECT 1 FROM target.users WHERE id = new.id);
```

#### **B. Parallelize with `pg_rewind` (PostgreSQL)**
```bash
# Rewind and copy data in parallel
pg_rewind --target-pgdata /path/to/target --source-pgdata /path/to/source
```

#### **C. Use External Tools for Large Datasets**
```bash
# For MySQL: Use pt-table-sync (Percona Toolkit)
pt-table-sync --sync-to-master --replicate-rows 1000 --chunk-size 5000
```

---

### **3.4 Data Integrity Issues (Foreign Key Violations)**
**Symptoms:**
```
ERROR: insert or update on table "orders" violates foreign key constraint
```

**Root Causes:**
- Orphaned records in the backup.
- Transactional integrity broken (e.g., partial writes).

**Fixes:**
#### **A. Check Referential Integrity Before Migration**
```sql
-- Find orphaned records (PostgreSQL)
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM orders);
```

#### **B. Use `ON CONFLICT DO NOTHING` or `IGNORE`**
```sql
-- Example for PostgreSQL
INSERT INTO target.users (id, email)
VALUES (1, 'test@example.com')
ON CONFLICT (id) DO NOTHING;
```

#### **C. Rebuild Constraints After Insert**
```sql
-- Disable constraints, insert, then re-enable
ALTER TABLE orders DISABLE TRIGGER ALL;
INSERT INTO orders (...) VALUES (...);
ALTER TABLE orders ENABLE TRIGGER ALL;
```

---

### **3.5 Network/Storage Bottlenecks**
**Symptoms:**
- `TimeoutError` during backup restore.
- High latency in cloud storage (S3, GCS).

**Root Causes:**
- Slow network connection.
- Storage provider throttling.

**Fixes:**
#### **A. Use Local Cache for Backups**
```bash
# Example: Pre-download critical backups
aws s3 cp s3://bucket/backup.sql /mnt/backup/ --recursive
```

#### **B. Monitor Network Performance**
```bash
# Check bandwidth usage during restore
nload | grep "backup-restore"
```

#### **C. Compress Backups (Reduce Transfer Size)**
```bash
# Compress before transfer (PostgreSQL)
pg_dump --format=custom --file=db.dump.db source_db
gzip db.dump.db
```

---

## **4. Debugging Tools & Techniques**
| **Tool** | **Use Case** | **Example Command** |
|----------|-------------|---------------------|
| `pg_verifybackups` | Check PostgreSQL backup integrity | `pg_verifybackups -d /backups` |
| `mysqldump --check` | Validate MySQL dump | `mysqldump db --check > checker.sql` |
| `pt-table-checksum` | Compare row counts (Percona) | `pt-table-checksum p_source p_target --replicate` |
| `strace` | Debug system calls (filesystem) | `strace pg_restore -d db < backup.sql` |
| `pg_stat_activity` | Monitor PostgreSQL slow queries | `SELECT * FROM pg_stat_activity WHERE state = 'active';` |
| `iostat` | Check disk I/O bottlenecks | `iostat -x 1` |

**Advanced Technique: Binary Log Replay (MySQL)**
```bash
# Resync using binary logs (if replication lag exists)
mysqlbinlog /var/log/mysql/mysql-bin.000123 | mysql -u root target_db
```

---

## **5. Prevention Strategies**
### **5.1 Pre-Migration Checks**
1. **Validate Backup Integrity**
   ```bash
   # Example: Check PostgreSQL backup
   pg_restore -l /backups/db.dump.sql | grep "table"
   ```
2. **Test Restore in Staging**
   ```bash
   # Spin up a staging DB and test restore
   docker run -d --name staging_db postgres
   pg_restore -d staging_db -U postgres /backups/db.dump
   ```
3. **Schema Compatibility Matrix**
   Keep a mapping of schema changes between source and target.

### **5.2 Automated Monitoring**
- **Backup Health Alerts**
  ```yaml
  # Example Prometheus alert for failed backups
  - alert: FailedBackup
      expr: up{job="backup-job"} == 0
      for: 5m
      labels:
        severity: critical
  ```
- **Data Drift Detection**
  ```python
  # Compare key metrics pre/post-migration
  import pandas as pd
  pre_mig = pd.read_sql("SELECT COUNT(*) FROM users", source_conn)
  post_mig = pd.read_sql("SELECT COUNT(*) FROM users", target_conn)
  assert pre_mig["count"] == post_mig["count"]
  ```

### **5.3 Post-Migration Validation**
1. **Row Count Validation**
   ```sql
   -- Compare row counts for critical tables
   SELECT
       table_name,
       (SELECT COUNT(*) FROM source.t) - (SELECT COUNT(*) FROM target.t) AS diff
   FROM source.tables;
   ```
2. **Sample Data Validation**
   ```python
   # Verify a sample of records
   def validate_sample(source, target, sample_size=100):
       source_sample = list(source.execute("SELECT * FROM users LIMIT :size", {"size": sample_size}))
       target_sample = list(target.execute("SELECT * FROM users LIMIT :size", {"size": sample_size}))
       assert len(source_sample) == len(target_sample)  # Simple check
   ```

### **5.4 Documentation & Runbooks**
- **Backup Migration Playbook**
  ```markdown
  ## Step 1: Take Consistent Backup
  - For PostgreSQL: `pg_basebackup -D /backups`
  - For MySQL: `mysqldump --single-transaction --all-databases > full_dump.sql.gz`

  ## Step 2: Validate Backup
  - Check checksum: `sha256sum /backups/db.dump.sql`
  - Test restore in staging.
  ```
- **Rollback Plan**
  ```yaml
  rollback_steps:
    - Restore from last known good backup.
    - Verify application health.
    - Reapply critical patches if needed.
  ```

---

## **6. Final Checklist Before Production**
| **Task** | **Done?** |
|----------|-----------|
| Backup integrity verified (`pg_verifybackups` / `mysqldump --check`) | ☐ |
| Schema compatibility confirmed (no breaking changes) | ☐ |
| Migration tested in staging with sample data | ☐ |
| Performance bottlenecks identified (CPU, I/O, network) | ☐ |
| Post-migration validation script ready | ☐ |
| Rollback plan documented | ☐ |

---
## **7. References**
- [PostgreSQL Backup Tools](https://www.postgresql.org/docs/current/app-pgbasebackup.html)
- [MySQL pt-table-sync](https://www.percona.com/doc/percona-toolkit/pt-table-sync.html)
- [Backup Migration Patterns (CNCF)](https://github.com/cncf/specification/blob/main/migration-patterns.md)

---
**Next Steps:**
- If issues persist, isolate components (e.g., test backup restore separately from schema migration).
- Use `strace` or `tcpdump` for low-level debugging if network/storage is suspected.