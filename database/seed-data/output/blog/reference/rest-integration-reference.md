# **[Pattern] REST Integration – Reference Guide**

---

## **Overview**
The **REST Integration** pattern standardizes how systems communicate over HTTP using RESTful APIs, ensuring loose coupling, scalability, and machine-readable data exchanges. This pattern formalizes best practices for designing, consuming, and maintaining RESTful endpoints, authentication, error handling, and versioning. It applies to microservices, third-party integrations, and internal system interactions, emphasizing stateless requests, resource-oriented URLs, and HTTP methods (GET, POST, PUT, DELETE). Proper implementation ensures interoperability, performance, and maintainability across distributed systems.

---

## **Implementation Details**

### **Core Principles**
1. **Resource-Oriented Design**
   Represent data as resources accessible via URLs (e.g., `/users/{id}`).
2. **Statelessness**
   No client/server session state; each request contains all necessary information.
3. **Standard HTTP Methods**
   - `GET`: Retrieve a resource.
   - `POST`: Create a resource.
   - `PUT/PATCH`: Update a resource.
   - `DELETE`: Remove a resource.
4. **Idempotency**
   Safe methods (`GET`, `PUT`, `DELETE`) should not alter data unexpectedly. `POST` should not modify resources if repeated.
5. **Semantic URLs**
   Use nouns (e.g., `/orders`) and avoid verbs (e.g., `/createOrder`).
6. **Content Negotiation**
   Support multiple formats (JSON, XML) via `Accept` headers.
7. **Versioning**
   Use URL paths (e.g., `/v1/users`) or custom headers (`X-API-Version`) to manage API versions.

---

## **Schema Reference**
| **Component**          | **Definition**                                                                                     | **Example**                          | **Required** |
|------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------|--------------|
| **Endpoint URI**       | Resource path following REST conventions.                                                           | `/api/v1/users`                      | Yes          |
| **HTTP Method**        | Specifies the operation (GET, POST, etc.).                                                        | `POST`                               | Yes          |
| **Headers**            | Metadata for request/response (e.g., `Content-Type`, `Authorization`).                          | `Accept: application/json`            | Optional*    |
| **Query Parameters**   | Key-value pairs for filtering/pagination (e.g., `?limit=10`).                                     | `?status=active&sort=date`           | Optional*    |
| **Request Body**       | Payload for `POST/PUT` (JSON/XML).                                                                | `{ "name": "John", "email": "john@example.com" }` | Optional*    |
| **Response Status**    | HTTP status code (e.g., `200 OK`, `404 Not Found`).                                              | `200 OK`                             | Yes          |
| **Response Body**      | Data returned for `GET`/`POST` (JSON/XML).                                                         | `{ "id": 123, "status": "active" }`  | Optional*    |
| **Authentication**     | Security mechanism (e.g., `Bearer <token>`, API keys).                                            | `Authorization: Bearer abc123`         | Yes*         |

*Varies by use case; check API documentation.

---

## **Query Examples**
### **1. Retrieve a User (GET)**
```http
GET /api/v1/users/123
Headers:
  Accept: application/json
```
**Response (200 OK):**
```json
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com"
}
```

### **2. Create a User (POST)**
```http
POST /api/v1/users
Headers:
  Content-Type: application/json
  Authorization: Bearer abc123
Body:
{
  "name": "Bob",
  "email": "bob@example.com"
}
```
**Response (201 Created):**
```json
{
  "id": 456,
  "name": "Bob",
  "email": "bob@example.com"
}
```

### **3. Filter Users with Pagination (GET)**
```http
GET /api/v1/users?active=true&limit=5&offset=10
Headers:
  Accept: application/json
```
**Response (200 OK):**
```json
{
  "users": [
    { "id": 7, "name": "Charlie" },
    { "id": 8, "name": "Dana" }
  ],
  "total": 20,
  "limit": 5,
  "offset": 10
}
```

### **4. Update User (PATCH)**
```http
PATCH /api/v1/users/123
Headers:
  Content-Type: application/json
  Authorization: Bearer abc123
Body:
{
  "name": "Alice Smith"
}
```
**Response (200 OK):**
```json
{
  "id": 123,
  "name": "Alice Smith",
  "email": "alice@example.com"
}
```

### **5. Error Handling (400 Bad Request)**
```http
POST /api/v1/users
Headers:
  Content-Type: application/json
Body:
{
  "email": "invalid-email"  // Invalid format
}
```
**Response (400 Bad Request):**
```json
{
  "error": "Invalid email format",
  "code": "BAD_REQUEST_EMAIL"
}
```

---

## **Best Practices**
1. **Versioning**
   Use URL paths (`/v1/resource`) or `X-API-Version` header to avoid breaking changes.
   Example: `/v1/users` (deprecated) → `/v2/users`.

2. **Rate Limiting**
   Implement `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers to prevent abuse.

3. **Caching**
   Use `Cache-Control` headers for responses (e.g., `max-age=3600` for GET requests).

4. **Pagination**
   Standardize with `limit`/`offset` or `cursor`-based pagination for large datasets.

5. **Idempotency Keys**
   For `POST` requests, include an `Idempotency-Key` to ensure retries don’t duplicate actions.

6. **Logging**
   Log request/response metadata (IP, timestamp, headers) for debugging.

7. **Security**
   - Use **HTTPS** for all communications.
   - Validate all inputs to prevent injection attacks.
   - Restrict sensitive endpoints to specific roles (e.g., `Authorization: Bearer admin_token`).

8. **OpenAPI/Swagger**
   Document APIs using OpenAPI 3.0 for auto-generated SDKs and UI tools.

---

## **Related Patterns**
1. **[GraphQL Integration]**
   For flexible, client-driven data fetching when REST’s fixed endpoints are less efficient.
2. **[Event-Driven Integration]**
   Useful for asynchronous workflows where REST polling is inefficient (e.g., payments, notifications).
3. **[Gateway Pattern]**
   Centralizes REST endpoints for routing, load balancing, and security, reducing client-side complexity.
4. **[Service Mesh (e.g., Istio, Linkerd)**
   Manages REST traffic, retries, circuit breaking, and observability in microservices.
5. **[Service Contracts]**
   Formalize REST API agreements between teams (e.g., using OpenAPI or AsyncAPI).
6. **[Retry & Circuit Breaker]**
   Implement exponential backoff for transient failures in REST calls (e.g., using Polly in .NET).
7. **[API Gateway (e.g., Kong, Apigee]**
   Aggregates multiple REST APIs, adds auth, rate limiting, and transforms requests/responses.

---
## **Troubleshooting**
| **Issue**               | **Root Cause**                          | **Solution**                                                                 |
|-------------------------|----------------------------------------|------------------------------------------------------------------------------|
| **401 Unauthorized**     | Missing/invalid auth token.           | Verify `Authorization` header or token expiry.                            |
| **403 Forbidden**        | Insufficient permissions.              | Check role-based access control (RBAC) or scope claims.                     |
| **404 Not Found**        | Incorrect URL or resource deleted.     | Validate endpoint path and resource existence.                             |
| **500 Server Error**     | Backend failure.                       | Enable logging and trace requests to the server.                           |
| **Slow Responses**       | Large payloads or DB bottlenecks.      | Implement pagination, caching, or optimize queries.                         |
| **CORS Errors**          | Missing `Access-Control-Allow-Origin`. | Add CORS headers to the server response.                                   |

---
## **Tools & Libraries**
| **Purpose**               | **Tools/Libraries**                                                                 |
|---------------------------|------------------------------------------------------------------------------------|
| **Client Libraries**      | Axios (JavaScript), Retrofit (Android), `HttpClient` (Java), `requests` (Python). |
| **Proxy/Load Balancing**  | NGINX, HAProxy, Envoy.                                                           |
| **Monitoring**            | Prometheus, Grafana, OpenTelemetry.                                            |
| **API Design**            | OpenAPI Generator, Swagger UI, Postman.                                           |
| **Security**              | OAuth2/OIDC (Auth0, Keycloak), JWT, API Gateway filters.                        |

---
## **When to Avoid REST**
- **Real-time requirements**: Use WebSockets or Server-Sent Events (SSE).
- **Complex queries**: GraphQL reduces over-fetching and under-fetching.
- **Eventual consistency needed**: Consider event-driven architectures (e.g., Kafka).