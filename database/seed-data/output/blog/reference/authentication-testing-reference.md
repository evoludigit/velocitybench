---

# **[Pattern] Authentication Testing Reference Guide**

---
## **Overview**
This guide provides a technical reference for implementing **Authentication Testing** patterns in software systems. Authentication Testing ensures that user credentials (e.g., usernames, passwords, tokens) are validated securely and correctly, verifying system resistance to unauthorized access. It covers key concepts, validation requirements, schema definitions, query examples, and integration with related security patterns.

The pattern emphasizes:
- **Credential validation** against expected formats (e.g., regex patterns, complexity rules).
- **Session management** (e.g., JWT, OAuth, or cookie-based sesssion tokens).
- **Brute-force attack mitigation** (e.g., lockout mechanisms, rate limiting).
- **Authentication flow testing** (e.g., login/logout, password reset, MFA).

---
## **Implementation Details**

### **1. Key Concepts**
| **Concept**               | **Description**                                                                 | **Example Implementation**                     |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Credential Validation** | Ensures inputs (username/password) meet security criteria (e.g., length, special chars). | Regex: `^(?=.*[A-Z])(?=.*\d).{8,}$` (8+ chars, uppercase, number). |
| **Session Token**         | Uses JWT/OAuth tokens or server-side cookies to maintain authenticated state. | `Authorization: Bearer <token>` HTTP header. |
| **Brute-Force Protection**| Limits login attempts to prevent credential guessing attacks.                 | 5 failed attempts → 15-minute lockout.        |
| **Multi-Factor Authentication (MFA)** | Requires secondary verification (e.g., TOTP, SMS codes).            | OTP sent via SMS after password entry.         |
| **Password Reset Flow**   | Validates reset tokens and temporary credentials for security.               | Token expires in 1 hour; requires new password. |

### **2. Testing Scenarios**
| **Scenario**              | **Objective**                                                                 | **Validation Rules**                          |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Login Validation**      | Verify correct credentials grant access; incorrect credentials should reject. | Username/password regex + SQL injection checks. |
| **Session Hijacking**     | Ensure tokens are short-lived or expiring (e.g., JWT `exp` claim).          | Token refreshes after 15 minutes.             |
| **MFA Bypass Attempts**   | Block access if MFA is required but not completed.                           | No access unless TOTP/SMS code is provided.   |
| **Password Reset**        | Confirm reset tokens are valid and single-use.                              | Token URL parameter + password strength rules. |

---

## **Schema Reference**
Below are standardized schemas for authentication testing components. Use these for API/DB validation.

### **1. User Credential Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "minLength": 4,
      "pattern": "^[a-zA-Z0-9_]+$"
    },
    "password": {
      "type": "string",
      "minLength": 8,
      "pattern": "^(?=.*[A-Z])(?=.*\d).{8,}$",
      "description": "Requires uppercase, number, and 8+ length."
    },
    "email": {
      "type": "string",
      "format": "email"
    }
  },
  "required": ["username", "password", "email"]
}
```

### **2. Login Response Schema**
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "failed", "locked"]
    },
    "token": {
      "type": "string",
      "description": "JWT/OAuth token (if successful)."
    },
    "message": {
      "type": "string"
    },
    "retriesRemaining": {
      "type": "integer",
      "minimum": 0
    }
  },
  "required": ["status"]
}
```

### **3. Session Token Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "token": {
      "type": "string",
      "format": "jwt"  // Valid JWT structure expected.
    },
    "expiresIn": {
      "type": "string",
      "format": "duration"  // e.g., "15m"
    },
    "tokenType": {
      "type": "string",
      "enum": ["bearer", "cookie"]
    }
  },
  "required": ["token", "expiresIn"]
}
```

---
## **Query Examples**

### **1. Validating User Credentials (REST API)**
**Request:**
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user123",
  "password": "SecurePass123!"
}
```
**Success Response (200 OK):**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "bearer"
}
```
**Failure Response (401 Unauthorized):**
```json
{
  "status": "failed",
  "message": "Invalid credentials",
  "retriesRemaining": 3
}
```

### **2. Testing Brute-Force Protection**
**Request (5 failed attempts):**
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "wrong_user",
  "password": "wrong_pass"
}
```
**Response (429 Too Many Requests):**
```json
{
  "status": "locked",
  "message": "Account locked for 15 minutes. Try again later."
}
```

### **3. MFA Verification (TOTP)**
**Request after username/password:**
```http
POST /api/auth/mfa
Content-Type: application/json

{
  "mfaToken": "123456"  // TOTP code
}
```
**Success Response (200 OK):**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
**Failure Response (400 Bad Request):**
```json
{
  "status": "failed",
  "message": "Invalid MFA code"
}
```

### **4. Token Refresh**
**Request:**
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "old_refresh_token..."
}
```
**Success Response (200 OK):**
```json
{
  "status": "success",
  "newToken": "new_jwt_token..."
}
```

---
## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Connection to Authentication Testing**                     |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------|
| **[Rate Limiting](https://link-to-rate-limiting)** | Limits request frequency to prevent brute-force attacks.           | Used in brute-force protection (e.g., 5 failed attempts → lockout). |
| **[JWT Security](https://link-to-jwt)** | Secure token generation/validation for stateless auth.               | Ensures session tokens (JWT) are validated in login flows.     |
| **[Input Sanitization](https://link-to-sanitization)** | Cleans user input to prevent injection attacks.              | Applied to username/password fields to block SQL injection.   |
| **[OAuth 2.0](https://link-to-oauth)** | Delegated authentication via third parties (e.g., Google, GitHub). | Used for external MFA or single-sign-on (SSO) integration.    |
| **[Session Management](https://link-to-session)** | Tracks user sessions via cookies or tokens.                   | Validates token expiration and revocation in auth flows.      |

---
## **Best Practices**
1. **Use Strong Algorithms**:
   - Hash passwords with **bcrypt** (cost factor ≥ 10) or **Argon2**.
   - Encrypt tokens with **HS256** (HMAC) or **RS256** (RSA) for JWT.

2. **Implement Rate Limiting**:
   - Limit login attempts (e.g., 5/1 min) via API gateways or middleware.

3. **Secure Token Storage**:
   - Store refresh tokens securely (e.g., Redis with TTL).
   - Rotate tokens on suspicious activity (e.g., IP change).

4. **Test Edge Cases**:
   - Empty/malformed inputs (e.g., `password: ""`).
   - Concurrent login attempts (race conditions).
   - Token replay attacks (ensure `iat`/`nbf` claims).

5. **Audit Logs**:
   - Log failed attempts (without PII) for forensic analysis.

---
## **Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| **Postman/Newman**        | Automate API endpoint testing for auth flows.                             |
| **OWASP ZAP**             | Scan for vulnerabilities in auth implementation.                          |
| **JWT Tools (jwt.io)**    | Decode/validate JWT tokens during testing.                                |
| **Python: `passlib`**     | Secure password hashing/verification.                                     |
| **Node.js: `bcrypt`**    | Password hashing with salting.                                            |
| **Dockerized Test Suites** | Isolation for auth service testing (e.g., `docker-compose` with Redis).   |

---
## **Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                  |
|------------------------------------|----------------------------------------|-----------------------------------------------|
| **Token expiration errors**        | JWT `exp` claim misconfigured.         | Set `exp` to 15–60 minutes.                    |
| **Brute-force bypass**             | Rate limiter not enforced.             | Implement middleware (e.g., `express-rate-limit`). |
| **MFA code validation fails**      | Incorrect TOTP secret/algorithm.       | Verify secret matches backend (e.g., `pyotp`). |
| **Session hijacking**              | Long-lived tokens without refresh.     | Use short-lived tokens + refresh endpoints.   |
| **SQL injection in queries**       | Unsanitized user input.                | Use parameterized queries (e.g., `pg.format`).|

---
**References:**
- [OWASP Authentication Testing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [RFC 7519 (JWT Specification)](https://tools.ietf.org/html/rfc7519)
- [NIST SP 800-63B (MFA Guidelines)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B.pdf)