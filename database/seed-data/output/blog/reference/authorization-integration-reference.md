# **[Pattern] Authorization Integration – Reference Guide**
*Securely enforce access control across your application ecosystem.*

---

## **Overview**
The **Authorization Integration** pattern ensures that permissions, roles, and policies are consistently enforced across microservices, APIs, and third-party integrations. By centralizing or federating authorization logic, this pattern reduces redundant checks, improves security, and simplifies compliance. It’s critical for systems requiring fine-grained access control (e.g., SaaS platforms, multi-tenant apps, or IoT device management).

Common use cases include:
- **API Gateways**: Validating JWT/OAuth tokens from downstream services.
- **Headless CMS/CRM Integrations**: Enforcing read/write permissions for third-party data.
- **Multi-tenant SaaS**: Dynamic tenant-specific authorization rules.
- **Identity Federation**: Synchronizing roles from IdP (Identity Provider) like Okta or Azure AD.

---

## **Key Concepts**
| Term               | Definition                                                                                     | Example                                                                 |
|--------------------|---------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Policies**       | Rules defining what operations are allowed (e.g., `can_edit_tenant_x`).                     | `require(role: "admin").allow(operation: "delete")`                     |
| **Token Claims**   | Data embedded in JWT/OAuth tokens (e.g., `user_id`, `permissions`).                         | `{"scp": "profile:read profile:write"}` (OpenID Connect Scopes)          |
| **Policy Store**   | Centralized or distributed db storing policies (e.g., Redis, PostgreSQL, or model files).   | [CASL](https://casl.js.org/) policy definitions                           |
| **Decision API**   | Service evaluating if a request should be allowed/denied.                                     | `/api/authorize` endpoint returning `{"allowed": true, "reason": "..."}` |
| **RBAC**           | Role-Based Access Control (e.g., `editor`, `auditor`).                                        | User `"alice"` assigned role `"editor"` grants `can_update_posts`.       |
| **ABAC**           | Attribute-Based Access Control (e.g., `dept == "finance" && role == "analyst"`).             | Access granted if `user.department = "finance"` **and** `user.role = "analyst"`. |

---

## **Schema Reference**
### **1. Policy Definition Schema (Example: JSON)**
| Field          | Type     | Description                                                                 | Required | Example Value                     |
|----------------|----------|-----------------------------------------------------------------------------|----------|------------------------------------|
| `id`           | String   | Unique identifier for the policy.                                           | Yes      | `"can_edit_posts_v1"`               |
| `target`       | Object   | Defines what the policy applies to (e.g., resource type/ID).                | Yes      | `{"type": "Post", "id": "123"}`     |
| `action`       | String   | Allowed operation (e.g., `create`, `update`).                               | Yes      | `"update"`                          |
| `conditions`   | Object   | ABAC-style attributes (e.g., time, department).                            | No       | `{"time": "before noon", "dept": "marketing"}` |
| `roles`        | Array    | RBAC roles that satisfy the policy.                                        | No       | `["editor", "admin"]`              |
| `permissions`  | Array    | Explicit permission strings (e.g., `"posts.update"`).                      | No       | `["posts:read", "posts:write"]`    |

**Example Policy (JSON):**
```json
{
  "id": "edit_post_as_editor",
  "target": {"type": "Post", "id": "456"},
  "action": "update",
  "roles": ["editor", "author"],
  "conditions": {"status": "published"}
}
```

---

### **2. Token Claim Schema**
| Field            | Type     | Description                                                                 | Example Value                     |
|------------------|----------|-----------------------------------------------------------------------------|------------------------------------|
| `sub`            | String   | Subject (user/device ID).                                                   | `"user_789"`                       |
| `aud`            | String   | Audience (API/service name).                                               | `"api.apps.example.com"`           |
| `exp`            | Number   | Expiration timestamp (UNIX epoch).                                         | `1712345678`                       |
| `permissions`    | Array    | Granted permissions (scope-like).                                          | `["posts:read", "comments:delete"]`|
| `roles`          | Array    | Assigned roles.                                                             | `["editor", "freelancer"]`         |
| `tenant_id`      | String   | Multi-tenant context.                                                      | `"org_abc123"`                     |

**Example Token Payload:**
```json
{
  "sub": "user_789",
  "permissions": ["posts:read", "comments:delete"],
  "roles": ["editor"],
  "exp": 1712345678,
  "tenant_id": "org_abc123"
}
```

---

### **3. Authorization Decision Response**
| Field          | Type     | Description                                                                 | Example                     |
|----------------|----------|-----------------------------------------------------------------------------|-----------------------------|
| `allowed`      | Boolean  | Whether the request is permitted.                                          | `true`/`false`              |
| `reason`       | String   | Human-readable explanation (or error code).                                 | `"Missing role 'admin'."`   |
| `expires_at`   | Number   | Time (UNIX) when the decision becomes invalid (e.g., due to token rotation).| `1712346000`                 |
| `policy_ids`   | Array    | IDs of policies evaluated (for audit logs).                                | `["edit_post_as_editor"]`    |

**Example Response:**
```json
{
  "allowed": true,
  "reason": "User has role 'editor' and permission 'posts:update'.",
  "expires_at": 1712346000,
  "policy_ids": ["edit_post_as_editor"]
}
```

---

## **Query Examples**
### **1. Check Policy via API**
**Request:**
```http
POST /api/authorize
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "request": {
    "action": "update",
    "target": {"type": "Post", "id": "456"}
  }
}
```

**Response (Allowed):**
```json
{
  "allowed": true,
  "reason": "Token has role 'editor' and permission 'posts:update'.",
  "policy_ids": ["edit_post_as_editor"]
}
```

**Response (Denied):**
```json
{
  "allowed": false,
  "reason": "Permission 'posts:update' not found in token claims.",
  "policy_ids": ["edit_post_as_editor"]
}
```

---

### **2. Dynamically Load Policies (e.g., from Redis)**
**Pseudo-code (Node.js):**
```javascript
const { authorize } = require("./authorizer");

// Load policy from cache
const policy = await redis.get(`policy:edit_post_as_editor`);
if (!policy) throw new Error("Policy not found");

// Check authorization
const decision = authorize({
  tokenClaims: parsedToken,
  policy: JSON.parse(policy),
  request: { action: "update", target: { type: "Post", id: "456" } }
});
```

---
### **3. Federated Authorization (IdP Sync)**
**Example: Sync Okta Roles to Your System**
```bash
# Use Okta API to fetch user roles
curl --request GET \
     --url 'https://{okta-domain}/api/v1/users/{user-id}/roles' \
     --header 'Authorization: Bearer {okta-token}'

# Map roles to your internal RBAC system
{
  "okta_roles": ["app:editor", "app:admin"],
  "mapped_roles": ["editor", "admin"]
}
```

---

## **Implementation Patterns**
### **1. Centralized Policy Store**
- **Pros**: Single source of truth, easy auditing.
- **Cons**: Bottleneck if policies are frequently updated.
- **Tools**: PostgreSQL, Redis, or [OPA (Open Policy Agent)](https://www.openpolicyagent.org/).

**Example OPA Policy (ReGo):**
```rego
default allow = false

allow {
  input.action == "update"
  input.target.type == "Post"
  input.user.roles[_] == "editor"
}
```

---

### **2. Distributed Policy Agents**
- **Pros**: Scalable, low-latency decisions.
- **Cons**: Eventual consistency challenges.
- **Tools**: [Casbin](https://casbin.org/), [Styra DAS](https://www.styra.com/).

**Casbin Policy File (RBAC):**
```
p, admin, /api/, update
g, alice, editor
p, editor, /api/posts/{id}, update
```

---

### **3. Hybrid Approach (Policy-as-Code)**
- Embed policies in app code (e.g., TypeScript enums) for default rules.
- Override with centralized store for tenant-specific needs.

**Example (TypeScript):**
```typescript
enum DefaultPermissions {
  POSTS_READ = "posts:read",
  COMMENTS_DELETE = "comments:delete"
}

const tenantSpecificPolicies = {
  "org_abc123": [
    { target: "posts", action: "delete", roles: ["admin"] }
  ]
};
```

---

## **Query Examples for Common Scenarios**
### **Scenario 1: API Gateway Authorization**
**Request Flow:**
1. Client → **API Gateway** (JWT validated via `aud` claim).
2. Gateway calls `/api/authorize` with token and request details.
3. Decision enforces **ABAC** (e.g., `tenant_id` + `action`).

**API Gateway Config (Kong):**
```yaml
plugins:
  - name: request-transformer
    config:
      remove: ["Authorization"]
  - name: jwt
    config:
      claim_name: "sub"
  - name: authorization
    config:
      upstream_url: "http://authorizer-service/authorize"
      policy_ttl: 300
```

---

### **Scenario 2: Database-Level Enforcement**
**PostgreSQL Row-Level Security (RLS):**
```sql
-- Enable RLS on 'posts' table
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Policy: Allow updates if user is post author
CREATE POLICY user_can_edit_post ON posts
  USING (author_id = current_setting('app.user_id')::uuid);
```

**Sync with Authorization Service:**
```sql
-- Fetch user_id from JWT in app (e.g., via middleware)
SET LOCAL app.user_id = jsonb_extract_path_text(jwt_claims, 'sub');
```

---

### **Scenario 3: Real-Time Updates (WebSockets)**
**WebSocket Authorization Middleware (Python/FastAPI):**
```python
from fastapi import WebSocket

async def authorize_socket(websocket: WebSocket, token: str):
    claims = jwt.decode(token, options={"verify_signature": False})
    decision = await authorizer.check(
        user=claims["sub"],
        action="subscribe",
        target={"channel": "notifications"}
    )
    if not decision.allowed:
        await websocket.close(code=403)
```

---

## **Error Handling & Logging**
| Code   | Meaning                     | Example Response Body                          |
|--------|-----------------------------|------------------------------------------------|
| `401`  | Unauthorized (invalid token)| `{"error": "Missing or invalid token."}`       |
| `403`  | Forbidden                   | `{"error": "Permission 'posts:update' denied."}`|
| `429`  | Rate-limited                | `{"error": "Too many policy checks."}`          |
| `500`  | Policy evaluation failed    | `{"error": "Internal policy error."}`           |

**Audit Log Structure:**
```json
{
  "timestamp": "2024-05-20T12:00:00Z",
  "user_id": "user_789",
  "ip": "192.168.1.1",
  "action": "update",
  "target": {"type": "Post", "id": "456"},
  "decision": "denied",
  "reason": "Missing role 'admin'.",
  "policy_ids": ["edit_post_admin_only"]
}
```

---

## **Performance Considerations**
| Technique                | Description                                                                 | Best For                          |
|--------------------------|-----------------------------------------------------------------------------|------------------------------------|
| **Caching Decisions**    | Store results of common checks (e.g., Redis).                              | High-throughput APIs.              |
| **Local Policy Cache**   | Pre-load policies for offline decision-making (e.g., mobile apps).        | Edge cases (e.g., IoT devices).    |
| **Async Policy Checks**  | Non-blocking calls to policy service (e.g., gRPC streams).                | Long-running workflows.            |
| **Token Claims Validation** | Validate `sub`, `iat`, `exp` before policy checks.                      | Latency-sensitive paths.           |

---

## **Security Best Practices**
1. **Token Rotation**: Short-lived tokens (e.g., 15-minute `exp` claims).
2. **Policy Sandboxing**: Isolate policy evaluation from business logic (e.g., OPA).
3. **Audit Trails**: Log all deny decisions (compliance requirement).
4. **Limited Scope**: Avoid wildcard permissions (e.g., `*:*`) in tokens.
5. **Zero Trust**: Assume breach; require re-authentication for sensitive actions.

---

## **Related Patterns**
| Pattern                      | Description                                                                 | Integration Point                          |
|------------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **[JWT Validation]**         | Verify token signatures and claims before authorization.                   | Precedes `Authorization Integration`.        |
| **[API Gateway]**            | Routes and authorizes requests before reaching services.                    | Uses `Authorization Integration` as plugin. |
| **[Multitenancy]**           | Isolates tenant data/data policies.                                         | Policies include `tenant_id` in conditions. |
| **[Rate Limiting]**          | Throttles requests per user/permission.                                     | Combines with `429 Forbidden` responses.    |
| **[Event-Driven Auth]**      | Uses webhooks/events for dynamic permission updates (e.g., role changes). | Asynchronous policy refresh.               |

---

## **Tools & Libraries**
| Tool/Library               | Description                                                                 | Language/Platform          |
|----------------------------|-----------------------------------------------------------------------------|----------------------------|
| [CASL](https://casl.js.org/) | Authorization library for fine-grained rules.                             | JavaScript/TypeScript      |
| [Casbin](https://casbin.org/) | Enforce policies in ABAC/RBAC.                                             | Go, Java, Python, etc.     |
| [OPA](https://www.openpolicyagent.org/) | Policy-as-code engine (e.g., Kubernetes RBAC).                           | Rego language               |
| [Styra DAS](https://www.styra.com/) | Cloud-native policy management.                                          | Multi-language              |
| [AWS IAM](https://aws.amazon.com/iam/) | Managed RBAC for AWS services.                                             | AWS                         |
| [Okta/OAuth2](https://developer.okta.com/) | Identity federation with scopes/roles.                                     | Multi-language SDKs         |

---
## **Troubleshooting**
| Issue                          | Diagnosis Steps                                                                 | Solution                                                                 |
|---------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **403 Forbidden**               | Check token claims for missing permissions/roles.                               | Issue new token with required scopes or update policy.                   |
| **Slow Policy Checks**          | Policy store latency or complex ABAC conditions.                               | Cache decisions or simplify policies.                                     |
| **Token Claims Mismatch**       | IdP (e.g., Okta) not emitting correct roles/scopes.                            | Verify IdP config and token payload.                                       |
| **Policy Drift**                | Policies out of sync between dev/staging/prod.                                | Use infrastructure-as-code (e.g., Terraform) for policy deployment.       |

---
**Appendix: Glossary**
- **ABAC**: Attribute-Based Access Control (e.g., `dept = "finance"`).
- **RBAC**: Role-Based Access Control (e.g., `role = "admin"`).
- **JWT**: JSON Web Token (standard for stateless auth).
- **IdP**: Identity Provider (e.g., Okta, Azure AD).
- **Policy Agent**: Service evaluating authorization decisions.