**[Pattern] Governance Configuration Reference Guide**

---

### **1. Overview**
The **Governance Configuration** pattern defines a structured approach to enforce compliance, manage access controls, and ensure consistency across organizational systems, APIs, and data flows. Governance configurations act as enforceable policies that regulate permissions, auditing, data classification, and operational guardrails.

This pattern is implemented via:
- **Policy definitions** (e.g., IAM roles, RBAC rules, data retention policies)
- **Configuration standards** (e.g., API throttling limits, field-level encryption)
- **Audit logging** (mandatory tracking of actions)
- **Automated validation** (preventing non-compliant deployments)

Governance configurations are often tied to **infrastructure-as-code (IaC)** tools (Terraform, CloudFormation) or platform-native configuration services (e.g., AWS IAM Policy Generator).

**Key Use Cases:**
- Ensuring **least-privilege access** for services and users.
- Enforcing **data sovereignty** (e.g., GDPR compliance via region-specific storage).
- Standardizing **operational checks** (e.g., backup window enforcement).

---

### **2. Schema Reference**
Governance configurations are defined via structured metadata. Below are core components and their schemas.

#### **Core Schema Components**
| Component               | Description                                                                 | Required Fields                                                                 |
|-------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **PolicySet**           | A collection of linked governance rules.                                  | `id`, `name`, `version`, `appliedTo`, `effectiveDate`                          |
| **ResourceDefinition**  | The target system/resource (e.g., API endpoint, storage bucket).           | `type`, `namespace`, `identifier`, `owner`                                     |
| **Rule**                | Specific governance constraint.                                            | `id`, `ruleType`, `severity` (high/medium/low), `action` (allow/deny)        |
| **Parameter**           | Rule-specific settings (e.g., timeout, max retries).                       | `name`, `value`, `dataType` (string/int/enum)                                 |
| **AuditLog**            | Tracking of rule application/violations.                                  | `timestamp`, `ruleId`, `resourceId`, `complianceStatus` (pass/fail/warning)   |

#### **Example Rule Schema**
```json
{
  "policySet": {
    "id": "ps-data-retention",
    "rules": [
      {
        "id": "r-daily-backup",
        "ruleType": "backupPolicy",
        "severity": "high",
        "action": "require",
        "parameters": [
          {
            "name": "retentionDays",
            "value": "7",
            "dataType": "int"
          }
        ]
      }
    ]
  }
}
```

#### **Supported Rule Types**
| Rule Type              | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **IAM Policy**         | Specifies access controls (e.g., `Allow: s3:GetObject`).                   |
| **Rate Limiting**      | Throttles API calls (e.g., `maxRequests: 1000/sec`).                      |
| **Encryption**         | Enforces TLS/field-level encryption (e.g., `encryptFields: ["PII"]`).      |
| **Audit Logging**      | Requires logging for sensitive operations (e.g., `logUserActions: true`).   |
| **Network Restriction**| Restricts traffic to VPCs/private subnets.                                 |

---

### **3. Query Examples**
Governance configurations can be queried via APIs or CLI tools to inspect compliance or validate rules.

#### **A. Querying Applicable Rules**
**CLI (Pseudo-Command):**
```bash
get-governance-rules --resource-type "s3-bucket" --namespace "prod"
```
**Expected Response:**
```json
{
  "rules": [
    {
      "id": "r-s3-versioning",
      "ruleType": "storagePolicy",
      "severity": "medium",
      "action": "require"
    }
  ]
}
```

#### **B. Validating a Resource Against Policies**
**API Endpoint:**
`POST /api/validate`
**Request Body:**
```json
{
  "resource": {
    "type": "api-gateway",
    "config": { "throttling": { "rateLimit": 900 } }
  }
}
```
**Response:**
```json
{
  "compliance": {
    "violations": [
      {
        "ruleId": "r-api-throttle",
        "issue": "Rate limit too high (max allowed: 500)."
      }
    ]
  }
}
```

#### **C. Updating a Policy**
**CLI Command:**
```bash
update-governance-policy --policy-id "ps-sso" --add-rule '{
  "id": "r-mfa-enforcement",
  "ruleType": "authPolicy",
  "action": "require"
}'
```

---

### **4. Implementation Details**

#### **A. Key Concepts**
1. **Policy Inheritance:**
   Governance rules can be inherited from parent configurations (e.g., a `global` policy applied to all `dev` environments).

2. **Change Freezes:**
   Critical periods (e.g., during audits) can lock configurations to prevent edits.

3. **Versioning:**
   Policies include `version` fields to track updates. Example:
   ```json
   "version": "2.1",  // Latest stable; "1.0" = deprecated
   ```

4. **Contextual Rules:**
   Rules can adapt to runtime context (e.g., geo-location-based data processing).

#### **B. Integration Points**
| System               | Integration Approach                                                                 |
|----------------------|------------------------------------------------------------------------------------|
| **IaC Tools**        | Embed governance rules in manifests (e.g., Terraform `locals` blocks).             |
| **CI/CD Pipelines**  | Fail builds if resources violate policies (e.g., GitHub Actions `if: $GOVERNANCE_OK`). |
| **API Gateways**     | Enforce rules at runtime (e.g., Kong’s `plugins: governance`).                     |
| **Data Lakes**       | Use tools like Apache Atlas for metadata governance.                                |

#### **C. Validation Strategies**
| Strategy               | Description                                                                         |
|------------------------|-------------------------------------------------------------------------------------|
| **Static Checks**      | Scan IaC templates for rule violations pre-deploy (e.g., `tfsec` for Terraform).   |
| **Runtime Enforcement**| Apply rules during execution (e.g., AWS Lambda event policies).                   |
| **Third-Party Audits** | External tools (e.g., Open Policy Agent) validate configurations.                 |

---

### **5. Related Patterns**
| Pattern                     | Description                                                                       |
|-----------------------------|-----------------------------------------------------------------------------------|
| **Infrastructure as Code**  | Governance configurations are version-controlled alongside infrastructure.          |
| **Attribute-Based Access**  | Extends RBAC with dynamic policies (e.g., `allow if user.department = "Finance"`). |
| **Observability**           | Logs and metrics track governance rule adherence (e.g., Prometheus + Grafana).    |
| **Data Mesh**               | Decentralizes governance while maintaining centralized standards.                 |

---

### **6. Common Pitfalls & Mitigations**
| Pitfall                          | Mitigation                                                                       |
|----------------------------------|----------------------------------------------------------------------------------|
| **Overly Complex Rules**         | Start with coarse-grained policies; refine iteratively.                          |
| **Unreachable Policies**         | Use `appliedTo` to target only relevant resources.                               |
| **Configuration Drift**          | Sync governance configs with IaC repositories (e.g., GitOps).                    |
| **False Positives**              | Implement rule severity tiers (e.g., `low` = advisory, `high` = blocking).      |

---
**Appendix: Example IaC Snippet (Terraform)**
```hcl
resource "aws_iam_policy" "governance_example" {
  name        = "data-retention-policy"
  description = "Enforces 7-day backup retention."

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Deny",
      Action   = "s3:PutObject",
      Resource = "arn:aws:s3:::${var.bucket-name}/*",
      Condition = {
        StringNotEquals = {
          "s3:x-amz-meta-retention": "7"
        }
      }
    }]
  })
}
```