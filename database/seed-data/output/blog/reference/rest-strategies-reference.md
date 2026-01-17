# **[Pattern] REST Strategies Reference Guide**

---

## **Overview**
The **REST (Representational State Transfer) Strategies** pattern defines best practices for designing scalable, maintainable, and efficient RESTful APIs. REST is a stateless, client-server architectural style that leverages HTTP methods, URIs, and standard response formats (typically JSON/XML). This guide outlines key REST strategies, including **resource design, HTTP method usage, caching, authentication, rate limiting, and versioning**, ensuring APIs adhere to REST principles while addressing real-world constraints.

REST APIs should prioritize **statelessness**, **uniform interface**, **resource identification**, and **resource manipulation via representations**. However, pragmatic considerations (e.g., session management, performance optimization) often necessitate deviations from strict REST purity. This guide balances theoretical ideals with practical implementations.

---

## **Key Concepts & Implementation Details**

### **1. Resource Design**
REST APIs organize data as **resources**, identified by URIs (e.g., `/users`, `/orders/{id}`). Proper resource design improves discoverability and maintainability.

| Concept               | Implementation Details                                                                 |
|-----------------------|----------------------------------------------------------------------------------------|
| **Noun-based URIs**   | Use plural nouns to denote collections (e.g., `/products` instead of `/product`).      |
| **Hierarchical URIs** | Nest resources logically (e.g., `/users/{userId}/orders`). Avoid overly deep hierarchies. |
| **Sub-resource URIs** | Embed child resources (e.g., `/users/{id}/addresses`).                                  |
| **Avoid Actions**     | Replace `/users/search` with `/users?q=...` or `/search/users`.                         |

**Example:**
✅ Good: `/api/v1/users/123/orders`
❌ Bad: `/api/v1/getUserOrders?id=123`

---

### **2. HTTP Methods**
Standard HTTP methods define **CRUD operations** (Create, Read, Update, Delete) with semantic meaning.

| Method | Use Case                          | Example URI               | Notes                                  |
|--------|-----------------------------------|---------------------------|----------------------------------------|
| `GET`  | Retrieve a resource               | `/users/123`              | Should be **idempotent**; cacheable.    |
| `POST` | Create a resource                 | `/users`                  | Client provides data in request body.  |
| `PUT`  | Replace a resource **completely** | `/users/123`              | Idempotent; client must include full data. |
| `PATCH`| Partial update                    | `/users/123` (JSON Patch) | Non-idempotent; specify changes only.  |
| `DELETE`| Remove a resource                 | `/users/123`              | Idempotent; may require confirmation.  |
| `HEAD` | Retrieve headers only             | `/users/123` (without body) | Useful for caching checks.             |

**Best Practice:**
- Use **`POST` for collection creation** (e.g., `/orders`), **`PUT`/`PATCH` for updates**.
- Avoid `GET` for side-effect operations (e.g., password resets).

---

### **3. Status Codes**
Return appropriate HTTP status codes to signal success/failure.

| Code   | Description                                      | Use Case                                  |
|--------|--------------------------------------------------|-------------------------------------------|
| `200 OK`| Success (GET/POST/PUT/PATCH/DELETE)              | Default for successful requests.          |
| `201 Created` | Resource created (POST)                        | Include `Location` header with URI.       |
| `204 No Content` | Success without response body (DELETE)      | Use for operations with no return value. |
| `400 Bad Request` | Client error (invalid input)                   | Validate input; return error details.     |
| `401 Unauthorized` | Authentication failed                        | Require `401` + `WWW-Authenticate` header.|
| `403 Forbidden`   | Authorization failed (valid user, no access)    | Use for permission denial.                |
| `404 Not Found`   | Resource does not exist                         | Distinguish from `403` (e.g., soft deletes). |
| `405 Method Not Allowed` | Unsupported HTTP method          | Return `Allow` header (e.g., `Allow: GET, POST`). |
| `429 Too Many Requests` | Rate limit exceeded                    | Include `Retry-After` header.              |
| `500 Internal Server Error` | Server failure                  | Log errors; return generic message in prod. |

**Example Response:**
```json
{
  "error": "Invalid email format",
  "status": 400,
  "message": "Email must contain '@'."
}
```

---

### **4. Caching Strategies**
Improve performance by leveraging HTTP caching headers.

| Header            | Description                                                                 | Example Use Case                     |
|-------------------|-----------------------------------------------------------------------------|--------------------------------------|
| `Cache-Control`   | Directs caching behavior (e.g., `max-age`, `no-store`).                    | `Cache-Control: max-age=3600` (1 hour) |
| `ETag`            | Entity tag for conditional requests (strong validation).                   | `ETag: "xyz123"`                     |
| `Last-Modified`   | Timestamp for weak validation.                                              | `Last-Modified: Mon, 01 Jan 2023 00:00:00 GMT` |
| `Expires`         | Absolute expiration time (deprecated; prefer `Cache-Control`).              | Rarely used today.                   |
| `Vary`            | Specifies request headers that affect cacheability (e.g., `Accept-Language`). | `Vary: Accept-Language`              |

**Scenario:**
- **`GET /users/123`** → Return `Cache-Control: max-age=300` (5 minutes).
- Client can reuse cached response if unchanged (reduces server load).

---

### **5. Authentication & Authorization**
REST APIs require secure access control. Common strategies:

| Strategy               | Implementation Details                                                                 |
|------------------------|----------------------------------------------------------------------------------------|
| **Basic Auth**         | Base64-encoded `Authorization: Basic <credentials>` (insecure; use only for testing).  |
| **Bearer Tokens**      | JWT/OAuth2 tokens in `Authorization: Bearer <token>`.                                | Store securely; validate expiration. |
| **API Keys**           | Pass in headers (e.g., `X-API-Key: <key>`) or query params (less secure).           | Use for rate limiting.               |
| **OAuth 2.0**          | Authorization code flow, client credentials, etc. (complex but secure).               | Preferred for third-party integrations.|
| **Session Cookies**    | Server-side sessions (violates REST statelessness; use cautiously).                   | Combine with stateless tokens where possible. |

**Example (JWT):**
```http
GET /api/v1/users/123
Host: example.com
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
```

**Best Practice:**
- Use **HTTPS** for all communications.
- Enforce **short-lived tokens** (e.g., 15–30 min) + refresh tokens.

---

### **6. Rate Limiting**
Prevent abuse by limiting requests per client.

| Mechanism               | Implementation Details                                                                 |
|-------------------------|----------------------------------------------------------------------------------------|
| **Fixed Window**        | Allow `N` requests in a time window (e.g., 100 requests/second).                        | Simple but can spike at window edges.  |
| **Sliding Window**      | Track requests over a rolling window (e.g., last 60 seconds).                          | More accurate than fixed window.      |
| **Token Bucket**        | Clients "consume" tokens at a fixed rate (e.g., 1 token/sec).                          | Smooths traffic bursts.               |
| **Response Headers**    | Return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.                     | Example: `X-RateLimit-Limit: 100`      |

**Example Response:**
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
Retry-After: 15
```

**Best Practice:**
- Start with **generous limits** (e.g., 1000 requests/minute) and adjust based on usage.
- Log rate limit events for analytics.

---

### **7. Versioning**
Avoid breaking changes by versioning APIs.

| Strategy               | Implementation Details                                                                 |
|------------------------|----------------------------------------------------------------------------------------|
| **URI Versioning**     | Include version in URI (e.g., `/v1/users`, `/v2/users`).                               | Backward-compatible; easy to migrate. |
| **Header Versioning**  | Send `Accept: application/vnd.company.v2+json`.                                         | Flexible; supports multiple versions. |
| **Query Parameter**    | `?version=2`                                                                          | Less explicit; harder to enforce.       |
| **Deprecation Policy** | Clearly document deprecation timelines (e.g., 6 months notice).                       | Communicate changes proactively.         |

**Example:**
```http
GET /api/v1/users HTTP/1.1
Accept: application/vnd.company.v1+json
```

**Best Practice:**
- **Never remove old versions** abruptly; provide **deprecated headers** (e.g., `Deprecation: "v1 will be removed in 3 months"`).
- Use **semantic versioning** (e.g., `1.0.0`, `1.1.0`).

---

### **8. Error Handling**
Provide **machine-readable** and **human-readable** error details.

| Field            | Description                                                                 | Example                                                                 |
|------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------|
| `error`          | Short error code (e.g., `invalid_email`, `rate_limit_exceeded`).           | `"error": "invalid_email"`                                              |
| `message`        | User-friendly description.                                                  | `"message": "Please provide a valid email address."`                     |
| `status`         | HTTP status code.                                                           | `"status": 400`                                                         |
| `details`        | Technical debugging info (exclude in production).                           | `"details": { "field": "email", "reason": "format" }`                    |
| `requestId`      | Trace ID for logging.                                                        | `"requestId": "abc123"`                                                  |

**Example:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "status": 429,
  "retryAfter": 30,
  "requestId": "xyz789"
}
```

**Best Practice:**
- **Never expose raw stack traces** in production.
- Use **standardized error codes** (e.g., [RFC 7807](https://tools.ietf.org/html/rfc7807)).

---

### **9. Pagination**
Efficiently return large datasets.

| Strategy               | Implementation Details                                                                 |
|------------------------|----------------------------------------------------------------------------------------|
| **Offset/Limit**       | `?limit=10&offset=20` (simple but inefficient for large offsets).                     | Avoid `offset > 1000`.              |
| **Cursor-Based**       | `?cursor=abc123` (scales well; uses a token to fetch next page).                     | Preferred for performance.          |
| **Keyset Pagination**  | `?before=123&after=456` (returns records between two keys).                           | Works well with ordered data (e.g., timestamps). |
| **Headers**            | `Link: <http://api.example.com/page=2?limit=10>; rel="next"`                          | Machine-readable pagination links.  |

**Example (Cursor-Based):**
```http
GET /api/v1/users?cursor=eyJkIjoiMzAwMDAwMDAwMCJ9
```

**Best Practice:**
- **Avoid deep pagination** (e.g., `offset=100000`).
- Provide ** estimators** (e.g., `X-Total-Count: 1000`).

---

### **10. Idempotency & Retries**
Ensure reliability with idempotent operations.

| Operation       | Idempotent? | Notes                                                                 |
|-----------------|-------------|-----------------------------------------------------------------------|
| `GET`           | Yes         | Safe to retry.                                                       |
| `POST`          | No          | May create duplicate resources unless handled (e.g., idempotency keys). |
| `PUT`           | Yes         | Replacing the same resource twice has no effect.                      |
| `DELETE`        | Yes         | Safe to retry if resource still exists.                               |
| `PATCH`         | No          | May apply changes multiple times (unless specified).                 |

**Idempotency Key:**
- Add `Idempotency-Key: <unique-key>` header to `POST` requests.
- Server checks for duplicates; returns `200` or `409 Conflict`.

**Retry Strategy:**
- Exponential backoff for transient errors (e.g., `503 Service Unavailable`).
- Libraries: [Retry](https://github.com/jd/backoff) (Node.js), [ExponentialBackoff](https://docs.spring.io/spring-retry/docs/current/reference/htmlsingle/) (Java).

---

## **Schema Reference**
Below is a reference table for common REST API schemas.

| Field               | Type      | Required | Description                                                                 | Example                          |
|---------------------|-----------|----------|-----------------------------------------------------------------------------|----------------------------------|
| `id`                | string    | Yes      | Unique identifier for the resource.                                        | `"id": "550e8400-e29b-41d4-a716"` |
| `name`              | string    | No       | Human-readable name.                                                       | `"name": "John Doe"`             |
| `email`             | string    | No       | User email (validate format).                                              | `"email": "john@example.com"`     |
| `createdAt`         | datetime  | Yes      | ISO 8601 timestamp of creation.                                            | `"createdAt": "2023-01-01T00:00:00Z"` |
| `updatedAt`         | datetime  | Yes      | Last update timestamp.                                                     | `"updatedAt": "2023-01-02T12:00:00Z"` |
| `status`            | string    | No       | Enumerated value (e.g., `"active"`, `"inactive"`).                        | `"status": "active"`             |
| `metadata`          | object    | No       | Arbitrary key-value pairs (e.g., `{"preferences": {...}}`).                | `"metadata": {...}`              |
| `links`             | object    | No       | HATEOAS links (e.g., `self`, `next`).                                       | `"links": { "self": "/users/123" }` |

**Example Response Body:**
```json
{
  "id": "550e8400-e29b-41d4-a716-466e9965ab50",
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2023-01-01T00:00:00Z",
  "updatedAt": "2023-01-02T12:00:00Z",
  "status": "active",
  "metadata": {
    "preferences": {
      "theme": "dark"
    }
  },
  "links": {
    "self": "/users/550e8400-e29b-41d4-a716-466e9965ab50",
    "orders": "/users/550e8400-e29b-41d4-a716-466e9965ab50/orders"
  }
}
```

---

## **Query Examples**
### **1. Create a User (POST)**
```http
POST /api/v1/users HTTP/1.1
Host: example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
Accept: application/vnd.company.v1+json

{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "secure123"
}
```

**Success Response (201 Created):**
```http
HTTP/1.1 201 Created
Location: /api/v1/users/550e8400-e29b-41d4-a716-466e9965abc1
Cache-Control: max-age=300
```

---

### **2. Retrieve a User (GET)**
```http
GET /api/v1/users/550e8400-e29b-41d4-a716-466e9965abc1 HTTP/1.1
Host: example.com
Accept: application/vnd.company.v1+json
If-None-Match: "xyz123"
```

**Success Response (200 OK):**
```http
HTTP/1.1 200 OK
ETag: "xyz123"
Content-Type: application/vnd.company.v1+json

{
  "id": "550e8400-e29b-41d4-a716-466e9965abc1",
  "name": "Jane Smith",
  "email": "jane@example.com",
  ...
}
```

---

### **3. Update a User (PATCH)**
```http
PATCH /api/v1/users/550e8400-e29b-41d4-a716-466e9965abc1 HTTP/1.1
Host: example.com
Content-Type: application/merge-patch+json
Authorization: Bearer eyJhbGciOiJIUzI1Ni...

{
  "name": "Jane Doe"
}
```

**Success Response (200 OK):**
```http
HTTP/1.1 20