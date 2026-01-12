# **[Pattern] Cloud Conventions Reference Guide**

---

## **Overview**
The **Cloud Conventions** pattern defines standardized naming, tagging, and structural conventions for cloud resources to ensure consistency, scalability, and maintainability across multi-cloud environments. By adopting these conventions, organizations reduce operational complexity, improve resource discoverability, and streamline compliance and cost management. The pattern covers resource naming, hierarchical tagging, folder/bucket organization, lifecycle policies, and security controls—applicable to IaaS (AWS, Azure, GCP), SaaS (Docker, Kubernetes), and managed services (Databases, APIs).

This guide provides implementation details for resource naming, tagging hierarchies, and operational best practices to enforce consistency across cloud deployments.

---

## **Key Concepts**

| **Concept**               | **Definition**                                                                                     | **Purpose**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Resource Naming**       | Structured prefixsuffix conventions for cloud resources (e.g., `prod-api-webapp-az1`).           | Ensures uniqueness, versioning, and role-based categorization.                                |
| **Tagging Hierarchy**     | Multi-level tags (e.g., `Environment=prod`, `Owner=team-x`) structured by ownership and scope.   | Enables filtering, cost allocation, and security segmentation.                                |
| **Hierarchical Storage**  | Consistent folder/bucket naming (e.g., `projects/{project-name}/environments/{env}/services/{svc}`) | Simplifies access control and automated backups.                                                |
| **Lifecycle Policies**    | Automated retention/expiry rules for transient resources (e.g., logs, snapshots).                 | Reduces costs and ensures compliance with data residency laws.                                |
| **Security Controls**     | Standardized IAM roles, VPC/subnet naming, and encryption policies.                              | Enforces least-privilege access and auditable configurations.                                  |

---

## **Schema Reference**

### **1. Resource Naming Convention**
Use the format:
`{environment}-{application}-{component}-{unique-identifier}-{region-suffix}`

| **Field**               | **Format**                          | **Examples**                          | **Notes**                                      |
|-------------------------|-------------------------------------|---------------------------------------|------------------------------------------------|
| **Environment**         | `dev`, `staging`, `prod`            | `prod`                                | Mandatory; lowercase.                         |
| **Application**         | `{3-letter code}`                    | `web`, `api`, `data`                  | Domain-specific (e.g., `fin` for finance apps). |
| **Component**           | `{abbreviation}`                     | `webapp`, `db`, `cache`               | Lowercase, hyphen-separated.                   |
| **Unique Identifier**   | `{team-abbr}-{version}` or `{id}`   | `team-x-v2`, `app-123`                | For versioning or auto-generated IDs.          |
| **Region Suffix**       | `-{region-az}`                      | `-usw2-az1`                           | Optional for multi-region deployments.         |

**Best Practices:**
- Avoid spaces/punctuation (except hyphens).
- Limit prefixes to 10 characters; suffixes to 5.

---

### **2. Tagging Hierarchy**
Mandatory tags (applied to all resources):

| **Tag Key**          | **Values**                          | **Purpose**                          | **Example**                     |
|----------------------|-------------------------------------|---------------------------------------|---------------------------------|
| `Environment`        | `dev`, `staging`, `prod`            | Scope of the resource.                | `Environment=prod`              |
| `Owner`              | Team name/abbreviation (e.g., `data-engineering`) | Accountability.               | `Owner=finance-team`            |
| `Project`            | Project code (e.g., `pm-xyz123`)     | Cross-team alignment.                 | `Project=pm-xyz123`             |
| `CostCenter`         | Budget code (e.g., `CC-2024-001`)   | Cost tracking.                        | `CostCenter=CC-2024-001`        |
| `CreatedBy`          | Automated tool or user name.        | Audit trail.                          | `CreatedBy=terraform-user`      |

**Optional Tags:**
- `Sensitivity`: `PII`, `Confidential`, `Public`
- `BackupPolicy`: `Daily`, `Weekly`, `Never`
- `EgressRule`: `Restricted`, `PublicIP`, `VPCOnly`

**Example Resource Tags:**
```json
{
  "Environment": "prod",
  "Owner": "data-engineering",
  "Project": "pm-xyz123",
  "CostCenter": "CC-2024-001",
  "Sensitivity": "Confidential",
  "BackupPolicy": "Daily"
}
```

---

### **3. Storage Hierarchy**
Folder/bucket structure:
```
{project-name}/
├── environments/
│   ├── {env}/
│   │   ├── {application}/
│   │   │   ├── {component}/
│   │   │   │   ├── logs/
│   │   │   │   ├── snapshots/
│   │   │   │   └── config/
│   │   └── shared/
│   └── templates/
└── shared-resources/
```

**Folder Naming Rules:**
- Use lowercase, hyphens for separators.
- Avoid numbers unless critical (e.g., `logs-2024-01`).

---

### **4. Lifecycle Policies**
| **Resource Type**  | **Retention Policy**                          | **Expiry Rule**                          | **Example**                     |
|--------------------|-----------------------------------------------|------------------------------------------|---------------------------------|
| Logs (S3/Cloud Storage) | 90 days for dev, 365+ days for prod.      | Delete after retention + 14 days.        | `DeleteAfter=375d`              |
| Snapshots (EBS/RDS) | 7 days for dev, 30 days for prod.           | Expiry at `RetainUntil=2024-12-31`.      | `Expiry=30d`                    |
| Temporary VMs      | 24-hour auto-shutdown in dev.                | Delete after `IdleTimeout=1d`.           | `Lifecycle=ephemeral`           |

---

### **5. Security Controls**
| **Control**               | **Requirement**                                    | **Example Implementation**               |
|---------------------------|----------------------------------------------------|------------------------------------------|
| **IAM Roles**             | Least privilege; role names prefixed by `rd-`.    | `rd-data-readonly`, `rd-s3-fullaccess`   |
| **VPC Naming**            | `{env}-{app}-vpc`.                                | `prod-webapp-vpc`                        |
| **Encryption**            | Default encryption for all block storage.         | `kms-key=arn:aws:kms:...`               |
| **Network Segmentation**  | Subnets named `{env}-{app}-{subnet-role}-{az}`.   | `prod-webapp-public-usw2-az1`           |

---

## **Query Examples**

### **1. Find All Production Databases**
**AWS (CLI):**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=prod" \
  "Name=tag:OwnedBy,Values=data-engineering" \
  --query 'Reservations[*].Instances[*].[InstanceId, Tags[?Key==`Type`].Value]'
```

**Azure (CLI):**
```bash
az sql server show \
  --name prod-db-server \
  --query "[?tags['Environment']=='prod']"
```

### **2. List All Snapshots Expiring Soon**
**GCP (gsutil):**
```bash
gsutil ls -l \
  gs://{bucket}/prod/data-snapshots/* \
  | grep "ExpirationTime:.*2024-06-*" \
  | sort -k 2
```

### **3. Filter Tags by Cost Center**
**Terraform (Policy Check):**
```hcl
resource "aws_s3_bucket" "example" {
  tags = {
    CostCenter = "CC-2024-001"  # Enforced via SCP
  }
}
```

---

## **Implementation Steps**

### **1. Enforce Naming Conventions**
- **Infrastructure-as-Code (IaC):**
  Use tools like **Terraform** or **CloudFormation** with validation rules:
  ```hcl
  variable "resource_name" {
    validation {
      condition     = can(regex("^[a-z0-9-]{3,15}$", var.resource_name))
      error_message = "Must follow lowercase, hyphen-separated format."
    }
  }
  ```

- **CI/CD Pipelines:**
  Add validation in build steps (e.g., GitHub Actions):
  ```yaml
  - name: Validate Naming Convention
    run: |
      if [[ ! "$RESOURCE_NAME" =~ ^[a-z0-9-]{3,15}$ ]]; then
        exit 1
      fi
  ```

### **2. Apply Tagging Automatically**
- **AWS:**
  Use **AWS Config Rules** or **Tag Editor** to enforce tags:
  ```json
  {
    "RuleName": "required-tags",
    "InputParameters": {
      "requiredTags": "[{\"key\":\"Project\",\"required\":\"true\"}]"
    }
  }
  ```

- **Azure:**
  Deploy **Tag Policies** via ARM templates:
  ```json
  {
    "properties": {
      "displayName": "Project Tag Enforcement",
      "definition": {
        "field": "tags.Project",
        "allowedValues": ["pm-xyz123"]
      }
    }
  }
  ```

### **3. Adopt Storage Hierarchy**
- **S3 Buckets:**
  Enforce via **Bucket Policy**:
  ```json
  {
    "Effect": "Deny",
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::invalid-naming/*",
    "Condition": {
      "StringNotLike": {
        "s3:x-amz-acl": "projects/*/environments/*/"
      }
    }
  }
  ```

- **GCP:**
  Use **IAM Conditions** in bucket policies:
  ```json
  {
    "bindings": [
      {
        "role": "roles/storage.objectCreator",
        "condition": {
          "title": "enforce-structure",
          "expression": "request.resource.contains('projects/')"
        }
      }
    ]
  }
  ```

### **4. Automate Lifecycle Policies**
- **AWS:**
  Apply via **S3 Lifecycle Rules**:
  ```json
  {
    "Rules": [
      {
        "ID": "log-expiry",
        "Status": "Enabled",
        "Transitions": [],
        "Expiration": {
          "Days": 90
        }
      }
    ]
  }
  ```

- **Azure:**
  Use **Azure Policy** for Blob Storage:
  ```json
  {
    "properties": {
      "displayName": "Log Retention (90d)",
      "policyRule": {
        "if": {
          "field": "[concat('storageAccountProperties.blobServices[0].containerServiceProperties.containers[].properties.deleteRetentionPolicy.enabled')]",
          "equals": false
        },
        "then": {
          "effect": "auditIfNotExists"
        }
      }
    }
  }
  ```

### **5. Secure Resources**
- **IAM Roles:**
  Restrict access with **条件基于键 (CBOR)**:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "s3:ListBucket",
        "Resource": "arn:aws:s3:::prod-api-bucket",
        "Condition": {
          "StringEquals": {
            "aws:ResourceTag/Environment": "prod"
          }
        }
      }
    ]
  }
  ```

- **Networking:**
  Enforce **VPC Flow Logs** with tags:
  ```bash
  aws ec2 create-flow-logs \
    --resource-type VPC \
    --traffic-type ALL \
    --flow-logs-name prod-webapp-flows \
    --vpc-id vpc-123456 \
    --deliver-logs-permission-arn arn:aws:iam::123456789012:role/flow-logs-role
  ```

---

## **Query Examples (Expanded)**

### **4. Audit Tag Compliance**
**AWS (Athena):**
```sql
SELECT
  resource_id,
  COUNT(DISTINCT tag_key) AS tag_count
FROM cloudtrail_logs
WHERE event_name = 'CreateResource'
  AND eventTime > DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY resource_id
HAVING COUNT(DISTINCT tag_key) < 4;  -- Minimum required tags
```

### **5. Cost Allocation Report**
**GCP (BigQuery):**
```sql
SELECT
  project_id,
  SUM(cost) AS total_cost,
  COUNT(DISTINCT resource_name) AS resource_count
FROM `bigquery-public-data.google_bigquery_analysis.public_data.google_cost`
WHERE date BETWEEN '2024-01-01' AND '2024-01-31'
  AND tags['CostCenter'] = 'CC-2024-001'
GROUP BY project_id;
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Resource Tagging Best Practices](https://cloud.google.com/blog)** | Extends Cloud Conventions with advanced tagging strategies for analytics.     | For cost optimization or compliance reports.    |
| **[Infrastructure Encryption](https://aws.amazon.com/kms/)**         | Standardizes encryption at rest/transit using KMS.                        | For sensitive data compliance (e.g., PCI-DSS).   |
| **[Multi-Region Resilience](https://cloud.google.com/multi-regional)** | Distributes resources across regions with synchronized naming.              | For global low-latency or disaster recovery.    |
| **[Cost Monitoring](https://azure.microsoft.com/en-us/products/cost-management/)** | Integrates with Cloud Conventions to alert on budget overruns.              | Proactive cost management.                      |
| **[GitOps for Cloud](https://www.weave.works/technologies/gitops/)**  | Uses Git to enforce Cloud Conventions in IaC.                              | For CI/CD pipelines with policy-as-code.        |

---

## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| **Resource naming conflicts**       | Use auto-generated IDs (e.g., UUIDs) in `{unique-identifier}`.              |
| **Tag inheritance broken**          | Apply tags at the **root level** (e.g., folder/bucket) to propagate.        |
| **Lifecycle rules not applying**    | Verify **resource state** (e.g., `aws_iam_policy` vs. `aws_iam_role_policy`). |
| **Cross-cloud tag differences**     | Standardize on **AWS:ResourceTag** metadata for portability.               |

---

## **Tools & Integrations**
| **Tool**               | **Purpose**                                                                 | **Link**                                  |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **Terraform**          | Enforce conventions via validators.                                        | [terraform.io](https://www.terraform.io) |
| **AWS Config**         | Audit compliance of tags/naming.                                             | [aws.amazon.com/config](https://aws.amazon.com/config) |
| **Azure Policy**       | Enforce hierarchical rules.                                                  | [azure.microsoft.com/policy](https://azure.microsoft.com/en-us/services/governance/policy/) |
| **Open Policy Agent (OPA)** | Policy-as-code for cross-cloud enforcement.                                 | [openpolicyagent.org](https://www.openpolicyagent.org/) |
| **CycloneDX**          | Validate resource naming in SBOMs.                                           | [cyclonedx.org](https://cyclonedx.org/)   |

---
**Last Updated:** [Insert Date]
**Version:** 1.2