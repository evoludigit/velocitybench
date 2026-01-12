---
**[Pattern] Reference Guide: Authentication Conventions**

---

### **1. Overview**
The **Authentication Conventions** pattern standardizes how authentication is handled across an API, application, or microservices ecosystem. By defining reusable conventions—such as authentication headers, token formats, validation rules, and error responses—it ensures consistency, reduces boilerplate, and simplifies integration. This pattern is critical for security, scalability, and maintainability in distributed systems. It abstracts authentication logic into a cohesive framework, allowing teams to focus on business logic rather than reinventing security mechanisms. Common use cases include:

- **APIs**: Uniform token validation across endpoints.
- **Microservices**: Cross-service authentication without duplicated logic.
- **Client-Server Apps**: Consistent authentication flows (e.g., OAuth2, JWT).

Adopting this pattern improves security by limiting misconfigurations (e.g., inconsistent token expiration) and enhances developer productivity by centralizing authentication logic.

---

### **2. Key Concepts**
| Concept               | Description                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **Authentication Header**  | Standard HTTP header (e.g., `Authorization: Bearer <token>`) where tokens are transmitted.        |
| **Token Format**       | Defined schema for tokens (e.g., JWT with `iss`, `exp`, `sub` claims).                           |
| **Validation Rules**   | Rules for token expiration, signature verification, or role-based access (e.g., `exp < current_time`). |
| **Error Responses**    | Consistent HTTP status codes (e.g., `401 Unauthorized`, `403 Forbidden`) and error payloads.      |
| **Refresh Tokens**     | Mechanism to rotate short-lived tokens without user re-login (e.g., via `/refresh` endpoint).   |
| **Session Management** | Rules for session invalidation (e.g., after inactivity or logout).                                |

---

### **3. Schema Reference**
#### **A. Authentication Header**
| Field               | Type     | Required | Description                                                                                     | Example                          |
|---------------------|----------|----------|-------------------------------------------------------------------------------------------------|----------------------------------|
| **Header Name**     | `string` | Yes      | Standard HTTP header name (e.g., `Authorization`).                                               | `Authorization`                   |
| **Token Prefix**    | `string` | Yes      | Prefix for token type (e.g., `Bearer`, `Basic`).                                                | `Bearer`                         |
| **Token Value**     | `string` | Yes      | Encoded token (e.g., JWT, opaque token).                                                         | `xyz.abc.123`                     |

**Example Header:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

---

#### **B. JWT Claims Schema**
| Claim       | Type    | Required | Description                                                                                     | Example Value                  |
|-------------|---------|----------|-------------------------------------------------------------------------------------------------|--------------------------------|
| `iss`       | `string`| Yes      | Issuer of the token (e.g., API domain).                                                          | `https://api.example.com`       |
| `sub`       | `string`| Yes      | Subject/unique identifier for the user/tenant.                                                   | `user_12345`                    |
| `exp`       | `int`   | Yes      | Expiration timestamp (UTC epoch seconds).                                                        | `1672531202`                    |
| `iat`       | `int`   | No       | Issued-at timestamp (for auditing).                                                              | `1672500000`                    |
| `roles`     | `array` | No       | User roles/permissions (e.g., `["admin", "user"]`).                                              | `["admin"]`                     |
| `tenant_id` | `string`| No       | Multi-tenancy identifier (if applicable).                                                         | `tenant_a1b2c3`                 |

**JWT Payload Example:**
```json
{
  "iss": "https://api.example.com",
  "sub": "user_12345",
  "exp": 1672531202,
  "roles": ["admin"],
  "tenant_id": "tenant_a1b2c3"
}
```

---

#### **C. Error Responses**
| Status Code | Error Type      | Description                                                                                     | Example Payload                                                                 |
|-------------|-----------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `401`       | `Unauthorized`  | Missing/invalid token or credentials.                                                          | `{"error": "invalid_token", "message": "Token expired"}`                        |
| `403`       | `Forbidden`     | Valid token but insufficient permissions.                                                        | `{"error": "insufficient_scope", "message": "Missing 'admin' role"}`           |
| `400`       | `BadRequest`    | Malformed header (e.g., missing prefix).                                                       | `{"error": "invalid_header", "message": "Missing 'Authorization' header"}`     |
| `429`       | `TooManyRequests` | Rate-limiting exceeded (optional).                                                              | `{"error": "rate_limit_exceeded", "retry_after": 60}`                          |

---

### **4. Implementation Examples**
#### **A. Validating a JWT (Node.js with `jsonwebtoken`)**
```javascript
const jwt = require('jsonwebtoken');

function validateToken(token, secret) {
  try {
    const decoded = jwt.verify(token, secret);
    if (!decoded.roles?.includes('user')) {
      throw new Error('Insufficient permissions');
    }
    return decoded;
  } catch (err) {
    throw new Error('Invalid token');
  }
}

// Usage:
const token = req.headers.authorization?.split(' ')[1];
const user = validateToken(token, 'your-secret-key');
```

#### **B. API Gateway Rules (Kong)**
```yaml
# Kong configuration for JWT validation
plugins:
  - name: jwt
    config:
      claims_to_verify:
        - iss: "https://api.example.com"
      key_claim_name: "sub"
      secret_is_base64: false
      secret: "your-secret-key"
```

#### **C. Query Example: Refresh Token**
**Request:**
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "opaque_refresh_token_123"
}
```

**Response (Success):**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "jwt_new_access_token",
  "expires_in": 3600,
  "refresh_token": "opaque_refresh_token_456"  // New refresh token
}
```

**Response (Error: Refresh Token Expired):**
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": "expired_refresh_token",
  "message": "Refresh token has expired. User must re-authenticate."
}
```

---

### **5. Validation Rules**
| Rule                          | Implementation Notes                                                                             | Example Check                     |
|-------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| **Token Expiration**          | Ensure `exp` claim is > current timestamp.                                                    | `if (decoded.exp < Date.now() / 1000) throw Error('Expired')` |
| **Issuer Verification**       | Check `iss` claim matches expected issuer (e.g., API domain).                                | `if (decoded.iss !== 'https://api.example.com') throw Error('Invalid issuer')` |
| **Required Roles**            | Validate `roles` claim contains at least one permitted role.                                   | `if (!decoded.roles?.includes('admin')) throw Error('Forbidden')` |
| **Token Signature**           | Verify JWT signature using the public key.                                                     | Use `jwt.verify()` in libraries. |
| **Rate Limiting**             | Track failed attempts to prevent brute-force attacks.                                          | Log `401` errors per IP.          |
| **Multi-Tenancy**             | Ensure `tenant_id` claim matches the request’s tenant context.                                 | Context from subdomain or header. |

---

### **6. Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **[OAuth 2.0 Flows](https://tools.ietf.org/html/rfc6749)** | Standardized authorization framework for delegated access (e.g., authorization codes).       | External identity providers (e.g., Google, GitHub).                        |
| **[OpenID Connect](https://openid.net/specs/openid-connect-core-1_0.html)** | Extends OAuth 2.0 to include authentication and user info.                                     | Single Sign-On (SSO) across services.                                     |
| **[API Gateway](https://www.mulesoft.com/apigateway/what-is-an-api-gateway)** | Centralized entry point for request routing, authentication, and rate limiting.                  | High-traffic APIs needing unified security.                               |
| **[stateless Authentication](https://docs.microsoft.com/en-us/azure/architecture/patterns/stateless-authentication)** | Servers rely on tokens (e.g., JWT) rather than server-side sessions.                          | Scalable microservices.                                                    |
| **[Role-Based Access Control (RBAC)](https://en.wikipedia.org/wiki/Role-based_access_control)** | Assign permissions to roles rather than individual users.                                      | Fine-grained access control (e.g., `admin`, `editor`).                     |

---

### **7. Best Practices**
1. **Standardize Headers**:
   - Always use `Authorization: Bearer <token>` for JWTs. Avoid custom headers (e.g., `X-Auth-Token`).

2. **Token Lifecycle**:
   - Short-lived access tokens (e.g., 15–30 minutes) with long-lived refresh tokens (e.g., 7 days).
   - Use `exp` and `iat` claims for auditing.

3. **Error Handling**:
   - Return **machine-readable** errors (e.g., `{"error": "invalid_token"}`) to avoid leaking sensitive details.
   - Log failed attempts for security monitoring.

4. **Testing**:
   - Mock tokens in unit tests (e.g., `jwt.sign({ sub: 'test' }, 'secret', { expiresIn: '1h' })`).
   - Validate token parsing in integration tests.

5. **Documentation**:
   - Publish a **Swagger/OpenAPI** spec with authentication requirements.
   - Include examples for `curl`, Postman, or client SDKs.

6. **Security**:
   - Rotate secrets periodically.
   - Use **HTTPS** for all token transmission.
   - Consider **token revocation** for sensitive operations (e.g., admin actions).

---

### **8. Troubleshooting**
| Issue                          | Cause                                  | Solution                                                                 |
|--------------------------------|----------------------------------------|---------------------------------------------------------------------------|
| `401 Unauthorized`             | Missing/invalid token.                 | Check header format and token expiration.                                |
| `403 Forbidden`                | Valid token but missing roles.         | Verify `roles` claim and RBAC policies.                                  |
| Token parsing fails            | Corrupted JWT (e.g., mismatched keys). | Regenerate tokens if signature fails.                                    |
| Refresh token rejected         | Expired or revoked refresh token.      | Force re-authentication.                                                   |
| Rate limit exceeded            | Too many failed attempts.               | Implement retry-with-backoff or CAPTCHA for locked users.                |

---
**[End of Guide]**
*Last updated: [YYYY-MM-DD]*