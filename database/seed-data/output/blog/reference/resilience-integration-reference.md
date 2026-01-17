# **[Pattern] Resilience Integration – Reference Guide**

## **Overview**
The **Resilience Integration** pattern ensures reliable system operation by embedding fault-tolerance mechanisms into distributed applications. It leverages patterns like **Circuit Breaker**, **Retry**, **Bulkhead**, and **Fallback** to mitigate failures (timeouts, crashes, network issues) while maintaining business continuity. This guide details implementation strategies, schema conventions, and best practices for integrating resilience tools (e.g., Resilience4j, Spring Retry) into microservices or monoliths.

---

## **Key Concepts**
| **Concept**            | **Definition**                                                                 | **Use Case**                                                                 |
|------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Circuit Breaker**    | Short-circuits failed dependencies to prevent cascading failures.             | External API calls (e.g., payment processor).                                |
| **Retry**              | Automatically reattempts transient failures (exponential backoff recommended). | Database retries after network blips.                                       |
| **Bulkhead**           | Isolates resource access (threads, connections) to prevent overload.          | Rate-limiting high-traffic endpoints.                                       |
| **Fallback**           | Provides degraded functionality when primary services fail.                  | User profile data from cache if DB fails.                                   |
| **Timeouts**           | Limits execution time to avoid hanging requests.                              | API gateway callouts with 1-second timeout.                                 |

**Integration Layers:**
1. **Application Layer** – Configures resilience policies.
2. **Infrastructure Layer** – Implements retries/bulkheads.

---

## **Schema Reference**

### **1. Resilience Configuration Schema**
| Field                  | Type       | Required | Description                                                                 |
|------------------------|------------|----------|-----------------------------------------------------------------------------|
| `policyName`           | String     | Yes      | Name of resilience policy (e.g., `paymentServiceBreaker`).                  |
| `type`                 | Enum*      | Yes      | `CIRCUIT_BREAKER`, `RETRY`, `BULKHEAD`, `FALLBACK`.                          |
| `resourceName`         | String     | Yes      | Target service/resource (e.g., `dbConnectionPool`).                          |
| `threshold`            | Integer    | Conditional | Failures before triggering (e.g., `5` for circuit breaker).                 |
| `timeoutMs`            | Integer    | Conditional | Max execution time (e.g., `3000` ms).                                      |
| `retryMaxAttempts`     | Integer    | Conditional | Max retries (e.g., `3`).                                                  |
| `fallbackMethod`       | String     | Conditional | Alternative method (e.g., `cacheService.getProfile()`).                    |
| `bulkheadIsolation`    | String     | Conditional | `THREAD` or `SEMAPHORE` (for concurrency control).                         |

**`*` Enum values:** See implementation library documentation (e.g., Resilience4j’s API).

---

### **2. Event Schema (Resilience Events)**
| Field          | Type     | Description                                                                 |
|----------------|----------|-----------------------------------------------------------------------------|
| `id`           | UUID     | Unique event identifier.                                                   |
| `timestamp`    | ISO8601  | When the event occurred.                                                   |
| `policyName`   | String   | Associated resilience policy.                                              |
| `eventType`    | Enum      | `SUCCESS`, `FAILURE`, `CIRCUIT_OPENED`, `RECOVERED`.                       |
| `details`      | JSON      | Additional metadata (e.g., `{"attempt": 2, "exception": "TimeoutException"}`). |

---

## **Implementation Examples**

### **1. Java (Spring Boot + Resilience4j)**
#### **a. Add Dependencies**
```xml
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot2</artifactId>
    <version>2.1.0</version>
</dependency>
```

#### **b. Configure Circuit Breaker**
```yaml
# application.yml
resilience4j.circuitbreaker:
  instances:
    paymentService:
      registerHealthIndicator: true
      slidingWindowSize: 10
      minimumNumberOfCalls: 5
      permittedNumberOfCallsInHalfOpenState: 3
      automaticTransitionFromOpenToHalfOpenEnabled: true
      waitDurationInOpenState: 5s
      failureRateThreshold: 50
```

#### **c. Annotate Service Method**
```java
@CircuitBreaker(name = "paymentService", fallbackMethod = "fallbackProcess")
public Payment processPayment(PaymentRequest request) {
    // Call external payment service
}
```

#### **d. Define Fallback**
```java
private Payment fallbackProcess(PaymentRequest request, Exception ex) {
    log.error("Payment failed: {}", ex.getMessage());
    return new Payment("FALLBACK_TRANSACTION_ID", request.getAmount());
}
```

---

### **2. Python (with `tenacity` and `aiohttp`)**
#### **a. Retry with Exponential Backoff**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_api(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()
```

#### **b. Bulkhead (Thread Pool)**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_with_bulkhead(tasks, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task): task for task in tasks}
        for future in as_completed(futures):
            yield future.result()
```

---

### **3. Query Examples (Monitoring Metrics)**
#### **a. Prometheus Query (Circuit Breaker State)**
```promql
resilience4j_circuitbreaker_state{policy="paymentService"} == 1
```
*(Returns `1` if circuit is open.)*

#### **b. Logs Filter (Retry Attempts)**
```bash
grep "attempt=2" /var/log/app.log | jq '.details.attempt'
```
*(JSON logs showing retry count.)*

#### **c. Kubernetes Liveness Probe**
```yaml
livenessProbe:
  httpGet:
    path: /actuator/health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

---

## **Best Practices**
1. **Threshold Tuning**:
   - Start with conservative values (e.g., `threshold=3`) and adjust based on failure rates.
   - Use **sliding window** for real-time monitoring (vs. fixed window).

2. **Fallback Design**:
   - Provide **degraded UX** (e.g., read-only mode) rather than silent failures.
   - Cache fallback responses to avoid repeated calls.

3. **Timeouts**:
   - Set timeouts **per operation**, not globally (e.g., 1s for API calls, 10s for DB queries).

4. **Observability**:
   - Correlate resilience events with traces (e.g., OpenTelemetry).
   - Alert on circuits opening (e.g., PagerDuty integration).

5. **Testing**:
   - Use **chaos engineering** tools (e.g., Gremlin) to validate resilience.
   - Mock failures in unit tests (e.g., `@CircuitBreaker` annotation with `mockServer`).

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use Together**                                                                 |
|---------------------------|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Adapter**               | Resilience integrations often require adapters for legacy systems.              | Wrapping a legacy SOAP service with retry logic.                                         |
| **Saga**                  | Compensating transactions depend on resilient service calls.                     | Distributed order processing with retries.                                              |
| **Rate Limiting**         | Bulkhead patterns share principles with token bucket algorithms.                 | Protecting APIs from DDoS while supporting retries.                                      |
| **CQRS**                  | Read models benefit from fallback mechanisms.                                    | Cache-first reads with DB fallback.                                                     |
| **Observer**              | Notifies external systems of resilience breaches (e.g., CircuitBreaker events). | Alerting SRE teams via webhooks.                                                       |

---

## **Troubleshooting**
| **Issue**                  | **Cause**                          | **Solution**                                                                 |
|----------------------------|------------------------------------|------------------------------------------------------------------------------|
| Circuit remains open       | Too aggressive `failureRateThreshold`. | Lower threshold or increase `waitDurationInOpenState`.                     |
| Timeouts on retries        | Backoff delay too long.             | Reduce `min` in `wait_exponential`.                                          |
| Bulkhead starvation        | Max workers set too low.            | Increase `max_workers` or use `SEMAPHORE` isolation.                          |
| Fallback not triggered     | Exception type not caught.          | Add `instanceof` checks in fallback method.                                  |

---
**References:**
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Spring Retry Guide](https://docs.spring.io/spring-retry/docs/current/reference/html/)
- [Chaos Engineering with Gremlin](https://www.gremlin.com/)