# **[Pattern] Security Gotchas: Reference Guide**

---

## **Overview**
The **Security Gotchas** pattern helps developers identify and mitigate common security vulnerabilities that often go unnoticed due to oversight, misconfiguration, or poor coding practices. Unlike traditional security checks (e.g., input validation, encryption), gotchas are subtle flaws that bypass conventional protections, making them particularly dangerous. This guide categorizes known **security gotchas**, their root causes, detection methods, and remediation strategies to enforce secure coding practices.

This pattern is critical for:
- **APIs and microservices** (authentication/authorization flaws)
- **Databases** (injection, overprivileged queries)
- **Networked applications** (side-channel attacks, insecure defaults)
- **Legacy systems** (unpatched vulnerabilities)

By proactively addressing gotchas, teams reduce risk exposure, improve audit readiness, and align with standards like **OWASP Top 10**, **CWE/SANS Top 25**, and **NIST SP 800-53**.

---

## **Schema Reference**
Below is a structured breakdown of security gotchas by **category**, **impact**, and **mitigation**:

| **Category**               | **Gotcha Name**                          | **Description**                                                                                                                                                                                                 | **Impact Level** | **Root Cause**                                                                                                                                 | **Detection Methods**                                                                                                                                                                                                 | **Mitigation Strategies**                                                                                                                                                                                                 |
|----------------------------|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authentication**         | **IDOR (Insecure Direct Object Reference)** | Exposing internal object IDs (e.g., `/users/123`) without access checks, allowing privilege escalation.                                                                                                       | High             | Poor API design, missing row-level security (RLS).                                                                                                     | Manual review, static analysis (e.g., **SonarQube**, **Checkmarx**), dynamic testing (e.g., **OWASP ZAP**).                                                                                                     | Enforce access controls via middleware (e.g., **JWT scopes**, **Policy-as-Code**). Use **UUIDs** instead of auto-increment IDs.                                                                                          |
|                            | **Token Leakage**                        | Hardcoding, logging, or committing secrets (API keys, tokens) in code/config files.                                                                                                                                | Critical         | Lazy debugging, CI/CD misconfigurations.                                                                                                                   | **Git scanning tools** (e.g., **GitLeaks**, **Trivy**), **SAST** (e.g., **Snyk**).                                                                                                                                     | Use **env vars**, secrets managers (e.g., **AWS Secrets Manager**, **HashiCorp Vault**), and **`.gitignore`**. Rotate keys post-deployment.                                                                      |
| **Authorization**          | **Over-Permissive Policies**             | Granting excessive permissions (e.g., `*` in IAM roles) or relying on default group mappings.                                                                                                                 | High             | Legacy permission schemes, lack of least-privilege enforcement.                                                                                          | **Policy scanners** (e.g., **Open Policy Agent (OPA)**), **RBAC audits**.                                                                                                                                               | Apply **role-based access control (RBAC)**, **attribute-based access (ABAC)**, and **tiered permissions**. Review policies quarterly.                                                                                          |
|                            | **Missing CSRF Protection**               | Omitting CSRF tokens in state-changing API calls (e.g., `POST /delete`).                                                                                                                                      | Medium           | Frontend/backend misalignment, dynamic content.                                                                                                             | **OWASP ZAP**, **Burp Suite** (automated CSRF scans).                                                                                                                                                              | Implement **SameSite cookies**, **CSRF tokens**, or **stateless APIs** (e.g., REST).                                                                                                                                 |
| **Input Validation**       | **Regex Bypass**                        | Using overly permissive regex (e.g., `^[a-z]+$`) that accepts hidden characters (e.g., `\x00` in SQLi).                                                                                                      | High             | Underestimating input complexity.                                                                                                                                | **Fuzzing tools** (e.g., **Sqlmap**, **FFuF**), **static analysis**.                                                                                                                                          | Use **blacklists** for unsafe chars (`\0`, `;`, `'`), or frameworks like **Express-validator** (Node.js).                                                                                                          |
|                            | **Type Juggling**                        | Implicitly converting input types (e.g., `'1' === 1` in PHP/JS).                                                                                                                                             | Medium           | Dynamic languages, loose comparisons.                                                                                                                      | **SAST tools**, manual code review.                                                                                                                                                                         | Enforce **explicit type checks**, use **stricter equality operators** (`===`).                                                                                                                                           |
| **Injection**              | **NoSQL Injection**                      | Improperly sanitizing inputs in NoSQL queries (e.g., MongoDB `$where` clauses).                                                                                                                                 | Critical         | Mismatched query builders (e.g., `JSON.stringify()` bypass).                                                                                         | **SAST** (e.g., **Checkmarx**), **manual testing with malicious payloads** (`{"$ne": null}`).                                                                                                          | Use **ORMs** (e.g., **Mongoose**, **TypeORM**), parameterized queries. Escape inputs via **BSON libraries**.                                                                                                      |
|                            | **HTTP Header Injection**                | Injecting CRLF (`\r\n`) or malicious headers (e.g., `X-Forwarded-For: <attacker-IP>`) into responses.                                                                                                       | High             | Lack of input sanitization in headers.                                                                                                                      | **Intercept proxies** (e.g., **Burp Collaborator**), **fuzzing**.                                                                                                                                              | Whitelist allowed headers, validate lengths (`< 256 chars`). Use **`Strict-Transport-Security` (HSTS)**.                                                                                                            |
| **Error Handling**         | **Stack Traces in Production**           | Exposing raw stack traces with sensitive data (e.g., DB credentials, query details).                                                                                                                           | Medium           | Debugging on live systems.                                                                                                                                  | **Log analysis** (e.g., **ELK Stack**), **error monitoring** (e.g., **Sentry**).                                                                                                                                      | Log **errno** only, redact sensitive fields (e.g., **AWS CloudWatch Logs Insights**). Use **custom error pages**.                                                                                                   |
|                            | **Resource Exhaustion**                  | Allocating unbounded resources (e.g., `SELECT * FROM table WHOLE TABLE`) in error handlers.                                                                                                                  | Critical         | Poor query planning, unhandled exceptions.                                                                                                               | **Monitoring** (e.g., **Prometheus**, **Datadog**), **slow query logs**.                                                                                                                                           | Implement **query timeouts**, **row limits**, and **circuit breakers**.                                                                                                                                               |
| **Cryptography**           | **Weak PRNG**                            | Using predictable pseudo-random generators (e.g., `Math.random()` in JS) for tokens/secrets.                                                                                                               | High             | Misunderstanding cryptographic primitives.                                                                                                                   | **Cryptographic audits**, **entropy testing**.                                                                                                                                                               | Use **CSPRNGs** (e.g., `crypto.getRandomValues()`), **libraries** (e.g., **Bouncy Castle**).                                                                                                                           |
|                            | **Hardcoded Salts**                      | Embedding salts in code (e.g., `salt = "secret"` in password hashing).                                                                                                                                         | Medium           | Static configurations, reuse of salts.                                                                                                                       | **Code review**, **static analysis**.                                                                                                                                                                         | Generate salts **per user**, store in DB (never hardcode). Use **argon2id** with adaptive memory.                                                                                                                      |
| **Network Security**       | **Side-Channel Attacks**                 | Exposing timing/caching data (e.g., slow DB queries leaking secrets).                                                                                                                                         | High             | Asymmetric encryption, predictable algorithms.                                                                                                             | **Timing attack tools** (e.g., **TimingAttack.js**), **network sniffers**.                                                                                                                                         | Use **constant-time algorithms** (e.g., **libsodium**), **TCP_NODELAY**.                                                                                                                                              |
|                            | **Insecure Defaults**                    | Enabling admin interfaces, debug ports, or weak algorithms (e.g., SHA-1) by default.                                                                                                                         | Critical         | Config drift, vendor defaults.                                                                                                                                   | **Configuration scanners** (e.g., **Checkmarx**, **OpenSCAP**), **audit logs**.                                                                                                                                       | **Disable unused services**, enforce **secure defaults** (e.g., **CIS benchmarks**). Rotate defaults post-install.                                                                                                    |
| **Session Management**     | **Session Fixation**                     | Reusing session IDs across logins (e.g., `session_id = "old_id"`).                                                                                                                                         | Medium           | Manual session handling.                                                                                                                                     | **Session hijacking tools** (e.g., **BeEF**, **Setoolkit**).                                                                                                                                                     | Regenerate sessions on login, use **HTTP-only**, **Secure cookies**.                                                                                                                                                     |
|                            | **Long-Lived Sessions**                  | Allowing sessions to persist indefinitely (e.g., `Expires=1y` in cookies).                                                                                                                                     | High             | Legacy auth flows.                                                                                                                                           | **Session timeout monitoring**.                                                                                                                                                                           | Set **short TTLs** (e.g., 30 mins), use **refresh tokens**.                                                                                                                                                              |
| **Dependencies**           | **Unpatched Libraries**                 | Using outdated packages (e.g., `npm install lodash@4.17.15` with CVE-2021-41338).                                                                                                                             | Critical         | Neglected dependency management.                                                                                                                                  | **Dependency scanners** (e.g., **Dependabot**, **Snyk**), **vulnerability databases**.                                                                                                                            | Enforce **`npm audit`, `pip check`**, **automated updates**. Use **locked versions** (`package-lock.json`).                                                                                                            |
|                            | **Supply Chain Attacks**                 | Compromised dependencies (e.g., **npm event-stream** backdoor).                                                                                                                                             | Critical         | Trust in third-party repos.                                                                                                                                   | **SBOM tools** (e.g., **Syft**, **Anchore**), **reputation checks**.                                                                                                                                           | Use **trusted registries** (e.g., GitHub Packages), **code signing**. Audit dependencies **pre-deploy**.                                                                                                         |

---

## **Query Examples**
### **1. Detecting Over-Permissive IAM Roles (AWS CLI)**
```bash
aws iam list-roles --query 'Roles[?PolicyDocuments[?PolicyVersion.PolicyDocument.Statement[?Action.length>=3 && !contains(Action, `Get`) && !contains(Action, `List`)].StatementId == `*`].RoleName'
```
**Explanation**: Query for IAM roles granting `*` permissions to actions beyond `Get`/`List`.

### **2. Finding Hardcoded Secrets (Regex Search)**
```bash
# Linux/macOS
grep -r --include="*.{py,js,json}" "api_key:" /path/to/codebase
# Windows (PowerShell)
Select-String -Path "*.py" -Pattern "api_key" -Recurse
```
**Mitigation**: Replace with environment variables:
```python
import os
DB_PASSWORD = os.getenv("DB_PASSWORD")  # Avoid hardcoding
```

### **3. NoSQL Injection Test Payload**
```javascript
// Malicious input to test MongoDB injection
{
  "$ne": null,
  "$where": "this.email == 'admin' || 1 == 1"
}
```
**Expected Behavior**: Query should fail or return unexpected results.
**Fix**: Use parameterized queries:
```javascript
db.users.find({ email: "$email" }); // Safe
```

### **4. Regex Bypass Test (Python)**
```python
import re
pattern = re.compile(r"^[a-z]+$")  # Vulnerable
pattern.match("test\0")  # Returns match (hidden null byte)
```
**Fix**: Explicitly block null bytes:
```python
pattern = re.compile(r"^[a-z][\x00-\x7E]+$")  # Blocks \0
```

### **5. Detecting Unpatched Dependencies (Node.js)**
```bash
npm audit --audit-level=critical
```
**Output Example**:
```
high      EventEmitter2
  - event-emitter2@6.4.0
    Normalized name: "eventemitter2"
    Installed version: 6.4.0
    Dependency of: your-package@1.0.0
    Project dependency tree:
      your-package@1.0.0
        +-- eventemitter2@6.4.0
    Severity: high
      - event-emitter2 6.4.0 - Regular expression denial of service
        More info: https://npmjs.com/advisories/734
```
**Mitigation**: Update or pin version:
```bash
npm install event-emitter2@7.0.0
```

---

## **Related Patterns**
To complement **Security Gotchas**, reference these patterns for a layered defense:

| **Pattern**                     | **Purpose**                                                                                     | **Key Integration Points**                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **[Defense in Depth]**          | Layer security controls (e.g., auth + encryption + monitoring) to mitigate single-point failures. | Use **gotcha detection** (this pattern) to identify weak layers.                                               |
| **[Zero Trust]**                | Assume breach; enforce least-privilege access everywhere.                                          | Apply **RBAC policies** to remediate **Over-Permissive Gotchas**.                                              |
| **[Secret Management]**          | Securely store/rotate credentials without hardcoding.                                            | Fix **Token Leakage** and **Hardcoded Salts** via **Vault/Secrets Manager**.                                   |
| **[Input Sanitization]**         | Validate and escape all user inputs.                                                             | Address **Regex Bypass** and **NoSQL Injection** with strict parsers.                                        |
| **[Secure Defaults]**            | Configure systems aggressively secure by default.                                                 | Remediate **Insecure Defaults** (e.g., disable debug modes).                                                   |
| **[Observability]**              | Log/monitor security events to detect gotchas in production.                                     | Use **error logging** to catch **Stack Trace Leaks** or **Resource Exhaustion**.                              |
| **[Dependency Hardening]**      | Scan and update dependencies proactively.                                                       | Prevent **Unpatched Libraries** and **Supply Chain Attacks** via **SBOMs**.                                    |
| **[Rate Limiting]**              | Throttle requests to prevent brute-force attacks on gotchas (e.g., **IDOR**).                   | Combine with **auth checks** to block malicious payloads.                                                    |

---

## **Key Takeaways**
1. **Gotchas are code-level**: They often bypass traditional security controls (e.g., firewalls, WAFs). Focus on **code reviews** and **static analysis**.
2. **Automate detection**: Use **SAST/DAST tools** (Checkmarx, OWASP ZAP) to catch gotchas early.
3. **Assume breach**: Apply **least privilege**, **rate limiting**, and **logging** to contain damage.
4. **Regular audits**: Re-evaluate configurations (e.g., IAM, dependencies) quarterly.
5. **Educate teams**: Conduct **security training** on common gotchas (e.g., **Regex Bypass**, **Session Fixation**).

---
**References**:
- [OWASP Top 10](https://owasp.org/Top10/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST SP 800-53](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/nist.sp.800-53.r5.pdf)