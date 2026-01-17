# **[Pattern] REST Techniques Reference Guide**

---
## **Overview**
The **REST Techniques** pattern defines a set of best practices for designing and implementing **RESTful APIs**, ensuring scalability, consistency, and interoperability. REST (Representational State Transfer) leverages HTTP methods, resource-based URIs, and stateless communication to create efficient and maintainable web services. This guide covers core principles, implementation details, and common query patterns, along with related architectural patterns.

---

## **1. Key Concepts & Schema Reference**

### **Core REST Principles**
| **Principle**               | **Definition**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|
| **Resource-Based Design**   | APIs expose resources (e.g., `/users`, `/orders`) as uniform endpoints.      |
| **Statelessness**          | Servers do not store client context; each request must contain all required data. |
| **Uniform Interface**      | Standardized methods (`GET`, `POST`, etc.), URIs, and representations.          |
| **Client-Server Separation**| Frontends (clients) and backends (servers) are decoupled.                     |
| **Layered System**         | Intermediaries (load balancers, proxies) can be inserted transparently.      |
| **Caching**                | Responses can be cached to reduce latency and server load.                    |
| **HTTP Methods**           | Defines actions: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, etc.                |

---

### **Schema Reference: RESTful Endpoint Structure**
| **Component**       | **Description**                                                                 | **Example**                     |
|---------------------|-------------------------------------------------------------------------------|---------------------------------|
| **Base URI**        | Root domain/path for all endpoints.                                           | `/api/v1`                       |
| **Resource Path**   | Noun representing a data entity.                                               | `/customers`                    |
| **Identifiers**     | Unique keys in URLs (optional for collections).                                | `/customers/123`                |
| **Query Parameters**| Optional key-value pairs for filtering/sorting.                                | `?status=active&page=2`         |
| **Body (Payload)**  | Request data for `POST/PUT/PATCH` (JSON/XML).                                 | `{ "name": "Alice", "email": "alice@example.com"}` |

**Example URI Structure:**
```
GET  /api/v1/users/42?role=admin&sort=date:desc
POST /api/v1/orders
    Content-Type: application/json
    { "userId": 42, "items": [...] }
```

---

## **2. Implementation Details**

### **HTTP Methods & Use Cases**
| **Method** | **Purpose**                          | **Idempotent?** | **Example**                     |
|------------|--------------------------------------|-----------------|---------------------------------|
| `GET`      | Retrieve a resource or collection.   | ✅ Yes          | `GET /api/v1/products`          |
| `POST`     | Create a new resource.               | ❌ No           | `POST /api/v1/users`            |
| `PUT`      | Replace an existing resource.         | ✅ Yes          | `PUT /api/v1/users/42`          |
| `PATCH`    | Partially update a resource.         | ✅ Yes          | `PATCH /api/v1/users/42`        |
| `DELETE`   | Remove a resource.                   | ✅ Yes          | `DELETE /api/v1/users/42`       |
| `HEAD`     | Fetch headers only (for caching).    | ✅ Yes          | `HEAD /api/v1/users/42`         |

**Best Practices:**
- Use `GET` for safe, idempotent operations.
- Avoid `PUT`/`DELETE` for side effects (e.g., password resets).
- Prefer `PATCH` over `PUT` for partial updates.

---

### **Status Codes & Responses**
| **Code** | **Category**  | **Meaning**                                      | **Example Use Case**               |
|----------|---------------|--------------------------------------------------|------------------------------------|
| `200 OK` | Success       | Request succeeded.                               | Returning data.                   |
| `201 Created` | Success     | Resource created (with `Location` header).      | POST `/users` → `201 Created`     |
| `204 No Content` | Success | No content returned.                           | DELETE `/orders/123` → `204`      |
| `400 Bad Request` | Client Error | Invalid syntax/input.                          | Missing required field.           |
| `401 Unauthorized` | Client Error | Authentication failed.                         | Missing API key.                  |
| `403 Forbidden`   | Client Error | No permission.                                  | GET `/admin` (unauthorized).     |
| `404 Not Found`   | Client Error | Resource doesn’t exist.                         | GET `/users/999`                  |
| `405 Method Not Allowed` | Client Error | Unsupported HTTP method.                       | POST `/users` (only GET allowed). |
| `500 Internal Server Error` | Server Error | Unexpected server failure.                   | Database crash.                   |

---

### **Pagination & Filtering**
| **Pattern**       | **Description**                                                                 | **Example Query**                          |
|-------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| **Offset/Limit**  | Basic pagination (simple but inefficient for large datasets).                | `?offset=10&limit=50`                      |
| **Cursor-Based**  | Uses a token (e.g., last ID) for efficient pagination.                       | `?after=12345`                             |
| **Key-Based**     | Filters by specific fields (e.g., `status`, `category`).                     | `?status=active&category=electronics`     |
| **Sorting**       | Orders results by a field (ascending/descending).                           | `?sort=-created_at` (descending)           |
| **Projection**    | Selects only needed fields (reduces bandwidth).                             | `?fields=id,name`                          |

---
## **3. Query Examples**

### **Example 1: Fetching a User Profile**
```http
GET /api/v1/users/42?fields=id,name,email
Host: api.example.com
Accept: application/json
```
**Response (`200 OK`):**
```json
{
  "id": 42,
  "name": "Alice Smith",
  "email": "alice@example.com"
}
```

---

### **Example 2: Creating an Order**
```http
POST /api/v1/orders
Host: api.example.com
Content-Type: application/json

{
  "userId": 42,
  "items": [
    { "productId": 101, "quantity": 2 }
  ]
}
```
**Response (`201 Created`):**
```http
Location: /api/v1/orders/789
```

---

### **Example 3: Updating a Product (Partial)**
```http
PATCH /api/v1/products/202
Host: api.example.com
Content-Type: application/json

{
  "price": 19.99,
  "stock": 15
}
```
**Response (`200 OK`):**
```json
{
  "id": 202,
  "name": "Laptop",
  "price": 19.99,
  "stock": 15
}
```

---

### **Example 4: Filtered & Paginated Orders**
```http
GET /api/v1/orders?userId=42&status=shipped&page=2&limit=10
Host: api.example.com
Accept: application/json
```
**Response (`200 OK`):**
```json
{
  "data": [
    { "id": 789, "userId": 42, "status": "shipped", ... },
    ...
  ],
  "pagination": {
    "total": 25,
    "page": 2,
    "limit": 10
  }
}
```

---

## **4. Security Considerations**
| **Technique**               | **Description**                                                                 | **Implementation**                          |
|-----------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Authentication**          | Secure API access via tokens (JWT, OAuth2).                                    | `Authorization: Bearer <token>`             |
| **Authorization**           | Role-based access control (RBAC) for endpoints.                              | `/api/v1/admin/*` (only for admin roles).   |
| **Input Validation**        | Sanitize/query parameters to prevent injection.                              | Use libraries like `express-validator`.     |
| **HTTPS**                   | Encrypt traffic to protect data in transit.                                  | Enforce TLS 1.2+.                           |
| **Rate Limiting**           | Prevent abuse with token buckets/leaky buckets.                              | Nginx `limit_req` or cloud provider rules.  |
| **CORS**                    | Restrict domain access to trusted origins.                                    | `Access-Control-Allow-Origin: https://client.com` |

---

## **5. Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[GraphQL]**             | Query language for flexible data fetching (alternative to REST).              | When clients need dynamic field selection. |
| **[HATEOAS]**             | Links in responses to guide client navigation.                               | For API-first architectures.             |
| **[Event-Driven Architectures]** | Decoupled communication via events (e.g., Kafka, WebSockets).           | Real-time updates or async workflows.    |
| **[API Gateways]**        | Single entry point for routing, rate limiting, and security.                  | Multi-service microservices.             |
| **[OpenAPI/Swagger]**     | Standard for API documentation and testing.                                  | For self-documenting APIs.               |
| **[gRPC]**                | High-performance RPC (alternative to REST).                                   | Internal services or low-latency needs.  |

---
## **6. Troubleshooting Common Issues**

| **Issue**                          | **Root Cause**                          | **Solution**                              |
|------------------------------------|----------------------------------------|-------------------------------------------|
| **500 Errors**                     | Server-side exceptions (e.g., DB crash).| Implement logging (e.g., Sentry) and retries. |
| **CORS Errors**                    | Missing `Access-Control-Allow-Origin`.   | Configure CORS headers server-side.       |
| **Rate Limits Exceeded**           | Too many requests in a short time.      | Implement exponential backoff or caching. |
| **Pagination Too Slow**            | Inefficient `OFFSET` queries.           | Use cursor-based pagination.              |
| **Large Payloads**                 | Clients receiving unnecessary data.     | Use projection (`?fields=...`) or GraphQL. |

---
## **7. Tools & Libraries**

| **Category**               | **Tools/Libraries**                          | **Purpose**                              |
|----------------------------|---------------------------------------------|------------------------------------------|
| **Frameworks**             | Express.js, Flask, Spring Boot             | Backend API development.                 |
| **Validation**             | Zod, Joi, express-validator                 | Schema validation.                      |
| **Testing**                | Postman, Newman, Jest                      | API testing and mocking.                 |
| **Documentation**          | Swagger UI, Redoc, OpenAPI Generator       | Auto-generated docs.                     |
| **Monitoring**             | Prometheus, Grafana, Datadog               | Performance and error tracking.          |
| **Caching**                | Redis, Memcached                           | Reduce database load.                    |

---
## **8. Best Practices Checklist**
1. **Design First**: Use OpenAPI/Swagger to define contracts.
2. **Versioning**: Include version in URIs (`/api/v1/users`).
3. **Idempotency**: Ensure `GET`, `PUT`, `DELETE` are idempotent.
4. **HATEOAS**: Include links in responses for discoverability.
5. **Caching**: Use `ETag` or `Cache-Control` headers.
6. **Error Handling**: Return consistent error formats (e.g., JSON API spec).
7. **Rate Limiting**: Protect against abuse.
8. **Logging**: Track requests/responses for debugging.

---
**Final Note**: REST is a **standard**, not a strict standard—adapt practices to your use case while maintaining consistency. For complex APIs, consider hybrid approaches (e.g., REST + GraphQL).