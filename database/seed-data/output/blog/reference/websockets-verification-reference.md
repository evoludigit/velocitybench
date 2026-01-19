# **[Pattern] Websockets Verification Reference Guide**

---

## **Overview**
The **Websockets Verification** pattern ensures real-time validation and authentication of WebSocket connections between a client (e.g., browser, IoT device, or server) and a WebSocket backend (e.g., server, gateway, or service). Unlike HTTP, WebSockets maintain persistent connections, requiring robust validation before allowing communication. This pattern prevents unauthorized access, malformed messages, and connection flooding while ensuring seamless real-time data exchange.

Key use cases include:
- Validating WebSocket handshake headers (e.g., `Sec-WebSocket-Key`, `Origin`).
- Authenticating users via tokens, JWT, or custom challenges.
- Enforcing rate-limiting to prevent abuse.
- Validating message structure (e.g., payload format, content-type).
- Handling upgrade requests from HTTP (e.g., `Connection: Upgrade` header).

This guide covers implementation details, schema validation, query examples, and related patterns for secure WebSocket communication.

---

## **Implementation Details**

### **1. Key Concepts**
| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **WebSocket Handshake** | The initial HTTP-like upgrade request from client to server to establish a WebSocket connection. |
| **Sec-WebSocket-Key**  | A client-generated key used by the server to verify the upgrade request.   |
| **Sec-WebSocket-Accept** | Server-generated response (SHA-1 hash of `Sec-WebSocket-Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"`) to confirm the handshake. |
| **Authentication**    | Validating tokens (e.g., JWT), API keys, or user credentials before granting access. |
| **Message Validation** | Ensuring payloads adhere to a schema (e.g., JSON, Protobuf) and lack malicious content. |
| **Rate Limiting**     | Restricting connection attempts per IP/user to prevent abuse.               |
| **Upgrade Headers**   | Headers like `Connection: Upgrade`, `Host`, and `Origin` that must be validated. |

---

### **2. Server-Side Workflow**
1. **Handshake Validation**:
   - Verify `Sec-WebSocket-Key` and generate `Sec-WebSocket-Accept`.
   - Check `Origin`, `Host`, and `Connection: Upgrade` headers.
   - Reject malformed or unauthorized requests.

2. **Authentication**:
   - Extract tokens (e.g., from `Sec-WebSocket-Protocol` or custom headers).
   - Validate against a database or external service (e.g., OAuth2).

3. **Connection Establishment**:
   - Accept the WebSocket connection upon successful validation.
   - Assign a unique connection ID (for tracking/rate limiting).

4. **Message Handling**:
   - Validate payloads against a schema (see **Schema Reference**).
   - Enforce message size limits (e.g., 1MB).

5. **Connection Termination**:
   - Close connections on errors (e.g., invalid tokens, rate limits).
   - Allow graceful disconnections (e.g., `1000` close code for normal closure).

---

### **3. Client-Side Workflow**
1. Send WebSocket upgrade request with:
   ```http
   GET /ws HTTP/1.1
   Host: example.com
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
   Sec-WebSocket-Version: 13
   Origin: https://client.example.com
   ```
2. Include authentication (e.g., in `Sec-WebSocket-Protocol`):
   ```http
   Sec-WebSocket-Protocol: token=abc123
   ```
3. Handle server responses:
   - Reject if `Sec-WebSocket-Accept` is missing or invalid.
   - Reconnect on failure (with exponential backoff).

---

## **Schema Reference**
Validate WebSocket messages using a structured schema (e.g., JSON Schema, Protobuf). Below are common fields and their validation rules.

| Field Name          | Type     | Required | Description                                                                 | Example Value                     |
|---------------------|----------|----------|-----------------------------------------------------------------------------|-----------------------------------|
| **action**          | string   | Yes      | Specifies the message type (e.g., `auth`, `data`, `ping`).                  | `"auth"`                          |
| **user_id**         | string   | Conditional | Unique identifier for the user (used in auth/data messages).                 | `"user123"`                       |
| **token**           | string   | Conditional | JWT or API key for authentication.                                          | `"eyJhbGciOiJIUzI1Ni..."`        |
| **payload**         | object   | Conditional | Encapsulates message-specific data.                                         | `{"value": 42}`                  |
| **timestamp**       | integer  | No       | Unix timestamp for message ordering.                                         | `1672531200`                     |
| **nonce**           | string   | No       | Anti-replay token (e.g., for auth pings).                                  | `"nonce456"`                      |
| **signature**       | string   | No       | HMAC-SHA256 of payload + secret (for integrity).                           | `"abc123=="`                      |

### **Example Valid Message (JSON)**
```json
{
  "action": "data",
  "user_id": "user123",
  "payload": {"temperature": 25.5, "units": "C"},
  "timestamp": 1672531200
}
```

### **Common Validation Errors**
| Error Code | Description                          | Example Response                     |
|------------|--------------------------------------|---------------------------------------|
| `401`      | Unauthorized (invalid token).         | `{"error": "Unauthorized", "code": 401}` |
| `400`      | Malformed message (missing fields).   | `{"error": "Invalid payload", "code": 400}` |
| `429`      | Rate limit exceeded.                  | `{"error": "Too many requests", "code": 429}` |

---

## **Query Examples**

### **1. Server-Side Validation (Pseudocode)**
```javascript
// Validate WebSocket handshake (Node.js with `ws` library)
const WebSocket = require('ws');
const crypto = require('crypto');

const server = new WebSocket.Server({ port: 8080 });

server.on('connection', (ws, req) => {
  // 1. Validate handshake headers
  if (!req.headers['sec-websocket-key']) {
    ws.close(1008, 'Invalid Key'); // Policy violation
    return;
  }

  const accept = crypto
    .createHash('sha1')
    .update(req.headers['sec-websocket-key'] + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
    .digest('base64');

  if (req.headers['sec-websocket-accept'] !== accept) {
    ws.close(1002, 'Protocol Error');
    return;
  }

  // 2. Authenticate (simplified)
  const token = req.headers['sec-websocket-protocol']?.split('=')[1];
  if (!validateToken(token)) {
    ws.close(1008, 'Unauthorized');
    return;
  }

  // 3. Allow connection
  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data.toString());
      // Validate schema (e.g., using `ajv` validator)
      if (!validateMessageSchema(msg)) {
        ws.send(JSON.stringify({ error: 'Invalid message' }));
        return;
      }
      // Process message...
    } catch (e) {
      ws.close(1007, 'Bad payload');
    }
  });
});
```

---

### **2. Client-Side Connection (JavaScript)**
```javascript
// Connect with authentication
const socket = new WebSocket('wss://example.com/ws', [
  `token=${generateAuthToken()}`
]);

socket.onopen = () => {
  console.log('Connected');
  socket.send(JSON.stringify({
    action: 'auth',
    token: generateAuthToken(),
    nonce: generateNonce()
  }));
};

socket.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    if (data.error) {
      throw new Error(data.error);
    }
    // Handle valid message...
  } catch (e) {
    console.error('Message error:', e);
    socket.close(1007);
  }
};

socket.onclose = () => {
  console.log('Disconnected');
};
```

---

### **3. Rate-Limiting (Redis-Based)**
```python
# Pseudocode for rate-limiting connections
import redis
import time

r = redis.Redis(host='localhost', port=6379)

def check_rate_limit(ip):
  key = f"rate_limit:{ip}"
  current = r.get(key) or 0
  if int(current) > 100:  # Max 100 connections/min
    return False
  r.incr(key)
  r.expire(key, 60)  # Reset in 60s
  return True

# Usage in WebSocket server:
if not check_rate_limit(req.client.address):
  ws.close(429, 'Rate limit exceeded');
```

---

## **Related Patterns**
| Pattern                        | Description                                                                 | When to Use                                                                 |
|---------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **JWT Authentication**          | Validate WebSocket tokens using JSON Web Tokens (JWT).                     | When using stateless auth (e.g., mobile clients).                          |
| **WebSocket Compression**       | Enable `permessage-deflate` for bandwidth optimization.                    | For high-latency networks or large payloads.                               |
| **Connection Health Checks**    | Ping/pong messages to detect dead connections.                              | In long-lived connections (e.g., IoT devices).                             |
| **Message Prioritization**      | Assign priorities to messages (e.g., `high`, `low`).                        | For mixed traffic (e.g., chat + notifications).                             |
| **WebSocket Proxy**             | Route WebSocket traffic through a proxy (e.g., for load balancing).        | In distributed systems or multi-region deployments.                        |
| **Binary WebSocket Protocols**  | Use Protobuf/MessagePack for efficient binary payloads.                    | For high-throughput systems (e.g., real-time analytics).                    |
| **WebSocket Over HTTP/2**       | Leverage HTTP/2 multiplexing for WebSocket connections.                     | Modern browsers with HTTP/2 support.                                      |

---

## **Best Practices**
1. **Use WSS (wss://) for Encryption**:
   - Always encrypt WebSocket connections with TLS to prevent MITM attacks.
2. **Validate All Headers**:
   - Check `Origin`, `Host`, and custom headers (e.g., `Authorization`).
3. **Implement Graceful Degradation**:
   - Fall back to HTTP if WebSocket fails (e.g., for legacy clients).
4. **Monitor Connection Metrics**:
   - Track dropped connections, latency, and error rates (e.g., with Prometheus).
5. **Clean Up Resources**:
   - Close unused connections to avoid memory leaks.
6. **Test Edge Cases**:
   - Validate against malformed messages, large payloads, and rapid reconnects.

---
## **Troubleshooting**
| Issue                          | Solution                                                                     |
|---------------------------------|-----------------------------------------------------------------------------|
| **Handshake Fails**             | Verify `Sec-WebSocket-Key`/`Accept`, CORS headers, and server logs.          |
| **Authentication Rejected**    | Check token format, expiration, and server-side validation logic.           |
| **High Latency**                | Enable compression (`permessage-deflate`), optimize server location.         |
| **Connection Drops**            | Implement ping/pong, check network stability, and monitor server resources.|

---
## **Tools & Libraries**
| Tool/Library          | Purpose                                                                   |
|-----------------------|--------------------------------------------------------------------------|
| [`ws` (Node.js)](https://github.com/websockets/ws) | WebSocket server/client for Node.js.                                     |
| [`websockets-lite`](https://github.com/websockets/websockets-lite) | Lightweight WebSocket library (Python, Ruby, etc.).                      |
| [`ajv`](https://ajv.js.org/) | JSON Schema validator for message validation.                             |
| [`redis`](https://redis.io/) | Rate-limiting with Redis.                                                  |
| [`ngrok`](https://ngrok.com/) | Expose local WebSocket servers for testing.                               |

---
**End of Reference Guide** (Word count: ~950)