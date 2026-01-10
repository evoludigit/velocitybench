---

# **[Pattern] API Standards Reference Guide**

---

## **1. Overview**
API Standards define a consistent framework for designing, documenting, and consuming APIs across an organization or ecosystem. By adhering to standardized practices, developers can reduce complexity, improve maintainability, and ensure compatibility between services. This guide outlines core API standards, including **schema conventions**, **HTTP method usage**, **error handling**, and **authentication/authorization**, while providing actionable examples and best practices. The goal is to ensure APIs are **predictable, scalable, and developer-friendly**.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Principles**
- **Consistency**: Uniform naming, structure, and behavior across all APIs.
- **Modularity**: APIs should be loosely coupled, with clear boundaries between services.
- **Versioning**: APIs must support backward compatibility and versioned endpoints (e.g., `/v1/resource`).
- **Security**: Mandatory authentication, rate limiting, and input validation.
- **Observability**: Comprehensive logging, metrics, and tracing for debugging.

### **2.2 Required Components**
| Component         | Description                                                                 | Example                            |
|-------------------|-----------------------------------------------------------------------------|------------------------------------|
| **Endpoint Naming** | Use **lowercase, kebab-case**, and avoid special characters.                 | `/users/v1/list` (✅) vs `/getUsers` (❌) |
| **HTTP Methods**   | Follow REST conventions (GET, POST, PUT, DELETE, PATCH).                     | GET `/users`, POST `/orders`        |
| **Status Codes**  | Use standard HTTP status codes for responses.                               | 200 OK, 404 Not Found, 500 Server Error |
| **Pagination**     | Support `offset`, `limit`, and `cursor`-based pagination.                   | `?limit=10&offset=50`              |
| **Filters**        | Use query params for filtering (e.g., `?status=active`).                    | `?type=premium&created_after=2023`  |
| **Sorting**        | Allow sorting via `?sort=name:asc`.                                          | `?sort=-created_at` (descending)    |
| **Error Responses**| Structured JSON with `error`, `code`, and `message` fields.                 | `{ "error": "invalid_token", ... }` |
| **Rate Limiting**  | Enforce limits (e.g., 1000 requests/minute) with headers (`X-Rate-Limit-*`).| `X-Rate-Limit-Remaining: 950`       |
| **Authentication** | Support OAuth 2.0, API keys, or JWT.                                        | `Authorization: Bearer <token>`    |

---

## **3. Schema Reference**

### **3.1 Request/Response Schema**
All APIs must adhere to the following ** OpenAPI 3.0** schema structure:

| Field               | Type       | Required | Description                                                                 | Example                                  |
|---------------------|------------|----------|-----------------------------------------------------------------------------|------------------------------------------|
| **`id`**            | `string`   | Yes      | Unique identifier for the resource.                                          | `"abc123"`                               |
| **`name`**          | `string`   | No       | Human-readable name.                                                        | `"John Doe"`                             |
| **`created_at`**    | `string`   | Yes      | ISO 8601 timestamp (UTC).                                                   | `"2023-10-15T14:30:00Z"`                |
| **`updated_at`**    | `string`   | No       | Last modification timestamp (UTC).                                          | `"2023-10-16T09:15:00Z"`                |
| **`metadata`**      | `object`   | No       | Additional key-value pairs (e.g., `{"status": "active"}`).                  | `{ "tags": ["admin", "premium"] }`       |
| **`links`**         | `object`   | No       | Navigation links (self, next, prev).                                        | `{ "self": "/users/abc123" }`           |

### **3.2 Error Schema**
| Field      | Type    | Required | Description                                                                 | Example                     |
|------------|---------|----------|-----------------------------------------------------------------------------|-----------------------------|
| **`error`** | `string`| Yes      | Human-readable error message.                                               | `"Invalid API key"`         |
| **`code`**  | `string`| Yes      | Machine-readable error code (e.g., `403_forbidden`).                        | `"AUTH_001"`                |
| **`status`**| `integer`| Yes      | HTTP status code.                                                          | `404`                       |
| **`details`**| `object` | No       | Additional context (e.g., `{"field": "api_key"}`).                          | `{ "missing_field": "token" }` |

---

## **4. Query Examples**

### **4.1 GET /users**
**Request:**
```http
GET /v1/users?limit=20&sort=-created_at&filter[status]=active
Headers:
  Authorization: Bearer xxxx.yyyy.zzzz
  Accept: application/json
```
**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "user123",
      "name": "Alice",
      "email": "alice@example.com",
      "created_at": "2023-10-01T10:00:00Z",
      "metadata": { "role": "admin" }
    }
  ],
  "links": {
    "self": "/v1/users?limit=20&sort=-created_at",
    "next": "/v1/users?limit=20&offset=20"
  },
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0
  }
}
```

### **4.2 POST /orders**
**Request:**
```http
POST /v1/orders
Headers:
  Content-Type: application/json
  Authorization: Bearer xxxx.yyyy.zzzz
Body:
{
  "user_id": "user123",
  "items": [
    { "product_id": "prod456", "quantity": 2 }
  ]
}
```
**Response (201 Created):**
```json
{
  "id": "order789",
  "user_id": "user123",
  "total": 99.99,
  "status": "pending",
  "created_at": "2023-10-15T12:00:00Z",
  "links": {
    "self": "/v1/orders/order789"
  }
}
```

### **4.3 Error Example (400 Bad Request)**
**Request:**
```http
POST /v1/login
Headers:
  Content-Type: application/json
Body:
{
  "email": "invalid-email",
  "password": "secret"
}
```
**Response:**
```json
{
  "error": "Invalid credentials",
  "code": "AUTH_001",
  "status": 400,
  "details": {
    "field": "email",
    "message": "Must be a valid email address"
  }
}
```

---

## **5. Implementation Checklist**
To ensure compliance with API Standards:
1. **Design Phase**:
   - [ ] Use **OpenAPI** (Swagger) for API documentation.
   - [ ] Define **versioned endpoints** (e.g., `/v2/users`).
   - [ ] Plan for **pagination** and **filtering** requirements.

2. **Development Phase**:
   - [ ] Implement **input validation** (e.g., using libraries like `joi` or `zod`).
   - [ ] Enforce **rate limiting** (e.g., `express-rate-limit` or `nginx`).
   - [ ] Log all API calls with **structured metadata** (e.g., `user_id`, `ip_address`).

3. **Testing Phase**:
   - [ ] Validate **error responses** match the schema.
   - [ ] Test **authentication flows** (OAuth/JWT).
   - [ ] Verify **performance** under load (e.g., 1000+ requests/minute).

4. **Deployment Phase**:
   - [ ] Enable **API gateway** (e.g., Kong, Apigee) for routing and caching.
   - [ ] Set up **monitoring** (Prometheus + Grafana).
   - [ ] Document **deprecation policies** (e.g., 6-month notice before removal).

---

## **6. Related Patterns**
| Pattern               | Description                                                                 | When to Use                          |
|-----------------------|-----------------------------------------------------------------------------|---------------------------------------|
| **[RESTful API]**     | Resource-oriented APIs using HTTP methods.                                  | When building standard CRUD APIs.     |
| **[gRPC]**            | High-performance RPC framework.                                             | For internal microservices.           |
| **[GraphQL]**         | Flexible query language for APIs.                                           | When clients need custom data shapes. |
| **[Event-Driven APIs]** | Async communication via events (e.g., Kafka, Webhooks).                 | For real-time updates or decoupled services. |
| **[OpenAPI/Swagger]** | Standard for API documentation and testing.                                 | When collaborating with external teams. |

---
**Last Updated:** [Insert Date]
**Version:** 1.2.0