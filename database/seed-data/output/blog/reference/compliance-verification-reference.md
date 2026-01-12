# **[Pattern] Compliance Verification Reference Guide**

---

## **Overview**
The **Compliance Verification** pattern ensures that business operations, data, and processes adhere to regulatory, security, and industry-specific standards. This pattern automates and centralizes compliance checks across systems, reducing manual enforcement errors and accelerating audit readiness. It integrates with event-driven workflows to validate compliance in real time, log violations, and trigger corrective actions. By standardizing compliance checks, this pattern mitigates risks, ensures traceability, and aligns with frameworks like **GDPR, HIPAA, PCI-DSS, SOX, or ISO 27001**.

---

## **1. Key Concepts & Implementation Details**

### **Core Components**
| **Component**               | **Description**                                                                                     | **Example Use Case**                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Compliance Rules Engine** | Defines validation rules (e.g., "All PII must be encrypted"), scoped by entity (user, system, data). | Enforcing GDPR data anonymization thresholds. |
| **Audit Logs**              | Immutable records of all compliance checks, violations, and remediation actions.                   | Tracking SOX financial transaction audits.    |
| **Notification Handler**   | Triggers alerts (emails, Slack, ticketing systems) for violations or automated remediation failures. | Notifying security teams on PCI-DSS failures. |
| **Remediation Workflow**    | Automated or guided steps (e.g., redaction, access revocation) to remediate violations.             | Auto-deleting expired credentials.            |
| **Regulatory Scopes**       | Tags/compartments grouping rules by compliance framework (e.g., `GDPR:TTP`, `HIPAA:PHI`).          | Tagging healthcare records under HIPAA.       |
| **Validation Hooks**        | Integrates into pipelines (CI/CD, ETL, API calls) to verify compliance pre-deployment.              | Blocking deployments with unencrypted secrets. |

---

### **Common Validation Types**
| **Type**          | **Purpose**                                                                                      | **Example Rule**                              |
|-------------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Data Integrity** | Ensures data hasn’t been tampered with (e.g., checksums, hashes).                                | Verify OS certificates haven’t been altered.  |
| **Access Control**| Validates user/system permissions align with least-privilege principles.                          | Block `sudo` access for temporary users.     |
| **Policy Enforcement** | Checks adherence to organizational policies (e.g., password complexity).                         | Enforce 14-character passwords for admins.   |
| **Regulatory Checks** | Applies rules from frameworks like GDPR (consent logs) or PCI-DSS (PIN storage bans).            | Flag unencrypted credit card fields.          |
| **Configuration Audits** | Scans infrastructure (servers, containers) for misconfigurations (e.g., open S3 buckets).      | Close unencrypted SAP system connections.     |

---

### **Data Flow**
1. **Trigger**: Event (e.g., user login, file upload) or scheduled check.
2. **Rule Evaluation**: Compliance rules engine applies validation logic.
3. **Result Handling**:
   - **Pass**: Log success; continue workflow.
   - **Fail**: Log violation + notify stakeholders; trigger remediation.
4. **Remediation**: Automated fix (where possible) or human review.
5. **Audit**: Immutable record stored in compliance database.

---
## **2. Schema Reference**
Below is the core data schema for the **Compliance Verification** pattern.

### **2.1 Core Entities**
| **Entity**          | **Fields**                                                                                     | **Data Type**          | **Description**                                  |
|---------------------|-------------------------------------------------------------------------------------------------|------------------------|--------------------------------------------------|
| **ComplianceRule**  | `id`, `name`, `description`, `scopeTags` (e.g., `GDPR:DataMinimization`), `ruleType` (e.g., `AccessControl`), `severity` (LOW/MED/HIGH/CRITICAL), `enabled` | UUID, String, String, List<String>, Enum, Enum, Boolean | Defines a validation rule (e.g., "Block non-encrypted emails"). |
| **AuditEvent**      | `id`, `ruleId`, `entityId`, `timestamp`, `status` (PASSED/FAILED/REMIDIATED), `details` (JSON), `remediationSteps` (List<Step>) | UUID, UUID, UUID, ISO8601, Enum, JSON, List<Step> | Immutable log of a compliance check.              |
| **RemediationStep** | `stepId`, `action` (e.g., `REDACT`, `REVOKE_ACCESS`), `status` (PENDING/COMPLETED/FAILED), `attempts`, `notes` | UUID, Enum, Enum, Int, String | Steps to resolve a violation (e.g., "Mask SSN in database"). |

### **2.2 Example JSON Payloads**
#### **Rule Definition**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "PCI-DSS: No Plaintext Credit Cards",
  "description": "Block storage of unencrypted credit card data.",
  "scopeTags": ["PCI-DSS:PaymentData", "Environment:Production"],
  "ruleType": "DataIntegrity",
  "severity": "CRITICAL",
  "enabled": true,
  "validationScript": "require('zod'); const schema = z.object({ cardNumber: z.string().min(16) }); schema.parse(data).catch(() => { throw 'Unencrypted card data detected'; });"
}
```

#### **Audit Event**
```json
{
  "id": "6e8bc9f1-6c8a-4e7b-a7e7-8f4f05050505",
  "ruleId": "550e8400-e29b-41d4-a716-446655440000",
  "entityId": "transaction_123",
  "timestamp": "2023-10-15T14:30:00Z",
  "status": "FAILED",
  "details": {
    "violation": "Plaintext credit card number '4111111111111111' found in `orders` table.",
    "affectedFields": ["cardNumber"]
  },
  "remediationSteps": [
    {
      "stepId": "a1b2c3d4-e5f6-4789-a0b1-234567890abc",
      "action": "REDACT",
      "status": "PENDING",
      "notes": "Mask field with token `XXXX-XXXX-XXXX-1111`"
    }
  ]
}
```

---

## **3. Query Examples**
### **3.1 List All Active Compliance Rules for GDPR**
```sql
SELECT * FROM ComplianceRule
WHERE enabled = true
AND scopeTags LIKE '%GDPR%';
```

### **3.2 Find Unresolved Violations for HIPAA-PHI Data**
```sql
SELECT a.*
FROM AuditEvent a
JOIN ComplianceRule r ON a.ruleId = r.id
WHERE r.scopeTags LIKE '%HIPAA:PHI%'
  AND a.status = 'FAILED'
  AND a.remediationSteps.status = 'PENDING';
```

### **3.3 Generate a Compliance Report for SOX Audits (Past 30 Days)**
```sql
SELECT
  r.name AS rule_name,
  COUNT(a.id) AS violation_count,
  MAX(a.timestamp) AS last_violation
FROM AuditEvent a
JOIN ComplianceRule r ON a.ruleId = r.id
WHERE r.scopeTags LIKE '%SOX%'
  AND a.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY r.name;
```

### **3.4 Check if a User Has Pending Access Violations**
```sql
SELECT u.username, a.details
FROM User u
JOIN AuditEvent a ON u.id = a.entityId
JOIN ComplianceRule r ON a.ruleId = r.id
WHERE r.ruleType = 'AccessControl'
  AND a.status = 'FAILED'
  AND a.remediationSteps.status = 'PENDING';
```

---

## **4. Implementation Steps**

### **4.1 Design Phase**
1. **Inventory Assets**: Catalog systems, data, and processes to scope compliance rules.
   - Example: List all databases storing PII under **GDPR**.
2. **Map Frameworks**: Align rules to regulatory requirements (e.g., **HIPAA’s PHI protections**).
3. **Define Scopes**: Tag entities/rules by environment (e.g., `Production`, `Staging`).

### **4.2 Rule Authoring**
- **Static Rules**: Use schema validation (e.g., JSON Schema, OpenAPI) for API/data checks.
- **Dynamic Rules**: Write custom scripts (e.g., Python, JavaScript) for complex logic.
  ```javascript
  // Example: Check for weak passwords in user database
  const weakPasswords = users.filter(u => /^[a-z]{4}$/.test(u.password));
  if (weakPasswords.length > 0) throw new Error('Weak password detected');
  ```
- **Integrate Hooks**: Deploy rules as **pre-commit hooks (Git)**, **pre-deploy checks (CI/CD)**, or **runtime validators (API gateways)**.

### **4.3 Automation**
- **Trigger Sources**:
  - **Scheduled**: Daily scans for misconfigurations.
  - **Event-Driven**: On file uploads, user logins, or system changes.
- **Remediation**:
  - **Automated**: Patch misconfigurations (e.g., close open ports).
  - **Semi-Automated**: Flag for human review (e.g., "Require approval to delete records").

### **4.4 Monitoring & Reporting**
- **Dashboards**: Visualize violation trends (e.g., Grafana, Dash).
- **Alerts**: Configure thresholds (e.g., "Alert if >5 HIPAA violations/day").
- **Audit Trail**: Ensure logs are **immutable** and **preserved** per retention policies.

---

## **5. Query Examples (Code Snippets)**
### **5.1 Validate API Requests with OpenAPI + Compliance Rules**
```yaml
# openapi.yaml (Swagger/OpenAPI)
paths:
  /orders:
    post:
      security:
        - apiKeyAuth: []
      x-compliance:
        - rule: "PCI-DSS:NoPlaintextCards"
        - rule: "GDPR:DataMinimization"
      responses:
        201: { description: "Order created" }
```

**Integration Code (Node.js):**
```javascript
const { OpenAPIValidator } = require('openapi-validator');
const complianceEngine = require('./compliance-engine');

async function validateOrder(req, res) {
  const validator = new OpenAPIValidator();
  const complianceResult = await validateSchema(req.body, validator);
  const ruleChecks = await complianceEngine.checkRules(
    req.body,
    ["PCI-DSS:NoPlaintextCards"]
  );

  if (!complianceResult.valid || ruleChecks.some(r => r.status === 'FAILED')) {
    return res.status(400).json({ errors: ruleChecks });
  }
  // Proceed if valid.
}
```

### **5.2 Scan Kubernetes Pods for Compliance**
```bash
# Example using OPA/Gatekeeper (Open Policy Agent)
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8s-required-annotations
spec:
  crd:
    spec:
      names:
        kind: KubernetesPodSecurity
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package kubernetes.admission
        violation[{"msg": msg}] {
          input.review.op == "CREATE"
          not input.review.object.metadata.annotations["compliance.checked"] == "true"
          msg := sprintf("Pod %v lacks compliance annotation", [input.review.object.metadata.name])
        }
```

### **5.3 Remediate Unencrypted Secrets in Vault**
```bash
# Example using HashiCorp Vault + Compliance Plugin
vault policy-test -policy-name=compliance-policy
# Output: Violations for policies like:
#   "secret.leak_detection" -> "Flagged unencrypted secrets in `dev/db_creds`"
```

**Automated Fix:**
```bash
#!/bin/bash
# Script to encrypt secrets detected by compliance scan
for secret in $(vault kv list -mount=secret dev/); do
  vault kv patch -mount=secret "$secret" encrypted=true
done
```

---

## **6. Tools & Integrations**
| **Category**               | **Tools**                                                                                     | **Use Case**                                  |
|----------------------------|-----------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Rule Engine**            | [Open Policy Agent (OPA)](https://www.openpolicyagent.org/), [Kyverno](https://kyverno.io/) | Kubernetes pod policy enforcement.           |
| **Audit Logging**          | [Loki + Promtail](https://grafana.com/oss/loki/), [ELK Stack](https://www.elastic.co/elk-stack) | Centralized compliance event logs.            |
| **CI/CD Integration**      | [GitHub Actions](https://github.com/features/actions), [Jenkins](https://www.jenkins.io/) | Block non-compliant deployments.              |
| **Data Scanning**          | [Trivy](https://aquasecurity.github.io/trivy/), [Prisma Cloud](https://prismacloud.io/) | Scan containers/images for vulnerabilities.   |
| **Database Security**      | [pgAudit](https://www.pgaudit.org/), [AWS Macie](https://aws.amazon.com/macie/)              | Audit database queries for compliance.        |
| **Notification**           | [PagerDuty](https://www.pagerduty.com/), [Slack API](https://api.slack.com/)                  | Alert teams on violations.                   |

---

## **7. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                      |
|----------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **[Event Sourcing](link)**       | Capture state changes as immutable events for auditing.                                               | When compliance requires a detailed audit trail.    |
| **[Policy as Code](link)**       | Define security/compliance policies in code (e.g., OPA, Terraform).                                   | For infrastructure-as-code (IaC) compliance.         |
| **[Zero Trust](link)**           | Enforce least-privilege access and continuous validation of identities.                             | For PCI-DSS or HIPAA environments.                  |
| **[Data Masking](link)**         | Dynamically redact sensitive data in queries/reports.                                               | GDPR or HIPAA compliance for sensitive datasets.    |
| **[Immutable Infrastructure](link)** | Treat infrastructure as code with version control and automated rollbacks.                       | Ensuring compliance across deployments.              |

---
## **8. Best Practices**
1. **Start Small**: Pilot with high-risk areas (e.g., PII storage) before scaling.
2. **Automate Remediation**: Where possible, auto-fix violations (e.g., patch misconfigurations).
3. **Collaborate with Teams**: Work with legal, security, and devops to align rules.
4. **Test Rules**: Use chaos engineering to validate rule coverage (e.g., simulate data breaches).
5. **Document Exceptions**: Log manual overrides with justification for audit purposes.
6. **Regular Reviews**: Update rules to reflect regulatory updates (e.g., GDPR changes).
7. **Performance**: Optimize rule execution to avoid bottlenecks in high-volume systems.
8. **Immutable Logs**: Use WORM (Write Once, Read Many) storage for audit trails.

---
## **9. Troubleshooting**
| **Issue**                          | **Root Cause**                                  | **Solution**                                      |
|-------------------------------------|-------------------------------------------------|---------------------------------------------------|
| **False Positives**                 | Overly strict rules or misconfigured validation. | Refine rule thresholds or add exceptions.         |
| **High Remediation Backlog**        | Rules trigger too many unresolved violations.   | Prioritize critical rules; automate fixes.        |
| **Performance Degradation**         | Excessive rule evaluations in high-traffic paths. | Cache rule results or use sampling.               |
| **Audit Log Overload**              | Too many small events being logged.              | Aggregate similar events; use sampling.          |
| **Rule Conflicts**                  | Multiple rules apply to the same entity.         | Define rule precedence or merge overlapping rules. |

---
## **10. Example Workflow: GDPR Consent Verification**
1. **Trigger**: User submits a form to update consent preferences.
2. **Validation**:
   - Rule: `GDPR:ConsentLogging` → Check if user confirmed via checkbox.
   - Rule: `GDPR:DataRetention` → Verify no personal data is stored beyond 7 years.
3. **Result**:
   - If failed: Block submission; notify user to re-consent.
   - If passed: Log consent in immutable audit trail.
4. **Remediation**: Auto-archive old records exceeding retention period.

---
**Last Updated**: [MM/YYYY]
**Contact**: [support@yourorg.com] for implementation guidance.