# **[Pattern] WebSockets "Gotchas" Reference Guide**

---

## **Overview**
WebSockets enable **real-time, persistent, bidirectional** communication between clients and servers, but their asynchronous nature introduces subtle bugs and edge cases. This guide documents common pitfalls—*"gotchas"*—that cause failures, performance issues, or security vulnerabilities in WebSocket implementations. Addressing these issues ensures reliable, scalable, and secure WebSocket-based applications.

---

## **Key Concepts & Implementation Details**
WebSockets operate under these core assumptions, which often lead to unexpected behavior:

| **Concept**               | **Details**                                                                                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Handshake**             | Requires `HTTP Upgrade` header (`"Upgrade: websocket"`) and `Sec-WebSocket-Key` validation. Failure to comply (e.g., missing headers, invalid keys) causes connection drops.                              |
| **Connection Management** | Servers must handle disconnections (`close` frame) gracefully. Clients must respect the `Connection: keep-alive` (or lack thereof) from the server.                                                       |
| **Frame Structure**       | Messages are fragmented into **frames**, each with a **payload**, **masking** (client-side), and **opcode** (e.g., `0x1` for text, `0x8` for close). Misinterpretation causes corrupt data or crashes.      |
| **Asynchronous Nature**   | WebSockets are **fire-and-forget**. Missing acknowledgments or race conditions between events can lead to missing data or duplicate processing.                                                         |
| **Security Constraints**  | **Masking**: Only client-side frames are masked (to prevent MITM attacks). Servers must **strip masks**. **Subprotocols**: Must be negotiated in the handshake (`Sec-WebSocket-Protocol`).                       |
| **Heartbeats**            | Servers/clients may send **ping/pong** frames to detect dead connections. Timeout configurations (e.g., 30s) must align between peers.                                                               |
| **Buffering**             | Unread messages accumulate in memory. Clients must **acknowledge** receipt (e.g., via `onmessage` handlers) to prevent memory exhaustion.                                                           |
| **Scalability Limits**    | Each connection consumes server resources. Excessive connections may overload the system. **Connection pooling** or **session-based routing** may be needed.                                           |

---

## **Schema Reference**
Common WebSocket "gotchas" and their root causes:

| **Category**               | **Gotcha**                                                                               | **Root Cause**                                                                                                                                                                                                 | **Mitigation**                                                                                                                                                                                                 |
|----------------------------|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Handshake**              | Client/server fails to complete handshake.                                               | Missing `Upgrade` header, invalid `Sec-WebSocket-Key`, or unsupported subprotocol.                                                                                                                              | Verify headers before sending responses; log handshake failures.                                                                                                                                                     |
| **Connection State**       | Clients assume connection is always "open."                                             | Server drops connections (e.g., due to inactivity).                                                                                                                                                          | Implement reconnection logic with exponential backoff.                                                                                                                                                              |
| **Message Processing**     | `onmessage` callback triggered **after** buffer overflow.                                 | Client doesn’t read messages quickly enough; server buffers exceed limits.                                                                                                                                      | Use `textDecoder`/`DataView` for incremental parsing; set `maxPayloadSize` in server libs (e.g., `ws` module).                                                                                              |
| **Frame Corruption**       | Received frames are malformed or incomplete.                                             | Network issues, improper masking, or opcode misinterpretation.                                                                                                                                                   | Validate frame headers; retry corrupted messages.                                                                                                                                                                  |
| **Security Risks**         | Unmasked server frames or unnegotiated subprotocols.                                      | Missing mask verification or subprotocol headers.                                                                                                                                                             | Enforce masking on client frames; validate `Sec-WebSocket-Protocol`.                                                                                                                                                   |
| **Heartbeat Failures**     | Timeout before ping/pong exchange is detected.                                           | Mismatched heartbeat intervals or network latency.                                                                                                                                                              | Set conservative timeouts (e.g., 60s) and log ping/pong roundtrip times.                                                                                                                                                  |
| **Resource Leaks**         | Unclosed connections or unread buffers.                                                  | Forgetting to call `socket.close()` or `socket.onclose`.                                                                                                                                                      | Use `finally` blocks or async/await with `try-finally`.                                                                                                                                                          |
| **Cross-Origin Issues**    | CORS preflight fails due to `Upgrade` header restrictions.                                | Browsers block handshake attempts unless `Access-Control-Allow-Origin` includes WebSocket endpoints.                                                                                                          | Configure CORS headers for WebSocket paths (`/ws/*`).                                                                                                                                                              |
| **Scalability Bottlenecks**| Server overwhelmed by many connections.                                                   | No connection limits or reuse (e.g., TCP keep-alive).                                                                                                                                                         | Use connection pooling; limit concurrent connections per client.                                                                                                                                                      |
| **Protocol Violations**    | Closing handshake sent without `reason` or `code`.                                       | Invalid `close` frame (missing or misconfigured).                                                                                                                                                              | Always include `code` (e.g., `1008: Policy Violation`) and `reason` in close frames.                                                                                                                                |
| **Browser Quirks**         | `WebSocket` API misbehaves in legacy browsers.                                           | Lack of WebSocket support; race conditions in `onopen`/`onerror`.                                                                                                                                                 | Feature detection; graceful degradation to long-polling.                                                                                                                                                            |

---

## **Query Examples**
### **Debugging Handshake Failures**
**Scenario**: Client fails to connect.
**Check**:
```javascript
// Verify HTTP headers before handshake
console.log(response.headers.get("Upgrade"), response.headers.get("Sec-WebSocket-Accept"));
```
**Expected**:
- `Upgrade: websocket`
- `Sec-WebSocket-Accept: [SHA1-hash-of-key]`

---

### **Detecting Buffer Overflows**
**Scenario**: Server buffers grow indefinitely.
**Check**:
```javascript
// Monitor incoming bytes
const WebSocket = require("ws");
const wss = new WebSocket.Server({ maxPayload: 1024 * 1024 }); // 1MB limit

wss.on("connection", (ws) => {
  ws.on("message", (data) => {
    if (data.length > maxPayload) {
      ws.close(1009, "Message too large"); // Protocol Error
    }
  });
});
```

---

### **Testing Heartbeat Failures**
**Scenario**: Connection times out before pong.
**Check**:
```javascript
// Client-side ping/pong with timeout
const socket = new WebSocket("ws://example.com");
let lastPong = Date.now();

socket.onopen = () => {
  setInterval(() => {
    socket.send("\x04"); // Ping
    lastPong = Date.now();
  }, 20000);

  socket.onmessage = (e) => {
    if (e.data === "\x05") { // Pong
      console.log("Pong received:", Date.now() - lastPong);
    }
  };
};

socket.onclose = () => {
  if (Date.now() - lastPong > 30000) {
    console.error("Heartbeat timeout!");
  }
};
```

---

### **Validating Subprotocol Negotiation**
**Scenario**: Server ignores `Sec-WebSocket-Protocol`.
**Check**:
```javascript
// Server-side subprotocol validation
const WebSocket = require("ws");
const wss = new WebSocket.Server({
  handleProtocols: (protocols) => {
    if (protocols.includes("chat")) {
      return "chat";
    }
    return false; // Reject
  }
});
```

---

### **Closing Connections Properly**
**Scenario**: Client disconnects without acknowledgment.
**Check**:
```javascript
// Client-side graceful close
socket.close(1000, "Leaving chat"); // 1000 = Normal Closure

// Server logs close reasons
socket.on("close", (code, reason) => {
  console.log(`Closed with code ${code}: ${reason}`);
});
```

---

## **Related Patterns**
1. **[Long-Polling Fallback]** – Use HTTP long-polling for browsers lacking WebSocket support.
   - *Example*: Detect `WebSocket` support with `try-catch`; fall back to AJAX if unavailable.
   ```javascript
   try {
     new WebSocket("ws://example.com");
   } catch (e) {
     useLongPolling();
   }
   ```

2. **[WebSocket + JWT Authentication]** – Secure WebSocket connections with JWT tokens.
   - *Gotcha*: Avoid sending tokens in `Upgrade` headers (use HTTP-first auth).
   - *Example*:
     ```javascript
     const token = localStorage.getItem("authToken");
     socket = new WebSocket(`ws://example.com?token=${token}`);
     ```

3. **[Pub/Sub Patterns]** – Use message brokers (e.g., Redis, RabbitMQ) for WebSocket relay.
   - *Gotcha*: Ensure broker supports WebSocket-like pub/sub (e.g., Redis Pub/Sub).
   - *Example*:
     ```javascript
     // Relay messages via Redis
     const redis = require("redis");
     const pub = redis.createClient();
     const sub = redis.createClient();

     sub.on("message", (channel, message) => {
       socket.send(message);
     });
     ```

4. **[Heartbeat Monitoring]** – Proactively detect dead connections.
   - *Tools*: Integrate with monitoring platforms (e.g., Prometheus) to track `ping/pong` latency.
   - *Example Metric*:
     ```yaml
     # Prometheus alert for heartbeat failures
     ALERT HighLatencyPing
       IF websocket_ping_latency_seconds > 5
       FOR 5m
     ```

5. **[Connection Pooling]** – Reuse WebSocket connections for efficiency.
   - *Gotcha*: Avoid connection leakage (e.g., forgetting to `close()`).
   - *Example*:
     ```javascript
     const connectionPool = new Map();
     function getOrCreateSocket(url) {
       if (!connectionPool.has(url)) {
         connectionPool.set(url, new WebSocket(url));
       }
       return connectionPool.get(url);
     }
     ```

---

## **Final Notes**
- **Testing**: Use tools like `wstest` (Node.js) or browser DevTools to inspect WebSocket traffic.
- **Logging**: Capture handshake failures, close reasons, and message sizes for debugging.
- **Security**: Always validate WebSocket endpoints in CORS policies and use TLS (`wss://`).

By addressing these gotchas, you can build **resilient, high-performance** WebSocket applications.