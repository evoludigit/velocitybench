---
# **[Pattern] WebSocket & Real-time Patterns – Reference Guide**
*Designing Scalable Real-Time Applications with Bidirectional Communication*

---

## **1. Overview**
This guide details the **WebSocket & Real-time Patterns**, enabling **persistent, low-latency bidirectional communication** between clients and servers. Unlike traditional HTTP polling or long polls, WebSockets establish a single, open connection, reducing overhead and enabling real-time updates (e.g., chat apps, live dashboards, collaborative editing). This pattern covers:
- Core WebSocket mechanics (connection lifecycle, framing, protocols).
- Common real-time use cases (push notifications, signaling, presence systems).
- **Implementation best practices** (scaling, security, fallbacks, and hybrid architectures).
- **Advanced patterns** (message queues, long-polling fallbacks, and WebSocket relay services).

---
## **2. Schema Reference**
| **Component**               | **Description**                                                                 | **Key Attributes**                                                                 | **Example Values**                          |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------|
| **WebSocket Connection**    | Persistent bi-directional connection between client and server.                | - `Connection State`: `CONNECTING`, `OPEN`, `CLOSING`, `CLOSED`                | `ws://example.com/ws`                      |
| **Frame Header**            | Defines the type and payload of each message (RFC 6455).                      | - `FIN` (1-bit): Message completion flag                                         | `FIN=1 (final frame)`                       |
| **Frame Payload**           | Encoded data (text, binary, or opaque).                                     | - `Opcode`: `0x1` (Text), `0x2` (Binary), `0x8` (Close)                         | `{"event": "update", "data": "value"}`       |
| **Pong/Ping Frames**        | Heartbeat mechanism to detect dead connections.                               | - `Opcode`: `0x9` (Ping), `0xA` (Pong)                                          | `Ping: {"keepalive": true}`                 |
| **Error Frames**            | Server-side or peer errors (e.g., protocol violations).                      | - `Close Code`: `1008` (Policy Violation)                                        | `Close: {"code": 1008, "reason": "Rate limit"}` |
| **Scaling Layer**           | Middleware (e.g., Redis, Socket.io) to distribute connections across servers.| - `Sharding Key`: Unique identifier for client grouping                          | `user_id:12345`                             |
| **Authentication**          | Secure handshake (JWT, OAuth2 tokens, or custom headers).                     | - `Auth Header`: `Authorization: Bearer <token>`                                 | `Bearer eyJhbGciOiJIUzI1Ni...`               |
| **Message Queue**           | Offloads real-time processing (e.g., Kafka, RabbitMQ).                        | - `Queue Topic`: `notifications`, `updates`                                       | `topic:notifications`                       |
| **Hybrid Fallback**         | Graceful degradation to long-polling if WebSockets fail.                     | - `Timeout`: 30 seconds (long-poll duration)                                      | `ws://fallback.example.com/poll?timeout=30` |

---
## **3. Implementation Details**

### **3.1 Core WebSocket Lifecycle**
1. **Handshake**:
   - Client sends `HTTP Upgrade` header: `Connection: Upgrade, websocket`.
   - Server responds with `HTTP 101 Switching Protocols`.
2. **Connection State**:
   - **`CONNECTING`**: Handshake in progress.
   - **`OPEN`**: Active communication (frames exchanged).
   - **`CLOSING`**: Graceful shutdown (Close frame sent).
   - **`CLOSED`**: Connection terminated.
3. **Frame Structure**:
   - **Header**: `FIN`, `Opcode`, `Mask` (client-side), `Length` (payload size).
   - **Payload**: UTF-8 (text) or binary data (e.g., Protocol Buffers).

---
### **3.2 Real-Time Patterns**
| **Pattern**               | **Use Case**                          | **Implementation**                                                                 | **Example Code Snippet**                          |
|---------------------------|---------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------|
| **Publish-Subscribe**     | Live updates (e.g., stock ticker).    | Server broadcasts to subscribed clients via WebSocket topic.                       | `server.publish('ticker', {symbol: 'AAPL', price: 150.50});` |
| **Signaling**             | Peer-to-peer interactions (e.g., video calls). | Clients exchange metadata (e.g., SDP offers/answers) via WebSocket.          | `client.send(JSON.stringify({type: 'offer', sdp: '...'}));` |
| **Presence System**       | Track online users (e.g., chat apps). | Server maintains a `user_status` map.                                              | `server.on('connection', user => { user.join('room1'); });` |
| **Long-Polling Fallback** | Degrade gracefully if WebSockets fail.| Use HTTP long-polling with `Connection: keep-alive`.                              | `setInterval(() => pollServerForUpdates(), 30000);` |

---
### **3.3 Scaling Strategies**
1. **Horizontal Scaling**:
   - Use a **WebSocket gateway** (e.g., Socket.io, Pusher) to route connections to backend servers.
   - **Sharding**: Partition clients by a key (e.g., `user_id`) to distribute load.
2. **Message Queues**:
   - Offload processing to async queues (e.g., Kafka, RabbitMQ) for high-throughput events.
   - Example: Chat messages → Queue → Database → Broadcast to users.
3. **Connection Management**:
   - **Heartbeats**: Send `Ping`/`Pong` frames every 30 seconds to detect dead connections.
   - **Reconnections**: Exponential backoff for client disconnections.

---
### **3.4 Security Considerations**
| **Threat**               | **Mitigation**                                                                 |
|--------------------------|-------------------------------------------------------------------------------|
| **Man-in-the-Middle (MITM)** | Use **WSS** (WebSocket Secure) with TLS.                                     |
| **DDoS Attacks**         | Rate-limit connections (e.g., 1000 connections/user).                          |
| **Protocol Exploits**    | Validate frames (e.g., reject oversized payloads).                            |
| **Unauthorized Access**  | Authenticate via JWT/OAuth2 in the handshake.                                 |
| **Data Tampering**       | Use **HMAC** for signed messages.                                             |

---
## **4. Query Examples**
### **4.1 Client-Side (JavaScript)**
```javascript
// Connect to WebSocket
const socket = new WebSocket('wss://api.example.com/ws');
socket.addEventListener('open', () => {
  socket.send(JSON.stringify({ event: 'subscribe', channel: 'news' }));
});

// Handle messages
socket.addEventListener('message', (event) => {
  console.log('Received:', JSON.parse(event.data));
});

// Close connection
socket.close();
```

### **4.2 Server-Side (Node.js with `ws` Library)**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  // Broadcast to all clients
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ type: 'announcement', message: 'Server update!' }));
    }
  });

  // Handle messages
  ws.on('message', (data) => {
    const message = JSON.parse(data);
    if (message.event === 'subscribe') {
      ws.channel = message.channel; // Assign channel for pub/sub
    }
  });
});
```

### **4.3 Long-Polling Fallback (Python/Flask)**
```python
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/poll', methods=['GET'])
def poll():
    timeout = int(request.args.get('timeout', 30))
    # Simulate real-time data fetch (e.g., from database)
    data = {"status": "update", "value": 42}
    return jsonify(data)

if __name__ == '__main__':
    app.run()
```

---
## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Long-Polling](link)**  | HTTP-based real-time alternative (simpler but higher latency).                 | Legacy support or WebSocket unavailable.         |
| **[Server-Sent Events (SSE)](link)** | Unidirectional server-to-client updates (HTML5 native).               | Simple push notifications (e.g., alerts).       |
| **[Message Brokers](link)** | Decouple producers/consumers (e.g., Kafka, RabbitMQ).                      | High-throughput event streaming.                |
| **[GraphQL Subscriptions](link)** | Real-time GraphQL queries via WebSocket.                                       | APIs with real-time data (e.g., dashboards).     |
| **[Peer-to-Peer (P2P)](link)** | Direct client-to-client communication (e.g., WebRTC).                      | Low-latency apps (e.g., gaming, video calls).   |

---
## **6. Best Practices Checklist**
1. **Optimize Performance**:
   - Enable **compression** (`rfc7692`) for text payloads.
   - Use **binary frames** for non-text data (e.g., WebP images).
2. **Error Handling**:
   - Implement retry logic for reconnections.
   - Log close codes (e.g., `1000`: Normal, `1008`: Policy Violation).
3. **Scalability**:
   - Test with **load testing tools** (e.g., Locust).
   - Monitor **connection count** and **throughput**.
4. **Security**:
   - Enforce **TLS 1.2+** for all WebSocket connections.
   - Validate **auth tokens** on every frame.
5. **Fallbacks**:
   - Combine WebSocket with **long-polling** for graceful degradation.
6. **Monitoring**:
   - Track **latency**, **dropped connections**, and **message rates**.
   - Use tools like **Prometheus** + **Grafana**.

---
## **7. Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                 |
|--------------------------------------|------------------------------------------------------------------------------|
| **Connection Drops**                 | Implement **reconnection logic** with exponential backoff.                   |
| **Memory Leaks**                     | Close `WebSocket` connections explicitly (`ws.close()`).                    |
| **Protocol Violations**              | Validate frames with libraries like [`ws`](https://github.com/websockets/ws). |
| **Cross-Origin Issues**              | Use **CORS** or **proxy** for `ws://` origins.                              |
| **High Latency**                     | Deploy servers closer to users (e.g., **CDN-based WebSockets**).             |

---
## **8. Further Reading**
- [RFC 6455: The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [Socket.io Documentation](https://socket.io/docs/v4/)
- [WebSocket Security Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)
- [Real-Time Strategies with Redis](https://redis.io/topics/real-time)