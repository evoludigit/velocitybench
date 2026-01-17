```markdown
# **Capacity Planning Patterns: Scaling Your Database and APIs Like a Pro**

**Designing systems to handle growth without breaking under pressure isn’t just about adding more servers—it’s about patterns. In this post, we’ll explore proven capacity planning patterns for databases and APIs, their trade-offs, and how to apply them in real-world scenarios.**

---

## **Introduction: Why Capacity Planning Matters**

Imagine your application is a bustling restaurant. **Capacity planning** is the equivalent of ensuring you have enough tables, chefs, and inventory to handle a dinner rush—without breaking dishes or disappointing guests. For backend systems, this means ensuring your databases and APIs can scale efficiently under load, whether it’s a viral product launch or a slow, steady growth.

Most developers start with a monolithic setup—a single database and a single API—until they hit a bottleneck. Then, they scramble to scale, often with costly refactoring. **The smarter approach?** Plan for capacity *upfront* using proven patterns. This post covers:

- **Database capacity patterns** (sharding, replication, read replicas)
- **API capacity patterns** (caching, rate limiting, load balancing)
- **Hybrid approaches** (microservices + serverless)
- **Practical code examples** in SQL, Go, and Python

By the end, you’ll understand when to use which pattern—and how to avoid common pitfalls.

---

## **The Problem: Growing Pain Points**

Most systems start small but face challenges as they scale:

1. **Database Bottlenecks**
   - A single MySQL instance can’t handle 10K requests/sec.
   - Write-heavy workloads (e.g., fintech transactions) slow down responses.
   - Read-heavy workloads (e.g., analytics dashboards) overwhelm the main database.

2. **API Latency Under Load**
   - Caching strategies (Redis, CDNs) degrade if misconfigured.
   - Unrestricted rate limits lead to API abuse or DDoS risks.
   - Poor load distribution causes uneven resource usage.

3. **Cost vs. Performance Tradeoffs**
   - Over-provisioning wastes money; under-provisioning causes outages.
   - Vertical scaling (bigger machines) hits limits; horizontal scaling (more machines) adds complexity.

4. **Data Consistency Risks**
   - Sharding introduces distributed transaction challenges.
   - Eventual consistency in caching can lead to stale data.

**Example:** A startup’s API handles 1K requests/day with a single PostgreSQL instance. When traffic spikes to 100K/day, response times degrade, and users complain.

---

## **The Solution: Capacity Planning Patterns**

Capacity planning isn’t a single fix—it’s a mix of patterns tailored to your workload. Below are the most effective strategies, categorized by layer.

---

### **1. Database Capacity Patterns**

#### **A. Read Replicas (Scale Reads)**
When your app reads far more than it writes (e.g., e-commerce product catalogs), read replicas distribute read load across multiple database instances.

**How it works:**
- Master database handles writes.
- Replicas sync data asynchronously (or synchronously) and handle reads.
- Clients route read queries to replicas.

**Trade-offs:**
✅ **Pros:** Linear scaling for reads, low cost.
❌ **Cons:** Eventual consistency (stale reads), replication lag, increased complexity.

**Example (PostgreSQL):**
```sql
-- Configure a read replica in PostgreSQL (using logical replication)
CREATE PUBLICATION app_reads FOR TABLE products, users;

-- On the replica side:
CREATE SUBSCRIPTION app_reads_sub CONNECTION 'host=replica dbname=app' PUBLICATION app_reads;
```

**Code Example (Go – Routing Reads):**
```go
func GetProduct(productID int) (*Product, error) {
    if isWriteRequest() {
        return dbMaster.GetProduct(productID) // Master handles writes
    }
    return dbReplica.GetProduct(productID)   // Replica handles reads
}
```

#### **B. Sharding (Horizontal Partitioning)**
When a single database can’t handle the volume, **sharding** splits data across multiple instances by key (e.g., user ID, region).

**How it works:**
- Data is partitioned (e.g., by `user_id % 4`).
- A **shard router** directs queries to the correct shard.

**Trade-offs:**
✅ **Pros:** Scales writes and reads independently.
❌ **Cons:** Joins across shards are hard; complex failover; eventual consistency.

**Example (MongoDB Sharding):**
```javascript
// Enable sharding on a collection
sh.shardCollection("users", { "country": "hashed" });

// Query automatically routed to the correct shard
db.users.find({ country: "US" });
```

**Code Example (Python – Shard Router):**
```python
def get_shard(user_id):
    return f"shard-{user_id % 4}"

def get_user(user_id):
    shard = get_shard(user_id)
    return db_clients[shard].find_one({"id": user_id})
```

#### **C. Caching (Reduce Database Load)**
Cache frequent queries (e.g., product listings, user profiles) in Redis or Memcached to offload the database.

**How it works:**
- Write-through: Update cache *and* DB.
- Write-behind: Update cache first, then DB (async).
- Read-through: Check cache first, fall back to DB.

**Trade-offs:**
✅ **Pros:** 10x faster reads, reduces DB load.
❌ **Cons:** Cache invalidation complexity, stale data risks.

**Example (Redis Caching):**
```python
import redis

r = redis.Redis(host='localhost', port=6379)
cache = r.get("product:123")

if not cache:
    cache = db.get_product(123)
    r.setex("product:123", 3600, cache)  # Cache for 1 hour
```

---

### **2. API Capacity Patterns**

#### **A. Rate Limiting (Prevent Abuse)**
Limit requests per client (e.g., 100 requests/minute/user) to:
- Prevent DDoS attacks.
- Fairly distribute traffic.

**Approaches:**
- **Token Bucket:** Issues tokens at a fixed rate.
- **Leaky Bucket:** Buffers requests at a fixed rate.
- **Fixed Window:** Counts requests in sliding windows.

**Example (Nginx Rate Limiting):**
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
server {
    location /api/ {
        limit_req zone=api_limit burst=50;
    }
}
```

**Code Example (Python – Token Bucket):**
```python
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_tokens, refill_rate):
        self.tokens = defaultdict(lambda: max_tokens)
        self.refill_rate = refill_rate
        self.last_refill = defaultdict(lambda: 0)

    def consume(self, client_id):
        now = time.time()
        self._refill(client_id, now)
        if self.tokens[client_id] <= 0:
            raise Exception("Rate limit exceeded")
        self.tokens[client_id] -= 1
        return True

    def _refill(self, client_id, now):
        elapsed = now - self.last_refill[client_id]
        tokens_gained = elapsed * self.refill_rate
        self.tokens[client_id] = min(
            self.tokens[client_id] + tokens_gained,
            100  # Max tokens
        )
        self.last_refill[client_id] = now
```

#### **B. Load Balancing (Distribute Traffic)**
Spread API requests across multiple servers to avoid overloading a single instance.

**Tools:**
- Nginx, HAProxy (Layer 7)
- AWS ALB, Cloudflare (Managed)

**Example (Nginx Load Balancer):**
```nginx
upstream api_backend {
    server backend1:8080;
    server backend2:8080;
    server backend3:8080;
}

server {
    location /api/ {
        proxy_pass http://api_backend;
    }
}
```

#### **C. Caching APIs (CDN + Edge Caching)**
Offload static content (e.g., images, JS, CSS) to a CDN like Cloudflare or Fastly.

**Example (Cloudflare Workers):**
```javascript
// Cache dynamic API responses at the edge
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
});

async function handleRequest(request) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/users/')) {
        // Check cache first
        const cache = caches.default;
        const cachedResponse = await cache.match(request);
        if (cachedResponse) return cachedResponse;

        // Fall back to origin
        const response = await fetch(request);
        const clone = response.clone();
        cache.put(request, clone);
        return response;
    }
}
```

---

### **3. Hybrid Patterns (Microservices + Serverless)**
For unpredictable workloads, combine:
- **Microservices** (for stable workloads).
- **Serverless** (for spiky traffic, e.g., AWS Lambda).

**Example:**
```yaml
# Terraform: Auto-scaling microservice + serverless
resource "aws_lb" "api_lb" {
  name               = "api-lb"
  load_balancer_type = "application"
}

resource "aws_lambda_function" "spike_handler" {
  function_name = "scale-on-demand"
  handler       = "main.handler"
  runtime       = "go1.x"
}
```

---

## **Implementation Guide**

### **Step 1: Profile Your Workload**
Before choosing patterns, measure:
- **Read/write ratio** (e.g., 90% reads → read replicas).
- **Peak traffic** (e.g., 10x during Black Friday).
- **Data locality** (e.g., users in the same region → regional sharding).

**Tools:**
- Prometheus + Grafana (metrics)
- JMeter (load testing)

### **Step 2: Start Simple, Iterate**
1. **Monolithic DB + API** → Works for <1K users.
2. **Add read replicas** when reads slow down.
3. **Shard writes** when writes bottleneck.
4. **Cache aggressively** for static data.
5. **Introduce rate limiting** if abuse is detected.

### **Step 3: Automate Scaling**
Use:
- **Auto-scaling groups** (AWS, GCP).
- **Database autopilot** (e.g., Aurora Serverless).
- **CI/CD pipelines** to test scaling.

---

## **Common Mistakes to Avoid**

1. **Over-Caching**
   - Caching everything leads to **cache stampedes** and inconsistent data.
   - *Fix:* Use **TTL** (time-to-live) and **cache invalidation strategies**.

2. **Ignoring Write Performance**
   - Replicas help reads but **not writes**—a single master can become a bottleneck.
   - *Fix:* Use **sharding** for high-write workloads.

3. **Poor Shard Key Selection**
   - Sharding by `user_id` is fine, but sharding by `timestamp` leads to **hot shards**.
   - *Fix:* Use **composite keys** (e.g., `user_id + random_suffix`).

4. **No Graceful Degradation**
   - If one shard fails, the whole system crashes.
   - *Fix:* Implement **multi-active replicas** or **circuit breakers**.

5. **Underestimating Cold Starts**
   - Serverless functions have latency on first call.
   - *Fix:* Use **warm-up calls** or **provisioned concurrency**.

---

## **Key Takeaways**

| **Pattern**               | **Best For**                          | **Trade-offs**                          | **When to Avoid**                     |
|---------------------------|---------------------------------------|-----------------------------------------|---------------------------------------|
| **Read Replicas**         | Read-heavy workloads                  | Eventual consistency                    | Writes are also frequent              |
| **Sharding**              | High write/read volume                | Complex joins, failover                 | Small, predictable loads              |
| **Caching**               | Frequent, static queries              | Cache invalidation                     | Data must be fresh                     |
| **Rate Limiting**         | Preventing abuse/DDoS                 | False positives (legit users blocked)   | Low-traffic APIs                       |
| **Load Balancing**        | Distributing traffic                  | Addition latency (DNS resolution)       | Single AZ deployments                  |
| **Serverless**            | Spiky, unpredictable traffic          | Cold starts, vendor lock-in             | Long-running tasks                    |

---

## **Conclusion: Scale Intentionally**

Capacity planning isn’t about guessing—it’s about **measuring, iterating, and automating**. Start with read replicas for reads, shard when writes bottleneck, and cache aggressively for static data. Use rate limiting to protect your API, and leverage serverless for unpredictable spikes.

**Remember:**
- **No silver bullet.** Combine patterns based on your workload.
- **Test under load.** Use tools like Locust or k6 to simulate traffic.
- **Monitor everything.** Prometheus, Datadog, or CloudWatch are your friends.

Now go forth and build systems that scale—not just for today, but for tomorrow’s traffic spikes.

---
**Further Reading:**
- [Google’s SRE Book (Capacity Planning)](https://sre.google/sre-book/capacity-planning/)
- [Database Sharding Deep Dive (Citus)](https://www.citusdata.com/blog/)
- [API Rate Limiting Patterns (O’Reilly)](https://www.oreilly.com/library/view/api-design-patterns/9781491950659/)

**What’s your favorite capacity planning pattern?** Share in the comments!
```