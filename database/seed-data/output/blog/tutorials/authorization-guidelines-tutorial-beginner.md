```markdown
---
title: "Authorization Guidelines: The Pattern Every Beginner Backend Dev Should Know"
date: 2023-11-05
tags: ["database design", "api design", "backend engineering", "authorization", "security"]
series: ["Database & API Design Patterns"]
---

# **Authorization Guidelines: How to Secure Your APIs Like a Pro**

When you build an API, your first priority should be **making it secure**. But how do you ensure that only the right users can access the right data? This is where the **Authorization Guidelines Pattern** comes in—a structured approach to managing permissions that keeps your application safe from unauthorized access while remaining flexible and maintainable.

In this tutorial, we’ll explore:
✅ Why improper authorization can turn your API into a security nightmare
✅ A practical, step-by-step approach to implementing authorization
✅ Code examples in **REST APIs, JWT, and role-based access**
✅ Common pitfalls to avoid
✅ Best practices for long-term maintainability

Let’s dive in.

---

## **The Problem: What Happens Without Proper Authorization?**

Imagine this:
A user logs into your e-commerce app and can **edit any customer’s order**, not just their own. Or, an admin accidentally deletes a product that a regular user was supposed to manage. These scenarios aren’t just bugs—they’re **security vulnerabilities**.

Without clear authorization rules, APIs become:
- **Chaotic**: Users can perform actions they shouldn’t.
- **Hard to debug**: Security issues slip through without clear patterns.
- **Scalable nightmares**: Adding new roles or permissions becomes a headache.

Worse yet, in real-world incidents (like [AWS S3 breaches](https://www.wired.com/story/aws-s3-data-leakage-incidents/) or [Twitter API hacks](https://www.csoonline.com/article/3516652/how-twitter-hacks-work-and-how-to-protect-your-account.html)), poor authorization was a **key factor**.

---
## **The Solution: The Authorization Guidelines Pattern**

The **Authorization Guidelines Pattern** provides a **structured way** to define, enforce, and document permissions. It consists of **three core components**:

1. **Role-Based Access Control (RBAC)** – Assign predefined roles (e.g., `admin`, `user`) with permissions.
2. **Attribute-Based Access Control (ABAC)** – Fine-grained rules (e.g., "only approve orders from registered users").
3. **Policy Enforcement** – A logic layer (API middleware, database checks) that verifies permissions before allowing actions.

Together, these ensure **least privilege**—users only get the permissions they need.

---

## **Components & Solutions**

### **1. Defining Roles & Permissions**
First, decide what roles exist in your system and what each can do.

#### **Example: A Simple E-Commerce API**
| Role      | Can Edit | Can Delete | Can View Orders |
|-----------|----------|------------|-----------------|
| `admin`   | ✅ Yes   | ✅ Yes     | ✅ Yes          |
| `manager` | ✅ Yes   | ❌ No      | ✅ Yes          |
| `user`    | ❌ No    | ❌ No      | ✅ (Only own)   |

#### **Implementation in Database (PostgreSQL)**
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id),
    permission_id INTEGER REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

-- Insert sample data
INSERT INTO roles (name, description) VALUES
('admin', 'Full access to all features'),
('manager', 'Can edit but not delete'),
('user', 'Basic user with limited actions');

INSERT INTO permissions (name, description) VALUES
('edit_order', 'Edit any order'),
('delete_order', 'Delete any order'),
('view_orders', 'View orders (filtered)');
```

---

### **2. Assigning Roles to Users**
Each user should belong to **one or more roles**.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);

-- Assign roles to users
INSERT INTO user_roles (user_id, role_id) VALUES
(1, 1),  -- User 1 is an admin
(2, 2);  -- User 2 is a manager
```

---

### **3. Enforcing Permissions at the API Level**
Now, **every API endpoint must check permissions** before executing.

#### **Option A: Role-Based Middleware (Express.js Example)**
```javascript
const express = require('express');
const app = express();

// Define roles (could also come from DB)
const ROLES = {
    ADMIN: 'admin',
    MANAGER: 'manager',
    USER: 'user'
};

// Middleware to check permissions
const checkPermission = (requiredPermission) => {
    return (req, res, next) => {
        const userRole = req.user.role; // Assume we set this via JWT auth

        // Define role-permission mapping
        const rolePermissions = {
            [ROLES.ADMIN]: ['edit_order', 'delete_order', 'view_orders'],
            [ROLES.MANAGER]: ['edit_order', 'view_orders'],
            [ROLES.USER]: ['view_orders']
        };

        if (!rolePermissions[userRole].includes(requiredPermission)) {
            return res.status(403).json({ error: 'Forbidden' });
        }

        next();
    };
};

// Protected route example
app.post('/orders/:id/edit',
    checkPermission('edit_order'),
    (req, res) => {
        res.json({ success: true, message: 'Order updated!' });
    }
);
```

#### **Option B: Database-Level Checks (PostgreSQL Example)**
For **ultra-sensitive operations** (e.g., deleting user data), enforce checks in the DB:

```sql
-- Only admins can delete users
CREATE OR REPLACE FUNCTION can_delete_user()
RETURNS boolean AS $$
DECLARE
    user_id integer := current_setting('app.current_user_id')::integer;
    user_role text := (SELECT r.name FROM auth.user u JOIN auth.user_roles ur ON u.id = ur.user_id
                      JOIN roles r ON ur.role_id = r.id WHERE u.id = user_id LIMIT 1);
BEGIN
    RETURN user_role = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Use the function in a DELETE trigger
CREATE TRIGGER prevent_unauthorized_deletes
BEFORE DELETE ON users
FOR EACH ROW EXECUTE FUNCTION can_delete_user()
WHEN (not can_delete_user());
```

---

### **4. Token-Based Authorization (JWT Example)**
Most modern APIs use **JWT (JSON Web Tokens)** to attach user permissions.

```javascript
// Generate a JWT with role info
const jwt = require('jsonwebtoken');

const generateToken = (user) => {
    return jwt.sign(
        { id: user.id, role: user.role },
        process.env.JWT_SECRET,
        { expiresIn: '1h' }
    );
};

// Verify JWT and attach role to request
app.use((req, res, next) => {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'No token' });

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        req.user = decoded; // Attach role to request
        next();
    } catch (err) {
        res.status(401).json({ error: 'Invalid token' });
    }
});
```

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Define Roles & Permissions**
- Start with a **small set of roles** (e.g., `admin`, `user`).
- Use a **database table** (`roles`, `permissions`) for scalability.

### **Step 2: Assign Roles to Users**
- Link users to roles via a **join table** (`user_roles`).
- Example:
  ```sql
  INSERT INTO user_roles (user_id, role_id)
  VALUES (1, 1), (2, 2); -- User 1 is admin, User 2 is manager
  ```

### **Step 3: Implement Middleware for API Checks**
- Use **Express middleware** (Node.js) or **ASP.NET filters** (C#) to verify permissions.
- Example (Fastify.js):
  ```javascript
  const fastify = require('fastify')();

  fastify.decorate('authenticate', async (request, reply) => {
      if (!request.user.role.includes('admin')) {
          throw new Error('Unauthorized');
      }
  });

  fastify.post('/admin-only',
      fastify.authenticate,
      async (request, reply) => {
          reply.send('Welcome, admin!');
      }
  );
  ```

### **Step 4: Use JWT for Stateless Auth**
- Store roles in the JWT payload.
- Example payload:
  ```json
  {
      "id": 1,
      "role": "admin",
      "exp": 1700000000
  }
  ```

### **Step 5: Test Edge Cases**
- **What if a role has no permissions?**
  → Return `403 Forbidden` instead of `200 OK + error`.
- **What if a new role is added?**
  → Update your middleware logic (or use a DB lookup).

---

## **Common Mistakes to Avoid**

❌ **Over-Permissive Roles**
- *Problem:* Giving `admin` too many permissions.
- *Fix:* Follow **least privilege** (only grant what’s needed).

❌ **Hardcoding Permissions**
- *Problem:* Hardcoding `if (user.role === 'admin')` makes refactoring hard.
- *Fix:* Use a **database-backed role-permission table**.

❌ **No Database-Level Checks**
- *Problem:* Even if the API checks permissions, a clever attacker might bypass it.
- *Fix:* Enforce **row-level security (RLS) in PostgreSQL** or **application-level filters**.

❌ **Ignoring Token Expiry**
- *Problem:* Stale JWTs can lead to unauthorized access.
- *Fix:* Set **short expiry times** (e.g., 1 hour) and require re-authentication.

❌ **Not Testing Edge Cases**
- *Problem:* A role with no permissions still gets an empty response.
- *Fix:* Mock tests for **denied access** scenarios.

---

## **Key Takeaways**

✔ **Authorization ≠ Authentication**
- Auth (login) ≠ **who can do what** (authz).

✔ **Roles + Permissions = Scalability**
- Adding new features? Just add a new permission.

✔ **DB Checks + Middleware = Defense in Depth**
- Never rely on **just one layer** (API or DB).

✔ **JWTs Work, But Be Cautious**
- Tokens are stateless, so **validity checks are crucial**.

✔ **Document Your Rules**
- Keep a **README** or **API spec** explaining permissions.

---

## **Conclusion: Build Secure APIs, Not Just Features**

Authorization isn’t just a checkbox—it’s the **foundation of a secure system**. By following the **Authorization Guidelines Pattern**, you’ll:

✅ Prevent accidental data leaks
✅ Make your API easier to maintain
✅ Future-proof your permissions system

**Next Steps:**
- Try implementing this in your own project.
- Explore **attribute-based access control (ABAC)** for more granular rules.
- Read up on **[OWASP’s Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)** for best practices.

Got questions? Drop them in the comments—I’d love to help!

---
```

---
**Why This Works:**
- **Code-first approach** with real-world examples (Node.js, PostgreSQL, JWT).
- **Balanced tradeoffs** (e.g., DB checks vs. API middleware).
- **Beginner-friendly** but still practical for intermediate devs.
- **Actionable takeaways** with clear steps.

Would you like any refinements (e.g., more focus on a specific tech stack)?