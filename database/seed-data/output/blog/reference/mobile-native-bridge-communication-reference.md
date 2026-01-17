# **[Pattern] Native Bridge Communication Patterns Reference Guide**

---

## **Overview**
The **Native Bridge Communication Patterns** reference guide outlines how to design and implement robust communication between native applications (e.g., mobile, desktop, or IoT devices) and backend systems using bridge architectures. This pattern ensures secure, scalable, and efficient data exchange while abstracting platform-specific complexities.

Common use cases include:
- **Mobile apps** syncing with REST/WebSocket APIs
- **Desktop apps** interacting with cloud services
- **IoT devices** transmitting sensor data to backend dashboards
- **Hybrid apps** (e.g., React Native) bridging JavaScript and native modules

This guide covers core communication models, message formats, and best practices for reliability, error handling, and performance optimization.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                                                                                                                                 | **Example Data Format**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Request Message**        | A structured payload sent by the client to the server, including metadata (e.g., auth, routing) and payload data.                                                                                              | ```json { "headers": { "Content-Type": "application/json", "Auth-Token": "abc123" }, "payload": { "action": "login", "data": { "userId": "123" } } } ``` |
| **Response Message**       | Server's reply with status, payload, and error details (if any). Includes HTTP-like status codes but abstracted for cross-platform use.                                                                    | ```json { "status": "200", "payload": { "token": "xyz789" }, "errors": null } ```                          |
| **Message Headers**        | Standard fields for routing, authentication, and performance.                                                                                                                                                   | `"headers": { "deviceId": "DV-456", "timestamp": "2024-05-20T12:00:00Z", "retryCount": "0" }`         |
| **Payload Structure**      | Nested JSON object for domain-specific data. Follows [Draft 7](https://datatracker.ietf.org/doc/html/draft-ietf-json-api-media-type-07) conventions for consistency.                                        | ```json { "user": { "name": "John", "preferences": { "theme": "dark" } } } ```                          |
| **Error Payload**          | Standardized error response with `code`, `message`, and optional `details`.                                                                                                                                   | ```json { "status": "403", "errors": [ { "code": "INVALID_TOKEN", "message": "Auth failed", "details": { "field": "token" } } ] } ``` |
| **WebSocket Frame**        | Lightweight binary/text payload for real-time updates (e.g., chat apps). Includes `opcode` and `mask` for security.                                                                                                | Binary: `[Opcode(0x2), Payload("data"), MaskKey(0xAA)]`                                                      |
| **Batch Request**          | Aggregates multiple calls into one message for efficiency (e.g., bulk updates). Uses `batchId` for correlation.                                                                                               | ```json { "batchId": "B-789", "requests": [ { "action": "update", "data": { "key": "val" } } ] } ```   |
| **Retry Policy Headers**   | Tunable settings for transient failures (e.g., `maxRetries`, `backoffExponential`).                                                                                                                              | `"retryPolicy": { "maxRetries": 3, "baseDelayMs": 1000, "jitter": true }`                                   |

---

## **Query Examples**

### **1. Synchronous REST-like Request**
**Scenario**: Authenticate a user via a bridge call.
```http
POST /api/v1/bridge/communicate HTTP/1.1
Headers:
  Content-Type: application/json
  Auth-Token: xxxx
  X-Device-Type: mobile

Body:
{
  "headers": { "traceId": "TR-001" },
  "payload": {
    "action": "login",
    "data": { "username": "user1", "password": "pass123" }
  }
}
```
**Response**:
```json
{
  "status": "200",
  "payload": {
    "sessionToken": "sess_abc123",
    "expiresIn": 3600
  }
}
```

---

### **2. Asynchronous WebSocket Update**
**Scenario**: Stream live sensor data from an IoT device.
```javascript
// Client-side (e.g., mobile app)
const ws = new WebSocket("wss://backend.example.com/bridge/ws");
ws.send(JSON.stringify({
  "headers": { "deviceId": "SENSOR-001", "format": "binary" },
  "payload": {
    "type": "sensor_reading",
    "data": { "temp": 22.5, "humidity": 45 }
  }
}));
```
**Server-handled WebSocket Frame**:
```
[Opcode(0x2), MaskedPayload(JSON.stringify({...}))]
```

---

### **3. Batch Processing**
**Scenario**: Update multiple user profiles in one call.
```json
{
  "headers": { "batchId": "USERS-2024-05", "compress": true },
  "payload": {
    "actions": [
      { "op": "update", "userId": "101", "data": { "email": "new@email.com" } },
      { "op": "delete", "userId": "102" }
    ]
  }
}
```
**Response**:
```json
{
  "status": "207",
  "payload": [
    { "userId": "101", "result": "success" },
    { "userId": "102", "result": "deleted" }
  ]
}
```

---

### **4. Error Handling**
**Scenario**: Invalid payload format.
```http
POST /api/v1/bridge/communicate
Body: { "malformed": "data" }  // Missing required headers
```
**Response**:
```json
{
  "status": "400",
  "errors": [
    {
      "code": "INVALID_FORMAT",
      "message": "Headers missing or malformed",
      "details": { "expected": "headers + payload" }
    }
  ]
}
```

---

## **Implementation Details**

### **1. Core Communication Models**
| **Model**          | **Use Case**                          | **Pros**                          | **Cons**                          | **Example Tech Stack**               |
|--------------------|---------------------------------------|------------------------------------|------------------------------------|--------------------------------------|
| **REST-like**      | Idempotent requests (GET/POST).       | Standardized, tooling support.    | Latency for large payloads.       | HTTP/JSON, gRPC                     |
| **WebSocket**      | Real-time updates (e.g., chat).       | Low latency, persistent.          | Stateful, complexity.              | Socket.IO, Raw WebSockets           |
| **Message Queue**  | Decoupled processing (e.g., async DB).| Scalable, resilient.              | Higher complexity.                 | RabbitMQ, Kafka                      |
| **Binary Protocol**| High-performance (e.g., games).      | Bandwidth-efficient.               | Platform-specific code.            | Protocol Buffers, MessagePack       |

---

### **2. Performance Optimizations**
- **Compression**: Enable `gzip`/`deflate` for JSON payloads (e.g., via `Accept-Encoding` header).
- **Connection Reuse**: Persistent WebSocket/HTTP/2 connections reduce handshake overhead.
- **Batch Processing**: Aggregate requests when possible (e.g., 10 updates → 1 batch).
- **Caching**: Use `ETag` headers for conditional requests to avoid reprocessing.
- **Prioritization**: Mark critical payloads with `priority: high` in headers.

---
### **3. Security Considerations**
| **Risk**               | **Mitigation**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Unauthorized Access** | Use JWT/OAuth tokens in headers + short expiration.                            |
| **Data Tampering**     | Sign messages with HMAC or use TLS (e.g., WebSocket `Sec-WebSocket-Protocol`). |
| **Replay Attacks**     | Include `nonce` or `timestamp` in headers to prevent replay.                  |
| **DDoS**               | Rate-limit by `deviceId` + implement circuit breakers.                          |

---
### **4. Retry Policies**
| **Policy**            | **Description**                                                                 | **Example**                                  |
|-----------------------|-------------------------------------------------------------------------------|----------------------------------------------|
| **Exponential Backoff**| Increase delay between retries (e.g., 1s → 2s → 4s).                          | `baseDelayMs: 1000, maxDelayMs: 30000`      |
| **Fixed Jitter**      | Add randomness to avoid thundering herd.                                      | `jitter: true`                               |
| **Max Retries**       | Stop after `N` failures to avoid infinite loops.                              | `maxRetries: 5`                              |
| **Circuit Breaker**   | Temporarily halt retries if backend is down (e.g., 10 failures → 30s timeout).| Integrate with Hystrix/Resilience4j.         |

**Example Retry Header**:
```json
"retryPolicy": {
  "strategy": "exponential",
  "maxRetries": 3,
  "backoffMs": [1000, 2000, 4000]
}
```

---

## **Query Examples (Advanced)**
### **1. Conditional Updates**
**Use Case**: Only update user data if it hasn’t changed since `lastModified`.
```json
{
  "headers": { "ifNoneMatch": "ETag-12345" },
  "payload": {
    "action": "updateUser",
    "data": { "name": "Updated Name" },
    "conditional": { "field": "lastModified", "value": "2024-05-20T10:00:00Z" }
  }
}
```
**Response (204 No Content if unchanged)**:
```json
{ "status": "204", "payload": null }
```

---

### **2. Streaming Responses**
**Use Case**: Large file downloads (chunked transfer).
```http
GET /api/v1/bridge/stream/file?id=123
Headers:
  Accept: application/octet-stream
  Range: bytes=0-999
```
**Server Streams**:
```
[Header(Content-Type: octet-stream), Chunk1, Chunk2, ...]
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Event-Driven Architecture](https://docs.microsoft.com/en-us/azure/architecture/guide/architecture-styles/event-driven)** | Decouple producers/consumers via events (e.g., Kafka topics).               | Real-time systems (e.g., notifications).        |
| **[CQRS](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)**   | Separate read/write models for scalability.                                   | High-write-throughput systems.                  |
| **[API Gateway](https://docs.microsoft.com/en-us/azure/architecture/microservices/api-gateway)** | Centralized routing for multiple native apps.                               | Multi-tenant apps with varied client needs.      |
| **[Service Mesh](https://istio.io/latest/docs/concepts/what-is-istio/)**         | Manage service-to-service communication (e.g., mTLS, retries).               | Microservices with complex inter-service flows. |
| **[Long Polling](https://medium.com/@vikychakraborty/long-polling-vs-websockets-fb4405732d9a)** | Server holds request until data arrives (fallback to WebSockets).           | Legacy apps needing real-time but without WS.    |

---

## **Troubleshooting**
| **Issue**                     | **Debugging Steps**                                                                 |
|--------------------------------|------------------------------------------------------------------------------------|
| **Timeout Errors**            | Check `retryPolicy` headers; verify network firewalls.                              |
| **Payload Size Limits**        | Use compression or batching; increase timeout if needed.                            |
| **WebSocket Drops**           | Enable `keepAlive` pings; check for TLS misconfigurations.                         |
| **Authentication Failures**   | Validate token format; test with `curl`/`Postman`.                                  |
| **Duplicate Messages**        | Ensure `idempotencyKey` is unique per operation.                                   |

**Tools**:
- **Logging**: Structured logs with `traceId` (e.g., OpenTelemetry).
- **Monitoring**: Prometheus metrics for latency/errors (e.g., `native_bridge_request_duration`).
- **Testing**: Postman/Newman for REST; Socket.IO clients for WebSocket.

---
## **Example Code Snippets**
### **Java (Android/Kotlin)**
```kotlin
suspend fun <T> sendRequest(
    endpoint: String,
    payload: Map<String, Any>,
    retryPolicy: RetryPolicy? = null
): Response<T> {
    val client = OkHttpClient.Builder()
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .header("Auth-Token", "abc123")
                .header("Retry-Policy", retryPolicy?.toJson() ?: "{}")
                .build()
            chain.proceed(request)
        }
        .build()

    return client.newCall(
        Request.Builder()
            .url("https://backend.example.com/$endpoint")
            .post(RequestBody.create(payload.toJson(), MediaType.parse("application/json")))
            .build()
    ).execute()
}
```

### **JavaScript (React Native)**
```javascript
const sendToBridge = async (action, data) => {
  const response = await fetch('https://backend.example.com/api/v1/bridge', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Device-Type': 'mobile',
    },
    body: JSON.stringify({
      headers: { traceId: generateTraceId() },
      payload: { action, data },
    }),
  });
  return response.json();
};
```

---
## **Best Practices**
1. **Idempotency**: Design actions to be repeatable (e.g., use `idempotencyKey`).
2. **Versioning**: Prefix endpoints with `/v1` to support backward compatibility.
3. **Graceful Degradation**: Fall back to REST if WebSocket fails (e.g., add `fallbackToHttp: true`).
4. **Offline Support**: Cache responses locally (e.g., SQLite in mobile apps) and sync when online.
5. **Documentation**: Use OpenAPI/Swagger for native bridge endpoints to auto-generate SDKs.