**[Pattern] Type Projection with Auth Masking Reference Guide**

---

### **Overview**
Type projection with **Auth Masking** dynamically filters API responses to hide sensitive or unauthorized fields based on user permissions. This pattern complements **Type Projection** (selecting only requested fields) by enforcing **row-level security (RLS)** and **field-level security (FLS)**. It ensures clients receive only allowed data without exposing schema details or unintended attributes.

Use cases include:
- **Multi-tenant SaaS** (hide tenant-specific data).
- **Role-based access control (RBAC)** (mask fields based on user roles, e.g., `admin` vs. `user`).
- **Compliance requirements** (e.g., GDPR, HIPAA) to redact PII.
- **Granular API design** where clients shouldn’t know all possible fields.

This pattern assumes a backend service (e.g., GraphQL, REST, or gRPC) processes queries and enforces masking via middleware, database policies, or application logic.

---

## **Key Concepts**

| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Type Projection**   | Clients specify fields to include (or exclude) via query parameters (e.g., `fields=name,email`).                                                                                                        |
| **Auth Masking**      | A layer (e.g., database function, middleware) dynamically replaces or omits fields based on user permissions. Example: Replace `salary` with `null` for non-admin users.                     |
| **Masking Strategies**|                                                                                                                                                                                                         |
| - **Field Omission**  | Exclude fields entirely from the response.                                                                                                                                                         |
| - **Value Replacement**| Replace sensitive values with defaults (e.g., `****`, `null`) or placeholders.                                                                                                                       |
| - **Dynamic Field Names**| Rename fields based on permissions (e.g., `user_profile` → `employee_profile` for admins).                                                                                                            |
| **Policy Engines**    | Tools like [AWS IAM Policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html), [PostgreSQL Row Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html), or custom middleware. |

---

## **Schema Reference**

Below is a **sample schema** for a `User` type with fields that may be masked. Columns marked with `*` are mutable via auth policies.

| Field          | Type    | Description                          | Auth Masking Policy                                                                 |
|----------------|---------|--------------------------------------|------------------------------------------------------------------------------------|
| `id`           | UUID    | Unique identifier                    | *Never masked (required for relationships).                                          |
| `name`         | String  | Full name                            | *Visible to all roles.                                                              |
| `email`        | String  | Email address                        | *Visible to all roles; redacted in responses if `marketing_opt_out: true`.          |
| `salary`       | Float   | Annual compensation                  | *Masked for non-admin roles (replaced with `null`).                                 |
| `manager_id`   | UUID    | ID of direct supervisor              | *Visible only to users with `view_org_hierarchy` permission.                        |
| `created_at`   | Timestamp | Account creation date               | *Visible to all roles.                                                              |
| `is_active`    | Boolean | Account status                       | *Visible to all roles. Masked if `user` role lacks `view_inactive_users` permission. |

---

## **Implementation Details**

### **1. Database-Level Masking (PostgreSQL Example)**
Use **Row-Level Security (RLS)** and **Custom Functions** to mask fields:
```sql
-- Enable RLS on the users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy to mask salary for non-admins
CREATE POLICY mask_salary ON users
    FOR SELECT USING (current_user = 'admin')
    HANDLER FUNCTION public.reveal_salary(policy_obj record);

-- Custom function to replace salary
CREATE OR REPLACE FUNCTION public.reveal_salary(record users)
RETURNS TABLE (id UUID, name VARCHAR, email VARCHAR, **salary NUMERIC**)
LANGUAGE SQL
AS $$
    SELECT id, name, email,
        CASE WHEN current_user = 'admin' THEN salary ELSE null END AS salary
    FROM users $$;

-- Query example (returns salary only for admins)
SELECT * FROM users WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

### **2. Application-Level Masking (Node.js Example)**
Use middleware (e.g., Express) or GraphQL resolvers to mask fields:
```javascript
// GraphQL Resolver Example
const userResolver = (parent, args, context) => {
  if (!context.user.isAdmin && args.fields.includes('salary')) {
    args.fields = args.fields.filter(f => f !== 'salary');
  }
  return db.query('SELECT * FROM users WHERE id = $1', [args.id]);
};

// REST Middleware Example (Express)
app.get('/users/:id', (req, res, next) => {
  db.query('SELECT * FROM users WHERE id = $1', [req.params.id], (err, rows) => {
    if (err) return next(err);
    const maskedUser = maskFields(rows[0], req.user.roles);
    res.json(maskedUser);
  });
});

function maskFields(user, roles) {
  if (!roles.includes('admin')) {
    delete user.salary;
    user.email = user.email.replace(/(\..*)$/, '****');
  }
  return user;
}
```

### **3. Client-Side Projection (GraphQL Example)**
Clients specify fields to include, and the server enforces masking:
```graphql
# Client Query (requests only visible fields)
query {
  user(id: "123") {
    id
    name
    email  # May be masked if user opts out of marketing
    # salary  # Omitted from query; server won’t return it for non-admins
  }
}
```

---
## **Query Examples**

### **1. GraphQL Query with Auth Masking**
**Request:**
```graphql
query {
  user(id: "123") @include(if: $isAdmin) {
    id
    name
    salary @include(if: $isAdmin)
  }
}
```
**Variables:**
```json
{ "isAdmin": true }
```
**Response (Admin):**
```json
{
  "data": {
    "user": {
      "id": "123",
      "name": "Alice",
      "salary": 75000.00
    }
  }
}
```
**Response (Non-Admin):**
```json
{
  "data": {
    "user": {
      "id": "123",
      "name": "Alice"
      // salary omitted
    }
  }
}
```

### **2. REST Endpoint with Field Filtering**
**Request:**
```
GET /users/123?fields=name,email
```
**Headers:**
```
Authorization: Bearer <non-admin-token>
```
**Response:**
```json
{
  "id": "123",
  "name": "Alice",
  "email": "alice****@example.com"  // Masked email
}
```

### **3. Database Query with RLS**
**Request (Admin):**
```sql
SELECT name, salary FROM users WHERE id = '123';
```
**Response (Admin):**
```
| name | salary |
|------|--------|
| Alice | 75000  |
```
**Request (Non-Admin):**
```sql
SELECT name, salary FROM users WHERE id = '123';
```
**Response (Non-Admin):**
```
| name | salary |
|------|--------|
| Alice | null   |
```

---

## **Error Handling and Edge Cases**
| Scenario                          | Solution                                                                                                                                 |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| **Permission Denied**             | Return `403 Forbidden` with a generic message (avoid exposing schema details).                                                    |
| **Missing Required Fields**      | Validate projections server-side and return `400 Bad Request` if critical fields are omitted.                                       |
| **Dynamic Schema Changes**       | Use a **field whitelist** in the backend to validate projections against allowed fields.                                          |
| **Nesting Masking**               | Apply masking recursively to nested objects (e.g., `user.profile.address`).                                                      |
| **Audit Logging**                | Log masked operations for compliance (e.g., `salary masked for user:123, role:user`).                                             |

---

## **Related Patterns**
| Pattern                     | Description                                                                                                                                 |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| **[Type Projection](https://example.com/type-projection)** | Clients specify fields to include/exclude; reduces bandwidth and improves security.                                         |
| **[Row-Level Security (RLS)](https://example.com/rls)**      | Restricts row access (e.g., "only show your own records"). Combines well with field masking.                                   |
| **[Policy As Code](https://example.com/policy-as-code)**   | Define auth rules in code (e.g., Open Policy Agent) for complex logic.                                                          |
| **[Attribute-Based Access Control (ABAC)](https://example.com/abac)** | Extends masking to environment/device-based policies (e.g., mask PII on mobile apps).         |
| **[GraphQL Directives](https://example.com/graphql-directives)** | Use `@require`, `@skip` directives to enforce masking in GraphQL schemas.                                                  |

---
## **Tools and Libraries**
| Tool/Library               | Use Case                                                                                                                                 |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| **PostgreSQL RLS**        | Database-level row/field masking.                                                                                                   |
| **AWS Cognito IAM**       | Enforce masking based on user groups.                                                                                              |
| **Open Policy Agent (OPA)** | Policy engine for dynamic masking rules.                                                                                           |
| **GraphQL Shield**        | Middleware for GraphQL auth/masking (e.g., `isAuthenticated`, `authorize`).                                                            |
| **Prisma Client Extensions** | Custom query logic (e.g., mask fields before returning results).                                                                      |
| **Hasura Actions**        | Serverless functions to transform data before exposing it via Hasura’s built-in auth.                                                   |

---
## **Best Practices**
1. **Whitelist Fields**: Only allow known fields in projections; reject unknown fields.
2. **Default Deny**: Assume fields are masked unless explicitly allowed (e.g., via `@allow` directives in GraphQL).
3. **Log Masking Decisions**: Track why fields were masked (e.g., "salary masked for user:123, role:user").
4. **Performance**: Cache masked responses for high-traffic fields.
5. **Document Policies**: Maintain a spec of which roles see which fields (e.g., a **Field Access Matrix**).
6. **Testing**:
   - Use property-based testing (e.g., Hypothesis) to verify masking logic.
   - Test edge cases (e.g., nested projections, concurrent requests).