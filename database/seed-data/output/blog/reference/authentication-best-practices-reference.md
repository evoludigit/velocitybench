# **[Pattern] Authentication Best Practices Reference Guide**

---

## **1. Overview**
This reference guide outlines best practices for designing and implementing **secure, scalable, and maintainable authentication systems**. Authentication is the process of verifying a user’s identity using credentials (e.g., passwords, tokens, biometrics). Adhering to these best practices mitigates risks like credential stuffing, phishing, and unauthorized access while ensuring compliance with security standards (e.g., OWASP, NIST, GDPR).

Best practices cover **multi-factor authentication (MFA), secure credential storage, token management, session handling, and regular auditing**. This guide assumes familiarity with basic authentication mechanisms (e.g., OAuth 2.0, JWT, SAML) and aims to provide actionable guidance for developers, architects, and security teams.

---

## **2. Key Concepts**

| **Concept**               | **Definition**                                                                                     | **Key Considerations**                                                                                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Multi-Factor Authentication (MFA)**  | Requires two or more verification factors (e.g., password + SMS code + biometric).               | Use time-based OTPs (TOTP) instead of SMS where possible; avoid SMS-based MFA due to SIM-swapping risks.                                                          |
| **Secure Credential Storage**       | Hashing passwords with salts and storing only cryptographic hashes (e.g., bcrypt, Argon2).      | Never store plaintext passwords; rotate secrets regularly (e.g., via Vault or AWS Secrets Manager).                                                                        |
| **Token-Based Authentication**     | Uses tokens (JWT, OAuth2) to authenticate requests without repeated credential submission.         | Set short token expiration times (e.g., 15–30 minutes); use refresh tokens securely.                                                                                   |
| **Session Management**         | Tracks active user sessions with unique session IDs and timeouts.                                  | Implement secure session cookies (HttpOnly, Secure, SameSite attributes); invalidate sessions on logout or inactivity.                                                   |
| **Brute Force Protection**     | Limits login attempts and enforces delays after failures.                                           | Use rate-limiting (e.g., Redis with fail2ban); implement CAPTCHAs for suspicious activity.                                                                             |
| **Identity Providers (IdPs)**      | Third-party services (e.g., Auth0, Okta) for centralised authentication.                          | Prefer IdPs for social logins (Google, Facebook) to reduce credential management burdens; enforce ID token validation.                                                 |
| **Audit Logging**             | Records authentication events (logins, failures, MFA use) for forensic analysis.                 | Log IP addresses, timestamps, and user actions; comply with data retention policies (e.g., GDPR).                                                                         |
| **Secure Defaults**            | Hardening configurations (e.g., disabling legacy auth protocols, enforcing HTTPS).                 | Use security headers (e.g., CSP, HSTS); disable empty password hashes.                                                                                                     |
| **Password Policies**         | Enforces complexity, length, and rotation rules for passwords.                                     | Require minimum 12 characters with mixed case, numbers, and symbols; ban common passwords from breach databases (e.g., Have I Been Pwned).                                     |

---

## **3. Schema Reference**
Below are essential components of a secure authentication system with their attributes.

### **3.1 Authentication Schema**
| **Component**               | **Attributes**                                                                 | **Example Value**                          | **Notes**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------|--------------------------------------------|------------------------------------------------------------------------------------------------|
| **User Credentials**        | `user_id`, `username`, `password_hash` (bcrypt/Argon2), `salt`, `last_updated` | `{"user_id": "u123", "password_hash": "$2b$12$..."}` | Store only hashed passwords; salt must be unique per user.                                      |
| **Session Token**           | `token`, `expires_at`, `ip_address`, `user_agent`, `created_at`                | `{"token": "eyJhbGciOiJIUzI1NiIs..."}`      | Token should include `alg`: "HS256" (HMAC) or "RS256" (RSA) for JWTs.                         |
| **Refresh Token**           | `refresh_token`, `expires_at`, `revoked`                                     | `{"refresh_token": "rf5678..."}`           | Store refresh tokens securely (e.g., in a database with revocation flag); issue short-lived access tokens. |
| **MFA Configuration**       | `mfa_enabled`, `method` (TOTP/SMS/email), `secret` (for TOTP)                  | `{"mfa_enabled": true, "method": "TOTP"}`  | For TOTP, use `pyotp` or `google-authenticator`; rotate secrets periodically.                |
| **Rate Limit Rules**        | `max_attempts`, `cool_down_seconds`, `ip_blacklist`                          | `{"max_attempts": 5, "cool_down": 10}`     | Implement per-user and per-IP limits; log failed attempts.                                      |
| **Audit Log Entry**         | `event_id`, `user_id`, `event_type` (login/failure), `timestamp`, `ip`, `status` | `{"event_id": "a456", "status": "failed"}` | Include `event_type`: "login_success", "login_failure", "mfa_approved", etc.                 |

---

## **4. Implementation Details**

### **4.1 Secure Password Hashing**
- **Algorithm**: Use **Argon2i** (recommended by OWASP) or **bcrypt** (for legacy systems).
- **Work Factor**: Adjust `cost` parameter (e.g., bcrypt: `cost=12`).
- **Salting**: Generate a unique salt per user (16+ bytes).

**Example (Python with Argon2):**
```python
import argon2
hasher = argon2.PasswordHasher()
password_hash = hasher.hash("user_password")  # Output: "$argon2id$v=19$m=65536,t=2,p=1$c2VuZXI$..."
```

### **4.2 JWT Token Generation**
- **Claims**: Include `iss`, `sub` (subject), `exp`, `iat`, and custom claims (e.g., `roles`).
- **Signing**: Use **RSA (RS256)** for production; avoid HMAC (HS256) on shared secrets.
- **Expiration**: Set `exp` to **15–30 minutes**; use refresh tokens for longer sessions.

**Example (JWT with PyJWT):**
```python
import jwt
payload = {
    "sub": "u123",
    "exp": datetime.utcnow() + timedelta(minutes=30),
    "roles": ["user"]
}
token = jwt.encode(payload, "RS256_PRIVATE_KEY", algorithm="RS256")
```

### **4.3 Multi-Factor Authentication (MFA)**
- **TOTP (Time-Based OTP)**:
  - Use libraries like `pyotp` or `google-authenticator`.
  - Example secret: `JBSWY3DPEHPK3PXP`.
  - Generate 6-digit codes valid for **30 seconds**.

**Example (TOTP Setup):**
```python
import pyotp
totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")
current_code = totp.now()  # Output: "123456"
```

- **SMS/Email OTP**:
  - Avoid if possible (vulnerable to SIM swapping).
  - Use **email-based OTPs** only for low-risk accounts.

### **4.4 Session Management**
- **Secure Cookies**:
  - Set `HttpOnly`, `Secure`, and `SameSite=Strict` attributes.
  - Example (Flask):
    ```python
    @app.route("/login")
    def login():
        session["user_id"] = "u123"
        session.permanent = True  # Adjust cookie expiry
    ```
- **Invalidation**:
  - Invalidate sessions on logout or after inactivity (e.g., 30 minutes).
  - Use a database or Redis to track active sessions.

### **4.5 Rate Limiting**
- **Library**: Use `flask-limiter` (Python) or `nginx rate limiting`.
- **Rules**:
  - Default: **5 attempts per 10 seconds per IP**.
  - Increase limits for MFA users (e.g., 10 attempts).

**Example (Flask-Limiter):**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route("/login")
@limiter.limit("5 per 10 seconds")
def login():
    ...
```

### **4.6 Audit Logging**
- **Fields to Log**:
  1. `user_id` (if authenticated)
  2. `ip_address`
  3. `user_agent`
  4. `event_type` (login/failure/MFA)
  5. `timestamp`
- **Storage**: Centralised logs (e.g., ELK Stack, Splunk) or database tables.

**Example Log Entry (JSON):**
```json
{
  "event_id": "a789",
  "user_id": "u123",
  "event_type": "login_failure",
  "ip_address": "192.0.2.1",
  "timestamp": "2023-10-01T12:00:00Z",
  "status": "failed"
}
```

### **4.7 Secure Defaults**
- **Disable Legacy Protocols**:
  - Disable `Basic Auth` in favour of JWT/OAuth2.
  - Block outdated TLS versions (e.g., TLS 1.0/1.1).
- **HTTP Headers**:
  - Add:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `Content-Security-Policy: default-src 'self'`
- **HTTPS Enforcement**:
  - Use **HSTS** with `Strict-Transport-Security` header.

---

## **5. Query Examples**

### **5.1 Check User Credentials (Secure Hashing)**
**Input**:
```json
{
  "username": "alice",
  "password": "SecureP@ss123"
}
```
**Output**:
```python
# Verify password in Python
if hasher.verify("SecureP@ss123", password_hash):
    # Authenticate user
```

### **5.2 Validate JWT Token**
**Input**:
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
**Output**:
```python
# Decode JWT in Python
decoded = jwt.decode(token, "RS256_PUBLIC_KEY", algorithms=["RS256"])
```

### **5.3 Enforce MFA**
**Input**:
```json
{
  "mfa_secret": "JBSWY3DPEHPK3PXP",
  "totp_code": "123456"
}
```
**Output**:
```python
# Verify TOTP in Python
if totp.verify("123456"):
    return "MFA approved"
else:
    return "Invalid code"
```

### **5.4 Rate Limit Check**
**Input**:
```json
{
  "ip": "192.0.2.1",
  "action": "login"
}
```
**Output**:
```python
# Check rate limit (pseudo-code)
if is_rate_limited(ip, action):
    return HTTP_429("Too many requests")
```

### **5.5 Log Authentication Event**
**Input**:
```json
{
  "event_id": "a789",
  "user_id": "u123",
  "event_type": "login_success",
  "ip": "192.0.2.1"
}
```
**Output**:
```python
# Store in database/ELK
insert_into_audit_log(event_id, user_id, event_type, ip, timestamp)
```

---

## **6. Common Pitfalls and Mitigations**

| **Pitfall**                          | **Risk**                                  | **Mitigation**                                                                                     |
|---------------------------------------|------------------------------------------|----------------------------------------------------------------------------------------------------|
| Storing plaintext passwords           | Credential leaks                          | Use **Argon2/bcrypt** with salts; never store plaintext.                                           |
| Long-lived JWT tokens                 | Token theft                               | Set `exp` to **≤30 minutes**; use refresh tokens.                                                  |
| Weak MFA (e.g., SMS)                  | SIM swapping                              | Prefer **TOTP** or hardware keys (FIDO2).                                                          |
| No rate limiting                       | Brute force attacks                      | Implement **5 attempts per 10 seconds**; log failures.                                            |
| Insecure session storage              | Session hijacking                         | Use **HttpOnly, Secure, SameSite cookies**; invalidate on logout.                                  |
| No audit logging                       | Undetected breaches                       | Log **all** auth events; comply with GDPR/legal requirements.                                     |
| Hardcoded secrets                      | Credential exposure                       | Use **Vault, AWS Secrets Manager, or environment variables** (never in code).                     |
| Ignoring password breach databases    | Reused credentials                        | Block hashed passwords from **Have I Been Pwned**; enforce complexity.                                |

---

## **7. Related Patterns**
1. **[Token Rotation]** – Automatically rotate refresh tokens to mitigate token theft.
2. **[Zero Trust Architecture]** – Verify every request, not just at login (e.g., OAuth2 with `request_uri`).
3. **[Passwordless Authentication]** – Use magic links or WebAuthn for phishing-resistant logins.
4. **[OAuth 2.0 Best Practices]** – Securely implement `authorization_code` and `client_credentials` flows.
5. **[Biometric Authentication]** – Integrate FIDO2/WebAuthn for passwordless MFA.
6. **[Secure API Gateway]** – Use **API Gateways** (e.g., Kong, Apigee) to enforce auth policies centrally.
7. **[Password Reset Flow]** – Implement **time-limited, one-time tokens** for resets (never via email).

---
## **8. Further Reading**
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) (Digital Identity Guidelines)
- [JWT Best Practices](https://auth0.com/blog/critical-jwt-security-considerations/)
- [Google’s Password Management](https://security.googleblog.com/2021/08/better-passwords-for-better-security.html)