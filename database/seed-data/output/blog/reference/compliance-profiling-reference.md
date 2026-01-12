# **[Pattern] Compliance Profiling Reference Guide**

---

## **Overview**
**Compliance Profiling** is a pattern used to assign, track, and validate *compliance profiles*—predefined rulesets or configurations—that ensure systems, services, or data adhere to regulatory requirements (e.g., GDPR, HIPAA, SOC 2, PCI DSS). This pattern automates compliance checks, reduces manual auditing, and provides audit trails for governance teams. It is widely applied in cloud-native environments, DevOps pipelines, and data platforms where dynamic configurations and automated validation are critical.

Key use cases include:
- Enforcing policy-as-code via IaC tools (Terraform, CloudFormation).
- Real-time validation of containerized workloads (Kubernetes) or serverless functions.
- Assessing data processing workflows for privacy/security risks.
- Integrating compliance into CI/CD pipelines to block non-compliant deployments.

---

## **Implementation Details**
### **Core Components**
1. **Compliance Profile**
   A structured set of rules, checks, or constraints defined by a regulatory standard or organizational policy. Profiles may include:
   - Mandatory fields (e.g., encryption standards).
   - Blocked configurations (e.g., disabled audit logging).
   - Thresholds (e.g., max data retention period).

2. **Profile Assignment**
   The mechanism to tag resources/services with a specific profile (e.g., `GDPR-PII`, `HIPAA-EHR`).

3. **Compliance Engine**
   A tool or service that evaluates resources against assigned profiles, generating pass/fail results and remediation steps.

4. **Audit Logs**
   Immutable records of compliance checks, including timestamps, evaluators, and evidence of violations.

5. **Remediation Actions**
   Automated or manual fixes triggered by violations (e.g., rotating encryption keys, reconfiguring IAM roles).

---

### **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                  |
|------------------------|-------------------------------------------------------------------------------|----------------------------------------------|
| **Rule**               | A single atomic check (e.g., "Ensure TLS 1.2+ is enforced").                  | *"Verify `allow_insecure_transport` = false."*|
| **Profile Version**    | A snapshot of a profile (e.g., GDPR v2023-05).                               | `GDPR-2.3-20230501`                          |
| **Compliance Status**  | Result of a profile evaluation ("Pass"/"Fail"/"Warn").                        | `ComplianceStatus: "Fail" (Rule ID: 42)`      |
| **Evidence**           | Data used to validate a rule (e.g., logs, configurations, metadata).         | S3 bucket access logs showing no public reads.|
| **Baseline**           | Default profile for a resource type (e.g., "cloud-compute-minimal").        | AWS EC2 instance with default security groups.|

---

## **Schema Reference**
Below is a schema for a normalized compliance profiling system (JSON/YAML format). Adjust fields to match your tooling (e.g., Azure Policy, AWS Config, Open Policy Agent).

### **1. Compliance Profile Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ComplianceProfile",
  "type": "object",
  "properties": {
    "profileId": { "type": "string", "format": "uuid" },
    "name": { "type": "string" },                     // e.g., "GDPR-PII"
    "version": { "type": "string" },                  // e.g., "2.3"
    "description": { "type": "string" },
    "scope": {                                        // Target resource types
      "type": "array",
      "items": { "type": "string" },
      "examples": ["k8s-namespace", "aws-s3-bucket"]
    },
    "rules": {                                        // Array of rule definitions
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ruleId": { "type": "string" },
          "severity": { "enum": ["Low", "Medium", "High", "Critical"] },
          "check": {                                   // Definition of the check
            "type": "object",
            "properties": {
              "expression": { "type": "string" },      // OPA-like logic
              "resourceType": { "type": "string" },
              "requiredField": { "type": "string" },
              "validationRegex": { "type": "string" }
            }
          },
          "remediation": {                             // Fix instructions
            "type": "object",
            "properties": {
              "actions": { "type": "array", "items": { "type": "string" } },
              "automated": { "type": "boolean" }
            }
          }
        }
      }
    },
    "excludedResources": {                            // Opt-out patterns
      "type": "array",
      "items": { "type": "string" }
    },
    "createdAt": { "type": "string", "format": "date-time" },
    "updatedAt": { "type": "string", "format": "date-time" }
  },
  "required": ["profileId", "name", "rules"]
}
```

### **2. Resource Assignment Schema**
```json
{
  "resourceId": { "type": "string" },                // Unique identifier (e.g., ARN)
  "profileId": { "type": "string" },                 // Reference to `ComplianceProfile`
  "assignmentReason": { "type": "string" },          // Why this resource is assigned
  "effectiveFrom": { "type": "string", "format": "date-time" },
  "tags": {                                          // Metadata
    "type": "object",
    "additionalProperties": { "type": "string" }
  }
}
```

### **3. Compliance Evaluation Result**
```json
{
  "evaluationId": { "type": "string", "format": "uuid" },
  "resourceId": { "type": "string" },
  "profileId": { "type": "string" },
  "status": { "enum": ["Pass", "Fail", "Warn", "Pending"] },
  "timestamp": { "type": "string", "format": "date-time" },
  "results": {                                      // Rule-by-rule outcomes
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "ruleId": { "type": "string" },
        "status": { "enum": ["Pass", "Fail", "Warn"] },
        "evidence": { "type": "object" },             // Raw data used for validation
        "remediation": {                              // Action taken/required
          "type": "object",
          "properties": {
            "status": { "enum": ["Completed", "Pending", "Failed"] },
            "notes": { "type": "string" }
          }
        }
      }
    }
  }
}
```

---

## **Query Examples**
Use these queries to interact with a compliance profiling system (pseudocode for common operations).

### **1. List All Resources Assigned to a Profile**
```sql
SELECT resourceId, assignmentReason
FROM resource_profiles
WHERE profileId = 'uuid-of-gdpr-profile'
ORDER BY effectiveFrom DESC;
```

### **2. Evaluate a Resource Against Its Profile**
```python
# Pseudocode for a compliance engine
def evaluate_resource(resource_id, profile):
    results = []
    for rule in profile["rules"]:
        evidence = fetch_evidence(resource_id, rule)
        if not rule["check"].validate(evidence):
            results.append({
                "ruleId": rule["ruleId"],
                "status": "Fail",
                "evidence": evidence
            })
    return {"status": "Pass" if not results else "Fail", "results": results}
```

### **3. Generate a Compliance Report (JSON)**
```json
{
  "reportId": "uuid",
  "timestamp": "2023-10-15T12:00:00Z",
  "summary": {
    "totalResources": 42,
    "compliant": 35,
    "nonCompliant": 7,
    "warnings": 0
  },
  "details": [
    {
      "resourceId": "arn:aws:s3:::sensitive-bucket",
      "profileId": "GDPR-PII",
      "status": "Fail",
      "violations": [
        {
          "ruleId": "encryption-enabled",
          "evidence": { "serverSideEncryption": "None" }
        }
      ]
    }
  ]
}
```

### **4. CI/CD Pipeline Integration (GitHub Actions)**
```yaml
- name: Check compliance before deployment
  uses: compliance-engine/action@v1
  with:
    resource-id: ${{ env.K8S_NAMESPACE }}
    profile-id: "GDPR-2.3"
    token: ${{ secrets.ADMIN_TOKEN }}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Policy as Code**        | Define infrastructure/policy rules as code (e.g., Terraform, OPA).                                | When compliance must be version-controlled and reproducible.                                       |
| **Immutable Infrastructure** | Treat infrastructure as ephemeral; rebuild from trusted templates.                             | Critical environments where drift must be minimized.                                               |
| **Audit Logging**         | Centralized collection of user/actions for forensic analysis.                                    | Required by PCI DSS (Article 10) or HIPAA (Audit Controls).                                       |
| **Secret Management**     | Secure handling of credentials/keys (e.g., HashiCorp Vault, AWS Secrets Manager).             | Protecting PII or financial data (GDPR Article 32, SOC 2).                                         |
| **Data Classification**   | Tagging data based on sensitivity (e.g., "Highly Sensitive").                                   | GDPR’s principle of data minimization and right to erasure.                                       |
| **Chaos Engineering**     | Test system resilience to failures (e.g., netflixchaos).                                         | Validate compliance during outages (e.g., HIPAA’s "Backup Plan" requirement).                     |

---

## **Tools & Frameworks**
| **Tool**               | **Purpose**                                                                                     | **Links**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Open Policy Agent (OPA)**       | Flexible policy engine for Kubernetes, cloud, and APIs.                                      | [opensource.googlesource.com](https://github.com/open-policy-agent/opa)                     |
| **AWS Config**         | Record and evaluate resource compliance against rules.                                        | [aws.amazon.com/config](https://aws.amazon.com/config/)                                      |
| **Azure Policy**       | Enforce organizational standards in Azure.                                                     | [azure.microsoft.com/policy](https://azure.microsoft.com/en-us/services/governance/policy/) |
| **Terraform + Sentinel** | Integrate compliance checks into IaC workflows.                                               | [hashicorp.com/sentinel](https://www.hashicorp.com/products/sentinel)                         |
| **Kyverno**           | Kubernetes-native policy engine.                                                              | [kyverno.io](https://kyverno.io/)                                                             |
| **Compass (Databricks)** | Data governance and compliance for cloud data lakes.                                          | [databricks.com/compass](https://databricks.com/product/compass)                               |

---
**Note:** For cloud providers, leverage **built-in compliance tools** (e.g., AWS Config Rules, Azure Security Benchmark) to reduce custom implementation overhead.