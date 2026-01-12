# **[Pattern] Authentication Integration – Reference Guide**

---

## **1. Overview**
The **Authentication Integration** pattern enables secure, centralized user authentication across multiple services, applications, or microservices. This pattern decouples authentication logic from business logic, improving security, scalability, and maintainability. It supports single sign-on (SSO), role-based access control (RBAC), and OAuth 2.0/OpenID Connect (OIDC) flows while ensuring compliance with standards like JWT (JSON Web Tokens) and SAML.

Key benefits:
- **Single source of truth** for authentication data (e.g., user credentials, sessions).
- **Reduced boilerplate** in application code.
- **Enhanced security** via standardized protocols.
- **Flexibility** to integrate third-party identity providers (IdPs) or federated identity systems.

---

## **2. Schema Reference**
Below are the core components and their data structures for Authentication Integration.

| **Component**               | **Description**                                                                 | **Schema Example**                                                                                     |
|-----------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Authentication Request**  | Client request to validate credentials or tokens.                              | ```json { "userId": "str", "password": "str", "clientId": "str", "redirectUri": "str" }```         |
| **Token Response**          | Server response containing JWT/access tokens.                                   | ```json { "access_token": "str", "id_token": "str", "expires_in": "int", "token_type": "str" }``` |
| **Session Token**           | Short-lived token stored client-side for stateless sessions.                     | `{ "sessionId": "UUID", "userId": "str", "expiry": "ISO8601" }`                                    |
| **User Profile**            | Metadata about a user (e.g., roles, permissions).                              | ```json { "sub": "user123", "name": "string", "roles": ["admin", "user"], "email": "string" }```  |
| **OAuth 2.0 Grant**         | Authorization flow data (e.g., `authorization_code`, `client_credentials`).      | ```json { "grant_type": "string", "code": "str", "scope": "string" }```                              |
| **JWT Payload**             | Claims embedded in a JWT token.                                               | ```json { "iss": "str", "sub": "str", "aud": "str", "exp": "int", "iat": "int" }```                  |
| **Role Binding**            | Link between a user and permissions (RBAC).                                    | `{ "userId": "str", "role": "str", "scope": ["API-v1", "Dashboard"] }`                              |

---

## **3. Implementation Details**
### **Core Workflow**
1. **Client Authenticates**: User provides credentials or delegates to an IdP (e.g., OAuth login).
2. **Server Validates**: Authentication service validates credentials/tokens (e.g., via JWT verification).
3. **Token Issued**: Access/ID tokens are returned (JWT or session tokens).
4. **Protected Resource Access**: Client includes tokens in subsequent requests (e.g., `Authorization: Bearer <token>`).

### **Key Implementation Scenarios**
#### **A. Local Authentication (Username/Password)**
- **Flow**:
  1. Client sends `POST /auth/login` with `userId` and `password`.
  2. Server hashes password and compares it to stored credentials.
  3. On success, issue a **JWT access token** or **session cookie**.
- **Example Response**:
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
  ```

#### **B. OAuth 2.0/OpenID Connect (OIDC)**
- **Flow**: `Authorization Code` or `Implicit` flow.
  1. Client redirects user to IdP (e.g., Google, Auth0) for consent.
  2. IdP returns `code` or `id_token` to `redirectUri`.
  3. Client exchanges `code` for tokens via `/token` endpoint.
- **Token Endpoint Request**:
  ```http
  POST /oauth/token
  Content-Type: application/x-www-form-urlencoded

  grant_type=authorization_code&code=AUTH_CODE&redirect_uri=https://client.com/callback
  ```
- **Response**:
  ```json
  {
    "access_token": "JWT_STRING",
    "id_token": "JWT_STRING",
    "refresh_token": "str",
    "expires_in": 3600
  }
  ```

#### **C. JWT Validation**
- **Server-side Validation**:
  - Verify signature using **public key** (RS256, ES256).
  - Check `iss`, `aud`, `exp`, and `iat` claims.
  - Example (Python with `pyjwt`):
    ```python
    import jwt
    public_key = load_public_key_from_pem("-----BEGIN PUBLIC KEY-----...")
    decoded = jwt.decode(token, public_key, algorithms=["RS256"])
    ```

#### **D. Role-Based Access Control (RBAC)**
- **Example Policy**:
  - Users with `role: "admin"` can access `/api/admin`.
  - Middleware checks JWT claims:
    ```javascript
    function checkRole(req, res, next) {
      const token = req.headers.authorization.split(" ")[1];
      const decoded = jwt.verify(token, secretKey);
      if (decoded.roles.includes("admin")) next();
      else res.status(403).send("Forbidden");
    }
    ```

---

## **4. Query Examples**
### **A. Login with Username/Password**
```http
POST /auth/login HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "userId": "alice123",
  "password": "securePass456"
}
```

### **B. OAuth Token Exchange**
```http
POST /oauth/token HTTP/1.1
Host: auth-server.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=AUTH-12345&redirect_uri=https://client.com/callback
```

### **C. Token Validation Query (OpenAPI/Swagger)**
```yaml
paths:
  /auth/validate:
    get:
      summary: Validate JWT
      parameters:
        - name: token
          in: query
          required: true
          schema:
            type: string
      responses:
        200:
          description: Valid token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenPayload'
```

### **D. Session Token Rotation**
```http
POST /auth/refresh HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "refresh_token": "rfc_123..."
}
```

---

## **5. Error Handling**
| **Error Code** | **Description**                          | **HTTP Status** | **Example Response**                                                                 |
|-----------------|------------------------------------------|-----------------|-------------------------------------------------------------------------------------|
| `auth_001`      | Invalid credentials                      | 401             | `{ "error": "auth_failed", "details": "Invalid password" }`                        |
| `auth_002`      | Missing token                            | 401             | `{ "error": "auth_required" }`                                                    |
| `auth_003`      | Expired token                            | 401             | `{ "error": "token_expired" }`                                                     |
| `auth_004`      | Invalid scope                            | 403             | `{ "error": "insufficient_scope" }`                                                |
| `idp_500`       | IdP connection failure                   | 502             | `{ "error": "idp_unavailable" }`                                                   |

---

## **6. Security Considerations**
1. **Token Storage**:
   - Store access tokens in **memory** (short-lived) or encrypted databases.
   - Use **HttpOnly, Secure cookies** for session tokens.
2. **Rate Limiting**:
   - Throttle login attempts to prevent brute-force attacks (e.g., 5 attempts/minute).
3. **Token Invalidation**:
   - Implement **short-lived tokens** (TTL: 15–60 minutes) + **refresh tokens**.
   - Support **logout** via token blacklisting or revocation endpoints.
4. **Transport Security**:
   - Enforce **HTTPS** for all authentication flows.
   - Use **CORS** policies to restrict token exposure.

---

## **7. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                                      |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| **Stateless Session**     | Avoid server-side session storage; rely on JWT/tokens.                        | Microservices, distributed systems.              |
| **Federated Identity**    | Delegate authentication to external IdPs (e.g., SAML, OIDC).                  | Enterprise SSO.                                  |
| **API Gateway Auth**      | Centralize auth in a gateway (e.g., Kong, Apigee) before routing requests.     | Multi-tenant APIs.                               |
| **Multi-Factor Auth (MFA)**| Require secondary factors (e.g., TOTP, biometrics) for sensitive operations.  | High-security applications.                     |
| **Claim-Based Authorization** | Use JWT claims to enforce fine-grained permissions.                          | RBAC with dynamic roles.                          |

---

## **8. Tools & Libraries**
| **Tool/Library**       | **Purpose**                                      | **Language/Framework**               |
|------------------------|--------------------------------------------------|---------------------------------------|
| **JWT**                | Token encoding/decoding                          | JavaScript (jwt-lib), Python (PyJWT) |
| **Auth0/Ory Hydra**    | OAuth2/OIDC server                               | Go, Node.js                          |
| **Spring Security**    | Java auth framework                              | Java Spring Boot                     |
| **Passport.js**        | Node.js auth middleware                          | Node.js                              |
| **Django REST Framework** | Django auth extensions                          | Python                              |
| **Kubernetes RBAC**    | Kubernetes role-based access control             | Kubernetes                           |

---
**Note**: Replace placeholders (e.g., `api.example.com`) with your actual endpoints. Adjust schemas based on your tech stack (e.g., protobuf for gRPC).