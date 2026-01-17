---
# **[REST Standards] Reference Guide**

---

## **Overview**
The **REST (Representational State Transfer)** standard defines a **declarative architectural style** for designing networked applications using **HTTP/HTTPS** as the foundation. This guide outlines standard conventions, best practices, and implementation details for building **stateless, scalable** APIs following REST principles. Key tenets include:
- **Resource-based URIs** (stateless requests)
- **Standard HTTP methods** (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`)
- **HTTP status codes** for responses
- **JSON/XML** for request/response bodies
- **Pagination, filtering, sorting** for data retrieval
- **Idempotency** and caching strategies

This guide ensures **consistency, predictability, and interoperability** across APIs.

---

## **Schema Reference**

| **Convention**               | **Description**                                                                                      | **Example**                                                                                     |
|------------------------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Base URI**                 | Root endpoint of the API. Must be unique, meaningful, and versioned.                               | `https://api.example.com/v1/`                                                                  |
| **Resource Naming**          | Use **plural nouns** for collections, **singular nouns** for individual entities.                   | `/users` (collection), `/users/{id}` (entity)                                                  |
| **HTTP Methods**             | Standard CRUD operations mapped to HTTP verbs.                                                      | `GET /users` (fetch), `POST /users` (create), `PUT /users/{id}` (update), `DELETE /users/{id}` |
| **Request/Response Format** | Prefer **JSON** with `Content-Type: application/json`.                                               | `{ "id": 123, "name": "Alice" }`                                                               |
| **Query Parameters**         | Filter, sort, and paginate data using URL-encoded parameters.                                        | `?name=Alice&sort=-created_at&page=2&limit=10`                                                  |
| **Status Codes**             | Use **standard HTTP status codes** (e.g., `200 OK`, `201 Created`, `404 Not Found`).                | `200 OK` on success, `400 Bad Request` on validation failure.                                   |
| **Authentication**           | Use **JWT, OAuth2, or API keys** in headers (`Authorization: Bearer <token>`).                     | `Authorization: Bearer xyz123`                                                                   |
| **Versioning**               | Include **version in URI** (`/v1/resource`) or headers (`X-API-Version: 1`).                        | `/v1/users` (URI) or `Accept: application/vnd.example.v1+json` (header).                       |
| **Content Negotiation**      | Support **multiple formats** (JSON, XML) via headers (`Accept: application/json`).                   | `Accept: application/xml`                                                                       |
| **Rate Limiting**            | Implement **headers** (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).                              | `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 95`                                           |
| **Error Responses**          | Return **structured error JSON** with `status`, `code`, and `message`.                             | `{ "status": 400, "code": "INVALID_INPUT", "message": "Name required" }`                          |
| **Caching Headers**          | Use `ETag`, `Cache-Control`, or `Last-Modified` for caching.                                     | `Cache-Control: max-age=3600`                                                                   |
| **Idempotency Keys**         | For non-idempotent operations (e.g., `POST`), include an `Idempotency-Key` header.                | `Idempotency-Key: abc123`                                                                       |

---

## **Query Examples**

### **1. Basic Resource Retrieval**
**Request:**
`GET /v1/users`

**Response (Success - 200 OK):**
```json
{
  "data": [
    { "id": 1, "name": "Alice", "email": "alice@example.com" },
    { "id": 2, "name": "Bob", "email": "bob@example.com" }
  ],
  "meta": {
    "count": 2,
    "total": 100,
    "page": 1,
    "limit": 10
  }
}
```

---
### **2. Filtering & Sorting**
**Request:**
`GET /v1/users?name=Alice&sort=-created_at`

**Response (Filtered & Sorted - 200 OK):**
```json
{
  "data": [
    { "id": 1, "name": "Alice", "email": "alice@example.com" }
  ],
  "meta": { "count": 1 }
}
```

---
### **3. Paginated Results**
**Request:**
`GET /v1/users?page=2&limit=5`

**Response (Paginated - 200 OK):**
```json
{
  "data": [
    { "id": 6, "name": "Charlie" },
    { "id": 7, "name": "Dana" }
  ],
  "meta": {
    "count": 2,
    "total": 100,
    "page": 2,
    "limit": 5,
    "next": "/v1/users?page=3&limit=5",
    "prev": "/v1/users?page=1&limit=5"
  }
}
```

---
### **4. Creating a Resource**
**Request:**
`POST /v1/users`
**Headers:**
`Content-Type: application/json`
**Body:**
```json
{ "name": "Charlie", "email": "charlie@example.com" }
```

**Response (Success - 201 Created):**
```json
{
  "id": 3,
  "name": "Charlie",
  "email": "charlie@example.com",
  "created_at": "2023-10-01T12:00:00Z"
}
```

---
### **5. Updating a Resource**
**Request:**
`PUT /v1/users/3`
**Headers:**
`Content-Type: application/json`
**Body:**
```json
{ "name": "Charlie Updated", "email": "newemail@example.com" }
```

**Response (Success - 200 OK):**
```json
{
  "id": 3,
  "name": "Charlie Updated",
  "email": "newemail@example.com",
  "updated_at": "2023-10-01T13:00:00Z"
}
```

---
### **6. Deleting a Resource**
**Request:**
`DELETE /v1/users/3`

**Response (Success - 204 No Content):**
*(Empty body, no response body)*

---
### **7. Error Response**
**Request:**
`GET /v1/users/invalid_id`

**Response (Error - 404 Not Found):**
```json
{
  "status": 404,
  "code": "RESOURCE_NOT_FOUND",
  "message": "User with ID 'invalid_id' not found",
  "details": {
    "param": "id",
    "value": "invalid_id"
  }
}
```

---
### **8. Rate Limit Exceeded**
**Request:**
`POST /v1/users` *(after exceeding limit)*

**Response (Error - 429 Too Many Requests):**
```json
{
  "status": 429,
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Try again later.",
  "retry_after": 60
}
```

---
### **9. Conditional Requests (ETag)**
**Request:**
`PATCH /v1/users/1`
**Headers:**
`If-Match: "abc123"`

**Response (Success - 200 OK):**
*(Only updates if ETag matches)*

---
### **10. Content Negotiation (JSON → XML)**
**Request:**
`GET /v1/users`
**Headers:**
`Accept: application/xml`

**Response (XML - 200 OK):**
```xml
<users>
  <user>
    <id>1</id>
    <name>Alice</name>
    <email>alice@example.com</email>
  </user>
</users>
```

---

## **Implementation Best Practices**

### **1. URI Design**
- **Avoid actions in URIs** → ❌ `/users/activate/{id}`
  **Use HTTP methods instead** → ✅ `POST /users/{id}/activate`
- **Use hyphens for compound words** → `/user-profile`
- **Keep URIs short and intuitive** → `/products/{id}/reviews` (not `/productItemReviewDetails`)

### **2. HTTP Methods**
| **Method** | **Use Case**                          | **Idempotent?** | **Example**                          |
|------------|---------------------------------------|-----------------|--------------------------------------|
| `GET`      | Retrieve data                        | ✅ Yes          | `/users`                             |
| `POST`     | Create resource                      | ❌ No           | `/users` (with body)                 |
| `PUT`      | Replace entire resource               | ✅ Yes          | `/users/1` (full update)             |
| `PATCH`    | Partial update                       | ❌ No           | `/users/1` (partial body)            |
| `DELETE`   | Remove resource                      | ✅ Yes          | `/users/1`                           |
| `HEAD`     | Retrieve headers only                 | ✅ Yes          | `/users/1`                           |

### **3. Status Codes**
| **Code** | **Name**               | **Use Case**                                                                 |
|----------|------------------------|-----------------------------------------------------------------------------|
| `200 OK` | Success                | Default for successful requests.                                            |
| `201 Created` | Resource created      | After `POST`/`PUT` with location header (`Location: /users/3`).           |
| `204 No Content` | Success (no body)   | After `DELETE` or successful `PATCH` with no response.                      |
| `400 Bad Request` | Client error      | Invalid input (e.g., missing required field).                              |
| `401 Unauthorized` | Auth required   | Missing/invalid auth credentials.                                           |
| `403 Forbidden`   | No permission         | User lacks permissions (e.g., `DELETE /users/1` without admin rights).       |
| `404 Not Found`   | Resource missing       | Requested resource doesn’t exist.                                            |
| `405 Method Not Allowed` | Invalid HTTP method | `GET` on a `POST`-only endpoint.                                             |
| `409 Conflict`    | Idempotency conflict | `PUT` on a resource that changed since last `GET`.                          |
| `429 Too Many Requests` | Rate limit exceeded | Exceeded request quota.                                                      |
| `500 Internal Server Error` | Server failure | Unexpected backend error.                                                   |

### **4. Versioning**
- **URI Versioning (Recommended):**
  `/v1/users`, `/v2/users`
- **Header Versioning:**
  `Accept: application/vnd.example.v1+json`
- **Query Parameter Versioning:**
  `/users?version=1`

### **5. Pagination**
| **Parameter** | **Description**                          | **Example**                |
|---------------|------------------------------------------|----------------------------|
| `page`        | Current page number (1-based)           | `?page=2`                  |
| `limit`       | Items per page                          | `?limit=10`                |
| `offset`      | Alternative to `page` (0-based index)    | `?offset=10`               |
| `sort`        | Field to sort by (`+` for asc, `-` for desc) | `?sort=-created_at` |
| `filter`      | Filter criteria (e.g., `name=Alice`)    | `?filter[name]=Alice`      |

**Response Meta:**
```json
"meta": {
  "count": 10,    // Items in current page
  "total": 100,   // Total items
  "page": 2,      // Current page
  "limit": 10,    // Items per page
  "next": "/v1/users?page=3&limit=10",  // Pagination links
  "prev": "/v1/users?page=1&limit=10"
}
```

### **6. Error Handling**
- **Standardize error JSON:**
  ```json
  {
    "status": 400,
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": {
      "field": "email",
      "expected": "string",
      "received": null
    }
  }
  ```
- **Log errors** for debugging (avoid exposing details in production).
- **Return `422 Unprocessable Entity`** for semantic validation errors (e.g., "Age must be > 18").

### **7. Security**
- **Use HTTPS** for all endpoints.
- **Implement CORS** if frontend is separate (`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`).
- **Validate all inputs** (sanitize against XSS, SQL injection).
- **Use CSRF tokens** for state-changing methods (`POST`, `PUT`, `DELETE`).

### **8. Performance**
- **Enable compression** (`gzip`, `deflate`) for responses.
- **Cache responses** with `Cache-Control` headers:
  ```http
  Cache-Control: public, max-age=3600
  ```
- **Use `ETag`/`Last-Modified`** for conditional requests.
- **Implement rate limiting** to prevent abuse.

### **9. Testing**
- **Unit tests** for route handlers and controllers.
- **Integration tests** for API endpoints (using tools like **Postman**, **Supertest**, or **Pytest**).
- **Load testing** to ensure scalability (e.g., **Locust**, **JMeter**).
- **Postman/Newman** for API documentation and testing.

### **10. Documentation**
- **OpenAPI/Swagger** for interactive API docs:
  ```yaml
  paths:
    /users:
      get:
        summary: List users
        parameters:
          - name: name
            in: query
            schema:
              type: string
        responses:
          200:
            description: OK
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    data:
                      type: array
                      items:
                        $ref: '#/components/schemas/User'
  ```
- **Generate docs** using `swagger-ui` or `Redoc`.
- **Include examples** in the docs for common use cases.

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[GraphQL]**             | Query language for APIs (flexible, single endpoint).                          | When clients need **ad-hoc data fetching** or **complex filtering**.          |
| **[Webhooks]**            | Server-to-server notifications (event-driven).                               | For **real-time updates** (e.g., payment confirmations, status changes).      |
| **[HATEOAS]**             | Hypermedia controls (links in responses for navigation).                     | When designing **decoupled APIs** with dynamic discovery.                    |
| **[SOAP]**                | XML-based standard (strict, formal).                                         | Legacy systems or **enterprise integrations** requiring WS-* standards.       |
| **[gRPC]**                | Binary protocol (high performance, internal services).                       | **Microservices** or **low-latency** requirements (e.g., game servers).       |
| **[Event Sourcing]**      | Store state changes as immutable events.                                     | **Audit trails**, **time-travel debugging**, or **complex domain logic**.      |
| **[CQRS]**                | Separate read/write models (optimized for performance).                      | **High-throughput** systems (e.g., e-commerce checkouts).                    |
| **[OAuth 2.0 / OpenID Connect]** | Authentication/authorization framework.   | Secure **third-party access** (e.g., social login, API keys).                 |
| **[JWT (JSON Web Tokens)]** | Stateless authentication (signed tokens).                          | **Stateless APIs** (e.g., mobile/web apps).                                     |
| **[API Gateways]**        | Single entry point for routing, security, and analytics.                     | **Multi-service APIs**, **A/B testing**, or **global traffic management**.     |
| **[Service Mesh (Istio/Linkerd)]** | Networking layer for microservices (traffic control, observability). | **Complex microservice architectures** needing **resilience & security**.    |

---

## **Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| **Express.js**            | Node.js framework for building REST APIs.                                  |
| **FastAPI**               | Python framework (auto-Generator OpenAPI docs, async support).              |
| **Django REST Framework** | Python ORM for building REST APIs with Django.                             |
| **Spring Boot (Java)**    | Java framework with REST annotations (`@RestController`).                   |
| **Fluentd/Nginx**         | API gateways, rate limiting, load balancing.                               |
| **Postman/Newman**        | API testing, documentation, and automation.                                |
| **Swagger UI/OpenAPI**    | Interactive API documentation.                                              |
| **Redis**                 | Caching, rate limiting, session storage.                                    |
| **Kafka/RabbitMQ**        | Event-driven architectures (webhooks, async processing).                   |
| **Prometheus/Grafana**    | Monitoring API performance and errors.                                     |
| **Sentry**                | Error tracking and logging.                                                |

---

## **Common Pitfalls & Anti-Patterns**
| **Anti-Pattern**          | **Problem**                                                                 | **Solution**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Overuse of `GET` for side effects** | `GET` should be **safe and idempotent** (e.g., don’t use `GET` to delete). | Use `POST`/`DELETE` for state-changing operations.                          |
| **Long URIs**             | Poor readability and increased latency