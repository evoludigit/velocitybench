# **[Pattern] Security Troubleshooting Reference Guide**

---

## **1. Overview**
The **[Security Troubleshooting]** pattern provides a structured, step-by-step methodology to identify, diagnose, and resolve security-related issues in systems, applications, or networks. It ensures a systematic approach to security incidents, minimizing risk exposure while maintaining operational continuity. This guide covers key concepts, implementation steps, tooling validation, and common security scenarios.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Principles**
- **Incident Classification** – Categorize security events (e.g., unauthorized access, malware, misconfigurations).
- **Root Cause Analysis (RCA)** – Identify underlying vulnerabilities or misconfigurations.
- **Mitigation & Remediation** – Apply fixes and verify resolution.
- **Post-Mortem & Documentation** – Record lessons learned for future incidents.
- **Automation & Scalability** – Leverage tools and automation to streamline troubleshooting.

### **2.2 Common Security Troubleshooting Scenarios**
| **Scenario**               | **Description**                                                                 | **Typical Causes**                          |
|----------------------------|---------------------------------------------------------------------------------|--------------------------------------------|
| **Unauthorized Access**    | Suspicious logins, brute-force attempts, or privilege escalation.                | Weak credentials, misconfigured IAM.       |
| **Malware/Infection**      | Detecting malicious processes, cryptominers, or ransomware.                      | Phishing, unpatched vulnerabilities.       |
| **Configuration Drift**    | Deviation from security baselines (e.g., open ports, disabled firewalls).     | Poor patch management, misapplied policies. |
| **Data Leaks**             | Unauthorized data exposure (e.g., logs, databases, APIs).                       | Missing encryption, weak access controls.  |
| **DDoS/DOS Attacks**       | Abnormal traffic spikes overwhelming resources.                                | Lack of WAF rules, insufficient scaling.   |

### **2.3 Troubleshooting Workflow**
1. **Detection** – Identify an anomaly via logs, alerts, or monitoring tools.
2. **Containment** – Isolate affected systems to prevent lateral movement.
3. **Analysis** – Gather forensic evidence (e.g., logs, network traffic).
4. **Resolution** – Apply fixes (patches, policy updates, access revocation).
5. **Verification** – Confirm incident closure via validation checks.
6. **Post-Incident Review** – Update security procedures and tools.

---

## **3. Schema Reference**

### **3.1 Security Incident Schema**
Below is a structured schema for documenting security incidents. Use this as a template for automation (e.g., in SIEMs like Splunk or ELK).

| **Field**               | **Type**   | **Description**                                                                 | **Example Value**                     |
|-------------------------|------------|-------------------------------------------------------------------------------|----------------------------------------|
| `incident_id`           | String     | Unique identifier for the incident.                                           | `SEC-2024-001`                        |
| `severity`              | Enum       | Critical, High, Medium, Low (based on CVSS, NIST, or custom scale).            | `High`                                |
| `timestamp`             | Datetime   | When the incident was first detected or reported.                             | `2024-05-15T14:30:00Z`                |
| `source_system`         | String     | Affected system (host, app, network segment).                                | `web-server-01`                       |
| `action_taken`          | Array      | List of mitigation steps performed.                                           | `[{"step": "revoked access", "time": "2024-05-15T15:00:00Z"}]` |
| `root_cause`            | String     | Concise explanation of the vulnerability or misconfiguration.                 | `Unpatched CVE-2023-1234 exploit.`    |
| `resolution_status`     | Boolean    | `true` if fully resolved, `false` if pending.                               | `true`                                |
| `related_alerts`        | Array      | References to linked security alerts (e.g., from SIEM).                      | `[{"alert_id": "ALRT-005", "tool": "Splunk"}]` |
| `forensic_data`         | Object     | Raw evidence (logs, hashes, network captures).                               | `{"logs": "/var/log/auth.log", "pcap": "capture-20240515.pcap"}` |

### **3.2 Tooling Schema (SIEM Integration)**
For SIEM tools (e.g., **Splunk, ELK, Microsoft Sentinel**), standardize incident data with this schema:

```json
{
  "incident": {
    "id": "SEC-2024-001",
    "severity": "high",
    "source": {
      "system": "web-server-01",
      "component": "nginx"
    },
    "timestamp": "2024-05-15T14:30:00Z",
    "description": "Brute-force attack detected on admin portal.",
    "actions": [
      {
        "type": "access_revoked",
        "user": "admin_user",
        "time": "2024-05-15T15:00:00Z"
      }
    ],
    "forensic_evidence": {
      "logs": ["auth.log", "fail2ban.log"],
      "ip_addresses": ["192.0.2.1", "203.0.113.45"]
    }
  }
}
```

---

## **4. Query Examples**

### **4.1 SIEM Query (Splunk SPL)**
**Scenario:** Find all high-severity incidents involving brute-force attempts.
```splunk
index=security sourcetype=security_alerts
| search severity="High" AND (event="bruteforce" OR event="failed_login")
| table incident_id, source_system, timestamp, action_taken
| sort -timestamp
```

### **4.2 ELK (Kibana) Search**
**Scenario:** Query for misconfigured S3 buckets in AWS.
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event.category": "aws.s3" } },
        { "bool": {
            "should": [
              { "term": { "response.status": "403" } },  // Access denied
              { "term": { "policy.violation": "true" } }   // Policy mismatch
            ]
          }
        }
      ]
    }
  }
}
```

### **4.3 AWS CLI Query (Check for Open Ports)**
**Scenario:** Scan EC2 instances for open ports (troubleshoot unauthorized access).
```bash
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].[InstanceId, NetworkInterfaces[].Groups[].GroupId]"
```
**Follow-up:** Use `nmap` or AWS Security Hub to verify open ports:
```bash
nmap -p 22,80,443 <instance-ip>
```

### **4.4 Python Script (Log Analysis)**
**Scenario:** Parse Apache logs for suspicious 404 errors (potential scanning).
```python
import re
from collections import defaultdict

log_file = "access.log"
suspicious_pattern = re.compile(r'404\s+\S+\s+\S+\s+\[\S+\]\s+"GET\s+(.+) HTTP/1.1"\s+404')

error_endpoints = defaultdict(int)
with open(log_file, 'r') as f:
    for line in f:
        match = suspicious_pattern.search(line)
        if match:
            endpoint = match.group(1)
            error_endpoints[endpoint] += 1

for endpoint, count in sorted(error_endpoints.items(), key=lambda x: -x[1]):
    print(f"Endpoint: {endpoint}, Requests: {count}")
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                          |
|----------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Defense in Depth]**           | Layered security controls (e.g., firewalls + encryption + IAM).                | Designing secure architectures.           |
| **[Zero Trust Architecture]**   | Verify every access request, even inside the network.                          | High-security environments.              |
| **[Security Monitoring]**        | Real-time detection of anomalies via SIEMs, IDS/IPS.                           | Continuous threat monitoring.            |
| **[Incident Response Playbook]** | Step-by-step guidance for handling breaches.                                   | During active security incidents.        |
| **[Compliance Automation]**      | Automate audit checks (e.g., CIS benchmarks, GDPR).                            | Regulatory compliance verification.      |
| **[Threat Modeling]**            | Proactively identify vulnerabilities in system design.                         | Pre-deployment security reviews.         |

---

## **6. Best Practices**
1. **Standardize Terminology** – Use consistent labels (e.g., `severity: High`, `status: Resolved`).
2. **Automate Where Possible** – Integrate SIEMs with ticketing systems (e.g., Jira, ServiceNow).
3. **Document Everything** – Maintain runbooks for recurring issues (e.g., "How to patch CVE-2023-XXXX").
4. **Test Remediation Plans** – Use sandbox environments to validate fixes.
5. **Stay Updated** – Regularly review CVEs (e.g., [NVD](https://nvd.nist.gov/)) and tooling.

---
**Example Runbook Template:**
```
### Incident: Brute-Force on SSH (High)
**Trigger:** 10+ failed login attempts in 5 minutes.
**Steps:**
1. Revoke SSH keys for affected user (`aws iam remove-user-ssh-key-key-pair`).
2. Temporarily block IP in WAF (`aws waf add-statement --priority 0 --action Block`).
3. Rotate credentials via Secrets Manager.
**Validation:** Confirm no further attempts in 24h.
**Tools:** Splunk, AWS GuardDuty, Fail2Ban.
```