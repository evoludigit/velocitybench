**[Pattern] REST Troubleshooting Reference Guide**

---

### **Overview**
The **REST Troubleshooting** pattern provides a structured approach to diagnosing and resolving issues in RESTful APIs. This guide covers systematic steps for identifying root causes—such as client-side errors, server misconfigurations, or network issues—along with tools, logging best practices, and diagnostic schemas. It ensures developers can efficiently validate API interactions, inspect payloads, and correlate errors with expected behaviors without relying solely on undocumented heuristics.

---

### **Key Concepts & Implementation Details**

#### **1. Core Principles**
REST troubleshooting follows a **layered debugging model**:
- **Client Layer** – Verify input/output (e.g., request formatting, headers, authentication).
- **Transport Layer** – Inspect HTTP status codes, latency, and protocol compliance.
- **Server Layer** – Validate backend responses, rate limits, and resource availability.
- **Infrastructure Layer** – Check load balancers, proxies, and firewall rules.

#### **2. Common REST Troubleshooting Scenarios**
| **Scenario**               | **Symptoms**                          | **Tools/Checks**                          |
|----------------------------|---------------------------------------|-------------------------------------------|
| **Authentication Errors**  | `401/403`                              | Verify API keys, JWT expiration, OAuth2 scopes. |
| **Payload Validation**     | `400 Bad Request`                      | Inspect schema mismatches (e.g., missing fields, type errors). |
| **Throttling**             | `429 Too Many Requests`               | Check rate limits (e.g., `X-RateLimit-Remaining`). |
| **Network Issues**         | Timeouts, intermittent failures       | Use `curl`/`Postman` with `-v`, `tcpdump`, and `ping`. |
| **Server-Side Crashes**    | `500/503`                              | Review server logs, GC pauses, or DB queries. |
| **CORS Errors**            | `403` with CORS headers               | Validate `Access-Control-Allow-Origin`.    |
| **Idempotency Violations** | Duplicate side effects (e.g., `POST` duplicates). | Test with `Idempotency-Key` headers. |

---

### **Schema Reference**
The following table outlines key REST troubleshooting schema elements for structured debugging.

| **Category**               | **Field**               | **Type**       | **Description**                                                                                     | **Example Values**                     |
|----------------------------|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| **HTTP Headers**           | `Content-Type`          | String         | Specifies media type (e.g., `application/json`).                                                     | `application/json; charset=utf-8`      |
|                            | `Authorization`         | String         | Bearer tokens, API keys, or OAuth2 credentials.                                                     | `Bearer <token>`                       |
|                            | `X-Request-ID`          | String         | Unique ID for tracing requests across services.                                                    | `req_12345abc`                         |
| **Response Fields**        | `status`                | Integer        | HTTP status code (e.g., `200`, `404`).                                                              | `400`                                  |
|                            | `error`                 | Object         | Standardized error payload (e.g., `{ "code": "INVALID_INPUT" }`).                                    | `{ "code": "429", "message": "Rate limit exceeded" }` |
|                            | `traceId`               | String         | Correlation ID for distributed tracing.                                                             | `trace_67890def`                       |
| **Validation**             | `requiredFields`        | Array          | List of mandatory fields in requests.                                                                | `[ "userId", "timestamp" ]`            |
| **Rate Limiting**          | `X-RateLimit-Limit`     | Integer        | Max allowed requests per interval.                                                                  | `100`                                  |
|                            | `X-RateLimit-Remaining` | Integer        | Remaining requests before throttling.                                                              | `42`                                   |
| **Logging Context**        | `requestId`             | String         | Client-assigned ID for log correlation.                                                              | `client_req_7890`                      |
|                            | `correlationId`         | String         | Server-assigned ID for internal tracing.                                                           | `server_trace_abc123`                  |

---

### **Query Examples**

#### **1. Debugging Authentication Issues**
**Problem:** `401 Unauthorized` when calling `/users/me`.
**Steps:**
1. Verify the `Authorization` header:
   ```http
   GET /users/me HTTP/1.1
   Host: api.example.com
   Authorization: Bearer <valid_token>
   ```
2. Check token validity:
   ```bash
   # Decode JWT (e.g., using https://jwt.io)
   echo "<token>" | base64 --decode | jq .
   ```
3. Inspect server logs for token rejection reasons.

#### **2. Validating Payload Structure**
**Problem:** `400 Bad Request` with no clear error message.
**Steps:**
- Compare incoming payload against schema (e.g., OpenAPI/Swagger):
  ```json
  // Expected schema for `/orders` POST
  {
    "required": ["customerId", "items"],
    "items": { "type": "array", "minItems": 1 }
  }
  ```
- Use `curl` with `--header "Content-Type: application/json"` and pipe a malformed payload:
  ```bash
  curl -X POST -H "Content-Type: application/json" \
       -d '{"missing": "customerId"}' \
       https://api.example.com/orders
  ```

#### **3. Tracing Requests Across Services**
**Problem:** Intermittent `500` errors from `/products`.
**Steps:**
1. Enable distributed tracing with `traceId`:
   ```http
   GET /products?traceId=client_123 HTTP/1.1
   ```
2. Correlate logs using:
   ```bash
   # Filter logs with traceId
   grep "traceId=client_123" /var/log/api/*.log
   ```
3. Use tools like **Jaeger** or **Zipkin** for visual tracing.

#### **4. Checking Rate Limiting**
**Problem:** `429 Too Many Requests`.
**Steps:**
1. Review response headers:
   ```http
   HTTP/1.1 429 Too Many Requests
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 0
   Retry-After: 60
   ```
2. Implement exponential backoff:
   ```javascript
   if (res.headers["x-ratelimit-remaining"] === "0") {
     const retryAfter = parseInt(res.headers["retry-after"]);
     await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
   }
   ```

#### **5. Validating Idempotency**
**Problem:** Duplicate charges after `POST /payments`.
**Steps:**
1. Add `Idempotency-Key` header:
   ```http
   POST /payments HTTP/1.1
   Idempotency-Key: abc123
   ```
2. Server should return `200` on retry with the same key and avoid duplicates.

---

### **Tools & Utilities**
| **Tool**               | **Purpose**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **curl**               | Send raw HTTP requests + debug headers.                                     | `curl -v -X POST -d '{"key":"value"}' https://api.example.com` |
| **Postman**            | GUI for REST debugging (inspectors, mock servers).                         | Open request → "Inspectors" tab → Headers   |
| **Fiddler/Wireshark**  | Capture and analyze HTTP traffic.                                           | Filter for `api.example.com`                |
| **PostgreSQL/Prometheus** | Query database or metrics for bottlenecks.                                | `SELECT * FROM transactions WHERE status = 'failed';` |
| **OpenAPI Validator**  | Validate API contracts and payloads.                                        | `swagger-cli validate openapi.yaml`         |
| **Jaeger**             | Distributed tracing for microservices.                                     | Deploy sidecar agents; query traces UI.     |

---

### **Logging Best Practices**
1. **Structured Logging**:
   Include `traceId`, `requestId`, and `correlationId` in every log entry.
   ```json
   {
     "level": "ERROR",
     "message": "Invalid payload",
     "traceId": "trace_67890",
     "requestId": "client_req_123",
     "payload": { "missing": "field" }
   }
   ```

2. **Error Tracking**:
   Use tools like **Sentry** or **Datadog** to aggregate errors with context.

3. **Rate Limiting Logs**:
   Log `X-RateLimit-*` headers when throttling occurs.

4. **Audit Trails**:
   Log sensitive operations (e.g., `/users/delete`) with timestamps and user context.

---

### **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[REST Error Handling](https://docs.example.com/rest-error-handling)** | Standardized error codes and response formats.                                   | Define consistent error responses for clients.    |
| **[API Gateway Patterns](https://docs.example.com/api-gateways)**        | Use gateways for routing, rate limiting, and request validation.              | Centralize API logic and security.              |
| **[Idempotency in REST](https://docs.example.com/idempotency)**            | Design safe, retriable operations.                                               | Handle duplicate requests (e.g., payments).      |
| **[OpenAPI/Swagger Validation](https://docs.example.com/openapi)**       | Document and validate API contracts.                                             | Ensure API consumers have accurate specs.         |
| **[Circuit Breaker](https://docs.example.com/circuit-breaker)**            | Prevent cascading failures in distributed systems.                              | Mitigate backend outages.                       |

---
**Last Updated:** `YYYY-MM-DD`
**Contributors:** `@author1`, `@author2`