# **[Pattern] Microservices Conventions Reference Guide**

---

## **Overview**
Microservices Conventions define **standardized patterns, naming conventions, and best practices** to ensure consistency, scalability, and maintainability across a distributed system. Unlike monolithic applications, microservices often introduce **inconsistent naming, divergent data formats, or conflicting APIs**, leading to **technical debt and operational inefficiencies**.

This guide outlines **key conventions** for:
- **Service Naming & Discovery**
- **API Design & Versioning**
- **Data & Schema Standards**
- **Logging & Monitoring**
- **Security & Authentication**
- **Deployment & CI/CD**

Adopting these conventions reduces **context-switching overhead**, minimizes **integration errors**, and improves **developer productivity**.

---

## **Schema Reference**
The following table summarizes **mandatory vs. optional conventions** across key microservice aspects.

| **Category**          | **Convention**                          | **Mandatory?** | **Example**                                                                 | **Notes**                                                                 |
|-----------------------|-----------------------------------------|---------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Service Naming**    | Service names use lowerCase             | ✅ Yes         | `user-service`, `order-service`                                             | Avoid camelCase or PascalCase to prevent ambiguity in DNS/hostnames.       |
|                       | Domain prefix (e.g., `auth-`, `payment-`)| Optional      | `auth-service`, `inventory-service`                                           | Helps group related services (e.g., all payment-related services).         |
|                       | Avoid generic names                     | ✅ Yes         | ❌ `service-a`, `backend-1` → ✅ `cart-service`                               | Descriptive names reduce debugging time.                                  |
| **API Design**        | RESTful endpoints use `/v1/` prefix    | ✅ Yes         | `GET /api/v1/users/{id}`                                                    | Enables backward compatibility during versioning.                      |
|                       | Query params for filtering              | ✅ Yes         | `GET /api/v1/products?category=electronics&price>50`                          | Prefer over nested paths for dynamic queries.                           |
|                       | Pagination (`?page=1&limit=10`)         | ✅ Yes         |                                                                             | Required for large datasets.                                             |
|                       | Consistent error responses              | ✅ Yes         | `{ "error": { "code": "404", "message": "User not found" }}`                | Standard JSON schema for errors (see [Error Codes](#error-codes)).       |
| **Data & Schema**     | JSON-based payloads (no XML)            | ✅ Yes         |                                                                             | Use `application/json` for all requests/responses.                       |
|                       | CamelCase for JSON keys                 | ✅ Yes         | `{ "userId": 123, "firstName": "John" }`                                     | Consistent with most programming languages.                             |
|                       | Schema registry (e.g., Avro, Protobuf) | Optional      |                                                                             | Enforces backward compatibility for event-driven services.               |
| **Logging**           | Structured logs (JSON)                  | ✅ Yes         | `{ "timestamp": "2024-05-20T12:00:00Z", "level": "INFO", "service": "user" }` | Tools like ELK or Datadog parse structured logs.                        |
|                       | Correlation ID for requests             | ✅ Yes         | `X-Correlation-ID: abc123`                                                   | Tracks requests across distributed services.                             |
| **Security**          | JWT for stateless auth                  | ✅ Yes         | `Authorization: Bearer <token>`                                              | Prefer short-lived tokens (e.g., 15-30 min).                            |
|                       | OAuth2 for third-party auth             | Optional      |                                                                             | Use for social logins (e.g., Google, GitHub).                            |
| **Deployment**        | Immutable Docker images                  | ✅ Yes         |                                                                             | Avoid runtime modifications (e.g., `docker run -v`).                      |
|                       | Rollback strategy (blue-green)          | Optional      |                                                                             | Critical for high-availability services.                                 |
| **CI/CD**             | GitHub Actions / GitLab CI              | ✅ Yes         |                                                                             | Standardize pipeline definitions.                                        |
|                       | Automated security scanning             | ✅ Yes         |                                                                             | Tools: Trivy, Snyk, OWASP ZAP.                                          |

---

## **Implementation Details**

### **1. Service Naming & Discovery**
Microservices should follow a **predictable naming scheme** to simplify service discovery (e.g., via **Consul, Eureka, or Kubernetes DNS**).

| **Pattern**               | **Example**               | **Purpose**                                                                 |
|---------------------------|---------------------------|-----------------------------------------------------------------------------|
| **Domain + Resource**     | `payment-service`         | Clearly indicates service purpose.                                           |
| **Avoid Numbers/Suffixes**| ❌ `service-1` → ✅ `cart`| Numbers complicate scaling and DNS resolution.                           |
| **Consistent Suffixes**   | `-service`, `-api`        | Optional but improves readability.                                           |

**Example Discovery Entry (Consul):**
```yaml
payment-service:
  id: payment-service
  name: payment-service
  address: payment-service.default.svc.cluster.local
  port: 8080
```

---

### **2. API Design & Versioning**
APIs should follow **REST principles** with explicit versioning to avoid breaking changes.

#### **Versioning Strategies**
| **Strategy**       | **Example**               | **Use Case**                                  |
|--------------------|---------------------------|-----------------------------------------------|
| **URI Prefix**     | `/api/v1/orders`          | Most common; supports backward compatibility.|
| **Header**         | `Accept: application/vnd.api.v1+json` | Flexible but less intuitive.               |
| **Query Param**    | `/orders?version=1`       | Rarely used; can cause SEO issues.          |

**Example API Response:**
```json
{
  "data": {
    "id": "123",
    "name": "Premium Plan",
    "price": 9.99
  },
  "meta": {
    "version": "v1"
  }
}
```

#### **Error Codes**
Standardize HTTP status codes with custom headers for consistency.

| **Code** | **Status**       | **Example Header**                     | **Description**                          |
|----------|------------------|----------------------------------------|------------------------------------------|
| `400`    | Bad Request      | `{ "error": "invalid_request" }`      | Client-side validation failure.         |
| `401`    | Unauthorized     | `{ "error": "missing_auth_token" }`   | Missing/invalid JWT.                     |
| `404`    | Not Found        | `{ "error": "resource_not_found" }`   | Requested resource does not exist.       |
| `429`    | Too Many Requests| `{ "retry-after": 30 }`               | Rate limiting enforced.                  |

---

### **3. Data & Schema Standards**
Use **schema validation** (e.g., JSON Schema, OpenAPI/Swagger) to enforce consistency.

**Example JSON Schema (`user.schema.json`):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "email": { "type": "string", "format": "email" },
    "roles": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["email"]
}
```

**Validation Tools:**
- **OpenAPI/GitHub Actions** → Auto-enforce schemas.
- **Avro/Protobuf** → For event-driven systems (e.g., Kafka).

---

### **4. Logging & Correlation IDs**
Logs should include:
- **Timestamp** (ISO 8601)
- **Service name**
- **Request ID** (for tracing)
- **Log level** (`INFO`, `ERROR`, `DEBUG`)

**Example Log Entry:**
```json
{
  "timestamp": "2024-05-20T12:00:00.123Z",
  "service": "order-service",
  "level": "INFO",
  "requestId": "abc123-xyz456",
  "message": "Order processed",
  "userId": "user-789"
}
```

**Tools:**
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Datadog** / **Loki** (for distributed tracing)

---

### **5. Security Best Practices**
| **Aspect**               | **Convention**                          | **Example**                                  |
|--------------------------|----------------------------------------|----------------------------------------------|
| **Authentication**       | JWT with short expiry (15-30 min)      | `Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`|
| **Authorization**        | Role-based access control (RBAC)      | `{ "roles": ["admin", "user"] }`            |
| **Rate Limiting**        | Redis-based throttling (e.g., 100 req/min) | `X-RateLimit-Limit: 100`                   |
| **Input Validation**     | Use libraries (e.g., Zod, Joi)        | Validate always (never trust client input). |

**Example JWT Payload:**
```json
{
  "sub": "user-123",
  "name": "Alice",
  "roles": ["admin"],
  "exp": 1716233600  // Expiry timestamp
}
```

---

### **6. Deployment & CI/CD**
**Mandatory Pipeline Stages:**
1. **Linting & Unit Tests** → `npm test` / `pytest`
2. **Build & Dockerize** → `docker build -t user-service:v1.`
3. **Security Scan** → `trivy image user-service:v1.`
4. **Deploy to Staging** → Blue-green or canary.
5. **Rollback Mechanism** → Automated on health check failures.

**Example GitHub Actions Workflow:**
```yaml
name: CI/CD Pipeline
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install && npm test
      - run: docker build -t user-service:$GITHUB_SHA .
      - run: trivy image user-service:$GITHUB_SHA
```

---

## **Query Examples**
### **1. Fetching User Data (REST)**
```http
GET /api/v1/users/123
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
  X-Correlation-ID: abc123

Response:
HTTP/1.1 200 OK
{
  "data": {
    "id": "123",
    "name": "Alice",
    "email": "alice@example.com"
  }
}
```

### **2. Creating an Order (gRPC)**
**Protobuf Definition (`order.proto`):**
```protobuf
service OrderService {
  rpc CreateOrder (CreateOrderRequest) returns (OrderResponse);
}
```

**Request (`CreateOrderRequest`):**
```json
{
  "userId": "user-123",
  "items": [
    { "productId": "prod-456", "quantity": 2 }
  ]
}
```

**Response (`OrderResponse`):**
```json
{
  "orderId": "order-789",
  "status": "CREATED",
  "total": 39.98
}
```

### **3. Event-Driven (Kafka)**
**Topic:** `user.updated`
**Message Schema (Avro):**
```json
{
  "schemaId": 1,
  "payload": {
    "userId": "user-123",
    "action": "UPDATED_EMAIL",
    "newEmail": "new@example.com"
  }
}
```

---

## **Related Patterns**
To further improve microservices architecture, consider:
1. **[Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architecture.html)**
   - Use **Kafka, RabbitMQ, or NATS** for async communication.
2. **[CQRS](https://microservices.io/patterns/data/cqrs.html)**
   - Separate read/write models for scalability.
3. **[Saga Pattern](https://microservices.io/patterns/data/saga.html)**
   - Manage distributed transactions via long-running workflows.
4. **[API Gateway](https://microservices.io/patterns/apigateway.html)**
   - Centralized routing (e.g., **Kong, Apigee, or AWS API Gateway**).
5. **[Service Mesh (Istio/Linkerd)](https://istio.io/latest/docs/concepts/what-is-istio/)**
   - Handles **traffic management, security, and monitoring** at the service level.

---

## **Further Reading**
- **[12-Factor App](https://12factor.net/)** – Best practices for modern apps.
- **[OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)** – API design standards.
- **[Cloud Native Computing Foundation (CNCF)](https://www.cncf.io/)** – Tools for microservices (Kubernetes, Prometheus).

---
**Last Updated:** `2024-05-20`
**Contributors:** [Your Name]