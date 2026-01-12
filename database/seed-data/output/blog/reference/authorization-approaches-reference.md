# **[Pattern Name: Authorization Approaches] Reference Guide**

## **Overview**
Authorization determines whether a user or system can access a specific resource, perform an action, or execute a function. This reference guide covers key **authorization approaches**, including their use cases, trade-offs, and implementation details. Each approach involves balancing **security**, **performance**, and **scalability**. Choose based on your system’s requirements: strict control (e.g., role-based access) for compliance, fine-grained flexibility (e.g., attribute-based) for dynamic access, or simplicity (e.g., policy-based) for rapid deployment.

---

## **Schema Reference**
Below are the **core components** of authorization approaches, structured in a table for quick comparison. Key attributes include **granularity**, **scalability**, **flexibility**, and **integration complexity**.

| **Attribute**         | **Role-Based (RBAC)** | **Attribute-Based (ABAC)** | **Policy-Based (PBP)** | **Claim-Based (OAuth/JWT)** | **Rule-Based (RB)** |
|-----------------------|----------------------|---------------------------|-----------------------|----------------------------|--------------------|
| **Granularity**       | Medium (roles)       | High (attributes/conditions) | Medium (predefined rules) | Medium (scope claims) | Low to Medium (hardcoded rules) |
| **Scalability**       | High (centralized)   | Medium-High (rule engine) | Medium (rule set) | Scalable (distributed) | Low (rule-heavy) |
| **Flexibility**       | Low (static roles)   | Very High (dynamic)       | Medium (configurable) | Medium (claims)           | High (custom rules) |
| **Use Case**          | Enterprise applications | Federated systems, IoT | Legacy systems, security policies | Microservices, APIs | Simple access controls |
| **Integration**       | LDAP/AD, IAM tools   | Policy engines (e.g., Open Policy Agent) | Custom rule sets | OAuth 2.0/JWT providers | Application logic |
| **Performance**       | Fast (role lookup)   | Slower (rule evaluation) | Medium (rule parsing) | Fast (token validation) | Medium (rule execution) |
| **Dynamic Updates**   | Manual (slow)        | Automatic (events/conditions) | Configurable | Token renewal | Manual (code changes) |

---

## **Implementation Details**
### **1. Role-Based Access Control (RBAC)**
**Key Concepts:**
- **Roles** define permission groups (e.g., `Admin`, `Editor`, `Guest`).
- Users are assigned roles, and roles have associated permissions.

**Implementation Steps:**
1. **Define Roles:** Create a role schema (e.g., MongoDB: `{ role: String, permissions: [String] }`).
2. **Assign Permissions:** Map permissions to roles (e.g., `Admin` → `create:article`, `delete:article`).
3. **Check Access:** Validate user role against requested action (e.g., `if user.role === "Admin" && action === "delete" { allow }`).

**Example Schema (JSON):**
```json
{
  "roles": {
    "Editor": ["read:article", "update:article"],
    "Admin": ["read:article", "update:article", "delete:article"]
  },
  "users": [
    { "name": "Alice", "role": "Editor" }
  ]
}
```

**Trade-offs:**
✅ **Simplicity:** Easy to implement and understand.
❌ **Stiffness:** Adding new permissions requires role updates.

---

### **2. Attribute-Based Access Control (ABAC)**
**Key Concepts:**
- Access decisions based on **attributes** (e.g., user’s department, time, device).
- Uses a **rule engine** (e.g., Open Policy Agent).

**Implementation Steps:**
1. **Define Attributes:**
   - User: `{ name: Alice, department: "Engineering", time: "morning" }`
   - Resource: `{ type: "article", sensitivity: "high" }`
2. **Write Policies:**
   - Rule: `if (user.department == "Engineering" && time == "morning") { allow }`
3. **Evaluate:** Policy engine checks conditions before granting access.

**Example Policy (Rego - OPA):**
```rego
package article
default allow = false

allow {
  input.user.department == "Engineering"
  input.time == "morning"
}
```

**Trade-offs:**
✅ **Flexibility:** Adapts to dynamic environments (e.g., IoT devices).
❌ **Complexity:** Requires a rule engine and tuning.

---

### **3. Policy-Based Authorization (PBP)**
**Key Concepts:**
- **Predefined policies** (e.g., "Only admins can delete data").
- Policies stored in a **centralized repository** (e.g., JSON/YAML).

**Implementation Steps:**
1. **Define Policies:**
   ```yaml
   # policies.yaml
   - name: "Delete Protection"
     condition: "user.role == 'Admin'"
     action: "delete:article"
   ```
2. **Load Policies:** Fetch at runtime (e.g., via API or file).
3. **Validate:** Check if requested action matches a policy.

**Example Code (Python):**
```python
import yaml

policies = yaml.safe_load(open("policies.yaml"))
def check_access(user, action):
    return any(p["condition"].format(user=user) for p in policies if p["action"] == action)
```

**Trade-offs:**
✅ **Configurable:** Policies change without code deployments.
❌ **Overhead:** Requires policy management layer.

---

### **4. Claim-Based (OAuth/JWT)**
**Key Concepts:**
- **Claims** in tokens (e.g., `scope: "read:profile"`) define permissions.
- Used in **OAuth 2.0** and **JWT** (JSON Web Tokens).

**Implementation Steps:**
1. **Issue Token:**
   ```json
   {
     "sub": "12345",
     "scope": ["read:article", "update:article"]
   }
   ```
2. **Validate Token:** Check claims against requested action.
3. **Enforce Scope:** Reject requests missing claims.

**Example (Node.js):**
```javascript
const jwt = require("jsonwebtoken");
function checkScope(token, requiredScope) {
  const payload = jwt.verify(token, "secret");
  return payload.scope.includes(requiredScope);
}
```

**Trade-offs:**
✅ **Stateless:** Tokens handle auth/authorization.
❌ **Short-Lived:** Requires token refresh mechanisms.

---

### **5. Rule-Based Authorization**
**Key Concepts:**
- **Hardcoded rules** in application logic (e.g., `if user.isAdmin { allow }`).

**Implementation Steps:**
1. **Embed Rules:**
   ```python
   def can_delete(user):
       return user.role == "Admin"
   ```
2. **Execute:** Rules run on every request.

**Trade-offs:**
✅ **No External Dependencies:** Simple for small apps.
❌ **Maintenance:** Rules spread across codebase.

---

## **Query Examples**
### **1. RBAC: Check User Permissions**
**Request:**
```http
GET /articles/123?action=delete
Headers: Authorization: Bearer <token>
```
**Response (Success):**
```json
{
  "status": "allowed",
  "role": "Admin"
}
```
**Response (Denied):**
```json
{
  "status": "denied",
  "reason": "Insufficient permissions"
}
```

### **2. ABAC: Dynamic Access Check**
**Request:**
```http
POST /api/policy?user.department=Engineering&time=morning
Body: { "action": "update:article" }
```
**Response (Success):**
```json
{ "authorized": true }
```

### **3. JWT: Scope Validation**
**Request:**
```http
GET /profile?scope=read:profile
Headers: Authorization: Bearer <token>
```
**Response (Valid Token):**
```json
{ "profile": { "name": "Alice" } }
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Resource Ownership](https://docs.microsoft.com/en-us/azure/architecture/patterns/resource-ownership)** | Users own resources; grants access by default.                              | Shared environments (e.g., SaaS).      |
| **[Authorization as a Service (AaaS)](https://aws.amazon.com/iam/)**          | Delegates auth to third-party services (e.g., AWS IAM).                      | Enterprise-grade security.              |
| **[Policy Enforcement Point (PEP)](https://www.oasis-open.org/committees/tc_home.php?wg_ab=open)** | Enforces policies at the application layer.                                | Microservices, APIs.                    |
| **[Least Privilege](https://cloud.google.com/architecture/least-privilege)**  | Grants minimal required permissions.                                         | Security-sensitive systems.            |
| **[Open Policy Agent (OPA)](https://www.openpolicyagent.org/)**               | Rule engine for ABAC policies.                                              | Dynamic, scalable authorization.        |

---

## **Best Practices**
1. **Combine Approaches:**
   - Use **RBAC for simplicity** + **ABAC for dynamic rules**.
   - Example: RBAC defines roles; ABAC handles time-based access.
2. **Audit Logs:**
   - Track authorization decisions (e.g., "User denied delete:article at 10:00 AM").
3. **Rate Limiting:**
   - Prevent brute-force attacks on auth endpoints.
4. **Token Rotation:**
   - Short-lived JWTs reduce risk of token theft.
5. **Document Policies:**
   - Update policy docs when rules change (e.g., Confluence/GitHub).

---
## **Antipatterns to Avoid**
- **Over-Permissive Roles:** Avoid giving admins `*` permissions.
- **Hardcoded Secrets:** Never bake policies into client-side code.
- **Ignoring Context:** ABAC without attributes (e.g., only role checks).
- **No Fallback:** Ensure denied requests return clear error messages (not 500 errors).

---
## **Further Reading**
- [IETF OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [Open Policy Agent Docs](https://www.openpolicyagent.org/docs/latest/)
- [NIST ABAC Guide](https://csrc.nist.gov/publications/detail/sp/800-162/final)
- [AWS IAM Best Practices](https://aws.amazon.com/iam/best-practices/)