# **[Pattern] Circuit Breaker Reference Guide**

---

## **Overview**
The **Circuit Breaker Pattern** is a resilience mechanism that prevents cascading failures in distributed systems by temporarily disabling calls to a failing service. Inspired by electrical circuit breakers, this pattern "trips" when failure rates exceed a predefined threshold, blocking subsequent requests until a recovery timeout period elapses. During this period, the breaker allows sporadic test requests (*half-open state*) to verify if the service has recovered.

This pattern mitigates:
- **Downtime amplification** (where a single failure propagates across a system)
- **Resource exhaustion** (unnecessary retries consuming limited quotas)
- **Latency spikes** (resulting from repeated timeouts)

Circuit breakers are typically implemented using libraries (e.g., Resilience4j, Hystrix) but can be custom-built with stateful logic.

---

## **Schema Reference**
Below are key attributes and states of a circuit breaker implementation:

| **Attribute**          | **Description**                                                                                     | **Default (Common Libraries)**                     |
|------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Failure Threshold**  | Number of failures before tripping the circuit (e.g., 5 failures).                                 | 5                                                  |
| **Success Threshold**  | Number of successful test calls in *half-open* state to reset the circuit.                         | 1 (default) or configurable (e.g., 3)            |
| **Cooling Period**     | Duration (time window) after tripping before allowing test requests (e.g., 1 minute).               | 30s–5 minutes                                     |
| **Timeout**            | Max duration for a single call to the failing service before counting as a failure.                  | 60s                                                |
| **Ignore Exceptions**  | List of exceptions to *not* count toward the failure threshold (e.g., `TimeoutException`).          | `TimeoutException`                                 |
| **Metrics**            | Tracked metrics: failure count, state transitions, request/response times.                          | Prometheus/Grafana endpoints                      |
| **State**              | Current breaker state: `Closed`, `Open`, or `Half-Open`.                                            | —                                                  |

---

## **Key States**
1. **Closed**
   - Default state; calls proceed normally.
   - Failure count resets after each successful call.

2. **Open**
   - Tripped after exceeding `Failure Threshold`.
   - All new calls immediately fail with `CircuitBreakerOpenException`.
   - No calls are allowed until the `Cooling Period` expires.

3. **Half-Open**
   - After the cooling period, a *limited* number of calls (often 1) are permitted to test recovery.
   - If the test succeeds, the breaker resets to `Closed`.
   - If it fails, the breaker re-opens and starts the cooling period again.

---

## **Implementation Details**
### **Core Logic**
1. **Track Failures**
   - Increment a counter for each failed call (excluding ignored exceptions).
   - Reset the counter on successful calls when the breaker is `Closed`.

2. **State Transitions**
   - **Closed → Open**: When `failureCount >= Failure Threshold`.
   - **Open → Half-Open**: After `Cooling Period` elapses.
   - **Half-Open → Closed/Open**:
     - Success: Reset counter, return to `Closed`.
     - Failure: Increment counter; if threshold exceeded, re-open.

3. **Testing Recovery**
   - In *Half-Open* state, allow **1 call** (default) to verify service health.
   - Adjust `Success Threshold` to require multiple successes (e.g., 3) for confidence.

### **Pseudo-Code Example**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, cooling_period=30):
        self.failure_threshold = failure_threshold
        self.cooling_period = cooling_period
        self.state = "Closed"
        self.failure_count = 0
        self.last_trip_time = 0

    def call(self, service_call):
        if self.state == "Open":
            if time.time() - self.last_trip_time > self.cooling_period:
                self.state = "Half-Open"
            else:
                raise CircuitBreakerOpenException()

        try:
            result = service_call()
            if self.state == "Closed":
                self.failure_count = 0
            return result
        except Exception as e:
            if self.state != "Open" and not self._should_ignore(e):
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self.state = "Open"
                    self.last_trip_time = time.time()
                raise

    def _should_ignore(self, e):
        return isinstance(e, TimeoutException)
```

### **Common Tuning Parameters**
| **Parameter**          | **Recommendation**                                                                                     | **Example Values**                          |
|------------------------|-------------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Failure Threshold**  | Adjust based on tolerance (e.g., 3 for critical services, 10 for less critical).                      | 5                                             |
| **Cooling Period**     | Balance recovery time vs. user impact (e.g., 1 minute for APIs, 5 minutes for batch jobs).          | 30s–300s                                     |
| **Timeout**            | Set to match service SLA (e.g., 1s for REST APIs, 30s for synchronous calls).                         | 1s–60s                                       |
| **Success Threshold**  | Require multiple successes if false positives are likely (e.g., 3).                                    | 1 (default) or 3                             |

---

## **Query Examples**
### **1. Using Resilience4j (Java)**
```java
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;

CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50) // Percentage (50% = 5 failures out of 10)
    .waitDurationInOpenState(Duration.ofSeconds(30))
    .slidingWindowSize(10)
    .slidingWindowType(CircuitBreakerConfig.SlidingWindowType.COUNT_BASED)
    .build();

CircuitBreaker breaker = CircuitBreakerRegistry.of(config).circuitBreaker("paymentService");

try {
    breaker.executeSupplier(() -> callExternalPaymentService());
} catch (Exception e) {
    log.error("Payment service failed: {}", e.getMessage());
}
```

### **2. Using Python (`resilipy` Library)**
```python
from resilipy.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    reset_timeout=30,  # Cooling period in seconds
    success_threshold=1,
)

@breaker
def call_api():
    response = requests.get("https://api.example.com/data")
    return response.json()
```

### **3. Custom Implementation (Node.js)**
```javascript
const { CircuitBreaker: Breaker } = require("opossum");

const breaker = new Breaker({
    timeout: 3000,
    errorThresholdPercentage: 50, // 5 failures in 10 calls
    resetTimeout: 30000,          // Cooling period
    onStateChange: (state) => {
        console.log(`Breaker state changed to: ${state}`);
    },
});

breaker.execute(async () => {
    const result = await fetch("https://api.example.com/data");
    return result.json();
}).catch(err => {
    console.error("Breaker open:", err);
});
```

---

## **Configuration Best Practices**
1. **Dynamic Thresholds**
   - Adjust thresholds based on traffic patterns (e.g., higher thresholds for peak hours).
   - Use **adaptive circuit breakers** (e.g., [Resilience4j’s dynamic config](https://resilience4j.readme.io/docs/circuitbreaker#dynamic-configuration)).

2. **Metrics Integration**
   - Expose Prometheus metrics for monitoring:
     ```promql
     circuit_breaker_failure_count_total{service="payments"}
     circuit_breaker_state{service="payments"} == "OPEN"
     ```

3. **Fallback Mechanisms**
   - Combine with **Fallback Pattern** (e.g., return cached data or a degraded response).
   - Example:
     ```python
     @breaker
     def get_user_data(user_id):
         data = cache.get(user_id)
         if data:
             return data
         raise Exception("No cached data")
     ```

4. **Bulkhead Integration**
   - Use with **Bulkhead Pattern** to limit concurrent calls:
     ```java
     BulkheadConfig bulkheadConfig = BulkheadConfig.custom()
         .maxConcurrentCalls(5)
         .maxWaitDuration(Duration.ofMillis(50))
         .build();

     Bulkhead bulkhead = Bulkhead.of("paymentBulkhead", bulkheadConfig);
     breaker.executeRunnable(() -> bulkhead.run(() -> callPaymentService()));
     ```

5. **Graceful Degradation**
   - Log failures and alert when the breaker trips:
     ```python
     @breaker(on_error=log_failure)
     def fetch_data():
         ...
     ```

---

## **Query Examples: Monitoring & Alerts**
### **1. Detecting Open Breakers (Prometheus)**
```promql
# Alert if a breaker is open for >5 minutes
alert CircuitBreakerOpen {
  labels:
    severity: warning
  annotations:
    summary: "Breaker {{ $labels.service }} is open"
  for: 5m
  circuit_breaker_state{state="OPEN"} > 0
}
```

### **2. Failure Rate Over Time**
```promql
# Rate of failures in the last 5 minutes
rate(circuit_breaker_failure_count_total[5m]) by (service)
```

### **3. Cooling Period Elapsed**
```promql
# Time since last trip (for cooling period tracking)
time() - circuit_breaker_last_trip_time_seconds{state="OPEN"}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use Together**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Retry Pattern**         | Automatically retries failed operations (with backoff).                                             | Use **Retry** only when the circuit is `Closed`; avoid retries when the breaker is `Open`. |
| **Fallback Pattern**      | Provides alternative responses when a call fails.                                                    | Combine with Circuit Breaker to return cached or degraded data when the service is down. |
| **Bulkhead Pattern**      | Limits concurrency to prevent resource exhaustion.                                                   | Use **Bulkhead** alongside Circuit Breaker to control thread pools for downstream services. |
| **Rate Limiting**         | Throttles requests to avoid overload.                                                               | Circuit Breaker + Rate Limiting = defense-in-depth (fail fast vs. slow down).         |
| **Bulkhead with Thread Pool** | Isolates failures to specific thread pools.                                                         | Isolate critical services (e.g., payments) in their own thread pool.                   |
| **Asynchronous Processing** | Offloads non-critical work to queues (e.g., Kafka, RabbitMQ).                                     | Use for long-running calls where immediate failure isn’t critical.                     |

---

## **Anti-Patterns & Pitfalls**
1. **Over-Reliance on Retries**
   - *Problem*: Retrying an `Open` breaker wastes resources and delays recovery.
   - *Fix*: Only retry when the breaker is `Closed`.

2. **Ignoring Too Many Exceptions**
   - *Problem*: Excluding all exceptions (e.g., `NetworkException`) may mask critical errors.
   - *Fix*: Ignore only transient exceptions (e.g., timeouts, connection resets).

3. **Static Thresholds**
   - *Problem*: Fixed thresholds (e.g., 5 failures) don’t adapt to traffic spikes.
   - *Fix*: Use dynamic thresholds or percentile-based metrics.

4. **No Monitoring**
   - *Problem*: Unmonitored breakers lead to undetected outages.
   - *Fix*: Integrate with observability tools (Prometheus, Datadog).

5. **Long Cooling Periods**
   - *Problem*: Extended cooling periods degrade user experience.
   - *Fix*: Balance recovery time with SLA requirements.

---

## **Example Use Cases**
| **Scenario**               | **Circuit Breaker Role**                                                                         | **Parameters**                                      |
|----------------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Payment Gateway**        | Prevent payment failures from crashing a shopping cart.                                         | `FailureThreshold=3`, `CoolingPeriod=1m`           |
| **External API**           | Avoid cascading failures if a 3rd-party API is down.                                            | `Timeout=2s`, `IgnoreExceptions=[TimeoutException]` |
| **Batch Processing Job**   | Skip failed records instead of halting the entire job.                                          | `FailureThreshold=10`, `CoolingPeriod=5m`          |
| **Microservice Dependency** | Isolate failures between services (e.g., `auth-service` → `payment-service`).                 | `SuccessThreshold=2` (require 2 successful tests)   |
| **IoT Device Fleet**       | Retry failed cloud uploads a limited number of times before giving up.                           | `RetryCount=3` (in combination with Circuit Breaker) |

---

## **Tools & Libraries**
| **Language/Framework** | **Library**               | **Key Features**                                                                 |
|-------------------------|---------------------------|---------------------------------------------------------------------------------|
| Java                    | Resilience4j              | Reactive/Spring Boot support, metrics, dynamic config.                           |
| Java/Kotlin             | Hystrix (Legacy)          | Circuit Breaker, Bulkhead, Retry, Fallback.                                       |
| Python                  | `resilipy`                | Lightweight, integrates with `requests`/`aiohttp`.                              |
| JavaScript/Node.js      | `opossum`                 | Async/await support, customizable thresholds.                                    |
| .NET                    | Polly                      | Circuit Breaker, Retry, Bulkhead, Timeouts.                                       |
| Go                      | `go-circuitbreaker`       | Simple, thread-safe implementation.                                               |
| Cloud Native            | AWS App Mesh              | Service mesh integration with circuit breakers for Kubernetes.                   |

---
**Note**: For distributed systems, prefer **resilient libraries** over custom implementations to avoid edge-case bugs (e.g., race conditions during state transitions).