```markdown
---
title: "Throughput Testing: The Unseen Hero of Scalable APIs (With Real-World Code Examples)"
date: 2023-10-15
author: "Alex Carter"
tags: ["database", "api-design", "performance", "testing"]
---

# Throughput Testing: The Unseen Hero of Scalable APIs

As backend engineers, we often fixate on individual requests—latency, error rates, and 99th-percentile response times. Yet, in real-world applications, success isn’t measured by how fast one request completes, but by how many requests your system can handle **simultaneously** without collapse. This is where **throughput testing** becomes your secret weapon.

Throughput testing reveals how your system behaves under *load*—whether that’s concurrent users, API calls, or database operations. It exposes bottlenecks (hidden in unit tests), validates scalability assumptions, and ensures your backend doesn’t turn into a single-point-of-failure when traffic spikes. In this guide, we’ll dive into why throughput testing matters, how to implement it practically, and how to avoid common pitfalls—using real-world examples to demonstrate tradeoffs and solutions.

---

## The Problem: When "It Works on My Machine" Isn’t Enough

Let’s start with a relatable scenario. You’re building a “successful” e-commerce backend. Your API handles product listings, cart operations, and checkout—each feature is tested in isolation with a mock database. Throughput? Not a priority. Then, Black Friday hits.

**What goes wrong:**
1. **Database locks and contention**: Your `ORDER` table gets flooded with concurrent `INSERT`/`UPDATE` operations, causing row-level locks that choke transactions.
2. **Connection pool starvation**: Too many concurrent requests drain your database connection pool, leaving new connections to wait in limbo.
3. **Memory pressure**: Caching layers (Redis, in-memory stores) get overwhelmed, forcing costly disk fallbacks.
4. **Cold starts**: Serverless functions or containers fail to scale quickly enough, leading to timeouts.

All of these issues are *silent* until they break. Worse, they’re often undetectable in traditional unit or integration tests, which run sequentially and under controlled conditions.

> **Example**: A well-optimized REST API might handle 100ms requests for a single user, but under 100 concurrent users, it collapses due to race conditions in a shared cache. This is throughput testing’s job to catch.

---

## The Solution: Designing for Throughput

Throughput testing isn’t just about throwing load at your system—it’s about designing for resilience under realistic conditions. The key components include:

1. **Load Generation**: Simulating concurrent users/API calls with controlled patterns.
2. **Monitoring**: Tracking throughput metrics (RPS, TPS, error rates) and system health (CPU, memory, disk).
3. **Automation**: Integrating tests into CI/CD to catch regressions early.
4. **Bottleneck Analysis**: Identifying where throughput drops off (e.g., database, network, code).

---

## Components/Solutions: Tools and Techniques

### 1. Load Generation
Use tools like **Locust**, **k6**, or **JMeter** to simulate concurrent users. Below is a minimal example using **Locust** for an API measuring order throughput.

#### Example: Locust Test for Order API
```python
from locust import HttpUser, task, between

class OrderUser(HttpUser):
    wait_time = between(1, 3)  # Random wait time between requests

    @task
    def create_order(self):
        payload = {
            "user_id": 123,
            "items": [{"product_id": 456, "quantity": 2}]
        }
        self.client.post("/api/orders", json=payload, headers={"Content-Type": "application/json"})

    @task(3)  # 3x more likely to run than create_order
    def get_order_status(self):
        self.client.get("/api/orders/123/status")
```

*Tradeoff*: Locust is simple but lacks advanced features like HTTP/2 or graphing. For complex scenarios, **k6** (with its JavaScript-based syntax) or **JMeter** (with its visual scripting) are better.

---

### 2. Database Stress Testing
Throughput testing isn’t just about HTTP—your database is the true bottleneck. Use **PostgreSQL’s `pgbench`**, **MySQL’s `sysbench`**, or **custom tools** to simulate simultaneous queries.

#### Example: `pgbench` for Write Throughput
```bash
# Simulate 100 concurrent users inserting data (100x more aggressive than pgbench default)
pgbench -i -s 100 -c 100 -T 60 my_database
```
*Output metrics*:
```
transaction type: TPS (transactions per second)
... (repeated lines)
total time:      60.006 s
transactions:    31253 per second
latency average: 3192.627 ms
```

*Tradeoff*: `pgbench` is database-specific and doesn’t model real-world query patterns. For complex scenarios, use **custom scripts** or **load-testing tools** (e.g., **k6** with PostgreSQL plugins).

---

### 3. Cache Resilience Testing
Caches like Redis fail catastrophically when under load. Test with tools like **redis-stress** or **custom scripts**:

```python
# Python script to simulate cache busting
import redis
import random
import time

r = redis.Redis(host='localhost', port=6379)
keys = ["key_" + str(i) for i in range(1, 10000)]

for _ in range(1000):
    key = random.choice(keys)
    r.setex(key, 60, "value_" + str(random.randint(1, 10)))
    r.get(key)  # Simulate read
```

*Tradeoff*: This is a simple example. For production-like tests, use **Locust with Redis plugins** or **JMeter**.

---

### 4. Monitoring and Alerts
Track metrics in real-time. Tools like **Prometheus + Grafana** or **Dynatrace** help visualize throughput vs. errors.

#### Example: Grafana Dashboard for Throughput
1. Set up Prometheus to scrape your app’s `/metrics` endpoint.
2. Add these queries:
   - `rate(http_requests_total[1m])` (RPS)
   - `database_operations_total` (custom metric)
   - `error_rate` = `sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))`

![Example Grafana Dashboard](https://grafana.com/static/img/docs/dashboard-example.png)

---

## Implementation Guide: Step-by-Step Throughput Testing

### Step 1: Define Your Targets
- **Baseline**: What’s your current throughput?
- **Goals**: How many RPS/TPS do you need for your peak traffic?
- **Failures**: What’s your error threshold (e.g., >1% errors = fail)?

*Example*:
| Metric       | Target       |
|--------------|--------------|
| RPS          | 1000         |
| 99th pctl RT | <500ms       |
| Error Rate   | <0.1%        |

---

### Step 2: Instrument Your Code
Add metrics to track end-to-end performance:
```go
// Example in Go (using Prometheus client)
var (
    httpRequestsTotal = prom.NewCounterVec(
        prom.CounterOpts{
            Name: "http_requests_total",
            Help: "Total HTTP requests.",
        },
        []string{"method", "endpoint", "status"},
    )
)

func handler(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    defer func() {
        httpRequestsTotal.WithLabelValues(
            r.Method,
            r.URL.Path,
            http.StatusText(w.(http.ResponseWriter).Status()),
        ).Inc()
    }()
    // ... your logic ...
    latency := time.Since(start)
    metrics.LatencyHistogram.WithLabelValues(r.URL.Path).Observe(latency.Seconds())
}
```

---

### Step 3: Set Up Load Tests
Use **Locust** or **k6** to simulate users. Ramp up gradually:
```bash
# Locust example: 10 users for 5 minutes, ramp up to 1000
locust -f locustfile.py --headless --host=http://localhost:8080 --users 10 --spawn-rate 2 --run-time 300s --max-users 1000
```

---

### Step 4: Analyze Bottlenecks
When throughput drops:
1. Check **database logs** for slow queries (`EXPLAIN ANALYZE`).
2. Monitor **memory usage** (e.g., Redis memory spikes).
3. Review **cache hit ratios** (e.g., Redis `keyspace_hits` vs. `keyspace_misses`).

*Example*:
```sql
-- Find slow PostgreSQL queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

### Step 5: Optimize and Repeat
Optimize bottlenecks (e.g., add indexes, shard tables, tune Redis memory) and retest.

---

## Common Mistakes to Avoid

1. **Testing Too Late**: Wait until production? No. Integrate throughput tests in your CI/CD pipeline.
2. **Ignoring Non-Linear Scaling**: Assume 10x users = 10x throughput? Wrong. Database connections, caches, and OS limits often break linearity.
3. **No Gradual Ramp-Up**: Jumping from 10 to 1000 users at once exposes issues you won’t catch.
4. **Overlooking Edge Cases**: Test:
   - Long-running queries (e.g., reports).
   - Network partitions (simulate with `chaos engineering` tools).
   - Cache invalidation race conditions.
5. **False Positives**: A high RPS doesn’t mean success if errors spike or latency explodes.

---

## Key Takeaways

### For Backend Engineers:
- **Throughput ≠ Latency**: Optimize for both, but throughput catches hidden issues.
- **Test Early, Test Often**: Integrate load tests into your workflow.
- **Design for Failure**: Assume components will fail; test resilience.
- **Monitor in Production**: Use tools like Prometheus to track real-world throughput.

### For Architects:
- **Decouple Components**: Cache, database, and API layers should scale independently.
- **Use Connection Pools**: For databases (e.g., PgBouncer for PostgreSQL).
- **Plan for Spikes**: Serverless, auto-scaling, or load-balanced architectures help.

### For DevOps:
- **Set Up Alerts**: Notify when throughput drops (e.g., RPS < 90% of target).
- **Benchmark Regularly**: Compare against baselines to catch regressions.

---

## Conclusion

Throughput testing isn’t about building the fastest backend—it’s about building one that *works under load*. By simulating real-world traffic, you uncover bottlenecks before they impact users, validate scalability assumptions, and ensure your API remains resilient.

Remember:
- **Start small**: Test early with simple scripts.
- **Iterate**: Throughput testing is part of the feedback loop, not a one-time task.
- **Automate**: Integrate tests into your pipeline to catch regressions.

Now go write those load tests—your future self (and your users) will thank you.

---
### Further Reading
- [k6 Docs: Throughput Testing](https://k6.io/docs/guides/load-testing-glossary/#throughput)
- [PostgreSQL Performance Tuning](https://pgmustard.com/)
- [Redis Performance Testing](https://redis.io/topics/benchmarks)

---
### Appendix: Sample Docker Compose for Locust + Redis
```yaml
version: '3'
services:
  locust:
    image: locustio/locust
    ports:
      - "8089:8089"
    depends_on:
      - app
      - redis
    environment:
      - LOCUST_HOST=http://app:8080
    volumes:
      - ./locustfile.py:/mnt/locust/locustfile.py

  app:
    image: your-app-image
    ports:
      - "8080:8080"
    depends_on:
      - redis

  redis:
    image: redis
    ports:
      - "6379:6379"
```

---
```