# **[Pattern] Virtual-Machines Guidelines – Reference Guide**

---

## **Overview**
This reference guide outlines best practices, implementation details, and operational requirements for managing **Virtual Machines (VMs)** within cloud, hybrid, or on-premises environments. The guidelines ensure **performance, security, cost efficiency, scalability, and compliance** while adhering to enterprise-grade architectures. This document applies to **administrators, developers, and DevOps teams** responsible for VM provisioning, configuration, and lifecycle management.

---

## **Key Concepts & Implementation Details**
### **1. VM Lifecycle Phases**
| Phase          | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| **Provisioning** | Deploying VMs via **Infrastructure-as-Code (IaC)** (e.g., Terraform, Ansible, ARM templates) or manual deployment tools. |
| **Configuration** | Hardening, patching, and role-based setup (e.g., web servers, databases). |
| **Operation**   | Monitoring, scaling, and troubleshooting during runtime.                   |
| **Maintenance** | Patching, backups, and optimization (e.g., right-sizing, snapshot management). |
| **Decommissioning** | Secure deletion, data archival, or migration (avoid orphaned resources).   |

### **2. Performance & Scalability Guidelines**
| Guideline               | Action Items                                                                 |
|-------------------------|------------------------------------------------------------------------------|
| **CPU/Memory Allocation** | Allocate resources based on workload (e.g., **burstable instances** for dev/test, **high-memory** for databases). |
| **Storage Tiering**     | Use **SSD (ephemeral/local)** for high I/O workloads; **HDD (persistent)** for cost-sensitive workloads. |
| **Auto-Scaling**        | Enable **Horizontal Pod Autoscaler (HPA)** for stateless apps; **Vertical Scaling** for stateful services. |
| **Network Optimization** | Use **subnet isolation**, **VPC peering**, and **low-latency egress** for global workloads. |

### **3. Security Hardening**
| Control Area          | Recommended Practices                                                                 |
|-----------------------|--------------------------------------------------------------------------------------|
| **Identity & Access** | Enforce **role-based access (IAM roles/policies)**, **MFA**, and **least-privilege** principles. |
| **Network Security**  | Deploy **firewall rules**, **Network Security Groups (NSG)**, and **private subnets**.   |
| **Data Protection**   | Encrypt disks (**BitLocker/AES-256**), secrets (**Vault/Key Management Service**), and backups. |
| **Patch Management**  | Use **automated patching** (e.g., Windows Server Update Services, Linux `apt-get`). |
| **Isolation**         | Run VMs on **dedicated hosts** for sensitive workloads (e.g., financial systems).   |

### **4. Cost Optimization**
| Strategy               | Implementation                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Right-Sizing**       | Use **CloudWatch/VM Insights** to monitor CPU/memory usage; resize underutilized VMs. |
| **Spot Instances**     | Leverage **spot VMs** for fault-tolerant workloads (e.g., batch processing).   |
| **Reserved Instances** | Commit to **1- or 3-year RIs** for steady-state workloads (up to **72% discount**). |
| **Shutdown Schedules** | Automate **non-production VM shutdowns** during off-hours (e.g., weekends).    |

### **5. Backup & Disaster Recovery (DR)**
| Requirement            | Solution                                                                       |
|------------------------|-------------------------------------------------------------------------------|
| **Backup Frequency**   | **Daily snapshots** for critical VMs; **hourly incremental backups** for databases. |
| **Backup Storage**     | Use **cross-region replication** for DR; **immutable backups** (WORM) for compliance. |
| **RTO/RPO**            | Define **Recovery Time Objective (RTO ≤ 15 min)** and **Recovery Point Objective (RPO ≤ 5 min)**. |
| **Test Restores**      | Simulate **failover drills** quarterly to validate backup integrity.           |

### **6. Compliance & Governance**
| Standard               | Guideline                                                                     |
|------------------------|-------------------------------------------------------------------------------|
| **GDPR/HIPAA**         | Anonymize PII, encrypt data at rest/transit, and maintain audit logs.          |
| **SOC 2 Type II**      | Implement **VM inventory tracking**, **change logging**, and **access reviews**. |
| **CIS Benchmarks**     | Apply **CIS hardening guides** for OS configurations (e.g., disable unused ports). |
| **Tagging**            | Tag VMs with **owner, environment, purpose, and cost center** for tracking.   |

---

## **Schema Reference**
Below is a structured reference for VM configuration attributes. Use this as a **validation checklist** during deployment.

| **Category**          | **Attribute**               | **Description**                                                                 | **Required?** | **Example Values**                          |
|-----------------------|-----------------------------|---------------------------------------------------------------------------------|---------------|---------------------------------------------|
| **Basic VM Setup**    | `VM_Name`                   | Unique identifier for the VM.                                                  | ✅             | `app-prod-web-01`                          |
|                       | `VM_Type`                   | Instance family (e.g., **t3.medium**, **r5.xlarge**).                          | ✅             | `m5.large`                                   |
|                       | `OS_Type`                   | Operating system (Linux/Windows + version).                                    | ✅             | `Ubuntu 22.04 LTS`, `Windows Server 2022`   |
|                       | `Subnet`                    | VPC subnet with appropriate tier (public/private).                             | ✅             | `subnet-1234567890abcdef0`                  |
|                       | `AvailabilityZone`          | High-availability preference (e.g., `us-east-1a`).                              | ⚠️ (Multi-AZ recommended) | `us-east-1a`          |
| **Networking**        | `SecurityGroups`            | List of allowed inbound/outbound rules (e.g., `sg-0123456789abcdef0`).      | ✅             | `[sg-web-tier, sg-db-tier]`                 |
|                       | `ElasticIP`                 | Static public IP assignment (if exposed to internet).                          | ⚠️ (Avoid if possible) | `eipalloc-1234567890`                     |
|                       | `NATGateway`                | Required for private subnet VMs to access the internet.                        | ✅ (if private) | `nat-0123456789abcdef0`                     |
| **Storage**           | `RootVolume`                | EBS volume type/size (e.g., **gp3 50GiB**).                                   | ✅             | `gp3, 100GiB, io1 (1000 IOPS)`              |
|                       | `DataVolumes`               | Additional disks (e.g., **EBS, EFS, or local NVMe**).                          | ⚠️ (Optional) | `[/dev/sdb: 200GiB gp3, /dev/sdc: 1TB gp2]` |
| **Monitoring**        | `CloudWatchAgent`           | Enable metrics/logs collection.                                                  | ✅             | `enabled`                                    |
|                       | `AlarmThresholds`           | CPU > 80% for 5 min → trigger notification.                                    | ⚠️ (Customize) | `CPUtilization > 80% for 5m`                |
| **Backup**            | `BackupSchedule`            | Frequent snapshots (e.g., **daily at 2 AM**).                                  | ✅             | `Daily, 02:00 UTC`                          |
|                       | `BackupRetention`           | Minimum 30 days for compliance.                                                | ✅             | `30d`                                        |
| **Tags**              | `Environment`               | **dev**, **staging**, **prod**.                                                 | ✅             | `prod`                                       |
|                       | `Owner`                     | Team/responsible engineer.                                                      | ✅             | `web-team@company.com`                       |
|                       | `CostCenter`                | Budget owner for financial tracking.                                             | ✅             | `CC-12345`                                   |

---

## **Query Examples**
Use these **CLI/API queries** to inspect VM configurations and troubleshoot issues.

### **1. List All VMs with Tags**
**AWS CLI:**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=prod" \
  --query "Reservations[*].Instances[*].[InstanceId, Tags[?Key=='Name']|[?Key=='Owner']|[0].Value]" \
  --output table
```

**Azure CLI:**
```bash
az vm list --query "[?tags.environment=='prod'].{Name:name, Owner:tags.owner}" --output table
```

### **2. Check VM CPU/Memory Usage**
**AWS (CloudWatch):**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time 2023-10-01T00:00:00Z \
  --end-time 2023-10-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

**Azure (Metrics API):**
```bash
az monitor metrics list \
  --resource-group myResourceGroup \
  --resource /subscriptions/xxxx/yyzz/vms/myVM \
  --metric "Percentage CPU" \
  --time-grain 01:00:00 \
  --start-time "2023-10-01T00:00:00Z" \
  --end-time "2023-10-02T00:00:00Z"
```

### **3. Verify Backups**
**AWS (EBSSnapshots):**
```bash
aws ebssnapshots describe-snapshots \
  --filters Name=volume-id,Values=vol-1234567890 \
  --query "Snapshots[?start-time > '$(date -d '30 days ago' +%Y-%m-%d)'].snapshot-id" \
  --output text
```

**Azure (Recovery Services):**
```bash
az backup protected-item list \
  --policy-name MyBackupPolicy \
  --resource-group myResourceGroup \
  --resource /subscriptions/xxxx/vms/myVM \
  --query "[?protectionState=='Protected']" \
  --output table
```

### **4. Find Orphaned VMs**
**AWS (Tag-based):**
```bash
aws ec2 describe-instances \
  --query "Reservations[*].Instances[?tags[?key=='Owner'].value=='unassigned']" \
  --output json > orphaned_vms.json
```

**Azure (Unused VMs):**
```bash
az vm list --query "[?tags.lastUsed=='2023-01-01']" --output json
```

---

## **Related Patterns**
Consult these complementary patterns for broader architectural guidance:

1. **[Infrastructure-as-Code (IaC)]**
   - Standardize VM provisioning with **Terraform**, **CloudFormation**, or **Pulumi**.
   - *Reference:* [IaC Best Practices Guide](link)

2. **[Containerization & VM Alternatives]**
   - Replace monolithic VMs with **Kubernetes (EKS/GKE/AKS)** for microservices.
   - *Reference:* [K8s VM Migration Checklist](link)

3. **[Hybrid Cloud VM Management]**
   - Sync VM configurations between **on-prem (Hyper-V/VirtualBox)** and cloud.
   - *Reference:* [Multi-Cloud VM Sync Tools](link)

4. **[Disaster Recovery (DR) Patterns]**
   - Implement **pilot light**, **warm standby**, or **multi-region failover**.
   - *Reference:* [DR Strategy Matrix](link)

5. **[Observability for VMs]**
   - Centralize logs/metrics with **Prometheus + Grafana** or **Azure Monitor**.
   - *Reference:* [VM Monitoring Stack](link)

---
**Last Updated:** `2023-10-15`
**Version:** `1.2` (Additions: Spot Instance section, Backup RTO/RPO guidance)