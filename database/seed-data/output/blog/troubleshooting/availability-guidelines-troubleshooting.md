# **Debugging Availability Guidelines: A Troubleshooting Guide**
*A focused guide for diagnosing and resolving system availability issues in distributed applications*

---

## **1. Introduction**
Availability Guidelines ensure that distributed systems remain operational despite failures. These guidelines define:
- **Graceful degradation** (handling partial failures)
- **Fault tolerance** (redundancy, retries, circuit breakers)
- **Resilience patterns** (bulkheads, timeouts, backpressure)

This guide helps diagnose common availability issues, providing actionable fixes, debugging steps, and prevention strategies.

---

## **2. Symptom Checklist**
Check these signs to identify availability-related problems:

### **User-Visible Symptoms**
- [ ] Random 5xx errors (e.g., `503 Service Unavailable`, `504 Gateway Timeout`)
- [ ] Intermittent failures (works sometimes, fails others)
- [ ] Slow response times (latency spikes)
- [ ] System-wide outages during peak load
- [ ] Notifications of "unexpected downtime" (e.g., AWS alarms, Kubernetes pod crashes)
- [ ] External APIs/third-party services failing unexpectedly

### **System-Level Symptoms**
- [ ] High error rates in logs (e.g., `ConnectionRefused`, `TimeoutException`)
- [ ] Unhealthy checks failing (e.g., Prometheus alerts, LoadBalancer health probes)
- [ ] Sudden spikes in retry counts (indicates transient failures)
- [ ] Resource exhaustion (CPU, memory, or disk usage at 100%)
- [ ] Database connection pool depletion
- [ ] Cascading failures (one failure triggers others)

### **Log-Based Clues**
- [ ] `java.net.ConnectException`, `ConnectionTimeoutException` (network issues)
- [ ] `TimeoutException`, `ResponseTimeout` (slow dependencies)
- [ ] `OutOfMemoryError`, `HeapSpace` (memory leaks or spikes)
- [ ] `CircuitBreakerOpen` (frequent failures in a downstream service)
- [ ] `BulkheadFull` (thread pool exhaustion)

---
## **3. Common Issues and Fixes**

### **Issue 1: Transient Failures (Network/Dependency Timeouts)**
**Symptoms:**
- `TimeoutException` in logs
- Intermittent `504 Gateway Timeout`
- Slow external API responses

**Root Causes:**
- Unstable downstream services (e.g., databases, payment gateways)
- No retry logic or retries too aggressive
- No fallback mechanisms

**Fixes:**

#### **A. Implement Retries with Exponential Backoff**
```java
// Using Resilience4j (Java)
RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofMillis(100))
    .retryExceptions(TransientError.class)
    .build();

Retry retry = Retry.of("myRetry", retryConfig);

ServiceResponse response = retry.executeSupplier(() -> client.callExternalService());
```

#### **B. Circuit Breaker for Faulty Services**
```java
// Using Resilience4j
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)  // 50% failures trigger a trip
    .waitDurationInOpenState(Duration.ofSeconds(30))
    .permittedNumberOfCallsInHalfOpenState(2)
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("externalApi", config);

try {
    circuitBreaker.executeSupplier(() -> callExternalApi());
} catch (CircuitBreakerOpenException e) {
    // Fallback logic (e.g., cache, grace degradation)
    return fallbackResponse();
}
```

#### **C. Timeout Handling**
```java
// Spring WebClient (Kotlin-like pseudocode)
val response = withTimeout(5_000) {  // 5s timeout
    webClient.get()
        .uri("/slow-endpoint")
        .retrieve()
        .bodyToMono(String::class.java)
}
```
**Key Fix:** Always implement **timeouts + retries + circuit breakers**.

---

### **Issue 2: Resource Exhaustion (CPU/Memory/Disk)**
**Symptoms:**
- `OutOfMemoryError`, `StackOverflowError`
- High CPU usage (100% for prolonged periods)
- Slow response times due to GC pauses

**Root Causes:**
- Memory leaks (e.g., unclosed DB connections, cached objects)
- Infinite loops or blocking calls
- No backpressure (e.g., Kafka consumers choking on messages)

**Fixes:**

#### **A. Implement Backpressure (Kafka Example)**
```java
// Using Kafka Consumer with backpressure
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 100); // Limit batch size

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Collections.singletonList("topic"));

try {
    while (true) {
        ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
        for (ConsumerRecord<String, String> record : records) {
            try {
                process(record.value());
                consumer.commitSync(); // Manual commit to avoid lag
            } catch (Exception e) {
                // Skip bad records (dead-letter queue if needed)
                logger.error("Failed to process: " + record, e);
            }
        }
        // Sleep if processing is slow (backpressure)
        if (records.isEmpty()) {
            Thread.sleep(100);
        }
    }
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
}
```

#### **B. Monitor and Limit Concurrency**
```java
// Using Resilience4j Bulkhead
BulkheadConfig bulkheadConfig = BulkheadConfig.custom()
    .maxConcurrentCalls(10)  // Limit concurrent calls
    .maxWaitDuration(Duration.ofMillis(1000))
    .build();

Bulkhead bulkhead = Bulkhead.of("databaseOperations", bulkheadConfig);

bulkhead.executeRunnable(() -> {
    // Database-bound work here
    database.query("SELECT * FROM large_table");
});
```

#### **C. Garbage Collection Tuning**
Add to JVM args:
```bash
-XX:+UseG1GC -XX:MaxGCPauseMillis=200 -Xmx8G
```
**Key Fix:** Use **bulkheads, backpressure, and proper GC tuning**.

---

### **Issue 3: Cascading Failures**
**Symptoms:**
- One service failure takes down the entire system
- `StackOverflow` in logs (deep call stacks)
- External dependencies failing in a chain reaction

**Root Causes:**
- Tightly coupled services
- No isolation (e.g., sharing a single database pool)
- No circuit breakers on downstream calls

**Fixes:**

#### **A. Isolate Dependencies (Bulkhead Pattern)**
```java
// Spring Boot with Resilience4j
@Bean
public Bulkhead bulkhead(Resilience4jCircuitBreakerFactory factory) {
    return factory.bulkhead("paymentService",
        BulkheadConfig.custom()
            .maxConcurrentCalls(5)
            .build()
    );
}

@Service
public class PaymentService {
    @CircuitBreaker(name = "paymentService", fallbackMethod = "fallbackPayment")
    public PaymentProcessResult processPayment(PaymentRequest request) {
        // Call external payment gateway
    }

    private PaymentProcessResult fallbackPayment(PaymentRequest request, Exception e) {
        // Use fallback (e.g., offline processing)
        return new PaymentProcessResult("FALLBACK_MODE");
    }
}
```

#### **B. Graceful Degradation**
```python
# Python (FastAPI-like pseudocode)
from fastapi import FastAPI, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/expensive-endpoint")
@limiter.limit("5/minute")
async def expensive_endpoint():
    try:
        result = call_slow_service()
        return result
    except ServiceUnavailable:
        return {"status": "degraded", "message": "Slow service unavailable"}
```

**Key Fix:** Use **bulkheads, circuit breakers, and graceful fallbacks**.

---

### **Issue 4: Database Connection Pool Exhaustion**
**Symptoms:**
- `SQLTransientConnectionException` (HikariCP)
- `TooManyConnections` in logs
- Slow queries due to connection wait times

**Root Causes:**
- Too few connections in the pool
- Long-running transactions
- No connection validation

**Fixes:**

#### **A. Configure HikariCP Properly**
```yaml
# application.properties
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.idle-timeout=30000  # 30s
spring.datasource.hikari.max-lifetime=1800000  # 30m
spring.datasource.hikari.connection-timeout=30000
```

#### **B. Use Connection Validation**
```java
// HikariConfig with validation
HikariConfig config = new HikariConfig();
config.setMaximumPoolSize(20);
config.setConnectionTestQuery("SELECT 1");  // Basic ping
config.setLeakDetectionThreshold(60000);   // Detect leaks
HikariDataSource ds = new HikariDataSource(config);
```

**Key Fix:** Tune **pool size, timeout, and validation**.

---

## **4. Debugging Tools and Techniques**

### **Logging and Monitoring**
| Tool               | Use Case                                  | Example Command/Config          |
|--------------------|-------------------------------------------|----------------------------------|
| **Structured Logging** (ELK, Loki) | Correlate failures across services | `logger.error("Failed to process event", eventId, error)` |
| **Distributed Tracing** (Jaeger, Zipkin) | Trace requests across microservices | `tracer.span("db-query").finish()` |
| **Metrics** (Prometheus + Grafana) | Detect spikes in latency/errors | `request_duration_seconds` histogram |
| **APM Tools** (New Relic, Datadog) | End-to-end performance insights | `newrelic.noticeError(error)` |

**Example Alert Rule (Prometheus):**
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate on {{ $labels.instance }}"
```

---

### **Debugging Workflow**
1. **Isolate the Symptom**
   - Check logs for errors (e.g., `java.net.ConnectException` → network issue).
   - Use tracing to see which service failed.

2. **Reproduce Locally**
   - Mock the failing dependency (e.g., use WireMock or local DB).
   - Test with chaos engineering tools (Gremlin, Chaos Monkey).

3. **Inspect Resource Usage**
   - Check CPU/memory via `top`, `htop`, or Prometheus.
   - Profile slow methods with `async-profiler`.

4. **Test Fixes**
   - Deploy changes incrementally (canary releases).
   - Verify with synthetic monitoring (e.g., Locust).

---

## **5. Prevention Strategies**

### **Design-Time Mitigations**
| Pattern               | Implementation Example                          | Tools/Libraries                 |
|-----------------------|------------------------------------------------|---------------------------------|
| **Circuit Breaker**   | Resilience4j, Hystrix                             | `@CircuitBreaker` (Spring)      |
| **Retry + Backoff**   | Exponential backoff with jitter                 | Resilience4j, Polly (AWS)       |
| **Bulkhead**          | Isolate threads for high-risk operations       | Resilience4j, Akka              |
| **Timeouts**          | Hard time limits for external calls             | Netty, Spring WebClient         |
| **Backpressure**      | Limit ingestion rate (e.g., Kafka consumers)    | Kafka `max.poll.records`        |
| **Graceful Degradation** | Fallback to cached or simplified responses   | Custom fallback methods         |

### **Operational Practices**
- **Chaos Engineering:** Run controlled failures (e.g., kill pods randomly).
- **Rate Limiting:** Protect APIs with `slowapi` or Kong.
- **Multi-Region Deployments:** Use AWS Global Accelerator or Kubernetes federations.
- **Blue-Green Deployments:** Reduce downtime risk.
- **Chaos Mesh:** Simulate network partitions, node failures.

### **Monitoring Checklist**
- **Error Rates:** Alert on `>1%` of requests failing.
- **Latency Percentiles:** Watch `p99` response times.
- **Resource Usage:** Set alerts for `CPU > 90%` or `Memory > 80%`.
- **Dependency Health:** Monitor external API uptime (e.g., Pingdom).
- **Circuit Breaker States:** Track `open`/closed states.

---
## **6. Quick Fix Cheat Sheet**

| **Symptom**               | **Immediate Fix**                          | **Long-Term Fix**                |
|---------------------------|--------------------------------------------|----------------------------------|
| `TimeoutException`        | Increase timeout + add retry               | Circuit breaker + fallback       |
| `OutOfMemoryError`        | Kill Java process, reduce heap size        | Fix leaks, optimize GC           |
| `ConnectionPoolExhausted` | Increase pool size                         | Validate connections, optimize queries |
| `503 Service Unavailable` | Check Kubernetes pod health                | Bulkhead + graceful degradation  |
| Cascading failures        | Isolate services                          | Circuit breakers + retries       |

---

## **7. Conclusion**
Availability issues stem from **uncaught failures, resource exhaustion, and tight coupling**. Focus on:
1. **Defensive programming** (timeouts, retries, circuit breakers).
2. **Resource isolation** (bulkheads, backpressure).
3. **Observability** (logs, metrics, tracing).
4. **Prevention** (chaos testing, rate limiting).

**Action Plan:**
- Audit services for missing resilience patterns.
- Implement at least **timeouts + retries + circuit breakers** for external calls.
- Monitor critical paths with **Prometheus + Alertmanager**.
- Run **chaos experiments** to validate robustness.

By following this guide, you’ll reduce downtime and build **resilient, high-availability systems**.