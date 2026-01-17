# **[Pattern] Security Strategies Reference Guide**

---

## **Overview**
The **Security Strategies** pattern provides a structured approach to designing, implementing, and enforcing security controls across applications, systems, and infrastructure. This pattern ensures defense-in-depth by combining defensive, preventive, detective, and responsive strategies. It covers authentication, authorization, encryption, monitoring, logging, incident response, and compliance alignment. The goal is to mitigate risks while maintaining operational efficiency.

This guide outlines **key concepts**, **implementation details**, and **best practices** to deploy Security Strategies effectively.

---

## **Schema Reference**

| **Category**          | **Component**               | **Description**                                                                                     | **Example Technologies**                                                                 | **Key Attributes**                                                                                                                                                     |
|-----------------------|-----------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authentication**    | Multi-Factor Authentication | Adds layers beyond passwords (e.g., SMS, TOTP, hardware keys).                                      | Duo, Google Authenticator, YubiKey                                                      | - **Factor Types**: Knowledge, Possession, Inherence <br> - **Session Timeout**: Configurable (e.g., 15–60 mins) <br> - **Fallback Mechanisms**: Backup codes |
|                       | OAuth 2.0 / OpenID Connect | Federated authentication via third-party identity providers (IdPs).                                | Azure AD, Okta, Auth0                                                                | - **Scopes**: `openid`, `profile`, `email` <br> - **Token Types**: JWT, Refresh Tokens <br> - **PKCE**: Enabled for public clients                              |
| **Authorization**     | Role-Based Access Control   | Grants permissions based on predefined roles (e.g., Admin, Editor, Guest).                          | AWS IAM, Azure RBAC, Spring Security Roles                                               | - **Role Hierarchies**: Inheritance (e.g., `Editor → Viewer`) <br> - **Attribute-Based**: Dynamic policies (e.g., `Department=Finance`)           |
|                       | Attribute-Based Access      | Fine-grained access using user attributes (e.g., time, location, device).                          | AWS IAM Policies, Microsoft Entra ID Policies                                           | - **Conditions**: `IpAddress`, `DeviceCompliance`, `TimeBased` <br> - **Temporal Constraints**: Scheduled access (e.g., 9–5 ET)                    |
| **Data Protection**   | Encryption at Rest          | Secures data stored in databases/filesystems with encryption keys.                                 | AES-256, AWS KMS, Azure Disk Encryption                                                   | - **Key Management**: HSM-backed (e.g., AWS CloudHSM) <br> - **Key Rotation**: Automated (e.g., 90-day cycle)                          |
|                       | Encryption in Transit       | Secures data in motion via TLS/SSL and VPNs.                                                       | TLS 1.2/1.3, WireGuard, OpenVPN                                                            | - **Cipher Suites**: `TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384` <br> - **Certificate Lifespan**: 1–3 years (rotated proactively) |
|                       | Field-Level Encryption      | Encrypts individual data fields (e.g., PII) in databases.                                         | Oracle Transparent Data Encryption, Microsoft Always Encrypted                           | - **Query Overhead**: Minimal (e.g., SQL Server `COLUMN_ENCRYPTED`) <br> - **Key Derivation**: PBKDF2, Argon2                 |
| **Monitoring**        | SIEM Integration            | Centralized logging and anomaly detection via SIEM tools.                                         | Splunk, ELK Stack (Elasticsearch, Logstash, Kibana), Microsoft Sentinel                    | - **Event Sources**: API logs, auth failures, network traffic <br> - **Alert Thresholds**: Customizable (e.g., 5 failed logins in 5 mins)      |
|                       | Runtime Application Self-Protection (RASP) | Monitors app behavior for intrusions during execution.                                            | Imperva SecureSphere, AWS WAF + GuardDuty                                                  | - **Detection Rules**: Heuristics, ML-based anomalies <br> - **Response Actions**: Block requests, log events                              |
| **Incident Response** | Playbook Automation         | Predefined steps for handling breaches (e.g., contain, eradicate, recover).                      | ServiceNow, PagerDuty, AWS Security Hub                                                     | - **Escalation Paths**: Tiered (L1 → L3) <br> - **Automation Triggers**: Failed logins, policy violations                     |
|                       | Forensic-Ready Logging      | Preserves raw logs for post-incident analysis with timestamps and metadata.                       | AWS CloudTrail, Azure Monitor, Wazuh                                                     | - **Retention Policies**: 7–365 days <br> - **Immutable Storage**: WORM (Write-Once, Read-Many) disks                     |
| **Compliance**        | Policy-as-Code              | Enforces compliance via automated checks (e.g., CIS benchmarks, GDPR).                           | Open Policy Agent (OPA), Terraform Policies, AWS Config                                     | - **Framework Alignment**: NIST, ISO 27001, SOC 2 <br> - **Audit Trails**: Change logs for policy updates                          |
|                       | Automated Compliance Scanning | Scans infrastructure/configurations for deviations from baselines.                                | Drift Detection: AWS Config, Azure Policy, Prisma Cloud                                    | - **Remediation**: Auto-apply fixes (e.g., patch vulnerabilities) <br> - **Frequency**: Daily/Continuous                          |

---

## **Implementation Details**

### **1. Defensive Strategies**
- **Zero Trust Architecture (ZTA):**
  - **Principle**: "Never trust, always verify."
  - **Implementation**:
    - Enforce MFA for all users/apps.
    - Segment networks (e.g., micro-segmentation with firewalls like Palo Alto).
    - Use short-lived credentials (e.g., OAuth tokens with 1-hour expiry).
  - **Tools**: AWS Zero Trust, Microsoft BeyondCorp, CrowdStrike Falcon.

- **Least Privilege Access:**
  - **Principle**: Grant only the permissions required for a user’s role.
  - **Implementation**:
    - Regularly audit IAM/RBAC roles (e.g., AWS IAM Access Analyzer).
    - Revoke access for inactive users (e.g., 90 days of inactivity).
  - **Tools**: AWS IAM Policy Simulator, Azure Policy Guardian.

### **2. Preventive Strategies**
- **Data Classification:**
  - Label data by sensitivity (e.g., Public, Internal, PII, Confidential).
  - Apply access controls and encryption based on labels.
  - **Tools**: Microsoft Information Protection, AWS Data Labeling.

- **Hardening Configurations:**
  - Apply security baselines (e.g., CIS benchmarks) to servers/VMs.
  - Disable unused services/ports (e.g., disable Telnet via AWS SSM).
  - **Tools**: OpenSCAP, Encase Enterprise, Chef InSpec.

### **3. Detective Strategies**
- **Anomaly Detection:**
  - Use ML to flag unusual behavior (e.g., sudden data exfiltration).
  - **Example Query (SIEM):**
    ```sql
    -- Detect unusually high data export from a user
    SELECT user_id, COUNT(*) as export_count
    FROM api_logs
    WHERE action = 'data_export' AND timestamp > NOW() - INTERVAL '1 hour'
    GROUP BY user_id
    HAVING COUNT(*) > 10  -- Threshold
    ```
  - **Tools**: Darktrace, Splunk ES.

- **Behavioral Analytics:**
  - Monitor for deviations from normal user patterns (e.g., login from unusual location).
  - **Tools**: Microsoft Defender for Cloud Apps, Okta Adaptive MFA.

### **4. Responsive Strategies**
- **Incident Response Plan (IRP):**
  - Define roles (e.g., Incident Commander, Technical Lead) and escalation paths.
  - Include runbooks for common scenarios (e.g., ransomware, credential stuffing).
  - **Template Structure:**
    ```
    1. **Detection**: How to identify the incident (e.g., SIEM alerts).
    2. **Containment**: Isolate affected systems (e.g., terminate compromised IPs).
    3. **Eradication**: Remove root cause (e.g., patch vulnerable software).
    4. **Recovery**: Restore systems from clean backups.
    5. **Post-Incident**: Lessons learned (e.g., update IRP, retrain staff).
    ```

- **Automated Containment:**
  - Use tools to auto-isolate compromised hosts (e.g., block IPs in firewalls).
  - **Example (Terraform + AWS):**
    ```hcl
    resource "aws_security_group_rule" "block_compromised_ip" {
      security_group_id = aws_security_group.web.id
      type              = "ingress"
      from_port         = 0
      to_port           = 0
      protocol          = "-1"
      cidr_blocks       = ["${var.compromised_ip}/32"]  # Dynamic via Lambda
      description       = "Temporarily block compromised IP"
    }
    ```

### **5. Compliance Alignment**
- **Automated Compliance Checks:**
  - Integrate policy-as-code with CI/CD pipelines (e.g., fail builds if non-compliant).
  - **Example (Open Policy Agent):**
    ```rego
    package aws

    default allow = true

    violation {
      input.resource_type == "ec2-instance"
      input.security_groups[*] == null
    }
    ```
  - **Tools**: Policy-as-Code (PaC), AWS Config Rules.

- **Audit Trail:**
  - Ensure all actions (e.g., config changes, access grants) are logged and immutable.
  - **Tools**: AWS CloudTrail, Azure Activity Log, Google Cloud Audit Log.

---

## **Query Examples**

### **1. Detect Unpatched Vulnerabilities (SIEM Query)**
```sql
-- Find servers with CVEs from NVD (National Vulnerability Database)
SELECT
    host_name,
    vulnerability_id,
    severity_score
FROM
    vulnerability_scans
WHERE
    scan_date > CURRENT_DATE - INTERVAL '7 days'
    AND severity_score > 7.0  -- Critical/High
ORDER BY
    severity_score DESC;
```

### **2. Identify Overprivileged IAM Roles (AWS CLI)**
```bash
# List roles with "*" permissions
aws iam list-policies --scope Local --output text |
  grep -E '\*|All' --color=always |
  awk '{print $3}'
```

### **3. Query for Sensitive Data Exposure (Database Audit)**
```sql
-- Find queries accessing PII without encryption
SELECT
    user_name,
    query_text,
    COUNT(*) as access_count
FROM
    audit_logs
WHERE
    query_text LIKE '%SELECT% name, ssn%'  -- Pattern for sensitive fields
    AND encrypted = FALSE
GROUP BY
    user_name, query_text
HAVING
    COUNT(*) > 5;  -- Threshold for repeated access
```

### **4. Detect Shadow IT (Network Traffic Analysis)**
```python
# Pseudocode for detecting unauthorized cloud services
def detect_shadow_it(logs):
    suspicious_domains = ["dropbox.com", "weTransfer.com", "mega.nz"]
    for log in logs:
        if log["domain"] in suspicious_domains and log["user"] not in whitelisted_users:
            alert("Potential Shadow IT usage by " + log["user"])
```

---

## **Related Patterns**

| **Related Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|-----------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Defense in Depth]**            | Layers of security controls to protect against multiple failure points.                            | When designing multi-layered security architectures (e.g., perimeter + network + host).           |
| **[Secure by Design]**            | Integrating security into the SDLC (e.g., DevSecOps).                                               | During application development to embed security from the start.                                    |
| **[Observability]**               | Centralized logging, metrics, and tracing for security monitoring.                                  | To detect and diagnose security incidents in real-time.                                           |
| **[Least Privilege Access]**      | Minimizing permissions to reduce attack surface.                                                    | For IAM/RBAC configurations to limit access based on role requirements.                             |
| **[Data Minimization]**           | Collecting and retaining only necessary data.                                                        | To reduce exposure from data breaches and comply with GDPR/CCPA.                                   |
| **[Incident Response]**           | Structured approach to handling security incidents.                                                 | After a breach is detected to contain, eradicate, and recover effectively.                         |
| **[Threat Modeling]**             | Identifying threats early in the development lifecycle.                                             | During design phases to proactively address vulnerabilities.                                      |

---

## **Best Practices**
1. **Start with Zero Trust**: Assume breach and verify every access request.
2. **Automate Compliance**: Use policy-as-code to reduce manual errors.
3. **Monitor Continuously**: Detect anomalies before they escalate (e.g., SIEM + RASP).
4. **Test Resilience**: Conduct red-team exercises and penetration tests.
5. **Document Everything**: Maintain up-to-date runbooks for incident response.
6. **Stay Updated**: Patch systems regularly and update threat intelligence feeds (e.g., MITRE ATT&CK).
7. **Train Teams**: Educate users on phishing, password hygiene, and secure coding.

---
**Last Updated**: [Insert Date]
**Version**: [X.Y]