# **Debugging Distributed Systems: A Troubleshooting Guide**

Distributed systems are inherently complex due to their reliance on multiple interconnected components (services, microservices, databases, queues, etc.). When issues arise, they often manifest in subtle, non-obvious ways—latency spikes, intermittent failures, or cascading outages. This guide provides a structured approach to diagnosing and resolving distributed system issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, use this checklist to identify symptoms and isolate the problem scope.

| **Symptom**                          | **Common Causes**                          | **Quick Checks**                                                                 |
|--------------------------------------|--------------------------------------------|----------------------------------------------------------------------------------|
| High latency in API calls            | Network congestion, DB overload, thrashing | Check `latency percentiles`, `queue backlog`, `CPU usage` on involved services.   |
| Intermittent timeouts                | Flaky network, rate limits, external APIs   | Enable distributed tracing; monitor `error rates` in `Prometheus/Grafana`.      |
| Degraded performance (slow responses) | Cold starts, memory leaks, inefficient queries | Review `memory GC logs`, `query execution plans`, `service cold starts`.        |
| Service crashes/restarts             | Memory leaks, unhandled exceptions, config errors | Check `logs`, `crash dumps`, `container health checks`.                          |
| Data inconsistency (e.g., duplicates, missing records) | Failed transactions, eventual consistency not respected | Review `event sourcing logs`, `transaction retries`, `replication lag`.       |
| Cascading failures                   | Poor circuit breakers, retries without backoff | Enable `distributed tracing`, audit `retries` and `backoff policies`.          |
| Authentication/Authorization failures | Misconfigured JWT/OAuth, expired tokens      | Validate `token expiration`, `RBAC policies`, `API gateway logs`.               |
| Increased error rates (5xx responses) | Dependency failures, concurrency issues   | Use `error tracking tools` (Sentry, Datadog) to identify root causes.            |

---

## **2. Common Issues & Fixes (With Code)**

### **Issue 1: High Latency in Microservices**
**Symptoms:**
- API responses taking > 2s (SLO breach).
- Slow database queries (`N+1` problem).
- Network delays between services.

**Root Causes:**
- Unoptimized database queries (e.g., `SELECT *`).
- Lack of caching (e.g., Redis/Memcached).
- Too many synchronous calls between services.

**Fixes:**

#### **Optimize Database Queries**
```sql
-- Bad: Fetches all columns, inefficient joins
SELECT * FROM users WHERE id = 1;

-- Good: Use indexed columns and limit data
SELECT id, email FROM users WHERE id = 1;
```

#### **Implement Caching (Redis Example)**
```python
# Before: Always hits DB
def get_user(user_id):
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")

# After: Cached with TTL (1 hour)
import redis
r = redis.Redis()
def get_user(user_id):
    cached = r.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    r.setex(f"user:{user_id}", 3600, json.dumps(user))  # Cache for 1 hour
    return user
```

#### **Use Async/Await for I/O-Bound Tasks**
```javascript
// Before: Blocking call
async function fetchUser() {
    const user = await db.queryUser(); // Blocks event loop
    return user;
}

// After: Non-blocking (Node.js example)
async function fetchUser() {
    const user = await db.queryUser(); // Runs in background
    return user;
}
```

---

### **Issue 2: Intermittent Timeouts**
**Symptoms:**
- Inconsistent `504 Gateway Timeout` errors.
- External API failures retrying too aggressively.

**Root Causes:**
- No retry logic with backoff.
- Hard-coded timeouts (e.g., 5s for slow APIs).
- Missing circuit breakers.

**Fixes:**

#### **Implement Retry with Exponential Backoff**
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_external_api():
    response = requests.get("https://external-api.com/data")
    if response.status_code != 200:
        raise Exception("API failed")
    return response.json()
```

#### **Use Circuit Breaker Pattern (Hystrix/Resilience4j)**
```java
// Using Resilience4j
@CircuitBreaker(name = "externalApi", fallbackMethod = "fallback")
public String callExternalApi() {
    return restTemplate.getForObject("https://external-api.com/data", String.class);
}

public String fallback(Exception e) {
    return "Service unavailable, returning cached data";
}
```

---

### **Issue 3: Data Inconsistency (Eventual Consistency Issues)**
**Symptoms:**
- Duplicate orders.
- Missing database records after retries.

**Root Causes:**
- Failed transactions (e.g., `INSERT` + `UPDATE` in separate calls).
- No idempotency keys.
- Eventual consistency not respected (e.g., Kafka lag).

**Fixes:**

#### **Use ACID Transactions (Database-Level)**
```sql
-- Single transaction to prevent inconsistency
BEGIN;
INSERT INTO orders (user_id, amount) VALUES (1, 100);
UPDATE users SET balance = balance - 100 WHERE id = 1;
COMMIT;
```

#### **Implement Idempotency Keys (for Retries)**
```python
import uuid

def create_order(user_id, amount):
    idempotency_key = str(uuid.uuid4())
    if db.get(f"order:{idempotency_key}") is not None:
        return "Duplicate order detected"
    db.execute(
        "INSERT INTO orders (id, user_id, amount) VALUES (?, ?, ?)",
        (idempotency_key, user_id, amount)
    )
    return f"Order processed with key: {idempotency_key}"
```

#### **Monitor Event Processing Lag (Kafka Example)**
```bash
# Check Kafka consumer lag
kafka-consumer-groups --bootstrap-server broker:9092 --group my-group --describe
# Output: LAG > 0 indicates stale events
```

---

### **Issue 4: Cascading Failures**
**Symptoms:**
- One service failure brings down dependent services.
- Retries cause snowballing errors.

**Root Causes:**
- No circuit breakers.
- No dependency isolation.
- Aggressive retries without backoff.

**Fixes:**

#### **Isolate Dependencies with Circuit Breakers**
```typescript
// Using Axios + Circuit Breaker
import { CircuitBreaker } from "opossum";

const breaker = new CircuitBreaker({
    timeout: 5000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
});

async function callPaymentService() {
    return breaker.execute(() =>
        axios.post("https://payment-service/api/charge", payload)
    );
}
```

#### **Use Bulkheads (Limit Concurrency)**
```python
from concurrent.futures import ThreadPoolExecutor

def process_payments(orders):
    with ThreadPoolExecutor(max_workers=5) as executor:  # Limit concurrency
        results = list(executor.map(lambda o: call_payment_service(o), orders))
    return results
```

---

## **3. Debugging Tools & Techniques**

### **A. Distributed Tracing**
- **Tools:** Jaeger, OpenTelemetry, Zipkin.
- **How:** Instrument services with trace IDs to track requests across services.
  ```bash
  # Start Jaeger
  docker run -d -p 16686:16686 jaegertracing/all-in-one:latest
  ```
  ```python
  # Instrument with OpenTelemetry
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)

  with tracer.start_as_current_span("process_order"):
      # Business logic
  ```

### **B. Logging & Structured Logging**
- **Tools:** ELK Stack, Loki, Datadog.
- **Best Practices:**
  - Correlation IDs for tracing requests.
  - Structured logs (JSON) for easy querying.
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)

  # Log with correlation ID
  logger.info(
      {"correlation_id": request.headers.get("X-Correlation-ID"), "event": "order_created"}
  )
  ```

### **C. Metrics & Monitoring**
- **Tools:** Prometheus + Grafana, Datadog, New Relic.
- **Key Metrics:**
  - **Latency percentiles** (P50, P90, P99).
  - **Error rates** (4xx, 5xx).
  - **Queue depths** (Kafka, RabbitMQ).
  - **Memory/CPU usage**.
  ```yaml
  # Example Prometheus alert rule
  - alert: HighLatency
      expr: rate(http_request_duration_seconds{quantile="0.99"}[5m]) > 2
      for: 5m
      labels:
        severity: warning
  ```

### **D. Postmortem Analysis**
- **Root Cause Analysis (RCA):**
  1. **Reproduce** the issue in staging.
  2. **Check logs** from all involved services.
  3. **Review metrics** (latency, errors, throughput).
  4. **Isolate the bottleneck** (e.g., DB, network, code).
- **Example Template:**
  ```
  Incident: Payment Service Timeout
  Time: Jan 10, 2024, 3:00 PM
  Root Cause: External API (Stripe) had a 99th percentile latency of 8s (SLO breach).
  Fix: Implemented retry with exponential backoff + fallback to cached data.
  ```

---

## **4. Prevention Strategies**

### **A. Design for Failure**
- **Chaos Engineering:** Use tools like Gremlin or Chaos Mesh to test failure scenarios.
- **Circuit Breakers:** Always protect dependent services.
- **Retries with Backoff:** Never retry blindly.

### **B. Observability Best Practices**
- **Instrument Everything:** Logs, metrics, traces.
- **SLOs & Error Budgets:** Define acceptable error rates.
- **Automated Alerts:** Set up alerts for critical failures.

### **C. Code-Level Safeguards**
- **Idempotency:** Design APIs to be retry-safe.
- **Bulkheads:** Limit concurrent executions (e.g., thread pools).
- **Graceful Degradation:** Fallback to cached data when APIs fail.

### **D. Infrastructure Resilience**
- **Multi-Region Deployments:** Reduce latency and improve fault tolerance.
- **Auto-Scaling:** Handle traffic spikes gracefully.
- **Database Replication:** Ensure high availability.

---

## **Summary Checklist for Distributed Debugging**
| **Step**               | **Action**                                                                 |
|------------------------|---------------------------------------------------------------------------|
| **Reproduce**          | Isolate the issue (staging/production).                                   |
| **Check Logs**         | Look for correlation IDs, errors, and time stamps.                       |
| **Review Metrics**     | Use Prometheus/Grafana for latency, errors, and queue depth.              |
| **Enable Tracing**     | Correlate requests across services with Jaeger/OpenTelemetry.            |
| **Test Fixes**         | Deploy changes incrementally and monitor impact.                          |
| **Document**           | Write a postmortem for future reference.                                  |

---

## **Final Notes**
Distributed debugging requires **patience, correlation, and systematic elimination**. Focus on:
1. **Logs first** (structured, correlation IDs).
2. **Metrics second** (latency, errors, throughput).
3. **Traces third** (end-to-end request flow).

By adopting these practices, you’ll reduce mean time to resolution (MTTR) and build more resilient systems.