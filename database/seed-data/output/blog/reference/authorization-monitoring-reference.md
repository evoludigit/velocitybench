# **[Pattern] Authorization Monitoring – Reference Guide**

---
## **Overview**
The **Authorization Monitoring** pattern tracks and analyzes access control decisions to detect anomalies, enforce compliance, and improve security posture. It logs permission evaluations—including results (allow/deny), subjects (users/roles), resources, actions, and policies—enabling post-hoc auditing, risk scoring, and automated response to unauthorized attempts.

Key use cases:
- Detecting **privilege escalation** or **misconfigurations** in real-time.
- Enforcing **compliance** (e.g., GDPR, SOC 2) by validating access patterns.
- Identifying **suspicious activity** (e.g., an administrator accessing sensitive data).
- Aiding **forensic investigations** with detailed audit trails.

Implementations typically integrate with identity providers (IdP), RBAC (Role-Based Access Control), or attribute-based access control (ABAC) systems.

---

## **Schema Reference**

| **Field**            | **Type**       | **Description**                                                                                                                                                                                                 | **Required** | **Example Values**                     |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|----------------------------------------|
| `event_id`           | String (UUID) | Unique identifier for the authorization event.                                                                                                                                                                   | ✅ Yes        | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8`   |
| `timestamp`          | ISO 8601      | When the decision was evaluated (UTC).                                                                                                                                                                          | ✅ Yes        | `2024-05-20T14:30:45Z`                  |
| `subject`            | Object        | The entity requesting access.                                                                                                                                                                                  | ✅ Yes        | `{"user_id": "usr_123", "role": "admin"}` |
| `subject_type`       | String        | `user`, `service_account`, `group`, or other.                                                                                                                                                                | ⚠️ Optional   | `user`                                  |
| `resource`           | Object        | The accessed resource.                                                                                                                                                                                       | ✅ Yes        | `{"type": "database", "id": "prod_db1"}` |
| `resource_type`      | String        | Type of resource (e.g., `database`, `API_endpoint`, `file`).                                                                                                                                                 | ⚠️ Optional   | `database`                              |
| `action`             | String        | Permission assessed (e.g., `read`, `write`, `delete`).                                                                                                                                                     | ✅ Yes        | `write`                                 |
| `policy_name`        | String        | Name of the policy applied (e.g., `DataProtectionPolicy`).                                                                                                                                                 | ⚠️ Optional   | `DataProtectionPolicy`                 |
| `decision`           | String        | `ALLOW` or `DENY`.                                                                                                                                                                                          | ✅ Yes        | `DENY`                                  |
| `reason`             | String        | Human-readable explanation for denial (e.g., "Missing `data_access` role").                                                                                                                                     | ⚠️ Optional   | `"Missing 'data_access' role"`           |
| `duration_ms`        | Integer       | Time taken for the authorization check (for latency analysis).                                                                                                                                                | ⚠️ Optional   | `42`                                    |
| `metadata`           | Object        | Key-value pairs for contextual data (e.g., `client_ip`, `request_id`).                                                                                                                                            | ⚠️ Optional   | `{"client_ip": "192.168.1.1", "location": "NY"}` |

---

## **Query Examples**
Use these queries to analyze authorization logs in tools like Elasticsearch, Splunk, or custom databases.

### **1. Find All Denied Requests for Sensitive Data**
```sql
SELECT *
FROM authorization_logs
WHERE resource_type = 'database' AND resource.id LIKE '%sensitive%' AND decision = 'DENY'
ORDER BY timestamp DESC;
```

**Output Columns:** `event_id`, `subject.user_id`, `action`, `reason`, `timestamp`

### **2. Detect Anomalous Access Patterns (e.g., Admin Accessing Unusual Resources)**
```sql
SELECT
    subject.user_id,
    resource.type AS resource_type,
    COUNT(*) AS access_count
FROM authorization_logs
WHERE subject.role = 'admin'
  AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY subject.user_id, resource.type
HAVING COUNT(*) > 5;
```

**Output Columns:** `user_id`, `resource_type`, `access_count`

### **3. Latency Analysis for Slow Authorization Checks**
```sql
SELECT
    policy_name,
    AVG(duration_ms) AS avg_latency,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_latency
FROM authorization_logs
WHERE duration_ms > 100  -- Threshold for "slow" checks
GROUP BY policy_name
ORDER BY p95_latency DESC;
```

**Output Columns:** `policy_name`, `avg_latency`, `p95_latency`

### **4. Compliance Reporting: Access to PII by Non-Compliance Roles**
```sql
SELECT
    subject.user_id,
    resource.id,
    action,
    decision
FROM authorization_logs
WHERE resource.type = 'user_profile'  -- PII likely stored here
  AND subject.role NOT IN ('compliance_officer', 'auditor');
```

**Output Columns:** `user_id`, `resource.id`, `action`, `decision`

### **5. Real-Time Alerting (Pseudocode for Alert System)**
```python
# Example for a rule-based alert engine
def check_for_privilege_escalation(logs):
    for log in logs:
        if (log["action"] == "role_change"
            and log["subject"]["role"] == "super_admin"
            and log["decision"] == "ALLOW"
            and log["timestamp"] > previous_user_activity["timestamp"] + 5 * 60 * 1000):
            trigger_alert("Potential privilege escalation detected")
```

---

## **Implementation Details**
### **Key Components**
1. **Authorization Decision Logs**
   - Store every evaluation (not just denials) to correlate events.
   - Include **why** a decision was made (e.g., missing attribute, policy violation).

2. **Real-Time vs. Batch Processing**
   - **Real-time:** Stream logs to SIEM (e.g., Splunk, Datadog) for immediate alerts.
   - **Batch:** Analyze logs daily/weekly for trends (e.g., unusual access patterns).

3. **Integrations**
   - **IdP:** OAuth2/OpenID Connect (e.g., Okta, Azure AD).
   - **Policy Engines:** Open Policy Agent (OPA), Casbin.
   - **Databases:** PostgreSQL (with `pgAudit`), MongoDB (native logging).

4. **Data Retention**
   - **Audit Logs:** Retain for compliance (e.g., 7+ years).
   - **Anomaly Logs:** Retain for 90 days (adjust based on risk).

### **Best Practices**
- **Minimize Overhead:** Sample logs if volume is high (e.g., log only denials for low-risk actions).
- **Anonymize Data:** Mask PII in logs for non-compliance users (e.g., replace `user_id` with a hash).
- **Correlate Events:** Link authorization logs with other telemetry (e.g., failed login attempts).
- **Automate Responses:** Use rules to block IPs/accounts after repeated denials (e.g., `DENY` + `reason="invalid_token"`).

### **Tools & Libraries**
| **Tool**               | **Use Case**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **OpenTelemetry**      | Standardized logging/metrics for authorization decisions.                    |
| **Elasticsearch**      | Full-text search and visualizations for logs.                               |
| **Prometheus + Grafana** | Monitor latency and error rates in authorization checks.                    |
| **Splunk**             | Advanced anomaly detection with ML (e.g., "unusual hour for admin access").  |
| **Casdoor**            | Open-source auth server with built-in monitoring.                            |

---

## **Related Patterns**
1. **[Permission Auditing](https://example.com/permission-auditing)**
   - Focuses on *manual* reviews of access rights (complements this pattern).

2. **[Just-In-Time (JIT) Access](https://example.com/jit-access)**
   - Temporarily grants access (e.g., for incident response) and logs the justification.

3. **[Context-Aware Access](https://example.com/context-aware-access)**
   - Extends authorization decisions with environmental context (e.g., device health, location).

4. **[Attribute-Based Access Control (ABAC)](https://example.com/abac)**
   - Fine-grained policies (e.g., `allow = resource.owner == user`) that generate detailed logs.

5. **[Zero Trust Architecture](https://example.com/zero-trust)**
   - Framework where authorization monitoring is a core component for continuous verification.

---
**See Also:**
- [NIST SP 800-175B](https://csrc.nist.gov/publications/detail/sp/800-175b/final) (Guidelines for logging).
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).