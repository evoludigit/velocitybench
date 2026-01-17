# **[Pattern] REST Approaches: Reference Guide**

---

## **Overview**
The **REST (Representational State Transfer) Approaches** pattern defines how resource interactions are designed, structured, and accessed in RESTful APIs. This guide covers REST’s core principles, request/response conventions, and best practices for implementing scalable, stateless, and cacheable web services.

REST operates on a **client-server architecture** with clear separation of concerns. Each resource (e.g., `/users`, `/orders`) follows a **resource-based URI**, uses **standard HTTP methods** (`GET`, `POST`, `PUT`, `DELETE`), and relies on **stateless requests**—where each call contains all necessary data for processing.

This pattern emphasizes **semantic URIs**, **proper HTTP status codes**, and **payload standardization** (e.g., JSON/XML) for consistency and tooling support.

---

## **Key Concepts & Implementation Details**

| **Concept**               | **Definition**                                                                                     | **Implementation Notes**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Statelessness**         | Each request must contain all required data to fulfill a task (no server-side session tracking).   | Use tokens (JWT) for auth but avoid storing session state on the server.                                      |
| **Resource Identification**| URIs represent resources, not actions.                                                             | Example: `/products/123` (not `/deleteProduct?id=123`).                                                     |
| **HTTP Methods**          | Standard actions mapped to HTTP verbs: `GET` (read), `POST` (create), `PUT/PATCH` (update), `DELETE` (remove). | Use `405 Method Not Allowed` if a method is unsupported.                                                   |
| **CRUD Mappings**         | REST maps database operations to HTTP methods.                                                     |                                                                                                               |
|                           | `GET`       | Fetch a resource or collection.                                                                       |
|                           | `POST`      | Create a new resource.                                                                               |
|                           | `PUT`       | Fully replace a resource (idempotent).                                                                  |
|                           | `PATCH`     | Partially update a resource.                                                                          |
|                           | `DELETE`    | Remove a resource.                                                                                     |
| **Idempotency**           | Repeating identical requests should have the same effect (e.g., safe methods like `GET`, `PUT`).   | Ensure `PUT` requests overwrite data deterministically.                                                     |
| **Caching**               | Servers indicate cacheability via headers (`Cache-Control`, `ETag`, `Last-Modified`).              | Use conditional requests (`If-None-Match`) to avoid unnecessary data transfer.                               |
| **Security**              | Auth via `Authorization` header (e.g., `Bearer <token>`), HTTPS for encryption.                  | Avoid sensitive data in URIs (use query params or headers only for small tokens).                           |
| **Pagination**            | Large datasets are split via `?page=2&limit=10`.                                                  | Return `X-Total-Count` and `Link` headers for next/prev pages.                                              |
| **Error Responses**       | Standardized JSON responses with `status`, `error`, and `message`.                                 | Use `400` (client), `404` (resource), `500` (server) errors appropriately.                                  |
| **HATEOAS**               | Hypermedia controls provide links to related actions.                                             | Return `links` array in responses (e.g., `GET /users/1 → { "links": { "self": "/users/1", "orders": "/users/1/orders" } }`). |

---

## **Schema Reference**

### **Standard Response Format**
All REST responses follow this schema (JSON example):

```json
{
  "status": integer (e.g., 200, 201, 400),
  "error": string (null if success),
  "message": string,
  "data": {
    // Payload data
  },
  "links": {
    "self": string (resource URI),
    "parent": string (optional),
    "next": string (optional pagination),
    "prev": string (optional pagination)
  }
}
```

### **Common HTTP Status Codes**
| **Code** | **Name**         | **Use Case**                                                                                     |
|----------|------------------|-------------------------------------------------------------------------------------------------|
| `200 OK` | Success          | Request processed; data returned.                                                               |
| `201 Created` | New resource     | `POST` successful; return `Location: <URI>` header.                                            |
| `400 Bad Request` | Client error     | Invalid input (e.g., malformed JSON).                                                          |
| `401 Unauthorized` | Auth failed      | Missing/invalid `Authorization` header.                                                       |
| `403 Forbidden`   | Access denied     | Valid auth but insufficient permissions.                                                        |
| `404 Not Found`   | Resource missing  | Endpoint/ID doesn’t exist.                                                                    |
| `405 Method Not Allowed` | Wrong HTTP method | `GET` called on a `POST` endpoint.                                                              |
| `500 Internal Error` | Server failure   | Unexpected backend error (return generic message).                                              |

---

## **Query Examples**

### **1. Create a User**
**Request:**
```http
POST /api/v1/users
Headers:
  Content-Type: application/json
  Authorization: Bearer <token>
Body:
{
  "name": "Alice",
  "email": "alice@example.com"
}
```
**Success Response (201 Created):**
```json
{
  "status": 201,
  "data": {
    "id": "123",
    "name": "Alice",
    "createdAt": "2023-10-01T12:00:00Z"
  },
  "links": {
    "self": "/api/v1/users/123"
  }
}
```

### **2. Retrieve User Orders**
**Request:**
```http
GET /api/v1/users/123/orders?page=1&limit=5
Headers:
  Authorization: Bearer <token>
```
**Response:**
```json
{
  "status": 200,
  "data": [
    { "orderId": "456", "total": 99.99 },
    { "orderId": "789", "total": 49.99 }
  ],
  "links": {
    "self": "/api/v1/users/123/orders?page=1&limit=5",
    "next": "/api/v1/users/123/orders?page=2&limit=5"
  }
}
```

### **3. Update User Address (PATCH)**
**Request:**
```http
PATCH /api/v1/users/123
Headers:
  Content-Type: application/json
  Authorization: Bearer <token>
Body:
{
  "address": {
    "street": "123 Main St",
    "city": "New York"
  }
}
```
**Response (200 OK):**
```json
{
  "status": 200,
  "data": {
    "address": {
      "street": "123 Main St",
      "city": "New York"
    }
  }
}
```

### **4. Handle Validation Error (400)**
**Request:**
```http
POST /api/v1/users
Headers:
  Content-Type: application/json
Body:
{
  "name": "",
  "email": "invalid-email"
}
```
**Response:**
```json
{
  "status": 400,
  "error": "validation",
  "message": "Email is invalid; Name is required.",
  "details": [
    { "field": "name", "message": "Cannot be empty" },
    { "field": "email", "message": "Must be a valid email" }
  ]
}
```

---

## **Related Patterns**
1. **AJAX (Asynchronous JavaScript + XML)**
   - Frontend pattern for asynchronous REST calls via `fetch`/`axios` with JSON handling.
   - *Key Link*: REST clients often use AJAX for dynamic UI updates.

2. **GraphQL**
   - Alternative to REST for data querying (no over-fetching; flexible schemas).
   - *Comparison*: REST is resource-centric; GraphQL is query-centric.

3. **Stateless Session Pattern**
   - Complements REST by using tokens (JWT) for auth without server-side sessions.

4. **API Gateway**
   - Routes requests to backend services (REST or otherwise) for scalability and security.

5. **HATEOAS (Hypermedia as the Engine of Application State)**
   - Extends REST by dynamically linking resources via hypermedia controls (e.g., `links` in responses).

6. **OpenAPI Specification**
   - Standardized API contract (Swagger) for REST endpoints, enabling tooling (Postman, Redoc).