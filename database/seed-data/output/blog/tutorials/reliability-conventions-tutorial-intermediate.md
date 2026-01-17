```markdown
# **Reliability Conventions: Designing Resilient APIs and Databases in Modern Apps**

*How to build systems that handle failures gracefully—without sacrificing developer productivity*

When you ship a feature, the last thing you want is for it to *work 99% of the time*—that’s an insult to your users. You want it to work *consistently*, whether the network hiccups, a database hiccups, or a user hits Refresh *five times in a row*. But how do you design systems that recover from failures while keeping things performant and maintainable?

That’s where **Reliability Conventions** come in. This isn’t a single pattern—it’s a set of *design principles* and *implementation practices* that make your APIs and databases behave predictably under stress. Unlike traditional error-handling techniques (like *try-catch blocks* or *retry policies*), reliability conventions focus on **designing for failure** before it happens.

In this guide, we’ll cover:
- **Why failure handling is harder than it seems** (and how most teams underestimate it)
- **Core reliability conventions** (with code examples in Python, SQL, and API design)
- **Practical implementation strategies** (including idempotency, circuit breakers, and retry logic)
- **Common mistakes** that turn simple failures into cascading disasters
- **Tradeoffs** to help you pick the right approach for your system

---

## **The Problem: When "It Works on My Machine" Isn’t Enough**

Most developers treat failure as an edge case—a bug to be caught in QA or production monitoring. But in reality, **failures are the norm**, not the exception. Here’s why:

1. **Networks are unreliable** – Latency spikes, timeouts, and reconnects happen. Half the time, a `POST` request might fail because the client never got the response.
2. **Databases are fickle** – Transactions deadlock, replication lags, and eventually-consistent stores (like DynamoDB) can return stale data.
3. **Users are impatient** – They’ll refresh, retry, or switch tabs. Your system must handle duplicates, race conditions, and partial updates without breaking.
4. **Infrastructure is temporary** – Servers crash, data centers go offline, and cloud providers throttle requests. Your code needs to assume failure, not just handle it reactively.

Without reliability conventions, failures become:
- **Undiagnosable**: Is a `500` error from the app or the database?
- **Unrecoverable**: A failed payment transaction might get duplicated forever.
- **Unpredictable**: One user gets a success, another gets a `429 Too Many Requests`.
- **Maintenance nightmares**: Patching failures after they happen is expensive.

### **Real-World Example: The Payment Duplicate**
Here’s a classic failure scenario (and why most teams get it wrong):

```python
# Bad: No reliability conventions -> Duplicate payments
@app.post("/checkout")
def checkout():
    payment = create_payment(user_id=123, amount=9.99)  # Returns payment_id=5
    if process_payment(payment_id=5):  # Fails mid-execution
        send_confirmation(payment_id=5)
    else:
        refund_payment(payment_id=5)  # Refund + duplicate payment later
```

What happens if `process_payment()` fails *after `send_confirmation()`*? You’ve just:
1. **Sent a confirmation** (user expects money deducted).
2. **Refunded** (because `process_payment` failed).
3. **Processed the payment again** (if the user retries or the system recovers).

Result? A **duplicate deduction**—and a very angry customer.

---

## **The Solution: Reliability Conventions**

Reliability conventions are **design patterns that make failures predictable and recoverable**. They fall into three categories:

1. **Idempotency**: Ensure operations can be repeated safely.
2. **Retry Logic**: Strategically retry failed requests without causing cascades.
3. **Circuit Breakers**: Stop retrying when a service is clearly broken.
4. **Eventual Consistency Handlers**: Gracefully handle partial failures in distributed systems.
5. **Observability First**: Design systems where failures are visible and debuggable.

Let’s dive into each with code examples.

---

## **Components/Solutions**

### **1. Idempotency: The Safety Net for Retries**
**Problem**: If a request fails and retries, the same operation should have the same result—no duplicates, no partial updates.

**Solution**: Use **idempotency keys** to track already-processed requests.

#### **Example: Idempotent API Endpoint (FastAPI)**
```python
from fastapi import FastAPI, HTTPException
from uuid import uuid4
from typing import Optional

app = FastAPI()

# In-memory "store" of processed idempotency keys (use a real DB in production)
processed_keys = set()

@app.post("/process-payment/{amount}")
async def process_payment(amount: float, idempotency_key: Optional[str] = None):
    if idempotency_key is None:
        idempotency_key = str(uuid4())

    if idempotency_key in processed_keys:
        return {"status": "already_processed"}

    # Simulate a payment processing delay/failure
    try:
        # ... actual payment logic ...
        processed_keys.add(idempotency_key)
        return {"status": "success", "payment_id": 123}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Key Takeaways**:
- Clients generate their own `idempotency_key` (e.g., `uuid()`).
- The server validates it before processing (avoids duplicates).
- Works with retries, timeouts, and client refreshes.

---

### **2. Retry Logic: When to Retry and How**
**Problem**: Retrying blindly causes cascading failures (e.g., retries overload a database).

**Solution**: Implement **exponential backoff** and **jitter** to avoid thundering herds.

#### **Example: Retry with Backoff (Python + Tenacity)**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(DatabaseTimeoutError),
    after=log_retry  # Custom logger
)
def fetch_user(user_id: int):
    return database.query(f"SELECT * FROM users WHERE id = {user_id}")
```

**Best Practices**:
- **Max retries**: Limit retries to avoid long-running operations.
- **Exponential backoff**: Wait longer after each retry (`4s, 8s, 16s`).
- **Jitter**: Add randomness (`+ random(0, 2s)`) to avoid synchronized retries.
- **Circuit breakers**: Stop retrying if a service is clearly down (see next section).

---

### **3. Circuit Breakers: When to Give Up**
**Problem**: Retrying a failed database forever just wastes resources.

**Solution**: Use a **circuit breaker** to short-circuit retries after a threshold of failures.

#### **Example: Circuit Breaker with `pybreaker`**
```python
import pybreaker

circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=3,  # Trip after 3 failures
    reset_timeout=60  # Reset after 60s
)

@circuit_breaker
def call_external_service():
    response = http.get("https://external-api.example.com/data")
    response.raise_for_status()
    return response.json()
```

**When to Use**:
- For external APIs (e.g., payment processors, 3rd-party services).
- When retries are dangerous (e.g., deleting records).

**Tradeoff**: False positives (e.g., asynchronously resolved failures) can still occur.

---

### **4. Eventual Consistency Handlers**
**Problem**: Distributed systems (like Kafka, DynamoDB) return results asynchronously.

**Solution**: Design for **eventual consistency** with:
- **Compensation transactions** (undo operations if a step fails).
- **Sagas** (choreography of long-running workflows).

#### **Example: Saga Pattern (Payment Processing)**
```python
# Step 1: Lock inventory (reserve items)
inventory_lock(id=123, user_id=456)  # Fails if stock is low

# Step 2: Process payment
if payment_successful:
    # Step 3: Release inventory
    inventory_release(id=123, user_id=456)
else:
    # Compensating transaction: Release inventory
    inventory_release(id=123, user_id=456)
```

**Tools**:
- **Saga libraries**: [Camunda](https://camunda.com/), [Temporal](https://temporal.io/).
- **Event sourcing**: Store state changes as events (e.g., `PaymentCreated`, `InventoryReserved`).

---

### **5. Observability First**
**Problem**: Failures happen silently. How do you debug?

**Solution**: Instrument your code with:
- **Structured logging** (e.g., `request_id` for tracing).
- **Metrics** (e.g., `errors_total`, `retry_count`).
- **Distributed tracing** (e.g., OpenTelemetry).

#### **Example: Structured Logging (Python)**
```python
import logging
from uuid import uuid4

logger = logging.getLogger("reliability")
logger.setLevel(logging.INFO)

def process_order(order_id: str):
    request_id = str(uuid4())
    try:
        # ... business logic ...
        logger.info(
            {"request_id": request_id, "event": "order_processed", "status": "success"}
        )
    except Exception as e:
        logger.error(
            {
                "request_id": request_id,
                "event": "order_failed",
                "error": str(e),
                "order_id": order_id
            }
        )
        raise
```

**Tools**:
- **OpenTelemetry**: For distributed tracing.
- **Prometheus + Grafana**: For metrics.
- **Sentry/LogRocket**: For error tracking.

---

## **Implementation Guide: How to Adopt Reliability Conventions**

### **Step 1: Start with Idempotency**
- **For APIs**: Require `idempotency-key` headers for state-changing operations.
- **For databases**: Use `INSERT ... ON CONFLICT DO NOTHING` (PostgreSQL) or `UPSERT` (SQL Server).

```sql
-- PostgreSQL: Idempotent insert
INSERT INTO payments (user_id, amount, payment_id)
VALUES (123, 9.99, 5)
ON CONFLICT (payment_id) DO NOTHING;
```

### **Step 2: Add Retry Logic**
- Use libraries like `tenacity` (Python), `@retry` (JavaScript), or `pollyjs` (Node.js).
- Configure:
  - Max retries (e.g., 3).
  - Backoff (e.g., exponential with jitter).
  - Exceptions to retry (e.g., `DatabaseTimeoutError`, not `404`).

### **Step 3: Implement Circuit Breakers**
- For external APIs, use `pybreaker` (Python), `Resilience4j` (Java), or `Polly` (.NET).
- Set `fail_max` and `reset_timeout` based on SLA (e.g., `fail_max=5`, `reset_timeout=1m`).

### **Step 4: Design for Eventual Consistency**
- Use **sagas** for long-running workflows.
- Implement **compensating transactions** (e.g., rollback inventory if payment fails).
- For databases, consider **eventual consistency** (e.g., DynamoDB’s `ConditionalWrite`).

### **Step 5: Instrument for Observability**
- Add `request_id` to all logs and traces.
- Expose metrics for retries, errors, and latency.
- Use APM tools (e.g., Datadog, New Relic) to correlate failures.

---

## **Common Mistakes to Avoid**

| **Mistake**                          | **Why It’s Bad**                                                                 | **Better Approach**                          |
|---------------------------------------|----------------------------------------------------------------------------------|-----------------------------------------------|
| **No idempotency**                    | Duplicate payments, lost updates.                                               | Always use idempotency keys.                  |
| **Unbounded retries**                 | Retries cause cascading failures (e.g., DB overload).                           | Limit retries (e.g., 3) + backoff.           |
| **No circuit breakers**               | Retrying forever when a service is down (e.g., payment gateway).               | Use `pybreaker` or `Resilience4j`.           |
| **Ignoring eventual consistency**      | Users see "inconsistent" data (e.g., "Payment processed" but no funds deducted). | Design for eventual consistency.              |
| **No observability**                  | Failures go undetected until users complain.                                  | Log structured data + trace requests.        |
| **Hardcoding retries in business logic** | Mixes reliability concerns with domain logic.                                | Use libraries (e.g., `tenacity`).            |
| **Over-relying on transactions**      | Long-running transactions block resources.                                     | Use short-lived transactions + retries.      |

---

## **Key Takeaways**

✅ **Idempotency is non-negotiable** – Every state-changing operation should be repeatable.
✅ **Retries should be strategic** – Exponential backoff + jitter > blind retries.
✅ **Circuit breakers save resources** – Don’t retry forever when a service is down.
✅ **Eventual consistency is a feature** – Design for it, don’t fight it.
✅ **Observability is your safety net** – Without logs/metrics, failures are invisible.
✅ **Tradeoffs exist** –
   - Idempotency adds complexity (but prevents duplicates).
   - Eventual consistency means "eventually correct" (not "immediately correct").
   - Retries increase resilience but can hide real issues.

---

## **Conclusion: Build for Failure, Not Just Functionality**

Reliability conventions aren’t about writing "bulletproof" code—they’re about **designing systems that degrade gracefully** when things go wrong. The best teams don’t treat failures as exceptions; they **build them into their architecture** from day one.

**Start small**:
1. Add idempotency to your next API.
2. Instrument one critical path with metrics.
3. Implement a circuit breaker for an external dependency.

**Scale smartly**:
- Use sagas for complex workflows.
- Optimize retries with backoff and jitter.
- Observe everything—failures are just data.

Remember: **A system that works 99% of the time is unreliable**. Aim for **consistently predictable** behavior, even in the face of chaos.

Now go build something that doesn’t break under pressure.

---
**Further Reading**:
- [Martin Fowler on Idempotency](https://martinfowler.com/articles/idempotency.html)
- [Resilience Patterns (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/)
- [Event Sourcing Patterns (Greg Young)](https://eventstore.com/blog/post/2013/11/08/event-sourcing-patterns.aspx)
```