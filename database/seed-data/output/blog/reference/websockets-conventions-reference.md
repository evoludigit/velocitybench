# **[Pattern] Websockets Conventions Reference Guide**

---
## **Overview**
The **Websockets Conventions** pattern defines standardized message structures, protocols, and best practices for real-time bidirectional communication via WebSocket connections. This guide ensures consistency across frontend and backend implementations, reducing complexity in building scalable, maintainable, and interoperable real-time applications (e.g., chat systems, live updates, gaming, or collaborative tools).

Key principles include:
- **Structured message schemas** for clarity and validation.
- **Opinionated fields** (e.g., `action`, `data`, `metadata`) to separate intent from payload.
- **Error handling conventions** for robust client-server communication.
- **Connection lifecycle** management (handshake, reconnection, cleanup).

This pattern is designed for **Node.js/Express**, **Python (FastAPI/Django Channels)**, and **Java (Spring WebSocket)** but can be adapted to other frameworks.

---

## **1. Core Concepts**
### **1.1 WebSocket Message Structure**
All messages follow this schema (see [Schema Reference](#schema-reference)):

```
{
  "action": "string",    // Required: Defines intent (e.g., "subscribe", "event")
  "data": "object/array", // Required: Payload (varies by `action`)
  "metadata": "object",  // Optional: Context (e.g., timestamps, auth tokens)
  "error": "object",     // Optional: Error details (if applicable)
  "requestId": "string"  // Optional: Correlation ID for acknowledgments
}
```

### **1.2 Connection Lifecycle**
| Phase          | Description                                                                 | Example Events                      |
|----------------|-----------------------------------------------------------------------------|-------------------------------------|
| **Handshake**  | Client initiates connection; server validates and assigns a session ID.   | `connect`, `authenticate`           |
| **Active**     | Bidirectional communication (messages can be sent/received).                | `event`, `command`, `response`      |
| **Disconnect** | Clean termination or forced closure.                                        | `disconnect`, `heartbeat_timeout`   |

### **1.3 Message Types**
| Type          | Description                                                                 | Example `action` Values             |
|---------------|-----------------------------------------------------------------------------|--------------------------------------|
| **Command**   | Client→Server: Requests action (e.g., data fetch, subscription).           | `subscribe`, `unsubscribe`, `send`   |
| **Event**     | Server→Client: Pushes updates (e.g., notifications, state changes).       | `update`, `notification`, `status`   |
| **Response**  | Server→Client: Acknowledges commands with results or errors.             | `success`, `error`                  |
| **Heartbeat** | Keeps connection alive (optional).                                         | `ping`, `pong`                      |

---

## **2. Schema Reference**
Below is the **JSON Schema** for Websockets messages. Use this to validate incoming/outgoing payloads.

| **Field**     | **Type**       | **Required** | **Description**                                                                 | **Constraints/Examples**                                                                 |
|---------------|----------------|--------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `action`      | `string`       | ✅ Yes        | Defines the message intent.                                                      | `subscribe`, `event:user_typing`, `ping`                                                 |
| `data`        | `object/array` | ✅ Yes        | Payload data (schema varies by `action`).                                         | `{ "userId": "123", "message": "Hello" }`                                               |
| `metadata`    | `object`       | ❌ No         | Supplemental context (e.g., timestamps, auth).                                  | `{ "timestamp": "2023-10-01T12:00:00Z", "sessionId": "abc123" }`                     |
| `error`       | `object`       | ❌ No         | Error details (only if `action` fails).                                          | `{ "code": 400, "message": "Invalid payload", "details": {...} }`                       |
| `requestId`   | `string`       | ❌ No         | Unique ID for correlating requests/responses.                                     | `"req_abc456"` (UUID or auto-incremented)                                               |
| `timestamp`   | `string`       | ❌ No         | ISO 8601 timestamp (metadata or error field).                                     | `"2023-10-01T12:00:00.000Z"`                                                             |

---

## **3. Query Examples**
### **3.1 Client-Side Requests**
#### **Subscribe to Updates**
```json
{
  "action": "subscribe",
  "data": {
    "channel": "user_messages",
    "userId": "456",
    "filters": { "type": ["message", "reaction"] }
  },
  "metadata": {
    "sessionId": "def789",
    "timestamp": "2023-10-01T12:00:00.000Z"
  }
}
```
**Server Response (Success):**
```json
{
  "action": "acknowledge",
  "data": { "status": "subscribed" },
  "metadata": { "timestamp": "2023-10-01T12:00:01.000Z" }
}
```

#### **Send a Message**
```json
{
  "action": "send",
  "data": {
    "channel": "chat_room_1",
    "content": "Hello, team!",
    "senderId": "123",
    "timestamp": "2023-10-01T12:01:00.000Z"
  }
}
```

---
### **3.2 Server-Side Events**
#### **Broadcast Notification**
```json
{
  "action": "event",
  "data": {
    "type": "notification",
    "title": "New Comment",
    "content": "User XYZ commented on your post.",
    "recipientId": "789"
  },
  "metadata": {
    "timestamp": "2023-10-01T12:02:00.000Z",
    "senderId": "admin_1"
  }
}
```

#### **Error Response**
```json
{
  "action": "error",
  "error": {
    "code": 403,
    "message": "Permission denied",
    "details": {
      "missingRole": "admin",
      "requiredFields": ["token"]
    }
  },
  "requestId": "req_abc456"
}
```

---
### **3.3 Heartbeat (Optional)**
#### **Client Ping**
```json
{
  "action": "ping",
  "metadata": { "timestamp": "2023-10-01T12:05:00.000Z" }
}
```
**Server Pong:**
```json
{
  "action": "pong",
  "metadata": { "timestamp": "2023-10-01T12:05:00.500Z" }
}
```

---

## **4. Implementation Guidelines**
### **4.1 Validation**
Use **JSON Schema** (e.g., [Ajv](https://github.com/ajv-validator/ajv)) or framework-specific validators (e.g., FastAPI’s `Pydantic`).
**Example Schema (simplified):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["action", "data"],
  "properties": {
    "action": { "type": "string", "pattern": "^[a-z_]+$" },
    "error": {
      "type": "object",
      "properties": {
        "code": { "type": "integer", "minimum": 100, "maximum": 599 }
      }
    }
  }
}
```

### **4.2 Security**
- **Authenticate early**: Validate `metadata.authToken` in the handshake phase.
- **Rate limiting**: Enforce limits on `subscribe`/`send` actions per `sessionId`.
- **Encryption**: Use **WSS** (WebSocket Secure) for production.

### **4.3 Reconnection**
- **Exponential backoff**: Clients should retry connections with delays (e.g., 1s → 2s → 4s).
- **Session persistence**: Server should preserve state (e.g., Redis) for reconnected clients.

---

## **5. Error Handling Conventions**
| **Error Code** | **Description**               | **Example `error` Field**                                                                 |
|----------------|-------------------------------|------------------------------------------------------------------------------------------|
| `400`          | Invalid payload               | `{ "code": 400, "message": "Missing `data.channel`" }`                                   |
| `401`          | Unauthorized                  | `{ "code": 401, "message": "Invalid token" }`                                            |
| `403`          | Forbidden                     | `{ "code": 403, "message": "Insufficient permissions", "missingRole": "moderator" }`     |
| `404`          | Resource not found            | `{ "code": 404, "message": "Channel `chat_room_1` not found" }`                         |
| `429`          | Rate limited                  | `{ "code": 429, "message": "Too many requests", "retryAfter": 30 }`                     |
| `500`          | Server error                  | `{ "code": 500, "message": "Database connection failed" }`                              |

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Pub/Sub Model](#)**   | Decouples producers/consumers using topics/channels.                        | Real-time notifications, event-driven architectures.                           |
| **[Request-Response](#)**| Synchronous WebSocket messages for RPC-like interactions.                   | API-like queries (e.g., `getUserProfile`).                                    |
| **[Throttling](#)**      | Limits message frequency to prevent abuse.                                  | High-traffic apps (e.g., stock tickers).                                      |
| **[Presence System](#)** | Tracks connected users/sessions in a room.                                | Chat apps, gaming lobbies.                                                    |
| **[Message Retry](#)**   | Automatic retries for failed messages (with backoff).                       | Unstable networks (mobile apps).                                               |

---

## **7. Frameworks & Libraries**
| **Language/Framework** | **Library**                     | **Key Features**                                                                 |
|-------------------------|---------------------------------|---------------------------------------------------------------------------------|
| Node.js                 | `ws`, `Socket.IO`              | WebSocket server/client, rooms, namespaces, reconnection logic.               |
| Python                  | `FastAPI (WebSockets)`, `Django Channels` | Async support, ORM integration, authentication.                               |
| Java                    | `Spring WebSocket`, `Vert.x`    | STOMP over WebSockets, message brokers (e.g., RabbitMQ).                      |
| Go                      | `gorilla/websocket`            | Coroutine-friendly, built-in ping/pong support.                              |

---
## **8. Best Practices**
1. **Idempotency**: Use `requestId` to deduplicate duplicate messages.
2. **Batching**: Aggregate small events (e.g., keyboard input) into a single message.
3. **Logging**: Include `requestId` in logs for tracing.
4. **Testing**: Mock WebSocket connections (e.g., `jest-websocket`, `pytest-asyncio`).
5. **Documentation**: Auto-generate OpenAPI/Swagger for WebSocket endpoints.

---
## **9. Example: Full Client-Server Flow**
### **Client (Frontend)**
1. Connects to `wss://api.example.com/ws`.
2. Sends:
   ```json
   { "action": "authenticate", "data": { "token": "xyz123" } }
   ```
3. Receives `acknowledge`; proceeds to subscribe.

### **Server (Backend)**
1. Validates token; assigns `sessionId`.
2. Stores session in Redis.
3. Broadcasts updates to subscribed clients:
   ```json
   { "action": "event", "data": { "type": "chat", "message": "Hello!" } }
   ```

---
## **10. Troubleshooting**
| **Issue**               | **Diagnosis**                          | **Solution**                                                                 |
|-------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| **Connection drops**    | Network latency, missing pings.        | Enable heartbeats (`ping/pong`), increase timeout.                         |
| **Duplicate messages**  | Client reconnects before server ack.   | Use `requestId` for deduplication.                                          |
| **Memory leaks**        | Unclosed sockets or listeners.         | Implement graceful disconnection (`socket.close()`).                       |
| **Slow responses**      | Heavy payloads or blocking operations. | Compress payloads (e.g., gzip), use async DB queries.                      |