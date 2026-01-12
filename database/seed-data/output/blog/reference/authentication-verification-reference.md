# **[Pattern] Authentication Verification Reference Guide**

---
## **1. Overview**

The **Authentication Verification** pattern ensures secure access to systems, APIs, or services by validating user credentials (e.g., usernames, passwords, tokens) and authorizing their requests. This pattern enforces **confidentiality, integrity, and availability** by authenticating identities and verifying permissions before granting access.

This guide covers:
- **Key components** (auth tokens, tokens, challenge-response mechanisms).
- **Implementation best practices** (stateless vs. stateful auth, token storage, and expiry).
- **Common authentication methods** (OAuth 2.0, JWT, SAML, API keys).
- **Security considerations** (brute-force protection, token rotation, logging).

---

## **2. Key Concepts & Schema Reference**

### **Core Components**
| **Component**          | **Description**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Auth Token**         | A cryptographic identifier (e.g., JWT, session ID) used to prove valid access. |
| **Challenge-Response** | Server sends a challenge; client provides a response (e.g., CAPTCHA, one-time codes). |
| **Stateless vs. Stateful** | Stateless (JWT) stores data in tokens; stateful (sessions) relies on server-side storage. |
| **Refresh Token**      | Long-lived token used to obtain new access tokens without re-authenticating.   |
| **Multi-Factor (MFA)**  | Requires two+ credentials (e.g., password + TOTP).                              |

### **Schema Reference (Common Fields)**
| **Field**            | **Type**       | **Description**                                                                                     | **Example Value**                     |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `token`              | `string`      | Session/authentication token (e.g., JWT).                                                         | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...` |
| `expires_at`         | `timestamp`   | Token expiry time (UTC).                                                                         | `2024-12-31T23:59:59Z`                |
| `issuer`             | `string`      | Entity that issued the token (e.g., `auth-service`).                                               | `auth-service.example.com`            |
| `user_id`            | `UUID/Int`    | Unique identifier for the authenticated user.                                                      | `uuid:550e8400-e29b-41d4-a716-446655440000` |
| `scope`              | `array`       | Permissions granted (e.g., `["read:profile", "write:data"]`).                                       | `["read:profile", "write:data"]`      |
| `refresh_token`      | `string`      | Long-lived token for refreshing short-lived access tokens.                                          | `refresh_abc123xyz456`                |
| `challenge`          | `string`      | Dynamic value for challenge-response flows (e.g., TOTP code).                                       | `CAPTCHA-abc123`                     |

---

## **3. Implementation Details**

### **A. Authentication Flows**
| **Flow**               | **Description**                                                                                     | **Use Case**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| **OAuth 2.0**          | Uses tokens (access/refresh) with explicit scopes (e.g., `read`, `write`).                       | Third-party integrations (e.g., GitHub OAuth). |
| **JWT (JSON Web Token)** | Stateless tokens with headers (alg), payload (data), and signature.                                | API authentication.                   |
| **Session-Based**      | Server stores session IDs (e.g., cookies).                                                          | Traditional web apps.                 |
| **Two-Factor (MFA)**   | Requires 2+ factors (e.g., password + TOTP/SMS).                                                   | High-security applications.           |
| **API Keys**           | Simple key-value pairs for basic auth (e.g., `Authorization: Bearer API-KEY`).                     | Internal services.                    |

### **B. Token Management**
- **Expiry**: Set short expiry (e.g., 15–30 mins) for access tokens; use refresh tokens for longer sessions.
- **Storage**:
  - **Secure**: Use `HttpOnly`, `Secure` cookies or HTTP-only headers for sessions.
  - **Client-Side**: Store JWTs in `localStorage` (vulnerable to XSS) or `sessionStorage` (cleared on tab close).
- **Rotation**: Implement token rotation to mitigate leaks (e.g., rotate refresh tokens after use).

### **C. Security Hardening**
| **Measure**            | **Implementation**                                                                                  |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **Brute-Force Protection** | Rate-limit login attempts (e.g., 5 tries → lockout for 15 mins).                                  |
| **Token Binding**      | Bind tokens to device fingerprint (e.g., WebAuthn, HTTP `Public-Key-Credentials`).                  |
| **Logging**            | Audit failed logins, token revocations, and MFA attempts.                                            |
| **Token Revocation**   | Implement a revocation list (e.g., Redis) or short-lived tokens.                                    |

---

## **4. Query Examples**

### **A. OAuth 2.0 Token Request (POST)**
```http
POST /oauth/token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=user123&password=securePass&scope=read%20write
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_abc123xyz456",
  "scope": "read write"
}
```

### **B. JWT Validation (Header Check)**
```http
GET /api/user/profile HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Server-Side Validation (Pseudocode):**
```python
import jwt

def validate_token(token):
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return payload.get("user_id")  # Return user ID if valid
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
```

### **C. Challenge-Response (TOTP)**
1. **Server sends challenge:**
   ```http
   POST /auth/verify HTTP/1.1
   Host: auth.example.com
   Content-Type: application/json

   {"challenge": "CAPTCHA-abc123", "user_id": "user123"}
   ```
2. **Client responds with valid TOTP:**
   ```json
   {"response": "765431", "user_id": "user123"}
   ```

---

## **5. Error Handling & Status Codes**
| **Code** | **Error**               | **Description**                                                                                     |
|----------|-------------------------|-----------------------------------------------------------------------------------------------------|
| `401`    | `Unauthorized`          | Missing/invalid auth token.                                                                    |
| `403`    | `Forbidden`             | Valid token but insufficient scope (e.g., `write:data` missing).                                 |
| `429`    | `Too Many Requests`     | Rate-limit exceeded (e.g., 5 failed login attempts).                                                |
| `400`    | `Invalid Token`         | Malformed token (e.g., expired, tampered).                                                        |
| `500`    | `Auth Service Unavailable` | Backend auth failure (e.g., database error).                                                    |

---

## **6. Related Patterns**
1. **[Authorization]** – Validates user permissions after authentication.
2. **[Rate Limiting]** – Protects against brute-force attacks.
3. **[Session Management]** – Handles server-side session tokens.
4. **[Single Sign-On (SSO)]** – Federated authentication (e.g., SAML, OpenID Connect).
5. **[API Gateway]** – Centralized auth enforcement for microservices.

---
## **7. Best Practices**
- **Use HTTPS**: Never transmit tokens over unencrypted channels.
- **Minimize Token Scope**: Grant only necessary permissions.
- **Regular Audits**: Rotate secrets (e.g., JWT signing keys) periodically.
- **Client-Side Security**: Sanitize token handling to prevent XSS/CSRF.

---
**Last Updated:** `[Insert Date]`
**Version:** `1.2`