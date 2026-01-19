# **[Pattern] Virtual Machines Troubleshooting Reference Guide**

---

## **Overview**
This reference guide provides a structured approach to diagnosing and resolving common issues in virtualized environments. It covers core components of virtual machine (VM) infrastructure—**hosts, hypervisors, virtual networks, storage, and VM lifecycles**—with diagnostic steps, tools, and best practices for **on-premises (VMware, Hyper-V, KVM) and cloud-based (AWS EC2, Azure VMs, GCP Compute Engine)** deployments. The guide emphasizes **log analysis, resource monitoring, and configuration validation**, ensuring alignment with ITIL and DevOps troubleshooting methodologies.

---

## **Schema Reference**
Below are standardized troubleshooting categories with key attributes for root-cause analysis.

| **Category**               | **Subcategory**               | **Key Attributes**                                                                 | **Common Tools/Commands**                          |
|----------------------------|--------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------|
| **Host/Hypervisor**        | Resource Allocation           | CPU, Memory, Disk I/O, Network Bandwidth, Utilization (%)                          | `vmstat`, `iostat`, `htop`, Hypervisor CLI (`esxcli`, `virsh`) |
|                            | Service Status                | Hypervisor Agent, Time Sync, Firewall Rules, Kernel Logs                           | `systemctl`, `journalctl`, `netstat`, `ss`        |
| **Virtual Networking**     | Connectivity Issues           | IP Assignment, VLANs, NAT/Routing, DNS Resolution, ARP Cache                        | `ping`, `traceroute`, `ipconfig`, `tcpdump`      |
|                            | Performance Bottlenecks       | Packet Drops, Latency, MTU Size, VXLAN/GRE Tunnels                               | `mtr`, `nload`, `ethtool`, `tcpdump`              |
| **Storage**                | Availability/Throttling       | Disk Latency, I/O Queue Depth, SAN/NAS Failures, Storage Tier Usage               | `fio`, `iotop`, `lsscsi`, `multipath`             |
|                            | Configuration Errors          | VMFS/Datastore Permissions, Thin vs. Thick Provisioning, Snapshots                | `vmkfstools`, `ls -l /vmfs/volumes`                |
| **VM Lifecycle**           | Boot Errors                   | Guest OS Logs, Bootloader Failures, Kernel Panics, Firmware Issues                | `dmesg`, `vmware.log`, `hyperv.log`                |
|                            | Migration Failures            | VMotion/HVMotion Errors, Storage Compatibility, Network Reachability              | `esxtop`, `vmware-vmotion` logs                    |
| **Guest OS**               | Performance Issues            | CPU Affinity, Ballooning, Disk Swap, Process Throttling                            | `top`, `vmstat`, `perf`, Guest OS-specific tools   |
|                            | Application Failures          | Port Conflicts, Environment Variables, Dependency Failures                        | `netstat -tulnp`, `env`, `journalctl` (Linux)     |
| **Security**               | Unauthorized Access           | VM Escape Attacks, Misconfigured Permissions, Guest Firewall Rules                 | `chkrootkit`, `rkhunter`, `auditd`                |
|                            | Vulnerability Exploits        | Outdated Hypervisor Patches, VM Tools Exploits, Credential Leaks                  | `OpenVMTools-Upgrade`, Cloud Provider CVEs         |

---

## **Query Examples**
### **1. Hypervisor Resource Monitoring (Linux Host)**
**Scenario:** A VM is unresponsive due to host resource exhaustion.
**Commands:**
```bash
# Check CPU usage (per-core)
vmstat 1 5
# Check memory pressure (slab/buffer cache)
free -h
# Check disk I/O latency
iostat -x 1 5
# Check network saturation
sar -n DEV 1 5
```
**Expected Output:**
- CPU: >90% usage on all cores → **vertical scaling** or **VM migration**.
- Swap usage: 80% → **increase host memory** or **adjust VM memory limits**.

---

### **2. VM Network Connectivity Issue (VMware)**
**Scenario:** A VM cannot ping the gateway.
**Steps:**
```bash
# Check VM network settings (from vCenter/CLI)
esxcli network ip interface list  # Verify IP assignment
ping 8.8.8.8  # Test reachability
tcpdump -i vmnic0 port 80  # Check for dropped packets
```
**Expected Findings:**
- **ARP cache incomplete** → Check VLAN configuration.
- **Packet loss** → Investigate **MTU mismatches** or **firewall drops**.

---

### **3. Storage Throttling (AWS EC2)**
**Scenario:** Slow EBS volume performance.
**Queries:**
```bash
# Check disk I/O metrics (using AWS CloudWatch)
aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name DiskBytesRead/Write \
    --dimensions Name=VolumeId,Value=${VOLUME_ID} \
    --start-time $(date -u -v-1h +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 300 \
    --statistics Average
```
**Mitigation:**
- Switch from **gp2** to **io1/io2** EBS volumes.
- Enable **EBS-Optimized Instances**.

---

### **4. VM Boot Failure (KVM/QEMU)**
**Scenario:** Guest OS fails to boot with "No such device" error.
**Debugging Steps:**
```bash
# Check VM XML config for disk mappings
virsh dumpxml <vm_name> | grep -i "disk"
# Verify storage pool status
virsh vol-list --pool default
# Check guest logs (if enabled)
cat /var/log/libvirt/qemu/<vm_name>.log
```
**Fix:**
- Reattach missing disk:
  ```xml
  <disk type='file' device='disk'>
      <driver name='qemu' type='raw'/>
      <source file='/path/to/rescue.iso'/> <!-- Example: Boot rescue image -->
  </disk>
  ```

---

### **5. Security Audit (Azure VMs)**
**Scenario:** Detect guest OS vulnerabilities.
**PowerShell Query:**
```powershell
# Check for outdated packages (Linux)
Get-Package | Where-Object { $_.Installed -eq "False" -and $_.Status -ne "Unassigned" }

# Check Azure Security Center recommendations
Get-AzSecurityContact | Select-Object *
Get-AzVMExtension -VMName <vm_name> -ResourceGroupName <rg_name> | Where-Object { $_.Type -eq "AzureSecurityCenter" }
```
**Action Items:**
- Enable **Azure Defender for Servers**.
- Patch **OpenSSL** vulnerabilities (e.g., Heartbleed).

---

## **Related Patterns**
1. **[Performance Tuning for VMs]**
   - Optimize CPU/Memory allocation, ballooning, and storage tiers.
   - *Tools:* `vmware-top`, `Azure VM Scale Sets`, `KVM live-migration`.

2. **[Disaster Recovery for VMs]**
   - Configure **VM snapshots**, **replication (SR-IOV, vMotion)**, and **cloud backup**.
   - *Tools:* `VMware SRM`, `AWS Backup`, `Azure Site Recovery`.

3. **[Security Hardening for Virtual Environments]**
   - Enforce **guest OS hardening**, **network segmentation**, and **hypervisor patches**.
   - *Tools:* `CIS Benchmarks`, `OpenSCAP`, `Azure Policy`.

4. **[Multi-Cloud VM Management]**
   - Standardize **VM templates**, **tagging**, and **lifecycle automation** across clouds.
   - *Tools:* `Terraform`, `Packer`, `Kubernetes (for stateless workloads)`.

5. **[Cost Optimization for VMs]**
   - Right-size VMs, use **spot instances**, and **shut down non-production VMs**.
   - *Tools:* `AWS Cost Explorer`, `Azure Cost Management`, `GCP Recommender`.

---
## **Best Practices**
- **Centralize Logs:** Use **ELK Stack (Elasticsearch, Logstash, Kibana)** or **Splunk** for hypervisor/guest logs.
- **Automate Alerts:** Set thresholds for **CPU/memory/disk** in **Prometheus/Grafana**.
- **Documentation:** Maintain a **runbook** for common issues (e.g., VM reset procedure).
- **Testing:** Regularly validate **backup/restore** and **failover** processes.

---
**References:**
- [VMware Docs: Troubleshooting Tools](https://docs.vmware.com/)
- [AWS EC2 Troubleshooting Guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Troubleshooting.html)
- [ITIL Service Operation for Virtualization](https://www.itilknowledge.com/)

---
**Note:** Adjust commands/queries based on your hypervisor (VMware, Hyper-V, KVM, etc.) and cloud provider (AWS/Azure/GCP). For production environments, always test fixes in a **non-production staging area**.