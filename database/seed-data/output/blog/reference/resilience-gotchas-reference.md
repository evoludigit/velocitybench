# **[Pattern] Resilience Gotchas Reference Guide**

---

## **Overview**
Resilience patterns help systems withstand and recover from failures, but poorly implemented or misunderstood resilience mechanisms can introduce subtle bugs and anti-patterns. This guide covers common **"resilience gotchas"**—unexpected pitfalls that undermine robustness, performance, or correctness when applying resilience techniques like retry, circuit breaking, bulkheads, or timeouts.

These pitfalls often arise from:
- Over-reliance on retries without backoff (thundering herd)
- Incorrectly handling transient vs. permanent failures
- Misconfiguring timeouts (cascading failures)
- Overusing bulkheads (wasted resources)
- Ignoring resource cleanup (memory leaks)
- Misplaced reactive patterns (unnecessary complexity)

Addressing these gotchas ensures resilience doesn’t *cause* additional instability.

---

## **Schema Reference**
Below are critical parameters and configurations for resilience patterns, along with their common misuse vectors. Values marked *red* indicate critical thresholds or anti-pattern triggers.

| **Gotcha**               | **Description**                                                                                                                                 | **Affected Pattern**       | **Critical Settings/Values**                                                                                     | **Impact of Misuse**                                                                                          |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Retry Without Backoff** | Exponential backoff is skipped, causing repeated concurrent requests under load.                                                            | **Retry**                   | `maxRetries = 10`, `backoff = 0`                                                                               | Thundering herd: Overwhelms downstream services.                                                           |
| **Retry on Permanent Fail**| Retrying on 5xx errors when the failure is structural (e.g., database schema mismatch).                                                     | **Retry**                   | `retryOn = ["5xx", "4xx"]` (should exclude `"4xx"` except for transient errors)                                  | Waste CPU cycles; prolongs recovery time.                                                                     |
| **Incorrect Timeout**     | Timeout set too short (misses response) or too long (blocks system).                                                                          | **Timeout**                 | `timeout = 50ms` (too aggressive)                                                                             | Half-open connections, cascading failures.                                                              |
| **Bulkhead Misuse**       | Thread/process pool size too small (leads to queue buildup) or too large (resource waste).                                                  | **Bulkhead**                | `maxThreads = 2` (for 100K requests)                                                                         | Requests queued indefinitely; resource exhaustion.                                                         |
| **Circuit Breaker Leak**  | Breaker state not reset after recovery (false positives).                                                                                 | **Circuit Breaker**         | `resetTimeout = never`                                                                                         | Continuously rejects valid traffic.                                                                        |
| **Async Deadlock**        | Overusing `async` without proper ordered completion (e.g., chaining promises).                                                               | **Async Resilience**        | `async` calls nested without `.then()`/`await`                                                                 | Stuck threads, memory buildup.                                                                              |
| **Resource Leak**         | Unclosed connections/stream in retry logic (e.g., HTTP clients).                                                                              | **Retry + Bulkhead**        | Missing `HttpClient.Dispose()` or `.close()`                                                                   | Memory leaks, connection pools exhausted.                                                              |
| **Observer Pattern**      | Publishing failures to observers without rate limiting (noise overload).                                                                       | **Failure Observer**        | `maxObserverMessages = 0`                                                                                   | Alert fatigue, ignored critical alerts.                                                                     |
| **Lazy Initialization**   | Resilient components initialized only on failure (cold starts).                                                                             | **Lazy Loading**            | `initOnFailure = true` without `warmup`                                                                       | First failure after idle period; degraded performance.                                                    |
| **Over-Retries**          | Retry logic implemented with exponential backoff but cap too high (e.g., 1 hour).                                                          | **Retry**                   | `maxRetryDelay = 1hr`                                                                                         | Delays recovery; violates SLOs.                                                                              |
| **Misplaced Resilience**  | Resilience applied to I/O-bound operations where the issue is client-side (e.g., DNS misconfiguration).                                      | **Generic Resilience**      | Retrying DNS lookups                                                                                          | Debugging becomes harder; masks actual root cause.                                                       |

---

## **Query Examples**
### **1. Retry Gotchas**
#### **❌ Bad Practice: Infinite Retries**
```java
// Skips backoff; will hammer DB on 5xx errors
public void syncUserData(User user) {
    while (true) {
        try {
            repo.save(user); // Retries forever
            break;
        } catch (Exception e) {
            if (e instanceof DatabaseTimeout) {
                Thread.sleep(1000); // No exponential backoff
            }
        }
    }
}
```
**Fix:**
```java
// Uses exponential backoff with cap
RetryPolicy retry = RetryPolicyBuilder.newBuilder()
    .maxAttempts(3)
    .backoff(Duration.ofMillis(100))
    .maxBackoff(Duration.ofSeconds(2))
    .build();
```

---

### **2. Circuit Breaker Gotchas**
#### **❌ Bad Practice: No Reset**
```java
// Breaker stays "open" indefinitely
CircuitBreaker breaker = CircuitBreaker.ofDefaults("paymentService");
breaker.execute(() -> callPaymentService()); // First failure: breaker "open"
breaker.execute(() -> callPaymentService()); // Second failure: breaker remains open
```
**Fix:**
```java
// Reset after 1 minute if failures < 50%
CircuitBreaker breaker = CircuitBreaker.ofDefaults("paymentService")
    .withFailureThreshold(50) // Reset after 50% failures
    .withSuccessThreshold(0);  // Reset immediately after success
```

---

### **3. Timeout Gotchas**
#### **❌ Bad Practice: Blocking Timeout**
```java
// Blocks thread for 5s (bad for async systems)
Future<String> future = executor.submit(() -> callSlowService());
String result = future.get(5, TimeUnit.SECONDS); // Throws TimeoutException but blocks thread
```
**Fix:**
```java
// Non-blocking with CompletableFuture
CompletableFuture<String> future = CompletableFuture.supplyAsync(
    () -> callSlowService(),
    executor)
    .exceptionally(e -> fallbackResponse())
    .completeOnTimeout("timeoutResponse", 5, TimeUnit.SECONDS);
```

---

### **4. Bulkhead Gotchas**
#### **❌ Bad Practice: Starving Other Threads**
```java
// Single-threaded bulkhead (bottleneck)
ExecutorService executor = Executors.newSingleThreadExecutor();
executor.submit(() -> processOrder()); // All orders queued serially
```
**Fix:**
```java
// Dynamic bulkhead (thread pool sized to workload)
ExecutorService executor = Executors.newFixedThreadPool(
    Math.max(1, Runtime.getRuntime().availableProcessors() * 2)
);
```

---

### **5. Resource Leak Gotchas**
#### **❌ Bad Practice: Unclosed Streams**
```java
// Stream not closed after retry
InputStream stream = new BufferedInputStream(url.openStream());
for (int attempt = 0; attempt < 3; attempt++) {
    try {
        process(stream); // stream still open after retry
        break;
    } catch (IOException e) {
        Thread.sleep(1000);
    }
}
```
**Fix:**
```java
// Use try-with-resources or manual close
try (InputStream stream = new BufferedInputStream(url.openStream())) {
    process(stream); // Auto-closed after retry
}
```

---

## **Related Patterns**
| **Pattern**              | **Relationship to Resilience Gotchas**                                                                                                                                                                                                 | **When to Combine**                                                                                         |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Retry**                | Retry gotchas *directly* impact retry patterns (e.g., backoff, retries-on-permanent-fail).                                                                                                                                          | Always use with exponential backoff and separate transient/permanent fail logic.                           |
| **Circuit Breaker**      | Breaker state leaks or misconfigured reset thresholds cause cascading failures.                                                                                                                                              | Use with retry to avoid repeated breaker trips.                                                              |
| **Bulkhead**             | Misconfigured thread pools worsen resource leaks or queue buildups.                                                                                                                                                              | Combine with timeout to avoid bulkhead starvation.                                                            |
| **Timeout**              | Poorly set timeouts mask concurrency issues (e.g., async deadlocks).                                                                                                                                                            | Set timeouts slightly longer than expected slowest path (with jitter).                                       |
| **Lazy Initialization**  | Cold starts during retries degrade performance; combine with pre-warming.                                                                                                                                                   | Use for expensive connection pools (e.g., DB, HTTP clients).                                                 |
| **Observer Pattern**     | Overloaded failure observers lead to alert fatigue.                                                                                                                                                                        | Rate-limit observer notifications (e.g., sample every 5th failure).                                              |
| **Fallback**             | Fallbacks with hardcoded responses may mask actual errors.                                                                                                                                                                   | Use dynamic fallbacks (e.g., cached data) and log fallback usage.                                            |
| **Idempotency**          | Retries without idempotency cause duplicate side effects (e.g., double payments).                                                                                                                                            | Apply to retry logic for stateless operations (e.g., HTTP `PUT`/`POST` with IDs).                          |
| **Chaos Engineering**    | Intentionally injected failures can expose resilience gotchas (e.g., circuit breaker leaks).                                                                                                                                     | Use to test recovery from misconfigured resilience patterns.                                                   |

---

## **Key Takeaways**
1. **Backoff is mandatory** for retries—never skip exponential delays.
2. **Distinguish transient vs. permanent failures** to avoid wasted retries.
3. **Timeouts should be dynamic** (adjust for observed latency percentiles).
4. **Bulkheads must scale** with load; use dynamic thread pools.
5. **Always close resources** (connections, streams) in retry loops.
6. **Test resilience under load** using chaos engineering to uncover gotchas.
7. **Combine patterns** (e.g., retry + circuit breaker + bulkhead) but avoid circular dependencies.

---
**References:**
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Google SRE Book](https://sites.google.com/site/srebook/) (Chapter 5: Resilience)
- [Netflix Hystrix Gotchas](https://github.com/Netflix/Hystrix/wiki/Gotchas)