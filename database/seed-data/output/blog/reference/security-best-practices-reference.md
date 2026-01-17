**[Pattern] Security Best Practices – Reference Guide**

---

### **Overview**
Security Best Practices is a **pattern** that defines reusable, proven safeguards to minimize risk, protect sensitive data, and ensure compliance across applications, infrastructure, and workflows. This pattern encompasses technical controls, operational policies, and governance strategies to detect, deter, and mitigate threats. It applies to **all systems** (cloud, on-premises, hybrid) and **all roles** (developers, DevOps, security teams).

Key objectives:
- **Prevent** unauthorized access or data breaches.
- **Detect** suspicious activity early via monitoring and alerts.
- **Respond** quickly to incidents with least-privilege access and automated remediation.
- **Comply** with regulations (GDPR, HIPAA, SOC 2, ISO 27001).

Best practices are categorized by **layers** (e.g., identity, infrastructure, application code) and **phases** (development, deployment, runtime). This guide provides a **scannable, actionable framework** for implementing these practices in your environment.

---

### **Security Best Practices: Schema Reference**

The pattern follows a **modular structure** with core components:

| **Category**          | **Subcategory**               | **Control Name**                     | **Description**                                                                                     | **Tools/Techniques**                                                                                     |
|-----------------------|--------------------------------|--------------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Identity & Access** | **Authentication**             | Multi-Factor Authentication (MFA)     | Require a second factor (TOTP, hardware key, biometric) for all privileged access.                  | Duo, Microsoft Authenticator, YubiKey, RSA SecurID                                    |
|                       |                                | Just-In-Time (JIT) Access             | Grant temporary access via approval workflows (e.g., for CI/CD pipelines).                          | HashiCorp Vault, CyberArk, Okta                                                                         |
|                       | **Authorization**              | Principle of Least Privilege (PoLP)   | Restrict permissions to only required roles/functions (IAM roles/policies, RBAC).                | AWS IAM, Azure RBAC, Kubernetes RBAC, Linux Capabilities                                       |
|                       |                                | Role-Based Access Control (RBAC)     | Assign roles (e.g., `dev`, `admin`) instead of individual permissions.                              | Open Policy Agent (OPA), AWS IAM Policies, Azure Managed Identities                                  |
| **Infrastructure**    | **Network Security**           | Zero Trust Network Access (ZTNA)     | Assume breach; validate every request (micro-segmentation, VPN alternatives).                     | Cloudflare Access, Zscaler Private Access, Cisco Umbrella                                        |
|                       |                                | Private Networks                     | Isolate workloads in VPCs, VLANs, or overlay networks (e.g., Kubernetes networks).                 | AWS VPC, Azure Virtual Networks, Calico, Cilium                                                   |
|                       | **Host Security**              | Immutable Infrastructure             | Treat servers/containers as ephemeral; rebuild from scratch on compromise.                       | Terraform, Docker/K8s `readOnlyRootFilesystem`, AWS EC2 Image Builder                          |
|                       |                                | Host Hardening                       | Apply OS-level protections (disable SSH root login, disable unused services, update patches).      | CIS Benchmarks, OSSEC, Ansible, OpenSCAP                                                                |
| **Data Protection**   | **Encryption**                 | Data at Rest                          | Encrypt sensitive data (databases, storage, backups) with strong keys (AES-256).                    | AWS KMS, Azure Key Vault, HashiCorp Vault, LUKS                                                        |
|                       |                                | Data in Transit                      | Enforce TLS 1.2+/1.3 for all network traffic.                                                     | Let’s Encrypt, Cloudflare SSL/TLS, mTLS (mutual TLS)                                                 |
|                       |                                | Tokenization/Field-Level Encryption  | Mask PII (PII) with tokens (e.g., credit card numbers) for logs/dashboards.                       | Google Cloud DLP, AWS Glue DataBrew, Microsoft Purview                                                 |
|                       | **Secrets Management**         | Secrets Rotation                      | Rotate secrets (API keys, DB passwords) automatically (no hardcoded values).                        | HashiCorp Vault, AWS Secrets Manager, Kubernetes Secrets                                          |
|                       |                                | Secrets Scanning                     | Scan repos (Git, CI/CD) for hardcoded secrets using SAST/SCA tools.                               | Snyk, Checkmarx, GitHub Secret Scanning                                                               |
| **Application Security** | **Code Security**            | Secure Coding Practices              | Follow OWASP Top 10 (e.g., input validation, SQLi/XXE prevention).                                | SonarQube, Checkmarx, OWASP ZAP                                                                         |
|                       |                                | Dependency Scanning                  | Scan libraries/vulnerabilities in dependencies (e.g., npm, Maven).                                | Dependabot, Snyk, GitHub Dependency Graph                                                           |
|                       | **Runtime Protection**         | Web Application Firewall (WAF)       | Filter malicious traffic (SQLi, XSS, DDoS) at the app layer.                                      | AWS WAF, Cloudflare WAF, ModSecurity                                                                 |
|                       |                                | Runtime Application Self-Protection (RASP) | Monitor app behavior for anomalies (e.g., unusual API calls).     | Imperva SecureSphere, Akamai Kona SiteDefender                                                      |
| **Monitoring & Response** | **Logging**               | Centralized Logging                  | Aggregate logs (ELK Stack, Datadog) with retention policies (comply with GDPR).                   | Splunk, ELK Stack (Elasticsearch, Logstash, Kibana), Datadog                                        |
|                       |                                | Structured Logging                   | Log events as JSON (standardized format) for easier parsing.                                       | OpenTelemetry, Corelogic                                                                               |
|                       | **Incident Response**          | Automated Alerts                     | Trigger alerts (Slack/PagerDuty) for failures, unauthorized access, or policy violations.         | Datadog, Prometheus + Alertmanager, AWS CloudWatch Events                                            |
|                       |                                | Playbooks                            | Define runbooks for common incidents (e.g., brute-force attack, data leak).                       | Jira Service Management, ServiceNow                                                                   |
| **Compliance**        | **Audit & Governance**         | Configuration Management             | Track changes to configs (GitOps, drifts) for audit trails.                                        | Ansible Tower, Chef, Puppet, GitLab CI/CD                                                             |
|                       |                                | Regular Audits                       | Conduct penetration tests (PT), vulnerability scans (SAST/DAST), and compliance checks.           | Burp Suite, OWASP ZAP, Nessus, Qualys                                                                 |

---

### **Implementation Guidelines**
#### **1. Start Small, Scale Gradually**
- **Phase 1 (Low Risk):** Enforce MFA for all user accounts and rotate credentials. Harden host OS (disable unnecessary services).
- **Phase 2 (Medium Risk):** Implement RBAC, network segmentation, and secrets rotation.
- **Phase 3 (High Risk):** Deploy runtime protections (WAF, RASP) and automated incident response.

#### **2. Toolchain Integration**
- **CI/CD Pipeline:**
  ```yaml
  # Example GitHub Actions workflow for dependency scanning
  - name: Scan dependencies
    uses: snyk/actions@master
    env:
      SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  ```
- **Infrastructure as Code (IaC):**
  ```hcl
  # Terraform example for AWS IAM role with least privilege
  resource "aws_iam_role" "example" {
    assume_role_policy = jsonencode({
      Version = "2012-10-17",
      Statement = [
        {
          Action = "sts:AssumeRole",
          Effect = "Allow",
          Principal = {
            Service = "ec2.amazonaws.com"
          }
        }
      ]
    })
    inline_policy {
      name = "restricted_s3"
      policy = jsonencode({
        Version = "2012-10-17",
        Statement = [{
          Effect   = "Allow",
          Action   = ["s3:GetObject"],
          Resource = "arn:aws:s3:::my-bucket/*"
        }]
      })
    }
  }
  ```

#### **3. Common Pitfalls**
- **Over-Permissioning:** Avoid "admin" roles; use granular least-privilege policies.
- **Ignoring Third-Party Libraries:** Dependencies like `log4j` or `Heartbleed` can introduce vulnerabilities. Scan regularly.
- **Decoupled Monitoring:** Centralize logs/alerts to avoid blind spots (e.g., siloed team tools).
- **Static Configurations:** Use dynamic policies (e.g., OPA) instead of static firewall rules.

---

### **Query Examples**
#### **1. Checking IAM Role Permissions**
```bash
# AWS CLI: List IAM policies attached to a role
aws iam list-attached-role-policies --role-name "DeploymentRole"
```
**Expected Output:**
```json
{
  "AttachedPolicies": [
    {
      "PolicyName": "AmazonS3ReadOnlyAccess",
      "PolicyArn": "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    }
  ]
}
```

#### **2. Scanning for Unencrypted Secrets in Git**
```bash
# GitHub secret scanning CLI
gh secrets scan --repo owner/repo --pattern "*.env"
```
**Expected Output:**
```text
Found 2 potential secrets in .env:
  - AWS_ACCESS_KEY_ID=AKIA...
  - DATABASE_URL=postgres://...
```

#### **3. Validating TLS Configuration**
```bash
# Test TLS endpoint
openssl s_client -connect example.com:443 -servername example.com | openssl x509 -noout -dates
```
**Expected Output:**
```text
notBefore=Jan 10 00:00:00 2023 GMT
notAfter=Apr  8 23:59:59 2023 GMT
```

#### **4. Querying Failed Login Attempts (SIEM)**
```spath
# Splunk query for brute-force attempts
index=logs source="/var/log/auth.log" *failed* | stats count by user
```
**Expected Output:**
```
user       | count
-----------+------
admin      | 15
backup     | 8
```

---

### **Related Patterns**
1. **[Zero Trust Architecture]**
   - Builds on Security Best Practices by enforcing continuous authentication and micro-segmentation.
   - *Tools:* Zscaler Private Access, Cloudflare Access.

2. **[Secure by Design]**
   - Integrates security into the development lifecycle (e.g., DevSecOps).
   - *Tools:* SonarQube, Checkmarx, Snyk.

3. **[Data Encryption at Rest]**
   - Focuses on encrypting databases and storage (complements broader security practices).
   - *Tools:* AWS KMS, Azure Key Vault, HashiCorp Vault.

4. **[Incident Response Playbooks]**
   - Defines automated responses to detected threats (e.g., blocking IPs, isolating hosts).
   - *Tools:* Jira Service Management, PagerDuty, Slack Integrations.

5. **[Compliance Automation]**
   - Uses tools to automate compliance checks (e.g., CIS benchmarks, PCI DSS).
   - *Tools:* OpenSCAP, Drata, Turbot.

---
### **Further Reading**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/cis-controls/)
- [AWS Well-Architected Security Pillar](https://aws.amazon.com/architecture/well-architected/)