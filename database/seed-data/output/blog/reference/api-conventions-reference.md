---
# **[Pattern] API Conventions Reference Guide**
*Standards and Best Practices for Consistent API Design*

---

## **Overview**
API Conventions define a standardized set of rules for designing, structuring, and documenting APIs to ensure **predictability, developer-friendliness, and interoperability**. This pattern establishes reusable patterns for:
- **Resource naming**, **path design**, and **HTTP methods** (RESTful principles)
- **Request/response formats** (JSON/XML, content negotiation)
- **Error handling**, **authentication**, and **rate-limiting conventions**
- **Pagination**, **filtering**, and **sorting** consistency

Adhering to these conventions reduces onboarding friction, minimizes documentation overhead, and fosters maintainable, scalable APIs.

---

## **Implementation Details**

### **1. Core Principles**
| Principle               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **RESTful Design**      | Use nouns for resources, not verbs (e.g., `/users` instead of `/getUsers`). |
| **Resource Hierarchy**  | Nested resources follow hierarchical paths (e.g., `/orders/{orderId}/items`). |
| **Idempotent Methods**  | `GET`, `PUT`, `DELETE` should be idempotent; `POST` and `PATCH` are non-idempotent. |
| **Statelessness**       | Avoid server-side session storage; use tokens (JWT/OAuth) for auth.           |
| **Uniform Interface**   | Standardize request/response shapes (e.g., always return `{ data, meta }`). |

---

### **2. Path and Query Conventions**

#### **Resource Naming**
| Rule                  | Example                          | Anti-Example              |
|-----------------------|----------------------------------|---------------------------|
| **Lowercase singular**| `/users`                         | `/Users`, `/user`         |
| **Hyphens for compound** | `/user-profiles`            | `/userProfiles`, `/user profile` |
| **Plural endpoints**  | `/tasks` (not `/task`)          | `/task`                   |

#### **HTTP Methods**
| Method | Use Case                          | Example Endpoint               |
|--------|-----------------------------------|---------------------------------|
| `GET`  | Retrieve data (idempotent)        | `/api/v1/users/{id}`            |
| `POST` | Create new resource               | `/api/v1/users`                 |
| `PUT`  | Replace entire resource           | `/api/v1/users/{id}`            |
| `PATCH`| Partial updates                   | `/api/v1/users/{id}` (with `patch` header) |
| `DELETE`| Remove resource                    | `/api/v1/users/{id}`            |
| `HEAD` | Fetch headers only (e.g., metadata) | `/api/v1/users/{id}` (HEAD)    |

#### **Query Parameters**
| Purpose          | Syntax                     | Example                          | Notes                                  |
|------------------|---------------------------|----------------------------------|----------------------------------------|
| **Filtering**    | `?field=value`             | `/api/v1/users?status=active`     | Use `AND/OR` via `filter[]` arrays if needed. |
| **Pagination**   | `?page=1&limit=10`         | `/api/v1/tasks?page=2&limit=5`   | Server-side pagination required.       |
| **Sorting**      | `?sort=-createdAt`         | `/api/v1/posts?sort=title`       | `-` for descending order.             |
| **Search**       | `?q=keyword`               | `/api/v1/products?q=laptop`      | Full-text search (client-side or Elasticsearch). |

---

### **3. Request/Response Schema**
#### **Request Body (POST/PUT/PATCH)**
- **Content-Type:** `application/json` (default).
- **Idempotency Key:** For `POST`/`PATCH`, include `Idempotency-Key` header to prevent duplicate operations.

| Field         | Description                          | Example                          |
|---------------|--------------------------------------|----------------------------------|
| `data`        | Required payload                     | `{ "name": "John", "email": "john@example.com" }` |
| `meta` (opt.) | Additional metadata (e.g., `locale`) | `{ "locale": "en-US" }`         |

#### **Response Structure**
| Field       | Type    | Required | Description                                                                 |
|-------------|---------|----------|-----------------------------------------------------------------------------|
| `status`    | string  | ✅        | `"success"` or `"error"` (human-readable)                                   |
| `code`      | string  | ✅        | HTTP status code (e.g., `"200"`, `"404"`).                                 |
| `data`      | object  | ✅        | Payload (empty `{}` for no data).                                           |
| `meta`      | object  | ❌        | Metadata (e.g., `pagination`, `links`).                                      |
| `errors`    | array   | ❌        | `[{ "field": "email", "message": "Invalid format" }]` (only if `status=error`). |

**Example Success Response:**
```json
{
  "status": "success",
  "code": "200",
  "data": {
    "id": "123",
    "name": "Jane Doe"
  },
  "meta": {
    "pagination": { "total": 100, "limit": 10, "page": 1 }
  }
}
```

**Example Error Response:**
```json
{
  "status": "error",
  "code": "400",
  "errors": [
    { "field": "email", "message": "Must be a valid email address" }
  ]
}
```

---

### **4. Error Handling**
| HTTP Code | Code Field | Description                          | Example Use Case                |
|-----------|------------|--------------------------------------|----------------------------------|
| `200`     | `"200"`    | Success                              | GET `/tasks`                     |
| `201`     | `"201"`    | Resource created                     | POST `/users`                    |
| `400`     | `"400"`    | Bad request                          | Invalid `Content-Type` header    |
| `401`     | `"401"`    | Unauthorized                         | Missing/invalid API key          |
| `403`     | `"403"`    | Forbidden                            | Insufficient permissions         |
| `404`     | `"404"`    | Not found                            | `/users/999` (non-existent)      |
| `429`     | `"429"`    | Rate limit exceeded                  | Too many requests in 1 minute    |
| `500`     | `"500"`    | Internal server error                | Backend crash                    |

**Rate Limiting Headers:**
- `X-RateLimit-Limit`: Maximum allowed requests (e.g., `60`).
- `X-RateLimit-Remaining`: Requests left (e.g., `55`).
- `X-RateLimit-Reset`: Seconds until reset (e.g., `30`).

---

### **5. Authentication & Authorization**
| Method               | Usage                                  | Example Header                     |
|----------------------|----------------------------------------|------------------------------------|
| **API Key**          | Simple auth for non-sensitive endpoints| `Authorization: ApiKey <token>`    |
| **Bearer Token (JWT)**| Secure auth                            | `Authorization: Bearer <jwt>`       |
| **OAuth 2.0**        | Delegated access                       | `Authorization: Bearer <oauth-token>`|
| **Basic Auth**       | Legacy systems                         | `Authorization: Basic <base64-encoded>` |

**Token Claims (JWT):**
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "email": "john@example.com",
  "roles": ["user", "admin"],
  "exp": 1735689600
}
```

---

### **6. Versioning**
- **Path Versioning:** `/api/v1/users` (recommended for REST).
- **Header Versioning:** `Accept-API-Version: v1` (alternative).
- **Never break backward compatibility** unless absolutely necessary.

---

### **7. Example APIs**
#### **Create a User (POST)**
```http
POST /api/v1/users
Content-Type: application/json

{
  "data": {
    "name": "Alice",
    "email": "alice@example.com",
    "role": "admin"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "code": "201",
  "data": { "id": "abc123", "name": "Alice" }
}
```

#### **List Users (GET with Pagination)**
```http
GET /api/v1/users?page=1&limit=10
Accept: application/json
Authorization: Bearer <jwt>
```

**Response:**
```json
{
  "status": "success",
  "code": "200",
  "data": [
    { "id": "1", "name": "Bob" },
    { "id": "2", "name": "Charlie" }
  ],
  "meta": {
    "pagination": { "total": 50, "page": 1, "limit": 10 }
  }
}
```

---

## **Query Examples**
### **1. Filtering**
```http
GET /api/v1/posts?status=published&category[]=tech&category[]=news
```

### **2. Sorting**
```http
GET /api/v1/products?sort=-price&sort=name
```

### **3. Complex Search**
```http
GET /api/v1/search?q=laptop+black&filter[price][min]=500
```

### **4. Conditional Requests**
```http
GET /api/v1/inventory?if-match=ETag:"abc123"
```

---

## **Related Patterns**
| Pattern                        | Description                                                                 | When to Use                          |
|--------------------------------|-----------------------------------------------------------------------------|--------------------------------------|
| **[Idempotency Keys]**          | Prevent duplicate operations via unique request IDs.                       | For `POST/PATCH` to avoid race conditions. |
| **[HATEOAS]**                  | Include links in responses for navigation (e.g., `links: { self: "/users/1" }`). | When designing highly linked APIs. |
| **[OpenAPI/Swagger]**           | Standardize API docs with OpenAPI 3.0.                                       | For interactive API documentation.  |
| **[GraphQL]**                  | Alternate query language for flexible data fetching.                        | When clients need dynamic schemas.   |
| **[Event-Driven APIs]**        | Asynchronous operations via webhooks/events.                               | For real-time updates (e.g., order status). |
| **[CORS]**                     | Enable cross-origin requests with `Access-Control-Allow-Origin`.             | For frontend-backend integration.    |

---

## **Best Practices**
1. **Document Early:** Use OpenAPI/Swagger to auto-generate docs.
2. **Deprecate Gracefully:** Add `deprecated: true` to endpoints and redirect to new ones.
3. **Monitor:** Track errors with tools like Sentry or Datadog.
4. **Localization:** Support `Accept-Language` headers for i18n.
5. **Caching:** Use `ETag`/`Last-Modified` headers for efficient caching.