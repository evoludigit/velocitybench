# **[Pattern] Cloud Setup Reference Guide**

---

## **Overview**
The **Cloud Setup** pattern defines a structured approach to configuring, deploying, and connecting cloud-based resources, services, and infrastructure. It ensures scalability, consistency, and security while minimizing manual intervention. This guide covers key concepts, implementation schema, query examples, and best practices for setting up cloud environments across major providers (AWS, Azure, GCP).

This pattern supports:
- **Infrastructure as Code (IaC)** (Terraform, CloudFormation, ARM/Bicep)
- **Resource provisioning** (VMs, databases, storage)
- **Network configurations** (VPCs, subnets, security groups)
- **Integration with CI/CD pipelines** (GitHub Actions, Azure DevOps)
- **Multi-cloud or hybrid deployments**

---

## **Schema Reference**
Below is a structured schema for defining cloud setups. This table represents core components and their relationships.

| **Component**               | **Description**                                                                                     | **Attributes (Key-Value)**                                                                                     | **Supported Providers**          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|-----------------------------------|
| **Environment**             | Logical grouping (e.g., dev, staging, prod)                                                        | `name: string`, `tags: array`, `region: string`, `billing_code: string`                                   | AWS, Azure, GCP                   |
| **Networking**              | Defines VPC/subnet configurations and security rules                                                | `cidr_block: string`, `subnets: array`, `security_groups: array`, `peering: boolean`                     | AWS, Azure, GCP                   |
| **Compute**                 | Virtual machines, containers, or serverless functions                                                 | `instance_type: string`, `image: string`, `autoscaling: boolean`, `user_data: string`                     | AWS, Azure, GCP                   |
| **Storage**                 | Block, object, or file storage solutions                                                             | `volume_size: number`, `backup_schedule: string`, `encryption: boolean`, `access_control: array`          | AWS, Azure, GCP                   |
| **Database**                | Managed databases (RDS, Cosmos DB, Cloud SQL)                                                       | `engine: string`, `instance_class: string`, `backup_retention: number`, `replication_region: string`       | AWS, Azure, GCP                   |
| **Security**                | IAM policies, roles, and encryption configurations                                                   | `role_name: string`, `policy_arn: string`, `kms_key: string`, `vpc_flow_logs: boolean`                     | AWS, Azure, GCP                   |
| **CI/CD Integration**       | Connects setup to deployment pipelines                                                            | `provider: string`, `repo_url: string`, `trigger: string`, `artifacts: array`                           | AWS CodePipeline, Azure DevOps    |
| **Monitoring**              | Logging, metrics, and alerting configurations                                                       | `cloudwatch_alarms: array`, `log_aggregation: string`, `synthetic_checks: boolean`                        | AWS, Azure, GCP                   |

---
### **Example Cloud Setup Schema (JSON)**
```json
{
  "environment": {
    "name": "prod-us-east-1",
    "tags": ["prod", "high-priority"],
    "region": "us-east-1",
    "billing_code": "DEV-001"
  },
  "networking": {
    "vpc": { "cidr_block": "10.0.0.0/16" },
    "subnets": [
      { "name": "public", "cidr": "10.0.1.0/24", "is_public": true },
      { "name": "private", "cidr": "10.0.2.0/24" }
    ],
    "security_groups": [
      { "name": "allow_http", "ports": [80] }
    ]
  },
  "compute": {
    "instance": {
      "type": "t3.medium",
      "image": "Ubuntu 22.04",
      "autoscaling": true,
      "min_instances": 2,
      "max_instances": 5
    }
  },
  "database": {
    "name": "app_db",
    "engine": "postgresql",
    "instance_class": "db.t3.small",
    "backup_retention": 7,
    "replication_region": "us-west-2"
  }
}
```

---

## **Implementation Details**

### **1. Key Concepts**
- **Infrastructure as Code (IaC):** Define cloud resources via code (e.g., Terraform modules, AWS CloudFormation).
- **Modularity:** Break setups into reusable components (e.g., VPC, DB, compute).
- **Immutability:** Treat deployments as immutable; replace rather than configure.
- **Tagging:** Use tags for cost tracking, access control, and environment differentiation.
- **Multi-Region Support:** Deploy critical services across regions for failover.

### **2. Supported Cloud Providers**
| **Provider** | **IaC Tools**               | **Key Services**                          |
|--------------|-----------------------------|-------------------------------------------|
| AWS          | Terraform, CloudFormation   | EC2, RDS, S3, Lambda, VPC                 |
| Azure        | Bicep, ARM, Terraform       | VMs, Cosmos DB, Azure Functions, VNet     |
| GCP          | Terraform, Deployment Manager| Compute Engine, Cloud SQL, GKE            |

### **3. Best Practices**
- **Security:**
  - Enforce least-privilege IAM roles.
  - Encrypt data at rest (KMS/Azure Key Vault/GCP KMS).
  - Use private subnets for databases.
- **Cost Optimization:**
  - Right-size instances (e.g., AWS Instance Scheduler).
  - Use spot instances for fault-tolerant workloads.
  - Enable auto-scaling based on metrics.
- **Disaster Recovery:**
  - Replicate databases across regions.
  - Use cross-region backups for critical data.
- **Observability:**
  - Centralize logs (CloudWatch, Azure Monitor, GCP Logging).
  - Set up alerts for failures or anomalies.

---

## **Query Examples**

### **1. Terraform (AWS Example)**
Create a VPC with public/private subnets:
```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "prod-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  tags = {
    Name = "public-subnet"
  }
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.2.0/24"
  tags = {
    Name = "private-subnet"
  }
}
```

### **2. Azure Bicep (Networking Example)**
Define a VNet and subnet:
```bicep
resource vnet 'Microsoft.Network/virtualNetworks@2022-05-01' = {
  name: 'prod-vnet'
  location: resourceGroup().location
  properties: {
    addressSpace: {
      addressPrefixes: [ '10.0.0.0/16' ]
    }
    subnets: [
      {
        name: 'public-subnet'
        properties: {
          addressPrefix: '10.0.1.0/24'
        }
      }
    ]
  }
}
```

### **3. GCP Terraform (Compute + Database)**
Deploy a VM and Cloud SQL instance:
```hcl
resource "google_compute_instance" "default" {
  name         = "web-server"
  machine_type = "e2-medium"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }
}

resource "google_sql_database_instance" "postgres" {
  name             = "app-db"
  database_version = "POSTGRES_14"
  region           = "us-central1"

  settings {
    tier = "db-f1-micro" # Free tier
  }
}
```

### **4. CI/CD Integration (GitHub Actions for AWS)**
Deploy Terraform on push to `main`:
```yaml
name: Deploy Cloud Setup
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.3.0
      - name: Terraform Apply
        run: terraform apply -auto-approve
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Multi-Region Deployment]** | Deploy resources across multiple cloud regions for high availability.                                | Critical applications requiring global redundancy.                                                 |
| **[Serverless Setup]**    | Define cloud functions (Lambda, Azure Functions, Cloud Run) with event-driven triggers.             | Event-driven workloads (e.g., APIs, data processing) with variable traffic.                         |
| **[Hybrid Cloud]**        | Combine on-premises infrastructure with cloud resources.                                            | Legacy systems needing gradual migration or compliance-sensitive workloads.                          |
| **[Cost Optimization]**   | Strategies to reduce cloud spending (reserved instances, spot markets, right-sizing).               | High-budget environments needing cost control.                                                      |
| **[Security Hardening]**  | Enforce security best practices (encryption, network segmentation, IAM policies).                    | Compliance-driven environments (e.g., HIPAA, GDPR).                                                |

---

## **Troubleshooting**
| **Issue**                          | **Solution**                                                                                       |
|-------------------------------------|---------------------------------------------------------------------------------------------------|
| **Terraform Plan Fails**           | Check for syntax errors; validate provider versions. Use `terraform validate`.                   |
| **VPC Subnet Overlap**              | Ensure CIDR blocks are non-overlapping. Use AWS VPC CIDR Calculator.                             |
| **Database Connection Errors**      | Verify security groups allow traffic; check IAM roles for DB access.                               |
| **CI/CD Pipeline Fails**           | Check secrets permissions; review Terraform state corruption.                                     |
| **High Cloud Costs**               | Use AWS Cost Explorer or Azure Cost Management to identify cost drivers. Enable cost alerts.      |

---

## **Glossary**
| **Term**               | **Definition**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **IaC**               | Infrastructure as Code: Managing cloud resources via version-controlled scripts.                  |
| **VPC**               | Virtual Private Cloud: Isolated network within a cloud provider.                                     |
| **Autoscaling**       | Automatically adjusts compute capacity based on demand.                                            |
| **KMS**               | Key Management Service: Encrypts data at rest.                                                      |
| **ARM Template**      | Azure Resource Manager template for declarative deployments.                                        |
| **Spot Instance**     | Discounted VMs available when capacity is unused (AWS/Azure).                                       |

---
**See Also:**
- [AWS Cloud Setup Best Practices](https://aws.amazon.com/architecture/)
- [Azure Well-Architected Framework](https://docs.microsoft.com/en-us/azure/architecture/framework/)
- [GCP Architecture Center](https://cloud.google.com/architecture)