**[Pattern] WebSockets Patterns – Reference Guide**

---

### **1. Overview**
WebSockets enable **full-duplex, low-latency bidirectional communication** between clients and servers over a single TCP connection. Unlike traditional HTTP (request/response), WebSockets maintain persistent connections, making them ideal for real-time applications (chats, live dashboards, collaborative editing, IoT telemetry). This guide covers fundamental WebSocket patterns, their use cases, message schemas, and implementation best practices.

Key advantages:
- **Efficiency**: Avoids repeated TCP handshakes (reduces overhead).
- **Real-time**: Immediate push updates without client polling.
- **Scalability**: Suitable for chat, multiplayer games, and publish-subscribe systems.
- **Flexibility**: Supports custom framing and binary/text payloads.

---

### **2. Core WebSockets Patterns**

#### **A. Publish-Subscribe (PubSub)**
**Use Case**: Event-based systems (e.g., stock tickers, notifications).
**Flow**:
1. Clients subscribe to topics/topics (e.g., `WS://server/subs?topic=stocks:AAPL`).
2. Server broadcasts messages to subscribed clients.
3. Clients send data to a topic (e.g., `{"action": "publish", "topic": "stocks:AAPL", "data": {"price": 150}}`).

**Schema Reference**:
| Field          | Type     | Description                                  | Example Value               |
|----------------|----------|----------------------------------------------|-----------------------------|
| `action`       | string   | `"subscribe"/"unsubscribe"/"publish"`       | `"subscribe"`               |
| `topic`        | string   | Topic name (e.g., `stocks:AAPL`)             | `"stocks:AAPL"`             |
| `data`         | object   | Payload (varies by use case)                | `{"price": 150}`            |
| `clientId`     | string   | Unique identifier (for unsubscribing)       | `"user_1234"`               |

**Query Example**:
```javascript
// Subscribe to a topic
ws.send(JSON.stringify({
  action: "subscribe",
  topic: "stocks:AAPL"
}));

// Publish a stock price update
ws.send(JSON.stringify({
  action: "publish",
  topic: "stocks:AAPL",
  data: { price: 150 }
}));
```

---

#### **B. Chat Room**
**Use Case**: Real-time group messaging (e.g., Slack, Discord clones).
**Flow**:
1. Clients join a room (e.g., via `WS://server/chat?room=general`).
2. Messages are broadcast to all room members.
3. Server manages room membership and message history.

**Schema Reference**:
| Field          | Type     | Description                                  | Example Value               |
|----------------|----------|----------------------------------------------|-----------------------------|
| `action`       | string   | `"join"/"leave"/"send"`                     | `"send"`                    |
| `room`         | string   | Room name                                   | `"general"`                 |
| `message`      | string   | Text content (or object for rich data)       | `"Hello, team!"`            |
| `senderId`     | string   | User identifier                             | `"user_5678"`               |
| `timestamp`    | number   | Unix epoch (for ordering)                  | `1678901234`                |

**Query Example**:
```javascript
// Send a message to the "general" room
ws.send(JSON.stringify({
  action: "send",
  room: "general",
  message: "Hi everyone!",
  senderId: "user_5678"
}));
```

---

#### **C. Heartbeat (Keep-Alive)**
**Use Case**: Detect disconnected clients and maintain connection liveness.
**Flow**:
1. Server sends periodic pings (e.g., every 30 seconds).
2. Client replies with pongs.
3. Client closes connection if no heartbeat received within `timeout` (e.g., 55s).

**Schema Reference**:
| Field          | Type     | Description                                  | Example Value               |
|----------------|----------|----------------------------------------------|-----------------------------|
| `type`         | string   | `"ping"/"pong"`                             | `"ping"`                    |
| `timestamp`    | number   | Unix epoch (for tracking delays)            | `1678901234`                |

**Query Example**:
```javascript
// Server sends (pseudo-code):
ws.send(JSON.stringify({ type: "ping", timestamp: Date.now() }));

// Client replies:
ws.onmessage = (event) => {
  if (event.data.type === "ping") {
    ws.send(JSON.stringify({ type: "pong", timestamp: event.data.timestamp }));
  }
};
```

---

#### **D. State Synchronization**
**Use Case**: Shared state (e.g., collaborative whiteboard, multiplayer games).
**Flow**:
1. Client requests the current state (e.g., `{"action": "sync"}`).
2. Server sends the full state snapshot.
3. Clients send state updates (e.g., `{"action": "update", "data": { /* changes */ }}`).
4. Server resolves conflicts and broadcasts resolved state.

**Schema Reference**:
| Field          | Type     | Description                                  | Example Value               |
|----------------|----------|----------------------------------------------|-----------------------------|
| `action`       | string   | `"sync"/"update"`                           | `"sync"`                    |
| `stateId`      | string   | Version to sync to (for delta updates)       | `"v2"`                      |
| `data`         | object   | Current state or delta changes               | `{ "canvas": { /* ... */ } }`|

**Query Example**:
```javascript
// Request full state
ws.send(JSON.stringify({ action: "sync" }));

// Send an update (e.g., draw action)
ws.send(JSON.stringify({
  action: "update",
  data: { type: "draw", coordinates: { x: 10, y: 20 } }
}));
```

---

#### **E. Authentication**
**Use Case**: Secure WebSocket connections (e.g., JWT tokens).
**Flow**:
1. Client sends credentials (e.g., `{"action": "auth", "token": "xyz123"}`).
2. Server validates the token and grants access.
3. Token is stored in the session for subsequent requests.

**Schema Reference**:
| Field          | Type     | Description                                  | Example Value               |
|----------------|----------|----------------------------------------------|-----------------------------|
| `action`       | string   | `"auth"`                                     | `"auth"`                    |
| `token`        | string   | JWT or session token                        | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"` |
| `userId`       | string   | (Optional) Pre-authenticated user ID         | `"user_1234"`               |

**Query Example**:
```javascript
// Authenticate via token
ws.send(JSON.stringify({
  action: "auth",
  token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
}));
```

---

### **3. Schema Reference (Summary Table)**
| **Pattern**            | **Key Fields**                          | **Payload Example**                          | **Use Case**                  |
|------------------------|----------------------------------------|---------------------------------------------|-------------------------------|
| Publish-Subscribe      | `action`, `topic`, `data`               | `{"action": "publish", "topic": "stocks:AAPL", "data": {...}}` | Real-time data feeds          |
| Chat Room              | `action`, `room`, `message`, `senderId` | `{"action": "send", "room": "general", "message": "Hi!"}` | Group chat                    |
| Heartbeat              | `type`, `timestamp`                    | `{"type": "ping", "timestamp": 1678901234}` | Connection liveness           |
| State Sync             | `action`, `stateId`, `data`            | `{"action": "update", "data": {...}}`       | Collaborative apps            |
| Authentication         | `action`, `token`, `userId`            | `{"action": "auth", "token": "xyz123"}`     | Secure connections            |

---

### **4. Query Examples (Code Snippets)**
#### **Client-Side (JavaScript)**
```javascript
// Connect to WebSocket
const socket = new WebSocket("wss://api.example.com/ws");

// Publish-Subscribe
socket.onopen = () => {
  socket.send(JSON.stringify({
    action: "subscribe",
    topic: "notifications"
  }));
};

// Heartbeat
let lastHeartbeat = Date.now();
socket.addEventListener("message", (event) => {
  if (event.data.type === "ping") {
    socket.send(JSON.stringify({ type: "pong", timestamp: event.data.timestamp }));
    lastHeartbeat = Date.now();
  }
});
```

#### **Server-Side (Node.js with `ws` Library)**
```javascript
const WebSocket = require("ws");
const wss = new WebSocket.Server({ port: 8080 });

wss.on("connection", (ws) => {
  // PubSub example: Broadcast to subscribed clients
  ws.on("message", (data) => {
    const msg = JSON.parse(data);
    if (msg.action === "publish") {
      wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify({
            ...msg.data,
            metadata: { timestamp: Date.now() }
          }));
        }
      });
    }
  });
});
```

---

### **5. Related Patterns**
1. **Server-Sent Events (SSE)**: Unidirectional (server → client) alternative to WebSockets (simpler but lacks duplex).
2. **Long Polling**: HTTP-based fallback for WebSocket browsers (e.g., legacy IE).
3. **GRPC/WebSockets**: Combines WebSockets with gRPC’s protocol buffers for structured RPC.
4. **Message Queues (e.g., RabbitMQ)**: For offloading WebSocket message processing (e.g., pubsub via queue workers).
5. **Rate Limiting**: Protect WebSocket endpoints from abuse (e.g., using Redis to track client spikes).
6. **Message Compression**: Reduce payload size (e.g., `zlib` for frequent small updates).

---
### **6. Implementation Best Practices**
1. **Error Handling**: Implement reconnect logic (exponential backoff) and graceful disconnects.
   ```javascript
   let reconnectAttempts = 0;
   const maxAttempts = 5;
   ws.onclose = () => {
     if (reconnectAttempts < maxAttempts) {
       setTimeout(() => {
         ws = new WebSocket("wss://api.example.com/ws");
         reconnectAttempts++;
       }, 1000 * Math.pow(2, reconnectAttempts));
     }
   };
   ```
2. **Scalability**: Use a **WebSocket gateway** (e.g., Socket.io, Pusher) for load balancing.
3. **Security**:
   - Validate all incoming data (prevent injection attacks).
   - Use **WSS (wss://)** for encryption.
   - Implement CORS for cross-origin connections.
4. **Message Prioritization**: Use `OPEN_WEBSOCKET` in Redis to route critical updates.
5. **Monitoring**: Track:
   - Connection count.
   - Message throughput.
   - Latency (ping-pong RTT).

---
### **7. Troubleshooting**
| **Issue**               | **Solution**                                  |
|--------------------------|-----------------------------------------------|
| Connection drops         | Enable heartbeat and reconnect logic.         |
| High latency             | Use WebSocket compression (`permessage-deflate`). |
| Memory leaks             | Use weak references for client management.    |
| Cross-origin errors      | Configure CORS headers (`Access-Control-Allow-Origin`). |
| Message loss             | Implement acknowledgments (`ack: true/false`). |

---
### **8. Tools & Libraries**
| **Tool/Library**         | **Purpose**                                  | **Link**                          |
|--------------------------|----------------------------------------------|-----------------------------------|
| `ws` (Node.js)           | Core WebSocket implementation.               | [GitHub](https://github.com/websockets/ws) |
| Socket.io                | Fallback to HTTP long-polling + pubsub.      | [Website](https://socket.io/)     |
| Pusher                   | Managed WebSocket service (pubsub).         | [Website](https://pusher.com/)    |
| Redis + WebSockets       | Shared state with pubsub.                   | [Redis Docs](https://redis.io/)   |
| NGINX WebSocket Module   | Load balancing for WebSockets.               | [NGINX](https://nginx.org/)       |

---
**References**:
- [RFC 6455](https://tools.ietf.org/html/rfc6455) (WebSocket Protocol).
- [HTML5 Rocks: WebSockets Guide](https://www.html5rocks.com/en/tutorials/websockets/basics/).