---

# **[Pattern] Authentication Techniques: Reference Guide**

---

## **Overview**
Authentication Techniques define methods to verify a user's identity before granting access to systems, services, or data. This guide covers foundational concepts, implementation details, and practical use cases for common authentication patterns. Properly configured authentication ensures security, compliance, and a seamless user experience (UX). Techniques include **password-based, multi-factor (MFA), biometric, OAuth, JWT, and session-based** methods. Each technique balances security trade-offs (e.g., usability vs. security) and may integrate with patterns like **Authorization**, **Identity Federation**, or **Rate Limiting**.

---

## **1. Key Concepts**
| **Term**               | **Definition**                                                                                     | **Use Case Example**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Factor**             | A method of authentication (e.g., *something you know* = password). Factors can be **single (1FA)** or **multi (MFA)**. | MFA combining a password (1FA) and SMS code (2FA).                                  |
| **Credential**         | Data proving identity (e.g., password, token, fingerprint).                                        | A JWT token stored in an HTTP header.                                                |
| **Challenge-Response** | Server sends a challenge (e.g., CAPTCHA) to validate user response.                                | Verifying a human user via a distorted word puzzle on a login page.                   |
| **Session Token**      | Temporary identifier (e.g., cookie) to track authenticated users.                                | A `session_id` stored as a HTTP-only cookie.                                         |
| **Stateless Auth**     | No server-side session storage (e.g., JWTs).                                                     | API clients using a JWT in every request.                                             |
| **Stateful Auth**      | Server maintains session state (e.g., cookies).                                                  | Web apps using server-side session storage with PHP sessions.                        |
| **IdP (Identity Provider)** | Third-party service managing user identities (e.g., Google, OAuth2).                           | A user logging in via "Sign in with Google."                                         |

---

## **2. Schema Reference**
Below are common data structures and formats for authentication techniques.

### **2.1 Authentication Request/Response Schema**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                                                                                     |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `auth_type`             | `String`       | Authentication method (e.g., `password`, `jwt`, `oauth`).                                          | `"auth_type": "jwt"`                                                                          |
| `credentials`           | `Object`       | User-provided data (e.g., password, token, biometric hash).                                       | `{"password": "secure123", "remember_me": true}`                                              |
| `challenge`             | `String`       | CAPTCHA text or dynamic code (e.g., SMS/email OTP).                                              | `"challenge": "CAPTCHA_2xy7"`                                                                |
| `token`                 | `String`       | JWT/OAuth token, session ID, or refresh token.                                                   | `"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`                                          |
| `metadata`              | `Object`       | Additional context (e.g., IP, device fingerprint, user agent).                                    | `{"ip_address": "192.0.2.1", "device_type": "mobile", "geo": {"country": "US"}}`           |
| `status`                | `String`       | Outcome of authentication (`success`, `failed`, `pending`).                                       | `"status": "success", "message": "Authenticated"`                                             |
| `session_id`            | `String`       | Unique identifier for server-side sessions.                                                      | `"session_id": "abc123xyz456"`                                                              |
| `expires_at`            | `Timestamp`    | Session token expiration (UTC).                                                                | `"expires_at": "2024-12-01T12:00:00Z"`                                                     |
| `refresh_token`         | `String`       | Token to obtain new access tokens without re-authenticating.                                      | `"refresh_token": "refresh_abc789def120"`                                                   |

---

### **2.2 Common Authentication Methods**
| **Method**               | **Schema Key**  | **Description**                                                                                     | **Storage**          | **Security Level** | **Example Use Case**                          |
|--------------------------|-----------------|---------------------------------------------------------------------------------------------------|----------------------|--------------------|-----------------------------------------------|
| **Password-Based**       | `password`      | Plaintext or hashed password.                                                                      | DB (hashed)          | Medium             | Traditional username/password login.           |
| **Multi-Factor Auth (MFA)** | `factor1/factor2` | Combines two+ factors (e.g., password + TOTP).                                                      | DB + TOTP secrets     | High               | Bank login requiring SMS code after password.   |
| **Biometric**            | `biometric_hash` | Fingerprint/face recognition hash.                                                                 | Device/OS            | High               | iPhone Face ID for app unlock.                 |
| **JWT (JSON Web Token)** | `token`         | Stateless token with payload (claims) and signature.                                               | Client-side          | High               | API auth via `Authorization: Bearer <token>`.    |
| **OAuth2/OIDC**          | `access_token`  | Third-party token for delegated auth (e.g., Google).                                               | Client/Server        | Medium-High        | "Sign in with Google" flow.                    |
| **Session-Based**        | `session_id`    | Server-generated temporary ID (e.g., PHPSESSID).                                                   | Server (cookies)     | Medium             | Web app login preserving state.               |
| **Challenge-Response**   | `challenge`     | Dynamic code (e.g., SMS, email OTP) or CAPTCHA.                                                   | Transient            | Medium-High        | 2FA SMS code after password.                   |

---
## **3. Query Examples**
### **3.1 Password Authentication (Stateless)**
**Request:**
```http
POST /auth/login
Content-Type: application/json

{
  "auth_type": "password",
  "credentials": {
    "username": "user@example.com",
    "password": "secure123",
    "remember_me": false
  },
  "metadata": {
    "ip_address": "192.0.2.1"
  }
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2024-12-01T12:00:00Z",
  "refresh_token": "refresh_abc123"
}
```

**Failure Response (401 Unauthorized):**
```json
{
  "status": "failed",
  "message": "Invalid credentials",
  "errors": {
    "password": "Incorrect password"
  }
}
```

---

### **3.2 JWT Authentication (Stateless)**
**Request (Bearer Token):**
```http
GET /api/protected-resource
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Server Validation (Pseudocode):**
```python
def validate_jwt(token):
    try:
        payload = decode_jwt(token, SECRET_KEY)  # Verify signature
        return payload["sub"]  # User ID
    except:
        raise HTTPError(401)
```

---

### **3.3 OAuth2 (Delegated Auth)**
**Request (Authorization Code Flow):**
```http
GET /auth/authorize?
  client_id=CLIENT_ID&
  redirect_uri=https://client.com/callback&
  response_type=code&
  scope=email+profile
```

**Success Redirect:**
```http
GET https://client.com/callback?
  code=AUTHORIZATION_CODE&
  state=RANDOM_STATE
```

**Token Exchange:**
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
redirect_uri=https://client.com/callback&
client_id=CLIENT_ID&
client_secret=SECRET
```

**Response:**
```json
{
  "access_token": "ACCESS_TOKEN",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN"
}
```

---

### **3.4 Multi-Factor Auth (MFA)**
**Step 1: Password Login**
```http
POST /auth/login
{
  "auth_type": "password",
  "credentials": { "username": "user", "password": "pass" }
}
```
**Response (200 + MFA Challenge):**
```json
{
  "status": "pending",
  "challenge": { "type": "sms", "code": "123456" }
}
```

**Step 2: Submit MFA Code**
```http
POST /auth/verify-mfa
{
  "challenge": {
    "type": "sms",
    "code": "123456",
    "user_provided_code": true
  }
}
```
**Success Response:**
```json
{
  "status": "success",
  "token": "JWT_TOKEN"
}
```

---

## **4. Implementation Best Practices**
| **Practice**                     | **Description**                                                                                     | **Tools/Libraries**                                                                 |
|-----------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Password Hashing**             | Use slow algorithms (e.g., Argon2, bcrypt) to resist brute-force attacks.                        | `bcrypt`, `Argon2`, `PBKDF2`                                                        |
| **Token Expiration**             | Short-lived tokens (e.g., 15–60 min) with refresh tokens.                                         | JWT libraries with TTL settings                                                    |
| **Secure Storage**               | Store credentials securely (e.g., hashed passwords in DB, tokens in HTTP-only cookies).           | `HttpOnly`, `Secure` cookies, encrypted DB fields                                   |
| **Rate Limiting**                | Protect against brute-force attacks (e.g., 5 failed attempts → lockout).                          | `Redis` + rate-limiting middleware                                                  |
| **Logging & Monitoring**          | Audit failed logins and token revocations.                                                      | SIEM tools (e.g., Splunk, ELK Stack)                                               |
| **Session Management**           | Invalidate sessions on logout or suspected compromise.                                           | Server-side session cleanup (e.g., `redis-store` in Express.js)                     |
| **OAuth2 Best Practices**         | Use short-lived access tokens, PKCE for public clients, and token binding.                       | `oauth2-server` (Python), `node-oauth2-server` (Node.js)                            |
| **Biometric Security**           | Enforce liveness detection (e.g., video challenges) to prevent replay attacks.                   | Rekognition, Microsoft Azure Face API                                               |
| **CAPTCHA Integration**          | Use hCaptcha/reCAPTCHA for bot mitigation on login pages.                                        | `recaptcha-v3` (client-side), server-side validation                               |
| **Token Revocation**             | Implement a revocation list (e.g., Redis blacklist) for compromised tokens.                     | JWT blacklist middleware                                                         |

---

## **5. Security Considerations**
| **Risk**                          | **Mitigation Strategy**                                                                           | **Tools**                                                                          |
|-----------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Credentials Leak**              | Enforce password policies (length, complexity) and use salted hashing.                          | Enforcer (e.g., `zxcvbn` for password strength)                                |
| **Token Theft**                   | Use short-lived tokens, secure cookies, and audit token usage.                                   | `HttpOnly`, `SameSite` cookies, JWT libraries with TTL                          |
| **Phishing**                      | Educate users on phishing risks and use FIDO2/WebAuthn for passwordless auth.                    | WebAuthn API, `FIDO2` libraries                                                  |
| **DoS Attacks**                   | Implement rate limiting and challenge-response for slow users.                                   | Cloudflare, ` rate-limit` middleware (e.g., `express-rate-limit`)               |
| **Insecure Transfers**            | Enforce TLS (HTTPS) for all auth flows.                                                        | Let’s Encrypt, `nginx`/`Apache` HTTPS redirects                                  |
| **Man-in-the-Middle (MITM)**      | Use PKCE for OAuth2, HSTS, and token binding.                                                  | `PKCE` in OAuth2 flows, `hstspreload.org`                                       |
| **Session Hijacking**             | Regenerate session IDs after login and enforce `Secure` cookies.                               | Session rotation middleware                                                     |
| **Backdoor Accounts**             | Monitor for suspicious activity (e.g., admin account access from unusual locations).           | SIEM tools, user behavior analytics                                             |

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **Integration Example**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **[Authorization]**       | Defines what authenticated users can access after authentication.                                 | Role-based access control (RBAC) via JWT claims (e.g., `"roles": ["admin"]`).         |
| **[Identity Federation]** | Uses third-party IdPs (e.g., OAuth2, SAML) to centralize identity management.                     | Google Login via OAuth2 redirect flow.                                                |
| **[Rate Limiting]**       | Protects auth endpoints from brute-force attacks by limiting requests per user/IP.                 | Rate-limiting middleware (e.g., `nginx rate limit`).                                  |
| **[Secure Storage]**      | Encrypts sensitive data (e.g., passwords, tokens) at rest.                                        | Database encryption (e.g., `AWS KMS`), token masking in logs.                         |
| **[CAPTCHA]**             | Discourages bots from automating login attempts.                                                 | `reCAPTCHA v3` integrated with login endpoints.                                      |
| **[WebAuthn/FIDO2]**      | Passwordless auth using biometric or hardware keys.                                               | Browser-based WebAuthn API for device-bound credentials.                             |
| **[Session Management]**  | Handles session creation, validation, and termination.                                           | Server-side sessions (e.g., `RedisStore` in Express.js) or stateless JWTs.          |
| **[Audit Logging]**       | Logs auth events (e.g., logins, token revocations) for compliance and debugging.                 | SIEM tools (e.g., `Papertrail`, `AWS CloudTrail`).                                   |

---
## **7. Example Architecture**
```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│             │       │             │       │             │       │             │
│   Client    │──────▶│  Auth       │◀──────│  DB / Redis │◀──────│  Rate       │
│ (Browser/   │       │   Endpoint  │       │   (Tokens,   │       │  Limiter    │
│  Mobile)    │       │             │       │   Creds)     │       │             │
└─────────────┘       └─────────────┘       └─────────────┘       └─────────────┘
       ▲                                ▲                                ▲
       │                                │                                │
       ▼                                ▼                                ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│             │       │             │       │             │
│ OAuth2 IdP  │◀──────│  Callback   │       │  SIEM /     │
│ (Google,     │       │   Handler   │       │  Monitor    │
│  GitHub)    │──────▶│             │◀──────│  (Audit Logs)│
│             │       └─────────────┘       └─────────────┘
└─────────────┘
```

---
## **8. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                                     |
|------------------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------|
| **401 Unauthorized**               | Invalid credentials, expired token.    | Verify token signature, refresh tokens, check password storage.                                |
| **Session Stale**                  | Session expired or cookie deleted.     | Regenerate session ID, enforce `Secure` cookies.                                                |
| **MFA Failure**                    | Incorrect code or device mismatch.    | Resend code, enforce TOTP time synchronization.                                                 |
| **OAuth2 Redirect Mismatch**       | `redirect_uri` mismatch in flow.       | Match `redirect_uri` exactly with client registration.                                        |
| **Rate Limit Hit**                 | Too many failed attempts.              | Implement 2FA after X failed attempts, use CAPTCHA.                                            |
| **Token Leak**                     | Token exposed in logs/headers.         | Sanitize logs, use short-lived tokens, token binding.                                           |
| **Biometric Failure**              | Liveness detection failed.             | Retry with video challenge or fallback to password.                                            |

---
## **9. Further Reading**
- **OAuth 2.0 Authorization Framework**: [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- **JWT Best Practices**: [OAuth Tools](https://oauth.net/2/best_practices/)
- **Password Security**: [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- **WebAuthn**: [W3C Web Authentication API](https://www.w3.org/TR/webauthn-1/)
- **CAPTCHA**: [Google reCAPTCHA v3](https://developers.google.com/recaptcha/docs/v3)

---
**Last Updated:** *YYYY-MM-DD*
**Version:** *1.0*