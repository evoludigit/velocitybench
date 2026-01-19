# **Debugging Websockets: A Troubleshooting Guide**

---

## **1. Introduction**
Websockets provide real-time, bidirectional communication between clients and servers, replacing traditional HTTP polling mechanisms. Despite their efficiency, Websockets can fail due to network issues, protocol misconfigurations, or server/client mismatches. This guide helps diagnose and resolve common Websockets issues efficiently.

---

## **2. Symptom Checklist: Is It a Websockets Problem?**
Before diving deep, verify if the issue is Websockets-related:

✅ **Connection Success:**
   - Can the client connect to the Websockets endpoint? (Check `wss://` or `ws://` URI)
   - Does the server log show successful connection handshakes?

✅ **Data Flow:**
   - Are messages being sent/received in real-time, or are there delays?
   - Is the connection dropping unexpectedly?

✅ **Error Codes & Logs:**
   - **Client-side:** Check browser console (`WebSocket` errors like `ERR_CONNECTION_REFUSED`, `WebSocket is closed before the connection is established`).
   - **Server-side:** Look for `WS` or `WebSocket` errors in logs (e.g., `connection refused`, `handshake failed`).

✅ **Firewall/Proxy Issues:**
   - Is the Websockets traffic blocked by firewalls, CSP, or proxies?

✅ **Browser/Client-Side Support:**
   - Does the client (browser, app, or custom client) fully support Websockets?

---

## **3. Common Issues & Fixes**

### **3.1 WebSocket Connection Rejected**
**Symptoms:**
- Client fails to establish connection (`WSERR_CONNECTION_REFUSED`).
- Server logs show no incoming connections.

**Root Causes:**
- Incorrect WebSocket URL (HTTP vs. WS, missing port).
- Server not running or WebSocket endpoint misconfigured.
- Client blocked by CORS or firewall.

**Fixes:**

#### **Code Example: Correct WebSocket URL**
```javascript
// ✅ Correct (WS over secure connection)
const socket = new WebSocket('wss://yourdomain.com/socket');

// ❌ Incorrect (HTTP instead of WS, wrong port)
const badSocket = new WebSocket('http://yourdomain.com:8080/socket');
//   or
const badSocket = new WebSocket('ws://yourdomain.com:8080');
```

#### **Server-Side Fix (Python - `websockets` library):**
```python
import asyncio
from websockets.sync.client import connect

async def check_connection():
    try:
        with connect("ws://localhost:8765") as websocket:
            print("✅ Connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.get_event_loop().run_until_complete(check_connection())
```

#### **CORS & Firewall Checks:**
- Ensure your server allows WebSocket connections:
  ```http
  Access-Control-Allow-Origin: *
  ```
- Check OS/firewall rules to allow ports (typically `80`, `443`, or a custom port).

---

### **3.2 Connection Drops Randomly**
**Symptoms:**
- Clients reconnect intermittently.
- Server logs show abrupt disconnections (`websocket connection closed`).

**Root Causes:**
- Network instability (latency, packet loss).
- Server-side timeouts (`pingInterval`, `pingTimeout` misconfigured).
- Client-side crashes before proper disconnect.

**Fixes:**

#### **Server-Side (Node.js - `ws` library):**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080, clientTracking: true });

wss.on('connection', (ws, req) => {
    // Ensure ping/pong keepalive is set
    ws.isAlive = true;
    ws.on('pong', () => { ws.isAlive = true; });

    ws.on('ping', () => ws.ping()); // Auto-keepalive

    setInterval(() => {
        if (!ws.isAlive) ws.terminate();
        ws.isAlive = false;
        ws.ping();
    }, 30000); // Check every 30 sec
});
```

#### **Client-Side (JavaScript):**
```javascript
const socket = new WebSocket('wss://yourdomain.com/socket');

socket.onclose = (e) => {
    if (e.wasClean) {
        console.log("Closed cleanly:", e.code, e.reason);
    } else {
        console.warn("Connection dropped:", e.reason);
        // Attempt reconnect
        setTimeout(() => connect(), 5000);
    }
};
```

---

### **3.3 Messages Not Received**
**Symptoms:**
- Server sends messages, but clients don’t receive them.
- No errors, but data is lost.

**Root Causes:**
- Improper message framing (binary vs. text).
- Server/client buffering issues.
- Missing `onmessage` handler.

**Fixes:**

#### **Server-Side (Python):**
```python
async def handle_connection(websocket):
    async for message in websocket:
        print("Received:", message)  # Log incoming messages
        await websocket.send(f"Echo: {message}")  # Resend to verify
```

#### **Client-Side (JavaScript):**
```javascript
socket.onmessage = (event) => {
    console.log("Received:", event.data); // Ensure handler exists
    if (typeof event.data !== 'string') {
        console.warn("Binary data received, but not handled!");
    }
};
```

---

### **3.4 Handshake Failure (`1008: Policy Violation` or `1007: Invalid Frame`)**
**Symptoms:**
- Connection fails with `WebSocket protocol error`.
- Server logs show malformed requests.

**Root Causes:**
- Incorrect `Sec-WebSocket-Key` or `Sec-WebSocket-Version` headers.
- Unsupported subprotocols.
- Client sending non-UTF-8 text.

**Fixes:**

#### **Debugging Handshake Headers:**
```bash
# Use `curl` to test handshake
curl -v 'ws://localhost:8080'
```
Check for proper `Sec-WebSocket-Key` and `Upgrade: websocket` headers.

#### **Server-Side (Node.js):**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({
    port: 8080,
    verifyClient: (info) => {  // Extra security (optional)
        return info.origin === 'https://trusted-domain.com';
    }
});
```

---

### **3.5 Performance Issues (High Latency)**
**Symptoms:**
- Messages take too long to arrive.
- High CPU usage on server.

**Root Causes:**
- Too many connections (server throttling).
- Large message sizes (> 16KB).
- Missing compression (`permessage-deflate`).

**Fixes:**

#### **Enable Frame Compression:**
```javascript
// Node.js
wss.on('connection', (ws) => {
    ws.supports('permessage-deflate') && ws.setCompression(true);
});
```

#### **Rate Limiting:**
```javascript
const rateLimit = new RateLimiter({ ... }); // Use a library like `limiter`
wss.on('connection', (ws) => rateLimit.check(ws.ip) || ws.close());
```

---

## **4. Debugging Tools & Techniques**

### **4.1 Browser DevTools**
- **Network Tab:** Filter for `WebSocket` events.
- **Console:** Check `WebSocket` errors.
- **Performance Tab:** Time WebSocket operations.

### **4.2 Server-Side Logging**
```javascript
// Node.js
wss.on('connection', (ws) => {
    console.log(`New connection: ${ws.remoteAddress}`);
    ws.on('close', () => console.log('Connection closed'));
});
```

### **4.3 WireShark / tcpdump**
Analyze raw network traffic:
```bash
# Capture WebSocket traffic (port 8080)
tcpdump -i eth0 -A port 8080 | grep -A 10 "Sec-WebSocket"
```

### **4.4 Postman / WebSocket Testing Tools**
- **Postman:** Test WebSocket endpoints.
- **WebSocket King:** Simulate clients.

### **4.5 Automated Tests**
```javascript
const WebSocket = require('ws');
const assert = require('assert');

describe('WebSocket Tests', () => {
    it('should connect and send message', async () => {
        const ws = new WebSocket('ws://localhost:8080');
        await new Promise((resolve) => ws.on('open', resolve));
        ws.send('test');
        assert.ok(true, 'Message sent');
    });
});
```

---

## **5. Prevention Strategies**

### **5.1 Secure & Validate Connections**
- Use HTTPS (should be `wss://`).
- Implement proper CORS headers.
- Validate WebSocket headers server-side.

### **5.2 Optimize Message Handling**
- Use binary frames for efficiency.
- Implement batching for frequent updates.

### **5.3 Monitor & Alert**
- Track connection drops in logs.
- Set up alerts for high latency.

### **5.4 Graceful Degradation**
```javascript
// Fallback to polling if WebSocket fails
const tryWebSocket = async () => {
    try {
        const socket = new WebSocket('wss://yourdomain.com');
        socket.onmessage = (e) => handleMessage(e.data);
    } catch (e) {
        console.warn('Falling back to polling...');
        setInterval(fetchUpdates, 5000);
    }
};
```

---

## **6. Final Checklist Before Deployment**
| Item | ✅ Yes | ❌ Needs Fix |
|------|-------|-------------|
| Correct WebSocket URL (`ws://` or `wss://`) | | |
| Server supports `Sec-WebSocket-Key` | | |
| Client & server timeouts configured | | |
| Message format consistent (text/binary) | | |
| Connection reconnect logic in place | | |
| Performance tested (latency, throughput) | | |

---

## **7. Conclusion**
Websockets are powerful but can fail silently. Focus on:
1. **Connection stability** (handshakes, reconnects).
2. **Data integrity** (message framing, encoding).
3. **Performance** (compression, rate limiting).

Use logs, network tools, and automated tests to catch issues early. For production, implement monitoring and graceful fallbacks.

**Need help?** Check:
- [MDN WebSocket Docs](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [WebSocket Server Libraries](https://github.com/websockets/websockets)