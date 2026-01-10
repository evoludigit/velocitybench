**[Pattern] API Techniques Reference Guide**

---

### **Overview**
API (Application Programming Interface) **Techniques** refer to standardized methods, patterns, and best practices for designing, structuring, and optimizing RESTful or GraphQL APIs. This guide covers core implementation details, common patterns (e.g., pagination, filtering, caching), and anti-patterns to ensure scalability, consistency, and performance. Whether you're building a new API or refining an existing one, these techniques help enforce clarity in requests/responses, reduce client-side complexity, and improve maintainability.

---

### **Key Concepts & Implementation Details**
Below are foundational API techniques categorized by functionality:

#### **1. Resource Design**
- **Nouns, not verbs**: Use plural nouns for resources (e.g., `/users`, not `/getUsers`).
- **Hierarchical relationships**: Nest sub-resources (e.g., `/users/{id}/orders`).
- **Versioning**: Include via URL (`/v1/users`) or headers (`Accept: application/vnd.company.v1+json`).

#### **2. HTTP Methods**
| Method  | Use Case                          | Example                      |
|---------|-----------------------------------|------------------------------|
| `GET`   | Retrieve data                     | `/users?role=admin`          |
| `POST`  | Create a resource                 | `/users`                     |
| `PUT`   | Replace a resource (full update)  | `/users/123`                 |
| `PATCH` | Partial update                    | `/users/123` (with `JSON Patch`) |
| `DELETE`| Remove a resource                 | `/users/123`                 |

#### **3. Status Codes**
- **Success**: `200 OK`, `201 Created`, `204 No Content`.
- **Client Errors**: `400 Bad Request`, `401 Unauthorized`, `404 Not Found`.
- **Server Errors**: `500 Internal Server Error`, `503 Service Unavailable`.

#### **4. Query Parameters & Filtering**
Use query strings to refine responses:
- **Basic filters**: `?role=admin&status=active`.
- **Pagination**: `?page=2&limit=10`.
- **Sorting**: `?sort=-createdAt`.
- **Field selection**: Reduce payload size with `?fields=id,name`.

#### **5. Request/Response Formats**
- **Request**: Typically `application/json` or `x-www-form-urlencoded`.
- **Response**: Include:
  - Standard fields: `data`, `links`, `meta` (e.g., pagination counts).
  - Error responses: Structured JSON:
    ```json
    {
      "error": {
        "code": 400,
        "message": "Invalid input field 'email'."
      }
    }
    ```

#### **6. Authentication & Authorization**
- **Auth**: Bearer tokens (`Authorization: Bearer <token>`), API keys (header/cookie).
- **Roles**: Scope permissions via `roles` claim (e.g., `"roles": ["admin"]`).
- **OAuth 2.0**: Use flows like `password` or `client_credentials`.

#### **7. Caching Strategies**
- **HTTP Caching**:
  - `Cache-Control`: Set `max-age` (e.g., `Cache-Control: max-age=3600`).
  - `ETag`/`Last-Modified`: For conditional requests.
- **Client-Side**: Cache responses (e.g., Redis, CDN).

#### **8. Error Handling**
- **Standardize errors**: Use consistent schemas (e.g., `status`, `title`, `detail`).
- **Rate Limiting**: Return `429 Too Many Requests` with `Retry-After` header.

---
### **Schema Reference**
| **Category**         | **Field**          | **Description**                                                                 | **Example**                          |
|----------------------|--------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Pagination**       | `page`             | Current page number.                                                        | `?page=1`                            |
|                      | `limit`            | Items per page.                                                              | `?limit=20`                          |
|                      | `total` (meta)     | Total items across all pages.                                                | `"meta": {"total": 100}`            |
| **Filtering**        | `role`             | Filter by role.                                                              | `?role=admin`                        |
|                      | `status`           | Filter by status (e.g., `active`).                                          | `?status=inactive`                   |
| **Sorting**          | `sort`             | Field to sort by (use `-` for descending).                                  | `?sort=-createdAt`                   |
| **Field Selection**  | `fields`           | Comma-separated fields to include.                                           | `?fields=id,name,email`              |
| **Authentication**   | `Authorization`    | Bearer token in header.                                                      | `Authorization: Bearer xyz123`       |
| **Errors**           | `code`             | HTTP status code (e.g., `404`).                                              | `"code": 404`                        |
|                      | `message`          | Human-readable error description.                                            | `"message": "User not found."`       |

---

### **Query Examples**

#### **1. Basic GET Request**
**Endpoint**: `/users`
**Query**: `?role=admin&limit=10`
**Response**:
```json
{
  "data": [
    { "id": 1, "name": "Alice", "role": "admin" },
    { "id": 2, "name": "Bob", "role": "user" }
  ],
  "meta": { "page": 1, "total": 2 }
}
```

#### **2. Pagination**
**Endpoint**: `/posts?page=2&limit=5`
**Response**:
```json
{
  "data": [
    { "id": 6, "title": "API Techniques 101" },
    { "id": 7, "title": "Scalability Tips" }
  ],
  "meta": {
    "page": 2,
    "total": 50,
    "limit": 5,
    "has_next": true
  }
}
```

#### **3. Filtering & Sorting**
**Endpoint**: `/products?category=electronics&sort=-price`
**Response**:
```json
{
  "data": [
    { "id": 101, "name": "Laptop", "price": 999.99 },
    { "id": 102, "name": "Phone", "price": 699.99 }
  ]
}
```

#### **4. Field Selection**
**Endpoint**: `/users/123?fields=id,name,email`
**Response**:
```json
{
  "data": {
    "id": 123,
    "name": "Charlie",
    "email": "charlie@example.com"
  }
}
```

#### **5. Error Response**
**Endpoint**: `/users/999` (non-existent)
**Response**:
```json
{
  "error": {
    "code": 404,
    "message": "User with ID 999 not found."
  }
}
```

#### **6. Authentication (Bearer Token)**
**Header**:
```
Authorization: Bearer xyz123abc
```
**Response** (Successful):
```json
{
  "data": { "message": "Access granted." }
}
```

---
### **Related Patterns**
1. **[Resource-Oriented Architecture]**
   - Design APIs around distinct resources (e.g., `/users`, `/orders`) to decouple clients from backend logic.

2. **[HATEOAS (Hypermedia as the Engine of Application State)]**
   - Include links in responses to guide clients (e.g., `links: { "next": "/users?page=2" }`).

3. **[GraphQL Alternative to REST]**
   - Query specific fields in one request (e.g., `{ user(id: 1) { name email } }`).

4. **[Webhooks for Asynchronous Events]**
   - Push updates to clients via endpoints (e.g., `/webhooks/order-updated`).

5. **[Rate Limiting & Throttling]**
   - Prevent abuse with headers like `X-RateLimit-Limit: 1000`.

6. **[OpenAPI/Swagger for Documentation]**
   - Automate API docs with tools like Swagger UI (YAML/JSON specs).

7. **[gRPC for High-Performance APIs]**
   - Use binary protocols for internal services (instead of REST/GraphQL).

---
### **Anti-Patterns to Avoid**
- **Overloading URLs**: Avoid `/getUserById?role=admin` (use `/users` with query filters).
- **Unsafe Methods**: Never use `GET` for side effects (e.g., payments).
- **No Versioning**: Hardcodes APIs (break changes force client updates).
- **Under-Engineered Caching**: No `Cache-Control` or stale data.
- **Bulk Data in GET**: Use `POST` for large payloads (e.g., `/import-data`).
- **Ignoring Compression**: Missing `Content-Encoding: gzip` for large responses.