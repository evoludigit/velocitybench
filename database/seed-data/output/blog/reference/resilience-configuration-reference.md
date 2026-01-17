**[Pattern] Resilience Configuration: Reference Guide**

---
### **Overview**
The **Resilience Configuration** pattern defines structured, machine-readable rules for implementing resilience behaviors in distributed systems. This pattern standardizes configurations for common resilience patterns—such as retries, circuit breakers, timeouts, and rate limiting—into a declarative schema. Teams can apply these configurations across services, libraries, and frameworks (e.g., Kubernetes, Istio, Resilience4j, Retry Policies) for consistent fault tolerance.

Resilience configurations are **versioned schemas** (e.g., OpenAPI/JSON/YAML) that map directly to runtime implementations, ensuring alignment between design and execution. Use cases include:
- **Microservices** where components must adapt dynamically to failure.
- **Hybrid cloud/edge** environments requiring per-service resilience policies.
- **CI/CD pipelines** that inject resilience rules into deployed artifacts.

By centralizing resilience logic, this pattern reduces technical debt, simplifies monitoring, and enables automated resilience testing.

---

### **2. Schema Reference**
Resilience configurations use a **hierarchical schema** with four core components. Below is a **Canonical Schema** (compatible with OpenAPI/JSON/YAML):

| **Component**       | **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Examples**                                                                                     |
|---------------------|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Global**          | -                       | Object         | Root object defining global defaults.                                                                                                                                                                         |                                  |
|                     | `version`               | String         | Schema version (e.g., `"v1.2"`).                                                                                                                                                                                | `"v1.2"`                                                                                           |
|                     | `defaultTimeout`        | Duration       | Default timeout for operations (applied if no per-service override).                                                                                                                                               | `"5s"`, `"2m"`                                                                                   |
|                     | `retryDefault`          | RetrySpec      | Default retry policy (see Subschema for details).                                                                                                                                                                     | See **RetrySpec** table below.                                                                  |
| **Services**        | `services`              | Array[Object]  | List of services and their resilience rules.                                                                                                                                                                     | `[{ "name": "user-service", "retries": {...} }]`                                                 |
|                     | `name`                  | String         | Service identifier (e.g., Kubernetes service name).                                                                                                                                                                      | `"user-service"`                                                                                   |
|                     | `timeout`               | Duration       | Service-specific timeout override.                                                                                                                                                                             | `"3s"`                                                                                            |
|                     | `retries`               | RetrySpec      | Service-specific retry rules.                                                                                                                                                                                   | `{ "maxAttempts": 3, "backoff": "exponential" }`                                                 |
|                     | `circuitBreaker`        | CircuitBreaker | Circuit breaker rules (see Subschema below).                                                                                                                                                                     | `{ "threshold": 5, "resetTimeout": "10s" }`                                                      |
|                     | `rateLimiting`          | RateLimiter    | Rate limiting rules (see Subschema below).                                                                                                                                                                       | `{ "maxRequests": 100, "window": "1m" }`                                                         |
|                     | `fallback`              | FallbackSpec   | Fallback logic (e.g., local cache, degrade modes).                                                                                                                                                                   | `{ "type": "cache", "cacheKey": "requestId" }`                                                   |
| **RetrySpec**       | `maxAttempts`           | Integer        | Maximum retry attempts (0 = no retries).                                                                                                                                                                            | 3                                                                                                |
|                     | `backoff`               | String         | Backoff strategy: `"fixed"`, `"exponential"`, or custom function reference.                                                                                                                                         | `"exponential"`                                                                                   |
|                     | `backoffDuration`       | Duration       | Duration for backoff (e.g., `"1s"` for fixed delays).                                                                                                                                                                      | `"1s"`                                                                                            |
|                     | `includeMethods`        | Array[String]  | HTTP methods to retry (e.g., `["GET", "PUT"]`).                                                                                                                                                                       | `["GET"]`                                                                                         |
|                     | `excludeStatusCodes`    | Array[Int]     | HTTP status codes to exclude from retries (e.g., `[400, 401]`).                                                                                                                                                           | `[400, 401]`                                                                                       |
| **CircuitBreaker**  | `threshold`             | Integer        | Failures to trigger circuit open.                                                                                                                                                                                 | 5                                                                                                |
|                     | `resetTimeout`          | Duration       | Time until circuit closes after being open.                                                                                                                                                                       | `"10s"`                                                                                           |
|                     | `automaticReset`        | Boolean        | Whether to reset automatically after timeout.                                                                                                                                                                       | `true`/`false`                                                                                     |
|                     | `halfOpenRequests`      | Integer        | Requests allowed during half-open state.                                                                                                                                                                         | 2                                                                                                |
| **RateLimiter**     | `maxRequests`           | Integer        | Requests allowed per window.                                                                                                                                                                                     | 100                                                                                               |
|                     | `window`                | Duration       | Time window for rate limiting (e.g., `"1m"`).                                                                                                                                                                        | `"1m"`                                                                                            |
|                     | `burstCapacity`         | Integer        | Burst capacity (short-term spikes allowed).                                                                                                                                                                        | 50                                                                                                |
| **FallbackSpec**    | `type`                  | String         | Fallback strategy: `"cache"`, `"degradedResponse"`, or `"none"`.                                                                                                                                                     | `"cache"`                                                                                          |
|                     | `cacheKey`              | String         | Key for cached responses (e.g., `"{requestId}"`).                                                                                                                                                                    | `"{requestId}"`                                                                                     |
|                     | `degradedResponse`      | Object         | Custom degraded response payload.                                                                                                                                                                                 | `{ "status": "degraded", "data": "{}"]`                                                           |

---
### **3. Query Examples**
Resilience configurations are queried via:
- **API Gateway Config** (e.g., Istio `ConfigMap`):
  ```yaml
  apiVersion: config.istio.io/v1alpha2
  kind: ResilienceConfig
  metadata:
    name: user-service-config
  spec:
    version: v1.2
    services:
      - name: user-service
        timeout: 3s
        retries:
          maxAttempts: 3
          backoff: exponential
        circuitBreaker:
          threshold: 5
          resetTimeout: 10s
  ```
- **Resilience4j Integration** (Java):
  ```json
  {
    "services": [
      {
        "name": "inventory-service",
        "retries": {
          "maxAttempts": 5,
          "backoff": { "type": "exponential", "baseDuration": "100ms" }
        }
      }
    ]
  }
  ```
- **Kubernetes Sidecar Proxy**:
  ```bash
  kubectl apply -f - <<EOF
  configMap:
    data:
      resilience-config.yaml: |
        version: v1.1
        global:
          defaultTimeout: "2s"
        services:
          - name: auth-service
            rateLimiting:
              maxRequests: 50
              window: "1s"
  EOF
  ```

---
### **4. Implementation Details**
#### **Key Concepts**
- **Versioning**: Configurations are versioned (e.g., `v1.2`) to support backward compatibility. Use semantic versioning (MAJOR.MINOR.PATCH).
- **Overrides**: Service-specific rules override global defaults (e.g., `services.auth-service.timeout` overrides `global.defaultTimeout`).
- **Dynamic Updates**: Configurations can be hot-reloaded (e.g., via Kubernetes ConfigMaps or Redis pub/sub).
- **Validation**: Tools like [JSON Schema](https://json-schema.org/) validate configurations before runtime.

#### **Integration Patterns**
| **Framework**       | **Implementation Notes**                                                                                                                                                                                                 |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Resilience4j**    | Map schema fields to `Retry`, `CircuitBreaker`, and `RateLimiter` constructors.                                                                                                                                         |
| **Istio/Envoy**     | Use `ResilienceConfig` CRD to inject rules into Envoy filters.                                                                                                                                                     |
| **Spring Retry**    | Convert `RetrySpec` to `RetryTemplate` configurations.                                                                                                                                                               |
| **Kubernetes**      | Deploy as a `ConfigMap` and mount as environment variables.                                                                                                                                                       |
| **Serverless**      | Embed configurations in Lambda functions or API Gateway policies.                                                                                                                                                 |

#### **Performance Considerations**
- **Schema Size**: Keep configurations <5KB to avoid overhead in runtime serialization.
- **Cache Invalidation**: Invalidate resilience configs when updated (e.g., via cache tags in Redis).
- **Telemetry**: Log config loads for auditing (e.g., `"Applied config v1.2 for service X at 10:00:00"`).

---
### **5. Query Examples (Advanced)**
#### **Filtering by Service**
```sql
-- Pseudo-query to extract retries for "order-service"
SELECT retries FROM resilience_configs
WHERE services.name = 'order-service';
```
**Output**:
```json
{
  "maxAttempts": 4,
  "backoff": "exponential",
  "backoffDuration": "500ms"
}
```

#### **Validation Example**
```bash
# Validate against JSON Schema
jq -S . resilience-config.json > schema.json
jsonschema -i resilience-config.json schema.json
```
**Output** (if valid):
```
Validation passed.
```

---
### **6. Related Patterns**
| **Pattern**               | **Relationship**                                                                                                                                                                                                 | **When to Use Together**                                                                               |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Resilience Testing**    | Resilience configurations are inputs for chaos engineering tools (e.g., Gremlin, Chaos Mesh).                                                                                                               | Test configurations before production deployment.                                                       |
| **Circuit Breaker**       | Complimentary to Resilience Configuration; this pattern defines *where* to apply circuit breakers, while Circuit Breaker defines *how*.                                                                     | Combine to implement multi-tier resilience (e.g., regional vs. global breakers).                      |
| **Retry Policies**        | Retry rules are a subcomponent of Resilience Configuration; this pattern standardizes retry schemas.                                                                                                          | Use Retry Policies to define granular retry logic within configurations.                                 |
| **Service Mesh**          | Istio/Linkerd integrate with Resilience Configurations via sidecar proxies.                                                                                                                               | Deploy configurations alongside mesh policies for unified control.                                      |
| **Chaos Mesh**            | Chaos Mesh can inject resilience configs dynamically during experiments.                                                                                                                                         | Simulate failure modes with real-world resilience rules.                                               |

---
### **7. Best Practices**
1. **Start Global**: Define defaults to reduce duplication (e.g., `global.defaultTimeout`).
2. **Tag Configs**: Label configurations by environment (e.g., `env: prod`, `env: staging`).
3. **Monitor**: Track config changes via audit logs (e.g., `resilience-config-updates` table).
4. **Document**: Include examples in code comments or a `README.md` for each service’s config.
5. **Iterate**: Use feature flags to enable/disable configurations gradually.

---
### **8. Troubleshooting**
| **Issue**                          | **Root Cause**                                                                 | **Solution**                                                                                     |
|-------------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| Config not applied                  | Missing Kubernetes `ConfigMap` or sidecar injection.                            | Verify `env` variables or Istio `VirtualService` references.                                    |
| Retries failing to trigger          | `excludeStatusCodes` or `includeMethods` misconfigured.                          | Check logs for `HttpStatusCodeNotInRange` errors.                                              |
| Circuit breaker too aggressive      | `threshold` or `resetTimeout` set too low.                                       | Increase thresholds or implement gradual rollout.                                               |
| Rate limiting blocking requests     | `maxRequests` or `window` too restrictive.                                       | Adjust based on load testing metrics.                                                           |

---
### **9. Example: Full Configuration**
```yaml
version: v1.2
global:
  defaultTimeout: "4s"
  retryDefault:
    maxAttempts: 2
    backoff: fixed
    backoffDuration: "1s"
services:
  - name: payment-service
    timeout: "2s"
    retries:
      maxAttempts: 5
      backoff: exponential
      includeMethods: ["POST", "PUT"]
      excludeStatusCodes: [409, 429]
    circuitBreaker:
      threshold: 3
      resetTimeout: "30s"
      halfOpenRequests: 1
    rateLimiting:
      maxRequests: 10
      window: "1s"
  - name: notification-service
    fallback:
      type: cache
      cacheKey: "{requestId}"
```
---
**Appendices**
- [Resilience Configuration Schema (GitHub)](https://github.com/resilience4j/resilience-config-schema)
- [Istio Resilience Config CRD](https://istio.io/latest/docs/reference/config/istio.config.resilience.v1alpha2/)
- [Resilience4j Documentation](https://resilience4j.readme.io/docs)