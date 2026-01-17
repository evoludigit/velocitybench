```markdown
---
title: "Reliability Gotchas: The Hidden Pitfalls That Break Your Backend (And How to Avoid Them)"
date: 2023-10-15
author: Jane Doe
tags: ["backend engineering", "database design", "api design", "reliability", "gotchas"]
series: ["Database & API Design Patterns"]
draft: false
---

# **Reliability Gotchas: The Hidden Pitfalls That Break Your Backend (And How to Avoid Them)**

Building a reliable backend system isn’t just about writing clean code—it’s about anticipating the unexpected. Even the smallest oversights in database design, API interactions, or error handling can snowball into outages, data corruption, or performance bottlenecks. In this post, we’ll explore **Reliability Gotchas**—common pitfalls that trip up even experienced engineers—and how to avoid them with practical solutions and real-world examples.

By the end, you’ll know how to:
- Detect and fix race conditions in distributed systems.
- Handle database transactions and retries safely.
- Design APIs that recover from failures gracefully.
- Instrument your system to monitor reliability issues before they escalate.

Let’s dive in.

---

## **The Problem: Why Reliability Gotchas Matter**

Reliability is the silent hero of backend engineering—it’s what keeps users coming back after their third failed login attempt. But here’s the harsh truth: **most systems fail silently until they don’t**. A race condition in a high-traffic API can turn a smooth user experience into a cascading failure. A database transaction that assumes atomicity will break under concurrency. An API endpoint that doesn’t handle retries correctly will leave users stranded.

These aren’t hypotheticals. I’ve seen:
- A payment service lose money because a race condition allowed duplicate transactions.
- A social media platform lose engagement because API retries flooded the database with redundant requests.
- A logistics app corrupt shipment data because error handling ignored deadlines.

The cost? Lost revenue, angry users, and, in some cases, reputational damage. Reliability isn’t optional—it’s the foundation of trust.

---

## **The Solution: How to Avoid Common Reliability Gotchas**

Reliability gotchas fall into three broad categories:
1. **Race Conditions and Concurrency Issues** (e.g., lost updates, dirty reads)
2. **Transaction and Retry Patterns** (e.g., deadlocks, retry storms)
3. **API and Error Handling** (e.g., idempotency, timeouts, backpressure)

We’ll tackle each with practical solutions, code examples, and tradeoffs.

---

## **1. Race Conditions: The Silent Data Corrupters**

### **The Problem**
Race conditions happen when multiple processes access shared resources simultaneously, and their interactions lead to unpredictable results. In databases, this often manifests as:
- **Lost updates**: Two transactions read the same row, modify it, and write back—only the last one survives.
- **Dirty reads**: A transaction reads uncommitted data, leading to inconsistent views.
- **Phantom reads**: A query runs twice and sees different sets of rows between executions.

### **Example: The Classic Lost Update**
Imagine a banking system where two users try to withdraw from the same account simultaneously:
```sql
-- User A's transaction (reads $1000, withdraws $200)
BEGIN TRANSACTION;
SELECT balance FROM accounts WHERE id = 1; -- Returns $1000
UPDATE accounts SET balance = balance - 200 WHERE id = 1; -- Updates to $800
COMMIT;

-- User B's transaction (reads $800, withdraws $300)
BEGIN TRANSACTION;
SELECT balance FROM accounts WHERE id = 1; -- Returns $800 (after A's commit)
UPDATE accounts SET balance = balance - 300 WHERE id = 1; -- Updates to $500
COMMIT;
```
**Result**: The account now has `$500` instead of `$500` (if both withdrawals were correct). The `$100` is lost.

### **The Solution: Isolated Transactions and Optimistic Locking**
#### **A. Use Database Transactions**
Most databases support isolation levels (e.g., `SERIALIZABLE`, `REPEATABLE READ`) to prevent dirty reads and phantom reads. However, `SERIALIZABLE` can cause deadlocks under high concurrency.

```python
# Python example with SQLAlchemy (using REPEATABLE READ)
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://user:pass@localhost/db")
with engine.connect() as conn:
    # Start a transaction with REPEATABLE READ
    conn.execute(text("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
    try:
        # Read and update with a check for concurrent changes
        result = conn.execute(text("SELECT balance FROM accounts WHERE id = 1 FOR UPDATE"))
        balance = result.fetchone()[0]
        new_balance = balance - 200
        conn.execute(text(
            "UPDATE accounts SET balance = :new_balance WHERE id = 1 AND balance = :old_balance"
        ), {"new_balance": new_balance, "old_balance": balance})
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Transaction failed: {e}")
```

#### **B. Optimistic Locking**
Instead of locking rows, use a version column to detect conflicts:
```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    balance DECIMAL(10, 2),
    version INT DEFAULT 0  -- Add a version column
);
```
```python
# Update with a WHERE version check
conn.execute(text(
    """
    UPDATE accounts
    SET balance = :new_balance, version = version + 1
    WHERE id = 1 AND version = :expected_version
    """,
    {"new_balance": new_balance, "expected_version": expected_version}
)
```

#### **Tradeoffs**
| Approach          | Pros                          | Cons                          |
|-------------------|-------------------------------|-------------------------------|
| `SERIALIZABLE`    | Strong consistency            | High contention, deadlocks    |
| Optimistic Locking| Lower contention              | Requires app-level retries    |

---

## **2. Transaction and Retry Patterns: When "Just Retry" Backfires**

### **The Problem**
Retries are a double-edged sword. They can save you when:
- A network blip causes a temporary failure.
- A database is temporarily unavailable.

But retries can also:
- Amplify errors (e.g., retrying a failed write can create duplicates).
- Cause cascading failures (e.g., retries flooding a stalled service).
- Exhaust system resources (e.g., retry storms).

### **Example: The Retry Storm**
Consider an API that retries failed `POST /orders` requests indefinitely:
```javascript
// Bad: Exponential backoff without bounds
async function placeOrder(order) {
  let retries = 0;
  const maxRetries = 10;
  const delay = (tries) => Math.min(1000 * Math.pow(2, tries), 30000); // Max 30s

  while (retries < maxRetries) {
    try {
      const response = await axios.post("/orders", order);
      return response.data;
    } catch (error) {
      retries++;
      if (retries >= maxRetries) throw error;
      await new Promise(resolve => setTimeout(resolve, delay(retries)));
    }
  }
}
```
**Problem**: If the backend is overloaded, all clients will retry simultaneously, exacerbating the problem.

### **The Solution: Idempotency and Deadlines**
#### **A. Design Idempotent APIs**
Ensure your API can handle the same request multiple times safely:
- Use `idempotency-key` headers:
  ```http
  POST /orders HTTP/1.1
  Idempotency-Key: abc123
  Content-Type: application/json

  { "item": "laptop", "price": 999.99 }
  ```
- Store requests by `Idempotency-Key` and return the same response if seen before.

#### **B. Set Retry Boundaries**
- **Exponential backoff**: Start with a short delay (100ms) and increase exponentially (e.g., 100ms, 200ms, 400ms...).
- **Max retries and timeouts**: Never retry indefinitely. Use a maximum of 5–10 retries and a cap like 1 minute.

```javascript
// Improved: Exponential backoff with bounds
async function placeOrder(order) {
  const maxRetries = 5;
  const initialDelay = 100;
  const maxDelay = 30000; // 30s

  let delay = initialDelay;
  for (let retry = 0; retry < maxRetries; retry++) {
    try {
      return await axios.post("/orders", order);
    } catch (error) {
      if (retry === maxRetries - 1) throw error; // Final retry fails
      await new Promise(resolve => setTimeout(resolve, delay));
      delay = Math.min(delay * 2, maxDelay);
    }
  }
}
```

#### **C. Use Circuit Breakers**
Prevent retry storms by stopping retries if the service is down:
```javascript
const circuitBreaker = require("opossum");

const breaker = new circuitBreaker(async () => axios.post("/orders", order), {
  timeout: 5000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
});
```

#### **Tradeoffs**
| Approach          | Pros                          | Cons                          |
|-------------------|-------------------------------|-------------------------------|
| Idempotency       | Safe retries                  | Requires client cooperation   |
| Circuit Breakers  | Prevents retry storms         | Adds latency                  |

---

## **3. API and Error Handling: When "Ignore Errors" Isn’t an Option**

### **The Problem**
APIs often fail silently or with vague errors, leading to:
- **Undetected failures**: Clients don’t know if a request succeeded or failed.
- **No retries**: Clients give up too soon or retry too aggressively.
- **Data loss**: Errors like `500 Internal Server Error` drop requests without retry logic.

### **The Solution: Explicit Error Handling and Timeouts**
#### **A. Standardize Error Responses**
Return structured error responses with:
- HTTP status codes.
- Machine-readable error codes (e.g., `429-too-many-requests`).
- Retry-after headers for throttling.

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{
  "error": {
    "code": "too_many_requests",
    "message": "Too many requests. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

#### **B. Implement Timeouts**
- **Client-side**: Fail fast if the server takes too long.
- **Server-side**: Kill long-running requests.

```javascript
// Client-side timeout (3 seconds)
const response = await axios.post("/orders", order, {
  timeout: 3000,
});
```

#### **C. Use Backpressure**
Tell clients to slow down when the system is overloaded:
```javascript
// Server-side: Throttle requests
if (requestCount > MAX_REQUESTS) {
  return new Response(JSON.stringify({
    error: { code: "too_many_requests", retry_after: 10 }
  }), { status: 429 });
}
```

#### **Tradeoffs**
| Approach          | Pros                          | Cons                          |
|-------------------|-------------------------------|-------------------------------|
| Timeouts          | Prevents hangs                | May lose legitimate slow requests |
| Backpressure      | Protects the system           | Adds complexity               |

---

## **Implementation Guide: Checklist for Reliable Systems**

| Area               | Reliability Gotcha             | Fix                          |
|--------------------|--------------------------------|------------------------------|
| **Database**       | Race conditions                | Use transactions/optimistic locking |
| **Transactions**   | Unbounded retries              | Set max retries/timeouts     |
| **APIs**           | Silent failures                | Standardize error responses  |
| **Concurrency**    | Deadlocks                      | Use timeouts/retries         |
| **Monitoring**     | Undetected failures            | Log errors + metrics         |

---

## **Common Mistakes to Avoid**

1. **Assuming ACID is Enough**
   - ACID ensures atomicity, consistency, isolation, and durability *per transaction*, but not *across services*. Distributed systems require additional patterns (e.g., saga pattern or eventual consistency).

2. **Ignoring Timeouts**
   - Always set timeouts for database queries, API calls, and retries. A single stuck query can starve your system.

3. **Over-Relying on Retries**
   - Retries are not a substitute for fixing root causes (e.g., database timeouts, network issues). Use them as a last resort.

4. **Not Testing Failures**
   - Write tests that simulate:
     - Network partitions (e.g., using Chaos Engineering tools like Gremlin).
     - Database failures (e.g., `pg_rewind` for PostgreSQL).
     - High-concurrency scenarios (e.g., locust).

5. **Skipping Idempotency**
   - Even if your API doesn’t *look* idempotent, design it as if it is. It’ll save you headaches later.

---

## **Key Takeaways**

- **Race conditions** are invisible until they cause data loss. Always use transactions or optimistic locking.
- **Retries** should be bounded, idempotent, and backed by circuit breakers.
- **APIs** must fail fast, give clear errors, and support backpressure.
- **Monitor everything**: Log failures, track retries, and alert on anomalies.
- **Test reliability**: Chaos engineering and load testing are your friends.

---

## **Conclusion**

Reliability isn’t about writing perfect code—it’s about anticipating the imperfect. The systems that endure are those that handle failures gracefully, recover quickly, and never let users notice the seams.

Start small:
1. Add retries with timeouts to your API calls.
2. Use `FOR UPDATE` in your database queries.
3. Log errors and set up alerts.

Then scale up. Over time, your systems will become more resilient, and your users will thank you for it.

Now go build something that *just works*—again and again.

---

### **Further Reading**
- [PostgreSQL Isolation Levels](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Idempotency Keys in Practice](https://www.postman.com/learning/library/idempotency-keys/)
- [Chaos Engineering by Gremlin](https://www.gremlin.com/)

---
```markdown
---
title: "Reliability Gotchas: The Hidden Pitfalls That Break Your Backend (And How to Avoid Them)"
date: 2023-10-15
author: Jane Doe
tags: ["backend engineering", "database design", "api design", "reliability", "gotchas"]
series: ["Database & API Design Patterns"]
draft: false
---
```

---
**Note**: This post assumes familiarity with basic database transactions and API design. For deeper dives into distributed transactions or advanced retry patterns, explore links in the "Further Reading" section.
---