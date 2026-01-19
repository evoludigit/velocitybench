**[Pattern] Virtual-Machines Setup – Reference Guide**

---

### **1. Overview**
This reference guide outlines the **Virtual-Machines Setup** pattern, a standardized framework for configuring, deploying, and managing virtual machines (VMs) in cloud, on-premises, or hybrid environments. It covers key concepts, implementation requirements, configuration schemas, query examples, and related patterns for ensuring scalable, secure, and reproducible virtualized infrastructure.

The pattern streamlines VM provisioning by defining best practices for:
- **Host Selection** (cloud providers, hypervisors, or bare-metal)
- **Operating System Customization** (templates, roles, and configurations)
- **Network & Security** (subnets, firewalls, and access controls)
- **Resource Allocation** (CPU, RAM, storage, and quotas)
- **Automation & Lifecycle Management** (CI/CD integration, state management, and backup policies).

Designed for DevOps engineers, cloud administrators, and infrastructure teams, this guide ensures consistency across VM deployments while accommodating specific use cases (e.g., development, testing, production).

---

### **2. Key Concepts & Implementation Details**

#### **2.1 Core Components**
| **Component**               | **Description**                                                                                                                                                                                                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **VM Template**             | Pre-configured golden image (OS + applications) for rapid deployment. Supports customizable variables (e.g., `VM_NAME`, `MEMORY_GB`).                                                                                                                     |
| **Deployment Plan**         | Defines VM attributes (e.g., `hostname`, `cpu_cores`, `disk_size_GB`) and deployment triggers (e.g., CI/CD pipeline, manual request).                                                                                                                  |
| **Resource Pool**           | Logical grouping of VMs (e.g., "dev," "prod") with shared quotas (CPU, RAM, storage) to enforce resource limits.                                                                                                                                     |
| **Network Zone**            | Isolated subnet or VPC segment (e.g., "public," "private") with predefined security groups, CIDR blocks, and NACLs.                                                                                                                                  |
| **Lifecycle Hooks**         | Callbacks executed at VM stages (e.g., `pre_start`, `post_migration`) for custom logic (e.g., software updates, monitoring tagging).                                                                                                                 |
| **Backup Strategy**         | Scheduled snapshots or volume backups with retention policies (e.g., daily/weekly incremental backups).                                                                                                                                                   |
| **Scaling Policy**          | Auto-scaling rules (e.g., scale-up if CPU > 70% for 5 mins) or manual scaling via API/CLI.                                                                                                                                                                             |
| **Audit Logs**              | Immutable records of VM changes (e.g., `2024-02-20 14:30:00: VM "web-01" rebooted by user "admin123"`).                                                                                                                                                     |

#### **2.2 Best Practices**
- **Image Optimization**: Use minimal base images (e.g., Alpine Linux) and exclude unnecessary packages.
- **Immutable Infrastructure**: Treat VMs as ephemeral; rebuild from templates instead of modifying running instances.
- **Secrets Management**: Store credentials (e.g., DB passwords) in a secrets manager (HashiCorp Vault, AWS Secrets Manager) with short-lived credentials for VMs.
- **Tagging Strategy**: Apply consistent tags (e.g., `env=prod`, `owner=team-x`) for cost tracking and access control.
- **Isolation**: Segregate VMs by function (e.g., DBs in private subnets, web servers in public) and enforce least-privilege policies.

#### **2.3 Supported Environments**
| **Environment**      | **Providers/Tools**                                                                                     | **Notes**                                                                                     |
|----------------------|--------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Cloud**            | AWS (EC2), Azure (VMs), GCP (Compute Engine), Oracle Cloud (VM)                                    | Leverage provider-specific APIs for native integrations (e.g., AWS Auto Scaling).            |
| **On-Premises**      | VMware vSphere, Proxmox, KVM, Hyper-V                                                               | Requires additional plugins for automation (e.g., Terraform providers).                      |
| **Hybrid**           | Multi-cloud (e.g., AWS + Azure) or edge deployments (e.g., VMs on IoT gateways)                     | Use consistent CLI/API interfaces (e.g., OpenStack, Kubernetes Virtualization).               |
| **Containerized**    | VMs hosting container runtimes (e.g., Docker/Kubernetes pods)                                     | Ideal for lightweight workloads with VM-based security boundaries.                          |

---

### **3. Schema Reference**
The following tables define the core data schemas for the **Virtual-Machines Setup** pattern. Fields marked with `*` are required.

#### **3.1 VM Template Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `template_id`*          | `string`       | Unique identifier for the template (e.g., generated UUID or `my-app-template-v2`).                                                                                                                                                                             | `texample-abc123`                     |
| `os`*                   | `string`       | Base OS (e.g., `ubuntu-22.04`, `windows-server-2022`).                                                                                                                                                                                                                   | `ubuntu-22.04-lts`                    |
| `architecture`          | `string`       | CPU architecture (e.g., `x86_64`, `arm64`).                                                                                                                                                                                                                           | `x86_64`                              |
| `packages`              | `array[string]`| List of packages to install during template creation (e.g., `nginx`, `postgresql`).                                                                                                                                                                          | `["nginx", "postgresql-14"]`          |
| `user_data_script`      | `string`       | Cloud-init or user-data script for post-install configuration (e.g., SSH keys, firewall rules).                                                                                                                                                             | `[...] #!/bin/bash\napt-get update`  |
| `created_at`            | `datetime`     | Timestamp of template creation.                                                                                                                                                                                                                                   | `2024-02-15T10:30:00Z`                |
| `last_updated`          | `datetime`     | Timestamp of last template update.                                                                                                                                                                                                                                 | `2024-02-20T14:45:00Z`                |
| `version`               | `string`       | Semantic version (e.g., `1.2.0`).                                                                                                                                                                                                                                     | `1.2.0`                               |

---

#### **3.2 Deployment Plan Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `plan_id`*              | `string`       | Unique plan identifier (e.g., `web-tier-plan`).                                                                                                                                                                                                                              | `web-tier-plan`                       |
| `template_id`*          | `string`       | Reference to the VM template (from `template_id` above).                                                                                                                                                                                                                     | `texample-abc123`                     |
| `name`*                 | `string`       | VM hostname (e.g., `web-server-01`).                                                                                                                                                                                                                                      | `web-server-01`                       |
| `cpu_cores`*            | `integer`      | Minimum guaranteed CPU cores.                                                                                                                                                                                                                                          | `2`                                    |
| `memory_gb`*            | `integer`      | Minimum guaranteed RAM in GB.                                                                                                                                                                                                                                    | `4`                                    |
| `disk_size_gb`*         | `integer`      | Root disk size in GB (additional volumes can be attached separately).                                                                                                                                                                                           | `50`                                   |
| `network_zone`*         | `string`       | Subnet or VPC segment (e.g., `public-web`, `private-db`).                                                                                                                                                                                                               | `public-web`                          |
| `security_groups`       | `array[string]`| List of security group rules (e.g., `allow-ssh`, `allow-http`).                                                                                                                                                                                                          | `["allow-ssh", "allow-http-80"]`       |
| `autoscale`             | `object`       | Auto-scaling configuration (e.g., `min_instances: 2`, `max_instances: 5`).                                                                                                                                                                                    | `{ "min": 2, "max": 5, "trigger": "cpu>70%" }` |
| `backup_policy`         | `object`       | Backup schedule (e.g., `daily`, `weekly`).                                                                                                                                                                                                                                   | `{ "frequency": "daily", "retention": 30 }` |
| `tags`                  | `map<string>`   | Metadata keys/values (e.g., `env=prod`, `owner=devops`).                                                                                                                                                                                                               | `{ "env": "prod", "owner": "devops" }` |

---

#### **3.3 Resource Pool Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `pool_name`*            | `string`       | Logical name (e.g., `dev-pool`, `prod-pool`).                                                                                                                                                                                                                                | `prod-pool`                           |
| `max_cpu_cores`*        | `integer`      | Hard limit on total CPU cores for all VMs in the pool.                                                                                                                                                                                                                 | `128`                                  |
| `max_memory_gb`*        | `integer`      | Hard limit on total RAM in GB.                                                                                                                                                                                                                                     | `256`                                  |
| `max_disk_gb`*          | `integer`      | Hard limit on total disk space across all VMs.                                                                                                                                                                                                                         | `5000`                                 |
| `default_template`      | `string`       | Default template ID for new deployments (optional).                                                                                                                                                                                                               | `texample-abc123`                     |
| `members`               | `array<string>`| List of VM names currently in the pool.                                                                                                                                                                                                                              | `["web-01", "app-02"]`                |

---

#### **3.4 Lifecycle Hook Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `hook_name`*            | `string`       | Identifier for the hook (e.g., `pre_start`, `post_migration`).                                                                                                                                                                                                           | `pre_start`                           |
| `action`*               | `string`       | Script or command to execute (e.g., `run_antivirus_scan`).                                                                                                                                                                                                             | `run_antivirus_scan`                  |
| `timeout_sec`           | `integer`      | Maximum execution time in seconds.                                                                                                                                                                                                                                   | `300`                                  |
| `error_retry_count`     | `integer`      | Number of retries on failure (default: `0`).                                                                                                                                                                                                                               | `3`                                    |
| `payload`               | `object`       | Dynamic inputs (e.g., `{"vm_id": "vm-123"}`).                                                                                                                                                                                                                                   | `{ "vm_id": "vm-123", "param": "value" }` |

---

### **4. Query Examples**
Use the following CLI/API examples to interact with the **Virtual-Machines Setup** pattern. Assume a REST API endpoint `https://api.vm-setup.example.com/v1`.

---

#### **4.1 List Available VM Templates**
```bash
curl -X GET "https://api.vm-setup.example.com/v1/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```
**Response (JSON):**
```json
{
  "templates": [
    {
      "template_id": "texample-abc123",
      "os": "ubuntu-22.04-lts",
      "architecture": "x86_64",
      "created_at": "2024-02-15T10:30:00Z"
    },
    {
      "template_id": "texample-def456",
      "os": "windows-server-2022",
      "architecture": "x86_64",
      "created_at": "2024-02-10T09:15:00Z"
    }
  ]
}
```

---

#### **4.2 Create a New VM from a Template**
```bash
curl -X POST "https://api.vm-setup.example.com/v1/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "texample-abc123",
    "name": "analytics-web-01",
    "cpu_cores": 4,
    "memory_gb": 8,
    "disk_size_gb": 100,
    "network_zone": "public-analytics",
    "security_groups": ["allow-ssh", "allow-http-80"]
  }'
```
**Response (JSON):**
```json
{
  "deployment_id": "dep-g78901",
  "status": "pending",
  "vm_name": "analytics-web-01",
  "start_time": "2024-02-20T15:20:00Z",
  "endpoint": "https://api.vm-setup.example.com/v1/deployments/dep-g78901"
}
```

---

#### **4.3 Attach a Lifecycle Hook**
```bash
curl -X POST "https://api.vm-setup.example.com/v1/deployments/dep-g78901/hooks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hook_name": "pre_start",
    "action": "run_security_scan",
    "timeout_sec": 60,
    "payload": { "severity_threshold": "high" }
  }'
```

---

#### **4.4 Scale a Deployment**
```bash
curl -X PATCH "https://api.vm-setup.example.com/v1/deployments/dep-g78901/scale" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "scale_out",
    "count": 3
  }'
```

---
#### **4.5 Check VM Status**
```bash
curl -X GET "https://api.vm-setup.example.com/v1/deployments/dep-g78901/status" \
  -H "Authorization: Bearer $TOKEN"
```
**Response (JSON):**
```json
{
  "status": "running",
  "vm_id": "vm-xyz789",
  "ip_address": "192.168.1.10",
  "public_ip": "203.0.113.45",
  "tags": {
    "env": "prod",
    "owner": "analytics-team"
  },
  "last_backup": "2024-02-20T14:00:00Z"
}
```

---

#### **4.6 Trigger a Backup**
```bash
curl -X POST "https://api.vm-setup.example.com/v1/deployments/dep-g78901/backup" \
  -H "Authorization: Bearer $TOKEN"
```

---

### **5. Related Patterns**
Complement the **Virtual-Machines Setup** pattern with these related patterns for end-to-end infrastructure management:

| **Pattern**                     | **Description**                                                                                                                                                                                                                                                                 |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Configuration Management**    | Use **Ansible**, **Puppet**, or **Chef** to enforce consistent VM configurations post-deployment.                                                                                                                                                   |
| **Network Segmentation**        | Apply **Zero Trust Network Access (ZTNA)** or **Software-Defined Networking (SDN)** to dynamically isolate VMs based on policies (e.g., micro-segmentation).                                                                                     |
| **Secrets & Credential Management** | Integrate **HashiCorp Vault**, **AWS Secrets Manager**, or **Azure Key Vault** to rotate and secure VM credentials (e.g., SSH keys, DB passwords).                                                                                           |
| **Observability & Monitoring**  | Deploy **Prometheus**, **Grafana**, or **AWS CloudWatch** to track VM metrics (CPU, memory, disk I/O) and set up alerts.                                                                                                                 |
| **Disaster Recovery (DR)**      | Use **multi-region VM replication** or **VM snapshots** with **Azure Site Recovery** or **AWS Backup** for failover capabilities.                                                                                                             |
| **Container Orchestration**     | Run VMs hosting **Kubernetes clusters** or **Docker Swarm** for containerized workloads (e.g., VM-backed Kubernetes nodes).                                                                                                           |
| **Cost Optimization**           | Apply **right-sizing recommendations** (e.g., AWS Compute Optimizer) and **spot instances** for non-critical VMs to reduce cloud costs.                                                                                                       |
| **Immutable Infrastructure**    | Combine with **CI/CD pipelines** (e.g., GitHub Actions, Jenkins) to rebuild VMs from templates on every change, avoiding manual updates.                                                                                                      |
| **Policy as Code**              | Enforce compliance with **Open Policy Agent (OPA)** or **AWS Config** to validate VM configurations against standards (e.g., CIS benchmarks).                                                                                             |
| **Hybrid Cloud Management**     | Use **Tools like Terraform Cloud**, **Crossplane**, or **Microsoft Hybrid Cloud Solution Accelerator (HCSA)** to manage VMs across on-premises and cloud providers.                                                                              |

---

### **6. Frequently Asked Questions (FAQ)**
| **Q**                          | **A**                                                                                                                                                                                                                                                                 |
|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **How do I update a VM template?** | Use the PATCH endpoint for templates: `curl -X PATCH .../templates/texample-abc123 -d '{"os": "ubuntu-22.0