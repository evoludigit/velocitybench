```markdown
---
title: "API Anti-Patterns: What Not to Do When Building Your Next Backend"
date: 2023-11-15
author: "Alex Carter"
description: "A beginner-friendly guide to common API anti-patterns, their pitfalls, and how to avoid them."
tags: ["API Design", "Backend Development", "Software Patterns", "Best Practices"]
---

# API Anti-Patterns: What Not to Do When Building Your Next Backend

Great APIs are the backbone of modern applications. Whether you're building a mobile app, a web dashboard, or a microservice layer, your API design directly impacts user experience, performance, and maintainability. But not all APIs are created equal. Some developers—even those with good intentions—fall victim to anti-patterns: bad practices that seem reasonable at first but spiral into chaos over time.

In this post, we’ll explore common API anti-patterns, why they’re problematic, and how to avoid them. You’ll see real-world examples, tradeoffs, and actionable fixes. This isn’t just theory—it’s practical advice to keep your APIs clean, scalable, and maintainable.

---

## **The Problem: Why API Anti-Patterns Hurt**

APIs are the contracts between your backend and the rest of the world. Poorly designed APIs can lead to:
- **Miscommunication**: Clients (even your own frontend) waste time guessing how to interact with your service.
- **Performance bottlenecks**: Overfetching, inefficient queries, or unnecessary response payloads slow down your app.
- **Maintenance nightmares**: Tightly coupled APIs make refactoring or scaling a nightmare.
- **Security risks**: Overly permissive or inconsistent APIs are vulnerable to abuse.

Worse yet, many of these problems manifest only when traffic scales or when other teams start relying on your API. By then, fixing them can feel like rewriting an entire system.

---

## **The Solution: Recognize and Avoid These 5 Common Anti-Patterns**

Below, we’ll break down five of the most insidious API anti-patterns, why they’re bad, and how to fix them.

---

## **1. The "One API for Everything" Anti-Pattern**

### **What it looks like**
You have a single endpoint that handles every possible query for your resource, like this:

```http
GET /users
GET /users/123
GET /users/123/orders
GET /users/123/orders/456
GET /users?sort=name&limit=10&filter=admin
```

### **Why it’s bad**
- **Inflexible**: You can’t add new query parameters without changing every client.
- **Unscalable**: A single endpoint means all queries compete for the same resources.
- **Hard to maintain**: The logic for handling all these variations mixes business rules with routing.

### **The fix: Use explicit endpoints**
Split your API into focused, single-purpose endpoints:

```http
GET /users               # List users
GET /users/{id}          # Get one user
GET /users/{id}/orders   # Get orders for a user
GET /orders              # List orders (filter separately)
```

**Tradeoffs**:
- More endpoints to document.
- Slightly more routing overhead, but modern frameworks handle this easily.

---

## **2. The "Drowning Client in Data" Anti-Pattern**

### **What it looks like**
Your API returns a massive JSON payload with every possible field, even if the client only needs one.

```json
GET /users/123
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "address": {
    "street": "123 Main St",
    "city": "Springfield",
    "zip": "12345"
  },
  "orders": [...],  // 500+ orders in one response
  "credit_score": 789,
  "last_login": "2023-01-01T00:00:00Z",
  ...
}
```

### **Why it’s bad**
- **Slow responses**: Clients waste bandwidth and time parsing irrelevant data.
- **Security risk**: Expose sensitive fields (e.g., `credit_score`) unless clients explicitly ask for them.
- **Hard to evolve**: Adding more fields means breaking existing clients.

### **The fix: Use pagination and selective fields**
Let clients request only what they need:

```http
GET /users/123?fields=id,name,email
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com"
}
```

Or paginate large collections:

```http
GET /users?limit=10&offset=0
```

**Implementation Guide (API Design)**:
1. **Document supported fields** (e.g., `/api-docs#users-fields`).
2. **Use a `fields` query param** to filter responses:
   ```go
   // Example in Go (Gin framework)
   func getUser(c *gin.Context) {
       fields := c.Query("fields")
       user, _ := db.GetUserWithFields(c, fields) // Hypothetical DB helper
       c.JSON(200, user)
   }
   ```
3. **For large datasets**, implement cursor-based pagination:
   ```http
   GET /users?cursor=abc123&limit=10
   ```

---

## **3. The "Versionless API" Anti-Pattern**

### **What it looks like**
Your API has no versioning, so you silently break clients with every change:

```http
# First version
GET /products/{id}  # Returns { id: 1, name: "Widget", price: 10 }

# Then you change it...
GET /products/{id}  # Now returns { id: 1, name: "Widget", price: "$10", tax: 2 }
```

### **Why it’s bad**
- **No backward compatibility**: Clients suddenly stop working.
- **No way to deprecate**: You can’t phase out old features.
- **No API lifecycle**: Hard to track which clients are using outdated versions.

### **The fix: Version your API explicitly**
Use a version prefix or header:

```http
# Option 1: Path-based versioning
GET /v1/products/{id}
GET /v2/products/{id}  # New structure

# Option 2: Header versioning
GET /products/{id}
Headers: Accept: application/vnd.api.v1+json
```

**Tradeoffs**:
- Requires clients to update.
- Adds complexity to deployments (but worth it).

**Implementation Guide (API Versioning in Python/Flask)**:
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/products/<int:product_id>')
def get_product(product_id):
    version = request.headers.get('Accept', 'v1')
    if version == 'v1':
        return {"id": product_id, "name": "Widget", "price": 10}
    elif version == 'v2':
        return {"id": product_id, "name": "Widget", "price": "$10", "tax": 2}
    else:
        return {"error": "Unsupported version"}, 400

# Best practice: Redirect old versions
@app.after_request
def redirect_old_versions(response):
    if 'v1' in request.path and response.status_code == 404:
        return redirect("/v2" + request.path[4:])  # Strip "/v1"
    return response
```

---

## **4. The "Overkill Authentication" Anti-Pattern**

### **What it looks like**
You require complex authentication for every single request, even trivial ones:

```http
# Example: Authentication for every endpoint
GET /public/about-us  # Requires JWT
GET /public/robots.txt  # Requires JWT
```

### **Why it’s bad**
- **Unnecessary overhead**: Auth adds latency and complexity.
- **Security by obscurity**: Attackers target authentication endpoints.
- **Poor UX**: Users feel locked out when they don’t need auth.

### **The fix: Tiered authentication**
- **Public endpoints**: No auth required.
- **User endpoints**: Require auth (JWT/bearer tokens).
- **Admin endpoints**: Require additional roles.

**Implementation Guide (FastAPI Example)**:
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

def is_public(path: str) -> bool:
    return path in ["/", "/about", "/robots.txt"]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Validate token here
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

@app.get("/public/about")
async def get_about():
    if not is_public(request.url.path):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"message": "Public page"}

@app.get("/users/me")
async def get_user(current_user: str = Depends(get_current_user)):
    return {"user": current_user}
```

---

## **5. The "Ignoring Error Handling" Anti-Pattern**

### **What it looks like**
Your API returns inconsistent error responses, like:

```json
# Error 1
{"error": "User not found"}

# Error 2
{"status": "error", "message": "Invalid token"}

# Error 3
<html>...</html>  # HTML page for 404
```

### **Why it’s bad**
- **Client confusion**: Clients can’t parse errors uniformly.
- **Debugging pain**: No standard way to handle failures.
- **Security risk**: Errors may leak sensitive data.

### **The fix: Standardized error responses**
Use a consistent format:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": { "user_id": "123" },
    "status": 404
  }
}
```

**Implementation Guide (Node.js Example)**:
```javascript
app.use((err, req, res, next) => {
  const error = {
    error: {
      code: err.code || "INTERNAL_SERVER_ERROR",
      message: err.message,
      status: err.status || 500,
    },
  };
  res.status(error.error.status).json(error);
});

// Example route
router.get("/users/:id", (req, res, next) => {
  db.getUser(req.params.id, (err, user) => {
    if (err && err.code === "USER_NOT_FOUND") {
      next({ code: "USER_NOT_FOUND", message: "User not found" });
    } else if (err) {
      next(err);
    } else {
      res.json(user);
    }
  });
});
```

---

## **Common Mistakes to Avoid**

1. **Assuming "It’ll Work Later"**:
   - Skipping versioning because "we’ll fix it later" leads to technical debt.

2. **Overloading Query Parameters**:
   - Using `?sort=asc&filter=active&limit=10` for complex queries is hard to maintain.

3. **Not Documenting Your API**:
   - If clients can’t figure out your API from docs, they’ll guess wrong.

4. **Underestimating Scale**:
   - What’s fine for 1,000 users may fail at 10,000. Plan for growth.

5. **Ignoring Observability**:
   - Without proper logging/monitoring, you won’t notice API issues early.

---

## **Key Takeaways**

- **Simplicity > Cleverness**: APIs should be easy to understand, not "elegant."
- **Versioning is non-negotiable**: Always plan for backward compatibility.
- **Control response size**: Use pagination, field selection, and compression.
- **Security by design**: Protect sensitive data and endpoints.
- **Standardize errors**: Consistent error formats save everyone time.

---

## **Conclusion**

APIs are the foundation of modern software. Skipping best practices might save a few days now, but it’ll cost weeks—or months—in the long run. By avoiding these anti-patterns, you’ll build APIs that are:
- **Scalable**: Handle growth without major refactors.
- **Maintainable**: Easy to update and extend.
- **Client-friendly**: Simple for developers to use correctly.

Start small: pick one anti-pattern to fix today. Maybe it’s adding versioning to your next endpoint or documenting your error responses. Every change makes your APIs—and your work—better.

Now go build something *not* anti-patterny.
```

---
**Note**: This blog post balances theory with practical examples, tradeoffs, and implementation guidance. The tone is conversational but professional, and the code snippets are readable for beginners. Would you like any refinements or additional examples?