---
# **[Pattern] REST Conventions Reference Guide**
*Standardized design principles for RESTful APIs*

---

## **Overview**
REST (Representational State Transfer) **Conventions** define a set of best practices for structuring HTTP-based APIs to ensure consistency, scalability, and developer-friendliness. Unlike strict architectural constraints (e.g., REST constraints), REST Conventions provide recommendations for resource naming, URI design, HTTP methods, and error handling to improve usability without mandating rigid rules. This guide outlines key conventions and their implementation.

---

## **Key Concepts & Implementation Details**

### **1. Resource Naming**
Use **nouns** (not verbs) to represent resources to reflect their state.
✅ **Good**:
`/users`, `/products`, `/orders`
❌ **Avoid**:
`/getUsers`, `/searchProducts` (use query params for filters)

### **2. URI Design**
- **Lowercase with hyphens** for readability (avoid underscores).
  ✅ `/user-profile`
  ❌ `/user_profile`
- **Plural nouns** for collections (unless domain-specific).
  ✅ `/posts` (not `/post`)
- **Versioning** via URI path or header (prefer path for backward compatibility).
  ✅ `/v1/users` or `/users?api_version=1`
  ❌ `/users/latest` (avoid implicit assumptions)

### **3. HTTP Methods**
| Method | Use Case                          | Example URI          | Notes                                  |
|--------|-----------------------------------|----------------------|----------------------------------------|
| `GET`  | Retrieve resources               | `/users/123`         | Safe, idempotent, cacheable.           |
| `POST` | Create a new resource            | `/users`             | Send entity in request body.            |
| `PUT`  | Replace a resource (full update) | `/users/123`         | Idempotent; requires full payload.     |
| `PATCH`| Partial update                    | `/users/123`         | Body specifies fields to modify.       |
| `DELETE`| Remove a resource                | `/users/123`         | Safe for collections (e.g., soft delete). |
| `HEAD` | Minimal response (headers only)  | `/users/123`         | Useful for checks (e.g., existence).   |

**Notes**:
- Use `POST` for **idempotent** actions (e.g., sending a purchase order).
- Reserve `PUT`/`DELETE` for **resource-level** operations.

### **4. Query Parameters**
- **Filtering**: `?status=active`
- **Sorting**: `?sort=name:desc`
- **Pagination**: `?page=2&limit=10`
- **Field selection**: `?fields=name,email`
- **Pagination headers**:
  ```http
  Link: <https://api.example.com/users?page=3>; rel="next",
        <https://api.example.com/users?page=1>; rel="first"
  ```

### **5. Response Formats**
- **Default**: `application/json` (with `Content-Type` header).
- **Support other formats** (e.g., `application/xml`) via `Accept` header:
  ```http
  Accept: application/json, application/xml
  ```
- **Error responses**: Standardize using [HTTP status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) and [JSON:API error format](https://jsonapi.org/format/#errors).

### **6. Authentication & Authorization**
- **OAuth 2.0/JWT** (preferred for stateless APIs).
- **Headers**:
  ```http
  Authorization: Bearer <token>
  ```
- **Scope-based access**:
  ```http
  Authorization: Bearer <token>; scope=read:orders,write:shipping
  ```

### **7. Idempotency & Retries**
- **Idempotent requests** (e.g., `PUT`, `GET`) can be retried safely.
- **Non-idempotent** actions (e.g., `POST` to `/orders`) may require:
  - **Idempotency keys** in headers (`Idempotency-Key: abc123`).
  - **Retry-after** headers for rate-limited endpoints.

---

## **Schema Reference**

| Convention          | Description                                                                 | Example URI          | Notes                                  |
|---------------------|-----------------------------------------------------------------------------|----------------------|----------------------------------------|
| **Resource Naming** | Use plural nouns for collections.                                           | `/products`          | Avoid verbs (e.g., `/searchProducts`). |
| **Nesting**         | Use `/parent/child` for hierarchical data (e.g., `/orders/{id}/items`).   | `/users/{id}/orders` | Depth limited to 3–4 levels.           |
| **Query Params**    | Filter, sort, paginate via query strings.                                  | `/users?status=active`| Avoid deep nesting (e.g., `?a.b.c=1`). |
| **Versioning**      | Embed version in URI or header.                                            | `/v1/users`          | Prefer URI for clarity.                |
| **Hyphens**         | Use `-` in paths (not underscores or spaces).                              | `/user-profile`      | Improves readability.                  |
| **HTTP Methods**    | Align methods with CRUD operations.                                         | `POST /orders`       | See table above for details.           |
| **Status Codes**    | Use standard HTTP codes (e.g., `201 Created`).                              | `200 OK`             | Custom codes (e.g., `429 Too Many Requests`). |
| **Pagination**      | Support `?page` and `?limit` with `Link` headers.                          | `Link: <next-page>`  | Use cursor-based pagination for large datasets. |

---

## **Query Examples**

### **1. Retrieving a User**
```http
GET /v1/users/123
Headers:
  Accept: application/json
Response (200 OK):
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com"
}
```

### **2. Creating a Product (Idempotent POST)**
```http
POST /v1/products
Headers:
  Content-Type: application/json
  Idempotency-Key: abc123
Body:
{
  "name": "Laptop",
  "price": 999.99
}
Response (201 Created):
{
  "id": "456",
  "name": "Laptop"
}
Headers:
  Location: /v1/products/456
```

### **3. Updating a User (Partial Patch)**
```http
PATCH /v1/users/123
Headers:
  Content-Type: application/json
Body:
{
  "email": "new-email@example.com"
}
Response (200 OK):
{
  "id": "123",
  "email": "new-email@example.com"
}
```

### **4. Filtering and Paginating Users**
```http
GET /v1/users?status=active&page=2&limit=10
Response (200 OK):
{
  "data": [
    { "id": "789", "name": "Bob" },
    { "id": "101", "name": "Charlie" }
  ],
  "links": {
    "next": "/v1/users?status=active&page=3&limit=10"
  }
}
Headers:
  Link: <https://api.example.com/users?status=active&page=3>; rel="next"
```

### **5. Error Handling (404 Not Found)**
```http
GET /v1/users/999
Response (404 Not Found):
{
  "error": {
    "code": "not_found",
    "message": "User with ID 999 not found",
    "details": {
      "resource": "user",
      "id": "999"
    }
  }
}
```

---

## **Related Patterns**
1. **[API Versioning](https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api)**
   - How to version APIs alongside REST conventions (e.g., `/v1/endpoint`).

2. **[HATEOAS (Hypermedia as the Engine of Application State)](https://www.martinfowler.com/articles/richardsonMaturityModel.html)**
   - Extends REST by dynamically linking resources (e.g., `Link` headers).

3. **[OpenAPI/Swagger](https://swagger.io/specification/)**
   - Standardize API documentation for REST APIs (use `OpenAPI 3.0` for modern schemas).

4. **[GraphQL Over REST](https://graphql.org/)**
   - Alternative to REST for flexible queries (complements REST conventions via subresources).

5. **[RESTful Security](https://www.owasp.org/www-community/REST_Security_Cheat_Sheet)**
   - Best practices for securing REST APIs (e.g., JWT, rate limiting).

6. **[CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)**
   - Configure Cross-Origin Resource Sharing for web-based clients.

7. **[Event-Driven REST](https://blog.logrocket.com/api-event-driven-architecture/)**
   - Combine REST with async events (e.g., Webhooks) for scalability.

---
**Further Reading**:
- [Fielding’s Dissertation (REST Origins)](https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm)
- [REST API Design Rulebook](https://restfulapi.net/) (by Roy Fielding)