# **Debugging Security Setup: A Troubleshooting Guide**

Security misconfigurations are a leading cause of vulnerabilities, data breaches, and system instability. This guide provides a structured approach to diagnosing and resolving common security setup issues in applications, APIs, and infrastructure.

---

## **1. Symptom Checklist**
Before diving into fixes, verify which symptoms match your issue:

✅ **Authentication Failures**
- `401 Unauthorized` errors despite correct credentials
- Session expiration issues (`403 Forbidden` or "Session expired")
- API keys being rejected or revoked unexpectedly

✅ **Authorization Failures**
- Users accessing restricted endpoints without permissions
- Role-based access control (RBAC) misapplied
- Unauthorized data exposure (e.g., sensitive fields in logs/errors)

✅ **Cryptographic Failures**
- Decryption errors (`InvalidToken`, `DecryptionFailed`)
- Key rotation issues (old keys still accepted)
- Weak encryption algorithm warnings

✅ **Network & Infrastructure Issues**
- Unauthorized access attempts (failed login brute-force attempts)
- Firewall/ACL misconfigurations blocking legitimate traffic
- Port scanning or probing attempts (indicating open vulnerabilities)

✅ **Compliance & Audit Failures**
- Missing security headers (`CSP`, `HSTS`)
- Sensitive data exposed in logs or error responses
- Policy violations (e.g., password complexity, MFA not enforced)

✅ **Injection & Exploitation Attempts**
- SQLi, XSS, or Command Injection logs
- Unexpected payloads in logs (e.g., `payload='; DROP TABLE users--`)

---

## **2. Common Issues & Fixes**

### **A. Authentication Failures**
#### **Issue: `401 Unauthorized` Despite Correct Credentials**
**Root Causes:**
- Incorrect token generation (e.g., JWT misconfigured).
- Session not properly validated (e.g., refresh token expired).
- Password hashing mismatch (e.g., bcrypt vs. SHA-1).

**Fixes:**
##### **1. Verify JWT Token Generation & Validation**
```javascript
// Example: Secure JWT Setup
const jwt = require('jsonwebtoken');

const SECRET_KEY = process.env.JWT_SECRET || 'fallback-key'; // ❌ Never hardcode

// ✅ Correct: Use HS256 with a strong secret
const token = jwt.sign({ userId: 123 }, SECRET_KEY, { expiresIn: '1h' });

// ✅ Validate token with correct algorithm
jwt.verify(token, SECRET_KEY, (err, decoded) => {
  if (err) return res.status(401).send("Invalid token");
});
```
**Common Mistakes:**
- Using `HS256` with a weak key (e.g., `'secret'`).
- Missing `exp` claim in token.
- Not validating `iat` (issued-at) to prevent replay attacks.

##### **2. Check Session Storage & Expiry**
```python
# Example: Flask-Session Fix
from flask_session import Session

app.config['SESSION_PERMANENT'] = False  # ❌ Avoid permanent sessions
app.config['SESSION_USE_SIGNER'] = True  # ✅ Secure against tampering
app.config['SESSION_COOKIE_HTTPONLY'] = True  # ✅ Prevent XSS
app.config['SESSION_COOKIE_SECURE'] = True  # ✅ Only send over HTTPS
```
**Debugging Steps:**
- Log session ID on each request to check expiry.
- Use browser dev tools to inspect cookies (`Application > Cookies`).

##### **3. Password Hashing Mismatch**
```javascript
// ✅ Always use bcrypt (or Argon2)
const bcrypt = require('bcrypt');
const saltRounds = 12;

const hashedPassword = await bcrypt.hash('userpass', saltRounds);

// During login:
const match = await bcrypt.compare('userpass', storedHash);
if (!match) throw new Error("Invalid credentials");
```
**Fix:**
- Audit all password fields for weak hashing (e.g., `SHA1`, `MD5`).
- Regenerate hashes if unsure.

---

### **B. Authorization Failures (RBAC Misconfigurations)**
#### **Issue: Users Accessing Unauthorized Endpoints**
**Root Causes:**
- Overly permissive role assignments.
- Missing middleware checks.
- Incorrect API gatekeeper logic.

**Fixes:**
##### **1. Enforce Role-Based Checks**
```go
// Example: Golang Middleware for RBAC
func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        claims, ok := r.Context().Value("user").(jwt.MapClaims)
        if !ok || claims["role"] != "admin" { // ❌ Restrictive check
            http.Error(w, "Forbidden", http.StatusForbidden)
            return
        }
        next.ServeHTTP(w, r)
    })
}
```
**Improvement:**
- Use fine-grained permissions (e.g., `can("update:user:123")`).
- Log denied access attempts for audit.

##### **2. Validate API Gatekeeper Policies**
```yaml
# Example: Kong API Gateway Policy
plugins:
  - name: rbac
    config:
      roles:
        - name: "admin"
          policy: "/api/admin/*"
        - name: "user"
          policy: "/api/user/*"
```
**Debugging Steps:**
- Test with a `curl` request:
  ```sh
  curl -v -H "Authorization: Bearer invalid" https://api.example.com/admin
  ```
- Check gateway logs for denied requests.

---

### **C. Cryptographic Failures**
#### **Issue: Decryption Fails (`InvalidToken`)**
**Root Causes:**
- Key rotation not handled.
- Wrong key used for signing/verification.
- Token expired but not caught early.

**Fixes:**
##### **1. Handle Key Rotation Gracefully**
```python
# Python: Support multiple signing keys
from cryptography.hazmat.primitives import serialization

def verify_token(token, public_keys):
    for key in public_keys:
        try:
            return jwt.decode(token, key, algorithms=["RS256"])
        except:
            continue
    raise ValueError("Invalid token")
```
**Debugging Steps:**
- List active signing keys:
  ```sh
  openssl rsa -in /path/to/key.pem -pubout -text
  ```
- Compare key usage in logs.

##### **2. Set Proper Expiry & Leeway**
```javascript
// ✅ Never rely on server time; use leeway
const token = jwt.sign({ userId: 123 }, SECRET_KEY, {
    expiresIn: '1h',
    issuer: 'your-app',
    audience: 'client'
});

jwt.verify(token, SECRET_KEY, { algorithms: ['HS256'], clockTolerance: 5 }); // ✅ 5s leeway
```
**Fix:**
- Audit tokens with `exp` < current time.
- Check for clock skew in logs.

---

### **D. Network & Infrastructure Issues**
#### **Issue: Unauthorized Access Attempts (Brute Force)**
**Root Causes:**
- Weak login limits.
- No rate-limiting in place.
- Credentials stored in plaintext.

**Fixes:**
##### **1. Implement Rate Limiting**
```python
# Flask-Limiter Example
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/login")
@limiter.limit("5 per minute")
def login():
    return "Login successful"
```
**Debugging Steps:**
- Check logs for failed attempts:
  ```sh
  grep "Unauthorized" /var/log/nginx/error.log
  ```
- Test with `ab` (Apache Benchmark):
  ```sh
  ab -n 100 -c 10 http://example.com/login
  ```

##### **2. Secure SSH & Database Access**
```bash
# ✅ Restrict SSH to key-based auth
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```
**Fixes:**
- Disable root login (`PermitRootLogin no`).
- Use fail2ban to auto-ban brute-force attempts.

---

### **E. Compliance & Audit Failures**
#### **Issue: Missing Security Headers**
**Root Causes:**
- Headers not configured in web server.
- Dynamic content bypassing CSP.

**Fixes:**
##### **1. Enforce Security Headers**
```nginx
# Nginx: Security Headers
add_header X-Content-Type-Options "nosniff";
add_header X-Frame-Options "DENY";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```
**Debugging Steps:**
- Verify headers with:
  ```sh
  curl -I https://example.com
  ```
- Use [SecurityHeaders.com](https://securityheaders.com/) for auditing.

##### **2. Audit Logs for Sensitive Data**
```bash
# Logrotate sensitive fields
logrotate -f /etc/logrotate.conf
```
**Fix:**
- Exclude `password`, `token`, `api_key` from logs.
- Use structured logging (e.g., JSON) and mask PII.

---

## **3. Debugging Tools & Techniques**
| Tool/Technique          | Purpose                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| **`curl` / `Postman`**  | Test API endpoints with custom headers/body.                          |
| **`ngrep` / Wireshark** | Capture and inspect network traffic for suspicious requests.           |
| **`fail2ban`**         | Automatically block brute-force attackers.                            |
| **`OWASP ZAP`**        | Scan for security vulnerabilities in web apps.                         |
| **`jq`**               | Parse logs for JSON fields (e.g., errors, timestamps).                |
| **`traceroute`**       | Check network path for anomalous delays or misconfigurations.          |
| **`auditd` (Linux)**   | Log syscalls for unauthorized file access.                             |
| **`OpenSSL`**          | Validate certificates and encryption keys.                              |

**Example Workflow:**
```sh
# Check for open ports
ss -tulnp | grep LISTEN

# Scan for SQLi vulnerabilities
curl -X POST http://example.com/login -d "user=admin' OR '1'='1&pass=anything"
```

---

## **4. Prevention Strategies**
### **A. Secure Development Lifecycle (SDLC) Practices**
1. **Default Deny Principle:**
   - Start with least privilege (e.g., `nobody` user for services).
   - Use `chmod 600` for credentials files.

2. **Automated Security Checks:**
   - Integrate **SAST/DAST** (e.g., SonarQube, Checkmarx) into CI/CD.
   - Example GitHub Action:
     ```yaml
     - name: Run OWASP ZAP Scan
       uses: zaproxy/action-full-scan@v0.7.0
       with:
         target: 'https://example.com'
     ```

3. **Infrastructure as Code (IaC):**
   - Use **Terraform**/`AWS CloudFormation` to enforce security policies.
   - Example:
     ```hcl
     resource "aws_security_group" "app" {
       name = "app-sg"
       ingress {
         from_port   = 80
         to_port     = 80
         protocol    = "tcp"
         cidr_blocks = ["10.0.0.0/8"] # ✅ Restrict to internal subnet
       }
     }
     ```

### **B. Runtime Protections**
1. **Web Application Firewall (WAF):**
   - Deploy **Cloudflare**, **AWS WAF**, or **ModSecurity**.
   - Block SQLi/XSS patterns:
     ```apache
     SecRule ARGS "@rx <script>" "id:1001,phase:2,deny,status:403"
     ```

2. **Secrets Management:**
   - Use **Vault** or **AWS Secrets Manager** (never hardcode passwords).
   - Rotate secrets automatically:
     ```bash
     vault rotate secret=db/credentials path=password
     ```

3. **Logging & Monitoring:**
   - Centralize logs with **ELK Stack** or **Datadog**.
   - Alert on:
     - Failed logins (`status=401`).
     - Unusual API calls (e.g., `POST /admin` from unknown IP).

### **C. Regular Audits**
1. **Penetration Testing:**
   - Schedule quarterly **bug bounty programs** or **external audits**.
2. **Dependency Scanning:**
   - Use **Dependabot**, **Snyk**, or `npm audit` to fix vulnerable libs:
     ```sh
     npm audit --fix
     ```
3. **Compliance Checks:**
   - Automate **PCI DSS**, **GDPR**, or **HIPAA** checks (e.g., **Prisma Cloud**).

---

## **5. Quick Reference Cheat Sheet**
| **Issue**               | **Quick Fix**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|
| `401 Unauthorized`      | Check JWT secret, session expiry, or password hashing.                       |
| RBAC Misconfiguration   | Audit role assignments; test with `curl -H "role:admin"`.                   |
| Brute Force Attacks     | Enable rate-limiting (`flask-limiter`, `Nginx rate-limit`).                 |
| Missing Security Headers| Add `Strict-Transport-Security`, `CSP` headers in Nginx/Apache.              |
| Key Rotation Failed     | Support multiple signing keys in JWT validation.                            |
| Logs Exposing Secrets   | Mask PII in logs; use `logrotate` to clean old logs.                         |

---

## **Final Checklist Before Deployment**
- [ ] All credentials (DB, API keys) are stored securely (Vault/Secrets Manager).
- [ ] JWT tokens expire and use `HS256`/`RS256` with strong keys.
- [ ] Rate-limiting is enabled for auth endpoints.
- [ ] Security headers (`CSP`, `HSTS`) are set in all responses.
- [ ] Logs exclude sensitive data (tokens, passwords).
- [ ] RBAC is enforced via middleware (not client-side).
- [ ] Network ACLs restrict access to only trusted subnets.
- [ ] Penetration testing was performed (or automated scans passed).

---
**Next Steps:**
1. **Reproduce the issue** in a staging environment.
2. **Apply fixes** incrementally and test.
3. **Monitor** for regressions post-deployment.

By following this guide, you should be able to quickly identify and resolve 80% of security setup issues. For persistent problems, consult your team’s security lead or external auditors.