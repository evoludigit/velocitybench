# **[Pattern] Reference Guide: WebSocket Anti-Patterns**

---

## **Overview**
WebSockets enable real-time bidirectional communication between clients and servers, but implementing them poorly can lead to performance bottlenecks, scalability issues, or client disconnections. This guide identifies and explains **common WebSocket anti-patterns**, their root causes, and best practices to avoid them. By recognizing these pitfalls, you can design efficient, scalable, and reliable WebSocket applications.

---

## **Key Anti-Patterns & Implementation Pitfalls**

### **1. Unbounded Message Accumulation**
**Definition**
Allowing the server to accumulate too many unsent messages in the WebSocket buffer, causing resource exhaustion or client disconnections.

**Symptoms**
- High memory usage on the server.
- Clients disconnect due to timeouts (e.g., `1008: policy violation`).
- Sluggish or silent disconnections.

**Root Cause**
No buffer size limit or excessive backpressure handling.

**Solution**
- **Set buffer limits** (e.g., 100–500 messages per connection).
- **Implement backpressure** (e.g., pause sending if the buffer fills).
- **Use graceful degradation** (drop old messages if the buffer overflows).

**Example Backpressure Logic (Pseudocode)**
```python
if websocket.buffer_size >= MAX_BUFFER:
    websocket.pause()  # Stop sending new messages
else:
    websocket.resume()
```

---

### **2. Polling Instead of Streaming**
**Definition**
Continuously polling for updates (e.g., via HTTP or periodic WebSocket pings) instead of using real-time streaming.

**Symptoms**
- High latency due to polling intervals.
- Unnecessary network traffic.
- Eventual consistency issues.

**Root Cause**
Over-reliance on periodic checks or lack of event-driven architecture.

**Solution**
- **Use event-driven pushes** (send updates only when data changes).
- **Debounce rapid messages** (e.g., throttle heartbeats to 1 ping/sec).
- **Replace polling with subscriptions** (e.g., `subscribe("user:123")`).

**Example: Efficient Subscription**
```json
// Client subscribes to updates for user ID 123
{
  "event": "subscribe",
  "topic": "user:123",
  "payload": {}
}
```

---

### **3. Ignoring Connection Drops**
**Definition**
Failing to handle disconnections gracefully, leading to lost state or silent failures.

**Symptoms**
- Clients reconnect without restoring state.
- Server-side loops assume connections are alive.
- Data loss during reconnects.

**Root Cause**
No reconnection strategy or session persistence.

**Solution**
- **Implement reconnection logic** (exponential backoff, max retries).
- **Use Connection IDs or Tokens** to restore state on reconnect.
- **Server-side tracking** (e.g., Redis for active sessions).

**Example Reconnection Policy**
```javascript
let retries = 0;
const maxRetries = 5;
const baseDelay = 1000; // ms

async function connectWithRetry() {
  while (retries < maxRetries) {
    try {
      await websocket.connect();
      break;
    } catch (e) {
      retries++;
      await new Promise(resolve => setTimeout(resolve, baseDelay * retries));
    }
  }
}
```

---

### **4. Broadcast Storms**
**Definition**
Sending too many messages to all connected clients simultaneously, overwhelming the network or clients.

**Symptoms**
- High CPU/memory usage on the server.
- Client-side lag or crashes.
- Network congestion.

**Root Cause**
Broadcasting events without filtering or throttling.

**Solution**
- **Filter recipients** (e.g., broadcast only to subscribed users).
- **Rate-limit broadcasts** (e.g., cap at 100 messages/sec).
- **Use partial updates** (e.g., diff-only changes instead of full payloads).

**Example Filtered Broadcast**
```python
# Instead of sending to all clients:
for client in websocket.clients:
    client.send(update_data)

# Send only to subscribed users:
subscribed_users = {"user:123", "user:456"}
for client in websocket.clients:
    if client.user_id in subscribed_users:
        client.send(update_data)
```

---

### **5. No Heartbeat or Keepalive**
**Definition**
Lacking periodic pings to maintain the WebSocket connection alive, leading to false disconnections.

**Symptoms**
- Clients disconnect without warning (`1006: abnormal closure`).
- Server assumes clients are offline when they’re still active.

**Root Cause**
No heartbeat mechanism to detect idle connections.

**Solution**
- **Implement server-side pings** (every 30–60 seconds).
- **Client-side pong responses** to confirm connectivity.
- **Close idle connections** after N seconds of inactivity.

**Example Heartbeat Logic**
```javascript
// Server-side ping every 30 seconds
setInterval(() => {
  for (const client of websocket.clients) {
    if (client.lastActivity < Date.now() - 30000) {
      client.close(1001, "Inactive");
    } else {
      client.ping(); // Trigger pong
    }
  }
}, 30000);
```

---

### **6. Overcomplicating Message Formats**
**Definition**
Using overly complex or non-standard message formats that complicate parsing and increase overhead.

**Symptoms**
- High CPU usage due to serialization/deserialization.
- Poor interoperability between clients/server.
- Hard-to-debug errors.

**Root Cause**
Custom binary protocols or mismatched parsers.

**Solution**
- **Standardize on JSON** (human-readable, widely supported).
- **Use protobuf or MessagePack** for binary efficiency.
- **Validate messages strictly** (e.g., schema enforcement).

**Example JSON Payload**
```json
{
  "type": "update",
  "id": "user:123",
  "data": {
    "name": "Alice",
    "last_seen": "2023-10-01T12:00:00Z"
  }
}
```

---

### **7. No Authentication/Authorization**
**Definition**
Failing to secure WebSocket connections, exposing APIs to unauthorized clients.

**Symptoms**
- Spoofed connections orman-in-the-middle attacks.
- Data leaks or API misuse.
- Hard-to-track abuse.

**Root Cause**
Lack of token validation or session management.

**Solution**
- **Require tokens/JWT** in the initial handshake.
- **Use WebSocket subprotocols** (e.g., `wss://` with TLS).
- **Rotate tokens periodically**.

**Example Secure Handshake**
```javascript
// Client sends JWT in the upgrade handshake header
const jwt = "eyJhbGciOiJIUzI1Ni...";
const ws = new WebSocket(`wss://api.example.com/ws?token=${jwt}`);
```

---

### **8. Ignoring Scalability Limits**
**Definition**
Designing for a single server without considering horizontal scaling.

**Symptoms**
- Server crashes under load.
- Uneven load distribution.
- State management failures.

**Root Cause**
No partitioning (e.g., by user ID or region).

**Solution**
- **Use message queues** (e.g., RabbitMQ) for decoupled processing.
- **Partition WebSocket connections** (e.g., by shard).
- **Load balance connections** (e.g., Nginx with WebSocket proxies).

**Example Sharded Architecture**
```
Client → Load Balancer → [WebSocket Server 1 (users A-C)]
                                   [WebSocket Server 2 (users D-F)]
```

---

## **Schema Reference**
| **Anti-Pattern**               | **Root Cause**               | **Mitigation Strategy**                          | **Example Fix**                          |
|---------------------------------|-------------------------------|--------------------------------------------------|------------------------------------------|
| Unbounded Buffer               | No buffer limits              | Set buffer size limits + backpressure           | `MAX_BUFFER = 500`                       |
| Polling Instead of Streaming    | Lack of event-driven design   | Use subscriptions + debounce                    | `subscribe("user:123")`                 |
| Ignoring Connection Drops      | No reconnection logic         | Exponential backoff + session tokens            | `connectWithRetry()`                    |
| Broadcast Storms               | Unfiltered broadcasts         | Rate-limiting + filtering                       | Filter by `subscribed_users`             |
| No Heartbeat                   | Idle connections closed       | Server pings + client pongs                     | `setInterval(websocket.ping, 30000)`     |
| Overcomplicating Formats        | Custom binary protocols       | Standardize on JSON/protobuf                    | `{"type": "update", "data": {...}}`      |
| No Authentication              | Unsecured handshakes          | JWT + TLS                                      | `wss://api.example.com/ws?token=...`     |
| Ignoring Scalability            | Single-server design          | Sharding + load balancing                      | `[WebSocket Server 1...N]`              |

---

## **Query Examples**
### **1. Checking Buffer Size (Server-Side)**
```python
# Pseudo-code to inspect WebSocket buffer
def check_buffer(client):
    if client.buffer_size > MAX_BUFFER:
        print(f"Warning: Client {client_id} buffer overflow!")
```

### **2. Debounced Heartbeat (Client-Side)**
```javascript
// Send a ping every 30 seconds, but only if idle
let lastActivity = Date.now();
setInterval(() => {
  if (Date.now() - lastActivity > 30000) {
    websocket.send(JSON.stringify({ type: "heartbeat" }));
  }
}, 30000);
```

### **3. Filtered Broadcast (Server-Side)**
```python
# Broadcast only to subscribed users
subscribers = {"user:123", "user:456"}
message = {"event": "update", "data": {...}}

for client in websocket.clients:
    if client.user_id in subscribers:
        client.send(message)
```

### **4. Token Validation (Handshake)**
```javascript
// Verify JWT in WebSocket upgrade headers
function validateToken(token) {
  try {
    const decoded = jwt.decode(token);
    return decoded.user_id; // Return user ID if valid
  } catch (e) {
    return null; // Invalid token
  }
}
```

---

## **Related Patterns**
1. **[Connection Management]** – Strategies for handling WebSocket lifecycles (e.g., reconnects, timeouts).
2. **[Message Throttling]** – Preventing flood attacks via rate limiting.
3. **[Event-Driven Architecture]** – Designing systems around async event flows.
4. **[Scalable Pub/Sub]** – Using message brokers (e.g., Kafka, RabbitMQ) for horizontal scaling.
5. **[Secure WebSockets]** – Implementing TLS, JWT, and-auth for WebSocket security.

---
## **Further Reading**
- [IETF WebSocket Protocol RFC](https://datatracker.ietf.org/doc/html/rfc6455)
- [Rate Limiting for WebSockets](https://betterstack.com/community/guides/engineering/rate-limiting-for-websockets/)
- [Heartbeat Mechanisms in Real-Time Systems](https://www.nginx.com/blog/web-sockets-heartbeats/)