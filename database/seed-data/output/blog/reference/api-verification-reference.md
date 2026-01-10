# **[Pattern] API Verification Reference Guide**

---

## **Overview**
The **API Verification** pattern ensures that external APIs—used by a service or application—are functioning correctly, reliable, and secure before processing user requests. This pattern mitigates risks from **downtime, data corruption, rate limits, or malicious responses**, improving system resilience and fault tolerance.

API verification typically involves:
- **Health checks** to validate API accessibility.
- **Response validation** to ensure correct data formats and consistency.
- **Rate limit and quota monitoring** to prevent overuse.
- **Authentication/authorization checks** to verify API access permissions.
- **Data integrity checks** (e.g., checksums, expected structure).

This pattern is often implemented as a **pre-processing layer** in microservices architectures or as a **gateway-level filter** (e.g., in API gateways like Kong, Apigee, or AWS API Gateway).

---

## **Implementation Details**

### **Key Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **API Health Check**  | Periodic or on-demand checks to confirm the API endpoint is reachable and responsive (e.g., HTTP `2xx` status).                                                                                        |
| **Response Validation** | Validating API responses against a known schema (e.g., JSON Schema, OpenAPI/Swagger) or business rules (e.g., required fields, data types).                                                          |
| **Rate Limit Enforcement** | Monitoring and enforcing API usage quotas (e.g., requests per minute) to avoid throttling or abuse.                                                                                                       |
| **Circuit Breaker**   | Temporarily disabling API calls if errors exceed a threshold (e.g., using Hystrix or Resilience4j) to prevent cascading failures.                                                                  |
| **Retry Logic**       | Configurable retries for transient failures (e.g., `5xx` errors) with exponential backoff to handle temporary outages.                                                                                  |
| **Data Sanitization** | Filtering or transforming API responses to remove harmful content (e.g., SQL injection patterns, malformed data) before processing.                                                                   |
| **Logging & Metrics** | Tracking verification failures, latencies, and success rates for observability (e.g., Prometheus, Datadog).                                                                                               |
| **Fallback Mechanisms** | Serving cached or default data if the API fails (e.g., gracefully degrade functionality).                                                                                                              |
| **Idempotency**       | Ensuring repeated API calls produce the same result to avoid duplicate processing errors.                                                                                                               |

---

### **Implementation Strategies**
1. **Pre-Request Verification (Best Practice)**
   - Validate the API before processing user requests (e.g., in a middleware layer).
   - Example: A payment service verifies the payment gateway API before processing a transaction.

2. **Scheduled Health Checks**
   - Use cron jobs or Kubernetes liveness probes to periodically check API endpoints.
   - Example: A background worker pings the third-party weather API every 5 minutes.

3. **Gateway-Level Verification**
   - Integrate verification logic into an API gateway (e.g., Kong plugins, AWS Lambda@Edge).
   - Example: A mobile app gateway validates all external API calls before forwarding them.

4. **Client-Side Verification (Fallback Option)**
   - Implement lightweight checks in the client application (e.g., JavaScript `fetch` interceptors).
   - Example: A web app caches a "last valid response" if the API fails.

5. **Distributed Tracing**
   - Correlate verification failures across services using traces (e.g., OpenTelemetry).
   - Example: Track a failed payment API call from the user request to the verification layer.

---

## **Schema Reference**
Below is a reference table for common API verification schemas and validation rules.

| **Component**          | **Example Schema/Rule**                                                                                                                                                                                                 | **Tools/Libraries**                          |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Health Check**       | `GET /api/health` → Expect: `{ "status": "ok" }` with `200 OK`                                                                                                                                            | `axios`, `curl`, `Superagent`                 |
| **Response Schema**    | ```json { "type": "object", "properties": { "user": { "type": "object", "required": ["id", "email"] } } } ```                                                                                          | `JSON Schema`, `Ajv`, OpenAPI Validator      |
| **Rate Limit Header**  | `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 95`                                                                                                                                                     | `axios-rate-limit`, `Nginx rate limiting`     |
| **Authentication**     | `Authorization: Bearer <token>` with `401 Unauthorized` on failure                                                                                                                                         | `JWT`, OAuth2 (Passport.js, AWS SigV4)        |
| **Data Integrity**     | SHA-256 checksum of response body (e.g., `X-Integrity: abc123...`)                                                                                                                                      | `Crypto.js`, `bcrypt`                         |
| **Idempotency Key**    | `Idempotency-Key: user_12345` to deduplicate duplicate requests                                                                                                                                              | `Postman`, custom middleware                  |

---

## **Query Examples**
### **1. Health Check (HTTP GET)**
```http
GET /v1/users HTTP/1.1
Host: example-api.com
Accept: application/json

# Expected Response (Success)
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "last_check": "2024-01-15T12:00:00Z"
}

# Expected Response (Failure)
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "error": "API down for maintenance"
}
```

### **2. Response Validation (JSON Schema)**
**Request:**
```http
POST /v1/payment HTTP/1.1
Host: payment-gateway.com
Content-Type: application/json

{
  "amount": 99.99,
  "currency": "USD",
  "card": "4111111111111111"
}
```

**Valid Response:**
```json
{
  "transaction_id": "tx_123",
  "status": "approved",
  "amount": 99.99
}
```

**Invalid Response (Validation Failure):**
```json
{
  "error": "Invalid card number"
}
```
*Triggered if `card` does not match `^4\\d{12}(?:\\d{3})?$` regex.*

---

### **3. Rate Limit Enforcement**
**Request:**
```http
GET /v1/logs?limit=100 HTTP/1.1
Host: logs-service.com
```

**First Request (Allowed):**
```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
```

**After 100 Requests (Throttled):**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

### **4. Circuit Breaker Example (Pseudocode)**
```javascript
const circuitBreaker = new CircuitBreaker({
  service: "payment-api",
  timeout: 5000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000
});

async function processPayment() {
  try {
    const response = await circuitBreaker.exec(async () =>
      await axios.post("/v1/payment", { amount: 99.99 })
    );
    return response.data;
  } catch (error) {
    if (error instanceof CircuitBreakerError) {
      return { fallback: "Use cached payment" };
    }
    throw error;
  }
}
```

---

### **5. Idempotency Example (Header-Based)**
**Request 1:**
```http
POST /v1/orders HTTP/1.1
Host: orders-system.com
Idempotency-Key: order_123
Content-Type: application/json

{
  "product": "laptop",
  "quantity": 1
}
```
**Response:**
```json
{
  "order_id": "ord_456",
  "status": "created"
}
```

**Duplicate Request:**
```http
POST /v1/orders HTTP/1.1
Host: orders-system.com
Idempotency-Key: order_123  # Same key!
Content-Type: application/json

{
  "product": "laptop",
  "quantity": 1
}
```
**Response (Idempotent):**
```json
{
  "order_id": "ord_456",  # Same order ID returned
  "status": "already_exists"
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Temporarily stops calls to a failing service to prevent cascading failures.                                                                                                                              | When API failures risk system-wide outages.                                                        |
| **Retry with Backoff**    | Automatically retries failed API calls with increasing delays.                                                                                                                                              | For transient errors (e.g., network timeouts, temporary overloads).                                 |
| **Request Tracing**       | Correlates API calls across services for debugging.                                                                                                                                                       | In distributed systems with multiple API dependencies.                                              |
| **Bulkhead Pattern**      | Limits concurrent API calls to avoid resource exhaustion.                                                                                                                                                  | During high-load scenarios where API throttling is expected.                                       |
| **Fallback Mechanism**    | Serves cached or default data if the API fails.                                                                                                                                                         | For non-critical features where graceful degradation is acceptable.                                 |
| **OpenAPI/Swagger**       | Defines API contracts for validation and documentation.                                                                                                                                                  | When collaborating with third-party APIs or internal teams.                                          |
| **API Gateway**           | Centralizes routing, authentication, and verification for multiple APIs.                                                                                                                                  | For microservices architectures with many external API dependencies.                                |
| **Idempotency Keys**      | Ensures duplicate requests produce the same result.                                                                                                                                                    | For payment, order, or data sync APIs where retries are possible.                                   |
| **Rate Limiting**         | Controls API request volume to prevent abuse.                                                                                                                                                             | When protecting against DDoS or rate-limiting external APIs.                                       |
| **Schema Validation**     | Validates API responses against predefined schemas.                                                                                                                                                     | When data consistency across services is critical.                                                   |

---

## **Best Practices**
1. **Fail Fast**: Reject requests immediately if the API fails (avoid partial processing).
2. **Monitor & Alert**: Set up alerts for verification failures (e.g., Prometheus + Alertmanager).
3. **Cache Responses**: Cache valid API responses to reduce load (e.g., Redis).
4. **Graceful Degradation**: Provide fallback data or error messages to users.
5. **Document Assumptions**: Clearly document API dependencies and their SLAs.
6. **Test Thoroughly**: Include verification in CI/CD pipelines (e.g., Postman/Newman tests).
7. **Logging**: Log verification failures with context (e.g., API endpoint, request/response payloads).
8. **Security**: Use HTTPS, validate all inputs/outputs, and rotate API keys periodically.

---
## **Anti-Patterns to Avoid**
- **Ignoring Errors**: Silently swallowing API failures can lead to silent data corruption.
- **No Retry Logic**: Blind retries without backoff may exacerbate outages.
- **Over-Reliance on Fallbacks**: Fallback mechanisms should be a last resort, not the primary approach.
- **Tight Coupling**: Avoid hardcoding API endpoints; use config files or feature flags.
- **No Circuit Breakers**: Allowing unlimited retries can overwhelm failing services.
- **Skipping Validation**: Assuming API responses are always correct without verification.