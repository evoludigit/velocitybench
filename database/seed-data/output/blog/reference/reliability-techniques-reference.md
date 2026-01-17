# **[Pattern] Reliability Techniques – Reference Guide**

## **Overview**
The **Reliability Techniques** pattern ensures that distributed systems remain operational despite failures, network partitions, or unexpected errors. This pattern combines principles from **resilient design**, **fault tolerance**, and **self-healing architectures** to minimize downtime and data loss. Common techniques include **circuit breakers**, **retries with backoff**, **idempotency**, **bulkheads**, and **fallback mechanisms**. Implementations must balance **availability**, **consistency**, and **latency** while accounting for edge cases like cascading failures.

Key goals:
- **Minimize failure impact** (limit blast radius).
- **Automate recovery** (self-healing).
- **Graceful degradation** (maintain partial functionality).
- **Fail fast** (avoid silent errors).

This guide covers implementation strategies, trade-offs, and integration considerations for cloud-native, microservices, and legacy systems.

---

## **Schema Reference**
A structured breakdown of reliability techniques and their properties.

| **Technique**          | **Purpose**                                  | **Key Metrics**               | **Trade-offs**                          | **Applicability**                     |
|-------------------------|---------------------------------------------|--------------------------------|-----------------------------------------|----------------------------------------|
| **Circuit Breaker**     | Prevents cascading failures by stopping retries after repeated failures. | Failure threshold, timeout, reset duration | Increased latency during open state; may mask transient issues. | Highly dependent services.            |
| **Retry with Backoff**  | Handles transient failures (timeouts, throttling). | Exponential backoff (base, max retries). | Risk of retry storms; unnecessary load on upstream. | Idempotent operations (e.g., API calls). |
| **Bulkheading**         | Isolates failures (e.g., thread pools, queues). | Resource limits (CPU, connections). | Higher resource overhead.               | High-concurrency workloads.           |
| **Idempotency**         | Ensures repeated identical operations have the same effect. | Unique request IDs or keys.   | Complexity in tracking state.           | Event-driven systems, payments.       |
| **Fallback Mechanisms** | Provides degraded but functional behavior. | Priority order (e.g., cache → DB → offline log). | Reduced accuracy/throughput.          | Critical user-facing services.       |
| **Graceful Degradation**| Limits scope of failure (e.g., disable features). | Feature flags, circuit states. | Perceived poor UX if not transparent.   | User-facing applications.             |
| **Timeouts**            | Prevents hanging calls.                     | Hard/soft timeouts, retries.   | May cut off valid responses.            | External API calls, DB queries.       |
| **Checkpointing**       | Saves state to recover from crashes.        | Interval frequency, durability. | Increased storage/overhead.             | Long-running processes.               |
| **Redundancy**          | Duplicates components (e.g., replicas, backups). | RPO/RTO (Recovery Point/Time Objective). | Higher cost, eventual consistency risks. | Mission-critical data.                |
| **Dead Letter Queues (DLQ)** | Isolates failed messages for later analysis. | TTL (time-to-live), retry policies. | Manual intervention required.          | Event-driven pipelines.               |

---

## **Implementation Details**

### **1. Circuit Breaker**
**How it works**: Monitors a downstream service’s health. If failures exceed a threshold (e.g., 5 in 10 seconds), it "trips" the breaker (blocks requests). After a cooldown period, it "resets" and allows limited traffic to test recovery.

**Example (Python with `tenacity` + `circuitbreaker`)**:
```python
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@circuit(failure_threshold=5, recovery_timeout=60)
def call_external_api():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

**Configuration Key Parameters**:
- `failure_threshold`: Number of consecutive failures to trip (e.g., 3).
- `recovery_timeout`: Seconds before attempting recovery.
- `timeout`: Request timeout (default: 30s).
- `exceptions`: Which exceptions count as failures (e.g., `requests.exceptions.RequestException`).

**When to Use**:
- Calling unstable third-party APIs.
- Database queries with high variability (e.g., bursting traffic).
- Avoid in stateless servers (race conditions if multiple instances trip simultaneously).

---

### **2. Retry with Backoff**
**How it works**: Retries failed operations with increasing delays to avoid overload. Uses **exponential backoff** (`delay *= base`).

**Example (Java with Spring Retry)**:
```java
@Retryable(
    value = {TimeoutException.class, ServiceUnavailableException.class},
    maxAttempts = 3,
    backoff = @Backoff(delay = 1000, multiplier = 2, maxDelay = 5000)
)
public String fetchData() {
    return restTemplate.getForObject("https://api.example.com/data", String.class);
}
```

**Key Parameters**:
- `maxAttempts`: Maximum retries (1–5 typical).
- `initialInterval`: Starting delay (ms).
- `multiplier`: Growth factor (e.g., `2` doubles each retry).
- `maxInterval`: Cap on delay (e.g., 10s).

**Jitter (Randomization)**:
Add randomness to delays to avoid synchronized retries (thundering herd problem):
```python
delay *= multiplier + random.uniform(0, 1)
```

**When to Avoid**:
- Non-idempotent operations (e.g., payments, stock purchases).
- Long-lived requests (risk of stale data).

---

### **3. Bulkheading**
**How it works**: Limits resource usage per request (e.g., thread pools, connection pools) to isolate failures.

**Example (Node.js with `p-queue`)**:
```javascript
const queue = new PQueue({ concurrency: 5 }); // Max 5 concurrent tasks
async function processOrder(order) {
  await queue.add(() => {
    await database.save(order); // Isolated DB connections
  });
}
```

**Implementation Strategies**:
- **Thread pools**: Limit threads per request (e.g., Java `ExecutorService`).
- **Connection pools**: Reuse DB/API connections (e.g., HikariCP).
- **Queue-based workloads**: Decouple producers/consumers (e.g., Kafka, RabbitMQ).

**Trade-offs**:
- Increased complexity (e.g., queue management).
- Higher memory usage for isolated resources.

---

### **4. Idempotency**
**How it works**: Ensures duplicate requests have the same effect as a single request. Useful for retries or deduplication.

**Example (REST API with Idempotency Key)**:
```http
POST /orders HTTP/1.1
Idempotency-Key: 12345-abcde
Content-Type: application/json

{
  "user_id": "67890",
  "amount": 100
}
```
**Server-side**:
```python
if request.headers.get("Idempotency-Key") in idempotency_cache:
    return cached_response, 200
else:
    result = process_order(request)
    idempotency_cache[request.headers["Idempotency-Key"]] = result
    return result, 201
```

**Implementation Tips**:
- Use **UUIDs** or **hashes** for keys.
- Cache responses with a **TTL** (e.g., 1 hour).
- Log idempotency keys for debugging.

**When to Use**:
- Payments, order processing, or any retry-prone workflow.
- Eventual consistency systems (e.g., CQRS).

---

### **5. Fallback Mechanisms**
**How it works**: Provides a secondary data source (e.g., cache → DB → offline log) if the primary fails.

**Example (Java with Spring Cloud Circuit Breaker)**:
```java
@CircuitBreaker(name = "paymentService", fallbackMethod = "fallbackPayment")
public PaymentProcessResult processPayment(PaymentRequest request) {
    return paymentClient.charge(request);
}

public PaymentProcessResult fallbackPayment(PaymentRequest request, Exception e) {
    // Fallback to offline processing
    return offlinePaymentProcessor.handle(request, e);
}
```

**Fallback Strategies**:
1. **Cache-first**: Use Redis/Memcached before hitting DB.
2. **Stub responses**: Return mocked data (for UX).
3. **Graceful degradation**: Disable non-critical features.
4. **Error boundaries**: Show user-friendly messages (e.g., "Retry later").

**Trade-offs**:
- Stale data (cache inconsistencies).
- Increased complexity in logic.

---

## **Query Examples**

### **1. Detecting a Tripped Circuit Breaker (Prometheus)**
```promql
# Circuit breaker state (e.g., "open" = 1)
up{job="api-service"} * on() group_left circuit_breaker_state {
  circuit_breaker_state: circuit_breaker_state{service="payment-service"}
} == 1
```
**Alert Rule**:
```yaml
- alert: CircuitBreakerOpen
  expr: circuit_breaker_state{state="open"} == 1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Circuit breaker for {{ $labels.service }} is open"
```

---

### **2. Monitoring Retry Failures (ELK Stack)**
**Log Pattern**:
```json
{
  "event": "retry_failure",
  "service": "order-service",
  "request_id": "123-456",
  "attempt": 5,
  "error": "timeout",
  "backoff_delay": "20s"
}
```
**Kibana Query**:
```
event: "retry_failure" AND service: "order-service" AND error: "timeout"
| stats count(*) as failures by service, error
```

---

### **3. Idempotency Key Validation (SQL)**
```sql
-- Check for existing order with the same idempotency key
SELECT id, status
FROM orders
WHERE idempotency_key = '12345-abcde';

-- Insert if not exists (PostgreSQL)
INSERT INTO orders (idempotency_key, user_id, amount)
VALUES ('12345-abcde', '67890', 100)
ON CONFLICT (idempotency_key) DO NOTHING;
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Pair With**                          |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Retry with Backoff**    | Handles transient failures.                                                   | Circuit Breaker, Bulkheading.                 |
| **Circuit Breaker**       | Prevents cascading failures.                                                  | Retry, Fallback Mechanisms.                   |
| **Bulkheading**           | Isolates resource usage per request.                                          | Thread Pools, Connection Pools.               |
| **Idempotency**           | Ensures safe retries.                                                         | Payments, Event-Driven Systems.               |
| **Fallback Mechanisms**   | Provides degraded functionality.                                             | Cache-Aside, Graceful Degradation.             |
| **Graceful Degradation**  | Limits impact of failures.                                                    | Feature Flags, Circuit Breakers.              |
| **Saga Pattern**          | Manages distributed transactions.                                             | Idempotency, Retries.                         |
| **CQRS**                  | Separates read/write models for scalability.                                   | Event Sourcing, Idempotency.                  |
| **Chaos Engineering**     | Proactively tests resilience.                                                 | All reliability techniques.                   |

---

## **Best Practices**
1. **Monitor Metrics**:
   - Track `failure_rate`, `retry_count`, `circuit_trip_count`.
   - Use APM tools (e.g., Datadog, New Relic) for distributed tracing.

2. **Avoid Over-Reliance**:
   - Circuit breakers should not replace **code-level fixes** (e.g., timeouts, retries for retriable errors).
   - Fallbacks should be **transparent** to users.

3. **Testing**:
   - **Chaos testing**: Simulate node failures, network partitions (e.g., Chaos Mesh, Gremlin).
   - **Load testing**: Validate retry/bulkhead behavior under load (e.g., Locust).

4. **Configuration**:
   - Use **feature flags** to toggle reliability mechanisms (e.g., disable retries in staging).

5. **Documentation**:
   - Clearly document **idempotency keys**, **circuit breaker thresholds**, and **fallback logic** for operators.

---
**References**:
- [Resilient Design Patterns (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/resilience-patterns)
- [Circuit Breaker (Netflix Hystrix)](https://github.com/Netflix/Hystrix)
- [Exponential Backoff (AWS Retries)](https://docs.aws.amazon.com/general/latest/gr/aws-service-specific-retry-strategies.html)
- [Idempotency in REST APIs (IETF RFC 7231)](https://www.rfc-editor.org/rfc/rfc7231.html)