# **[Pattern] WebSocket Validation Reference Guide**

---

## **Overview**
WebSocket Validation ensures data integrity and security by enforcing structured, consistent, and valid messages exchanged between clients and servers via WebSocket connections. This pattern applies validation rules (e.g., schema compliance, payload format, rate limiting, authentication, and real-time error responses) at both the connection and message level. It prevents malicious payloads, reduces processing overhead, and maintains system reliability—critical for real-time applications like chat, gaming, IoT telemetry, and live dashboards.

Key use cases include:
- **Real-time APIs** (e.g., WebSocket-based microservices)
- **Presence-aware systems** (e.g., multiplayer games)
- **IoT device communication** (e.g., sensor data streams)
- **Collaborative tools** (e.g., collaborative editing)

This guide covers validation strategies, schema definitions, implementation examples, and integration with complementary patterns.

---

## **Implementation Details**

### **1. Core Validation Layers**
WebSocket validation operates across three layers:

| **Layer**               | **Purpose**                                                                 | **Validation Tasks**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Connection Layer**    | Establish a secure, authenticated WebSocket handshake.                       | - TLS/SSL verification<br>- Protocol version check<br>- Rate limiting (e.g., connection storms) |
| **Handshake Validation** | Validate the initial WebSocket upgrade request (e.g., `Sec-WebSocket-Key`). | - Check for malformed headers<br>- Verify subprotocol support (e.g., `chat`, `binary`) |
| **Message Layer**       | Validate payloads in real-time during the WebSocket session.                | - **Schema validation** (e.g., JSON structure)<br>- **Data type checks**<br>- **Payload size limits**<br>- **Authentication** (e.g., JWT in custom headers) |

---

### **2. Key Validation Techniques**
| **Technique**            | **Description**                                                                      | **Tools/Libraries**                                                                 |
|--------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Schema Validation**    | Enforce structured payloads using schemas (e.g., JSON Schema, Protobuf).           | [JSON Schema](https://json-schema.org/), [Cerberus](https://docs.python-cerberus.org/), [Ajv](https://github.com/ajv-validator/ajv) |
| **Rate Limiting**        | Prevent abuse by limiting message frequency per client.                            | [Redis Rate Limiter](https://redis.io/docs/stack/enterprise/redis-enterprise-module/rem/), [Express Rate Limiter](https://github.com/express-rate-limit/express-rate-limit) |
| **Payload Sanitization** | Remove or escape malicious input (e.g., SQL injection, XSS).                       | [DOMPurify](https://github.com/cure53/DOMPurify), [OWASP Java Encoder](https://owasp.org/www-project-java-encoder/) |
| **Authentication**       | Verify sender identity (e.g., token-based or mutual TLS).                          | [JWT](https://jwt.io/), [Mutual TLS](https://en.wikipedia.org/wiki/Mutual_authentication) |
| **Real-Time Error Handling** | Send immediate feedback for invalid messages.                                     | Custom WebSocket error codes (e.g., `400 Bad Request`, `403 Forbidden`)            |

---

### **3. Schema Reference**
Define validation rules using a schema (example for JSON payloads):

| **Field**          | **Type**   | **Required** | **Validation Rules**                                   | **Description**                                  |
|--------------------|------------|--------------|-------------------------------------------------------|--------------------------------------------------|
| `operation`        | `string`   | Yes          | Enum: `create`, `update`, `delete`                   | Action type (must match a predefined set).       |
| `data`             | `object`   | Conditional* | N/A                                                     | Payload data (varies by `operation`).            |
| `data.id`          | `string`   | Yes          | Regex: `^[a-f0-9]{24}$`                               | MongoDB-style UUID (if applicable).               |
| `data.timestamp`   | `number`   | Yes          | Range: `[currentTime - 86400000, currentTime]`        | Data must be within last 24 hours.               |
| `metadata.userId`  | `string`   | Yes          | Custom: Valid JWT header claim                       | Must match authenticated user.                  |
| `metadata.signature`| `string`   | Yes          | HMAC-SHA256 verification                            | Ensures payload integrity.                       |

*Conditional: Required if `operation` is `create` or `update`.

**Example JSON Schema (Simplified):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["create", "update", "delete"]
    },
    "data": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "pattern": "^[a-f0-9]{24}$" },
        "timestamp": {
          "type": "number",
          "minimum": "1609459200000"  // 2021-01-01
        }
      },
      "required": ["id", "timestamp"]
    }
  },
  "required": ["operation", "data"]
}
```

---

## **Query Examples**
### **1. Valid WebSocket Message**
**Client → Server:**
```json
{
  "operation": "update",
  "data": {
    "id": "5f8d0d55b54764421b7156a1",
    "timestamp": 1630000000000,
    "value": 42
  },
  "metadata": {
    "userId": "auth-123",
    "signature": "abc123..."
  }
}
```
**Server Response (Success):**
```json
{
  "status": "ok",
  "operation": "update",
  "data": {
    "id": "5f8d0d55b54764421b7156a1",
    "updated": true
  }
}
```

---

### **2. Invalid Payload (Missing `id`)**
**Client → Server:**
```json
{
  "operation": "update",
  "data": {
    "timestamp": 1630000000000,
    "value": 42
  }
}
```
**Server Response (Error):**
```json
{
  "status": "error",
  "code": 400,
  "message": "Missing required field: data.id",
  "details": {
    "path": ["data", "id"],
    "expected": "string matching regex"
  }
}
```

---

### **3. Authentication Failure**
**Client → Server:**
```json
{
  "operation": "update",
  "data": {
    "id": "5f8d0d55b54764421b7156a1",
    "timestamp": 1630000000000
  },
  "metadata": {
    "userId": "invalid-token",
    "signature": "abc123..."
  }
}
```
**Server Response (Error):**
```json
{
  "status": "error",
  "code": 403,
  "message": "Invalid or expired authentication token",
  "details": {
    "userId": "invalid-token",
    "action": "update"
  }
}
```

---

### **4. Rate-Limited Client**
**Client Behavior:** Sent 100 messages in 1 second.
**Server Response (First Message):**
```json
{
  "status": "ok",
  "message": "Valid operation"
}
```
**Server Response (101st Message):**
```json
{
  "status": "error",
  "code": 429,
  "message": "Too Many Requests",
  "retryAfter": 5,  // Seconds
  "limit": 60       // Messages per minute
}
```

---

## **Related Patterns**

| **Pattern**                  | **Description**                                                                 | **Integration Points**                                                                 |
|------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **[Message Broker](https://www.enterpriseintegrationpatterns.com/patterns/messaging.html)** | Decouple WebSocket consumers/producers using a broker (e.g., RabbitMQ, Kafka). | Validate messages *before* publishing to the broker.                                    |
| **[Authentication](https://auth0.com/docs/guides/security/ensure-security/what-is-authentication)** | Secure WebSocket connections with OAuth2, JWT, or mutual TLS.                | Validate tokens in the `metadata` field or WebSocket headers (`Sec-WebSocket-Protocol`). |
| **[Circuit Breaker](https://microservices.io/patterns/data/circuit-breaker.html)** | Prevent cascading failures during validation storms.                          | Use a circuit breaker to throttle validation servers during DDoS.                      |
| **[Compression](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers#Compression)** | Reduce payload size for efficient validation.                                  | Validate *after* decompression (e.g., `permessage-deflate`).                           |
| **[Idempotency](https://blog.groot.io/idempotency-key-pattern/)**                    | Ensure duplicate messages don’t cause side effects.                          | Add an `idempotencyKey` field to payloads and cache responses.                          |
| **[Schema Registry](https://confluent.io/product/schema-registry/)**             | Centralize schemas for all WebSocket services.                               | Reference schemas in validation tools (e.g., Avro, Protobuf).                         |

---

## **Best Practices**
1. **Validate Early**: Reject malformed messages at the connection or first message layer to minimize processing overhead.
2. **Use Idempotency**: Prevent duplicate operations by requiring clients to include an `idempotencyKey`.
3. **Log Violations**: Track validation failures (e.g., rate limits, schema errors) for analytics.
4. **Leverage Standards**:
   - [RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455) (WebSocket Basics)
   - [RFC 7231](https://datatracker.ietf.org/doc/html/rfc7231) (HTTP Status Codes for Errors)
5. **Benchmark**: Profile validation performance to avoid latency spikes during high traffic.

---
**See also:**
- [WebSocket Security Checklist](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Security_checklist)
- [OWASP WebSocket Vulnerabilities](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)