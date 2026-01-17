# **[Pattern] Latency Configuration Reference Guide**
*Optimizing System Responsiveness with Granular Latency Controls*

---

## **Overview**
Latency configuration patterns enable precise control over system responsiveness by defining upper bounds on message propagation, service calls, or data retrieval delays. This ensures predictable performance, avoids cascading failures, and adheres to SLAs. Implementations typically involve:
- **Timeouts**: Hard limits on operations (e.g., HTTP requests, database queries).
- **Retries/Backoff**: Exponential or constant delays between retries.
- **Prioritization**: Adjusting latency thresholds for critical vs. non-critical workflows.
- **Degradation Mechanisms**: Fallback responses when latency exceeds thresholds.

Use this guide to design, validate, and enforce latency configurations across microservices, distributed systems, or cloud-native architectures.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**               | **Description**                                                                 | **Implementation Examples**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **Latency Threshold**       | Maximum acceptable delay (e.g., 500ms for API responses).                     | Configured in config files, environment variables, or metadata.                              |
| **Timeout Mechanism**       | Enforces thresholds via timeout exceptions (e.g., `TimeoutError`).              | Libraries: Apache HttpClient (connection timeout), gRPC (deadline).                         |
| **Monitoring Tool**         | Tracks latency (e.g., Prometheus, Datadog).                                   | Alerts if thresholds breach SLAs (e.g., `latency_p99 > 1s`).                                |
| **Degradation Strategy**    | Graceful fallback when latency exceeds thresholds.                            | Cache invalidation, circuit breakers (e.g., Resilience4j), or degraded UI responses.       |
| **Dynamic Adjustment**      | Runtime scaling of thresholds based on load (e.g., Kubernetes HPA).           | Use metrics like `CPUUsage` or `RequestRate` to adjust thresholds.                        |

---

### **2. Latency Types**
| **Type**               | **Scope**               | **Use Case**                                                                 | **Example**                                                                 |
|------------------------|-------------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Request-Level**      | Individual API calls    | Prevent hang-ups in user-facing flows.                                      | FastAPI timeout middleware: `@app.middleware("http") async def timeout_middleware(...)` |
| **Service-Level**      | Inter-service calls    | Avoid downstream latency cascades.                                          | gRPC `Deadline`: `client.call(deadline=5s)`.                               |
| **Global**             | System-wide            | Hard limits for critical infrastructure (e.g., auth services).              | Kubernetes Pod Disruption Budgets (PDBs) to limit eviction time.            |
| **User-Defined**       | Custom workflows        | Business logic-dependent delays (e.g., analytics).                         | Custom interceptor in Spring Boot: `@Around("execution(* com.company..*.*(..))")`. |

---

## **Schema Reference**
### **1. Latency Configuration Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LatencyConfig",
  "type": "object",
  "properties": {
    "globalTimeout": {
      "description": "Default timeout for all operations (in ms).",
      "type": "integer",
      "minimum": 10
    },
    "services": {
      "type": "object",
      "patternProperties": {
        "^[a-zA-Z0-9_-]+$": {
          "type": "object",
          "properties": {
            "requestTimeout": {"type": "integer", "minimum": 10},
            "maxRetries": {"type": "integer", "minimum": 0},
            "backoff": {
              "type": "object",
              "properties": {
                "strategy": {"enum": ["exponential", "constant"]},
                "factor": {"type": "number", "minimum": 1.0},
                "maxDelay": {"type": "integer"}
              }
            },
            "fallback": {
              "type": "object",
              "properties": {
                "enabled": {"type": "boolean"},
                "response": {"type": "string"}
              }
            }
          }
        }
      }
    }
  },
  "required": ["globalTimeout"]
}
```

### **2. Example Valid Configuration**
```json
{
  "globalTimeout": 3000,
  "services": {
    "auth-service": {
      "requestTimeout": 1500,
      "maxRetries": 3,
      "backoff": {
        "strategy": "exponential",
        "factor": 2,
        "maxDelay": 10000
      },
      "fallback": {
        "enabled": true,
        "response": "{\"error\": \"Authentication service unavailable\"}"
      }
    },
    "analytics": {
      "requestTimeout": 8000
    }
  }
}
```

---

## **Query Examples**
### **1. Configuring Timeouts in Python (FastAPI)**
```python
from fastapi import FastAPI, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import httpx

app = FastAPI()

@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
        try:
            response = await client.get("https://api.example.com/data")
            return JSONResponse(response.json())
        except httpx.TimeoutException:
            return JSONResponse({"error": "Request timed out"})
```

### **2. gRPC Deadline Configuration (Go)**
```go
import (
	"context"
	"time"
	"google.golang.org/grpc"
)

func callService(client UserServiceClient) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	_, err := client.GetUser(ctx, &pb.UserRequest{Id: 123})
	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			log.Println("Request timed out")
		} else {
			log.Printf("Error: %v", err)
		}
	}
}
```

### **3. Kubernetes Pod Disruption Budget (YAML)**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: critical-service-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: critical-service
  disruptAllowed: false  # Prevents disruptions exceeding latency SLA
```

### **4. Spring Boot Retry Configuration (XML)**
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:retry="http://www.springframework.org/schema/retry"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="...">
  <retry:retry policy-id="myRetryPolicy">
    <retry:constant-attempts value="3" />
    <retry:back-off policy-id="myBackOffPolicy" />
  </retry:retry>

  <retry:back-off policy-id="myBackOffPolicy">
    <retry:fixed-back-off initial-interval="1000" multiplier="2" />
  </retry:back-off>
</beans>
```

---

## **Query Examples (CLI/Configuration Tools)**
### **1. Update Latency Config via Kubernetes ConfigMap**
```bash
kubectl create configmap latency-config \
  --from-literal=globalTimeout=3000 \
  --from-literal=auth.requestTimeout=1500 \
  --dry-run=client -o yaml | kubectl apply -f -
```

### **2. Validate Schema with JSON Schema Validator**
```bash
jq -S '. | test("$.globalTimeout > 0")' config.json
# Output: true/false
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Circuit Breaker**              | Prevents cascading failures by stopping requests to failing services.         | High-availability systems with unpredictable latency spikes.                     |
| **Retry with Jitter**           | Randomizes retry delays to avoid thundering herds.                           | Distributed systems with bursty traffic.                                      |
| **Bulkheading**                 | Isolates latency-sensitive operations to prevent resource contention.        | Systems with mixed workloads (e.g., batch + real-time).                       |
| **Degradation Strategies**       | Gradually reduces functionality under latency pressure.                      | Web apps needing to maintain partial functionality during outages.             |
| **Asynchronous Processing**      | Offloads latency to background queues (e.g., Kafka, RabbitMQ).                | Long-running tasks (e.g., report generation).                                  |
| **Local Cache**                 | Reduces latency for repetitive requests.                                     | Read-heavy workloads (e.g., user sessions).                                   |

---

## **Best Practices**
1. **Start Conservative**: Set thresholds 10–20% above baseline latency to account for noise.
2. **Monitor & Alert**: Use tools like Prometheus to track `latency_p99` metrics.
3. **Prioritize Critical Paths**: Apply stricter thresholds to user-facing services.
4. **Test Under Load**: Simulate latency spikes with tools like **Chaos Mesh** or **Locust**.
5. **Document SLAs**: Clearly define latency requirements for each service tier.
6. **Avoid "Busy Waiting"**: Prefer async I/O (e.g., `async/await`) over polling loops.

---
**See Also**:
- [Resilience4j Circuit Breaker Documentation](https://resilience4j.readme.io/docs/circuitbreaker)
- [gRPC Timeouts and Deadlines](https://grpc.io/docs/guides/timeouts/)
- [Kubernetes QoS Classes](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/)