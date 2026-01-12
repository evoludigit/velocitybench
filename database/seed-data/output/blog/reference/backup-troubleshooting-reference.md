---

# **[Pattern] Backup Troubleshooting Reference Guide**
*Ensure reliable data recovery by diagnosing and resolving common backup failures, verification issues, and restore complexities.*

---

## **Overview**
Backup failures can disrupt business continuity, leading to lost data or prolonged downtime. This guide outlines systematic troubleshooting approaches for identifying root causes of backup failures, validating backup integrity, and restoring data efficiently. Whether troubleshooting **full/partial failures**, **corrupt backups**, or **slow restore operations**, this pattern provides structured steps to isolate issues using logs, diagnostics, and verification tools. It also covers common pitfalls (e.g., insufficient storage, network throttling) and best practices for proactive monitoring.

---

## **Implementation Details**
Troubleshooting backups involves three core phases:
1. **Pre-Failure Analysis**: Verify backup health and logs before issues escalate.
2. **Root Cause Diagnosis**: Use logs, metrics, and validation tools to pinpoint failures.
3. **Remediation**: Apply fixes, retest, and implement preventive measures.

Key components include:
- **Backup Agent/Server Logs**: Detailed records of job execution, errors, and warnings.
- **Verification Utilities**: Tools to test backup integrity (e.g., checksum validation, file restoration tests).
- **Performance Metrics**: Monitoring storage I/O, network bandwidth, and job duration.
- **Restore Simulations**: Dry-run restores to validate backup recoverability.

---

## **Schema Reference**
Below are critical components and their attributes for troubleshooting.

| **Component**               | **Attributes**                                                                 | **Purpose**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Backup Job**              | - `JobID` (string) <br> - `Status` (enum: *Success/Failed/Partial*) <br> - `StartTime` (timestamp) <br> - `EndTime` (timestamp) <br> - `Duration` (seconds) <br> - `Source` (path) <br> - `Destination` (path) | Track job execution and identify anomalies in timing or status.             |
| **Error Log Entry**         | - `LogID` (string) <br> - `Severity` (enum: *Critical/Warn/Info*) <br> - `Timestamp` (timestamp) <br> - `Message` (string) <br> - `Code` (string, e.g., `ERR_1002`) | Filter errors by severity and code to isolate specific issues.               |
| **Validation Check**        | - `CheckType` (enum: *Integrity/Completeness/Performance*) <br> - `Pass/Fail` (boolean) <br> - `Metrics` (object: { `FileCount`: int, `BytesScanned`: int }) | Validate backup data integrity and performance bottlenecks.                   |
| **Restore Operation**       | - `RestoreID` (string) <br> - `SourceBackupID` (string) <br> - `TargetPath` (string) <br> - `Speed` (MB/s) <br> - `Errors` (array of objects) | Diagnose slow or failed restores by analyzing speed and error patterns.       |
| **Dependency**              | - `Type` (enum: *Storage/Network/ExternalAPI*) <br> - `Status` (string) <br> - `Latency` (ms) | Identify throttled or failed dependencies (e.g., SAN latency, API timeouts). |
| **Alert Rule**              | - `RuleName` (string, e.g., *BackupFailureAlert*) <br> - `Threshold` (e.g., *3 consecutive failures*) <br> - `TriggeredAt` (timestamp) | Proactively detect recurrent issues via predefined thresholds.               |

---

## **Query Examples**
Use these queries (pseudo-code) to extract troubleshooting data from logs, databases, or monitoring tools.

### **1. Identify Failed Backups in the Last 24 Hours**
```sql
SELECT
  JobID,
  Status,
  Source,
  Destination,
  COUNT(ErrorLog.LogID) AS ErrorCount
FROM BackupJob
JOIN ErrorLog ON BackupJob.JobID = ErrorLog.JobID
WHERE Status = 'Failed'
  AND EndTime >= NOW() - INTERVAL '24 HOUR'
GROUP BY JobID, Status, Source, Destination
ORDER BY ErrorCount DESC;
```
**Output Interpretation**:
- Jobs with high `ErrorCount` require deep diving into `ErrorLog.Message`.
- Correlate `Source`/`Destination` paths with storage/network issues.

---

### **2. Filter Critical Errors by Type**
```sql
SELECT
  Message,
  COUNT(*) AS Occurrences,
  STRING_AGG(DISTINCT Code, ', ') AS ErrorCodes
FROM ErrorLog
WHERE Severity = 'Critical'
  AND Timestamp >= NOW() - INTERVAL '7 DAY'
GROUP BY Message
HAVING Occurrences > 3;
```
**Output Interpretation**:
- Frequent `ERR_1002` (e.g., "Disk full") may indicate misconfigured quotas.
- Group by `Code` to apply vendor-specific fixes (e.g., patch update).

---

### **3. Validate Backup Integrity for a Specific Job**
```bash
# Example using a backup tool's CLI (e.g., Veeam, Commvault)
./validate-backup --job-id JOB12345 --checksum --file-count
```
**Expected Output**:
```
Validation for JOB12345:
- Integrity: PASS (0 mismatches)
- File Count: 1024/1024 (100%)
- Performance: 500 MB/s (Target: >= 300 MB/s)
```
**Troubleshooting Steps if Failed**:
1. Re-run with `--verbose` to isolate corruption.
2. Check storage for bad sectors (`smartctl` for HDDs/SSDs).
3. Compare with a previous successful backup’s `Metrics`.

---

### **4. Analyze Restore Performance Bottlenecks**
```sql
SELECT
  RestoreID,
  SourceBackupID,
  TargetPath,
  Speed,
  AVG(Errors.Length) AS AvgErrorSize
FROM RestoreOperation
WHERE Speed < (SELECT AVG(Speed) * 0.7 FROM RestoreOperation)
ORDER BY Speed ASC;
```
**Output Interpretation**:
- Low `Speed` + small `AvgErrorSize` → Network bottleneck (e.g., VPN throttling).
- Large `AvgErrorSize` → Corrupted files in backup (re-run validation).

---

### **5. List Storage-Dependency Latency Spikes**
```sql
SELECT
  Dependency.Type,
  AVG(Dependency.Latency) AS AvgLatency,
  MAX(Dependency.Latency) AS PeakLatency
FROM BackupJob
JOIN Dependency ON BackupJob.JobID = Dependency.JobID
WHERE Latency > 500  -- Threshold (ms)
GROUP BY Dependency.Type;
```
**Output Interpretation**:
- `Type: Storage` with `PeakLatency: 2000ms` → Check SAN health or backup window timing.
- `Type: Network` → Isolate ISP or firewall issues.

---

## **Step-by-Step Troubleshooting Workflow**
Follow this structured approach for systematic diagnosis:

### **1. Verify Logs for Patterns**
- **Check**:
  - `BackupJob.Status` for `Failed`/`Partial`.
  - `ErrorLog` for recurring `Code` (e.g., `ERR_2001` = "Permission denied").
  - `Dependency.Status` for `Timeout` or `ConnectionLost`.
- **Action**:
  - Use vendor-specific tools to decode error codes (e.g., "Veeam Error Code 0xC0000005").

### **2. Validate Backup Data**
- **Tools**:
  - **Integrity Check**: Compare checksums of source and backup.
  - **File-Level Test**: Restore a single critical file to a known good location.
  - **Performance Test**: Measure restore speed against baseline.
- **Example Command**:
  ```bash
  # Compare checksums (Linux/macOS)
  cmp --silent /backup/source.txt /restore/source.txt || echo "Checksum mismatch"
  ```

### **3. Isolate Root Cause**
| **Symptom**               | **Possible Cause**                          | **Diagnostic Query**                          | **Fix**                                  |
|---------------------------|--------------------------------------------|-----------------------------------------------|------------------------------------------|
| Backup hangs at 95%       | Storage throttle                           | Analyze `Dependency.Latency` for `Storage`    | Increase storage bandwidth or schedule. |
| Restore fails intermittently | Corrupted backup data                     | Run `validate-backup --integrity`              | Recreate backup incrementally.          |
| Slow performance          | Network saturation                         | Check `RestoreOperation.Speed` < threshold    | Offload to direct-attached storage.     |
| Job marked as "Partial"   | Permission issues                          | Filter `ErrorLog` by `ERR_2001`               | Update backup agent permissions.         |

### **4. Apply Fixes and Retest**
- **Common Fixes**:
  - **Storage**: Clean up old backups, expand volume, or upgrade hardware.
  - **Network**: Prioritize backup traffic or switch to LAN/WAN optimization.
  - **Agent**: Update backup software or reconfigure retries.
- **Retest**:
  - Run a small-scale backup/restore test.
  - Monitor `BackupJob.Duration` for regression.

### **5. Prevent Recurrence**
- **Proactive Measures**:
  - **Alerting**: Set up `AlertRule` for `Status = 'Failed'` with `Threshold = 2`.
  - **Capacity Planning**: Monitor `Destination` storage usage trends.
  - **Documentation**: Add notes to `BackupJob` for known issues (e.g., "Avoid backing up DB1 after 3 AM").

---

## **Related Patterns**
1. **[Backup Automation]**
   - *Automate backup job scheduling and failover triggers to reduce manual intervention.*
   - **Link**: [`/patterns/backup-automation`](#)

2. **[Disaster Recovery Planning]**
   - *Design recovery strategies (RTO/RPO) and offsite backup replication to mitigate data loss.*
   - **Link**: [`/patterns/disaster-recovery`](#)

3. **[Data Integrity Validation]**
   - *Implement continuous checksum validation for real-time data consistency checks.*
   - **Link**: [`/patterns/data-integrity`](#)

4. **[Performance Optimization]**
   - *Tune backup jobs for speed (e.g., parallelism, compression) without compromising reliability.*
   - **Link**: [`/patterns/performance-tuning`](#)

5. **[Security Hardening]**
   - *Secure backup media and encrypt data at rest/in-transit to prevent unauthorized access.*
   - **Link**: [`/patterns/security-backup`](#)

---
**Note**: For vendor-specific tools (e.g., Veritas, Acronis), consult their documentation for toolchain-specific error codes and CLI commands. Always test fixes in a non-production environment first.