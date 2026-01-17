---
# **[Pattern Name] Messaging Guidelines Reference Guide**
*Version: 1.2*
*Last Updated: [Date]*
*Status: Stable*

---

## **1. Overview**
The **Messaging Guidelines** pattern ensures consistent, structured, and reliable communication within distributed systems by defining standardized formats, rules, and best practices for sending, parsing, and responding to messages. It enforces clarity, error handling, and versioning to mitigate ambiguity and scalability bottlenecks. This pattern is critical for microservices architectures, event-driven systems, and cross-team integrations where loosely coupled components exchange data.

Key objectives:
- **Standardize message formats** (schema validation, serialization).
- **Ensure idempotency and retries** with unique message IDs and acknowledgments.
- **Define response handling** (timing, retries, fallback strategies).
- **Support versioning** (backward/forward compatibility).

---

## **2. Schema Reference**
All messages adhere to the following schema types. Use **JSON Schema** or **Protocol Buffers** for validation.

| **Field**          | **Type**       | **Description**                                                                                     | **Validation Rules**                                                                 | **Example Value**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|---------------------------------------|
| **message_id**     | `string`       | Unique identifier for tracking (UUID or UUIDv4).                                                   | Must match regex `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`. | `"550e8400-e29b-41d4-a716-446655440000"` |
| **timestamp**      | `timestamp`    | RFC 3339 ISO 8601 format (UTC).                                                                    | Required; must be in `YYYY-MM-DDTHH:mm:ss.sssZ`.                                      | `"2023-10-05T14:30:00.000Z"`            |
| **version**        | `string`       | Semantic version (e.g., `1.2.0`).                                                                   | Must follow **SemVer** (v1.x.x or v2.x.x).                                            | `"2.1.0"`                              |
| **type**           | `string`       | Message category (e.g., `order.created`, `payment.failed`).                                          | Listed in **Message Types** registry.                                                | `"payment.failed"`                    |
| **body**           | `object`       | Payload specific to `type` (schema defined per message type).                                       | Validated against **Type-Specific Schema**.                                           | `{ "order_id": "12345", "status": "failed" }` |
| **metadata**       | `object`       | Optional context (e.g., `source_ip`, `correlation_id`).                                             | Keys must be lowercase kebab-case.                                                    | `{ "source_ip": "192.168.1.1" }`       |
| **acknowledgment** | `object`       | Response flag (consumer use only).                                                                 | Keys: `received`, `processed`, `error` (bool values).                                  | `{ "received": true, "processed": false }` |

---

### **2.1 Message Types Registry**
Define message types in a centralized registry (e.g., API gateway or config service). Example entries:

| **Type**           | **Schema Path**           | **Description**                          | **Required Fields**                  |
|--------------------|---------------------------|------------------------------------------|---------------------------------------|
| `order.created`    | `schemas/order_created.json` | Triggered when a new order is placed.  | `order_id`, `user_id`, `total`       |
| `payment.failed`   | `schemas/payment_failed.json` | Payment processing error.           | `payment_id`, `error_code`, `retry_at`|
| `inventory.updated`| `schemas/inventory_updated.json` | Stock level changes.               | `product_id`, `quantity`, `timestamp` |

---

## **3. Implementation Details**
### **3.1 Serialization**
- Use **JSON** for human-readability (default) or **Protocol Buffers (protobuf)** for performance-critical systems.
- Encode binary payloads (e.g., images) in **Base64**.

### **3.2 Message Lifecycle**
1. **Produce**:
   - Assign a `message_id` and `timestamp`.
   - Validate against `type`-specific schema.
   - Enqueue to broker (e.g., Kafka, RabbitMQ) or HTTP endpoint.

   ```python
   message = {
       "message_id": generate_uuid(),
       "timestamp": datetime.utcnow().isoformat() + "Z",
       "version": "2.1.0",
       "type": "order.created",
       "body": {"order_id": "123", "user_id": "456"},
       "metadata": {"source": "webapp"}
   }
   validate_schema(message, "order.created")  # Using jsonschema or protobuf
   broker.publish(message)
   ```

2. **Consume**:
   - Acknowledge receipt (`acknowledgment.received = true`).
   - Process and update `acknowledgment.processed`.
   - Retry failed messages (max 3 attempts; exponential backoff).

   ```java
   @KafkaListener(topics = "orders")
   public void handleOrder(Message<byte[]> message) {
       Message<?> deserialized = serializer.deserialize(message.value());
       deserialized.getAcknowledgments().setReceived(true);
       // Process logic (e.g., DB update)
       deserialized.getAcknowledgments().setProcessed(true);
       broker.commit();  // Acknowledge success
   }
   ```

3. **Idempotency**:
   - Use `message_id` to deduplicate (e.g., retrying the same message).
   - Store processed messages in a database table with columns:
     ```sql
     CREATE TABLE processed_messages (
         message_id VARCHAR(36) PRIMARY KEY,
         type VARCHAR(100),
         processed_at TIMESTAMP,
         status VARCHAR(20)  -- e.g., "success", "failed"
     );
     ```

4. **Versioning**:
   - **Backward Compatibility**: Add optional fields (e.g., `v2.0` includes `shipping_address`).
   - **Breaking Changes**: Deprecate old versions with a transition period (e.g., `1.0` → `1.1`).
   - Example schema evolution:
     ```json
     // v1.0
     { "order_id": "123" }

     // v2.0 (adds optional 'shipping')
     { "order_id": "123", "shipping": { "address": "..." } }
     ```

---

### **3.3 Error Handling**
| **Scenario**               | **Action**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| Invalid schema             | Return `400 Bad Request` with `error_details` in `body`.                   |
| Missing `message_id`       | Reject with `422 Unprocessable Entity`.                                      |
| Broker timeout             | Retry 3 times; escalate to dead-letter queue if persistent.               |
| Duplicate `message_id`     | Ignore or return `409 Conflict`.                                             |
| Version unsupported        | Return `410 Gone` with upgrade instructions.                                 |

---

## **4. Query Examples**
### **4.1 Producing a Message (HTTP API)**
**Request**:
```http
POST /api/messages
Content-Type: application/json

{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2023-10-05T14:30:00.000Z",
  "version": "2.1.0",
  "type": "payment.failed",
  "body": {
    "payment_id": "pay_abc123",
    "error_code": "GATEWAY_TIMEOUT"
  }
}
```

**Response (Success)**:
```http
201 Created
{
  "status": "accepted",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "broker_name": "kafka"
}
```

**Response (Error)**:
```http
400 Bad Request
{
  "error": "validation_failed",
  "details": {
    "field": "body.error_code",
    "message": "must match pattern '^[A-Z_]+$'"
  }
}
```

---

### **4.2 Querying Processed Messages (gRPC)**
**Request**:
```protobuf
service MessageService {
  rpc GetMessageStatus (GetStatusRequest) returns (GetStatusResponse);
}

message GetStatusRequest {
  string message_id = 1;
}

message GetStatusResponse {
  enum Status { SUCCESS = 0; FAILED = 1; PENDING = 2; }
  Status status = 1;
  string processed_at = 2;  // ISO 8601 timestamp
}
```

**Example Call**:
```bash
grpcurl -plaintext localhost:50051 MessageService.GetMessageStatus '{
  "message_id": "550e8400-e29b-41d4-a716-446655440000"
}'
```
**Response**:
```json
{
  "status": "SUCCESS",
  "processed_at": "2023-10-05T14:35:00.000Z"
}
```

---

## **5. Related Patterns**
| **Pattern Name**               | **Relationship**                                                                 | **When to Use**                                                                 |
|---------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Command Query Responsibility Segregation (CQRS)** | Messages often feed read models in CQRS systems.                                  | When separating write/read paths improves scalability.                          |
| **Event Sourcing**              | Messages can double as events in an event-sourced architecture.                  | For audit trails and temporal queries.                                           |
| **Retry as a Service (RaAS)**   | Complements idempotency with automated retries.                                    | For transient failures (e.g., network issues).                                  |
| **Circuit Breaker**             | Protects consumers from cascading failures by halting retries.                    | When downstream services are unreliable.                                        |
| **Schema Registry (Confluent Schema Registry)** | Centralizes message schemas for validation.                                       | In Kafka/RabbitMQ-based systems.                                                |
| **Saga Pattern**                | Uses messages to coordinate long-running transactions across services.           | For distributed transactions (e.g., order processing).                          |

---

## **6. Anti-Patterns**
- **Ad-hoc Messages**: Avoid unstructured payloads (e.g., raw strings).
  *✖️* `{"data": "user:123 logged in"}`
  *✔️* Use a schema: `{"type": "user.logged_in", "body": {"user_id": "123"}}`

- **No Versioning**: Hardcoding versions breaks compatibility.
  *✖️* `version: "1"` (hidden upgrade path).
  *✔️* Always include `version` field.

- **Ignoring Retries**: Unlimited retries cause resource exhaustion.
  *✖️* Infinite loop on `503 Service Unavailable`.
  *✔️* Max 3 retries with exponential backoff.

- **Tight Coupling**: Message types should not depend on internal service details.
  *✖️* `type: "user.db_updated"` (tests DB directly).
  *✔️* `type: "user.profile_changed"`.

---

## **7. Tools & Libraries**
| **Tool**                          | **Purpose**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| **JSON Schema Validator**         | Validate payloads (e.g., [Ajv](https://github.com/ajv-validator/ajv)).       |
| **Protocol Buffers**              | High-performance serialization (e.g., [protobuf-go](https://github.com/golang/protobuf)). |
| **Kafka/RabbitMQ**                | Message brokers for pub/sub patterns.                                       |
| **OpenTelemetry**                 | Trace message flows across services.                                         |
| **Postman/Newman**                | Test message APIs (e.g., mock brokers).                                     |

---
**Appendices**
- [A] **Example Schema Definitions** (JSON Schema snippets).
- [B] **Dead-Letter Queue Configuration** (Kafka/RabbitMQ).
- [C] **Monitoring Metrics** (Latency, error rates).