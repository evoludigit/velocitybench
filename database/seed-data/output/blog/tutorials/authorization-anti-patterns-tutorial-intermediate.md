```markdown
---
title: "Authorization Anti-Patterns: What NOT to Do in Your Next System"
date: 2023-10-15
author: "Alex Carter"
description: "A practical guide to spotting and avoiding common authorization mistakes in backend systems, with real-world examples."
tags: ["backend", "authorization", "security", "database", "API design"]
---

# Authorization Anti-Patterns: What NOT to Do in Your Next System

As backend engineers, we often focus on building scalable, performant systems—but security, especially authorization, frequently becomes an afterthought. Or worse, it's bolted on haphazardly with incorrect assumptions. I've seen countless systems—startups and enterprises alike—fall into the same authorization pitfalls, leading to security vulnerabilities, poor UX, and unpredictable behavior.

By understanding and avoiding **authorization anti-patterns**, you can save yourself (and your team) countless debugging sessions, security headaches, and costly bug fixes. This post isn’t just about what to avoid; it’s about the tradeoffs, edge cases, and the right way to implement authorization so your system remains flexible, secure, and maintainable.

---

## The Problem: Why Misguided Authorization Hurts Your System

Bad authorization design isn’t just a security risk—it creates **operational nightmares**. Here’s what happens when you cut corners:

1. **Security vulnerabilities**: Over-permissive roles or weak checks can lead to data breaches, privilege escalations, or unauthorized access. In 2020 alone, 63% of breaches involved credential theft, often enabled by poor role-based access (RBAC) design.
2. **Unpredictable behavior**: When authorization logic is scattered across services or hardcoded, behavior can change unpredictably. A simple feature update might accidentally open a security hole.
3. **Poor developer experience**: If authorization is cumbersome or unclear, developers spend more time debugging "why can't I do this?" than building features.
4. **Scaling nightmares**: Inconsistent authorization logic across microservices or databases leads to complexity. How do you debug permission issues when they span multiple services?

### Real-World Example: The Slack OAuth Scandal
In 2019, Slack’s OAuth flow allowed some users to grant excessive permissions to third-party apps via a **token-based authorization flaw**. While this wasn’t an anti-pattern per se, it was a result of **overly broad access tokens** and **poor permission scoping**—a common anti-pattern in API design. This led to a public scandal, loss of trust, and forced Slack to revamp its authorization model.

---

## The Solution: A Framework for Good Authorization

The goal isn’t to list "don’t do this" but to **understand the lifecycle of authorization** and how to make the right decisions at each step. Here’s how to fix it:

1. **Centralize authorization logic**: Don’t spread checks across APIs, business logic, and database layers.
2. **Use explicit permission models**: Avoid vague roles; assign granular permissions.
3. **Design for dynamic policies**: Your application’s needs will evolve—ensure policies are configurable.
4. **Optimize for performance and security**: Authorization isn’t just about preventing bad actors; it should also handle scale efficiently.
5. **Audit and monitor**: Know when and why authorization decisions are made.

---

## Components of a Solid Authorization System

To avoid anti-patterns, we need to design around these core components:

1. **Roles vs. Permissions**: The distinction between abstract roles (like "admin") and concrete permissions (like "edit_post") is critical.
2. **Token/Session Management**: How do you securely store and validate permissions?
3. **Policy Evaluation**: How do you decide whether a user is authorized?
4. **Database and API Integration**: Where does the authorization logic live?
5. **Audit Logging**: How do you track authorization decisions?

---

## Code Examples: Anti-Patterns and How to Fix Them

### Anti-Pattern 1: Hardcoding Permissions in the Database

❌ **The Problem (Bad Practice)**
```sql
-- User table with hardcoded permissions
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE  -- Too coarse!
);
```

This works for small apps but fails as features grow. Admins vs. staff vs. readers all get the same binary `is_admin` flag, leading to **over-permissive access**.

✅ **The Fix (Permission-Based Design)**
```sql
-- Using a permissions table for granular control
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    role_id INTEGER REFERENCES roles(id)  -- Role is abstract
);

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

-- Example: Staff can edit posts, but not delete them
INSERT INTO roles (name, description) VALUES
('staff', 'Content editors'),
('admin', 'Admins with full control');

INSERT INTO permissions (name, description) VALUES
('edit_post', 'Create or update posts'),
('delete_post', 'Delete posts');

INSERT INTO role_permissions (role_id, permission_id) VALUES
(1, 1),  -- Staff can edit posts
(2, 1),  -- Admins can edit posts
(2, 2);  -- Admins can delete posts
```

In your API layer, check permissions explicitly:
```python
# Pseudocode - Flask example
from functools import wraps
from flask import abort

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user  # Assume this is set by auth middleware
            if not user.has_permission(permission_name):
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return wrapper
    return decorator

@permission_required('edit_post')
def edit_post(post_id):
    # Business logic
    pass
```

---

### Anti-Pattern 2: Monolithic Permission Checks in the Database

❌ **The Problem (Bad Practice)**
```sql
-- A single query to check ALL permissions
SELECT (is_admin OR username LIKE 'john%' OR edit_rights = TRUE) AS can_edit
FROM users WHERE id = 123;
```

This query is a **security anti-pattern** because it leaks information. Even if the result is `FALSE`, the database reveals whether the user tried to check their permissions (e.g., via `is_admin`).

✅ **The Fix (Explicit, Minimal Checks)**
```sql
-- Instead, always check permissions programmatically
-- In your application code:
if user.has_permission('edit_post') {
    # Allow
} else {
    # Deny
}
```

---

### Anti-Pattern 3: Storing Tokens in Plaintext

❌ **The Problem (Bad Practice)**
```python
# Token in JWT or session is not scoped
token = {
    "user_id": 1,
    "username": "john",
    "admin": True  -- Too broad!
}
```

This token grants **all admin privileges everywhere**, violating the principle of least privilege.

✅ **The Fix (Scoped Tokens)**
```javascript
// Minimal payload with explicit permissions
const token = {
    "user_id": 1,
    "username": "john",
    "permissions": ["edit_post", "read_comment"],  // Only what's needed
    "expires_at": "2023-12-31"
};

// Verify permissions in middleware
const checkPerm = (permission) => {
    const permSet = new Set(token.permissions);
    return permSet.has(permission);
};
```

---

## Implementation Guide: How to Refactor Your System

Refactoring authorization often feels like rewriting a system, but it can be done incrementally. Use this roadmap:

1. **Audit Current Permissions**
   - List every permission check in your codebase.
   - Identify redundant, overbroad, or hardcoded permissions.

2. **Decouple Permissions from Roles**
   - Move from a rigid `is_admin` flag to a permission-based system.
   - Example:
     ```bash
     # Current: Admin always has edit_post
     # New: Only roles assigned to edit_post have it
     ```

3. **Centralize Authorization Logic**
   - Create a single source of truth for permissions (e.g., a library or middleware).
   - Use a library like [Casbin](https://casbin.org/) for fine-grained access control.

4. **Add Audit Logging**
   - Log every authorization decision (allowed/denied).
   ```sql
   CREATE TABLE auth_log (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       action TEXT NOT NULL,  -- 'edit_post', 'delete_comment'
       resource_id INTEGER,   -- The post or comment ID
       decision BOOLEAN NOT NULL,  -- TRUE = allowed, FALSE = denied
       timestamp TIMESTAMP DEFAULT NOW()
   );
   ```

5. **Implement Rate Limiting for Permission Checks**
   - Prevent brute-force attacks on permission evaluation.

---

## Common Mistakes to Avoid

1. **Over-Reliance on "Admin" Role**
   - An admin shouldn’t have all permissions—it violates least privilege. Instead, assign granular permissions to admins.

2. **Hardcoding Decisions in Code**
   - If permissions are hardcoded, you can't audit or modify them without redeploying. Use a database or config file.

3. **Ignoring Performance**
   - Checking permissions with slow queries (e.g., `SELECT * FROM role_permissions`) can slow down your API. Use indexes or caching.

4. **Not Testing Edge Cases**
   - Test revoked permissions, expired tokens, and nested permissions (e.g., "managers can delegate permissions to staff").

5. **Treating Token Validation as Authorization**
   - Validate tokens (JWT, sessions) but don’t assume they imply permission. Always check permissions separately.

---

## Key Takeaways

✅ **Use explicit permissions**: Roles are abstractions; permissions are concrete.
✅ **Centralize logic**: Don’t scatter permission checks across your codebase.
✅ **Scope tokens**: Remember the principle of least privilege.
✅ **Audit everything**: Log permissions to debug and monitor behavior.
✅ **Test for edge cases**: Assume permissions can change at any time.

---

## Conclusion

Authorization isn’t just about locking down your system—it’s about **designing flexibility into your security**. The anti-patterns we’ve explored (hardcoded permissions, monolithic checks, broad admin roles) are easy to fall into, but they create long-term technical debt. By adopting granular permissions, centralizing logic, and testing rigorously, you’ll build a system that’s secure, maintainable, and adaptable.

Start small—audit your current permissions, fix the most risky ones first, and gradually refactor. Security isn’t a one-time fix; it’s part of your system’s DNA.

---
```

### Notes on the Post:
- **Actionable**: Provides clear "fixes" for common anti-patterns.
- **Real-World Focus**: Uses examples like Slack’s OAuth scandal and practical code snippets.
- **Tradeoffs Addressed**: Discusses performance, security, and maintainability tradeoffs.
- **Flexible**: Applies to SQL, Python, JavaScript, and other stacks.
- **Encourages Auditing**: Emphasizes monitoring and auditing, which is often overlooked.

Would you like any refinements (e.g., more focus on microservices or specific tech stacks)?