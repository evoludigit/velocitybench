---
# **[Pattern] Configuration Management Reference Guide**

---

## **Overview**
Configuration Management (CM) ensures servers, services, and applications operate consistently across environments by centralizing, versioning, and automating the deployment of **configuration files**, **policies**, and **settings**. This pattern standardizes configurations while reducing drift, human error, and manual maintenance. It applies to **infrastructure as code (IaC)**, **microservices**, **monolithic apps**, and **hybrid cloud** deployments.

Key benefits:
✔ **Consistency** – Identical configurations across dev, staging, and production.
✔ **Auditability** – Track changes via version control (e.g., Git).
✔ **Scalability** – Deploy configurations at scale using tools like Ansible, Chef, or Terraform.
✔ **Disaster Recovery** – Restore configurations quickly during outages.
✔ **Compliance** – Enforce security/policy standards (e.g., CIS benchmarks).

This guide covers best practices, schema designs, query examples, and integrations with related patterns.

---

## **1. Schema Reference**
A well-structured **configuration schema** defines how data is stored, structured, and validated. Below are common schema types for Configuration Management.

### **1.1 Configuration File Schema (YAML/JSON)**
Standardized templates for machine-readable configs (e.g., for **Nginx, PostgreSQL, Kubernetes**).

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                          | **Validation Rules**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|------------------------------------------|
| **`service_name`**      | `string`       | Unique identifier for the service (e.g., `web-server`).                          | `"nginx"`                                  | Required, regex: `^[a-z0-9-]+$`          |
| **`environment`**       | `enum`         | Deployment environment (dev/stage/prod).                                       | `"production"`                             | Must match allowed values (`"dev"|"stage"|"prod"`) |
| **`version`**           | `string`       | Version of the config (e.g., `v1.2.0`).                                       | `"2.0"`                                    | SemVer-compliant: `^[0-9]+\.[0-9]+\.[0-9]+$` |
| **`params`**            | `object`       | Key-value pairs for dynamic settings.                                            | `{ "listen_port": 8080, "max_conns": 1000 }` | Schema-specific (e.g., `max_conns > 0`) |
| **`dependencies`**      | `array`        | Required services/plugins for this config.                                      | `["redis", "mysql"]`                      | All dependencies must exist in the system |
| **`metadata`**          | `object`       | Non-functional metadata (e.g., author, last_updated).                           | `{ "author": "admin", "timestamp": "2024-05-20" }` | Optional |

---

### **1.2 Infrastructure-as-Code (IaC) Schema (Terraform Example)**
For cloud and on-prem deployments, CM integrates with IaC tools.

| **Field**               | **Type**       | **Description**                                                                 | **Example**                          | **Notes**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------|------------------------------------|
| **`resource`**          | `string`       | Type of resource (e.g., `aws_instance`, `k8s_deployment`).                     | `"aws_instance"`                     | Must match provider schema.        |
| **`name`**              | `string`       | Unique name for the resource (e.g., `web-server-01`).                           | `"app-server"`                       | Alphanumeric + hyphens only.      |
| **`config`**            | `map`          | Key-value pairs for resource attributes.                                         | `{ "ami": "ami-123456", "instance_type": "t3.medium" }` | Provider-specific rules apply.     |
| **`tags`**              | `map`          | Metadata for tracking (e.g., `Environment: prod`).                               | `{ "Team": "Backend", "Owner": "Alice" }` | Optional but recommended.         |
| **`update_strategy`**   | `string`       | How updates are applied (e.g., `rolling`, `immediate`).                          | `"rolling"`                           | Depends on resource type.          |

**Example (Terraform HCL):**
```hcl
resource "aws_instance" "web_server" {
  ami           = "ami-123456"
  instance_type = "t3.medium"
  tags = {
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```

---

### **1.3 Secrets Management Schema**
Sensitive data (e.g., API keys, DB passwords) should **never** be hardcoded. Use encrypted vaults.

| **Field**               | **Type**       | **Description**                                                                 | **Example**                          | **Security Notes**                  |
|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------|------------------------------------|
| **`secret_id`**         | `string`       | Unique identifier (e.g., `db_password`).                                          | `"prod_db_password"`                 | Must follow naming conventions.    |
| **`value`**             | `string` (enc) | Encrypted sensitive value.                                                         | `{"ciphertext": "AQ==", "iv": "..."}` | Use **AWS KMS**, **Vault**, or **HashiCorp Secrets**. |
| **`rotation_policy`**   | `object`       | Rules for automatic rotation.                                                    | `{ "interval_hours": 720, "ttl_days": 90 }` | Required for PII/data protection. |
| **`access_policy`**     | `array`        | IAM/RBAC roles allowed to access.                                                  | `[{ "role": "db_admin", "scope": "read-write" }]` | Principle of least privilege.    |

---

## **2. Query Examples**
Queries retrieve/configurate management data for auditing, deployment, or troubleshooting.

---

### **2.1 Query Configurations by Service**
**Use Case:** List all configs for a specific service (e.g., `postgresql`).
**Tool:** CLI (e.g., `cfn describe-configures` / `ansible inventory`)

```bash
# AWS Systems Manager Parameter Store (CLI)
aws ssm get-parameters-by-path --path "/configs/postgresql"

# Ansible (YAML Inventory)
cat inventory.ini | grep -A 5 "postgresql:"
[postgresql:vars]
db_version=14.3
max_connections=200
```

**Output:**
```json
{
  "Parameters": [
    {
      "Name": "/configs/postgresql/version",
      "Type": "String",
      "Value": "14.3"
    },
    {
      "Name": "/configs/postgresql/logging",
      "Type": "String",
      "Value": "true"
    }
  ]
}
```

---

### **2.2 Check Configuration Drift**
**Use Case:** Detect unintended changes in live servers vs. desired state.
**Tool:** **InSpec**, **CFN Lint**, or **Puppet Server**

```bash
# Compare local config (git) vs. remote server
ansible-playbook -i inventory.ini drift_check.yml
```
**Example Playbook (`drift_check.yml`):**
```yaml
---
- hosts: all
  tasks:
    - name: Check if nginx listen_port matches config
      assert:
        that: ansible_facts.nginx_listen_ports | intersect([8080]) | length > 0
        msg: "Port mismatch! Expected: 8080, Found: {{ ansible_facts.nginx_listen_ports }}"
```

---

### **2.3 Apply Config Changes via API**
**Use Case:** Dynamically update a config (e.g., scaling limits) without redeploying.
**Tool:** **AWS Config API**, **Kubernetes ConfigMaps**

```bash
# Update Kubernetes ConfigMap (v1.28+)
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
  namespace: default
data:
  LOG_LEVEL: "DEBUG"  # Changed from "INFO"
EOF
```

**Response:**
```json
{
  "kind": "ConfigMap",
  "metadata": {
    "resourceVersion": "12345"
  }
}
```

---

### **2.4 Audit Config Changes**
**Use Case:** Log who modified a config and when.
**Tool:** **Git Commit History** + **SIEM Integration** (e.g., Splunk, Datadog)

```bash
# Git audit for config changes (e.g., nginx.conf)
git log --since="2024-05-01" --follow -- nginx/
```
**Example Output:**
```
commit abc123 (HEAD -> main)
Author: Alice Dev <alice@example.com>
Date:   Mon May 20 10:00:00 2024 +0000

    [CM-456] Updated nginx timeout settings for new API endpoints
    ...
```

---

## **3. Implementation Best Practices**
### **3.1 Version Control**
- Store configs in **Git** (private repos for secrets).
- Use **branches** for environment-specific configs (e.g., `main` → `prod`).
- **Tag releases** (e.g., `git tag v1.2.0`).

### **3.2 Tooling Stack**
| **Tool**          | **Purpose**                                                                 | **Example Commands**                          |
|--------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Ansible**       | Idempotent config deployment.                                                 | `ansible-playbook site.yml --limit web-servers` |
| **Chef/Puppet**   | Declarative automation (enterprise).                                         | `chef-client --node-name web01`               |
| **Terraform**     | IaC for infrastructure + configs.                                            | `terraform apply -auto-approve`               |
| **AWS Systems Manager (SSM)** | Centralized config storage/management.                                      | `aws ssm put-parameter --name "db_url" --value "postgres://..."` |
| **Vault (HashiCorp)** | Secure secrets management.                                                   | `vault write secret/db_creds username=admin`  |
| **InSpec**        | Compliance checking (e.g., CIS benchmarks).                                  | `inspec exec compliance.rb`                   |

### **3.3 Security**
- **Encrypt secrets** at rest (use **AWS KMS**, **HashiCorp Vault**).
- **Rotate secrets** automatically (e.g., every 90 days).
- **Restrict access** via IAM roles (e.g., `config-readonly` policies).
- **Immutable configs**: Treat configs as code—no manual edits in production.

### **3.4 Performance**
- **Caching**: Use **CDNs** (e.g., CloudFront) for static configs.
- **Lazy loading**: Load configs only when needed (e.g., Kubernetes `ConfigMaps` on-pod startup).
- **Validation**: Validate configs during deployment (e.g., **Ansible `validate`**).

### **3.5 Disaster Recovery**
- **Backup configs** daily to S3/Artifact Registry.
- **Test rollback**: Simulate config failures in staging.
- **Chaos Engineering**: Use **Gremlin** or **Chaos Monkey** to test resilience.

---

## **4. Schema Validation**
Validate configs before deployment to catch errors early.

### **4.1 JSON Schema Example**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Nginx Config Schema",
  "type": "object",
  "properties": {
    "server": {
      "type": "object",
      "properties": {
        "listen": { "type": "string", "pattern": "^:(\\d{1,5})$" },
        "server_name": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["listen"]
    }
  },
  "required": ["server"]
}
```

**Validation Tool:** [`jsonschema`](https://pypi.org/project/jsonschema/) (Python)
```bash
pip install jsonschema
jsonschema -i schema.json -f nginx.conf
```

---

### **4.2 Ansible Validation**
Use **Ansible `validate`** in playbooks:
```yaml
---
- hosts: localhost
  tasks:
    - name: Validate nginx config
      ansible.builtin.command: nginx -t -c /etc/nginx/nginx.conf
      register: nginx_test
      changed_when: false
      failed_when: nginx_test.rc != 0
```

---

## **5. Related Patterns**
Configuration Management integrates with these patterns for a complete DevOps workflow:

| **Pattern**               | **Description**                                                                 | **Integration Example**                          |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **Infrastructure as Code** | Define infrastructure in code (IaC) to ensure reproducibility.               | Terraform + Ansible for hybrid cloud.          |
| **Secrets Management**    | Securely store and rotate sensitive data.                                      | HashiCorp Vault + Kubernetes Secrets.           |
| **Immutable Infrastructure** | Treat servers as ephemeral; replace instead of patch.                        | Docker/Kubernetes deployments from CM.          |
| **Canary Deployments**    | Gradually roll out config changes to minimize risk.                           | Istio + ConfigMaps for phased updates.          |
| **Observability**         | Monitor config health (e.g., log analysis, metrics).                          | Prometheus + Grafana for config performance.    |
| **GitOps**                | Sync configs via Git (e.g., ArgoCD, Flux).                                    | ArgoCD applying configs from a Git repo.        |

---

## **6. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                  |
|-------------------------------------|----------------------------------------|-----------------------------------------------|
| Config drift detected               | Manual edits overwrote CM.             | Enable `immutable: true` in your CM tool.     |
| Secrets exposed                     | Hardcoded in config files.              | Use **Vault** or **Secrets Manager**.         |
| Slow deployments                   | Large config files (e.g., 50MB+).       | Split configs by service (modularize).       |
| Permission errors                  | IAM roles lack `config:Update` rights.  | Attach `AWSConfigFullAccess` policy.          |
| Validation failures                 | Schema mismatches (e.g., wrong data type). | Use **OpenAPI/Swagger** for APIs.             |

---

## **7. Example Workflow**
1. **Define**:
   Store `nginx.conf` in Git (`git add nginx.conf`).
   Validate with `jsonschema` or Ansible’s `validate`.

2. **Deploy**:
   ```bash
   # Ansible push (idempotent)
   ansible-playbook -i prod_inventory.yml nginx_config.yml

   # Terraform (IaC + CM)
   terraform apply -target aws_instance.web
   ```

3. **Monitor**:
   - **Prometheus Alert**: Trigger if `nginx_up` drops below 99%.
   - **SIEM**: Log config changes in Splunk.

4. **Rollback**:
   ```bash
   # Revert to last good config
   git checkout HEAD~1 -- nginx.conf
   ansible-playbook -i prod_inventory.yml nginx_config.yml
   ```

---

## **8. Further Reading**
- [AWS Well-Architected Config Management](https://aws.amazon.com/architecture/well-architected/)
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/table-of-contents/)
- [Terraform Best Practices](https://developer.hashicorp.com/terraform/tutorials/aws-get-started)
- [Open Policy Agent (OPA) for Config Validation](https://www.openpolicyagent.org/)