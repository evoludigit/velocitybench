# **Debugging Resilience Conventions: A Troubleshooting Guide**

## **1. Introduction**
The **Resilience Conventions** pattern ensures that distributed systems remain stable under failure, network latency, or resource constraints. It enforces consistent error handling, retries, circuit breaking, and fallback mechanisms across microservices and APIs.

This guide focuses on **quick issue resolution** for common misconfigurations, misbehaviors, and debugging techniques when implementing resilience conventions like **Retry, Circuit Breaker, Fallback, Bulkhead, and Timeout**.

---

## **2. Symptom Checklist**
Before diving into debugging, check these common symptoms:

### **Application-Level Symptoms**
- [ ] **Repeated timeouts** (e.g., `ConnectTimeoutException`, `ReadTimeoutException`)
- [ ] **Unbounded retry loops** causing cascading failures
- [ ] **Exponential backoff misconfigurations** leading to throttling or delays
- [ ] **Fallback mechanism bypassed** (e.g., returning `null` instead of a default response)
- [ ] **Circuit breaker failing to open/close** (e.g., still allowing requests after threshold reached)
- [ ] **High-latency responses** due to excessive retry attempts
- [ ] **Resource exhaustion** (CPU, memory) from stuck threads (e.g., in bulkheads)
- [ ] **Logs showing `5xx` errors despite resilience configurations**

### **Infrastructure-Level Symptoms**
- [ ] **Load balancer overwhelmed** (if bulkheads are misconfigured)
- [ ] **Database connection pools exhausted** (if circuit breakers are bypassed)
- [ ] **Kafka/RabbitMQ queue backlog** due to failed retries
- [ ] **Monitoring alerts for "too many retries"** or "circuit breaker tripped"

---

## **3. Common Issues and Fixes**

### **Issue 1: Unbounded Retries Causing Cascading Failures**
**Symptoms:**
- Requests retry indefinitely, overwhelming downstream services.
- System logs show `"Retry count exceeded [maxRetries]"` but still failing.

**Root Cause:**
- Missing `maxRetries` or incorrect backoff strategy.
- Retry logic not respecting `Callable<>` timeout.

**Fix (Java - Resilience4j):**
```java
Retry retryConfig = RetryConfig.custom()
    .maxAttempts(3)  // Limit retries
    .waitDuration(Duration.ofMillis(100))  // Initial delay
    .multiplier(2)  // Exponential backoff
    .retryExceptions(TimeoutException.class, ConnectException.class)
    .build();

RetryDecorators.ofCallable(() -> callExternalService(), retryConfig)
    .execute();  // Safe retry with bounds
```

**Fix (Kotlin - Kotlin Coroutines):**
```kotlin
suspend fun withRetry(
    maxRetries: Int = 3,
    initialDelay: Long = 100,
    block: suspend () -> Unit
) {
    repeat(maxRetries) { retry ->
        try {
            block()
            return
        } catch (e: Exception) {
            if (retry == maxRetries - 1) throw e
            delay(initialDelay * (2L shl retry))
        }
    }
}

// Usage:
withRetry { callUnreliableService() }
```

---

### **Issue 2: Circuit Breaker Not Tripping (False Positives)**
**Symptoms:**
- Service keeps calling a failed downstream dependency.
- Circuit breaker state remains `CLOSED` despite repeated failures.

**Root Cause:**
- Incorrect `failureRateThreshold` or `slowCallRateThreshold`.
- Not excluding transient errors (e.g., `TimeoutException` not in retry/success list).

**Fix (Resilience4j):**
```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)  // Open after 50% failures
    .waitDurationInOpenState(Duration.ofSeconds(10))  // Wait before retrying
    .permittedNumberOfCallsInHalfOpenState(2)  // Test 2 calls before closing
    .slowCallDurationThreshold(Duration.ofSeconds(1))
    .slowCallRateThreshold(50)
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("serviceA", config);
// Ensure all exceptions are caught:
circuitBreaker.executeSupplier(() -> callServiceA(), () -> fallbackResponse());
```

**Debugging Steps:**
1. Check logs for `CIRCUIT_OPENED`/`CIRCUIT_HALF_OPEN`.
2. Verify `failureRateThreshold` matches observed failures (e.g., 50% → `failureRateThreshold=50`).

---

### **Issue 3: Fallback Mechanism Not Triggering**
**Symptoms:**
- Expected fallback response (`OK`) but downstream still fails.
- Logs show `null` or empty response where a fallback was expected.

**Root Cause:**
- Fallback provider not properly defined.
- Exception handling too broad (e.g., catching all `Exception` but not logging).

**Fix (Spring Retry + Resilience4j):**
```java
@Bean
public RetryableRetryHandler retryHandler() {
    return new RetryableRetryHandler() {
        @Override
        public RetryResult handleRetry(RecoveryContext recoveryContext) {
            if (recoveryContext.getFailureCount() >= 3) {
                return new RetryResult(true, "Fallback triggered");
            }
            return RetryResult.continueWithDelay(100);
        }
    };
}

@Retryable(value = TimeoutException.class, maxAttempts = 2)
public String callServiceWithFallback() {
    return callUnreliableService();
}

@Recover
public String fallback(String cause) {
    log.warn("Fallback due to: {}", cause);
    return "default-response";
}
```

**Debugging Steps:**
1. Add logging in the fallback method:
   ```java
   @Recover
   public String fallback(Exception e) {
       log.error("Fallback called: {}", e.getMessage());
       return "fallback";
   }
   ```
2. Verify `cause` is not `null` (indicates exception was swallowed).

---

### **Issue 4: Bulkhead Starvation (Thread Pool Exhaustion)**
**Symptoms:**
- Thread pool exhausted (`TooManyThreadsException`).
- High CPU usage with stuck threads in `WAITING` state.

**Root Cause:**
- Bulkhead size too small for expected load.
- No thread reuse (e.g., `ThreadPoolExecutor` not configured).

**Fix (Resilience4j Bulkhead):**
```java
BulkheadConfig bulkheadConfig = BulkheadConfig.custom()
    .maxConcurrentCalls(10)  // Limit concurrent calls
    .maxWaitDuration(Duration.ofMillis(100))  // Reject after 100ms
    .build();

Bulkhead bulkhead = Bulkhead.of("dbBulkhead", bulkheadConfig);
bulkhead.executeRunnable(() -> {
    // Database call (blocks thread)
});
```

**Debugging Steps:**
1. Monitor thread pool metrics (e.g., via Micrometer).
2. Increase `maxConcurrentCalls` if threads are unused.
3. Use **asynchronous bulkheads** (e.g., `Bulkhead.ofAsync()`) for I/O-bound tasks.

---

### **Issue 5: Timeout Misconfiguration**
**Symptoms:**
- Requests hang indefinitely (`ReadTimeoutException` too late).
- Timeout too aggressive, breaking valid but slow responses.

**Root Cause:**
- Timeout set too low (e.g., `100ms` for a slow API).
- Timeout not propagated to downstream calls.

**Fix (Java HttpClient with Timeout):**
```java
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com"))
    .timeout(Duration.ofSeconds(5))  // Global timeout
    .build();

try {
    HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
} catch (TimeoutException e) {
    // Retry or fallback
}
```

**Best Practices:**
- Use **context-propagated timeouts** (e.g., Spring Cloud Sleuth + Resilience4j).
- Log timeout durations for analysis.

---

## **4. Debugging Tools and Techniques**

### **A. Logging and Observability**
- **Logging Best Practices:**
  - Log **failure counts**, **circuit breaker state**, and **retry delays**.
  - Example:
    ```java
    log.debug("Retry attempt {} of 3 for service {}", attempt, serviceName);
    ```
- **Structured Logging (JSON):**
  ```json
  {
    "event": "retry",
    "service": "user-service",
    "attempt": 2,
    "exception": "ConnectException",
    "delay": 100
  }
  ```
- **APM Tools:**
  - **Spring Boot Actuator** (`/actuator/health`)
  - **Prometheus + Grafana** (monitor `resilience4j_circuitbreaker_state`)
  - **Distributed Tracing** (Jaeger, Zipkin)

### **B. Metrics and Alerts**
| Metric                     | Tool          | Alert Threshold       |
|----------------------------|---------------|-----------------------|
| `resilience4j.retry.failures` | Micrometer    | > 5 failures/min      |
| `resilience4j.circuitbreaker.state` | Prometheus | `OPEN` > 1 minute     |
| `bulkhead.threads.active`  | Custom metrics| > 80% of max threads  |

**Example Prometheus Alert:**
```yaml
- alert: CircuitBreakerOpen
  expr: resilience4j_circuitbreaker_state{state="OPEN"} > 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Circuit breaker for {{ $labels.service }} is OPEN"
```

### **C. Unit Testing Resilience Logic**
**Example (JUnit + Mockito):**
```java
@Test
void shouldFallbackWhenCircuitBreakerOpens() {
    CircuitBreaker circuitBreaker = mock(CircuitBreaker.class);
    when(circuitBreaker.isOpen()).thenReturn(true);

    Supplier<String> call = () -> circuitBreaker.executeSupplier(() -> "failed", "fallback");
    assertEquals("fallback", call.get());
}
```

**Test Edge Cases:**
- Simulate **network partitions** (`ConnectException`).
- Test **exponential backoff** under load.

### **D. Debugging with `resilience4j-debug`**
Enable debug logging for Resilience4j:
```properties
logging.level.io.github.resilience4j=DEBUG
```
Look for:
```
[io.github.resilience4j.retry] Unable to execute callable: java.net.ConnectException
[io.github.resilience4j.circuitbreaker] Circuit for serviceA is now OPEN
```

---

## **5. Prevention Strategies**

### **A. Configuration Guidelines**
| Conventional Practice       | Recommended Setting                     |
|-----------------------------|------------------------------------------|
| **Retry maxAttempts**       | 3-5 (avoid unbounded retries)            |
| **Circuit breaker threshold** | 50-80% (adjust based on SLA)            |
| **Bulkhead max threads**    | Match expected concurrent calls          |
| **Timeout duration**        | 2-5x expected response time              |
| **Fallback response**       | Graceful degradation (not `null`)         |

### **B. Coding Standards**
1. **Fail Fast:** Validate inputs before retries.
   ```java
   if (request == null) {
       throw new IllegalArgumentException("Request cannot be null");
   }
   ```
2. **Idempotency:** Ensure retries don’t cause side effects.
3. **Context Propagation:** Use `ThreadLocal` or `MDC` (MDC = Mapped Diagnostic Context) for tracing.
   ```java
   MDC.put("traceId", UUID.randomUUID().toString());
   ```

4. **Centralized Resilience Config:**
   Use **Spring Cloud Config** or **Kubernetes ConfigMaps** for shared resilience settings.

### **C. Chaos Engineering**
- **Simulate failures** in staging (e.g., using **Gremlin** or **Chaos Mesh**).
- **Test circuit breaker recovery:**
  ```java
  @Test
  void shouldRecoverAfterCircuitBreakerCloses() {
      CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("test");
      // Simulate recovery
      when(circuitBreaker.isOpen()).thenReturn(false);
      assertTrue(circuitBreaker.isClosed());
  }
  ```

### **D. Documentation**
- **Resilience Policy Cheatsheet:**
  ```
  | Service  | Retry | Circuit Breaker | Timeout | Fallback |
  |----------|-------|-----------------|---------|----------|
  | User API | 3     | 70%             | 2s      | Cache   |
  | Payment  | 5     | 90% (5s)        | 5s      | Charge later |
  ```
- **Postmortem Templates:**
  - What triggered the resilience mechanism?
  - Was the fallback effective?
  - Were retries unnecessary?

---

## **6. Quick Resolution Cheat Sheet**
| **Symptom**               | **Likely Cause**               | **Quick Fix**                          |
|---------------------------|---------------------------------|-----------------------------------------|
| Retries > maxAttempts     | Missing `maxAttempts`           | Set `maxAttempts(3)` in retry config    |
| Circuit breaker stuck OPEN| Wrong `failureRateThreshold`    | Lower threshold (e.g., `30`)            |
| Fallback not called       | Exception not listed in retry    | Add exception to retry/success list    |
| Bulkhead starvation       | Too few threads                 | Increase `maxConcurrentCalls`           |
| Timeouts too aggressive   | Timeout too low                 | Increase to `5s`                        |

---

## **7. Conclusion**
Resilience conventions are **not a silver bullet**—they require **proper tuning, testing, and monitoring**. Follow these steps for quick debugging:
1. **Check logs** for resilience-related events.
2. **Validate metrics** (failures, timeouts, circuit state).
3. **Test edge cases** in isolation.
4. **Optimize configurations** based on real-world failure rates.

**Key Takeaway:**
> *"Resilience is observable, measurable, and tunable—don’t assume it works without validation."*

For further reading:
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Spring Retry](https://docs.spring.io/spring-retry/docs/current/reference/html/)
- [Chaos Engineering Guide (Gremlin)](https://www.gremlin.com/ocean/)