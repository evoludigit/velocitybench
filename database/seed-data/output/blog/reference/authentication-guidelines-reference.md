# **[Pattern] Authentication Guidelines Reference Guide**

---

## **Overview**
This reference guide outlines the **Authentication Guidelines** pattern, a structured framework ensuring consistent, secure, and scalable authentication implementations across systems. It defines best practices for **authentication flows, credential handling, security hardening, and integration with identity providers (IdPs)** while adhering to industry standards (e.g., OAuth 2.0, OpenID Connect, FAPI). The pattern balances **usability, security, and compliance** by standardizing:
- **Authentication mechanisms** (e.g., password-based, multi-factor, device-bound tokens).
- **Credential storage** (hashing, key rotation, secure token generation).
- **Session management** (token expiration, refresh mechanisms, revocation).
- **IdP integrations** (social logins, SAML, federated identity).
- **Audit and monitoring** (logging, anomaly detection, rate limiting).

This guide is intended for **developers, security architects, and DevOps teams** responsible for designing or reviewing authentication systems.

---

## **Schema Reference**
The following table defines key components of the **Authentication Guidelines** pattern and their attributes:

| **Component**               | **Attribute**                          | **Description**                                                                                                                                                                                                 | **Example Value**                     | **Constraints**                                                                                     |
|-----------------------------|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|------------------------------------------------------------------------------------------------------|
| **Authentication Method**   | `method`                              | Core mechanism (e.g., password, OAuth 2.0, biometric).                                                                                                                                                             | `PASSWORD`, `OIDC`, `MFA`            | Must comply with [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749).                   |
|                             | `strength`                            | Security level (e.g., weak, moderate, strong).                                                                                                                                                                   | `STRONG`                              | `STRONG` requires crypto-agility (e.g., PBKDF2 with 100k iterations).                                |
|                             | `federated`                           | Boolean: whether external IdP is used (e.g., Google, Azure AD).                                                                                                                                               | `true`/`false`                       | If `true`, must support [OpenID Connect Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html). |
| **Credential Storage**      | `algorithm`                           | Hashing algorithm for passwords (e.g., bcrypt, Argon2).                                                                                                                                                          | `bcrypt`                              | Must resist brute-force attacks; avoid MD5/SHA-1.                                                     |
|                             | `key_rotation_policy`                 | Time-based or event-based (e.g., "rotate keys every 90 days").                                                                                                                                                     | `"90d"`                               | Compliance with [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html#sec5).                |
|                             | `token_encryption`                    | Symmetric/asymmetric encryption for tokens (e.g., AES-256, RSA-OAEP).                                                                                                                                            | `AES-256-GCM`                        | Mandatory for tokens containing PII.                                                               |
| **Session Management**      | `token_type`                          | JWT, opaque token, or session cookie.                                                                                                                                                                         | `JWT`                                 | JWTs must include [standard claims](https://datatracker.ietf.org/doc/html/rfc7519#section-4.1).         |
|                             | `expiry`                              | Token lifetime (e.g., 1h, 1d).                                                                                                                                                                                     | `PT1H` (ISO 8601)                     | Max: 24h for access tokens; shorter for refresh tokens.                                              |
|                             | `refresh_token_validity`              | Duration refresh tokens remain valid (e.g., 30d).                                                                                                                                                               | `P30D`                                | Must implement [sliding validation windows](https://auth0.com/docs/secure/tokens/refresh-tokens).       |
| **Multi-Factor Authentication (MFA)** | `factor`                                | TOTP, hardware key, SMS, or biometric.                                                                                                                                                                         | `TOTP`                                | FAPI Level 2+ requires cryptographic MFA (e.g., FIDO2).                                               |
|                             | `backup_codes`                        | Boolean: enable disposable backup codes.                                                                                                                                                                       | `true`/`false`                       | Required for critical systems (e.g., [NIST SP 800-63-3](https://pages.nist.gov/800-63-3/sp800-63b.html)). |
| **IdP Integration**         | `provider`                            | IdP type (e.g., OpenID Connect, SAML 2.0).                                                                                                                                                                       | `openid_connect`                     | Must support [token binding](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-token-binding-13). |
|                             | `claims_request`                      | Custom claims requested from IdP (e.g., `email`, `groups`).                                                                                                                                                   | `["email", "picture"]`               | Avoid unnecessary PII; limit to scope.                                                              |
| **Security Hardening**      | `rate_limiting`                       | Max attempts before lockout (e.g., 5 attempts).                                                                                                                                                                   | `5`                                   | Enforce per-IP and per-user limits.                                                                |
|                             | `anomaly_detection`                   | Boolean: enable AI/ML for suspicious logins.                                                                                                                                                                       | `true`/`false`                       | Integrate with SIEM (e.g., Splunk, Datadog).                                                         |
|                             | `hsts_policy`                         | HTTP Strict Transport Security header (e.g., `max-age=31536000`).                                                                                                                                                 | `max-age=31536000; includeSubDomains`| Required for public-facing endpoints.                                                              |
| **Audit & Compliance**      | `logging`                             | Events logged (e.g., login successes/failures, token revocations).                                                                                                                                                   | `LOGIN_SUCCESS, LOGIN_FAILURE`        | Retain logs for 12 months (GDPR compliance).                                                         |
|                             | `compliance_framework`                | Standards met (e.g., SOC 2, HIPAA, GDPR).                                                                                                                                                                         | `SOC2_TYPE2`                          | Audit trail required for frameworks like PCI DSS.                                                    |

---

## **Implementation Details**
### **1. Authentication Flows**
#### **Password-Based Authentication**
- **Workflow**:
  1. User submits credentials (username/password).
  2. Server validates credentials against hashed storage (e.g., `bcrypt`).
  3. Issue JWT or session cookie with `exp` and `nbf` claims.
- **Example Request/Response**:
  ```http
  POST /auth/login
  Content-Type: application/json

  {
    "username": "user@example.com",
    "password": "securePassword123!"
  }

  HTTP/1.1 200 OK
  {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
  ```

#### **OAuth 2.0 / OpenID Connect**
- **Workflow**:
  1. Redirect user to IdP (e.g., `https://idp.example.com/authorize?response_type=code&client_id=...`).
  2. IdP redirects back with `code` or `id_token`.
  3. Exchange `code` for tokens via `/token` endpoint.
- **Example Token Request**:
  ```http
  POST /oauth/token
  Content-Type: application/x-www-form-urlencoded

  grant_type=authorization_code&code=AUTH_CODE_HERE&redirect_uri=https://client.example.com/callback

  HTTP/1.1 200 OK
  {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "id_token": "eyJhbGciOiJSUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
  ```

#### **Multi-Factor Authentication (MFA)**
- **TOTP Example**:
  - User provides password + TOTP code (e.g., from Google Authenticator).
  - Server validates TOTP using [HMAC-based OTP](https://tools.ietf.org/html/rfc6238).
  ```json
  {
    "challenge": "totp://otpauth:6:nameservice:user@example.com?secret=JBSWY3DPEHPK3PXP",
    "totp_code": "123456"
  }
  ```

### **2. Credential Storage**
- **Password Hashing**:
  - Use **bcrypt** or **Argon2id** (resistant to GPU/ASIC attacks).
  - Salt length: **16+ bytes**.
  - Cost factor: **12+ rounds** (adjust based on benchmarking).
  ```python
  # Example (bcrypt in Python)
  import bcrypt
  hashed = bcrypt.hashpw("password", bcrypt.gensalt(rounds=12))
  ```
- **Token Generation**:
  - Use **JWT** with short-lived access tokens (`exp` claim) and long-lived refresh tokens.
  - Sign with **HS256** (symmetric) or **RS256** (asymmetric).
  ```javascript
  // Node.js (jsonwebtoken)
  const jwt = require('jsonwebtoken');
  const token = jwt.sign({ userId: 123 }, 'SECRET_KEY', { expiresIn: '1h' });
  ```

### **3. Security Hardening**
- **Rate Limiting**:
  - Block after **5 failed attempts** (adjust for high-risk systems).
  - Use libraries like [Redis Rate Limiter](https://github.com/alizain/redis-rate-limiter).
- **Token Binding**:
  - Enforce [Token Binding](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-token-binding-13) to prevent token theft via MITM.
  - Example header:
    ```http
    HTTP/1.1 200 OK
    Content-Type: application/json
    DPR: http://example.com:8080

    { "access_token": "..." }
    ```
- **HTTP Security Headers**:
  ```http
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Content-Security-Policy: default-src 'self'
  Referrer-Policy: same-origin
  ```

### **4. IdP Integrations**
- **OpenID Connect Discovery**:
  - Fetch metadata from `https://idp.example.com/.well-known/openid-configuration`.
  - Validate `issuer`, `jwks_uri`, and `response_types_supported`.
- **SAML 2.0**:
  - Use libraries like [`python3-saml`](https://github.com/rohe/python3-saml) for XML parsing.
  - Enforce **strict validation** of `Assertion` elements.

### **5. Compliance**
- **GDPR/HIPAA**:
  - Anonymize user data in logs.
  - Implement **right to erasure** (delete tokens/credentials upon request).
- **PCI DSS**:
  - Never store CVV or full PANs in plaintext.
  - Use [PCI-compliant tokenization](https://www.pcisecuritystandards.org/).

---

## **Query Examples**
### **1. Validate JWT**
```bash
# Using jq and curl
curl -s "https://api.example.com/auth/validate" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.valid'
```
**Expected Output**:
```json
true
```

### **2. Rotate Refresh Token**
```http
POST /auth/refresh
Content-Type: application/x-www-form-urlencoded

refresh_token=REFRESH_TOKEN_HERE&client_id=CLIENT_ID

HTTP/1.1 200 OK
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "expires_in": 3600
}
```

### **3. Revoke Token**
```http
POST /auth/revoke
Content-Type: application/x-www-form-urlencoded

token=ACCESS_TOKEN_HERE

HTTP/1.1 204 No Content
```

### **4. Check MFA Status**
```http
GET /auth/mfa/status
Authorization: Bearer ACCESS_TOKEN

HTTP/1.1 200 OK
{
  "mfa_enabled": true,
  "backup_codes_available": true
}
```

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **[JWT Best Practices](#)** | Design secure JSON Web Tokens.                                              | When using JWTs for stateless auth.                                             |
| **[Passwordless Auth](#)**  | Eliminate passwords via magic links/SMS.                                    | For low-friction UX (e.g., public apps).                                       |
| **[Federated Identity](#)** | Manage identity across multiple domains.                                    | Multi-tenant SaaS or enterprise integrations.                                  |
| **[Session Management](#)** | Handle server-side sessions securely.                                       | When cookies or server-side sessions are preferred over JWTs.                 |
| **[Token Revocation](#)**  | Invalidate tokens proactively.                                             | For user account compromises or policy changes.                                 |
| **[Behavioral Analysis](#)** | Detect fraudulent logins.                                                  | High-risk applications (e.g., banking).                                       |
| **[Key Rotation](#)**      | Automate cryptographic material updates.                                    | For long-lived systems (e.g., APIs).                                           |

---
**Note**: For enterprise deployments, combine this pattern with **[Zero Trust Network Access (ZTNA)](#)** for perimeterless security.