---
# **[Pattern] Websockets Testing – Reference Guide**

---

## **Overview**
Websockets Testing is a pattern for validating bidirectional, real-time communication protocols between clients and servers via WebSocket connections. Unlike traditional HTTP testing, this pattern ensures correctness of message exchange, connection lifecycle (handshake, upgrades, disconnections), and error handling (e.g., reconnection, timeouts). Use cases include testing chat applications, live dashboards, collaborative editing tools, and IoT platforms. This guide covers key concepts, schema references, query examples, and related patterns for a comprehensive testing approach.

---

## **Key Concepts**
The Websockets Testing pattern revolves around the following core components:

| **Concept**               | **Description**                                                                 | **Example**                          |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **WebSocket Connection**  | Establishes a persistent TCP connection (from HTTP upgrade) to enable full-duplex communication. | `wss://api.example.com/ws` |
| **Handshake**             | Initial HTTP upgrade request (`GET /ws?token=...`, `Upgrade: websocket`) and server response (e.g., `101 Switching Protocols`). | HTTP headers + WebSocket frame (opcode `0x81`). |
| **Frames**                | Low-level protocol data units (masking, compression, binary/text payloads).     | `Opcode 0x1 (text) + payload: "hello"` |
| **Events**                | High-level application-level triggers (e.g., `onopen`, `onmessage`, `onerror`). | `connection.onmessage = (e) => console.log(e.data)` |
| **Reconnection**          | Client-server resilience via auto-reconnect logic (e.g., exponential backoff).     | Retry after 3 seconds on `ERR_CONNECTION_REFUSED`. |
| **Authentication**        | Securing connections via tokens, cookies, or custom headers in handshake.        | `Sec-WebSocket-Protocol: auth=Bearer:XYZ`. |

---

## **Schema Reference**
### **1. WebSocket Connection Schema**
| **Field**                 | **Type**       | **Description**                                                                 | **Example Value**                     |
|---------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| `url`                     | `string`       | Target WebSocket URI (supports `ws://`, `wss://`).                              | `wss://api.example.com/ws/v1`         |
| `protocol`                | `string[]`     | Subprotocols negotiated in handshake (e.g., `chat`, `auth`).                    | `["chat-v1", "v2"]`                   |
| `headers`                 | `object`       | Custom headers for handshake (e.g., `Sec-WebSocket-Extensions: permessage-deflate`). | `{ "Sec-WebSocket-Key": "dGhlIHNhbXBsZSB..." }` |
| `authToken`               | `string`       | Bearer token for handshake.                                                     | `Bearer:abc123xyz`                    |
| `pingInterval`            | `number`       | Ping interval (ms) to maintain connection (default: `25_000`).                 | `30_000`                              |
| `reconnectAttempts`       | `number`       | Max reconnection attempts (default: `3`).                                      | `5`                                   |
| `reconnectDelay`          | `number`       | Initial reconnection delay (ms) (default: `1_000`).                            | `5_000`                               |

---

### **2. WebSocket Frame Schema**
| **Field**                 | **Type**       | **Description**                                                                 | **Example Value**                     |
|---------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| `opcode`                  | `number`       | Frame type (`0x0`=continuation, `0x1`=text, `0x2`=binary, `0x8`=close).      | `0x8` (close frame)                   |
| `masked`                  | `boolean`      | Whether client-side data is masked (client: `true`, server: `false`).          | `true`                                |
| `payload`                 | `string\|Uint8Array` | Message content (UTF-8 or binary).                                       | `"Hello, websocket!"` or `new Uint8Array([0x48, 0x65])` |
| `compressed`              | `boolean`      | Whether payload is compressed (e.g., `permessage-deflate`).                 | `false`                               |
| `mask`                     | `Uint8Array`   | Optional mask for client-side frames.                                         | `Uint8Array.from([0x12, 0x34, 0x56])` |

---

### **3. Reconnection Strategy Schema**
| **Field**                 | **Type**       | **Description**                                                                 | **Example Value**                     |
|---------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| `strategy`                | `string`       | Retry strategy (`exponential`, `linear`, `fixed`).                              | `exponential`                         |
| `baseDelay`               | `number`       | Base delay (ms) for exponential backoff.                                        | `1_000`                               |
| `maxDelay`                | `number`       | Maximum delay (ms) before giving up.                                            | `30_000`                              |
| `jitter`                  | `number`       | Random delay jitter (ms) to avoid thundering herd.                              | `500`                                 |
| `onRetry`                 | `function`     | Callback on retry (e.g., log, metrics).                                         | `(attempt: number) => console.log(attempt)` |

---

## **Query Examples**
### **1. Establishing a WebSocket Connection**
```javascript
import { WebSocket } from 'ws';

const socket = new WebSocket('wss://api.example.com/ws', {
  protocol: ['chat-v1'],
  headers: {
    'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSB...',
    'Sec-WebSocket-Extensions': 'permessage-deflate'
  }
});

socket.onopen = () => {
  console.log('Connected');
  socket.send(JSON.stringify({ type: 'auth', token: 'abc123' }));
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.payload);
};
```

### **2. Sending Binary Data**
```javascript
// Encode as binary (e.g., image data)
const imageData = new Uint8Array([0x47, 0x49, 0x46, 0x38]); // "GIF8" header
socket.send(imageData, {
  opcode: 0x2, // Binary frame
  compressed: false
});
```

### **3. Handling Errors and Reconnection**
```javascript
let reconnectAttempt = 0;
const maxAttempts = 5;

socket.onerror = (error) => {
  console.error('WebSocket error:', error);
  if (reconnectAttempt < maxAttempts) {
    reconnectAttempt++;
    setTimeout(() => {
      socket = new WebSocket('wss://api.example.com/ws');
    }, 1000 * reconnectAttempt);
  }
};

socket.onclose = () => {
  console.log('Disconnected');
};
```

### **4. Testing Pings/Pongs**
```javascript
// Server-side: Send ping every 30s
socket.ping = () => {
  socket.send('', { opcode: 0x9 }); // Ping frame
};

// Client-side: Handle pong
socket.on('pong', () => {
  console.log('Pong received');
});
```

### **5. Close Connection Gracefully**
```javascript
// Close with reason code (1000=normal)
socket.close(1000, 'Client closing connection');
```

---

## **Validation Rules**
| **Rule**                          | **Description**                                                                 | **Example Check**                          |
|-----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------|
| **Handshake Header Validation**   | Verify `Upgrade: websocket` and `Connection: Upgrade` in HTTP response.         | `response.headers['upgrade'] === 'websocket'` |
| **Frame Masking**                 | Ensure client frames are masked (`true`), server frames are not.               | `frame.masked === (socket.binaryType === 'arraybuffer')` |
| **Reconnection Throttle**         | Exponential backoff must not exceed `maxDelay`.                               | `delay <= Math.min(exponentialBackoff, maxDelay)` |
| **Message Schema**                | Validate payload against expected schema (e.g., JSON, Protobuf).               | `validatePayload(data, { type: 'string' })`  |
| **Timeout Handling**              | No ping/pong response after `pingInterval` + 2s should trigger reconnect.     | `lastPongTime < Date.now() - (pingInterval + 2000)` |

---

## **Testing Tools & Libraries**
| **Tool/Library**               | **Purpose**                                                                     | **Link**                                  |
|---------------------------------|---------------------------------------------------------------------------------|-------------------------------------------|
| `ws` (Node.js)                  | Native WebSocket implementation for server/client testing.                     | [GitHub](https://github.com/websockets/ws) |
| `Socket.IO`                     | Higher-level abstraction for WebSocket + fallbacks (HTTP long-polling).        | [Socket.IO](https://socket.io/)            |
| Postman (WebSocket Proxy)       | GUI for testing WebSocket APIs with request/response inspection.               | [Postman WebSocket](https://learning.postman.com/docs/sending-requests/supported-api-frameworks/websockets/) |
| Karma + `karma-websocket`        | Browser-based WebSocket testing for unit/integration tests.                      | [Plugin](https://github.com/karma-runner/karma-websocket) |
| Cypress                         | End-to-end WebSocket testing with assertions and mocks.                         | [Cypress Docs](https://docs.cypress.io/guides/guides/network-requests.html#WebSockets) |
| WebSocket++ (C++)               | High-performance WebSocket server/client for benchmarking.                      | [WebSocket++](https://github.com/websocketspp/websocketspp) |

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                          |
|----------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Event-Driven Architecture]**  | Design systems around asynchronous, decoupled events (e.g., message queues).   | Scalable real-time systems (e.g., stock tickers). |
| **[HTTP/2 Server Push]**         | Preemptively send resources to clients over HTTP/2.                             | Reduce latency for static assets.        |
| **[Long-Polling]**               | Fallback for WebSocket clients when connection is unavailable.                  | Legacy browser support.                  |
| **[SSE (Server-Sent Events)]**   | Unidirectional server-to-client streaming (simpler than WebSockets).           | Log aggregation, notifications.          |
| **[GRPC Web]**                   | Binary protcol over HTTP/2 for high-performance WebSocket-like APIs.            | Microservices communication.              |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Cause**                                      | **Mitigation**                                      |
|---------------------------------------|-------------------------------------------------|-----------------------------------------------------|
| **Connection Drops**                  | Network instability, server timeouts.           | Implement exponential backoff + reconnection logic. |
| **Memory Leaks**                      | Unclosed sockets or retained event listeners.   | Use `socket.removeAllListeners()` on close.         |
| **Malformed Frames**                  | Missing masking or invalid payloads.            | Validate frames with `isValidWebSocketFrame`.       |
| **CORS Restrictions**                 | WebSocket handshake blocked by Same-Origin Policy.| Use a proxy server (e.g., CORS Anywhere).          |
| **Compression Overhead**              | `permessage-deflate` slows down small messages. | Disable compression for low-latency needs.        |

---

## **Example Test Suite (Jest + `@jest/globals`)**
```javascript
const WebSocket = require('ws');
const { validateFrame, testConnection } = require('./websocket-utils');

describe('WebSocket Integration', () => {
  let socket;
  const testURL = 'wss://api.example.com/ws';

  beforeEach(() => {
    socket = new WebSocket(testURL, {
      pingInterval: 30_000,
      reconnectAttempts: 3
    });
  });

  afterEach(() => {
    socket.close();
  });

  test('should establish connection and send/receive message', async () => {
    await testConnection(socket, {
      url: testURL,
      expectedHandshakeHeaders: { 'sec-websocket-protocol': 'chat-v1' }
    });

    const testMessage = { type: 'ping', timestamp: Date.now() };
    await new Promise((resolve) => {
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        expect(data).toEqual(testMessage);
        resolve();
      };
      socket.send(JSON.stringify(testMessage));
    });
  });

  test('should validate frame masking', () => {
    const frame = { opcode: 0x1, masked: true, payload: 'test' };
    expect(validateFrame(frame)).toBe(true);
  });
});
```

---
**End of Reference Guide** (≈1,000 words)