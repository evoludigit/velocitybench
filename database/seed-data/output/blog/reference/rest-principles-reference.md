# **[Pattern] REST API Design Principles Reference Guide**

---

## **Overview**
This guide provides best-practice principles for designing RESTful APIs that are scalable, maintainable, and intuitive. REST (Representational State Transfer) APIs should prioritize **statelessness**, **uniform interfaces**, and **resource-oriented architecture**. Poorly designed APIs lead to inefficiencies, high latency, or miscommunication between clients and servers. This document outlines foundational principles, common structuring patterns, and implementation best practices to ensure your API adheres to RESTful standards while optimizing performance and developer experience.

---

## **Core Principles & Best Practices**

| **Principle**               | **Description**                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | **Key Considerations**                                                                                                                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Statelessness**           | Each request from a client must contain all necessary context. No server-side session storage should influence responses.                                                                                                                                                                                                                                                                                                                                                     | Use tokens (JWT/OAuth) for authentication, not cookies/sessions. Avoid client-side state in URLs.                                                                                     |
| **Resource-Oriented Design**| Represent data as resources (nouns, e.g., `/users`, `/orders`). Operations are performed via HTTP methods (`GET`, `POST`, `PUT`, `DELETE`).                                                                                                                                                                                                                                                                                         | Avoid verbs in URLs (e.g., `/deleteUser`). Use plural nouns.                                                                                                                       |
| **Uniform Interface**       | Ensure all resources expose consistent structure through:
- **Identification of resources** (URLs)
- **Resource manipulation via representations** (JSON/XML)
- **Self-descriptive messages** (standardized responses)
- **Hypermedia controls** (e.g., `Link` headers for navigation)
                                                                                                                                                                                                                                                                 | Use RESTful conventions; avoid non-standard extensions (e.g., custom HTTP methods).                                                                                               |
| **Scalability**             | APIs should handle increased traffic without performance degradation. Use:
- **Pagination** (e.g., `?limit=10&offset=20`)
- **Caching** (HTTP caching headers, CDNs)
- **Idempotency** (ensuring repeated identical requests produce the same result)                                                                                                                                                                                                 | Avoid queries that return large datasets without pagination. Use `ETag`/`Last-Modified` for caching.                                                                                     |
| **Idempotency**             | Safe methods (`GET`, `HEAD`, `OPTIONS`, `TRACE`) and PUT/DELETE should be idempotent. POST should not be idempotent (unless explicitly designed as such).                                                                                                                                                                                                                                                                                      | Document idempotency guarantees in API specs (e.g., OpenAPI).                                                                                                                           |
| **Stateless Validation**    | Validate input data on the client *and* server. Use schemas (e.g., JSON Schema, OpenAPI) for consistency.                                                                                                                                                                                                                                                                                                                                                     | Return clear error messages for invalid requests (e.g., `400 Bad Request`).                                                                                                       |
| **Versioning**              | Explicitly version APIs using:
- URL paths (e.g., `/v1/users`)
- Headers (e.g., `Accept: application/vnd.api.v1+json`)
- Media types (e.g., `application/json; version=1`)                                                                                                                                                                                                                                                                                                       | Avoid breaking changes. Use backward-compatible updates.                                                                                                                              |
| **Rate Limiting**           | Protect APIs from abuse by implementing:
- Token bucket or sliding window algorithms.
- Response headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).                                                                                                                                                                                                                                                                                                                                                          | Document limits in API specs. Use 429 `Too Many Requests` for exceeded limits.                                                                                                    |
| **Security**                | Secure APIs using:
- **Authentication**: OAuth 2.0, JWT.
- **Authorization**: Role-based access control (RBAC).
- **HTTPS**: Enforce TLS 1.2+.
- **Input Sanitization**: Prevent SQL injection/XSS.                                                                                                                                                                                                                                                                                                                                   | Never expose sensitive data in URLs/errors. Use `403 Forbidden` instead of `401 Unauthorized` for permission issues.                                                                 |
| **Error Handling**          | Return consistent error responses:
- HTTP status codes (e.g., `500 Internal Server Error`).
- Detailed error payloads (e.g., `{"error": "invalid_token", "code": 401}`).                                                                                                                                                                                                                                                                                                                           | Avoid generic errors. Use machine-readable formats (e.g., JSON).                                                                                                                 |
| **Documentation**           | Provide clear, up-to-date docs using:
- OpenAPI/Swagger specs.
- Interactive docs (e.g., Swagger UI).
- Examples for common use cases.                                                                                                                                                                                                                                                                                                                                               | Include rate limits, authentication flows, and versioning details.                                                                                                                |
| **Performance Optimization**| Reduce latency by:
- Compressing responses (`gzip`, `deflate`).
- Using efficient serialization (e.g., Protocol Buffers for high-throughput APIs).
- Minimizing payload sizes (avoid excessive nesting).                                                                                                                                                                                                                                                                                               | Benchmark APIs with tools like `k6` or `Locust`.                                                                                                                                       |
| **Deprecation Policy**      | Plan for API deprecation with:
- Clear deprecation notices (headers/response fields).
- Deprecation timeframes (e.g., 6–12 months notice).                                                                                                                                                                                                                                                                                                                                                   | Avoid abrupt deprecations. Provide migration guides.                                                                                                                                |

---

## **Resource Structuring Patterns**

### **1. Nested Resources**
Use slashes (`/`) to denote hierarchical relationships:
```
GET /users/{id}/orders       → List orders for a user
POST /users/{id}/orders      → Add an order to a user
```
- **Best Practice**: Limit nesting depth to 3–4 levels to avoid complexity.

### **2. Collection vs. Item**
- **Collections**: Represent groups of resources (plural nouns).
  `GET /users` → List all users.
- **Items**: Represent single resources (singular nouns).
  `GET /users/{id}` → Fetch a single user.

### **3. Filtering & Sorting**
Use query parameters:
```
GET /products?category=electronics&sort=price:asc
```
- **Best Practice**: Document supported filters/sorts in API specs.

### **4. Pagination**
Use `limit` and `offset` or `cursor`-based pagination:
```
GET /posts?limit=10&offset=20    (Offset-style)
GET /posts?cursor=abc123          (Cursor-style, preferred for large datasets)
```
- **Best Practice**: Include `total_pages` or `total_count` in responses.

### **5. Partial Updates**
Use `PATCH` for partial updates (avoid overwriting unrelated fields):
```
PATCH /users/123
{
  "name": "Updated Name"
}
```
- **Best Practice**: Specify supported fields in the API docs.

### **6. Webhooks**
Expose events via HTTP callbacks:
```
POST /webhooks/subscribe
{
  "url": "https://client.example.com/events",
  "events": ["order_created"]
}
```
- **Best Practice**: Use signed payloads to validate webhook deliveries.

---

## **Query Examples**

### **1. Creating a Resource**
**Request**:
```http
POST /users
Content-Type: application/json

{
  "name": "Alice",
  "email": "alice@example.com"
}
```
**Response (201 Created)**:
```json
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com",
  "links": {
    "self": "/users/123"
  }
}
```

---

### **2. Retrieving a Resource**
**Request**:
```http
GET /users/123
Accept: application/json
```
**Response (200 OK)**:
```json
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2023-01-01T00:00:00Z"
}
```

---

### **3. Updating a Resource**
**Request**:
```http
PUT /users/123
Content-Type: application/json

{
  "name": "Alice Updated",
  "email": "alice@example.com"
}
```
**Response (200 OK)**:
```json
{
  "id": "123",
  "name": "Alice Updated",
  "email": "alice@example.com"
}
```

---

### **4. Deleting a Resource**
**Request**:
```http
DELETE /users/123
```
**Response (204 No Content)**:
*(Empty body)*

---

### **5. Querying with Filters & Pagination**
**Request**:
```http
GET /products?category=books&price_min=10&price_max=50&limit=10&offset=0
```
**Response (200 OK)**:
```json
{
  "data": [
    { "id": "1", "name": "Book 1", "price": 15 },
    { "id": "2", "name": "Book 2", "price": 20 }
  ],
  "pagination": {
    "total_items": 42,
    "limit": 10,
    "offset": 0,
    "total_pages": 5
  }
}
```

---

### **6. Handling Errors**
**Request**:
```http
POST /users
Content-Type: application/json

{
  "email": "invalid-email"  // Missing required field
}
```
**Response (400 Bad Request)**:
```json
{
  "error": {
    "code": "missing_field",
    "message": "Name is required",
    "details": {
      "missing": ["name"]
    }
  }
}
```

---

### **7. Webhook Subscription**
**Request**:
```http
POST /webhooks/subscribe
Content-Type: application/json

{
  "url": "https://client.example.com/webhook",
  "events": ["order_created", "payment_processed"],
  "secret": "abc123xyz"  // For verification
}
```
**Response (201 Created)**:
```json
{
  "id": "webhook_456",
  "url": "https://client.example.com/webhook",
  "events": ["order_created", "payment_processed"],
  "status": "active"
}
```

---

## **Schema Reference**

| **Component**          | **Example**                                                                 | **Description**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **URL Paths**          | `/users/{id}/orders`                                                      | Resource hierarchy (e.g., `/users/123/orders`).                                                                                                                                                            |
| **Query Parameters**   | `?category=electronics&sort=price:desc`                                    | Filtering, sorting, pagination (e.g., `?limit=10&offset=5`).                                                                                                                                        |
| **Headers**            | `Authorization: Bearer token123`                                            | Authentication (e.g., `Content-Type: application/json`).                                                                                                                                              |
| **Request Body**       | `{"name": "Alice", "email": "alice@example.com"}`                           | Payload for `POST`/`PUT`/`PATCH` requests.                                                                                                                                                              |
| **Response Body**      | `{"id": "123", "name": "Alice"}`                                           | Serialized resource data (JSON/XML).                                                                                                                                                                 |
| **Status Codes**       | `200 OK`, `201 Created`, `400 Bad Request`, `500 Internal Server Error`     | HTTP status codes for standard responses.                                                                                                                                                             |
| **Links**              | `"links": {"self": "/users/123"}`                                         | Hypermedia controls for resource navigation (HATEOAS).                                                                                                                                                 |
| **Pagination**         | `"pagination": {"total": 100, "limit": 10, "offset": 0}`                   | Metadata for large datasets (e.g., `total_pages`, `next_cursor`).                                                                                                                                        |
| **Errors**             | `{"error": "invalid_token", "code": 401}`                                 | Structured error responses with `code` and `message`.                                                                                                                                                     |
| **Webhooks**           | `{"url": "https://client.example.com/webhook", "events": ["order_created"]}` | Subscription endpoints for async events.                                                                                                                                                                |

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                                                                                                                                                                                                                                                                 | **When to Use**                                                                                                                                                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[GraphQL API Design]**         | Query language for APIs (flexible client-side data fetching).                                                                                                                                                                                                                                                                                                                                                     | When clients need fine-grained control over response payloads or have varying data requirements.                                                                                                           |
| **[gRPC]**                       | High-performance RPC framework (binary protocol).                                                                                                                                                                                                                                                                                                                                                     | For internal services requiring low-latency communication (e.g., microservices).                                                                                                                              |
| **[OAuth 2.0 / OpenID Connect]** | Standard for secure authorization/delegated access.                                                                                                                                                                                                                                                                                                                                                      | When APIs require third-party authentication (e.g., social logins).                                                                                                                                          |
| **[Event-Driven Architecture]**  | Asynchronous communication via events (e.g., Kafka, RabbitMQ).                                                                                                                                                                                                                                                                                                                                              | For decoupled systems where real-time updates are needed (e.g., order processing).                                                                                                                            |
| **[API Gateways]**               | Single entry point for routing, auth, and rate limiting.                                                                                                                                                                                                                                                                                                                                                    | To consolidate multiple backend services into a unified API endpoint.                                                                                                                                  |
| **[HATEOAS]**                    | Self-descriptive links in responses to guide client navigation.                                                                                                                                                                                                                                                                                                                                         | For APIs where clients should discover actions dynamically (e.g., RESTful services with evolving endpoints).                                                                                                     |
| **[OpenAPI/Swagger]**            | Standard for API documentation and validation.                                                                                                                                                                                                                                                                                                                                                     | For generating interactive docs, client SDKs, or automated testing.                                                                                                                                           |
| **[CORS (Cross-Origin Resource Sharing)]** | Mechanism for controlling cross-origin requests.                                                                                                                                                                                                                                                                                                                                                  | When APIs serve multiple domains (e.g., frontend deployed separately from backend).                                                                                                                         |
| **[Retry Policies]**             | Strategies for handling transient failures (e.g., exponential backoff).                                                                                                                                                                                                                                                                                                                                     | For resilient clients interacting with potentially unreliable APIs.                                                                                                                                             |
| **[API Versioning]**             | Techniques to manage API evolution (e.g., path, header, query parameters).                                                                                                                                                                                                                                                                                                                                  | When APIs undergo breaking changes and backward compatibility is critical.                                                                                                                                |

---

## **Key Takeaways**
1. **Design for Scalability**: Use pagination, caching, and statelessness.
2. **Prioritize Clarity**: Structure URLs intuitively; document everything.
3. **Security First**: Enforce HTTPS, validate inputs, and limit exposure.
4. **Optimize Performance**: Compress responses, minimize payloads, and leverage CDNs.
5. **Plan for Evolution**: Version APIs, deprecate gracefully, and provide migration paths.
6. **Leverage Standards**: Follow REST conventions (HTTP methods, status codes) for consistency.