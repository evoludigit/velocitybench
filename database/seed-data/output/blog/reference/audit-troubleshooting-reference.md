# **[Pattern] Audit Troubleshooting Reference Guide**

---

## **Overview**
Audit Troubleshooting is a structured methodology for diagnosing, resolving, and preventing issues in system audit logs, tracing, and compliance events. This pattern applies to applications, microservices, and distributed systems where audit records are critical for security, compliance, or operational visibility. The pattern ensures traceability of user actions, system changes, and suspicious events while providing a systematic approach to identifying discrepancies, performance bottlenecks, or security breaches in logs.

Key objectives include:
- **Verification**: Confirming log correctness (e.g., missing entries, timestamp alignment).
- **Correlation**: Linking log events across services and systems.
- **Detection**: Identifying anomalies (e.g., unauthorized access, configuration drift).
- **Resolution**: Mitigating issues and documenting fixes.

This guide covers schema standards, common queries, and integration patterns with adjacent systems like SIEM or observability tools.

---

## **Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                                     | **Example Use Case**                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Audit Log Schema**   | Standardized fields for consistency (e.g., action, subject, timestamp, severity).                    | Ensuring all services log user logins in the same format.                            |
| **Log Collection**     | Centralized ingestion (e.g., Fluentd, Loki, or ELK Stack).                                        | Aggregating logs from 100+ microservices into a single searchable store.              |
| **Alerting Rules**     | Define thresholds (e.g., "Block if `severity=critical` and `count > 5 in 1 hour`").                | Auto-notifying security teams for brute-force attempts.                               |
| **Enrichment**         | Augment logs with metadata (e.g., user roles, IP geolocation).                                    | Adding context to failed API calls (e.g., "User `admin@example.com` from Brazil").   |
| **Retention Policy**   | Define lifecycle for logs (e.g., 30 days hot storage, 1 year cold archive).                       | Compliance with GDPR by purging personal data after 2 years.                          |
| **Integration**        | Connect to SIEM (e.g., Splunk), monitoring (e.g., Prometheus), or business systems (e.g., CRM).  | Syncing audit logs to a customer support ticketing system for post-incident analysis.  |

---

### **2. Schema Reference**
Below is a **recommended schema** for audit logs. Customize fields as needed for your domain.

| **Field**            | **Type**       | **Description**                                                                                     | **Example Value**                          | **Required?** |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|----------------|
| `event_id`           | String (UUID)  | Unique identifier for the log entry.                                                                | `"550e8400-e29b-41d4-a716-446655440000"`   | Yes            |
| `timestamp`          | ISO 8601       | When the event occurred (use UTC).                                                                 | `"2023-10-15T14:30:00Z"`                   | Yes            |
| `event_type`         | String         | Category of the event (e.g., `authentication`, `data_access`, `configuration_change`).           | `"authentication"`                          | Yes            |
| `subtype`            | String         | Subcategory (e.g., `login_success`, `login_failure`, `privilege_escalation`).                    | `"login_success"`                           | Yes            |
| `severity`           | String         | Criticality level (`low`, `medium`, `high`, `critical`).                                           | `"medium"`                                  | Yes            |
| `user_id`            | String         | Identifier for the user performing the action (e.g., email, system username).                     | `"alice@company.com"`                       | Conditional*   |
| `user_agent`         | String         | Client device/software used (e.g., `Mozilla/5.0`).                                                  | `"Postman/8.2.1"`                           | No             |
| `source_ip`          | String         | IP address of the request origin.                                                                  | `"192.0.2.1"`                               | Yes            |
| `target_resource`    | String         | Affected system/resource (e.g., `/api/users`, `database:users`).                                   | `"/api/users/123"`                          | Yes            |
| `action`             | String         | Specific operation (e.g., `create`, `delete`, `update_password`).                                | `"update_password"`                         | Yes            |
| `status`             | String         | Outcome (`success`, `failure`, `pending`).                                                          | `"success"`                                  | Yes            |
| `additional_context` | JSON           | Free-form data (e.g., `{"previous_value": "admin", "new_value": "guest"}`).                       | `{"old_password": "*****"}`                   | No             |
| `metadata`           | JSON           | Non-sensitive metadata (e.g., `{"service": "auth-service", "version": "v2.1"}`).                   | `{"trace_id": "abc123"}`                     | No             |

\* **Conditional**: Include `user_id` only if the event involves a user action (exclude system-generated logs like "scheduled cleanup").

---

### **3. Query Examples**
Use these **query templates** (adjust for your log system—e.g., LogQL, ELK, or Athena).

#### **A. Basic Filtering**
**Query:** Find all failed login attempts in the last 24 hours.
```sql
-- LogQL (Loki)
status="failure" AND event_type="authentication" AND subtype="login"
| line_format "{{.severity}}: {{.user_id}} tried to login from {{.source_ip}} at {{.timestamp}}"
```
**Output:**
```
high: alice@company.com tried to login from 192.0.2.1 at 2023-10-15T14:30:00Z
high: bob@example.com tried to login from 198.51.100.1 at 2023-10-15T14:31:00Z
```

#### **B. Anomaly Detection**
**Query:** Alert if the same IP performs >5 login failures in 1 minute.
```sql
// Prometheus Alert Rule
increase(auth_failure_total{source_ip="$ip"}[1m]) > 5
```
**Output:**
```
ALERT: Brute-force attempt detected from 198.51.100.1
```

#### **C. Correlation Across Services**
**Query:** Find all API calls leading to a failed `update_password` event.
```sql
// ELK Query (Kibana)
(event_type: "data_access" AND action: "update_password" AND status: "failure")
AND
(event_type: "api_request" AND target_resource: "/api/auth/update_password")
| sort timestamp desc
```
**Output:**
```
2023-10-15T14:35:00Z - Failed password update for user alice@company.com
2023-10-15T14:34:00Z - API call to /api/auth/update_password from alice@company.com
```

#### **D. Compliance Check**
**Query:** Audit all admin role changes in the last 30 days.
```sql
// Athena (Glue Catalog)
SELECT *
FROM audit_logs
WHERE event_type = 'configuration_change'
  AND additional_context->>'new_role' = 'admin'
  AND timestamp > date_add(current_date(), -30)
ORDER BY timestamp DESC;
```
**Output:**
| `event_id`               | `timestamp`          | `user_id`       | `target_resource` | `action`            |
|--------------------------|----------------------|-----------------|--------------------|---------------------|
| `6ec7c86a-...`           | `2023-10-01T09:00:00`| `devops@company` | `roles/admin`      | `assign_role`        |

---

### **4. Common Troubleshooting Scenarios**
| **Scenario**                          | **Diagnostic Query**                                                                 | **Resolution Steps**                                                                 |
|----------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Missing audit logs**                | `SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() - INTERVAL '1 hour'`         | Check log shipper (e.g., Fluentd) for errors; verify permissions on the log store.  |
| **Inconsistent timestamps**           | `SELECT MIN(timestamp), MAX(timestamp) FROM audit_logs`                              | Sync system clocks across nodes; use NTP.                                             |
| **High cardinality in `user_id`**     | `SELECT user_id, COUNT(*) FROM audit_logs GROUP BY user_id ORDER BY COUNT DESC`     | Implement pseudonymization for privacy; sample high-frequency users.                  |
| **False positives in alerts**         | `event_type="authentication" AND severity="high" AND status="success"`              | Adjust alert thresholds; whitelist known IPs.                                         |
| **Missing context in events**         | `SELECT event_id, additional_context FROM audit_logs WHERE additional_context IS NULL` | Enrich logs with dynamic metadata (e.g., user roles from a database).                |

---

### **5. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                         |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **[Observability Pipeline](link)** | Standardized logging, metrics, and tracing for system health.                                       | When audit logs are part of a broader observability strategy.                           |
| **[Security Event Enrichment](link)** | Augmenting logs with threat intelligence (e.g., IP reputation, malicious hashes).                | During forensic investigations or compliance audits.                                     |
| **[Canary Releases](link)**      | Gradually roll out changes while monitoring audit logs for errors.                                  | Testing changes to audit schemas or collection pipelines.                                 |
| **[Incident Response Playbook](link)** | Structured guide for handling security incidents traced to audit logs.                           | During post-mortems or when logs indicate a breach.                                      |
| **[Audit Trail Compliance](link)** | Mapping audit logs to regulatory requirements (e.g., GDPR, HIPAA).                               | For organizations subject to strict compliance rules.                                     |

---

### **6. Best Practices**
1. **Normalize Logs Early**: Use a log processor (e.g., Fluentd, Logstash) to standardize schemas before ingestion.
2. **Retain Proportional Data**: Store high-severity logs longer than low-severity ones (e.g., 7 days vs. 30 days).
3. **Immutable Storage**: Use write-once-read-many (WORM) storage for logs to prevent tampering.
4. **De-duplication**: Avoid duplicate entries (e.g., retrying the same failed login).
5. **Dynamic Fields**: Use JSON for optional fields to accommodate evolving requirements.
6. **Performance**: Index high-cardinality fields (e.g., `user_id`) for faster queries.

---
**See Also:**
- [Log Collection Patterns](link) for designing pipelines.
- [SIEM Integration Guide](link) for advanced threat detection.