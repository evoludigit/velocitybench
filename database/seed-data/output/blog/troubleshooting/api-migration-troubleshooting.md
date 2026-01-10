# **Debugging API Migration: A Troubleshooting Guide**

API migrations are critical but complex operations that require careful planning and execution. Migrating APIs—whether due to refactoring, version upgrades, or replacing a legacy service—often introduces downtime, errors, and integration issues. This guide provides a structured approach to diagnosing and resolving common API migration problems efficiently.

---

## **1. Symptom Checklist: Signs of API Migration Issues**
Before diving into fixes, confirm the symptoms of a problematic API migration. Use this checklist to identify issues:

### **Core API Symptoms**
✅ **5xx Errors (Internal Server Errors)** – *(e.g., 500, 502, 503, 504)*
✅ **Rate Limiting / Throttling** – *(e.g., 429 Too Many Requests)*
✅ **Missing or Incorrect Headers** – *(e.g., `Content-Type`, `Authorization` misconfiguration)*
✅ **Payload Validation Failures** – *(e.g., Invalid JSON, missing required fields)*
✅ **Inconsistent Responses** – *(e.g., same request returns different data between old & new APIs)*
✅ **Slow Response Times** – *(e.g., timeouts, prolonged processing)*
✅ **Client-Side Errors (4xx)** – *(e.g., 400 Bad Request, 403 Forbidden, 404 Not Found)*
✅ **Database Connection Issues** – *(e.g., failed queries, ORM errors)*
✅ **Caching Invalidation Problems** – *(e.g., stale responses from CDN/cache)*
✅ **Third-Party Dependency Failures** – *(e.g., external API calls timing out)*

### **Infrastructure & Log Symptoms**
✅ **High CPU/Memory Usage** – *(check server logs for spikes)*
✅ **Connection Pool Exhaustion** – *(e.g., `Too many open connections` errors)*
✅ **Load Balancer Failover Issues** – *(e.g., traffic not routing correctly)*
✅ **DNS Resolution Failures** – *(e.g., `DNS_PROBE_FINISHED_NXDOMAIN`)*

### **Client-Side Symptoms (Frontend/Backend Clients)**
✅ **Fallback Mechanism Not Triggering** – *(if using dual-write or hybrid APIs)*
✅ **Retry Policies Failing** – *(e.g., exponential backoff not working)*
✅ **Serialization/Deserialization Errors** – *(e.g., malformed responses)*
✅ **WebSocket/Real-Time API Disconnections** – *(e.g., heartbeats failing)*

---
## **2. Common Issues and Fixes (With Code Examples)**

### **Issue 1: 5xx Errors (Internal Server Errors)**
**Symptoms:**
- API returns `500 Internal Server Error` or `502 Bad Gateway`.
- Server logs show unhandled exceptions.

**Root Causes:**
- Unhandled exceptions in middleware/controllers.
- Database connection failures.
- Missing retry logic for transient failures.

**Fixes:**

#### **A. Centralized Error Handling (Node.js/Express Example)**
```javascript
// Middleware to catch and log errors
app.use((err, req, res, next) => {
  console.error(`[API MIGRATION ERROR] ${err.stack}`);
  res.status(500).json({
    error: "Internal Server Error",
    details: process.env.NODE_ENV === "development" ? err.message : null,
  });
});
```

#### **B. Database Connection Retries (PostgreSQL Example)**
```python
# Using SQLAlchemy with retry logic (Python)
from sqlalchemy import exc
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def execute_query(connection, query):
    try:
        return connection.execute(query)
    except exc.OperationalError as e:
        print(f"Retrying due to DB error: {e}")
        raise
```

---

### **Issue 2: Missing/Incorrect Headers**
**Symptoms:**
- Clients receive `401 Unauthorized` or `403 Forbidden`.
- Headers like `Content-Type` or `Authorization` are missing.

**Root Causes:**
- Header propagation broken in proxies (e.g., Nginx, Cloudflare).
- Missing `forwarded` headers in Kubernetes/load balancers.
- CORS misconfiguration.

**Fixes:**

#### **A. Ensure Headers Are Forwarded (Nginx Example)**
```nginx
# Proxy pass with header forwarding
location /api/ {
    proxy_pass http://backend_service;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

#### **B. Enforce Headers in API Gateway (AWS API Gateway Example)**
```yaml
# OpenAPI/Swagger for AWS API Gateway
x-amazon-apigateway-integration:
  responses:
    default:
      headers:
        Access-Control-Allow-Origin: "'*'"
        Access-Control-Allow-Methods: "'*'"
```

---

### **Issue 3: Payload Validation Failures**
**Symptoms:**
- Clients receive `400 Bad Request` with validation errors.
- JSON schema mismatches between old and new APIs.

**Root Causes:**
- Missing required fields in requests.
- Schema changes not reflected in API clients.
- Dynamic payload validation not implemented.

**Fixes:**

#### **A. Use a Schema Validator (JSON Schema + Zod Example)**
```javascript
// Using Zod for request validation
const createUserSchema = z.object({
  name: z.string().min(3),
  email: z.string().email(),
  age: z.number().int().min(18),
});

app.post("/users", async (req, res) => {
  const validatedData = createUserSchema.parse(req.body);
  // Proceed with validated data
});
```

#### **B. Backward Compatibility Fallback (Dual-Write Example)**
```python
# Python - Handle both old and new payload formats
def handle_migration_payload(payload):
    if "old_field" in payload:
        return transform_old_format(payload)
    elif "new_field" in payload:
        return transform_new_format(payload)
    else:
        raise ValueError("Unsupported payload format")
```

---

### **Issue 4: Inconsistent Responses (Old vs. New API)**
**Symptoms:**
- Same request returns different data between legacy and new API.
- Caching causes stale responses.

**Root Causes:**
- Incomplete data migration.
- Race conditions in database writes.
- Caching layers not invalidated.

**Fixes:**

#### **A. Data Migration Audit Logs (PostgreSQL Example)**
```sql
-- Track changes during migration
CREATE TABLE migration_audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMP DEFAULT NOW()
);
```

#### **B. Cache Invalidation (Redis Example)**
```bash
# Redis command to flush cache when schema changes
redis-cli FLUSHALL  # Use cautiously in production!
# Better: Use named keys for per-API version caching
```

---

### **Issue 5: Third-Party Dependency Failures**
**Symptoms:**
- External API calls time out or return `429 Too Many Requests`.
- Rate limits exceeded during migration.

**Root Causes:**
- No retry logic for external calls.
- Rate limiting not accounted for.
- Circuit breakers not implemented.

**Fixes:**

#### **A. Exponential Backoff with Retry (Python Example)**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

response = session.get("https://external-api.example.com/data")
```

#### **B. Circuit Breaker Pattern (Python Resilience Example)**
```python
from resilience4j.resilience4j.circuitbreaker import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_rate_threshold=50,
    waiting_time_in_open_state=5,
    permitted_number_of_calls_in_half_open_state=3,
    sliding_window_size=10,
    sliding_window_type="COUNT_BASED",
)

circuit_breaker = CircuitBreaker(config)
```

---

## **3. Debugging Tools and Techniques**

### **A. Observability Tools**
| Tool               | Purpose                          | Example Use Case                     |
|--------------------|----------------------------------|--------------------------------------|
| **Prometheus + Grafana** | Metrics monitoring               | Track API latency, error rates       |
| **OpenTelemetry**   | Distributed tracing              | Trace requests across microservices   |
| **ELK Stack (Elasticsearch, Logstash, Kibana)** | Log aggregation | Correlate logs for slow API calls    |
| **Datadog/New Relic** | APM (Application Performance Monitoring) | Identify bottlenecks in migration   |

#### **Example Prometheus Query for Migration Errors**
```promql
# Count 5xx errors per API endpoint
sum(rate(http_server_requests_total{status=~"5.."}[5m])) by (route)
```

### **B. Logging Strategies**
- **Structured Logging** (JSON format) for easier parsing.
  ```javascript
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    level: "ERROR",
    message: "API migration failed",
    endpoint: "/v2/users",
    error: err.stack
  }));
  ```
- **Correlation IDs** for tracing requests across services.
  ```javascript
  // Add correlation ID to requests
  const correlationId = req.headers["x-correlation-id"] || uuidv4();
  req.correlationId = correlationId;
  ```

### **C. Postman/Newman for API Testing**
- **Pre-migration:** Run `newman run migration_test_collection.json`.
- **Post-migration:** Compare responses between old and new endpoints.
  ```bash
  # Compare API responses using Postman
  newman compare --collection legacy_api_collection.json --collection new_api_collection.json --environment env.json
  ```

### **D. Chaos Engineering (Controlled Testing)**
- Use **Gremlin** or **Chaos Mesh** to simulate failures (e.g., timeouts, network partitions) during migration.

---

## **4. Prevention Strategies**

### **A. Pre-Migration Checklist**
1. **Backward Compatibility Testing**
   - Ensure old clients can still consume the new API (e.g., via deprecated endpoints).
2. **Rate Limiting & Throttling**
   - Set up gradual rollouts to avoid overwhelming new infrastructure.
3. **Feature Flags**
   - Use flags to toggle between old and new APIs.
     ```javascript
     // Example: Toggle API version
     const useNewAPI = flags.getBoolean("USE_NEW_API", false);
     ```
4. **Database Migration Strategy**
   - Use **Zero-Downtime Migrations** (e.g., Proxy-based or Dual-Write).
   - Test with **Black Box Testing** (simulate clients without internal access).

### **B. Rollout Phases**
| Phase          | Action                                                                 |
|----------------|-------------------------------------------------------------------------|
| **Phase 1**    | Deploy new API alongside old one (Canary Release).                     |
| **Phase 2**    | Gradually shift traffic (e.g., 10% → 50% → 100%).                       |
| **Phase 3**    | Sunset old API (with proper deprecation notices).                       |
| **Phase 4**    | Monitor for drift in new API behavior.                                 |

### **C. Documentation & Communication**
- **API Deprecation Policy**: Clearly state when old endpoints will be removed.
  ```markdown
  # API Deprecation Notice
  **Endpoints affected**: `/v1/users`, `/v1/orders`
  **Deprecation Date**: 2024-06-30
  **Migration Path**: Use `/v2/users` (documented [here](#))
  ```
- **Client SDK Updates**: Ensure all libraries (SDKs) are updated to support new APIs.
- **Internal Runbooks**: Document steps for rollback (e.g., re-enable old API if critical).

### **D. Automated Testing**
- **Unit Tests**: Mock external dependencies (e.g., database, third-party APIs).
  ```python
  # Example: pytest with mock
  from unittest.mock import patch

  @patch("services.external_api.fetch_data")
  def test_migration_endpoint(mock_fetch):
      mock_fetch.return_value = {"data": "migrated"}
      response = client.get("/v2/data")
      assert response.json() == {"data": "migrated"}
  ```
- **Integration Tests**: Test end-to-end flows (e.g., user registration with new API).
- **Load Testing**: Simulate traffic spikes (e.g., using **Locust** or **k6**).

---

## **5. Rollback Plan (If Things Go Wrong)**
1. **Identify the Breakpoint**
   - Check API logs for the exact time when errors spiked.
2. **Revert Infrastructure Changes**
   - Roll back Docker/Kubernetes deployments.
   - Revert database schema changes.
3. **Fall Back to Old API**
   - Use a feature flag to toggle back.
   - Temporarily disable rate limiting if API is overloaded.
4. **Communicate the Incident**
   - Notify stakeholders via **PagerDuty/Slack alerts**.
   - Provide a timeline for resolution.

---

## **Conclusion**
API migrations are high-stakes operations that require meticulous planning, observability, and gradual rollouts. By following this guide, you can:
✔ **Quickly diagnose** issues using structured symptoms and logs.
✔ **Apply fixes** with code examples for common failure modes.
✔ **Prevent future problems** with rate limiting, backward compatibility, and automated testing.
✔ **Ensure rollback** with clear documentation and monitoring.

**Next Steps:**
1. Audit your current API migration.
2. Implement structured logging and metrics.
3. Run a pre-migration load test.
4. Plan a phased rollout with feature flags.

Good luck with your migration! 🚀