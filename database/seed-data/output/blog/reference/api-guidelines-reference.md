# **[Pattern] API Guidelines Reference Guide**
*Standards for designing, documenting, and maintaining scalable, maintainable RESTful APIs*

---

## **Overview**
This guide outlines best practices for designing RESTful APIs to ensure consistency, scalability, and usability. By adhering to these guidelines, developers can create APIs that are intuitive for consumers (clients, integrations, and SDks) and maintainable for the team. Key principles include:
- **Consistency** (uniform structure, naming conventions).
- **Predictability** (clear error handling, versioning).
- **Performance** (efficient resource usage, caching).
- **Security** (authentication, rate limiting, data protection).

Following these guidelines reduces friction in API development, testing, and adoption.

---

## **1. Key Concepts & Best Practices**

### **1.1 RESTful Principles**
| Principle               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Resource-Oriented**   | APIs should expose resources (e.g., `/users`, `/orders`).                     |
| **Stateless**           | Each request should contain all needed data (no server-side session storage). |
| **Uniform Interface**   | Standardized methods (GET, POST, PUT, DELETE) and response formats.         |
| **Client-Server**       | Separation of UI (client) and business logic (server).                      |
| **Layered System**      | APIs may use intermediaries (e.g., load balancers, proxies).                 |
| **Cachable**            | Responses should include caching headers where appropriate.                  |

---

### **1.2 Request & Response Standards**

| Standard               | Rule                                                                 |
|------------------------|------------------------------------------------------------------------|
| **Base URL**           | Always include a version in the base URL (e.g., `https://api.example.com/v1`). |
| **Content-Type**       | Default to `application/json`.                                         |
| **Response Codes**     | Use standard HTTP status codes (e.g., `200 OK`, `404 Not Found`).       |
| **Pagination**         | Use `?page=1&limit=10` or `next/prev` links in responses.              |
| **Error Responses**    | Return structured JSON with `status`, `error`, and `message` fields.    |
| **Rate Limiting**      | Implement `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers.     |

---

### **1.3 Resource Naming & Structure**
| Convention             | Example                                                                 |
|------------------------|--------------------------------------------------------------------------|
| **Plural Nouns**       | `/users` (not `/user`).                                                  |
| **Hyphenated Terms**   | `/user-profiles`.                                                       |
| **No Action Words**    | Avoid `/get-user`; use `/users/{id}`.                                     |
| **Hierarchy**          | `/orders/{orderId}/items` (nested resources).                            |
| **Underscores**        | Avoid in paths (use hyphens or camelCase in query params).                |

---

### **1.4 Authentication & Security**
| Requirement            | Implementation                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Token-Based Auth**   | Use JWT (Bearer Token) in `Authorization: Bearer <token>`.                   |
| **API Keys**           | For public APIs, include `X-API-Key` header (obfuscated in docs).           |
| **HTTPS**              | Always enforce HTTPS (`Strict-Transport-Security` header).                    |
| **CORS**               | Allow origins via `Access-Control-Allow-Origin` (whitelist if sensitive).    |
| **Input Validation**   | Reject malformed requests early (e.g., `400 Bad Request`).                   |

---

### **1.5 Performance & Scalability**
| Best Practice          | Implementation                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Compression**        | Enable response compression (`Content-Encoding: gzip`).                        |
| **Caching**            | Use `ETag` or `Last-Modified` for caching.                                   |
| **Lazy Loading**       | Return partial data (e.g., `/users?fields=id,name`) to reduce payload size.    |
| **Webhooks**           | For real-time updates, offer `/subscriptions` endpoints.                      |

---

## **2. Schema Reference**
Below is a standard response schema for API success/error cases.

### **2.1 Success Response Schema**
```json
{
  "status": "success",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "meta": {
    "count": 1,
    "page": 1,
    "total_pages": 1
  }
}
```

### **2.2 Error Response Schema**
```json
{
  "status": "error",
  "code": 400,
  "error": "bad_request",
  "message": "Email is invalid",
  "details": {
    "field": "email",
    "reason": "must be a valid email"
  }
}
```

---

## **3. Query Examples**
### **3.1 Create a User**
**Method:** `POST`
**Endpoint:** `/users`
**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "secure123"
}
```
**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": "789e4567-e89b-12d3-a456-426614174001",
    "name": "Jane Smith"
  }
}
```

---

### **3.2 Retrieve a User with Pagination**
**Method:** `GET`
**Endpoint:** `/users?page=2&limit=5`
**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    { "id": "1", "name": "User 6" },
    { "id": "2", "name": "User 7" },
    { "id": "3", "name": "User 8" },
    { "id": "4", "name": "User 9" },
    { "id": "5", "name": "User 10" }
  ],
  "meta": {
    "count": 5,
    "page": 2,
    "total_pages": 3
  }
}
```

---

### **3.3 Update a User**
**Method:** `PUT`
**Endpoint:** `/users/123e4567-e89b-12d3-a456-426614174000`
**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Jane Updated",
  "email": "jane.updated@example.com"
}
```
**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Jane Updated"
  }
}
```

---

### **3.4 Handle an Error (Invalid Email)**
**Method:** `POST`
**Endpoint:** `/users`
**Body:**
```json
{
  "name": "Invalid User",
  "email": "not-an-email"
}
```
**Response (400 Bad Request):**
```json
{
  "status": "error",
  "code": 400,
  "error": "bad_request",
  "message": "Email is invalid",
  "details": {
    "field": "email",
    "reason": "must be a valid email"
  }
}
```

---

## **4. Related Patterns**
For further refinement of your API design, consider these complementary patterns:

| Pattern               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **[Versioning]**      | How to manage breaking changes (e.g., URL, header, or query param versioning). |
| **[OpenAPI/Swagger]** | Automated API documentation using OpenAPI specs.                           |
| **[GraphQL]**         | Alternative to REST for flexible, typed queries.                            |
| **[OAuth 2.0]**       | Standardized framework for delegated authorization.                         |
| **[gRPC]**            | High-performance RPC for internal services.                                  |

---
**Note:** For versioning, prefer **URL-based** (e.g., `/v1/users`) over header-based for simplicity in client-side caching. Always document deprecated endpoints and their migration paths.

---
**Last Updated:** `[Insert Date]`
**Feedback:** `[Contact Email/Link]`