---
**[Pattern] Virtual Machines (VMs) Reference Guide**
*Version 1.0 | Last Updated: [Date]*

---

### **1. Overview**
The **Virtual Machines (VMs) Pattern** defines a software abstraction where isolated guest operating systems (OS) run on top of a **host system** via a **hypervisor**. This pattern is used for:
- **Resource isolation** (CPU, memory, networking, storage).
- **Cost efficiency** (shared hardware, reduced physical server count).
- **Flexibility** (rapid OS deployment, sandboxing, and testing).
- **High availability** (live migration, failover support).

VMs are categorized by **hypervisor type**:
- **Type 1 (Bare-Metal):** Runs directly on hardware (e.g., VMware ESXi, Microsoft Hyper-V, Nutanix AHV).
- **Type 2 (Hosted):** Runs on top of a host OS (e.g., VirtualBox, Oracle VM VirtualBox).
- **Cloud-Native:** Managed by cloud providers (e.g., AWS EC2, Azure VMs, GCP Compute Engine).

---

### **2. Key Concepts & Implementation Details**

#### **Core Components**
| **Component**          | **Description**                                                                                     | **Example Technologies**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Hypervisor**         | Virtualizes hardware, manages VM lifecycles.                                                     | VMware vSphere, KVM, Hyper-V, Xen                 |
| **Guest OS**           | Isolated OS instance running inside a VM.                                                          | Linux (Ubuntu, CentOS), Windows Server, FreeBSD   |
| **Virtualized Resources** | Abstracted hardware (CPU, RAM, disk, network).                                                   | vCPU, vRAM, vDisk, Virtual NICs                   |
| **Storage Backend**    | Underlying storage for VM disks (local, network, cloud).                                           | NFS, iSCSI, SAN, AWS EBS, Azure Disk Storage     |
| **Networking**         | Virtual interfaces (vNICs) and routing between VMs/host.                                           | Virtual Switches (vSwitch), NAT, Bridged Mode     |
| **Snapshot**           | Point-in-time copy of a VM’s state (disk + memory).                                              | VMware Snapshot, KVM QEMU Snapshot                |
| **Template**           | Pre-configured VM (e.g., base OS image) for cloning.                                             | Ubuntu 22.04 LTS Template, Windows Server ISO    |
| **Live Migration**     | Seamless VM relocation without downtime (requires shared storage).                                | VMware vMotion, KVM Migration                     |
| **Resource Pool**      | Group of VMs sharing allocated hardware resources.                                                  | ESXi Resource Pool, Azure Availability Set        |
| **Security**           | Isolation via **separation kernel** (Type 1) or **VM escape** protections.                         | TPM 2.0, SELinux, Guest Isolation Policies       |

---

#### **Implementation Scenarios**
| **Scenario**               | **Use Case**                                                                                     | **Hypervisor Choice**          | **Key Configurations**                     |
|----------------------------|-------------------------------------------------------------------------------------------------|---------------------------------|---------------------------------------------|
| **Server Consolidation**   | Reduce physical servers by virtualizing workloads.                                              | ESXi, Hyper-V                    | vCPU Cores, RAM Allocation, Shared Storage  |
| **Development/Testing**    | Isolated dev environments without affecting production.                                          | VirtualBox, KVM                  | Snapshots, Clone Templates, NAT Networking   |
| **Disaster Recovery**      | Failover VMs to secondary sites with minimal downtime.                                           | VMware vSphere, Nutanix AHV      | Replication, vMotion, Live Migration       |
| **Containers as VMs**      | Legacy apps requiring full OS isolation (e.g., .NET Framework).                                | KVM, Hyper-V                     | Lightweight VMs, Paravirtualization         |
| **Cloud Migration**        | Lift-and-shift workloads to cloud platforms.                                                    | AWS EC2, Azure VMs              | EBS Snapshots, VNet Integration, Auto-Scaling|
| **Guest Sandboxing**       | Run untrusted code (e.g., malware analysis) in isolated VMs.                                    | VirtualBox, QEMU/KVM             | Full Disk Encryption, Read-Only Mode        |

---

### **3. Schema Reference**
Below are **core schemas** for VM configurations and management.

#### **A. VM Instance Definition**
```json
{
  "vm_id": "vm-12345",
  "name": "web-server-01",
  "hypervisor_type": "Type1",
  "guest_os": "Ubuntu 22.04 LTS",
  "cpu": {
    "sockets": 1,
    "cores_per_socket": 2,
    "threads_per_core": 1,
    "reservation": 1000MHz,
    "limit": 2500MHz
  },
  "memory": {
    "size_mb": 4096,
    "ballooning": true,
    "hot_add": true
  },
  "disks": [
    {
      "disk_id": "disk-001",
      "path": "/vmfs/volumes/datastore1/web-server-01.vmdk",
      "size_gb": 50,
      "controller_type": "SCSI",
      "bootable": true
    },
    {
      "disk_id": "disk-002",
      "path": "nfs://192.168.1.100/vms/shared-data.vhdx",
      "size_gb": 20,
      "read_only": true
    }
  ],
  "network_interfaces": [
    {
      "nic_id": "nic-main",
      "mac_address": "00:50:56:ab:cd:ef",
      "network": "VM_Network_LAN",
      "ip_address": "192.168.1.50/24",
      "connected": true
    }
  ],
  "snapshots": [
    {
      "snapshot_id": "snapshot-001",
      "description": "Pre-update baseline",
      "timestamp": "2023-10-15T10:00:00Z"
    }
  ],
  "templates": ["ubuntu-22.04-base"],
  "tags": ["web-tier", "production"]
}
```

#### **B. Hypervisor Cluster Configuration**
```json
{
  "cluster_id": "cluster-001",
  "hosts": [
    {
      "host_id": "host-001",
      "ip_address": "10.0.0.1",
      "cpu": { "cores": 32, "threads": 64 },
      "memory_gb": 256,
      "storage_path": "/vmfs/volumes/datastore1",
      "status": "online"
    },
    {
      "host_id": "host-002",
      "ip_address": "10.0.0.2",
      "cpu": { "cores": 16, "threads": 32 },
      "memory_gb": 128,
      "storage_path": "nfs://192.168.1.100/cluster_storage",
      "status": "maintenance"
    }
  ],
  "resource_pool": {
    "name": "web-tier-pool",
    "cpu_reservation_mhz": 5000,
    "memory_reservation_gb": 20,
    "expandable": true
  },
  "drs_settings": {
    "enabled": true,
    "cpu_load_threshold": 80,
    "memory_load_threshold": 75
  }
}
```

#### **C. Network Configuration**
```json
{
  "network_id": "vm_network_lan",
  "type": "Distributed_vSwitch",
  "port_group": "web-tier-pg",
  "vlan_id": 10,
  "mtu": 1500,
  "ip_range": {
    "start": "192.168.1.50",
    "end": "192.168.1.254",
    "gateway": "192.168.1.1"
  },
  "dns_servers": ["8.8.8.8", "1.1.1.1"],
  "connected_hosts": [
    "host-001",
    "host-002"
  ]
}
```

---

### **4. Query Examples**
Below are **CLI/API examples** for common VM operations across hypervisors.

#### **A. List VMs (vSphere CLI)**
```bash
# List all VMs in a vCenter inventory
vim-cmd vmsvc/getallvms
```
**Output:**
```
VM Name (ID)   State     IP Address   Guest OS
------------------------------
web-server-01  poweredOn  192.168.1.50 Ubuntu 22.04
db-server-01   poweredOff  -           Windows Server 2019
```

#### **B. Start a VM (AWS CLI)**
```bash
aws ec2 start-instances --instance-ids i-0123456789abcdef0
```
**Response:**
```json
{
  "StartingInstances": [
    {
      "InstanceId": "i-0123456789abcdef0",
      "CurrentState": {
        "Name": "running",
        "Code": 16
      }
    }
  ]
}
```

#### **C. Create a VM Snapshot (KVM/QEMU)**
```bash
# Stop the VM first
virsh shutdown web-server-01

# Create snapshot
virsh snapshot-create-as web-server-01 "pre-deploy-snapshot" --description "Backup before config changes"
```
**Output:**
```
Snapshot web-server-01 created
```

#### **D. Live Migration (VMware PowerCLI)**
```powershell
# Enable enhanced vMotion compatibility (if not already)
Set-VM -Name web-server-01 -EnhancedMigrationEnabled $true

# Perform live migration to another host
Move-VM -Name web-server-01 -Destination $host2 -Confirm:$false
```

#### **E. Check Disk Usage (Azure CLI)**
```bash
az vm show --name web-server-01 --resource-group myRG --query "storageProfile.dataDisks[].vhd.diskSizeGb" --output table
```
**Output:**
```
DiskSizeGb
-----------
50
20
```

#### **F. Clone a VM (VirtualBox API)**
```bash
# Clone a VM with mac address modification
VBoxManage clonehd "Original.vdi" "Cloned.vdi" --format VDI --register
VBoxManage clonevm "Original-VM" --name "Cloned-VM" --register
VBoxManage modifyvm "Cloned-VM" --macaddress1 auto
```

---

### **5. Related Patterns**
To complement **Virtual Machines**, consider these patterns for **performance, security, or orchestration**:

| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Containerization](link)**     | Lightweight OS-level virtualization (e.g., Docker, Kubernetes) instead of full VMs.               | Microservices, CI/CD pipelines, cloud-native apps.                             |
| **[Live Migration](link)**      | Zero-downtime VM relocation across hosts/storages.                                                  | High-availability clusters, disaster recovery.                                  |
| **[Resource Pooling](link)**    | Group VMs to share allocated CPU/memory dynamically.                                                 | Cloud environments, auto-scaling workloads.                                    |
| **[Security Hardening](link)**  | Isolate VMs with micro-segmentation, encryption, and least-privilege access.                     | Compliance (PCI-DSS, HIPAA), sensitive workloads.                              |
| **[Orchestration (K8s)](link)** | Manage VMs/containers with Kubernetes (e.g., VMs as "bare metal" nodes).                          | Hybrid cloud, multi-cloud deployments.                                         |
| **[Storage Tiering](link)**     | Tier VM disks between fast (SSD) and slow (HDD) storage based on access patterns.                 | Cost optimization for low-traffic VMs.                                          |
| **[Disaster Recovery](link)**   | Replicate VMs to remote sites with RPO/RTO requirements.                                            | Critical production workloads.                                                 |

---

### **6. Best Practices**
1. **Resource Allocation:**
   - Over-provision **CPU/RAM** by 10–20% for burst workloads.
   - Use **reservation limits** to prevent VM overload.

2. **Storage:**
   - **Thin provisioning** for uninitialized disks (saves space initially).
   - **Thick provisioning** for performance-critical VMs (e.g., databases).

3. **Networking:**
   - **vSwitch uplinks:** Use **Load Balancing** (Active/Standby) for redundant NICs.
   - **VLANs:** Isolate VM traffic (e.g., separate VLANs for DBs vs. web servers).

4. **Security:**
   - **Enable TPM 2.0** for VMs requiring secure boot.
   - **Disable unnecessary services** in guest OS (e.g., RDP if not needed).
   - **Use VMware Tools/Agent** for patch management.

5. **Backup:**
   - Schedule **automated snapshots** for critical VMs.
   - Test **restore procedures** regularly.

6. **Performance Tuning:**
   - **Ballooning:** Dynamically reclaim unused RAM.
   - **Memory overcommit:** Monitor with tools like `vmstat` (Linux) or **vSphere Performance Charts**.

7. **Cost Optimization:**
   - **Right-size VMs** (e.g., move small workloads to **nano/instanced VMs**).
   - **Auto-scaling:** Use cloud provider tools (e.g., AWS Auto Scaling).

---
**See Also:**
- [Hypervisor-Specific Guides](link)
- [VM Performance Benchmarking](link)
- [Legacy App Migration to VMs](link)