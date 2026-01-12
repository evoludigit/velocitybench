# **[Pattern] Cloud Gotchas Reference Guide**

## **Overview**
Cloud computing introduces operational efficiencies, scalability, and cost flexibility—but it also embeds **hidden pitfalls** (*"gotchas"*) that can lead to unexpected costs, performance degradation, or security vulnerabilities if overlooked. This guide catalogs common **Cloud Gotchas** across infrastructure, networking, security, billing, and operational practices. It provides structured patterns for detecting, mitigating, and avoiding these issues across major cloud providers (AWS, Azure, GCP).

---

## **1. Key Concepts & Implementation Details**
A **Cloud Gotcha** is an **unintended consequence** of misconfigurations, misinterpretations, or overlookings of cloud-specific behaviors. These can be grouped into **categories** with shared causes and remedies:

| **Category**          | **Description**                                                                 | **Common Triggers**                              |
|-----------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Billing**           | Unexpected charges from unused resources, idle services, or over-provisioning. | Auto-scaling, reserved instances, data egress.    |
| **Performance**       | Latency spikes, throttling, or inefficient resource utilization.              | Poor instance sizing, misconfigured IAM.        |
| **Security**          | Over-permissive permissions, exposed endpoints, or compliance violations.     | Loose IAM policies, unencrypted storage.         |
| **Operational**       | Unpredictable outages, data loss, or debugging challenges.                     | Lack of monitoring, no backup strategy.         |
| **Networking**        | Misrouted traffic, security group misconfigurations, or VPN issues.           | Overlapping subnets, incorrect route tables.     |

**Mitigation Strategy**:
- **Automate detection** (e.g., AWS Config, Azure Policy, GCP Security Command Center).
- **Enforce least-privilege access** (IAM roles, RBAC).
- **Monitor usage patterns** (CloudWatch, Azure Monitor, GCP Operations Suite).
- **Audit regularly** (compliance checks, cost reviews).

---

## **2. Schema Reference**
Below is a **standardized schema** for documenting Cloud Gotchas, adaptable to any provider.

| **Field**               | **Description**                                                                 | **Example Values**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Identifier**          | Unique hash or name (e.g., `AWS-S3-Bucket-Logging-Missing`).                  | `AWS-S3-Grant-Public-Access`, `GCP-VPC-Peering-Latency`.                            |
| **Provider**            | Cloud platform (AWS, Azure, GCP, multi-cloud).                                | AWS, Azure, GCP                                                                        |
| **Service**             | Core service affected (EC2, RDS, S3, VNet, etc.).                             | EC2, S3, Lambda, VNet, Cosmos DB, Cloud SQL.                                         |
| **Severity**            | Impact level: Critical, High, Medium, Low.                                      | Critical (data loss), High (cost overruns), Medium (performance degradation).       |
| **Description**         | Concise problem statement and impact.                                          | *"S3 buckets default to public access; objects may be leaked if not explicitly blocked."* |
| **Root Cause**          | Why it happens (misconfiguration, default settings, etc.).                     | Default bucket policy, IAM over-permissioning, no encryption at rest.               |
| **Detection Method**    | How to identify the issue (tools, logs, queries).                               | AWS Config Rules, S3 Access Logs, Azure Policy As-You-Go.                          |
| **Mitigation Steps**    | Step-by-step fix + preventative actions.                                       | Deny public access (`s3:BlockPublicAcls = true`), Enable S3 Object Lock.            |
| **Provider-Specific Docs** | Links to official documentation.                                                | [AWS S3 Bucket Policies Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policy.html) |
| **Related Patterns**    | Linked patterns for broader context (e.g., *Infrastructure as Code*, *Cost Optimization*). | IaC, Tagging Strategy, Reserved Instances Review. |

---

## **3. Query Examples**
Use these **cloud-native queries** to detect common gotchas (syntax varies by provider; adapt as needed).

### **AWS Examples**
#### **Detect Unmonitored EC2 Instances**
```bash
# AWS CLI - List idle instances (no CloudWatch alarms)
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].[InstanceId, State.Name, Tags[?Key==`Name`].Value]' \
  --output text
```
**Gotcha**: Running instances without billing alarms or auto-shutdown schedules.

#### **Find S3 Buckets with Public Access**
```bash
# AWS Config Rules (via AWS Console or CLI)
aws configservice list-discovered-resources \
  --resource-type "AWS::S3::Bucket" \
  --filter name="ResourceId",value="<bucket-name>"
```
**Gotcha**: Accidental public exposure of sensitive data.

---

### **Azure Examples**
#### **Detect Unused Azure VMs**
```powershell
# PowerShell - List inactive VMs (no recent activity)
Get-AzVM | Where-Object { ($_.ProvisioningState -eq "Succeeded") -and
  (Get-AzLogAnalyticsQuery -ResourceGroupName <RG> -QueryResourceId
  (Get-AzResource -Name $_.Name -ResourceGroupName <RG>).ResourceId
  -StartTime (Get-Date).AddDays(-30) -EndTime (Get-Date))
  -ErrorAction SilentlyContinue | Measure-Object }).Count -eq 0 }
```
**Gotcha**: Accumulating costs from unused VMs.

#### **Check Over-Permissive Role Assignments**
```json
# Azure Policy (Definition: Deny roles with * permissions)
{
  "mode": "All",
  "policyRule": {
    "if": {
      "allOf": [
        {"field": "[concat('assignableScopes[0]', '/', subscription().subscriptionId)]",
        "equals": "[subscription().subscriptionId]"},
        {"field": "[concat('roleDefinition.id', '/', roleDefinition().roleName)]",
        "contains": "Contributor"}
      ]
    },
    "then": {
      "effect": "deny"
    }
  }
}
```
**Gotcha**: Role assignments granting excessive permissions.

---

### **GCP Examples**
#### **Find Unused GKE Clusters**
```bash
# gcloud CLI - List idle clusters (no recent node activity)
gcloud container clusters list --format="value(name,status)" \
  | xargs -I {} gcloud container clusters describe {} --format="value(nodePools[*].initialNodeCount,status)"
```
**Gotcha**: Clusters retained past project needs.

#### **Detect Unencrypted GCS Buckets**
```sql
# BigQuery (GCP) - Query for unencrypted buckets
SELECT bucket_name
FROM `region-us`.`projects.*.logs_cloudaudit_*` as audit_log
WHERE protoPayload.methodName = "Storage.Buckets.Insert" OR
      protoPayload.methodName = "Storage.Buckets.LockRetentionPolicy"
AND NOT JSON_CONTAINS(protoPayload.request.payload, '{"encryption":{"defaultKmsKeyName":"gs://..."}}')
```
**Gotcha**: Data encryption misconfigurations.

---

## **4. Common Cloud Gotchas by Category**
### **Billing Gotchas**
| **Gotcha**                          | **Example**                                                                 | **Fix**                                                                               |
|-------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Idling Reserved Instances (RIs)** | RI committed but unused for 3+ months.                                        | Terminate unused RIs, use Spot Instances for flexibility.                             |
| **Data Egress Fees**                | Cross-region data transfer costs not accounted for.                          | Use regional services (e.g., RDS regional endpoints).                               |
| **Orphaned Resources**              | Unattached EBS volumes, unused Lambdas.                                       | Implement tagging + lifecycle policies (e.g., AWS Backup for EBS).                    |

---

### **Security Gotchas**
| **Gotcha**                          | **Example**                                                                 | **Fix**                                                                               |
|-------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **IAM Over-Permissioning**         | `*` permissions in roles or policies.                                         | Enforce least privilege; use AWS IAM Access Analyzer.                                |
| **Default Network ACLs**            | Open inbound/outbound rules in VPC.                                          | Restrict to necessary ports (e.g., allow only SSH from bastion IPs).                   |
| **Exposed API Keys**                | Leaked API keys in logs, Git repos.                                           | Rotate keys; use temporary credentials (AWS STS, GCP Workload Identity).              |

---

### **Performance Gotchas**
| **Gotcha**                          | **Example**                                                                 | **Fix**                                                                               |
|-------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Over-Provisioned Instances**      | EC2 instances sized for peak load but underutilized 90% of the time.        | Use Auto Scaling Groups with CloudWatch metrics.                                      |
| **Cold Start Latency (Serverless)** | Lambda functions idle for >15 minutes.                                        | Use Provisioned Concurrency for predictable workloads.                                |
| **Storage Bottlenecks**             | S3 GET requests throttled due to high throughput.                            | Distribute requests via CloudFront; use S3 Transfer Acceleration.                     |

---

### **Operational Gotchas**
| **Gotcha**                          | **Example**                                                                 | **Fix**                                                                               |
|-------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **No Backup Strategy**              | Critical databases (RDS, Cosmos DB) without automated snapshots.           | Enable automated backups + retention policies (e.g., RDS daily + weekly snapshots).  |
| **Lack of Monitoring**              | No alerts for failed deployments or spike in latency.                        | Set up CloudWatch Alarms (AWS), Azure Monitor (Azure), or GCP Operations Suite.       |
| **Dependency on Single Region**     | All workloads in one availability zone.                                      | Use multi-region deployments (e.g., Global Accelerator for low-latency apps).        |

---

## **5. Related Patterns**
To complement **Cloud Gotchas**, reference these established patterns:

| **Pattern**                          | **Description**                                                                 | **Link to Reference**                          |
|--------------------------------------|---------------------------------------------------------------------------------|------------------------------------------------|
| **Infrastructure as Code (IaC)**     | Automate deployments via Terraform, CloudFormation, or Bicep to avoid manual misconfigurations. | [AWS CloudFormation Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/userguide/what-is-cloudformation.html) |
| **Tagging Strategy**                 | Tag resources for cost allocation, ownership, and compliance tracking.       | [AWS Tagging Best Practices](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/tagging-best-practices.html) |
| **Cost Optimization**                | Right-size resources, use spot instances, and set up budget alerts.            | [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) |
| **Disaster Recovery (DR)**           | Implement multi-region backups and failover strategies.                        | [AWS Well-Architected DR Frameworks](https://docs.aws.amazon.com/wellarchitected/latest/dr-frameworks/welcome.html) |
| **Security Hardening**              | Enforce encryption, network segmentation, and least privilege access.         | [CIS Benchmarks for Cloud](https://www.cisecurity.org/benchmark/) |

---

## **6. Best Practices Summary**
1. **Automate Detection**: Use tools like **AWS Config**, **Azure Policy**, or **GCP Security Command Center**.
2. **Enforce Guardrails**: Apply **IAM policies**, **network ACLs**, and **backup rules** via IaC.
3. **Monitor Proactively**: Set up **CloudWatch Alarms**, **Azure Monitor Queries**, or **GCP Operations Dashboards**.
4. **Review Regularly**: Schedule ** billing/review cycles** (e.g., monthly cost audits).
5. **Document Gotchas**: Maintain a **runbook** of common issues (e.g., Confluence, GitHub Wiki).

---
**Note**: This guide is **provider-agnostic** but includes provider-specific examples. For full implementation, refer to your cloud provider’s documentation linked in the *Provider-Specific Docs* field.