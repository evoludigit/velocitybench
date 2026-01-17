# **[Pattern] Failover Verification Reference Guide**

---

## **Overview**
The **Failover Verification** pattern ensures that a backup system (primary or secondary) can seamlessly take over in case of a primary system failure. This pattern validates that support systems (e.g., databases, APIs, authentication services) and dependencies remain operational post-failover. Proper verification mitigates downtime, data loss, and user disruption by confirming that critical services handle failover correctly.

Key objectives include:
- **Automated validation** of failover triggers and recovery paths.
- **Real-time monitoring** of service health during and after failover.
- **Minimal manual intervention** for routine checks.
- **Auditability** of failover events and system responses.

This guide covers implementation details, schema references for verification logic, sample queries, and related patterns for resilient system design.

---

## **Key Concepts**
### **1. Components of Failover Verification**
| **Component**          | **Description**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Primary System**     | The default active system (e.g., database, API, microservice).                 |
| **Backup System**      | Standby system ready to take over if the primary fails.                         |
| **Failover Trigger**   | Event or condition that activates failover (e.g., primary unavailability, health probe failure). |
| **Verification Agent** | Tool or process that tests backup system functionality post-failover.         |
| **Recovery Path**      | Steps/data replication process to restore primary functionality on the backup. |
| **Monitoring Dashboard** | Visual representation of failover status, latency, and system health.         |

### **2. Types of Failover**
| **Type**               | **Description**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Automatic Failover** | Triggered by a failure detection mechanism (e.g., load balancer, health checks). |
| **Manual Failover**    | Admin-initiated (e.g., scheduled maintenance, planned outages).                 |
| **Semi-Automated**     | Hybrid approach where user confirms failover after automated detection.          |

### **3. Verification Metrics**
Metrics to validate failover success:
- **Latency**: Response time degradation post-failover.
- **Throughput**: Requests handled per second on the backup system.
- **Data Consistency**: Sync status between primary and backup (e.g., replication lag).
- **Dependency Health**: Status of dependent services (e.g., caching layers, external APIs).

---

## **Implementation Details**
### **1. Schema Reference**
Below is a **JSON schema** for failover verification metadata. This schema can be embedded in monitoring tools or configuration files.

#### **FailoverVerificationSchema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FailoverVerification",
  "description": "Schema for defining failover verification rules and metrics.",
  "type": "object",
  "properties": {
    "systemName": {
      "type": "string",
      "description": "Name of the primary/backup system (e.g., 'DB_Primary', 'API_Backup')"
    },
    "failoverTrigger": {
      "type": "object",
      "properties": {
        "condition": {
          "type": "string",
          "enum": ["health_probe_failure", "manual_override", "threshold_violation"],
          "description": "Trigger event for failover."
        },
        "threshold": {
          "type": "number",
          "description": "Numeric threshold for health checks (e.g., 99.9%% uptime)."
        }
      },
      "required": ["condition"]
    },
    "verificationSteps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "Name of the verification step (e.g., 'database_connectivity', 'api_latency')."
          },
          "query": {
            "type": "string",
            "description": "SQL, HTTP request, or script to test backup system."
          },
          "expectedResult": {
            "type": "string",
            "description": "Expected outcome (e.g., '200 OK', 'data_synced')."
          },
          "timeout": {
            "type": "number",
            "description": "Max allowed time for step completion (seconds)."
          }
        },
        "required": ["name", "query", "expectedResult"]
      }
    },
    "recoveryPath": {
      "type": "object",
      "properties": {
        "promoteBackup": {
          "type": "boolean",
          "description": "Whether to automatically promote backup to primary."
        },
        "replicationSync": {
          "type": "string",
          "description": "Command/script to sync data post-failover (e.g., 'pg_standby')."
        }
      }
    },
    "alerting": {
      "type": "object",
      "properties": {
        "channels": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["email", "slack", "pagerduty"]
          },
          "description": "Alert channels for failover events."
        },
        "severity": {
          "type": "string",
          "enum": ["critical", "warning"],
          "description": "Severity level for alerts."
        }
      }
    }
  },
  "required": ["systemName", "failoverTrigger", "verificationSteps"]
}
```

---

### **2. Query Examples**
#### **Example 1: Database Connectivity Check (SQL)**
**Scenario**: Verify that the backup database accepts connections post-failover.
**Query**:
```sql
-- Test backup database connection
SELECT 1
FROM backup_db.test_table
LIMIT 1;
-- Expected: No errors, result = "1"
```
**Verification Rule**:
- **Expected Result**: Query executes in `<500ms` with no errors.
- **Timeout**: 2 seconds.

---

#### **Example 2: API Endpoint Latency Test (HTTP)**
**Scenario**: Check if the backup API responds within SLA.
**Tool**: `curl` or `Postman`.
**Command**:
```bash
curl -X GET "https://backup-api.example.com/health" -o /dev/null -w "%{http_code}" -s
```
**Verification Rule**:
- **Expected Result**: HTTP `200 OK`.
- **Latency Threshold**: `<300ms`.
- **Timeout**: 1 second.

---

#### **Example 3: Data Consistency Check (Custom Script)**
**Scenario**: Compare primary and backup database records for critical tables.
**Script (Python)**:
```python
import psycopg2
from psycopg2 import OperationalError

def check_consistency():
    try:
        # Connect to primary and backup
        primary_conn = psycopg2.connect("host=primary_db port=5432")
        backup_conn = psycopg2.connect("host=backup_db port=5432")

        # Compare row counts in critical table
        primary = primary_conn.cursor().execute("SELECT COUNT(*) FROM users").fetchone()[0]
        backup = backup_conn.cursor().execute("SELECT COUNT(*) FROM users").fetchone()[0]

        if primary != backup:
            raise ValueError(f"Consistency error: Primary={primary}, Backup={backup}")

    except OperationalError as e:
        return False
    finally:
        primary_conn.close()
        backup_conn.close()
    return True

if not check_consistency():
    raise Exception("Data inconsistency detected!")
```

---

### **3. Automated Verification Workflow**
1. **Trigger Detection**: Monitor for failover conditions (e.g., health probe failures).
2. **Failover Execution**: Promote backup system (if automated) or notify admins (if manual).
3. **Verification Phase**:
   - Run predefined queries/scripts (see examples above).
   - Compare results against `expectedResult` in the schema.
4. **Alerting**: Notify teams via configured channels if verification fails.
5. **Recovery**: Execute `recoveryPath` steps (e.g., data sync) if needed.

---
## **Schema Reference Table**
| **Field**               | **Type**       | **Required** | **Description**                                                                 |
|-------------------------|---------------|--------------|---------------------------------------------------------------------------------|
| `systemName`            | String        | ✅           | Name of the system (e.g., `DB_Primary`).                                           |
| `failoverTrigger.condition` | String (enum) | ✅           | Type of trigger (e.g., `health_probe_failure`).                                   |
| `failoverTrigger.threshold` | Number    | ❌           | Numeric threshold for health checks (if applicable).                              |
| `verificationSteps.name`     | String        | ✅           | Name of the verification step (e.g., `database_connectivity`).                   |
| `verificationSteps.query`     | String        | ✅           | Query/script to test the backup system.                                          |
| `verificationSteps.expectedResult` | String   | ✅           | Expected outcome (e.g., `200 OK`).                                                |
| `verificationSteps.timeout`    | Number        | ❌           | Max allowed time for the step (seconds).                                          |
| `recoveryPath.promoteBackup` | Boolean       | ❌           | Auto-promote backup to primary?                                                   |
| `recoveryPath.replicationSync` | String    | ❌           | Script/command to sync data post-failover.                                        |
| `alerting.channels`         | Array (enum)  | ❌           | Alert channels (e.g., `["slack", "email"]`).                                       |
| `alerting.severity`           | String (enum) | ❌           | Severity level (`critical` or `warning`).                                          |

---

## **Query Examples Summary**
| **Use Case**               | **Tool/Query**                          | **Verification Rule**                          |
|----------------------------|----------------------------------------|-----------------------------------------------|
| Database Connection        | SQL `SELECT 1`                         | No errors, response <500ms.                   |
| API Endpoint Health        | `curl -X GET "..."`                    | HTTP `200 OK`, latency <300ms.                |
| Data Consistency          | Custom Python script                   | Primary == Backup record counts.              |
| Replication Lag           | `pg_stat_replication` (PostgreSQL)     | Lag <10 seconds.                               |
| External Dependency Check  | HTTP `HEAD /health`                    | Status `204 No Content`.                       |

---

## **Related Patterns**
1. **[Circuit Breaker](https://link-to-pattern)**
   - Complements failover by temporarily stopping requests to a failing system.
2. **[Bulkhead](https://link-to-pattern)**
   - Isolates failures in one component from affecting others during failover.
3. **[Retry with Backoff](https://link-to-pattern)**
   - Ensures transient failures are recovered gracefully post-failover.
4. **[Chaos Engineering](https://link-to-pattern)**
   - Proactively tests failover resilience by injecting failures.
5. **[Multi-Region Deployment](https://link-to-pattern)**
   - Distributes failover across geographies for higher availability.

---
## **Best Practices**
1. **Test Failover Regularly**: Simulate failures in staging environments.
2. **Minimize Downtime**: Design for sub-second failover verification.
3. **Log Everything**: Track failover events, verification results, and recovery actions.
4. **Document Recovery Steps**: Clearly outline manual overrides for complex scenarios.
5. **Monitor Post-Failover**: Use dashboards to track long-term system health.