# **[Pattern] Virtual Machines Tuning: Reference Guide**

---

## **Overview**
This **Virtual Machines (VM) Tuning Reference Guide** provides a **structured approach** to optimizing VM performance, resource allocation, and operational efficiency in cloud or hybrid environments. VM tuning balances workload demands with host system constraints, ensuring **scalability, cost savings, and high availability**. This guide covers **key configurations, metrics, and best practices** for tuning VMs across hypervisors (VMware, Hyper-V, KVM, Nutanix AHV, etc.) and cloud platforms (AWS, Azure, GCP).

Optimizing VMs involves:
- **CPU, memory, and storage allocation** (vCPU, RAM, disk I/O tuning)
- **Network and I/O optimization** (virtual NICs, storage tiers, QoS policies)
- **Guest OS and hypervisor-level optimizations** (kernel parameters, scheduler tuning)
- **Performance monitoring and adaptive scaling** (auto-scaling policies, throttling)

This guide assumes familiarity with **virtualization fundamentals** and **basic cloud/hypervisor administration**. Adjust configurations based on **workload type** (e.g., database, web server, batch processing).

---

## **Schema Reference**

| **Category**               | **Parameter**                          | **Description**                                                                                     | **Common Values/Ranges**                                                                 | **Default (Example)**                     |
|----------------------------|----------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------|
| **CPU Tuning**             | vCPU (Virtual CPUs)                    | Number of allocated processor cores per VM.                                                          | Depends on workload (e.g., 1–16 vCPUs).                                                   | 2 vCPUs (VMware)                          |
|                            | CPU Shares                              | Relative priority for CPU allocation in shared environments.                                          | 1000–8192 (higher = more priority).                                                      | 1000 (default)                             |
|                            | CPU Limit                               | Hard cap on vCPU usage (prevents overcommitment).                                                    | 0 = no limit; >0 = max allowed (e.g., 8000 MHz).                                           | Unlimited (unless overcommitted)         |
|                            | CPU Pinning (Static Assignment)         | Locks vCPUs to physical cores for predictability (e.g., real-time workloads).                      | Specific core IDs (e.g., `0-3`).                                                          | None (dynamic scheduling)                 |
|                            | NUMA Node Affinity                      | Binds vCPUs to specific NUMA nodes to reduce latency.                                               | Node IDs (e.g., `node0`, `node1`).                                                       | Auto (system-managed)                     |
| **Memory Tuning**          | RAM Allocation                          | Total memory assigned to VM (overallocation may cause ballooning/throttling).                       | GB (e.g., 4–512 GB).                                                                       | 4 GB (Linux VM)                           |
|                            | Memory Overcommit Ratio                 | Allowed ratio of allocated vs. available memory (risk of killswitch or page swapping).             | 1.0–3.0 (e.g., 2.5x).                                                                    | 1.0 (strict)                              |
|                            | Memory Reserved (Balloon Driver)        | Minimum RAM to keep reserved for host OS.                                                            | MB (e.g., 512–4096).                                                                       | 512 MB                                     |
|                            | Memory Swappiness (Guest OS)            | Linux kernel parameter controlling swap usage (0–100).                                               | 10–60 (higher = more swap).                                                              | 60 (default)                               |
| **Storage Tuning**         | Disk Controller                         | Emulated storage controller (e.g., SCSI, SATA, NVMe).                                                | Type (e.g., `lsiblast` for KVM, `Paravirtual` for VMware).                                  | SCSI (default)                             |
|                            | Storage Tier (SSD/HDD)                  | Assigns VM disks to fast (SSD) or slow (HDD) storage tiers.                                           | Tier name (e.g., `ssd-tier-1`).                                                         | Balanced (auto-tiered)                     |
|                            | I/O Schedule (Guest OS)                | Linux scheduler for disk I/O (e.g., `deadline`, `noop`, `cfq`).                                       | Scheduler (e.g., `deadline` for SSDs).                                                    | `deadline` (default)                       |
|                            | Disk I/O Limit                          | Bandwidth throttling for individual disks (KB/s or IOPS).                                             | 1000–100000 (e.g., 10000 for heavy workloads).                                              | Unlimited                                  |
| **Network Tuning**         | vNIC Type                               | Virtual network interface type (e.g., `e1000`, `virtio`).                                              | Type (e.g., `virtio` for Linux, `e1000` for Windows).                                        | `virtio` (Linux) / `e1000` (Windows)       |
|                            | MTU Size                                | Maximum Transmission Unit (increase for Jumbo Frames).                                                | 1500–9000 bytes.                                                                          | 1500                                       |
|                            | Bandwidth Limit                         | Network traffic throttling (KB/s or % of available).                                                 | 10000–10000000 KB/s.                                                                      | Unlimited                                  |
|                            | QoS Policy                              | Quality of Service rules for prioritization (e.g., latency, jitter).                                | Low/Medium/High priority.                                                                | Default (no priority)                      |
| **Guest OS Tuning**        | Kernel Parameters (Linux)               | Tunable parameters via `/etc/sysctl.conf` (e.g., `vm.swappiness`, `net.core.somaxconn`).          | Value range (e.g., `vm.swappiness=10`).                                                   | System-dependent                           |
|                            | Page Cache Tuning                       | Adjusts file system cache behavior (`vm.dirty_ratio`, `vm.dirty_background_ratio`).                  | 10–90% (higher = more cache).                                                             | 10/5 (default)                             |
|                            | Transparent HugePages (THP)             | Enables/disables memory page merging for performance (Linux).                                       | `always`, `never`, `default`.                                                             | `always` (default)                         |
| **Hypervisor-Specific**    | VMware Tools / Agent                    | Refers to VMware’s optimization tools for OS integration.                                             | Status (e.g., `installed`, `outdated`).                                                   | Installed (recommended)                   |
|                            | Hyper-V Enlightened I/O (EIOP)          | Hyper-V feature for reduced I/O latency.                                                            | Enabled/Disabled.                                                                          | Disabled (default)                          |
|                            | KVM Live Migration (Checkpoint)         | Enables/disables qemu-guest-agent for seamless migration.                                           | `on`, `off`.                                                                               | `on` (recommended)                         |
| **Monitoring & Scaling**   | Auto-Scaling Policy                     | Dynamic vCPU/RAM adjustments based on CPU/memory usage.                                              | Rules (e.g., "Scale up if CPU > 80% for 5m").                                              | Static allocation                          |
|                            | Performance Monitor (PM) Alerts         | Thresholds for CPU/memory/storage alerts (e.g., 90% CPU for 1h).                                  | %/Usage thresholds.                                                                        | 70% (default)                              |

---

## **Query Examples**

### **1. CPU Overcommitment Check (VMware)**
```bash
# List all VMs with CPU usage and allocation
esxcli vm process list --type vm | grep -E "Name|CpuUsage|CpuAllocated"
```
**Output Interpretation:**
- **CpuAllocated > CpuUsage (by <10%)**: Safe overcommit.
- **CpuUsage ≈ CpuAllocated**: Risk of throttling; reduce overcommit ratio.

---

### **2. Memory Ballooning Configuration (KVM)**
```bash
# Check memory balloon status of a VM
virsh dommemstat <vm-name> | grep balloon
```
**Adjust Ballooning:**
```xml
<!-- In KVM XML config -->
<memoryBacking>
  <balloon>
    <stats period='60' />
  </balloon>
</memoryBacking>
```

---

### **3. Disk I/O Latency Analysis (Linux Guest)**
```bash
# Check I/O latency and scheduler
iostat -x 1 5
iotop -o  # Monitor disk usage by process
```
**Optimization:**
- If `await` > 100ms, consider:
  - Changing I/O scheduler (`echo "noop" > /sys/block/sdX/queue/scheduler`).
  - Upgrading disk to SSD.

---

### **4. Network Bottleneck Detection (Azure)**
```powershell
# Check NIC utilization in Azure Portal CLI
az vm nic show --name <nic-name> --vm-name <vm-name> --resource-group <rg> --query "networkInterfaceProperties"
```
**Mitigation:**
- Increase MTU to 9000 bytes.
- Enable **Azure Accelerated Networking** for low-latency.

---

### **5. Auto-Scaling Rule (AWS)**
```json
// CloudWatch Events rule for AWS Auto Scaling
{
  "source": ["aws.autoscaling"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": {
    "state": ["running"],
    "instance-type": ["t3.medium", "t3.large"]
  }
}
```
**Tune with:**
```bash
aws autoscaling put-scaling-policy \
  --policy-name CPUScaleUp \
  --scaling-adjustment 1 \
  --auto-scaling-group-name my-asg \
  --adjustment-type ChangeInCapacity
```

---

### **6. Hyper-V CPU Affinity (PowerShell)**
```powershell
# Set CPU affinity for a VM (e.g., cores 2-5)
$vm = Get-VM -Name "MyVM"
$vm | Set-VMAffinity -CoreIds 2,3,4,5
```

---

## **Related Patterns**
To complement **Virtual Machines Tuning**, consider these patterns for holistic optimization:

| **Pattern**                     | **Purpose**                                                                 | **When to Use**                                                                 | **Tools/Platforms**                     |
|----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------|
| **[Resource Overcommitment]**    | Balances host resources across VMs while preventing throttling.             | High-density environments (e.g., Dev/Test labs).                                | VMware, KVM, Nutanix AHV                |
| **[Storage Tiering]**            | Dynamically routes I/O to optimal storage (SSD vs. HDD).                    | Mixed workloads (e.g., databases + file servers).                                | AWS EBS Multi-AZ, Azure Managed Disks   |
| **[Network Load Balancing]**     | Distributes traffic across VMs for high availability.                        | Web servers, APIs, or stateless applications.                                   | NLB in AWS, Azure Load Balancer         |
| **[Live Migration Optimization]**| Minimizes downtime during VM migration (e.g., maintenance).                 | Critical production workloads with SLA requirements.                            | VMware vMotion, Hyper-V EVAC           |
| **[Guest OS Optimization]**      | Configures OS-level settings for performance (e.g., kernel tuning).        | Linux/Windows VMs with high I/O or CPU workloads.                               | Linux `sysctl`, Windows `bcdedit`       |
| **[Cold Start Mitigation]**      | Reduces latency for ephemeral VMs (e.g., serverless).                      | Cloud-native apps (e.g., AWS Lambda, Azure Functions).                          | AWS Provisioned Concurrency, GCP Warmup |
| **[Security Hardening]**         | Isolates VMs with minimal attack surface (e.g., no balloons, seccomp).     | Secure environments (e.g., finance, healthcare).                                | VMware Security Configurations, `seccomp`|

---

## **Best Practices Summary**
1. **Right-Size VMs**:
   - Use **cloud provider’s "Right Sizing" tools** (e.g., AWS Compute Optimizer).
   - Avoid over-provisioning (cost) or under-provisioning (throttling).

2. **Monitor proactively**:
   - Track **CPU steal time**, **memory ballooning**, and **disk latency**.
   - Set alerts for **90%+ CPU/memory usage** for 15+ minutes.

3. **Isolate critical workloads**:
   - Use **dedicated hosts** or **isolated VMs** for latency-sensitive apps.

4. **Update hypervisor/guest tools**:
   - Ensure **VMware Tools**, **Hyper-V Integration Services**, or **KVM qemu-guest-agent** are current.

5. **Leverage cloud-specific features**:
   - **AWS**: Enhanced Networking (ENA/SR-IOV).
   - **Azure**: Dedicated Hosts for multi-tenancy isolation.
   - **GCP**: Persistent Disk Auto-Tiering.

6. **Test changes in staging**:
   - Always validate tuning in a **non-production environment** before applying to live VMs.

7. **Document tuning rules**:
   - Maintain a **runbook** for CPU/RAM limits, I/O policies, and auto-scaling rules.

---
**Note**: Adjust values based on **workload patterns** (e.g., burstable vs. steady-state). For databases, prioritize **storage latency**; for web servers, focus on **network throughput**.