# **Debugging Security Gotchas: A Troubleshooting Guide**
*For Senior Backend Engineers*

Security misconfigurations and bad practices (commonly called **"Security Gotchas"**) can lead to vulnerabilities such as data leakage, unauthorized access, or system compromise. This guide helps you quickly identify, debug, and fix common security pitfalls in backend systems.

---

## **1. Symptom Checklist**
Use this checklist to determine if your system may have a security issue:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|--------------------------------------------|
| Unauthorized API access attempts     | Missing or weak authentication (e.g., JWT, OAuth misconfigurations) |
| Sensitive data exposed in logs       | Improper logging (e.g., plaintext secrets in logs) |
| SQL injection or NoSQL injection     | Unsanitized user input in queries         |
| Denial-of-Service (DoS) attacks      | Weak rate limiting or missing input validation |
| Insecure file uploads                | Missing file type/permission checks        |
| Cross-Site Scripting (XSS)            | Unescaped user input in HTML responses    |
| Overprivileged accounts              | Hardcoded admin credentials in code         |
| Broken access control                | Role-based checks bypassed in business logic |
| Unencrypted sensitive data           | Missing TLS, insecure storage (e.g., plaintext DB fields) |
| Dependency vulnerabilities           | Outdated libraries with known CVEs        |
| Session fixation or hijacking        | Weak session management (e.g., predictable session IDs) |

If you observe any of these, proceed with debugging.

---

## **2. Common Issues & Fixes (With Code Examples)**

### **2.1 Missing or Weak Authentication**
**Symptom:** API endpoints accessible without proper credentials, or tokens expiring too soon.

**Common Fixes:**
- **JWT Misconfigurations**
  - **Issue:** JWT secret leaked or expired too quickly.
  - **Fix:**
    ```javascript
    // Node.js (Express + jsonwebtoken)
    const jwt = require('jsonwebtoken');

    // Use a strong secret (store in env vars, never hardcode!)
    const SECRET_KEY = process.env.JWT_SECRET || 'fallback-secret';
    const token = jwt.sign({ userId: 123 }, SECRET_KEY, { expiresIn: '1h' });
    ```

- **OAuth2 Token Leaks**
  - **Issue:** OAuth tokens exposed in client-side logs.
  - **Fix:** Use **PKCE (Proof Key for Code Exchange)** in OAuth flows:
    ```python
    # Flask-OAuthlib (Python)
    from flask_oauthlib.client import OAuth
    oauth = OAuth()
    oauth.register(
        name='github',
        client_id='your-client-id',
        client_secret='your-secret',
        request_token_params={'scope': 'read:user'},
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
    )
    ```

---

### **2.2 Sensitive Data in Logs**
**Symptom:** Credentials, API keys, or PII (Personally Identifiable Information) appear in server logs.

**Common Fixes:**
- **Mask Sensitive Fields in Logs**
  ```javascript
  // Node.js (winston logger)
  const { combine, timestamp, json } = require('winston');
  const logger = winston.createLogger({
      level: 'info',
      format: combine(
          timestamp(),
          json()
      ),
      transports: [new winston.transports.Console()],
      // Mask secrets dynamically
      meta: { mask: (meta) => {
          if (meta.secret) meta.secret = '***REDACTED***';
          return meta;
      }}
  });
  ```

- **Use Structured Logging with Sensitive Data Handling**
  ```python
  # Python (logging)
  import logging
  import re

  def redact_secrets(log_record):
      for secret in ['password', 'token', 'api_key']:
          log_record.msg = re.sub(secret + r'=[^ ]+', f'{secret}="REDACTED"', log_record.msg)
      return log_record

  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger()
  logger.addFilter(redact_secrets)
  ```

---

### **2.3 SQL Injection / NoSQL Injection**
**Symptom:** Application crashes or behaves unexpectedly with user input in queries.

**Common Fixes:**
- **Use Parameterized Queries (Never Concatenate Strings!)**
  ```python
  # Python (SQLAlchemy - Safe)
  from sqlalchemy import text
  query = text("SELECT * FROM users WHERE username = :username")
  result = db.execute(query, {"username": user_input})  # Safe

  # UNSAFE (Do NOT do this!)
  query = f"SELECT * FROM users WHERE username = '{user_input}'"
  ```

- **ORM-Based Solutions (Recommended)**
  ```javascript
  // Node.js (Sequelize)
  const User = await models.User.findOne({ where: { username: userInput } }); // Safe
  ```

---

### **2.4 Missing Rate Limiting (DoS Vulnerability)**
**Symptom:** System becomes unresponsive under heavy traffic.

**Common Fixes:**
- **Express Rate Limiting (Node.js)**
  ```javascript
  const rateLimit = require('express-rate-limit');
  const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100, // Limit each IP to 100 requests per window
  });
  app.use(limiter);
  ```

- **Nginx Rate Limiting (Reverse Proxy)**
  ```nginx
  limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;

  server {
      location /api {
          limit_req zone=one burst=20;
          proxy_pass http://backend;
      }
  }
  ```

---

### **2.5 Insecure File Uploads**
**Symptom:** Malicious files uploaded (e.g., `.php` files in a static assets folder).

**Common Fixes:**
- **Validate File Types Before Upload**
  ```javascript
  // Node.js (Express)
  const fileFilter = (req, file, cb) => {
      const allowedTypes = ['image/jpeg', 'image/png'];
      if (!allowedTypes.includes(file.mimetype)) {
          return cb(new Error('Invalid file type'), false);
      }
      cb(null, true);
  };
  upload.use(fileFilter);
  ```

- **Sanitize Filenames to Prevent Path Traversal**
  ```python
  # Python (Flask)
  import os
  from werkzeug.utils import secure_filename

  ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
  def allowed_file(filename):
      return '.' in filename and \
             filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

  if allowed_file(file.filename):
      filename = secure_filename(file.filename)  # Removes malicious chars
      file.save(os.path.join('uploads', filename))
  ```

---

### **2.6 Broken Access Control (BAC)**
**Symptom:** Users access resources they shouldn’t (e.g., `/admin` via URL manipulation).

**Common Fixes:**
- **Enforce Role-Based Checks in Routes**
  ```javascript
  // Node.js (Express Middleware)
  function checkAdmin(req, res, next) {
      if (!req.user || req.user.role !== 'admin') {
          return res.status(403).send('Forbidden');
      }
      next();
  }

  app.get('/admin', checkAdmin, adminController.getDashboard);
  ```

- **Resource-Based Authorization (RBAC)**
  ```python
  # Python (FastAPI)
  from fastapi import Depends, HTTPException
  from fastapi.security import OAuth2PasswordBearer

  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

  async def check_permission(user, resource_id):
      if user.role != 'admin' and not user.can_access(resource_id):
          raise HTTPException(status_code=403, detail="Unauthorized")

  @app.get("/dashboard/{resource_id}")
  async def read_dashboard(
      resource_id: str,
      token: str = Depends(oauth2_scheme)
  ):
      user = decode_token(token)
      await check_permission(user, resource_id)
      return {"data": get_resource(resource_id)}
  ```

---

### **2.7 Unencrypted Sensitive Data**
**Symptom:** Database dumps or API responses contain plaintext passwords.

**Common Fixes:**
- **Encrypt Data at Rest (Database)**
  ```sql
  -- PostgreSQL: Use pgcrypto
  CREATE EXTENSION pgcrypto;
  UPDATE users SET password = encrypt(password, 'secret_key');
  ```
  ```javascript
  // Node.js (CryptoJS for in-memory encryption)
  const encrypted = CryptoJS.AES.encrypt(user.password, process.env.CRYPTO_KEY);
  ```

- **Use HTTPS (TLS) for All Communications**
  ```nginx
  # Nginx TLS Configuration
  server {
      listen 443 ssl;
      server_name example.com;

      ssl_certificate /path/to/cert.pem;
      ssl_certificate_key /path/to/key.pem;

      location / {
          proxy_pass http://backend;
      }
  }
  ```

---

### **2.8 Dependency Vulnerabilities**
**Symptom:** Outdated libraries with known CVEs (e.g., `npm audit`, `snyk` warnings).

**Common Fixes:**
- **Run Dependency Scanning**
  ```bash
  # npm
  npm audit

  # Python (pip-audit)
  pip install pip-audit
  pip-audit
  ```

- **Update Dependencies Securely**
  ```bash
  # npm (update with dependabot)
  npx npm-check-updates -u
  npm install
  ```

- **Lock File Integrity Checks**
  ```json
  // package-lock.json / yarn.lock
  # Ensure versions are pinned, not wildcards
  ```
  ```bash
  # Verify checksums (GPG)
  gpg --verify package.tgz.asc
  ```

---

### **2.9 Session Fixation / Hijacking**
**Symptom:** Users logged in via one session can hijack another.

**Common Fixes:**
- **Use Secure, HttpOnly Cookies**
  ```javascript
  // Node.js (Express)
  res.cookie('session', token, {
      secure: true,       // Only send over HTTPS
      httpOnly: true,     // Not accessible via JavaScript
      sameSite: 'strict', // Prevent CSRF
      maxAge: 24 * 60 * 60 * 1000 // 1 day
  });
  ```

- **Regenerate Session ID on Login**
  ```python
  # Flask (Secure Sessions)
  from itsdangerous import URLSafeTimedSerializer

  def generate_session():
      s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
      return s.dumps({'user_id': current_user.id}, salt='session')

  @app.route('/login', methods=['POST'])
  def login():
      session.permanent = True
      session['session_token'] = generate_session()  # Regenerate on login
      return redirect(url_for('dashboard'))
  ```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**               | **Purpose**                          | **Example Usage**                          |
|-----------------------------------|---------------------------------------|--------------------------------------------|
| **OWASP ZAP**                     | Web app security scanning             | `zap-baseline.py -t http://localhost:3000` |
| **Burp Suite**                    | Intercept & manipulate HTTP requests  | Proxy traffic through Burp                 |
| **SQLMap**                        | Detect SQLi vulnerabilities           | `sqlmap -u "http://example.com/login.php?id=1" --dbs` |
| **Nessus/OpenVAS**                | Network vulnerability scanning       | Scan entire subnet for misconfigurations   |
| **Trivy / Snyk CLI**              | Dependency vulnerability scanning     | `trivy fs .` (scans local filesystem)      |
| **Wireshark**                     | Packet inspection (TLS, HTTP)        | Capture HTTPS traffic (with CA certs)      |
| **Fail2Ban**                      | Automate IP blocking for brute force | Block IPs after failed login attempts     |
| **AWS Security Hub / CloudTrail** | Cloud security monitoring            | Audit AWS IAM, S3, Lambda permissions      |

---

## **4. Prevention Strategies**

### **4.1 Code-Level Security**
✅ **Use Security Libraries**
- **Authentication:** `passlib` (Python), `bcrypt` (JS)
- **Input Validation:** `validator.js`, `zod` (TypeScript)
- **Dependency Management:** `npm audit`, `snyk test`

✅ **Follow Secure Coding Practices**
- **Never log secrets** (passwords, API keys).
- **Use parameterized queries** (never string interpolation in SQL).
- **Sanitize all user input** (HTML, JS, SQL).

✅ **Implement Least Privilege**
- Avoid `root`/`admin` accounts in production.
- Use **IAM policies** (AWS) or **RBAC** (OAuth2).

---

### **4.2 Infrastructure & Deployment**
✅ **Hardening Servers**
- **Disable unused ports** (SSH, RDP).
- **Use `fail2ban`** to block brute-force attacks.
- **Rotate keys & secrets** (use tools like `vault.sh` or AWS Secrets Manager).

✅ **Container Security**
- **Scan Docker images** (`docker scan`).
- **Run as non-root** (`USER 1000` in Dockerfile).
- **Use `distroless` or `Alpine` images**.

✅ **Network Security**
- **Force HTTPS** (redirect HTTP → HTTPS).
- **Use WAFs** (Cloudflare, AWS WAF).
- **Rate limit API endpoints**.

---

### **4.3 Monitoring & Incident Response**
✅ **Logging & Alerts**
- **Centralized logs** (ELK Stack, Datadog).
- **Monitor for anomalies** (sudden traffic spikes, failed logins).

✅ **Regular Audits**
- **Penetration testing** (quarterly).
- **Dependency updates** (automate with GitHub Actions).

✅ **Incident Response Plan**
- **Isolate compromised systems** (failover to read-only DBs).
- **Notify stakeholders** (team, customers).
- **Post-mortem analysis** (find root cause, prevent recurrence).

---

## **5. Quick Checklist for Security Gotchas**
Before deploying, run:
1. **Dependency scan** (`npm audit`, `snyk test`).
2. **SQL/NoSQL injection test** (fuzz input fields).
3. **Rate limit testing** (send 100+ requests/sec).
4. **File upload validation** (try `.php` files).
5. **Authentication bypass test** (manually change JWT tokens).
6. **Log inspection** (ensure no secrets leak).
7. **Network scan** (`nmap`, `nessus`).

---
### **Final Note**
Security is an **iterative process**. Even after fixing issues, **re-test** and **monitor** for regressions. Use **automated security tools** (SAST/DAST) in CI/CD pipelines.

**Happy debugging!** 🔒🚀