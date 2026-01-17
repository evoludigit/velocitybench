# **Debugging Resilience Observability: A Troubleshooting Guide**

---

## **1. Introduction**
Resilience Observability ensures that your system not only recovers from failures but also provides visibility into resilience mechanisms (retries, circuit breakers, timeouts, and fallbacks). Without proper observability, resilience patterns become "black boxes," making debugging difficult when failures occur.

This guide focuses on **quick troubleshooting** of common issues in **rate limiting, retry logic, circuit breakers, timeouts, and fallback mechanisms**.

---

## **2. Symptom Checklist**
Before diving into debugging, confirm these symptoms:
✅ **Unexpected timeouts** – Requests hanging or timing out unexpectedly.
✅ **Failed retries not retrying** – Retry logic not executing when expected.
✅ **Circuit breaker trips too early/never** – False positives or false negatives.
✅ **No fallback execution** – Fallbacks not triggering when dependencies fail.
✅ **Logging gaps** – Missing logs for resilience-related events.
✅ **Performance degradation** – High latency or throughput drops due to resilience logic.
✅ **Inconsistent behavior** – Same failure handled differently in different environments.

---

## **3. Common Issues & Fixes**

### **Issue 1: Retry Logic Not Working**
**Symptom:**
- A transient failure is not being retried, leading to cascading failures.
- Logs show no retry attempts.

**Root Causes:**
- Retry policy misconfigured (too few/many retries, no exponential backoff).
- Exception not matching retry filter.
- Thread pool exhausted before retries complete.

**Fixes:**
#### **Code Example: Configure Retry Correctly (Java - Resilience4j)**
```java
RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(3) // Default 3 retries (total 4 attempts)
    .intervalFunction(IntervalFunction.ofExponentialBackoff(Duration.ofMillis(100))) // Exponential backoff
    .retryExceptions(TransientError.class) // Only retry transient errors
    .build();

Retry retry = Retry.of("myRetry", retryConfig);

// Usage
retry.executeSupplier(() -> {
    if (Math.random() < 0.5) {
        throw new TransientError("Simulated transient failure");
    }
    return "Success";
});
```

**Debugging Steps:**
1. **Check logs** for `Retry` events (e.g., `onRetry`, `onSuccess`, `onFailure`).
2. **Verify exception type** – Ensure the failing exception is in `retryExceptions`.
3. **Test with `executeRunnable`** to simulate retries manually:
   ```java
   retry.executeRunnable(() -> {
       try { /* failing call */ }
       catch (Exception e) { System.err.println("Retry attempt: " + retry.getRetryCount()); }
   });
   ```

---

### **Issue 2: Circuit Breaker Trips Too Early**
**Symptom:**
- Circuit breaker opens after **1 failure** instead of the expected threshold (e.g., 5 failures).
- System behaves as if completely down when it should still function.

**Root Causes:**
- Incorrect `failureRateThreshold` in circuit breaker config.
- `minimumNumberOfCalls` too low.
- `waitDurationInOpenState` too short.

**Fixes:**
#### **Code Example: Adjust Circuit Breaker Settings (Java - Resilience4j)**
```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50) // 50% failure rate to trip (default: 50, but often set lower)
    .minimumNumberOfCalls(10) // Require 10 calls before triggering
    .waitDurationInOpenState(Duration.ofSeconds(30)) // Stay open for 30s
    .permittedNumberOfCallsInHalfOpenState(3) // Allow 3 calls when half-open
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("myService", config);
```

**Debugging Steps:**
1. **Check metrics** (`failureRate`, `state`, `numberOfCalls`):
   ```java
   System.out.println("Failure rate: " + circuitBreaker.getMetrics().getFailureRate());
   System.out.println("State: " + circuitBreaker.getState());
   ```
2. **Simulate calls** and verify behavior:
   ```java
   circuitBreaker.executeSupplier(() -> {
       if (Math.random() < 0.6) throw new RuntimeException("Simulated failure");
       return "Success";
   });
   ```
3. **Adjust thresholds** based on real-world data (not just theoretical failure rates).

---

### **Issue 3: Timeouts Not Enforced**
**Symptom:**
- Requests hang beyond expected timeouts.
- Logs show no timeout events.

**Root Causes:**
- Timeout value too high/low.
- Timeout applied to the wrong operation (e.g., blocking call instead of async).
- Thread pool starvation (timeout ignored due to blocked threads).

**Fixes:**
#### **Code Example: Set Timeout Correctly (Java - Resilience4j)**
```java
TimeoutConfig timeoutConfig = TimeoutConfig.custom()
    .timeoutDuration(Duration.ofSeconds(2)) // Enforce 2s timeout
    .build();

Timeout timeout = Timeout.of("myTimeout", timeoutConfig);

// Usage with async call
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    if (Math.random() < 0.5) Thread.sleep(3000); // Simulate slow call
    return "Done";
}, executor);

timeout.executeRunnable(() -> future.get()); // Throws TimeoutException after 2s
```

**Debugging Steps:**
1. **Check logs** for `TimeoutException`.
2. **Test with `executeCallable`**:
   ```java
   timeout.executeCallable(() -> {
       Thread.sleep(3000); // Simulate long call
       return "Result";
   });
   ```
3. **Monitor thread pool** – Ensure executor is not saturated:
   ```java
   ExecutorService executor = Executors.newFixedThreadPool(10);
   System.out.println("Thread pool size: " + ((ThreadPoolExecutor) executor).getPoolSize());
   ```

---

### **Issue 4: Fallback Not Triggering**
**Symptom:**
- A failure occurs, but the fallback does not execute.
- Logs show no fallback logs.

**Root Causes:**
- Fallback method not properly annotated/registered.
- Exception not propagated correctly.
- Fallback logic itself fails silently.

**Fixes:**
#### **Code Example: Configure Fallback (Java - Resilience4j)**
```java
Function<String, String> fallbackFunction = input -> "Fallback response for: " + input;

RetryFunction<String, String> retryFunction = Retry.decorateSupplier(
    supplier, // Original failing supplier
    retryConfig,
    fallbackFunction
);

// Usage
String result = retryFunction.get();
System.out.println(result); // Will use fallback if retries fail
```

**Debugging Steps:**
1. **Check logs** for fallback execution.
2. **Test manually**:
   ```java
   Supplier<String> failingSupplier = () -> { throw new RuntimeException("Fallback test"); };
   System.out.println(retryFunction.get()); // Should trigger fallback
   ```
3. **Verify fallback function** is reachable:
   ```java
   System.out.println(fallbackFunction.apply("test")); // Ensure it works standalone
   ```

---

### **Issue 5: Logs Missing Resilience Events**
**Symptom:**
- No logs for retries, circuit breaker states, or fallbacks.
- Hard to correlate failures with resilience behavior.

**Root Causes:**
- Logging level too high (e.g., `ERROR` when `DEBUG` is needed).
- Custom logger not configured.
- Resilience4j logging disabled.

**Fixes:**
#### **Configure Logging Properly (Logback Example)**
```xml
<!-- logback.xml -->
<logger name="io.github.resilience4j" level="DEBUG" />
<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
        <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
    </encoder>
</appender>
```

**Debugging Steps:**
1. **Check log levels**:
   ```java
   Logger logger = LoggerFactory.getLogger(Retry.class);
   logger.setLevel(Level.DEBUG);
   ```
2. **Force debugging logs in code**:
   ```java
   Retry.retry(() -> {
       if (Math.random() < 0.5) throw new RuntimeException("Test");
       return "OK";
   }, retryConfig, (e, attempt) -> {
       logger.debug("Retry attempt {} failed: {}", attempt, e.getMessage());
   });
   ```
3. **Filter logs** in Logback/Spring Boot:
   ```java
   @Bean
   public FilterRegistrationBean<LoggerFilter> loggingFilter() {
       FilterRegistrationBean<LoggerFilter> registrationBean = new FilterRegistrationBean<>();
       LoggerFilter filter = new LoggerFilter();
       filter.setPattern("io.github.resilience4j.*");
       registrationBean.setFilter(filter);
       return registrationBean;
   }
   ```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                                                 | **Example Usage** |
|--------------------------|-----------------------------------------------------------------------------|-------------------|
| **Resilience4j Metrics** | Monitor failure rates, retry attempts, circuit breaker state.              | `circuitBreaker.getMetrics()` |
| **Spring Boot Actuator** | Expose resilience metrics via `/actuator/health`.                          | `@Endpoint(id = "resilience")` |
| **Prometheus + Grafana** | Visualize circuit breaker, retry, and timeout metrics over time.          | `resilience4j_retry_success_count` |
| **Logging Correlation IDs** | Track requests through retries/fallbacks with a single ID.               | `MDC.put("traceId", UUID.randomUUID().toString());` |
| **Distributed Tracing (Zipkin/Jaeger)** | Trace calls across services with resilience patterns.                     | `Tracing.currentSpan().setTag("resilience.action", "retry");` |
| **Thread Dumps**         | Identify thread starvation causing timeouts.                               | `jstack <pid>` |
| **Local Variable Inspection** | Debug retry/fallback logic step-by-step in IDE (IntelliJ/Eclipse).        | Breakpoints in `Retry.executeRunnable()` |

---

## **5. Prevention Strategies**

### **A. Code-Level Best Practices**
✔ **Use `@Retry`/`@CircuitBreaker` annotations** (Spring Cloud Circuit Breaker) to standardize resilience.
✔ **Test resilience in CI** – Simulate failures with tools like:
   - **WireMock** (mock unreliable services).
   - **Testcontainers** (spin up flaky databases).
   - **Chaos Engineering** (kill containers mid-test).
✔ **Log structured events** (JSON) for easier querying:
   ```json
   {
     "event": "retry",
     "attempt": 2,
     "exception": "TimeoutException",
     "timestamp": "2023-10-01T12:00:00Z"
   }
   ```
✔ **Avoid nested resilience decorators** – They can mask failures or cause exponential delays.

### **B. Configuration Best Practices**
✔ **Set realistic timeouts** (start with **1-5s** for REST calls).
✔ **Use exponential backoff** (default in Resilience4j is `100ms * 2^attempt`).
✔ **Monitor failure rates** – Adjust `failureRateThreshold` based on SLOs.
✔ **Disable resilience in tests** (use `@DisabledResilience4j` for unit tests).

### **C. Observability Setup**
✔ **Expose resilience metrics** via Prometheus:
   ```java
   @Bean
   public Metrics metrics(Resilience4jMetrics metrics) {
       metrics.configureResilience4j();
       return metrics;
   }
   ```
✔ **Alert on anomalies** (e.g., sudden increase in `retry.failureCount`).
✔ **Use correlation IDs** to track end-to-end requests:
   ```java
   String correlationId = UUID.randomUUID().toString();
   MDC.put("x-correlation-id", correlationId);
   ```

### **D. Chaos Engineering**
✔ **Gradually increase chaos** (start with 1% failure rate, then 10%, etc.).
✔ **Test fallbacks under load** (e.g., `locust` + resilience patterns).
✔ **Document recovery procedures** for each resilience mechanism.

---

## **6. Quick Reference Table**
| **Problem**               | **Check First**                          | **Quick Fix**                                 |
|---------------------------|------------------------------------------|-----------------------------------------------|
| Retries not happening     | Logs, exception type                     | Add exception to `retryExceptions()`          |
| Circuit breaker too strict | Failure rate threshold                   | Increase `minimumNumberOfCalls`              |
| Timeouts ignored          | Thread pool exhaustion                   | Increase thread pool size                     |
| Fallback silent failure   | Fallback function logs                   | Add `try-catch` in fallback + logging        |
| No observability          | Log levels, metrics                     | Enable `DEBUG` for `io.github.resilience4j`   |

---

## **7. Conclusion**
Resilience Observability is **not optional**—without it, you’re flying blind. Follow this guide to:
1. **Quickly debug** retry, circuit breaker, timeout, and fallback issues.
2. **Use the right tools** (logs, metrics, tracing).
3. **Prevent future failures** with proper configurations and chaos testing.

**Next Steps:**
- **Set up Prometheus + Grafana** for resilience metrics.
- **Run a chaos test** to validate fallback behavior.
- **Automate logging correlation** for distributed tracing.

---
**Debugging is faster when you know where to look.** Bookmark this guide and use it when resilience goes wrong! 🚀