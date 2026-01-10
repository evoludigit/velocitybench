# **[Pattern] API Gotchas: Reference Guide**

## **Overview**
API Gotchas are subtle, often undocumented behaviors, edge cases, or edge conditions that can lead to unexpected errors, degraded performance, or inconsistent responses if not handled intentionally. While APIs aim to provide predictable interfaces, real-world usage introduces complexities in versioning, rate limits, authentication, data formats, and environmental factors. This guide documents common API Gotchas across REST, GraphQL, and gRPC to help developers avoid pitfalls, optimize interactions, and debug issues efficiently.

---

## **Key Concepts & Implementation Details**

### **1. Common Sources of API Gotchas**
| **Category**          | **Description**                                                                 | **Example Scenarios**                                                                 |
|-----------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Versioning**        | APIs evolve but may retain backward compatibility breakages.                  | A v1 endpoint returns a field removed in v2 under a new name.                        |
| **Rate Limiting**     | Throttling policies can change unexpectedly.                                   | A 1,000 requests/minute limit becomes 100 after an update, triggering silent failures. |
| **Authentication**    | Token expiration, scope mismatches, or CORS misconfigurations.                | A JWT token expires mid-request, returning `401 Unauthorized` instead of retry hints. |
| **Idempotency**       | Non-idempotent actions (e.g., `DELETE`) may cause data inconsistency.          | Concurrent `DELETE` requests on the same resource may return `200 OK` but different data. |
| **Error Handling**    | Inconsistent error codes (e.g., `400` for malformed input vs. `403`).         | A `400 Bad Request` may hide missing required fields vs. a `422 Unprocessable Entity`. |
| **Data Format**       | Parser inconsistencies (JSON vs. XML), floating-point precision, or timezone handling. | A timestamp `2023-01-01T00:00:00Z` becomes `2023-01-01` due to client-side parsing.   |
| **Pagination**        | Offset-based vs. cursor-based pagination may behave differently.              | A `?offset=10` query returns 10 items, but `?limit=10&offset=10` may return fewer.   |
| **Concurrency**       | Race conditions in distributed systems (e.g., optimistic locking).          | Two API calls concurrently update the same row, with one overwriting the other.       |
| **Environment**       | Sandbox vs. production differences (e.g., mock data, delay mitigations).     | A `429 Too Many Requests` in production but not in staging due to mock rate limits.   |
| **Performance**       | Latency spikes due to unseen dependencies (e.g., third-party integrations). | A `POST /payments` call fails silently because a payment gateway is down.           |

---

### **2. Schema Reference (Key Fields & Edge Cases)**

| **Field**            | **Description**                                                                 | **Gotcha**                                                                             | **Mitigation**                                                                         |
|----------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `Content-Type`       | Specifies data format (e.g., `application/json`, `application/xml`).        | Server ignores `Content-Type`; client sends `text/plain` by mistake.                  | Validate headers; use tools like Postman to enforce Content-Type.                      |
| `X-RateLimit-*`      | Rate-limiting headers (e.g., `X-RateLimit-Limit`, `X-RateLimit-Remaining`).  | Headers missing in production but present in docs.                                     | Check headers in real traffic; implement exponential backoff.                           |
| `Retry-After`        | Time to wait before retrying (for rate limits).                             | `Retry-After` header missing despite `429` response.                                   | Use HTTP clients (e.g., `axios-retry`) to handle retries automatically.                 |
| `Etag`               | Entity tag for caching/conditional requests.                                  | `ETag` changes between reads/write but client doesn’t use `If-Match`.                | Always include `If-Match` for PUT/DELETE to avoid overwrites.                          |
| `id` (Resource ID)   | Unique identifier for a resource.                                             | IDs are UUIDs but client uses auto-incremented integers.                              | Document ID format; validate schema in client code.                                    |
| `timestamp`          | Server-generated timestamp.                                                   | Timezone mismatch: server uses UTC (`2023-01-01T00:00:00Z`), client expects local time. | Normalize timestamps to ISO 8601 or document timezone handling.                       |
| `metadata`           | Extra fields not in the primary schema.                                      | `metadata` field changes without version updates.                                     | Document deprecation policies for metadata fields.                                    |
| `sort`/`order`       | Query parameters for sorting data.                                            | `sort=-created_at` returns descending order, but API docs say "descending = `sort=+`". | Test all combinations of `sort`/`order` parameters.                                   |
| `links` (HATEOAS)    | Hypermedia controls for resource navigation.                                 | `links` object missing in responses despite docs claiming support.                     | Check endpoint consistency; use tools like Insomnia for dynamic API exploration.        |
| `version`            | API version in headers/paths.                                                | Client uses `/v1/users` instead of `/v2/users` with `Accept: application/vnd.v2+json`. | Hardcode version in client; handle version negotiation gracefully.                      |

---

## **Query Examples & Anti-Patterns**

### **✅ Correct Usage**
```http
# Idempotent DELETE with ETag
DELETE /api/v1/resources/123
Headers:
  If-Match: "abc123"
  Accept: application/vnd.v2+json
```

```http
# Respecting Rate Limits with Retry-After
POST /api/v1/submit
Headers:
  Authorization: Bearer <token>
# If 429 received:
# GET /api/v1/ratelimit
# Retry after 5 seconds
```

### **❌ Common Anti-Patterns**
| **Anti-Pattern**                     | **Problem**                                                                     | **Fix**                                                                               |
|--------------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| Ignoring `Content-Type`               | Server parses `text/plain` as JSON, causing errors.                           | Always set `Content-Type: application/json`.                                           |
| Hardcoding `Accept` headers          | Client requests `v1` data but API is `v2`.                                    | Fetch latest version metadata or use feature flags.                                   |
| No error handling for `429`          | Silent failures due to rate limits.                                           | Implement exponential backoff; monitor `Retry-After`.                                   |
| Assuming `id` is numeric            | API uses UUIDs, but client queries `?id=1`.                                   | Validate IDs against regex `/^[0-9a-f]{8}-[0-9a-f]{4}-.*/`.                            |
| No retries for transient failures   | Network blips cause `5xx` errors to propagate.                               | Use circuit breakers (e.g., Hystrix) or retry policies.                                |
| Overlooking `links` in responses     | Client misses pagination controls in `links` object.                          | Parse `links` dynamically; use libraries like `jsonapi-serializer`.                    |
| Not testing edge cases               | Works in staging but fails in production due to unseen constraints (e.g., max file size). | Use chaos engineering tools (e.g., Gremlin) to simulate failures.                     |

---

## **Related Patterns**

### **1. [Idempotency Keys](https://www.api-gateway.dev/docs/patterns/idempotency/)**
- **Relationship**: API Gotchas often arise from non-idempotent operations.
- **Mitigation**: Use idempotency keys to ensure retries don’t cause duplicate side effects.
- **Example**: For a `POST /payments`, include `Idempotency-Key: abc123` to deduplicate requests.

### **2. [Circuit Breakers](https://microservices.io/patterns/resilience/circuit-breaker.html)**
- **Relationship**: Gotchas like rate limits or third-party failures can trigger cascading errors.
- **Mitigation**: Implement circuit breakers to fail fast and avoid retries during outages.
- **Tools**: Hystrix, Resilience4j, or custom solutions with exponential backoff.

### **3. [Feature Flags](https://launchdarkly.com/glossary/feature-flags/)**
- **Relationship**: Undocumented API changes or A/B testing can introduce Gotchas.
- **Mitigation**: Use feature flags to toggle API versions or experimental endpoints.
- **Example**: `Accept: application/vnd.experimental.v3+json` for preview features.

### **4. [OpenAPI/Swagger Validation](https://swagger.io/tools/swagger-editor/)**
- **Relationship**: API docs may not reflect runtime behavior.
- **Mitigation**: Validate requests against OpenAPI specs to catch mismatches early.
- **Tools**:
  - [Swagger Editor](https://editor.swagger.io/) (manual validation).
  - [Spectral](https://stoplight.io/open-source/spectral/) (linter for OpenAPI).

### **5. [Retry Policies](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)**
- **Relationship**: Gotchas like `5xx` errors or rate limits require intelligent retries.
- **Mitigation**: Implement exponential backoff with jitter to avoid thundering herds.
- **Example**:
  ```javascript
  // Using axios-retry
  const axios = require('axios');
  const axiosRetry = require('axios-retry');

  axiosRetry(axios, {
    retries: 3,
    retryDelay: (retryCount) => Math.min(retryCount * 100, 1000),
    retryCondition: (error) => error.response?.status === 500 || error.response?.status === 429,
  });
  ```

### **6. [Observability Patterns](https://www.observabilitybook.org/)**
- **Relationship**: Gotchas often go unnoticed without logs/metrics.
- **Mitigation**:
  - **Logging**: Correlate requests with traces (e.g., X-Request-ID).
  - **Metrics**: Track error rates, latency percentiles, and rate limit hits.
  - **Tracing**: Use OpenTelemetry to identify bottlenecks.
- **Tools**: Prometheus (metrics), Jaeger (traces), ELK (logs).

---

## **Debugging Workflow for API Gotchas**
1. **Reproduce**: Isolate the issue (e.g., does it occur in staging/production?).
2. **Inspect Headers**: Check for missing/incorrect `Content-Type`, `Authorization`, etc.
3. **Validate Schema**: Compare request/response against OpenAPI docs.
4. **Check Logs/Metrics**: Look for 4xx/5xx errors or rate limit hits.
5. **Test Edge Cases**:
   - Empty payloads.
   - Malformed IDs/timestamps.
   - Concurrent requests.
6. **Review Change Logs**: Did the API update recently? Check release notes.
7. **Consult Community**: Check API forums (e.g., GitHub discussions, Stack Overflow) for similar reports.
8. **Mitigate**: Apply fixes (e.g., retries, idempotency keys) and monitor for regressions.

---
**Note**: API Gotchas are inevitable in distributed systems. Proactively document unresolved issues in your API’s `/health` or `/status` endpoint and communicate changes via changelogs.