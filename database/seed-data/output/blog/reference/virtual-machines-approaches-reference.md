# **[Pattern] Virtual Machines (VM) Approaches – Reference Guide**

---

## **1. Overview**
The **Virtual Machines (VM) Approaches** pattern abstracts physical hardware resources into isolated, emulated environments (virtual machines). This enables **resource multiplexing, cross-platform compatibility, isolation, and simplified management** of computing workloads. Common use cases include:

- **Isolation**: Running untrusted or legacy applications without affecting the host system.
- **Testing & Development**: Deploying different OS versions or dependencies without modifying the host.
- **Resource Efficiency**: Consolidating multiple workloads onto fewer physical machines.
- **Disaster Recovery & Migration**: Quickly rebuilding environments post-failure.

VMs are typically managed via hypervisors (e.g., **Type 1**: VMware ESXi, Microsoft Hyper-V, Xen; **Type 2**: VirtualBox, VMware Workstation). Key trade-offs include **performance overhead** (vs. native containers) and **resource consumption** (vs. lightweight alternatives like Docker).

---

## **2. Schema Reference**
Below is a structured breakdown of **Virtual Machines (VM) Approaches**, covering core components, configurations, and interactions.

| **Category**               | **Attribute**               | **Description**                                                                                     | **Example Values/Options**                                                                                     | **Notes**                                                                                     |
|----------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Virtual Machine (VM)**   | `Name`                      | Unique identifier for the VM.                                                                       | `web-server-vm`, `dev-db-vm`                                                                                 | Must be alphanumeric, no spaces.                                                                |
|                            | `OS Type`                   | Guest OS installed in the VM.                                                                      | `Windows 10`, `Ubuntu 22.04`, `CentOS 7`                                                              | Affects driver compatibility and performance.                                                   |
|                            | `Hypervisor`                | Software managing the VM.                                                                         | VMware ESXi, Microsoft Hyper-V, KVM (Linux), VirtualBox (Desktop)                                       | Type 1 hypervisors (bare-metal) offer better performance than Type 2.                            |
|                            | `CPU Cores/Threads`         | Allocated virtual CPUs (vCPUs).                                                                  | `2`, `4 (2 vCPUs, 2 threads each)`                                                                      | Over-provisioning may degrade performance; use CPU throttling for dynamic allocation.             |
|                            | `Memory (RAM)`              | Memory allocated to the VM (GB).                                                                   | `4`, `8`, `16`                                                                                             | Minimum: 2GB (basic OS); add 1GB per active application.                                         |
|                            | `Storage (Disk)**          | Virtual disk(s) attached to the VM.                                                                | `100GB SSD`, `500GB HDD (thin provisioned)`                                                             | Thin provisioning saves space but may slow down if disk grows.                                    |
|                            | `Network Interface`         | Network type (NAT, Bridged, Host-only, Custom).                                                      | NAT (default), Bridged (direct LAN access), Host-only (isolated)                                       | Bridged mode requires physical NIC configuration.                                                |
|                            | `Snapshots`                 | Saved VM states for rollback or experimentation.                                                   | `Pre-install`, `Post-upgrade`, `Debug-build`                                                          | Unlimited snapshots may bloat storage; clean up unused ones.                                      |
|                            | `Isolation Level`           | Security/sandboxing mode (e.g., SELinux, Firewall Rules).                                          | `Default`, `Strict`, `Custom (Firewall Ports: 80, 443)`                                                | Higher isolation increases overhead.                                                          |
|                            | `Shared Resources`          | Resource sharing rules (e.g., storage NFS, GPU passthrough).                                       | `Shared NFS Drive`, `Passthrough NVIDIA GPU`                                                          | Requires hypervisor support and proper configuration.                                           |
|                            | `Automation Profile`        | Scripts/configs for VM provisioning (e.g., Ansible, Terraform).                                    | `Terraform HCL`, `Puppet Manifest`                                                                       | Use for repeatable deployments.                                                                |
| **Hypervisor**             | `Type`                      | Hypervisor classification (Type 1/Type 2).                                                          | Type 1 (ESXi, Hyper-V), Type 2 (VirtualBox, VMware Workstation)                                         | Type 1: Better performance; Type 2: Easier for development.                                      |
|                            | `Host OS`                   | OS running the hypervisor.                                                                        | `Linux (Ubuntu 22.04)`, `Windows Server 2022`                                                            | Must support the hypervisor (e.g., KVM requires Linux).                                          |
|                            | `Resource Limits`           | CPU/Memory caps for the hypervisor host.                                                            | `Max CPU: 32 cores`, `Max RAM: 128GB`                                                                   | Prevents host instability during VM overload.                                                    |
|                            | `Live Migration`           | Ability to move running VMs between hosts without downtime.                                        | `Enabled`, `Disabled`                                                                                     | Requires shared storage (e.g., iSCSI, NFS) and network latency < 10ms.                           |
| **Storage Backend**        | `Type`                      | Storage method for VM disks.                                                                        | SATA (HDD), NVMe, iSCSI, NFS, Cloud (AWS EBS, Azure Disk)                                              | NVMe offers best performance; iSCSI/NFS requires network configuration.                           |
|                            | `Provisioning Method`       | How disk space is allocated.                                                                       | Thick (pre-allocated), Thin (on-demand)                                                                 | Thin: Space-efficient but slower initial I/O.                                                   |
|                            | `Storage Tiering`           | Multi-tier storage (e.g., SSD for OS, HDD for logs).                                               | `SSD (OS: 50GB), HDD (Data: 500GB)`                                                                    | Use for cost-performance balance.                                                              |
| **Networking**             | `Network Mode`              | VM network connectivity type.                                                                      | NAT, Bridged, Host-only, Custom (VLAN)                                                                  | Bridged: VM appears as physical device on LAN.                                                   |
|                            | `Firewall Rules`            | Port forwarding/whitelisting.                                                                     | `80:TCP`, `443:TCP`, `All ICMP`                                                                         | Default: Close all ports; enable only necessary ones.                                            |
|                            | `MAC Address`               | Virtual NIC identifier.                                                                           | Auto-generated (e.g., `00:0C:29:XX:XX:XX`)                                                             | Use static MACs for predictable networking.                                                      |
| **Performance Tuning**    | `CPU Pinning`               | Assign physical CPU cores to vCPUs.                                                                  | `vCPU0 → Core1`, `vCPU1 → Core2`                                                                          | Reduces latency for latency-sensitive apps (e.g., databases).                                    |
|                            | `Memory Overcommit`         | Allow VMs to use more RAM than allocated (risky).                                                   | `Enabled (1.5x)`, `Disabled`                                                                             | Use cautiously; can cause host OOM crashes.                                                     |
|                            | `Disk Cache`                | Caching strategy for VM disks.                                                                     | `Write-back`, `Write-through`, `None`                                                                   | Write-back: Faster but risks data loss on host crash.                                             |
| **Lifecycle Management**  | `Startup Mode`              | How the VM boots.                                                                        | Automatically, Manually, Never                                                                             | Use "Automatic" for critical services; "Manual" for dev/test.                                     |
|                            | `Backup Policy`             | VM backup schedule/frequency.                                                                    | Daily (7-day retention), Weekly (4-week retention)                                                    | Integrate with tools like Veeam, Hyper-V Backup.                                                |
|                            | `Shutdown Behavior`         | Action when host reboots.                                                                        | `Save State`, `Shutdown`, `Hibernate`                                                                   | "Save State" for quick resume; "Shutdown" for clean VM state.                                    |
| **Security**               | `Encryption`                | Disk/VM encryption.                                                                               | `AES-256 (LUKS for Linux)`, `BitLocker (Windows)`                                                      | Enable for sensitive data; adds ~5-10% overhead.                                                |
|                            | `UEFI/BIOS Mode`            | Firmware mode for the VM.                                                                         | UEFI (modern), Legacy (BIOS)                                                                             | UEFI: Better security (Secure Boot); Legacy: Compatibility with old OS.                           |
|                            | `Guest OS Hardening`        | Security settings in the VM.                                                                        | Disabled, `Basic (firewall enabled)`, `Strict (no services exposed)`                                  | Follow CIS benchmarks for OS hardening.                                                        |

---

## **3. Query Examples**
Below are **CLI and API examples** for common VM operations across hypervisors.

---

### **3.1 VM Creation**
#### **VMware ESXi (vSphere API - PowerCLI)**
```powershell
# Create a VM with 2 vCPUs, 4GB RAM, and 50GB disk
New-VM -Name "web-server" -VMHost "esxi-host" -ResourcePool "Default" `
 -MemoryGB 4 -NumCpu 2 -DiskGB 50 -Location "datastore1" `
 -GuestOS "otherGuestLinux64Guest" -NetworkName "VM Network"
```

#### **Proxmox VE (REST API)**
```bash
# Create a VM with LXC container (lightweight alternative)
curl -X PUT "https://<proxmox-url>/api2/json/nodes/<node>/lxc/<ctid>/config" \
  -H "Authorization: PVEAPIToken=NAME=<token>USERID=<user>TKT=<ticket>" \
  -H "Content-Type: application/json" \
  -d '{
    "ostemplate": "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.gz",
    "rootfs": "local-lvm:vm-100-disk-0",
    "hostname": "web-server",
    "unprivileged": 1,
    "memory": 4096,
    "swap": 1024,
    "cores": 2,
    "onboot": 1
  }'
```

---

### **3.2 VM Configuration**
#### **Modify Memory (KVM/qemu - virsh)**
```bash
# Resize a VM's memory to 8GB
virsh setvcpumemory "web-server-vm" --memory 8192 --config
```

#### **Attach a New Disk (VirtualBox)**
```bash
# Add a 100GB SATA disk to a running VM
VBoxManage modifyhd "web-server-vm.vmdk" --resize 100000
VBoxManage storagectl "web-server-vm" --name "SATA" --add sata
VBoxManage storageattach "web-server-vm" --storagectl "SATA" --port 1 --device 0 --type hdd --medium "new_disk.vdi"
```

---

### **3.3 Networking**
#### **Bridged Mode (VirtualBox)**
```bash
# Configure VM to use bridged networking
VBoxManage modifyvm "web-server-vm" --nic1 bridged --bridgeadapter1 "enp3s0"
```

#### **Port Forwarding (Proxmox)**
```bash
# Forward host port 8080 to VM's port 80
pct set <ctid> -net0 name=eth0,bridge=vmbr0,firewall=1,ip=dhcp,routes=,gw=,nameserver=,nopromisc=0,noslave=0,vlan=0,bridge_ports=,host_bridge=1,host_iface=,host_ip=,ipv6=ignore,ipv6gw=,ipv6nameserver=,ipv6dhcp=0,ipv6acceptra=0,ipv6acceptra_override=0,ipv6privacy=0
qm set <vmid> -net0 name=eth0,bridge=vmbr0,firewall=1,ip=dhcp,routes=8080:tcp:0.0.0.0:80,firewall_rules=1
```

---

### **3.4 Snapshots**
#### **Create a Snapshot (VMware ESXi)**
```powershell
# Take a snapshot of a VM
New-VMSnapshot -VM "web-server" -Name "Pre-update" -Description "Before OS upgrade" -Memory
```

#### **Restore from Snapshot (KVM)**
```bash
# Revert a VM to a snapshot
virsh snapshot-revert "web-server-vm" --snapshotname "Pre-update"
```

---

### **3.5 Performance Monitoring**
#### **Check CPU Stats (Hyper-V)**
```powershell
# Get VM CPU usage
Get-VM -Name "web-server" | Get-VMProcessor | Measure-Object -Property Usage -Average
```

#### **Disk I/O Latency (Proxmox)**
```bash
# Monitor VM disk latency
pvesh get /cluster/perf/vm/<vmid>/disk/io
```

---

## **4. Related Patterns**
To complement **Virtual Machines**, consider these patterns for **enhanced isolation, portability, or efficiency**:

| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     | **Trade-offs**                                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Containerization](https://example.com/containerization)** | Lightweight OS-level virtualization (e.g., Docker, LXC).                                           | For microservices, CI/CD pipelines, or when VM overhead is prohibitive.                               | Less isolation than VMs; not suitable for untrusted workloads.                                      |
| **[Live Migration](https://example.com/live-migration)**     | Seamlessly move running VMs between hosts.                                                          | High-availability clusters, cloud bursting, or hardware maintenance.                                    | Requires shared storage and low-latency networks.                                                  |
| **[ Immutable Infrastructure](https://example.com/immutable-infra)** | Treat VMs as ephemeral; rebuild from templates on change.                                           | DevOps environments, infrastructure-as-code (IaC) deployments.                                        | Higher operational overhead for rebuilds.                                                          |
| **[Serverless (VM-backed)](https://example.com/serverless)** | Dynamic VM allocation (e.g., AWS EC2 Spot Instances).                                               | Bursty workloads where manual scaling is impractical.                                                 | Higher cost for short-lived workloads; cold starts possible.                                        |
| **[Hyperconverged Infrastructure](https://example.com/hyperconverged)** | Combine compute, storage, and networking in a single VM.                                           | Converged IT environments with limited hardware.                                                     | Vendor lock-in; complexity in management.                                                            |
| **[Security Hardening](https://example.com/security-hardening)** | Apply CIS benchmarks or OS-level security policies to VMs.                                         | Compliance-sensitive environments (finance, healthcare).                                             | Requires expertise; may impact performance if over-configured.                                    |
| **[Network Isolation (VLANs)](https://example.com/network-isolation)** | Segment VM networks using VLANs or microsegmentation.                                               | Multi-tenant environments or zero-trust architectures.                                               | Increased network complexity; requires proper tagging.                                             |

---

## **5. Best Practices**
1. **Resource Allocation**:
   - Start with **50% of host resources** for VMs; adjust based on monitoring.
   - Use **CPU throttling** (e.g., `maxCpu` in VMware) to prevent host overload.

2. **Storage**:
   - **SSDs for OS disks**; HDDs for data (if cost is a concern).
   - Enable **thin provisioning** for cost savings, but monitor growth.

3. **Networking**:
   - **Bridged mode** for VMs needing direct LAN access.
   - **Limit exposed ports**; use **firewall rules** to restrict traffic.

4. **Security**:
   - Enable **disk encryption** for sensitive VMs.
   - Use **UEFI + Secure Boot** to prevent bootkit attacks.
   - Regularly **update hypervisor and guest OS**.

5. **Backup**:
   - Implement **automated snapshots** for critical VMs.
   - Test **restore procedures** periodically.

6. **Automation**:
   - Use **Terraform/Ansible** to provision VMs consistently.
   - Script **common tasks** (e.g., `VBoxManage` for VirtualBox).

7. **Performance Tuning**:
   - **Pin vCPUs** to physical cores for latency-sensitive apps.
   - **Ballooning** (e.g., `memoryOverhead` in KVM) can reclaim unused RAM.

8. **Monitoring**:
   - Track **CPU, memory, disk I/O, and network** with tools like:
     - **VMware vCenter** (ESXi)
     - **Hyper-V Manager** (Windows)
     - **Prometheus + Grafana** (custom metrics)
     - **Proxmox Monitoring Plugin**

---
**See Also**:
- [Cloud-Native Virtualization](https://example.com/cloud-native-vm) (for serverless VMs).
- [Hybrid VM/Container Strategies](https://example.com/hybrid-deployment) (combinations of VMs and containers).