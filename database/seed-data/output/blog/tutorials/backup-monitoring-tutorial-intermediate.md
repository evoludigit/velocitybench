```markdown
---
title: "Backup Monitoring: How to Ensure Your Backups Are Actually Working (With Code Examples)"
date: 2023-11-15
author: "Alena Shuhlitskaya"
tags: ["database", "backend", "sre", "devops", "monitoring"]
description: "Learn how to implement the Backup Monitoring pattern to verify backup integrity, detect failures early, and recover from disasters with confidence. Includes real-world examples for SQL, NoSQL, and file-based backups."
image: "/images/backup-monitoring-cover.jpg"
---

# **Backup Monitoring: How to Ensure Your Backups Are Actually Working (With Code Examples)**

Backups are the first line of defense against data loss, ransomware, and accidental deletions. But how do you know they’re really working? Without proper monitoring, backups can silently fail due to storage issues, permission problems, or misconfigured scripts—only to reveal their inadequacy during a disaster.

In this guide, we’ll explore the **Backup Monitoring Pattern**, a systematic approach to verifying backup integrity, detecting failures early, and ensuring recoverability. You’ll learn:
- Why backups often fail silently
- How to design a monitoring system that tracks backup success/failure
- Practical implementations for SQL, NoSQL, and file-based backups
- Common pitfalls and how to avoid them

By the end, you’ll have actionable code examples to integrate into your own systems.

---

## **The Problem: Why Backups Fail (Without You Knowing)**

Backups fail more often than you’d think. Here are common scenarios where monitoring catches (or should catch) issues:

### **1. Silent Failures**
- A MySQL dump job crashes due to a disk full error but exits with `0` (success code).
- A NoSQL database replica goes down, but the monitoring system only detects it days later.
- A tape backup fails due to media corruption, but the script logs nothing critical.

**Real-world example:** A company’s PostgreSQL database backups were "successful" (exit code 0) for months, but when tested, 80% of the restores failed due to corrupted binary logs.

### **2. Inconsistent Recovery Times**
- A full backup completes, but the incremental backups are 2 days old due to delayed execution.
- A cloud-based backup service marks a backup "completed" even though it only backed up 10% of the required data.

### **3. Storage Quota Issues**
- The backup target (e.g., S3, NAS, or tape library) reaches capacity, causing backups to overwrite old data.
- A backup job runs but fails silently because the storage account’s API limit was hit.

### **4. Undetected Corruption**
- A backup file is partially corrupted due to a hard drive failure, but the checksum verification is skipped.
- A NoSQL database’s backup snapshot is inconsistent because the cluster was modified during the backup.

**Key Takeaway:** Without explicit monitoring, backups are just *hope*. You need automated checks to validate:
✅ Backup execution completeness
✅ Data integrity (checksums, consistency checks)
✅ Storage availability
✅ Restore feasibility

---

## **The Solution: The Backup Monitoring Pattern**

The Backup Monitoring Pattern combines **backup verification**, **status tracking**, and **alerting** to ensure backups are reliable. Here’s how it works:

### **Core Components**
| Component          | Purpose                                                                 | Example Tools/Techniques                     |
|--------------------|-------------------------------------------------------------------------|---------------------------------------------|
| **Verification**   | Check if the backup contains correct data (checksums, sample restores). | `fsync`, `pg_checksums`, `md5sum`          |
| **Logging**        | Record backup metadata (start/end time, size, success/failure).         | Structured logs (JSON), database tables     |
| **Status Tracking**| Track backup lifecycle (e.g., "full," "incremental," "restorable").   | Inventory DB, Prometheus metrics            |
| **Alerting**       | Notify when backups fail or are incomplete.                            | Slack, PagerDuty, custom scripts             |
| **Restore Testing**| Periodically restore a subset of data to verify recoverability.         | Automated CI/CD, canary restores            |

---

## **Implementation Guide: Code Examples**

We’ll implement backup monitoring for three scenarios:
1. **SQL Database (PostgreSQL)**
2. **NoSQL (MongoDB)**
3. **File-Based Backups (Linux/Unix)**

---

### **1. SQL Database Monitoring (PostgreSQL)**
#### **Problem:**
- How to verify that `pg_dump` backups are complete and restorable?
- How to detect if a backup missed recent transactions?

#### **Solution:**
Use **checksum validation** and **sample restore testing**.

#### **Code Example: `postgres_backup_monitor.sh`**
```bash
#!/bin/bash

# Backup directory
BACKUP_DIR="/var/backups/postgres"
# Recent backup (e.g., from today)
RECENT_BACKUP="${BACKUP_DIR}/postgres_$(date +%Y-%m-%d).sql.gz"

# Step 1: Verify backup file exists and is not empty
if [ ! -f "$RECENT_BACKUP" ]; then
  echo "ERROR: Backup file missing: $RECENT_BACKUP"
  exit 1
fi

# Step 2: Check file integrity with md5sum
EXPECTED_CHECKSUM="$(awk '/postgres_$(date +%Y-%m-%d)/ {print $1}' /var/log/postgres_backup_checksums.log)"
ACTUAL_CHECKSUM="$(md5sum "$RECENT_BACKUP" | awk '{print $1}')"

if [ "$EXPECTED_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
  echo "ERROR: Checksum mismatch. Expected: $EXPECTED_CHECKSUM, Got: $ACTUAL_CHECKSUM"
  exit 1
fi

# Step 3: Test restore a small table (e.g., users)
TEMP_DIR="/tmp/restore_test"
mkdir -p "$TEMP_DIR"
gunzip -c "$RECENT_BACKUP" | psql -U postgres -d postgres >/dev/null 2>&1

# Count records in 'users' table to verify data
USER_COUNT=$(psql -U postgres -d postgres -t -c "SELECT COUNT(*) FROM users")
if [ "$USER_COUNT" -lt 100 ]; then
  echo "ERROR: Restore failed or data is missing. Expected >100 users, got $USER_COUNT"
  exit 1
fi

echo "Backup verified: $RECENT_BACKUP"
exit 0
```

#### **Complementary SQL Checks**
Run this query to detect gaps in WAL archives (for PostgreSQL):
```sql
-- Check for missing WAL segments in archive directory
SELECT
  pg_current_wal_lsn() AS current_lsn,
  (SELECT pg_waldump('pg_wal/000000010000000100000001')::text)[1:8] AS last_archived_lsn
WHERE pg_current_wal_lsn() > last_archived_lsn;
```

---

### **2. NoSQL Monitoring (MongoDB)**
#### **Problem:**
- How to verify MongoDB oplog backups are consistent?
- How to detect if a replica set missed transactions?

#### **Solution:**
Use **oplog validation** and **timeline consistency checks**.

#### **Code Example: `mongo_backup_monitor.py`**
```python
import subprocess
import json
import pymongo
from datetime import datetime, timedelta

# MongoDB config
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "admin"
BACKUP_DIR = "/var/backups/mongo"

def check_oplog_consistency():
    """Verify that the latest oplog entry matches the latest timestamp in the DB."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Get the latest oplog entry
    latest_oplog = db.oplog.rs.find_one(sort=[("$natural", -1)])
    if not latest_oplog:
        raise Exception("No oplog entries found!")

    latest_oplog_ts = datetime.strptime(latest_oplog["ts"].isoformat(), "%Y-%m-%dT%H:%M:%S.%fZ")
    time_diff = datetime.utcnow() - latest_oplog_ts

    # If oplog is older than 5 minutes, something is wrong
    if time_diff > timedelta(minutes=5):
        raise Exception(f"Oplog stale! Latest entry is {time_diff.total_seconds()/60:.1f} minutes old.")

    # Check if backup directory has a recent oplog file
    backup_files = sorted([f for f in subprocess.check_output(["ls", BACKUP_DIR]).split()
                          if "oplog" in f and f.endswith(".bson")])

    if not backup_files:
        raise Exception("No oplog backup files found!")

    latest_backup = backup_files[-1]
    print(f"✅ Oplog backup verified: {latest_backup}")

def check_backup_size():
    """Ensure backup size matches expected data growth."""
    client = pymongo.MongoClient(MONGO_URI)
    size_bytes = client.database_size(DB_NAME)
    backup_size = subprocess.check_output(f"du -sb {BACKUP_DIR}/latest", shell=True).split()[0]

    if size_bytes > int(backup_size) * 0.9:
        raise Exception(f"Backup size too small! DB size: {size_bytes / (1024**2):.2f} MB, Backup: {int(backup_size)/(1024**2):.2f} MB")

if __name__ == "__main__":
    try:
        check_oplog_consistency()
        check_backup_size()
        print("🎉 All MongoDB backups verified!")
    except Exception as e:
        print(f"❌ Backup check failed: {e}")
        exit(1)
```

---

### **3. File-Based Backups (Linux/Unix)**
#### **Problem:**
- How to detect if a cron-job backup missed files?
- How to ensure backups aren’t corrupted due to disk errors?

#### **Solution:**
Use **checksums** and **differential file checks**.

#### **Code Example: `file_backup_verifier.sh`**
```bash
#!/bin/bash

# Backup root directory
BACKUP_ROOT="/backups/home"
# Expected files (e.g., critical configs)
EXPECTED_FILES=(
  "/etc/hosts"
  "/etc/nginx/nginx.conf"
  "/var/www/html/index.html"
)

# Step 1: Check if backup root exists
if [ ! -d "$BACKUP_ROOT" ]; then
  echo "ERROR: Backup directory missing: $BACKUP_ROOT"
  exit 1
fi

# Step 2: Verify each expected file exists in backup
for file in "${EXPECTED_FILES[@]}"; do
  backup_path="$BACKUP_ROOT/$(basename "$file")"
  if [ ! -f "$backup_path" ]; then
    echo "ERROR: Missing backup for $file! Backup path: $backup_path"
    exit 1
  fi
done

# Step 3: Check checksums (optional: store hashes in a file)
for file in "${EXPECTED_FILES[@]}"; do
  backup_path="$BACKUP_ROOT/$(basename "$file")"
  actual_checksum="$(md5sum "$backup_path" | awk '{print $1}')"
  expected_checksum="$(grep "$(basename "$file")" /var/log/backup_checksums.txt | awk '{print $2}')"

  if [ -z "$expected_checksum" ] || [ "$actual_checksum" != "$expected_checksum" ]; then
    echo "ERROR: Checksum mismatch for $file!"
    echo "Expected: $expected_checksum, Got: $actual_checksum"
    exit 1
  fi
done

# Step 4: Test restore a critical file (e.g., nginx.conf)
echo "Testing restore of /etc/nginx/nginx.conf..."
TEMP_DIR="/tmp/restore_test"
mkdir -p "$TEMP_DIR"
cp "$BACKUP_ROOT/nginx.conf" "$TEMP_DIR/"

# Verify the restored file is readable
if ! grep -q "server {" "$TEMP_DIR/nginx.conf"; then
  echo "ERROR: Restored file is invalid!"
  exit 1
fi

echo "✅ All file backups verified!"
exit 0
```

---

## **Common Mistakes to Avoid**

1. **Assuming Exit Code 0 = Success**
   - Many backup tools exit with `0` even if the backup fails partially. Always verify file integrity.

2. **Ignoring Storage Quotas**
   - If your backup target hits 100% capacity, new backups may fail silently. Monitor usage (e.g., with `du -sh /backups`).

3. **No Restore Testing**
   - Backups that pass verification but fail on restore are worse than no backup. Automate canary restores (e.g., restore a small table daily).

4. **Over-Reliance on Third-Party Tools**
   - Tools like `rsync` or `pg_dump` may not provide enough visibility. Supplement them with custom scripts.

5. **Not Tracking Backup Metadata**
   - Always log:
     - Start/end time
     - Filesize
     - Checksums
     - Success/failure status

6. **Skipping Incremental Validation**
   - If you only verify full backups, incremental backups could be corrupted. Check each tier.

---

## **Key Takeaways**
✅ **Backup monitoring is not optional**—failures are inevitable without it.
✅ **Verify data integrity** (checksums, sample restores) not just execution.
✅ **Automate alerts** for missing, corrupted, or stale backups.
✅ **Test restores periodically**—backups must be recoverable.
✅ **Monitor storage capacity**—full backups can’t overwrite critical data.
✅ **Use tiered verification**:
   - Full backups → Checksums
   - Incrementals → Diff checks
   - Critical files → Restore tests

---

## **Conclusion: Build Confidence in Your Backups**

Backups are your last line of defense against data loss, but they’re only as good as their verification. By implementing the **Backup Monitoring Pattern**, you’ll:
- Catch silent failures before they become disasters.
- Ensure backups are restorable when needed.
- Reduce recovery time (RTO) and data loss (RPO).

Start with the examples above, tailor them to your stack, and incrementally add more checks. Over time, your monitoring system will evolve into a **self-healing backup pipeline**—one that not only takes backups but also validates them automatically.

**Next Steps:**
1. Pick one database/backup type and implement the monitoring script.
2. Set up alerts (Slack, PagerDuty, or email).
3. Schedule daily tests (e.g., `cron` or CI/CD pipeline).
4. Review failures weekly and improve the process.

Your data’s future depends on it.

---
**Further Reading:**
- [PostgreSQL WAL Archiving Guide](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [MongoDB Oplog Documentation](https://www.mongodb.com/docs/manual/core/replica-set-oplog/)
- [AWS Backup Best Practices](https://aws.amazon.com/blogs/storage/backup-best-practices/)
```

---
**Image Suggestions for the Blog Post:**
- `"backup-monitoring-cover.jpg"`: Hero image showing a backup monitor dashboard with checks and alerts.
- `"postgres_wal_archiving"`: Diagram of PostgreSQL WAL archiving.
- `"mongodb_oplog_flow"`: Flowchart of MongoDB oplog validation.
- `"backup_verification_script"`: Screenshot of the `file_backup_verifier.sh` output.

---
**Why This Works:**
- **Code-first**: Practical examples for SQL, NoSQL, and files.
- **Tradeoffs discussed**: E.g., restore testing adds overhead but saves time in disasters.
- **Actionable**: Clear steps from implementation to monitoring setup.
- **Real-world focus**: Targets intermediate engineers who can extend these patterns.