# **[Pattern] Virtual Machines Gotchas – Reference Guide**

---

## **Overview**
Virtual machines (VMs) offer flexibility, isolation, and portability but introduce unique pitfalls that can disrupt workflows, degrade performance, or lead to security vulnerabilities. This guide identifies **common "gotchas"**—unintended behaviors, misconfigurations, or edge cases—when working with VMs in cloud, on-premises, or hybrid environments. Whether you're provisioning VMs, managing disk layouts, or optimizing resource usage, understanding these challenges helps avoid costly errors. Key areas covered: **resource allocation, storage quirks, network latency, snapshot management, security risks, and OS-specific traps.**

---

## **1. Key Gotchas by Category**

| **Category**               | **Subtype**                     | **Gotcha**                                                                                     | **Impact**                                                                                     |
|----------------------------|----------------------------------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Resource Allocation**    | CPU Overcommitment               | VMs may not get guaranteed CPU shares; burstiness can starve IO-bound workloads.              | Performance degradation, throttling.                                                         |
|                            | Memory Swapping                   | VMs can swap to disk if allocated memory < physical RAM + reserved swap.                       | Slowdowns, unpredictable behavior.                                                            |
|                            | Storage I/O Limits               | Thin-provisioned disks may throttle writes if over-subscribed.                                | Slower storage operations, potential 409 errors.                                             |
| **Storage & Disk**         | Disk Resizing                     | Cannot expand a VM’s disk after booting (varies by hypervisor; e.g., Azure requires offline resize). | Downtime or data corruption.                                                                 |
|                            | Snapshot Bloat                    | Snapshots accumulate overhead; large snapshots slow down VMs and snapshots themselves.           | Performance drain, storage fill-up, snapshot explosion.                                       |
|                            | Shared Storage Latency           | Block storage (e.g., NFS, iSCSI) may introduce latency for VMs on separate hosts.                | Degraded network-attached storage performance.                                                |
| **Networking**             | MAC Address Duplication          | VMs may share MAC addresses with parent host or other VMs (e.g., in nested virtualization).     | Network conflicts, unreachable VMs.                                                           |
|                            | NAT Gateways & Firewall Rules    | Missing firewall rules or improper NAT mappings can block VM traffic.                          | VM isolation failures, connectivity issues.                                                   |
|                            | Floating IP Leaks                | Public IPs not properly reclaimed after VM termination (e.g., in cloud VMs).                 | Unauthorized access, cost overruns.                                                           |
| **Security**               | Shared Kernel Exploits           | Rootkits or host-level attacks may compromise all VMs on a hypervisor.                          | Full VM compromise, lateral movement.                                                         |
|                            | Credential Reuse                 | Default credentials (e.g., `admin:password`) left in VMs post-deployment.                      | Unauthorized access, privilege escalation.                                                     |
|                            | Guest OS Updates                 | Unpatched guest OSes expose VMs to vulnerabilities (e.g., Meltdown/Spectre).                  | Exploitable via host or network.                                                              |
| **Operational Traps**     | Snapshots as Backups              | Snapshots are *not* backups; they’re cumulative and can’t be relied upon for disaster recovery. | Data loss if snapshots corrupt or delete.                                                      |
|                            | Disk Encryption                    | Guest OS encryption (e.g., BitLocker) requires host-level support (e.g., Azure Disk Encryption). | Failed VM instantiation, data exposure.                                                       |
|                            | IOPS Throttling                  | Thin-provisioned disks hit limits when VMs simultaneously write large files.                   | High latency, failed operations.                                                             |
| **Hybrid/Cloud-Specific** | Vendor-Specific Quirks           | AWS’s EBS vs. Azure’s Managed Disks vs. GCP’s Persistent Disks have different resize/cloning rules. | Cross-cloud migration failures, unexpected costs.                                            |
|                            | Cold Boot Delays                 | Cloud VMs may take minutes to initialize (e.g., Azure’s "PV" disks).                           | Unpredictable startup times.                                                                  |

---

## **2. Schema Reference**
Below is a structured schema for documenting VM gotchas (extendable for CMDBs or runbooks).

| **Field**          | **Description**                                                                                     | **Example Value**                                                                               |
|--------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `category`         | Broad classification (e.g., `Resource`, `Storage`, `Network`).                                       | `"Storage"`                                                                                     |
| `subtype`          | Specific variant (e.g., `snapshot_bloat`, `cpu_throttling`).                                        | `"snapshot_bloat"`                                                                              |
| `impact`           | Severity (Critical/Low/Medium) and impact description.                                               | `"Medium: Slower VM performance, potential storage exhaustion."`                               |
| `mitigation`       | Recommended action (e.g., enable auto-scaling, use thick provisioning).                             | `"Delete unused snapshots quarterly; enable CPU governor."`                                    |
| `hypervisor`       | Affects which platforms/vendors (e.g., `VMware`, `AWS`, `Hyper-V`).                                  | `"VMware, AWS EC2"`                                                                             |
| `os_family`        | Operating system (e.g., `Linux`, `Windows`).                                                         | `"Linux (RHEL, Ubuntu)"`                                                                         |
| `prerequisite`     | Required tools/configs (e.g., `Hypervisor CLI`, `PowerShell`).                                        | `"PowerShell 7.0+, VMware Tools installed."`                                                   |
| `references`       | Links to vendor docs/whitepapers.                                                                     | `[VMware KB 10220](https://kb.vmware.com/s/article/10220)`                                     |

**Example JSON Entry:**
```json
{
  "id": "gotcha_001",
  "category": "Storage",
  "subtype": "snapshot_bloat",
  "impact": {
    "severity": "Medium",
    "description": "Large snapshots slow down VMs and consume host storage."
  },
  "mitigation": [
    "Use thin provisioning sparingly.",
    "Schedule snapshot cleanup via automation (e.g., Terraform)."
  ],
  "hypervisor": ["VMware", "Hyper-V"],
  "os_family": ["Linux", "Windows"],
  "prerequisite": "VMware Converter/CLI",
  "references": ["VMware Snapshot Best Practices"]
}
```

---

## **3. Query Examples**
### **A. Find All Gotchas Affecting Windows VMs on Azure**
**Query (SQL-like pseudocode):**
```sql
SELECT *
FROM vm_gotchas
WHERE os_family = 'Windows'
  AND hypervisor IN ('AWS', 'Azure');
```
**Expected Output:**
| `subtype`         | `impact`                                                                 | `mitigation`                          |
|-------------------|--------------------------------------------------------------------------|---------------------------------------|
| `credential_reuse` | Critical: Default credentials exposed.                                   | Rotate passwords via Azure AD.       |
| `disk_resizing`    | Medium: Resizing requires offline state.                                 | Stop VM > resize > reboot.             |

---

### **B. List Gotchas with High Storage Impact**
**Query:**
```sql
SELECT *
FROM vm_gotchas
WHERE impact.severity = 'Critical'
  AND category = 'Storage';
```
**Output:**
| `subtype`         | `impact`                                                                 | `mitigation`                          |
|-------------------|--------------------------------------------------------------------------|---------------------------------------|
| `snapshot_bloat`  | Critical: Storage exhaustion risk.                                       | Enable snapshot retention policies.   |
| `thin_provisioning`| High: IOPS throttling under load.                                       | Use thick provisioning for I/O-critical VMs. |

---

### **C. Filter Gotchas by Hypervisor (CLI)**
**Bash Example (using `jq`):**
```bash
jq '.[] | select(.hypervisor | contains("AWS"))' vm_gotchas.json | grep -E 'subtype|impact'
```
**Output:**
```
  "subtype": "ebs_io_limit",
  "impact": {
    "severity": "Medium",
    "description": "EBS volumes hit burst limits during peak traffic."
  },
```

---

## **4. Mitigation Strategies**
### **Proactive Measures**
| **Gotcha**               | **Mitigation**                                                                                     | **Tools/Automation**                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| CPU Overcommitment        | Use **CPU reservations** or **CPU governor** in virtualization software (e.g., VMware’s "Host CPU Limits"). | Terraform `vm.cpu_reservation`, Kubernetes `resource.requests`.                       |
| Snapshot Bloat            | Schedule **automated cleanup** with retention policies (e.g., delete snapshots >30 days old).    | Ansible playbooks, VMware vCenter API scripts.                                          |
| Disk Resizing             | Plan resizes during **off-peak hours**; test resize procedures.                                  | Cloud-init scripts, `growpart` (Linux), `Resize-VMHardDisk` (PowerShell).               |
| Credential Reuse          | Enforce **password rotation** and disable default accounts (e.g., `vmadmin`).                  | Azure AD, HashiCorp Vault, OpenSSH `PAM` modules.                                       |
| Floating IP Leaks         | **Tag VMs** with lifecycle ownership; use IP whitelisting.                                         | AWS Resource Groups, Terraform `tags`.                                                  |

---

### **Reactive Measures**
| **Symptom**               | **Diagnosis**                                                                                     | **Action**                                                                                   |
|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| VM freezes under load     | Check `top`/`htop` for CPU/memory swapping; review hypervisor logs.                              | Increase memory/reservations or upgrade VM tier.                                             |
| Slow disk I/O             | Monitor `iostat`; check for thin-provisioning alerts in cloud console.                           | Switch to thick provisioning or upgrade storage tier.                                       |
| Network unreachable       | Verify MAC address conflicts (e.g., `ip neigh`); check firewall rules.                           | Reassign MAC address or reboot VM.                                                          |
| High snapshot overhead    | Use `vmware-cmd` to list snapshots; check disk space (`df -h`).                                   | Consolidate snapshots or delete unused ones.                                                |

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **Use Case**                                                                                 |
|---------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **[Isolation via Containers]**  | Use lightweight containers (e.g., Docker, Kubernetes) instead of VMs for stateless workloads.       | Microservices, CI/CD pipelines.                                                              |
| **[Immutable Infrastructure]**  | Treat VMs as disposable; rebuild from golden images on changes.                                      | DevOps pipelines, ephemeral workloads.                                                       |
| **[Resource Quotas]**           | Enforce CPU/memory limits per VM or user group.                                                   | Shared environments (e.g., labs, test teams).                                               |
| **[Disaster Recovery (DR)]**   | Implement **backup snapshots + cross-region replication** for VMs.                                  | High-availability requirements (e.g., databases, APIs).                                     |
| **[Hypervisor Comparison]**     | Understand tradeoffs between VMware (enterprise), Hyper-V (Windows-centric), and KVM (Linux).     | Choosing a hypervisor for specific OS/performance needs.                                       |

---

## **6. Hypervisor-Specific Notes**
### **VMware**
- **Gotcha:** VMware Tools must be installed for dynamic memory/snapshots to work.
  **Fix:** Use `ovftool` for automated provisioning.
- **Gotcha:** Nested virtualization requires `vmx` flag in `.vmx` config.
  **Fix:** Enable in BIOS or via `vmware -nested`.

### **AWS EC2**
- **Gotcha:** EBS volumes detach during `stop`; snapshots are point-in-time.
  **Fix:** Use **Amazon Machine Image (AMI)** for full backups.
- **Gotcha:** NVMe instances lack **EBS-optimized** networking by default.
  **Fix:** Enable `ebs-optimized` flag during launch.

### **Azure VMs**
- **Gotcha:** Managed Disks **cannot** be resized online (unlike EBS).
  **Fix:** Stop VM > resize > restart.
- **Gotcha:** **PV Disks** (Premium SSD) have different I/O caps than Standard SSDs.
  **Fix:** Use **Premium SSD v2** for high-throughput workloads.

### **KVM/QEMU**
- **Gotcha:** Live migration (`migrate`) may corrupt disks if storage is shared.
  **Fix:** Enable `virtio-scsi` for better compatibility.
- **Gotcha:** `qcow2` images bloat over time; convert to `raw` for performance.
  **Fix:** Use `qemu-img convert -O raw`.

---

## **7. Checklist for VM Deployment**
Use this to audit VM deployments for common gotchas:
1. [ ] **Resource Allocation:**
   - CPU/memory reservations enabled?
   - Swap space configured (if OS requires it)?
2. [ ] **Storage:**
   - Disk type (thin/thick) matches workload?
   - Snapshots scheduled for cleanup?
3. [ ] **Networking:**
   - Firewall rules allow VM-to-VM traffic?
   - MAC address conflicts checked?
4. [ ] **Security:**
   - Default credentials rotated?
   - Guest OS up-to-date?
5. [ ] **Backups:**
   - Snapshots or AMIs created post-deployment?
   - Backup retention policy enforced?

---
**Last Updated:** `2023-10-01`
**Contributors:** [List names/links to docs teams]