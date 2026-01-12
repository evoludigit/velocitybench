---
**[Pattern] Reference Guide: Compliance Migration**

---

## **Overview**
The **Compliance Migration** pattern ensures seamless transition of systems, data, and processes to meet regulatory requirements without disrupting operations. It addresses gaps between legacy systems and modern compliance standards (e.g., **GDPR, HIPAA, CCPA, PCI-DSS**) by structuring migration efforts into **assessment → remediation → validation → monitoring** phases.

This pattern applies to:
- Organizations transitioning from **legacy systems** (e.g., on-premise databases) to **cloud-native compliance frameworks**.
- Teams adopting **zero-trust architectures** or **data privacy regulations** in new markets.
- Configuring **identity governance, access controls, or audit trails** during infrastructure upgrades.

Key outcomes:
✔ **Regulatory alignment** without business downtime.
✔ **Audit-ready documentation** for compliance verification.
✔ **Scalable migration** for evolving compliance needs.

---

## **Schema Reference**

| **Component**               | **Description**                                                                 | **Example Values/Configuration**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Assessment Phase**        | Identify gaps vs. compliance requirements.                                   | Tools: Open Policy Agent (OPA), NIST CSF, CIS Benchmarks.<br>Output: Risk matrix (high/medium/low). |
| **Remediation Layer**       | Apply fixes (code, policies, infrastructure).                               | - **Data masking**: AWS KMS + DynamoDB conditional writes.<br>- **Access controls**: IAM policies + SAML 2.0.<br>- **Logging**: CloudTrail + SIEM integration. |
| **Validation Framework**    | Test compliance pre- and post-migration.                                     | - **Automated scans**: Trivy, Snyk.<br>- **Manual reviews**: Compliance audits via SOC 2 Type II.<br>- **Penetration tests**: Calysto, Burp Suite. |
| **Monitoring & Alerts**     | Continuous enforcement of compliance rules.                                  | - **Anomaly detection**: Cloud Security Posture Management (CSPM) tools.<br>- **Alerts**: Slack/email for policy violations.<br>- **Automated remediation**: Terraform policies. |
| **Data Migration Pipeline** | Secure transfer of PII/PCI/regulated data.                                  | - **Encryption**: TLS 1.3 in transit, AES-256 at rest.<br>- **Immutable backups**: WORM storage (e.g., AWS Glacier Deep Archive).<br>- **Deletion workflows**: GDPR-compliant retention policies. |
| **Documentation Repository**| Centralized compliance evidence.                                              | - **Artifacts**: Change logs, compliance whitepapers, training records.<br>- **Tools**: Confluence, Notion, or dedicated compliance platforms (e.g., OneTrust). |

---

## **Query Examples**

### **1. Assessing Compliance Gaps**
**Use Case:** Identify unpatched vulnerabilities in legacy systems against **PCI DSS v4.0**.

**SQL (Example for a relational database):**
```sql
SELECT
    table_name,
    column_name,
    'PCI DSS 3.5.3' AS requirement,
    CASE WHEN column_name LIKE '%credit_card%'
         OR column_name LIKE '%ssn%' THEN 'HIGH' ELSE 'MEDIUM' END AS risk_level
FROM
    information_schema.columns
WHERE
    table_schema = 'financial_transactions';
```

**Kubernetes (Helm Chart Check):**
```yaml
# Check if 'resource-requests' are set in pods (GCP compliance requirement)
{{- if not (hasKey .Values.pod.template.spec.containers.0.resources "requests") }}
  {{- fail "Missing resource requests in Pod template!" }}
{{- end }}
```

---

### **2. Validating Access Controls**
**Use Case:** Ensure **least-privilege access** for AWS IAM roles (HIPAA compliance).

**AWS CLI Query:**
```bash
# List IAM policies with excessive permissions
aws iam list-policies --scope Local --query 'Policies[?PolicyDefaultVersion?.Document?.Statement[?Effect==`Allow` && !contains(Condition, `{\"StringEquals\": {\"aws:RequestedRegion\": \"*\"}}` )] ]'
```

**Terraform Validation (HCL):**
```hcl
variable "allowed_regions" {
  type    = list(string)
  default = ["us-west-2", "eu-west-1"]
}

resource "aws_iam_policy" "example" {
  name        = "restricted_access"
  description = "HIPAA-compliant IAM policy"

  policy {
    version = "2012-10-17"
    statement {
      effect    = "Allow"
      actions   = ["s3:GetObject"]
      resources = ["arn:aws:s3:::example-bucket/**"]

      condition {
        test     = "StringEquals"
        variable = "aws:RequestedRegion"
        values   = var.allowed_regions
      }
    }
  }
}
```

---

### **3. Auditing Data Migration**
**Use Case:** Log all GDPR-compliant data deletions in Azure.

**Azure PowerShell:**
```powershell
# Query Log Analytics for Data Deletion Events
Get-AzLogAnalyticsQuery -WorkspaceName "compliance_ws" |
    Where-Object { $_.Query -like "*Delete*" -and $_.Query -like "*GDPR*" } |
    Select-Object -First 10
```

**Output Example:**
```
| TimeGenerated | OperationName | User | Status | ComplianceReference
|----------------|----------------|------|--------|-----------------------
| 2023-10-15     | Delete-User     | admin| Success| GDPR ARTICLE_17
```

---

### **4. Automated Policy Enforcement**
**Use Case:** Enforce **CCPA opt-out requests** in a Django app.

**Python (Flask Middleware):**
```python
from functools import wraps

def ccpa_compliant(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if request.headers.get('X-CCPA-Opt-Out') == 'true':
            return jsonify({"error": "Access denied"}), 403
        return f(request, *args, **kwargs)
    return wrapper

@app.route('/api/data')
@ccpa_compliant
def get_data():
    return jsonify({"data": "sensitive_info"})
```

---

## **Related Patterns**
To complement **Compliance Migration**, consider combining with:

1. **[Zero Trust Architecture]**
   - **Purpose:** Enforces least-privilege access post-migration.
   - **Integration:** Use **SIEM tools** (e.g., Splunk) to log Zero Trust policy violations detected during migration.

2. **[Data Masking & Tokenization]**
   - **Purpose:** Protect PII in transit during compliance migrations.
   - **Example:** Replace credit card numbers with tokens (e.g., AWS Tokenization).

3. **[Infrastructure as Code (IaC) with Compliance Checks]**
   - **Purpose:** Embed compliance rules in IaC pipelines (e.g., **Terraform policies** or **Open Policy Agent**).

4. **[Event-Driven Compliance Alerts]**
   - **Purpose:** Trigger alerts for non-compliant states (e.g., **AWS Config + SNS**).

5. **[Chaos Engineering for Compliance]**
   - **Purpose:** Test resilience of compliance controls under failure scenarios (e.g., **Gremlin + compliance metrics**).

---
**Tools & Frameworks for Compliance Migration:**
| **Category**          | **Tools**                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| **Policy as Code**    | Open Policy Agent (OPA), Kyverno, Terraform Policies                     |
| **Audit & Logging**   | AWS CloudTrail, Azure Monitor, SIEM (Splunk, Datadog)                    |
| **Data Protection**   | AWS KMS, HashiCorp Vault, Microsoft Purview                              |
| **Testing**           | Trivy, Snyk, AWS Inspector, Calysto                                     |
| **Documentation**     | Confluence, Notion, OneTrust, Collibra                                   |

---
**Best Practices:**
- **Phase 1:** Document *as-is* compliance state before migration.
- **Phase 2:** Use **immutable infrastructure** (e.g., Terraform) to prevent drift.
- **Phase 3:** Automate **90% of compliance checks** (e.g., CI/CD pipelines).
- **Phase 4:** Schedule **quarterly compliance reviews** with audit trails.