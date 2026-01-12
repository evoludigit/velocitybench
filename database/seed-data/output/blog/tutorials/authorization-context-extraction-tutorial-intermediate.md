```markdown
---
title: "Extraction Made Easy: The Authorization Context Pattern in Backend Design"
date: 2023-11-15
tags: ["backend", "design-patterns", "api", "authentication", "authorization", "jwt", "security"]
---

# **Extraction Made Easy: The Authorization Context Pattern in Backend Design**

When building secure APIs or backend services, authorization is the unsung hero that gates access to resources—ensuring only authenticated and authorized users can perform actions. But what happens when your codebase grows? How do you ensure that authorization context—like user roles, claims, or tenant information—is consistently available throughout your application?

In this post, we’ll explore the **Authorization Context Extraction** pattern, a foundational technique for efficiently capturing and distributing authorization data across your application. We’ll break down the problem, dive into practical implementations in **Node.js (Express), Python (FastAPI), and Go**, discuss common pitfalls, and highlight key takeaways for maintainable security.

---

## **Introduction**

Authorization is about more than just checking if a user is logged in. It’s about *what* they can do—whether they’re an admin, a power user, or restricted to read-only access. Without a structured way to handle this context, your code can quickly become a disorganized mess:

- **Spaghetti code**: Authorization logic scattered across route handlers, middleware, and business logic.
- **Inconsistencies**: Some endpoints enforce RBAC (Role-Based Access Control) while others rely on manual checks.
- **Performance bottlenecks**: Repeatedly parsing JWT tokens or querying databases for user roles.
- **Security risks**: Hardcoding credentials or over-relying on middleware with limited scope.

The **Authorization Context Extraction** pattern solves these issues by centralizing the extraction and distribution of authorization data, making it available consistently across your application. Instead of manually injecting user roles into every function, you rely on a structured context object that gets populated early in the request lifecycle and reused everywhere.

---

## **The Problem**

### **1. Authorization Data Scattered Everywhere**
Imagine a growing API where authorization checks are implemented ad-hoc:

```javascript
// Express route without a pattern
app.get('/admin/dashboard', (req, res) => {
  if (req.user?.role === 'admin') { // Manual check every time
    // ...
  } else {
    res.status(403).send('Forbidden');
  }
});
```

This approach has several downsides:
- **Duplication**: The same check might repeat 10+ times across different routes.
- **Inconsistencies**: Some endpoints might miss checks entirely.
- **Hard to test**: Logic is tightly coupled with route handlers.

### **2. Inconsistent Token Handling**
Many applications use JWTs, but parsing them inconsistently:

```javascript
// Bad: Parse JWT in every route
app.get('/profile', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).send('Unauthorized');
  const decoded = jwt.verify(token, process.env.JWT_SECRET); // Expensive operation!
  if (decoded.role !== 'user') return res.status(403).send('Forbidden');
  // ...
});
```

Each route parsing JWTs is inefficient and error-prone.

### **3. Tenant-Aware Applications Struggle**
For SaaS applications, handling multi-tenancy adds complexity. You might need to:

- Attach tenant ID to every request.
- Ensure tenant context is available in all business logic.
- Handle tenant-specific permissions.

Without a structured pattern, this becomes a nightmare of manual context passing.

---

## **The Solution: Authorization Context Extraction**

The **Authorization Context Extraction** pattern centralizes the process of extracting and storing authorization data into a single, reusable context object. This context is then made available throughout the request lifecycle, reducing duplication and ensuring consistency.

### **Key Components**
1. **Extractor**: Parses tokens (JWT, session) and fetches additional data (e.g., roles, tenant).
2. **Middleware/Interceptors**: Injects the extracted context into the request object or a global store.
3. **Context Object**: A structured payload containing:
   - User identity (ID, username).
   - Roles/permissions.
   - Tenant information (if applicable).
   - Claims or custom claims.
4. **Usage**: Business logic assumes the context is available and acts on it.

---

## **Implementation Guide**

Let’s implement this pattern in **Node.js (Express), Python (FastAPI), and Go**.

---

### **1. Node.js (Express) Example**

#### **Context Structure**
```javascript
// models/auth-context.js
class AuthContext {
  constructor(user, tenant, permissions) {
    this.user = user;
    this.tenant = tenant;
    this.permissions = permissions;
  }
  hasPermission(permission) {
    return this.permissions.includes(permission);
  }
}

module.exports = AuthContext;
```

#### **Extractor Middleware**
```javascript
// middleware/auth-extractor.js
const jwt = require('jsonwebtoken');
const AuthContext = require('../models/auth-context');

const extractAuthContext = async (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).send('Unauthorized');
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Fetch additional data (e.g., user roles from DB)
    const user = await User.findById(decoded._id);
    const tenant = await Tenant.findById(decoded.tenantId);

    const context = new AuthContext(
      user,
      tenant,
      decoded.permissions || []
    );

    // Attach to request for downstream use
    req.authContext = context;
    next();
  } catch (err) {
    res.status(403).send('Forbidden');
  }
};

module.exports = extractAuthContext;
```

#### **Usage in a Route**
```javascript
// routes/admin.js
app.get('/admin/dashboard', authExtractor, (req, res) => {
  // Assume context is available
  if (!req.authContext?.hasPermission('admin:dashboard')) {
    return res.status(403).send('Forbidden');
  }

  // Business logic
  res.send('Welcome, Admin!');
});
```

---

### **2. Python (FastAPI) Example**

#### **Context Structure**
```python
# models/auth_context.py
from pydantic import BaseModel

class AuthContext(BaseModel):
    user_id: str
    username: str
    tenant_id: str
    roles: list[str]

    @property
    def is_admin(self):
        return 'admin' in self.roles
```

#### **Extractor Dependency Injection**
```python
# dependencies/auth.py
from fastapi import Depends, HTTPException, Request
from jose import jwt
from models.auth_context import AuthContext

async def get_auth_context(
    request: Request
) -> AuthContext:
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # Fetch additional data (e.g., user roles)
        user = await User.get(decoded['sub'])
        tenant = await Tenant.get(decoded['tenant_id'])

        return AuthContext(
            user_id=user.id,
            username=user.username,
            tenant_id=decoded['tenant_id'],
            roles=user.roles
        )
    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid token")
```

#### **Usage in a Route**
```python
# routers/admin.py
from fastapi import APIRouter, Depends
from dependencies.auth import get_auth_context

router = APIRouter()

@router.get('/dashboard')
async def dashboard(
    context: AuthContext = Depends(get_auth_context)
):
    if not context.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    return {"message": "Welcome, Admin!"}
```

---

### **3. Go Example**

#### **Context Structure**
```go
// models/auth_context.go
package models

type AuthContext struct {
    UserID   string
    Username string
    TenantID string
    Roles    []string
}

func (a *AuthContext) HasPermission(perm string) bool {
    for _, role := range a.Roles {
        if role == perm {
            return true
        }
    }
    return false
}
```

#### **Extractor Middleware**
```go
// middleware/auth_extractor.go
package middleware

import (
    "net/http"
    "github.com/golang-jwt/jwt/v5"
    "yourproject/models"
)

func AuthExtractor(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }

        var decoded map[string]interface{}
        token = token[len("Bearer "):]
        claim, err := jwt.ParseWithClaims(token, &decoded, func(token *jwt.Token) (interface{}, error) {
            return []byte(SECRET_KEY), nil
        })

        if err != nil || !claim.Valid {
            http.Error(w, "Forbidden", http.StatusForbidden)
            return
        }

        // Fetch additional data (e.g., user roles)
        user, err := UserService.GetUser(decoded["_id"].(string))
        tenant, err := TenantService.GetTenant(decoded["tenant_id"].(string))

        context := &models.AuthContext{
            UserID:   decoded["_id"].(string),
            Username: user.Username,
            TenantID: decoded["tenant_id"].(string),
            Roles:    decoded["roles"].([]string),
        }

        // Attach to context variable (Go doesn’t have request objects, so we use a middleware library like gin or a custom struct)
        // For simplicity, we’ll assume a struct is passed through the chain.
        ctx := r.Context()
        ctx = context.WithValue(ctx, "auth_context", context)
        r = r.WithContext(ctx)
    })
}
```

#### **Usage in a Handler**
```go
// handlers/admin.go
package handlers

import (
    "net/http"
    "yourproject/models"
)

func DashboardHandler(w http.ResponseWriter, r *http.Request) {
    context := r.Context().Value("auth_context").(*models.AuthContext)
    if !context.HasPermission("admin:dashboard") {
        http.Error(w, "Forbidden", http.StatusForbidden)
        return
    }

    // Business logic
    w.Write([]byte("Welcome, Admin!"))
}
```

---

## **Common Mistakes to Avoid**

1. **Overloading the Context**
   Don’t stuff every possible field into the context. Keep it focused on authorization needs (roles, permissions, tenant).
   ❌ Bad:
   ```javascript
   req.authContext = {
     user, tenant, permissions, billingInfo, preferences, ...
   };
   ```
   ✅ Good:
   ```javascript
   req.authContext = { user, permissions, tenant };
   ```

2. **Not Validating the Context Early**
   If your context is invalid (e.g., missing a required field), handle it immediately and fail fast.

3. **Ignoring Performance**
   Avoid expensive operations (e.g., DB calls) during context extraction. Cache roles or use lightweight claims.

4. **Hardcoding Secrets**
   Never hardcode JWT secrets or database credentials in middleware. Use environment variables or a secrets manager.

5. **Assuming the Context is Always Available**
   Always check `if (!req.authContext)` before using it. Assume nothing!

6. **Overcomplicating the Context for Simple Apps**
   If your app only needs basic auth, skip the context and use simple middleware checks.

---

## **Key Takeaways**

✅ **Centralize Extraction**: Extract authorization context once and reuse it everywhere.
✅ **Reduce Duplication**: Avoid repeating JWT parsing or role checks in every route.
✅ **Improve Performance**: Cache or optimize expensive operations during context extraction.
✅ **Enforce Consistency**: Ensure all endpoints use the same context structure.
✅ **Keep It Lean**: Only include necessary fields in the context (roles, tenant, permissions).
✅ **Fail Fast**: Validate the context early if it’s missing or invalid.
✅ **Test Thoroughly**: Mock the context in unit tests to isolate business logic.

---

## **Conclusion**

The **Authorization Context Extraction** pattern is a simple yet powerful way to handle authorization in backend applications. By centralizing context extraction, you reduce duplication, improve consistency, and make your code more secure and maintainable.

Next time you’re building an API or backend service, ask yourself:
- *Where is my authorization context coming from?*
- *Is it being reused across my application?*
- *Can I extract it more efficiently?*

If the answer isn’t obvious, start applying this pattern. Your future self (and your team) will thank you.

---
**Further Reading**
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://auth0.com/blog/critical-jwt-security-considerations/)
- [Role-Based Access Control (RBAC) Patterns](https://www.securecoding.cert.org/confluence/display/java/RBAC+Pattern)
```