# **[Pattern] Audit Troubleshooting – Reference Guide**

---

## **1. Overview**
Audit Troubleshooting is a **pattern for diagnosing, investigating, and resolving discrepancies** in system audits, logs, or compliance records. It leverages structured **audit trails**, metadata, and incident correlation to identify root causes of anomalies, failed validations, or security breaches. This pattern applies to:
- **Security & Compliance**: Detecting unauthorized access, policy violations, or data leaks.
- **Operational Systems**: Identifying failed deployments, misconfigurations, or service outages.
- **Data Integrity**: Validating correct transaction processing or schema changes.
- **Custom Applications**: Debugging application-layer audit failures (e.g., API calls, user actions).

The pattern follows a **structured workflow**:
1. **Collect** relevant audit logs and metadata.
2. **Filter** data based on time, status, or severity.
3. **Analyze** patterns (e.g., spikes, repeated errors, missing entries).
4. **Correlate** events across systems (e.g., authentication + resource access).
5. **Validate** findings against known issues or baselines.
6. **Remediate** and update monitoring for prevention.

This guide assumes familiarity with **audit schemas** (e.g., AWS CloudTrail, Splunk, ELK, or custom JSON/XML logs) and basic **querying tools** (CLI, Grafana, SIEM dashboards).

---

## **2. Schema Reference**
Audit logs typically follow a **standardized schema** with core fields. Below is a **reference table** for common fields across platforms (adapt as needed):

| **Field**               | **Description**                                                                 | **Data Type**       | **Example Values**                          |
|-------------------------|-------------------------------------------------------------------------------|---------------------|---------------------------------------------|
| `event_id`              | Unique identifier for the audit log entry.                                   | UUID/Integer        | `a3f4b7e8-1234-5678-90ab-cdef12345678`       |
| `timestamp`             | When the event occurred (ISO 8601 format recommended).                      | DateTime            | `2024-05-15T14:30:22Z`                      |
| `event_type`            | Category of the event (e.g., `Authentication`, `ResourceAccess`, `PolicyChange`). | Enum/String         | `ResourceAccess`, `FailedLogin`, `ConfigUpdate` |
| `subject`               | Entity initiating the event (user, service, IP).                            | Object              | `{ "user": "admin", "account": "aws:user:1234" }` |
| `object`                | Resource affected by the event (e.g., table, file, endpoint).                | Object              | `{ "table": "users", "action": "DELETE" }`   |
| `status`                | Outcome of the event (`SUCCESS`, `FAILURE`, `PENDING`).                      | Enum                | `FAILURE`                                   |
| `error_code`            | System-specific error identifier (if applicable).                          | String              | `403Forbidden`, `PermissionDenied`           |
| `metadata`              | Key-value pairs for context (e.g., `region`, `api_version`, `request_body`). | Object              | `{ "region": "us-east-1", "method": "POST" }` |
| `source_system`         | Originating platform (e.g., `AWS`, `Kubernetes`, `CustomApp`).               | String              | `AWSCloudTrail`, `KubernetesAudit`           |
| `severity`              | Criticality of the event (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).               | Enum                | `HIGH`                                      |
| `related_events`        | References to linked events (e.g., parent/child transactions).               | Array[UUID]         | `[a3f4b7e8-1234, b2c3d4e5-6789]`            |

---
**Note:** Adjust fields based on your **audit source** (e.g., AWS adds `requestParameters`, Kubernetes adds `auditID`).

---

## **3. Query Examples**
Use these **query snippets** to extract meaningful data from audit logs. Adapt syntax for your query tool (e.g., Splunk, Athena, Grafana, or custom scripts).

---

### **3.1 Filtering by Time Range & Status**
**Objective:** Find all failed login attempts in the last 24 hours.

#### **SQL (Athena/BigQuery)**
```sql
SELECT *
FROM audit_logs
WHERE
    timestamp >= datetime_sub(current_timestamp(), INTERVAL 24 HOUR)
    AND event_type = 'Authentication'
    AND status = 'FAILURE'
ORDER BY timestamp DESC;
```

#### **Splunk Query**
```splunk
index=audit_logs event_type="Authentication" status=FAILURE
| time_range(start=-24h end=now)
| sort -timestamp
```

#### **Grafana PromQL**
```promql
# Metric: Count of failed authentication events in the last hour
count(
  sum by (status) (
    rate(audit_logs_events_total{status="FAILURE", event_type="Authentication"}[1h])
  )
)
```

---

### **3.2 Correlating Authentication + Resource Access**
**Objective:** Identify users who accessed sensitive data after failed logins.

```sql
-- Step 1: Get failed logins
WITH failed_logins AS (
    SELECT DISTINCT subject.user
    FROM audit_logs
    WHERE
        timestamp >= datetime_sub(current_timestamp(), INTERVAL 1H)
        AND event_type = 'Authentication'
        AND status = 'FAILURE'
)

-- Step 2: Join with successful resource access (e.g., DELETE operations)
SELECT f.user, a.timestamp AS access_time, a.object.table, a.object.action
FROM failed_logins f
JOIN audit_logs a ON f.user = a.subject.user
WHERE
    a.event_type = 'ResourceAccess'
    AND a.object.action = 'DELETE'
    AND a.object.table LIKE '%sensitive%'
ORDER BY a.timestamp;
```

---
**Splunk Alternative:**
```splunk
index=audit_logs event_type=Authentication status=FAILURE
| time_range(start=-1h end=now)
| table subject.user
| inputlookup failed_users.csv
| stats values(timestamp) AS access_time by subject.user
| join type=left [search index=audit_logs event_type="ResourceAccess" object_action="DELETE" object_table="*sensitive*" | stats values(timestamp) AS delete_time by subject.user]
| sort +access_time
```

---

### **3.3 Detecting Anomalies (e.g., Unusual Access Patterns)**
**Objective:** Flag users accessing resources outside their typical role (e.g., admin accessing HR data).

#### **Python (Pandas) Example**
```python
import pandas as pd

# Load audit logs (CSV/Parquet)
logs = pd.read_csv("audit_logs.csv")

# Define "expected" roles for users (e.g., from HR system)
expected_roles = {
    "johndoe": ["finance", "reports"],
    "janedoe": ["marketing", "social"]
}

# Flag anomalies: User accessed a table outside their role
logs["is_anomaly"] = logs.apply(
    lambda row: row["object.table"] not in expected_roles.get(row["subject.user"], []),
    axis=1
)

anomalies = logs[logs["is_anomaly"]].sort_values("timestamp", ascending=False)
print(anomalies[["subject.user", "object.table", "timestamp"]])
```

---

### **3.4 Detecting Missing Audit Entries (Gaps)**
**Objective:** Identify periods where audit logs are incomplete (e.g., due to system failures).

#### **SQL (Gap Detection)**
```sql
WITH audit_sequence AS (
    SELECT
        event_id,
        timestamp,
        LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp
    FROM audit_logs
    WHERE event_type = 'ResourceAccess'
)
SELECT
    user,
    MAX(timestamp) AS last_log_time,
    MIN(prev_timestamp) AS next_expected_time,
    (MIN(prev_timestamp) - MAX(timestamp)) AS gap_seconds
FROM audit_sequence
WHERE prev_timestamp IS NOT NULL
GROUP BY user
HAVING gap_seconds > 3600  -- Flag gaps >1 hour
ORDER BY gap_seconds DESC;
```

---

## **4. Implementation Steps**
Follow this **troubleshooting workflow** when investigating audit discrepancies:

| **Step**               | **Action Items**                                                                 | **Tools/Queries**                          |
|------------------------|---------------------------------------------------------------------------------|--------------------------------------------|
| **1. Define Scope**    | Clarify the issue (e.g., "Why did User X delete records?").                   | Review tickets, alerts, or incident reports. |
| **2. Collect Data**    | Export audit logs for the relevant timeframe.                                   | AWS CLI (`aws cloudtrail lookup-events`), Splunk export. |
| **3. Filter Events**   | Narrow down by `event_type`, `status`, or `subject`.                            | See **Query Examples** (Section 3).        |
| **4. Correlate**       | Link related events (e.g., login + access).                                    | JOINs (SQL), SPL (Splunk), or Python scripts. |
| **5. Analyze Patterns**| Look for spikes, repeated failures, or outliers.                                | Visualize with Grafana/Kibana.             |
| **6. Validate**        | Cross-reference with other systems (e.g., IAM, DB logs).                        | API calls, DB queries.                     |
| **7. Remediate**       | Fix the root cause (e.g., revoke permissions, patch vulnerability).            | Follow platform-specific guides.           |
| **8. Update Monitoring**| Adjust alerts or baselines to prevent recurrence.                               | Update SIEM rules, CloudWatch Alarms.      |

---

## **5. Known Issues & Mitigations**
| **Issue**                          | **Root Cause**                          | **Mitigation**                              |
|-------------------------------------|-----------------------------------------|---------------------------------------------|
| **Incomplete audit logs**          | Service outages, retention policies.    | Enable continuous backups (e.g., S3 lifecycle). |
| **False positives in alerts**      | Overly broad filters (e.g., `status=FAILURE`). | Tune severity thresholds (e.g., `status=CRITICAL`). |
| **Correlation challenges**          | Disconnected systems (e.g., auth + DB). | Use event IDs or timestamps for linking.    |
| **Performance bottlenecks**        | Large log volumes (e.g., 1M+ events).   | Sample data or use columnar storage (Parquet). |
| **Missing metadata**                | Custom apps not logging sufficiently.   | Enforce schema compliance (e.g., OpenTelemetry). |

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                              |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **[Event Sourcing]**      | Store audit logs as an append-only sequence for replayability.                 | Systems requiring immutable audit trails.  |
| **[SIEM Integration]**    | Centralize logs in a Security Information and Event Management (SIEM) tool.    | Multi-cloud environments.                   |
| **[Canary Analysis]**     | Test changes in staging before production using audit logs.                     | Deploying new features or policies.         |
| **[Policy as Code]**      | Define and enforce audit rules via code (e.g., Terraform, OPA).               | Infrastructure-as-Code (IaC) workflows.      |
| **[Dark Data Detection]** | Identify unused or orphaned resources via audit analysis.                       | Cost optimization or security hardening.    |

---

## **7. Tools & Libraries**
| **Category**       | **Tools**                                                                     | **Use Case**                                  |
|--------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Log Storage**    | Splunk, ELK (Elasticsearch), AWS CloudWatch, Datadog                          | Centralized log management.                    |
| **Querying**       | Athena, BigQuery, Splunk SPL, Grafana, Kibana                             | Ad-hoc analysis.                              |
| **Analysis**       | Python (Pandas), R, Tableau, Gremlin (GraphQL for relationships)            | Custom correlations.                         |
| **Automation**     | Terraform, OPA (Open Policy Agent), AWS Lambda                             | Enforce policies or trigger alerts.           |
| **Visualization**  | Grafana, Power BI, Tableau                                                  | Dashboards for trends/patterns.               |

---
**Example Stack:**
- **Storage:** Amazon S3 + AWS Athena
- **Querying:** Grafana (with Prometheus) + Python scripts
- **Alerting:** AWS Lambda + SNS for critical events

---
## **8. Best Practices**
1. **Standardize Schemas**: Use a consistent format (e.g., JSON schema) across systems.
2. **Retention Policies**: Balance cost vs. compliance (e.g., 7–365 days).
3. **Automate Alerts**: Set up thresholds for anomalies (e.g., "5+ failed logins in 1 hour").
4. **Document Findings**: Update runbooks for common issues (e.g., "Failed S3 Permissions").
5. **Test Regularly**: Simulate breaches (e.g., "What if an admin accesses DBs?").

---
## **9. Example Walkthrough**
**Scenario:** *"User `devops@company.com` deleted production tables, but their access was revoked 2 days ago."*

### **Steps:**
1. **Filter Events**:
   ```sql
   SELECT * FROM audit_logs
   WHERE subject.user = 'devops@company.com'
   AND timestamp BETWEEN '2024-05-14' AND '2024-05-16';
   ```
   → Finds a `DELETE` on `prod_tables` at `2024-05-15T10:00:00Z`.

2. **Check Permissions**:
   - Query IAM/RBAC: `devops` had `admin` role until `2024-05-13`.
   - **Issue:** Role wasn’t revoked in time or a **temporary escalation** occurred.

3. **Correlate with Authentication**:
   ```sql
   SELECT * FROM audit_logs
   WHERE timestamp = '2024-05-15T10:00:00Z'
   AND event_type = 'Authentication';
   ```
   → Shows `devops` logged in via **SSH key** (not MFA).

4. **Remediation**:
   - Rotate SSH keys immediately.
   - Update RBAC policies to enforce **just-in-time (JIT) access**.
   - Add an alert for `DELETE` operations on `prod_*` tables.

---
**Outcome:** Prevent future breaches by enforcing **least privilege + MFA**.

---
**End of Guide.** For platform-specific details, consult:
- [AWS CloudTrail Best Practices](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-best-practices.html)
- [GCP Audit Logs Reference](https://cloud.google.com/logging/docs/audit)
- [Kubernetes Audit Docs](https://kubernetes.io/docs/tasks/debug-application-cluster/audit-logging/)