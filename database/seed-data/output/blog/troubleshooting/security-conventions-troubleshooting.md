# **Debugging Security Conventions: A Troubleshooting Guide**
*For Backend Engineers*

---

## **1. Introduction**
Security Conventions ensure consistent, secure coding practices across an application, reducing vulnerabilities like injection attacks, improper authentication, and sensitive data leaks. This guide helps backend engineers diagnose and resolve common issues related to security misconfigurations, broken security controls, or inconsistent implementations.

---

## **2. Symptom Checklist**
Check for these **symptoms** indicating a security convention failure:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|--------------------------------------------|
| `SQL Injection` errors in logs       | Missing parameterized queries             |
| `CSRF tokens missing` in forms       | Improper session/CSRF handling             |
| `Hardcoded credentials` in config    | Secrets management misconfiguration         |
| `Permission denied` errors           | Incorrect IAM/role-based access control     |
| `Unencrypted data in logs/network`   | Missing TLS/encryption policies            |
| `Exposed API endpoints without auth` | Omitted or weak authentication              |
| `Deprecated algorithms` (e.g., MD5)   | Outdated crypto libraries                  |
| `Dependencies with known vulnerabilities` | Outdated `package.json`/`Gemfile` locks   |
| `Massive credential brute-force attempts` | Weak password policies or rate limits missing |

---

## **3. Common Issues & Fixes**

### **Issue 1: SQL Injection Vulnerabilities**
**Symptom:** Logs show raw SQL strings being concatenated (`"WHERE user = 'admin' OR '1'='1"'`).

**Root Cause:** Direct string interpolation instead of parameterized queries.

#### **Fix (Python - SQLAlchemy):**
```python
# ❌ Vulnerable (string concatenation)
query = f"SELECT * FROM users WHERE username = '{username}'"

# ✅ Secure (parameterized query)
query = "SELECT * FROM users WHERE username = :username"
result = db.execute(query, {"username": username})
```

#### **Fix (Java - JDBC):**
```java
// ❌ Vulnerable
String query = "SELECT * FROM users WHERE username = '" + userInput + "'";

// ✅ Secure
PreparedStatement stmt = conn.prepareStatement(
    "SELECT * FROM users WHERE username = ?");
stmt.setString(1, userInput);
ResultSet rs = stmt.executeQuery();
```

---

### **Issue 2: Missing CSRF Protection**
**Symptom:** Forms can be submitted without tokens, or tokens are hardcoded.

**Root Cause:** No CSRF middleware or improper token generation.

#### **Fix (Express.js - CSRF Middleware):**
```javascript
// Install: `npm install csurf`
const csurf = require('csurf');
const csrfProtection = csurf({ cookie: true });

// Middleware
app.use(csrfProtection);

// In templates, include the token:
<form method="POST">
  <input type="hidden" name="_csrf" value="<%= csrfToken %>">
  <!-- form fields -->
</form>
```

#### **Fix (Django - Default CSRF Middleware):**
```python
# Django already includes CSRF protection by default.
# If disabled, add `CsrfViewMiddleware` to `MIDDLEWARE`.
# Ensure forms include `{{ csrf_token }}`.
```

---

### **Issue 3: Hardcoded Secrets**
**Symptom:** Database credentials, API keys, or tokens appear in code or Git history.

**Root Cause:** Secrets committed to version control or hardcoded in config.

#### **Fix (Use Environment Variables + `.gitignore`):**
```python
# ❌ Vulnerable
DB_PASSWORD = "supersecret123"

# ✅ Secure (dotenv + .gitignore)
import os
from dotenv import load_dotenv

load_dotenv()  # Loads .env file
DB_PASSWORD = os.getenv("DB_PASSWORD")  # Set in `.env`, not code
```

**`.gitignore` Rule:**
```
.env
*.secret
```

---

### **Issue 4: Weak Authentication (OAuth/JWT Issues)**
**Symptom:** API tokens can be forged, or sessions persist after logout.

**Root Cause:** Missing `HttpOnly`, `Secure`, or `SameSite` flags on cookies.

#### **Fix (JWT Security Best Practices):**
```javascript
// ✅ Secure JWT (Node.js + JSON Web Tokens)
const jwt = require("jsonwebtoken");

const token = jwt.sign(
  { userId: user.id },
  process.env.JWT_SECRET,
  {
    expiresIn: "1h",  // Short expiry
    algorithm: "HS256", // Avoid deprecated algs
  }
);

// Set cookie with Secure/SameSite flags
res.cookie("token", token, {
  httpOnly: true,  // Prevent JS access
  secure: true,    // HTTPS only
  sameSite: "strict",
});
```

#### **Fix (OAuth2 - PKCE):**
Ensure OAuth flows use **PKCE** (Proof Key for Code Exchange) to prevent code interception attacks.

---

### **Issue 5: Outdated Dependencies**
**Symptom:** Vulnerabilities reported in `snyk`/`dependabot` scans.

**Root Cause:** Unpatched libraries in `package.json`/`requirements.txt`.

#### **Fix (Automated Updates):**
```bash
# npm
npm audit fix --force

# Python (pip)
pip install -U --upgrade-strategy=eager <package>

# Docker
docker pull <image>:latest
```

#### **Manual Check (Dependency-Tree):**
```bash
npm install dependency-tree  # Identifies high-risk deps
```

---

### **Issue 6: Missing TLS/HTTPS**
**Symptom:** Mixed content warnings (`http://` in `https://` pages).

**Root Cause:** No TLS enforcement or self-signed certificates.

#### **Fix (Force HTTPS):**
```python
# Flask (via middleware)
@app.after_request
def force_https(response):
    if request.host != "localhost":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        if request.scheme != "https":
            url = request.url.replace("http://", "https://", 1)
            return redirect(url)
    return response
```

#### **Certificate Setup (Let’s Encrypt):**
```bash
# Certbot (Nginx)
sudo certbot --nginx -d yourdomain.com
```

---

## **4. Debugging Tools & Techniques**

### **Static Analysis Tools**
| Tool          | Purpose                          | Example Command |
|---------------|----------------------------------|-----------------|
| **ESLint**    | Lint JavaScript for security risks | `npx eslint --rule "security:error"` |
| **Pylint**    | Python security checks           | `pylint --enable=security` |
| **Bandit**    | Python vuln scanner              | `bandit -r ./app` |
| **Snyk**      | Dependency scanning              | `snyk test` |
| **Trivy**     | Container/image scanning         | `trivy image --severity HIGH` |

### **Dynamic Analysis**
- **OWASP ZAP** – Automated web vuln scanning.
- **Burp Suite** – Manual security testing (intercept requests).
- **fail2ban** – Block brute-force attacks (e.g., SSH).

### **Logging & Monitoring**
- **Sentry/Errata** – Track security-related exceptions.
- **Prometheus/Grafana** – Monitor failed auth attempts.

---

## **5. Prevention Strategies**
### **Coding Best Practices**
1. **Least Privilege:** Limit permissions (IAM roles, DB users).
2. **Input Validation:** Reject malformed data early (e.g., `express-validator`).
3. **Secret Management:**
   - Use **AWS Secrets Manager**, **HashiCorp Vault**, or **AWS Parameter Store**.
   - Rotate keys regularly.
4. **Dependencies:**
   - Enable **auto-updates** (`dependabot`, `renovate`).
   - Pin versions (`^` should be avoided; use exact versions).

### **Infrastructure Security**
- **Network Policies:** Restrict pod-to-pod communication (Kubernetes `NetworkPolicy`).
- **WAF Rules:** Block SQLi/XSS patterns (AWS WAF, Cloudflare).
- **TLS Everywhere:** Enforce `HSTS` and disable HTTP.

### **CI/CD Security**
1. **Scan Dependencies in CI:**
   ```yaml
   # GitHub Actions
   - name: Snyk Security Scan
     run: npx snyk test --severity-threshold=high
   ```
2. **Image Scanning:**
   ```yaml
   - name: Trivy Scan
     run: trivy image --exit-code 1 --severity CRITICAL ${{ env.IMAGE }}
   ```

### **Regular Audits**
- **Penetration Testing:** Quarterly internal/third-party scans.
- **Code Reviews:** Enforce security checks in PRs (e.g., GitHub CodeQL).

---

## **6. Final Checklist Before Production**
| Task                          | Status (✅/❌) |
|-------------------------------|--------------|
| All dependencies up-to-date    |              |
| Secrets stored in environment |              |
| TLS enforced (HSTS)            |              |
| CSRF tokens enabled            |              |
| SQL queries parameterized      |              |
| Rate limiting on auth endpoints|              |
| Dependency vulnerabilities patched |       |
| Logging sensitive data disabled |         |

---

## **7. References**
- [OWASP Security Cheat Sheet](https://cheatsheetseries.owasp.org/)
- [AWS Security Best Practices](https://aws.amazon.com/security/well-architected/)
- [CIS Benchmarks](https://www.cisecurity.org/benchmark/)

By following this guide, you can **quickly identify, debug, and prevent** security misconfigurations. **Always validate fixes in staging** before production deployment.