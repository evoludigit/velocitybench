# **[Pattern] Authorization Best Practices Reference Guide**

---

## **Overview**
This guide provides a comprehensive reference for implementing **secure, scalable, and maintainable authorization patterns** in modern applications. Authorization determines what authenticated users (or service accounts) are **permitted or denied** access to specific resources, actions, or data. Adhering to best practices ensures robustness, minimizes security vulnerabilities (e.g., privilege escalation), and simplifies compliance with standards like **OWASP Top 10** and **CIS Benchmarks**. This reference covers foundational concepts, implementation strategies, schema design, and real-world examples across common architectures (REST APIs, microservices, and frontend applications).

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authentication**     | Verifying an entity’s identity (e.g., via tokens, OAuth, or certificates). Authorization builds on authentication to control access.                                                                           |
| **Authorization**      | Granting or denying permissions to authenticated entities based on roles, policies, or resource attributes.                                                                                                      |
| **Role-Based Access Control (RBAC)** | Assigns permissions based on predefined roles (e.g., `admin`, `editor`). Scalable for medium-sized apps.                                                                                                     |
| **Attribute-Based Access Control (ABAC)** | Grants access based on dynamic attributes (e.g., `user.age > 18`, `request.method == "POST"`). Flexible but complex to manage.                                                                          |
| **Policy-Based Access Control (PBAC)** | Uses policies (e.g., JSON rules) to define conditions. Common in cloud environments (e.g., AWS IAM policies).                                                                                                    |
| **Resource-Based Access Control (ReBAC)** | Permissions tied to resources (e.g., `user:can:delete:post(id=123)`). Decentralized and fine-grained but requires careful modeling.                                                                       |
| **Least Privilege**    | Users/servers should have only the permissions necessary to perform their tasks. Mitigates lateral movement attacks.                                                                                           |
| **Separation of Concerns** | Split authorization logic from business logic (e.g., use middleware for API gates, not application code).                                                                                                   |
| **Token Scopes**       | JWT/OAuth tokens can include scopes (e.g., `read:user`, `write:project`) to limit permissions per request.                                                                                                   |
| **Dynamic Policies**   | Rules that update without code changes (e.g., AWS IAM, Open Policy Agent). Ideal for cloud-native apps.                                                                                                        |
| **Audit Logs**         | Record authorization decisions for compliance and debugging. Tools: AWS CloudTrail, Splunk, or custom logging.                                                                                            |

---

## **Schema Reference**
Below are schema examples for common authorization systems.

### **1. Role-Based Access Control (RBAC) Schema**
| **Entity**       | **Fields**                                                                       | **Example Values**                          |
|------------------|-----------------------------------------------------------------------------------|---------------------------------------------|
| `Role`           | `id`, `name`, `description`, `permissions` (array of permission IDs)             | `{ "id": "1", "name": "admin", "permissions": [1, 2, 3] }` |
| `Permission`     | `id`, `resource_type`, `action`, `description`                                   | `{ "id": "1", "resource_type": "user", "action": "read" }` |
| `User`           | `id`, `username`, `roles` (array of role IDs)                                   | `{ "id": "101", "roles": ["1", "2"] }`       |
| `Resource`       | `id`, `type`, `owner_id`                                                        | `{ "id": "42", "type": "project", "owner_id": "101" }` |

**Example Query:**
```json
// Check if user (id=101) can read resource (type=user, id=5)
SELECT EXISTS (
  SELECT 1 FROM Role r
  JOIN Permission p ON r.id = p.role_id
  JOIN User u ON u.id = 101
  WHERE r.id IN (SELECT role_id FROM User_Role WHERE user_id = 101)
    AND p.resource_type = 'user'
    AND p.action = 'read'
    AND p.resource_id = 5
);
```

---

### **2. Attribute-Based Access Control (ABAC) Schema**
| **Entity**       | **Fields**                                                                       | **Example Values**                          |
|------------------|-----------------------------------------------------------------------------------|---------------------------------------------|
| `Policy`         | `id`, `conditions` (JSON), `effect` ("allow" or "deny")                         | `{ "id": "1", "conditions": { "user.age": { "$gt": 18 } }, "effect": "allow" }` |
| `Request`        | `user_id`, `resource_id`, `attributes` (e.g., `{ "time": "2023-10-01" }`)       | `{ "user_id": "101", "resource_id": "42", "attributes": { "time": "2023-10-01" } }` |

**Example Policy Engine (Pseudocode):**
```python
def evaluate_policy(policy, request_attributes):
    for condition in policy["conditions"]:
        if not evaluate_condition(condition, request_attributes):
            return "deny"
    return policy["effect"]
```

---

### **3. Open Policy Agent (OPA) Rego Policy Example**
```rego
package example

default allow = false

allow {
    input.request.user.role == "admin"
}

allow {
    input.request.user.age > 18
    input.request.resource.type == "public"
}
```

**Input:**
```json
{
  "request": {
    "user": { "role": "user", "age": 25 },
    "resource": { "type": "public" }
  }
}
```

**Output:** `allow = true`

---

## **Implementation Patterns**

### **1. Centralized Authorization Service**
- **Use Case:** Microservices, high scalability.
- **Components:**
  - **API Gateway:** Validates tokens and enforces policies (e.g., Kong, Apigee).
  - **Authorization Service:** Hosts RBAC/ABAC logic (e.g., AWS Cognito, Azure AD).
  - **Database:** Stores roles, permissions, and policies (PostgreSQL, DynamoDB).
- **Pros:** Decouples auth from business logic; easy to update policies.
- **Cons:** Adds latency; single point of failure if the service crashes.

**Example Flow:**
```
Client → [API Gateway] → [Auth Service] → [Backend Service]
```

---

### **2. Decentralized Authorization (Resource-Based)**
- **Use Case:** Fine-grained control (e.g., GitHub’s permissions).
- **Implementation:**
  - Resources embed their own permissions (e.g., `POST /projects/42` requires `user:write:project(id=42)`).
  - Use **OAuth 2.0 Scopes** or **Custom Tokens** with claims.
- **Pros:** No central service; permissions travel with requests.
- **Cons:** Harder to audit; requires careful claim design.

**Example Token Claim:**
```json
{
  "sub": "user123",
  "permissions": [
    { "resource": "project:42", "action": "write" }
  ]
}
```

---

### **3. Hybrid Approach (RBAC + ABAC)**
- **Use Case:** Complex environments needing both role-based and dynamic rules.
- **Implementation:**
  - **RBAC** for coarse-grained roles (e.g., `admin`, `editor`).
  - **ABAC** for fine-grained rules (e.g., "only allow edits during business hours").
- **Tools:** Combine **AWS IAM** (RBAC) with **OPA** (ABAC).

---

## **Query Examples**

### **1. Checking Permissions in a REST API (Express.js + JWT)**
```javascript
const jwt = require("jsonwebtoken");

// Middleware to validate token and check permissions
app.use("/projects/:id", (req, res, next) => {
  const token = req.headers.authorization.split(" ")[1];
  const decoded = jwt.verify(token, process.env.JWT_SECRET);

  // Check if user has 'write' permission for this project
  const hasPermission = decoded.permissions.some(
    p => p.resource === `project:${req.params.id}` && p.action === "write"
  );

  if (!hasPermission) return res.status(403).send("Forbidden");
  next();
});
```

---

### **2. SQL Query for ABAC (PostgreSQL)**
```sql
-- Check if user can delete a file based on size limit
SELECT
    u.id AS user_id,
    f.id AS file_id,
    CASE
        WHEN u.storage_quota >= f.size THEN 'allow'
        ELSE 'deny'
    END AS decision
FROM Users u
JOIN Files f ON u.id = f.owner_id
WHERE u.id = '101' AND f.id = 'file123';
```

---

### **3. OPA Query (CLI)**
```bash
opa eval --data=file://policies.rego \
  --input=file://request.json \
  --format=pretty json \
  --bundle=file://bundle \
  path=data.example.allow
```

**Input (`request.json`):**
```json
{
  "user": { "role": "editor", "age": 20 },
  "resource": { "type": "public" }
}
```

**Output:**
```json
{ "allow": false }
```

---

## **Error Handling and Security Considerations**

| **Issue**               | **Mitigation Strategy**                                                                                                                                                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Permission Bloat**    | Use **least privilege**; audit permissions regularly.                                                                                                                                                         |
| **Token Theft**         | Short-lived tokens (e.g., 15-minute JWTs); rotate secrets.                                                                                                                                                     |
| **Policy Conflicts**    | Ensure `deny` overrides `allow` (explicit deny). Use tools like **OPA’s decision stack**.                                                                                                             |
| **Inconsistent State**  | Synchronize authorization data (e.g., eventual consistency for distributed systems).                                                                                                                 |
| **Lazy Loading**        | Pre-fetch permissions during login to avoid N+1 queries.                                                                                                                                                     |
| **Audit Gaps**          | Log all authorization decisions (successes + failures) with timestamps.                                                                                                                             |
| **Vendor Lock-in**      | Abstract auth logic (e.g., interface for `AuthorizationService`). Avoid hardcoding to AWS/OAuth providers.                                                                                              |

---

## **Related Patterns**

| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[JWT Best Practices](link)**       | Securely generate, validate, and store JWTs to avoid token manipulation.                                                                                                                           | Stateless APIs, microservices.                                                                      |
| **[OAuth 2.0 Authorization Flow](link)** | Standardized flows (e.g., `authorization_code`, `client_credentials`) for third-party access.                                                                                                         | SPAs, mobile apps, or services needing OAuth integration.                                            |
| **[Open Policy Agent](link)**        | Declarative policy engine for ABAC/PBAC.                                                                                                                                                                   | Cloud-native apps, dynamic policy requirements.                                                      |
| **[Circuit Breaker](link)**           | Fail fast if the authorization service is unavailable.                                                                                                                                                | High-availability systems.                                                                           |
| **[Permissionless Architecture](link)** | Avoid explicit permissions; use capabilities (e.g., "can write to X").                                                                                                                              | Experimental; only for low-risk systems.                                                             |
| **[Attribute-Based Encryption](link)** | Encrypt data based on user attributes (e.g., only doctors can decrypt patient records).                                                                                                                | Highly sensitive data (e.g., healthcare).                                                            |
| **[Mutual TLS (mTLS)](link)**         | Secure service-to-service auth with TLS certificates.                                                                                                                                                   | Microservices communicating over networks.                                                          |

---

## **Tools and Libraries**
| **Category**               | **Tools/Libraries**                                                                                                                                                                                                 |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **RBAC Frameworks**        | [Casbin](https://casbin.org/), [Open Policy Agent (OPA)](https://www.openpolicyagent.org/), [AWS IAM](https://aws.amazon.com/iam/)                                                                   |
| **Token Libraries**        | [jsonwebtoken](https://github.com/auth0/node-jsonwebtoken) (Node.js), [PyJWT](https://pyjwt.readthedocs.io/) (Python), [Spring Security](https://spring.io/projects/spring-security) (Java)          |
| **API Gateways**           | [Kong](https://konghq.com/), [Apigee](https://cloud.google.com/apigee), [AWS API Gateway](https://aws.amazon.com/api-gateway/)                                                                     |
| **Audit Logging**          | [AWS CloudTrail](https://aws.amazon.com/cloudtrail/), [Splunk](https://www.splunk.com/), [ELK Stack](https://www.elastic.co/elk-stack)                                                                 |
| **Testing**                | [Postman](https://www.postman.com/) (API testing), [Testcontainers](https://www.testcontainers.org/) (auth service mocking)                                                                             |

---
## **Common Pitfalls and Anti-Patterns**

| **Anti-Pattern**               | **Problem**                                                                                                                                                                                                 | **Fix**                                                                                                                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Magic Strings**              | Hardcoded permissions (e.g., `if (role == "admin")`).                                                                                                                                                   | Use enums or a permissions database.                                                                                                                              |
| **Centralized Authorization**  | Single point of failure; hard to scale.                                                                                                                                                               | Decentralize (e.g., embed permissions in tokens).                                                                                                               |
| **Over-Permissive Tokens**      | Tokens with excessive scopes (e.g., `*` wildcards).                                                                                                                                                       | Issue scoped tokens; rotate frequently.                                                                                                                       |
| **No Fallback for Offline Mode**| Users lose access when the auth service is down.                                                                                                                                                         | Cache permissions locally (with TTL) or use offline-first auth (e.g., Service Workers).                                                                         |
| **Ignoring Rate Limits**       | Permission checks bypassed by brute-force attacks.                                                                                                                                                     | Rate-limit auth endpoints (e.g., [AWS WAF](https://aws.amazon.com/waf/) or [Cloudflare](https://www.cloudflare.com/rates/)).                                       |
| **Poorly Scoped Policies**      | Policies too broad (e.g., "All users can read all data").                                                                                                                                               | Use **least privilege**; test with [OWASP ZAP](https://www.zaproxy.org/).                                                                                         |

---
## **Performance Considerations**

| **Optimization**               | **Strategy**                                                                                                                                                                                                 | **Trade-offs**                                                                                                                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Caching Permissions**         | Cache user/role permissions in Redis/Memcached for N+1 query avoidance.                                                                                                                                     | Stale data risk; invalidate cache on role changes.                                                                                                                 |
| **Query Optimization**          | Index frequently queried fields (e.g., `user_id`, `role_id`). Use **materialized views** for complex ABAC rules.                                                                                          | Higher database overhead.                                                                                                                                         |
| **Token Size**                  | Minimize JWT claims to reduce token size (impacts latency).                                                                                                                                               | Trade-off with flexibility (e.g., nested roles).                                                                                                                 |
| **Batch Validation**           | Validate multiple permissions in a single call (e.g., `GET /permissions?user=101`).                                                                                                                         | Increases payload size; cache responses.                                                                                                                             |
| **Edge Evaluation**             | Offload auth checks to CDNs (e.g., Cloudflare Workers).                                                                                                                                                   | Latency if edge nodes are distant.                                                                                                                                  |

---
## **Example: Full API Authorization Flow (REST + RBAC)**
```
1. Client → POST /login (username/password)
   → Server validates credentials → Returns JWT with `roles: ["user", "editor"]`.

2. Client → GET /projects/42 (JWT in Authorization header)
   → API Gateway decodes JWT → Validates `editor` role can `read` projects.
   → Backend service checks resource ownership (optional ReBAC layer).
   → Returns project data if authorized.

3. Client → PUT /projects/42 (JWT + additional scope)
   → JWT must include `projects:write` scope → Server validates.
   → Audit log records: `user=101, action=update, resource=project:42, status=allowed`.
```

---

## **Further Reading**
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Google’s BeyondCorp Zero Trust](https://cloud.google.com/blog/products/security/beyondcorp-zero-trust)
- [AWS IAM Policy Examples](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples.html)
- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/latest/)

---
**Last Updated:** [Insert Date]
**Contributors:** [List Names]