# **[Pattern] Microservices Validation – Reference Guide**

---

## **Overview**
The **Microservices Validation pattern** ensures that interactions between distributed services are reliable, coherent, and secure. Unlike monolithic applications, microservices often communicate asynchronously via APIs, event-driven systems, or direct calls (e.g., HTTP/gRPC). Validation in this context prevents data inconsistencies, enforces business rules, and mitigates risks like:

- **Schema drift** (incompatible message formats across service versions)
- **Invalid payloads** (malformed or unauthorized requests)
- **Corrupted state** (e.g., missing dependencies or circular references in event streams)
- **Latency-induced errors** (timeouts or stale data in distributed transactions)

This pattern combines **pre-validation** (at the service boundary), **post-validation** (after processing), and **runtime validation** (e.g., event sourcing or idempotency) to maintain system integrity. It complements patterns like **API Gateway**, **CQRS**, and **Saga** by adding a layer of enforceable correctness.

---

## **Implementation Details**
### **Core Principles**
| Principle               | Description                                                                                                                                                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Self-Validation**     | Each microservice validates its own inputs/outputs (e.g., using JSON Schema, OpenAPI, or Protobuf).                                                                                                      |
| **Gateway Validation**  | API Gateways or Edge Services validate requests/responses before forwarding them (e.g., OAuth tokens, payload size limits, or rate limits).                                                            |
| **Event Validation**    | Event producers and consumers validate events against a schema (e.g., Avro, Protocol Buffers) to prevent schema evolution issues.                                                                |
| **Runtime Checks**      | Post-processing validation (e.g., checking transactional integrity or referential constraints) via **Sagas** or **compensating transactions**.                                               |
| **Idempotency Keys**    | Deduping duplicate requests (e.g., retries) using keys like `X-Request-ID` or transaction IDs.                                                                                                       |
| **Observability**       | Logs, metrics, and traces (e.g., with OpenTelemetry) to detect validation failures early.                                                                                                            |

---

### **Validation Layers**
Validation occurs at multiple stages of a microservice interaction:

| Layer               | Validation Scope                                                                 | Tools/Techniques                                                                 |
|---------------------|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Client-Side**     | Library-level checks (e.g., SDKs validate before sending requests).               | TypeScript **Zod**, Python **Pydantic**, Java **JsonSchemaValidator**.            |
| **API Gateway**     | Request/response headers, payload formats, and authentication.                    | Kong, Apigee, AWS API Gateway (OpenAPI validation).                              |
| **Service Boundary**| Request parsing, schema compliance, and business rule enforcement.               | Spring Validator, Express.js **Joi**, gRPC **Schema Validation**.                 |
| **Database Layer**  | Row-level constraints (e.g., NOT NULL, foreign keys) or application-level checks.| PostgreSQL **Constraints**, MongoDB **Validation Rules**.                         |
| **Event Stream**    | Schema evolution, event sourcing consistency, and duplicate event handling.     | Kafka **Schema Registry**, Debezium.                                              |
| **Post-Processing** | Cross-service validation (e.g., checking a payment was successful before confirming). | Sagas, Kafka Streams, Event Sourcing **Event Sinks**.                           |

---

## **Schema Reference**
Validation schemas define the structure and constraints of requests, responses, and events. Below are common schema formats:

### **1. JSON Schema (for REST/gRPC)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OrderCreateRequest",
  "type": "object",
  "properties": {
    "customerId": { "type": "string", "format": "uuid" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "productId": { "type": "string" },
          "quantity": { "type": "integer", "minimum": 1 }
        },
        "required": ["productId", "quantity"]
      }
    }
  },
  "required": ["customerId", "items"]
}
```

### **2. Protobuf (for gRPC)**
```proto
syntax = "proto3";

message OrderItem {
  string product_id = 1;
  int32 quantity = 2;
}

message OrderCreateRequest {
  string customer_id = 1;  // UUID format enforced by server
  repeated OrderItem items = 2;
}
```

### **3. Event Schema (Kafka/Avro)**
```avsc
{
  "name": "OrderCreatedEvent",
  "namespace": "com.example.orders",
  "type": "record",
  "fields": [
    {"name": "orderId", "type": "string"},
    {"name": "customerId", "type": ["null", "string"]},  // Optional
    {"name": "items", "type": {"type": "array", "items": "OrderItem"}}
  ]
}
```

---
## **Query Examples**
### **1. Validating a REST Request (Express.js + Joi)**
```javascript
const Joi = require('joi');

const schema = Joi.object({
  customerId: Joi.string().uuid().required(),
  items: Joi.array()
    .items(
      Joi.object({
        productId: Joi.string().required(),
        quantity: Joi.number().integer().min(1).required()
      })
    )
    .min(1).required()
});

app.post('/orders', async (req, res) => {
  const { error, value } = schema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details[0].message });
  // Proceed if validated
});
```

### **2. gRPC Server-Side Validation (Go)**
```go
import (
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func (s *OrderService) CreateOrder(ctx context.Context, req *pb.OrderCreateRequest) (*pb.Order, error) {
	if req.CustomerId == "" {
		return nil, status.Error(codes.InvalidArgument, "customer_id is required")
	}
	if len(req.Items) == 0 {
		return nil, status.Error(codes.InvalidArgument, "items cannot be empty")
	}
	// Business logic...
}
```

### **3. Event Validation (Kafka + Schema Registry)**
```bash
# Validate a produced event against the schema registry
kafka-avro-console-producer \
  --broker localhost:9092 \
  --topic order_events \
  --property schema.registry.url=http://localhost:8081 \
  --property value.schema='{
    "type": "record",
    "name": "OrderCreated",
    "fields": [{"name": "id", "type": "string"}]
  }'

# Produce a message (will fail if schema mismatches)
echo '{"id": "123"}' | jql -r '{"id": "$(id)"}' | kafka-console-producer \
  --broker localhost:9092 \
  --topic order_events \
  --property parse.key=true \
  --property key.separator=: \
  --property schema.registry.url=http://localhost:8081 \
  --property value.schema='{"type":"string"}'
```

---

## **Error Handling Patterns**
| Scenario                     | Solution                                                                                     | Example Response                                                                 |
|------------------------------|---------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Invalid Payload**          | Return HTTP `400 Bad Request` with validation details.                                         | `{"error": "Missing required field 'customerId'"}`                              |
| **Schema Mismatch**          | Reject event with `400` or `415 Unsupported Media Type`.                                     | `{"error": "Schema mismatch: expected v1, got v2"}`                             |
| **Transaction Validation**   | Use `409 Conflict` for duplicate operations (e.g., retries).                                  | `{"error": "Order already processed: 123"}`                                    |
| **Incompatible Service**     | Return `426 Upgrade Required` if the client must upgrade to support the request.            | `{"error": "Upgrade to API v2 required"}`                                       |
| **Idempotency Conflict**     | Log duplicate request and return `200` with `Idempotency-Key` in headers.                  | `{"message": "Already processed"}` + `X-Idempotency-Key: abc123`                 |

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                       |
|-----------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **[API Gateway](https://microservices.io/patterns/apigateway.html)** | Centralizes request routing, authentication, and validation.                                   | When multiple clients (mobile/web) access microservices.                          |
| **[CQRS](https://microservices.io/patterns/data/cqrs.html)**      | Separates read/write models; validation rules apply per model.                                  | For high-throughput systems with complex queries.                                |
| **[Saga](https://microservices.io/patterns/data/saga.html)**     | Manages distributed transactions via compensating actions; validation ensures atomic steps.    | For long-running workflows (e.g., order fulfillment).                            |
| **[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)** | Stores state as a sequence of events; validation enforces event integrity.              | For audit trails and replayable state changes.                                    |
| **[Polly Pattern](https://microservices.io/patterns/resiliency/polly.html)** | Retries failed requests; validation ensures idempotency.                                    | For handling transient failures in external services.                            |
| **[BFF (Backend-for-Frontend)](https://microservices.io/patterns/apigateway/bfp.html)** | Aggregates validation logic for specific clients (e.g., mobile vs. web).                 | When client-specific rules exist (e.g., field hiding).                           |

---

## **Best Practices**
1. **Schema Evolution**:
   - Use **backward-compatible changes** (e.g., add optional fields) and **deprecation warnings** for breaking changes.
   - Example: Add a `v1` and `v2` schema side-by-side during transition.

2. **Performance**:
   - Validate early (e.g., at the gateway) to avoid wasting server resources.
   - Cache schemas (e.g., Protobuf schemas) to reduce parsing overhead.

3. **Security**:
   - Never trust client-provided schemas. Always validate against a **central schema registry**.
   - Use **JWT/OAuth** to validate client identity before allowing schema access.

4. **Testing**:
   - Write **contract tests** (e.g., with Pact) to verify schema compatibility between services.
   - Use **mutation testing** (e.g., Stryker) to ensure validation logic covers edge cases.

5. **Observability**:
   - Instrument validation failures with:
     - `validation_error` metric (per schema/type).
     - Logs including `request_id`, `schema_version`, and `invalid_fields`.
   - Example Prometheus query:
     ```promql
     sum(rate(validation_errors_total[5m])) by (schema_name)
     ```

6. **Idempotency**:
   - Assign a unique `Idempotency-Key` header to deduplicate retries.
   - Store keys in a cache (e.g., Redis) with a TTL (e.g., 24 hours).

---

## **Anti-Patterns**
| Anti-Pattern               | Problem                                                                                     | Fix                                                                                  |
|----------------------------|---------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **No Client-Side Validation** | Clients send invalid data; server validates late, wasting resources.                       | Use SDKs/library validation (e.g., `Zod`, `Pydantic`) to fail fast.               |
| **Overly Strict Validation** | Business rules are enforced at the database level, coupling services to storage.          | Move validation to the application layer for flexibility.                          |
| **Schema Registry Bypass**  | Services ignore the schema registry, leading to incompatible messages.                      | Enforce schema validation via API Gateway or client libraries.                     |
| **Silent Failures**        | Validation errors are logged but not surfaced to clients, hiding bugs.                     | Return HTTP `4xx` responses or event `NACK`s with detailed errors.                  |
| **Version-Tagging Without Deprecation** | Schema changes are labeled `v2` without warning, breaking producers.                    | Use **feature flags** or **deprecation headers** to signal upcoming changes.       |

---
## **Tools & Libraries**
| Category               | Tools                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------|
| **Schema Validation**  | [JSON Schema](https://json-schema.org/), [Protobuf](https://developers.google.com/protocol-buffers), [Avro](https://avro.apache.org/) |
| **REST Validation**    | Express.js **Joi**, Spring **Validator**, Django **DRF**                                  |
| **gRPC Validation**    | [gogoproto](https://github.com/gogo/protobuf) (Go), [protobuf-java](https://github.com/protocolbuffers/protobuf-java) |
| **Event Validation**   | [Kafka Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html), [Debezium](https://debezium.io/) |
| **Testing**            | [Pact](https://docs.pact.io/), [Stryker](https://stryker-mutator.io/) (mutation testing)  |
| **Observability**      | OpenTelemetry, Prometheus, Jaeger                                                            |

---
## **Further Reading**
- [JSON Schema Specification](https://json-schema.org/)
- [gRPC Validation Best Practices](https://grpc.io/blog/schema-validation/)
- [Event-Driven Microservices Validation](https://www.infoq.com/articles/event-driven-microservices/)
- [Schema Registry Patterns](https://www.confluent.io/blog/schema-registry-best-practices/)