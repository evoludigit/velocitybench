---

# **[Pattern] Virtual Machine Debugging Reference Guide**

---

## **Overview**
The **Virtual Machine Debugging (VM Debugging)** pattern provides a structured approach to diagnosing, monitoring, and resolving issues in virtualized environments. This pattern is applicable when troubleshooting **VM crashes, performance degradation, network misconfigurations, or storage-related problems** in hypervisor-based or containerized virtualized systems (e.g., VMware ESXi, Hyper-V, KVM, Docker, or Kubernetes).

Key objectives include:
- **Isolating root causes** via logging, snapshots, and telemetry.
- **Efficiently reproducing issues** using VM snapshots, live migration, and debugging tools.
- **Minimizing downtime** by leveraging non-disruptive operations (NDOs) where possible.
- **Ensuring compliance** with security and audit policies via captured VM states.

This guide assumes familiarity with **hypervisor administration, OS debugging tools (e.g., `gdb`, `logrotate`), and cloud/on-prem virtualization platforms**.

---

## **1. Key Concepts & Implementation Details**

### **1.1 Core Components**
| **Component**               | **Description**                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|
| **Hypervisor Logs**         | Centralized logs from ESXi, Hyper-V, or KVM for VM lifecycle events (start/stop, errors). |
| **VM Snapshots**            | Point-in-time copies of VM states for rollback testing.                         |
| **Debugging Tools**         | Platform-specific tools (e.g., `vmware-toolbox-cmd`, `hyperv-guest-tools`, `strace`). |
| **Performance Counters**    | Metrics like CPU utilization, memory ballooning, or I/O latency.                 |
| **Network/Tracing Tools**   | `tcpdump`, Wireshark, or `ethtool` for packet inspection.                      |
| **Automated Playbooks**     | Ansible/Terraform scripts for VM provisioning and scaling during debugging.      |
| **Security Hardening**      | Enforcing SELinux/AppArmor, disabling unused services, and patching VM guests.  |

---

### **1.2 Common Debugging Scenarios**
| **Scenario**                | **Tools/Methods**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------|
| **VM Crash on Boot**        | Check hypervisor logs (`/var/log/vmware/*)`, enable **core dumps** in guest OS.   |
| **Network Connectivity Issues** | Use `ping`, `traceroute`, and `nslookup` in guest; inspect host/VM firewall rules. |
| **Disk I/O Bottlenecks**    | Monitor `iostat`/`vmstat`; optimize VMware VMFS/KVM storage drivers.               |
| **CPU Throttling**          | Check hypervisor CPU scheduling (e.g., Hyper-V Dynamic Memory, KVM cpuset).       |
| **Guest OS Hang**           | Use `gdb` or `dtrace` (Solaris) to inspect kernel traces.                         |
| **Live Migration Failures** | Verify network latency (`migrate-tool` in VMware), storage synchronization.      |

---

### **1.3 Debugging Workflow**
1. **Reproduce the Issue**
   - Use snapshots to revert to a known-good state.
   - Enable **debug logging** in hypervisor (e.g., `vSphere Client > Guest OS > Debug > Enable`).
2. **Gather Telemetry**
   - Hypervisor logs, VMware Tools logs (`/var/log/vmware-tools/`), or `perf` (Linux).
   - Use `vmkfstools` (VMware) to inspect disk corruption.
3. **Analyze Data**
   - Correlate logs with performance metrics (e.g., high CPU + `dmesg` errors).
   - Reproduce in isolation (e.g., test VM on different hosts).
4. **Resolve & Validate**
   - Apply fixes (e.g., OS patch, hypervisor update) and **verify with health checks**.
   - Document changes in a **change log** for auditing.

---

## **2. Schema Reference**

### **2.1 Hypervisor-Specific Log Files**
| **Hypervisor** | **Log Location**               | **Key Entries to Check**                          |
|----------------|---------------------------------|---------------------------------------------------|
| **VMware ESXi** | `/var/log/vmkernel.log`         | `vmkernel`, `hostd`, or `ESXi` boot errors.       |
| **Hyper-V**     | `%SystemRoot%\Logs\Microsoft\Windows\Hyper-V\Admin` | `Hyper-V Admin Service`, VM network errors.        |
| **KVM/QEMU**    | `/var/log/libvirt/qemu/`        | `qemu-kvm`, `libvirt` startup/shutdown logs.      |
| **Docker**      | `/var/lib/docker/containers/*/json.log` | Container runtime errors, OOM kills.         |

---

### **2.2 VM Configuration Schema (JSON Example)**
```json
{
  "vm_name": "debug-vm",
  "hypervisor": "VMware ESXi",
  "snapshots": [
    {
      "name": "pre-crash",
      "timestamp": "2024-05-20T10:00:00Z",
      "vm_state": {
        "memory": "2GiB",
        "cpu": "2 vCPUs",
        "network": ["vmnic0", "vmnic1"]
      }
    }
  ],
  "debug_tools": {
    "guest_os": "Linux",
    "tools_installed": ["gdb", "strace", "dtrace"],
    "kernel_module": "vmtoolsd"
  },
  "performance_metrics": {
    "avg_cpu_usage": 78.5,
    "disk_latency": 15ms,
    "memory_ballooned": 1.2GiB
  }
}
```

---
## **3. Query Examples**

### **3.1 Checking VMware Tools Logs**
```bash
# Access logs via SSH (if enabled)
vmware-toolbox-cmd -T ssh -u root -p <password> query-tools-status

# Inspect VMware Tools log directly
tail -f /var/log/vmware-tools/vmware-tools.log
```
**Expected Output:**
```
2024-05-20T09:30:00.123Z | info | VixDiskLib: Disk snapshot created successfully.
2024-05-20T09:35:00.456Z | error | vixDiskLib: Disk I/O timeout on /vmfs/volumes/datastore1/snapshot.vmdk
```

---

### **3.2 Analyzing Hyper-V VM Events**
```powershell
# Query Hyper-V logs using Get-VMEvent
Get-VMEvent -ComputerName <HyperVHost> -VMName "debug-vm" -ErrorAction Stop |
  Select-Object TimeGenerated, VMName, EventID, Message
```
**Filter for critical events:**
```powershell
Get-VMEvent -VMName "debug-vm" -Error | Where-Object { $_.EventID -eq 13030 }  # VM crash
```

---

### **3.3 Troubleshooting Docker Container Crashes**
```bash
# Inspect container logs
docker logs --tail 50 <container_id>

# Check system-wide Docker daemon logs
journalctl -u docker --no-pager | grep -i "error"

# Profile CPU/memory usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

### **3.4 Using `strace` for Guest OS Debugging**
```bash
# Attach strace to a process in a Linux guest (if enabled)
sudo strace -p <PID> -o debug_trace.log

# Analyze for blocked system calls
grep "block" debug_trace.log
```

---

## **4. Related Patterns**
| **Pattern**                          | **Purpose**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| **[Blue-Green Deployment]**           | Minimize downtime during VM updates by running two identical environments.   |
| **[Canary Releases]**                 | Gradually roll out VM changes to isolate issues.                            |
| **[Configuration as Code]**           | Use Terraform/Ansible to manage VM debugging templates consistently.         |
| **[Observability Pipeline]**           | Correlate logs, metrics, and traces (e.g., Prometheus + Grafana + ELK).    |
| **[Chaos Engineering]**                | Intentional VM failures (e.g., `Chaos Mesh`) to test resilience.           |

---
## **5. Best Practices**
1. **Enable Debugging Early**
   - Add debug tools (e.g., `vmware-tools`, `hyperv-daemons`) during VM creation.
2. **Automate Log Collection**
   - Use scripts to archive logs on schedule (e.g., `cron` + `rsync`).
3. **Limit Snapshot Overhead**
   - Delete unused snapshots (`vmware-vim-cmd` or `virsh snapshot-delete`).
4. **Isolate Debugging VMs**
   - Use separate VLANs/networks for debugging to avoid production impact.
5. **Document Root Causes**
   - Maintain a **debugging knowledge base** with reproducible steps and fixes.

---
**Note:** Always consult vendor documentation for hypervisor-specific commands (e.g., [VMware KB](https://kb.vmware.com), [Microsoft Hyper-V Docs](https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/)).