```markdown
# **Immutable Context Pattern: Locking Down Security in Database Operations**

*How FraiseQL binds authentication and authorization context once per request to prevent privilege escalation—and why this matters for your API design.*

---

## **Introduction**

When you write a backend service, security isn’t just about adding `WHERE current_user_id = ...` to every query. It’s about enforcing access controls **consistently**—even when your code branches, routes, or modifies data in unexpected ways.

Imagine this:
- A user with `READ` permissions tries to delete a record via a "safe" UI button.
- Your middleware sets `current_user_id` and `user_privileges`.
- Meanwhile, your query logic lets the user escalate to `WRITE` permissions by modifying variables in memory.
- **BOOM.** A malicious actor bypasses authorization.

This is why the **Immutable Context Pattern** exists: to freeze security-sensitive data (like user identity and permissions) **once per request** and prevent tampering later. This pattern isn’t just for databases—it applies to APIs, microservices, and even frontend state—but we’ll focus on database-driven scenarios since they’re where privilege escalation is most dangerous.

By the end of this post, you’ll see:
✅ Why mutable context is a security risk
✅ How FraiseQL (and similar systems) implement immutable context
✅ Practical code examples in Go, JavaScript, and SQL
✅ Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Mutable Context Allows Privilege Escalation**

Most backend systems pass security context (e.g., user ID, permissions) through middleware—like JSON Web Tokens, session variables, or database connections. But once that context hits your application logic, things go wrong:

1. **Context Leaks:** User data gets stored in local variables, function arguments, or even query parameters.
   ```go
   // ❌ Dangerous: Passing context to a lower-privilege handler
   func deleteResource(request *http.Request, conn *sql.DB) error {
       userID := getUserIDFromRequest(request) // Context can be modified!
       _, err := conn.Exec(deleteQuery, userID) // What if userID changes later?
       return err
   }
   ```

2. **Race Conditions:** Async code (e.g., goroutines, promises) may read/stub context after it’s been invalidated.
   ```javascript
   // ❌ Race condition: Context lost in async
   async function handleRequest(req) {
       const user = await authMiddleware(req); // Context here
       setTimeout(() => { req.currentUser = "admin" }, 100); // Later: Tampered!
       await db.query("DELETE FROM *"); // Not the original user!
   }
   ```

3. **Query Injection:** Even if you validate context in middleware, a malicious payload could overwrite it.
   ```sql
   -- ❌ SQL injection via dynamic context
   EXECUTE deleteQuery USING (malicious_user_id_here); -- Not the original user!
   ```

The root cause? **Context is mutable.** Once you assign it to a variable or pass it to a function, it can change—even if you forget to update all references.

---

## **The Solution: Immutable Context Pattern**

The Immutable Context Pattern solves this by:
1. **Baking context into a single, sealed object** (e.g., a struct or wrapper) at request startup.
2. **Propagating that object immutably** to all components (queries, services, middleware).
3. **Wrapping database operations** to enforce context checks during execution.

### **Key Insights**
- **Immutability prevents tampering.** Once set, the context cannot be altered.
- **Side-by-side execution.** All query planning (e.g., FraiseQL) happens with the original context.
- **Defense in depth.** Even if a query escapes your control (e.g., via `EXECUTE`), the context remains intact.

---

## **Components of the Immutable Context Pattern**

Here’s how it works in practice:

| Component          | Role                                                                 |
|--------------------|-----------------------------------------------------------------------|
| **Context Wrapper** | Immutable struct storing user ID, permissions, etc. (e.g., `AuthContext`). |
| **Request Hook**   | Middleware that binds context to the request object before processing. |
| **Query Engine**   | Processes queries with the context sealed in place (e.g., FraiseQL). |
| **Error Response** | Explicitly rejects unauthorized operations with 403/401.                |

---

## **Code Examples**

### **1. Immutable Context Wrapper (Go)**
```go
// auth.go
package auth

import (
	"errors"
	"time"
)

type UserRole int

const (
	RoleGuest UserRole = iota
	RoleUser
	RoleAdmin
)

type AuthContext struct {
	UserID     uint64
	Roles      []UserRole
	ExpiresAt  time.Time
	IsValid    bool
}

// NewAuthContext creates an immutable copy (Go slices are reference types, so we deep-copy roles)
func NewAuthContext(userID uint64, roles []UserRole, expiresAt time.Time) AuthContext {
	return AuthContext{
		UserID:     userID,
		Roles:      append([]UserRole(nil), roles...), // Deep copy
		ExpiresAt:  expiresAt,
		IsValid:    true,
	}
}

// CheckRole returns true if the user has the role, without exposing the full context.
func (ac AuthContext) CheckRole(role UserRole) bool {
	if !ac.IsValid {
		return false
	}
	for _, r := range ac.Roles {
		if r == role {
			return true
		}
	}
	return false
}
```

### **2. Middleware Binding (JavaScript)**
```javascript
// authMiddleware.js
function createAuthContext(req, res, next) {
    const token = req.headers.authorization;
    if (!token) {
        return res.status(401).json({ error: "Unauthorized" });
    }

    // Validate token (e.g., JWT decode)
    const { userId, roles, expiresAt } = validateToken(token);

    // Create an immutable context
    const authContext = {
        userId,
        roles: [...roles], // Defensive copy
        expiresAt: new Date(expiresAt),
        isValid: true,
    };

    req.authContext = authContext;
    next();
}
```

### **3. Query Execution with Immutable Context (FraiseQL Example)**
FraiseQL (a hypothetical SQL engine) enforces context at compile time:

```sql
-- FraiseQL: Context is baked into the query plan
CREATE QUERY deletePost(postID) AS
    DELETE FROM posts
    WHERE posts.id = postID AND
          current_user_id = 123 AND         -- From AuthContext
          current_privileges & (1 << WRITE) -- From AuthContext
```

**How it works internally:**
1. The query engine **locks** the `AuthContext` at request time.
2. **All derived checks** (e.g., `current_user_id`) reference this context.
3. If context is tampered with later (e.g., via `EXECUTE`), the query **fails with 403**.

---

## **Implementation Guide**

### **Step 1: Define Your Context Structure**
```go
type DBContext struct {
    UserID     uint64
    Permissions map[string]bool // e.g., {"read": true, "write": false}
    CreatedAt  time.Time
}
```

### **Step 2: Middleware to Bind Context**
```go
// middleware.go
func AuthMiddleware(next http.HandlerFunc) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        // Validate token, extract user data
        ctx := NewDBContext(userID, permissions)

        // Attach context to the request (or use a context.Context)
        r = r.WithContext(context.WithValue(r.Context(), "authContext", ctx))

        next.ServeHTTP(w, r)
    }
}
```

### **Step 3: Enforce Context in Queries**
#### **Option A: Parameterized Queries (Safe)**
```sql
-- ✅ Safe: Context passed as params
DELETE FROM items
WHERE id = $1 AND user_id = (SELECT user_id FROM auth_context);
```

#### **Option B: Database-Side Enforcement (FraiseQL-Style)**
```sql
-- ✅ Even safer: Context enforced in query engine
SELECT * FROM items
WHERE id = 1 AND security_check(user_id, 'write') = true;
```

### **Step 4: Handle Async Operations**
```go
// In Go: Pass context to goroutines
func handleRequest(ctx context.Context, w http.ResponseWriter, r *http.Request) {
    authCtx := ctx.Value("authContext").(DBContext)
    go asyncTask(authCtx) //Context remains immutable
}

func asyncTask(authCtx DBContext) {
    // authCtx is read-only; tampering here has no effect!
    fmt.Println("User:", authCtx.UserID)
}
```

---

## **Common Mistakes to Avoid**

### **1. Forgetting to Deep-Copy Context**
❌ **Bad:** Slices/arrays are reference types:
```go
authCtx.Roles = []UserRole{RoleUser} // Another function can modify this!
```

✅ **Fix:** Always deep-copy immutable data:
```go
authCtx.Roles = append([]UserRole(nil), roles...)
```

### **2. Using Context as a Mutable Variable**
❌ **Bad:** Storing context in local variables:
```go
func deleteItem(conn *sql.DB, ctx DBContext) error {
    userID := ctx.UserID // Now ctx is exposed!
    // ...
    userID = 999          // Tampering possible!
}
```

✅ **Fix:** Pass context by reference but enforce immutability:
```go
func deleteItem(conn *sql.DB, ctx *DBContext) error {
    if !ctx.CheckRole(RoleAdmin) { // Uses context methods
        return errors.New("forbidden")
    }
    // ctx is read-only (e.g., via Getter methods)
}
```

### **3. Bypassing Context in Async Code**
❌ **Bad:** Async tasks ignore context:
```go
go func() {
    db.Query("DELETE FROM *") // No context check!
}.()
```

✅ **Fix:** Propagate context to all goroutines:
```go
go func(ctx context.Context) {
    authCtx := ctx.Value("authContext").(DBContext)
    // Always use the context!
}.(r.Context())
```

### **4. Overrelying on ORM "Magic"**
❌ **Bad:** Assuming ORMs like Hibernate/GORM lock context:
```go
// GORM "automatically" checks permissions? Nope!
db.Where("id = ?", post.ID).Delete(&Post{})
```

✅ **Fix:** Write explicit checks:
```go
if !authCtx.CheckRole(RoleAdmin) {
    return ErrPermissionDenied
}
db.Where("id = ? AND user_id = ?", post.ID, authCtx.UserID).Delete(&Post{})
```

---

## **Key Takeaways**

- **Immutable context prevents privilege escalation** by freezing security data early.
- **Deep-copy mutable fields** (e.g., slices, maps) to avoid reference leaks.
- **Enforce context at the database level** (e.g., FraiseQL-style checks) for defense in depth.
- **Propagate context to async operations** to ensure consistency.
- **Avoid ORM "magic"**—explicit checks are safer than relying on abstraction.

---

## **Conclusion**

The Immutable Context Pattern isn’t about reinventing authentication—it’s about **defending against the negative consequences of mutable state**. In systems where even a single missed check can lead to data breaches (e.g., SaaS applications, admin panels), this pattern is a must.

**Try it yourself:**
1. Start with a minimal `AuthContext` struct.
2. Bind it in middleware using Go’s `context.Context` or JavaScript’s `req.authContext`.
3. Enforce checks in every database operation, even async ones.

For databases like PostgreSQL, you can extend this with **row-level security (RLS)** or **PL/pgSQL hooks** to ensure queries never bypass context. For FraiseQL-like engines, treat context as a **compile-time invariant**.

Would you like a deeper dive into how FraiseQL specifically implements this? Or examples for other languages (Python, Rust)? Let me know in the comments!

---
```

---
**P.S.** This pattern works best when combined with:
- **Least Privilege:** Database users with minimal permissions.
- **Audit Logging:** Tracking when/where context checks fail.
- **Input Validation:** Beyond context, always validate query parameters.

Happy coding—and may your context always remain immutable! 🚀