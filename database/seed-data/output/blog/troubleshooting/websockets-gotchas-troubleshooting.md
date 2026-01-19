# **Debugging Websockets Gotchas: A Troubleshooting Guide**

Websockets provide real-time bidirectional communication between clients and servers, but their asynchronous, persistent nature introduces unique challenges. Misconfigurations, network quirks, or protocol violations can lead to subtle bugs that are hard to diagnose. This guide covers common Websocket pitfalls, debugging techniques, and best practices to resolve issues efficiently.

---

## **1. Symptom Checklist: Red Flags for Websocket Issues**
Before diving into debugging, confirm the problem using these symptoms:

✅ **Connection Failures**
- Clients fail to establish Websocket handshake (`WebSocket.connect()` rejects, `Upgrade` HTTP response fails).
- Server logs show `1008: POLICY VIOLATION` or `1013: GOING AWAY` errors.

✅ **Disconnections & Reconnection Loops**
- Clients abruptly drop (`onclose` triggered unexpectedly).
- Server logs show frequent `1001: GOING AWAY` or `1002: PROTOCOL ERROR`.

✅ **Data Corruption or Loss**
- Messages arrive out of order or incomplete.
- Server/client reports missing or duplicated frames.

✅ **Performance Degradation**
- High CPU/memory usage on server (e.g., unclosed connections).
- Latency spikes without clear cause.

✅ **Browser/Platform-Specific Issues**
- Works in Chrome but fails in Firefox/Safari.
- Mobile apps crash on Websocket operations.

---
## **2. Common Issues & Fixes**

### **A) Websocket Handshake Fails**
**Symptoms:**
- `WebSocket.connect()` throws `NetworkError` or `InvalidStateError`.
- Server responds with `400 Bad Request` or `403 Forbidden` instead of `101 Switching Protocols`.

**Root Causes & Fixes:**

| **Cause**                          | **Fix**                                                                                                      |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Missing `Sec-WebSocket-Key`**     | Ensure the server validates `Sec-WebSocket-Key` (generate `SHA1(key + GUID)`).                            |
| **Incorrect Subprotocols**          | If using subprotocols (e.g., `Sec-WebSocket-Protocol`), verify client/server agreement.                     |
| **CORS Misconfiguration**           | Server must include `Access-Control-Allow-Origin` and `Access-Control-Allow-Methods: GET, OPTIONS`.         |
| **Proxy/Load Balancer Issues**      | Some proxies (Nginx, HAProxy) require explicit Websocket upgrade rules.                                   |
| **HTTPS/SSL Mismatch**              | Ensure `Sec-WebSocket-Extensions` and TLS match (e.g., `permessage-deflate`).                            |

**Example Fix (Node.js Server):**
```javascript
const WebSocket = require('ws');
const server = new WebSocket.Server({ server: httpsServer });

server.on('connection', (ws) => {
  console.log('New connection');
  ws.on('message', (data) => { /* ... */ });
});
```
**If using HTTP proxy (e.g., Nginx):**
```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

### **B) Unexpected Disconnections (`1001`/`1002` Errors)**
**Symptoms:**
- Clients reconnect without warning.
- Server logs show `onError` with `1001: GOING AWAY` or `1002: PROTOCOL ERROR`.

**Root Causes & Fixes:**

| **Cause**                          | **Fix**                                                                                                      |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Server-Created Frames Only**     | Ensure both client and server send **binary or text frames** (no malformed masks).                         |
| **Ping/Pong Timeout**               | Implement `ping/pong` intervals (e.g., `ws.ping()` every 30 sec).                                           |
| **Memory Leaks**                    | Close connections explicitly (`ws.close()`). Avoid global `ws` references.                                   |
| **Protocol Violation**              | Validate payloads (e.g., JSON schema) before sending.                                                        |
| **Network Partitioning**            | Use reconnection logic (e.g., exponential backoff).                                                          |

**Example Fix (Ping/Pong):**
```javascript
const ws = new WebSocket('wss://example.com');
ws.on('open', () => {
  ws.send('ping');
  ws.on('message', (data) => {
    if (data === 'pong') ws.send('ping'); // Keep alive
  });
});
```

**Server-Side Ping/Pong (Node.js):**
```javascript
server.on('connection', (ws) => {
  let interval = setInterval(() => ws.ping(), 30000);
  ws.on('pong', () => clearInterval(interval)); // Reset on pong
});
```

---

### **C) Data Corruption or Ordering Issues**
**Symptoms:**
- Messages arrive truncated or out of sequence.
- Binary data decoded incorrectly.

**Root Causes & Fixes:**

| **Cause**                          | **Fix**                                                                                                      |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Missing Frame Fin Flag**          | Ensure `FIN` bit is set for each message (no partial frames).                                               |
| **Masking Errors**                 | Clients **must** mask frames; servers **must not** (RFC 6455).                                             |
| **Padded/Continuation Frames**      | Avoid mixing `FIN`/`CONT` flags improperly.                                                                    |
| **Compression Mismatch**            | For `permessage-deflate`, agree on extensions (e.g., `client_no_context_takeover`).                           |

**Example Fix (Proper Frame Handling):**
```javascript
// Client: Always mask
ws.send('Hello', { binary: false });
// Server: Must mask=false in raw frames
ws.on('message', (data) => {
  if (data instanceof Buffer) console.log('Binary:', data);
  else console.log('Text:', data);
});
```

---

### **D) Scaling & Performance Issues**
**Symptoms:**
- Server crashes under load.
- High memory usage (`ws._clients` grows).

**Root Causes & Fixes:**

| **Cause**                          | **Fix**                                                                                                      |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **No Connection Limits**            | Set max connections (e.g., `server.maxConnections = 1000`).                                                  |
| **Unclosed Connections**           | Use `ws.on('close', () => cleanup())`.                                                                       |
| **Inefficient Serialization**       | Prefer `JSON` or `MessagePack` over raw strings.                                                              |
| **Event Loop Blocking**             | Offload heavy processing (e.g., Web Workers in browser).                                                     |
| **Database Bottlenecks**            | Batch writes or use WebSocket → HTTP proxy for persistence.                                                   |

**Example Fix (Connection Limits):**
```javascript
const WebSocket = require('ws');
const server = new WebSocket.Server({ server, maxConnections: 5000 });
server.on('connection', (ws) => { /* ... */ });
```

---

## **3. Debugging Tools & Techniques**
### **A) Browser DevTools**
- **Network Tab**: Check Websocket handshake (look for `Upgrade: websocket`).
- **Console Logs**: Capture `onopen`, `onerror`, and `onclose` events.
- **Performance Tab**: Identify latency spikes.

### **B) Server-Side Logging**
```javascript
server.on('connection', (ws, req) => {
  console.log(`New connection from ${req.socket.remoteAddress}`);
  ws.on('message', (data) => console.log(`Received: ${data}`));
});
```

### **C) WebSocket Debugging Extensions**
- **Chrome**: [WebSocket Debugger](https://chrome.google.com/webstore/detail/websocket-debugger/hgimnogjllphhhkhlmebbmlpeogceged)
- **Firefox**: Built-in `WebSocket` inspector in DevTools.

### **D) Network Sniffing**
- **Wireshark/tcpdump**: Filter for `WebSocket` traffic (`ws://` or `wss://`).
- **Example Wireshark Filter**: `ws.handshake`.

### **E) Unit Testing Websockets**
- **Mocha + `ws` Library**:
  ```javascript
  const WebSocket = require('ws');
  const assert = require('assert');

  describe('Websocket', () => {
    it('should handle ping/pong', (done) => {
      const server = new WebSocket.Server({ port: 0 });
      const client = new WebSocket(`ws://localhost:${server.options.port}`);
      client.on('ping', () => client.pong());
      client.on('close', done);
    });
  });
  ```

---

## **4. Prevention Strategies**
### **A) Design-Time Checks**
1. **Validate Handshake**: Use a library like [`ws`](https://github.com/websockets/ws) in Node.js or [`django-websocket-redis`](https://github.com/django-websocket-redis/django-websocket-redis) for Django.
2. **Subprotocol Agreement**: Document supported subprotocols (e.g., `chat`).
3. **Reconnection Logic**: Implement exponential backoff:
   ```javascript
   let retryCount = 0;
   function reconnect() {
     retryCount = retryCount * 2 + 1;
     const delay = Math.min(retryCount * 1000, 30000);
     setTimeout(connect, delay);
   }
   ```

### **B) Runtime Safeguards**
- **Timeouts**: Kill stale connections after `idleTimeout` (e.g., 5 mins).
- **Payload Validation**:
  ```javascript
  ws.on('message', (data) => {
    try { JSON.parse(data); } // Reject malformed JSON
    catch (e) { ws.close(1002, 'Invalid JSON'); }
  });
  ```
- **Monitoring**: Track:
  - Active connections (`ws._clients.size`).
  - Message latency (P99 percentile).

### **C) Security Hardening**
- **Origin Validation**: Restrict `Access-Control-Allow-Origin`.
- **Rate Limiting**: Throttle connections per IP.
- **TLS**: Enforce `wss://` (not `ws://`).

---

## **5. Quick Reference Cheatsheet**
| **Issue**               | **Check**                          | **Fix**                                  |
|-------------------------|-------------------------------------|------------------------------------------|
| Handshake fails         | `Sec-WebSocket-Key` mismatch        | Generate `SHA1(key + GUID)`.              |
| Client disconnects      | Missing `ping/pong`                | Add `ws.ping()` interval.                |
| Data corruption         | Unmasked frames                     | Ensure client masks, server doesn’t.    |
| High CPU                | No connection limits               | Set `maxConnections`.                    |
| Browser-specific bugs   | `Upgrade` header missing            | Verify proxy/Nginx config.               |

---
## **Final Notes**
Websockets are powerful but fragile. **Prototype early** with tools like:
- [Socket.IO](https://socket.io/) (abstraction over raw Websockets).
- [WebSocket++](https://github.com/websocketpp/websocketpp) (C++ library).

For production:
- Use a **load balancer** (e.g., Kong, Traefik) with Websocket support.
- **Monitor connections** with Prometheus + Grafana.

By systematically checking handshakes, frames, and reconnections, you’ll resolve 90% of Websocket issues in minutes.