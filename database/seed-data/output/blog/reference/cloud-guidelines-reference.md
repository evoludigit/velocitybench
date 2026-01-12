# **[Pattern] Cloud Guidelines Reference Guide**
*Design, enforce, and maintain consistent cloud best practices for scalable, secure, and cost-effective deployments.*

---

## **Overview**
Cloud Guidelines define a standardized set of rules, policies, and best practices to ensure consistency, security, reliability, and cost efficiency across cloud deployments. This pattern helps organizations:
- **Reduce operational overhead** by centralizing cloud operations (e.g., infrastructure as code, automated compliance checks).
- **Enhance security** by enforcing least-privilege access, encryption, and network segmentation.
- **Optimize costs** via tagging, right-sizing, and idle resource cleanup.
- **Improve auditability** through logging, monitoring, and governance tracking.

Cloud Guidelines are typically implemented via:
- **Infrastructure-as-Code (IaC)** (e.g., Terraform, AWS CDK, Terragrunt).
- **Policy-as-Code** (e.g., Open Policy Agent, AWS Config Rules).
- **Cloud Provider Services** (e.g., AWS Organizations SCPs, Azure Policy, GCP Recommender).
- **CI/CD Pipelines** (e.g., GitHub Actions, GitLab CI) to enforce checks before deployment.

This guide covers the core components, schema references, query examples, and related patterns for implementing Cloud Guidelines.

---

## **Schema Reference**
Below is a structured schema for defining and managing Cloud Guidelines. Use this as a template in policy-as-code tools or documentation repositories.

| **Category**          | **Field**                     | **Description**                                                                                                                                                                                                 | **Example Values**                                                                                     | **Data Type**       | **Required** |
|-----------------------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|--------------------|--------------|
| **Metadata**          | `guideline_id`                | Unique identifier for the guideline (e.g., `sg-001`).                                                                                                                                                     | `sg-001`                                                                                             | String              | Yes          |
|                       | `name`                        | Human-readable name (e.g., "Resource Tagging Standard").                                                                                                                                               | `Resource Tagging Standard`                                                                          | String              | Yes          |
|                       | `version`                     | Version of the guideline (e.g., `v1.2`).                                                                                                                                                             | `v1.2`                                                                                               | String              | Yes          |
|                       | `owner`                       | Team/role responsible (e.g., "Cloud Security Team").                                                                                                                                                   | `Cloud Security Team`                                                                            | String              | Yes          |
|                       | `last_updated`                | Timestamp of the last update (ISO 8601).                                                                                                                                                               | `2023-10-15T09:30:00Z`                                                                              | DateTime            | No           |
|                       | `status`                      | Current state (`draft`, `active`, `deprecated`).                                                                                                                                                      | `active`                                                                                             | Enum               | Yes          |
| **Scope**             | `applies_to`                  | Cloud providers/targets (e.g., `["aws", "gcp"]`).                                                                                                                                                       | `["aws"]`                                                                                             | Array[String]      | Yes          |
|                       | `resource_types`              | Types of resources affected (e.g., `["ec2", "s3", "iam"]`).                                                                                                                                                | `["ec2", "s3"]`                                                                                      | Array[String]      | Yes          |
|                       | `regions`                     | Geographic regions (e.g., `["us-east-1", "eu-west-2"]`).                                                                                                                                             | `["us-east-1"]`                                                                                      | Array[String]      | No           |
| **Rules**             | `requirements`                | Mandatory compliance criteria (e.g., "Enable multi-factor authentication (MFA) on all IAM users").                                                                | `"MFA must be enabled for all IAM users within 30 days of creation."`                            | String/JSON        | Yes          |
|                       | `recommendations`             | Best practices (non-mandatory) (e.g., "Use spot instances for non-critical workloads").                                                                                                                   | `"Consider spot instances for fault-tolerant applications."`                                          | String/JSON        | No           |
|                       | `exceptions`                  | Approved deviations (e.g., `"temporary storage bucket: s3://dev-backups"`).                                                                                                                              | `[{"bucket": "s3://dev-backups", "reason": "CI/CD pipeline artifacts", "expiry": "2024-01-01"}]` | Array[Object]      | No           |
| **Enforcement**       | `enforcement_level`           | Severity (`warning`, `blocking`, `monitoring`).                                                                                                                                                 | `blocking`                                                                                           | Enum               | Yes          |
|                       | `tool`                        | Automation tool (e.g., `aws-config`, `terrform-validate`, `gcp-recommender`).                                                                                                                            | `aws-config`                                                                                         | String              | Yes          |
|                       | `ci_cd_stage`                 | Pipeline stage to enforce (e.g., `validate`, `deploy`, `compliance`).                                                                                                                                   | `validate`                                                                                            | String              | Yes          |
| **Documentation**     | `links`                       | References (e.g., AWS docs, RFC).                                                                                                                                                                    | `[{ "url": "https://aws.amazon.com/well-architected/", "type": "framework" }]`                       | Array[Object]      | No           |
|                       | `notes`                       | Additional context.                                                                                                                                                                                     | `"Exceptions require approval via #cloud-guidelines channel."`                                      | String              | No           |

---

### **Example Schema (JSON)**
```json
{
  "guideline_id": "sg-001",
  "name": "Resource Tagging Standard",
  "version": "v1.2",
  "owner": "Cloud Governance Team",
  "status": "active",
  "last_updated": "2023-10-15T09:30:00Z",
  "applies_to": ["aws", "gcp"],
  "resource_types": ["ec2", "s3", "gke"],
  "requirements": {
    "mandatory_tags": ["Environment", "Owner", "CostCenter"],
    "compliance_check": "All EC2/S3/GKE resources must include `Environment: production` or `Environment: staging`."
  },
  "recommendations": [
    "Use AWS Tag Editor for bulk tagging.",
    "Automate tagging via Terraform or CloudFormation."
  ],
  "exceptions": [
    {
      "description": "Dev/test resources",
      "pattern": "tag:Environment=dev-*",
      "expiry": "2024-06-30"
    }
  ],
  "enforcement_level": "blocking",
  "tool": "aws-config",
  "ci_cd_stage": "validate",
  "links": [
    {
      "url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/tagging-resources.html",
      "type": "aws"
    }
  ],
  "notes": "Exceptions require approval via #cloud-guidelines Slack channel."
}
```

---

## **Query Examples**
Use these queries to filter, validate, or generate Cloud Guidelines in tools like:
- **Terraform** (for IaC validation).
- **Open Policy Agent (OPA)** (for policy-as-code).
- **AWS CLI/GCP CLI** (for compliance checks).
- **Databases** (e.g., PostgreSQL, DynamoDB) to store guideline metadata.

---

### **1. Filter Active AWS-Specific Guidelines**
**Tool:** Terraform + OPA (Rego)
```rego
package main

default allow = false

# Check if guideline is active and applies to AWS
guideline.active = true
guideline.applies_to = ["aws"]

allow {
    input.guideline = guideline
    input.resource_type in guideline.resource_types
}
```
**Input (Terraform variable):**
```hcl
variable "cloud_guidelines" {
  type = list(object({
    id       = string
    active   = bool
    applies_to = list(string)
    resource_types = list(string)
  }))
}
```

---

### **2. AWS CLI: List Non-Compliant Resources**
**Command:**
```bash
aws configservice list-compliance-by-config-rule --config-rule-name sg-001-tagging-compliance
```
**Output Filter:**
```bash
jq '.complianceResources[] | select(.complianceResourceType=="AWS::EC2::Instance")'
```
**Expected Result:**
```json
[
  {
    "complianceResourceId": "i-1234567890abcdef0",
    "complianceResourceType": "AWS::EC2::Instance",
    "complianceResourceName": "non-compliant-instance",
    "complianceType": "non-compliant"
  }
]
```

---

### **3. GCP Recommender: Enforce Guidelines via API**
**Endpoint:**
```bash
gcloud alpha recomender policies list
```
**Filter for "sg-001":**
```bash
gcloud alpha recomender policies list --filter="title:sg-001" --format="value(title,description)"
```
**Expected Output:**
```
Title: Resource Tagging Standard
Description: All resources must include mandatory tags: Environment, Owner, CostCenter.
```

---

### **4. SQL Query (PostgreSQL): Find Deprecated Guidelines**
```sql
SELECT *
FROM cloud_guidelines
WHERE status = 'deprecated'
AND last_updated < CURRENT_DATE - INTERVAL '90 days';
```
**Example Result:**
| guideline_id | name                     | status      |
|--------------|--------------------------|-------------|
| sg-003       | Legacy VPC Design        | deprecated  |

---

### **5. Terraform Validation (Locals Block)**
```hcl
locals {
  invalid_guidelines = [
    for guideline in var.cloud_guidelines :
    guideline if contains(guideline.resource_types, "unmanaged-resource") && guideline.enforcement_level == "blocking"
  ]
}

variable "cloud_guidelines" {
  description = "List of cloud guidelines to validate."
  type = list(object({
    resource_types = list(string)
    enforcement_level = string
  }))
}

# Error if blocking guideline targets unmanaged resource
variable "blocked_guidelines" {
  validation {
    condition     = length(local.invalid_guidelines) == 0
    error_message = "Blocked guideline ${local.invalid_guidelines[0].name} targets unmanaged resource ${local.invalid_guidelines[0].resource_types[0]}."
  }
}
```

---

## **Related Patterns**
To complement **Cloud Guidelines**, consider integrating the following patterns:

| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Infrastructure as Code (IaC)](https:// patterns.cloud/iac)** | Define and version cloud resources declaratively (e.g., Terraform, AWS CDK).                                                                                                                               | When you need reproducible, auditable deployments.                                                   |
| **[Policy-as-Code](https:// patterns.cloud/policy-as-code)** | Enforce rules via code (e.g., OPA, AWS Config Rules).                                                                                                                                                     | When you require automated compliance checks in CI/CD.                                               |
| **[Cost Optimization](https:// patterns.cloud/cost-optimization)** | Right-size resources, use spot instances, and monitor costs.                                                                                                                                               | When reducing cloud spend is a priority.                                                             |
| **[Zero Trust Security](https:// patterns.cloud/zero-trust)** | Assume breach; enforce least privilege, MFA, and network segmentation.                                                                                                                                    | When security is a top concern (e.g., regulated industries).                                      |
| **[Chaos Engineering](https:// patterns.cloud/chaos)**       | Proactively test resilience by injecting failures.                                                                                                                                                       | When high availability is critical (e.g., SaaS platforms).                                          |
| **[Multi-Cloud Orchestration](https:// patterns.cloud/multi-cloud)** | Manage resources across providers with unified tools (e.g., Pulumi, Crossplane).                                                                                                                      | When using multiple cloud providers (e.g., AWS + Azure).                                            |
| **[Observability Stack](https:// patterns.cloud/observability)** | Centralize logs, metrics, and traces (e.g., Prometheus + Grafana + AWS CloudWatch).                                                                                                                    | When debugging performance or security issues.                                                      |
| **[GitOps](https:// patterns.cloud/gitops)**                | Sync infrastructure state with Git repositories (e.g., ArgoCD, Flux).                                                                                                                                     | When teams collaborate on infrastructure changes.                                                   |

---

## **Best Practices**
1. **Start Small**: Begin with 3–5 high-impact guidelines (e.g., tagging, MFA, encryption).
2. **Automate Enforcement**: Use CI/CD pipelines to block non-compliant deployments.
3. **Monitor Compliance**: Set up dashboards (e.g., AWS Health Dashboard, GCP Operations) to track adherence.
4. **Communicate Changes**: Update teams via runbooks, Slack alerts, or email digests.
5. **Review Quarterly**: Audit guidelines for relevance (e.g., deprecate outdated rules).
6. **Leverage Provider Tools**:
   - AWS: **Service Control Policies (SCPs)**, **AWS Config**.
   - GCP: **Policy Intelligencer**, **Recommender**.
   - Azure: **Azure Policy**, **Blueprints**.
7. **Exception Process**: Document how to request deviations (e.g., Jira tickets, approval workflows).

---
## **Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                                                                                                                                                 |
|-------------------------------------|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Guideline not enforced in CI/CD** | Tool misconfiguration (e.g., wrong policy path). | Verify policy-as-code tool logs (e.g., OPA `opa eval`).                                                                                                                                                   |
| **False positives in compliance checks** | Overly strict requirements. | Review `exceptions` field or adjust thresholds (e.g., "warn" instead of "block").                                                                                                                     |
| **High enforcement overhead**       | Too many guidelines blocking deployments. | Prioritize critical rules; phase in non-blocking recommendations.                                                                                                                                     |
| **Team resistance to guidelines**   | Lack of visibility or transparency.    | Publish a public FAQ in a shared doc (e.g., Notion, Confluence) with rationale for each rule.                                                                                                       |
| **Guidelines outdated**             | No versioning or review process.       | Use semantic versioning (`v1.0`, `v1.1`) and schedule quarterly reviews.                                                                                                                                   |

---
## **Further Reading**
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [GCP Recommender Documentation](https://cloud.google.com/recommender)
- [Terraform Modules for Cloud Governance](https://registry.terraform.io/namespaces/terraform-aws-modules)
- [Open Policy Agent (OPA) Policy Language](https://www.openpolicyagent.org/docs/latest/policy-language/)