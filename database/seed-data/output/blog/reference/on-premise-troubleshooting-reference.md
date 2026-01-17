# **[Pattern] On-Premise Troubleshooting Reference Guide**

---

## **Overview**
This **On-Premise Troubleshooting** reference guide provides systematic approaches, tools, and best practices for identifying, diagnosing, and resolving technical issues in **on-premises infrastructure environments**. Unlike cloud-based troubleshooting—which often relies on vendor-managed APIs and centralized dashboards—on-premise troubleshooting requires direct access to physical or virtual machines, networks, and logs scattered across local systems.

This guide assumes familiarity with core IT operations, including networking, operating systems, and basic scripting. The pattern is structured into **logical stages**:
- **Pre-Troubleshooting Preparation** (documentation, tooling, and checklists)
- **Diagnostic Workflow** (structured root-cause analysis)
- **Solution Implementation** (fixes, rollbacks, and validation)
- **Post-Mortem & Knowledge Capture** (documentation and improvement).

Best suited for **enterprise environments with hybrid or fully on-premise setups**, this guide covers troubleshooting for:
- **Servers** (Windows/Linux)
- **Databases** (SQL, Oracle, PostgreSQL)
- **Networking** (firewalls, load balancers, VPNs)
- **Storage & Virtualization** (NAS/SAN, VMware/Hyper-V)
- **Applications** (custom or legacy software)

---

## **1. Schema Reference**
Below is a structured breakdown of **key troubleshooting components** and their metadata.

| **Component**          | **Description**                                                                 | **Variables**                                                                 | **Tools/Utilities**                          | **Output**                     |
|-------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------|-------------------------------|
| **Preparation**         | Checklists, tooling, and documentation needed before troubleshooting.         | - Pre-troubleshooting checklist (steps 1–5) <br> - Tool versions <br> - Access permissions | - Snagit/Notepad++ (docs) <br> - Git (version control) <br> - Configuration management (Ansible/Chef) | Checklist validation report |
| **Diagnostic Layer**    | Systematic steps to isolate issues by layers (e.g., hardware → software).     | - Log file paths <br> - Network interfaces <br> - Service dependencies | - Wireshark (network) <br> - Event Viewer (`eventvwr.msc`) <br> - `netstat -ano` (ports) | Log extracts, network traces |
| **Root-Cause Analysis** | Logical deduction to identify root cause (e.g., misconfiguration vs. hardware). | - Error codes <br> - Timeline of events <br> - Dependency graphs | - Grep/AWK (log parsing) <br> - Event Viewer Correlator <br> - Dependency tools (`dnf list –installed`) | Root-cause hypothesis |
| **Solution**            | Corrective actions (patches, reboots, reconfigurations).                       | - Patch versions <br> - Step-by-step procedures <br> - Rollback plan          | - Package managers (`apt`, `yum`) <br> - PowerShell/Bash scripts <br> - Backup tools | Proof-of-correctness log   |
| **Post-Mortem**        | Documentation and improvements after remediation.                           | - Incident details <br> - Timeline <br> - Lessons learned                  | - Confluence/Notion (collab tools) <br> - Jira (issue tracking) | Updated knowledge base |

---

## **2. Diagnostic Workflow**
This section outlines a **structured troubleshooting approach** using the **Layered Troubleshooting Model**.

### **A. Preparation Phase**
Before diving into diagnostics, ensure:
1. **Permissions**:
   - Admin access to all relevant systems (servers, logs, databases).
   - **Example Grant Command**:
     ```bash
     sudo usermod -aG sudo troubleshooter_user
     ```
2. **Documentation**:
   - Review runbooks for the affected service.
   - Example: [Service XYZ Troubleshooting Runbook](https://docs.example.com/runbook/XYZ).
3. **Tooling**:
   - **Essential Tools**:
     | Tool          | Purpose                                                                 |
     |---------------|-------------------------------------------------------------------------|
     | `tcpdump`     | Capture network traffic (e.g., `tcpdump -i eth0 port 22`).               |
     | `jstack`      | Analyze Java application hangs (e.g., `jstack <PID>`).                  |
     | `perf`        | System performance profiling (Linux).                                   |
     | PuTTY/WinSCP  | Remote server access & file transfers.                                  |

4. **Checklist**:
   - Verify system uptime (`uptime` or `SystemUptime` in Windows).
   - Check recent patches (`lsb_release -a` on Linux; `Get-HotFix` in PowerShell).

---

### **B. Layered Diagnostic Process**
Treat the system as **stacked layers**; diagnose from **bottom up** (hardware) or **top down** (application).

#### **Layer 1: Physical/Hardware**
| Issue Type       | Troubleshooting Steps                                                                 | Tools/Commands                          |
|------------------|---------------------------------------------------------------------------------------|-----------------------------------------|
| **Storage Failure** | Check SMART status (`smartctl -a /dev/sda`). Verify disk health via RAID controller UI. | `smartctl`, `fdisk -l`                  |
| **Network Hardware** | Test cables, ports (`ip neigh`), and switch logs.                                     | `ipconfig /all`, `arp -a`               |
| **Power Supply** | Check UPS logs and server motherboard status LEDs.                                    | UPS management software (e.g., APC)     |

#### **Layer 2: Operating System**
| Symptom          | Diagnostic Queries                                                                 | Tools/Commands                          |
|------------------|--------------------------------------------------------------------------------------|-----------------------------------------|
| **High CPU Usage** | Identify top processes (`top`, `Task Manager`). Check for rogue scripts.           | `htop`, `Resource Monitor`              |
| **Memory Leaks** | Analyze heap dumps (`jmap -dump:format=b,file=heap.hprof <PID>`).                   | `jhat`, `VisualVM`                      |
| **Disk I/O Issues** | Check pending I/O (`iostat -x 1`), `dmesg | grep -i error`.                           | `iostat`, `df -h`                       |

#### **Layer 3: Networking**
| Symptom          | Diagnostic Queries                                                                 | Tools/Commands                          |
|------------------|--------------------------------------------------------------------------------------|-----------------------------------------|
| **Latency**      | Measure RTT (`ping -f 8.8.8.8`), Traceroute (`traceroute 1.1.1.1`).                 | `ping`, `mtr`, Wireshark (capture)       |
| **Port Blocking**| Verify open ports (`netstat -tulnp`, `ss -tulnp`). Check firewall rules (`iptables -L`). | `telnet <host> <port>`, `nmap -sT <IP>` |

#### **Layer 4: Services & Applications**
| Symptom          | Diagnostic Queries                                                                 | Tools/Commands                          |
|------------------|--------------------------------------------------------------------------------------|-----------------------------------------|
| **Service Crash**| Review event logs (`Get-EventLog -LogName "Application"`). Check service dependencies. | `systemctl status <service>`, `journalctl -xe` |
| **Database Errors**| Parse SQL error logs (`grep ERROR /var/log/mysql/error.log`).                        | `pgbadger` (PostgreSQL analytics)       |

---

### **C. Root-Cause Analysis (Template)**
Use the **5 Whys** technique to drill down to the root cause:
1. **Symptom**: "Application X is crashing after 2 hours of uptime."
   → Why? → "High CPU usage spikes detected."
   → Why? → "Background thread is stuck in a deadlock."
   → Why? → "Missing `timeout` parameter in a database query."
   → **Root Cause**: **Query timeout not configured** → Fixed by updating the query.

---

## **3. Query Examples**
### **A. Log Parsing**
Extract critical errors from `syslog`:
```bash
grep -i "error\|fail" /var/log/syslog | sort | uniq -c | sort -nr
```

### **B. Network Tracing**
Identify TCP connection issues:
```bash
netstat -anp | grep ESTABLISHED
```

### **C. Process Monitoring**
Find processes using excessive memory:
```bash
ps aux --sort=-%mem | head -20
```

### **D. Database Diagnostics**
Check PostgreSQL deadlocks:
```sql
SELECT * FROM pg_locks WHERE NOT(pid = pg_backend_pid());
```

---

## **4. Solution Implementation**
### **A. General Fixes**
| Issue Type       | Recommended Fix                                                                   |
|------------------|----------------------------------------------------------------------------------|
| **Config Misconfiguration** | Apply corrected config via `systemctl reload service` or `iisreset`.           |
| **Outdated Software** | Patch via `apt-get upgrade` or vendor-provided installer.                          |
| **Disk Full**    | Clean logs (`journalctl --vacuum-size=100M`) or expand storage.                    |

### **B. Rollback Plan**
Always test fixes in a **staging environment** and document rollback steps:
```powershell
# Example: Revert a Windows service to previous state
sc config "ServiceName" start=auto
sc start "ServiceName"
```

---

## **5. Post-Mortem & Knowledge Capture**
### **A. Documentation Checklist**
- [ ] Update **runbook** with new troubleshooting steps.
- [ ] Add **lessons learned** to Confluence/Jira.
- [ ] Flag **recurring issues** for automation (e.g., Ansible playbooks).

### **B. Example Post-Mortem Template**
| Field               | Details                                                                 |
|---------------------|-------------------------------------------------------------------------|
| **Incident ID**     | `TR-2024-05-15-001`                                                     |
| **Root Cause**      | "Misconfigured firewall rule blocked inbound traffic."                   |
| **Resolution Time** | 4 hours                                                                 |
| **Affected Systems**| Web servers (3 nodes)                                                   |
| **Preventative Measure** | "Deploy Ansible playbook to auto-check firewall rules."                 |

---

## **6. Related Patterns**
| Pattern                     | Description                                                                 | When to Use                          |
|-----------------------------|-----------------------------------------------------------------------------|---------------------------------------|
| **Logging & Monitoring**     | Implement centralized logs (ELK Stack, Splunk) for proactive alerts.         | When manual log parsing is unscalable. |
| **Automated Remediation**   | Use tools like Ansible/Terraform to auto-apply fixes.                     | For recurring issues.                |
| **Chaos Engineering**       | Intentionally inject failures to test resilience.                           | During system redesigns.             |
| **Incident Response Playbook** | Structured steps for rapid response during outages.                      | Critical production incidents.        |

---
**Last Updated**: 2024-05-15
**Applicable To**: On-premises Windows/Linux environments (hybrid/fully on-prem).