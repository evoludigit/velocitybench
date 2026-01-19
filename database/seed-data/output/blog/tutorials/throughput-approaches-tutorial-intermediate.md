```markdown
# **Throughput Approaches: Scaling Your APIs and Databases for Real-World Load**

![Throughput Approaches Diagram](https://miro.medium.com/max/1400/1*XyZ1q987AJ5vL9KJU7Q6mQ.png)

As backend engineers, we’re constantly juggling two critical metrics: **latency** (how fast responses come back) and **throughput** (how many requests our system can handle per second). Most tutorials focus on optimizing latency—how to make a single request blazing fast—but **scaling for high throughput** is where real-world systems break down.

High throughput isn’t just about throwing more servers at the problem. It’s about **architectural design**, **query optimization**, **caching smartly**, and **distributing load** without sacrificing reliability. Whether you’re building a social media platform, a financial trading system, or even a high-traffic microservice, ignoring throughput can lead to cascading failures, degraded user experience, and costly downtime.

This guide dives deep into **throughput approaches**—practical strategies to handle massive request volumes while keeping costs and complexity in check. We’ll cover **horizontal scaling**, **caching layers**, **data partitioning**, and **asynchronous processing**, with real-world examples in Go, Python, and SQL.

---

## **The Problem: Why Throughput Matters (and Where It Fails)**

High throughput isn’t just a nice-to-have—it’s a **survival requirement** for modern applications. Here’s why:

### **1. Database Bottlenecks**
Most systems start with a single database instance. But as users (or queries) grow, even a well-optimized SQL server hits its limits:
- **Connection pooling exhaustion**: Too many open connections (e.g., 10K concurrent DB connections) drain memory.
- **Lock contention**: Long-running transactions block others, turning a 100ms query into a 10-second one.
- **Disk I/O saturation**: SSDs have limits—once you exceed them, queries time out or fail silently.

**Example**: A rising SaaS product sees **100K concurrent users**. Their PostgreSQL instance starts returning `503 Service Unavailable` errors after a few hours. Purchasing a beefier server temporarily fixes it… until the next spike.

### **2. API Latency Under Load**
Even if your database scales, your API might not keep up:
- **Synchronous processing**: Every user request waits for every downstream service (DB, cache, third-party API).
- **Unoptimized queries**: N+1 problems (e.g., fetching users and their posts in a loop) explode under load.
- **Network overhead**: Too many API calls (e.g., a microservice calling 5 databases per request) slow everything down.

**Example**: A chat app’s real-time messaging service works fine at 1K users but **delays messages by 500ms at 10K users** because each message triggers 3 DB writes + a WebSocket broadcast.

### **3. Caching Doesn’t Always Help**
Caching is often the first optimization, but it’s **not a silver bullet**:
- **Cache stampede**: Without proper invalidation, every request hits the DB after cache misses.
- **Hot-key problems**: A few popular items (e.g., "Trending Posts") overwhelm the cache.
- **Stale reads**: Even with TTL, stale cache entries can cause inconsistent data.

**Example**: A news aggregator caches trending articles. During a viral story surge, the cache gets **90% miss rate** because the data changes every 10 minutes.

---
## **The Solution: Throughput Approaches**

To handle high throughput, we need a **multi-layered strategy**. Here are the key approaches, categorized by where they act:

| **Layer**          | **Goal**                          | **Key Strategies**                          |
|--------------------|-----------------------------------|---------------------------------------------|
| **Application**    | Reduce per-request overhead       | Async processing, batching, streaming      |
| **Database**       | Distribute load, minimize locks   | Read replicas, sharding, connection pooling |
| **API**           | Scale request handling            | Load balancing, rate limiting, gRPC         |
| **Caching**       | Reduce DB load                    | Multi-level caching, cache-aside, stale-while-revalidate |
| **Infrastructure**| Horizontal scaling                | Auto-scaling, serverless, edge caching     |

We’ll explore each in detail with **real-world examples**.

---

## **1. Horizontal Scaling: Distribute the Load**

### **The Problem**
Vertical scaling (bigger servers) works… until it doesn’t. Eventually, even a **256-core machine with 1TB RAM** can’t keep up if the workload is distributed.

### **The Solution: Shard Your Database**
Instead of one giant database, split data across **multiple instances** (shards). Common strategies:

#### **A. Consistent Hashing (for Key-Based Sharding)**
Distribute data by a hash of a key (e.g., user ID, post ID).

**Example (Go):**
```go
package main

import (
	"fmt"
	"hash/crc32"
)

// Simple consistent hashing for sharding
func GetShardId(key string, numShards int) int {
	hash := int(crc32.ChecksumIEEE([]byte(key)))
	return hash % numShards
}

func main() {
	fmt.Println(GetShardId("user123", 3)) // Output: 1 (user123 → shard 1)
	fmt.Println(GetShardId("post456", 3)) // Output: 0 (post456 → shard 0)
}
```

**Tradeoffs**:
- ✅ **Even distribution**: Keys spread evenly across shards.
- ❌ **Hot keys**: A few keys (e.g., "global_stats") may still skew load.
- ❌ **Join complexity**: Cross-shard joins are expensive (use denormalization).

#### **B. Range-Based Sharding (for Time-Series Data)**
Split by ranges (e.g., `user_id % 1000`).

**SQL Example:**
```sql
-- User sharding by range (e.g., shard-0: users 0-999)
CREATE TABLE users_shard_0 (
    user_id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT
) PARTITION BY RANGE (user_id);

-- Add more partitions dynamically
CREATE TABLE users_shard_1 (
    user_id INT PRIMARY KEY,
    name TEXT,
    email TEXT
) PARTITION BY RANGE (user_id);

-- Insert into the correct partition
INSERT INTO users_shard_0 (user_id, name, email)
VALUES (100, 'Alice', 'alice@example.com');
```

**Tradeoffs**:
- ✅ **Simple**: Easy to implement with PostgreSQL’s `PARTITION BY RANGE`.
- ❌ **Skewed writes**: If users sign up in bursts, one shard may become hot.

---

### **2. Read Replicas: Offload Read-Heavy Workloads**

**Problem**: Your app reads data **10x more** than it writes (common in analytics, dashboards).

**Solution**: Use **read replicas**—copies of the primary DB for reads only.

**Example (PostgreSQL):**
```sql
-- Create a read replica (requires streaming replication)
SELECT pg_create_physical_replication_slot('replica_slot');
-- Configure in postgresql.conf:
# wal_level = logical
# max_wal_senders = 5
# hot_standby = on
```

**Go Client Load Balancing:**
```go
package main

import (
	"database/sql"
	"fmt"
	"math/rand"
	"time"

	_ "github.com/lib/pq"
)

var readReplicas = []string{
	"postgres://user:pass@replica1:5432/db",
	"postgres://user:pass@replica2:5432/db",
}

func GetRandomReadReplica() *sql.DB {
	replica := readReplicas[rand.Intn(len(readReplicas))]
	db, _ := sql.Open("postgres", replica)
	return db
}

func main() {
	db := GetRandomReadReplica()
	defer db.Close()

	// Safe for reads-only
	rows, _ := db.Query("SELECT * FROM posts WHERE id = $1", 1)
	defer rows.Close()
	// ...
}
```

**Tradeoffs**:
- ✅ **Low cost**: Cheap compared to sharding.
- ❌ **Eventual consistency**: Replicas may lag behind primary.
- ❌ **Write overhead**: Primary DB still handles all writes.

---

### **3. Connection Pooling: Avoid DB Connection Leaks**

**Problem**: Every request opens/closes a DB connection → **10K requests = 10K connections**, draining memory.

**Solution**: Use a **connection pool** (e.g., PgBouncer, database/sql in Go).

**Go Example (with PgBouncer):**
```go
package main

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

func main() {
	// PgBouncer manages connections (e.g., pool_size=100)
	connStr := "postgres://user:pass@localhost:6432/db?pool_size=100"
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	// Reuse connections efficiently
	rows, err := db.Query("SELECT * FROM posts LIMIT 10")
	// ...
}
```

**Tradeoffs**:
- ✅ **Fast recovery**: Pools reuse connections, reducing cold starts.
- ❌ **Memory usage**: Too many idle connections waste RAM.

---

## **4. Caching Layers: Reduce DB Load**

### **Problem**
Every API call hitting the DB **100x per second** → **10K QPS** becomes **1M DB queries**.

### **Solution: Multi-Level Caching**
1. **Client-side cache** (Redis, Memcached)
2. **App-level cache** (in-memory, e.g., `sync.Map` in Go)
3. **Database cache** (PostgreSQL’s `pg_pool_hba.conf` for connection reuse)

**Example: Redis Caching (Python with FastAPI):**
```python
from fastapi import FastAPI
import redis
import json

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/posts/{id}")
async def get_post(id: int):
    cache_key = f"post:{id}"
    cached = r.get(cache_key)

    if cached:
        return json.loads(cached)

    # Fallback to DB (simplified)
    db_post = {"id": id, "title": "Sample Post", "content": "..."}
    r.setex(cache_key, 300, json.dumps(db_post))  # Cache for 5 mins
    return db_post
```

**Tradeoffs**:
- ✅ **Massive speedup**: Redis can handle **100K+ reads/sec**.
- ❌ **Cache invalidation**: Stale data if not handled properly.

---

## **5. Asynchronous Processing: Avoid Blocking APIs**

### **Problem**
Synchronous APIs **block** until DB writes/complete → **high latency under load**.

### **Solution: Queue-Based Async Processing**
Use **message queues** (Kafka, RabbitMQ, AWS SQS) to offload work.

**Example (Go + RabbitMQ):**
```go
package main

import (
	"github.com/streadway/amqp"
)

func main() {
	conn, _ := amqp.Dial("amqp://guest:guest@localhost:5672/")
	ch, _ := conn.Channel()
	ch.QueueDeclare(
		"async_tasks", // queue name
		false,         // durable
		false,         // exclusive
		false,         // auto-delete
		false,         // no-wait
		nil,           // args
	)

	// Publish tasks (e.g., send email)
	task := map[string]interface{}{
		"user_id": 123,
		"email":   "alice@example.com",
	}
	ch.Publish(
		"",     // exchange
		"async_tasks", // routing key
		false,   // mandatory
		false,   // immediate
		amqp.Publishing{
			ContentType: "application/json",
			Body:        []byte(task),
		},
	)
}
```

**Worker Consumer (Go):**
```go
func processTask(delivery amqp.Delivery) {
	// Parse JSON, send email, etc.
	println(string(delivery.Body))
	delivery.Ack(false) // Acknowledge
}

func main() {
	// ... (same conn/ch as above)
	msgs, _ := ch.Consume(
		"async_tasks", // queue
		"",            // consumer
		true,          // auto-ack
		false,         // exclusive
		false,         // no-local
		false,         // no-wait
		nil,           // args
	)

	for msg := range msgs {
		processTask(msg)
	}
}
```

**Tradeoffs**:
- ✅ **Decoupled**: API doesn’t wait for DB writes.
- ❌ **Complexity**: Need monitoring for stalled queues.

---

## **6. API-Level Optimizations**

### **A. Rate Limiting**
Prevent abuse by limiting requests per IP/user.

**Example (FastAPI with Redis):**
```python
from fastapi import FastAPI, HTTPException, Depends
import redis
from fastapi.security import APIKeyHeader

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)
api_key_header = APIKeyHeader(name="X-API-Key")

def check_rate_limit(api_key: str = Depends(api_key_header)):
    key = f"rate_limit:{api_key}"
    current = r.incr(key)
    if current > 100:  # 100 requests/min
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    r.expire(key, 60)  # Reset in 60s

@app.get("/data")
def read_data(api_key: str = Depends(check_rate_limit)):
    return {"data": "ok"}
```

### **B. Batch Processing**
Reduce DB calls by fetching multiple records at once.

**Example (Go + Batch DB Queries):**
```go
// Instead of 100 separate queries:
for i := 0; i < 100; i++ {
    _, err := db.Exec("INSERT INTO logs VALUES ($1)", i)
}

// Use a transaction + batch:
tx, _ := db.Begin()
for i := 0; i < 100; i++ {
    _, err := tx.Exec("INSERT INTO logs VALUES ($1)", i)
}
tx.Commit()
```

**Tradeoffs**:
- ✅ **Faster reads/writes**: Fewer network roundtrips.
- ❌ **Higher memory usage**: Batch size must fit in memory.

---

## **Implementation Guide: Step-by-Step Checklist**

| **Step**               | **Action**                                                                 | **Tools/Libraries**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| 1. **Profile Load**    | Measure QPS, DB latency, API response times.                                | Prometheus, Grafana, `go pprof`            |
| 2. **Add Read Replicas** | Offload read-heavy workloads.                                              | PostgreSQL, MySQL                          |
| 3. **Shard If Needed** | Split by user ID, time range, or geography.                                | Vitess, Citus (PostgreSQL)                 |
| 4. **Connection Pooling** | Configure `pgbouncer` or `database/sql` pool size.                        | PgBouncer, HikariCP (Java)                 |
| 5. **Cache Strategically** | Use Redis/Memcached for hot data.                                         | Redis, Memcached                            |
| 6. **Async Processing** | Move heavy tasks to queues (Kafka, RabbitMQ).                              | NATS, AWS SQS                               |
| 7. **Rate Limit APIs** | Enforce limits per user/IP.                                                | Redis, FastAPI Middleware                   |
| 8. **Monitor & Iterate** | Set up alerts for queue backlogs, DB locks, or high latency.                | Datadog, New Relic                         |

---

## **Common Mistakes to Avoid**

### **1. Ignoring Cache Invalidation**
**Problem**: Stale cache causes inconsistent data.
**Fix**: Use **write-through** (update cache + DB) or **stale-while-revalidate**.

**Bad (Stale Cache):**
```python
# Cache miss → query DB → cache result (but DB changes 100ms later)
```

**Good (Write-Through):**
```python
def update_post(post_id, title):
    db.update(title)  # Update DB first
    cache.set(f"post:{post_id}", title)  # Then cache
```

### **2. Over-Sharding**
**Problem**: Too many shards → **network overhead** and **management complexity**.
**Fix**: Start with **2-4 shards**, monitor, then expand.

### **3. Not Testing Under Load**
**Problem**: "It works on my machine" → **catastrophe in production**.
**Fix**: Use **locust**, **k6**, or **Gatling** to simulate 10K+ users.

**Example (Locust Load Test):**
```python
from locust import HttpUser, task, between

class DatabaseUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def read_post(self):
        self.client.get("/posts/1")

    @task(3)
    def write_post(self):
        self.client.post("/posts", json={"title": "Test"})
```

### **4. Forgetting About Failover**
**Problem**: A single DB shard goes down → **downtime**.
**Fix**: Use **auto-failover** (PostgreSQL + Patroni) or **multi-region replicas**.

### **5. Blocking on External Calls**
**Problem**: API waits for slow third-party API (e.g., Stripe, Twilio).
**Fix**: Use **async HTTP clients** (e.g., `go-http-client` with context timeouts).

**Bad (Blocking):**
```go
resp, _ := http.Get("https://external-api.com/data")