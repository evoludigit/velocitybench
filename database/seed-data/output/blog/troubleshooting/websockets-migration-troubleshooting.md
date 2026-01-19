# **Debugging Websockets Migration: A Troubleshooting Guide**

## **Introduction**
Websockets provide **real-time bidirectional communication** between client and server, but migrating to or troubleshooting Websockets in production can be tricky due to connection drops, scaling issues, and protocol quirks. This guide helps diagnose and resolve common problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|--------------------------------------------|
| ✅ Websocket connection drops intermittently | Firewall blocking, server crashes, client-side issues |
| ✅ High latency or lag in messages   | Poor server scaling, network congestion     |
| ✅ Failed handshake (1008/1006 errors) | Invalid protocol, HTTP proxy misconfiguration |
| ✅ Duplicate messages or missed updates | Client reconnection logic, server-side bugs |
| ✅ Inconsistent state between clients  | Eventual consistency not implemented       |
| ✅ High CPU/memory usage on server    | Unoptimized Websocket listeners            |

---

## **2. Common Issues & Fixes**

### **Issue 1: Connection Drops (1005/1006 Errors)**
**Symptoms:**
- Clients report "Connection closed unexpectedly."
- Server logs show `WebSocket connection dropped` (Node.js: `ws` library).

**Root Cause:**
- **Server crashes** (unhandled exceptions, OOM).
- **Network instability** (firewalls, load balancers terminating idle connections).
- **Client-side disconnects** (mobile devices, browser closed).

**Fixes:**

#### **A) Server-Side Stability (Node.js Example)**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('error', (err) => {
  console.error('WebSocket Server Error:', err);
  // Auto-reconnect logic (if using a load balancer)
  setTimeout(() => wss.handleUpgrade = () => {}, 1000);
});
```
**→ Ensure proper error handling** to prevent crashes.

#### **B) Keep-Alive & Heartbeats**
```javascript
// Enable ping/pong to detect dead connections
wss.on('connection', (ws) => {
  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });
});

setInterval(() => {
  wss.clients.forEach((ws) => {
    if (!ws.isAlive) return ws.terminate();
    ws.isAlive = false;
    ws.ping(() => {});
  });
}, 30000);
```
**→ Prevents stale connections.**

---

### **Issue 2: High Latency or Lag**
**Symptoms:**
- Real-time messages arrive delayed (e.g., chat messages not syncing instantly).
- `WebSocket` events fire unpredictably.

**Root Cause:**
- **Server overloaded** (too many concurrent connections).
- **Network bottlenecks** (CDN misconfiguration, slow clients).
- **Inefficient event loop** (blocking operations in WebSocket handlers).

**Fixes:**

#### **A) Optimize Server Scaling (Horizontal vs. Vertical)**
- **Vertical:** Upgrade CPU/RAM (e.g., AWS t3.medium → t3.large).
- **Horizontal:** Use a **WebSocket load balancer** (e.g., Kong, Nginx WebSocket module).

**Nginx WebSocket Load Balancing:**
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

#### **B) Non-Blocking WebSocket Handlers**
```javascript
wss.on('connection', (ws) => {
  ws.on('message', async (data) => {
    // Process data in a worker thread (avoid blocking event loop)
    const result = await processMessage(data);
    ws.send(JSON.stringify(result));
  });
});
```
**→ Use `worker_threads` or offload to a queue (BullMQ, RabbitMQ).**

---

### **Issue 3: Failed Handshake (1008/1006 Errors)**
**Symptoms:**
- Browser console logs:
  ```
  WebSocket connection to 'wss://example.com' failed: Error during WebSocket handshake: Unexpected response code: 400
  ```
- Server logs show `Invalid protocol` or `Handshake timeout`.

**Root Cause:**
- **HTTPS misconfiguration** (missing SNI, self-signed certs).
- **HTTP proxy blocking `Upgrade` header** (e.g., Cloudflare, AWS ALB).
- **Client sending unsupported subprotocols**.

**Fixes:**

#### **A) Verify SSL/TLS (Node.js Example)**
```javascript
const https = require('https');
const fs = require('fs');

const options = {
  key: fs.readFileSync('key.pem'),
  cert: fs.readFileSync('cert.pem'),
  allowHTTP1: true, // Required for WebSocket upgrades
};

const wss = new WebSocket.Server({ server: https.createServer(options), port: 443 });
```

#### **B) Allow Proxy-Friendly Headers**
```nginx
# Nginx: Ensure WebSocket headers are passed
location / {
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
}
```

---

### **Issue 4: Duplicate/Missed Messages**
**Symptoms:**
- Clients receive the same message multiple times.
- State gets out of sync (e.g., chat messages duplicated).

**Root Cause:**
- **No connection recovery** (client reconnects without resync).
- **No acknowledgment system** (server doesn’t confirm message delivery).

**Fixes:**

#### **A) Implement Reconnection Logic (Client-Side)**
```javascript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

const ws = new WebSocket('wss://example.com');
ws.onclose = () => {
  if (reconnectAttempts < maxReconnectAttempts) {
    reconnectAttempts++;
    setTimeout(() => ws.connect(), 2000);
  }
};
```

#### **B) Use Sequence IDs & ACKs (Server-Side)**
```javascript
let lastMessageId = 0;

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    const msg = JSON.parse(data);
    if (msg.id <= lastMessageId) return ws.send('Duplicate detected');
    lastMessageId = msg.id;
    // Process message
  });
});
```

---

### **Issue 5: High CPU/Memory Usage**
**Symptoms:**
- Server crashes with `FATAL: maximum memory reached`.
- WebSocket connections stuck in `TIME_WAIT`.

**Root Cause:**
- **Memory leaks** (storing too many active WebSocket objects).
- **Unclosed connections** (clients never disconnect).

**Fixes:**

#### **A) Limit Concurrent Connections**
```javascript
let connectionCount = 0;
const MAX_CONNECTIONS = 10000;

wss.on('connection', (ws) => {
  if (connectionCount >= MAX_CONNECTIONS) {
    ws.terminate();
    return;
  }
  connectionCount++;
  ws.on('close', () => connectionCount--);
});
```

#### **B) Use Weak Sets to Track Connections**
```javascript
const activeConnections = new WeakSet();

wss.on('connection', (ws) => {
  activeConnections.add(ws);
  ws.on('close', () => activeConnections.delete(ws));
});
```
**→ Automatically cleans up when connections close.**

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                          | **How to Use**                          |
|------------------------|---------------------------------------|-----------------------------------------|
| **Wireshark**          | Inspect WebSocket packets             | Filter for `ws://` or `wss://` traffic.  |
| **Chrome DevTools**    | Monitor WebSocket events               | Open **Network** tab → Filter `WS`.      |
| **`ws` Library Logs**  | Debug server-side issues              | `wss.on('error', console.log)`          |
| **New Relic/Browser DevTools** | Track latency/throughput | Use XHR/WS tabs for real-time monitoring. |
| **`ngrep`**            | Check for blocked traffic            | `ngrep -d any 'GET /ws'` (Linux)        |
| **`curl` (for HTTP upgrades)** | Test handshake | `curl -vI ws://example.com` |

**Example Debug Workflow:**
1. **Open Chrome DevTools → Network → WS tab** → Check for failed handshakes.
2. **Run `wireshark`** → Filter for `WebSocket` to see protocol-level issues.
3. **Check server logs** → Look for `1006` (abnormal closure) or `1008` (policy violation).

---

## **4. Prevention Strategies**

### **A) Infrastructure Best Practices**
✅ **Use WebSocket-compatible load balancers** (Nginx, Kong, AWS ALB).
✅ **Enable HTTP/2 + WebSocket** (reduces connection overhead).
✅ **Monitor connection counts** (set alerts for sudden spikes).

### **B) Code-Level Mitigations**
✅ **Implement reconnection logic** (exponential backoff).
✅ **Use connection pooling** (reuse WebSocket clients where possible).
✅ **Rate-limit slow clients** (prevent DoS via flood attacks).

### **C) Testing & Validation**
🔹 **Load test with k6 or Artillery** (simulate 10K concurrent users).
🔹 **Chaos engineering** (kill random connections to test resilience).
🔹 **Unit test WebSocket handlers** (e.g., Jest + `ws` mocking).

**Example Load Test (k6):**
```javascript
import { check } from 'k6';
import { WebSocket } from 'k6/experimental/websockets';

export default function () {
  const ws = new WebSocket('wss://example.com');
  check(ws, { 'is open': (ws) => ws.readyState === WebSocket.OPEN });
  ws.send(JSON.stringify({ test: 'ping' }));
}
```
**→ Run with `k6 run --vus 1000 -d 30s script.js`.**

---

## **5. Final Checklist Before Production**
| **Step**                          | **Action**                                  |
|-----------------------------------|--------------------------------------------|
| ✅ **HTTPS certificate**          | Valid, not self-signed.                    |
| ✅ **Firewall rules**             | Allow `UDP/TCP 80, 443` (WebSocket ports).  |
| ✅ **Load balancer config**       | Supports WebSocket upgrades (`Upgrade: websocket`). |
| ✅ **Connection cleanup**         | No memory leaks (use `WeakSet`).           |
| ✅ **Fallback for failures**      | Client reconnection logic.                |
| ✅ **Monitoring alerts**          | Set up logs for `1006`, `1008` errors.      |

---

## **Conclusion**
Websockets require **careful handling** of connections, scaling, and protocol compliance. By following this guide:
✔ You can **diagnose drops, latency, and handshake issues** quickly.
✔ You’ll **optimize for performance** with load balancing and non-blocking I/O.
✔ You’ll **prevent common pitfalls** with monitoring and testing.

**Next Steps:**
- **Replicate issues in staging** before production.
- **Automate reconnection logic** in clients.
- **Set up alerts** for abnormal connection drops.

If problems persist, check **firewall logs, proxy configurations, and browser console** for clues. Happy debugging! 🚀