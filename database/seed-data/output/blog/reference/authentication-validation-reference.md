# **[Pattern] Authentication Validation Reference Guide**

---

## **Overview**
The **Authentication Validation (AV) pattern** ensures secure access to systems, APIs, or services by verifying user credentials or tokens before granting authorization. This pattern mitigates unauthorized access risks while maintaining usability. It typically involves:
- **Credential validation** (username/password, MFA, or biometric checks).
- **Token validation** (JWT, OAuth, or session tokens).
- **Rate limiting** to prevent brute-force attacks.
- **Session management** (expiration, revocation, and refresh mechanisms).

AV is foundational in **authentication systems**, complements **Authorization Validation**, and integrates with **API Gateway**, **Identity Provider (IdP)**, and **Single Sign-On (SSO)** patterns.

---

## **Key Concepts**
| Concept               | Definition                                                                                     | Example Use Case                                      |
|-----------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **Authentication**    | Process of verifying a user’s identity via credentials (e.g., password, token).             | Logging into a web app with an email + password.      |
| **Validation**        | Checking credentials against stored hashes, databases, or external IdPs.                   | Comparing a JWT’s `exp` claim to the current timestamp.|
| **Token-Based Auth**  | Using tokens (JWT, OAuth) instead of repeated credentials.                                   | Mobile app accessing a backend via a short-lived JWT. |
| **Multi-Factor Auth** | Requiring two+ verification methods (e.g., password + SMS code).                            | Bank login requiring a PIN and fingerprint.           |
| **Rate Limiting**     | Restricting login attempts to prevent brute-force attacks.                                   | Blocking after 5 failed login attempts.                |
| **Session Management**| Controlling active sessions (creation, expiration, revocation).                             | Logging out a user from all devices.                  |
| **Idle Timeout**      | Ending sessions after inactivity.                                                           | Auto-logout after 30 minutes of inactivity.           |

---

## **Implementation Details**

### **1. Input Schema**
Inputs to the **Authentication Validation** pattern include:
- **User-provided data**:
  - `username`/`email` (string)
  - `password` (string, hashed on storage)
  - `token` (string, for token-based auth)
  - `device_id` (string, for session tracking)
  - `ip_address` (string, for anomaly detection)
- **Contextual data**:
  - `request_timestamp` (ISO 8601)
  - `user_agent` (string)

**Schema Reference Table**
| Field                | Type     | Required | Description                                                                 |
|----------------------|----------|----------|-----------------------------------------------------------------------------|
| `username`           | `string` | No*      | User identifier (email or username).                                         |
| `password`           | `string` | Yes      | Plaintext password (never stored; hashed during validation).                 |
| `token`              | `string` | Yes      | JWT/OAuth token for stateless validation.                                    |
| `refresh_token`      | `string` | No       | Used to generate new access tokens.                                          |
| `device_id`          | `string` | No       | Unique ID for device-based session management.                                |
| `ip_address`         | `string` | No       | Client IP for fraud detection (e.g., geoblocking).                          |
| `mfa_code`           | `string` | No       | TOTP/SMS code for MFA.                                                        |
| `session_id`         | `string` | No       | Existing session token for session continuation.                             |
| `request_timestamp`  | `ISO8601`| Yes      | Timestamp to detect replay attacks or clock skew.                            |
| `user_agent`         | `string` | No       | Browser/client info for session binding.                                      |

*Optional if using token-based auth (e.g., POST `/login` with `token`).

---

### **2. Output Schema**
Validation results include:
- **Success Response**:
  ```json
  {
    "status": "success",
    "user_id": "uuid4",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string",
    "expires_in": 3600,
    "session_id": "session_token",
    "metadata": {
      "device_name": "iPhone 15",
      "ip_address": "192.168.1.1",
      "last_seen": "2024-05-20T14:30:00Z"
    }
  }
  ```
- **Failure Response**:
  ```json
  {
    "status": "error",
    "code": "invalid_credentials" | "token_expired" | "mfa_required",
    "message": "Invalid password or username.",
    "retry_after": 60  // for rate limiting
  }
  ```

**Error Codes Table**
| Code                  | Description                                                                                     | Example Response Message                      |
|-----------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------|
| `invalid_credentials` | Username/password or token is incorrect.                                                       | "Email or password incorrect."               |
| `token_expired`       | JWT/OAuth token has expired.                                                                   | "Session expired. Please re-authenticate."     |
| `mfa_required`        | Multi-factor authentication needed.                                                           | "Verification code required."                |
| `rate_limited`        | Too many attempts. Retry after `X` seconds.                                                    | "Too many attempts. Try again in 300s."       |
| `lockout`             | Account temporarily locked due to repeated failures.                                            | "Account locked. Contact support."            |
| `invalid_token`       | Malformed or invalid token (e.g., missing signature).                                         | "Invalid authentication token."               |
| `unverified_email`    | User email not confirmed.                                                                     | "Please verify your email first."             |

---

### **3. Validation Workflow**
1. **Input Sanitization**
   - Check for SQL injection, XSS, or malformed payloads.
   - Example: Strip whitespace from `username`/`password`.

2. **Credential/Token Check**
   - **Password Auth**:
     - Hash input password (e.g., `bcrypt`) and compare with stored hash.
     - Example:
       ```python
       import bcrypt
       hashed_input = bcrypt.hashpw(password.encode(), salt)
       if bcrypt.checkpw(hashed_input, stored_hash):
           proceed
       ```
   - **Token Auth**:
     - Decode JWT, verify signature, and validate claims (`exp`, `iss`, `aud`).
     - Example (Python `PyJWT`):
       ```python
       from jwt import decode, InvalidTokenError, ExpiredSignatureError
       try:
           token_data = decode(token, SECRET_KEY, algorithms=["HS256"])
           if token_data["exp"] < datetime.now().timestamp():
               raise ExpiredSignatureError
       except (InvalidTokenError, ExpiredSignatureError):
           return {"status": "error", "code": "token_expired"}
       ```

3. **Rate Limiting**
   - Use a **fixed-window counter** or **sliding window log**:
     - Track failed attempts per `user_id`/`ip_address`.
     - Block after `N` attempts (e.g., 5) or enforce a cooldown.
   - Example (Redis + Node.js):
     ```javascript
     const rateLimit = async (userId) => {
       const key = `rate_limit:${userId}`;
       const attempts = await redis.incr(key);
       if (attempts > 5) {
         await redis.expire(key, 60); // Lock for 1 minute
         return { status: "error", code: "rate_limited" };
       }
     };
     ```

4. **MFA (Optional)**
   - Generate a TOTP code (e.g., using `pyotp` or `google-auth`).
   - Example:
     ```python
     import pyotp
     totp = pyotp.TOTP("base32secret")
     user_code = totp.now()  # User enters this
     if user_code == input_code:
         proceed
     ```

5. **Session Creation**
   - Generate a **session ID** (e.g., UUID) and store it server-side (Redis, DB).
   - Set `expires_in` (e.g., 1 hour) and `refresh_token` (long-lived, revocable).
   - Example (Redis):
     ```python
     import uuid
     session_id = str(uuid.uuid4())
     redis.setex(f"session:{session_id}", 3600, user_id)
     ```

---

### **4. Security Considerations**
| Risk                     | Mitigation Strategy                                                                 |
|--------------------------|------------------------------------------------------------------------------------|
| **Brute Force**          | Rate limiting, account lockout after `N` attempts.                                 |
| **Replay Attacks**       | Issue short-lived tokens; validate `request_timestamp`.                          |
| **Token Leakage**        | Use short expiry times (e.g., 15–30 minutes) + refresh tokens.                    |
| **Credential Stuffing**  | Enforce strong passwords + breach detection (e.g., [Have I Been Pwned API](https://haveibeenpwned.com/API)). |
| **Session Hijacking**    | Bind sessions to `ip_address`/`device_id`; use HttpOnly cookies.                  |
| **Man-in-the-Middle**    | Enforce HTTPS; use PKCE for OAuth flows.                                          |

---

## **Query Examples**

### **1. POST /api/auth/login (Username/Password)**
**Request**
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "SecureP@ssw0rd",
  "device_id": "abc123"
}
```

**Success Response (200 OK)**
```json
{
  "status": "success",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_abc123",
  "expires_in": 1800,
  "session_id": "session_xyz789",
  "metadata": {
    "ip_address": "192.168.1.1",
    "device_name": "MacBook Pro"
  }
}
```

**Failure Response (401 Unauthorized)**
```json
{
  "status": "error",
  "code": "invalid_credentials",
  "message": "Invalid email or password."
}
```

---

### **2. POST /api/auth/refresh (Refresh Token)**
**Request**
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_abc123"
}
```

**Success Response (200 OK)**
```json
{
  "status": "success",
  "access_token": "new_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

**Failure Response (401 Unauthorized)**
```json
{
  "status": "error",
  "code": "invalid_token",
  "message": "Refresh token expired or invalid."
}
```

---

### **3. POST /api/auth/mfa (MFA Challenge)**
**Request**
```http
POST /api/auth/mfa
Content-Type: application/json

{
  "username": "user@example.com",
  "mfa_code": "123456"
}
```

**Success Response (200 OK)**
```json
{
  "status": "success",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

**Failure Response (401 Unauthorized)**
```json
{
  "status": "error",
  "code": "mfa_failed",
  "message": "Invalid verification code."
}
```

---

### **4. POST /api/auth/logout (Session Revocation)**
**Request**
```http
POST /api/auth/logout
Content-Type: application/json

{
  "session_id": "session_xyz789"
}
```

**Response (204 No Content)**
```json
{}
```

---

## **Related Patterns**
| Pattern                          | Description                                                                                     | Integration Point                          |
|----------------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------|
| **[Authorization Validation]**   | Defines permissions after authentication (e.g., role-based access control).                     | Post-AV (e.g., protect `/admin` routes).   |
| **[API Gateway]**                | Routes authenticated requests; validates tokens before forwarding.                              | AV layer in Gateway (e.g., Kong, AWS API GW). |
| **[Identity Provider (IdP)]**    | External auth service (e.g., Google, Okta) for federated login.                                | Delegated AV (e.g., OAuth/OIDC flows).      |
| **[Single Sign-On (SSO)]**       | Centralized authentication across multiple services.                                           | AV + IdP (e.g., SAML, OAuth).              |
| **[Token Rotation]**              | Automatically refresh tokens before expiry to reduce risk.                                    | Post-AV (refresh token endpoint).          |
| **[Rate Limiting]**              | Complements AV by throttling login attempts.                                                  | AV pipeline (e.g., Redis-based enforcement).|
| **[Session Management]**         | Tracks and manages active user sessions.                                                      | AV (session creation/revocation).          |

---
## **Best Practices**
1. **Never store plaintext passwords** – Use **bcrypt**, **Argon2**, or **PBKDF2**.
2. **Short-lived tokens** – Use JWT with `exp` ≤ 30 minutes; issue refresh tokens.
3. **Secure token storage** – Use **HttpOnly, Secure, SameSite=Strict** cookies for session tokens.
4. **Audit logging** – Log failed attempts (without exposing PII) for security monitoring.
5. **Regularly rotate secrets** – Update `SECRET_KEY` for JWT signing and database salts.
6. **Use WebAuthn** – For passwordless auth (e.g., biometric or FIDO2 keys).
7. **Validate input types** – Reject malformed payloads early (e.g., check `password` length ≥ 8).

---
## **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌───────────────┐
│   Client    │───▶│  API Gateway│───▶│ Authentication  │───▶│  Application  │
│ (Browser/   │    │  (Kong,     │    │  Validation     │    │  Layer        │
│  Mobile)    │    │   AWS API   │    │  (AV Pattern)   │    │               │
└─────────────┘    │  Gateway)   │    └─────────────────┘    └───────────────┘
                    └─────────────┘
                                   │
                                   ▼
                      ┌─────────────┐
                      │  Database   │
                      │ (Users,    │
                      │  Sessions) │
                      └─────────────┘
```

---
This guide provides a **scannable**, **implementation-ready** reference for the **Authentication Validation** pattern. Adjust schemas, workflows, and security measures based on your environment (e.g., cloud vs. on-premises).