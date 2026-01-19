# **[Pattern] REST Troubleshooting – Reference Guide**

---

## **Overview**
Troubleshooting REST APIs requires a structured approach to identify issues in **requests, responses, authentication, performance, and infrastructure**. This guide outlines best practices, common error scenarios, and diagnostic steps to resolve REST API failures efficiently. Coverage includes **client-side issues, server-side errors, network problems, and API misconfigurations** (e.g., rate limits, CORS, authentication failures).

Key focus areas:
- **HTTP status codes** and response parsing
- **Log analysis** and debugging tools
- **Testing frameworks** (Postman, cURL, Swagger)
- **Common pitfalls** (IDL mismatches, caching issues, payload validation errors)
- **Monitoring and observability** techniques

This guide assumes familiarity with core REST principles (statelessness, resource endpoints) and basic HTTP methods.

---

## **Implementation Details**

### **1. Common Troubleshooting Scenarios**
API issues typically fall into these categories:

| **Category**            | **Example Problems**                                                                 |
|-------------------------|------------------------------------------------------------------------------------|
| **Client-Side Issues**  | Incorrect headers, malformed payloads, expired tokens, invalid URL encoding       |
| **Server-Side Errors**  | Backend crashes, database timeouts, misconfigured endpoints                      |
| **Network Problems**    | Latency, DNS resolution failures, proxy misconfigurations                         |
| **Security Issues**     | Missing authentication, CSRF attacks, CORS misconfigurations                       |
| **Performance**         | Slow responses, throttling (429 errors), unoptimized queries                       |
| **Data Issues**         | Schema mismatches, null values in required fields, pagination errors              |

---

### **2. Diagnostic Workflow**
Follow this structured approach to isolate issues:

1. **Replicate the Problem** – Confirm the error occurs consistently.
2. **Inspect Requests/Responses** – Use tools like **Postman, cURL, or browser DevTools**.
3. **Validate Headers** – Ensure `Content-Type`, `Authorization`, and `Accept` headers are correct.
4. **Check Logs** – Review server-side logs (e.g., `nginx`, `Spring Boot`, or `AWS CloudTrail`).
5. **Test with Minimal Payload** – Rule out payload-related issues.
6. **Compare Working vs. Broken Requests** – Identify subtle differences.
7. **Verify Rate Limits** – Check for `429 Too Many Requests`.
8. **Test with Different Tools** – Confirm if the issue is tool-specific (e.g., Postman vs. `curl`).

---

### **3. Key Troubleshooting Tools**
| **Tool**               | **Purpose**                                                                                     | **Example Use Case**                              |
|------------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **Postman**            | Send requests, inspect headers, save collections, and test APIs interactively.              | Debugging OAuth 2.0 token exchanges              |
| **cURL**               | Command-line tool for HTTP requests (lightweight, scriptable).                                | Testing API with specific headers/body           |
| **Swagger/OpenAPI**    | Validate API contracts, test endpoints with interactive UI.                                   | Verifying schema compatibility                  |
| **Wireshark/tcpdump**  | Network-level packet inspection (for latency/connection issues).                            | Detecting packet loss or DNS resolution errors   |
| **K6/Locust**          | Load testing to identify bottlenecks.                                                          | Simulating high traffic to find rate limits      |
| **AWS X-Ray / Jaeger** | Distributed tracing for microservices.                                                       | Tracing requests across multiple services        |
| **New Relic/Datadog**  | Monitoring API performance, error rates, and latency.                                        | Alerting on spike in 5xx errors                  |

---

## **Schema Reference**

### **REST API Error Response Schema**
Most REST APIs follow a standardized error format. Below are common schemas (adjust fields as needed):

| **Field**          | **Type**   | **Description**                                                                 | **Example**                     |
|--------------------|------------|-------------------------------------------------------------------------------|---------------------------------|
| `error`            | String     | Human-readable error message (avoid exposing sensitive details).              | `"Invalid token expiration"`    |
| `status`           | Integer    | HTTP status code (e.g., `400`, `500`).                                          | `401`                           |
| `code`             | String     | Machine-readable error identifier (e.g., `auth.401`, `validation.422`).        | `"authentication_required"`     |
| `timestamp`        | ISO 8601   | When the error occurred (useful for logs).                                     | `"2024-05-20T14:30:00Z"`        |
| `path`             | String     | The API endpoint where the error occurred.                                      | `"/users/delete"`               |
| `details`          | Object     | Additional context (e.g., missing fields, validation errors).                   | `{ "field": ["must be a number"] }`|
| `requestId`        | String     | Unique identifier for tracing (correlate with server logs).                     | `"req_abc123xyz"`               |

**Example Response:**
```json
{
  "error": "Unauthorized",
  "status": 401,
  "code": "auth.401",
  "timestamp": "2024-05-20T14:30:00Z",
  "path": "/api/v1/users/me",
  "details": { "message": "Token expired" },
  "requestId": "req_xyz789"
}
```

---

### **Common HTTP Status Code Troubleshooting**
| **Status Code** | **Category**       | **Possible Causes**                                                                 | **Action Items**                                  |
|------------------|--------------------|------------------------------------------------------------------------------------|--------------------------------------------------|
| **200 OK**       | Success            | Request processed.                                                                 | None                                              |
| **201 Created**  | Success            | Resource created (check `Location` header for ID).                                   | Verify resource exists via GET                   |
| **400 Bad Request** | Client Error     | Malformed request (e.g., invalid JSON, missing headers).                              | Validate payload with Swagger/OpenAPI             |
| **401 Unauthorized** | Client Error   | Missing/invalid authentication (e.g., token expired).                                | Check `Authorization` header                     |
| **403 Forbidden** | Client Error      | Authenticated but lack permissions.                                                  | Review RBAC policies                              |
| **404 Not Found** | Client Error      | Endpoint does not exist.                                                              | Verify URL and check API docs                    |
| **405 Method Not Allowed** | Client Error | Incorrect HTTP method (e.g., `PUT` on a `GET`-only endpoint).                      | Use correct verb (check Swagger docs)           |
| **408 Request Timeout** | Client Error | Server took too long to respond.                                                     | Increase timeout or optimize backend             |
| **409 Conflict**  | Client Error       | Duplicate resource or pre-condition failed (e.g., `ETag` mismatch).                  | Check for idempotency keys                       |
| **422 Unprocessable Entity** | Client Error | Valid request but payload fails validation (e.g., missing required field).         | Review `details` field in response               |
| **429 Too Many Requests** | Client Error | Rate limit exceeded.                                                               | Implement exponential backoff                    |
| **500 Internal Server Error** | Server Error | Backend crash (generic; check logs).                                               | Review server logs for stack traces              |
| **502 Bad Gateway** | Server Error     | Upstream service failed (e.g., database).                                            | Check dependent service health                   |
| **503 Service Unavailable** | Server Error | Server overloaded or down.                                                          | Monitor capacity; restart services if needed      |
| **504 Gateway Timeout** | Server Error   | Proxy/gateway timed out waiting for response.                                        | Increase timeout settings                        |

---

## **Query Examples**

### **1. Testing a Failed Request in cURL**
```bash
# Failed request (missing Authorization header)
curl -X POST http://api.example.com/v1/users \
     -H "Content-Type: application/json" \
     -d '{"name": "Test User", "email": "test@example.com"}'

# Expected response:
# {"error": "Unauthorized", "status": 401, ...}

# Fixed request (with token)
curl -X POST http://api.example.com/v1/users \
     -H "Authorization: Bearer valid_token_123" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test User", "email": "test@example.com"}'
```

---

### **2. Debugging a 429 Error (Rate Limiting)**
```bash
# Check headers for rate limit details
curl -I http://api.example.com/v1/items

# Response Headers:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 0
# X-RateLimit-Reset: 60

# Implement backoff (Python example):
import time
import requests

response = requests.get("http://api.example.com/v1/items")
while response.status_code == 429:
    reset_time = int(response.headers.get("X-RateLimit-Reset"))
    wait_time = max(reset_time - time.time(), 0) + 5  # Add buffer
    print(f"Rate limited. Retrying in {wait_time:.1f}s...")
    time.sleep(wait_time)
    response = requests.get("http://api.example.com/v1/items")
```

---

### **3. Validating a JSON Payload with Swagger**
1. Open the **Swagger UI** for the API (e.g., `http://api.example.com/swagger`).
2. Select the endpoint (e.g., `POST /users`).
3. Fill in the request body and click **Try it out**.
4. Swagger will:
   - Validate the schema.
   - Generate `cURL` or code snippets.
   - Show errors if the payload is invalid (e.g., wrong `email` format).

---
### **4. Checking Server Logs for 500 Errors**
```bash
# Example log entry for a 500 error (Spring Boot):
2024-05-20 14:30:10.123 ERROR 1 --- [nio-8080-exec-1] com.example.controller.UserController : 500 Internal Server Error for HTTP POST "/users/delete"

# Key details to extract:
- **Timestamp**: When the error occurred.
- **Thread**: Identify if it’s stuck in a long-running task.
- **Stack Trace**: Points to the root cause (e.g., `NullPointerException` in `UserRepository.save()`).
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Idempotency Key](pattern.md)** | Ensure safe retries by using unique IDs for requests (e.g., `Idempotency-Key` header).                                             | Handling duplicate requests or rate-limited retries.                          |
| **[Retries & Backoff](pattern.md)** | Implement exponential backoff for transient failures (e.g., 5xx errors).                                                       | Improving resilience in distributed systems.                                  |
| **[Circuit Breaker](pattern.md)** | Stop cascading failures by temporarily blocking requests to a failing service.                                                     | High-latency or unstable backend services.                                   |
| **[API Gateway](pattern.md)** | Centralize routing, authentication, and request validation.                                                                        | Managing microservices or complex auth flows.                                 |
| **[Versioning](pattern.md)** | Mitigate breaking changes with URL/path versioning (e.g., `/v1/users`).                                                       | Maintaining backward compatibility during API updates.                       |
| **[Observability](pattern.md)** | Collect logs, metrics, and traces for real-time debugging.                                                                        | Proactively detecting and diagnosing issues.                                  |
| **[Authentication](pattern.md)** | Secure APIs with OAuth 2.0, JWT, or API keys.                                                                                     | Protecting endpoints from unauthorized access.                               |
| **[Pagination](pattern.md)** | Handle large datasets with `offset`, `limit`, or cursor-based pagination.                                                     | Avoiding timeouts and improving performance for large collections.          |

---

## **Best Practices**
1. **Standardize Error Responses** – Use the schema above to ensure consistency across teams.
2. **Log Request/Response Pairs** – Correlate client and server logs with `requestId`.
3. **Monitor Key Metrics** – Track:
   - Error rates (`5xx` responses).
   - Latency percentiles (p50, p99).
   - Rate limit hits (`429` errors).
4. **Test Edge Cases** – Validate:
   - Empty/malformed payloads.
   - Race conditions (e.g., concurrent updates).
   - Offline scenarios (network partition handling).
5. **Use Feature Flags** – Disable problematic endpoints without deploying code.
6. **Document Breaking Changes** – Clearly communicate API version updates.

---

## **Glossary**
| **Term**               | **Definition**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|
| **Idempotency**        | Repeating the same request has the same effect as sending it once (e.g., `GET`, safe `POST`).  |
| **Retry Token**        | A temporary token allowing a client to retry a failed request after a timeout.                  |
| **Gateway Timeout**    | When a proxy/gateway waits too long for a response from a backend service.                     |
| **CORS (Cross-Origin)**| Restriction on sending requests from one domain to another (configured via `Access-Control-Allow-Origin`). |
| **Throttling**         | Limiting API requests per client/IP to prevent abuse (e.g., `429` errors).                     |
| **Distributed Tracing**| Tracking a request as it traverses multiple services (e.g., using Jaeger or AWS X-Ray).       |

---
**End of Reference Guide.** For further reading, see the [REST API Design Patterns](pattern-collection.md) collection.