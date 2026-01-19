---
# **[Pattern] Websockets Setup Reference Guide**

---

## **Overview**
Websockets provide full-duplex, bidirectional communication between clients and servers over a **single, persistent TCP connection**, eliminating the inefficiencies of HTTP polling or long-polling. This guide outlines how to set up Websockets in applications, including server configuration, client integration, and security best practices.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example Use Case**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Websocket Protocol** | A protocol for real-time, bidirectional communication via HTTP upgrade (WS/WSS).                 | Live chat, stock tickers, multiplayer games.                                                          |
| **Handshake**          | Initial HTTP request/response exchange to establish a Websocket connection.                     | Client sends `Sec-WebSocket-Key`; server responds with `101 Switching Protocols`.                     |
| **Frames**             | Data packets exchanged over the Websocket connection (opcode-based).                             | Text (`0x1`), binary (`0x2`), ping (`0x9`), or close (`0x8`) frames.                                   |
| **Connection States**  | `CONNECTING`, `OPEN`, `CLOSING`, `CLOSED` (RFC 6455).                                              | Handling reconnects after a `CLOSE` frame.                                                          |
| **Scalability**        | Requires load balancing or message brokers (e.g., Redis, RabbitMQ) for high-volume setups.         | Scaling a Websocket server in a microservices architecture.                                          |
| **Security**           | Encrypts traffic via TLS (`wss://`) and validates origins via headers (e.g., `Origin`).           | Secure real-time payments or remote collaboration tools.                                             |

---

## **Implementation Requirements**
### **Server-Side Setup**
#### **1. Language-Specific Frameworks**
| **Framework**          | **Key Features**                                                                                     | **Example Library**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Node.js**            | Lightweight, async I/O model.                                                                       | `ws` (low-level), `Socket.IO` (higher-level with fallbacks).                                           |
| **Python**             | High scalability with `asyncio`.                                                                     | `websockets` (async), `FastAPI` (Websocket integration).                                               |
| **Java**               | Enterprise-grade, supports clustering.                                                               | `Tomsocket`, `Java WebSocket API (JSR-356)`.                                                          |
| **Go**                 | High performance, minimal overhead.                                                                  | `gorilla/websocket`.                                                                                   |
| **.NET**               | Built-in support via `Kestrel` or `SignalR`.                                                       | `Microsoft.AspNetCore.SignalR`.                                                                        |
| **Ruby**               | Simple, Ruby-centric API.                                                                           | `Thin`, `Puma` with `actioncable-rails`.                                                              |

#### **2. Core Configuration Steps**
```sh
# Example: Node.js (Express + ws)
const WebSocket = require('ws');
const express = require('express');

const app = express();
const server = app.listen(3000);
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    console.log(`Received: ${data}`);
    ws.send(`Echo: ${data}`);
  });
});
```
**Key Parameters:**
- `port`: Must match client connection (e.g., `:3000`).
- `origin`: Whitelist domains (e.g., `wss://client.example.com`).
- `maxPayload`: Limit frame size (default: 16MB).

---

### **Client-Side Setup**
#### **1. Browser API**
```javascript
// JavaScript WebSocket Constructor
const socket = new WebSocket('wss://api.example.com/ws');

socket.onopen = () => {
  console.log('Connected');
  socket.send(JSON.stringify({ type: 'login', user: '123' }));
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message:', data);
};

socket.onclose = () => {
  console.log('Disconnected');
};
```
**Headers:**
- `Sec-WebSocket-Protocol`: Negotiate subprotocols (e.g., `chat`, `metrics`).
- `Sec-WebSocket-Extensions`: Encode binary data (e.g., `permessage-deflate`).

#### **2. Mobile Frameworks**
| **Framework** | **Implementation**                                                                                     |
|---------------|-------------------------------------------------------------------------------------------------------|
| **Flutter**   | `dart:html` for Web, `dart:io` for mobile via `web_socket_channel`.                                  |
| **React Native** | [`react-native-websocket`](https://github.com/Perolov/react-native-websocket).                          |
| **Kotlin (Android)** | `OkHttp.WebSocket`.                                                                                   |

---

## **Schema Reference**
### **Websocket Handshake Headers**
| **Header**               | **Purpose**                                                                                     | **Example Value**                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| `Sec-WebSocket-Key`      | Unique key for challenge-response authentication.                                                | `dGhlIHNhbXBsZSBub25jZQ==` (base64-encoded).                                                          |
| `Sec-WebSocket-Version`  | Specifies Websocket protocol version (default: `13`).                                             | `13`.                                                                                                  |
| `Upgrade`                | Indicates the client wishes to upgrade from HTTP.                                               | `websocket`.                                                                                            |
| `Connection`             | Lists protocols to upgrade to.                                                                    | `Upgrade, Sec-WebSocket-Protocol`.                                                                     |
| `Sec-WebSocket-Extensions` | Supports compression or other extensions.                                                         | `permessage-deflate`.                                                                                   |

### **Frame Structure (Binary)**
| **Byte (0-1)** | **Opcode** | **Meaning**                                                                                     |
|----------------|------------|---------------------------------------------------------------------------------------------------|
| `0x01`         | Text       | UTF-8 encoded string.                                                                        |
| `0x02`         | Binary     | Raw binary data.                                                                               |
| `0x08`         | Close      | Indicates connection termination.                                                               |
| `0x09`         | Ping       | Server/client ping (RFC 6455).                                                                |
| `0x0A`         | Pong       | Response to `Ping`.                                                                             |

**Masking Bit:** The 7th bit (MSB) in the first byte indicates whether data is masked (client → server).

---

## **Query Examples**
### **1. Server-Side Event Handling (Node.js)**
```javascript
// Broadcast to all clients
wss.clients.forEach((client) => {
  if (client.readyState === WebSocket.OPEN) {
    client.send(JSON.stringify({ type: 'update', data: { time: new Date() } }));
  }
});

// Handle ping/pong
wss.on('ping', () => wss.pong());
```

### **2. Client-Side Connection Management**
```javascript
// Reconnect logic
let socket;
const reconnect = () => {
  socket = new WebSocket('wss://api.example.com/ws');
  socket.onopen = () => console.log('Reconnected');
};
socket.onclose = () => setTimeout(reconnect, 5000);
```

### **3. Query Parameters (URL)**
Websockets support query strings for dynamic routing:
```
wss://api.example.com/ws?user_id=123&room=lobby&protocol=chat
```
**Server-side (Node.js):**
```javascript
wss.on('connection', (ws, req) => {
  const { user_id, room } = new URL(req.url, 'https://api.example.com').searchParams;
  ws.user_id = user_id;
  ws.room = room;
});
```

---

## **Security Best Practices**
| **Risk**               | **Mitigation**                                                                                     | **Example**                                                                                            |
|------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Man-in-the-Middle**  | Enforce TLS (`wss://`).                                                                        | Redirect HTTP → HTTPS with `Location` header.                                                          |
| **Origin Spoofing**    | Validate `Origin`/`Sec-WebSocket-Origin` headers.                                                 | `if (req.headers.origin !== 'https://trusted.example.com') reject()`.                               |
| **DDoS**               | Rate-limit connections (e.g., 1000 connections/second).                                          | Use `ws.maxBacklog` or a reverse proxy (Nginx).                                                         |
| **Authentication**     | JWT or session tokens in first message.                                                          | `socket.on('message', (data) => { if (!validateToken(data)) reject() })`.                          |
| **Payload Tampering**  | Use HMAC for critical frames.                                                                     | Sign messages with `HMAC-SHA256`.                                                                       |

---

## **Performance Optimization**
| **Technique**          | **Description**                                                                                     | **Tool/Library**                                                                                      |
|------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Compression**        | Enable `permessage-deflate` for large payloads.                                                    | `wss://?extensions=permessage-deflate`.                                                              |
| **Load Balancing**     | Use sticky sessions (e.g., NGINX with `proxy_set_header`).                                          | NGINX `upstream ws_cluster { ... }`.                                                                   |
| **Message Queuing**    | Offload processing to Celery/RabbitMQ for async tasks.                                              | `Socket.IO` with `adapter: redisAdapter`.                                                             |
| **Heartbeats**         | Pings every 30s to detect dead connections.                                                        | Set `pingInterval` (client/server).                                                                  |

---

## **Related Patterns**
1. **[HTTP/2 & Websockets]** – Leverage HTTP/2 multiplexing for Websockets over the same port.
2. **[Server-Sent Events (SSE)]** – Unidirectional (server → client) alternative to Websockets.
3. **[SignalR (Microsoft)]** – Higher-level abstraction for Websockets + fallback protocols.
4. **[WebTransport]** – Future-proof protocol for reliable/ordered streams (experimental).
5. **[Message Brokers]** – Decouple Websocket clients from servers using Redis/PubSub.

---
## **Troubleshooting**
| **Issue**               | **Diagnosis**                                                                                     | **Solution**                                                                                             |
|-------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Handshake Fails**     | Missing `Sec-WebSocket-Key` or invalid signature.                                                 | Check browser console for `Sec-WebSocket-Accept` mismatch.                                              |
| **Connection Drops**    | Network issues or invalid `ping`/`pong`.                                                          | Implement exponential backoff for reconnects.                                                            |
| **Memory Leaks**        | Unclosed sockets or lingering listeners.                                                          | Use `ws.on('close', () => ws.terminate())` in Node.js.                                                  |
| **Cross-Origin Errors** | Invalid `Origin` header.                                                                        | Configure CORS: `wss.on('connection', (ws, req) => { if (req.headers.origin === '...') {...}}}}`. |

---
## **Further Reading**
- [RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455) – Websockets spec.
- [Socket.IO Guide](https://socket.io/docs/) – Fallback mechanisms (Websockets → HTTP long-polling).
- [Kubernetes Websocket Ingress](https://kubernetes.io/docs/tasks/run-application/ingress-websocket/) – Deploying Websockets in K8s.