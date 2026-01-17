# **[Pattern] Governance Setup – Reference Guide**

---

## **Overview**
Governance patterns define procedures, roles, and controls to ensure compliance, accountability, and consistency in enterprise operations. The **Governance Setup** pattern provides a structured approach to configure organizational governance frameworks (e.g., IT governance, data governance, or risk governance) using standardized schemas, role-based access, and automated enforcement.

This guide covers how to define governance structures, assign responsibilities, and integrate compliance checks into workflows. It assumes a basic familiarity with governance models (e.g., **COSO**, **ISO 31000**) and platform capabilities (e.g., **Archer**, **ServiceNow**, or custom governance tools).

---

## **Key Concepts**

| **Term**               | **Definition**                                                                 | **Example**                                  |
|------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Governance Framework** | A set of policies, standards, and metrics governing a domain (e.g., IT security). | ISO 27001 for cybersecurity governance.      |
| **Governance Rule**    | A configurable policy (e.g., "All systems must undergo annual audits").       | Mandatory patching interval = 14 days.      |
| **Governance Role**    | Defined responsibilities (e.g., **Governance Owner**, **Compliance Auditor**). | Chief Compliance Officer (CCO).             |
| **Governance Scope**   | Specifies which systems, teams, or departments a rule applies to.             | All "Finance" department systems.           |
| **Automation Trigger** | Event or time-based action to enforce a rule (e.g., alert, remediation).       | Hourly system health checks.                |
| **Compliance Status**  | Tracked state of adherence (e.g., `Pending`, `Compliant`, `Non-Compliant`).    | "Data encryption enabled: ✅".              |

---

## **Schema Reference**

Below is the core schema for **Governance Setup**, designed for extensibility. Use this as a foundation for your platform or database.

### **1. Governance Framework Schema**
| Field                | Type         | Description                                                                 | Example Value                     |
|----------------------|--------------|-----------------------------------------------------------------------------|-----------------------------------|
| `framework_id`       | UUID         | Unique identifier for the governance framework.                            | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6` |
| `name`               | String       | Human-readable name (e.g., "Security Governance Framework").              | "ISO 27001"                       |
| `description`        | Text         | Overview of the framework’s purpose and scope.                              | "Ensures confidentiality/integrity of IT assets." |
| `owner_role`         | RoleRef      | Role assigned as primary steward (e.g., "Governance Manager").             | `role:governance-manager`        |
| `active`             | Boolean      | Whether the framework is currently enforced.                               | `true`                             |
| `created_at`         | Timestamp    | Timestamp of framework creation.                                            | `2023-10-15T12:00:00Z`            |
| `updated_at`         | Timestamp    | Last update timestamp.                                                      | `2023-11-20T08:45:00Z`            |

---
### **2. Governance Rule Schema**
| Field                | Type         | Description                                                                 | Example Value                     |
|----------------------|--------------|-----------------------------------------------------------------------------|-----------------------------------|
| `rule_id`            | UUID         | Unique identifier for the rule.                                              | `x9y8z7w6-v5u4-t3s2-r1p0-q2n1`    |
| `framework_id`       | UUID (Ref)   | Links to the parent governance framework.                                    | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6` |
| `name`               | String       | Rule name (e.g., "Multi-Factor Authentication Enforcement").                | "MFA for All Employee Accounts"   |
| `description`        | Text         | Detailed logic or rationale behind the rule.                                 | "All user accounts require MFA to prevent credential theft." |
| `scope`              | Array[Scope] | Defines applicable systems/teams (e.g., `department: finance`).             | `[{"type": "department", "value": "finance"}]` |
| `severity`           | Enum         | Criticality level (`low`, `medium`, `high`, `critical`).                     | `high`                             |
| `automation_trigger` | String       | Type of enforcement (e.g., `scheduled`, `event-based`).                     | `scheduled`                        |
| `remediation_action` | String       | Action taken if non-compliant (e.g., `alert`, `lock_account`).               | `alert`                            |
| `compliance_criteria`| JSON         | Structured logic for evaluating compliance (e.g., `{"attribute": "mfa_enabled", "operator": "==", "value": true}`). | `{"user_role": "admin", "mfa": true}` |
| `status`             | Enum         | Current compliance state (`pending`, `compliant`, `non-compliant`).          | `pending`                          |
| `created_at`         | Timestamp    | Rule creation timestamp.                                                    | `2023-10-18T10:30:00Z`            |

---
### **3. Governance Role Schema**
| Field        | Type      | Description                                                                 | Example Value               |
|--------------|-----------|-----------------------------------------------------------------------------|-----------------------------|
| `role_id`    | UUID      | Unique role identifier.                                                    | `y7x6v5u4-t3s2-r1p0-q2n1-m0` |
| `name`       | String    | Role name (e.g., "Data Steward").                                          | "Data Governance Steward"    |
| `description`| Text      | Responsibilities of the role.                                              | "Ensures data accuracy and security." |
| `permissions` | Array[String] | List of allowed actions (e.g., `["approve_access", "audit_reports"]`).    | `["approve_data_access", "escalate_violations"]` |
| `assigned_to` | UserRef   | Linked user or team (nullable).                                            | `user:john.doe@company.com`   |

---

## **Query Examples**

### **1. List Active Governance Frameworks**
```sql
SELECT
  framework_id,
  name,
  description,
  owner_role
FROM governance_frameworks
WHERE active = true;
```
**Output Example:**
| framework_id                     | name                     | description                          | owner_role        |
|----------------------------------|--------------------------|--------------------------------------|-------------------|
| `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6`| "ISO 27001"               | Confidentiality/integrity governance. | `governance-manager` |

---

### **2. Check Compliance Status of a Rule**
```sql
SELECT
  r.rule_id,
  r.name,
  r.status,
  r.compliance_criteria,
  COUNT(DISTINCT c.system_id) as non_compliant_systems
FROM governance_rules r
LEFT JOIN compliance_checks c ON r.rule_id = c.rule_id AND c.status = 'non-compliant'
WHERE r.framework_id = 'a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6'
  AND r.name = 'MFA for All Employee Accounts'
GROUP BY r.rule_id;
```
**Output Example:**
| rule_id                        | name                          | status       | compliance_criteria           | non_compliant_systems |
|--------------------------------|-------------------------------|--------------|-------------------------------|-----------------------|
| `x9y8z7w6-v5u4-t3s2-r1p0-q2n1` | "MFA for All Employee Accounts" | `non-compliant` | `{"mfa": false}`              | 4                     |

---

### **3. Assign a Role to a User**
```json
PATCH /api/governance/roles/{role_id}/assigned_users
Headers: { "Authorization": "Bearer <token>" }
Body:
{
  "user_id": "b2c3d4e5-f6g7-h8i9-j0k1-l2m3n4o5",
  "role_id": "y7x6v5u4-t3s2-r1p0-q2n1-m0"
}
```
**Response:**
```json
{
  "success": true,
  "message": "User assigned to 'Data Governance Steward' role."
}
```

---

### **4. Trigger an Automated Compliance Check**
```bash
curl -X POST "https://api.yourplatform.com/governance/rules/{rule_id}/check"
  -H "Authorization: Bearer <token>"
  -H "Content-Type: application/json"
  -d '{
    "scope": ["system:payroll-app"],
    "timestamp": "2023-11-25T09:00:00Z"
  }'
```
**Expected Output:**
```json
{
  "rule_id": "x9y8z7w6-v5u4-t3s2-r1p0-q2n1",
  "status": "compliant",
  "details": {
    "payroll-app": {
      "mfa_enabled": true,
      "last_audit": "2023-11-20"
    }
  }
}
```

---

## **Implementation Steps**

### **Step 1: Define Governance Frameworks**
1. **Input Data**: Map existing governance models (e.g., ISO 27001 controls) to your schema.
2. **Assign Owners**: Link roles (e.g., CCO, IT Director) to frameworks via the `owner_role` field.
3. **Validate Scope**: Ensure frameworks cover critical domains (e.g., data, security, risk).

---
### **Step 2: Configure Rules**
1. **Categorize Rules**: Group rules by framework (e.g., "Access Control" under ISO 27001).
2. **Set Compliance Logic**: Define `compliance_criteria` using structured queries (e.g., attribute checks).
   - Example: `{"attribute": "password_complexity", "operator": ">", "value": "8"}`.
3. **Automate Enforcement**: Configure `automation_trigger` (e.g., nightly scans for MFA compliance).

---
### **Step 3: Assign Roles and Permissions**
1. **Map Roles to Users**: Use the `governance_role` schema to assign stewards/auditors.
2. **Grant Permissions**: Define granular access (e.g., "approve_exceptions" for the CCO).
3. **Audit Changes**: Log role assignments with timestamps for traceability.

---
### **Step 4: Monitor and Remediate**
1. **Schedule Checks**: Use the `automation_trigger` to run periodic compliance scans.
2. **Alert Non-Compliance**: Set up integrations (e.g., Slack, email) for `non-compliant` statuses.
3. **Remediate Violations**: Define escalation paths (e.g., lock accounts if MFA fails).

---

## **Related Patterns**

| **Pattern**               | **Purpose**                                                                 | **Connection to Governance Setup**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **[Access Control]**      | Enforces permissions at the system level.                                  | Governance rules can trigger access reviews or revocations (e.g., "Disable inactive accounts").     |
| **[Audit Logging]**       | Tracks user/actions for compliance.                                        | Governance frameworks require audit trails (e.g., "All changes must be logged for 3 years").      |
| **[Incident Response]**   | Handles security breaches or violations.                                   | Governance violations may escalate to incidents (e.g., non-compliant MFA → breach risk).         |
| **[Data Masking]**        | Protects sensitive data in reports.                                        | Governance rules may enforce masking (e.g., "PII must be redacted in external reports").           |
| **[Configuration Management]** | Ensures system consistency.          | Governance checks can validate configurations (e.g., "All endpoints must use TLS 1.2+").           |

---
## **Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                                                                     |
|------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------------------------|
| Rule fails compliance checks.      | Incorrect `compliance_criteria`.          | Validate logic (e.g., check attribute names/operators in the database).                          |
| Role assignments not persisted.    | Permission mismatch.                      | Verify API credentials or database write permissions for the `governance_roles` table.            |
| High non-compliance count.         | Scope too broad.                          | Narrow `scope` filters (e.g., exclude deprecated systems).                                      |
| Alerts overwhelmed.                | Too many rules triggering.                | Adjust `automation_trigger` frequency or prioritize critical rules (e.g., severity = `high`).   |

---
## **Best Practices**
1. **Start Small**: Pilot with 1–2 frameworks (e.g., security) before scaling.
2. **Document Assumptions**: Clarify edge cases (e.g., "What if a system is offline during a check?").
3. **Automate Remediation**: Use workflows to auto-fix low-severity issues (e.g., expired certificates).
4. **Review Quarterly**: Update rules to align with new regulations or business changes.
5. **Integrate with CI/CD**: Enforce governance in deployment pipelines (e.g., block code without compliance tags).

---
## **Further Reading**
- **ISO 27001 Annex A**: Control objectives for information security governance.
- **NIST SP 800-53**: Security and privacy controls for federal systems (adaptable to enterprise).
- **[Governance, Risk, and Compliance (GRC) Tools]**:
  - [ServiceNow GRC](https://www.servicenow.com/products/governance-risk-compliance/)
  - [Archer GRC](https://www.archer.com/)

---
**Last Updated**: `[Insert Date]`
**Version**: `1.2`