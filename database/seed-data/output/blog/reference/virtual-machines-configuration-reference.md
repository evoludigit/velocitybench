# **[Pattern] Virtual Machines Configuration Reference Guide**

---

## **1. Overview**
The **Virtual Machines (VM) Configuration Pattern** enables centralized management of virtual machine infrastructure by abstracting hardware, networking, and storage details into reusable configurations. This pattern decouples VM definitions from underlying physical resources, allowing dynamic provisioning, scaling, and lifecycle management.

Key use cases include:
- **Multi-tenancy** – Isolate workloads per team/department.
- **Disaster recovery** – Clone and restore VMs from backups.
- **Compliance** – Enforce consistent security/policy templates.
- **Cost optimization** – Right-size resources via predefined templates.

This guide covers schema design, query operations, and integration with related infrastructure patterns.

---

## **2. Key Concepts**
| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **VM Template**    | A blueprint defining OS, CPU, RAM, storage, and networking settings.       |
| **VM Instance**    | A running VM based on a template with an assigned ID and state.             |
| **Network Profile**| Configuration for VM networking (VLAN, security groups, IP ranges).         |
| **Storage Profile**| Storage type (SSD/HDD), volume size, and provisioning method (thin/dense). |
| **Lifecycle Hooks**| Custom scripts (pre/post-migrate, start/stop).                             |

---

## **3. Schema Reference**

### **Core Tables**
| Entity               | Description                                                                                     | Fields                                                                                     |
|----------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **`vm_templates`**   | Defines reusable VM configurations.                                                             | `template_id (PK)`, `name`, `os_type`, `cpu_cores`, `ram_gb`, `storage_profile_id`,      |
|                      |                                                                                                 | `network_profile_id`, `created_by`, `created_at`, `updated_at`                             |
| **`vm_instances`**   | Tracks running VMs derived from templates.                                                      | `instance_id (PK)`, `template_id (FK)`, `hostname`, `state` ("running"/"stopped"/"error"), |
|                      |                                                                                                 | `ip_address`, `started_at`, `stopped_at`, `error_message`                                  |
| **`network_profiles`** | Configures VM networking (VLAN, firewall rules, DHCP).                                      | `profile_id (PK)`, `vlan_id`, `subnet_mask`, `gateway`, `firewall_rules`, `dhcp_range` |
| **`storage_profiles`** | Defines storage settings (block storage, object storage).                                      | `profile_id (PK)`, `storage_type` ("SSD"/"HDD"), `volume_size_gb`, `iops`, `backup_policy` |
| **`lifecycle_hooks`** | Custom scripts triggered at VM lifecycle events.                                              | `hook_id (PK)`, `template_id (FK)`, `event_type` ("on_start"/"on_stop"), `script_url`     |

---

### **Relationships**
- A **`vm_instance`** references one **`vm_template`** (`template_id`).
- Templates use **`network_profile_id`** and **`storage_profile_id`**.
- Hooks are attached to **`vm_templates`** via `template_id`.

---

## **4. Query Examples**

### **Retrieve All VM Templates**
```sql
SELECT
    template_id,
    name,
    os_type,
    cpu_cores,
    ram_gb
FROM vm_templates
WHERE os_type = 'Linux';
```

### **List Running VM Instances**
```sql
SELECT
    instance_id,
    hostname,
    ip_address,
    started_at
FROM vm_instances
WHERE state = 'running'
ORDER BY started_at DESC;
```

### **Get Storage Profile for a VM**
```sql
SELECT
    s.profile_id,
    s.storage_type,
    s.volume_size_gb
FROM vm_instances i
JOIN vm_templates t ON i.template_id = t.template_id
JOIN storage_profiles s ON t.storage_profile_id = s.profile_id
WHERE i.instance_id = 'vm-xyz123';
```

### **Filter Templates by Network Profile**
```sql
SELECT
    t.name,
    n.vlan_id,
    n.gateway
FROM vm_templates t
JOIN network_profiles n ON t.network_profile_id = n.profile_id
WHERE n.vlan_id = 10;
```

### **Filter Instances by Lifecycle Hooks**
```sql
SELECT
    i.hostname,
    l.event_type,
    l.script_url
FROM vm_instances i
JOIN vm_templates t ON i.template_id = t.template_id
JOIN lifecycle_hooks l ON t.template_id = l.template_id
WHERE l.event_type = 'on_start';
```

---

## **5. Implementation Best Practices**
### **1. Enforce Naming Conventions**
- Use prefixes (e.g., `web-`, `db-`) to categorize instances.
- Avoid spaces/special characters in `hostname` or `template_id`.

### **2. Versioning**
- Add `version` field to `vm_templates` to manage updates.
- Use immutable template IDs for new versions (e.g., `template-v1`, `template-v2`).

### **3. Backup & Rollback**
- Store snapshots of storage profiles.
- Use `instance_id` for auditing rollbacks.

### **4. Security**
- Restrict `template_id` updates via RBAC (e.g., only admins can modify).
- Encrypt sensitive fields in `lifecycle_hooks` (e.g., `script_url`).

---

## **6. Related Patterns**
| Pattern                          | Integration Points                                                                 |
|----------------------------------|----------------------------------------------------------------------------------|
| **Infrastructure as Code (IaC)** | Use templates in Terraform/CloudFormation for declarative VM provisioning.       |
| **Auto-Scaling**                  | Create dynamic scaling rules based on `vm_instances` state (e.g., scale out when `state='running'`). |
| **Observability**                 | Export VM metrics (CPU/RAM) from `vm_instances` to monitoring dashboards.         |
| **Disaster Recovery (DR)**       | Use `vm_templates` to restore from backups via `storage_profiles`.                |
| **Multi-Cloud Management**        | Extend the schema to include cloud provider-specific fields (e.g., `provider='AWS'`). |

---

## **7. Troubleshooting**
| Issue                          | Solution                                                                             |
|--------------------------------|--------------------------------------------------------------------------------------|
| **VM fails to start**           | Check `error_message` in `vm_instances`. Validate `lifecycle_hooks` for `on_start`. |
| **Storage profile mismatches**  | Verify `storage_profile_id` consistency across `vm_templates` and `storage_profiles`. |
| **Network connectivity issues**  | Audit `network_profiles` for VLAN/gateway misconfigurations.                       |

---

## **8. Example Workflow**
1. **Create a Template**:
   ```sql
   INSERT INTO vm_templates
   VALUES (1, 'Web-Server-Linux', 'Ubuntu', 4, 8, 2, 1, 'admin', NOW(), NOW());
   ```
2. **Provision a VM**:
   ```sql
   INSERT INTO vm_instances
   VALUES (101, 1, 'webhost-01', 'running', '192.168.1.10', NOW(), NULL, NULL);
   ```
3. **Attach a Hook**:
   ```sql
   INSERT INTO lifecycle_hooks
   VALUES (1, 1, 'on_start', 'https://scripts.example.com/start.sh');
   ```

---
**Last Updated**: [Insert Date]
**Version**: 1.2