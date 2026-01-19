# **[Pattern] Websockets Techniques Reference Guide**

---

## **Overview**
The **Websockets Techniques Pattern** enables **real-time, bidirectional communication** between a client (e.g., browser or mobile app) and a server over a single TCP connection. Unlike HTTP polling or Server-Sent Events (SSE), Websockets provide **low-latency, persistent connections** with minimal overhead, making them ideal for applications requiring instant updates (e.g., chat, live dashboards, collaborative tools, or IoT devices).

This guide covers **key concepts, implementation principles, protocol interactions, and best practices** for integrating Websockets into applications. It assumes familiarity with HTTP/1.1 and JavaScript fundamentals.

---

## **Implementation Details**

### **1. Core Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Websockets Protocol** | Defined by [RFC 6455](https://tools.ietf.org/html/rfc6455), enabling full-duplex communication over a single socket. Uses a **handshake** (initially via HTTP) before switching to the Websockets protocol. |
| **Handshake Process** | Client initiates with `GET /ws` (or similar), server responds with `101 Switching Protocols` if the upgrade is successful.                                                                                       |
| **Frames**            | Data is exchanged via **frames** (binary or text). Two types:                                                                                                                                             |
| - Control Frames      | Used for connection management (e.g., ping/pong, close).                                                                                                                                                     |
| - Data Frames         | Carry application data (text, binary).                                                                                                                                                                      |
| **Masking**           | Clients (browsers) **must mask** their data frames with a 32-bit mask to prevent MITM attacks. Servers do not mask.                                                                                           |
| **Subprotocols**      | Clients and servers can negotiate optional subprotocols (e.g., `chat`, `json-patch`).                                                                                                                     |
| **Connection States** | `CONNECTING`, `OPEN`, `CLOSING`, `CLOSED`. Errors or timeouts may trigger `CLOSING`.                                                                                                                       |

### **2. Message Flow**
1. **Handshake**
   - Client sends `GET ws://example.com/socket HTTP/1.1` with headers like `Connection: Upgrade`, `Upgrade: websocket`, and `Sec-WebSocket-Key`.
   - Server validates the key (via SHA-1 + GUID) and responds with `HTTP/1.1 101 Switching Protocols`.

2. **Frame Exchange**
   - Binary/text frames are sent/received asynchronously. Each frame begins with an **8-byte header** (opcode, mask, length, etc.).

3. **Closing**
   - Initiated with a `Close` control frame (status code, reason text). Both parties must acknowledge.

---

## **Schema Reference**
A Websockets message follows this **binary frame structure**:

| Byte(s)       | Field               | Details                                                                                                                                                                                                 |
|----------------|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1**          | `FIN` + `RSV1-3`    | `FIN`: 1 = last frame in message; `RSV`: reserved (must be 0).                                                                                                                                              |
| **1**          | **Opcode**          | Indicates frame type (e.g., `0x0`=continuation, `0x1`=text, `0x2`=binary, `0x8`=close).                                                                                                                |
| **7**          | **Mask** + **Payload Length** | `Mask`: 1 = client-sent data is masked; length: 7 bits for ≤125 bytes, extended length for larger payloads.                                                                                                  |
| **Variable**   | **Masking Key**     | 4-byte array (if masked).                                                                                                                                                                              |
| **Variable**   | **Payload**         | Data (text/binary).                                                                                                                                                                                        |

**Example Text Frame (19-byte header + 4-byte mask + "hello"):**
```
FIN:1 RSV:000 Opcode:0x1 (Text), Masked:1, Length:4
[Mask: 0x3D 0x29 0x0D 0xDE] "hello" (after XOR with mask)
```

---

## **Query Examples**

### **1. Handshake (Client-Side)**
```javascript
// JavaScript: Upgrade from HTTP to Websockets
const socket = new WebSocket("wss://example.com/socket");
socket.onopen = () => console.log("Connected!");
socket.onmessage = (event) => console.log("Message:", event.data);
```
**Headers sent by client:**
```
GET /socket HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

### **2. Server-Side (Node.js Example)**
```javascript
// Using the 'ws' library
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    console.log("Received:", data.toString());
    ws.send("ACK"); // Echo back
  });
});
```

### **3. Sending Messages**
```javascript
// Client sends JSON data
socket.send(JSON.stringify({ type: "chat", text: "Hello!" }));

// Server processes binary data (e.g., sensor data)
ws.on('message', (binaryData) => {
  const parsed = JSON.parse(new TextDecoder().decode(binaryData));
  console.log(parsed);
});
```

### **4. Closing Gracefully**
```javascript
// Client-initiated close (status code 1000 = normal closure)
socket.close(1000, "Goodbye");

// Server-initiated close
ws.close(1008, "Invalid payload"); // 1008 = protocol error
```

### **5. Advanced: Subprotocols & Ping/Pong**
```javascript
// Negotiate subprotocol
const socket = new WebSocket("wss://example.com/socket", ["chat"]);

// Ping/pong for heartbeats
socket.on("ping", () => socket.send("pong"));
```

---

## **Edge Cases & Error Handling**
| Scenario               | Solution                                                                                                                                                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Masking Issues**     | Ensure client masks data frames (servers cannot mask). Validate masks in custom implementations.                                                                                                         |
| **Connection Drops**   | Reconnect logic (exponential backoff): `setInterval(() => socket.reconnect(), delay)` (use libraries like `reconnecting-websocket`).                                                                |
| **Memory Leaks**       | Close sockets explicitly (`ws.close()`) to free resources.                                                                                                                                               |
| **Large Payloads**     | Fragment data into multiple frames (FIN=0 until the last frame).                                                                                                                                      |
| **Authentication**     | Use custom headers (e.g., `Sec-WebSocket-Protocol: auth=Bearer xyz`) or upgrade tokens via the handshake (see [RFC 7692](https://tools.ietf.org/html/rfc7692)). |

---

## **Performance Considerations**
| Technique               | Benefit                                                                                                                                                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Compression**         | Enable `permessage-deflate` subprotocol for large text payloads (but adds CPU overhead).                                                                                                              |
| **Connection Pooling**  | Reuse connections (e.g., long-lived sessions) instead of opening/closing.                                                                                                                            |
| **Heartbeats**          | Send/pong frames to detect dead connections (e.g., every 30 seconds).                                                                                                                              |
| **Binary Frames**       | Use binary frames for non-text data (e.g., images, protocol buffers) to reduce overhead.                                                                                                               |
| **Scalability**         | Use a reverse proxy (e.g., Nginx) or load balancer to distribute Websockets connections.                                                                                                          |

---

## **Related Patterns**

| Pattern                          | Relationship to Websockets                                                                                                                                                                                                 |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Event-Driven Architecture](https://patterns.dev/catalog/event-driven)** | Websockets enable **publish-subscribe** models for real-time event distribution.                                                                                                                           |
| **[Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)** | SSE is unidirectional (server → client); Websockets support **bidirectional** communication. Use SSE for one-way updates (e.g., stock prices).                                                       |
| **[Long Polling](https://en.wikipedia.org/wiki/Push_technology#Long_polling)** | Websockets replace long polling by maintaining a **persistent connection** instead of repeatedly opening/closing HTTP connections.                                                                             |
| **[GraphQL Subscriptions](https://graphql.org/learn/subscriptions/)**       | Websockets can power GraphQL subscriptions for **real-time query updates** (e.g., `onCreateUser`).                                                                                                       |
| **[Webhooks](https://www.postman.com/learning/webhooks)**               | Unlike Webhooks (server → client callbacks), Websockets provide **client-driven** real-time interactions (e.g., live collaboration tools).                                                               |
| **[gRPC Web](https://grpc.io/blog/grpc-web/)**                          | gRPC Web uses HTTP/2 with binary frames; Websockets can emulate gRPC-like RPCs with custom framing.                                                                                                       |

---

## **Tools & Libraries**
| Tool/Library         | Purpose                                                                                                                                                                                                 |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Browser API**      | Native `WebSocket` support in all modern browsers.                                                                                                                                                     |
| **Node.js (`ws`)**   | [`ws`](https://www.npmjs.com/package/ws) – Lightweight Websockets library for Node.js.                                                                                                                  |
| **Python (`websockets`)** | [`websockets`](https://pypi.org/project/websockets/) – Asyncio-based Websockets server.                                                                                                                 |
| **Go (`gorilla/websocket`)** | [`gorilla/websocket`](https://github.com/gorilla/websocket) – Websockets for Go.                                                                                                                          |
| **Testing**          | [`ws`](https://www.npmjs.com/package/ws) + `websockify` (for local testing), or browser DevTools "Network" tab (filter by `ws://`).                                                                 |
| **Monitoring**       | Track connections with tools like **Prometheus** (expose metrics via `/metrics` endpoint) or **Datadog**.                                                                                            |

---
## **Security Best Practices**
1. **Use WSS (wss://)** to encrypt traffic with TLS.
2. **Validate Origins**: Restrict connections via `Origin` header (e.g., `if (!allowedOrigins.includes(ws.request.headers.origin)) ws.close()`).
3. **Rate Limiting**: Prevent abuse (e.g., cap messages/second per connection).
4. **Input Sanitization**: Reject malformed frames or oversized payloads.
5. **Authenticate Early**: Use tokens in the handshake (e.g., `Sec-WebSocket-Protocol: auth=Bearer <token>`).

---
## **Troubleshooting**
| Symptom                     | Check                                                                                                                                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Handshake Fails**         | Verify `Sec-WebSocket-Key` calculation (client) and server response headers.                                                                                                                            |
| **Data Corruption**         | Ensure masking is applied correctly (client-side).                                                                                                                                                     |
| **Connection Drops**       | Check for network timeouts or firewalls blocking Websockets (port 80/443).                                                                                                                          |
| **Memory High Usage**       | Leaky connections? Ensure `onclose` handlers are called.                                                                                                                                                 |
| **Slow Performance**       | Profile with Chrome DevTools (Network tab); consider compression or binary frames.                                                                                                                    |

---
## **Further Reading**
- [RFC 6455](https://tools.ietf.org/html/rfc6455) – Websockets Protocol.
- [MDN Websockets Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API).
- [Nginx Websockets Proxy](https://docs.nginx.com/nginx/admin-guide/web-tutorials/nginx-websockets/).
- [Subprotocol RFC 7692](https://tools.ietf.org/html/rfc7692) – Authentication via handshake.