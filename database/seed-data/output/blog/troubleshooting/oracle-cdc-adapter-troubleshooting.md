# **Debugging Oracle CDC Adapter: A Troubleshooting Guide**

## **Introduction**
Change Data Capture (CDC) in Oracle enables near real-time data synchronization by capturing row-level changes (inserts, updates, deletes) and propagating them to downstream systems. The **Oracle CDC Adapter** is responsible for extracting these changes, transforming them, and delivering them efficiently.

This guide provides a structured approach to diagnosing and resolving common issues with the Oracle CDC Adapter.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the following symptoms:

| **Symptom** | **Description** |
|-------------|----------------|
| **No CDC Logs** | No changes captured in `dba_cdc` or `v_$capture_process` |
| **Slow Capture** | CDC logs lag behind source transactions |
| **Missing Data** | Downstream systems receive incomplete/inaccurate data |
| **Errors in Alert Logs** | `ORA-*` errors in `alert_<SID>.log` or adapter logs |
| **Adapter Hang/Freeze** | CDC process stuck, no progress in monitoring |
| **Duplicate Records** | Same row changes captured multiple times |
| **Transformation Failures** | Schema mismatches in target system |

---
## **2. Common Issues & Fixes**
### **2.1 CDC Log Not Created**
**Symptom:** No changes captured, `dba_cdc` query returns empty.

**Root Cause:**
- Missing CDC initialization (no `CAPTURE PROCESS` created).
- Incorrect credentials or permissions.
- Capture process crashed or not running.

**Solution:**
```sql
-- Check if CDC is enabled
SELECT * FROM dba_cdc_capture_processes;

-- Create a missing capture process (example for HR schema)
BEGIN
  DBMS_CDC_STARTER.START_CDC(
    capture_name => 'HR_CAPTURE',
    schema_name => 'HR',
    table_name => 'EMPLOYEES',
    capture_options => 'ROWID,COMMIT_SCN'
  );
END;
/

-- Verify process status
SELECT * FROM v$capture_process;
```
**Fix Permissions:**
```sql
GRANT EXECUTE ON DBMS_CDC_STARTER TO app_user;
GRANT SELECT ON dba_cdc* TO app_user;
```
**Check Logs:**
```sql
SELECT * FROM v$diag_info WHERE name LIKE 'ORACLE_CDC%';
```
Look for errors in `alert_<SID>.log`.

---

### **2.2 CDC Data Lag (Slow Capture)**
**Symptom:** Changes take minutes/hours to appear in target.

**Root Causes:**
- Low capture process priority.
- High transaction volume overwhelming CDC.
- `CAPTURE_PROCESS` not keeping up with SCN (System Change Number) growth.

**Solution:**
```sql
-- Check SCN lag
SELECT MAX(SCN) - MIN(SCN) AS lag FROM dba_cdc_capture_logs;

-- Increase capture process priority
ALTER SYSTEM SET events '10503 trace name context forever, level 1';
-- Monitor with: select * from v$diag_trace_file where spid = ...
```
**Optimize Capture Process:**
```sql
-- Restart with higher throtling (if applicable)
BEGIN
  DBMS_CDC_STARTER.STOP_CDC('HR_CAPTURE');
  DBMS_CDC_STARTER.START_CDC(
    capture_name => 'HR_CAPTURE',
    schema_name => 'HR',
    table_name => 'EMPLOYEES',
    capture_options => 'ROWID,COMMIT_SCN,throttle=50' -- Adjust value
  );
END;
/
```

---

### **2.3 Duplicate Records in Downstream**
**Symptom:** Same change appears multiple times in target.

**Root Causes:**
- Race condition in CDC log reading.
- Capture process restarted mid-stream.
- Transaction rollbacks causing retry.

**Solution:**
```sql
-- Check for duplicate rows in CDC log
SELECT count(*), min(scb_scn), max(scb_scn)
FROM dba_cdc_capture_logs
WHERE capture_name = 'HR_CAPTURE'
GROUP BY scb_scn
HAVING count(*) > 1;
```
**Fix:**
```sql
-- Use DML capture instead of CDC for better reliability
BEGIN
  DBMS_CDC_STARTER.STOP_CDC('HR_CAPTURE');
  DBMS_CDC_STARTER.START_CDC(
    capture_name => 'HR_CAPTURE',
    schema_name => 'HR',
    table_name => 'EMPLOYEES',
    capture_options => 'DML,ROWID' -- Use DML instead of CDC
  );
END;
/
```
**Verify with:**
```sql
SELECT capture_method FROM dba_cdc_capture_processes;
```

---

### **2.4 Adapter Integration Failures**
**Symptom:** Downstream system fails to consume CDC changes.

**Root Causes:**
- Schema mismatch (column name/type differences).
- Kafka/Queue connection issues.
- Adapter buffer full or stuck.

**Solution (Example for Kafka Integration):**
```bash
# Check Kafka consumer lag
./kafka-consumer-groups.sh --bootstrap-server <broker> --group <group-id> --describe

# If lag is high, check adapter logs
tail -f /var/log/oracle-cdc-adapter.log
```
**Fix Schema Mismatch:**
```sql
-- Compare source and target schema
SELECT column_name, data_type
FROM all_tab_cols
WHERE table_name = 'EMPLOYEES';

-- Modify adapter config to handle differences
# Example in config.json:
{
  "mappings": {
    "OLD_SCHEMA" : {
      "column_1" : { "target_column" : "column_1", "type" : "VARCHAR2" }
    }
  }
}
```

---

## **3. Debugging Tools & Techniques**
### **3.1 Oracle-Specific Tools**
- **`v$capture_process`:** Check running CDC processes.
- **`dba_cdc_capture_logs`:** Audit CDC operations.
- **`v$diag_info`:** Find Oracle trace locations.
- **`TRACE_NAME`:** Enable Oracle CDC tracing:
  ```sql
  ALTER SYSTEM SET events '10503 trace name context forever, level 1';
  ```

### **3.2 External Monitoring**
- **Prometheus/Grafana:** Track CDC queue lengths.
- **ELK Stack:** Centralized CDC logs.
- **Kafka Lag Exporter:** Monitor Kafka consumer lag.

### **3.3 Log Analysis**
**Adapter Logs:**
```bash
grep -i "error\|duplicate\|log" /var/log/oracle-cdc-adapter.log
```
**Oracle Alert Logs:**
```bash
grep -i "ORA-*|CDC" alert_<SID>.log
```

---

## **4. Prevention Strategies**
### **4.1 Optimize CDC Configuration**
- **Batch Size:** Adjust `capture_options` batch size based on workload.
- **Parallelism:** Use multiple capture processes for high-volume tables.
- **Throttling:** Limit CDC load during peak hours.

### **4.2 Schema Design**
- Avoid dynamic column names that break CDC mappings.
- Standardize data types between source and target.

### **4.3 Monitoring & Alerts**
- Set up alerts for:
  - High SCN lag (`> 1000` SCNs).
  - Capture process crashes.
  - Adapter queue backlog (`> 10,000` messages).

**Example Monitoring Query:**
```sql
SELECT
  capture_name,
  SCN - MIN(log_seq) AS lag_scns,
  COUNT(*) AS log_count
FROM dba_cdc_capture_logs
GROUP BY capture_name
HAVING lag_scns > 1000;
```

### **4.4 Testing & Validation**
- **Unit Test CDC Pipelines:** Simulate data changes and verify downstream.
- **Backfill:** Use `DBMS_CDC.MERGE_TABLE` for initial sync.

**Example Backfill:**
```sql
BEGIN
  DBMS_CDC.MERGE_TABLE(
    table_name => 'EMPLOYEES',
    merge_options => 'FULL'
  );
END;
/
```

---

## **Conclusion**
Debugging Oracle CDC issues requires:
✅ **Checking logs** (`v$capture_process`, `dba_cdc_capture_logs`).
✅ **Adjusting configuration** (batch size, parallelism, throttling).
✅ **Monitoring performance** (SCN lag, adapter queue).
✅ **Preventing duplicates** (DML capture, schema consistency).

By following this guide, you can quickly diagnose and resolve Oracle CDC Adapter issues while ensuring reliability. 🚀