# **[Pattern] Authentication Troubleshooting - Reference Guide**

---

## **Overview**
Authentication failures can disrupt user access, API integrations, and system reliability. This guide provides a structured approach to diagnosing and resolving authentication issues across single-sign-on (SSO), OAuth2, JWT, and traditional username/password systems. Debugging follows a **layered methodology**—from client-side validation to server-side configuration—ensuring systematic resolution. Common pitfalls include expired tokens, misconfigured endpoints, or incorrect credentials, which this pattern addresses with **step-by-step diagnostics**, tools, and validation techniques.

---

## **Key Concepts & Implementation Details**
### **1. Authentication Troubleshooting Layers**
Troubleshooting follows a **bottom-up approach**:
- **Client Layer**: Check UI/forms, network requests, and SDKs.
- **Transport Layer**: Validate redirects, headers, and payload integrity.
- **Backend Layer**: Inspect middleware, database queries, and session handling.
- **Identity Provider Layer**: Verify IDP logs, token issuance, and revocation policies.

### **2. Common Failure Scenarios**
| Scenario               | Cause                          | Resolution Path                          |
|------------------------|-------------------------------|------------------------------------------|
| **401 Unauthorized**   | Expired token, invalid scope   | Refresh token/grant or check permissions |
| **403 Forbidden**      | Role-based access denied       | Validate user roles/claims               |
| **500 Server Error**   | Backend misconfiguration        | Check server logs, retry limits          |
| **Redirect Loop**      | Malformed state/CSRF token     | Validate `state` parameter integrity     |
| **Silent Failures**    | Missing `onError` handlers     | Log client-side exceptions               |

### **3. Essential Tools**
| Tool/Technique       | Purpose                                  | Example Command/Usage          |
|----------------------|------------------------------------------|---------------------------------|
| **Postman/cURL**     | Test API endpoints manually              | `curl -X POST -H "Authorization: Bearer <token>" ...` |
| **Wireshark**        | Inspect HTTP/S traffic                   | Capture `POST /token` requests |
| **JWT Decoder**      | Validate token signature/claims          | [jwt.io](https://jwt.io)        |
| **OpenID Connect**   | Debug OIDC flows (e.g., `id_token_hint`) | Check `.well-known/openid-configuration` |
| **Strace/Process Monitor** | System-level debugging      | `strace -f node /path/to/auth-server` |

### **4. Token-Lifetime Management**
| Token Type       | Lifetime Default | Recommended Reset On          |
|------------------|------------------|--------------------------------|
| **Access Token** | 1h–24h           | Login, role change, or session revocation |
| **Refresh Token**| 7–30 days        | Compromise, explicit revocation |
| **ID Token**     | Non-expiring*    | Re-authentication required     |

*_OIDC ID tokens may include `exp` claims; check spec for compliance._*

---
## **Schema Reference**

### **1. Authentication Request Payloads**
| Field               | Type      | Required | Description                                                                 |
|---------------------|-----------|----------|-----------------------------------------------------------------------------|
| **username/email**  | string    | Yes      | User’s identity credential                                                 |
| **password**        | string    | Yes      | Encrypted client-side (never logged)                                       |
| **grant_type**      | string    | Yes      | OAuth2 flow type (`password`, `refresh_token`, `client_credentials`)       |
| **client_id**       | string    | Yes      | Registered app ID (OAuth2)                                                  |
| **client_secret**   | string    | Conditional | Confidential client apps only (OAuth2)                                    |
| **scope**           | string    | Optional | Space-separated permissions (`openid profile email`)                        |
| **redirect_uri**    | URL       | Conditional | Required for implicit/authorization flows                                  |
| **state**           | string    | Optional | CSRF protection (must match reply)                                         |

---

### **2. JWT Claim Requirements**
| Claim          | Type    | Description                                                                 |
|----------------|---------|-----------------------------------------------------------------------------|
| `iss`          | string  | Issuer URI (e.g., `https://auth.example.com`)                              |
| `sub`          | string  | Subject (user ID or email)                                                  |
| `aud`          | string  | Audience (client ID or app URI)                                             |
| `exp`          | number  | Unix timestamp (seconds) for expiration                                     |
| `nbf`          | number  | Not before (prevents premature use)                                         |
| `iat`          | number  | Issue at (timestamp validation)                                             |
| `auth_time`    | number  | Last authentication timestamp (OIDC)                                        |

---
## **Query Examples**

### **1. Diagnosing OAuth2 Token Exchange**
**Request (cURL):**
```bash
curl -X POST \
  https://auth.example.com/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=user123&password=PASSWORD&client_id=APP_ID&client_secret=SECRET&scope=read write"
```

**Expected Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN"
}
```

**Failure Response (401 Unauthorized):**
```json
{
  "error": "invalid_grant",
  "error_description": "Incorrect username or password"
}
```

---
### **2. Validating JWT Claims**
```bash
# Decode and verify JWT (without secret to inspect claims)
echo "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." | base64 -d | jq .
```
**Output:**
```json
{
  "iss": "https://auth.example.com",
  "sub": "user@example.com",
  "exp": 1712345678,
  "nbf": 1712340000
}
```

---
### **3. Checking Session Revocation**
**Request (cURL):**
```bash
curl -X POST \
  https://auth.example.com/logout \
  -H "Authorization: Bearer ACCESS_TOKEN"
```
**Expected Response (200 OK):**
```json
{
  "revoked": ["eyJhbGciOiJSUzI1NiIs..."]
}
```

---
## **Validation Techniques**

### **1. Cross-Origin Resource Sharing (CORS) Checks**
- **Verify Headers**:
  ```bash
  curl -I https://auth.example.com/token \
    -H "Origin: https://client.app"
  ```
  **Expected**:
  `Access-Control-Allow-Origin: https://client.app`

### **2. Rate Limiting Diagnostics**
- **Test Throttling**:
  ```bash
  while true; do curl -X POST -d "username=test" https://auth.example.com/login; done
  ```
  **Expected Failure**:
  `HTTP 429 Too Many Requests`

---
## **Related Patterns**
| Pattern Name                     | Purpose                                                                 |
|-----------------------------------|-------------------------------------------------------------------------|
| **[Token Rotation]**              | Securely refresh tokens without user intervention.                      |
| **[Multi-Factor Authentication]** | Enforce 2FA (TOTP, SMS, or hardware keys) for sensitive operations.    |
| **[Session Hijacking Protection]** | Mitigate CSRF, XSS, and replay attacks via `SameSite` cookies.         |
| **[Fine-Grained Permissions]**    | Map JWT claims to role-based access (e.g., `admin:read/write`).         |
| **[Audit Logging]**               | Track authentication events for compliance (e.g., GDPR).                |

---
## **Further Reading**
- **[OAuth 2.0 Security Best Current Practices](https://datatracker.ietf.org/doc/html/rfc8252)**
- **[JWT Best Practices](https://auth0.com/blog/critical-jwt-security-best-practices/)**
- **[OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)**