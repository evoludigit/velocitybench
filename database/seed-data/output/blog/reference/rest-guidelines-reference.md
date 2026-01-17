**[REST API Design Guidelines] Reference Guide**

---
### **Overview**
The **REST (Representational State Transfer) API Design Guidelines** define best practices for creating scalable, maintainable, and efficient RESTful web services. This guide outlines key principles, resource modeling, HTTP method usage, versioning, authentication, error handling, and data formatting to ensure consistency, performance, and developer experience.

REST APIs should adhere to the **statelessness**, **client-server architecture**, **uniform interface**, and **resource-based** principles. This guide provides concrete rules for implementation while allowing flexibility for domain-specific needs.

---

### **Core Concepts & Schema Reference**

| **Category**               | **Rule**                                                                                                                                                                                                 | **Notes**                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Resources & URIs**        | Use **nouns** (not verbs) for resource identifiers (e.g., `/users`, `/orders`). Avoid action words (e.g., `/deleteUser`).                                                                               | URIs should be hierarchical (`/v1/customers/{id}/orders`).                |
| **HTTP Methods**           |                                                                                                                                                                                                             |                                                                           |
|                            | **GET** – Retrieve a resource or list. Must be **safe** and **idempotent**.                                                                                                                                  | Use `?filter`, `?limit`, and `?page` for pagination.                     |
|                            | **POST** – Create a new resource. Client provides data in the request body.                                                                                                                                   | Return the created resource with `201 Created` and `Location` header.     |
|                            | **PUT** – **Idempotently** fully replace a resource. Requires full resource data in the body.                                                                                                             | Use `204 No Content` if no response is needed.                           |
|                            | **PATCH** – Partially update a resource. Use `application/merge-patch+json` or `application/json-patch+json`.                                                                                              | Avoid `PUT`-style updates for partial changes.                            |
|                            | **DELETE** – Remove a resource. Must be **idempotent** and **safe for clients**.                                                                                                                              | Return `204 No Content` for success.                                     |
| **HTTP Status Codes**      | Return **standard status codes** (e.g., `200 OK`, `201 Created`, `404 Not Found`, `500 Internal Server Error`).                                                                                               | Document **custom codes** (e.g., `429 Too Many Requests`) in API specs.   |
| **Versioning**             | Include version in **URI** (`/v1/users`) or **header** (`Accept: application/vnd.company.v1+json`). Avoid versioning in query parameters.                                                                      | Plan for backward compatibility when updating.                           |
| **Authentication**         | Use **OAuth 2.0** or **JWT** for stateless auth. Include token in `Authorization: Bearer <token>`. Avoid basic auth in production.                                                                      | Document token expiration and refresh mechanisms.                        |
| **Data Format**            | Use **JSON** (default) or **XML** for responses. Define a **schema** (e.g., OpenAPI/Swagger).                                                                                                                     | Example: `Content-Type: application/vnd.company.users.v1+json`.          |
| **Pagination**             | Support `/users?limit=10&offset=0` or **cursor-based** pagination (`?cursor=<value>`).                                                                                                                   | Return `total_items` and `total_pages` in response metadata.               |
| **Error Handling**         | Return **structured errors** with `error` object in JSON: `{ "error": { "code": "400", "message": "Invalid input" } }`.                                                                                   | Use `4xx` for client errors, `5xx` for server errors.                     |
| **Content Negotiation**    | Support `Accept` headers (e.g., `Accept: application/json;q=1.0, text/html;q=0.9`) to return preferred format.                                                                                                 | Default to JSON unless specified otherwise.                              |
| **HATEOAS (Optional)**     | Include **links** in responses for navigation (e.g., `"_links": { "next": "/users?page=2" }`).                                                                                                               | Improves discoverability but adds complexity.                            |
| **Rate Limiting**          | Implement `X-Ratelimit-Limit` and `X-Ratelimit-Remaining` headers. Allow granular limits (e.g., per IP or API key).                                                                                            | Document rate limits in the API docs.                                    |
| **Caching**                | Use `Cache-Control` headers (`max-age`, `no-store`). Cache **GET** responses unless data is sensitive.                                                                                                       | Avoid caching for **idempotent** but **side-effecting** operations.     |
| **Idempotency**            | Ensure **POST/PUT/DELETE** are idempotent where possible. Use `Idempotency-Key` header for idempotent requests.                                                                                                 | Reduces duplicate operations.                                           |

---

### **Query Examples**

#### **1. Retrieve a User**
```http
GET /v1/users/123
Headers:
  Accept: application/vnd.company.users.v1+json
Response (200 OK):
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2023-01-01T00:00:00Z"
}
```

#### **2. Create an Order (POST)**
```http
POST /v1/orders
Headers:
  Content-Type: application/json
  Authorization: Bearer abc123
Body:
{
  "userId": 123,
  "items": [
    { "productId": 456, "quantity": 2 }
  ]
}
Response (201 Created):
{
  "orderId": "ord_789",
  "status": "pending",
  "createdAt": "2023-01-02T12:00:00Z"
}
Headers:
  Location: /v1/orders/ord_789
```

#### **3. Update a User (PATCH)**
```http
PATCH /v1/users/123
Headers:
  Content-Type: application/merge-patch+json
  Authorization: Bearer abc123
Body:
{
  "email": "john.doe@newdomain.com"
}
Response (200 OK):
{
  "id": 123,
  "email": "john.doe@newdomain.com"
}
```

#### **4. Delete a User**
```http
DELETE /v1/users/123
Headers:
  Authorization: Bearer abc123
Response (204 No Content)
```

#### **5. Paginated Query**
```http
GET /v1/orders?limit=5&offset=0
Headers:
  Accept: application/vnd.company.orders.v1+json
Response (200 OK):
{
  "orders": [
    { "id": "ord_1", "status": "completed" },
    { "id": "ord_2", "status": "pending" }
  ],
  "meta": {
    "limit": 5,
    "offset": 0,
    "total": 100
  }
}
```

#### **6. Filtered Query**
```http
GET /v1/products?status=active&category=electronics
Headers:
  Accept: application/json
Response (200 OK):
{
  "products": [
    { "id": 7, "name": "Laptop", "status": "active" }
  ]
}
```

#### **7. Error Response**
```http
POST /v1/users
Headers:
  Content-Type: application/json
Body:
{
  "email": "invalid-email"
}
Response (400 Bad Request):
{
  "error": {
    "code": "400",
    "message": "Invalid email format",
    "details": ["Email must contain @"]
  }
}
```

---

### **Related Patterns & Best Practices**

| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Resource Fields (REST)** | Model resources as nouns (e.g., `/users` instead of `/getUser`).                                                                                                                                             | Designing core API endpoints.                                                  |
| **Hypermedia as the Engine of Application State (HATEOAS)** | Include links in responses to guide clients (e.g., `"_links": { "order": "/orders/123" }`).                                                                                                                | APIs with dynamic workflows (e.g., checkout processes).                       |
| **OpenAPI/Swagger**       | Define contracts for APIs using OpenAPI 3.0.                                                                                                                                                               | Documenting and validating API specs.                                          |
| **GraphQL Over REST**     | Use GraphQL for flexible querying when clients need dynamic data shaping.                                                                                                                                   | Complex, nested queries with varying needs.                                   |
| **API Gateway**           | Route and manage requests through a gateway for security, monitoring, and rate limiting.                                                                                                                       | Multi-service architectures or microservices.                                 |
| **Event-Driven APIs**     | Use webhooks or async messages (e.g., Kafka, RabbitMQ) for real-time updates.                                                                                                                                 | Notifications (e.g., order status changes) or high-throughput systems.         |
| **CORS (Cross-Origin Resource Sharing)** | Configure `Access-Control-Allow-Origin` headers to enable cross-domain requests.                                                                                                                            | Frontend-backend separation (e.g., React + Node.js).                          |
| **Idempotency Keys**      | Use `Idempotency-Key` header to ensure duplicate requests are handled safely.                                                                                                                                   | Financial transactions or high-concurrency scenarios.                         |
| **API Versioning Strategies** | Version via **URI** (`/v1/users`), **headers** (`Accept: v=1`), or **query params** (`?v=1`). Avoid breaking changes unless necessary.                                                                             | Maintaining backward compatibility.                                           |
| **Security Headers**      | Add `X-Content-Type-Options`, `X-Frame-Options`, and `Strict-Transport-Security` for protection.                                                                                                              | Production APIs exposed to the internet.                                      |
| **Field-Level Permissions** | Use **JWT claims** or **RBAC (Role-Based Access Control)** to restrict access to specific fields (e.g., hide `ssn` for non-admin users).                                                                       | APIs with granular data sensitivity.                                          |

---
### **Anti-Patterns to Avoid**

1. **Using GET for Side Effects**
   - ❌ `GET /users?action=delete` (modifies data).
   - ✅ Use `DELETE /users/123` instead.

2. **Overusing POST**
   - ❌ `POST /users` for updates (use `PUT` or `PATCH`).
   - ✅ `POST` only for creating resources.

3. **Buried Resources**
   - ❌ `/resources/byId/user/123/data` (nested URIs).
   - ✅ `/users/123/data`.

4. **No Pagination**
   - ❌ Returning 1000 items in one response.
   - ✅ Always paginate with `limit`/`offset` or cursors.

5. **Ignoring Caching**
   - ❌ No `Cache-Control` headers.
   - ✅ Cache immutable responses (e.g., `ETag` or `Last-Modified`).

6. **Tight Coupling to Database**
   - ❌ Exposing DB columns directly (e.g., `/users?fields=password_hash`).
   - ✅ Expose only business-relevant fields.

7. **No Rate Limiting**
   - ❌ API vulnerable to DDoS.
   - ✅ Implement `X-Ratelimit-*` headers.

---
### **Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Swagger/OpenAPI**       | Define and document APIs interactively.                                                                                                                                                                 |
| **Postman/Newman**        | Test and mock APIs.                                                                                                                                                                                            |
| **Apache Kafka/RabbitMQ** | Enable event-driven communication.                                                                                                                                                                       |
| **Spring Boot (Java)**    | Framework with REST support (Spring Data REST, Spring WebFlux).                                                                                                                                       |
| **FastAPI (Python)**      | Modern async framework for REST/GraphQL.                                                                                                                                                                  |
| **Express.js (Node.js)**  | Lightweight Node.js framework for REST APIs.                                                                                                                                                              |
| **AWS API Gateway**       | Managed service for REST/HTTP APIs with auth, caching, and monitoring.                                                                                                                                      |
| **Django REST Framework** | Python framework for building RESTful APIs.                                                                                                                                                               |
| **GraphQL (Apollo/Hasura)** | Query language for flexible data fetching.                                                                                                                                                              |
| **JWT Libraries**         | `jsonwebtoken` (Node.js), `pyjwt` (Python) for auth tokens.                                                                                                                                               |

---
### **Further Reading**
1. **Fielding’s Dissertation** – [REST and HATEOAS](https://www.ics.uci.edu/~fielding/pubs/dissertation/fielding_dissertation.html)
2. **REST API Design Rulebook** – [REST API Design Rulebook (GitHub)](https://github.com/rtfeldman/secure-rest-java)
3. **OpenAPI Specification** – [spec.openapis.org](https://spec.openapis.org/)
4. **OAuth 2.0 RFC** – [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
5. **JSON Schema** – [json-schema.org](https://json-schema.org/)

---
**Last Updated:** [Insert Date]
**Version:** 1.3