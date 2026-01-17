# **[Pattern] Resilience Best Practices Reference Guide**

---
## **Overview**
Building resilient systems ensures applications remain functional under adverse conditions, such as network failures, spikes in traffic, or hardware malfunctions. This guide outlines key resilience principles—circuit breaking, retry strategies, rate limiting, fallback mechanisms, and graceful degradation—and provides implementation guidelines across microservices, distributed systems, and cloud-native architectures.

Resilience minimizes cascading failures and improves system availability by combining defensive programming, adaptive retries, and circuit breaker patterns. Best practices include **timeouts, bulkheads (resource isolation), and idempotency** to handle transient faults. This guide references specific tools (e.g., **Hystrix, Resilience4j, Retry**) and frameworks (e.g., **Spring Cloud Circuit Breaker**) for integration.

---
## **Schema Reference**

| **Category**               | **Best Practice**                     | **Key Implementation Components**                          | **Example Use Case**                          | **Tools/Frameworks**                          |
|----------------------------|----------------------------------------|------------------------------------------------------------|-----------------------------------------------|-----------------------------------------------|
| **Fault Isolation**        | **Circuit Breaker Pattern**            | - Open/Closed/Half-Open states<br>- Thresholds (failure rate, timeout)<br>- Fallback handlers | Prevent cascading failures in payment processing | Hystrix, Resilience4j, Spring Retry          |
|                            | **Bulkheading**                        | - Resource quotas<br>- Thread pools per service<br>- Isolation via containers | Limit database connection exhaustion          | Spring Boot Actuator, Kubernetes HPA          |
| **Retry & Backoff**        | **Exponential Backoff Retry**          | - Max retries<br>- Delay formula (e.g., `minDelay * 2^attempt`)<br>- Jitter (randomized delay) | API retry for temporary 5xx errors           | Resilience4j, Spring Retry                   |
|                            | **Idempotency Keys**                   | - Unique request IDs<br>- Deduplication (e.g., database stores)<br>- Stateless repeatability | Prevent duplicate payments                    | Custom ID generation + DB tracking            |
| **Rate Limiting**          | **Token Bucket / Leaky Bucket**        | - Token rate (tokens/sec)<br>- Burst capacity<br>- Reject policies (429/503) | API gateway throttling                        | Redis Rate Limiter, NGINX, Envoy              |
| **Graceful Degradation**   | **Fallback Mechanisms**                | - Static data caching<br>- Shadow mode (partial functionality)<br>- Feature flags | Serve cached content during outages           | Spring Cloud Circuit Breaker fallback         |
|                            | **Deferred Processing**                | - Queue-based retries (e.g., Kafka, SQS)<br>- Priority queues | Async order processing                        | Apache Kafka, AWS SQS                        |
| **Observability**          | **Distributed Tracing**                | - Trace IDs<br>- Span logging<br>- Error correlation IDs (X-Correlation-ID) | Debugging microservices failures               | Jaeger, OpenTelemetry, Zipkin                 |
|                            | **Metrics & Alerts**                   | - Latency (p99, p95)<br>- Error rates<br>- Thresholds (e.g., 1% error rate) | Proactive failure detection                  | Prometheus + Grafana, Datadog                 |
| **Configuration**          | **Dynamic Reconfiguration**            | - Config servers (Spring Cloud Config)<br>- Feature toggles<br>- Canary releases | Adjust retry limits without redeployments       | Spring Cloud Config, LaunchDarkly              |

---

## **Query Examples**

### **1. Circuit Breaker Configuration (Resilience4j)**
```java
@CircuitBreaker(
    name = "paymentService",
    fallbackMethod = "fallbackPayment",
    retryCount = 3,
    waitDuration = "1s",
    slidingWindowType = SlidingWindowType.COUNT_BASED,
    slidingWindowSize = 5,
    minimumNumberOfCalls = 2,
    permittedNumberOfCallsInHalfOpenState = 3
)
public Payment processPayment(PaymentRequest request) {
    return paymentClient.charge(request);
}

public Payment fallbackPayment(PaymentRequest request, Exception e) {
    return new Payment(request, Status.PENDING, "Fallback - Payment Service Down");
}
```

### **2. Exponential Backoff Retry (Spring Retry)**
```yaml
# application.yml
spring:
  retry:
    max-attempts: 3
    backoff:
      initial-interval: 1000
      multiplier: 2
      max-interval: 10000
```

**Java Configuration:**
```java
@Configuration
@EnableRetry
public class RetryConfig {
    @Bean
    public RetryTemplate retryTemplate() {
        ExponentialBackOffPolicy backOffPolicy = new ExponentialBackOffPolicy();
        backOffPolicy.setInitialInterval(1000);
        backOffPolicy.setMultiplier(2.0);
        backOffPolicy.setMaxInterval(10000);

        RetryTemplate template = new RetryTemplate();
        template.setBackOffPolicy(backOffPolicy);
        template.setRetryPolicy(new SimpleRetryPolicy(3));
        return template;
    }
}
```

### **3. Rate Limiting (Redis Token Bucket)**
```python
# Flask + Redis example
from flask import Flask, jsonify
from redis import Redis

app = Flask(__name__)
redis = Redis(host='redis', db=0)

@app.route('/api')
def api():
    key = "api:rate_limit:user1"
    rate = redis.incr(f"{key}:count")

    if rate == 1:
        redis.expire(key, 60)  # Reset after 1 minute
        redis.set(f"{key}:capacity", 100)  # Max 100 requests/min

    capacity = redis.get(f"{key}:capacity")
    if rate > int(capacity):
        return jsonify({"error": "Rate limit exceeded"}), 429

    return jsonify({"data": "Allowed"})
```

### **4. Distributed Tracing (OpenTelemetry)**
```java
// Java Spring Boot with OpenTelemetry
@Bean
public Tracer tracer() {
    return OpenTelemetry.getTracer("my-app");
}

@RestController
public class OrderController {
    private final Tracer tracer = tracer();

    @PostMapping("/orders")
    public ResponseEntity<?> createOrder(@RequestBody Order order) {
        TraceContext.SpanContext spanContext = tracer.span()
            .setAttribute("request.id", order.getId())
            .end();

        // Business logic...
        return ResponseEntity.ok(order);
    }
}
```

### **5. Fallback with Circuit Breaker (Hystrix)**
```java
@HystrixCommand(
    fallbackMethod = "defaultPayment",
    commandKey = "paymentKey",
    groupKey = "paymentGroup",
    threadPoolKey = "paymentThreadPool"
)
public Payment processPayment(PaymentRequest request) {
    return paymentService.charge(request);
}

public Payment defaultPayment(PaymentRequest request, Throwable e) {
    log.error("Payment failed: {}", e.getMessage());
    return new Payment(request, Status.FAILED, "Service unavailable");
}
```

---

## **Implementation Guidelines**

### **1. Circuit Breaker Rules of Thumb**
- **Thresholds**:
  - **Failure Rate**: Open circuit if >50% of calls fail (adjust based on SLA).
  - **Timeout**: Default to 60s, but reduce for critical paths.
- **Half-Open State**: Test 2–5 requests before reclosing the circuit.
- **Resilience4j Defaults**:
  ```yaml
  resilience4j.circuitbreaker:
    instances:
      paymentService:
        registerHealthIndicator: true
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        permittedNumberOfCallsInHalfOpenState: 3
        automaticTransitionFromOpenToHalfOpenEnabled: true
  ```

### **2. Retry Strategies**
- **When to Retry**:
  - Transient errors (5xx, timeouts, connection resets).
  - Avoid retries for 4xx (client-side) errors unless idempotent.
- **Backoff**:
  - Exponential backoff (e.g., `1s, 2s, 4s, 8s`) with jitter to avoid thundering herds.
  - Cap max delay (e.g., 10s) to prevent unbounded retries.

### **3. Rate Limiting**
- **Token Bucket Algorithm**:
  - `tokens_per_second = 100` → 100 requests/minute.
  - `burst_capacity = 100` → Allow all tokens upfront.
- **Reject Policies**:
  - **429 Too Many Requests**: For client-side limits.
  - **503 Service Unavailable**: When backend is overloaded.

### **4. Idempotency**
- **Key Design**:
  - Use `UUID` or `requestId` as the key.
  - Store in Redis/memory with TTL (e.g., 24h).
- **Database Example**:
  ```sql
  CREATE TABLE idempotency_keys (
      key VARCHAR(36) PRIMARY KEY,
      request_payload JSONB,
      status VARCHAR(20), -- PENDING, COMPLETED, FAILED
      created_at TIMESTAMP
  );
  ```

### **5. Graceful Degradation**
- **Fallback Scenarios**:
  - Serve cached data during DB downtime.
  - Disable non-critical features (e.g., analytics).
- **Shadow Mode**:
  - Route a % of traffic to a degraded version for testing.

### **6. Observability**
- **Key Metrics**:
  - `resilience4j.circuitbreaker.statistics.calledCount`.
  - `resilience4j.retry.statistics.failedAttemptCount`.
- **Alerting**:
  - Prometheus alert on `rate(http_requests_total{status=~"5.."}[1m]) > 0.01`.

---

## **Related Patterns**

| **Related Pattern**          | **Description**                                                                 | **When to Use**                                  |
|-------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Retry Pattern**             | Automatically retry operations on failure with backoff.                          | Transient network/DB failures.                  |
| **Bulkhead Pattern**          | Isolate resource usage (e.g., threads, DB connections) to prevent overloading.   | High-concurrency scenarios.                     |
| **Circuit Breaker Pattern**   | Stop cascading failures by "tripping" after repeated failures.                   | External service dependencies.                  |
| **Saga Pattern**              | Manage distributed transactions via compensating actions.                      | Microservices with transactional workflows.     |
| **Chaos Engineering**         | Intentionally inject failures to test resilience.                               | Pre-deployment resilience testing.               |
| **CQRS**                      | Separate read/write models for scalability and resilience.                      | High-write-throughput systems.                  |
| **Idempotency Key Pattern**   | Ensure duplicate operations are safe (e.g., duplicate payments).               | HTTP APIs with retries.                         |

---
## **Tools & Libraries**
| **Tool**               | **Use Case**                                      | **Language Support**          |
|-------------------------|---------------------------------------------------|-------------------------------|
| **Resilience4j**        | Circuit breakers, retries, rate limiting.          | Java                          |
| **Polly**               | Retry/backoff policies (Microsoft).               | .NET                          |
| **Hystrix**             | Circuit breakers (deprecated but still used).     | Java                          |
| **Spring Retry**        | Spring Boot retry integration.                    | Java                          |
| **AWS SQS/SNS**         | Async retries and dead-letter queues.             | All                          |
| **Redis Rate Limiter**  | Token bucket/leaky bucket algorithms.             | All                          |
| **Jaeger/Zipkin**       | Distributed tracing.                              | All                          |
| **Prometheus**          | Metrics collection for resilience monitoring.     | All (exporters available)     |
| **LaunchDarkly**        | Feature flags for gradual rollouts.               | All                          |

---
## **Anti-Patterns to Avoid**
1. **Unbounded Retries**: Never retry indefinitely (use `maxAttempts`).
2. **No Circuit Breaker**: Blind retries amplify failures (e.g., DB connection exhaustion).
3. **Ignoring Timeouts**: Default timeouts (e.g., 30s) may hide slow dependencies.
4. **Global Fallbacks**: Avoid single fallback handlers; scope to specific services.
5. **No Observability**: Unmonitored retries/failures lead to blind spots.
6. **Hardcoded Thresholds**: Adjust circuit breaker thresholds per environment (dev vs. prod).
7. **Non-Idempotent Retries**: Retry POST requests without deduplication.