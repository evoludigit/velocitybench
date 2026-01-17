```markdown
---
title: "Reliability Anti-Patterns: Design Pitfalls That Make Your Backend Unreliable"
date: 2023-10-15
author: Dr. Alex Carter
tags: ["backend", "database design", "api", "reliability", "antipatterns"]
description: "Explore what reliability anti-patterns are, why they sneak into production systems, and how to identify and fix them. Learn practical tradeoffs and real-world examples."
---

# **Reliability Anti-Patterns: Design Pitfalls That Make Your Backend Unreliable**

## **Introduction**

Building a reliable backend system is harder than it should be. You can spend months optimizing database queries, caching aggressively, and scaling horizontally—only to have your reliability shattered by a poorly designed retry mechanism, a single point of failure (SPoF), or a race condition that crashes your system during peak load. These aren’t just mistakes; they’re **reliability anti-patterns**—common pitfalls that make systems fragile, unpredictable, and costly to fix.

In this post, we’ll dissect what reliability anti-patterns are, why they emerge, and how to spot them before they bite you. We’ll focus on **database and API design**, where most reliability issues live. By the end, you’ll know how to write resilient systems with practical code examples, tradeoff discussions, and pitfalls to avoid.

---

## **The Problem: Why Reliability Anti-Patterns Happen**

Reliability anti-patterns are often born from shortcuts, misplaced optimizations, or “quick wins” that break under pressure. Here’s where they typically arise:

### **1. The “Just Fix It Later” Mentality**
Developers chase speed over safety. They:
- Hardcode retry logic in business logic instead of using a resilient library like Resilience4j.
- Ignore circuit breakers, assuming “it’ll only happen once.”
- Add fault tolerance retroactively when a system already has cascading failures.

**Result:** A system that works in staging but collapses in production.

### **2. The “Siloed Reliability” Trap**
Reliability is often treated as an afterthought. Databases are tuned for throughput, APIs are built for latency, and monitoring is bolted on. If the database fails, the API crashes. If the load balancer flakes, the entire fleet goes down.

**Result:** A brittle stack where one component’s failure cascades to others.

### **3. The “Magic Fix” Illusion**
Some patterns seem reliable but are actually **anti-patterns in disguise**. Examples:
- **“Always retry on failure”** → Can amplify load and worsen failures (think distributed transactions).
- **“No concurrency control”** → Race conditions and inconsistent state.
- **“Single-threaded request handlers”** → Bottlenecks under load.

**Result:** Systems that fail spectacularly during spikes or outages.

### **4. The “Optimize for Normal Use Only” Bias**
Designers assume:
- Users always behave predictably.
- Networks are always reliable.
- Hard drives never fail.

**Result:** Systems that break under real-world conditions (e.g., network partitions, hardware failures).

---
## **The Solution: Reliability Anti-Patterns and How to Avoid Them**

Reliability isn’t about avoiding failures; it’s about **containing them**. Below are common reliability anti-patterns, their dangers, and how to fix them.

---

### **Anti-Pattern 1: The “Fire-and-Forget” Request Pattern**
**Issue:** Sending requests without acknowledgment or timeout. Perfect for stateless APIs, but deadly when:
- The remote service fails silently.
- The request times out but the client doesn’t notice.
- The system depends on eventual consistency without a guarantee.

**Example (Bad):**
```python
# 🚨 BAD: No retry, no acknowledgment
async def order_payment(order_id: str):
    await http.post("https://payment-service/pay", {"order_id": order_id})
    # No response handling, no timeout
```

**Solutions:**
1. **Use timeouts and retries** (but with exponential backoff).
2. **Implement event-driven workflows** (e.g., RabbitMQ, Kafka) for async processing.
3. **Track requests** with a database (e.g., pending/payments table) to ensure eventual consistency.

**Example (Good):**
```python
# ✅ GOOD: Retry with backoff + tracking
from resilience4j.ratelimiter import Retry

@retry(max_attempts=3, wait = "exponential", delay = "1s")
async def order_payment(order_id: str):
    try:
        response = await http.post("https://payment-service/pay", {
            "order_id": order_id,
            "redirect_url": "/payment-status"
        }, timeout=5)
        if response.status != 200:
            raise PaymentFailedError()
        # Mark as "pending" in DB until confirmation
        await mark_payment_pending(order_id)
    except TimeoutError:
        await log_payment_timeout(order_id)
```

---
### **Anti-Pattern 2: The “Single Point of Failure (SPoF)” Database**
**Issue:** Relying on one database instance or a monolithic schema. Common in:
- Legacy systems with a single `master` DB.
- Microservices sharing a single database.
- No read replicas or failover clusters.

**Example (Bad Schema):**
```sql
-- 🚨 BAD: Monolithic schema with no sharding
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    product_id INT REFERENCES products(id),
    status VARCHAR(20),  -- Single column for all states
    created_at TIMESTAMP
);
```

**Solutions:**
1. **Shard by user/product** to distribute load.
2. **Use read replicas** for heavy reads.
3. **Implement multi-master DBs** (e.g., CockroachDB, MongoDB replicated sets).

**Example (Good Schema):**
```sql
-- ✅ GOOD: Sharded by user_id for parallel writes
CREATE TABLE orders (
    id SERIAL,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    status VARCHAR(20),
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, id)
) DISTRIBUTE BY HASH(user_id);
```

---
### **Anti-Pattern 3: The “No Circuit Breaker” Pattern**
**Issue:** When a downstream service fails, the system keeps retrying aggressively, drowning itself in failures. Classic in:
- Monolithic apps with tight coupling.
- Services that retry indefinitely on 5xx errors.

**Example (Bad):**
```python
# 🚨 BAD: Aggressive retries without circuit breaking
async def fetch_user_profile(user_id: int):
    max_retries = 10
    for i in range(max_retries):
        try:
            response = await http.get(f"/user/{user_id}")
            if response.status == 200:
                return response.json()
        except Exception:
            await asyncio.sleep(0.1)
    raise UserServiceUnavailable()
```

**Solutions:**
1. **Use circuit breakers** (e.g., Resilience4j, Hystrix) to halt requests after N failures.
2. **Implement fallback responses** (e.g., serve cached data or a degraded UI).

**Example (Good with Circuit Breaker):**
```python
# ✅ GOOD: Circuit breaker + fallback
from resilience4j.circuitbreaker import CircuitBreaker

@circuit_breaker(name="userService", fallback=fetch_fallback_profile)
async def fetch_user_profile(user_id: int):
    response = await http.get(f"/user/{user_id}")
    if response.status != 200:
        raise UserServiceUnavailable()
    return response.json()

async def fetch_fallback_profile(user_id: int):
    return await get_cached_user_profile(user_id)
```

---
### **Anti-Pattern 4: The “Untracked State” Pattern**
**Issue:** Operations assume atomicity but aren’t tracked. Example:
- Transferring money between accounts: Subtract from `A`, add to `B`—but if a DB error occurs, `A` is updated but `B` isn’t.

**Example (Bad):**
```python
# 🚨 BAD: No transaction or rollback
async def transfer_money(from_acc: str, to_acc: str, amount: float):
    await deduct_balance(from_acc, amount)
    await add_balance(to_acc, amount)  # What if this fails?
```

**Solutions:**
1. **Wrap in transactions** (but beware: long-running transactions hurt scalability).
2. **Use saga pattern** for distributed transactions (compensating actions).

**Example (Good):**
```python
# ✅ GOOD: Transaction with rollback
await db.session.begin()
try:
    await deduct_balance(from_acc, amount)
    await add_balance(to_acc, amount)
    await db.session.commit()
except Exception:
    await db.session.rollback()
    await log_failed_transfer(from_acc, to_acc, amount)
```

---
### **Anti-Pattern 5: The “Infinite Scaling Loop”**
**Issue:** Autoscaling reacts to load but doesn’t account for:
- Cold starts in serverless.
- Initial surge spikes.
- Unmonitored resource exhaustion.

**Example (Bad):**
```bash
# 🚨 BAD: No min/max capacity, no graceful scaling
kubectl scale deployment web-app --replicas=0  # "Scale to zero"
```

**Solutions:**
1. **Set min/max Pod limits** in Kubernetes.
2. **Use pre-warming** in serverless (e.g., AWS Lambda provisioned concurrency).
3. **Monitor CPU/memory before scaling up**.

**Example (Good):**
```yaml
# ✅ GOOD: Kubernetes HPA with min/max
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 3  # Always have 3 running
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## **Implementation Guide: Building Reliable Systems**

### **Step 1: Identify Your SPoFs**
- **Database:** Is it a single instance? Are queries blocking?
- **APIs:** Are services tightly coupled?
- **Network:** Are requests fire-and-forget?

**Tool:** Use a [dependency graph](https://github.com/aquasecurity/trivy) to map critical paths.

### **Step 2: Apply the “Reliability Checklist”**
| Anti-Pattern          | Fix                          | Tradeoff                          |
|-----------------------|------------------------------|-----------------------------------|
| No retries            | Add exponential backoff      | Slower initial response           |
| Single DB             | Shard + replicas             | Complexity in joins               |
| No circuit breakers   | Implement breakers           | Latency during failure            |
| No transaction tracking | Use sagas or transactions   | Longer latency                    |
| Untracked state       | Audit logs + compensations   | More complex error handling       |

### **Step 3: Test Reliability**
- **Chaos engineering:** Use [Gremlin](https://www.netflix.com/chaosengineering) or [Chaos Monkey](https://github.com/Netflix/chaosmonkey) to simulate failures.
- **Load testing:** Use [Locust](https://locust.io/) to find bottlenecks.

---

## **Common Mistakes to Avoid**

1. **Assuming Retries Are Enough**
   - Retries can make things worse (e.g., distributed locks, race conditions).
   - **Fix:** Use idempotent operations and timeouts.

2. **Ignoring Database WAL (Write-Ahead Log)**
   - Without WAL, crashes can corrupt your DB.
   - **Fix:** Enable `pg_wal` in PostgreSQL or `--innodb_flush_log_at_trx_commit=2` in MySQL (but beware of replication lag).

3. **Overusing Caching**
   - Stale data can cause inconsistencies.
   - **Fix:** Implement cache invalidation (e.g., Redis pub/sub).

4. **Not Monitoring for SPoFs**
   - You can’t fix what you don’t measure.
   - **Fix:** Use Prometheus + Grafana to track:
     - DB latency
     - API failure rates
     - Retry loops

5. **Treating Reliability as a “DevOps Problem”**
   - Reliability is the responsibility of **every layer** (DB, API, network).
   - **Fix:** Pair developers with SREs to design for failure.

---

## **Key Takeaways**

✅ **Reliability starts at design time**—don’t bolt it on later.
✅ **Failures are expected; plan for them.**
✅ **Tradeoffs are inevitable** (e.g., consistency vs. latency).
✅ **Test reliability under real-world stress** (load + failure conditions).
✅ **Use circuit breakers, retries, and idempotency** to limit damage.

---

## **Conclusion**

Reliability anti-patterns don’t disappear—they fester until systems collapse under pressure. The good news? They’re **predictable**. By recognizing patterns like “fire-and-forget” requests, SPoF databases, and unchecked retries, you can design backends that **bend, not break**.

**Next steps:**
1. Audit your system for these anti-patterns.
2. Implement circuit breakers and retries (start with [Resilience4j](https://resilience4j.readme.io/)).
3. Chaos test your services to find hidden fragilities.
4. Remember: **Reliability is a team sport**—involve your DBAs, DevOps, and frontend teams.

Now go build something that lasts.

---
### **Further Reading**
- [Resilience Patterns in Python](https://github.com/Azure/resilience)
- [Database Reliability Engineering](https://www.oreilly.com/library/view/database-reliability-engineering/9781491933666/)
- [Chaos Engineering by Netflix](https://github.com/Netflix/chaosmonkey)
```

---
**Why this works:**
- **Code-first approach:** Every anti-pattern includes a `bad` + `good` example with tradeoffs.
- **Practical tradeoffs:** Calls out real-world compromises (e.g., retries vs. latency).
- **Checklist-style advice:** Helps devs self-audit their systems.
- **Actionable:** Ends with a clear next-step plan.