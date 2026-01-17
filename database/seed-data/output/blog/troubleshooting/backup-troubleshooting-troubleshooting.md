# **Debugging Backup Troubleshooting: A Practical Guide**

Backups are critical for data integrity and disaster recovery, but failures—whether due to misconfigurations, storage issues, or application errors—can lead to catastrophic data loss. This guide provides a structured approach to diagnosing and resolving backup-related problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm which symptoms match your issue:

| **Symptom**                          | **Possible Cause**                          | **Action Required**                          |
|--------------------------------------|--------------------------------------------|---------------------------------------------|
| Backups fail silently with no logs   | Missing logging, permissions, or storage    | Check logs, verify storage access            |
| Partial backups (missing files)      | Incomplete process, interrupted execution   | Review job logs, increase timeout settings   |
| Long-running backups with high CPU   | Large datasets, inefficient algorithms      | Optimize backup strategy, split workload    |
| Failed restores despite successful backups | Corrupted backups, misconfigured restore | Validate backup integrity, test restore     |
| Storage quotas exceeded              | Insufficient disk space, misconfigured retention | Clean up old backups, adjust retention policy |
| Network backups failing              | Connectivity issues, authentication errors | Check network logs, verify credentials      |

---

## **2. Common Issues and Fixes (With Code)**

### **2.1. Backup Job Fails Without Logs**
**Symptom:** Backups appear in the UI as failed, but no logs are generated.
**Root Cause:** Logging may be disabled, or logs are not being written to the correct location.

#### **Fix (Log Configuration Adjustment)**
Ensure your backup tool (e.g., **AWS Backup, Velero, Restic, or Duplicati**) writes logs to a file or cloud storage.

**Example (AWS Backup CLI):**
```bash
aws backup create-logging-configuration \
  --backup-vault-name MyBackupVault \
  --logging-configuration '{"LoggingEnabled=true,"LogDestination":"s3:my-bucket/logs/"}'
```

**Example (Velero for Kubernetes):**
```yaml
# velero-plugin-for-aws/v0.1.0/config/logging.yaml
logLevel: info
logFormat: json
logFile: /var/log/velero/velero.log
```

**Check Logs:**
```bash
# For AWS Backup
aws logs tail /aws/backup/backup-vault-name --follow

# For Velero
kubectl logs -n velero -l app=velero
```

---

### **2.2. Partial Backups (Missing Files)**
**Symptom:** Some files/folders are not included in the backup.

#### **Possible Causes & Fixes:**
| **Cause**                          | **Fix**                                      |
|------------------------------------|---------------------------------------------|
| Incorrect include/exclude patterns | Verify backup rules in config.             |
| Permissions issue                  | Ensure backup user has read access.         |
| Large files skipped due to limits  | Increase `--max-uploads` (Restic) or `--limit` (Duplicati). |
| Cross-device backups               | Use `--across-devices` flag (Restic).       |

**Example (Restic Configuration):**
```bash
# Check current config
restic config show

# Modify to include excluded paths
restic -r /backup/repo config set exclude-paths-fn 'path.ExcludeWithPattern("temp/*", "logs/*")'
```

**Verify Backed-Up Files:**
```bash
# List all files in repo
restic snapshots --short
```

---

### **2.3. Storage Quota Exceeded**
**Symptom:** Backups fail with `Disk full` or `Quota exceeded`.

#### **Fixes:**
1. **Clean up old backups (Retention Policy):**
   ```bash
   # Restic: Prune old snapshots
   restic forget --keep-last 7 --prune

   # Velero: Adjust retention
   velero backup retain --name backup-2024 --hours 24
   ```

2. **Expand storage (AWS S3, GCS, etc.):**
   - Check current usage:
     ```bash
     aws s3 ls s3://my-backup-bucket --recursive | wc -l
     ```
   - Adjust bucket policy to allow more space.

3. **Compress backups (Reduce Size):**
   - Enable compression in Restic:
     ```bash
     restic backup --verify --one-file-system /data --repo /backup/repo --host my-server --exclude /temp
     ```

---

### **2.4. Failed Restores Despite Successful Backups**
**Symptom:** Backups complete, but restore fails.

#### **Debugging Steps:**
1. **Verify Backup Integrity:**
   ```bash
   # Restic: Check repo
   restic check

   # Velero: Test restore to a temporary namespace
   velero restore create --from-backup my-backup --include-namespaces default --dry
   ```

2. **Check Restore Logs:**
   ```bash
   # Velero restore logs
   kubectl logs -n velero -l job-name=velero-restore-my-backup

   # Duplicati: Check UI logs
   tail -f /var/log/duplicati/duplicati-server.log
   ```

3. **Common Fixes:**
   - **Corrupted files?** Re-run backup.
   - **Permission issues?** Restore with `--volumes-from` (K8s) or `--chown` (Linux).
     ```bash
     # Example: Restore with corrected ownership
     restic restore latest --target /restored-data --volumes-from=/backup/repo --chown=1000:1000
     ```

---

### **2.5. Network Backups Failing (AWS S3, GCS, etc.)**
**Symptom:** Backups hang or fail with `Connection timeout` or `403 Forbidden`.

#### **Troubleshooting:**
1. **Check Network Connectivity:**
   ```bash
   # Test S3 endpoint
   aws s3 ls s3://my-bucket --endpoint-url=https://s3.us-east-1.amazonaws.com

   # Check DNS resolution
   nslookup my-bucket.s3.amazonaws.com
   ```

2. **Verify Credentials:**
   ```bash
   # Test AWS CLI auth
   aws sts get-caller-identity
   ```

3. **Adjust Timeout Settings:**
   - **Restic (increase `--timeout`):**
     ```bash
     restic backup --timeout 1h /data
     ```
   - **Velero (adjust `backupStorageLocation`):**
     ```yaml
     restic:
       timezone: "America/New_York"
       timeout-duration: "1h"
     ```

---

## **3. Debugging Tools and Techniques**

| **Tool**               | **Purpose**                          | **Example Usage**                          |
|------------------------|--------------------------------------|--------------------------------------------|
| **`restic check`**     | Validate backup integrity            | `restic check /backup/repo`                |
| **`velero get backups`** | List backup status                   | `velero get backups --all-namespaces`      |
| **`aws logs tail`**    | Monitor AWS Backup logs               | `aws logs tail /aws/backup`                |
| **`kubectl logs`**     | Check Velero/K8s backup job logs      | `kubectl logs -n velero -l job-name=backup`|
| **`duplicati --dry-run`** | Test backup without storing data    | `duplicati --dry-run --source /data`       |
| **`iotop` / `iotop -o`** | Monitor disk I/O bottlenecks        | `iotop -o` (check for high read/write)     |

---

## **4. Prevention Strategies**

### **4.1. Automated Testing**
- **Run dry-runs before real backups:**
  ```bash
  # Velero: Test backup
  velero create backup test-backup --include-namespaces default --dry

  # Restic: Dry backup
  restic backup --dry-run /data
  ```
- **Automate restore tests (weekly):**
  ```bash
  # Script to restore a small namespace
  velero restore create --from-backup daily-backup --include-namespaces kube-system --dry
  ```

### **4.2. Monitoring & Alerts**
- **Set up CloudWatch/AWS Backup alerts:**
  ```bash
  aws cloudwatch put-metric-alarm \
    --alarm-name "BackupFailed" \
    --metric-name "BackupJobStatus" \
    --namespace "AWS/Backup" \
    --threshold 1 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --statistic Maximum \
    --period 3600
  ```
- **Monitor backup repo health (Restic):**
  ```bash
  restic repo stats
  ```

### **4.3. Retention Policies**
- **Enforce strict retention:**
  ```bash
  # Restic: Keep only last 30 days + 1 monthly backup
  restic forget --keep-last 30 --keep-daily 7 --prune

  # Velero: Auto-delete old backups
  velero schedule create daily-backup \
    --schedule="@daily" \
    --ttl=30d \
    --include-namespaces default
  ```

### **4.4. Backup Validation**
- **Schedule periodic checksum validation:**
  ```bash
  # Compare backup repo snapshot vs. live data
  rsync -avz /original /backup/repo && restic check
  ```
- **Use checksum tools (e.g., `md5sum`):**
  ```bash
  find /critical-data -type f -exec md5sum {} + | sort > data.md5
  # Restore and verify
  md5sum -c data.md5
  ```

---

## **5. Conclusion**
Backup failures are often preventable with proper monitoring, logging, and testing. Follow this guide to:
1. **Diagnose** issues using logs and tools.
2. **Fix** common problems (permisions, storage, network).
3. **Prevent** future failures with automated testing and retention policies.

**Final Checklist Before Going Live:**
✅ Test restore in staging.
✅ Monitor backup jobs in real-time.
✅ Set up alerts for failures.
✅ Validate backups periodically.

By following structured debugging and proactive measures, you can ensure reliable backups with minimal downtime.