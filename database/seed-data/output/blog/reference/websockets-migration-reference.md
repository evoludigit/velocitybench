# **[Pattern] WebSockets Migration Reference Guide**

---

## **Overview**
This guide details the **WebSockets Migration** pattern, a structured approach for transitioning from traditional HTTP-based long-polling or server-sent events (SSE) to **WebSocket-based real-time communication** in web applications. WebSockets enable **full-duplex, low-latency bidirectional communication** between clients and servers, reducing overhead compared to HTTP-based alternatives. This pattern describes key decisions, implementation considerations, and migration strategies to ensure minimal disruption while improving scalability and responsiveness.

---

## **Key Concepts**
Before migrating, understand these core components:

| **Concept**               | **Description**                                                                 | **Key Considerations**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **WebSocket Protocol**    | A persistent TCP connection over `wss://` (secure) or `ws://` (insecure)        | Supports text (`UTF-8`) and binary data frames.                                       |
| **Handshake**             | Initial HTTP upgrade request (HTTP 1.1) to establish a WebSocket connection      | Must be configured on the server (e.g., via `Sec-WebSocket-Key` handshake).           |
| **Connection States**     | `CONNECTING`, `OPEN`, `CLOSING`, `CLOSED` (RFC 6455)                            | Error handling required for state transitions (e.g., reconnection logic).             |
| **Scalability**           | Horizontal scaling via load balancers with sticky sessions                      | Session management (e.g., Redis) may be needed for multi-server setups.               |
| **Security**              | TLS required for production; validate origins (`Sec-WebSocket-Origin` header)  | Avoid exposing WebSocket endpoints to untrusted networks.                             |
| **Fallback Mechanisms**   | Polyfill libraries (e.g., `socket.io`) for browsers without native WebSocket support | Graceful degradation for older clients.                                               |
| **Message Framing**       | Data split into frames with_opcode_,_masking_, and length prefixes               | Binary data requires masking in certain cases (e.g., non-RFC 6455 clients).           |

---

## **Schema Reference**
Below are common WebSocket message schemas for migration scenarios.

### **1. Connection Establishment**
| **Field**                | **Type**       | **Description**                                                                 | **Example Value**                     |
|--------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| `Sec-WebSocket-Key`      | String (base64) | Unique key for handshake validation                                           | `dGhlIHNhbXBsZSBub25jZQ==`            |
| `Sec-WebSocket-Version`  | String         | Protocol version (must be `13`)                                               | `13`                                   |
| `Connection`             | String         | Must include `Upgrade: websocket`                                              | `Upgrade: websocket\r\nConnection:Upgrade` |
| `Upgrade`                | String         | Specifies WebSocket as the target protocol                                     | `websocket`                            |

**Server Response Headers (Successful Handshake):**
| **Header**               | **Value**                     | **Description**                                                                 |
|--------------------------|-------------------------------|---------------------------------------------------------------------------------|
| `Upgrade`                | `websocket`                   | Confirms protocol switch.                                                       |
| `Connection`             | `Upgrade`                     | Maintains connection after upgrade.                                             |
| `Sec-WebSocket-Accept`   | SHA-1 hash of key + GUID      | Validates client key (e.g., `s3pPLMBiTxaQ9kYGzzhZRbK+xOo=`).                     |

---

### **2. Message Payload**
| **Frame Type**           | **Purpose**                                      | **Schema**                                                                       | **Opcode** |
|--------------------------|--------------------------------------------------|---------------------------------------------------------------------------------|------------|
| **Text Frame**           | Arbitrary text data (UTF-8 encoded)             | `{ "type": "text", "data": string, "timestamp": ISO8601 }`                     | `0x1`      |
| **Binary Frame**         | Binary data (e.g., images, protocol buffers)     | `{ "type": "binary", "data": base64 }`                                           | `0x2`      |
| **Close Frame**          | Initiates graceful connection termination       | `{ "reason": string, "code": number (1000–4999) }`                              | `0x8`      |
| **Ping/Pong**            | Connection lifecycle checks                    | `{ "type": "ping" }` or `{ "type": "pong" }`                                    | `0x9`/`0xA`|

**Example Text Frame (JSON):**
```json
{
  "type": "text",
  "data": "{\"event\":\"update\",\"data\":{\"count\":42}}",
  "timestamp": "2023-10-01T12:00:00Z",
  "id": "req-12345"
}
```

---

### **3. Error Handling**
| **Error Code** | **Description**                          | **Example Use Case**                          |
|----------------|------------------------------------------|-----------------------------------------------|
| `1000`         | Normal closure                           | Client-initiated disconnect.                  |
| `1001`         | Going away                              | Server shutting down gracefully.              |
| `1002`         | Protocol error                           | Malformed handshake or frame.                 |
| `1008`         | Policy violation                         | Client sending forbidden data (e.g., DDoS).   |
| `4000–4999`    | Application-specific                     | Custom error codes (e.g., `4001`: "Invalid auth"). |

**Example Close Frame:**
```json
{
  "type": "close",
  "code": 4001,
  "reason": "Authentication required",
  "data": "{\"token\":\"invalid\"}"
}
```

---

## **Migration Steps**
### **1. Assess Current Architecture**
- Identify HTTP-based long-polling/SSE endpoints (e.g., `/stream`, `/ping`).
- Map real-time dependencies (e.g., chat, live updates).
- Audit security requirements (e.g., JWT validation, rate limiting).

### **2. Design WebSocket Endpoints**
| **Endpoint**       | **HTTP → WebSocket** | **Description**                                                                 |
|--------------------|----------------------|---------------------------------------------------------------------------------|
| `/api/stream`      | `ws://domain/stream` | Replaces polling with persistent connection.                                   |
| `/api/chat`        | `ws://domain/chat`   | Replaces SSE for bidirectional messaging.                                       |
| `/api/auth`        | N/A (HTTP)           | Authenticate WebSocket connections via HTTP-first flow (e.g., `/login`).        |

**Route Examples:**
```javascript
// Server (Node.js with `ws`)
const wss = new WebSocketServer({ server: httpServer });
wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    // Parse JSON: { "type": "message", "user": "123", "text": "Hello" }
    broadcast(data, wss.clients);
  });
});

// Client (Browser)
const socket = new WebSocket('wss://domain.com/chat');
socket.addEventListener('message', (event) => {
  const payload = JSON.parse(event.data);
  console.log(payload.text);
});
```

---

### **3. Implement Backward Compatibility**
- **Fallback to HTTP/SSE:** Use `socket.io` for clients without native WebSocket support:
  ```javascript
  const socket = io('https://domain.com', {
    transports: ['websocket', 'polling'], // Fallback to HTTP long-polling
    reconnection: true
  });
  ```
- **Feature Flags:** Route legacy vs. WebSocket traffic via headers:
  ```http
  GET /api/stream?upgrade=websocket
  ```
- **Graceful Degradation:** Queue WebSocket messages for disconnected clients (e.g., Redis pub/sub).

---

### **4. Security Hardening**
| **Measure**               | **Implementation**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------|
| **TLS Enforcement**       | Redirect HTTP → HTTPS; validate `Sec-WebSocket-Extensions` (e.g., `permessage-deflate`). |
| **Origin Validation**     | Check `Sec-WebSocket-Origin` header against allowed domains.                       |
| **Auth Integration**      | Attach JWT to connection handshake or first message:                              |
|                           | `ws://domain/chat?token=eyJhbGciOiJIUzI1Ni...`                                    |
| **Rate Limiting**         | Use middleware (e.g., `express-rate-limit`) to block abusive connections.         |
| **Binary Data Safety**    | Mask binary frames if clients are non-compliant (RFC 6455 §5.6).                   |

---

### **5. Testing**
| **Test Type**             | **Tools/Methods**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------|
| **Connection Lifecycle**  | Use `curl` for handshake validation:                                             |
|                           | `curl -I -H "Upgrade: websocket" -H "Connection: Upgrade" http://domain.com/ws`   |
| **Message Integrity**     | Verify checksums for binary data (e.g., `crc32`).                                |
| **Load Testing**          | Simulate 10K+ concurrent connections with `wrk` or `k6`.                         |
| **Reconnection**          | Test auto-reconnect logic (e.g., exponential backoff).                           |
| **Security Scanning**     | Use OWASP ZAP to detect WebSocket vulnerabilities (e.g., CORS misconfigurations). |

**Example `wrk` Test Command:**
```bash
wrk -t12 -c5000 -d30s ws://domain.com/chat
```

---

### **6. Monitoring**
| **Metric**                | **Tool**       | **Threshold**               |
|---------------------------|----------------|-----------------------------|
| **Open Connections**      | Prometheus     | Alert if > 90% of capacity. |
| **Message Latency**       | Datadog        | P99 < 100ms                  |
| **Connection Drops**      | ELK Stack      | < 0.1%/hour                  |
| **Bandwidth Usage**       | Cloud Monitoring | Warn at 80% of tier limits. |

**Key Alerts:**
- `WebSocket_Drops_Increasing` (e.g., due to network partitions).
- `Message_Queue_Backlog` (unhandled messages in Redis).

---

## **Query Examples**
### **1. Establishing a Connection**
**Client-Side (Browser):**
```javascript
// Basic WebSocket
const socket = new WebSocket('wss://domain.com/stream');

// With Auth token
const socket = new WebSocket('wss://domain.com/stream', {
  headers: { Authorization: 'Bearer JWT_TOKEN' }
});

// Socket.IO (fallback)
const socket = io('https://domain.com', {
  path: '/socket.io',
  query: { token: 'JWT_TOKEN' }
});
```

**Server-Side (Node.js):**
```javascript
// Handle handshake
server.on('upgrade', (req, socket, head) => {
  const auth = req.headers.authorization;
  if (!auth || !validateToken(auth)) {
    socket.destroy();
    return;
  }
  ws.handleUpgrade(req, socket, head, (ws) => {
    app.emit('connection', ws, req);
  });
});
```

---

### **2. Sending/Receiving Messages**
**Client → Server (JSON Payload):**
```javascript
socket.send(JSON.stringify({
  type: 'subscribe',
  channel: 'notifications',
  userId: '123'
}));
```

**Server → Client (Broadcast):**
```javascript
// Emit to all clients in a channel
io.to('notifications').emit('update', {
  type: 'message',
  content: 'New notification',
  timestamp: Date.now()
});
```

**Binary Data (e.g., Image Upload):**
```javascript
// Client
const binaryData = new Blob([new Uint8Array([...])]);
socket.send(binaryData);

// Server
ws.on('message', (data) => {
  if (ws.isBinaryType) {
    const buffer = new Uint8Array(data);
    // Process binary data (e.g., save to S3)
  }
});
```

---

### **3. Error Handling**
**Client-Side:**
```javascript
socket.addEventListener('error', (event) => {
  if (event.code === 1008) { // Policy violation
    console.error('Authentication failed:', event.reason);
  }
  reconnect(); // Exponential backoff
});

socket.addEventListener('close', (event) => {
  if (event.code !== 1000) { // Only reconnect on non-normal closure
    reconnect();
  }
});
```

**Server-Side:**
```javascript
ws.on('error', (error) => {
  if (error.code === 'ECONNRESET') {
    // Client closed abruptly; log and ignore
  }
});

ws.on('close', (code, reason) => {
  if (code === 4001 && reason === 'Invalid auth') {
    // Log failed attempt
    incrementAuthFailures();
  }
});
```

---

## **Performance Considerations**
| **Aspect**               | **Recommendation**                                                                 |
|--------------------------|-----------------------------------------------------------------------------------|
| **Connection Pooling**   | Reuse connections (WebSockets are persistent).                                    |
| **Message Size**         | Limit to < 16MB (RFC 6455 §5.6). Use compression for large payloads.                |
| **Scaling**              | Use Redis for session affinity in clustered environments.                          |
| **Garbage Collection**   | Close idle connections (e.g., after 5 minutes of inactivity).                     |
| **Heartbeats**           | Send `ping` every 30s; expect `pong` within 5s (RFC 6455 §5.5.2).                |

**Example Heartbeat:**
```javascript
// Client
setInterval(() => {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);

// Server
ws.on('message', (data) => {
  if (data === '{ "type": "ping" }') {
    ws.send('{ "type": "pong" }'); // Acknowledge
  }
});
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Event Sourcing](link)** | Store state changes as immutable events for auditing/replay.                  | Migrate from polling-based event logs to WebSocket streams.                      |
| **[CQRS](link)**          | Separate read/write models for scalability.                                     | WebSocket endpoints serve read-heavy use cases (e.g., live dashboards).         |
| **[Serverless WebSockets](link)** | Deploy WebSocket handlers on-demand (e.g., AWS AppSync).               | Cost-efficient for sporadic traffic.                                            |
| **[WebSocket + gRPC](link)** | Combine WebSocket for real-time + gRPC for structured RPC.               | Polyglot architecture (e.g., mobile clients).                                   |
| **[Rate Limiting](link)** | Throttle WebSocket connections to prevent abuse.                            | High-traffic APIs (e.g., stock tickers).                                       |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**               | **Cause**                          | **Mitigation**                                                                 |
|---------------------------|------------------------------------|---------------------------------------------------------------------------------|
| **Connection Storms**     | Clients reconnecting aggressively after drops. | Implement exponential backoff + jitter.                                          |
| **Memory Leaks**          | Unclosed WebSocket instances.        | Use garbage-collectable references (e.g., ` WeakSet` in Node.js).               |
| **Cross-Origin Issues**   | CORS misconfiguration.               | Set `Access-Control-Allow-Origin` + `Sec-WebSocket-Origin` headers.              |
| **Binary Frame Masking**  | Non-compliant clients blocking messages. | Use `permessage-deflate` or validate client capability.                        |
| **No Fallback Path**      | Browser blocks WebSockets.           | Use `socket.io` or HTTP long-polling as a secondary transport.                   |
| **Scalability Bottlenecks** | High CPU usage (e.g., unoptimized JSON parsing). | Batch messages; use Protocol Buffers for binary data.                          |

---

## **Tools & Libraries**
| **Category**              | **Tools/Libraries**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------|
| **Client-Side**          | `WebSocket` (native), `socket.io-client`, `ws` (Node.js), `Stomp.js` (STOMP over WS). |
| **Server-Side**          | `ws` (Node.js), `uWebSockets.js`, `websockets.py` (Python), `Spring WebSocket` (Java). |
| **Load Testing**         | `wrk`, `k6`, `Artillery`.                                                          |
| **Monitoring**           | `Prometheus` + `Grafana`, `Datadog`, `New Relic`.                                  |
| **Security**             | `OWASP ZAP`, `Nmap` (port scanning), `TLS Checker`.                                 |
| **Protocol Buffers**     | `protobufjs` (client), `protoc` (server).                                         |

---

## **Further Reading**
- [RFC 6455: The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [Socket.IO Docs](https://socket.io/docs/v4/)
- [WebSocket Security Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)
- [Redis Pub/Sub for WebSocket Scaling](https://redis.io/topics/pubsub)