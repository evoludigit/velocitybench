# **Debugging WebSockets: A Troubleshooting Guide**

WebSockets enable real-time, bidirectional communication between clients and servers, making them crucial for applications like chat systems, live updates, and collaborative tools. However, WebSockets can fail due to network issues, misconfigurations, or protocol errors. This guide provides a structured approach to diagnosing and resolving WebSocket-related problems efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, identify which symptoms match your issue:

| **Symptom**                          | **Likely Cause**                          |
|--------------------------------------|-------------------------------------------|
| Connection fails to establish        | Network issues, CORS misconfiguration, TLS/SSL errors |
| Connection drops intermittently      | Network instability, server restarts, timeout issues |
| Data not being received              | Message format errors, protocol mismatches |
| High latency or delayed messages     | Server load, inefficient reconnection logic |
| Browser console errors               | Missing WebSocket support, policy violations |
| `ERR_WEBSOCKET_CLOSED` or `ERR_WEBSOCKET_ACCEPT` | Incorrect handshake, server misconfiguration |
| Server logs show connection refusals | Authentication failures, rate limiting |

If your issue matches multiple symptoms, prioritize **network & handshake-related** problems first.

---

## **2. Common Issues and Fixes**

### **2.1 WebSocket Connection Rejection**
**Symptom:** The browser logs:
```
WebSocket connection to 'ws://example.com/socket' failed: Error during WebSocket handshake: Unexpected response code: 400
```

**Root Cause:** Server misconfigured to reject connections (e.g., incorrect host verification, missing CORS headers).
**Fix:**
```javascript
// Server-side (Node.js with ws library)
const WebSocket = require('ws');
const wss = new WebSocket.Server({ host: '0.0.0.0', port: 8080 });

wss.on('connection', (ws) => {
  console.log('New client connected');
  ws.send('Welcome!');
});

// Ensure CORS is allowed (if needed)
wss.on('request', (req) => {
  req.headers['origin'] = 'http://your-client-domain.com';
  wss.handleUpgrade(req, req.socket, Buffer.alloc(0), (ws) => {
    wss.emit('connection', ws, req);
  });
});
```
**Client-side (JavaScript):**
```javascript
const socket = new WebSocket('ws://your-server.com/socket');
socket.onopen = () => console.log('Connected');
socket.onerror = (e) => console.error('Error:', e);
```

---

### **2.2 CORS (Cross-Origin) Issues**
**Symptom:** Chrome/Lighthouse blocks WebSocket connections with:
```
Access to WebSocket 'ws://example.com' from origin 'http://client.com' has been blocked by CORS policy.
```

**Root Cause:** Server does not include proper CORS headers.
**Fix (Node.js):**
```javascript
// Enable CORS for all origins (or restrict to specific domains)
wss.on('request', (req) => {
  req.headers['origin'] = '*'; // Allow all origins (for development)
  // OR restrict to specific domains:
  // if (req.headers.origin === 'http://trusted-domain.com') { ... }
  wss.handleUpgrade(req, req.socket, Buffer.alloc(0), (ws) => {
    wss.emit('connection', ws, req);
  });
});
```
**Alternative (Express.js middleware):**
```javascript
const cors = require('cors');
app.use(cors());
```

---

### **2.3 TLS/SSL Handshake Failures**
**Symptom:** Connection fails with:
```
SSL handshake failed (Error code: 1)
```

**Root Cause:** Missing or invalid SSL certificate.
**Fix:**
1. Ensure you are using `wss://` (secure WebSocket) instead of `ws://`.
2. Generate a valid certificate (e.g., using `mkcert` for local testing):
   ```bash
   mkcert -install
   mkcert localhost
   ```
3. Configure your server to use SSL:
   ```javascript
   const https = require('https');
   const fs = require('fs');

   const options = {
     key: fs.readFileSync('localhost-key.pem'),
     cert: fs.readFileSync('localhost.pem')
   };

   const wss = new WebSocket.Server({ server: https.createServer(options), port: 8443 });
   ```

---

### **2.4 Connection Timeouts**
**Symptom:** Connection hangs and eventually fails with `ERR_WEBSOCKET_DISCONNECTED`.

**Root Cause:** Server-side timeouts (e.g., keep-alive not enabled) or client-side reconnection delays.
**Fix:**
- **Server-side:** Enable keep-alive:
  ```javascript
  wss.on('connection', (ws) => {
    ws.isAlive = true;
    ws.on('pong', () => { ws.isAlive = true; });
    setInterval(() => {
      if (!ws.isAlive) ws.terminate();
      ws.isAlive = false;
      ws.ping();
    }, 30000); // Ping every 30s
  });
  ```
- **Client-side:** Auto-reconnect logic:
  ```javascript
  let socket = new WebSocket('wss://your-server.com');
  socket.onclose = () => {
    console.log('Reconnecting...');
    setTimeout(() => {
      socket = new WebSocket('wss://your-server.com');
    }, 5000);
  };
  ```

---

### **2.5 Message Format Errors**
**Symptom:** Data is not received correctly, or the server rejects messages.

**Root Cause:** Mismatched message formats (e.g., JSON parsing errors, wrong encoding).
**Fix:**
- **Server:** Ensure messages are parsed correctly:
  ```javascript
  wss.on('message', (ws, data) => {
    try {
      const message = JSON.parse(data);
      console.log('Received:', message);
    } catch (e) {
      console.error('Invalid JSON:', data);
      ws.close(1008, 'Invalid message format');
    }
  });
  ```
- **Client:** Send valid JSON:
  ```javascript
  socket.send(JSON.stringify({ event: 'chat', text: 'Hello!' }));
  ```

---

### **2.6 Firewall/Network Blocking**
**Symptom:** Connections work locally but fail in production.

**Root Cause:** Firewall, NAT, or ISP blocking WebSocket ports (default: `80`, `443`).
**Fix:**
1. Verify network connectivity:
   ```bash
   telnet your.server.com 8080
   ```
2. If using a cloud provider, ensure **Security Groups** allow WebSocket traffic.
3. Use a proxy (e.g., Nginx) to forward WebSocket connections:
   ```nginx
   location /socket {
     proxy_pass http://localhost:8080;
     proxy_http_version 1.1;
     proxy_set_header Upgrade $http_upgrade;
     proxy_set_header Connection "upgrade";
   }
   ```

---

## **3. Debugging Tools & Techniques**

### **3.1 Browser DevTools**
- **Network Tab:** Check WebSocket connections under "WebSocket" in the network log.
- **Console:** Look for errors like `WebSocket connection failed`.
- **Application Tab:** Inspect active WebSocket connections.

### **3.2 Server Logs**
- Check server logs for connection drops:
  ```bash
  tail -f /var/log/nginx/error.log
  ```
- For Node.js, enable detailed logging:
  ```javascript
  wss.on('connection', (ws) => {
    console.log('New connection:', ws.remoteAddress);
    ws.on('error', (err) => console.error('WebSocket error:', err));
  });
  ```

### **3.3 Wireshark & tcpdump**
- Capture traffic to diagnose handshake failures:
  ```bash
  tcpdump -i any port 8080 -w websocket.pcap
  ```
- Analyze the `.pcap` file in Wireshark for handshake errors.

### **3.4 WebSocket Testing Tools**
- **WebSocket King** ([websocketking.com](https://websocketking.com/)) – Test WebSocket connections.
- **Postman** – Send WebSocket requests via the "WebSocket" tab.

### **3.5 Health Checks**
- Implement a `/ws-health` endpoint to test connectivity:
  ```javascript
  app.get('/ws-health', (req, res) => {
    res.json({ status: 'WebSocket is reachable' });
  });
  ```

---

## **4. Prevention Strategies**

### **4.1 Secure WebSocket Endpoints**
- Always use `wss://` in production (TLS enforced).
- Restrict origins via CORS:
  ```javascript
  const allowedOrigins = ['https://trusted.com'];
  wss.on('request', (req) => {
    if (!allowedOrigins.includes(req.headers.origin)) {
      return req.socket.destroy();
    }
    wss.handleUpgrade(req, req.socket, Buffer.alloc(0), (ws) => {
      wss.emit('connection', ws, req);
    });
  });
  ```

### **4.2 Rate Limiting & Throttling**
- Prevent abuse with libraries like `express-rate-limit` or `slowdown`:
  ```javascript
  const slowdown = require('express-slowdown');
  app.use(slowdown({
    windowMs: 15 * 60 * 1000, // 15 min
    delayAfter: 10, // Allow 10 requests
    delayMs: 500 // Block after 10th request
  }));
  ```

### **4.3 Graceful Shutdown Handling**
- Ensure WebSocket connections close properly on server restart:
  ```javascript
  process.on('SIGINT', () => {
    wss.clients.forEach(client => client.close());
    process.exit();
  });
  ```

### **4.4 Monitor Connection Stability**
- Track reconnection attempts and errors:
  ```javascript
  let reconnectionAttempts = 0;
  socket.on('close', () => {
    reconnectionAttempts++;
    if (reconnectionAttempts < 5) {
      setTimeout(() => {
        socket = new WebSocket('wss://your-server.com');
      }, 3000 * reconnectionAttempts);
    }
  });
  ```

### **4.5 Load Testing**
- Use tools like **Artillery** to simulate high traffic:
  ```yaml
  # artillery.yaml
  config:
    target: "wss://your-server.com"
    phases:
      - duration: 60
        arrivalRate: 10
  scenario:
    flow:
      - websocket:
          path: "/socket"
          message: '{"type":"message"}'
  ```

---

## **5. Summary of Key Actions**
| **Issue**               | **Quick Fix**                          |
|--------------------------|-----------------------------------------|
| Connection refused       | Check CORS, SSL, and server config      |
| CORS blocked             | Add `Access-Control-Allow-Origin`        |
| SSL handshake fails      | Ensure valid certificate is used        |
| Connection drops         | Enable keep-alive & auto-reconnect      |
| Message format errors    | Validate JSON parsing on server         |
| Firewall blocking        | Open ports in cloud provider settings    |

---

## **Final Recommendations**
1. **Start with the browser console** – Most issues are visible there.
2. **Check server logs** – Many WebSocket failures are server-side.
3. **Test with a WebSocket client tool** – Confirm if the issue is client or server-specific.
4. **Implement reconnection logic** – WebSockets are inherently unreliable without it.

By following this guide, you should be able to diagnose and resolve WebSocket issues efficiently. If problems persist, consider checking:
- **Proxy/Firewall logs** (e.g., Nginx, CDN)
- **Third-party services** (e.g., AWS ALB, Cloudflare)
- **Client-side JavaScript errors** (e.g., `WebSocket` not supported in older browsers)