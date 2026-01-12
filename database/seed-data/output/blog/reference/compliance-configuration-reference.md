**[Pattern] Compliance Configuration Reference Guide**

---

### **1. Overview**
The **Compliance Configuration** pattern ensures that applications and systems adhere to regulatory standards, industry best practices, and organizational policies by centralizing configuration rules. This pattern enforces consistency, automates compliance checks, and simplifies audit trails by exposing configurable rules (e.g., access control, logging, encryption) via a standardized interface. It is ideal for systems requiring **GDPR, HIPAA, PCI-DSS, or SOC 2 compliance** or internal policy alignment (e.g., least-privilege access, data retention).

Key benefits:
- **Centralized governance**: Rules are defined in one place and applied uniformly.
- **Dynamic enforcement**: Rules can be updated without redeploying applications.
- **Auditability**: Change tracking and automated validation logs compliance status.
- **Scalability**: Supports large-scale environments with minimal operational overhead.

---

### **2. Key Concepts & Implementation Details**

#### **2.1 Core Components**
| **Component**          | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Compliance Rules**   | Declarative policies (e.g., "All PII must be encrypted at rest," "Logs must retain 1 year"). Rules are versioned and tied to specific compliance frameworks.                                                | `{"rule_id": "ENCRYPTION_REQUIRED", "framework": "PCI-DSS", "severity": "high"}`          |
| **Configuration Profiles** | Groups of rules applied to systems/environments (e.g., "Production-Level," "Dev-Test"). Profiles inherit or override rules.                                                                                  | Profile: `{"name": "Production", "rules": ["ENCRYPTION_REQUIRED", "AUDIT_LOGS_ENABLED"]}` |
| **Enforcement Engine** | Validates system configurations against active rules. May integrate with CI/CD pipelines, infrastructure-as-code (IaC), or runtime monitors.                                                       | Checks if AWS S3 buckets comply with `ENCRYPTION_REQUIRED` during deployment.                  |
| **Audit Logs**         | Immutable records of rule violations, compliance checks, and configuration changes with timestamps, user context, and remediation steps.                                                                   | `{"event": "FAILED_CHECK", "rule": "AUDIT_LOGS_ENABLED", "resource": "app-logger", "time": "2023-10-01T12:00Z"}` |
| **Notification Triggers** | Alerts (email, Slack, SIEM) for rule breaches or profile changes, escalating based on severity.                                                                                                             | Slack alert: `⚠️ Rule "ENCRYPTION_REQUIRED" failed for database `prod-db`. Fix by EOD.`      |

#### **2.2 Compliance Frameworks Supported**
The pattern abstracts specific frameworks but provides **mapping templates** for common standards:
- **GDPR**: Data subject access rights, consent tracking, right-to-erasure.
- **HIPAA**: Protected health information (PHI) encryption, access logs.
- **PCI-DSS**: Tokenization, secure storage of cardholder data.
- **SOC 2**: System availability, security controls, confidentiality.
- **Internal Policies**: Least-privilege roles, patch management cadences.

*Example Mapping*:
| **Framework** | **Rule Example**                          | **Technical Implementation**                          |
|----------------|-------------------------------------------|-------------------------------------------------------|
| GDPR           | "User data retention ≤ 30 days"          | Automatically purge logs older than 30 days via cron.  |
| PCI-DSS        | "Log all access to cardholder data"     | Enable AWS CloudTrail for S3 buckets storing CC numbers.|
| SOC 2          | "Multi-factor authentication enforced"   | Enforce MFA via `compliance_profile: {"mfa_required": true}`. |

#### **2.3 Integration Points**
| **Integration**       | **Use Case**                                                                 | **Implementation Notes**                                                                     |
|-----------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **CI/CD Pipelines**   | Block deployments violating compliance rules.                               | GitHub Actions: `if: steps.compliance-check.outputs.compliant == 'false'` then abort.         |
| **Infrastructure-as-Code (IaC)** | Enforce compliance in Terraform/Pulumi templates.                          | Terraform module with `compliance_validation` input: `validate_compliance()` function.        |
| **Runtime Monitoring** | Detect drift (e.g., misconfigured encryption keys).                          | Use tools like Open Policy Agent (OPA) or AWS Config Rules to scan configurations.             |
| **Identity & Access Management (IAM)** | Enforce least-privilege roles based on profiles.                          | AWS IAM Policy: `Condition: { "StringEquals": { "compliance_profile": "Production" } }`.     |
| **API Gateways**      | Validate incoming requests against rules (e.g., GDPR consent flags).          | Lambda@Edge or Kong gateway rules: `validate_gdpr_consent(header.x-gdpr-consent)`.           |

#### **2.4 Rule Syntax (YAML Example)**
```yaml
# File: compliance/rules/pci-dss.yaml
rules:
  - id: "ENCRYPTION_AT_REST"
    severity: high
    description: "All databases must use TLS or AES-256 encryption."
    targets:
      - resource_type: "database"
        frameworks: ["PCI-DSS"]
    checks:
      - type: "attribute_check"
        attribute: "encryption_method"
        required_value: "AES-256"
        tools:
          - "aws_kms_check"
          - "database_inspector"
  - id: "LOG_RETENTION"
    severity: medium
    description: "Application logs must retain data for 1 year."
    targets:
      - resource_type: "log_group"
    checks:
      - type: "time_based"
        max_age_days: 365
        tool: "log_retention_validator"
```

---
### **3. Schema Reference**
Below is the core schema for Compliance Configuration. Fields marked with `*` are required.

| **Field**               | **Type**               | **Description**                                                                                                                                                                                                 | **Example Values**                                                                 |
|-------------------------|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **compliance_profile**  | `Object*`              | Defines which rules apply to a system/environment.                                                                                                                                                           | `{ "name": "Production", "inherits": ["Dev"], "rules": ["ENCRYPTION_REQUIRED"] }` |
| **rules**               | `Array[Rule]*`         | Array of compliance rules applied to the profile.                                                                                                                                                              | See **Rule Schema** table below.                                                   |
| **status**              | `String`               | Current compliance status: `compliant`, `non-compliant`, `pending_review`.                                                                                                                                   | `"status": "non-compliant"`                                                         |
| **last_checked**        | `Datetime*`            | Timestamp of the last compliance validation run.                                                                                                                                                            | `"2023-10-01T14:30:00Z"`                                                           |
| **notifications**       | `Array[Notification]`  | Configured alerts for rule breaches.                                                                                                                                                                        | `[{ "channel": "slack", "severity": "high", "contact": "#security-team" }]`       |

---

#### **Rule Schema**
| **Field**          | **Type**         | **Description**                                                                                                                                                     | **Example**                                                                 |
|--------------------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **id**             | `String*`        | Unique identifier for the rule (e.g., `ENCRYPTION_REQUIRED`).                                                                                                     | `"id": "ENCRYPTION_REQUIRED"`                                                |
| **severity**       | `String*`        | Criticality level: `critical`, `high`, `medium`, `low`.                                                                                                         | `"severity": "high"`                                                         |
| **frameworks**     | `Array[String]`  | Applicable compliance frameworks (e.g., `["GDPR", "PCI-DSS"]`).                                                                                              | `"frameworks": ["PCI-DSS"]`                                                  |
| **targets**        | `Array[Target]`  | Resources or systems the rule applies to (e.g., databases, log groups).                                                                                            | `[{ "resource_type": "database" }]`                                         |
| **checks**         | `Array[Check]`   | Validation methods to enforce the rule (attribute checks, time-based, etc.).                                                                                  | See **Check Schema** below.                                                 |
| **remediation**    | `String`         | Steps to fix violations (optional).                                                                                                                                 | `"remediation": "Enable KMS encryption via AWS Console."`                     |

---

#### **Target Schema**
| **Field**          | **Type**         | **Description**                                                                                     | **Example**                          |
|--------------------|------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **resource_type**  | `String*`        | Type of resource (e.g., `database`, `log_group`, `api_endpoint`).                                  | `"resource_type": "database"`         |
| **tags**           | `Object`         | Optional filters (e.g., `environment: "production"`).                                              | `"tags": { "environment": "prod" }`   |

---

#### **Check Schema**
| **Field**      | **Type**         | **Description**                                                                                     | **Example**                                                                          |
|----------------|------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **type**       | `String*`        | Validation type: `attribute_check`, `time_based`, `policy_enforced`.                               | `"type": "attribute_check"`                                                       |
| **attribute**  | `String`         | Attribute to validate (e.g., `encryption_method`, `retention_days`).                                | `"attribute": "retention_days"`                                                    |
| **required_value** | `Any`      | Expected value for attribute checks.                                                               | `"required_value": "AES-256"`                                                     |
| **max_age_days**| `Integer`        | Maximum allowed age for time-based checks.                                                         | `"max_age_days": 365`                                                          |
| **tool**       | `String`         | Tool/script to perform the check (e.g., `aws_kms_check`, `log_retention_validator`).              | `"tool": "database_inspector"`                                                   |

---

### **4. Query Examples**
Use the following queries to interact with the Compliance Configuration system (assuming a REST API or CLI).

#### **4.1 List Compliance Profiles**
```bash
# CLI
compliance list-profiles --environment production

# REST (GET)
GET /api/v1/compliance/profiles?environment=production
```
**Response**:
```json
{
  "profiles": [
    {
      "name": "Production",
      "status": "non-compliant",
      "rules": ["ENCRYPTION_REQUIRED", "LOG_RETENTION"],
      "last_checked": "2023-10-01T14:30:00Z"
    },
    {
      "name": "Dev",
      "status": "compliant",
      "inherits": ["Default"]
    }
  ]
}
```

#### **4.2 Check Rule Compliance for a Resource**
```bash
# CLI
compliance validate --resource-id db-prod-1 --rule ENCRYPTION_REQUIRED

# REST (POST)
POST /api/v1/compliance/check
{
  "resource_id": "db-prod-1",
  "rule_id": "ENCRYPTION_REQUIRED"
}
```
**Response**:
```json
{
  "resource_id": "db-prod-1",
  "rule_id": "ENCRYPTION_REQUIRED",
  "compliant": false,
  "violation_details": {
    "attribute": "encryption_method",
    "expected": "AES-256",
    "actual": "AES-128",
    "tool_output": "KMS policy allows weaker encryption."
  }
}
```

#### **4.3 Apply a Compliance Profile to a System**
```bash
# CLI
compliance apply-profile --system-id app-server-001 --profile Production

# REST (PUT)
PUT /api/v1/compliance/systems/app-server-001
{
  "profile": "Production",
  "auto_remediation": true
}
```

#### **4.4 View Audit Logs for Rule Violations**
```bash
# CLI
compliance logs --rule ENCRYPTION_REQUIRED --days 7

# REST (GET)
GET /api/v1/compliance/logs?rule=ENCRYPTION_REQUIRED&days=7
```
**Response**:
```json
{
  "logs": [
    {
      "event": "FAILED_CHECK",
      "rule": "ENCRYPTION_REQUIRED",
      "resource": "db-prod-1",
      "time": "2023-10-01T10:15:00Z",
      "user": "admin@example.com",
      "status": "unresolved"
    },
    {
      "event": "PASS_CHECK",
      "rule": "ENCRYPTION_REQUIRED",
      "resource": "db-dev-001",
      "time": "2023-10-01T11:00:00Z"
    }
  ]
}
```

#### **4.5 Generate a Compliance Report (PDF/CSV)**
```bash
# CLI
compliance report --profile Production --format pdf --output report_2023-10.pdf

# REST (POST)
POST /api/v1/compliance/report
{
  "profile": "Production",
  "format": "pdf",
  "include_details": true
}
```
**Output**: Downloadable PDF/CSV with:
- Rule breakdown by compliance status.
- Violation details and remediation steps.
- Timeline of changes.

---

### **5. Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **When to Use Together**                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Infrastructure as Code (IaC)** | Deploys infrastructure with compliance rules embedded (e.g., Terraform modules).                                                                                                                   | Use **IaC** to enforce compliance during provisioning; **Compliance Configuration** validates post-deploy. |
| **Policy as Code**              | Enforces security policies (e.g., OPA Gatekeeper, AWS IAM policies) via declarative rules.                                                                                                              | Combine with **Compliance Configuration** to align framework-specific rules (e.g., PCI-DSS) with policy-as-code. |
| **Observability (Logging/Metrics)** | Monitors system state for compliance drift (e.g., Prometheus alerts for misconfigured roles).                                                                                                          | Use **Observability** to trigger **Compliance Configuration** revalidations or alert on violations.          |
| **Secret Management**           | Rotates and encrypts secrets to meet compliance (e.g., GDPR data protection).                                                                                                                        | Integrate with **Secret Management** to ensure encryption rules (from **Compliance Configuration**) are met. |
| **Least Privilege Access**      | Grants minimal permissions to roles/users based on compliance profiles.                                                                                                                                | Apply **Least Privilege** to roles defined in **Compliance Configuration** profiles (e.g., `severity: critical`). |
| **Data Masking/Tokenization**   | Protects sensitive data (e.g., PII) per compliance requirements (e.g., HIPAA).                                                                                                                      | Use **Data Masking** to implement `ENCRYPTION_REQUIRED` or `TOKENIZATION_MANDATORY` rules.                     |

---
### **6. Best Practices**
1. **Start with Minimal Viable Compliance (MVC)**:
   - Begin with critical rules (e.g., `ENCRYPTION_REQUIRED`) and expand incrementally.
   - Prioritize rules based on framework penalties (e.g., PCI-DSS fines).

2. **Automate Validations**:
   - Integrate checks into CI/CD pipelines (e.g., GitHub Actions, Jenkins).
   - Use tools like **Open Policy Agent (OPA)** or **Kyverno** for runtime enforcement.

3. **Tag Resources for Scalability**:
   - Label resources with `compliance_profile: "Production"` to apply profiles dynamically.

4. **Document Exceptions**:
   - Use `remediation` fields to note temporary overrides (e.g., `legacy_app: "PTR-1234"`).

5. **Regular Audits**:
   - Schedule quarterly compliance reviews to update rules (e.g., GDPR retention periods).

6. **Train Teams**:
   - Educate developers on rule implications (e.g., "This rule blocks deployments without TLS").

---
### **7. Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                                                                     |
|-------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------------------------|
| False positives in rule checks      |tool misconfiguration (e.g., incorrect attribute name). |Review `tool_output` and adjust the rule’s `attribute` field.                                   |
| High remediation backlog            |Too many non-compliant resources.          |Prioritize critical rules (e.g., `severity: high`) and batch fixes.                            |
| Profile inheritance conflicts       |Overrides in child profiles.               |Use `override_rules` in YAML to explicitly conflict inherited rules.                            |
| API rate-limiting                   |High query volume for compliance checks.   |Cache results (e.g., Redis) or use batch endpoints (e.g., `/api/v1/compliance/checks/batch`). |

---
### **8. Example Workflow: PCI-DSS Compliance**
1. **Define Rules**:
   Create `compliance/rules/pci-dss.yaml` with encryption, logging, and access control rules.
2. **Apply Profile**:
   Tag your database with `compliance_profile: "Production"`. The enforcement engine runs checks.
3. **Detect Violation**:
   The system logs a failure for `ENCRYPTION_REQUIRED` on `db-prod-1` (using AES-128).
4. **Remediate**:
   Update the KMS policy to AES-256 via AWS Console or CI/CD.
5. **Revalidate**:
   Re-run compliance checks; status updates to `compliant`.
6. **Audit**:
   Generate a report for the PCI-DSS quarterly review.

---
**See Also**:
- [Compliance as Infrastructure (CaI) Guide](link)
- [Open Policy Agent