```markdown
# **[Pattern] Authorization Anti-Patterns Reference Guide**
*Buy the ticket, take the ride: Common pitfalls and how to avoid them in authorization systems.*

---

## **Overview**
Authorization Anti-Patterns document **critical mistakes** in designing, implementing, and maintaining access control systems. These mistakes—such as over-permissiveness, poor segregation of duties, or rigid role hierarchies—can introduce security vulnerabilities, operational bottlenecks, or compliance risks. This guide outlines **11 recognized anti-patterns**, their **root causes**, **consequences**, and **best-practice alternatives** with practical examples. It targets **security architects, developers, and DevSecOps teams** building or auditing authorization logic in enterprise systems, cloud applications, or APIs.

---

## **Schema Reference: Authorization Anti-Pattern Categories**

| **Anti-Pattern**                     | **Definition**                                                                 | **Root Cause**                                                                 | **Impact**                                                                 |
|--------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **1. Overly Permissive Roles**       | Roles grant excessive permissions with no fine-grained control.              | Lack of granularity; "default-deny" not enforced; legacy system refactoring. | Data breaches, privilege misuse, audit failures.                           |
| **2. Static Roles**                  | Roles are hard-coded with no dynamic or contextual adjustments.              | Over-reliance on RBAC (Role-Based Access Control) without ABAC (Attribute-Based). | Inflexible for hybrid/saas workflows; ignores temporal or situational rules. |
| **3. No Segregation of Duties (SoD)**| Users with conflicting privileges (e.g., approving + executing purchases).    | Poor workflow modeling; lack of policy-as-code.                              | Fraud, insider threats, regulatory penalties (e.g., SOX, Basel III).         |
| **4. "Administrator" Overload**      | Generic superuser roles with unbounded permissions.                         | Ease of implementation; "admin" as a shortcut for undefined use cases.      | Single point of failure; no accountability.                                |
| **5. Role Explosion**                | Unmanageable number of roles due to overly granular specialization.           | Micromanagement of access; "permission bloat."                             | High maintenance cost; confusion among users.                             |
| **6. Missing Contextual Authorization** | Access decisions ignore metadata (e.g., time, location, user attributes).    | Static policies; siloed identity and access management (IAM).                | Unauthorized access during off-hours or from risky devices.                |
| **7. Weak Separation of Concerns**   | Authorization logic mixed with business logic or UI code.                    | Monolithic architectures; "security as an afterthought."                   | Harder to audit; bypasses (e.g., `admin=true` hardcoded in frontend).      |
| **8. No Revocation Strategy**        | Permissions linger after user departure or role changes.                      | Lack of lifecycle management; batch updates instead of real-time.            | Ex-situ employees retain access; privilege creep.                          |
| **9. Over-Reliance on Resource Ownership** | Permissions tied to ownership (e.g., "owner can modify").              | Simplified assumptions; no multi-tenancy support.                          | Tenant isolation breaches; "owner" as a single point of failure.          |
| **10. No Audit Trail for Access Decisions** | Decisions aren’t logged or correlated with events.                   | Security logging treated as optional; "just trust the system."               | No forensics; compliance violations (e.g., GDPR, HIPAA).                   |
| **11. Token-Based Bypass Vulnerabilities** | Weak token validation (e.g., no short-lived tokens, no claim validation). | Legacy auth systems; JWT misconfigurations.                                  | Token interception; unauthorized API access.                              |

---

## **Implementation Details: Anti-Patterns Deep Dive**

### **1. Overly Permissive Roles**
**Example:**
A system grants `"admin"` roles to all users who hit `/admin`, regardless of their actual task (e.g., billing vs. support).

**Mitigation:**
- **Principle of Least Privilege (PoLP):** Map roles to job functions. Use attributes (e.g., `dept="finance"`) instead of broad labels.
- **Dynamic Roles:** Use ABAC to adjust permissions based on context:
  ```json
  // ABAC policy snippet
  {
    "action": "edit_revenue",
    "resource": "2024-Q1",
    "conditions": [
      { "attribute": "user.department", "operator": "==", "value": "finance" },
      { "attribute": "time.hour", "operator": ">", "value": "9" }
    ]
  }
  ```

---

### **2. Static Roles**
**Example:**
A SaaS app uses fixed roles (`"freemium"`, `"pro"`) without tiered permissions.

**Mitigation:**
- **Modular Roles:** Combine roles + attributes:
  ```python
  # Pseudo-code for dynamic role assignment
  if user.tier == "gold" and user.country == "US":
      assign_roles(["customer_support", "discounted_pricing"])
  ```
- **Policy Engines:** Leverage tools like [OPA](https://www.openpolicyagent.org/) or [Kyverno](https://kyverno.io/).

---

### **3. No Segregation of Duties (SoD)**
**Example:**
A user can approve **and** execute wire transfers.

**Mitigation:**
- **SoD Rules:** Enforce separation via policy:
  ```yaml
  # Example Kyverno SoD policy
  rules:
    - apiVersion: constraints.kyverno.io/v1beta1
      kind: SoD
      metadata:
        name: transfer-separation
      match:
        resources:
          kinds:
            - Pod
      validation:
        message: "Approval and execution roles cannot coexist."
        pattern:
          spec:
            containers:
              - name: "transfer-approver"
              - name: "transfer-executor"
  ```
- **Automated Enforcement:** Integrate with IAM tools (e.g., [Okta](https://www.okta.com/), [Azure AD](https://azure.microsoft.com/en-us/products/active-directory/)).

---

### **4. "Administrator" Overload**
**Example:**
A superuser (`"all-permissions"`) is created for every dev environment.

**Mitigation:**
- **Tiered Admins:** Create scoped admin roles:
  ```json
  // Role hierarchy example
  {
    "name": "env-admin-database",
    "permissions": ["select", "insert", "update", "delete"],
    "scope": "staging-db"
  }
  ```
- **Just-In-Time (JIT) Access:** Use tools like [HashiCorp Vault](https://www.vaultproject.io/) for temporary escalation.

---

### **5. Role Explosion**
**Example:**
100+ roles due to manual permission mapping.

**Mitigation:**
- **Role Aggregation:** Group permissions logically:
  ```sql
  -- Simplified role schema
  CREATE TABLE roles (
    role_id INT PRIMARY KEY,
    name VARCHAR(50),
    permissions JSONB  -- E.g., ["read:docs", "write:docs:section*"]
  );
  ```
- **Automated Role Mining:** Use tools like [PAL](https://pal.securework.io/) to discover unused permissions.

---

### **6. Missing Contextual Authorization**
**Example:**
A doctor can access patient records at any time.

**Mitigation:**
- **Time-Based Restrictions:** Example policy:
  ```javascript
  // Node.js (Express middleware)
  function enforceHospitalHours(req, res, next) {
    const now = new Date();
    if (!(now.getHours() >= 9 && now.getHours() < 17)) {
      return res.status(403).send("Access denied outside office hours.");
    }
    next();
  }
  ```
- **Device/Location Checks:** Integrate with [FIDO2](https://fidoalliance.org/) or geofencing APIs.

---

### **7. Weak Separation of Concerns**
**Example:**
Authorization logic in the frontend:
```javascript
// ❌ Bad: Frontend bypass
const isAdmin = sessionStorage.getItem("isAdmin") === "true";
```

**Mitigation:**
- **Centralized Policy Store:** Use an auth service (e.g., [Auth0](https://auth0.com/)) or [AWS Cognito](https://aws.amazon.com/cognito/).
- **Attribute-Based Access Control (ABAC):** Decouple policies from code:
  ```yaml
  # OPA policy (regcon.policy)
  default deny
  allow {
    input.request.method == "GET" &&
    input.user.role == "viewer"
  }
  ```

---

### **8. No Revocation Strategy**
**Example:**
A terminated employee’s API keys remain valid.

**Mitigation:**
- **Automated Revocation:** Trigger on user deletion:
  ```python
  # Pseudo-code for role revocation
  def on_user_delete(user_id):
      db.execute("REVOKE ALL ON * FROM user_%s" % user_id)
  ```
- **Short-Lived Tokens:** Use [OAuth 2.0](https://oauth.net/2/) with refresh tokens.

---

### **9. Over-Reliance on Resource Ownership**
**Example:**
A "tenant owner" can delete all tenant data.

**Mitigation:**
- **Granular Ownership:** Define "owner" by sub-resource:
  ```sql
  CREATE TABLE tenant_data_access (
    tenant_id INT,
    user_id INT,
    resource_type VARCHAR(50),  -- "users", "reports"
    permission VARCHAR(10),     -- "read", "delete"
    PRIMARY KEY (tenant_id, user_id, resource_type, permission)
  );
  ```

---

### **10. No Audit Trail**
**Example:**
No logs for who accessed a patient’s EHR at 3 AM.

**Mitigation:**
- **Comprehensive Logging:** Track decisions + outcomes:
  ```json
  // Audit log entry
  {
    "timestamp": "2023-11-15T02:30:00Z",
    "user": "dr_smith@hospital.com",
    "action": "access_patient_data",
    "patient_id": "12345",
    "resource": "EHR",
    "decision": "allow",
    "context": {
      "device": "iPhone_12",
      "location": "New York, USA"
    }
  }
  ```
- **Tools:** Integrate with [ELK Stack](https://www.elastic.co/elasticsearch/) or [Splunk](https://www.splunk.com/).

---

### **11. Token-Based Bypass Vulnerabilities**
**Example:**
A JWT missing `aud` (audience) validation.

**Mitigation:**
- **Strict Token Validation:**
  ```go
  // Go (Golang) example with JWT
  token, err := jwt.ParseWithClaims(req.Header.Get("Authorization"),
      &Claims{},
      func(token *jwt.Token) (interface{}, error) {
          return []byte(os.Getenv("JWT_SECRET")), nil
      }
  )
  if claims.Audience != "secure-api" {
      return errors.New("invalid audience")
  }
  ```
- **Short Lifespan:** Set `exp` claim to 15 minutes max.

---

## **Query Examples**
### **1. Query for Over-Permissive Roles**
```sql
-- SQL to find roles with excessive permissions
SELECT role_name, COUNT(DISTINCT permission)
FROM roles_permissions
GROUP BY role_name
HAVING COUNT(DISTINCT permission) > 50;
```

### **2. ABAC Policy Query (OPA)**
```javascript
// Check if user can edit a report during business hours
allow {
  input.user.role == "editor" &&
  input.action == "edit" &&
  input.resource.type == "report" &&
  input.time.hour >= 9 &&
  input.time.hour < 17
}
```

### **3. SoD Violation Detection (Grafana + Prometheus)**
```promql
# Alert if user has conflicting roles
count_over_time(
  sum by (user_id) (
    label_replace(
      role_assignments{role="~approver|executor"},
      "action", "$1", "role", "(.*)"
    )
  )[1h:1m]
) > 1
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Role-Based Access Control (RBAC)** | Assign permissions to roles; roles to users.                                  | Simple, static environments (e.g., corporate directories).                     |
| **Attribute-Based Access Control (ABAC)** | Grant access based on dynamic attributes (time, location, etc.).            | Context-aware systems (e.g., IoT, SaaS).                                      |
| **Policy as Code (PaC)**        | Define authorization policies in code (e.g., OPA, Kyverno).                    | Infrastructure-as-code (IaC) workflows; compliance-heavy environments.        |
| **Just-In-Time (JIT) Access**   | Grant temporary elevated permissions.                                           | Dev/test environments; privileged access reviews.                             |
| **Zero Trust Architecture (ZTA)** | Assume breach; verify every access request.                                   | High-security environments (e.g., defense, healthcare).                         |
| **Permission Boundaries**       | Restrict admin roles to specific namespaces/resources.                         | Multi-tenant systems (e.g., Kubernetes).                                      |

---

## **Mitigation Checklist**
Use this to audit your authorization system:
1. [ ] Have roles followed **PoLP**? Audit permissions with a tool like [PAL](https://pal.securework.io/).
2. [ ] Are roles **dynamic** (ABAC) or **context-aware**? Test with scenario-based queries.
3. [ ] Enforced **SoD**? Use Kyverno or Open Policy Agent to validate policies.
4. [ ] **No "admin" overload**? Replace with scoped roles (e.g., `db-admin`).
5. [ ] **Audit logs** exist for all critical actions? Integrate with SIEM (e.g., Splunk).
6. [ ] **Token validation** includes audience, expiration, and claims? Test with [OWASP ZAP](https://www.zaproxy.org/).
7. [ ] **Revocation** is automated? Trigger on user termination.

---
**Further Reading:**
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST SP 800-162: Role-Based Access Control](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-162.pdf)
- [Kyverno Documentation](https://kyverno.io/docs/)
```