---
# **[Pattern] Resilience Techniques – Reference Guide**

---

## **Overview**
The **Resilience Techniques** pattern provides a structured approach to building fault-tolerant systems capable of gracefully handling failures, network latency, and external disruptions. By combining retry mechanisms, circuit breakers, rate limiting, fallback strategies, and bulkheading, applications can minimize downtime and degrade gracefully under adverse conditions.

This guide covers implementation details, schema references, query examples (where applicable), and related patterns to integrate resilience into distributed systems (e.g., microservices, cloud applications).

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Use Case Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Retry Mechanism**    | Automatically reprocess failed operations with backoff logic to avoid overwhelming systems.       | API calls to external services with transient errors (e.g., 5xx responses).                             |
| **Circuit Breaker**    | Prevents cascading failures by stopping calls to a failing service after a threshold of failures.   | Database connections crashing repeatedly under load.                                                  |
| **Bulkheading**       | Isolates different components/services to limit the impact of failures (e.g., thread pools).      | Microservice A failing shouldn’t crash Microservice B sharing the same host.                            |
| **Rate Limiting**     | Controls the request volume to prevent overload or abuse (e.g., API throttling).                | Third-party payment gateway under heavy traffic.                                                      |
| **Fallback Strategy** | Provides a secondary response when primary logic fails (e.g., cached data or degraded mode).      | Showing placeholder content if a CDN fails.                                                            |
| **Timeout**           | Enforces a maximum execution time for operations to prevent hanging.                                | Long-running database queries timing out.                                                              |
| **Idempotency**       | Ensures repeated identical operations produce the same result without side effects.               | Retrying a failed payment request (avoid duplicate charges).                                           |

---

## **Schema Reference**
Below are schema structures for implementing resilience techniques in code (adapted for common languages/frameworks).

### **1. Retry Mechanism (Exponential Backoff)**
```json
// Example: Resilience4j Retry configuration (Java)
{
  "retry": {
    "maxAttempts": 3,
    "waitDuration": "100ms",
    "enableExponentialBackoff": true,
    "multiplier": 2,
    "excludedExceptions": ["java.io.IOException"]
  }
}
```
**Key Attributes:**
- `maxAttempts`: Maximum retry count (default: 3).
- `waitDuration`: Initial delay between retries.
- `exponentialBackoff`: Scales delays exponentially (e.g., 100ms → 200ms → 400ms).
- `excludedExceptions`: List of exceptions to ignore (e.g., timeouts vs. permanent failures).

---

### **2. Circuit Breaker**
```json
// Example: Resilience4j Circuit Breaker configuration
{
  "circuitBreaker": {
    "failureThreshold": 50,       // % of calls that fail to trip
    "minimumNumberOfCalls": 4,   // Min calls to evaluate threshold
    "automaticTransitionFromOpenToHalfOpenEnabled": true,
    "waitDurationInOpenState": "5s",
    "permittedNumberOfCallsInHalfOpenState": 1
  }
}
```
**Key Attributes:**
- `failureThreshold`: % of failures to trip the circuit (e.g., 50%).
- `minimumNumberOfCalls`: Minimum calls to trigger the threshold.
- `waitDurationInOpenState`: Time before attempting to "half-open" the circuit.
- `permittedNumberOfCallsInHalfOpenState`: Allows 1 call to test recovery.

---

### **3. Bulkheading (Thread Isolation)**
```java
// Example: Using Spring’s @LoadBalanced with resiliency
@Bean
public Resilience4jRetryFactory CustomRetryFactory(
    @Value("${resilience.maxAttempts:3}") int maxAttempts) {
    return Retry.of("customRetry", builder ->
        builder.maxAttempts(maxAttempts)
               .waitDuration(Duration.ofMillis(100))
               .enableExponentialBackoff(true));
}
```
**Key Attributes:**
- **Thread Pools**: Dedicate separate pools for high-risk operations (e.g., `ExecutorService`).
- **Isolated Components**: Deploy critical services on separate instances/k8s pods.

---

### **4. Rate Limiting**
```json
// Example: Redis-based token bucket (Node.js)
{
  "rateLimiter": {
    "tokensPerSecond": 100,
    "bucketSize": 1000,
    "decayTime": 1000  // ms
  }
}
```
**Key Attributes:**
- `tokensPerSecond`: Max allowed requests per second.
- `bucketSize`: Max capacity of the "bucket."
- `decayTime`: Time to refill tokens (e.g., 1 token every 10ms).

---
### **5. Fallback Strategy**
```java
// Example: Spring’s @CircuitBreaker with fallback
@CircuitBreaker(name = "paymentService", fallbackMethod = "handlePaymentFailure")
public String processPayment(String amount) {
    return paymentGateway.charge(amount);
}

private String handlePaymentFailure(Exception e) {
    return "Fallback: Processed $0 (temporarily suspended).";
}
```
**Key Attributes:**
- **Fallback Method**: Executes when the primary operation fails.
- **Degradation Mode**: Return cached data or simplified responses.

---

## **Implementation Examples**
### **1. Retry with Resilience4j (Java)**
```java
import io.github.resilience4j.retry.Retry;
import io.github.resilience4j.retry.RetryConfig;

RetryConfig config = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofMillis(100))
    .enableExponentialBackoff(true)
    .build();

Retry retry = Retry.of("customRetry", config);

retry.executeRunnable(() -> {
    // Attempt to call external service
    externalService.doSomething();
});
```

### **2. Circuit Breaker in Python (PyResilience)**
```python
from pyresilience4j.circuitbreaker import CircuitBreaker, CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,
    wait_duration="5s",
    permitted_number_of_calls_in_half_open_state=1
)

circuit_breaker = CircuitBreaker(config)

@circuit_breaker.decorate
def call_failing_service():
    # Your failing service call
    pass
```

### **3. Rate Limiting in Node.js (Express)**
```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests
    handler: (req, res) => res.status(429).send('Too many requests.')
});

app.use(limiter);
```

---

## **Query Examples**
Resilience patterns don’t typically involve direct queries, but monitoring and configuration often rely on these patterns:

### **1. Monitoring Circuit Breaker State (Prometheus)**
```plaintext
# Metrics exposed by Resilience4j (Prometheus)
resilience4j_circuitbreaker_calls_total{name="paymentService"} 100
resilience4j_circuitbreaker_failures_total{name="paymentService"} 42
resilience4j_circuitbreaker_state{name="paymentService"} "OPEN"
```

### **2. Logging Retry Attempts**
```json
// Example log (JSON format)
{
  "timestamp": "2023-10-01T12:00:00Z",
  "event": "retry_attempt",
  "service": "orderService",
  "attempt": 2,
  "durationMs": 500,
  "exception": "ConnectionTimeoutException"
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **Integration Opportunity**                                                                             |
|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Retry as Last Resort**  | Only retry after confirming the failure is transient (e.g., check database replica status).      | Combine with circuit breakers to avoid exponential retries on permanent failures.                    |
| **Saga Pattern**          | Manage distributed transactions with resilience (e.g., retry compensating actions).              | Use retries for saga steps in case of failures.                                                      |
| **Chaos Engineering**     | Deliberately inject failures to test resilience (e.g., AWS Fault Injection Simulator).           | Validate resilience techniques under controlled chaos.                                               |
| **CQRS**                  | Separate read/write paths to isolate failures (e.g., read from cache on write failures).         | Fallback to read models if primary writes fail.                                                    |
| **Backpressure**          | Slow down producers when consumers are overwhelmed (e.g., Kafka backpressure).                     | Pair with rate limiting to prevent cascading failures.                                               |

---

## **Best Practices**
1. **Configure Timeouts**: Always set timeouts for external calls (e.g., 2–5 seconds for APIs).
2. **Monitor Circuit States**: Use dashboards (Grafana/Prometheus) to track `CLOSED`/`OPEN` states.
3. **Avoid Retrying Idempotent Operations**: Idempotency keys (e.g., `idempotency-key`) prevent duplicate actions.
4. **Graceful Degradation**: Prioritize user experience (e.g., show cached data even if primary fails).
5. **Test Resilience**: Use chaos tools (e.g., Gremlin) to simulate failures in staging.

---
## **Further Reading**
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Spring Cloud Circuit Breaker](https://spring.io/projects/spring-cloud-circuitbreaker)

---
**Last Updated**: [Insert Date]
**Version**: 1.2