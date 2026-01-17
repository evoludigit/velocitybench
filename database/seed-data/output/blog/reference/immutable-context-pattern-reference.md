# **[Pattern] Immutable Context Pattern – Reference Guide**

---

## **1. Overview**
The **Immutable Context Pattern** ensures that authentication and authorization context is bound once per request in FraiseQL and remains unchanged throughout query execution. By making the context immutable, this pattern prevents:
- **Privilege escalation** (e.g., accidental or malicious context modification).
- **Inconsistent authorization decisions** (ensures decisions are based on a fixed, request-scoped context).

This pattern works in conjunction with FraiseQL’s query execution engine, which enforces authorization checks at each step using the predefined context. It is ideal for systems where fine-grained, request-level security controls are critical, such as multi-tenant applications or systems handling sensitive data.

---

## **2. Key Concepts**
| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Immutable Context** | A read-only object containing authentication/authorization attributes (e.g., user ID, roles, permissions). Must not be altered after binding. |
| **Binding**           | The process of attaching the context to a request when it first arrives.   |
| **Request Scope**     | The context is valid only for the duration of a single query execution.    |
| **Privilege Escalation** | Any attempt to modify the context after binding (e.g., via middleware) is blocked. |

---

## **3. Schema Reference**
The **Immutable Context** schema defines the structure of the context object. It includes:

| Field             | Type          | Description                                                                 | Required |
|-------------------|---------------|-----------------------------------------------------------------------------|----------|
| `userId`          | `UUID`        | Unique identifier of the authenticated user.                                | Yes       |
| `roles`           | `Array[String]`| List of roles (e.g., `["admin", "user"]`).                                 | Yes       |
| `permissions`     | `Object`      | Key-value pairs of module-specific permissions (e.g., `{ "db": ["read"] }`). | No        |
| `tenantId`        | `UUID`        | Identifier for a multi-tenant system (if applicable).                      | No        |
| `metadata`        | `Object`      | Arbitrary key-value pairs for additional context (e.g., `{"ip": "192.0.2.1"}`). | No        |

**Example Context Object:**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "roles": ["admin", "auditor"],
  "permissions": { "db": ["read", "write"], "api": ["list"] },
  "tenantId": "123e4567-e89b-12d3-a456-426614174000",
  "metadata": { "ip": "192.0.2.1" }
}
```

---

## **4. Implementation Steps**

### **4.1 Binding the Context**
The context is bound to a request **once** during the initial request processing. This typically occurs in:
- A middleware layer (e.g., Express.js, FastAPI).
- The entry point of your application (e.g., a gateway service).

**Pseudocode (Middleware Example):**
```javascript
// Example: Express middleware binding context
app.use(async (req, res, next) => {
  const context = await authenticateRequest(req); // Fetch from auth headers/JWT
  if (!context) return res.status(401).send("Unauthorized");

  // Attach context to request (for FraiseQL to consume)
  req.context = new ImmutableContext(context);
  next();
});
```

**Key Rules:**
1. The context **must not** be modified after binding (enforced via `ImmutableContext`).
2. FraiseQL queries **only** access the bound context (no runtime mutations).

---

### **4.2 Query Execution with Context**
FraiseQL queries automatically use the bound context for authentication checks. Example:

**Query:**
```fraiseql
query {
  users(where: { id: { eq: { value: "user_123" } } })
    @auth(permission: "db.read")
}
```

**How It Works:**
1. FraiseQL validates that the request’s context includes the `db.read` permission.
2. If the permission is missing, the query fails with a `403 Forbidden` error.
3. The context remains immutable during execution.

---

## **5. Query Examples**

### **5.1 Basic Query with Context**
```fraiseql
query {
  posts(where: { authorId: { eq: { value: { ref: "userId" } } } })
    @auth(roles: ["admin"])
}
```
- **Parameters:**
  - `{ ref: "userId" }` dynamically inserts the `userId` from the context.
- **Authorization:** Only users with the `admin` role can access this query.

---

### **5.2 Conditional Permissions**
```fraiseql
query {
  settings
    @auth(permissions: { db: ["admin", "write"] })
}
```
- Requires either the `admin` role **or** the specific `db.write` permission.

---

### **5.3 Multi-Tenant Context**
```fraiseql
query {
  tenantData(tenantId: { eq: { value: { ref: "tenantId" } } })
    @auth(roles: ["user"])
}
```
- Uses the `tenantId` from the context to scope data access.

---

## **6. Error Handling**
| Error Type               | Description                                                                 | Example Response                     |
|--------------------------|-----------------------------------------------------------------------------|---------------------------------------|
| **Unauthorized (401)**   | No context bound to the request.                                             | `{"error": "Authentication required"}` |
| **Forbidden (403)**     | Context lacks required permissions/roles.                                    | `{"error": "Missing permission: db.read"}` |
| **Immutable Violation**  | Attempt to modify the context after binding (e.g., in middleware).          | `{"error": "Context is immutable"}`   |

---

## **7. Related Patterns**

### **7.1 Request-Level Authorization**
- **Complement:** The Immutable Context Pattern works with request-level auth (e.g., JWT validation) to ensure context integrity.
- **Use Case:** Multi-layered security where JWT validates identity, and the context enforces permissions.

### **7.2 Fine-Grained Access Control (FGAC)**
- **Complement:** FGAC policies (e.g., `@auth`) dynamically apply rules based on the immutable context.
- **Use Case:** Database queries where permissions depend on roles, metadata, or tenant IDs.

### **7.3 Circuit Breakers for Context**
- **Complement:** If context binding fails (e.g., auth service unavailable), use a circuit breaker to fallback to a default context (e.g., guest mode).
- **Example:**
  ```javascript
  const context = await retryOrFallback(authenticateRequest, 3, () => guestContext);
  req.context = new ImmutableContext(context);
  ```

### **7.4 Context Propagation in Microervices**
- **Complement:** For distributed systems, propagate the context via headers (e.g., `X-Auth-Context`) between services.
- **Example Header:**
  ```
  X-Auth-Context: eyJ1c2VySWQiOiJ...&roles=admin
  ```

---

## **8. Best Practices**
1. **Validate Early:** Bind the context as soon as possible (e.g., in the first middleware) to fail fast on auth errors.
2. **Use References:** Prefer `{ ref: "userId" }` over hardcoded values in queries to avoid context leakage.
3. **Audit Context:** Log the bound context (excluding sensitive fields) for security audits.
4. **Immutable Enforcement:** Use runtime checks (e.g., `Object.freeze()` in JavaScript) to prevent accidental mutations.
5. **Testing:** Mock the context in unit tests to verify auth logic independently of the auth service.

---

## **9. Troubleshooting**
| Issue                          | Diagnosis                                                                 | Solution                                  |
|--------------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **Permission Denied**          | Query lacks required `@auth` rules.                                         | Check context roles/permissions vs. query. |
| **Context Not Bound**          | Middleware failed to attach context.                                        | Verify auth middleware is enabled.        |
| **Immutable Violation**        | Context modified after binding (e.g., in a library).                       | Review third-party code for context access.|

---

## **10. See Also**
- **[FraiseQL Authorization Guide]** – Details on `@auth` syntax and policy evaluation.
- **[Middleware Patterns]** – How to structure auth middleware for FraiseQL.
- **[Security Hardening]** – Additional measures for context-based systems.