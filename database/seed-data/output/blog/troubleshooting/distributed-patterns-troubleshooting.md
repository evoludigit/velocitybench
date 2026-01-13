# **Debugging Distributed Patterns: A Troubleshooting Guide**

Distributed Patterns—such as **Saga, CQRS, Event Sourcing, Circuit Breaker, and Retry Mechanisms**—are essential for building resilient, scalable microservices systems. However, their distributed nature introduces complexity, leading to common issues like **network latency, inconsistent state, cascading failures, and debugging challenges**.

This guide provides a **structured, actionable approach** to diagnosing and resolving issues in distributed systems using these patterns.

---

## **1. Symptom Checklist**

Before diving into debugging, systematically check for the following symptoms:

| **Category**               | **Symptom**                                                                 | **Likely Cause**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Network & Connectivity** | Timeouts, slow responses, intermittent failures                              | High latency, DNS issues, firewall blocks, or overloaded services.               |
| **State Inconsistency**    | Inconsistent data across services, lost transactions, or duplicate events   | Failed compensating transactions, event replay issues, or message loss.          |
| **Failure Handling**       | Cascading failures, repeated retries, or stuck services                     | Misconfigured retries, circuit breakers not tripping, or deadlocks in sagas.     |
| **Monitoring & Logging**   | Missing logs, uncorrelated events, or incomplete audit trails                 | Improper logging, missing correlation IDs, or event sourcing gaps.               |
| **Performance Issues**     | High CPU/memory usage, throttling, or degraded throughput                   | Inefficient load balancing, unoptimized queries, or unhandled backpressure.       |
| **Event Processing**       | Duplicate/missing events, or stale data                                      | Event source not replayable, duplicates from retries, or consumer lag.           |

---

## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Failed Transactions in Saga Pattern**
**Symptoms:**
- One or more steps in a saga fail, but the compensating transaction doesn’t roll back.
- Inconsistent database state (e.g., payment received but order not confirmed).

**Root Cause:**
- Compensating transactions not executed due to:
  - Timeouts in asynchronous calls.
  - Missing error handling in compensators.
  - Saga orchestration stuck due to retries.

**Fix:**
```java
// Example: Saga Step with Retry and Compensator
public class OrderSaga {
    private final OrderService orderService;
    private final PaymentService paymentService;

    public void executeOrder(Order order) {
        try {
            // Step 1: Place Order
            orderService.placeOrder(order);

            // Step 2: Process Payment (with retry)
            retryPolicy.execute(() -> paymentService.processPayment(order.getPayment()),
                new ExponentialBackoffRetry(3, 1000));

            // If payment fails, compensator will reverse the order
        } catch (Exception e) {
            executeCompensation(order.getId());
            throw e;
        }
    }

    private void executeCompensation(String orderId) {
        try {
            paymentService.cancelPayment(orderId); // Compensator
            orderService.cancelOrder(orderId);     // Compensator
        } catch (Exception e) {
            log.error("Compensation failed for order: {}", orderId, e);
        }
    }
}
```
**Debugging Steps:**
1. Check saga logs for failed steps.
2. Verify compensators are called (add logging).
3. Use **Saga Tracking** (e.g., database table with `status` and `compensationAttempted` flags).

---

### **Issue 2: Event Sourcing: Lost or Duplicate Events**
**Symptoms:**
- Events not replaying correctly.
- Stale data due to missing events.

**Root Cause:**
- Events not persisted before publishing (race conditions).
- Event consumers fail to process due to duplicates.

**Fix:**
```java
// Event Sourcing with Idempotency
@Service
public class OrderEventService {
    @Transactional
    public void sendOrderCreatedEvent(Order order) {
        // Publish event AFTER persisting (to ensure durability)
        eventBus.publish(new OrderCreatedEvent(order.getId(), order.getUserId()));
        orderEventRepository.save(new OrderEvent(order.getId(), "ORDER_CREATED"));
    }

    @Retry(maxAttempts = 3)
    public void consumeEvent(OrderCreatedEvent event) {
        // Idempotent processing (no side effects on reprocessing)
        orderService.applyEvent(event);
    }
}
```
**Debugging Steps:**
1. **Replay events from scratch** (if using Event Sourcing DB).
2. **Check event store consistency** (e.g., `SELECT COUNT(*) FROM events WHERE id = ?`).
3. **Enable duplicate detection** in event consumers (e.g., Kafka `isolation.level=read_committed`).

---

### **Issue 3: Circuit Breaker Not Triggering (False Positives/Negatives)**
**Symptoms:**
- System keeps failing under load despite circuit breaker trips.
- Overly aggressive retries causing cascading failures.

**Root Cause:**
- Incorrect **failure threshold** (e.g., too high).
- **Half-open state** not properly tested.
- **Retry policy** allowing too many attempts.

**Fix (Resilience4j Example):**
```java
// Configure Circuit Breaker with appropriate settings
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50) // Trip if 50% failures in 10s
    .waitDurationInOpenState(Duration.ofSeconds(30))
    .permittedNumberOfCallsInHalfOpenState(2)
    .recordExceptions(TimeoutException.class)
    .build();

// Usage
CircuitBreaker circuitBreaker = CircuitBreaker.of("paymentService", config);
Supplier<Payment> paymentSupplier = circuitBreaker.run(
    () -> paymentService.fetchPayment(), // Fallback if open
    throwable -> fallbackPayment()
);
```
**Debugging Steps:**
1. **Check Open/Closed states** in metrics (e.g., Prometheus).
2. **Test half-open state** manually (disable circuit briefly).
3. **Adjust thresholds** based on SLA (e.g., 99% availability).

---

### **Issue 4: Retry Mechanism Causing Infinite Loops**
**Symptoms:**
- Service keeps retrying indefinitely.
- Queue builds up with stale requests.

**Root Cause:**
- No **max retry limit**.
- Retry delay too short for transient issues.

**Fix:**
```java
// Exponential Backoff with Max Retries
RetryConfig config = RetryConfig.custom()
    .maxAttempts(3) // Prevent infinite retries
    .waitRatio(2)   // Double delay each time
    .retryExceptions(IOException.class)
    .build();

@Override
public void submitOrder(Order order) {
    retryTemplate.execute(config, context -> {
        externalService.submit(order);
    });
}
```
**Debugging Steps:**
1. **Log retry attempts** (include `attemptNumber`).
2. **Set a timeout** for retries (e.g., 1 hour max).
3. **Monitor retry queue** (e.g., Kafka consumer lag).

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**          | **Purpose**                                                                 | **Example**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Distributed Tracing**     | Track requests across services (e.g., OpenTelemetry, Jaeger)               | `tracer.spanBuilder("order-service").startSpan()`                          |
| **Audit Logging**           | Correlate events with request IDs                                           | `log.info("Event processed, requestId={}", requestId)`                     |
| **Health Checks**           | Detect unhealthy services before failures propagate                         | `/actuator/health` (Spring Boot)                                            |
| **Chaos Engineering**       | Test failure resilience (e.g., Gremlin, Chaos Mesh)                         | Kill a service randomly to see circuit breakers in action                  |
| **Event Replay**            | Debug missing/duplicate events                                              | `eventStore.replayEventsFrom(offset)`                                      |
| **Metrics & Alerts**        | Monitor retry rates, error percentages, and latency                         | Prometheus + Grafana dashboards                                              |
| **Postmortem Analysis**     | Document failures for future prevention                                     | Blameless retrospectives with action items                                   |

---

## **4. Prevention Strategies**

### **A. Design-Time Mitigations**
✅ **Use Idempotency Keys** – Ensure retries don’t cause duplicates.
✅ **Implement Circuit Breakers Early** – Prevent cascade failures.
✅ **Design for Failure** – Assume services will fail; compensate gracefully.
✅ **Eventual Consistency Guarantees** – Use sagas for ACID across services.

### **B. Runtime Optimizations**
⚡ **Optimize Retry Policies** – Use exponential backoff.
⚡ **Batch Small Requests** – Reduce overhead (e.g., Kafka batching).
⚡ **Rate Limiting** – Prevent throttling (e.g., Redis rate limiter).
⚡ **Chaos Testing in CI/CD** – Automate failure scenarios.

### **C. Observability Best Practices**
📊 **Correlation IDs** – Track a single request across services.
📊 **Structured Logging** – Use JSON logs for easier parsing.
📊 **Distributed Tracing** – Visualize latency bottlenecks.
📊 **Alert on Anomalies** – Set up dashboards for failure rates.

---

## **5. Quick Checklist for Fast Resolution**
🔹 **Is the issue transient?** (Check retries, circuit breakers)
🔹 **Are events being lost/replayed?** (Verify event store consistency)
🔹 **Is a service overloaded?** (Check metrics, scale horizontally)
🔹 **Are compensations failing?** (Inspect saga logs)
🔹 **Is tracing available?** (Use OpenTelemetry to follow request flow)

---

### **Final Thoughts**
Distributed patterns introduce complexity, but with **structured debugging, observability, and resilience practices**, most issues can be resolved efficiently. Focus on:
1. **Correlation** (tracing logs across services).
2. **Idempotency** (preventing duplicates).
3. **Graceful Degradation** (fallbacks, circuit breakers).
4. **Automated Detection** (metrics, alerts).

By following this guide, you’ll **reduce mean time to resolution (MTTR)** and build more robust distributed systems. 🚀