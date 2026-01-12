```markdown
# **"Availability Gotchas: How to Build Fault-Tolerant APIs That Never Go Down"**

*Your API might look perfect in staging—until it hits real-world load, network failures, and human error. In this guide, we’ll cover common availability pitfalls (and how to avoid them) so your services stay up even when the world tries to break them.*

---

## **Introduction: Why Availability Matters More Than You Think**

As a backend developer, you’ve probably spent countless hours debugging slow queries, optimizing cache misses, or refactoring monolithic code. But there’s one killer bug you might not be prepared for: **when your API simply stops working—no errors, no logs, just silence.**

This isn’t a hypothetical. Real-world systems fail under:
- Unexpected traffic spikes (e.g., a viral tweet, a DDoS attack, or a misconfigured cron job).
- Network partitions (a misrouted Kubernetes pod, AWS AZ failure, or misconfigured VPN).
- Human error (a `kubectl delete --all` in production, a misplaced firewall rule, or a `rm -rf /` typo).

If your API isn’t designed to handle these scenarios gracefully, users will see **503 errors, timeouts, or blank screens**—and your team will spend hours scrambling to restore service.

In this guide, we’ll explore **"Availability Gotchas"**—common assumptions that lead to outages—and **practical patterns** to make your APIs resilient. We’ll cover:
✅ **Database connection pools and timeouts**
✅ **Retry logic that backfires**
✅ **Circuit breakers and fallback strategies**
✅ **Graceful degradation under load**
✅ **Monitoring and alerting for downtime**

By the end, you’ll know how to build systems that **never go down**—or at least recover quickly when they do.

---

## **The Problem: Why Your API Might Die Unexpectedly**

Most backend engineers focus on **correctness** (e.g., "Does this query return the right data?") and **performance** (e.g., "Is this API response time under 500ms?"). But **availability**—the ability to handle failures—is often an afterthought. Let’s look at three real-world scenarios where APIs fail silently:

### **1. The Database Connection Pool Dries Up**
Imagine your Node.js API connects to PostgreSQL using `pg-pool` with a default pool size of **5 connections**. Suddenly, your app scales to **100 requests/second**, but the database can only handle **20 concurrent queries**. The remaining 80 requests **hang forever**, making your API unresponsive.

```javascript
// ❌ Default pool size (too small for load)
const pool = new Pool({
  user: 'postgres',
  host: 'db.example.com',
  max: 5, // Too low!
});
```
**Result?** Users see **timeout errors** or **blank screens**—but your server logs don’t show any errors because the client never got a response.

---

### **2. Retries That Amplify Problems**
Your backend calls an external API (e.g., Stripe, a third-party payment service). When it fails, you **retry automatically**—but the service is **overloaded**, so your retries **make things worse**. Now, Stripe’s API is **flooded with failed requests**, and your system **keeps failing**.

```javascript
// ❌ Naive retry logic (exponential backoff would help, but this is worse)
async function chargeCustomer(userId, amount) {
  while (true) {
    try {
      await stripe.charge({ userId, amount });
      break;
    } catch (err) {
      console.log("Retrying...");
      await new Promise(resolve => setTimeout(resolve, 1000)); // No exponential backoff!
    }
  }
}
```
**Result?** Your app **spawns a retry storm**, worsening the outage.

---

### **3. No Graceful Degradation**
Your API fetches user data from **three sources**:
1. **Primary database** (fast, but occasionally slow)
2. **Cache (Redis)** (faster, but can be stale)
3. **Fallback to a legacy API** (slow, but always available)

If the primary database fails, your app **waits forever** instead of falling back to Redis or the legacy system.

```javascript
// ❌ No fallback logic (database failure = app failure)
async function getUserData(userId) {
  const data = await db.query(`SELECT * FROM users WHERE id = $1`, [userId]);
  return data.rows[0];
}
```
**Result?** A **single database issue** brings down your entire API.

---

## **The Solution: Availability Gotchas to Watch For (And Fix)**

The good news? **Most availability issues are preventable** with small, intentional changes. Below are the **key patterns** to make your APIs resilient:

| **Gotcha**               | **Problem**                          | **Solution**                          |
|--------------------------|--------------------------------------|---------------------------------------|
| **Database timeouts**    | Queries hang indefinitely.           | Set **connection timeouts** and **retry logic**. |
| **Retry storms**         | Exponential retries flood systems.   | Use **circuit breakers** and **backoff**. |
| **No fallbacks**         | A single failure kills everything.   | Implement **gradual degradation**. |
| **Unbounded retries**    | Long-running failures block threads. | Use **asynchronous retries** (e.g., queues). |
| **No monitoring**        | Failures go unnoticed.               | Set up **alerting for availability**. |

Let’s dive into each of these with **code examples**.

---

## **1. Database Connection Timeouts and Retries**

### **The Problem**
Database queries can **block indefinitely** if:
- The database is slow (e.g., a large `JOIN`).
- The network is unstable (e.g., AWS AZ failure).
- The connection pool is exhausted.

Without timeouts, your API **hangs forever**, making it **unresponsive**.

### **The Solution: Timeouts + Retry Logic**
Use **connection timeouts** and **exponential backoff retries**:

#### **Option 1: PostgreSQL (Node.js with `pg-pool`)**
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  user: 'postgres',
  host: 'db.example.com',
  max: 20, // Larger pool for load
  connectionTimeoutMillis: 2000, // Fail fast if DB is slow
});

// Retry failed queries with exponential backoff
async function safeQuery(query, params) {
  let lastError;
  let delay = 100; // Start with 100ms delay

  while (delay <= 5000) { // Max 5 seconds
    try {
      const { rows } = await pool.query(query, params);
      return rows;
    } catch (err) {
      lastError = err;
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2; // Exponential backoff
    }
  }
  throw lastError; // Give up after max retries
}

// Usage:
safeQuery('SELECT * FROM users WHERE id = $1', [123]);
```

#### **Option 2: MySQL (Python with `sqlalchemy`)**
```python
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import time

engine = create_engine(
    "mysql+pymysql://user:pass@db.example.com/db",
    pool_size=10,
    pool_timeout=30,  # Fail fast if pool is exhausted
    pool_recycle=3600,  # Recycle connections after 1 hour
)

def safe_query(query, params):
    last_error = None
    delay = 0.1  # Start with 100ms delay
    max_delay = 5  # Max 5 seconds

    while delay <= max_delay:
        try:
            with engine.connect() as conn:
                result = conn.execute(query, params)
                return result.fetchall()
        except OperationalError as e:
            last_error = e
            time.sleep(delay)
            delay *= 2  # Exponential backoff
    raise last_error
```

### **Key Takeaways for Database Timeouts**
✔ **Set `connectionTimeoutMillis`** (PostgreSQL) or `pool_timeout` (SQLAlchemy) to fail fast.
✔ **Use exponential backoff** (`delay *= 2`) to avoid retry storms.
✔ **Limit max retries** (e.g., 5 attempts) to prevent infinite loops.
✔ **Monitor slow queries** (e.g., with `pg_stat_statements` or `slow_query_log`).

---

## **2. Retry Storms: Circuit Breakers for External APIs**

### **The Problem**
If you **retry failed API calls** without limits, you can:
- **Worsen the failure** (e.g., Stripe’s API gets flooded).
- **Exhaust thread pools** (e.g., Node.js `unhandledPromiseRejections`).
- **Block your own system** (e.g., a retry loop ties up a database connection).

### **The Solution: Circuit Breakers**
A **circuit breaker** temporarily **stops retries** when a service is failing, allowing it to recover.

#### **Option 1: Node.js (using `opossum`)**
```javascript
const { CircuitBreaker } = require('opossum');

const stripeCircuitBreaker = new CircuitBreaker(async (params) => {
  return await stripe.charge(params);
}, {
  timeout: 5000, // Fail after 5s
  errorThresholdPercentage: 50, // Open circuit if 50% of calls fail
  resetTimeout: 30000, // Reset after 30s
});

// Usage:
try {
  await stripeCircuitBreaker.charge({ userId: 123, amount: 100 });
} catch (err) {
  console.error("Stripe is down! Falling back to payment gateway.");
}
```

#### **Option 2: Python (using `tenacity` + `requests`)**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import requests
import logging

@retry(
    stop=stop_after_attempt(3),  # Max 3 retries
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    before_sleep=before_sleep_log(logging, logging.warning),
)
def call_external_api(url, data):
    response = requests.post(url, json=data)
    response.raise_for_status()  # Raise HTTP errors
    return response.json()

# Usage:
try:
    call_external_api("https://api.stripe.com/charges", {"amount": 100})
except Exception as e:
    logging.error("Fallback to payment gateway.")
```

### **Key Takeaways for Circuit Breakers**
✔ **Use a circuit breaker** (e.g., `opossum`, `tenacity`, or `Resilience4j`).
✔ **Set a timeout** (e.g., 5s) to avoid hanging.
✔ **Open the circuit after X failures** (e.g., 50% error rate).
✔ **Auto-retry after resetTimeout** (e.g., 30s) to allow recovery.

---

## **3. Graceful Degradation: Fallbacks for Critical Paths**

### **The Problem**
If your API relies on **one critical dependency** (e.g., a database, external API, or cache), a failure **kills everything**.

### **The Solution: Multi-Level Fallbacks**
Instead of failing fast, **gradually degrade**:

#### **Example: Database + Cache + Legacy API Fallback**
```javascript
// ⚡ Fast path: Cache (Redis)
async function getUserData(userId) {
  const cachedData = await redis.get(`user:${userId}`);
  if (cachedData) return JSON.parse(cachedData);

  // 🔄 Slow path: Database (PostgreSQL)
  try {
    const dbData = await pool.query(
      'SELECT * FROM users WHERE id = $1',
      [userId]
    );
    await redis.set(`user:${userId}`, JSON.stringify(dbData.rows[0]), 'EX', 300);
    return dbData.rows[0];
  } catch (err) {
    console.warn("Database failed, falling back to legacy API...");

    // 🏛️ Emergency fallback: Legacy REST API
    try {
      const legacyResponse = await fetchLegacyUserAPI(userId);
      return legacyResponse.data;
    } catch (legacyErr) {
      console.error("All fallbacks failed!");
      throw new Error("User data unavailable (temporary issue)");
    }
  }
}
```

### **Key Takeaways for Graceful Degradation**
✔ **Use a fallback chain** (e.g., cache → DB → legacy API).
✔ **Cache aggressively** to reduce DB load.
✔ **Log warnings** (not errors) when fallbacks kick in.
✔ **Return a graceful error** (e.g., `503 Service Unavailable`) instead of crashing.

---

## **4. Asynchronous Retries (Queues over Threads)**

### **The Problem**
If retries are **synchronous**, they **block threads** (e.g., in Node.js or Java), leading to:
- **Thread pool exhaustion** (e.g., `unhandledPromiseRejections` in Node).
- **Long GC pauses** (if retries hold locks).

### **The Solution: Offload Retries to a Queue**
Use **message queues** (e.g., RabbitMQ, SQS, Kafka) to **decouple retries** from your main API.

#### **Example: Node.js with RabbitMQ**
```javascript
const amqp = require('amqp');
const conn = amqp.createConnection({ host: 'rabbitmq' });
conn.on('ready', async () => {
  const queue = await conn.queue('failed-payments', { durable: true });

  // Send to queue instead of retrying immediately
  await queue.send(JSON.stringify({
    userId: 123,
    amount: 100,
    retries: 0,
  }));
});
```

#### **Consumer (Retry Worker)**
```javascript
conn.on('ready', () => {
  const queue = conn.queue('failed-payments');

  queue.subscribe({
    acknowledgeMessage: (msg) => {
      const { userId, amount, retries } = JSON.parse(msg.content.toString());

      if (retries >= 3) {
        // Give up after 3 retries
        console.error("Max retries reached for user:", userId);
        return;
      }

      try {
        await stripe.charge({ userId, amount });
        console.log("Payment succeeded!");
      } catch (err) {
        console.log(`Retry #${retries + 1} for user ${userId}`);
        // Requeue with increased retries
        queue.send(JSON.stringify({
          ...msg.content.toString(),
          retries: retries + 1,
        }));
      }
    },
  });
});
```

### **Key Takeaways for Async Retries**
✔ **Offload retries to a queue** (e.g., RabbitMQ, SQS).
✔ **Use workers to process retries** (not your API endpoints).
✔ **Limit max retries** (e.g., 3 attempts).
✔ **Monitor queue length** to detect failures early.

---

## **5. Monitoring & Alerting for Availability**

### **The Problem**
If your API fails, **how will you know?** Without monitoring:
- Failures go **unnoticed** until users complain.
- You **can’t compare "before/after" metrics**.
- You **miss scaling opportunities**.

### **The Solution: Alerts for Downtime**
Use **synthetic monitoring** (e.g., Pingdom, UptimeRobot) and **metrics** (e.g., Prometheus, Datadog) to detect issues.

#### **Example: Prometheus + Alertmanager (Node.js)**
```javascript
const client = new promClient.Client();
const collectDefaultMetrics = promClient.collectDefaultMetrics;

// Metrics to track
const requestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  buckets: [0.1, 0.5, 1, 2, 5],
});

// Middleware to track API responses
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    requestDuration.observe({ path: req.path }, duration);
  });
  next();
});

// Alert: If 90% of requests take > 1s, alert!
collectDefaultMetrics();
client
  .register.collect()
  .then(metrics => console.log(metrics));
```

#### **Alert Rule (Alertmanager)**
```yaml
# alertmanager.config.yaml
groups:
- name: availability-alerts
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.90, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High API latency (90th percentile > 1s)"
      description: "Check for slow dependencies or DB timeouts."
```

### **Key Takeaways for Monitoring**
✔ **Track latency** (e.g., `http_request_duration`).
✔ **Set up alerts** (e.g., Prometheus + Alertmanager).
✔ **Monitor queue lengths** (e.g., Kafka/SQS lag).
✔ **Use synthetic checks** (e.g., UptimeRobot) for external availability.

---

## **Common Mistakes to Avoid**

| **Mistake**                          | **Why It’s Bad**                          | **How to Fix It**                          |
|--------------------------------------|-------------------------------------------|--------------------------------------------|
| **No timeouts on DB/API calls**      | Queries hang indefinitely.                | Set `timeout` and `pool_timeout`.          |
| **Unlimited retries**                | Retry storms flood systems.               | Use **circuit breakers** (max 3 retries).  |
| **No fallbacks**                     | Single failure kills everything.           | Implement **cache + legacy API fallbacks**. |
| **