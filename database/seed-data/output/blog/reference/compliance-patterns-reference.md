# **[Compliance Patterns] Reference Guide**

---

## **Overview**
Compliance Patterns define structured, reusable approaches to ensure systems, processes, or applications adhere to regulatory, industry, or organizational standards. This pattern provides a modular framework for embedding compliance checks (e.g., GDPR, HIPAA, CCPA) into workflows, data flows, or infrastructure. Implementations typically include:
- **Policy Enforcement Points (PEPs):** Automated checks (e.g., access controls, data encryption).
- **Compliance Reporting:** Audit logs, automated certifications, and metrics.
- **Dynamic Compliance:** Context-aware adjustments (e.g., jurisdiction-based data handling).

Use this pattern when you need to **standardize compliance** across systems, reduce manual audits, or ensure real-time adherence to evolving regulations.

---

## **Schema Reference**
The pattern consists of **three core components**, represented in the following schema:

| **Component**               | **Purpose**                                                                 | **Key Fields/Attributes**                                                                 | **Example Values**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Compliance Rule**         | Defines a specific regulatory or internal requirement (e.g., "PII must be encrypted at rest"). | - `rule_id` (UUID) <br> - `name` (string) <br> - `description` (string) <br> - `scope` (object: `{data_type, entity_type, jurisdiction}`) <br> - `severity` (enum: `low/moderate/high/critical`) <br> - `status` (enum: `active/draft/deprecated`) <br> - `dependencies` (array of `rule_id`s) | `{ "rule_id": "550e8400-e29b-41d4-a716-446655440000", "name": "Encryption-at-Rest", "scope": { "data_type": "PII", "jurisdiction": "EU" } }` |
| **Compliance Check**        | Implements a rule via code or external service (e.g., a Lambda function validating encryption keys). | - `check_id` (UUID) <br> - `rule_id` (reference) <br> - `type` (enum: `pre_process/post_process/api_gateway/lambda/terraform`) <br> - `implementation` (string/URL to code/service) <br> - `frequency` (enum: `real_time/batch/daily`) <br> - `output_format` (enum: `json/logs/slack`) | `{ "check_id": "660fce6f-9c61-418f-9c7d-78a0b55d9403", "type": "lambda", "implementation": "s3://compliance-lambda/validate_encryption.py" }` |
| **Compliance Audit**        | Records execution results (pass/fail) and evidence for reporting. | - `audit_id` (UUID) <br> - `check_id` (reference) <br> - `timestamp` (ISO 8601) <br> - `status` (enum: `pass/fail/pending`) <br> - `details` (string/json) <br> - `remediation_steps` (array of strings) <br> - `evidence` (URL/reference to logs/attachments) | `{ "audit_id": "770fce6f-9c61-418f-9c7d-78a0b55d9404", "status": "fail", "details": "Encryption key rotation not configured", "evidence": "s3://audits/report_2023.csv" }` |

---

## **Implementation Details**
### **1. Core Concepts**
- **Modularity:** Rules and checks are decoupled for reuse (e.g., a single "GDPR Consent" rule can apply to multiple services).
- **Context Awareness:** Checks can filter based on **entity type** (e.g., "user profile" vs. "payment transaction") or **jurisdiction** (e.g., EU vs. US).
- **Automation Layers:**
  - *Pre-processing:* Validate inputs before database writes (e.g., mask PII).
  - *Post-processing:* Enforce rules after API calls (e.g., log access).
  - *Infrastructure-as-Code (IaC):** Embed checks in Terraform/CloudFormation (e.g., enforce IAM policies).

- **Evidence Collection:** Audits must preserve **immutable logs** (e.g., AWS CloudTrail, SIEM tools) for compliance proofs.

### **2. Integration Patterns**
| **Context**               | **Implementation Strategy**                                                                 | **Tools/Libraries**                                                                 |
|---------------------------|--------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **API Gateways**          | Validate requests/responses using OAS3 extensions or AWS API Gateway authorizers.           | OpenAPI/Swagger, AWS Lambda Authorizers, Kong plugins                         |
| **Databases**             | Enforce rules via triggers, stored procedures, or application logic.                       | PostgreSQL tslint, MongoDB validators, DynamoDB IAM policies                  |
| **Container Orchestration** | Inject sidecar containers (e.g., Istio) or pre-start hooks to run compliance checks.       | Kubernetes MutatingAdmissionWebhooks, Linkerd, Aqua Security                |
| **CI/CD Pipelines**       | Fail builds if compliance checks fail (e.g., scan for hardcoded secrets).                 | SonarQube, Checkmarx, GitHub Actions, GitLab Pipelines                       |
| **Serverless**            | Use event-driven checks (e.g., Lambda triggers for DynamoDB writes).                       | AWS Lambda, Google Cloud Functions, Azure Functions                         |

### **3. Dynamic Compliance**
Adjust checks based on:
- **User Location:** Detect jurisdiction via IP/headers and apply region-specific rules (e.g., CCPA for California residents).
- **Data Sensitivity:** Escalate checks for PII vs. anonymous data.
- **Temporal Rules:** Schedule checks (e.g., "Rotate encryption keys every 90 days").

**Example:** A compliance rule for "Data Retention" might:
1. Query the user’s location via `aws-lambda-ip` (or MaxMind GeoIP).
2. Apply a 1-year retention for EU users, 3 years for US users.
3. Trigger a Lambda to archive/expire data via S3 Lifecycle Policies.

---

## **Query Examples**
### **1. List Active Compliance Rules for a Data Type**
```sql
SELECT c.rule_id, c.name, c.severity
FROM Compliance_Rule c
WHERE c.status = 'active'
  AND c.scope->>'data_type' = 'PII';
```
**Output:**
| rule_id               | name                | severity   |
|-----------------------|---------------------|------------|
| 550e8400-e29b...      | Encryption-at-Rest  | high       |
| 660fce6f-9c61...      | Mask-PII-in-Logs    | moderate   |

---

### **2. Find Recent Audit Failures for a Check**
```graphql
query {
  complianceAudits(
    where: { status: "fail", timestamp_gt: "2023-10-01T00:00:00Z" }
    orderBy: timestamp_DESC
    first: 10
  ) {
    audit_id
    check_id
    details
    remediation_steps
  }
}
```
**Output:**
```json
[
  {
    "audit_id": "770fce6f-9c61...",
    "check_id": "660fce6f-9c61...",
    "details": "AWS KMS key rotation not completed",
    "remediation_steps": ["Run 'aws kms enable-key-rotation' on key 'arn:aws:kms:..."]
  }
]
```

---

### **3. Terraform Example: Enforce IAM Least Privilege**
```hcl
resource "aws_iam_policy" "compliance_deny_public_access" {
  name        = "deny_public_s3_access"
  description = "Blocks S3 buckets from being public (GDPR compliance)"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Deny",
        Action   = "s3:*",
        Resource = "arn:aws:s3:::my-bucket/*",
        Condition = {
          Bool = { "aws:RequestTag/Compliance-Approved": "false" }
        }
      }
    ]
  })
}
```
**Trigger:** Attach this policy to IAM roles/users via a **Compliance Check** of type `iam`.

---

## **Related Patterns**
Consume or complement these patterns for broader compliance architectures:

| **Pattern**                     | **Relationship**                                                                 | **When to Use**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Data Masking](https://...)**  | Compliance Patterns may rely on Data Masking to obscure sensitive fields.       | When protecting PII in logs/dashboards.                                         |
| **[Audit Logging](https://...)** | Compliance Audits feed into centralized logging systems.                        | For tracking user actions across services (e.g., AWS CloudTrail + OpenSearch). |
| **[Secrets Management](https://...)** | Rules like "Never hardcode API keys" are enforced via Secrets Management.      | Rotating credentials or retrieving secrets at runtime.                          |
| **[Permission Management](https://...)** | IAM/OAuth policies are validated by Compliance Checks.                          | Granular access control for multi-region deployments.                            |
| **[Event-Driven Architecture](https://...)** | Triggers checks on data changes (e.g., Kafka topics → Lambda).               | Real-time compliance for streaming data (e.g., GDPR "Right to Erasure").        |

---

## **Best Practices**
1. **Start Small:** Pilot with 1–2 high-severity rules (e.g., "Block public S3 buckets") before scaling.
2. **Automate Remediation:** Pair checks with self-healing mechanisms (e.g., Terraform apply on audit failure).
3. **Document Assumptions:** Clearly define scope exceptions (e.g., "Rule X does not apply to legacy systems").
4. **Test in Staging:** Use tools like **ComplianceAsCode** (Open Policy Agent) to validate rules before production.
5. **Monitor False Positives:** Alert on recurring audit failures to refine checks.

---
**See Also:**
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) for control baselines.
- [OWASP Compliance Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Compliance_Cheat_Sheet.html) for common pitfalls.