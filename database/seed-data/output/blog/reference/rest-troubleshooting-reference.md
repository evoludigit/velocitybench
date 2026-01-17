# **[Pattern] REST Troubleshooting: Reference Guide**

---

## **Overview**
This guide provides a structured approach to **diagnosing, logging, and resolving issues** in RESTful APIs. Common problems (e.g., authentication failures, rate limits, malformed requests) often stem from misconfigurations, network issues, or client-server mismatches. This pattern focuses on systematic troubleshooting by categorizing problems (authentication, performance, errors), outlining diagnostic steps, and suggesting fixes.

Key activities:
- **Logging & Monitoring** – Capture client/server logs and metrics.
- **Validation** – Ensure requests/responses match OpenAPI/Swagger specs.
- **Network Checks** – Test latency, CORS, and proxy interferences.
- **Tooling** – Use Postman, cURL, or browser DevTools for debugging.

For advanced troubleshooting, consult **gRPC Troubleshooting** or **GraphQL Error Handling** patterns.

---

## **Schema Reference**
Below are key troubleshooting categories along with their **data fields, valid values, and actions**.

| **Category**          | **Field**               | **Description**                                                                 | **Valid Values/Notes**                                                                 | **Action**                                  |
|-----------------------|-------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------|
| **Authentication**    | `status_code`           | HTTP error code (e.g., 401, 403)                                            | `4xx`, `5xx`, or custom (e.g., `401-Unauthorized`)                                   | Check credentials, tokens, or IAM policies. |
|                       | `error_type`            | Authentication error type (e.g., `invalid_token`, `expired_session`)        | `invalid_token`, `missing_credentials`, `rate_limited`                                   | Regenerate tokens; adjust quotas.           |
|                       | `timestamp`             | When the error occurred (ISO 8601)                                           | `YYYY-MM-DDTHH:MM:SSZ`                                                               | Filter logs by time.                        |
| **Validation**        | `invalid_field`         | Field causing failure (e.g., `email`, `password`)                            | API response schema fields                                                            | Correct input format or add `required` tags.  |
|                       | `request_body`          | Raw request payload (if applicable)                                         | JSON/Payload strings                                                                   | Validate against OpenAPI schema.            |
| **Performance**       | `latency_ms`            | Response time (end-to-end)                                                  | Integer value (e.g., `300`)                                                            | Optimize backend or use caching.            |
|                       | `backoff_retry`         | Whether retries were throttled                                             | `true`/`false` or `max_retries: 3`                                                    | Adjust retry policies in client code.       |
| **Network**           | `proxy_host`            | Proxy server in the chain                                                | IP/hostname (e.g., `corporate-gateway.example.com`)                                   | Check proxy logs for dropped requests.      |
|                       | `cors_origin`           | Blocked CORS request origin                                                 | Whitelisted domains                                                                   | Update CORS headers in server config.       |
| **General Errors**    | `error_message`         | Human-readable error description                                           | String (e.g., `"Invalid JSON"`, `"Database connectivity failed"`)                     | Fix client code or server-side issues.       |
|                       | `stack_trace`           | Server-side error trace (if available)                                      | Stack trace logs                                                                       | Review server logs for root cause.           |

---

## **Query Examples**
### **1. Authenticaion Failure**
**Scenario:** API returns `401-Unauthorized` with `invalid_token` in `error_type`.

**Steps:**
1. **Check Logs:**
   ```bash
   # Server-side log query (example for AWS CloudWatch)
   grep "Unauthorized" /var/log/api_gateway.log | sort -r | head -5
   ```
2. **Validate Token:**
   ```bash
   # Decode JWT token in cURL
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://jwt.io/ | jq .payload
   ```
3. **Fix:**
   - Rotate expired tokens.
   - Update `access_token` in client code.

**Expected Output:**
```json
{
  "error_type": "expired_session",
  "status_code": 401,
  "timestamp": "2024-05-20T14:30:00Z"
}
```

---

### **2. Payload Validation Error**
**Scenario:** Client sends malformed JSON; API returns `400 Bad Request`.

**Steps:**
1. **Inspect Request:**
   ```bash
   # Use Postman to validate request
   POST /users HTTP/1.1
   Content-Type: application/json

   {
     "name": "John Doe",  # Missing "email" field
     "age": 30
   }
   ```
2. **Check OpenAPI Schema:**
   ```yaml
   # Example from schema.json
   required:
     - name
     - email
   ```
3. **Fix:**
   - Add `email` to payload.
   - Update client-side validation.

**Expected Fix:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "age": 30
}
```

---

### **3. Performance Bottleneck**
**Scenario:** API response takes >1s; `latency_ms` exceeds SLO.

**Steps:**
1. **Profile Request:**
   ```bash
   # Use k6 to benchmark
   import http from 'k6/http';
   export const params = {
     url: 'https://api.example.com/users',
     latency_threshold: 1000  // 1 second
   };
   ```
2. **Check Server Metrics:**
   ```bash
   # Prometheus query for slow endpoints
   histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
   ```
3. **Fix:**
   - Add caching (Redis).
   - Optimize slow queries (e.g., add indexes).

**Expected Result:**
```json
{
  "latency_ms": 1500,
  "backoff_retry": false,
  "recommendation": "Enable Redis caching"
}
```

---

### **4. Network Issues**
**Scenario:** CORS preflight fails; browser blocks request.

**Steps:**
1. **Verify Headers:**
   ```bash
   # Check CORS headers in server response
   curl -I https://api.example.com/users
   ```
   **Expected Headers:**
   ```
   Access-Control-Allow-Origin: https://client.example.com
   Access-Control-Allow-Methods: GET, POST
   ```
2. **Test Proxy:**
   ```bash
   # Trace request via proxy
   curl -x http://proxy.example.com:8080 -v https://api.example.com/users
   ```
3. **Fix:**
   - Update server CORS config.
   - Whitelist client domains.

**Expected Fix:**
```bash
# Flask (Python) example
@app.after_request
def cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://client.example.com'
    return response
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[gRPC Troubleshooting]** | Debugging gRPC-specific issues like connection errors or serialization.       | If using gRPC instead of REST.                    |
| **[GraphQL Error Handling]** | Resolving GraphQL query errors (e.g., malformed queries, N+1 problems).    | For GraphQL APIs.                                |
| **[Rate Limiting]**        | Managing/mitigating API throttling issues.                                   | When hits exceed quota.                          |
| **[API Gateway Logging]**  | Centralized logging for API gateways (AWS ALB, Kong).                       | For distributed microservices.                   |
| **[Client-Side Validation]** | Preemptive validation to avoid server errors.                                  | Before sending requests.                          |

---
**See Also:**
- [OpenAPI Specification](https://swagger.io/specification/) – Validate schemas.
- [Postman Debugging Guides](https://learning.postman.com/docs/debugging-requests/) – Test APIs interactively.