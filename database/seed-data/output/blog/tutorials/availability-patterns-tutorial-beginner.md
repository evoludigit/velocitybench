```markdown
---
title: "Availability Patterns: Building Resilient APIs for Modern Applications"
date: "2023-11-15"
tags: ["backend", "database design", "API design", "resilience", "patterns"]
---

# Availability Patterns: Building Resilient APIs for Modern Applications

When you're building an API that powers a web app or serves millions of users, nothing feels worse than a *10-minute downtime* that hits your front page on Twitter. Or worse yet—that fatal error that takes your entire system down for hours.

You’ve probably spent hundreds (or thousands) of hours fixing bugs, optimizing queries, and scaling infrastructure. Yet, if your system isn’t designed for **availability**, everything else becomes meaningless. Availability isn’t just about uptime—it’s about ensuring your application stays responsive under pressure, fails gracefully when things go wrong, and recovers quickly when they do.

In this guide, we’ll explore **availability patterns**—practical techniques to make your APIs resilient against failures. We’ll cover:
- Why availability matters beyond uptime
- Common failure modes that break availability
- Real-world patterns to improve availability
- Code examples in Python, SQL, and Redis
- Anti-patterns to avoid

---

## The Problem: Why Availability Matters Beyond Uptime

### "But Isn’t Database Replication Enough?"
Replication is a great start—it copies data to multiple nodes—but it doesn’t solve all availability challenges. Consider these real-world failure scenarios:

1. **Network Partitions** (The "Split Brain" Problem):
   If your primary database node goes down and replicas take too long to sync, users might get stale or inconsistent data. Imagine an e-commerce site where a user’s cart state depends on a database that’s temporarily unreachable.

2. **Slow Queries or Lock Contention**:
   A single slow query (e.g., a misindexed join) can lock up a read/write database, blocking all requests. Think of a social media site where a user’s timeline query gets stuck, freezing the login page for everyone.

3. **Hardware Failures or Server Crashes**:
   A server crash (or even a memory leak) can bring down your entire service. Vertical scaling alone can’t protect you from a failure in your primary database node.

4. **API Gateway or Load Balancer Failures**:
   If your load balancer misroutes traffic or your API gateway hangs, even healthy backend services won’t help users.

5. **Human Errors or Bad Data**:
   A rogue script, a misconfigured backup, or a malicious actor (e.g., a hacker sending a flood of `DELETE` requests) can overwhelm your system.

### The Cost of Poor Availability
- **Lost Revenue**: Every minute of downtime can cost thousands per second (e.g., a downtime calculator from [UptimeRobot](https://www.uptimerobot.com/blog/calculator/) shows that a 1% downtime per year for a $10M revenue company = $25,100 lost).
- **Poor User Experience**: Users expect instant responses. Even a 1-second delay can increase bounce rates by ~20% (Google’s [Speed Study](https://developer.chrome.com/docs/devtools/memory/performance/)).
- **Trust Erosion**: One major outage can make users distrust your service forever. Think of a bank’s API failing during tax season.

---

## The Solution: Availability Patterns to Build Resilient APIs

Availability patterns aren’t a single silver bullet—they’re a **toolbox** of strategies to handle failures gracefully. Below, we’ll dive into three key patterns with code examples:

1. **Database Read/Write Separation**
2. **Circuit Breakers**
3. **Retry with Exponential Backoff**
4. **Caching with Stale Data Handling**
5. **Bulkhead Pattern**

---

### 1. Database Read/Write Separation
**Problem**: A single database handling both reads and writes can become a bottleneck during traffic spikes or when a slow write query locks up the server.
**Solution**: Decouple read and write operations using dedicated replicas for reads.

#### How It Works
- **Write operations** go to a primary (master) database.
- **Read operations** go to replicas (slaves) to reduce load.
- Replicas stay in sync with the master.

#### Code Example: Python with SQLAlchemy
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Primary (write) database
primary_engine = create_engine("postgresql://user:password@primary-db:5432/app")
primary_session = sessionmaker(bind=primary_engine)

# Replica (read) database
replica_engine = create_engine("postgresql://user:password@replica-db:5432/app")
replica_session = sessionmaker(bind=replica_engine)

def write_user(name, email):
    with primary_session() as session:
        user = User(name=name, email=email)
        session.add(user)
        session.commit()

def read_profiles():
    # Read from replica to avoid locking the primary
    with replica_session() as session:
        return session.query(User).all()
```

#### When to Use
- For read-heavy applications (e.g., blogs, news sites).
- When writes are infrequent but reads are high (e.g., analytics dashboards).

#### Tradeoffs
- **Eventual Consistency**: Replicas may temporarily lag behind the primary.
- **Complexity**: Requires careful monitoring to detect and handle replication lag.

---

### 2. Circuit Breaker Pattern
**Problem**: A failing service (e.g., a payment gateway or external API) can crash your application if you keep retrying indefinitely.
**Solution**: Use a **circuit breaker** to detect failures and stop retrying after a threshold.

#### How It Works
- When a failure occurs, a circuit breaker trips and stops sending requests to the failing service.
- After a cooldown period, it resumes with a limited number of requests to test if the service is back.

#### Code Example: Python with `pybreaker`
```python
from pybreaker import CircuitBreaker

# Initialize a circuit breaker (fails after 3 failures, cooldown 10s)
breaker = CircuitBreaker(fail_max=3, reset_timeout=10)

@breaker
def call_external_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"External API failed: {e}")

# Usage
data = call_external_api("https://api.example.com/data")
```

#### When to Use
- Calling external APIs (e.g., Stripe, Twilio).
- When dependencies are critical but unreliable.

#### Tradeoffs
- **False Positives/Negatives**: May stop working when the dependency is actually healthy.
- **Latency Spike**: When the circuit breaker resets, there may be a delay as it tests the connection.

---

### 3. Retry with Exponential Backoff
**Problem**: Temporary failures (e.g., network blips or overload) can be retried successfully, but blind retries can overload a failing service.
**Solution**: Retry failed operations with increasing delays (exponential backoff).

#### How It Works
- First retry after 100ms, then 200ms, then 400ms, etc.
- Stop after a maximum number of retries or timeout.

#### Code Example: Python with `tenacity`
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def send_payment_webhook(payload):
    response = requests.post(
        "https://payment-gateway.example.com/webhook",
        json=payload,
        timeout=5
    )
    response.raise_for_status()
    return response.json()
```

#### When to Use
- Idempotent operations (e.g., sending webhooks, triggering async tasks).
- When failures are transient (e.g., network issues).

#### Tradeoffs
- **Non-Idempotent Operations**: Not safe for operations like `DELETE` (may cause duplicate deletions).
- **Infinite Loops**: If the service is truly broken, retries may never succeed.

---

### 4. Caching with Stale Data Handling
**Problem**: A slow database query can delay responses, and stale data may be acceptable for some use cases.
**Solution**: Cache frequently accessed data and serve stale data when the primary source is unavailable.

#### How It Works
- Use Redis or Memcached to cache responses.
- If the cache is unavailable, fall back to stale data or a backup data source.

#### Code Example: Python with Redis
```python
import redis
import json

r = redis.Redis(host="redis-cache", port=6379)

def get_user_profile(user_id):
    # Try cache first
    cached_data = r.get(f"user:{user_id}")
    if cached_data:
        return json.loads(cached_data)

    # Fall back to database
    try:
        user = User.query.get(user_id)
        if user:
            # Update cache with 5-minute TTL
            r.setex(f"user:{user_id}", 300, json.dumps(user.to_dict()))
        return user
    except Exception as e:
        # Return stale data if cache exists (even if it's old)
        if cached_data:
            return json.loads(cached_data)
        raise Exception(f"Failed to fetch user: {e}")
```

#### When to Use
- High-read applications (e.g., dashboards, user profiles).
- When stale data is tolerable (e.g., a user’s last activity time).

#### Tradeoffs
- **Inconsistency**: Users might see slightly old data.
- **Cache Invalidation**: Requires careful handling (e.g., TTLs, event-based invalidation).

---

### 5. Bulkhead Pattern
**Problem**: A single failure (e.g., a slow query) can block all threads in your application, bringing it to a halt.
**Solution**: Split your application into independent "bulkheads" so that one failure doesn’t crash everything.

#### How It Works
- Each bulkhead has its own thread pool or worker pool.
- If one bulkhead fails, others continue working.

#### Code Example: Python with `concurrent.futures`
```python
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

def process_order(order_id):
    # Simulate a slow operation that might fail
    try:
        if order_id == 9999:  # Simulate a failure
            raise Exception("Order processing failed")
        # Actual processing logic
        return f"Processed order {order_id}"
    except Exception as e:
        return f"Failed to process order {order_id}: {str(e)}"

# Bulkhead: Limit to 4 concurrent workers
with ThreadPoolExecutor(max_workers=4) as executor:
    orders = [1, 2, 3, 9999, 5]  # One failing order
    futures = [executor.submit(process_order, order) for order in orders]

    for future in concurrent.futures.as_completed(futures):
        print(future.result())
```

#### Output:
```
Processed order 1
Processed order 2
Processed order 3
Failed to process order 9999: Order processing failed
Processed order 5
```

#### When to Use
- CPU-bound or I/O-bound tasks (e.g., processing orders, generating reports).
- When you want to isolate failures.

#### Tradeoffs
- **Overhead**: Managing multiple pools adds complexity.
- **Resource Leaks**: If bulkheads aren’t cleaned up properly, they can consume too many resources.

---

## Implementation Guide: Putting It All Together

Here’s a step-by-step approach to applying these patterns to your backend:

### Step 1: Audit Your Failure Modes
- Identify where failures occur most often (e.g., external APIs, slow queries, network partitions).
- Use tools like:
  - **Prometheus + Grafana** for monitoring.
  - **Sentry** for error tracking.
  - **New Relic** for performance insights.

### Step 2: Start Small
- Pick **one pattern** (e.g., circuit breakers for external APIs) and implement it incrementally.
- Example: Add a circuit breaker to your payment service calls.

### Step 3: Test Failure Scenarios
- Simulate failures:
  - Kill database replicas randomly.
  - Inject latency into network calls.
  - Overload your API with traffic.
- Use tools like:
  - **Chaos Engineering Toolkit** ([chaostoolkit.org](https://chaostoolkit.org/)).
  - **Locust** for load testing.

### Step 4: Monitor and Iterate
- Track metrics like:
  - **Latency percentiles** (P99, P95).
  - **Error rates** per service.
  - **Cache hit/miss ratios**.
- Adjust patterns based on data (e.g., increase TTLs if cache misses are high).

### Step 5: Document Your Design
- Write a **runbook** for common failures (e.g., "If Redis fails, fall back to stale data").
- Document circuit breaker thresholds and retry policies.

---

## Common Mistakes to Avoid

1. **Over-Reliance on Retries**
   - ❌ Blindly retrying every failure (e.g., for non-idempotent operations).
   - ✅ Use retries **only for transient failures** and idempotent operations.

2. **Ignoring Cache Invalidation**
   - ❌ Setting infinite TTLs or not invalidating cache when data changes.
   - ✅ Use **event-based invalidation** (e.g., publish an event when a user is updated).

3. **Not Testing Failures**
   - ❌ Assuming your circuit breakers will work in production.
   - ✅ Test failure scenarios in staging (e.g., kill a database replica).

4. **Tight Coupling to Single Databases**
   - ❌ Relying on a single primary database.
   - ✅ Use **read replicas** and **multi-region deployments**.

5. **Ignoring Dependency Failures**
   - ❌ Not monitoring external APIs (e.g., Stripe, Twilio).
   - ✅ Set up alerts for dependency failures (e.g., "Stripe API latency > 500ms").

6. **No Graceful Degradation**
   - ❌ Crashing when a dependency fails.
   - ✅ Gracefully degrade (e.g., show cached data if the primary is down).

---

## Key Takeaways

- **Availability ≠ Uptime**: It’s about resilience, not just keeping the lights on.
- **Patterns Work Together**: Use multiple patterns (e.g., caching + circuit breakers + retries).
- **Test Failures**: Assume things will break and design for it.
- **Monitor and Iterate**: Availability is an ongoing process, not a one-time fix.
- **Start Small**: Pick one pattern (e.g., circuit breakers) and expand gradually.

---

## Conclusion

Building resilient APIs isn’t about perfection—it’s about **minimizing the impact of failures** when they happen. The patterns we’ve covered (read/write separation, circuit breakers, retries, caching, and bulkheads) are battle-tested tools to handle real-world issues.

Start with the pattern that affects your most critical bottlenecks. Test it in staging, monitor it in production, and iterate. Over time, your system will become more available, your users will stay happy, and your revenue will stay safe.

### Next Steps
- Experiment with **multi-region deployments** for global availability.
- Explore **event sourcing** for handling failures at the data level.
- Consider **serverless architectures** (e.g., AWS Lambda) for automatic scaling.

Happy coding—and may your availability always be 100%!
```

---
**Additional Resources**:
- [AWS Availability Zones](https://aws.amazon.com/about-aws/global-infrastructure/availability-zones/)
- [Chaos Engineering by Netflix](https://netflixtechblog.com/chaos-engineering-at-netflix-f8e748339378)
- [PyBreaker Documentation](https://github.com/benoitc/pybreaker)
- [Tenacity Retry Library](https://tenacity.readthedocs.io/)