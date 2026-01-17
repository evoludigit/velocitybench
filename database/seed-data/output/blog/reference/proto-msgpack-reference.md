# **[Pattern] MessagePack Protocol Patterns – Reference Guide**

---
## **Overview**
MessagePack is a lightweight binary serialization format optimized for speed and compactness, widely used in distributed systems, APIs, and high-performance messaging. This reference guide outlines **MessagePack protocol patterns**—structured conventions for encoding data, handling payloads, and integrating with systems like gRPC, Kafka, or REST. It covers core concepts, schema definitions, query patterns, and implementation best practices to ensure interoperability and efficiency.

Key focus areas:
- **Efficient serialization** (binary vs. JSON alternatives)
- **Payload structures** (headers, versions, and payload encoding)
- **Error handling** (invalid data, corrupt streams)
- **Performance optimizations** (compression, batching)

---

## **Schema Reference**
The following table defines common MessagePack payload structures and their binary representations.

| **Component**          | **Purpose**                                                                 | **Format**                                                                 | **Example (Hex)**                     | **Notes**                          |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|----------------------------------------|------------------------------------|
| **Header**             | Identifies payload type and version.                                       | `Map:1 ["type" => "msg", "version" => 1.0]`                                | `82 61 74 79 70 65 22 6D 73 67 22 62...` | Versioning enables backward compatibility. |
| **Payload Type**       | Specifies data format (e.g., `protobuf`, `json`).                          | String (`"protobuf"`, `"json"`, etc.).                                     | `82 61 74 79 70 65 22 70 72 6F 74 6F ...` | Required for deserialization.       |
| **Data Payload**       | Actual content (encoded via MessagePack/other formats).                    | Binary data (MessagePack array/map, protobuf, etc.).                      | `D4 00 ...` (protobuf) or `A3 ...` (MessagePack) | Payload size capped at 65,535 bytes. |
| **Metadata**           | Optional key-value pairs (e.g., `timestamp`, `source`).                       | `Map:2 ["timestamp" => ISOTIME, "source" => "service-A"]`                   | `A2 61 6C 74 ...`                      | Use sparingly to avoid bloat.      |
| **Signature**          | HMAC for integrity (optional).                                             | Base64-encoded HMAC (`"sig" => hmac(base64)`).                            | `82 61 73 69 67 ...`                   | Recommended for security.         |

---
## **Common Payload Structures**
### 1. **Raw MessagePack Payload**
```plaintext
{
  "type": "msg",
  "version": "1.0",
  "data": [1, {"key": "value"}, null],
  "metadata": {
    "timestamp": "2024-05-20T12:00:00Z",
    "source": "service-A"
  }
}
```
**Binary Representation**:
```
A3 61 74 79 70 65 22 6D 73 67 22 62 22 76 65 72 73 69 6F 6E 22 31 2E 30 22 64 61 74 61 22 A3 01 00 A3 61 6B 65 79 22 76 61 6C 75 65 22 61 64 ... 00
```

### 2. **Protobuf-Wrapped Payload**
```plaintext
{
  "type": "protobuf",
  "version": "1.0",
  "data": <binary protobuf>,
  "signature": "base64-hmac"
}
```

---
## **Query Examples**
### **1. Sending a MessagePack Payload (Node.js)**
```javascript
const msgpack = require('msgpack-lite');

const payload = {
  type: "msg",
  version: "1.0",
  data: { user: "Alice", status: "active" }
};

const buffer = msgpack.encode(payload);
const header = msgpack.encode({ type: "msg", version: "1.0" });
const fullPayload = Buffer.concat([header, buffer]);

// Send via WebSocket/HTTP
client.send(fullPayload);
```

### **2. Decoding a Protobuf Payload (Python)**
```python
import msgpack
import base64

def decode_protobuf_payload(buffer):
    header = msgpack.unpackb(buffer[:10])  # Extract header
    data_start = 10  # Skip header
    data_end = buffer.find(b'\x00\x00\x00\x00')  # Protobuf length prefix

    protobuf_data = buffer[data_start:data_end]
    signature = base64.b64decode(buffer[data_end:].decode())
    return protobuf_data, signature
```

### **3. Validating a Signature (Go)**
```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
)

func verifySignature(data, signature, key []byte) bool {
	h := hmac.New(sha256.New, key)
	h.Write(data)
	expectedSig := h.Sum(nil)
	return hmac.Equal(expectedSig, signature)
}
```

---

## **Best Practices**
1. **Versioning**: Use semantic versioning in headers to support backward compatibility.
2. **Payload Size**: Limit payloads to <64KB to avoid fragmentation (especially for TCP/UDP).
3. **Compression**: Enable `gzip`/`zstd` for large payloads (e.g., Protobuf).
4. **Error Handling**:
   - Return `400 Bad Request` for malformed payloads.
   - Use `Map{"error": "invalid_signature"}` for integrity failures.
5. **Performance**:
   - Pre-allocate buffers for repeated operations.
   - Use streaming decoders (e.g., `msgpack-stream` in Node.js).

---

## **Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| Incorrect length prefixes (protobuf). | Always include 4-byte length prefix for binary data.                        |
| Missing `type` header.               | Validate headers before processing; reject malformed payloads.              |
| No compression for large JSON.       | Encode JSON as MessagePack or use `zstd` compression in HTTP headers.       |
| Race conditions in concurrent sends. | Use sequence IDs or timestamps in metadata to detect duplicates.            |

---

## **Related Patterns**
1. **[Binary Payload Encoding]**
   - Covers protobuf, Avro, and MessagePack for performance-critical systems.
   - *See*: [Protobuf Schema Design](https://developers.google.com/protocol-buffers).

2. **[Streaming Protocol]**
   - Combines MessagePack with gRPC streaming for real-time data.
   - *See*: [gRPC Streaming Guide](https://grpc.io/docs/what-is-grpc/core-concepts/#streaming).

3. **[Idempotent Requests]**
   - Ensures replayability of MessagePack payloads using IDs in metadata.
   - *See*: [Idempotency in APIs](https://docs.aws.amazon.com/amazons3/latest/userguide/idempotency.html).

4. **[Payload Chunking]**
   - Splits large payloads into chunks (e.g., for WebSockets or Kafka).
   - *See*: [Kafka Message Chunking](https://kafka.apache.org/documentation/#basic_ops_message_format).

---

## **Tools & Libraries**
| **Language** | **Library**               | **Features**                                  |
|--------------|---------------------------|-----------------------------------------------|
| JavaScript   | `msgpack-lite`            | Ultra-fast encoding/decoding.                  |
| Python       | `msgpack`                 | Supports streaming and extensions.             |
| Go           | `msgpack`                 | Zero-alloc encoding for performance.          |
| Rust         | `rmp-serde`               | Serialization with `serde` support.           |
| Java         | `msgpack-java`            | Integrates with Protobuf/Jackson.             |

---
## **Further Reading**
- [MessagePack Spec](https://msgpack.org/index.html)
- [gRPC Messagepack Interop](https://github.com/google/gnostic)
- [Protobuf vs. MessagePack](https://blog.protobuf.dev/2020/01/protobuf-vs-messagepack.html)