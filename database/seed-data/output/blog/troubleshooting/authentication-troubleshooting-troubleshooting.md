# **Debugging Authentication Troubleshooting: A Troubleshooting Guide**

Authentication failures can severely disrupt user access, degrade system security, and degrade user experience. This guide provides a structured approach to diagnosing, resolving, and preventing common authentication issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm which symptoms are present:

| **Symptom** | **Description** |
|-------------|----------------|
| Username/Password Rejection | Valid credentials fail to authenticate, returning "Invalid credentials." |
| Session Timeout Early | Users log out unexpectedly before their session should expire. |
|Redirect Loops or Errors | Authentication attempts lead to infinite redirects or 500/401 errors. |
|Token/Session Mismatch | JWT/OAuth tokens are rejected or expired unexpectedly. |
|3rd-Party Login Failures | OAuth/providers (Google, GitHub) fail during login. |
|Rate Limiting/Throttling | Too many failed attempts lock users out temporarily. |
|Logging Issues | No debug logs or insufficient error details in logs. |
|Configuration Drift | Recent code/config changes broke authentication. |
|Multi-Factor Auth (MFA) Issues | Users stuck in MFA flows or unable to complete them. |

If multiple symptoms appear, prioritize:
1. **System Stability (401/403 errors, redirects)**
2. **User Experience (session expiry, MFA failures)**
3. **Security (rate limits, credential lockouts)**

---

## **2. Common Issues & Fixes (Code Examples Included)**

### **A. Invalid Credentials**
**Symptom:** Users enter correct credentials but get "Invalid credentials" repeatedly.
**Root Causes:**
- Password hashing mismatch (e.g., bcrypt vs. plaintext).
- Case-sensitive username matching.
- Database corruption or stale entries.

#### **Fix:**
**1. Verify Password Hashing**
Ensure frontend sends **hashed passwords** (if using hashed login), and backend verifies with the same algorithm.
```javascript
// Backend (Node.js + bcrypt)
const bcrypt = require('bcrypt');
const checkPassword = async (storedHash, inputPassword) => {
    return await bcrypt.compare(inputPassword, storedHash);
};

// Frontend (if sending hashed passwords)
const hashedPassword = await bcrypt.hash(password, 10);
```

**2. Check Database for Typos**
```sql
-- Debug SQL query to find discrepancies
SELECT * FROM users WHERE username = 'john_doe'; -- Verify stored hash
SELECT * FROM users WHERE LOWER(username) = LOWER('JohnDoe'); -- Case-sensitive check
```

**3. Reset Password for Suspicious Users**
```javascript
// If corruption is suspected
await db.query('UPDATE users SET password_hash = NULL WHERE id = ?', [userId]);
```

---

### **B. Session Expires Too Soon**
**Symptom:** Users logged in for 5 minutes get logged out.
**Root Causes:**
- Incorrect `COOKIE_SECURE`/`HTTPONLY` settings.
- Missing `res.cookie()` expiration time.
- Overly aggressive session invalidation.

#### **Fix:**
**1. Set Secure & HTTP-Only Cookies**
```javascript
// Node.js (Express)
res.cookie('sessionId', token, {
    secure: process.env.NODE_ENV === 'production', // HTTPS only in prod
    httpOnly: true, // Prevent XSS via JS
    maxAge: 24 * 60 * 60 * 1000, // 1 day in ms
});
```

**2. Verify Session Expiry Logic**
```javascript
// Example: Extended session expiry for admins
const sessionDuration = user.isAdmin ? 30 * 24 * 60 * 60 * 1000 : 8 * 60 * 60 * 1000;
```

---

### **C. JWT/OAuth Token Issues**
**Symptom:** Tokens are rejected with `invalid_token` or expired prematurely.
**Root Causes:**
- Mismatched signing secret.
- Improper token storage (e.g., localStorage vs. secure cookies).
- Expired tokens due to incorrect `exp` claim.

#### **Fix:**
**1. Compare Signing Key**
```javascript
// Backend (JWT generation)
const jwt = require('jsonwebtoken');
const secret = process.env.JWT_SECRET; // Should match frontend's verification
const token = jwt.sign({ userId: 123 }, secret, { expiresIn: '1h' });
```

**2. Validate Token in Frontend**
```javascript
// Frontend (React)
import jwtDecode from 'jwt-decode';

const isTokenValid = () => {
    const token = localStorage.getItem('token');
    if (!token) return false;
    const decoded = jwtDecode(token);
    return decoded.exp * 1000 > Date.now();
};
```

**3. Ensure Clock Synchronization**
If tokens expire early, ensure server/client clocks align (NTP sync).

---

### **D. Rate Limiting & Lockouts**
**Symptom:** Users get `429 Too Many Requests` or locked out after 5 attempts.
**Root Causes:**
- Missing rate-limiting middleware.
- Overly aggressive lockout policies.

#### **Fix:**
**1. Configure Rate Limiting (Express)**
```javascript
const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 mins
    max: 10, // Limit each IP to 10 requests
    handler: (req, res) => res.status(429).send('Too many attempts.'),
});

app.use('/login', limiter);
```

**2. Implement Temporary Lockout**
```javascript
// Pseudocode for lockout logic
if (failedAttempts >= 5 && !isLocked) {
    await db.query('UPDATE users SET is_locked = true WHERE id = ?', [userId]);
    setTimeout(() => {
        db.query('UPDATE users SET is_locked = false WHERE id = ?', [userId]);
    }, 15 * 60 * 1000);
}
```

---

### **E. OAuth Provider Failures**
**Symptom:** Google/GitHub login redirects to "Login failed" page.
**Root Causes:**
- Incorrect callback URL.
- Missing OAuth scopes.
- Token revocation by provider.

#### **Fix:**
**1. Verify Callback URL**
```javascript
// Pass correct redirect_uri to OAuth client
const googleOAuth = new GoogleAuth({
    clientId: 'YOUR_CLIENT_ID',
    clientSecret: 'YOUR_SECRET',
    redirectUri: 'https://yourdomain.com/auth/google/callback', // Must match provider config
});
```

**2. Check Token Response**
```javascript
// Debug token exchange
const { tokens } = await googleOAuth.generateAuthURL({
    access_type: 'offline', // For refresh tokens
    scope: 'openid email profile', // Required scopes
});
```

**3. Handle Token Expiry Gracefully**
```javascript
// Refresh token if expired
const { tokens } = await googleOAuth.refreshToken(refreshToken);
```

---

## **3. Debugging Tools & Techniques**

### **A. Logging**
- **Backend:** Use structured logging (Winslog, Winston).
  ```javascript
  logger.error({ userId: 123, error: 'Invalid credentials' }, 'Login failed');
  ```
- **Frontend:** Track auth errors in a client-side error tracker (Sentry, LogRocket).

### **B. Network Inspection**
- **Chrome DevTools:** Check `Network` tab for failed API calls (JWT/OAuth responses).
- **Postman:** Replay failed auth requests with `Authorization` headers.

### **C. Session Debugging**
- **Redis DB:** Inspect session store (if using Redis):
  ```bash
  redis-cli GET session:abc123
  ```
- **Cookie Inspection:** Verify `Secure`, `HttpOnly`, and `SameSite` flags.

### **D. Mock Testing**
- Use **Postman** or **curl** to simulate auth flows:
  ```bash
  curl -X POST http://localhost:3000/login \
       -H "Content-Type: application/json" \
       -d '{"username": "test", "password": "test"}'
  ```

---

## **4. Prevention Strategies**

### **A. Secure Defaults**
- **Always** use HTTPS.
- **Never** log plaintext passwords.
- **Rotate secrets** regularly (use AWS Secrets Manager).

### **B. Input Validation**
- Frontend: Sanitize inputs (e.g., `username` length, `password` complexity).
- Backend: Validate **all** auth fields (e.g., `email` format).

### **C. Regular Audits**
- **Database:** Scan for stale user records.
- **Dependencies:** Update auth libraries (e.g., Passport.js, JWT).
- **Security Headers:** Add `Content-Security-Policy` to mitigate XSS.

### **D. Monitoring**
- **Alert on failed logins** (e.g., Slack/email notifications).
- **Track token usage** (e.g., failed JWT verifications).

### **E. Documentation**
- Maintain a **runbook** for common auth outages.
- Document **API keys/secrets** securely (e.g., 1Password).

---

## **5. Escalation Path**
If issues persist:
1. **Check recent deployments** (revert if needed).
2. **Isolate the problem** (backend vs. frontend).
3. **Engage security team** if credential leaks are suspected.
4. **Review logs** for correlation between failures.

---
**Final Tip:** For complex auth flows, **mock the entire sequence** (e.g., using **Postman** + **Redis**). Quickly identify where the pipeline breaks.

---
**Key Takeaway:** Authentication issues are rarely frontend/backend-only. **Correlate logs**, **test endpoints**, and **validate assumptions** systematically. Most fixes involve checking **secrets**, **timeouts**, and **configuration drift**.