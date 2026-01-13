```markdown
---
title: "Distributed Systems Best Practices: Building Scalable, Resilient Applications"
date: 2023-09-15
author: Jane Techno
description: "Learn actionable distributed systems best practices with practical examples, tradeoffs, and anti-patterns to avoid."
tags: ["distributed systems", "backend engineering", "scalability", "resilience", "API design"]
---

# Distributed Systems Best Practices: Building Scalable, Resilient Applications

Directly from the trenches of system design conversations, I know one thing: **distributed systems aren’t just about adding more machines.** They’re about managing complexity—latency, inconsistency, failures, and more—while keeping your system responsive, predictable, and maintainable. Whether you’re dealing with microservices, eventual consistency, or global deployments, the right best practices can mean the difference between a stable service and a chaotic disaster.

The best way to learn? **Do it wrong first, then fix it.** This post covers practical distributed system best practices with real-world examples, tradeoffs, and code snippets to help you build systems that scale without unintended consequences.

---

## The Problem: Why Distributed Systems Are Hard

Distributed systems introduce challenges that monolithic systems don’t:
1. **Latency and Network Overhead**: Even a small network round-trip (RTT) can add milliseconds or more to your response time.
2. **Partial Failures**: A system might be "up" but unresponsive due to node failures, network partitions, or cascading timeouts.
3. **Data Inconsistency**: With eventual consistency models (e.g., distributed databases), you must accept temporary inconsistencies.
4. **Complex Debugging**: Logs are fragmented across services, and tracing requests across nodes is non-trivial.

Consider this example: A user clicks "Buy Now" on an e-commerce site. If your payment service fails after inventory updates but before order confirmation, you’ve just sold a product that no longer exists. Without proper distributed best practices, you’re left with angry customers and lost revenue.

### Real-World Example: The Netflix Chaos Experiments
Netflix famously ran [chaos experiments](https://netflixtechblog.com/) to test resilience. They discovered that **even a 2% failure rate in a critical component** could cascade into system-wide outages if unchecked. Their solution? **Design for failure**—assume components will fail, and build in redundancy, retries, and circuit breakers.

---

## The Solution: Distributed Best Practices

Here are the core patterns and principles to follow:

### 1. **Idempotency: Handle Retries Safely**
When a request fails due to network issues, retries are often necessary—but you *must* ensure idempotency to avoid duplicate side effects.

**Example: Payment Processing**
```python
# Non-idempotent (dangerous!)
def process_payment(payment_id, amount):
    if not payment_exists(payment_id):
        create_payment(payment_id, amount)  # Could create duplicates on retry

# Idempotent (safe)
def process_payment(payment_id, amount):
    if not payment_exists(payment_id):
        # Retry-safe: Use a lock or transaction to block duplicates
        if not create_payment_safely(payment_id, amount):
            raise DuplicatePaymentError
```

**Tradeoff**: Idempotency adds complexity (e.g., locks, transactions) but is essential for resilience.

### 2. **Circuit Breakers: Fail Fast**
Avoid cascading failures by stopping retries after repeated failures. Use libraries like [Hystrix](https://github.com/Netflix/Hystrix) (Java) or [circuit-breaker](https://www.npmjs.com/package/circuit-breaker) (Node.js).

**Example: Microservice Client**
```javascript
const CircuitBreaker = require('opossum');

const paymentService = new CircuitBreaker(
  async (orderId) => await fetch(`/api/payments/${orderId}`),
  {
    timeout: 5000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000
  }
);

// Usage
paymentService.execute('order123').then(/* handle */).catch(/* fallback */);
```

### 3. **Saga Pattern: Distributed Transactions**
For long-running workflows, break them into smaller steps (sagas) with compensating transactions.

**Example: Order Fulfillment Saga**
```sql
-- Step 1: Reserve inventory
BEGIN TRANSACTION;
UPDATE inventory SET quantity = quantity - 1 WHERE product_id = 'prod123';
COMMIT;

-- Step 2: Charge payment (may fail)
BEGIN TRANSACTION;
UPDATE orders SET status = 'paid' WHERE id = 'order456';
COMMIT;

-- If payment fails, compensate by releasing inventory
ROLLBACK;
UPDATE inventory SET quantity = quantity + 1 WHERE product_id = 'prod123';
```

**Tradeoff**: Sagas add operational complexity but are necessary for distributed ACID-like behavior.

### 4. **Event-Driven Architecture: Decouple Components**
Use message queues (e.g., Kafka, RabbitMQ) to decouple producers and consumers. This isolates failures and enables async processing.

**Example: Kafka Topic for Orders**
```bash
# Order Service publishes an event
kafka-console-producer --topic orders --bootstrap-server localhost:9092
> {"event": "order_created", "order_id": "order456"}

# Inventory Service consumes it
kafka-console-consumer --topic orders --from-beginning --bootstrap-server localhost:9092
# Logic to deduct inventory...
```

### 5. **Consistency Models: Choose Wisely**
- **Strong Consistency**: Use for critical data (e.g., `bank_transactions`). Requires distributed locks or 2PC (two-phase commit).
- **Eventual Consistency**: Use for non-critical data (e.g., user preferences). Accept temporary staleness.

**Example: DynamoDB vs. PostgreSQL**
```sql
-- PostgreSQL (strong consistency)
UPDATE accounts SET balance = balance - 100 WHERE id = 'user1';

-- DynamoDB (eventual consistency)
update_item(
  TableName: 'accounts',
  Key: { 'id': 'user1' },
  UpdateExpression: 'SET balance = balance - :val',
  ExpressionAttributeValues: { ':val': -100 },
  ConditionExpression: 'balance >= :val'  # Optional strong consistency
);
```

### 6. **Rate Limiting: Prevent Abuse**
Use tokens or fixed windows to limit requests per client.

**Example: Redis Rate Limiter**
```python
import redis

r = redis.Redis()
def rate_limited(func):
    def wrapper(client_id):
        key = f"rate_limit:{client_id}"
        count = r.incr(key)
        if count == 1:
            r.expire(key, 60)  # Reset after 60 seconds
        if count > 100:  # 100 requests/minute
            raise RateLimitError
        return func(client_id)
    return wrapper

@rate_limited
def process_payment(client_id):
    # Business logic...
```

### 7. **Observability: Monitor and Alert**
- **Metrics**: Track latency, error rates, and throughput (e.g., Prometheus).
- **Logging**: Use structured logs (e.g., JSON) with correlation IDs.
- **Tracing**: Distributed tracing (e.g., Jaeger) to follow requests across services.

**Example: OpenTelemetry Trace**
```go
import "go.opentelemetry.io/otel/trace"

// Start a span for an API call
ctx, span := otel.Tracer("payment-service").Start(ctx, "process_payment")
defer span.End()

// Simulate work
span.SetAttributes(
  attribute.String("order_id", orderID),
  attribute.Int64("amount", 999),
)

// Simulate failure
span.RecordError(errors.New("bank timeout"))
span.AddEvent("payment_failed")
```

---

## Implementation Guide

### Step 1: Start Small, Iterate
- **Begin with a monolith** if your system is small. Split only when bottlenecks appear.
- **Use feature flags** to toggle distributed components (e.g., "Enable distributed inventory checks").

### Step 2: Design for Failure
- **Assume nodes will fail**. Use retries with exponential backoff.
- **Test failure modes** (e.g., kill a node during load testing).

### Step 3: Standardize Interfaces
- **APIs**: Use REST for simplicity, gRPC for high-performance internal calls.
- **Events**: Define schemas upfront (e.g., Avro or Protobuf).

### Step 4: Automate Recovery
- **Self-healing**: Use Kubernetes to auto-restart failed pods.
- **Data reconciliation**: Run periodic checks to sync divergent states.

### Step 5: Document Tradeoffs
- **Example**: "We use DynamoDB for scalability but accept eventual consistency for user profiles."

---

## Common Mistakes to Avoid

1. **Ignoring Latency**: Don’t assume all services will be fast. Add timeouts and fallbacks.
2. **No Idempotency Keys**: Without idempotency, retries can cause chaos.
3. **Over-Retrying**: Retries can amplify errors (e.g., "thundering herd" problem). Use backoff and limits.
4. **Tight Coupling**: Avoid direct dependencies between services. Use queues or events.
5. **Skipping Observability**: Without metrics/logs, you’ll spend hours debugging in production.

---

## Key Takeaways

- **Idempotency is non-negotiable** for distributed systems.
- **Circuit breakers prevent cascading failures**.
- **Sagas replace distributed transactions** when needed.
- **Event-driven decoupling improves resilience**.
- **Consistency models should align with requirements** (strong vs. eventual).
- **Rate limiting protects against abuse**.
- **Observability is your lifeline** in distributed chaos.

---

## Conclusion

Distributed systems are hard, but with the right patterns, you can build scalable, resilient applications. Start with idempotency and circuit breakers, then iteratively add complexity as needed. Remember: **the goal isn’t "perfect" consistency—it’s predictable behavior under failure**.

For further reading:
- ["Designing Data-Intensive Applications" (Martin Kleppmann)](https://dataintensive.net/)
- ["Site Reliability Engineering" (Google SRE Book)](https://sre.google/sre-book/table-of-contents/)
- [Chaos Engineering by Netflix](https://netflixtechblog.com/)

Now go build something that scales!
```