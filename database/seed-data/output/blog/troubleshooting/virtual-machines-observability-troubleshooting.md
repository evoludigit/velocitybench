# **Debugging Virtual-Machines Observability: A Troubleshooting Guide**

## **1. Introduction**
Virtual Machine (VM) observability ensures visibility into VM resource usage, performance, health, and dependencies (e.g., storage, networking, hypervisor). Poor observability can lead to undetected failures, degraded performance, or unplanned outages.

This guide provides a structured approach to diagnosing VM observability issues, focusing on **quick resolution** with real-world examples.

---

## **2. Symptom Checklist**
Use this checklist to identify symptoms before diving into debugging:

| **Category**            | **Symptom**                                                                 | **Possible Root Cause**                          |
|-------------------------|-----------------------------------------------------------------------------|-------------------------------------------------|
| **Performance**         | High CPU/memory/network latency in VMs                                     | Overloaded host, misconfigured QoS, storage bottlenecks |
| **Availability**        | VMs crashing or failing to start                                          | Hypervisor issues, disk corruption, misconfigured VM settings |
| **Monitoring Missing**  | No metrics/logs from VMs in observability tools (Prometheus, Grafana, ELK) | Agent misconfiguration, permissions, or agent crashes |
| **Network Issues**      | VMs unable to communicate with external systems or internal dependencies | Firewall misconfiguration, VLAN/IP conflicts, misrouted traffic |
| **Storage Problems**    | Slow I/O, timeouts, or VM crashes on disk-intensive operations             | Thin provisioning issues, SAN/NAS performance, misconfigured disk alignment |
| **Hypervisor Issues**   | Host-level crashes, VM migrations failing, or hypervisor resource exhaustion | Resource starvation, kernel panics, misconfigured DRS/HA |
| **Log Corruption**      | Critical logs missing or truncated                                        | Log rotation misconfiguration, agent crashes, or disk full |

---
**Next Steps:**
- If multiple symptoms exist, prioritize **availability** and **performance** before diving into logs/metrics.
- Check **hypervisor logs** (e.g., `vcenter.log`, `esx.log`) if VMs are unresponsive.

---

## **3. Common Issues & Fixes**

### **3.1 Issue: VMs Not Reporting Metrics (Prometheus/Grafana/ELK Missing Data)**
**Symptom:**
- No CPU/memory/network metrics in observability dashboards.
- VM agents (e.g., `prometheus-node-exporter`, `Datadog Agent`) show as offline.

**Diagnosis:**
1. **Check Agent Status**
   ```bash
   sudo systemctl status prometheus-node-exporter  # Linux VM
   ```
   - If **dead**, check logs:
     ```bash
     journalctl -u prometheus-node-exporter -n 50 --no-pager
     ```
   - Look for **permission errors, network issues, or misconfigurations**.

2. **Verify Agent Configuration**
   - Example `node_exporter.yml` (if using custom config):
     ```yaml
     scrape_configs:
       - job_name: 'vm_metrics'
         static_configs:
           - targets: ['localhost:9100']  # Default port
     ```
   - If using **containerized agents**, check if the host interface is exposed:
     ```bash
     docker exec -it <agent_container> curl -I http://localhost:9100/metrics
     ```
     (Should return `200 OK`)

3. **Check Firewall/SELinux**
   - Ensure **port `9100` (Prometheus) or `8125` (Datadog)** is open:
     ```bash
     sudo iptables -L -n | grep 9100  # Verify rule exists
     sudo setenforce 0  # Temporarily disable SELinux for testing
     ```

**Fixes:**
| **Root Cause**               | **Solution**                                                                 |
|------------------------------|------------------------------------------------------------------------------|
| Agent not running            | Restart service: `sudo systemctl restart prometheus-node-exporter`           |
| Wrong config file            | Validate YAML syntax: `yamllint config.yml`                                 |
| Missing permissions          | Run as root or adjust `/etc/sudoers` to allow port access                   |
| Network misconfiguration      | Verify `host.docker.internal` is reachable (if using Docker)               |
| Agent crashed due to OOM      | Set resource limits: `ulimit -v unlimited` (temporarily)                    |

---

### **3.2 Issue: VMs Crash on Heavy I/O (Disk Latency)**
**Symptom:**
- VMs freeze or crash during large file operations (e.g., `dd`, database backups).
- Hypervisor logs show **`SCSI timeout` or `disk I/O error`**.

**Diagnosis:**
1. **Check Disk Latency**
   ```bash
   iostat -x 1  # Monitor disk utilization
   ```
   - Look for **`await` > 200ms** (indicates latency).
   - Check **`tps` (throughput)** – if low, storage may be saturated.

2. **Verify Disk Alignment**
   - Misaligned LVM/partitioning can cause **4K-alignment issues**:
     ```bash
     sudo filefrag -v /path/to/large/file
     ```
     - If **fragments are misaligned**, realign partitions:
       ```bash
       sudo partprobe /dev/sdX  # For physical disks
       ```

3. **Check Hypervisor Storage Queue Depth**
   - If using **NFS/iSCSI**, adjust queue depth in VM settings:
     ```xml
     <!-- Example for VMware vSphere -->
     <disk type="scsi" controllerType="lsilogic">
       <file>/vmfs/volumes/datastore/disk.vmdk</file>
       <backing>
         <deviceName>/vmfs/volumes/datastore</deviceName>
         <controllerKey>1000</controllerKey>
         <unitNumber>0</unitNumber>
         <queueDepth>64</queueDepth>  <!-- Increase if throttling -->
       </backing>
     </disk>
     ```

**Fixes:**
| **Root Cause**               | **Solution**                                                                 |
|------------------------------|------------------------------------------------------------------------------|
| Storage bottleneck           | Add storage, optimize LUNs, or use **Thin Provisioning**                     |
| Misaligned partitions        | Realign partitions (LVM/NTFS)                                               |
| Hypervisor QoS misconfigured | Increase **CPU/Memory reservations** in VM settings                         |
| NFS/iSCSI timeouts           | Adjust `soft`/`hard` timeouts in `/etc/fstab` or VMware settings            |

---

### **3.3 Issue: VM Migration Fails (vMotion/DRS)**
**Symptom:**
- VM migration stalls or fails with:
  - `Invalid CPU or memory size`
  - `Network connectivity lost during migration`
  - `Storage latency too high`

**Diagnosis:**
1. **Check Hypervisor Logs**
   ```bash
   tail -f /var/log/vmware/vpxa/vpxa.log  # vCenter logs
   ```
   - Look for **`vMotion failures` or `storage latency` warnings**.

2. **Verify Compatibility**
   - Migrate to a **compatible host** (same CPU model if `CPU pinning` is enabled).

3. **Network Test**
   - Ensure **vMotion network** has sufficient bandwidth:
     ```bash
     ping -c 4 <destination_host>  # Low latency (<10ms) required
     ```

**Fixes:**
| **Root Cause**               | **Solution**                                                                 |
|------------------------------|------------------------------------------------------------------------------|
| Insufficient resources       | Add CPU/RAM to destination host or **shrink VM**                          |
| Network misconfiguration     | Isolate vMotion traffic, increase MTU (jumbos frames)                       |
| Storage latency              | Check SAN health, adjust **LIO queue depth**                                |
| Mixed CPU architectures      | Upgrade all hosts to compatible CPU models                                  |

---

### **3.4 Issue: Hypervisor Resource Exhaustion (OOM Killer, CPU Throttling)**
**Symptom:**
- VMs are **throttled or killed** by the OOM killer.
- Hypervisor CPU usage at **100% with no free resources**.

**Diagnosis:**
1. **Check Host Metrics**
   ```bash
   vmstat 1  # Monitor CPU, memory, swap
   top -c     # Check OOM killer activity
   ```
   - If **`OOMKill:`** appears in `top`, note the process being killed.

2. **Verify Hypervisor Settings**
   - Check **memory overcommit**:
     ```bash
     esxcli hardware memory get  # For ESXi
     ```
   - If **`overcommitment` is too high**, reduce VM memory limits.

**Fixes:**
| **Root Cause**               | **Solution**                                                                 |
|------------------------------|------------------------------------------------------------------------------|
| Memory overcommit            | Reduce **`ballooning` or set reservations** in VM settings                |
| Swap starvation              | Increase swap space or **disable swap** for VMs                           |
| CPU scheduling issues        | Enable **RT (Real-Time) scheduling** for critical VMs                       |
| Misconfigured DRS            | Adjust **CPU/Memory weight** in DRS settings                                |

---

## **4. Debugging Tools & Techniques**

| **Tool**                     | **Use Case**                                                                 | **Example Command**                                  |
|------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| **`vmstat`, `iostat`, `mpstat`** | Monitor host/VM CPU, memory, disk I/O                                     | `iostat -x 1`                                        |
| **`netstat`, `ss`**         | Check network connections, bottlenecks                                      | `ss -tulnp \| grep 9100`                             |
| **`journalctl`**             | Debug agent crashes (Prometheus, Datadog)                                   | `journalctl -u prometheus-node-exporter -n 50`       |
| **`vSphere CLI`**            | Check VMware host/VM status                                                | `vim-cmd vmsvc/getallvms \| grep <VM_NAME>`           |
| **`perf`**                   | Deep CPU profiling for latency issues                                      | `perf top`                                          |
| **`tcpdump`**                | Capture network packets (vMotion, NFS)                                       | `tcpdump -i vmk0 port 902 -w capture.pcap`          |
| **`Prometheus Alertmanager`** | Get automated alerts for VM failures                                        | Configure rules for `up{job="node_exporter"} == 0`   |
| **`Grafana Explore`**        | Quickly debug metrics (CPU, disk, network)                                   | `Grafana → Explore → Select "Prometheus"`            |

**Advanced Debugging:**
- **Hypervisor Kernel Logs** (ESXi):
  ```bash
  esxcli system console log list
  esxcli system console log read -l 10000 > esxi_logs.txt
  ```
- **VM Core Dump Analysis** (for crashes):
  ```bash
  gcore /path/to/crashed_vm
  addresssanitizer ./coredump  # If compiled with ASan
  ```

---

## **5. Prevention Strategies**

### **5.1 Proactive Monitoring**
- **Set Up Alerts:**
  - Prometheus Alerts:
    ```yaml
    - alert: VMDown
      expr: up{job="node_exporter"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "VM {{ $labels.instance }} is down"
    ```
  - Datadog Dashboards: Track **CPU%, disk saturation, network errors**.

- **Scheduled Checks:**
  - **Disk Alignment** (monthly):
    ```bash
    sudo filefrag -v /var/log | grep "ext4"
    ```
  - **Agent Health** (daily):
    ```bash
    curl -I http://<agent_ip>:9100/metrics 2>/dev/null
    ```

### **5.2 Configuration Best Practices**
| **Component**       | **Best Practice**                                                                 |
|---------------------|---------------------------------------------------------------------------------|
| **VM Memory**       | Set **memory reservations** (avoid overcommit)                                  |
| **Storage QoS**     | Use **LIO queue depth tuning** (`/etc/modules-load.d/lio.conf`)                |
| **Networking**      | Enable **vMotion jumbo frames**, separate VLANs for management/data traffic      |
| **Hypervisor Upgrades** | Patch **VMware ESXi** and **KVM/QEMU** regularly (CVE scans)                   |
| **Agent Deployment**| Use **containerized agents** (Docker/Kubernetes) for easier updates/maintenance |

### **5.3 Disaster Recovery Planning**
- **VM Snapshots:** Schedule **weekly snapshots** for critical VMs.
- **Hypervisor HA:** Enable **DRS, vMotion, or KVM live migration**.
- **Backup Observability Data:**
  - Export Prometheus metrics to **Thanos** or **VictoriaMetrics**.
  - Archive ELK logs to **S3/Glacier**.

---
## **6. Summary Checklist for Rapid Resolution**
| **Step**               | **Action**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **1. Verify VM Status** | Check `vCenter` or `virsh list --all` (KVM)                                  |
| **2. Check Logs**      | `journalctl`, `esx.log`, or `vmware.log`                                     |
| **3. Isolate Symptoms** | Narrow down (CPU? Disk? Network?)                                            |
| **4. Apply Fixes**     | Use **3. Common Issues & Fixes** as reference                               |
| **5. Validate**        | Confirm metrics/logs are restored                                           |
| **6. Prevent Recurrence** | Update config, set alerts, test DR plan                                       |

---
## **7. Final Notes**
- **For Production Issues:** Follow **structured incident management** (e.g., **PagerDuty, Jira**).
- **For Dev/Test:** Use **Terraform/Ansible** to automate VM observability setup.
- **Keep Learning:** Follow **VMware/KVM blogs**, **Prometheus docs**, and **Datadog Guides**.

By following this guide, you can **quickly diagnose and resolve VM observability issues** while preventing future problems. 🚀