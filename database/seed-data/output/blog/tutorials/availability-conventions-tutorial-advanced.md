```markdown
---
title: "Availability Conventions: Designing APIs for Graceful Degradation"
date: 2024-04-20
author: Jane Doe
description: "Learn how to design resilient APIs with Availability Conventions to handle failures gracefully, ensuring robustness in real-world systems. Code examples included."
---

# **Availability Conventions: Designing APIs for Graceful Degradation**

APIs power modern systems, but they’re not immune to failure. Whether it’s a database outage, network latency, or a cascading failure in a microservice, how your API handles availability can mean the difference between a seamless user experience and a frustrating crash. This is where **Availability Conventions** come in—a deliberate design pattern for making systems resilient to partial failures.

In this guide, we’ll explore real-world challenges of APIs without proper availability strategies, then dive into **Availability Conventions**—a pattern that prioritizes graceful degradation, predictable behavior under stress, and clear communication of service limitations. You’ll see practical implementations in code, learn how to apply this pattern in your own systems, and discover common pitfalls to avoid.

---

## **The Problem: Why APIs Fail Without Availability Conventions**

APIs are the nervous system of modern applications, connecting frontends, microservices, and third-party integrations. However, real-world systems rarely run in perfect conditions. Here’s what happens when APIs lack **availability conventions**:

### **1. Unpredictable Behavior Under Load**
Without clear availability rules, APIs may:
- Crash or return errors when overloaded (e.g., `503 Service Unavailable`).
- Block requests indefinitely (e.g., due to unhandled connection pools).
- Return inconsistent data (e.g., partial results from a failed query).

**Example:** An e-commerce API that fails entirely during a Black Friday sale instead of gracefully throttling requests.

### **2. Cascading Failures**
When one service fails, dependencies may propagate errors:
- A payment service timeout causes an order service to reject all requests.
- A caching layer failure forces the API to hit slow databases for every request.

**Example:** A social media app where a bug in the notification service causes login failures due to shared database locks.

### **3. Poor User Experience**
API failures often manifest as:
- Broken UI elements (e.g., "Something went wrong" without context).
- Slow responses due to retries or exponential backoff misconfigurations.
- Loss of work (e.g., unsaved form data when an API times out).

**Example:** A banking app that freezes during peak hours instead of showing a friendly "Try again later" message.

### **4. Debugging Nightmares**
Without explicit availability rules, failures are harder to diagnose:
- Logs are cluttered with `500 Internal Server Error` messages.
- Team members argue over whether a bug was caused by the API or a dependent service.

**Example:** A logistics API where a `NULL` response could mean:
- The requested shipment was never found, or
- The database server was temporarily unreachable.

---

## **The Solution: Availability Conventions**

**Availability Conventions** are a set of design principles and patterns that ensure APIs:
1. **Degrade gracefully** (e.g., return partial data instead of crashing).
2. **Communicate limitations** (e.g., `429 Too Many Requests` with retry headers).
3. **Handle failures predictably** (e.g., timeouts, circuit breakers, retries with backoff).

This pattern is inspired by:
- **HTTP standards** (e.g., status codes, `Retry-After` headers).
- **Resilience patterns** (e.g., bulkheads, circuit breakers).
- **Database design** (e.g., read replicas for scalability).

Unlike traditional error handling (which often treats failures as catastrophic), **Availability Conventions** treat them as expected states—designing for them at every layer.

---

## **Components of Availability Conventions**

A robust API design incorporates these key components:

| Component               | Purpose                                                                 | Example (API Response)                     |
|-------------------------|-------------------------------------------------------------------------|--------------------------------------------|
| **Status Codes**        | Clearly communicate availability state.                                  | `429 Too Many Requests`                     |
| **Retry Headers**       | Guide clients on when to retry.                                         | `Retry-After: 30`                          |
| **Graceful Fallbacks**  | Serve partial data instead of failing.                                   | `{ "data": [], "partial": true }`         |
| **Circuit Breakers**    | Stop cascading failures in dependent services.                          | `503 Service Unavailable`                   |
| **Rate Limiting**       | Prevent overload and ensure fair usage.                                  | `X-RateLimit-Limit: 100`                   |
| **Health Checks**       | Help clients decide whether to retry.                                    | `/health` → `{ "status": "degraded" }`     |
| **Versioning**          | Isolate breaking changes and load.                                        | `/v2/orders`                               |

---

## **Code Examples: Implementing Availability Conventions**

Let’s walk through a practical example using **Node.js + Express** and **PostgreSQL**, focusing on:
1. Rate limiting.
2. Graceful degradation with partial data.
3. Health checks.

---

### **1. Rate Limiting (Preventing Overload)**
Clients should know when to throttle requests. Use **Express Rate Limit** and return `429` with `Retry-After`.

```javascript
// server.js
const express = require('express');
const rateLimit = require('express-rate-limit');

const app = express();

// Rate limit to 100 requests per 15 minutes
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  message: {
    error: 'Too many requests',
    retryAfter: 30, // Retry after 30 seconds
  },
});

app.use(limiter);

// Example API endpoint
app.get('/api/orders', (req, res) => {
  // Simulate a slow DB query
  setTimeout(() => {
    res.json({ orders: [] });
  }, 1000);
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

**Key Takeaways:**
- Clients receive `429 Too Many Requests` with `Retry-After`.
- No server crashes from DDoS or misbehaving clients.

---

### **2. Graceful Degradation (Partial Data)**
Instead of failing on database errors, return partial results with a `partial: true` flag.

```sql
-- PostgreSQL query with fallback
SELECT
  o.id,
  o.customer_id,
  c.name AS customer_name,
  o.status
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id
WHERE o.created_at > NOW() - INTERVAL '7 days'
ORDER BY o.created_at DESC
LIMIT 10;
```

```javascript
// Express route with error handling
app.get('/api/orders', async (req, res) => {
  try {
    const { rows } = await db.query(`
      SELECT
        o.id,
        o.customer_id,
        c.name AS customer_name,
        o.status
      FROM orders o
      LEFT JOIN customers c ON o.customer_id = c.id
      WHERE o.created_at > NOW() - INTERVAL '7 days'
      ORDER BY o.created_at DESC
      LIMIT 10
    `);

    res.json({ orders: rows, partial: false });
  } catch (err) {
    // Log the error but serve partial data
    console.error('DB query failed:', err);
    res.json({
      orders: [],
      partial: true,
      message: 'Some orders may be missing due to a temporary issue. Refresh later.',
    });
  }
});
```

**Key Takeaways:**
- The API never crashes; it just warns users.
- Clients can handle `partial: true` gracefully (e.g., show a "Refresh" button).

---

### **3. Health Checks (Client Decision Making)**
Expose a `/health` endpoint that clients can poll to decide whether to retry.

```javascript
app.get('/health', (req, res) => {
  const healthStatus = {
    status: 'normal', // normal, degraded, or unavailable
    services: {
      database: 'up',
      cache: 'up',
      payments: 'degraded', // Simulate a degraded service
    },
  };

  res.json(healthStatus);
});
```

**Usage:**
Clients can poll `/health` and retry non-critical requests if `status: 'degraded'`.

```javascript
// Client-side retry logic (e.g., JavaScript)
async function fetchWithRetry(url, maxRetries = 3) {
  let retries = 0;
  while (retries < maxRetries) {
    try {
      const response = await fetch(url);
      if (response.ok) return await response.json();
      // Only retry on "degraded" or "unavailable" statuses
      const health = await fetch('/health').then(r => r.json());
      if (health.status === 'normal') break;
      retries++;
      await new Promise(res => setTimeout(res, 1000 * retries)); // Exponential backoff
    } catch (err) {
      retries++;
      await new Promise(res => setTimeout(res, 1000 * retries));
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Key Takeaways:**
- Clients avoid blind retries; they check `/health` first.
- Non-critical operations (e.g., analytics) can defer during degraded states.

---

## **Implementation Guide: Steps to Adopt Availability Conventions**

### **1. Define Availability Policies**
Document how your API behaves under different failure modes:
- **Normal:** `200 OK` with full data.
- **Degraded:** `200 OK` with partial data or `206 Partial Content`.
- **Unavailable:** `503 Service Unavailable` with `Retry-After`.

**Example Policy:**
| Scenario               | Response Code | Behavior                          |
|------------------------|----------------|-----------------------------------|
| Database timeout       | `200 OK`       | Return empty array with `partial: true` |
| Rate limit exceeded    | `429`          | Include `Retry-After` header      |
| Critical service down  | `503`          | Return `Retry-After`              |

---

### **2. Instrument Your API**
- **Logging:** Log failures with context (e.g., `db:timeout`, `rate_limit_exceeded`).
- **Metrics:** Track latency, error rates, and retry patterns (e.g., with Prometheus).
- **Tracing:** Use OpenTelemetry to trace requests across services.

```javascript
// Example with Winston logging
const winston = require('winston');
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()],
});

app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info({
      level: 'request',
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration,
    });
  });
  next();
});
```

---

### **3. Design for Partial Failures**
- **Database Queries:** Use `LEFT JOIN` or `LIMIT` to avoid full-table scans on failure.
- **Caching:** Implement cache invalidation strategies (e.g., TTLs, event-based refresh).
- **Async Tasks:** Use queues (e.g., RabbitMQ, Kafka) for non-critical operations.

```sql
-- Safe query with fallback (PostgreSQL)
SELECT
  u.id,
  u.name,
  COALESCE(p.email, 'unknown@example.com') AS email
FROM users u
LEFT JOIN profiles p ON u.id = p.user_id
WHERE u.active = true;
```

---

### **4. Expose Health Checks**
Use a dedicated endpoint (e.g., `/health`) with structured responses:

```javascript
// Fast, lightweight health check
app.get('/health', (req, res) => {
  // Simulate checking multiple services
  Promise.all([
    checkDatabase(),
    checkCache(),
  ]).then(([dbStatus, cacheStatus]) => {
    res.json({
      status: 'normal',
      services: {
        database: dbStatus,
        cache: cacheStatus,
      },
    });
  });
});

async function checkDatabase() {
  try {
    await db.query('SELECT 1');
    return 'up';
  } catch (err) {
    return 'down';
  }
}
```

---

### **5. Handle Retries Client-Side**
Clients should:
- Respect `Retry-After` headers.
- Implement exponential backoff.
- Avoid retrying critical operations during degraded states.

**Example (Python with `requests`):**
```python
import requests
import time

def fetch_with_retry(url, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 30)
                time.sleep(int(retry_after))
                retries += 1
                continue
            return response.json()
        except requests.exceptions.RequestException as e:
            retries += 1
            time.sleep(2 ** retries)  # Exponential backoff
    raise Exception("Max retries exceeded")
```

---

### **6. Test Your Availability**
- **Chaos Engineering:** Simulate failures (e.g., kill database processes).
- **Load Testing:** Use tools like **Locust** or **k6** to test rate limits.
- **Integration Tests:** Verify behavior under degraded states.

**Example Load Test (Locust):**
```python
# locustfile.py
from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def fetch_orders(self):
        with self.client.get('/api/orders', catch_response=True) as response:
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                self.wait(int(retry_after))
                self.fetch_orders()
```

---

## **Common Mistakes to Avoid**

### **1. Ignoring HTTP Status Codes**
❌ **Bad:** Always return `200` and let clients parse errors.
✅ **Good:** Use `429`, `503`, or `408` (Request Timeout) appropriately.

### **2. Not Communicating Degraded States**
❌ **Bad:** Crash silently during high load.
✅ **Good:** Expose `/health` and use `503` with `Retry-After`.

### **3. Blind Retries Without Backoff**
❌ **Bad:** Retry every request indefinitely.
✅ **Good:** Use exponential backoff and respect `Retry-After`.

### **4. Overloading Databases with Fallbacks**
❌ **Bad:** Return partial data by running slow fallback queries on every failure.
✅ **Good:** Cache fallbacks or use read replicas.

### **5. Hiding Failures Behind "Internal Server Error"**
❌ **Bad:** Catch all errors and return `500`.
✅ **Good:** Distinguish between:
- `500 Internal Server Error` (bugs).
- `503 Service Unavailable` (temporary).
- `429 Too Many Requests` (rate limiting).

### **6. Not Documenting Availability Policies**
❌ **Bad:** Assume clients know how to handle failures.
✅ **Good:** Document:
- Retry strategies.
- Health check endpoints.
- Expected partial responses.

---

## **Key Takeaways**

- **Availability Conventions** treat failures as expected, not exceptional.
- **Graceful degradation** (e.g., partial data) is better than crashes.
- **Status codes and headers** (e.g., `429`, `Retry-After`) guide clients.
- **Health checks** help clients decide whether to retry.
- **Instrumentation** (logs, metrics, tracing) is critical for debugging.
- **Test failures** with chaos engineering and load tests.

---

## **Conclusion**

APIs don’t run in a vacuum—they operate in dynamic environments where failures are inevitable. **Availability Conventions** shift the mindset from "nothing should fail" to "what happens when it does?" By designing for graceful degradation, clear communication, and predictable behavior, you build systems that:
- **Respect clients’ time** (no indefinite waits).
- **Avoid cascading failures** (isolate components).
- **Provide better user experiences** (clear error messages).
- **Are easier to debug** (structured logs and metrics).

Start small: add rate limiting, expose `/health`, and test failure scenarios. Over time, your APIs will become more resilient—and your users will notice.

**Next Steps:**
1. Audit your API for unhandled failure modes.
2. Implement `/health` and rate limiting.
3. Test with chaos engineering tools like **Chaos Mesh** or **Gremlin**.
4. Document your availability policies for the team.

Happy coding!
```