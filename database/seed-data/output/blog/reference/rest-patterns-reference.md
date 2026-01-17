# **[REST API Design Patterns] Reference Guide**

---
## **Overview**
REST (Representational State Transfer) is a lightweight architectural style for designing networked applications. This guide outlines **common REST API design patterns** to ensure consistency, scalability, and maintainability. These patterns cover resource representation, request handling, error responses, and security best practices.

Key principles include:
- **Statelessness**: Each request must contain all necessary information.
- **Resource-based**: APIs expose resources (nouns) as endpoints.
- **Uniform Interface**: Standardized methods (HTTP verbs) for resource manipulation.
- **HATEOAS (Optional)**: Dynamic discovery of API capabilities via hyperlinks.

This guide focuses on **practical patterns** rather than theoretical REST constraints, leveraging modern best practices (e.g., OpenAPI/Swagger, JSON:API).

---

## **1. Core REST Patterns**

| **Pattern**               | **Description**                                                                                                                                                                                                 | **Use Case Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Resource Naming**       | Endpoints follow resource naming conventions (nouns in plural, hyphens for compound words). Avoid actions (e.g., `/user` instead of `/getUser`).                                                           | `/products`, `/orders/{id}`                                                                              |
| **HTTP Methods**          | Use standard HTTP verbs: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.                                                                                                                                         | `POST /cart` (add item), `DELETE /cart/123` (remove item)                                              |
| **Idempotency**           | Design endpoints to be idempotent where possible (e.g., `PUT`, `DELETE`).                                                                                                                                      | `PUT /users/456` (update user) should not change data on retries.                                       |
| **Versioning**            | Include API version in the URL (`/v1/users`) or `Accept`/`Content-Type` headers. Avoid backward-incompatible changes.                                                                                         | `/v2/orders` (new version), `Accept: application/vnd.api.v2+json`                                     |
| **Pagination**            | Use query params (`?page=2&limit=10`) or cursor-based pagination for large datasets.                                                                                                                       | `/posts?page=3&per_page=20`                                                                             |
| **Filtering/Sorting**     | Support query params for filtering (`?category=books`) and sorting (`?sort=-price`).                                                                                                                      | `/products?category=electronics&sort=-price`                                                           |
| **Field Selection**       | Allow clients to request specific fields (`?fields=id,name`) instead of full responses.                                                                                                                   | `/users?fields=id,email` (avoids sending unnecessary data).                                           |
| **Error Handling**        | Standardize error responses (HTTP status codes + JSON payloads).                                                                                                                                           | `404 { "error": "Resource not found" }`, `500 { "status": "error", "code": 1001 }`                     |
| **Authentication**        | Use `Bearer` tokens (JWT) or API keys in headers (`Authorization: Bearer <token>`).                                                                                                                      | `GET /profile`, `Authorization: Bearer xy...`                                                           |
| **Caching**               | Leverage `ETag`, `Last-Modified`, or `Cache-Control` headers for caching responses.                                                                                                                       | `Cache-Control: max-age=3600` (1-hour cache), `ETag: "xyz123"`                                         |
| **Rate Limiting**         | Implement `X-RateLimit-*` headers to prevent abuse.                                                                                                                                                           | `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 95`                                                 |
| **Webhooks**              | Notify clients of async events via HTTP callbacks (e.g., order updates).                                                                                                                                      | `POST /webhooks/orders` (server sends update to registered URLs).                                       |

---

## **2. Schema Reference**

### **Request/Response Structure**
| **Component**      | **Description**                                                                                                                                                                                                 | **Example**                                                                                             |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Headers**        | Standard metadata (e.g., `Content-Type: application/json`, `Authorization`).                                                                                                                              | `Content-Type: application/vnd.api+json`                                                                 |
| **Query Params**   | Filtering, sorting, pagination.                                                                                                                                                                               | `?search=query&sort=-created_at&page=2&per_page=10`                                                      |
| **Body**           | JSON payload for `POST/PUT/PATCH` (e.g., `application/json`).                                                                                                                                                 | `{"name": "Laptop", "price": 999.99}`                                                                  |
| **Response Body**  | JSON structure with data, pagination metadata, or errors.                                                                                                                                                     | `{ "data": { "id": 1, "name": "Laptop" }, "links": { "self": "/products/1" } }`                      |
| **Pagination Meta** | Fields like `total`, `page`, `limit`, `next_page`.                                                                                                                                                       | `{ "pagination": { "total": 100, "page": 2, "limit": 10, "next": "/products?page=3" } }`            |

### **Error Response Schema**
| **Field**   | **Type**   | **Description**                                                                                                                                                       | **Example**                          |
|-------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `status`    | String     | Human-readable error message (e.g., "Validation failed").                                                                                                     | `"Validation failed: 'price' must be > 0."` |
| `code`      | Integer    | Machine-readable error code (e.g., `40001` for validation errors).                                                                                            | `"code": 40001`                       |
| `errors`    | Array      | Detailed field-level errors (for `422 Unprocessable Entity`).                                                                                               | `{ "errors": [ { "field": "price", "message": "Must be positive." } ] }` |
| `details`   | Object     | Additional context (e.g., `request_id` for debugging).                                                                                                         | `"details": { "request_id": "abc123" }` |

---

## **3. Query Examples**

### **Basic CRUD Operations**
```http
# GET (List resources)
GET /products?category=books&sort=-price

# POST (Create)
POST /products
Content-Type: application/json

{
  "name": "REST API Design",
  "price": 29.99,
  "description": "A guide to REST patterns."
}

# GET (Retrieve single resource)
GET /products/123

# PUT (Replace entirely)
PUT /products/123
Content-Type: application/json

{
  "name": "REST API Design (Updated)",
  "price": 24.99
}

# PATCH (Partial update)
PATCH /products/123
Content-Type: application/json

{
  "price": 24.99
}

# DELETE
DELETE /products/123
```

### **Pagination Example**
```http
GET /orders?page=2&per_page=10
```

**Response:**
```json
{
  "data": [
    { "id": 11, "user_id": 5, "amount": 50.00 },
    { "id": 12, "user_id": 5, "amount": 30.00 }
  ],
  "pagination": {
    "total": 25,
    "page": 2,
    "limit": 10,
    "next": "/orders?page=3&per_page=10"
  }
}
```

### **Filtering/Sorting**
```http
# Filter by status + sort by date
GET /orders?status=completed&sort=-created_at

# Field selection
GET /users?fields=id,name,email
```

**Response:**
```json
{
  "data": [
    { "id": 1, "name": "Alice", "email": "alice@example.com" },
    { "id": 2, "name": "Bob", "email": "bob@example.com" }
  ]
}
```

### **Error Handling**
```http
# Invalid request (400 Bad Request)
POST /orders
Content-Type: application/json

{
  "amount": -50  // Negative value
}
```

**Response:**
```json
{
  "status": "Validation failed: 'amount' must be positive.",
  "code": 40001,
  "errors": [
    { "field": "amount", "message": "Must be positive." }
  ]
}
```

---

## **4. Related Patterns**

| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                          |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **GraphQL**               | Query language for APIs (request only needed fields).                                                                                                                                                     | When clients need flexible, nested data retrieval.                                                      |
| **HATEOAS**               | Dynamic API discovery via hypermedia links in responses.                                                                                                                                                     | For highly interactive or evolving APIs.                                                                |
| **Event-Driven (Webhooks)** | Async notifications for state changes (e.g., order updates).                                                                                                                                                 | When real-time updates are required (e.g., notifications, status changes).                             |
| **OpenAPI/Swagger**       | Standard for API documentation (auto-generates client code).                                                                                                                                                 | For public APIs or collaborative development.                                                            |
| **OAuth 2.0**             | Standard for authorization (delegated access).                                                                                                                                                             | When third-party integrations or user authentication are needed.                                       |
| **gRPC**                  | High-performance RPC framework (binary protocol).                                                                                                                                                         | For internal services or low-latency requirements.                                                      |
| **Serverless APIs**       | Event-driven APIs (e.g., AWS Lambda, Firebase Functions).                                                                                                                                                | For scalable, cost-effective backendless integrations.                                                   |
| **API Gateways**          | Single entry point for routing, auth, and monitoring (e.g., Kong, AWS API Gateway).                                                                                                                     | For complex architectures or microservices.                                                            |
| **Query Parameters vs. Path** | Use query params for optional/searchable fields; paths for required IDs.                                                                                                                               | `/users` (list) vs. `/users/123` (retrieve)                                                             |
| **Idempotency Keys**      | Prevent duplicate `POST/PUT` requests by using unique keys (e.g., `Idempotency-Key: abc123`).                                                                                                           | For financial transactions (e.g., payments).                                                        |

---

## **5. Best Practices**
1. **Consistency**: Stick to one pattern (e.g., always use `POST` for creates).
2. **Versioning**: Avoid breaking changes; use semantic versioning (`/v2/endpoint`).
3. **Security**:
   - Use HTTPS.
   - Sanitize inputs to prevent injection attacks.
   - Validate all requests.
4. **Documentation**: Use OpenAPI/Swagger for auto-generated docs.
5. **Rate Limiting**: Protect against abuse with `X-RateLimit-*` headers.
6. **Caching**: Leverage `ETag`/`Last-Modified` for static data.
7. **Performance**: Avoid `SELECT *`; use field selection (`?fields=id,name`).

---
**References**:
- [REST API Design Rules](https://restfulapi.net/)
- [JSON:API Specification](https://jsonapi.org/)
- [OpenAPI Specification](https://swagger.io/specification/)

---
**Last Updated**: [Insert Date]
**Version**: 1.2