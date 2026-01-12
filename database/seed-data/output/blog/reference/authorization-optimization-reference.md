**[Pattern] Authorization Optimization – Reference Guide**

---

### **Overview**
Authorization Optimization is a **performance-critical pattern** that minimizes redundant or inefficient authorization checks while maintaining security. It ensures that access control decisions are computed only when necessary, reducing latency and resource overhead—critical in high-throughput systems like APIs, microservices, or real-time applications.

This guide covers:
- Key concepts and principles for optimizing authorization logic.
- Patterns and trade-offs for implementation.
- Schema and query examples for common authorization use cases.
- Related patterns for complementary security optimizations.

---

## **1. Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                                                                                 | **Use Case Example**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Selective Authorization** | Apply granular permissions only when required (e.g., per API endpoint, field-level).                                                                                                                                                                       | A user only needs to read `order_details`; avoid checking `user_admin` if irrelevant.               |
| **Cache-Aware Authorization** | Reuse authorization decisions when the subject/resource hasn’t changed.                                                                                                                                                                                      | Cache the result of `can_user_edit_document(id)` for 30 seconds if the document hasn’t mutated.     |
| **Deferred Authorization** | Postpone checks until the last moment (e.g., at API response time).                                                                                                                                                                                       | Check permissions *after* building a query result to avoid filtering early.                          |
| **Authorization Layer Abstraction** | Use a unified module (e.g., Open Policy Agent, Casbin) to centralize rules and avoid code duplication.                                                                                                                                                   | Replace 100s of `if (user.role === "admin")` checks with a single policy engine call.             |
| **Resource Graphs**     | Represent resources and relationships as a graph for efficient traversal (e.g., access control for nested structures like directories).                                                                                                              | A user can access `file:///x/ folder` and its contents; traverse the graph to validate permissions. |
| **Policy Decoupling**   | Separate policy evaluation from business logic to improve flexibility.                                                                                                                                                                                          | Store policies in a database and reload them without redeploying the app.                           |

---

## **2. Schema Reference**

### **2.1. Core Entities**
| **Entity**          | **Attributes**                                                                 | **Description**                                                                                     |
|---------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| `User`              | `id` (String), `roles` (Array[String]), `attributes` (JSON), `session_id` (String) | Represents authenticated entities; `roles` may include `admin`, `auditor`, or custom roles.      |
| `Resource`          | `id` (String), `type` (String), `owner_id` (String), `metadata` (JSON)      | Any entity being accessed (e.g., `document`, `api_endpoint`).                                       |
| `Permission`        | `action` (String), `resource_type` (String), `effect` (Boolean)             | Defines what can be done (e.g., `create`, `delete`) on a resource type.                          |
| `PolicyRule`        | `user_id` (String), `resource_id` (String), `action` (String), `conditions` (JSON) | Describes *who* can perform *what* on *which* resource under *what* constraints.               |

---
### **2.2. Policy Storage Models**
#### **Option 1: Relational Database (Simplified)**
```sql
CREATE TABLE policies (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(id),
  resource_id VARCHAR(255) REFERENCES resources(id),
  action VARCHAR(50),  -- e.g., "read", "update"
  conditions JSONB     -- e.g., {"time": {"before": "2024-01-01"}}
);
```

#### **Option 2: Graph-Based (Neo4j)**
```cypher
CREATE (u:User {id: "user123", roles: ["editor"]})
CREATE (r:Resource {id: "doc456", type: "document"})
CREATE (u)-[:HAS_PERMISSION {action: "edit"}]->(r);
```

#### **Option 3: Attribute-Based (ABAC)**
```json
{
  "policy": {
    "target": {"resource": {"type": "order"}, "action": "create"},
    "condition": {
      "request": {
        "user.attributes.department": "finance"
      }
    }
  }
}
```

---

## **3. Implementation Patterns**

### **3.1. Selective Authorization**
**Goal:** Avoid checking permissions for irrelevant actions/resources.
**Implementation:**
- **API Gateway Filtering:**
  Use middleware to block unauthorized endpoints early (e.g., Express `authMiddleware`).
  ```javascript
  // Example: Only check admin permissions for /admin routes
  app.use("/admin", (req, res, next) => {
    if (!req.user.isAdmin) return res.status(403).send("Forbidden");
    next();
  });
  ```
- **Field-Level Security:**
  Restrict query responses to permitted fields.
  ```graphql
  # Only return "name" and "status" if user has "view" permission on "order"
  query {
    order(id: "123") {
      name @authorized(field: "name", action: "view")
      status @authorized(field: "status", action: "view")
    }
  }
  ```

---

### **3.2. Cache-Aware Authorization**
**Goal:** Reuse decisions when inputs haven’t changed.
**Implementation:**
- **Redis Cache:**
  Store evaluated permissions with TTL (e.g., 1 minute).
  ```python
  # Pseudocode: Cache check for "can_edit_document(123)"
  cached_result = redis.get(f"perm:user123:doc123:edit")
  if cached_result:
      return json.loads(cached_result)["allowed"]
  else:
      # Evaluate and cache
      result = policy_engine.evaluate(...)
      redis.setex(f"perm:user123:doc123:edit", 60, json.dumps(result))
      return result
  ```
- **Cache Invalidation:**
  Invalidate cache on policy changes or resource updates.
  ```javascript
  // Example: Invalidate cache when a document is updated
  when Document.updated:
      cache.del(`perm:*:${updatedDoc.id}:*`);
  ```

---

### **3.3. Deferred Authorization**
**Goal:** Compute permissions after data is fetched to avoid filtering early.
**Implementation:**
- **Database Query Optimization:**
  Fetch all data first, then filter in-app.
  ```sql
  -- Fetch all orders for user (no WHERE clause)
  SELECT * FROM orders WHERE user_id = '123';
  -- Filter in Python:
  permitted_orders = [o for o in orders if policy_engine.allowed(user, o, "view")]
  ```
- **Streaming Responses:**
  Use dynamic field resolution (e.g., FastAPI’s `@authorized` decorator).
  ```python
  from fastapi import Depends, HTTPException
  from pydantic import BaseModel

  class Document(BaseModel):
      id: str
      name: str = Field(..., alias="__name")  # Hidden if unauthorized

      @property
      def name(self):
          if not policy_engine.allowed(user, self, "view"):
              raise HTTPException(403)
          return super().name
  ```

---

### **3.4. Policy Decoupling**
**Goal:** Isolate policy logic for easier maintenance.
**Implementation:**
- **Policy-as-Code (ReGo/Open Policy Agent):**
  Define rules externally (Rego) and plug into your app.
  ```rego
  # policies/rego
  package auth
  default allow = false

  allow {
      input.user.roles[_] == "admin"
  }
  ```
  ```go
  // Load policy in Go
  policy, _ := rego.New(
      rego.Config{EnablePreprocessing: true},
      []byte(policyText),
  )
  res, _ := policy.Evaluate(context.Background(), rego.Input{...})
  ```
- **Dynamic Policy Reload:**
  Use a watcher to reload policies on file changes.
  ```python
  # Pseudocode: Reload policies from file
  def watch_policies(file_path):
      while True:
          with open(file_path) as f:
              policy = json.load(f)
          # Recompile policy engine
          time.sleep(10)
  ```

---

## **4. Query Examples**

### **4.1. Check Permissions (Direct)**
**Request:**
```http
GET /api/documents/123
Headers:
  Authorization: Bearer <token>
```
**Response (200 OK):**
```json
{
  "id": "123",
  "title": "Confidential",
  "content": "Secret data",
  "permissions": ["view", "edit"]
}
```
**Validation Logic:**
```javascript
// Node.js: Check if user has "view" permission
const hasPermission = await policyEngine.hasPermission(
  { id: userId, roles: userRoles },
  { id: "123", type: "document" },
  "view"
);
if (!hasPermission) throw new ForbiddenError();
```

---

### **4.2. Field-Level Access Control (GraphQL)**
**Query:**
```graphql
query GetUserProfile($userId: ID!) {
  user(id: $userId) {
    id
    name
    email @authorized(field: "email", action: "view")
    salary @authorized(field: "salary", action: "view") {
      amount @authorized(field: "amount", action: "view")
    }
  }
}
```
**Variables:**
```json
{ "userId": "user456" }
```
**Response (200 OK):**
```json
{
  "data": {
    "user": {
      "id": "user456",
      "name": "Alice",
      "email": "alice@example.com",
      "salary": { "amount": 100000 }
    }
  }
}
```

---

### **4.3. Policy-Based Routing (Express.js)**
**Route Handler:**
```javascript
const express = require("express");
const router = express.Router();
const policyEngine = require("./policy-engine");

router.get("/orders/:id", async (req, res) => {
  const order = await Order.findById(req.params.id);
  if (!policyEngine.allowed(req.user, order, "view")) {
    return res.status(403).send("Access denied");
  }
  res.json(order);
});
```

---

## **5. Performance Trade-offs**
| **Optimization**               | **Pros**                                                                 | **Cons**                                                                 | **Use Case**                          |
|---------------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|---------------------------------------|
| **Selective Authorization**     | Reduces redundant checks.                                               | Complex to implement for dynamic permissions.                           | REST/GraphQL APIs.                   |
| **Cache-Aware**                 | Near-zero latency for repeated checks.                                  | Cache invalidation can be error-prone.                                 | High-traffic systems (e.g., dashboards). |
| **Deferred**                    | Avoids filtering data early.                                            | Higher memory usage for unsanitized data.                               | Real-time analytics.                 |
| **Policy Decoupling**           | Easier to update rules without redeploying.                             | Adds latency for external policy engines.                              | Enterprise apps with evolving rules. |
| **Resource Graphs**             | Efficient for hierarchical permissions (e.g., folders/teams).          | Overhead for simple permissions.                                        | org-wide access control.            |

---

## **6. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                          |
|----------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Role-Based Access Control (RBAC)** | Assign permissions to roles rather than individual users.                     | Simplify admin workflows.               |
| **Attribute-Based Access Control (ABAC)** | Evaluate permissions based on dynamic attributes (e.g., time, location).     | Context-aware systems (e.g., IoT).       |
| **Rate Limiting + Authorization** | Combine auth with rate limiting to prevent brute-force attacks.              | Public APIs under DDoS risk.            |
| **Zero-Trust Architecture**      | Assume breach; verify every request end-to-end.                               | High-security environments (e.g., finance). |
| **JWT Validation Optimization**  | Cache JWT claims to reduce cryptographic overhead.                             | Mobile/web apps with frequent API calls. |

---

## **7. Anti-Patterns**
- **Over-Fetching Permissions:**
  Avoid checking all possible permissions for every request (e.g., `if (user.role === "admin")` always).
  **Fix:** Use selective checks or a policy engine.

- **Global Cache Stampede:**
  When multiple requests invalidate the same cache key simultaneously.
  **Fix:** Use distributed locks (e.g., Redis `SETNX`) or probabilistic data structures.

- **Hardcoded Checks:**
  Embedding permissions in business logic (e.g., `if (isOwner(user, resource))`).
  **Fix:** Centralize in a policy engine.

- **Ignoring Context:**
  Forgetting to account for time, location, or device in ABAC policies.
  **Fix:** Define conditions explicitly (e.g., `time_of_day: "business_hours"`).

---
**References:**
- [OAuth 2.0 Authorization Framework (RFC 6749)](https://datatracker.ietf.org/doc/html/rfc6749)
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/)
- [Casbin: Access Control Engine](https://casbin.org/)
- [Field-Level Security in GraphQL](https://graphql.org/learn/field-level-security/)