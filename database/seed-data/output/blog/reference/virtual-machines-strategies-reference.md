# **[Pattern] Virtual Machines Strategies – Reference Guide**

## **Overview**
The **Virtual Machines (VMs) Strategies** pattern defines reusable strategies for managing virtual machine deployments, scaling, and lifecycle operations in cloud-native, hybrid, or on-premises environments. This pattern helps standardize VM provisioning, configuration, and orchestration while supporting auto-scaling, high availability (HA), and cost optimization. It integrates with infrastructure-as-code (IaC) tools (e.g., Terraform, Ansible) and cloud provider APIs (AWS EC2, Azure VMs, GCP Compute Engine).

Key use cases:
- **Auto-scaling VMs** based on load (e.g., CPU/memory thresholds).
- **Multi-region HA deployments** with distributed VMs.
- **Spot instance cost savings** via dynamic termination protection.
- **Blue-green or canary deployments** for zero-downtime updates.
- **Security hardening** with automated patching and role-based access (RBAC).

This guide covers implementation strategies (e.g., *Spot Instance*, *Reserved Instance*, *Auto-Scaling*), their trade-offs, and integration patterns.

---

## **1. Schema Reference**

| **Strategy**               | **Purpose**                                      | **Key Attributes**                                                                 | **Provider-Specific Notes**                                                                 |
|----------------------------|---------------------------------------------------|------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Reserved Instance (RI)** | Commit to 1–3 years for discounted VM pricing.   | - Term (1Y/3Y)<br>- Region/Zone<br>- Instance type<br>- Upfront/payment plan<br>- Cross-account sharing? | AWS: **Reserved Instances (RI)**, Azure: **Reserved VM Instances (RVM)**, GCP: **Committed Use Discounts (CUD)** |
| **Spot Instance**          | Leverage unused capacity for >90% cost savings.  | - Max bid price (e.g., 60% of on-demand)<br>- Interruption handling (e.g., checkpoint)<br>- Spot fleet vs. single instance | AWS: **Spot Fleet**, Azure: **Spot VMs**, GCP: **Preemptible VMs** (shorter termination notice) |
| **Auto-Scaling (ASG)**     | Dynamically adjust VM count based on metrics.    | - Min/max instances<br>- Scaling policies (CPU > 70%)<br>- Cooldown periods<br>- Health checks | AWS: **Auto Scaling Group (ASG)**, Azure: **Scaled Sets**, GCP: **Managed Instance Groups (MIG)** |
| **Multi-Zone HA**          | Distribute VMs across zones for fault tolerance. | - Zone affinity rules<br>- Load balancer integration<br>- Cross-zone replication | AWS: **Multi-AZ ASG**, Azure: **Availability Zones (AZ)**, GCP: **Multi-Zonal MIG**            |
| **Blue-Green Deploy**      | Zero-downtime VM swapping for updates.            | - Traffic splitting (e.g., 20% to new VMs)<br>- Rollback trigger (health checks)<br>- Snapshot sync | Tools: **Terraform (workspaces)**, **Ansible (dynamic groups)**, **Kubernetes (Deployments)** |
| **Serverless VMs**         | Pay-per-use VMs with auto-shutdown.               | - Shutdown timer (e.g., 8 PM – 6 AM)<br>- Cold start mitigation<br>- Cost alerts | AWS: **EC2 Auto Scaling + Lambda for triggers**, Azure: **Azure Functions + VM Scale Sets** |
| **Patch & Compliance**     | Automate OS/security updates across VMs.         | - Patch baselines (e.g., Windows Server 2022)<br>- Approval workflows<br>- Rollback window | AWS: **SSM Patch Manager**, Azure: **Update Management**, GCP: **Config Connector**         |
| **Cold Storage VMs**       | Pause VMs when idle (e.g., dev/test environments).| - Checkpoint/restore time<br>- Network-attached storage (NAS) dependency<br>- User permissions | AWS: **EC2 Hibernation**, Azure: **VM Scale Sets (hibernation)**, GCP: **No native hibernation** |

---

## **2. Implementation Details**

### **2.1 Core Strategies**
#### **A. Reserved Instances (RI)**
- **When to Use**: Predictable workloads (e.g., production databases) where long-term savings justify upfront cost.
- **Trade-offs**:
  - **Pros**: Up to **72% discount** vs. on-demand; no upfront cost with "No Upfront" plans.
  - **Cons**: **Commitment period** (1–3 years); rigid instance type/region selection.
- **Best Practices**:
  - Use **AWS RI Portfolio** or **Azure RVM Marketplace** to buy/sell unused RIs.
  - Combine with **Spot Instances** for hybrid savings (e.g., 30% of workload on Spot).
  - Monitor usage with **AWS Cost Explorer** or **Azure Cost Management**.

#### **B. Spot Instances**
- **When to Use**: Fault-tolerant workloads (e.g., batch processing, CI/CD, ML training).
- **Trade-offs**:
  - **Pros**: Up to **90% cost savings**; scalable to millions of instances.
  - **Cons**: **Instant termination** (2-minute notice); requires checkpointing.
- **Implementation**:
  - **AWS Spot Fleet**: Mix of on-demand + Spot instances with custom bid strategies.
  - **GCP Preemptible VMs**: Shorter (0–24h) notice period; ideal for short jobs.
  - **Checkpointing**: Use **AWS EBS Snapshots** or **Azure VM Backups** to restore state.
  - **Fallback Strategy**: Auto-replace failed Spot VMs with on-demand (e.g., via CloudWatch alarms).

#### **C. Auto-Scaling Groups (ASG)**
- **When to Use**: Variable workloads (e.g., web servers, microservices) needing dynamic scaling.
- **Key Policies**:
  | **Policy Type**       | **Use Case**                          | **Example Rule**                          |
  |-----------------------|---------------------------------------|-------------------------------------------|
  | **Target Tracking**   | Scale based on a metric (e.g., CPU).  | `Desired CPU < 60% → Scale Out`           |
  | **Scheduled Actions** | Predictable traffic (e.g., weekends). | `Scale to 200 VMs every Friday 9 AM`      |
  | **Predictive Scaling**| ML-driven scaling (AWS only).         | Adjusts for future demand patterns.       |
- **Best Practices**:
  - **Warm Pools**: Pre-warm VMs to reduce cold starts (set `MinSize > 0`).
  - **Cooldown Periods**: Avoid rapid scaling (default: 5 mins for ASG).
  - **Health Checks**: Use **EC2 Status Checks** or **Enhanced Monitoring**.

#### **D. Multi-Zone High Availability**
- **When to Use**: Critical workloads requiring **99.99% uptime** (e.g., databases, APIs).
- **Implementation**:
  - **AWS**: Deploy ASG across **3 AZs** with **Elastic Load Balancer (ELB)**.
  - **Azure**: Use **Availability Zones (AZ)** + **Azure Traffic Manager**.
  - **GCP**: Configure **Multi-Zonal MIG** with **Global Load Balancer**.
- **Failure Scenarios**:
  - **Zone Outage**: ASG replaces failed VMs in another AZ.
  - **Region Outage**: Use **cross-region replication** (e.g., RDS Global Database).

#### **E. Blue-Green Deployment**
- **When to Use**: Risky updates (e.g., database schema changes) with zero downtime.
- **Steps**:
  1. Deploy **new VMs** (e.g., `app-v2`) in a separate ASG.
  2. Gradually **route traffic** (e.g., 10% → 90%) to the new VMs.
  3. **Monitor health** (e.g., CloudWatch custom metrics).
  4. **Failover**: Roll back if errors exceed threshold (e.g., 5xx errors > 1%).
- **Tools**:
  - **Terraform**: Use `workspaces` or `module` for parallel environments.
  - **Ansible**: Dynamic inventory groups (`app-v1`, `app-v2`).
  - **Kubernetes**: Deployments with `rollingUpdate` strategy.

#### **F. Serverless VMs (Hybrid Approach)**
- **When to Use**: Cost-sensitive dev/test environments with sporadic usage.
- **Implementation**:
  - **AWS**: Combine **EC2 Auto Scaling** with **Lambda triggers** (e.g., shut down at 8 PM).
  - **Azure**: Use **VM Scale Sets** + **Logic Apps** for automation.
- **Example Workflow**:
  ```plaintext
  1. User requests VM → Lambda triggers ASG to scale to 1.
  2. VM boots in <60s (pre-warmed if needed).
  3. Job completes → Lambda scales ASG to 0 (shuts down after 1h idle).
  ```

#### **G. Patch & Compliance Automation**
- **When to Use**: Regulated environments (e.g., HIPAA, GDPR) requiring OS updates.
- **Tools**:
  - **AWS SSM Patch Manager**: Automate patching for Windows/Linux.
  - **Azure Update Management**: Patch **VMs, containers, and servers**.
  - **GCP Config Connector**: Enforce compliance with **config rules**.
- **Best Practices**:
  - **Test in Staging**: Run patch jobs in a non-production ASG first.
  - **Rollback Window**: Set **30-min window** for failed patches.
  - **Audit Logs**: Track patches with **AWS CloudTrail** or **Azure Monitor**.

---

## **3. Query Examples**
### **3.1 AWS CLI/SDK Queries**
| **Use Case**                          | **AWS CLI Command**                                                                 |
|----------------------------------------|------------------------------------------------------------------------------------|
| List Reserved Instances               | `aws ec2 describe-reserved-instances`                                              |
| Check Spot Instance interrupt notices | `aws ec2 describe-spot-instance-Requests`                                         |
| ASG scaling activity                  | `aws autoscaling describe-scaling-activities --auto-scaling-group-name my-asg`     |
| Multi-AZ VM health                    | `aws ec2 describe-instance-status --instance-ids i-1234567890abcdef0`              |
| Patch compliance status               | `aws ssmmessages list-compliance-summary-for-patch-baseline --baseline-id X`       |

### **3.2 Azure PowerShell Queries**
| **Use Case**                          | **Azure PowerShell Command**                                                        |
|----------------------------------------|------------------------------------------------------------------------------------|
| List Reserved VMs                     | `Get-AzReservedVMInstance`                                                         |
| Spot VM termination history           | `Get-AzVMInstanceView -VMName "my-vm" -InstanceViewType "InstanceView"`           |
| Scale Set activity logs                | `Get-AzScaleSetVM -ResourceGroupName "rg1" -Name "my-scale-set" -Status`          |
| Update Management compliance          | `Get-AzVM -ResourceGroupName "rg1" -Name "vm1" | Get-AzVMAssessmentResult`                  |

### **3.3 GCP Command-Line Tool (gcloud)**
| **Use Case**                          | **gcloud Command**                                                                 |
|----------------------------------------|------------------------------------------------------------------------------------|
| List Preemptible VMs                  | `gcloud compute instances list --filter="status=TERMINATED" --format="table(name)"` |
| Check zone health                     | `gcloud compute zones list --filter="status=UP"`                                  |
| MIG scaling activity                  | `gcloud compute instance-groups managed get-health my-mig --zone us-central1-a`   |
| Config Connector compliance rules      | `gcloud alpha config compliance rules list`                                        |

---

## **4. Related Patterns**
| **Pattern Name**               | **Description**                                                                 | **Integration with VMs**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **[Infrastructure as Code (IaC)]** | Define VMs declaratively (Terraform, Pulumi, Ansible).                          | Use `aws_autoscaling_group`, `azurerm_virtual_machine_scale_set` in Terraform.            |
| **[Serverless Containers]**       | Run VM workloads as containers (e.g., Kubernetes on VMs).                       | Deploy **GKE Autopilot** or **EKS on EC2** for hybrid workloads.                          |
| **[Cost Optimization]**          | Right-size VMs and optimize spending.                                           | Pair with **AWS Compute Optimizer** or **Azure Cost Management**.                         |
| **[Multi-Cloud Orchestration]**   | Manage VMs across AWS, Azure, and GCP.                                           | Use **Terraform Cloud** or **Crossplane** for unified provisioning.                      |
| **[Security Hardening]**          | Apply security best practices to VMs.                                             | Integrate **AWS Inspector**, **Azure Defender for VMs**, or **GCP Security Command Center**. |
| **[Disaster Recovery (DR)]**      | Protect VMs from regional outages.                                              | Implement **AWS DMS** (database replication) + **ASG cross-region deployment**.           |

---

## **5. Best Practices Checklist**
1. **Cost Optimization**:
   - [ ] Use **Reserved Instances** for predictable workloads.
   - [ ] Enable **Spot Instances** for fault-tolerant jobs.
   - [ ] Right-size VMs with **AWS Compute Optimizer** or **Azure Advisor**.

2. **High Availability**:
   - [ ] Deploy **ASGs across 3 AZs** in each region.
   - [ ] Use **multi-region load balancers** (e.g., AWS Global Accelerator).
   - [ ] Test **chaos engineering** (e.g., kill a VM to verify failover).

3. **Operational Efficiency**:
   - [ ] Automate patching with **SSM Patch Manager** or **Azure Update Mgmt**.
   - [ ] Set up **cloudwatch alarms** for VM health/metrics.
   - [ ] Use **Terraform** or **Ansible** for drift detection.

4. **Security**:
   - [ ] Restrict **IAM roles** to least privilege (e.g., `AmazonSSMManagedInstanceCore`).
   - [ ] Enable **EC2 Instance Connect** or **Azure Bastion** for secure RDP/SSH.
   - [ ] Encrypt **EBS volumes** (AWS) or **managed disks** (Azure).

5. **Performance**:
   - [ ] Use **Nitro-enabled VMs** (AWS) or **Azure Hyperscale** for high throughput.
   - [ ] Enable **enhanced monitoring** for ASGs.
   - [ ] Cache frequently accessed data (e.g., **ElastiCache** for VM-backed apps).

---
**See Also**:
- [AWS Auto Scaling Documentation](https://docs.aws.amazon.com/autoscaling/)
- [Azure Virtual Machine Scale Sets](https://docs.microsoft.com/en-us/azure/virtual-machine-scale-sets/)
- [GCP Managed Instance Groups](https://cloud.google.com/compute/docs/instance-groups)