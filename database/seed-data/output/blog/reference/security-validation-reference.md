# **[Pattern] Security Validation Reference Guide**

---

## **Overview**
The **Security Validation** pattern ensures that interactions with systems, applications, and APIs adhere to strict security policies before granting access or authorization. This pattern validates user identity, permissions, and input data integrity across authentication, authorization, and runtime checks. By integrating validation at multiple layers—client, server, and application logic—it mitigates risks like unauthorized access, injection attacks, and data tampering. This guide provides implementation instructions, schema references, and use cases for deploying security validation effectively.

---

## **Key Concepts**
The **Security Validation** pattern consists of three core components:

| **Component**       | **Purpose**                                                                 | **Key Checks**                                                                 |
|---------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Authentication**  | Verifies user identity via credentials or tokens.                           | Credential strength, token expiration, session integrity.                       |
| **Authorization**   | Confirms user permissions for requested actions.                           | Role-based access control (RBAC), attribute-based policies, least-privilege.   |
| **Input Validation**| Ensures data integrity and prevents malicious input.                        | Type checking, format validation, sanitization, SQL injection/NoSQL query checks. |

---

## **Schema Reference**
Below are standardized schemas for security validation checks.

### **1. Authentication Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "authMethod": {
      "type": "string",
      "enum": ["OAuth2", "JWT", "SAML", "BasicAuth", "MultiFactor"]
    },
    "credentialStrength": {
      "type": "string",
      "enum": ["Low", "Medium", "High"],
      "description": "Evaluates password complexity or token entropy."
    },
    "expirationCheck": {
      "type": "boolean",
      "description": "Ensures tokens/sessions have valid expiry."
    },
    "sessionIntegrity": {
      "type": "boolean",
      "description": "Verifies session tokens aren’t tampered with."
    }
  },
  "required": ["authMethod", "credentialStrength", "expirationCheck"]
}
```

### **2. Authorization Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "policyType": {
      "type": "string",
      "enum": ["RBAC", "ABAC", "ClaimBased"]
    },
    "permissions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "action": { "type": "string" },  // e.g., "read", "delete"
          "resource": { "type": "string" } // e.g., "/api/users", "database.table"
        },
        "required": ["action", "resource"]
      }
    },
    "leastPrivilege": {
      "type": "boolean",
      "description": "Enforces minimal required permissions."
    }
  },
  "required": ["policyType", "permissions"]
}
```

### **3. Input Validation Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "typeCheck": {
      "type": "string",
      "description": "Validates data type (e.g., 'integer', 'email')."
    },
    "formatCheck": {
      "type": "string",
      "description": "Ensures compliance with formats (e.g., 'YYYY-MM-DD')."
    },
    "sanitization": {
      "type": "boolean",
      "description": "Removes or encodes harmful characters."
    },
    "injectionProtection": {
      "type": "object",
      "properties": {
        "sql": { "type": "boolean" },
        "nosql": { "type": "boolean" },
        "xss": { "type": "boolean" }
      },
      "description": "Prevents SQL/NoSQL injection and XSS attacks."
    }
  },
  "required": ["typeCheck", "injectionProtection"]
}
```

---

## **Implementation Details**
### **1. Authentication Layer**
- **Where to Implement**: API gateways, authentication servers (e.g., Keycloak, Auth0), or application entry points.
- **Steps**:
  1. **Validate Credentials**: Reject weak passwords/tokens (e.g., using `credentialStrength: "High"`).
  2. **Token Expiry**: Check `expirationCheck` to revoke expired tokens.
  3. **Session Integrity**: Use HMAC signatures or JWT claims to detect tampering.

**Example (Pseudocode)**:
```javascript
if (!validateToken(token, { expirationCheck: true, sessionIntegrity: true })) {
  reject("Invalid or expired token");
}
```

### **2. Authorization Layer**
- **Where to Implement**: Middleware (e.g., Express.js, Spring Security), database query builders, or API controllers.
- **Steps**:
  1. **Policy Enforcement**: Use `policyType: "RBAC"` to map roles to permissions.
  2. **Least Privilege**: Ensure `leastPrivilege: true` limits access to only required actions.
  3. **Dynamic Checks**: Validate permissions per request (e.g., `permissions: [{ action: "delete", resource: "/users/123" }]`).

**Example (REST API)**:
```http
GET /api/users/123
Headers: Authorization: Bearer <token>
Response: 403 Forbidden (if user lacks "read" permission on "/users/123")
```

### **3. Input Validation Layer**
- **Where to Implement**: API request parsers, ORM queries (e.g., Sequelize, Prisma), or frontend form handling.
- **Steps**:
  1. **Type/Formats**: Enforce `typeCheck: "email"` or `formatCheck: "YYYY-MM-DD"`.
  2. **Sanitization**: Use libraries like `DOMPurify` (JS) or `OWASP ESAPI`.
  3. **Injection Protection**: Disable unsafe string interpolation in SQL (e.g., parameterized queries).

**Example (SQL Query)**:
```sql
-- ✅ Safe (parameterized)
SELECT * FROM users WHERE id = ?; -- ? = userInput

-- ❌ Vulnerable (direct interpolation)
SELECT * FROM users WHERE id = ${userInput}; -- Risk of SQL injection
```

---

## **Query Examples**
### **1. Validating a JWT Token**
**Request**:
```http
POST /login
Content-Type: application/json

{
  "username": "admin",
  "password": "SecurePass123!",
  "authMethod": "JWT"
}
```
**Response (Success)**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": "1h",
  "permissions": [{"action": "read", "resource": "/api/data"}]
}
```

**Response (Failure)**:
```json
{
  "error": "Invalid credentials or expired token",
  "validation": {"credentialStrength": "Low", "expirationCheck": false}
}
```

### **2. Checking Permissions**
**Request**:
```http
GET /api/admin/settings
Headers: Authorization: Bearer <token>
```
**Response (Authorized)**:
```json
{
  "data": { ... },
  "policy": {"policyType": "RBAC", "role": "admin"}
}
```
**Response (Denied)**:
```json
{
  "error": "Insufficient permissions",
  "missingActions": ["admin.settings.update"]
}
```

### **3. Validating User Input**
**Request**:
```http
POST /api/submit
Content-Type: application/json

{
  "email": "user@example.com",
  "birthDate": "2000-01-01",
  "comment": "<script>alert('xss')</script>"
}
```
**Response (Valid)**:
```json
{
  "status": "success",
  "sanitizedComment": "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
}
```
**Response (Invalid)**:
```json
{
  "error": "Invalid input format",
  "details": {"birthDate": "Expected YYYY-MM-DD", "comment": "XSS detected"}
}
```

---

## **Query Examples (Programmatic)**
### **Python (Flask + JWT)**
```python
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)
SECRET_KEY = "your-secret-key"

@app.route('/protected', methods=['GET'])
def protected():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("permissions") and "read" in payload["permissions"]:
            return jsonify({"data": "Sensitive data"})
        else:
            return jsonify({"error": "Permission denied"}), 403
    except:
        return jsonify({"error": "Invalid token"}), 401
```

### **JavaScript (Node.js + Express)**
```javascript
const express = require('express');
const { body, validationResult } = require('express-validator');
const app = express();

app.post('/submit',
  [
    body('email').isEmail(),
    body('birthDate').matches(/^\d{4}-\d{2}-\d{2}$/),
    body('comment').escape() // Sanitize
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }
    res.json({ success: true });
  }
);
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **API Gateway**           | Centralizes authentication/authorization before routing requests.               | Microservices architecture, multi-tenant applications.                         |
| **Rate Limiting**         | Limits request frequency to prevent brute-force attacks.                        | High-traffic APIs, authentication endpoints.                                    |
| **Zero Trust Architecture**| Assumes breach risk; validates every request dynamically.                      | High-security environments (gov, finance).                                     |
| **Principle of Least Privilege** | Grants minimal permissions by default.                                     | Database access, file system operations.                                       |
| **Fail-Secure Defaults**  | Rejects requests by default; requires explicit permission grants.             | Security-critical systems (e.g., defense, healthcare).                         |

---
## **Best Practices**
1. **Defense in Depth**: Combine multiple validation layers (client + server).
2. **Logging**: Audit failed validations for security monitoring.
3. **Regular Updates**: Use updated schemas (e.g., OWASP Top 10, CWE).
4. **Testing**: Automate validation tests (e.g., Postman, unit tests for input checks).
5. **Documentation**: Clearly define validation rules for developers (e.g., OpenAPI specs).

---
**Keywords**: Security Validation, Authentication, Authorization, Input Sanitization, JWT, RBAC, OWASP, Zero Trust.