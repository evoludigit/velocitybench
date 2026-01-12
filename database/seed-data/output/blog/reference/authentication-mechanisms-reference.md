# **[Pattern] Authentication Mechanisms (OAuth, JWT, Session) Reference Guide**

---

## **Overview**
Authentication is the cornerstone of secure system access, ensuring that users and services can verify their identities before granting permissions. This reference guide outlines three primary **Authentication Mechanisms**:
**OAuth 2.0** (delegated authorization), **JSON Web Tokens (JWT)** (stateless token-based auth), and **Session-Based Authentication** (server-state tracking).
Each mechanism serves distinct use cases (e.g., third-party integrations, single-sign-on, or internal app auth). This guide provides key concepts, implementation choices, security considerations, and workflow examples for each approach, aiding architects, developers, and security teams in selecting and integrating the right solution.

---

## **1. Authentication Mechanisms: Implementation Details**

### **1.1 OAuth 2.0**
OAuth 2.0 is an **authorization framework** enabling third-party apps to delegate user authentication via trusted third parties (e.g., Google, Facebook). It delegates access tokens rather than passwords, reducing the risk of credential exposure.

#### **Key Components**
| **Component**       | **Description**                                                                 |
|---------------------|---------------------------------------------------------------------------------|
| **Resource Owner**  | End-user granting access to their data.                                          |
| **Client**          | Application requesting access on behalf of the user (e.g., a mobile app).       |
| **Authorization Server** | Issues access tokens (e.g., OAuth provider like Auth0, Okta).                |
| **Resource Server** | Hosts protected resources (e.g., API endpoints).                                |
| **Access Token**    | Short-lived credential for accessing resource server APIs.                       |
| **Refresh Token**   | Long-lived token to obtain new access tokens without re-authenticating.         |
| **Scopes**          | Defines permissions (e.g., `read:profile`, `write:photos`).                     |

#### **Common Grant Types**
| **Grant Type**      | **Use Case**                                                                     | **Security Considerations**                          |
|---------------------|---------------------------------------------------------------------------------|------------------------------------------------------|
| **Authorization Code** | Web apps (e.g., redirect to OAuth provider for user login).                     | Requires HTTPS; code flows securely via redirect URI. |
| **Implicit**        | Legacy single-page apps (not recommended; deprecated in OAuth 2.1).             | No backend code storage; vulnerable to CSRF.         |
| **Client Credentials** | Machine-to-machine auth (e.g., backend services).                            | No user involved; limited to API-to-API scopes.      |
| **Password**        | Direct username/password delegation (rarely used; may violate OAuth’s intent). | High risk; avoid for sensitive user credentials.     |
| **PKCE (Proof Key for Code Exchange)** | Public clients (e.g., mobile apps) to prevent code interception.           | Adds security layer to Authorization Code flows.     |

---

### **1.2 JSON Web Tokens (JWT)**
JWT is a **stateless, JSON-based token format** for securely transmitting claims between parties. It comprises three parts: **Header**, **Payload**, and **Signature**.

#### **Structure**
| **Part**      | **Description**                                                                 | **Example**                                      |
|---------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Header**    | Contains the `alg` (algorithm) and `typ` (token type).                          | `{"alg":"HS256","typ":"JWT"}`                      |
| **Payload**   | Claims (user data, metadata) stored as a key-value map.                          | `{ "sub": "12345", "name": "Alice", "iat": 123456 }` |
| **Signature** | HMAC/SHA or RSA signature to verify integrity and authenticity.                  | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`          |

#### **JWT Claims**
| **Claim Type** | **Description**                                                                 | **Example**                                      |
|----------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Registered** | Standard claims (e.g., `iss`, `exp`, `sub`).                                      | `"sub": "user123", "iss": "auth.example.com"`     |
| **Public**     | Custom claims published by the issuer.                                            | `"role": "admin"`                                |
| **Private**    | Custom claims between the issuer and verifier.                                    | `"pref_language": "fr"`                          |

#### **JWT Claims Validation Rules**
1. **Issuer (`iss`)**: Must match the expected authorization server.
2. **Audience (`aud`)**: Token must be for the intended recipient.
3. **Expiration (`exp`)**: Token must not be expired.
4. **Not Before (`nbf`)**: Token must not be active before this time.
5. **Signature**: Must match the expected algorithm (e.g., HS256, RS256).

---

### **1.3 Session-Based Authentication**
Session-based authentication relies on **server-side state management** to track logged-in users via a **session ID** (e.g., cookie).

#### **Flow**
1. User logs in → Server generates a session ID → Stores session data (e.g., user ID, permissions) on the server.
2. Client receives a session cookie → Server validates the cookie for subsequent requests.
3. Session expires after inactivity or max duration.

#### **Session Storage Options**
| **Option**          | **Pros**                                  | **Cons**                                      |
|---------------------|-------------------------------------------|-----------------------------------------------|
| **In-Memory**       | Fast access; easy to invalidate.          | Lose sessions on server restart (use Redis).   |
| **Database (SQL)**  | Persistent; scalable.                     | Latency overhead.                             |
| **Redis**           | High performance; distributed support.    | Additional dependency.                        |

#### **Security Considerations**
- **Secure Cookies**: Set `HttpOnly`, `Secure`, and `SameSite` attributes.
- **CSRF Protection**: Use tokens (CSRF tokens) in forms.
- **Session Fixation**: Regenerate session IDs after login.

---

## **2. Comparison Table: OAuth vs. JWT vs. Session**

| **Feature**               | **OAuth 2.0**                          | **JWT**                                      | **Session-Based**               |
|---------------------------|----------------------------------------|---------------------------------------------|---------------------------------|
| **State**                 | Stateless (tokens)                     | Stateless (tokens)                          | Stateful (server-side)          |
| **Use Case**              | Third-party auth (e.g., login with Google). | REST APIs, microservices.                | Traditional web apps.           |
| **Token Storage**         | Client-side (e.g., `localStorage`)     | Client-side (e.g., `localStorage`, headers) | Server-side (cookies).          |
| **Token Size**            | Typically small (~1KB)                 | Small (~2.5KB max)                          | No token (uses server-side ID). |
| **Refresh Mechanism**     | Refresh tokens                          | Short-lived JWT + refresh tokens (JWT-RT).    | Session regeneration.           |
| **Scalability**           | High (no server storage)               | High (stateless)                            | Medium (server-side state).     |
| **Security**              | High (scopes, PKCE)                    | High (cryptographic signing)                | Medium (cookies vulnerable).    |

---

## **3. Schema Reference**

### **3.1 OAuth 2.0 API Schema**
```http
# OAuth Token Endpoint (POST)
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE&
redirect_uri=https://client.example.com/callback&
client_id=CLIENT_ID&
client_secret=CLIENT_SECRET
```

| **Parameter**  | **Type**   | **Required?** | **Description**                              |
|----------------|------------|---------------|----------------------------------------------|
| `grant_type`   | string     | Yes           | OAuth flow type (e.g., `authorization_code`).|
| `code`         | string     | (Varies)      | Authorization code (Authorization Code flow).|
| `redirect_uri` | URL        | (Varies)      | Registered URI for OAuth callback.           |
| `client_id`    | string     | Yes           | OAuth client ID.                             |
| `client_secret`| string     | (Depends)     | Client secret (not required for PKCE).       |

**Response (Success):**
```json
{
  "access_token": "ACCESS_TOKEN",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN"
}
```

---

### **3.2 JWT Schema**
| **Claim**      | **Type**   | **Required** | **Description**                              |
|----------------|------------|--------------|----------------------------------------------|
| `iss`          | string     | No           | Issuer (e.g., `"auth.example.com"`).        |
| `sub`          | string     | Recommended  | Subject (user ID).                           |
| `aud`          | string     | Recommended  | Audience (api endpoint).                     |
| `exp`          | integer    | Yes          | Expiration time (UNIX timestamp).            |
| `iat`          | integer    | Recommended  | Issued at (UNIX timestamp).                  |
| `nbf`          | integer    | Optional     | Not before (token not valid before this time).|
| `jti`          | string     | Optional     | JWT ID (unique identifier).                  |

**Encoded JWT Example:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

---

### **3.3 Session Schema**
| **Attribute**    | **Type**   | **Description**                              |
|------------------|------------|----------------------------------------------|
| `session_id`     | string     | Unique identifier (e.g., UUID).             |
| `user_id`        | string     | User’s ID (e.g., `"user123"`).               |
| `roles`          | array      | User permissions (e.g., `["admin", "user"]`).|
| `created_at`     | timestamp  | Session creation time.                       |
| `expires_at`     | timestamp  | Expiration time.                             |

**Example Session Cookie:**
```
Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=3600
```

---

## **4. Query Examples**

### **4.1 OAuth: Authorize Endpoint (Authorization Code Flow)**
```http
# Redirect user to OAuth provider
GET https://auth-provider.com/oauth/authorize?
  response_type=code&
  client_id=CLIENT_ID&
  redirect_uri=https://client.example.com/callback&
  scope=read:profile%20write:photos&
  state=RANDOM_STATE_STRING
```

**Callback Response (Success):**
```
GET https://client.example.com/callback?
  code=AUTH_CODE&
  state=RANDOM_STATE_STRING
```

---

### **4.2 JWT: API Request with Bearer Token**
```http
GET /api/user/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### **4.3 Session: Login Request**
```http
POST /api/login
Content-Type: application/json

{
  "username": "alice",
  "password": "securepass123"
}
```

**Response (Success):**
```http
HTTP/1.1 200 OK
Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=Lax
```

---

## **5. Security Best Practices**

| **Mechanism** | **Best Practices**                                                                 |
|----------------|-----------------------------------------------------------------------------------|
| **OAuth**      | - Use PKCE for public clients.                                                   |
|                | - Rotate `client_secret` regularly.                                             |
|                | - Validate `state` parameter to prevent CSRF.                                    |
|                | - Limit token scopes to least privilege.                                         |
| **JWT**        | - Use symmetric (HS256) or asymmetric (RS256/ES256) signing.                     |
|                | - Store signing keys securely (HSM or sealed storage).                           |
|                | - Set short `exp` times (e.g., 15-30 minutes) and use refresh tokens.           |
|                | - Avoid storing sensitive data in JWT payloads.                                  |
| **Session**    | - Use `HttpOnly`, `Secure`, and `SameSite` cookies.                              |
|                | - Regenerate session IDs after login.                                            |
|                | - Invalidate sessions on logout.                                                 |
|                | - Implement rate limiting for login attempts.                                    |

---

## **6. Error Handling**

### **6.1 OAuth Errors**
| **Error Code** | **Description**                          | **HTTP Status** |
|----------------|------------------------------------------|-----------------|
| `invalid_request` | Invalid parameters (e.g., missing `grant_type`). | 400             |
| `unauthorized_client` | Client not authenticated.             | 401             |
| `access_denied`   | User denied access.                      | 403             |
| `unsupported_grant_type` | Unsupported OAuth flow.            | 400             |

**Example Response:**
```json
{
  "error": "access_denied",
  "error_description": "The user denied the request."
}
```

---

### **6.2 JWT Errors**
| **Error**               | **Description**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|
| `invalid_token`         | Token is malformed or invalid signature.                                       |
| `expired_token`         | Token expired (`exp` claim).                                                   |
| `invalid_issuer`        | `iss` claim does not match expected issuer.                                    |
| `missing_audience`      | No matching `aud` claim for recipient.                                         |

---

## **7. Related Patterns**
1. **[Authorization Patterns (RBAC, ABAC)]** – Extend authentication with permission systems.
2. **[API Gateway Patterns]** – Use gateways to enforce OAuth/JWT validation centrally.
3. **[Stateless vs. Stateful Services]** – Consider trade-offs between session and token-based auth.
4. **[Multi-Factor Authentication (MFA)]** – Add 2FA (e.g., TOTP) to enhance security.
5. **[Identity Federation]** – Integrate with SAML, OpenID Connect, or LDAP for cross-domain auth.

---
**See Also:**
- [RFC 6749 (OAuth 2.0)](https://tools.ietf.org/html/rfc6749)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)