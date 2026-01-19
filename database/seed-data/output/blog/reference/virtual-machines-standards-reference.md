**[Pattern] Virtual-Machines Standards Reference Guide**

---

### **Overview**
The **Virtual-Machines Standards** pattern defines consistent design principles, configurations, and naming conventions for virtual machine (VM) deployments across an organization. This ensures interoperability, simplifies management, and reduces operational overhead by enforcing standardized VM templates, resource allocation, and lifecycle processes. It applies to cloud VMs (AWS, Azure, GCP), on-premises hypervisors (VMware, Hyper-V), and containerized deployments (Kubernetes VMs).

Key benefits:
- **Portability**: VMs adhere to uniform specifications, easing migration between environments.
- **Scalability**: Predictable resource allocation simplifies scaling workloads.
- **Cost Control**: Standardized templates reduce wasteful over-provisioning.
- **Compliance**: Built-in guardrails align with security and governance policies.

This guide covers foundational concepts, schema requirements, query patterns, and integration points with other infrastructure standards.

---

### **Schema Reference**
Below are core components of the **Virtual-Machines Standards** pattern, structured as a schema for implementation.

| **Component**               | **Description**                                                                 | **Attributes**                                                                                     | **Example Value**                     |
|------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|---------------------------------------|
| **VM Template**              | Pre-configured VM blueprint with OS, software, and security settings.         | - `template_name` (string) <br>- `os_type` (enum: Ubuntu, CentOS, Windows) <br>- `cpu_cores` (int) <br>- `ram_gb` (float) <br>- `disk_gb` (int) <br>- `security_groups` (array) <br>- `compliance_level` (enum: Basic, Strict) | `{"template_name": "web-server-2023", "os_type": "Ubuntu", "cpu_cores": 4, "ram_gb": 8.0}` |
| **VM Lifecycle States**      | Standardized stages of VM lifecycle (creation, scaling, termination).           | - `state` (enum: pending, running, scaling, terminating) <br>- `transition_time` (timestamp)   | `{"state": "scaling", "transition_time": "2024-05-15T10:00:00Z"}` |
| **Resource Allocation Rules** | Policies governing CPU, RAM, and storage allocation based on workload.         | - `rule_name` (string) <br>- `workload_type` (enum: dev, prod, batch) <br>- `min_cpu` (int) <br>- `max_cpu` (int) <br>- `auto_scale` (bool) | `{"rule_name": "dev-tier", "min_cpu": 2, "max_cpu": 8, "auto_scale": true}` |
| **Naming Convention**        | Structured naming rules for VMs (environment + role + region + unique ID).   | - `environment` (enum: dev, staging, prod) <br>- `role` (string) <br>- `region` (string) <br>- `instance_id` (string) | `prod-web-app-us-east-1a-xyz123`      |
| **Security Baseline**        | Mandatory security configurations enforced at VM creation.                    | - `patching_schedule` (enum: weekly, daily) <br>- `encryption_enabled` (bool) <br>- `firewall_rules` (array) | `{"patching_schedule": "weekly", "firewall_rules": [{"port": 80, "protocol": "tcp"}]}` |
| **Backup Policy**            | Rules for automated VM backups (frequency, retention, storage).                 | - `backup_frequency` (enum: hourly, daily, weekly) <br>- `retention_days` (int) <br>- `storage_type` (enum: S3, NAS) | `{"backup_frequency": "daily", "retention_days": 30, "storage_type": "S3"}` |

---
**Notes:**
- **Dynamic Attributes**: Some fields (e.g., `security_groups`, `firewall_rules`) may expand based on cloud provider or use case.
- **Versioning**: Schema updates should follow [semantic versioning](https://semver.org/) to avoid breaking changes.
- **Validation**: Use tools like **OpenAPI/Swagger** or **Terraform validation** to enforce schema compliance.

---

### **Query Examples**
Below are common queries for managing VM standards, formatted for **SQL-like** (e.g., Terraform, AWS CloudTrail) and **REST API** contexts.

#### **1. List VMs in Compliance with Standards**
**Query (SQL-like):**
```sql
SELECT *
FROM virtual_machines
WHERE (
    template_name IN (SELECT template_name FROM vm_templates WHERE compliance_level = 'Strict')
    AND resource_allocation.rules.matching_rule_name = 'prod-tier'
);
```

**REST API Example (AWS CLI):**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Compliance,Values=Strict" \
  --query 'Reservations[*].Instances[*].[InstanceId, State.Name]'
```

#### **2. Validate VM Naming Convention**
**Query (Regex Check):**
```sql
SELECT
  instance_id,
  CASE
    WHEN vm_name !~ '^[a-z]{3}-[a-z]+-[a-z]{3}-[a-z0-9]{6}$' THEN 'Invalid'
    ELSE 'Valid'
  END AS compliance_status
FROM virtual_machines;
```

**Python Function (Example):**
```python
import re

def validate_naming(vm_name: str) -> bool:
    pattern = r"^[a-z]{3}-[a-z]+-[a-z]{3}-[a-z0-9]{6}$"
    return bool(re.match(pattern, vm_name))
```

#### **3. Enforce Auto-Scaling Rules**
**Query (Check Active VMs Against Rules):**
```sql
SELECT
  vm_id,
  (SELECT max_cpu FROM resource_allocation_rules WHERE workload_type = 'prod') AS max_cpus_allowed
FROM virtual_machines
WHERE cpu_cores > (SELECT max_cpu FROM resource_allocation_rules WHERE workload_type = 'prod');
```

**Terraform Validation (HCL):**
```hcl
resource "aws_autoscaling_policy" "prod_cpu_limit" {
  policy_name = "prod-cpu-max-8"
  scaling_adjustment = -100
  adjustment_type     = "ChangeInCapacity"
  cooldown            = 3600

  # Enforce max CPU of 8 for prod workloads
  condition {
    alarm_name = "prod-cpu-high"
  }
}
```

#### **4. Audit VM Security Baselines**
**Query (Check Encryption Status):**
```sql
SELECT
  vm_name,
  CASE
    WHEN encryption_enabled = false THEN '❌ Non-Compliant'
    ELSE '✅ Compliant'
  END AS security_status
FROM virtual_machines;
```

**AWS Config Rule Example:**
```json
{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Deny",
    "Action": "ec2:RunInstances",
    "Resource": "*",
    "Condition": {
      "BoolIfExists": {
        "encryption-enabled": false
      }
    }
  }
}
```

---

### **Related Patterns**
To complement **Virtual-Machines Standards**, integrate with the following patterns:

1. **[Infrastructure as Code (IaC) Standards](https://docs.example.org/iac-standards)**
   - Use Terraform/Pulumi to enforce VM templates as code.
   - Example: Define VM modules with configurable variables for CPU/RAM.

2. **[Observability Standards](https://docs.example.org/observability-standards)**
   - Deploy consistent monitoring (Prometheus, CloudWatch) for all VMs.
   - Mandate metrics like CPU utilization, disk I/O, and network latency.

3. **[Security Standards](https://docs.example.org/security-standards)**
   - Enforce least-privilege roles (IAM, OS users) and regular vulnerability scans.
   - Example: Integrate **AWS Inspector** or **OpenSCAP** for compliance checks.

4. **[Cost Optimization Standards](https://docs.example.org/cost-standards)**
   - Right-size VMs using tools like **AWS Compute Optimizer** or **Kubernetes Horizontal Pod Autoscaler**.
   - Example: Schedule non-prod VMs to terminate after business hours.

5. **[Multi-Cloud VM Standards](https://docs.example.org/multi-cloud-vm)**
   - Extend standards to Azure/Kubernetes (e.g., `aks_node_pools`) with provider-specific adjustments.

---
### **Implementation Checklist**
| **Task**                          | **Tool/Action**                                  | **Owner**       |
|------------------------------------|--------------------------------------------------|-----------------|
| Define VM templates                | Terraform/CloudFormation                         | DevOps/Cloud    |
| Enforce naming conventions         | CI/CD pipeline (e.g., GitHub Actions)            | DevOps          |
| Set up auto-scaling                | AWS Auto Scaling / Kubernetes HPA                 | SRE             |
| Implement backup policies          | AWS Backup / Velero (Kubernetes)                 | Data Engineering|
| Validate security baselines       | AWS Config / Open Policy Agent                   | Security        |
| Document exceptions                | Confluence/Jira issue tracker                   | Compliance      |

---
### **Troubleshooting**
| **Issue**                          | **Root Cause**                                  | **Solution**                                    |
|-------------------------------------|------------------------------------------------|------------------------------------------------|
| VM fails to launch due to CPU limits| Resource allocation rule misconfigured.        | Verify `max_cpu` in `resource_allocation_rules`. |
| Naming convention violations       | Ad-hoc VM deployments bypassing standards.     | Enforce IaC for all VM provisions.              |
| Backup failures                     | Incorrect `storage_type` or `retention_days`.  | Test backup policies with `aws backup test-start`.|

---
### **References**
- **[AWS Well-Architected VM Best Practices](https://aws.amazon.com/architecture/well-architected/)**
- **[CNCF Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)**
- **[OpenStack VM Lifecycle](https://docs.openstack.org/)**