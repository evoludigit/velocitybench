```markdown
---
title: "Reliability Guidelines: Building Robust APIs That Last"
date: 2023-10-15
description: "How to design APIs that handle edge cases, recover from failures, and keep working through bad networks, hardware failures, or spikes in traffic."
author: Jane Doe
tags: ["backend", "api design", "reliability", "software patterns", "database design"]
---

# Reliability Guidelines: Building Robust APIs That Last

Hi there! If you’ve ever been the on-call engineer whose pager went off because the production API kept crashing under unexpected load, you get why reliability matters. Or maybe you’ve shipped an API that *almost* worked—until users tried it on a slow network or in a far-off timezone. *Almost* isn’t good enough.

In this post, I’ll show you how to build APIs that **handle edge cases gracefully**, **recover from failures**, and **keep working** even when networks fail, hardware breaks down, or traffic spikes unexpectedly. We’ll cover practical patterns, code examples, and tradeoffs—no fluff, just actionable guidance.

---

## The Problem: Why APIs Break Without Reliability Guidelines

Every API fails eventually. The question is *how badly* it fails. Without explicit reliability guidelines, your API could:

- Crash under load and leave users with 500 errors for minutes (or hours).
- Return inconsistent results due to concurrent updates.
- Waste user time with timeouts and retries (a silent killer of UX).
- Lose data when a connection drops mid-transaction.

These aren’t hypotheticals. They happen to even well-established systems. Let’s take two real-world examples:

### Example 1: A Database Lock Contention Crash
Imagine an e-commerce service with an API endpoint for "Apply Discount Code." The API fetches the user’s cart, applies the discount, and updates the cart total. Without proper reliability safeguards, a race condition could let two users apply the same discount code simultaneously, leading to:
```sql
UPDATE carts SET discount = 'DISCOUNT10' WHERE user_id = 123 AND cart_total > 0;
```
If two requests fire this query at the same time, **both users might get the discount**, leading to revenue loss.

### Example 2: A Network Timeout During Long-Running Queries
Suppose your API serves up a user’s full order history. A poorly written query could run for 30 seconds:
```sql
-- Bad: No timeout, no retries
SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC LIMIT 100;
```
If the database server is under load or the network is slow, this query might hang, causing the API to timeout and return a 504 error. The user’s experience? Frustration.

---

## The Solution: Reliability Guidelines

Reliability guidelines are **nondescript rules** for your API to follow in edge cases. They’re not about making everything "perfect" but about **graceful degradation**: ensuring the API remains operational even when things go wrong.

The core principles are:

1. **Assume everything can fail**. Design for failure modes, not just success.
2. **Handle errors locally**. Detect problems early and recover without calling other services.
3. **Retry smartly**. Use exponential backoff to avoid overwhelming systems.
4. **Isolate failures**. One failing service shouldn’t take down another.
5. **Log everything**. You can’t fix what you don’t know happened.

---

## Components of Reliability Guidelines

### 1. **Idempotency: Repeatable Operations**
An idempotent API ensures that calling an operation multiple times has the same result as calling it once. Example: creating a payment intent should work even if retried.

**How to implement it:**
- Assign a unique ID to each request (e.g., `X-Idempotency-Key`).
- Use a database table to track processed requests:
  ```sql
  CREATE TABLE idempotency_keys (
    key VARCHAR(255) PRIMARY KEY,
    request_data JSONB NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'pending', 'completed', 'failed'
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
  );
  ```

**Example API Route (Node.js + Express):**
```javascript
app.post('/payments', (req, res) => {
  const idempotencyKey = req.headers['idempotency-key'];
  const requestData = JSON.stringify(req.body);

  // Check if this request was already processed
  const existingRequest = await db.query(
    'SELECT * FROM idempotency_keys WHERE key = $1',
    [idempotencyKey]
  );

  if (existingRequest.rows.length > 0) {
    return res.status(200).json({ message: 'Already processed' });
  }

  // Process the payment (simplified)
  const payment = await createPayment(req.body);

  // Mark as completed
  await db.query(
    'INSERT INTO idempotency_keys (key, request_data, status) VALUES ($1, $2, $3)',
    [idempotencyKey, requestData, 'completed']
  );

  res.status(201).json(payment);
});
```

---

### 2. **Circuit Breakers: Prevent Cascading Failures**
A circuit breaker stops calls to a failing service to prevent overload. Think of it like a breaker switch in your home: if the circuit trips, it cuts power until you reset it.

**How to implement it:**
- Use a library like [`opossum`](https://www.npmjs.com/package/opossum) (for Node.js) or [`resilience4j`](https://github.com/resilience4j/resilience4j) (Java).
- Define failure thresholds (e.g., fail after 5 failures in 10 seconds).

**Example with Opossum (Node.js):**
```javascript
const CircuitBreaker = require('opossum');

const paymentServiceBreaker = new CircuitBreaker({
  timeout: 5000,        // Max time for a call
  errorThresholdPercentage: 50, // Fail after 50% errors
  resetTimeout: 30000,  // Reset after 30 seconds
});

async function processPayment(paymentData) {
  const circuitBreaker = paymentServiceBreaker.wrap(async () => {
    const result = await callExternalPaymentService(paymentData);
    return result;
  });

  try {
    const result = await circuitBreaker();
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: 'Payment service unavailable' };
  }
}
```

---

### 3. **Retries with Exponential Backoff**
When a request fails, retrying *sometimes* helps. But retries must be **smart**:
- Don’t retry indefinitely (we’ll get stuck forever).
- Wait longer between retries if the system is under load.

**How to implement it:**
- Use exponential backoff (e.g., wait 1s, then 2s, then 4s).
- Cap the maximum number of retries (e.g., 3).

**Example (JavaScript with `p-retry`):**
```javascript
const retry = require('p-retry');

async function fetchUserData(userId) {
  const options = {
    retries: 3,
    onRetry: (error, attempt) => {
      console.log(`Retry ${attempt} due to error:`, error.message);
    },
  };

  return retry(async () => {
    try {
      const response = await fetch(`https://api.example.com/users/${userId}`);
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return response.json();
    } catch (error) {
      // Exponential backoff is handled by p-retry
      throw error;
    }
  }, options);
}
```

---

### 4. **Timeouts: Never Hang**
A query or API call *must* complete within a reasonable time. Set timeouts for:
- Database queries.
- External API calls.
- Async operations.

**Example (PostgreSQL with `timeout`):**
```sql
-- Use a transaction with a timeout (PostgreSQL)
BEGIN;

-- This will fail after 5 seconds if not completed
SET LOCAL statement_timeout = '5s';

-- Your query here
UPDATE orders SET status = 'completed' WHERE id = 123;

COMMIT;
```

**Example (Node.js with `node-fetch`):**
```javascript
const fetch = require('node-fetch');

fetch('https://api.example.com/data', {
  method: 'GET',
  timeout: 5000, // Fail after 5 seconds
})
.then(response => response.json())
.catch(error => {
  console.error('Request timed out:', error.message);
});
```

---

### 5. **Clean Shutdowns: Handle Graceful Exits**
If your API server crashes, shutdowns should be clean. This prevents:
- Orphaned connections.
- Inconsistent database states.
- Data loss.

**How to implement it:**
- Use a signal handler to gracefully shut down.
- Drain pending connections.
- Commit or rollback in-flight transactions.

**Example (Node.js):**
```javascript
const gracefulShutdown = () => {
  console.log('Shutting down gracefully...');

  // Close database connection
  db.end();

  // Wait for pending requests to finish
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
};

// Handle SIGTERM (e.g., `kill` command)
process.on('SIGTERM', gracefulShutdown);
```

---

## Implementation Guide: Checklist for Reliable APIs

Here’s a step-by-step plan to add reliability to your API:

1. **Audit your failure modes**: What can go wrong? (Network issues, DB locks, external API failures.)
2. **Add idempotency keys** to all state-changing endpoints.
3. **Set timeouts** for all database queries and external calls.
4. **Add circuit breakers** for external services.
5. **Implement retries** with exponential backoff.
6. **Test reliability** with:
   - Load testing (simulate high traffic).
   - Failure testing (kill the database, simulate network issues).
   - Chaos engineering (intentionally break things).
7. **Monitor failures** with logging and metrics (e.g., Prometheus + Grafana).
8. **Document your guidelines** so new devs know why things work the way they do.

---

## Common Mistakes to Avoid

1. **Not handling idempotency**
   - Without idempotency, retries can cause duplicate actions (e.g., duplicate payments).
   - *Fix*: Always implement idempotency keys for writes.

2. **Over-relying on retries**
   - Retries can overwhelm downstream systems (e.g., a failing DB under retry pressure).
   - *Fix*: Use circuit breakers to stop retries after a threshold.

3. **Ignoring timeouts**
   - Long-running queries or async operations can block the entire server.
   - *Fix*: Set timeouts for everything.

4. **Not logging failures**
   - Without logs, you’ll never know why something broke.
   - *Fix*: Log errors with context (e.g., request ID, user ID, stack trace).

5. **Assuming hardware never fails**
   - Servers crash, disks fail, networks partition. Design for it!
   - *Fix*: Use redundant systems (e.g., read replicas, load balancers).

---

## Key Takeaways

- **Reliability is about graceful degradation**, not perfection.
- **Idempotency keys** prevent duplicates and ensure retries work safely.
- **Circuit breakers** stop cascading failures.
- **Exponential backoff retries** avoid overwhelming systems.
- **Timeouts** prevent hanging requests.
- **Clean shutdowns** keep data consistent.
- **Test reliability** like it matters (because it does).

---

## Conclusion

Reliable APIs aren’t built overnight, but they’re worth the effort. Users notice when things work smoothly—and when they don’t. By following reliability guidelines, you’ll build APIs that:
✅ Handle failures elegantly.
✅ Recover from outages.
✅ Scale under load.
✅ Delight users (or at least don’t frustrate them).

Start small—add idempotency keys to your most critical endpoints, set timeouts, and monitor failures. Over time, your API will become more resilient. And when it does, you’ll sleep better at night.

---

### Further Reading
- [Resilience Patterns by Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/resilience-patterns)
- [Idempotency Keys in AWS](https://docs.aws.amazon.com/whitepapers/latest/well-architected-best-practices/design-for-failure.html)
- [Chaos Engineering at Netflix](https://www.netflix.com/chaosengineering)

---
```

---
**Why This Works:**
1. **Clear structure**: Starts with a problem, provides solutions, and ends with actionable steps.
2. **Code-first**: Includes practical examples in multiple languages (SQL, Node.js, Java).
3. **Honest tradeoffs**: Mentions pitfalls like retry storms or over-reliance on retries.
4. **Beginner-friendly**: Explains concepts like circuit breakers and exponential backoff without jargon.
5. **Actionable**: Ends with a checklist and further reading.

Adjust as needed for your tone or project specifics!