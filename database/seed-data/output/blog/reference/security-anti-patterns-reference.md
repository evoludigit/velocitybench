# **[Pattern] Security Anti-Patterns Reference Guide**

---
## **Overview**
Security anti-patterns are common, often counterintuitive practices that introduce vulnerabilities, weaken defenses, or undermine best security practices in software development, architecture, or operational environments. Unlike design patterns (which promote proven solutions), anti-patterns highlight **misconceptions, shortcuts, or poor decisions** that lead to security breaches, compliance gaps, or degraded protection. This guide categorizes security anti-patterns by domain (e.g., authentication, encryption, network security) and provides actionable insights to recognize, mitigate, and replace them with secure alternatives.

---
## **1. Key Concepts**
Security anti-patterns arise from:
- **Laziness**: Cutting corners (e.g., hardcoded secrets, weak default passwords).
- **Misunderstanding**: Relying on myths (e.g., "SSL terminates at the load balancer, so client-side encryption isn’t needed").
- **Pressure**: Sacrificing security for speed (e.g., bypassing input validation for "better user experience").
- **Overconfidence**: Assuming "it can’t happen here" (e.g., ignoring patch management for legacy systems).

**Anti-patterns vs. Patterns**:
| **Aspect**          | **Anti-Pattern**                          | **Secure Pattern**                     |
|----------------------|-------------------------------------------|----------------------------------------|
| **Authentication**   | "Password123" everywhere (weak passwords)| Multi-factor authentication (MFA)       |
| **Encryption**       | Storing plaintext passwords in DB         | Hashing with salting (bcrypt, Argon2)    |
| **Networking**       | Exposed RDP/service ports to the internet | Zero Trust + VPN/SSH tunneling         |
| **Code**             | Inline secrets in source code             | Secrets management (HashiCorp Vault)    |
| **Monitoring**       | No logging for critical operations        | SIEM + real-time anomaly detection     |

---
## **2. Schema Reference**
Below is a taxonomy of security anti-patterns, organized by category. Replace placeholders (`{domain}`) with specific context (e.g., "API," "Database").

| **Category**               | **Anti-Pattern Name**               | **Description**                                                                                     | **Impact**                                                                 | **Mitigation**                                                                 |
|----------------------------|--------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Authentication**         | **Password Spraying**               | Brute-forcing common passwords (e.g., `Admin:admin123`) across accounts.                           | Account takeovers, credential stuffing.                                      | Enforce MFA, rate-limiting, and strong password policies (8+ chars, no reuse). |
|                            | **Session Fixation**                 | Allowing users to reuse session IDs without regeneration.                                           | Session hijacking if IDs are leaked.                                          | regenerate session IDs after login (e.g., `uuid4()`).                         |
| **Encryption**             | **Plaintext Secrets in Code**        | Hardcoding API keys, DB passwords, or tokens in source control (Git, etc.).                          | Exposure via version control leaks.                                           | Use secrets managers (AWS Secrets Manager, Azure Key Vault).                      |
|                            | **Weak Encryption (e.g., DES)**      | Using outdated or broken algorithms (e.g., DES, RC4).                                               | Cryptographic attacks (e.g., brute force).                                    | Use AES-256-GCM or ChaCha20-Poly1305 (modern standards).                       |
| **Network Security**       | **Over-Permissive ACLs**             | Granting `*` access to resources (e.g., `SELECT * FROM users`).                                      | Data breaches, privilege escalation.                                          | Follow the principle of least privilege (scope permissions tightly).            |
|                            | **Unpatched Vulnerabilities**        | Ignoring CVEs (e.g., unpatched Log4j in production).                                                  | Exploits via known vulnerabilities.                                            | Automate patching (e.g., Chocolatey, Ansible) + vulnerability scanning.       |
| **Code Security**          | **SQL Injection via String Concatenation** | Building SQL queries with raw user input (e.g., `query = "SELECT * FROM users WHERE id = " + user_id`). | Database corruption, data leakage.                                             | Use parameterized queries (ORMs like Hibernate, or prepared statements).      |
|                            | **Hardcoded Credentials**             | Baking secrets into binaries (e.g., `if (password == "admin") { ... }`).                          | Credential theft via reverse-engineering.                                       | Use runtime secrets injection (e.g., Docker secrets, Kubernetes Secrets).     |
| **Monitoring/Logging**     | **No Logging for Critical Operations** | Omitting logs for logins, payments, or admin actions.                                                | Undetected breaches or fraud.                                                  | Log everything (sensitive data redactions allowed) + retain logs for audits.  |
|                            | **Alert Fatigue**                    | Overloading teams with noise (e.g., 10K false positives/day).                                       | Ignored real alerts, delayed response.                                         | Fine-tune alerts (e.g., correlation rules, anomaly detection).                |
| **Development Practices**  | **Security as an Afterthought**      | Adding security "later" (e.g., penetration testing at the end).                                       | Late-stage fixes are costly.                                                  | Shift-left security: integrate SAST/DAST in CI/CD.                           |
|                            | **Copy-Paste Security**               | Reusing the same security controls across systems without context.                                  | Inconsistent protection, missed edge cases.                                    | Customize controls per system (e.g., different policies for CI vs. prod).     |

---
## **3. Query Examples**
### **Detecting Anti-Patterns via Logs/Code Analysis**
Use these queries in **SIEM tools (e.g., Splunk, ELK)** or **static analysis tools (e.g., SonarQube)** to identify anti-patterns.

#### **3.1 SQL Injection via Concatenation (Code)**
**Tool**: SonarQube/Snyk CLI
**Query**:
```sql
-- Detect hardcoded SQL queries (anti-pattern: dynamic SQL without parameterization)
SELECT file_path, lines
FROM code_scan_results
WHERE regex_matches(lines, 'CREATE TABLE \\w+.*SELECT \\*.*\\s+\\w+ \\+')
AND file_path LIKE '%backend%.sql';
```
**Mitigation**:
Replace with:
```python
# Secure (parameterized query)
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

#### **3.2 Unpatched Vulnerabilities (Network)**
**Tool**: Nessus/OpenVAS
**Query**:
```
-- Find systems with unpatched Log4j (CVE-2021-44228)
select host_name, port, severity
from vuln_scans
where cve_id = 'CVE-2021-44228'
and status = 'unpatched';
```
**Mitigation**:
Apply patch or upgrade to Log4j 2.17.1+.

#### **3.3 Weak Passwords (Authentication)**
**Tool**: Splunk
**Search Query**:
```
index=authentication sourcetype=log
| regex "_password.*(?i)(123|admin|password|letmein)"
| stats count by user_id
| sort -count
```
**Mitigation**:
Enforce password policies + MFA.

---
## **4. Related Patterns**
Replace anti-patterns with these **secure alternatives**:

| **Anti-Pattern**               | **Secure Pattern**                          | **Tools/Libraries**                          | **Key Principles**                          |
|---------------------------------|---------------------------------------------|-----------------------------------------------|---------------------------------------------|
| Hardcoded secrets               | Secrets Management                          | HashiCorp Vault, AWS Secrets Manager          | Encryption at rest + rotation policies       |
| Weak authentication             | Multi-Factor Authentication (MFA)           | TOTP (Google Authenticator), FIDO2           | Defense in depth for credential protection |
| No input validation             | Whitelisting + Output Encoding              | OWASP ESAPI, Sanitize libraries              | Prevent XSS/SQLi via strict validation     |
| Centralized logging              | Distributed Tracing + SIEM                  | Jaeger, ELK Stack, Splunk                    | Correlate events across services            |
| No encryption at rest           | Encrypted Databases/Volumes                 | AWS KMS, TLS 1.3, VeraCrypt                  | Protect data even if infrastructure is breached |
| Overly permissive ACLs          | Principle of Least Privilege (PoLP)         | Kubernetes RBAC, IAM Policies                 | Limit access to only what’s needed          |
| Bypassing security tests        | Shift-Left Security                         | SAST (SonarQube), DAST (OWASP ZAP)           | Integrate security into development workflow |

---
## **5. Implementation Checklist**
**Before Refactoring**:
- [ ] Audit logs for anti-pattern usage (e.g., concat-based queries).
- [ ] Run static/dynamic analysis tools (e.g., `bandit` for Python, `checkmarx`).
- [ ] Review incident reports for patterns (e.g., "over 80% of breaches used weak passwords").

**During Refactoring**:
- [ ] Replace hardcoded values with environment variables/secrets managers.
- [ ] Enforce parameterized queries in all database interactions.
- [ ] Implement MFA for all admin/user accounts.
- [ ] Patch all CVEs within 72 hours of disclosure.

**Post-Refactor**:
- [ ] Validate fixes with penetration testing (e.g., Burp Suite).
- [ ] Monitor for re-emergence of anti-patterns (e.g., alert on new hardcoded secrets).
- [ ] Document changes in a security runbook for future reference.

---
## **6. Resources**
- **Books**:
  - *Building Secure Software* (Michael Howard)
  - *The Web Application Hacker’s Handbook* (Dafydd Stuttard)
- **Tools**:
  - [OWASP Anti-Patterns Cheat Sheet](https://cheatsheetseries.owasp.org/)
  - [CIS Benchmarks](https://www.cisecurity.org/) (for hardened configurations)
- **Standards**:
  - NIST SP 800-53 (Security and Privacy Controls)
  - PCI DSS (Payment Card Industry standards)

---
**Note**: Security anti-patterns evolve with threat landscapes. Regularly update this guide based on new vulnerabilities (e.g., CVE databases) or emerging trends (e.g., AI-driven attacks).