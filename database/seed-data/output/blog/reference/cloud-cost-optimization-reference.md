---
# **[Pattern] Cloud Cost Optimization – Reference Guide**

---

## **Overview**
The **Cloud Cost Optimization** pattern helps organizations minimize unnecessary cloud spend while maintaining operational efficiency. It focuses on identifying underutilized resources, rightsizing workloads, leveraging reserve purchasing (e.g., Savings Plans, Reserved Instances), and automating cost controls. By combining **financial controls**, **operational efficiency**, and **technical optimizations**, this pattern ensures cost savings without sacrificing performance or reliability.

This guide provides actionable steps, best practices, and reference schema for implementing cloud cost optimization, along with examples of cost-saving queries.

---

## **1. Key Concepts**
| **Term**                     | **Definition**                                                                                                                                                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Right-sizing**             | Adjusting resource capacity (CPU, memory, storage) to match actual workload demands, avoiding over-provisioning.                                                                                           |
| **Reserved Instances (RIs)** | Long-term commitments (1- or 3-year) for EC2, RDS, or other services, offering up to **72% discounts** compared to on-demand pricing.                                                           |
| **Savings Plans**            | Flexible commitments (1- or 3-year) that apply across AWS regions, services, or compute families, offering up to **72% savings** for sustained use.                                                     |
| **Spot Instances**           | Highly discounted (~90% off on-demand) EC2 capacity for fault-tolerant workloads.                                                                                                                      |
| **Tagging & Cost Allocation**| Assigning cost-tracking tags (e.g., `Department`, `Project`) to resources for granular billing transparency.                                                                                             |
| **Cost Anomaly Detection**   | Using AI/ML to flag unexpected cost spikes or inefficiencies (e.g., unused EBS volumes, idle Lambda functions).                                                                                       |
| **Cost Alerts**              | Automated notifications (e.g., AWS Budgets) when spending exceeds predefined thresholds.                                                                                                                   |
| **Multi-Cloud Optimization** | Comparing costs across providers (AWS, Azure, GCP) to switch workloads to the most cost-effective environment.                                                                                          |

---

## **2. Implementation Schema**
### **2.1 Core Cost Optimization Components**
| **Category**               | **Sub-Category**               | **Optimization Actions**                                                                                     | **Tools/Features**                          |
|----------------------------|---------------------------------|-------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Resource Efficiency**    | Right-sizing                    | Analyze CPU/memory utilization; adjust EC2/RDS instance types/sizes.                                         | AWS Compute Optimizer, RightScale          |
|                            | Spot & Savings Plans            | Replace on-demand workloads with Spot Instances or Savings Plans.                                           | AWS Savings Plans, Spot Fleet               |
|                            | Multi-Region Optimization       | Deploy workloads in regions with lower costs or use local data storage to reduce egress fees.                | AWS Global Accelerator                      |
| **Financial Controls**     | Budget Alerts                   | Set spending limits and receive alerts for anomalies.                                                       | AWS Budgets, Azure Cost Management          |
|                            | Tagging & Cost Allocation       | Apply consistent tags (e.g., `Owner`, `Environment`) for cost tracking.                                     | AWS Cost Explorer, Azure Cost Analysis      |
|                            | Reserved Instances              | Purchase RIs for predictable workloads (e.g., dev/test environments).                                       | AWS RI Purchase Guide                       |
| **Operational Efficiency** | Idle Resource Cleanup           | Automatically terminate unused EC2 instances, EBS volumes, or S3 buckets.                                  | AWS Lambda + Cost Explorer Triggers         |
|                            | Auto-Scaling                     | Scale resources up/down based on demand to avoid over-provisioning.                                         | AWS Auto Scaling, Azure App Service Scaling |
|                            | Serverless Optimization         | Use Lambda/DynamoDB for variable workloads instead of always-on servers.                                   | AWS Lambda Power Tuning                     |
| **Multi-Cloud Strategies** | Cost Comparison                 | Benchmark costs across clouds (e.g., AWS vs. Azure for Linux instances).                                     | CloudHealth by VMware, CloudCheckr         |
|                            | Workload Replacement            | Migrate cost-intensive workloads (e.g., Oracle DB → RDS PostgreSQL).                                         | AWS Database Migration Service              |

---

### **2.2 Data Flow Diagram**
```
[Cost Data Sources]
    │
    ▼
[Tagging & Cost Allocation] → [AWS Cost Explorer / Azure Cost Management]
    │
    ▼
[Anomaly Detection] → [Cost Alerts (e.g., AWS Budgets)]
    │
    ▼
[Optimization Engine]
    ├── [Right-sizing (Compute Optimizer)]
    ├── [Spot/Savings Plans Procurement]
    └── [Idle Resource Cleanup (Lambda)]
    │
    ▼
[Reporting & Dashboards] → [Stakeholders (Finance/DevOps)]
```

---

## **3. Query Examples**

### **3.1 AWS Cost Explorer Queries**
#### **Query 1: Identify Underutilized EC2 Instances**
```sql
-- Find EC2 instances with <30% CPU utilization over 30 days
SELECT
    instance_id,
    instance_type,
    AVG(CPU_Utilization) as avg_cpu_util
FROM
    cloudtrail_cpu_metrics
WHERE
    timestamp > ADD_DAYS(CURRENT_DATE, -30)
    AND CPU_Utilization < 30
GROUP BY
    instance_id, instance_type;
```

#### **Query 2: Save Potential with Savings Plans**
```sql
-- Estimate savings by converting on-demand usage to Savings Plans
SELECT
    service,
    SUM(Usage_Quantity) as on_demand_units,
    SUM(Usage_Quantity * UnitPrice) as current_cost,
    SUM(Usage_Quantity * UnitPrice * 0.3) as estimated_savings_plan_cost  -- ~70% discount
FROM
    cost_and_usage
WHERE
    usage_start_date > ADD_MONTHS(CURRENT_DATE, -6)
GROUP BY
    service;
```

#### **Query 3: Detect Unused EBS Volumes**
```sql
-- Find EBS volumes with no I/O for >90 days
SELECT
    volume_id,
    attachment_instance_id,
    MAX(created_time) as last_io_time
FROM
    ebs_iops_metrics
WHERE
    timestamp < ADD_DAYS(CURRENT_DATE, -90)
GROUP BY
    volume_id, attachment_instance_id;
```

---

### **3.2 Azure Cost Management Queries**
#### **Query 1: Top-Spending Services by Department**
```sql
-- Azure Cost Query for department-level breakdown
cost
| where TimeGenerated > ago(90d)
| where ResourceType == "Microsoft.Compute/virtualMachines"
| summarize TotalCost=sum(Cost) by Department, ResourceType
| order by TotalCost desc;
```

#### **Query 2: Idle Azure VMs (Last Boot Check)**
```sql
-- Find VMs not booted in >14 days
AzureMetrics
| where Name == "Percentage CPU" and MetricName == "Percentage CPU"
| where TimeGenerated > ago(14d)
| summarize avg(Percentage) by Computer, InstanceType
| where avg_Percentage == 0
| project Computer, InstanceType;
```

---

### **3.3 GCP Cost Analysis Queries**
#### **Query 1: Highest-Cost GKE Clusters**
```sql
-- Identify expensive GKE clusters by node type
SELECT
    cluster_name,
    node_type,
    SUM(cost) as total_cost
FROM
    `project-id/bigquery-public-data.google cloud_cost`
WHERE
    service = "container.googleapis.com"
    AND date > DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY
    cluster_name, node_type
ORDER BY
    total_cost DESC;
```

#### **Query 2: Unused GCP Persistent Disks**
```sql
-- Find disks with no I/O for >60 days
SELECT
    disk_name,
    size_gb,
    MAX(last_io_time) as last_activity
FROM
    `project-id.logs_cloud_operations`
WHERE
    operationType = "write"
    AND timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)
GROUP BY
    disk_name, size_gb;
```

---

## **4. Best Practices**
### **4.1 Right-sizing Workloads**
- **Use AWS Compute Optimizer** or **Azure Cost Analysis** to recommend instance types.
- **Baseline utilization**: Measure workload patterns for at least 1–2 weeks before resizing.
- **Right-size incrementally**: Adjust 1–2 resources at a time to avoid disruption.

### **4.2 Reserved Instances vs. Savings Plans**
| **Factor**               | **Reserved Instances**                          | **Savings Plans**                          |
|--------------------------|-------------------------------------------------|--------------------------------------------|
| **Flexibility**          | Region/tenancy/scope-specific                    | Cross-region, cross-service               |
| **Commitment Duration**  | 1- or 3-year                                    | 1- or 3-year                              |
| **Use Case**             | Predictable workloads (e.g., dev/test)          | Variable workloads (e.g., web apps)       |
| **Over-provision Risk**  | Higher (must commit to exact instance type)     | Lower (applies to compute usage)          |

- **Rule of thumb**: Use **Reserved Instances** for homogeneous workloads; **Savings Plans** for heterogeneous or unpredictable usage.

### **4.3 Spot Instances Strategy**
- **Best for**: Fault-tolerant, batch, or CI/CD workloads (e.g., ETL, ML training).
- **Mitigation strategies**:
  - Use **Spot Fleet** to auto-replace failed instances.
  - Pair with **checkpointing** for stateful applications.
- **Avoid**: Production databases or real-time APIs.

### **4.4 Tagging & Cost Allocation**
- **Standardize tags**:
  - `Owner`: Team/department (e.g., `marketing-team`).
  - `Environment`: `prod`, `dev`, `staging`.
  - `Project`: Cost-center identifier (e.g., `Q3-spring-refactor`).
- **Enforce tags**: Use **AWS Organizations SCPs** or **Azure Policy** to block untagged resources.
- **Aggregate costs**: Use **Cost Categories** (AWS) or **Cost Centers** (Azure) to roll up tags.

### **4.5 Automation**
- **Idle resource cleanup**: Schedule **AWS Lambda** functions to terminate unused EC2 instances (e.g., daily at 6 PM).
- **Auto-scaling policies**: Configure **AWS Application Auto Scaling** to scale Lambda functions based on invocations.
- **Cost alerts**: Set **AWS Budgets** or **Azure Cost Alerts** for:
  - Daily spend >110% of last month’s average.
  - Unusual spikes in a specific service (e.g., RDS storage growth).

### **4.6 Multi-Cloud Optimization**
- **Benchmark costs**: Use tools like **CloudHealth by VMware** to compare AWS vs. Azure/GCP pricing for equivalent workloads.
- **Leverage provider-specific savings**:
  - **AWS**: Savings Plans, RIs, and **Compute Savings Plans** (for EC2).
  - **Azure**: **Reserved VM Instances** and **Spot VMs**.
  - **GCP**: **Committed Use Discounts** and **Sustained Use Discounts**.
- **Data transfer costs**: Place workloads near data sources to minimize egress fees (e.g., deploy a Lambda in `us-west-2` if data is stored in `us-west-2` S3).

### **4.7 Continuous Monitoring**
- **Dashboards**: Set up **AWS Cost Explorer** or **Azure Cost Management** dashboards with:
  - Monthly spend trends.
  - Cost per service/resource type.
  - Anomaly detection (e.g., unexpected S3 storage growth).
- **Root cause analysis**: For cost spikes, investigate:
  - Newly launched resources (e.g., a misconfigured RDS instance).
  - Data transfer between regions.
  - Unused or over-provisioned storage (e.g., unoptimized EBS snapshots).

---

## **5. Schema Reference (Detailed)**
### **5.1 AWS Cost Optimization Schema**
| **Field**                  | **Description**                                                                                                                                                     | **Example Values**                     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| `CostCategory`             | Predefined or custom cost allocation tag (e.g., `Department`, `Project`).                                                                                          | `marketing`, `Q3-launch`                |
| `Service`                  | AWS service (e.g., EC2, S3, Lambda).                                                                                                                            | `AmazonEC2`, `S3`                      |
| `UsageType`                | Detailed breakdown of resource usage (e.g., `Compute:On-Demand:t3.medium`).                                                                                     | `Compute:Spot:c5.large`                |
| `LinkedInstanceId`         | EC2 instance ID or resource ARN for traceability.                                                                                                               | `i-1234567890abcdef0`                  |
| `InstanceType`             | EC2 instance family (e.g., `m5.large`).                                                                                                                       | `m5.xlarge`, `t3.micro`                |
| `CPUUtilization`           | Average CPU usage percentage over a period.                                                                                                                  | `15.2%`                                 |
| `SavingsPotential`         | Estimated savings by switching to Spot/Savings Plans or right-sizing.                                                                                          | `45%`                                   |
| `AnomalyScore`             | Risk score (0–100) for cost inefficiency (e.g., unused resources).                                                                                             | `82` (high risk)                       |
| `ReservedInstanceCoverage`| Percentage of usage covered by RIs/Savings Plans.                                                                                                              | `60%`                                   |

---

### **5.2 Azure Cost Optimization Schema**
| **Field**                  | **Description**                                                                                                                                                     | **Example Values**                     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| `ResourceGroup`            | Azure resource group containing the service.                                                                                                                     | `rg-marketing-website`                 |
| `ResourceType`             | Type of Azure resource (e.g., `VirtualMachine`, `StorageAccount`).                                                                                               | `Microsoft.Compute/virtualMachines`   |
| `UsageType`                | Specific usage category (e.g., `Compute:Reserved:VM:Standard_D4s_v3`).                                                                                           | `Compute:Spot:VM:Standard_D2s_v2`      |
| `VMSize`                   | Azure VM family (e.g., `Standard_D4s_v3`).                                                                                                                     | `Standard_B2s`, `D4s_v3`               |
| `CPUAllocation`            | Number of vCPUs allocated.                                                                                                                                        | `2`                                     |
| `MemoryAllocation`         | Memory in GB allocated.                                                                                                                                       | `16`                                    |
| `CostPerGBMonth`           | Cost per GB of storage/month.                                                                                                                              | `0.045`                                 |
| `CommittedUseDiscount`     | Percentage discount from Reserved VM Instances.                                                                                                               | `30%`                                   |
| `LastActivityTime`         | Timestamp of last usage (for idle detection).                                                                                                                 | `2023-10-01T02:15:00Z`                 |

---

### **5.3 GCP Cost Optimization Schema**
| **Field**                  | **Description**                                                                                                                                                     | **Example Values**                     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| `ProjectId`                | GCP project ID.                                                                                                                                             | `my-project-12345`                     |
| `Service`                  | GCP service (e.g., `compute.googleapis.com`, `storage.googleapis.com`).                                                                                          | `container.googleapis.com`             |
| `Zone`                     | Compute zone (e.g., `us-central1-a`).                                                                                                                       | `europe-west1-b`                       |
| `CostComponent`            | Breakdown of costs (e.g., `Compute Engine: Preemptible VM hours`).                                                                                           | `Compute Engine: Regional SSD persistent disk` |
| `InstanceType`             | VM or node type (e.g., `n1-standard-4`).                                                                                                                    | `e2-medium`                            |
| `SustainedUseDiscount`     | Automatic discount for long-term usage.                                                                                                                    | `30%`                                   |
| `CommittedUseDiscount`     | Discount from a **Committed Use Discount** (1- or 3-year).                                                                                                   | `50%`                                   |
| `LastIOTime`               | Timestamp of last I/O operation (for unused resource detection).                                                                                             | `2023-09-15T08:42:00+00:00`            |

---

## **6. Query Examples (Extended)**
### **6.1 AWS: Identify Over-Provisioned RDS Instances**
```sql
-- Find RDS instances with >50% reserved capacity unused
SELECT
    db_instance_identifier,
    allocated_storage_gb,
    (allocated_storage_gb - used_storage_gb) as unused_storage,
    ROUND((used_storage_gb / allocated_storage_gb) * 100, 2) as storage_utilization
FROM
    rds_metrics
WHERE
    storage_utilization < 50
    AND timestamp > ADD_DAYS(CURRENT_DATE, -7);
```

### **6.2 Azure: Cost Impact of Unused Blob Storage**
```sql
-- Calculate cost of unused Blob Storage (no access for >90 days)
BlobStorageUsage
| where LastAccessTime < ago(90d)
| summarize TotalSizeGB=sum(SizeGB), TotalCost=sum(Cost) by ContainerName
| order by TotalCost desc;
```

### **6.3 GCP: Detect Unused Cloud Functions**
```sql
-- Find inactive Cloud Functions (no invocations in >30 days)
SELECT
    function_name,
    last_invoke_time,
    invocations_per_day
FROM
    `project-id.cloudfunctions.googleapis.com`
WHERE
    last_invoke_time < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    AND invocations_per_day = 0
ORDER BY
    last_invoke_time;
```

---

## **7. Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **Use Case**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **[Right