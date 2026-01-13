---
# **[Pattern] Deployment Standards Reference Guide**

## **Overview**
This guide outlines **Deployment Standards**, a pattern that establishes consistent rules, naming conventions, and best practices for deploying applications, infrastructure, and services. By enforcing standardized deployment practices, teams ensure reproducibility, scalability, and reliability across environments (development, staging, production). This pattern covers infrastructure-as-code (IaC) templates, containerization, versioning, and rollback procedures to minimize human error and support CI/CD pipelines.

Key benefits include:
- **Consistency** across deployments
- **Reduced outages** via automated validation
- **Easier troubleshooting** with documented standards
- **Scalability** through reusable, modular templates

---

## **Implementation Details**

### **Core Principles**
1. **Infinite Reproducibility** – Deployments must be repeatable without manual intervention.
2. **Environment Parity** – Staging/production should mirror real-world conditions (e.g., identical resource sizes, permissions).
3. **Minimal Change** – Deployments should only apply necessary updates (e.g., via rollback-capable state management).
4. **Observability** – Standardized logging, monitoring, and tracing for all environments.

### **Key Components**
| **Component**         | **Description**                                                                                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Infrastructure-as-Code (IaC)**       | Use tools like Terraform, CloudFormation, or Pulumi to define infrastructure in code. Store IaC templates in version control (e.g., Git).                          |
| **Containerization**      | Package applications in containers (Docker) with standardized images, tags, and entrypoints. Enforce image scanning for vulnerabilities.                       |
| **Versioning**           | Tag deployments with semantic versions (e.g., `git-commit-short-hash`, `build-metadata`) to track changes.                                                                   |
| **Environment Naming**    | Use clear naming conventions (e.g., `prod/myapp`, `staging/myapp-dev`). Avoid hardcoded environment names in code.                                                   |
| **Rollback Procedures**  | Define automated rollback triggers (e.g., health checks, failure thresholds) and stored rollback snapshots.                                                           |
| **Access Control**       | Apply least-privilege principles in IaC (e.g., IAM roles, Kubernetes RBAC) and audit deployment permissions.                                         |
| **Documentation**        | Include deployment playbooks, approval workflows, and runbooks in a central knowledge base (e.g., Confluence, Notion).                                       |

---

## **Schema Reference**

### **1. IaC Template Schema (Terraform Example)**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region          # Standardized region (e.g., "us-east-1")
  profile    = "deployer"              # Dedicated IAM profile for deployments
}

resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type     # Enforced via variable set
  tags = {
    Environment = var.environment       # "dev", "staging", "prod"
    ManagedBy   = "Terraform"          # Audit trail
    Owner       = "my-team"             # Accountability
  }
}

variable "environment" {
  description = "Deployment environment (required)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be one of: dev, staging, prod."
  }
}
```

### **2. Docker Image Tagging Standard**
| **Tag**               | **Purpose**                                                                                     | **Example**                          |
|-----------------------|-------------------------------------------------------------------------------------------------|--------------------------------------|
| **Build Hash**        | Uniquely identifies a build (from CI pipeline).                                                | `myapp:v1.2.3-abc123`                |
| **Version Tag**       | Semantic version (linked to Git tags).                                                          | `myapp:1.2.3`                        |
| **Latest**            | Points to the most stable version (avoid overuse).                                             | `myapp:latest` (deprecated in prod)  |
| **Pre-release**       | Unstable builds (e.g., `dev`, `staging`).                                                      | `myapp:1.2.3-dev`                    |
| **Rollback Tag**      | Version used for rollback (stored in artifact registry).                                       | `myapp:rollback-20240515`            |

### **3. Environment Naming Conventions**
| **Environment** | **Prefix**       | **Suffix (if applicable)** | **Example**                |
|-----------------|------------------|----------------------------|----------------------------|
| Development     | `dev`            | `-{team}`                   | `dev/auth-service`         |
| Staging         | `staging`        | `-{env}` or `-{stage}`     | `staging/prod-like`        |
| Production      | `prod`           | `-{region}` or `-{account}` | `prod/us-west-2`           |
| Canary           | `canary`         | `-{percentage}-{commit}`   | `canary/5%-abc123`         |

---

## **Query Examples**

### **1. IaC Configuration Validation (Terraform)**
```bash
# Dry-run to validate changes without applying
terraform plan -out=tfplan -var="environment=staging"
terraform show -json tfplan | jq '.planned_values.root_module.resources[] | select(.type == "aws_instance")'
```
**Output:**
```json
{
  "address": "i-0123456789abcdef0",
  "type": "aws_instance",
  "name": "app_server",
  "tags": {
    "Environment": "staging",
    "ManagedBy": "Terraform"
  }
}
```

### **2. Docker Image Inspection**
```bash
# List all tags for a specific image
docker inspect --format='{{json .RepoDigests}}' myapp:latest

# Verify vulnerable packages in an image
docker scan myapp:v1.2.3-abc123
```
**Expected Output:**
```
myapp@sha256:1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3
Vulnerabilities: 0 critical, 2 high-priority
```

### **3. Rollback Simulation (Kubernetes)**
```yaml
# Rollback to a previous deployment in Kubernetes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  revisionHistoryLimit: 5
---
apiVersion: apps/v1
kind: Rollback
metadata:
  name: myapp-rollback
spec:
  targetRevision: "2"  # Second deployment in revision history
```
**Verify Rollback:**
```bash
kubectl rollout history deployment/myapp --revision=2
kubectl get pods -w  # Watch for rollback completion
```

### **4. Environment Access Check**
```bash
# Validate IAM permissions for a deployment profile
aws sts get-caller-identity --profile deployer
aws iam list-attached-user-policies --user-name deployer
```
**Expected Output:**
```
UserId: AIDASAMPLEUSER
Account: 123456789012
Arn: arn:aws:iam::123456789012:user/deployer
```

---

## **Related Patterns**

1. **[Infrastructure as Code (IaC) Pattern]**
   - Best practices for managing IaC repos, versioning, and secret handling.
   - *Link*: [IaC Pattern Guide](#)

2. **[GitFlow for Releases]**
   - Coordinates deployment versioning with Git branching strategies.
   - *Link*: [GitFlow Pattern Guide](#)

3. **[Chaos Engineering]**
   - Validates deployment resilience by intentionally introducing failures.
   - *Link*: [Chaos Engineering Guide](#)

4. **[Observability First]**
   - Ensures deployments are monitored for performance, logs, and metrics.
   - *Link*: [Observability Pattern Guide](#)

5. **[Blue-Green Deployments]**
   - Minimizes downtime by maintaining two identical environments.
   - *Link*: [Blue-Green Pattern Guide](#)

6. **[Secret Management]**
   - Securely stores and injects credentials/configuration into deployments.
   - *Link*: [Secret Management Pattern](#)

---
**Note:** Replace placeholder links (`[#]`) with actual pattern documentation URLs. Adjust examples to match your organization’s tooling (e.g., AWS, GCP, Azure, Kubernetes distributions).