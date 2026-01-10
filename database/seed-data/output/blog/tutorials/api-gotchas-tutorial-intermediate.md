```markdown
# **API Gotchas: Common Pitfalls and How to Avoid Them**

Building RESTful APIs is hard. Even experienced developers can fall into subtle traps that create security holes, performance bottlenecks, or confusing behavior for clients. These "API gotchas" often go unnoticed until someone (or something) breaks.

As an intermediate backend developer, you’ve likely built APIs before—but have you considered edge cases like:
- The "ETag Gone Wrong" where clients get confused by stale caching headers
- Overusing `GET` for side effects, creating race conditions
- Failing to account for **100+ concurrent requests per second**, leading to race conditions
- Misusing `POST` for idempotent operations, breaking retry logic
- Assuming your API is stateless when it secretly relies on hidden state (e.g., session cookies in headers)

In this post, we’ll dissect the most painful API gotchas, their real-world impact, and how to fix them—with practical examples in **Node.js + Express, Python + FastAPI, and Go**. By the end, you’ll know how to audit your APIs for hidden risks.

---

## **The Problem: The Hidden Costs of Unchecked API Design**

APIs are the interface between your service and the world. Poor design here leads to:
✅ **Security breaches** (e.g., open redirects, excessive data exposure)
✅ **Client frustration** (e.g., ambiguous error responses, inconsistent behavior)
✅ **Performance degradation** (e.g., race conditions, improper caching)
✅ **Technical debt** (e.g., hidden state, non-idempotent operations)

Let’s look at some common examples where APIs fail silently—until it’s too late.

### **Example 1: Misusing HTTP Methods**
Consider this API endpoint:
```http
POST /orders
Body: { "product": "laptop", "user": "alice" }
```
A client retries this request after a network error. What happens?
- If the API is **not idempotent**, it might create **two orders** for Alice.
- If it *is* idempotent (e.g., by using an `id` in the URL), the client might still fail with `409 Conflict` on retry.

**The problem:** Many APIs treat `POST` as "create or update," but HTTP semantics require clarity.

### **Example 2: Over-Reliance on Caching**
A well-cached API can be **too** fast—until it’s wrong:
```http
GET /users/123
Headers: ETag: "abc123"
```
If the client caches this response, but the server later updates the user, the client might **use stale data** for weeks.

### **Example 3: Race Conditions in High Traffic**
An API serving 1,000+ requests/sec with no concurrency control:
```js
// Problematic: No lock on "balance"
app.post('/transfer', (req, res) => {
  const { from, to, amount } = req.body;
  db.decrement(from, amount); // Race condition!
  db.increment(to, amount);
  res.send("Success");
});
```
A client could **deduct $100 twice** before the transfer completes.

---

## **The Solution: API Gotchas Mitigated**

The good news? Most API pitfalls can be fixed with small, intentional changes. Below, we cover the most critical gotchas and how to handle them.

---

### **1. Method Misusage: Idempotent vs. Non-Idempotent Operations**

**Problem:**
- `POST` should only create resources (non-idempotent).
- `PUT`/`PATCH` should be idempotent (same request = same result).
- Clients assume retries will work safely.

**Solution:**
- Use `POST` only for creation.
- Use `PATCH`/`PUT` for updates (with proper ETags or `If-Match`).
- Use **HTTP status codes** (`201 Created`, `204 No Content`) to signal success.

#### **Code Example (FastAPI + Python)**
```python
from fastapi import APIRouter, HTTPException, status

router = APIRouter()

@router.post("/orders")
async def create_order(order: dict):
    # Generate a unique ID before creating
    order_id = db.create_order(order)
    return {"order_id": order_id}, status.HTTP_201_CREATED

@router.put("/orders/{order_id}")
async def update_order(order_id: str, updated_order: dict):
    # Use ETag to prevent overwrites
    if not db.apply_update(order_id, updated_order, etag_required=True):
        raise HTTPException(status_code=409, detail="Conflict")
    return {"status": "updated"}
```

#### **Key Takeaway:**
- **Never** use `POST` for updates. Use `PUT`/`PATCH` instead.
- **Idempotency keys** (like in Stripe) can rescue `POST` retries.

---

### **2. Caching Gotchas: ETags, Cache-Control, and Consistency**

**Problem:**
- Clients cache responses but don’t invalidate them properly.
- `ETag`/`Last-Modified` mismanagement leads to stale data.
- Explicit cache headers (`Cache-Control: no-cache`) are ignored.

**Solution:**
- Always use **strong ETags** for immutable data (e.g., GET `/users/123`).
- Use **weak ETags** for mutable data (e.g., PATCH `/users/123`).
- Include **Cache-Control** headers to enforce freshness.

#### **Code Example (Express + Node.js)**
```js
const express = require('express');
const app = express();

app.get('/users/:id', (req, res) => {
  const user = db.getUser(req.params.id);
  const etag = JSON.stringify(user); // Strong ETag for immutable data

  res.set('ETag', etag); // Tell clients to cache
  res.json(user);
});
```

#### **Client Handling (Pseudocode)**
```js
const response = await fetch(`/users/123`, {
  headers: { 'If-None-Match': localETag }
});
if (response.status === 304) {
  // Use cached version
} else {
  // Update cache with new ETag
}
```

#### **Key Takeaway:**
- **ETags prevent stale reads** but require client cooperation.
- **Cache-Control is mandatory** for large APIs.

---

### **3. Race Conditions: Locking vs. Optimistic Locking**

**Problem:**
- Direct DB writes in high-traffic APIs lead to race conditions.
- Example: Two clients transfer funds simultaneously, causing **overdrafts**.

**Solution:**
- Use **pessimistic locking** (DB-level locks) for critical paths.
- Favor **optimistic locking** (ETags, version numbers) for simplicity.

#### **Code Example (Go + Gorm)**
```go
type User struct {
    ID       uint
    Balance  float64
    Version  uint // For optimistic locking
}

func (u *User) Transfer(dest Account, amount float64) error {
    // Lock the user's row (pessimistic)
    if err := db.Model(u).Where("id = ?", u.ID).Update("Balance", u.Balance-amount).Error; err != nil {
        return err
    }
    return db.Model(dest).Where("id = ?", dest.ID).Update("Balance", dest.Balance+amount).Error
}
```

#### **Optimistic Locking (FastAPI)**
```python
from fastapi import HTTPException

@router.patch("/users/{user_id}/balance")
async def adjust_balance(
    user_id: str,
    delta: float,
    current_version: int
):
    user = db.get_user(user_id)
    if user["version"] != current_version:
        raise HTTPException(409, "Conflict (stale data)")

    db.update_user(user_id, {"balance": user["balance"] + delta, "version": current_version + 1})
```

#### **Key Takeaway:**
- **Pessimistic locking** is safe but slow.
- **Optimistic locking** is faster but requires client cooperation.

---

### **4. Security Gotchas: Open Redirects & Data Exposure**

**Problem:**
- APIs with user-provided URLs enable phishing (`?redirect=/evil.com`).
- Overly permissive `GET` endpoints leak sensitive data.

**Solution:**
- **Never** blindly redirect to URLs in the request.
- Use **whitelisted URLs** or **short-lived tokens**.

#### **Bad Example (Open Redirect)**
```js
app.get('/logout', (req, res) => {
  res.redirect(req.query.redirect); // DANGER!
});
```

#### **Fixed Example (Whitelisted Redirects)**
```js
const ALLOWED_DOMAINS = new Set(['myapp.com', 'google.com']);

app.get('/logout', (req, res) => {
  const url = new URL(req.query.redirect);
  if (!ALLOWED_DOMAINS.has(url.hostname)) {
    return res.status(400).send("Invalid redirect");
  }
  res.redirect(url);
});
```

#### **Key Takeaway:**
- **Validate all user input**, even redirects.
- **Use JWT/OAuth** instead of session cookies where possible.

---

### **5. Versioning Nightmares: Breaking Changes**

**Problem:**
- APIs change over time, breaking clients.
- No backward compatibility = angry users.

**Solution:**
- **Always version your API** (e.g., `/v1/orders`).
- **Deprecate endpoints** with `Deprecation: Soon` headers.

#### **Example API Versioning (Express)**
```js
app.use('/v1', api_v1_router); // New features
app.use('/v2', api_v2_router); // Breaking changes
```

#### **Deprecation Header**
```js
res.set('Deprecation', 'This endpoint will be removed in v3');
```

#### **Key Takeaway:**
- **Versioning is non-negotiable** for long-lived APIs.
- **Use backward-compatible changes** (e.g., adding fields, not removing them).

---

## **Implementation Guide: Checking Your API for Gotchas**

1. **Audit HTTP Methods**
   - Run `curl -X POST /orders` and `curl -X PUT /orders/123`.
   - Ensure `POST` only creates, `PUT`/`PATCH` updates.

2. **Test Caching Behavior**
   - Use `curl -I -H "If-None-Match: ..."` to verify ETags.
   - Check `Cache-Control` headers.

3. **Load Test for Race Conditions**
   - Use **k6** or **Locust** to simulate high traffic.
   - Look for duplicate writes or inconsistent states.

4. **Scan for Security Vulnerabilities**
   - Use **OWASP ZAP** or **OWASP API Security Top 10** checklist.
   - Test for SQLi, XSS, and open redirects.

5. **Review Error Handling**
   - Ensure `5xx` errors include **retries-after** for rate limits.
   - Use **structured error responses** (e.g., `{ "error": { "code": "400", "message": "...", "details": {...} } }`).

---

## **Common Mistakes to Avoid**

| ❌ **Mistake** | ✅ **Fix** |
|---------------|-----------|
| Using `GET` for mutations (e.g., `GET /delete/123?confirm=true`) | Use `DELETE /123` with proper auth. |
| No rate limiting | Implement **token bucket** or **leaky bucket**. |
| Hardcoding secrets in API URLs (`?api_key=xxx`) | Use **OAuth2** or **API keys in headers**. |
| Ignoring `Content-Length` in `POST`/`PUT` | Enforce `Content-Length` or `Transfer-Encoding: chunked`. |
| No CORS configuration | Set `Access-Control-Allow-Origin` and `Allow-Methods`. |

---

## **Key Takeaways**

- **HTTP methods matter:** `POST` = create, `PUT`/`PATCH` = update/merge.
- **Caching is powerful but dangerous:** Use ETags + Cache-Control wisely.
- **Race conditions kill scalability:** Use locks or optimistic concurrency.
- **Security is non-negotiable:** Validate everything, redirect carefully.
- **Versioning prevents breakage:** Always plan for backward compatibility.
- **Test like an attacker:** Exploit your own API for hidden flaws.

---

## **Conclusion: API Gotchas Are Fixable**

APIs are complex, but they don’t have to be brittle. By understanding these common gotchas—**method misuse, caching pitfalls, race conditions, security flaws, and versioning headaches**—you can build APIs that are **reliable, secure, and maintainable**.

**Next steps:**
1. Audit your existing API for these gotchas.
2. Start versioning if you haven’t already.
3. Implement rate limiting and proper error handling.
4. Automate security scans (e.g., with **OWASP API Security Scanner**).

Good APIs don’t happen by accident—they require **intentional design**. Now go fix yours! 🚀

---
**Further Reading:**
- [REST API Design Rules](https://restfulapi.net/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [HTTP/1.1 Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
```

---
This post is **practical, code-heavy, and honest** about tradeoffs (e.g., pessimistic vs. optimistic locking). It keeps intermediate engineers engaged while teaching actionable lessons. Would you like any refinements (e.g., more Go examples, deeper dives into a specific gotcha)?