# **[Pattern] Websockets Strategies Reference Guide**

---

## **Overview**
**Websockets Strategies** is a design pattern for implementing efficient, low-latency bidirectional communication between clients and servers over the WebSocket protocol. It addresses traditional HTTP’s request-response model by maintaining persistent connections, enabling real-time data exchange for applications like live dashboards, collaborative tools, and IoT systems. This pattern covers connection management, message routing, error handling, and scaling strategies to ensure reliability, performance, and maintainability in distributed systems.

---

## **Key Concepts & Implementation Details**

### **Core Principles**
1. **Persistent Connection:** WebSocket establishes a single, long-lived connection (instead of repeated HTTP handshakes).
2. **Full-Duplex Communication:** Clients *and* servers can send messages independently.
3. **Lightweight Protocol:** Minimal overhead (vs. HTTP/SOAP) with binary/text framing.
4. **Scalability:** Strategies to manage concurrent connections (e.g., clustering, load balancing).

---

## **Schema Reference**

| **Component**          | **Description**                                                                                     | **Example Format**                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **WebSocket URL**      | Endpoint for connection (e.g., `ws://` or `wss://`).                                               | `wss://api.example.com/ws/notifications`                                           |
| **Connection Handshake**| Initial HTTP upgrade request to establish WebSocket (RFC 6455).                                    | `GET /ws/endpoint HTTP/1.1<br>Upgrade: websocket<br>Connection: Upgrade`             |
| **Message Framing**    | Payload structure (FIN bit, opcode, mask, payload data).                                           | `[FIN=1, opcode=2 (text), payload="Hello"]`                                       |
| **Message Types**      | Standard opcodes (`0x1`: text, `0x2`: binary, `0x8`: close).                                      | `{ "event": "user_join", "data": { "userId": 123 } }`                             |
| **Heartbeat Pings**    | Prevents idle disconnections via periodic `PING`/`PONG` messages.                                | `PING`, `PONG 12345` (nonces to detect packet loss).                              |
| **Error Handling**     | Error codes: `1000` (normal), `1006` (malformed).                                                 | `close(1006, "Invalid opcode")`                                                    |
| **Reconnection Logic** | Exponential backoff: `waitTime = min(5s * (2^n), 30s)`.                                          | `retryDelay = Math.min(5 * Math.pow(2, attempt), 30000)`                          |
| **Scaling**            | **Horizontal Scaling**: Load balancer distributes connections (e.g., via `ws://<load-balancer>`).  | NGINX/HAProxy: `stream { proxy_pass ws://backend; }`                             |
| **Authentication**     | Early auth via `Sec-WebSocket-Extensions` or post-handshake tokens.                              | Header: `Sec-WebSocket-Protocol: token=abc123`                                    |
| **Compression**        | Optional `permessage-deflate` extension (RFC 7692).                                               | `Accept-Encoding: deflate`                                                         |

---

## **Implementation Examples**

### **1. Basic Client-Server Connection**
#### **Client-Side (JavaScript)**
```javascript
const socket = new WebSocket('wss://api.example.com/ws/updates');
socket.onopen = () => console.log('Connected');
socket.onmessage = (e) => console.log('Message:', e.data);
socket.onclose = () => console.log('Disconnected');
socket.send(JSON.stringify({ type: 'subscribe', channel: 'news' }));
```

#### **Server-Side (Node.js with `ws` Library)**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    console.log('Received:', data);
    if (data === 'subscribe') ws.send(JSON.stringify({ status: 'subscribed' }));
  });
});
```

---

### **2. Reconnection Strategy**
```javascript
let attempt = 0;
const maxAttempts = 5;
const socket = new WebSocket('wss://api.example.com/ws');

socket.onclose = () => {
  if (attempt < maxAttempts) {
    const delay = Math.min(5 * Math.pow(2, attempt), 30000);
    setTimeout(() => reconnect(), delay);
    attempt++;
  }
};
```

---

### **3. Heartbeat Mechanism**
#### **Client**
```javascript
socket.addEventListener('open', () => {
  setInterval(() => socket.send('ping'), 30000); // Send PING every 30s
});

socket.addEventListener('message', (e) => {
  if (e.data === 'pong') clearTimeout(lastPingTimeout);
});
```

#### **Server**
```javascript
wss.on('connection', (ws) => {
  setInterval(() => ws.send('pong'), 25000); // Respond every 25s
  ws.on('ping', () => ws.send('pong'));
});
```

---

### **4. Load Balancing (NGINX)**
```nginx
stream {
  upstream ws_backend {
    server backend1:8080;
    server backend2:8080;
  }
  server {
    listen 8080;
    proxy_pass ws_backend;
  }
}
```

---

### **5. Security Considerations**
- **TLS**: Always use `wss://` to encrypt traffic.
- **Validation**: Sanitize incoming messages (e.g., reject oversized payloads).
  ```javascript
  if (data.length > 1024 * 1024) { // 1MB limit
    ws.close(1007, 'Message too large');
  }
  ```
- **Rate Limiting**: Throttle messages per client (e.g., using `express-rate-limit`).

---

## **Related Patterns**
1. **[Event-Driven Architecture](https://refarchitectures.dev/event-driven-pub-sub)**:
   Use WebSockets for real-time event delivery alongside Pub/Sub systems (e.g., Redis, Kafka).
2. **[Connection Pooling (Database)](https://refarchitectures.dev/connection-pooling)**:
   Reuse WebSocket connections efficiently to reduce overhead.
3. **[CQRS](https://refarchitectures.dev/cqrs)**:
   WebSockets can serve as the "read model" channel for live updates.
4. **[Service Mesh (Envoy/Istio)](https://refarchitectures.dev/service-mesh)**:
   Integrate WebSocket traffic into a service mesh for observability and retries.
5. **[Webhooks vs. WebSockets]**:
   - **Webhooks**: Asynchronous, one-time HTTP callbacks.
   - **WebSockets**: Persistent, bidirectional, real-time.

---

## **Troubleshooting**
| **Issue**               | **Check**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------|
| Connection drops         | Verify `keepalive` settings, TLS, or firewall rules.                                         |
| High latency             | Test with `wss://` (TLS) vs. `ws://` (plaintext).                                           |
| Memory leaks             | Monitor heap usage; close sockets explicitly (`ws.close()`) when done.                      |
| Authentication failures  | Ensure `Sec-WebSocket-Extensions` or post-handshake tokens are set correctly.              |
| Scaling bottlenecks      | Use connection brokers (e.g., Socket.IO’s rooms) or horizontal scaling.                     |

---

## **Best Practices**
1. **Use `wss://`**: Enforce TLS to prevent MITM attacks.
2. **Compress Messages**: Enable `permessage-deflate` for large payloads (e.g., JSON APIs).
3. **Graceful Degradation**: Fall back to polling if WebSockets fail.
4. **Logging**: Track connection lifecycles, errors, and message volumes.
5. **Testing**:
   - Load test with tools like **Locust** or **k6**.
   - Simulate network partitions (e.g., `mock-socket` for unit tests).

---
**Length**: ~1,000 words
**Target Audience**: Backend engineers, full-stack developers, system architects.