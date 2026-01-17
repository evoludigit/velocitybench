# **[Pattern] Monolith Standards Reference Guide**

---

## **Overview**
The **Monolith Standards** pattern standardizes the design and behavior of monolithic microservices (or *service monoliths*), ensuring consistency in architecture, communication, data handling, and error management. Unlike traditional monoliths, this pattern decouples service boundaries and enforces standards for integration, API contracts, and operational consistency. It is ideal for teams transitioning from traditional monoliths or consolidating loosely coupled microservices into a cohesive but scalable architecture.

Key benefits include:
- **Predictability**: Uniform structure reduces cognitive load for developers.
- **Maintainability**: Shared conventions simplify refactoring.
- **Scalability**: Independent services can scale based on demand without rigid coupling.
- **Tooling**: Centralized standards enable automation (e.g., CI/CD, observability).

This guide covers schema requirements, query conventions, and integration patterns with complementary architectures (e.g., event-driven systems).

---

## **1. Schema Reference**
All services adhering to Monolith Standards must conform to the following schema conventions.

| **Component**          | **Description**                                                                 | **Requirements**                                                                                                                                                                                                 | **Example**                                                                                     |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Service Naming**     | Unique, camelCased identifier for the service                                  | - Must start with a noun (e.g., `user`, `order`).<br>- Prefix with domain (e.g., `auth`, `inventory`).<br>- Avoid underscores or hyphens.                                                                                    | `auth.user.profile`, `inventory.stock`                                                           |
| **API Contract**       | REST/OpenAPI specification for endpoints                                        | - Versioned (e.g., `/v1/users`).<br>- Standardized response formats (JSON).<br>- Rate-limiting headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).<br>- OpenAPI 3.0 schema validation.                     | `/v1/users/{id}` → `{ "id": "123", "name": "Alice", "email": "alice@example.com" }`            |
| **Request/Response**   | Data payload structure                                                        | - Use **PascalCase** for objects (e.g., `User`, `OrderItem`).<br>- Arrays as `[Element]` (e.g., `[User]`).<br>- Nullable fields marked with `?` (e.g., `email?: string`).<br>- Pagination: `offset`, `limit`. | `{ "users": [{ "id": "1", "name": "Bob" }], "totalCount": 2 }`                                  |
| **Error Handling**     | Standardized error responses                                                  | - HTTP status codes (4xx/5xx).<br>- Structured payload: `{ "error": { "code": "string", "message": "string", "details": "optional" } }`.<br>- Avoid generic `500` errors.                                    | `404 → { "error": { "code": "NOT_FOUND", "message": "User not found" } }`                       |
| **Database Schema**    | Database table/domain naming and relationships                                 | - **Snake_case** for tables (e.g., `user_profiles`).<br>- Foreign keys prefixed with `fk_` (e.g., `fk_user_id`).<br>- Timestamps: `created_at`, `updated_at`.<br>- Avoid redundant columns (e.g., `full_name` vs. `first_name + last_name`). | `users: { id (PK), email (UNIQUE), created_at }`                                                |
| **Event Schema**       | Event-driven communication (Kafka/RabbitMQ)                                    | - Schema: `{ "event": "string", "data": {}, "timestamp": "ISO8601" }`.<br>- Event names: `UserCreated`, `OrderShipped`.<br>- Data must be serializable (avoid circular refs).                                | `{ "event": "UserCreated", "data": { "id": "456", "email": "eve@example.com" } }`              |
| **Configuration**      | Environment variables and secrets                                             | - Prefix with `SERVICE_` (e.g., `SERVICE_USER_DB_HOST`).<br>- Secrets managed via Vault/secrets manager.<br>- Override precedence: `dev < staging < prod`.<br>- Avoid hardcoding.                                   | `SERVICE_AUTH_JWT_SECRET=...`, `DB_MAX_CONNECTIONS=50`                                          |
| **Logging**            | Structured logging format                                                     | - JSON format: `{ "level": "string", "service": "string", "message": "string", "metadata": {} }`.<br>- Include trace IDs for distributed tracing.<br>- Log levels: `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`.       | `{"level": "INFO", "service": "auth", "message": "User logged in", "metadata": { "userId": "1" }}` |
| **Security**           | Authentication/authorization standards                                         | - JWT/OAuth2 for APIs.<br>- Role-based access control (RBAC).<br>- Input validation (e.g., `zod.js`, `joi`).<br>- CORS restricted to approved domains.<br>- Rate limiting enforced.                               | `Bearer <token>` in `Authorization` header                                                |
| **Metrics**            | Observability metrics                                                         | - Prometheus metrics: `<namespace>_<subsystem>_<operation>[<dimension>]`.<br>- Counters: `requests_total{method="GET", path="/users"}`.<br>- Histograms: `request_latency_seconds{service="auth"}.`                    | `http_requests_duration_seconds{service="inventory", path="/stock", status="200"}`             |
| **Idempotency**        | Handling duplicate requests                                                  | - Idempotency keys for `POST/PUT` (e.g., UUID-based headers).<br>- Retry policies: exponential backoff.<br>- Dead-letter queues for failed events.                                                          | `Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000`                                      |

---

## **2. Query Examples**
### **REST API Examples**
#### **Retrieve User Profile**
```http
GET /v1/auth/users/123
Headers:
  Accept: application/json
  Authorization: Bearer xxxxx.yyyyy.zzzzz
```
**Response (200 OK):**
```json
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com",
  "createdAt": "2023-01-01T00:00:00Z",
  "roles": ["ADMIN", "USER"]
}
```

#### **Create Order with Idempotency**
```http
POST /v1/inventory/orders
Headers:
  Content-Type: application/json
  Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000
Body:
{
  "customerId": "987",
  "items": [
    { "productId": "101", "quantity": 2 }
  ]
}
```
**Response (201 Created):**
```json
{
  "orderId": "abc123",
  "status": "PENDING",
  "createdAt": "2023-05-15T14:30:00Z"
}
```

#### **Error Response (400 Bad Request)**
```http
POST /v1/auth/login
Body:
{
  "email": "invalid@",
  "password": "123"
}
```
**Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVALID_EMAIL",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "expected": "user@example.com"
    }
  }
}
```

---

### **Event-Driven Example**
**OrderShipped Event**
```json
{
  "event": "OrderShipped",
  "data": {
    "orderId": "abc123",
    "shipmentId": "xyz789",
    "trackingUrl": "https://tracker.example.com/abc123",
    "status": "SHIPPED"
  },
  "timestamp": "2023-05-15T15:00:00.000Z"
}
```

---

## **3. Implementation Details**
### **Key Concepts**
1. **Service Boundaries**
   - Define boundaries using **Domain-Driven Design (DDD)**. Each service owns its data (e.g., `auth` manages users; `inventory` manages stock).
   - Avoid **distributed transactions** (use Saga pattern for cross-service workflows).

2. **API Gateway**
   - Centralize routing, authentication, and rate limiting.
   - Tools: **Kong**, **Apigee**, or **AWS API Gateway**.
   - Example routing:
     ```
     /auth → auth-service
     /inventory → inventory-service
     /shippings → shipping-service
     ```

3. **Database Per Service**
   - Each service has its own database (avoid shared DBs).
   - Use **connection pooling** (e.g., PgBouncer for PostgreSQL).
   - **Read replicas** for high-traffic services (e.g., `auth-read`).

4. **Eventual Consistency**
   - Use **events** (Kafka, RabbitMQ) for async communication.
   - Example workflow:
     1. `inventory` publishes `OrderItemReserved`.
     2. `shipping` consumes event → creates `Shipment`.
     3. `auth` updates user balance via `OrderProcessed`.

5. **Schema Registry**
   - Centralized schema storage (e.g., **Confluent Schema Registry**, **Avro/Protobuf**).
   - Enforce backward/forward compatibility.

6. **CI/CD Pipeline**
   - **Automated testing**: Unit, integration, and contract tests (e.g., **Pact.io**).
   - **Canary deployments**: Roll out changes gradually (e.g., 5% → 100%).
   - **Rollback strategy**: Automated if health checks fail.

---

### **Configuration Management**
| **Environment** | **Database Host**       | **JWT Secret**               | **Feature Flags**                     |
|-----------------|--------------------------|-------------------------------|----------------------------------------|
| `development`   | `db-dev.example.com`     | `dev-jwt-secret`              | `{"new_auth_flow": false}`            |
| `staging`       | `db-staging.example.com` | `staging-jwt-secret`          | `{"new_auth_flow": true}`             |
| `production`    | `db-prod.example.com`    | `{VAULT_SECRET:/jwt/prod}`    | `{"new_auth_flow": true}` (default)   |

---

## **4. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                                                 | **Example Integration**                          |
|---------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|--------------------------------------------------|
| **Saga Pattern**          | Manage long-running transactions across services                             | Replace distributed transactions with compensating actions.                     | `Order → Inventory → Shipping` workflow.         |
| **CQRS**                  | Separate read/write models for performance                                 | High-read throughput (e.g., analytics dashboards).                                | `users-read` (optimized for queries).           |
| **Event Sourcing**        | Store state changes as immutable events                                   | Audit trails, time-travel debugging.                                             | `UserCreated`, `UserEmailUpdated`.               |
| **API Gateway**           | Centralized API management                                                | Single entry point for clients.                                                 | Route `/users` to `auth-service`.               |
| **Circuit Breaker**       | Fail fast and recover from service failures                                | Resilient microservices (e.g., `auth-service` calling `payment-service`).       | `Hystrix` or `Resilience4j`.                    |
| **Service Mesh**          | Manage service-to-service communication                                   | Advanced traffic routing, mTLS, observability.                                    | **Istio** or **Linkerd**.                        |
| **Domain Events**         | Decouple services via domain-specific events                                | Event-driven architectures (e.g., `OrderShipped` → `EmailService`).             | Kafka topics for events.                        |

---

## **5. Anti-Patterns to Avoid**
1. **Tight Coupling**
   - ❌ Direct DB calls between services.
   - ✅ Use event sourcing or API contracts.

2. **Shared Database**
   - ❌ Single DB for multiple services.
   - ✅ Database per service (even if schema overlaps).

3. **Ignoring Idempotency**
   - ❌ Non-idempotent `POST` endpoints (e.g., payments).
   - ✅ Enforce idempotency keys.

4. **Overloading Events**
   - ❌ Publishing events for every data change.
   - ✅ Only emit **domain-specific** events (e.g., `OrderShipped`, not `StockUpdated`).

5. **Inconsistent Logging**
   - ❌ Ad-hoc log formats.
   - ✅ Structured logs with `service`, `level`, and trace IDs.

6. **No Schema Versioning**
   - ❌ Hardcoding schemas.
   - ✅ Use **Avro/Protobuf** with schema registry.

---

## **Tools & Technologies**
| **Category**       | **Tools**                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **API Gateway**    | Kong, Apigee, AWS API Gateway, NGINX                                        |
| **Event Bus**      | Kafka, RabbitMQ, AWS SNS/SQS, NATS                                         |
| **Schema Registry**| Confluent Schema Registry, Schema Registry (Apache Avro)                  |
| **Observability**  | Prometheus, Grafana, Jaeger, OpenTelemetry                                 |
| **Security**       | OAuth2 (Auth0), JWT (jsonwebtoken), Vault (HashiCorp)                     |
| **Testing**        | Pact.io (contract testing), Postman, Jest                                 |
| **CI/CD**          | ArgoCD, Jenkins, GitHub Actions, Spinnaker                                 |
| **Service Mesh**   | Istio, Linkerd, Consul                                                       |

---

## **References**
1. **Books**:
   - *Microservices Patterns* by Chris Richardson.
   - *Release It!* by Michael Nygard (resilience patterns).
2. **Standards**:
   - [OpenAPI Spec](https://spec.openapis.org/).
   - [JWT Best Practices](https://auth0.com/docs/get-started/token-reference).
3. **Templates**:
   - [Monolith Standards GitHub Repo](https://github.com/your-org/monolith-standards).