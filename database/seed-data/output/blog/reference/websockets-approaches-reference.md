**[Pattern] Websockets Approaches – Reference Guide**

---

### **Overview**
Websockets Approaches provide a persistent, bidirectional communication channel between a client (browser, mobile app, or IoT device) and a server, replacing traditional HTTP polling. This pattern is ideal for real-time applications such as live chat, collaborative editing, stock tickers, and multiplayer games. Unlike REST or GraphQL, Websockets enable low-latency, full-duplex communication with minimal overhead, making them perfect for scenarios requiring event-driven updates. This guide outlines key implementation approaches, protocols, and integration strategies.

---

### **Implementation Details**

#### **Core Concepts**
1. **Connection Lifecycle**
   - **Handshake**: Initial TCP handshake between client (via `ws://` or `wss://`) and server to establish a WebSocket connection.
   - **Data Framing**: Messages are split into frames (with headers indicating type: text, binary, ping/pong).
   - **Keepalive**: Optional periodic pings/pongs to maintain connection health.
   - **Clean Closure**: Graceful shutdown via `close()` method or server-triggered disconnection.

2. **Protocols**
   - **Standard WebSockets (`ws://`/`wss://`)**:
     - Baseline protocol with text/binary framing and basic security (WSS = TLS).
     - No built-in authentication; rely on headers or tokens in messages.
   - **Protocol Extensions**:
     - **Security**: [RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455) (standard) or [Per-Message Deflate](https://tools.ietf.org/html/rfc7692) (compression).
     - **Scalability**: [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) (unidirectional, HTTP-based fallback).

3. **Scalability Considerations**
   - **Load Balancing**: Use sticky sessions or dedicated WebSocket proxies (e.g., NGINX, Envoy).
   - **Cluster Management**: Shared state via Redis or databases for horizontal scaling.
   - **Connection Limits**: Monitor and throttle connections (e.g., 10K–100K connections/node).

4. **Error Handling**
   - **Client Errors**:
     - `ONERROR` event (browser) or `ConnectionError` (Node.js).
     - Network issues: Retry logic with exponential backoff.
   - **Server Errors**:
     - Return HTTP 101 (Switching Protocols) or HTTP 400–500 for misconfigured requests.
     - Use `close()` with status codes (e.g., `1008: Policy Violation`).

5. **Security**
   - **TLS**: Enforce `wss://` to encrypt traffic.
   - **Authentication**: Pass tokens in the initial handshake (e.g., via query params or cookies) or in messages.
   - **Prevent Abuse**:
     - Rate-limit connections (e.g., 100/sec).
     - Validate message size (e.g., max 16KB frames).

6. **Message Formats**
   - **Text**: JSON (recommended for structured data):
     ```json
     {"type": "chat", "user": "alice", "message": "Hello!"}
     ```
   - **Binary**: Prot Buffers, MessagePack, or raw bytes (e.g., for multimedia).

---

### **Schema Reference**
Below are common WebSocket message schemas for different use cases.

| **Use Case**          | **Schema**                                                                 | **Example Payload**                          | **Notes**                                  |
|-----------------------|---------------------------------------------------------------------------|----------------------------------------------|--------------------------------------------|
| **Authentication**    | `{ "type": "auth", "token": string }`                                   | `{"token": "abc123"}`                        | Sent on connect.                           |
| **Chat Messages**     | `{ "type": "message", "sender": string, "text": string }`                | `{"sender": "bob", "text": "Hi!}`           | Use `ONMESSAGE` event.                     |
| **Presence Updates**  | `{ "type": "presence", "user": string, "action": "join|leave" }`        | `{"user": "eve", "action": "join"}`          | Track online users.                        |
| **Notifications**     | `{ "type": "notify", "title": string, "body": string }`                  | `{"title": "Alert", "body": "New task!"}`     | For push-like updates.                     |
| **Binary Data**       | Binary frame (e.g., WebRTC, WebGL texture updates)                       | `ArrayBuffer`                               | Use `ArrayBuffer` in `ONMESSAGE`.          |
| **Heartbeat**         | `{ "type": "heartbeat" }` (or empty frame)                              | `{"type": "heartbeat"}`                     | Built-in via `close()` with `ping/pong`.   |

---

### **Query Examples**
#### **1. Establishing a Connection**
**Client-Side (JavaScript):**
```javascript
const socket = new WebSocket("wss://api.example.com/ws/chat");
socket.onopen = () => {
  socket.send(JSON.stringify({ type: "auth", token: "abc123" }));
};
```

**Server-Side (Node.js with `ws` library):**
```javascript
const WebSocket = require("ws");
const wss = new WebSocket.Server({ port: 8080 });

wss.on("connection", (ws) => {
  ws.on("message", (data) => {
    const msg = JSON.parse(data);
    if (msg.type === "auth" && msg.token === "abc123") {
      ws.send(JSON.stringify({ type: "auth_ok" }));
    }
  });
});
```

#### **2. Sending/Receiving Messages**
**Client:**
```javascript
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Received: ${data.text}`);
};
socket.send(JSON.stringify({ type: "message", text: "Hello server!" }));
```

**Server:**
```javascript
wss.on("connection", (ws) => {
  ws.send(JSON.stringify({ type: "welcome", message: "Connected!" }));
});
```

#### **3. Handling Errors**
**Client:**
```javascript
socket.onerror = (error) => {
  console.error("WebSocket error:", error);
  // Retry logic
};
```

**Server:**
```javascript
wss.on("connection", (ws) => {
  ws.on("error", (error) => {
    console.error("Client error:", error);
    ws.terminate(); // Force-close
  });
});
```

#### **4. Scaling with Multiple Servers**
Use a load balancer (e.g., NGINX) with sticky sessions:
```nginx
upstream websocket_servers {
  ip_hash;
  server ws-server1:8080;
  server ws-server2:8080;
}
server {
  listen 8080;
  location /ws {
    proxy_pass http://websocket_servers;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```

#### **5. Fallback to SSE**
For browsers without WebSocket support:
```javascript
if (!WebSocket) {
  const eventSource = new EventSource("http://api.example.com/sse/chat");
  eventSource.onmessage = (e) => console.log(e.data);
}
```

---

### **Related Patterns**
1. **[Event-Driven Architecture]**
   - Websockets complement event-driven systems by enabling real-time event propagation (e.g., Kafka + WebSocket bridges).

2. **[Pub/Sub (Publish-Subscribe)]**
   - Use Websockets to deliver pub/sub messages (e.g., via Redis Pub/Sub or NATS).

3. **[JWT Authentication]**
   - Integrate JWT tokens in WebSocket handshakes for stateless auth:
     ```json
     {"type": "auth", "token": "eyJhbGciOiJIUzI1Ni..."}
     ```

4. **[Long Polling]**
   - Legacy fallback for WebSocket browsers (not recommended for new projects).

5. **[Server-Sent Events (SSE)]**
   - Unidirectional alternative to Websockets (e.g., for notifications).

6. **[gRPC-Web]**
   - For high-performance APIs with WebSocket-like transport (binary protocol).

7. **[Rate Limiting]**
   - Apply rate limits to WebSocket connections (e.g., via Redis + `ws` middleware).

8. **[Graceful Degradation]**
   - Fall back to polling if WebSocket fails (e.g., for offline-first apps).

---

### **Best Practices**
- **Keep Messages Small**: Fragment large payloads to avoid latency.
- **Compress Data**: Use [Per-Message Deflate](https://tools.ietf.org/html/rfc7692) for text.
- **Monitor Connections**: Track active connections and latency (e.g., with Prometheus).
- **Avoid Blocking**: Never block the event loop on the server (use async/await).
- **Document APIs**: Publish a spec for message types (e.g., OpenAPI + WebSocket extensions).