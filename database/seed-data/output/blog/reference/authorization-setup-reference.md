**[Pattern] Authorization Setup: Reference Guide**

---

### **Overview**
The **Authorization Setup** pattern defines a structured approach to configuring fine-grained access control for users, services, and resources within an application. This pattern ensures that permissions are systematically assigned, validated, and enforced, reducing security risks while maintaining flexibility. It integrates with authentication mechanisms (e.g., JWT, OAuth) to grant or deny access based on roles, scopes, or attribute-based policies. Key use cases include:
- Multi-tenancy applications
- Microservices with cross-cutting security needs
- APIs exposing sensitive data
- Hybrid environments combining on-prem and cloud services

This guide covers the core components, schema, implementation steps, and query examples for setting up authorization effectively.

---

### **Key Concepts**
The pattern relies on three foundational elements (visualized in the schema below):

1. **Resource Definitions** – Specifies what can be accessed (e.g., `/users`, `/api/orders/#{id}`).
2. **Permission Policies** – Rules defining allowed actions (e.g., `GET`, `POST`, `UPDATE`) on resources.
3. **Subjects** – Entities (users, services) bound to policies via roles or claims.

---

### **Schema Reference**
The following table outlines the data model for the pattern.

| **Entity**               | **Attributes**                          | **Description**                                                                 |
|--------------------------|-----------------------------------------|---------------------------------------------------------------------------------|
| **Resource**             | `id` (UUID), `name` (string), `path` (string), `type` (e.g., "Collection", "Document") | Unique identifier, human-readable name, endpoint path, and resource category. Example: `{"id": "res_123", "name": "Orders", "path": "/api/orders"}`. |
| **Action**               | `id` (UUID), `name` (e.g., "read", "write"), `description` (optional) | Standardized verbs for operations (e.g., `GET` maps to "read").                |
| **Permission**           | `id` (UUID), `resource_id` (UUID), `action_id` (UUID), `scope` (optional) | Combines resource + action; scope may restrict to subsets (e.g., `scope: "premium"`). |
| **Role**                 | `id` (UUID), `name` (string), `description` (optional) | Logical grouping of permissions (e.g., "Admin", "Editor").                     |
| **Role-Permission Mapping** | `role_id` (UUID), `permission_id` (UUID) | Links roles to specific permissions (many-to-many).                           |
| **Subject**              | `id` (UUID), `type` (e.g., "User", "ServiceAccount"), `identifier` (string) | Represents a user or service (e.g., `{"type": "User", "identifier": "user_456"}`). |
| **Subject-Role Assignment** | `subject_id` (UUID), `role_id` (UUID)    | Assigns roles to subjects (e.g., user `user_456` has role `editor_789`).          |

---
### **Query Examples**
Below are common operations to configure authorization (using a hypothetical API or database schema).

#### 1. **Define a Resource**
```sql
-- Create a resource for user profiles
INSERT INTO resources (id, name, path, type)
VALUES ('res_100', 'User Profiles', '/api/profiles', 'Collection');
```

#### 2. **Create Permissions**
```sql
-- Allow "read" and "write" on user profiles
INSERT INTO permissions (id, resource_id, action_id)
VALUES
  ('perm_101', 'res_100', 'act_001'),  -- read
  ('perm_102', 'res_100', 'act_002');  -- write
```

#### 3. **Map Permissions to a Role**
```sql
-- Create the "Editor" role and assign permissions
INSERT INTO roles (id, name)
VALUES ('role_002', 'Editor');

-- Link permissions to the role
INSERT INTO role_permission (role_id, permission_id)
VALUES
  ('role_002', 'perm_101'),  -- Editor can read
  ('role_002', 'perm_102');  -- Editor can write
```

#### 4. **Assign a Role to a Subject**
```sql
-- Grant the "Editor" role to user_id=456
INSERT INTO subject_role (subject_id, role_id)
VALUES ('sub_456', 'role_002');
```

#### 5. **Query Authorized Actions for a Subject**
```sql
-- Check which permissions user_456 has via JOINs
SELECT a.name AS action
FROM subject_role sr
JOIN roles r ON sr.role_id = r.id
JOIN role_permission rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
JOIN actions a ON p.action_id = a.id
WHERE sr.subject_id = 'sub_456';
```

#### 6. **Validate Access Programmatically (Pseudocode)**
```python
def check_permission(request):
    token = extract_jwt(request)
    subject_id = token.user_id  # from JWT claims
    resource_path = request.path

    # Fetch assigned permissions for the subject
    permissions = db.query("""
        SELECT a.name
        FROM subject_role sr
        JOIN roles r ON sr.role_id = r.id
        JOIN role_permission rp ON r.id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        JOIN actions a ON p.action_id = a.id
        WHERE sr.subject_id = %s
    """, [subject_id])

    # Check if requested action exists in permissions
    requested_action = request.method.lower()
    allowed = any(p["name"] == requested_action for p in permissions)
    return {"authorized": allowed, "permissions": permissions}
```

---

### **Implementation Considerations**
1. **Policy Granularity**:
   - Avoid overly broad permissions (e.g., wildcard paths). Use specific resource paths.
   - Use **scopes** (e.g., `scope: "premium"`) for environment-specific rules.

2. **Performance**:
   - Cache role-permission mappings to reduce runtime queries.
   - Index frequently queried fields (e.g., `subject_id` in `subject_role`).

3. **Dynamic Assignment**:
   - Support role assignment via APIs (e.g., `/admin/roles/subject/{id}`) for self-service.
   - Use **attribute-based access control (ABAC)** for flexible conditions (e.g., `if user.department == "Finance"`).

4. **Audit Logging**:
   - Track role assignments and permission changes via a separate `audit_log` table.

5. **Integration with Auth**:
   - Extend JWT/OAuth tokens to include role/permission claims for stateless validation.

---

### **Query Examples (Alternative: GraphQL)**
For GraphQL APIs, use directives or custom fields to enforce authorization:

```graphql
type Query {
  user(id: ID!): User @authorize(requires: ["read:profiles"])
}
```

**Resolver Logic**:
```javascript
resolve: async (parent, args, context) => {
  const user = await db.getUser(args.id);
  if (!context.user.hasPermission('read:profiles')) {
    throw new Error("Forbidden");
  }
  return user;
}
```

---

### **Related Patterns**
1. **[Attribute-Based Access Control (ABAC)](https://example.com/abac)**
   - Extends role-based rules with dynamic attributes (e.g., time, location).

2. **[Claims-Based Authentication](https://example.com/claims-auth)**
   - Uses JWT/OAuth claims to propagate authorization data directly.

3. **[Resource Ownership](https://example.com/resource-ownership)**
   - Grants access based on object ownership (e.g., a user can only edit their own profile).

4. **[Policy-as-Code](https://example.com/policy-as-code)**
   - Stores authorization rules in declarative files (e.g., Open Policy Agent) for CI/CD integration.

5. **[Delegated Authorization](https://example.com/delegated-auth)**
   - Allows temporary role delegation (e.g., "project admin" for a specific task).

---
### **Common Pitfalls**
- **Permission Bloat**: Overly complex role hierarchies reduce maintainability. Use modular roles (e.g., "Editor" + "Billing" instead of a monolithic "SuperUser").
- **Hardcoded Checks**: Avoid inline permission logic in business logic; centralize to the authorization layer.
- **No Fallback**: Define default deny rules (e.g., all actions denied unless permitted).
- **Static Roles**: Roles should adapt to business changes (e.g., "Trial User" → "Premium User").

---
### **Tools & Libraries**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Casbin**             | Open-source policy enforcement library (supports ABAC/RBAC).                |
| **OPA (Open Policy Agent)** | Policy-as-code with flexible rule evaluation (supports Rego DSL).          |
| **Auth0/JWT**          | Integrates with JWT claims for stateless auth.                              |
| **AWS IAM**            | Managed RBAC for cloud services.                                            |
| **Grafana Auth Proxy** | Enforces permissions at the API layer.                                     |

---
### **Example Workflow: Microservice Integration**
1. **Service A** (User Profiles) defines:
   ```json
   {
     "resources": [
       { "path": "/api/profiles", "actions": ["GET", "POST"] }
     ],
     "roles": [
       { "name": "ProfileManager", "permissions": ["GET", "POST"] }
     ]
   }
   ```
2. **Service B** (Auth Service) assigns roles to users:
   ```json
   { "user_id": "123", "roles": ["ProfileManager"] }
   ```
3. **Request Flow**:
   - User accesses `/api/profiles`.
   - **Auth Service** validates JWT, checks `ProfileManager` role, and returns allowed actions (`GET`, `POST`).
   - **Service A** enforces the result (e.g., rejects `PUT` if not permitted).