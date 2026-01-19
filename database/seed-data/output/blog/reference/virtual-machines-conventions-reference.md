# **[Pattern] Virtual Machines Conventions Reference Guide**

---

## **Overview**
The **Virtual Machines Conventions** pattern defines standardized conventions for naming, tagging, and managing virtual machines (VMs) to ensure consistency, scalability, and operational efficiency across cloud and on-premises environments. These conventions help teams avoid naming collisions, simplify discoverability, and enforce compliance with security, governance, and lifecycle policies.

This guide outlines **requirements, schema, query examples, and best practices** for implementing VM conventions in hybrid infrastructure settings. It assumes familiarity with cloud platforms (AWS, Azure, GCP) and virtualization tools (VMware, Hyper-V).

---

## **1. Core Conventions Schema**

| **Category**          | **Field**               | **Description**                                                                                                                                                     | **Format Examples**                                                                                     | **Requirements**                                                                                     |
|-----------------------|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Naming**            | `vm-name`               | Unique, human-readable identifier. Follows camelCase or kebab-case. Avoid special characters.                                                                      | `app-db-postgres-primary`, `ml-workload-ai-training-alg01`                                            | - Max **64 chars**<br>- Must include **environment suffix** (`dev`, `staging`, `prod`).<br>- Prefix: **team/role** (`hr`, `finance`, `devops`). |
|                       | `vm-id`                 | Auto-generated, immutable identifier (e.g., AWS Instance ID, Azure VM-ID).                                                                                         | `i-1234ab56`, `vm-8765efgh`                                                                             | - Auto-assigned by provider (use existing IDs).<br>- **No manual override.**                          |
| **Tagging**           | `purpose`               | Role/function of the VM (e.g., database, application, dev machine).                                                                                              | `database`, `web-server`, `jump-host`                                                                  | - **Mandatory**.<br>- Must match **1 of 30 predefined values** (see [Appendix](#tagging-roles)).    |
|                       | `environment`           | Deployment stage (dev, staging, prod).                                                                                                                             | `dev`, `staging`, `prod`                                                                               | - **Mandatory**.<br>- **No uppercase letters.**                                                      |
|                       | `owner`                 | Team/owner responsible for the VM (e.g., `marketing-team`, `finance`).                                                                                     | `hr-department`, `data-science`                                                                        | - **Mandatory**.<br>- Use **consistent team naming** (e.g., `engineering-frontend`).                 |
|                       | `cost-center`           | Budget code (e.g., `dept-123`, `project-xyz`).                                                                                                                 | `dept-123`, `innovation-fund-2024`                                                                    | - **Mandatory for prod/staging**.<br>- Format: **alphanumeric + hyphen**.                             |
|                       | `project`               | High-level initiative (e.g., `payroll-upgrade`, `ml-scaleout`).                                                                                                | `payroll-upgrade-v2`, `ml-scaleout-phase2`                                                            | - **Optional for dev**.<br>- Max **32 chars**.                                                          |
|                       | `security-level`        | Compliance classification (e.g., `internal-only`, `public-read`).                                                                                             | `internal-only`, `public-read`, `restricted`                                                          | - **Mandatory for prod**.<br>- See [Appendix](#security-levels).                                     |
|                       | `maintenance-window`    | Scheduled downtime (e.g., `mon-fri-0300-0500`).                                                                                                               | `mon-fri-0200-0400`, `weekend-only`                                                                    | - **Mandatory for prod**.<br>- Format: `weekday-hours`.                                               |
|                       | `image-version`         | OS/base image version (e.g., `ubuntu-22.04-lts`, `windows-2022`).                                                                                            | `ubuntu-22.04-lts`, `rhel-8.6`                                                                         | - **Mandatory**.<br>- Include **patch level** (e.g., `-1`).                                           |
|                       | `deletion-protected`    | Flag to prevent accidental deletion (true/false).                                                                                                            | `true`, `false`                                                                                       | - Default: **false for dev**, **true for prod**.                                                     |
| **Lifecycle**         | `provisioner`           | Tool/team responsible for provisioning (e.g., `terraform`, `cloud-ops`).                                                                                        | `terraform`, `cloud-ops`                                                                               | - **Mandatory**.<br>- Use **lowercase + hyphen**.                                                    |
|                       | `provision-date`        | ISO 8601 timestamp (e.g., `2024-05-15T14:30:00Z`).                                                                                                       | `2024-05-15T14:30:00Z`                                                                                 | - Auto-filled by system.                                                                               |
|                       | `expiry-date`           | Scheduled termination (ISO 8601).                                                                                                                          | `2024-12-31T00:00:00Z` (for dev VMs)                                                                   | - **Mandatory for dev/staging**.<br>- Format: **YYYY-MM-DD**.                                         |
| **Networking**        | `vpc-id`                | Virtual Private Cloud/Network ID (e.g., `vpc-12345678`).                                                                                                       | `vpc-12345678`, `network-abc123`                                                                       | - **Mandatory**.<br>- Use **provider-assigned ID**.                                                   |
|                       | `subnet-id`             | Subnet identifier (e.g., `subnet-abc123`).                                                                                                                   | `subnet-abc123`, `10.0.1.0/24`                                                                           | - **Mandatory**.<br>- Include **CIDR if internal**.                                                  |
|                       | `security-group`        | Allowlist rules (e.g., `allow-ssh:10.0.0.0/8`).                                                                                                            | `allow-ssh:0.0.0.0/0`, `deny-all:except-0.0.0.0/0`                                                      | - **Mandatory**.<br>- Format: `rule:source-ip`.                                                       |
| **Compliance**        | `compliance-tag`        | Regulatory tags (e.g., `gdp-privacy`, `hipa`).                                                                                                             | `gdp-privacy`, `sox-compliant`                                                                          | - **Mandatory for prod**.<br>- Max **2 tags**.                                                         |
|                       | `audit-trail`           | Flag for enabled auditing (true/false).                                                                                                                   | `true`, `false`                                                                                       | - Default: **true for prod**.                                                                           |

---

## **2. Schema Validation Rules**
| **Rule**                          | **Description**                                                                                                                                                     | **Example**                                                                                            |
|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Naming Collision**              | VM names must be **globally unique** within a region/tenant.                                                                                                     | ✅ `app-web-server-dev` (OK)<br>❌ `app-web-server` (ambiguous)                                      |
| **Tag Consistency**               | Tags must match **predefined dictionaries** (e.g., `purpose`, `security-level`).                                                                                 | ✅ `purpose:database`<br>❌ `purpose:db` (invalid)                                                      |
| **Expiry Enforcement**            | Dev VMs **must expire** within **90 days** unless approved.                                                                                                       | ✅ `expiry-date:2024-08-15` (OK)<br>❌ `expiry-date:2025-01-01` (invalid)                        |
| **Provisioner Ownership**         | The `provisioner` tag must match the **requesting team**.                                                                                                       | ✅ `provisioner:devops` (if requested by DevOps)<br>❌ `provisioner:hr` (invalid)                   |
| **Network Isolation**             | Prod VMs **must** be in a **dedicated subnet**.                                                                                                                   | ✅ `subnet-id:prod-subnet-1` (OK)<br>❌ `subnet-id:shared-subnet` (invalid)                           |

---

## **3. Query Examples**
Use these queries to filter VMs based on conventions in **AWS CLI**, **Azure CLI**, or **GCP SDK**.

### **AWS CLI (EC2)**
```bash
# List all prod databases in the 'engineering' team
aws ec2 describe-instances \
  --filters "Name=tag:environment,Values=prod" \
          "Name=tag:purpose,Values=database" \
          "Name=tag:owner,Values=engineering*" \
  --query "Reservations[].Instances[].[InstanceId, Tags[?Key=='vm-name'].Value | [0]]"

# Find VMs expiring in 30 days (dev environment)
aws ec2 describe-instances \
  --filters "Name=tag:environment,Values=dev" \
          "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].[InstanceId, Tags[?Key=='expiry-date'].Value | [0]]" \
  --output text | xargs -I {} aws ec2 describe-tags --filters "Name=resource-id,Values={}" \
    --query "Tags[?Key=='expiry-date'].Value" | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}"
```

### **Azure CLI**
```bash
# List all VMs tagged with 'cost-center:dept-123'
az vm list --query "[?tags.cost_center=='dept-123']" \
  --output table --show-details

# Find VMs with security-level 'restricted'
az vm list --query "[?tags['security-level']=='restricted']" \
  --output json | jq '.[] | {vm_name: .name, tags: .tags}'
```

### **GCP (gcloud)**
```bash
# List all VMs in 'staging' environment with 'image-version' containing 'ubuntu'
gcloud compute instances list \
  --filter="tags.items.environment='staging' AND tags.items.image-version:~/ubuntu" \
  --format="table(name,zone,tags.items)"

# Find VMs without a deletion-protected tag
gcloud compute instances list \
  --filter="NOT tags.items.deletion-protected:" \
  --format="table(name,zone)"
```

---

## **4. Implementation Steps**
### **Step 1: Enforce Naming via IAM Policies**
- **AWS**: Use **AWS Resource Access Manager (RAM)** to restrict VM creation to names matching regex:
  ```json
  {
    "Effect": "Deny",
    "Action": "ec2:RunInstances",
    "Resource": "*",
    "Condition": {
      "StringNotLike": { "ec2:Tags/vm-name": "*^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*(-(dev|staging|prod))$" }
    }
  }
  ```
- **Azure**: Use **Azure Policy** to validate VM names:
  ```json
  {
    "mode": "All",
    "policyRule": {
      "if": {
        "allOf": [
          { "field": "tags['environment']", "notEquals": "dev" },
          { "field": "name", "matches": "^[a-z0-9][a-z0-9-]*[a-z0-9](-[dev|staging|prod])$" }
        ]
      }
    }
  }
  ```

### **Step 2: Automate Tagging with Infrastructure-as-Code (IaC)**
- **Terraform (AWS Example)**:
  ```hcl
  resource "aws_instance" "example" {
    tags = {
      vm-name       = "app-web-server-${var.env}"
      purpose       = "web-server"
      environment   = var.env
      owner         = "frontend-team"
      cost-center   = "dept-456"
      image-version = "ubuntu-22.04-lts"
    }
  }
  ```
- **Azure ARM Template**:
  ```json
  {
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
    "resources": [
      {
        "type": "Microsoft.Compute/virtualMachines",
        "apiVersion": "2023-03-01",
        "name": "[variables('vmName')]",
        "tags": {
          "vm-name": "[variables('vmName')]",
          "purpose": "database",
          "environment": "[parameters('environment')]"
        }
      }
    ]
  }
  ```

### **Step 3: Enforce Expiry with Cloud Scheduler**
- **AWS**: Use **AWS Lambda + EventBridge** to check expiry dates:
  ```python
  # Lambda function (Python) to cleanup expired dev VMs
  import boto3

  def lambda_handler(event, context):
      ec2 = boto3.client('ec2')
      today = datetime.now().strftime('%Y-%m-%d')
      expired_vms = ec2.describe_instances(
          Filters=[
              {'Name': 'tag:environment', 'Values': ['dev']},
              {'Name': 'tag:expiry-date', 'Values': [f'{today}*']},
              {'Name': 'instance-state-name', 'Values': ['running']}
          ]
      )
      for vm in expired_vms['Reservations']:
          ec2.stop_instances(InstanceIds=[vm['Instances'][0]['InstanceId']])
          ec2.terminate_instances(InstanceIds=[vm['Instances'][0]['InstanceId']])
  ```
- **Azure**: Use **Azure Monitor Alerts** with Logic Apps to tag/terminate expired VMs.

### **Step 4: Audit Compliance with Config Rules**
- **AWS Config**:
  ```json
  {
    "ConfigRuleName": "vm-tagging-compliance",
    "Source": {
      "Owner": "AWS",
      "SourceIdentifier": "COM_INDEX_0"
    },
    "Statement": {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "config:*",
      "Resource": "*",
      "Condition": {}
    },
    "InputParameters": {
      "requiredTags": [
        {
          "key": "environment",
          "values": ["dev", "staging", "prod"]
        },
        {
          "key": "purpose",
          "values": ["database", "web-server", "dev-machine"]
        }
      ]
    }
  }
  ```
- **Azure Policy**:
  ```json
  {
    "mode": "All",
    "policyRule": {
      "if": {
        "allOf": [
          { "field": "tags.environment", "notEquals": "dev" },
          { "not": { "field": "tags.provisioner" } }
        ]
      }
    }
  }
  ```

---

## **5. Query Examples (Advanced)**
### **Find Orphans: VMs Without a `provisioner` Tag**
```bash
# AWS
aws ec2 describe-instances \
  --filters "Name=tag:provisioner,Values:*" \
  --query "Reservations[].Instances[?contains(tags[*].{Key:Key,Value:Value}, [Key:'provisioner',Value:''])].InstanceId" \
  --output text

# Azure
az vm list --query "[?not_contains(tags.provisioner, '')]" --output table
```

### **Identify VMs with Unapproved Security Groups**
```bash
# GCP
gcloud compute instances list \
  --filter="tags.items.security-group:~/^(allow-ssh:10\..*|deny-all:except-0\..*)$" \
  --format="table(name)"

# AWS
aws ec2 describe-security-groups \
  --group-ids $(aws ec2 describe-instances --query "Reservations[].Instances[].SecurityGroups[].GroupId" --output text) \
  --query "SecurityGroups[?IpPermissions[?(IpProtocol=='tcp' && FromPort==22 && IpRanges[*].CidrIp!='10.0.0.0/8')].IpPermissions[*]]" \
  --output text | grep -v "10.0.0.0/8"
```

---

## **6. Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                     | **When to Use**                                                                                          |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Infrastructure-as-Code (IaC)** | Standardize VM provisioning via Terraform/Pulumi for repeatable deployments.                                                                                         | When scaling VMs across environments (dev/staging/prod).                                                   |
| **Tag-Based Access Control**     | Restrict VM access based on tags (e.g., `environment=prod` requires MFA).                                                                                            | For **zero-trust security models**.                                                                        |
| **Auto-Scaling Groups**          | Dynamically adjust VM counts based on workload (e.g., `purpose=web-server`).                                                                                      | For **stateless applications** with variable traffic.                                                       |
| **Spot Instance Conventions**    | Extend VM conventions for spot instances (`spot-termination:preemptible`).                                                                                         | For **cost-sensitive, fault-tolerant workloads**.                                                            |
| **Blue/Green Deployments**       | Use VM tags (`deployment:blue`, `deployment:green`) to route traffic.                                                                                             | For **minimal downtime updates**.                                                                           |
| **Cost Allocation Tags**         | Align VM tags (`cost-center`) with cloud provider cost reports.                                                                                                   | For **budget tracking and chargeback**.                                                                    |

---

## **7. Appendix**
### **Predefined Tag Values**
