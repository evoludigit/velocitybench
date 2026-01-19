**[Pattern] Websockets Best Practices – Reference Guide**

---

### **Overview**
WebSockets provide persistent, bidirectional, and low-latency communication between a client and server over a single TCP connection. Unlike HTTP long-polling or Server-Sent Events (SSE), WebSockets maintain a single persistent connection, reducing overhead for real-time applications (e.g., chat apps, live dashboards, gaming, and collaborative tools).

To ensure reliability, scalability, and security, follow these best practices for WebSocket implementation:
- **Connection Management**: Securely establish and recover from dropped connections.
- **Error Handling**: Implement robust retry logic and graceful fallbacks for unreliable networks.
- **Scalability**: Use connection pooling, load balancing, and efficient message serialization.
- **Security**: Enforce TLS/WSS (WebSocket Secure) and validate data integrity.
- **Performance**: Minimize bandwidth usage by compressing messages and using binary protocols.
- **State Management**: Maintain consistent client-server state to handle reconnections without data loss.

---

### **Schema Reference**
The following table outlines key WebSocket configuration and payload structures.

| **Component**          | **Description**                                                                 | **Format/Example**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **WebSocket Upgrade Header** | HTTP headers sent during WebSocket handshake.                                | `Upgrade: websocket` <br> `Connection: Upgrade` <br> `Sec-WebSocket-Key: ...`    |
| **Server-Side Config** | Backend settings for WebSocket server.                                        | `{ host: "0.0.0.0", port: 8080, path: "/ws", maxPayload: 1MB }`                   |
| **Client Connection**  | Client-side WebSocket connection options.                                      | `new WebSocket("wss://example.com/ws", ["subprotocol"])`                         |
| **Message Payload**    | Structure of messages sent/received (JSON or binary).                         | `{"type": "chat", "data": "Hello", "timestamp": 12345}`                          |
| **Ping/Pong Frames**   | Keeping the connection alive.                                                 | `Ping: opcode 0x9` <br> `Pong: opcode 0xA`                                        |
| **Close Frame**        | Graceful connection termination.                                              | `{ code: 1000, reason: "Leaving chat" }`                                           |
| **Reconnection Policy**| Logic for handling lost connections.                                          | `{ maxRetries: 5, retryDelay: [1000, 2000, 4000, 8000, 16000] }`                |

---

### **Implementation Details**

#### **1. Connection Management**
- **Handshake Security**: Always use `wss://` (WebSocket Secure) to encrypt traffic. Validate the `Sec-WebSocket-Key` and `Sec-WebSocket-Version` headers.
  ```javascript
  // Server-side handshake validation (Node.js)
  if (!req.headers['sec-websocket-key'] || req.headers['sec-websocket-version'] !== '13') {
      res.writeHead(400);
      res.end('Invalid WebSocket upgrade request');
      return;
  }
  ```
- **Client-Side Reconnection**: Implement exponential backoff for reconnects after disconnections.
  ```javascript
  // Client reconnection logic (JavaScript)
  let retryCount = 0;
  const maxRetries = 5;
  const timeout = (retryCount) => Math.min(1000 * Math.pow(2, retryCount), 30000);

  ws.on('close', () => {
      if (retryCount < maxRetries) {
          setTimeout(() => {
              ws = new WebSocket(URL);
              retryCount++;
          }, timeout(retryCount));
      }
  });
  ```

#### **2. Error Handling & Fallbacks**
- **Monitor Connection Stability**: Use `onopen`, `onclose`, and `onerror` events to detect issues.
  ```javascript
  ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      // Fallback to HTTP polling if WebSocket fails
      fallbackToHttpPolling();
  };
  ```
- **Message Validation**: Reject malformed or attacker-generated messages.
  ```javascript
  // Example: Validate JSON payload size
  if (JSON.parse(message).size > MAX_PAYLOAD) {
      ws.close(1003, 'Message too large');
  }
  ```

#### **3. Scalability**
- **Connection Pooling**: Limit concurrent connections per client to avoid resource exhaustion.
  ```javascript
  // Example: Rate-limiting connections (Node.js with jwt)
  const maxConnections = 10;
  const activeConnections = new Set();

  app.use((req, res, next) => {
      if (activeConnections.size >= maxConnections) {
          return res.status(429).send('Too many connections');
      }
      activeConnections.add(req.connection);
      next();
  });
  ```
- **Load Balancing**: Deploy WebSocket servers behind a reverse proxy (e.g., Nginx, Envoy) with sticky sessions.
  ```nginx
  # Nginx WebSocket load balancing config
  upstream websocket_backend {
      ip_hash;
      server ws1:8080;
      server ws2:8080;
  }

  server {
      listen 80;
      location /ws/ {
          proxy_pass http://websocket_backend;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
      }
  }
  ```

#### **4. Security**
- **TLS/WSS**: Enforce TLS 1.2+ endpoints. Use certificate rotation and HSTS (HTTP Strict Transport Security).
- **Authentication**: Validate tokens (JWT/OAuth) during handshake or via initial message.
  ```javascript
  // JWT validation on handshake
  const token = req.headers['sec-websocket-protocol']?.split(' ')[1];
  if (!validateJWT(token)) {
      ws.close(1008, 'Unauthorized');
  }
  ```
- **Rate Limiting**: Prevent DoS attacks with connection/throttle limits.
  ```javascript
  // Rate-limiting middleware (Node.js)
  const rateLimit = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100 // limit each IP to 100 connections per windowMs
  });
  ```

#### **5. Performance**
- **Compression**: Enable `permessage-deflate` for large text payloads.
  ```javascript
  // Client-side compression enable
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => {
      ws.send(JSON.stringify({ compress: true }));
  };
  ```
- **Binary Frames**: Use `ArrayBuffer` or `Blob` for non-JSON data (e.g., audio, images).
  ```javascript
  // Send binary data
  const blob = new Blob([imageData], { type: 'image/png' });
  ws.send(blob);
  ```
- **Efficient Serialization**: Prefer `Protocol Buffers` or `MessagePack` over JSON for high-frequency data.

#### **6. State Management**
- **Client-Side State**: Store session data locally (e.g., `localStorage`) and sync on reconnect.
  ```javascript
  // Persist state on close
  ws.onclose = () => {
      localStorage.setItem('lastMessageId', lastMessageId);
  };
  ```
- **Server-Side State**: Use a database (e.g., Redis) to persist client states during disconnections.
  ```javascript
  // Redis-based session persistence
  const redis = require('redis');
  const client = redis.createClient();

  ws.on('message', (data) => {
      client.hset(`ws:${ws.id}`, 'lastMessage', data);
  });
  ```

---

### **Query Examples**
The following examples demonstrate common WebSocket operations.

#### **1. Client-Side Connection**
```javascript
// Establish connection with subprotocol
const ws = new WebSocket('wss://example.com/ws', ['chat-v1']);

// Send message
ws.send(JSON.stringify({ type: 'message', text: 'Hello' }));

// Handle events
ws.onmessage = (event) => {
    console.log('Received:', event.data);
};
```

#### **2. Server-Side Message Handling (Node.js)**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
    ws.on('message', (message) => {
        const data = JSON.parse(message);
        if (data.type === 'chat') {
            broadcast(JSON.stringify({ type: 'echo', text: data.text }));
        }
    });

    // Handle client disconnection
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Broadcast to all clients
function broadcast(message) {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}
```

#### **3.Graceful Close**
```javascript
// Client-side close
ws.close(1000, 'Leaving chat'); // 1000 = normal closure code

// Server-side forced close
ws.close(1008, 'Policy violation'); // 1008 = invalid message
```

---

### **Related Patterns**
1. **[Long-Polling/Short-Polling](https://docs.acme.io/patterns/long-polling)**: Fallback for WebSocket unreliable environments.
2. **[Server-Sent Events (SSE)](https://docs.acme.io/patterns/sse)**: One-way server-to-client updates (e.g., live notifications).
3. **[WebSocket Compression](https://docs.acme.io/patterns/compression)**: Optimize message size for high-frequency data.
4. **[Rate Limiting](https://docs.acme.io/patterns/rate-limiting)**: Protect WebSocket endpoints from abuse.
5. **[JWT Authentication](https://docs.acme.io/patterns/auth-jwt)**: Secure WebSocket handshakes with tokens.

---
### **Key Takeaways**
| **Goal**               | **Action Item**                                                                 |
|------------------------|--------------------------------------------------------------------------------|
| **Reliability**        | Implement reconnection logic with exponential backoff.                          |
| **Security**           | Enforce WSS, validate tokens, and limit connections.                           |
| **Scalability**        | Use connection pooling and load balancing.                                     |
| **Performance**        | Compress messages and use binary framing for non-JSON data.                    |
| **State Management**   | Persist client state locally and server-side.                                  |