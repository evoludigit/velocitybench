# **[Pattern] Security Verification Reference Guide**

---

## **Overview**
The **Security Verification Pattern** ensures that systems, applications, or APIs authenticate and validate user identity, data integrity, and access permissions before granting resources or executing actions. This pattern prevents unauthorized access, data breaches, and malicious activities by enforcing **multi-layered verification** (e.g., authentication, authorization, input validation, and non-repudiation). It is widely used in identity management, financial systems, and API security to maintain compliance with standards like **OAuth 2.0, SAML, or GDPR**.

This guide covers implementation concepts, schema structures, query examples, and related best practices to enforce robust security verification.

---

## **Key Concepts & Implementation Details**

### **1. Core Components of Security Verification**
| Component               | Description                                                                                     | Example Use Case                          |
|-------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Authentication**      | Verifies user identity (e.g., credentials, tokens, biometrics).                               | Login with JWT/OAuth token validation.   |
| **Authorization**       | Ensures users have permissions for requested actions.                                          | Role-based access control (RBAC).       |
| **Input Validation**    | Sanitizes and validates user inputs to prevent injection attacks (e.g., SQLi, XSS).          | Regex validation for email fields.       |
| **Non-Repudiation**     | Ensures actions cannot be denied (e.g., digitally signed requests).                           | Audit logs with cryptographic proof.     |
| **Rate Limiting**       | Limits repeated requests to prevent brute-force attacks.                                     | API rate limits per IP/user.             |
| **Encryption**          | Secures data in transit (TLS) and at rest (AES).                                             | HTTPS for API endpoints.                 |

### **2. Common Security Verification Verbs**
| Verb               | Definition                                                                                     | Example Implementation                     |
|--------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------|
| `verifyAuthToken`  | Checks if a token (e.g., JWT) is valid and not expired.                                      | `verifyAuthToken("eyJhbGciOiJIUzI1Ni...")` |
| `checkPermissions` | Validates if a user has required permissions for an action.                                  | `checkPermissions(userId, "edit:post")`   |
| `validateInput`    | Sanitizes and validates user-provided data (e.g., SQL injection checks).                     | `validateInput("user_input", "email")`    |
| `enforceRateLimit` | Limits API requests based on user/IP to prevent abuse.                                      | `enforceRateLimit(100, "user123")`        |
| `signRequest`      | Adds a cryptographic signature to a request for non-repudiation.                             | `signRequest(data, privateKey)`           |

---

## **Schema Reference**

### **1. Authentication Token Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "token": {
      "type": "string",
      "format": "jwt",
      "description": "JSON Web Token (JWT) for authentication."
    },
    "expiresAt": {
      "type": "string",
      "format": "date-time",
      "description": "Token expiration timestamp (UTC)."
    },
    "issuer": {
      "type": "string",
      "description": "System/issuer that generated the token."
    },
    "userId": {
      "type": "string",
      "description": "Unique identifier of the authenticated user."
    }
  },
  "required": ["token", "expiresAt", "userId"]
}
```

### **2. Permission Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "userId": {
      "type": "string",
      "description": "User identifier."
    },
    "action": {
      "type": "string",
      "description": "Action to verify (e.g., 'read:data')."
    },
    "resource": {
      "type": "string",
      "description": "Resource being accessed (e.g., 'user_profile')."
    },
    "granted": {
      "type": "boolean",
      "description": "Whether access is allowed."
    }
  },
  "required": ["userId", "action", "granted"]
}
```

### **3. Input Validation Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "field": {
      "type": "string",
      "description": "Input field name (e.g., 'email')."
    },
    "value": {
      "type": "string",
      "description": "User-provided value."
    },
    "regex": {
      "type": "string",
      "description": "Regex pattern for validation (e.g., `^[^@]+@[^@]+\.[^@]+$`)."
    },
    "isValid": {
      "type": "boolean",
      "description": "True if input matches constraints."
    }
  },
  "required": ["field", "value", "isValid"]
}
```

---

## **Query Examples**

### **1. Verify JWT Token**
**Request:**
```http
POST /api/verify-token
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (Success):**
```json
{
  "status": "success",
  "userId": "user_123",
  "expiresAt": "2023-12-31T23:59:59Z"
}
```

**Response (Failure):**
```json
{
  "status": "error",
  "message": "Invalid or expired token."
}
```

### **2. Check User Permissions**
**Request:**
```http
POST /api/check-permission
Content-Type: application/json

{
  "userId": "user_123",
  "action": "edit:post",
  "resource": "post_456"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "granted": true
}
```

**Response (Failure):**
```json
{
  "status": "error",
  "message": "Permission denied: 'edit:post' not allowed."
}
```

### **3. Validate User Input**
**Request:**
```http
POST /api/validate-input
Content-Type: application/json

{
  "field": "email",
  "value": "test@example.com",
  "regex": "^[^@]+@[^@]+\\.[^@]+$"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "isValid": true
}
```

**Response (Failure):**
```json
{
  "status": "error",
  "message": "Invalid email format."
}
```

### **4. Enforce Rate Limiting**
**Request:**
```http
GET /api/data?limit=100
```

**Response (Success):**
```json
{
  "status": "success",
  "data": [...]
}
```

**Response (Failed Due to Rate Limit):**
```json
{
  "status": "error",
  "message": "Rate limit exceeded. Try again in 1 minute."
}
```

---

## **Related Patterns**
1. **[Authentication Pattern]** – Core user identity verification (e.g., OAuth 2.0, SAML).
2. **[Authorization Pattern]** – Role-based access control (RBAC) for fine-grained permissions.
3. **[Input Sanitization Pattern]** – Deep cleaning of user-provided data to prevent injection attacks.
4. **[Audit Logging Pattern]** – Recording actions for non-repudiation and compliance.
5. **[TLS Encryption Pattern]** – Securing data in transit (HTTPS, mTLS).
6. **[Zero Trust Architecture]** – Verifying every request internally and externally.

---

## **Best Practices**
- **Use JWT/OAuth** for stateless authentication where possible.
- **Implement least-privilege access** – Grant only necessary permissions.
- **Log all security verification attempts** (successful/failure) for auditing.
- **Rotate secrets** (API keys, private keys) regularly.
- **Rate-limit API endpoints** to prevent brute-force attacks.
- **Comply with regulations** (GDPR, PCI-DSS) based on your industry.

---
**References:**
- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)
- [JWT Best Practices](https://auth0.com/docs/secure/tokens/jwt-best-practices)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)