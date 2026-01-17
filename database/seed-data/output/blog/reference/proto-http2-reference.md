# **[Pattern] HTTP/2 Protocol Patterns Reference Guide**

---
## **Overview**
HTTP/2 (Hypertext Transfer Protocol version 2) is a major revision of the HTTP protocol designed to improve performance, security, and efficiency over HTTP/1.1. This guide covers **key implementation patterns**, best practices, and common pitfalls for developers integrating HTTP/2 into web applications, APIs, and microservices. Unlike HTTP/1.1, HTTP/2 introduces **multiplexing, header compression (HPACK), server push**, and binary framing, reducing latency and improving resource loading. While adoption is widespread, improper implementation can lead to degraded performance, protocol violations, or security risks.

This document is structured for **developers, architects, and DevOps engineers** working with HTTP/2 in backend systems, edge networks, or client applications (e.g., browsers, mobile apps). We’ll focus on **server-side patterns** (e.g., handling requests/responses) and **client-side optimizations** (e.g., dynamic server push, connection management).

---

## **Schema Reference**
HTTP/2 operates over **TLS (required)** or plaintext (legacy support) and uses a binary **frame-based protocol** for communication. Below are critical **schema patterns** with key fields:

| **Pattern**               | **Description**                                                                 | **Key HTTP/2 Frames**               | **Example Use Case**                          |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------|-----------------------------------------------|
| **Multiplexed Requests**  | Multiple requests/responses share a single TCP connection via stream IDs.       | `HEADERS`, `DATA`, `PRIORITY`          | Concurrent API calls over one persistent conn. |
| **Server Push**           | Server proactively sends resources before the client requests them.            | `PRIORITY`, `RST_STREAM`              | Preload CSS/JS in web pages.                  |
| **Header Compression (HPACK)** | Compresses repeated headers (e.g., `Host`, `Authorization`) to reduce overhead. | `HEADERS` (with dynamic tables)       | High-frequency API calls in mobile apps.      |
| **Stream Prioritization** | Client hints server on request priority (e.g., critical resources first).       | `PRIORITY` frame                       | Prioritize hero image over footer in SPAs.    |
| **Connection Pooling**    | Reuse TCP connections with connection window tuning (e.g., `SETTINGS_WINDOW_UPDATE`). | `SETTINGS`, `WINDOW_UPDATE`           | Microservices with high request volumes.     |
| **Error Handling**        | Graceful handling of `GOAWAY`, `RST_STREAM`, or `PROTOCOL_ERROR`.               | `RST_STREAM`, `GOAWAY`                | Retry failed streams with exponential backoff.|
| **Trailers**              | Send metadata after response body (e.g., `Content-Length` for chunked transfers). | `HEADERS` (trailer frame)             | Large file uploads with progress tracking.    |

---
**Note:**
- **Frame Types**: See [RFC 7540](https://tools.ietf.org/html/rfc7540#section-5) for all frame types (e.g., `DATA`, `PING`, `GOAWAY`).
- **Dependencies**: HTTP/2 requires TLS (port 443). Plaintext HTTP/2 is deprecated post-June 2024.

---

## **Implementation Patterns**

### **1. Multiplexed Requests**
**Goal**: Maximize throughput by sending multiple requests concurrently over a single connection.

#### **Key Considerations**:
- **Stream IDs**: Each request/response is a **bidirectional stream** (unique stream ID).
- **Dependency Graph**: Parent streams (e.g., HTML) can prioritize child streams (e.g., CSS).
- **Flow Control**: Avoid overwhelming the server with `WINDOW_UPDATE` frames.

#### **Example (Server-Side in Node.js)**:
```javascript
const http2 = require('http2');
const server = http2.createSecureServer({ key, cert });

server.on('stream', (stream, headers) => {
  // Stream ID: e.g., 1 (first request)
  stream.respond({ ':status': 200 });
  stream.end('HTML + CSS/JS (concurrent)');
});

server.listen(443);
```

#### **Client-Side (Browser)**:
HTTP/2 is automatically used in modern browsers for `https://` domains. For custom clients:
```python
# Python (using h2)
import h2.connection
conn = h2.connection.H2Connection()
conn.send_headers(frame_type=h2.headers.HeadersFrame, stream_id=1, headers=[
    ("GET", "/api/data"),
    ("Host", "example.com")
])
```

---
### **2. Server Push**
**Goal**: Reduce round trips by pre-sending static/assets.

#### **Requirements**:
- Server must know client needs resources (e.g., via `Accept` headers).
- Use `PRIORITY` frame to hint importance (e.g., `stream_id=1` for critical resources).

#### **Example (Nginx Configuration)**:
```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    location / {
        push @static/css/main.css;
        push @static/js/app.js;
    }
}
```

#### **Client-Side Handling**:
- Clients must **ignore unsolicited pushes** (use `PRIORITY` to hint preference).
- Monitor `GOAWAY` frames to avoid overloading servers.

---
### **3. Header Compression (HPACK)**
**Goal**: Reduce header size (e.g., repeated `Host`, `Cookie` fields).

#### **Dynamic Table**:
- The HPACK table grows dynamically (up to 65,535 entries).
- **Static Table**: Predefined 61 entries (e.g., `:method`, `content-length`).

#### **Mitigating Issues**:
- **Table Overflow**: Reset with `PING` or `GOAWAY`.
- **Denial-of-Service**: Limit dynamic table size (e.g., `SETTINGS_HEADER_TABLE_SIZE`).
  ```http2
  SETTINGS_HEADER_TABLE_SIZE: 4096
  ```

---
### **4. Stream Prioritization**
**Goal**: Optimize load order (e.g., render-critical resources first).

#### **Priority Levels**:
- **Weight (1–256)**: Higher weight = higher priority (default: 16).
- **Dependency Stream ID**: Link child streams to parents (e.g., CSS depends on HTML).

#### **Example (Python Client)**:
```python
conn.send_priority(stream_id=3, weight=10, dependency_stream_id=1)
```

---
### **5. Connection Management**
**Goal**: Balance throughput vs. resource usage.

#### **Window Tuning**:
- Adjust `WINDOW_UPDATE` frames to avoid TCP congestion.
- Example: Increase receiver window size for large payloads.

#### **Connection Teardown**:
- Use `GOAWAY` to close connections gracefully (e.g., on server overload).
  ```http2
  GOAWAY: last_stream_id=42, debug_data="Server busy"
  ```

---
## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Cause**                                  | **Mitigation**                                  |
|---------------------------------------|--------------------------------------------|------------------------------------------------|
| **Latency Spikes**                    | Headers too large (HPACK table full).      | Limit dynamic table size (`SETTINGS`).          |
| **Connection Resets**                 | Malformed frames (e.g., invalid `stream_id`). | Use `RST_STREAM` for errors.                  |
| **Server Overload**                   | Uncontrolled server push.                 | Rate-limit pushes; monitor `GOAWAY`.           |
| **Browser/Client Misconfiguration**   | Incorrect TLS settings (e.g., no SNI).     | Test with [http2.pro](https://http2.pro/).      |
| **Legacy HTTP/1.1 Interoperability** | Mixed protocols on one port.              | Use separate ports (e.g., HTTP/2 on 443, HTTP/1.1 on 80). |

---

## **Query Examples**
### **1. Multiplexed API Calls (cURL)**
```bash
# Send 3 concurrent requests over HTTP/2
curl -v --http2 --connect-to example.com:443:localhost:8443 \
  -H "Host: example.com" \
  -X GET "https://example.com/api/a" \
  -X GET "https://example.com/api/b" \
  -X GET "https://example.com/api/c"
```

### **2. Server Push (Nginx)**
```nginx
location / {
    push @static/images/logo.png priority=high;
    push @static/scripts/app.js;
}
```

### **3. Prioritized Streams (Python)**
```python
# Prioritize /api/data over /api/logs
conn.send_headers(frame_type=h2.headers.HeadersFrame, stream_id=1, headers=[...
conn.send_priority(stream_id=1, weight=255, dependency_stream_id=None)
conn.send_headers(frame_type=h2.headers.HeadersFrame, stream_id=2, headers=[...
```

---

## **Related Patterns**
1. **[TLS Everywhere]** – HTTP/2 mandates TLS; ensure secure connections with modern cipher suites (e.g., TLS 1.2+).
2. **[Connection Pooling]** – Reuse HTTP/2 connections to minimize TCP handshakes.
3. **[Header Splitting Attack Mitigation]** – Use `SETTINGS_ENABLE_PUSH` cautiously to avoid injection risks.
4. **[Load Balancer Tuning]** – Configure load balancers (e.g., Nginx, Envoy) for HTTP/2-specific settings (e.g., `proxy_http2_max_field_size`).
5. **[Progressive Enhancement]** – Gracefully degrade for HTTP/1.1 clients via feature detection.

---
## **Further Reading**
- [RFC 7540 (HTTP/2 Spec)](https://tools.ietf.org/html/rfc7540)
- [HPACK Format (RFC 7541)](https://tools.ietf.org/html/rfc7541)
- [HTTP/2 Server Push Guide](https://http2.github.io/httpr2-spec/#push)
- [Envoy HTTP/2 Docs](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/http/http2)

---
**Last Updated**: [Insert Date]
**Contributors**: [List Names]