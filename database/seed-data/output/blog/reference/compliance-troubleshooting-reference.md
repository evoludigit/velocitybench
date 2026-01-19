# **[Pattern] Compliance Troubleshooting: Reference Guide**

---
## **Overview**
Compliance Troubleshooting is a structured approach to identify, diagnose, and resolve discrepancies between system behavior, regulatory requirements, and auditing standards. This pattern provides a standardized methodology for detecting compliance violations, analyzing root causes, and applying remedial actions while maintaining audit trails for future validation. Key use cases include post-audit corrective actions, real-time policy adherence checks, and automated compliance verification in DevOps/SRE pipelines. The pattern emphasizes **non-disruptive remediation**, **documented evidence**, and **scalable diagnostics** to minimize operational overhead while ensuring adherence to frameworks like **GDPR, HIPAA, PCI-DSS, SOC 2**, or ISO 27001.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**               | **Purpose**                                                                 | **Example Implementation**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Compliance Rules Engine** | Enforces predefined policy checks (e.g., data encryption, access controls). | Rule: *"All PII must be encrypted at rest using AES-256."*                                |
| **Audit Trail Logger**      | Records system state, user actions, and compliance status changes.         | Log format: `{timestamp, event_type, resource_id, compliance_status, remediation_action}` |
| **Violation Alerts**        | Triggers notifications for critical deviations (e.g., email/SMS/SIEM).      | Alert: *"User ‘admin@domain.com’ accessed DB without MFA in violation of NIST SP 800-63."* |
| **Remediation Playbooks**    | Step-by-step procedures to resolve violations (e.g., patching, role updates). | Playbook: *"Disable legacy protocols (SSLv3) in web servers."*                            |
| **Compliance Scorecard**    | Aggregates metrics to assess overall adherence (e.g., 92% compliance).      | Dashboard: Tiered scoring (Red-Amber-Green) with drill-down reports.                     |
| **Automated Testing**       | Validates configurations against compliance baselines (e.g., OVAL, CIS).   | Tool: `"yawning-sphinx"` for AWS/GCP compliance scanning.                                  |

---

### **2. Workflow Phases**
The troubleshooting process follows a **4-phase cycle**:

| **Phase**               | **Objective**                                                                 | **Artifacts Generated**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Detection**           | Scan for deviations using agents, logs, or third-party tools.               | Violation list (e.g., `{"rule_id": "GDPR.4.1", "severity": "High", "affected_users": 12}`). |
| **Classification**      | Categorize issues by type (e.g., misconfiguration, human error, system flaw). | Tagged violations (e.g., `#misconfig`, `#thirdparty`).                                |
| **Investigation**       | Root-cause analysis (e.g., trace logs, UI artifacts, or forensic tools).     | Debug logs, screenshots, or chain-of-custody reports.                                   |
| **Remediation**         | Apply fixes per playbooks; log changes for audit.                           | Patch rollback logs, IAM policy updates, or access revocations.                         |

---

### **3. Schema Reference**
Below is a normalized schema for compliance records (JSON format). Adapt fields as needed.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "compliance_id": { "type": "string", "format": "uuid" },
    "rule": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },       // E.g., "PCI-DSS.3.5"
        "name": { "type": "string" },     // E.g., "Tokenization of Cardholder Data"
        "framework": { "type": "string" }, // E.g., "PCI-DSS", "GDPR"
        "severity": { "enum": ["Critical", "High", "Medium", "Low"] }
      }
    },
    "resource": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },       // E.g., "db:prod/orders"
        "type": { "type": "string" },     // E.g., "Database", "API"
        "owner": { "type": "string" }    // E.g., "DevOps Team"
      }
    },
    "violation": {
      "type": "object",
      "properties": {
        "description": { "type": "string" },
        "first_detected": { "type": "string", "format": "date-time" },
        "last_detected": { "type": "string", "format": "date-time" },
        "status": { "enum": ["Open", "In-Progress", "Resolved", "False-Positive"] }
      }
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": { "type": "string" }, // E.g., "log", "screenshot"
          "url": { "type": "string" },   // Link to evidence (e.g., SIEM query)
          "notes": { "type": "string" }
        }
      }
    },
    "remediation": {
      "type": "object",
      "properties": {
        "assigned_to": { "type": "string" },
        "target_date": { "type": "string", "format": "date" },
        "status": { "enum": ["Not Started", "In Progress", "Completed"] },
        "playbook_id": { "type": "string" } // Reference to playbook description
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "discovered_by": { "type": "string" }, // E.g., "Compliance Scanner"
        "last_updated": { "type": "string", "format": "date-time" }
      }
    }
  },
  "required": ["compliance_id", "rule", "resource", "violation"]
}
```

---

## **Query Examples**
### **1. List Open Violations for a Framework**
**Use Case**: Audit team wants to prioritize **GDPR** violations.
```sql
SELECT *
FROM compliance_records
WHERE rule.framework = 'GDPR'
  AND violation.status = 'Open'
ORDER BY rule.severity DESC;
```

**Output**:
| compliance_id | rule_id      | resource_id   | severity | description                          |
|----------------|--------------|----------------|----------|--------------------------------------|
| `abc123`       | GDPR.5.1     | `api:users`    | High     | PII stored without encryption.       |
| `def456`       | GDPR.2.2     | `db:logs`      | Medium   | Retention policy exceeds 1 year.    |

---

### **2. Find Resources with Unresolved Misconfigurations**
**Use Case**: DevOps needs to deprioritize **misconfigurations** (tagged `#misconfig`).
```sql
SELECT r.resource_id, r.type, ev.type AS evidence_type
FROM compliance_records r
JOIN evidence ev ON r.compliance_id = ev.compliance_id
WHERE r.violation.status = 'Open'
  AND ev.type = '#misconfig';
```

**Output**:
| resource_id   | type       | evidence_type                     |
|----------------|------------|-----------------------------------|
| `web:checkout` | Web Server | Logs showing outdated TLS cert.   |

---

### **3. Generate a Compliance Scorecard**
**Use Case**: CISO requires a weekly scorecard for **PCI-DSS** compliance.
```sql
WITH compliance_stats AS (
  SELECT
    rule.framework,
    COUNT(*) AS total_violations,
    SUM(CASE WHEN violation.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count
  FROM compliance_records
  WHERE rule.framework = 'PCI-DSS'
  GROUP BY rule.framework
)
SELECT
  framework,
  total_violations,
  resolved_count,
  (resolved_count * 100.0 / NULLIF(total_violations, 0)) AS compliance_percentage
FROM compliance_stats;
```

**Output**:
| framework | total_violations | resolved_count | compliance_percentage |
|-----------|------------------|-----------------|------------------------|
| PCI-DSS   | 42               | 38              | 90.48%                 |

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **When to Use**                                                                                     |
|--------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Policy as Code]**                 | Define compliance rules in infrastructure-as-code (e.g., Terraform, Open Policy Agent).           | When integrating compliance checks into CI/CD pipelines.                                            |
| **[Centralized Logging]**            | Aggregate logs from multiple systems for forensic analysis.                                           | To correlate violations across distributed environments (e.g., Kubernetes clusters).                |
| **[Chaos Engineering for Compliance]**| Test resilience of compliance controls under failure conditions (e.g., simulate data leaks).       | To validate disaster recovery plans against audit requirements.                                       |
| **[Configuration Management]**       | Enforce consistent system states (e.g., Ansible, Chef) to prevent drift.                          | When automating remediation of misconfigurations at scale.                                           |
| **[Incident Response Playbooks]**    | Structured guides for breaches (e.g., GDPR breach notification workflows).                          | During compliance-related incidents to meet legal timelines (e.g., HIPAA 60-day breach reporting). |

---
**Notes**:
- For **real-time monitoring**, integrate with tools like **OpenCompliance**, **ComplianceAsCode**, or **Prisma Cloud**.
- **Audit trails** should comply with **NIST SP 800-53** or **ISO 27001 Annex A.12.4** for evidence retention.
- **Automate where possible**: Use **GitHub Actions**, **Jenkins**, or **ArgoCD** to trigger remediation scripts on violation detection.