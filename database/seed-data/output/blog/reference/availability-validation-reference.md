**[Pattern] Availability Validation Reference Guide**

---

### **1. Overview**
**Availability Validation** ensures that a service, resource, or endpoint is operational before proceeding with a transaction or request. This pattern prevents failed operations due to unavailability, improving system resilience and reliability. It is commonly used in microservices, distributed architectures, and client-server interactions to validate if downstream services are reachable, healthy, and capable of fulfilling requests.

Key use cases:
- **Pre-flight checks** (e.g., checking database connectivity before querying).
- **Circuit breaker fallback** (e.g., using a secondary endpoint if primary fails).
- **Rate limiting or throttling validation** (e.g., verifying API quotas before execution).
- **Dependency health monitoring** (e.g., ensuring a payment gateway is active before processing transactions).

This pattern is distinct from **retries** or **timeouts**, as it focuses on *proactively* validating availability before any work begins.

---

### **2. Implementation Details**

#### **2.1 Key Concepts**
| Concept               | Description                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------|
| **Proxy/Adapter**     | Acts as an intermediary to validate availability before forwarding requests.                  |
| **Health Check Endpoint** | A dedicated endpoint (e.g., `/health`) that returns a status (e.g., `200 OK` or `503`).        |
| **Validation Threshold** | The acceptable response time or success rate (e.g., "99.9% uptime required").              |
| **Fallback Strategy** | Alternative actions if validation fails (e.g., retry, queue, or return a degraded response). |

#### **2.2 Architecture Patterns**
1. **Direct Validation**
   - Client polls a health endpoint before sending requests.
   - Example: `GET /api/v1/payment-gateway/health`.

2. **Proxy-Based Validation**
   - A service proxy (e.g., API Gateway) validates dependencies before routing requests.
   - Example: Kong, AWS API Gateway, or custom load balancer checks.

3. **Sidecar Validation**
   - A sidecar container (e.g., Istio, Linkerd) monitors pod health in Kubernetes.
   - Example: Sidecar injects validation logic via Envoy proxies.

4. **Client-Side Validation**
   - Client libraries (e.g., Python `requests`, JavaScript `fetch`) integrate validation logic.
   - Example: Retry with exponential backoff if health check fails.

---

### **3. Schema Reference**
Below is a standardized schema for defining **Availability Validation** configurations.

#### **3.1 Validation Configuration Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AvailabilityValidationConfig",
  "description": "Configuration for validating resource availability.",
  "type": "object",
  "properties": {
    "target": {
      "type": "string",
      "description": "Endpoint or service to validate (e.g., 'http://payments-service:8080')."
    },
    "healthCheckEndpoint": {
      "type": "string",
      "description": "Path to health endpoint (default: '/health').",
      "default": "/health"
    },
    "method": {
      "type": "string",
      "enum": ["GET", "POST", "HEAD"],
      "description": "HTTP method for health check.",
      "default": "GET"
    },
    "timeout": {
      "type": "integer",
      "description": "Timeout in milliseconds for the health check.",
      "minimum": 100
    },
    "acceptableStatusCodes": {
      "type": "array",
      "items": {
        "type": "integer"
      },
      "description": "HTTP status codes considered 'healthy' (e.g., [200, 204])."
    },
    "validationInterval": {
      "type": "integer",
      "description": "How often to re-check availability (in seconds).",
      "minimum": 5
    },
    "fallbackStrategy": {
      "type": "object",
      "properties": {
        "retryCount": { "type": "integer", "minimum": 0 },
        "retryDelay": { "type": "integer", "minimum": 100 },
        "queue": { "type": "string", "description": "Queue to enqueue failed requests." },
        "degradeResponse": {
          "type": "object",
          "properties": {
            "statusCode": { "type": "integer" },
            "message": { "type": "string" }
          }
        }
      }
    }
  },
  "required": ["target", "acceptableStatusCodes"]
}
```

#### **3.2 Example Valid Configuration**
```json
{
  "target": "http://payments-service:8080",
  "healthCheckEndpoint": "/ready",
  "method": "GET",
  "timeout": 2000,
  "acceptableStatusCodes": [200, 204],
  "validationInterval": 10,
  "fallbackStrategy": {
    "retryCount": 3,
    "retryDelay": 500,
    "degradeResponse": {
      "statusCode": 503,
      "message": "Service temporarily unavailable. Retrying..."
    }
  }
}
```

---

### **4. Query Examples**

#### **4.1 Direct Validation (HTTP)**
**Request:**
```http
GET /api/v1/payments-service/health HTTP/1.1
Host: payments-service:8080
Accept: application/json
```

**Successful Response (200 OK):**
```json
{
  "status": "healthy",
  "lastChecked": "2023-10-01T12:00:00Z",
  "dependencies": [
    { "name": "database", "status": "healthy" },
    { "name": "gateway", "status": "degraded" }
  ]
}
```

**Failed Response (503 Service Unavailable):**
```json
{
  "error": "Service unavailable",
  "retryAfter": 30
}
```

---

#### **4.2 Proxy-Based Validation (Istio Sidecar)**
**Istio `DestinationRule` Example:**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: payment-service-dr
spec:
  host: payments-service
  trafficPolicy:
    loadBalancer:
      simple: ROUND_ROBIN
    outlierDetection:
      consecutiveErrors: 5
      interval: 5s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

**Effect:**
- Istio sidecar automatically ejects unhealthy pods and retries requests.

---

#### **4.3 Client-Side Validation (Python)**
```python
import requests
from requests.exceptions import RequestException

def validate_availability(target: str, timeout: int = 2) -> bool:
    try:
        response = requests.get(
            f"{target}/health",
            timeout=timeout
        )
        return response.status_code in [200, 204]
    except RequestException:
        return False
```

**Usage:**
```python
if not validate_availability("http://payments-service"):
    print("Service unavailable. Falling back to backup.")
```

---

### **5. Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Circuit Breaker**         | Temporarily stops requests to a failing service to prevent cascading failures.              | When a dependency fails repeatedly (e.g., database timeouts).              |
| **Bulkhead**                | Isolates resource usage (e.g., threads/processes) to prevent one dependent from overwhelming another. | When a service has limited capacity (e.g., a single-threaded queue).      |
| **Retry with Backoff**      | Retries failed requests with increasing delays to avoid thundering herd.                  | When transient failures are expected (e.g., network blips).                |
| **Load Shedding**           | Drops requests during peak load to maintain performance.                                    | During traffic spikes to prioritize critical requests.                     |
| **Resilience Patterns**     | Collection of patterns (e.g., Retry, Circuit Breaker, Fallback) for building resilient systems. | For comprehensive fault tolerance in distributed systems.                  |

---
### **6. Best Practices**
1. **Minimize Validation Overhead**
   - Keep health checks lightweight (e.g., avoid complex queries).
   - Cache results if validation frequency is high.

2. **Define Clear SLAs**
   - Document acceptable downtime (e.g., "99.95% uptime").

3. **Leverage Standardized Endpoints**
   - Use `/health`, `/ready`, or `/live` for consistency (see [OpenTelemetry Health Checks](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/telemetry/health.md)).

4. **Log and Monitor**
   - Track validation failures and response times (e.g., using Prometheus or Datadog).

5. **Graceful Degradation**
   - Provide fallback responses (e.g., degraded API responses) instead of outright failures.

---
### **7. Tools & Libraries**
| Tool/Library               | Description                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------|
| **Istio**                  | Service mesh for proxy-based validation and traffic management.                              |
| **AWS CloudWatch**         | Monitor health checks and set alarms for failures.                                          |
| **Prometheus + Grafana**   | Track availability metrics and visualize trends.                                            |
| **Resilience4j** (Java)    | Library for implementing Circuit Breakers, Retries, and Bulkheads.                          |
| **Hystrix** (Legacy)       | Netflix’s resilience library (replaced by Resilience4j).                                     |
| **Kubernetes LivenessProbe** | Built-in probe for validating container health in Kubernetes.                                |

---
### **8. Anti-Patterns**
- **Over-Policing**
  Avoid validating every minor dependency (e.g., a CDN endpoint) unless critical.
- **Long Validation Timeouts**
  Set reasonable timeouts (e.g., 2s) to avoid blocking requests unnecessarily.
- **Ignoring Failures**
  Always implement fallback strategies (e.g., retries, queues) when validation fails.
- **Hardcoding Thresholds**
  Make validation intervals and status codes configurable for flexibility.