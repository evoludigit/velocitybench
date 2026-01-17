```markdown
---
title: "Resilience Testing: Building APIs That Don’t Crash When the WorldGoes Wrong"
date: 2023-11-15
tags: ["database", "api-design", "resilience", "testing", "backend-engineering"]
author: "Alex Carter"
image: "/images/resilience-testing-diagram.png"
---

# Resilience Testing: Building APIs That Don’t Crash When the World Goes Wrong

Every backend engineer has faced it: an API deployment that seems perfect until you hit production and it collapses under "unexpected" load, network partitions, or database failures. Resilience isn't just about writing robust code—it's about designing systems that can handle failure gracefully without catastrophically impacting users. In this post, we'll explore the **Resilience Testing** pattern: a framework for validating your system’s behavior under fault conditions.

## Why Resilience Matters

Modern applications are distributed by design—microservices talk to each other, databases sprawl across regions, and cloud providers can (and will) fail. The problem isn't failure—it's *inevitable* failure. A system that works in the lab but crashes in production is like a bridge designed for calm weather but not earthquakes.

Resilience testing goes beyond unit tests. It’s about simulating real-world chaos and verifying your system can recover. Think of it as a stress test for failure modes, not just happy paths.

---

## The Problem: Why Systems Fail Under Pressure

Let’s examine three common failure scenarios that resilience testing addresses:

1. **Network Partitions**: Services lose connectivity to databases or other services.
2. **Resource Exhaustion**: High traffic consumes CPU, memory, or disk I/O.
3. **Data Corruption**: Databases crash or return inconsistent results.

Here’s a real-world example:
Imagine your `OrderService` depends on a `PaymentService`. If `PaymentService` is down, what should `OrderService` do? Return a 500 error? Queue the order? Fall back to offline mode? Without resilience testing, you won’t know until it’s too late.

---

## The Solution: Resilience Testing Patterns

Resilience testing validates how your system behaves under specific failure conditions. It’s not about testing individual components in isolation but the *interactions* between them. Here are the key components:

### 1. **Chaos Engineering Principles**
   - **Define Failure Scenarios**: Identify critical points where failure could break the system (e.g., database latency, API timeouts).
   - **Simulate Failures in Isolation**: Force failures (e.g., kill a process, corrupt a DB) in staging before production.
   - **Observe System Behavior**: Does your system recover? Does it degrade gracefully?

### 2. **Resilience Mechanisms**
   Implement these in your code **before** testing:
   - **Circuit Breakers**: Stop retries after repeated failures (e.g., Hystrix, Polly).
   - **Retries with Backoff**: Exponential backoff to avoid overwhelming a failing service.
   - **Bulkheads**: Isolate failures to prevent cascading (e.g., thread pools, rate limiting).
   - **Fallbacks**: Predefined responses when dependencies fail (e.g., cached data, degraded mode).

### 3. **Testing Strategies**
   - **Chaos Experiments**: Use tools like [Chaos Mesh](https://chaos-mesh.org/) or [Gremlin](https://www.gremlin.com/) to inject failures.
   - **Failure Injection Tests**: Mock dependencies to force errors (e.g., `payments-service` returns 500 30% of the time).
   - **Load Testing with Failures**: Combine [k6](https://k6.io/) with artificial network degradation.

---

## Implementation Guide: Resilience Testing in Practice

Let’s walk through a practical example using a Node.js API with PostgreSQL and a simulated failure.

### Example: Order Service with Payment Service Dependency

#### 1. **Define the Failure Scenario**
Our `OrderService` calls `PaymentService` to process payments. If `PaymentService` fails, we want:
- Retry 3 times with exponential backoff.
- If all retries fail, mark the order as "pending" and notify the user.

#### 2. **Implement Resilience Mechanisms**

##### **Circuit Breaker (Polly.js)**
We’ll use [Polly.js](https://github.com/microsoft/polly) to retry and fail fast.

```javascript
// order-service/payment-client.js
const { AsyncRetryPolicy } = require('polly');
const { RetryStrategy } = require('polly/lib/strategies');

// Configure retry with exponential backoff
const retryPolicy = new AsyncRetryPolicy({
  retryTimeout: 10000, // Total time for retries
  retries: 3,
  strategy: new RetryStrategy({
    delay: 1000,
    backoffType: 'exponential' // 1s, 2s, 4s...
  })
});

// Mock payment service (replace with actual HTTP client)
async function processPayment(orderId, amount) {
  return retryPolicy.executeAsync(async () => {
    const response = await fetch('http://payments-service/api/process', {
      method: 'POST',
      body: JSON.stringify({ orderId, amount }),
    });
    if (!response.ok) throw new Error(`Payment failed: ${response.status}`);
    return response.json();
  });
}
```

##### **Fallback Logic**
If retries fail, log and return a fallback response.

```javascript
// order-service/order-service.js
async function createOrder(userId, items) {
  try {
    const paymentResult = await processPayment(orderId, total);
    // Save order to DB
    await db.query(`INSERT INTO orders (user_id, status) VALUES ($1, $2)`, [
      userId, 'paid'
    ]);
    return { status: 'success', payment: paymentResult };
  } catch (error) {
    // Log the failure
    console.error(`Payment failed for order ${orderId}:`, error);

    // Fallback: Mark as pending and notify user
    await db.query(`INSERT INTO orders (user_id, status) VALUES ($1, $2)`, [
      userId, 'pending'
    ]);
    await sendNotification(userId, 'Your order is pending payment.');
    return { status: 'pending', message: 'Retry later.' };
  }
}
```

#### 3. **Test with Failure Injection**
Use [Pact](https://docs.pact.io/) or a mock server to simulate `PaymentService` failures.

```javascript
// __tests__/payment-service-mock.js
const { createServer } = require('http');
const { mockPaymentService } = require('pact-mock-service');

const options = {
  ports: { 'payments-service': 3020 },
  providers: [
    {
      name: 'PaymentService',
      requests: [
        {
          method: 'POST',
          path: '/api/process',
          responses: [
            { status: 200, body: { success: true } },
            { status: 500, body: { error: 'Service Unavailable' } }, // Force failure 30% of the time
          ]
        }
      ]
    }
  ]
};

const server = createServer(options);
server.listen(3010, () => {
  console.log('Mock server running on port 3010');
});
```

Run your test suite against the mock server:
```bash
# Start mock server
npm run mock:start

# Run tests with failure injection
npm test -- --mock
```

#### 4. **Chaos Experiment (Optional)**
For deeper testing, use [Chaos Mesh](https://chaos-mesh.org/) to kill pods or introduce latency:
```yaml
# chaos-mesh-pod-stress.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: payment-service-stress
spec:
  action: pod-failure
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: payment-service
  duration: "30s"
```

Apply the experiment:
```bash
kubectl apply -f chaos-mesh-pod-stress.yaml
```

---

## Common Mistakes to Avoid

1. **Testing in Isolation**:
   - ❌ Running unit tests on `PaymentService` without mocking failures.
   - ✅ Test the **interaction** between `OrderService` and `PaymentService` under stress.

2. **Over-Reliance on Retries**:
   - Retrying indefinitely on a failing service can amplify problems (e.g., database connection pools exhausted).
   - ✅ Set reasonable retry limits (e.g., 3 retries with backoff).

3. **Ignoring Timeouts**:
   - Not setting timeouts on dependent calls can hang your system.
   - ✅ Always add timeouts (e.g., `fetch` with `{ timeout: 5000 }`).

4. **No Fallbacks**:
   - Assuming your system will always work is risky.
   - ✅ Design for failure: Can users proceed without the failed service?

5. **Testing Only Happy Paths**:
   - Resilience testing is about **unhappy paths**.
   - ✅ Simulate failures in staging before production.

---

## Key Takeaways

- **Resilience testing is about failure scenarios, not just functionality**.
  - Test how your system recovers from network drops, timeouts, and database failures.

- **Implement resilience mechanisms before testing**:
  - Circuit breakers, retries, fallbacks, and bulkheads are non-negotiable.

- **Use tools to simulate failures**:
  - Pact for API mocking, Chaos Mesh for Kubernetes, or manual retry delays.

- **Gradual rollout**:
  - Start with chaos experiments in staging. Only move to production after validating recovery.

- **Document failure modes**:
  - Know which failures your system tolerates and which are critical.

- **Monitor post-deployment**:
  - Use observability (e.g., Prometheus, Datadog) to detect resilience issues in production.

---

## Conclusion

Resilience testing isn’t about making your system perfect—it’s about preparing for the inevitable. By designing APIs that handle failure gracefully and testing those behaviors proactively, you’ll build systems that survive when others fail.

### Next Steps:
1. **Add resilience mechanisms** to your critical dependencies (e.g., database timeouts, retry policies).
2. **Set up a mock service** to inject failures in your tests.
3. **Run a chaos experiment** in staging next month—knowing you’re ready is half the battle.

Resilience isn’t a one-time task; it’s a mindset. Start small, iterate, and your systems will thank you during the next outage.

---
```

---
**Image Suggestion**:
Include a diagram like this for the post:
```
┌───────────────────────────────────────────────────┐
│                     Order Service                 │
├───────────────────────────────────────────────────┤
│  ✅ Retry 3x with backoff → PaymentService       │
│  ⚠️ On failure: Mark order as 'pending'         │
│  📈 Monitor & alert on prolonged outages        │
└───────────────────────────────────────────────────┘
       │
       ▼
┌───────────────────────────────────────────────────┐
│                   PaymentService                 │
├───────────────────────────────────────────────────┤
│  🔄 Chaos tool injects 500 errors (30% of calls)   │
│  🚨 Circuit breaker trips after 3 retries         │
└───────────────────────────────────────────────────┘
```
This visualizes the resilience loop.
```