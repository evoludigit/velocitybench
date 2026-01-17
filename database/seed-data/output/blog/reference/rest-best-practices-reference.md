---
# **[Pattern] RESTful API Best Practices Reference Guide**

---

## **Overview**
REST (Representational State Transfer) is a stateless, client-server architectural style for designing scalable web services. This guide outlines key REST best practices to ensure **consistency, performance, and maintainability** in API development. Follow these conventions to build standards-compliant APIs that are easy to adopt, debug, and extend.

---

## **Key Concepts & Implementation Details**

### **1. Use HTTP Methods Correctly**
| **Method** | **Purpose**                          | **Example Use Case**                     |
|------------|--------------------------------------|------------------------------------------|
| `GET`      | Retrieve data                        | `/users` (list), `/users/123` (single)  |
| `POST`     | Create new resource                  | `/users` (create user)                  |
| `PUT`      | Replace entire resource              | `/users/123` (fully update user data)   |
| `PATCH`    | Partially update a resource          | `/users/123` (update only `name`)       |
| `DELETE`   | Remove a resource                    | `/users/123` (delete user)              |
| `HEAD`     | Retrieve headers only (optimized)    | `/users/123` (fetch metadata)           |
| `OPTIONS`  | Describe allowed methods/headers      | `/users` (CORS preflight, capabilities) |

**Best Practice:**
- Use `POST` for **idempotent** operations (no side effects).
- Use `PATCH` for **partial updates** (avoid overwriting unrelated fields).
- Avoid `GET` for actions that modify data (violates REST principles).

---

### **2. Resource Naming & URIs**
- **Use lowercase, plural nouns** for collections.
  ✅ `/users`, `/orders`
  ❌ `/user`, `/Order`
- **Separate hierarchy with slashes** (`/`).
  ✅ `/orders/{id}/items`
  ❌ `/order_id_items`
- **Avoid query parameters for IDs** (use path variables).
  ✅ `/users/5`
  ❌ `/users?id=5`

**Best Practice:**
- Keep URIs **hierarchical** but not overly nested.
- Use **slugs or alphanumeric IDs** (not auto-incremented IDs).

---

### **3. HTTP Status Codes**
| **Code** | **Meaning**                          | **Example Use Case**                     |
|----------|--------------------------------------|------------------------------------------|
| `200 OK` | Success (GET)                        | `/users/123` (user exists)              |
| `201 Created` | Success (POST/PUT/PATCH) | `/users` (new resource created)       |
| `204 No Content` | Success (no response body) | `/users/123` (deleted, no confirmation) |
| `400 Bad Request` | Invalid input            | Missing required `name` field           |
| `401 Unauthorized` | Auth required               | Missing/expired token                    |
| `403 Forbidden`  | Auth OK but no permission    | `/admin` (user lacks role)              |
| `404 Not Found`  | Resource doesn’t exist         | `/users/999` (user ID invalid)          |
| `500 Internal Error` | Server-side failure      | Database timeout                         |

**Best Practice:**
- Return **422 Unprocessable Entity** for validation errors (instead of `400`).

---

### **4. Headers & Content Negotiation**
| **Header**          | **Purpose**                          | **Example**                          |
|---------------------|--------------------------------------|--------------------------------------|
| `Content-Type`      | Specify request/response format     | `application/json`                   |
| `Accept`            | Client’s preferred format           | `Accept: application/vnd.api+json`   |
| `Authorization`     | Auth token                          | `Bearer <token>`                     |
| `Cache-Control`     | Caching directives                  | `max-age=3600`                       |
| `ETag`              | Optimistic concurrency control       | `"abc123"`                           |

**Best Practice:**
- Support **multiple formats** (e.g., `application/json`, `application/xml`).
- Use **`ETag` or `Last-Modified`** for caching.

---

### **5. Versioning**
| **Method**          | **Pros**                              | **Cons**                              | **Example**                          |
|---------------------|--------------------------------------|--------------------------------------|--------------------------------------|
| **URL Versioning**  | Simple for clients                   | Breaks forward compatibility         | `/v1/users`                          |
| **Header Versioning** | No URI changes                     | Adds complexity                       | `Accept: application/v2+json`        |
| **Media-Type Versioning** | Cleanest (RFC 6648) | Requires client support        | `Accept: application/vnd.company.v1+json` |

**Best Practice:**
- **Prefer header/media-type versioning** for long-term support.
- Avoid versioning via query parameters (`?v=2`).

---

### **6. Pagination**
Use **`Range` or `Limit/Offset` headers** (or query params).

**Example (Query Params):**
```
GET /users?limit=10&offset=20
```
**Example (Headers - RFC 5985):**
```
Accept-Ranges: items 0-1000
Range: items=20-29
```

**Best Practice:**
- Default to **10–50 items per page** (avoid excessive data).
- Return `X-Total-Count` header for total results.

---

### **7. Error Handling**
**Structured Error Responses:**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Name is required",
    "details": ["Name cannot be empty"]
  }
}
```

**Best Practice:**
- **Standardize error shapes** (e.g., `error.code`, `error.message`).
- Include **developer-friendly details** in staging but sanitize in production.

---

### **8. Security**
| **Best Practice**               | **Implementation**                          |
|----------------------------------|--------------------------------------------|
| **Use HTTPS**                    | Enforce TLS 1.2+                            |
| **Rate Limiting**                | `429 Too Many Requests` with `Retry-After` |
| **Input Validation**             | Sanitize all inputs (e.g., SQL injection)   |
| **CORS Policies**                | Restrict `Allow-Origin` headers            |
| **JWT Best Practices**           | Short-lived tokens, refresh tokens        |

**Example Rate Limiting:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 10
```

---

### **9. API Documentation**
- **Use OpenAPI/Swagger** for interactive docs.
- **Version docs separately** (e.g., `/docs/v1`).
- **Include examples** for common use cases.

**Example OpenAPI Snippet:**
```yaml
paths:
  /users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        '201':
          description: User created
          headers:
            Location:
              schema:
                type: string
                format: uri
```

---

## **Schema Reference**
| **Field**          | **Type**       | **Description**                          | **Example**                     |
|--------------------|----------------|------------------------------------------|---------------------------------|
| `id`               | `string/uuid`  | Unique identifier                        | `"u123e4567-e89b-12d3-a456-426614174000"` |
| `name`             | `string`       | Full name (required)                     | `"John Doe"`                    |
| `email`            | `string`       | Valid email (validation)                 | `"john@example.com"`            |
| `createdAt`        | `datetime`     | ISO 8601 timestamp                       | `"2023-10-01T12:00:00Z"`        |
| `isActive`         | `boolean`      | User status                              | `true`                          |
| `metadata`         | `object`       | Arbitrary key-value pairs                 | `{"profile": "admin", "flags": {}}` |

**Best Practice:**
- Use **snake_case** for JSON keys (e.g., `user_id`).
- **Avoid nested objects** for deep hierarchies (flatten when possible).

---

## **Query Examples**
### **1. Create a User (POST)**
```http
POST /users HTTP/1.1
Content-Type: application/json

{
  "name": "Alice",
  "email": "alice@example.com"
}
```
**Response (201 Created):**
```http
HTTP/1.1 201 Created
Location: /users/abc123
```

---

### **2. Get a User (GET)**
```http
GET /users/abc123 HTTP/1.1
Accept: application/vnd.user.detail+json
```
**Response (200 OK):**
```json
{
  "id": "abc123",
  "name": "Alice",
  "email": "alice@example.com",
  "createdAt": "2023-10-01T12:00:00Z"
}
```

---

### **3. Update User (PATCH)**
```http
PATCH /users/abc123 HTTP/1.1
Content-Type: application/json
If-Match: "abc123"  # Optional: optimistic concurrency

{
  "name": "Alice Smith"
}
```
**Response (200 OK):**
```json
{
  "id": "abc123",
  "name": "Alice Smith",
  "email": "alice@example.com"
}
```

---

### **4. Delete User (DELETE)**
```http
DELETE /users/abc123 HTTP/1.1
```
**Response (204 No Content):**
*(Empty body)*

---

### **5. Search Users (GET with Query Params)**
```http
GET /users?email=alice@example.com&active=true HTTP/1.1
```
**Response (200 OK):**
```json
[
  {
    "id": "abc123",
    "name": "Alice Smith",
    "email": "alice@example.com"
  }
]
```

---

### **6. Paginated List (GET)**
```http
GET /users?limit=5&offset=10 HTTP/1.1
```
**Response (200 OK):**
```json
{
  "data": [
    { "id": "def456", "name": "Bob" },
    { "id": "ghi789", "name": "Charlie" }
  ],
  "metadata": {
    "total": 50,
    "limit": 5,
    "offset": 10
  }
}
```

---

## **Related Patterns**
1. **[HATEOAS](https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm#sec_5_4_1)**
   - Dynamically include links in responses (e.g., `/users/{id}/orders`).
   - *Tools:* Use `Link` headers or embed `rels` in JSON.

2. **[GraphQL Over REST](https://graphql.org/learn/)**
   - Alternative for flexible querying (but adds complexity).
   - *When to use:* When clients need fine-grained data control.

3. **[OAuth 2.0 for REST APIs](https://oauth.net/2/)**
   - Standard for authentication/authorization.
   - *Best Practice:* Use **token scopes** (`roles`, `permissions`).

4. **[API Gateway Patterns](https://www.apigee.com/connections/api-gateway)**
   - Route, rate-limit, and secure APIs behind a single entry point.
   - *Tools:* Kong, AWS API Gateway, NGINX.

5. **[Event-Driven REST (Server-Sent Events)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)**
   - Push updates via SSE or WebSockets for real-time data.

6. **[Performance Optimization](https://www.michaelsync.net/2017/04/03/rest-api-performance-best-practices/)**
   - **Caching:** `Cache-Control`, CDNs.
   - **Compression:** `gzip`/`Brotili` for responses.
   - **Lazy Loading:** Filter `?fields=id,name` to avoid over-fetching.

---

## **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Why It’s Bad**                          | **Solution**                          |
|---------------------------------|------------------------------------------|---------------------------------------|
| **Long URIs** (`/products/123/reviews/456/comments`) | Hard to maintain, breaks REST principles | Use nested resources (`/products/{id}/reviews/{id}/comments`). |
| **Non-Idempotent POST**         | Duplicate submissions cause side effects  | Use `PUT` for idempotent updates.     |
| **SOAP-like WSDL**              | Heavy, not REST-native                  | Stick to JSON/XML (lightweight).     |
| **Hiding Errors**               | Debugging becomes impossible              | Return consistent error formats.      |
| **No Versioning**               | Breaks backward compatibility            | Version APIs explicitly.              |

---

## **Tools & Libraries**
| **Category**          | **Tools**                          | **Purpose**                          |
|-----------------------|------------------------------------|--------------------------------------|
| **Validation**        | Zod, JSON Schema, Pydantic         | Schema enforcement                   |
| **Documentation**     | Swagger UI, Redoc, Stoplight       | Auto-generated docs from OpenAPI     |
| **Testing**           | Postman, Newman, pytest           | API contract testing                 |
| **Monitoring**        | Prometheus, Datadog, New Relic     | Track latency, errors, rate limits   |
| **Security**          | OWASP ZAP, Burp Suite              | Scan for vulnerabilities             |
| **Framework**         | FastAPI, Express, Spring Boot      | REST implementation                  |

---
**End of Guide** (Word count: ~950)