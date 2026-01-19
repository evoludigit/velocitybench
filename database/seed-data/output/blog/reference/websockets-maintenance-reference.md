# **[Pattern] Websockets Maintenance – Reference Guide**

---

## **Overview**
The **Websockets Maintenance** pattern ensures reliable persistent connections between clients and servers over WebSocket protocols. Unlike traditional HTTP requests, WebSockets enable real-time, two-way communication with low latency, ideal for applications requiring live updates (e.g., chat apps, financial tickers, or IoT dashboards).

This pattern addresses **connection stability**, **graceful degradation**, **reconnection logic**, and **bandwidth optimization** while handling edge cases like server restarts, network interruptions, or client disconnects. Implementations must balance **latency** vs. **reliability**, ensuring clients can recover seamlessly from failures while minimizing resource overhead.

Key components include:
- **WebSocket handshake** (upgrade from HTTP to WebSocket).
- **Ping/Pong frames** (keepalive mechanism to detect dead connections).
- **Reconnection algorithms** (exponential backoff, jitter).
- **Session management** (tracking active connections, reconnect throttling).
- **Client-side retransmission** (for failed messages).

---

## **Implementation Details**

### **1. Core Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **WebSocket Protocol**    | RFC 6455 standard enabling full-duplex communication over a single TCP connection.                                                                                                                           |
| **Connection Lifecycle** | `CONNECTING` → `OPEN` → `CLOSING` → `CLOSED` (with optional `ERROR` state for failures).                                                                                                                      |
| **Ping/Pong Frames**      | Used to detect dead connections if no traffic occurs within a configurable timeout (e.g., 30 seconds).                                                                                                          |
| **Reconnection Strategy** | Automatic retries with backoff (e.g., 1s, 3s, 5s, 8s...) to avoid overwhelming the server during outages.                                                                                                       |
| **Message Retransmission**| Failed messages (e.g., due to `CLOSE` events) are queued client-side and resent upon reconnection.                                                                                                             |
| **Server-Side Tracking**  | Servers maintain connection metadata (e.g., last activity, IP, user agent) for debugging and rate-limiting.                                                                                                       |
| **Close Codes**           | Standardized reasons for connection termination (e.g., `1008: Policy Violation`, `1001: Going Away`).                                                                                                         |
| **Scalability**           | Horizontal scaling requires shared session stores (e.g., Redis) or sticky sessions to prevent split-brain scenarios.                                                                                       |
| **Security**              | TLS (wss://) encryption, origin validation, and rate-limiting to prevent abuse.                                                                                                                                   |

---

### **2. Schema Reference**
*(Key data structures for Websockets Maintenance)*

| **Component**            | **Schema**                                                                                                                                                                                                 | **Notes**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **WebSocket URL**        | `wss://{host}:{port}/{path}?token={authToken}`                                                                                                                                                              | Use `wss://` for secure connections.                                                           |
| **Connection Metadata**  | ```json                                                                                                                                                                                      {                                                                   "id": "ws-123",                                                                   "userId": "user-456",                                                                   "lastActive": "2024-05-20T12:00:00Z",                                                                      "ip": "192.168.1.1",                                                                       "reconnectAttempts": 3,                                                                   "maxRetries": 5                                                                   }```                                                                       | Tracked server-side for analytics and reconnection logic.                                      |
| **Ping/Pong Payload**    | `Ping`: `{"type": "ping", "timestamp": ISO8601}`<br>`Pong`: `{"type": "pong", "responseTo": "ping-id"}`                                                                                                      | Clients must respond within `pongTimeout` (default: 25s).                                    |
| **Reconnection Config**  | ```json                                                                                                                                                                                      {                                                                   "baseDelayMs": 1000,                                                                     "maxDelayMs": 30000,                                                                     "jitter": 0.5,                                                                         "exponential": true                                                                   }```                                                                       | `jitter` adds randomness to avoid thundering herd during outages.                             |
| **Message Retry Queue**  | ```json                                                                                                                                                                                      {                                                                   "queue": [                                                                       {"id": "msg-1", "payload": "data", "attempts": 1, "retries": 3},                                                                       {"id": "msg-2", "payload": {"critical": true}, "retries": 5}                                                                   ],                                                                   "maxQueueSize": 100                                                                   }```                                                                       | Prioritize `critical` messages via `retries` and `queue` limits.                             |
| **Close Event**          | ```json                                                                                                                                                                                      {                                                                   "code": 1000,                                                                     "reason": "Normal Closure",                                                                     "wasClean": true,                                                                       "retentionPeriodMs": 30000                                                                   }```                                                                       | `wasClean=false` indicates an abrupt disconnect (e.g., network drop).                         |

---

### **3. Query Examples**
*(Client-Side Implementation Snippets)*

#### **A. Establishing a WebSocket Connection**
```javascript
// JavaScript (browser/client)
const socket = new WebSocket("wss://api.example.com/ws/maintenance", {
  reconnectInterval: 1000,
  connectionTimeout: 10000,
  maxRetries: 5,
  onopen: () => console.log("Connected!"),
  onclose: (e) => {
    if (e.code !== 1000) { // Ignore normal closures
      console.error("Disconnected:", e.reason);
      reconnect(); // Trigger exponential backoff
    }
  },
});
```

#### **B. Handling Ping/Pong**
```javascript
socket.onmessage = (event) => {
  if (event.data.type === "ping") {
    socket.send(JSON.stringify({
      type: "pong",
      responseTo: event.data.id
    }));
  }
};

// Server expects pong within 25s; otherwise, closes the connection.
```

#### **C. Reconnection Logic (Exponential Backoff)**
```javascript
let retryCount = 0;
const MAX_RETRIES = 5;
const BASE_DELAY_MS = 1000;

function reconnect() {
  if (retryCount >= MAX_RETRY) return; // Give up
  const delay = BASE_DELAY_MS * Math.pow(2, retryCount) + Math.random() * 1000;
  retryCount++;
  setTimeout(() => {
    socket.close(); // Force reconnect
    socket = new WebSocket("wss://api.example.com/ws/maintenance");
  }, delay);
}
```

#### **D. Message Retransmission**
```javascript
const messageQueue = [];

socket.sendWithRetry = (message) => {
  const msgId = `msg-${Date.now()}`;
  socket.send(message);
  messageQueue.push({ id: msgId, payload: message, attempts: 1 });
};

socket.onclose = (e) => {
  // Retry failed messages after reconnect
  setTimeout(() => {
    messageQueue.forEach(msg => {
      if (msg.attempts < 5) {
        socket.send(msg.payload);
        msg.attempts++;
      }
    });
  }, 1000);
};
```

#### **E. Server-Side Ping Logic (Node.js)**
```javascript
// Server (e.g., using `ws` library)
const WebSocket = require("ws");
const wss = new WebSocket.Server({ port: 8080 });

wss.on("connection", (ws) => {
  ws.isAlive = true;
  ws.on("pong", () => ws.isAlive = true);

  // Ping client every 30s
  setInterval(() => {
    ws.send(JSON.stringify({ type: "ping", timestamp: Date.now() }));
  }, 30000);

  ws.on("close", () => {
    clearInterval(ws.interval);
  });
});
```

---

### **4. Error Handling & Edge Cases**
| **Scenario**               | **Solution**                                                                                                                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Network Outage**         | Client implements exponential backoff with jitter. Server logs disconnected IPs for manual review.                                                                                                         |
| **Server Restart**         | Use a shared session store (Redis) to restore state. Clients reconnect automatically.                                                                                                                    |
| **Client Disconnect**      | Server detects via `pongTimeout` and closes gracefully. Client retries with backoff.                                                                                                                         |
| **Message Timeout**        | Clients resend failed messages (with increasing delays). Servers acknowledge receipt via `ack` frames.                                                                                                     |
| **Rate Limiting**          | Server tracks `lastActive` and `reconnectAttempts`; blocks clients exceeding `maxRetries`.                                                                                                                   |
| **TLS Handshake Failure**  | Fallback to HTTP long-polling for legacy clients (with a warning).                                                                                                                                          |
| **Memory Leaks**           | Server cleans up `ws.on("close")` callbacks and client-side `setInterval` timers.                                                                                                                         |

---

### **5. Benchmarking & Optimization**
| **Metric**               | **Target**                          | **Optimization**                                                                                     |
|--------------------------|-------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Latency**              | <100ms ping-pong                     | Enable `persistentConnection: true` in WebSocket implementations.                                    |
| **Throughput**           | 10K+ concurrent connections         | Use `ws` (Node.js) or `FastWebSocket` (Go) for high-scale servers.                                    |
| **Reconnection Time**    | <5s median                           | Minimize `baseDelayMs` and reduce `jitter` for critical systems.                                       |
| **Memory Usage**         | <10MB per 10K connections           | Implement connection pruning for idle clients (`lastActive` + timeout).                               |
| **Message Duplication**  | <1%                                 | Use sequence IDs or client-side deduplication for retries.                                             |

---

### **6. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Webhooks](https://example.com/webhooks)** | Alternative to WebSockets for event-driven architectures (server initiates push to client). Ideal for one-time notifications (e.g., order updates).                   |
| **[HTTP Long-Polling](https://example.com/http-long-polling)** | Fallback for clients without WebSocket support. Higher latency but simpler to debug.                                                                                              |
| **[Server-Sent Events (SSE)](https://example.com/sse)**   | Unidirectional (server→client) streaming via HTTP. Simpler than WebSockets but lacks duplex communication.                                                                                         |
| **[Rate Limiting](https://example.com/rate-limiting)**   | Complementary pattern to prevent abuse in WebSocket APIs (e.g., `reconnectAttempts` limit).                                                                                                    |
| **[Circuit Breaker](https://example.com/circuit-breaker)** | Server-side pattern to gracefully degrade if WebSocket connections overload (e.g., queue messages during outages).                                                                               |
| **[Session Affinity](https://example.com/session-affinity)** | Ensures a client’s WebSocket connections always route to the same server node (critical for stateful apps).                                                                                     |

---
### **7. Tools & Libraries**
| **Language/Tool**         | **Library**                          | **Features**                                                                                          |
|---------------------------|--------------------------------------|-------------------------------------------------------------------------------------------------------|
| **JavaScript (Browser)**  | `WebSocket` (native)                | Standard API; use `EventSource` for fallback.                                                          |
| **Node.js**               | [`ws`](https://github.com/websockets/ws) | High-performance server library with ping/pong support.                                               |
| **Python**                | [`websockets`](https://github.com/aaugustin/websockets) | Async/await support; built-in connection tracking.                                                    |
| **Go**                    | [`gorilla/websocket`](https://github.com/gorilla/websocket) | Optimized for high concurrency; includes compression.                                                 |
| **Java**                  | [`Java WebSocket (Tomcat)](https://tomcat.apache.org/)** | Embedded in servers like WildFly or Tomcat.                                                            |
| **Monitoring**            | `Prometheus` + `Grafana`             | Track `ws_connections_active`, `ws_messages_received`, `ws_pings_failed`.                              |
| **Testing**               | [`WebSocket++`](https://github.com/websocketspp/websocketpp) | Protocols testing framework for C++.                                                                   |

---
### **8. Anti-Patterns to Avoid**
1. **No Reconnection Logic**
   - *Problem*: Clients hang indefinitely after network drops.
   - *Fix*: Always implement exponential backoff.

2. **Ignoring Ping/Pong**
   - *Problem*: Server marks connections as dead due to inactivity, even if clients are alive.
   - *Fix*: Enable `pingInterval` (e.g., 30s) and handle `pong` events.

3. **Unbounded Retries**
   - *Problem*: Clients retry indefinitely, causing server overload.
   - *Fix*: Set `maxRetries` and `reconnectAttempts` thresholds.

4. **No Message Deduplication**
   - *Problem*: Duplicate messages on reconnects clutter logs and UI.
   - *Fix*: Use message IDs or timestamps for idempotency.

5. **Hardcoded Timeouts**
   - *Problem*: Timeouts too short cause false positives; too long waste resources.
   - *Fix*: Dynamically adjust based on network conditions (e.g., `navigator.connection`).

---
### **9. Troubleshooting**
| **Issue**                 | **Diagnosis**                                                                 | **Solution**                                                                                       |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Clients can’t connect** | Check CORS headers (`Access-Control-Allow-Origin`).                          | Ensure server responds with `Sec-WebSocket-Accept` header.                                         |
| **Pings fail**            | `pongTimeout` too short or client not responding.                           | Increase timeout (e.g., 45s) or debug client-side `onmessage`.                                    |
| **High memory usage**     | Server not closing idle connections.                                        | Implement `ws.on("close", () => {})` cleanup and prune stale sessions.                             |
| **Messages lost**         | Client disconnected mid-message.                                             | Enable message queuing on both client/server and retry on reconnect.                              |
| **Race conditions**       | Multiple reconnect attempts overlap.                                        | Use `setTimeout` with unique IDs to avoid duplicate handlers.                                     |

---
### **10. Further Reading**
- [RFC 6455 – The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [MDN WebSocket Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [WebSocket Security Best Practices](https://security.type-system.com/web-sockets-security/)
- [Exponential Backoff in Distributed Systems](https://www.awsarchitectureblog.com/2015/03/backoff.html)