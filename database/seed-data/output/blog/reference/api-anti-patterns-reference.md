# **[Pattern] API Anti-Patterns: Reference Guide**

---

## **Overview**
API anti-patterns are flawed design choices that introduce inefficiency, poor usability, security risks, or maintenance burdens. Avoiding these patterns ensures scalable, performant, and maintainable APIs that align with RESTful principles, best practices, and modern standards. This guide identifies common API anti-patterns, explains their pitfalls, and provides alternatives to promote cleaner, more effective API development.

---

## **Key Categorization of API Anti-Patterns**

| **Category**         | **Description**                                                                 | **Key Problems**                                                                 |
|----------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Over/Under-Posting** | Incorrect use of HTTP methods (e.g., GET for updates, PUT/DELETE for side effects). | Violates REST semantics, leads to ambiguity, and breaks client expectations.    |
| **Resource Nesting** | Overly nested resource structures (e.g., `/orders/123/products/456`).          | Increases latency, reduces scalability, and complicates caching.                |
| **Chatty APIs**      | Excessive round-trips via multiple endpoints for simple operations.           | Degrades performance, increases latency, and burdens clients.                    |
| **Versioning Gimmicks** | Poorly handled API versioning (e.g., version in query params, headers, or URLs). | Confuses clients, requires backward compatibility management, and complicates updates. |
| **Posting to GET**    | Using `GET` for operations with side effects (e.g., modifying data).           | Breaks immutability, enables accidental data corruption, and violates REST.     |
| **Over-Fetching**    | Returning excessive data (e.g., entire objects instead of fields).            | Increases payload size, slows clients, and wastes bandwidth.                    |
| **Under-Fetching**   | Missing critical metadata (e.g., timestamps, relationships) in responses.      | Forces clients to make additional requests, degrading performance.              |
| **Tight Coupling**   | API schema changes tied to client implementation details (e.g., hardcoded IDs). | Reduces flexibility, complicates refactoring, and breaks clients on updates.     |
| **Ignoring CORS**    | Failing to implement proper CORS headers for cross-origin requests.           | Blocks modern frontend integrations and limits API usability.                   |
| **Error Handling Chaos** | Inconsistent or poorly documented error responses (e.g., no standard status codes). | Confuses clients, makes debugging harder, and breaks automation.               |
| **Overly Complex Authentication** | Unnecessary or poorly designed auth flows (e.g., tokens in URLs, no refresh mechanisms). | Increases attack surface, complicates client implementation, and reduces security. |
| **Idempotency Ignored** | Non-idempotent operations (e.g., `DELETE` without checks).                     | Causes data inconsistency, especially in retry scenarios.                       |
| **Rate Limiting Abuse** | Poorly enforced or undocumented rate limits.                                  | Enables abuse, degrades service reliability, and frustrates legitimate users.    |
| **Hidden Dependencies** | Assumptions about client-side processing (e.g., API returns raw SQL results).  | Makes APIs brittle and non-portable to other systems.                          |
| **No API Docs**      | Lack of automated, up-to-date documentation.                                   | Increases onboarding time, reduces adoption, and invites misuse.               |

---

## **Detailed Breakdown of Anti-Patterns**

### **1. Over/Under-Posting (HTTP Method Abuse)**
**Problem:** Misusing HTTP verbs (e.g., using `GET` to delete or `POST` for updates).
**Example Anti-Pattern:**
```http
GET /users/123?delete=true  # Breaks immutability (GET should be safe).
POST /users/123/activate    # Unclear intent (is this a creation or side effect?).
```
**Solution:**
- Use `DELETE` for removal, `PATCH`/`PUT` for updates, `POST` for creations.
- Follow [RFC 7231](https://datatracker.ietf.org/doc/html/rfc7231) for method semantics.

---

### **2. Resource Nesting (Excessive Depth)**
**Problem:** Deeply nested URLs (e.g., `/users/123/orders/456/products/789`) slow down clients and servers.
**Example Anti-Pattern:**
```http
GET /users/123/orders/456/products/789
```
**Solution:**
- Use **query parameters** or **HATEOAS links** for filtering/expandability:
  ```http
  GET /users/123/orders?filter=product_id=789
  ```
- Flatten relationships with **graphQL-style joins** (if supported).

---
### **3. Chatty APIs (Excessive Round-Trips)**
**Problem:** Multiple calls for simple operations (e.g., fetching user + orders separately).
**Example Anti-Pattern:**
```http
GET /users/123          // Round-trip 1
GET /users/123/orders  // Round-trip 2
```
**Solution:**
- Use **aggregation endpoints**:
  ```http
  GET /users/123?include=orders
  ```
- Implement **client-side caching** (e.g., with `ETag` or `Last-Modified` headers).

---
### **4. Versioning Gimmicks**
**Problem:** Versioning hidden in URLs, headers, or query params (e.g., `/v1/users`, `Accept: application/vnd.api.v1+json`).
**Example Anti-Pattern:**
```http
GET /v2/users?version=1.0
```
**Solution:**
- Use **API endpoints** (`/v1/users`) or **headers** (`X-API-Version: 1`).
- Document deprecation timelines clearly.

---
### **5. Posting to GET (Side Effects in GET)**
**Problem:** Using `GET` for operations that modify data (e.g., `GET /payments?action=process`).
**Example Anti-Pattern:**
```http
GET /payments?action=refund
```
**Solution:**
- Use `POST` for side effects:
  ```http
  POST /payments/123/refund
  ```

---
### **6. Over-Fetching (Bloat in Responses)**
**Problem:** Returning entire objects when clients only need fields.
**Example Anti-Pattern:**
```json
// Full user object (but client only needs `name` and `email`).
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "address": { ... },
  "preferences": { ... }
}
```
**Solution:**
- Use **field selection**:
  ```http
  GET /users?fields=name,email
  ```
- Implement **partial responses** (e.g., GraphQL, JSON:API).

---
### **7. Under-Fetching (Missing Metadata)**
**Problem:** Omitting timestamps, relationships, or pagination data.
**Example Anti-Pattern:**
```json
// Missing `created_at`, `links`, or `pagination`.
{
  "id": 123,
  "name": "Alice"
}
```
**Solution:**
- Include **standard metadata**:
  ```json
  {
    "data": { "id": 123, "name": "Alice" },
    "links": { "self": "/users/123" },
    "pagination": { "total": 100 }
  }
  ```

---
### **8. Tight Coupling (Hardcoded Dependencies)**
**Problem:** API schemas tied to client-specific IDs or processing logic.
**Example Anti-Pattern:**
```http
// Client requires `internalId` field (not part of public API).
GET /users?internalId=abc123
```
**Solution:**
- Expose **public-facing fields only**.
- Use **query params** for filtering:
  ```http
  GET /users?status=active
  ```

---
### **9. Ignoring CORS**
**Problem:** Missing `Access-Control-Allow-Origin` headers, blocking frontend use.
**Example Anti-Pattern:**
```http
// No CORS headers → Frontend blocked.
GET /api/data
```
**Solution:**
- Set proper CORS headers:
  ```http
  HTTP/1.1 200 OK
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE
  ```

---
### **10. Error Handling Chaos**
**Problem:** Inconsistent error formats (e.g., mixing `500` with custom `419` codes).
**Example Anti-Pattern:**
```json
{
  "error": "Invalid input",  // No status code!
  "code": 400,
  "details": "Missing 'name'."
}
```
**Solution:**
- Follow **standard HTTP status codes** (e.g., `400 Bad Request`).
- Include **structured error payloads**:
  ```json
  {
    "status": 400,
    "title": "Validation Failed",
    "details": ["Missing 'name' field."]
  }
  ```

---
### **11. Overly Complex Authentication**
**Problem:** Tokens in URLs (`/login?token=abc`), no refresh mechanism, or poor JWT handling.
**Example Anti-Pattern:**
```http
GET /profile?token=abc123  // Insecure!
```
**Solution:**
- Use **HTTP-only cookies** or **Bearer tokens in headers**:
  ```http
  GET /profile
  Authorization: Bearer abc123
  ```
- Implement **refresh tokens** for long-lived sessions.

---
### **12. Non-Idempotent Operations**
**Problem:** Allowing duplicate `DELETE` or `POST` calls (e.g., without `Idempotency-Key`).
**Example Anti-Pattern:**
```http
DELETE /users/123  // Should fail on retry, but may succeed.
```
**Solution:**
- Use **idempotency keys**:
  ```http
  DELETE /users/123?idempotency-key=unique123
  ```
- Log operations to prevent duplicates.

---
### **13. Rate Limiting Abuse**
**Problem:** Unclear or absent rate limits (e.g., `429 Too Many Requests` without docs).
**Example Anti-Pattern:**
```http
// Client gets 500 errors without knowing why.
GET /api/data
```
**Solution:**
- Set **clear rate limits** (e.g., `429` with `Retry-After` header).
- Document limits in API specs.

---
### **14. Hidden Dependencies**
**Problem:** API returns raw SQL or system-specific data (e.g., database internal IDs).
**Example Anti-Pattern:**
```json
{
  "user": {
    "id": 123,       // Might refer to DB auto-increment.
    "role": "admin"  // Not exposed to clients.
  }
}
```
**Solution:**
- Expose **only business-logic fields**.
- Use **mapping layers** to abstract backend details.

---
### **15. No API Documentation**
**Problem:** Missing or outdated docs (e.g., Swagger/OpenAPI not updated).
**Example Anti-Pattern:**
```http
// Client stuck with unclear API usage.
GET /unclear-endpoint?param=value
```
**Solution:**
- Automate docs with **OpenAPI/Swagger**.
- Use **versioned endpoints** (`/v1/docs`).

---

## **Query Examples: Anti-Pattern vs. Solution**

| **Anti-Pattern**                          | **Solution**                                      | **Best Practice**                          |
|--------------------------------------------|----------------------------------------------------|--------------------------------------------|
| `GET /users?action=delete`                 | `DELETE /users/123`                                | Use correct HTTP methods.                  |
| `/users/123/orders/456/products/789`       | `/users/123/orders?product_id=789`                 | Flatten relationships.                     |
| Multiple calls: `GET /users`, `GET /orders` | `/users/123?include=orders`                       | Aggregate data.                            |
| `/v2/users?version=1.0`                    | `/v2/users` (with header `X-API-Version: 2`)       | Standardize versioning.                    |
| `GET /payments?refund=true`                | `POST /payments/123/refund`                       | Use POST for side effects.                  |
| Full user object (unnecessary fields)      | `GET /users?fields=name,email`                     | Enable field selection.                    |
| Missing metadata (e.g., `created_at`)      | Include timestamps in responses.                   | Standardize metadata.                      |
| `/users?internalId=abc123`                 | `/users?status=active`                            | Avoid backend-specific params.              |
| No CORS headers                             | Add `Access-Control-Allow-Origin: *`               | Enable cross-origin requests.              |
| Inconsistent error codes (e.g., `419`)      | Use standard `400`/`500` with structured payloads. | Follow HTTP standards.                     |
| Tokens in URLs (`/login?token=abc`)         | Use `Authorization: Bearer token` in headers.       | Secure authentication.                     |
| Non-idempotent `DELETE`                    | Add `Idempotency-Key` header.                      | Ensure reproducibility.                     |
| Unclear rate limits                         | Return `429` with `Retry-After` header.            | Document limits proactively.               |
| Raw SQL data in responses                   | Map to business objects.                           | Abstract backend details.                  |
| No API documentation                        | Generate OpenAPI specs.                            | Automate docs with tools.                  |

---

## **Related Patterns**
To counter anti-patterns, adopt these **best practices**:
1. **[RESTful API Design](https://restfulapi.net/)** – Follow HTTP standards for clarity.
2. **[HATEOAS](https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm)** – Link resources dynamically for discoverability.
3. **[GraphQL](https://graphql.org/)** – Reduce over/under-fetching with flexible queries.
4. **[OpenAPI/Swagger](https://swagger.io/)** – Document APIs automatically.
5. **[Idempotency Keys](https://www.practicallynetworked.com/tech/what-is-idempotency/)** – Ensure safe retries.
6. **[JWT Best Practices](https://auth0.com/blog/critical-jwt-security-best-practices/)** – Secure authentication.
7. **[Field-Level Permissions](https://www.okta.com/identity-101/rbac/)** – Avoid exposing sensitive data.
8. **[API Versioning Strategies](https://blog.postman.com/api-versioning-best-practices/)** – Manage breaking changes.

---
## **Mitigation Checklist**
To audit your API for anti-patterns:
✅ **HTTP Methods:** Verify `GET`/`POST`/`PUT`/`DELETE` usage.
✅ **Nesting:** Avoid URLs deeper than 3 levels.
✅ **Aggregation:** Combine related data (e.g., `?include=...`).
✅ **Versioning:** Use clear endpoints/headers (not query params).
✅ **Field Selection:** Support partial responses.
✅ **CORS:** Enable headers for frontend access.
✅ **Errors:** Standardize `HTTP 4xx/5xx` responses.
✅ **Auth:** Use tokens in headers, not URLs.
✅ **Idempotency:** Add `Idempotency-Key` for critical ops.
✅ **Rate Limits:** Document and enforce limits.
✅ **Docs:** Auto-generate OpenAPI specs.

---
**Final Note:** Anti-patterns often stem from hasty development or tight coupling to backend systems. Prioritize **declarative designs**, **standard compliance**, and **client-first thinking** to build resilient APIs. Always validate changes with tools like Postman, Swagger, or automated tests.