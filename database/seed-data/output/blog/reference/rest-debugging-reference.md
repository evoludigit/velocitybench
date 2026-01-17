# **[Pattern] REST Debugging Reference Guide**

## **Overview**
REST debugging is a structured approach to troubleshooting API issues by systematically analyzing HTTP requests, responses, and backend behavior. This guide covers key debugging techniques, schema validation, common query patterns, and tools to resolve latency, errors, and inconsistencies in RESTful services. Debugging follows a **3-phase workflow**:
1. **Inspect** (validate requests/response structure, logs, and metadata).
2. **Compare** (demonstrate differences between expected vs. actual behavior).
3. **Isolate** (narrow down root causes using tools like request replay, rate limiting, and schema diffing).

---
## **Key Concepts & Implementation Details**

### **1. Core Debugging Phases**
| **Phase**       | **Purpose**                                                                 | **Tools/Methods**                                                                 |
|------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Inspect**      | Validate API structure, check headers, payloads, and logs.                   | Postman, cURL, browser DevTools, server-side logs.                               |
| **Compare**      | Spot discrepancies between expected and actual responses.                   | Schema validation (OpenAPI/Swagger), request/response diffing, A/B testing.     |
| **Isolate**      | Identify bottlenecks (e.g., slow dependencies, rate limits).               | Tracer tools (Jaeger), performance profiling, dependency injection mocks.       |

### **2. Common Debugging Scenarios**
| **Scenario**            | **Debugging Focus**                                                                 | **Checklist**                                                                     |
|-------------------------|-------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **4xx/5xx Errors**      | Incorrect payloads, missing headers, or server-side logic failures.                 | Validate status codes, error messages, and logs.                                  |
| **Latency Issues**      | Slow responses due to external dependencies, timeouts, or inefficient queries.       | Use `curl -v` to inspect network delays; check server-side metrics.                |
| **Data Inconsistencies**| Mismatched responses between clients (e.g., mobile vs. web).                     | Replay requests with identical headers/params; compare raw responses.             |
| **Authentication Failures** | Invalid tokens, expired sessions, or incorrect scopes.                          | Verify JWT payload, refresh tokens, and RBAC rules.                                |

### **3. REST Debugging Workflow**
1. **Reproduce the Issue**
   - Capture the failing request (e.g., `curl -X GET -H "token: XYZ" ...`).
   - Log headers/body (`curl -v` for detailed output).
2. **Validate Schema**
   - Compare response against OpenAPI/Swagger schema.
   - Use tools like [Swagger Editor](https://editor.swagger.io/) or Postman.
3. **Analyze Logs**
   - Check backend logs (e.g., Spring Boot Actuator, AWS CloudTrail).
   - Correlate timestamps with request IDs.
4. **Replay & Compare**
   - Simulate identical requests (Postman’s "Run Collection").
   - Use `jq` to filter JSON responses (e.g., `jq '.data.id'`).
5. **Isolate Root Cause**
   - Test edge cases (e.g., malformed input, race conditions).
   - Mock dependencies (e.g., `wiremock` for external APIs).

---
## **Schema Reference**
Below are common REST API schemas used for debugging. Use these to validate request/response structures.

| **Schema Type**       | **Description**                                                                 | **Example (OpenAPI 3.0)**                                                                 |
|-----------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Request Body**      | Validates input payloads (e.g., `POST /users`).                               | `{ "name": "string", "email": "string", "role": ["user", "admin"] }`                  |
| **Response Body**     | Ensures consistent output (e.g., `GET /users/{id}`).                         | `{ "data": { "id": 42, "name": "Alice" }, "status": "success" }`                      |
| **Query Parameters**  | Validates `?key=value` syntax.                                                | `?limit=10&offset=0` (numeric constraints).                                             |
| **Headers**           | Checks for required headers (e.g., `Authorization`, `Content-Type`).          | `Accept: application/json`, `X-API-Key: abc123`.                                       |
| **Error Responses**   | Standardized error formats (RFC 7807).                                        | `{ "error": { "type": "InvalidRequest", "title": "Bad Input" } }`                     |

---
## **Query Examples**
### **1. Basic GET Request Debugging**
```bash
curl -v -X GET https://api.example.com/users/1 \
  -H "Authorization: Bearer abc123" \
  -H "Accept: application/json"
```
**Debugging Steps:**
- Check `-v` output for HTTP headers/response status.
- Use `jq` to inspect JSON:
  ```bash
  curl ... | jq '.data.role'
  ```

### **2. POST Request with JSON Payload**
```bash
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob", "email":"bob@example.com"}'
```
**Debugging Tips:**
- Use **Postman** to visualize the request/response flow.
- Validate schema with [JSON Schema Validator](https://www.jsonschemalint.com/).

### **3. Debugging Rate Limits**
```bash
# Simulate 100 requests in 1 second
for i in {1..100}; do curl -s https://api.example.com/users; done
```
**Expected Behavior:**
- Server should return `429 Too Many Requests`.
- Check `Retry-After` header for recovery time.

### **4. Testing CORS Issues**
```bash
curl -X GET https://api.example.com/users \
  -H "Origin: https://myapp.com" \
  -H "Access-Control-Request-Method: GET"
```
**Debugging:**
- Verify `Access-Control-Allow-Origin` in response headers.
- Use browser DevTools → **Network** tab to inspect CORS errors.

---
## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                 | **Link**                                                                         |
|------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Postman**            | API testing, request replay, collection runner.                             | [postman.com](https://www.postman.com/)                                        |
| **cURL**               | Low-level HTTP debugging.                                                   | [curl.se](https://curl.se/)                                                     |
| **Swagger Editor**     | Validate OpenAPI schemas.                                                   | [editor.swagger.io](https://editor.swagger.io/)                                  |
| **Jaeger**             | Distributed tracing for latency analysis.                                   | [jaegertracing.io](https://jaegertracing.io/)                                  |
| **WireMock**           | Mock external APIs for isolated testing.                                    | [wiremock.org](https://wiremock.org/)                                          |
| **jq**                 | Filter JSON responses in CLI.                                               | [stedolan.github.io/jq/](https://stedolan.github.io/jq/)                        |
| **PostgreSQL `pgBadger`** | Analyze SQL query performance in logs.                                     | [dba.stackexchange.com](https://dba.stackexchange.com/questions/126123/) (community) |

---
## **Best Practices**
1. **Standardize Logging**
   - Include `requestId`, `timestamp`, and `userAgent` in logs.
   - Example:
     ```json
     { "requestId": "abc123", "status": 400, "error": "Missing field 'name'" }
     ```
2. **Use Unique Request IDs**
   - Correlate frontend logs with backend logs via `X-Request-ID`.
3. **Version Your APIs**
   - Example: `GET /v2/users` vs. `GET /users` to avoid breaking changes.
4. **Implement Circuit Breakers**
   - Use tools like **Resilience4j** to handle cascading failures.
5. **Document Debugging Flows**
   - Add a `/debug` endpoint for internal tools (e.g., `GET /debug/health`).

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                   |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **[API Gateway Debugging]** | Centralize logging/proxy for distributed APIs.                                | Multi-service architectures (e.g., AWS ALB, Kong).                               |
| **[Schema Validation]**   | Enforce request/response contracts (JSON Schema, GraphQL).                   | Prevent malformed data before processing.                                         |
| **[Rate Limiting]**       | Control request volume (e.g., token bucket, fixed window).                  | Prevent abuse (e.g., Slurm, Redis).                                              |
| **[Retry with Backoff]**  | Exponential backoff for transient failures (e.g., 5xx errors).               | Resilient clients (e.g., Axios retry, Spring Retry).                             |
| **[Caching Strategies]**  | Reduce latency with CDN or in-memory caches (e.g., Redis).                  | Frequently accessed static data.                                                 |

---
## **Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Idempotency Key**    | Ensures duplicate requests produce the same outcome (e.g., `X-Idempotency-Key`). |
| **HATEOAS**            | Hypermedia controls in responses (e.g., `links` field for discoverable actions). |
| **OpenAPI 3.0**        | Standard for REST API documentation (replaces Swagger).                        |
| **gRPC**               | High-performance RPC alternative to REST (uses Protocol Buffers).            |
| **E2E Testing**        | Validates full request-response flows (e.g., Jest, Cypress).                  |

---
## **Troubleshooting Checklist**
1. **Client-Side Issues**
   - Check network connectivity (ping, `curl -v`).
   - Verify CORS headers if using browsers.
2. **Server-Side Issues**
   - Review backend logs for `NullPointerException`, `SQLException`.
   - Test with `curl` to rule out client-side bugs.
3. **Network Issues**
   - Firewall rules blocking requests?
   - DNS resolution problems?
4. **Data Corruption**
   - Mismatched schemas? Use `jq` to compare responses.
5. **Permissions**
   - Invalid tokens? Check `Authorization` header and RBAC policies.

---
## **Further Reading**
- [REST API Debugging Blog](https://www.postman.com/guides/rest-api-debugging/)
- [O’Reilly: REST API Testing](https://www.oreilly.com/library/view/rest-api-testing/9781492037152/)
- [Postman University: Debugging 101](https://learning.postman.com/docs/sending-requests/debugging-requests/)