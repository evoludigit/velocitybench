# **[Pattern] Infrastructure Provisioning – Reference Guide**

---

## **1. Overview**
Infrastructure Provisioning is a core pattern in cloud and DevOps workflows that automates the setup, configuration, and deployment of computational resources (servers, containers, VMs, networks, etc.). This pattern ensures **reproducibility, scalability, and consistency** by abstracting manual provisioning tasks into declarative or scripted pipelines.

Key use cases include:
- **Onboarding new environments** (dev, staging, prod)
- **Disaster recovery** (rapid rollback/redeployment)
- **Multi-cloud deployments** (AWS, Azure, GCP)
- **CI/CD pipelines** (GitOps integrations)

Best practices emphasize **idempotency, version control, and modularity**, ensuring infrastructure aligns seamlessly with application dependencies.

---

## **2. Schema Reference**
Below is a reference schema for infrastructure provisioning, categorized by role and technology.

| **Component**          | **Key Attributes**                                                                 | **Example Tools/Libraries**                     |
|------------------------|------------------------------------------------------------------------------------|--------------------------------------------------|
| **Infrastructure-as-Code (IaC)**       | Compliance with IaC principles, supports multi-cloud, versioned templates          | Terraform, AWS CDK, Pulumi, Ansible, CloudFormation |
| **Configuration Management** | Supports OS-level/config drift detection, agent-based or push-based models       | Ansible, Chef, Puppet, SaltStack                   |
| **Container Orchestration**  | Manages containers (Pods, Services, Deployments), scales dynamically           | Kubernetes (K8s), Docker Swarm, Nomad             |
| **Networking**          | Defines VPC, subnets, security groups, load balancers, and DNS                       | AWS VPC, Cloudflare, Traefik, MetalLB             |
| **Storage**            | Persistent or ephemeral storage (block, object, file), backup policies           | EBS (AWS), Azure Blob, Ceph, NFS                  |
| **Monitoring & Logging** | Observability stack (metrics, logs, alerts), integrates with CI/CD              | Prometheus + Grafana, ELK Stack, Datadog         |
| **Security**           | Role-based access control (RBAC), secrets management, compliance checks          | Vault, HashiCorp Sentinel, OpenPolicyAgent (OPA)   |
| **CI/CD Integration**  | Triggers provisioning from code commits/promotions (e.g., GitHub Actions, ArgoCD)| GitOps (Flux, ArgoCD), Tekton, Jenkins             |

---

## **3. Implementation Details**

### **3.1 Core Principles**
- **Idempotency**: Re-running provisioning scripts should yield the same result (no unintended side effects).
- **Declarative State**: Define desired infrastructure in human-readable files (e.g., HCL, YAML) rather than imperative scripts.
- **Immutable Infrastructure**: Treat servers/containers as stateless; rebuild after updates.
- **Modularity**: Break infrastructure into reusable modules (e.g., separate `networking.tf` and `database.tf` files).

### **3.2 Workflow Steps**
1. **Define Infrastructure**:
   - Use a language/toolchain (e.g., Terraform for Terraform Language, Python for Ansible).
   - Example (Terraform HCL):
     ```hcl
     resource "aws_instance" "web_server" {
       ami           = "ami-0c55b159cbfafe1f0"
       instance_type = "t3.micro"
       tags = {
         Name = "web-server"
         Environment = "production"
       }
     }
     ```
2. **Version Control**:
   - Store IaC templates in Git (e.g., `./terraform/modules/networking/`).
   - Use semantic versioning for modules/configs.
3. **Execute Provisioning**:
   - Run via CLI, CI/CD pipeline, or scheduled jobs.
   - Example CLI command:
     ```bash
     terraform apply -auto-approve
     ```
4. **Validate & Monitor**:
   - Integrate with tools like **Trivy** (security scanning) or **Terraform Cloud** (state tracking).
   - Set up alerts for drift (e.g., using **Crossplane** or **Kubectl** for K8s).

5. **Cleanup**:
   - Use lifecycle policies (e.g., Terraform’s `terraform destroy`) or garbage collection (e.g., **K8s TTLController**).

---

### **3.3 Best Practices**
| **Category**               | **Best Practice**                                                                 | **Example**                                      |
|----------------------------|-----------------------------------------------------------------------------------|--------------------------------------------------|
| **Security**               | Rotate secrets via Vault; restrict IAM roles with least privilege.               | AWS `IAMPolicyGenerator` + HashiCorp Vault       |
| **Performance**            | Right-size resources (e.g., spot instances for batch jobs).                       | AWS Auto Scaling Groups                           |
| **Cost Optimization**      | Use spot/fleet instances; tag resources for cost tracking.                        | AWS Cost Explorer + Terraform tags               |
| **Multi-Region Deployments** | Deploy infrastructure-as-code in multiple regions with redundancy.              | Terraform `provider "aws" { region = "us-west-2" }` |
| **Disaster Recovery**      | Maintain backup states (e.g., Terraform state in S3) and cross-region replication.| Terraform backup + DR plan                      |

---

## **4. Query Examples**
### **4.1 Terraform Provisioning**
**Scenario**: Deploy a VPC with public/private subnets.
```hcl
# main.tf
provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "prod_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "production-vpc"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id     = aws_vpc.prod_vpc.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags = {
    Name = "public-subnet"
  }
}
```
**Command**:
```bash
terraform init       # Initialize backend
terraform plan       # Preview changes
terraform apply      # Deploy
```

### **4.2 Kubernetes Deployment**
**Scenario**: Deploy a Nginx Pod with Helm.
```bash
# Install Helm chart
helm install my-nginx nginx/nginx --set service.type=LoadBalancer
```
**Verify**:
```bash
kubectl get pods -o wide
kubectl expose deployment my-nginx --port=80 --type=LoadBalancer
```

### **4.3 Ansible Playbook**
**Scenario**: Install and configure Apache.
```yaml
# install_apache.yml
- name: Install Apache
  hosts: webservers
  become: yes
  tasks:
    - name: Ensure Apache is installed
      apt:
        name: apache2
        state: present
    - name: Start Apache service
      service:
        name: apache2
        state: started
        enabled: yes
```
**Run**:
```bash
ansible-playbook -i inventory.ini install_apache.yml
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Pair With**                          |
|----------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **[Configuration as Code (CaC)](https://example.com/cac)** | Manages OS/config files (e.g., `/etc/hosts`) via version-controlled scripts. | Infrastructure Provisioning                    |
| **[Blue-Green Deployment](https://example.com/blue-green)** | Minimizes downtime by switching traffic between identical environments.     | Infrastructure Provisioning + CI/CD           |
| **[GitOps](https://example.com/gitops)**                  | Syncs infrastructure state with Git repositories (e.g., ArgoCD, Flux).      | Kubernetes + Infrastructure Provisioning      |
| **[Chaos Engineering](https://example.com/chaos)**        | Tests failure resilience by intentionally injecting chaos (e.g., Gremlin).   | Disaster Recovery + Infrastructure Provisioning|
| **[Canary Releases](https://example.com/canary)**         | Gradually rolls out changes to a subset of users.                         | Microservices + Infrastructure Provisioning   |

---

## **6. Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|--------------------------------------|--------------------------------------------------------------------------------|
| **Drift between IaC and real state** | Enable monitoring (e.g., **Terraform Cloud** or **Crossplane**).              |
| **Overly complex modules**           | Enforce 1-responsibility-per-module; use **Terraform workspaces** for isolation. |
| **Secrets hardcoded in scripts**     | Use **Vault** or **AWS Secrets Manager** with IaC.                            |
| **No rollback plan**                 | Test `terraform destroy` beforehand or use **Terraform State Locks**.          |
| **Vendor lock-in**                   | Abstract cloud-specific logic (e.g., use **Terraform providers** or **Pulumi**).|

---
### **References**
- [Terraform Best Practices](https://www.terraform.io/docs/language/beyond-basic-usage/state.html)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/cluster-administration/)
- [GitOps Manifesto](https://www.gitops.tech/)
- [Infrastructure as Code Guide](https://cloud.google.com/blog/products/devops-sre/infrastructure-as-code-best-practices)

---
**Last Updated**: [YYYY-MM-DD]
**Contributors**: [Team Names/Links]