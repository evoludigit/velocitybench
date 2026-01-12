# **[Pattern] Reference Guide: Authentication Anti-Patterns to Avoid**

---

## **Overview**
Authentication is foundational to secure systems, but poorly implemented or misapplied designs can introduce vulnerabilities, degrade usability, or violate compliance requirements. This reference guide documents **authentication anti-patterns**—common pitfalls in authentication design, implementation, or enforcement—that must be avoided to ensure security, scalability, and user experience. By recognizing these patterns, architects, developers, and security teams can proactively design robust authentication flows that resist attacks, minimize friction, and align with best practices (e.g., OWASP, NIST, or Zero Trust principles).

Anti-patterns here are categorized by **design flaws** (e.g., over-reliance on passwords) and **implementation mistakes** (e.g., insecure credential storage), along with their consequences and mitigation strategies. Each pattern includes schema definitions, example attacks, and alternative approaches for reference.

---

## **Key Concepts & Terminology**
| **Term**               | **Definition**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|
| **Authentication Anti-Pattern** | A suboptimal or insecure practice in validating user identity that introduces risks.           |
| **Credential Stuffing**     | Attackers reuse leaked credentials from one platform to access others.                          |
| **Phishing Resilience**   | Measures that make authentication resistant to social engineering (e.g., fake login pages).      |
| **Multi-Factor Resistance** | Designs that either ignore MFA or weaken its effectiveness.                                    |
| **Session Fixation**       | Exploiting predictable session identifiers to hijack user sessions.                             |
| **Over-Permissive Tokens**  | Tokens granting excessive scope (e.g., superuser access) or no expiration.                      |

---

## **Anti-Pattern Schema Reference**
Each table below outlines an anti-pattern, its **classification** (e.g., credential, session), **impact**, and **schema** (if applicable). The "Mitigation" column provides direct alternatives or safeguards.

| **Anti-Pattern**               | **Classification**       | **Primary Impact**                          | **Schema** (if applicable)                                                                 | **Mitigation**                                                                                                                                                                                                 |
|----------------------------------|---------------------------|---------------------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Plaintext Password Storage**   | Credential Storage        | Credential leaks enable account takeover.   | `UserCredentials { password: string }` (stored in DB without hashing/salt).             | **Use:** PBKDF2, bcrypt, or Argon2. Never store plaintext passwords. Add salt and limit retries (e.g., 5 attempts).                                                                                               |
| **Password Expired Too Freq**   | Password Policy           | User fatigue -> weak passwords or password managers. | Custom expiry period (e.g., `PASSWORD_EXPIRY = 90 days`).                                  | **Use:** 120–180 days (NIST) or dynamic policies tied to risk (e.g., 30 days for high-risk users). Offer secure password managers as an exemption.                                                                   |
| **Weak Password Rules**          | Password Policy           | Predictable passwords (e.g., "Password123").   | Rules: `{ minLength: 8, requireSpecialChar: true, avoidCommonWords: false }`.            | **Use:** NIST-compliant rules (no special chars, allow passphrases). Enforce entropy (e.g., 28+ bits) and block weak patterns (e.g., "admin", "123456").                                                                 |
| **Hardcoded Admin Credentials** | Deployment Security       | Accessible via source code or config files. | `config: { adminUser: "default", adminPassword: "password123" }`.                         | **Use:** Generate random credentials post-deployment. Store in secrets manager (e.g., AWS Secrets Manager) with short TTL. Rotate credentials periodically.                                                                     |
| **Session Fixation**             | Session Management        | Hijacked sessions via predictable tokens.    | `SessionToken { id: `user123_abc` }` (based on predictable user ID).                    | **Use:** Token regeneration on login. Bind sessions to client IP/device (with user consent). Employ short-lived tokens (e.g., JWT with 15-minute expiry).                                                                   |
| **Over-Permissive OAuth Scopes** | Token Design              | Unrestricted API access via tokens.           | `OAuthToken { scopes: ["read:all", "write:database"] }`.                                | **Use:** Least privilege principle. Scope tokens to granular permissions (e.g., `read:user_profile`). Validate scopes server-side. Avoid `"all"` or superuser scopes in tokens.                                                                 |
| **No Rate Limiting on Login**    | Brute Force Protection    | Credential stuffing via automated attacks.     | `LoginAttempts { userId: "123", attempts: 0 }` (no limits).                             | **Use:** 3–5 failed attempts → lock account temporarily (with admin review). Implement CAPTCHA post-3 attempts. Monitor for unusual patterns (e.g., rapid logins from multiple locations).                                                                 |
| **Shared Session Tokens**        | Session Sharing           | Token reuse across devices/compromised systems.| `SessionToken { id: `shared_token_123`, validFor: 30 days }`.                           | **Use:** Device-specific tokens (e.g., browser/device fingerprinting). Enforce MFA for shared sessions. Limit token validity to session duration (e.g., 15–30 mins).                                                                   |
| **No Passwordless Options**      | User Experience           | Phishing risk via username/password prompts.| `AuthMethods { usernamePassword: true, passwordless: false }`.                          | **Use:** Offer MFA (SMS, TOTP, push notifications) and passwordless flows (e.g., Magic Links, FIDO2). Prioritize phishing-resistant factors (e.g., biometrics, hardware keys).                                                                    |
| **Token Leakage via URLs**       | Token Exposure            | Accidental token exposure in browser history.| `LoginURL: "example.com/login?token=abc123"` (token in query string).                    | **Use:** Pass tokens via `POST` requests or `HttpOnly` cookies. Avoid query strings. Encode tokens (e.g., Base64) only if additionally encrypted.                                                                                     |
| **No Logging/Monitoring**        | Incident Response         | Undetected credential leaks or breaches.       | No audit logs for failed logins or token revocations.                                      | **Use:** Centralized logging (e.g., SIEM) for failed attempts, token issuance/revocation. Alert on anomalies (e.g., logins from unusual locations). Enforce retention policies (e.g., 90 days).                                                                 |
| **Ignoring MFA for High-Risk Users** | Access Control         | Elevated risk for privileged accounts.      | `UserRole { role: "admin", requiresMFA: false }`.                                         | **Use:** Mandate MFA for all high-risk users (e.g., admins, devs). Enforce 2FA for sensitive operations (e.g., sensitive data access).                                                                                             |
| **Generic Error Messages**       | User Feedback             | Hides attack indicators (e.g., whether username exists).| `ErrorResponse: "Invalid credentials."` (no specifics).                                   | **Use:** Generic messages forSuccessful logins; specific (but non-leaky) messages for failures (e.g., "Email not found" vs. "Incorrect password"). Avoid revealing account existence.                                                                   |
| **No Token Revocation Mechanism** | Token Lifecycle          | Compromised tokens remain valid.               | `Token { id: "abc123", revoked: false }` (no revocation endpoint).                       | **Use:** Implement token revocation endpoints (e.g., `/revoke?token=abc123`). Add short expiry (e.g., 1 hour) and refresh tokens. Store revoked tokens in a blockchain or hashtable for quick lookup.                                                          |
| **Cross-Origin Token Exposure**  | CORS Misconfiguration     | Tokens accessible via `document.cookie` from malicious sites.| `CORS: { allowedOrigins: ["*"] }` (wildcard).                                            | **Use:** Restrict `allowedOrigins` to trusted domains. Set `SameSite` cookies to `Strict` or `Lax`. Use `HttpOnly` and `Secure` flags for cookies.                                                                                     |

---

## **Query Examples**
Below are common database/API queries to **detect or mitigate** anti-patterns. Replace `<placeholder>` with actual values.

### **1. Detect Hardcoded Credentials in Config Files**
**Query (grep for plaintext passwords):**
```sql
-- Check config files for password patterns
grep -r "password\|secret" /etc/config/ | grep -v "#"
```
**Mitigation:**
- Replace with placeholders (e.g., `password: "{{env.PASSWORD}}"`).
- Use secrets managers (e.g., AWS Secrets Manager, HashiCorp Vault).

### **2. Audit Password Hashing Strength**
**Query (check for weak hashes):**
```sql
-- Identify users with unsalted or weak hashes
SELECT user_id, password_hash
FROM users
WHERE password_hash NOT LIKE '%$2a$%'  -- Not bcrypt
   OR LENGTH(password_hash) < 60;     -- Weak hash length
```
**Mitigation:**
- Enforce bcrypt with cost factor ≥ 12:
  ```python
  # Example (Python)
  from bcrypt import gensalt, hashpw
  salt = gensalt(rounds=12)
  hashed = hashpw(b"userpass", salt)
  ```

### **3. Check for Over-Permissive Tokens**
**Query (find tokens with excessive scopes):**
```sql
-- Tokens granting elevated permissions
SELECT token_id, scopes
FROM auth_tokens
WHERE scopes LIKE '%admin%' OR scopes LIKE '%superuser%';
```
**Mitigation:**
- Scope tokens to least privilege:
  ```json
  // Example JWT payload
  {
    "scopes": ["read:user_data", "update:profile"]
  }
  ```

### **4. Detect Session Fixation Vulnerabilities**
**Query (find predictable session IDs):**
```sql
-- Sessions using predictable patterns (e.g., user_id concatenated)
SELECT session_id
FROM sessions
WHERE session_id LIKE '%_user%'  -- Example pattern
   OR session_id LIKE '%123%';   -- User ID in session ID
```
**Mitigation:**
- Regenerate session IDs on login:
  ```python
  # Example (Python Flask)
  from flask import session
  session.clear()
  session['session_id'] = generate_random_id()
  ```

### **5. Monitor Brute Force Attempts**
**Query (track failed login attempts):**
```sql
-- Failed logins per user (brute force detection)
SELECT user_id, COUNT(*) as attempts
FROM login_attempts
WHERE status = 'failed'
GROUP BY user_id
HAVING COUNT(*) > 3;
```
**Mitigation:**
- Enforce rate limiting:
  ```python
  # Example (Python using Flask-Limiter)
  from flask_limiter import Limiter
  limiter = Limiter(app, key_func=get_remote_address, default_limits=["5 per minute"])
  ```

### **6. Check for Token Leakage in URLs**
**Query (find tokens in URLs):**
```sql
-- Log entries with tokens in query strings
SELECT *
FROM access_logs
WHERE request_uri LIKE '%token=%'
   OR request_uri LIKE '%access_token=';
```
**Mitigation:**
- Avoid tokens in URLs:
  ```http
  -- Bad: Token in URL
  GET /api/data?token=abc123

  -- Good: Token in headers
  POST /api/data
  Authorization: Bearer abc123
  ```

---

## **Related Patterns**
To counter authentication anti-patterns, leverage these complementary patterns:

| **Pattern**                     | **Purpose**                                                                                     | **Reference**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Multi-Factor Authentication (MFA)** | Adds resilience against credential theft.                                                   | [OWASP MFA Guide](https://cheatsheetseries.owasp.org/cheatsheets/Multi-Factor_Authentication_Cheat_Sheet.html) |
| **Passwordless Authentication** | Eliminates password-related risks (e.g., phishing).                                         | [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html)               |
| **Zero Trust Architecture**      | Verifies every request, even within the network.                                             | [Zero Trust Principles](https://www.cisa.gov/zero-trust)                       |
| **Least Privilege Access**       | Limits token scopes to minimal required permissions.                                         | [OWASP Least Privilege](https://owasp.org/www-community/Least_privilege_principle) |
| **Token Bindings**               | Ensures tokens are used only by the intended client (e.g., IP/device).                       | [IETF Token Binding](https://datatracker.ietf.org/doc/html/rfc8475)             |
| **Passwordless with WebAuthn**   | Uses FIDO2 for phishing-resistant authentication.                                              | [WebAuthn Spec](https://www.w3.org/TR/webauthn/)                              |
| **Session Resilience**           | Protects sessions from hijacking via token regeneration and binding.                          | [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) |
| **Secure Password Policies**     | Enforces strong, memorable passwords with entropy checks.                                     | [NIST Digital Identity Guidelines](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B.pdf) |
| **API Gateways for Token Validation** | Centralizes token validation and revocation.                                               | [AWS API Gateway Token Auth](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api-develop-authorizers-jwt.html) |

---

## **Best Practices Summary**
1. **Credential Storage:**
   - Never store plaintext passwords. Use Argon2 or bcrypt with salts.
   - Rotate credentials periodically (especially for admins).

2. **Password Policies:**
   - Follow NIST guidelines (no special chars, allow passphrases).
   - Expiry: 120–180 days (or dynamic based on risk).

3. **Session Management:**
   - Regenerate tokens on login.
   - Bind sessions to client IP/device (with user consent).
   - Enforce short-lived tokens (e.g., 15–30 mins).

4. **Token Design:**
   - Least privilege principle: Granular scopes, no "all" permissions.
   - Revoke tokens on logout or compromise.

5. **Protection Against Attacks:**
   - Rate limit login attempts (3–5 tries → lockout).
   - Implement MFA for high-risk users.
   - Monitor for brute force patterns.

6. **User Experience:**
   - Offer passwordless or phishing-resistant auth (e.g., WebAuthn).
   - Avoid exposing errors that leak account existence.

7. **Observability:**
   - Log failed logins and token activity.
   - Alert on anomalies (e.g., logins from unusual locations).

---
**Final Note:** Anti-patterns evolve with attack vectors. Regularly audit authentication flows against [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) and [CWE Top 25](https://cwe.mitre.org/top25/) for credential-related vulnerabilities.