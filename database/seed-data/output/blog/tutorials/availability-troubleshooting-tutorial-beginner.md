```markdown
---
title: "How to Troubleshoot Availability Issues: A Beginner-Friendly Guide to Keeping Your Apps Online"
date: 2024-02-15
tags: ["database", "api", "backend", "devops", "troubleshooting"]
description: "Learn how to diagnose and resolve availability problems in your systems with practical patterns, code examples, and real-world tradeoffs"
author: "Alex Carter"
---

# **How to Troubleshoot Availability Issues: A **Code-First** Guide**

As a backend developer, nothing feels worse than staring at a downtime alert while users flood your support channel with complaints. Availability isn’t just about uptime—it’s about *rate*, *latency*, and *recoverability*. Whether your API is crawling under load or your database is stuck in a read-only state, a systematic approach to troubleshooting can save you hours of frustration.

In this post, we’ll explore the **Availability Troubleshooting Pattern**, a structured way to diagnose and fix availability issues. Think of it as a **checklist with code examples** to help you methodically identify bottlenecks—whether they’re in your database, API layer, or infrastructure.

---

## **The Problem: Why Availability Troubleshooting Matters**

Imagine this scenario:
- Your service is under heavy traffic (e.g., Black Friday sales).
- Users start reporting timeouts.
- Your monitoring tool shows a spike in **HTTP 503 errors** and **database connection pool exhaustion**.
- You check logs, but the error messages are vague: `"Connection refused"` or `"Query timeout."`

Without a structured approach, you might:
- Blindly restart services (which *sometimes* works, but often masks the root cause).
- Blindly increase resource limits (which can hide inefficiencies).
- Waste time digging through logs without a clear path.

This is where the **Availability Troubleshooting Pattern** comes in. It provides a **reproducible, step-by-step methodology** to:
✅ **Isolate** whether the issue is in your app, database, or network.
✅ **Reproduce** the problem under controlled conditions.
✅ **Fix** it with minimal downtime.

---

## **The Solution: The Availability Troubleshooting Pattern**

The pattern follows a **four-phase approach**:

1. **Reproduce the Issue**
   - Confirm the problem exists and understand its scope.
2. **Isolate the Problem**
   - Narrow down whether it’s API-level, database-level, or external.
3. **Diagnose the Root Cause**
   - Use logs, metrics, and controlled experiments.
4. **Resolve & Validate**
   - Apply fixes and verify they work.

Let’s dive into each phase with **real-world examples**.

---

## **Phase 1: Reproduce the Issue**

Before fixing anything, you need to **confirm the problem**. A misconfigured alert might trigger false positives, or the issue could be temporary.

### **Example: API Timeout Under Load**
Suppose your `/checkout` API starts failing under load. Here’s how to reproduce it:

#### **Load Testing with `locust` (Python)**
```python
from locust import HttpUser, task

class CheckoutUser(HttpUser):
    @task
    def trigger_checkout(self):
        self.client.post("/checkout", json={"user_id": 123})
```

Run it with:
```bash
locust -f checkout_locustfile.py --host=https://your-api.com --users=100 --spawn-rate=50
```
If errors spike, **you’ve reproduced the issue**.

#### **Key Questions to Ask:**
- Does the issue happen **consistently** under load?
- Is it **transactional** (e.g., only during peak hours) or **random**?
- Does it affect **all users** or just a subset?

**Tradeoff:** Load testing requires infrastructure, but it’s better than guessing.

---

## **Phase 2: Isolate the Problem**

Now, determine if the issue is in:
- The **API layer** (e.g., connection pooling, rate limiting).
- The **database** (e.g., slow queries, deadlocks).
- **Network/External services** (e.g., downstream API failures).

### **Example: Isolating a Database Bottleneck**

#### **Check Database Metrics (PostgreSQL Example)**
```sql
-- Check active connections
SELECT usename, count(*) as connections
FROM pg_stat_activity
GROUP BY usename;

-- Slowest queries
SELECT query, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

If you see:
- **High connection count** → Likely **connection pooling** issue.
- **Slow queries** → Possible **indexing problem**.

#### **Example: Connection Pool Exhaustion**
If your app uses `pgbouncer` or `PgPool`, check logs:
```bash
# Check pgbouncer stats
SELECT * FROM pgbouncer.stats WHERE dbname = 'your_db';

# If pool is full, new connections fail
```
**Fix:** Increase pool size **temporarily** to confirm:
```python
# Django (with django-db-geventpool)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'POOL_SIZE': 50,  # Default is 10
    }
}
```

---

## **Phase 3: Diagnose the Root Cause**

### **Case 1: API-Level Issues (Timeouts, Rate Limiting)**
If the issue is in your API, check:
- **Request/Response logging** (e.g., `logrus` in Go).
- **Latency breakdown** (e.g., `OpenTelemetry` traces).

#### **Example: Go HTTP Middleware for Latency Tracking**
```go
package main

import (
	"net/http"
	"time"
)

func logRequestDuration(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		defer func() {
			log.Printf("%s %s took %v", r.Method, r.URL.Path, time.Since(start))
		}()
		next.ServeHTTP(w, r)
	})
}
```

#### **Case 2: Database-Level Issues (Slow Queries, Deadlocks)**
If queries are slow, optimize with:
- **EXPLAIN ANALYZE** (PostgreSQL):
  ```sql
  EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
  ```
- **Index tuning** (if missing):
  ```sql
  CREATE INDEX idx_orders_user_id ON orders(user_id);
  ```

#### **Case 3: External Dependencies**
If a downstream API fails, check:
- **Retry logic** (exponential backoff).
- **Circuit breakers** (e.g., `Hystrix` or `Resilience4j`).

**Example: Python with `tenacity`**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_external_api():
    response = requests.get("https://external-service.com/api")
    response.raise_for_status()
    return response.json()
```

---

## **Phase 4: Resolve & Validate**

### **Temporary Fixes (for Recovery)**
- **Scale up** (e.g., increase DB read replicas).
- **Restart services** (if stuck in a bad state).
- **Bypass problematic services** (e.g., disable a slow third-party API).

### **Permanent Fixes (to Prevent Future Issues)**
- **Database:**
  - Add indexes for slow queries.
  - Optimize connection pooling.
- **API:**
  - Implement **circuit breakers**.
  - Add **rate limiting** (`NGINX` or `Redis`).

#### **Example: NGINX Rate Limiting**
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend;
    }
}
```

### **Validation**
After applying fixes:
1. **Reproduce the issue again** (load test).
2. **Monitor metrics** (e.g., `Prometheus`).
3. **Roll back if needed** (use **blue-green deployment**).

---

## **Implementation Guide: Step-by-Step Checklist**

| Step | Action | Tools/Commands |
|------|--------|----------------|
| 1 | **Reproduce** | Load test with `Locust`, `k6` |
| 2 | **Check API logs** | `journalctl`, `ELK Stack` |
| 3 | **Check DB metrics** | `pg_stat_activity`, `EXPLAIN ANALYZE` |
| 4 | **Isolate** | `pgbouncer.stats`, `Redis info` |
| 5 | **Fix** | Optimize queries, scale, retry logic |
| 6 | **Validate** | Load test again, monitor |

---

## **Common Mistakes to Avoid**

1. **Ignoring Logs**
   - ❌ *"It must be network!"*
   - ✅ **Always check logs first** (`/var/log/nginx/error.log`, `Docker logs`).

2. **Overlooking Connection Pooling**
   - ❌ *"I’ll just increase DB size."*
   - ✅ **Tune connection pooling** (`pgbouncer`, `PgPool`).

3. **Not Load Testing Before Deployment**
   - ❌ *"It works locally!"*
   - ✅ **Test under realistic load** (`Locust`, `k6`).

4. **Blindly Restarting Services**
   - ❌ *"Restarting fixed it!"* (but might not be a fix).
   - ✅ **Diagnose first**, then restart if needed.

5. **Assuming All Queries Are Slow**
   - ❌ *"My SELECTs are slow!"*
   - ✅ **Use `EXPLAIN ANALYZE` to find the culprit.**

---

## **Key Takeaways**

✅ **Reproduce first** – Confirm the issue exists.
✅ **Isolate** – API? DB? Network?
✅ **Diagnose** – Logs, metrics, `EXPLAIN ANALYZE`.
✅ **Fix incrementally** – Temporary fixes → permanent optimizations.
✅ **Validate** – Load test again, monitor.

---

## **Conclusion**

Availability troubleshooting isn’t about fixing symptoms—it’s about **systematically diagnosing bottlenecks**. By following the **Availability Troubleshooting Pattern**, you’ll avoid:
- Blindly restarting services.
- Wasting time on incorrect assumptions.
- Deploying fixes that don’t work.

**Start small:**
1. **Reproduce** the issue with load tests.
2. **Check logs and metrics** (database, API).
3. **Optimize** connection pooling, queries, and retries.
4. **Validate** with monitoring.

The next time your API crashes under load, you’ll have a **structured, code-backed approach** to get it back up—**and stay up** this time.

---
**Further Reading:**
- [PostgreSQL Performance Tips](https://www.postgresql.org/docs/current/using-explain.html)
- [Locust Load Testing](https://locust.io/)
- [Circuit Breakers in Go](https://resilience4j.io/)

**Got questions?** Drop them in the comments—I’d love to discuss your own availability challenges!
```