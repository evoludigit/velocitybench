# **[Pattern] Authorization Techniques Reference Guide**

---
## **Overview**
The **Authorization Techniques** pattern defines standardized methods for controlling access to system resources, ensuring users can only perform actions permitted by their role, permissions, or attributes. This guide covers core concepts, implementation details, supported schemas, query examples, and best practices for securing applications while maintaining flexibility and scalability.

Common authorization techniques include **role-based access control (RBAC)**, **attribute-based access control (ABAC)**, **access control lists (ACLs)**, **claims-based auth**, and **policy-based enforcement**. Each technique balances granularity with usability. This reference helps developers implement robust authorization logic while avoiding common pitfalls like overly restrictive or overly permissive policies.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authorization**      | The process of determining whether a user/agent has permission to access a resource or perform an action. Contrasts with *authentication* (verifying identity).                                          |
| **Access Control**     | A broader term encompassing mechanisms (RBAC, ABAC, etc.) to enforce authorization rules.                                                                                                                       |
| **Policy**             | A rule or set of rules defining what operations are allowed/denied. Policies can be static (e.g., RBAC roles) or dynamic (e.g., ABAC attributes).                                                         |
| **Permission**         | A specific right granted to a user/role (e.g., `edit:post`, `view:profile`).                                                                                                                                   |
| **Resource**           | Any entity (e.g., API endpoint, database table, file) that requires access control.                                                                                                                          |
| **Context**            | Additional information (e.g., time, location, device) used by ABAC to evaluate permissions.                                                                                                                   |

---

## **Schema Reference**

### **1. Role-Based Access Control (RBAC)**
| **Component**       | **Description**                                                                                                                                                     | **Example**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Role**            | A named collection of permissions (e.g., `admin`, `editor`).                                                                                                      | `"role": "admin"`                                                                               |
| **Permission**      | An action/resource pair (e.g., `create:article`, `delete:user`).                                                                                                  | `"permissions": ["edit:post", "view:dashboard"]`                                              |
| **User->Role Map**  | Links users to roles (1:many).                                                                                                                                     | `{ "user_id": "123", "role": "editor" }`                                                      |
| **Policy Engine**   | Evaluates whether a user’s role has a given permission.                                                                                                        | If user has role `admin`, grant `delete:user`.                                              |

---

### **2. Attribute-Based Access Control (ABAC)**
| **Component**       | **Description**                                                                                                                                                     | **Example**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Attribute**       | Key-value pairs describing a user, resource, or environment (e.g., `location="us-east"`, `department="marketing"`).                                            | `{"user.department": "marketing", "request.time": "9am-5pm"}`                                  |
| **Policy Rule**     | A condition (e.g., `department == "marketing" AND time_in_business_hours`).                                                                                       | `ALLOW IF (user.role == "admin" OR (user.department == target.department))`                    |
| **Decision Engine** | Evaluates policies against attributes in real-time.                                                                                                          | If `user.department == target.department`, grant `edit:project`.                             |

---

### **3. Access Control Lists (ACLs)**
| **Component**       | **Description**                                                                                                                                                     | **Example**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Resource ACL**    | A list of allowed users/roles for a specific resource.                                                                                                          | `{"file:/data/report.csv": ["role:admin", "user:jane"]}`                                        |
| **Entry Format**    | `{resource_path}: [list_of_grantees]` where grantees are users/roles.                                                                                              | `"api:/v1/users/{id}": ["role:auditor"]`                                                       |
| **Permission**      | Implicitly defined by the ACL (e.g., presence in the list grants access).                                                                                       | Adding `user:bob` to `file:/config.yaml` grants `read` access.                                |

---

### **4. Claims-Based Authorization**
| **Component**       | **Description**                                                                                                                                                     | **Example**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Claim**           | A statement in a token (JWT) asserting attributes/permissions (e.g., `{"perm": "edit:post"}`).                                                                    | `{"roles": ["admin"], "permissions": ["delete:user"]}`                                          |
| **Token Format**    | Typically JWT with a payload containing claims.                                                                                                                    | `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (includes `perm` claims).                     |
| **Validation**      | The server verifies token claims against allowed permissions.                                                                                                      | If token lacks `edit:post`, deny the request.                                                 |

---

### **5. Policy-Based Enforcement (PBE)**
| **Component**       | **Description**                                                                                                                                                     | **Example**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Policy Registry** | A central store for policy definitions (e.g., JSON/YAML files).                                                                                                   | `{ "delete:user": { "allow": ["role:admin"], "deny": ["department:hr"] } }`                    |
| **Policy Cache**    | Optimizes performance by storing evaluated policies.                                                                                                              | Cache `allow`/`deny` decisions for frequent actions (e.g., `view:dashboard`).                  |
| **Dynamic Policies**| Policies can update without code changes (e.g., via API or config reload).                                                                                       | Update `delete:user` policy via `/api/policies` endpoint to block weekend deletions.        |

---

## **Query Examples**

### **1. RBAC: Check User Permissions**
**Input:**
```json
{
  "user_id": "456",
  "action": "delete:user",
  "resource": "users/789"
}
```
**Output (Pseudocode):**
```python
def check_permission(user_id, action):
    role = get_role_for_user(user_id)
    if action in get_permissions_for_role(role):
        return True
    return False
```
**Result:** `True` if user has `admin` role; otherwise, `False`.

---

### **2. ABAC: Evaluate Time-Based Access**
**Policy:**
```json
{
  "action": "edit:project",
  "conditions": [
    { "attribute": "user.department", "operator": "==", "value": "engineering" },
    { "attribute": "request.time", "operator": "between", "value": ["09:00", "17:00"] }
  ]
}
```
**Query:**
```json
{
  "user": { "department": "engineering" },
  "time": "14:30",
  "action": "edit:project"
}
```
**Result:** `ALLOW` (if time is within 9am–5pm); otherwise, `DENY`.

---

### **3. ACL: Check File Access**
**ACL Entry:**
```json
{
  "file:/data/private.txt": ["user:alice", "role:admin"]
}
```
**Query:**
```json
{
  "requester": "user:bob",
  "resource": "file:/data/private.txt"
}
```
**Result:** `DENY` (Bob is not in the ACL list).

---

### **4. Claims-Based: Validate JWT Token**
**Token Claims:**
```json
{
  "sub": "123",
  "perm": ["view:dashboard", "edit:post"],
  "exp": 1735689600
}
```
**Query:**
```python
def validate_permission(token, required_perm):
    claims = decode_jwt(token)
    return required_perm in claims.get("perm", [])
```
**Result:** `True` if token includes `edit:post`; otherwise, `False`.

---

### **5. Policy-Based: Dynamic Rule Enforcement**
**Policy (YAML):**
```yaml
allow:
  delete:user:
    - role: admin
    - not:
        department: hr
```
**Query:**
```json
{
  "action": "delete:user",
  "user": { "role": "auditor", "department": "hr" }
}
```
**Result:** `DENY` (auditor lacks `admin` role and belongs to `hr`).

---

## **Implementation Best Practices**

1. **Separation of Concerns**
   - Keep authorization logic decoupled from business logic (e.g., use middleware like [OAuth2](https://oauth.net/2/) or [Casbin](https://casbin.org/)).
   - Example: Use an [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) for policy-as-code.

2. **Least Privilege**
   - Grant only the minimum permissions required. Example: Avoid giving `admin` roles to users unless necessary.

3. **Audit Logging**
   - Log authorization decisions (e.g., `DENIED: user 456 attempted delete:user/789`). Tools: ELK Stack, AWS CloudTrail.

4. **Performance**
   - Cache frequently evaluated policies (e.g., RBAC roles) to reduce lookup time.
   - For ABAC, precompute attribute combinations where possible.

5. **Dynamic Updates**
   - Allow policies to update without application restarts (e.g., via config files or APIs).

6. **Fallback Rules**
   - Define defaults (e.g., `DENY ALL` unless a policy explicitly allows access).

7. **Testing**
   - Use tools like [SpiceDB](https://spicedb.dev/) or [OPA’s `opa test`](https://www.openpolicyagent.org/docs/latest/test/) to validate policies.
   - Test edge cases (e.g., expired tokens, malformed claims).

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                                                                                         | **Use Case**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Authentication]**      | Verifies user identity (e.g., OAuth2, JWT). Authorization builds on authentication.                                                                    | Required before authorization (e.g., validate `user_id` in JWT before checking permissions).   |
| **[Policy as Code]**      | Define authorization rules in languages (e.g., Rego for OPA).                                                                                                 | Centralized, version-controlled policies (e.g., GitOps for auth rules).                         |
| **[Attribute Aggregation]** | Combine user attributes from multiple sources (e.g., LDAP, database).                                                                                           | ABAC requires rich user/context attributes (e.g., `user.location` from GPS + `time` from API).  |
| **[Rate Limiting]**       | Throttle access to prevent abuse (e.g., 100 requests/hour per user).                                                                                                | Prevents brute-force attacks on authorized endpoints.                                          |
| **[Multi-Factor Auth]**   | Adds layers of verification (e.g., TOTP, biometrics).                                                                                                               | Enhances security for high-risk actions (e.g., `delete:account`).                                |
| **[CORS Headers]**        | Restrict web API access by origin/headers.                                                                                                                        | Secure frontend-backend communication (e.g., `Access-Control-Allow-Origin: https://trusted.com`). |

---

## **Troubleshooting**

| **Issue**                          | **Cause**                                                                                     | **Solution**                                                                                     |
|------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Permission Denied**              | Incorrect role/permission mapping or missing claims.                                           | Verify user->role mappings, token claims, and policy rules.                                     |
| **Slow Authorization**             | Complex ABAC policies or inefficient caching.                                                 | Simplify policies, use indexes for attributes, or cache results.                                |
| **Dynamic Policy Failures**        | Policy updates not propagated to runtime.                                                    | Implement hot-reload for policies (e.g., watch YAML files for changes).                         |
| **Token Expiry Issues**            | Short-lived tokens or misconfigured `exp` claims.                                             | Extend token validity or use short-lived refresh tokens.                                        |
| **Race Conditions**                | Concurrent policy updates during checks.                                                      | Use locks or immutable policy versions (e.g., Git commits).                                     |

---

## **Example Architectures**
### **Option 1: Monolithic (Simplified)**
```
User Request → Auth Middleware (JWT Validation) →
                 RBAC Policy Engine → Decision → Response
```
**Tools:** Spring Security, Django’s `permissions.py`, Flask extensions like `flask-login`.

### **Option 2: Distributed (Scalable)**
```
User Request → Ingress (API Gateway) →
                 Policy Agent (OPA) → Check Claims/Policies →
                 Service Mesh (Istio/Envoy) → Enforce ACLs → Response
```
**Tools:** Open Policy Agent (OPA), Envoy, AWS IAM.

### **Option 3: Hybrid (ABAC + RBAC)**
```
User Request → Auth Service (JWT + Claims) →
                 ABAC Engine (Evaluate Attributes + RBAC Roles) →
                 Database ACL Lookup → Decision → Response
```
**Tools:** SpiceDB, Azure Policy, AWS IAM Conditions.

---
**References:**
- [OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [Casbin Documentation](https://casbin.org/docs/en/)
- [Open Policy Agent (OPA) Guide](https://www.openpolicyagent.org/docs/latest/)
- [NIST SP 800-162 (ABAC Overview)](https://nvlpubs.nist.gov/nistpubs/Legacy/sp/nistspecialpublication/800-162.pdf)