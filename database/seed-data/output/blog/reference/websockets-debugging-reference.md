# **[Pattern] Websockets Debugging – Reference Guide**

---

### **Overview**
Websockets provide **real-time, bidirectional communication** between clients and servers, eliminating the overhead of HTTP polling. However, debugging Websocket connections—unlike HTTP—requires specialized tools and techniques due to their persistent, two-way nature. This guide covers **debugging Websockets for performance, connectivity, and protocol errors**, including tools, logging strategies, and common pitfalls. Whether troubleshooting **connection drops, message corruption, or scalability issues**, this reference ensures efficient Websocket diagnostics across **frontend (client-side) and backend (server-side)** environments.

---

## **1. Key Concepts**

### **Core Websocket States & Events**
| State/Event          | Description                                                                 | Client-Side Check | Server-Side Check |
|----------------------|-----------------------------------------------------------------------------|-------------------|--------------------|
| **`CONNECTING`**     | Handshake in progress (WS → HTTP Upgrade).                                  | Check `WebSocket.readyState === WebSocket.CONNECTING`. | Verify upgrade request headers. |
| **`OPEN`**           | Connection established; bidirectional communication.                      | `WebSocket.readyState === WebSocket.OPEN`. | Monitor active connections. |
| **`CLOSEING`/`CLOSED`** | Connection terminated gracefully or abnormally.                       | `WebSocket.onclose` or `readyState` check. | Check close codes (e.g., `1000`, `1008`). |
| **`ERROR`**          | Connection failed or protocol violation.                                    | `WebSocket.onerror` event. | Server logs & `ws://` vs `wss://` misconfigurations. |

### **Websocket Protocol Layers**
- **Transport Layer (TCP/IP)**: Verify network connectivity (firewalls, NAT).
- **Application Layer (WS/WS)**:
  - **`ws://`** (unencrypted) vs **`wss://`** (TLS-encrypted).
  - Frame fragmentation and masking (for client→server).
- **Message Format**:
  - **Text/JSON**: Validate payloads with `JSON.parse()`.
  - **Binary**: Check MIME type (`binaryType` in `WebSocket`).

---

## **2. Debugging Tools**

### **Browser DevTools**
| Tool                | Use Case                                                                 | Example Command/Flag |
|---------------------|--------------------------------------------------------------------------|----------------------|
| **Network Tab**     | Capture Websocket handshake & messages.                                 | Filter by "WebSocket". |
| **Console**         | Log `readyState`, errors, and custom events.                            | `console.log(ws.readyState)`. |
| **Application Tab** | Inspect active WS connections (Chrome/Firefox).                         | Search for `WebSocket` in "Storage". |
| **Performance Profiler** | Measure latency/memory usage during WS events.                        | Record while sending messages. |

### **Server-Side Tools**
| Tool                | Purpose                                                                 | Example Setup |
|---------------------|--------------------------------------------------------------------------|----------------|
| **`ws`/`socket.io` logs** | Server-level errors, reconnections, and message counts.               | `server.on('connection', (ws) => { ws.on('error', (err) => console.log(err)); }).` |
| **NGINX/Apache logs** | Check TCP-level drops/proxies.                                          | `access.log` filtering for `WebSocket` headers. |
| **Prometheus/Grafana** | Monitor WS connection metrics (e.g., `ws_open_connections`).          | Expose `/metrics` endpoint. |

### **External Tools**
| Tool                | Use Case                                                                 | URL |
|---------------------|--------------------------------------------------------------------------|-----|
| **Wireshark**       | Deep-dive TCP/Websocket frames.                                          | [Wireshark](https://www.wireshark.org/) |
| **Postman/Newman**  | Validate WS endpoints with custom scripts.                              | [Newman](https://www.postman.com/newman/) |
| **WebSocket King**  | Stress-test connections & measure throughput.                          | [WebSocket King](https://websocketking.com/) |

---

## **3. Common Issues & Fixes**

### **A. Connection Failures**
| Symptom                     | Root Cause                          | Fix |
|-----------------------------|-------------------------------------|-----|
| **Handshake timeout**       | Firewall blocking `ws://` port 80/443. | Use `wss://` + valid SSL cert. |
| **`ERR_CONNECTION_REFUSED`** | Server not listening on WS port.     | Verify `server.listen(8080, () => { /* WS logic */ })`. |
| **CORS errors**             | Missing `Access-Control-Allow-Origin` header. | Configure server middleware (e.g., `cors()`). |

### **B. Message Corruption**
| Symptom                     | Root Cause                          | Fix |
|-----------------------------|-------------------------------------|-----|
| **Garbled payloads**        | Incorrect `binaryType` or encoding. | Set `ws.binaryType = 'arraybuffer'`. |
| **Truncated messages**      | Server/client sending partial frames. | Check frame size limits (e.g., `socket.setMaxListeners`). |
| **JSON parsing errors**     | Malformed payloads.                 | Validate with `try/catch` around `JSON.parse()`. |

### **C. Performance Bottlenecks**
| Symptom                     | Root Cause                          | Fix |
|-----------------------------|-------------------------------------|-----|
| **High latency**            | Unoptimized server (e.g., blocking I/O). | Use `async/await` or event loops. |
| **Memory leaks**            | Unclosed connections (`ws.close()`). | Implement cleanup (e.g., in Node.js: `ws.on('close', () => { /* free resources */ })`). |
| **Throttling**              | Too many concurrent WS connections.  | Use connection pooling or scaling. |

---

## **4. Schema Reference**

| **Category**            | **Field**               | **Type**          | **Description**                                                                 | **Example**                     |
|-------------------------|-------------------------|-------------------|---------------------------------------------------------------------------------|---------------------------------|
| **Connection Metadata** | `readyState`            | Number (0–3)      | Current Websocket state (CONNECTING=0, OPEN=1, CLOSED=3).                     | `ws.readyState === 1`           |
|                         | `url`                   | String            | Websocket URI (e.g., `wss://example.com/ws`).                                 | `"wss://api.example.com/chat"`  |
|                         | `protocol`              | String            | Subprotocol (e.g., `chat`, `v2`).                                              | `"chat"`                        |
| **Message Payload**     | `data`                  | Binary/String     | Incoming/outgoing message.                                                     | `JSON.stringify({ msg: "hello" })` |
|                         | `opcode`                | Number (0–7)      | RFC 6455 opcode (e.g., `0`=continuation, `1`=text, `2`=binary).              | `1` (text frame)                |
| **Error Handling**      | `closeCode`             | Number            | RFC 6454 close reason (e.g., `1000`=normal, `1008`=protocol error).          | `1008`                          |
|                         | `errorMessage`          | String            | Custom error description.                                                      | `"Payload too large"`           |

**Key RFC References**:
- [RFC 6455 (Websocket)](https://datatracker.ietf.org/doc/html/rfc6455)
- [RFC 6454 (HTTP Upgrade)](https://datatracker.ietf.org/doc/html/rfc6454)

---

## **5. Query Examples**

### **Client-Side Debugging**
**Check Connection State:**
```javascript
const ws = new WebSocket("wss://example.com/ws");
ws.onopen = () => console.log(`State: ${ws.readyState} (OPEN)`);
ws.onerror = (event) => console.error("WS Error:", event);
```

**Log All Messages:**
```javascript
ws.onmessage = (event) => {
  console.log("Received:", event.data);
  if (event.data instanceof ArrayBuffer) {
    const viewer = new WebAssembly.Viewer();
    console.log(viewer.inspect(event.data));
  }
};
```

### **Server-Side Debugging (Node.js)**
**Log Active Connections:**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  console.log(`New connection: ${ws._socket.remoteAddress}`);
  ws.on('message', (data) => console.log(`Message: ${data}`));
});
```

**Validate Close Codes:**
```javascript
wss.on('close', (ws, code, reason) => {
  if (code === 1008) {
    console.error(`Client quit abruptly: ${reason}`);
  }
});
```

---

## **6. Related Patterns**

| Pattern                          | Description                                                                 | Link/Reference |
|-----------------------------------|-----------------------------------------------------------------------------|----------------|
| **[Retry Mechanisms for Websockets]** | Implement exponential backoff for reconnects.                            | [MDN Retry](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/reconnect) |
| **[Websocket Security Best Practices]** | TLS, authentication (e.g., JWT in headers), and rate limiting.           | [OWASP WS Guide](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html) |
| **[Scaling Websockets with Redis/Pub-Sub]** | Broadcast messages to multiple clients via a message queue.              | [Socket.io + Redis](https://socket.io/docs/v4/using-redis/) |
| **[Websocket State Management]**   | Track user sessions and offline messages.                                 | [State Pattern](https://www.confluent.io/blog/web-socket-state-pattern/) |
| **[HTTP → Websocket Fallback]**    | Graceful degradation if WS fails (e.g., polling).                         | [Service Worker Caching](https://developers.google.com/web/fundamentals/primers/service-worker) |

---
**Note**: For advanced scenarios, consider **WebSocket secured with OAuth2** or **compression (PerMessageDeflate)**. Always test in **non-production environments** first.