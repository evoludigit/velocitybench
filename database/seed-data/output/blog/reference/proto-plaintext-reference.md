# **[Pattern] PLAINTEXT Protocol Patterns Reference Guide**

---

## **Overview**
The **PLAINTEXT Protocol Patterns** pattern standardizes the structure and semantics of inter-process communication (IPC) in plaintext-based protocols. This guide defines best practices for encoding requests/responses, handling error states, and versioning in human-readable, machine-parsable formats. Suitable for REST APIs, command-line tools, and file-based exchanges, this pattern ensures **interoperability, debuggability, and extensibility** while avoiding binary dependencies.

Key principles:
- **Readability first**: Prioritize human readability over compression.
- **Semantic consistency**: Use standardized structure for requests/responses/errors.
- **Idempotency**: Design patterns to allow repeated execution without unintended side effects.
- **Versioning**: Support backward compatibility via schema evolution strategies.

---

## **Schema Reference**
Below are the core components of PLAINTEXT Protocol Patterns, expressed as a nested JSON-like schema for clarity.

| **Component**               | **Field**       | **Type**          | **Description**                                                                                     | **Example**                     | **Requirements**                                                                 |
|-----------------------------|-----------------|-------------------|-----------------------------------------------------------------------------------------------------|----------------------------------|----------------------------------------------------------------------------------|
| **Message Header**          | `version`       | String            | Protocol version (e.g., `1.0`). Must match client/server expectations.                             | `"version": "1.0"`               | Mandatory. Use **semver** syntax (e.g., `MAJOR.MINOR.PATCH`).                     |
|                             | `id`            | UUID/String       | Unique identifier for request/response (for correlation).                                          | `"id": "a1b2c3d4-e5f6-7890"`     | Optional but recommended for debugging.                                         |
|                             | `timestamp`     | ISO 8601 String   | When the request was sent (RFC 3339 format).                                                       | `"timestamp": "2024-05-20T12:00:00Z"` | Mandatory if used for replay protection.                                      |
| **Payload**                 | `method`        | String            | Operation to execute (e.g., `GET`, `CREATE`, `UPDATE`).                                            | `"method": "GET"`                | Mandatory. Use **verb-noun** convention (e.g., `USER_FETCH`).                     |
|                             | `params`        | Object/Array      | Key-value pairs or structured data for the operation.                                              | `"params": {"user_id": 123}`    | Optional. May require validation rules per `method`.                           |
|                             | `data`          | Object/Array      | Embedded payload (e.g., JSON, XML, or CSV strings).                                                | `"data": {"name": "Alice"}`      | Optional if `method` doesn’t require it.                                         |
| **Error Handling**          | `error`         | Object            | Error details (only present in responses).                                                          | `"error": {"code": "404", "msg": "Not found"}` | Optional but recommended for non-successful responses.                           |
|                             | `error.code`    | Number/String     | HTTP-like status code or custom identifier (e.g., `400`, `VALIDATION_FAILED`).                     | `"code": "400"`                  | Mandatory if `error` is present. Use **numeric codes** for machine parsing.     |
|                             | `error.msg`     | String            | Human-readable error description.                                                                   | `"msg": "Invalid email format"`  | Mandatory if `error` is present. Localize when possible.                        |
|                             | `error.details` | Object/Array      | Structured error metadata (e.g., `field: "email"`, `reason: "required"`).                         | `"details": {"field": "email"}`  | Optional for debugging.                                                          |
| **Versioning**              | `compat`        | Object            | Indicates support for older protocol versions.                                                    | `"compat": {"supports": ["0.9"]}` | Optional but recommended for backward compatibility.                            |
|                             | `compat.supports`| Array of Strings  | List of compatible versions (e.g., `["0.9", "0.8"]`).                                               | `["0.9"]`                        | If present, server must validate against these versions.                         |

---

## **Query Examples**
### **1. Successful Request/Response (GET User)**
**Request:**
```plaintext
version: 1.0
id: a1b2c3d4-e5f6-7890
timestamp: 2024-05-20T12:00:00Z
method: USER_FETCH
params:
  user_id: 123
```

**Response:**
```plaintext
version: 1.0
id: a1b2c3d4-e5f6-7890
timestamp: 2024-05-20T12:00:01Z
data:
  user_id: 123
  name: Alice
  email: alice@example.com
```

---

### **2. Error Response (Invalid Parameters)**
**Request:**
```plaintext
version: 1.0
id: b2c3d4e5-f6a7-0981
timestamp: 2024-05-20T12:00:02Z
method: USER_CREATE
params:
  email: invalid-email
```

**Response:**
```plaintext
version: 1.0
id: b2c3d4e5-f6a7-0981
timestamp: 2024-05-20T12:00:03Z
error:
  code: 400
  msg: "Invalid email format"
  details:
    field: email
    reason: "must be a valid email address"
```

---

### **3. Backward-Compatible Response (Legacy Version)**
**Request:**
```plaintext
version: 1.0
compat:
  supports: ["0.9"]
id: c3d4e5f6-a7b8-1920
timestamp: 2024-05-20T12:00:04Z
method: USER_FETCH
params:
  user_id: 123
```

**Response (v0.9 Compatible):**
```plaintext
version: 0.9
id: c3d4e5f6-a7b8-1920
user: "123:Alice,alice@example.com"
```
*(Note: Server may return a simplified format for legacy clients.)*

---

## **Implementation Best Practices**
### **1. Encoding**
- **Use UTF-8**: All text must be encoded in UTF-8 to ensure cross-platform compatibility.
- **Line-Delimited Format**: Separate key-value pairs with `\n` for parsers (e.g., key`: value\n`).
- **Escape Special Characters**: Use backslashes (`\`) for newlines/tabs in values (e.g., `\n` → `\\n`).

### **2. Validation**
- **Schema Enforcement**: Use tools like [JSON Schema](https://json-schema.org/) or custom parsers to validate `params`/`data`.
- **Idempotency Keys**: For state-changing operations (e.g., `CREATE`), include a `client_id` in `params` to allow retries.

### **3. Security**
- **Avoid Sensitive Data**: Plaintext protocols are **not encrypted**. Use TLS/SSL for transport security.
- **Rate Limiting**: Implement `X-RateLimit-*` headers (e.g., `X-RateLimit-Remaining: 10`) in responses.

### **4. Versioning Strategies**
- **Backward Compatibility**: Add new fields (not remove or rename existing ones).
- **Deprecation Policy**: Use `compat.supports` to signal end-of-life for old versions (e.g., `supports: ["1.0"]` → `supports: []` in v2.0).

---

## **Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                                                                                 |
|--------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **Parsing Ambiguity**                | Use strict delimiters (e.g., `\n` for key-value pairs) and avoid multi-line values unless escaped.                                                   |
| **Large Payloads**                   | For data >1KB, use base64-encoded binary (e.g., `data: base64: ...`) or link to external resources (e.g., `data_url: "https://..."`).          |
| **Case Sensitivity**                 | Standardize field names (e.g., `snake_case` for public APIs, `camelCase` for internal tools).                                                          |
| **Circular References**              | Flatten nested objects or use `id`/`ref` fields (e.g., `data: {"user": {"id": 123, "ref": "/users/123"}}`).                                     |
| **Timezone Issues**                  | Always use **UTC** (RFC 3339) for `timestamp`. Clients should convert to local timezone client-side.                                                  |

---

## **Related Patterns**
1. **RESTful API Design**
   - Use PLAINTEXT alongside REST for human-readable request/response bodies (e.g., `Application/Plaintext` media type).
   - *Reference*: [REST API Design Best Practices](https://restfulapi.net/).

2. **gRPC with Plaintext Overrides**
   - Combine PLAINTEXT with gRPC’s binary efficiency for internal services (e.g., use PLAINTEXT for debugging, Protobuf for performance).
   - *Reference*: [gRPC Protocol Buffers](https://grpc.io/docs/protocol-buffers/).

3. **Cron Job Logging**
   - Format cron job output as PLAINTEXT for parsing (e.g., `LOG: [2024-05-20 12:00:00] status: success, users_processed: 100`).
   - *Reference*: [Structured Logging Patterns](https://www.oreilly.com/library/view/structured-logging/9781492076147/).

4. **Configuration Files**
   - Use PLAINTEXT for machine-readable configs (e.g., `service: {enabled: true, max_retries: 3}` in INI/TOML).
   - *Reference*: [TOML Specification](https://toml.io/en/).

5. **Event Streaming**
   - Encode events in PLAINTEXT for tools like Kafka or RabbitMQ (e.g., `{event: "user_login", user_id: 123, time: "2024-05-20T12:00:00Z"}`).
   - *Reference*: [Event-Driven Architecture](https://www.eventstore.com/blog/event-driven-architecture-vs-event-sourcing-vs-cqrs).

---
## **Further Reading**
- [RFC 7159 (JSON)](https://datatracker.ietf.org/doc/html/rfc7159) – Structured data standard for `params`/`data`.
- [Semantic Versioning 2.0](https://semver.org/) – Guidelines for `version` field.
- [HTTP Status Codes](https://httpstatuses.com/) – Reference for `error.code` values.