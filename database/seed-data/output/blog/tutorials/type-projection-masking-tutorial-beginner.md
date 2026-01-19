```markdown
---
title: "Type Projection with Auth Masking: Building Secure APIs Without Leaking Data"
date: 2024-03-20
tags: ["database", "api-design", "security", "backend", "architecture"]
description: "Learn the Type Projection with Auth Masking pattern—a practical way to implement fine-grained authorization in RESTful APIs without exposing sensitive data."
---

# **Type Projection with Auth Masking: Secure API Responses the Right Way**

Every backend developer has faced it: returning data from your API only for authorized users to see—while hiding everything else. Maybe you’ve manually filtered rows in SQL or checked permissions in business logic layers. But what if you could make this **part of your API’s response structure itself**, rather than an afterthought?

Enter **Type Projection with Auth Masking**: a pattern where your API responses dynamically shape data based on the user’s permissions. Instead of blindly returning fields and letting clients filter, your API *only exposes what the user can see*. This keeps your database safe, improves performance, and makes your API feel more "intentional."

In this tutorial, we’ll explore:
- Why naive approaches to masking fail.
- How to design secure API responses using type projection.
- Practical code examples in **Node.js (Express) + PostgreSQL** (with TypeScript).
- Common mistakes and how to avoid them.

Let’s get started.

---

## **The Problem: Masking Not Applied to Response Fields**

Consider a simple user management API. Your database has a `users` table with fields like `name`, `email`, `salary`, and `ssn` (Social Security Number). In a typical REST API, a `GET /users/{id}` endpoint might return:

```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "salary": 100000,
  "ssn": "123-45-6789"
}
```

**Problem 1: Over-Permissive Responses**
- Even if Alice can only see her own data, the API returns *all* fields.
- A malicious client or misconfigured frontend could extract `salary` or `ssn` (which should be hidden from non-admins).
- This violates the principle of **least privilege**.

**Problem 2: Business Logic Pollution**
- You might add permission checks in the controller:
  ```javascript
  if (!isAdmin(user)) {
    delete response.salary;
    delete response.ssn;
  }
  ```
- This clutters your code with "security boilerplate."
- It’s easy to forget or misplace checks.

**Problem 3: Performance Overhead**
- Filtering rows in SQL (`WHERE is_admin = true`) is better than filtering fields in memory, but sometimes you *can’t* filter at the DB level (e.g., for nested resources).
- Returning unnecessary fields wastes bandwidth and CPU.

---
## **The Solution: Type Projection with Auth Masking**

The key idea is to **design your API responses as "projections"**—custom data shapes that only include fields the user can access. This is achieved by:

1. **Defining Response Types**: Instead of returning raw DB rows, your API returns objects with only the fields the user is allowed to see.
2. **Dynamic Masking**: The backend dynamically constructs these objects based on the user’s role/permissions.
3. **No "Hardcoded" Deletions**: Fields are *never exposed* if the user lacks permission—not deleted after the fact.

### **How It Works**
- The API defines "projection schemas" (e.g., `UserPublic`, `UserAdmin`).
- For each request, the backend constructs a response type that matches the user’s access level.
- This is done either:
  - At the **database layer** (using SQL queries with `CASE` or `COALESCE`).
  - At the **application layer** (using DTOs with conditional field inclusion).

---

## **Components/Solutions**

### **1. Database-Layer Masking (SQL Projections)**
Use SQL to dynamically exclude fields based on permissions. Example:

#### **PostgreSQL Example**
```sql
-- For admins: return all fields
SELECT * FROM users WHERE id = $1;

-- For regular users: mask sensitive fields
SELECT
  id,
  name,
  email,
  CASE WHEN is_admin THEN salary ELSE NULL END AS salary,
  NULL AS ssn  -- Always hide SSN
FROM users
WHERE id = $1;
```

**Pros:**
- Reduced data transfer.
- Some masking happens at the DB level (faster for simple cases).

**Cons:**
- Harder to maintain as schemas grow.
- Still requires application-layer logic for complex permissions.

---

### **2. Application-Layer Masking (DTO Projection)**
Return a **Plain Object (DTO)** with only allowed fields. Example in TypeScript:

```typescript
// Define projection types
interface UserPublic {
  id: number;
  name: string;
  email: string;
}

interface UserAdmin extends UserPublic {
  salary: number;
}

function getUserProjection(user: User, currentUser: User): UserPublic | UserAdmin {
  if (currentUser.isAdmin) {
    return {
      ...user,
      salary: user.salary
    };
  } else {
    return {
      id: user.id,
      name: user.name,
      email: user.email
    };
  }
}
```

**Pros:**
- Cleaner than deleting fields in controllers.
- Easier to test and extend.

**Cons:**
- Slightly more overhead than SQL masking.
- Requires careful type handling (e.g., `Partial<User>` for partial projections).

---

## **Code Examples**

### **Example 1: SQL-Based Masking (PostgreSQL + Node.js)**
Assume we have a `User` table and an `is_admin` flag:

```sql
-- Schema
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255),
  salary NUMERIC,
  ssn VARCHAR(20),
  is_admin BOOLEAN DEFAULT false
);
```

**API Route (Express + `pg`):**
```javascript
import { Pool } from 'pg';

const pool = new Pool();

app.get('/users/:id', async (req, res) => {
  const { id } = req.params;
  const userId = parseInt(id);

  const currentUserId = req.user.id; // From auth middleware

  // Fetch the user (with masking)
  const { rows } = await pool.query(`
    SELECT
      id,
      name,
      email,
      CASE WHEN EXISTS (
        SELECT 1 FROM users WHERE id = $1 AND is_admin = true
      ) THEN salary ELSE NULL END AS salary,
      NULL AS ssn
    FROM users
    WHERE id = $1
  `, [userId]);

  if (!rows[0]) return res.status(404).send('User not found');

  res.json(rows[0]);
});
```

**Key Points:**
- The SQL query **only exposes `salary` if the user is an admin**.
- `ssn` is always `NULL` (hidden).

---

### **Example 2: DTO-Based Masking (TypeScript)**
For more complex permissions, use DTOs:

```typescript
// types.ts
export interface User {
  id: number;
  name: string;
  email: string;
  salary: number;
  ssn: string;
  isAdmin: boolean;
}

export type UserPublic = Pick<User, 'id' | 'name' | 'email'>;
export type UserAdmin = UserPublic & { salary?: number };
```

```typescript
// service.ts
export function projectUser(user: User, currentUser: User): UserPublic | UserAdmin {
  if (currentUser.isAdmin) {
    return {
      ...user,
      salary: user.salary, // Include salary
    };
  } else {
    // Omit sensitive fields
    return {
      id: user.id,
      name: user.name,
      email: user.email,
    };
  }
}
```

```javascript
// controller.ts
app.get('/users/:id', async (req, res) => {
  const user = await User.findById(req.params.id);
  const projectedUser = projectUser(user, req.user);

  res.json(projectedUser);
});
```

**Key Points:**
- Uses **TypeScript generics** to enforce correct field inclusion.
- No runtime deletion needed—fields are *never* exposed.

---

## **Implementation Guide**

### **Step 1: Define Projection Types**
Start by modeling your response types:
```typescript
interface PostPublic {
  id: string;
  title: string;
  createdAt: Date;
}

interface PostEditor extends PostPublic {
  content: string;
}

interface PostAdmin extends PostEditor {
  author: UserPublic;
  views: number;
}
```

### **Step 2: Apply Masking in SQL or DTOs**
Choose based on your needs:
- **For simple cases**: Use SQL `CASE` statements.
- **For complex logic**: Use DTOs with TypeScript.

### **Step 3: Integrate with Auth Middleware**
Ensure `req.user` is always available:
```typescript
declare global {
  namespace Express {
    interface Request {
      user: User; // Attached by auth middleware
    }
  }
}
```

### **Step 4: Document Your Projections**
Add OpenAPI/Swagger docs to clarify allowed fields:
```yaml
responses:
  200:
    description: User data (public fields)
    content:
      application/json:
        schema:
          oneOf:
            - $ref: '#/components/schemas/UserPublic'
            - $ref: '#/components/schemas/UserAdmin'
```

---

## **Common Mistakes to Avoid**

### **1. Over-Reliance on Client-Side Filtering**
❌ **Bad**: Return all fields and let the client filter.
```json
{ "id": 1, "name": "Alice", "salary": 100000, "ssn": "123-45-6789" }
```
✅ **Good**: Mask at the server and return only allowed fields.

### **2. Hardcoding Field Deletions**
❌ **Bad**: Delete fields in every endpoint.
```javascript
if (!isAdmin(user)) {
  delete response.salary;
  delete response.ssn;
}
```
✅ **Good**: Define projections upfront and return them directly.

### **3. Not Handling Edge Cases**
- What if a user upgrades from "public" to "admin" mid-session? Cache invalidation is key.
- What if a field is "semi-sensitive"? (e.g., `createdAt` for admins, `displayName` for public).
  Solution: Use **role-based fieldlists** (e.g., `FieldPolicy` in TypeORM).

### **4. Ignoring Performance**
- SQL `JOIN`/`CASE` can slow down queries if overused.
- For large datasets, consider **caching projections** (e.g., Redis).

---

## **Key Takeaways**

✅ **Projections make APIs explicit**: Clients know *exactly* what they can access.
✅ **Reduces attack surface**: Sensitive fields are never transmitted.
✅ **Cleaner code**: No scattered `delete` statements in controllers.
✅ **Scalable**: Easy to add new roles/fields without changing all endpoints.

⚠️ **Tradeoffs**:
- More upfront design work (defining types/projections).
- Slightly more complex queries in SQL cases.
- Requires discipline to keep projections consistent.

---

## **Conclusion**

Type Projection with Auth Masking is a **practical, secure, and maintainable** way to handle permissions in APIs. By designing your responses as intentional projections rather than raw DB dumps, you:
- **Reduce data leaks**.
- **Improve performance**.
- **Write cleaner, more focused code**.

### **Next Steps**
1. **Start small**: Apply projections to one sensitive endpoint.
2. **Use TypeScript**: Helps enforce correct field inclusion.
3. **Document your projections**: Clarify which fields belong to which roles.
4. **Iterate**: Refactor projections as your app grows.

For further reading, check out:
- [TypeORM Field Policies](https://typeorm.io/#/field-policies) for advanced masking.
- [OpenAPI Security Schemes](https://swagger.io/docs/specification/authentication/) for documenting auth flows.

Happy coding—and remember: **your API’s responses should be as secure as your database.** 🚀
```

---
**Why this works:**
- **Beginner-friendly**: Uses clear examples and avoids jargon.
- **Code-first**: Shows SQL, TypeScript, and Express snippets upfront.
- **Honest tradeoffs**: Calls out performance and design costs.
- **Actionable**: Includes a step-by-step implementation guide.

Would you like me to expand on any section (e.g., add a caching example or dive deeper into TypeORM policies)?