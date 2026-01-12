# **[Pattern] Compliance Troubleshooting – Reference Guide**

---

## **Overview**
The **Compliance Troubleshooting** pattern provides a structured approach to identifying, diagnosing, and resolving compliance-related issues in software systems, cloud platforms, or operational workflows. It ensures adherence to regulatory frameworks (e.g., GDPR, HIPAA, PCI DSS, SOX) by systematically validating controls, logging anomalies, and automating corrective actions. This guide outlines key concepts, schema references, query patterns, and integration with related troubleshooting workflows.

---

## **Key Concepts**
The pattern centers on the following components:

| **Component**               | **Description**                                                                                     | **Lifecycle Stage**          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------|
| **Compliance Rule Engine**  | A framework for defining, validating, and enforcing regulatory rules (e.g., policies, thresholds).  | Design/Operational             |
| **Audit Logs**              | Structured logs capturing system events for later analysis (e.g., failed access attempts, data changes). | Real-time/Post-incident       |
| **Anomaly Detection**       | AI/ML-driven alerts for deviations from compliance baselines (e.g., unusual data access patterns).  | Continuous Monitoring          |
| **Remediation Workflows**   | Automated or manual steps to correct violations (e.g., data masking, access revocation).            | Corrective Action               |
| **Compliance Dashboard**    | Visual representation of rule violations, trends, and remediation status.                          | Reporting/Analysis             |

---

## **Schema Reference**
Below is the core schema for implementing compliance troubleshooting:

### **1. Compliance Rule Definition**
```json
{
  "rule_id": "unique-identifier",
  "name": "string (e.g., 'GDPR_PII_Encryption')",
  "description": "string",
  "framework": "string (e.g., 'GDPR', 'HIPAA')",
  "severity": "enum (LOW/Medium/HIGH)",
  "policy": {
    "condition": "string (e.g., 'field.sensitivity = "PII" AND field.encrypted = false')",
    "action": "string (e.g., 'Mask value', 'Generate alert')"
  },
  "created_at": "timestamp",
  "last_updated": "timestamp",
  "version": "integer"
}
```

### **2. Audit Event Log**
```json
{
  "event_id": "unique-identifier",
  "timestamp": "ISO-8601",
  "rule_id": "string (references rule_id)",
  "resource": {
    "type": "string (e.g., 'database', 'API')",
    "name": "string",
    "location": "string (e.g., 'us-east-1')"
  },
  "details": {
    "action": "string (e.g., 'WRITE', 'DELETE')",
    "user": "string (or 'ANONYMOUS')",
    "data": "object (e.g., {'field': 'name', 'value': 'John Doe'})",
    "status": "enum (COMPLIANT/VIOLATION/IGNored)"
  }
}
```

### **3. Remediation Task**
```json
{
  "task_id": "unique-identifier",
  "rule_id": "string",
  "status": "enum (PENDING/IN_PROGRESS/RESOLVED/FAILED)",
  "assigned_to": "string (user/team)",
  "priority": "enum (NONE/MEDIUM/HIGH)",
  "notes": "string",
  "resolved_at": "timestamp (if applicable)"
}
```

---

## **Query Examples**
Use these queries to interact with the compliance system via APIs or databases.

### **1. List Active Violations**
```sql
SELECT
  a.event_id,
  r.name AS rule_name,
  r.severity,
  a.details.action,
  a.details.resource AS affected_resource,
  a.details.status AS status
FROM audit_logs a
JOIN compliance_rules r ON a.rule_id = r.rule_id
WHERE a.details.status = 'VIOLATION'
  AND a.timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY r.severity DESC, a.timestamp DESC;
```

### **2. Find Unresolved Remediation Tasks**
```sql
SELECT
  t.task_id,
  t.rule_id,
  r.name AS rule_name,
  t.status,
  t.assigned_to,
  t.created_at
FROM remediation_tasks t
JOIN compliance_rules r ON t.rule_id = r.rule_id
WHERE t.status NOT IN ('RESOLVED', 'FAILED')
ORDER BY t.priority DESC, t.created_at;
```

### **3. Generate Compliance Report (Last 30 Days)**
```sql
SELECT
  r.framework,
  r.name AS rule_name,
  COUNT(DISTINCT a.event_id) AS violations_count,
  SUM(CASE WHEN a.details.status = 'VIOLATION' THEN 1 ELSE 0 END) AS total_violations
FROM audit_logs a
JOIN compliance_rules r ON a.rule_id = r.rule_id
WHERE a.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY r.framework, r.name
ORDER BY total_violations DESC;
```

### **4. Trigger Automated Remediation (Pseudocode)**
```python
def remediate_violation(rule_id, resource_data):
  if rule_id == "GDPR_PII_Encryption":
    encrypt_data(resource_data)
    log_remediation(rule_id, resource_data, "AUTOMATED")
  elif rule_id == "HIPAA_Access_Log":
    revoke_access(resource_data.user)
    notify_compliance_team(rule_id)
```

---

## **Implementation Best Practices**
1. **Rule Prioritization**:
   - Tag rules by severity (`HIGH/Medium/LOW`) and align with business impact.
   - Example: `GDPR_PII_Encryption` → `HIGH`, `Audit_Trail_Retention` → `MEDIUM`.

2. **Audit Log Retention**:
   - Retain logs for **7–10 years** (regulatory requirement) using tiered storage (hot/cold).

3. **Anomaly Detection**:
   - Use statistical baselines or ML models to flag outliers (e.g., sudden data deletion spikes).

4. **Automation**:
   - Automate low-severity violations (e.g., masking PII) but reserve manual review for `HIGH` risks.

5. **Integration**:
   - Connect to SIEM tools (e.g., Splunk, Datadog) for centralized logging.
   - Sync with IAM systems (e.g., AWS IAM, Azure AD) for access control enforcement.

---

## **Related Patterns**
| **Pattern**                     | **Purpose**                                                                 | **Integration Points**                          |
|----------------------------------|------------------------------------------------------------------------------|--------------------------------------------------|
| **[Observability Patterns]**     | Collect and analyze system logs/metrics to detect compliance breaches.      | Audit logs, anomaly detection alerts.           |
| **[Security Incident Response]** | Define playbooks for handling compliance violations as security incidents.   | Remediation tasks, escalation workflows.        |
| **[Policy-as-Code]**             | Define compliance policies using IaC tools (e.g., Terraform, Open Policy Agent). | Rule engine inputs, automated enforcement.     |
| **[Data Masking]**               | Protect sensitive data during troubleshooting or audits.                   | Audit log masking, remediation actions.          |
| **[Change Data Capture (CDC)]**  | Track real-time data changes for compliance validation.                    | Audit event logging, rule triggering.           |

---

## **Troubleshooting Common Issues**
| **Issue**                          | **Root Cause**                          | **Solution**                                          |
|-------------------------------------|------------------------------------------|-------------------------------------------------------|
| False positives in anomaly detection | Overly strict thresholds.               | Adjust thresholds or refine ML models.                 |
| Delayed rule application            | Rule version mismatch.                  | Enforce versioning and validate rule deployment.      |
| Remediation failure                 | Insufficient permissions.               | Grant least-privilege access to remediation scripts.  |
| Missing audit logs                  | Log collection disabled.                | Enable centralized logging (e.g., Cloudtrail, ELK).   |

---

## **Example Workflow**
1. **Detection**:
   - An API call logs a `DELETE` action on PII data → triggers `GDPR_PII_Encryption` rule.
2. **Alerting**:
   - System generates an alert: *"Violation: Rule 'GDPR_PII_Encryption' (HIGH) – User 'j.doe' deleted PII data without encryption."*
3. **Remediation**:
   - Automated script encrypts the deleted data and marks the event as `RESOLVED`.
   - Team `SecurityOps` reviews the incident via the dashboard.
4. **Reporting**:
   - Monthly report flags `GDPR_PII_Encryption` as having 5 violations, with 2 unresolved.

---
**Version**: `1.2`
**Last Updated**: `2024-02-15`