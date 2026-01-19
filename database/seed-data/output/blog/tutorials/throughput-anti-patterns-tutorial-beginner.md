```markdown
---
title: "Throughput Anti-Patterns: How to Not Break Your System at Scale"
author: "Alex Chen"
date: "2023-10-15"
tags: ["database design", "api design", "scalability", "backend engineering"]
---

# Throughput Anti-Patterns: How to Not Break Your System at Scale

![System overload illustration](https://via.placeholder.com/800x300?text=Throughput+Anti-Patterns+Illustration)

As a backend engineer, you’ve probably faced moments where your application *seems* to work perfectly during development and testing—but then, when it hits production with real-world traffic, the wheels fall off. One of the most sneaky culprits behind this is **poor throughput handling**. Throughput—the rate at which your system processes requests—isn’t just about raw power; it’s about **design choices, query patterns, and architectural decisions** that silently sabotage your system’s scalability.

In this post, we’ll explore **throughput anti-patterns**—common pitfalls that drain resources, create bottlenecks, and turn your system into a performance nightmare. We’ll cover the problems, solutions, and code examples to help you avoid these traps. By the end, you’ll know how to design systems that **scale gracefully under load** instead of choking at even moderate traffic.

---

## The Problem: Why Throughput Matters

### The Silent Killer of Scalability
Imagine you’ve built a feature that works fine at 1,000 requests per second (RPS), but when traffic spikes to 10,000 RPS, your database starts throwing timeouts, memory usage surges, or latency spikes. What went wrong?

Often, it’s not a lack of hardware—but **poor throughput design**. Throughput anti-patterns are design choices that **inefficiently allocate resources**, create **unnecessary overhead**, or **fail to distribute load** evenly. These patterns waste CPU, memory, and I/O, making your system feel sluggish even when it’s "over-provisioned."

### Real-World Examples
- **E-commerce Cart Abandonment**: A 30-second delay in checkout increases abandonment rates by 30%. If your cart feature has a throughput anti-pattern (e.g., repeatedly querying user carts without caching), you’re directly hurting revenue.
- **Social Media Feeds**: A poorly optimized "trending posts" API might block the entire database while fetching popular content, causing delays for all users.
- **API Gateways**: A misconfigured load balancer with no throughput monitoring might send all traffic to a single backend instance, causing it to crash under load.

### The Cost of Ignoring Throughput
- **Increased Cloud Bills**: Poorly optimized queries force you to buy more (and more expensive) servers.
- **Poor User Experience**: Slow responses lead to frustrated users and lost business.
- **Technical Debt**: Fixing throughput issues later often requires rewriting code, not just tuning.

---

## The Solution: Throughput Anti-Patterns (And How to Fix Them)

Throughput anti-patterns fall into three broad categories:
1. **Database-Level Issues** (How your queries behave under load).
2. **Application-Level Issues** (How your code processes requests).
3. **Infrastructure-Level Issues** (How your system distributes and manages load).

We’ll dive into each with **actionable fixes** and **code examples**.

---

## 1. Database-Level Throughput Anti-Patterns

### Anti-Pattern 1: N+1 Query Problem
**What it is**: Fetching data in one step, but your ORM (or custom code) makes an additional N queries to load related data.

**Why it’s bad**:
- Each query adds latency and database load.
- Under load, the database can’t keep up, causing timeouts.

#### Example: The N+1 Problem in Code
```python
# Bad: Fetch all users, THEN fetch each user's orders (N+1 queries)
users = db.session.query(User).all()
orders = []
for user in users:
    orders.append(db.session.query(Order).filter_by(user_id=user.id).first())

# This is 1 + N queries where N = number of users!
```

#### The Fix: Use Eager Loading or Batch Fetching
```python
# Good: Use JOIN or subqueries to fetch everything in one go
users_with_orders = db.session.query(
    User,
    Order.user_id.label("ord_id"),
    Order.id.label("ord_id"),
    Order.amount
).join(Order, User.id == Order.user_id).all()

# Or use LEFT JOIN to avoid missing orders
users_with_orders = db.session.query(User, Order).outerjoin(Order, User.id == Order.user_id).all()
```

**Key Takeaway**: Always analyze your query plans (`EXPLAIN` in SQL) to spot hidden N+1 issues.

---

### Anti-Pattern 2: Select * (Fetching All Columns)
**What it is**: Writing `SELECT *` instead of explicitly listing columns.

**Why it’s bad**:
- Databases send **unnecessary data** over the network.
- Under load, this increases memory usage and CPU time.

#### Example: The SELECT * Trap
```sql
-- Bad: Fetching ALL columns (could be hundreds!)
SELECT * FROM users WHERE id = 1;
```

#### The Fix: List Only Needed Columns
```sql
-- Good: Only fetch what you need
SELECT id, name, email FROM users WHERE id = 1;
```

**Key Takeaway**: Use `pg_pretty` (PostgreSQL) or `EXPLAIN ANALYZE` to check if your queries are bloated.

---

### Anti-Pattern 3: No Indexes on Filtered Fields
**What it is**: Querying tables with `WHERE` clauses on unindexed columns.

**Why it’s bad**:
- The database must **scan every row**, slowing down queries.
- Under load, full table scans cause **disk I/O bottlenecks**.

#### Example: Missing Indexes
```sql
-- Bad: No index on `email`, forcing a full table scan
SELECT * FROM users WHERE email = 'user@example.com';
```

#### The Fix: Add Indexes (Carefully!)
```sql
-- Good: Add an index for frequently queried fields
CREATE INDEX idx_users_email ON users(email);
```

**Key Takeaway**: Use `ANALYZE` to confirm indexes are being used. Too many indexes slow down writes!

---

### Anti-Pattern 4: Long-Running Transactions
**What it is**: Transactions that hold locks for too long (e.g., loops in application code).

**Why it’s bad**:
- Locks **block other transactions**, reducing concurrency.
- Under high load, this leads to **deadlocks and timeouts**.

#### Example: Blocking Transaction
```python
# Bad: A long-running transaction (e.g., processing a large report)
with db.session.begin():
    users = db.session.query(User).all()
    for user in users:
        # Simulate work (e.g., analytics, notifications)
        time.sleep(2)  # Delay of 2 seconds per user!
```

#### The Fix: Break Work into Smaller Transactions
```python
# Good: Process in chunks with smaller transactions
batch_size = 1000
users = db.session.query(User).limit(batch_size).all()
for user in users:
    with db.session.begin():  # Short-lived transaction
        # Do one user at a time
        update_user_stats(user)
```

**Key Takeaway**: Use `pg_stat_activity` (PostgreSQL) to detect long-running transactions.

---

## 2. Application-Level Throughput Anti-Patterns

### Anti-Pattern 5: Synchronous External Calls
**What it is**: Waiting for external APIs or services without async/parallelism.

**Why it’s bad**:
- Each call **blocks the thread**, wasting CPU.
- Under load, this turns a fast app into a single-threaded bottleneck.

#### Example: Blocking API Calls
```python
# Bad: Synchronous HTTP calls (e.g., Python requests)
def fetch_user_data(user_id):
    response = requests.get(f"https://external-api/users/{user_id}")  # Blocks!
    return response.json()
```

#### The Fix: Use Async/Parallelism
```python
# Good: Async HTTP calls (e.g., Python aiohttp)
async def fetch_user_data(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://external-api/users/{user_id}") as resp:
            return await resp.json()
```

**Key Takeaway**: Use `async/await` (Python), `Promise` (Node.js), or `goroutines` (Go) for I/O-bound work.

---

### Anti-Pattern 6: No Connection Pooling
**What it is**: Creating new database connections for every request.

**Why it’s bad**:
- Each connection uses **memory and file descriptors**.
- Under load, you exhaust system resources and cause timeouts.

#### Example: No Connection Pooling
```python
# Bad: New connection per request
def get_user_by_id(id):
    conn = psycopg2.connect("dburl")  # New connection!
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (id,))
    return cursor.fetchone()
```

#### The Fix: Use a Connection Pool
```python
# Good: Configure a pool (e.g., SQLAlchemy's pool_size)
from sqlalchemy import create_engine
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=10,  # Reuse connections
    max_overflow=20  # Allow extra connections if needed
)

def get_user_by_id(id):
    with engine.connect() as conn:
        return conn.execute("SELECT * FROM users WHERE id = :id", {"id": id}).fetchone()
```

**Key Takeaway**: Set `pool_size` to ~2-5x the number of application threads.

---

### Anti-Pattern 7: Uncached Repeated Work
**What it is**: Recomputing the same data over and over (e.g., fetching the same API response repeatedly).

**Why it’s bad**:
- **Wastes CPU and network bandwidth**.
- Under load, this creates **unnecessary load on upstream services**.

#### Example: No Caching
```python
# Bad: Fetching the same data repeatedly
def get_user_stats(user_id):
    # Same API call for every stats request!
    response = requests.get(f"https://analytics-api/stats/{user_id}")
    return response.json()
```

#### The Fix: Use Caching (Redis, Memcached)
```python
import redis
r = redis.Redis()

def get_user_stats(user_id):
    cache_key = f"user:{user_id}:stats"
    cached_data = r.get(cache_key)
    if cached_data:
        return cached_data  # Return cached version
    else:
        response = requests.get(f"https://analytics-api/stats/{user_id}")
        r.set(cache_key, response.json(), ex=300)  # Cache for 5 minutes
        return response.json()
```

**Key Takeaway**: Cache **expensively computed** or **frequently accessed** data.

---

## 3. Infrastructure-Level Throughput Anti-Patterns

### Anti-Pattern 8: No Load Balancing
**What it is**: Sending all traffic to a single backend server.

**Why it’s bad**:
- **No redundancy**—if the server crashes, your app crashes.
- **No scalability**—you can’t distribute load.

#### Example: No Load Balancer
```bash
# Bad: Direct traffic to one server (e.g., Nginx without upstream)
server {
    listen 80;
    server_name api.example.com;
    location / {
        proxy_pass http://localhost:5000;  # Only one server!
    }
}
```

#### The Fix: Use a Load Balancer
```bash
# Good: Distribute traffic across multiple servers (e.g., Nginx with upstream)
upstream backend {
    server 192.168.1.10:5000;
    server 192.168.1.11:5000;
    server 192.168.1.12:5000;
}

server {
    listen 80;
    server_name api.example.com;
    location / {
        proxy_pass http://backend;
    }
}
```

**Key Takeaway**: Use **round-robin** or **least-connections** strategies for most cases.

---

### Anti-Pattern 9: No Rate Limiting
**What it is**: Allowing unlimited requests from a single IP or user.

**Why it’s bad**:
- **Malicious bots** can overload your system.
- **Legitimate users** can accidentally cause outages (e.g., a poorly written script).

#### Example: No Rate Limiting
```python
# Bad: No protection against abuse
@app.route("/endpoint")
def handler():
    # Anyone can call this as much as they want!
    return {"data": "..."}
```

#### The Fix: Add Rate Limiting (e.g., Flask-Limiter)
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@limiter.limit("100 per minute")  # Allow 100 requests/minute
@app.route("/endpoint")
def handler():
    return {"data": "..."}
```

**Key Takeaway**: Start with **per-IP limits** (e.g., 100 RPS), then adjust.

---

### Anti-Pattern 10: No Monitoring
**What it is**: Not tracking performance metrics under load.

**Why it’s bad**:
- **You don’t know where bottlenecks occur**.
- **Outages happen silently** until users complain.

#### Example: No Monitoring Setup
```python
# Bad: No metrics collection
@app.route("/")
def home():
    return "Hello, World!"
```

#### The Fix: Enable APM (e.g., Datadog, New Relic)
```python
# Good: Instrument your app (e.g., with OpenTelemetry)
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

@app.route("/")
def home():
    with tracer.start_as_current_span("homepage"):
        return "Hello, World!"
```

**Key Takeaway**: Track **latency, throughput, and error rates** in production.

---

## Implementation Guide: Checking for Throughput Issues

### Step 1: Profile Your Database Queries
- Use `EXPLAIN ANALYZE` (PostgreSQL) to analyze query performance.
- Look for:
  - Full table scans (`Seq Scan`).
  - Slow joins (`Nested Loop` without indexes).
  - High `Seq Scan` rows.

```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

### Step 2: Analyze Application Logs
- Check for **timeouts, slow requests, or high latency**.
- Tools: `stdout`, `ELK Stack`, `Datadog`.

### Step 3: Test Under Load
- Use **load testing tools** like:
  - `locust` (Python)
  - `k6` (JavaScript)
  - `JMeter` (Java)
- Example Locust script:
  ```python
  from locust import HttpUser, task

  class DatabaseUser(HttpUser):
      @task
      def fetch_user(self):
          self.client.get("/users/1")  # Simulate 100 RPS
  ```

### Step 4: Monitor Infrastructure
- Check:
  - CPU/memory usage (`top`, `htop`).
  - Database connections (`pg_stat_activity`).
  - Network I/O (`iftop`).

---

## Common Mistakes to Avoid

1. **Over-Optimizing Without Benchmarks**:
   - Don’t prematurely optimize. Profile first, then optimize.

2. **Ignoring Write vs. Read Throughput**:
   - Some workloads (e.g., logs) are **write-heavy**; others (e.g., reads) are **read-heavy**. Design accordingly.

3. **Assuming "More Servers = Faster"**:
   - Adding servers doesn’t fix **non-scalable queries** or **bottlenecks**.

4. **Not Testing Failure Modes**:
   - How does your app behave when:
     - A database crashes?
     - A cache fails?
     - A upstream API is slow?

5. **Assuming SQL is the Only Bottleneck**:
   - Sometimes, the **application logic** or **network** is the issue.

---

## Key Takeaways

✅ **Database Queries**:
- Avoid `SELECT *` and unindexed fields.
- Use eager loading or batch fetching.
- Keep transactions short and non-blocking.

✅ **Application Code**:
- Use async/parallelism for I/O-bound tasks.
- Implement connection pooling.
- Cache repeated work.

✅ **Infrastructure**:
- Use load balancers for redundancy.
- Enforce rate limiting.
- Monitor everything in production.

✅ **Testing**:
- Profile before optimizing.
- Test under realistic load.
- Fail fast (and gracefully).

---

## Conclusion

Throughput anti-patterns are **silent killers**—they don’t crash your app in production, but they **gradually erode performance** until your system feels slow, unreliable, and expensive to run. By recognizing these patterns and applying the fixes we’ve discussed, you’ll build systems that **scale gracefully**, handle spikes in traffic, and keep users happy.

### Next Steps:
1. **Audit your current system** for these anti-patterns.
2. **Test with load** to find bottlenecks.
3. **Start small**—fix one layer at a time (database → application → infrastructure).
4. **Monitor continuously**—performance is an ongoing journey, not a one-time fix.

Now go forth and build **scalable, high-throughput systems**! 🚀

---
**Further Reading**:
- ["Database Performance Tuning" (Use the Index, Luke!)](https://use-the-index-luke.com/)
- ["Designing Data-Intensive Applications" (Martin Kleppmann)](https://dataintensive.net/)
- ["High Performance MySQL" (Baron Schwartz)](https://www.oreilly.com/library/view/high-performance-mysql/9781449332471/)
```