# **[Pattern] API Troubleshooting Reference Guide**

---
### **Overview**
API troubleshooting is a structured approach to diagnosing and resolving issues in API interactions, covering authentication failures, rate limits, request/response errors, latency, and integration problems. This guide provides a systematic framework for identifying root causes—whether technical (e.g., malformed payloads, server-side errors) or operational (e.g., misconfigured endpoints, dependency issues)—and applying corrective actions. By leveraging structured logging, monitoring, and API-specific tools (e.g., Postman, OpenTelemetry), teams can minimize downtime and improve resilience. This guide outlines common failure scenarios, their causes, and diagnostic workflows, tailored for REST, GraphQL, and gRPC APIs.

---

---

## **1. Key Concepts**
### **1.1 API Failure Taxonomy**
| **Failure Type**       | **Description**                                                                 | **Common Causes**                                                                 |
|------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Authentication/Authorization** | Failed verification of identity/permissions.                                   | Expired tokens, invalid credentials, role mismatches.                           |
| **Syntactic Errors**   | Issues in request/response structure (e.g., malformed JSON, incorrect headers). | Missing required fields, schema mismatches, encoding errors.                     |
| **Semantic Errors**    | Logical inconsistencies (e.g., invalid data models, API version mismatches).    | Outdated SDKs, API version skew, business rule violations.                       |
| **Rate/Throttling**    | API quota or time-based restrictions exceeded.                                 | Unoptimized batching, lack of retry logic, DDoS attacks.                        |
| **Latency/Performance**| Slow responses or timeouts.                                                     | Cold starts, inefficient queries, network bottlenecks.                         |
| **Transport Errors**   | Network-level failures (e.g., TCP timeouts, TLS handshake failures).           | Unstable endpoints, proxy misconfigurations, firewall rules.                    |
| **Server-Side Errors** | Backend failures (e.g., database locks, unhandled exceptions).                | Poorly written business logic, unscaled infrastructure, dependency failures.    |
| **Third-Party Dependencies** | Failures in linked services (e.g., payment gateways, CDNs).                   | Service outages, API key revocations, version incompatibilities.                 |

---
### **1.2 Troubleshooting Workflow**
1. **Reproduce Issue**: Confirm the problem (e.g., 5xx errors, timeouts).
2. **Isolate Scope**: Check if the issue is client-side (e.g., request format) or server-side (e.g., logs).
3. **Gather Evidence**:
   - Client logs: Request/response headers, payloads, timestamps.
   - Server logs: Error stacks, throttling metrics, dependency call traces.
   - Monitoring: APM tools (e.g., Datadog, New Relic) or cloud traces (AWS X-Ray).
4. **Hypothesize**: Narrow down potential causes (e.g., "Is the rate limit hit?").
5. **Validate**: Test fixes (e.g., retry with smaller payloads) and monitor resolution.
6. **Document**: Update runbooks or knowledge bases for future incidents.

---

## **2. Schema Reference**
Below are standardized schemas for diagnostic payloads and error responses.

### **2.1 Common Error Response Schema**
```json
{
  "error": {
    "code": "400",
    "type": "BadRequest",
    "message": "Invalid payload: Missing 'userId' field",
    "details": [
      {
        "field": "userId",
        "expectedType": "string",
        "received": null
      }
    ],
    "timestamp": "2023-10-15T14:30:22Z"
  }
}
```

| **Field**      | **Type**   | **Description**                                                                 | **Example Values**                  |
|----------------|------------|---------------------------------------------------------------------------------|--------------------------------------|
| `code`         | Integer    | HTTP status code (e.g., `401`, `503`).                                        | `403`, `429`                        |
| `type`         | String     | Error category (e.g., `AuthenticationError`, `ThrottlingError`).                | `RateLimitExceeded`                 |
| `message`      | String     | Human-readable summary.                                                        | `"Quota exceeded"`                   |
| `details`      | Array      | Structured breakdown of causes.                                                | See below                           |
| `timestamp`    | ISO8601    | When the error occurred.                                                       | `"2023-10-15T14:30:22Z"`            |

**Nested `details` Schema**:
```json
{
  "field": "string",
  "expected": "string|number|boolean",
  "received": "string|number|boolean",
  "constraint": "string"  // e.g., "minLength: 5"
}
```

---

### **2.2 Request Validation Schema**
| **Field**            | **Type**   | **Description**                                                                 | **Example**                          |
|----------------------|------------|---------------------------------------------------------------------------------|--------------------------------------|
| `operation`          | String     | API method (e.g., `POST /users`).                                              | `POST /api/v1/users`                 |
| `headers`            | Object     | Request headers with keys/values.                                              | `{"Authorization": "Bearer xyz"}`    |
| `body`               | Object     | Request payload (parsed).                                                      | `{ "name": "Alice", "age": 30 }`     |
| `queryParams`        | Object     | URL query parameters.                                                          | `{"limit": "10", "offset": "0"}`     |
| `clientIP`           | String     | Source IP (for throttling analysis).                                          | `"192.168.1.1"`                      |
| `userAgent`          | String     | Client identifier.                                                              | `"PostmanRuntime/7.30.0"`            |

---

## **3. Query Examples**
### **3.1 Debugging Authentication Failures**
**Problem**: `401 Unauthorized` for `/api/v1/orders`.
**Diagnostic Steps**:

1. **Inspect Headers**:
   ```bash
   curl -v -X GET "https://api.example.com/api/v1/orders" \
        -H "Authorization: Bearer invalid_token_123"
   ```
   - Look for `401` in response + `WWW-Authenticate: Bearer realm="..."` header.

2. **Validate Token**:
   ```bash
   # Decode JWT (if applicable) to check expiry/claims
   echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | base64 --decode | jq
   ```

3. **Check Server Logs**:
   ```log
   [2023-10-15 14:30:22] ERROR: Authentication failed for user=unknown, token=eyJ...
   ```

---

### **3.2 Handling Rate Limits**
**Problem**: `429 Too Many Requests` for `/api/v1/search`.
**Diagnostic Steps**:

1. **Review Headers**:
   ```bash
   curl -v -X GET "https://api.example.com/api/v1/search" | grep -i "rate-limit"
   ```
   - Expected: `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 0`.

2. **Adjust Client Retry Logic**:
   ```python
   # Use exponential backoff
   def call_api_with_retry(url, max_retries=3):
       retry_count = 0
       while retry_count < max_retries:
           response = requests.get(url)
           if response.status_code == 429:
               sleep(2 ** retry_count)  # Exponential delay
               retry_count += 1
           else:
               break
   ```

3. **Monitor Usage**:
   ```bash
   # Check API gateway metrics (e.g., Cloudflare, AWS API Gateway)
   kubectl get --raw "/metrics" | grep -i "rate_limit"
   ```

---

### **3.3 Resolving Timeout Errors**
**Problem**: `504 Gateway Timeout` for `/api/v1/orders/{id}`.
**Diagnostic Steps**:

1. **Check Server-Side Timeouts**:
   ```yaml
   # Example: Configure timeout in FastAPI (Python)
   @app.post("/orders")
   async def create_order(order: dict):
       await asyncio.wait_for(some_operation(), timeout=10)  # 10s max
   ```

2. **Increase Client Timeout**:
   ```javascript
   // Example: Node.js with Axios
   axios.get('https://api.example.com/orders/123', {
     timeout: 15000  // 15s
   });
   ```

3. **Trace Dependency Calls**:
   ```bash
   # Use OpenTelemetry to trace slow DB calls
   otel-collector --config-file=otel-config.yaml
   ```

---

## **4. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **When to Use**                                      |
|--------------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------|
| **[Resilient API Design]**           | Build APIs to handle failures gracefully (retries, circuit breakers).           | When designing new APIs or refactoring existing ones. |
| **[API Versioning]**                 | Manage breaking changes without disrupting clients.                             | When introducing schema changes or deprecations.     |
| **[Observability-Driven Development]**| Integrate logging, metrics, and tracing for proactive debugging.                | For production APIs requiring SLOs/SLIs.             |
| **[Rate Limiting Strategies]**        | Implement throttling to prevent abuse (token bucket, leaky bucket).            | When scaling APIs to high-traffic users.             |
| **[Idempotency Keys]**               | Ensure safe retries for side-effect operations (e.g., payments).               | For APIs with `POST/PATCH` that modify state.        |

---

## **5. Tools & Libraries**
| **Category**          | **Tools**                                                                       | **Use Case**                                      |
|-----------------------|-------------------------------------------------------------------------------|----------------------------------------------------|
| **Debugging**         | Postman, Insomnia, cURL                                                          | Manually test API endpoints.                      |
| **Monitoring**        | Datadog, New Relic, Prometheus/Grafana                                          | Track errors, latency, and dependency health.      |
| **Tracing**           | OpenTelemetry, AWS X-Ray, Jaeger                                                 | Trace requests across microservices.                |
| **Logging**           | ELK Stack (Elasticsearch, Logstash, Kibana), Loki                                | Aggregate and analyze logs at scale.              |
| **Validation**        | JSON Schema (Draft 7), AsyncAPI, FastAPI OpenAPI                                | Validate request/response schemas.                |
| **Retry Logic**       | Polly (AWS), Resilient Java Client, Axios Retry                                | Implement resilient clients.                      |

---

## **6. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------|
| **Ignoring Client-Side Errors**       | Always check request payloads and headers for syntax/validation issues.        |
| **Silent Failures**                   | Use `5xx` responses for server errors; log client errors with stack traces.    |
| **No Circuit Breaker**                | Implement retries with exponential backoff (e.g., Hystrix, Resilience4j).     |
| **Static Error Messages**             | Provide actionable details (e.g., `429: Retry-After: Sun, 31 Dec 2023 23:59:59 GMT`). |
| **Overlooking Dependencies**          | Trace external API calls (e.g., payment gateways) with distributed tracing.    |

---
### **Next Steps**
- **For Developers**: Use SDKs with built-in retries (e.g., `axios-retry`, `requests-retry`).
- **For Ops**: Set up alerts for `5xx` errors and rate limit breaches.
- **For Architects**: Design APIs with backward-compatible versions and clear deprecation policies.