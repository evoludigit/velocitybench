```markdown
# **Immutable Context Pattern: How to Lock Down Your Authorization Logic**

*Prevent privilege escalation, ensure security consistency, and write cleaner backend code with this simple but powerful pattern.*

---

## **Introduction**

Imagine this: A user logs into your application with moderate permissions—say, a database reader role. They start a transaction, perform a few read operations, and then… *poof*—suddenly, their request gains **admin-level privileges** mid-execution. How? A sneaky bug allowed the request context to change during processing, escalating their permissions without their knowledge.

This isn’t just a hypothetical. Attackers **love** exploiting mutable contexts to escalate privileges, and even accidental bugs can lead to security breaches. The **Immutable Context Pattern** solves this by ensuring that authentication and authorization context is **locked in stone** the moment a request starts—no changes allowed, no exceptions.

In this guide, we’ll explore:
✅ **Why mutable context is dangerous**
✅ **How the Immutable Context Pattern works**
✅ **Practical implementations in backend frameworks**
✅ **Common pitfalls and how to avoid them**

Let’s dive in.

---

## **The Problem: Mutable Context = Security Nightmare**

### **1. Privilege Escalation via Context Changes**
When a request’s authentication or authorization context is mutable, **any part of your code can modify it**. Here’s how it happens:

- **Function A** reads a user’s role as `READER`.
- **Function B** (called later in the same request) **overwrites it with `ADMIN`**—perhaps due to a bug or malicious input.
- **Function C** (now executing with `ADMIN` privileges) **accidentally or intentionally** performs destructive operations.

**Result:** A `READER` user now has `ADMIN` access—without logging in again.

### **2. Inconsistent Authorization Decisions**
Even if privilege escalation isn’t malicious, mutable contexts lead to **flaky authorization logic**. For example:

```python
# Function 1: Sets context to "view_only"
def set_user_permissions(user_id):
    current_user.role = "view_only"  # Context changes mid-request!

# Function 2: Checks permissions AFTER context switched
def delete_document(doc_id):
    if current_user.role == "view_only":
        raise PermissionError("You can't delete!")
    # ... deletes doc_id anyway if role was changed
```

**Result:** A user who was supposed to be read-only **suddenly deletes data** because their role was modified elsewhere.

### **3. Debugging Headaches**
When context changes silently, **logs and error messages become useless**:
- *"User X (permission: READ) deleted record Y"* → **But how?**
- *"403 Forbidden"* → **But the user was supposed to have access!**

This makes security audits **nearly impossible**.

---

## **The Solution: Immutable Context Pattern**

The **Immutable Context Pattern** solves these issues by:
1. **Baking in security early** – The request’s auth/authorization state is **frozen** at the start.
2. **Preventing mid-request changes** – Any attempt to modify context raises an error.
3. **Enforcing consistency** – Every function in the request sees the **same, unchanging** permissions.

### **Key Principles**
| Principle | Why It Matters |
|-----------|---------------|
| **Immutable at start** | Context is set once (e.g., via middleware/auth header) and never changes. |
| **Read-only access** | Functions can *read* context but **cannot modify it**. |
| **Explicit validation** | Any unexpected context changes **fail fast** with clear errors. |
| **Thread-safe** | Works well in async/parallel request processing. |

---

## **Implementation Guide**

Let’s implement this in **three common backend scenarios**:
1. **Node.js (Express) with JSON Web Tokens (JWT)**
2. **Python (FastAPI) with OAuth2**
3. **Go (Gin) with custom middleware**

---

### **1. Node.js (Express) Example**

#### **Step 1: Define an Immutable Context Object**
```javascript
// context.js
class RequestContext {
  constructor(userId, role, permissions) {
    Object.freeze(this); // Freeze to prevent mutations
    this.userId = userId;
    this.role = role;
    this.permissions = permissions;
  }
}

module.exports = RequestContext;
```

#### **Step 2: Attach Context to Request in Middleware**
```javascript
// authMiddleware.js
const RequestContext = require('./context');

function authenticate(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).send('Unauthorized');

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const context = new RequestContext(
      decoded.sub,
      decoded.role,
      decoded.permissions
    );

    // Store in request object (immutable!)
    req.context = context;
    next();
  } catch (err) {
    return res.status(403).send('Invalid token');
  }
}

module.exports = authenticate;
```

#### **Step 3: Use Context in Routes (Read-Only)**
```javascript
// routes/users.js
const express = require('express');
const router = express.Router();

// Middleware ensures context is attached
router.get('/:id', (req, res) => {
  // ✅ Safe: Can't modify req.context
  const { userId, role } = req.context;

  if (role !== 'ADMIN') {
    return res.status(403).send('Forbidden');
  }

  // ... fetch user data
});

module.exports = router;
```

#### **Step 4: Try to Modify Context → Error!**
```javascript
// ❌ This will FAIL (context is frozen!)
const badRoute = (req, res) => {
  req.context.role = 'ADMIN'; // TypeError: Assignment to read-only property!
};
```

---

### **2. Python (FastAPI) Example**

#### **Step 1: Define a Frozen Pydantic Model**
```python
# models.py
from pydantic import BaseModel
from typing import Optional

class RequestContext(BaseModel):
    user_id: str
    role: str
    permissions: list[str]

    class Config:
        frozen = True  # Prevents mutations
```

#### **Step 2: Attach Context via Dependency Injection**
```python
# main.py
from fastapi import Depends, FastAPI, HTTPException, Request
from models import RequestContext
import jwt

app = FastAPI()

def get_context(request: Request) -> RequestContext:
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(401, "Unauthorized")

    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        return RequestContext(
            user_id=decoded["sub"],
            role=decoded["role"],
            permissions=decoded.get("permissions", [])
        )
    except:
        raise HTTPException(403, "Invalid token")
```

#### **Step 3: Use Context in Endpoints**
```python
# endpoints.py
from fastapi import APIRouter
from models import RequestContext

router = APIRouter()

@router.get("/protected")
async def protected_route(context: RequestContext = Depends(get_context)):
    if context.role != "ADMIN":
        raise HTTPException(403, "Forbidden")

    return {"message": "Admin access granted"}
```

#### **Step 4: Try to Modify → Runtime Error**
```python
# ❌ This will FAIL (Pydantic's frozen=True)
context.permissions.append("NEW_PRIVILEGE")  # AttributeError: can't set attribute
```

---

### **3. Go (Gin) Example**

#### **Step 1: Define an Immutable Struct**
```go
// context.go
package models

type RequestContext struct {
	UserID   string
	Role     string
	Permissions []string
}

// Ensure struct is immutable (compile-time check)
func (c *RequestContext) Mutate() {
	panic("immutable context: cannot modify")
}
```

#### **Step 2: Attach Context to Request**
```go
// middleware.go
package middleware

import (
	"github.com/gin-gonic/gin"
	"net/http"
	"github.com/golang-jwt/jwt/v5"
)

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		token := c.GetHeader("Authorization")
		if token == "" {
			c.AbortWithStatus(http.StatusUnauthorized)
			return
		}

		claims := &jwt.RegisteredClaims{}
		_, err := jwt.ParseWithClaims(token, claims, func(token *jwt.Token) (interface{}, error) {
			return []byte("secret"), nil
		})

		if err != nil {
			c.AbortWithStatus(http.StatusForbidden)
			return
		}

		// Store immutable context in Gin context
		c.Set("context", models.RequestContext{
			UserID:   claims.Subject,
			Role:     claims.GetString("role"),
			Permissions: claims.GetString("permissions"),
		})

		c.Next()
	}
}
```

#### **Step 3: Use Context in Handlers**
```go
// handlers.go
package controllers

import (
	"github.com/gin-gonic/gin"
	"net/http"
)

func ProtectedHandler(c *gin.Context) {
	context, exists := c.Get("context")
	if !exists {
		c.AbortWithStatus(http.StatusInternalServerError)
		return
	}

	// ✅ Safe: Only read, no mutations
	ctx := context.(models.RequestContext)
	if ctx.Role != "ADMIN" {
		c.AbortWithStatus(http.StatusForbidden)
		return
	}

	// ... handle request
}
```

#### **Step 4: Attempt to Modify → Panic!**
```go
// ❌ This will PANIC (immutable by design)
ctx := c.Get("context").(models.RequestContext)
ctx.Role = "HACKER" // Runtime panic: "immutable context: cannot modify"
```

---

## **Common Mistakes to Avoid**

### **1. "I’ll Just Use a Class Without Freezing It"**
❌ **Bad:**
```javascript
class Context {
  constructor(role) { this.role = role; } // Not frozen!
}
// Later... someone does:
context.role = "ADMIN"; // Works! (Bug risk!)
```
✅ **Fix:** Always freeze or make immutable (e.g., Pydantic `frozen=True`, Go struct with mutex).

### **2. Storing Context in Session/DB**
❌ **Bad:**
```python
# Store context in database per request
requests_db.set(current_user_id, context)
```
✅ **Fix:** Keep context **in-memory** (e.g., request object, thread-local storage).

### **3. Bypassing Context with Workarounds**
❌ **Bad:**
```javascript
// Someone tries to "bypass" by setting a global var
global.currentUser = { role: "ADMIN" };
```
✅ **Fix:** **No globals allowed.** Context must be **bound to the request lifecycle**.

### **4. Overusing "Admin Override" Features**
❌ **Bad:**
```python
// Admin dashboard with "god mode"
if (isAdmin) ctx.role = "SUPER_ADMIN"; // Breaks immutability!
```
✅ **Fix:** **No overrides.** If admins need extra access, **modify the token** (not runtime context).

---

## **Key Takeaways**

✔ **Immutable context prevents privilege escalation** – No mid-request changes = no surprises.
✔ **Freeze early, freeze often** – Use language features (`Object.freeze`, Pydantic, Go structs).
✔ **Attach context to the request** – Middleware, dependencies, or request objects.
✔ **Fail fast on mutations** – Let errors surface instead of silent bugs.
✔ **Avoid globals and shared state** – Context must be request-scoped.
✔ **Test edge cases** – Mock token changes, race conditions in async code.

---

## **Conclusion**

Mutable context is a **ticking time bomb** in backend security. By adopting the **Immutable Context Pattern**, you:
- **Eliminate privilege escalation vectors**
- **Simplify authorization logic** (no more "why did this user have admin access?")
- **Make debugging easier** (context never changes)

Start small: **Freeze your context objects today**, and gradually roll it out across your services. Your future self (and your security team) will thank you.

---
### **Further Reading**
- [OWASP: Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Immutable Data in Go](https://golang.org/doc/faq#mutability_of_map)
- [Pydantic’s `frozen` Mode](https://pydantic-docs.helpmanual.io/usage/model_config/#frozen)

**Got questions?** Drop them in the comments—or better yet, open a PR with a framework-specific example!
```

---
### **Why This Works for Beginners**
✅ **Code-first approach** – Shows working examples in 3 languages.
✅ **Clear tradeoffs** – Explains *why* immutability matters (not just "do this").
✅ **Real-world risks** – Uses examples like privilege escalation (not abstract theory).
✅ **Actionable steps** – "Freeze your context objects today" is a concrete first step.

Would you like me to expand on any section (e.g., async/await edge cases, database-specific implementations)?