# **[Pattern] API Troubleshooting Reference Guide**

---

## **Overview**
API troubleshooting is a structured approach to diagnosing, isolating, and resolving issues in API-based integrations. This guide outlines systematic methods for inspecting API responses, logs, network conditions, and configuration settings. It covers common error types, tools for inspection, and best practices to minimize downtime. Whether debugging **4xx (client-side) errors**, **5xx (server-side) failures**, or **latency throttling**, this pattern ensures methodical problem-solving while minimizing disruption to dependent services.

---

## **1. Key Concepts & Implementation Details**

### **1.1 API Error Classification**
API errors are categorized by HTTP status codes and root cause:

| **Category**       | **Status Codes** | **Common Causes**                                                                 | **Troubleshooting Focus Area**                     |
|--------------------|------------------|-----------------------------------------------------------------------------------|----------------------------------------------------|
| **Client Errors**  | 4xx              | Invalid requests, authentication failures, rate limits, malformed payloads        | Payload validation, headers, auth tokens, quotas  |
| **Server Errors**  | 5xx              | Backend crashes, database timeouts, misconfigurations                             | Server logs, resource constraints, retries        |
| **Network Issues** | 5xx/Timeout      | DNS failures, VPN interruptions, firewall blocks                                 | Network tools (Wireshark, `curl`), MTTR tracking   |
| **Authentication** | 401/403          | Expired tokens, incorrect scopes, missing headers                                | Auth flows, key rotation, token lifetime           |
| **Rate Limiting**  | 429              | Exceeded request quotas, burst limits                                           | Quota monitoring, exponential backoff             |

---
### **1.2 Troubleshooting Workflow**
Follow this **step-by-step diagnostic process**:

1. **Reproduce the Issue**
   - Confirm if the error is intermittent or consistent.
   - Note timestamps, API endpoints, and request/response payloads.

2. **Inspect the API Response**
   - Capture **raw HTTP responses** (headers, body, status code).
   - Look for error messages in `X-API-Error` or `error` fields.

3. **Check Logs**
   - **Client Logs**: Local API client libraries (e.g., `axios`, `Postman`).
   - **Server Logs**: Backend logs (e.g., `nginx`, `Spring Boot`, `AWS CloudTrail`).
   - **Third-Party Logs**: If using SaaS APIs (e.g., Stripe, Twilio), review their dashboards.

4. **Validate Inputs**
   - Sanitize payloads for schema compliance (e.g., `JSON Schema` validation).
   - Verify headers (e.g., `Content-Type`, `Authorization`).

5. **Network Analysis**
   - Use tools like `curl`, `Postman`, or `Wireshark` to inspect traffic.
   - Check for **DNS resolution issues** or **firewall blocks**.

6. **Retry & Throttling**
   - Implement exponential backoff for `429` errors.
   - Monitor API usage quotas (e.g., AWS API Gateway, Stripe limits).

7. **Isolate Dependencies**
   - If the API depends on external services (e.g., databases, microservices), test those separately.

8. **Escalate if Needed**
   - Contact the API provider’s support with **reproducible steps** and logs.

---

## **2. Schema Reference**
Common API response schemas for troubleshooting:

| **Field**          | **Type**       | **Description**                                                                                     | **Example Values**                          |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `status`           | `integer`      | HTTP status code                                                                                   | `404`, `500`                                 |
| `error`            | `string`       | Human-readable error message                                                                         | `"Invalid API Key"`                         |
| `errorCode`        | `string`       | Machine-readable error code (for automation)                                                      | `"AUTH_001"`                                |
| `requestId`        | `string`       | Unique identifier for tracing the request (useful in distributed systems)                           | `"req_123abc"`                              |
| `timestamp`        | `ISO8601`      | When the error occurred                                                                             | `"2024-05-20T14:30:00Z"`                    |
| `retryAfter`       | `integer`      | Seconds until retry (for `429`)                                                                        | `30`                                        |
| `traceId`          | `string`       | Distributed tracing ID (if using tools like OpenTelemetry)                                           | `"trc_456def"`                              |
| `metadata`         | `object`       | Additional context (e.g., affected resources)                                                       | `{"resource": "user_789", "action": "delete"}`|

---
**Example Error Response (JSON):**
```json
{
  "status": 400,
  "error": "Invalid payload format",
  "errorCode": "BAD_REQUEST",
  "requestId": "req_789xyz",
  "timestamp": "2024-05-20T14:30:00Z",
  "retryAfter": null,
  "metadata": {
    "missingField": "userId"
  }
}
```

---

## **3. Query Examples**
### **3.1 Inspecting API Responses**
Use `curl` to fetch raw responses:
```bash
# Get raw response (includes headers + body)
curl -v -X GET "https://api.example.com/users/123" -H "Authorization: Bearer token_abc123"
```
- `-v` enables verbose output (logs HTTP headers and timing).

### **3.2 Validating JSON Payloads**
Use `jq` to parse and validate responses:
```bash
# Extract error details from JSON
curl -s "https://api.example.com/validate" | jq '.error' -r
```
- Install `jq`: `sudo apt install jq` (Linux) or `brew install jq` (Mac).

### **3.3 Checking Rate Limits**
```bash
# Simulate a 429 error and retry with backoff
for i in {1..5}; do
  curl -X POST "https://api.example.com/bulk" -H "Retry-After: 5" && break
  sleep $i  # Exponential backoff
done
```

### **3.4 Distributed Tracing**
If using OpenTelemetry:
```bash
# Generate a trace ID for debugging
curl -H "X-Trace-ID: trc_456def" "https://api.example.com/track"
```

---

## **4. Common Tools & Debugging Commands**
| **Tool/Command**       | **Purpose**                                                                                     | **Example**                                  |
|------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------|
| `curl`                 | HTTP request inspection                                                                      | `curl -v -H "Content-Type: application/json" -d '{"key": "value"}' https://api.example.com` |
| `Postman`              | GUI for sending requests and storing collections                                             | Import `.json` collections for testing      |
| `Wireshark`/`tcpdump`  | Low-level network packet inspection                                                           | `tcpdump -i eth0 port 443`                  |
| `ngrep`                | Filter HTTP traffic by port/host                                                              | `ngrep -d eth0 "POST /api/users" port 8080`   |
| `jq`                   | JSON parsing and validation                                                                  | `curl -s API_URL | jq '(.data | length > 0)'` |
| `aws cloudtrail`       | AWS API call logging (if using AWS services)                                                  | `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateTable` |
| `k6`/`Locust`          | Load testing to reproduce rate-limiting issues                                                | `k6 run --vus 100 --duration 30s script.js`  |

---

## **5. Related Patterns**
1. **[Retries & Backoff](https://<pattern-link>)**
   - Implement exponential backoff for transient errors (e.g., `5xx` responses).
   - Use libraries like `retry` (Node.js) or `Polly` (.NET).

2. **[Circuit Breaker](https://<pattern-link>)**
   - Stop retrying failed calls if the backend is down (e.g., Hystrix, Resilience4j).

3. **[API Monitoring](https://<pattern-link>)**
   - Proactively detect errors with tools like Datadog, New Relic, or Prometheus.

4. **[Idempotency Keys](https://<pattern-link>)**
   - Prevent duplicate requests (critical for `POST`/`PUT` operations).

5. **[API Versioning](https://<pattern-link>)**
   - Isolate breaking changes by versioning endpoints (e.g., `/v1/users`).

6. **[Logging & Observability](https://<pattern-link>)**
   - Centralized logs (ELK Stack, Splunk) and distributed tracing (Jaeger, Zipkin).

7. **[Rate Limiting](https://<pattern-link>)**
   - Configure client-side throttling to avoid `429` errors (e.g., Redis rate limiters).

---

## **6. Best Practices**
- **Document Errors**: Maintain a runbook for common issues (e.g., GitHub Gist, Confluence).
- **Reproduce Locally**: Use tools like **ngrok** to mock APIs or **VCR** for recording responses.
- **Automate Alerts**: Set up alerts for `5xx` errors (e.g., Slack/PagerDuty).
- **Minimize Debugging Impact**: Use staging environments for API testing.
- **Update SDKs**: Ensure client libraries are up-to-date for bug fixes.

---
## **7. Glossary**
| **Term**               | **Definition**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|
| **Idempotency**        | A request can be made multiple times without changing the outcome.                                |
| **MTTR**               | Mean Time To Recovery (time to fix an issue).                                                     |
| **Retry Policy**       | Rules for retrying failed requests (e.g., exponential backoff).                                   |
| **Backpressure**       | Handling overload by slowing down requests (e.g., `429` responses).                               |
| **Distributed Trace**  | Tracking a request across microservices using trace IDs.                                           |

---
**End of Guide**
*Last updated: [YYYY-MM-DD]*