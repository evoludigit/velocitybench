---
# **[Pattern] Retry Strategies and Backoff Patterns – Reference Guide**
*DevOps, Distributed Systems, and Resilience Best Practices*

---

## **1. Overview**
Transient failures (e.g., timeouts, throttling, network partitions) are inevitable in distributed systems. The **Retry Strategies and Backoff Patterns** mitigate these failures by automatically recuperating from temporary errors without manual intervention. Core principles include:
- **When to retry**: Only for transient errors (e.g., `5xx` HTTP codes, `ECONNREFUSED`).
- **How many times**: Configurable limits to avoid infinite loops.
- **How long to wait**: Exponential backoff with jitter prevents cascading failures when multiple clients retry simultaneously.

This pattern balances **reliability** (retries) and **efficiency** (delayed attempts), ensuring graceful failure recovery while minimizing resource waste.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**          | **Purpose**                                                                 | **Example Implementation**                     |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Retry Policy**       | Defines which operations/errors to retry and retry limits.                  | Retry `POST /payments` up to 3 times for `503`.  |
| **Backoff Strategy**   | Calculates delay between retries (e.g., exponential, linear).               | 1s → 2s → 4s → 8s (exponential).                |
| **Jitter**             | Adds randomness to delays to avoid synchronized retries (thundering herd). | ±30% variance on exponential backoff.           |
| **Max Retry Duration** | Hard limit to prevent excessive waiting (e.g., 1 hour total).               | Total retry time ≤ 3600s.                       |

### **2.2 Failure Modes to Handle**
Retry **only** transient failures (non-retryable errors should propagate immediately):
- **HTTP**: `429` (Too Many Requests), `5xx` (Server Errors).
- **Database**: `SQLTransientError` (e.g., connection timeouts).
- **Network**: `ECONNRESET`, `ETIMEDOUT`.

---
## **3. Schema Reference**

### **3.1 Retry Policy Schema**
| Field                | Type     | Description                                                                 | Default          |
|----------------------|----------|-----------------------------------------------------------------------------|------------------|
| `operation`          | String   | API/operation to retry (e.g., `POST /orders`).                             | Required         |
| `retryable_errors`   | Array    | List of error codes/patterns (e.g., `["5xx", "ServiceUnavailable"]`).     | `[]`             |
| `max_attempts`       | Integer  | Max retries (N = total attempts = N + 1).                                 | `3`              |
| `max_total_duration` | Duration | Soft timeout (e.g., `3600s`) to stop retries after.                        | `PT1H`           |
| `backoff_strategy`   | Enum     | `exponential`, `linear`, or `fixed`.                                       | `exponential`    |
| `jitter_enabled`     | Boolean  | Randomize delays to avoid herd problems.                                   | `true`           |
| `base_delay`         | Duration | Base delay for backoff (e.g., `1s`).                                       | `PT1S`           |
| `multiplier`         | Float    | Exponential multiplier (e.g., `2.0`).                                       | `2.0`            |

**Example Policy (JSON):**
```json
{
  "operation": "POST /payment/process",
  "retryable_errors": ["5xx", "ServiceUnavailable"],
  "max_attempts": 3,
  "backoff_strategy": "exponential",
  "jitter_enabled": true,
  "base_delay": "PT1S",
  "multiplier": 2.0
}
```

---
### **3.2 Backoff Algorithm Table**
| Strategy      | Formula                          | Example Sequence       | Use Case                          |
|---------------|----------------------------------|------------------------|-----------------------------------|
| **Exponential** | `delay = base_delay × multiplier<sup>attempt</sup>` + jitter | 1s, 2s, 4s, 8s          | Default; balances speed/retry.   |
| **Linear**     | `delay = base_delay × attempt`   | 1s, 2s, 3s, 4s         | Predictable delays (e.g., DB polls).|
| **Fixed**      | `delay = base_delay`             | 1s, 1s, 1s, 1s         | Low-variability workloads.       |

**Jitter Calculation**:
`delay ± (delay × jitter_percentage)`
*(Default: `±30%` of calculated delay.)*

---

## **4. Query Examples**

### **4.1 Retry with Exponential Backoff (Pseudocode)**
```python
def retry_operation(operation, max_attempts=3, base_delay=1, multiplier=2.0):
    attempt = 0
    while attempt < max_attempts:
        try:
            response = operation()
            return response  # Success
        except RetryableError as e:
            if attempt == max_attempts - 1:  # Final attempt
                raise  # Propagate non-retryable error
            delay = base_delay * (multiplier ** attempt)
            delay += random.uniform(-0.3, 0.3) * delay  # Jitter
            time.sleep(delay)
            attempt += 1
```

### **4.2 HTTP Client Implementation (cURL + Retry Logic)**
```bash
#!/bin/bash
MAX_ATTEMPTS=3
BASE_DELAY=1
MULTIPLIER=2

attempt=0
until [ $attempt -ge $MAX_ATTEMPTS ]; do
  response=$(curl -s -o /dev/null -w "%{http_code}" $URL)
  if [[ $response =~ ^[2-3][0-9]{2}$ ]]; then
    echo "Success on attempt $((attempt + 1))"
    exit 0
  fi

  delay=$((BASE_DELAY * $((2 ** attempt))))
  delay=$((delay + RANDOM % (delay * 3) / 10))  # ±30% jitter
  echo "Retrying in $delay seconds (attempt $((attempt + 1))/$MAX_ATTEMPTS)"
  sleep $delay
  ((attempt++))
done
echo "Max retries exceeded"
exit 1
```

### **4.3 Database Connection Retry (Python + SQLAlchemy)**
```python
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import time
import random

def connect_with_retry():
    engine = create_engine("postgresql://user:pass@db:5432/mydb")
    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        try:
            with engine.connect() as conn:
                return conn  # Success
        except OperationalError as e:
            if attempt == max_attempts - 1:
                raise
            delay = 1 * (2 ** attempt) + random.uniform(-0.3, 0.3) * (1 * (2 ** attempt))
            time.sleep(delay)
            attempt += 1
```

---
## **5. Configuration Examples**

### **5.1 Kubernetes Retry Policies (YAML)**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  template:
    spec:
      containers:
      - name: payment-service
        env:
        - name: RETRY_MAX_ATTEMPTS
          value: "3"
        - name: RETRY_BASE_DELAY
          value: "1s"
        - name: RETRY_STRATEGY
          value: "exponential"
        - name: RETRY_JITTER
          value: "true"
```

### **5.2 AWS Step Functions Retry Configuration**
```json
{
  "Heartbeat": {
    "Retry": [
      {
        "ErrorEquals": ["States.ALL"],
        "IntervalSeconds": 1,
        "MaxAttempts": 3,
        "BackoffRate": 2.0,
        "Jitter": true
      }
    ]
  }
}
```

---
## **6. Related Patterns**

| **Pattern**                     | **Relation**                                                                 | **Reference Guide**                     |
|----------------------------------|------------------------------------------------------------------------------|------------------------------------------|
| **Circuit Breaker**              | Complements retries by stopping repeated failures after a threshold.        | [Circuit Breaker Pattern]               |
| **Bulkhead Pattern**             | Limits concurrent retries to avoid resource exhaustion.                       | [Bulkhead Pattern]                      |
| **Rate Limiting**                | Controls retry frequency to avoid overwhelming systems.                     | [Rate Limiting]                         |
| **Idempotency**                  | Ensures retries don’t cause duplicate side effects (e.g., duplicate payments).| [Idempotency Pattern]                   |
| **Exponential Backoff (Standalone)** | Core algorithm used in this pattern for delay calculation.                | [Exponential Backoff]                   |

---
## **7. Best Practices & Anti-Patterns**

### **✅ Do:**
- **Retry only transient errors** (use logs to distinguish them).
- **Use jitter** to avoid synchronized retries.
- **Set max total duration** to prevent indefinite hangs.
- **Log retry attempts** for observability (e.g., `attempt 3/3: delay 8s`).

### **❌ Don’t:**
- **Retry non-idempotent operations** (e.g., `DELETE /user`).
- **Use fixed retries without backoff** (thundering herd risk).
- **Retry indefinitely** (always set `max_attempts`).
- **Ignore circuit breakers**—retries alone can’t solve persistent failures.

---
## **8. Tools & Libraries**
| **Language/Framework** | **Library**                          | Notes                                  |
|-------------------------|---------------------------------------|----------------------------------------|
| Python                  | `tenacity`, `urllib3`                 | Highly configurable retries.           |
| Java                    | `Resilience4j`, `Apache Retries`     | Integrates with Spring Boot.           |
| .NET                    | `Polly`                               | Extensive retry/backoff strategies.    |
| Go                      | `go-retry`                           | Lightweight retry logic.               |
| Kubernetes              | `retry-on-failure` (Custom Metrics)  | For pods/deployments.                  |
| AWS                     | `AWS SDK Retry Config`                | Built-in exponential backoff.          |

---
## **9. Troubleshooting**
| **Issue**                          | **Diagnosis**                                  | **Solution**                              |
|-------------------------------------|------------------------------------------------|-------------------------------------------|
| Infinite retries                    | Missing `max_attempts` or `max_total_duration`.| Set limits in retry policy.               |
| Thundering herd                     | No jitter or high concurrency.                | Enable jitter (`±30%`).                   |
| Retrying non-transient errors       | Misconfigured `retryable_errors`.             | Audit error logs; exclude `4xx` errors.   |
| Slow responses due to retries       | High `multiplier` or low `base_delay`.         | Adjust backoff parameters.                |

---
## **10. Further Reading**
- [AWS Retry Best Practices](https://docs.aws.amazon.com/general/latest/gr/random.html#amazon-retry-scenarios)
- [Exponential Backoff in Distributed Systems](https://www.awsarchitectureblog.com/2015/03/backoff.html)
- [Resilience Patterns (Microsoft)](https://docs.microsoft.com/en-us/dotnet/architecture/microservices/resilient-applications/implement-retry-mechanism)