# **[Pattern] Infrastructure as Code (IaC) Reference Guide**

---

## **Overview**
Infrastructure as Code (IaC) is a **pattern** where infrastructure (e.g., servers, networks, storage, and databases) is defined, provisioned, and managed using **code and automated tools** rather than manual processes or GUI configurations. IaC enables **reproducible, version-controlled, and scalable** infrastructure deployment, reducing human error and enabling DevOps practices like **CI/CD pipelines**. Key benefits include:
- **Consistency** (identical environments across dev, staging, and production)
- **Speed** (rapid provisioning and rollback)
- **Cost efficiency** (reduced manual effort and waste)
- **Auditability** (track changes via version control)

IaC is widely used with **cloud platforms (AWS, Azure, GCP)**, container orchestration (Kubernetes), and configuration management tools (Ansible, Terraform). This guide provides a structured approach to implementing IaC effectively.

---

## **Schema Reference**
Below is a **high-level schema** for IaC implementation, broken into core components, tools, and best practices.

| **Category**               | **Component**                          | **Description**                                                                 | **Example Tools/Standards**                     |
|----------------------------|----------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Core Concepts**          | **Code Repository**                    | Version-controlled storage for IaC scripts/configs (e.g., Git).               | Git, GitHub, GitLab, Bitbucket               |
|                            | **Provisioning Engine**                | Tool that interprets code to deploy infrastructure (e.g., Terraform, CloudFormation). | Terraform, AWS CloudFormation, Pulumi        |
|                            | **Configuration Management**           | Tools to enforce desired states post-deployment (e.g., Ansible, Chef).         | Ansible, Chef, Puppet                       |
|                            | **Orchestration Layer**                | Manages containerized workloads (e.g., Kubernetes, Docker Swarm).              | Kubernetes, Docker, Nomad                    |
| **Workflows**              | **CI/CD Pipeline**                     | Automates testing, validation, and deployment of IaC changes.                    | Jenkins, GitHub Actions, GitLab CI           |
|                            | **State Management**                   | Tracks infrastructure state (e.g., Terraform state files, Kubernetes manifests). | Terraform (remote state), etcd               |
| **Best Practices**         | **Idempotency**                        | Ensure repeatable, non-destructive deployments.                                | Terraform (`apply` with `auto-approve`), Ansible (`idempotent` tasks) |
|                            | **Modularity**                         | Break IaC into reusable modules (e.g., VPCs, databases).                        | Terraform modules, AWS CDK stacks            |
|                            | **Secret Management**                  | Securely store/manage credentials (e.g., passwords, API keys).                   | HashiCorp Vault, AWS Secrets Manager        |
|                            | **Validation & Testing**               | Pre-deployment checks (e.g., linting, unit tests, integration tests).          | Terraform validate, InSpec, Terragrunt       |
|                            | **Rollback Strategies**                | Automated rollback on failure (e.g., backup states, blue-green deployments).   | Terraform (`destroy` + backup), Kubernetes Rollback |
| **Cloud Providers**        | **Provider-Specific Tools**            | Native IaC tools for cloud platforms (e.g., AWS CDK, Azure ARM templates).      | AWS CDK, Azure Bicep, Google Deployment Manager |
|                            | **Multi-Cloud Considerations**         | Avoid vendor lock-in; use cross-cloud tools (e.g., Terraform).                 | Terraform, Kubernetes, OpenTofu            |

---

## **Implementation Details**

### **1. Core IaC Tools and Workflows**
#### **A. Provisioning Engine: Terraform (Example)**
Terraform is a **declarative** IaC tool that uses **HashiCorp Configuration Language (HCL)** or Terraform Language (TF). Key steps:
1. **Write Infrastructure Code**:
   ```hcl
   # Example: Deploy an AWS EC2 instance
   resource "aws_instance" "web_server" {
     ami           = "ami-0c55b159cbfafe1f0"
     instance_type = "t2.micro"
     tags = {
       Name = "WebServer"
     }
   }
   ```
2. **Initialize and Plan**:
   ```sh
   terraform init   # Downloads provider plugins
   terraform plan   # Shows changes before applying
   ```
3. **Apply Changes**:
   ```sh
   terraform apply  # Creates/deletes resources
   ```
4. **State Management**:
   - Store state in **remote backend** (e.g., S3 + DynamoDB) for team collaboration.
   - Example remote state config:
     ```hcl
     terraform {
       backend "s3" {
         bucket         = "my-terraform-state"
         key            = "prod/terraform.tfstate"
         region         = "us-west-2"
         dynamodb_table = "terraform-locks"
       }
     }
     ```

#### **B. Configuration Management: Ansible (Example)**
Ansible uses **YAML playbooks** to enforce desired states. Example:
```yaml
# Example: Install NGINX on remote hosts
---
- name: Install NGINX
  hosts: webservers
  tasks:
    - name: Ensure NGINX is installed
      apt:
        name: nginx
        state: present
```
Run with:
```sh
ansible-playbook -i inventory.ini nginx_install.yml
```

#### **C. CI/CD Integration**
Automate IaC deployment using pipelines. Example **GitHub Actions workflow**:
```yaml
# .github/workflows/terraform-deploy.yml
name: Terraform Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - run: terraform init
      - run: terraform plan -out=tfplan
      - run: terraform apply tfplan
```

---

### **2. Best Practices**
| **Best Practice**               | **Implementation Guide**                                                                 | **Example Command/Tool**                          |
|----------------------------------|----------------------------------------------------------------------------------------|----------------------------------------------------|
| **Modularize Code**              | Split IaC into reusable modules (e.g., `networking`, `databases`).                       | Terraform modules, AWS CDK libraries              |
| **Use Variables & Secrets**      | Avoid hardcoding; use variables (e.g., `terraform.tfvars`) and secrets managers.      | `terraform -var-file=prod.tfvars`                 |
| **Validate Before Deployment**   | Lint code and run dry runs (e.g., Terraform `plan`).                                    | `terraform validate`, `ansible-lint`              |
| **Enforce Git Hooks**            | Use hooks (e.g., `pre-commit`) to run tests/linters before commits.                    | Pre-commit framework (Python/JS)                 |
| **Document Dependencies**        | List explicit dependencies in `requirements.txt` (Ansible) or `providers.tf` (Terraform). | `terraform init -upgrade`                        |
| **Backup State Regularly**       | Schedule backups of Terraform state (e.g., AWS S3 versioning).                          | `aws s3 cp s3://bucket/terraform.tfstate ./backup/` |

---

### **3. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Cause**                                  | **Mitigation**                                                                 |
|---------------------------------------|--------------------------------------------|--------------------------------------------------------------------------------|
| **State Drift**                       | Manual changes override IaC.               | Use `terraform plan` frequently; enforce no manual edits.                      |
| **Vendor Lock-in**                    | Provider-specific syntax (e.g., CloudFormation). | Use Terraform/Pulumi for cross-cloud; abstract cloud specifics.               |
| **Slow Deployments**                  | Large Terraform plans or missing optimizations. | Split state into modules; use `terraform workspace`.                            |
| **Secret Leakage**                    | Hardcoding credentials in code.            | Use **Vault** or **AWS Secrets Manager**; reference via `terraform_remote_state`. |
| **No Rollback Plan**                  | Critical failures without undo mechanism.   | Implement **Terraform destroy** + backup; use Kubernetes Rollback.              |

---

## **Query Examples**
### **1. How do I deploy a Kubernetes cluster with Terraform?**
```hcl
# main.tf
provider "azurerm" {
  features {}
}

resource "azurerm_container_registry" "acr" {
  name                = "myregistry${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = true
}

resource "kubernetes_cluster" "aks" {
  name                = "my-aks-cluster"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "myakscluster"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2_v2"
  }
}
```
**Steps**:
1. Install Azure CLI and Terraform.
2. Run `terraform init` (requires Azure provider).
3. Apply with `terraform apply`.

---

### **2. How to secure secrets in Ansible?**
Use **Ansible Vault** to encrypt variables:
```sh
# Create encrypted vars file
ansible-vault create secrets.yml

# Reference in playbook
- name: Use encrypted secrets
  hosts: localhost
  vars_files:
    - secrets.yml
  tasks:
    - debug: var=db_password
```

---

### **3. How to rollback a failed Terraform deployment?**
1. **If using remote state**:
   ```sh
   terraform state list           # List resources
   terraform destroy -target=aws_instance.web_server  # Targeted rollback
   ```
2. **For full rollback**:
   ```sh
   terraform plan -out=rollback.plan
   terraform apply -auto-approve rollback.plan
   ```
3. **Restore from backup**:
   ```sh
   aws s3 cp s3://bucket/terraform.tfstate ./terraform.tfstate
   terraform apply
   ```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[GitOps](https://gitops.dev/)** | Syncs infrastructure state with Git repositories (e.g., Flux, ArgoCD).         | Kubernetes environments; CI/CD for IaC.          |
| **[Blue-Green Deployment]**      | Minimizes downtime by running two identical environments.                        | Production deployments with zero downtime.       |
| **[Canary Releases]**            | Gradually rolls out changes to a subset of users/traffic.                        | High-traffic apps; risk mitigation.              |
| **Immutable Infrastructure**      | Treats infrastructure as ephemeral; rebuilds instead of patching.               | Security-focused environments (e.g., containers). |
| **[Serverless IaC]**             | Deploys serverless functions (e.g., AWS Lambda) via IaC.                        | Event-driven architectures.                     |
| **[Policy as Code]**             | Enforces compliance rules (e.g., AWS Config, Open Policy Agent).                | Regulatory compliance; guardrails for IaC.      |

---
## **Further Reading**
- [Terraform Official Docs](https://developer.hashicorp.com/terraform/tutorials)
- [AWS Well-Architected IaC Guide](https://docs.aws.amazon.com/wellarchitected/latest/iac-lens/welcome.html)
- [Kubernetes IaC with Crossplane](https://www.crossplane.io/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)