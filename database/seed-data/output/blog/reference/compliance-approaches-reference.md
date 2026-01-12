# **[Pattern] Compliance Approaches Reference Guide**

## **Overview**
The **Compliance Approaches** pattern defines a structured methodology to align system capabilities with regulatory, policy, or organizational standards. It ensures traceability, auditability, and consistency in compliance requirements across domains such as security, privacy (GDPR, CCPA), financial regulations (SOX, PCI DSS), or industry-specific frameworks (HIPAA, ISO 27001).

This pattern enables organizations to:
- **Classify compliance requirements** into categorized approaches (mandatory, policy-driven, best practice).
- **Automate compliance checks** via policy-as-code (PaC) and rule engines.
- **Maintain audit trails** with timestamped evidence of compliance status.
- **Simplify remediation** with contextualized recommendations and predefined workflows.

---
## **Schema Reference**

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                     | **Example Values**                                                                                     |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Requirement ID**      | UUID           | Unique identifier for compliance rules (e.g., `req-123e4567-e89b-12d3-a456-426614174000`).                                                                                                                                  | `req-a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8`                                                        |
| **Category**            | Enum           | Classification of compliance scope (e.g., `security`, `privacy`, `audit-logging`).                                                                                                                                                     | `security`, `privacy`, `financial`, `custom`                                                         |
| **Priority**            | Enum           | Urgency level (`high`, `medium`, `low`).                                                                                                                                                                                      | `high`, `medium`, `low`                                                                               |
| **Source**              | String         | Origin of the rule (e.g., `GDPR Art. 5`, `NIST SP 800-53`, `internal_policy`).                                                                                                                                                     | `GDPR Art. 5.1`, `PCI DSS 3.2.2`, `company_policy:confidentiality`                                   |
| **Type**                | Enum           | Rule enforcement mode (`mandatory`, `policy-driven`, `best-practice`).                                                                                                                                                             | `mandatory`, `policy-driven`, `best-practice`                                                   |
| **Status**              | Enum           | Current compliance state (`not_started`, `in_progress`, `compliant`, `non-compliant`, `pending_review`).                                                                                                                    | `compliant`, `non-compliant`, `pending_review`                                                     |
| **Description**         | String         | Human-readable explanation of the requirement.                                                                                                                                                                               | `"Encrypt all PII data at rest using AES-256."`                                                    |
| **Impact**              | String         | Consequences of non-compliance (e.g., `fines`, `data_breach`, `reputation_damage`).                                                                                                                                                | `fines_up_to_4_percent_of_global_revenue`, `data_breach_notification_required`                  |
| **Owner**               | String         | Team/department responsible for enforcement (e.g., `security_team`, `devops`).                                                                                                                                                     | `security_team`, `compliance_officer`                                                              |
| **Automation**          | Boolean        | Flag indicating if the rule is automated (e.g., via CI/CD pipelines, monitoring tools).                                                                                                                                               | `true`, `false`                                                                                      |
| **Evidence**            | Array[Object]  | Proof of compliance (e.g., logs, scan reports, audit signatures).                                                                                                                                                                    | `[{type: "scan_report", file: "vuln_scan_2024-05-15.pdf", timestamp: "2024-05-15T14:30:00Z"}]` |
| **Related_Assets**      | Array[UUID]    | Linked system components (e.g., `config_files`, `code_repos`, `services`).                                                                                                                                                      | `[asset-98765432-1234-5678-90ab-cdef12345678, asset-12345678-90ab-cdef-1234-567890abcdef]` |
| **Remediation_Steps**   | Array[String]  | Step-by-step fixes for non-compliance.                                                                                                                                                                                         | `[`Apply patch to CVE-2023-1234`, `Update IAM policies to restrict S3 bucket access`]`             |
| **Tags**                | Array[String]  | Metadata labels (e.g., `critical`, `legacy_system`, `cross-team`).                                                                                                                                                              | `["critical", "cross-team", "third-party"]`                                                         |

---
## **Implementation Details**

### **1. Categorize Compliance Approaches**
| **Approach Type**      | **Use Case**                                                                 | **Example Rules**                                                                                     | **Tools/Techniques**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Mandatory**           | Legal/regulatory obligations (e.g., GDPR, HIPAA).                          | `"Log all access to patient data (HIPAA §164.310)."`                                                  | Audit logs, SIEM tools (Splunk, ELK), SIEM integrations.                                             |
| **Policy-Driven**       | Internal policies or industry standards (e.g., ISO 27001).                 | `"Enforce MFA for all admin users (ISO 27001 A.9.4.1)."`                                             | IAM tools (Okta, Azure AD), policy-as-code (Open Policy Agent).                                       |
| **Best Practice**       | Proactive security hygiene (e.g., CIS benchmarks).                         | `"Rotate credentials every 90 days."`                                                                | Password managers (HashiCorp Vault), automation scripts (Ansible, Terraform).                         |

---

### **2. Map Requirements to System Assets**
Use a **compliance matrix** to link rules to:
- **Configuration files** (e.g., Kubernetes `securityContext`, Docker `Dockerfile`).
- **Code repositories** (e.g., GitHub PR checks, SonarQube rules).
- **Infrastructure** (e.g., AWS CIS controls, Azure Policy assignments).

**Example Matrix Snippet:**
| **Requirement ID** | **Asset Type**   | **Asset Name**               | **Compliance Status** |
|--------------------|------------------|-------------------------------|------------------------|
| `req-a1b2c3d4...`  | Configuration    | `k8s-namespace-policy.yaml`   | Compliant              |
| `req-56789012...`  | Code Repository  | `repo:auth-service`           | Non-compliant          |

---

### **3. Automate Compliance Checks**
- **Static Analysis:** Integrate tools like **Trivy** (container scans) or **Checkmarx** (SAST) into CI/CD pipelines.
- **Dynamic Analysis:** Use **Open Policy Agent (OPA)** or **Kyverno** for runtime enforcement.
- **Audit Logging:** Centralize logs in **Splunk**, **Datadog**, or **CloudWatch**.

**Example CI/CD Pipeline Step (GitHub Actions):**
```yaml
name: GDPR-Compliance-Check
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
```

---

### **4. Generate Audit Reports**
Automate report generation with:
- **CLI Tools:** `compliance-cli` (custom scripts).
- **Dashboards:** Grafana plugins, Power BI connected to SIEM data.
- **Templates:** Predefined reports for regulators (e.g., **SOX Certification**, **PCI DSS RoC**).

**Example Report Metadata (JSON):**
```json
{
  "compliance_run": {
    "id": "report-2024-05-15",
    "timestamp": "2024-05-15T14:30:00Z",
    "status": "partial_compliance",
    "summary": {
      "compliant_rules": 42,
      "non_compliant_rules": 3,
      "automated_checks": 15,
      "manual_reviews": 2
    }
  }
}
```

---

## **Query Examples**

### **1. Find All High-Priority, Non-Compliant Rules**
```sql
SELECT *
FROM compliance_rules
WHERE priority = 'high' AND status = 'non-compliant'
ORDER BY impact;
```

**Expected Output:**
| **Requirement ID** | **Description**            | **Impact**                          | **Owner**         |
|--------------------|----------------------------|-------------------------------------|-------------------|
| `req-b1c2d3e4...`  | "Missing TLS 1.3 on API gateways." | `reputation_damage`          | `security_team`   |

---

### **2. List Assets Linked to a Specific Rule**
```graphql
query GetAssetsByRule($ruleId: UUID!) {
  rule(id: $ruleId) {
    id
    relatedAssets {
      id
      type
      name
    }
  }
}
```

**Variables:**
```json
{ "ruleId": "req-a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8" }
```

---

### **3. Aggregate Compliance Status by Category**
```python
from collections import defaultdict

# Pseudocode for aggregation
categories = defaultdict(lambda: {"compliant": 0, "non_compliant": 0})
for rule in db.query("SELECT category, status FROM compliance_rules"):
    categories[rule["category"]][rule["status"]] += 1
print(categories)
```

**Output:**
```json
{
  "security": {
    "compliant": 89,
    "non_compliant": 2
  },
  "privacy": {
    "compliant": 35,
    "non_compliant": 1
  }
}
```

---

## **Related Patterns**

| **Pattern Name**               | **Purpose**                                                                 | **When to Use**                                                                                     | **Integration Points**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Policy-as-Code (PaC)**        | Define compliance rules as code (e.g., OPA, Kyverno).                      | Automate enforcement across environments (dev, staging, prod).                                       | Integrates with **Compliance Approaches** for rule storage/retrieval.                                     |
| **Observability for Compliance** | Centralize logs, metrics, and traces for auditability.                     | Regulatory reporting (e.g., GDPR Article 30).                                                      | Connects to **Compliance Approaches** via evidence collection.                                            |
| **Remediation Automation**      | Auto-fix non-compliant items (e.g., patch vulnerabilities).                | Reduce manual effort in compliance workflows.                                                      | Reuses **Remediation_Steps** from **Compliance Approaches**.                                             |
| **Configuration Management**    | Ensure consistent system configurations (e.g., Terraform, Ansible).       | Enforce CIS benchmarks or platform-specific policies.                                               | Links to **Related_Assets** in **Compliance Approaches**.                                                |
| **Risk Assessment**             | Prioritize compliance efforts based on risk scores.                        | Balance resources for high-impact rules.                                                          | Uses **Impact** and **Priority** fields from **Compliance Approaches**.                                   |

---
**See Also:**
- [Policy-as-Code Best Practices](https://www.openpolicyagent.org/)
- [NIST SP 800-53 Compliance Mapping](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)