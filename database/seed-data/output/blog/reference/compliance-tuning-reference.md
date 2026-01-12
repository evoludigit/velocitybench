**[Pattern] Compliance Tuning Reference Guide**

---

### **Overview**
The **Compliance Tuning** pattern ensures that **security, governance, and operational policies** are dynamically enforced across cloud, on-premises, or hybrid environments. This pattern automates compliance checks, adjusts configurations in real-time, and mitigates risks by aligning infrastructure with **regulatory standards** (e.g., HIPAA, GDPR, PCI DSS) and **internal policies**.

Use cases include:
✔ **Regulatory compliance** (e.g., audit readiness, data residency enforcement).
✔ **Policy-as-code** (automating remediation for misconfigurations).
✔ **Continuous security posture management** (detecting drift from compliance baselines).
✔ **Hybrid/multi-cloud compliance** (standardizing enforcements across environments).

---

### **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Compliance Baseline** | A predefined set of **CIS Benchmarks, NIST guidelines, or custom policy rules**. | AWS CIS Benchmarks for Security Best Practices (v1.2.0).                     |
| **Compliance Check**    | A **scan or evaluation** against baselines (e.g., using OpenSCAP, CISLabs tools). | Checking if IAM roles lack MFA (AWS Config Rule).                           |
| **Remediation Action**  | **Automated or manual fixes** triggered by compliance failures (e.g., tagging, access revocation). | AWS Lambda deleting S3 buckets without encryption via **AWS Config Remediation**. |
| **Policy Drift**        | Deviation from compliance baselines over time (e.g., outdated resource tags). | A VPN gateway left unpatched 60 days past maintenance window.              |
| **Compliance Dashboard**| **Centralized monitoring** of compliance status (e.g., via AWS Compliance Hub). | Grafana dashboard showing PCI DSS compliance score per region.            |

---

### **Implementation Details**

#### **1. Compliance Baseline Definition**
Define compliance rules using:
- **Standard frameworks** (CIS, NIST, ISO 27001).
- **Custom policies** (e.g., internal security rules).
- **Third-party tools** (Open Policy Agent [OPA], Terraform policies).

**Example (AWS Config Custom Rule in YAML):**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  EnforceEncryptionRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: s3-bucket-encryption-enabled
      Description: "Ensure S3 buckets use SSE."
      InputParameters:
        BucketName: "my-bucket"
      Source:
        Owner: AWS
        SourceIdentifier: S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED
```

#### **2. Compliance Tuning Workflow**
1. **Define Baselines** – Map to frameworks (e.g., CIS AWS Foundations).
2. **Continuous Monitoring** – Use tools like:
   - **AWS Config** (for AWS resources).
   - **Azure Policy** (for Azure).
   - **Terraform + Sentinel** (multi-cloud).
3. **Automate Remediation** – Trigger fixes via:
   - **Lambda functions** (AWS).
   - **Policy Execution** (Azure).
   - **Open Policy Agent (OPA)** for cross-platform.
4. **Report & Remediate** – Generate reports (e.g., AWS Compliance Reports) and alert stakeholders.

#### **3. Tools & Integrations**
| **Tool**               | **Purpose**                                                                 | **Key Features**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **AWS Config**          | Track compliance of AWS resources.                                          | Supports CIS benchmarks, custom rules, and remediation via AWS Systems Manager. |
| **Azure Policy**        | Enforce compliance in Azure (e.g., disable public endpoints).               | Built-in policies for security, cost, and governance.                          |
| **OpenSCAP**            | SCAP-compliant vulnerability scanning (DISA STIGs).                         | Integrates with Red Hat, OVAL, and XCCDF standards.                             |
| **Terraform + Sentinel**| Policy-as-code for multi-cloud.                                             | Enforce compliance during IaC deployment.                                       |
| **Prisma Cloud / CloudCheckr** | Third-party compliance-as-code platforms.                              | Centralized compliance tracking across clouds.                                  |

---

### **Schema Reference**
Below is a **normalized schema** for compliance tuning configurations.

#### **1. Compliance Baseline Schema**
```json
{
  "baseline": {
    "name": "string",                     // e.g., "CIS_AWS_Foundations_v1.2.0"
    "framework": "enum",                  // "CIS", "NIST", "ISO27001", "CUSTOM"
    "version": "string",                  // e.g., "v1.2.0"
    "rules": [
      {
        "id": "string",                   // e.g., "S3.1.1"
        "description": "string",
        "severity": "enum",               // "CRITICAL", "HIGH", "MEDIUM", "LOW"
        "resourceTypes": ["string"],      // ["S3Bucket", "EC2Instance"]
        "check": "string",                // Query (e.g., "!s3.encryption.disabled")
        "remediation": {
          "action": "enum",               // "AUTO_FIX", "ALERT_ONLY", "MANUAL"
          "script": "string"              // Lambda/Azure Function URL
        }
      }
    ]
  }
}
```

#### **2. Compliance Check Output Schema**
```json
{
  "checkId": "string",              // e.g., "S3.1.1"
  "resource": {                     // Affected resource
    "arn": "string",
    "type": "string",
    "region": "string"
  },
  "status": "enum",                 // "NON_COMPLIANT", "COMPLIANT", "PENDING"
  "complianceTime": "datetime",
  "remediationStatus": "string"    // "SUCCESS", "FAILED", "PENDING"
}
```

---

### **Query Examples**

#### **1. Query Non-Compliant S3 Buckets (AWS Config CLI)**
```bash
aws configservice describe-compliance-by-resource \
  --resource-type 'AWS::S3::Bucket' \
  --compliance-resource-type 'AWS::Config::ResourceComplianceByConfigRule' \
  --filter '{"ComplianceResourceType": {"Values": ["AWS::Config::ConfigRule"]}, "ComplianceResourceId": {"Values": ["s3-bucket-server-side-encryption-enabled"]}}'
```

#### **2. Terraform Policy Check (Sentinel)**
```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-remote-state"
    key    = "network/terraform.tfstate"
  }
}

module "compliance_check" {
  source = "github.com/example/compliance-checker"
  rules = [
    {
      name    = "vpc_no_public_access"
      check   = "!aws_vpc.vpc.public_access_cidrs"
      action  = "Block"
    }
  ]
}
```

#### **3. Open Policy Agent (OPA) Policy**
```rego
package aws_s3_encryption

default allow = false

# Require SSE for all S3 buckets
aws_s3_bucket_encryption[bucket] {
  input.resource.type == "s3Bucket"
  input.resource.encryption == "disabled"
  allow := false
}
```

#### **4. Azure Policy Rule (JSON)**
```json
{
  "mode": "All",
  "policyRule": {
    "if": {
      "allOf": [
        {
          "field": "type",
          "equals": "Microsoft.Network/networkSecurityGroups"
        },
        {
          "field": "properties.securityRules[].access",
          "equals": "Allow"
        },
        {
          "field": "properties.securityRules[].destinationAddressPrefix",
          "equals": "*"
        }
      ]
    },
    "then": {
      "effect": "Deny"
    }
  }
}
```

---

### **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Infrastructure as Code (IaC)]** | Manage compliance via version-controlled templates (Terraform, CloudFormation). | Deploying compliant infrastructure from scratch.                              |
| **[Security Automation Framework]** | Integrate compliance checks into CI/CD pipelines (e.g., GitHub Actions).     | Automating compliance in DevOps workflows.                                     |
| **[Event-Driven Remediation]** | Use **AWS EventBridge** or **Azure Event Grid** to trigger fixes on violations. | Responding to compliance failures in real-time.                              |
| **[Data Residency Enforcement]** | Restrict data location via **AWS KMS** or **Azure Storage Geo-Redundancy**.   | Meeting GDPR or regional compliance laws.                                      |
| **[Secret Rotation]**      | Automate credential rotation (e.g., **AWS Secrets Manager + Lambda**).      | Maintaining compliance for secrets management.                                |

---

### **Best Practices**
1. **Start Small** – Pilot with a single compliance baseline (e.g., CIS AWS Foundations).
2. **Automate Remediation** – Use **AWS Systems Manager** or **Azure Policy remediation tasks**.
3. **Monitor Drift** – Schedule **weekly compliance scans** to detect drift.
4. **Document Policies** – Maintain a **compliance playbook** with remediation steps.
5. **Test in Staging** – Validate remediation scripts in a **non-production environment**.

---
**Example Compliance Playbook Entry:**
| **Violation**               | **Remediation Step**                          | **Owner**       | **SLA**       |
|------------------------------|-----------------------------------------------|-----------------|---------------|
| S3 bucket without encryption | Apply SSE-S3 via AWS CLI/Lambda.             | Cloud Team      | 24h           |
| EC2 instance missing patches | Run AWS SSM patch compliance run.            | DevOps          | 48h           |

---
**Further Reading:**
- [AWS Compliance Resources](https://aws.amazon.com/compliance/)
- [OpenSCAP Documentation](https://www.open-scap.org/)
- [Terraform Sentinel Policies](https://www.terraform.io/docs/enterprise/sentinel/policies.html)