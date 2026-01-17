---

# **[Pattern] Security Troubleshooting Reference Guide**

---

## **Overview**
This guide documents the **Security Troubleshooting Pattern**, a structured approach for diagnosing, isolating, and resolving security-related incidents or anomalies. The pattern emphasizes **methodical analysis**, **logging best practices**, and **collaborative validation** to reduce time-to-resolution while maintaining operational stability. It applies to **cloud resources, on-premises infrastructure, and hybrid environments**, covering issues like unauthorized access, misconfigurations, compliance violations, and lateral movement threats.

Key principles include:
- **Isolate the issue** (scope, impact, and root cause).
- **Validate with observability tools** (logs, metrics, traces).
- **Apply remediation with least privilege** (avoid cascading failures).
- **Document findings** for auditing and future reference.

---

## **Schema Reference**
The following tables describe the core components of the Security Troubleshooting Pattern.

### **1. Troubleshooting Phases**
| **Phase**               | **Objective**                                                                 | **Key Actions**                                                                 | **Tools/Artifacts**                          |
|-------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|
| **Detection**           | Identify a potential security event or anomaly.                             | Review alerts (SIEM, WAF, IAM), check logs (CloudTrail, VPC Flow Logs), monitor anomalies (unusual API calls, unauthorized SSH access). | SIEM (Splunk, Datadog), Cloud Audit Logs, Custom Dashboards |
| **Triage**              | Assess severity, scope, and impact.                                          | Check affected systems/user accounts, review related events, correlate telemetry. | Incident Management Tools (Jira, PagerDuty), Threat Intelligence Feeds |
| **Analysis**            | Determine root cause and attack vector.                                      | Deep-dive logs/traces (e.g., AWS X-Ray, GCP Trace), inspect misconfigurations (e.g., overly permissive IAM roles), analyze malware signatures. | Forensic Tools (Velociraptor, TheHive), Static Analysis (Trivy, Checkmarx) |
| **Remediation**         | Apply fixes with minimal disruption.                                         | Revoke compromised credentials, patch vulnerabilities, adjust policies (e.g., MFA enforcement), isolate affected systems. | Configuration Management (Ansible, Terraform), IAM Console, Firewall Rules |
| **Recovery**            | Restore normal operations and validate success.                              | Rotate credentials, restore backups, monitor for recurrence, update runbooks.   | Backup Systems (AWS Backup, Vault), Custom Scripts |
| **Post-Mortem**         | Document lessons learned for improvement.                                    | Review incident timeline, assess response time, update playbooks, train teams.  | Runbook Documentation, Slack/Confluence Updates |

---

### **2. Common Security Issues and Their Indicators**
| **Issue Type**          | **Indicators**                                                                 | **Example Events/Logs**                                      | **Tools for Detection**                  |
|-------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------|------------------------------------------|
| **Unauthorized Access** | Suspicious logins (e.g., brute force, unusual IP, MFA bypass).               | `AWS CloudTrail: "UserAccessKeyExpired"` + `FailedLoginAttempts=5` | SIEM, GuardDuty, AWS Inspector          |
| **Misconfiguration**    | Overly permissive policies (e.g., public S3 buckets, wildcard IAM permissions). | `S3 AccessLog: "PUT /${bucket-name}/*"` with `PublicRead`   | AWS Config, Checkov, Prisma Cloud        |
| **Data Exfiltration**   | Unusual outbound traffic (e.g., large data transfers to unknown locations).   | `VPC Flow Logs: "DestinationPort=443, BytesSent=5GB"`         | Network Security Groups, Wazuh           |
| **Lateral Movement**    | Unauthorized privilege escalation (e.g., `sudo`, `su`, or cross-AZ jumps).     | `Linux Auth Logs: "auth.log: user 'admin' executed 'sudo su'"` | SIEM, CrowdStrike, Splunk               |
| **Compliance Violation**| Failing rule checks (e.g., missing encryption, stale certs).                  | `AWS Config: "Rule='aws-encrypt-ebs-volumes' => FAILED"`      | AWS Config Rules, Open Policy Agent (OPA)|
| **Malware Activity**    | Unusual process execution (e.g., `powershell -nop -ep bypass`).               | `Windows Event Log: "EventID=4688 (Process Creation)"`        | Windows Defender ATP, Wazuh             |

---

### **3. Key Query Examples**
Below are **query templates** for common troubleshooting scenarios using tools like **AWS Athena (CloudTrail logs)**, **GCP BigQuery (Audit Logs)**, or **SIEM (Splunk/ELK)**.

#### **1. Find Unauthorized API Calls (AWS CloudTrail)**
**Query (Athena):**
```sql
SELECT
  userIdentity.userName,
  eventName,
  awsRegion,
  eventTime,
  requestParameters.*.*,
  responseElements.*.*
FROM cloudtrail_logs
WHERE eventName IN ('AssumeRole', 'GenerateDataKey', 'GetSecretValue')
  AND userIdentity.type = 'IAMUser'
  AND eventTime > datetime('now', '-1h')
ORDER BY eventTime DESC
LIMIT 100;
```
**Filter for suspicious activity:**
- Add `AND errorCode != 'Success'` or `AND resourceType = 'AWS::RDS::DBInstance'` (unusual DB access).

---

#### **2. Detect Publicly Accessible S3 Buckets (AWS Config)**
**Query (Athena):**
```sql
SELECT
  resourceId,
  resourceType,
  configuration.blockPublicAcls,
  configuration.publicAccessBlockConfiguration
FROM awsconfig_buckets
WHERE configuration.publicAccessBlockConfiguration IS NULL
  OR configuration.publicAccessBlockConfiguration.blockPublicAcls = false;
```
**Alternative (AWS CLI):**
```bash
aws s3api list-buckets --query "Buckets[?CreationDate==`$(date -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')][].Name"
```

---

#### **3. Find Stale IAM Credentials (AWS IAM)**
**Query (Athena):**
```sql
SELECT
  user_name,
  credential_last_used,
  credential_last_rotated
FROM iam_users
WHERE credential_last_rotated < date_sub(current_date(), INTERVAL 90 DAY)
  AND credential_last_used IS NULL;
```

---

#### **4. Correlate Failed Logins with IP Reputation (SIEM - Splunk)**
**Query (Splunk):**
```splunk
index=aws_cloudtrail sourcetype=aws:cloudtrail_event
| search userIdentity.type="IAMUser" AND eventName="ConsoleLogin" AND outcome="Fail"
| lookup threat_intel ip=clientIp as reputation output reputation
| where reputation="Malicious"
| table _time, userIdentity.userName, clientIp, reputation
```

---
#### **5. Detect Unusual SSH Brute Force (Linux Syslog)**
**Query (ELK/Grok Parsing):**
```kibana
index=linux logs
| json { "source": "message", "target": "data" }
| where data.type="SSHD" AND data.event="Failed password"
| stats count by source_ip, user
| sort -count desc
| where count > 10
```

---

### **4. Related Patterns**
To complement **Security Troubleshooting**, reference these patterns for context:
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Observability-Driven Development](link)** | Design systems with logging, metrics, and traces for proactive monitoring. | During architecture design or new feature rollouts. |
| **[Zero Trust Architecture](link)** | Assume breach; enforce least-privilege access and micro-segmentation.       | For high-security environments (e.g., finance, healthcare). |
| **[Incident Response Playbooks](link)** | Standardized procedures for common security incidents.                     | After detection (to guide triage and remediation). |
| **[Policy as Code](link)**       | Enforce security policies via Gitops (e.g., Terraform, Open Policy Agent).   | During infrastructure-as-code deployments.      |
| **[Runtime Security](link)**    | Monitor runtime behavior (e.g., eBPF, Falco) to catch anomalies.              | For containerized or serverless workloads.       |

---

## **Best Practices**
1. **Automate Detection**:
   - Set up **SIEM alerts** for known indicators (e.g., AWS GuardDuty findings).
   - Use **CloudWatch Alarms** for anomalous metrics (e.g., `ErrorRate > 5%`).

2. **Isolate Early**:
   - Quarantine compromised hosts immediately (e.g., `aws ec2 stop-instances --instance-ids i-xxxxx`).
   - Rotate credentials in batch for affected users (`aws iam update-login-profile --user-name ADMIN --password "NEWPASS"`).

3. **Document Everything**:
   - Tag incidents with **Jira tickets** or **Slack threads** for traceability.
   - Update **runbooks** with new attack vectors (e.g., "Brute-force via API Gateway").

4. **Leverage Threat Intelligence**:
   - Enrich logs with **STIX/TAXII feeds** (e.g., AlienVault OTX, MISP).
   - Block known malicious IPs/asns at the **network level** (e.g., AWS Security Groups).

5. **Validate Fixes**:
   - After remediation, **re-run detection queries** to confirm resolution.
   - Use **Chaos Engineering** (e.g., Gremlin) to test resilience to future attacks.

---
## **Troubleshooting Checklist**
| **Step**                | **Action Items**                                                                 |
|--------------------------|---------------------------------------------------------------------------------|
| **1. Confirm the Issue** | Verify alerts are legitimate (avoid false positives).                        |
| **2. Scope Impact**      | Identify affected systems/users via logs (e.g., `whoami` on compromised hosts). |
| **3. Gather Telemetry**  | Export logs to **S3/Cloud Storage** for offline analysis.                      |
| **4. Hypothesize**       | Brainstorm likely attack paths (e.g., "Did an insider leak credentials?").     |
| **5. Test Remediation**  | Apply fixes in a **staging environment** first if possible.                    |
| **6. Communicate**       | Notify stakeholders (e.g., "Security team investigating S3 exposure").        |
| **7. Review Logs**       | Search for **secondary indicators** (e.g., `curl` commands to exfiltrate data).|

---
## **Limitations**
- **False Positives/Negatives**: SIEM alerts may require manual validation.
- **Tooling Gaps**: Some cloud providers lack native forensic tools (e.g., Azure lacks AWS X-Ray).
- **Performance Impact**: Heavy logging can increase latency (monitor `cloudtrail:PutEvent` metrics).
- **Human Error**: Misconfigured queries or missed logs can lead to delayed detection.

---
## **Further Reading**
- [AWS Security Troubleshooting Guide](https://docs.aws.amazon.com/security/troubleshooting/latest/userguide/welcome.html)
- [GCP Security Command Center](https://cloud.google.com/security-command-center)
- [MITRE ATT&CK Framework](https://attack.mitre.org/) (for attack path analysis)
- [CIS Controls v8](https://www.cisecurity.org/controls/) (baseline for hardening).