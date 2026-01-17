# **[Pattern] On-Premise Best Practices Reference Guide**

---

## **1. Overview**
Deploying workloads on-premise requires meticulous planning to ensure **security, scalability, reliability, and compliance** while maximizing operational efficiency. This guide outlines best practices for **hardware selection, network architecture, data storage, disaster recovery, security, monitoring, and maintenance** to optimize on-premise deployments. It applies to **enterprise environments** (data centers, traditional servers, or hybrid setups) and covers foundational principles for **infrastructure, applications, and operational workflows**.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Hardware & Infrastructure Best Practices**
| **Aspect**               | **Best Practice**                                                                 | **Key Considerations**                                                                 |
|--------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Server Selection**     | Use **high-performance, redundant components** (RAID 10, ECC RAM, dual-power supplies). | Balance cost vs. performance (e.g., Xeon vs. ARM for specific workloads).               |
| **Virtualization**       | Deploy **Type 1 hypervisors (esxi, Hyper-V)** for better isolation and resource control. | Ensure **vMotion live migration** and **SR-IOV** for high-I/O workloads.               |
| **Storage**              | **NAS/SAN with tiered storage (SSD for hot data, HDD for cold)** for cost efficiency. | Use **thin provisioning** (if snapshot-heavy) and **dedupe/compression** for backups.   |
| **Networking**           | **Spanning-tree protocol (STP/RSTP)** + **VLAN segmentation** for network isolation. | Implement **BGP/OSPF** for multi-site redundancy; avoid flat networks (use MACsec).      |
| **Power & Cooling**      | **UPS with runtime ≥ 15 mins**, **row-based cooling**, and **liquid cooling** for dense setups. | Monitor **PDU load** and **temperature thresholds (≤85°F)** for hardware health.        |

**Hardware Lifecycle Management:**
- **Replace hardware every 3–5 years** (or at **70% utilization**).
- **DDR4/5 memory** for CPU-bound workloads; **NVMe SSDs** for I/O-heavy tasks.
- **Blade servers** for space efficiency (e.g., Dell PowerEdge, HP ProLiant).

---

### **2.2 Network Architecture**
| **Component**            | **Recommended Practices**                                                                 | **Tools/Technologies**                          |
|--------------------------|------------------------------------------------------------------------------------------|-------------------------------------------------|
| **Firewall**             | **Stateful inspection + deep packet inspection (DPI)**; **Zero Trust model** (mutual TLS). | Palo Alto, Cisco ASA, PfSense.                  |
| **Load Balancing**       | **Layer 4 (TCP/UDP) + Layer 7 (HTTP/HTTPS) LB** for high availability.                   | HAProxy, NGINX, F5 BIG-IP.                      |
| **DNS & DHCP**           | **Split-horizon DNS** (internal vs. external views); **DHCP with reservation + lease tracking**. | BIND, Windows DNS, Infoblox.                   |
| **VPN & Remote Access**  | **IPsec (site-to-site) + WireGuard/OpenVPN** for secure access; **MFA enforced**.          | OpenVPN, StrongSwan, ZeroTier.                  |
| **SDN/Network Automation** | **Ansible + Python for config management**; **Cisco ACI/Nexus 9K** for cloud-like control. | Ansible, Terraform, Cisco DevNet.             |

**Network Redundancy:**
- **Dual ISPs** with **BGP failover** (keepalived for VRRP).
- **LACP (Link Aggregation Control Protocol)** for 10G/40G uplinks.
- **Heartbeat monitoring** (e.g., `keepalived`, `heartbeat` tools) for failover.

---

### **2.3 Data Storage & Backup**
| **Strategy**             | **Implementation**                                                                       | **Validation Steps**                             |
|--------------------------|------------------------------------------------------------------------------------------|--------------------------------------------------|
| **RAID Levels**          | **RAID 10** for OS/data, **RAID 5/6** for archival; avoid RAID 0.                         | Test rebuild times (≤24h for critical drives).   |
| **Backup Types**         | **3-2-1 Rule**: 3 copies, 2 media types, 1 offsite.                                      | **Immutable backups** (WORM storage) for compliance. |
| **Backup Tools**         | **Bareos, Veeam, or Duply** (for deduplication); **rsync + LVM snapshots**.              | **Test restore** every 6 months.                 |
| **Disaster Recovery (DR)**| **Hot site (synchronous), Warm site (asynchronous), or Cold site (manual)**.              | **RTO ≤ 4h**, **RPO ≤ 15 mins** for critical apps. |
| **Storage Tiering**      | **Tier-0 (FlashCache), Tier-1 (SSD), Tier-2 (HDD), Tier-3 (Cold Storage)**.               | Use **NetApp ONTAP** or **Dell ECS** for automation. |

**Backup Best Practices:**
- **Incremental + Differential** backups (avoid full backups daily).
- **Air-gap offsite backups** (e.g., encrypted USB drives, tape libraries).
- **Blockchain hashing** for integrity verification.

---

### **2.4 Security Best Practices**
| **Area**                 | **Best Practice**                                                                         | **Tools**                                      |
|--------------------------|------------------------------------------------------------------------------------------|------------------------------------------------|
| **Authentication**       | **LDAP/AD + MFA (TOTP/HSM-based)**; **Kerberos** for SPN integration.                     | FreeRADIUS, Duo Security, HashiCorp Vault.     |
| **Patch Management**     | **Automated patching (weekly for critical, monthly for others)**; **quarantine unpatched nodes**. | Microsoft WSUS, Ansible Galaxy.             |
| **Endpoint Security**    | **EDR (Endpoint Detection & Response) + AMSI (Antimalware Scan Interface)**.              | CrowdStrike, SentinelOne, Microsoft Defender.   |
| **Network Security**     | **Micro-segmentation** (Cisco ACI, VMware NSX); **MACsec for fabric**.                   | Cisco Umbrella, Zscaler.                      |
| **Compliance**           | **Regular audits (NIST 800-53, ISO 27001, GDPR)**; **SIEM integration (Splunk, ELK)**. | OpenSCAP, MITRE ATT&CK Matrix.                |

**Security Hardening:**
- **Disable unused services** (e.g., `rpcbind`, `telnet`).
- **Rotate credentials every 90 days** (hardcoded passwords in configs → secrets manager).
- **Enable **DDoS protection** (Cloudflare, AWS Shield).

---

### **2.5 Monitoring & Observability**
| **Component**            | **Best Practice**                                                                         | **Tools**                                      |
|--------------------------|------------------------------------------------------------------------------------------|------------------------------------------------|
| **Logging**              | **Centralized logs (ELK Stack, Splunk, Graylog)**; **retention policy (30–365 days)**.      | Filebeat, Fluentd.                             |
| **Metrics**              | **Prometheus + Grafana** for time-series data; **custom dashboards for SLA monitoring**.    | Telegraf, VictoriaMetrics.                     |
| **Alerting**             | **Threshold-based + anomaly detection** (e.g., CPU >90% for >5 mins).                   | PagerDuty, Opsgenie.                           |
| **Synthetic Monitoring** | **Daily health checks** (e.g., Pingdom, UptimeRobot) for external-facing services.         | Synthetic monitoring APIs.                     |
| **APM (App Performance)**| **Distributed tracing (Jaeger, OpenTelemetry)** for microservices; **APM (New Relic, Dynatrace)**. | OpenTelemetry Collector.                      |

**Key Metrics to Monitor:**
- **Server:** CPU, RAM, Disk I/O, Network Saturation.
- **Database:** Query latency, lock contention, cache hit ratio.
- **Network:** Packet loss, jitter, latency (ping, traceroute).
- **Security:** Failed logins, unauthorized access attempts.

---

### **2.6 Disaster Recovery & High Availability**
| **Strategy**             | **Implementation**                                                                       | **Testing**                                    |
|--------------------------|------------------------------------------------------------------------------------------|------------------------------------------------|
| **Active-Active (Multi-AZ)** | **Database replication (PostgreSQL Streaming, MySQL GTID)** + **DNS failover**.           | **Chaos Engineering** (Gremlin, Chaos Monkey). |
| **Active-Passive (Backup Site)** | **Asynchronous replication (SQL Server Log Shipping, ZFS Send/Receive)**.               | **DR drill every 6 months**.                   |
| **Cloud Hybrid DR**      | **Backup critical VMs to AWS/Azure** (Veeam, Commvault); **geo-redundant storage**.        | **RPO/RTO testing**.                           |
| **Chaos Engineering**    | **Randomly kill nodes/services** to test resilience (e.g., kill a DB node).              | **Record recovery time**.                      |

**DR Documentation:**
- **Runbooks** for failover procedures.
- **System topology diagrams** (Networkmaps, Mermaid).
- **Contact list** for on-call rotations.

---

### **2.7 Operational Workflows**
| **Workflow**             | **Best Practice**                                                                         | **Tools**                                      |
|--------------------------|------------------------------------------------------------------------------------------|------------------------------------------------|
| **Change Management**    | **GitOps (ArgoCD, Flux)** for infrastructure-as-code; **pre-production staging**.        | Terraform, Ansible, Kubernetes.               |
| **Incident Response**    | **Blameless postmortems** (Google SRE model); **SLI/SLO tracking**.                       | PagerDuty, Jira.                               |
| **Documentation**        | **Confluence/Wiki** for non-technical docs; **Markdown + Mermaid for technical**.        | Obsidian, Notion.                              |
| **Knowledge Sharing**    | **Weekly syncs**, **internal blog**, **runbook library**.                                 | Slack, MS Teams, GitHub Wiki.                  |

**Automation Scripts:**
- **Backup automation** (Bash/Python for rsync/NAKIVO).
- **Patch deployment** (Ansible for Windows/Linux).
- **Auto-scaling** (Kubernetes HPA, RightScale).

---

## **3. Schema Reference**
Below are key configuration schemas for common on-premise setups.

### **3.1 Network Schema (VLAN Example)**
| **VLAN ID** | **Purpose**               | **IP Range**       | **Firewall Rule**                     |
|-------------|---------------------------|--------------------|---------------------------------------|
| 10          | Management               | 192.168.10.0/24    | Allow from **SecOps VPN (10.0.0.0/8)** |
| 20          | Database                 | 192.168.20.0/24    | Allow from **App Tier (192.168.30.0/24)** |
| 30          | Application              | 192.168.30.0/24    | Deny all external access.             |
| 40          | Storage NAS              | 192.168.40.0/24    | Allow from **Backup Server (192.168.10.5)** |

### **3.2 Backup Schema (3-2-1 Rule)**
| **Copy** | **Location**       | **Type**          | **Retention** | **Encryption** |
|----------|--------------------|-------------------|---------------|----------------|
| 1        | Local NAS (ZFS)    | Full + Incremental | 30 days       | AES-256 (keyrotation monthly) |
| 2        | Offsite USB Drives | Full Snapshots    | 90 days       | BitLocker      |
| 3        | Cloud (AWS S3)     | Deduplicated     | 1 year        | KMS + S3 SSE  |

### **3.3 Security Policy Schema**
| **Policy**               | **Enforcement**                          | **Compliance Standard** |
|--------------------------|------------------------------------------|-------------------------|
| Password Complexity      | **8 chars + special chars + MFA**        | NIST SP 800-63B         |
| Port Security            | **SSH (22), RDP (3389), HTTPS (443 only)** | CIS Benchmark           |
| Guest Access             | **VLAN isolation + FQDN whitelisting**   | Zero Trust               |
| Audit Logs               | **Retain 1 year; immutable storage**     | PCI DSS, HIPAA          |

---

## **4. Query Examples**
### **4.1 Network Troubleshooting (Linux)**
**Check network latency:**
```bash
ping -c 10 192.168.10.1
traceroute google.com
```
**Check firewall rules (iptables):**
```bash
sudo iptables -L -n -v
sudo iptables -S  # Save rules
```
**Check MTU issues:**
```bash
ping -M do -s 1472 8.8.8.8  # Test with DF bit
```

### **4.2 Backup Verification (Bareos)**
**Test restore:**
```bash
bareos restore fileset="CriticalDB" catalog=MyCatalog
```
**Check backup status:**
```bash
bareos console
status jobid=12345
```

### **4.3 Security Auditing (OpenSCAP)**
**Scan for CIS benchmarks:**
```bash
openscap scan --profile xccdf_org.ssgproject.content_std_cis_Linux-7 level2 --results-sarif > scan.sarif
```
**Parse results:**
```bash
grep "result=FAIL" scan.sarif | jq
```

### **4.4 Monitoring Alerts (Prometheus)**
**Alert if CPU > 90% for 5 mins:**
```yaml
groups:
- name: high_cpu_alerts
  rules:
  - alert: HighCPUUsage
    expr: 100 * rate(node_cpu_seconds_total{mode="user"}[5m]) by (instance) > 90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High CPU on {{ $labels.instance }}"
```

---

## **5. Related Patterns**
| **Pattern**                     | **Use Case**                                                                 | **Reference Guide Link**                          |
|----------------------------------|------------------------------------------------------------------------------|---------------------------------------------------|
| **[Hybrid Cloud Best Practices]** | Combining on-premise with cloud (e.g., AWS Outposts, Azure Stack).          | [Link]                                           |
| **[Serverless On-Prem]**         | Running Kubernetes (K3s, k0s) or serverless (Knative) on bare metal.         | [Link]                                           |
| **[Edge Computing]**             | Distributed workloads (IoT gateways, branch offices).                        | [Link]                                           |
| **[Data Sovereignty]**           | Compliance-focused data storage (immutable logs, regional storage).         | [Link]                                           |
| **[Container Orchestration]**    | Kubernetes/Rancher best practices for on-premise clusters.                  | [Link]                                           |
| **[AI/ML On-Prem]**              | GPU-accelerated workloads (NVIDIA DGX, HPC clusters).                       | [Link]                                           |

---
**Note:** Replace `[Link]` with actual internal/external references.

---
**Word Count:** ~1,100 (excluding schema examples). Adjust depth based on audience (e.g., reduce complexity for ops teams).