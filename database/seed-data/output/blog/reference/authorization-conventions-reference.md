---
# **[Pattern] Authorization Conventions Reference Guide**

---

## **Overview**
**Authorization Conventions** standardizes how applications enforce access control across microservices and APIs by defining convention-based rules for role assignments, permission validation, and granular permission checks. This pattern ensures consistency in security policies while allowing flexibility for custom domain-specific logic. It maps business roles to technical permissions (e.g., `Admin` → `read:dashboard, write:users`) and enforces these rules via declarative configurations (e.g., YAML, feature flags, or annotation-based metadata). By centralizing conventions, teams avoid reinventing security logic and simplify auditing and policy updates.

Key benefits include **reduced boilerplate**, **consistent RBAC (Role-Based Access Control)**, and **scalable access management** for distributed systems.

---

## **Key Concepts**

### **1. Core Components**
| Component               | Description                                                                                                                                                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Role-Tier Mapping**   | Maps business roles (e.g., `Editor`, `Viewer`) to technical tiers (e.g., `read`, `write`, `admin`). Example: `Editor` → `read:content, write:content, delete:own_posts`.                          |
| **Permission Granularity** | Defines scope (e.g., resource type: `post`, `user`; actions: `create`, `update`; conditions: `owner-only`).                                                                                          |
| **Convention Annotations** | Metadata tags (e.g., `@Authorize(role="Editor", action="create", resource="post")`) or YAML configs to attach permissions to endpoints/modules.                                                    |
| **Policy Engine**       | Evaluates permissions against request attributes (e.g., `user.role`, `request.method`) using a centralized logic layer (e.g., Spring Security, OPA/Gatekeeper, or custom predicates).            |
| **Audit Trail**         | Logs permission checks and denials (e.g., `User X failed to access Y due to missing [role:Viewer, action:write]`).                                                                                          |
| **Feature Flags**       | Temporarily overrides or defines permissions (e.g., `disable_read_permission:content` for maintenance).                                                                                                    |

---

### **2. Implementation Flow**
1. **Define Roles/Tiers**: Align business roles with technical actions (e.g., `Admin` → `*` for full access).
2. **Annotate Resources**: Apply conventions to APIs/modules via metadata (e.g., OpenAPI/Swagger tags or code annotations).
3. **Validate Requests**: The policy engine cross-references user roles against annotated permissions during runtime.
4. **Handle Denials**: Return standardized error codes (e.g., `403 Forbidden`) with audit logs.
5. **Update Dynamically**: Modify permissions via configs (e.g., Kubernetes ConfigMaps) without redeploying code.

---

## **Schema Reference**

### **1. Role-Tier Mapping Schema**
| Field          | Type       | Description                                                                                     | Example                          |
|----------------|------------|-------------------------------------------------------------------------------------------------|----------------------------------|
| `role`         | String     | Business role (e.g., `Editor`, `Guest`).                                                        | `"Editor"`                       |
| `tier`         | String[]   | Array of technical actions (see [Actions Schema](#2-actions-schema)).                          | `["read:content", "write:own"]`  |
| `conditions`   | Object     | Optional constraints (e.g., `ownerOnly: true`).                                                 | `{"ownerOnly": true}`             |

**Example:**
```yaml
roles:
  - role: "Editor"
    tier:
      - "read:*"
      - "write:content"
      - "delete:own_posts"
    conditions: { "region": "us-west" }
```

---

### **2. Actions Schema**
| Field          | Type       | Description                                                                                     | Example                          |
|----------------|------------|-------------------------------------------------------------------------------------------------|----------------------------------|
| `action`       | String     | CRUD operation (`read`, `write`, `delete`, `execute`).                                           | `"write"`                        |
| `resource`     | String     | Entity type (e.g., `post`, `project`).                                                          | `"post"`                         |
| `wildcard`     | Boolean    | `true` for global access (e.g., `read:*`).                                                      | `true` (implicit if `*` used)    |
| `scope`        | String[]   | Optional filters (e.g., `["user", "team"]`).                                                    | `["user"]`                       |

**Examples:**
- `read:content` → Read any `content`.
- `write:own_posts` → Write only posts owned by the user.
- `delete:*` → Delete any resource (admin-only).

---

### **3. Annotations Schema**
| Field          | Type       | Description                                                                                     | Example                          |
|----------------|------------|-------------------------------------------------------------------------------------------------|----------------------------------|
| `@Authorize`   | Object     | Applied to endpoints/modules.                                                                   | `@Authorize(role="Editor")`      |
| `role`         | String[]   | Required roles.                                                                                 | `["Editor", "Admin"]`             |
| `action`       | String     | CRUD action required.                                                                           | `"write"`                        |
| `resource`     | String     | Target resource.                                                                               | `"project"`                      |
| `conditions`   | Object     | Additional checks (e.g., `timeOfDay` restrictions).                                             | `{"timeOfDay": "9am-5pm"}`       |

**Code Example (Java/Spring):**
```java
@PostMapping("/projects")
@Authorize(role = "Editor", action = "create", resource = "project")
public ResponseEntity<Project> createProject(@RequestBody Project project) { ... }
```

**OpenAPI Example:**
```yaml
paths:
  /posts/{id}:
    patch:
      summary: Update a post
      security:
        - bearerAuth: []
      x-authorize:
        - role: "Editor"
          action: "update"
          resource: "post"
          conditions: { "ownerId": "$auth.userId" }
```

---

### **4. Policy Engine Configuration**
| Field          | Type       | Description                                                                                     | Example                          |
|----------------|------------|-------------------------------------------------------------------------------------------------|----------------------------------|
| `defaultRole`  | String     | Fallback role for unauthenticated users.                                                          | `"Guest"`                        |
| `denyPolicy`   | String     | `allow` (default) or `deny` (least privilege).                                                   | `"allow"`                        |
| `fallbackTo*`  | Boolean    | If `true`, wildcard roles (e.g., `read:*`) override strict checks.                                | `false`                          |
| `auditLog`     | Boolean    | Enable detailed permission logs.                                                                 | `true`                           |

**Example (OPA/Gatekeeper Policy):**
```rego
package authz

default allow = false

# Allow if user role has the required action
allow {
  input.user.role in roles[_]
  role.tier[_] == input.action
}
```

---

## **Query Examples**

### **1. Check Permission via API**
**Request:**
```http
GET /api/permissions?user=john&resource=post&action=write
Headers:
  Authorization: Bearer <token>
```
**Response (200 OK):**
```json
{
  "authorized": true,
  "validRoles": ["Editor", "Admin"],
  "conditionsMet": true
}
```

**Response (403 Forbidden):**
```json
{
  "error": "Forbidden",
  "missingRole": "Editor",
  "requiredAction": "write",
  "resource": "post"
}
```

---

### **2. Dynamic Permission Override (Feature Flags)**
**Request:**
```yaml
# ConfigMap override (Kubernetes)
apiVersion: v1
kind: ConfigMap
metadata:
  name: auth-override
data:
  permissions: |
    - role: "Editor"
      tier:
        - "write:content"  # Temporarily disabled
    - role: "Guest"
      tier:
        - "read:public_posts"
```

**Effect**: Users with `Editor` roles cannot write to `content` until the override is removed.

---

### **3. Audit Log Query**
**Request (gRPC):**
```proto
service AuditService {
  rpc GetPermissionDenials(filter: AuditFilter) returns (AuditLog);
}

message AuditFilter {
  string resource = 1;
  string role = 2;
  string timestamp = 3;  // ISO 8601 format
}
```
**Response Example:**
```json
[
  {
    "timestamp": "2023-10-01T12:00:00Z",
    "user": "alice",
    "resource": "dashboard",
    "action": "read",
    "deniedRole": "Viewer",
    "reason": "Missing permission 'read:dashboard'"
  }
]
```

---

## **Implementation Steps**

### **1. Define Role-Tier Mapping**
```bash
# Example YAML (roles.yml)
---
roles:
  - role: "Guest"
    tier: ["read:public_posts"]
  - role: "Viewer"
    tier:
      - "read:*"
      - "write:own_posts"
    conditions: { "verified": true }
```

### **2. Annotate Code/APIs**
**Option A: Code Annotations (Java/Spring)**
```java
@RestController
@RequestMapping("/api/posts")
public class PostController {

  @PostMapping
  @Authorize(role = "Editor", action = "create", resource = "post")
  public Post createPost(@RequestBody Post post) { ... }
}
```

**Option B: OpenAPI/Swagger**
```yaml
# openapi.yml
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer }
paths:
  /posts/{id}:
    delete:
      security: [ bearerAuth ]
      x-authorize:
        - role: "Editor"
          action: "delete"
          resource: "post"
          conditions: { "ownerId": "$auth.userId" }
```

### **3. Integrate Policy Engine**
- **Option A: Spring Security**
  Add `AuthorizationConventionFilter` as a beans post-processor:
  ```java
  @Bean
  public AuthorizationConventionFilter authorizationFilter() {
    return new AuthorizationConventionFilter(rolesConfig, resourceHandlers);
  }
  ```
- **Option B: Open Policy Agent (OPA)**
  Deploy OPA with a custom plugin that validates against your conventions:
  ```bash
  opa run --server --plugin=authz-plugin
  ```

### **4. Enable Auditing**
```java
@Configuration
public class AuditConfig {

  @Bean
  public PermissionAuditAspect auditAspect() {
    return new PermissionAuditAspect(auditService);
  }
}
```

---

## **Error Handling**

| Code | Description                     | Example Response Body                                                                 |
|------|---------------------------------|---------------------------------------------------------------------------------------|
| 401  | Unauthenticated                 | `{ "error": "Unauthorized", "type": "auth" }`                                         |
| 403  | Permission Denied               | `{ "error": "Forbidden", "missingRole": "Editor", "resource": "post" }`              |
| 422  | Invalid Permission Request      | `{ "error": "InvalidPermissions", "_detail": "Action 'admin' not allowed for role 'Viewer'" }` |
| 500  | Policy Engine Error             | `{ "error": "InternalServerError", "detail": "Policy evaluation failed" }`         |

---

## **Related Patterns**

### **1. Role-Based Access Control (RBAC)**
- **Relation**: Authorization Conventions extends RBAC by standardizing how roles map to technical permissions across services.
- **Key Difference**: RBAC defines roles hierarchically (e.g., `Admin > Editor`), while Conventions focus on **how** roles map to actions/resources.

### **2. Attribute-Based Access Control (ABAC)**
- **Relation**: Conventions can implement ABAC by embedding attributes (e.g., `conditions: { "department": "marketing" }`) into permission checks.
- **Key Difference**: ABAC is dynamic and contextual; Conventions provide a structured way to enforce ABAC-like rules declaratively.

### **3. Service Mesh (e.g., Istio, Linkerd)**
- **Relation**: Service meshes can enforce Conventions via sidecar proxies (e.g., JWT validation + permission checks).
- **Use Case**: Useful for API gateways or service-to-service auth where conventions are applied at the network layer.

### **4. Open Policy Agent (OPA)**
- **Relation**: OPA can act as the **policy engine** for Conventions, evaluating permissions against Rego policies.
- **Example**: Store Conventions in OPA bundles for zero-trust enforcement.

### **5. Feature Flags (e.g., LaunchDarkly, Flagsmith)**
- **Relation**: Feature flags can **overwrite or extend** Conventions temporarily (e.g., disable permissions during maintenance).
- **Example**: Toggle `read:dashboard` for all users via a feature flag.

### **6. API Gateways (e.g., Kong, Apigee)**
- **Relation**: Gateways can validate Conventions at the edge, reducing load on downstream services.
- **Implementation**: Use Kong’s [Plugin API](https://docs.konghq.com/hub/plugins/) to insert Permission checks.

### **7. Zero Trust Architecture**
- **Relation**: Conventions align with zero-trust principles by enforcing **least privilege** and **context-aware access**.
- **Practice**: Combine with [Just-In-Time (JIT) Access](https://www.zerotrustnetwork.com/glossary/just-in-time-access-jita) for dynamic permissions.

---

## **Best Practices**

### **1. Granularity**
- **Do**: Use wildcards sparingly (e.g., `read:*` for Admins). Prefer explicit permissions (e.g., `read:dashboard`, `read:reports`).
- **Avoid**: `*` in `resource` fields unless necessary (e.g., `delete:*` for Admins).

### **2. Role Naming**
- **Convention**: Use lowercase with underscores (`viewer_document`, not `ViewerDocument`).
- **Hierarchy**: Prefix roles with tiers (e.g., `admin_*` for admin-only actions).

### **3. Conditions**
- **Structure**: Group conditions by resource/type (e.g., `ownerOnly`, `timeRestricted`).
- **Fallbacks**: Define default behaviors (e.g., `deny` if conditions are missing).

### **4. Testing**
- **Unit Tests**: Mock the policy engine to test permission logic.
  ```java
  @Test
  public void testEditorCanWriteOwnPosts() {
    assertTrue(permissionChecker.hasPermission("Editor", "write", "post", Map.of("ownerId", "123")));
  }
  ```
- **Integration Tests**: Verify API endpoints reject unauthorized requests.
  ```bash
  curl -X POST /api/posts -H "Authorization: Bearer invalid-token" # Should return 403
  ```

### **5. Documentation**
- **Ensure**: Role-Tier mappings are documented in a central repo (e.g., [Confluent’s Access Control](https://docs.confluent.io/platform/current/security/access-control.html)).
- **Tools**: Use tools like [Postman Collections](https://learning.postman.com/docs/sending-requests/collections/) to document annotated endpoints.

### **6. Performance**
- **Optimize**: Cache permission checks for frequently accessed resources.
- **Async**: Offload validation to a sidecar or OPA for high-latency tolerance.

### **7. Audit and Compliance**
- **Log**: Track all permission denials with user/IP context.
- **GDPR**: Anonymize audit logs for personal data (e.g., replace user IDs with tokens).

---

## **Anti-Patterns**

| Anti-Pattern                          | Problem                                                                 | Mitigation                                                                 |
|---------------------------------------|-------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **Hardcoded Permissions**             | Magic strings in code (e.g., `if (userRole == "Admin")`).               | Use annotations/YAML configs.                                              |
| **Overly Permissive Wildcards**       | `read:*` for all roles leads to security gaps.                           | Enforce strict defaults; use wildcards only for Admins.                   |
| **Ignoring Conditions**               | Skipping `conditions` leads to brittle permissions (e.g., `ownerOnly`). | Validate conditions in all checks.                                          |
| **Policy Engine Monolith**            | Centralizing all logic in one service creates a single point of failure.| Decouple policy evaluation (e.g., OPA, sidecars).                           |
| **No Audit Trail**                    | Unable to trace unauthorized access attempts.                            | Enable auditing from day one.                                              |
| **Dynamic Roles Without Fallbacks**   | Feature flags override static roles unpredictably.                      | Document fallback roles and test edge cases.                               |

---
## **Tools and Libraries**
| Tool/Library               | Purpose                                                                 | Example Use Case                                      |
|----------------------------|-------------------------------------------------------------------------|-------------------------------------------------------|
| **Spring Security**        | Java-based policy engine with annotation support.                       | Annotate Spring Boot endpoints.                      |
| **Open Policy Agent (OPA)**| Declarative policy language (Rego) for zero-trust enforcement.          | Evaluate Conventions in Kubernetes with Gatekeeper.   |
| **Kong/Apigee**            | API gateways to validate permissions at ingress.                        | Block unauthorized requests before they reach microservices. |
| **LaunchDarkly**           | Feature flags to override permissions dynamically.                       | Disable `write:content` for all Editor roles.      |
| **JWT/OAuth2 Tools**       | Token validation with embedded roles (e.g., `sub`, `roles` claims).     | Use `Authorization: Bearer <token>` headers.         |
| **Serilog/ELK Stack**      | Centralized logging for audit trails.                                    | Query denied permissions in Kibana.                   |

---
## **When to Use This Pattern**
- **Use When**:
  - You have **multiple microservices** with inconsistent auth logic.
  - You need **scalable RBAC** without custom code per service.
  - You require **auditability** for compliance (e.g., SOC2, GDPR).
  - You want to **reduce boilerplate** (e.g., no duplicate permission checks).
- **Avoid When**:
  - Permissions are **truly dynamic** (e.g., real-time game balance updates). Use ABAC instead.
  - Your stack **lacks metadata support** (e.g., legacy monoliths without annotations).
  - Teams **resist declarative configs** (e.g., prefer runtime logic over YAML).

---
## **Example Workflow: E-Commerce Platform**
1. **Roles**:
  