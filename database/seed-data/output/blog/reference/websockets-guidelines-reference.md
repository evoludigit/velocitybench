# **[Pattern] WebSockets Guidelines Reference Guide**

---

## **Overview**
WebSockets provide full-duplex, bidirectional, low-latency communication between clients and servers over a single, persistent connection. This guide outlines best practices, key requirements, and implementation patterns for integrating WebSockets in modern applications. Following these guidelines ensures scalability, security, and reliability while minimizing performance overhead. Topics include protocol selection, connection management, message framing, error handling, and integration with REST/HTTP APIs.

---

## **Key Concepts & Implementation Details**

### **1. Core Principles**
| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Connection Persistence** | WebSockets maintain a single open connection, reducing handshake latency compared to HTTP polling. |
| **Full-Duplex Communication** | Both client and server can send/receive messages independently.                                    |
| **Lightweight Protocol**  | Header overhead minimized (vs. HTTP/HTTPS).                                                         |
| **Stateful Sessions**     | Each connection maintains session state (unlike stateless HTTP).                                   |
| **Binary vs. Text Frames** | Supports both text (UTF-8) and binary (Base64, Prot Buff, etc.) message framing.                   |

---

### **2. WebSocket States**
WebSockets follow a clear **state machine**:

| **State**      | **Description**                                                                                     | **Transition Trigger**                          |
|-----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `CONNECTING`    | Initiating handshake (e.g., upgrading from HTTP).                                                   | `open` event (success) or `error` (failure).     |
| `OPEN`          | Ready for bidirectional communication.                                                              | `close` event (graceful or abrupt termination). |
| `CLOSING`       | Initiating close handshake (clean termination).                                                      | `close` event (server-initiated).                 |
| `CLOSED`        | Connection terminated.                                                                              | Timeout or external interrupt.                    |

**Note:** Always check `readyState` before sending/receiving messages to avoid race conditions.

---

### **3. Protocol & Handshake**
#### **Handshake Process**
1. **HTTP Upgrade Request**:
   ```
   GET /chat HTTP/1.1
   Host: example.com
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
   Sec-WebSocket-Version: 13
   ```
2. **HTTP Response (Upgrade Success)**:
   ```
   HTTP/1.1 101 Switching Protocols
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
   ```

#### **Key Headers**
| **Header**                  | **Purpose**                                                                                          | **Example Values**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------|
| `Upgrade`                   | Specifies WebSocket protocol.                                                                         | `websocket`                             |
| `Connection`               | Indicates protocol upgrade.                                                                          | `Upgrade`                               |
| `Sec-WebSocket-Key`        | Random token for secure handshake (SHA-1 + GUID).                                                    | Base64-encoded string (16 chars)       |
| `Sec-WebSocket-Version`    | Specifies WebSocket protocol version (default: `13`).                                                | `13`                                    |
| `Sec-WebSocket-Extensions`  | Optional extensions (e.g., compression: `permessage-deflate`).                                       | `permessage-deflate`                    |

---

### **4. Message Framing**
WebSockets use a binary framing protocol (RFC 6455). Each message is wrapped in a **frame**:

| **Field**       | **Size (Bytes)** | **Description**                                                                                     |
|------------------|------------------|-----------------------------------------------------------------------------------------------------|
| **FIN**          | 1                | `1` = final frame, `0` = fragment.                                                                |
| **RSV1/RSV2/RSV3** | 3               | Reserved bits (extensibility; usually `0`).                                                          |
| **OpCode**       | 4                | Defines message type (e.g., `0x1` = text, `0x2` = binary).                                         |
| **Payload Length** | 7               | Length of payload (or 76/126/127 for extended lengths).                                              |
| **Masking Key**  | 4 (if client-to-server) | Optional security mask for client-sent frames.                                                      |
| **Payload Data** | Variable         | Actual message content (UTF-8 or binary).                                                          |

**Example Frame (Text Message, Length = 10):**
```
FIN=1, RSV=000, OpCode=0x1, Length=10, Mask=0x00000000
[Masked Payload: 0x4D616E6167656D656E74]
```

**Frame Types:**
| **OpCode (Hex)** | **Name**       | **Description**                                                                                     |
|------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `0x0`            | Continuation   | Part of a fragmented message.                                                                    |
| `0x1`            | Text           | UTF-8 encoded text message.                                                                        |
| `0x2`            | Binary         | Arbitrary binary data.                                                                             |
| `0x8`            | Close          | Connection termination frame.                                                                      |
| `0x9`            | Ping           | Ping-pong mechanism for keeping connection alive.                                                  |
| `0xA`            | Pong           | Response to `Ping`.                                                                               |

---

### **5. Connection Management**
#### **Best Practices**
- **Reconnection Logic**:
  - Implement exponential backoff (e.g., 1s → 2s → 4s → ...) for failed connections.
  - Use `WebSocket.BinaryType = 'arraybuffer'` for binary data to avoid serialization overhead.
- **Timeout Handling**:
  - Set a `pingInterval` (e.g., 30s) to detect dead connections (RFC 6455 §5.5.3).
  - Example:
    ```javascript
    if (!setInterval(() => socket.send(Uint8Array.of(0x9)), 30000)) {
      socket.close();
    }
    ```
- **Scalability**:
  - Use **clustering** (e.g., Node.js `cluster` module) or **load balancing** (Nginx WebSocket proxy).
  - For high traffic, consider **horizontal scaling** with a message broker (e.g., Redis Pub/Sub).

#### **Error Handling**
| **Error**               | **Cause**                                                                                          | **Resolution**                              |
|-------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `ERR_CONNECTION_CLOSED` | Server closed the connection.                                                                      | Reconnect with backoff.                     |
| `ERR_PROTOCOL`          | Invalid handshake or malformed frames.                                                              | Validate headers/frames.                    |
| `ERR_INVALID_URL`       | Invalid WebSocket URL (must use `ws://` or `wss://`).                                               | Use correct protocol.                       |
| `ERR_TOO_MANY_REQUESTS` | Rate-limiting (e.g., too many concurrent connections).                                               | Implement authentication (e.g., JWT).       |

---

### **6. Security Guidelines**
#### **Transport Security**
- **Always use `wss://`** (WebSocket Secure) with TLS 1.2+.
- Validate certificate chains to prevent MITM attacks.

#### **Authentication**
- **Headers**: Pass tokens in the first message (avoid `Sec-WebSocket-Extensions` for auth).
  ```javascript
  socket.send(JSON.stringify({ token: "abc123" }));
  ```
- **Subprotocols**: Extend handshake for auth (e.g., `Sec-WebSocket-Protocol: jwt-auth`).
- **Rate Limiting**: Block abuse with tools like Cloudflare or AWS WAF.

#### **Data Validation**
- Reject oversized messages (e.g., >1MB) to prevent DoS attacks.
- Sanitize text messages to avoid injection (e.g., SQL/JS code).

---

### **7. Integration with REST/HTTP**
#### **Hybrid Architectures**
- **WebSocket + REST**:
  - Use WebSockets for real-time updates (e.g., chat, live feeds).
  - Fall back to REST for initial auth/data fetch.
  - Example flow:
    1. User logs in via REST → receives JWT.
    2. Connects to WebSocket with JWT in first message.
    3. Server validates JWT and grants access.

#### **API Gateway Patterns**
| **Pattern**               | **Use Case**                                                                                          | **Implementation**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Edge Proxy**            | Route WebSocket traffic to backend servers (e.g., Nginx).                                            | Configure `proxy_pass` with WebSocket flags. |
| **API Gateway**           | Auth/rate-limit WebSocket connections before forwarding.                                               | Use Kong or AWS API Gateway.                |
| **Serverless**            | Scalable WebSocket endpoints (e.g., AWS Lambda + API Gateway).                                        | Deploy WebSocket handler as Lambda function. |

---

## **Schema Reference**
### **WebSocket Connection Schema**
| **Field**               | **Type**          | **Description**                                                                                     | **Example**                          |
|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `url`                   | `string`          | WebSocket URL (e.g., `wss://api.example.com/chat`).                                                  | `wss://api.example.com/chat`         |
| `protocols`             | `array<string>`   | Supported subprotocols (e.g., `["jwt-auth", "compression"]`).                                        | `["jwt-auth"]`                       |
| `timeout`               | `number`          | Handshake timeout in milliseconds (default: 30,000).                                                 | `10000`                               |
| `maxPayloadSize`        | `number`          | Maximum message size in bytes (default: 16KB).                                                       | `1048576` (1MB)                      |
| `extensions`            | `object`          | Optional protocol extensions (e.g., `permessage-deflate`).                                           | `{ "permessage-deflate": {} }`       |

### **Message Schema**
| **Field**               | **Type**          | **Description**                                                                                     | **Example**                          |
|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `opcode`                | `string`          | Message type (`text`, `binary`, `close`, etc.).                                                     | `text`                                |
| `payload`               | `string` or `Uint8Array` | Message content (UTF-8 or binary).                                                                 | `Uint8Array.from([0x48, 0x65, 0x6C, 0x6C, 0x6F])` |
| `mask`                  | `boolean`         | Whether payload is masked (client→server).                                                            | `true`                                |
| `fragmented`            | `boolean`         | Indicator if message is part of a fragment.                                                          | `false`                               |

---

## **Query Examples**
### **1. Basic Connection**
**Client (JavaScript):**
```javascript
const socket = new WebSocket("wss://api.example.com/chat");
socket.onopen = () => console.log("Connected");
socket.onmessage = (event) => console.log("Message:", event.data);
socket.onclose = () => console.log("Disconnected");
```

**Server (Node.js):**
```javascript
const WebSocket = require("ws");
const wss = new WebSocket.Server({ port: 8080 });

wss.on("connection", (ws) => {
  ws.on("message", (data) => {
    ws.send(`Server received: ${data}`);
  });
});
```

### **2. Authenticated Connection**
**Client:**
```javascript
socket.send(
  JSON.stringify({
    type: "auth",
    token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  })
);
```

**Server:**
```javascript
ws.on("message", (data) => {
  const msg = JSON.parse(data);
  if (msg.type === "auth") {
    if (validateToken(msg.token)) {
      ws.send('{"status":"authenticated"}');
    } else {
      ws.close(1008, "Unauthorized");
    }
  }
});
```

### **3. Binary Data Transfer**
**Client (Binary):**
```javascript
const imageData = new Uint8Array([...]);
socket.binaryType = "arraybuffer";
socket.send(imageData);
```

**Server:**
```javascript
ws.on("message", (data) => {
  if (ws.binaryType === "arraybuffer") {
    console.log("Binary data received:", data);
  }
});
```

### **4. Heartbeat/Ping-Pong**
**Client:**
```javascript
setInterval(() => {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(Uint8Array.of(0x9)); // Ping
  }
}, 30000);

socket.onmessage = (event) => {
  if (event.data instanceof Uint8Array && event.data[0] === 0xA) {
    console.log("Pong received");
  }
};
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| **[Server-Sent Events (SSE)]** | One-way server-to-client updates via HTTP.                                                          | Firehose-style updates (no bidirectional). |
| **[Long Polling]**        | Simulates WebSockets with repeated HTTP requests.                                                    | Legacy browser support.                   |
| **[Event-Driven Architecture]** | Decouple producers/consumers via message brokers (e.g., Kafka, RabbitMQ).                          | Microservices with high throughput.      |
| **[WebSocket + JWT]**     | Secure WebSocket connections with JSON Web Tokens.                                                  | OAuth2/OpenID flows.                     |
| **[WebSocket Compression]** | Use `permessage-deflate` to reduce payload size.                                                    | High-bandwidth scenarios (e.g., gaming). |
| **[WebSocket Load Balancing]** | Distribute WebSocket traffic across multiple servers.                                                | Scaling to thousands of concurrent users.|

---

## **Troubleshooting**
| **Issue**               | **Diagnosis**                                                                                     | **Fix**                                  |
|-------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| **Connection Drops**    | Check server logs for `ERR_CONNECTION_CLOSED`.                                                     | Ensure `keepalive` ping/pong is enabled.|
| **High Latency**        | Monitor RTT (Round-Trip Time) with `performance.now()`.                                           | Optimize server location (CDN, edge).   |
| **Memory Leaks**        | Browser/dev tools show unbounded WebSocket connections.                                            | Implement `socket.close()` on unmount.   |
| **CORS Errors**         | Client blocked by `Access-Control-Allow-Origin` (even for WebSockets).                             | Configure CORS headers: `Access-Control-Allow-Origin: *`. |
| **Binary Data Corruption** | Messages arrive garbled.                                                                             | Verify `binaryType` is set correctly.    |

---
**References**:
- [RFC 6455: The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [MDN WebSocket Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Node.js `ws` Library](https://github.com/websockets/ws)