**[Pattern] Authorization Configuration – Reference Guide**

---

# **[Pattern] Authorization Configuration Reference Guide**

---
## **Overview**
This pattern defines how to securely configure **role-based access control (RBAC)** and **attribute-based access control (ABAC)** in applications, APIs, and microservices. It ensures granular permission validation while minimizing latency and overhead. Proper configuration prevents unauthorized access and aligns with **least privilege principles**, common security frameworks (e.g., OAuth2, JWT, Open Policy Agent), and compliance standards (GDPR, SOC2).

Key considerations:
- **Decouple** authorization rules from business logic for maintainability.
- **Cache** permission checks when possible to reduce real-time lookups.
- **Validate inputs** (e.g., user IDs, roles) to prevent injection attacks.
- Use **introspectable policies** to debug misconfigurations.

This guide covers **configuration formats**, **schema validation**, **query examples**, and integrations with major authorization systems.

---

## **Schema Reference**

| **Component**          | **Description**                                                                                     | **Example Format**                                                                                     | **Validation Rules**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Roles**              | Defines user permissions as role objects.                                                          | ```{ "id": "admin", "permissions": ["read:users", "delete:posts"] }```                          | - `id`: UUID/string (no whitespace).                                                                 |
|                        |                                                                                                     |                                                                                                     | - `permissions`: Array of strings (glob-style wildcards allowed).                                        |
| **Users**              | Maps users to roles (e.g., via JWT claims, database lookup).                                         | ```{ "user_id": "123e4567", "roles": ["admin", "editor"] }```                                        | - `user_id`: Non-empty string.                                                                       |
|                        |                                                                                                     |                                                                                                     | - `roles`: Array of role IDs.                                                                          |
| **Policies**           | Attribute-based rules (e.g., "users in department X can edit Y").                                    | ```{ "condition": "req.user.department == 'engineering'", "access": "allow", "action": "edit:data" }``` | - `condition`: Valid JavaScript expression (sanitized).                                                  |
|                        |                                                                                                     |                                                                                                     | - `access`: `"allow"/"deny"` (case-insensitive).                                                       |
| **Policy Sets**        | Groups policies for modularity (e.g., `"core": [policy1, policy2]`).                               | ```{ "core": [ { "name": "delete-post", "condition": ... } ] }```                              | - Nested objects must follow schema.                                                                      |
| **API Endpoints**      | Maps HTTP methods/paths to required permissions.                                                     | ```{ "path": "/api/posts/:id", "methods": ["GET"], "required": ["read:posts"] }```          | - `methods`: Array of HTTP verbs (`GET`, `POST`, etc.).                                                |
| **Cache TTL**          | Defines how long permission checks are cached (in seconds).                                        | `{"cache_ttl": 300}` (applies to role/user lookups).                                                 | - `cache_ttl`: Integer ≥ 0.                                                                           |
| **Error Handling**     | Defines responses for failed authorization checks.                                                  | ```{ "on_failure": { "status": 403, "message": "Insufficient permissions" } }```                   | - `status`: HTTP 4xx/5xx codes.                                                                       |
|                        |                                                                                                     |                                                                                                     | - `message`: String (sanitized for XSS).                                                               |

---
## **Implementation Examples**

### **1. Role-Based Configuration (JSON)**
Configure roles and user assignments for an API gateway.

**Example (`config/authz.json`):**
```json
{
  "roles": [
    {
      "id": "admin",
      "permissions": [
        "*",          // Wildcard (all permissions)
        "create:users" // Explicit override
      ],
      "metadata": {
        "description": "Full admin access"
      }
    },
    {
      "id": "editor",
      "permissions": ["write:posts", "read:posts"]
    }
  ],
  "users": [
    {
      "user_id": "alice123",
      "roles": ["editor"],
      "metadata": { "department": "marketing" }
    }
  ],
  "cache_ttl": 60
}
```

**Key Notes:**
- Wildcards (`*`) are **evaluated last** (use explicit permissions for granularity).
- `metadata` can be referenced in ABAC policies (see below).

---

### **2. Attribute-Based Configuration (YAML)**
Define dynamic policies for a cloud service (e.g., AWS-like conditions).

**Example (`policies/access.yaml`):**
```yaml
policies:
  - name: "post_edit_allowed"
    description: "Edit posts if user owns them or is editor/developer."
    condition: |
      (req.user.id == post.author_id) ||
      (req.user.roles.contains("editor") || req.user.roles.contains("developer"))
    effect: "allow"
  - name: "dept_restricted"
    condition: "post.department == 'finance'"
    effect: "deny"  # Overrides other policies
```

**Integration with SQL (PostgreSQL):**
```sql
CREATE TABLE policies AS
SELECT * FROM jsonb_to_recordset('{
  "policies": [
    { "name": "post_edit_allowed", "condition": "...", "effect": "allow" }
  ]
}'::jsonb) WITH OIDS;
```

---

### **3. API Endpoint Mapping**
Map endpoints to required permissions (e.g., for an Express.js app).

**Example (`routes/authz.js`):**
```javascript
const authzConfig = {
  "/api/users": {
    methods: ["GET", "POST"],
    required: ["read:users", "create:users"]
  },
  "/api/posts/:id": {
    methods: ["PUT", "DELETE"],
    required: ["edit:posts"],
    cache_ttl: 120
  }
};

// Usage in middleware:
app.use((req, res, next) => {
  const requiredPerms = authzConfig[req.path].required;
  if (!hasPermissions(req.user.roles, requiredPerms)) {
    return res.status(403).json({ error: "Permission denied" });
  }
  next();
});
```

---

## **Query Examples**

### **1. Validate User Permissions (CLI Tool)**
Use `authz-cli` to check if a user has a permission:
```bash
authz-cli validate --config authz.json --user alice123 --perm write:posts
```
**Output:**
```json
{
  "user": "alice123",
  "permission": "write:posts",
  "allowed": true,
  "roles": ["editor"]
}
```

---

### **2. List Users with Specific Role (SQL)**
Query users assigned to the `admin` role:
```sql
SELECT user_id FROM users
WHERE jsonb_array_elements_text(roles) = 'admin';
```

---

### **3. Evaluate ABAC Policy**
Use **Open Policy Agent (OPA)** to enforce dynamic policies:
```rego
package authz

default allow = false

allow {
  input.user.roles[_] == "editor"
}

deny {
  input.action == "delete"
  input.resource.department == "finance"
}
```
**Query:**
```bash
opa eval --data=policy.rego --input=query.json authz.allow
```
**Input (`query.json`):**
```json
{
  "user": { "roles": ["editor"] },
  "action": "edit",
  "resource": { "department": "marketing" }
}
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Authentication](link)** | Manages user identity (e.g., JWT/OAuth2)                                                          | Before Authorization (authenticates users).                                                         |
| **[Rate Limiting](link)**  | Limits API calls to prevent abuse                                                                | Protects against brute-force attacks on auth endpoints.                                           |
| **[JWT Claims](link)**     | Embeds permissions in JWT tokens                                                                  | Stateless authorization for microservices.                                                          |
| **[Policy-as-Code](link)** | Stores policies in Git (e.g., Terraform, GitHub Actions)                                        | Compliance audit trails.                                                                        |
| **[Service Mesh](link)**   | Enforces auth via Istio/Linkerd                                                                  | Kubernetes-native RBAC.                                                                             |
| **[Audit Logging](link)**  | Logs auth decisions for forensic analysis                                                        | Compliance (GDPR, SOC2).                                                                           |

---

## **Best Practices**
1. **Separation of Concerns**:
   - Use **roles** for static permissions (e.g., `admin`).
   - Use **ABAC** for dynamic rules (e.g., time-based access).

2. **Performance**:
   - **Cache** role/user lookups (TTL: 60s–300s).
   - **Batch** permission checks for multiple endpoints.

3. **Security**:
   - **Sanitize** user input in ABAC conditions (e.g., prevent SQLi).
   - **Rotate** secrets (e.g., cache keys) periodically.

4. **Testing**:
   - **Unit tests**: Mock `hasPermission()` function.
   - **Integration tests**: Verify OPA/OPAL policies.

5. **Tooling**:
   - **Open Policy Agent (OPA)**: For advanced ABAC.
   - **Authzed**: Distributed RBAC.
   - **CASL.js**: Attribute-based for frontend apps.

---
## **Troubleshooting**
| **Issue**                  | **Solution**                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------|
| **403 Forbidden**          | Check `required` permissions in endpoint config vs. user roles.                                  |
| **Slow Response**          | Increase `cache_ttl` or optimize ABAC conditions.                                                |
| **Policy Mismatch**        | Use `opa test` or `authz-cli validate` to debug.                                                 |
| **Wildcard Overlap**       | Explicit permissions take precedence over wildcards (`*`).                                       |
| **Metadata Not Found**     | Ensure `user.metadata` is populated in JWT/database.                                            |

---
## **Example Workflow**
1. **User logs in** → JWT issued with `roles: ["editor"]`.
2. **Client requests `/api/posts/123` (PUT)** → Frontend attaches JWT.
3. **API checks**:
   - Config: `/api/posts/:id` requires `edit:posts`.
   - User’s roles include `editor` → `edit:posts` is allowed (via wildcard or explicit rule).
4. **Response**: `200 OK` (or `403` if permission denied).

---
## **References**
- [RFC 7519 (JWT)](https://tools.ietf.org/html/rfc7519)
- [Open Policy Agent Docs](https://www.openpolicyagent.org/)
- [Authzed RBAC](https://authzed.com/)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)