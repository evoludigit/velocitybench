# **Debugging Websockets Conventions: A Troubleshooting Guide**
*(For Backend Engineers Handling Real-Time Communication)*

---

## **Introduction**
WebSockets provide full-duplex, persistent connections between clients and servers, enabling low-latency real-time applications (e.g., chat, gaming, live dashboards). However, misconfigurations, connection drops, or protocol issues can disrupt functionality. This guide helps diagnose and resolve common WebSocket problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom**                     | **Description**                                                                 | **Severity** |
|---------------------------------|---------------------------------------------------------------------------------|--------------|
| Clients can’t establish connection | `WebSocket.onopen` is never called; `onerror` fires with `ERR_CONNECTION_REFUSED` | **Critical** |
| Frequent reconnects            | Clients repeatedly call `ws.connect()` or `reconnect(true)`                     | **High**     |
| Data sent but not received     | Server logs show messages, but clients don’t receive them                       | **High**     |
| High latency or packet loss    | Real-time messages arrive late or incomplete                                   | **Medium**   |
| CORS errors                    | Browser blocks WebSocket handshake due to missing headers (`Access-Control-Allow-Origin`) | **Medium** |
| Memory leaks                   | Server CPU/memory spikes after prolonged WebSocket activity                      | **Critical** |

---

## **2. Common Issues and Fixes**

### **2.1 WebSocket Handshake Fails (Connection Rejected)**
**Symptom:** `onerror` with `ERR_HANDSHAKE_FAILED` or blank response.

#### **Root Causes & Fixes**
| **Cause**                              | **Fix**                                                                 | **Code Example**                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Incorrect WebSocket path              | Server must listen on `/ws` (e.g., `ws://example.com/ws`).               | ```javascript // Client: ws = new WebSocket('ws://example.com/ws'); ```         |
| Missing `Sec-WebSocket-Key` header    | Server must validate and respond with `HTTP 101 Switching Protocols`.    | ```javascript // Server (Node.js): const WebSocket = require('ws'); const wss = new WebSocket.Server({ port: 8080 }); ``` |
| CORS misconfiguration                | Server missing `Access-Control-Allow-Origin` header.                      | ```javascript wss.on('connection', (ws) => { ws.send('Hello'); }); ```         |
| Firewall/Proxy blocking WebSocket    | Port `8080` (or custom) must allow WebSocket traffic.                   | **Firewall Rule:** `iptables -A INPUT -p tcp --dport 8080 -j ACCEPT`              |

**Debugging Steps:**
1. Verify the WebSocket URL matches the server endpoint (check browser DevTools → Network tab).
2. Use `curl` to test the handshake:
   ```bash
   curl -v -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" http://localhost:8080
   ```
   (Check for `101 Switching Protocols` response.)

---

### **2.2 Connection Drops (Unexpected Closing)**
**Symptom:** `onclose` with `code: 1006` (abnormal closure) or `code: 1008` (policy violation).

#### **Root Causes & Fixes**
| **Cause**                              | **Fix**                                                                 | **Code Example**                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Server crashes                        | Graceful shutdown with `server.terminate()`.                           | ```javascript process.on('SIGINT', () => { server.terminate(); }); ```          |
| Keep-alive timeout                    | Enable ping/pong to keep connection alive.                             | ```javascript // Server: ws.on('pong', () => { ws.send('pong', { opcode: 8 }); }); ``` |
| Client-side disconnects               | Implement auto-reconnect logic.                                         | ```javascript let reconnectAttempts = 0; ws.onclose = () => { if (reconnectAttempts < 3) { setTimeout(() => ws.connect(), 2000); } }; ``` |

**Debugging Steps:**
- Check server logs for unhandled errors.
- Use Wireshark or Chrome DevTools to inspect WebSocket traffic for `1000` (normal close) vs. non-standard codes.
- Test with `ws://` (no TLS) first to rule out SSL issues.

---

### **2.3 Data Not Received by Client**
**Symptom:** Server logs show sent messages, but clients never receive them.

#### **Root Causes & Fixes**
| **Cause**                              | **Fix**                                                                 | **Code Example**                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Connection closed before send          | Ensure `ws.readyState === WebSocket.OPEN` before sending.                | ```javascript if (ws.readyState === WebSocket.OPEN) { ws.send('data'); } ```     |
| Messages too large                    | Default max payload: ~16MB. Split large messages.                        | ```javascript const chunkSize = 1024 * 64; let offset = 0; while (offset < data.length) { ws.send(data.slice(offset, offset + chunkSize)); offset += chunkSize; } ``` |
| Binary vs. Text mode mismatch         | Use `ws.binaryType = 'arraybuffer'` for binary data.                    | ```javascript ws.binaryType = 'arraybuffer'; // Enable binary mode ```         |

**Debugging Steps:**
- Verify `onmessage` is attached on the client:
  ```javascript ws.addEventListener('message', (event) => { console.log(event.data); }); ```
- Use server-side logging to confirm messages are sent:
  ```javascript wss.clients.forEach((client) => client.send('DEBUG: Sending test')); ```

---

### **2.4 CORS Errors (`No 'Access-Control-Allow-Origin'`)**
**Symptom:** Browser blocks WebSocket with:
```
Error during WebSocket handshake: Unexpected response code: 403
```

#### **Root Causes & Fixes**
| **Cause**                              | **Fix**                                                                 | **Code Example**                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Missing CORS headers                  | Server must send `Access-Control-Allow-Origin`.                          | ```javascript const wss = new WebSocket.Server({ server, handleProtocols: (protocols) => { return protocols[0]; }, }); ``` |
| Incorrect origin                      | Allow wildcards (`*`) for development, or specify exact domains.         | ```javascript wss.on('upgrade', (req, socket, head) => { if (req.headers.origin === 'http://client.local') { wss.handleUpgrade(req, socket, head, (ws) => { wss.emit('connection', ws, req); }); } }); ``` |

**Debugging Steps:**
- Test with a simple CORS-enabled endpoint:
  ```javascript
  // Temporary test server
  app.get('/test-cors', (req, res) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.send('OK');
  });
  ```
- Check browser DevTools → Console for exact CORS error details.

---

### **2.5 Memory Leaks (CPU/RAM Spikes)**
**Symptom:** Server memory grows indefinitely with active WebSocket connections.

#### **Root Causes & Fixes**
| **Cause**                              | **Fix**                                                                 | **Code Example**                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Unclosed connections                 | Track clients and close them explicitly.                                | ```javascript const clients = new Set(); wss.on('connection', (ws) => { clients.add(ws); ws.on('close', () => { clients.delete(ws); }); }); ``` |
| Large message history                 | Limit message buffering (e.g., 1000 messages).                            | ```javascript ws.on('message', (data) => { if (messages.length > 1000) messages.shift(); messages.push(data); }); ``` |

**Debugging Steps:**
- Use `heapdump` (Node.js) or `htop` (Linux) to monitor memory.
- Check for lingering references:
  ```javascript
  // Example: Cleanup every 5 minutes
  setInterval(() => { wss.clients.forEach((ws) => { if (ws.readyState === ws.OPEN) ws.send('PING'); }); }, 300000);
  ```

---

## **3. Debugging Tools and Techniques**
| **Tool**               | **Use Case**                                                                 | **Command/Setup**                                                                 |
|------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Wireshark**          | Capture WebSocket handshake/payloads.                                       | Filter for `port 8080` and `HTTP WebSocket`.                                       |
| **Chrome DevTools**    | Inspect WebSocket connections (Network tab → WS events).                   | Right-click → "Preserve log" for debugging.                                        |
| **`ws` CLI**           | Test WebSocket endpoints manually.                                          | ```bash ws://example.com/ws ```                                                   |
| **`tls-date`**         | Check for SSL/TLS issues (if using `wss://`).                               | ```bash tls-date -host example.com ```                                           |
| **Node.js `debug`**    | Attach debugger to WebSocket server.                                         | ```bash node --inspect server.js ```                                             |
| **APM Tools (New Relic)** | Monitor WebSocket connection metrics.                                      | Integrate with `newrelic` agent for latency/spikes.                               |

---

## **4. Prevention Strategies**
### **4.1 Server-Side Best Practices**
- **Use `ws` with `WebSocketServer`** (or `socket.io` if additional features like rooms are needed).
  ```javascript
  const WebSocket = require('ws');
  const wss = new WebSocket.Server({ port: 8080 });
  ```
- **Implement Heartbeats** to detect dead connections.
  ```javascript
  setInterval(() => { wss.clients.forEach((ws) => { if (ws.readyState === ws.OPEN) ws.ping(); }); }, 30000);
  ```
- **Rate-Limit Connections** to prevent abuse.
  ```javascript
  let connectionCount = 0;
  wss.on('connection', () => { if (connectionCount > 1000) return ws.close(1008, 'Too many connections'); });
  ```

### **4.2 Client-Side Best Practices**
- **Retry Logic** for failed connections.
  ```javascript
  const reconnect = () => { ws = new WebSocket('ws://example.com/ws'); ws.onclose = reconnect; };
  ```
- **Validate Messages** on receipt.
  ```javascript
  ws.onmessage = (event) => { if (typeof event.data !== 'string') return; };
  ```
- **Handle Errors Gracefully**.
  ```javascript
  ws.onerror = (error) => { console.error('WebSocket error:', error); };
  ```

### **4.3 Monitoring and Alerts**
- **Track Metrics**:
  - Connections/sec, message throughput, latency.
  - Alert on sudden drops (e.g., `Prometheus + Grafana`).
- **Log Critical Events**:
  ```javascript
  wss.on('connection', (ws) => { console.log('New connection:', ws.id); ws.on('close', () => { console.log('Closed:', ws.id); }); });
  ```

---

## **5. Final Checklist for Production**
Before deploying WebSocket services:
1. [ ] Test handshake with `curl`/`ws` CLI.
2. [ ] Verify CORS headers for all client domains.
3. [ ] Implement reconnection logic (client-side).
4. [ ] Set up heartbeat/ping-pong to detect dead connections.
5. [ ] Monitor memory leaks (e.g., `node --inspect` + Chrome DevTools).
6. [ ] Load-test with tools like `wstest` or `k6`.
7. [ ] Document WebSocket API (URL, protocols, message formats).

---
## **Conclusion**
WebSockets are powerful but require careful handling. Focus on:
1. **Handshake issues** (URL, CORS, firewalls).
2. **Connection stability** (pings, reconnects, timeouts).
3. **Data reliability** (chunking, binary/text modes).
4. **Debugging tools** (Wireshark, DevTools, APM).

By following this guide, you can quickly isolate and fix WebSocket problems, ensuring real-time apps run smoothly.