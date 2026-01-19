# **Debugging Websockets Integration: A Troubleshooting Guide**

Websockets provide real-time, bidirectional communication between a client and server. While powerful, misconfigurations, network issues, or protocol violations can disrupt functionality.

This guide helps diagnose and resolve common Websockets integration problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, ensure the issue matches these symptoms:

| **Symptom**                     | **Possible Causes**                          |
|---------------------------------|---------------------------------------------|
| Connection fails (400-499 errors) | Incorrect Websocket URL, CORS misconfigurations |
| Connection drops intermittently | Network issues, WS/HTTP upgrades failing     |
| Messages not delivered           | Incorrect message framing, server-side bugs |
| High latency or stalls          | Server overload, slow clients, firewall rules |
| Authentication/authorization issues | Missing headers, expired tokens, misconfigured security |

---

## **2. Common Issues & Fixes**

### **Issue 1: Connection Refused (400 Bad Request or Connection Timeout)**
**Symptoms:**
- Client fails to initiate Websocket handshake (e.g., `WebSocket is closed before the connection is established`).
- Server logs show no incoming requests.

**Root Causes:**
- Incorrect Websocket URL (e.g., using `http://` instead of `ws://` or `wss://`).
- Firewall or proxy blocking Websocket ports (default: 80 for `ws://`, 443 for `wss://`).
- Server not configured to handle Websocket upgrades.

**Fixes:**
#### **Frontend (Client-Side Check)**
```javascript
// Correct Websocket URL (use `wss://` for secure connections)
const ws = new WebSocket('wss://yourdomain.com/api/ws');

// Test with a simple echo server (e.g., `ws://localhost:8080`)
```
✅ **Verify URL format** – Use `ws` (unencrypted) or `wss` (encrypted).
✅ **Check for typos** – Ensure the path is correct.

#### **Backend (Server-Side Check)**
**For Node.js (Express + `ws` package):**
```javascript
const express = require('express');
const { WebSocketServer } = require('ws');
const app = express();

const server = app.listen(8080); // Use HTTPS in production
const wss = new WebSocketServer({ server }); // Enable Websocket upgrades

wss.on('connection', (ws) => {
  console.log('Client connected!');
  ws.send('Welcome!');
});
```
✅ **Ensure `server` object is passed to `WebSocketServer`** – Without it, upgrades fail.
✅ **Enable CORS (if needed):**
```javascript
wss.on('connection', (ws, req) => {
  const origin = req.headers.origin;
  ws.send(`Allowed from: ${origin}`);
});
```

**For Python (FastAPI + `websockets`):**
```python
from fastapi import FastAPI
import websockets

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send("Connected!")
```
✅ **Use `/ws` endpoint** – Ensure Websocket routes are properly defined.
✅ **Check ASGI server (e.g., Uvicorn)**:
```bash
uvicorn main:app --reload --ssl-keyfile key.pem --ssl-certfile cert.pem
```

---

### **Issue 2: Intermittent Drops (Connection Closed Unexpectedly)**
**Symptoms:**
- `onclose` event triggers without warning.
- Logs show `1006` (abnormal closure) or `1006: ABNORMAL_CLOSURE`.

**Root Causes:**
- **Network instability** (flaky connections, VPNs, public Wi-Fi).
- **Server-side crashes** (unhandled exceptions in Websocket events).
- **Ping/Pong timeout** (Websockets require keepalive).

**Fixes:**
#### **Client-Side: Handle Reconnection Logic**
```javascript
let ws;
const reconnect = () => {
  ws = new WebSocket('wss://yourdomain.com/api/ws');
  ws.onclose = () => setTimeout(reconnect, 3000);
};
reconnect();

// Test with a simple reconnect loop
```
✅ **Implement automatic reconnection** – Use exponential backoff for robustness.

#### **Server-Side: Ensure Proper Cleanup**
**Node.js (Express + `ws`):**
```javascript
wss.on('connection', (ws) => {
  ws.on('error', (err) => console.error('Websocket error:', err));
  ws.on('close', () => console.log('Client disconnected'));

  ws.send('Message sent!');
});
```
✅ **Handle `error` events** – Prevent crashes from corrupt messages.

**Python (FastAPI):**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            await websocket.send(f"Echo: {data}")
    except Exception as e:
        print(f"Websocket error: {e}")
    finally:
        await websocket.close()
```
✅ **Use `try-finally`** – Ensures graceful shutdown.

#### **Network Stability Checks**
- **Test with `curl --websocket`** (to verify server responsiveness):
  ```bash
  curl --web-socket 'wss://yourdomain.com/api/ws' --data '{"test": "ping"}'
  ```
- **Check firewall rules** – Allow Websocket traffic (UDP/TCP ports).

---

### **Issue 3: Messages Not Delivered (Partial/Missing Data)**
**Symptoms:**
- Client receives no messages or corrupted data.
- Server logs show sent messages, but clients don’t receive them.

**Root Causes:**
- **Incorrect framing** (e.g., sending binary vs. text incorrectly).
- **Message size limits** (some servers cap payload size).
- **Rate limiting** (too many rapid messages).

**Fixes:**
#### **Client-Side: Verify Message Format**
```javascript
// Send text message
ws.send(JSON.stringify({ event: "chat", text: "Hello" }));

// Receive and parse
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.event, data.text);
};
```
✅ **Use `JSON.stringify`/`JSON.parse`** for consistency.
✅ **Check `event.data` type** – Ensure binary/text alignment.

#### **Server-Side: Enforce Proper Handling**
**Node.js:**
```javascript
wss.on('message', (message, client) => {
  if (typeof message === 'string') {
    const data = JSON.parse(message);
    client.send(JSON.stringify({ response: "OK" }));
  } else {
    client.close(1003, "Invalid payload"); // 1003: Policy Violation
  }
});
```
✅ **Validate input format** – Reject malformed messages.

**Python:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    while True:
        try:
            data = await websocket.receive_json()  # Expects JSON
            await websocket.send_json({"status": "received"})
        except ValueError:
            await websocket.close(1002, "Invalid JSON")
```
✅ **Use `receive_json`/`send_json`** for structured data.

---

### **Issue 4: Authentication/Authorization Failures**
**Symptoms:**
- `1008` (policy violation) on connection.
- Server rejects handshake.

**Root Causes:**
- Missing `Sec-WebSocket-Extensions` or `Authorization` headers.
- Invalid JWT tokens or missing cookies.

**Fixes:**
#### **Client-Side: Include Auth Headers**
```javascript
const ws = new WebSocket('wss://yourdomain.com/api/ws');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "auth",
    token: "your_jwt_token_here"
  }));
};
```
✅ **Send auth data immediately** – Some servers require it before data.

#### **Server-Side: Validate Headers**
**Node.js:**
```javascript
wss.on('connection', (ws, req) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    ws.close(1008, "Authorization required");
    return;
  }
  // Verify JWT or session token
});
```
✅ **Reject without auth** – Close with `1008` (policy violation).

**Python:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.headers.get("Authorization", None)
    if not token:
        await websocket.close(1008, "Missing token")
    # Validate token (e.g., using PyJWT)
```
✅ **Check headers in `websocket.headers`** – FastAPI passes WS headers here.

---

## **3. Debugging Tools & Techniques**

### **Browser DevTools**
- **WebSocket tab** – Monitor connections, messages, and errors.
- **Network tab** – Check for `101` (switching protocols) or `400` errors.
- **Console logs** – Debug `onopen`, `onmessage`, `onerror`.

### **Network Tools**
- **`wscat` (WebSocket CLI tool)** – Test connections manually:
  ```bash
  npx wscat -c wss://yourdomain.com/api/ws
  ```
- **`ngrok`** – Expose local Websocket dev server securely:
  ```bash
  ngrok http --scheme=https 8080
  ```
- **Packet capture (`tcpdump`/`Wireshark`)** – Inspect Websocket frames:
  ```bash
  tcpdump -i any port 8080
  ```

### **Server-Side Logging**
- **Log all Websocket events** (connection, message, close):
  ```javascript
  wss.on('connection', (ws) => {
    console.log('New connection:', ws.remoteAddress);
  });
  ```
- **Track message sizes** – Detect payload issues:
  ```python
  @app.websocket("/ws")
  async def websocket_endpoint(websocket: WebSocket):
      while True:
          data = await websocket.receive_bytes()  # For binary
          print(f"Received {len(data)} bytes")
  ```

---

## **4. Prevention Strategies**

### **Server-Side Best Practices**
✔ **Use HTTPS (`wss://`)** – Prevent MITM attacks.
✔ **Rate limit connections** – Avoid DoS:
  ```javascript
  const rateLimit = new RateLimiter({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000
  });
  ```
✔ **Implement heartbeat/ping-pong** – Detect dead connections:
  ```javascript
  wss.on('connection', (ws) => {
    setInterval(() => ws.ping(), 30000); // Ping every 30s
    ws.on('pong', () => console.log('Pong received'));
  });
  ```
✔ **Graceful shutdown** – Close Websockets on server restart:
  ```javascript
  process.on('SIGTERM', () => {
    wss.clients.forEach(client => client.close());
    process.exit(0);
  });
  ```

### **Client-Side Best Practices**
✔ **Reconnection with exponential backoff**:
  ```javascript
  let retryDelay = 1000;
  const reconnect = () => {
    setTimeout(() => {
      ws = new WebSocket('wss://yourdomain.com/api/ws');
      retryDelay *= 2;
    }, retryDelay);
  };
  ```
✔ **Message batching** – Reduce overhead for frequent updates.
✔ **Error handling** – Retry failed messages:
  ```javascript
  ws.onerror = (error) => {
    console.error('Websocket error:', error);
    if (error.code === 1006) { // Abnormal closure
      reconnect();
    }
  };
  ```

### **Security Hardening**
✔ **Origin validation** – Restrict allowed domains:
  ```javascript
  wss.on('connection', (ws, req) => {
    if (!allowedOrigins.includes(req.headers.origin)) {
      ws.close(1003, "Invalid origin");
    }
  });
  ```
✔ **Input sanitization** – Prevent injection attacks.
✔ **Use WebSocket subprotocols** – For custom negotiation:
  ```javascript
  const ws = new WebSocket('wss://yourdomain.com/api/ws', ['protocol-v1']);
  ```

---

## **Final Checklist for Resolution**
| **Step** | **Action** | **Expected Outcome** |
|----------|------------|----------------------|
| 1 | Verify Websocket URL (`ws://` vs. `wss://`) | Connection attempt succeeds |
| 2 | Check server Websocket upgrade support | No 404/400 errors in logs |
| 3 | Test with `wscat` or browser DevTools | Handshake completes |
| 4 | Monitor for reconnection issues | No `onclose` without warning |
| 5 | Validate message format (JSON/binary) | Data received intact |
| 6 | Enable logging on server/client | Errors surface in logs |

---
**If all else fails:**
- **Isolate the issue** – Test with a minimal echo server (e.g., `wscat`).
- **Check OS/network logs** – Firewall/proxy blocking?
- **Compare with working instances** – What’s different?

Websockets require careful tuning, but following this guide should resolve 90% of integration issues quickly. For persistent problems, share logs and network traces for deeper analysis.