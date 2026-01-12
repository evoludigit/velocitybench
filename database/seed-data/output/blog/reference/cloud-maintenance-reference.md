---
**[Pattern] Reference Guide: Cloud Maintenance**
*Best Practices, Implementation, and Automation for Sustained Cloud Infrastructure Health*

---

### **1. Overview**
The **Cloud Maintenance** pattern ensures cloud environments remain **highly available, secure, and optimized** by automating routine tasks like patching, backups, monitoring, and capacity adjustments. It combines **Infrastructure as Code (IaC)**, **automated pipelines**, and **observability** to reduce manual overhead while minimizing downtime.

Key benefits:
- **Proactive fixes** (e.g., OS patches, dependency updates).
- **Cost efficiency** (right-sizing resources, eliminating idle instances).
- **Compliance adherence** (automated policy enforcement).
- **Disaster recovery** (consistent backup and restore processes).

This guide details schema designs, implementation steps, and tooling for integrating cloud maintenance into CI/CD pipelines.

---

### **2. Schema Reference**
Use the following schema to model maintenance workflows in **CloudFormation (AWS), Terraform, or Azure Resource Manager (ARM)**.

| **Component**          | **Description**                                                                 | **Key Attributes**                                                                                     | **Example Input**                     |
|------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------|
| **Maintenance Window** | Defines when patches/reboots occur (e.g., off-peak hours).                      | `StartTime`, `Duration`, `Timezone`, `Recurrence` (weekly/daily).                                      | `"2024-06-15T02:00:00Z"`, `"PT1H"`    |
| **Patch Group**        | Logical grouping of resources (e.g., "web-servers", "db-instances").               | `Name`, `Source` (e.g., AWS Systems Manager, Patch Manager), `Severity` (Critical/High).              | `"Name": "app-servers"`               |
| **Action Plan**        | Sequence of tasks (e.g., "install-patches", "test-connections").                | `Steps` (order), `Conditions` (e.g., "if CPU > 80%"), `RollbackPlan`.                                 | `[ { "action": "patch", "target": "OS" } ]` |
| **Notification**       | Alerts for critical events (e.g., failed patching).                            | `Topic` (SNS/SQL), `Threshold` (e.g., "3 failed attempts"), `Recipients`.                              | `"Topic": "arn:aws:sns:us-east-1:123456789012:MaintenanceAlerts"` |
| **Resource Tag**       | Tags to filter maintenance scope.                                               | `Key`: `Maintenance`, `Value`: `Automated` (or custom groups).                                         | `"Key": "Environment", "Value": "Prod"` |
| **Rollback Strategy**  | Recovery plan if maintenance fails.                                             | `Action` (e.g., "restore-from-snapshot"), `Timeout`.                                                  | `"Action": "RollbackToLastGoodPatch"`  |

---
**Example Schema Snippet (Terraform):**
```hcl
resource "aws_systems_managerMaintenanceWindow" "example" {
  name     = "prod-servers-weekly"
  duration = 60  # minutes
  schedule = "cron(0 3 ? * MON *)"  # 3 AM on Mondays
  tags = {
    Environment = "Production"
  }
}

resource "aws_systems_managerMaintenanceWindowTask" "patch_task" {
  maintenance_window_id = aws_systems_managerMaintenanceWindow.example.id
  task_type            = "RUN_COMMAND"
  task_role_arn        = "arn:aws:iam::123456789012:role/SSM-Patch-Role"
  task_invoke_parameters {
    run_command_targets {
      key    = "InstanceIds"
      values = ["i-1234567890abcdef0"]  # Replace with tag-based filtering
    }
  }
}
```

---

### **3. Implementation Steps**
#### **Step 1: Define Maintenance Scope**
- **Tag resources** with `Maintenance: Automated` or custom groups (e.g., `Tier: High`).
- Use **AWS Resource Groups** or **Azure Tags** to filter targets:
  ```bash
  # AWS CLI: List tagged instances
  aws ec2 describe-instances --filters "Name=tag:Maintenance,Values=Automated"
  ```

#### **Step 2: Automate Patching**
| **Cloud Provider** | **Tool**               | **Key Features**                                                                 |
|--------------------|------------------------|---------------------------------------------------------------------------------|
| AWS                | SSM Patch Manager       | Supports OS patches, custom maintenance windows, approval gates.               |
| Azure              | Update Management      | Patch packages for VMs, containers, and IaaS.                                    |
| GCP                | Operations Suite       | Automated patching for Compute Engine instances with predefined policies.       |
| Multi-Cloud        | Ansible/Puppet         | Agent-based patching with cross-platform playbooks.                              |

**Example: AWS SSM Patch Baseline (JSON)**
```json
{
  "PatchGroups": {
    "OS-Patches": {
      "PatchRules": [
        {
          "PatchFilterGroup": {
            "PatchTypes": ["SecurityUpdates", "CriticalUpdates"],
            "ApprovedPatchesOnly": false
        }
      }
    }
  }
}
```

#### **Step 3: Integrate with CI/CD**
- **GitHub Actions Example** (patch validation):
  ```yaml
  - name: Run patch compliance check
    uses: actions/github-script@v6
    with:
      script: |
        const { data: patches } = await github.rest.systemsManager.listComplianceSummaries({
          instanceId: context.issue.number,
          filters: { patchGroups: ["OS-Patches"] }
        });
        if (patches.some(p => p.complianceResourceType === "NON_COMPLIANT")) {
          core.setFailed("Unpatched instances found!");
        }
  ```

#### **Step 4: Monitor and Alert**
- **Metrics to Track**:
  - **Patch Compliance** (% of resources patched).
  - **Reboot Failures** (consecutive failures).
  - **CPU/Memory Spikes** post-patch.
- **Tools**:
  - AWS CloudWatch + SNS for alerts.
  - Azure Monitor + Logic Apps for workflows.
  - Prometheus/Grafana for custom dashboards.

**Query Example (CloudWatch):**
```sql
-- Check failed patch attempts
SELECT * FROM "SSM/PatchCompliance"
WHERE "PatchStatus" = 'FAILED'
AND "InstanceId" IN (
  SELECT InstanceId FROM "EC2/InstanceStatus"
  WHERE "InstanceState.name" = 'running'
)
```

---

### **4. Query Examples**
#### **A. List Unpatched Instances (AWS CLI)**
```bash
aws ssm get-compliance-summaries \
  --instance-ids "i-1234567890*" \
  --filters '{"name":"PATTERNS","values":["*.SecurityUpdates"]}' \
  --query "ComplianceSummaries[?complianceResourceType=='NON_COMPLIANT']"
```

#### **B. Filter Azure VMs by Maintenance Tag**
```powershell
# Azure CLI
az vm list --query "[?tags['Maintenance']=='Automated']" --output table
```

#### **C. Trigger Manual Rollback (Terraform)**
```hcl
resource "aws_ssm_document" "rollback_plan" {
  name          = "rollback-app-servers"
  document_type = "Command"
  content = jsonencode({
    "schemaVersion": "2.2",
    "description": "Restore from snapshot",
    "runtimeConfig": {
      "aws:runShellScript": {
        "runCommand": [
          "echo 'Restoring from snapshot...' && aws ec2 create-volume-image --volume-id vol-1234567890abcdef0 --region us-east-1"
        ]
      }
    }
  })
}
```

---

### **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Blue/Green Deployment** | Zero-downtime updates by shifting traffic.                                      | Critical applications requiring 99.99% uptime.   |
| **Chaos Engineering**     | Intentional failure testing to validate resilience.                            | Post-maintenance validation.                     |
| **Cost Optimization**     | Right-sizing resources post-maintenance.                                       | Cloud environments with idle resources.          |
| **Disaster Recovery**     | Automated failover to backup regions.                                           | Multi-region deployments.                        |
| **Secret Rotation**       | Automated credential updates for security.                                      | Long-running services with static credentials.   |

---
### **6. Best Practices**
1. **Test in Staging**: Validate patches on a non-production clone before production.
2. **Granular Rollback**: Use snapshot-based recovery (e.g., AWS EBS snapshots).
3. **Logging**: Centralize logs in **CloudTrail (AWS)** or **Azure Monitor**.
4. **Dependency Awareness**: Patch databases **before** dependent services.
5. **Vendor-Specific Tools**:
   - AWS: **SSM Patch Manager + Systems Manager**.
   - Azure: **Update Management + Azure Policy**.
   - GCP: **Operations Suite + Config Advisor**.

---
### **7. Troubleshooting**
| **Issue**                  | **Diagnosis**                                                                 | **Solution**                                      |
|----------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| Patches failing silently    | Check SSM logs (`/var/log/amazon/ssm/amazon-ssm-agent.log`).                | Increase `--log-level` in SSM Agent config.       |
| Reboot storms              | Multiple instances rebooting simultaneously caused by overlapping windows. | Use **exclusive maintenance windows**.           |
| Compliance drift           | Manually installed patches not detected.                                    | Enable **AWS Config Rules** for audit trails.     |

---
**References**:
- [AWS Patch Manager Docs](https://docs.aws.amazon.com/systems-manager/latest/userguide/patch-manager.html)
- [Azure Update Management](https://learn.microsoft.com/en-us/azure/automation/update-management/)
- [Terraform SSM Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_maintenance_window)