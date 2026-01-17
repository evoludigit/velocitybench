**[Pattern] Security Conventions Reference Guide**

---

### **1. Overview**
The **Security Conventions** pattern defines standardized naming, configuration, and placement rules for security-related resources (e.g., policies, keys, roles) to ensure consistency, enforce least privilege, and simplify compliance audits. This pattern applies to cloud-native architectures, DevOps pipelines, and infrastructure-as-code (IaC) deployments (e.g., Terraform, CloudFormation, Helm).

Key principles:
- **Explicit naming**: Security resources must use clear, context-aware labels (e.g., `prod-api-db-readonly-role`).
- **Hierarchical organization**: Group resources by environment (dev/stage/prod) and scope (e.g., `security/iam/policies`).
- **Immutable defaults**: Avoid hardcoded secrets; use dynamic providers (e.g., AWS Secrets Manager, HashiCorp Vault).
- **Audit trails**: Log access patterns (via CloudTrail, OpenTelemetry) and enforce periodic reviews (via Config conformance checks).

Adopting this pattern reduces misconfigurations (e.g., over-permissive IAM roles) and streamlines compliance validation (e.g., PCI DSS, SOC 2).

---

### **2. Schema Reference**
| **Component**               | **Requirement**                                                                 | **Example**                                                                 | **Validation Rules**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Resource Naming**         | Follow `[scope]-<type>-<purpose>-[env]` format.                               | `security/iam/leastprivilege-db-role-prod`                                  | Regex: `^[a-z-]+/(?:[a-z-]+/-){1,2}[a-z-]+$`                                        |
| **Environment Separation**  | Isolate dev/stage/prod resources in distinct directories.                      | `/security/dev/` vs. `/security/prod/`                                        | Terraform: `var.env` tag; CloudFormation: `!Ref Environment`                      |
| **IAM Roles/Policies**      | Use *least privilege* and tag with `cost-center` and `owner`.                | `{ "Name": "data-analytics-read", "Tags": { "cost-center": "FIN-123" } }` | AWS IAM: Policy simulator; Check `aws:ResourceTag/owner` in SCP policies.           |
| **Secrets Management**      | Store secrets in secrets vaults (not plaintext in IaC).                        | `{{vault://prod/db/creds}}` (Terraform)                                    | Enforce via OPA/Gatekeeper: `data.kubernetes.secret.data["password"] == null`      |
| **Logging & Monitoring**    | Enable audit logging and set alerts for anomalous access (e.g., `UnusualLogin`).| CloudWatch Alarm: `FilterPattern: "EventName: AssumeRole"`                  | Retention: 90+ days; Parse with Fluentd.                                              |
| **Policy-as-Code**          | Encode security constraints in IaC (e.g., OPA policies, Terraform modules).  | ```hcl # Terraform module: require "aws_kms_key_policy" { condition { ... } }``` | Lint with `tfsec` or `checkov`.                                                      |
| **Network Isolation**       | Use private subnets for security resources; restrict ingress/egress.            | VPC: `security-group-rule=allow_icmp_from_vpn_only`                          | AWS: `aws ec2 describe-security-group-rules`.                                       |
| **Compliance Tags**         | Tag resources with compliance metadata (e.g., `compliance: pci-dss`).          | `aws:ResourceTag/compliance: "pci-dss"`                                       | AWS Config: `compliance_resource_compliance` rule.                                   |

---
### **3. Implementation Details**

#### **3.1 Naming Conventions**
- **Scope**: Module path (e.g., `security/iam`).
- **Type**: Resource type (`role`, `policy`, `key`).
- **Purpose**: Function (e.g., `db-readonly`, `s3-logs`).
- **Environment**: `dev`, `stage`, or `prod`.

**Do**:
```plaintext
security/iam/leastprivilege-s3-role-dev
security/kms/aws-key-prod
```

**Don’t**:
```plaintext
iam/admin-role  # Vague; lacks environment.
security/key-master  # Incomplete scope.
```

#### **3.2 IAM Least Privilege**
- **Principle**: Grant minimal permissions via explicit policies.
- **Tools**:
  - **AWS IAM Access Analyzer**: Detect unused permissions.
  - **Terraform**: Use `aws_iam_policy_document` + `aws_iam_role_policy_attachment`.
- **Example Policy**:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject"],
        "Resource": "arn:aws:s3:::my-bucket/*"
      }
    ]
  }
  ```

#### **3.3 Secrets Management**
| **Provider**       | **Implementation**                                                                 | **Example**                                                                 |
|--------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **AWS Secrets Manager** | Reference via `data.aws_secretsmanager_secret_version`.                        | ```hcl data "aws_secretsmanager_secret_version" "db_creds" { name = "prod/db" } ``` |
| **HashiCorp Vault**   | Use `vault` provider in Terraform.                                                | ```hcl provider "vault" { token = var.vault_token } ```                    |
| **Kubernetes**         | Encrypt secrets with `kubeseal` or `sealed-secrets`.                            | ```yaml apiVersion: bitnami.com/v1alpha1 kind: SealedSecret ```            |

#### **3.4 Audit Logging**
- **AWS**: Enable [CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html) for all API calls.
- **GCP**: Use [Audit Logs](https://cloud.google.com/logging/docs/audit) with `Data Access` scope.
- **Query Example (AWS Athena)**:
  ```sql
  SELECT *
  FROM cloudtrail_*
  WHERE eventName = 'AssumeRole'
    AND eventTime > timestampadd(day, -7, current_timestamp())
    AND awsRegion = 'us-east-1'
  ```

#### **3.5 Compliance Validation**
- **AWS Config Rules**: Create rules like `aws-config-rule-compliance-resources`.
- **Terraform**: Use [`terraform-compliance`](https://github.com/palantir/terraform-compliance):
  ```yaml # config.yaml rules: - name: "aws-secret-no-plaintext" regex: '{{.*?}}' ```

---

### **4. Query Examples**
#### **4.1 Find Over-Permissive IAM Roles (AWS CLI)**
```bash
aws iam list-roles --query 'Roles[?PolicySummaries[?Effect==`Allow` && !contains(Statement, `Resource`)].Statement]'
```

#### **4.2 Terraform Validation for Missing Tags**
```hcl
resource "aws_s3_bucket" "example" {
  tags = {
    cost-center = "FIN-123"
    owner       = "security-team"
  }
}

# Validate with `terraform validate` or `tfsec`
```

#### **4.3 Kubernetes RBAC Least Privilege Check**
```yaml
# Check if role has excessive permissions.
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]  # Allow only read operations.
```

---

### **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Dependency**                          |
|---------------------------------|-------------------------------------------------------------------------------|----------------------------------------|
| **Infrastructure as Code**     | Enforce security conventions via IaC templates (Terraform, CloudFormation).     | [Terraform Best Practices](link)        |
| **Secrets Management**          | Centralized storage and rotation of secrets (Vault, AWS Secrets Manager).      | [Secret Rotation Pattern](link)         |
| **Zero Trust Architecture**    | Enforce least privilege and micro-segmentation.                                | [Micro-Segmentation](link)              |
| **Policy-as-Code**              | Encode security policies in declarative formats (OPA, Terraform).            | [Open Policy Agent](link)               |
| **Compliance Automation**       | Automate compliance checks (AWS Config, OpenTOOLKit).                          | [Compliance Scanning](link)             |

---
### **6. Anti-Patterns**
- **Hardcoded Secrets**: Avoid embedding credentials in scripts or IaC.
- **Wildcard Permissions**: Never use `"Resource": "*"` in IAM policies.
- **Ignored Audit Logs**: Failing to monitor for suspicious activities (e.g., `AssumeRole` spikes).
- **Unversioned Roles**: Ensure IAM roles are versioned and documented.

---
### **7. Tools & Libraries**
| **Tool**               | **Use Case**                                                                 | **Link**                                  |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **Terraform**          | Enforce naming conventions and least privilege.                            | [Terraform Docs](https://www.terraform.io)|
| **AWS IAM Access Analyzer** | Detect unused permissions.                                                 | [AWS Docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer.html) |
| **OPA/Gatekeeper**      | Validate Kubernetes manifests against policies.                            | [Open Policy Agent](https://www.openpolicyagent.org/) |
| **Checkov**            | Scan IaC for security misconfigurations.                                    | [Checkov GitHub](https://github.com/bridgecrewio/checkov) |
| **AWS Config**         | Continuously assess compliance.                                            | [AWS Config](https://aws.amazon.com/config/) |

---
### **8. Further Reading**
- [AWS Well-Architected Security Pillar](https://aws.amazon.com/architecture/well-architected/)
- [CIS Benchmarks for Cloud](https://www.cisecurity.org/benchmarks/)
- [OWASP Cloud Security Top 10](https://owasp.org/www-project-cloud-security-top-10/)

---
**Last Updated**: `YYYY-MM-DD`
**Version**: `1.2`