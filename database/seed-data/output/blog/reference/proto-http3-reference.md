# **[Pattern] HTTP/3 Protocol Patterns – Reference Guide**

## **Overview**
HTTP/3 (Hypertext Transfer Protocol version 3) is the latest major revision of HTTP, built on **QUIC** (Quick UDP Internet Connections) instead of TCP. This protocol replaces the traditional TCP-based handshake with a **multiplexed, secure-by-default** connection, enabling improved performance, reduced latency, and better resilience. This reference guide covers **key patterns, implementation details, best practices, and common pitfalls** for integrating and optimizing HTTP/3 in applications.

Key advantages over HTTP/2 and earlier versions include:
- **Faster connection establishment** (0-RTT for returning users).
- **Built-in encryption** (TLS 1.3 over QUIC).
- **Flow control & congestion avoidance** via QUIC’s built-in mechanisms.
- **Reduced head-of-line blocking**, improving scalability.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                     | **Example Value**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| **Protocol Layer**          | Underlying transport protocol. QUIC (UDP-based) replaces TCP.                                     | `QUIC/v1`                             |
| **Connection Establishment**| Initial handshake using TLS 1.3 (encapsulated in QUIC).                                             | `0-RTT` (pre-shared key), `1-RTT`      |
| **Stream Management**       | Multiplexed streams (like HTTP/2) but with better resource prioritization.                          | `Stream ID:` `0-2^64-1`               |
| **Header Compression**      | HPACK (like HTTP/2) for efficient request/response headers.                                        | `HPACK Dynamic Table`                 |
| **Server Push**             | Proactive resource delivery (similar to HTTP/2).                                                  | `Push-Promise` header                 |
| **Traffic Control**         | QUIC’s built-in congestion control (e.g., QUIC-Loss, QUIC-CC).                                    | `Pacing Rate: 10 Mbps`                |
| **Security**                | Mandatory TLS 1.3, preventing unencrypted QUIC.                                                   | `TLS 1.3 + Aead`                      |
| **Error Handling**          | QUIC-specific errors (e.g., `QUIC_STREAM_ERROR`, `QUIC_CONNECTION_ERROR`).                       | `ERR_STREAM_FLOW_CONTROL_ERROR`       |
| **Load Balancing**          | QUIC’s client affinity (reduces handoffs) and server affinity (optimized routing).                 | `Client IP → Server Affinity`          |

---

## **Query Examples**

### **1. Establishing an HTTP/3 Connection**
HTTP/3 uses **h3** instead of `http/1.1` or `http/2` in the ALPN (Application-Layer Protocol Negotiation).
```http
CONNECT :authority:example.com:443 HTTP/3
Host: example.com
```
- **Server Response:**
  ```http
  HTTP/3 200
  :status: 200
  Content-Type: text/html
  ```

### **2. Sending a GET Request with Multiplexed Streams**
HTTP/3 enables **parallel requests** without TCP head-of-line blocking.
```http
GET /images/photo.jpg HTTP/3
:method: GET
:path: /images/photo.jpg
:scheme: https
:authority: example.com
```
- **Server Push Example:**
  ```http
  103 Priority: 1
  PUSH-PROMISE :method: GET
  :path: /styles/main.css
  ```
  (Server proactively sends `main.css` before the client requests it.)

### **3. Stream Prioritization (Critical vs. Non-Critical Resources)**
```http
GET /critical-resource.js HTTP/3
:method: GET
:path: /critical-resource.js
stream_priority: 16384:256:100  # High priority
```
- **Lower stream_priority values** indicate higher priority.

### **4. QUIC-Specific Error Responses**
If a stream fails, HTTP/3 sends a **QUIC error**:
```http
HTTP/3 499 QUIC_STREAM_ERROR
:status: 499
quic_error_code: 0x80000001  # STREAM_ERROR
quic_error_reason: "INTERNAL_ERROR"
```

### **5. Connection Migration (Mobile Devices)**
QUIC allows **seamless handoff** between networks (e.g., Wi-Fi to cellular).
```http
QUIC CONNECT example.com:443
# Client IP changes, but QUIC maintains the connection.
```

---

## **Implementation Best Practices**

### **Server-Side Considerations**
1. **Enable QUIC on TLS Ports**
   - Configure `h2` and `h3` support in your server (e.g., Nginx, Caddy, Cloudflare).

2. **Optimize Stream Prioritization**
   - Use **`stream_priority`** to mark critical resources (e.g., JavaScript, CSS) for faster delivery.

3. **Test Latency & Throughput**
   - Use tools like **`speedtest-cli`**, **`quic-tools`**, or **`nghttp3`** to benchmark performance.

4. **Handle QUIC Errors Gracefully**
   - Implement retries for `QUIC_STREAM_ERROR` or `QUIC_CONNECTION_ERROR`.

5. **Leverage Server Push**
   - Push static assets (JS, CSS) to reduce RTT.

### **Client-Side Considerations**
1. **Support 0-RTT (If Supported)**
   - Use **pre-shared keys** (PSK) for faster initial connections.

2. **Fallback to HTTP/2 if QUIC Fails**
   - Detect QUIC availability and gracefully degrade.

3. **Monitor QUIC Metrics**
   - Track:
     - Latency (RTT)
     - Packet loss (QUIC’s built-in recovery)
     - Stream prioritization effectiveness

4. **Use QUIC in Mobile Apps**
   - Ideal for apps with frequent network changes (e.g., VoIP, gaming).

### **Network & Infrastructure**
1. **Firewall & NAT Considerations**
   - QUIC operates over UDP; ensure firewalls allow **UDP port 443**.

2. **Load Balancing with QUIC**
   - Use **IP-based affinity** to minimize connection resets.

3. **CDN & HTTP/3**
   - Edge networks (Cloudflare, Fastly) accelerate HTTP/3 by caching at the edge.

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Description**                                                                 | **Mitigation**                                                                 |
|---------------------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Lack of HTTP/3 Server Support**     | Some legacy servers don’t support h3.                                          | Use reverse proxies (Nginx, Caddy) or edge services.                         |
| **QUIC Congestion Control Issues**    | Suboptimal loss recovery compared to TCP.                                     | Tune QUIC congestion algorithms (e.g., QUIC-CC).                            |
| **Mobile Data Cost Overhead**         | QUIC may increase UDP packet overhead.                                        | Compress payloads (e.g., Brotli) and optimize image sizes.                  |
| **Debugging Complexity**              | QUIC errors (e.g., `0x80000001`) are less standardized than HTTP/2 errors.      | Use `wireshark` with QUIC dissector or `quiclog`.                             |
| **Browser Support Gaps**              | Older browsers (e.g., Safari <15) don’t fully support HTTP/3.                  | Feature detection (`navigator.connection.effectiveType`).                    |

---

## **Benchmarking HTTP/3 vs. HTTP/2**
| **Metric**            | **HTTP/3 (QUIC)**       | **HTTP/2 (TCP)**          |
|-----------------------|-------------------------|---------------------------|
| **Connection Time**   | ~1 RTT (0-RTT possible) | ~3 RTTs (TLS + TCP handshake) |
| **Latency**           | Lower (multiplexed)     | Higher (head-of-line blocking) |
| **Encryption**        | Mandatory TLS 1.3       | Optional                  |
| **Mobility Support**  | Seamless handoff         | Requires TCP reconnect     |

---

## **Tools & Libraries**
| **Tool/Library**       | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| [`nghttp3`](https://nghttp2.org/doc/) | C library for QUIC/HTTP/3.                                                  |
| [`quiche`](https://github.com/cloudflare/quiche) | Cloudflare’s QUIC implementation (Rust).                              |
| [`h3`](https://github.com/cloudflare/h3) | HTTP/3 library (used in Cloudflare’s CDN).                               |
| [`quic-tools`](https://github.com/quic-go/quic-go/tree/master/tools) | Testing QUIC connections.                                               |
| [`go-quic`](https://github.com/lucas-clemente/quic-go) | Go implementation of QUIC.                                               |
| [`wireshark QUIC dissector`](https://wiki.wireshark.org/QUIC) | Packet analysis.                                                          |

---

## **Related Patterns**
1. **Multiplexed Requests**
   - HTTP/3’s stream-based model improves performance by allowing concurrent requests without blocking.

2. **TLS 1.3 Enforcement**
   - HTTP/3 mandates TLS 1.3; ensure your infrastructure supports modern cipher suites.

3. **Connection Pooling (QUIC vs. TCP)**
   - QUIC maintains **persistent connections** with better resource reuse than TCP.

4. **Edge Caching Strategies**
   - Leverage HTTP/3’s low latency for **edge caching** (e.g., Cloudflare Workers).

5. **Protocol Migration (HTTP/2 → HTTP/3)**
   - Gradually adopt HTTP/3 while supporting HTTP/2 for backward compatibility.

---

## **Conclusion**
HTTP/3’s **QUIC-based architecture** delivers **faster, more reliable** web interactions compared to HTTP/2. By following this guide—**prioritizing streams, optimizing for 0-RTT, and mitigating QUIC-specific issues**—you can unlock performance gains in high-latency environments.

For further reading:
- [RFC 9114 (HTTP/3)](https://www.rfc-editor.org/rfc/rfc9114)
- [QUIC WG](https://github.com/quicwg/base-drafts)
- [Cloudflare’s HTTP/3 Guide](https://developers.cloudflare.com/quic/)