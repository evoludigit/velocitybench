# **[Pattern] Authentication Gotchas: Common Pitfalls & Best Practices Reference Guide**

---

## **Overview**
Authentication is foundational to secure systems, but poorly designed or misconfigured authentication mechanisms introduce critical vulnerabilities. This guide outlines **common "gotchas"**—unexpected issues or misconfigurations—that developers often overlook, leading to security breaches, credential leaks, or application lockouts. The goal is to arm engineers with actionable insights to proactively mitigate risks in auth workflows, ensuring robustness while avoiding costly mistakes. Topics include session management, credential handling, multi-factor authentication (MFA), and API-level pitfalls.

---

## **Key Concepts & Implementation Details**
Authentication gotchas stem from misalignment between theoretical best practices and real-world constraints. The following categories encapsulate common failure modes:

| **Category**               | **Description**                                                                                     | **Impact**                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Credential Handling**    | Poor storage, exposure, or reuse of secrets (passwords, tokens, keys).                            | Account takeover, credential stuffing, or API abuse.                                             |
| **Session Management**     | Weak session validity, lack of expiration, or improper token handling.                          | Session hijacking, persistent access after deauthentication.                                  |
| **Multi-Factor Authentication (MFA)** | Misconfigured MFA (e.g., bypasses, weak fallback mechanisms).                                   | Reduced security; single-factor reliance in "backup" flows.                                  |
| **Session Fixation**       | Allowing attackers to manipulate session IDs/tokens.                                               | Compromised sessions without user interaction.                                                 |
| **Race Conditions**        | Undefined timing in auth flows (e.g., concurrent logins, token rotation).                        | Security gaps, inconsistent state, or denial-of-service.                                       |
| **API Authentication**     | Misuse of tokens in stateless APIs or overuse of cookies for stateless auth.                     | Token leakage via logs/headers, session fixation in APIs.                                      |
| **Password Practices**    | Weak password policies, brute-force vulnerabilities, or reused credentials.                      | Credential leaks via phishing or brute-force attacks.                                          |
| **Deauthentication**       | Incomplete session cleanup (e.g., lingering tokens, cached credentials).                       | Persistent access even after user logout.                                                     |

---

## **Schema Reference**
Below are table schemas for critical authentication configurations, highlighting common missteps and their fixes.

### **1. Session Configuration Schema**
| Field               | Description                                                                                     | **Gotcha**                                                                                     | **Best Practice**                                                                                  |
|---------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `SessionTimeout`    | Max inactivity duration before session expires (seconds).                                          | **Too long:** Leaves active sessions exposed after device loss. **Too short:** Frustrates users. | **Default:** 30–1800 seconds; tie to app activity (e.g., last-click).                            |
| `SessionType`       | Type: stateless (JWT) or stateful (server-side cookies).                                         | **Stateless:** JWTs can leak in logs/headers; **Stateful:** Server must store session state. | **Stateless for APIs**, **stateful for SPAs** (cookies with `HttpOnly`, `Secure` flags).          |
| `TokenIssuer`       | Entity generating tokens (e.g., `auth-service`, `third-party`).                                  | **Third-party tokens:** Risk if issuer is compromised.                                          | Prefer **in-house JWT issuance** with short-lived tokens.                                            |
| `TokenRotation`     | How frequently tokens should refresh/replace.                                                   | **No rotation:** Stale tokens persist after password changes.                                  | **Short-lived tokens** (e.g., 15–30 mins) + refresh tokens.                                          |

---

### **2. Password Policy Schema**
| Field               | Description                                                                                     | **Gotcha**                                                                                     | **Best Practice**                                                                                  |
|---------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `MinLength`         | Minimum password length (chars).                                                                | **Too short:** Prone to brute-force. **Too long:** User frustration.                          | **Minimum:** 12 chars; **Complexity:** Require uppercase, lowercase, numbers, symbols.           |
| `MaxAttempts`       | Max login attempts before lockout.                                                             | **Too few:** Locks out legitimate users. **Too many:** Enables brute-force.                     | **Default:** 5 attempts; **Lockout Duration:** 15 mins.                                             |
| `PasswordHistory`   | Number of unique passwords to enforce before reuse.                                            | **None:** Allows password reuse post-reset.                                                    | **Enforce:** 3–5 unique passwords before reuse.                                                    |
| `BreachCheck`       | Integrate with known-compromised credential databases.                                         | **Off:** Exposed credentials reused without detection.                                         | **Enable:** Integrate with HaveIBeenPwned or similar services.                                        |

---

### **3. MFA Schema**
| Field               | Description                                                                                     | **Gotcha**                                                                                     | **Best Practice**                                                                                  |
|---------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `EnforcementLevel`  | Who requires MFA (admins, guests, all users).                                                  | **Optional:** Users bypass MFA; **All:** Admin overhead.                                        | **Enforce MFA for:** All privileged users (e.g., `email=admin@...`).                              |
| `FallbackMethod`    | Backup auth method if primary MFA fails (e.g., SMS → email).                                    | **SMS-only:** Vulnerable to SIM swapping. **Email-only:** Slower than SMS.                     | **Prefer hardware keys** over SMS/email; **Multi-fallback:** Email + backup codes.                  |
| `SessionScope`      | Whether MFA is required for new sessions or all sessions.                                      | **New-only:** Existing sessions remain single-factor.                                           | **Require MFA for all sessions** (including existing ones on reauth).                             |
| `RateLimit`         | Max MFA attempts before account lockout.                                                       | **Unlimited:** Enables brute-force on MFA steps.                                               | **Max 3 attempts** before lockout; **Use CAPTCHA** post-2nd failure.                               |

---

### **4. Token Management Schema**
| Field               | Description                                                                                     | **Gotcha**                                                                                     | **Best Practice**                                                                                  |
|---------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `TokenType`         | Token format (JWT, OAuth2, SAML, etc.).                                                       | **JWT:** Self-contained but risks if not short-lived. **OAuth:** Scope mismanagement.          | **JWT:** Use with `exp` and `nbf` claims. **OAuth:** Scope tokens strictly.                       |
| `TokenStorage`      | Where tokens are stored (client-side, server-side, etc.).                                      | **LocalStorage:** Vulnerable to XSS. **Cookies:** Session fixation risk.                      | **HttpOnly, Secure cookies** for server-side sessions; **Memory-only** for client-side tokens.    |
| `Revocation`        | How tokens are invalidated (e.g., blacklist, short lifetime).                                  | **No revocation:** Stale tokens persist after deauth.                                           | **Short-lived tokens + refresh tokens** over blacklists.                                            |
| `TokenSize`         | Token length (bits/shorter).                                                                  | **Too long:** Overhead for APIs. **Too short:** Easier to brute-force.                        | **256-bit (32-byte) tokens** for balance of security/size.                                          |

---

## **Query Examples**
Below are code snippets illustrating common misconfigurations and their fixes.

---

### **1. Session Fixation Attack (Vulnerable)**
```javascript
// ❌ UNSAFE: Lets attacker set session ID
app.get('/login', (req, res) => {
  req.session.sessionID = generateSessionID(); // Fixed ID exposed to attacker
  res.send('Login page');
});
```
**Fix:** Generate session ID **after** authentication:
```javascript
// ✅ SAFE: Session ID created post-auth
app.post('/login', (req, res) => {
  if (authenticateUser(req.body)) {
    req.session.regenerate(() => { // New ID per session
      req.session.save(() => res.redirect('/dashboard'));
    });
  }
});
```

---

### **2. Weak Password Policy (Vulnerable)**
```javascript
// ❌ UNSAFE: Allows weak passwords
const validatePassword = (password) => password.length >= 6;
```
**Fix:** Enforce complexity and breach checks:
```javascript
// ✅ SAFE: Complexity + breach check
const zxcvbn = require('zxcvbn');
const breachCheck = require('haveibeenpwned-api');

async function validatePassword(password) {
  if (zxcvbn(password).score < 3) return false; // Weak
  const pwned = await breachCheck.isPwned(password);
  return !pwned;
}
```

---

### **3. MFA Bypass (Vulnerable)**
```javascript
// ❌ UNSAFE: Allows login without MFA for "guest" users
if (isGuest(req.user)) return true; // Bypasses MFA
```
**Fix:** Enforce MFA for all privileged users:
```javascript
// ✅ SAFE: MFA for admins only
if (req.user.role === 'admin' && !req.session.mfaVerified) {
  return res.redirect('/mfa/setup');
}
```

---

### **4. JWT Token Leak (Vulnerable)**
```javascript
// ❌ UNSAFE: Exposes JWT in client-side logs
const token = jwt.sign({ userId: 123 }, 'secret', { expiresIn: '1h' });
console.log('JWT:', token); // Leaks in browser console
```
**Fix:** Tokenize in memory and use `HttpOnly` cookies:
```javascript
// ✅ SAFE: Server-side token + HttpOnly cookie
const token = jwt.sign({ userId: 123 }, process.env.JWT_SECRET, { expiresIn: '15m' });
res.cookie('token', token, { httpOnly: true, secure: true });
```

---

## **Error Handling Gotchas**
| **Error**               | **Cause**                                                                                     | **Solution**                                                                                  |
|-------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **500 Server Error on Logout** | Session cleanup race condition.                                                              | Use `req.session.destroy()` with error handling.                                              |
| **Token Rotates Too Often** | Short `exp` claim causes friction.                                                           | Balance with refresh tokens (e.g., 15m access + 1h refresh).                                  |
| **MFA Lockout Without Feedback** | No user feedback on MFA failures.                                                             | Show error: *"3/3 attempts. Try again in 15m."*                                               |
| **Session Hijacking via CSRF** | Missing CSRF tokens in stateless APIs.                                                        | Use `SameSite` cookies + CSRF tokens for stateful sessions.                                    |
| **Password Reset Tokens Leaked** | Tokens sent via email without encryption.                                                    | Use **TOTP** or **OAuth PKCE** for reset flows; encrypt tokens.                               |

---

## **Related Patterns**
To complement **Authentication Gotchas**, consider integrating these patterns for layered security:

| **Pattern**               | **Purpose**                                                                                     | **When to Use**                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **[Zero Trust Access](https://example.com/zero-trust)** | Assume breach; verify every request.                                                           | Cloud-native apps, distributed teams, or high-security sectors (e.g., finance).              |
| **[Rate Limiting](https://example.com/rate-limiting)** | Throttle auth requests to mitigate brute-force.                                               | High-traffic APIs, login endpoints, or payment gateways.                                      |
| **[Passwordless Auth](https://example.com/passwordless)** | Eliminate password storage risks via magic links/TOTP.                                         | Consumer apps prioritizing UX over legacy auth.                                                |
| **[API Gateway Auth](https://example.com/api-gateway)** | Centralize auth for microservices via JWT/OAuth at the gateway.                               | Microservices architectures; avoids per-service auth logic.                                    |
| **[Post-Compromise Response](https://example.com/post-compromise)** | Detect and revoke compromised credentials.                                                     | After breach detection or credential leak incidents.                                          |

---
## **Debugging Tools**
- **JWT Debugging:** [jwt.io](https://jwt.io) (decode/validate tokens).
- **Brute-Force Testing:** `hydra` (for local auth endpoint testing).
- **MFA Testing:** Tools like **OTP Authenticator** or **Duo Security**.
- **Session Inspection:** Browser DevTools (`Application > Cookies` for session tokens).

---
## **Conclusion**
Authentication gotchas often stem from trade-offs between security, usability, and performance. The key is to **fail securely**—default to strict policies (e.g., MFA, short-lived tokens) and allow exceptions via explicit user opt-in. Regularly audit auth flows with tools like **OWASP ZAP** or **Burp Suite**, and keep policies updated with evolving threats (e.g., quantum-resistant crypto).

**Final Checklist:**
1. [ ] Enforce MFA for all privileged users.
2. [ ] Short-lived tokens (<1h) with refresh tokens.
3. [ ] `HttpOnly`, `Secure` cookies for sessions.
4. [ ] Rate-limit auth endpoints (e.g., 5 attempts/15m).
5. [ ] Monitor for credential breaches (e.g., HIBP).
6. [ ] Test MFA fallbacks (e.g., backup codes).