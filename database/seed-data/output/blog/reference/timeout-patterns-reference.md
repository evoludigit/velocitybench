# **[Pattern] Timeout & Deadline Patterns – Reference Guide**

---

## **Overview**
The **Timeout & Deadline Patterns** address critical software reliability concerns by enforcing constraints on execution time for operations, preventing indefinite hangs, and mitigating risks like resource exhaustion or deadlocks. These patterns apply to synchronous and asynchronous systems, distributed services, and user-facing applications where responsiveness is paramount.

By implementing timeouts or deadlines, developers can:
- Gracefully fail slow operations instead of waiting indefinitely.
- Reduce latency for end-users by terminating unresponsive calls.
- Protect system stability in fault-tolerant architectures.
- Automate retry mechanisms for transient failures.

This guide covers core concepts, implementation strategies, schema references, and practical examples for real-world scenarios.

---

## **Key Concepts**
### **1. Timeout vs. Deadline**
| **Term**   | **Definition**                                                                 | **Use Case**                                                                 |
|------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Timeout**| A hard limit on how long a single operation (e.g., API call, database query) can execute. | Short-lived requests (e.g., REST APIs, CLI commands).                       |
| **Deadline**| A relative or absolute time by which a set of coordinated operations must complete. | Long-running workflows, distributed transactions, or batch processing.      |

### **2. Timeout Behavior Strategies**
| **Strategy**       | **Description**                                                                 | **Example Scenarios**                                                   |
|--------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Fail Fast**      | Immediate error after timeout (no retry).                                       | Critical system operations (e.g., authentication, authz checks).          |
| **Retry with Backoff** | Exponential delay before retrying (e.g., 1s, 2s, 4s).                       | Transient failures (network instability, database timeouts).              |
| **Cancel & Fallback** | Abort operation and switch to a backup (e.g., cache, alternative service).   | High-priority requests where reliability > speed (e.g., payment processing). |
| **Degrade Gracefully** | Limit functionality or degrade performance (e.g., downgrade images).       | User-facing apps with non-critical features.                              |

---

## **Implementation Details**

### **3. Schema Reference**
Below are key schema elements for designing timeout/deadline systems.

#### **3.1 Core Schemas**
| **Schema**               | **Description**                                                                 | **Example Values**                                                          |
|--------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `OperationTimeout`       | Configures timeout duration for a single operation (e.g., request/method).    | `"timeout": "3s"`, `"timeout": "PT5M"` (ISO 8601).                          |
| `Deadline`               | Defines a relative (`since_start`) or absolute (`at`) time limit for workflows.   | `"deadline": {"since_start": "PT1H"}`; `"deadline": {"at": "2024-01-01T00:00:00Z"}`. |
| `RetryPolicy`            | Rules for retrying failed operations with timeouts.                            | `"max_retries": 3, "backoff_factor": 2.0, "timeout": "10s"`.                |
| `FallbackStrategy`       | Actions to take if a timeout occurs (e.g., cache, default value).             | `"fallback": {"type": "cache", "ttl": "30m"}`.                              |
| `MonitoringAlert`        | Configures alerts for repeated timeouts (e.g., Prometheus rules).             | `{"threshold": "5", "window": "5m", "severity": "critical"}`.              |

#### **3.2 Example: API Endpoint Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["get_user", "process_payment", "fetch_logs"]
    },
    "timeout": {
      "type": "string",
      "format": "duration",
      "example": "PT5S"
    },
    "deadline": {
      "type": "object",
      "properties": {
        "since_start": { "type": "string", "format": "duration" },
        "at": { "type": "string", "format": "date-time" }
      }
    },
    "retry_policy": {
      "type": "object",
      "properties": {
        "max_retries": { "type": "integer", "minimum": 0 },
        "backoff": { "type": "object", "properties": { "factor": { "type": "number" } } }
      }
    }
  },
  "required": ["operation", "timeout"]
}
```

---
## **Query Examples**

### **4.1 Timeout Configuration in Code**
#### **4.1.1 Synchronous Example (Python)**
```python
from concurrent.futures import TimeoutError

def fetch_data_with_timeout(url: str, timeout_seconds: int = 3):
    try:
        response = requests.get(url, timeout=timeout_seconds)
        return response.json()
    except TimeoutError:
        raise TimeoutError(f"Request to {url} timed out after {timeout_seconds}s")
```

#### **4.1.2 Asynchronous Example (JavaScript/TypeScript)**
```typescript
async function fetchWithTimeout(url: string, timeoutMs: number = 3000): Promise<any> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    return await response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    throw new Error(`Request timed out: ${err.message}`);
  }
}
```

#### **4.1.3 Deadline in Distributed Workflows (gRPC)**
```protobuf
service OrderProcessing {
  rpc PlaceOrder (OrderRequest) returns (OrderResponse) {
    option (google.api.deadline = "300"); // 5-minute deadline
  }
}
```

### **4.2 Retry Policy Implementation (Go)**
```go
package main

import (
	"time"
	"github.com/hashicorp/go-retry"
	"github.com/google/uuid"
)

func retryWithBackoff(op func() error, maxRetries int, initialInterval time.Duration) error {
	retryable := retry.NewExponentialBackoff(
		retry.Backoff{
			Initial: initialInterval,
			Factor:  2.0,
			Max:     time.Minute,
		},
	)
	return retry.Do(retryable, func() error {
		return op()
	})
}

// Usage:
err := retryWithBackoff(
    func() error {
        // Call slow operation (e.g., database query)
        return doExpensiveQuery()
    },
    3,
    1*time.Second,
)
```

### **4.3 Fallback Strategy (Kubernetes)**
```yaml
# Deployment with fallback pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
        startupProbe:
          exec:
            command: ["curl", "http://localhost:8080/health"]
          initialDelaySeconds: 5
          timeoutSeconds: 3  # Timeout for probe
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Circuit Breaker**              | Limits retry attempts and fails fast to avoid cascading failures.               | High-availability systems with external dependencies (e.g., payment gateways). |
| **Bulkhead**                     | Isolates resource usage to prevent one operation from starving others.          | Multi-tenant services with shared resources (e.g., databases).                 |
| **Retry with Jitter**            | Adds random delays between retries to avoid thundering herd.                   | Distributed systems with transient failures (e.g., microservices).             |
| **Rate Limiting**                | Controls request volume to prevent overload.                                  | APIs with variable workloads (e.g., public APIs).                              |
| **Saga Pattern**                 | Manages distributed transactions with compensating actions.                   | Workflows spanning multiple services (e.g., order processing).                 |

---

## **Best Practices**
1. **Default Timeouts**: Configure sensible defaults (e.g., 30s for APIs, 5m for batch jobs).
2. **Monitoring**: Track timeout failures (e.g., Prometheus metrics for `http_request_duration_seconds`).
3. **Logging**: Log timeout events with contextual data (e.g., request ID, operation type).
4. **Testing**: Simulate timeouts in integration tests (e.g., mock slow databases).
5. **Documentation**: Clearly communicate timeouts/deadlines to consumers (e.g., API docs).

---
## **Anti-Patterns**
- **Unbounded Timeouts**: Avoid `"timeout": "infinity"`; always enforce limits.
- **No Retry Logic**: Failing silently may mask transient issues.
- **Ignoring Deadlines**: Skipping deadlines can lead to missed SLOs (Service Level Objectives).
- **Over-Retrying**: Exponential backoff should cap at a reasonable max (e.g., 1 minute).