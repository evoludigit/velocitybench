# **[Pattern] Authorization Strategies Reference Guide**

---

## **Overview**
The **Authorization Strategies** pattern defines a structured way to enforce access control within an application by systematically validating and granting permissions to users, services, or systems based on predefined rules. This pattern is crucial for securing APIs, microservices, and backend systems by ensuring that only authenticated entities perform allowed operations.

Key benefits include:
- **Granular control** over permissions (e.g., role-based, attribute-based, or policy-based).
- **Separation of concerns** between authentication (identifying users) and authorization (granting permissions).
- **Scalability** for complex permission matrices (e.g., RBAC x ABAC combinations).
- **Auditability** via explicit rules that can be logged or validated.

Common use cases:
- RESTful APIs where endpoints require specific roles (e.g., `admin:delete`).
- Microservices communicating via service-to-service authorization.
- Enterprise applications with dynamic permissions (e.g., conditional access).

---

## **Schema Reference**
Below is a standardized schema for defining authorization strategies. Implementations may extend or adapt this structure.

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                                                                 |
|-------------------------|----------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `strategy`              | String (enum)  | The authorization strategy type.                                                | `role-based`, `attribute-based`, `policy-based`, `custom`                          |
| `name`                  | String         | A human-readable identifier for the strategy.                                    | `admin_privileges`, `read_write_access`                                           |
| `description`           | String         | A brief explanation of the strategy’s purpose.                                  | *"Grants full CRUD access to projects."*                                           |
| `conditions`            | Array          | Rules governing access (varies by strategy).                                    | See strategy-specific examples below.                                             |
| `scope`                 | Array          | Targets of the authorization (e.g., endpoints, resources, or actions).         | `["/api/projects", "user:update:profile"]`                                       |
| `expiry`                | Timestamp      | Optional: When the strategy revokes permissions (e.g., session-based).          | `2024-05-01T12:00:00Z`                                                             |
| `metadata`              | Object         | Additional context (e.g., environment-specific overrides).                      | `{ "environment": "production", "team": "backend" }`                              |

---

### **Strategy-Specific Fields**
#### **1. Role-Based Access Control (RBAC)**
| Field               | Type    | Description                                                                 | Example                                                                 |
|---------------------|---------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `roles`             | Array   | List of roles granted access.                                               | `["admin", "editor"]`                                                    |
| `roleHierarchy`     | Object  | Defines parent-child role relationships (e.g., `admin > editor`).          | `{ "admin": ["editor", "viewer"] }`                                       |

**Example:**
```json
{
  "strategy": "role-based",
  "name": "project_editor",
  "roles": ["editor", "project_leader"],
  "scope": ["/api/projects/{id}"]
}
```

---

#### **2. Attribute-Based Access Control (ABAC)**
| Field               | Type    | Description                                                                 | Example                                                                 |
|---------------------|---------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `attributes`        | Object  | Key-value pairs defining dynamic conditions (e.g., `department: "engineering"`). | `{ "department": "engineering", "active": true }`                     |
| `attributeSources`  | Array   | Where attributes are sourced (e.g., `user_profile`, `environment`).        | `["user_profile", "request_headers"]`                                    |

**Example:**
```json
{
  "strategy": "attribute-based",
  "name": "department_access",
  "attributes": { "department": "finance" },
  "attributeSources": ["user_profile"]
}
```

---

#### **3. Policy-Based Access Control (PBAC)**
| Field               | Type    | Description                                                                 | Example                                                                 |
|---------------------|---------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `policies`          | Array   | List of policy conditions (e.g., time-of-day, IP ranges).                  | `[{ "policy": "office_hours", "value": true }]`                          |
| `policyEngine`      | String  | Reference to a custom policy engine (e.g., "xacml", "custom_lua").          | `"xacml"`                                                                 |

**Example:**
```json
{
  "strategy": "policy-based",
  "name": "time_restricted",
  "policies": [
    { "policy": "business_hours", "value": true },
    { "policy": "geo_location", "value": ["US", "CA"] }
  ]
}
```

---

#### **4. Custom Strategy**
| Field               | Type    | Description                                                                 | Example                                                                 |
|---------------------|---------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `handler`           | String  | Path to a custom implementation (e.g., `/auth/handlers/custom.js`).        | `"/auth/handlers/custom.js"`                                             |
| `inputs`            | Object  | Parameters passed to the custom handler.                                    | `{ "max_retries": 3 }`                                                   |

**Example:**
```json
{
  "strategy": "custom",
  "name": "audit_override",
  "handler": "/auth/handlers/audit.js",
  "inputs": { "require_approval": true }
}
```

---

## **Implementation Details**
### **1. Core Components**
- **Authorization Service**: Centralized logic for evaluating strategies (e.g., a library like [Casbin](https://casbin.org/) or a custom service).
- **Strategy Registry**: A data store (e.g., Redis, database) mapping strategy names to their configurations.
- **Decision Engine**: Evaluates conditions and returns `allow`/`deny` for each request.

### **2. Decision Flow**
1. **Request Interception**: The HTTP/API gateway or middleware captures the request.
2. **Strategy Lookup**: The system retrieves the relevant strategy(ies) for the requested resource/action.
3. **Condition Evaluation**: The decision engine checks `conditions`, `attributes`, or `policies`.
4. **Permission Grant**: If conditions pass, access is granted; otherwise, a `403 Forbidden` is returned.

### **3. Example Decision Engine Pseudocode**
```python
def evaluate_permission(strategy, request):
    if strategy["strategy"] == "role-based":
        user_roles = get_user_roles(request.user_id)
        return any(role in user_roles for role in strategy["roles"])
    elif strategy["strategy"] == "attribute-based":
        attributes = get_attributes(request, strategy["attributeSources"])
        return all(
            attributes.get(attr_key) == attr_value
            for attr_key, attr_value in strategy["attributes"].items()
        )
    # Add custom strategy handlers...
    else:
        return custom_handler(strategy["handler"], request, strategy["inputs"])
```

---

## **Query Examples**
### **1. RBAC: Check if User Has Role**
**Request:**
```http
GET /api/projects/123
Headers:
  Authorization: Bearer <token>
```
**Decision:**
- The gateway checks the `project_editor` RBAC strategy.
- If the user’s role is in `["editor", "project_leader"]` → **200 OK**.
- Else → **403 Forbidden**.

---

### **2. ABAC: Department-Specific Access**
**Request:**
```http
POST /api/reports
Headers:
  X-Department: engineering
```
**Decision:**
- The system evaluates the `department_access` ABAC strategy.
- If `X-Department: "engineering"` matches `attributes.department` → **201 Created**.
- Else → **403 Forbidden**.

---

### **3. PBAC: Time-Based Restriction**
**Request:**
```http
DELETE /api/data
Timestamp: 2024-05-01 23:00:00 (outside business hours)
```
**Decision:**
- The `time_restricted` PBAC strategy checks the `business_hours` policy.
- If `business_hours` policy returns `false` → **403 Forbidden**.
- Else → Proceed.

---

### **4. Custom Strategy: Audit Override**
**Request:**
```http
PATCH /api/settings
Headers:
  X-Override-Audit: true
```
**Decision:**
- The custom handler (`audit.js`) checks `X-Override-Audit`.
- If `require_approval: true` and the header is present → **200 OK**.
- Else → **403 Forbidden**.

---

## **Error Handling**
| Error Code | Description                          | Example Response                                                                 |
|------------|--------------------------------------|---------------------------------------------------------------------------------|
| `401`      | Unauthenticated (missing/expired token). | `{"error": "Unauthorized"}`                                                     |
| `403`      | Missing permissions.                 | `{"error": "Forbidden", "missing_roles": ["admin"]}`                           |
| `422`      | Invalid strategy configuration.      | `{"error": "Unsupported strategy 'malformed'"}`                                  |
| `500`      | Decision engine failure.              | `{"error": "Service unavailable: Check auth service"}`                          |

---

## **Related Patterns**
1. **[Authentication Patterns](link)**
   - *Complements Authorization*: Authentication verifies identity, while this pattern defines what authenticated users *can do*.
   - See: JWT, OAuth 2.0, API Keys.

2. **[Rate Limiting](link)**
   - *Integration*: Combine with Authorization to enforce both permission *and* rate constraints (e.g., "admin can delete 10 items/hour").

3. **[Event-Driven Authorization](link)**
   - *Advanced*: Use event buses (e.g., Kafka) to dynamically update permissions (e.g., "revoke access when user leaves the team").

4. **[Policy as Code](link)**
   - *Best Practice*: Store authorization rules in version-controlled files (e.g., YAML, JSON) for auditability.

5. **[Zero-Trust Architecture](link)**
   - *Context*: Authorization strategies are foundational for micro-segmentation and least-privilege access.

---
## **Anti-Patterns to Avoid**
- **Overly Complex Strategies**: Depth > 3 nested conditions increases maintainability risks.
- **Static Permissions Only**: Dynamic ABAC/PBAC scales better than static RBAC in large orgs.
- **Bypassing Strategies**: Avoid workarounds (e.g., hardcoding `allow` in debug mode).
- **Ignoring Expiry**: Always set `expiry` for temporary permissions (e.g., session tokens).

---
## **Tools & Libraries**
| Tool/Library          | Description                                                                 | Language/Framework       |
|-----------------------|-----------------------------------------------------------------------------|---------------------------|
| **Casbin**            | Open-source access control engine with RBAC/ABAC support.                   | Go, Python, JavaScript    |
| **OPA (Open Policy Agent)** | Policies as code (Rego language) for dynamic decisions.                   | Multi-language            |
| **AWS IAM**           | Managed RBAC/ABAC for cloud services.                                      | AWS                       |
| **Auth0/Pilot**       | SaaS-based authorization with fine-grained policies.                       | Cloud-based               |
| **JWT + Custom Claims** | Lightweight token-based authorization.                                   | Node.js, Python, etc.    |

---
## **Performance Considerations**
- **Cache Strategies**: Cache evaluated permissions (e.g., Redis) to avoid repeated decision engine calls.
- **Batch Evaluation**: Group requests (e.g., in APIs) to evaluate permissions in bulk.
- **Strategy Prioritization**: Order strategies by frequency (e.g., RBAC > ABAC) to optimize lookup time.