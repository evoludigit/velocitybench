# **[Pattern] CBOR Protocol Patterns – Reference Guide**

---

## **Overview**
CBOR (Concise Binary Object Representation) is a minimal binary serialization format designed for efficiency, interoperability, and interoperability in constrained environments. This reference guide covers **CBOR Protocol Patterns**, focusing on structured protocols, message encoding, and real-world implementations. It includes **best practices for schema design, message framing, error handling, and performance optimizations**, along with tables, code snippets, and anti-patterns to avoid.

Key use cases include **IoT device communication, edge computing, and low-power applications** where JSON’s verbosity is prohibitive. This guide assumes familiarity with CBOR basics (e.g., major types, tags) but details advanced patterns.

---

## **1. Core Concepts & Schema Design**
CBOR’s flexibility allows protocol designers to create structured patterns while maintaining efficiency. Below are foundational building blocks:

### **1.1. Message Framing**
CBOR does not natively include framing (unlike HTTP/2 or AMQP). Common framing approaches include:

| **Framing Method**       | **Use Case**                          | **Pros**                          | **Cons**                          |
|--------------------------|---------------------------------------|-----------------------------------|-----------------------------------|
| **Length-prefixed**      | Fixed-size or variable payloads       | Simple to implement               | Inefficient for large messages    |
| **Protocbuf-like**       | Streamed binary protocols             | Supports partial reads            | Requires parser tuning            |
| **Chunked (e.g., CBOR+)**| Large binary data (e.g., images)      | Works with CBOR’s binary tags     | Complex to decode                 |

**Example (Length-Prefixed):**
```cbor
[ uint(4): payload_length, CBOR_payload ]
```
*Payload length (4 bytes) precedes data.*

### **1.2. Tagged Data for Extensibility**
CBOR tags enable semantic meaning without breaking compatibility. Common tags:

| **Tag**       | **Purpose**                          | **Example Use Case**               |
|---------------|--------------------------------------|------------------------------------|
| `23`          | JSON-compatible text                | Legacy system interop              |
| `32`          | DateTime (ISO 8601)                  | Event timestamps                    |
| `42`          | URL                                  | Remote configuration URLs          |
| `custom`      | Protocol-specific metadata           | Device firmware version            |

**Example (Tagged Device Metadata):**
```cbor
[ 42: "https://config.example.com", 65532: "v1.2.3" ]
```

---

## **2. Schema Reference**
Use this table to design CBOR message schemas. Columns define **major type**, **semantics**, and **validation rules**.

| **Field**          | **Type**       | **CBOR Major Type** | **Description**                          | **Validation Rules**                     | **Example**                     |
|--------------------|----------------|---------------------|------------------------------------------|------------------------------------------|---------------------------------|
| `device_id`        | Text           | Text String (7)     | Unique device identifier                 | 32-char hex, uppercase                  | `"A1B2C3..."`                  |
| `timestamp`        | DateTime       | Tag 32              | Unix epoch (seconds)                     | Must be > current timestamp             | `2023-01-01T00:00:00Z` (tagged) |
| `sensor_data`      | Array          | Array (8)           | List of `(value, unit)` pairs            | Each pair must be `[float, text]`        | `[ [23.5, "C"], [1013, "hPa"] ]`|
| `error_code`       | Integer        | Integer (2/4/6)     | Error classification (e.g., 404, 500)   | Must match predefined enum              | `404`                           |
| `binary_payload`   | Binary         | Byte String (3)     | Raw sensor data (e.g., FFT samples)      | Max size: 1024 bytes                     | `base64: "AQIDBA=="`           |

---
**Key Validation Tools:**
- **BEAM (CBOR Schema Language)**: Define schemas declaratively.
- **libcbor (C)**: Validate with `libcbor_map_get` checks.

---

## **3. Query Examples**
### **3.1. Sensor Data Collection**
**Request (Device → Backend):**
```cbor
{
  "device_id": "DEV-1234",
  "timestamp": 1704067200, // Jan 1, 2024
  "sensors": [
    [23.5, "C"],
    [1013, "hPa"],
    [0.87, "humidity"]
  ],
  "status": "healthy"
}
```
*Encoded as a CBOR map (major type 5).*

**Response (Backend → Device):**
```cbor
{
  "status": "acknowledged",
  "config": {
    "threshold": 25.0,
    "update_interval": 60
  }
}
```

### **3.2. Error Handling**
**Error Response (Tagged):**
```cbor
{
  "error": {
    "code": 400,
    "message": "Invalid timestamp",
    "details": {
      "received": 1600000000, // Invalid epoch
      "required": "32-bit signed"
    }
  }
}
```
*Use **Tag 18 (`application/error`)** for protocol-wide errors.*

### **3.3. Binary Payloads (e.g., Image Upload)**
```cbor
{
  "format": "jpeg",
  "compression": "none",
  "data": <base64-encoded binary>,
  "sha256": "hash_123..."
}
```
*For large payloads, split into chunks and send incrementally.*

---
**Anti-Patterns:**
- **Over-tagging**: Reserve tags for critical use cases (e.g., 0–31 are reserved).
- **Unbounded Arrays**: Limit array sizes to prevent denial-of-service (e.g., max 1000 elements).

---

## **4. Performance Optimizations**
| **Optimization**               | **Technique**                                  | **Impact**                          |
|---------------------------------|-----------------------------------------------|-------------------------------------|
| **Major Type Compression**      | Prefer integers (major type 2) over floats (6) | Reduces size by ~50%                 |
| **Canonical Order**             | Sort maps by key                              | Faster decoding                     |
| **Shared References**           | Use CBOR’s `reference` (tag 6) for large objects | Avoids duplication                  |
| **Client-Side Parsing**         | Use streaming parsers (e.g., `cbor-stream`)   | Lower latency                       |

---
**Benchmark Example:**
| **Message Type**       | **JSON Size (Bytes)** | **CBOR Size (Bytes)** | **Speedup** |
|------------------------|-----------------------|-----------------------|-------------|
| Sensor Readings        | 312                   | 102                   | 3x          |
| Device Config          | 456                   | 89                    | 5x          |

---

## **5. Related Patterns**
| **Pattern**               | **Related Concept**               | **Reference**                     |
|---------------------------|-----------------------------------|-----------------------------------|
| **JSON-CBOR Hybrid**      | Use CBOR for binary, JSON for text | [RFC 8946](https://tools.ietf.org/html/rfc8946) |
| **CoAP over CBOR**        | Lightweight IoT protocols         | [RFC 7252](https://tools.ietf.org/html/rfc7252) |
| **gRPC-CBOR**             | High-performance RPC              | [gRPC-CBOR Encoding](https://github.com/protocolbuffers/protobuf/blob/master/src/google/protobuf/cbor/cbor_test.proto) |
| **Schema Registry**       | Centralized validation            | [Avro-CBOR Interop](https://avro.apache.org/docs/current/encoding.html) |

---
**Further Reading:**
- [RFC 7049](https://tools.ietf.org/html/rfc7049) (CBOR spec)
- [libcbor Codec](https://github.com/P sabotage/libcbor) (Implementation)
- [CBOR in Rust](https://crates.io/crates/cbor) (Efficient parsing)

---
**Last Updated:** 2024-03-15
**Version:** 1.2