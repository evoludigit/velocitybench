# **[Pattern] Failover Conventions Reference Guide**

---

## **Overview**
The **Failover Conventions** pattern ensures high availability by defining standardized rules for automatic or manual system recovery when primary components (e.g., services, databases, or hardware) fail. This pattern prevents cascading failures and minimizes downtime by enforcing consistent failover criteria, triggers, and recovery procedures.

Common scenarios include:
- **Service-level failover** (e.g., switching from a primary API endpoint to a backup).
- **Database replication failover** (e.g., promoting a slave database to primary).
- **Multi-region deployment failover** (e.g., switching from a primary region to a secondary one due to outages).
- **Hardware failover** (e.g., replacing a failed node in a cluster).

Key benefits include **predictability, reduced downtime, and consistency** across environments. This guide outlines the core components, schema, and implementation examples for Failover Conventions.

---

## **Implementation Details**

### **Core Components**
1. **Failover Triggers**
   - Events that initiate failover (e.g., health checks, manual intervention, load thresholds).
2. **Failover Priority**
   - Order in which backup components become active (e.g., regional failover before service failover).
3. **Failover Actions**
   - Steps taken during failover (e.g., traffic redirection, database promotion, alerting).
4. **Recovery & Rollback**
   - Procedures to revert to the original state if failover fails or is no longer needed.
5. **Metrics & Monitoring**
   - Tools to track failover health, success rates, and performance impact.

### **Failover States**
| State            | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| **Primary**      | Active, serving traffic (e.g., primary database, API endpoint).            |
| **Secondary**    | Standby, replicating data (e.g., slave database, backup region).           |
| **Failed**       | Primary component is unreachable; failover triggered.                      |
| **Recovering**   | System is recovering from a failover (e.g., re-syncing data).              |
| **Rollback**     | Original primary is restored (e.g., after temporary failure).              |

### **Best Practices**
- **Idempotency**: Ensure failover actions can be repeated safely.
- **Minimal Latency**: Failover should occur within predefined SLAs (e.g., <10 seconds).
- **Logging**: Record all failover events for auditing and debugging.
- **Testing**: Simulate failovers in staging to validate procedures.

---

## **Schema Reference**
Below is a reference schema for defining Failover Conventions in a declarative format (e.g., JSON/YAML). This schema can be integrated into infrastructure-as-code (IaC) tools like Terraform or Ansible.

| Field               | Type     | Required | Description                                                                 | Example Value                          |
|---------------------|----------|----------|-----------------------------------------------------------------------------|----------------------------------------|
| `name`              | String   | Yes      | Unique identifier for the failover convention (e.g., `api-failover-v1`).   | `"primary-database-failover"`          |
| `priority`          | Integer  | Yes      | Order of failover priority (lower = higher).                               | `1`                                    |
| `type`              | Enum     | Yes      | Type of failover (e.g., `service`, `database`, `region`).                  | `"database"`                           |
| `triggers`          | Array    | Yes      | Conditions to trigger failover.                                             | `[{"type": "health_check", "threshold": 3}, {"type": "manual"}]` |
| `targets`           | Array    | Yes      | List of backup components to failover to.                                   | `[{"region": "us-west-2", "service": "db-slave"}]` |
| `actions`           | Array    | Yes      | Steps to execute during failover.                                           | `[{"type": "promote", "endpoints": ["db-endpoint"]}]` |
| `rollback_actions`  | Array    | No       | Steps to revert failover (if needed).                                       | `[{"type": "demote", "endpoints": ["db-endpoint"]}]` |
| `metrics`           | Object   | No       | Monitoring rules (e.g., alerts, dashboards).                                | `{"alert_threshold": 99.9%}`           |
| `dependencies`      | Array    | No       | Other patterns or services required for failover.                          | `[{"pattern": "circuit-breaker"}]`     |
| `version`           | String   | Yes      | Schema version for backward compatibility.                                  | `"1.0"`                                |

### **Example Schema (JSON)**
```json
{
  "name": "primary-database-failover",
  "priority": 1,
  "type": "database",
  "triggers": [
    {
      "type": "health_check",
      "threshold": 3,
      "check_interval": "10s"
    },
    {
      "type": "manual"
    }
  ],
  "targets": [
    {
      "region": "us-west-2",
      "service": "db-slave-1",
      "endpoint": "db-backup.example.com"
    }
  ],
  "actions": [
    {
      "type": "promote",
      "endpoints": ["db-primary.example.com"]
    },
    {
      "type": "alert",
      "severity": "critical",
      "recipients": ["team@example.com"]
    }
  ],
  "rollback_actions": [
    {
      "type": "demote",
      "endpoints": ["db-primary.example.com"]
    }
  ],
  "metrics": {
    "alert_threshold": 99.9,
    "monitored_metrics": ["db_latency", "replication_lag"]
  },
  "version": "1.0"
}
```

---

## **Query Examples**
Failover Conventions can be queried or validated using scripts, APIs, or tooling. Below are example queries for common scenarios.

### **1. Check Failover Health**
**Query (CLI/API):**
```bash
# Example: Check if a failover trigger is active
curl -X GET "http://api.example.com/failover/conventions/primary-database-failover/health" \
  -H "Authorization: Bearer <TOKEN>"
```
**Response:**
```json
{
  "status": "healthy",
  "last_failover": "2023-10-01T12:00:00Z",
  "current_primary": "db-primary.example.com",
  "backup_ready": true
}
```

### **2. Simulate a Failover**
**Script (Python):**
```python
import requests

failover_url = "http://api.example.com/failover/conventions/primary-database-failover/trigger"
headers = {"Authorization": "Bearer <TOKEN>"}

response = requests.post(failover_url, headers=headers)
print(response.json())
```
**Expected Response:**
```json
{
  "status": "success",
  "action": "promoted",
  "new_primary": "db-backup.example.com",
  "timestamp": "2023-10-01T12:00:05Z"
}
```

### **3. Validate Failover Priority**
**Query (SQL-like Pseudocode):**
```sql
SELECT *
FROM failover_conventions
WHERE priority <= 2
  AND type = 'database'
ORDER BY priority;
```
**Result:**
| name                     | priority | type      |
|--------------------------|----------|-----------|
| primary-database-failover| 1        | database  |
| secondary-api-failover    | 2        | service   |

### **4. List Rollback Actions**
**CLI Command:**
```bash
# Example: List rollback actions for a failover convention
get-failover-rollback --convention-name primary-database-failover
```
**Output:**
```
Rollback Actions for primary-database-failover:
1. Demote primary endpoint: db-primary.example.com
2. Restore original primary: db-backup.example.com
```

---

## **Relation to Other Patterns**
Failover Conventions often interact with these patterns:

| Pattern                     | Relationship                                                                 | Example Integration                          |
|-----------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Circuit Breaker**         | Failover Conventions use Circuit Breaker to timeout failed primary components. | Trigger failover if circuit breaker opens.   |
| **Bulkhead**                | Limits the impact of failover by isolating components.                     | Failover only specific services, not all.   |
| **Retry with Exponential Backoff** | Retries can failover to backup if primary keeps failing.            | Retry API calls; if all retries fail, failover to backup endpoint. |
| **Rate Limiting**           | Prevents failover storms by limiting concurrent failover attempts.        | Cap failover rate to 1 per minute.          |
| **Chaos Engineering**       | Tests failover procedures under controlled conditions.                     | Simulate database outages to validate failover. |

---

## **Troubleshooting**
| Issue                          | Root Cause                          | Solution                                  |
|--------------------------------|-------------------------------------|-------------------------------------------|
| Failover not triggering        | Health check threshold misconfigured. | Verify `triggers` threshold values.       |
| Slow failover                  | High latency in backup components.  | Optimize network/DB replication.         |
| Rollback fails                 | Data inconsistency between primaries. | Run pre-rollback sync checks.             |
| Cascading failures             | Dependencies not failing over.      | Ensure all linked services follow conventions. |

---
## **Further Reading**
- **[Circuit Breaker Pattern]** – Isolate failures to prevent cascading outages.
- **[Bulkhead Pattern]** – Segment services to limit failover scope.
- **[Database Replication]** – Understand multi-master vs. master-slave setups for failover.
- **[Infrastructure Resilience]** – Apache Kafka’s [exactly-once semantics](https://kafka.apache.org/documentation/#semantics).