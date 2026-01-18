# **[Pattern] API Troubleshooting: Reference Guide**

---

## **Overview**
This guide provides a structured methodology for diagnosing and resolving common API-related issues. API troubleshooting involves systematically identifying, reproducing, analyzing, and resolving errors (e.g., 4xx/5xx responses, timeouts, rate limits, or integration failures) to restore system functionality. Best practices include logging, validation checks, and tiered debugging (client → network → server → dependencies).

---
## **1. Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                                                                           |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Latency**            | Delay between request initiation and response receipt (e.g., due to network hops, server processing).                                                                                                                                         |
| **Error Response Codes** | HTTP codes indicating failure types (e.g., `401 Unauthorized`, `503 Service Unavailable`).                                                                                                                                                     |
| **Rate Limiting**      | API throttling to prevent abuse (e.g., `429 Too Many Requests`).                                                                                                                                                                                 |
| **Dependency Failure** | Failure in a linked service (e.g., database, third-party service).                                                                                                                                                                                 |
| **Logging**            | Recording request/response data for post-analysis.                                                                                                                                                                                             |
| **Retry Mechanism**    | Automatic re-attempts for transient errors (common in HTTP `429` or `503`).                                                                                                                                                                   |
| **Payload Validation** | Ensuring request/response schemas match expected formats (e.g., JSON schema).                                                                                                                                                                     |

---

## **2. Implementation Details**
### **A. Step-by-Step Troubleshooting Workflow**
1. **Reproduce the Issue**
   - Confirm (manually or programmatically) if the problem occurs consistently.
   - Isolate variables: Test with different clients (Postman, browser, app) or environments (dev/stage/prod).

2. **Check Logs and Metrics**
   - **Client-Side Logs**: Verify payload, headers, and response statuses.
   - **Server-Side Logs**: Inspect backend APIs for errors (e.g., `ERROR`, `WARN`).
   - **Infrastructure Metrics**: Monitor CPU, memory, or latency spikes.

3. **Validate Requests/Responses**
   - Compare with expected schemas using tools like [JSON Schema](https://json-schema.org/) or [Swagger](https://swagger.io/).
   - Example: A missing `Authorization` header may trigger `401`.

4. **Network Diagnostics**
   - Use `curl`/`Postman` to test endpoints directly (bypassing client logic).
   - Check intermediate proxies/firewalls for blocking rules.
   - Example:
     ```bash
     curl -v -X POST https://api.example.com/endpoint -H "Content-Type: application/json" -d '{"key":"value"}'
     ```

5. **Dependency Checks**
   - Verify linked services (e.g., databases, payment gateways) have no outages.
   - Check rate limits (e.g., AWS API Gateway quotas).

6. **Retry and Backoff Strategies**
   - Implement exponential backoff for transient errors (e.g., `500` → wait 1s → 2s → 4s).
   - Example (Python):
     ```python
     import time
     retry_count = 0
     while retry_count < 3:
         try:
             response = requests.post(url, headers=headers)
             break
         except requests.exceptions.RequestException:
             time.sleep(2 ** retry_count)  # Exponential backoff
             retry_count += 1
     ```

7. **Rollback/Workarounds**
   - Temporarily disable features to isolate the issue.
   - Use feature flags to bypass problematic code paths.

---

### **B. Error Response Handling**
| **HTTP Status Code** | **Typical Cause**                     | **Troubleshooting Steps**                                                                                     |
|-----------------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **400 Bad Request**   | Invalid payload payload (e.g., malformed JSON). | Validate schema; check payload format (e.g., `Content-Type: application/json`).                              |
| **401 Unauthorized**  | Missing/invalid `Authorization` header. | Verify token/key; test with curl: `curl -H "Authorization: Bearer <token>"`.                                |
| **403 Forbidden**     | Authenticated but no permission.       | Check IAM roles/ACLs; audit user permissions.                                                            |
| **404 Not Found**     | Invalid endpoint/ID.                  | Verify URL path; check routing logic.                                                                    |
| **429 Too Many Requests** | Rate limit exceeded.                | Implement retry logic with backoff; check API gateway quotas.                                             |
| **500/503**           | Server error (e.g., DB crash).          | Check server logs; verify underlying dependencies (e.g., database availability).                          |
| **Timeout**           | Request took too long.                | Increase timeout; optimize slow queries (e.g., `LIMIT` clauses).                                           |

---

## **3. Schema Reference**
### **Error Response Schema**
APIs should return consistent error formats. Example (JSON):

| **Field**          | **Type**   | **Description**                                                                                                                                                     | **Example**                     |
|--------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|
| `error`            | `string`   | Human-readable error description.                                                                                                                       | `"Invalid API key"`              |
| `code`             | `string`   | Machine-readable error code (e.g., `AUTH_001`).                                                                                                              | `"UNAUTHORIZED"`                 |
| `details`          | `object`   | Structured metadata (e.g., missing fields).                                                                                                               | `{"field": "api_key"}`          |
| `timestamp`        | `string`   | ISO-8601 formatted time of error.                                                                                                                      | `"2023-10-15T12:00:00Z"`        |
| `request_id`       | `string`   | Unique identifier for tracing.                                                                                                                          | `"req_abc123"`                   |
| `suggestions`      | `array`    | Steps to resolve (e.g., `["Verify your key."]`).                                                                                                           | `["Check your network connection"]` |

---

## **4. Query Examples**
### **A. Debugging with `curl`**
Check API response:
```bash
curl -i -X GET "https://api.example.com/users?limit=10" -H "Authorization: Bearer $TOKEN"
```

Test rate limit handling:
```bash
for i in {1..100}; do curl -s "https://api.example.com/stats"; done
```

### **B. Postman Collection Example**
1. **Set Headers**:
   - `Content-Type: application/json`
   - `Authorization: Bearer <token>`
2. **Send Request**:
   ```json
   POST https://api.example.com/orders
   Body: {
     "user_id": "123",
     "items": ["item1"]
   }
   ```
3. **Analyze Response**:
   - Status: `201` (success) or `400` (validation error).

### **C. Python Debugging Script**
```python
import requests

def debug_api():
    url = "https://api.example.com/data"
    headers = {"Authorization": "Bearer token123"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx
        print("Response:", response.json())
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err.response.status_code} - {err.response.text}")
    except requests.exceptions.Timeout:
        print("Request timed out.")

debug_api()
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                     | **Use Case**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Idempotency](https://docs.patterns.dev/api/idempotency)** | Ensures repeated identical requests produce the same outcome.                                                                                                   | Prevent duplicate payments in financial APIs.                                                  |
| **[Circuit Breaker](https://docs.patterns.dev/api/circuit-breaker)** | Temporarily stops failing calls to avoid cascading failures.                                                                                                    | Protect APIs from cascading crashes during dependency outages.                                  |
| **[Request Validation](https://docs.patterns.dev/api/validation)** | Validates input/output data before processing.                                                                                                               | Reject malformed requests early (e.g., empty `user_id`).                                      |
| **[Retries and Backoff](https://docs.patterns.dev/api/retries)** | Automatically retries failed requests with increasing delays.                                                                                                   | Handle temporary network blips (e.g., `429` or `503`).                                         |
| **[Distributed Tracing](https://docs.patterns.dev/api/tracing)** | Tracks requests across microservices using unique IDs (e.g., `request_id`).                                                                                      | Debug latency in multi-service workflows (e.g., order processing).                            |
| **[Rate Limiting](https://docs.patterns.dev/api/rate-limiting)** | Controls request volume to prevent abuse.                                                                                                                    | Protect APIs from DDoS attacks.                                                                |

---

## **6. Best Practices**
1. **Centralized Logging**
   - Use tools like [ELK Stack](https://www.elastic.co/elk-stack) or [Datadog](https://www.datadoghq.com/) to aggregate logs.
2. **Automated Alerts**
   - Set up alerts for repeated errors (e.g., Slack/email notifications).
3. **Canary Releases**
   - Roll out fixes to a small user group first to test stability.
4. **Documentation**
   - Update API docs (e.g., Swagger/OpenAPI) when breaking changes occur.
5. **Postmortems**
   - After incidents, document root causes and preventive actions.

---
## **7. Tools for API Troubleshooting**
| **Tool**               | **Purpose**                                                                                                                                                     | **Link**                                  |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Postman**            | Test APIs with saved collections and environments.                                                                                                               | [postman.com](https://www.postman.com/)   |
| **New Relic**          | Monitor API performance and errors in real-time.                                                                                                               | [newrelic.com](https://newrelic.com/)    |
| **K6**                 | Load-test APIs for latency/throughput issues.                                                                                                                  | [k6.io](https://k6.io/)                   |
| **AWS CloudWatch**     | Logs and metrics for AWS-hosted APIs.                                                                                                                          | [aws.amazon.com/cloudwatch](https://aws.amazon.com/cloudwatch/) |
| **Grafana**            | Visualize API metrics (latency, error rates).                                                                                                                 | [grafana.com](https://grafana.com/)       |
| **Telemetry SDKs**     | Track API calls (e.g., OpenTelemetry).                                                                                                                       | [opentelemetry.io](https://opentelemetry.io/) |

---
## **8. Common Pitfalls**
- **Ignoring Client-Side Issues**: Assume the server is always correct; validate client payloads/headers.
- **Over-Retrying**: Retrying on `409 Conflict` may corrupt data; use idempotency keys instead.
- **Silent Failures**: Always log errors (even if recovered) for post-analysis.
- **Hardcoding Secrets**: Use environment variables or vaults (e.g., AWS Secrets Manager) for API keys.
- **No Circuit Breakers**: Unbound retries can worsen outages (e.g., during database crashes).

---
## **9. Example Workflow: Timeouts**
**Symptom**: API call hangs indefinitely.
**Steps**:
1. **Test with `curl`**: Confirm if the issue persists outside the app.
   ```bash
   curl -v -X GET "https://api.example.com/slow-endpoint" --connect-timeout 3
   ```
2. **Check Server Logs**: Look for slow queries (e.g., unindexed DB columns).
3. **Optimize**:
   - Add database indexes.
   - Implement caching (e.g., Redis) for frequent queries.
4. **Update Client**: Increase timeout or retry with backoff.

---
## **10. Glossary**
| **Term**               | **Definition**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|
| **API Gateway**        | Entry point for routing API requests (e.g., AWS API Gateway).                                      |
| **Idempotency Key**    | Unique identifier to ensure repeated identical requests succeed once.                            |
| **Load Balancer**      | Distributes traffic across servers to prevent overload.                                           |
| **Payload**            | Data sent/received in an API request/response.                                                    |
| ** Sanitization**      | Removing harmful input (e.g., SQL injection) before processing.                                  |

---
**End of Guide**
*For updates, refer to the latest [API Troubleshooting Patterns](https://docs.patterns.dev/api).*