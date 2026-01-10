**[Pattern] API Patterns Reference Guide**

---

### **1. Overview**
API patterns define standard, reusable designs for structuring and implementing RESTful (or other) APIs. These patterns solve common challenges in security, data handling, versioning, caching, and error management while ensuring scalability and maintainability. This guide covers core API patterns, including their purpose, implementation details, and best practices.

---

### **2. Schema Reference**
| **Pattern**            | **Purpose**                                                                 | **Key Components**                                                                 | **HTTP Methods**                     |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------|
| **Resource-based**     | Organizes endpoints around **nouns** (resources) and their attributes.     | `/users`, `/products/{id}`, query filters (`?status=active`).                      | `GET`, `POST`, `PUT`, `DELETE`       |
| **Collection vs. Item** | Separates **collections** (lists) from **items** (individual records).     | `/users` (collection), `/users/123` (item).                                         | `GET`, `POST` (collection), `GET/PUT/DELETE` (item) |
| **Filtering/Sorting**  | Adds search/sort functionality to endpoints via query params.               | `?filter[status]=active&sort=-createdAt`.                                           | `GET`                                |
| **Paginated Responses**| Breaks large datasets into manageable chunks.                              | `?page=2&limit=10`, includes `pagination` metadata in response.                     | `GET`                                |
| **Error Responses**    | Standardizes error formats for debugging/client handling.                  | HTTP status codes + structured JSON (e.g., `{ "error": "invalid_input" }`)        | All                                   |
| **Versioning**         | Manages API changes without breaking clients.                               | Path (`/v1/users`), headers (`Accept: application/vnd.company.v1+json`), or URL query (`?v=1`). | All |
| **Authentication**     | Secures endpoints via tokens/jwt, API keys, or OAuth.                      | Headers (`Authorization: Bearer <token>`), query params (`?api_key=...`).          | All (except public endpoints)        |
| **Rate Limiting**      | Controls API abuse by enforcing request limits.                            | Headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`), `429 Too Many Requests`.  | All                                   |
| **Caching**            | Reduces server load by serving cached responses.                           | Headers (`Cache-Control`, `ETag`), via reverse proxies (e.g., Redis/Varnish).      | `GET` (read-only)                    |
| **Idempotency**        | Ensures identical requests produce the same result.                        | Idempotency keys (e.g., `Idempotency-Key: 123`), retry-safe endpoints.            | `POST`, `PUT`, `DELETE`             |
| **Webhooks**           | Pushes events to clients in real-time.                                      | Subscription endpoints (`/webhooks`), payload validation, signed requests.          | `POST` (client), `GET` (polling)     |
| **GraphQL**            | Flexible querying via single endpoints.                                     | Root schema, `query`/`mutation` operations, resolvers.                              | `POST` (default)                     |
| **gRPC**               | High-performance RPC over HTTP/2.                                           | `.proto` definitions, binary payloads, streaming.                                  | Custom (e.g., `UnaryCall`, `Streaming`).|
| **OpenAPI/Swagger**    | Documents APIs with interactive specs.                                       | YAML/JSON files, tools like Swagger UI.                                            | N/A (meta)                           |

---
**Note:** Patterns can overlap (e.g., use **Filtering + Pagination** together).

---

### **3. Implementation Details**
#### **3.1 Core Principles**
- **RESTful Design**: Follow [REST principles](https://restfulapi.net/) (stateless, uniform interface).
- **HTTP Standards**: Leverage HTTP methods (`GET`, `POST`, etc.) and status codes semantically.
- **Idempotency**: Design `PUT/DELETE` endpoints to be idempotent where possible.
- **Versioning Strategy**: Choose **path**, **header**, or **query** versioning (avoid breaking changes).

#### **3.2 Common Pitfalls**
- **Over-Fetching**: Return only needed fields (use **Resource Fields** pattern).
- **Tight Coupling**: Avoid exposing internal entities (e.g., prefer `/orders` over `/customer_order_history`).
- **Missing HATEOAS**: Links to related resources improve discoverability (e.g., `/users/123` includes `links: { "orders": "/users/123/orders" }`).

---

### **4. Query Examples**
#### **4.1 Resource-based API**
**Endpoint:** `GET /users`
**Request:**
```http
GET /users?status=active&sort=-createdAt&page=1&limit=10
```
**Response:**
```json
{
  "data": [
    { "id": 1, "name": "Alice", "status": "active" },
    { "id": 2, "name": "Bob", "status": "active" }
  ],
  "pagination": { "page": 1, "limit": 10, "total": 20 }
}
```

#### **4.2 GraphQL Query**
**Request:**
```graphql
query {
  user(id: "123") {
    name
    orders {
      id
      total
    }
  }
}
```
**Response:**
```json
{
  "data": {
    "user": {
      "name": "Alice",
      "orders": [{ "id": "456", "total": 99.99 }]
    }
  }
}
```

#### **4.3 gRPC (Unary RPC)**
**.proto Definition:**
```protobuf
service UserService {
  rpc GetUser (GetUserRequest) returns (User);
}
```
**Request (Binary):**
```json
{ "id": "123" }
```
**Response:**
```json
{ "id": "123", "name": "Alice" }
```

#### **4.4 Webhook Subscription**
**Client Endpoint:** `POST https://client.com/webhooks`
**Server Request:**
```http
POST /webhooks HTTP/1.1
Host: client.com
Content-Type: application/json

{
  "event": "order_created",
  "data": { "order_id": "789" }
}
```
**Headers:**
- `X-Signature`: HMAC for validation.
- `Content-Type`: `application/json`.

#### **4.5 Error Response**
**Request:** `POST /orders` (malformed data)
**Response (400 Bad Request):**
```json
{
  "error": {
    "code": "invalid_input",
    "message": "Missing 'items' array",
    "details": {
      "field": "items",
      "expected": "array"
    }
  }
}
```

---

### **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Event Sourcing**        | Stores state changes as immutable events.                                       | Auditing, replayability (e.g., financial transactions).                         |
| **CQRS**                  | Separates read (`Query`) and write (`Command`) models.                           | High-throughput systems with complex queries.                                   |
| **Saga Pattern**          | Manages distributed transactions via compensating actions.                      | Microservices with eventual consistency.                                        |
| **Async API**             | Decouples producers/consumers via messaging (e.g., Kafka, RabbitMQ).           | Event-driven workflows (e.g., notifications).                                   |
| **Schema Registry**       | Centralizes validation schemas (e.g., Avro, JSON Schema).                      | Ensuring consistent data formats across services.                               |
| **API Gateway**           | Routes, rates-limits, and secures APIs centrally.                               | Managing multiple microservices with unified entry points.                       |
| **Service Mesh**          | Handles networking, observability, and security for microservices (e.g., Istio). | Complex distributed systems.                                                    |

---

### **6. Best Practices**
1. **Consistency**: Use the same pattern across your API (e.g., always paginate).
2. **Documentation**: Include OpenAPI/Swagger docs and example payloads.
3. **Testing**: Mock endpoints for unit tests (e.g., Postman/Newman).
4. **Monitoring**: Log requests/responses (e.g., Prometheus, ELK).
5. **Deprecation**: Use `/v2/deprecated` endpoints with clear migration paths.

---
**Further Reading**:
- [REST API Design Rules](https://restfulapi.net/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [gRPC Fundamentals](https://grpc.io/docs/what-is-grpc/core-concepts/)