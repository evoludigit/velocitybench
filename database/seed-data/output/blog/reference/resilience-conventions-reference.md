# **[Pattern] Resilience Conventions Reference Guide**
*Define explicit standards to ensure consistent resilience behavior across distributed systems.*

---

## **Overview**
The **Resilience Conventions** pattern establishes **standardized, machine-readable attributes and query conventions** for resilience policies (e.g., retries, timeouts, fallbacks) across services, APIs, or microservices. By defining a **unified schema** (e.g., OpenAPI, JSON Schema, or attribute annotations), teams can declaratively enforce resilience behavior without hardcoding logic in client/server code. This enables **automated discovery, validation, and enforcement** of resilience policies, reducing inconsistencies and improving system reliability.

Key benefits:
- **Decouples resilience policies** from implementation (e.g., HTTP clients, gRPC calls).
- **Supports dynamic configuration** via runtime inspection (e.g., service mesh, API gateways).
- **Enables tooling** (e.g., CI/CD validation, chaos engineering, observability).
- **Standardizes failure modes** (e.g., retries for transient errors vs. circuit-breaking for permanent failures).

---

## **Implementation Details**

### **1. Core Concepts**
| Concept               | Description                                                                                                                                                                                                 | Example Attributes                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Resilience Context** | A scope (e.g., endpoint, operation, or service) where policies apply.                                                                                                                                     | `@context: "GET /api/orders"`                                                                         |
| **Policy Type**        | Defines the resilience mechanism (e.g., retry, timeout, fallback).                                                                                                                                        | `type: "retry"`                                                                                         |
| **Conditions**         | Rules to trigger a policy (e.g., HTTP status codes, exception types).                                                                                                                                     | `conditions: { statusCodes: [500, 503], exception: "TimeoutException" }`                           |
| **Parameters**         | Configures policy behavior (e.g., max retries, timeout duration).                                                                                                                                         | `maxRetries: 3`, `timeoutMs: 2000`                                                                   |
| **Fallback**           | Defined response or action when a policy fails.                                                                                                                                                           | `fallback: { response: { status: 204, body: "NoContent" } }`                                        |
| **Metadata**           | Additional context (e.g., documentation, severity).                                                                                                                                                     | `description: "Retry for database timeouts", severity: "high"`                                         |

---

### **2. Schema Reference**
Define resilience conventions using **one of the following schemas** (or a hybrid):

#### **A. Attribute-Based (Annotations)**
Add resilience attributes to **HTTP endpoints, gRPC methods, or service contracts** (e.g., via OpenAPI/Swagger, gRPC service descriptions).
**Example (OpenAPI 3.0 Extension):**
```yaml
paths:
  /api/orders/{id}:
    get:
      operationId: getOrder
      x-resilience:
        - context: "GET /api/orders/{id}"
          type: "retry"
          conditions:
            statusCodes: [500, 503]
          maxRetries: 3
          intervalMs: 1000
          fallback:
            response:
              status: 200
              body: { "status": "fallback", "message": "Order data unavailable" }
```

#### **B. JSON Schema (Standalone)**
Define resilience policies in a **separate JSON file** referenced by services.
**Example (`resilience-policies.json`):**
```json
{
  "$schema": "http://example.com/resilience/v1/schema.json",
  "policies": [
    {
      "context": "POST /api/payments",
      "type": "circuitBreaker",
      "conditions": { exception: "PaymentServiceException" },
      "parameters": { maxRequests: 10, failureThreshold: 50, resetTimeoutMs: 60000 }
    },
    {
      "context": "GET /api/users",
      "type": "timeout",
      "parameters": { timeoutMs: 1500 }
    }
  ]
}
```

#### **C. Attribute-Based (Code Annotations)**
Use **language-specific annotations** (e.g., Java `@ResilienceContext`, Python decorators).
**Example (Java):**
```java
@ResilienceContext(
    context = "GET /api/users",
    type = ResilienceType.RETRY,
    conditions = { StatusCondition.CODE_5XX },
    maxRetries = 3
)
public User getUser(String id) { ... }
```

---

### **3. Schema Validation**
Validate resilience policies against a **reference schema** (e.g., JSON Schema, OpenAPI):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ResiliencePolicy",
  "type": "object",
  "properties": {
    "context": { "type": "string" },
    "type": { "enum": ["retry", "timeout", "circuitBreaker", "fallback"] },
    "conditions": {
      "type": "object",
      "properties": {
        "statusCodes": { "type": "array", "items": { "type": "number" } },
        "exception": { "type": "string" }
      }
    },
    "parameters": { "type": "object" },
    "fallback": { "type": "object" }
  },
  "required": ["context", "type"]
}
```

**Tools:**
- **JSON Schema Validator** (e.g., [Ajv](https://ajv.js.org/), [jsonschema](https://github.com/josdejong/json-schema))
- **OpenAPI Validator** (e.g., [Swagger Parser](https://github.com/swagger-api/swagger-parser))
- **CI/CD Plugins** (e.g., GitHub Actions, Jenkins) to enforce schema compliance.

---

## **Query Examples**
Resilience conventions enable **programmatic discovery and application** of policies. Below are examples of how to **query and use** policies.

---

### **1. Query Policies for an Endpoint**
**Input:** Request to `/api/orders/{id}?resilience-policies=true`
**Output (JSON):**
```json
{
  "policies": [
    {
      "context": "GET /api/orders/{id}",
      "type": "retry",
      "conditions": { "statusCodes": [500, 503] },
      "maxRetries": 3,
      "intervalMs": 1000,
      "fallback": { "response": { "status": 204 } }
    }
  ]
}
```

**Implementation (HTTP Client):**
```java
// Pseudo-code for fetching policies (e.g., via service discovery or metadata store)
List<ResiliencePolicy> policies = resilienceClient.getPolicies(
    "GET",
    "/api/orders/123"
);
```

---

### **2. Apply Policies Dynamically**
Use policies to **modify client behavior** (e.g., retries, timeouts) at runtime.
**Example (gRPC Client with Retry):**
```python
# Pseudocode: Apply retry policy from conventions
def call_grpc_service(service, method, request, policy):
    max_retries = policy["maxRetries"]
    for attempt in range(max_retries):
        try:
            response = service.method(request)
            return response
        except Exception as e:
            if policy["conditions"]["statusCodes"].includes(get_status_code(e)):
                time.sleep(policy["intervalMs"] / 1000)
            else:
                raise
    return policy["fallback"]["response"]
```

**Example (HTTP Client with Timeout):**
```javascript
// Apply timeout from conventions
const resiliencePolicy = await getPolicyForRequest("GET", "/api/users");
const timeoutMs = resiliencePolicy.parameters.timeoutMs;
const response = await fetch("/api/users", { timeout: timeoutMs });
```

---

### **3. Fallback Handling**
**Example: Return a fallback response for failed calls.**
```typescript
// Pseudocode fallback logic
function callWithFallback(url: string, fallback: any) {
  try {
    const response = fetch(url);
    return response;
  } catch (error) {
    if (isResilienceError(error)) {
      return fallback;
    }
    throw error;
  }
}
```

---

## **Related Patterns**
| Pattern                          | Relationship                                                                 | When to Use                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Circuit Breaker**              | Complementary: Defines when to apply circuit-breaking (e.g., `failureThreshold`). | Use alongside Resilience Conventions to enforce circuit-breaker rules in policies.         |
| **Retry as a Service**           | Extends: Policies can specify retry logic (e.g., exponential backoff).      | Combine with a distributed retry library (e.g., Resilience4j, Polly) to enforce conventions. |
| **Bulkhead Pattern**             | Extends: Policies can limit concurrent requests (e.g., `maxConcurrentRequests`). | Use in conjunction to define thread pool or concurrency limits.                              |
| **Fallback Service**             | Complements: Policies define when to route to a fallback (e.g., caching).     | Pair with fallback services (e.g., Redis cache) for degraded operation.                         |
| **Observability for Resilience** | Supports: Policies can include metrics/telemetry (e.g., `metricsEnabled: true`). | Use OpenTelemetry or Prometheus to track policy application and failures.                      |
| **API Gateway Resilience**       | Applies at edge: Gateways enforce policies before routing to backend.       | Deploy policies in API gateways (e.g., Kong, Apigee) to centralize resilience logic.           |

---

## **Best Practices**
1. **Standardize Naming:** Use consistent naming for contexts (e.g., `/api/users` vs. `user-service`).
2. **Version Policies:** Include versioning in policies (e.g., `version: "1.0"`).
3. **Document Defaults:** Define fallback/default policies for missing conventions.
4. **Tooling Integration:**
   - **Service Mesh:** Inject policies via Istio/Linkerd (e.g., Envoy filters).
   - **CI/CD:** Validate policies in build pipelines.
   - **Chaos Engineering:** Use policies to simulate failures (e.g., `timeoutMs: 0` for testing).
5. **Security:** Encrypt sensitive parameters (e.g., credentials in fallback URIs).
6. **Performance:** Cache policies to avoid runtime lookups.

---
## **Example Workflow**
1. **Define:** Add resilience attributes to an OpenAPI spec or JSON file:
   ```yaml
   x-resilience:
     - context: "POST /api/orders"
       type: "retry"
       conditions: { statusCodes: [429, 503] }
       maxRetries: 5
   ```
2. **Validate:** Use a schema validator to ensure correctness.
3. **Apply:** Client/server libraries (e.g., Resilience4j, Axios plugins) read policies at runtime.
4. **Monitor:** Track policy application (e.g., "Retry policy triggered 42 times today").

---
## **Limitations**
- **Runtime Overhead:** Parsing policies adds latency (mitigate with caching).
- **Complexity:** Overlapping policies may require prioritization rules.
- **Tooling Gaps:** Not all languages/frameworks support dynamic policy loading.

---
## **Tools & Libraries**
| Tool/Library               | Purpose                                                                 |
|----------------------------|-------------------------------------------------------------------------|
| **Resilience4j**           | Java library to apply policies (retry, circuit breaker) from conventions. |
| **Polly**                  | .NET library for resilience (supports attribute-based policies).         |
| **OpenTelemetry**          | Instrument policy application for observability.                         |
| **Istio/Linkerd**          | Service mesh to enforce policies via Envoy filters.                     |
| **Swagger Codegen**        | Generate client/server SDKs with built-in resilience support.           |
| **JSON Schema Validator**  | Enforce schema compliance in CI/CD.                                      |

---
## **Further Reading**
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [OpenAPI Extensions for Resilience](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.3.md#extensions)
- [Chaos Engineering with Resilience Conventions](https://chaoss.community/)
- [Service Mesh Patterns](https://www.oreilly.com/library/view/service-mesh-patterns/9781492056835/)