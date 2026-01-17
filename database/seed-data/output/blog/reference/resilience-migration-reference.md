# **[Resilience Migration] Reference Guide**

---

## **Overview**
The **Resilience Migration** pattern enables applications to transition from non-resilient (e.g., synchronous, brittle) interactions to resilient, asynchronous, and fault-tolerant behaviors. This pattern is critical for migrating legacy systems or monolithic architectures to **microservices**, **event-driven architectures**, or **cloud-native** environments where failures are inevitable.

Resilience migration involves:
- **Decoupling** monolithic dependencies into independent, resilient components.
- **Introducing circuit breakers**, **retry policies**, **fallbacks**, and **bulkheads** to handle failures gracefully.
- **Minimizing downtime** during migration by using **dual-write** or **event sourcing** strategies.

This pattern ensures **zero-downtime transitions**, **gradual resilience adoption**, and **backward compatibility** during migration.

---

## **Key Concepts & Implementation Details**

### **1. Migration Strategies**
| **Strategy**          | **Description**                                                                 | **Use Case**                                  |
|-----------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Dual-Write**        | Write data to both legacy and new systems until the new system stabilizes.      | Transition from SQL to NoSQL.                |
| **Event Sourcing**    | Persist all state changes as a sequence of events for replayability.           | Financial systems requiring auditability.     |
| **Canary Deployment** | Gradually shift traffic to the new resilient system while monitoring.          | High-traffic web applications.               |
| **Feature Flags**     | Toggle resilience features on/off without deployment.                          | A/B testing resilience improvements.          |
| **Sidecar Pattern**   | Deploy a helper service alongside a legacy service to handle resilience.      | Legacy microservices lacking resilience.      |

---

### **2. Resilience Mechanisms**
| **Mechanism**         | **Description**                                                                 | **When to Use**                          |
|-----------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **Circuit Breaker**   | Stops cascading failures by disabling a failing service after repeated errors. | Distributed systems with unreliable APIs. |
| **Retry with Backoff**| Automatically retries failed requests with exponential delays.                | Transient network issues.               |
| **Bulkhead**          | Limits concurrency to prevent a single failure from overwhelming the system. | High-throughput APIs.                   |
| **Fallback**          | Provides degraded but functional behavior when primary resources fail.      | Critical services needing graceful degradation. |
| **Compression**       | Reduces payload size to improve latency and bandwidth usage.              | Cross-data-center communications.        |
| **Rate Limiting**     | Controls request volume to prevent overload.                                  | External APIs or public-facing services.  |

---

### **3. Migration Phases**
1. **Assessment Phase**
   - Identify **failure points** (e.g., timeouts, deadlocks, cascading failures).
   - Audit dependencies for resilience gaps.
   - Define **SLOs (Service Level Objectives)** and **SLAs (Service Level Agreements)**.

2. **Isolation Phase**
   - Introduce **boundaries** between legacy and new components.
   - Implement **circuit breakers** for external dependencies.
   - Use **asynchronous messaging** (e.g., Kafka, RabbitMQ) instead of synchronous calls.

3. **Gradual Adoption Phase**
   - Shift **non-critical** workloads to the new system first.
   - Use **feature flags** to enable resilience features incrementally.
   - Monitor **error rates** and **latency** during the transition.

4. **Full Migration Phase**
   - Sunset legacy components once new system is stable.
   - Ensure **data consistency** (e.g., using **eventual consistency** or **dual-write**).
   - Validate **end-to-end resilience** under failure scenarios.

---

### **4. Data Consistency Strategies**
| **Strategy**          | **Description**                                                                 | **Trade-offs**                          |
|-----------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **Dual-Write**        | Write to both legacy and new systems until migration is complete.             | Higher storage costs, eventual consistency. |
| **Event Sourcing**    | Replay events to rebuild state if needed.                                      | Complex schema evolution.                |
| **CQRS (Command Query Responsibility Segregation)** | Separate read/write models for scalability. | Additional complexity in event handling. |
| **Saga Pattern**      | Break long transactions into smaller, compensatable steps.                | Harder to debug; requires idempotency.   |

---

## **Schema Reference**
Below are common schemas used in resilience migration.

### **1. Circuit Breaker Configuration**
```json
{
  "circuitBreaker": {
    "name": "PaymentService",
    "failureThreshold": 5,          // Max failures before tripping
    "successThreshold": 3,          // Min successes to reset
    "timeout": "30s",               // Timeout for requests
    "resetTimeout": "1m",           // Time before retrying
    "fallback": {
      "method": "returnDefaultPayment",  // Fallback method
      "response": { "status": "fallback", "message": "Payment service unavailable" }
    }
  }
}
```

### **2. Retry Policy**
```json
{
  "retryPolicy": {
    "maxAttempts": 3,
    "initialInterval": "100ms",
    "maxInterval": "5s",
    "backoffFactor": 2.0,          // Exponential backoff (2^x)
    "jitter": true                 // Randomize delays to avoid thundering herd
  }
}
```

### **3. Bulkhead Configuration**
```json
{
  "bulkhead": {
    "concurrency": 10,              // Max concurrent requests
    "queueCapacity": 50,            // Pending requests buffer
    "rejectPolicy": "abort"         // "abort", "queue", or "allow" on overload
  }
}
```

---

## **Query Examples**

### **1. Checking Circuit Breaker Status (Resilience4j)**
```java
// Java (Resilience4j)
CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("paymentService");
if (circuitBreaker.getState().equals(State.OPEN)) {
    System.out.println("Payment service is down. Using fallback.");
} else {
    System.out.println("Payment service is available.");
}
```

### **2. Retry Failed API Call (Python with `tenacity`)**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_external_api():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()  # Raise exception on failure
    return response.json()
```

### **3. Dual-Write Database Transactions (PostgreSQL + MongoDB)**
```sql
-- PostgreSQL (Legacy)
BEGIN;
INSERT INTO orders (user_id, amount) VALUES (123, 100.00);
INSERT INTO audit_logs (action, table, data) VALUES ('insert', 'orders', '{"user_id":123,"amount":100}');
COMMIT;

-- MongoDB (New System - Async via Kafka)
{
  "order": {
    "user_id": 123,
    "amount": 100.00,
    "timestamp": ISODate("2023-10-01T12:00:00Z")
  }
}
```

---

## **Monitoring & Observability**
To ensure a smooth migration, implement:
- **Distributed Tracing** (e.g., **Jaeger**, **OpenTelemetry**) to track request flow.
- **Metrics** for:
  - **Error rates** (`error_rate`).
  - **Latency percentiles** (`p99_latency`).
  - **Circuit breaker state** (`circuit_breaker.open`).
- **Logging** with structured formats (e.g., **JSON logs**).
- **Alerting** for:
  - `error_rate > 1%`.
  - `circuit_breaker.state = OPEN`.
  - `latency > 2s`.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Circuit Breaker]**     | Prevents cascading failures by stopping calls to a failing service.           | High-latency external APIs.              |
| **[Retry with Backoff]**  | Automatically retries transient failures with increasing delays.              | Network partitions, temporary outages.   |
| **[Bulkhead]**            | Isolates resources to limit the impact of failures.                          | High-throughput services.               |
| **[Saga Pattern]**        | Manages distributed transactions using compensating actions.                | Microservices with complex workflows.    |
| **[Resilient Messaging]** | Ensures reliable event delivery (e.g., Kafka, SQS).                          | Event-driven architectures.              |
| **[CQRS]**                | Separates read and write models for scalability.                              | High-read workloads with complex queries.|
| **[Event Sourcing]**      | Stores state changes as events for replayability.                            | Audit-heavy domains (e.g., finance).     |

---

## **Anti-Patterns to Avoid**
❌ **Big Bang Migration** – Cutting over abruptly leads to extended downtime.
❌ **Ignoring Timeouts** – Infinite retries can exhaust resources.
❌ **No Fallback Mechanism** – Applications crash if primary services fail.
❌ **Over-Reliance on Retries** – Retry loops can mask deeper issues.
❌ **Neglecting Monitoring** – Undetected failures propagate silently.

---

## **Tools & Libraries**
| **Tool/Library**         | **Purpose**                                                                 | **Language/Platform**               |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------|
| **Resilience4j**         | Java library for circuit breakers, retries, rate limiting.                  | Java                            |
| **Polly**                | .NET resilience library (retry, fallback, circuit breaker).                  | C#/.NET                      |
| **Hystrix**              | Netflix’s circuit breaker and fallback library.                            | Java                            |
| **Tenacity**             | Python retry library with exponential backoff.                             | Python                         |
| **Kafka**                | Distributed event streaming for resilient messaging.                        | Multi-language                   |
| **Prometheus + Grafana** | Monitoring and alerting for resilience metrics.                            | Cloud-native                    |
| **OpenTelemetry**        | Distributed tracing for observability.                                      | Multi-language                   |

---
**Final Notes:**
- **Start small** – Migrate one service at a time.
- **Test failures** – Validate resilience under controlled outages.
- **Iterate** – Refine policies based on real-world failure patterns.

Would you like additional details on any specific section?