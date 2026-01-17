**[Pattern] REST API Setup Reference Guide**

---

### **Overview**
This guide provides a structured approach to implementing a **RESTful API** following modern best practices. It covers foundational concepts, schema design, authentication/authorization, request/response handling, and integration with common services. Whether you're building a new API or migrating an existing one, this reference ensures clarity, scalability, and maintainability.

---

## **1. Key Concepts**
A **REST API** adheres to principles defined by *Fielding’s REST architectural style*. Core components include:

| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Resource**              | A logical entity (e.g., `/users`, `/products`) that APIs expose. Resources are unique via URIs.                                                                                                               |
| **HTTP Methods**          | Standard actions on resources: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.                                                                                                                                       |
| **Statelessness**         | The server does not retain client session data; all context is passed via requests (e.g., headers, query params, body).                                                                            |
| **HTTP Status Codes**     | Standardized responses (e.g., `200 OK`, `404 Not Found`, `500 Server Error`).                                                                                                                                  |
| **Headers**               | Metadata for requests/responses (e.g., `Content-Type: application/json`, `Authorization: Bearer <token>`).                                                                                                   |
| **Versioning**            | Explicitly include version in the API URI (e.g., `/v1/users`). Avoid backward-compatible breaking changes unless necessary.                                                                                  |
| **Rate Limiting**         | Prevent abuse by enforcing request quotas (e.g., `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 50`).                                                                                                   |
| **HATEOAS**               | Clients discover actions via links in responses (common in dynamic APIs).                                                                                                                                     |
| **Idempotency**           | Ensures repeated identical requests produce the same outcome (e.g., `PUT` is idempotent; `POST` is not).                                                                                                   |
| **Security**              | Use protocols like **HTTPS**, **OAuth 2.0**, or **API keys** to authenticate and authorize requests.                                                                                                              |

---

## **2. Schema Reference**

Below are standardized schemas for common REST API constructs. Use **JSON Schema** (or OpenAPI/Swagger) for validation.

### **2.1 Core Resource Schema**
Represents a standard resource (e.g., `User`, `Order`).

| **Field**            | **Type**      | **Description**                                                                                     | **Example**                          |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `id`                 | `string`      | Unique identifier (UUID or auto-incremented).                                                      | `"e8b8e6c6-b8ab-4f5e-8a52-4a00f7e93d41"` |
| `created_at`         | `datetime`    | Timestamp when resource was created (ISO 8601 format).                                               | `"2023-10-15T14:30:00Z"`            |
| `updated_at`         | `datetime`    | Last-modified timestamp.                                                                          | `"2023-10-15T14:35:00Z"`            |
| `metadata`           | `object`      | Optional key-value pairs for additional attributes.                                                 | `{ "department": "Engineering" }`    |

---

### **2.2 Paginated Responses**
Use for listing resources (e.g., `/users` returns 50 items).

| **Field**            | **Type**      | **Description**                                                                                     | **Example**                          |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `results`            | `array`       | List of resource objects.                                                                          | `[{...}, {...}]`                     |
| `pagination`         | `object`      | Navigation metadata.                                                                               | `{ "page": 1, "per_page": 20, ... }` |
| `pagination.total`   | `integer`     | Total number of items across all pages.                                                             | `100`                                |
| `pagination.links`   | `object`      | Links to next/previous pages.                                                                       | `{ "next": "/v1/users?page=2" }`     |

---

### **2.3 Error Response**
Standardized error format for consistency.

| **Field**            | **Type**      | **Description**                                                                                     | **Example**                          |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `error`              | `string`      | Human-readable error message.                                                                       | `"Invalid credentials"`              |
| `code`               | `string`      | Machine-readable error code (e.g., `auth_invalid_token`).                                           | `"auth_invalid_token"`               |
| `status`             | `integer`     | HTTP status code (e.g., `401`, `404`).                                                              | `401`                                |
| `details`            | `object`      | Additional debugging info (optional).                                                              | `{ "field": "username" }`            |

---

### **2.4 Authentication Headers**
Include in requests to validate access.

| **Header**            | **Type**      | **Description**                                                                                     | **Example**                          |
|-----------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Authorization`       | `string`      | Bearer token for OAuth2.                                                                           | `Bearer xxxxx.yyyyy.zzzzz`           |
| `X-API-Key`           | `string`      | API key for client identification.                                                                  | `sk_live_xyz123`                     |
| `X-Correlation-ID`    | `string`      | Unique ID for logging/tracing.                                                                        | `corr-54e3e8d9-479c-4922-9f16-50445` |

---

## **3. Request/Response Examples**

### **3.1 Create a Resource (POST)**
**Endpoint:** `/v1/users`
**Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "metadata": {
    "role": "admin"
  }
}
```
**Success Response (201 Created):**
```json
{
  "id": "e8b8e6c6-b8ab-4f5e-8a52-4a00f7e93d41",
  "created_at": "2023-10-15T14:30:00Z",
  "updated_at": "2023-10-15T14:30:00Z",
  "email": "user@example.com",
  "metadata": {
    "role": "admin"
  }
}
```
**Error Response (400 Bad Request):**
```json
{
  "error": "Invalid email format",
  "code": "validation_failed",
  "status": 400
}
```

---

### **3.2 Fetch a Resource (GET)**
**Endpoint:** `/v1/users/{id}`
**Headers:** `Accept: application/json`
**Query Param:** `?include=orders` (optional)
**Response:**
```json
{
  "id": "e8b8e6c6-b8ab-4f5e-8a52-4a00f7e93d41",
  "name": "John Doe",
  "orders": [
    { "id": "ord-1", "status": "pending" }
  ]
}
```

---

### **3.3 Update a Resource (PUT/PATCH)**
**Endpoint:** `/v1/users/{id}`
**Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
**PUT Request Body (full update):**
```json
{
  "email": "john.doe@example.com",
  "metadata": {
    "role": "editor"
  }
}
```
**PATCH Request Body (partial update):**
```json
{
  "metadata": {
    "last_login": "2023-10-16T09:00:00Z"
  }
}
```
**Response (200 OK, no body returned).**

---

### **3.4 Delete a Resource**
**Endpoint:** `/v1/users/{id}`
**Headers:** `Authorization: Bearer <token>`
**Response (204 No Content).**
**Error Response (404 Not Found):**
```json
{
  "error": "User not found",
  "code": "resource_not_found",
  "status": 404
}
```

---

### **3.5 Paginated List (GET)**
**Endpoint:** `/v1/users`
**Query Params:**
- `page=2`
- `per_page=10`
- `sort=created_at:desc`
**Response:**
```json
{
  "results": [
    { "id": "u-1", "name": "Alice" },
    { "id": "u-2", "name": "Bob" }
  ],
  "pagination": {
    "page": 2,
    "per_page": 10,
    "total": 100,
    "links": {
      "next": "/v1/users?page=3",
      "prev": "/v1/users?page=1"
    }
  }
}
```

---

## **4. Security Best Practices**
- **Always use HTTPS** to encrypt data in transit.
- **Validate all inputs** to prevent injection attacks (e.g., SQLi, XSS).
- **Implement rate limiting** (e.g., `nginx`, `AWS WAF`) to mitigate abuse.
- **Rotate API keys/secrets** regularly.
- **Avoid exposing sensitive data** in error responses (use generic messages).

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **Use Case**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| **[JWT Authentication]**  | Secure APIs using JSON Web Tokens for stateless auth.                                              | User sessions, internal services.     |
| **[GraphQL Over REST]**   | Query resources via GraphQL instead of REST for flexible schemas.                                   | Complex frontends with dynamic data.   |
| **[CORS Configuration]**  | Enable Cross-Origin Resource Sharing for frontend APIs.                                             | Browser-based apps.                   |
| **[API Gateway]**         | Route requests to microservices with load balancing and auth.                                       | Monolithic → microservices migration. |
| **[Webhooks]**            | Real-time callbacks for events (e.g., `order_created`).                                             | Async notifications.                |
| **[OpenAPI/Swagger]**     | Define API contracts for auto-generated docs/client SDKs.                                           | Collaboration, versioning.            |

---

## **6. Tools & Libraries**
| **Tool/Library**         | **Purpose**                                                                                         | **Example**                          |
|--------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **FastAPI**              | Python framework for REST APIs with OpenAPI support.                                                 | [fastapi.dev](https://fastapi.dev)   |
| **Express.js**           | Node.js middleware for REST endpoints.                                                              | [expressjs.com](https://expressjs.com)|
| **Django REST Framework**| Python ORM for building RESTful APIs.                                                                 | [djangorestframework.org](https://www.drf.com) |
| **Postman/Newman**       | API testing and documentation.                                                                       | [postman.com](https://www.postman.com)|
| **Swagger UI**           | Visualize API docs from OpenAPI specs.                                                               | [swagger.io](https://swagger.io)     |
| **Kong/Apigee**          | API gateways for routing, rate limiting, and monitoring.                                            | [konghq.com](https://konghq.com)    |

---
**Note:** For production, validate schemas using **JSON Schema** or **OpenAPI**. Use tools like **Postman** or **Insomnia** for testing. Always document breaking changes via [Semantic Versioning](https://semver.org/).