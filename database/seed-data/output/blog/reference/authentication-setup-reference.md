# **[Pattern] Authentication Setup – Reference Guide**

---

## **Overview**
The **Authentication Setup** pattern defines a structured approach to implementing user authentication in applications. It ensures secure identity verification while allowing flexibility for different use cases—from simple local sign-in to multi-factor authentication (MFA) and third-party integrations.

This guide covers:
- Core components (e.g., authentication flows, tokens, and session management).
- Key implementation details (security best practices, token expiration, and error handling).
- A standardized schema for authentication configurations.
- Common query examples (API calls, JWT handling).
- Related patterns like **Authorization** and **Session Management** for extended functionality.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authentication Flow**   | Defines how users prove identity (e.g., username/password, OAuth 2.0, biometrics).                                                                                                                                                                                  |
| **JWT (JSON Web Tokens)** | Stateless tokens containing claims (e.g., user ID, expiry) for secure API communication.                                                                                                                                                                       |
| **Session Management**   | Server-side tracking of authenticated users (e.g., cookies, session IDs).                                                                                                                                                                                   |
| **Multi-Factor Auth (MFA)**| Additional verification layers (e.g., SMS codes, TOTP) for higher security.                                                                                                                                                                                 |
| **OAuth 2.0**             | Delegated authentication via third-party providers (e.g., Google, Facebook).                                                                                                                                                                               |
| **Token Expiry**          | Time-limited tokens to mitigate unauthorized access risks (default: 1 hour; configurable).                                                                                                                                                                  |

---

## **Schema Reference**
Below is the standardized schema for defining authentication configurations.

| **Field**               | **Type**      | **Description**                                                                                                                                                                                                                                                                               | **Required?** | **Example Value**                          |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|---------------------------------------------|
| `auth_method`           | `string`      | Primary authentication method (e.g., `local`, `oauth2`, `mfa`).                                                                                                                                                                                                                     | Yes            | `"local"`                                  |
| `realm`                 | `string`      | Identity provider realm (e.g., `internal`, `social`).                                                                                                                                                                                                                               | Conditional*   | `"social"`                                 |
| `token_ttl`             | `integer`     | Token validity in seconds (default: 3600).                                                                                                                                                                                                                                               | No             | `7200` (2 hours)                           |
| `refresh_token`         | `boolean`     | Enable refresh tokens for long-lived sessions.                                                                                                                                                                                                                                             | No             | `true`                                     |
| `salt_rounds`           | `integer`     | Password hashing rounds (default: 10).                                                                                                                                                                                                                                       | No             | `12`                                        |
| `mfa_required`          | `boolean`     | Enforce MFA for all users.                                                                                                                                                                                                                                                     | No             | `false`                                    |
| `oauth_providers`       | `array`       | List of OAuth 2.0 providers (e.g., `google`, `github`).                                                                                                                                                                                                                                   | Conditional*   | `["google", "facebook"]`                    |
| `session_cookie`        | `object`      | Cookie settings for session management.                                                                                                                                                                                                                                           | No             | `{ "secure": true, "httpOnly": true }`      |
| `error_handling`        | `object`      | Custom error responses (e.g., `invalid_credentials`, `token_expired`).                                                                                                                                                                                                             | No             | `{ "invalid_credentials": { "message": "Login failed" } }` |

*Conditional*: Required if `auth_method` is `oauth2` or `mfa`.

---

## **Implementation Details**

### **1. Authentication Flows**
| **Flow**               | **Description**                                                                                                                                                                                                                                                   | **Use Case**                          |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| **Local Auth**         | Username/password + hashed storage (e.g., bcrypt).                                                                                                                                                                                                          | Internal applications.                 |
| **OAuth 2.0**          | Redirects to provider (e.g., Google) for authentication.                                                                                                                                                                                                       | Social logins.                         |
| **MFA**                | Additional verification step (e.g., TOTP or SMS).                                                                                                                                                                                                         | High-security environments.            |
| **JWT Flow**           | Stateless tokens with refresh tokens for scalability.                                                                                                                                                                                                  | APIs and microservices.                |
| **Session-Based**      | Server-side sessions (cookies) for stateful apps.                                                                                                                                                                                                        | Traditional web apps.                  |

### **2. Security Best Practices**
- **Password Storage**: Always hash passwords (use `bcrypt` with `salt_rounds ≥ 10`).
- **Token Security**:
  - Use **short-lived tokens** (TTL ≤ 2 hours).
  - Store refresh tokens securely (encrypted in DB).
- **Rate Limiting**: Prevent brute-force attacks (e.g., 5 attempts/10 mins).
- **HTTPS**: Enforce secure connections for all auth endpoints.

### **3. Token Handling**
- **JWT Structure**:
  ```json
  {
    "header": { "alg": "HS256", "typ": "JWT" },
    "payload": {
      "sub": "user123",
      "iat": 1625097600,
      "exp": 1625183600,
      "auth_method": "local"
    },
    "signature": "..."
  }
  ```
- **Refresh Tokens**: Issued alongside JWTs; valid for **30 days** (configurable).

---

## **Query Examples**

### **1. Local Authentication (API)**
**Endpoint**: `POST /api/auth/local`
**Request Body**:
```json
{
  "username": "user123",
  "password": "securePass123",
  "device_id": "xyz123"  // Optional for tracking
}
```
**Success Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_xyz456",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Error Response (Invalid Credentials)**:
```json
{
  "error": "invalid_credentials",
  "message": "Username or password incorrect"
}
```

---

### **2. OAuth 2.0 Flow (Authorization Code)**
**Step 1: Redirect to Provider**
```http
GET /oauth/authorize?client_id=xyz123&redirect_uri=https://app.com/callback
```
**Step 2: Receive Code**
```http
GET https://app.com/callback?code=AUTH_CODE_123
```
**Step 3: Exchange Code for Tokens (API)**
```json
POST /api/auth/oauth2/token
{
  "code": "AUTH_CODE_123",
  "client_id": "xyz123",
  "client_secret": "secret456",
  "grant_type": "authorization_code"
}
```
**Response**:
```json
{
  "access_token": "oauth_eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

### **3. JWT Validation (API Gateway)**
**Header**:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
**Validation Logic (Pseudocode)**:
```javascript
function validateJWT(token) {
  if (!token || !isValidSignature(token)) return { error: "invalid_token" };
  const payload = decodeToken(token);
  if (payload.exp < Date.now() / 1000) return { error: "token_expired" };
  return { userId: payload.sub, authMethod: payload.auth_method };
}
```

---

### **4. Refresh Token Request**
**Endpoint**: `POST /api/auth/refresh`
**Request Body**:
```json
{
  "refresh_token": "refresh_xyz456"
}
```
**Response**:
```json
{
  "access_token": "new_jwt_eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "refresh_new789",  // Rotated token
  "expires_in": 3600
}
```

---

## **Error Handling**
| **Error Code**          | **HTTP Status** | **Description**                                                                 |
|-------------------------|-----------------|---------------------------------------------------------------------------------|
| `invalid_credentials`   | 401             | Username/password or OAuth code invalid.                                        |
| `token_expired`         | 401             | JWT or refresh token expired.                                                   |
| `mfa_required`          | 401             | User must complete MFA (e.g., TOTP code).                                       |
| `rate_limit_exceeded`   | 429             | Too many attempts; retry after [X] seconds.                                      |
| `unsupported_provider`  | 400             | OAuth provider not configured.                                                  |
| `session_expired`       | 401             | Server-side session invalidated.                                                |

---

## **Related Patterns**
1. **[Authorization]** – Extend authentication with role-based access control (RBAC).
2. **[Session Management]** – Handle server-side sessions and invalidation.
3. **[Token Revocation]** – Blacklist compromised tokens (e.g., after logout).
4. **[Password Reset]** – Secure flow for resetting forgotten passwords.
5. **[Two-Factor Authentication (TFA)]** – Enhance security with time-based codes.

---
**Next Steps**:
- [ ] Integrate with your preferred auth provider (e.g., Auth0, Firebase).
- [ ] Customize token TTL and error messages in the schema.
- [ ] Test edge cases (e.g., token leakage, concurrent logins).