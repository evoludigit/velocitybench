---
# **[Websockets Standard] Reference Guide**

## **Overview**
The **Websockets Standards** pattern enables **full-duplex, real-time bidirectional communication** between a client (browser or application) and a server over a single, persistent TCP connection. Unlike traditional HTTP polling or Server-Sent Events (SSE), Websockets provide **low-latency, low-overhead** communication ideal for live updates, chat applications, collaborative tools, and IoT devices. This reference outlines the **IETF standards (RFC 6455), key protocols, security considerations, implementation best practices, and common use cases**.

---

## **Implementation Details**

### **1. Core Standards & Protocols**
| **Standard/Protocol**       | **Version** | **Purpose**                                                                                     | **Key Features**                                                                                     |
|-----------------------------|------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **RFC 6455 (The WebSocket Protocol)** | Latest     | Defines the application protocol for persistent, full-duplex communication over TCP.         | - Framed data exchange <br> - Masking for client-side data integrity <br> - Connection handshake |
| **RFC 6520 (Hybi-17)**      | 2014       | Upgrade mechanism from HTTP/1.1 to WebSockets.                                                 | - `Sec-WebSocket-Key` challenge/response <br> - Subprotocol negotiation via `Sec-WebSocket-Protocol` |
| **RFC 7692 (HTTP Upgrade Header)** | 2015      | Standardizes the `Upgrade: websocket` HTTP header for protocol switching.                     | - Enables seamless transition from HTTP to WebSockets                                       |
| **RFC 8446 (TLS 1.3)**      | Latest     | Secure WebSockets (wss://) via TLS 1.3, replacing older SSL/TLS handshakes.                   | - Reduced handshake latency <br> - Forward secrecy support                                      |
| **RFC 8114 (Permissions & Security)** | 2017   | Addresses security risks (e.g., CORS, origin validation).                                      | - Strict origin checks <br> - Deprecation of `Sec-WebSocket-Origin` in favor of CORS             |

---

### **2. Connection Lifecycle**
#### **Handshake Process**
1. **Client Initiation**
   - Client sends an **HTTP Upgrade** request with WebSocket-specific headers:
     ```http
     GET /chat HTTP/1.1
     Host: example.com
     Connection: Upgrade
     Upgrade: websocket
     Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
     Sec-WebSocket-Version: 13
     ```
   - Optional headers:
     - `Sec-WebSocket-Protocol`: Subprotocols (e.g., `chat`, `compression`).
     - `Sec-WebSocket-Extensions`: Negotiates extensions like [permessage-deflate](https://tools.ietf.org/html/rfc7692#section-4).

2. **Server Response**
   - Server validates headers and responds with:
     ```http
     HTTP/1.1 101 Switching Protocols
     Upgrade: websocket
     Connection: Upgrade
     Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
     Sec-WebSocket-Protocol: chat
     ```

3. **Data Exchange**
   - After handshake, raw WebSocket frames are exchanged (see **[Frame Structure](#frame-structure)**).

#### **Frame Structure**
| **Field**            | **Size (Bytes)** | **Description**                                                                 |
|----------------------|------------------|---------------------------------------------------------------------------------|
| **FIN (1 bit)**      | 1                | Ends frame (0 = fragment, 1 = complete).                                       |
| **RSV1/RSV2/RSV3 (3 bits)** | 0.5            | Reserved for extensions (e.g., compression).                                  |
| **OpCode (4 bits)**  | 0.5              | Defines frame type (e.g., `0x1` = text, `0x8` = close).                      |
| **Mask (1 bit)**     | 0.125            | Client-masked data (server-masked frames are invalid).                         |
| **Payload Length**   | Variable         | Size of payload (7 or 16/64-bit integer).                                       |
| **Payload Data**     | Variable         | Encoded message (UTF-8 for text, binary data).                                 |
| **Extension Data**   | Optional         | For negotiated extensions (e.g., compression headers).                         |

---

### **3. Message Types & OpCodes**
| **OpCode (Hex)** | **Name**       | **Description**                                                                 |
|------------------|----------------|---------------------------------------------------------------------------------|
| `0x0`            | **Continuation** | Fragment of a multi-frame message.                                               |
| `0x1`            | **Text**        | UTF-8 encoded text (most common for JSON).                                      |
| `0x2`            | **Binary**      | Raw binary data (e.g., image streams).                                          |
| `0x8`            | **Close**       | Graceful connection termination (includes status code).                          |
| `0x9`            | **Ping**        | Ping-pong mechanism for connection health checks.                                |
| `0xA`            | **Pong**        | Response to a ping.                                                              |
| `0xC`            | **Close (Undecoded)** | Legacy close frame (avoid in modern implementations).                     |

**Example: Sending a JSON Message**
```javascript
// Client-side send (UTF-8 text frame)
const message = { event: "user_typing", text: "Hello" };
const encoder = new TextEncoder();
const data = encoder.encode(JSON.stringify(message));

const frame = new Uint8Array(2 + data.length);
frame[0] = 0x80 | 0x1; // FIN + Text OpCode
frame[1] = data.length;
frame.set(data, 2);

socket.send(frame.buffer); // Low-level WebSocket API
```

---

### **4. Security & Best Practices**
| **Guideline**               | **Detail**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| **Use `wss://` (TLS)**      | Always encrypt WebSocket connections to prevent MITM attacks.                                  |
| **Validate Origins**        | Enforce `Sec-WebSocket-Origin` or CORS policies.                                             |
| **Subprotocol Negotiation** | Use `Sec-WebSocket-Protocol` to support APIs like:
   - `chat`                            |
   - `compression` (permessage-deflate) |
   - `binary`                          |
| **Frame Masking**           | Clients **must** mask payloads; servers **must not**.                                       |
| **Heartbeat Ping/Pong**     | Implement to detect dead connections (e.g., ping every 30s, timeout after 1m).              |
| **Connection Limits**       | Server-side: Track and limit concurrent connections to prevent abuse.                        |
| **Error Handling**          | Handle `1008` (Policy Violation), `1009` (Invalid Frame), and `1013` (Going Away).         |

**Example: Server-Side Validation (Node.js)**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ server, verifyClient });

function verifyClient(info, callback) {
  const origin = info.req.headers.origin || info.req.headers['sec-websocket-origin'];
  callback(origin === 'https://trusted-domain.com', info.connection.remoteAddress);
}
```

---

### **5. Scalability Considerations**
| **Challenge**               | **Solution**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| **High Latency**            | Use **edge caching** (e.g., Cloudflare Workers) or **CDN-based WebSocket termination**.        |
| **Connection Flooding**     | Implement **rate limiting** (e.g., Redis + Lua scripts).                                      |
| **Memory Leaks**            | Close idle connections after inactivity (e.g., 5 minutes).                                    |
| **Load Balancing**          | Use **sticky sessions** (client IP affinity) or **session sharing** (Redis).                   |
| **Protocol Extensions**     | Test with [compression](https://tools.ietf.org/html/rfc7692) or [binary data](https://tools.ietf.org/html/rfc7692#section-5). |

---

## **Schema Reference**
### **WebSocket Frame Schema (JSON-LD)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WebSocket Frame",
  "description": "RFC 6455 compliant frame structure.",
  "type": "object",
  "required": ["opcode", "payloadLength", "payload"],
  "properties": {
    "header": {
      "type": "object",
      "properties": {
        "fin": { "type": "boolean", "description": "Final frame flag." },
        "rsv1": { "type": "string", "enum": ["0", "1"], "description": "Extension bit." },
        "rsv2": { "type": "string", "enum": ["0", "1"] },
        "rsv3": { "type": "string", "enum": ["0", "1"] },
        "opcode": {
          "type": "string",
          "enum": ["CONTINUATION", "TEXT", "BINARY", "CLOSE", "PING", "PONG"],
          "description": "OpCode for frame type."
        },
        "mask": { "type": "boolean", "description": "Client-masked data flag." }
      }
    },
    "payloadLength": {
      "type": "integer",
      "minimum": 0,
      "description": "Size of payload in bytes (varint encoded)."
    },
    "payload": {
      "oneOf": [
        { "type": "string", "contentEncoding": "utf-8" },  // Text
        { "type": "string", "format": "binary" }           // Binary
      ],
      "description": "Encoded message data."
    },
    "extensions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "data": { "type": "string", "format": "byte" }
        }
      }
    }
  }
}
```

---

## **Query Examples**

### **1. Client-Side Connection (JavaScript)**
```javascript
// Establish connection
const socket = new WebSocket('wss://example.com/chat');

// Send message
socket.send(JSON.stringify({ type: "message", text: "Hello" }));

// Handle events
socket.onmessage = (event) => {
  console.log('Received:', event.data); // Parse JSON if needed
};

socket.onclose = () => {
  console.log('Connection closed');
};
```

### **2. Server-Side (Node.js with `ws` Library)**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    const message = JSON.parse(data.toString());
    if (message.type === "message") {
      broadcast(JSON.stringify({ type: "replica", text: message.text }));
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

function broadcast(message) {
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}
```

### **3. Server-Side (Python with `websockets` Library)**
```python
import asyncio
import json
from websockets.sync.client import connect
from websockets.server import serve

async def handle_client(websocket, path):
    while True:
        data = await websocket.recv()
        message = json.loads(data)
        if message["type"] == "message":
            await broadcast(json.dumps({"type": "replica", "text": message["text"]}))

async def broadcast(message):
    async with serve(handle_client, "0.0.0.0", 8765):
        for client in clients:
            await client.send(message)

clients = set()
```

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Server-Sent Events (SSE)](./sse.md)** | One-way server-to-client push (HTTP-based).                                  | Simpler than WebSockets for **fire-and-forget** updates (e.g., stock tickers). |
| **[gRPC Web](https://grpc.io/)**          | Binary protocol over HTTP/2, supports streaming.                                | High-performance APIs with **bidirectional streaming** (alternative to WebSockets). |
| **[Long Polling](https://developer.mozilla.org/en-US/docs/Web/HTTP/Long_polling)** | HTTP-based polling fallback for legacy support.                          | When WebSockets aren’t supported (e.g., older browsers).                      |
| **[Message Queues ( RabbitMQ/Kafka )]** | Decoupled communication via brokers.                                          | Scaling **event-driven architectures** with high throughput.                   |
| **[HTTP/2 Server Push](https://httpwg.org/specs/rfc7540.html)** | Server preemptively sends resources.                                         | Optimizing **page loads** with static assets (not real-time).                   |

---

## **Troubleshooting**
| **Issue**                  | **Diagnosis**                                                                 | **Solution**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Handshake Failure**     | `1008` (Policy Violation) or `1003` (Invalid Payload).                       | Check `Sec-WebSocket-Accept` header (must be SHA-1 hash of `key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"`). |
| **Connection Drops**      | No `onopen` or `onclose` events.                                             | Enable **keepalive pings** (`pingInterval` in libraries like `ws`).            |
| **High Latency**          | Delays in message delivery.                                                    | Reduce payload size or use **compression extensions**.                         |
| **Memory Leaks**          | Server crashes under load.                                                     | Set **idle timeout** (e.g., close after 5 minutes of inactivity).              |
| **CORS Errors**           | `Not allowed to connect to 'wss://example.com'`.                               | Configure server to accept `Origin` header or use `ws://localhost` for dev.    |

---
**Last Updated:** 2023-10
**Standards:** [IETF RFCs](https://www.rfc-editor.org/) | [WHATWG](https://whatwg.org/)