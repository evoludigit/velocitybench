# **Debugging WebSocket Profiling: A Troubleshooting Guide**

WebSocket Profiling is used to monitor real-time application performance, track long-lived connections, and analyze latency, throughput, and error patterns in interactive applications (e.g., chat, live dashboards, gaming). This guide focuses on diagnosing common issues, optimizing WebSocket profiling, and preventing performance degradation.

---

## **1. Symptom Checklist**
Before diving into debugging, identify if the issue aligns with these symptoms:

| **Issue Type**               | **Symptoms**                                                                 |
|------------------------------|------------------------------------------------------------------------------|
| **Connection Failures**      | WebSocket handshake fails, `onerror` fires, or no `onopen` callback.       |
| **High Latency**             | Messages take >200ms to transmit; visual lag in real-time apps.             |
| **Connection Drops**         | Frequent `onclose` events; reconnection loops.                             |
| **Memory Leaks**             | Server-side memory usage grows uncontrollably with more WebSocket connections. |
| **Message Processing Bottlenecks** | Messages are lost or processed too slowly; `onmessage` queue backlog.   |
| **Authentication Failures**  | Invalid token errors, 403/401 responses; `AuthenticatorError` in client.      |
| **Heartbeat Issues**         | Server or client fails to send/receive pings (WebSocket ping/pong).         |
| **Scalability Problems**     | Performance degrades under load (e.g., >10K concurrent connections).         |
| **Logging/Monitoring Gaps**  | Missing WebSocket-related logs or metrics in observability tools.            |

---

## **2. Common Issues and Fixes**

### **Issue 1: WebSocket Handshake Failures**
**Symptoms:**
- Client fails to connect (`onopen` never triggers).
- Server logs show `101 Switching Protocols` errors or `400 Bad Request`.
- Browser DevTools: `WebSocket connection failed: WebSocket is closed before the connection is established`.

**Root Causes:**
- Incorrect URL (must include `ws://` or `wss://`).
- Missing or malformed protocol header (e.g., `Sec-WebSocket-Protocol`).
- CORS misconfiguration.
- Firewall/proxy blocking WebSocket traffic.

**Debugging Steps & Fixes:**
1. **Verify the WebSocket URL:**
   ```javascript
   // Correct format (client-side)
   const socket = new WebSocket("wss://yourdomain.com/api/socket", ["protocol-v1"]);
   ```
2. **Check Server Headers:**
   Ensure the server responds with:
   ```
   HTTP/1.1 101 Switching Protocols
   Connection: Upgrade
   Upgrade: websocket
   Sec-WebSocket-Accept: <correct-accept-string>
   Sec-WebSocket-Protocol: protocol-v1
   ```
   **Example (Node.js with `ws` library):**
   ```javascript
   const WebSocket = require('ws');
   const wss = new WebSocket.Server({ port: 8080 });

   wss.on('connection', (ws) => {
     ws.on('upgrade', (req, socket, head) => {
       const protocols = req.headers['sec-websocket-protocol']?.split(',') || [];
       socket.upgrade(req, head, false, protocols);
     });
   });
   ```
3. **CORS Configuration (Server-Side):**
   ```javascript
   // Express.js example
   app.use((req, res, next) => {
     res.header("Access-Control-Allow-Origin", "*");
     res.header("Access-Control-Allow-Methods", "GET, OPTIONS, WS");
     next();
   });
   ```
4. **Firewall/Proxy Check:**
   - Ensure ports `80` (HTTP) or `443` (HTTPS) allow WebSocket traffic.
   - Test with `telnet` or `curl`:
     ```bash
     curl -v ws://yourdomain.com/api/socket
     ```

---

### **Issue 2: High Latency in WebSocket Messages**
**Symptoms:**
- Real-time updates appear delayed (>500ms).
- `performance.now()` shows inconsistent message transmission times.

**Root Causes:**
- Large payloads (>16KB; WebSocket fragments messages automatically but adds overhead).
- Network congestion (e.g., load balancers, CDN misconfigurations).
- Server-side blocking (e.g., database queries slowing message processing).

**Debugging Steps & Fixes:**
1. **Optimize Payload Size:**
   - Compress messages (e.g., gzip, Brotli) or use JSON/Protobuf serialization.
   ```javascript
   // Client-side compression (browser)
   const compressedData = pako.deflate(JSON.stringify(data));

   // Server-side decompression
   const decompressedData = pako.inflate(ws.buffer);
   ```
2. **Check Network Path:**
   - Use `curl` or `wget` to benchmark latency:
     ```bash
     curl -v -X POST ws://yourdomain.com/api/socket --data-binary '{"test":1}'
     ```
   - Test with a local proxy (e.g., `mitmproxy`) to detect delays.
3. **Server-Side Bottlenecks:**
   - Profile CPU usage with `top` or `htop` during peak traffic.
   - Use APM tools (e.g., New Relic, Datadog) to identify slow endpoints.
   ```javascript
   // Example: Rate-limit message processing
   const messageQueue = [];
   let isProcessing = false;

   ws.on('message', (data) => {
     messageQueue.push(data);
     if (!isProcessing) {
       processNext();
     }
   });

   async function processNext() {
     isProcessing = true;
     const msg = messageQueue.shift();
     await slowOperation(msg); // Replace with your logic
     isProcessing = false;
     if (messageQueue.length > 0) processNext();
   }
   ```

---

### **Issue 3: Connection Drops Without Reason**
**Symptoms:**
- Sudden `onclose` events with no error message (code `1006`).
- Client reconnects automatically but fails repeatedly.

**Root Causes:**
- **Server-side:**
  - Unhandled exceptions in WebSocket listeners.
  - Timeout due to `ServerTimeout` or `Keep-Alive` misconfiguration.
  - OS-level kills (`OOM` or `ulimit` exhaustion).
- **Client-side:**
  - Network instability (e.g., mobile data drops).
  - Browser tab closed or `visibilitychange` event triggers disconnection.

**Debugging Steps & Fixes:**
1. **Server-Side Logging:**
   Capture full stack traces for dropped connections:
   ```javascript
   wss.on('connection', (ws) => {
     ws.on('close', (code, reason) => {
       console.error(`Connection closed: ${code} - ${reason}`);
       // Send error to monitoring system
       sendToMonitoring({ event: 'websocket_close', code, reason });
     });
     ws.on('error', (err) => console.error('WebSocket Error:', err));
   });
   ```
2. **Enable WebSocket Heartbeats:**
   Detect silent drops by sending periodic pings:
   ```javascript
   // Client-side
   setInterval(() => {
     if (socket.readyState === WebSocket.OPEN) {
       socket.send(JSON.stringify({ type: 'heartbeat' }));
     }
   }, 30000);

   // Server-side
   ws.on('message', (data) => {
     if (data === 'heartbeat') {
       ws.send('pong');
     }
   });
   ```
3. **Auto-Reconnect Logic (Client-Side):**
   ```javascript
   let reconnectAttempts = 0;
   const maxAttempts = 5;
   const delay = ( attempt ) => Math.pow(2, attempt) * 1000;

   ws.onclose = () => {
     if (reconnectAttempts < maxAttempts) {
       setTimeout(() => {
         ws = new WebSocket("wss://yourdomain.com/api/socket");
         reconnectAttempts++;
       }, delay(reconnectAttempts));
     }
   };
   ```
4. **OS-Level Checks:**
   - Monitor `netstat` for dropped connections:
     ```bash
     netstat -an | grep ESTABLISHED | grep 8080
     ```
   - Increase file descriptor limits (Linux):
     ```bash
     ulimit -n 65536
     ```

---

### **Issue 4: Memory Leaks in WebSocket Servers**
**Symptoms:**
- Server memory grows linearly with connections.
- Garbage collection (`gc`) logs show no reduction in heap usage.

**Root Causes:**
- Unclosed WebSocket connections (`ws.close()` not called).
- Storing references to all sockets (e.g., in a global array).
- Buffer accumulation from unread messages.

**Debugging Steps & Fixes:**
1. **Track Active Connections:**
   ```javascript
   const activeConnections = new Set();
   wss.on('connection', (ws) => {
     activeConnections.add(ws);
     ws.on('close', () => activeConnections.delete(ws));
   });
   ```
2. **Force Garbage Collection (Node.js):**
   ```javascript
   setInterval(() => {
     global.gc(); // Not recommended for production (use heap snaps instead)
   }, 60000);
   ```
   Better: Use **Heap Snapshots** in Chrome DevTools or tools like `heapdump`:
   ```bash
   node --inspect-brk server.js && heapdump --pid <pid>
   ```
3. **Limit Connection Count:**
   ```javascript
   if (activeConnections.size > 10000) {
     ws.close(1001, 'Server overload');
   }
   ```
4. **Use a Connection Pool:**
   - Offload WebSocket handling to a message queue (e.g., Redis, RabbitMQ).
   - Example with Redis:
     ```javascript
     const redis = require('redis');
     const pubClient = redis.createClient();
     const subClient = redis.createClient();

     subClient.on('message', (channel, message) => {
       // Process async and respond via pub/sub
     });

     ws.on('message', (data) => {
       pubClient.publish('websocket_channel', JSON.stringify(data));
     });
     ```

---

### **Issue 5: Authentication Failures**
**Symptoms:**
- `onopen` fails with `1008 (Policy Violation)` or `403 Forbidden`.
- Server logs show invalid tokens.

**Root Causes:**
- Missing/tampered JWT tokens.
- Misconfigured `Sec-WebSocket-Extensions` (e.g., token passed incorrectly).
- Server auth middleware blocking connections.

**Debugging Steps & Fixes:**
1. **Log Authentication Headers:**
   ```javascript
   wss.on('connection', (ws, req) => {
     const token = req.headers['sec-websocket-protocol'];
     console.log('Received token:', token);
     if (!validateToken(token)) {
       ws.close(1008, 'Invalid token');
     }
   });
   ```
2. **Pass Token via Subprotocol:**
   ```javascript
   // Client
   const socket = new WebSocket('wss://yourdomain.com/api/socket', ['token=' + encodeURIComponent(token)]);

   // Server
   ws.on('upgrade', (req, socket, head) => {
     const token = req.headers['sec-websocket-protocol'].split('=')[1];
     if (!validateToken(token)) {
       socket.destroy();
       return;
     }
     socket.upgrade(req, head, false, ['token=' + token]);
   });
   ```
3. **Use HTTPS + Token in Cookies:**
   - Avoid passing tokens in headers (vulnerable to MITM).
   - Example (Express + `ws`):
     ```javascript
     app.use(cookieParser());
     wss.on('connection', (ws, req) => {
       const token = req.cookies['auth_token'];
       if (!token) ws.close(1008, 'No token');
     });
     ```

---

## **3. Debugging Tools and Techniques**
| **Tool**               | **Purpose**                                                                 | **Example Usage**                          |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **Browser DevTools**   | Inspect WebSocket traffic, headers, and events.                             | Open F12 → Network → WS tab.               |
| **Wireshark**          | Capture raw WebSocket frames (advanced).                                    | `tshark -i any port 8080`                  |
| **WebSocket Debugger** | Chrome extension to log messages in real-time.                              | [WebSocket Debugger](https://chrome.google.com/webstore/detail/websocket-debugger-pro/hmhgeddbpknejadmpffkdohmdjchhcaa) |
| **NetData**            | Monitor real-time network traffic and WebSocket metrics.                     | `sudo ./netdata-start.sh`                  |
| **Prometheus + Grafana** | Track WebSocket metrics (connections, latency, errors) via custom exporters. | Configure `ws_exporter` for Node.js.       |
| **Heap Snapshots**     | Detect memory leaks in Node.js.                                             | `node --inspect server.js` + DevTools      |
| **Mitmproxy**          | Intercept and modify WebSocket traffic (for testing).                       | `mitmproxy -s websocket_script.py`         |
| **Socket.IO Debugger** | If using Socket.IO, enable debug mode:                                     | `socket.io(io, { transports: ['websocket'], force new: true });` with `io.use(logger);` |

**Example Debug Workflow:**
1. Open **DevTools → Network → WS tab** to see connection state.
2. Use **Wireshark** to filter WebSocket frames:
   ```
   tcp port 8080 and ws
   ```
3. Monitor **Prometheus metrics** for `websocket_opened`, `websocket_closed`, and `websocket_errors`.

---

## **4. Prevention Strategies**
### **Server-Side Optimizations**
1. **Rate Limiting:**
   ```javascript
   const rateLimit = new RateLimiter({
     windowMs: 15 * 60 * 1000, // 15 minutes
     max: 1000,                 // Max 1000 connections per IP
   });

   wss.on('connection', async (ws, req) => {
     const ip = req.socket.remoteAddress;
     try {
       await rateLimit.add(ip);
     } catch {
       ws.close(1003, 'Rate limit exceeded');
     }
   });
   ```
2. **Graceful Shutdown:**
   ```javascript
   process.on('SIGTERM', () => {
     wss.clients.forEach((client) => client.close(1001, 'Server shutting down'));
     process.exit(0);
   });
   ```
3. **Use a WebSocket Library with Built-in Safeguards:**
   - **Socket.IO** (handles reconnects, rooms, namespaces).
   - **Fastify-WebSocket** (low overhead, supports clustering).

### **Client-Side Best Practices**
1. **Connection Management:**
   ```javascript
   const socket = new WebSocket('wss://yourdomain.com/api/socket', {
     maxPayload: 1024 * 1024, // 1MB max payload
     perMessageDeflate: true,  // Enable compression
   });
   ```
2. **Offload Heavy Processing:**
   - Use **Web Workers** for parsing large messages.
3. **Batch Messages:**
   ```javascript
   const messageQueue = [];
   let isSending = false;

   function sendQueued() {
     if (messageQueue.length === 0 || isSending) return;
     isSending = true;
     const msg = messageQueue.shift();
     socket.send(msg);
     isSending = false;
   }
   ```

### **Monitoring and Alerting**
1. **Key Metrics to Track:**
   - `websocket_connections` (total active).
   - `websocket_latency` (avg time from send to receive).
   - `websocket_errors` (drops, auth failures).
   - `memory_usage` (Node.js heap growth).
2. **Alerting Rules (Prometheus Example):**
   ```
   alert: HighWebSocketLatency
     if (rate(websocket_latency_seconds{job="websocket"}[1m]) > 0.5)
     for 5m
     labels: { severity: "warning" }
   ```
3. **Automated Recovery:**
   - Use **Kubernetes** liveness probes for WebSocket endpoints.
   - Example `deployment.yaml`:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 30
       periodSeconds: 10
     ```

---

## **5. Summary Checklist for Quick Resolution**
| **Step**                  | **Action**                                                                 |
|---------------------------|----------------------------------------------------------------------------|
| **Handshake Failures**    | Verify URL, CORS, and headers; test with `curl`.                           |
| **Latency Issues**        | Compress messages, test network path, optimize server bottlenecks.        |
| **Connection Drops**      | Enable heartbeats, log close reasons, check OS/network stability.          |
| **Memory Leaks**          | Track active connections, force GC (carefully), use connection pools.     |
| **Auth Failures**         | Log tokens, pass via subprotocol, use HTTPS + cookies.                    |
| **General Debugging**     | Use DevTools, Wireshark, Prometheus, and heap snapshots.                   |
| **Prevention**            | Rate-limit, batch messages, monitor metrics, auto-reconnect clients.      |

---
**Final Notes:**
- WebSocket debugging often requires **end-to-end tracing** (client → browser → network → server → DB).
- **Isolate issues** by testing with a minimal client (e.g., `wscat`):
  ```bash
  npm install -g wscat
  wscat -c wss://yourdomain.com/api/socket
  ```
- For **high-scale systems**, consider **dedicated WebSocket load balancers** (e.g., NGINX WebSocket module).