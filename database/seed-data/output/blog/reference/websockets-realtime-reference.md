# **[Pattern] WebSockets and Real-Time Communication – Reference Guide**

---

## **1. Overview**
WebSockets and Real-Time Communication enable bidirectional, low-latency data exchange between clients and servers via persistent TCP connections. Unlike traditional HTTP polling or long-polling, WebSockets establish a single, efficient channel for real-time updates. This pattern is ideal for applications requiring instant synchronization, such as live chat, collaborative tools, financial tickers, and multiplayer games. Server-Sent Events (SSE) are a simpler alternative for one-way server-to-client push if bidirectional communication isn’t required. Key benefits include reduced overhead, scalability, and seamless user experiences.

---

## **2. Key Concepts & Schema Reference**

### **Core Components**
| **Component**          | **Description**                                                                                     | **Protocol Standard**                     |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| **WebSocket**          | A full-duplex protocol enabling real-time text/binary data exchange                               | [RFC 6455](https://tools.ietf.org/html/rfc6455) |
| **Handshake**          | Upgrade from HTTP to WebSocket via HTTP headers (e.g., `Upgrade: websocket`)                        | Custom handshake via headers               |
| **Connection State**   | States include `CONNECTING`, `OPEN`, `CLOSING`, and `CLOSED`                                       | WebSocket API                               |
| **Messages**           | Text (`UTF-8`) or binary (`Base64`) data payloads with optional framing                            | WebSocket framing (`FIN`, `Opcode`, etc.)  |
| **Server-Sent Events (SSE)** | Simpler HTTP-based unidirectional server-to-client streaming (one response per connection)         | [RFC 7407](https://tools.ietf.org/html/rfc7407) |

---

### **WebSocket Message Schema**
| **Field**      | **Type**   | **Description**                                                                                     | **Example**                          |
|----------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **Opcode**     | `uint8`    | Defines message type (e.g., `0x1` for text, `0x2` for binary)                                       | `0x1` (Text)                         |
| **Mask**       | `uint8`    | Client-side masking flag (server sends unmasked frames)                                           | `0x80` (Masked)                      |
| **Payload Data** | `Blob`     | Raw data (text or binary)                                                                           | `"Hello, real-time!"`                |
| **Masking Key**| `uint32`   | 4-byte key used for client-side decryption (if masked)                                               | `[0x33, 0x55, 0x88, 0x00]`          |

---
### **SSE Event Schema**
| **Header**     | **Description**                                                                                     | **Example**                          |
|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Content-Type` | Must be `text/event-stream`                                                                         | `text/event-stream`                   |
| `data`         | Payload data (can be multiple `data:` fields per event)                                              | `: "Update: 42"`                     |
| `event`        | Custom event name (e.g., `chat_message`)                                                           | `event: chat_message`                |
| `id`           | Unique identifier for last event (used for reconnects)                                              | `id: 12345`                          |

---

## **3. Implementation Details**

### **Client-Side Implementation (JavaScript)**
```javascript
// Open WebSocket connection
const socket = new WebSocket("wss://example.com/ws");

// Event Handlers
socket.onopen = () => console.log("Connected");
socket.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log("Received:", data);
};
socket.onclose = () => console.log("Disconnected");
socket.onerror = (e) => console.error("Error:", e);

// Send message
socket.send(JSON.stringify({ action: "update", value: 100 }));
```

### **Server-Side Implementation (Node.js with `ws` Library)**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    console.log("Received:", data.toString());
    ws.send(JSON.stringify({ status: "ack" }));
  });

  ws.send(JSON.stringify({ welcome: true }));
});
```

### **SSE Server (Node.js with `http` Module)**
```javascript
const http = require('http');
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/event-stream' });
  res.write("event: update\n");
  res.write("data: 100\n\n");
  setInterval(() => {
    res.write(`data: ${Math.random()}\n\n`);
  }, 1000);
});
server.listen(3000);
```

---

## **4. Query Examples**

### **WebSocket Handshake (HTTP Upgrade Request)**
```http
GET /chat HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

### **Server Sent Event (SSE) Stream Response**
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: chat_message
data: {"user": "Alice", "message": "Hello!"}
id: 42
```

---

## **5. Best Practices**
1. **Connection Management**:
   - Implement reconnection logic for WebSockets (e.g., exponential backoff).
   - Use `ping`/`pong` frames to detect dead connections.
2. **Message Serialization**:
   - Prefer `JSON` for structured data; use `Base64` for binary payloads.
3. **Scalability**:
   - Use a WebSocket gateway (e.g., Socket.IO, Pusher) for load balancing.
   - Consider message brokers (Redis, RabbitMQ) for distributed systems.
4. **Security**:
   - Enforce TLS (`wss://`) to prevent MITM attacks.
   - Validate all messages on the server side.
5. **Performance**:
   - Compress messages (e.g., `zstd`) for large payloads.
   - Optimize framing to minimize overhead.

---

## **6. Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                                     |
|--------------------------------------|-------------------------------------------------------------------------------------------------|
| WebSocket connection drops over time | Use `ping`/`pong` frames and reconnection logic.                                               |
| Binary data corruption               | Ensure proper masking (clients mask; servers don’t).                                           |
| SSE client-side buffering             | Implement client-side `AbortController` for clean disconnections.                               |
| Memory leaks (e.g., Buffers)         | Close unused connections and clear event listeners.                                             |

---

## **7. Related Patterns**
| **Pattern**                     | **Use Case**                                                                                     | **When to Combine**                          |
|----------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Event-Driven Architecture**    | Decouple producers/consumers of real-time data.                                                  | Use SSE/WebSockets for event delivery.        |
| **CQRS (Command Query Separation)** | Separate read/write operations for scalability.                                                  | WebSockets can act as the "read" channel.     |
| **Pub/Sub (Redis Streams)**       | Scale real-time messaging across servers.                                                         | Pair with WebSockets for client push.          |
| **Long Polling**                 | Fallback for WebSocket support in legacy browsers.                                               | Hybrid approach (WebSocket first, fallback).  |
| **GraphQL Subscriptions**         | Real-time GraphQL queries (e.g., via Apollo Server + WebSockets).                                | Combine for GraphQL + WebSocket APIs.          |

---

## **8. Tools & Libraries**
| **Tool/Library**                  | **Language** | **Purpose**                                                                                     |
|-----------------------------------|--------------|-------------------------------------------------------------------------------------------------|
| `ws` (Node.js)                    | JavaScript   | Pure WebSocket implementation.                                                                 |
| `Socket.IO`                       | JavaScript   | WebSocket + fallbacks (e.g., HTTP long-polling).                                               |
| `Spring WebSocket`                | Java         | Spring Boot WebSocket support.                                                                  |
| `django-channels`                 | Python       | Django WebSocket framework.                                                                     |
| `Pusher.js`                       | JavaScript   | Managed WebSocket service with hosting.                                                         |
| `ActionCable` (Ruby on Rails)     | Ruby         | Rails-native real-time feature.                                                                |

---
## **9. Further Reading**
- [RFC 6455 (WebSockets)](https://tools.ietf.org/html/rfc6455)
- [MDN WebSocket Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Socket.IO Docs](https://socket.io/docs/v4/)
- [SSE Best Practices (Google)](https://developers.google.com/web/updates/2017/02/serversentevents-best-practices)