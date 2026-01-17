**[Pattern] Security Guidelines Reference Guide**
*Version: 1.0*

---

### **Overview**
This guide provides structured **Security Guidelines** for enforcing best practices across applications, infrastructure, and workflows. It defines measurable patterns that map to **OWASP Top 10**, **NIST SP 800-53**, and **CIS Benchmarks**, ensuring compliance with security standards. These guidelines are modular, allowing teams to customize rules based on risk profiles, environments (dev/staging/prod), and regulatory demands (e.g., GDPR, HIPAA).

Key principles:
- **Least privilege**: Restrict access granularly (e.g., IAM policies, database permissions).
- **Defense in depth**: Layer security controls (e.g., encryption + WAF + SIEM monitoring).
- **Immutable infrastructure**: Enforce automation (e.g., IaC templates) over manual configurations.
- **Observability**: Mandate logging and alerting for anomalous behavior.

**Scope**: Applies to code, cloud resources, CI/CD pipelines, and third-party integrations.

---

### **Schema Reference**
| **Category**       | **Rule ID**       | **Description**                                                                 | **Example**                                                                 | **Severity** | **Tooling**                          | **Remediation**                     |
|--------------------|-------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|---------------|---------------------------------------|--------------------------------------|
| **Authentication** | `AUTH-001`        | Enforce MFA for all admin accounts.                                           | Google Authenticator, Duo Security.                                         | Critical      | Opsgenie, Okta                          | Deploy MFA via IAM roles/policies.   |
|                    | `AUTH-002`        | Rotate credentials every 90 days.                                             | Aws Secrets Manager, HashiCorp Vault.                                       | High          | AWS Secrets, Azure Key Vault        | Automate rotation via IaC.          |
| **Data Protection**| `DATA-001`        | Encrypt data at rest (AES-256) and in transit (TLS 1.2+).                     | Kubernetes Secrets, S3 Server-Side Encryption.                              | Critical      | OpenSSL, AWS KMS                       | Enforce via IaC (e.g., Terraform). |
|                    | `DATA-002`        | Anonymize PII in logs.                                                       | Obfuscate SSNs, emails (e.g., `user@example.com` → `****@example.com`).     | Medium        | Graylog, Splunk                       | Use log redaction tools.             |
| **Infrastructure** | `INFRA-001`      | Disable public APIs unless explicitly allowed.                               | Block port `443` for non-web services.                                      | High          | Cloudflare, AWS Security Groups      | Enforce via IAC policies.            |
|                    | `INFRA-002`      | Isolate workloads in separate VPCs/accounts.                                  | Multi-account strategy (e.g., prod/dev/staging).                           | High          | AWS Organizations, Azure Blueprints  | Use Terraform modules.               |
| **Code Security**  | `CODE-001`        | Scan dependencies for vulnerabilities (e.g., CVEs).                           | Dependabot, Snyk, Trivy.                                                  | High          | GitHub Actions, GitLab CI            | Remediate via dependency updates.    |
|                    | `CODE-002`        | Sanitize inputs to prevent injection attacks (SQL, XSS).                     | Use ORMs (e.g., SQLAlchemy), escape HTML.                                   | Critical      | OWASP ZAP, Bandit                       | Static code analysis (SonarQube).    |
| **CI/CD**          | `CI-001`          | Enforce sign-off (e.g., PR approvals) for prod deployments.                 | GitHub Branch Protection Rules.                                            | Medium        | GitHub, GitLab                        | Configure via repo settings.         |
|                    | `CI-002`          | Test security posture in staging (e.g., DAST scans).                         | OWASP ZAP, Burp Suite.                                                    | High          | CI/CD pipelines (Jenkins, GitHub Actions) | Add pre-deployment checks.           |
| **Monitoring**     | `MONITOR-001`     | Alert on failed login attempts (e.g., brute-force).                          | SIEM tools (e.g., Splunk, Datadog).                                       | High          | CloudWatch, Prometheus Alertmanager | Set up thresholds (e.g., 5 failures).|
|                    | `MONITOR-002`     | Monitor for unauthorized API calls.                                          | AWS CloudTrail, Azure Monitor.                                             | Critical      | SIEM, AWS GuardDuty                  | Block via WAF/IP restrictions.      |

---
**Note**: Severity mapped to **MITRE ATT&CK** tactics for prioritization.

---

### **Implementation Details**
#### **1. Rule Enforcement**
- **Automation**: Enforce via:
  - **Infrastructure**: Terraform, CloudFormation policies.
  - **Code**: Git hooks (e.g., `pre-commit` checks for secret leaks), SAST tools.
  - **Runtime**: Runtime security (e.g., Falco, Aqua Security).
- **Compliance**: Tie to frameworks like:
  | Framework       | Mapping Tool                          |
  |-----------------|---------------------------------------|
  | OWASP Top 10    | OWASP Dependency-Check                |
  | CIS Benchmarks  | CIS-CR (CIS Controls Remediation)     |
  | NIST SP 800-53  | NIST CSf (Cybersecurity Framework)    |

#### **2. Customization**
- **Risk Profiles**:
  - **Low Risk**: Enable `MONITOR-001` (alert threshold: 3 failures).
  - **High Risk**: Add `INFRA-002` + restrict SSH access via bastion hosts.
- **Regulatory Overrides**:
  - **GDPR**: Add `DATA-003` (right to erasure workflows).
  - **HIPAA**: Enforce `AUTH-003` (audit logs for PHI access).

#### **3. Validation**
- **Static Checks**: Use tools like:
  | Tool               | Purpose                          |
  |--------------------|----------------------------------|
  | Checkov            | IaC template validation.         |
  | Prisma Cloud       | Cloud resource compliance.       |
  | OpenSCAP           | Benchmark remediation (e.g., RHEL).|
- **Dynamic Checks**:
  - **Penetration Tests**: Quarterly (e.g., Burp Suite scans).
  - **Red Team Exercises**: Bi-annual (simulate phishing/privilege escalation).

---

### **Query Examples**
#### **1. Find Non-Compliant IAM Roles**
```sql
-- AWS CloudTrail query (Athena)
SELECT *
FROM iam_policy_violation_logs
WHERE policy_arn NOT IN (
    SELECT policy_arn
    FROM compliance_policies
    WHERE rule_id = 'AUTH-001'  -- MFA enforcement
);
```

#### **2. Detect Unencrypted Secrets in Git**
```bash
# Using `git-secrets`
git secrets --scan --all
# Output: Flag files containing plaintext DB passwords.
```

#### **3. Check for Vulnerable Dependencies in CI**
```yaml
# GitHub Actions workflow (Snyk)
- name: Run Snyk
  uses: snyk/actions@master
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  with:
    command: test --severity-threshold=high
```

#### **4. Query SIEM for Brute-Force Attempts**
```spath
# Splunk SPARQL (for AWS CloudTrail)
index=aws_cloudtrail source="*.json" action="Authenticate"
| search failure_message="Credentials not available or invalid"
| stats count by user_identity.arn
| where count > 3
```

---

### **Related Patterns**
1. **[Zero Trust Architecture]**
   - Complements `INFRA-002` (network segmentation) and `AUTH-001` (MFA).
   - *See*: [IETF RFC 8220](https://datatracker.ietf.org/doc/html/rfc8220).

2. **[Secrets Management]**
   - Extends `DATA-001` (encryption) with tools like **HashiCorp Vault** or **AWS Secrets Manager**.
   - *See*: [Vault Dynamic Secrets](https://www.vaultproject.io/docs/secrets).

3. **[Incident Response Playbook]**
   - Triggers from `MONITOR-001`/`MONITOR-002` alerts.
   - *See*: [NIST SP 800-61](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final).

4. **[Observability Stack]**
   - Enriches `MONITOR-*` rules with metrics/logs (e.g., **Prometheus + Loki**).
   - *See*: [OpenTelemetry](https://opentelemetry.io/).

5. **[Least Privilege Principle]**
   - Foundational for `AUTH-002` (credential rotation) and `INFRA-001` (API restrictions).
   - *See*: [CIS Principle of Least Privilege](https://www.cisecurity.org/principles/).

---
### **Troubleshooting**
| **Issue**                          | **Diagnostic Query**                          | **Solution**                                  |
|-------------------------------------|-----------------------------------------------|-----------------------------------------------|
| Failed MFA enforcement (`AUTH-001`) | `aws iam list-user-login-profile --user-name <admin>` | Re-enforce via `aws iam update-login-profile`. |
| Unencrypted S3 bucket (`DATA-001`)  | `aws s3api list-buckets --query "Buckets[?ServerSideEncryptionConfiguration==null]"` | Enable SSE-KMS via S3 console.               |
| Vulnerable npm package (`CODE-001`) | `npm audit -- severity=critical`               | Patch via `npm install <package>@^x.y.z`.     |

---
### **Resources**
- **Frameworks**:
  - [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
  - [CIS Benchmarks](https://www.cisecurity.org/benchmarks/)
- **Tools**:
  - [Checkov](https://www.checkov.io/) (IaC scanning)
  - [Trivy](https://aquasecurity.github.io/trivy/) (container scanning)
- **Training**:
  - [SANS SEC504](https://www.sans.org/course/sec504/) (Hacking Exposed)
  - [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework).

---
**Last Updated**: 2023-10-05
**Owners**: Security Team, DevOps
**Feedback**: Report issues via [GitHub Discussions](link).