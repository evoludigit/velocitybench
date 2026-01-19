# **[Pattern] Security Troubleshooting Reference Guide**

---

## **Overview**
The **Security Troubleshooting** pattern provides a structured approach to diagnosing, investigating, and resolving security-related issues in cloud-native, on-premises, or hybrid environments. This guide outlines key concepts, troubleshooting workflows, common security anomalies, diagnostic tools, and best practices for mitigating risks. It applies to security events such as unauthorized access attempts, misconfigured resources, compliance violations, or anomalies in user behavior. The pattern emphasizes correlation of logs, leveraging automation, and following a **defensive debugging** approach to minimize blast radius.

Key use cases include:
- Investigating failed authentication attempts or brute-force attacks.
- Diagnosing improper IAM policies or over-permissive access controls.
- Analyzing unexpected API calls or data exfiltration attempts.
- Addressing compliance gaps detected by security tools.

---

## **Implementation Details**

### **Key Concepts**
| Concept                | Definition                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------|
| **Security Event**     | An anomaly detected by a security tool (e.g., failed login, unauthorized API call).         |
| **Root Cause**         | The underlying issue (e.g., weak password, misconfigured RBAC policy).                       |
| **Threat Vector**      | How an attacker exploits a vulnerability (e.g., phishing, privilege escalation).             |
| **Defensive Debugging**| Actively monitoring and validating security controls to detect breaches early.             |
| **Blast Radius**       | Scope of impact if an issue is left unaddressed (e.g., one compromised credential).       |
| **Security Control**   | A safeguard (e.g., MFA, network firewall) preventing or mitigating an attack.               |

---

### **Troubleshooting Workflow**
1. **Detection**
   Triggered by alerts from SIEM, CSPM, or custom monitoring (e.g., CloudTrail for AWS, Azure Sentinel).
2. **Triage**
   Classify events by severity and type (e.g., login failure, policy violation).
3. **Investigation**
   Correlate logs from multiple sources (e.g., authentication logs + API calls).
4. **Remediation**
   Apply fixes (e.g., rotate credentials, tighten policies) and validate resolution.
5. **Post Morton**
   Document findings, update playbooks, and refine detection rules.

---

### **Common Security Anomalies & Patterns**
| Anomaly Type               | Description                                                                 | Possible Root Cause                          |
|----------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **Brute Force Attacks**    | Repeated failed login attempts from a single IP.                           | Weak credentials, exposed RDP/SMB.          |
| **Over-Permissive IAM**    | User/role granted excessive permissions (e.g., `*` in `Allow` policies).   | Misconfigured RBAC, automated policy generation. |
| **Data Exfiltration**      | Unusual outbound API calls or large file downloads.                        | Compromised credentials, missing DLP rules. |
| **Lateral Movement**       | Unauthorized access from one system to another (e.g., jump hosts).        | Shared credentials, weak network segmentation. |
| **Compliance Violation**   | Non-compliance with CIS benchmarks or frameworks (e.g., PCI DSS).         | Missing patches, outdated security groups. |

---

## **Schema Reference**
Below are key schema elements for security troubleshooting data models. Adapt these to your tooling (e.g., Terraform, OpenPolicyAgent, or custom scripts).

### **1. Security Event Schema**
```json
{
  "event_id": "unique_identifier",
  "timestamp": "ISO_8601_format",
  "severity": "low|medium|high|critical",
  "type": "login_failure|api_call|policy_violation|network_scan",
  "source": {
    "tool": "SIEM|CSPM|CloudTrail",
    "resource": "user|role|service_account",
    "region": "us-east-1"
  },
  "details": {
    "user_agent": "string",
    "ip_address": "public_ip",
    "failed_attempts": "integer",
    "affected_resource": "arn|uri"
  },
  "related_events": ["event_id_1", "event_id_2"] // For correlation
}
```

### **2. Remediation Playbook Schema**
```json
{
  "playbook_id": "unique_identifier",
  "anomaly_type": "brute_force|over_permissive_iam",
  "steps": [
    {
      "action": "rotate_credentials|restrict_policy",
      "tool": "AWS IAM|GCP IAM|Custom Script",
      "prerequisites": ["rule_1", "rule_2"],
      "validation_query": "sql_or_graphql_query"
    }
  ],
  "blast_radius": "low|medium|high",
  "owner": "security_team|devops"
}
```

---

## **Query Examples**
Use these queries to analyze security events in databases (e.g., PostgreSQL) or SIEM tools (e.g., Splunk, ELK).

### **1. Find Brute Force Attempts (Last 24 Hours)**
```sql
SELECT
  user_agent,
  ip_address,
  COUNT(*) AS failed_attempts
FROM security_events
WHERE
  type = 'login_failure'
  AND timestamp > NOW() - INTERVAL '24 hours'
  AND severity = 'high'
GROUP BY user_agent, ip_address
HAVING COUNT(*) > 5
ORDER BY failed_attempts DESC;
```

### **2. Detect Over-Permissive IAM Policies (AWS CloudTrail)**
```sql
SELECT
  resource,
  action,
  principal
FROM cloudtrail_logs
WHERE
  event_name IN ('PassRole', 'AttachPolicy', 'PutUserPolicy')
  AND resource LIKE '%*%'  -- Wildcard in resource/condition
ORDER BY timestamp DESC;
```

### **3. Correlate API Calls with Unusual Data Transfer (GCP Logs)**
```sql
SELECT
  user_email,
  method,
  payload_size_mb,
  timestamp
FROM api_calls
WHERE
  method = 'POST'
  AND payload_size_mb > 100  -- Large payload threshold
  AND LAG(user_email) OVER (
    PARTITION BY user_email
    ORDER BY timestamp
    ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) != user_email
ORDER BY timestamp;
```

### **4. Validate Remediation for Policy Changes**
```sql
SELECT
  policy_arn,
  last_modified_date,
  denied_actions
FROM iam_policies
WHERE
  last_modified_date > CURRENT_DATE - INTERVAL '7 days'
  AND denied_actions LIKE '%deny %';
```

---

## **Diagnostic Tools**
| Tool                  | Purpose                                                                 | Example Use Case                          |
|-----------------------|-------------------------------------------------------------------------|-------------------------------------------|
| **SIEM (Splunk/Elastic)** | Centralized log correlation and alerting.                               | Detecting lateral movement across systems. |
| **CSPM (Prisma Cloud/Checkov)** | Scans cloud resources for misconfigurations.                           | Finding open S3 buckets.                 |
| **CloudTrail/Azure Monitor** | Audits API calls and admin actions.                                       | Tracing a compromised service account.     |
| **Wazuh/Valido**      | Open-source security monitoring for on-prem/containerized workloads.   | Detecting CVE exploiting unpatched hosts. |
| **Terraform Policy Checks** | Enforce security rules during IaC deployment.                          | Blocking storage classes with `s3:PutObject`. |
| **Custom Scripts (Python/Golang)** | Ad-hoc analysis (e.g., parsing logs for anomalies).                    | Analyzing DNS exfiltration patterns.     |

---

## **Best Practices**
1. **Automate Triage**
   Use ML-based anomaly detection (e.g., AWS GuardDuty) to reduce alert fatigue.
2. **Isolate Incidents**
   Quarantine affected systems (e.g., detach IAM roles, revoke SSH keys).
3. **Validate Fixes**
   Re-run queries after remediation to confirm resolution.
4. **Document Lessons Learned**
   Update playbooks with new attack vectors or tooling gaps.
5. **Monitor for Reoccurrence**
   Set up long-term alerts for similar patterns.

---

## **Related Patterns**
| Pattern                     | Description                                                                 | When to Use                                                  |
|-----------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------|
| **[Defensive Deployment]**  | Harden infrastructure before deployment (e.g., immutable AMIs, least privilege). | Proactive security during IaC pipelines.                     |
| **[Chaos Engineering]**     | Test system resilience to failures (e.g., kill pods randomly).              | Validate security controls under stress.                     |
| **[Compliance as Code]**    | Enforce policies via IaC (e.g., Terraform modules).                        | Automate compliance checks in CI/CD.                         |
| **[Audit Logging]**         | Centralize logs for forensic analysis.                                       | Investigating post-breach incidents.                        |
| **[Zero Trust]**            | Assume breach, enforce least privilege.                                     | High-security environments (e.g., finance, healthcare).      |

---
**Note:** For advanced scenarios, integrate with **SOAR (Security Orchestration, Automation, and Response)** tools (e.g., Palo Alto Cortex XSOAR) to automate response workflows.