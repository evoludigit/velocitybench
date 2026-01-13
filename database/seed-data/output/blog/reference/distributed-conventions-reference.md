# **[Pattern] Distributed Conventions Reference Guide**

## **Overview**
The **Distributed Conventions** pattern standardizes naming, formatting, and structural rules across distributed systems to ensure consistency, reduce ambiguity, and simplify interoperability between services, APIs, and data stores. This pattern is critical in microservices architectures, event-driven systems, and multi-team environments where collaboration is essential. By enforcing conventions for resource naming, path design, metadata schemas, event formats, and logging structures, teams can minimize context-switching, automate tooling (e.g., API gateways, monitoring dashboards), and streamline developer onboarding. This guide outlines core principles, schema requirements, implementation best practices, and query examples to help teams apply distributed conventions effectively.

---

## **Key Concepts**
Distributed conventions address consistency challenges by defining rules across **six primary domains**:

| **Domain**               | **Purpose**                                                                 | **Example Scope**                          |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **Resource Naming**      | Standardizes identity for services, endpoints, and data entities.         | Service names (`order-service`, not `OrderSystem`), database tables (`users_v2`). |
| **API/Endpoint Conventions** | Ensures predictable request/response structures and query syntax.    | RESTful path prefixes (`/v1/orders`), pagination (`?page=2&limit=10`). |
| **Data Schema Conventions** | Unifies data structures (JSON, Protobuf) and metadata conventions.      | JSON keys (`createdAt` instead of `DateCreated`), timestamp formats (`ISO 8601`). |
| **Event-Driven Conventions** | Normalizes event schemas, naming, and routing for event-driven systems. | Event types (`OrderCreatedEvent` vs. `EventOrderCreated`), schema evolution. |
| **Logging & Monitoring** | Defines structured logging formats and metric naming conventions.      | Log keys (`{ "service": "auth", "level": "INFO" }`), metric prefixes (`app.auth.login.count`). |
| **Configuration & Secrets** | Standardizes how environments, secrets, and settings are exposed.     | Environment variables (`DB_HOST=postgres`), secrets naming (`AWS_ACCESS_KEY`). |

---

## **Schema Reference**
Below are standardized schemas for each domain. Replace placeholders (`{X}`) with team-specific values.

### **1. Resource Naming Conventions**
| **Category**          | **Rule**                                                                 | **Example**                     | **Anti-Example**              |
|-----------------------|--------------------------------------------------------------------------|---------------------------------|--------------------------------|
| **Service Names**     | Lowercase, kebab-case, no special chars (max 30 chars).                   | `payment-service`               | `PaymentsSystemV2`, `user_auth`. |
| **Endpoint Paths**    | `/v{major_version}/{resource}.{action}` (REST) or `{event_type}` (gRPC/Events). | `/v1/orders/{orderId}/items`    | `/api/orders/listItems`, `/users`. |
| **Database Tables**   | Plural lowercase, underscore-separated, versioned if needed.           | `customer_orders_v2`            | `CustomerOrder`, `cust_orders`. |
| **Schema Files**      | `.avro`, `.proto`, or `.json` extensions; name matches service/resource. | `order.avro`                     | `OrderSchema.json`, `schema_v1`. |

---

### **2. API/Endpoint Conventions**
| **Rule**                          | **Requirement**                                                                 | **Example**                          |
|-----------------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Versioning**                   | Include major/minor versions in paths/headers.                                | `/v1/orders`, `Accept: application/vnd.order-service.v1+json` |
| **Query Parameters**             | Use `snake_case` for simple queries; `camelCase` for complex objects.       | `?status=active&page=1`              | `?pageNum=1&IsActive=true`.     |
| **Pagination**                   | `page` (1-based) and `limit` (max 1000).                                    | `?page=2&limit=50`                   |
| **Status Codes**                 | Follow HTTP spec + custom codes prefixed with `42X` (e.g., `429` for throttling). | `420 Too Many Requests`               |
| **Headers**                      | Standardized headers: `X-Correlation-ID`, `X-Request-ID`.                    | `X-Correlation-ID: abc123`           |

---

### **3. Data Schema Conventions**
| **Rule**                          | **Requirement**                                                                 | **Example (JSON)**                  |
|-----------------------------------|-------------------------------------------------------------------------------|-------------------------------------|
| **Timestamp Fields**              | Always `createdAt`, `updatedAt`; format `ISO 8601` (UTC).                     | `"createdAt": "2023-10-01T12:00:00Z"` |
| **Boolean Fields**                | `false`/`true` (lowercase) or `Y/N`.                                        | `"isActive": false`                 |
| **Enums/Static Fields**          | Use `snake_case` for enum values.                                            | `"status": "pending"`               |
| **Array Fields**                  | Nested objects in arrays must be consistent (e.g., always include `id`).     | `[{ "id": "1", "name": "Item A" }]`  |
| **Id Fields**                     | UUIDv4 for new systems; auto-incrementing integers for legacy.                | `"id": "550e8400-e29b-41d4-a716-446655440000"` |

**Example Schema (JSON):**
```json
{
  "orders": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "userId": { "type": "string" },
        "items": {
          "type": "array",
          "items": { "type": "object" }
        },
        "status": { "enum": ["pending", "shipped", "cancelled"] },
        "createdAt": { "type": "string", "format": "date-time" }
      }
    }
  }
}
```

---

### **4. Event-Driven Conventions**
| **Rule**                          | **Requirement**                                                                 | **Example**                          |
|-----------------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Event Naming**                 | `PascalCase` for event types; suffix `-Event` (e.g., `OrderCreatedEvent`).    | `PaymentProcessedEvent`              |
| **Event Schema**                 | Include `eventId`, `timestamp`, `source`, `type`.                              | `{ "type": "OrderCreatedEvent", "source": "order-service" }` |
| **Event Versioning**             | Add `version` field (e.g., `"version": "1.0"`).                              | `"version": "2.0"`                   |
| **Routing Keys**                 | Use snake_case for topics (e.g., `order.created`).                             | `{ "routingKey": "order.created" }` |

**Example Event (Protobuf):**
```protobuf
message EventHeader {
  string eventId = 1;
  string timestamp = 2; // ISO 8601
  string source = 3;    // e.g., "order-service"
  string type = 4;      // e.g., "OrderCreatedEvent"
  string version = 5;   // e.g., "1.0"
}

message OrderCreatedEvent {
  EventHeader header = 1;
  string orderId = 2;
  User user = 3;
}
```

---

### **5. Logging & Monitoring**
| **Rule**                          | **Requirement**                                                                 | **Example (JSON Log)**               |
|-----------------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Log Structure**                | Key-value pairs; required fields: `{service, level, traceId, timestamp}`.   | `{ "service": "auth", "level": "ERROR", "traceId": "abc123" }` |
| **Severity Levels**              | `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`.                            | `"level": "WARN"`                   |
| **Metric Prefixes**              | `app.{service}.{component}` (e.g., `app.auth.login.count`).                 | `app.payment.processed.success`     |
| **Correlation IDs**              | Include `X-Correlation-ID` in logs/metrics for tracing.                        | `"correlationId": "xyz789"`          |

**Example Metric (Prometheus):**
```
app_payment_processed_total{status="success"} 42
app_payment_processed_duration_seconds{status="failure"} 0.123
```

---

### **6. Configuration & Secrets**
| **Rule**                          | **Requirement**                                                                 | **Example**                          |
|-----------------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Environment Variables**         | Prefix with `APP_` or `{SERVICE}_`; use `_` for multi-word keys.            | `APP_DB_HOST`, `PAYMENT_SERVICE_URL` |
| **Secrets Management**           | Use vault namespaces (e.g., `payment-service/keys/access-key`).               | `secret: "payment-service/keys/stripe-key"` |
| **Config File Naming**           | `config.{environment}.{service}.yaml` (e.g., `config-prod-payment.yaml`).   | `config-dev-order.yaml`              |

---

## **Query Examples**
### **1. REST API Queries**
**Retrieve orders with pagination:**
```
GET /v1/orders?page=3&limit=20&status=shipped
Headers:
  Accept: application/vnd.order-service.v1+json
```

**Filter orders by user:**
```json
POST /v1/orders/search
{
  "query": {
    "filter": {
      "userId": "user-123",
      "status": "pending"
    },
    "sort": "-createdAt"
  }
}
```

---

### **2. Event-Driven Queries**
**Consume `OrderCreatedEvent`:**
```json
{
  "headers": {
    "eventType": "OrderCreatedEvent",
    "source": "order-service",
    "version": "1.0"
  },
  "body": {
    "orderId": "ord-456",
    "userId": "user-789",
    "items": [...]
  }
}
```

**Route event to a sink:**
```
TOPIC: order.created
KEY: order-456
MESSAGE:
  {
    "event": { ... },
    "metadata": {
      "processedAt": "2023-10-01T12:00:00Z"
    }
  }
```

---

### **3. Schema Validation Queries**
**Validate an order object against the schema:**
```bash
# Using JSON Schema
jq --argjson schema '{"$ref": "#/definitions/order"}' 'validate($schema)' input.json
```

**Validate an event against Protobuf schema:**
```bash
protoc --validate --include_imports order_events.proto order_created_event.json
```

---

## **Implementation Best Practices**
1. **Tooling Automation**:
   - Use OpenAPI/Swagger to generate clients from standardized API specs.
   - Enforce schema validation with tools like **JSON Schema**, **Protobuf**, or **Apache Avro**.
   - Deploy a **convention validator** (e.g., GitHub Action) to catch violations early.

2. **Documentation**:
   - Maintain a **conventions repository** (e.g., `CONVENTIONS.md`) with examples and rationale.
   - Link to schemas/APIs in service documentation (e.g., Confluence/Markdown).

3. **Evolution**:
   - **Backward compatibility**: Prefix new fields (e.g., `v2_status`) during schema changes.
   - **Deprecation**: Use `deprecated: true` in schemas/events for flagging removal.

4. **Exemptions**:
   - Document exceptions (e.g., legacy systems) in the conventions repo.
   - Require approval for deviations via a **Change Board**.

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **[API Versioning]**      | Manage evolving APIs without breaking clients.                             | When services require backward-incompatible changes. |
| **[Event Sourcing]**      | Store state changes as a sequence of events.                              | For auditability and replayability.      |
| **[Service Mesh]**        | Manage service-to-service communication (e.g., retries, circuit breaking). | In complex distributed systems.         |
| **[Schema Registry]**     | Centralize schema versioning and evolution.                                | For event-driven or multi-team data pipelines. |
| **[OpenAPI/Swagger]**     | Document REST APIs interactively.                                          | When exposing public or internal APIs.  |
| **[Context Propagation]** | Track requests across services (e.g., traces, correlation IDs).            | For debugging distributed transactions. |

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                          |
|-------------------------------------|-------------------------------------------------------------------------------|---------------------------------------|
| **Ambiguous API paths**            | Paths conflict between services (e.g., `/users`).                           | Use namespaces (e.g., `/auth/users`).  |
| **Schema evolution conflicts**     | New fields break backward-compatible consumers.                             | Use optional fields or versioned schemas. |
| **Missing correlation IDs**        | Hard to trace requests across services.                                      | Enforce `X-Correlation-ID` in all APIs.|
| **Inconsistent logging formats**   | Logs are unstructured or service-specific.                                  | Adopt structured logging (e.g., JSON). |

---

## **Further Reading**
- [REST API Design Best Practices](https://restfulapi.net/)
- [Event-Driven Architecture Patterns](https://event-driven.io/)
- [OpenAPI Specification](https://spec.openapis.org/)
- [JSON Schema](https://json-schema.org/)