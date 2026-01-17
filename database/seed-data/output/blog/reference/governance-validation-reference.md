# **[Pattern] Reference Guide: Governance Validation**
*A structured approach to enforcing compliance, consistency, and security in technical systems.*

---

## **Overview**
Governance Validation enforces predefined rules, policies, and constraints across cloud resources, infrastructure, or application deployments to ensure:
- **Compliance** with regulatory standards (e.g., SOC2, GDPR, HIPAA).
- **Security** by mitigating vulnerabilities (e.g., open ports, outdated software).
- **Operational consistency** (e.g., tagging conventions, cost controls).
- **Auditability** via structured validation logs.

This pattern integrates with **Infrastructure as Code (IaC)** tools (Terraform, CloudFormation), **CI/CD pipelines**, and cloud provider APIs (AWS Config, Azure Policy, GCP Recommender). Validations can be **proactive** (pre-deployment checks) or **reactive** (post-event remediation).

---

## **Key Concepts**

| Term               | Definition                                                                                                                                                                                                                                                                                                                                 |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Policy Rule**    | A declarative condition (e.g., *"All EC2 instances must have a minimum 2 vCPUs"*) tied to a **compliance standard** (e.g., *AWS Well-Architected*). Rules may include **remediation actions** (e.g., terminate non-compliant instances).                                                                                     |
| **Validation Scope** | The context where rules apply (e.g., **account-level**, **region-specific**, **resource-type-specific** like "S3 buckets").                                                                                                                                                                                              |
| **Severity Levels** | Defines urgency/impact (e.g., **Critical**: Block deployment; **Warning**: Log but allow; **Informational**: No action).                                                                                                                                                                             |
| **Remediation Script** | Automated fix (e.g., Terraform apply, API call) executed post-validation failure.                                                                                                                                                                                                                         |
| **Exclusion Tags**  | Opt-out markers (e.g., `compliance-exempt=true`) to exclude specific resources from validation.                                                                                                                                                                                                           |
| **Validation Triggers** | Events that invoke checks (e.g., **resource create/update/delete**, **scheduled scans**, **user-initiated compliance reports**).                                                                                                                                                                           |

---

## **Schema Reference**
Validate resources via a standardized schema (JSON/YAML) or cloud provider policies.

### **1. Rule Definition Schema**
```json
{
  "name": "Require-Min-2-VCPUs",
  "description": "Enforce minimum 2 vCPUs for production EC2 instances.",
  "provider": "aws",
  "scope": ["region": "us-east-1", "resourceType": "EC2"],
  "complianceStandard": "AWS Well-Architected",
  "severity": "Critical",
  "ruleType": "Condition",
  "condition": {
    "operator": "and",
    "tests": [
      { "key": "InstanceType", "operator": "notIn", "values": ["t2.micro", "t3.small"] },
      { "key": "Tag['Environment']", "operator": "equals", "value": "production" }
    ]
  },
  "remediation": {
    "action": "stop_and_terminate",
    "script": "scripts/ec2-resize-min-2vcpus.sh"
  },
  "exclusions": [
    { "tag": "compliance-exempt", "value": "true" }
  ]
}
```

### **2. Validation Output Schema**
```json
{
  "result": "non_compliant",
  "resourceId": "i-1234567890abcdef0",
  "rule": "Require-Min-2-VCPUs",
  "timestamp": "2024-05-20T12:00:00Z",
  "details": {
    "vCPUs": 1,
    "expectedMin": 2,
    "remediationStatus": "pending"
  },
  "suggestedFix": {
    "action": "resize_instance",
    "resources": ["ami-id: ami-0abcdef1234567890"]
  }
}
```

---

## **Query Examples**
### **1. AWS Config Query (CloudTrail)**
```bash
aws configservice list-discovered-resources \
  --configuration-recorder-name "compliance-recorder" \
  --resource-type "AWS::EC2::Instance" \
  | jq '
    .configurationItems[]
    | select(.resourceType == "AWS::EC2::Instance")
    | select(.resourceId | test(/^i-[0-9a-z]{8}$/))
  '
```
**Use Case**: List EC2 instances for governance validation.

### **2. Azure Policy Query (ARM Template)**
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "resources": [
    {
      "type": "Microsoft.Authorization/policyAssignments",
      "name": "Require-Vnet-Subnet",
      "properties": {
        "policyDefinition": "/subscriptions/00000000-1111-2222-3333-444444444444/providers/Microsoft.Authorization/policyDefinitions/48b192cc-..."
      },
      "dependsOn": []
    }
  ]
}
```
**Use Case**: Enforce VNet/subnet separation for Azure resources.

### **3. GCP Recommender Query (REST API)**
```bash
gcloud resource-manager recommender-recommendations list \
  --recommender="security/recommendations" \
  --filter="resource.type='compute_vm_instance' and recommendationCategory='SECURITY'"
```
**Use Case**: Identify unpatched VMs with open ports.

---

## **Implementation Steps**
### **1. Define Policies**
- **Tooling**: Use Terraform `aws_config_rule`, Azure Policy JSON, or GCP Policy Controller.
- **Example (Terraform)**:
  ```hcl
  resource "aws_config_rule" "ec2_tag_requirements" {
    name     = "ec2-tag-requirements"
    source {
      owner     = "AWS"
      source_identifier = "REQUIRE_TAGS"
    }
    input_parameters = jsonencode({
      tag1 = { key = "Environment", expected = ["production", "dev"] },
      tag2 = { key = "Owner", expected = ["team-a", "team-b"] }
    })
  }
  ```

### **2. Integrate with CI/CD**
- **GitHub Actions Example**:
  ```yaml
  - name: Run Governance Validation
    uses: example/governance-validator@v1
    with:
      validation-script: validate-aws-resources.sh
      severity-threshold: "Critical"
      fail-on-warnings: true
  ```

### **3. Automate Remediation**
- **AWS Lambda Trigger**: Execute `aws ec2 modify-instance-attribute` to add missing tags.
- **Example Script**:
  ```bash
  #!/bin/bash
  aws ec2 modify-instance-attribute \
    --instance-id $INSTANCE_ID \
    --attribute "tagSpecifications" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Environment,Value=production}]"
  ```

### **4. Generate Reports**
- **AWS Config Aggregator**: Sync cross-account compliance data.
- **Example CLI**:
  ```bash
  aws configservice aggregate-compliance \
    --account-ids "123456789012 987654321098" \
    --configuration-recorder-name "compliance-recorder" \
    --output-format "text" > compliance-report.txt
  ```

---

## **Query Examples (Expanded)**
### **Find Non-Compliant S3 Buckets (AWS CLI)**
```bash
aws s3api list-buckets \
  --query "Buckets[?tags[?key=='compliance-status' && value=='non-compliant'].key==`compliance-status`].Name" \
  --output text
```

### **Azure Policy Compliance Summary**
```powershell
(Get-AzPolicyAssignment -Filter "displayName eq 'Require-Vnet-Subnet'").ComplianceState | Sort-Object
```

### **GCP IAM Policy Violations**
```bash
gcloud iam policies get-binding \
  --member="user:example@domain.com" \
  --policy=projects/my-project/roles/..." \
  --format=json | jq '.bindings[].members'
```

---

## **Error Handling & Edge Cases**
| Scenario                          | Recommendation                                                                                                                                                                                                                                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Temporary non-compliance**      | Use `severity="Warning"` with a **wait-timeout** (e.g., 7-day grace period).                                                                                                                                                                                               |
| **Resource locked/non-modifiable** | Return `remediationStatus="manual-review"` with a **Jira ticket link** for manual action.                                                                                                                                                                          |
| **Exclusion tag misconfigured**   | Log a `Warning` and suggest retagging via CloudWatch.                                                                                                                                                                                                                             |
| **API throttling**                | Implement **exponential backoff** in remediation scripts.                                                                                                                                                                                                                           |
| **Cross-cloud validation**        | Use **Terraform Cloud** or **Open Policy Agent (OPA)** for unified checks.                                                                                                                                                                                                     |

---

## **Related Patterns**
1. **Infrastructure as Code (IaC) Guardrails**
   - *How to*: Embed governance rules in Terraform/TFModules or AWS CloudFormation Macros.
   - *Tooling*: Terraform `count` conditions, `aws_iam_policy_document` validation.

2. **Compliance-as-Code**
   - *How to*: Use **Open Policy Agent (OPA)** with Rego policies for fine-grained access control.
   - *Example*: [OPA Policy Examples](https://rego.readthedocs.io/en/latest/examples/)

3. **Observability for Governance**
   - *How to*: Integrate **Prometheus/Grafana** for real-time compliance dashboards.
   - *Metrics*: `compliance_rule_failed_total`, `resource_tags_missing`.

4. **Chaos Engineering for Governance**
   - *How to*: Simulate policy violations (e.g., delete a tag) to test remediation workflows.
   - *Tooling*: Gremlin, Chaos Mesh.

5. **Policy-as-Code with GitOps**
   - *How to*: Store policies in Git (e.g., GitHub Repo) and sync via **ArgoCD** or **Flux**.
   - *Example*: [GitOps for Policy](https://www.argoproj.io/docs/argo-cd/user-guide/rbac/)

6. **zero-trust Governance**
   - *How to*: Combine governance with **identity-aware access** (e.g., AWS IAM Conditions, Azure Conditional Access).
   - *Example*: Block S3 bucket access unless `compliance-status = "approved"`.

---

## **Best Practices**
1. **Start Small**: Validate **1-3 critical rules** before expanding (e.g., tag requirements > security patches).
2. **Document Exclusions**: Track opted-out resources in a **Compliance Exceptions DB** (e.g., DynamoDB).
3. **Alert Fatigue Mitigation**:
   - Use **severity-based alerting** (e.g., PagerDuty for Critical, Slack for Warning).
   - Suppress repeated alerts for **known-good non-compliance** (e.g., staging environments).
4. **Cross-Team Alignment**:
   - Engage **Security, DevOps, and Finance** teams to define rules.
   - Example: Finance may enforce **cost-tagging** (`CostCenter=1234`), DevOps may enforce **security tags** (`SecurityClass=High`).
5. **Automate Remediation**: Aim for **>90% auto-remediation rate** to reduce manual effort.
6. **Regular Audits**: Schedule **quarterly policy reviews** to update rules (e.g., new regulations, tooling updates).
7. **Immutable Resources**: Where possible, use **immutable infrastructure** (e.g., AWS EBS snapshots) to simplify validation.

---
## **Troubleshooting**
| Issue                          | Solution                                                                                                                                                                                                                                                                 |
|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **False Positives**            | Refine conditions (e.g., exclude `Environment=test` from `Require-Min-2-VCPUs`).                                                                                                                                                                               |
| **Performance Bottlenecks**    | Batch validation queries (e.g., paginate AWS Config results).                                                                                                                                                                                           |
| **Vendor Lock-in**             | Use **OPA** or **Terraform** for portable policies.                                                                                                                                                                                                           |
| **Missing Documentation**      | Generate **auto-docs** from policy schemas (e.g., [Slate](https://github.com/slatedocs/slate)).                                                                                                                                                   |
| **Policy Conflicts**           | Prioritize rules with **explicit override tags** (e.g., `compliance-level=high`).                                                                                                                                                                        |

---
## **Further Reading**
- [AWS Config Rule Examples](https://docs.aws.amazon.com/config/latest/userguide/evaluate-config_with-aws-config-rules.html)
- [Azure Policy Definitions](https://learn.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure)
- [GCP Recommender](https://cloud.google.com/resource-manager/docs/recommender/recommender)
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/)
- [Terraform Cloud Governance](https://developer.hashicorp.com/terraform/cloud-docs/enterprise/governance)