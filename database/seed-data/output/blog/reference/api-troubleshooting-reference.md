# **[Pattern] API Troubleshooting Reference Guide**

---

## **Overview**
This guide provides structured methods for diagnosing and resolving common issues in API-based systems. API troubleshooting follows a systematic approach to isolate problems, verify configurations, and apply fixes efficiently. It covers **client-side, server-side, and infrastructure-level** diagnostics while maintaining clear routing paths between symptoms and possible solutions.

For developers, DevOps engineers, and operations teams, this reference ensures alignment when debugging APIs in microservices, REST, GraphQL, or gRPC environments. Use this guide alongside logging tools (e.g., ELK, Prometheus) and monitoring frameworks (e.g., OpenTelemetry) to streamline troubleshooting workflows.

---

## **Key Concepts & Implementation Details**

### **1. Troubleshooting Phases**
| **Phase**               | **Objective**                                                                 | **Key Actions**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Verification**        | Confirm the API request/receive cycle is functional.                          | Check network connectivity, CORS headers, and basic HTTP status codes.           |
| **Isolation**           | Narrow down the issue to a specific component (client, server, network).     | Use tools like Postman, cURL, or load balancer logs.                             |
| **Diagnosis**           | Identify root cause (e.g., payload parsing errors, rate limiting).           | Review error logs, code breakpoints, and dependency failures.                     |
| **Resolution**          | Apply fixes or escalate if unresolved.                                       | Update code, adjust infrastructure, or consult vendor documentation.            |

### **2. Common API Issues & Patterns**
| **Issue**               | **Symptom**                                      | **Common Root Causes**                                                                 |
|-------------------------|--------------------------------------------------|--------------------------------------------------------------------------------------|
| **5xx Errors**          | Server errors (Internal Server Error, Gateway Timeout). | Backend service crashes, database overload, or misconfigured dependencies.            |
| **4xx Errors**          | Client errors (Bad Request, Unauthorized).     | Invalid payload, missing/expired tokens, or API key misconfiguration.                  |
| **Latency Spikes**      | Slower-than-expected response times.            | Cold starts, unoptimized queries, or throttle limits.                                 |
| **Connectivity Failures** | API unreachable (DNS resolution, timeouts).    | Network policies, VPN issues, or API gateway misconfigurations.                     |
| **Data Corruption**     | Inconsistent or missing responses.             | Incorrect schema validation, serialization issues (e.g., JSON/XML parsing errors). |

---

## **Schema Reference**
The following tables outline key API request/response objects and troubleshooting schemas.

### **1. API Request Schema**
| **Field**          | **Type**   | **Description**                                                                                     | **Example Value**                     |
|--------------------|------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `method`           | String     | HTTP method (`GET`, `POST`, etc.).                                                                   | `GET`                                 |
| `endpoint`         | String     | API route (e.g., `/v1/users/{id}`).                                                                 | `/v1/users/123`                       |
| `headers`          | Object     | Metadata (e.g., `Authorization: Bearer <token>`).                                                 | `{ "Accept": "application/json" }`   |
| `payload`          | Object/Array| Request body (serialized JSON, XML, etc.).                                                          | `{ "name": "John Doe" }`              |
| `query_params`     | Object     | URL-encoded parameters (e.g., `?limit=10&offset=0`).                                                | `{ limit: "10" }`                     |
| `timeout`          | Number     | Request timeout in milliseconds.                                                                  | `5000`                                |

### **2. API Response Schema**
| **Field**          | **Type**   | **Description**                                                                                     | **Example Value**                     |
|--------------------|------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `status`           | String     | HTTP status code (e.g., `200`, `404`).                                                              | `200`                                 |
| `body`             | Object/Array| Deserialized response payload.                                                                       | `{ "id": 123, "name": "John" }`       |
| `headers`          | Object     | Headers (e.g., `Content-Type: application/json`).                                                   | `{ "X-RateLimit-Limit": "100" }`     |
| `errors`           | Object     | Error details if `status` is `4xx/5xx`.                                                              | `{ "message": "Invalid token" }`      |
| `trace_id`         | String     | Unique identifier for tracing requests across services.                                             | `abc123-xyz456`                       |

---

## **Query Examples**
Use these examples to validate API functionality and diagnose common issues.

### **1. Basic GET Request (Verification)**
**Command:**
```bash
curl -X GET "https://api.example.com/v1/users/123" \
     -H "Authorization: Bearer <token>" \
     -H "Accept: application/json" \
     -v
```
**Expected Output:**
```json
{
  "status": 200,
  "body": { "id": 123, "name": "John Doe" },
  "headers": { "Content-Type": "application/json" }
}
```
**Troubleshooting Steps if Failed:**
- Verify the `/v1/users/123` endpoint exists.
- Check token validity with `curl -X GET "https://api.example.com/auth/validate" -H "Authorization: Bearer <token>"`.

---

### **2. POST Request with Payload (Diagnosis)**
**Command:**
```bash
curl -X POST "https://api.example.com/v1/users" \
     -H "Content-Type: application/json" \
     -d '{"name": "Alice", "email": "alice@example.com"}' \
     --verbose
```
**Error Handling:**
- **400 Bad Request:** Validate payload schema (e.g., missing `email`).
- **500 Server Error:** Check backend logs for database connection errors.

---

### **3. End-to-End Latency Test**
**Command (using `time` for timing):**
```bash
time curl -s -o /dev/null -w "%{http_code}" "https://api.example.com/v1/health"
```
**Expected:**
```
200  # HTTP status
0.3s  # Latency (compare against SLA thresholds)
```
**If Latency Exceeds Threshold:**
- Use `traceroute` or `mtr` to check network hops.
- Check API gateway logs for queue delays.

---

### **4. Schema Validation Check**
**Command (using `jq` to validate JSON):**
```bash
curl -s "https://api.example.com/v1/users" | \
jq 'has("id") and has("name")'
```
**Output:**
- `true` (valid response).
- `false` (missing fields; check API documentation).

---

## **Related Patterns**
Consult these patterns for deeper diagnostics:

1. **[Circuit Breaker Pattern]**
   - Useful for handling cascading failures in distributed APIs.
   - *Tools:* Hystrix, Resilience4j.

2. **[Rate Limiting Pattern]**
   - Mitigates abuse by enforcing request quotas.
   - *Tools:* NGINX, Tokens Bucket Algorithm.

3. **[Retries & Backoff Pattern]**
   - Automatically retries failed API calls with exponential backoff.
   - *Tools:* Spring Retry, Axios retry plugin.

4. **[Canary Releases Pattern]**
   - Gradually rolls out API changes to minimize risks.
   - *Tools:* Istio, Kubernetes.

5. **[Observability Patterns]**
   - Centralized logging, metrics, and tracing.
   - *Tools:* OpenTelemetry, Prometheus + Grafana.

---
**Note:** Always reference the **API specification (Swagger/OpenAPI)** and **vendor documentation** for environment-specific details. For production issues, consult the **SRE (Site Reliability Engineering)** team.