# **Debugging Security Patterns: A Troubleshooting Guide**
*For Backend Engineers Troubleshooting Authentication, Authorization, Input Sanitization, and Cryptographic Failures*

---

## **1. Introduction**
Security patterns ensure that applications are robust against common vulnerabilities (e.g., SQL injection, XSS, CSRF, insecure authentication). This guide provides a **structured troubleshooting approach** for diagnosing and fixing security-related issues efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms using **logging, monitoring tools, and manual testing**:

### **Authentication & Session Issues**
✅ **Failed login attempts** (e.g., `401 Unauthorized` for valid users)
✅ **Session hijacking** (e.g., logged-in user’s session stolen by another device)
✅ **Brute-force attacks** (high login attempt rates from IP ranges)
✅ **Token expiration mismatches** (JWT/OAuth tokens expiring unexpectedly)

### **Authorization & Access Control Issues**
✅ **Unintended API access** (e.g., `GET /admin` without permission)
✅ **Role-based access violations** (e.g., "User" tries to perform "Admin" actions)
✅ **Missing `403 Forbidden` responses** (API returns `200 OK` for unauthorized requests)

### **Input & Output Sanitization Issues**
✅ **SQL injection** (e.g., `admin' --` bypassing login)
✅ **XSS payloads rendered in responses** (e.g., `<script>alert('hacked')</script>` executes)
✅ **Insecure file uploads** (e.g., `.php` files uploaded despite extension checks)
✅ **CSRF vulnerabilities** (e.g., unauthorized state changes via malicious links)

### **Cryptographic & Data Protection Issues**
✅ **Exposed secrets** (API keys, DB passwords in logs or Git history)
✅ **Weak encryption** (e.g., `MD5` used instead of `bcrypt`)
✅ **Hardcoded credentials** (e.g., `db_user="admin"` in config files)
✅ **Insecure data transmission** (HTTP instead of HTTPS for sensitive endpoints)

### **General Security Failures**
✅ **High latency in security checks** (e.g., slow JWT validation)
✅ **Missing security headers** (`CSP`, `HSTS`, `X-XSS-Protection`)
✅ **Deprecated libraries** (e.g., `openssl < 1.1.1` vulnerable to POODLE)

---

## **3. Common Issues & Fixes (With Code)**

### **3.1 Authentication Failures**
#### **Issue:** Login fails with `401 Unauthorized` even for valid credentials
**Possible Causes:**
- **Hashing mismatch** (e.g., bcrypt rounds too high, salt missing)
- **Session fixation** (attacker forces a session token)
- **Rate-limiting bypass** (too many failed attempts)

**Debugging Steps:**
1. **Verify credentials in DB:**
   ```sql
   SELECT * FROM users WHERE username = 'testuser';
   -- Check if password matches (use `bcrypt.compare()` in app)
   ```
2. **Check password hashing:**
   ```javascript
   // Bad: Using plaintext hash
   const badHash = bcrypt.hash("password", 4); // Too few rounds

   // Good: Secure bcrypt (12 rounds minimum)
   const goodHash = await bcrypt.hash("password", 12);
   ```
3. **Inspect session tokens:**
   ```python
   # Flask (SessionSecurity)
   app.secret_key = os.urandom(24)  # Ensure secret is strong & rotated
   ```

**Fix:**
```python
# Flask example: Secure password hashing + session fixes
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

def verify_login(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return True
    return False
```

---

#### **Issue:** Session hijacking (stolen cookies)
**Possible Causes:**
- **No `HttpOnly` flag** on cookies
- **No `Secure` flag** (cookies sent over HTTP)
- **Predictable session IDs**

**Fix:**
```javascript
// Node.js (Express) - Secure cookies
res.cookie('session', token, {
    httpOnly: true,
    secure: true,    // Only send over HTTPS
    sameSite: 'strict',
    maxAge: 24 * 60 * 60 * 1000  // 1 day expiry
});
```

---

### **3.2 Authorization Violations**
#### **Issue:** User bypasses role checks (`403` → `200`)
**Possible Causes:**
- **Missing middleware** (e.g., authorization not enforced in API routes)
- **Weak role checks** (e.g., `if (user.role === "admin")` instead of `user.hasRole("admin")`)

**Debugging Steps:**
1. **Check middleware:**
   ```javascript
   // Express middleware example (should inspect user role)
   const authorize = (roles) => (req, res, next) => {
       if (!req.user || !roles.includes(req.user.role)) {
           return res.status(403).send("Forbidden");
       }
       next();
   };
   ```
2. **Verify role enforcement:**
   ```python
   # Flask example: Role decorator
   from functools import wraps
   def role_required(role):
       def wrapper(fn):
           @wraps(fn)
           def decorated_view(*args, **kwargs):
               if current_user.role != role:
                   return abort(403)
               return fn(*args, **kwargs)
           return decorated_view
       return wrapper
   ```

**Fix:**
```python
@role_required("admin")
def delete_user():
    if not user.has_permission("delete_users"):
        return {"error": "Access Denied"}, 403
    # Proceed...
```

---

### **3.3 Input Sanitization Issues**
#### **Issue:** SQL Injection (`' OR 1=1 --`)
**Possible Causes:**
- **Raw SQL queries** (e.g., `psycopg2.cursor().execute(f"SELECT * FROM users WHERE username = '{username}'")`)
- **ORM bypass** (e.g., passing raw SQL in Django ORM)

**Fix:**
```python
# Python (SQLAlchemy - Safe)
user = session.query(User).filter_by(username=username).first()

# Bad: Raw SQL (VULNERABLE)
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

# Good: Parameterized queries (Node.js)
const safeQuery = "SELECT * FROM users WHERE username = $1";
const result = await pool.query(safeQuery, [username]);
```

---

#### **Issue:** XSS in HTML responses
**Possible Causes:**
- **Unescaped user input** in templates
- **Missing Content Security Policy (CSP)**

**Fix:**
```python
# Django (auto-escapes by default, but verify)
{{ user_input|safe }}  # ONLY if trusted (avoid)
```

**CSP Header (Nginx):**
```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://cdn.example.com";
```

---

### **3.4 Cryptographic Failures**
#### **Issue:** Stored passwords cracked in a few minutes
**Possible Causes:**
- **Using `MD5` or `SHA-1`** (fast to crack)
- **No salt** (rainbow table attacks)
- **Weak password policies** (e.g., allowing `password123`)

**Fix:**
```javascript
// Node.js (bcrypt - Secure)
const bcrypt = require('bcrypt');
const saltRounds = 12;

const hash = await bcrypt.hash(password, saltRounds);
const match = await bcrypt.compare(inputPassword, hash); // Returns boolean
```

**Password Policy Enforcement:**
```python
# Django - Password validator
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
]
```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                                                 | **Example Command**                          |
|--------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Burp Suite**           | Intercept & modify requests (test auth, CSRF)                                | `burp proxy on`                             |
| **OWASP ZAP**            | Automated security scanner for API/vulnerabilities                           | `zap-baseline.py --target https://api.example.com` |
| **SQLMap**               | Detect SQL injection vulnerabilities                                         | `sqlmap -u "http://example.com/login.php?id=1"` |
| **JWT Debugger** (Chrome Extension) | Inspect JWT claims/expiresAt                                                | Open DevTools → JWT tab                     |
| **Logging & Metrics**    | Track failed logins, slow responses                                          | `access.log | grep "401"`                               |
| **Security Headers Checker** (Mozilla Observatory) | Verify CSP, HSTS, XSS-Protection headers | [https://observatory.mozilla.org](https://observatory.mozilla.org) |
| **Depends** (GitHub Action) | Scan dependencies for vulnerabilities                                     | `.github/workflows/security.yml`            |
| **Fail2Ban**             | Block brute-force attackers                                                | `sudo service fail2ban start`               |
| **Postman (with Security Tests)** | Test API security (rate-limiting, auth)                                   | Postman "Tests" tab                         |

---

### **Debugging Workflow**
1. **Reproduce the issue** (e.g., try SQLi on login form).
2. **Check logs** (`/var/log/nginx/error.log`, app logs).
3. **Use Burp/ZAP** to inspect request/response.
4. **Test fixes incrementally** (e.g., disable rate-limiting to see if it’s the issue).
5. **Validate with tools** (e.g., `sqlmap`, CSP checker).

---

## **5. Prevention Strategies**
### **5.1 Coding Best Practices**
✅ **Authentication:**
- Use **JWT/OAuth2** with short expiry (15-30 min).
- Implement **refresh tokens** (long-lived but revocable).
- Rotate **secret keys** every 30 days.

✅ **Authorization:**
- Follow **least privilege principle** (e.g., "User" → can’t delete others).
- Use **attribute-based access control (ABAC)** for fine-grained permissions.

✅ **Input Sanitization:**
- **Never trust user input** (sanitize HTML, SQL, file uploads).
- Use **ORMs** (SQLAlchemy, Django ORM) to avoid raw SQL.
- **Validate file types** (e.g., `mime-types` module in Node.js).

✅ **Cryptography:**
- **Never log raw passwords** (hash only).
- Use **PBKDF2, bcrypt, or Argon2** (not SHA-256 alone).
- **Encrypt secrets** (AWS Secrets Manager, HashiCorp Vault).

### **5.2 Infrastructure & Tooling**
🔒 **Enable HTTPS** (Let’s Encrypt for free certificates).
🔒 **Set security headers** (CSP, HSTS, X-Frame-Options).
🔒 **Rate-limit APIs** (fail2ban, Cloudflare WAF).
🔒 **Audit logs** (track failed logins, admin actions).
🔒 **Regular dependency checks** (Dependabot, Snyk).

### **5.3 Testing & Monitoring**
🧪 **Unit Tests for Security:**
```python
# pytest example: Test password hashing
def test_password_hashing():
    hashed = hash_password("test123")
    assert bcrypt.checkpw("test123".encode(), hashed.encode())  # Should pass
```

🚨 **Monitor for:**
- **Failed login attempts** (alert if >5 from one IP).
- **Slow JWT validation** (could indicate DoS).
- **Missing security headers** (Nginx/Apache config alerts).

### **5.4 Red Team vs. Blue Team**
- **Red Team:** Simulate attacks (e.g., SQLi, CSRF).
- **Blue Team:** Patch vulnerabilities (e.g., fix XSS in 24h).
- **Penetration Testing:** Quarterly external audit.

---

## **6. Quick Reference Table**
| **Issue**               | **Symptom**                     | **Immediate Fix**                          | **Long-Term Fix**                     |
|-------------------------|---------------------------------|--------------------------------------------|---------------------------------------|
| SQL Injection           | `SyntaxError` or admin access   | Use ORM/parameterized queries              | Input validation + WAF                |
| XSS                     | `<script>` executes in output   | Escape HTML (Django’s `mark_safe`)         | CSP + Sanitize inputs                  |
| Brute Force Attacks     | `429 Too Many Requests`         | Enable rate-limiting                       | 2FA + CAPTCHA                          |
| Weak Passwords          | Hash cracked in <1 hour         | Upgrade to bcrypt/Argon2                   | Enforce 12+ char passwords              |
| Missing Security Headers| No `HSTS` or `CSP`              | Add headers in Nginx/Apache                | Automate with tools (e.g., OWASP ZAP)  |

---

## **7. Final Checklist Before Deployment**
✔ **All secrets are encrypted** (not in Git).
✔ **Passwords are hashed with bcrypt/Argon2**.
✔ **HTTPS is enforced** (`HSTS` header).
✔ **CSP is configured** to block inline scripts.
✔ **Rate-limiting is enabled** (e.g., 5 failed logins → IP ban).
✔ **Dependencies are up-to-date** (no deprecated libs).
✔ **Logging includes security events** (failed logins, admin actions).
✔ **Penetration test passed** (or recent audit).

---
**Troubleshooting security issues is a mix of automation (tools) and manual checks (logging, testing). Start with symptoms, fix the root cause, and prevent recurrence with proactive measures.**